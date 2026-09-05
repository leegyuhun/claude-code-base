# claude-code-base

Claude Code로 PRD → 계획 → 스프린트 구현 → 검증 → 배포까지 이어지는 개발 파이프라인을
`.claude/agents`, `.claude/commands`, `.claude/rules`로 구성한 하네스(harness) 템플릿 저장소입니다.
`main`이 기술 스택 비종속 베이스이고, 나머지 브랜치들은 이를 특정 스택/워크플로우/실제 프로젝트에 맞게
변형하거나 실제로 적용해 본 결과물입니다.

## 브랜치 개요

| 브랜치 | 성격 | 한 줄 설명 |
| --- | --- | --- |
| `main` | 베이스 템플릿 | 스택 비종속 오케스트레이터 하네스 (PRD → plan → ROADMAP → GOAL → 구현 → 검증 → 배포) |
| `main_csharp` | 스택 변형 | `main`을 .NET / C# 스택에 맞게 변환 |
| `main_java` | 스택 변형 | `main`을 Java + Spring Boot 스택에 맞게 변환, CI/CD 규칙 추가 |
| `main_python` | 스택 변형 | `main`을 Python(FastAPI) + React/TypeScript 스택에 맞게 변환, CI/CD 규칙 + `/review` 추가 |
| `main_delphi` | 워크플로우 변형 | Delphi 2007 레거시 유지보수용 하네스. GitLab/Redmine 연동, 이슈 기반 브랜치·PR 전략 |
| `main_delphi_loop` | 워크플로우 변형 | `main_delphi`의 스프린트 방식을 "루프 엔지니어링" 방식으로 전환 (구현⇄검증 자동 반복) |
| `main_delphi_sprint-01` | 적용 사례 | `main` 계열 하네스로 실제 구현한 예시 프로젝트 (SNMP 프린터 스캐너, sprint-01 완료본) |
| `main_harness` | 별도 하네스 | YSR EMR 프로젝트 전용 이슈 기반 버그 수정 하네스 (조사 → 수정 → 커밋) |
| `main_harness_sprint` | 별도 하네스 변형 | `main_harness`에 스프린트형 Phase A/B/C 패치 패턴과 상태 조회 기능 추가 |

---

## `main` — 베이스 오케스트레이터 하네스

기술 스택을 가리지 않는 기본형입니다. `docs/PRD.md`를 사람이 작성하면 아래 파이프라인이 진행됩니다.

```
PRD.md
  → Orchestrator  (PHASE 1~4.5): plan.md, ROADMAP.md, CLAUDE.md 생성
  → Planner       (PHASE 5)    : sprints/{n}/GOAL.md 작성
  → Implementer   (PHASE 6)    : GOAL.md 체크리스트 기반 구현
  → Validator     (PHASE 7~10) : 빌드/테스트 검증, DONE.md, PR 생성
  → deploy-prod / hotfix-close : 프로덕션 배포, 핫픽스 마무리
```

- `.claude/agents`: `orchestrator`, `planner`, `implementer`, `validator`, `deploy-prod`, `hotfix-close`
- `.claude/commands`: `/sprint-dev`, `/status`, `/next`, `/rollback`, `/sprint-log`, `/debt`
- `.claude/rules`: `sprint-workflow.md`(워크플로우 규칙), `coding-principles.md`(스택 TODO 포함), `dev-process.md`
- `docs/`: `PRD.md`(사용자 작성), `STATUS.md`(현재 PHASE), `구조.md`, `프로세스.md`

## `main_csharp` — .NET / C# 스택

`main`과 에이전트·커맨드 구성은 동일하며, `coding-principles.md`만 C#에 맞게 교체되어 있습니다.

- 적용 경로가 `src/**` 대신 `**/*.cs`, `**/*.csproj`, `**/*.sln`
- 기술 스택 예시: .NET 8, ASP.NET Core, Entity Framework Core, xUnit
- 네이밍 컨벤션(PascalCase/camelCase/`_camelCase`), `Async` 접미사 규칙 명시
- 보안 절: `appsettings.json`/`IConfiguration`/`dotnet user-secrets`, `SqlParameter`/EF Core 파라미터 쿼리

## `main_java` — Java + Spring Boot 스택

`main` + Java/Spring 컨벤션 + CI/CD 규칙이 추가된 버전입니다.

- `.claude/rules/cicd.md` 신규: `.github/**`, `Dockerfile`, `docker-compose*.yml`, `Jenkinsfile` 대상
  - 파이프라인: 빌드 → 단위/통합/E2E(Playwright) 테스트 → 코드 품질 검사 → Docker 빌드/배포
  - 브랜치 트리거: PR(CI만) / `develop` push(CI+staging) / `main` push(CI+production)

## `main_python` — Python(FastAPI) + React/TypeScript 스택

`main` + Python/React 컨벤션 + CI/CD 규칙 + PR 리뷰 커맨드가 추가된 버전입니다.

- `.claude/rules/cicd.md`: 백엔드/프론트엔드 빌드·테스트 → E2E(Playwright) → 타입체크/린트 → Docker 배포
- `.claude/commands/review.md` 신규: `/review` — 베이스 브랜치 대비 diff를 Critical/High 체크리스트
  (시크릿 하드코딩, SQL injection, XSS, 인증 우회, N+1 쿼리, 에러 핸들링 등)로 검토

## `main_delphi` — Delphi 2007 레거시 유지보수 하네스

스프린트 파이프라인은 유지하되, 실제 사내 레거시 프로젝트(GitLab + Redmine 연동) 운영에 맞춰 확장한 버전입니다.

- 이슈 기반 흐름: `/prd #이슈번호` → Redmine 이슈 조회/PRD 생성 → 브랜치 생성 → Orchestrator → Planner →
  구현 → 검증 → `/resolve #이슈번호`(Redmine 상태 전이)
- `.claude/commands` 추가: `/branch`, `/prd`, `/resolve` · `.claude/agents/commit-writer.md` 추가
- `.claude/rules` 추가: `encoding-critical.md`(CP949 인코딩 주의), `delphi2007-patterns.md`,
  `active-issue.md`, `pitfalls-index.md`
- `.claude/skills`: `commit-format`, `redmine`, `requesting-code-review`,
  `subagent-driven-development`, `systematic-debugging`, `verification-before-completion`, `writing-plans`
- `.claude/hooks/pretooluse-bash-guard.sh`: 브랜치 명명 규칙 등 위험 명령 가드
- GitLab MCP 연동(`​.mcp.json.example`), `setup_claude.bat`으로 초기 설정 (Readme.md 참고)

## `main_delphi_loop` — 루프 엔지니어링 방식

`main_delphi`와 동일한 기반이지만, "사람이 프롬프트를 치는 대신 설계한 루프가 에이전트를 프롬프팅한다"는
원칙으로 구현⇄검증 단계를 자동 반복시키는 방식입니다.

- 기존 `sprint-dev.md`(커맨드), `sprint-workflow.md`/`dev-process.md`(규칙)는
  `.claude/_harness_backup/`으로 보관하고 비활성화
- PHASE 6~7(구현↔검증)을 Maker(구현)/Checker(독립 검증)가 종료 조건(기계 검증) 충족까지 자동 반복하는
  루프로 대체 — 계획(Orchestrator/Planner)과 최종 게이트(수동 테스트 이후 커밋/PR)만 사람이 개입
- 메모리 3계층: `VISION.md`(불변 방향), `AGENTS.md`(작업 규칙), `PROGRESS.md`/`STATUS.md`(가변 진행 상태)
- `implementer.md`, `planner.md`, `commands/next.md`, `commands/prd.md`가 루프 방식에 맞게 수정됨

## `main_delphi_sprint-01` — 적용 사례: SNMP 프린터 스캐너

Delphi 하네스로 실제 구현을 진행해 본 예시 프로젝트입니다(sprint-01까지 완료).

- 대상: **PrinterScanApp**(독립 실행 EXE) / **PrinterScanLib**(stdcall export DLL) —
  네트워크 프린터를 SNMP로 검색하는 Delphi 2007 유틸리티
- sprint-01 범위: SNMP v1/v2c 통신 모듈(UDP 161, ASN.1/BER 파싱), 네트워크 인터페이스 자동 감지
  (`GetAdaptersInfo`), CIDR 기반 서브넷 IP 범위 계산
- `sprints/ROADMAP.md`에 sprint-02(스캔 엔진+UI), sprint-03(사용자 기능), sprint-04(DLL Export) 로드맵 포함
- `.claude/rules/delphi2007-patterns.md`가 `main` 베이스에 추가된 형태(= `main` + Delphi 규칙 + 실제 소스)

## `main_harness` — YSR EMR 유지보수 하네스

앞의 브랜치들과 달리 PRD/스프린트 파이프라인이 아닌, **이슈 기반 버그 수정** 전용 경량 하네스입니다.

- 목표: 조사 → 수정 → 커밋 문서화를 자동화
- `.claude/agents`: `bug-investigator`, `commit-writer`, `patch-author`
- `.claude/skills`: `investigate`, `patch`, `redmine`, `ysr-maintenance`, `commit-format`
- 단순 코드 설명은 스킬 없이 바로 응답, 유지보수 작업 요청 시 `ysr-maintenance` 스킬 트리거

## `main_harness_sprint` — YSR 하네스 + 스프린트 패치 패턴

`main_harness`에 스프린트형 패치 절차를 얹은 버전입니다.

- `patch` 스킬에 **Phase A(계획) → Phase B(점진 수정) → Phase C(검증)** + `[PAUSE]` 체크포인트 도입
- 진행 중 상태를 조회할 수 있는 기능 추가 (`patch-author` 에이전트에도 반영)

---

## 브랜치 선택 가이드

- 새 프로젝트를 스택에 맞게 시작하려면 `main`(범용) 또는 `main_java` / `main_python` / `main_csharp`(스택 확정 시)에서 분기
- 레거시 Delphi 프로젝트를 GitLab/Redmine과 함께 이슈 단위로 운영하려면 `main_delphi`
- 사람 개입을 최소화한 반복 구현이 필요하면 `main_delphi_loop`
- 이슈 기반 버그 수정만 필요한 유지보수 전용 프로젝트라면 `main_harness`(또는 스프린트 패치 패턴이 필요하면 `main_harness_sprint`)
- `main_delphi_sprint-01`은 하네스를 그대로 참고용으로 재사용하기보다, 파이프라인이 실제로 어떤 산출물을 만들어내는지 확인하는 참고 예시로 활용
