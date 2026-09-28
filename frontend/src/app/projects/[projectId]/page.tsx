"use client";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import Shell from "@/features/Shell";
import { api, message, Project } from "@/lib/api";

function Workspace() {
  const { projectId } = useParams<{projectId: string}>();
  const [project, setProject] = useState<Project>();
  const [error, setError] = useState("");
  useEffect(() => { api<Project>(`/projects/${projectId}`).then(setProject).catch(e => setError(message(e))); }, [projectId]);
  if (error) return <section className="panel"><h1>Workspace unavailable</h1><p role="alert">{error}</p><Link href="/projects">Back to projects</Link></section>;
  if (!project) return <p>Loading project…</p>;
  return <><p><Link href="/projects">All projects</Link></p><h1>{project.name}</h1>
    <div className="row"><span className="badge">{project.my_role}</span><span>{project.status}</span>
      <Link href={`/projects/${projectId}/settings`}>Project settings and members</Link>
      <Link href={`/projects/${projectId}/sources`}>Sources</Link>
      <Link href={`/projects/${projectId}/evidence`}>Evidence</Link>
      <Link href={`/projects/${projectId}/search`}>Search project</Link></div>
    <section className="panel" style={{marginTop: 24}}><h2>Project context</h2>
      <p className="muted">{project.project_code} · {project.organization || "Organization not specified"}</p>
      <p className="pre">{project.description || "No description provided."}</p>
      <h3>Scope</h3><p className="pre">{project.scope || "Scope has not been defined."}</p>
      <h3>Out of scope</h3><p className="pre">{project.out_of_scope || "No exclusions recorded."}</p>
    </section></>;
}
export default function PageView() { return <Shell><Workspace/></Shell>; }
