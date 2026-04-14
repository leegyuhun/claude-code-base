@echo off
setlocal enabledelayedexpansion
chcp 65001 > nul

echo.
echo ============================================================
echo   YSR EMR - Claude Code Setup
echo ============================================================

echo.
echo [1/2] Git Hook (commit message format check)...
git config core.hooksPath .githooks
if !errorlevel! equ 0 (
    echo   OK
) else (
    echo   FAIL - git config error
)

echo.
echo [2/2] .mcp.json...
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

if exist ".mcp.json" (
    echo   [.mcp.json] OK - file exists
    findstr /C:"YOUR_GITLAB_TOKEN" .mcp.json > nul 2>&1
    if !errorlevel! equ 0 (
        echo   [.mcp.json] WARN - credentials not filled in yet
    ) else (
        echo   [.mcp.json] OK - credentials filled in
    )
) else (
    echo   [.mcp.json] NOT CREATED
)

node --version > nul 2>&1
if !errorlevel! equ 0 (
    for /f "tokens=*" %%v in ('node --version 2^>nul') do set NODE_VER=%%v
    echo   [Node.js  ] OK - !NODE_VER! (MCP npx 실행 가능)
) else (
    echo   [Node.js  ] NOT INSTALLED - MCP 서버를 실행하려면 Node.js가 필요합니다
    echo               https://nodejs.org 에서 설치하세요
)

echo.
echo Press any key to close...
pause > nul
