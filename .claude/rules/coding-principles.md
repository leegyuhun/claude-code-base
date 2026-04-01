---
paths:
  - "**/*.pas"
  - "**/*.dfm"
---

# 코딩 원칙 (Delphi 2007 / Object Pascal)

## 기술 스택
# TODO: 프로젝트 초기화(PHASE 4.5) 후 기술 스택을 기입하세요
# 예: Delphi 2007 (BDS 5.0), VCL

## 핵심 규칙

### 1. 코딩 전에 생각하라
- 가정을 명시적으로 밝혀라. 불확실하면 물어봐라.
- .dfm 변경이 필요한지 먼저 파악하라.

### 2. 단순함 우선
- 요청한 것 이상의 기능을 만들지 마라.
- VCL 표준 컴포넌트로 해결 가능하면 서드파티 불필요.

### 3. 수술적 변경
- 요청과 관련된 유닛/폼만 건드려라.
- .pas 수정 시 해당 .dfm 파일과 싱크를 유지하라.
- 기존 스타일을 따라라.

### 4. 메모리 관리 (중요)
- 생성한 객체는 반드시 해제하라: FreeAndNil(Obj)
- try..finally 블록으로 리소스 보호
- TComponent 계층에 속하면 Owner가 해제 담당

## 명명 규칙
- 클래스: TMyClassName
- 폼: TfrmLogin, TfrmMain
- 데이터모듈: TdmMain
- 변수: 지역변수 AVarName, 멤버변수 FVarName, 전역변수 GVarName, 매개변수 MParam
- 상수: S_CONST_NAME
- 프로시저: DoSomething, HandleClick

## DBMS
 - Sybase와 PostgreSQL을 모두 사용중입니다.
  가능하다면 두 DBMS에서 모두 동작할 수 있는 SQL을 작성합니다.
  불가피하게 분기해야할 경우, TtsQuery.UsingPG 프로퍼티를 이용해 SQL을 분기합니다.
  TsQuery.pas 내 정의된 SQL 문법 관련 메소드를 적극적으로 활용합니다.

### 5. Application.ProcessMessages 재진입 방지 (중요)
- 버튼/액션 핸들러에서 ProcessMessages 호출 전 재진입 가드 필수
```pascal
procedure TfrmMain.btnProcessClick(Sender: TObject);
begin
  if FIsProcessing then Exit;
  FIsProcessing := True;
  btnProcess.Enabled := False;
  try
    // 작업 + Application.ProcessMessages
  finally
    FIsProcessing := False;
    btnProcess.Enabled := True;
  end;
end;
```

### 6. TDataSet 상태 관리 (중요)
- 폼 종료/닫기 전 반드시 State 확인
```pascal
// FormClose, 저장 전 공통 패턴
if Dataset.State in [dsEdit, dsInsert] then
begin
  if MessageDlg('저장하시겠습니까?', mtConfirmation, [mbYes, mbNo], 0) = mrYes then
    Dataset.Post
  else
    Dataset.Cancel;
end;
```
- `Post` 누락은 조용히 데이터를 날린다. 반드시 명시적으로 처리.

### 7. TThread UI 접근 금지
- 백그라운드 쓰레드에서 VCL 컴포넌트 직접 접근 금지
- 반드시 `Synchronize` 사용
```pascal
// 금지
procedure TWorkerThread.Execute;
begin
  lblStatus.Caption := '완료'; // 크래시/오염
end;

// 필수
procedure TWorkerThread.Execute;
begin
  Synchronize(UpdateUI);
end;
procedure TWorkerThread.UpdateUI;
begin
  lblStatus.Caption := '완료';
end;
```

### 8. GDI 핸들 관리
- CreateFont, CreatePen, CreateBrush 등 GDI 생성 후 반드시 DeleteObject
```pascal
var hFont: HFONT; hOld: HGDIOBJ;
begin
  hFont := CreateFont(...);
  try
    hOld := SelectObject(Canvas.Handle, hFont);
    // 그리기
    SelectObject(Canvas.Handle, hOld);
  finally
    DeleteObject(hFont);
  end;
end;
```

### 9. AnsiString / WideString 혼용 금지
- Delphi 2007의 String은 AnsiString(CP949). WideString과 암묵적 변환 금지
- DB/파일/API 경계에서만 명시적 변환 수행
```pascal
// 금지: 암묵적 변환
s := ws; // WideString → AnsiString, 한글 손실 가능

// 허용: 명시적 변환
s := AnsiString(WideCharToString(PWideChar(ws)));
```

### 10. BeginUpdate / EndUpdate 패턴
- TListView, TTreeView, TStringList 대량 업데이트 시 필수
```pascal
lvwList.Items.BeginUpdate;
try
  for i := 0 to Count - 1 do
    lvwList.Items.Add.Caption := Data[i];
finally
  lvwList.Items.EndUpdate;
end;
```

### 11. IFDEF 전략
- 디버그 로그는 반드시 `{$IFDEF DEBUG}` 블록 안에
- 프로젝트 옵션에서 DEBUG/RELEASE 조건부 컴파일 심볼 분리 관리
```pascal
{$IFDEF DEBUG}
  OutputDebugString(PChar('SQL: ' + qry.SQL.Text));
{$ENDIF}
```

### 12. TDataModule 분리 원칙
- 비즈니스 로직, DB 쿼리는 TDataModule에. 폼에 직접 작성 금지
- TfrmXxx는 UI 이벤트 처리와 화면 표시만 담당
- 복잡한 폼은 TFrame으로 분해하여 재사용

## 임시 코드
- 임시 코드 사용 시 TODO 주석 필수
  // TODO: [tech-debt] 임시처리 - 이유

## .dfm / .pas 동기화
- 폼 컴포넌트 추가/삭제 시 반드시 .dfm도 함께 커밋
- 텍스트 .dfm 형식 권장 (IDE: Edit → Form as Text)

