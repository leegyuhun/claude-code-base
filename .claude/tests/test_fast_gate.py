"""PostToolUse 빠른 게이트 — CP949 손상 탐지와 구조 경고."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _harness import Result, run_py, temp_repo  # noqa: E402

HOOK_NAME = "posttooluse-fast-gate.py"

PAS_BODY = """unit Treat;

interface

uses Classes, Controls, Forms;

type
  TfrmTreat = class(TForm)
    btnSave: TButton;
  private
    // 환자 정보를 저장한다
    procedure SavePatient;
  end;

implementation

procedure TfrmTreat.SavePatient;
begin
  // 여기에 저장 로직
end;

end.
"""

DFM_BODY = "object frmTreat: TfrmTreat\n  Caption = 'Treat'\nend\n"
DPR_BODY = "program Proj;\nuses\n  Treat in 'Forms\\Treat.pas' {frmTreat};\nbegin\nend.\n"

BASH = lambda c: {"tool_name": "Bash", "tool_input": {"command": c}}
TOUCH = BASH('python3 -c "..." Forms/Treat.pas')


def git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, capture_output=True, timeout=60)


def seed(root: Path) -> Path:
    (root / "Forms").mkdir(exist_ok=True)
    (root / "Forms" / "Treat.pas").write_bytes(PAS_BODY.encode("cp949"))
    (root / "Forms" / "Treat.dfm").write_bytes(DFM_BODY.encode("cp949"))
    (root / "Proj.dpr").write_bytes(DPR_BODY.encode("cp949"))
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "init")
    return root / "Forms" / "Treat.pas"


def reset(root: Path) -> None:
    git(root, "checkout", "--", ".")
    for extra in ("Forms/New.pas",):
        path = root / extra
        if path.exists():
            path.unlink()


def main() -> int:
    rep = Result("PostToolUse 빠른 게이트")

    with temp_repo(hooks=(HOOK_NAME,), git=True) as root:
        hook = root / ".claude" / "hooks" / HOOK_NAME
        pas = seed(root)

        rc, out, err = run_py(hook, TOUCH, cwd=root)
        rep.case("변경 없음 -> 통과", 0, rc, True, err)

        reset(root)
        pas.write_bytes(PAS_BODY.replace("저장 로직", "저장 로직 구현").encode("cp949"))
        rc, out, err = run_py(hook, TOUCH, cwd=root)
        rep.case("CP949 유지 수정 -> 통과", 0, rc, True, err)

        reset(root)
        pas.write_bytes(PAS_BODY.encode("utf-8"))
        rc, out, err = run_py(hook, TOUCH, cwd=root)
        rep.case("UTF-8 덮어쓰기 -> 교정요구", 2, rc, "UTF-8로 저장됐다" in err, err)

        reset(root)
        pas.write_bytes(b"\xef\xbb\xbf" + PAS_BODY.encode("utf-8"))
        rc, out, err = run_py(hook, TOUCH, cwd=root)
        rep.case("UTF-8 BOM -> 통과", 0, rc, True, err)

        reset(root)
        (root / "Forms" / "New.pas").write_bytes(b"unit New;\ninterface\nimplementation\nend.\n")
        rc, out, err = run_py(hook, TOUCH, cwd=root)
        rep.case("신규 pas 미등록 -> 경고", 0, rc, ".dpr/.dproj에 미등록" in out, out)

        reset(root)
        pas.write_bytes(PAS_BODY.replace(
            "    btnSave: TButton;",
            "    btnSave: TButton;\n    edtName: TEdit;").encode("cp949"))
        rc, out, err = run_py(hook, TOUCH, cwd=root)
        rep.case("컴포넌트 변경 dfm 미동기 -> 경고", 0, rc, "동기화 확인 필요" in out, out)

        reset(root)
        pas.write_bytes(PAS_BODY.replace(
            "  // 여기에 저장 로직",
            "  d := StrToDate('2026-01-01');").encode("cp949"))
        rc, out, err = run_py(hook, TOUCH, cwd=root)
        rep.case("날짜 하드코딩 -> 경고", 0, rc, "날짜 하드코딩" in out, out)

        # Bash는 명령 문자열과 무관하게 항상 검사한다 — `python fix.py`가 .pas를 망칠 수 있다
        reset(root)
        pas.write_bytes(PAS_BODY.encode("utf-8"))
        rc, out, err = run_py(hook, BASH("python fix_encoding.py"), cwd=root)
        rep.case("문자열 무관 Bash -> 손상 탐지", 2, rc, "UTF-8로 저장됐다" in err, err)

        # Write/Edit는 file_path로 판단한다 — .md 편집은 .pas를 바꿀 수 없으니 즉시 통과
        rc, out, err = run_py(
            hook, {"tool_name": "Write", "tool_input": {"file_path": "docs/note.md"}}, cwd=root)
        rep.case("Write .md -> 빠른 경로 통과(손상 있어도)", 0, rc, err.strip() == "", err)

        rc, out, err = run_py(
            hook, {"tool_name": "Write", "tool_input": {"file_path": "Forms/Treat.pas"}}, cwd=root)
        rep.case("Write 경로 트리거 -> 교정요구", 2, rc, "UTF-8로 저장됐다" in err, err)

    return rep.done()


if __name__ == "__main__":
    sys.exit(main())
