# /next — 다음 실행할 에이전트 안내

## 워크스페이스 해석

1. `.claude/ACTIVE_ISSUE` 읽기 → ACTIVE_ISSUE 값 획득
2. 없으면 `git branch --show-current` 출력에서 `#([A-Za-z0-9-]+)` 추출 (폴백)
3. 모두 실패 시 → "`⚠️ 활성 이슈를 확인할 수 없습니다. /prd #이슈번호 를 실행하세요.`" 출력 후 종료

WORKSPACE_DIR = `workspace/{ACTIVE_ISSUE}`
STATUS_FILE = `{WORKSPACE_DIR}/STATUS.md`

`{STATUS_FILE}`을 읽고 현재 PHASE를 확인한 뒤, 다음에 실행해야 할 명령어를 출력해줘.

## 분기 로직

### 0단계 — 루프 중단 상태 확인 (PHASE 분기보다 먼저)

`{STATUS_FILE}`의 `LOOP` 값이 `halted`면, 재시도 상한이나 헛돌기 감지에 걸려
자동 진행이 멈춘 상태다. **PHASE 안내보다 이것을 먼저 출력한다.**

```
python .claude/scripts/loop_state.py status
```

출력 형식:

```
┌─────────────────────────────────────┐
│ ⛔ 루프 중단됨                       │
│                                     │
│ 사유: {HALT_REASON}                 │
│ PHASE: {N} (변경되지 않았음)         │
└─────────────────────────────────────┘

최근 시도 (workspace/{ACTIVE_ISSUE}/.loop/attempts.log):
  {최근 3~5줄}

같은 방법으로 재시도하면 같은 결과가 나온다. 접근을 바꾸거나 범위를 줄여야 한다.

판단 후 재개하려면:
  python .claude/scripts/loop_state.py clear-halt

그 다음 아래 PHASE 안내를 따른다.
```

`LOOP`가 없거나 `running`이면 아래로 진행한다.

### 1단계 — TRACK 확인

`{STATUS_FILE}`에서 `TRACK` 값을 먼저 확인한다.

### TRACK=defect 인 경우

- PHASE 1~5 → Defect 트랙에서는 이 단계를 건너뜁니다.
  ```
  ⚠️ TRACK=defect — Orchestrator·Planner 단계는 Defect 트랙에서 스킵됩니다.
  구현을 바로 시작하려면 Implementer를 실행하세요.
  ```
  (STATUS.md의 PHASE가 1~5로 남아있으면 PHASE=6 으로 수동 수정을 안내한다)

- PHASE 6 → Implementer (PRD 기준)
  ```
  /sprint-dev
  ```
  (sprint-dev는 TRACK=defect 감지 시 PRD의 `## 검증 계약` 섹션을 GOAL 대체로 사용한다)

- PHASE 7~9 → Validator
  ```
  .claude/agents/validator.md를 읽고 TRACK=defect 모드로 검증을 시작해줘.
  [PAUSE] 지점에서 멈추고 내 확인을 기다려.
  ```

- PHASE 10 → Defect 트랙 완료
  ```
  ✅ Defect 트랙이 완료되었습니다.
  이슈 트래커를 쓴다면 해당 이슈 상태를 직접 갱신하세요.
  프로덕션 배포가 필요하면: .claude/agents/deploy-prod.md를 읽고 배포를 진행해줘.
  ```

### TRACK=sprint 또는 TRACK 미지정인 경우

- PHASE 1~4.5 → Orchestrator
  ```
  .claude/agents/orchestrator.md를 읽고 현재 PHASE부터 실행해줘.
  [PAUSE] 지점에서 멈추고 내 확인을 기다려.
  코드 구현은 하지 마. 계획 문서 작성만 해.
  ```

- PHASE 5 → Planner
  ```
  .claude/agents/planner.md를 읽고 현재 스프린트 GOAL.md를 작성해줘.
  코드 구현은 하지 마. GOAL.md 작성만 해.
  완료되면 다음 에이전트 실행 방법을 알려줘.
  ```

- PHASE 6 → Implementer
  ```
  /sprint-dev
  ```

- PHASE 7~9 → Validator
  ```
  .claude/agents/validator.md를 읽고
  {WORKSPACE_DIR}/sprints/{CURRENT_SPRINT} 검증을 시작해줘.
  [PAUSE] 지점에서 멈추고 내 확인을 기다려.
  ```

- PHASE 10 → 스프린트 완료 상태에 따라 분기
  먼저 {STATUS_FILE}의 `PIPELINE` 값과 스프린트 진행 현황을 확인한다.

  - **다음 스프린트가 남아있는 경우** (진행 현황에 ⬜/🔄 스프린트 존재):
    > Validator가 정상 종료했다면 이미 PHASE=5로 전환되어 이 경우는 드물다. 방어적으로 안내한다.
    ```
    .claude/agents/planner.md를 읽고 현재 스프린트 GOAL.md를 작성해줘.
    코드 구현은 하지 마. GOAL.md 작성만 해.
    ```

  - **모든 스프린트 완료** (`PIPELINE=mvp_done` 이거나 진행 현황이 전부 ✅/⏭️/❌):
    ```
    🎉 MVP 달성 — 모든 스프린트가 완료되었습니다.

    이후 경로를 선택하세요:
      [배포]        .claude/agents/deploy-prod.md를 읽고 프로덕션 배포를 진행해줘.
      [신규 요구사항] .claude/agents/orchestrator.md와 {STATUS_FILE} 읽고 PHASE 11을 실행해줘.
                     [PAUSE] 지점에서 멈추고 내 확인을 기다려.
                     코드 구현은 하지 마. plan.md와 ROADMAP.md 업데이트만 해.
    ```
    (Validator가 PHASE=10에 머문 채 종료하므로, 신규 요구사항은 위 명령으로 orchestrator를
     PHASE 11 모드로 직접 호출해야 진입한다. orchestrator PHASE 11이 plan.md·ROADMAP.md를
     갱신한 뒤 PHASE=5로 재진입시킨다.)

- PHASE 11 → Orchestrator (Re-plan)
  ```
  .claude/agents/orchestrator.md를 읽고 PHASE 11을 실행해줘.
  [PAUSE] 지점에서 멈추고 내 확인을 기다려.
  코드 구현은 하지 마. {WORKSPACE_DIR}/plan.md와 {WORKSPACE_DIR}/sprints/ROADMAP.md 업데이트만 해.
  ```

## 별도 프로세스 안내

Sprint이 완료(PHASE 10)되고 배포가 필요하면:
```
.claude/agents/deploy-prod.md를 읽고 프로덕션 배포를 진행해줘.
```

## 출력 형식

```
┌─────────────────────────────────────┐
│ 다음 단계                           │
│                                     │
│ 이슈:    {ACTIVE_ISSUE}             │
│ 현재: PHASE {N} — {PHASE 이름}     │
│ 실행: {에이전트명}                  │
│                                     │
│ 아래 명령어를 복사해서 실행하세요:  │
└─────────────────────────────────────┘

{해당 명령어}
```

- {CURRENT_SPRINT} 자리에는 {STATUS_FILE}의 실제 스프린트명을 넣어줘
- 명령어는 코드 블록으로 감싸서 복사하기 쉽게 해줘
