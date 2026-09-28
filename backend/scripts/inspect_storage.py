"""Read-only operator reconciliation: counts only, no content or automatic deletion."""

from sqlalchemy import create_engine, text

from app.core.config import get_settings


def main():
    settings = get_settings()
    with create_engine(settings.migration_database_url, hide_parameters=True).connect() as connection:
        registered = set(connection.execute(text("SELECT storage_key FROM source_versions")).scalars())
        pending = connection.execute(
            text("SELECT count(*) FROM parse_runs WHERE parser_status IN ('PENDING','PROCESSING')")
        ).scalar_one()
    root = settings.storage_root.resolve()
    disk = {path.relative_to(root).as_posix() for path in root.glob("*/*/*.bin") if path.is_file()}
    print(
        f"Registered objects: {len(registered)}; on disk: {len(disk)}; "
        f"missing: {len(registered - disk)}; unreferenced: {len(disk - registered)}; "
        f"unfinished parses: {pending}"
    )


if __name__ == "__main__":
    main()
