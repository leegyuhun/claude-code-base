---
name: redmine
description: Redmine 이슈를 실시간으로 조회한다. 이슈 번호를 받아 제목, 현상 설명, 담당자, 우선순위, 첨부 정보를 가져온다. bug-investigator 에이전트가 코드 탐색 전 이슈 컨텍스트를 파악할 때 사용한다.
---

# Redmine 이슈 조회 스킬

## API 정보

- **베이스 URL**: `https://redmine.ubware.com`
- **이슈 조회**: `GET /issues/{id}.json`
- **인증**: `X-Redmine-API-Key` 헤더

## API 키 로드

`.env` 파일에서 읽는다 (프로젝트 루트: `E:/Source/ysr/.env`):

```
REDMINE_API_KEY=xxxxxxxxxxxxxxxx
```

파일을 Read 도구로 읽고 `REDMINE_API_KEY=` 뒤의 값을 추출한다.

## 이슈 조회 방법

WebFetch 도구로 호출:

```
URL: https://redmine.ubware.com/issues/{이슈번호}.json
Headers:
  X-Redmine-API-Key: {API_KEY}
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
| `.env` 파일 없음 | "`.env` 파일이 없습니다. `.env.example`을 참고해 API 키를 설정하세요." 출력 후 중단 |
| API 키 없음/빈 값 | 동일 |
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
