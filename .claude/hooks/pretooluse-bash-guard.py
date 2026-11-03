#!/usr/bin/env python3
"""Claude Code PreToolUse Hook — 셸 위험 명령 차단 (Bash · PowerShell).

pretooluse-bash-guard.sh의 python 포팅. 규칙은 cd 체이닝 / 보호 브랜치 push /
force push / reset --hard / 브랜치 명명 5가지다. 보호 브랜치 목록은 RULES에서 고친다.

왜 포팅했나 (이 환경 실측, Windows + Git Bash)
  bash -c true              1797 ms   <- 셸 기동만으로 이만큼
  bash-guard.sh             8029 ms   <- 기동 + 내부 python3/grep 반복 포크
  python3 -c 인라인          754 ms
  이 훅은 모든 Bash 도구 호출마다 실행된다. 8초가 매번 붙는다.

입력: stdin JSON {"tool_name": "Bash"|"PowerShell", "tool_input": {"command": "..."}}
종료: 0 = 허용 / 2 = 차단

PowerShell 도구
  같은 훅이 PowerShell 도구도 받는다 (settings.json matcher `Bash|PowerShell`).
  git 규칙(보호 브랜치 push, force push, reset --hard)과 브랜치 명명은 그대로 적용하고,
  cd 체이닝 규칙은 적용하지 않는다 — PowerShell의 `;`는 문장 구분자라 오탐만 난다.
  (Bash 도구에서 cd 체이닝을 막는 이유: cwd가 바뀌면 상대 경로로 적힌 훅 경로 해석이
  깨져 모든 Bash가 막힐 수 있다 — 2026-09-28 실측)

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
    re.compile(r"_#[A-Za-z0-9-]+$"),     # {base}_#{이슈ID}  (#123, #PROJ-45)
    re.compile(r"_sprint-[0-9]+$"),      # {base}_sprint-{NN}
    re.compile(r"_hotfix_[a-z0-9-]+$"),  # {base}_hotfix_{설명}
    # 하네스/툴링 작업 — 위 셋은 전부 제품 코드 작업 전제(이슈·스프린트·핫픽스)라
    # .claude/ 자체를 고치는 작업에 붙일 이름이 없었다.
    re.compile(r"_harness_[a-z0-9-]+$"),  # {base}_harness_{설명}
    # 릴리스/차수 브랜치 — /branch 커맨드가 만드는 이름 (예: 2026_release-1, 2026_다빈도).
    # 이 패턴이 없으면 /branch 예시가 전부 차단된다. 팀 규칙이 다르면 여기를 고친다.
    re.compile(r"^20[0-9]{2}_\S+$"),     # {연도}_{차수·릴리스명}
)

# (정규식, 차단 사유) — 원본 .sh의 규칙 순서를 따른다 (master/Release 두 규칙은 보호 브랜치 하나로 합침)
# 정규식은 원본 .sh보다 넓다. 감사에서 확인된 우회 경로를 막기 위해서다:
#   git push origin HEAD:master      refspec 뒤의 master       (원본은 `\s+master` 만 봄)
#   git push origin +feature_x       + 접두 force              (원본은 -f/--force 만 봄)
#   bash -c 'cd /x && ls' / (cd /x; ls)   줄 시작이 아닌 cd 체이닝
#   cd /x 2>/dev/null; ls            경로 뒤 리다이렉트·인자 뒤의 체이닝
#   git -C /x reset --hard           git 과 reset 사이의 옵션
# 인용 구간을 벗기지 않는다 — 인용 안이라도 bash -c 로 실제 실행될 수 있다.
RULES = (
    (
        # 경로 뒤 리다이렉트·인자(`cd /x 2>/dev/null; ...`)로 빠져나가지 못하게 같은 줄의 나머지 토큰을 허용한다.
        re.compile(r"\bcd\s+[^\s&;|()]+(?:[ \t]+[^&;|()\n]*?)?\s*(?:&&|;)"),
        "디렉토리 체이닝(cd /path && ... / cd /path; ...)은 금지됩니다.\n"
        "  → 절대 경로로 직접 명령을 실행하세요.",
    ),
    (
        # 보호 브랜치 — 팀 규칙이 다르면 이 목록만 고친다
        re.compile(r"git push(?:\s+\S+)*?\s+(?:\S+:)?(?:main|master|[Rr]elease)(?:\s|$)", re.M),
        "보호 브랜치(main/master/release) 직접 push는 금지됩니다.\n"
        "  → 작업 브랜치를 push한 뒤 PR/MR을 통해 병합하세요.",
    ),
    (
        re.compile(r"git push.+?(?:-f\b|--force\b|--force-with-lease\b|\s\+\S)"),
        "Force push는 공유 브랜치의 히스토리를 손상시킵니다.\n"
        "  → 대안: 충돌을 해소하거나 새 커밋을 생성하세요.",
    ),
    (
        re.compile(r"\bgit\b[^\n|;&]*?\breset\s+--hard"),
        "git reset --hard는 로컬 변경 사항을 영구적으로 삭제합니다.\n"
        "  → 대안: 'git stash'로 임시 보관하거나 'git revert'를 사용하세요.",
    ),
)

CD_RULE_COUNT = 1  # RULES 앞쪽의 Bash 전용 규칙 수 (cd 체이닝)

# `git -C /path checkout -b X` 처럼 git 과 하위 명령 사이의 전역 옵션도 허용한다 (2026-09-28 우회 실측)
BRANCH_CMD = re.compile(r"\bgit(?:\s+-C\s+\S+|\s+-c\s+\S+)*\s+(?:checkout\s+-b|switch\s+-c)\s+(\S+)")


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


def strip_quoted(text: str) -> str:
    """따옴표로 감싼 구간을 공백으로 치환한다.

    **브랜치 명명 검사 전용이다.** 명령 안에 인용된 예시 문자열
    (테스트 코드나 문서를 작성할 때)을 실제 브랜치 생성으로 오인하지 않기 위해서다.

    다른 규칙(force push, master push, hard reset)에는 적용하지 않는다 —
    `bash -c "git push -f ..."` 처럼 인용 안의 내용이 실제로 실행될 수 있어서,
    인용을 벗기면 우회 경로가 생긴다. 브랜치명은 되돌리기 쉬운 반면 그쪽은 아니다.
    """
    out: list[str] = []
    quote = ""
    escaped = False
    for ch in text:
        if escaped:
            out.append(" " if quote else ch)
            escaped = False
        elif ch == "\\":
            escaped = True
            out.append(" " if quote else ch)
        elif quote:
            if ch == quote:
                quote = ""
            out.append(" ")
        elif ch in "'\"":
            quote = ch
            out.append(" ")
        else:
            out.append(ch)
    return "".join(out)


def check_branch_name(command: str) -> str | None:
    match = BRANCH_CMD.search(strip_quoted(command))
    if not match:
        return None
    branch = match.group(1)
    if not branch or any(p.search(branch) for p in BRANCH_ALLOWED):
        return None
    return (
        f"브랜치 명명 규칙 위반: '{branch}'\n"
        "  허용 패턴:\n"
        "    ✓ {base}_#{이슈ID}                예: main_#1234, develop_#PROJ-45\n"
        "    ✓ {base}_sprint-{NN}              예: main_sprint-01\n"
        "    ✓ {base}_hotfix_{영문소문자-설명}  예: main_hotfix_login-fix\n"
        "    ✓ {base}_harness_{영문소문자-설명} 예: main_harness_loop (하네스/툴링 작업)\n"
        "    ✓ {연도}_{차수·릴리스명}           예: 2026_release-1 (/branch)\n"
        "  허용되지 않는 패턴:\n"
        "    ✗ 위 패턴에 해당하지 않는 임의 브랜치명"
    )


def main() -> int:
    try:
        # stdin은 UTF-8이다. json.load(sys.stdin)은 로캘(cp949 등)로 디코드해서 한글 명령이 깨진다
        data = json.loads(sys.stdin.buffer.read().decode("utf-8-sig"))
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

    is_powershell = data.get("tool_name") == "PowerShell"
    rules = RULES[CD_RULE_COUNT:] if is_powershell else RULES
    for pattern, reason in rules:
        if pattern.search(command):
            return block(reason, command)

    branch_reason = check_branch_name(command)
    if branch_reason:
        return block(branch_reason, command)

    return 0


if __name__ == "__main__":
    sys.exit(main())
