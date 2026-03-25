---
paths:
  - "Source/**"
  - "Tests/**"
---

# 코딩 원칙 (Delphi 2007 / Object Pascal)

## 기술 스택
# TODO: 프로젝트 초기화(PHASE 4.5) 후 기술 스택을 기입하세요
# 예: Delphi 2007 (BDS 5.0), VCL, ADO/BDE, FastReport

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
- 폼 클래스: TFrm접두사 (예: TFrmMain)
- 데이터 모듈 클래스: TDM접두사 (예: TDMMain)
- 일반 클래스: T접두사 (예: TCustomer)
- 유닛 파일명: U접두사 (예: UBusinessLogic.pas)
- 상수: c접두사 (예: cMaxRetry = 3)
- 전역 변수: g접두사 (사용 최소화)

## 보안
- DB 연결 문자열은 설정 파일(.ini)로 분리 (코드 하드코딩 금지)
- SQL은 파라미터 바인딩 사용 (SQL injection 방지)
  예: Query.Parameters.ParamByName('Id').Value := Id;

## 임시 코드
- 임시 코드 사용 시 TODO 주석 필수
  // TODO: [tech-debt] 임시처리 - 이유

## .dfm / .pas 동기화
- 폼 컴포넌트 추가/삭제 시 반드시 .dfm도 함께 커밋
- 텍스트 .dfm 형식 권장 (IDE: Edit → Form as Text)
