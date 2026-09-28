"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, ApiError, Session, message } from "@/lib/api";

export default function Shell({ children }: {children: React.ReactNode}) {
  const router = useRouter();
  const [session, setSession] = useState<Session>();
  const [error, setError] = useState("");
  useEffect(() => {
    api<Session>("/auth/me").then(setSession).catch((e: unknown) => {
      if (e instanceof ApiError && e.status === 401) router.replace("/login");
      else setError(message(e));
    });
  }, [router]);
  async function logout() {
    try { await api("/auth/logout", {method: "POST"}); router.replace("/login"); }
    catch (e) { setError(message(e)); }
  }
  return <>
    <header><Link href="/projects" className="brand">Medical BA AI</Link><nav>
      <Link href="/projects">Projects</Link><span>{session?.user.display_name}</span>
      {session && <button className="secondary" onClick={logout}>Sign out</button>}
    </nav></header>
    <main>{error && <p role="alert" className="error">{error}</p>}
      {session ? children : <p>Loading your workspace…</p>}
    </main>
  </>;
}
