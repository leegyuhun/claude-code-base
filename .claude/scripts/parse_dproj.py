"""
Delphi .dproj 파서 — 프로젝트별 의존성 카드 자동 생성.

입력: .dproj 파일 경로 (1개 또는 여러 개)
출력: .claude/projects/{ProjectName}.generated.md

추출 항목:
  - DCC_Define (Release / Debug 분리)
  - DCCReference (외부 unit 참조, 경로 기준 카테고리 그루핑)
  - <Form>, <DesignClass> 메타
  - VersionInfoKeys (회사, 파일 설명, 버전, 코드페이지)
  - DCC_UnitSearchPath, DCC_ExeOutput 등 빌드 경로

`.dpr`은 CP949 인코딩이므로 의도적으로 읽지 않는다 — `.dproj` XML(UTF-8)만 사용.
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

# .dproj 루트 네임스페이스
NS = "http://schemas.microsoft.com/developer/msbuild/2003"
NS_PREFIX = f"{{{NS}}}"

# 산출물 루트 (프로젝트 루트 기준 상대)
PROJECTS_DIR = Path(__file__).resolve().parent.parent / "projects"
TRUNK_ROOT = Path(__file__).resolve().parent.parent.parent / "trunk"


# ---------------------------------------------------------------------------
# 데이터 구조
# ---------------------------------------------------------------------------


@dataclass
class Reference:
    """DCCReference 1건."""

    raw_path: str  # 원본 (역슬래시 그대로)
    norm_path: str  # trunk 기준 forward-slash 상대경로 (밖이면 절대경로)
    is_local: bool = False  # 프로젝트 폴더 내부 = 로컬 소스
    in_trunk: bool = True  # trunk 외부면 False (외부 라이브러리 등)
    form: str | None = None
    design_class: str | None = None


@dataclass
class Project:
    dproj_path: Path
    name: str
    main_source: str = ""
    project_guid: str = ""
    exe_output: str = ""
    defines_release: list[str] = field(default_factory=list)
    defines_debug: list[str] = field(default_factory=list)
    search_paths: list[str] = field(default_factory=list)
    version_info: "OrderedDict[str, str]" = field(default_factory=OrderedDict)
    code_page: str = ""
    references: list[Reference] = field(default_factory=list)


# ---------------------------------------------------------------------------
# XML 헬퍼
# ---------------------------------------------------------------------------


def _qname(tag: str) -> str:
    """루트 네임스페이스가 붙은 태그명."""
    return f"{NS_PREFIX}{tag}"


def _strip_ns(tag: str) -> str:
    """`{ns}Name` 형태 → `Name`."""
    if tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


# ---------------------------------------------------------------------------
# 경로 → 카테고리
# ---------------------------------------------------------------------------

# (정규식 prefix, 라벨) — 위에서부터 가장 먼저 매치되는 게 선택됨.
# 더 구체적인 prefix를 위에, 일반적인 prefix를 아래에 둘 것.
CATEGORY_RULES: list[tuple[str, str]] = [
    (r"Common/Class/CtComm/", "공용/Class/CtComm — DLL 호출 래퍼"),
    (r"Common/Class/LIBData/", "공용/Class/LIBData — 라이브러리 데이터"),
    (r"Common/Class/Helper/", "공용/Class/Helper"),
    (r"Common/Class/", "공용/Class — 공용 클래스 (MType/MString/...)"),
    (r"Common/Const/YSRMDLConst/", "공용/Const/YSRMDLConst — 모듈 상수"),
    (r"Common/Const/", "공용/Const — 공용 상수"),
    (r"Common/Func/Json/", "공용/Func/Json"),
    (r"Common/Func/Encryption/", "공용/Func/Encryption"),
    (r"Common/Func/XMLLibrary/", "공용/Func/XMLLibrary"),
    (r"Common/Func/", "공용/Func — 공용 함수 (MUtil/MCOMFunction/...)"),
    (r"Common/Forms/", "공용/Forms — 공용 폼"),
    (r"Common/ExtraMDL/Checkup/", "공용/ExtraMDL/Checkup — 검진"),
    (r"Common/ExtraMDL/NullChart/", "공용/ExtraMDL/NullChart — 백지차트"),
    (r"Common/ExtraMDL/MedInterface/", "공용/ExtraMDL/MedInterface"),
    (r"Common/ExtraMDL/NHISLinkage/", "공용/ExtraMDL/NHISLinkage — 건강보험 연계"),
    (r"Common/ExtraMDL/Doctorvice/", "공용/ExtraMDL/Doctorvice"),
    (r"Common/ExtraMDL/HiWebnet/", "공용/ExtraMDL/HiWebnet"),
    (r"Common/ExtraMDL/MsgClient/", "공용/ExtraMDL/MsgClient"),
    (r"Common/ExtraMDL/UBInterface/", "공용/ExtraMDL/UBInterface"),
    (r"Common/ExtraMDL/UBCertificate/", "공용/ExtraMDL/UBCertificate"),
    (r"Common/ExtraMDL/UBAuthSJ/", "공용/ExtraMDL/UBAuthSJ"),
    (r"Common/ExtraMDL/UBcareMedia/", "공용/ExtraMDL/UBcareMedia"),
    (r"Common/ExtraMDL/PatientGroup/", "공용/ExtraMDL/PatientGroup"),
    (r"Common/ExtraMDL/PatientHistory/", "공용/ExtraMDL/PatientHistory"),
    (r"Common/ExtraMDL/PatientWaitStatus/", "공용/ExtraMDL/PatientWaitStatus"),
    (r"Common/ExtraMDL/LiveCampaign/", "공용/ExtraMDL/LiveCampaign"),
    (r"Common/ExtraMDL/DisReg/", "공용/ExtraMDL/DisReg"),
    (r"Common/ExtraMDL/Survey/", "공용/ExtraMDL/Survey"),
    (r"Common/ExtraMDL/BARCode/", "공용/ExtraMDL/BARCode"),
    (r"Common/ExtraMDL/UBTransData/", "공용/ExtraMDL/UBTransData"),
    (r"Common/ExtraMDL/YSRAgentMaterial/", "공용/ExtraMDL/YSRAgentMaterial"),
    (r"Common/ExtraMDL/YSRFile/", "공용/ExtraMDL/YSRFile"),
    (r"Common/ExtraMDL/", "공용/ExtraMDL — 기타 확장 모듈"),
    (r"Common/ResData/", "공용/ResData — 리소스"),
    (r"Common/About/", "공용/About"),
    (r"Common/", "공용 (기타)"),
    (r"CommonBL/", "CommonBL — 비즈로직 공용"),
    (r"CommonV7/Class/", "CommonV7/Class — VCL 오버라이드"),
    (r"CommonV7/Const/", "CommonV7/Const"),
    (r"CommonV7/", "CommonV7 (기타)"),
    (r"ComUnit/진료파트/Finale/Child/", "ComUnit/진료파트/Finale/Child"),
    (r"ComUnit/진료파트/Finale/CtComm/", "ComUnit/진료파트/Finale/CtComm"),
    (r"ComUnit/진료파트/Finale/Class/", "ComUnit/진료파트/Finale/Class"),
    (r"ComUnit/진료파트/Finale/ToolWin/", "ComUnit/진료파트/Finale/ToolWin"),
    (r"ComUnit/진료파트/Finale/FindCode/", "ComUnit/진료파트/Finale/FindCode"),
    (r"ComUnit/진료파트/Finale/FindPa/", "ComUnit/진료파트/Finale/FindPa"),
    (r"ComUnit/진료파트/Finale/DETAIL/", "ComUnit/진료파트/Finale/DETAIL"),
    (r"ComUnit/진료파트/Finale/", "ComUnit/진료파트/Finale (기타)"),
    (r"ComUnit/진료파트/OCS/", "ComUnit/진료파트/OCS"),
    (r"ComUnit/진료파트/_DupFiles/", "ComUnit/진료파트/_DupFiles"),
    (r"ComUnit/진료파트/Class/", "ComUnit/진료파트/Class"),
    (r"ComUnit/진료파트/Etc/", "ComUnit/진료파트/Etc"),
    (r"ComUnit/진료파트/", "ComUnit/진료파트 (기타)"),
    (r"ComUnit/접수파트/Class/", "ComUnit/접수파트/Class"),
    (r"ComUnit/접수파트/CashReceipt/", "ComUnit/접수파트/CashReceipt — 현금영수증"),
    (r"ComUnit/접수파트/Closing/", "ComUnit/접수파트/Closing — 마감"),
    (r"ComUnit/접수파트/Deposit/", "ComUnit/접수파트/Deposit — 예수금"),
    (r"ComUnit/접수파트/Discount/", "ComUnit/접수파트/Discount — 할인"),
    (r"ComUnit/접수파트/DisReg/", "ComUnit/접수파트/DisReg"),
    (r"ComUnit/접수파트/Boho/", "ComUnit/접수파트/Boho — 보험"),
    (r"ComUnit/접수파트/Address/", "ComUnit/접수파트/Address — 주소"),
    (r"ComUnit/접수파트/AssentDoc/", "ComUnit/접수파트/AssentDoc — 동의서"),
    (r"ComUnit/접수파트/AuthSuJinJa/", "ComUnit/접수파트/AuthSuJinJa — 수진자 인증"),
    (r"ComUnit/접수파트/Cert/", "ComUnit/접수파트/Cert — 인증서"),
    (r"ComUnit/접수파트/Certification/", "ComUnit/접수파트/Certification — 본인확인"),
    (r"ComUnit/접수파트/ChronicCntrl/", "ComUnit/접수파트/ChronicCntrl — 만성질환"),
    (r"ComUnit/접수파트/ActualExpenseInsurance/", "ComUnit/접수파트/실손보험"),
    (r"ComUnit/접수파트/DdocdocPayment/", "ComUnit/접수파트/똑닥 결제"),
    (r"ComUnit/접수파트/DdocdocMobilePaper/", "ComUnit/접수파트/똑닥 모바일증명서"),
    (r"ComUnit/접수파트/Etc/", "ComUnit/접수파트/Etc"),
    (r"ComUnit/접수파트/", "ComUnit/접수파트 (기타)"),
    (r"ComUnit/", "ComUnit (기타)"),
    (r"Module/AddOn/NCare_New/", "Module/AddOn/NCare_New — NCare SMS/알림톡"),
    (r"Module/AddOn/", "Module/AddOn — 부가기능 모듈"),
    (r"Module/Counter/", "Module/Counter — 접수 모듈"),
    (r"Module/Chart/", "Module/Chart — 진료 모듈"),
    (r"Module/Mobile/", "Module/Mobile — 모바일 모듈"),
    (r"Module/Tool/", "Module/Tool — 도구 모듈"),
    (r"Module/Support/", "Module/Support — 지원 모듈"),
    (r"Module/Interface/", "Module/Interface — 인터페이스 모듈"),
    (r"Module/", "Module — 다른 모듈"),
    (r"Projects/YsrExternalInterface/Ddocdoc/", "Projects/YsrExternalInterface/똑닥"),
    (r"Projects/YsrExternalInterface/YsrPortal/", "Projects/YsrExternalInterface/YsrPortal"),
    (r"Projects/YsrExternalInterface/", "Projects/YsrExternalInterface — 외부 연동"),
    (r"Projects/", "Projects (기타)"),
    (r"PackageBL/DBLOGInPacks/", "PackageBL/DBLOGInPacks — DB 접속"),
    (r"PackageBL/", "PackageBL — 비즈로직 패키지"),
    (r"PackageV7/", "PackageV7 — 서드파티 패키지"),
    (r"Interface/", "Interface — 인터페이스 모듈"),
]

# DCC_Define에서 RELEASE/DEBUG 토큰만 차이 나면 노이즈 — 비교 시 제거.
DEFINE_NOISE = {"RELEASE", "DEBUG"}


def _find_trunk_root(start: Path) -> Path | None:
    """`start`에서 부모로 올라가며 이름이 `trunk`인 디렉토리 탐색."""
    for parent in [start, *start.parents]:
        if parent.name.lower() == "trunk":
            return parent
    return None


def _find_module_root(dproj_path: Path) -> Path:
    """프로젝트 모듈 루트 — `.dproj`가 들어있는 `_D7` (또는 `_DXE` 등) 의 부모.

    EN-FwChart/_D7/FwChart.dproj  →  EN-FwChart/
    그 안에 있는 unit은 '로컬 소스'로 분류.
    """
    parent = dproj_path.parent
    if parent.name.startswith("_"):  # _D7, _DXE3 등
        return parent.parent
    return parent


def _resolve_reference(
    dproj_path: Path,
    include: str,
    trunk_root: Path | None,
    module_root: Path,
) -> tuple[str, bool, bool]:
    """DCCReference Include → (표시 경로, is_local, in_trunk).

    1) `.dproj` 기준 상대경로를 resolve해서 절대경로 얻음
    2) module_root 안쪽이면 is_local=True, 표시는 module_root 기준 상대
    3) trunk_root 안쪽이면 trunk 기준 상대 (forward-slash)
    4) trunk 밖이면 절대경로 그대로
    """
    raw_norm = include.replace("\\", "/")
    try:
        abs_path = (dproj_path.parent / raw_norm).resolve()
    except (OSError, ValueError):
        # resolve 실패 시 원본 사용 (선행 ../ 제거)
        p = raw_norm
        while p.startswith("../"):
            p = p[3:]
        return p, False, True

    try:
        rel_to_module = abs_path.relative_to(module_root)
        return rel_to_module.as_posix(), True, True
    except ValueError:
        pass

    if trunk_root:
        try:
            rel_to_trunk = abs_path.relative_to(trunk_root)
            return rel_to_trunk.as_posix(), False, True
        except ValueError:
            pass

    return abs_path.as_posix(), False, False


def _categorize(norm_path: str, is_local: bool, in_trunk: bool) -> str:
    if is_local:
        return "로컬 소스 (모듈 내부)"
    if not in_trunk:
        return "외부 (trunk 밖)"
    for prefix, label in CATEGORY_RULES:
        if norm_path.startswith(prefix):
            return label
    return "(미분류)"


# ---------------------------------------------------------------------------
# 파싱
# ---------------------------------------------------------------------------


def parse_dproj(dproj_path: Path) -> Project:
    tree = ET.parse(dproj_path)
    root = tree.getroot()

    project = Project(
        dproj_path=dproj_path,
        name=dproj_path.stem,
    )
    trunk_root = _find_trunk_root(dproj_path)
    module_root = _find_module_root(dproj_path)

    # PropertyGroup 순회
    for pg in root.findall(_qname("PropertyGroup")):
        cond = pg.get("Condition", "")

        # 루트 PropertyGroup (Condition 없음)
        if not cond:
            ms = pg.find(_qname("MainSource"))
            if ms is not None and ms.text:
                project.main_source = ms.text.strip()
            guid = pg.find(_qname("ProjectGuid"))
            if guid is not None and guid.text:
                project.project_guid = guid.text.strip()

        # Release / Debug 조건부
        is_release = "Release" in cond
        is_debug = "Debug" in cond

        if is_release or is_debug:
            define_el = pg.find(_qname("DCC_Define"))
            if define_el is not None and define_el.text:
                defines = [d.strip() for d in define_el.text.split(";") if d.strip()]
                if is_release:
                    project.defines_release = defines
                else:
                    project.defines_debug = defines

            if is_release:
                exe_el = pg.find(_qname("DCC_ExeOutput"))
                if exe_el is not None and exe_el.text:
                    project.exe_output = exe_el.text.strip()
                sp_el = pg.find(_qname("DCC_UnitSearchPath"))
                if sp_el is not None and sp_el.text:
                    project.search_paths = [
                        s.strip() for s in sp_el.text.split(";") if s.strip()
                    ]

    # VersionInfoKeys — ProjectExtensions 안 깊숙이 박혀 있음.
    # 네임스페이스 없는 inner XML이라 iter()로 전체 트리에서 찾아낸다.
    for el in root.iter():
        tag = _strip_ns(el.tag)
        if tag == "VersionInfoKeys" and el.get("Name"):
            project.version_info[el.get("Name")] = (el.text or "").strip()
        elif tag == "VersionInfo" and el.get("Name") == "CodePage":
            project.code_page = (el.text or "").strip()

    # DCCReference
    for ig in root.findall(_qname("ItemGroup")):
        for ref_el in ig.findall(_qname("DCCReference")):
            include = ref_el.get("Include", "")
            if not include or include.lower().endswith(".dpr"):
                # MainSource 자기 자신은 DelphiCompile 태그라서 여기 안 옴.
                # 혹시 모를 .dpr 참조는 스킵.
                continue
            norm, is_local, in_trunk = _resolve_reference(
                dproj_path, include, trunk_root, module_root
            )
            ref = Reference(
                raw_path=include,
                norm_path=norm,
                is_local=is_local,
                in_trunk=in_trunk,
            )
            form_el = ref_el.find(_qname("Form"))
            if form_el is not None and form_el.text:
                ref.form = form_el.text.strip()
            dc_el = ref_el.find(_qname("DesignClass"))
            if dc_el is not None and dc_el.text:
                ref.design_class = dc_el.text.strip()
            project.references.append(ref)

    return project


# ---------------------------------------------------------------------------
# 마크다운 출력
# ---------------------------------------------------------------------------


LOCAL_LABEL = "로컬 소스 (모듈 내부)"
EXTERNAL_LABEL = "외부 (trunk 밖)"


def _group_by_category(refs: list[Reference]) -> "OrderedDict[str, list[Reference]]":
    groups: dict[str, list[Reference]] = defaultdict(list)
    for ref in refs:
        groups[_categorize(ref.norm_path, ref.is_local, ref.in_trunk)].append(ref)

    # 표시 순서: 로컬 → trunk 카테고리 룰 순서 → 미분류 → trunk 밖
    ordered = OrderedDict()
    if LOCAL_LABEL in groups:
        ordered[LOCAL_LABEL] = sorted(groups[LOCAL_LABEL], key=lambda r: r.norm_path)
    for _, label in CATEGORY_RULES:
        if label in groups:
            ordered[label] = sorted(groups[label], key=lambda r: r.norm_path)
    if "(미분류)" in groups:
        ordered["(미분류)"] = sorted(groups["(미분류)"], key=lambda r: r.norm_path)
    if EXTERNAL_LABEL in groups:
        ordered[EXTERNAL_LABEL] = sorted(
            groups[EXTERNAL_LABEL], key=lambda r: r.norm_path
        )
    return ordered


def render_markdown(project: Project) -> str:
    lines: list[str] = []
    a = lines.append

    a(f"# {project.name} — 의존성 카드 (자동 생성)")
    a("")
    a("> 이 파일은 `.claude/scripts/parse_dproj.py`가 자동 생성한다.")
    a("> 직접 편집 금지 — 다음 실행에 덮어쓰임. 수기 보강은")
    a(f"> `{project.name}.notes.md`에 분리해서 작성.")
    a(">")
    a("> 출처: `.dproj`의 `<DCCReference>` 만 사용. `.dpr`의 uses 절에만 등장하고")
    a("> `.dproj`에 등록되지 않은 unit(빌드 제외 파일 등)은 누락될 수 있음.")
    a("")

    # ── 헤더 메타 ────────────────────────────────────────────────
    a("## 기본 정보")
    a("")
    if project.version_info.get("FileDescription"):
        a(f"- **설명**: {project.version_info['FileDescription']}")
    if project.version_info.get("FileVersion"):
        a(f"- **버전**: {project.version_info['FileVersion']}")
    if project.version_info.get("CompanyName"):
        a(f"- **회사**: {project.version_info['CompanyName']}")
    if project.code_page:
        a(f"- **코드페이지**: {project.code_page}")
    if project.main_source:
        a(f"- **진입점**: `{project.main_source}`")
    if project.exe_output:
        a(f"- **EXE 출력**: `{project.exe_output}`")
    if project.project_guid:
        a(f"- **GUID**: `{project.project_guid}`")
    a(f"- **dproj**: `{project.dproj_path.as_posix()}`")
    a("")

    # ── 컴파일 조건부 정의 ───────────────────────────────────────
    a("## 컴파일 조건부 정의")
    a("")
    if project.defines_release:
        a("**Release**")
        a("")
        a("```")
        a(";".join(project.defines_release))
        a("```")
        a("")
    if project.defines_debug:
        a("**Debug**")
        a("")
        a("```")
        a(";".join(project.defines_debug))
        a("```")
        a("")

    # Release - Debug 차이 표시 (RELEASE/DEBUG 토큰 자체는 노이즈라 제외)
    if project.defines_release and project.defines_debug:
        rel = set(project.defines_release) - DEFINE_NOISE
        dbg = set(project.defines_debug) - DEFINE_NOISE
        only_rel = sorted(rel - dbg)
        only_dbg = sorted(dbg - rel)
        if only_rel or only_dbg:
            a("**실질 차이**")
            a("")
            if only_rel:
                a(f"- Release 전용: `{', '.join(only_rel)}`")
            if only_dbg:
                a(f"- Debug 전용: `{', '.join(only_dbg)}`")
            a("")

    # ── 외부 의존성 ──────────────────────────────────────────────
    grouped = _group_by_category(project.references)
    total = len(project.references)

    a(f"## 외부 의존성 ({total}개)")
    a("")
    a("카테고리별 그루핑. 각 unit은 `.dproj`의 `<DCCReference>`에서 추출.")
    a("폼/데이터모듈은 옆에 `[FormName]`, `TDataModule` 등으로 표시.")
    a("")

    # 요약 표
    a("| 카테고리 | 개수 |")
    a("| --- | ---: |")
    for label, refs in grouped.items():
        a(f"| {label} | {len(refs)} |")
    a(f"| **합계** | **{total}** |")
    a("")

    # 상세
    a("### 상세 목록")
    a("")
    for label, refs in grouped.items():
        a(f"<details>")
        a(f"<summary><b>{label}</b> — {len(refs)}개</summary>")
        a("")
        for ref in refs:
            unit_name = Path(ref.norm_path).stem
            extras = []
            if ref.form:
                extras.append(f"`[{ref.form}]`")
            if ref.design_class:
                extras.append(f"`{ref.design_class}`")
            suffix = " " + " ".join(extras) if extras else ""
            a(f"- `{unit_name}` — `{ref.norm_path}`{suffix}")
        a("")
        a("</details>")
        a("")

    # ── Search Path ───────────────────────────────────────────────
    if project.search_paths:
        a("## DCC_UnitSearchPath (Release)")
        a("")
        for sp in project.search_paths:
            a(f"- `{sp}`")
        a("")

    return "\n".join(lines).rstrip() + "\n"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def find_all_dprojs(root: Path) -> list[Path]:
    """`trunk/` 하위의 모든 `.dproj` 검색."""
    return sorted(root.rglob("*.dproj"))


def resolve_card_names(dproj_paths: Iterable[Path]) -> dict[Path, str]:
    """dproj 경로 리스트 → 충돌 없는 카드 이름 매핑.

    같은 stem(파일명)이 여러 위치에 있으면 모듈 디렉토리명을 prefix로 붙여 구별한다.
    예: `Foo/_D7/X.dproj` + `Bar/_D11/X.dproj` → `Foo__X`, `Bar__X`.
    """
    by_stem: dict[str, list[Path]] = defaultdict(list)
    for p in dproj_paths:
        by_stem[p.stem].append(p)

    result: dict[Path, str] = {}
    for stem, paths in by_stem.items():
        if len(paths) == 1:
            result[paths[0]] = stem
            continue
        # 충돌 — 모듈 디렉토리(._D7 등 컴파일 폴더의 부모) 이름으로 구별
        # 그래도 같으면 한 단계 더 올라간 디렉토리를 prefix에 누적
        for p in paths:
            module_parent = p.parent
            if module_parent.name.startswith("_"):
                module_parent = module_parent.parent
            prefix = module_parent.name
            result[p] = f"{prefix}__{stem}"
        # 그래도 같은 이름이 남으면 한 단계 더 추가
        used: dict[str, list[Path]] = defaultdict(list)
        for p in paths:
            used[result[p]].append(p)
        for name, group in used.items():
            if len(group) > 1:
                for p in group:
                    module_parent = p.parent
                    if module_parent.name.startswith("_"):
                        module_parent = module_parent.parent
                    grandparent = module_parent.parent.name
                    result[p] = f"{grandparent}__{name}"
    return result


def write_card(project: Project, out_dir: Path, card_name: str | None = None) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    name = card_name or project.name
    out_path = out_dir / f"{name}.generated.md"
    out_path.write_text(render_markdown(project), encoding="utf-8")
    return out_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=".dproj → 의존성 카드 (.claude/projects/*.generated.md)"
    )
    parser.add_argument(
        "dproj",
        nargs="*",
        type=Path,
        help=".dproj 파일 경로 (1개 이상). --all과 함께 쓰면 무시됨.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help=f"trunk/ 전체에서 .dproj 자동 검색 (루트: {TRUNK_ROOT})",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=PROJECTS_DIR,
        help=f"출력 디렉토리 (기본: {PROJECTS_DIR})",
    )
    args = parser.parse_args(argv)

    if args.all:
        targets = find_all_dprojs(TRUNK_ROOT)
        if not targets:
            print(f"[!] {TRUNK_ROOT} 하위에 .dproj 없음", file=sys.stderr)
            return 1
    else:
        if not args.dproj:
            parser.error("dproj 경로 또는 --all 필요")
        targets = args.dproj

    # 카드 이름 충돌 회피 — 동일 stem이 여러 dproj 경로에 있으면 prefix 추가
    name_map = resolve_card_names(targets)

    written: list[Path] = []
    for dproj in targets:
        if not dproj.exists():
            print(f"[!] 없음: {dproj}", file=sys.stderr)
            continue
        try:
            project = parse_dproj(dproj)
        except ET.ParseError as e:
            print(f"[!] XML 파싱 실패: {dproj} — {e}", file=sys.stderr)
            continue
        card_name = name_map.get(dproj, project.name)
        out = write_card(project, args.out, card_name=card_name)
        written.append(out)
        # 화면 출력에서 경로 표시는 카드 파일 자체 경로
        try:
            disp = out.relative_to(out.parent.parent.parent)
        except ValueError:
            disp = out
        print(f"[ok] {dproj.name} -> {disp}  ({len(project.references)} refs)")

    print(f"\n총 {len(written)}개 카드 생성됨.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
