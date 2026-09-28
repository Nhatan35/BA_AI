from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from fastapi import Depends

from app.core.errors import fail
from app.modules.auth.dependencies import DB, Current
from app.modules.auth.models import User
from app.modules.projects import repository
from app.modules.projects.models import Project, ProjectMember


@dataclass(frozen=True)
class ProjectContext:
    user: User
    project: Project
    membership: ProjectMember

    def require_admin(self):
        if self.membership.role != "PROJECT_ADMIN":
            fail(403, "FORBIDDEN", "Project administrator permission is required.")


def authorized_project(project_id: UUID, identity: Current, db: DB) -> ProjectContext:
    member = repository.membership(db, project_id, identity.user.id)
    project = repository.project(db, project_id) if member else None
    if member is None or project is None:
        fail(404, "NOT_FOUND", "Project was not found.")
    return ProjectContext(user=identity.user, project=project, membership=member)


Context = Annotated[ProjectContext, Depends(authorized_project)]
