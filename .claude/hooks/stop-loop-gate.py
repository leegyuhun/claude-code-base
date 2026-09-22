#!/usr/bin/env python3
"""Claude Code Stop Hook — 긴 루프 게이트.

설계 근거: docs/Upgrade_loop.md STEP 2.

동작 순서
  1. stop_hook_active 가 true면 즉시 통과 (무한루프 방지 — 이 분기가 없으면 실패한 구현이다)
  2. 층 A: 하네스 무결성 (gate_harness.py). PHASE와 무관하게 항상 검사한다.
     하네스가 깨진 채로 루프를 돌리면 모든 판정이 의미를 잃는다.
  3. 상태 해석: ACTIVE_ISSUE -> STATUS.md. 없으면 루프 대상이 아니므로 통과.
  4. LOOP=halted 면 통과 (이미 사람 판단 대기 중)
  5. PHASE 게이팅 (아래 PHASE_GATES)
  6. 층 B: PHASE 6 = 빌드 / PHASE 7 = 검증 계약 잔여
  7. 실패면 카운터를 올리고, 상한/헛돌기면 탈출(exit 0), 아니면 exit 2

종료 코드
  2 = 종료를 막는다. stderr가 다음 턴의 지시가 된다.
  0 = 통과 / 루프 대상 아님 / 검증기 부재 / 탈출
  1 = 이 스크립트 자체의 버그 (Claude Code가 경고만 표시하고 흐름은 유지)

절대 지켜야 할 것
  - PHASE 8은 무조건 통과시킨다. 사람의 수동 UI 테스트 대기 상태이므로
    여기서 막으면 사용자가 빠져나갈 수 없다.
  - "검증기 부재"를 "검증 실패"로 보고하지 않는다. build.bat이 없거나 .dproj를
    못 찾은 것은 exit 0 + 경고다. exit 2로 처리하면 루프가 영원히 헛돈다.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

HOOK_DIR = Path(__file__).resolve().parent
REPO = HOOK_DIR.parents[1]
SCRIPTS = REPO / ".claude" / "scripts"
sys.path.insert(0, str(SCRIPTS))

try:
    import loop_state  # noqa: E402  (경로 주입 후 import)
except Exception:  # pragma: no cover - loop_state가 없으면 루프를 돌릴 수 없다
    loop_state = None

# PHASE별 게이트. 여기 없는 PHASE는 통과시킨다.
PHASE_GATES = {"6": "build", "7": "contract"}

# 검증기 부재를 나타내는 표식 (실패가 아니다)
MISSING = object()

BUILD_ERROR = re.compile(r"([\w./\\-]+\.pas)\((\d+)\)\s*(?:Error:)?\s*(\w\d+)?(.*)", re.I)
# goal-format.md의 수동 항목 표기: "(⚠️ 수동)" 또는 "(수동)"
MANUAL_TAG = re.compile(r"\(\s*(?:⚠️\s*)?수동\s*\)")
MISSING_MARKERS = ("rsvars.bat not found", "Project file not found", "not recognized")


def emit(text: str) -> None:
    """stderr에 UTF-8 바이트로 직접 쓴다.

    Windows 기본 인코딩(cp949)으로 내보내면 em dash나 이모지에서
    UnicodeEncodeError가 나고, 그 exit 1은 게이트를 통째로 무력화한다.
    """
    try:
        sys.stderr.buffer.write(text.encode("utf-8", errors="replace"))
        sys.stderr.buffer.flush()
    except Exception:
        try:
            sys.stderr.write(text.encode("ascii", "replace").decode("ascii"))
        except Exception:
            pass


def run(cmd: list[str], cwd: Path, timeout: int,
        env: dict[str, str] | None = None) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            cmd, cwd=cwd, capture_output=True, timeout=timeout, env=env
        )
    except subprocess.TimeoutExpired:
        return -1, "(timeout)"
    except OSError as exc:
        return -2, str(exc)
    out = (proc.stdout + proc.stderr).decode("utf-8", errors="replace")
    return proc.returncode, out


# ── 층 A ────────────────────────────────────────────────────────────


def gate_harness() -> tuple[bool, str]:
    """(ok, detail). 검증기가 없으면 ok=True로 통과시킨다."""
    script = SCRIPTS / "gate_harness.py"
    if not script.exists():
        return True, ""
    code, out = run([sys.executable, str(script), "--quiet"], REPO, 120)
    if code in (-1, -2):
        return True, ""  # 검증기 실행 불가 = 부재. 실패로 치지 않는다
    if code == 0:
        return True, ""
    fails = [ln.strip() for ln in out.splitlines() if ln.strip().startswith("FAIL")]
    return False, "\n".join(f"  {f}" for f in fails[:5]) or out.strip()[:400]


# ── 층 B ────────────────────────────────────────────────────────────


def changed_sources() -> list[str]:
    code, out = run(["git", "status", "--porcelain", "--untracked-files=all"], REPO, 30)
    if code != 0:
        return []
    files = []
    for line in out.splitlines():
        if len(line) < 4:
            continue
        path = line[3:].strip().strip('"')
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if path.lower().endswith((".pas", ".dfm")):
            files.append(path)
    return files


def find_dproj(rel_path: str) -> Path | None:
    directory = (REPO / rel_path).parent
    for _ in range(6):
        found = sorted(directory.glob("*.dproj"))
        if found:
            return found[0]
        if directory == REPO or directory.parent == directory:
            break
        directory = directory.parent
    return None


def gate_build(_status: dict):
    """PHASE 6: 컴파일. (None=통과 / MISSING=검증기 부재 / (요약, 시그니처)=실패)"""
    build_bat = REPO / "build.bat"
    if not build_bat.exists():
        return MISSING, "build.bat 없음"

    changed = changed_sources()
    if not changed:
        return None, ""  # 검사할 변경이 없다

    dproj = find_dproj(changed[0])
    if dproj is None:
        return MISSING, ".dproj를 찾지 못함"

    # DPROJ는 환경변수로 넘긴다. `set X && build.bat` 형태로 조립하면 셸 파싱에
    # 의존하게 되고, build.bat이 DPROJ를 무조건 덮어쓰면 오버라이드가 먹지 않는다.
    env = dict(os.environ)
    env["DPROJ"] = str(dproj)
    code, out = run(["cmd", "/c", str(build_bat), "debug"], REPO, 600, env=env)

    # 9009 = 명령을 찾을 수 없음. 배치 실행 자체가 불가능한 상태도 "부재"다.
    if code in (-1, -2, 9009) or any(m.lower() in out.lower() for m in MISSING_MARKERS):
        return MISSING, "빌드 환경 없음 (rsvars/msbuild 또는 프로젝트 파일)"
    if code == 0:
        return None, ""

    for line in out.splitlines():
        match = BUILD_ERROR.search(line)
        if match:
            unit, lineno, code_id = match.group(1), match.group(2), match.group(3) or "E?"
            return (line.strip()[:200], f"{code_id}:{Path(unit).name}:{lineno}")
    tail = [ln.strip() for ln in out.splitlines() if ln.strip()][-1:]
    return (tail[0][:200] if tail else f"build.bat exit {code}", f"build:exit{code}")


def goal_file(status: dict, issue: str) -> Path | None:
    workspace = REPO / "workspace" / issue
    if status.get("TRACK") == "defect":
        candidate = REPO / "docs" / f"PRD_{issue}.md"
    else:
        sprint = status.get("CURRENT_SPRINT", "")
        if not sprint or sprint == "-":
            return None
        candidate = workspace / "sprints" / sprint / "GOAL.md"
    return candidate if candidate.exists() else None


def gate_contract(status: dict, issue: str):
    """PHASE 7: 검증 계약에 미체크 항목이 남아있는가."""
    path = goal_file(status, issue)
    if path is None:
        return MISSING, "GOAL.md(또는 PRD)를 찾지 못함"
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return MISSING, "GOAL.md를 읽지 못함"

    section = re.search(r"^##\s*검증 계약.*?$(.*?)(?=^##\s|\Z)", text, re.M | re.S)
    if not section:
        return MISSING, "`## 검증 계약` 섹션 없음"

    # 수동 항목은 PHASE 8에서 사람이 확인한다. PHASE 7에서 [ ]인 것이 정상이므로
    # 여기서 세면 훅이 모델에게 "수동 항목을 [x]로 바꿔라"고 압박하는 꼴이 된다 —
    # 자기채점을 유도하는 게이트는 없는 것보다 나쁘다.
    pending = []
    skipped_manual = 0
    for ln in section.group(1).splitlines():
        if not re.match(r"^\s*-\s*\[ \]", ln):
            continue
        if MANUAL_TAG.search(ln):
            skipped_manual += 1
            continue
        pending.append(ln.strip())
    if not pending:
        return None, ""
    listed = "\n".join(f"    {p}" for p in pending[:5])
    more = f"\n    ... 외 {len(pending) - 5}건" if len(pending) > 5 else ""
    note = f"\n    (수동 항목 {skipped_manual}건은 PHASE 8 대상 — 제외)" if skipped_manual else ""
    return (f"검증 계약 미충족 {len(pending)}건\n{listed}{more}{note}", f"contract:{len(pending)}")


# ── 본체 ────────────────────────────────────────────────────────────


NEXT_STEPS = {
    "build": (
        "  1. 해당 유닛의 uses 절과 선언을 먼저 확인한다\n"
        "  2. .claude/refs/pitfalls.md 카테고리 B (Delphi 언어 함정)\n"
        "  3. 증상만 보고 고치지 말 것 — .claude/skills/systematic-debugging/SKILL.md Phase 1부터\n"
    ),
    "contract": (
        "  1. 각 항목을 실제로 검증하고 근거(파일:줄 또는 명령 출력)와 함께 [x]로 바꾼다\n"
        "  2. 검증되지 않은 항목을 체크하지 말 것 — 자기 채점 금지\n"
        "  3. 구현이 덜 됐으면 FEEDBACK.md를 만들고 PHASE=6으로 되돌린다\n"
    ),
    "harness": (
        "  1. 위 FAIL 항목을 고친다 (JSON 문법 / 스크립트 문법 / 깨진 경로)\n"
        "  2. python .claude/scripts/gate_harness.py 로 재확인한다\n"
    ),
}


def block(kind: str, phase: str, summary: str, attempts: str = "") -> int:
    emit(
        f"\n[loop-gate] PHASE {phase} 검증 실패{attempts}\n\n"
        f"실패: {kind}\n{summary}\n\n"
        f"다음에 볼 곳:\n{NEXT_STEPS.get(kind, '')}\n"
        "직전 시도와 같은 실패가 반복되면 접근을 바꿀 것. 같은 수정을 다시 하지 말 것.\n"
    )
    return 2


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    if not isinstance(data, dict):
        return 0

    # 1) 무한루프 방지 — 이 분기가 없으면 실패한 구현이다
    if data.get("stop_hook_active"):
        return 0

    # 2) 층 A — 하네스 무결성
    ok, detail = gate_harness()
    if not ok:
        return block("harness", "-", detail)

    if loop_state is None:
        return 0

    # 3) 상태 해석
    issue = loop_state.resolve_active_issue()
    if not issue:
        return 0
    workspace = loop_state.workspace_dir(issue)
    status = loop_state.read_status(workspace)
    if not status:
        return 0

    # 4) 이미 중단된 루프는 건드리지 않는다
    if status.get("LOOP") == "halted":
        return 0

    # 5) PHASE 게이팅 — 8은 절대 막지 않는다 (수동 테스트 대기)
    phase = status.get("PHASE", "").strip()
    kind = PHASE_GATES.get(phase)
    if kind is None:
        return 0

    # 6) 층 B
    if kind == "build":
        result, note = gate_build(status)
    else:
        result, note = gate_contract(status, issue)

    if result is MISSING:
        emit(
            f"\n[loop-gate] PHASE {phase} 검증기 부재 — 루프를 돌리지 않는다\n"
            f"  사유: {note}\n"
            "  이것은 검증 실패가 아니다. 환경을 갖추거나 사람이 직접 확인해야 한다.\n"
        )
        return 0

    state, _ = loop_state.load_state(workspace, status)
    scope = kind

    if result is None:
        # 통과 — 카운터를 되돌린다
        if state["scopes"].pop(scope, None) is not None:
            loop_state.save_state(workspace, state)
        return 0

    summary, signature = result, note
    code, out = run(
        [
            sys.executable, str(SCRIPTS / "loop_state.py"), "bump",
            "--scope", scope, "--signature", signature,
            "--note", summary.splitlines()[0][:120],
        ],
        REPO, 60,
    )
    action = ""
    for line in out.splitlines():
        if line.startswith("ACTION="):
            action = line.split("=", 1)[1].strip()

    if action == "halt":
        # loop_state 출력에 이미 사유·이력 경로·보존 지침이 들어있다. 덧붙이지 않는다.
        detail = "\n".join(
            ln for ln in out.strip().splitlines() if not ln.startswith("ACTION=")
        )
        emit(
            f"\n[loop-gate] PHASE {phase} 루프 중단\n\n"
            f"{detail}\n\n"
            "  같은 방법으로 재시도하면 같은 결과가 나온다. 사람의 판단이 필요하다.\n"
            "  재개: python .claude/scripts/loop_state.py clear-halt\n"
        )
        return 0

    attempts = ""
    match = re.search(r"attempts=(\d+/\d+)", out)
    if match:
        attempts = f" (시도 {match.group(1)})"
    return block(kind, phase, summary, attempts)


if __name__ == "__main__":
    sys.exit(main())
