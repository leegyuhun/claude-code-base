unit uDLLExport;
{
  DLL Export 인터페이스 유닛.
  외부 모듈에서 호출하는 stdcall 함수를 정의한다.
  Sprint-04에서 구현.
}

interface

uses
  Windows;

{ DLL에서만 사용되는 타입 재선언 (AnsiChar 기반) }
type
  TPrinterFoundCallback = procedure(
    pszIP: PAnsiChar;
    pszName: PAnsiChar;
    pszModel: PAnsiChar;
    nResponseTime: Integer
  ); stdcall;

{ 프린터 스캔 창 표시 (모달)
  반환값: 0=취소, 1=선택됨 }
function ShowPrinterScanner(
  hOwner: HWND;
  pszCommunity: PAnsiChar;
  pszSubnets: PAnsiChar;
  pszSelectedIP: PAnsiChar;
  nBufLen: Integer
): Integer; stdcall;

{ 백그라운드 스캔 실행 (비동기, 결과는 콜백으로 전달) }
procedure StartPrinterScan(
  pszCommunity: PAnsiChar;
  pszSubnets: PAnsiChar;
  pfnCallback: TPrinterFoundCallback
); stdcall;

implementation

uses
  SysUtils, Forms;

function ShowPrinterScanner(
  hOwner: HWND;
  pszCommunity: PAnsiChar;
  pszSubnets: PAnsiChar;
  pszSelectedIP: PAnsiChar;
  nBufLen: Integer
): Integer; stdcall;
begin
  // TODO: Sprint-04에서 구현
  Result := 0;
end;

procedure StartPrinterScan(
  pszCommunity: PAnsiChar;
  pszSubnets: PAnsiChar;
  pfnCallback: TPrinterFoundCallback
); stdcall;
begin
  // TODO: Sprint-04에서 구현
end;

end.
