"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import KnowledgeWorkspace from "@/features/KnowledgeWorkspace";
import { api, message, Page, Project } from "@/lib/api";
import { Evidence } from "@/lib/knowledge";

function Register({project}: {project: Project}) {
  const [rows, setRows] = useState<Evidence[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [loaded, setLoaded] = useState(false);
  const base = `/projects/${project.id}/evidence`;
  async function load(after?: string) {try {const data = await api<Page<Evidence>>(base + (after ? `?after=${after}` : "")); setRows(old => after ? [...old, ...data.items] : data.items); setCursor(data.next_cursor); setLoaded(true);} catch(e) {setError(message(e));}}
  useEffect(() => {void load();}, [base]);
  return <><h1>Evidence</h1><p>Manually cited source statements. Evidence and confirmation do not approve business requirements.</p>
    {["BA","PROJECT_ADMIN"].includes(project.my_role) && <p><Link href={`/projects/${project.id}/sources`}>Create evidence: choose a source and passage</Link></p>}
    {error && <p role="alert" className="error">{error}</p>}<section className="panel"><div className="table-scroll"><table><thead><tr><th>Evidence</th><th>Classification</th><th>Exact reference</th><th>Confirmation</th></tr></thead><tbody>
      {rows.map(e => <tr key={e.id}><td><Link href={`${base}/${e.id}`}>{e.evidence_code}</Link><p className="pre">{e.summary || e.extracted_text.slice(0, 180)}</p></td><td>{e.classification}</td><td>{e.exact_reference}</td><td>{e.confirmed_by ? "Human confirmed" : "Unconfirmed"}</td></tr>)}
    </tbody></table></div>{loaded && rows.length === 0 && <p>No evidence yet.</p>}{cursor && <button className="secondary" onClick={() => load(cursor)}>Load more evidence</button>}</section></>;
}
export default function PageView() {return <KnowledgeWorkspace>{project => <Register project={project}/>}</KnowledgeWorkspace>;}
