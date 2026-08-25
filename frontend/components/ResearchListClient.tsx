"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { ResearchListItem } from "@/lib/types";
import { RunRow } from "./DashboardClient";

export default function ResearchListClient() {
  const [runs, setRuns] = useState<ResearchListItem[]>([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => { api<ResearchListItem[]>("/api/v1/research?limit=100").then(setRuns).finally(() => setLoading(false)); }, []);
  return <main className="shell dashboard"><div className="page-head"><div><div className="kicker">Archive</div><h1>Research history</h1></div><Link className="btn btn-primary" href="/research/new">New research</Link></div><div className="list">{loading ? <div className="empty">Loading research...</div> : runs.length ? runs.map((run) => <RunRow run={run} key={run.id} />) : <div className="empty">Nothing here yet.</div>}</div></main>;
}
