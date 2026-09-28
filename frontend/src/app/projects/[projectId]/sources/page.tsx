"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import KnowledgeWorkspace from "@/features/KnowledgeWorkspace";
import { api, message, Page, Project } from "@/lib/api";
import { Source, sourceTypes } from "@/lib/knowledge";

function Sources({project}: {project: Project}) {
  const router = useRouter();
  const [rows, setRows] = useState<Source[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const editor = ["BA", "PROJECT_ADMIN"].includes(project.my_role);
  const base = `/projects/${project.id}/sources`;
  async function load(after?: string) {
    try {const data = await api<Page<Source>>(base + (after ? `?after=${after}` : "")); setRows(old => after ? [...old, ...data.items] : data.items); setCursor(data.next_cursor); setLoaded(true);}
    catch(e) {setError(message(e));}
  }
  useEffect(() => { void load(); }, [base]);
  async function upload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(""); setBusy(true);
    const values = new FormData(event.currentTarget);
    const data = new FormData(); data.set("file", values.get("file") as File);
    data.set("metadata", JSON.stringify({name: values.get("name"), source_type: values.get("source_type"), description: values.get("description"), owner: values.get("owner"), source_date: values.get("source_date") || null, trust_level: values.get("trust_level")}));
    try {const result = await api<{source: Source}>(base, {method: "POST", body: data}); router.push(`${base}/${result.source.id}`);}
    catch(e) {setError(message(e));} finally {setBusy(false);}
  }
  return <><h1>Sources</h1><p>Original documents and their versions. Parsing and trust labels do not approve their statements.</p>
    {error && <p className="error" role="alert">{error}</p>}
    <section className="panel"><h2>Source register</h2><div className="table-scroll"><table><thead><tr><th>Source</th><th>Type</th><th>Status</th><th>Trust</th><th>Owner</th></tr></thead><tbody>
      {rows.map(source => <tr key={source.id}><td><Link href={`${base}/${source.id}`}>{source.source_code} · {source.name}</Link></td><td>{source.source_type}</td><td>{source.status}</td><td>{source.trust_level}</td><td>{source.owner || "Unspecified"}</td></tr>)}
    </tbody></table></div>{loaded && rows.length === 0 && <p>No sources yet.</p>}{cursor && <button className="secondary" onClick={() => load(cursor)}>Load more sources</button>}</section>
    {editor && <section className="panel"><h2>Upload source</h2><p className="muted">Use synthetic, non-patient information. TXT, MD, text PDF, DOCX, CSV or XLSX. Text files use UTF-8.</p>
      <form onSubmit={upload}><label>Source name<input name="name" required maxLength={200}/></label>
        <div className="grid"><label>Source type<select name="source_type" defaultValue="TEXT">{sourceTypes.map(t => <option key={t}>{t}</option>)}</select></label><label>Trust level<select name="trust_level" defaultValue="LOW">{["LOW", "MEDIUM", "HIGH"].map(t => <option key={t}>{t}</option>)}</select></label></div>
        <label>Description<textarea name="description" maxLength={10000}/></label><div className="grid"><label>Owner<input name="owner" maxLength={200}/></label><label>Source date<input type="date" name="source_date"/></label></div>
        <label>Source file<input type="file" name="file" required accept=".txt,.md,.pdf,.docx,.csv,.xlsx"/></label><button disabled={busy}>{busy ? "Uploading and parsing…" : "Upload and parse"}</button>
      </form></section>}
  </>;
}
export default function PageView() {return <KnowledgeWorkspace>{project => <Sources project={project}/>}</KnowledgeWorkspace>;}
