"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { api, ApiError } from "@/lib/api";
import type { ResearchRun } from "@/lib/types";

export default function ResearchRunClient({ id }: { id: string }) {
  const [run, setRun] = useState<ResearchRun | null>(null);
  const [error, setError] = useState("");
  const load = useCallback(async () => {
    try { const data = await api<ResearchRun>(`/api/v1/research/${id}`); setRun(data); return data; }
    catch (err) { setError(err instanceof ApiError ? err.message : "Could not load this research run"); return null; }
  }, [id]);
  useEffect(() => {
    let active = true;
    let timer: ReturnType<typeof setTimeout> | undefined;
    async function poll() {
      const data = await load();
      if (!active || !data || ["completed", "failed"].includes(data.status)) return;
      timer = setTimeout(poll, 1800);
    }
    poll();
    return () => { active = false; if (timer) clearTimeout(timer); };
  }, [load]);

  if (error) return <main className="shell dashboard"><div className="error">{error}</div></main>;
  if (!run) return <main className="shell dashboard"><div className="empty">Loading research run...</div></main>;

  const active = ["queued", "running"].includes(run.status);
  return <main className="shell dashboard"><div className="page-head"><div><div className="kicker">Research run</div><h1 style={{fontSize: 38}}>{run.question}</h1><div className="run-meta"><span>{run.depth} depth</span><span>{run.model_name || "local model"}</span><span>{new Date(run.created_at).toLocaleString()}</span></div></div>{run.status === "completed" && <a className="btn" href={`/api/backend/api/v1/research/${run.id}/report.md`}>Download Markdown</a>}</div>
  {active && <div className="card" style={{marginBottom: 20}}><div className="claim-top"><strong>{run.stage.replaceAll("_", " ")}</strong><span>{run.progress}%</span></div><div className="progress"><span style={{width: `${run.progress}%`}} /></div><div className="muted" style={{fontSize: 13}}>The worker is moving through the research graph. This page updates automatically.</div></div>}
  {run.status === "failed" && <div className="error" style={{marginBottom: 20}}>{run.error_message || "This research run failed."}</div>}
  {run.warnings?.map((warning) => <div className="warning" key={warning}>{warning}</div>)}
  <div className="research-layout">
    <section>
      {run.report_markdown ? <article className="card report"><ReactMarkdown remarkPlugins={[remarkGfm]}>{run.report_markdown}</ReactMarkdown></article> : <div className="card"><h3>Research plan</h3>{run.plan?.length ? <ol>{run.plan.map((item) => <li key={item} style={{margin: "10px 0"}}>{item}</li>)}</ol> : <p className="muted">The plan will appear after the first stage completes.</p>}</div>}
      {run.claims.length > 0 && <div className="card" style={{marginTop: 18}}><h3>Fact-check notes</h3><p className="muted">These checks are retained separately from the final report.</p>{run.claims.map((claim, i) => <div className="claim" key={`${claim.claim_text}-${i}`}><div className="claim-top"><strong>{claim.verdict}</strong><span className="muted">grounding {Math.round(claim.grounding_score * 100)}%</span></div><div style={{marginTop: 8}}>{claim.claim_text}</div><div className="run-meta"><span>{claim.source_keys.join(", ")}</span><span>confidence {Math.round(claim.confidence * 100)}%</span></div></div>)}</div>}
    </section>
    <aside className="card sidebar"><h3>Sources</h3><p className="muted" style={{fontSize: 13}}>{run.sources.length} source{run.sources.length === 1 ? "" : "s"} saved</p>{run.sources.length ? run.sources.map((source) => <div className="source" key={source.source_key}><a href={source.url} target="_blank" rel="noreferrer">[{source.source_key}] {source.title}</a><small>{source.domain} · {source.fetch_status}</small></div>) : <div className="muted" style={{fontSize: 13}}>Sources will appear after search completes.</div>}<Link className="btn btn-ghost" style={{display:"inline-block", marginTop:18}} href="/research">Back to history</Link></aside>
  </div></main>;
}
