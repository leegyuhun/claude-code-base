#!/usr/bin/env python3
"""Claude Code PostToolUse Hook — 빠른 게이트 (짧은 루프).

설계 근거: docs/Upgrade_loop.md STEP 3.

왜 Bash가 핵심 매처인가
  PreToolUse가 .pas/.dfm에 대한 Write/Edit을 전면 차단한다. 따라서 이 파일들이
  바뀌는 경로는 사실상 Bash(python cp949 스크립트)뿐이다. Write/Edit도 매처에
  포함하지만 그건 이중 방어이고, 실제로 손상을 잡는 지점은 Bash 이후다.

비용 관리
  Write/Edit는 file_path가 .pas/.dfm이 아니면 즉시 통과한다.
  Bash는 **항상** git status로 실제 변경을 본다 (수백 ms). 처음엔 명령 문자열에
  .pas/.dfm/cp949가 있을 때만 검사했는데, `python fix.py` 한 줄이 .pas 수십 개를
  다시 쓰는 경로를 통째로 놓쳤다. 놓치는 비용(복구 불가)이 검사 비용보다 크다.
  Delphi에는 린터도 단독 타입체커도 없으므로, 빠른 게이트에서 린트를 돌릴 수
  없다. 인코딩·구조 검사가 그 자리를 대신한다.

종료 코드
  2 = 즉시 교정 요구. stderr가 모델에게 전달된다.
      PostToolUse는 이미 실행된 뒤이므로 "차단"이 아니라 "되돌려라"는 신호다.
      인코딩 손상처럼 두면 안 되는 것에만 쓴다.
  0 = 통과. 경고는 stdout으로만 남긴다 — 편집마다 흐름을 끊지 않기 위해서다.
      경고 항목은 Validator PHASE 7이 다시 검사한다.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

CP949_SUFFIXES = (".pas", ".dfm")

# validator 7-1.5의 날짜 하드코딩 검사와 같은 패턴
DATE_HARDCODE = re.compile(
    r"StrToDate\('20|EncodeDate\(\s*20|StrToDateTime\('20", re.IGNORECASE
)

# .pas의 컴포넌트 필드 선언 — 이게 바뀌면 .dfm도 같이 바뀌어야 한다
COMPONENT_FIELD = re.compile(r"^\s*\w+\s*:\s*T[A-Z]\w*\s*;")


def emit(stream, text: str) -> None:
    """UTF-8 바이트로 직접 쓴다.

    Windows에서 stdout/stderr의 기본 인코딩은 cp949다. em dash(—)나 이모지처럼
    cp949에 없는 문자를 그냥 write하면 UnicodeEncodeError로 훅이 죽고,
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


def git(*args: str) -> str:
    try:
        proc = subprocess.run(
            ["git", *args], cwd=REPO, capture_output=True, timeout=20
        )
    except (subprocess.TimeoutExpired, OSError):
        return ""
    if proc.returncode != 0:
        return ""
    return proc.stdout.decode("utf-8", errors="replace")


def changed_cp949_files() -> list[tuple[str, str]]:
    """(status, path) 목록. status는 git status --porcelain의 2글자."""
    out = git("status", "--porcelain", "--untracked-files=all")
    files: list[tuple[str, str]] = []
    for line in out.splitlines():
        if len(line) < 4:
            continue
        status, path = line[:2], line[3:].strip()
        if path.startswith('"') and path.endswith('"'):
            path = path[1:-1]
        if " -> " in path:  # rename
            path = path.split(" -> ", 1)[1]
        if path.lower().endswith(CP949_SUFFIXES):
            files.append((status.strip(), path))
    return files


def check_encoding(path: Path) -> str | None:
    """CP949 무결성. 손상이면 사유 문자열, 정상이면 None."""
    try:
        raw = path.read_bytes()
    except OSError:
        return None
    if not raw:
        return None
    if raw.startswith(b"\xef\xbb\xbf"):
        # UTF-8 BOM 파일은 encoding-critical.md가 명시적으로 허용하는 형태다
        return None
    try:
        raw.decode("cp949")
        return None
    except UnicodeDecodeError:
        pass
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError:
        return "CP949로도 UTF-8로도 디코딩되지 않는다 — 인코딩이 깨졌다"
    return "UTF-8로 저장됐다 — 원본 CP949 한글 바이트가 파괴됐을 가능성이 높다"


def diff_added_lines() -> dict[str, list[str]]:
    """수정된 .pas/.dfm의 추가된 줄. 신규(untracked) 파일은 여기 없다."""
    out = git("diff", "-U0", "--", "*.pas", "*.dfm")
    result: dict[str, list[str]] = {}
    current: str | None = None
    for line in out.splitlines():
        if line.startswith("+++ b/"):
            current = line[6:]
            result.setdefault(current, [])
        elif line.startswith("+++") or line.startswith("---"):
            continue
        elif line.startswith("+") and current is not None:
            result[current].append(line[1:])
    return result


def project_files(start: Path):
    """변경 파일에서 상위로 올라가며 .dpr/.dproj를 찾는다 (validator 7-2와 같은 방식)."""
    directory = start.parent
    for _ in range(6):
        for pattern in ("*.dpr", "*.dproj"):
            yield from directory.glob(pattern)
        if directory == REPO or directory.parent == directory:
            break
        directory = directory.parent


def check_dpr_registration(rel_path: str) -> str | None:
    path = REPO / rel_path
    unit = path.stem.lower().encode("ascii", errors="ignore")
    if not unit:
        return None
    seen = False
    for project in project_files(path):
        seen = True
        try:
            if unit in project.read_bytes().lower():
                return None
        except OSError:
            continue
    if not seen:
        return None  # 프로젝트 파일을 못 찾았으면 판단하지 않는다
    return f"{rel_path} — .dpr/.dproj에 미등록. 빌드 시 'Unit not found' 발생 가능"


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    if not isinstance(data, dict):
        return 0
    tool_input = data.get("tool_input")
    if not isinstance(tool_input, dict):
        return 0

    # ── 빠른 경로 ──
    # Write/Edit는 file_path로 판단할 수 있다: .pas/.dfm이 아니면 CP949 파일이 바뀔 수 없다.
    # Bash는 판단할 수 없다. 명령 문자열에 .pas가 없어도 `python fix.py` 한 줄이
    # 수십 개 .pas를 다시 쓸 수 있다 — 문자열 필터는 우회 경로였다 (감사 결함 ③).
    # Bash 뒤에는 항상 git status로 실제 변경을 본다. 비용은 수백 ms, 놓치는 비용은 복구 불가.
    file_path = tool_input.get("file_path") or ""
    if file_path and not file_path.lower().endswith(CP949_SUFFIXES):
        return 0

    changed = changed_cp949_files()
    if not changed:
        return 0

    changed_paths = {path for _, path in changed}
    problems: list[str] = []
    warnings: list[str] = []

    # 1) CP949 무결성 — 유일한 exit 2 사유
    for _, rel in changed:
        reason = check_encoding(REPO / rel)
        if reason:
            problems.append(f"{rel} — {reason}")

    added = diff_added_lines()

    for status, rel in changed:
        lower = rel.lower()
        is_new = "?" in status or "A" in status

        # 2) 신규 .pas의 프로젝트 등록
        if is_new and lower.endswith(".pas"):
            note = check_dpr_registration(rel)
            if note:
                warnings.append(note)

        # 3) .pas 수정 시 짝 .dfm 동기화
        #    컴포넌트 필드 선언이 바뀐 경우에만 경고한다 (로직만 고친 건 제외)
        if lower.endswith(".pas") and not is_new:
            lines = added.get(rel, [])
            if any(COMPONENT_FIELD.match(line) for line in lines):
                dfm = (REPO / rel).with_suffix(".dfm")
                dfm_rel = dfm.relative_to(REPO).as_posix()
                if dfm.exists() and dfm_rel not in changed_paths:
                    warnings.append(
                        f"{rel} — 컴포넌트 선언이 바뀌었는데 {dfm_rel}는 미변경. 동기화 확인 필요"
                    )

        # 4) 날짜 하드코딩
        if lower.endswith(".pas"):
            if is_new:
                try:
                    text = (REPO / rel).read_bytes().decode("cp949", errors="replace")
                except OSError:
                    text = ""
                hits = [ln for ln in text.splitlines() if DATE_HARDCODE.search(ln)]
            else:
                hits = [ln for ln in added.get(rel, []) if DATE_HARDCODE.search(ln)]
            for hit in hits[:3]:
                warnings.append(f"{rel} — 날짜 하드코딩: {hit.strip()[:80]}")

    if warnings:
        out = "\n".join(f"  [warn] {w}" for w in warnings)
        emit(sys.stdout, f"[fast-gate] 경고 {len(warnings)}건\n{out}\n")

    if not problems:
        return 0

    body = "\n".join(f"  - {p}" for p in problems)
    message = (
        "\n[fast-gate] CP949 인코딩 손상 감지 — 즉시 되돌릴 것\n\n"
        f"{body}\n\n"
        "  방금 실행한 수정이 파일을 UTF-8로 다시 썼을 가능성이 높다.\n"
        "  1) git checkout -- <파일> 로 원본을 복구한다\n"
        "  2) python3 의 encoding='cp949' 방식으로 다시 수정한다\n"
        "     (.claude/rules/encoding-critical.md 참조)\n"
        "  3) Write/Edit 도구로는 이 파일들을 고칠 수 없다\n"
    )
    emit(sys.stderr, message)
    return 2


if __name__ == "__main__":
    sys.exit(main())
