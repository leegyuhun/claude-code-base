unit uSNMP;
{
  SNMP v1/v2c 통신 모듈.
  UDP 161 포트로 SNMP GET 요청을 보내고 응답을 파싱한다.
  Indy 10 IdSNMP를 활용한다.
}

interface

uses
  SysUtils, Classes, Windows,
  uScanTypes;

type
  TSNMPClient = class
  private
    FCommunity: string;
    FTimeout: Integer;  // ms
  public
    constructor Create;
    destructor Destroy; override;

    { SNMP GET 요청. OID에 대한 값을 반환. 실패 시 빈 문자열. }
    function GetValue(const AHost: string; const AOID: string): string;

    { 여러 OID에 대한 GET 요청. AValues에 OID=Value 쌍을 반환. 성공 시 True. }
    function GetMultipleValues(const AHost: string; AOIDs: TStrings;
      AValues: TStrings): Boolean;

    { 지정 호스트가 프린터인지 확인 (hrDeviceType OID 체크) }
    function IsPrinter(const AHost: string): Boolean;

    { 호스트에서 프린터 정보를 조회하여 TPrinterInfo 레코드에 채움.
      성공 시 True, 실패 시 False. }
    function QueryPrinterInfo(const AHost: string;
      var AInfo: TPrinterInfo): Boolean;

    property Community: string read FCommunity write FCommunity;
    property Timeout: Integer read FTimeout write FTimeout;
  end;

implementation

uses
  IdSNMP, IdASN1Util;

{ TSNMPClient }

constructor TSNMPClient.Create;
begin
  inherited Create;
  FCommunity := DEFAULT_COMMUNITY;
  FTimeout := DEFAULT_TIMEOUT;
end;

destructor TSNMPClient.Destroy;
begin
  inherited Destroy;
end;

function TSNMPClient.GetValue(const AHost: string; const AOID: string): string;
var
  ASNMP: TIdSNMP;
begin
  Result := '';
  ASNMP := TIdSNMP.Create(nil);
  try
    try
      ASNMP.Host := AHost;
      ASNMP.Port := DEFAULT_SNMP_PORT;
      ASNMP.Community := FCommunity;
      ASNMP.ReceiveTimeout := FTimeout;

      ASNMP.Query.Clear;
      ASNMP.Query.PDUType := PDUGetRequest;
      ASNMP.Query.MIBAdd(AOID, '', ASN1_NULL);

      if ASNMP.SendQuery then
      begin
        if ASNMP.Reply.ValueCount > 0 then
          Result := ASNMP.Reply.Value[0];
      end;
    except
      // 타임아웃, 네트워크 미도달 등 예외를 삼키고 빈 문자열 반환
      on E: Exception do
      begin
        {$IFDEF DEBUG}
        OutputDebugString(PChar('SNMP GetValue error [' + AHost + ']: ' + E.Message));
        {$ENDIF}
        Result := '';
      end;
    end;
  finally
    ASNMP.Free;
  end;
end;

function TSNMPClient.GetMultipleValues(const AHost: string; AOIDs: TStrings;
  AValues: TStrings): Boolean;
var
  ASNMP: TIdSNMP;
  i: Integer;
begin
  Result := False;
  AValues.Clear;

  ASNMP := TIdSNMP.Create(nil);
  try
    try
      ASNMP.Host := AHost;
      ASNMP.Port := DEFAULT_SNMP_PORT;
      ASNMP.Community := FCommunity;
      ASNMP.ReceiveTimeout := FTimeout;

      ASNMP.Query.Clear;
      ASNMP.Query.PDUType := PDUGetRequest;
      for i := 0 to AOIDs.Count - 1 do
        ASNMP.Query.MIBAdd(AOIDs[i], '', ASN1_NULL);

      if ASNMP.SendQuery then
      begin
        for i := 0 to ASNMP.Reply.ValueCount - 1 do
          AValues.Add(ASNMP.Reply.Value[i]);
        Result := (AValues.Count > 0);
      end;
    except
      on E: Exception do
      begin
        {$IFDEF DEBUG}
        OutputDebugString(PChar('SNMP GetMultiple error [' + AHost + ']: ' + E.Message));
        {$ENDIF}
        Result := False;
      end;
    end;
  finally
    ASNMP.Free;
  end;
end;

function TSNMPClient.IsPrinter(const AHost: string): Boolean;
var
  ADeviceType: string;
begin
  // hrDeviceType OID를 조회하여 프린터인지 확인
  // 프린터의 경우 응답값에 hrDevicePrinter(1.3.6.1.2.1.25.3.1.5)가 포함됨
  ADeviceType := GetValue(AHost, OID_HR_DEVICE_TYPE);
  Result := (Pos(OID_DEVICE_TYPE_PRINTER, ADeviceType) > 0);
end;

function TSNMPClient.QueryPrinterInfo(const AHost: string;
  var AInfo: TPrinterInfo): Boolean;
var
  ATickStart: Cardinal;
begin
  Result := False;

  AInfo.IP := AHost;
  AInfo.Name := '';
  AInfo.Model := '';
  AInfo.DeviceType := '';
  AInfo.ResponseTime := 0;
  AInfo.Online := False;
  AInfo.Status := '';

  // 응답 시간 측정 시작
  ATickStart := GetTickCount;

  // hrDeviceType으로 프린터 여부 확인
  AInfo.DeviceType := GetValue(AHost, OID_HR_DEVICE_TYPE);
  if AInfo.DeviceType = '' then
  begin
    // hrDeviceType에 응답이 없으면 sysDescr로 재시도
    AInfo.Name := GetValue(AHost, OID_SYS_DESCR);
    if AInfo.Name = '' then
      Exit; // SNMP 응답 없음
  end;

  // 응답 시간 기록
  AInfo.ResponseTime := Integer(GetTickCount - ATickStart);
  AInfo.Online := True;

  // 프린터 판별
  if Pos(OID_DEVICE_TYPE_PRINTER, AInfo.DeviceType) = 0 then
  begin
    AInfo.Status := 'Not a printer';
  end
  else
  begin
    AInfo.Status := 'Printer';
    Result := True;
  end;

  // 추가 정보 조회 (이름, 모델)
  if AInfo.Name = '' then
    AInfo.Name := GetValue(AHost, OID_SYS_NAME);
  AInfo.Model := GetValue(AHost, OID_HR_DEVICE_DESCR);
end;

end.
