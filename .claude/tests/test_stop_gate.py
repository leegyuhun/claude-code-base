"""Stop 훅 — PHASE 게이팅 · 검증기 부재 구분 · 무한루프 방지 · 탈출.

docs/Upgrade_loop.md STEP 7 검수 시나리오에 대응한다.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _harness import Result, run_py, status_field, temp_repo, write_status  # noqa: E402

HOOK_NAME = "stop-loop-gate.py"
NEEDED_SCRIPTS = ("gate_harness.py", "loop_state.py")
ISSUE = "#208801"

GOAL_TMPL = """# sprint-01 상세 계획

## 목표
테스트

## 검증 계약 (Validator가 이 기준으로 채점)
- [{a}] 빌드: build.bat debug 0 error (자동)
- [{b}] 환자 조회: 목록에 10건 표시 (수동)

## 수동 테스트 시나리오
1. 없음
"""


def setup(root: Path, phase: str = "7", loop: str = "running",
          goal: tuple[str, str] = ("x", "x"), with_issue: bool = True) -> Path | None:
    if not with_issue:
        return None
    (root / ".claude" / "ACTIVE_ISSUE").write_text(ISSUE, encoding="utf-8")
    workspace = root / "workspace" / ISSUE
    (workspace / "sprints" / "sprint-01").mkdir(parents=True, exist_ok=True)
    write_status(workspace, phase=phase, loop=loop)
    (workspace / "sprints" / "sprint-01" / "GOAL.md").write_text(
        GOAL_TMPL.format(a=goal[0], b=goal[1]), encoding="utf-8")
    return workspace


def fire(root: Path, stop_active: bool = False) -> tuple[int, str]:
    hook = root / ".claude" / "hooks" / HOOK_NAME
    rc, _, err = run_py(hook, {"stop_hook_active": stop_active, "session_id": "t"}, cwd=root)
    return rc, err


def main() -> int:
    rep = Result("Stop 훅")
    common = {"scripts": NEEDED_SCRIPTS, "hooks": (HOOK_NAME,)}

    # 층 A가 깨지면 종료를 막는다 + stop_hook_active면 즉시 통과
    with temp_repo(**common) as root:
        setup(root)
        (root / ".claude" / "settings.json").write_text('{"permissions":,}', encoding="utf-8")
        rc, err = fire(root)
        rep.case("하네스 파손 -> 종료 차단", 2, rc, "harness" in err, err)
        rc, err = fire(root, stop_active=True)
        rep.case("stop_hook_active -> 즉시 통과", 0, rc, err.strip() == "", err)

    with temp_repo(**common) as root:
        setup(root, phase="7", goal=(" ", " "))
        rc, err = fire(root)
        rep.case("검증계약 미충족 -> 차단", 2, rc, "검증 계약 미충족 2건" in err, err)

    with temp_repo(**common) as root:
        setup(root, phase="7", goal=("x", "x"))
        rc, err = fire(root)
        rep.case("검증계약 충족 -> 통과", 0, rc, err.strip() == "", err)

    # PHASE 8은 수동 UI 테스트 대기 — 절대 막지 않는다
    with temp_repo(**common) as root:
        setup(root, phase="8", goal=(" ", " "))
        rc, err = fire(root)
        rep.case("PHASE 8 -> 무조건 통과", 0, rc, err.strip() == "", err)

    with temp_repo(**common) as root:
        setup(root, phase="5", goal=(" ", " "))
        rc, err = fire(root)
        rep.case("PHASE 5 -> 게이트 없음", 0, rc, True, err)

    with temp_repo(**common) as root:
        setup(root, phase="7", loop="halted", goal=(" ", " "))
        rc, err = fire(root)
        rep.case("LOOP=halted -> 통과", 0, rc, err.strip() == "", err)

    with temp_repo(**common) as root:
        setup(root, with_issue=False)
        rc, err = fire(root)
        rep.case("ACTIVE_ISSUE 없음 -> 통과", 0, rc, err.strip() == "", err)

    # 검증기 부재는 실패가 아니다 (이걸 exit 2로 처리하면 루프가 영원히 헛돈다)
    with temp_repo(**common, git=True) as root:
        setup(root, phase="6")
        (root / "dummy.pas").write_bytes(b"unit d;\n")
        rc, err = fire(root)
        rep.case("build.bat 없음 -> 부재로 통과", 0, rc, "검증기 부재" in err, err)

    with temp_repo(**common, git=True) as root:
        setup(root, phase="6")
        (root / "build.bat").write_text(
            "@echo off\necho [Error] rsvars.bat not found\nexit /b 1\n", encoding="utf-8")
        (root / "sub").mkdir()
        (root / "sub" / "P.dproj").write_text("<Project/>", encoding="utf-8")
        (root / "sub" / "a.pas").write_bytes(b"unit a;\n")
        rc, err = fire(root)
        rep.case("빌드환경 없음 -> 부재로 통과", 0, rc, "검증기 부재" in err, err)

    # 반복 실패 -> 탈출 (차단을 풀고 사람에게 넘긴다)
    with temp_repo(**common) as root:
        workspace = setup(root, phase="7", goal=(" ", " "))
        fire(root)
        rc, err = fire(root)
        rep.case("동일 실패 2회 -> 탈출", 0, rc, "루프 중단" in err, err)
        log = (workspace / ".loop" / "attempts.log").read_text(encoding="utf-8")
        rep.case("halt 기록 (STATUS + log)", True,
                 status_field(workspace, "LOOP") == "halted" and "HALT" in log)

    return rep.done()


if __name__ == "__main__":
    sys.exit(main())
