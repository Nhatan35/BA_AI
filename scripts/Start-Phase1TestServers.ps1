$ErrorActionPreference = 'Stop'
$workspace = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path -LiteralPath (Join-Path $workspace 'var/e2e-fixtures.json'))) { throw 'Run backend/scripts/seed_e2e.py first.' }
$values = @{}
Get-Content -LiteralPath (Join-Path $workspace 'backend/.env') | ForEach-Object {
    if ($_ -match '^([A-Z_]+)=(.*)$') { $values[$Matches[1]] = $Matches[2] }
}
$env:DATABASE_URL = $values['TEST_DATABASE_URL']
$env:MIGRATION_DATABASE_URL = $values['TEST_MIGRATION_DATABASE_URL']
$env:APP_ENV = 'test'
$env:STORAGE_ROOT = Join-Path $workspace 'var/e2e-storage'
$env:LOGIN_MAX_ATTEMPTS = '1000'
$env:ALLOWED_ORIGINS = '["http://localhost:3000","http://127.0.0.1:3000"]'
$env:PYTHONDONTWRITEBYTECODE = '1'
$backend = Start-Process -FilePath (Join-Path $workspace 'backend/.venv/Scripts/python.exe') -ArgumentList @('-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8001') -WorkingDirectory (Join-Path $workspace 'backend') -WindowStyle Hidden -RedirectStandardOutput (Join-Path $workspace 'var/test-backend.out.log') -RedirectStandardError (Join-Path $workspace 'var/test-backend.err.log') -PassThru
$env:BACKEND_URL = 'http://127.0.0.1:8001'
$env:NEXT_TELEMETRY_DISABLED = '1'
$frontend = Start-Process -FilePath (Get-Command node).Source -ArgumentList @('node_modules/next/dist/bin/next','dev','--hostname','127.0.0.1','--port','3000') -WorkingDirectory (Join-Path $workspace 'frontend') -WindowStyle Hidden -RedirectStandardOutput (Join-Path $workspace 'var/test-frontend.out.log') -RedirectStandardError (Join-Path $workspace 'var/test-frontend.err.log') -PassThru
@{backend = $backend.Id; frontend = $frontend.Id} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $workspace 'var/test-server-pids.json')
Write-Output "Test backend PID $($backend.Id), frontend PID $($frontend.Id). Stop these test servers after verification."
