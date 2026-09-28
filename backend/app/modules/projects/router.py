from uuid import UUID

from fastapi import APIRouter, Query

from app.modules.auth.dependencies import DB, Current
from app.modules.projects import repository, service
from app.modules.projects.authorization import Context
from app.modules.projects.schemas import (
    MemberCreate,
    MemberList,
    MemberRead,
    MemberUpdate,
    ProjectCreate,
    ProjectList,
    ProjectRead,
    ProjectUpdate,
)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectRead, status_code=201)
def create(body: ProjectCreate, identity: Current, db: DB):
    return service.create_project(db, identity.user, body)


@router.get("", response_model=ProjectList)
def projects(identity: Current, db: DB, after: UUID | None = None, limit: int = Query(50, ge=1, le=100)):
    rows = repository.projects_for_user(db, identity.user.id, after, limit)
    return ProjectList(
        items=[service.project_read(p, r) for p, r in rows[:limit]],
        next_cursor=rows[limit - 1][0].id if len(rows) > limit else None,
    )


@router.get("/{project_id}", response_model=ProjectRead)
def detail(context: Context):
    return service.project_read(context.project, context.membership.role)


@router.patch("/{project_id}", response_model=ProjectRead)
def update(body: ProjectUpdate, context: Context, db: DB):
    return service.update_project(db, context, body)


@router.get("/{project_id}/members", response_model=MemberList)
def members(context: Context, db: DB, after: UUID | None = None, limit: int = Query(50, ge=1, le=100)):
    rows = repository.members(db, context.project.id, after, limit)
    return MemberList(
        items=[service.member_read(m, u) for m, u in rows[:limit]],
        next_cursor=rows[limit - 1][0].id if len(rows) > limit else None,
    )


@router.get("/{project_id}/members/{member_id}", response_model=MemberRead)
def member(member_id: UUID, context: Context, db: DB):
    from app.core.errors import fail
    from app.modules.auth.models import User

    result = repository.member_by_id(db, context.project.id, member_id)
    if result is None:
        fail(404, "NOT_FOUND", "Member was not found.")
    return service.member_read(result, db.get(User, result.user_id))


@router.post("/{project_id}/members", response_model=MemberRead, status_code=201)
def add(body: MemberCreate, context: Context, db: DB):
    return service.add_member(db, context, body)


@router.patch("/{project_id}/members/{member_id}", response_model=MemberRead)
def change(member_id: UUID, body: MemberUpdate, context: Context, db: DB):
    return service.update_member(db, context, member_id, body)
