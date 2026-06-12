---
paths:
  - "workspace/**/sprints/**"
  - "workspace/**/STATUS.md"
---

# Sprint 워크플로우 보완 규칙

> Sprint 기본 프로세스, 에이전트 역할, 커밋 형식은 `dev-process.md`를 참조하세요.
> 이 문서는 `dev-process.md`에 없는 고유 규칙만 포함합니다.

## 트랙 정의

모든 이슈는 `/prd` 실행 시 **자동 판정 + [PAUSE] 확정**으로 트랙이 결정된다.
STATUS.md의 `TRACK` 필드에 기록되며, 이후 모든 에이전트가 이 값을 참조한다.

### 판정 기준

| 항목 | Defect 트랙 (모두 충족해야 Defect) | Sprint 트랙 (하나라도 해당 시 Sprint) |
|------|-----------------------------------|--------------------------------------|
| 이슈 성격 | 프로덕션 장애·버그·긴급 수정 | 새 기능 추가 또는 여러 모듈 작업 |
| 변경 파일 수 | ≤ 3개 | ≥ 4개 |
| 변경 코드량 | ≤ 50줄 | > 50줄 |
| DB 스키마 변경 | 없음 | 필요 |
| 새 .pas 파일 | 없음 (dproj 변경 없음) | 필요 |

### 워크플로 비교

| 단계 | Sprint 트랙 | Defect 트랙 |
|------|-------------|-------------|
| PRD 생성 | `/prd` (기존 동일) | `/prd` (기존 동일) |
| Orchestrator | ✅ PHASE 1~4.5 | ⏭️ 스킵 |
| Planner | ✅ PHASE 5 | ⏭️ 스킵 |
| Implementer | ✅ PHASE 6 (GOAL.md 기준) | ✅ PHASE 6 (PRD `## 검증 계약` 기준) |
| Validator | ✅ PHASE 7~10 | ✅ PHASE 7~9 → PHASE 10에서 종료 |
| 브랜치 | 기존과 동일 | 기존과 동일 |

### 산출물 차이

**Sprint 트랙:**
```
workspace/{ACTIVE_ISSUE}/
├── plan.md, ROADMAP.md, TECH_DEBT.md, STATUS.md (TRACK=sprint)
└── sprints/sprint-NN/
    ├── GOAL.md, DONE.md, FEEDBACK.md, COMMIT_MESSAGE.md, OUT_OF_SCOPE.md
```

**Defect 트랙:**
```
workspace/{ACTIVE_ISSUE}/
├── STATUS.md      (TRACK=defect)
├── DONE.md        (sprints/ 없음, 루트에 직접)
├── COMMIT_MESSAGE.md
└── FEEDBACK.md    (검증 실패 시)
```

PRD는 양 모드 공통 `docs/PRD_{ACTIVE_ISSUE}.md`. Defect 트랙에서 PRD가 GOAL.md를 대체한다.

---

## GOAL.md 체크박스 관리

- **Implementer**: GOAL.md 체크박스 수정 금지. 기능 완료 시 `"✅ {기능명} 구현 완료"` 텍스트만 출력.
- **Validator**: 코드를 독립 검증한 뒤 `[ ]` → `[x]` 체크. 검증 실패 시 `FEEDBACK.md` 생성 후 Implementer로 타겟 수정 지시.

## 스프린트 진행 중 요구사항 변경

**경미한 변경** (구현 방법 수정, 세부사항 조정):
- Implementer가 GOAL.md 직접 수정 후 계속 진행

**중간 변경** (기능 추가/제거):
- [PAUSE] 후 사용자 확인 → GOAL.md 수정 → 계속 진행

**대규모 변경** (스프린트 목표 자체가 바뀌는 수준):
- 현재 스프린트 중단 → Planner가 GOAL.md 재작성
- workspace/{ACTIVE_ISSUE}/STATUS.md PHASE=5로 리셋

## 스프린트 Skip / 취소

**Skip** (스프린트를 건너뛰어야 할 때):
- workspace/{ACTIVE_ISSUE}/STATUS.md 스프린트 진행 현황에서 해당 스프린트 상태 → ⏭️ skip
- CURRENT_SPRINT → 다음 스프린트로 업데이트
- ROADMAP.md에 skip 이유 기록

**취소** (더 이상 필요 없는 스프린트):
- workspace/{ACTIVE_ISSUE}/STATUS.md에서 해당 스프린트 상태 → ❌ 취소
- workspace/#이슈번호/plan.md에 취소 이유 메모
- ROADMAP.md 해당 행에 취소 표시

## 신규 요구사항 (MVP 완료 후)

모든 스프린트 완료 후 새 요구사항이 생기면:
- 규모 판단: 신규 스프린트 추가 → Orchestrator PHASE 11 (Re-plan)
- Re-plan: Orchestrator PHASE 11 진입
  명령어: `.claude/agents/orchestrator.md와 workspace/{ACTIVE_ISSUE}/STATUS.md 읽고 PHASE 11 실행해줘`

## 누적 Tech Debt 관리

- `sprints/TECH_DEBT.md` — 모든 스프린트의 기술 부채 중앙 관리
- Validator가 스프린트 종료 시 OUT_OF_SCOPE.md + TODO 주석을 여기에 집계
- Planner는 GOAL.md 작성 전 TECH_DEBT.md를 읽고 처리 가능한 항목 반영
- 처리 완료 시 ✅ 표시 (삭제하지 않고 이력 유지)

## 체크리스트 형식

- 완료: `[x]` 또는 `✅`
- 미완료: `[ ]` 또는 `⬜`
