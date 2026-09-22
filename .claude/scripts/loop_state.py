#!/usr/bin/env python3
"""루프 상태 — 이터레이션 카운터 · 벽시계 · 헛돌기 감지의 단일 소스.

설계 근거: docs/Upgrade_loop.md STEP 0-F, STEP 2-3, STEP 5-2, STEP 6.

왜 필요한가
  하네스에는 이미 재시도 루프가 4개 있다 (validator 7-2 빌드 재시도, 7-6 FEEDBACK
  왕복, 8-6 수정 재시도, sprint-dev 리뷰 왕복). 그런데 "최대 3회"는 모델이
  머릿속으로 세는 숫자여서 컴팩션 한 번이면 0으로 돌아가고, 나머지 셋은 상한이
  아예 없다. 카운터를 파일로 빼야 루프가 성립한다.

무엇을 세는가
  scope별로 독립 카운터를 둔다. 빌드 재시도와 리뷰 왕복이 서로의 횟수를
  잡아먹으면 안 된다. PHASE나 스프린트가 바뀌면 전부 리셋한다 — 다른 작업의
  실패를 이어 세지 않기 위해서다.

중단 판정 순서 (헛돌기가 상한보다 먼저다)
  1. 동일 실패 시그니처 2회 연속  -> 즉시 중단. 같은 자리에서 두 번 같은 방식으로
     실패한 모델이 세 번째에 성공할 확률은 무시할 만하다.
  2. 이터레이션 상한 초과         -> 중단
  3. 벽시계 상한 초과             -> 중단

사용법 (에이전트가 Bash로 호출한다)
  python .claude/scripts/loop_state.py status
  python .claude/scripts/loop_state.py bump --scope build --signature "E2003:Treat.pas:412" --note "uses 절 추가 시도"
  python .claude/scripts/loop_state.py reset --scope build
  python .claude/scripts/loop_state.py halt --reason "빌드 상한 도달"
  python .claude/scripts/loop_state.py clear-halt

  마지막 줄에 ACTION=continue 또는 ACTION=halt 를 출력한다. 에이전트는 이 값만
  보면 된다. 종료 코드는 항상 0이다 — 이 스크립트는 판정자이지 게이트가 아니다.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

# scope별 이터레이션 상한. 기존 하네스의 "최대 3회"와 맞춘다.
SCOPE_LIMITS = {
    "build": 3,      # validator 7-2
    "feedback": 3,   # validator 7-6 <-> implementer 왕복
    "manual": 3,     # validator 8-6 수정 재시도
    "review": 3,     # sprint-dev 4단계 Spec/Quality 리뷰 왕복
}
DEFAULT_LIMIT = 3

WALL_CLOCK_LIMIT_SEC = 30 * 60   # 빌드 1회 1분 미만 기준, 수정 시간 포함 여유값
REPEAT_LIMIT = 2                 # 동일 시그니처 연속 허용 횟수


def now() -> datetime:
    return datetime.now(timezone.utc).astimezone()


def emit(text: str) -> None:
    """UTF-8 바이트로 직접 쓴다 (Windows 콘솔 cp949에서 em dash 등이 죽는 것 방지)."""
    try:
        sys.stdout.buffer.write(text.encode("utf-8", errors="replace"))
        sys.stdout.buffer.flush()
    except Exception:
        try:
            sys.stdout.write(text.encode("ascii", "replace").decode("ascii"))
        except Exception:
            pass


def git(*args: str) -> str:
    try:
        proc = subprocess.run(["git", *args], cwd=REPO, capture_output=True, timeout=20)
    except (subprocess.TimeoutExpired, OSError):
        return ""
    if proc.returncode != 0:
        return ""
    return proc.stdout.decode("utf-8", errors="replace").strip()


def resolve_active_issue() -> str | None:
    """.claude/rules/active-issue.md의 해석 순서를 그대로 따른다."""
    pointer = REPO / ".claude" / "ACTIVE_ISSUE"
    if pointer.exists():
        try:
            value = pointer.read_text(encoding="utf-8-sig").strip()
        except OSError:
            value = ""
        if value:
            return value
    match = re.search(r"#(\d+)", git("branch", "--show-current"))
    return f"#{match.group(1)}" if match else None


def workspace_dir(issue: str) -> Path:
    return REPO / "workspace" / issue


STATUS_KEYS = ("PHASE", "TRACK", "CURRENT_SPRINT", "PIPELINE", "LOOP", "HALT_REASON")


def read_status(ws: Path) -> dict[str, str]:
    path = ws / "STATUS.md"
    if not path.exists():
        return {}
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return {}
    found = {}
    for key in STATUS_KEYS:
        match = re.search(rf"^{key}:\s*(.*)$", text, re.M)
        if match:
            found[key] = match.group(1).strip()
    return found


def write_status_fields(ws: Path, fields: dict[str, str]) -> bool:
    """STATUS.md의 필드를 갱신한다. 없는 필드는 PHASE 줄 뒤에 추가한다."""
    path = ws / "STATUS.md"
    if not path.exists():
        return False
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return False

    for key, value in fields.items():
        pattern = re.compile(rf"^({key}:\s*).*$", re.M)
        if pattern.search(text):
            text = pattern.sub(lambda m: f"{m.group(1)}{value}", text, count=1)
        else:
            phase = re.search(r"^PHASE:.*$", text, re.M)
            if phase:
                insert = f"\n{key}:{' ' * max(1, 18 - len(key) - 1)}{value}"
                text = text[: phase.end()] + insert + text[phase.end():]
            else:
                text += f"\n{key}: {value}\n"
    try:
        path.write_text(text, encoding="utf-8")
    except OSError:
        return False
    return True


def loop_dir(ws: Path) -> Path:
    return ws / ".loop"


def counter_path(ws: Path) -> Path:
    return loop_dir(ws) / "counter.json"


def attempts_path(ws: Path) -> Path:
    return loop_dir(ws) / "attempts.log"


def new_state(status: dict[str, str]) -> dict:
    return {
        "phase": status.get("PHASE", ""),
        "sprint": status.get("CURRENT_SPRINT", ""),
        "scopes": {},
        "halted": False,
        "halt_reason": "",
    }


# PHASE가 바뀌면 지워도 되는 scope — 그 PHASE 안에서만 의미가 있는 것들.
# feedback / manual / review:* 는 PHASE를 넘나드는 왕복을 세는 카운터라 여기 없다.
# (7→6→7 왕복마다 전부 리셋하면 그 왕복은 영원히 계수되지 않는다 — 감사 결함 ①)
PHASE_BOUND_SCOPES = {"build", "contract"}


def load_state(ws: Path, status: dict[str, str]) -> tuple[dict, str]:
    """(state, reset_kind). reset_kind: "" / "sprint" / "phase".

    스프린트가 바뀌면 전부 리셋한다 — 다른 작업의 실패를 이어 세지 않는다.
    PHASE만 바뀌면 PHASE_BOUND_SCOPES 만 리셋한다 — 왕복 카운터는 살려둔다.
    """
    path = counter_path(ws)
    if not path.exists():
        return new_state(status), ""
    try:
        state = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return new_state(status), ""
    if not isinstance(state, dict):
        return new_state(status), ""

    state.setdefault("scopes", {})
    state.setdefault("halted", False)
    state.setdefault("halt_reason", "")

    phase = status.get("PHASE", "")
    sprint = status.get("CURRENT_SPRINT", "")
    if sprint and state.get("sprint") != sprint:
        return new_state(status), "sprint"
    if phase and state.get("phase") != phase:
        for scope in list(state["scopes"]):
            if scope.split(":", 1)[0] in PHASE_BOUND_SCOPES:
                del state["scopes"][scope]
        state["phase"] = phase
        return state, "phase"
    return state, ""


def save_state(ws: Path, state: dict) -> None:
    loop_dir(ws).mkdir(parents=True, exist_ok=True)
    counter_path(ws).write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def append_attempt(ws: Path, line: str) -> None:
    """한 줄로 압축해 누적한다.

    전체 로그를 쌓으면 모델이 같은 오답에 고착된다 (STEP 5-2).
    FEEDBACK.md는 최신 지시만 담고, 이력은 여기에만 남긴다.
    """
    loop_dir(ws).mkdir(parents=True, exist_ok=True)
    with attempts_path(ws).open("a", encoding="utf-8") as handle:
        handle.write(line.rstrip() + "\n")


def limit_for(scope: str, phase: str = "") -> int:
    base = scope.split(":", 1)[0]
    return SCOPE_LIMITS.get(base, DEFAULT_LIMIT)


def elapsed_seconds(scope_state: dict) -> int:
    first = scope_state.get("first_at")
    if not first:
        return 0
    try:
        started = datetime.fromisoformat(first)
    except ValueError:
        return 0
    return int((now() - started).total_seconds())


def fmt_minutes(seconds: int) -> str:
    return f"{seconds // 60}m"


def context() -> tuple[str | None, Path | None, dict[str, str]]:
    issue = resolve_active_issue()
    if not issue:
        return None, None, {}
    ws = workspace_dir(issue)
    return issue, ws, read_status(ws)


def cmd_status(_args: argparse.Namespace) -> int:
    issue, ws, status = context()
    if not issue:
        emit("[loop] ACTIVE_ISSUE를 확인할 수 없다 (.claude/ACTIVE_ISSUE 없음, 브랜치에도 없음)\n")
        emit("ACTION=continue\n")
        return 0
    state, _ = load_state(ws, status)
    emit(f"[loop] issue={issue} phase={status.get('PHASE', '?')} sprint={status.get('CURRENT_SPRINT', '-')}\n")
    if state.get("halted"):
        emit(f"  HALTED: {state.get('halt_reason', '')}\n")
    if not state["scopes"]:
        emit("  카운터 없음 (아직 실패 기록 없음)\n")
    for scope, sc in sorted(state["scopes"].items()):
        emit(
            f"  {scope:<12} attempts={sc.get('attempts', 0)}/{limit_for(scope, state.get('phase', ''))}"
            f" repeat={sc.get('repeat', 0)} elapsed={fmt_minutes(elapsed_seconds(sc))}\n"
        )
    log = attempts_path(ws)
    if log.exists():
        lines = log.read_text(encoding="utf-8-sig").splitlines()[-5:]
        if lines:
            emit("  최근 시도:\n")
            for line in lines:
                emit(f"    {line}\n")
    emit("ACTION=halt\n" if state.get("halted") else "ACTION=continue\n")
    return 0


def cmd_bump(args: argparse.Namespace) -> int:
    issue, ws, status = context()
    if not issue:
        emit("[loop] ACTIVE_ISSUE 없음 - 카운터를 기록하지 않는다\n")
        emit("ACTION=continue\n")
        return 0

    state, reset_kind = load_state(ws, status)
    if reset_kind == "sprint":
        emit("[loop] 스프린트 변경 감지 - 카운터 전체 리셋\n")
    elif reset_kind == "phase":
        emit("[loop] PHASE 변경 감지 - build/contract 카운터 리셋 (왕복 카운터는 유지)\n")

    scope = args.scope
    sc = state["scopes"].setdefault(
        scope, {"attempts": 0, "first_at": now().isoformat(), "last_signature": "", "repeat": 0}
    )
    sc["attempts"] = int(sc.get("attempts", 0)) + 1

    repeated = False
    if args.signature:
        digest = hashlib.sha1(args.signature.encode("utf-8")).hexdigest()[:12]
        if sc.get("last_signature") == digest:
            sc["repeat"] = int(sc.get("repeat", 0)) + 1
            repeated = True
        else:
            sc["last_signature"] = digest
            sc["repeat"] = 1

    phase = state.get("phase") or status.get("PHASE", "")
    limit = limit_for(scope, phase)
    attempts = sc["attempts"]
    elapsed = elapsed_seconds(sc)

    stamp = now().strftime("%Y-%m-%d %H:%M")
    sprint = status.get("CURRENT_SPRINT", "-")
    note = args.note or args.signature or ""
    append_attempt(
        ws,
        f"[{sprint}][P{status.get('PHASE', '?')}][{scope}][iter {attempts}][{stamp}] {note}",
    )

    reason = ""
    if repeated and sc.get("repeat", 0) >= REPEAT_LIMIT:
        reason = f"동일 실패 {sc['repeat']}회 연속 (헛돌기) - 접근을 바꾸지 않으면 반복된다"
    elif attempts >= limit:
        reason = f"이터레이션 상한 도달 ({attempts}/{limit})"
    elif elapsed >= WALL_CLOCK_LIMIT_SEC:
        reason = f"벽시계 상한 도달 ({fmt_minutes(elapsed)})"

    emit(
        f"[loop] scope={scope} attempts={attempts}/{limit}"
        f" elapsed={fmt_minutes(elapsed)}"
        f" signature={'repeat' if repeated else 'new'}\n"
    )

    if not reason:
        save_state(ws, state)
        emit("ACTION=continue\n")
        return 0

    state["halted"] = True
    state["halt_reason"] = reason
    save_state(ws, state)
    write_status_fields(ws, {"LOOP": "halted", "HALT_REASON": reason})
    append_attempt(ws, f"[{sprint}][{scope}][HALT][{stamp}] {reason}")

    emit(f"  HALT: {reason}\n")
    emit("  부분 산출물은 그대로 둔다. 커밋하지 말 것.\n")
    emit(f"  이력: workspace/{issue}/.loop/attempts.log\n")
    emit("ACTION=halt\n")
    return 0


def cmd_reset(args: argparse.Namespace) -> int:
    issue, ws, status = context()
    if not issue:
        emit("[loop] ACTIVE_ISSUE 없음\nACTION=continue\n")
        return 0
    state, _ = load_state(ws, status)
    if args.scope:
        state["scopes"].pop(args.scope, None)
        emit(f"[loop] scope={args.scope} 카운터 리셋\n")
    else:
        state["scopes"] = {}
        emit("[loop] 전체 카운터 리셋\n")
    state["halted"] = False
    state["halt_reason"] = ""
    state["phase"] = status.get("PHASE", state.get("phase", ""))
    state["sprint"] = status.get("CURRENT_SPRINT", state.get("sprint", ""))
    save_state(ws, state)
    write_status_fields(ws, {"LOOP": "running", "HALT_REASON": "-"})
    emit("ACTION=continue\n")
    return 0


def cmd_halt(args: argparse.Namespace) -> int:
    issue, ws, status = context()
    if not issue:
        emit("[loop] ACTIVE_ISSUE 없음\nACTION=halt\n")
        return 0
    state, _ = load_state(ws, status)
    state["halted"] = True
    state["halt_reason"] = args.reason
    save_state(ws, state)
    write_status_fields(ws, {"LOOP": "halted", "HALT_REASON": args.reason})
    append_attempt(ws, f"[{status.get('CURRENT_SPRINT', '-')}][HALT][{now():%Y-%m-%d %H:%M}] {args.reason}")
    emit(f"[loop] HALT 기록: {args.reason}\n")
    emit("ACTION=halt\n")
    return 0


def cmd_clear_halt(_args: argparse.Namespace) -> int:
    return cmd_reset(argparse.Namespace(scope=None))


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="루프 카운터/상한 관리")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("status").set_defaults(func=cmd_status)

    p_bump = sub.add_parser("bump")
    p_bump.add_argument("--scope", required=True, help="build | feedback | manual | review[:항목]")
    p_bump.add_argument("--signature", default="", help="실패 식별자 (에러코드:파일:줄)")
    p_bump.add_argument("--note", default="", help="attempts.log에 남길 한 줄 요약")
    p_bump.set_defaults(func=cmd_bump)

    p_reset = sub.add_parser("reset")
    p_reset.add_argument("--scope", default=None)
    p_reset.set_defaults(func=cmd_reset)

    p_halt = sub.add_parser("halt")
    p_halt.add_argument("--reason", required=True)
    p_halt.set_defaults(func=cmd_halt)

    sub.add_parser("clear-halt").set_defaults(func=cmd_clear_halt)

    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
