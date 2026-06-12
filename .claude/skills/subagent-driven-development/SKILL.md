---
name: subagent-driven-development
description: GOAL.md 체크리스트 항목 구현 시 사용. 항목별 fresh subagent 디스패치 + 2단계 리뷰(Spec 적합성 → 코드 품질). 단일 세션 순회보다 품질이 높고 컨텍스트 오염이 없다.
---

# Subagent-Driven Development

GOAL.md 항목별 fresh subagent를 디스패치하고, 각 항목 완료 후 Spec 리뷰 → 코드 품질 리뷰 2단계 게이트를 통과한다.

**왜 Subagent인가:** 각 구현 subagent는 대화 히스토리 없이 정확히 필요한 컨텍스트만 받는다. 이로써 컨텍스트 오염이 없고, 스프린트 후반 항목도 초반과 동일한 품질로 구현된다.

**핵심 원칙:** 항목당 fresh subagent + 2단계 리뷰(Spec → 품질) = 높은 품질, 빠른 피드백

## 언제 사용하는가

GOAL.md 체크리스트를 실행할 때 기본적으로 사용.
단, 다음 경우에는 단일 세션 진행도 허용:
- GOAL.md 항목이 단 1개이고 파일 변경 범위가 명확히 1~2개인 경우
- TRACK=defect에서 매우 단순한 1-liner 수정인 경우

## 절차

```
GOAL.md 읽기 → 항목 목록 추출 및 TaskCreate →
  각 항목에 대해:
    1. Implementer subagent 디스패치 (implementer-prompt.md 기반)
    2. Spec Reviewer subagent 디스패치 (spec 통과까지)
    3. Code Quality Reviewer subagent 디스패치 (품질 통과까지)
    4. TaskUpdate 완료
→ 모든 항목 완료 → 5단계(최종 검증)로
```

## 모델 선택

- 단순 구현 (파일 1~2개, 명확한 명세): claude-haiku 또는 claude-sonnet
- 복합 구현 (다중 파일, 통합 고려): claude-sonnet
- 아키텍처 판단, 리뷰: claude-opus

## Implementer 상태 처리

**DONE:** Spec Reviewer로 진행.

**DONE_WITH_CONCERNS:** 우려사항 내용 검토. 정확성/범위 문제이면 먼저 처리. 단순 관찰(파일이 크다 등)이면 기록 후 Spec Reviewer로 진행.

**NEEDS_CONTEXT:** 추가 컨텍스트 제공 후 재디스패치.

**BLOCKED:**
1. 컨텍스트 부족 → 더 많은 정보 제공 후 재디스패치
2. 더 복잡한 추론 필요 → 더 강력한 모델로 재디스패치
3. 태스크가 너무 큼 → 더 작은 단위로 분해
4. 계획 자체가 잘못됨 → [PAUSE] 후 사용자에게 보고

## 프롬프트 템플릿

- `./implementer-prompt.md` — Implementer subagent 디스패치용
- `./spec-reviewer-prompt.md` — Spec 적합성 리뷰어 subagent 디스패치용
- `./code-quality-reviewer-prompt.md` — 코드 품질 리뷰어 subagent 디스패치용

## 금지 사항

- Implementer subagent를 병렬로 동시 디스패치 (코드 충돌 위험)
- Spec 리뷰 통과 전 Code Quality 리뷰 진행
- 리뷰어가 이슈를 발견했는데 다음 항목으로 이동
- Implementer report만 믿고 코드 실제 확인 생략 (Spec Reviewer 의무)
- 코드 품질 리뷰를 건너뛰고 완료 처리
