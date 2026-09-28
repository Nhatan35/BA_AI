# Medical BA AI — Phase 2 ingestion and evidence

The accepted Phase 1 provides authentication, isolated projects, memberships and audit. Phase 2 adds six-format ingestion, immutable raw versions, parsed content, manual evidence and project search using FastAPI/PostgreSQL and Next.js. Original files in `00_START_HERE/` through `14_Development/` are preserved. Start with [local development](docs/LOCAL_DEVELOPMENT.md), [ingestion/storage](docs/INGESTION_AND_STORAGE.md) and [Phase 2 result](docs/PHASE_2_RESULT.md).

Start the technical review with:

1. [Product understanding](docs/PRODUCT_UNDERSTANDING.md)
2. [Baseline findings and open decisions](docs/BASELINE_ASSESSMENT.md)
3. [Architecture](docs/ARCHITECTURE.md)
4. [Data model](docs/DATA_MODEL.md)
5. [API plan](docs/API_PLAN.md)
6. [Implementation plan and epic coverage](docs/IMPLEMENTATION_PLAN.md)
7. [Phase 0 validation](docs/PHASE_0_VALIDATION.md)

The stack remains Next.js/React/TypeScript, FastAPI/Pydantic/SQLAlchemy/Alembic and PostgreSQL, with locked dependencies and native Windows development. Private local storage has an adapter boundary. Docker Compose remains an unexecuted alternative. AI, BA domain registers, governance, full traceability, changes and artifacts await their phases. Work stops after Phase 2 for review.

Read-only assessment commands (PowerShell, from the workspace root):

```powershell
powershell -NoProfile -File scripts/Inspect-Baseline.ps1
powershell -NoProfile -File scripts/Validate-Phase0.ps1
```

The first prints original-file hashes and workbook contents; the second verifies the saved assessment and documentation. Both use built-in .NET ZIP/XML APIs and require no Python/Excel package installation.
