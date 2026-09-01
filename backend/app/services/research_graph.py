from __future__ import annotations

import json
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app.config import settings
from app.domain.evidence import (
    content_hash,
    grounding_score,
    invalid_citations,
    uncited_key_blocks,
)
from app.services.fetcher import fetch_article
from app.services.ollama import LocalModelError, ollama
from app.services.prompts import (
    CHECKER_SYSTEM,
    CHECKER_USER,
    PLANNER_SYSTEM,
    PLANNER_USER,
    WRITER_SYSTEM,
    WRITER_USER,
)
from app.services.repository import (
    complete_run,
    replace_claims,
    replace_sources,
    save_plan,
    set_run_stage,
)
from app.services.search import SearchError, search_web


class ResearchState(TypedDict, total=False):
    run_id: str
    question: str
    depth: str
    plan: list[str]
    sources: list[dict]
    claims: list[dict]
    summary: str
    report: str
    warnings: list[str]


DEPTHS = {
    "quick": {"min_queries": 2, "max_queries": 3, "max_sources": 6},
    "standard": {"min_queries": 3, "max_queries": 5, "max_sources": 10},
    "deep": {"min_queries": 5, "max_queries": 7, "max_sources": 14},
}


def _fallback_queries(question: str, depth: str) -> list[str]:
    limit = DEPTHS[depth]["min_queries"]
    candidates = [
        question,
        f"{question} official source",
        f"{question} evidence analysis",
        f"{question} limitations criticism",
        f"{question} latest developments",
        f"{question} data statistics",
    ]
    return candidates[:limit]


def planner_node(state: ResearchState) -> ResearchState:
    set_run_stage(state["run_id"], "planning", 12)
    depth_cfg = DEPTHS[state["depth"]]
    warnings = list(state.get("warnings", []))

    try:
        payload = ollama.chat_json(
            PLANNER_SYSTEM,
            PLANNER_USER.format(
                question=state["question"],
                depth=state["depth"],
                min_queries=depth_cfg["min_queries"],
                max_queries=depth_cfg["max_queries"],
            ),
            temperature=0.1,
        )
        queries = [
            str(q).strip()
            for q in payload.get("queries", [])
            if str(q).strip()
        ]
        queries = list(dict.fromkeys(queries))[: depth_cfg["max_queries"]]

        if len(queries) < depth_cfg["min_queries"]:
            raise LocalModelError("planner returned too few usable queries")

    except LocalModelError:
        queries = _fallback_queries(state["question"], state["depth"])
        warnings.append(
            "Planner used deterministic fallback because the local model was "
            "unavailable or malformed."
        )

    save_plan(state["run_id"], queries)
    return {"plan": queries, "warnings": warnings}


def research_node(state: ResearchState) -> ResearchState:
    set_run_stage(state["run_id"], "researching", 35)
    max_sources = DEPTHS[state["depth"]]["max_sources"]
    warnings = list(state.get("warnings", []))
    raw_hits = []
    search_failures = 0

    for query in state["plan"]:
        try:
            raw_hits.extend(search_web(query))
        except SearchError:
            search_failures += 1

    if search_failures == len(state["plan"]):
        raise RuntimeError(
            "The search service did not return results. "
            "Check the SearXNG container."
        )

    if search_failures:
        warnings.append(
            f"{search_failures} search query or queries failed; "
            "the report used the remaining evidence."
        )

    unique_by_url = {}

    for hit in raw_hits:
        unique_by_url.setdefault(hit.url, hit)

    sources = []
    seen_hashes = set()

    for hit in list(unique_by_url.values())[: max_sources * 2]:
        fetched = fetch_article(hit.url)
        evidence_text = fetched.text or hit.snippet
        digest = content_hash(evidence_text) if evidence_text else None

        if digest and digest in seen_hashes:
            continue

        if digest:
            seen_hashes.add(digest)

        sources.append(
            {
                "source_key": f"S{len(sources) + 1}",
                "title": hit.title,
                "url": hit.url,
                "domain": hit.domain,
                "snippet": hit.snippet,
                "content_excerpt": fetched.text or None,
                "content_hash": digest,
                "fetch_status": (
                    fetched.status
                    if fetched.text
                    else (fetched.status or "snippet_only")
                ),
            }
        )

        if len(sources) >= max_sources:
            break

    if not sources:
        raise RuntimeError(
            "No usable sources were collected for this question."
        )

    replace_sources(state["run_id"], sources)
    return {"sources": sources, "warnings": warnings}


def _evidence_text(
    sources: list[dict],
    per_source_chars: int = 2200,
) -> str:
    blocks = []

    for source in sources:
        text = (
            source.get("content_excerpt")
            or source.get("snippet")
            or ""
        )
        blocks.append(
            f"BEGIN SOURCE {source['source_key']}\n"
            f"Title: {source['title']}\n"
            f"URL: {source['url']}\n"
            f"Evidence: {text[:per_source_chars]}\n"
            f"END SOURCE {source['source_key']}"
        )

    return "\n\n".join(blocks)


def checker_node(state: ResearchState) -> ResearchState:
    set_run_stage(state["run_id"], "fact_checking", 68)
    warnings = list(state.get("warnings", []))
    allowed = {
        source["source_key"]
        for source in state["sources"]
    }
    evidence = _evidence_text(state["sources"])

    try:
        payload = ollama.chat_json(
            CHECKER_SYSTEM,
            CHECKER_USER.format(
                question=state["question"],
                evidence=evidence,
            ),
            temperature=0.0,
        )
        raw_claims = payload.get("claims", [])

    except LocalModelError:
        raw_claims = []
        warnings.append(
            "Fact-check stage could not use the local model; "
            "the final report will be evidence-extractive."
        )

    source_map = {
        item["source_key"]: (
            item.get("content_excerpt")
            or item.get("snippet")
            or ""
        )
        for item in state["sources"]
    }

    claims = []

    for item in raw_claims[:20]:
        claim = str(item.get("claim", "")).strip()
        keys = [
            str(key)
            for key in item.get("sources", [])
            if str(key) in allowed
        ]

        if not claim or not keys:
            continue

        joined = " ".join(source_map[key] for key in keys)
        score = grounding_score(claim, joined)
        model_verdict = str(
            item.get("verdict", "partial")
        ).lower()

        verdict = (
            model_verdict
            if model_verdict
            in {"supported", "partial", "unsupported"}
            else "partial"
        )

        if score < 0.18:
            verdict = "unsupported"
        elif score < 0.32 and verdict == "supported":
            verdict = "partial"

        try:
            confidence = max(
                0.0,
                min(
                    1.0,
                    float(item.get("confidence", 0.5)),
                ),
            )
        except (TypeError, ValueError):
            confidence = 0.5

        claims.append(
            {
                "claim_text": claim[:1800],
                "verdict": verdict,
                "confidence": round(confidence, 3),
                "grounding_score": score,
                "source_keys": keys,
                "note": (
                    str(item.get("note", "")).strip()[:800]
                    or None
                ),
            }
        )

    replace_claims(state["run_id"], claims)
    return {"claims": claims, "warnings": warnings}


def _fallback_report(
    question: str,
    sources: list[dict],
) -> tuple[str, str]:
    summary = (
        "The local generation model was unavailable, so this run returned "
        "a source-led research digest instead of a synthesized narrative."
    )

    findings = []

    for source in sources[:6]:
        snippet = (
            source.get("snippet")
            or source.get("content_excerpt")
            or "No extract available."
        )
        findings.append(
            f"- {snippet[:420].strip()} "
            f"[{source['source_key']}]"
        )

    source_lines = [
        f"- [{source['source_key']}] "
        f"{source['title']} - {source['url']}"
        for source in sources
    ]

    report = (
        f"# Research: {question}\n\n"
        "## Overview\n\n"
        f"{summary}\n\n"
        "## Key Findings\n\n"
        + "\n".join(findings)
        + (
            "\n\n## Caveats\n\n"
            "This fallback is extractive and should not be treated "
            "as a full synthesis.\n\n"
            "## Sources\n\n"
        )
        + "\n".join(source_lines)
    )

    return summary, report


def writer_node(state: ResearchState) -> ResearchState:
    set_run_stage(state["run_id"], "writing", 88)
    warnings = list(state.get("warnings", []))
    allowed = {
        source["source_key"]
        for source in state["sources"]
    }
    evidence = _evidence_text(
        state["sources"],
        per_source_chars=1500,
    )
    usable_claims = [
        claim
        for claim in state.get("claims", [])
        if claim["verdict"] != "unsupported"
    ]

    try:
        payload = ollama.chat_json(
            WRITER_SYSTEM,
            WRITER_USER.format(
                question=state["question"],
                claims=json.dumps(
                    usable_claims,
                    ensure_ascii=False,
                ),
                evidence=evidence,
            ),
            temperature=0.2,
        )

        summary = str(
            payload.get("summary", "")
        ).strip()
        report = str(
            payload.get("report_markdown", "")
        ).strip()

        if not summary or not report:
            raise LocalModelError(
                "writer returned an empty report"
            )

        bad = invalid_citations(report, allowed)

        if bad:
            raise LocalModelError(
                f"writer used invalid citations: {sorted(bad)}"
            )

        if uncited_key_blocks(report):
            raise LocalModelError(
                "writer left substantive Overview or Key Findings "
                "text uncited"
            )

        if "## Sources" not in report:
            source_lines = [
                f"- [{source['source_key']}] "
                f"{source['title']} - {source['url']}"
                for source in state["sources"]
            ]
            report += (
                "\n\n## Sources\n\n"
                + "\n".join(source_lines)
            )

    except LocalModelError as error:
        summary, report = _fallback_report(
            state["question"],
            state["sources"],
        )
        warnings.append(
            f"Writer fallback reason: {error}"
        )

    complete_run(
        state["run_id"],
        summary,
        report,
        warnings,
        settings.ollama_model,
    )

    return {
        "summary": summary,
        "report": report,
        "warnings": warnings,
    }


def build_graph():
    graph = StateGraph(ResearchState)
    graph.add_node("planner", planner_node)
    graph.add_node("researcher", research_node)
    graph.add_node("fact_checker", checker_node)
    graph.add_node("writer", writer_node)

    graph.add_edge(START, "planner")
    graph.add_edge("planner", "researcher")
    graph.add_edge("researcher", "fact_checker")
    graph.add_edge("fact_checker", "writer")
    graph.add_edge("writer", END)

    return graph.compile()


research_graph = build_graph()


def run_research(
    run_id: str,
    question: str,
    depth: str,
) -> None:
    research_graph.invoke(
        {
            "run_id": run_id,
            "question": question,
            "depth": depth,
            "warnings": [],
        }
    )