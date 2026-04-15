---
name: redmine
description: Redmine 이슈를 실시간으로 조회한다. 이슈 번호를 받아 제목, 요구사항 설명, 담당자, 우선순위, 버전 정보를 가져온다. #이슈번호가 언급되면 반드시 이 스킬을 사용하라. orchestrator(PRD 분석·기능 목록 도출), planner(스프린트 계획·GOAL.md 작성), 기타 요구사항 파악이 필요한 모든 신규개발 단계에서 사용한다.
model: opus
---

# Redmine 이슈 조회 스킬

## 조회 방법

**MCP 우선**: `.mcp.json`에 redmine MCP 서버가 설정된 경우 MCP 도구를 사용한다.

```
MCP 도구: get_issue
파라미터: issue_id = {이슈번호}
```

**MCP 없을 때 폴백**: curl로 직접 호출.

API 키 우선순위:
1. 환경변수 `$REDMINE_API_KEY` (settings.json `env` 섹션에 설정됨)
2. `.env` 파일 (프로젝트 루트 기준, 없으면 상위 탐색)

```bash
curl -s -H "X-Redmine-API-Key: $REDMINE_API_KEY" \
  "$REDMINE_URL/issues/{이슈번호}.json"
```

## 응답에서 추출할 정보

| 필드 | 경로 | 용도 |
|------|------|------|
| 제목 | `issue.subject` | 커밋 메시지 제목 작성 |
| 설명 | `issue.description` | 버그 현상 파악 |
| 담당자 | `issue.assigned_to.name` | 참고용 |
| 우선순위 | `issue.priority.name` | 긴급도 판단 |
| 상태 | `issue.status.name` | 진행 상태 확인 |
| 카테고리 | `issue.category.name` | 커밋 카테고리 결정 |
| 버전 | `issue.fixed_version.name` | 대상 릴리즈 |

## 에러 처리

| 상황 | 처리 |
|------|------|
| MCP 도구 없음 | WebFetch 폴백으로 자동 전환 |
| API 키 없음 (폴백 시) | "`$REDMINE_API_KEY` 환경변수 또는 `.env` 파일이 없습니다. settings.json `env` 섹션에 `REDMINE_API_KEY`를 설정하세요." 출력 후 중단 |
| 401 Unauthorized | "API 키가 유효하지 않습니다. Redmine 계정의 API 키를 확인하세요." |
| 404 Not Found | "이슈 #{번호}를 찾을 수 없습니다. 이슈 번호를 확인하세요." |
| 네트워크 오류 | "Redmine 서버에 연결할 수 없습니다. 이슈 내용을 직접 붙여넣어 주세요." 출력 후, 코드 탐색만으로 진행 |

## 출력 형식

조회 성공 시 아래 형식으로 정리하여 반환:

```markdown
## Redmine 이슈 #[번호]

**제목:** [subject]
**상태:** [status] | **우선순위:** [priority]
**담당자:** [assigned_to] | **버전:** [fixed_version]
**카테고리:** [category]

### 설명
[description 전문]
```
