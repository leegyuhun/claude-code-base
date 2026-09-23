#!/usr/bin/env python3
"""작업 정책 — [PAUSE]를 앞으로 당겨 1회 인터뷰로 굳힌다.

왜 필요한가
  하네스에는 [PAUSE]가 15개 있고 그중 5~6개가 초반(PRD~계획)에 몰려 있다.
  그런데 이들 대부분은 산출물을 봐야 판단할 수 있는 게 아니라 "이 프로젝트에서
  어떻게 할지"를 묻는 것이다 — 즉 매번 물을 이유가 없다.
  한 번 답을 받아 파일로 굳히면 이후 이슈에서는 묻지 않는다.

당길 수 없는 것 (이 파일이 다루지 않는 것)
  - plan.md 검토: plan이 나와야 본다  (단 pause/notify 선택은 정책으로 가능)
  - PHASE 8 수동 UI 테스트: 구현이 끝나야 한다. 절대 자동화 대상이 아니다
  - MR 머지 확인: 외부 시스템 상태
  - BLOCKED / 요구사항 변경 / 루프 halt: 예외 상황

사용법
  python .claude/scripts/policy.py show          # key=value 목록 (에이전트가 파싱)
  python .claude/scripts/policy.py get plan_review
  python .claude/scripts/policy.py init branch=new plan_review=notify ...
  python .claude/scripts/policy.py set plan_review=pause
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
POLICY_FILE = REPO / ".claude" / "loop-policy.json"

# 키 -> (허용값, 기본(=권장)값, 설명)
SCHEMA: dict[str, tuple[tuple[str, ...], str, str]] = {
    "branch": (
        ("new", "current"),
        "new",
        "이슈 작업 시 새 브랜치를 만들지 현재 브랜치를 쓸지",
    ),
    "track_confirm": (
        ("always", "boundary", "never"),
        "boundary",
        "TRACK(Sprint/Defect) 판정을 확인받을 시점. boundary=기준 경계일 때만",
    ),
    "plan_review": (
        ("pause", "notify"),
        "notify",
        "plan.md 검토 방식. notify=요약만 출력하고 진행(이의 시 /rollback)",
    ),
    "auto_run": (
        ("standard", "strict", "relaxed"),
        "standard",
        "구현 자동 진행 기준. standard=sprint-dev의 AUTO_RUN 6조건",
    ),
    "pitfall_capture": (
        ("ask", "auto", "skip"),
        "ask",
        "함정 회고 기록 방식. auto=후보를 자동 append",
    ),
}

ORDER = list(SCHEMA)


def emit(text: str) -> None:
    """UTF-8 바이트로 직접 쓴다 (Windows 콘솔 cp949에서 깨지거나 죽는 것 방지)."""
    try:
        sys.stdout.buffer.write(text.encode("utf-8", errors="replace"))
        sys.stdout.buffer.flush()
    except Exception:
        try:
            sys.stdout.write(text.encode("ascii", "replace").decode("ascii"))
        except Exception:
            pass


def load() -> tuple[dict[str, str], bool]:
    """(정책, 인터뷰 완료 여부). 파일이 없으면 기본값 + False."""
    defaults = {key: spec[1] for key, spec in SCHEMA.items()}
    if not POLICY_FILE.exists():
        return defaults, False
    try:
        data = json.loads(POLICY_FILE.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return defaults, False
    if not isinstance(data, dict):
        return defaults, False

    policy = dict(defaults)
    for key, spec in SCHEMA.items():
        value = data.get(key)
        if isinstance(value, str) and value in spec[0]:
            policy[key] = value
    return policy, bool(data.get("interviewed_at"))


def save(policy: dict[str, str], mark_interviewed: bool) -> None:
    payload = {"version": 1}
    payload.update({key: policy[key] for key in ORDER})
    if mark_interviewed:
        payload["interviewed_at"] = datetime.now(timezone.utc).astimezone().isoformat()
    else:
        _, was = load()
        if was:
            try:
                prev = json.loads(POLICY_FILE.read_text(encoding="utf-8-sig"))
                payload["interviewed_at"] = prev.get("interviewed_at", "")
            except Exception:
                pass
    POLICY_FILE.parent.mkdir(parents=True, exist_ok=True)
    POLICY_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


class PolicyError(Exception):
    """사용자에게 보여줄 오류. 메시지는 emit으로 내보낸다 (cp949에서 깨지지 않게)."""


def parse_pairs(args: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for arg in args:
        if "=" not in arg:
            raise PolicyError(f"형식 오류: '{arg}' (key=value 여야 한다)")
        key, value = arg.split("=", 1)
        key, value = key.strip(), value.strip()
        if key not in SCHEMA:
            raise PolicyError(f"알 수 없는 키: {key} (가능: {', '.join(ORDER)})")
        if value not in SCHEMA[key][0]:
            raise PolicyError(
                f"'{key}'의 값이 잘못됐다: {value} (가능: {', '.join(SCHEMA[key][0])})"
            )
        out[key] = value
    return out


def cmd_show() -> int:
    policy, interviewed = load()
    emit(f"interviewed={'true' if interviewed else 'false'}\n")
    for key in ORDER:
        emit(f"{key}={policy[key]}\n")
    if not interviewed:
        emit("\n# 아직 인터뷰하지 않았다. 위 값은 권장 기본값이며 아직 저장되지 않았다.\n")
        emit("# /prd 가 최초 1회 통합 인터뷰를 수행하고 policy.py init 으로 저장한다.\n")
    return 0


def cmd_get(args: list[str]) -> int:
    if not args:
        raise PolicyError("get KEY 형식으로 호출할 것")
    key = args[0]
    if key not in SCHEMA:
        raise PolicyError(f"알 수 없는 키: {key}")
    policy, _ = load()
    emit(policy[key] + "\n")
    return 0


def cmd_init(args: list[str]) -> int:
    policy, _ = load()
    policy.update(parse_pairs(args))
    save(policy, mark_interviewed=True)
    emit("[policy] 저장 완료 — 이후 이슈에서는 다시 묻지 않는다\n")
    for key in ORDER:
        emit(f"  {key}={policy[key]}\n")
    return 0


def cmd_set(args: list[str]) -> int:
    if not args:
        raise PolicyError("set key=value 형식으로 호출할 것")
    policy, interviewed = load()
    policy.update(parse_pairs(args))
    save(policy, mark_interviewed=not interviewed)
    emit("[policy] 갱신 완료\n")
    for key in ORDER:
        emit(f"  {key}={policy[key]}\n")
    return 0


def cmd_describe() -> int:
    """인터뷰 문항을 만들 때 쓰는 스키마 덤프."""
    for key in ORDER:
        values, default, desc = SCHEMA[key]
        emit(f"{key}: {desc}\n")
        emit(f"  가능={'|'.join(values)}  권장={default}\n")
    return 0


def main(argv: list[str]) -> int:
    if not argv:
        return cmd_show()
    command, args = argv[0], argv[1:]
    try:
        if command == "show":
            return cmd_show()
        if command == "get":
            return cmd_get(args)
        if command == "init":
            return cmd_init(args)
        if command == "set":
            return cmd_set(args)
        if command == "describe":
            return cmd_describe()
        raise PolicyError(f"알 수 없는 명령: {command} (show|get|init|set|describe)")
    except PolicyError as exc:
        emit(f"[policy] {exc}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
