param([string]$Root = (Split-Path -Parent $PSScriptRoot))
$ErrorActionPreference = 'Stop'
$rootPath = (Resolve-Path -LiteralPath $Root).Path
$snapshot = Get-Content -LiteralPath (Join-Path $rootPath 'docs/baseline-inspection.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$current = (& (Join-Path $PSScriptRoot 'Inspect-Baseline.ps1') -Root $rootPath) | ConvertFrom-Json
$failures = [System.Collections.Generic.List[string]]::new()
$checks = [System.Collections.Generic.List[string]]::new()

if ($snapshot.inventory.Count -ne 53 -or $current.inventory.Count -ne 53) { $failures.Add('Expected 53 original baseline files.') }
foreach ($file in $snapshot.inventory) {
    $actual = @($current.inventory | Where-Object { $_.path -eq $file.path })
    if ($actual.Count -ne 1 -or $actual[0].sha256 -ne $file.sha256) { $failures.Add('Baseline changed or missing: ' + $file.path) }
}
$checks.Add('All 53 original files match the saved SHA-256 inventory.')

$expectedSheets = @('Dashboard','Project','Sources','Stakeholders','Requirements','Evidence','Questions','Assumptions','Decisions','Risks','Business_Rules','Data_Dictionary','Roles_Permissions','Integrations','NFR','Traceability','Change_Requests','UAT','Glossary','Regulations','AI_Evaluation','AI_Incidents','Development_Scope')
if ($current.sheet_count -ne 23 -or (Compare-Object $expectedSheets @($current.sheets.name))) { $failures.Add('Workbook sheet inventory differs from the inspected 23 sheets.') }
if (($snapshot.sheets | ConvertTo-Json -Depth 12 -Compress) -cne ($current.sheets | ConvertTo-Json -Depth 12 -Compress)) { $failures.Add('Workbook contents differ from the saved inspection.') }
$checks.Add('All 23 workbook sheets, populated cells, formulas and validation lists match the snapshot.')

$requiredDocs = @('PRODUCT_UNDERSTANDING.md','BASELINE_ASSESSMENT.md','ARCHITECTURE.md','DATA_MODEL.md','API_PLAN.md','IMPLEMENTATION_PLAN.md','PHASE_0_VALIDATION.md')
foreach ($doc in $requiredDocs) {
    $path = Join-Path $rootPath ('docs/' + $doc)
    if (-not (Test-Path -LiteralPath $path) -or (Get-Item -LiteralPath $path).Length -eq 0) { $failures.Add('Required document missing/empty: ' + $doc) }
}
$plan = Get-Content -LiteralPath (Join-Path $rootPath 'docs/IMPLEMENTATION_PLAN.md') -Raw -Encoding UTF8
1..12 | ForEach-Object { $epic = 'EPIC-{0:D2}' -f $_; if (-not $plan.Contains($epic)) { $failures.Add('Missing epic mapping: ' + $epic) } }
$model = Get-Content -LiteralPath (Join-Path $rootPath 'docs/DATA_MODEL.md') -Raw -Encoding UTF8
$entities = @('User','Project','ProjectMember','Stakeholder','Source','SourceVersion','Evidence','Requirement','RequirementVersion','RequirementRelation','BusinessRule','Question','Assumption','Decision','Risk','GlossaryTerm','RegulationReference','ChangeRequest','ImpactItem','Artifact','AIAnalysisRun','AIOutputItem','AuditLog','AIEvaluationCase','AIIncident','DataDictionaryEntry','RolePermission','Integration','NFRDetail','UATScenario','AcceptanceCriteria','HumanConfirmation','Review')
foreach ($entity in $entities) { if ($model -notmatch ('\b' + [regex]::Escape($entity) + '\b')) { $failures.Add('Missing planned entity: ' + $entity) } }
$checks.Add('Seven review/validation documents, all 12 epic mappings and 33 key entity names are present (presence checks, not design proof).')

$docPaths = @(Get-Item -LiteralPath (Join-Path $rootPath 'README.md'))
$docPaths += @(Get-ChildItem -LiteralPath (Join-Path $rootPath 'docs') -Filter '*.md' -File)
foreach ($area in @('backend','frontend','infra')) { $docPaths += Get-Item -LiteralPath (Join-Path $rootPath ($area + '/README.md')) }
$linkCount = 0
foreach ($doc in $docPaths) {
    $content = Get-Content -LiteralPath $doc.FullName -Raw -Encoding UTF8
    foreach ($match in [regex]::Matches($content, '\[[^\]]+\]\(([^)]+)\)')) {
        $target = $match.Groups[1].Value
        if ($target -match '^(https?://|#)') { continue }
        $target = ($target -split '#',2)[0]
        if (-not (Test-Path -LiteralPath (Join-Path $doc.DirectoryName $target))) { $failures.Add('Broken local link in ' + $doc.Name + ': ' + $target) }
        $linkCount++
    }
}
$checks.Add("All $linkCount local Markdown file links resolve; external URLs and heading anchors are not tested.")
$structure = @('frontend/src/app','frontend/src/features','frontend/src/lib','frontend/tests','backend/app/core','backend/app/modules','backend/app/storage','backend/app/ai','backend/app/jobs','backend/migrations/versions','backend/tests/unit','backend/tests/integration','backend/tests/evaluation','infra')
foreach ($relative in $structure) { if (-not (Test-Path -LiteralPath (Join-Path $rootPath $relative) -PathType Container)) { $failures.Add('Missing structure: ' + $relative) } }
$checks.Add('Planned frontend/backend/infra, migration and test directories exist.')
if ($failures.Count) {
    foreach ($failure in $failures) { Write-Output ('FAIL: ' + $failure) }
    exit 1
}
foreach ($check in $checks) { Write-Output ('PASS: ' + $check) }
Write-Output 'Phase 0 documentation checks passed. This script does not test application behavior, security or migrations.'
