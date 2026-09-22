"""policy — 값 검증 · 저장 · interviewed 표식."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _harness import Result, run_py, temp_repo  # noqa: E402

SCRIPT_NAME = "policy.py"


def call(root: Path, *args: str) -> tuple[int, str]:
    script = root / ".claude" / "scripts" / SCRIPT_NAME
    rc, out, err = run_py(script, None, cwd=root, args=list(args))
    return rc, out + err


def field(out: str, key: str) -> str:
    for line in out.splitlines():
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip()
    return ""


def main() -> int:
    rep = Result("policy")

    with temp_repo(scripts=(SCRIPT_NAME,)) as root:
        # 파일이 없으면 권장 기본값 + interviewed=false
        rc, out = call(root, "show")
        rep.case("인터뷰 전 show", 0, rc, field(out, "interviewed") == "false", out)
        rep.case("기본값 제시", "notify", field(out, "plan_review"), True, out)

        # 인터뷰 저장
        rc, out = call(root, "init", "branch=current", "track_confirm=never",
                       "plan_review=pause", "auto_run=strict", "pitfall_capture=auto")
        rep.case("init 저장", 0, rc, "저장 완료" in out, out)

        rc, out = call(root, "show")
        rep.case("interviewed=true 전환", "true", field(out, "interviewed"), True, out)
        rep.case("저장값 유지 (branch)", "current", field(out, "branch"), True, out)
        rep.case("저장값 유지 (auto_run)", "strict", field(out, "auto_run"), True, out)

        # get은 값만 내보낸다 (에이전트가 그대로 쓴다)
        rc, out = call(root, "get", "plan_review")
        rep.case("get 단일값", "pause", out.strip(), rc == 0, out)

        # 잘못된 값/키/명령은 거부하되 죽지 않는다
        rc, out = call(root, "set", "plan_review=nope")
        rep.case("잘못된 값 거부", 1, rc, "가능" in out, out)
        rc, out = call(root, "set", "bogus_key=1")
        rep.case("알 수 없는 키 거부", 1, rc, "알 수 없는 키" in out, out)
        rc, out = call(root, "nosuchcmd")
        rep.case("알 수 없는 명령 거부", 1, rc, "알 수 없는 명령" in out, out)

        # 거부 후에도 기존 값이 보존돼야 한다
        rc, out = call(root, "get", "plan_review")
        rep.case("거부 후 값 보존", "pause", out.strip(), rc == 0, out)

        # set은 일부만 바꾼다
        rc, out = call(root, "set", "plan_review=notify")
        rep.case("set 부분 갱신", 0, rc, "notify" in out, out)
        rc, out = call(root, "show")
        rep.case("다른 키는 그대로", "current", field(out, "branch"), True, out)

        # 손상된 JSON은 기본값으로 안전 복구
        (root / ".claude" / "loop-policy.json").write_text("{broken", encoding="utf-8")
        rc, out = call(root, "show")
        rep.case("손상 파일 -> 기본값 복구", 0, rc,
                 field(out, "interviewed") == "false" and field(out, "branch") == "new", out)

    return rep.done()


if __name__ == "__main__":
    sys.exit(main())
