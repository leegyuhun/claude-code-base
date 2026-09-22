---
name: sprint-dev
description: "GOAL.md에 따라 스프린트를 구현. Implementer/Spec Reviewer/Code Quality Reviewer 3단계 진행."
---

GOAL.md에 따라 스프린트를 구현하는 오케스트레이터.

> 이 커맨드는 `implementer` 에이전트(PHASE 6)의 커맨드 래퍼입니다.
> implementer 에이전트를 직접 호출하는 대신 이 커맨드를 사용하면
> 스프린트명 파싱, 브랜치 준비, 구현 Plan, 최종 검증까지 자동 진행됩니다.

## 워크스페이스 해석 (항상 먼저 수행)

1. `.claude/ACTIVE_ISSUE` 읽기 → ACTIVE_ISSUE 값 획득
2. 없으면 `git branch --show-current` 출력에서 `#(\d+)` 추출 (폴백)
3. 모두 실패 시 → "`⚠️ 활성 이슈를 확인할 수 없습니다. /prd #이슈번호 를 실행하세요.`" 출력 후 종료
4. WORKSPACE_DIR = `workspace/{ACTIVE_ISSUE}`
5. STATUS_FILE = `{WORKSPACE_DIR}/STATUS.md`

## TRACK 변수 정의 (워크스페이스 해석 직후)

STATUS_FILE에서 `TRACK` 값을 읽어 경로 변수를 결정한다:

**TRACK=sprint (또는 미지정):**
- `GOAL_FILE` = `{WORKSPACE_DIR}/sprints/{CURRENT_SPRINT}/GOAL.md`
- `DONE_FILE` = `{WORKSPACE_DIR}/sprints/{CURRENT_SPRINT}/DONE.md`
- `FEEDBACK_FILE` = `{WORKSPACE_DIR}/sprints/{CURRENT_SPRINT}/FEEDBACK.md`
- `OUT_OF_SCOPE_FILE` = `{WORKSPACE_DIR}/sprints/{CURRENT_SPRINT}/OUT_OF_SCOPE.md`

**TRACK=defect:**
- `GOAL_FILE` = `docs/PRD_{ACTIVE_ISSUE}.md` (PRD의 `## 검증 계약` 섹션을 체크리스트로 사용)
- `DONE_FILE` = `{WORKSPACE_DIR}/DONE.md`
- `FEEDBACK_FILE` = `{WORKSPACE_DIR}/FEEDBACK.md`
- `OUT_OF_SCOPE_FILE` = `{WORKSPACE_DIR}/OUT_OF_SCOPE.md`

## 인수

`$ARGUMENTS`: 스프린트 이름 (예: `sprint-01`, `01`)
- `{WORKSPACE_DIR}/sprints/{CURRENT_SPRINT}/GOAL.md` 경로를 결정한다.
- 인수가 없으면 {STATUS_FILE}에서 CURRENT_SPRINT을 읽는다.

## 실행 절차

### 사전 검증: PHASE 확인

1. {STATUS_FILE}에서 PHASE와 TRACK 값을 확인한다.
2. PHASE가 5 또는 6이 아니면:
   - TRACK=defect + PHASE 1~5 → 정상 진행 (PHASE=6으로 자동 승격 처리)
   - TRACK=sprint + PHASE 1~4.5 → "⚠️ 아직 계획 단계입니다 (PHASE={N}). Orchestrator/Planner를 먼저 완료해주세요." 출력 후 종료
   - PHASE 7~10 → "⚠️ 이미 검증 단계입니다 (PHASE={N}). Validator를 실행해주세요." 출력 후 종료
3. PHASE 5 또는 6 (또는 TRACK=defect) → 정상 진행

### 1단계: 스프린트 문서 읽기

필수:
- CLAUDE.md (없으면 경고 후 계속: `"⚠️ CLAUDE.md가 없습니다. .claude/rules/coding-principles.md를 참조합니다."`)
- {STATUS_FILE} ← 현재 PHASE와 CURRENT_SPRINT 확인
- `{GOAL_FILE}` ← 구현 명세 (전체 읽기; TRACK=defect면 PRD의 `## 검증 계약` 섹션을 체크리스트로 사용)

참조 가능 (수정 금지):
- `{WORKSPACE_DIR}/plan.md` ← 전체 설계 맥락 파악용
- `{WORKSPACE_DIR}/sprints/ROADMAP.md` ← 스프린트 간 의존성 확인용
- `{WORKSPACE_DIR}/sprints/TECH_DEBT.md` ← 누적 기술 부채 (이번 스프린트 처리 항목 확인)
- `{WORKSPACE_DIR}/sprints/{PREV_SPRINT}/DONE.md` ← 직전 스프린트 주의사항
- `{WORKSPACE_DIR}/sprints/{PREV_SPRINT}/OUT_OF_SCOPE.md` ← 직전 스프린트 범위 외 사항
- `{FEEDBACK_FILE}` ← Validator 롤백 시 생성된 피드백 (있을 때만)

구현 패턴 레퍼런스 (구현 중 필요 시 Read):
- `.claude/rules/delphi2007-patterns.md` ← 재진입 가드, TDataSet 상태, TThread, GDI 핸들, TtsQuery·SQL 구성, Record 기반 파라미터, INI 프로파일, TJGrid 등 17개 구현 패턴. 4단계에서 해당 패턴이 필요한 기능을 만날 때 해당 섹션만 부분 Read한다.

FEEDBACK.md 재진입 판단:
- `{FEEDBACK_FILE}`이 존재하면 → Validator가 PHASE 7 검증 실패 후 롤백한 상황
  - FEEDBACK.md에 기술된 항목만 타겟 수정 (전체 재구현 금지)
  - 수정 완료 후 5단계(최종 검증)로 직접 이동
- FEEDBACK.md가 없으면 정상 진입. 다음을 파악한다:
  - **구현 기능 체크리스트**: 구현할 기능 목록과 순서
  - **완료 조건**: 자동/수동 검증 항목
  - **예상 산출물**: 생성/수정할 파일 목록
  - **기술 고려사항**: 주의할 기술적 포인트

### 2단계: 브랜치 준비

TRACK=sprint:
1. 현재 브랜치가 `{현재 브랜치명}_{CURRENT_SPRINT}`이 아니면:
   - 현재 브랜치명을 확인(`git branch --show-current`)하여 `{현재 브랜치명}_{CURRENT_SPRINT}` 브랜치 생성
2. 이미 해당 브랜치면 그대로 진행

TRACK=defect:
- 스프린트별 브랜치 분기 없음. 현재 브랜치(`{현재 브랜치명}`)에서 그대로 진행.

### 2.5단계: Redmine 상태 → InProgress

브랜치명에서 `#이슈번호` 패턴을 추출한다.
이슈 번호가 있으면 InProgress(2)까지 순차 전환하고 start_date를 설정한다.

```
워크플로우: New(1) → Confirmed(11) → Assigned(10) → InProgress(2)
목표 상태: InProgress (status_id=2)
start_date: 오늘 날짜 (YYYY-MM-DD)

1. 현재 사용자 ID 조회
   MCP: 없음 → curl -s -H "X-Redmine-API-Key: $REDMINE_API_KEY" $REDMINE_URL/users/current.json
   → user.id 추출하여 {MY_USER_ID} 로 저장

2. 현재 상태 조회
   MCP(폴백): get_issue(issue_id={이슈번호})
   curl(우선): curl -s -H "X-Redmine-API-Key: $REDMINE_API_KEY" $REDMINE_URL/issues/{이슈번호}.json

3. 현재 status_id에서 2까지 순서대로 호출
   - 현재=1:  → 11(Confirmed) → 10(Assigned) → 2(InProgress)
   - 현재=11: → 10(Assigned)  → 2(InProgress)
   - 현재=10: → 2(InProgress)
   - 현재=2:  생략

   ※ status_id=10(Assigned) 전환 시 assigned_to_id 필수:
   MCP(폴백): update_issue(issue_id={이슈번호}, status_id=10, assigned_to_id={MY_USER_ID})
   curl(우선): Body: {"issue": {"status_id": 10, "assigned_to_id": {MY_USER_ID}}}

   그 외 단계는 status_id만:
   MCP(폴백): update_issue(issue_id={이슈번호}, status_id={다음상태})
   curl(우선): Body: {"issue": {"status_id": {다음상태}}}

4. InProgress 전환 시 start_date 함께 설정:
   MCP(폴백): update_issue(issue_id={이슈번호}, status_id=2, start_date="{오늘날짜}")
   curl(우선): Body: {"issue": {"status_id": 2, "start_date": "{오늘날짜}"}}
```

성공: `✅ Redmine #{이슈번호} → 진행 중 (start_date: {오늘날짜})`
실패: 무시하고 계속 진행 (이슈 번호 없으면 이 단계 건너뜀)

### 3단계: 구현 Plan 작성 + AUTO_RUN 판정

Plan을 작성한 뒤, 아래 6개 조건을 **기계적으로** 판정한다.
판정은 재량이 아니다. "명확해 보인다"는 이유로 통과시키지 않는다.
하나라도 판단이 불가능하면 **미충족(☐)으로 처리**한다.

```
[AUTO_RUN 조건 — 전부 ☑ 이어야 자동 진행]
  1. 수정 예상 파일 ≤ 3개
  2. 신규 .pas / .dfm 생성 없음 (= .dproj 변경 없음)
  3. 공용 유닛 미수정
     — Common/, CommonBL/, CommonV7/, ComUnit/, PackageBL/ 경로 일체
       (참조 프로젝트가 다수이므로 파급 범위 확인이 필수)
  4. DB 스키마 변경 없음 (테이블/컬럼 추가·변경·삭제 DDL 없음)
  5. Plan의 '예상 이슈' 0건
  6. FEEDBACK.md 재진입이 아님
     (재진입 = 이미 사람이 한 번 반려한 상태이므로 항상 확인)
```

**AUTO_RUN = 전부 충족:** Plan 박스를 출력하고 [PAUSE] 없이 4단계로 바로 진행한다.

```
┌─────────────────────────────────────┐
│ 📋 구현 Plan — {CURRENT_SPRINT}    │
│                                     │
│ 구현 순서:                          │
│  1. {기능명} — {접근 방식}          │
│  2. {기능명} — {접근 방식}          │
│                                     │
│ 예상 이슈: 없음                     │
│                                     │
│ [AUTO_RUN 판정]                     │
│  ☑ 수정 파일 3개 이하 ({N}개)       │
│  ☑ 신규 .pas/.dfm 없음              │
│  ☑ 공용 유닛 미수정                 │
│  ☑ DB 스키마 변경 없음              │
│  ☑ Plan 예상 이슈 0건               │
│  ☑ FEEDBACK 재진입 아님             │
│                                     │
│ → 자동 진행합니다 (중단: Esc)       │
└─────────────────────────────────────┘
```

**하나라도 미충족:** 기존대로 Plan 출력 후 [PAUSE] — '실행' 입력을 기다린다.
미충족 항목에 ☐를 표시하고 사유를 한 줄로 명시한다.

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
│ [AUTO_RUN 판정]                     │
│  ☐ {미충족 항목} — {사유}           │
│                                     │
│ '실행' 입력 시 구현 시작합니다      │
└─────────────────────────────────────┘
```

### 4단계: 기능별 Subagent 디스패치

> 참조: `.claude/skills/subagent-driven-development/SKILL.md`

3단계에서 AUTO_RUN이면 즉시, 아니면 '실행' 입력 후
GOAL.md 체크리스트 항목 수를 파악하고, 각 항목에 대해 아래 3-STEP 루프를 **순차** 실행한다.

**STEP 1 — Implementer Subagent 디스패치**

`.claude/skills/subagent-driven-development/implementer-prompt.md`를 읽어 프롬프트를 구성한 뒤
Agent tool (subagent_type=implementer)로 디스패치:
- 항목 전체 텍스트 (GOAL.md 해당 항목 원문)
- 맥락: CURRENT_SPRINT, WORKSPACE_DIR, 직전 완료 항목
- YSR 필수 규칙 포함 (CP949, TtsQuery, GOAL.md 범위 엄수, 컴파일 확인 의무)
- `{함정 카테고리}` 치환: 이 항목의 작업 영역으로 카테고리를 식별해 넘긴다
  (기본 A·B / SQL이면 C / DFM·UI면 D / 빌드·패키지면 E / git·셸이면 F —
   `.claude/rules/pitfalls-index.md`의 "빠른 매핑" 표 기준)

subagent 보고에서 **함정 후보**를 항목별로 수집해 둔다 (0건 보고도 그대로 기록).
수집분은 5.5단계에서 한 번에 취합해 사용자에게 제안한다.

상태별 처리:
- DONE: STEP 2로
- DONE_WITH_CONCERNS: 우려사항 검토 → 정확성/범위 문제이면 처리, STEP 2로
- NEEDS_CONTEXT: 추가 컨텍스트 제공 후 재디스패치
- BLOCKED: [PAUSE] 후 사용자에게 보고 (컨텍스트/분해/아키텍처 문제 판단)

**STEP 2 — Spec Reviewer Subagent 디스패치 (Implementer 완료 후)**

`.claude/skills/subagent-driven-development/spec-reviewer-prompt.md`를 읽어
Agent tool (general-purpose)로 디스패치:
- GOAL.md 해당 항목 명세 전체 + Implementer 보고 내용 전달
- ❌ 이슈 발견 → 재리뷰 **전에** 카운터를 올린다 (이 왕복에는 원래 상한이 없었다):

      python .claude/scripts/loop_state.py bump --scope review:{항목번호} \
        --signature "spec:{이슈 요지}" --note "{반려 사유 한 줄}"

  ACTION=continue → Implementer에 수정 지시 후 재리뷰
  ACTION=halt     → 같은 지적이 반복되는 상태다. [PAUSE] 후 사용자에게 보고
- ✅ 통과 후에만 STEP 3 진행 (품질 리뷰 먼저 시작 금지)

**STEP 3 — Code Quality Reviewer Subagent 디스패치 (Spec 통과 후에만)**

`.claude/skills/subagent-driven-development/code-quality-reviewer-prompt.md`를 읽어
Agent tool (general-purpose)로 디스패치:
- dev-process.md §6 + CLAUDE.md 코딩 규칙 기준
- ❌ 이슈 발견 → 재리뷰 **전에** 카운터를 올린다:

      python .claude/scripts/loop_state.py bump --scope review:{항목번호} \
        --signature "quality:{이슈 요지}" --note "{반려 사유 한 줄}"

  ACTION=continue → Implementer에 수정 지시 후 재리뷰
  ACTION=halt     → [PAUSE] 후 사용자에게 보고
- ✅ 통과 → 항목 완료. 다음 항목으로. 카운터를 되돌린다:

      python .claude/scripts/loop_state.py reset --scope review:{항목번호}

**공통 규칙:**
- GOAL.md(또는 PRD 검증 계약) 범위 밖 발견 시 → `{OUT_OF_SCOPE_FILE}`에 기록하고 건너뜀
- .pas 파일 수정 시 .dfm 동기화 (Implementer prompt에 명시)
- Implementer subagent 병렬 디스패치 금지 (코드 충돌 위험, 직렬 순차 실행)
- Implementer에서 오류 시 `.claude/skills/systematic-debugging/SKILL.md` Phase 1부터 시작.
  재시도 전 `loop_state.py bump --scope review:{항목번호}` 로 카운터를 올리고,
  ACTION=halt 이면 BLOCKED 처리 후 사용자 보고 (횟수를 직접 세지 않는다)
- 계획과 다른 결정 필요 시 → [PAUSE] 후 사용자에게 확인

요구사항 변경 발생 시:
- [PAUSE]
  "요구사항 변경이 감지되었습니다.
   변경 내용: {내용}
   영향받는 항목: {목록}
   GOAL.md를 수정하고 계속할까요? (예/아니오)"
- '예' → GOAL.md 수정 후 계속
- '아니오' → 현재까지 완료된 항목만으로 5단계 진행

### 5단계: 최종 검증

모든 기능 완료 후:

1. GOAL.md의 **완료 조건** 섹션 체크
2. 최종 빌드 재실행 — 이번 스프린트에서 변경된 .dproj 대상 `build.bat debug` 실행 및 결과(에러 0건) 출력
   (각 기능 완료 시 컴파일 확인했더라도 최종 통합 빌드를 다시 실행해야 함)

### 5.5단계: 함정 회고 캡처 (건너뛸 수 없음)

4단계에서 수집한 함정 후보를 취합해 사용자에게 기록 여부를 묻는다.
**후보가 0건이어도 이 단계를 생략하지 않는다.** 침묵으로 넘어가면 회고가 사라진다.

**후보 0건 — 아래 한 줄만 출력하고 6단계로:**

```
[함정 회고] 새 함정 후보 없음 — pitfalls.md 변경 없이 종료.
```

**후보 1건 이상 — 제안 후 [PAUSE]:**

```
[함정 회고 캡처 제안] {CURRENT_SPRINT}

1) [증상]     {무엇이 잘못 보였는지}
   [원인]     {왜 그렇게 됐는지}
   [해결]     {어떻게 고쳤는지}
   [다음 체크] {재발 방지용 한 줄}
   [카테고리]  {A~F 중 판정}

2) ...

→ 기록 여부:
   (y) 모두 기록  /  (n) 모두 폐기  /  (e) 편집 후 기록  /  항목 번호(예: 1,3) 선택
```

**응답 처리:**

| 입력 | 처리 |
|------|------|
| `y` | 모든 후보를 append (아래 기록 형식) |
| `n` | 폐기 후 6단계로. 파일 변경 없음 |
| `e` | 사용자 수정본을 그대로 append |
| `1,3` 등 숫자 | 지정 항목만 append |

**기록 형식 — 두 파일을 모두 갱신해야 완료:**

1. `.claude/refs/pitfalls.md` — 판정한 카테고리 섹션에 4단 구조로 추가.
   번호는 **현재 본문의 최대 함정 번호 + 1** (카테고리별이 아니라 전체 통합 번호)

   ```markdown
   ### #{N} {증상 한 줄 요약}

   **증상**: {사용자 관점에서 무엇이 잘못 보였는지}

   **원인**: {왜 그렇게 됐는지}

   **해결**: {어떻게 고쳤는지}

   **다음 체크**: {재발 방지용 한 줄}

   ---
   ```

   말미 `---` 구분선까지 기존 항목과 동일하게 맞춘다.
   해당 카테고리 섹션(`## E. 빌드 / 패키지 ...` 등)이 본문에 아직 없으면 섹션부터 새로 만든다.

2. `.claude/rules/pitfalls-index.md` — 해당 카테고리에 `- **#{N}** {한 줄 요약}` 추가.
   인덱스에 "(아직 없음)"으로 표시된 카테고리라면 그 줄을 새 항목으로 교체한다.
   필요하면 "빠른 매핑" 표도 갱신한다.

> 인덱스 갱신을 빠뜨리면 다음 작업에서 그 함정은 없는 것과 같다. 본문만 쓰고 끝내지 않는다.

**처리 결과는 6단계 요약에 한 줄로 남긴다** (`append 2건` / `사용자 폐기(n)` / `후보 없음`).

### 6단계: 완료 보고 및 Validator 인계

1. 결과 요약:
   ```
   🏁 {CURRENT_SPRINT} 구현 완료

   | 검증 항목 | 결과 |
   |-----------|------|
   | 빌드 | ✅ 성공 |
   | 테스트 | ✅ N passed |
   | 함정 회고 | {append N건 / 사용자 폐기(n) / 후보 없음} |
   | ... | ... |

   다음 단계: Validator 에이전트 실행
   명령어(TRACK=sprint): '.claude/agents/validator.md를 읽고
            {WORKSPACE_DIR}/sprints/{CURRENT_SPRINT} 검증해줘'
   명령어(TRACK=defect): '.claude/agents/validator.md를 읽고
            TRACK=defect 모드로 검증을 시작해줘. [PAUSE] 지점에서 멈추고 내 확인을 기다려.'
   ```

2. {STATUS_FILE} PHASE=7 업데이트

## 주의사항

- **GOAL.md가 Single Source of Truth**: 문서에 명시되지 않은 작업은 하지 않는다.
- **계획과 다른 결정이 필요하면 사용자에게 확인**한다.
- **CLAUDE.md의 코딩 원칙 준수**
- **구현 패턴은 `.claude/rules/delphi2007-patterns.md`를 먼저 확인**한다. 동일 패턴이 이미 문서화돼 있으면 직접 재발명하지 말고 해당 섹션을 인용·적용한다.

## 금지 사항

- ❌ GOAL.md 범위 밖 기능 구현
- ❌ GOAL.md 체크박스 수정 (Validator가 독립 검증 후 체크 — 자기 평가 금지)
- ❌ {WORKSPACE_DIR}/plan.md, ROADMAP.md 수정 (참조는 가능)
- ❌ git push (Validator 완료 후 처리)
- ❌ 아키텍처 변경 (Orchestrator 결정 사항)
- ❌ 기능 검증·통합 테스트 (Validator 담당) — 단, 컴파일 확인(build.bat)은 implementer 의무이며 예외
- ❌ 추측성 기능, 불필요한 추상화, 주변 코드 "개선"
