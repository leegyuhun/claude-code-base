# /branch — 브랜치 생성

## 인수 처리 (`$ARGUMENTS`)

`$ARGUMENTS`에서 **베이스 브랜치**와 **신규 브랜치명**을 추출한다.

```
패턴 1: 베이스 명시
  "master 기준으로 2026_다빈도"   → BASE=master      NEW=2026_다빈도
  "master 2026_다빈도"            → BASE=master      NEW=2026_다빈도
  "2026_다빈도 from master"       → BASE=master      NEW=2026_다빈도

패턴 2: 베이스 생략 (신규 브랜치명만)
  "2026_다빈도"                   → BASE=현재 브랜치  NEW=2026_다빈도

식별 규칙:
  - "기준으로", "기준", "from", "에서" 앞의 토큰 → BASE
  - git 기존 브랜치명(main, master, develop 등)이 포함되면 → BASE 후보
  - 나머지 또는 유일한 토큰 → NEW 브랜치명
```

---

## 실행 절차

### 1단계: 현재 상태 파악

```bash
git branch --show-current          # 현재 브랜치
git status --short                 # 미커밋 변경사항 확인
git branch -a | grep "^  {BASE}"  # BASE 브랜치 존재 여부
```

### 2단계: 확인 출력 후 [PAUSE]

```
┌─────────────────────────────────────┐
│ 브랜치 생성                          │
│                                     │
│ 베이스: {BASE}                      │
│ 신규:   {NEW}                       │
│                                     │
│ 생성 후 {NEW}으로 이동합니다.        │
└─────────────────────────────────────┘
```

경고 조건 (경고만 표시, 실행은 계속):
- 미커밋 변경사항 있음 → "⚠️ 미커밋 변경사항이 있습니다."
- BASE가 현재 브랜치와 다름 → BASE로 먼저 이동 필요

[PAUSE] "생성할까요? (예/아니오)"

### 3단계: 브랜치 생성

**BASE = 현재 브랜치인 경우:**
```bash
git checkout -b {NEW}
```

**BASE ≠ 현재 브랜치인 경우:**
```bash
# 원격에서 최신 BASE 가져오기
git fetch origin {BASE} 2>/dev/null || true
# BASE 기준 브랜치 생성 (현재 브랜치 이동 없이)
git checkout -b {NEW} {BASE} 2>/dev/null || git checkout -b {NEW} origin/{BASE}
```

### 4단계: 완료 보고

```
✅ 브랜치 생성 완료

   {BASE} → {NEW}
   현재 위치: {NEW}

git push -u origin {NEW}   ← 원격에 올리려면 이 명령어 실행
```

---

## 에러 처리

| 상황 | 처리 |
|------|------|
| NEW 브랜치 이미 존재 | "⚠️ '{NEW}' 브랜치가 이미 있습니다. 이동할까요? (예/아니오)" |
| BASE 브랜치 없음 (로컬+원격) | "'{BASE}' 브랜치를 찾을 수 없습니다. 브랜치명을 확인해주세요." |
| 인수 없음 | "생성할 브랜치명을 입력해주세요. 예: /branch 2026_다빈도" |
