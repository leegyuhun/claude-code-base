---
paths:
  - "sprints/**"
  - "docs/STATUS.md"
  - "docs/PRD.md"
  - "plan.md"
---

# 개발 프로세스

> 이 문서는 claude-code-base 프로젝트의 전체 개발 프로세스를 정의합니다.
> 에이전트와 사용자 모두가 참조하는 프로세스 정책 문서입니다.

---

## 1. 프로젝트 라이프사이클

```
docs/PRD.md 작성
  → Orchestrator (PHASE 1~4.5)
    → PRD 분석 → plan.md → ROADMAP.md → 프로젝트 초기화
  → Planner (PHASE 5)
    → sprints/{sprint}/GOAL.md 생성
  → Implementer (PHASE 6)
    → GOAL.md 기준 구현
  → Validator (PHASE 7~10)
    → 검증 → 수동 테스트 → PR 생성 → 다음 스프린트
  → deploy-prod
    → 프로덕션 배포
```

### 전체 흐름도

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌──────────┐    ┌──────────┐
│   PRD   │ →  │  Plan   │ →  │ ROADMAP │ →  │  Init    │ →  │  GOAL    │
│  분석   │    │  생성   │    │  세분화 │    │ (4.5)    │    │  작성    │
│ PHASE 1 │    │ PHASE 2 │    │ PHASE 4 │    │ 초기화   │    │ PHASE 5  │
└─────────┘    └─────────┘    └─────────┘    └──────────┘    └──────────┘
                                                                   │
                                                                   ▼
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌──────────┐    ┌──────────┐
│  배포   │ ←  │  다음   │ ←  │  PR     │ ←  │  수동    │ ←  │  구현    │
│ deploy  │    │ Sprint  │    │  생성   │    │  테스트  │    │  실행    │
│         │    │ PHASE 10│    │ PHASE 9 │    │ PHASE 8  │    │ PHASE 6  │
└─────────┘    └─────────┘    └─────────┘    └──────────┘    └──────────┘
                    │                                              ▲
                    └── PHASE 5로 반복 ──────────────────────────────┘
```

---

## 2. Hotfix vs Sprint 의사결정

수정사항이 발생하면 **반드시 Hotfix vs Sprint 판단을 먼저** 수행합니다.

### 판단 기준

| 기준 | Hotfix | Sprint |
|------|--------|--------|
| 긴급도 | 프로덕션 장애/버그 | 새 기능, 개선 |
| 변경 범위 | 파일 3개 이하, 코드 50줄 이하 | 파일 4개 이상 또는 50줄 초과 |
| DB 변경 | 없음 | 있을 수 있음 |
| 새 의존성 | 없음 | 있을 수 있음 |

### Hotfix 프로세스

```
1. 현재 브랜치 기반 hotfix 브랜치 생성
   git checkout -b {현재브랜치}_hotfix/{설명}

2. 수정 구현 (sprint-planner 불필요)

3. hotfix-close 에이전트 실행
   → 경량 코드 리뷰 + 타겟 검증 + 베이스 브랜치 PR 생성

4. 머지 후 역머지
   git checkout {개발 브랜치}
   git merge {베이스 브랜치}
```

### Sprint 프로세스

```
1. Planner → GOAL.md 생성 (PHASE 5)
2. Implementer → 구현 (PHASE 6)
3. Validator → 검증 + PR (PHASE 7~10)
4. deploy-prod → 프로덕션 배포
```

---

## 3. Git 브랜치 전략

### Sprint 흐름

```
{현재브랜치}_{CURRENT_SPRINT}  →  PR to 베이스 브랜치  →  배포
```

### Hotfix 흐름

```
{현재브랜치}_hotfix/{설명}  →  PR to 베이스 브랜치  →  배포  →  스프린트 브랜치에 역머지
```

### 브랜치 명명 규칙

| 용도 | 패턴 | 예시 |
|------|------|------|
| 스프린트 | `{현재브랜치}_{CURRENT_SPRINT}` | `main_sprint-01` |
| 핫픽스 | `{현재브랜치}_hotfix/{설명}` | `main_hotfix/login-fix` |
| 메인 | `main` | — |

---

## 4. 에이전트 사용 가이드

### 에이전트별 역할

| 에이전트 | PHASE | 역할 | 모델 |
|----------|-------|------|------|
| orchestrator | 1~4.5 | PRD 분석, plan.md, ROADMAP.md, 초기화 | opus |
| planner | 5 | GOAL.md 작성 | opus |
| implementer | 6 | 기능 구현 | opus |
| validator | 7~10 | 검증, PR 생성, 스프린트 전환 | sonnet |
| hotfix-close | 독립 | 핫픽스 마무리 | sonnet |
| deploy-prod | 독립 | 프로덕션 배포 | sonnet |

### 에이전트 호출 방법

에이전트는 **Agent 도구**로 호출합니다 (Skill 도구가 아님).

```
# 직접 실행
.claude/agents/{에이전트}.md와 docs/STATUS.md를 읽고 ...

# /next 커맨드로 다음 단계 자동 안내
/next
```

### 커맨드 사용

```
# Sprint 구현 오케스트레이터
/sprint-dev sprint-01
```

---

## 5. 검증 매트릭스

| 검증 항목 | Sprint | Hotfix | Deploy |
|-----------|--------|--------|--------|
| 빌드 성공 | ✅ 자동 | ✅ 자동 | ✅ 자동 |
| lint/타입체크 | ✅ 자동 | — | — |
| 단위 테스트 | ✅ 자동 | ✅ 타겟 | ✅ 전체 |
| API 엔드포인트 | ✅ 자동 | ✅ 타겟 | ✅ 전체 |
| 수동 UI 테스트 | ⚠️ 수동 | ⚠️ 타겟 | ⚠️ 수동 |
| 헬스체크 | — | — | ✅ 자동 |

범례:
- ✅ 자동: 에이전트가 자동 실행
- ✅ 타겟: 변경 관련만 자동 실행
- ⚠️ 수동: 사용자가 직접 수행
- —: 해당 없음

---

## 6. 코드 리뷰 체크리스트

### Critical (배포 차단)
- [ ] 보안 취약점 (하드코딩된 시크릿, SQL injection, XSS)
- [ ] 데이터 유실 가능성
- [ ] 인증/권한 우회

### High (수정 권장)
- [ ] 성능 이슈 (N+1 쿼리, 불필요한 루프)
- [ ] 에러 핸들링 누락 (외부 API 호출, DB 연결)
- [ ] 테스트 커버리지 부족

### Medium (기록)
- [ ] 코딩 스타일 불일치
- [ ] 불필요한 코드/import
- [ ] 주석 부족 (복잡한 로직)

---

## 7. 커밋 메시지 규칙

### Sprint 중간 커밋

```
wip: [{sprint-name}] {기능명}
```

### Sprint 최종 커밋 (Validator)

```
feat: [{sprint-name}] {목표 요약}

- 구현 기능 1
- 구현 기능 2

Sprint: {sprint-name}
```

### Hotfix 커밋

```
fix: {핫픽스 설명}

Hotfix: {브랜치명}
```

---

## 8. 문서 구조

```
프로젝트 루트/
├── docs/PRD.md                              ← 프로젝트 요구사항
├── plan.md                             ← 기능 분석 결과 (Orchestrator 생성)
├── docs/STATUS.md                           ← 파이프라인 상태 (공유 상태 파일)
├── CLAUDE.md                           ← 코딩 원칙, 빌드 명령 (claude /init)
├── .gitignore
│
├── sprints/
│   ├── ROADMAP.md                      ← 전체 스프린트 로드맵
│   ├── TECH_DEBT.md                    ← 누적 기술 부채 중앙 관리
│   ├── sprint-01/
│   │   ├── GOAL.md                     ← 구현 명세서 (Planner 생성)
│   │   ├── DONE.md                     ← 완료 보고서 (Validator 생성)
│   │   └── OUT_OF_SCOPE.md             ← 범위 외 발견사항
│   └── sprint-02/
│       └── ...
│
└── .claude/
    ├── settings.json                   ← 권한 설정
    ├── agents/
    │   ├── orchestrator.md             ← PHASE 1~4.5
    │   ├── planner.md                  ← PHASE 5
    │   ├── implementer.md              ← PHASE 6
    │   ├── validator.md                ← PHASE 7~10
    │   ├── hotfix-close.md             ← 핫픽스 마무리
    │   └── deploy-prod.md              ← 프로덕션 배포
    ├── commands/
    │   ├── sprint-dev.md               ← Sprint 구현 오케스트레이터
    │   ├── status.md                   ← /status — 현재 상태 요약
    │   ├── next.md                     ← /next — 다음 에이전트 안내
    │   ├── rollback.md                 ← /rollback — PHASE 롤백
    │   ├── sprint-log.md               ← /sprint-log — 스프린트 종합 요약
    │   └── debt.md                     ← /debt — Tech Debt 보고
    └── rules/
        ├── sprint-workflow.md          ← Sprint/Hotfix 워크플로우 규칙
        ├── coding-principles.md        ← 코딩 원칙 (paths 기반 자동 활성화)
        └── dev-process.md              ← 개발 프로세스 정책 (이 문서)
```

---

## 9. 스프린트 실행 상세

### 9.1 계획 단계 (PHASE 1~5)

1. **docs/PRD.md 작성** (사용자)
   - 목적 & 배경, 핵심 기능, 기술 스택, MVP 기준, 제약 조건

2. **Orchestrator 실행** (PHASE 1~4.5)
   - PRD 분석 → plan.md 생성 → 사용자 확인 → ROADMAP.md 생성
   - 프로젝트 초기화 + CLAUDE.md 생성

3. **Planner 실행** (PHASE 5)
   - ROADMAP.md 기준으로 GOAL.md 생성
   - 기능 체크리스트, 완료 조건, 예상 산출물, 수동 테스트 시나리오

### 9.2 구현 단계 (PHASE 6)

```
기능별 구현 루프:
  1. GOAL.md 체크리스트에서 다음 기능 확인
  2. 구현
  3. GOAL.md [ ] → [x] 업데이트
  4. 중간 커밋: wip: [{sprint}] {기능명}
  5. 반복
```

규칙:
- GOAL.md 범위 밖 기능 → OUT_OF_SCOPE.md에 기록
- CLAUDE.md 코딩 원칙 준수
- karpathy-guidelines 준수 (단순함 우선, 수술적 변경)

### 9.3 검증 단계 (PHASE 7~8)

1. **자동 검증** (PHASE 7)
   - 빌드, lint, 타입체크, 단위 테스트, API 응답
   - 실패 시: 명백한 오류 직접 수정 → 3회 실패 시 Implementer로 롤백

2. **수동 테스트** (PHASE 8)
   - GOAL.md의 수동 테스트 시나리오 기반
   - 사용자가 직접 테스트 후 '통과' 또는 '수정 필요' 입력

### 9.4 종료 단계 (PHASE 9~10)

1. **DONE.md 생성 + PR 생성** (PHASE 9)
2. **다음 스프린트 전환** (PHASE 10)
   - CURRENT_SPRINT 업데이트 → PHASE 5로 복귀

---

## 10. 배포 프로세스

### Sprint 배포

```
Sprint 완료 (PHASE 10)
  → deploy-prod 에이전트 실행
    → 사전 점검 (빌드, 테스트, 완료된 스프린트 확인)
    → main PR 생성
    → 배포 후 검증 가이드 제공
```

### Hotfix 배포

```
Hotfix 구현 완료
  → hotfix-close 에이전트 실행
    → 경량 코드 리뷰 + 타겟 검증
    → 베이스 브랜치 PR 생성
    → 머지 후 역머지 안내
```

### 롤백

문제 발생 시:
```bash
git revert {merge_commit_hash}
git push origin main
```

---

## 11. 세션 재개

세션이 끊겼을 때:

1. `/status` 실행 → 현재 상태 확인
2. `/next` 실행 → 다음 에이전트 명령어 확인
3. 해당 명령어 실행

또는 직접:
```
docs/STATUS.md를 읽고 현재 PHASE에 맞는 에이전트를 실행해줘.
```

---

## 12. 커맨드 사용 가이드

| 커맨드 | 용도 | 사용 시점 |
|------|------|----------|
| `/status` | 현재 파이프라인 상태 요약 | 언제든지 |
| `/next` | 다음 실행할 에이전트 안내 | 다음 단계가 불확실할 때 |
| `/rollback` | 특정 PHASE로 되돌리기 | 계획/구현을 다시 하고 싶을 때 |
| `/sprint-log` | 현재 스프린트 종합 요약 | 스프린트 상태 파악 시 |
| `/debt` | Tech Debt 종합 보고 | 기술 부채 점검 시 |

---

## 13. 프로젝트 시작 체크리스트

새 프로젝트를 시작할 때:

- [ ] docs/PRD.md 작성 (목적, 기능, 기술 스택, MVP, 제약 조건)
- [ ] Orchestrator 실행 (PHASE 1~4.5)
- [ ] plan.md 확인 및 수정
- [ ] ROADMAP.md 확인
- [ ] 프로젝트 초기화 (PHASE 4.5)
- [ ] CLAUDE.md 생성 (`claude /init` 권장)
- [ ] `.claude/rules/coding-principles.md`에 기술 스택 기입
- [ ] 첫 스프린트 시작 (Planner → Implementer → Validator)
