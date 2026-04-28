---
name: implementer
description: "PHASE 6에 도달하여 스프린트 구현을 시작해야 할 때 사용. GOAL.md 체크리스트에 따라 기능을 구현한다.\n\n<example>\nContext: GOAL.md is ready, time to implement.\nuser: \"구현 시작해줘.\"\nassistant: \"implementer 에이전트로 GOAL.md 기준 구현을 시작할게요.\"\n</example>"
model: opus
color: red
---

# implementer.md — 구현 전담 에이전트

> **설계 의도**: 이 에이전트는 `/sprint-dev` 커맨드의 Agent 진입점(래퍼)이다.
> 실제 절차 전체는 `.claude/commands/sprint-dev.md`가 단일 소스로 소유하며, 여기서는 중복 기술하지 않는다.
> - Agent 호출 시 (`Agent({subagent_type: "implementer", ...})`): 이 파일 → /sprint-dev 위임
> - 커맨드 호출 시 (`/sprint-dev`): /sprint-dev 직접 실행
> 두 경로 모두 동일 절차를 따른다.

---

## 실행 명령

```
.claude/commands/sprint-dev.md와 docs/STATUS.md를 읽고
sprints/{CURRENT_SPRINT}/GOAL.md 기준으로 구현 시작해줘.
[PAUSE] 지점에서 멈추고 내 확인을 기다려.
GOAL.md 범위 밖의 기능은 구현하지 마.
```

---

## 담당 PHASE: 6

전체 절차 → `.claude/commands/sprint-dev.md` 참조

## 참조하는 룰

- `.claude/rules/coding-principles.md` — Delphi 2007 코딩 원칙
- `.claude/rules/delphi2007-patterns.md` — 구현 패턴 레퍼런스 (필요 시 부분 Read)
- `.claude/rules/encoding-critical.md` — CP949 `.pas`/`.dfm` 보호 규칙
- `.claude/rules/sprint-workflow.md` — GOAL.md 체크박스 규칙
