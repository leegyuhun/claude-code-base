# Codex 운영 안내

## 자동 로드 규칙

Codex는 저장소 루트의 `AGENTS.override.md`를 자동으로 읽는다. `AGENTS.override.md`는 상세 규칙인 `AGENTS.md`와 방향 문서 `VISION.md`를 먼저 읽도록 지시한다. 별도 에이전트 정의나 슬래시 명령은 필요 없다.

## 제품 코드 작업 준비

`.codex/ACTIVE_ISSUE.example`을 `.codex/ACTIVE_ISSUE`로 복사하고 이슈 번호를 입력한다. 실제 값은 Git에서 제외된다. 작업 계약은 우선순위대로 다음 중 하나다.

1. `sprints/{sprint}/GOAL.md`
2. `docs/PRD_{issue}.md`의 `## 검증 계약`
3. 사용자가 제공한 범위와 검증 기대치

Codex는 구현과 로컬 검증을 수행할 수 있다. 커밋·push·배포·마이그레이션·외부 이슈 변경은 사용자의 별도 요청이 필요하다.

## 복사해 쓸 요청

```text
AGENTS.md, VISION.md, .codex/ACTIVE_ISSUE를 읽어라. 현재 이슈의 작업 계약을 확인한 뒤 미완료 항목을 구현해라. CP949 및 Sybase ASA/PostgreSQL 규칙을 지키고, 변경에 맞는 검증을 새로 실행한 뒤 명령과 결과를 보고해라. 커밋과 push는 하지 마라.
```

```text
현재 빌드 실패의 근본 원인을 조사해라. AGENTS.md를 먼저 읽고 가장 작은 안전한 수정을 적용한 뒤 관련 빌드를 다시 실행해라. 해결되지 않으면 가설·증거·다음 판단에 필요한 정보를 보고해라.
```

```text
현재 diff를 AGENTS.md의 CP949, SQL, 공유 유닛, 데이터 안전성 규칙으로 검토해라. 파일은 수정하지 말고 Critical, High, Medium 순으로 재현 가능한 문제만 보고해라.
```

## 권장 상태 기록

복잡한 작업은 `tasks/todo.md`에 계획·진행·검증 결과를 남긴다. 이슈가 길어지면 `workspace/{issue}/PROGRESS.md`에 가설, 변경 요약, 검증 결과, 미해결 위험을 기록한다. `GOAL.md` 체크박스는 구현자가 임의로 완료 처리하지 않으며, 검증 뒤에만 변경한다.

## 설치 확인

저장소 루트에서 다음 명령으로 지침 로드를 확인할 수 있다.

```powershell
codex exec --sandbox read-only --ephemeral "Summarize the project instructions. Do not run tools."
```
