"""하네스 테스트 전체 실행.

  python .claude/tests/run_all.py

훅이나 .claude/scripts/*.py 를 고쳤으면 이걸 돌린다.
Stop 훅이 매 턴 gate_harness를 호출하므로, 수십 초가 걸리는 이 테스트는
자동 실행에 넣지 않는다 — 턴마다 그 비용을 물게 된다.

종료 코드: 0 = 전부 통과 / 1 = 실패 있음
"""

from __future__ import annotations

import io
import subprocess
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, io.UnsupportedOperation):
        pass

HERE = Path(__file__).resolve().parent

MODULES = (
    "test_guards.py",
    "test_fast_gate.py",
    "test_loop_state.py",
    "test_stop_gate.py",
    "test_policy.py",
    "test_gate_harness.py",
)


def main() -> int:
    print("하네스 회귀 테스트\n")
    failed: list[str] = []
    started = time.perf_counter()

    for name in MODULES:
        path = HERE / name
        if not path.exists():
            print(f"=== {name} ===\n  SKIP (파일 없음)\n")
            continue
        proc = subprocess.run([sys.executable, str(path)], timeout=1800)
        if proc.returncode != 0:
            failed.append(name)

    elapsed = int(time.perf_counter() - started)
    print("─" * 52)
    if failed:
        print(f"결과: FAIL — {', '.join(failed)}  ({elapsed}초)")
        return 1
    print(f"결과: PASS — 전체 통과 ({elapsed}초)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
