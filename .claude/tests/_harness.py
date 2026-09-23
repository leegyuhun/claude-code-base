"""하네스 테스트 공통 헬퍼.

이 디렉터리의 테스트는 훅과 스크립트의 회귀를 잡는 것이 목적이다.
`gate_harness.py`가 하네스의 "문법"을 본다면, 여기는 "동작"을 본다.

경로 원칙
  절대 경로를 박지 않는다. REPO는 이 파일 위치에서 계산하고, 격리 레포는
  tempfile로 만든다 — 다른 사람 PC에서도, CI에서도 그대로 돌아야 한다.

실행
  python .claude/tests/run_all.py          전체
  python .claude/tests/test_guards.py      개별
"""

from __future__ import annotations

import io
import json
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, io.UnsupportedOperation):
        pass

REPO = Path(__file__).resolve().parents[2]
HOOKS = REPO / ".claude" / "hooks"
SCRIPTS = REPO / ".claude" / "scripts"


class Result:
    """케이스 집계. 실패한 것만 상세를 찍는다."""

    def __init__(self, title: str) -> None:
        self.title = title
        self.passed = 0
        self.failed = 0
        print(f"=== {title} ===")

    def case(self, name: str, expect, got, extra: bool = True, detail: str = "") -> None:
        ok = got == expect and extra
        if ok:
            self.passed += 1
        else:
            self.failed += 1
        mark = "OK" if ok else "FAIL"
        print(f"  {name:<42} {got!s:>4} (기대 {expect}) {mark}")
        if not ok and detail.strip():
            for line in detail.strip().splitlines()[:4]:
                print(f"       {line[:160]}")

    def done(self) -> int:
        total = self.passed + self.failed
        if self.failed:
            print(f"  -> FAIL {self.failed}/{total}\n")
            return 1
        print(f"  -> PASS {self.passed}/{total}\n")
        return 0


def run_py(script: Path, payload: dict | None = None, cwd: Path | None = None,
           args: list[str] | None = None, timeout: int = 300) -> tuple[int, str, str]:
    """python 스크립트를 실행하고 (exit code, stdout, stderr)를 돌려준다.

    payload가 주어지면 JSON으로 직렬화해 stdin에 넣는다 (훅 호출 형태).
    payload가 None이면 stdin을 비운다 — 빈 입력 처리도 테스트 대상이다.
    """
    data = b"" if payload is None else json.dumps(payload).encode("utf-8")
    proc = subprocess.run(
        [sys.executable, str(script), *(args or [])],
        input=data,
        capture_output=True,
        timeout=timeout,
        cwd=str(cwd or REPO),
    )
    return (
        proc.returncode,
        proc.stdout.decode("utf-8", errors="replace"),
        proc.stderr.decode("utf-8", errors="replace"),
    )


def action_of(stdout: str) -> str:
    """loop_state / policy 류가 마지막 줄에 내보내는 ACTION= 값."""
    action = ""
    for line in stdout.splitlines():
        if line.startswith("ACTION="):
            action = line.split("=", 1)[1].strip()
    return action


@contextmanager
def temp_repo(scripts: tuple[str, ...] = (), hooks: tuple[str, ...] = (),
              git: bool = False, harness: dict | None = None) -> Iterator[Path]:
    """격리된 가짜 레포를 만든다.

    실제 훅/스크립트를 복사해 넣으므로, 안에서 실행하면 REPO가 이 임시 디렉터리로
    잡힌다(모두 __file__ 기준 parents[2]를 쓴다). 실제 레포를 오염시키지 않는다.
    harness가 주어지면 `.claude/harness.json`으로 쓴다 (없으면 빈 어댑터 — 검증기 부재).
    """
    root = Path(tempfile.mkdtemp(prefix="claude-harness-"))
    try:
        (root / ".claude" / "scripts").mkdir(parents=True)
        (root / ".claude" / "hooks").mkdir(parents=True)
        for name in scripts:
            shutil.copy(SCRIPTS / name, root / ".claude" / "scripts" / name)
        for name in hooks:
            shutil.copy(HOOKS / name, root / ".claude" / "hooks" / name)
        # gate_harness가 통과하려면 있어야 하는 최소 구성
        (root / ".claude" / "settings.json").write_text(
            '{"permissions":{"allow":["Read"]}}', encoding="utf-8")
        (root / ".claude" / "settings.local.json.sample").write_text("{}", encoding="utf-8")
        (root / ".claude" / "harness.json").write_text(
            json.dumps(harness or {}), encoding="utf-8")
        if git:
            subprocess.run(["git", "init", "-q"], cwd=root, capture_output=True, timeout=60)
            subprocess.run(["git", "config", "user.email", "t@t"], cwd=root,
                           capture_output=True, timeout=60)
            subprocess.run(["git", "config", "user.name", "t"], cwd=root,
                           capture_output=True, timeout=60)
        yield root
    finally:
        shutil.rmtree(root, ignore_errors=True)


def write_status(workspace: Path, phase: str = "7", sprint: str = "sprint-01",
                 track: str = "sprint", loop: str = "running") -> None:
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "STATUS.md").write_text(
        "# STATUS.md\n\n## 현재 상태\n\n```\n"
        f"PHASE:            {phase}\n"
        f"LOOP:             {loop}\n"
        "HALT_REASON:      -\n"
        f"TRACK:            {track}\n"
        f"CURRENT_SPRINT:   {sprint}\n"
        "```\n",
        encoding="utf-8",
    )


def status_field(workspace: Path, key: str) -> str:
    path = workspace / "STATUS.md"
    if not path.exists():
        return ""
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if line.startswith(f"{key}:"):
            return line.split(":", 1)[1].strip()
    return ""
