"""Provision only named development databases/roles. No default credentials."""

import argparse
import secrets
from pathlib import Path

import psycopg
from psycopg import sql
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=55432)
    parser.add_argument("--password-file", type=Path, default=ROOT / "var/postgres-password.txt")
    args = parser.parse_args()
    env_path = ROOT / "backend/.env"
    if env_path.exists():
        print("backend/.env already exists; configuration was preserved. Run migrations and grants.")
        return
    passwords = {"medical_owner": secrets.token_urlsafe(32), "medical_app": secrets.token_urlsafe(32)}
    with psycopg.connect(
        host=args.host,
        port=args.port,
        dbname="postgres",
        user="postgres",
        password=args.password_file.read_text().strip(),
        autocommit=True,
    ) as conn:
        for role, password in passwords.items():
            if conn.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", (role,)).fetchone():
                raise RuntimeError("Named development roles already exist; manual configuration is required")
            # SQL literal quoting is handled by psycopg, never raw user-string interpolation.
            conn.execute(
                sql.SQL(
                    "CREATE ROLE {} LOGIN PASSWORD {} NOSUPERUSER NOCREATEDB NOCREATEROLE "
                    "NOINHERIT NOREPLICATION NOBYPASSRLS"
                ).format(sql.Identifier(role), sql.Literal(password))
            )
        for database in ("medical_ba", "medical_ba_test"):
            conn.execute(sql.SQL("CREATE DATABASE {} OWNER medical_owner").format(sql.Identifier(database)))
            conn.execute(sql.SQL("REVOKE ALL ON DATABASE {} FROM PUBLIC").format(sql.Identifier(database)))
            conn.execute(
                sql.SQL("GRANT CONNECT ON DATABASE {} TO medical_app").format(sql.Identifier(database))
            )

    def url(role, database):
        value = make_url("postgresql+psycopg://localhost/" + database)
        return value.set(
            username=role, password=passwords[role], host=args.host, port=args.port
        ).render_as_string(hide_password=False)

    env_path.write_text(
        "\n".join(
            [
                "DATABASE_URL=" + url("medical_app", "medical_ba"),
                "MIGRATION_DATABASE_URL=" + url("medical_owner", "medical_ba"),
                "TEST_DATABASE_URL=" + url("medical_app", "medical_ba_test"),
                "TEST_MIGRATION_DATABASE_URL=" + url("medical_owner", "medical_ba_test"),
                "APP_ENV=development",
                'ALLOWED_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]',
                "SESSION_HOURS=8",
                "COOKIE_SECURE=false",
                "LOGIN_MAX_ATTEMPTS=10",
                "LOGIN_WINDOW_SECONDS=300",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print("Development roles/databases created; private credentials written to ignored backend/.env.")


if __name__ == "__main__":
    main()
