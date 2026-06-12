---
paths:
  - always
---

# 워크스페이스 해석 규칙 (Active Issue)

모든 에이전트/커맨드는 작업 시작 시 아래 순서로 ACTIVE_ISSUE와 WORKSPACE_DIR를 결정한다.

## 변수 정의

| 변수 | 예시 | 설명 |
|---|---|---|
| ACTIVE_ISSUE | `#208801` 또는 `exp_login` | 현재 작업 중인 이슈 번호 또는 임시 ID |
| WORKSPACE_DIR | `workspace/#208801` | 이슈별 산출물 루트 |
| STATUS_FILE | `workspace/#208801/STATUS.md` | 파이프라인 상태 파일 |
| PLAN_FILE | `workspace/#208801/plan.md` | 계획 문서 |
| ROADMAP_FILE | `workspace/#208801/sprints/ROADMAP.md` | 스프린트 로드맵 |
| TECH_DEBT_FILE | `workspace/#208801/sprints/TECH_DEBT.md` | 누적 기술 부채 |
| SPRINT_DIR | `workspace/#208801/sprints/{CURRENT_SPRINT}` | 현재 스프린트 디렉토리 |
| PRD_FILE | `docs/PRD_#208801.md` | 입력 문서 (docs/ 고정, 변경 없음) |

## 해석 순서

### 1단계 — `.claude/ACTIVE_ISSUE` 파일 읽기

파일이 존재하고 비어있지 않으면 그 값을 ACTIVE_ISSUE로 사용한다.

형식:
  - 이슈번호: `#NNNNNN` (예: `#208801`)
  - 임시 ID: `^[a-z][a-z0-9_]{2,30}$` (예: `exp_login`)

### 2단계 — (폴백) git 브랜치명에서 추출

`.claude/ACTIVE_ISSUE`가 없거나 비어있을 때:

```bash
git branch --show-current
```

출력에서 `#(\d+)` 패턴을 매칭한다.
예: `main_delphi_#208801_sprint-01` → `#208801`

### 3단계 — (실패) 사용자 안내 후 중단

두 방법 모두 실패하면 에이전트 실행을 중단하고 아래 메시지를 출력한다:

```
⚠️ 활성 이슈를 확인할 수 없습니다.

다음 중 하나를 실행해주세요:
  /prd #이슈번호    ← 새 이슈 시작 (권장)
  /prd              ← 이슈번호 없이 시작 (임시 ID 입력 받음)
  .claude/ACTIVE_ISSUE 파일에 #이슈번호 직접 입력
```

## WORKSPACE_DIR 구성

```
WORKSPACE_DIR = workspace/{ACTIVE_ISSUE}
```

예: `workspace/#208801`

## 이슈 없이 작업하는 경우

이슈 번호가 없는 실험성·임시 작업은 **임시 ID**로 격리한다.
- `/prd`를 이슈번호 없이 실행하면 Phase 0에서 [PAUSE]로 임시 ID 입력을 요구한다.
- 임시 ID 형식: `^[a-z][a-z0-9_]{2,30}$` (영문 소문자/숫자/언더스코어, 첫 글자 영문)
- 예: `exp_login`, `bug_repro_001`, `learn_async`
- `.claude/ACTIVE_ISSUE`에 임시 ID 그대로 기록 (`#` 접두사 없음)
- WORKSPACE_DIR = `workspace/{임시ID}` (예: `workspace/exp_login`)
- 청소: 작업 완료 후 `workspace/{임시ID}/` 디렉토리 수동 삭제 (브랜치 정리 시 함께 처리 권장)

## 브랜치/포인터 불일치 감지 (`/status` 전용)

`/status` 실행 시 자동 감지한다:

ACTIVE_ISSUE 값이 `#NNNNNN` 형식일 때만 검사한다. 임시 ID(`#` 접두사 없음)는 검사 대상 외.

`.claude/ACTIVE_ISSUE`의 이슈 번호와 현재 브랜치명에서 추출한 이슈 번호(`#(\d+)`)가 다르면:

```
⚠️ ACTIVE_ISSUE(#208801) ≠ 브랜치 이슈(#208900)
.claude/ACTIVE_ISSUE를 수동 수정하거나 /prd #이슈번호 로 전환하세요.
```

자동 수정하지 않음 — 의도적 불일치일 수 있음.

## ACTIVE_ISSUE 자동 갱신 시점

| 트리거 | 담당 |
|---|---|
| `/prd #이슈번호` 실행 시 | prd 커맨드 |
| Orchestrator PHASE 1 시작 시 (이슈번호 감지 시) | orchestrator 에이전트 |

## 에이전트 코드 패턴 (참조용)

각 에이전트 첫 단계에서 아래 순서로 수행:

```
[워크스페이스 해석]
1. .claude/ACTIVE_ISSUE 읽기
2. ACTIVE_ISSUE 값이 없으면 git 브랜치에서 추출
3. 모두 실패 시 → 사용자 안내 후 종료
4. WORKSPACE_DIR = workspace/{ACTIVE_ISSUE}
5. STATUS_FILE = {WORKSPACE_DIR}/STATUS.md
6. workspace/{ACTIVE_ISSUE}/ 디렉토리 없으면 생성
```
