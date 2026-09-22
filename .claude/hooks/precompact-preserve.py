#!/usr/bin/env python3
"""Claude Code PreCompact Hook — 컴팩션 후에도 이어받을 수 있게 좌표만 남긴다.

설계 근거: docs/Upgrade_loop.md STEP 5-3.

왜 내용이 아니라 경로인가
  파일 내용을 통째로 뱉으면 그 자체가 컨텍스트를 다시 채운다. 컴팩션의 목적을
  스스로 무너뜨리는 셈이다. 어디를 보면 되는지와 현재 좌표만 남기고,
  다음 턴이 필요할 때 직접 읽게 한다.

무엇을 남기는가
  ACTIVE_ISSUE / PHASE / 스프린트 / 루프 중단 여부 / 상태 파일 경로.
  이것만 있으면 세션이 끊겨도 STATUS.md 기준으로 재개할 수 있다.

종료 코드는 항상 0이다. 이 훅은 게이트가 아니라 메모다.
"""

from __future__ import annotations

import sys
from pathlib import Path

HOOK_DIR = Path(__file__).resolve().parent
REPO = HOOK_DIR.parents[1]
sys.path.insert(0, str(REPO / ".claude" / "scripts"))

try:
    import loop_state
except Exception:
    loop_state = None


def emit(text: str) -> None:
    try:
        sys.stdout.buffer.write(text.encode("utf-8", errors="replace"))
        sys.stdout.buffer.flush()
    except Exception:
        try:
            sys.stdout.write(text.encode("ascii", "replace").decode("ascii"))
        except Exception:
            pass


def main() -> int:
    if loop_state is None:
        return 0
    try:
        issue = loop_state.resolve_active_issue()
    except Exception:
        return 0
    if not issue:
        return 0

    workspace = loop_state.workspace_dir(issue)
    status = loop_state.read_status(workspace)
    if not status:
        return 0

    lines = [
        "[작업 좌표 — 컴팩션 후 이어받기용]",
        f"  ACTIVE_ISSUE : {issue}",
        f"  PHASE        : {status.get('PHASE', '?')}",
        f"  SPRINT       : {status.get('CURRENT_SPRINT', '-')}",
        f"  TRACK        : {status.get('TRACK', '-')}",
    ]
    if status.get("LOOP") == "halted":
        lines.append(f"  ⛔ LOOP HALTED: {status.get('HALT_REASON', '')}")
        lines.append("     재개: python .claude/scripts/loop_state.py clear-halt")

    rel = workspace.relative_to(REPO).as_posix()
    lines += [
        "",
        "  아래 파일이 진행 상태의 단일 소스다. 필요할 때 직접 읽을 것:",
        f"    {rel}/STATUS.md              현재 PHASE와 진행률",
        f"    {rel}/sprints/{status.get('CURRENT_SPRINT', '{sprint}')}/GOAL.md   구현 계약",
        f"    {rel}/.loop/attempts.log     실패한 시도 이력 (같은 방법을 다시 쓰지 말 것)",
        "",
        "  막히면 /next 를 실행하면 현재 PHASE 기준 다음 명령을 안내한다.",
    ]
    emit("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
