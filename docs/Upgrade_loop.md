# Upgrade_loop.md — 루프 엔지니어링 시공 기록 + 잔여 작업

> 대상: `claude-code-base` (YSR EMR / Delphi 2007 Claude Code 하네스 템플릿)
> 갱신: 2026-09-22 — **4단계 시공 완료 후**
>
> 이전 버전은 "앞으로 만들 것"을 지시하는 프롬프트였다. 시공이 끝났으므로
> 이제 이 문서는 세 가지를 담는다:
>   (a) 현재 상태의 정확한 인벤토리 — 설계의 근거가 되는 사실
>   (b) 무엇을 채택하고 무엇을 버렸는지, 그 이유
>   (c) 남은 작업과 알려진 한계

---

# 0. 현재 상태 한눈에

```
있는 것                              위치
─────────────────────────────────    ────────────────────────────────────────
PHASE 1~11 상태기계                  workspace/{이슈}/STATUS.md
자동 재진입 트리거                   .claude/hooks/stop-loop-gate.py
외부 이터레이션 카운터               .claude/scripts/loop_state.py
벽시계 상한 (30분)                   loop_state.py WALL_CLOCK_LIMIT_SEC
헛돌기 감지 (동일 실패 2회)          loop_state.py REPEAT_LIMIT
빠른 게이트                          .claude/hooks/posttooluse-fast-gate.py
실패 시도 이력                       workspace/{이슈}/.loop/attempts.log
PreCompact 좌표 보존                 .claude/hooks/precompact-preserve.py
탈출로                               STATUS.md LOOP=halted + /next 0단계
층 A 검증기                          .claude/scripts/gate_harness.py
```

핵심 설계 결정 세 가지:

1. **검증기를 두 층으로 나눴다.** 이 레포에는 Delphi 빌드 대상이 없으므로(0-B),
   하네스 자체의 무결성(층 A)이 여기서 유일하게 성립하는 종료 조건이다.
2. **"검증기 부재"와 "검증 실패"를 구분한다.** `build.bat`·`.dproj`·`rsvars` 부재는
   `exit 0` + 경고다. 실패로 세면 루프가 영원히 헛돈다.
3. **PHASE 8은 절대 막지 않는다.** 수동 UI 테스트 대기 상태에서 막으면 사용자가
   빠져나갈 방법이 없다. 하드코딩된 안전 요구사항이다.

---

# STEP 0 — 인벤토리 (2026-09-22 시공 후 실측)

## 0-A. 훅 인벤토리

| 이벤트 | 매처 | 스크립트 | 형상관리 |
|---|---|---|---|
| PreToolUse | `Write\|Edit\|MultiEdit` | `pretooluse-cp949-guard.py` | ✅ settings.json |
| PreToolUse | `Bash` | `pretooluse-bash-guard.py` | ✅ |
| PostToolUse | `Bash\|Write\|Edit\|MultiEdit` | `posttooluse-fast-gate.py` | ✅ |
| Stop | (전체) | `stop-loop-gate.py` | ✅ |
| PreCompact | (전체) | `precompact-preserve.py` | ✅ |
| (git) commit-msg | — | `.githooks/commit-msg` | ✅ |

**시공 전과의 차이**: 훅 3종이 `settings.local.json.sample`에만 있었고 그 파일은
`.gitignore` 대상이었다 — 즉 팀 전체에 보장되지 않았다. `settings.json`으로 옮겼고,
`setup_claude.bat`에 `[3/5]` 마이그레이션을 넣어 기존 설치의 중복 배선을 제거한다.

**bash-guard 규칙 7개** (기존 6 + 1):
`cd && ` 체이닝 / `push master` / `push Release` / force push / `reset --hard` /
브랜치 명명(`_#NNN` · `_sprint-NN` · `_hotfix_xxx` · **`_harness_xxx`**).
마지막 패턴은 이번에 추가했다 — 기존 셋은 전부 제품 코드 작업 전제라
`.claude/` 자체를 고치는 작업에 붙일 이름이 없었다.

## 0-B. 실행 가능한 검증 명령

| 명령 | 이 레포에서 동작? | 소요 |
|---|---|---|
| `python .claude/scripts/gate_harness.py` | ✅ **층 A 검증기** | 1~2초 |
| `python .claude/scripts/loop_state.py status` | ✅ | 1초 |
| `build.bat [debug/release]` | ❌ `_D7/FwChart.dproj` 없음 | 적용 레포 기준 1분 미만 |
| `run_tests.bat` | ❌ `TestRunner.dproj` 없음, `Tests/Source/` 비어 있음 | — |
| `python .claude/scripts/parse_dproj.py` | ✅ (입력 필요) | 초 단위 |
| lint / 정적분석 / 타입체크 단독 | 없음 (Delphi 2007) | — |

**이 레포는 여전히 빌드할 코드가 없는 배포용 템플릿이다.** 층 B(Delphi 빌드)는
적용 레포에서만 검증된다 — 잔여 작업 참조.

## 0-C. 커버리지

| 영역 | 시공 전 | 시공 후 |
|---|---|---|
| 문법 / 타입 / 링크 | 높음 (컴파일) | 동일 + Stop 훅이 PHASE 6에서 강제 |
| **인코딩 손상** | **0%** | **사후 탐지 + exit 2 교정 요구** |
| 하네스 무결성 | 없음 | JSON·스크립트 문법·문서 참조·훅 경로 |
| 유닛 등록 누락 | 프롬프트 지시뿐 | 스크립트 경고 |
| `.dfm` 동기화 | 없음 | 컴포넌트 선언 변경 시 경고 |
| 검증 계약 충족 | 0% (기계) | Stop 훅이 `- [ ]` 잔여를 기계 판정 |
| 단위 테스트 | 0% | **여전히 0%** (`Tests/Source/` 비어 있음) |
| 런타임 / UI 동작 | 0% | **여전히 0%** (PHASE 8 수동 의존) |

**남은 구멍** (메우지 않기로 한 것 포함):
1. 빌드 통과인데 런타임 AV — EXE 스모크는 **미채택**. YSR EMR은 DB 접속이 전제라
   단독 실행이 성립하지 않는다. 억지로 만들면 거짓 신호만 늘어난다.
2. 검증 계약 문구가 "정상 동작" 수준이면 기계 판정 자체가 무의미 — 휴리스틱 검사 **미채택**.
   오탐이 많으면 Planner 단계에서 무시된다.
3. 체크박스를 누가 채웠는지 사후 구분 불가 — 구조적으로 불가능. Validator가
   근거를 동반하도록 프롬프트로만 강제한다.

## 0-D. 세션 밖 상태 기록

| 수단 | 경로 | 역할 |
|---|---|---|
| 활성 이슈 포인터 | `.claude/ACTIVE_ISSUE` | 모든 경로 해석의 시작점 |
| 파이프라인 상태 | `workspace/{이슈}/STATUS.md` | PHASE / TRACK / **LOOP / HALT_REASON** |
| 구현 계약 | `sprints/{N}/GOAL.md` | 검증 계약 체크박스 |
| 반려 사유 | `FEEDBACK.md` | **최신본만** (이력 아님) |
| **이터레이션 카운터** | `.loop/counter.json` | scope별 횟수·벽시계·실패 시그니처 |
| **실패 시도 이력** | `.loop/attempts.log` | 한 줄 압축 누적 |

FEEDBACK.md와 attempts.log의 역할 분리가 핵심이다. 전자에 이력을 쌓으면
최신 지시가 과거 로그에 묻힌다.

## 0-E. 사람 개입 지점 — 무엇이 자동화됐나

| 위치 | 시공 전 | 시공 후 |
|---|---|---|
| Validator 7-2 빌드 재시도 | 모델이 3회를 셈 | `--scope build` 파일 카운터 |
| Validator 7-6 FEEDBACK 왕복 | **상한 없음** | `--scope feedback` |
| Validator 8-6 수정 재시도 | **상한 없음** | `--scope manual` |
| sprint-dev 리뷰 왕복 | **"통과까지 반복"** | `--scope review:{항목}` |
| sprint-dev 4단계 오류 | 모델이 3회를 셈 | 동일 scope |
| PHASE 6/7 종료 검증 | 없음 | Stop 훅 |
| 루프 중단 안내 | 없음 | `/next` 0단계 |

**여전히 사람이 해야 하는 것** (의도적):
PHASE 3 plan 승인 · PHASE 8 수동 UI 테스트 · MR 머지 확인 · Redmine Resolved 전이 ·
BLOCKED 판단 · halt 후 접근 변경 결정.

## 0-F. 소프트 루프 — 전부 카운터에 연결됨

```
L1  Validator 7-2   빌드 실패 → 수정 → 재빌드         scope=build      상한 3
L2  Validator 7-6   FEEDBACK → Implementer 왕복       scope=feedback   상한 3
L3  sprint-dev S2/S3 리뷰 반려 → 수정 → 재리뷰        scope=review:N   상한 3
L4  Validator 8-6   수동 반려 → 수정 → 재검증         scope=manual     상한 3
L5  Stop 훅         PHASE 6 빌드 / PHASE 7 검증계약   scope=build/contract
```

모든 scope는 독립이다. PHASE나 스프린트가 바뀌면 전부 리셋된다.
동일 실패 시그니처 2회 연속이면 상한(3)을 기다리지 않고 조기 중단한다.

## 0-G. 환경 제약 (설계 입력값)

- **Windows + Git Bash.** 훅 프로세스 기동 비용 실측:
  `bash -c true` 1797ms / bash 스크립트 훅 5412ms / python 754ms.
  **bash가 python보다 2.4배 비싸다** — 모든 훅을 python으로 통일한 근거.
- **훅 출력은 반드시 UTF-8 바이트로 직접 쓴다.** `sys.stdout`/`sys.stderr`의 기본
  인코딩이 cp949라 이모지·em dash에서 `UnicodeEncodeError`가 나고, 그 exit 1은
  non-blocking error로 처리되어 **차단이 통째로 무효화된다.** 이 함정을 세 번 밟았다.
- **차단 사유는 stderr로 보낸다.** stdout에 쓰면 `hook error: No stderr output`만 뜨고
  이유가 모델에게 전달되지 않는다 — 원본 `.sh`의 결함이었다.
- **빌드 1회 1분 미만** (형님 실측) → 벽시계 상한 30분의 근거.
- Delphi 2007에는 린터도 단독 타입체커도 없다. 빠른 게이트를 린트로 채울 수 없어
  **인코딩·구조 검사가 그 자리를 대신한다.**

---

# 시공 결과 — 원래 STEP 1~7이 무엇이 되었나

| STEP | 결과 |
|---|---|
| 1 종료 조건 | 층 A `gate_harness.py` 신설 / 층 B는 `build.bat` + 검증계약 파싱 |
| 2 긴 루프 | `stop-loop-gate.py` — PHASE 게이팅, 이중 상한, 부재 구분, stderr 행동 지시 |
| 3 짧은 루프 | `posttooluse-fast-gate.py` — 인코딩만 exit 2, 나머지 3종은 경고 |
| 4 생성자/검증자 분리 | **이미 되어 있었다.** 재발명하지 않고 상한만 추가 |
| 5 컨텍스트 위생 | `attempts.log` 신설 + `precompact-preserve.py` |
| 6 탈출로 | `LOOP=halted` + `/next` 0단계 + `clear-halt` |
| 7 검수 | 격리 환경에서 78케이스 (아래) |

## 검수 현황

`.claude/tests/` — `python .claude/tests/run_all.py` (약 100초)

```
gate_harness      PASS       JSON·문법·참조·훅경로 (별도 실행)
PreToolUse 가드   42/42      규칙 7종 + 우회 7경로 차단 + 정상 통과 + 인용/인코딩 회귀
fast-gate         10/10      CP949 손상 탐지, BOM 허용, Bash 상시 검사, Write 빠른 경로
loop_state        15/15      상한·헛돌기·scope 독립·PHASE/스프린트 리셋 분리
stop-loop-gate    13/13      STEP 7 시나리오 전량 + 수동 항목 제외
policy            14/14      값 검증·저장·손상 파일 복구
                  ─────
                  94건
```

테스트는 절대 경로를 박지 않는다. `REPO`는 `__file__` 기준으로 계산하고 격리 레포는
`tempfile`로 만든다 — 다른 PC에서도 그대로 돌아야 하기 때문이다.

실물 검증(이 레포에서 직접): CP949 손상 탐지, `.pas` Write 차단, `cd &&` 차단,
브랜치 명명 위반 차단, 정상 명령 통과.

## STEP 4에 대한 판단 (원본이 요구한 결론)

**Validator 7-6의 "High 이하 직접 수정"은 유지한다.** 검증자가 수정 권한을 갖는 것은
원칙 위반이지만, 폐지하면 사소한 지적마다 FEEDBACK 왕복이 발생해 이터레이션이
늘어난다. 대신 `--scope feedback` 카운터가 왕복 자체에 상한을 걸므로,
남용되면 루프가 멈추고 사람에게 온다. 트레이드오프를 카운터로 관리하는 쪽을 택했다.

---

# 루프 금지 구역 (어떤 이유로도 자동화하지 않는다)

```
❌ PHASE 8 수동 UI 테스트를 루프가 통과 처리        런타임 검증 0%인 상태의 유일한 안전망
❌ 공용 유닛 자동 수정
   Common/ CommonBL/ CommonV7/ ComUnit/ PackageBL/  참조 프로젝트 다수
❌ DB 스키마 DDL 자동 실행
❌ .pas/.dfm 에 Write 도구 사용                     encoding-critical.md, 예외 없음
❌ 기존 한글 주석 수정/삭제                         깨져 보여도 원본 CP949 바이트
❌ master / Release 직접 push, force push, reset --hard
❌ 브랜치 명명 규칙 우회
❌ Implementer가 GOAL.md 체크박스 채우기            자기 채점 금지
❌ Redmine 상태 자동 Resolved 전이
❌ GitLab MR 자동 머지
❌ 상한 도달 시 "그래도 완료"로 STATUS 기록
```

---

# 남은 작업

## 1. 층 B 실전 검수 (우선순위 높음)

이 레포에는 Delphi 빌드 대상이 없어 `build.bat` 경로는 **"부재로 안전 통과"만**
검증했다. 실제 사이클 — 컴파일 실패 → Stop 훅 차단 → 수정 → 통과 → 카운터 리셋 —
은 적용 레포에서 첫 스프린트를 돌려야 확인된다.

확인할 것:
- `.dproj` 자동 탐지가 실제 디렉터리 구조에서 맞는 파일을 찾는가
- 빌드 에러 메시지에서 시그니처(`E2003:Unit.pas:412`) 추출이 되는가
- 빌드 1회 소요가 벽시계 상한(30분) 대비 합리적인가

## 2. ~~회귀 테스트가 레포에 없다~~ → 해결 (2026-09-22)

`.claude/tests/` 로 이관했다. 77케이스, 전체 약 100초.

```
python .claude/tests/run_all.py
```

`gate_harness.py`에는 **연결하지 않았다.** Stop 훅이 매 턴 `gate_harness`를 호출하므로
거기에 100초짜리 테스트를 물리면 턴마다 그 비용을 물게 된다. 훅이나
`.claude/scripts/*.py`를 고쳤을 때 수동으로 돌리는 쪽이 맞다.

## 3. ~~단위 테스트 실체 불일치~~ → 해결 (2026-09-22)

`dev-process.md` 5장 검증 매트릭스를 현실에 맞게 다시 썼다.
"단위 테스트 ✅ 자동"은 `⬜ 미구축`으로, 존재하지 않는 항목(API 엔드포인트·헬스체크·
린트)은 제거하거나 `—`로 바꿨다. 대신 실제로 도는 검증(빠른 게이트, 하네스 무결성,
검증 계약, 코드 리뷰)을 채웠다.

**DUnit 자체는 여전히 비어 있다.** 표기만 정직해졌을 뿐이므로, 런타임 커버리지 0%라는
사실은 그대로다. 표에 경고로 명시했다.

## 4. ~~bash-guard 오탐~~ → 해결 (2026-09-22)

브랜치 명명 검사에만 `strip_quoted()`를 적용했다. 인용된 문자열 안의 브랜치명은
실제 생성이 아니므로 검사에서 뺀다.

**다른 규칙에는 적용하지 않았다.** `bash -c "git push -f origin main"` 처럼
인용 안의 내용이 실제로 실행될 수 있어서, 인용을 벗기면 우회 경로가 된다.
브랜치명은 되돌리기 쉽고 force push는 아니라는 위험도 차이에 따른 결정이다.
(테스트에 두 경우를 모두 넣어 고정했다)

---

# 부록 A — 시공 중 드러난 결함 7건 (재발 방지용)

전부 **루프를 얹기 전에 터졌어야 할 것들**이다. 4단계로 쪼개 진행했기 때문에
루프 바깥에서 하나씩 분리해 잡을 수 있었다.

| # | 결함 | 영향 |
|---|---|---|
| 1 | 훅이 `settings.local.json`에만 배선 | 팀 전체에 CP949 보호가 보장되지 않음 |
| 2 | 훅 메시지의 이모지 | cp949 인코딩 실패 → exit 1 → **차단 무효화** |
| 3 | 차단 사유를 stdout에 출력 | 모델이 이유를 모른 채 같은 시도 반복 |
| 4 | bash 훅 기동 8초 | 모든 Bash 호출마다 지연 |
| 5 | em dash가 cp949에 없음 | 경고 출력 중 exit 1 → 게이트 무력화 |
| 6 | 검증기 early return | 스캔 문서가 없으면 훅 경로 검사까지 건너뜀 |
| 7 | `__pycache__` 유출 | 훅이 모듈을 import하며 생성 |
| 8 | **`build.bat`의 `SET DPROJ=` 무조건 대입** | `validator.md`·`verification` 스킬이 안내하는<br>`set DPROJ=... && build.bat` 오버라이드가 **애초에 동작하지 않았다**.<br>`IF "%DPROJ%"==""` 로 고쳐 외부 지정을 우선하게 했다 |

8번은 테스트를 레포로 옮기는 과정에서 드러났다. scratchpad 테스트는 우연히
`.dproj` 탐지 실패 경로를 타서 통과했었다 — **테스트 환경이 달라지자 잡혔다.**
회귀 테스트를 레포에 두어야 하는 이유가 이것이다.

9~12번은 시공 완료 후 **루프 감사**(아래 절)에서 드러났다.

| # | 결함 | 영향 |
|---|---|---|
| 9 | **PHASE 전이 시 전 scope 리셋** (`loop_state.py` 구 `:188`) | 7→6→7 왕복마다 `feedback` 카운터·벽시계·repeat가 0으로 → **왕복이 영원히 계수되지 않음.** 6↔7 자동 전이를 붙였다면 무한루프. 스프린트 변경만 전체 리셋, PHASE 변경은 `build`/`contract`만 리셋으로 분리 |
| 10 | **`gate_contract`가 수동 항목까지 계수** | PHASE 7에서 `(⚠️ 수동)` 항목은 `[ ]`가 정상인데 미충족으로 세고 "`[x]`로 바꿔라"고 지시 → **훅이 자기채점을 압박.** 테스트가 이 동작을 기대값으로 고정해놓기까지 했다. 수동 태그 줄 제외 |
| 11 | **fast-gate 문자열 트리거** | 명령에 `.pas`가 없으면 git을 안 봄 → `python fix.py` 한 줄이 `.pas` 수십 개를 UTF-8로 다시 써도 미탐. Bash 뒤엔 항상 `git status` |
| 12 | **bash-guard 우회 7경로** | `HEAD:master` refspec / `+브랜치` force / `bash -c 'cd && '` / `(cd ;)` 서브셸 / `git -C reset --hard` 전부 통과했음. 정규식 확장 |

# 루프 감사 (2026-09-22, 시공 완료 직후)

"루프 엔지니어링을 실제로 구현했는가, 아니면 재시도 위장인가"를 증거 기반으로 판정했다.

**판정: 재시도 위장 루프** — 골격(카운터·상한·탈출로)은 코드로 존재하지만,
작업 산출물에 대한 유일한 외부 검증(컴파일)은 이 레포에서 한 번도 돌지 않았고,
PHASE 7 게이트는 모델이 채운 체크박스를 훅이 세는 것이다.

| PART 1 | 판정 | 핵심 근거 |
|---|---|---|
| 종료 | 부분 | 층 A는 하네스만 검사. PHASE 6 빌드는 이 레포에서 미실행. PHASE 7은 모델 채점 카운트. (c)를 못 쓰는 이유는 문서화됨 |
| 분리 | 부분 | Implementer/Validator 분리는 **프롬프트만**. `GOAL.md`는 `.md`라 Edit 허용 — `[x]` 쓰기를 막는 코드 없음. `validator.md` 7-6 검증자 직접 수정 |
| 진전 | 충족(훅) / 희망사항(프롬프트) | Stop 훅 경로만 코드 강제. validator/sprint-dev의 bump는 모델이 호출해야 함 |
| 탈출 | 충족 | `LOOP=halted` · `attempts.log` · `/next` 0단계 · `clear-halt` |

**병목은 검증기다, 모델이 아니다.** 이 루프가 잡을 수 있는 것은 (a) `.claude/` 설정 파손
(b) `.pas` UTF-8 저장 (c) 컴파일 실패(대상 레포에서만) 셋이다. "기능이 맞게 동작하는가"는
어느 게이트도 보지 않는다. `Tests/Source/`는 `.gitkeep` 하나다.

감사 직후 결함 9~12를 고쳤다(부록 A). **판정 자체는 바뀌지 않는다** — 층 B가 실전에서
한 번 돌기 전까지는 "설계된 루프"라고 부를 근거가 없다.

## 감사 후 유지한 결정

- **Validator 7-6 "High 이하 직접 수정" 유지.** 분리 원칙 위반이지만 폐지하면 사소한 수정마다
  FEEDBACK 왕복이 생기고, 그 왕복은 결함 9를 고친 지금에야 비로소 계수된다.
  `--scope feedback` 상한이 남용을 막는다. 재검토 시점: 층 B 실전에서 왕복 빈도를 본 뒤.
- **bash-guard 인용 구간을 벗기지 않는다** (브랜치 검사 제외). 인용 안이라도 `bash -c`로
  실행될 수 있어, 벗기면 우회 경로가 된다.
- **`shlex` 전면 재작성은 하지 않았다.** 정규식 확장으로 확인된 7경로를 막았다. 셸 파싱을
  정확히 하려면 결국 토크나이저가 필요하지만, 지금 규모에 과하다.

---

# 부록 B — 설계 시 자주 틀리는 지점

1. **Stop 훅은 subagent 종료에 발동하지 않는다.** sprint-dev의 3-STEP 리뷰 왕복은
   Stop 훅으로 못 잡는다 — 그래서 프롬프트 지시 + 파일 카운터 병행으로 처리했다.
2. **PHASE 8에서 막으면 사용자가 갇힌다.**
3. **환경 부재를 실패로 보고하면 루프가 영원히 헛돈다.**
4. **카운터를 모델에게 세게 하지 마라.** 컴팩션 한 번이면 사라진다.
5. **FEEDBACK.md에 이력을 쌓지 마라.** 최신 지시가 과거 로그에 묻힌다.
6. **PostToolUse에 컴파일을 넣지 마라.** 툴 호출당 곱해지면 사용 불가가 된다.
7. **Windows 훅 출력은 항상 바이트로 써라.** 이 함정을 세 번 밟았다(부록 A #2 #3 #5).
8. **훅 경로 오타는 조용한 실패다.** 차단이 안 걸려도 아무 신호가 없으므로
   `gate_harness`가 `settings.json`의 command 경로 실재 여부를 검사한다.
9. **카운터 리셋 조건을 너무 넓게 잡지 마라.** "PHASE 바뀌면 리셋"은 직관적이지만,
   PHASE를 넘나드는 왕복 카운터까지 지운다. 무엇이 그 PHASE 안에서만 유효한지 나눠라.
10. **게이트가 모델에게 무엇을 시키는지 보라.** "미체크 항목을 체크하라"는 지시는
    체크할 수 없는 항목(수동 검증)이 섞여 있으면 자기채점 압박이 된다.
    게이트 실패 메시지가 곧 다음 턴의 행동이다 — 그 행동이 올바른지 먼저 확인할 것.
11. **명령 문자열을 보고 판단하지 마라.** 훅이 보는 건 문자열이고 실행되는 건 그 결과다.
    `python fix.py`는 아무것도 말해주지 않는다. 사후 게이트는 실제 변경(파일·git)을 봐야 한다.
12. **정규식 가드는 반드시 우회 프로브로 검증하라.** refspec, `+` 접두, 서브셸, `-C` 옵션 —
    "이 명령이 위험한가"를 문자열로 판정하는 순간 표현의 다양성이 전부 공격면이 된다.
