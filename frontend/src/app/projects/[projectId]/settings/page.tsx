"use client";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import Shell from "@/features/Shell";
import { api, Member, message, Page, Project, Role, roles, Session } from "@/lib/api";

type Audit = {id: string; action: string; timestamp: string};
function Settings() {
  const { projectId } = useParams<{projectId: string}>();
  const base = `/projects/${projectId}`;
  const [project, setProject] = useState<Project>();
  const [members, setMembers] = useState<Member[]>([]);
  const [memberCursor, setMemberCursor] = useState<string | null>(null);
  const [self, setSelf] = useState("");
  const [logs, setLogs] = useState<Audit[]>([]);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [busy, setBusy] = useState(false);
  async function load() {
    const [p, ms, session] = await Promise.all([api<Project>(base), api<Page<Member>>(base + "/members"), api<Session>("/auth/me")]);
    setProject(p); setMembers(ms.items); setMemberCursor(ms.next_cursor); setSelf(session.user.id);
    if (p.my_role === "PROJECT_ADMIN") setLogs((await api<Page<Audit>>(base + "/audit")).items);
  }
  useEffect(() => { void load().catch(e => setError(message(e))); }, [projectId]); // eslint-disable-line react-hooks/exhaustive-deps
  async function action(operation: () => Promise<unknown>, successMessage: string) {
    setBusy(true); setError(""); setSuccess("");
    try { await operation(); await load(); setSuccess(successMessage); }
    catch (e) { setError(message(e)); } finally { setBusy(false); }
  }
  async function save(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const values = Object.fromEntries(new FormData(event.currentTarget));
    await action(() => api(base, {method: "PATCH", body: JSON.stringify({...values, expected_revision: project?.revision})}), "Project updated.");
  }
  async function add(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const values = Object.fromEntries(new FormData(event.currentTarget));
    await action(() => api(base + "/members", {method: "POST", body: JSON.stringify(values)}), "Member added.");
  }
  async function change(member: Member, role: Role, status: string) {
    await action(() => api(base + "/members/" + member.id, {method: "PATCH", body: JSON.stringify({role, status, expected_revision: member.revision})}), "Membership updated.");
  }
  async function moreMembers() {
    try { const page = await api<Page<Member>>(base + "/members?after=" + memberCursor); setMembers(old => [...old, ...page.items]); setMemberCursor(page.next_cursor); }
    catch (e) { setError(message(e)); }
  }
  if (!project) return <section className="panel"><h1>Project settings</h1>{error ? <p role="alert">{error}</p> : <p>Loading…</p>}<Link href="/projects">Back to projects</Link></section>;
  const admin = project.my_role === "PROJECT_ADMIN";
  return <><p><Link href={`/projects/${projectId}`}>Back to workspace</Link></p><h1>Project settings</h1>
    {error && <p role="alert" className="error">{error}</p>}{success && <p role="status" className="success">{success}</p>}
    {admin && <section className="panel"><h2>Context</h2><form onSubmit={save} key={project.revision}>
      <label>Project name<input name="name" defaultValue={project.name} required maxLength={200}/></label>
      <label>Organization<input name="organization" defaultValue={project.organization} maxLength={200}/></label>
      <label>Description<textarea name="description" defaultValue={project.description} maxLength={10000}/></label>
      <label>Scope<textarea name="scope" defaultValue={project.scope} maxLength={10000}/></label>
      <label>Out of scope<textarea name="out_of_scope" defaultValue={project.out_of_scope} maxLength={10000}/></label>
      <label>Project status<select name="status" defaultValue={project.status}>{["PLANNING", "ACTIVE", "ON_HOLD", "CLOSED"].map(s => <option key={s}>{s}</option>)}</select></label>
      <button disabled={busy}>Save project</button>
    </form></section>}
    <section className="panel"><h2>Members</h2>{!admin && <p>Project administrators manage memberships.</p>}
      <div className="table-scroll"><table><thead><tr><th>Member</th><th>Role</th><th>Status</th><th>Access</th></tr></thead><tbody>
        {members.map(member => <tr key={member.id}><td>{member.display_name}<br/><span className="muted">{member.email}</span></td>
          <td><select aria-label={`Role for ${member.email}`} value={member.role} disabled={!admin || busy || member.user_id === self} onChange={e => change(member, e.target.value as Role, member.status)}>{roles.map(role => <option key={role}>{role}</option>)}</select></td>
          <td>{member.status}</td><td>{admin && member.user_id !== self && <button className="secondary" disabled={busy} onClick={() => change(member, member.role, member.status === "ACTIVE" ? "INACTIVE" : "ACTIVE")}>{member.status === "ACTIVE" ? "Deactivate" : "Activate"}</button>}</td></tr>)}
      </tbody></table></div>
      {memberCursor && <button className="secondary" onClick={moreMembers}>Load more members</button>}
      {admin && <><h3>Add existing account</h3><form onSubmit={add}>
        <label>Member email<input name="email" type="email" required maxLength={320}/></label>
        <label>Project role<select name="role" defaultValue="VIEWER">{roles.map(role => <option key={role}>{role}</option>)}</select></label>
        <button disabled={busy}>Add member</button>
      </form></>}
    </section>
    {admin && <section className="panel"><h2>Recent audit events</h2>{logs.map(log => <p key={log.id}>{log.action} · {new Date(log.timestamp).toLocaleString()}</p>)}</section>}
  </>;
}
export default function PageView() { return <Shell><Settings/></Shell>; }
