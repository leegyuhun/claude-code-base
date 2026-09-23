"""PostToolUse 빠른 게이트 — harness.json의 fast_check 실행과 빠른 경로."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _harness import Result, run_py, temp_repo  # noqa: E402

HOOK_NAME = "posttooluse-fast-gate.py"
SCRIPTS = ("harness_config.py",)

PY = f'"{sys.executable}"'
# 변경 파일 안에 "BAD"가 있으면 실패하는 가짜 린터. {files}로 대상 파일을 받는다
LINT = (
    f'{PY} -c "import sys; bad=[f for f in sys.argv[1:] if \'BAD\' in open(f).read()];'
    f' print(*(f+\': lint error\' for f in bad)); sys.exit(1 if bad else 0)" {{files}}'
)
GLOBS = ["src/**/*.py"]

BASH = lambda c: {"tool_name": "Bash", "tool_input": {"command": c}}
TOUCH = BASH("python fix.py")


def git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, capture_output=True, timeout=60)


def seed(root: Path) -> Path:
    (root / "src").mkdir(exist_ok=True)
    (root / "src" / "app.py").write_text("print('ok')\n", encoding="utf-8")
    (root / "docs").mkdir(exist_ok=True)
    (root / "docs" / "note.md").write_text("note\n", encoding="utf-8")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "init")
    return root / "src" / "app.py"


def harness(cmd: str) -> dict:
    return {"source_globs": GLOBS, "fast_check": {"cmd": cmd, "timeout": 60}}


def main() -> int:
    rep = Result("PostToolUse 빠른 게이트")

    # fast_check 미설정 = 검증기 부재. 변경이 망가져 있어도 조용히 통과한다
    with temp_repo(scripts=SCRIPTS, hooks=(HOOK_NAME,), git=True, harness=harness("")) as root:
        hook = root / ".claude" / "hooks" / HOOK_NAME
        seed(root).write_text("BAD\n", encoding="utf-8")
        rc, out, err = run_py(hook, TOUCH, cwd=root)
        rep.case("fast_check 없음 -> 통과", 0, rc, err.strip() == "", err)

    with temp_repo(scripts=SCRIPTS, hooks=(HOOK_NAME,), git=True, harness=harness(LINT)) as root:
        hook = root / ".claude" / "hooks" / HOOK_NAME
        src = seed(root)

        rc, out, err = run_py(hook, TOUCH, cwd=root)
        rep.case("변경 없음 -> 통과", 0, rc, True, err)

        src.write_text("print('fine')\n", encoding="utf-8")
        rc, out, err = run_py(hook, TOUCH, cwd=root)
        rep.case("린트 통과 수정 -> 통과", 0, rc, True, err)

        # Bash는 명령 문자열과 무관하게 항상 검사한다 — `python fix.py`가 소스를 망칠 수 있다
        src.write_text("BAD\n", encoding="utf-8")
        rc, out, err = run_py(hook, TOUCH, cwd=root)
        rep.case("Bash 뒤 린트 실패 -> 교정요구", 2, rc,
                 "fast_check 실패" in err and "lint error" in err, err)

        # {files}에는 변경된 소스만 들어간다 — 소스가 아닌 파일은 대상이 아니다
        rep.case("{files} 치환 -> 변경 소스 전달", True, "src/app.py" in err, err)

        # Write/Edit는 file_path로 판단한다 — 소스가 아닌 파일 편집은 즉시 통과
        rc, out, err = run_py(
            hook, {"tool_name": "Write", "tool_input": {"file_path": "docs/note.md"}}, cwd=root)
        rep.case("Write 비소스 -> 빠른 경로 통과", 0, rc, err.strip() == "", err)

        rc, out, err = run_py(
            hook, {"tool_name": "Edit", "tool_input": {"file_path": "src/app.py"}}, cwd=root)
        rep.case("Edit 소스 -> 교정요구", 2, rc, "lint error" in err, err)

        abs_path = str(root / "src" / "app.py")
        rc, out, err = run_py(
            hook, {"tool_name": "Write", "tool_input": {"file_path": abs_path}}, cwd=root)
        rep.case("절대경로 소스 -> 교정요구", 2, rc, "lint error" in err, err)

        # 비소스 파일만 바뀐 경우는 린트 대상이 없다
        git(root, "checkout", "--", ".")
        (root / "docs" / "note.md").write_text("BAD\n", encoding="utf-8")
        rc, out, err = run_py(hook, TOUCH, cwd=root)
        rep.case("비소스만 변경 -> 통과", 0, rc, err.strip() == "", err)

    # 도구가 없는 것은 실패가 아니다 (막으면 편집마다 헛돈다)
    missing = harness("definitely-not-a-linter-xyz {files}")
    with temp_repo(scripts=SCRIPTS, hooks=(HOOK_NAME,), git=True, harness=missing) as root:
        hook = root / ".claude" / "hooks" / HOOK_NAME
        seed(root).write_text("BAD\n", encoding="utf-8")
        rc, out, err = run_py(hook, TOUCH, cwd=root)
        rep.case("린터 명령 없음 -> 부재로 통과", 0, rc, "검증기 부재" in out, out + err)

    # 입력 불량은 훅 문제다. 흐름을 막지 않는다
    with temp_repo(scripts=SCRIPTS, hooks=(HOOK_NAME,), harness=harness(LINT)) as root:
        hook = root / ".claude" / "hooks" / HOOK_NAME
        rc, out, err = run_py(hook, None, cwd=root)
        rep.case("빈 입력 -> 통과", 0, rc, True, err)

    return rep.done()


if __name__ == "__main__":
    sys.exit(main())
