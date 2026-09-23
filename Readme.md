### 적용방법
 1. 이 템플릿의 `.claude/`, `.githooks/`, `docs/`, `setup_claude.bat` 을 대상 프로젝트 루트에 복사합니다.
 2. setup_claude.bat을 실행해주세요. (git hook 경로, `.claude/settings.local.json`, `.gitignore` 항목을 설정합니다)
 3. 클로드코드를 재실행합니다.
 4. `/prd {이슈ID}` 로 작업을 시작합니다. 이슈ID는 자유 형식입니다. (`#123`, `PROJ-45`, `exp_login` 등)

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

### PR / MR

PHASE 9에서 브랜치를 push한 뒤 PR/MR 제목·본문 초안을 안내합니다.
호스팅(GitHub/GitLab/Bitbucket 등)에 종속되지 않으므로 생성은 각 호스팅 화면에서 직접 진행합니다.
