"""PreToolUse 가드 2종 — 차단/통과 판정과 stderr 전달."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _harness import HOOKS, Result, run_py  # noqa: E402

BASH_GUARD = HOOKS / "pretooluse-bash-guard.py"
CP949_GUARD = HOOKS / "pretooluse-cp949-guard.py"

# 케이스 문자열에 위험 명령이 들어가므로 셸 명령줄이 아니라 이 파일에 담는다.
# (그러지 않으면 테스트를 띄우는 명령 자체가 bash-guard에 걸린다)
BASH_CASES = [
    ("force push -f", "git push -f origin main_delphi", 2),
    ("force push --force", "git push --force origin x", 2),
    ("force-with-lease", "git push --force-with-lease origin x", 2),
    ("master push", "git push origin master", 2),
    ("Release push", "git push origin Release", 2),
    ("hard reset", "git reset --hard HEAD~1", 2),
    ("cd 체이닝", "cd /e/proj && ls", 2),
    # 감사에서 확인된 우회 경로 — 전부 막혀야 한다
    ("우회: HEAD:master refspec", "git push origin HEAD:master", 2),
    ("우회: 브랜치:master refspec", "git push origin main_delphi:master", 2),
    ("우회: HEAD:Release refspec", "git push origin HEAD:Release", 2),
    ("우회: + 접두 force", "git push origin +main_delphi", 2),
    ("우회: bash -c 안 cd 체이닝", "bash -c 'cd /x && ls'", 2),
    ("우회: 서브셸 cd 체이닝", "(cd /x; ls)", 2),
    ("우회: git -C reset --hard", "git -C /x reset --hard", 2),
    ("브랜치 명명 위반", "git checkout -b main_delphi_wip", 2),
    ("switch -c 위반", "git switch -c feature", 2),
    ("harness 대문자 위반", "git checkout -b main_delphi_harness_Loop", 2),
    ("이슈 브랜치 통과", "git checkout -b main_delphi_#207500", 0),
    ("스프린트 브랜치 통과", "git checkout -b main_delphi_sprint-01", 0),
    ("hotfix 브랜치 통과", "git checkout -b main_delphi_hotfix_login-fix", 0),
    ("harness 브랜치 통과", "git checkout -b main_delphi_harness_loop", 0),
    ("일반 명령 통과", "git status", 0),
    ("정상 push 통과", "git push -u origin main_delphi_sprint-01", 0),
    ("빈 명령 통과", "", 0),
    ("cd 단독 통과", "ls /e/proj", 0),
    ("cd 줄바꿈 분리 통과", "cd /e/proj\nls", 0),
    ("masterpiece 오탐 없음", "git push origin masterpiece", 0),
    ("refspec 정상 브랜치 통과", "git push origin HEAD:main_delphi_sprint-01", 0),
    # 인용된 브랜치명은 실제 생성이 아니다 (테스트·문서 작성 시 오탐 방지)
    ("인용된 브랜치명 통과(큰따옴표)", 'echo "git checkout -b some_name"', 0),
    ("인용된 브랜치명 통과(작은따옴표)", "echo 'git switch -c other_name'", 0),
    # 단, 인용을 벗긴다고 force push까지 풀어주지는 않는다
    ("인용 안 force push 차단", 'bash -c "git push -f origin main"', 2),
]

CP949_CASES = [
    ("pas Write 차단", {"tool_name": "Write", "tool_input": {"file_path": "C:/ysr/T.pas"}}, 2),
    ("dfm Edit 차단", {"tool_name": "Edit", "tool_input": {"file_path": "C:/ysr/T.dfm"}}, 2),
    ("PAS 대문자 차단", {"tool_name": "Write", "tool_input": {"file_path": "C:/ysr/A.PAS"}}, 2),
    ("윈도경로 차단", {"tool_name": "Edit", "tool_input": {"file_path": "E:\\ysr\\T.pas"}}, 2),
    ("MultiEdit 차단", {"tool_name": "MultiEdit", "tool_input": {"file_path": "a/b.pas"}}, 2),
    ("md 통과", {"tool_name": "Write", "tool_input": {"file_path": "docs/readme.md"}}, 0),
    ("py 통과", {"tool_name": "Edit", "tool_input": {"file_path": "a/gen.py"}}, 0),
    ("pastel 경로 통과", {"tool_name": "Write", "tool_input": {"file_path": "src/pastel/n.md"}}, 0),
    ("file_path 없음", {"tool_name": "Bash", "tool_input": {"command": "ls"}}, 0),
    ("tool_input null", {"tool_name": "Write", "tool_input": None}, 0),
]


def main() -> int:
    rep = Result("PreToolUse 가드")

    for name, command, expect in BASH_CASES:
        payload = {"tool_name": "Bash", "tool_input": {"command": command}}
        rc, _, err = run_py(BASH_GUARD, payload)
        # 차단(2)인데 stderr가 비면 사유가 모델에게 전달되지 않는다
        stderr_ok = (rc != 2) or bool(err.strip())
        rep.case(f"bash: {name}", expect, rc, stderr_ok, err)

    for name, payload, expect in CP949_CASES:
        rc, _, err = run_py(CP949_GUARD, payload)
        stderr_ok = (rc != 2) or bool(err.strip())
        rep.case(f"cp949: {name}", expect, rc, stderr_ok, err)

    # 메시지가 cp949 콘솔에서 죽지 않는지 (이모지/em dash 회귀 방지)
    rc, _, err = run_py(BASH_GUARD,
                        {"tool_name": "Bash", "tool_input": {"command": "git push -f origin x"}})
    rep.case("bash: 차단 메시지 인코딩", True, "Force push" in err and rc == 2)

    return rep.done()


if __name__ == "__main__":
    sys.exit(main())
