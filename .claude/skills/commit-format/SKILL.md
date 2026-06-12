---
name: commit-format
description: YSR EMR 프로젝트 스타일의 한국어 커밋 메시지를 작성한다. 스프린트 형식으로 커밋 메시지와 브랜치명을 생성한다. commit-writer 에이전트가 이 스킬을 사용한다.
---

# 커밋 메시지 형식 스킬

---

## 모드 1: Sprint 커밋 형식

```
fix: #{이슈번호} {목표 요약 한 줄} - {sprint-name}

　# 변경 내용
　　- 변경사항 1
　　　: 부연 설명
　　- 변경사항 2
　　　: 부연설명
　# 관련파일
　　- 수정파일.pas (수정 내용 요약)
```

### 핵심 규칙

| 항목 | 규칙 |
|------|------|
| 첫 줄 | `fix: #{이슈번호} {목표 요약} - {sprint-name}` |
| 이슈번호 | GOAL.md 또는 브랜치명에서 추출; 없으면 `#?` |
| 본문 들여쓰기 | 전각 공백(`　`) 사용 — 일반 스페이스 아님 |
| 계층 | `#` 대분류 → `-` 항목 → `:` 설명 |
| 언어 | 한국어 (함수명·파일명은 원어) |

### Sprint 커밋 예시

```
fix: #207500 처방 인쇄 미리보기 기능 추가 - sprint-01

　# 변경 내용
　　- 미리보기 폼 신규 추가
　　　: TPrescriptionPreviewForm 구현
　　- 인쇄 버튼 이벤트 연결
　　　: TMainForm.btnPrintClick 핸들러 수정
　# 관련파일
　　- PrescriptionPreview.pas (미리보기 폼 신규 생성)
　　- MainForm.pas (인쇄 버튼 이벤트 연결)
```

---

## 모드 2: Defect 커밋 형식

```
fix: #{이슈번호} {수정 요약 한 줄}

　# 변경 내용
　　- 변경사항 1
　　　: 부연 설명
　# 관련파일
　　- 수정파일.pas (수정 내용 요약)
```

### 핵심 규칙

| 항목 | 규칙 |
|------|------|
| 첫 줄 | `fix: #{이슈번호} {수정 요약}` (**sprint-name 접미사 없음**) |
| 이슈번호 | PRD 또는 브랜치명에서 추출; 없으면 `#?` |
| 본문 들여쓰기 | 전각 공백(`　`) — Sprint와 동일 |
| 계층 | `#` 대분류 → `-` 항목 → `:` 설명 |

### Defect 커밋 예시

```
fix: #208801 환자 조회 시 삭제된 항목 노출 문제 수정

　# 변경 내용
　　- 환자 조회 쿼리에 IsDeleted=0 조건 추가
　　　: TPaInfo.LoadPatients SQL 수정
　# 관련파일
　　- PaInfo.pas (조회 쿼리 수정)
```

---

## 브랜치 네이밍

| 유형 | 패턴 | 예시 |
|------|------|------|
| Sprint | `{base}_sprint-{NN}` | `main_delphi_sprint-01` |
| Defect | `{base}_#{이슈번호}` (기존 브랜치 그대로 사용) | `main_delphi_#208801` |

---

## 작성 절차

1. `git diff`로 변경 내용 파악 → `# 변경내용` 블록 작성
2. 수정 파일 목록 → `# 관련파일` 섹션 작성
3. 전각 공백 들여쓰기 확인
4. 저장 경로:
   - TRACK=sprint: `{WORKSPACE_DIR}/sprints/{sprint_name}/COMMIT_MESSAGE.md`
   - TRACK=defect: `{WORKSPACE_DIR}/COMMIT_MESSAGE.md`
