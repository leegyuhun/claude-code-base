### 적용방법
 1. 이 템플릿의 `.claude/`, `.githooks/`, `docs/`, `setup_claude.bat`, `clone_claude_template.*` 을 대상 프로젝트 루트에 복사합니다.
    (이미 한 번 적용한 프로젝트는 `clone_claude_template.bat` 로 최신 템플릿을 다시 당겨옵니다 — 아래 참조)
 2. setup_claude.bat을 실행해주세요.
 3. 클로드코드를 재실행합니다.
 4. `/prd {이슈ID}` 로 작업을 시작합니다. 이슈ID는 자유 형식입니다. (`#123`, `PROJ-45`, `exp_login` 등)

### setup_claude.bat이 하는 일

| 단계 | 작업 |
|------|------|
| [1/5] Git Hook | `core.hooksPath .githooks` — 커밋 메시지 포맷 검사 |
| [2/5] settings.local.json | `.claude/settings.local.json` 생성 또는 누락 키 병합 |
| [3/5] 훅 이관 | 구버전 settings.local.json 에 남은 hooks 블록 제거 (훅은 `.claude/settings.json` 공유) |
| [4/5] Python | 훅·루프 스크립트가 쓰는 `python3` 가 **실제로 실행되는지** 확인 (Store 스텁이면 가드가 조용히 무력화됨) |
| [5/5] .git/info/exclude | 아래 항목이 없으면 자동 추가 — `.gitignore` 가 아니라 저장소 로컬 ignore 라서 모든 브랜치에 적용되고 추적 파일을 건드리지 않음 |

**.git/info/exclude 자동 추가 항목**

| 항목 | 설명 |
|------|------|
| `.mcp.json` | MCP 설정 — 토큰이 남아 있을 수 있어 제외 |
| `/.claude/` | 작업 브랜치에서 템플릿을 untracked 로 두기 위함 (템플릿 브랜치에서는 추적) |
| `/docs`, `/workspace`, `/sprints/`, `/plan.md` | PRD·이슈별 산출물 |
| `claude.md`, `readme.md`, `setup_claude.bat`, `/.githooks/`, `/clone_claude_template.*` | 템플릿 파일 |

이미 존재하는 항목은 중복 추가되지 않습니다.

### 템플릿 재동기화 (`clone_claude_template.bat`)

템플릿 브랜치의 최신 `.claude/` 를 **현재 브랜치가 무엇이든** 작업 트리로 당겨옵니다. 브랜치명·경로는 `clone_claude_template.json` 에서 정합니다 (프로젝트 소유 — 템플릿 동기화 대상이 아님).

```json
{
  "remote": "origin",
  "default": "common",
  "templates": {
    "common": {
      "branch": "main_common",
      "paths": [".claude", "setup_claude.bat", ".githooks", "docs/STATUS.md", "docs/구조.md", "docs/프로세스.md", "docs/흐름도.html"],
      "fillOnly": [".claude/harness.json"],
      "runSetup": true
    }
  }
}
```

- `paths` 는 템플릿 커밋에서 그대로 체크아웃합니다. agents/commands/hooks/rules/skills/templates 와 settings.json 은 **정확 미러** — 거기에 로컬에서 추가한 파일은 지워집니다 (전체 백업 폴더가 먼저 만들어집니다).
- `fillOnly` 는 작업 기록입니다. 없으면 채우고, 내가 손대지 않았으면 갱신하고, 내가 고쳤으면 3-way 병합하거나 내 것을 유지합니다. `.claude/harness.json` 이 여기 들어가는 이유: PHASE 4.5 가 이 프로젝트에 맞게 채운 빌드 명령을 템플릿의 빈 값으로 덮으면 안 됩니다.
- `.claude/ACTIVE_ISSUE` 는 항상 현재 값을 유지합니다. `.claude/settings.local.json` 은 untracked 라 건드리지 않습니다.
- 마지막 동기화 커밋은 `.claude/.template-base` 에 기록되어 다음 동기화의 3-way 기준이 됩니다.
- 에이전트가 실행하는 경우(콘솔 없음) 메뉴를 건너뛰고 `default` 템플릿을 씁니다.

### 빌드·테스트 어댑터 (`.claude/harness.json`)

하네스는 특정 언어에 묶여 있지 않습니다. 빌드·테스트·빠른 검사 명령은 `.claude/harness.json` 한 곳에서 정의하고,
Stop 훅(PHASE 6 빌드)과 PostToolUse 훅(fast_check)이 이 명령을 실행합니다.

- Orchestrator PHASE 4.5가 프로젝트 스택을 감지해서 자동으로 채웁니다.
- 수동으로 작성해도 됩니다. `cmd`가 비어 있으면 "검증기 부재"로 보고 루프를 돌리지 않습니다 (실패가 아닙니다).

```json
{
  "source_globs": ["src/**/*"],
  "build":      { "cmd": "", "timeout": 600 },
  "test":       { "cmd": "", "timeout": 900 },
  "fast_check": { "cmd": "", "timeout": 60 },
  "error_pattern": ""
}
```

스택별 예시 (`build` / `test` / `fast_check`):

```
node   : npm run build          / npm test              / npx eslint .
python : python -m compileall -q src / pytest -q        / ruff check .
dotnet : dotnet build           / dotnet test           / dotnet format --verify-no-changes
go     : go build ./...         / go test ./...         / go vet ./...
```

실행 확인: `python .claude/scripts/harness_config.py show` / `python .claude/scripts/harness_config.py run build`

**Stop 훅의 PHASE 6 빌드 게이트는 기본 꺼짐**입니다. 매 턴 종료마다 전체 빌드를 돌리면 턴이 수 분씩 늘어나고 훅 timeout(660초)에 걸리면 게이트가 조용히 사라집니다. 빌드가 짧은 프로젝트에서만 켭니다 — `.claude/settings.local.json` 에:

```json
{ "env": { "HARNESS_STOP_BUILD_GATE": "1" } }
```

꺼져 있어도 빌드 판정은 Validator PHASE 7-2 가 하고, PHASE 7 검증 계약 게이트는 그대로 동작합니다.

### 셸 가드

`.claude/settings.json` 의 PreToolUse 훅이 **Bash 와 PowerShell 도구 둘 다** 검사합니다 — 보호 브랜치(main/master/release) push, force push, `reset --hard`, 브랜치 명명 규칙. `cd /x && ...` 체이닝 차단은 Bash 에만 적용됩니다 (PowerShell 의 `;` 는 문장 구분자라 오탐만 납니다).

### PR / MR

PHASE 9에서 로컬 커밋까지는 묻지 않고 진행하고, **push 직전에 한 번** 확인합니다. push 뒤에는 PR/MR 제목·본문 초안을 안내합니다.
호스팅(GitHub/GitLab/Bitbucket 등)에 종속되지 않으므로 생성은 각 호스팅 화면에서 직접 진행합니다.
PR/MR 대상 브랜치는 `/prd` 가 STATUS.md 에 기록한 `PARENT_BRANCH` · `ISSUE_BRANCH` 로 정합니다 — 브랜치명에서 다시 추론하지 않습니다.
