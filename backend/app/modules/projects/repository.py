from sqlalchemy import select, text

from app.modules.auth.models import User
from app.modules.projects.models import Project, ProjectMember


def allocate_project_code(db):
    number = db.scalar(text("SELECT nextval('project_code_seq')"))
    return f"PRJ-{number:03d}"


def membership(db, project_id, user_id):
    return db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
            ProjectMember.status == "ACTIVE",
        )
    )


def project(db, project_id, lock=False):
    query = select(Project).where(Project.id == project_id)
    return db.scalar(query.with_for_update() if lock else query)


def projects_for_user(db, user_id, after, limit):
    query = (
        select(Project, ProjectMember.role)
        .join(ProjectMember)
        .where(ProjectMember.user_id == user_id, ProjectMember.status == "ACTIVE")
    )
    if after:
        query = query.where(Project.id > after)
    return db.execute(query.order_by(Project.id).limit(limit + 1)).all()


def members(db, project_id, after, limit):
    query = (
        select(ProjectMember, User)
        .join(User, User.id == ProjectMember.user_id)
        .where(ProjectMember.project_id == project_id)
    )
    if after:
        query = query.where(ProjectMember.id > after)
    return db.execute(query.order_by(ProjectMember.id).limit(limit + 1)).all()


def member_by_id(db, project_id, member_id):
    return db.scalar(
        select(ProjectMember).where(ProjectMember.project_id == project_id, ProjectMember.id == member_id)
    )
