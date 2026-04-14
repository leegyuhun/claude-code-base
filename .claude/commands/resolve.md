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

## Step 4 — Redmine API 업데이트

워크플로우: New(1) → Confirmed(11) → Assigned(10) → InProgress(2) → Resolved(3)
단계를 건너뛸 수 없으므로 현재 상태부터 순차 전환한다.

```
전환 순서 맵: 1→11→10→2→3
목표 상태: Resolved (status_id=3)

1. 현재 사용자 ID 조회 (Assigned 단계에 필요)
   MCP: 없음 → WebFetch GET https://redmine.ubware.com/users/current.json
   → user.id 추출하여 {MY_USER_ID} 로 저장

2. 현재 상태 조회
   MCP: get_issue(issue_id={이슈번호})
   폴백: GET https://redmine.ubware.com/issues/{이슈번호}.json

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

4. 마지막으로 Resolved(3) + done_ratio/날짜 한 번에 전환
   MCP: update_issue(issue_id={이슈번호}, status_id=3, done_ratio=100,
                     start_date="{start_date}", due_date="{due_date}")
   폴백: PUT https://redmine.ubware.com/issues/{이슈번호}.json
         Body: {
           "issue": {
             "status_id": 3,
             "done_ratio": 100,
             "start_date": "{start_date}",
             "due_date": "{due_date}"
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
