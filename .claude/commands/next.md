# /next — 다음 실행할 에이전트 안내

docs/STATUS.md를 읽고 현재 PHASE를 확인한 뒤, 다음에 실행해야 할 명령어를 출력해줘.

## 분기 로직

- PHASE 1~4.5 → Orchestrator
  ```
  .claude/agents/orchestrator.md와 docs/STATUS.md를 읽고 현재 PHASE부터 실행해줘.
  [PAUSE] 지점에서 멈추고 내 확인을 기다려.
  코드 구현은 하지 마. 계획 문서 작성만 해.
  ```

- PHASE 5 → Planner
  ```
  .claude/agents/planner.md와 docs/STATUS.md를 읽고 현재 스프린트 GOAL.md를 작성해줘.
  코드 구현은 하지 마. GOAL.md 작성만 해.
  완료되면 다음 에이전트 실행 방법을 알려줘.
  ```

- PHASE 6 → Implementer
  ```
  .claude/agents/implementer.md와 docs/STATUS.md를 읽고
  sprints/{CURRENT_SPRINT}/GOAL.md 기준으로 구현 시작해줘.
  [PAUSE] 지점에서 멈추고 내 확인을 기다려.
  GOAL.md 범위 밖의 기능은 구현하지 마.
  ```

- PHASE 7~10 → Validator
  ```
  .claude/agents/validator.md와 docs/STATUS.md를 읽고
  sprints/{CURRENT_SPRINT} 검증을 시작해줘.
  [PAUSE] 지점에서 멈추고 내 확인을 기다려.
  ```

## 별도 프로세스 안내

현재 브랜치가 `hotfix/*`이면:
```
.claude/agents/hotfix-close.md와 docs/STATUS.md를 읽고
현재 hotfix 브랜치의 마무리 작업을 진행해줘.
```

Sprint이 완료(PHASE 10)되고 배포가 필요하면:
```
.claude/agents/deploy-prod.md와 docs/STATUS.md를 읽고
프로덕션 배포를 진행해줘.
```

## 출력 형식

```
┌─────────────────────────────────────┐
│ 다음 단계                           │
│                                     │
│ 현재: PHASE {N} — {PHASE 이름}     │
│ 실행: {에이전트명}                  │
│                                     │
│ 아래 명령어를 복사해서 실행하세요:  │
└─────────────────────────────────────┘

{해당 명령어}
```

- {CURRENT_SPRINT} 자리에는 docs/STATUS.md의 실제 스프린트명을 넣어줘
- 명령어는 코드 블록으로 감싸서 복사하기 쉽게 해줘
