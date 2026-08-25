"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import type { ResearchRun } from "@/lib/types";

export default function NewResearchForm() {
  const router = useRouter();
  const [question, setQuestion] = useState("");
  const [depth, setDepth] = useState("standard");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function submit(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError("");
    try {
      const run = await api<ResearchRun>("/api/v1/research", { method: "POST", body: JSON.stringify({question, depth}) });
      router.push(`/research/${run.id}`);
    } catch (err) { setError(err instanceof ApiError ? err.message : "Could not queue the research run"); setBusy(false); }
  }
  return <form className="card" style={{padding: 26}} onSubmit={submit}><div className="field"><label>Research question</label><textarea className="input" value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="Example: How has small-scale solar adoption changed electricity demand in Pakistan since 2022, and what evidence supports the trend?" required minLength={12} maxLength={1200}/></div><div className="field"><label>Depth</label><select className="input" value={depth} onChange={(e) => setDepth(e.target.value)}><option value="quick">Quick — 2-3 searches, up to 6 sources</option><option value="standard">Standard — 3-5 searches, up to 10 sources</option><option value="deep">Deep — 5-7 searches, up to 14 sources</option></select></div>{error && <div className="error">{error}</div>}<button className="btn btn-primary" disabled={busy}>{busy ? "Queuing research..." : "Start research"}</button></form>;
}
