# /rollback — 특정 PHASE로 되돌리기

## 워크스페이스 해석

1. `.claude/ACTIVE_ISSUE` 읽기 → ACTIVE_ISSUE 값 획득
2. 없으면 `git branch --show-current` 출력에서 `#(\d+)` 추출 (폴백)
3. 모두 실패 시 → "`⚠️ 활성 이슈를 확인할 수 없습니다.`" 출력 후 종료

WORKSPACE_DIR = `workspace/{ACTIVE_ISSUE}`
STATUS_FILE = `{WORKSPACE_DIR}/STATUS.md`

## TRACK 확인 (워크스페이스 해석 직후)

STATUS_FILE에서 `TRACK` 값을 읽어 롤백 옵션 메뉴를 결정한다.
- `TRACK=sprint` 또는 미지정 → Sprint 옵션 메뉴 ([1]~[8])
- `TRACK=defect` → Defect 옵션 메뉴 ([1]~[4])

## 인수 처리 (`$ARGUMENTS`)

`$ARGUMENTS`에 숫자가 있으면 해당 옵션 번호로 직접 이동한다.
- `/rollback 5` → 옵션 [5] (PHASE 6 — 구현 다시) 직접 실행 (확인 후)
- `/rollback` → 인수 없으면 아래 메뉴 표시

## 절차

1. 현재 PHASE 출력 ({STATUS_FILE}에서 읽기)

2. `$ARGUMENTS`에 유효한 옵션 번호(1~8)가 있으면:
   - 해당 옵션 내용을 보여주고 "이대로 롤백할까요? (예/아니오)" 확인 후 실행
   - 유효하지 않은 번호면 → 메뉴 표시로 폴백

3. 인수가 없으면 롤백 가능한 옵션 제시 (현재 PHASE 기준, TRACK별 분기)

   **TRACK=sprint (또는 미지정):**
   ```
   롤백 가능한 옵션 (Sprint 트랙):

   [1] PHASE 2 — Plan 다시 생성
       → {WORKSPACE_DIR}/plan.md 삭제
   [2] PHASE 4 — ROADMAP 다시 생성
       → {WORKSPACE_DIR}/sprints/ROADMAP.md 삭제
   [3] PHASE 4.5 — 프로젝트 초기화 다시
       → CLAUDE.md 관련만 리셋
   [4] PHASE 5 — 현재 스프린트 GOAL 다시 작성
       → {WORKSPACE_DIR}/sprints/{CURRENT_SPRINT}/GOAL.md 삭제
   [5] PHASE 6 — 현재 스프린트 구현 다시
       → GOAL.md 체크박스 초기화, 구현 코드는 유지
   [6] PHASE 7 — 자동 검증 다시 실행
       → GOAL.md 체크박스 [x] → [ ] 초기화
   [7] PHASE 8 — 수동 테스트 안내 다시 출력
       → 상태만 리셋, 코드/파일 변경 없음
   [8] PHASE 9 — push + MR 안내 다시
       → DONE.md/COMMIT_MESSAGE.md 재생성 후 push

   번호를 입력하세요 (또는 '취소'):
   ```

   **TRACK=defect:**
   ```
   롤백 가능한 옵션 (Defect 트랙):

   [1] PHASE 6 — 구현 다시
       → docs/PRD_{ACTIVE_ISSUE}.md의 ## 검증 계약 체크박스 초기화
         구현 코드는 유지
   [2] PHASE 7 — 자동 검증 다시 실행
       → PRD 검증 계약 체크박스 [x] → [ ] 초기화
   [3] PHASE 8 — 수동 테스트 안내 다시 출력
       → 상태만 리셋, 코드/파일 변경 없음
   [4] PHASE 9 — push + MR 안내 다시
       → {WORKSPACE_DIR}/DONE.md, {WORKSPACE_DIR}/COMMIT_MESSAGE.md 재생성 후 push

   번호를 입력하세요 (또는 '취소'):
   ```

   인수로 옵션 번호가 지정됐을 때도 동일하게 TRACK 기준으로 유효 범위 검증:
   - TRACK=sprint: [1]~[8]
   - TRACK=defect: [1]~[4] (sprint 번호 체계와 의미 다름에 주의)

3. 선택에 따라 실행:
   - 해당 파일 삭제 또는 초기화
   - {STATUS_FILE}의 PHASE 업데이트
   - 에이전트 완료 현황 리셋
   - 변경 내용 요약 출력

## 주의사항
- 이미 커밋/푸시된 코드는 되돌리지 않음 (git 작업은 별도)
- 롤백 전 현재 상태를 반드시 보여주고 확인 받기
- 되돌릴 수 없는 작업이면 경고 출력
