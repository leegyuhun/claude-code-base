# /rollback — 특정 PHASE로 되돌리기

docs/STATUS.md를 읽고 현재 상태를 보여준 뒤, 롤백 옵션을 질의해줘.

## 절차

1. 현재 PHASE 출력

2. 롤백 가능한 옵션 제시 (현재 PHASE 기준)

   ```
   롤백 가능한 옵션:

   [1] PHASE 2 — Plan 다시 생성
       → plan.md 삭제
   [2] PHASE 4 — ROADMAP 다시 생성
       → sprints/ROADMAP.md 삭제
   [3] PHASE 4.5 — 프로젝트 초기화 다시
       → CLAUDE.md 관련만 리셋
   [4] PHASE 5 — 현재 스프린트 GOAL 다시 작성
       → sprints/{CURRENT_SPRINT}/GOAL.md 삭제
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

3. 선택에 따라 실행:
   - 해당 파일 삭제 또는 초기화
   - docs/STATUS.md의 PHASE 업데이트
   - 에이전트 완료 현황 리셋
   - 변경 내용 요약 출력

## 주의사항
- 이미 커밋/푸시된 코드는 되돌리지 않음 (git 작업은 별도)
- 롤백 전 현재 상태를 반드시 보여주고 확인 받기
- 되돌릴 수 없는 작업이면 경고 출력
