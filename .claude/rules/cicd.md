---
paths:
  - ".github/**"
  - "Dockerfile"
  - "docker-compose*.yml"
  - "Jenkinsfile"
---

# CI/CD 파이프라인 규칙 — Java + Spring Boot

> CI/CD 파이프라인 설정 및 운영 정책을 정의합니다.
> 에이전트는 CI/CD 설정을 생성하거나 수정할 때 이 문서를 준수합니다.

---

## 1. 파이프라인 구조

```
코드 Push/PR
  → CI: 빌드 → 단위테스트 → 통합테스트 → E2E테스트 (Playwright) → 코드 품질 검사
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
  build-and-test:
    name: Build & Test
    runs-on: ubuntu-latest

    services:
      mysql:
        image: mysql:8.0
        env:
          MYSQL_ROOT_PASSWORD: test
          MYSQL_DATABASE: testdb
        ports: [ "3306:3306" ]
        options: --health-cmd="mysqladmin ping" --health-interval=10s --health-timeout=5s --health-retries=3

    steps:
      - uses: actions/checkout@v4

      - name: Set up JDK 17
        uses: actions/setup-java@v4
        with:
          java-version: '17'
          distribution: 'temurin'
          cache: maven  # 또는 gradle

      - name: Build (skip tests)
        run: ./mvnw clean package -DskipTests
        # Gradle: ./gradlew build -x test

      - name: Run unit tests
        run: ./mvnw test
        # Gradle: ./gradlew test

      - name: Run integration tests
        run: ./mvnw verify -Pfailsafe
        # Gradle: ./gradlew integrationTest
        env:
          SPRING_DATASOURCE_URL: jdbc:mysql://localhost:3306/testdb
          SPRING_DATASOURCE_USERNAME: root
          SPRING_DATASOURCE_PASSWORD: test

      - name: Upload test results
        uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: test-results
          path: target/surefire-reports/

  e2e-test:
    name: Playwright E2E Tests
    runs-on: ubuntu-latest
    needs: build-and-test

    steps:
      - uses: actions/checkout@v4

      - name: Set up JDK 17
        uses: actions/setup-java@v4
        with:
          java-version: '17'
          distribution: 'temurin'
          cache: maven

      - name: Start application (background)
        run: ./mvnw spring-boot:run &
        env:
          SPRING_PROFILES_ACTIVE: test

      - name: Wait for application startup
        run: |
          timeout 60 bash -c 'until curl -s http://localhost:8080/actuator/health | grep "UP"; do sleep 2; done'

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
        run: npm run test:e2e
        env:
          BASE_URL: http://localhost:8080

      - name: Upload Playwright report
        uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: playwright-report
          path: e2e/playwright-report/

  docker-build:
    name: Docker Build & Push
    runs-on: ubuntu-latest
    needs: [ build-and-test, e2e-test ]
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

      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            ${{ secrets.REGISTRY_URL }}/app:${{ github.sha }}
            ${{ secrets.REGISTRY_URL }}/app:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy:
    name: Deploy
    runs-on: ubuntu-latest
    needs: docker-build
    if: github.ref == 'refs/heads/main'
    environment: production  # GitHub Environments 승인 게이트

    steps:
      - name: Deploy to production
        # 배포 방식에 따라 아래 중 하나 선택:
        # Option A: SSH + docker-compose
        run: |
          echo "배포 명령어를 여기에 작성하세요"
          # ssh user@server "cd /app && docker-compose pull && docker-compose up -d"
```

---

## 3. Dockerfile 표준 — Spring Boot

```dockerfile
# Multi-stage build
FROM eclipse-temurin:17-jdk-alpine AS builder
WORKDIR /app
COPY .mvn/ .mvn/
COPY mvnw pom.xml ./
RUN ./mvnw dependency:go-offline -q

COPY src/ src/
RUN ./mvnw clean package -DskipTests

FROM eclipse-temurin:17-jre-alpine
WORKDIR /app

# 보안: 비루트 사용자로 실행
RUN addgroup -S spring && adduser -S spring -G spring
USER spring:spring

COPY --from=builder /app/target/*.jar app.jar

EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
```

---

## 4. 환경 설정 전략

### `application.yml` 구조
```yaml
# application.yml — 공통 설정
spring:
  profiles:
    active: ${SPRING_PROFILES_ACTIVE:local}

---
# application-local.yml — 로컬 개발용
spring:
  config:
    activate:
      on-profile: local
  datasource:
    url: jdbc:mysql://localhost:3306/devdb

---
# application-test.yml — CI/CD 테스트용
spring:
  config:
    activate:
      on-profile: test
  datasource:
    url: jdbc:h2:mem:testdb  # 또는 CI DB

---
# application-prod.yml — 프로덕션 (시크릿은 환경변수로)
spring:
  config:
    activate:
      on-profile: prod
  datasource:
    url: ${DB_URL}
    username: ${DB_USERNAME}
    password: ${DB_PASSWORD}
```

### GitHub Actions Secrets 관리
```
REGISTRY_URL          — 컨테이너 레지스트리 URL
REGISTRY_USERNAME     — 레지스트리 사용자명
REGISTRY_PASSWORD     — 레지스트리 비밀번호
DB_URL                — 프로덕션 DB URL
DB_USERNAME           — 프로덕션 DB 사용자명
DB_PASSWORD           — 프로덕션 DB 비밀번호
DEPLOY_SSH_KEY        — 배포 서버 SSH 키 (SSH 배포 시)
```

---

## 5. 배포 후 헬스체크

Spring Boot Actuator를 반드시 포함:
```yaml
# application.yml
management:
  endpoints:
    web:
      exposure:
        include: health, info
  endpoint:
    health:
      show-details: when-authorized
```

배포 후 확인 명령:
```bash
curl -f http://{SERVER}/actuator/health
# 응답: {"status":"UP"}
```

---

## 6. CI/CD 운영 규칙

- **main 브랜치 직접 Push 금지** — PR + 리뷰 필수
- **E2E 테스트 실패 시 배포 차단** — 파이프라인 게이트
- **Docker 이미지 태그**: `git SHA` 사용 (latest만 쓰면 추적 불가)
- **시크릿은 GitHub Secrets에만** — `.env` 파일 커밋 금지 (`.gitignore` 등록)
- **배포 환경 격리**: `development` → `staging` → `production` 순서

---

## 7. 에이전트 금지 사항

- ❌ CI/CD 파이프라인에 시크릿 값 하드코딩
- ❌ main 브랜치에 force push
- ❌ 테스트 실패 무시하고 배포 진행
- ❌ Docker 이미지를 빌드 없이 직접 수정
