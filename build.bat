@echo off
REM Delphi 2007 build script
REM Usage: build.bat [debug|release]

REM 환경변수로 미리 지정된 값을 우선한다. 지정이 없을 때만 기본값을 쓴다.
REM (무조건 SET 하면 외부 오버라이드가 먹지 않는다 — validator.md와
REM  verification-before-completion 스킬이 안내하는 DPROJ 지정 방식이 이것에 의존한다)
IF "%RSVARS%"=="" SET RSVARS="C:\Program Files (x86)\CodeGear\RAD Studio\5.0\bin\rsvars.bat"
IF "%DPROJ%"=="" SET DPROJ=%~dp0_D7\FwChart.dproj
SET CONFIG=%1
IF "%CONFIG%"=="" SET CONFIG=Release

echo [Build Start] Config: %CONFIG%

IF NOT EXIST %RSVARS% (
  echo [Error] rsvars.bat not found: %RSVARS%
  exit /b 1
)

IF NOT EXIST "%DPROJ%" (
  echo [Error] Project file not found: %DPROJ%
  exit /b 1
)

call %RSVARS% && msbuild /t:Build /p:Config=%CONFIG% "%DPROJ%"

IF %ERRORLEVEL% NEQ 0 (
  echo [Build Failed] ErrorLevel: %ERRORLEVEL%
  exit /b %ERRORLEVEL%
)
echo [Build Success]
