---
name: prd
description: "PRD.md 생성. 구조화된 인터뷰 → GAP 분석 → 문서 생성 3단계."
---

# /prd — PRD.md 생성

> orchestrator(PHASE 1)가 검증 없이 바로 통과할 수 있는 완성도 높은 PRD.md를 목표로 한다.
> 구조화된 인터뷰 → GAP 분석 → 문서 생성 3단계로 진행한다.

## 인수 처리 (`$ARGUMENTS`)

`$ARGUMENTS`에서 아래 항목을 독립적으로 추출한다. 순서와 구분자(공백·쉼표·혼합)는 무관하다.

```
추출 규칙:

  PROJECT_PATH  절대경로 토큰 (/ 또는 C:\... 포함)
                없으면 현재 작업 디렉토리
                PROJECT_NAME은 경로의 마지막 디렉토리명으로 자동 설정

  PROJECT_NAME  #이슈번호·절대경로가 아닌 첫 번째 의미 있는 토큰
                예: "billing", "예약모듈"
                없으면 PROJECT_PATH의 마지막 디렉토리명, 둘 다 없으면 "전체"

  ISSUE_NUMBERS 이슈 ID 패턴 (여러 개 가능)
                `#`로 시작하는 토큰(#1234, #PROJ-45) 또는 트래커 키 형식(`[A-Z][A-Z0-9]*-\d+`, 예: PROJ-45)
                저장 시 `#` 접두사를 붙여 통일한다 (PROJ-45 → #PROJ-45)
                있으면 Phase 1 경로 A(이슈 본문 붙여넣기)로 진행

  FLAG_HERE     `--here` 토큰 존재 여부 (Phase 4 브랜치 자동 생성 대신 현재 브랜치 사용 — 이번 호출에만 적용)

  EXTRA_CONTEXT 위 항목 이외의 나머지 텍스트 (자유 설명)
                예: "원인파악해줘", "로그인 관련", "긴급"
                Phase 1 인터뷰의 초기 컨텍스트로 활용

예시:
  /prd billing, #1234, 원인파악해줘
    → PROJECT_NAME=billing  ISSUE_NUMBERS=[#1234]  EXTRA_CONTEXT="원인파악해줘"

  /prd E:/Source/myapp PROJ-45
    → PROJECT_PATH=E:/Source/myapp  PROJECT_NAME=myapp  ISSUE_NUMBERS=[#PROJ-45]

  /prd #1234 --here
    → ISSUE_NUMBERS=[#1234]  FLAG_HERE=true (브랜치 생성 없이 현재 브랜치 사용)

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
    (예: 현재 브랜치 `main_#213378`, 입력 `/prd #213378`)
→ 아래 한 줄만 출력하고 Phase 0으로 진행:
  "ℹ️ 동일 이슈 재진입 (#{이슈번호}, PHASE={N}) — 확인 생략하고 계속합니다."

[완료 이슈 전환 — 확인 생략]
위 조건에 해당하지 않고 PHASE=10 (다른 이슈의 작업 완료 — 다음 스프린트 없음 / Defect 완료 / MVP 완료)이면
전환 질문 없이 아래 안내만 출력하고 새 이슈로 진행한다:
  "ℹ️ 이전 이슈({ACTIVE_ISSUE})는 완료 상태(PHASE=10)입니다 — 새 이슈({입력된 이슈})로 전환합니다.
     기존 이슈 작업은 workspace/{ACTIVE_ISSUE}/에 그대로 보존됩니다."

[이슈 전환 판정 — 확인 필요]
위 조건에 해당하지 않고 PHASE가 5~9 (다른 이슈의 스프린트 진행 중)이면:
  ⚠️ "현재 이슈({ACTIVE_ISSUE})의 스프린트가 진행 중입니다 (PHASE={N}).
   /prd 실행 시 새 이슈({입력된 이슈})로 전환됩니다. 기존 이슈 작업은 그대로 보존됩니다.
   계속하시겠습니까? (1. 예 / 2. 아니오)"
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
  예: "예약 현황 조회" → PRD_예약현황.md
      "billing 로그인 오류" → PRD_billing_로그인.md
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
- 동일 파일명이 이미 있으면 [PAUSE]: "기존 {PRD_FILENAME}이 있습니다. 덮어쓸까요? (1. 예 / 2. 아니오 / 3. 수정)"
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
│    [1] 멈추고 검토 후 승인                (권장)          │
│        — 선 계획 후 실행 원칙                             │
│    [2] 요약만 보고 계속 진행                              │
│        — 이의가 있으면 /rollback [1] 로 되돌립니다        │
│                                                          │
│ 4. 구현 자동 진행                                          │
│    [1] AUTO_RUN 6조건 충족 시 자동        (권장)          │
│    [2] 항상 확인 후 진행                                  │
│    [3] 조건을 넓혀 자동 진행                              │
│                                                          │
│ 5. 함정 회고 기록                                          │
│    [1] 후보가 있으면 확인 후 기록         (권장)          │
│    [2] 기록하지 않음                                      │
│        (확인 없는 자동 기록은 없다 — pitfalls.md는 공유 자산) │
└──────────────────────────────────────────────────────────┘

`1,1,1,1,1` 처럼 한 줄로 답해도 되고, `전부 권장` 이라고 해도 됩니다.
```

응답을 아래 값으로 변환해 저장한다. 저장 후에는 다시 묻지 않는다.

| 문항 | 선택 → 값 |
|---|---|
| 1 브랜치 | [1] `branch=new` / [2] `branch=current` |
| 2 트랙 | [1] `track_confirm=boundary` / [2] `always` / [3] `never` |
| 3 plan | [1] `plan_review=pause` / [2] `notify` |
| 4 구현 | [1] `auto_run=standard` / [2] `strict` / [3] `relaxed` |
| 5 함정 | [1] `pitfall_capture=ask` / [2] `skip` |

```bash
python .claude/scripts/policy.py init \
  branch={값} track_confirm={값} plan_review={값} auto_run={값} pitfall_capture={값}
```

> 이 정책은 **판단 기준을 미리 정하는 것이지 검증을 없애는 것이 아니다.**
> PHASE 8 수동 UI 테스트, MR 머지 확인, BLOCKED 보고는 정책과 무관하게 항상 사람을 부른다.

---

## Phase 1: 요구사항 수집

### 경로 A — 이슈 기반 (ISSUE_NUMBERS 있을 때)

> 이슈 트래커 연동은 없다. 이슈 본문은 사용자가 붙여넣은 텍스트(또는 EXTRA_CONTEXT)로 받는다.

**1-A-1. 이슈 본문 수집 [PAUSE]**

`ISSUE_NUMBERS`가 있으면 인터뷰를 시작하기 전에 이슈 본문을 요청한다.
EXTRA_CONTEXT에 이미 충분한 설명이 있으면 이 단계를 생략한다.

```
─────────────────────────────────────────────
📥 이슈 #{번호} 의 제목·설명을 붙여넣어 주세요.
  (이슈 트래커 화면 내용 그대로 복사해도 됩니다)
  추가로 알려줄 배경·제약·완료 기준이 있으면 함께 적어주세요.

→ 붙여넣을 내용이 없으면 '없음' 입력 (경로 B 인터뷰로 전환)
─────────────────────────────────────────────
```

- 입력값을 `ISSUE_TEXT`로 저장한다. 여러 이슈면 공통 맥락을 추출한다.
- '없음' 입력 시 경로 B로 전환한다.

---

**1-A-2. 자동 추출 및 기술 분석**

자동 추출 대상 텍스트 = **ISSUE_TEXT + EXTRA_CONTEXT** 통합본.

분석 결과를 출력한다:

```
📥 이슈 분석 결과

이슈: #{번호} — {제목}

자동 추출된 PRD 항목:
  ✅ 핵심 문제: {이슈 본문에서 추출}
  ✅ 대상 사용자: {본문 기반 추정}
  ✅ 핵심 기능: {설명에서 추출된 기능 목록}
  ⬜ 완료 기준: (이슈에서 확인 불가 — 확인 필요)
  ⬜ 제약 조건: (이슈에서 확인 불가 — 확인 필요)
  ⬜ 제외 범위: (명시 없음)
```

이어서 프로젝트 기술 스택(CLAUDE.md "기술 스택") 관점으로 기술 분석한다:
- 변경 예상 파일 목록
- 공용 모듈(CLAUDE.md "프로젝트 구조"에 공용으로 표시된 경로) 변경 여부
- DB 스키마 변경 여부

```
📊 기술 분석 결과

변경 예상 파일: {목록}
공용 모듈 변경: 있음 / 없음
DB 변경: 있음 / 없음
```

공용 모듈이나 DB 변경이 있으면:
```
⚠️ 사전 확인 필요 항목
| 항목 | 내용 |
|---|---|
| {항목} | {내용} |
```

---

이어서 Phase 2.5의 **트랙 판정 체크(☑/☐ 5개)를 이 시점에 미리 수행**하고, 정책(`track_confirm`)에 따라
확인이 필요한지(`always`, 또는 `boundary`에서 3~4/5 충족)를 판정해 둔다.

---

**1-A-3. 통합 확인 [PAUSE] — 경로 A의 유일한 인터뷰 질의**

보완 요청 · GAP 질문 · 트랙 제안을 **한 화면에 묶어 한 번만** 묻는다.
⬜ 항목만 질문하며(1~3개로 최소화), ✅ 항목은 건너뛴다.
(이슈 본문이나 EXTRA_CONTEXT로 이미 파악된 항목도 ✅ 처리하여 생략)

```
─────────────────────────────────────────────
📋 확인 (한 번에 답해주세요)

1. 이슈 보완 (선택)
   누락된 배경·제약·완료 기준, 이슈 설명의 오류 정정, 관련 화면 등
   → 없으면 비워두기

2. 추가 확인 (이슈에서 파악되지 않은 항목만)
   {⬜ 항목별 질문 — 1~3개}

3. 트랙: {Defect / Sprint} 제안  (체크 {N}/5 충족)        ← 정책상 확인이 필요할 때만 표시
   [A] Defect — Orchestrator·Planner 스킵, PRD `## 검증 계약` 기준 직접 구현
   [B] Sprint — Orchestrator(PHASE 1~4.5) → Planner(5) → Implementer(6)
   → 제안대로면 언급 불필요, 바꾸려면 A/B 입력

모두 괜찮으면 '건너뜀' 입력 → 제안 트랙으로 즉시 PRD 생성
─────────────────────────────────────────────
```

- 1번 응답 → `ADDITIONAL_CONTEXT`로 저장 (없으면 `""`). 2번 응답과 함께 PRD 항목에 반영한다.
- 1번 보완 내용으로 이미 해결된 2번 질문은 답이 없어도 ✅ 처리한다.
- 3번은 정책상 확인이 필요할 때만 표시한다. 표시하지 않았거나 응답이 없으면 제안 트랙을 `SELECTED_TRACK`으로 확정한다 (A → `defect` / B → `sprint`).
  자동 확정 시 `ℹ️ 트랙 자동 판정: {Sprint|Defect} (조건 {N}/5 충족) — 변경하려면 /rollback` 한 줄을 출력한다.
- ⬜ 항목이 0개이고 3번도 표시할 필요가 없으면 이 [PAUSE]를 생략하고 판정 한 줄만 출력한 뒤 Phase 3으로 간다.
- 경로 A는 이 응답 후 **Phase 2·Phase 2.5를 건너뛰고** Phase 3으로 직행한다.
  (단, 1번 보완 내용으로 DB 변경·파일 수 증가 등 트랙 판정 근거가 바뀌었는데
   사용자가 트랙을 지정하지 않았으면 Phase 2.5 체크를 다시 계산해 결과만 한 줄 출력)

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
   (예: "예약 현황을 한 화면에서 볼 수 없어 업무 효율이 낮다")

2. 대상 사용자
   누가 이 기능을 사용하나요? (역할/부서/권한 등)
   (예: "운영 담당자, 일반 사용자, 관리자")

3. 핵심 기능 (반드시 있어야 할 것)
   MVP에 꼭 포함되어야 할 기능을 나열해주세요.

4. 있으면 좋은 기능 (선택)
   중요하지만 MVP 이후로 미룰 수 있는 기능은?

5. 완료 기준
   언제 "완성됐다"고 할 수 있나요? 측정 가능한 기준으로 설명해주세요.
   (예: "예약 목록이 1초 이내 로딩, 날짜별 필터 동작")

6. 제약 조건
   기술, 일정, 연동, 권한 등 지켜야 할 제약이 있나요?
   (예: "기존 DB 스키마 변경 불가", "현재 프레임워크 버전 유지")

7. 하지 않을 것
   이번 작업 범위에서 명시적으로 제외할 것은?
```

---

## Phase 2: GAP 분석 및 보완 질의 (경로 B 전용)

> 경로 A는 1-A-3에서 GAP 질의를 이미 마쳤으므로 이 Phase를 실행하지 않는다 (중복 질의 금지).

경로 B 인터뷰 응답을 받은 후 아래 항목을 점검하고 **비어있거나 불명확한 것만** 추가 질의한다.

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

GAP 질의 전에 Phase 2.5의 트랙 판정 체크를 먼저 계산한다.

GAP이 있으면 (정책상 트랙 확인이 필요하면 같은 화면에 포함 — 별도 PAUSE 없음):

```
📌 추가 확인이 필요합니다

{비어있는 항목만 질문}

트랙: {Defect / Sprint} 제안  (체크 {N}/5 충족)        ← 정책상 확인이 필요할 때만 표시
  [A] Defect / [B] Sprint — 제안대로면 언급 불필요, 바꾸려면 A/B 입력

답변 후 PRD.md를 생성합니다.
(모두 괜찮으면 '건너뜀' 입력)
```

→ 트랙 응답이 없으면 제안 트랙으로 `SELECTED_TRACK` 확정, Phase 2.5 건너뜀.
GAP이 없으면 → Phase 2.5로 진행.

---

## Phase 2.5: 트랙 판정 [조건부 PAUSE]

> 경로 A(1-A-3) 또는 Phase 2 GAP 화면에서 이미 트랙이 확정됐으면 이 Phase를 건너뛴다.
> 실질적으로 **경로 B + GAP 없음**일 때만 실행된다.

수집된 정보와 기술 분석 결과를 종합하여 트랙을 자동 판정한다.

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
       (이슈 제목·설명 키워드 기반 추정)
  ☑/☐ 변경 예상 파일 ≤ 3개  ({추정 파일 수}개)
  ☑/☐ 변경 코드량 ≤ 50줄   (추정)
  ☑/☐ DB 스키마 변경 없음
  ☑/☐ 신규 소스 파일 없음 (프로젝트/빌드 설정 변경 없음)

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
  브랜치명 후보: `{현재브랜치}_#{이슈번호}` (이슈 베이스 브랜치 = ISSUE_BRANCH)
  → 이후 스프린트 브랜치: `{ISSUE_BRANCH}_sprint-{NN}`
    (/sprint-dev 2단계가 ISSUE_BRANCH 위에서 생성)

ISSUE_NUMBERS 없을 때:
  후보 없음 — 임시 작업은 현재 브랜치 사용 (4-2 규칙 5)
```

**4-2. 자동 결정 (질의 없음)**

브랜치는 되돌리기 쉬운 결정이다(`/branch`, `git switch`). 매 이슈마다 묻지 않고
아래 순서로 **첫 번째 해당 규칙**을 적용한다. 정책 `branch`(`policy.py get branch`)는 규칙 3에서 쓴다.

```
1. 현재 브랜치명에 입력된 `#{이슈번호}`가 이미 포함됨
   (예: 현재 `main_#213378`, 입력 `#213378`)
   → 현재 브랜치 사용
     "ℹ️ 현재 브랜치가 이미 이슈 브랜치입니다 ({현재 브랜치명}) — 그대로 사용합니다."
   ISSUE_BRANCH = 현재 브랜치
   PARENT_BRANCH = 현재 브랜치에서 끝의 `_#{이슈번호}`를 제거한 값 (예: `main`)
                   — 끝이 `_#{이슈번호}`가 아니면 빈 값 (PR/MR 시점에 질의)

2. 현재 브랜치가 main / master
   → FLAG_HERE·정책을 무시하고 반드시 새 브랜치 생성 (보호 브랜치 직접 커밋 금지 규칙)
   detached HEAD(`git branch --show-current`가 빈 값)면 브랜치명을 만들 수 없으므로
   [PAUSE] "detached HEAD 상태입니다. 이슈 브랜치를 만들 기준 브랜치명을 알려주세요." → 받은 이름으로 checkout 후 4번 규칙 적용
   ISSUE_BRANCH = 생성한 브랜치, PARENT_BRANCH = 기준 브랜치 (main/master 또는 입력값)

3. FLAG_HERE=true 또는 정책 `branch=current`
   → 현재 브랜치 사용
     "ℹ️ 현재 브랜치({현재 브랜치명})에서 작업합니다. (--here / 정책 branch=current)"
   ISSUE_BRANCH = 현재 브랜치, PARENT_BRANCH = 빈 값 (PR/MR 시점에 질의)

4. ISSUE_NUMBERS 있음 (정책 `branch=new`)
   → 새 브랜치 생성: `git checkout -b {브랜치명 후보}`
     "ℹ️ 이슈 브랜치 생성: {브랜치명 후보} (현재 브랜치 유지하려면 다음부터 --here)"
   ISSUE_BRANCH = {브랜치명 후보}, PARENT_BRANCH = 생성 직전의 현재 브랜치

5. ISSUE_NUMBERS 없음 (임시 작업)
   → 현재 브랜치 사용 (임시 ID 작업은 브랜치 분기 강제 안 함)
     "ℹ️ 임시 작업 — 현재 브랜치({현재 브랜치명})에서 작업합니다."
   ISSUE_BRANCH = 현재 브랜치, PARENT_BRANCH = 빈 값 (PR/MR 시점에 질의)
```

※ 같은 이름의 브랜치가 이미 존재하면 `git checkout {브랜치명}`으로 전환만 한다.
※ 확정한 `ISSUE_BRANCH`·`PARENT_BRANCH`는 Phase 5에서 STATUS.md에 기록한다.
  이후 단계(sprint-dev·validator)는 브랜치명을 다시 추론하지 않고 이 값을 읽는다 (`rules/active-issue.md` "STATUS.md 브랜치 필드").

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
PRD_FILE=docs/{PRD_FILENAME}
PARENT_BRANCH={4-2에서 확정한 값, 없으면 빈 값}
ISSUE_BRANCH={4-2에서 확정한 값}
SPRINT_BRANCH=
```

**SELECTED_TRACK = `defect` 인 경우:**
```
PHASE=6
TRACK=defect
PRD=done
PRD_FILE=docs/{PRD_FILENAME}
PARENT_BRANCH={4-2에서 확정한 값, 없으면 빈 값}
ISSUE_BRANCH={4-2에서 확정한 값}
```

> `KEY=value` 형식을 유지한다. 루프 층(`loop_state.py`)은 `KEY=value`·`KEY: value` 둘 다 읽지만,
> 한 파일 안에서 형식을 섞지 않는다.

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
해당 경로에 파일이 없으면 Phase 5에서 생성한다. 이미 있으면 기존 값은 건드리지 않고,
`PRD_FILE`·`PARENT_BRANCH`·`ISSUE_BRANCH` 중 **없는 키만** 끝에 덧붙인다 (기존 이슈 재진입 시 필드 보강).

---

## 에러 처리

| 상황 | 처리 |
|------|------|
| `$ARGUMENTS`가 경로인데 존재하지 않음 | [PAUSE] "경로가 존재하지 않습니다. 생성할까요?" |
| 인터뷰 응답이 너무 짧음 (1~2단어) | Phase 2에서 해당 항목 집중 보완 질의 |
| docs/ 쓰기 권한 없음 | "경로에 쓸 수 없습니다. 다른 경로를 입력해주세요." |
