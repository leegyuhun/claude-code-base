# AGENTS — Codex 작업 규칙

이 파일은 YSR(의사랑) EMR Delphi 2007 코드베이스를 Codex로 안전하게 유지보수하기 위한 프로젝트 정책이다. 사용자의 명시적 요청이 이 규칙보다 우선하지만, 환자 데이터 안전성과 인코딩 보호는 항상 고려한다.

## 1. 작업 범위와 상태

제품 코드 작업을 시작할 때 `.codex/ACTIVE_ISSUE`를 읽는다. 값은 이슈 번호 `#NNNNNN` 또는 임시 ID `^[a-z][a-z0-9_]{2,30}$` 형식이다.

- `WORKSPACE_DIR = workspace/{ACTIVE_ISSUE}`
- `STATUS_FILE = {WORKSPACE_DIR}/STATUS.md`
- `PROGRESS_FILE = {WORKSPACE_DIR}/PROGRESS.md`
- `PRD_FILE = docs/PRD_{ACTIVE_ISSUE}.md`

활성 이슈가 없으면 브랜치 이름에서 `#<number>`를 찾는다. 둘 다 없으면 제품 코드 변경 전에 사용자에게 이슈 ID를 요청한다. 이 템플릿 자체를 관리하는 작업에는 활성 이슈가 필요 없다.

`GOAL.md`, PRD의 검증 계약, 또는 사용자의 명시적 요청을 작업 계약으로 삼는다. 비단순 작업은 `tasks/todo.md`에 계획과 검증 결과를 기록한다.

## 2. CP949 인코딩 — 최우선

`.pas`와 `.dfm` 파일, 그리고 `ComUnit/`, `Common/`, `CommonBL/`, `CommonV7/`의 공유 유닛은 CP949(EUC-KR)일 수 있다.

- 해당 파일을 UTF-8로 변환하거나 일괄 포맷하지 않는다.
- 한글이 포함된 기존 줄을 교체 범위에 포함하지 않는다.
- 파일 전체를 다시 쓰지 않는다. 필요한 영문 코드 줄만 최소 범위로 수정한다.
- CP949 파일에 한글 주석을 추가해야 하면 CP949 인코딩을 명시한 방식으로만 읽고 쓴다.
- 인코딩이 불확실하면 수정 전 바이트와 인코딩을 확인하고, 안전한 방법이 확정되지 않으면 멈춰 보고한다.

## 3. SQL — Sybase ASA / PostgreSQL 듀얼 타겟

- 두 DBMS에서 동작하는 SQL을 우선한다.
- 불가피한 차이는 `TtsQuery.UsingPG`로만 분기한다.
- `TsQuery.pas`의 SQL 문법 관련 메서드를 우선 사용한다.
- 트랜잭션은 `DBBeginTrans`, `DBCommitTrans`, `DBRollbackTrans`만 사용한다. 데이터베이스 객체의 직접 트랜잭션 호출은 금지한다.

## 4. Delphi 구현 원칙

- 요청 범위에만 수술적으로 변경한다. `.pas`를 바꾸면 관련 `.dfm`의 동기화 필요성을 확인한다.
- 생성한 객체는 `FreeAndNil`, 리소스는 `try..finally`로 정리한다.
- 폼 종료·저장 전에 `TDataSet.State in [dsEdit, dsInsert]`를 확인하고 `Post` 또는 `Cancel`한다.
- 백그라운드 스레드는 VCL에 직접 접근하지 않고 `Synchronize`를 사용한다.
- `ProcessMessages` 사용 시 재진입 가드를 둔다.
- GDI `CreateFont`, `CreatePen`, `CreateBrush` 결과는 반드시 `DeleteObject`로 해제한다.
- 비즈니스 로직과 쿼리는 `TdmXxx`, 폼은 UI 중심의 `TfrmXxx`에 둔다.

명명: 클래스 `TMyClass`, 폼 `TfrmLogin`, 데이터모듈 `TdmMain`, 지역변수 `AVarName`, 멤버 `FVarName`, 전역 `GVarName`, 매개변수 `MParam`, 상수 `S_CONST_NAME`을 사용한다. 모든 제품 코드 수정에는 `// #이슈번호 변경 이유` 형식의 추적 주석을 남긴다. CP949 파일의 한글 주석은 2절을 따른다.

## 5. 공유 유닛 보호

`ComUnit/`, `Common/`, `CommonBL/`, `CommonV7/`은 다수 모듈이 공유한다. 기존 인터페이스(시그니처·프로퍼티)를 제거하거나 변경하지 않는다. 추가가 필요하거나 변경이 불가피하면 영향 모듈 목록을 보고하고 사용자 승인을 받은 뒤 진행한다.

## 6. Git과 외부 변경

- 작업 중간 커밋은 만들지 않는다. 커밋·push는 사용자가 요청한 시점에 한 번만 수행한다.
- 커밋 제목과 본문은 한글을 사용한다. 형식은 `fix: #{이슈번호} {목표 요약} - {sprint-name}`이다.
- force push, `git reset --hard`, 보호 브랜치 직접 push, 파일 대량 삭제, DB 마이그레이션 실행, 이슈 트래커 수정, 배포는 명시적 요청 없이는 하지 않는다.

## 7. 검증과 리뷰

완료를 말하기 전에 변경에 맞는 새 검증을 실행하고, 명령·exit code·오류 수를 확인한다. Delphi 프로젝트를 바꿨다면 가능한 경우 해당 `.dproj`로 `build.bat debug`를 실행해 `Build succeeded`와 exit 0을 확인한다.

다음은 차단(Critical 또는 High) 사항이다.

- 하드코딩된 시크릿, SQL injection, 데이터 손실 가능성, 인증·권한 우회
- DB·외부 API 오류 처리 누락, N+1과 불필요한 대량 루프
- `try..finally`/`FreeAndNil` 누락, 데이터셋 편집 상태 미처리
- 스레드의 VCL 직접 접근, GDI 해제 누락, `ProcessMessages` 재진입 미방지
- CP949 손상 또는 공유 유닛 인터페이스 변경

리뷰만 요청받은 경우에는 파일을 수정하지 않고 Critical, High, Medium 순으로 재현 가능한 사항만 보고한다.

## 8. 대형 작업 운영

기능 추가, 다중 모듈 변경, 스키마 변경, 50줄 초과 변경, 또는 원인이 불명확한
장애는 `.codex/playbooks/00-INTAKE.md`로 트랙을 먼저 분류한다.

- **Defect**: 프로덕션 장애·버그이며 변경이 작고(원칙적으로 3파일·50줄 이하),
  새 유닛·스키마 변경이 없는 작업이다.
- **Sprint**: 새 기능, 다중 모듈, 새 유닛, 스키마 변경, 또는 Defect 기준을 하나라도
  벗어나는 작업이다.

Sprint는 계획 → 구현 → 독립 리뷰 → 통합 검증 → 사람 게이트 순서를 따른다.
Defect는 검증 계약을 먼저 작성한 뒤 같은 구현·리뷰·검증 단계를 축소 적용한다.
상세 절차와 산출물 형식은 `.codex/playbooks/`와 `.codex/templates/`에 있다.

대형 작업의 상태는 `INTAKE → PLANNING → READY → IMPLEMENTING → REVIEWING →
VALIDATING → HUMAN_GATE → DONE` 순서다. `FEEDBACK`은 구현으로 되돌리는 상태이며,
`BLOCKED`와 `ESCALATED`는 어느 단계에서나 사용할 수 있다. 첫 오류 서명이 두 번
연속 같거나 전체 구현·복구 반복이 10회에 도달하면 추측을 멈추고 에스컬레이션한다.

작업 역할을 한 세션이 모두 수행할 수는 있지만, 대형 변경 또는 고위험 변경에서는
구현자와 검토자를 분리한다. 가능하면 `.codex/agents/planner.toml`,
`implementer.toml`, `reviewer.toml`, `build_recovery.toml`의 역할을 명시적으로
호출한다. Reviewer는 구현을 수정하지 않고 독립적으로 검토한다.

다음 산출물은 이슈 디렉터리 `workspace/{ACTIVE_ISSUE}/`에 둔다.

- `STATUS.md`: 현재 단계와 소유자
- `PROGRESS.md`: 가설, 시도, 검증 이력
- `GOAL.md`: Sprint 구현 계약
- `FEEDBACK.md`: 리뷰·검증 실패의 수정 지시
- `OUT_OF_SCOPE.md`: 발견했지만 이번 작업에 포함하지 않는 사항

`GOAL.md`의 체크박스는 독립 검증을 통과한 뒤에만 완료로 표시한다. 실패 시
`FEEDBACK.md`에 재현 방법, 기대/실제 결과, 수정 대상, 재검증 방법을 기록한다.

## 9. 종료 조건

자동 종료 조건은 다음을 모두 만족할 때만 충족된다.

1. 작업 계약의 자동 검증 항목 통과
2. 변경된 프로젝트 빌드 성공(해당 시)
3. 관련 테스트 성공(존재하는 경우)
4. Critical 0건, High 0건의 독립 리뷰
5. `PROGRESS.md`에 변경과 검증 근거 기록

수동 테스트, 커밋, push, PR/MR, 배포, DB 마이그레이션, 이슈 상태 변경은 자동
종료 조건 밖의 사람 게이트다.
