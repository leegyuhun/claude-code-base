# /resolve — Redmine 이슈 Resolved 처리

Redmine 이슈를 Resolved 상태로 업데이트합니다.

**사용법:**
- `/resolve 207500` — 이슈 번호 직접 지정

---

다음 단계를 순서대로 수행하세요.

## Step 1 — 이슈 번호 확인

이슈 번호 결정:
1. `$ARGUMENTS`에 숫자가 있으면 그 값 사용
2. 없으면 → "이슈 번호를 입력해주세요. 예: `/resolve 207500`" 출력 후 종료

## Step 2 — 날짜 계산

- `start_date`: `git log --format=%as --reverse | head -1` (브랜치 최초 커밋 날짜)
  - git log 결과가 없으면 오늘 날짜 사용
- `due_date`: 오늘 날짜 (YYYY-MM-DD)

## Step 3 — 확인 [PAUSE]

아래 내용을 출력하고 사용자 확인을 기다립니다:

```
Redmine 이슈 #{이슈번호}를 다음 내용으로 업데이트합니다.

- status  : Resolved
- 진행률  : 100%
- 시작일  : {start_date}
- 완료일  : {due_date}

계속할까요? '예' / '아니오'
```

'아니오' → 종료

## Step 3.5 — 댓글 작성 인터뷰 [PAUSE]

git diff를 읽어 현재 변경 내용을 파악한 뒤, 기획자·QA가 참고할 만한 내용이 있는지 판단한다.

**판단 기준 (하나라도 해당하면 인터뷰 진행):**
- UI/화면 동작이 변경됨
- 테스트가 필요한 특정 조건이 있음
- 수정 경위나 주의사항이 있음
- DB 데이터나 설정 변경이 수반됨

해당 없으면 이 단계를 건너뛴다.

**해당 있을 때** 아래 질문을 한 번에 출력하고 응답을 기다린다:

```
📝 Redmine 댓글 초안을 작성할게요. (빈칸은 생략됩니다)

1. 수정/구현 내용 한 줄 요약
   (예: "환자 조회 시 삭제된 항목이 노출되던 문제 수정")

2. 확인 방법 / 테스트 시나리오
   (예: "OO 화면 → OO 조건으로 조회 → 결과 확인")

3. 주의사항 또는 특이사항
   (예: "기존 데이터 중 XX 케이스는 수동 확인 필요")
```

응답을 받으면 아래 형식으로 댓글 초안을 구성하여 출력한다:

```
─────────────────────────────────────
📋 댓글 초안

[수정 내용]
{1번 답변}

[확인 방법]
{2번 답변}

{3번 답변이 있으면:}
[주의사항]
{3번 답변}
─────────────────────────────────────
댓글을 추가할까요? '예' / '아니오'
```

- '예' → {NOTES} 에 초안 내용 저장 후 Step 4로 진행
- '아니오' → {NOTES} 비움, Step 4로 진행

## Step 3.7 — 첨부파일 선택 [PAUSE]

첨부할 파일을 선택합니다. (복수 선택 가능, 없으면 Enter)

```
📎 첨부 옵션 (번호를 쉼표로 구분, 없으면 Enter)

  1. PRD.md — docs/PRD.md

선택 (예: "1" 또는 Enter로 건너뜀):
```

선택이 있으면 각 파일을 Redmine에 업로드하여 토큰을 획득한다.

**PRD.md 선택 시:**
1. `docs/PRD.md` 존재 확인
   - 없으면: "⚠️ docs/PRD.md 가 없습니다. 건너뜁니다." 출력 후 해당 항목 제외
2. 존재하면 업로드:
   ```
   curl -s -X POST \
     -H "X-Redmine-API-Key: $REDMINE_API_KEY" \
     -H "Content-Type: application/octet-stream" \
     --data-binary @docs/PRD.md \
     "$REDMINE_URL/uploads.json"
   ```
   응답: `{"upload": {"token": "..."}}`
   → 토큰을 `{UPLOAD_TOKENS}` 배열에 추가:
   ```json
   {"token": "{token}", "filename": "PRD.md", "content_type": "text/plain"}
   ```

선택 없으면 `{UPLOAD_TOKENS}` = 비움

---

## Step 4 — Redmine API 업데이트

워크플로우: New(1) → Confirmed(11) → Assigned(10) → InProgress(2) → Resolved(3)
단계를 건너뛸 수 없으므로 현재 상태부터 순차 전환한다.

```
전환 순서 맵: 1→11→10→2→3
목표 상태: Resolved (status_id=3)

1. 현재 사용자 ID 조회 (Assigned 단계에 필요)
   MCP: 없음 → curl -s -H "X-Redmine-API-Key: $REDMINE_API_KEY" $REDMINE_URL/users/current.json
   → user.id 추출하여 {MY_USER_ID} 로 저장

2. 현재 상태 조회
   MCP: get_issue(issue_id={이슈번호})
   폴백: curl -s -H "X-Redmine-API-Key: $REDMINE_API_KEY" $REDMINE_URL/issues/{이슈번호}.json

3. 현재 status_id에서 2(InProgress)까지 순서대로 전환
   - 현재=1:  → 11(Confirmed) → 10(Assigned) → 2(InProgress)
   - 현재=11: → 10(Assigned)  → 2(InProgress)
   - 현재=10: → 2(InProgress)
   - 현재=2:  생략
   - 현재=3:  이미 완료, 종료

   ※ status_id=10(Assigned) 전환 시 assigned_to_id 필수:
   MCP: update_issue(issue_id={이슈번호}, status_id=10, assigned_to_id={MY_USER_ID})
   폴백: Body: {"issue": {"status_id": 10, "assigned_to_id": {MY_USER_ID}}}

   그 외 단계는 status_id만:
   MCP: update_issue(issue_id={이슈번호}, status_id={다음상태})
   폴백: Body: {"issue": {"status_id": {다음상태}}}

4. 2단계 응답의 issue.start_date 값을 확인한다:
   - 값이 있으면(null·빈 문자열 아님) → {EXISTING_START_DATE} 로 저장, Resolved 전환 시 start_date 필드 생략
   - 값이 없으면 → start_date 필드에 {start_date} 포함

   마지막으로 Resolved(3) + done_ratio/날짜 + 댓글 + 첨부파일 한 번에 전환
   ({NOTES}가 있으면 notes 필드 포함, 없으면 생략)
   ({UPLOAD_TOKENS}가 있으면 uploads 필드 포함, 없으면 생략)

   MCP: update_issue(issue_id={이슈번호}, status_id=3, done_ratio=100,
                     start_date="{start_date}",  ← EXISTING_START_DATE 없을 때만 포함
                     due_date="{due_date}",
                     notes="{NOTES}")
   폴백: curl -s -X PUT -H "X-Redmine-API-Key: $REDMINE_API_KEY" -H "Content-Type: application/json" \
         $REDMINE_URL/issues/{이슈번호}.json
         Body: {
           "issue": {
             "status_id": 3,
             "done_ratio": 100,
             "start_date": "{start_date}",  ← EXISTING_START_DATE 없을 때만 포함
             "due_date": "{due_date}",
             "notes": "{NOTES}",
             "uploads": [{UPLOAD_TOKENS}]
           }
         }
```

성공 시:
```
✅ Redmine 이슈 #{이슈번호} Resolved 처리 완료
   시작일: {start_date} / 완료일: {due_date}
```

실패 시:
```
⚠️ Redmine 업데이트 실패. 수동으로 처리해주세요.
   이슈 번호: #{이슈번호}
   URL: https://redmine.ubware.com/issues/{이슈번호}
```

## 완료 후 항상 출력

```
─────────────────────────────────────
다음 단계:
  - MR이 아직 없다면 → GitLab에서 MR 생성
  - 배포 준비가 됐다면 → .claude/agents/deploy-prod.md 읽고 프로덕션 배포 진행해줘
  - 현재 상태 확인 → /status
─────────────────────────────────────
```
