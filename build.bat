@echo off
REM Delphi 2007 빌드 스크립트
REM 사용법: build.bat [debug|release]

SET RSVARS="C:\Program Files (x86)\CodeGear\RAD Studio\5.0\bin\rsvars.bat"
SET DPROJ=%~dp0_D7\FwChart.dproj
SET CONFIG=%1
IF "%CONFIG%"=="" SET CONFIG=Release

echo [빌드 시작] Config: %CONFIG%

IF NOT EXIST %RSVARS% (
  echo [오류] rsvars.bat 를 찾을 수 없습니다: %RSVARS%
  exit /b 1
)

IF NOT EXIST "%DPROJ%" (
  echo [오류] 프로젝트 파일을 찾을 수 없습니다: %DPROJ%
  exit /b 1
)

call %RSVARS% && msbuild /t:Build /p:Config=%CONFIG% "%DPROJ%"

IF %ERRORLEVEL% NEQ 0 (
  echo [빌드 실패] ErrorLevel: %ERRORLEVEL%
  exit /b %ERRORLEVEL%
)
echo [빌드 성공]
