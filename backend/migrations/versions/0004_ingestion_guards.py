"""Constrain append operations and human confirmation at the database boundary."""

from alembic import op

revision = "0004_ingestion_guards"
down_revision = "0003_ingestion"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("DROP POLICY scoped_insert ON evidence")
    op.execute("""CREATE POLICY scoped_insert ON evidence FOR INSERT WITH CHECK (
      app_private.editor(project_id) AND created_by=app_private.actor()
      AND confirmed_by IS NULL AND confirmed_at IS NULL)""")
    op.execute("""CREATE FUNCTION app_private.append_section() RETURNS trigger LANGUAGE plpgsql AS $$
      BEGIN IF NOT EXISTS (SELECT 1 FROM public.parse_runs p WHERE p.id=NEW.parse_run_id
        AND p.project_id=NEW.project_id AND p.parser_status='PROCESSING'
        AND p.created_by=app_private.actor())
      THEN RAISE EXCEPTION 'Sections require an authorized running parse'; END IF;
      RETURN NEW; END $$""")
    op.execute("""CREATE TRIGGER append_section BEFORE INSERT ON parsed_sections
      FOR EACH ROW EXECUTE FUNCTION app_private.append_section()""")
    op.create_check_constraint(
        "ck_versions_key",
        "source_versions",
        "storage_key = project_id::text || '/' || source_id::text || '/' || id::text || '.bin'",
    )
    op.create_check_constraint("ck_parse_attempt", "parse_runs", "attempt_number > 0")
    op.create_check_constraint("ck_sections_ordinal", "parsed_sections", "ordinal > 0")


def downgrade():
    op.drop_constraint("ck_sections_ordinal", "parsed_sections", type_="check")
    op.drop_constraint("ck_parse_attempt", "parse_runs", type_="check")
    op.drop_constraint("ck_versions_key", "source_versions", type_="check")
    op.execute("DROP TRIGGER append_section ON parsed_sections")
    op.execute("DROP FUNCTION app_private.append_section()")
    op.execute("DROP POLICY scoped_insert ON evidence")
    op.execute("""CREATE POLICY scoped_insert ON evidence FOR INSERT WITH CHECK (
      app_private.editor(project_id) AND created_by=app_private.actor())""")
