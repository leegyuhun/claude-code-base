---
paths:
  - ".github/**"
  - "Dockerfile"
  - "docker-compose*.yml"
---

# CI/CD 파이프라인 규칙 — Python + React + TypeScript

> CI/CD 파이프라인 설정 및 운영 정책을 정의합니다.
> 에이전트는 CI/CD 설정을 생성하거나 수정할 때 이 문서를 준수합니다.

---

## 1. 파이프라인 구조

```
코드 Push/PR
  → CI: 백엔드 빌드/테스트 → 프론트엔드 빌드/테스트 → E2E (Playwright) → 타입체크/린트
  → CD: Docker 빌드 → 이미지 Push → 배포 (main 브랜치 머지 시)
```

### 브랜치별 트리거
```
PR (→ main/develop) : CI 전체 실행 (배포 제외)
push → develop      : CI 전체 + staging 배포
push → main         : CI 전체 + production 배포
```

---

## 2. GitHub Actions — 표준 워크플로우

### `.github/workflows/ci.yml` 템플릿

```yaml
name: CI Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  backend:
    name: Backend (Python)
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: testdb
        ports: [ "5432:5432" ]
        options: --health-cmd pg_isready --health-interval 10s --health-timeout 5s --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'  # 또는 poetry

      - name: Install dependencies
        working-directory: backend
        run: pip install -r requirements.txt
        # poetry: poetry install --no-root
        # uv: uv sync

      - name: Run linting (ruff)
        working-directory: backend
        run: ruff check . && ruff format --check .

      - name: Run type check (mypy)
        working-directory: backend
        run: mypy app/

      - name: Run tests (pytest)
        working-directory: backend
        run: pytest --cov=app --cov-report=xml -v
        env:
          DATABASE_URL: postgresql+asyncpg://test:test@localhost:5432/testdb
          SECRET_KEY: test-secret-key

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        if: always()
        with:
          file: backend/coverage.xml

  frontend:
    name: Frontend (React + TypeScript)
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        working-directory: frontend
        run: npm ci

      - name: Type check
        working-directory: frontend
        run: npm run typecheck

      - name: Lint (ESLint)
        working-directory: frontend
        run: npm run lint

      - name: Unit tests (Vitest)
        working-directory: frontend
        run: npm run test

      - name: Build
        working-directory: frontend
        run: npm run build

  e2e-test:
    name: E2E Tests (Playwright)
    runs-on: ubuntu-latest
    needs: [ backend, frontend ]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Start backend (background)
        working-directory: backend
        run: |
          pip install -r requirements.txt
          uvicorn app.main:app --host 0.0.0.0 --port 8000 &
          timeout 30 bash -c 'until curl -s http://localhost:8000/health; do sleep 1; done'
        env:
          DATABASE_URL: sqlite+aiosqlite:///./test.db
          ENVIRONMENT: test

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: e2e/package-lock.json

      - name: Install Playwright
        working-directory: e2e
        run: |
          npm ci
          npx playwright install --with-deps chromium

      - name: Run Playwright E2E tests
        working-directory: e2e
        run: npx playwright test
        env:
          BASE_URL: http://localhost:3000
          API_URL: http://localhost:8000

      - name: Upload Playwright report
        uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: playwright-report
          path: e2e/playwright-report/

  docker-build:
    name: Docker Build & Push
    runs-on: ubuntu-latest
    needs: [ backend, frontend, e2e-test ]
    if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/develop'

    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ secrets.REGISTRY_URL }}
          username: ${{ secrets.REGISTRY_USERNAME }}
          password: ${{ secrets.REGISTRY_PASSWORD }}

      - name: Build and push backend image
        uses: docker/build-push-action@v5
        with:
          context: ./backend
          push: true
          tags: |
            ${{ secrets.REGISTRY_URL }}/backend:${{ github.sha }}
            ${{ secrets.REGISTRY_URL }}/backend:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Build and push frontend image
        uses: docker/build-push-action@v5
        with:
          context: ./frontend
          push: true
          tags: |
            ${{ secrets.REGISTRY_URL }}/frontend:${{ github.sha }}
            ${{ secrets.REGISTRY_URL }}/frontend:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy:
    name: Deploy
    runs-on: ubuntu-latest
    needs: docker-build
    if: github.ref == 'refs/heads/main'
    environment: production

    steps:
      - name: Deploy to production
        run: |
          echo "배포 명령어를 여기에 작성하세요"
          # ssh user@server "cd /app && docker-compose pull && docker-compose up -d"
```

---

## 3. Dockerfile 표준

### 백엔드 (Python/FastAPI)
```dockerfile
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

FROM python:3.12-slim
WORKDIR /app

# 보안: 비루트 사용자
RUN adduser --disabled-password --gecos '' appuser
USER appuser

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --chown=appuser:appuser . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 프론트엔드 (React/Vite + nginx)
```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

---

## 4. 환경 설정 전략

### 백엔드 환경 파일 구조
```
backend/
  .env.example        ← 커밋 O, 값 없음 (키 목록만)
  .env.local          ← 커밋 X, 로컬 개발용
  .env.test           ← 커밋 O, CI 테스트용 (시크릿 없는 것만)
```

### `pydantic-settings` 설정 패턴
```python
# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
    DATABASE_URL: str
    SECRET_KEY: str
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

settings = Settings()
```

### 프론트엔드 환경 파일 (Vite)
```
frontend/
  .env                ← 커밋 O, 공통 기본값 (VITE_APP_NAME 등)
  .env.local          ← 커밋 X, 로컬 개발용
  .env.production     ← 커밋 O (VITE_ prefix만, 민감정보 금지)
```

### GitHub Actions Secrets 관리
```
REGISTRY_URL          — 컨테이너 레지스트리 URL
REGISTRY_USERNAME     — 레지스트리 사용자명
REGISTRY_PASSWORD     — 레지스트리 비밀번호
DATABASE_URL          — 프로덕션 DB URL
SECRET_KEY            — JWT 시크릿 키
DEPLOY_SSH_KEY        — 배포 서버 SSH 키 (SSH 배포 시)
```

---

## 5. 배포 후 헬스체크

### FastAPI 헬스체크 엔드포인트
```python
# app/api/v1/routes/health.py
@router.get("/health")
async def health_check():
    return {"status": "ok"}
```

배포 후 확인:
```bash
curl -f https://{SERVER}/health
# 응답: {"status":"ok"}
```

---

## 6. CI/CD 운영 규칙

- **main 브랜치 직접 Push 금지** — PR + 리뷰 필수
- **E2E 테스트 실패 시 배포 차단** — 파이프라인 게이트
- **Docker 이미지 태그**: `git SHA` 사용 (`:latest`만 쓰면 추적 불가)
- **시크릿은 GitHub Secrets에만** — `.env` 파일 커밋 금지, `.gitignore` 등록
- **배포 환경 격리**: `development` → `staging` → `production` 순서

---

## 7. 에이전트 금지 사항

- ❌ CI/CD 파이프라인에 시크릿 값 하드코딩
- ❌ main 브랜치에 force push
- ❌ 테스트 실패 무시하고 배포 진행
- ❌ Docker 이미지를 빌드 없이 직접 수정
