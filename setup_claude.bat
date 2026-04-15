@echo off
setlocal enabledelayedexpansion
chcp 65001 > nul

echo.
echo ============================================================
echo   YSR EMR - Claude Code Setup
echo ============================================================

echo.
echo [1/3] Git Hook (commit message format check)...
git config core.hooksPath .githooks
if !errorlevel! equ 0 (
    echo   OK
) else (
    echo   FAIL - git config error
)

echo.
echo [2/3] .claude/settings.local.json...
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
echo [3/3] .mcp.json...
if exist ".mcp.json" (
    echo   OK - already exists, skipped
) else (
    copy ".mcp.json.example" ".mcp.json" > nul
    echo   OK - created
    echo   WARN - fill in YOUR_GITLAB_TOKEN, YOUR_REDMINE_API_KEY in .mcp.json
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

node --version > nul 2>&1
if !errorlevel! equ 0 (
    for /f "tokens=*" %%v in ('node --version 2^>nul') do set NODE_VER=%%v
    echo   [Node.js  ] OK - !NODE_VER! (MCP npx 실행 가능)
) else (
    echo   [Node.js  ] NOT INSTALLED - MCP 서버를 실행하려면 Node.js가 필요합니다
    echo               https://nodejs.org 에서 설치하세요
)

if exist ".claude\settings.local.json" (
    findstr /C:"<GITLAB_TOKEN>" ".claude\settings.local.json" > nul 2>&1
    if !errorlevel! equ 0 (
        echo.
        echo ============================================================
        echo   [필수] .claude\settings.local.json 키값 입력 필요
        echo ============================================================
        echo.
        echo   아래 항목을 실제 값으로 교체하세요:
        echo.
        echo     GITLAB_TOKEN   : GitLab Personal Access Token
        echo     REDMINE_API_KEY: Redmine API Key
        echo.
        echo   파일 위치: .claude\settings.local.json
        echo ============================================================
    )
)

echo.
echo Press any key to close...
pause > nul
