$ErrorActionPreference = 'Stop'
$workspace = Split-Path -Parent $PSScriptRoot
$pidFile = Join-Path $workspace 'var/test-server-pids.json'
if (-not (Test-Path -LiteralPath $pidFile)) { Write-Output 'No test-server PID record.'; exit 0 }
$record = Get-Content -LiteralPath $pidFile -Raw | ConvertFrom-Json
$processes = @(Get-CimInstance Win32_Process)
function Stop-Descendants([int]$ParentId) {
    foreach ($child in @($processes | Where-Object { $_.ParentProcessId -eq $ParentId })) {
        Stop-Descendants $child.ProcessId
        Stop-Process -Id $child.ProcessId -Force -ErrorAction SilentlyContinue
    }
}
foreach ($serverId in @($record.backend, $record.frontend)) {
    $process = $processes | Where-Object { $_.ProcessId -eq $serverId }
    if ($process -and $process.CommandLine -match '(uvicorn app\.main:app|node_modules[\\/]next[\\/]dist[\\/]bin[\\/]next)') {
        Stop-Descendants $serverId
        Stop-Process -Id $serverId -Force -ErrorAction SilentlyContinue
    }
}
Write-Output 'Recorded Phase 1 test-server processes stopped; PostgreSQL remains available.'
