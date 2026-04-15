---
paths:
  - "sprints/**"
  - "docs/STATUS.md"
---

# Sprint 워크플로우 보완 규칙

> Sprint 기본 프로세스, 에이전트 역할, 커밋 형식은 `dev-process.md`를 참조하세요.
> 이 문서는 `dev-process.md`에 없는 고유 규칙만 포함합니다.

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
- docs/STATUS.md PHASE=5로 리셋

## 스프린트 Skip / 취소

**Skip** (스프린트를 건너뛰어야 할 때):
- docs/STATUS.md 스프린트 진행 현황에서 해당 스프린트 상태 → ⏭️ skip
- CURRENT_SPRINT → 다음 스프린트로 업데이트
- ROADMAP.md에 skip 이유 기록

**취소** (더 이상 필요 없는 스프린트):
- docs/STATUS.md에서 해당 스프린트 상태 → ❌ 취소
- plan.md에 취소 이유 메모
- ROADMAP.md 해당 행에 취소 표시

## 신규 요구사항 (MVP 완료 후)

모든 스프린트 완료 후 새 요구사항이 생기면:
- 규모 판단: 신규 스프린트 추가 → Orchestrator PHASE 11 (Re-plan)
- Re-plan: Orchestrator PHASE 11 진입
  명령어: `.claude/agents/orchestrator.md와 docs/STATUS.md 읽고 PHASE 11 실행해줘`

## 누적 Tech Debt 관리

- `sprints/TECH_DEBT.md` — 모든 스프린트의 기술 부채 중앙 관리
- Validator가 스프린트 종료 시 OUT_OF_SCOPE.md + TODO 주석을 여기에 집계
- Planner는 GOAL.md 작성 전 TECH_DEBT.md를 읽고 처리 가능한 항목 반영
- 처리 완료 시 ✅ 표시 (삭제하지 않고 이력 유지)

## 체크리스트 형식

- 완료: `[x]` 또는 `✅`
- 미완료: `[ ]` 또는 `⬜`
