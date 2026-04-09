---
paths:
  - ".claude/rules/delphi2007-patterns.md"
description: "Delphi 2007 구현 패턴 레퍼런스 — 코딩 방법이 막힐 때 참조. coding-principles.md가 규칙을, 이 파일은 구체적 코드 예시를 제공한다."
---

# Delphi 2007 코딩 패턴 레퍼런스

> coding-principles.md의 규칙에 대한 구체적 구현 패턴 모음.
> "어떻게 짜야 하나?" 막힐 때 먼저 여기서 찾아라.

---

## 1. 재진입 가드 (Reentrancy Guard)

### 단순 플래그
```pascal
type
  TfrmMain = class(TForm)
  private
    FIsProcessing: Boolean;
  end;

procedure TfrmMain.btnSaveClick(Sender: TObject);
begin
  if FIsProcessing then Exit;
  FIsProcessing := True;
  btnSave.Enabled := False;
  try
    DoSave;
    Application.ProcessMessages;
  finally
    FIsProcessing := False;
    btnSave.Enabled := True;
  end;
end;
```

### Action 기반 (ActionList 사용 시 권장)
```pascal
procedure TfrmMain.actSaveExecute(Sender: TObject);
begin
  actSave.Enabled := False;
  try
    DoSave;
  finally
    actSave.Enabled := True;
  end;
end;
```

---

## 2. TDataSet 상태 패턴

### 저장 확인 후 닫기
```pascal
procedure TfrmOrder.FormCloseQuery(Sender: TObject; var CanClose: Boolean);
begin
  if qryOrder.State in [dsEdit, dsInsert] then
  begin
    case MessageDlg('변경사항을 저장하시겠습니까?',
                    mtConfirmation, [mbYes, mbNo, mbCancel], 0) of
      mrYes:    qryOrder.Post;
      mrNo:     qryOrder.Cancel;
      mrCancel: CanClose := False;
    end;
  end;
end;
```

### 안전한 Post 헬퍼
```pascal
// dmMain 등 DataModule에 공통 헬퍼로
function SafePost(ADataSet: TDataSet): Boolean;
begin
  Result := False;
  if not (ADataSet.State in [dsEdit, dsInsert]) then
  begin
    Result := True;
    Exit;
  end;
  try
    ADataSet.Post;
    Result := True;
  except
    on E: Exception do
    begin
      ADataSet.Cancel;
      raise;
    end;
  end;
end;
```

### 트랜잭션 + 여러 DataSet
```pascal
procedure TdmOrder.SaveOrder;
begin
  DBBeginTrans;
  try
    if qryOrder.State in [dsEdit, dsInsert] then qryOrder.Post;
    if qryOrderItem.State in [dsEdit, dsInsert] then qryOrderItem.Post;
    DBCommitTrans;
  except
    DBRollbackTrans;
    raise;
  end;
end;
```

---

## 3. TThread 패턴

### 기본 작업 쓰레드
```pascal
type
  TWorkerThread = class(TThread)
  private
    FProgress: Integer;
    FOnProgress: TNotifyEvent;
    procedure SyncProgress;
  protected
    procedure Execute; override;
  public
    constructor Create(AOnProgress: TNotifyEvent);
  end;

constructor TWorkerThread.Create(AOnProgress: TNotifyEvent);
begin
  FOnProgress := AOnProgress;
  FreeOnTerminate := True;
  inherited Create(False);
end;

procedure TWorkerThread.Execute;
var
  i: Integer;
begin
  for i := 1 to 100 do
  begin
    if Terminated then Break;
    // 작업
    FProgress := i;
    Synchronize(SyncProgress); // UI 업데이트는 반드시 Synchronize
    Sleep(10);
  end;
end;

procedure TWorkerThread.SyncProgress;
begin
  if Assigned(FOnProgress) then FOnProgress(Self);
end;
```

### 폼에서 쓰레드 생성/종료
```pascal
type
  TfrmMain = class(TForm)
  private
    FWorker: TWorkerThread;
    procedure HandleProgress(Sender: TObject);
  end;

procedure TfrmMain.StartWork;
begin
  btnStart.Enabled := False;
  // FreeOnTerminate = True 이므로 직접 Free 금지
  FWorker := TWorkerThread.Create(HandleProgress);
end;

procedure TfrmMain.HandleProgress(Sender: TObject);
begin
  // 이미 Synchronize 통해 호출됨 → UI 직접 접근 안전
  pbProgress.Position := (Sender as TWorkerThread).FProgress;
end;

procedure TfrmMain.FormClose(Sender: TObject; var Action: TCloseAction);
begin
  if Assigned(FWorker) then
  begin
    FWorker.Terminate;
    FWorker.WaitFor; // FreeOnTerminate = False일 때만
  end;
end;
```

---

## 4. GDI 핸들 패턴

### 폰트
```pascal
procedure TfrmReport.PaintHeader(ACanvas: TCanvas);
var
  hFont, hOldFont: HFONT;
begin
  hFont := CreateFont(
    -14, 0, 0, 0, FW_BOLD, 0, 0, 0,
    HANGEUL_CHARSET, OUT_DEFAULT_PRECIS,
    CLIP_DEFAULT_PRECIS, DEFAULT_QUALITY,
    DEFAULT_PITCH or FF_DONTCARE, '굴림');
  hOldFont := SelectObject(ACanvas.Handle, hFont);
  try
    ACanvas.TextOut(10, 10, '제목');
  finally
    SelectObject(ACanvas.Handle, hOldFont);
    DeleteObject(hFont);
  end;
end;
```

### 펜/브러시
```pascal
procedure DrawCustomRect(ACanvas: TCanvas; R: TRect);
var
  hPen, hOldPen: HPEN;
  hBrush, hOldBrush: HBRUSH;
begin
  hPen := CreatePen(PS_SOLID, 2, clRed);
  hBrush := CreateSolidBrush(clYellow);
  hOldPen := SelectObject(ACanvas.Handle, hPen);
  hOldBrush := SelectObject(ACanvas.Handle, hBrush);
  try
    Rectangle(ACanvas.Handle, R.Left, R.Top, R.Right, R.Bottom);
  finally
    SelectObject(ACanvas.Handle, hOldPen);
    SelectObject(ACanvas.Handle, hOldBrush);
    DeleteObject(hPen);
    DeleteObject(hBrush);
  end;
end;
```

---

## 5. 타입 안전 컬렉션 (제네릭 대체)

Delphi 2007에는 `TList<T>` 없음. Typed wrapper로 대체:

```pascal
type
  TOrderItem = class
    OrderID: Integer;
    Amount: Currency;
  end;

  TOrderItemList = class(TObjectList)  // OwnsObjects = True
  private
    function GetItem(Index: Integer): TOrderItem;
  public
    function Add(AItem: TOrderItem): Integer; reintroduce;
    function FindByOrderID(AID: Integer): TOrderItem;
    property Items[Index: Integer]: TOrderItem read GetItem; default;
  end;

function TOrderItemList.GetItem(Index: Integer): TOrderItem;
begin
  Result := TOrderItem(inherited Items[Index]);
end;

function TOrderItemList.Add(AItem: TOrderItem): Integer;
begin
  Result := inherited Add(AItem);
end;

function TOrderItemList.FindByOrderID(AID: Integer): TOrderItem;
var
  i: Integer;
begin
  Result := nil;
  for i := 0 to Count - 1 do
    if Items[i].OrderID = AID then
    begin
      Result := Items[i];
      Break;
    end;
end;
```

---

## 6. 커스텀 윈도우 메시지

```pascal
const
  // WM_USER($0400) 이상, 앱 전용 범위
  WM_REFRESH_GRID   = WM_USER + 100;
  WM_WORKER_DONE    = WM_USER + 101;
  WM_STATUS_UPDATE  = WM_USER + 102;

type
  TfrmMain = class(TForm)
  private
    procedure WMRefreshGrid(var Msg: TMessage); message WM_REFRESH_GRID;
    procedure WMWorkerDone(var Msg: TMessage); message WM_WORKER_DONE;
  end;

procedure TfrmMain.WMRefreshGrid(var Msg: TMessage);
begin
  inherited;
  RefreshGrid;
end;

// 쓰레드에서 PostMessage (비동기, 안전)
procedure TWorkerThread.NotifyDone;
begin
  PostMessage(FOwnerHandle, WM_WORKER_DONE, 0, 0);
end;
```

---

## 7. Modal 폼 패턴

### 결과 처리
```pascal
// 호출 측
procedure TfrmMain.OpenOrderDetail(AOrderID: Integer);
var
  frm: TfrmOrderDetail;
begin
  frm := TfrmOrderDetail.Create(nil);
  try
    frm.OrderID := AOrderID;
    if frm.ShowModal = mrOk then
      RefreshOrderList;
    // mrCancel이면 아무것도 안 함
  finally
    frm.Free;
  end;
end;

// 상세 폼 측
procedure TfrmOrderDetail.btnOkClick(Sender: TObject);
begin
  if not ValidateInput then Exit;
  SaveOrder;
  ModalResult := mrOk; // 폼 자동 닫힘
end;

procedure TfrmOrderDetail.btnCancelClick(Sender: TObject);
begin
  ModalResult := mrCancel;
end;
```

---

## 8. TDataModule 분리 원칙

```
TfrmXxx (폼)          ← UI 이벤트, 화면 표시만
    ↓ 호출
TdmXxx (DataModule)   ← 쿼리, 비즈니스 로직
    ↓ 호출
TdmMain (공용 DM)     ← DB 연결, 공용 쿼리
```

### 폼에서 DataModule 참조
```pascal
// frmOrderList.pas
uses dmOrderU; // DataModule 유닛 uses

procedure TfrmOrderList.LoadData;
begin
  dmOrder.LoadOrders(edtSearch.Text);
  dsOrders.DataSet := dmOrder.qryOrders; // DataSource 연결
end;
```

### DataModule 책임 범위
- **허용**: SQL 작성, 파라미터 바인딩, 결과 가공, 비즈니스 로직
- **금지**: ShowMessage, MessageDlg (UI 의존), 폼 직접 참조

---

## 9. 에러 처리 패턴

### 계층별 예외 처리
```pascal
// 예외 정의 (별도 유닛 권장: AppExceptionsU.pas)
type
  EAppError = class(Exception);
  EDBError = class(EAppError);
  EValidationError = class(EAppError);

// DataModule에서
procedure TdmOrder.SaveOrder(AOrder: TOrderRec);
begin
  if AOrder.Amount <= 0 then
    raise EValidationError.Create('금액은 0보다 커야 합니다.');
  try
    // DB 작업
  except
    on E: EDatabaseError do
      raise EDBError.CreateFmt('주문 저장 실패: %s', [E.Message]);
  end;
end;

// 폼에서
procedure TfrmOrder.btnSaveClick(Sender: TObject);
begin
  try
    dmOrder.SaveOrder(BuildOrderRec);
    ShowMessage('저장되었습니다.');
  except
    on E: EValidationError do
      ShowMessage('입력 오류: ' + E.Message);
    on E: EDBError do
      ShowMessage('DB 오류: ' + E.Message);
  end;
end;
```

---

## 10. AnsiString / WideString 변환

```pascal
// AnsiString(CP949) → WideString
function AnsiToWide(const S: AnsiString): WideString;
begin
  Result := WideString(S); // Delphi가 CP949 기준 변환
end;

// WideString → AnsiString(CP949)
function WideToAnsi(const W: WideString): AnsiString;
begin
  Result := AnsiString(W);
end;

// UTF-8 파일 읽기 → AnsiString
function UTF8FileToAnsi(const FileName: string): string;
var
  sl: TStringList;
begin
  sl := TStringList.Create;
  try
    sl.LoadFromFile(FileName); // BOM 있으면 자동 인식 안 됨
    // UTF8Decode → WideString → AnsiString 변환 필요
    Result := UTF8Decode(sl.Text);
  finally
    sl.Free;
  end;
end;
```

---

## 11. TQuery / SQL 구성 패턴

### 기본 SQL 구성 (with문 사용)
```pascal
procedure TdmOrder.LoadOrders(const ASearchText: string);
begin
  with qryOrders do
  begin
    Close;
    SQL.Clear;
    SQL.Add('SELECT');
    SQL.Add('  order_id, customer_nm, order_dt, amount');
    SQL.Add('FROM orders');
    SQL.Add('WHERE 1=1');
    if ASearchText <> '' then
      SQL.Add('  AND customer_nm LIKE ' + QuotedStr('%' + ASearchText + '%'));
    SQL.Add('ORDER BY order_dt DESC');
    Open;
  end;
end;
```

### 동적 WHERE 조건 추가
```pascal
procedure TdmOrder.SearchOrders(AFromDt, AToDt: TDateTime; AStatus: string);
begin
  with qryOrders do
  begin
    Close;
    SQL.Clear;
    SQL.Add('SELECT order_id, customer_nm, order_dt, amount, status');
    SQL.Add('FROM orders');
    SQL.Add('WHERE order_dt BETWEEN ' + QuotedStr(FormatDateTime('YYYY-MM-DD', AFromDt))
          + ' AND ' + QuotedStr(FormatDateTime('YYYY-MM-DD', AToDt)));
    if AStatus <> '' then
      SQL.Add('  AND status = ' + QuotedStr(AStatus));
    SQL.Add('ORDER BY order_dt DESC');
    Open;
  end;
end;
```

### INSERT / UPDATE (ExecSQL)
```pascal
procedure TdmOrder.InsertOrder(const ARec: TOrderRec);
begin
  with qryExec do
  begin
    SQL.Clear;
    SQL.Add('INSERT INTO orders');
    SQL.Add('  (customer_nm, order_dt, amount, status)');
    SQL.Add('VALUES (');
    SQL.Add('  ' + QuotedStr(ARec.CustomerNm) + ',');
    SQL.Add('  ' + QuotedStr(FormatDateTime('YYYY-MM-DD', ARec.OrderDt)) + ',');
    SQL.Add('  ' + FloatToStr(ARec.Amount) + ',');
    SQL.Add('  ' + QuotedStr(ARec.Status));
    SQL.Add(')');
    ExecSQL;
  end;
end;

procedure TdmOrder.UpdateOrderStatus(AOrderID: Integer; const AStatus: string);
begin
  with qryExec do
  begin
    SQL.Clear;
    SQL.Add('UPDATE orders');
    SQL.Add('SET status = ' + QuotedStr(AStatus));
    SQL.Add('WHERE order_id = ' + IntToStr(AOrderID));
    ExecSQL;
  end;
end;
```

### 값 타입별 SQL 삽입 규칙
```
문자열   → QuotedStr(Value)             → 'value' (따옴표 포함, 내부 ' 자동 이스케이프)
정수     → IntToStr(Value)              → 123
실수     → FloatToStr(Value)            → 123.45
날짜     → QuotedStr(FormatDateTime('YYYY-MM-DD', Value))
날짜시간 → QuotedStr(FormatDateTime('YYYY-MM-DD HH:NN:SS', Value))
Boolean  → IntToStr(Ord(Value))         → 0 또는 1
NULL     → 'NULL' (따옴표 없이 그대로)
```

### 주의사항
```
[ ] Open 전 반드시 Close 호출 (이미 열려있을 때 예외 방지)
[ ] SQL.Clear 후 SQL.Add (이전 SQL 잔존 방지)
[ ] 문자열 값은 반드시 QuotedStr() 사용 (내부 홑따옴표 이스케이프 처리)
[ ] 직접 따옴표 금지: '"' + Value + '"'  ← 값에 ' 포함 시 SQL 오류
[ ] ExecSQL은 SELECT 아닌 DML(INSERT/UPDATE/DELETE)에만
[ ] SELECT 결과 필요 시 Open, 결과 불필요한 DML은 ExecSQL
```

---

## 12. 리소스 정리 체크리스트

코드 리뷰 시 아래 항목 확인:

```
[ ] Create/Free 짝 맞음 (try..finally)
[ ] FreeAndNil 사용 (nil 체크 없이 재접근 방지)
[ ] TDataSet.State 체크 후 Post/Cancel
[ ] GDI 객체 DeleteObject 호출
[ ] TThread.Terminate + WaitFor 쌍
[ ] BeginUpdate → EndUpdate 짝 (ListView, TreeView, StringList)
[ ] ProcessMessages 호출 시 재진입 가드
[ ] UI 컴포넌트는 메인 쓰레드에서만 접근
[ ] WideString ↔ AnsiString 암묵적 혼용 없음
```

---

## 13. TtsQuery 사용 패턴

### 기본 SELECT
```pascal
procedure TdmOrder.LoadOrders(const ASearchKey: string);
var
  AQuery: TtsQuery;
begin
  AQuery := TtsQuery.Create(nil);
  try
    with AQuery do
    begin
      Close;
      SQL.Clear;
      SQL.Add('SELECT order_id, customer_nm, order_dt');
      SQL.Add('FROM orders');
      SQL.Add('WHERE 1=1');
      if ASearchKey <> '' then
        SQL.Add('AND customer_nm LIKE ' + QuotedStr('%' + ASearchKey + '%'));
      SQL.Add('ORDER BY order_dt DESC');
      Open;
      while not EOF do
      begin
        Next;
      end;
    end;
  finally
    AQuery.Free;
  end;
end;
```

### 다중 DB 분기 (PostgreSQL vs Sybase)
```pascal
procedure TdmOrder.ExecPlatformSQL(AQuery: TtsQuery);
begin
  with AQuery do
  begin
    Close;
    SQL.Clear;
    if UsingPg then
    begin
      SQL.Add('SELECT COALESCE(MAX(seq), 0) + 1 FROM orders');
    end
    else
    begin
      SQL.Add('SELECT ISNULL(MAX(seq), 0) + 1 FROM orders');
    end;
    Open;
  end;
end;
```

### ExecSQL (DML)
```pascal
procedure TdmOrder.UpdateStatus(AOrderID: Integer; const AStatus: string);
var
  AQuery: TtsQuery;
begin
  AQuery := TtsQuery.Create(nil);
  try
    with AQuery do
    begin
      SQL.Clear;
      SQL.Add('UPDATE orders');
      SQL.Add('SET status = ' + QuotedStr(AStatus));
      SQL.Add('WHERE order_id = ' + IntToStr(AOrderID));
      ExecSQL;
    end;
  finally
    AQuery.Free;
  end;
end;
```

---

## 14. Record 기반 데이터 전달 패턴

함수 간 복합 파라미터 전달 시 Record 구조체 사용.

```pascal
type
  TSearchDateType = (sdtJsDate, sdtRegDate);
  TSearchKeyType  = (sktChartNo, sktPatientNm);

  TRecSearchCondition = record
    SearchDateType: TSearchDateType;
    BeginDate: TDateTime;
    EndDate: TDateTime;
    SearchKeyType: TSearchKeyType;
    SearchKey: string;
  end;

procedure TdmOrder.Search(const ACondition: TRecSearchCondition);
begin
  // ACondition.BeginDate, ACondition.SearchKey 등 사용
end;

procedure TfrmOrder.btnSearchClick(Sender: TObject);
var
  aCondition: TRecSearchCondition;
begin
  aCondition.SearchDateType := sdtJsDate;
  aCondition.BeginDate := dtpBegin.Date;
  aCondition.EndDate := dtpEnd.Date;
  aCondition.SearchKey := edtSearch.Text;
  dmOrder.Search(aCondition);
end;
```

---

## 15. Logger 패턴

### TLogger (성능 측정 포함)
```pascal
uses Logger;

procedure TdmOrder.HeavyProcess;
begin
  TLogger.BeginTask('HeavyProcess');
  try
    // 작업
  finally
    TLogger.EndTask('HeavyProcess');
  end;
end;
```

### LogMan (간단한 위치 로그)
```pascal
uses LogMan;

procedure TdmOrder.SaveOrder;
begin
  WriteLogMan('TdmOrder.SaveOrder', 'start', qryOrder.SQL.Text);
end;
```

---

## 16. INI 기반 폼 설정 저장/복원 패턴

폼 크기, 위치, 컬럼 너비 등 사용자 설정은 INI 파일로 저장.

```pascal
procedure TfrmOrder.LoadProfile;
var
  aIni: TIniFile;
begin
  aIni := TIniFile.Create(GetProfilePath);
  try
    Left   := aIni.ReadInteger('Form', 'Left', Left);
    Top    := aIni.ReadInteger('Form', 'Top', Top);
    Width  := aIni.ReadInteger('Form', 'Width', Width);
    Height := aIni.ReadInteger('Form', 'Height', Height);
  finally
    aIni.Free;
  end;
end;

procedure TfrmOrder.SaveProfile;
var
  aIni: TIniFile;
begin
  aIni := TIniFile.Create(GetProfilePath);
  try
    aIni.WriteInteger('Form', 'Left', Left);
    aIni.WriteInteger('Form', 'Top', Top);
    aIni.WriteInteger('Form', 'Width', Width);
    aIni.WriteInteger('Form', 'Height', Height);
  finally
    aIni.Free;
  end;
end;

procedure TfrmOrder.FormCreate(Sender: TObject);
begin
  LoadProfile;
end;

procedure TfrmOrder.FormDestroy(Sender: TObject);
begin
  SaveProfile;
end;
```

---

## 17. TJGrid 기본 패턴

TJGrid는 프로젝트 커스텀 그리드 컴포넌트. TStringGrid 대신 이것을 사용.

```pascal
procedure TfrmOrder.FillGrid(AQuery: TtsQuery);
var
  i: Integer;
begin
  FGrid.BeginUpdate;
  try
    FGrid.RowCount := 1;
    AQuery.First;
    while not AQuery.EOF do
    begin
      FGrid.RowCount := FGrid.RowCount + 1;
      i := FGrid.RowCount - 1;
      FGrid.Cells[0, i] := AQuery.Fields[0].AsString;
      FGrid.Cells[1, i] := AQuery.Fields[1].AsString;
      AQuery.Next;
    end;
  finally
    FGrid.EndUpdate;
  end;
end;
```
