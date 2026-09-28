import uuid

from sqlalchemy.exc import IntegrityError

from app.core.errors import fail
from app.modules.audit.service import audit
from app.modules.auth.models import User
from app.modules.auth.repository import find_user
from app.modules.projects import repository
from app.modules.projects.models import Project, ProjectMember
from app.modules.projects.schemas import MemberRead, ProjectRead


def project_read(project, role):
    data = {key: getattr(project, key) for key in ProjectRead.model_fields if key != "my_role"}
    return ProjectRead(**data, my_role=role)


def member_read(member, user):
    return MemberRead(
        id=member.id,
        project_id=member.project_id,
        user_id=member.user_id,
        email=user.email,
        display_name=user.display_name,
        role=member.role,
        status=member.status,
        revision=member.revision,
    )


def create_project(db, user, body):
    project_id = uuid.uuid4()
    project = Project(
        id=project_id,
        project_code=repository.allocate_project_code(db),
        created_by=user.id,
        **body.model_dump(),
    )
    db.add(project)
    db.flush()
    member = ProjectMember(project_id=project_id, user_id=user.id, role="PROJECT_ADMIN", created_by=user.id)
    db.add(member)
    db.flush()
    audit(db, user, project_id, "PROJECT_CREATED", "Project", project_id)
    audit(
        db,
        user,
        project_id,
        "MEMBERSHIP_CREATED",
        "ProjectMember",
        member.id,
        {"role": member.role, "status": member.status},
    )
    result = project_read(project, member.role)
    db.commit()
    return result


def lock_and_authorize(db, context):
    # Serialize project administration, then recheck membership after waiting for the lock.
    project = repository.project(db, context.project.id, lock=True)
    member = repository.membership(db, context.project.id, context.user.id)
    if project is None or member is None:
        fail(404, "NOT_FOUND", "Project was not found.")
    db.refresh(member)
    if member.status != "ACTIVE" or member.role != "PROJECT_ADMIN":
        fail(403, "FORBIDDEN", "Project administrator permission is required.")


def update_project(db, context, body):
    context.require_admin()
    lock_and_authorize(db, context)
    db.refresh(context.project)
    if body.expected_revision != context.project.revision:
        fail(409, "STALE_REVISION", "Project changed; refresh before editing.")
    old_revision = context.project.revision
    for key, value in body.model_dump(exclude={"expected_revision"}).items():
        setattr(context.project, key, value)
    context.project.revision += 1
    audit(
        db,
        context.user,
        context.project.id,
        "PROJECT_UPDATED",
        "Project",
        context.project.id,
        {"from_revision": old_revision, "to_revision": context.project.revision},
    )
    result = project_read(context.project, context.membership.role)
    db.commit()
    return result


def add_member(db, context, body):
    context.require_admin()
    lock_and_authorize(db, context)
    user = find_user(db, str(body.email))
    if user is None or user.status != "ACTIVE":
        fail(422, "USER_UNAVAILABLE", "The account cannot be added; ask the operator to provision it.")
    member = ProjectMember(
        project_id=context.project.id, user_id=user.id, role=body.role, created_by=context.user.id
    )
    db.add(member)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        fail(409, "MEMBERSHIP_EXISTS", "Membership already exists; update it instead.")
    audit(
        db,
        context.user,
        context.project.id,
        "MEMBERSHIP_CREATED",
        "ProjectMember",
        member.id,
        {"role": member.role, "status": member.status},
    )
    result = member_read(member, user)
    db.commit()
    return result


def update_member(db, context, member_id, body):
    context.require_admin()
    lock_and_authorize(db, context)
    member = repository.member_by_id(db, context.project.id, member_id)
    if member is None:
        fail(404, "NOT_FOUND", "Member was not found.")
    if member.user_id == context.user.id:
        fail(409, "SELF_MEMBERSHIP_CHANGE", "Another project administrator must change your membership.")
    if member.revision != body.expected_revision:
        fail(409, "STALE_REVISION", "Membership changed; refresh before editing.")
    old_role, old_status = member.role, member.status
    metadata = {
        "old_role": old_role,
        "new_role": body.role,
        "old_status": old_status,
        "new_status": body.status,
    }
    audit(db, context.user, context.project.id, "MEMBERSHIP_UPDATED", "ProjectMember", member.id, metadata)
    if old_role != body.role:
        audit(
            db, context.user, context.project.id, "PROJECT_ROLE_CHANGED", "ProjectMember", member.id, metadata
        )
    member.role, member.status = body.role, body.status
    member.revision += 1
    db.flush()
    result = member_read(member, db.get(User, member.user_id))
    db.commit()
    return result
