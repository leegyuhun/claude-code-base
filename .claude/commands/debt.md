# /debt — Tech Debt 종합 보고

프로젝트 전체의 기술 부채를 수집하고 요약해줘.

## 수집 대상

1. **TODO 주석 스캔**
   - `**/*.cs` 파일에서 `TODO:` 패턴 검색
   - 특히 `[tech-debt]` 태그가 붙은 항목 우선 표시
   - 파일 경로, 라인 번호, 내용 포함

2. **OUT_OF_SCOPE.md 수집**
   - sprints/*/OUT_OF_SCOPE.md 파일 전체 읽기
   - 스프린트별로 그룹핑

3. **DONE.md Tech Debt 섹션**
   - sprints/*/DONE.md에서 "Tech Debt" 섹션 추출
   - 스프린트별로 그룹핑

## 출력 형식

```
┌──────────────────────────────────────┐
│ Tech Debt 종합 보고                  │
│                                      │
│ TODO 주석: N개                       │
│ 범위 외 사항: N개                    │
│ 누적 Tech Debt: N개                  │
└──────────────────────────────────────┘

## TODO 주석 (코드 내)
| 파일 | 라인 | 내용 |
|------|------|------|
| src/Foo.cs | 42 | [tech-debt] 임시 하드코딩 |
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
