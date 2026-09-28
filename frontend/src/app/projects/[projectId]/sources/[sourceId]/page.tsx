"use client";
import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { FormEvent, Suspense, useEffect, useState } from "react";
import EvidenceForm from "@/features/EvidenceForm";
import KnowledgeWorkspace from "@/features/KnowledgeWorkspace";
import { api, message, Page, Project } from "@/lib/api";
import { Parse, Parsed, Section, Source, sourceTypes, Version } from "@/lib/knowledge";

function Detail({project}: {project: Project}) {
  const {sourceId} = useParams<{sourceId: string}>();
  const query = useSearchParams();
  const [source, setSource] = useState<Source>();
  const [versions, setVersions] = useState<Version[]>([]);
  const [versionId, setVersionId] = useState("");
  const [cursor, setCursor] = useState<string | null>(null);
  const [parses, setParses] = useState<Parse[]>([]);
  const [runId, setRunId] = useState("");
  const [parsed, setParsed] = useState<Parsed>();
  const [section, setSection] = useState<Section>();
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const editor = ["BA", "PROJECT_ADMIN"].includes(project.my_role);
  const base = `/projects/${project.id}/sources/${sourceId}`;
  const version = versions.find(v => v.id === versionId);
  useEffect(() => {
    setSource(undefined); setError("");
    Promise.all([api<Source>(base), api<Page<Version>>(base + "/versions")]).then(async ([s, data]) => {
      setSource(s); setCursor(data.next_cursor);
      let rows = data.items;
      const requested = query.get("version");
      if (requested && !rows.some(v => v.id === requested)) rows = [...rows, await api<Version>(base + `/versions/${requested}`)];
      setVersions(rows); setVersionId(requested || [...rows].sort((a, b) => b.version_number - a.version_number)[0]?.id || "");
    }).catch(e => setError(message(e)));
  }, [base, query]);
  useEffect(() => {
    if (!versionId) return;
    setParsed(undefined); setSection(undefined); setRunId("");
    api<{items: Parse[]}>(`${base}/versions/${versionId}/parses`).then(data => {setParses(data.items); setRunId(query.get("parse") || data.items[0]?.id || "");}).catch(e => setError(message(e)));
  }, [base, versionId, query]);
  useEffect(() => { if (versionId && runId) void loadParsed(); }, [base, versionId, runId]);
  async function loadParsed(after?: number) {
    try {const data = await api<Parsed>(`${base}/versions/${versionId}/parsed?parse_run_id=${runId}${after ? `&after_ordinal=${after}` : ""}`); setParsed(old => after && old ? {...data, items: [...old.items, ...data.items]} : data);}
    catch(e) {setError(message(e));}
  }
  async function saveMetadata(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!source) return; setError(""); setNotice(""); setBusy(true);
    const values = new FormData(event.currentTarget);
    const body: Record<string, unknown> = {expected_revision: source.revision};
    for (const key of ["name", "source_type", "description", "owner", "trust_level", "status"]) body[key] = values.get(key);
    body.source_date = values.get("source_date") || null;
    if (values.get("supersedes_source_id")) body.supersedes_source_id = values.get("supersedes_source_id");
    try {setSource(await api<Source>(base, {method: "PATCH", body: JSON.stringify(body)})); setNotice("Source metadata saved.");}
    catch(e) {setError(message(e));} finally {setBusy(false);}
  }
  async function upload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(""); setBusy(true);
    const data = new FormData(event.currentTarget);
    try {const result = await api<{source: Source; version: Version}>(base + "/versions", {method: "POST", body: data}); setVersions(old => [...old, result.version]); setVersionId(result.version.id); setNotice("New immutable version uploaded.");}
    catch(e) {setError(message(e));} finally {setBusy(false);}
  }
  async function reparse() {
    setError(""); setBusy(true);
    try {const result = await api<Parse>(`${base}/versions/${versionId}/reparse`, {method: "POST"}); setParses(old => [result, ...old]); setRunId(result.id); const refreshed = await api<Version>(`${base}/versions/${versionId}`); setVersions(old => old.map(v => v.id === refreshed.id ? refreshed : v));}
    catch(e) {setError(message(e));} finally {setBusy(false);}
  }
  if (!source) return <><h1>Source</h1>{error ? <p role="alert" className="error">{error}</p> : <p>Loading source…</p>}</>;
  return <><h1>{source.name}</h1><p className="muted">{source.source_code} · {source.source_type} · {source.status} · Trust: {source.trust_level}</p>
    {error && <p className="error" role="alert">{error}</p>}{notice && <p className="success" role="status">{notice}</p>}
    <section className="panel"><h2>Version history</h2><label>View source version<select value={versionId} onChange={e => setVersionId(e.target.value)}>{[...versions].sort((a,b) => b.version_number-a.version_number).map(v => <option key={v.id} value={v.id}>Version {v.version_number} · {v.original_filename} · {v.parser_status}</option>)}</select></label>
      {cursor && <button className="secondary" onClick={async () => {try {const result = await api<Page<Version>>(`${base}/versions?after=${cursor}`); setVersions(old => [...old, ...result.items]); setCursor(result.next_cursor);} catch(e) {setError(message(e));}}}>Load older versions</button>}
      {version && <><p>{version.original_filename} · {version.file_size.toLocaleString()} bytes</p><p className="checksum">SHA-256: {version.checksum}</p><div className="row"><a href={`/api/v1${base}/versions/${versionId}/download`}>Download original</a>{editor && <button className="secondary" disabled={busy} onClick={reparse}>Reparse this version</button>}</div>
      {version.duplicate_version_ids.length > 0 && <p className="muted">Matching bytes already exist in {version.duplicate_version_ids.length} project version(s). This upload has been preserved.</p>}</>}
      <p className="muted">All versions remain available. A newer upload does not resolve a conflict or approve a statement.</p>
      {editor && source.status === "ACTIVE" && <form onSubmit={upload}><label>Replacement file<input name="file" type="file" accept=".txt,.md,.pdf,.docx,.csv,.xlsx" required/></label><button disabled={busy}>{busy ? "Working…" : "Upload new version"}</button></form>}
    </section>
    <section className="panel"><h2>Parsed content</h2>{parses.length > 0 && <label>Parse attempt<select value={runId} onChange={e => {setSection(undefined); setRunId(e.target.value);}}>{parses.map(p => <option key={p.id} value={p.id}>Attempt {p.attempt_number} · {p.parser_status}</option>)}</select></label>}
      {parsed ? <><p>Parser status: <strong>{parsed.parse.parser_status}</strong> · {parsed.parse.parser_name} {parsed.parse.parser_version}</p>
        {parsed.parse.parse_error && <p role="alert" className="error">Parse error: {parsed.parse.parse_error}{parsed.parse.parser_status === "UNSUPPORTED_OR_OCR_REQUIRED" && ". This PDF has no extractable text. OCR is outside Phase 2."}</p>}
        {parsed.items.map(item => <article className="passage" key={item.id}><div className="row"><strong>{item.display_reference}</strong>{editor && item.text.trim() && <button className="secondary" onClick={() => setSection(item)}>Create evidence from passage</button>}</div>
          {Object.keys(item.cells).length ? <div className="table-scroll"><table><thead><tr>{Object.keys(item.cells).map(col => <th key={col}>{col}{item.locator.start}</th>)}</tr></thead><tbody><tr>{Object.entries(item.cells).map(([col,text]) => <td className="pre" key={col}>{text}</td>)}</tr></tbody></table></div> : <p className="pre">{item.text || "(Empty passage)"}</p>}</article>)}
        {parsed.next_ordinal && <button className="secondary" onClick={() => loadParsed(parsed.next_ordinal!)}>Load more content</button>}
      </> : <p>Loading parse…</p>}</section>
    {section && version && <EvidenceForm key={`${section.id}:${runId}`} projectId={project.id} sourceId={sourceId} version={version} section={section} parseRunId={runId}/>}
    <section className="panel"><h2>Source metadata</h2>{editor ? <form onSubmit={saveMetadata} key={source.revision}>
      <label>Source name<input name="name" defaultValue={source.name} required maxLength={200}/></label><label>Description<textarea name="description" defaultValue={source.description} maxLength={10000}/></label>
      <div className="grid"><label>Source type<select name="source_type" defaultValue={source.source_type}>{sourceTypes.map(t => <option key={t}>{t}</option>)}</select></label><label>Trust level<select name="trust_level" defaultValue={source.trust_level}>{["LOW","MEDIUM","HIGH"].map(t => <option key={t}>{t}</option>)}</select></label></div>
      <div className="grid"><label>Owner<input name="owner" defaultValue={source.owner} maxLength={200}/></label><label>Source date<input name="source_date" type="date" defaultValue={source.source_date || ""}/></label></div>
      <label>Source status<select name="status" defaultValue={source.status}>{["ACTIVE","SUPERSEDED","ARCHIVED"].map(s => <option key={s}>{s}</option>)}</select></label>
      {!source.supersedes_source_id && <label>Source ID explicitly replaced (optional)<input name="supersedes_source_id"/><span className="muted">Saving this link marks the specified active source SUPERSEDED. Copy its ID from its source URL.</span></label>}
      <button disabled={busy}>Save metadata</button>
    </form> : <><p className="pre">{source.description}</p><p>Owner: {source.owner || "Unspecified"} · Date: {source.source_date || "Unspecified"}</p></>}
      {source.supersedes_source_id && <p>Explicitly replaces <Link href={`/projects/${project.id}/sources/${source.supersedes_source_id}`}>this source</Link>.</p>}
    </section>
  </>;
}
export default function PageView() {return <Suspense fallback={<p>Loading source…</p>}><KnowledgeWorkspace>{project => <Detail project={project}/>}</KnowledgeWorkspace></Suspense>;}
