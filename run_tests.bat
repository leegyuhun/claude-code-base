@echo off
REM DUnit 테스트 실행 스크립트
SET DELPHI_HOME=C:\Program Files\CodeGear\RAD Studio\5.0
SET DCC32=%DELPHI_HOME%\bin\dcc32.exe

echo [테스트 빌드]
"%DCC32%" -E"Output\Debug" -N"Lib" -Q -$D+ Tests\TestRunner.dpr
IF %ERRORLEVEL% NEQ 0 (
  echo [테스트 빌드 실패]
  exit /b %ERRORLEVEL%
)
echo [테스트 실행]
Output\Debug\TestRunner.exe
