"use client";
import Link from "next/link";
import { useParams } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import KnowledgeWorkspace from "@/features/KnowledgeWorkspace";
import { api, message, Project } from "@/lib/api";
import { classifications, Evidence } from "@/lib/knowledge";

function Detail({project}: {project: Project}) {
  const {evidenceId} = useParams<{evidenceId: string}>();
  const [record, setRecord] = useState<Evidence>();
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const base = `/projects/${project.id}/evidence/${evidenceId}`;
  const editor = ["BA", "PROJECT_ADMIN"].includes(project.my_role);
  const confirmer = ["BUSINESS_OWNER", "PROJECT_ADMIN"].includes(project.my_role);
  useEffect(() => {setRecord(undefined); api<Evidence>(base).then(setRecord).catch(e => setError(message(e)));}, [base]);
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!record) return; setError(""); setBusy(true); setNotice("");
    const data = new FormData(event.currentTarget);
    try {setRecord(await api<Evidence>(base, {method: "PATCH", body: JSON.stringify({expected_revision: record.revision, summary: data.get("summary"), classification: data.get("classification"), evidence_type: data.get("evidence_type"), confidence: data.get("confidence") ? Number(data.get("confidence")) : null})})); setNotice("Evidence metadata saved; confirmation cleared.");}
    catch(e) {setError(message(e));} finally {setBusy(false);}
  }
  async function confirm() {if (!record) return; setError(""); setBusy(true); try {setRecord(await api<Evidence>(base + "/confirmation", {method: "POST", body: JSON.stringify({expected_revision: record.revision, confirmed: !record.confirmed_by})})); setNotice("Human confirmation updated.");} catch(e) {setError(message(e));} finally {setBusy(false);}}
  if (!record) return <><h1>Evidence</h1>{error ? <p role="alert" className="error">{error}</p> : <p>Loading evidence…</p>}</>;
  return <><h1>{record.evidence_code}</h1><p>{record.classification} · {record.evidence_type} · {record.confirmed_by ? "Human confirmed" : "Unconfirmed"}</p>
    {error && <p className="error" role="alert">{error}</p>}{notice && <p role="status" className="success">{notice}</p>}
    <section className="panel"><h2>Exact provenance</h2><p>{record.exact_reference}</p><blockquote className="pre">{record.extracted_text}</blockquote>
      <Link href={`/projects/${project.id}/sources/${record.source_id}?version=${record.source_version_id}&parse=${record.parse_run_id}`}>Open cited source version and parse</Link>
      <p className="muted">A source statement remains evidence. Confirmation is attributed to a person and does not approve a requirement or decide a clinical policy.</p>
      {record.confirmed_by && <p>Confirmed by {record.confirmed_by} at {record.confirmed_at}</p>}
      {confirmer && <button disabled={busy} className="secondary" onClick={confirm}>{record.confirmed_by ? "Withdraw confirmation" : "Confirm evidence"}</button>}
    </section><section className="panel"><h2>Evidence metadata</h2>{editor ? <form onSubmit={save} key={record.revision}><label>Summary<textarea name="summary" defaultValue={record.summary} maxLength={10000}/></label>
      <label>Classification<select name="classification" defaultValue={record.classification}>{classifications.map(c => <option key={c}>{c}</option>)}</select></label><label>Evidence type<input name="evidence_type" defaultValue={record.evidence_type} maxLength={40} required/></label>
      <label>Confidence (optional, 0–1)<input name="confidence" type="number" min={0} max={1} step="0.01" defaultValue={record.confidence ?? ""}/></label><button disabled={busy}>Save evidence metadata</button></form> : <><p className="pre">{record.summary}</p><p>Confidence: {record.confidence ?? "Unspecified"}</p></>}
    </section></>;
}
export default function PageView() {return <KnowledgeWorkspace>{project => <Detail project={project}/>}</KnowledgeWorkspace>;}
