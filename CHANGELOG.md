# CHANGELOG

> 스프린트 단위 변경 이력. Validator가 스프린트 종료 시 자동 업데이트.

---

## [sprint-01] 핵심 인프라 구축 (SNMP + 네트워크) — 2026-03-31

### 추가
- uScanTypes.pas — TPrinterInfo, TScanState, TSubnetInfo 공통 타입 및 콜백 타입 정의
- uSNMP.pas — SNMP v1/v2c UDP 161 GET 요청 및 ASN.1/BER 응답 파싱
- uNetworkUtils.pas — GetAdaptersInfo 기반 로컬 네트워크 인터페이스 자동 감지
- uSubnetCalc.pas — CIDR 파싱, IP <-> DWORD 변환, 서브넷 IP 범위 계산
- uScanEngine.pas — 스캔 엔진 스텁 (sprint-02에서 완성)
- uDLLExport.pas — DLL Export 스텁 (sprint-04에서 완성)
- PrinterScanApp.dpr / PrinterScanLib.dpr — EXE/DLL 프로젝트 파일
- build.bat — Delphi 2007 dcc32 기반 EXE/DLL 빌드 스크립트

### 기술 부채
- uScanEngine.pas StartScan/StopScan 구현 필요 (sprint-02)
- uDLLExport.pas ShowPrinterScanner/StartPrinterScan 구현 필요 (sprint-04)
- 서브넷 IP 범위 계산 DUnit 단위 테스트 추가 필요
- SNMP GET 실장비 통합 테스트 미수행 (sprint-02 UI 완성 후 수행)
