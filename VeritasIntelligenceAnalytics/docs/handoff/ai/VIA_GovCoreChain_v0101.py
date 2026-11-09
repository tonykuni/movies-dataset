#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_GovCoreChain v0101 — 薄尾:治理件彼此的載入也進矩陣 · 本支自身與暫存夾具字串不算載入者(Codex PR 616 P2 · PR 617 P1 / P2)

v0100 已併進 main(PR 616)且有鎖住的 C-govcorechain-v0100 收據 → 不就地改,出薄尾(版本律;PR 617 P1 判得對,這是同一個錯第二次)。
兩個修正(換裝在位 BASE.scan_loaders / BASE.scan_writers,本體 build() 讀模組全域 → 換裝即生效;v0100 一字不動):
  ① 治理件彼此的載入要算:v0100 對六個治理件一律 continue,把 10_Core_Runtime 橋(v018 canonical adapter)以
     spec_from_file_location 指名 20_Registry_SSOT/VIA_RegistryCore_v1 · VIA_SSOT_Unified 的那條邊丟了,編號夾那份 RegistryCore
     被誤判「無獨佔載入者可退」(相依保留律 AGENTS.md L13)。本版照掃,只排除「對自己家族的引用」(檔名 / 版史 / 說明字串)。
  ② 本支自身(VIA_GovCoreChain_v*)與暫存夾具字串不算載入者:v0100 把自己自測夾具裡的路徑字串與 endswith 斷言算成
     20_Registry_SSOT/RegistryCore 的 PATH_LITERAL HIGH 載入者(PR 617 P2)。本版:自身家族整支排除;
     所在函式用 tempfile 的字串列為 FIXTURE 另列(loader_rows_fixture),不進任何副本的載入者計數。
輸出改寫到 VIA_GovCoreChain_v0101.json / .md / VIA_GovCoreChain_UI_v0101.html(v0100 的三個輸出不動)。唯讀 · 零網路。
"""

from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None
# ===== [VIA:NET-BRIDGE:END] =====

import ast
import importlib.util
import json
import re
import sys
import warnings
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = Path(__file__).stem
_STEM = "VIA_GovCoreChain"
SELF_RX = re.compile(r"^VIA_GovCoreChain_v\d{4}$")


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + ENGINE, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR
while "PRIOR" in vars(BASE):
    BASE = vars(BASE)["PRIOR"]
_V0100_LOADERS, _V0100_WRITERS, _V0100_BUILD = BASE.scan_loaders, BASE.scan_writers, BASE.build
FAMILIES = BASE.FAMILIES
FIXTURE_ROWS: list = []                                  # 最近一次 scan_loaders 另列出來的夾具字串(不計數)


def _is_fixture(node, par, src) -> bool:
    fn_node = BASE._enclosing_func(node, par)
    seg = ast.get_source_segment(src, fn_node) or ""
    return "tempfile." in seg or "mkdtemp" in seg or "TemporaryDirectory" in seg


def scan_loaders(root: Path, copies_by_family: dict) -> list:
    """v0100 的掃法 + ① 治理件照掃(只排除同家族自我引用)② 自身家族與夾具字串不算。"""
    rows = []
    FIXTURE_ROWS.clear()
    fam_copies_paths = {f: {c["path"] for c in cs} for f, cs in copies_by_family.items()}
    for p in BASE.active_py(root):
        if SELF_RX.match(p.stem):
            continue                                    # ② 本支(含前版 / 後版)自身:自測夾具字串與斷言不是載入者
        r = p.resolve().relative_to(root.resolve()).as_posix()
        self_fam = BASE.family_of(p.stem)               # ① 治理件照掃;自家族引用排除
        try:
            src = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if not any(f in src for f in FAMILIES if f != self_fam):
            continue
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                tree = ast.parse(src)
        except SyntaxError:
            continue
        par = BASE._parents(tree)
        has_bridge = "VIA:ACCEL-BRIDGE" in src
        inserts_root = "supportive modules" in src and "sys.path" in src
        hits = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    fam = BASE.family_of(a.name.split(".")[0])
                    if fam:
                        hits.append((fam, "IMPORT", "flat-or-lock", node, a.name))
            elif isinstance(node, ast.ImportFrom) and node.module:
                fam = BASE.family_of(node.module.split(".")[0])
                if fam:
                    hits.append((fam, "IMPORT", "flat-or-lock", node, node.module))
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                v = node.value
                for fam in FAMILIES:
                    if fam in v:
                        if v.endswith(".py") or "/" in v or "\\" in v:
                            segs, rel_file = BASE._path_chain(node, par)
                            layout, how = BASE.classify_literal(segs, rel_file, fam)
                            hits.append((fam, how, layout, node, v[:120]))
                        elif v == fam or v == fam + ".py":
                            hits.append((fam, "NAME_ONLY", "name-only", node, v))
                        break
        for fam, how, layout, node, text in hits:
            if fam == self_fam:
                continue
            resolved, conf = BASE.resolve(fam, how, layout, r, has_bridge or inserts_root, fam_copies_paths[fam])
            row = {"loader": r, "lane": BASE.lane_of(r), "family": fam, "how": how, "layout": layout, "line": node.lineno,
                   "text": text, "resolved": resolved, "confidence": conf, "bridge": has_bridge}
            if how != "IMPORT" and _is_fixture(node, par, src):
                row["scope"] = "FIXTURE(暫存夾)"
                FIXTURE_ROWS.append(row)                # 另列,不計數
            else:
                row["scope"] = "TREE"
                rows.append(row)
    return rows


def scan_writers(root: Path) -> list:
    """v0100 的寫入者掃法,但治理件照掃(排除自家族)、本支自身排除。"""
    rows = []
    for p in BASE.active_py(root):
        if SELF_RX.match(p.stem):
            continue
        r = p.resolve().relative_to(root.resolve()).as_posix()
        self_fam = BASE.family_of(p.stem)
        try:
            src = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if not any(f in src for f in FAMILIES if f != self_fam):
            continue
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                tree = ast.parse(src)
        except SyntaxError:
            continue
        par = BASE._parents(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            fn = node.func
            name = fn.id if isinstance(fn, ast.Name) else (fn.attr if isinstance(fn, ast.Attribute) else "")
            if name == "open":
                path_nodes = node.args[:1]
            elif isinstance(fn, ast.Attribute) and name in BASE.WRITE_ATTRS:
                path_nodes = [fn.value] + (list(node.args) if name in {"rename", "replace", "copy", "copy2", "copyfile", "move", "rmtree"} else [])
            else:
                continue
            strs = [s_ for pn in path_nodes for s_ in BASE._strings_under(pn)]
            fams = sorted({f for f in FAMILIES for s_ in strs if BASE.TARGET_RX[f].search(s_) and f != self_fam})
            if not fams:
                continue
            fixture = _is_fixture(node, par, src)
            kind = None
            if name == "open":
                mode = None
                if len(node.args) > 1 and isinstance(node.args[1], ast.Constant):
                    mode = str(node.args[1].value)
                for kw in node.keywords:
                    if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                        mode = str(kw.value.value)
                if mode and BASE.WRITE_MODES.match(mode):
                    kind = f"open(mode={mode})"
            else:
                kind = f".{name}()"
            if kind:
                fn_node = BASE._enclosing_func(node, par)
                rows.append({"writer": r, "lane": BASE.lane_of(r), "families": fams, "call": kind, "line": node.lineno, "scope": "FIXTURE(暫存夾)" if fixture else "TREE",
                             "func": getattr(fn_node, "name", "<module>"), "injector_name": bool(BASE.INJECTOR_NAME_RX.search(p.stem)), "gated_apply": "--apply" in src})
    return rows


def build(root: Path) -> dict:
    D = _V0100_BUILD(root)
    D["engine"] = ENGINE
    D["prior"] = "VIA_GovCoreChain_v0100.json"
    D["loader_rows_fixture"] = list(FIXTURE_ROWS)
    D["why_v0101"] = ("治理件彼此的載入進矩陣(排除同家族自我引用);本支自身與 tempfile 夾具字串不計數(另列 loader_rows_fixture)。"
                      "Codex PR 616 P2 · PR 617 P1 / P2;v0100 與其輸出、收據一字不動。")
    return D


BASE.scan_loaders = scan_loaders
BASE.scan_writers = scan_writers
BASE.build = build
BASE.OUT_JSON = HERE / "VIA_GovCoreChain_v0101.json"
BASE.OUT_MD = HERE / "VIA_GovCoreChain_v0101.md"
BASE.OUT_UI = HERE / "VIA_GovCoreChain_UI_v0101.html"
OUT_JSON, OUT_MD, OUT_UI = BASE.OUT_JSON, BASE.OUT_MD, BASE.OUT_UI


def __getattr__(name: str):
    return getattr(PRIOR, name)


def selftest() -> int:
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:260]) if note and not cond else ''}")

    print(f"=== {ENGINE} · 薄尾自測(治理件互載 · 自身 / 夾具不計數)===")
    chk("① 換裝在位:本體 scan_loaders / scan_writers / build 都是本版;輸出改指 v0101;v0100 檔在位且沒被動(有 PRIOR)",
        BASE.scan_loaders is scan_loaders and BASE.scan_writers is scan_writers and BASE.build is build and BASE.OUT_JSON.name == "VIA_GovCoreChain_v0101.json" and PRIOR_PATH.stem == "VIA_GovCoreChain_v0100")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        sm = root / "supportive modules"
        for d in ("20_Registry_SSOT", "10_Core_Runtime", "network"):
            (sm / d).mkdir(parents=True)
        (root / "functional modules" / "VRN").mkdir(parents=True)
        (root / "docs" / "handoff" / "ai").mkdir(parents=True)
        (sm / "VIA_RegistryCore_v1.py").write_text("R = 1\n", encoding="utf-8")
        (sm / "20_Registry_SSOT" / "VIA_RegistryCore_v1.py").write_text("R = 1\n", encoding="utf-8")
        (sm / "VIA_Runtime_Bridge_All_in_One.py").write_text("X = 1\n", encoding="utf-8")
        (sm / "10_Core_Runtime" / "VIA_Runtime_Bridge_All_in_One.py").write_text(
            "X = 1\nimport importlib.util\nfrom pathlib import Path\nME = 'VIA_Runtime_Bridge_All_in_One'\n"
            "P = Path(__file__).resolve().parent.parent / '20_Registry_SSOT' / 'VIA_RegistryCore_v1.py'\n"
            "spec = importlib.util.spec_from_file_location('VIA_RegistryCore_v1', str(P))\n", encoding="utf-8")
        (sm / "network" / "VeritasAegisNexus_v1652.py").write_text("N = 2\n", encoding="utf-8")
        (root / "docs" / "handoff" / "ai" / "VIA_GovCoreChain_v0100.py").write_text(
            "P = 'supportive modules/20_Registry_SSOT/VIA_RegistryCore_v1.py'\nassert P.endswith('20_Registry_SSOT/VIA_RegistryCore_v1.py')\n", encoding="utf-8")
        (root / "functional modules" / "VRN" / "VRN_T.py").write_text(
            "from pathlib import Path\ndef selftest():\n    import tempfile\n    t = Path(tempfile.mkdtemp())\n    (t / 'supportive modules' / '20_Registry_SSOT' / 'VIA_RegistryCore_v1.py').write_text('x')\n"
            "Q = 'supportive modules/20_Registry_SSOT/VIA_RegistryCore_v1.py'\n", encoding="utf-8")
        D = build(root)
        rc_ = D["families"]["VIA_RegistryCore_v1"]
        numbered = next(c for c in rc_["copies"] if "20_Registry_SSOT" in c["path"])
        edge = [lr for lr in D["loader_rows"] if lr["family"] == "VIA_RegistryCore_v1" and lr["loader"].endswith("10_Core_Runtime/VIA_Runtime_Bridge_All_in_One.py")]
        chk("② 跨家族邊:10_Core_Runtime 橋以 BinOp 路徑載 20_Registry_SSOT/RegistryCore → PATH_LITERAL numbered HIGH,算進該副本",
            edge and edge[0]["how"] == "PATH_LITERAL" and edge[0]["confidence"] == "HIGH" and edge[0]["resolved"].endswith("20_Registry_SSOT/VIA_RegistryCore_v1.py"), edge)
        chk("③ 自我引用不算:橋裡 ME = 'VIA_Runtime_Bridge_All_in_One' 沒變成 Runtime_Bridge 的載入者",
            not any(lr["family"] == "VIA_Runtime_Bridge_All_in_One" and "10_Core_Runtime" in lr["loader"] for lr in D["loader_rows"]))
        chk("④ 本支自身排除:docs/handoff/ai/VIA_GovCoreChain_v0100.py 的夾具字串與 endswith 斷言不是載入者",
            not any("VIA_GovCoreChain" in lr["loader"] for lr in D["loader_rows"] + D["loader_rows_fixture"]))
        fx = [lr for lr in D["loader_rows_fixture"] if lr["loader"].endswith("VRN_T.py")]
        tr = [lr for lr in D["loader_rows"] if lr["loader"].endswith("VRN_T.py")]
        chk("⑤ 夾具字串另列不計數:VRN_T.selftest 裡 tempfile 夾具的路徑 → FIXTURE;模組層那條 Q 字串 → TREE(算 1)",
            len(fx) == 1 and fx[0]["scope"].startswith("FIXTURE") and len(tr) == 1 and tr[0]["scope"] == "TREE", (fx, tr))
        chk("⑥ 副本計數:20_Registry_SSOT/RegistryCore 載入者 = 2(橋 1 + VRN_T 模組層 1),夾具與自身都沒灌進去",
            numbered["loader_total"] == 2 and numbered["loaders"] == {"PATH_LITERAL": 2}, numbered)
        chk("⑦ 輸出:engine / prior / why_v0101 / loader_rows_fixture 都在;to_md / to_ui 吃得下(無骨架標籤 · title 在頂)",
            D["engine"] == ENGINE and D["prior"] == "VIA_GovCoreChain_v0100.json" and "loader_rows_fixture" in D
            and BASE.to_ui(D).startswith("<title>") and not re.search(r"<(!doctype|html|body)", BASE.to_ui(D), re.I) and "## " in BASE.to_md(D))
    try:
        real = build(BASE.VIA)
        crashed = ""
    except Exception as exc:  # noqa: BLE001
        crashed, real = repr(exc), {}
    rcn = None if crashed else next(c for c in real["families"]["VIA_RegistryCore_v1"]["copies"] if "20_Registry_SSOT" in c["path"])
    bridge_rows = [] if crashed else [lr for lr in real["loader_rows"] if lr["family"] == "VIA_RegistryCore_v1" and lr["resolved"] == rcn["path"]]
    chk("⑧ 實樹:20_Registry_SSOT/RegistryCore 的載入者只剩 10_Core_Runtime 橋(1 筆 · TREE);沒有 GovCoreChain 自身、沒有夾具",
        not crashed and rcn["loader_total"] == 1 and len(bridge_rows) == 1 and bridge_rows[0]["loader"].endswith("10_Core_Runtime/VIA_Runtime_Bridge_All_in_One.py")
        and not any("VIA_GovCoreChain" in lr["loader"] for lr in real["loader_rows"]), crashed or (rcn, [(b["loader"], b["scope"]) for b in bridge_rows]))
    chk("⑨ 實樹:改動權 GREEN(樹上寫入者 0)· 六家族燈與正本候選不變(Runtime Bridge → 10_Core_Runtime · SSOT_Unified → ssot/ · AegisNexus → _v1652)",
        not crashed and real["mutation_rights"]["lamp"] == "GREEN" and real["mutation_rights"]["tree_writers"] == 0
        and any("正本候選" in c["advice"] and "10_Core_Runtime" in c["path"] for c in real["families"]["VIA_Runtime_Bridge_All_in_One"]["copies"])
        and any("正本候選" in c["advice"] and "ssot/" in c["path"] for c in real["families"]["VIA_SSOT_Unified"]["copies"])
        and any(c.get("is_tail") and c["vnum"] == 1652 for c in real["families"]["VeritasAegisNexus"]["copies"]), crashed or real.get("lamp"))
    src = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    subproc = any(isinstance(n, (ast.Import, ast.ImportFrom)) and any((x.name or "").split(".")[0] == "sub" + "process" for x in n.names) for n in ast.walk(tree))
    chk("⑩ 紀律:加速器橋 · 網路橋在;不碰 TA-Lib;不派子行程;v0100 檔位元沒被本版動(本版只換裝模組屬性)",
        "VIA:ACCEL-BRIDGE" in src and "VIA:NET-BRIDGE" in src and not re.search(r"^\s*(import|from)\s+talib", src, re.M) and not subproc
        and "self_fam" not in PRIOR_PATH.read_text(encoding="utf-8"))
    print(f"  [計] {ENGINE} 薄尾 OK {sum(ok)} · FAIL {len(ok) - sum(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    prc = PRIOR.selftest()
    print(f"  [計] 前版鏈 v0100 自測 rc {prc}")
    return 0 if all(ok) and prc == 0 else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        return selftest()
    if args and args[0] == "run":
        return BASE.run("--apply" in args)
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
