@echo off
setlocal enabledelayedexpansion
chcp 65001 > nul
cd /d "%~dp0"

echo.
echo ============================================================
echo   YSR EMR - Claude Code Setup
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
        echo   WARN - fill in GITLAB_TOKEN, REDMINE_API_KEY in .claude\settings.local.json
    ) else (
        echo   FAIL - copy error
    )
)

echo.
echo [3/4] .mcp.json...
if exist ".mcp.json" (
    echo   OK - already exists, skipped
) else (
    copy ".mcp.json.example" ".mcp.json" > nul
    echo   OK - created
    echo   WARN - fill in YOUR_GITLAB_TOKEN, YOUR_REDMINE_API_KEY in .mcp.json
)

echo.
echo [4/4] .gitignore (sprint / workspace entries)...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$lines=Get-Content '.gitignore'|ForEach-Object{$_.Trim()};$items=@('/CHANGELOG.md','/plan.md','/docs','/workspace','.mcp.json','/sprints/','/.claude/','build.bat','.mcp.json.example','claude.md','readme.md','setup_claude.bat','/.githooks/');$miss=$items|Where-Object{$lines -notcontains $_};if($miss.Count -gt 0){Add-Content '.gitignore' '';Add-Content '.gitignore' '# Claude Code - sprints/workspace (auto-added by setup_claude.bat)';$miss|ForEach-Object{Add-Content '.gitignore' $_};Write-Host ('  OK - added: '+($miss-join ', '))}else{Write-Host '  OK - already up to date'}"
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
    findstr /C:"<GITLAB_TOKEN>" ".claude\settings.local.json" > nul 2>&1
    if !errorlevel! equ 0 (
        echo   [settings.local] WARN - credentials not filled in yet
    ) else (
        echo   [settings.local] OK - credentials filled in
    )
) else (
    echo   [settings.local] NOT CREATED
)

if exist ".mcp.json" (
    echo   [.mcp.json  ] OK - file exists
    findstr /C:"YOUR_GITLAB_TOKEN" .mcp.json > nul 2>&1
    if !errorlevel! equ 0 (
        echo   [.mcp.json  ] WARN - credentials not filled in yet
    ) else (
        echo   [.mcp.json  ] OK - credentials filled in
    )
) else (
    echo   [.mcp.json  ] NOT CREATED
)

powershell -NoProfile -ExecutionPolicy Bypass -Command "$lines=Get-Content '.gitignore'|ForEach-Object{$_.Trim()};$items=@('/CHANGELOG.md','/plan.md','/docs','/workspace','.mcp.json','/sprints/','/.claude/','build.bat','.mcp.json.example','claude.md','readme.md','setup_claude.bat','/.githooks/');$miss=$items|Where-Object{$lines -notcontains $_};if($miss.Count -gt 0){Write-Host ('  [.gitignore   ] WARN - missing: '+($miss-join ', '))}else{Write-Host '  [.gitignore   ] OK - all entries present'}"

node --version > nul 2>&1
if !errorlevel! equ 0 (
    for /f "tokens=*" %%v in ('node --version 2^>nul') do set NODE_VER=%%v
    echo   [Node.js  ] OK - !NODE_VER! (MCP npx available)
) else (
    echo   [Node.js  ] NOT INSTALLED - Node.js is required to run MCP servers
    echo               Install from https://nodejs.org
)

if exist ".claude\settings.local.json" (
    findstr /C:"<GITLAB_TOKEN>" ".claude\settings.local.json" > nul 2>&1
    if !errorlevel! equ 0 (
        echo.
        echo ============================================================
        echo   [REQUIRED] .claude\settings.local.json credentials not filled in
        echo ============================================================
        echo.
        echo   Replace the following with actual values:
        echo.
        echo     GITLAB_TOKEN   : GitLab Personal Access Token
        echo     REDMINE_API_KEY: Redmine API Key
        echo.
        echo   File location: .claude\settings.local.json
        echo ============================================================
    )
)

echo.
echo Press any key to close...
pause > nul
