"""
층 A — 하네스 무결성 검증기.

이 레포에는 Delphi 빌드 대상이 없다 (`_D7/` 없음, `Tests/Source/` 비어 있음).
따라서 루프의 종료 조건으로 쓸 수 있는 유일한 검증기는 하네스 자체의 무결성이다.
설계 근거: docs/Upgrade_loop.md STEP 1-1 "층 A".

검사 항목
  1. JSON 파싱        — settings.json / settings.local.json.sample / .mcp.json.example
  2. 훅·스크립트 문법 — .claude/{hooks,scripts}/*.py (ast) · *.sh (bash -n)
  3. 내부 참조 무결성 — 문서가 가리키는 .claude/** 경로가 실재하는가

종료 코드
  0 = 전부 통과 (검증 불가 항목은 SKIP, 실패로 치지 않는다)
  1 = 검사 실패 — 하네스가 깨졌다

  ※ exit 2는 쓰지 않는다. Stop 훅이 이 스크립트의 1을 2로 번역한다.
    "검증기 부재"와 "검증 실패"를 섞지 않기 위함 — Upgrade_loop.md STEP 2-4 참조.

사용법
  python .claude/scripts/gate_harness.py
  python .claude/scripts/gate_harness.py --quiet    # 실패 항목만 출력
"""

from __future__ import annotations

import ast
import io
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

# 콘솔 인코딩이 utf-8이 아니면 강제 — 화살표·박스문자가 깨지지 않게.
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, io.UnsupportedOperation):
        pass

REPO = Path(__file__).resolve().parents[2]

# ── 검사 1 대상 ────────────────────────────────────────────────────
# (경로, 없어도 정상인가)
JSON_TARGETS = [
    (".claude/settings.json", False),
    (".claude/settings.local.json.sample", False),
    (".claude/settings.local.json", True),   # gitignore 대상
    (".mcp.json.example", False),
    (".mcp.json", True),                     # gitignore 대상
]

# ── 검사 3 설정 ────────────────────────────────────────────────────
# 런타임 생성물이거나 gitignore 대상 — 참조는 있으나 파일이 없어도 정상
REF_WHITELIST = {
    ".claude/ACTIVE_ISSUE",
    ".claude/settings.local.json",
    ".claude/projects",
}

# 아직 만들지 않은 파일을 의도적으로 나열하는 문서 — 참조 검사에서 제외.
# (Upgrade_loop.md는 시공 완료 후 실재 파일만 참조하므로 2026-09-22에 제외를 해제했다)
SCAN_EXCLUDE: set[str] = set()

REF_PATTERN = re.compile(r"\.claude/[A-Za-z0-9_][A-Za-z0-9_./\-]*")
# 플레이스홀더·글롭이 섞인 경로는 실재 검사 대상이 아니다
REF_SKIP_CHARS = set("{}*?<>")


class Report:
    def __init__(self, quiet: bool = False) -> None:
        self.quiet = quiet
        self.n_ok = 0
        self.n_skip = 0
        self.fails: list[str] = []

    def ok(self, msg: str) -> None:
        self.n_ok += 1
        if not self.quiet:
            print(f"  OK    {msg}")

    def skip(self, msg: str) -> None:
        self.n_skip += 1
        if not self.quiet:
            print(f"  SKIP  {msg}")

    def fail(self, msg: str) -> None:
        self.fails.append(msg)
        print(f"  FAIL  {msg}")

    def section(self, title: str) -> None:
        if not self.quiet:
            print(f"\n{title}")


def check_json(rep: Report) -> None:
    rep.section("[1/3] JSON 파싱")
    for rel, optional in JSON_TARGETS:
        path = REPO / rel
        if not path.exists():
            if optional:
                rep.skip(f"{rel} (없음 — gitignore 대상)")
            else:
                rep.fail(f"{rel} — 필수 파일이 없다")
            continue
        try:
            # utf-8-sig: setup_claude.bat의 Set-Content -Encoding UTF8이 BOM을 붙인다.
            # BOM이 남으면 json.loads가 실패하므로 읽을 때 제거한다.
            json.loads(path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as exc:
            rep.fail(f"{rel} — JSON 문법 오류 (line {exc.lineno}, col {exc.colno}): {exc.msg}")
        except UnicodeDecodeError as exc:
            rep.fail(f"{rel} — UTF-8 디코딩 실패: {exc}")
        else:
            rep.ok(rel)


def check_scripts(rep: Report) -> None:
    """훅·스크립트 문법 검사.

    훅이 문법 오류로 죽으면 exit 1이 되고, Claude Code는 그것을 non-blocking
    error로 처리한다 — 즉 가드가 조용히 무력화된다. 여기서 반드시 잡아야 한다.
    """
    rep.section("[2/3] 훅·스크립트 문법")

    py_files: list[Path] = []
    sh_files: list[Path] = []
    for rel_dir in (".claude/hooks", ".claude/scripts"):
        directory = REPO / rel_dir
        if not directory.is_dir():
            continue
        py_files.extend(sorted(directory.glob("*.py")))
        sh_files.extend(sorted(directory.glob("*.sh")))

    if not py_files and not sh_files:
        rep.skip(".claude/{hooks,scripts} — 검사할 스크립트 없음")
        return

    # python: 같은 인터프리터에서 파싱한다 (프로세스 포크 없음 — 훨씬 빠르다)
    for script in py_files:
        rel = script.relative_to(REPO).as_posix()
        try:
            ast.parse(script.read_text(encoding="utf-8"), filename=str(script))
        except SyntaxError as exc:
            rep.fail(f"{rel} — SyntaxError (line {exc.lineno}): {exc.msg}")
        except (OSError, UnicodeDecodeError) as exc:
            rep.fail(f"{rel} — 읽기 실패: {exc}")
        else:
            rep.ok(rel)

    if not sh_files:
        return

    bash = shutil.which("bash")
    if not bash:
        # 검증기 부재 — 실패가 아니다.
        rep.skip(f"bash 없음 — 셸 문법 검사 {len(sh_files)}건 건너뜀")
        return

    for script in sh_files:
        rel = script.relative_to(REPO).as_posix()
        try:
            proc = subprocess.run(
                [bash, "-n", str(script)],
                capture_output=True,
                text=True,
                timeout=15,
            )
        except (subprocess.TimeoutExpired, OSError) as exc:
            rep.skip(f"{rel} — 검사 실행 불가: {exc}")
            continue

        if proc.returncode == 0:
            rep.ok(rel)
        else:
            detail = (proc.stderr or proc.stdout).strip().splitlines()
            first = detail[0] if detail else f"exit {proc.returncode}"
            rep.fail(f"{rel} — {first}")


def iter_scan_files() -> list[Path]:
    files: list[Path] = []
    claude_dir = REPO / ".claude"
    if claude_dir.is_dir():
        files.extend(sorted(claude_dir.rglob("*.md")))
    docs_dir = REPO / "docs"
    if docs_dir.is_dir():
        files.extend(sorted(docs_dir.rglob("*.md")))
    return [f for f in files if f.relative_to(REPO).as_posix() not in SCAN_EXCLUDE]


def extract_refs(text: str) -> list[str]:
    found = []
    for match in REF_PATTERN.finditer(text):
        # 패턴이 플레이스홀더 직전에서 끊긴 경우 — `.claude/agents/{a,b}.md`가
        # `.claude/agents/`로 잘려 디렉터리 참조처럼 보이는 오탐을 막는다.
        if text[match.end():match.end() + 1] in REF_SKIP_CHARS:
            continue
        ref = match.group(0).rstrip(".,;:)]}`'\"")
        if ref and not (REF_SKIP_CHARS & set(ref)):
            found.append(ref)
    return found


def collect_hook_refs() -> dict[str, str]:
    """settings*.json의 hooks command가 가리키는 스크립트 경로.

    여기 오타가 나면 훅이 조용히 실패한다 — 차단이 안 걸려도 아무 신호가 없으므로
    문서의 깨진 링크보다 훨씬 위험하다.
    """
    refs: dict[str, str] = {}
    for rel in (".claude/settings.json", ".claude/settings.local.json"):
        path = REPO / rel
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue  # 검사 1이 이미 보고했다
        if not isinstance(data, dict):
            continue
        for event, entries in (data.get("hooks") or {}).items():
            for entry in entries or []:
                for hook in (entry or {}).get("hooks") or []:
                    for ref in extract_refs((hook or {}).get("command") or ""):
                        refs.setdefault(ref, f"{rel} [{event}]")
    return refs


def check_refs(rep: Report) -> None:
    rep.section("[3/3] 내부 참조 무결성")

    # ref -> 최초 발견 위치 (파일:줄 또는 settings 파일 [이벤트])
    # 훅 경로를 먼저 수집한다 — 스캔할 문서가 없어도 이 검사는 반드시 돌아야 한다.
    refs: dict[str, str] = dict(collect_hook_refs())
    n_hook_refs = len(refs)

    files = iter_scan_files()
    if not files:
        rep.skip("스캔 대상 문서 없음 — 훅 command 경로만 검사")
    for path in files:
        rel_src = path.relative_to(REPO).as_posix()
        try:
            lines = path.read_text(encoding="utf-8-sig").splitlines()
        except UnicodeDecodeError:
            rep.fail(f"{rel_src} — UTF-8 디코딩 실패 (문서는 UTF-8이어야 한다)")
            continue
        for lineno, line in enumerate(lines, start=1):
            for ref in extract_refs(line):
                refs.setdefault(ref, f"{rel_src}:{lineno}")

    broken = 0
    for ref in sorted(refs):
        if ref in REF_WHITELIST or (REPO / ref).exists():
            continue
        rep.fail(f"{ref} — 실재하지 않음 (참조: {refs[ref]})")
        broken += 1

    if not broken:
        rep.ok(
            f"문서 {len(files)}개 / 참조 {len(refs)}건"
            f" (훅 command 경로 {n_hook_refs}건 포함) — 깨진 링크 없음"
        )


def main(argv: list[str]) -> int:
    quiet = "--quiet" in argv
    rep = Report(quiet=quiet)

    if not quiet:
        print("[gate_harness] 층 A — 하네스 무결성 검증")
        print(f"  repo: {REPO}")

    check_json(rep)
    check_scripts(rep)
    check_refs(rep)

    print()
    if rep.fails:
        print(f"결과: FAIL {len(rep.fails)}건 / SKIP {rep.n_skip}건 / OK {rep.n_ok}건")
        print("하네스가 깨졌다. 위 FAIL 항목을 먼저 고칠 것.")
        return 1

    print(f"결과: PASS — SKIP {rep.n_skip}건 / OK {rep.n_ok}건")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
