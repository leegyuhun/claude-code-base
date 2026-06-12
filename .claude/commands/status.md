# /status — 현재 파이프라인 상태 요약

## 워크스페이스 해석

1. `.claude/ACTIVE_ISSUE` 읽기 → ACTIVE_ISSUE 값 획득
2. 없으면 `git branch --show-current` 출력에서 `#(\d+)` 추출 (폴백)
3. 모두 실패 시 → "`⚠️ 활성 이슈를 확인할 수 없습니다. /prd #이슈번호 를 실행하세요.`" 출력

WORKSPACE_DIR = `workspace/{ACTIVE_ISSUE}`
STATUS_FILE = `{WORKSPACE_DIR}/STATUS.md`

## 브랜치/포인터 불일치 감지

현재 브랜치명에서 `#(\d+)` 추출 → ACTIVE_ISSUE와 다르면:
```
⚠️ ACTIVE_ISSUE({ACTIVE_ISSUE}) ≠ 브랜치 이슈({브랜치 이슈번호})
.claude/ACTIVE_ISSUE를 수동 수정하거나 /prd #이슈번호 로 전환하세요.
```

## 상태 출력

{STATUS_FILE}을 읽고 `TRACK` 값에 따라 아래 형식으로 요약해줘.

**TRACK=defect 인 경우 (Defect 트랙, PHASE=6~10):**
```
┌─────────────────────────────────────┐
│ 현재 상태                           │
│                                     │
│ 이슈:    {ACTIVE_ISSUE}             │
│ 워크스페이스: {WORKSPACE_DIR}       │
│ 트랙:    defect (경량)              │
│ PHASE:   {N} — {PHASE 이름}        │
│          (PHASE=10이면: ✅ Defect   │
│           트랙 완료)                │
│ 담당:    {에이전트명}               │
│                                     │
│ 산출물 위치: {WORKSPACE_DIR}/       │
│  PRD: docs/PRD_{ACTIVE_ISSUE}.md   │
│  DONE.md: {WORKSPACE_DIR}/DONE.md  │
│   (GOAL.md/sprints/ 없음)          │
│                                     │
│ 미커밋 변경: {git status 요약}      │
└─────────────────────────────────────┘
```

**TRACK=sprint 또는 미지정인 경우 (Sprint 트랙):**
```
┌─────────────────────────────────────┐
│ 현재 상태                           │
│                                     │
│ 이슈:    {ACTIVE_ISSUE}             │
│ 워크스페이스: {WORKSPACE_DIR}       │
│ 트랙:    sprint                     │
│ PHASE:   {N} — {PHASE 이름}        │
│ 담당:    {에이전트명}               │
│ 스프린트: {CURRENT_SPRINT 또는 -}   │
│                                     │
│ 에이전트 현황:                      │
│  Orchestrator: {상태}               │
│  Planner:      {상태}               │
│  Implementer:  {상태}               │
│  Validator:    {상태}               │
│                                     │
│ 스프린트 진행:                      │
│  {sprint-01}: {상태}                │
│  {sprint-02}: {상태}                │
│  ...                                │
└─────────────────────────────────────┘
```

추가로:
- Sprint 트랙이면: CURRENT_SPRINT의 GOAL.md(`{WORKSPACE_DIR}/sprints/{CURRENT_SPRINT}/GOAL.md`) 존재 여부, 체크리스트 진행률도 표시
- LAST_COMMIT, LAST_PR 값이 있으면 마지막 줄에 표시
