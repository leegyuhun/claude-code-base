@echo off
REM DUnit 테스트 실행 스크립트

SET RSVARS="C:\Program Files (x86)\CodeGear\RAD Studio\5.0\bin\rsvars.bat"
SET DPROJ=%~dp0_D7\TestRunner.dproj

IF NOT EXIST %RSVARS% (
  echo [오류] rsvars.bat 를 찾을 수 없습니다: %RSVARS%
  exit /b 1
)

IF NOT EXIST "%DPROJ%" (
  echo [오류] 프로젝트 파일을 찾을 수 없습니다: %DPROJ%
  exit /b 1
)

echo [테스트 빌드]
call %RSVARS% && msbuild /t:Build /p:Config=Debug "%DPROJ%"
IF %ERRORLEVEL% NEQ 0 (
  echo [테스트 빌드 실패] ErrorLevel: %ERRORLEVEL%
  exit /b %ERRORLEVEL%
)

echo [테스트 실행]
"%~dp0Output\Debug\TestRunner.exe"

IF %ERRORLEVEL% NEQ 0 (
  echo [테스트 실패] ErrorLevel: %ERRORLEVEL%
  exit /b %ERRORLEVEL%
)
echo [테스트 성공]
