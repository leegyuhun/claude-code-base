---
description: "YSR 함정 인덱스 — 작업 중 놓치기 쉬운 케이스. 본문은 .claude/refs/pitfalls.md (부분 로드)."
---

# YSR 함정 인덱스

> 자동 로드는 이 인덱스만. 함정 본문은 `.claude/refs/pitfalls.md` — 작업 진입 시 키워드 `Grep` 또는 함정 번호 단위 `Read`.
>
> **목적**: 과거에 시간 잡아먹은 시행착오를 다시 안 밟기. 새 함정 발견 시 본문에 4단(증상·원인·해결·다음 체크)으로 append하고 여기 한 줄 추가.

## 사용 흐름

1. 작업 영역으로 **카테고리** 식별 (아래 매핑 표).
2. 해당 카테고리 함정 번호만 본문에서 부분 읽기.
3. 새 함정 발견 시 본문 끝 append + 이 인덱스 갱신.

```
Grep "UsingPG" path=".claude/refs/pitfalls.md" -n=true
Read ".claude/refs/pitfalls.md"   # 작거나 전체 훑을 때
```

---

## 카테고리별 함정

### A. 인코딩 / 파일 처리
- **#2** `.pas`/`.dfm`는 CP949 — Write 금지, Edit는 한글 줄 회피 (상세: `encoding-critical.md`)

### B. Delphi 언어 함정
- **#3** 새 enum 값 이름이 공용 타입(MType.pas 등)과 충돌 — 모듈 접두사 사용
- **#4** `const` 파라미터를 `var` 인자에 직접 전달 불가 — 로컬 복사 후 전달
- **#7** 서드파티(비표준 VCL) 라이브러리 API 추정 금지 — 소스 먼저 확인

### C. SQL / DBMS 분기
- **#5** Sybase ↔ PostgreSQL 양립 — 불가피한 분기는 `TtsQuery.UsingPG`

### D. DFM / UI 리소스
- **#6** DFM Glyph "Invalid bitmap" — BMP 크기 LE 4바이트 hex prefix 누락

### E. 빌드 / 패키지 / 조건부 정의
- (아직 없음)

### F. 하네스 / 도구 운영
- **#1** Bash 도구에서 PowerShell here-string(`@'...'@`) 사용 → 커밋 메시지 오염

---

## 빠른 매핑 (작업 → 점검 카테고리)

| 작업 종류 | 점검 함정 |
|---|---|
| `.pas`/`.dfm` 파일 편집 | A (#2) |
| Delphi 코드 신규 작성 (타입/enum/파라미터/외부 라이브러리) | B (#3, #4, #7) |
| SQL 작성/수정 | C (#5) |
| DFM 폼/버튼/이미지 작업 | D (#6) |
| git/커밋/셸 명령 | F (#1) |

새 함정 발견 시: 본문에 4단 형식 append → 이 인덱스 해당 카테고리에 한 줄 추가.
