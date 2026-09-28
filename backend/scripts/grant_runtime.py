"""Apply explicit runtime privileges after each migration; owner/operator only."""

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from app.core.config import get_settings


def main():
    settings = get_settings()
    role = make_url(settings.database_url).username
    if role != "medical_app":
        raise RuntimeError("This local grant script expects the dedicated medical_app runtime role")
    with create_engine(settings.migration_database_url, hide_parameters=True).begin() as conn:
        conn.execute(text("REVOKE CREATE ON SCHEMA public FROM PUBLIC"))
        conn.execute(text("GRANT USAGE ON SCHEMA public, app_private TO medical_app"))
        conn.execute(text("GRANT USAGE ON SEQUENCE project_code_seq TO medical_app"))
        conn.execute(text("GRANT SELECT ON users TO medical_app"))
        conn.execute(text("GRANT SELECT, INSERT, UPDATE ON auth_sessions TO medical_app"))
        conn.execute(text("GRANT SELECT, INSERT, UPDATE ON projects, project_members TO medical_app"))
        conn.execute(text("GRANT SELECT, INSERT ON audit_logs TO medical_app"))
        conn.execute(text("GRANT SELECT, INSERT, UPDATE ON sources, parse_runs, evidence TO medical_app"))
        conn.execute(text("GRANT SELECT, INSERT ON source_versions, parsed_sections TO medical_app"))
        conn.execute(
            text(
                "GRANT EXECUTE ON FUNCTION app_private.editor(uuid), "
                "app_private.confirmer(uuid) TO medical_app"
            )
        )
        conn.execute(text("GRANT INSERT ON security_events TO medical_app"))
        conn.execute(
            text(
                "GRANT EXECUTE ON FUNCTION app_private.actor(), app_private.member(uuid), "
                "app_private.admin(uuid), app_private.first_member(uuid) TO medical_app"
            )
        )
    print("Runtime grants applied; no owner, BYPASSRLS, delete or audit-update privileges.")


if __name__ == "__main__":
    main()
