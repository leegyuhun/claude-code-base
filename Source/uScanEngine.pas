unit uScanEngine;
{
  멀티스레드 병렬 스캔 엔진.
  TThread 기반으로 서브넷 내 IP를 병렬 스캔하며,
  프린터를 발견하면 콜백/이벤트로 결과를 전달한다.
  VCL 접근은 반드시 Synchronize를 사용한다.
}

interface

uses
  SysUtils, Classes, Windows,
  uScanTypes, uSNMP, uSubnetCalc;

type
  TScanEngine = class
  private
    FScanState: TScanState;
    FCommunity: string;
    FTimeout: Integer;
    FOnPrinterFound: TOnPrinterFound;
    FOnScanLog: TOnScanLog;
    FOnScanComplete: TOnScanComplete;
  public
    constructor Create;
    destructor Destroy; override;

    { 스캔 시작. ASubnets: CIDR 목록 (TStringList) }
    procedure StartScan(ASubnets: TStringList);

    { 스캔 중지 요청 }
    procedure StopScan;

    property ScanState: TScanState read FScanState;
    property Community: string read FCommunity write FCommunity;
    property Timeout: Integer read FTimeout write FTimeout;
    property OnPrinterFound: TOnPrinterFound read FOnPrinterFound write FOnPrinterFound;
    property OnScanLog: TOnScanLog read FOnScanLog write FOnScanLog;
    property OnScanComplete: TOnScanComplete read FOnScanComplete write FOnScanComplete;
  end;

implementation

{ TScanEngine }

constructor TScanEngine.Create;
begin
  inherited Create;
  FScanState := ssIdle;
  FCommunity := 'public';
  FTimeout := 1000;
end;

destructor TScanEngine.Destroy;
begin
  inherited Destroy;
end;

procedure TScanEngine.StartScan(ASubnets: TStringList);
begin
  // TODO: Sprint-02에서 구현
  // TThread 풀 생성, 서브넷별 IP 순회, SNMP 질의
end;

procedure TScanEngine.StopScan;
begin
  // TODO: Sprint-02에서 구현
  if FScanState = ssScanning then
    FScanState := ssStopping;
end;

end.
