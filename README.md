# Codex Delphi maintenance template

YSR EMR Delphi 2007 코드베이스를 Codex로 유지보수하기 위한 템플릿입니다.

## 시작

1. 이 템플릿을 대상 저장소에 복사합니다.
2. 제품 코드 작업 전 `.codex/ACTIVE_ISSUE.example`을 복사해 `.codex/ACTIVE_ISSUE`를 만들고 이슈 번호를 입력합니다.
3. 저장소 루트에서 Codex를 실행하고 작업 목표와 검증 기대치를 요청합니다.
4. Codex는 `AGENTS.override.md`, `AGENTS.md`, `VISION.md`을 읽어 CP949, Delphi 안전성, 듀얼 DB SQL, 공유 유닛 보호 규칙을 적용합니다.

## 핵심 문서

- [AGENTS.md](AGENTS.md): 구현·안전·검증의 정본 정책
- [VISION.md](VISION.md): 불변 방향과 책임 경계
- [Codex 운영 안내](docs/CODEX.md): 작업 계약과 복사 가능한 요청 예시
- [프로세스](docs/프로세스.md): 계획부터 검증까지의 Codex 작업 흐름
- [구조](docs/구조.md): 템플릿 파일 구조

Codex는 작업 트리 수정과 검증까지 수행합니다. 커밋, push, 배포, DB 마이그레이션, 외부 이슈 변경은 명시적으로 요청해야 합니다.
