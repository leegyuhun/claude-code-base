# Upgrade_loop.md — 하네스 → 루프 엔지니어링 전환 시공 지시서

> 대상: `claude-code-base` (YSR EMR / Delphi 2007 Claude Code 하네스 템플릿)
> 갱신: 2026-09-22 — 실제 템플릿 구조 조사 결과를 STEP 0에 주입한 버전
> 이 문서는 **읽는 사람이 아니라 시공하는 에이전트에게 주는 프롬프트**다.

---

# 0. 이 문서의 전제

이 템플릿은 이미 **상태기계 + 역할분리 + 피드백 문서**를 갖춘 성숙한 하네스다.
빠진 것은 루프의 몸통이 아니라 **루프를 스스로 돌리는 세 부품**뿐이다.

```
있는 것 (건드리지 않는다)          없는 것 (이번에 만든다)
─────────────────────────────    ─────────────────────────────
PHASE 1~11 상태기계               자동 재진입 트리거 (Stop 훅)
STATUS.md 외부 상태 파일          외부 이터레이션 카운터 / 벽시계 상한
FEEDBACK.md 반려 경로             헛돌기(동일 실패 반복) 감지
검증 계약 (GOAL.md)               빠른 게이트 (PostToolUse)
생성자/검증자 subagent 분리       실패 시도 누적 이력
PreToolUse 가드 3종               PreCompact 상태 보존
```

따라서 이 작업의 성격은 **"새 루프 발명"이 아니라 "이미 있는 사이클을 사람 손 없이 잇기"**다.
새 개념을 도입하기 전에, 기존 PHASE 전이를 그대로 쓸 수 없는지 먼저 따져라.

---

# 1. 역할

너는 Claude Code 하네스 템플릿을 루프 엔지니어링 층까지 끌어올리는 **시공자**다.
감사가 아니라 실제 파일을 만들고 고치는 작업을 한다.

---

# 2. 불변 규칙 (위반 시 작업 중단)

- **기존 하네스를 대체하지 않는다.** 루프는 하네스 위에 얹는 층이다.
  기존 훅·권한 설정·PHASE 번호 체계·CLAUDE.md 규칙 중 무엇 하나라도 지우거나
  의미를 바꾸려면 먼저 이유를 보고하고 승인을 받는다.
- **모든 변경은 파일 단위 diff로 제시한다.** "이렇게 하면 좋습니다" 서술 금지.
- **종료 조건은 반드시 외부에서 검사 가능해야 한다.**
  모델이 스스로 "완료"를 선언하는 방식은 최종 종료 조건으로 채택하지 않는다.
  (이 템플릿의 `verification-before-completion` 스킬은 *프롬프트 수준* 강제다.
   루프의 종료 조건은 그것과 별개로 **훅에서 실행되는 명령의 종료 코드**여야 한다.)
- **새 의존성 추가 전에 기존 스택으로 가능한지 먼저 검토한다.**
  현재 스택: Windows / PowerShell / Git Bash / python3 / msbuild(Delphi 2007) / git / curl.
  Node는 MCP 실행용으로만 쓰인다 — 검증기를 Node에 얹지 마라.
- **CP949 규칙은 루프보다 상위다.** `.claude/rules/encoding-critical.md`의 금지 항목은
  훅 스크립트가 자동으로 수행하는 동작에도 그대로 적용된다.
  루프가 `.pas`/`.dfm`을 자동 수정하게 만들지 마라.
- **9장 루프 금지 구역**에 나열된 지점은 어떤 이유로도 자동화하지 않는다.

---

# 3. 입력 (실제 경로 — 직접 읽어라)

```
.claude/settings.json                    ← 권한만 있음. hooks 키 없음 (중요)
.claude/settings.local.json.sample       ← 현재 훅 3종이 여기에만 배선돼 있음 (중요)
.claude/hooks/pretooluse-bash-guard.sh   ← 유일한 훅 스크립트
.githooks/commit-msg                     ← git hook (Claude 훅 아님)
.claude/agents/{orchestrator,planner,implementer,validator,commit-writer,deploy-prod}.md
.claude/commands/{prd,sprint-dev,next,status,rollback,sprint-log,debt,branch,resolve}.md
.claude/rules/{active-issue,dev-process,sprint-workflow,coding-principles,
               encoding-critical,delphi2007-patterns,pitfalls-index}.md
.claude/skills/{verification-before-completion,subagent-driven-development,
                systematic-debugging,requesting-code-review,writing-plans,
                commit-format,redmine}/SKILL.md
.claude/templates/{goal-format,prd-format}.md
.claude/scripts/{parse_dproj,gen_index}.py
build.bat / run_tests.bat / setup_claude.bat
docs/{프로세스,구조,STATUS,PRD}.md
```

---

# STEP 0 — 현황 인벤토리 (조사 완료본 — 재조사하지 말고 **검증**하라)

아래 표는 2026-09-22 기준 실측이다.
**네 첫 작업은 이 표를 다시 만드는 게 아니라, 각 행이 지금도 사실인지 확인하고 틀린 줄만 고치는 것이다.**
이후 모든 설계는 이 표를 근거로 한다. 표에 없는 사실을 근거로 설계하려면 먼저 표에 추가하라.

## 0-A. 훅 인벤토리

| 이벤트 | 배선 위치 | 매처 | 동작 | 형상관리 |
|---|---|---|---|---|
| PreToolUse | `settings.local.json.sample` | `Write` | `.pas`/`.dfm` 차단, exit 2 | ❌ local은 .gitignore |
| PreToolUse | `settings.local.json.sample` | `Edit` | `.pas`/`.dfm` 차단, exit 2 | ❌ |
| PreToolUse | `settings.local.json.sample` | `Bash` | `pretooluse-bash-guard.sh` 6규칙 | 스크립트 ✅ / 배선 ❌ |
| PostToolUse | **없음** | — | — | — |
| Stop | **없음** | — | — | — |
| SubagentStop | **없음** | — | — | — |
| PreCompact | **없음** | — | — | — |
| SessionStart | **없음** | — | — | — |
| (git) commit-msg | `.githooks/commit-msg` | — | 타입 접두사 강제 | ✅ |

**bash-guard 6규칙**: `cd && ` 체이닝 / `push master` / `push Release` / force push / `reset --hard` /
브랜치 명명 규칙(`_#NNN` · `_sprint-NN` · `_hotfix_xxx` 3패턴만 허용).

> ⚠️ **1순위 발견**: 형상관리되는 `settings.json`에는 `hooks` 키가 아예 없다.
> 훅은 `setup_claude.bat`이 `.sample` → `settings.local.json`으로 복사·머지할 때만 살아나며,
> `settings.local.json`은 `.gitignore` 대상이다.
> 즉 **현재 훅은 팀 전체에 보장되지 않는다.** 루프 훅을 어디에 배선할지는
> 이 문제를 먼저 결정해야 정해진다 → 10장 열린 질문 Q1.

## 0-B. 실행 가능한 검증 명령

| 명령 | 실체 | 이 레포에서 동작? | 소요 |
|---|---|---|---|
| `build.bat [debug/release]` | `rsvars.bat` + `msbuild /t:Build` | ❌ `_D7/FwChart.dproj` 없음 | 적용 레포 기준 수십초~수분 (미실측) |
| `set DPROJ=... && build.bat debug` | validator·verification 스킬이 쓰는 실제 형태 | 적용 레포에서만 | 상동 |
| `run_tests.bat` | `TestRunner.dproj` 빌드 + `Output/Debug/TestRunner.exe` | ❌ `.dproj` 없음, `Tests/Source/` 비어 있음(.gitkeep만) | — |
| `python .claude/scripts/parse_dproj.py` | .dproj XML 파서 | ✅ (입력 .dproj 필요) | 초 단위 |
| `python .claude/scripts/gen_index.py` | 프로젝트 카드 인덱서 | ✅ | 초 단위 |
| `.githooks/commit-msg` | 커밋 메시지 형식 | ✅ | 즉시 |
| lint / 정적분석 / 타입체크 단독 | **존재하지 않음** | — | — |

> ⚠️ **2순위 발견**: 이 레포는 **빌드할 코드가 없는 배포용 템플릿**이다.
> `_D7/` 디렉터리도 `rsvars.bat` 경로도 이 레포에 없다.
> 따라서 검증기는 **두 층**으로 분리해서 설계해야 한다 → STEP 1.

## 0-C. 커버리지 추정과 근거

| 영역 | 자동 커버리지 | 근거 |
|---|---|---|
| 문법 / 타입 / 링크 | **높음** | Delphi 컴파일이 곧 타입체크. `build.bat` 0 error가 강한 신호 |
| 유닛 등록 누락 | 중간 | validator 7-1.5 `.dpr` 등록 검사 — 단 **프롬프트 지시일 뿐 스크립트 아님** |
| 인코딩 손상 | **0%** | CP949 규칙은 전부 *사전 차단*(PreToolUse)이며 *사후 검증*이 없다 |
| 단위 테스트 | **0%** | `Tests/Source/` 비어 있음. `dev-process.md` 5장의 "단위 테스트 ✅ 자동"은 문서상 주장이며 현실과 불일치 |
| 런타임 / UI 동작 | **0%** | 전량 PHASE 8 수동 테스트 의존 |
| 검증 계약 충족 | 0% (기계) | GOAL.md 체크박스는 Validator가 **판단해서** 채운다. 파싱 가능한 형식이지만 채점자가 모델이다 |

**"통과했는데 실제로는 미완성"이 되는 구멍 (반드시 STEP 1에서 메워라):**
1. 빌드 0 error인데 런타임 Access Violation — 스모크 검증 없음
2. `.pas`만 고치고 `.dfm` 동기화 누락 — 컴파일은 통과
3. Edit 도구가 CP949 한글 바이트를 깨뜨렸는데 컴파일은 통과 (주석이므로)
4. GOAL.md 검증 계약 문구가 "정상 동작" 수준이면 채점 자체가 불가능
5. Validator가 체크박스를 채웠는지 Implementer가 채웠는지 사후 구분 불가

## 0-D. 세션 밖 상태 기록 수단

| 수단 | 경로 | 누가 쓰는가 | 루프 관점 평가 |
|---|---|---|---|
| 활성 이슈 포인터 | `.claude/ACTIVE_ISSUE` | /prd, orchestrator | ✅ 훅이 읽을 진입점으로 그대로 사용 |
| 파이프라인 상태 | `workspace/{ACTIVE_ISSUE}/STATUS.md` | 전 에이전트 | ✅ PHASE/TRACK/CURRENT_SPRINT/PIPELINE 보유 |
| 구현 계약 | `sprints/{SPRINT}/GOAL.md` | Planner 작성 / Validator 채점 | ✅ 체크박스 파싱 가능 |
| 반려 사유 | `FEEDBACK.md` | Validator → Implementer | ⚠️ **최신 1회분만. 덮어쓴다 → 반복 실패 감지 불가** |
| 완료 보고 | `DONE.md` / `CHANGELOG.md` | Validator | 사후 기록 |
| 범위 외 / 부채 | `OUT_OF_SCOPE.md` / `TECH_DEBT.md` | Implementer / Validator | 사후 기록 |
| 커밋 메시지 | `COMMIT_MESSAGE.md` | commit-writer | — |
| 브랜치명 | git | 전체 | 이슈번호 폴백 경로 |

**결론**: 상태 파일은 풍부하다. 빠진 것은 정확히 셋 —
**(a) 이터레이션 카운터 (b) 벽시계 시작 시각 (c) 실패 시도 누적 이력.**

## 0-E. 사람이 개입해야만 진행되는 지점 전수 (= 루프가 먹을 후보)

| # | 위치 | 내용 | 흡수 판정 |
|---|---|---|---|
| 1 | `/prd` Phase 0 | 임시 ID 입력 | △ 인자 있으면 생략 가능 |
| 2 | `/prd` | 브랜치 생성 선택 | △ 기본값 [1] 고정 가능 |
| 3 | `/prd` | TRACK 확정 | ✅ 판정 기준이 이미 표로 존재(`sprint-workflow.md`) → 기계화 가능 |
| 4 | Orchestrator PHASE 3 | plan.md 검토 | ❌ 설계 승인은 사람 몫 |
| 5 | Orchestrator PHASE 4.5 | 초기화 / CLAUDE.md | △ 1회성 |
| 6 | sprint-dev 3단계 | AUTO_RUN 6조건 미충족 시 `'실행'` 대기 | ✅ **이 레포에서 가장 성숙한 루프 씨앗 — 이미 절반 자동화됨** |
| 7 | sprint-dev 4단계 | BLOCKED 시 PAUSE | ❌ 유지 |
| 8 | sprint-dev 5.5 | 함정 회고 y/n/e | △ 0건이면 자동 통과 중 |
| 9 | Validator 7-2 | 빌드 3회 실패 시 PAUSE | ✅ 카운터를 외부화하면 그대로 루프 |
| 10 | Validator 7-6 | FEEDBACK.md 작성 → `PHASE=6` 리셋 → **사람이 명령어 복붙** | ✅✅ **루프의 1차 타깃** |
| 11 | Validator PHASE 8 | 수동 UI 테스트 | ❌ **절대 금지** (9장) |
| 12 | Validator 8-6 | `'수정 필요'` → PHASE=7 재시도 | ✅ 10번과 동일 사이클 |
| 13 | Validator 9-6 | GitLab 라벨 인터뷰 | △ 1회 후 캐시됨 |
| 14 | Validator 9-7 | `'머지완료'` 입력 | ❌ 외부 시스템 상태 |
| 15 | Validator 10-4 | 다음 스프린트 명령어 복붙 | ✅ 2차 타깃 |

## 0-F. 이미 존재하는 "소프트 루프" (자동 재진입만 없는 상태)

```
L1  Validator 7-2   빌드 실패 → 자체 수정 → 재시도        상한 3회 (프롬프트 텍스트)
L2  Validator 7-6   FEEDBACK.md → PHASE=6 → Implementer   상한 없음, 사람이 복붙으로 이음
    → sprint-dev 1단계 FEEDBACK 재진입 → 5단계 → PHASE=7  ← 완결된 사이클
L3  sprint-dev S2/S3 리뷰어 불통과 → 수정 → 재리뷰        "통과까지 반복" — 상한 없음
L4  Validator 8-6   '수정 필요' → PHASE=7 재시도           상한 없음
L5  sprint-dev 4단계 Implementer 오류 3회 → BLOCKED        상한 3회 (프롬프트 텍스트)
```

> ⚠️ **3순위 발견**: L1·L5의 "3회" 상한은 **모델이 스스로 세는 숫자**다.
> 파일로 기록되지 않으므로 컴팩션·세션 재시작 후 카운터가 0으로 돌아간다.
> L2·L3·L4에는 상한 자체가 없다. **무한 루프가 이미 문서상 가능하다.**
> 루프 층을 얹기 전에, 얹지 않더라도, 이 카운터부터 외부화해야 한다.

## 0-G. 이 레포 고유 제약 (설계 입력값)

- **OS**: Windows 11. 훅은 Git Bash(`bash .claude/hooks/*.sh`)로 실행된다.
  `pretooluse-bash-guard.sh`가 이미 이 방식이므로 전제는 성립.
- **python 명령명**: 기존 훅은 `python3`를 쓴다. Windows에 `python3`만 있고 `python`만 있는 환경이
  섞일 수 있다 → 새 스크립트는 **인터프리터 탐색을 한 곳에 모아라**.
- **경로 구분자**: 훅 스크립트 안에서 `/e/Git_leegh/...`(bash)와 `E:\Git_leegh\...`(bat)가 섞인다.
- **Delphi에는 린터가 없다.** 빠른 게이트를 "린트"로 채울 수 없다 → STEP 3 대체안 참조.
- **`docs/구조.md`가 낡았다.** `workspace/{ACTIVE_ISSUE}/` 구조 도입 이전 버전(루트 `sprints/` 기준)이다.
  루프 층 문서화 시 함께 고쳐라.

---

# STEP 1 — 종료 조건 설계 (가장 먼저, 가장 중요)

검증기가 곧 루프의 품질 상한이다. **검증기 설계 없이 Stop 훅부터 만들지 마라.**

## 1-1. 두 층으로 나눠 설계한다 (0-B 발견 때문에 필수)

```
층 A — 하네스 무결성 검증 (이 레포에서 지금 실행 가능)
  대상: .claude/ 자체. 훅 스크립트 문법, settings JSON 유효성,
        에이전트/커맨드 간 상호 참조 경로 깨짐, 템플릿 필수 섹션 존재
  성격: 빠름(수 초), 환경 비의존, 이 레포의 회귀 방지선
  → 이 레포에서 루프를 검수(STEP 7)할 때 쓰는 검증기이기도 하다

층 B — 적용 대상 Delphi 레포 검증 (이 레포에는 대상이 없음)
  대상: build.bat / run_tests.bat / GOAL.md 검증 계약
  성격: 느림, Windows+RAD Studio 의존, 부재 가능
```

**층 B 부재를 "검증 실패"로 보고하면 루프가 영원히 헛돈다.**
`_D7/` 없음 · `rsvars.bat` 없음 · `Tests/Source/` 비어 있음은 전부 **"검증기 부재"**이며
`exit 2`(재시도 유도)가 아니라 **`exit 0` + stderr 경고 + 사람 호출**로 처리해야 한다.
이 구분을 스크립트 최상단에 함수로 못박아라.

## 1-2. 게이트 배치

**[빠른 게이트] — PostToolUse, 목표 200ms 이내**

| 검사 | 근거 | 층 |
|---|---|---|
| 변경된 `.pas`/`.dfm`이 CP949로 디코딩되는가 | 0-C 구멍 ③ — 현재 커버리지 0% | B |
| U+FFFD / mojibake 패턴 유입 여부 | 상동 | B |
| `.pas` 수정 시 짝 `.dfm` 동기화 필요 여부 경고 | 0-C 구멍 ② | B |
| 신규 `.pas`의 `.dpr`/`.dproj` 등록 | validator 7-1.5를 스크립트화 | B |
| 날짜 하드코딩 grep | validator 7-1.5 | B |
| `settings*.json` / `.mcp.json.example` JSON 파싱 | 층 A 회귀 방지 | A |
| `.claude/hooks/*.sh` `bash -n` 문법 검사 | 훅이 깨지면 루프 전체 정지 | A |

**[느린 게이트] — Stop, 수십 초~**

| 검사 | 명령 | 층 |
|---|---|---|
| 컴파일 | `set DPROJ={탐지경로} && build.bat debug` → 0 error | B |
| 단위 테스트 | `run_tests.bat` — **`Tests/Source/*.pas`가 1개 이상일 때만** | B |
| 검증 계약 미충족 | `GOAL.md`의 `## 검증 계약` 섹션에 `- [ ]` 잔존 0건 | B |
| STATUS 정합성 | `PHASE` 값이 정의된 집합 내 / `CURRENT_SPRINT` 디렉터리 존재 | A/B |
| 하네스 링크 무결성 | 에이전트·커맨드가 참조하는 `.claude/**` 경로 전부 존재 | A |

## 1-3. 구멍 메우기 (0-C 목록에 대한 최소 추가 검증)

각각에 대해 **채택 / 기각 + 근거**를 적어라. 전부 채택할 필요는 없다.

1. 런타임 AV → EXE 스모크(실행 후 N초 생존).
   ⚠️ YSR EMR은 DB 접속이 전제라 단독 실행이 안 될 가능성이 높다. **실현 가능성을 먼저 확인하고,
   불가하면 "메울 수 없는 구멍"으로 8장 출력형식 ⑤에 명시**하라. 억지로 만들지 마라.
2. `.dfm` 동기화 → 빠른 게이트로 커버 가능.
3. CP949 손상 → 빠른 게이트로 커버 가능. **이게 이번 작업의 최대 실익일 수 있다.**
4. 검증 계약 문구 품질 → `goal-format.md`의 자기검증 체크리스트를 휴리스틱 스크립트로.
   ("정상 동작", "잘 됨" 같은 비측정 문구 탐지 → Planner 단계에서 경고)
5. 체크박스 채점 주체 → 구조적으로 사후 판별 불가.
   대안: Validator가 `[x]` 전환 시 **근거 한 줄(파일:줄 또는 명령 출력)** 동반을 형식으로 강제.

**산출물**: 검증 명령 목록 + 게이트 배치 + 각각의 실측 실행시간(추정치 금지, 실제로 돌려서 재라).

---

# STEP 2 — 긴 루프 구현 (Stop 훅)

## 2-1. 필수 동작 순서

```
1) stop_hook_active == true  → 즉시 exit 0
   (무한루프 방지. 이 분기 없으면 실패한 구현이다)
2) 진입점 상태 해석
   .claude/ACTIVE_ISSUE → 없으면 git 브랜치 #(\d+) 폴백 → 둘 다 실패면 exit 0 (루프 대상 아님)
   workspace/{ACTIVE_ISSUE}/STATUS.md 에서 PHASE / TRACK / CURRENT_SPRINT 파싱
3) PHASE 게이팅 (아래 2-2)
4) 카운터 로드 → 상한 초과 시 exit 0 + 실패로 기록 (STEP 6)
5) 느린 게이트 실행
6) 실패 → exit 2 + stderr에 "무엇이 왜 실패했는지 + 다음에 볼 곳"
7) 통과 → 카운터 리셋 + exit 0
```

## 2-2. PHASE별 게이팅 (이 템플릿 특화 — 반드시 구현)

| PHASE | Stop 훅 동작 | 이유 |
|---|---|---|
| 1~5 | exit 0 (통과) | 계획 단계. 검증할 코드가 없다 |
| 6 | 빌드 게이트 → 실패 시 exit 2 | Implementer 종료 시점 |
| 7 | 검증 계약 미체크 잔존 시 exit 2 | Validator 자동검증 시점 |
| **8** | **무조건 exit 0** | **사람의 수동 UI 테스트 대기 상태. 여기서 막으면 사용자가 갇힌다** |
| 9~10 | exit 0 | 커밋/MR/전환 단계. 외부 시스템 대기 |
| 11 | exit 0 | Re-plan |

> PHASE 8을 막지 않는 것은 선택이 아니라 **안전 요구사항**이다. 하드코딩하고 주석으로 이유를 남겨라.

## 2-3. 상한 (두 축 모두 — 한 축만 걸면 미완성)

```
이터레이션 상한 : 기본 3 (현행 validator 7-2 / sprint-dev 4단계의 "3회"와 맞춤)
벽시계 상한     : 기본값은 STEP 1에서 실측한 빌드 1회 시간 × (상한+1) × 안전계수
                  추정치로 적지 말고 실측 후 채워라
둘 중 하나라도 초과 → 탈출 (AND 아님)
```

카운터 파일 위치 제안: `workspace/{ACTIVE_ISSUE}/.loop/counter.json`

```json
{
  "phase": 7,
  "sprint": "sprint-01",
  "attempts": 2,
  "first_attempt_at": "2026-09-22T14:03:11+09:00",
  "last_signature": "sha1:...",
  "halted": false
}
```

**PHASE나 CURRENT_SPRINT가 바뀌면 카운터를 리셋**한다 (다른 작업의 실패를 이어 세지 않는다).

## 2-4. 검증 실패와 스크립트 오류의 구분 (필수)

```
exit 2  = 검증기가 정상 동작했고 결과가 FAIL     → 루프 계속
exit 0  = 통과 / 루프 대상 아님 / 검증기 부재    → 루프 정지
exit 1  = 훅 스크립트 자체 버그                  → 경고만 표시, 흐름 유지
```

아래는 **절대 exit 2로 처리하지 마라** (전부 "검증기 부재"다):
`rsvars.bat` 없음 · `.dproj` 탐지 실패 · `Tests/Source/` 비어 있음 · `python` 없음 ·
`STATUS.md` 없음 · `ACTIVE_ISSUE` 없음.

## 2-5. stderr 메시지 규격

stderr 내용이 **다음 턴의 지시**가 된다. 에러 로그 원문 덤프 금지. 아래 형식으로 가공하라.

```
[loop-gate] PHASE 7 검증 실패 (시도 2/3, 경과 6분)

실패: 컴파일
  FwChart\Forms\TreatForm.pas(412) E2003 Undeclared identifier: 'GetPatientNo'

다음에 볼 곳:
  1. TreatForm.pas uses 절에 해당 유닛이 있는지
  2. .claude/refs/pitfalls.md 카테고리 B (#3 #4 #7)
  3. 수정 전 .claude/skills/systematic-debugging/SKILL.md Phase 1부터

재검증: set DPROJ=FwChart\FwChart.dproj && build.bat debug

직전 시도와 동일한 실패면 즉시 중단하고 사람을 부를 것.
```

---

# STEP 3 — 짧은 루프 구현 (PostToolUse)

- 매처: `Edit|Write|MultiEdit` (파일 수정 계열).
- **Delphi 2007에는 린터도 단독 타입체커도 없다.** 빠른 게이트를 린트로 채울 수 없으므로
  STEP 1-2의 **인코딩·구조 검사가 린트의 대체재**다. 이 점을 설계 근거로 명시하라.
- 실행시간이 긴 명령을 여기 넣지 마라. 툴 호출마다 비용이 곱해진다. **컴파일은 절대 금지.**
- 이 훅은 기존 PreToolUse CP949 차단과 **역할이 다르다**:
  PreToolUse = 사전 차단(도구 자체를 막음) / PostToolUse = 사후 검증(손상 탐지).
  둘을 합치려 하지 마라.
- 출력은 경고 위주로. 여기서 exit 2를 남발하면 편집이 매번 멈춘다.
  **exit 2는 "인코딩 손상 실제 탐지"처럼 되돌리지 않으면 안 되는 경우로 한정**하라.

---

# STEP 4 — 생성자와 검증자 분리

## 4-1. 이미 되어 있는 것 (재발명 금지)

```
sprint-dev 4단계 : Implementer → Spec Reviewer → Code Quality Reviewer (3-STEP, 직렬)
Validator 7-3    : Implementer 자체 선언이 아닌 독립 검증으로 체크박스 전환
Validator 7-4    : code-reviewer subagent를 BASE_SHA..HEAD_SHA diff로 디스패치
sprint-workflow  : "Implementer는 GOAL.md 체크박스 수정 금지"
```

**원본 STEP 4의 요구사항은 이 템플릿에서 이미 충족돼 있다.** 새 분리 구조를 만들지 마라.

## 4-2. 그럼에도 남은 위반 2건 (반드시 판단하고 결론을 적어라)

1. **Validator 7-6이 "High 이하 코드 리뷰 지적이면 직접 수정 후 재검증"한다.**
   → 검증자가 수정 권한을 가진다. 원본 원칙("검증자에게 수정 권한을 주지 않는다") 위반.
   **유지 / 폐지 / 조건부 허용 중 하나를 골라 근거와 함께 적어라.**
   (참고: 폐지하면 사소한 수정도 FEEDBACK 왕복이 되어 이터레이션이 늘어난다. 트레이드오프다.)
2. **sprint-dev STEP 2/STEP 3 리뷰 루프에 상한이 없다** ("통과까지 반복").
   → 여기에 카운터를 걸어라. Stop 훅은 메인 세션 종료 시에만 발동하므로
   **subagent 리뷰 왕복은 Stop 훅이 못 잡는다.** 프롬프트 수준 상한 + 파일 카운터 병행이 필요하다.

## 4-3. 검증 subagent 입력 제한

code-reviewer는 현재 `BASE_SHA..HEAD_SHA` diff만 받는다(생성 과정의 추론을 받지 않음) — **올바르다. 유지.**
새로 추가하는 검증 subagent도 동일 원칙을 따르게 하라: **산출물만, 추론 과정은 금지.**

---

# STEP 5 — 컨텍스트 위생

## 5-1. 진행 상태 파일 — 이미 있다

`workspace/{ACTIVE_ISSUE}/STATUS.md`가 목표·완료·남은 것을 이미 담는다. **새 파일로 대체하지 마라.**
누락된 축만 보강한다:

| 필요 | 현재 | 조치 |
|---|---|---|
| 목표 | GOAL.md | — |
| 완료된 것 | STATUS 진행률 + GOAL 체크박스 | — |
| 남은 것 | 상동 | — |
| **실패한 시도와 이유** | **FEEDBACK.md가 덮어써서 소실** | **신규: 누적 로그** |
| 이터레이션/경과 | 없음 | 신규: counter.json |

## 5-2. 실패 이력 — 한 줄 압축 (전체 로그 누적 금지)

전체 로그를 쌓으면 모델이 같은 오답에 고착된다.
제안 경로 `workspace/{ACTIVE_ISSUE}/.loop/attempts.log`, 한 줄 형식:

```
[sprint-01][P7][iter 2][2026-09-22 14:03] BUILD FAIL E2003 TreatForm.pas:412 → uses 절 추가 시도
[sprint-01][P7][iter 3][2026-09-22 14:11] BUILD FAIL E2003 TreatForm.pas:412 → 동일 실패, 중단
```

**FEEDBACK.md는 최신본 유지(현행 그대로), 이력은 attempts.log** — 역할을 섞지 마라.

## 5-3. PreCompact 보존

컴팩션 시 `STATUS.md` · `GOAL.md` · `attempts.log` · `counter.json` 경로가 살아남게 한다.
**파일 내용을 훅이 통째로 뱉지 마라** — 그 자체가 컨텍스트를 다시 채운다.
경로와 한 줄 요약만 남기고, 다음 턴이 필요할 때 읽게 하라.

## 5-4. 이터레이션 간 전달물

넘어가는 것은 **구조화된 상태(STATUS/counter/attempts)여야지 대화 로그여서는 안 된다.**
Stop 훅 stderr도 "로그 붙여넣기"가 아니라 **행동 지시**여야 한다 (STEP 2-5 규격).

---

# STEP 6 — 탈출로

## 6-1. 상한 도달 시

```
1. 부분 산출물 보존       — 커밋하지 않는다. 브랜치 그대로 둔다 (Validator PHASE 9가 커밋 주체)
2. STATUS.md 기록          — LOOP=halted / HALT_REASON={사유} / HALT_AT={시각}
                             PHASE 값은 건드리지 않는다 (사람이 판단할 재료를 남긴다)
3. attempts.log 요약 출력  — 최근 N줄
4. 사람 호출               — /next 가 halted를 인지하고 안내하도록 next.md에 분기 추가
5. exit 0                  — 막지 않는다. 갇히게 하지 마라
```

## 6-2. 헛돌기 감지 (상한보다 먼저 걸린다)

실패 시그니처 = `(게이트종류, 에러코드, 파일, 줄번호)` 해시.
**2회 연속 동일 시그니처면 상한(3회)을 기다리지 않고 즉시 중단**한다.
같은 자리에서 두 번 같은 방식으로 실패한 모델이 세 번째에 성공할 확률은 무시할 만하다.

## 6-3. 비용 상한

훅에서 토큰을 직접 볼 수 없다. **이터레이션 횟수 + 벽시계 시간을 토큰의 대리 지표로 쓴다.**
subagent를 디스패치하는 sprint-dev 4단계는 1 이터레이션당 비용이 크므로
**PHASE 6 루프의 상한을 PHASE 7보다 낮게 잡는 것을 검토**하라 (예: P6=2, P7=3).

---

# STEP 7 — 검수 (재현 절차와 결과를 반드시 보고)

이 레포에는 Delphi 빌드 대상이 없다(0-B). 따라서 검수는 **층 A로 하고, 층 B는 명시적으로 미검증 처리**하라.
없는 것을 검수했다고 쓰지 마라.

| # | 시나리오 | 재현 절차 | 기대 결과 |
|---|---|---|---|
| 1 | 검증 실패 시 종료 차단 | 층 A 검증기가 반드시 실패하도록 `settings.json`에 고의로 JSON 문법 오류 주입 → 턴 종료 | Stop 훅 exit 2, stderr에 행동 지시, 세션 계속 |
| 2 | `stop_hook_active` 분기 | 1번 상태 유지한 채 연속 종료 시도 | 2회차부터 즉시 통과, 무한루프 없음 |
| 3 | **검증기 부재 안전 실패** | `_D7/` 없는 현 상태 그대로 PHASE=6으로 두고 종료 | **exit 0** + stderr 경고. exit 2면 설계 실패 |
| 4 | 상한 도달 탈출 | counter.json의 `attempts`를 상한값으로 조작 후 종료 | exit 0 + `STATUS.md LOOP=halted` 기록 + 요약 출력 |
| 5 | 헛돌기 조기 중단 | 동일 시그니처 실패를 2회 발생 | 3회차 기다리지 않고 중단 |
| 6 | **PHASE 8 비차단** | STATUS.md PHASE=8로 두고 종료 | **무조건 exit 0** (사용자가 갇히지 않음) |
| 7 | 카운터 리셋 | 검증 통과 1회 후 counter.json 확인 | `attempts=0`, `halted=false` |
| 8 | PHASE 전환 시 리셋 | PHASE 6→7 전환 후 counter 확인 | 이전 PHASE 실패 횟수 미승계 |
| 9 | 빠른 게이트 CP949 탐지 | CP949 `.pas` 샘플을 UTF-8로 저장 → PostToolUse | 손상 탐지 및 경고/차단 |
| 10 | 기존 훅 회귀 | `git push -f` / `.pas`에 Write / `cd x && y` 시도 | **기존 3종 PreToolUse 가드 전부 그대로 동작** |

각 항목에 **재현 절차 / 실제 출력 / 판정**을 적어라. 미실행 항목은 "미검증"으로 남기고 이유를 쓴다.

---

# 8. 출력 형식

```
1) STEP 0 인벤토리 — 이 문서의 표를 검증한 결과. 틀린 줄만 정정 diff로
2) 변경 계획       — 새로 만들 파일 / 수정할 파일 / 건드리지 않을 파일 (부록 A 기준)
3) 파일별 전체 내용 또는 diff
4) 설치·검수 절차  — 형님이 그대로 따라할 수 있게 (Windows / PowerShell 기준 명령)
5) 알려진 한계     — 이 루프가 처리 못 하는 작업 유형 + 그때 사람이 뭘 해야 하는지
                     (특히 런타임/UI 검증 부재, 층 B 미검수 범위를 반드시 포함)
6) 남은 리스크 3개
7) 층 A / 층 B 검수 범위 — 무엇을 실제로 돌려봤고 무엇을 못 돌려봤는지 명시
```

---

# 9. 루프 금지 구역 (어떤 이유로도 자동화하지 않는다)

```
❌ PHASE 8 수동 UI 테스트를 루프가 통과 처리        — 런타임 검증이 0%인 상태에서 유일한 안전망
❌ 공용 유닛 자동 수정
   Common/ CommonBL/ CommonV7/ ComUnit/ PackageBL/  — 참조 프로젝트 다수, 파급 범위 확인 필수
❌ DB 스키마 DDL 자동 실행
❌ .pas/.dfm 에 Write 도구 사용                     — encoding-critical.md, 예외 없음
❌ 기존 한글 주석 수정/삭제                         — 깨져 보여도 원본 CP949 바이트
❌ master / Release 직접 push, force push, reset --hard  — bash-guard 6규칙 우회 금지
❌ 브랜치 명명 규칙 우회
❌ Implementer가 GOAL.md 체크박스 채우기            — 자기 채점 금지
❌ Redmine 상태 자동 Resolved 전이                  — /resolve 는 사람이 호출
❌ GitLab MR 자동 머지
❌ 상한 도달 시 "그래도 완료"로 STATUS 기록
```

---

# 10. 열린 질문 (STEP 0 검증 직후 형님께 물어라 — 설계가 갈린다)

```
Q1. 루프 훅을 settings.json(팀 공유, 형상관리)에 넣을 것인가,
    settings.local.json(개인)에 넣을 것인가?
    → 현재 훅 3종이 local에만 있어 팀 보장이 안 된다(0-A). 같이 옮길지도 함께 결정 필요.

Q2. 층 A(하네스 자체 검증기)를 이번 범위에 포함할 것인가?
    → 포함하지 않으면 이 레포에서는 루프를 검수할 방법이 없다(STEP 7).

Q3. 자동 루프 허용 범위를 sprint-dev의 AUTO_RUN 6조건과 동일하게 갈 것인가, 더 좁힐 것인가?
    → 이미 검증된 판정 기준을 재사용하는 쪽을 권한다. 새 기준을 만들면 두 개를 관리하게 된다.

Q4. 실제 적용 레포에서 build.bat 1회 소요 시간은?
    → 벽시계 상한의 유일한 설계 입력값. 실측 없이는 STEP 2-3을 채울 수 없다.

Q5. Validator가 "High 이하 지적을 직접 수정"하는 현행 규칙을 유지할 것인가? (STEP 4-2)

Q6. Tests/Source/ 에 DUnit 테스트를 실제로 채울 계획이 있는가?
    → 없다면 dev-process.md 5장의 "단위 테스트 ✅ 자동" 표기를 현실에 맞게 고쳐야 한다(0-C).
```

---

# 부록 A — 파일 배치 제안 (확정 아님. STEP 1 결론 후 조정하라)

**신규**
```
.claude/hooks/stop-loop-gate.sh          Stop 훅 진입점
.claude/hooks/posttooluse-fast-gate.sh   PostToolUse 진입점
.claude/hooks/precompact-preserve.sh     PreCompact (선택)
.claude/scripts/loop_state.py            ACTIVE_ISSUE/STATUS 파싱 · 카운터 · 시그니처 (공용)
.claude/scripts/gate_fast.py             인코딩 · dfm 동기화 · dpr 등록 · 날짜 하드코딩
.claude/scripts/gate_slow.py             빌드 호출 · GOAL 검증계약 파싱 · 테스트
.claude/scripts/gate_harness.py          층 A — 하네스 무결성
.claude/rules/loop-contract.md           루프 규약(상한·탈출·금지구역) 문서화
```

**런타임 산출 (커밋 대상 여부 결정 필요)**
```
workspace/{ACTIVE_ISSUE}/.loop/counter.json
workspace/{ACTIVE_ISSUE}/.loop/attempts.log
```

**수정**
```
.claude/settings.json              hooks 키 신설 (Q1 결론에 따름)
.claude/settings.local.json.sample 중복 배선 정리
.claude/commands/next.md           LOOP=halted 분기 추가
.claude/agents/validator.md        7-2/7-6 카운터를 외부 파일 기준으로 변경
.claude/commands/sprint-dev.md     4단계 리뷰 왕복 상한 명시 (STEP 4-2)
docs/STATUS.md                     LOOP / HALT_REASON 필드 추가
docs/프로세스.md                   루프 층 흐름 반영
docs/구조.md                       낡은 구조 갱신 (0-G)
.gitignore                         .loop/ 처리
```

**건드리지 않을 것**
```
.claude/rules/encoding-critical.md        CP949 규칙 원문
.claude/hooks/pretooluse-bash-guard.sh    6규칙 (배선 위치만 바뀔 수 있음)
.githooks/commit-msg
.claude/rules/delphi2007-patterns.md
.claude/refs/pitfalls.md                  (append는 기존 5.5단계 절차로만)
PHASE 1~11 번호 체계와 의미
```

---

# 부록 B — 설계 시 자주 틀리는 지점

1. **Stop 훅은 subagent 종료에 발동하지 않는다.** sprint-dev의 3-STEP 리뷰 왕복(L3)은
   Stop 훅으로 못 잡는다. SubagentStop을 쓰거나 프롬프트 상한 + 파일 카운터로 잡아라.
2. **PHASE=8에서 막으면 사용자가 갇힌다.** 수동 테스트 대기 중에는 종료를 허용해야 한다.
3. **환경 부재를 실패로 보고하면 루프가 영원히 헛돈다** (0-B, STEP 2-4).
4. **카운터를 모델에게 세게 하지 마라.** 현행 "3회"가 이미 그 실패 사례다(0-F).
5. **FEEDBACK.md에 이력을 쌓지 마라.** 최신 지시가 과거 실패 로그에 묻힌다. 역할을 나눠라.
6. **PostToolUse에 컴파일을 넣지 마라.** Delphi 빌드는 툴 호출당 곱해지면 사용 불가가 된다.
