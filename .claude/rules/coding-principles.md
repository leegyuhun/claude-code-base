---
paths:
  - "src/**"
  - "backend/**"
---

# 코딩 원칙 — Java + Spring Boot

## 기술 스택
# TODO: 프로젝트 초기화(PHASE 4.5) 후 기술 스택을 기입하세요
# 예: Java 17, Spring Boot 3.x, Spring Data JPA, Spring Security 6.x
#     Maven or Gradle, MySQL/PostgreSQL, Redis
#     JUnit 5, Mockito, Playwright (E2E)
#     Lombok, MapStruct, QueryDSL (선택)

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
- 내 변경으로 인해 안 쓰게 된 import/변수/메서드만 제거하라.

### 4. 목표 기반 실행
- 작업을 검증 가능한 목표로 변환하라.
- 다단계 작업은 계획을 먼저 밝혀라.

---

## Spring Boot 패턴

### 레이어 구조
```
Controller → Service → Repository → Entity
           ↕                      ↕
        DTO (Request/Response)   Domain
```
- **Controller**: HTTP 요청/응답만 담당. 비즈니스 로직 금지.
- **Service**: 비즈니스 로직, `@Transactional` 경계 관리.
- **Repository**: JPA / QueryDSL, DB 접근만 담당.
- **DTO**: API 입출력 전용. Entity를 Controller에 직접 노출 금지.
- **Entity**: 도메인 상태만 보유. 비즈니스 로직 최소화.

### 네이밍 규칙
```
Controller     : XxxController.java
Service        : XxxService.java (interface) + XxxServiceImpl.java
Repository     : XxxRepository.java
Entity         : Xxx.java (단수형, ex. Order, User)
DTO(요청)      : XxxRequest.java
DTO(응답)      : XxxResponse.java
범용 DTO       : XxxDto.java
Config         : XxxConfig.java
Exception      : XxxException.java
ExceptionHandler: GlobalExceptionHandler.java
```

### REST API 설계
- URI: 소문자 + 하이픈 (`/api/v1/user-orders`)
- HTTP 메서드: GET(조회), POST(생성), PUT(전체수정), PATCH(부분수정), DELETE(삭제)
- 응답 형식: 공통 응답 래퍼 사용
  ```java
  ApiResponse<T> { boolean success; String message; T data; }
  ```
- 에러 응답: HTTP 상태코드 + `ErrorResponse { code, message, details }`

### 예외 처리
- `@ControllerAdvice` + `@ExceptionHandler`로 중앙 처리
- 커스텀 예외는 `RuntimeException` 상속
- `e.printStackTrace()` 절대 사용 금지 → `log.error("메시지", e)` 사용
- HTTP 상태코드를 예외 클래스에 매핑 (`@ResponseStatus` 또는 핸들러에서 설정)

### JPA 규칙
- Fetch 전략: `LAZY` 기본, `EAGER`는 명시적으로만
- N+1 방지: `@EntityGraph`, `JOIN FETCH`, QueryDSL 사용
- `@Transactional(readOnly = true)` 조회 메서드에 적용
- `@Modifying` + `@Transactional` 벌크 연산에 적용
- BaseEntity (createdAt, updatedAt) 공통 상속 권장

### Lombok 사용 규칙
- `@Data` Entity에 사용 금지 (무한순환 참조, equals/hashCode 문제)
- Entity: `@Getter`, `@NoArgsConstructor(access = PROTECTED)`, `@Builder`
- DTO: `@Getter`, `@Builder`, `@NoArgsConstructor`, `@AllArgsConstructor`
- `@Slf4j` 로거 어노테이션 사용

### 검증 (Validation)
- `@Valid` + `@RequestBody` / `@ModelAttribute`에 Bean Validation 적용
- `@NotNull`, `@NotBlank`, `@Size`, `@Pattern` 등 DTO에 명시
- 커스텀 검증 필요 시 `ConstraintValidator` 구현

---

## 보안

- 시크릿/API 키: `application.yml` 환경변수 참조 (`${ENV_VAR}`) — 코드에 하드코딩 금지
- Spring Security: 인증/인가 설정 명확히. `SecurityFilterChain` Bean으로 관리
- SQL injection: JPA/QueryDSL 파라미터 바인딩 사용. 네이티브 쿼리 문자열 연결 금지
- CORS: `CorsConfigurationSource` Bean으로 명시적으로 관리
- XSS: 입력값 검증 (`@Valid`) + Thymeleaf 자동 이스케이프 활용
- CSRF: REST API는 `csrf().disable()` 허용, 세션 기반이면 활성화
- 비밀번호: `BCryptPasswordEncoder` 사용. 평문 저장 절대 금지

---

## 테스트 원칙

### 테스트 계층
```
단위 테스트   : @ExtendWith(MockitoExtension.class) — Service, 도메인 로직
슬라이스 테스트: @WebMvcTest — Controller / @DataJpaTest — Repository
통합 테스트   : @SpringBootTest — 전체 컨텍스트, DB 연동
E2E 테스트    : Playwright — 브라우저 기반 시나리오 (e2e/ 디렉토리)
```

### 테스트 작성 규칙
- `@SpringBootTest`는 통합 테스트에만 사용 (무겁다)
- 테스트 메서드명: `메서드명_상태_기대결과` (ex. `createOrder_whenOutOfStock_throwsException`)
- Mock 객체: `@MockBean` (스프링 컨텍스트) / `@Mock` (순수 Mockito)
- Given-When-Then 구조 유지

### Playwright E2E 테스트
- 경로: `e2e/` (프로젝트 루트) — Node.js 기반 별도 모듈
- 설정: `playwright.config.ts`에 baseURL, timeout, retry 설정
- 테스트: 핵심 사용자 시나리오만 커버 (로그인, 주요 CRUD 등)
- CI에서 자동 실행: `npm run test:e2e`

---

## 빌드 & 실행
# TODO: CLAUDE.md에 실제 명령어를 기입하세요
```bash
# Maven
./mvnw clean package          # 빌드
./mvnw test                   # 단위/통합 테스트
./mvnw spring-boot:run        # 로컬 실행

# Gradle
./gradlew build               # 빌드
./gradlew test                # 테스트
./gradlew bootRun             # 로컬 실행

# E2E (Playwright)
cd e2e && npm install
npm run test:e2e              # E2E 테스트 실행
npm run test:e2e:headed       # 브라우저 띄워서 실행 (디버깅용)
```

---

## 임시 코드
- 임시 코드 사용 시 TODO 주석 필수
  ```java
  // TODO: [tech-debt] 임시처리 - 이유
  ```
