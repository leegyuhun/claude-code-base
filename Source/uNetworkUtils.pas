unit uNetworkUtils;
{
  네트워크 인터페이스 자동 감지 유닛.
  WinAPI GetAdaptersInfo (IpHlpApi)를 사용하여
  로컬 PC의 네트워크 어댑터 정보와 서브넷을 가져온다.
}

interface

uses
  SysUtils, Classes, Windows;

type
  TAdapterInfo = record
    Name: string;        // 어댑터 이름 (Description)
    IPAddress: string;   // IP 주소
    SubnetMask: string;  // 서브넷 마스크
    Gateway: string;     // 기본 게이트웨이
  end;

  TAdapterInfoArray = array of TAdapterInfo;

{ 로컬 PC의 활성 네트워크 어댑터 목록 반환 (루프백/미연결 제외) }
function GetLocalAdapters: TAdapterInfoArray;

{ IP + 서브넷 마스크로 CIDR 문자열 계산 (예: "192.168.1.0/24") }
function GetNetworkCIDR(const AIP, ASubnetMask: string): string;

implementation

uses
  uSubnetCalc;

// ===================================================================
// IpHlpApi 구조체 및 함수 선언
// Delphi 2007에서 IpTypes/IpHlpApi 유닛이 없을 수 있으므로 직접 선언
// ===================================================================

const
  MAX_ADAPTER_NAME_LENGTH        = 256;
  MAX_ADAPTER_DESCRIPTION_LENGTH = 128;
  MAX_ADAPTER_ADDRESS_LENGTH     = 8;

  ERROR_SUCCESS        = 0;
  ERROR_BUFFER_OVERFLOW = 111;

type
  PIP_ADDRESS_STRING = ^IP_ADDRESS_STRING;
  IP_ADDRESS_STRING = record
    S: array[0..15] of AnsiChar;
  end;
  IP_MASK_STRING = IP_ADDRESS_STRING;

  PIP_ADDR_STRING = ^IP_ADDR_STRING;
  IP_ADDR_STRING = record
    Next: PIP_ADDR_STRING;
    IpAddress: IP_ADDRESS_STRING;
    IpMask: IP_ADDRESS_STRING;
    Context: DWORD;
  end;

  PIP_ADAPTER_INFO = ^IP_ADAPTER_INFO;
  IP_ADAPTER_INFO = record
    Next: PIP_ADAPTER_INFO;
    ComboIndex: DWORD;
    AdapterName: array[0..MAX_ADAPTER_NAME_LENGTH + 3] of AnsiChar;
    Description: array[0..MAX_ADAPTER_DESCRIPTION_LENGTH + 3] of AnsiChar;
    AddressLength: UINT;
    Address: array[0..MAX_ADAPTER_ADDRESS_LENGTH - 1] of Byte;
    Index: DWORD;
    AType: UINT;
    DhcpEnabled: UINT;
    CurrentIpAddress: PIP_ADDR_STRING;
    IpAddressList: IP_ADDR_STRING;
    GatewayList: IP_ADDR_STRING;
    DhcpServer: IP_ADDR_STRING;
    HaveWins: BOOL;
    PrimaryWinsServer: IP_ADDR_STRING;
    SecondaryWinsServer: IP_ADDR_STRING;
    LeaseObtained: Integer;
    LeaseExpires: Integer;
  end;

function GetAdaptersInfo(pAdapterInfo: PIP_ADAPTER_INFO;
  var pOutBufLen: ULONG): DWORD; stdcall;
  external 'iphlpapi.dll' name 'GetAdaptersInfo';

// ===================================================================
// 구현
// ===================================================================

function GetLocalAdapters: TAdapterInfoArray;
var
  ABufLen: ULONG;
  ARetVal: DWORD;
  ABuffer: PAnsiChar;
  AAdapter: PIP_ADAPTER_INFO;
  AIPStr, AMaskStr: string;
  ACount: Integer;
begin
  SetLength(Result, 0);
  ACount := 0;

  // 1차 호출: 필요한 버퍼 크기 확인
  ABufLen := 0;
  ARetVal := GetAdaptersInfo(nil, ABufLen);
  if ARetVal <> ERROR_BUFFER_OVERFLOW then
    Exit;

  // 버퍼 할당
  GetMem(ABuffer, ABufLen);
  try
    // 2차 호출: 실제 데이터 가져오기
    ARetVal := GetAdaptersInfo(PIP_ADAPTER_INFO(ABuffer), ABufLen);
    if ARetVal <> ERROR_SUCCESS then
      Exit;

    // 어댑터 목록 순회
    AAdapter := PIP_ADAPTER_INFO(ABuffer);
    while AAdapter <> nil do
    begin
      AIPStr := string(AAdapter^.IpAddressList.IpAddress.S);
      AMaskStr := string(AAdapter^.IpAddressList.IpMask.S);

      // 루프백(127.x.x.x) 및 미연결(0.0.0.0) 어댑터 필터링
      if (AIPStr <> '0.0.0.0') and (AIPStr <> '') and
         (Copy(AIPStr, 1, 4) <> '127.') then
      begin
        Inc(ACount);
        SetLength(Result, ACount);
        Result[ACount - 1].Name := string(AAdapter^.Description);
        Result[ACount - 1].IPAddress := AIPStr;
        Result[ACount - 1].SubnetMask := AMaskStr;
        Result[ACount - 1].Gateway := string(AAdapter^.GatewayList.IpAddress.S);
      end;

      AAdapter := AAdapter^.Next;
    end;
  finally
    FreeMem(ABuffer, ABufLen);
  end;
end;

function GetNetworkCIDR(const AIP, ASubnetMask: string): string;
var
  AIPVal, AMaskVal, ANetworkVal: Cardinal;
  APrefix: Integer;
begin
  AIPVal := IPToCardinal(AIP);
  AMaskVal := IPToCardinal(ASubnetMask);

  if (AIPVal = 0) or (AMaskVal = 0) then
  begin
    Result := '';
    Exit;
  end;

  ANetworkVal := AIPVal and AMaskVal;
  APrefix := MaskToPrefix(ASubnetMask);
  Result := CardinalToIP(ANetworkVal) + '/' + IntToStr(APrefix);
end;

end.
