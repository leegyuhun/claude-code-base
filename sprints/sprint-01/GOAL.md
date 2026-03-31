# sprint-01 상세 계획

## 목표
SNMP 프로토콜 통신과 네트워크 인터페이스 감지, 서브넷 IP 범위 계산의 기반 인프라 모듈을 구현한다.

## 선행 스프린트
- 없음 (독립 모듈)

## 구현 기능 체크리스트
- [x] 공통 타입 정의 (uScanTypes.pas) (예상 소요: 1h)
- [ ] SNMP 통신 모듈 (uSNMP.pas) (예상 소요: 8h)
- [ ] 네트워크 인터페이스 자동 감지 (uNetworkUtils.pas) (예상 소요: 4h)
- [ ] 서브넷 IP 범위 계산 (uSubnetCalc.pas) (예상 소요: 3h)
- [ ] 빌드 스크립트 및 프로젝트 파일 초기 구성 (예상 소요: 2h)

## 완료 조건
- [ ] SNMP GET 요청을 UDP 161로 전송하고 응답을 ASN.1/BER 파싱할 수 있음 (자동 검증 -- 빌드 성공)
- [ ] sysDescr(1.3.6.1.2.1.1.1.0) OID로 GET 요청 시 응답 값을 AnsiString으로 추출 가능 (수동 확인 필요)
- [ ] GetAdaptersInfo 호출로 로컬 네트워크 인터페이스 목록(IP, 서브넷 마스크)을 가져올 수 있음 (수동 확인 필요)
- [ ] CIDR 표기(예: 192.168.1.0/24) 또는 IP+Mask 조합에서 시작~끝 IP 범위를 정확히 계산함 (자동 검증 -- 단위 테스트)
- [ ] /24 서브넷 입력 시 254개 호스트 IP를 정확히 생성함 (자동 검증 -- 단위 테스트)
- [ ] /16 서브넷 입력 시 65534개 호스트 IP를 정확히 생성함 (자동 검증 -- 단위 테스트)
- [ ] build.bat exe Release 실행 시 컴파일 에러 없이 빌드 성공 (자동 검증)

## 예상 산출물

### 생성될 파일
- Source/uScanTypes.pas -- 공통 레코드/타입/상수 정의
- Source/uSNMP.pas -- SNMP v1/v2c GET 요청 및 BER 응답 파싱
- Source/uNetworkUtils.pas -- GetAdaptersInfo 래퍼, 어댑터 목록 반환
- Source/uSubnetCalc.pas -- CIDR 파싱, IP<->DWORD 변환, 범위 생성
- PrinterScanApp.dpr -- EXE 프로젝트 파일 (빌드 확인용 스텁)
- build.bat -- dcc32 호출 빌드 스크립트

### 추가될 API 엔드포인트
- 해당 없음 (네이티브 Win32 애플리케이션)

### 추가될 화면/컴포넌트
- 해당 없음 (sprint-01은 인프라 모듈만 구현, UI는 sprint-02)

## 기술 고려사항

### uScanTypes.pas
- TPrinterInfo 레코드: IP(AnsiString), Name, Model, DeviceType, ResponseTime(Integer), Status
- TScanState 열거형: ssIdle, ssScanning, ssStopping, ssCompleted
- TSubnetInfo 레코드: IP(AnsiString), Mask(AnsiString), CIDR(AnsiString)
- 콜백 타입 정의: TScanProgressCallback, TScanCompleteCallback (sprint-02에서 사용)

### uSNMP.pas
- Indy 10 IdSNMP 활용 여부 판단 필요 -- IdSNMP가 Delphi 2007에 기본 포함되어 있으므로 우선 활용
- IdSNMP가 부적합할 경우 직접 UDP 소켓 + ASN.1/BER 인코딩/디코딩 구현
- SNMP v1 GET Request PDU 구조: Version(Integer) + Community(OctetString) + GetRequest-PDU
- BER 태그: INTEGER=0x02, OCTET_STRING=0x04, SEQUENCE=0x30, GetRequest=0xA0, GetResponse=0xA2
- 타임아웃 기본값 1000ms, Community String 기본값 "public"
- 에러 처리: 타임아웃, 잘못된 응답, 네트워크 미도달 시 예외를 삼키고 결과에 에러 상태 기록

### uNetworkUtils.pas
- WinAPI IpHlpApi.dll의 GetAdaptersInfo 사용
- IP_ADAPTER_INFO 구조체 동적 할당 (첫 호출로 버퍼 크기 확인, 재할당 후 재호출)
- 루프백(127.0.0.1)과 미연결 어댑터 필터링
- 반환: TSubnetInfo 배열 (IP, SubnetMask)

### uSubnetCalc.pas
- IP 문자열 <-> DWORD(Cardinal) 변환 함수
- 서브넷 마스크 -> 프리픽스 길이 변환
- CIDR 문자열 파싱 (예: "192.168.1.0/24" -> IP + Mask)
- 범위 계산: 네트워크 주소 + 1 ~ 브로드캐스트 주소 - 1
- /32(호스트 1개), /31(호스트 0개) 등 엣지 케이스 처리

### 빌드 구성
- build.bat: dcc32.exe 경로 확인 후 EXE/DLL 조건 빌드
- 컴파일러 옵션: -$D+(디버그 정보), -$L+(로컬 심볼), -N"Lib"(DCU 출력)
- Source 폴더를 유닛 검색 경로에 추가 (-U"Source")

## 수동 테스트 시나리오

1. [SNMP GET 요청/응답]
   - 준비: 네트워크에 SNMP 응답 가능한 장비 (프린터 또는 라우터) 확인
   - 시나리오: EXE 실행 -> uSNMP 테스트 코드에서 대상 IP로 sysDescr GET 요청 전송
   - 예상 결과: 응답으로 장비 설명 문자열을 정상 수신하여 콘솔/디버그 출력

2. [네트워크 인터페이스 감지]
   - 경로: EXE 실행 (콘솔 출력 또는 디버그 창)
   - 시나리오: uNetworkUtils의 GetLocalSubnets 호출
   - 예상 결과: 현재 PC에 연결된 네트워크 어댑터의 IP와 서브넷 마스크 목록 출력 (루프백 제외)

3. [서브넷 IP 범위 계산]
   - 시나리오: "192.168.1.0/24" 입력 -> IP 범위 생성
   - 예상 결과: 192.168.1.1 ~ 192.168.1.254 (254개) 반환
   - 시나리오: "10.0.0.0/16" 입력 -> IP 범위 생성
   - 예상 결과: 10.0.0.1 ~ 10.0.255.254 (65534개) 반환
   - 시나리오: "172.16.5.128/25" 입력 -> IP 범위 생성
   - 예상 결과: 172.16.5.129 ~ 172.16.5.254 (126개) 반환
