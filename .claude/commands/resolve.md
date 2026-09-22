# /resolve — Redmine 이슈 Resolved 처리

Redmine 이슈를 Resolved 상태로 업데이트합니다.
연결된 **요구관리(프로젝트 296) 일감**이 있으면 dev 일감과 동일한 값(담당자·시작일·완료일·개발팀)으로 동기화하고, 개발공수(cf147)를 입력받아 함께 Resolved 처리합니다.

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
📝 Redmine 댓글 초안을 작성할게요.

1. 수정/구현 내용 한 줄 요약
   (예: "환자 조회 시 삭제된 항목이 노출되던 문제 수정")

2. 확인 방법 / 테스트 시나리오
   (예: "OO 화면 → OO 조건으로 조회 → 결과 확인")

3. 주의사항 또는 특이사항
   (예: "기존 데이터 중 XX 케이스는 수동 확인 필요")

4. 건너띔
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

첨부할 파일을 선택합니다.

```
📎 첨부 옵션

  1. PRD.md — docs/PRD_*.md (현재 이슈 PRD)
  2. 첨부 없이 진행

선택 (1 또는 2):
```

- "1" → PRD.md 업로드 진행
- "2" → `{UPLOAD_TOKENS}` 비움, 다음 단계로 진행

선택이 있으면 각 파일을 Redmine에 업로드하여 토큰을 획득한다.

**PRD.md 선택 시:**
1. `.claude/ACTIVE_ISSUE`에서 이슈번호 확인 → `docs/PRD_{이슈번호}.md` 존재 확인
   - 없으면 `docs/PRD_*.md` Glob으로 최신 PRD 파일 탐색
   - 그래도 없으면: "⚠️ PRD 파일을 찾을 수 없습니다. 건너뜁니다." 출력 후 해당 항목 제외
   - PRD_FILE = 발견된 파일 경로
2. 존재하면 업로드:
   ```
   curl -s -X POST \
     -H "X-Redmine-API-Key: $REDMINE_API_KEY" \
     -H "Content-Type: application/octet-stream" \
     --data-binary @{PRD_FILE} \
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
   MCP(폴백): get_issue(issue_id={이슈번호})
   curl(우선): curl -s -H "X-Redmine-API-Key: $REDMINE_API_KEY" $REDMINE_URL/issues/{이슈번호}.json

3. 현재 status_id에서 2(InProgress)까지 순서대로 전환
   - 현재=1:  → 11(Confirmed) → 10(Assigned) → 2(InProgress)
   - 현재=11: → 10(Assigned)  → 2(InProgress)
   - 현재=10: → 2(InProgress)
   - 현재=2:  생략
   - 현재=3:  이미 완료, 종료

   ※ status_id=10(Assigned) 전환 시 assigned_to_id 필수:
   MCP(폴백): update_issue(issue_id={이슈번호}, status_id=10, assigned_to_id={MY_USER_ID})
   curl(우선): Body: {"issue": {"status_id": 10, "assigned_to_id": {MY_USER_ID}}}

   그 외 단계는 status_id만:
   MCP(폴백): update_issue(issue_id={이슈번호}, status_id={다음상태})
   curl(우선): Body: {"issue": {"status_id": {다음상태}}}

4. 날짜 필드 처리:
   - start_date: 2단계 응답의 issue.start_date 값 확인
     - 값이 있으면(null·빈 문자열 아님) → {EXISTING_START_DATE} 로 저장, Resolved 전환 시 start_date 필드 생략
     - 값이 없으면 → start_date 필드에 {start_date} 포함
   - due_date(완료일): 기존 값과 무관하게 항상 {due_date}(오늘)로 업데이트한다. 조건 없이 필수 포함.

   마지막으로 Resolved(3) + done_ratio/날짜 + 댓글 + 첨부파일 한 번에 전환
   ({NOTES}가 있으면 notes 필드 포함, 없으면 생략)
   ({UPLOAD_TOKENS}가 있으면 uploads 필드 포함, 없으면 생략)

   MCP(폴백): update_issue(issue_id={이슈번호}, status_id=3, done_ratio=100,
                     start_date="{start_date}",  ← EXISTING_START_DATE 없을 때만 포함
                     due_date="{due_date}",
                     notes="{NOTES}",
                     custom_fields=[{"id": 103, "value": "AI"}])
   curl(우선): curl -s -X PUT -H "X-Redmine-API-Key: $REDMINE_API_KEY" -H "Content-Type: application/json" \
         $REDMINE_URL/issues/{이슈번호}.json
         Body: {
           "issue": {
             "status_id": 3,
             "done_ratio": 100,
             "start_date": "{start_date}",  ← EXISTING_START_DATE 없을 때만 포함
             "due_date": "{due_date}",
             "notes": "{NOTES}",
             "uploads": [{UPLOAD_TOKENS}],
             "custom_fields": [{"id": 103, "value": "AI"}]
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

## Step 5 — 연결된 요구관리 일감 동기화

dev 일감(#{이슈번호}) Resolved 처리가 성공하면, **연결된 요구관리(프로젝트 ID 296) 일감**을
찾아 dev 일감과 동일한 값으로 동기화하고 Resolved까지 처리한다.

### 5.1 dev 일감 재조회 — 연결일감 + 동기화 값 확보

Step 4에서 확정된 최종 값을 얻기 위해 dev 일감을 relations 포함하여 재조회한다.

- MCP(폴백): getIssue(issueId={이슈번호}, include=relations)
- curl(우선): curl -s -H "X-Redmine-API-Key: $REDMINE_API_KEY" "$REDMINE_URL/issues/{이슈번호}.json?include=relations"

응답에서 추출:
- {DEV_ASSIGNED_ID} : issue.assigned_to.id (담당자)
- {DEV_START_DATE}  : issue.start_date (시작일)
- {DEV_DUE_DATE}    : issue.due_date (완료일)
- {DEV_TEAM}        : issue.custom_fields 중 id==128 의 value (개발팀). 값이 없으면 빈 값.
- {RELATIONS}       : issue.relations 배열

### 5.2 연결일감 중 요구관리(296) 필터

1. {RELATIONS}의 각 항목에서 상대 일감 ID를 구한다:
   - relation.issue_id == {이슈번호} → 상대 = relation.issue_to_id
   - 그 외 → 상대 = relation.issue_id

2. 각 상대 일감을 조회하여 프로젝트를 확인한다:
   - MCP(폴백): getIssue(issueId={상대ID})
   - curl(우선): curl -s -H "X-Redmine-API-Key: $REDMINE_API_KEY" "$REDMINE_URL/issues/{상대ID}.json"
   - project.id == 296 인 일감만 대상 목록 {REQ_ISSUES}에 담는다. (id, subject, status.id/name 보관)

3. {REQ_ISSUES}가 비어 있으면 Step 5를 종료하고 완료 출력으로 간다.

### 5.3 요구관리 일감별 처리 [각각 반복]

{REQ_ISSUES}의 각 일감마다 아래 (1)~(4)를 반복한다.

#### (1) 동기화 확인 [PAUSE]

```
🔗 연결된 요구관리 일감 발견

  #{req_id} {req_subject}
  현재 상태: {req_status_name}

이 일감을 dev 일감(#{이슈번호})과 동일하게 동기화하고 Resolved 처리할까요?
  - 담당자 : {DEV_ASSIGNED_ID}
  - 시작일 : {DEV_START_DATE}
  - 완료일 : {DEV_DUE_DATE}
  - 개발팀 : {DEV_TEAM}

'예' / '아니오'
```

'아니오' → 이 일감 건너뛰고 다음 일감으로.

#### (2) 개발공수 입력 [PAUSE]

```
⏱️ 개발공수(customField 147)를 입력해주세요.

  1. 0.25 (2h)
  2. 0.5  (4h)
  3. 0.75 (6h)
  4. 1    (1d)
  5. 직접입력

선택 (1~5):
```

- 1~4 → 각각 0.25 / 0.5 / 0.75 / 1
- 5 → "공수 값을 입력해주세요 (예: 2)" 출력 후 입력값 사용
→ 선택 값을 {DEV_TIME}로 저장.

#### (3) 순차 상태 전이 → Resolved

워크플로우: New(1) → Confirmed(11) → Assigned(10) → InProgress(2) → Resolved(3)
단계를 건너뛸 수 없으므로 요구관리 일감의 현재 상태부터 순차 전환하며, 각 단계에 dev 값을 실어 보낸다.

전환 경로:
- 현재=1(New):        →11 →10 →2 →3
- 현재=11(Confirmed): →10 →2 →3
- 현재=10(Assigned):  →2 →3
- 현재=2(InProgress): →3
- 현재=3(Resolved)/5(Closed): 상태 전이 없이 아래 Resolved 단계의 값 갱신 PUT만 수행

각 단계별 필드 ({DEV_TEAM}이 빈 값이면 id:128 항목 생략):
- →11(Confirmed): status_id=11, assigned_to_id={DEV_ASSIGNED_ID}, custom_fields=[{"id":128,"value":"{DEV_TEAM}"}]
- →10(Assigned):  status_id=10, assigned_to_id={DEV_ASSIGNED_ID}, custom_fields=[{"id":128,"value":"{DEV_TEAM}"}]
- →2(InProgress): status_id=2,  assigned_to_id={DEV_ASSIGNED_ID}, start_date="{DEV_START_DATE}", custom_fields=[{"id":128,"value":"{DEV_TEAM}"}]
- →3(Resolved):   status_id=3,  done_ratio=100, due_date="{DEV_DUE_DATE}", custom_fields=[{"id":128,"value":"{DEV_TEAM}"},{"id":147,"value":"{DEV_TIME}"}]

각 전환:
- MCP(폴백): updateIssue(issueId={req_id}, ...위 필드...)
- curl(우선): curl -s -X PUT -H "X-Redmine-API-Key: $REDMINE_API_KEY" -H "Content-Type: application/json" "$REDMINE_URL/issues/{req_id}.json" -d '{"issue": { ...위 필드... }}'

전환 중 하나라도 실패하면 남은 단계를 멈추고 (4)에서 실패로 보고한 뒤 다음 일감으로 넘어간다.
(dev 일감 resolve는 이미 확정되어 영향 없음)

#### (4) 결과 출력

성공:
```
✅ 요구관리 #{req_id} 동기화 + Resolved 완료 (개발공수 {DEV_TIME})
```
실패:
```
⚠️ 요구관리 #{req_id} 처리 실패 — {에러 메시지}
   URL: https://redmine.ubware.com/issues/{req_id}
   수동 확인이 필요합니다.
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
