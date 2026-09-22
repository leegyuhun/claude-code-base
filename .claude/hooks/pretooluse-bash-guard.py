#!/usr/bin/env python3
"""Claude Code PreToolUse Hook — Bash 위험 명령 차단.

pretooluse-bash-guard.sh의 python 포팅. 6규칙과 메시지는 원문 그대로 유지한다.
바뀐 것은 실행 언어뿐이다.

왜 포팅했나 (이 환경 실측, Windows + Git Bash)
  bash -c true              1797 ms   <- 셸 기동만으로 이만큼
  bash-guard.sh             8029 ms   <- 기동 + 내부 python3/grep 반복 포크
  python3 -c 인라인          754 ms
  이 훅은 모든 Bash 도구 호출마다 실행된다. 8초가 매번 붙는다.

입력: stdin JSON {"tool_input": {"command": "..."}}
종료: 0 = 허용 / 2 = 차단

실패 정책
  입력을 해석하지 못하면 통과시킨다(exit 0) — 원본 .sh와 동일하다.
  훅 결함으로 모든 명령이 막히는 쪽이 더 나쁘다.
"""

from __future__ import annotations

import json
import re
import sys

# 브랜치 명명 규칙 — 하나라도 매칭되면 허용
BRANCH_ALLOWED = (
    re.compile(r"_#[0-9]+$"),            # {base}_#{이슈번호}
    re.compile(r"_sprint-[0-9]+$"),      # {base}_sprint-{NN}
    re.compile(r"_hotfix_[a-z0-9-]+$"),  # {base}_hotfix_{설명}
    # 하네스/툴링 작업 — 위 셋은 전부 제품 코드 작업 전제(Redmine 이슈·스프린트·핫픽스)라
    # .claude/ 자체를 고치는 작업에 붙일 이름이 없었다.
    re.compile(r"_harness_[a-z0-9-]+$"),  # {base}_harness_{설명}
)

# (정규식, 차단 사유) — 원본 .sh의 규칙 1~5와 동일한 순서·패턴
RULES = (
    (
        re.compile(r"^\s*cd\s+[^\s&;]+\s*&&", re.M),
        "디렉토리 체이닝(cd /path && ...)은 금지됩니다.\n"
        "  → 절대 경로로 직접 명령을 실행하세요.",
    ),
    (
        re.compile(r"git push(\s+[^\s]+)?\s+master(\s|$)", re.M),
        "master 브랜치 직접 push는 금지됩니다.\n"
        "  → 브랜치 전략: Release → master PR을 통해 병합하세요.",
    ),
    (
        re.compile(r"git push(\s+[^\s]+)?\s+Release(\s|$)", re.M),
        "Release 브랜치 직접 push는 금지됩니다.\n"
        "  → 브랜치 전략: 정기 배포 브랜치(2026_정기_N차) → Release PR을 통해 병합하세요.",
    ),
    (
        re.compile(r"git push.+(-f\b|--force\b|--force-with-lease\b)"),
        "Force push는 공유 브랜치의 히스토리를 손상시킵니다.\n"
        "  → 대안: 충돌을 해소하거나 새 커밋을 생성하세요.",
    ),
    (
        re.compile(r"git reset\s+--hard"),
        "git reset --hard는 로컬 변경 사항을 영구적으로 삭제합니다.\n"
        "  → 대안: 'git stash'로 임시 보관하거나 'git revert'를 사용하세요.",
    ),
)

BRANCH_CMD = re.compile(r"git (?:checkout -b|switch -c)\s+(\S+)")


def emit(text: str) -> None:
    """차단 사유를 stderr에 UTF-8 바이트로 직접 쓴다.

    stderr인 이유: PreToolUse가 exit 2로 차단할 때 Claude Code는 stderr를 읽어
    모델에게 사유를 전달한다. 원본 .sh는 echo로 stdout에 썼기 때문에
    "hook error: No stderr output"만 뜨고 차단 이유가 전달되지 않았다.

    바이트로 직접 쓰는 이유: Windows에서 sys.stderr의 기본 인코딩은 cp949다.
    그대로 한글을 내보내면 UTF-8을 기대하는 쪽에서 깨지고, 이모지는
    UnicodeEncodeError로 훅을 죽인다 — 그 exit 1은 non-blocking error로
    처리되어 차단이 통째로 무효화된다.
    """
    data = text.encode("utf-8", errors="replace")
    try:
        sys.stderr.buffer.write(data)
        sys.stderr.buffer.flush()
    except Exception:
        try:
            sys.stderr.write(text)
        except Exception:
            pass


def block(reason: str, command: str) -> int:
    emit(
        "\n"
        f"🚫 [bash-guard] {reason}\n"
        "\n"
        f"  차단된 명령어: {command}\n"
        "\n"
    )
    return 2


def check_branch_name(command: str) -> str | None:
    match = BRANCH_CMD.search(command)
    if not match:
        return None
    branch = match.group(1)
    if not branch or any(p.search(branch) for p in BRANCH_ALLOWED):
        return None
    return (
        f"브랜치 명명 규칙 위반: '{branch}'\n"
        "  허용 패턴:\n"
        "    ✓ {base}_#{이슈번호}              예: main_delphi_#1234, 2026_정기5차_#207500\n"
        "    ✓ {base}_sprint-{NN}              예: main_delphi_sprint-01\n"
        "    ✓ {base}_hotfix_{영문소문자-설명}  예: main_delphi_hotfix_login-fix\n"
        "    ✓ {base}_harness_{영문소문자-설명} 예: main_delphi_harness_loop (하네스/툴링 작업)\n"
        "  허용되지 않는 패턴:\n"
        "    ✗ 위 3가지에 해당하지 않는 임의 브랜치명"
    )


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0  # 입력 불량 = 훅 문제. 명령을 막지 않는다.

    if not isinstance(data, dict):
        return 0
    tool_input = data.get("tool_input")
    if not isinstance(tool_input, dict):
        return 0
    command = tool_input.get("command") or ""
    if not isinstance(command, str) or not command:
        return 0

    for pattern, reason in RULES:
        if pattern.search(command):
            return block(reason, command)

    branch_reason = check_branch_name(command)
    if branch_reason:
        return block(branch_reason, command)

    return 0


if __name__ == "__main__":
    sys.exit(main())
