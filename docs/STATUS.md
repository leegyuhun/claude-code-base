# STATUS.md — 파이프라인 상태 (양식 참고)

> 이 문서는 STATUS.md **양식과 PHASE 정의 참고용**이다.
> 실제 상태 파일은 이슈별로 격리된 `workspace/{ACTIVE_ISSUE}/STATUS.md`에 생성된다.
> STATUS.md는 파이프라인 **포인터**(PHASE/TRACK/스프린트)이며, KEEP 커맨드(/status·/next·/rollback)가 읽는다.
> 루프 이터레이션의 시도/결과 로그는 STATUS.md가 아니라 `PROGRESS.md`에 기록된다.

---

## 현재 상태 (양식)

```
PHASE:            1
TRACK:            sprint        # sprint | defect
CURRENT_SPRINT:   -
LAST_COMMIT:      -
LAST_PR:          -
UPDATED_AT:       -
```

## PHASE 정의

```
--- 계획 (Orchestrator·Planner — 사람 판단 PAUSE) ---
1    = PRD 분석                      (Orchestrator)
2    = Plan 생성                     (Orchestrator)
3    = Plan 확인 [PAUSE]             (Orchestrator)
4    = Sprint 세분화                 (Orchestrator)
4.5  = 프로젝트 초기화 & CLAUDE.md   (Orchestrator) [PAUSE]
5    = Sprint 계획 (GOAL.md)         (Planner)      ← 스프린트마다 반복

--- 구현 루프 (loop-sprint — Maker⇄Checker 자동 반복) ---
6    = 구현 루프                     (loop-sprint)  ← 진입 시 설정. 자동검증(구 7)까지 흡수
7    = (루프 내부 통합 게이트)        (loop-sprint)  ← 별도 정지 없음. PHASE 6 루프가 자동 수행
                                                     빌드/테스트/검증계약/코드리뷰 종료조건 판정

--- 사람 게이트 (validator — 루프 종료 후) ---
8    = 수동 테스트 [PAUSE]           (validator)    ← 루프 종료 시 PHASE=8 설정
9    = 종료 / commit / push / MR     (validator)
10   = 다음 Sprint 진행 / 완료        (validator)
11   = 신규 요구사항 반영 (Re-plan)  (Orchestrator) ← MVP 완료 후 신규 요구사항 시

--- 배포 (Sprint 완료 후) ---
D    = deploy-prod 에이전트 사용
```

> Defect 트랙: PHASE 1~5(Orchestrator·Planner) 스킵. PRD `## 검증 계약`이 GOAL.md 대체.
> /prd가 TRACK=defect로 설정 시 PHASE=6에서 시작.

---

## 에이전트 / 루프 완료 현황 (양식)

```
ORCHESTRATOR:   pending   (PHASE 1~4.5)
PLANNER:        pending   (PHASE 5)
LOOP-SPRINT:    pending   (PHASE 6~7, Maker=implementer ⇄ Checker)
VALIDATOR:      pending   (PHASE 8~10, 사람 게이트)
DEPLOY-PROD:    -         (배포 시 사용)
```

---

## 스프린트 진행 현황 (양식)

| 스프린트 | 상태 | 브랜치 | 커밋 | PR | 완료일 |
|---|---|---|---|---|---|
| sprint-01 | ⬜ 대기 | - | - | - | - |

> 상태: ⬜ 대기 / 🔄 진행중 / ✅ 완료 / ❌ 실패 / ⏭️ skip / 🚫 취소

---

## 현재 스프린트 진행률 (양식)

```
SPRINT:   -
PROGRESS: 0 / 0
ITEMS:
  [ ] 예시 작업
```

> 루프 이터레이션 로그(시도/결과/다음계획)는 PROGRESS.md 참조.

---

## 재개 명령어

### Orchestrator (PHASE 1~4.5)
```
.claude/agents/orchestrator.md와 workspace/{이슈}/STATUS.md를 읽고 현재 PHASE부터 실행해줘.
[PAUSE] 지점에서 멈추고 내 확인을 기다려.
코드 구현은 하지 마. 계획 문서 작성만 해.
```

### Planner (PHASE 5)
```
.claude/agents/planner.md와 workspace/{이슈}/STATUS.md를 읽고 현재 스프린트 GOAL.md를 작성해줘.
코드 구현은 하지 마. GOAL.md 작성만 해.
완료되면 다음 단계 실행 방법을 알려줘.
```

### loop-sprint (PHASE 6~7 — 구현 ⇄ 검증 자동 반복)
```
/loop-sprint
```
> 종료조건(빌드 0에러·테스트·검증계약 자동항목·리뷰 Critical/High 0) 충족까지 자동 반복.
> 세션이 끊겨도 PROGRESS.md 기준으로 재진입하면 이어서 진행한다.

### loop-build-fix (빌드만 복구할 때)
```
/loop-build-fix
```

### Validator (PHASE 8~10 — 사람 게이트)
```
.claude/agents/validator.md와 workspace/{이슈}/STATUS.md를 읽고
sprints/{CURRENT_SPRINT} 검증을 시작해줘.
[PAUSE] 지점에서 멈추고 내 확인을 기다려.
```

### Orchestrator Re-plan (PHASE 11 — 신규 요구사항)
```
.claude/agents/orchestrator.md와 workspace/{이슈}/STATUS.md를 읽고 PHASE 11을 실행해줘.
[PAUSE] 지점에서 멈추고 내 확인을 기다려.
코드 구현은 하지 마. plan.md와 ROADMAP.md 업데이트만 해.
```

### Deploy-Prod (배포)
```
.claude/agents/deploy-prod.md와 workspace/{이슈}/STATUS.md를 읽고
프로덕션 배포를 진행해줘.
```
