# /sprint-log — 현재 스프린트 종합 요약

docs/STATUS.md에서 CURRENT_SPRINT을 확인하고, 해당 스프린트의 모든 문서를 읽어서 종합 요약해줘.

## 읽을 파일

- docs/STATUS.md → CURRENT_SPRINT 확인
- sprints/{CURRENT_SPRINT}/GOAL.md → 목표, 체크리스트, 완료 조건
- sprints/{CURRENT_SPRINT}/DONE.md → 완료 보고 (있는 경우)
- sprints/{CURRENT_SPRINT}/OUT_OF_SCOPE.md → 범위 외 사항 (있는 경우)

## 출력 형식

```
┌──────────────────────────────────────┐
│ {CURRENT_SPRINT} 요약               │
│                                      │
│ 목표: {GOAL.md 목표}                │
│ 상태: PHASE {N} — {PHASE 이름}      │
│                                      │
│ 구현 진행률: {완료}/{전체}           │
│  [x] 기능 1                         │
│  [ ] 기능 2                         │
│  ...                                 │
│                                      │
│ 완료 조건: {통과}/{전체}             │
│  [x] 조건 1 (자동)                  │
│  [ ] 조건 2 (수동)                  │
│  ...                                 │
└──────────────────────────────────────┘
```

추가 섹션 (파일이 있는 경우만):
- DONE.md → 완료된 기능, 생성된 파일 수
- OUT_OF_SCOPE.md → 범위 외 발견사항 목록

CURRENT_SPRINT이 `-`이면:
→ "아직 시작된 스프린트가 없습니다. /next를 실행해 다음 단계를 확인하세요."
