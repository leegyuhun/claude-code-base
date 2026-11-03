# Condition-Based Waiting

## 개요

임의 Sleep 값은 타이밍을 추측한다. 빠른 머신에선 통과하고 느린 머신이나 부하 시 실패하는
flaky 동작을 만든다.

**실제로 기다려야 할 조건을 기다려라. 예상 시간을 기다리지 마라.**

## 적용 시점

- 코드나 테스트에 `sleep(N)` 또는 이벤트 루프 펌핑 반복 루프가 있을 때
- 비동기 동작(스레드, 타이머, DB 연결, 네트워크 요청)이 완료되길 기다릴 때
- "어떤 상태가 됐으면" 조건이 있을 때

**사용하지 말 것:**
- 실제 타이밍 동작을 테스트할 때 (예: 디바운스, 주기 타이머 간격 자체가 검증 대상)
- 이 경우에는 WHY를 반드시 주석으로 명시

## 핵심 패턴

아래 예시는 의사코드(Python 풍)다. 프로젝트 언어의 관용구로 옮겨 쓴다.

```python
# ❌ 잘못된 방식: 임의 시간 대기
sleep(0.5)
if data_ready:
    process_data()

# ✅ 올바른 방식: 실제 조건 대기
deadline = now() + 5.0          # 최대 5초
while not data_ready:
    if now() > deadline:
        raise TimeoutError("데이터 준비 타임아웃")
    sleep(0.01)                  # 폴링 간격 (짧게)
process_data()
```

## 빈출 대기 패턴

### 스레드/작업 완료 대기
```python
# ❌ 잘못된 방식
worker = start_worker()
sleep(1.0)                       # "대충 1초면 되겠지"
process_result()

# ✅ 올바른 방식: 완료 신호를 직접 기다린다
worker = start_worker()
worker.join()                    # 또는 await task / future.result()
process_result()
```

### DB 상태 조건 대기
```python
# 특정 상태가 될 때까지 DB를 폴링해야 할 때
def wait_for_status(target, timeout_s):
    deadline = now() + timeout_s
    while True:
        status = query("SELECT status FROM job WHERE id = ?", job_id)  # 매번 새로 조회
        if status == target:
            return
        if now() > deadline:
            raise TimeoutError(f'상태 "{target}" 대기 타임아웃')
        sleep(0.1)
```

### 화면/컴포넌트 준비 대기
```python
# ❌ 잘못된 방식
report_view.show()
sleep(0.2)
report_view.print()

# ✅ 올바른 방식: 준비 플래그(또는 ready 이벤트) 확인
report_view.show()
wait_until(lambda: report_view.is_ready, timeout_s=3.0)
report_view.print()
```

## 임의 Sleep이 맞는 경우

```python
# 타이머가 100ms 간격으로 틱하는 동작 자체를 테스트할 때
# → "100ms 기다려야 타이머가 발동한다"가 테스트 대상이므로 sleep 정당
sleep(0.15)  # 타이머 1회 발동 확인용 — 100ms 간격 타이머 대기
```

**이 경우 반드시:**
1. 트리거 조건을 먼저 기다린 후
2. 알려진 타이밍 기반으로 (추측 아님)
3. 이유를 주석으로 명시

## 자주 하는 실수

| 실수 | 해결 |
|------|------|
| 폴링 간격이 너무 짧음 (1ms) | 10~50ms 정도로 조정 |
| 타임아웃 없음 | 항상 최대 대기 시간 지정 |
| 루프 안에서 오래된 데이터 사용 | 루프 안에서 매번 새로 조회 |

## 핵심 원칙

**실제로 기다려야 할 조건이 무엇인지 파악하고, 그 조건이 충족될 때까지 기다려라.**
임의 시간은 추측이다. 조건은 사실이다.
