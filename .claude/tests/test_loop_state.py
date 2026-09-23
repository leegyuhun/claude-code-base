"""loop_state — 카운터 · 상한 · 헛돌기 · scope 독립."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _harness import Result, action_of, run_py, status_field, temp_repo, write_status  # noqa: E402

SCRIPT_NAME = "loop_state.py"
ISSUE = "#208801"


def setup(root: Path, phase: str = "7", sprint: str = "sprint-01") -> Path:
    (root / ".claude" / "ACTIVE_ISSUE").write_text(ISSUE, encoding="utf-8")
    workspace = root / "workspace" / ISSUE
    write_status(workspace, phase=phase, sprint=sprint)
    return workspace


def call(script: Path, root: Path, *args: str) -> tuple[str, str]:
    _, out, _ = run_py(script, None, cwd=root, args=list(args))
    return action_of(out), out


def main() -> int:
    rep = Result("loop_state")

    # ACTIVE_ISSUE가 없으면 카운터를 만들지 않고 안전 통과
    with temp_repo(scripts=(SCRIPT_NAME,)) as root:
        script = root / ".claude" / "scripts" / SCRIPT_NAME
        action, _ = call(script, root, "status")
        rep.case("ACTIVE_ISSUE 없음 -> 통과", "continue", action)

    # 상한까지 누적 -> halt
    with temp_repo(scripts=(SCRIPT_NAME,)) as root:
        script = root / ".claude" / "scripts" / SCRIPT_NAME
        workspace = setup(root)
        action, _ = call(script, root, "status")
        rep.case("초기 status", "continue", action)

        action, _ = call(script, root, "bump", "--scope", "build",
                         "--signature", "build:E1:a.py:10", "--note", "import 추가")
        rep.case("bump 1/3", "continue", action)

        action, _ = call(script, root, "bump", "--scope", "build",
                         "--signature", "build:E2:b.py:20", "--note", "타입 수정")
        rep.case("bump 2/3 (다른 실패)", "continue", action)

        action, out = call(script, root, "bump", "--scope", "build",
                           "--signature", "build:E3:c.py:30", "--note", "재시도")
        rep.case("bump 3/3 -> 상한 halt", "halt", action, "이터레이션 상한" in out, out)
        rep.case("STATUS.md LOOP=halted", "halted", status_field(workspace, "LOOP"))
        rep.case("HALT_REASON 기록", True, bool(status_field(workspace, "HALT_REASON")))

        log = (workspace / ".loop" / "attempts.log").read_text(encoding="utf-8")
        rep.case("attempts.log 누적", True, log.count("[iter ") == 3 and "[HALT]" in log)

    # 헛돌기는 상한(3)보다 먼저 걸린다
    with temp_repo(scripts=(SCRIPT_NAME,)) as root:
        script = root / ".claude" / "scripts" / SCRIPT_NAME
        workspace = setup(root)
        call(script, root, "bump", "--scope", "feedback", "--signature", "SAME:x.py:99", "--note", "1차")
        action, out = call(script, root, "bump", "--scope", "feedback",
                           "--signature", "SAME:x.py:99", "--note", "2차")
        rep.case("동일 시그니처 2회 -> 헛돌기 halt", "halt", action, "헛돌기" in out, out)

        action, _ = call(script, root, "reset", "--scope", "feedback")
        rep.case("reset -> 복구", "continue", action, status_field(workspace, "LOOP") == "running")

    # scope는 서로 독립이다
    with temp_repo(scripts=(SCRIPT_NAME,)) as root:
        script = root / ".claude" / "scripts" / SCRIPT_NAME
        setup(root)
        for i in range(3):
            call(script, root, "bump", "--scope", "build", "--signature", f"S{i}", "--note", "x")
        action, _ = call(script, root, "bump", "--scope", "review:항목1",
                         "--signature", "R1", "--note", "리뷰 반려")
        rep.case("scope 독립 (build halt != review)", "continue", action)

    # PHASE가 바뀌면 그 PHASE 전용(build/contract)만 리셋한다.
    # 왕복 카운터(feedback/manual/review)는 살아야 한다 — 7→6→7 왕복을 세는 게 그것이다.
    with temp_repo(scripts=(SCRIPT_NAME,)) as root:
        script = root / ".claude" / "scripts" / SCRIPT_NAME
        workspace = setup(root)
        call(script, root, "bump", "--scope", "build", "--signature", "S1", "--note", "x")
        call(script, root, "bump", "--scope", "build", "--signature", "S2", "--note", "x")
        call(script, root, "bump", "--scope", "feedback", "--signature", "F1", "--note", "반려 1")
        write_status(workspace, phase="6")
        action, out = call(script, root, "bump", "--scope", "build", "--signature", "S3", "--note", "x")
        rep.case("PHASE 변경 -> build 리셋", "continue", action, "PHASE 변경 감지" in out, out)
        rep.case("build 1/3부터", True, "1/3" in out, out)
        action, out = call(script, root, "bump", "--scope", "feedback", "--signature", "F2", "--note", "반려 2")
        rep.case("PHASE 변경에도 feedback 유지 (2/3)", True, "2/3" in out, out)

    # 스프린트가 바뀌면 전부 리셋한다
    with temp_repo(scripts=(SCRIPT_NAME,)) as root:
        script = root / ".claude" / "scripts" / SCRIPT_NAME
        workspace = setup(root)
        call(script, root, "bump", "--scope", "feedback", "--signature", "F1", "--note", "x")
        call(script, root, "bump", "--scope", "feedback", "--signature", "F2", "--note", "x")
        write_status(workspace, phase="7", sprint="sprint-02")
        action, out = call(script, root, "bump", "--scope", "feedback", "--signature", "F3", "--note", "x")
        rep.case("스프린트 변경 -> 전체 리셋", "continue", action, "전체 리셋" in out and "1/3" in out, out)

    return rep.done()


if __name__ == "__main__":
    sys.exit(main())
