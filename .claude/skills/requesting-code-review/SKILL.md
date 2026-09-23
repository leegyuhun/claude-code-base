---
name: requesting-code-review
description: 구현 완료 후 또는 main 병합 전에 코드 리뷰 Subagent를 디스패치하여 문제가 커지기 전에 잡아낸다.
---

# Requesting Code Review

구현 완료 후 독립된 Code Reviewer subagent를 디스패치한다.
Reviewer는 현재 세션 히스토리가 아닌 **정확히 제작된 컨텍스트**만 받는다.
이를 통해 리뷰어는 구현 과정이 아닌 결과물에 집중하고, 메인 세션의 컨텍스트는 보존된다.

**핵심 원칙:** 문제는 일찍, 자주 잡아라.

---

## 언제 요청하는가

**필수:**
- Validator PHASE 7-4 — 스프린트 전체 구현 완료 후
- main 병합 전
- subagent-driven-development의 각 항목 완료 후 (3위 스킬과 통합)

**선택 (가치 있음):**
- 막혔을 때 (새로운 시각)
- 복잡한 버그 수정 후
- 공유 모듈(CLAUDE.md 목록) 수정 포함 시

---

## 요청 방법

**1. Git SHA 확보:**
```bash
# 스프린트 브랜치 분기점
BASE_SHA=$(git merge-base HEAD main)
HEAD_SHA=$(git rev-parse HEAD)
```

**2. code-reviewer subagent 디스패치:**

`Agent tool` 사용, `general-purpose` 타입, 템플릿은 `code-reviewer.md` 참조

**플레이스홀더:**
- `{DESCRIPTION}` — 구현 내용 요약 (GOAL.md 제목 활용)
- `{PLAN_OR_REQUIREMENTS}` — GOAL.md 전체 또는 검증 계약 섹션
- `{BASE_SHA}` — 분기 시작 커밋
- `{HEAD_SHA}` — 현재 커밋

**3. 결과 처리:**
- Critical 즉시 수정 → 재검증
- High 수정 권장 → 진행 전 처리
- Medium 기록 → 다음 스프린트 반영
- 리뷰어가 틀렸다면 근거로 반박 (비위 맞추기 금지)

---

## 특이사항

### 인코딩 손상 주의
git diff에서 비ASCII 문자가 깨진 패턴(`\xef\xbf\xbd`, `???`)이나 의도치 않은 파일 전체 재인코딩이 보이면 즉시 Critical 보고.

### 공유 모듈 변경 주의
CLAUDE.md에 명시된 공유 모듈 변경은 **전체 영향 범위**를 반드시 보고.
GOAL.md에 명시되지 않은 공유 모듈 변경은 High 이상으로 보고.

### DBMS 호환 확인
프로젝트가 여러 DBMS를 지원하면(CLAUDE.md), 새 SQL이 모든 대상에서 동작하는지 또는 프로젝트 표준 분기 방식을 따르는지 확인.

---

## 워크플로우 통합

**Validator PHASE 7-4:**
- 스프린트 전체 git diff 리뷰
- 결과를 7-5 자동 검증 항목에 반영

**subagent-driven-development와 함께:**
- 각 GOAL.md 항목의 Code Quality Reviewer (3위)와 별개
- 스프린트 전체 관점의 통합 리뷰

---

## 금지사항

**절대 금지:**
- "간단하니까" 리뷰 생략
- Critical 무시하고 진행
- High 미수정 상태로 main 병합
- 유효한 기술 피드백에 반박 없이 수용

**리뷰어가 틀렸을 때:**
- 기술적 근거로 반박
- 동작을 증명하는 코드/테스트 제시
- 명확화 요청

템플릿: `requesting-code-review/code-reviewer.md`
