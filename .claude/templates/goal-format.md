# GOAL.md 작성 양식 (YSR Sprint Template)

> 이 파일은 planner.md가 GOAL.md 작성 시 참조하는 템플릿이다.
> GOAL.md 저장 전 반드시 아래 자기검증 체크리스트를 통과해야 한다.

---

## 템플릿

```markdown
# {CURRENT_SPRINT} 상세 계획

## 목표
(한 줄 요약)

## 선행 스프린트
- sprint-XX (없으면 "없음")

## 구현 기능 체크리스트
- [ ] 기능 1 (예상 소요: Xh)
- [ ] 기능 2 (예상 소요: Xh)

## 검증 계약 (Validator가 이 기준으로 채점)
각 항목에 검증 방법과 측정 기준을 명시한다. Validator는 이 계약을 기반으로 합격/불합격을 판정한다.
- [ ] 빌드: build.bat debug 0 error (✅ 자동)
- [ ] {기능명}: {측정 가능한 성공 기준} (⚠️ 수동)

## 예상 산출물
### 신규/수정 파일
- path/to/UnitName.pas
- path/to/FormName.dfm

### 추가될 폼/다이얼로그
- TfrmXxx: 설명 (없으면 "없음")

### DB 변경사항
- 변경 테이블/쿼리: (없으면 "없음")

## 공용 유틸 참조 (재사용 필수)
- 문자열: `Common\Class\MString.pas`
- 범용 함수: `Common\Func\MUtil.pas`, `MCOMFunction.pas`, `MyFunc.pas`
- DB 쿼리: `TtsQuery` (SQL.Add 방식, QuotedStr 사용, Named Parameter 금지)
- DBMS 분기 필요 시: `TtsQuery.UsingPg`

## YSR 구현 주의사항
- `.pas`/`.dfm` 파일: Write 도구 절대 금지 → Edit 도구만 사용
- Edit 도구 사용 시: old_string/new_string 경계에 한글 포함 줄 금지
- 한글 주석 추가: Python `encoding='cp949'` 방식만 허용
- master 브랜치 직접 커밋 금지
- (공유 유닛 수정이 있다면) 영향 범위: {영향받는 프로젝트 목록}

## 관련 도메인 용어
(위 도메인 자료에서 참조한 핵심 용어 3~5개
 — 보험 청구 예시: TInsType.BOHUM, CalcBohumryo(), bohoBoninType
 — 진료실 예시: TTreatment.WriteToTable(), WM_MAKE_SUNAB, TdmCtData.VitalWin)

## 기술 고려사항
(구현 시 주의할 기술적 내용, 공유 유닛 영향 범위, CP949 인코딩 주의사항 등)

## 수동 테스트 시나리오
(PHASE 8에서 사용할 테스트 케이스 미리 작성)
1. [기능명]
   - 진입: 메뉴 → XX → XX (또는 단축키 F?)
   - 시나리오: ① → ② → ③
   - 예상 결과:
```

---

## GOAL.md 작성 완료 후 자기검증 체크리스트

> 참조: `.claude/skills/writing-plans/SKILL.md`
>
> **GOAL.md 저장 전** 아래 항목을 직접 체크한다. 실패 항목이 있으면 수정 후 재체크.

```
□ 수정할 파일 경로가 구체적으로 나열됐는가?
  (예: FwChart\Forms\TreatForm.pas — "관련 파일"처럼 모호하면 실패)

□ 재사용해야 할 공용 유틸이 명시됐는가?
  (MUtil.pas, MCOMFunction.pas, TtsQuery 등 — "공용 유틸 활용"처럼 막연하면 실패)

□ "하지 말아야 할 것"이 포함됐는가?
  (Write 도구 금지, master 직접 커밋 금지 등 YSR 구현 주의사항 섹션 존재)

□ 검증 계약 항목이 측정 가능한가?
  ("정상 동작"이 아닌 "빌드 0 오류", "X 필드에 Y 값 표시", "버튼 클릭 시 Z 화면 전환" 수준)

□ 이 문서만 보고 대화 없이 구현 가능한가?
  (Implementer가 추가 질문 없이 구현 가능한지 — 불분명한 부분 있으면 보완)
```

전부 통과 시 → GOAL.md 저장 후 5-6 완료 출력으로 진행
실패 항목 있으면 → 해당 섹션 수정 후 해당 항목만 재체크