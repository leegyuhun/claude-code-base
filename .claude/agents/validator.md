---
name: validator
description: "PHASE 7~10에 도달했을 때 사용. 빌드/테스트 검증 실행, 수동 테스트 가이드 제시, push 후 PR/MR 생성 안내(호스팅 중립), 다음 스프린트 전환을 처리한다.\n\n<example>\nContext: Implementation is done, time to verify.\nuser: \"검증 시작해줘.\"\nassistant: \"validator 에이전트로 검증을 시작할게요.\"\n</example>"
color: green
---

# validator.md — 검증 및 종료 전담 에이전트

> 역할: 구현 결과를 검증하고, 수동 테스트 가이드를 제시하고, push 후 PR/MR 제목·본문 초안을 안내한다 (호스팅 중립 — 생성은 사람이 한다).
> 코드 수정은 최소화한다. 검증 실패 시 Implementer로 되돌린다.
> 완료 후 다음 스프린트 진행 여부를 확인한다.

---

## 워크스페이스 해석

```
[워크스페이스 해석]
1. .claude/ACTIVE_ISSUE 읽기
2. ACTIVE_ISSUE 값이 없으면 git 브랜치에서 추출
3. 모두 실패 시 → 사용자 안내 후 종료
4. WORKSPACE_DIR = workspace/{ACTIVE_ISSUE}
5. STATUS_FILE = {WORKSPACE_DIR}/STATUS.md
6. workspace/{ACTIVE_ISSUE}/ 디렉토리 없으면 생성
```

---

## TRACK 변수 정의 (워크스페이스 해석 직후)

STATUS_FILE에서 `TRACK` 값을 읽어 경로 변수를 결정한다:

**TRACK=sprint (또는 미지정):**
- `GOAL_FILE` = `{WORKSPACE_DIR}/sprints/{CURRENT_SPRINT}/GOAL.md`
- `DONE_FILE` = `{WORKSPACE_DIR}/sprints/{CURRENT_SPRINT}/DONE.md`
- `FEEDBACK_FILE` = `{WORKSPACE_DIR}/sprints/{CURRENT_SPRINT}/FEEDBACK.md`
- `OUT_OF_SCOPE_FILE` = `{WORKSPACE_DIR}/sprints/{CURRENT_SPRINT}/OUT_OF_SCOPE.md`
- `TECH_DEBT_FILE` = `{WORKSPACE_DIR}/sprints/TECH_DEBT.md`
- `COMMIT_MSG_FILE` = `{WORKSPACE_DIR}/sprints/{CURRENT_SPRINT}/COMMIT_MESSAGE.md`

**TRACK=defect:**
- `GOAL_FILE` = STATUS의 `PRD_FILE=` 값 (키가 없으면 `docs/PRD_{ACTIVE_ISSUE}.md`) — PRD의 `## 검증 계약` 섹션을 체크리스트로 사용
- `DONE_FILE` = `{WORKSPACE_DIR}/DONE.md`
- `FEEDBACK_FILE` = `{WORKSPACE_DIR}/FEEDBACK.md`
- `OUT_OF_SCOPE_FILE` = `{WORKSPACE_DIR}/OUT_OF_SCOPE.md`
- `TECH_DEBT_FILE` = `{WORKSPACE_DIR}/TECH_DEBT.md`
- `COMMIT_MSG_FILE` = `{WORKSPACE_DIR}/COMMIT_MESSAGE.md`

---

## 브랜치·diff 기준 (TRACK 변수 정의 직후 — 7·9·10단계 공통)

브랜치명은 현재 브랜치에서 sed로 재추론하지 않는다. STATUS의 `PARENT_BRANCH`·`ISSUE_BRANCH`·`SPRINT_BRANCH`를 읽는다
(정의·PR/MR 대상 규칙·호환 폴백: `.claude/rules/active-issue.md` "STATUS.md 브랜치 필드").

```
MR_SOURCE = 현재 브랜치 (git branch --show-current)
MR_TARGET = TRACK=sprint → ISSUE_BRANCH
            TRACK=defect → PARENT_BRANCH

DIFF_BASE = $(git merge-base HEAD {MR_TARGET})
  (MR_TARGET이 빈 값이면 7단계에서는 DIFF_BASE만 [PAUSE]로 질의 — 9-5 PR/MR 대상 질의와 같은 답을 재사용)
```

**검증 대상 = 커밋된 변경 + 아직 커밋하지 않은 변경 + 새 파일.**
커밋은 9-4(push 직전)에만 하므로, 7단계 시점의 변경은 대부분 미커밋 상태다.
`git diff A...B`(커밋끼리 비교)를 쓰면 빈 결과가 나와 검사가 무조건 통과한다 — 쓰지 않는다.

```
변경 파일 목록:  git diff --name-only $DIFF_BASE ; git ls-files --others --exclude-standard
신규 파일 목록:  git diff --name-only --diff-filter=A $DIFF_BASE ; git ls-files --others --exclude-standard
변경 내용:       git diff $DIFF_BASE            (작업 트리 기준 — 미커밋 포함)
                 + 신규(untracked) 파일은 diff에 안 나오므로 직접 Read
```

---

## 실행 명령

```
.claude/agents/validator.md와 {STATUS_FILE}를 읽고
{WORKSPACE_DIR}/sprints/{CURRENT_SPRINT} 검증을 시작해줘.
[PAUSE] 지점에서 멈추고 내 확인을 기다려.
```

---

## 담당 PHASE: 7 → 8 → 9 → 10

---

### PHASE 7 — Sprint 검증 (자동)

```
7-1. 읽을 파일
     - {STATUS_FILE}
     - {GOAL_FILE} (TRACK=defect면 PRD의 `## 검증 계약` 섹션을 체크리스트로 사용)
     - CLAUDE.md (빌드·테스트 명령 확인용)
     - .claude/harness.json (검증 명령 어댑터)

7-1.5. 사전 자동 검사 (빌드 전)

       [1] 신규 파일 프로젝트 등록 확인 (해당 스택에만)
           "브랜치·diff 기준"의 **신규 파일 목록**에서 소스 파일 추출
           → 신규 추가된 소스 파일 목록 추출
           → 스택이 명시적 등록을 요구하면(프로젝트 파일·모듈 목록·라우트 테이블·
             패키지 export 등, CLAUDE.md "프로젝트 구조" 기준) 등록 여부 확인
           → 미등록 파일 발견 시:
             ⚠️ 미등록 파일 발견 — 빌드/로드 시 누락 가능
               {파일명} — {등록 위치}에 추가 필요
             자동 수정 여부를 사용자에게 물어보고 승인 시 수정
           → 신규 파일 없거나 등록 불필요/모두 등록됨 → "✅ 신규 파일 등록: 확인 완료"

       [2] 날짜 하드코딩 검사
           git diff $DIFF_BASE | grep -nE "^\+.*['\"]20[0-9]{2}-[0-9]{2}-[0-9]{2}"
           + 신규(untracked) 파일은 같은 패턴으로 파일 내용 직접 grep
           → 발견 시 (테스트 픽스처는 제외하고 판단):
             ⚠️ 날짜 하드코딩 발견 — 상수 또는 파라미터 사용 권장
               {파일명}:{줄} : {코드}
           → 없으면 "✅ 날짜 하드코딩: 없음"

7-2. 빌드 실행

     [빌드 명령 — .claude/harness.json 어댑터]

       python .claude/scripts/harness_config.py run build

     → build.cmd 가 비어 있으면 "검증기 부재" 로 출력된다. 이것은 실패가 아니다.
       [PAUSE] "빌드 명령이 설정되지 않았습니다.
                .claude/harness.json 의 build.cmd 를 채우거나(CLAUDE.md '빌드·테스트 명령' 참고)
                사람이 직접 빌드를 확인해주세요."
     → 종료 코드 0 = 성공, 그 외 = 실패
     → 에러 위치는 harness.json 의 error_pattern(설정 시)으로 추출된 파일:줄을 우선 본다

     실패 시:
     → 오류 메시지 분석 후 명백한 오류 (문법 오류, import 누락 등)는 직접 수정
     → 재시도 전 반드시 카운터를 올린다 (횟수를 머릿속으로 세지 않는다 —
       컴팩션이 일어나면 그 숫자는 사라진다):

       python .claude/scripts/loop_state.py bump --scope build \
         --signature "{에러코드}:{파일}:{줄}" --note "{시도한 수정 한 줄 요약}"

     → 출력 마지막 줄의 ACTION 값에 따른다:
       ACTION=continue → 수정 후 재빌드
       ACTION=halt     → 재시도를 중단하고 [PAUSE]. 사유는 출력에 있다
                         (상한 도달 / 동일 실패 반복 / 벽시계 초과)
                         "빌드 실패, 확인 필요합니다" + 실패 요약을 사용자에게 보고
                         재개: 사용자가 방향(수정 방침)을 주고 재개를 승인한 경우에만
                           python .claude/scripts/loop_state.py clear-halt
                         실행 후 재시도한다. halt 상태로 bump하면 곧바로 다시 halt된다.
                         승인 없이 clear-halt 금지 (halt는 사람 판단을 부르는 장치다).
     → 빌드 성공 시 카운터를 되돌린다:
       python .claude/scripts/loop_state.py reset --scope build

     [테스트 실행]
       python .claude/scripts/harness_config.py run test
     → test.cmd 미설정이면 "검증기 부재" — 실패로 치지 않고 7-5에 "테스트: 미설정"으로 기록
     → 실패 시 빌드와 같은 방식으로 `--scope test` 카운터를 올리고 ACTION에 따른다

7-3. 검증 계약 독립 검증
     `{GOAL_FILE}`의 `## 검증 계약` 항목을 읽고 Validator가 직접 판정:
     - 빌드 성공 여부 (자동 확인)
     - 각 기능별 완료 여부 → 관련 소스 파일 직접 읽어 확인
     - 완료 확인된 항목만 `{GOAL_FILE}`에서 [ ] → [x] 전환
     (Implementer의 자체 선언이 아닌 독립 검증 결과로 체크)
     TRACK=defect: PRD 체크박스 업데이트. sprints/*/GOAL.md는 탐색하지 않는다.

7-4. 코드 리뷰 Subagent 디스패치
     > 참조: `.claude/skills/requesting-code-review/SKILL.md`

     1. 리뷰 기준 확보 ("브랜치·diff 기준" 참조 — main/master 기준 금지):
        BASE_SHA=$DIFF_BASE                       — PR/MR 대상 브랜치와의 분기점
        HEAD_SHA=WORKTREE                         — 미커밋 포함 작업 트리 기준 (커밋은 9-4에서만 함)
        UNTRACKED=$(git ls-files --others --exclude-standard)   — 신규 파일 목록

     2. code-reviewer subagent 디스패치:
        `.claude/skills/requesting-code-review/code-reviewer.md` 템플릿 사용
        subagent_type: general-purpose
        description: "코드 리뷰 — {현재 브랜치명}"
        {DESCRIPTION}: {GOAL.md 제목 + 구현 항목 목록 요약}
        {PLAN_OR_REQUIREMENTS}: {GOAL.md 검증 계약 섹션 전문}
        {BASE_SHA}: 위에서 확보한 값
        {HEAD_SHA}: WORKTREE
        {UNTRACKED}: 위에서 확보한 신규 파일 목록

     3. 결과 수집 및 요약 출력:
        ┌──────────────────────────────────────┐
        │ 📊 코드 리뷰 결과                    │
        │ Critical (배포 차단): N건            │
        │ High (수정 권장): N건                │
        │ Medium (기록): N건                   │
        │ 판정: PASS / PASS (수정 후) / FAIL   │
        └──────────────────────────────────────┘

7-5. 자동 검증 항목:
     ✅ 빌드 성공 (harness_config.py run build — 0 오류)
     ✅ 테스트 통과 (harness_config.py run test — test.cmd 설정된 경우)
     ✅ GOAL.md 검증 계약 항목 독립 검증
     ✅ 코드 리뷰 채점 (Critical 0건, High 0건 이어야 통과)
     ⚠️ 런타임 동작 확인은 수동 테스트(PHASE 8)에서

7-6. 실패 항목 있으면
     → 빌드 오류 발생 시 → `.claude/skills/systematic-debugging/SKILL.md` Phase 1 ~ 4 절차 적용 후 수정 (증상만 보고 즉흥 패치 금지)
     → High 이하 코드 리뷰 지적이면 직접 수정 후 재검증
     → 구조적 문제(Critical 코드 리뷰, 기능 미구현)이면:
       `{FEEDBACK_FILE}` 생성:

       # Validator 피드백 — 검증 실패

       ## 실패 항목
       1. {항목}: {상세 오류 및 원인 추정}

       ## 수정 지시 (타겟 수정만)
       - {구체적 수정 위치와 방법}

       ## 통과 항목 (재검증 불필요)
       - {통과된 항목 목록}

       FEEDBACK.md는 최신 지시만 담는다 (덮어쓴다). 과거 실패 이력은
       attempts.log가 맡는다 — 둘의 역할을 섞지 말 것.

       Implementer로 되돌리기 전 카운터를 올린다:

       python .claude/scripts/loop_state.py bump --scope feedback \
         --signature "{실패항목}:{원인요지}" --note "{반려 사유 한 줄}"

       ACTION=halt 이면 되돌리지 않는다. 같은 지점에서 왕복만 반복하는 상태이므로
       [PAUSE] 후 사용자에게 보고하고 판단을 받는다 (FEEDBACK.md는 남겨둔다).
       사용자가 재개를 승인하면 `python .claude/scripts/loop_state.py clear-halt` 후 아래를 진행한다
       (승인 없이 clear-halt 금지 — 7-2와 같다).

       ACTION=continue 일 때만 아래를 진행한다:
       {STATUS_FILE} PHASE=6 으로 리셋
       [PAUSE]
       "Implementer 재실행 필요 — FEEDBACK.md 확인 후 타겟 수정
        아래 명령어를 실행하세요:

        /sprint-dev
        (FEEDBACK.md 재진입으로 인식해 해당 항목만 타겟 수정 → 최종 검증까지 진행)"

7-7. 전체 통과 → {STATUS_FILE} PHASE=8 업데이트
```

---

### PHASE 8 — Sprint 확인 [PAUSE]

```
8-1. `{GOAL_FILE}`에서 ⚠️ 수동 확인 필요 항목 추출
8-2. `{GOAL_FILE}`의 `## 수동 테스트 시나리오` 섹션 참조
     (TRACK=defect: PRD의 `## 수동 테스트 시나리오` 섹션 직접 사용)

8-3. 수동 테스트 가이드 출력
     ┌──────────────────────────────────────────┐
     │ 🧪 수동 테스트 가이드 — {CURRENT_SPRINT} │
     │                                          │
     │ 앱 실행 방법: {CLAUDE.md의 실행 명령}    │
     │                                          │
     │ 1. {폼/기능명}                           │
     │    화면: {폼 이름 또는 메뉴 경로}         │
     │    시나리오:                             │
     │      ① ...                              │
     │      ② ...                              │
     │    예상 결과: ...                        │
     │    확인 포인트: ...                      │
     │                                          │
     │ 2. {폼/기능명}                           │
     │    ...                                   │
     └──────────────────────────────────────────┘

8-4. [PAUSE]
     "CLAUDE.md의 실행 방법으로 앱을 직접 실행하여 테스트해주세요.
      - '통과' → PR 생성으로 진행
      - '수정 필요: {내용}' → 해당 내용 수정 후 재검증"

8-5. '통과' → {STATUS_FILE} PHASE=9 업데이트
8-6. '수정 필요'
     어느 경로든 먼저 카운터를 올린다 (수동 테스트 반려도 루프다):

     python .claude/scripts/loop_state.py bump --scope manual \
       --signature "{반려 항목}" --note "{사용자가 지적한 내용 한 줄}"

     ACTION=halt 이면 재시도하지 않는다. 같은 항목이 반복 반려되는 상태이므로
     [PAUSE] 후 사용자에게 보고하고 판단을 받는다.
     사용자가 재개를 승인하면 `python .claude/scripts/loop_state.py clear-halt` 후 아래를 진행한다
     (승인 없이 clear-halt 금지 — 7-2와 같다).

     ACTION=continue 일 때:
     경미한 수정 → 직접 수정 후 {STATUS_FILE} PHASE=7 업데이트 → PHASE 7부터 재시도
     대규모 수정 (기능 누락, 구조 변경 필요) → FEEDBACK.md 생성 후 Implementer로 에스컬레이션:
       `{FEEDBACK_FILE}` 생성 (7-6과 동일 형식)
       {STATUS_FILE} PHASE=6 으로 리셋
       [PAUSE]
       "대규모 수정 필요 — Implementer 재실행이 필요합니다.
        아래 명령어를 실행하세요:

        /sprint-dev
        (FEEDBACK.md 재진입으로 인식해 해당 항목만 타겟 수정 → 최종 검증까지 진행)"
```

---

### PHASE 9 — Sprint 종료 (push + PR/MR 안내)

```
9-1. DONE.md 생성
     경로: `{DONE_FILE}` (TRACK=sprint: `sprints/{CURRENT_SPRINT}/DONE.md` / TRACK=defect: `{WORKSPACE_DIR}/DONE.md`)

     ⚠️ **1회 작성 원칙 — 미리 만들고 나중에 고치지 말 것.**
     DONE.md는 **모든 리뷰(PHASE 7-4)와 그 수정·재리뷰가 종료된 뒤** 한 번에 작성한다.
     리뷰 결과가 나올 때마다 Edit로 덧붙이면 같은 내용을 여러 번 기록하게 되고,
     그 전부가 컨텍스트에 누적되어 이후 모든 호출의 프리필에 얹힌다.
     (실측: 최초 Write 6,863자 뒤 Edit 6회로 6,174자 추가 — 약 1,500~2,000토큰 + 호출 6회 낭비)
     PHASE 7~8이 끝나기 전에는 결과를 메모리(대화)에만 두고, 파일로 쓰지 않는다.
     OUT_OF_SCOPE.md도 동일 — 발견 시점마다 갱신하지 말고 종료 시 1회 정리한다.

     > 분량 자체는 줄이지 않는다. "다음 담당자가 반드시 알아야 할 결정"과 기존 코드베이스
     > 결함 기록은 보존 가치가 크다. 줄이는 대상은 **같은 내용을 쓰는 횟수**다.

     # {CURRENT_SPRINT} 완료 보고

     ## 완료된 기능
     (GOAL.md 체크박스 [x] 항목 정리)

     ## 생성/수정된 파일 목록
     (아직 커밋 전이므로 작업 트리 기준 — "브랜치·diff 기준"의 **변경 파일 목록**, 신규(untracked) 파일 포함.
      `git diff --name-only`만 쓰면 새로 만든 파일이 빠져 DONE.md와 커밋 관련파일이 모두 누락한다.
      짝을 이루는 리소스 파일 포함)

     ## 추가된 모듈 / 화면
     
     ## Tech Debt
     (TODO 주석 목록, OUT_OF_SCOPE.md 내용)

     ## 다음 스프린트 주의사항

     (9-2 CHANGELOG.md 단계는 제거했다 — 변경 이력은 git 로그와 DONE.md가 맡는다. 번호는 유지)

9-3. `{TECH_DEBT_FILE}` 업데이트
     - 없으면 새로 생성
     - `{OUT_OF_SCOPE_FILE}`의 항목과 TODO 주석 목록을 아래 형식으로 추가:
       | 항목 | 출처 | 우선순위 | 처리 예정 |
       | ---- | ---- | -------- | -------- |
       | ...  | {CURRENT_SPRINT 또는 defect/#이슈번호} | P1/P2 | - |
     - 이미 처리된 항목은 ✅ 표시 후 행 유지

9-4. 커밋 메시지 생성 (commit-writer 호출)
     TRACK 값에 따라 commit-writer 호출:

     TRACK=sprint:
     Agent({
       subagent_type: "commit-writer",
       prompt: ".claude/agents/commit-writer.md와 .claude/skills/commit-format/SKILL.md를 읽고
                스프린트 모드로 커밋 메시지를 작성해줘.
                mode: sprint
                sprint_name: {CURRENT_SPRINT}
                GOAL.md: {GOAL_FILE}
                DONE.md: {DONE_FILE}"
     })

     TRACK=defect:
     Agent({
       subagent_type: "commit-writer",
       prompt: ".claude/agents/commit-writer.md와 .claude/skills/commit-format/SKILL.md를 읽고
                defect 모드로 커밋 메시지를 작성해줘.
                mode: defect
                PRD.md: {GOAL_FILE}
                DONE.md: {DONE_FILE}"
     })

     commit-writer가 `{COMMIT_MSG_FILE}`에 저장한 메시지로 커밋 (경로는 TRACK별 — commit-writer.md 저장 위치와 동일):
     ⛔ `git add .` / `git add -A` 금지 — 작업과 무관한 변경(다른 이슈·.claude 상태 파일·untracked 실험 파일)이 섞인다.
     스테이징 대상 = "브랜치·diff 기준"의 **변경 파일 목록** 중 이번 작업 파일만 (DONE.md "생성/수정된 파일 목록"과 대조, 짝 파일 포함)
       git add -- {고른 파일 목록}
       git status --porcelain 로 남은 변경이 있으면 목록을 출력하고 이번 작업과 무관한지 한 줄로 판정해 둔다
     git commit -m "$(COMMIT_MESSAGE.md의 '## 커밋 메시지' 섹션)"
     (로컬 커밋은 묻지 않는다 — 원격 작업만 9-5에서 확인한다)

9-5. PR/MR 대상 확정 및 브랜치 푸시
     "브랜치·diff 기준"의 MR_SOURCE / MR_TARGET 사용 (sed 재추론 금지).

     [대상 검사 — 하나라도 해당하면 PR/MR 안내를 만들지 않고 [PAUSE]]
     - MR_TARGET이 빈 값 (--here·임시 작업·이미 이슈 브랜치에서 시작해 PARENT 판정 불가)
     - MR_TARGET == MR_SOURCE
     - MR_TARGET이 main / master
     → "PR/MR 대상 브랜치를 확인해주세요. (source: {MR_SOURCE}, 현재 target: {MR_TARGET 또는 '없음'})
        병합할 브랜치명을 입력해주세요."
     → 입력값을 MR_TARGET으로 사용. TRACK=defect면 STATUS의 `PARENT_BRANCH=`에 기록 (다음부터 묻지 않음)
       (main/master를 명시적으로 입력한 경우에만 main/master 대상 허용)

     [PAUSE] push는 원격(외부 공개) 작업이다 — 실행 전 확인 (커밋은 9-4에서 묻지 않고 이미 완료):
       "{MR_SOURCE} → origin push 후 {MR_TARGET} 대상 PR/MR 안내를 출력할까요? (1. 예 / 2. 아니오=로컬 커밋까지만)"
       '2'·'아니오' → push·안내(9-6)를 건너뛰고 9-7 대신 "로컬 커밋 완료 — push는 지시 시" 출력 후 종료.

     [push]
     git push -u origin {MR_SOURCE}

     [target 원격 존재 확인]
     git ls-remote --heads origin {MR_TARGET} 출력이 없으면:
     - TRACK=sprint (target=ISSUE_BRANCH): 로컬 ISSUE_BRANCH를 먼저 push → `git push -u origin {ISSUE_BRANCH}`
       (원격에 없는 신규 이슈 베이스 브랜치라 덮어쓸 대상이 없음)
     - TRACK=defect (target=PARENT_BRANCH): [PAUSE] "PR/MR 대상 {MR_TARGET}이(가) 원격에 없습니다. 브랜치명을 확인해주세요."

     BASE_BRANCH = MR_TARGET   (9-6 이하 기존 변수명 호환)

9-6. PR/MR 생성 안내 (호스팅 중립)

     > 자동 생성하지 않는다. 호스팅 서비스(GitHub/GitLab/Bitbucket 등)와 무관하게
     > 제목·본문 초안만 출력하고, 생성과 머지는 사람이 한다.
     > ⚠️ git push 출력에 뜨는 호스팅 링크는 target이 기본 브랜치(main/master)로 잡힌다 — 그 링크로 만들지 말고
     >   아래 Source/Target을 직접 지정한다.

     다음 변수를 먼저 준비:
       CURRENT_BRANCH = MR_SOURCE (9-5)
       BASE_BRANCH = MR_TARGET (9-5)
       PR_TITLE="fix: #{이슈번호} {목표 요약} - {CURRENT_SPRINT}"
       (이슈번호/요약은 GOAL.md 또는 COMMIT_MESSAGE.md에서 추출; 이슈번호가 없으면 "fix: {DONE.md 한줄 요약} - {CURRENT_SPRINT}")

     안내 출력:
       ─────────────────────────────────────────────
       PR/MR 생성 안내

       Source branch : {CURRENT_BRANCH}
       Target branch : {BASE_BRANCH}
       Title         : {PR_TITLE}

       Description 본문 (복사하여 사용):

       ## 변경 사항
       (DONE.md 완료된 기능 목록)

       ## 테스트 완료 항목
       - 빌드 성공 (harness_config.py run build)
       - 테스트 통과 (harness_config.py run test — 해당 시)
       - 수동 테스트 통과

       ## Tech Debt
       (TODO 주석, OUT_OF_SCOPE.md)

       ## 리뷰 포인트
       (주의 깊게 봐야 할 파일·구간)
       ─────────────────────────────────────────────

9-7. [PAUSE]
     "브랜치가 push 되었습니다: {현재 브랜치}
      위 안내에 따라 PR/MR을 생성하고
      머지 완료 후 '머지완료'를 입력해주세요."

9-8. '머지완료' 입력 시
     {STATUS_FILE} 업데이트:
     - 해당 스프린트 상태 → ✅ 완료
     - LAST_COMMIT, LAST_BRANCH 기록
     - PHASE=10

```

---

### PHASE 10 — 다음 Sprint 진행 (또는 Defect 완료)

```
TRACK 값에 따라 분기:

─── TRACK=defect ───────────────────────────────────────────

10-D. Defect 트랙 완료
      "✅ Defect 트랙 완료! (#ACTIVE_ISSUE)

       완료된 수정:
       - {DONE_FILE}의 ## 완료된 기능 목록

       이슈 트래커를 쓴다면 해당 이슈 상태를 직접 갱신하세요.

       프로덕션 배포가 필요하면:
       → .claude/agents/deploy-prod.md를 읽고 배포를 진행해줘."

      {STATUS_FILE} PHASE=10 으로 유지 (종료, 다음 스프린트 없음)

─── TRACK=sprint (또는 미지정) ──────────────────────────────

10-1. 전체 진행 현황 출력
      ✅ sprint-01 완료
      🔄 sprint-02 진행 예정
      ⬜ sprint-03 대기

10-2. DONE.md Tech Debt 중 다음 스프린트 영향 있는 것 알림

10-3. 남은 스프린트 없으면
      {STATUS_FILE}에 PHASE=10 유지 + `PIPELINE=mvp_done` 기록
      (모든 스프린트 완료 표식 — /next가 이 값을 보고 "MVP 완료" 분기로 라우팅한다)

      [최종 PR/MR — 이슈 브랜치 → 상위 브랜치]
      스프린트 PR/MR은 ISSUE_BRANCH로만 모였으므로, ISSUE_BRANCH → PARENT_BRANCH PR/MR이 남아 있다.
      - PARENT_BRANCH가 빈 값이거나 main/master이면 9-5와 같은 대상 질의를 먼저 한다.
      - 9-6 형식으로 source=ISSUE_BRANCH, target=PARENT_BRANCH 안내를 출력한다 (생성·병합은 사람이 한다).
        [PAUSE] "최종 PR/MR({ISSUE_BRANCH} → {PARENT_BRANCH})을 호스팅 화면에서 생성해주세요. 생성 후 '계속'을 입력하세요."

      "🎉 모든 스프린트 완료! MVP 달성" 출력 후 아래 경로 안내하고 종료:
      - 프로덕션 배포:
        '.claude/agents/deploy-prod.md를 읽고 배포를 진행해줘'
      - 신규 요구사항 반영(Re-plan):
        '.claude/agents/orchestrator.md와 {STATUS_FILE} 읽고 PHASE 11 실행해줘'
        (orchestrator PHASE 11이 plan.md·ROADMAP.md를 갱신한 뒤 PHASE=5로 재진입시킨다)
      - 현재 상태/다음 단계 재확인: /next

10-4. 다음 스프린트 있으면
      {STATUS_FILE} 업데이트:
      - CURRENT_SPRINT → 다음 스프린트
      - PHASE=5

      [PAUSE]
      "다음 {NEXT_SPRINT}를 시작하려면 아래 명령어를 실행하세요:

      '.claude/agents/planner.md와 {STATUS_FILE} 읽고
       {WORKSPACE_DIR}/sprints/{NEXT_SPRINT}/GOAL.md 작성해줘'"
```

---

## 이 에이전트의 금지 사항

- ❌ 새로운 기능 추가 (GOAL.md 범위 밖)
- ❌ 아키텍처 변경
- ❌ force push
- ❌ 검증 실패를 무시하고 다음 단계 진행
