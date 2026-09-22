#!/usr/bin/env python3
"""Claude Code PreToolUse Hook — CP949 파일(.pas/.dfm) 보호.

입력: stdin JSON {"tool_name": ..., "tool_input": {"file_path": ...}}
종료: 0 = 허용 / 2 = 차단

왜 인라인이 아니라 파일인가
  settings.json에 `python3 -c "..."` 로 두면 코드가 셸의 따옴표 파싱에 의존한다.
  이 코드에는 작은따옴표가 10개 넘게 들어가므로 실행 셸이 바뀌면 그대로 깨진다.
  파일로 두면 훅 명령이 `python3 <path>` 뿐이라 파싱할 것이 없다.

왜 bash가 아니라 python인가 (이 환경 실측, Windows + Git Bash)
  bash -c true          1797 ms   <- 셸 기동만으로 이만큼
  bash 스크립트 훅      5412 ms   <- 기동 + 내부 grep/sed 포크
  python3 -c 인라인      754 ms
  이 훅은 모든 Write/Edit 호출마다 실행되므로 기동 비용이 그대로 체감된다.

실패 정책
  입력을 해석하지 못하면 통과시킨다(exit 0). 훅 자체 결함으로 모든 편집이
  막히는 쪽이 더 나쁘다. 차단은 ".pas/.dfm임을 확인했을 때"만 한다.
"""

from __future__ import annotations

import json
import sys

CP949_SUFFIXES = (".pas", ".dfm")

# 메시지는 ASCII만 쓴다. Windows 콘솔 인코딩이 cp949라 이모지나 한글을 출력하면
# UnicodeEncodeError로 죽고, 그 exit 1을 Claude Code가 non-blocking error로
# 처리해서 차단이 통째로 무효화된다.
MESSAGE = """
[CP949] {tool} tool is blocked on .pas / .dfm files.

  file  : {path}

  reason: Write/Edit rewrite the whole file as UTF-8, destroying the existing
          CP949 Korean bytes. ASCII-only edits are affected too.

  do this instead:
    python3 with encoding='cp949' (read -> replace -> write)
    see .claude/rules/encoding-critical.md for the exact pattern
"""


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception as exc:  # 입력 불량 = 훅 문제. 편집을 막지 않는다.
        print(f"[CP949] hook could not parse input, allowing: {exc}", file=sys.stderr)
        return 0

    if not isinstance(data, dict):
        return 0

    tool_input = data.get("tool_input")
    if not isinstance(tool_input, dict):
        return 0

    path = tool_input.get("file_path") or ""
    if not isinstance(path, str) or not path:
        return 0

    # 대소문자 양쪽 방어 — .PAS/.DFM도 같은 CP949 파일이다.
    if not path.lower().endswith(CP949_SUFFIXES):
        return 0

    tool = data.get("tool_name") or "Write/Edit"
    # stderr로 보낸다. exit 2로 차단할 때 Claude Code는 stderr를 읽어 모델에게
    # 사유를 전달한다. stdout에 쓰면 "hook error: No stderr output"만 뜨고
    # 차단 이유가 전달되지 않는다.
    message = MESSAGE.format(tool=tool, path=path)
    try:
        sys.stderr.buffer.write(message.encode("utf-8", errors="replace"))
        sys.stderr.buffer.flush()
    except Exception:
        # 메시지 출력 실패가 차단 실패로 이어지면 안 된다. 차단이 본질이고 설명은 부수다.
        try:
            sys.stderr.write("[CP949] blocked: %s\n" % path)
        except Exception:
            pass
    return 2


if __name__ == "__main__":
    sys.exit(main())
