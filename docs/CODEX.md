# Codex 운영 안내

## 운영 계층

| 계층 | 역할 |
|---|---|
| `AGENTS.md` | Codex 자동 로드 정본: 도메인 안전 규칙과 종료 조건 |
| `.codex/playbooks/` | 반복 가능한 단계별 절차 |
| `.codex/templates/` | 이슈 상태·계획·피드백 산출물 |
| `.codex/agents/` | 계획·구현·리뷰·빌드복구 역할 |
| `workspace/{issue}/` | 이슈별 장기 작업 메모리 |

## 새 이슈 시작

```powershell
Copy-Item .codex/ACTIVE_ISSUE.example .codex/ACTIVE_ISSUE
New-Item -ItemType Directory workspace/#1234
Copy-Item .codex/templates/STATUS.md workspace/#1234/STATUS.md
Copy-Item .codex/templates/PROGRESS.md workspace/#1234/PROGRESS.md
```

Sprint로 분류되면 `GOAL.md`, `OUT_OF_SCOPE.md`도 복사한다. 그 다음 Codex에 아래 요청을 전달한다.

```text
AGENTS.md, VISION.md, .codex/playbooks/00-INTAKE.md와 workspace/#1234/STATUS.md를 읽어라.
이 요청을 Sprint 또는 Defect로 분류하고 상태·위험·검증 계약을 채워라. 아직 제품 코드는 수정하지 마라.
공유 유닛 영향이 있으면 모듈 목록과 함께 멈춰라.
```

## Sprint 운영

1. **계획**: planner가 `02-PLANNING.md`에 따라 `GOAL.md`를 작성한다.
2. **구현**: implementer가 한 GOAL 항목만 구현하고 `PROGRESS.md`에 근거를 기록한다.
3. **리뷰**: reviewer가 계약과 diff를 독립 검토한다.
4. **통합 검증**: 메인 Codex가 `05-VALIDATION.md`로 빌드·테스트·계약을 확인한다.
5. **사람 게이트**: 수동 테스트와 외부 변경은 사람이 승인한다.

```text
planner 에이전트에게 workspace/#1234/GOAL.md 계획을 맡겨라. 제품 코드는 변경하지 말고,
범위·비범위·자동 검증·수동 테스트·롤백 신호를 채워라.
```

```text
implementer 에이전트에게 GOAL.md의 항목 2만 구현하게 해라. PROGRESS.md에 근거를 기록하고,
GOAL 체크박스는 바꾸지 않게 해라.
```

```text
reviewer 에이전트에게 현재 diff를 독립 검토하게 해라. Critical/High만 FEEDBACK.md 형식으로
보고하고 제품 파일은 수정하지 않게 해라.
```

## Defect와 빌드 복구

Defect는 `00-INTAKE.md`의 경량 기준을 충족할 때만 사용한다. 원인이 불명확하거나 수정이 확장되면 Sprint로 승격한다. 빌드가 깨졌다면 `build_recovery` 역할과 `06-BUILD-RECOVERY.md`를 사용한다. 동일한 첫 오류가 두 번 반복되거나 총 10회 시도하면 추측을 멈추고 `PROGRESS.md` 증거와 함께 에스컬레이션한다.

## 재개와 설치 확인

재개할 때는 `STATUS.md`, `PROGRESS.md`, `GOAL.md`, `FEEDBACK.md` 순으로 읽는다. `NEXT_ACTION`이 다음 작업의 시작점이다.

```powershell
codex exec --sandbox read-only --ephemeral "프로젝트 지침을 요약하고 대형 프로젝트 워크플로우 단계를 나열해라. 도구는 실행하지 마라."
```
