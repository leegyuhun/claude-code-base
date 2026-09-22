---
name: prd
description: "PRD.md 생성. 구조화된 인터뷰 → GAP 분석 → 문서 생성 3단계."
---

# /prd — PRD.md 생성

> orchestrator(PHASE 1)가 검증 없이 바로 통과할 수 있는 완성도 높은 PRD.md를 목표로 한다.
> 구조화된 인터뷰 → GAP 분석 → 문서 생성 3단계로 진행한다.

## 인수 처리 (`$ARGUMENTS`)

`$ARGUMENTS`에서 아래 세 가지를 독립적으로 추출한다. 순서와 구분자(공백·쉼표·혼합)는 무관하다.

```
추출 규칙:

  PROJECT_PATH  절대경로 토큰 (/ 또는 C:\... 포함)
                없으면 현재 작업 디렉토리
                PROJECT_NAME은 경로의 마지막 디렉토리명으로 자동 설정

  PROJECT_NAME  #이슈번호·절대경로가 아닌 첫 번째 의미 있는 토큰
                예: "FwChart", "환자예약모듈"
                없으면 PROJECT_PATH의 마지막 디렉토리명, 둘 다 없으면 "전체"

  ISSUE_NUMBERS #숫자 패턴 (여러 개 가능)
                예: #1234, #207500
                있으면 Phase 1에서 redmine 스킬로 자동 조회

  EXTRA_CONTEXT 위 세 가지 이외의 나머지 텍스트 (자유 설명)
                예: "원인파악해줘", "로그인 관련", "긴급"
                Phase 1 인터뷰의 초기 컨텍스트로 활용

예시:
  /prd FwChart, #1234, 원인파악해줘
    → PROJECT_NAME=FwChart  ISSUE_NUMBERS=[#1234]  EXTRA_CONTEXT="원인파악해줘"

  /prd E:/Source/ysr #207500
    → PROJECT_PATH=E:/Source/ysr  PROJECT_NAME=ysr  ISSUE_NUMBERS=[#207500]

  /prd
    → PROJECT_NAME="전체"  PROJECT_PATH=현재 디렉토리

출력 경로: {PROJECT_PATH}/docs/{PRD_FILENAME}
```

---

## Phase 사전 검증

```
.claude/ACTIVE_ISSUE가 존재하면 현재 ACTIVE_ISSUE 값을 확인한다.
workspace/{ACTIVE_ISSUE}/STATUS.md가 존재하면 PHASE 값을 확인한다.

[동일 이슈 재진입 판정 — 확인 생략]
아래 중 하나라도 참이면 이슈 전환이 아니므로 [PAUSE] 없이 계속 진행한다.
  - ACTIVE_ISSUE == 입력된 ISSUE_NUMBERS[0]
  - `git branch --show-current` 출력에 입력된 #이슈번호가 포함됨
    (예: 현재 브랜치 `main_delphi_#213378`, 입력 `/prd #213378`)
→ 아래 한 줄만 출력하고 Phase 0으로 진행:
  "ℹ️ 동일 이슈 재진입 (#{이슈번호}, PHASE={N}) — 확인 생략하고 계속합니다."

[이슈 전환 판정 — 확인 필요]
위 조건에 해당하지 않고 PHASE가 5~10 (다른 이슈의 스프린트 진행 중)이면:
  ⚠️ "현재 이슈({ACTIVE_ISSUE})의 스프린트가 진행 중입니다 (PHASE={N}).
   /prd 실행 시 새 이슈({입력된 이슈})로 전환됩니다. 기존 이슈 작업은 그대로 보존됩니다.
   계속하시겠습니까? (예/아니오)"
  → '아니오' → 종료
  → '예' → 새 이슈로 계속 진행
```

## Phase 0: 시작 안내

**파일명 결정 (인터뷰 전 먼저 확정):**

```
ISSUE_NUMBERS가 있으면:
  이슈 1개  → PRD_#1234.md
  이슈 여러 개 → PRD_#1234_#5678.md

ISSUE_NUMBERS가 없으면:
  Phase 1 인터뷰의 "핵심 문제" 응답을 받은 뒤
  요구사항 내용에서 핵심 키워드 2~3개로 네이밍:
  예: "환자 예약 현황 조회" → PRD_환자예약현황.md
      "FwChart 로그인 오류" → PRD_FwChart_로그인.md
      PROJECT_NAME만 있고 내용 없음 → PRD_{PROJECT_NAME}.md
```

파싱 결과와 예상 파일명을 출력한다:

```
┌─────────────────────────────────────┐
│ PRD 생성 시작                       │
│                                     │
│ 프로젝트: {PROJECT_NAME}            │
│ 저장 경로: {PROJECT_PATH}/docs/     │
│ 파일명: {PRD_FILENAME}              │
│         (이슈 없으면 인터뷰 후 확정) │
│                                     │
│ 구조화된 인터뷰를 시작합니다.       │
│ 대략적인 아이디어도 괜찮습니다.     │
└─────────────────────────────────────┘
```

- `docs/` 디렉토리가 없으면 생성한다 (mkdir -p).
- ISSUE_NUMBERS가 있으면: `.claude/ACTIVE_ISSUE` 파일에 `#{이슈번호}` 기록, `workspace/#{이슈번호}/` 디렉토리 없으면 생성.
- ISSUE_NUMBERS가 없으면: [PAUSE] 출력 후 임시 ID 한 줄 입력 받기.
  - 안내 메시지:
    ```
    이슈번호 없이 진행합니다. 임시 작업 ID를 입력하세요.
    - 형식: 영문 소문자/숫자/언더스코어 (3~31자, 첫 글자는 영문)
    - 예: exp_login_test, bug_repro_001, learn_async
    ```
  - 입력 검증: `^[a-z][a-z0-9_]{2,30}$` 패턴 매칭. 실패 시 재입력 요청.
  - 검증 통과 시: `.claude/ACTIVE_ISSUE`에 임시 ID 기록 (`#` 접두사 없이), `workspace/{임시ID}/` 디렉토리 없으면 생성.
- 동일 파일명이 이미 있으면 [PAUSE]: "기존 {PRD_FILENAME}이 있습니다. 덮어쓸까요? (예/아니오/수정)"
  - '수정' → 기존 파일을 읽어 Phase 1 인터뷰 응답의 초기값으로 사용

---

## Phase 0.5: 작업 정책 확인 (프로젝트당 최초 1회)

이후 단계의 [PAUSE] 중 "산출물을 보지 않아도 판단할 수 있는 것"을 여기서 한 번에 받는다.
한 번 저장하면 다음 이슈부터는 이 Phase를 건너뛴다.

```bash
python .claude/scripts/policy.py show
```

`interviewed=true` 이면 **이 Phase를 건너뛰고** 출력된 값을 그대로 사용한다.
`interviewed=false` 일 때만 아래 인터뷰를 수행한다.

[PAUSE]
```
┌─ 작업 정책 (이 프로젝트에 한 번만 묻습니다) ──────────────┐
│ 나중에 변경: python .claude/scripts/policy.py set 키=값    │
│                                                          │
│ 1. 브랜치                                                 │
│    [1] 이슈마다 새 브랜치 생성            (권장)          │
│    [2] 현재 브랜치에서 작업                               │
│                                                          │
│ 2. 트랙(Sprint/Defect) 확인                               │
│    [1] 판정이 애매할 때만 확인            (권장)          │
│    [2] 항상 확인                                          │
│    [3] 항상 자동 판정                                     │
│                                                          │
│ 3. plan.md 검토                                           │
│    [1] 요약만 보고 계속 진행              (권장)          │
│        — 이의가 있으면 /rollback 으로 되돌립니다          │
│    [2] 멈추고 검토                                        │
│                                                          │
│ 4. 구현 자동 진행                                          │
│    [1] AUTO_RUN 6조건 충족 시 자동        (권장)          │
│    [2] 항상 확인 후 진행                                  │
│    [3] 조건을 넓혀 자동 진행                              │
│                                                          │
│ 5. 함정 회고 기록                                          │
│    [1] 후보가 있으면 확인 후 기록         (권장)          │
│    [2] 자동 기록                                          │
│    [3] 기록하지 않음                                      │
└──────────────────────────────────────────────────────────┘

`1,1,1,1,1` 처럼 한 줄로 답해도 되고, `전부 권장` 이라고 해도 됩니다.
```

응답을 아래 값으로 변환해 저장한다. 저장 후에는 다시 묻지 않는다.

| 문항 | 선택 → 값 |
|---|---|
| 1 브랜치 | [1] `branch=new` / [2] `branch=current` |
| 2 트랙 | [1] `track_confirm=boundary` / [2] `always` / [3] `never` |
| 3 plan | [1] `plan_review=notify` / [2] `pause` |
| 4 구현 | [1] `auto_run=standard` / [2] `strict` / [3] `relaxed` |
| 5 함정 | [1] `pitfall_capture=ask` / [2] `auto` / [3] `skip` |

```bash
python .claude/scripts/policy.py init \
  branch={값} track_confirm={값} plan_review={값} auto_run={값} pitfall_capture={값}
```

> 이 정책은 **판단 기준을 미리 정하는 것이지 검증을 없애는 것이 아니다.**
> PHASE 8 수동 UI 테스트, MR 머지 확인, BLOCKED 보고는 정책과 무관하게 항상 사람을 부른다.

---

## Phase 1: 요구사항 수집

### 경로 A — Redmine 이슈 기반 (ISSUE_NUMBERS 있을 때)

**1-A-1. 이슈 즉시 조회 (인터뷰 전)**

`ISSUE_NUMBERS`가 있으면 인터뷰를 시작하기 전에 `redmine` 스킬로 전부 조회한다.
여러 이슈면 공통 맥락을 추출한다.

조회 결과를 **원본 형식 그대로** 출력한다 (redmine 스킬 출력 형식 사용):

```
## Redmine 이슈 #{번호}

**제목:** {subject}
**상태:** {status} | **우선순위:** {priority}
**담당자:** {assigned_to} | **버전:** {fixed_version}
**카테고리:** {category}

### 설명
{description 전문}
```

---

**1-A-2. 이슈 내용 확인 및 보완 [PAUSE]**

이슈 원본을 출력한 직후 사용자에게 보완 기회를 준다:

```
─────────────────────────────────────────────
위 이슈 내용에 추가하거나 수정할 내용이 있나요?
  예) 누락된 배경·제약·완료 기준
      이슈 설명의 오류·오해 정정
      관련 화면·인접 기능 등 참고 정보

→ 보완 내용을 입력하거나, 없으면 '없음' 입력
─────────────────────────────────────────────
```

- 입력값을 `ADDITIONAL_CONTEXT`로 저장한다.
- '없음' 입력 시 `ADDITIONAL_CONTEXT = ""` 로 두고 다음 단계로 진행한다.

---

**1-A-3. 자동 추출 및 기술 분석**

자동 추출 대상 텍스트 = **이슈 description + ADDITIONAL_CONTEXT** 통합본.

분석 결과를 출력한다:

```
📥 Redmine 이슈 분석 결과 {ADDITIONAL_CONTEXT가 있을 때: (※ 사용자 보완 메모 반영됨)}

이슈: #{번호} — {제목}
카테고리: {category} | 우선순위: {priority}

자동 추출된 PRD 항목:
  ✅ 핵심 문제: {이슈 설명 + ADDITIONAL_CONTEXT에서 추출}
  ✅ 대상 사용자: {담당자·카테고리 기반 추정}
  ✅ 핵심 기능: {설명에서 추출된 기능 목록}
  ⬜ 완료 기준: (이슈에서 확인 불가 — 확인 필요)
  ⬜ 제약 조건: (이슈에서 확인 불가 — 확인 필요)
  ⬜ 제외 범위: (명시 없음)
```

이어서 Delphi/VCL 관점으로 기술 분석한다:
- 변경 예상 파일 목록 (.pas / .dfm)
- 공유 유닛(`ComUnit/`, `Common/`, `CommonBL/`, `CommonV7/`) 변경 여부
- DB 스키마 변경 여부

```
📊 기술 분석 결과

변경 예상 파일: {목록}
공유 유닛 변경: 있음 / 없음
DB 변경: 있음 / 없음
```

공유 유닛이나 DB 변경이 있으면:
```
⚠️ 사전 확인 필요 항목
| 항목 | 내용 |
|---|---|
| {항목} | {내용} |
```

---

**1-A-4. GAP만 질문**

✅ 항목은 건너뛰고, ⬜ 항목만 질문한다.
(이슈 설명이 충분하거나 ADDITIONAL_CONTEXT로 보완된 항목도 ✅ 처리하여 생략)

```
📋 추가 확인 (이슈에서 파악되지 않은 항목만)

{⬜ 항목별 질문 — 1~3개로 최소화}

답변 후 즉시 PRD.md를 생성합니다.
(모두 괜찮으면 '건너뜀' 입력)
```

---

### 경로 B — 직접 인터뷰 (ISSUE_NUMBERS 없을 때)

`EXTRA_CONTEXT`가 있으면 인터뷰 질문 앞에 요약 표시:
```
📌 인수에서 감지된 컨텍스트: "{EXTRA_CONTEXT}"
   → 해당 내용을 기반으로 질문을 보완합니다.
```
예: "원인파악해줘" → 질문 1번을 "어떤 문제/버그를 해결하려 하나요?"로 맞춤화

다음 질문을 **한 번에 모두 출력**하여 사용자가 한 번에 답하도록 한다.
(각 항목은 빈칸 가능 — Phase 2에서 GAP 분석으로 보완)

```
📋 요구사항 인터뷰

아래 질문에 답해주세요. 모르는 항목은 비워두셔도 됩니다.

1. 핵심 문제
   이 기능/프로젝트가 해결하려는 문제나 목적은 무엇인가요?
   (예: "환자 예약 현황을 한 화면에서 볼 수 없어 업무 효율이 낮다")

2. 대상 사용자
   누가 이 기능을 사용하나요? (역할/부서/권한 등)
   (예: "원무과 직원, 의사, 관리자")

3. 핵심 기능 (반드시 있어야 할 것)
   MVP에 꼭 포함되어야 할 기능을 나열해주세요.

4. 있으면 좋은 기능 (선택)
   중요하지만 MVP 이후로 미룰 수 있는 기능은?

5. 완료 기준
   언제 "완성됐다"고 할 수 있나요? 측정 가능한 기준으로 설명해주세요.
   (예: "예약 목록이 1초 이내 로딩, 날짜별 필터 동작")

6. 제약 조건
   기술, 일정, 연동, 권한 등 지켜야 할 제약이 있나요?
   (예: "기존 DB 스키마 변경 불가", "Delphi 2007로만 구현")

7. 하지 않을 것
   이번 작업 범위에서 명시적으로 제외할 것은?
```

---

## Phase 2: GAP 분석 및 보완 질의

인터뷰 응답을 받은 후 아래 항목을 점검하고 **비어있거나 불명확한 것만** 추가 질의한다.

```
GAP 체크리스트:
  □ 핵심 문제가 구체적인가? (모호하면 보완 질의)
  □ 대상 사용자가 명확한가?
  □ 핵심 기능이 2개 이상인가?
  □ 완료 기준이 측정 가능한가? ("잘 동작한다" → 불명확)
  □ 제약 조건이 기술됐는가? (없으면 "특별한 제약 없음"으로 처리)
  □ 기술 스택/환경이 파악됐는가? (CLAUDE.md 존재 시 읽어서 자동 보완)
```

**CLAUDE.md 자동 보완:**
`{PROJECT_PATH}/CLAUDE.md`가 있으면 읽어서 기술 스택, 빌드 방식, 코딩 원칙을
PRD의 "제약 조건" 및 "기술 고려사항"에 자동 반영한다.

GAP이 있으면:

```
📌 추가 확인이 필요합니다

{비어있는 항목만 질문}

답변 후 PRD.md를 생성합니다.
(모두 괜찮으면 '건너뜀' 입력)
```

---

## Phase 2.5: 트랙 판정 (공통)

수집된 이슈 정보와 기술 분석 결과를 종합하여 트랙을 자동 판정한다.

**확인 여부는 Phase 0.5의 `track_confirm` 정책을 따른다** (`policy.py get track_confirm`):

| 값 | 동작 |
|---|---|
| `never` | 판정 결과로 자동 확정. [PAUSE] 없음 |
| `boundary` | **Defect 조건 충족 개수가 3~4개일 때만** [PAUSE] (아래 참조) |
| `always` | 항상 [PAUSE] |

`boundary`의 판정 기준 — 5개 조건 중 충족 개수로 가른다:

```
0~2개 충족 → Sprint 확정 (자동)
5개 충족   → Defect 확정 (자동)
3~4개 충족 → 애매하다. [PAUSE]로 확인받는다
```

> 왜 3~4개가 애매한가: `sprint-workflow.md`는 "모두 충족해야 Defect"라고 정하므로
> 4개 충족은 규칙상 Sprint다. 하지만 한 조건 차이로 갈리는 지점이라 오판 비용이 크다 —
> Sprint 규모 작업을 Defect로 처리하면 계획 없이 바로 구현에 들어간다.

```
🔀 트랙 판정

[Defect 조건 체크 — 모두 충족 시 Defect 제안]
  ☑/☐ 프로덕션 장애·버그·긴급 수정
       (tracker, priority, 이슈 제목·설명 키워드 기반 추정)
  ☑/☐ 변경 예상 파일 ≤ 3개  ({추정 파일 수}개)
  ☑/☐ 변경 코드량 ≤ 50줄   (추정)
  ☑/☐ DB 스키마 변경 없음
  ☑/☐ 새 .pas 파일 없음 (dproj 변경 없음)

→ 판정: Defect 트랙 제안 / Sprint 트랙 제안
```

[PAUSE] — 위 정책에 따라 확인이 필요할 때만
```
  [A] Defect 트랙 — Orchestrator·Planner 스킵, PRD `## 검증 계약` 기준으로 직접 구현
  [B] Sprint 트랙  — Orchestrator(PHASE 1~4.5) → Planner(5) → Implementer(6)
```

선택값을 `SELECTED_TRACK` 변수에 저장한다 (A → `defect` / B → `sprint`).
자동 확정한 경우에는 판정 결과를 한 줄로 알린다:
`ℹ️ 트랙 자동 판정: {Sprint|Defect} (조건 {N}/5 충족) — 변경하려면 /rollback`

---

## Phase 3: PRD.md 생성

수집된 정보를 템플릿으로 변환하여 `{PROJECT_PATH}/docs/{PRD_FILENAME}`에 저장한다.

**템플릿:** `.claude/templates/prd-format.md`를 읽어 섹션 구조와 작성 원칙을 따른다.
수집된 정보로 `{...}` 자리표시자를 치환하여 최종 PRD.md를 생성한다.

---

## Phase 4: 브랜치 생성

PRD 생성 후 브랜치를 생성한다.

**4-1. 브랜치명 결정**

현재 브랜치 확인: `git branch --show-current`

```
ISSUE_NUMBERS 있을 때:
  브랜치명 후보: `{현재브랜치}_#{이슈번호}` (이슈 베이스 브랜치)
  → 이후 스프린트 브랜치: `{현재브랜치}_#{이슈번호}_sprint-{NN}`
    (sprint-dev / implementer가 이 브랜치 위에서 자동 생성)

ISSUE_NUMBERS 없을 때:
  브랜치명 후보: `{현재브랜치}_sprint-{NN}` (다음 스프린트 번호)
```

**4-2. 선택**

[자동 판정 — 확인 생략]
현재 브랜치명에 입력된 `#{이슈번호}` 패턴이 이미 포함되어 있으면
(예: 현재 `main_delphi_#213378`, 입력 `#213378`)
→ 이미 해당 이슈의 브랜치이므로 [2]를 자동 선택하고 아래 한 줄만 출력한다:
  "ℹ️ 현재 브랜치가 이미 이슈 브랜치입니다 ({현재 브랜치명}) — 그대로 사용합니다."

[정책 적용 — 위 조건에 해당하지 않을 때]

Phase 0.5의 `branch` 정책을 따른다 (`policy.py get branch`). **[PAUSE] 없이 진행한다.**

| 값 | 동작 | 출력 |
|---|---|---|
| `new` | `{브랜치명 후보}` 생성 | `ℹ️ 새 브랜치 생성: {브랜치명} — 변경하려면 /branch` |
| `current` | 현재 브랜치 그대로 | `ℹ️ 현재 브랜치에서 작업: {현재 브랜치명}` |

> 브랜치는 되돌리기 쉬운 결정이다(`/branch`, `git switch`). 매 이슈마다 물을 이유가 없어
> 정책으로 옮겼다.

[1] 선택 시: `git checkout -b {브랜치명}`

**4-3. Redmine 상태 업데이트 (ISSUE_NUMBERS 있을 때만)**

워크플로우: New(1) → Confirmed(11)
단계를 건너뛸 수 없으므로 현재 상태부터 순차 전환한다.

```
전환 순서 맵: 1→11
목표 상태: Confirmed (status_id=11)

1. 현재 사용자 ID 조회 (assigned_to_id 설정에 필요)
   MCP: 없음 → curl -s -H "X-Redmine-API-Key: $REDMINE_API_KEY" $REDMINE_URL/users/current.json
   → user.id 추출하여 {MY_USER_ID} 로 저장

2. 현재 상태 조회
   MCP(폴백): get_issue(issue_id={이슈번호})
   curl(우선): curl -s -H "X-Redmine-API-Key: $REDMINE_API_KEY" $REDMINE_URL/issues/{이슈번호}.json

3. 현재 status_id에서 11까지 순서대로 호출
   - 현재=1:  → 11(Confirmed) with assigned_to_id
   - 현재=11: 생략

   ※ status_id=11(Confirmed) 전환 시 assigned_to_id 필수:
   MCP(폴백): update_issue(issue_id={이슈번호}, status_id=11, assigned_to_id={MY_USER_ID})
   curl(우선): Body: {"issue": {"status_id": 11, "assigned_to_id": {MY_USER_ID}}}
```

성공: `✅ Redmine #{이슈번호} → 확인됨`
실패: 무시하고 계속 진행

---

## Phase 5: 완료 보고

PRD.md 저장 후 아래 형식을 **그대로** 출력한다.

```
✅ PRD 생성 완료
   경로: {PROJECT_PATH}/docs/{PRD_FILENAME}

📋 요약:
   P0 기능: N개 — {기능명 목록}
   P1 기능: N개
   완료 기준: N개 (자동 X개 / 수동 Y개)
   "[확인 필요]" 항목: Z개  ← Z > 0이면 목록 출력
```

```
──────────────────────────────────────────
✅ PRD 생성 완료: docs/{PRD_FILENAME}
   브랜치: {생성된 브랜치명 또는 현재 브랜치}
──────────────────────────────────────────
```

workspace/{ACTIVE_ISSUE}/STATUS.md 가 없으면 먼저 생성한다:

**SELECTED_TRACK = `sprint` 인 경우:**
```
PHASE=1
TRACK=sprint
CURRENT_SPRINT=
ORCHESTRATOR=pending
PRD=done
```

**SELECTED_TRACK = `defect` 인 경우:**
```
PHASE=6
TRACK=defect
PRD=done
```

---

**SELECTED_TRACK = `sprint` 인 경우:**

Phase 2.5에서 Sprint 트랙을 이미 확정했으므로 실행 여부를 다시 묻지 않고 이어간다.

```
✅ Sprint 트랙 준비 완료 — Orchestrator(PHASE 1)로 이어갑니다.
   (중단하려면 Esc)
```

`.claude/agents/orchestrator.md`를 읽고 현재 PHASE부터 실행한다. [PAUSE] 지점에서 멈추고 확인을 기다린다. 코드 구현은 하지 않는다.

**SELECTED_TRACK = `defect` 인 경우:**

```
✅ Defect 트랙 준비 완료

  TRACK=defect, PHASE=6 으로 STATUS.md 설정됨
  산출물 위치: workspace/{ACTIVE_ISSUE}/ (sprints/ 없음, 루트에 직접)
  PRD의 `## 검증 계약` 섹션이 GOAL.md를 대체합니다.

  바로 구현을 시작하려면 /sprint-dev 를 실행하세요.
```

**STATUS.md 자동 생성 규칙:**
STATUS.md 경로: `{PROJECT_PATH}/workspace/{ACTIVE_ISSUE}/STATUS.md`
(ACTIVE_ISSUE는 Phase 0에서 이슈번호 또는 임시 ID로 이미 확정됨)
해당 경로에 파일이 없으면 Phase 5에서 생성한다. 이미 있으면 건드리지 않는다.

---

## 에러 처리

| 상황 | 처리 |
|------|------|
| `$ARGUMENTS`가 경로인데 존재하지 않음 | [PAUSE] "경로가 존재하지 않습니다. 생성할까요?" |
| 인터뷰 응답이 너무 짧음 (1~2단어) | Phase 2에서 해당 항목 집중 보완 질의 |
| Redmine 조회 실패 | 사용자 입력으로 대체, 계속 진행 |
| docs/ 쓰기 권한 없음 | "경로에 쓸 수 없습니다. 다른 경로를 입력해주세요." |
