@echo off
setlocal enabledelayedexpansion
chcp 65001 > nul
cd /d "%~dp0"

echo.
echo ============================================================
echo   Claude Code Harness Setup
echo ============================================================

echo.
echo [1/5] Git Hook (commit message format check)...
git config core.hooksPath .githooks
if !errorlevel! equ 0 (
    echo   OK
) else (
    echo   FAIL - git config error
)

echo.
echo [2/5] .claude/settings.local.json...
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
echo [3/5] Migrate hooks (local -^> shared settings.json)...
REM Hooks moved from settings.local.json.sample to .claude/settings.json (team-wide guarantee).
REM Existing installs still carry a stale hooks block in their local file - remove it,
REM otherwise both definitions apply and every guard fires twice.
powershell -NoProfile -ExecutionPolicy Bypass -Command "$p='.claude\settings.local.json';if(-not (Test-Path $p)){Write-Host '  OK - no local settings yet';exit 0};$j=Get-Content $p -Raw|ConvertFrom-Json;if($j.PSObject.Properties.Name -contains 'hooks'){$j.PSObject.Properties.Remove('hooks');$j|ConvertTo-Json -Depth 10|Set-Content $p -Encoding UTF8;Write-Host '  OK - removed stale hooks block (now shared via .claude/settings.json)'}else{Write-Host '  OK - nothing to migrate'}"
if !errorlevel! neq 0 (
    echo   FAIL - migration error
)

echo.
echo [4/5] Python (hooks and harness scripts)...
REM The hooks run "python3". On Windows the Microsoft Store stub python3.exe exists even when
REM Python is NOT installed - it only opens the Store. A hook that hits the stub exits non-zero
REM as a non-blocking error, i.e. every guard silently fails open. Probe by actually running it.
python3 -c "import sys; sys.exit(0)" > nul 2>&1
if !errorlevel! equ 0 (
    for /f "tokens=*" %%v in ('python3 --version 2^>^&1') do echo   OK - %%v
) else (
    echo   WARN - python3 is not runnable. Hooks and loop scripts will fail open ^(no guards^).
    echo          Install Python 3 from https://www.python.org ^(check "Add python.exe to PATH"^)
    echo          and disable the Store alias: Settings ^> Apps ^> App execution aliases ^> python3.exe
)

echo.
echo [5/5] .git/info/exclude (repo-local ignore - all branches)...
REM Written to .git/info/exclude, NOT .gitignore: the ignore rules then apply on every branch
REM without ever touching a tracked file, and switching branches does not drop them.
REM --git-path resolves the file correctly inside a linked worktree (where .git is a file).
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ex=(git rev-parse --git-path info/exclude);New-Item -ItemType Directory -Force -Path (Split-Path -Parent $ex)|Out-Null;if(-not(Test-Path -LiteralPath $ex)){New-Item -ItemType File -Path $ex|Out-Null};$lines=Get-Content -LiteralPath $ex|ForEach-Object{$_.Trim()};$items=@('/plan.md','/docs','/workspace','.mcp.json','/sprints/','/.claude/','claude.md','readme.md','setup_claude.bat','/.githooks/','/clone_claude_template.bat','/clone_claude_template.ps1');$miss=$items|Where-Object{$lines -notcontains $_};if($miss.Count -gt 0){Add-Content -LiteralPath $ex '';Add-Content -LiteralPath $ex '# Claude Code - sprints/workspace (auto-added by setup_claude.bat)';$miss|ForEach-Object{Add-Content -LiteralPath $ex $_};Write-Host ('  OK - added: '+($miss-join ', '))}else{Write-Host '  OK - already up to date'}"
if !errorlevel! equ 0 (
    echo   OK
) else (
    echo   FAIL - exclude update error
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

powershell -NoProfile -ExecutionPolicy Bypass -Command "$ex=(git rev-parse --git-path info/exclude);if(-not(Test-Path -LiteralPath $ex)){Write-Host '  [info/exclude ] NOT CREATED';exit 0};$lines=Get-Content -LiteralPath $ex|ForEach-Object{$_.Trim()};$items=@('/plan.md','/docs','/workspace','.mcp.json','/sprints/','/.claude/','claude.md','readme.md','setup_claude.bat','/.githooks/','/clone_claude_template.bat','/clone_claude_template.ps1');$miss=$items|Where-Object{$lines -notcontains $_};if($miss.Count -gt 0){Write-Host ('  [info/exclude ] WARN - missing: '+($miss-join ', '))}else{Write-Host '  [info/exclude ] OK - all entries present'}"

python3 -c "import sys; sys.exit(0)" > nul 2>&1
if !errorlevel! equ 0 (
    for /f "tokens=*" %%v in ('python3 --version 2^>^&1') do set PY_VER=%%v
    echo   [Python   ] OK - !PY_VER! ^(hooks / loop scripts^)
) else (
    echo   [Python   ] NOT RUNNABLE - hooks fail open until Python 3 is installed
)

if exist ".claude\harness.json" (
    echo   [harness.json] OK - file exists ^(build/test commands^)
) else (
    echo   [harness.json] NOT FOUND - filled at PHASE 4.5, or write it manually
)

echo.
echo Press any key to close...
pause > nul
