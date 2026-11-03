"""PreToolUse 셸 가드 — 차단/통과 판정과 stderr 전달 (Bash · PowerShell)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _harness import HOOKS, REPO, Result, run_py  # noqa: E402

BASH_GUARD = HOOKS / "pretooluse-bash-guard.py"

# 케이스 문자열에 위험 명령이 들어가므로 셸 명령줄이 아니라 이 파일에 담는다.
# (그러지 않으면 테스트를 띄우는 명령 자체가 bash-guard에 걸린다)
BASH_CASES = [
    ("force push -f", "git push -f origin main_feature", 2),
    ("force push --force", "git push --force origin x", 2),
    ("force-with-lease", "git push --force-with-lease origin x", 2),
    ("master push", "git push origin master", 2),
    ("main push", "git push origin main", 2),
    ("Release push", "git push origin Release", 2),
    ("release push", "git push -u origin release", 2),
    ("hard reset", "git reset --hard HEAD~1", 2),
    ("cd 체이닝", "cd /e/proj && ls", 2),
    # 감사에서 확인된 우회 경로 — 전부 막혀야 한다
    ("우회: HEAD:master refspec", "git push origin HEAD:master", 2),
    ("우회: 브랜치:master refspec", "git push origin main_feature:master", 2),
    ("우회: HEAD:Release refspec", "git push origin HEAD:Release", 2),
    ("우회: HEAD:main refspec", "git push origin HEAD:main", 2),
    ("우회: + 접두 force", "git push origin +main_feature", 2),
    ("우회: bash -c 안 cd 체이닝", "bash -c 'cd /x && ls'", 2),
    ("우회: 서브셸 cd 체이닝", "(cd /x; ls)", 2),
    ("우회: git -C reset --hard", "git -C /x reset --hard", 2),
    ("우회: cd 뒤 리다이렉트 후 ;", "cd /x 2>/dev/null; grep a b", 2),
    ("우회: cd 뒤 리다이렉트 후 &&", "cd /x >/dev/null && ls", 2),
    ("브랜치 명명 위반", "git checkout -b main_wip", 2),
    ("switch -c 위반", "git switch -c feature", 2),
    ("harness 대문자 위반", "git checkout -b main_harness_Loop", 2),
    ("이슈 브랜치 통과", "git checkout -b main_#207500", 0),
    ("이슈키 브랜치 통과", "git checkout -b develop_#PROJ-45", 0),
    ("스프린트 브랜치 통과", "git checkout -b main_sprint-01", 0),
    ("hotfix 브랜치 통과", "git checkout -b main_hotfix_login-fix", 0),
    ("harness 브랜치 통과", "git checkout -b main_common_harness_loop", 0),
    ("릴리스 브랜치 통과(/branch)", "git checkout -b 2026_release-1 master", 0),
    ("연도 없는 임의명 위반", "git checkout -b release-1", 2),
    ("우회: git -C 뒤 checkout -b", "git -C /e/proj checkout -b hooktest_wip", 2),
    ("git -C 뒤 정상 브랜치 통과", "git -C /e/proj checkout -b main_#207500", 0),
    ("일반 명령 통과", "git status", 0),
    ("정상 push 통과", "git push -u origin main_sprint-01", 0),
    ("빈 명령 통과", "", 0),
    ("cd 단독 통과", "ls /e/proj", 0),
    ("cd 줄바꿈 분리 통과", "cd /e/proj\nls", 0),
    ("masterpiece 오탐 없음", "git push origin masterpiece", 0),
    ("main_ 접두 오탐 없음", "git push origin main_sprint-01", 0),
    ("refspec 정상 브랜치 통과", "git push origin HEAD:main_sprint-01", 0),
    # 인용된 브랜치명은 실제 생성이 아니다 (테스트·문서 작성 시 오탐 방지)
    ("인용된 브랜치명 통과(큰따옴표)", 'echo "git checkout -b some_name"', 0),
    ("인용된 브랜치명 통과(작은따옴표)", "echo 'git switch -c other_name'", 0),
    # 단, 인용을 벗긴다고 force push까지 풀어주지는 않는다
    ("인용 안 force push 차단", 'bash -c "git push -f origin main"', 2),
]

# PowerShell 도구 — git 규칙은 동일, cd 규칙은 제외 (`;`는 문장 구분자)
PS_CASES = [
    ("ps: force push", "git push -f origin x", 2),
    ("ps: master push", "git push origin master", 2),
    ("ps: reset --hard", "git reset --hard HEAD", 2),
    ("ps: 브랜치 명명 위반", "git checkout -b feature", 2),
    ("ps: ; 문장 구분 통과", "git status; git log --oneline -1", 0),
    ("ps: cd ; 체이닝 통과", "cd C:\\proj; Get-ChildItem", 0),
    ("ps: 정상 브랜치 통과", "git checkout -b main_#207500", 0),
]


def run_raw(payload: dict) -> tuple[int, str]:
    """ensure_ascii=False — stdin에 실제 UTF-8 한글 바이트를 넣는다.

    run_py는 json.dumps 기본값(ASCII escape)이라 디코딩 경로가 검증되지 않는다.
    훅이 로캘(cp949 등)로 stdin을 읽으면 여기서 깨지거나 죽는다.
    """
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    proc = subprocess.run([sys.executable, str(BASH_GUARD)], input=data,
                          capture_output=True, timeout=60, cwd=str(REPO))
    return proc.returncode, proc.stderr.decode("utf-8", errors="replace")


def main() -> int:
    rep = Result("PreToolUse 가드")

    for name, command, expect in BASH_CASES:
        payload = {"tool_name": "Bash", "tool_input": {"command": command}}
        rc, _, err = run_py(BASH_GUARD, payload)
        # 차단(2)인데 stderr가 비면 사유가 모델에게 전달되지 않는다
        stderr_ok = (rc != 2) or bool(err.strip())
        rep.case(f"bash: {name}", expect, rc, stderr_ok, err)

    for name, command, expect in PS_CASES:
        payload = {"tool_name": "PowerShell", "tool_input": {"command": command}}
        rc, _, err = run_py(BASH_GUARD, payload)
        stderr_ok = (rc != 2) or bool(err.strip())
        rep.case(name, expect, rc, stderr_ok, err)

    # stdin UTF-8 — 한글 브랜치명이 깨지지 않고 패턴 판정까지 간다
    rc, err = run_raw({"tool_name": "Bash", "tool_input": {"command": "git checkout -b 2026_다빈도 master"}})
    rep.case("bash: 한글 브랜치 UTF-8 stdin 통과", 0, rc, True, err)
    rc, err = run_raw({"tool_name": "Bash", "tool_input": {"command": "git checkout -b 다빈도"}})
    rep.case("bash: 한글 임의명 UTF-8 stdin 차단", 2, rc, "다빈도" in err, err)

    # 메시지가 Windows 로케일 콘솔(cp949 등)에서 죽지 않는지 (이모지/em dash 회귀 방지)
    rc, _, err = run_py(BASH_GUARD,
                        {"tool_name": "Bash", "tool_input": {"command": "git push -f origin x"}})
    rep.case("bash: 차단 메시지 인코딩", True, "Force push" in err and rc == 2)

    return rep.done()


if __name__ == "__main__":
    sys.exit(main())
