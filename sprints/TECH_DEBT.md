# Tech Debt 중앙 관리

> 모든 스프린트의 기술 부채를 집계. Validator가 스프린트 종료 시 업데이트.
> 처리 완료 시 행 삭제 없이 체크 표시 유지.

---

| 항목 | 출처 스프린트 | 우선순위 | 처리 스프린트 |
|------|--------------|----------|--------------|
| uScanEngine.pas StartScan 구현 (TThread 풀 기반 병렬 스캔) | sprint-01 | P0 | sprint-02 |
| uScanEngine.pas StopScan 구현 | sprint-01 | P0 | sprint-02 |
| uDLLExport.pas ShowPrinterScanner 구현 (stdcall 모달) | sprint-01 | P0 | sprint-04 |
| uDLLExport.pas StartPrinterScan 구현 (비동기 콜백) | sprint-01 | P1 | sprint-04 |
| 서브넷 IP 범위 계산 DUnit 단위 테스트 추가 (Tests/Source/) | sprint-01 | P1 | - |
| SNMP GET 실장비 통합 테스트 수행 | sprint-01 | P1 | sprint-02 |
