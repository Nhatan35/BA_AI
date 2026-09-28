"use client";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ReactNode, useEffect, useState } from "react";
import Shell from "@/features/Shell";
import { api, message, Project } from "@/lib/api";

export default function KnowledgeWorkspace({children}: {children: (project: Project) => ReactNode}) {
  const {projectId} = useParams<{projectId: string}>();
  const [project, setProject] = useState<Project>();
  const [error, setError] = useState("");
  useEffect(() => { api<Project>(`/projects/${projectId}`).then(setProject).catch(e => setError(message(e))); }, [projectId]);
  return <Shell>{error ? <section className="panel"><h1>Workspace unavailable</h1><p role="alert">{error}</p><Link href="/projects">Back to projects</Link></section> : project ? <>
    <p className="muted">{project.name} · {project.my_role}</p>
    <nav className="project-nav" aria-label="Project navigation">
      <Link href={`/projects/${projectId}`}>Project overview</Link>
      <Link href={`/projects/${projectId}/sources`}>Sources</Link>
      <Link href={`/projects/${projectId}/evidence`}>Evidence</Link>
      <Link href={`/projects/${projectId}/search`}>Search project</Link>
    </nav>{children(project)}</> : <p>Loading project…</p>}</Shell>;
}
