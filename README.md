# Codex Delphi 유지보수 템플릿

YSR EMR Delphi 2007 코드베이스를 Codex로 장기 유지보수하기 위한 템플릿입니다. 단일 수정뿐 아니라 기능 스프린트, 장애 복구, 독립 코드 리뷰, 통합 검증, 사람 승인 게이트를 파일 기반으로 운영합니다.

## 시작

1. `.codex/ACTIVE_ISSUE.example`을 `.codex/ACTIVE_ISSUE`로 복사하고 이슈 번호를 입력합니다.
2. `workspace/{issue}/`를 만들고 `.codex/templates/STATUS.md`, `PROGRESS.md`를 복사합니다.
3. Sprint면 `GOAL.md`, `OUT_OF_SCOPE.md`도 복사합니다. Defect면 PRD에 검증 계약을 작성합니다.
4. Codex에 목표를 요청합니다. Codex는 `AGENTS.md`를 자동으로 읽고, 그 지시에 따라 `VISION.md`와 작업별 플레이북을 적용합니다.

## 핵심 문서

- [AGENTS.md](AGENTS.md): Delphi·CP949·SQL·리뷰·종료 조건의 정본 정책
- [Codex 운영 안내](docs/CODEX.md): 역할별 에이전트와 복사 가능한 요청
- [프로세스](docs/프로세스.md): 대형 작업 상태 전이와 사람 게이트
- [구조](docs/구조.md): 프로젝트 파일 구조
- [.codex/playbooks](.codex/playbooks): 반복 절차
- [.codex/templates](.codex/templates): 이슈 산출물 양식

Codex는 로컬 조사·구현·검증을 수행할 수 있습니다. 커밋, push, 배포, DB 마이그레이션, 외부 이슈 변경은 명시적으로 요청해야 합니다.
