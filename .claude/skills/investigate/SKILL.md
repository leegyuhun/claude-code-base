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
