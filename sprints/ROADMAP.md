# Sprint Roadmap

> plan.md 기반으로 의존성 순서와 우선순위를 고려하여 분할한 스프린트 로드맵.

---

| 스프린트 | 핵심 목표 | 포함 기능 | 예상 결과물 |
| -------- | --------- | --------- | ----------- |
| sprint-01 | 핵심 인프라 구축 (SNMP + 네트워크) | SNMP 통신 모듈 (P0/M), 네트워크 인터페이스 자동 감지 (P0/S), 서브넷 IP 범위 계산 (P0/S) | SNMP GET 요청/응답 파싱 동작, GetAdaptersInfo 기반 로컬 서브넷 목록 도출, IP 범위 순회 유틸 |
| sprint-02 | 스캔 엔진 + 메인 UI | 멀티스레드 병렬 스캔 엔진 (P0/L), 메인 폼 UI (P0/M), 프린터 정보 조회 (P0/S), 스캔 결과 ListView 바인딩 (P0/S) | 서브넷 스캔 시 프린터 발견 및 ListView 표시, 병렬 스캔으로 /24 서브넷 10초 이내 완료 |
| sprint-03 | 사용자 기능 완성 | 프린터 선택 및 IP 반환 (P0/S), 수동 서브넷 입력 (P0/S), 실시간 로그 패널 (P1/S), 스캔 중지 기능 (P1/S), SNMP Community String UI (P1/S), 타임아웃 설정 UI (P1/S), 응답 시간 측정 (P1/S) | EXE 독립 실행 시 전체 기능 동작, 프린터 선택 후 IP 반환, 로그/중지/설정 UI 완비 |
| sprint-04 | DLL Export + 통합 마무리 | DLL Export ShowPrinterScanner (P0/M), DLL Export StartPrinterScan 비동기 콜백 (P1/M) | DLL 빌드 및 stdcall export 함수 동작, 외부 모듈에서 ShowPrinterScanner 호출 시 모달 창 표시 및 IP 반환 |

---

## 스프린트 상세

### Sprint-01: 핵심 인프라 구축 (3일)

**목표**: SNMP 프로토콜 통신과 네트워크 인터페이스 감지의 기반 모듈을 구현한다.

**포함 기능**:
- SNMP 통신 모듈 (UDP 161 GET 요청/응답 ASN.1/BER 파싱) [P0/M]
- 네트워크 인터페이스 자동 감지 (GetAdaptersInfo) [P0/S]
- 서브넷 IP 범위 계산 (CIDR 파싱, 시작~끝 IP 순회) [P0/S]

**완료 기준**:
- SNMP GET 요청을 보내고 응답을 파싱할 수 있음
- 로컬 PC의 네트워크 인터페이스 목록과 서브넷 마스크를 가져올 수 있음
- 서브넷에서 IP 범위를 정확히 계산할 수 있음

**의존성**: 없음 (독립 모듈)

---

### Sprint-02: 스캔 엔진 + 메인 UI (4일)

**목표**: Sprint-01의 인프라 위에 병렬 스캔 엔진을 구축하고, 메인 폼 UI와 연동하여 프린터 목록을 표시한다.

**포함 기능**:
- 멀티스레드 병렬 스캔 엔진 (TThread 풀) [P0/L]
- 메인 폼 UI (스캔 설정 패널 + ListView) [P0/M]
- 프린터 정보 조회 (sysName, hrDeviceDescr, hrDeviceType) [P0/S]
- 스캔 결과 ListView 바인딩 [P0/S]

**완료 기준**:
- /24 서브넷 병렬 스캔 10초 이내 완료
- 발견된 프린터가 ListView에 IP, 이름, 모델, 상태 표시
- 스캔 진행 중 UI가 멈추지 않음

**의존성**: Sprint-01 (SNMP 통신, 서브넷 계산)

---

### Sprint-03: 사용자 기능 완성 (4일)

**목표**: EXE 독립 실행 시 모든 사용자 기능이 동작하도록 완성한다.

**포함 기능**:
- 프린터 선택 및 IP 반환 로직 [P0/S]
- 수동 서브넷 입력 (추가/삭제) [P0/S]
- 실시간 로그 패널 [P1/S]
- 스캔 중지 기능 [P1/S]
- SNMP Community String UI 설정 [P1/S]
- 타임아웃 설정 UI [P1/S]
- 응답 시간 측정 및 표시 [P1/S]

**완료 기준**:
- 프린터 선택 후 접속 버튼 클릭 시 IP 반환
- 수동 서브넷 추가/삭제 후 스캔 동작
- 로그 패널에 스캔 진행 상황 실시간 표시
- 스캔 중지 버튼 동작
- Community String, 타임아웃 설정 변경 후 스캔 반영

**의존성**: Sprint-02 (스캔 엔진, 메인 폼 UI)

---

### Sprint-04: DLL Export + 통합 마무리 (3일)

**목표**: DLL 빌드 구성을 추가하고, 외부 모듈에서 호출 가능한 stdcall export 함수를 구현한다.

**포함 기능**:
- DLL Export ShowPrinterScanner (모달) [P0/M]
- DLL Export StartPrinterScan (비동기 콜백) [P1/M]

**완료 기준**:
- DLL 빌드 성공
- 외부 테스트 프로그램에서 ShowPrinterScanner 호출 시 모달 창 표시 및 선택 IP 반환
- StartPrinterScan 호출 시 콜백으로 프린터 정보 전달
- EXE와 DLL 모두 정상 동작

**의존성**: Sprint-03 (전체 기능 완성)
