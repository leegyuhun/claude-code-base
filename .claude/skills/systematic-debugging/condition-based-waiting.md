# Condition-Based Waiting (Delphi / YSR)

## 개요

임의 Sleep 값은 타이밍을 추측한다. 빠른 머신에선 통과하고 느린 머신이나 부하 시 실패하는
flaky 동작을 만든다.

**실제로 기다려야 할 조건을 기다려라. 예상 시간을 기다리지 마라.**

## 적용 시점

- 코드에 `Sleep(N)` 또는 `Application.ProcessMessages` 반복 루프가 있을 때
- 비동기 동작(쓰레드, 타이머, DB 연결)이 완료되길 기다릴 때
- "어떤 상태가 됐으면" 조건이 있을 때

**사용하지 말 것:**
- 실제 타이밍 동작을 테스트할 때 (예: 디바운스, 주기 타이머 간격 자체가 검증 대상)
- 이 경우에는 WHY를 반드시 주석으로 명시

## 핵심 패턴

```pascal
// ❌ 잘못된 방식: 임의 시간 대기
Sleep(500);
if FDataReady then ProcessData;

// ✅ 올바른 방식: 실제 조건 대기
ATimeout := GetTickCount + 5000; // 최대 5초
while not FDataReady do
begin
  if GetTickCount > ATimeout then
    raise Exception.Create('데이터 준비 타임아웃');
  Application.ProcessMessages;
  Sleep(10); // 폴링 간격 (짧게)
end;
ProcessData;
```

## YSR 빈출 대기 패턴

### 쓰레드 작업 완료 대기
```pascal
// ❌ 잘못된 방식
FWorkerThread := TWorkerThread.Create(nil);
Sleep(1000); // "대충 1초면 되겠지"
ProcessResult;

// ✅ 올바른 방식: FreeOnTerminate=False로 만들고 WaitFor
FWorkerThread := TWorkerThread.Create(nil);
FWorkerThread.WaitFor; // 완료까지 정확히 대기
FWorkerThread.Free;
ProcessResult;
```

### DB 쿼리 결과 조건 대기
```pascal
// 특정 상태가 될 때까지 DB를 폴링해야 할 때
procedure WaitForStatus(ATargetStatus: string; ATimeoutMs: Integer);
var
  ADeadline: Cardinal;
begin
  ADeadline := GetTickCount + Cardinal(ATimeoutMs);
  repeat
    qryStatus.Close;
    qryStatus.Open;
    if qryStatus.FieldByName('status').AsString = ATargetStatus then Exit;
    if GetTickCount > ADeadline then
      raise Exception.CreateFmt('상태 "%s" 대기 타임아웃', [ATargetStatus]);
    Application.ProcessMessages;
    Sleep(100);
  until False;
end;
```

### 폼/컴포넌트 준비 대기
```pascal
// ❌ 잘못된 방식
frmReport.Show;
Sleep(200);
frmReport.PrintReport;

// ✅ 올바른 방식: 준비 플래그 확인
frmReport.Show;
ADeadline := GetTickCount + 3000;
while not frmReport.IsReady do
begin
  if GetTickCount > ADeadline then
    raise Exception.Create('보고서 폼 준비 타임아웃');
  Application.ProcessMessages;
  Sleep(10);
end;
frmReport.PrintReport;
```

## 임의 Sleep이 맞는 경우

```pascal
// 타이머가 100ms 간격으로 틱하는 동작 자체를 테스트할 때
// → "100ms 기다려야 타이머가 발동한다"가 테스트 대상이므로 Sleep 정당
Sleep(150); // 타이머 1회 발동 확인용 — 100ms 간격 타이머 대기
```

**이 경우 반드시:**
1. 트리거 조건을 먼저 기다린 후
2. 알려진 타이밍 기반으로 (추측 아님)
3. 이유를 주석으로 명시

## 자주 하는 실수

| 실수 | 해결 |
|------|------|
| 폴링 간격이 너무 짧음 (Sleep(1)) | Sleep(10~50) 정도로 조정 |
| 타임아웃 없음 | 항상 최대 대기 시간 지정 |
| 루프 안에서 오래된 데이터 사용 | 루프 안에서 매번 새로 조회 |

## 핵심 원칙

**실제로 기다려야 할 조건이 무엇인지 파악하고, 그 조건이 충족될 때까지 기다려라.**
임의 시간은 추측이다. 조건은 사실이다.
