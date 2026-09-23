# Root Cause Tracing

## 개요

버그는 종종 콜 스택 깊은 곳에서 발생한다. 본능적으로 오류가 나타나는 위치를 고치려 하지만,
그건 증상 치료다. 콜 체인을 역방향으로 추적해 원래 트리거를 찾고, **원인 위치**에서 수정해야 한다.

## 적용 시점

- 오류가 실제 코드 실행 깊은 곳에서 발생할 때
- 잘못된 값이 어디서 왔는지 불명확할 때
- 쿼리 파라미터나 폼 입력값이 예상과 달리 잘못됐을 때

## 추적 절차

### 1. 증상 관찰
```
예: 쿼리 실행에서 'Invalid column name' 오류
예: 그리드에 표시된 금액이 0
예: NullPointerException / Segmentation fault / AttributeError: 'NoneType'
```

### 2. 직접 원인 찾기
오류가 발생한 코드 위치 확인 (런타임 메시지의 스택 트레이스 참고)

### 3. "이걸 호출한 것은?" 반복 추적

아래 예시는 의사코드(Python 풍)다.

```python
# 예: 잘못된 SQL 파라미터 추적
# 증상: 쿼리 실행에서 오류
class OrderRepository:
    def save_order(self, order_id):
        # order_id가 0으로 들어옴
        execute("UPDATE orders SET ... WHERE order_id = ?", order_id)

# 한 단계 위: save_order를 부른 곳
class OrderView:
    def on_save_click(self):
        self.repo.save_order(self.order_id)   # order_id를 어디서 가져오는가?

# 한 단계 위: order_id가 초기화됐는가?
    def __init__(self):
        self.order_id = 0                     # 초기화 누락! (기본값 0)
# 원인: 화면 초기화에서 order_id를 제대로 설정하지 않음
# 수정 위치: 화면 초기화 또는 표시 시점
```

### 4. 원인 위치에서 수정

증상이 나타나는 곳에서 수정하지 말고,
잘못된 값이 **처음 생성되는 곳**에서 수정한다.

### 5. 방어 계층 추가 (수정 후)

원인 위치 수정 후, 동일 문제가 다시 발생하지 않도록 경계마다 검증 추가:
```python
# 원인 수정 후 방어 계층:
def save_order(self, order_id):
    if order_id <= 0:
        raise ValidationError("유효하지 않은 주문 ID")
    ...
```

## 빈출 추적 패턴

### 파일 인코딩 손상 추적
```
증상: 파일을 열면 비ASCII 문자(한글 등)가 깨짐
추적: 어떤 도구/스크립트로 파일을 수정했는가? 원본 인코딩은 무엇이었는가?
      → 원본과 다른 인코딩으로 다시 저장 → 바이트 손상
원인: 인코딩을 지정하지 않은 읽기/쓰기
수정: git checkout -- <파일> 로 원본 복구 후, 원본 인코딩을 명시해 다시 수정
```

### null 참조 추적
```
증상: null/nil/None 참조 오류
추적: 어느 객체가 비어 있는가? → 생성 시점 확인
      → 해제 후 재접근? → 비동기 작업 종료 이후 접근?
원인: 객체 생명주기 불일치
수정: null 가드 + 생명주기 재설계
```

### SQL 방언 오류 추적 (다중 DBMS 프로젝트)
```
증상: 특정 DBMS에서만 SQL 실행 오류 (예: 한쪽에만 있는 함수 사용)
추적: 어느 쿼리에서 발생? → 프로젝트 표준 분기 방식을 따랐는가?
원인: 한 DBMS 전용 문법 사용
수정: 양쪽에서 동작하는 SQL로 교체하거나 프로젝트 표준 분기 적용 (CLAUDE.md)
```

### 리소스 핸들 누수 추적
```
증상: 장시간 실행 후 "too many open files" / 핸들 생성 실패 / 커넥션 풀 고갈
추적: 획득 후 해제가 호출됐는가?
      → 예외 경로에서 해제가 건너뛰어지지 않는가?
원인: 획득/해제 쌍 누락
수정: try/finally, using, with, defer 등으로 해제 보장
```

## 진단 로그 추가 (추적 불가 시)

콜 체인 추적이 어려울 때 각 경계에서 로그 추가:

```python
def save_order(self, order_id):
    log.debug("OrderRepository.save_order order_id=%s", order_id)
    ...

def on_save_click(self):
    log.debug("OrderView.on_save_click order_id=%s", self.order_id)
    self.repo.save_order(self.order_id)
```

로그에서 값이 잘못된 최초 지점 = 수정 위치.

## 핵심 원칙

**오류가 나타나는 곳에서 수정하지 마라. 잘못된 값이 시작되는 곳에서 수정하라.**
