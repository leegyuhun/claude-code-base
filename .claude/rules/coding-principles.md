---
paths:
  - "src/**"
  - "backend/**"
  - "frontend/**"
  - "app/**"
  - "lib/**"
---

# 코딩 원칙 — Python + React + TypeScript

## 기술 스택
# TODO: 프로젝트 초기화(PHASE 4.5) 후 기술 스택을 기입하세요
# 예: Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Alembic
#     React 18, TypeScript 5.x, Vite, TailwindCSS
#     Node.js 20 LTS, pnpm / npm
#     pytest, Vitest, Playwright (E2E)
#     PostgreSQL / MySQL, Redis (선택)

---

## 핵심 규칙

### 1. 코딩 전에 생각하라
- 가정을 명시적으로 밝혀라. 불확실하면 물어봐라.
- 해석이 여러 개면 제시하라 — 임의로 골라서 진행하지 마라.
- 더 단순한 접근이 있으면 말하라.

### 2. 단순함 우선
- 요청한 것 이상의 기능을 만들지 마라.
- 한 번만 쓰는 코드에 추상화를 만들지 마라.
- 요청하지 않은 "유연성"이나 "설정 가능성"을 넣지 마라.
- 불가능한 시나리오에 대한 에러 처리를 하지 마라.

### 3. 수술적 변경
- 요청과 관련된 코드만 건드려라.
- 주변 코드, 주석, 포맷을 "개선"하지 마라.
- 기존 스타일을 따라라.
- 내 변경으로 인해 안 쓰게 된 import/변수/함수만 제거하라.

### 4. 목표 기반 실행
- 작업을 검증 가능한 목표로 변환하라.
- 다단계 작업은 계획을 먼저 밝혀라.

---

## Python (백엔드) 패턴

### 레이어 구조 (FastAPI 기준)
```
Router (API 엔드포인트)
  → Service (비즈니스 로직)
    → Repository (DB 접근)
      → Model (SQLAlchemy Entity)
  ↕
Schema (Pydantic — 요청/응답 직렬화)
```

### 디렉토리 구조
```
backend/
  app/
    api/v1/routes/      ← APIRouter 단위 분리 (users.py, items.py)
    core/               ← config.py, security.py, dependencies.py
    models/             ← SQLAlchemy 모델 (단수형: user.py, order.py)
    schemas/            ← Pydantic 스키마 (UserCreate, UserResponse 등)
    services/           ← 비즈니스 로직 (user_service.py)
    repositories/       ← DB 접근 (user_repository.py)
    db/                 ← session.py, base.py
  alembic/              ← DB 마이그레이션
  tests/
    unit/
    integration/
    conftest.py
```

### 네이밍 규칙
```
Router 파일     : users.py, items.py (복수형)
Service         : user_service.py / UserService 클래스
Repository      : user_repository.py / UserRepository 클래스
Model           : user.py / User 클래스 (단수형)
Schema          : UserCreate / UserUpdate / UserResponse / UserInDB
Config          : settings.py / Settings 클래스
Exception       : user_exceptions.py / UserNotFoundException
```

### FastAPI 규칙
- **의존성 주입**: `Depends()` 활용, 함수 단위 DI 선호
- **응답 스키마**: `response_model=` 명시 — 내부 모델 노출 금지
- **상태코드**: `status_code=` 명시 (201 생성, 204 삭제 등)
- **비동기**: I/O 작업은 `async def`, 순수 계산은 `def`
- **에러 처리**: `HTTPException` 또는 커스텀 예외 + `@app.exception_handler`

### Pydantic v2 규칙
- `model_config = ConfigDict(from_attributes=True)` — ORM 모드 대체
- `model_validator`, `field_validator` 활용
- 응답 스키마와 요청 스키마 분리 (절대 같은 스키마 재사용 금지)

### SQLAlchemy 2.0 규칙
- `mapped_column()`, `Mapped[]` 타입 힌트 사용
- `async with AsyncSession` 패턴 (비동기 DB)
- N+1 방지: `selectinload`, `joinedload` 명시
- 마이그레이션: Alembic으로 관리 — `models/` 직접 수정 금지, 마이그레이션 파일 생성

### Python 일반 규칙
- 타입 힌트 필수 (`str | None`, `list[int]`, `dict[str, Any]`)
- `print()` 사용 금지 → `logging` 모듈 사용
- `try/except Exception` 광범위 catch 금지 → 구체적 예외 처리
- `.env` 파일로 시크릿 관리, `pydantic-settings`로 로드

---

## TypeScript / React (프론트엔드) 패턴

### 디렉토리 구조
```
frontend/src/
  components/           ← 재사용 가능한 UI 컴포넌트
    common/             ← Button, Input, Modal 등 범용
    feature/            ← 기능별 컴포넌트 (UserCard, OrderList 등)
  pages/                ← 라우트 단위 페이지 컴포넌트
  hooks/                ← 커스텀 훅 (use 접두사)
  services/             ← API 호출 함수 (axios/fetch 래핑)
  store/                ← 전역 상태 (Zustand / Redux Toolkit)
  types/                ← 공용 TypeScript 타입/인터페이스
  utils/                ← 순수 유틸리티 함수
  lib/                  ← 외부 라이브러리 설정 (axios 인스턴스 등)
```

### 컴포넌트 규칙
- **함수형 컴포넌트만** 사용 (클래스형 금지)
- 컴포넌트 파일명: `PascalCase.tsx`
- 훅 파일명: `useCamelCase.ts`
- Props 타입은 `interface XxxProps` 로 선언 (컴포넌트 파일 상단)
- 비즈니스 로직은 커스텀 훅으로 분리 — 컴포넌트는 UI만

### TypeScript 규칙
- `any` 사용 금지 → `unknown` 또는 구체적 타입 사용
- `interface`는 객체/클래스, `type`은 유니온/인터섹션에 사용
- `!` (non-null assertion) 최소화 → 명시적 타입 가드 사용
- API 응답 타입은 `types/api/` 하위에 별도 정의

### 서버 상태 관리 (React Query / TanStack Query)
- API 호출은 `useQuery`, `useMutation` 활용
- 쿼리 키는 `queryKeys` 상수 파일로 중앙 관리
- `staleTime`, `gcTime` 명시적 설정

### 클라이언트 상태 관리 (Zustand)
- 슬라이스 단위로 스토어 분리
- 셀렉터로 필요한 상태만 구독 (리렌더링 최소화)

### API 호출 규칙
- `axios` 인스턴스 중앙화 (`lib/axios.ts`) — baseURL, interceptor 설정
- 서비스 함수 단위로 분리 (`services/userService.ts`)
- 에러는 인터셉터에서 중앙 처리 (401 → 리다이렉트 등)

---

## 보안
- **백엔드**: 시크릿은 `.env` + `pydantic-settings` 관리, 코드 하드코딩 금지
- **프론트엔드**: API 키를 클라이언트 코드에 포함 금지 → 백엔드 프록시 사용
- **인증**: JWT AccessToken (단기) + RefreshToken (장기) 패턴
- **SQL injection**: SQLAlchemy ORM 파라미터 바인딩 — raw SQL 문자열 연결 금지
- **XSS**: React JSX 자동 이스케이프 활용, `dangerouslySetInnerHTML` 사용 금지
- **CORS**: FastAPI `CORSMiddleware`로 허용 출처 명시적 설정

---

## 테스트 원칙

### 테스트 계층
```
Python 단위 테스트    : pytest — 서비스/유틸 로직
Python 통합 테스트   : pytest + httpx.AsyncClient — API 엔드포인트
프론트엔드 단위 테스트: Vitest + React Testing Library — 컴포넌트/훅
E2E 테스트           : Playwright — 핵심 사용자 시나리오 (e2e/ 디렉토리)
```

### 테스트 작성 규칙
- 테스트 파일명: `test_xxx.py` (Python) / `xxx.test.ts` (TS) / `xxx.spec.ts` (E2E)
- `conftest.py`: fixture 중앙 관리 (DB 세션, 클라이언트, 인증 토큰 등)
- Given-When-Then / Arrange-Act-Assert 구조 유지
- 실제 DB 대신 테스트 DB 사용 (`TEST_DATABASE_URL`)

### Playwright E2E 테스트
- 경로: `e2e/` (프로젝트 루트) — 별도 Node.js 모듈
- 설정: `playwright.config.ts`에 baseURL, timeout, retry, webServer 설정
- `webServer` 옵션으로 테스트 서버 자동 기동 가능
- 테스트: 핵심 사용자 흐름만 (로그인, 주요 CRUD 등)
- CI에서 자동 실행: `npx playwright test`

---

## 빌드 & 실행
# TODO: CLAUDE.md에 실제 명령어를 기입하세요
```bash
# 백엔드 (Python/FastAPI)
cd backend
pip install -r requirements.txt   # 또는 poetry install / uv sync
uvicorn app.main:app --reload      # 로컬 실행
pytest                             # 테스트
alembic upgrade head               # DB 마이그레이션 적용

# 프론트엔드 (React + TypeScript)
cd frontend
npm install                        # 또는 pnpm install
npm run dev                        # 로컬 실행 (Vite)
npm run build                      # 프로덕션 빌드
npm run test                       # Vitest 단위 테스트
npm run typecheck                  # tsc --noEmit

# E2E (Playwright)
cd e2e
npm install
npx playwright test                # E2E 테스트
npx playwright test --headed       # 브라우저 띄워서 실행 (디버깅)
npx playwright show-report         # 리포트 확인
```

---

## 임시 코드
- 임시 코드 사용 시 TODO 주석 필수
  ```python
  # TODO: [tech-debt] 임시처리 - 이유
  ```
  ```typescript
  // TODO: [tech-debt] 임시처리 - 이유
  ```
