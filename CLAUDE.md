# CLAUDE.md

## 빌드 & 실행

### 빌드 명령
```bat
# EXE + DLL 전체 빌드
build.bat all Release

# EXE만 빌드
build.bat exe Release

# DLL만 빌드
build.bat dll Release

# 디버그 빌드
build.bat all Debug
```

### 빌드 환경
- Delphi 2007 (CodeGear RAD Studio 5.0)
- 컴파일러: dcc32.exe
- 경로: `C:\Program Files (x86)\CodeGear\RAD Studio\5.0\bin\dcc32.exe`

### 출력 경로
- Release: `Output/Release/`
- Debug: `Output/Debug/`
- DCU 중간파일: `Lib/`

---

## 프로젝트 구조

```
PrinterScanApp.dpr          -- EXE 프로젝트 (독립 실행)
PrinterScanLib.dpr          -- DLL 프로젝트 (stdcall export)
Source/
  uScanTypes.pas            -- 공통 타입 (TPrinterInfo, TScanState, 콜백)
  uSNMP.pas                 -- SNMP v1/v2c 통신 (UDP 161)
  uNetworkUtils.pas         -- 네트워크 인터페이스 감지 (GetAdaptersInfo)
  uSubnetCalc.pas           -- 서브넷 IP 범위 계산 (CIDR, IP 변환)
  uScanEngine.pas           -- 멀티스레드 병렬 스캔 엔진 (TThread)
  uMainForm.pas / .dfm      -- 메인 폼 UI (VCL)
  uDLLExport.pas            -- DLL export 함수 (ShowPrinterScanner, StartPrinterScan)
Tests/
  Source/                   -- 단위 테스트 소스
Output/
  Debug/                    -- 디버그 빌드 산출물
  Release/                  -- 릴리즈 빌드 산출물
Lib/                        -- DCU 중간 파일
docs/
  PRD.md                    -- 요구사항 정의서
  STATUS.md                 -- 파이프라인 상태
sprints/
  ROADMAP.md                -- 스프린트 로드맵
```

---

## 코딩 원칙

### 언어 규칙 (Delphi 2007)
- **AnsiString 기반** -- Unicode 미지원, 모든 문자열은 AnsiString
- **Win32 전용** -- 64비트 빌드 불필요
- 유닛 이름 접두어: `u` (예: uSNMP, uMainForm)
- 폼 클래스 접두어: `Tfrm` (예: TfrmMain)
- 레코드/클래스 접두어: `T` (예: TPrinterInfo, TScanEngine)

### 스레딩 규칙
- VCL 컴포넌트 접근은 반드시 `Synchronize` 사용
- `ProcessMessages` 호출 시 재진입 가드 필수
- TThread.FreeOnTerminate 사용 시 참조 관리 주의

### UI 규칙
- 대량 리스트 업데이트 시 `BeginUpdate` / `EndUpdate` 필수
- GDI 객체 생성 후 `DeleteObject` 또는 `Free` 필수
- 모달 폼에서는 `ShowModal` + `ModalResult` 패턴 사용

### SNMP 규칙
- SNMP v1/v2c만 지원 (v3 불필요)
- Community String 기본값: `public`
- 타임아웃 기본값: 1000ms
- 프린터 판별 OID: `1.3.6.1.2.1.25.3.2.1.2` (hrDeviceType)

### DLL Export 규칙
- 모든 export 함수는 `stdcall` 호출 규약
- 매개변수/반환값은 `PAnsiChar`, `Integer`, `HWND` 등 원시 타입만 사용
- 문자열 반환은 호출자가 버퍼를 할당하고 크기를 전달하는 방식

### 의존성
- 외부 라이브러리: Indy 10 (IdSNMP) -- Delphi 2007 기본 포함
- 서드파티 유료 컴포넌트 사용 금지
- WinAPI: IpHlpApi (GetAdaptersInfo), WinSock

---

## 테스트

### 빌드 검증
```bat
build.bat all Release
```
- EXE: `Output/Release/PrinterScanApp.exe` 존재 확인
- DLL: `Output/Release/PrinterScanLib.dll` 존재 확인

### 수동 테스트
- EXE 실행 후 스캔 시작 -> 프린터 목록 표시 확인
- 프린터 선택 후 접속 -> IP 반환 확인
- DLL 테스트 프로그램에서 ShowPrinterScanner 호출 확인
