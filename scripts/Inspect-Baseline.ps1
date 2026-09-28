param([string]$Root = (Split-Path -Parent $PSScriptRoot))
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression.FileSystem
$rootPath = (Resolve-Path -LiteralPath $Root).Path
$baselineFiles = @(Get-ChildItem -LiteralPath $rootPath -Directory | Where-Object { $_.Name -match '^\d{2}_' } | Get-ChildItem -Recurse -File)
$baselineFiles += Get-Item -LiteralPath (Join-Path $rootPath 'manifest.json')
$inventory = @($baselineFiles | Sort-Object FullName | ForEach-Object {
    [ordered]@{ path = $_.FullName.Substring($rootPath.Length + 1).Replace('\','/'); bytes = $_.Length; sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash }
})
$archive = [System.IO.Compression.ZipFile]::OpenRead((Join-Path $rootPath '11_Master_Tracker/Medical_BA_AI_Master_Tracker.xlsx'))
function Read-Part([string]$Name) {
    $entry = $archive.GetEntry($Name)
    if ($null -eq $entry) { return $null }
    $reader = [System.IO.StreamReader]::new($entry.Open())
    try { return $reader.ReadToEnd() } finally { $reader.Dispose() }
}
try {
    [xml]$workbook = Read-Part 'xl/workbook.xml'
    [xml]$rels = Read-Part 'xl/_rels/workbook.xml.rels'
    [xml]$shared = Read-Part 'xl/sharedStrings.xml'
    $strings = @($shared.sst.si | ForEach-Object { $_.InnerText })
    $sheets = @(foreach ($sheet in $workbook.workbook.sheets.sheet) {
        $relId = $sheet.GetAttribute('id','http://schemas.openxmlformats.org/officeDocument/2006/relationships')
        $target = ($rels.Relationships.Relationship | Where-Object { $_.Id -eq $relId }).Target
        $part = if ($target.StartsWith('/')) { $target.TrimStart('/') } else { 'xl/' + $target }
        [xml]$ws = Read-Part $part
        $rows = @(foreach ($row in $ws.worksheet.sheetData.row) {
            $cells = @(foreach ($cell in $row.c) {
                $value = if ($cell.t -eq 's') { $strings[[int]$cell.v] } elseif ($cell.t -eq 'inlineStr') { $cell.is.InnerText } else { [string]$cell.v }
                if ($value -or $cell.f) { [ordered]@{ address = [string]$cell.r; value = $value; formula = [string]$cell.f } }
            })
            if ($cells.Count) { [ordered]@{ row = [int]$row.r; cells = $cells } }
        })
        $validations = @(foreach ($validation in $ws.worksheet.dataValidations.dataValidation) {
            if ($validation) { [ordered]@{ range = [string]$validation.sqref; type = [string]$validation.type; formula = [string]$validation.formula1 } }
        })
        [ordered]@{ name = [string]$sheet.name; part = $part; rows = $rows; validations = $validations }
    })
    [ordered]@{ inventory = $inventory; sheet_count = $sheets.Count; sheets = $sheets } | ConvertTo-Json -Depth 12
} finally { $archive.Dispose() }
