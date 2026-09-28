"""Phase 1 identity, membership, project scope and append-only audit."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001_foundation"
down_revision = None
branch_labels = None
depends_on = None


def uid(name, nullable=False, foreign=None, primary=False):
    args = [sa.ForeignKey(foreign, ondelete="RESTRICT")] if foreign else []
    return sa.Column(name, sa.Uuid(), *args, nullable=nullable, primary_key=primary)


def stamp(name):
    return sa.Column(name, sa.DateTime(timezone=True), nullable=False)


def upgrade():
    op.create_table(
        "users",
        uid("id", primary=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("password_hash", sa.String(512), nullable=False),
        sa.Column("display_name", sa.String(150), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("is_system_admin", sa.Boolean(), nullable=False),
        stamp("created_at"),
        stamp("updated_at"),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.CheckConstraint("email = lower(trim(email))", name="ck_users_normalized_email"),
        sa.CheckConstraint("status IN ('ACTIVE','INACTIVE')", name="ck_users_status"),
    )
    op.create_table(
        "auth_sessions",
        uid("id", primary=True),
        uid("user_id", foreign="users.id"),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        stamp("created_at"),
        stamp("expires_at"),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_auth_sessions_user_id", "auth_sessions", ["user_id"])
    op.create_index("ix_auth_sessions_expires_at", "auth_sessions", ["expires_at"])
    op.create_table(
        "projects",
        uid("id", primary=True),
        sa.Column("project_code", sa.String(40), nullable=False, unique=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("organization", sa.String(200), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("scope", sa.Text(), nullable=False),
        sa.Column("out_of_scope", sa.Text(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        uid("created_by", foreign="users.id"),
        stamp("created_at"),
        stamp("updated_at"),
        sa.CheckConstraint("status IN ('PLANNING','ACTIVE','ON_HOLD','CLOSED')", name="ck_projects_status"),
    )
    op.create_table(
        "project_members",
        uid("id", primary=True),
        uid("project_id", foreign="projects.id"),
        uid("user_id", foreign="users.id"),
        sa.Column("role", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        uid("created_by", foreign="users.id"),
        stamp("created_at"),
        stamp("updated_at"),
        sa.UniqueConstraint("project_id", "user_id", name="uq_members_project_user"),
        sa.UniqueConstraint("project_id", "id", name="uq_members_project_id"),
        sa.CheckConstraint("status IN ('ACTIVE','INACTIVE')", name="ck_members_status"),
        sa.CheckConstraint(
            "role IN ('PROJECT_ADMIN','BA','BUSINESS_OWNER','MEDICAL_SME','TECH','QC','VIEWER')",
            name="ck_members_role",
        ),
    )
    op.create_index("ix_project_members_project_id", "project_members", ["project_id"])
    op.create_index("ix_project_members_user_id", "project_members", ["user_id"])
    op.create_table(
        "audit_logs",
        uid("id", primary=True),
        uid("project_id", foreign="projects.id"),
        uid("actor_user_id", foreign="users.id"),
        sa.Column("action", sa.String(60), nullable=False),
        sa.Column("entity_type", sa.String(60), nullable=False),
        uid("entity_id"),
        stamp("timestamp"),
        sa.Column("safe_metadata", postgresql.JSONB(), nullable=False),
    )
    op.create_index("ix_audit_logs_project_id", "audit_logs", ["project_id"])
    op.create_index("ix_audit_logs_timestamp", "audit_logs", ["timestamp"])
    op.create_table(
        "security_events",
        uid("id", primary=True),
        uid("actor_user_id", nullable=True, foreign="users.id"),
        sa.Column("action", sa.String(60), nullable=False),
        stamp("timestamp"),
    )

    op.execute("CREATE SCHEMA app_private")
    op.execute("""CREATE FUNCTION app_private.actor() RETURNS uuid LANGUAGE sql STABLE AS $$
      SELECT nullif(current_setting('app.user_id', true), '')::uuid
    $$""")
    # Owner bypass is intentional ONLY inside these narrowly scoped authorization predicates.
    # Runtime must be a non-owner without BYPASSRLS; startup and integration tests enforce this.
    op.execute("""CREATE FUNCTION app_private.member(p uuid) RETURNS boolean LANGUAGE sql STABLE
      SECURITY DEFINER SET search_path = pg_catalog, public AS $$
      SELECT EXISTS (SELECT 1 FROM public.project_members m JOIN public.users u ON u.id=m.user_id
        WHERE m.project_id=p AND m.user_id=app_private.actor() AND m.status='ACTIVE' AND u.status='ACTIVE')
    $$""")
    op.execute("""CREATE FUNCTION app_private.admin(p uuid) RETURNS boolean LANGUAGE sql STABLE
      SECURITY DEFINER SET search_path = pg_catalog, public AS $$
      SELECT EXISTS (SELECT 1 FROM public.project_members m JOIN public.users u ON u.id=m.user_id
        WHERE m.project_id=p AND m.user_id=app_private.actor() AND m.status='ACTIVE'
        AND m.role='PROJECT_ADMIN' AND u.status='ACTIVE')
    $$""")
    op.execute("""CREATE FUNCTION app_private.first_member(p uuid) RETURNS boolean LANGUAGE sql STABLE
      SECURITY DEFINER SET search_path = pg_catalog, public AS $$
      SELECT EXISTS (SELECT 1 FROM public.projects WHERE id=p AND created_by=app_private.actor())
      AND NOT EXISTS (SELECT 1 FROM public.project_members WHERE project_id=p)
    $$""")
    for table in ("projects", "project_members", "audit_logs"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY project_read ON projects FOR SELECT USING (app_private.member(id))")
    op.execute("""CREATE POLICY project_insert ON projects FOR INSERT
      WITH CHECK (created_by=app_private.actor())""")
    op.execute("""CREATE POLICY project_update ON projects FOR UPDATE
      USING (app_private.admin(id)) WITH CHECK (app_private.admin(id))""")
    op.execute("""CREATE POLICY member_read ON project_members FOR SELECT
      USING (app_private.member(project_id))""")
    op.execute("""CREATE POLICY member_insert ON project_members FOR INSERT WITH CHECK (
      created_by=app_private.actor() AND (app_private.admin(project_id) OR
      (app_private.first_member(project_id) AND user_id=app_private.actor()
       AND role='PROJECT_ADMIN' AND status='ACTIVE')))""")
    op.execute("""CREATE POLICY member_update ON project_members FOR UPDATE
      USING (app_private.admin(project_id)) WITH CHECK (app_private.admin(project_id))""")
    op.execute("""CREATE POLICY audit_read ON audit_logs FOR SELECT USING (app_private.admin(project_id))""")
    op.execute("""CREATE POLICY audit_insert ON audit_logs FOR INSERT
      WITH CHECK (actor_user_id=app_private.actor() AND app_private.member(project_id))""")
    op.execute("""CREATE FUNCTION app_private.no_audit_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
      BEGIN RAISE EXCEPTION 'Audit history is append-only'; END $$""")
    for table in ("audit_logs", "security_events"):
        op.execute(f"""CREATE TRIGGER immutable_audit BEFORE UPDATE OR DELETE ON {table}
          FOR EACH ROW EXECUTE FUNCTION app_private.no_audit_mutation()""")
    op.execute("""CREATE FUNCTION app_private.stable_project() RETURNS trigger LANGUAGE plpgsql AS $$
      BEGIN IF NEW.id<>OLD.id OR NEW.project_code<>OLD.project_code OR NEW.created_by<>OLD.created_by THEN
        RAISE EXCEPTION 'Project identity is immutable'; END IF; RETURN NEW; END $$""")
    op.execute("""CREATE TRIGGER stable_project BEFORE UPDATE ON projects
      FOR EACH ROW EXECUTE FUNCTION app_private.stable_project()""")
    op.execute("""CREATE FUNCTION app_private.stable_member() RETURNS trigger LANGUAGE plpgsql AS $$
      BEGIN IF NEW.id<>OLD.id OR NEW.project_id<>OLD.project_id OR NEW.user_id<>OLD.user_id
        OR NEW.created_by<>OLD.created_by THEN RAISE EXCEPTION 'Membership identity is immutable';
      END IF; RETURN NEW; END $$""")
    op.execute("""CREATE TRIGGER stable_member BEFORE UPDATE ON project_members
      FOR EACH ROW EXECUTE FUNCTION app_private.stable_member()""")
    op.execute("REVOKE ALL ON ALL FUNCTIONS IN SCHEMA app_private FROM PUBLIC")


def downgrade():
    for table in ("security_events", "audit_logs", "project_members", "projects", "auth_sessions", "users"):
        op.drop_table(table)
    op.execute("DROP SCHEMA app_private CASCADE")
