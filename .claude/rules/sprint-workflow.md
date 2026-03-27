---
paths:
  - "sprints/**"
  - "STATUS.md"
---

# Sprint/Hotfix 워크플로우 규칙

## Sprint 프로세스

### 1. 계획 (Orchestrator → Planner)
- Orchestrator: PRD 분석 → plan.md → ROADMAP.md → 프로젝트 초기화
- Planner: ROADMAP.md 기준으로 `sprints/{CURRENT_SPRINT}/GOAL.md` 생성
- GOAL.md는 **실행 명세서**: 기능 체크리스트, 완료 조건, 예상 산출물 포함
- 사용자가 검토/승인한 후 구현 단계로 진행

### 2. 구현 (Implementer)
- `{현재 브랜치명}_{CURRENT_SPRINT}` 브랜치 생성 (예: `main_sprint-01`)
- GOAL.md 체크리스트 순서대로 구현
- 기능 단위로 중간 커밋: `wip: [{CURRENT_SPRINT}] {기능명}`
- 완료마다 GOAL.md `[ ]` → `[x]` 업데이트
- GOAL.md 범위 밖 발견사항 → `sprints/{CURRENT_SPRINT}/OUT_OF_SCOPE.md`에 기록
- karpathy-guidelines 준수

### 3. 검증 (Validator)
- 빌드/린트/타입체크/테스트 자동 검증
- 수동 테스트 가이드 제시 후 사용자 확인
- 실패 시 Implementer로 롤백 가능

### 4. 종료 (Validator)
- DONE.md 생성 + PR 생성
- PR 머지 후 다음 스프린트 진행

## Hotfix 프로세스

1. 현재 브랜치 기반 `{현재브랜치}_hotfix/{설명}` 브랜치 생성
   예: `main_hotfix/login-fix`
2. 수정 후 hotfix-close 에이전트 실행
3. 베이스 브랜치로 PR 생성 → 머지 후 진행 중인 스프린트 브랜치에 역머지

## Hotfix vs Sprint 판단 기준

**Hotfix** (모두 충족 시):
- 프로덕션 장애/버그이거나 긴급 수정
- 변경 파일 3개 이하, 코드 50줄 이하
- DB 스키마 변경 없음
- 새 의존성 추가 없음

**Sprint** (하나라도 해당 시):
- 새 기능 추가 또는 여러 모듈에 걸친 작업
- DB 스키마 변경 필요
- 새 의존성 추가 필요
- 파일 4개 이상 또는 코드 50줄 초과

## 스프린트 진행 중 요구사항 변경

**경미한 변경** (구현 방법 수정, 세부사항 조정):
- Implementer가 GOAL.md 직접 수정 후 계속 진행

**중간 변경** (기능 추가/제거):
- [PAUSE] 후 사용자 확인 → GOAL.md 수정 → 계속 진행

**대규모 변경** (스프린트 목표 자체가 바뀌는 수준):
- 현재 스프린트 중단 → Planner가 GOAL.md 재작성
- STATUS.md PHASE=5로 리셋

## 스프린트 Skip / 취소

**Skip** (스프린트를 건너뛰어야 할 때):
- STATUS.md 스프린트 진행 현황에서 해당 스프린트 상태 → ⏭️ skip
- CURRENT_SPRINT → 다음 스프린트로 업데이트
- ROADMAP.md에 skip 이유 기록

**취소** (더 이상 필요 없는 스프린트):
- STATUS.md에서 해당 스프린트 상태 → ❌ 취소
- plan.md에 취소 이유 메모
- ROADMAP.md 해당 행에 취소 표시

## 신규 요구사항 (MVP 완료 후)

모든 스프린트 완료 후 새 요구사항이 생기면:
- 규모 판단: Hotfix 기준 이하 → Hotfix 프로세스 / 이상 → Re-plan
- Re-plan: Orchestrator PHASE 11 진입
  명령어: `.claude/agents/orchestrator.md와 STATUS.md 읽고 PHASE 11 실행해줘`

## 누적 Tech Debt 관리

- `sprints/TECH_DEBT.md` — 모든 스프린트의 기술 부채 중앙 관리
- Validator가 스프린트 종료 시 OUT_OF_SCOPE.md + TODO 주석을 여기에 집계
- Planner는 GOAL.md 작성 전 TECH_DEBT.md를 읽고 처리 가능한 항목 반영
- 처리 완료 시 ✅ 표시 (삭제하지 않고 이력 유지)

## 체크리스트 형식
- 완료: `[x]` 또는 `✅`
- 미완료: `[ ]` 또는 `⬜`

## 문서 구조
- 스프린트 계획: `sprints/{CURRENT_SPRINT}/GOAL.md`
- 스프린트 완료 보고: `sprints/{CURRENT_SPRINT}/DONE.md`
- 범위 외 사항: `sprints/{CURRENT_SPRINT}/OUT_OF_SCOPE.md`
- 누적 기술 부채: `sprints/TECH_DEBT.md`
- 전체 변경 이력: `CHANGELOG.md`
