@echo off
REM Delphi 2007 빌드 스크립트
REM 사용법: build.bat [debug|release]

SET DELPHI_HOME=C:\Program Files\CodeGear\RAD Studio\5.0
SET DCC32=%DELPHI_HOME%\bin\dcc32.exe
SET CONFIG=%1
IF "%CONFIG%"=="" SET CONFIG=debug

echo [빌드 시작] Config: %CONFIG%

IF "%CONFIG%"=="release" (
  "%DCC32%" -E"Output\Release" -N"Lib" -Q Source\ProjectMain.dpr
) ELSE (
  "%DCC32%" -E"Output\Debug" -N"Lib" -Q -$D+ Source\ProjectMain.dpr
)

IF %ERRORLEVEL% NEQ 0 (
  echo [빌드 실패] ErrorLevel: %ERRORLEVEL%
  exit /b %ERRORLEVEL%
)
echo [빌드 성공]
