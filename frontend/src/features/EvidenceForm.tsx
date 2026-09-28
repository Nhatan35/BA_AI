"use client";
import Link from "next/link";
import { FormEvent, useState } from "react";
import { api, message } from "@/lib/api";
import { classifications, Evidence, Section, Version } from "@/lib/knowledge";

export default function EvidenceForm({projectId, sourceId, version, section, parseRunId}: {projectId: string; sourceId: string; version: Version; section: Section; parseRunId: string}) {
  const [error, setError] = useState("");
  const [created, setCreated] = useState<Evidence>();
  const [busy, setBusy] = useState(false);
  const locator = section.locator;
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(""); setCreated(undefined); setBusy(true);
    const data = new FormData(event.currentTarget);
    const confidence = data.get("confidence");
    const location = {...locator, start: Number(data.get("start")), end: Number(data.get("end"))};
    if (locator.column_start) {location.column_start = String(data.get("column_start")); location.column_end = String(data.get("column_end"));}
    try {setCreated(await api<Evidence>(`/projects/${projectId}/evidence`, {method: "POST", body: JSON.stringify({source_id: sourceId, source_version_id: version.id, parse_run_id: parseRunId, locator: location, extracted_text: data.get("extract") || null, summary: data.get("summary"), classification: data.get("classification"), confidence: confidence ? Number(confidence) : null})}));}
    catch(e) {setError(message(e));} finally {setBusy(false);}
  }
  return <section className="panel"><h2>Create evidence</h2><p>Version {version.version_number} · {section.display_reference}. A FACT label records a source statement; it does not approve a requirement.</p>
    {error && <p className="error" role="alert">{error}</p>}{created && <p className="success" role="status">Evidence saved: <Link href={`/projects/${projectId}/evidence/${created.id}`}>{created.evidence_code}</Link></p>}
    <form onSubmit={save}><div className="grid"><label>Start line, page, paragraph or row<input name="start" type="number" min={1} required defaultValue={locator.start}/></label><label>End line, page, paragraph or row<input name="end" type="number" min={1} required defaultValue={locator.end || locator.start}/></label></div>
      {locator.column_start && <div className="grid"><label>Start column<input name="column_start" required defaultValue={locator.column_start}/></label><label>End column<input name="column_end" required defaultValue={locator.column_end}/></label></div>}
      <label>Exact extract<textarea name="extract" maxLength={30000} defaultValue={section.text}/></label><p className="muted">The quote must occur exactly in the selected passage. Leave it empty to use the full range.</p>
      <label>Summary<textarea name="summary" maxLength={10000}/></label><div className="grid"><label>Classification<select name="classification">{classifications.map(c => <option key={c}>{c}</option>)}</select></label><label>Confidence (optional, 0–1)<input name="confidence" type="number" min={0} max={1} step="0.01"/></label></div>
      <button disabled={busy}>{busy ? "Saving…" : "Save evidence"}</button>
    </form></section>;
}
