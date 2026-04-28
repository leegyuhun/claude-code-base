GOAL.md에 따라 스프린트를 구현하는 오케스트레이터.

> 이 커맨드는 `implementer` 에이전트(PHASE 6)의 커맨드 래퍼입니다.
> implementer 에이전트를 직접 호출하는 대신 이 커맨드를 사용하면
> 스프린트명 파싱, 브랜치 준비, 구현 Plan, 최종 검증까지 자동 진행됩니다.

## 인수

`$ARGUMENTS`: 스프린트 이름 (예: `sprint-01`, `01`)
- `sprints/{CURRENT_SPRINT}/GOAL.md` 경로를 결정한다.
- 인수가 없으면 docs/STATUS.md에서 CURRENT_SPRINT을 읽는다.

## 실행 절차

### 사전 검증: PHASE 확인

1. docs/STATUS.md에서 PHASE 값을 확인한다.
2. PHASE가 5 또는 6이 아니면:
   - PHASE 1~4.5 → "⚠️ 아직 계획 단계입니다 (PHASE={N}). Orchestrator/Planner를 먼저 완료해주세요." 출력 후 종료
   - PHASE 7~10 → "⚠️ 이미 검증 단계입니다 (PHASE={N}). Validator를 실행해주세요." 출력 후 종료
3. PHASE 5 또는 6 → 정상 진행

### 1단계: 스프린트 문서 읽기

필수:
- CLAUDE.md (없으면 경고 후 계속: `"⚠️ CLAUDE.md가 없습니다. .claude/rules/coding-principles.md를 참조합니다."`)
- docs/STATUS.md ← 현재 PHASE와 CURRENT_SPRINT 확인
- `sprints/{CURRENT_SPRINT}/GOAL.md` ← 구현 명세 (전체 읽기)

참조 가능 (수정 금지):
- `plan.md` ← 전체 설계 맥락 파악용
- `sprints/ROADMAP.md` ← 스프린트 간 의존성 확인용
- `sprints/TECH_DEBT.md` ← 누적 기술 부채 (이번 스프린트 처리 항목 확인)
- `sprints/{PREV_SPRINT}/DONE.md` ← 직전 스프린트 주의사항
- `sprints/{PREV_SPRINT}/OUT_OF_SCOPE.md` ← 직전 스프린트 범위 외 사항
- `sprints/{CURRENT_SPRINT}/FEEDBACK.md` ← Validator 롤백 시 생성된 피드백 (있을 때만)

구현 패턴 레퍼런스 (구현 중 필요 시 Read):
- `.claude/rules/delphi2007-patterns.md` ← 재진입 가드, TDataSet 상태, TThread, GDI 핸들, TtsQuery·SQL 구성, Record 기반 파라미터, INI 프로파일, TJGrid 등 17개 구현 패턴. 4단계에서 해당 패턴이 필요한 기능을 만날 때 해당 섹션만 부분 Read한다.

FEEDBACK.md 재진입 판단:
- FEEDBACK.md가 존재하면 → Validator가 PHASE 7 검증 실패 후 롤백한 상황
  - FEEDBACK.md에 기술된 항목만 타겟 수정 (전체 재구현 금지)
  - 수정 완료 후 5단계(최종 검증)로 직접 이동
- FEEDBACK.md가 없으면 정상 진입. 다음을 파악한다:
  - **구현 기능 체크리스트**: 구현할 기능 목록과 순서
  - **완료 조건**: 자동/수동 검증 항목
  - **예상 산출물**: 생성/수정할 파일 목록
  - **기술 고려사항**: 주의할 기술적 포인트

### 2단계: 브랜치 준비

1. 현재 브랜치가 `{현재 브랜치명}_{CURRENT_SPRINT}`이 아니면:
   - 현재 브랜치명을 확인(`git branch --show-current`)하여 `{현재 브랜치명}_{CURRENT_SPRINT}` 브랜치 생성
2. 이미 해당 브랜치면 그대로 진행

### 2.5단계: Redmine 상태 → InProgress

브랜치명에서 `#이슈번호` 패턴을 추출한다.
이슈 번호가 있으면 InProgress(2)까지 순차 전환하고 start_date를 설정한다.

```
워크플로우: New(1) → Confirmed(11) → Assigned(10) → InProgress(2)
목표 상태: InProgress (status_id=2)
start_date: 오늘 날짜 (YYYY-MM-DD)

1. 현재 사용자 ID 조회
   MCP: 없음 → WebFetch GET https://redmine.ubware.com/users/current.json
   → user.id 추출하여 {MY_USER_ID} 로 저장

2. 현재 상태 조회
   MCP: get_issue(issue_id={이슈번호})
   폴백: GET https://redmine.ubware.com/issues/{이슈번호}.json

3. 현재 status_id에서 2까지 순서대로 호출
   - 현재=1:  → 11(Confirmed) → 10(Assigned) → 2(InProgress)
   - 현재=11: → 10(Assigned)  → 2(InProgress)
   - 현재=10: → 2(InProgress)
   - 현재=2:  생략

   ※ status_id=10(Assigned) 전환 시 assigned_to_id 필수:
   MCP: update_issue(issue_id={이슈번호}, status_id=10, assigned_to_id={MY_USER_ID})
   폴백: Body: {"issue": {"status_id": 10, "assigned_to_id": {MY_USER_ID}}}

   그 외 단계는 status_id만:
   MCP: update_issue(issue_id={이슈번호}, status_id={다음상태})
   폴백: Body: {"issue": {"status_id": {다음상태}}}

4. InProgress 전환 시 start_date 함께 설정:
   MCP: update_issue(issue_id={이슈번호}, status_id=2, start_date="{오늘날짜}")
   폴백: Body: {"issue": {"status_id": 2, "start_date": "{오늘날짜}"}}
```

성공: `✅ Redmine #{이슈번호} → 진행 중 (start_date: {오늘날짜})`
실패: 무시하고 계속 진행 (이슈 번호 없으면 이 단계 건너뜀)

### 3단계: 구현 Plan 작성 후 [PAUSE]

아래 형식으로 출력:

```
┌─────────────────────────────────────┐
│ 📋 구현 Plan — {CURRENT_SPRINT}    │
│                                     │
│ 구현 순서:                          │
│  1. {기능명} — {접근 방식}          │
│  2. {기능명} — {접근 방식}          │
│                                     │
│ 예상 이슈:                          │
│  - {이슈 1}                         │
│                                     │
│ '실행' 입력 시 구현 시작합니다      │
└─────────────────────────────────────┘
```

### 4단계: 기능 순차 구현

'실행' 입력 후 GOAL.md 체크리스트 순서대로:

**매 기능마다 아래 체크리스트를 반드시 수행한다:**

```
기능 실행 체크리스트 (건너뛰기 금지):
1. ⬜ 기능 시작 알림 — "🔨 기능 {N}: {기능명} 시작"
2. ⬜ 구현 — GOAL.md 명세대로
3. ⬜ 검증 — 명시된 검증 방법 실행
4. ⬜ 완료 선언 — "✅ {기능명} 구현 완료" 텍스트 출력 (GOAL.md 체크박스 수정 금지 — Validator가 독립 검증 후 체크)
5. ⬜ (커밋 없음 — push 시점에 Validator가 최종 커밋)
```

규칙:
- GOAL.md 범위 밖 기능 발견 시 → `sprints/{CURRENT_SPRINT}/OUT_OF_SCOPE.md`에 기록하고 건너뜀
- .pas 파일 수정 시 해당 .dfm 파일과 싱크 유지
- 검증 실패 시 → 원인 분석 후 수정, 3회 실패 시 사용자에게 보고
- 계획과 다른 결정이 필요하면 사용자에게 확인

요구사항 변경 발생 시:
- 사용자가 구현 중 요구사항 변경을 요청하면 → [PAUSE]
  "요구사항 변경이 감지되었습니다.
   변경 내용: {내용}
   영향받는 항목: {목록}
   GOAL.md를 수정하고 계속할까요? (예/아니오)"
- '예' → GOAL.md 수정 후 계속 구현
- '아니오' → 현재까지 구현된 내용만으로 5단계 진행

### 5단계: 최종 검증

모든 기능 완료 후:

1. GOAL.md의 **완료 조건** 섹션 체크
2. 빌드 성공 확인
3. 결과 요약:
   ```
   🏁 {CURRENT_SPRINT} 구현 완료

   | 검증 항목 | 결과 |
   |-----------|------|
   | 빌드 | ✅ 성공 |
   | 테스트 | ✅ N passed |
   | ... | ... |

   다음 단계: Validator 에이전트 실행
   명령어: '.claude/agents/validator.md와 docs/STATUS.md 읽고
            sprints/{CURRENT_SPRINT} 검증해줘'
   ```

4. docs/STATUS.md PHASE=7 업데이트

## 주의사항

- **GOAL.md가 Single Source of Truth**: 문서에 명시되지 않은 작업은 하지 않는다.
- **계획과 다른 결정이 필요하면 사용자에게 확인**한다.
- **CLAUDE.md의 코딩 원칙 준수**
- **구현 패턴은 `.claude/rules/delphi2007-patterns.md`를 먼저 확인**한다. 동일 패턴이 이미 문서화돼 있으면 직접 재발명하지 말고 해당 섹션을 인용·적용한다.

## 금지 사항

- ❌ GOAL.md 범위 밖 기능 구현
- ❌ GOAL.md 체크박스 수정 (Validator가 독립 검증 후 체크 — 자기 평가 금지)
- ❌ plan.md, ROADMAP.md 수정 (참조는 가능)
- ❌ git push (Validator 완료 후 처리)
- ❌ 아키텍처 변경 (Orchestrator 결정 사항)
- ❌ 검증 / 테스트 실행 (Validator 담당)
- ❌ 추측성 기능, 불필요한 추상화, 주변 코드 "개선"
