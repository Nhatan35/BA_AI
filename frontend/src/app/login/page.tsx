"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, message } from "@/lib/api";

export default function Login() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError("");
    const values = new FormData(event.currentTarget);
    try {
      await api("/auth/login", {method: "POST", body: JSON.stringify({email: values.get("email"), password: values.get("password")})});
      router.replace("/projects");
    } catch (e) { setError(message(e)); } finally { setBusy(false); }
  }
  return <main className="login panel"><p className="muted">Medical BA AI</p><h1>Sign in</h1>
    <p>Open your business analysis projects.</p>
    {error && <p role="alert" className="error">{error}</p>}
    <form onSubmit={submit}>
      <label>Email<input name="email" type="email" autoComplete="username" required maxLength={320}/></label>
      <label>Password<input name="password" type="password" autoComplete="current-password" required maxLength={1024}/></label>
      <button disabled={busy}>{busy ? "Signing in…" : "Sign in"}</button>
    </form>
  </main>;
}
