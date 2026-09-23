#!/usr/bin/env python3
"""Claude Code PostToolUse Hook — 빠른 게이트 (짧은 루프).

무엇을 하나
  소스 파일이 바뀐 직후 `.claude/harness.json`의 fast_check(린트/타입체크)를 돌린다.
  언어를 모른다 — 명령은 harness.json이, 소스 판정은 source_globs가 정한다.

왜 Bash도 매처인가
  Write/Edit는 file_path로 대상이 보이지만, Bash는 안 보인다. `python fix.py` 한 줄이
  소스 수십 개를 다시 쓸 수 있다. 명령 문자열로 거르면 그 경로를 통째로 놓친다.
  그래서 Bash 뒤에는 git status로 실제 변경을 본다.

비용 관리
  1. fast_check.cmd가 비어 있으면 git status도 보지 않고 즉시 통과한다.
  2. Write/Edit는 file_path가 소스가 아니면 즉시 통과한다.
  3. 바뀐 소스가 없으면 통과한다.
  fast_check는 편집마다 도는 명령이다. 수 초 안에 끝나는 것만 넣을 것 —
  느린 전체 빌드는 Stop 훅(build)의 몫이다.

종료 코드
  2 = 즉시 교정 요구. stderr가 모델에게 전달된다.
      PostToolUse는 이미 실행된 뒤이므로 "차단"이 아니라 "고쳐라"는 신호다.
  0 = 통과 / 검증기 부재 (cmd 없음·명령 없음·타임아웃은 실패가 아니다)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / ".claude" / "scripts"))

try:
    import harness_config  # noqa: E402  (경로 주입 후 import)
except Exception:  # pragma: no cover - 어댑터가 없으면 검사할 방법이 없다
    harness_config = None

MAX_OUTPUT_LINES = 30


def emit(stream, text: str) -> None:
    """UTF-8 바이트로 직접 쓴다.

    Windows에서 stdout/stderr의 기본 인코딩은 cp949 같은 로케일 코드페이지다.
    em dash(—)나 이모지를 그냥 write하면 UnicodeEncodeError로 훅이 죽고,
    그 exit 1은 non-blocking error로 처리되어 게이트가 통째로 무력화된다.
    """
    try:
        stream.buffer.write(text.encode("utf-8", errors="replace"))
        stream.buffer.flush()
    except Exception:
        try:
            stream.write(text.encode("ascii", "replace").decode("ascii"))
        except Exception:
            pass


def relative(file_path: str) -> str:
    path = Path(file_path)
    if path.is_absolute():
        try:
            return path.resolve().relative_to(REPO.resolve()).as_posix()
        except ValueError:
            return ""  # 레포 밖 파일 — 이 레포의 소스가 아니다
    return path.as_posix()


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    if not isinstance(data, dict):
        return 0
    tool_input = data.get("tool_input")
    if not isinstance(tool_input, dict) or harness_config is None:
        return 0

    config = harness_config.load()
    cmd, _ = harness_config.command(config, "fast_check")
    if not cmd:
        return 0  # 검증기 부재 — 조용히 통과

    # ── 빠른 경로 ── Write/Edit는 file_path로 판단할 수 있다
    file_path = tool_input.get("file_path") or ""
    if file_path:
        rel = relative(file_path)
        if not rel or not harness_config.is_source(config, rel):
            return 0

    changed = harness_config.changed_sources(config)
    if not changed:
        return 0

    code, out = harness_config.run("fast_check", changed, config)
    if code is None:
        emit(sys.stdout, f"[fast-gate] 검증기 부재 — {out}\n")
        return 0
    if code == 0:
        return 0

    lines = [ln for ln in out.strip().splitlines() if ln.strip()]
    shown = "\n".join(f"  {ln}" for ln in lines[:MAX_OUTPUT_LINES])
    more = f"\n  ... 외 {len(lines) - MAX_OUTPUT_LINES}줄" if len(lines) > MAX_OUTPUT_LINES else ""
    files = ", ".join(changed[:5]) + (f" 외 {len(changed) - 5}개" if len(changed) > 5 else "")
    emit(
        sys.stderr,
        f"\n[fast-gate] fast_check 실패 (exit {code}) — 바로 고칠 것\n\n"
        f"  대상: {files}\n\n{shown}{more}\n\n"
        "  방금 수정이 원인이면 지금 고친다. 여러 파일을 순서대로 바꾸는 중이라\n"
        "  일시적으로 깨진 상태라면 남은 수정을 마저 끝낸다.\n",
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
