#!/usr/bin/env python3
"""프로젝트 어댑터 — 언어·빌드 도구와 하네스 사이의 유일한 접점.

왜 필요한가
  훅(Stop / PostToolUse)은 "무엇으로 빌드하는가"를 알면 안 된다. 그걸 훅에 박으면
  하네스가 특정 언어에 묶인다. 대신 `.claude/harness.json`에 명령만 적어두고,
  훅은 이 모듈을 통해 "build를 돌려라 / fast_check를 돌려라"만 요청한다.

harness.json 스키마
  {
    "source_globs": ["src/**/*.py"],             소스 판정. 비면 모든 변경 파일이 소스
    "build":      {"cmd": "", "timeout": 600},   Stop 훅 PHASE 6
    "test":       {"cmd": "", "timeout": 900},   Validator PHASE 7
    "fast_check": {"cmd": "", "timeout": 60},    PostToolUse (린트/타입체크)
    "error_pattern": ""                          실패 시그니처 추출 정규식 (선택)
  }
  - cmd가 비어 있으면 "검증기 부재"다. 실패가 아니다 — 훅은 통과시킨다.
  - fast_check.cmd의 `{files}`는 변경된 소스 파일 목록(공백 구분)으로 치환된다.
  - error_pattern의 named group `file`, `line`, `code`가 있으면 시그니처에 쓴다.
    그룹이 없으면 첫 매칭 줄이 시그니처다. 패턴이 없으면 마지막 비어있지 않은 줄.

사용법
  python .claude/scripts/harness_config.py show
  python .claude/scripts/harness_config.py run build|test|fast_check [파일...]

종료 코드 (run)
  0 = 통과 / 1 = 실패 / 3 = 검증기 부재 (cmd 없음·명령 없음·타임아웃)
"""

from __future__ import annotations

import fnmatch
import json
import locale
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CONFIG_FILE = REPO / ".claude" / "harness.json"

KINDS = ("build", "test", "fast_check")
DEFAULT_TIMEOUT = {"build": 600, "test": 900, "fast_check": 60}

EXIT_MISSING = 3


def emit(text: str, stream=None) -> None:
    """UTF-8 바이트로 직접 쓴다 (Windows 콘솔 기본 인코딩에서 em dash 등으로 죽는 것 방지)."""
    stream = stream or sys.stdout
    try:
        stream.buffer.write(text.encode("utf-8", errors="replace"))
        stream.buffer.flush()
    except Exception:
        try:
            stream.write(text.encode("ascii", "replace").decode("ascii"))
        except Exception:
            pass


def load() -> dict:
    """설정을 읽는다. 파일이 없거나 깨졌으면 빈 dict — 부재로 취급한다.

    깨진 JSON은 층 A(gate_harness.py)가 따로 FAIL로 보고한다. 여기서까지
    실패로 치면 같은 결함이 두 경로로 루프를 돌린다.
    """
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def command(config: dict, kind: str) -> tuple[str, int]:
    entry = config.get(kind)
    if not isinstance(entry, dict):
        return "", DEFAULT_TIMEOUT[kind]
    cmd = entry.get("cmd") or ""
    try:
        timeout = int(entry.get("timeout") or DEFAULT_TIMEOUT[kind])
    except (TypeError, ValueError):
        timeout = DEFAULT_TIMEOUT[kind]
    return (cmd.strip() if isinstance(cmd, str) else ""), timeout


def is_source(config: dict, rel_path: str) -> bool:
    globs = config.get("source_globs") or []
    if not isinstance(globs, list) or not globs:
        return True
    rel = rel_path.replace("\\", "/")
    # fnmatch의 *는 /까지 매칭하지만 `src/**/*.py`는 `src/a.py`를 놓친다 — `**/`를 접어 한 번 더 본다
    return any(
        fnmatch.fnmatch(rel, g) or fnmatch.fnmatch(rel, g.replace("**/", ""))
        for g in globs if isinstance(g, str)
    )


def changed_files() -> list[str]:
    """작업 트리에서 바뀐 파일 (추적·미추적, 삭제 제외)."""
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all"],
            cwd=REPO, capture_output=True, timeout=30,
        )
    except (subprocess.TimeoutExpired, OSError):
        return []
    if proc.returncode != 0:
        return []
    files = []
    for line in proc.stdout.decode("utf-8", errors="replace").splitlines():
        if len(line) < 4 or "D" in line[:2]:
            continue
        path = line[3:].strip().strip('"')
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        files.append(path)
    return files


def changed_sources(config: dict | None = None) -> list[str]:
    config = load() if config is None else config
    return [f for f in changed_files() if is_source(config, f)]


def run(kind: str, files: list[str] | None = None,
        config: dict | None = None) -> tuple[int | None, str]:
    """(exit code, 출력). code=None이면 검증기 부재."""
    config = load() if config is None else config
    cmd, timeout = command(config, kind)
    if not cmd:
        return None, f"harness.json에 {kind}.cmd 없음"
    if "{files}" in cmd:
        if not files:
            return 0, ""  # 검사할 파일이 없다
        # shlex.quote의 작은따옴표는 cmd.exe가 모른다 — 공백 있는 경로만 큰따옴표로 감싼다
        cmd = cmd.replace("{files}", " ".join(f'"{f}"' if " " in f else f for f in files))
    program = first_token(cmd)
    if program and not program_exists(program):
        return None, f"{kind} 명령을 찾을 수 없음: {program}"
    try:
        proc = subprocess.run(
            cmd, shell=True, cwd=REPO, capture_output=True, timeout=timeout
        )
    except subprocess.TimeoutExpired:
        return None, f"{kind} 타임아웃 ({timeout}초)"
    except OSError as exc:
        return None, f"{kind} 실행 불가: {exc}"
    out = decode(proc.stdout + proc.stderr)
    # 127 = sh의 command not found. 사전 검사를 빠져나간 경우의 이중 방어
    if proc.returncode == 127:
        return None, f"{kind} 명령을 찾을 수 없음: {program}"
    return proc.returncode, out


# 셸 내장 명령 — which로 찾을 수 없지만 실재한다
SHELL_BUILTINS = {"echo", "set", "cd", "call", "exit", "true", "false", "test", "[", "export", "."}


def first_token(cmd: str) -> str:
    cmd = cmd.strip()
    if cmd.startswith('"'):
        end = cmd.find('"', 1)
        return cmd[1:end] if end > 0 else cmd[1:]
    return cmd.split()[0] if cmd.split() else ""


def program_exists(program: str) -> bool:
    """명령이 실재하는가.

    도구가 없는 것은 "검증기 부재"지 "검증 실패"가 아니다. 그런데 cmd.exe는
    없는 명령에도 exit 1을 돌려준다 — 실행 후 exit code로는 구분할 수 없어서
    실행 전에 확인한다.
    """
    if program.lower() in SHELL_BUILTINS:
        return True
    if shutil.which(program):
        return True
    path = Path(program)
    return (path if path.is_absolute() else REPO / path).exists()


def decode(raw: bytes) -> str:
    """빌드 도구 출력은 UTF-8일 수도, OS 로케일 코드페이지일 수도 있다."""
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode(locale.getpreferredencoding(False) or "utf-8", errors="replace")


def signature(kind: str, output: str, code: int,
              config: dict | None = None) -> tuple[str, str]:
    """(요약 한 줄, 헛돌기 감지용 시그니처)."""
    config = load() if config is None else config
    pattern = config.get("error_pattern") or ""
    regex = None
    if isinstance(pattern, str) and pattern:
        try:
            regex = re.compile(pattern)
        except re.error:
            regex = None
    if regex:
        for line in output.splitlines():
            match = regex.search(line)
            if not match:
                continue
            groups = {k: v for k, v in match.groupdict().items() if v}
            if "file" in groups:
                groups["file"] = Path(groups["file"]).name
            parts = [groups[k] for k in ("code", "file", "line") if k in groups]
            sig = ":".join(parts) if parts else line.strip()[:120]
            return line.strip()[:200], f"{kind}:{sig}"
    tail = [ln.strip() for ln in output.splitlines() if ln.strip()][-1:]
    summary = tail[0][:200] if tail else f"{kind} exit {code}"
    return summary, f"{kind}:exit{code}:{summary[:60]}"


def main(argv: list[str]) -> int:
    if not argv or argv[0] not in ("show", "run"):
        emit(__doc__ or "")
        return 2
    config = load()
    if argv[0] == "show":
        emit(f"config={CONFIG_FILE.relative_to(REPO).as_posix()}"
             f" ({'있음' if CONFIG_FILE.exists() else '없음'})\n")
        for kind in KINDS:
            cmd, timeout = command(config, kind)
            emit(f"{kind}={cmd or '(없음)'} timeout={timeout}\n")
        emit(f"source_globs={config.get('source_globs') or '(전체)'}\n")
        return 0

    if len(argv) < 2 or argv[1] not in KINDS:
        emit(f"사용법: run {'|'.join(KINDS)} [파일...]\n", sys.stderr)
        return 2
    kind = argv[1]
    files = argv[2:] or (changed_sources(config) if kind == "fast_check" else None)
    code, out = run(kind, files, config)
    if code is None:
        emit(f"[{kind}] 검증기 부재 — {out}\n")
        return EXIT_MISSING
    emit(out)
    emit(f"\n[{kind}] {'PASS' if code == 0 else f'FAIL (exit {code})'}\n")
    return 0 if code == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
