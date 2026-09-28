$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$workspace = Split-Path -Parent $PSScriptRoot
$tools = Join-Path $workspace '.tools'
New-Item -ItemType Directory -Path $tools -Force | Out-Null
function Download-Checked([string]$Url, [string]$Path, [string]$Sha256) {
    if (-not (Test-Path -LiteralPath $Path)) { Invoke-WebRequest -UseBasicParsing -Uri $Url -OutFile $Path }
    if ((Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash -ne $Sha256) { throw "Archive checksum mismatch: $Path" }
}
Download-Checked 'https://github.com/astral-sh/uv/releases/download/0.12.19/uv-x86_64-pc-windows-msvc.zip' (Join-Path $tools 'uv.zip') '6DBB02D79E419522F1C500F0ADB1CDDCFF0CDA7D59B0D66EA7F5E3B4A1B2F5F0'
Expand-Archive -LiteralPath (Join-Path $tools 'uv.zip') -DestinationPath (Join-Path $tools 'uv') -Force
$env:UV_PYTHON_INSTALL_DIR = Join-Path $tools 'python'
$env:UV_CACHE_DIR = Join-Path $tools 'cache'
& (Join-Path $tools 'uv/uv.exe') python install 3.13.15 --no-bin
if ($LASTEXITCODE -ne 0) { throw 'Python installation failed.' }
Download-Checked 'https://sbp.enterprisedb.com/getfile.jsp?fileid=1260569' (Join-Path $tools 'postgresql.zip') 'B9424EE7BC60B52450FF910A3630225DF32E633F3CB29C1D126D9299D59AEA28'
$existingServer = Join-Path $tools 'postgresql/pgsql/bin/postgres.exe'
if (Test-Path -LiteralPath $existingServer) {
    $version = & $existingServer --version
    if ($version -notmatch '17\.11') { throw 'Existing workspace PostgreSQL differs from the pinned version.' }
    Write-Output $version
    Write-Output 'Workspace tools already installed; running PostgreSQL files were preserved.'
    exit 0
}
# Skip pgAdmin/StackBuilder to avoid Windows path-length failures. Extract only server/client files.
Add-Type -AssemblyName System.IO.Compression.FileSystem
$archive = [System.IO.Compression.ZipFile]::OpenRead((Join-Path $tools 'postgresql.zip'))
$target = [System.IO.Path]::GetFullPath((Join-Path $tools 'postgresql'))
try {
    foreach ($entry in $archive.Entries) {
        if ($entry.FullName -notmatch '^pgsql/(bin/|lib/|share/|server_license\.txt|commandlinetools_3rd_party_licenses\.txt)') { continue }
        $destination = [System.IO.Path]::GetFullPath((Join-Path $target $entry.FullName))
        if (-not $destination.StartsWith($target + '\', [System.StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe archive path.' }
        if ($entry.FullName.EndsWith('/')) { New-Item -ItemType Directory -Path $destination -Force | Out-Null; continue }
        New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
        [System.IO.Compression.ZipFileExtensions]::ExtractToFile($entry, $destination, $true)
    }
} finally { $archive.Dispose() }
& (Join-Path $tools 'postgresql/pgsql/bin/postgres.exe') --version
Write-Output 'Workspace tools ready. No system PATH, registry or Windows service was changed.'
