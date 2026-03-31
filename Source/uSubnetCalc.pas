unit uSubnetCalc;
{
  서브넷 IP 범위 계산 유닛.
  CIDR 표기(예: 192.168.1.0/24)와 시작~끝 IP 범위를
  순회 가능한 IP 목록으로 변환한다.
}

interface

uses
  SysUtils, Classes;

type
  TSubnetRange = record
    NetworkAddr: string;  // 네트워크 주소
    StartIP: Cardinal;    // 시작 IP (호스트 범위 첫 번째)
    EndIP: Cardinal;      // 끝 IP (호스트 범위 마지막)
    TotalHosts: Integer;  // 총 호스트 수
  end;

{ CIDR 문자열을 파싱하여 IP 범위 반환 (예: "192.168.1.0/24") }
function ParseCIDR(const ACIDR: string): TSubnetRange;

{ IP + 서브넷 마스크로부터 IP 범위 반환 }
function ParseSubnet(const AIP, AMask: string): TSubnetRange;

{ 시작IP~끝IP 문자열을 파싱 (예: "192.168.1.1~192.168.1.254") }
function ParseIPRange(const ARange: string): TSubnetRange;

{ IP 문자열을 Cardinal로 변환 (네트워크 바이트 오더) }
function IPToCardinal(const AIP: string): Cardinal;

{ Cardinal을 IP 문자열로 변환 }
function CardinalToIP(AValue: Cardinal): string;

{ 서브넷 마스크 문자열을 프리픽스 길이로 변환 (예: "255.255.255.0" -> 24) }
function MaskToPrefix(const AMask: string): Integer;

{ 프리픽스 길이를 서브넷 마스크 Cardinal로 변환 (예: 24 -> $FFFFFF00) }
function PrefixToMaskCardinal(APrefix: Integer): Cardinal;

{ 프리픽스 길이를 서브넷 마스크 문자열로 변환 (예: 24 -> "255.255.255.0") }
function PrefixToMask(APrefix: Integer): string;

implementation

function IPToCardinal(const AIP: string): Cardinal;
var
  AParts: array[0..3] of string;
  AStr: string;
  i, ADotPos, APartIdx: Integer;
begin
  Result := 0;
  AStr := AIP;
  APartIdx := 0;

  // IP 문자열을 '.' 기준으로 4개 파트로 분리
  for i := 0 to 3 do
    AParts[i] := '';

  for i := 1 to Length(AStr) do
  begin
    if AStr[i] = '.' then
    begin
      Inc(APartIdx);
      if APartIdx > 3 then
        Exit; // 잘못된 IP
    end
    else
      AParts[APartIdx] := AParts[APartIdx] + AStr[i];
  end;

  if APartIdx <> 3 then
    Exit; // 4개 파트가 아님

  for i := 0 to 3 do
  begin
    ADotPos := StrToIntDef(AParts[i], -1);
    if (ADotPos < 0) or (ADotPos > 255) then
    begin
      Result := 0;
      Exit;
    end;
    Result := (Result shl 8) or Cardinal(ADotPos);
  end;
end;

function CardinalToIP(AValue: Cardinal): string;
begin
  Result := IntToStr((AValue shr 24) and $FF) + '.' +
            IntToStr((AValue shr 16) and $FF) + '.' +
            IntToStr((AValue shr 8) and $FF) + '.' +
            IntToStr(AValue and $FF);
end;

function MaskToPrefix(const AMask: string): Integer;
var
  AMaskVal: Cardinal;
  i: Integer;
begin
  AMaskVal := IPToCardinal(AMask);
  Result := 0;
  for i := 31 downto 0 do
  begin
    if (AMaskVal and (Cardinal(1) shl i)) <> 0 then
      Inc(Result)
    else
      Break;
  end;
end;

function PrefixToMaskCardinal(APrefix: Integer): Cardinal;
begin
  if APrefix <= 0 then
    Result := 0
  else if APrefix >= 32 then
    Result := $FFFFFFFF
  else
    Result := Cardinal($FFFFFFFF shl (32 - APrefix));
end;

function PrefixToMask(APrefix: Integer): string;
begin
  Result := CardinalToIP(PrefixToMaskCardinal(APrefix));
end;

function CalcSubnetRange(ANetworkIP: Cardinal; APrefix: Integer): TSubnetRange;
var
  AMask, ABroadcast: Cardinal;
begin
  AMask := PrefixToMaskCardinal(APrefix);
  ANetworkIP := ANetworkIP and AMask; // 네트워크 주소 정규화
  ABroadcast := ANetworkIP or (not AMask);

  Result.NetworkAddr := CardinalToIP(ANetworkIP);

  if APrefix >= 31 then
  begin
    // /31: RFC 3021 (point-to-point), /32: 단일 호스트 -- 호스트 0개로 처리
    Result.StartIP := 0;
    Result.EndIP := 0;
    Result.TotalHosts := 0;
  end
  else
  begin
    Result.StartIP := ANetworkIP + 1;    // 네트워크 주소 다음
    Result.EndIP := ABroadcast - 1;      // 브로드캐스트 주소 이전
    Result.TotalHosts := Integer(Result.EndIP - Result.StartIP + 1);
  end;
end;

function ParseCIDR(const ACIDR: string): TSubnetRange;
var
  ASlashPos, APrefix: Integer;
  AIPStr: string;
  ANetworkIP: Cardinal;
begin
  FillChar(Result, SizeOf(Result), 0);

  ASlashPos := Pos('/', ACIDR);
  if ASlashPos = 0 then
    Exit;

  AIPStr := Copy(ACIDR, 1, ASlashPos - 1);
  APrefix := StrToIntDef(Copy(ACIDR, ASlashPos + 1, Length(ACIDR) - ASlashPos), -1);

  if (APrefix < 0) or (APrefix > 32) then
    Exit;

  ANetworkIP := IPToCardinal(AIPStr);
  if ANetworkIP = 0 then
    Exit;

  Result := CalcSubnetRange(ANetworkIP, APrefix);
end;

function ParseSubnet(const AIP, AMask: string): TSubnetRange;
var
  AIPVal: Cardinal;
  APrefix: Integer;
begin
  FillChar(Result, SizeOf(Result), 0);

  AIPVal := IPToCardinal(AIP);
  if AIPVal = 0 then
    Exit;

  APrefix := MaskToPrefix(AMask);
  if APrefix = 0 then
    Exit;

  Result := CalcSubnetRange(AIPVal, APrefix);
end;

function ParseIPRange(const ARange: string): TSubnetRange;
var
  ATildePos: Integer;
  AStartStr, AEndStr: string;
begin
  FillChar(Result, SizeOf(Result), 0);

  ATildePos := Pos('~', ARange);
  if ATildePos = 0 then
    Exit;

  AStartStr := Trim(Copy(ARange, 1, ATildePos - 1));
  AEndStr := Trim(Copy(ARange, ATildePos + 1, Length(ARange) - ATildePos));

  Result.StartIP := IPToCardinal(AStartStr);
  Result.EndIP := IPToCardinal(AEndStr);

  if (Result.StartIP = 0) or (Result.EndIP = 0) or (Result.StartIP > Result.EndIP) then
  begin
    FillChar(Result, SizeOf(Result), 0);
    Exit;
  end;

  Result.NetworkAddr := AStartStr;
  Result.TotalHosts := Integer(Result.EndIP - Result.StartIP + 1);
end;

end.
