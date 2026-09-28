# Backend — Phases 1 and 2

Implemented: Python/FastAPI/Pydantic, SQLAlchemy/Alembic, PostgreSQL and pytest for auth/projects/membership/audit. See [setup](../docs/LOCAL_DEVELOPMENT.md), [architecture](../docs/ARCHITECTURE.md), [schema](../docs/DATA_MODEL.md) and [API](../docs/API_PLAN.md).

Implemented modules own routers/schemas, services, authorization, repositories and models. Phase 2 adds sources/evidence/knowledge, bounded six-format parsers and private local Storage. [Ingestion contract](../docs/INGESTION_AND_STORAGE.md). `app/core/` supplies settings/database/safe errors. Alembic owns schema/RLS; runtime cannot own project tables or bypass policies. AI/domain/job modules remain reserved; no provider/approval engine exists.

From this directory after setup: `.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000`. Run `python -m pytest -q` using that virtual environment and dedicated PostgreSQL test URLs. `uv.lock` pins dependencies; copy `.env.example` only when configuring credentials manually. The documented local setup generates secrets rather than shipping defaults.
