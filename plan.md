# Plan — 네트워크 프린터 스캐너

## 프로젝트 개요

SNMP(UDP 161) 기반으로 서브넷 내 프린터를 탐색하고, 사용자가 선택한 프린터 IP를 반환하는 Delphi 2007 Win32 애플리케이션. EXE 독립 실행과 DLL(stdcall export) 두 가지 형태로 배포한다.

---

## 기능 목록

| 기능명 | 우선순위 | 복잡도 | 의존성 | MVP |
| ------ | -------- | ------ | ------ | --- |
| SNMP 통신 모듈 (UDP 161 GET 요청/응답 파싱) | P0 | M | 없음 | O |
| 네트워크 인터페이스 자동 감지 (GetAdaptersInfo) | P0 | S | 없음 | O |
| 서브넷 IP 범위 계산 (CIDR, 시작~끝 IP) | P0 | S | 없음 | O |
| 멀티스레드 병렬 스캔 엔진 (TThread) | P0 | L | SNMP 통신 모듈, 서브넷 IP 범위 계산 | O |
| 메인 폼 UI (스캔 설정 패널 + 프린터 목록 ListView) | P0 | M | 없음 | O |
| 프린터 정보 조회 (sysName, hrDeviceDescr, hrDeviceType) | P0 | S | SNMP 통신 모듈 | O |
| 스캔 결과 → ListView 바인딩 | P0 | S | 메인 폼 UI, 멀티스레드 스캔 엔진 | O |
| 프린터 선택 및 IP 반환 로직 | P0 | S | 메인 폼 UI | O |
| 수동 서브넷 입력 (추가/삭제) | P0 | S | 메인 폼 UI | O |
| 실시간 로그 패널 | P1 | S | 메인 폼 UI | O |
| 스캔 중지 기능 | P1 | S | 멀티스레드 스캔 엔진 | O |
| SNMP Community String UI 설정 | P1 | S | 메인 폼 UI | O |
| 타임아웃 설정 UI | P1 | S | 메인 폼 UI | O |
| DLL Export (ShowPrinterScanner stdcall) | P0 | M | 메인 폼 UI, 스캔 엔진, 프린터 선택 | O |
| DLL Export (StartPrinterScan 비동기 콜백) | P1 | M | 스캔 엔진 | O |
| 로그 파일 저장 (텍스트 export) | P2 | S | 실시간 로그 패널 | X |
| 응답 시간 측정 및 표시 | P1 | S | SNMP 통신 모듈 | O |

---

## 기술 스택 정리

| 항목 | 선택 |
| ---- | ---- |
| 언어/IDE | Delphi 2007 (Win32, AnsiString) |
| SNMP | Indy 10 IdSNMP 또는 직접 UDP 소켓 |
| 멀티스레딩 | TThread + Synchronize |
| 네트워크 감지 | WinAPI GetAdaptersInfo (IpHlpApi) |
| UI | VCL (TForm, TListView, TMemo, TEdit, TButton) |
| 출력 형태 | EXE (독립 실행) + DLL (stdcall export) |

---

## MVP 범위

1. SNMP v1/v2c 기반 프린터 탐색 (hrDeviceType = printer 확인)
2. 로컬 네트워크 인터페이스 자동 감지 및 서브넷 도출
3. 수동 서브넷 추가 입력
4. 멀티스레드 병렬 스캔 (단일 /24 서브넷 10초 이내)
5. 발견된 프린터 목록 표시 (IP, 이름, 모델, 응답시간, 상태)
6. 프린터 선택 후 IP 반환
7. DLL export ShowPrinterScanner (모달)
8. 실시간 스캔 로그 표시
9. 스캔 중지 기능
10. Community String / 타임아웃 UI 설정
11. DLL export StartPrinterScan (비동기 콜백)
12. 응답 시간 측정

---

## 제외 범위 (v2 이후)

- SNMP v3 지원
- 로그 파일 저장 (텍스트 export)
- 64비트 빌드
- 인스톨러/설치 프로그램
- 프린터 상세 정보 조회 (잉크 잔량, 페이지 카운트 등)
- 프린터 직접 제어 (인쇄 명령 전송)
- 탐색 결과 영구 저장/캐싱
