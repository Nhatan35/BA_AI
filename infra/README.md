# Phase 1 local infrastructure

Tested: workspace-local PostgreSQL 17.11 server/client, private loopback cluster and separate runtime/owner credentials. Alternative: `compose.yaml` for PostgreSQL with file secret and persistent volume. Docker startup is NOT RUN because Docker is absent. Full [Windows commands](../docs/LOCAL_DEVELOPMENT.md) include both paths.

`var/`, `.tools/`, virtual environments and `.env` files are ignored. Native database data/password files and synthetic browser fixtures live there. No storage/ingestion/AI service is implemented. Production TLS, image digests, retention, backups and deployment review remain later release work. Never commit credentials or real patient data.
