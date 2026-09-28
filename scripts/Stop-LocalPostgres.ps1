$ErrorActionPreference = 'Stop'
$workspace = Split-Path -Parent $PSScriptRoot
$bin = Join-Path $workspace '.tools/postgresql/pgsql/bin'
$data = Join-Path $workspace 'var/postgres-data'
& (Join-Path $bin 'pg_ctl.exe') -D $data -m fast -w stop
if ($LASTEXITCODE -ne 0) { throw 'PostgreSQL shutdown failed.' }
