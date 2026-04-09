---
name: ysr-maintenance
description: YSR EMR 시스템의 유지보수 워크플로우를 총괄한다. 버그 수정, 이슈 처리, 코드 분석, 커밋 메시지 작성, 영향도 분석 등 모든 유지보수 작업 요청 시 이 스킬을 사용하라. "이슈 #번호 수정", "버그 고쳐줘", "원인 파악해줘", "커밋 메시지 만들어줘", "어떤 파일 봐야 해", "다시 실행", "재분석", "수정 보완" 등의 요청에도 반드시 이 스킬을 사용할 것.
---

# YSR 유지보수 오케스트레이터

**실행 모드:** 서브 에이전트 (순차 파이프라인)

## 전체 워크플로우

```
[오케스트레이터]
    ├── Phase 0: 컨텍스트 확인 (신규/재실행/부분 재실행)
    ├── Phase 1: 버그 조사 (bug-investigator 서브 에이전트)
    ├── Phase 2: 코드 수정 (patch-author 서브 에이전트)  ← 사용자 선택적
    └── Phase 3: 커밋 메시지 작성 (commit-writer 서브 에이전트)  ← 사용자 선택적
```

## Phase 0: 컨텍스트 확인

작업 시작 전 기존 산출물을 확인한다:

```
_workspace/ 존재 + 부분 수정 요청 → 부분 재실행 (해당 Phase만)
_workspace/ 존재 + 새 이슈 입력  → 새 실행 (_workspace를 _workspace_prev/로 이동)
_workspace/ 미존재               → 초기 실행
```

사용자 요청에서 다음을 파악한다:
- **이슈 번호** (`#숫자` 패턴) — 없으면 사용자에게 확인
- **요청 범위** — 조사만? 수정까지? 커밋 메시지까지?
- **힌트 파일** — 사용자가 특정 파일을 언급했는지

요청 범위가 불명확하면 기본값: **조사 → 수정 → 커밋** 전체 실행.

## Phase 1: 버그 조사

`bug-investigator` 에이전트를 서브 에이전트로 호출한다.

```python
Agent(
    subagent_type="Explore",
    model="opus",
    description="YSR 버그 조사",
    prompt=f"""
    당신은 YSR EMR 코드베이스의 bug-investigator입니다.
    .claude/agents/bug-investigator.md의 역할 정의를 읽고 따르세요.
    .claude/skills/investigate/SKILL.md의 탐색 전략을 사용하세요.
    .claude/skills/redmine/SKILL.md의 방법으로 Redmine 이슈를 먼저 조회하세요.
    
    이슈 번호: #{issue_id}
    버그 현상 (사용자 보충 설명): {description}
    힌트 파일: {hint_files}
    .env 위치: E:/Source/ysr/.env
    
    분석 결과를 _workspace/01_investigation.md에 저장하세요.
    재현이 어려운 버그라면 재현 가이드도 포함하세요.
    프로젝트 루트: E:/Source/ysr/trunk/
    """
)
```

산출물: `_workspace/01_investigation.md`

## Phase 2: 코드 수정 (선택적)

사용자가 수정을 요청한 경우에만 실행. `patch-author` 에이전트를 호출한다.

```python
Agent(
    subagent_type="general-purpose",
    model="opus",
    description="YSR 코드 패치",
    prompt=f"""
    당신은 YSR EMR 코드베이스의 patch-author입니다.
    .claude/agents/patch-author.md의 역할 정의를 읽고 따르세요.
    .claude/skills/patch/SKILL.md의 수정 원칙을 사용하세요.
    .claude/rules/encoding-critical.md의 인코딩 규칙을 반드시 먼저 읽고 따르세요 (CP949 필수).
    .claude/rules/coding-principles.md의 Delphi 코딩 원칙을 따르세요 (공유 유닛 변경 시 특히 주의).
    
    이슈 번호: #{issue_id}
    분석 결과: _workspace/01_investigation.md를 읽으세요.
    
    코드를 수정하고 결과를 _workspace/02_patch_summary.md에 저장하세요.
    프로젝트 루트: E:/Source/ysr/trunk/
    """
)
```

산출물: `_workspace/02_patch_summary.md`

## Phase 3: 커밋 메시지 작성 (선택적)

`commit-writer` 에이전트를 호출한다.

```python
Agent(
    subagent_type="general-purpose",
    model="opus",
    description="YSR 커밋 메시지 작성",
    prompt=f"""
    당신은 YSR EMR 프로젝트의 commit-writer입니다.
    .claude/agents/commit-writer.md의 역할 정의를 읽고 따르세요.
    .claude/skills/commit-format/SKILL.md의 형식 규칙을 사용하세요.
    
    이슈 번호: #{issue_id}
    조사 결과: _workspace/01_investigation.md를 읽으세요.
    수정 요약: _workspace/02_patch_summary.md를 읽으세요.
    
    커밋 메시지와 브랜치명을 _workspace/03_commit_message.md에 저장하세요.
    """
)
```

산출물: `_workspace/03_commit_message.md`

## 에러 핸들링

| 상황 | 처리 방법 |
|------|----------|
| 이슈 번호 없음 | 사용자에게 확인 요청 후 대기 |
| Phase 1 실패 | 실패 이유 보고, Phase 2 건너뜀 |
| Phase 2 실패 | 실패 이유 보고, Phase 3는 조사 결과만으로 진행 |
| 파일 탐색 결과 없음 | 탐색 범위 확장 후 재시도 1회, 그래도 없으면 "미발견" 보고 |

## 데이터 흐름

```
사용자 요청
    ↓
_workspace/01_investigation.md  ← Phase 1 산출물
    ↓
_workspace/02_patch_summary.md  ← Phase 2 산출물
    ↓
_workspace/03_commit_message.md ← Phase 3 산출물
    ↓
사용자에게 커밋 메시지 및 적용 방법 전달
```

## 최종 보고

모든 Phase 완료 후 사용자에게 요약 보고:
1. 발견된 근본 원인 (1~2문장)
2. 수정된 파일 목록
3. 커밋 메시지 전문
4. `git` 명령어 (브랜치 생성 → 스테이징 → 커밋)
5. 재현 가이드 (환경/데이터/시퀀스 의존 버그일 경우)

## 테스트 시나리오

### 정상 흐름
```
입력: "이슈 #207500 확인해줘. 프린터 포트가 갱신 안 된다는 버그야"
예상 흐름: Phase 0 (신규) → Phase 1 (조사) → [사용자 확인] → Phase 2 (수정) → Phase 3 (커밋)
예상 산출물: 01_investigation.md, 02_patch_summary.md, 03_commit_message.md
```

### 에러 흐름
```
입력: "이 버그 수정해줘" (이슈 번호 없음)
예상 흐름: Phase 0에서 멈추고 "이슈 번호를 알려주시겠어요?" 질문
```

### 부분 재실행
```
입력: "커밋 메시지만 다시 만들어줘"
예상 흐름: Phase 0에서 _workspace/ 확인 → Phase 3만 재실행
```
