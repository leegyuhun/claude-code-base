@echo off
setlocal enabledelayedexpansion
chcp 65001 > nul
cd /d "%~dp0"

echo.
echo ============================================================
echo   Claude Code Harness Setup
echo ============================================================

echo.
echo [1/4] Git Hook (commit message format check)...
git config core.hooksPath .githooks
if !errorlevel! equ 0 (
    echo   OK
) else (
    echo   FAIL - git config error
)

echo.
echo [2/4] .claude/settings.local.json...
if exist ".claude\settings.local.json" (
    echo   INFO - already exists, merging missing keys from sample...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$e=Get-Content '.claude\settings.local.json'|ConvertFrom-Json;$s=Get-Content '.claude\settings.local.json.sample'|ConvertFrom-Json;function Merge-J($t,$src){foreach($p in $src.PSObject.Properties){$n=$p.Name;if($null -eq $t.$n){$t|Add-Member -MemberType NoteProperty -Name $n -Value $p.Value}elseif($t.$n -is [PSCustomObject] -and $p.Value -is [PSCustomObject]){Merge-J $t.$n $p.Value}}};Merge-J $e $s;$e|ConvertTo-Json -Depth 10|Set-Content '.claude\settings.local.json' -Encoding UTF8"
    if !errorlevel! equ 0 (
        echo   OK - merged
    ) else (
        echo   FAIL - merge error
    )
) else (
    copy ".claude\settings.local.json.sample" ".claude\settings.local.json" > nul
    if !errorlevel! equ 0 (
        echo   OK - created from sample
    ) else (
        echo   FAIL - copy error
    )
)

echo.
echo [3/4] Migrate hooks (local -^> shared settings.json)...
REM Hooks moved from settings.local.json.sample to .claude/settings.json (team-wide guarantee).
REM Existing installs still carry a stale hooks block in their local file - remove it,
REM otherwise both definitions apply and every guard fires twice.
powershell -NoProfile -ExecutionPolicy Bypass -Command "$p='.claude\settings.local.json';if(-not (Test-Path $p)){Write-Host '  OK - no local settings yet';exit 0};$j=Get-Content $p -Raw|ConvertFrom-Json;if($j.PSObject.Properties.Name -contains 'hooks'){$j.PSObject.Properties.Remove('hooks');$j|ConvertTo-Json -Depth 10|Set-Content $p -Encoding UTF8;Write-Host '  OK - removed stale hooks block (now shared via .claude/settings.json)'}else{Write-Host '  OK - nothing to migrate'}"
if !errorlevel! neq 0 (
    echo   FAIL - migration error
)

echo.
echo [4/4] .gitignore (sprint / workspace entries)...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$lines=Get-Content '.gitignore'|ForEach-Object{$_.Trim()};$items=@('/CHANGELOG.md','/plan.md','/docs','/workspace','.mcp.json','/sprints/','/.claude/','claude.md','readme.md','setup_claude.bat','/.githooks/');$miss=$items|Where-Object{$lines -notcontains $_};if($miss.Count -gt 0){Add-Content '.gitignore' '';Add-Content '.gitignore' '# Claude Code - sprints/workspace (auto-added by setup_claude.bat)';$miss|ForEach-Object{Add-Content '.gitignore' $_};Write-Host ('  OK - added: '+($miss-join ', '))}else{Write-Host '  OK - already up to date'}"
if !errorlevel! equ 0 (
    echo   OK
) else (
    echo   FAIL - gitignore update error
)

echo.
echo ============================================================
echo   Status
echo ============================================================

for /f "tokens=*" %%h in ('git config core.hooksPath 2^>nul') do set HOOKS_PATH=%%h
if defined HOOKS_PATH (
    echo   [Git Hook ] OK - !HOOKS_PATH!
) else (
    echo   [Git Hook ] NOT SET
)

if exist ".claude\settings.local.json" (
    echo   [settings.local] OK - file exists
) else (
    echo   [settings.local] NOT CREATED
)

powershell -NoProfile -ExecutionPolicy Bypass -Command "$lines=Get-Content '.gitignore'|ForEach-Object{$_.Trim()};$items=@('/CHANGELOG.md','/plan.md','/docs','/workspace','.mcp.json','/sprints/','/.claude/','claude.md','readme.md','setup_claude.bat','/.githooks/');$miss=$items|Where-Object{$lines -notcontains $_};if($miss.Count -gt 0){Write-Host ('  [.gitignore   ] WARN - missing: '+($miss-join ', '))}else{Write-Host '  [.gitignore   ] OK - all entries present'}"

if exist ".claude\harness.json" (
    echo   [harness.json] OK - file exists ^(build/test commands^)
) else (
    echo   [harness.json] NOT FOUND - filled at PHASE 4.5, or write it manually
)

echo.
echo Press any key to close...
pause > nul
