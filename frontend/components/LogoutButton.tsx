"use client";

import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function LogoutButton() {
  const router = useRouter();

  async function logout() {
    try {
      await api<{ ok: boolean }>("/api/v1/auth/logout", { method: "POST" });
    } finally {
      router.push("/login");
      router.refresh();
    }
  }

  return <button className="btn btn-ghost" onClick={logout}>Sign out</button>;
}
