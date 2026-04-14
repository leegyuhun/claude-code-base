# STATUS.md — 파이프라인 현재 상태

> 모든 에이전트가 공유하는 상태 파일.
> 각 에이전트는 담당 PHASE 완료 시 즉시 업데이트한다.
> 세션이 끊겨도 이 파일 기준으로 재개 가능.

---

## 현재 상태

```
PHASE:            1
CURRENT_SPRINT:   -
LAST_COMMIT:      -
LAST_PR:          -
UPDATED_AT:       -
```

## PHASE 정의

```
--- Sprint 프로세스 (메인 흐름) ---
1    = PRD 분석                      (Orchestrator)
2    = Plan 생성                     (Orchestrator)
3    = Plan 확인 [PAUSE]             (Orchestrator)
4    = Sprint 세분화                 (Orchestrator)
4.5  = 프로젝트 초기화 & CLAUDE.md   (Orchestrator) [PAUSE]
5    = Sprint 계획                   (Planner)      ← 스프린트마다 반복
6    = Sprint 실행                   (Implementer)  ← 스프린트마다 반복
7    = Sprint 검증                   (Validator)    ← 스프린트마다 반복
8    = Sprint 확인 [PAUSE]           (Validator)    ← 스프린트마다 반복
9    = Sprint 종료 / PR              (Validator)    ← 스프린트마다 반복
10   = 다음 Sprint 진행              (Validator)    ← 스프린트마다 반복
11   = 신규 요구사항 반영 (Re-plan)  (Orchestrator) ← MVP 완료 후 신규 요구사항 시

--- 배포 프로세스 (Sprint 완료 후) ---
D    = deploy-prod 에이전트 사용 (Sprint 검증 완료 후)
```

---

## 에이전트 완료 현황

```
ORCHESTRATOR:   pending   (PHASE 1~4.5)
PLANNER:        pending   (PHASE 5)
IMPLEMENTER:    pending   (PHASE 6)
VALIDATOR:      pending   (PHASE 7~10)
DEPLOY-PROD:    -         (배포 시 사용)
```

---

## 스프린트 진행 현황

| 스프린트 | 상태 | 브랜치 | 커밋 | PR | 완료일 |
|---|---|---|---|---|---|
| sprint-01 | ⬜ 대기 | - | - | - | - |

> 상태: ⬜ 대기 / 🔄 진행중 / ✅ 완료 / ❌ 실패 / ⏭️ skip / 🚫 취소

---

## 현재 스프린트 진행률

```
SPRINT:   -
PROGRESS: 0 / 0
ITEMS:
  [ ] 예시 작업
```

---

## 에이전트별 재개 명령어

### Orchestrator (PHASE 1~4.5)
```
.claude/agents/orchestrator.md와 docs/STATUS.md를 읽고 현재 PHASE부터 실행해줘.
[PAUSE] 지점에서 멈추고 내 확인을 기다려.
코드 구현은 하지 마. 계획 문서 작성만 해.
```

### Planner (PHASE 5)
```
.claude/agents/planner.md와 docs/STATUS.md를 읽고 현재 스프린트 GOAL.md를 작성해줘.
코드 구현은 하지 마. GOAL.md 작성만 해.
완료되면 다음 에이전트 실행 방법을 알려줘.
```

### Implementer (PHASE 6)
```
.claude/agents/implementer.md와 docs/STATUS.md를 읽고
sprints/{CURRENT_SPRINT}/GOAL.md 기준으로 구현 시작해줘.
[PAUSE] 지점에서 멈추고 내 확인을 기다려.
GOAL.md 범위 밖의 기능은 구현하지 마.
```

### Validator (PHASE 7~10)
```
.claude/agents/validator.md와 docs/STATUS.md를 읽고
sprints/{CURRENT_SPRINT} 검증을 시작해줘.
[PAUSE] 지점에서 멈추고 내 확인을 기다려.
```

### Orchestrator Re-plan (PHASE 11 — 신규 요구사항)
```
.claude/agents/orchestrator.md와 docs/STATUS.md를 읽고 PHASE 11을 실행해줘.
[PAUSE] 지점에서 멈추고 내 확인을 기다려.
코드 구현은 하지 마. plan.md와 ROADMAP.md 업데이트만 해.
```

### Deploy-Prod (배포)
```
.claude/agents/deploy-prod.md와 docs/STATUS.md를 읽고
프로덕션 배포를 진행해줘.
```

### Sprint-Dev 커맨드 (구현 오케스트레이터)
```
/sprint-dev {스프린트번호}
```
