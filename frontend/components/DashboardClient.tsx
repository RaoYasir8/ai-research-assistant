"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { ResearchListItem, Stats, User } from "@/lib/types";
import LogoutButton from "./LogoutButton";

export default function DashboardClient() {
  const [user, setUser] = useState<User | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);
  const [runs, setRuns] = useState<ResearchListItem[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([
      api<User>("/api/v1/auth/me"),
      api<Stats>("/api/v1/research/stats"),
      api<ResearchListItem[]>("/api/v1/research?limit=6"),
    ]).then(([me, summary, recent]) => {
      setUser(me); setStats(summary); setRuns(recent);
    }).catch(() => setError("Sign in to view this workspace."));
  }, []);

  if (error) return <div className="shell dashboard"><div className="error">{error}</div><Link className="btn" href="/login">Go to sign in</Link></div>;

  return (
    <main className="shell dashboard">
      <div className="page-head"><div><div className="kicker">Workspace</div><h1>{user ? `${user.name.split(" ")[0]}'s research` : "Research dashboard"}</h1></div><div style={{display: "flex", gap: 10}}><LogoutButton /><Link className="btn btn-primary" href="/research/new">Start research</Link></div></div>
      <div className="stats">
        <div className="card stat"><span>Total runs</span><strong>{stats?.total_runs ?? "—"}</strong></div>
        <div className="card stat"><span>Completed</span><strong>{stats?.completed_runs ?? "—"}</strong></div>
        <div className="card stat"><span>Sources collected</span><strong>{stats?.total_sources ?? "—"}</strong></div>
        <div className="card stat"><span>Failed</span><strong>{stats?.failed_runs ?? "—"}</strong></div>
      </div>
      <div className="page-head" style={{marginTop: 34}}><div><h2>Recent research</h2><div className="muted">Latest saved runs and their current state.</div></div><Link className="btn btn-ghost" href="/research">View all</Link></div>
      <div className="list">
        {runs.length === 0 ? <div className="empty">No research yet. Start with a question you actually need answered.</div> : runs.map((run) => <RunRow key={run.id} run={run} />)}
      </div>
    </main>
  );
}

export function RunRow({ run }: { run: ResearchListItem }) {
  return <Link className="run-row" href={`/research/${run.id}`}><div><div className="run-title">{run.question}</div><div className="run-meta"><span>{new Date(run.created_at).toLocaleString()}</span><span>{run.depth}</span><span>{run.stage.replaceAll("_", " ")}</span></div></div><span className={`badge badge-${run.status}`}>{run.status}</span></Link>;
}
