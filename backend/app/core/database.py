from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


@lru_cache
def get_engine():
    return create_engine(get_settings().database_url, pool_pre_ping=True, hide_parameters=True)


def get_db() -> Generator[Session]:
    with sessionmaker(get_engine(), expire_on_commit=False)() as session:
        yield session


def set_actor(db: Session, user_id):
    db.execute(text("SELECT set_config('app.user_id', :id, true)"), {"id": str(user_id)})


def verify_runtime_role():
    with get_engine().connect() as connection:
        unsafe = connection.execute(
            text("""
            SELECT r.rolsuper OR r.rolbypassrls OR EXISTS (
              SELECT 1 FROM pg_class c WHERE c.relname IN (
                'projects','project_members','audit_logs','sources',
                'source_versions','parse_runs','parsed_sections','evidence')
              AND c.relowner = r.oid AND c.relnamespace = 'public'::regnamespace
            ) FROM pg_roles r WHERE r.rolname = current_user
        """)
        ).scalar_one()
        if unsafe:
            raise RuntimeError("Runtime database role must not own project tables or bypass RLS")
        protected = connection.execute(
            text("""
            SELECT count(*)=8 AND bool_and(relrowsecurity) FROM pg_class
            WHERE relname IN ('projects','project_members','audit_logs','sources',
              'source_versions','parse_runs','parsed_sections','evidence')
            AND relnamespace='public'::regnamespace
        """)
        ).scalar_one()
        if not protected:
            raise RuntimeError("Apply migrations and enable project row policies before starting the backend")
