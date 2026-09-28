# Frontend — Phases 1 and 2

Next.js/React/TypeScript with login, projects/create, workspace/settings/members, plus Sources upload/version/parsed viewer, manual Evidence register/detail and project search. `src/features/` holds authenticated/project shells and evidence form; `src/lib/` has typed APIs; `tests/` contains Chromium workflow/isolation tests. See [setup](../docs/LOCAL_DEVELOPMENT.md) and [API contract](../docs/API_PLAN.md).

Use `npm.cmd ci`, `npm.cmd run dev`, `npm.cmd run typecheck`, `npm.cmd run build`. Set BACKEND_URL before build/start for the same-origin API rewrite. `package-lock.json` pins dependencies. Browser tests use dedicated synthetic fixtures/database and require local Chromium; commands are in the setup guide. Backend authorization remains mandatory regardless of hidden buttons or route guards.
