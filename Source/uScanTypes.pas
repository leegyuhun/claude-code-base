unit uScanTypes;
{
  공통 타입 정의 유닛.
  EXE/DLL 양쪽에서 공유하는 레코드, 콜백 타입 등을 정의한다.
}

interface

type
  // 프린터 탐색 결과 레코드
  TPrinterInfo = record
    IP: string;           // 프린터 IP 주소
    Name: string;         // SNMP sysName (1.3.6.1.2.1.1.5.0)
    Model: string;        // SNMP hrDeviceDescr (1.3.6.1.2.1.25.3.2.1.3)
    DeviceType: string;   // SNMP hrDeviceType (1.3.6.1.2.1.25.3.2.1.2)
    ResponseTime: Integer; // 응답 시간 (ms)
    Online: Boolean;      // 온라인 여부
    Status: string;       // 상태 문자열
  end;

  // 스캔 상태
  TScanState = (ssIdle, ssScanning, ssStopping, ssCompleted);

  // 서브넷 정보 레코드
  TSubnetInfo = record
    IP: string;           // IP 주소 (예: 192.168.1.100)
    Mask: string;         // 서브넷 마스크 (예: 255.255.255.0)
    CIDR: string;         // CIDR 표기 (예: 192.168.1.0/24)
  end;

  TSubnetInfoArray = array of TSubnetInfo;

  // 비동기 스캔 콜백 (DLL export용)
  TPrinterFoundCallback = procedure(
    pszIP: PAnsiChar;
    pszName: PAnsiChar;
    pszModel: PAnsiChar;
    nResponseTime: Integer
  ); stdcall;

  // 스캔 진행률 콜백 (DLL export용)
  TScanProgressCallback = procedure(
    nCurrent: Integer;
    nTotal: Integer
  ); stdcall;

  // 스캔 완료 콜백 (DLL export용)
  TScanCompleteCallback = procedure(
    nTotalFound: Integer
  ); stdcall;

  // 스캔 진행 이벤트 (VCL용)
  TOnPrinterFound = procedure(Sender: TObject; const Info: TPrinterInfo) of object;
  TOnScanLog = procedure(Sender: TObject; const Msg: string) of object;
  TOnScanComplete = procedure(Sender: TObject; TotalFound: Integer) of object;
  TOnScanProgress = procedure(Sender: TObject; Current, Total: Integer) of object;

const
  // SNMP OID 상수
  OID_SYS_DESCR      = '1.3.6.1.2.1.1.1.0';    // sysDescr
  OID_SYS_NAME       = '1.3.6.1.2.1.1.5.0';    // sysName
  OID_HR_DEVICE_TYPE  = '1.3.6.1.2.1.25.3.2.1.2'; // hrDeviceType
  OID_HR_DEVICE_DESCR = '1.3.6.1.2.1.25.3.2.1.3'; // hrDeviceDescr

  // hrDeviceType 값 (프린터)
  OID_DEVICE_TYPE_PRINTER = '1.3.6.1.2.1.25.3.1.5'; // hrDevicePrinter

  // SNMP 기본값
  DEFAULT_COMMUNITY = 'public';
  DEFAULT_TIMEOUT   = 1000; // ms
  DEFAULT_SNMP_PORT = 161;

implementation

end.
