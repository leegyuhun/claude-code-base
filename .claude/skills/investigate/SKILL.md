---
name: investigate
description: YSR EMR 시스템의 버그 원인을 코드베이스에서 탐색한다. 이슈 번호, 버그 현상, 오류 메시지 등을 입력받아 Delphi/C# 혼합 코드베이스에서 근본 원인과 관련 파일을 찾아낸다. bug-investigator 에이전트가 이 스킬을 사용한다.
---

# 버그 조사 스킬

## 탐색 전략

### 1단계: 이슈 컨텍스트 수집

**Redmine 조회 (우선):** `redmine` 스킬로 이슈 상세 내용을 가져온다.
- `.env`에서 `REDMINE_API_KEY` 읽기
- `GET https://redmine.ubware.com/issues/{이슈번호}.json` 호출
- 제목, 설명, 카테고리 추출 → 이후 코드 탐색 키워드로 활용
- 실패 시: 사용자가 제공한 설명이나 git 이력으로 대체

**git 이력 확인 (병행):** 동일 이슈의 기존 작업 이력을 확인한다:
```bash
git log --oneline --all | grep "#이슈번호"
git show [커밋해시] --stat
```

관련 브랜치도 확인한다:
```bash
git branch -a | grep "이슈번호"
```

### 2단계: 코드베이스 탐색 순서

YSR 코드베이스의 의존성 방향: `Common → CommonBL → Module → Projects`

버그 탐색은 **호출 방향의 역순**으로 진행한다:
1. 오류 발생 지점(Module 레벨) 확인
2. 공통 레이어(Common) 확인 — 실제 원인이 여기 있는 경우 많음
3. 외부 의존성(COM, Win32 API, DB) 확인

### 3단계: 키워드 기반 탐색

Grep 탐색 패턴:
- **Delphi**: 클래스명, 프로시저명은 PascalCase. `procedure TClassName.MethodName`
- **C#**: 네임스페이스 기반. `namespace YSR.`, `class XXXUtil`
- **공통**: 이슈 설명에서 핵심 도메인 용어 추출 (예: "프린터 포트" → `PrinterPort`, `GetPrinterPort`)

### 4단계: 영향 범위 확인

수정 대상 파일을 찾은 후:
- 해당 함수/클래스를 호출하는 다른 코드 탐색
- 같은 기능을 다루는 다른 버전 파일 확인 (예: `_D7`, `_BL`, `_v2007` 접미사)

### 5단계: 재현 가이드 생성 (조건부)

**진입 조건** — 다음 중 하나 이상 해당 시 실행한다:
- 환경 의존적 버그 (프린터, 네트워크, OS, 특정 DB 상태)
- 특정 데이터 조건이 필요한 버그 (환자 유형, 보험 유형, 날짜 범위 등)
- 특정 조작 순서에서만 발생하는 버그 (타이밍, UI 시퀀스)
- Redmine 이슈 설명에 재현 조건이 불명확하거나 "재현 불가" 기재된 경우

**분석 방법**:

1. **코드 경로 역추적**: 4단계에서 찾은 버그 원인 코드의 호출 체인을 UI 진입점까지 역추적
   - 이벤트 핸들러(`OnClick`, `OnChange` 등) → 폼 → 메뉴/버튼 매핑
   - `.dfm` 파일에서 컴포넌트의 이벤트 바인딩과 `Caption` 확인
   - 예: `procedure TfrmXxx.btnSaveClick` → `btnSave` → `.dfm`에서 Caption 확인

2. **분기 조건 추출**: 버그 코드까지 도달하기 위한 모든 `if`/`case` 조건을 역순으로 정리
   - DB 쿼리의 `WHERE` 조건 → 필요한 데이터 상태 도출
   - 파라미터 값 범위 → 어떤 입력이 버그 경로로 진입하는지 도출
   - 전역 변수/설정값 의존성 → 환경 설정 조건 도출

3. **환경 조건 식별**: Win32 API 호출, COM 객체, 외부 프로세스 의존성 파악
   - `GetPrinterPort`, WinSpool API → 프린터 설정 조건
   - Network 관련 → IP, 포트, 방화벽 조건
   - Registry 접근 → 레지스트리 키 존재 여부

4. **시퀀스 조건 식별**: `Application.ProcessMessages`, 비동기 콜백, 타이머 이벤트 관련 코드
   - 재진입 가드(`FIsProcessing` 등)의 존재/부재가 시퀀스 버그의 단서

**출력 형식** (`01_investigation.md`의 `## 재현 가이드` 섹션):

```
### 전제조건
[DB에 필요한 데이터 상태, 설정값 등]

### UI 진입 경로
[메뉴 > 화면 > 탭 > 버튼 순서. .dfm의 Caption 값 사용]

### 재현 절차
1. [구체적인 조작 단계]
2. [다음 단계]
→ 예상 결과: [정상 동작]
→ 실제 결과: [버그 현상]

### 환경 조건 (해당 시)
[프린터/네트워크/OS/권한 등 특수 환경 조건]

### 검증 방법
[버그 수정 후 동일 절차로 검증하는 방법]
```

## YSR 코드베이스 특성

### 디렉토리 역할
| 경로 | 역할 |
|------|------|
| `trunk/Common/` | 전역 공통 유틸리티 (암호화, DB, UI 헬퍼) |
| `trunk/CommonBL/` | BL 빌드용 공통 |
| `trunk/Module/Chart/` | 전자의료기록 차트 핵심 |
| `trunk/Module/Counter/` | 진료비 계산 |
| `trunk/Module/Insurance/` | 보험청구/DRG |
| `trunk/Module/AddOn/` | 협진, 음성녹음, 장비연동 |
| `trunk/Module/Support/` | 출력, 검사 지원 도구 |
| `trunk/Module/Tool/` | 데이터 마이그레이션, 설정 도구 |
| `trunk/Projects/` | 독립 실행 프로젝트 |

### 버전 접미사
- `_D7`: Delphi 7 전용
- `_BL`: Builder Live 버전
- `_v2007`, `_XE7`: 특정 Delphi 버전

버그가 특정 버전에서만 발생한다면 해당 접미사 파일을 먼저 확인한다.

### 프린터/네트워크 관련 버그
최근 유지보수의 주요 패턴. 관련 파일:
- `NetworkUtils.cs` — IP 검증, 포트 설정
- `PrinterUtil.cs` — 프린터 포트 관리, 설명 입력
- Win32 API 호출 래퍼 함수 확인 필요

### 보험청구 관련 버그
- `trunk/Module/Insurance/` 하위 탐색
- EDI 전송 코드는 C# 기반 (`*.cs`)
- 계산 로직은 Delphi 기반 (`*.pas`)

### UI 진입점 파악 패턴
- `.dfm`의 `Caption` 속성 → 사용자에게 보이는 버튼/메뉴명
- `TAction`의 `Caption`과 `ShortCut` → 메뉴/단축키 진입점
- `TPageControl`의 `ActivePage` 전환 이벤트 → 탭 전환 시나리오
- `TMainMenu`/`TPopupMenu` 구조 → 메뉴 계층 구조
- `.dfm`은 CP949 인코딩이므로 한글 Caption이 깨져 보일 수 있음. 컴포넌트명과 이벤트 바인딩은 영문이므로 코드 경로 역추적에 충분함.
