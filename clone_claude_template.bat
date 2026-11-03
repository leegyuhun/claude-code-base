@echo off
rem ============================================================================
rem clone_claude_template.bat
rem   Sync the latest Claude Code template into the CURRENT working tree, even
rem   when you are on another branch, then apply it.
rem     clone_claude_template.bat              menu (or the only/default template)
rem     clone_claude_template.bat <name>       template name from clone_claude_template.json
rem
rem   Real work is done by clone_claude_template.ps1 (PowerShell handles the
rem   menu and non-ASCII paths safely; this .bat stays pure ASCII as a launcher).
rem   Templates (branch, paths, fill-only paths) live in clone_claude_template.json.
rem ============================================================================
setlocal
cd /d "%~dp0"

if not exist "%~dp0clone_claude_template.ps1" (
    echo [ERROR] clone_claude_template.ps1 not found next to this .bat.
    echo         Both files must sit together in the repo root.
    pause
    endlocal & exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0clone_claude_template.ps1" %*
set "RC=%ERRORLEVEL%"

echo.
pause
endlocal & exit /b %RC%
