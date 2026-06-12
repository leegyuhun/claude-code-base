# /sprint-log — 현재 스프린트 종합 요약

## 워크스페이스 해석

1. `.claude/ACTIVE_ISSUE` 읽기 → ACTIVE_ISSUE 값 획득
2. 없으면 `git branch --show-current` 출력에서 `#(\d+)` 추출 (폴백)
3. 모두 실패 시 → "`⚠️ 활성 이슈를 확인할 수 없습니다.`" 출력 후 종료

WORKSPACE_DIR = `workspace/{ACTIVE_ISSUE}`
STATUS_FILE = `{WORKSPACE_DIR}/STATUS.md`

STATUS_FILE에서 `TRACK` 값을 읽어 출력 형식을 결정한다.

## TRACK=sprint (또는 미지정)

### 읽을 파일

- {STATUS_FILE} → CURRENT_SPRINT 확인
- {WORKSPACE_DIR}/sprints/{CURRENT_SPRINT}/GOAL.md → 목표, 체크리스트, 완료 조건
- {WORKSPACE_DIR}/sprints/{CURRENT_SPRINT}/DONE.md → 완료 보고 (있는 경우)
- {WORKSPACE_DIR}/sprints/{CURRENT_SPRINT}/OUT_OF_SCOPE.md → 범위 외 사항 (있는 경우)

### 출력 형식

```
┌──────────────────────────────────────┐
│ {CURRENT_SPRINT} 요약               │
│                                      │
│ 이슈:  {ACTIVE_ISSUE}               │
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

---

## TRACK=defect

### 읽을 파일

- {STATUS_FILE} → PHASE 확인
- `docs/PRD_{ACTIVE_ISSUE}.md` → 목적 요약, `## 검증 계약` 체크리스트
- `{WORKSPACE_DIR}/DONE.md` → 완료 보고 (있는 경우)

### 출력 형식

```
┌──────────────────────────────────────┐
│ Defect 진행 요약 — {ACTIVE_ISSUE}   │
│                                      │
│ 목적: {PRD ## 목적 & 배경 첫 줄}    │
│ 상태: PHASE {N} — {PHASE 이름}      │
│       (PHASE=10이면: ✅ 완료)        │
│                                      │
│ 검증 계약 진행률: {완료}/{전체}      │
│  [x] 항목 1 (자동/수동)             │
│  [ ] 항목 2 (자동/수동)             │
│  ...                                 │
└──────────────────────────────────────┘
```

추가 섹션 (파일이 있는 경우만):
- `{WORKSPACE_DIR}/DONE.md` → 완료된 수정 내용, 관련 파일 수
