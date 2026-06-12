"""
.claude/projects/INDEX.md 자동 생성기.

`.claude/projects/*.generated.md` 카드들을 스캔해서 한 장의 인덱스로 만든다.
모듈군(`trunk/` 첫 단계 디렉토리)별로 그룹핑.

카드의 메타 정보는 `parse_dproj.py`가 출력한 markdown 헤더에서 직접 추출한다.
스캔 대상 라인:
  - `- **설명**: ...`
  - `- **버전**: ...`
  - `- **dproj**: ...`            (모듈군 추출에 사용)
  - `## 외부 의존성 (N개)`         (refs 개수)
  - `**Release**` 다음 코드블럭     (주요 컴파일 정의)
"""

from __future__ import annotations

import io
import re
import sys

# 콘솔 인코딩이 utf-8이 아니면 강제 — em-dash 등이 깨지지 않게.
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, io.UnsupportedOperation):
        pass
from collections import OrderedDict, defaultdict
from pathlib import Path
from typing import Iterable

PROJECTS_DIR = Path(__file__).resolve().parent.parent / "projects"
INDEX_PATH = PROJECTS_DIR / "INDEX.md"


# 카드에서 뽑을 필드
RE_DESC = re.compile(r"^\s*-\s+\*\*설명\*\*:\s*(.+?)\s*$", re.M)
RE_VER = re.compile(r"^\s*-\s+\*\*버전\*\*:\s*(.+?)\s*$", re.M)
RE_DPROJ = re.compile(r"^\s*-\s+\*\*dproj\*\*:\s*`([^`]+)`\s*$", re.M)
RE_REFS = re.compile(r"^##\s+외부\s+의존성\s+\((\d+)개\)\s*$", re.M)
RE_RELEASE_BLOCK = re.compile(
    r"\*\*Release\*\*\s*\n\s*\n```\s*\n(.*?)\n```", re.S
)
RE_ENTRY_POINT = re.compile(r"^\s*-\s+\*\*진입점\*\*:\s*`([^`]+)`\s*$", re.M)

# 모듈 식별자 토큰 (CLAUDE.md 기준)
MODULE_TOKENS = {"FWCHART", "FCOUNT", "JRGROUP", "BOHUM", "BHGROUP"}


def _extract_module_group(dproj_path_str: str) -> str:
    """`.../trunk/<A>/<B>/...` 에서 모듈군 라벨(`<A>/<B>` 또는 `<A>`)을 뽑는다."""
    p = dproj_path_str.replace("\\", "/")
    m = re.search(r"/trunk/(.+)", p)
    if not m:
        return "(기타)"
    after = m.group(1)
    parts = after.split("/")
    if len(parts) >= 3 and parts[0] == "Module":
        return f"Module/{parts[1]}"
    if len(parts) >= 2:
        return parts[0]
    return "(기타)"


def _primary_defines(defines: list[str]) -> list[str]:
    """Release 정의 중 모듈 식별 토큰 + 처음 N개만 골라 인덱스 한 줄에 표시."""
    if not defines:
        return []
    # 모듈 토큰을 앞으로
    priority = [d for d in defines if d.upper() in MODULE_TOKENS]
    rest = [d for d in defines if d.upper() not in MODULE_TOKENS and d.upper() not in {"RELEASE", "DEBUG"}]
    return (priority + rest)[:4]


def parse_card(card_path: Path) -> dict | None:
    text = card_path.read_text(encoding="utf-8", errors="replace")

    desc_m = RE_DESC.search(text)
    ver_m = RE_VER.search(text)
    dproj_m = RE_DPROJ.search(text)
    refs_m = RE_REFS.search(text)
    rel_m = RE_RELEASE_BLOCK.search(text)
    entry_m = RE_ENTRY_POINT.search(text)

    defines: list[str] = []
    if rel_m:
        defines = [d.strip() for d in rel_m.group(1).split(";") if d.strip()]

    return {
        "card_file": card_path.name,
        "card_stem": card_path.name.replace(".generated.md", ""),
        "description": desc_m.group(1) if desc_m else "",
        "version": ver_m.group(1) if ver_m else "",
        "dproj": dproj_m.group(1) if dproj_m else "",
        "refs": int(refs_m.group(1)) if refs_m else 0,
        "entry_point": entry_m.group(1) if entry_m else "",
        "defines": defines,
        "primary_defines": _primary_defines(defines),
        "group": _extract_module_group(dproj_m.group(1)) if dproj_m else "(기타)",
    }


def collect_cards(projects_dir: Path) -> list[dict]:
    cards: list[dict] = []
    for card_path in sorted(projects_dir.glob("*.generated.md")):
        info = parse_card(card_path)
        if info:
            cards.append(info)
    return cards


def render_index(cards: list[dict]) -> str:
    # 그룹핑
    by_group: dict[str, list[dict]] = defaultdict(list)
    for c in cards:
        by_group[c["group"]].append(c)

    # 그룹 순서 — Module/* 우선, 그 뒤 알파벳, (기타)는 맨 끝
    group_keys = list(by_group.keys())
    def _gkey(g: str) -> tuple[int, str]:
        if g == "(기타)":
            return (3, g)
        if g.startswith("Module/"):
            return (0, g)
        if g in ("Common", "CommonV7", "ComUnit"):
            return (1, g)
        return (2, g)
    group_keys.sort(key=_gkey)

    lines: list[str] = []
    a = lines.append

    a("# 프로젝트 의존성 카드 인덱스")
    a("")
    a("> `.claude/scripts/gen_index.py`가 자동 생성. 직접 편집 금지.")
    a(">")
    a("> 작업 시작 시: 작업 대상 프로젝트를 아래에서 찾아 카드 링크로 이동 →")
    a("> 그 프로젝트가 이미 참조 중인 공용 unit에서 재사용 가능한 함수/클래스를 먼저 검색.")
    a(">")
    a("> 재생성:")
    a("> - 카드 일괄: `python .claude/scripts/parse_dproj.py --all`")
    a("> - 인덱스만: `python .claude/scripts/gen_index.py`")
    a("")
    a(f"**총 {len(cards)}개 프로젝트** · 그룹 {len(group_keys)}개")
    a("")

    # 그룹별 표
    for group in group_keys:
        group_cards = sorted(by_group[group], key=lambda c: c["card_stem"].lower())
        a(f"## {group}  ({len(group_cards)})")
        a("")
        a("| 카드 | 설명 | 버전 | 주요 정의 | refs |")
        a("| --- | --- | --- | --- | ---: |")
        for c in group_cards:
            defines_str = " ".join(f"`{d}`" for d in c["primary_defines"]) or "—"
            desc = c["description"] or "—"
            ver = c["version"] or "—"
            link = f"[{c['card_stem']}]({c['card_file']})"
            a(f"| {link} | {desc} | {ver} | {defines_str} | {c['refs']} |")
        a("")

    return "\n".join(lines).rstrip() + "\n"


def detect_stale_cards(projects_dir: Path, current_cards: Iterable[dict]) -> list[Path]:
    """카드의 `dproj` 메타 라인 기준으로 stale 식별.

    같은 dproj 경로가 두 카드에 동시에 매핑돼 있으면, base 단독(`__` 없음) 쪽이
    이전 실행의 잔존물이다. 그쪽을 stale로 잡는다.

    또한 어느 카드의 dproj 경로 파일이 실제로 사라진 경우(`.dproj` 이동/삭제)도
    stale로 잡는다.
    """
    by_dproj: dict[str, list[dict]] = defaultdict(list)
    for c in current_cards:
        if c["dproj"]:
            by_dproj[c["dproj"]].append(c)

    stale: list[Path] = []
    for dproj_path, group in by_dproj.items():
        # 같은 dproj를 가리키는 카드가 여러 개 — base 단독을 stale로
        if len(group) > 1:
            for c in group:
                if "__" not in c["card_stem"]:
                    stale.append(projects_dir / c["card_file"])
        # dproj 파일이 사라졌으면 그 카드도 stale
        else:
            try:
                if not Path(dproj_path).exists():
                    stale.append(projects_dir / group[0]["card_file"])
            except OSError:
                pass
    return sorted(set(stale))


def filter_dedup(cards: list[dict]) -> list[dict]:
    """같은 dproj를 가리키는 카드 중에서 prefixed(`__` 포함) 쪽을 우선 채택.

    INDEX 표에서 중복 줄이 보이지 않도록 dedup. base 단독은 stale 탐지에서만 사용.
    """
    by_dproj: dict[str, list[dict]] = defaultdict(list)
    others: list[dict] = []
    for c in cards:
        if c["dproj"]:
            by_dproj[c["dproj"]].append(c)
        else:
            others.append(c)
    chosen: list[dict] = []
    for group in by_dproj.values():
        if len(group) == 1:
            chosen.append(group[0])
            continue
        prefixed = [c for c in group if "__" in c["card_stem"]]
        chosen.append(prefixed[0] if prefixed else group[0])
    return chosen + others


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="프로젝트 의존성 카드 INDEX 생성기")
    ap.add_argument(
        "--delete-stale",
        action="store_true",
        help="식별된 stale 카드(.generated.md) 파일을 실제로 삭제. "
        "기준: 같은 dproj를 가리키는 카드 중 base 단독, "
        "또는 dproj 파일이 사라진 경우.",
    )
    args = ap.parse_args()

    if not PROJECTS_DIR.exists():
        print(f"[!] {PROJECTS_DIR} 없음", file=sys.stderr)
        return 1
    cards = collect_cards(PROJECTS_DIR)
    if not cards:
        print(f"[!] {PROJECTS_DIR}에 .generated.md 없음", file=sys.stderr)
        return 1

    # stale을 먼저 식별 (dedup 전 전체 카드 기준)
    stale = detect_stale_cards(PROJECTS_DIR, cards)
    stale_set = {p.name for p in stale}

    # INDEX에 stale 제외하고 출력
    visible = [c for c in cards if c["card_file"] not in stale_set]
    deduped = filter_dedup(visible)

    INDEX_PATH.write_text(render_index(deduped), encoding="utf-8")
    print(
        f"[ok] {INDEX_PATH} 생성됨 "
        f"(표시 {len(deduped)} / 카드 파일 {len(cards)} / stale {len(stale)})"
    )

    if stale:
        print(f"\n[!] stale 카드 {len(stale)}개:")
        for p in stale:
            try:
                rel = p.relative_to(p.parent.parent.parent)
            except ValueError:
                rel = p
            print(f"  - {rel}")

        if args.delete_stale:
            deleted = 0
            for p in stale:
                try:
                    p.unlink()
                    deleted += 1
                except OSError as e:
                    print(f"  [!] 삭제 실패: {p.name} ({e})", file=sys.stderr)
            print(f"\n[ok] {deleted}/{len(stale)}개 삭제 완료.")
        else:
            print(
                "\n정리하려면 `python .claude/scripts/gen_index.py --delete-stale` 실행."
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
