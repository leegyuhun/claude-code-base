# Root Cause Tracing (Delphi / YSR)

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
예: TtsQuery.ExecSQL에서 'Invalid column name' 오류
예: 그리드에 표시된 금액이 0
예: EAccessViolation at address 00000000
```

### 2. 직접 원인 찾기
오류가 발생한 코드 위치 확인 (Delphi 런타임 메시지에서 주소 또는 스택 트레이스 참고)

### 3. "이걸 호출한 것은?" 반복 추적

```pascal
// 예: 잘못된 SQL 파라미터 추적
// 증상: ExecSQL에서 오류
procedure TdmOrder.SaveOrder;
begin
  // SQL에 AOrderID가 0으로 들어옴
  SQL.Add('WHERE order_id = ' + IntToStr(AOrderID));
  ExecSQL;
end;

// 한 단계 위: TdmOrder.SaveOrder를 부른 곳
procedure TfrmOrder.btnSaveClick(Sender: TObject);
begin
  dmOrder.SaveOrder; // AOrderID를 어디서 가져오는가?
end;

// 한 단계 위: OrderID가 초기화됐는가?
procedure TfrmOrder.FormCreate(Sender: TObject);
begin
  // FOrderID가 초기화되지 않음! (기본값 0)
end;
// 원인: FormCreate에서 FOrderID를 제대로 설정하지 않음
// 수정 위치: 폼 초기화 또는 Show 시점
```

### 4. 원인 위치에서 수정

증상이 나타나는 곳에서 수정하지 말고,
잘못된 값이 **처음 생성되는 곳**에서 수정한다.

### 5. 방어 계층 추가 (수정 후)

원인 위치 수정 후, 동일 문제가 다시 발생하지 않도록 경계마다 검증 추가:
```pascal
// 원인 수정 후 방어 계층:
procedure TdmOrder.SaveOrder(AOrderID: Integer);
begin
  if AOrderID <= 0 then
    raise EValidationError.Create('유효하지 않은 주문 ID');
  // ...
end;
```

## YSR 빈출 추적 패턴

### CP949 인코딩 손상 추적
```
증상: .pas 파일 열면 한글이 깨짐
추적: 어떤 도구로 파일을 수정했는가?
      → Write 도구 사용 → UTF-8로 저장 → CP949 바이트 손상
원인: Write 도구 사용
수정: encoding-critical.md 절차로 복구 (Python cp949 방식)
```

### nil 포인터 (EAccessViolation) 추적
```
증상: EAccessViolation at address 00000000
추적: 어느 객체가 nil인가? → Create 시점 확인
      → FreeAndNil 후 재접근? → Terminated 이후 접근?
원인: 객체 생명주기 불일치
수정: FreeAndNil + nil 가드, 생명주기 재설계
```

### SQL 오류 추적 (Sybase/PG 방언)
```
증상: SQL 실행 오류 (예: ISNULL not recognized in PG)
추적: 어느 SQL 메소드에서 발생? → UsingPg 분기 있는가?
원인: UsingPg 분기 없이 Sybase 전용 함수 사용
수정: TtsQuery.UsingPg 분기 추가
```

### GDI 핸들 누수 추적
```
증상: 장시간 실행 후 화면 깨짐 또는 CreateFont 실패
추적: SelectObject 후 DeleteObject 호출됐는가?
      → try..finally 없이 SelectObject만 있지 않은가?
원인: SelectObject/DeleteObject 쌍 누락
수정: try..finally로 복구 + DeleteObject 보장
```

## 진단 로그 추가 (추적 불가 시)

Delphi에서 콜 체인 추적이 어려울 때 각 경계에서 로그 추가:

```pascal
uses LogMan;

procedure TdmOrder.SaveOrder(AOrderID: Integer);
begin
  WriteLogMan('TdmOrder.SaveOrder', 'AOrderID=' + IntToStr(AOrderID), '');
  // 기존 코드
end;

procedure TfrmOrder.btnSaveClick(Sender: TObject);
begin
  WriteLogMan('TfrmOrder.btnSaveClick', 'FOrderID=' + IntToStr(FOrderID), '');
  dmOrder.SaveOrder(FOrderID);
end;
```

로그 파일에서 값이 잘못된 최초 지점 = 수정 위치.

## 핵심 원칙

**오류가 나타나는 곳에서 수정하지 마라. 잘못된 값이 시작되는 곳에서 수정하라.**
