"""Stable business display-code sequence, independent of internal UUIDs."""

from alembic import op

revision = "0002_project_codes"
down_revision = "0001_foundation"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE SEQUENCE project_code_seq")
    op.execute("""SELECT setval('project_code_seq', coalesce((SELECT max(
        substring(project_code from 5)::bigint) FROM projects
        WHERE project_code ~ '^PRJ-[0-9]{1,12}$'), 0) + 1, false)""")


def downgrade():
    op.execute("DROP SEQUENCE project_code_seq")
