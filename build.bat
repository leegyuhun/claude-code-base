@echo off
REM Delphi 2007 build script
REM Usage: build.bat [debug|release]

SET RSVARS="C:\Program Files (x86)\CodeGear\RAD Studio\5.0\bin\rsvars.bat"
SET DPROJ=%~dp0_D7\FwChart.dproj
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
