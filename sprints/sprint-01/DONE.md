# sprint-01 완료 보고

## 완료된 기능

- [x] 공통 타입 정의 (uScanTypes.pas) — TPrinterInfo, TScanState, TSubnetInfo, 콜백 타입 정의
- [x] SNMP 통신 모듈 (uSNMP.pas) — SNMP v1/v2c UDP GET 요청 및 ASN.1/BER 응답 파싱
- [x] 네트워크 인터페이스 자동 감지 (uNetworkUtils.pas) — GetAdaptersInfo 기반 로컬 서브넷 목록
- [x] 서브넷 IP 범위 계산 (uSubnetCalc.pas) — CIDR 파싱, IP <-> DWORD 변환, 범위 순회
- [x] 빌드 스크립트 및 프로젝트 파일 초기 구성 — build.bat, PrinterScanApp.dpr, PrinterScanLib.dpr

## 생성/수정된 파일 목록

| 파일 | 구분 |
|------|------|
| Source/uScanTypes.pas | 신규 생성 |
| Source/uSNMP.pas | 신규 생성 |
| Source/uNetworkUtils.pas | 신규 생성 |
| Source/uSubnetCalc.pas | 신규 생성 |
| Source/uScanEngine.pas | 신규 생성 (스텁 — sprint-02에서 완성) |
| Source/uDLLExport.pas | 신규 생성 (스텁 — sprint-04에서 완성) |
| PrinterScanApp.dpr | 신규 생성 |
| PrinterScanApp.dproj | 신규 생성 |
| PrinterScanLib.dpr | 신규 생성 |
| PrinterScanLib.dproj | 신규 생성 |
| build.bat | 신규 생성 |
| PrinterScanApp.res | 신규 생성 |

## 추가된 폼 / 유닛

- 폼: 없음 (sprint-01은 인프라 모듈만 구현)
- 스텁 유닛: uScanEngine.pas (빌드 가능 수준), uDLLExport.pas (빌드 가능 수준)

## 빌드 검증 결과

- EXE 빌드 (build.bat debug): 성공 (0 오류, H2219 힌트 1개 — 무시)
- DLL 빌드: 성공 (0 오류)
- DUnit 테스트: 건너뜀 (Tests/Source/ 비어 있음)
- 수동 테스트: sprint-01은 UI 없는 백엔드 인프라 단계이므로 sprint-02 UI 완성 후 통합 테스트로 대체

## Tech Debt

| 항목 | 위치 | 우선순위 |
|------|------|----------|
| uScanEngine.pas StartScan/StopScan 구현 | Source/uScanEngine.pas:61,67 | P0 — sprint-02에서 구현 |
| uDLLExport.pas ShowPrinterScanner/StartPrinterScan 구현 | Source/uDLLExport.pas:52,62 | P0 — sprint-04에서 구현 |
| 서브넷 IP 범위 계산 DUnit 단위 테스트 | Tests/Source/ | P1 — sprint-02 또는 sprint-03에서 추가 |
| SNMP GET 실장비 통합 테스트 | 수동 | P1 — sprint-02 UI 완성 후 수행 |

## 다음 스프린트 주의사항

- sprint-02는 uScanEngine.pas의 TODO 구현을 포함: StartScan(TThread 풀), StopScan
- uMainForm.pas/.dfm 신규 생성 필요 — sprint-01에서 생성된 Source/ 유닛을 uses에 추가
- Indy 10 IdSNMP 경로는 build.bat의 -U 옵션에 이미 포함되어 있으므로 그대로 사용
- uSNMP.pas의 타임아웃 기본값 1000ms, Community String "public" — UI에서 변경 가능하도록 연동 예정
