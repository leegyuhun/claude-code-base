# /status — 현재 파이프라인 상태 요약

docs/STATUS.md를 읽고 아래 형식으로 요약해줘.

```
┌─────────────────────────────────────┐
│ 현재 상태                           │
│                                     │
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
- CURRENT_SPRINT이 있으면 해당 스프린트의 GOAL.md 존재 여부, 체크리스트 진행률도 표시
- LAST_COMMIT, LAST_PR 값이 있으면 마지막 줄에 표시
