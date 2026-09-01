import app.services.research_graph as research_graph
from app.services.ollama import LocalModelError


def _state():
    return {
        "run_id": "test-run",
        "question": "What are the benefits and risks of AI?",
        "sources": [
            {
                "source_key": "S1",
                "title": "Test Source",
                "url": "https://example.com/source",
                "domain": "example.com",
                "snippet": (
                    "Artificial intelligence can improve developer productivity "
                    "while introducing reliability and security risks."
                ),
                "content_excerpt": None,
                "content_hash": "test-hash",
                "fetch_status": "snippet_only",
            }
        ],
        "claims": [
            {
                "claim_text": (
                    "AI can improve developer productivity while introducing "
                    "reliability and security risks."
                ),
                "verdict": "supported",
                "confidence": 0.9,
                "grounding_score": 0.8,
                "source_keys": ["S1"],
                "note": None,
            }
        ],
        "warnings": [],
    }


def _invalid_payload():
    return {
        "summary": "Initial draft",
        "report_markdown": (
            "## Overview\n\n"
            "Artificial intelligence can improve software development "
            "productivity but also introduces several important risks.\n\n"
            "## Key Findings\n\n"
            "- AI can accelerate common software engineering workflows.\n\n"
            "## Sources\n\n"
            "- [S1] Test Source - https://example.com/source"
        ),
    }


def _valid_payload():
    return {
        "summary": "Repaired draft",
        "report_markdown": (
            "## Overview\n\n"
            "Artificial intelligence can improve software development "
            "productivity while also introducing important risks [S1].\n\n"
            "## Key Findings\n\n"
            "- AI can accelerate common software engineering workflows "
            "while requiring careful reliability controls [S1].\n\n"
            "## Caveats\n\n"
            "The available evidence is limited to the supplied sources.\n\n"
            "## Sources\n\n"
            "- [S1] Test Source - https://example.com/source"
        ),
    }


def test_writer_repairs_invalid_first_draft(monkeypatch):
    calls = []

    def fake_chat_json(*args, **kwargs):
        calls.append((args, kwargs))

        if len(calls) == 1:
            return _invalid_payload()

        return _valid_payload()

    monkeypatch.setattr(
        research_graph.ollama,
        "chat_json",
        fake_chat_json,
    )
    monkeypatch.setattr(
        research_graph,
        "set_run_stage",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        research_graph,
        "complete_run",
        lambda *args, **kwargs: None,
    )

    result = research_graph.writer_node(_state())

    assert len(calls) == 2
    assert result["summary"] == "Repaired draft"
    assert "[S1]" in result["report"]
    assert result["warnings"] == []


def test_writer_builds_claim_led_report_after_failed_repair(
    monkeypatch,
):
    calls = []

    def fake_chat_json(*args, **kwargs):
        calls.append((args, kwargs))
        return _invalid_payload()

    monkeypatch.setattr(
        research_graph.ollama,
        "chat_json",
        fake_chat_json,
    )
    monkeypatch.setattr(
        research_graph,
        "set_run_stage",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        research_graph,
        "complete_run",
        lambda *args, **kwargs: None,
    )

    result = research_graph.writer_node(_state())

    assert len(calls) == 2
    assert "assembled from claims" in result["summary"]
    assert "## Overview" in result["report"]
    assert "## Key Findings" in result["report"]
    assert "## Caveats" in result["report"]
    assert "[S1]" in result["report"]
    assert result["warnings"] == []


def test_writer_uses_source_led_report_when_no_claims(
    monkeypatch,
):
    calls = []

    def fake_chat_json(*args, **kwargs):
        calls.append((args, kwargs))
        return _invalid_payload()

    monkeypatch.setattr(
        research_graph.ollama,
        "chat_json",
        fake_chat_json,
    )
    monkeypatch.setattr(
        research_graph,
        "set_run_stage",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        research_graph,
        "complete_run",
        lambda *args, **kwargs: None,
    )

    state = _state()
    state["claims"] = []

    result = research_graph.writer_node(state)

    assert len(calls) == 2
    assert "enough verified claims" in result["summary"]
    assert "source-led research digest" in result["summary"]
    assert "[S1]" in result["report"]
    assert result["warnings"] == []


def test_writer_output_validation_rejects_uncited_content():
    try:
        research_graph._validate_writer_output(
            _invalid_payload(),
            {"S1"},
        )
    except LocalModelError as error:
        assert "uncited" in str(error)
    else:
        raise AssertionError(
            "Expected invalid writer output to be rejected"
        )