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

```
gate_harness      PASS       JSON·문법·참조·훅경로, 실패 경로까지
bash-guard        18/18      규칙 7종 차단 + 정상 통과
cp949-guard       10/10      .pas/.dfm/대문자/윈도경로 차단, 오탐 없음
fast-gate          9/9       CP949 손상 탐지, BOM 허용, 빠른 경로
loop_state        13/13      상한·헛돌기·scope 독립·PHASE 리셋
stop-loop-gate    12/12      STEP 7 시나리오 전량
```

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

## 2. 회귀 테스트가 레포에 없다

검수에 쓴 스크립트 6개가 전부 세션 scratchpad에만 있고 커밋되지 않았다.
**즉 다음 사람은 78케이스를 재현할 수 없다.** 훅을 고칠 때 회귀를 잡을 방법이 없는
상태이고, 이건 루프 엔지니어링 관점에서 모순이다 — 검증기를 만들어놓고 검증기의
검증기가 없다.

`Tests/harness/` 아래로 옮기고, `gate_harness.py`가 이를 실행하도록 연결하는 것을 권한다.

## 3. 단위 테스트 실체 (`dev-process.md` 5장 불일치)

`Tests/Source/`가 비어 있는데 검증 매트릭스는 "단위 테스트 ✅ 자동"이라고 적혀 있다.
DUnit을 실제로 채울 계획이 없다면 표기를 현실에 맞게 고쳐야 한다.

## 4. bash-guard 오탐 (경미)

명령 문자열 안에 인용된 브랜치명도 실제 명령으로 오인해 차단한다.
원본 `.sh`와 동일한 동작이며 실무에서 걸리는 경우는 드물다(테스트 코드 작성 시).
고치려면 인용 구간을 제외하는 파싱이 필요한데, 비용 대비 가치가 낮아 보류했다.

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
