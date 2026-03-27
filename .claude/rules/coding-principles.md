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

## 임시 코드
- 임시 코드 사용 시 TODO 주석 필수
  // TODO: [tech-debt] 임시처리 - 이유

## .dfm / .pas 동기화
- 폼 컴포넌트 추가/삭제 시 반드시 .dfm도 함께 커밋
- 텍스트 .dfm 형식 권장 (IDE: Edit → Form as Text)

## 파일인코딩
 - **Delphi 2007** 프로젝트의 `.pas` 파일은 **CP949(EUC-KR)** 인코딩입니다.
 - Edit 도구로 편집 시 기존 한글 주석은 절대 수정하지 않습니다.
   - 파일을 읽으면 기존 한글이 깨진 문자(`���`, `�Լ�` 등)로 보이는데, CP949 바이트가 그대로 표시된 것이므로 **원본 그대로 유지**합니다.
   - `old_string` 매칭 시 깨진 한글이 포함되어도, `new_string`에도 그대로 복사하여 변경하지 않습니다.
 - **Delphi Berlin 이상** 프로젝트의 `.pas` 파일은 **UTF-8** 인코딩이지만, BOM 처리 문제로 깨질 수 있으므로 한글 주석은 수정하지 않습니다.
