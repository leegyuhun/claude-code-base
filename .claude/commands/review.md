# /review — PR 코드 리뷰

현재 브랜치의 변경사항을 검토하고 코드 리뷰 의견을 제공합니다.

## 실행 절차

### 1단계: 변경 범위 파악
```bash
# 베이스 브랜치 자동 탐지 (main 또는 develop)
BASE_BRANCH=$(git branch -r | grep -E 'origin/(main|develop)' | head -1 | sed 's/origin\///' | xargs)
git diff --stat ${BASE_BRANCH}...HEAD
```
- 변경된 파일 수, 추가/삭제 라인 수 출력
- 변경 규모 판단: Hotfix 기준(파일 3개 이하, 50줄 이하) vs Sprint 기준

### 2단계: 파일별 변경 내용 검토
변경된 파일을 하나씩 읽어 내용 파악 후 아래 체크리스트 적용.

### 3단계: 체크리스트 검토

#### Critical (배포 차단)
- [ ] 시크릿/API키 하드코딩 여부 (`.env`, 환경변수로 관리해야 함)
- [ ] SQL injection 위험 (SQLAlchemy ORM 사용, raw SQL 문자열 연결 금지)
- [ ] XSS 위험 (`dangerouslySetInnerHTML` 사용, 사용자 입력 노출)
- [ ] 인증/권한 우회 (엔드포인트 `Depends(get_current_user)` 누락)
- [ ] 데이터 유실 위험 (DELETE/UPDATE without WHERE, 트랜잭션 미처리)

#### High (수정 권장)
- [ ] N+1 쿼리 (루프 내 DB 호출, `selectinload`/`joinedload` 누락)
- [ ] 에러 핸들링 누락 (외부 API 호출, DB 연결, 파일 I/O)
- [ ] `any` 타입 사용 (TypeScript — `unknown` 또는 구체적 타입 사용)
- [ ] 테스트 파일 누락 (새 기능에 pytest/Vitest 테스트 없음)
- [ ] `print()` 사용 (Python — `logging` 모듈 사용해야 함)

#### Medium (기록)
- [ ] 코딩 원칙 불일치 (`coding-principles.md` 기준)
- [ ] 불필요한 코드/import
- [ ] TODO 주석 미표시 임시 코드
- [ ] 컴포넌트에 비즈니스 로직 포함 (커스텀 훅으로 분리해야 함)

### 4단계: 결과 출력

```
┌──────────────────────────────────────────────┐
│ 코드 리뷰 결과                               │
│                                              │
│ 변경 범위: N개 파일, +X줄 / -Y줄            │
│                                              │
│ Critical: N건  ← 배포 차단                  │
│ High:     N건  ← 수정 권장                  │
│ Medium:   N건  ← 기록                       │
└──────────────────────────────────────────────┘

## Critical
(없으면 "없음")

## High
(없으면 "없음")

## Medium
(없으면 "없음")

## 종합 의견
(1~3줄 요약)
```

Critical 항목이 있으면:
→ "배포 전 반드시 수정이 필요합니다."

Critical 없음 + High 있으면:
→ "수정을 권장하지만 배포는 가능합니다."

모두 없거나 Medium만 있으면:
→ "리뷰 통과. 배포 가능합니다."

## 주의사항

- 이 커맨드는 의견 제시만 합니다. 코드를 직접 수정하지 않습니다.
- 수정이 필요하면 직접 요청하거나 Implementer 에이전트를 실행하세요.
- `.claude/rules/coding-principles.md`와 `CLAUDE.md`를 기준으로 리뷰합니다.
