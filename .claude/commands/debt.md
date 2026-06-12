# /debt — Tech Debt 종합 보고

## 워크스페이스 해석

1. `.claude/ACTIVE_ISSUE` 읽기 → ACTIVE_ISSUE 값 획득
2. 없으면 `git branch --show-current` 출력에서 `#(\d+)` 추출 (폴백)
3. 모두 실패 시 → "`⚠️ 활성 이슈를 확인할 수 없습니다.`" 출력 후 종료

WORKSPACE_DIR = `workspace/{ACTIVE_ISSUE}`

프로젝트 전체의 기술 부채를 수집하고 요약해줘.

## 수집 대상

1. **TODO 주석 스캔**
   - 전체 소스 코드에서 `TODO:` 패턴 검색
   - 특히 `[tech-debt]` 태그가 붙은 항목 우선 표시
   - 파일 경로, 라인 번호, 내용 포함

2. **OUT_OF_SCOPE.md 수집**
   - {WORKSPACE_DIR}/sprints/*/OUT_OF_SCOPE.md 파일 전체 읽기
   - 스프린트별로 그룹핑

3. **DONE.md Tech Debt 섹션**
   - {WORKSPACE_DIR}/sprints/*/DONE.md에서 "Tech Debt" 섹션 추출
   - 스프린트별로 그룹핑

4. **TECH_DEBT.md 중앙 집계**
   - {WORKSPACE_DIR}/sprints/TECH_DEBT.md 읽기 (있는 경우)

## 출력 형식

```
┌──────────────────────────────────────┐
│ Tech Debt 종합 보고                  │
│                                      │
│ 이슈:    {ACTIVE_ISSUE}              │
│ TODO 주석: N개                       │
│ 범위 외 사항: N개                    │
│ 누적 Tech Debt: N개                  │
└──────────────────────────────────────┘

## TODO 주석 (코드 내)
| 파일 | 라인 | 내용 |
|------|------|------|
| src/foo.pas | 42 | [tech-debt] 임시 하드코딩 |
| ...  | ...  | ...  |

## 범위 외 발견사항 (OUT_OF_SCOPE.md)
### sprint-01
- 내용 1
- 내용 2

### sprint-02
- ...

## DONE.md Tech Debt
### sprint-01
- 내용 1

### sprint-02
- ...
```

아무 항목도 없으면:
→ "Tech Debt가 없습니다."
