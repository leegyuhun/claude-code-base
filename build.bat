@echo off
REM ===================================================
REM  Delphi 2007 빌드 스크립트 - Network Printer Scanner
REM  사용법: build.bat [exe|dll|all] [debug|release]
REM ===================================================

SET RSVARS="C:\Program Files (x86)\CodeGear\RAD Studio\5.0\bin\rsvars.bat"
SET DCC32="C:\Program Files (x86)\CodeGear\RAD Studio\5.0\bin\dcc32.exe"
SET SRC_DIR=%~dp0Source
SET OUT_DIR=%~dp0Output

SET TARGET=%1
SET CONFIG=%2
IF "%TARGET%"=="" SET TARGET=all
IF "%CONFIG%"=="" SET CONFIG=Release

SET OUT_PATH=%OUT_DIR%\%CONFIG%
IF NOT EXIST "%OUT_PATH%" mkdir "%OUT_PATH%"

IF NOT EXIST "%~dp0Lib" mkdir "%~dp0Lib"

SET DELPHI_LIB=C:\Program Files (x86)\CodeGear\RAD Studio\5.0\lib
SET INDY10_LIB=C:\Program Files (x86)\CodeGear\RAD Studio\5.0\lib\Indy10
SET DELPHI_OPTS=-B -Q -N0"%~dp0Lib" -E"%OUT_PATH%" -U"%SRC_DIR%;%DELPHI_LIB%;%INDY10_LIB%"

echo ===================================================
echo  [빌드 시작] Target: %TARGET% / Config: %CONFIG%
echo ===================================================

IF NOT EXIST %DCC32% (
  echo [오류] dcc32.exe 를 찾을 수 없습니다: %DCC32%
  exit /b 1
)

REM ---------- EXE 빌드 ----------
IF "%TARGET%"=="exe" GOTO BUILD_EXE
IF "%TARGET%"=="all" GOTO BUILD_EXE
GOTO SKIP_EXE

:BUILD_EXE
echo.
echo [EXE 빌드] PrinterScanApp.dpr
%DCC32% %DELPHI_OPTS% "%~dp0PrinterScanApp.dpr"
IF %ERRORLEVEL% NEQ 0 (
  echo [EXE 빌드 실패] ErrorLevel: %ERRORLEVEL%
  exit /b %ERRORLEVEL%
)
echo [EXE 빌드 성공] %OUT_PATH%\PrinterScanApp.exe

:SKIP_EXE

REM ---------- DLL 빌드 ----------
IF "%TARGET%"=="dll" GOTO BUILD_DLL
IF "%TARGET%"=="all" GOTO BUILD_DLL
GOTO SKIP_DLL

:BUILD_DLL
echo.
echo [DLL 빌드] PrinterScanLib.dpr
%DCC32% %DELPHI_OPTS% "%~dp0PrinterScanLib.dpr"
IF %ERRORLEVEL% NEQ 0 (
  echo [DLL 빌드 실패] ErrorLevel: %ERRORLEVEL%
  exit /b %ERRORLEVEL%
)
echo [DLL 빌드 성공] %OUT_PATH%\PrinterScanLib.dll

:SKIP_DLL

echo.
echo ===================================================
echo  [빌드 완료] 출력 경로: %OUT_PATH%
echo ===================================================
