@echo off
REM DUnit test runner script

SET RSVARS="C:\Program Files (x86)\CodeGear\RAD Studio\5.0\bin\rsvars.bat"
SET DPROJ=%~dp0_D7\TestRunner.dproj

IF NOT EXIST %RSVARS% (
  echo [Error] rsvars.bat not found: %RSVARS%
  exit /b 1
)

IF NOT EXIST "%DPROJ%" (
  echo [Error] Project file not found: %DPROJ%
  exit /b 1
)

echo [Test Build]
call %RSVARS% && msbuild /t:Build /p:Config=Debug "%DPROJ%"
IF %ERRORLEVEL% NEQ 0 (
  echo [Test Build Failed] ErrorLevel: %ERRORLEVEL%
  exit /b %ERRORLEVEL%
)

echo [Test Run]
"%~dp0Output\Debug\TestRunner.exe"

IF %ERRORLEVEL% NEQ 0 (
  echo [Test Failed] ErrorLevel: %ERRORLEVEL%
  exit /b %ERRORLEVEL%
)
echo [Test Success]
