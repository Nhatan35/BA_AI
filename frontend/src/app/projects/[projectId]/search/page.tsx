"use client";
import Link from "next/link";
import { FormEvent, useState } from "react";
import KnowledgeWorkspace from "@/features/KnowledgeWorkspace";
import { api, message, Project } from "@/lib/api";
import { SearchResult } from "@/lib/knowledge";

function Search({project}: {project: Project}) {
  const [rows, setRows] = useState<SearchResult[]>([]);
  const [q, setQuery] = useState("");
  const [inactive, setInactive] = useState(false);
  const [next, setNext] = useState<number | null>(null);
  const [searched, setSearched] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function search(offset = 0) {setError(""); setBusy(true); try {const result = await api<{items: SearchResult[]; next_offset: number | null}>(`/projects/${project.id}/search?q=${encodeURIComponent(q)}&include_inactive=${inactive}&offset=${offset}`); setRows(old => offset ? [...old, ...result.items] : result.items); setNext(result.next_offset); setSearched(true);} catch(e) {setError(message(e));} finally {setBusy(false);}}
  function submit(event: FormEvent) {event.preventDefault(); void search();}
  return <><h1>Search project</h1><p>Search extracted text in this project. All versions of active sources are included, using their latest successful parse. Results are evidence, not approved policy.</p>
    <section className="panel"><form onSubmit={submit}><label>Search words<input value={q} onChange={e => setQuery(e.target.value)} required maxLength={200}/></label><label className="checkbox"><input type="checkbox" checked={inactive} onChange={e => setInactive(e.target.checked)}/>Include archived and superseded sources</label><button disabled={busy}>{busy ? "Searching…" : "Search"}</button></form></section>
    {error && <p className="error" role="alert">{error}</p>}{searched && rows.length === 0 && <p role="status">No matching passages in this project.</p>}
    {rows.map((row, index) => <article className="panel" key={`${row.parse_run_id}:${row.exact_reference}:${index}`}><h2><Link href={`/projects/${project.id}/sources/${row.source_id}?version=${row.source_version_id}&parse=${row.parse_run_id}`}>{row.source_code} · {row.source_name}</Link></h2><p className="muted">{row.original_filename} · Version {row.version_number} · {row.source_status} · {row.exact_reference}</p><p className="pre">{row.excerpt}</p></article>)}
    {next !== null && <button disabled={busy} className="secondary" onClick={() => search(next)}>Load more results</button>}
  </>;
}
export default function PageView() {return <KnowledgeWorkspace>{project => <Search project={project}/>}</KnowledgeWorkspace>;}
