"""gate_harness — 심각도 분리와 CP949 문서 처리.

실제 YSR 레포에 이식할 때 드러난 결함의 회귀 방지다:
  CP949로 저장된 프로젝트 고유 문서(keyword.md, Schema.md)를 UTF-8 전용으로 읽어
  영구 FAIL → Stop 훅이 매 턴 종료를 막아 하네스가 잠겼다.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _harness import Result, run_py, temp_repo  # noqa: E402

SCRIPT_NAME = "gate_harness.py"


def run(root: Path) -> tuple[int, str]:
    rc, out, err = run_py(root / ".claude" / "scripts" / SCRIPT_NAME, None, cwd=root)
    return rc, out + err


def main() -> int:
    rep = Result("gate_harness")

    with temp_repo(scripts=(SCRIPT_NAME,)) as root:
        rc, out = run(root)
        rep.case("최소 구성 -> PASS", 0, rc, True, out)

        # CP949 문서는 정상 자산이다. 읽혀야 하고, 턴을 막으면 안 된다
        (root / ".claude" / "keyword.md").write_bytes("# 키워드\n환자 조회\n".encode("cp949"))
        rc, out = run(root)
        rep.case("CP949 문서 -> PASS (FAIL 아님)", 0, rc, "FAIL" not in out, out)

        # CP949 문서 안의 참조도 검사된다 (읽고 버리는 게 아니다)
        (root / ".claude" / "Schema.md").write_bytes(
            "참조: .claude/nope/없는파일.md\n".encode("cp949"))
        rc, out = run(root)
        rep.case("CP949 문서 속 깨진 링크 -> WARN으로 탐지", 0, rc,
                 "WARN" in out and "nope" in out, out)

        # 런타임 산출물은 없어도 정상
        (root / "docs").mkdir()
        (root / "docs" / "a.md").write_text("정책: .claude/loop-policy.json\n", encoding="utf-8")
        rc, out = run(root)
        rep.case("loop-policy.json 참조 -> 화이트리스트", True,
                 "loop-policy.json" not in out, out)

        # 문서 링크 깨짐은 WARN — exit 0 (Stop 훅이 턴을 막지 않는다)
        (root / "docs" / "b.md").write_text("참조: .claude/rules/gone.md\n", encoding="utf-8")
        rc, out = run(root)
        rep.case("문서 링크 깨짐 -> WARN, exit 0", 0, rc, "WARN" in out and "gone.md" in out, out)

        # 훅 command 경로 깨짐은 FAIL — 가드가 조용히 무력화되므로 반드시 막는다
        (root / ".claude" / "settings.json").write_text(
            '{"hooks":{"Stop":[{"hooks":[{"type":"command",'
            '"command":"python3 .claude/hooks/missing.py"}]}]}}', encoding="utf-8")
        rc, out = run(root)
        rep.case("훅 경로 깨짐 -> FAIL, exit 1", 1, rc, "missing.py" in out, out)

        # 설정 파일 문법 오류도 FAIL
        (root / ".claude" / "settings.json").write_text('{"permissions":,}', encoding="utf-8")
        rc, out = run(root)
        rep.case("settings.json 문법 오류 -> FAIL", 1, rc, "JSON 문법 오류" in out, out)

    return rep.done()


if __name__ == "__main__":
    sys.exit(main())
