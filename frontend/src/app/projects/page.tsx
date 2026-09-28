"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import Shell from "@/features/Shell";
import { api, message, Page, Project } from "@/lib/api";

function Projects() {
  const [items, setItems] = useState<Project[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [loaded, setLoaded] = useState(false);
  async function load(after?: string) {
    try {
      const result = await api<Page<Project>>(`/projects${after ? `?after=${after}` : ""}`);
      setItems(previous => after ? [...previous, ...result.items] : result.items);
      setCursor(result.next_cursor); setLoaded(true);
    } catch (e) { setError(message(e)); }
  }
  useEffect(() => { void load(); }, []);
  async function create(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError("");
    const form = event.currentTarget;
    const values = Object.fromEntries(new FormData(form));
    try { await api<Project>("/projects", {method: "POST", body: JSON.stringify(values)}); form.reset(); await load(); }
    catch (e) { setError(message(e)); } finally { setBusy(false); }
  }
  return <><h1>Projects</h1><p className="muted">Your project workspaces and scope.</p>
    {error && <p role="alert" className="error">{error}</p>}
    <div className="grid"><section className="panel"><h2>Your workspaces</h2>
      {!loaded && <p>Loading projects…</p>}
      {loaded && items.length === 0 && <p>No projects yet. Create your first workspace.</p>}
      {items.map(project => <article key={project.id}><h3><Link href={`/projects/${project.id}`}>{project.name}</Link></h3>
        <p><span className="badge">{project.my_role}</span> · {project.status}</p><p className="muted">{project.organization}</p></article>)}
      {cursor && <button className="secondary" onClick={() => load(cursor)}>Load more projects</button>}
    </section><section className="panel"><h2>Create project</h2><form onSubmit={create}>
      <label>Project name<input name="name" required maxLength={200}/></label>
      <label>Organization<input name="organization" maxLength={200}/></label>
      <label>Description<textarea name="description" maxLength={10000}/></label>
      <label>Scope<textarea name="scope" maxLength={10000}/></label>
      <label>Out of scope<textarea name="out_of_scope" maxLength={10000}/></label>
      <button disabled={busy}>{busy ? "Creating…" : "Create project"}</button>
    </form></section></div></>;
}
export default function PageView() { return <Shell><Projects/></Shell>; }
