param([int]$Port = 55432)
$ErrorActionPreference = 'Stop'
$workspace = Split-Path -Parent $PSScriptRoot
$bin = Join-Path $workspace '.tools/postgresql/pgsql/bin'
if (-not (Test-Path -LiteralPath (Join-Path $bin 'pg_ctl.exe'))) { throw 'Install/extract the official PostgreSQL binaries first; see LOCAL_DEVELOPMENT.md.' }
$data = Join-Path $workspace 'var/postgres-data'
$passwordFile = Join-Path $workspace 'var/postgres-password.txt'
New-Item -ItemType Directory -Path (Join-Path $workspace 'var') -Force | Out-Null
if (-not (Test-Path -LiteralPath $passwordFile)) {
    $bytes = New-Object byte[] 32
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
    [System.IO.File]::WriteAllText($passwordFile, [Convert]::ToBase64String($bytes))
}
if (-not (Test-Path -LiteralPath (Join-Path $data 'PG_VERSION'))) {
    & (Join-Path $bin 'initdb.exe') -D $data -U postgres --encoding=UTF8 --locale=C --auth=scram-sha-256 --pwfile=$passwordFile
    if ($LASTEXITCODE -ne 0) { throw 'PostgreSQL initialization failed.' }
    Add-Content -LiteralPath (Join-Path $data 'postgresql.conf') -Value "`nlisten_addresses = '127.0.0.1'`nport = $Port"
}
& (Join-Path $bin 'pg_ctl.exe') status -D $data | Out-Null
if ($LASTEXITCODE -eq 0) { Write-Output 'Workspace PostgreSQL is already running.'; exit 0 }
$log = Join-Path $workspace 'var/postgresql.log'
$process = Start-Process -FilePath (Join-Path $bin 'pg_ctl.exe') -ArgumentList @('-D', ('"' + $data + '"'), '-l', ('"' + $log + '"'), '-w', 'start') -WindowStyle Hidden -Wait -PassThru
if ($process.ExitCode -ne 0) { throw 'PostgreSQL startup failed; inspect var/postgresql.log.' }
Write-Output "Workspace PostgreSQL started on 127.0.0.1:$Port."
