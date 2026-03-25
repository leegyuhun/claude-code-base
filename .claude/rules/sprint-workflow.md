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
- `sprint/{CURRENT_SPRINT}` 브랜치 생성
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

1. `main` 기반 `hotfix/{설명}` 브랜치 생성
2. 수정 후 hotfix-close 에이전트 실행
3. main PR 생성 → 머지 후 develop/sprint 브랜치에 역머지

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

## 체크리스트 형식
- 완료: `[x]` 또는 `✅`
- 미완료: `[ ]` 또는 `⬜`

## 문서 구조
- 스프린트 계획: `sprints/{CURRENT_SPRINT}/GOAL.md`
- 스프린트 완료 보고: `sprints/{CURRENT_SPRINT}/DONE.md`
- 범위 외 사항: `sprints/{CURRENT_SPRINT}/OUT_OF_SCOPE.md`
