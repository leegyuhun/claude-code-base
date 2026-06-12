---
description: >
  YSR 작업에서 실제로 밟은 함정·놓치기 쉬운 케이스 모음 (회고 기반).
  자동 로드되지 않음 — 인덱스(.claude/rules/pitfalls-index.md)에서 카테고리를 찾고
  여기서 해당 함정 번호만 Grep 또는 부분 Read 한다.
  Load when: "함정", "회고", "전에 비슷한 거 있었는데", 디버깅 중 원인 탐색.
---

# YSR 함정 모음 (회고 기반)

> 작업 중 시간을 잡아먹은 시행착오 / 놓치기 쉬운 케이스를 다음에 반복하지 않으려고 남긴다.
> **형식**: 증상 → 원인 → 해결 → 다음 체크. 추측으로 채우지 말고 실제 겪은 것만 적는다.
> **인덱스**: `.claude/rules/pitfalls-index.md` (한 줄 요약 + 카테고리). 본문 추가 시 인덱스도 한 줄 갱신.

---

## F. 하네스 / 도구 운영

### #1 Bash 도구에서 PowerShell here-string(`@'...'@`) 사용 → 커밋 메시지 오염

**증상**: `git commit` 후 제목이 `@ chore: ...`처럼 앞에 `@`가 붙고, 본문 끝에도 `@`가 남음.

**원인**: 이 환경은 셸이 PowerShell이라 멀티라인 문자열에 here-string `@'...'@`를 쓰는 습관이 있는데, **Bash 도구로 실행하면 bash가 `@'...'@`를 해석 못 한다.** bash에선 `@` + 단일인용 문자열 + `@`로 처리돼 리터럴 `@`가 메시지에 섞여 들어감.

**해결**: Bash 도구로 멀티라인 커밋을 쓸 때는 `-m`을 **여러 개** 쓴다 (`-m "제목" -m "본문줄1\n본문줄2"`). here-string이 꼭 필요하면 PowerShell 도구를 쓰고, 그때만 `@'...'@`(닫는 `'@`는 반드시 0열). amend로 정정 가능: `git commit --amend -m "..." -m "..."`.

**다음 체크**: 도구가 Bash인지 PowerShell인지 먼저 확인하고 그 셸 문법으로 작성. 커밋 직후 `git log -1 --pretty=%s`로 제목 오염 여부 1초 검증.

---

## A. 인코딩 / 파일 처리

### #2 `.pas` / `.dfm`는 CP949 — Write 금지, Edit는 한글 줄 회피

**요약**: 별도 강제 규칙 문서가 있다 → **`.claude/rules/encoding-critical.md` 참조** (자동 로드됨).

**핵심만**: `.pas`/`.dfm`/공유 유닛(`Common/`, `ComUnit/` 등)은 CP949. Write 도구 절대 금지(UTF-8 변환으로 한글 파괴). Edit는 old/new_string 경계를 한글 없는 줄로. 한글 주석 추가는 Python `encoding='cp949'` 표준 I/O로만. UTF-8 BOM(`efbbbf`) 파일만 Edit로 한글 주석 허용.

**다음 체크**: 편집 전 `python3 -c "print(open('파일','rb').read(3).hex())"` → `efbbbf`가 아니면 CP949 규칙 적용.

---

## B. Delphi 언어 함정

### #3 새 enum 값 이름이 공용 타입(MType.pas 등)과 충돌

**증상**: 컴파일러가 enum 값을 의도와 다른 타입으로 해석하거나 모호성 오류.

**원인**: 새로 정의한 enum의 값 이름이 `Common\Class\MType.pas`/`MTypeCom.pas` 등 공용 타입의 기존 값과 겹침. Delphi는 스코프 내 enum 값을 전역처럼 노출하므로 충돌.

**해결**: 모듈 고유 접두사를 붙인 값 이름 사용 (예: `mtXxx`, `fcXxx`).

**다음 체크**: 새 enum 정의 전 값 이름을 MType.pas/MTypeCom.pas에 grep.

### #4 `const` 파라미터를 `var` 파라미터에 직접 전달 불가

**증상**: 컴파일 오류 — const로 받은 변수를 var를 요구하는 호출에 그대로 넘길 때.

**원인**: `const`로 선언된 매개변수는 읽기 전용이라 `var`(참조/수정 가능) 인자로 직접 못 넘김.

**해결**: 로컬 변수에 복사한 뒤 그 로컬을 var 인자로 전달.

**다음 체크**: 서드파티/공용 함수가 var 파라미터를 요구하는지 시그니처 먼저 확인.

### #7 서드파티(비표준 VCL) 라이브러리 API를 추정해서 사용

**증상**: 비표준 라이브러리 API 호출이 컴파일 오류 나거나 런타임에 의도와 다르게 동작.

**원인**: 시그니처·동작을 추정으로 작성. 표준 VCL이 아니면 관례가 안 통함.

**해결**: 해당 라이브러리 소스 파일을 먼저 열어 시그니처/동작 확인 후 사용.

**다음 체크**: 비표준 VCL 라이브러리 API는 호출 전 소스 grep 필수. 추정 금지.

---

## C. SQL / DBMS 분기

### #5 Sybase ↔ PostgreSQL 양립 — 불가피한 분기는 `TtsQuery.UsingPG`

**요약**: 두 DBMS를 동시 운용. 가능하면 양쪽에서 도는 SQL을 쓰고, 불가피하면 분기.

**핵심만**: `TtsQuery` 클래스 사용(프로젝트 내 TsQuery 우선, 없으면 Delphi 버전별 — D2007은 `PackageBL\DBLOGInPacks\UniDAC`, Berlin 이상은 `PackageBL\DBLOGInPacks\TsQuery`). 분기는 `TtsQuery.UsingPG` 프로퍼티로. 여러 줄 SQL은 `SQL.Add` 한 줄씩. 동적 값은 Named Parameter 대신 `QuotedStr` 등으로 직접 삽입. TsQuery.pas의 SQL 문법 메소드 적극 활용.

**다음 체크**: 새 SQL 작성 시 PG 전용/Sybase 전용 문법(날짜 함수, 문자열 함수, TOP/LIMIT 등)이 섞였는지 확인. 섞였으면 UsingPG 분기.

---

## D. DFM / UI 리소스

### #6 DFM에 임베드한 Glyph가 런타임 "Invalid bitmap"

**증상**: 런타임에 TBitBtn 등의 Glyph 로드 시 "Invalid bitmap" 오류.

**원인**: `Glyph.Data` hex 앞에 **BMP 크기 little-endian 4바이트 hex prefix가 누락**됨.

**해결**: `Glyph.Data = { NNNNNNNN424D...FF }` 형식 — `NNNNNNNN`은 BMP 데이터 크기의 LE 4바이트. 각 줄 64 hex 문자, 마지막 줄 끝에 `}`. JPG/PNG는 `System.Drawing`으로 **24bpp BMP** 변환 후 인코딩(BMP는 raw bytes 직접 읽기 — 변환 시 손상). 한글 경로는 ASCII 경로로 복사 후 처리. 스크립트: `.claude\gen_dfm_glyph.ps1`.

**다음 체크**: 임베드 후 4바이트 prefix 존재 확인. 한글/유니코드 경로 파일은 변환 전 ASCII 경로 복사.

---

<!-- 새 함정 추가 시: 위 카테고리에 "### #N 제목" + 증상/원인/해결/다음 체크 4단으로 append.
     인덱스(.claude/rules/pitfalls-index.md) 해당 카테고리에 "- **#N** 한 줄 요약" 추가. -->
