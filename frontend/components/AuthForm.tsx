"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api, ApiError } from "@/lib/api";
import type { User } from "@/lib/types";

export default function AuthForm({ mode }: { mode: "login" | "register" }) {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      const body = mode === "register" ? { name, email, password } : { email, password };
      await api<User>(`/api/v1/auth/${mode}`, { method: "POST", body: JSON.stringify(body) });
      router.push("/dashboard");
      router.refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not complete the request");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit}>
      {mode === "register" && (
        <div className="field"><label>Name</label><input className="input" value={name} onChange={(e) => setName(e.target.value)} required minLength={2} /></div>
      )}
      <div className="field"><label>Email</label><input className="input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required /></div>
      <div className="field"><label>Password</label><input className="input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={mode === "register" ? 10 : 1} /></div>
      {error && <div className="error">{error}</div>}
      <button className="btn btn-primary" style={{width: "100%", marginTop: 14}} disabled={busy}>{busy ? "Working..." : mode === "register" ? "Create account" : "Sign in"}</button>
      <p className="muted" style={{fontSize: 13, marginTop: 18}}>
        {mode === "register" ? <>Already registered? <Link href="/login">Sign in</Link></> : <>Need an account? <Link href="/register">Create one</Link></>}
      </p>
    </form>
  );
}
