<#
  setup.ps1 - Wire up the Claude Code layer (.claude) for the datn monorepo.

  This machine has no Developer Mode / no admin, so symlinks cannot be created.
  Instead we use:
    - Directory Junction (mklink /J) for folders -> no admin required
    - Hard Link          (mklink /H) for files   -> no admin required

  Single source of truth:
    - Skills/workflows: reuse the original content under .agents/ (already git-tracked).
    - CLAUDE.md:        real file at datn-agent-skills/.claude/CLAUDE.md; root CLAUDE.md is a
                        1-line pointer that @imports it (survives editor atomic-saves, unlike
                        a hard link).

  Idempotent: removes existing links before recreating them.
  Run:  powershell -ExecutionPolicy Bypass -File datn-agent-skills\.claude\setup.ps1
#>

$ErrorActionPreference = 'Stop'

# Root monorepo = parent of datn-agent-skills (parent of the .claude holding this script)
$ClaudeSrc = Split-Path -Parent $MyInvocation.MyCommand.Path          # ...\datn-agent-skills\.claude
$DAS       = Split-Path -Parent $ClaudeSrc                            # ...\datn-agent-skills
$Root      = Split-Path -Parent $DAS                                  # ...\datn
$Agents    = Join-Path $DAS '.agents'

Write-Host "Root      = $Root"
Write-Host "Agents    = $Agents"
Write-Host "ClaudeSrc = $ClaudeSrc`n"

# --- helpers --------------------------------------------------------------
function Remove-Link($path) {
  if (Test-Path -LiteralPath $path) {
    $item = Get-Item -LiteralPath $path -Force
    if ($item.PSIsContainer) { cmd /c rmdir "`"$path`"" | Out-Null }   # junction -> rmdir (target untouched)
    else                     { Remove-Item -LiteralPath $path -Force }
  }
}
function New-Junction($link, $target) {
  Remove-Link $link
  cmd /c mklink /J "`"$link`"" "`"$target`"" | Out-Null
  Write-Host "  [J] $link  ->  $target"
}

# --- 1) root\.claude (real local folder holding the junctions) ------------
$RootClaude = Join-Path $Root '.claude'
if (-not (Test-Path -LiteralPath $RootClaude)) { New-Item -ItemType Directory -Path $RootClaude | Out-Null }

# --- 2) CLAUDE.md (root = 1-line pointer that @imports the real file) ------
Write-Host "CLAUDE.md:"
$RootClaudeMd = Join-Path $Root 'CLAUDE.md'
Remove-Link $RootClaudeMd
# Use a forward-slash relative path so Claude Code resolves the import from $Root.
Set-Content -LiteralPath $RootClaudeMd -Value '@datn-agent-skills/.claude/CLAUDE.md' -Encoding ASCII -NoNewline
Write-Host "  [P] $RootClaudeMd  ->  @datn-agent-skills/.claude/CLAUDE.md"

# --- 3) commands -> .agents\workflows (one junction) ----------------------
Write-Host "`nCommands:"
New-Junction (Join-Path $RootClaude 'commands') (Join-Path $Agents 'workflows')

# --- 4) skills (22 junctions, flattened - drop the category level) --------
Write-Host "`nSkills:"
$SkillsLink = Join-Path $RootClaude 'skills'
if (-not (Test-Path -LiteralPath $SkillsLink)) { New-Item -ItemType Directory -Path $SkillsLink | Out-Null }

# map: 'category/name'  (no slash = directly under .agents\skills)
$skills = @(
  'fastapidev/fastapi-iot-core',
  'fastapidev/fastapi-iot-security',
  'fastapidev/fastapi-route-generator',
  'fastapidev/iot-database-manager',
  'fastapidev/iot-testing-deployment',
  'firmware/esp-idf-build-manager',
  'firmware/esp-idf-sensor-driver',
  'firmware/lte-mqtt-client-manager',
  'firmware/tinyml-wrapper',
  'frontend/mqtt-hook-generator',
  'frontend/realtime-chart-config',
  'frontend/shadcn-component-builder',
  'general/git-ops-manager',
  'general/iot-system-architect-brainstormer',
  'general/requirement-validator',
  'general/sprint-review-gen',
  'general/task-breakdown',
  'infrastructure/influxdb-query-manager',
  'infrastructure/mqtt-to-db-bridge',
  'latex_generation',
  'resource_management'
)
foreach ($rel in $skills) {
  $name   = Split-Path $rel -Leaf
  $target = Join-Path $Agents (Join-Path 'skills' ($rel -replace '/','\'))
  if (-not (Test-Path -LiteralPath (Join-Path $target 'SKILL.md'))) {
    Write-Warning "  Skip $name - no SKILL.md at $target"
    continue
  }
  New-Junction (Join-Path $SkillsLink $name) $target
}

Write-Host "`nDone. Reopen Claude Code in $Root to load CLAUDE.md, /commands and skills."
