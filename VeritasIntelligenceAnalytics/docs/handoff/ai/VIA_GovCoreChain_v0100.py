#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_GovCoreChain v0100 — 治理核心相依鏈驗證矩陣(RC-1 W2 第一項;唯讀 · AST · 不改任何檔 · 零網路)

操作員 2026-11-09:「繼續 W2 桌機項,先出治理核心相依鏈驗證矩陣」。
RC-1 W0 判 Hydra RED:治理核心(VIA_EnvManager · VIA_RegistryCore_v1 · VIA_Panorama_AST_RuntimeInjector ·
VIA_Runtime_Bridge_All_in_One · VIA_SSOT_Unified · VeritasAegisNexus)各 3 份、AegisNexus 8 份在活目錄。
W1 試過「位元相同的副本換轉接殼」,Codex #615 P1 判就地覆寫已發布檔違版本律 → 撤回。
正解要先回答三個問題,這支就只回答這三個問題(不動手):
  ① 每個治理件有幾份副本、哪些位元相同、哪些是另一份的超集(append-only 加了塊)、哪些真的分岔;
  ② 誰載它、怎麼載(裸 import 經 sys.path · 字面路徑 · 以名字 + 搜尋夾動態找)、靜態推得出會落到哪一份 —— 治理件彼此的載入也算(只排除同家族自我引用);
  ③ 據此給每一份一個建議:正本候選 / 可退(沒有獨佔載入者)/ 遷呼叫者後再退 / 要操作員裁(分岔)。
解法不在這支裡 —— 殼 / 版本化轉接件 / _superseded 是 W2 操作員裁完才做的事。
三種目錄慣例並存是多頭的根因:平鋪根(supportive modules/X.py)· 編號夾(10_Core_Runtime … 50_Protection_Acceleration)·
主題夾(environment · registry · audit_tools · runtime_bridge · ssot · network);每一種各有自己的載入器。

動詞:run [--apply](寫 docs/handoff/ai/VIA_GovCoreChain_v0100.json · .md · VIA_GovCoreChain_UI.html;不帶 --apply 只印)· --selftest
解析是靜態估計(sys.path 在執行期可被改),矩陣逐列標 how 與 confidence,不冒充執行期事實。
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
import datetime as _dt
import warnings
import hashlib
import html
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent.parent                        # VeritasIntelligenceAnalytics
ENGINE = Path(__file__).stem
OUT_JSON = HERE / "VIA_GovCoreChain_v0100.json"
OUT_MD = HERE / "VIA_GovCoreChain_v0100.md"
OUT_UI = HERE / "VIA_GovCoreChain_UI.html"

FAMILIES = ("VIA_EnvManager", "VIA_RegistryCore_v1", "VIA_Panorama_AST_RuntimeInjector",
            "VIA_Runtime_Bridge_All_in_One", "VIA_SSOT_Unified", "VeritasAegisNexus")
# 凍結 / 鏡像 / 分身:不算活目錄(RC-1 出貨範圍律;_sha 分身是 CONFLICT-00005,另冊)
SKIP_RX = re.compile(r"VIA_RetiredEngines|_review_quarantine|references[/\\]intake|[/\\]\.git[/\\]|__pycache__|SCOPE_COPY|new modules engines|Standalone|_sha[0-9a-f]{8}")
NUMBERED_RX = re.compile(r"^\d\d_")
LAYOUT_NAMES = {"environment", "registry", "audit_tools", "runtime_bridge", "ssot", "network", "accelerator"}
TAIL_RX = re.compile(r"_v(\d{4})$")


def rel(p: Path) -> str:
    try:
        return p.resolve().relative_to(VIA.resolve()).as_posix()
    except ValueError:
        return p.as_posix()


def lane_of(relpath: str) -> str:
    s = "/" + relpath
    if "/functional modules/VDF/" in s:
        return "VDF"
    if "/functional modules/VRN/" in s:
        return "VRN"
    if "/functional modules/VQG/" in s:
        return "VQG"
    if "/functional modules/VAP/" in s:
        return "VAP"
    if "/supportive modules/registry/" in s or "/docs/handoff/" in s:
        return "VCGC"
    if "/supportive modules/" in s:
        return "SUP"
    return "CORE"


def layout_of(relpath: str) -> str:
    """副本落在哪種目錄慣例:flat(supportive modules 根)· numbered(10_…50_)· topic(environment/ssot/network…)· root(VIA 根)· other。"""
    parts = relpath.split("/")
    if len(parts) == 1:
        return "root"
    if parts[0] != "supportive modules":
        return "other"
    if len(parts) == 2:
        return "flat"
    d = parts[1]
    if NUMBERED_RX.match(d):
        return "numbered"
    if d in LAYOUT_NAMES:
        return "topic"
    return "other"


def family_of(stem: str):
    base = TAIL_RX.sub("", stem)
    return base if base in FAMILIES else None


def sha8(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()[:8]


def active_py(root: Path):
    for p in root.rglob("*.py"):
        if not SKIP_RX.search(p.as_posix()):
            yield p


# ------------------------------------------------------------------ ① 副本
def scan_copies(root: Path) -> dict:
    fams = {f: [] for f in FAMILIES}
    for p in active_py(root):
        fam = family_of(p.stem)
        if not fam:
            continue
        b = p.read_bytes()
        m = TAIL_RX.search(p.stem)
        r = p.resolve().relative_to(root.resolve()).as_posix()
        fams[fam].append({"path": r, "sha8": sha8(b), "bytes": len(b), "lines": b.count(b"\n"), "layout": layout_of(r),
                          "versioned": bool(m), "vnum": int(m.group(1)) if m else None, "lane": lane_of(r)})
    for fam, rows in fams.items():
        rows.sort(key=lambda x: (x["versioned"], x["vnum"] or 0, x["path"]))
        groups = defaultdict(list)
        for c in rows:
            groups[c["sha8"]].append(c["path"])
        for c in rows:
            c["group"] = sorted(groups).index(c["sha8"]) + 1
            c["identical_to"] = [q for q in groups[c["sha8"]] if q != c["path"]]
        vers = [c for c in rows if c["versioned"]]
        if vers:
            tail = max(vers, key=lambda c: c["vnum"])
            tail["is_tail"] = True
    return fams


def superset_relations(root: Path, copies: list) -> list:
    """同家族、內容不同的兩份:A 的每一行都在 B 裡(多重集合)→ B 是 A 的超集(append-only 加塊)。"""
    rels = []
    texts = {}
    for c in copies:
        if c["versioned"]:
            continue
        try:
            texts[c["path"]] = (root / c["path"]).read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            pass
    paths = list(texts)
    for i, a in enumerate(paths):
        for b in paths[i + 1:]:
            if sha8((root / a).read_bytes()) == sha8((root / b).read_bytes()):
                continue
            ca, cb = Counter(texts[a]), Counter(texts[b])
            only_a = sum((ca - cb).values())
            only_b = sum((cb - ca).values())
            if only_a == 0 and only_b > 0:
                rels.append({"subset": a, "superset": b, "added_lines": only_b, "kind": "SUPERSET"})
            elif only_b == 0 and only_a > 0:
                rels.append({"subset": b, "superset": a, "added_lines": only_a, "kind": "SUPERSET"})
            else:
                rels.append({"a": a, "b": b, "only_a": only_a, "only_b": only_b, "kind": "DIVERGED"})
    return rels


# ------------------------------------------------------------------ ② 載入器
def _parents(tree: ast.AST) -> dict:
    par = {}
    for node in ast.walk(tree):
        for ch in ast.iter_child_nodes(node):
            par[ch] = node
    return par


def _path_chain(node: ast.AST, par: dict):
    """字串常數往上爬 BinOp(/) 鏈,收齊鏈裡所有字串常數與 __file__ 相對記號。"""
    top = node
    while isinstance(par.get(top), ast.BinOp) and isinstance(par[top].op, ast.Div):
        top = par[top]
    segs, rel_file = [], False
    for n in ast.walk(top):
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            segs.append(n.value)
        if isinstance(n, ast.Name) and n.id == "__file__":
            rel_file = True
    return segs, rel_file


def classify_literal(segs: list, rel_file: bool, fam: str) -> tuple:
    """字面路徑 → (layout 推定, how)。"""
    joined = "/".join(s.replace("\\", "/") for s in segs)
    if re.search(r"^[A-Za-z]:/|OneDrive|Downloads|/Users/", joined):
        return "desktop", "PATH_DESKTOP"
    for s in segs:
        for part in s.replace("\\", "/").split("/"):
            if NUMBERED_RX.match(part):
                return "numbered", "PATH_LITERAL"
            if part in LAYOUT_NAMES:
                return "topic", "PATH_LITERAL"
    if "supportive modules" in joined or "supportive_module" in joined:
        return "flat", "PATH_LITERAL"
    if rel_file:
        return "relative", "PATH_RELATIVE"
    return "name-only", "NAME_ONLY"


def scan_loaders(root: Path, copies_by_family: dict) -> list:
    """每個活 .py 對六家族的引用:IMPORT(裸 import)· PATH_*(字面路徑)· NAME_ONLY(只給檔名 / 名字,交給搜尋夾)。"""
    rows = []
    fam_copies_paths = {f: {c["path"] for c in cs} for f, cs in copies_by_family.items()}
    for p in active_py(root):
        r = p.resolve().relative_to(root.resolve()).as_posix()
        self_fam = family_of(p.stem)                    # 治理件也要掃:它們彼此會載(10_Core_Runtime 橋 → 20_Registry_SSOT 兩份);只排除對自己家族的引用(Codex PR 616 P2)
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
        par = _parents(tree)
        has_bridge = "VIA:ACCEL-BRIDGE" in src
        inserts_root = "supportive modules" in src and "sys.path" in src
        hits = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    fam = family_of(a.name.split(".")[0])
                    if fam:
                        hits.append((fam, "IMPORT", "flat-or-lock", node.lineno, a.name))
            elif isinstance(node, ast.ImportFrom) and node.module:
                fam = family_of(node.module.split(".")[0])
                if fam:
                    hits.append((fam, "IMPORT", "flat-or-lock", node.lineno, node.module))
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                v = node.value
                for fam in FAMILIES:
                    if fam in v:
                        if v.endswith(".py") or "/" in v or "\\" in v:
                            segs, rel_file = _path_chain(node, par)
                            layout, how = classify_literal(segs, rel_file, fam)
                            hits.append((fam, how, layout, node.lineno, v[:120]))
                        elif v == fam or v == fam + ".py":
                            hits.append((fam, "NAME_ONLY", "name-only", node.lineno, v))
                        break
        for fam, how, layout, line, text in hits:
            if fam == self_fam:
                continue                                # 自我引用(檔名 / 版史 / 說明字串)不算載入者
            resolved, conf = resolve(fam, how, layout, r, has_bridge or inserts_root, fam_copies_paths[fam])
            rows.append({"loader": r, "lane": lane_of(r), "family": fam, "how": how, "layout": layout, "line": line,
                         "text": text, "resolved": resolved, "confidence": conf, "bridge": has_bridge})
    return rows


def resolve(fam: str, how: str, layout: str, loader: str, root_on_path: bool, copies: set) -> tuple:
    """靜態推定會落到哪一份。回 (路徑或說明, 信心)。"""
    flat = f"supportive modules/{fam}.py"
    same_dir = loader.rsplit("/", 1)[0] + f"/{fam}.py" if "/" in loader else f"{fam}.py"
    if how == "IMPORT":
        if fam == "VeritasAegisNexus":
            return "supportive modules/network/VeritasAegisNexus_v1652.py(鎖冊尾版;SUP_MDL737 v0110 把 import VeritasAegisNexus 接到鎖冊工具)" if root_on_path else same_dir, "MEDIUM"
        if same_dir in copies:
            return same_dir, "HIGH"
        if root_on_path and flat in copies:
            return flat, "HIGH"
        return flat if flat in copies else "(sys.path 不含任何副本:執行期 ImportError 或靠呼叫者先插路徑)", "LOW"
    if how == "PATH_DESKTOP":
        return "(桌機絕對路徑:倉內無此檔;只在桌機有意義)", "N/A"
    if how == "PATH_LITERAL":
        cands = [c for c in copies if layout_of(c) == layout]
        return (cands[0] if len(cands) == 1 else (" | ".join(sorted(cands)) if cands else f"(字面指 {layout} 夾,倉內無該夾副本)")), ("HIGH" if len(cands) == 1 else "MEDIUM")
    if how == "PATH_RELATIVE":
        return same_dir if same_dir in copies else "(相對 __file__ 組路徑;該夾無副本)", "MEDIUM"
    return "(只給名字;落點由呼叫者的搜尋夾決定 —— VRN 插件載入器用 ssot_dir 與其上層,桌機設定值)", "LOW"



# ------------------------------------------------------------------ ②b 改動權:誰會寫治理核心檔(操作員 2026-11-09:只有操作員與 AI 有改動權)
WRITE_MODES = re.compile(r"^[wax]b?\+?$|^r\+b?$|^wb$")
WRITE_ATTRS = {"write_text", "write_bytes", "unlink", "rename", "replace", "copy", "copy2", "copyfile", "move", "rmtree"}
TARGET_RX = {f: re.compile(re.escape(f) + r"(_v\d{4})?\.py\b") for f in FAMILIES}


def _enclosing_func(node: ast.AST, par: dict):
    """往上找:遇到函式就回函式;沒有函式就回那一條模組層級的敘述(不拿整檔當範圍,否則檔內任一處 tempfile 會把所有寫入都染成夾具)。"""
    n = node
    while n is not None:
        up = par.get(n)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return n
        if isinstance(up, ast.Module):
            return n
        n = up
    return node
INJECTOR_NAME_RX = re.compile(r"Inject|Sweep|AutoPatch|Repair|Rewrite|Patch", re.I)


def _strings_under(node: ast.AST):
    for n in ast.walk(node):
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            yield n.value


def scan_writers(root: Path) -> list:
    """靜態找會寫治理核心檔的呼叫:open(路徑含家族名, 'w'/'a'/'r+')· Path(...).write_text/bytes/unlink/rename/replace · shutil.copy*/move。
    只讀 open(無模式 / 'r')不算。找到的每一筆都是紅線:治理核心只有操作員與 AI(經 PR)能改,工具要有操作員 --apply 閘。"""
    rows = []
    for p in active_py(root):
        r = p.resolve().relative_to(root.resolve()).as_posix()
        self_fam = family_of(p.stem)
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
        par = _parents(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            fn = node.func
            name = fn.id if isinstance(fn, ast.Name) else (fn.attr if isinstance(fn, ast.Attribute) else "")
            # 只看「路徑」位置的字串:open 的第一個引數 · .write_text/.unlink/… 的接收者 · shutil.copy/move/replace 的引數;內容字串不算
            if name == "open":
                path_nodes = node.args[:1]
            elif isinstance(fn, ast.Attribute) and name in WRITE_ATTRS:
                path_nodes = [fn.value] + (list(node.args) if name in {"rename", "replace", "copy", "copy2", "copyfile", "move", "rmtree"} else [])
            else:
                continue
            strs = [s_ for pn in path_nodes for s_ in _strings_under(pn)]
            fams = sorted({f for f in FAMILIES for s_ in strs if TARGET_RX[f].search(s_) and f != self_fam})   # 目標必須是模組檔本身(X.py / X_v####.py),輸出冊 / 報告名不算;自我引用不算
            if not fams:
                continue
            fn_node = _enclosing_func(node, par)
            scope_src = ast.get_source_segment(src, fn_node) or ""
            fixture = bool(scope_src) and ("tempfile." in scope_src or "mkdtemp" in scope_src or "TemporaryDirectory" in scope_src)
            kind = None
            if name == "open":
                mode = None
                if len(node.args) > 1 and isinstance(node.args[1], ast.Constant):
                    mode = str(node.args[1].value)
                for kw in node.keywords:
                    if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                        mode = str(kw.value.value)
                if mode and WRITE_MODES.match(mode):
                    kind = f"open(mode={mode})"
            else:
                kind = f".{name}()"
            if kind:
                rows.append({"writer": r, "lane": lane_of(r), "families": fams, "call": kind, "line": node.lineno, "scope": "FIXTURE(暫存夾)" if fixture else "TREE",
                             "func": getattr(fn_node, "name", "<module>"), "injector_name": bool(INJECTOR_NAME_RX.search(p.stem)), "gated_apply": "--apply" in src})
    return rows


def lane_matrix(loaders: list) -> dict:
    """家族 × 車道:各獨立系統對治理核心的載入數(只讀借用;互不干涉律 L123)。"""
    m = {f: Counter() for f in FAMILIES}
    for lr in loaders:
        if lr["how"] != "PATH_DESKTOP":
            m[lr["family"]][lr["lane"]] += 1
    return {f: dict(c) for f, c in m.items()}

# ------------------------------------------------------------------ ③ 矩陣與建議
def build(root: Path) -> dict:
    fams = scan_copies(root)
    loaders = scan_loaders(root, fams)
    writers = scan_writers(root)
    lanes = lane_matrix(loaders)
    tree_w = [w for w in writers if w["scope"] == "TREE"]
    rights = {"rule": "治理核心(六件)只有操作員與 AI 經 PR 能改;VCGC / VDF / VRN-2 / VQG / VAP 五系統對它只讀借用(互不干涉律 L123),任何自動寫入都是紅線",
              "writers": writers, "tree_writers": len(tree_w), "fixture_writers": len(writers) - len(tree_w),
              "lamp": "RED" if any(not w["gated_apply"] for w in tree_w) else ("YELLOW" if tree_w else "GREEN"),
              "note": "只算 TREE(寫在樹上的):有 --apply 字樣算黃(有閘,仍要操作員按);沒閘算紅;0 筆 = 綠。FIXTURE(所在函式用 tempfile 造暫存夾的自測夾具)另列不計燈。靜態偵測只看路徑位置的字串(open 第一引數 · write_text/unlink/rename/replace 的接收者 · shutil.copy/move 的引數),目標必須是模組檔本身(X.py / X_v####.py),輸出冊 / 報告名不算。"}
    out_f = {}
    lamp_order = {"GREEN": 0, "YELLOW": 1, "RED": 2}
    worst = "GREEN"
    for fam, copies in fams.items():
        rels = superset_relations(root, copies)
        by_copy = defaultdict(lambda: Counter())
        name_only = Counter()
        desktop = 0
        for lr in loaders:
            if lr["family"] != fam:
                continue
            if lr["how"] == "PATH_DESKTOP":
                desktop += 1
            elif lr["how"] in ("NAME_ONLY",):
                name_only[lr["lane"]] += 1
            else:
                key = lr["resolved"].split("(")[0].strip() if lr["resolved"] else "?"
                by_copy[key][lr["how"]] += 1
        for c in copies:
            c["loaders"] = dict(by_copy.get(c["path"], {}))
            c["loader_total"] = sum(c["loaders"].values())
        n_unversioned = [c for c in copies if not c["versioned"]]
        groups = {c["group"] for c in n_unversioned}
        diverged = [r for r in rels if r["kind"] == "DIVERGED"]
        supersets = [r for r in rels if r["kind"] == "SUPERSET"]
        # 建議
        for c in copies:
            if c.get("is_tail"):
                c["advice"] = "正本候選(鎖冊尾版;鏈上前版都保留)"
            elif c["versioned"]:
                c["advice"] = "版本鏈前版:保留(相依鏈律)"
            elif any(r["kind"] == "SUPERSET" and r["superset"] == c["path"] for r in rels):
                c["advice"] = "正本候選(是另一份的 append-only 超集)"
            elif any(r["kind"] == "SUPERSET" and r["subset"] == c["path"] for r in rels):
                c["advice"] = "被超集涵蓋:可退(先遷獨佔載入者,再出版本化轉接件,原檔不就地改)" if c["loader_total"] else "被超集涵蓋 · 無獨佔載入者:可退(出版本化轉接件後進 _superseded)"
            elif any(r["kind"] == "DIVERGED" and c["path"] in (r["a"], r["b"]) for r in rels):
                c["advice"] = "分岔:要 diff 裁(操作員)"
            elif c["identical_to"] and c["loader_total"] == 0:
                c["advice"] = "位元相同 · 無獨佔載入者:可退(版本化轉接件,不就地改)"
            elif c["identical_to"]:
                c["advice"] = f"位元相同 · 有 {c['loader_total']} 個載入者落到這裡:遷呼叫者後再退"
            else:
                c["advice"] = "唯一一份:正本"
        if diverged:
            lamp = "RED"
        elif len(groups) > 1 or any(c["identical_to"] for c in copies if not c["versioned"]):
            lamp = "YELLOW"
        else:
            lamp = "GREEN"
        worst = max(worst, lamp, key=lambda x: lamp_order[x])
        out_f[fam] = {"lamp": lamp, "copies": copies, "relations": rels, "name_only_by_lane": dict(name_only), "desktop_path_refs": desktop, "loaders_by_lane": lanes.get(fam, {}),
                      "groups": len({c["sha8"] for c in copies}), "summary": _summary(fam, copies, rels, name_only, desktop)}
    worst = max(worst, rights["lamp"], key=lambda x: lamp_order[x])
    return {"schema": "VIA.GovCoreChain.v1", "engine": ENGINE, "generated_utc": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "mode": "READONLY · static resolution", "lamp": worst,
            "layout_rule": {"flat": "supportive modules/X.py —— 加速器橋把這個根插進 sys.path,裸 import 落這裡",
                            "numbered": "supportive modules/10_…50_/X.py —— 10_Core_Runtime Runtime Bridge 的 v018 canonical adapter 指名這裡",
                            "topic": "supportive modules/environment|registry|audit_tools|runtime_bridge|ssot|network/X.py —— VRN 插件載入器以 ssot_dir + 上層搜尋(桌機設定值)",
                            "lock": "VeritasAegisNexus:SUP_MDL737 SuperAccel v0110 把裸 import 接到鎖冊尾版 network/VeritasAegisNexus_v1652"},
            "families": out_f, "loader_rows": loaders, "mutation_rights": rights, "lane_matrix": lanes,
            "not_in_scope": ["凍結(RetiredEngines · quarantine · intake)· 鏡像(SCOPE_COPY · Standalone · new modules engines)· _sha 分身(CONFLICT-00005)",
                             "執行期 sys.path 的真實順序(本支只做靜態推定,逐列標 confidence)", "任何修改:殼 · 版本化轉接件 · _superseded 都是操作員裁完才做"]}


def _summary(fam, copies, rels, name_only, desktop) -> str:
    unv = [c for c in copies if not c["versioned"]]
    ver = [c for c in copies if c["versioned"]]
    bits = [f"副本 {len(copies)}(無版號 {len(unv)} · 版本鏈 {len(ver)})", f"內容組 {len({c['sha8'] for c in copies})}"]
    for r in rels:
        if r["kind"] == "SUPERSET":
            bits.append(f"{r['superset'].split('/')[-2] if '/' in r['superset'] else r['superset']} 是 {r['subset'].split('/')[-2] if '/' in r['subset'] else r['subset']} 的超集(+{r['added_lines']} 行)")
        else:
            bits.append(f"分岔 {r['a']} ↔ {r['b']}(各自獨有 {r['only_a']} / {r['only_b']} 行)")
    loaded = [(c["path"], c["loader_total"]) for c in copies if c["loader_total"]]
    bits.append("載入者落點:" + (" · ".join(f"{p} ×{n}" for p, n in loaded) if loaded else "靜態推不到任何一份(全是只給名字 / 桌機路徑)"))
    if name_only:
        bits.append("只給名字 " + " · ".join(f"{k} {v}" for k, v in sorted(name_only.items())))
    if desktop:
        bits.append(f"桌機絕對路徑 {desktop}(倉內無效)")
    return " · ".join(bits)


# ------------------------------------------------------------------ 輸出
def to_md(D: dict) -> str:
    L = []
    A = L.append
    A("# 治理核心相依鏈驗證矩陣(RC-1 W2 · 唯讀)")
    A("")
    A(f"`{D['engine']}` · {D['generated_utc']} · 總燈 **{D['lamp']}** · 靜態解析(逐列 confidence)")
    A("")
    A("## 三種目錄慣例(多頭的根因)")
    A("")
    for k, v in D["layout_rule"].items():
        A(f"- **{k}**:{v}")
    for fam, F in D["families"].items():
        A("")
        A(f"## {fam} · {F['lamp']}")
        A("")
        A(F["summary"])
        A("")
        A("| 副本 | 慣例 | sha8 | 行 | 位元相同於 | 載入者(靜態落點) | 建議 |")
        A("|---|---|---|---|---|---|---|")
        for c in F["copies"]:
            same = ", ".join(x.split("/")[-2] if "/" in x else x for x in c["identical_to"]) or "—"
            ld = ", ".join(f"{k} {v}" for k, v in c["loaders"].items()) or "0"
            A(f"| `{c['path']}` | {c['layout']}{' · tail' if c.get('is_tail') else ''} | {c['sha8']} | {c['lines']} | {same} | {ld} | {c['advice']} |")
        if F["relations"]:
            A("")
            for r in F["relations"]:
                A(f"- {r['kind']}:" + (f"`{r['superset']}` ⊇ `{r['subset']}`(+{r['added_lines']} 行)" if r["kind"] == "SUPERSET" else f"`{r['a']}` ↔ `{r['b']}`(獨有 {r['only_a']} / {r['only_b']} 行)"))
    A("")
    A("## 各獨立系統 × 治理核心(只讀借用;互不干涉律 L123)")
    A("")
    lanes_all = sorted({l for v in D["lane_matrix"].values() for l in v})
    A("| 家族 | " + " | ".join(lanes_all) + " |")
    A("|---|" + "---|" * len(lanes_all))
    for fam, v in D["lane_matrix"].items():
        A(f"| {fam} | " + " | ".join(str(v.get(l, 0)) for l in lanes_all) + " |")
    R = D["mutation_rights"]
    A("")
    A(f"## 改動權 · {R['lamp']}")
    A("")
    A(R["rule"])
    A("")
    if R["writers"]:
        A(f"TREE(真寫樹上){R['tree_writers']} · FIXTURE(暫存夾具){R['fixture_writers']}")
        A("")
        A("| 寫入者 | 車道 | 家族 | 呼叫 | 行 | 範圍 | 函式 | 有 --apply 閘 |")
        A("|---|---|---|---|---|---|---|---|")
        for w in sorted(R["writers"], key=lambda w: (w["scope"] != "TREE", w["writer"])):
            A(f"| `{w['writer']}` | {w['lane']} | {', '.join(w['families'])} | {w['call']} | {w['line']} | {w['scope']} | {w['func']} | {'✔' if w['gated_apply'] else '✘'} |")
    else:
        A("活目錄沒有任何程式會寫治理核心檔(靜態偵測 0 筆)。")
    A("")
    A(R["note"])
    A("")
    A("## 載入者明細(前 60 列)")
    A("")
    A("| 載入者 | 車道 | 家族 | 方式 | 慣例 | 行 | 推定落點 | 信心 |")
    A("|---|---|---|---|---|---|---|---|")
    for lr in D["loader_rows"][:60]:
        A(f"| `{lr['loader']}` | {lr['lane']} | {lr['family']} | {lr['how']} | {lr['layout']} | {lr['line']} | {lr['resolved'][:90]} | {lr['confidence']} |")
    A("")
    A("## 不在範圍")
    for x in D["not_in_scope"]:
        A(f"- {x}")
    return "\n".join(L) + "\n"


def to_ui(D: dict) -> str:
    e = html.escape

    def lc(x):
        x = str(x).upper()
        return "g" if x.startswith("GREEN") else "y" if x.startswith("YELLOW") else "r" if x.startswith("RED") else "k"
    secs = []
    for fam, F in D["families"].items():
        rows = "".join(f"<tr><td><code>{e(c['path'])}</code></td><td>{e(c['layout'])}{' · tail' if c.get('is_tail') else ''}</td><td><code>{e(c['sha8'])}</code></td><td>{c['lines']}</td>"
                       f"<td>{e(', '.join(x.split('/')[-2] if '/' in x else x for x in c['identical_to']) or '—')}</td><td>{e(', '.join(f'{k} {v}' for k, v in c['loaders'].items()) or '0')}</td><td>{e(c['advice'])}</td></tr>" for c in F["copies"])
        rels = "".join(f"<li>{e(r['kind'])}:" + (f"<code>{e(r['superset'])}</code> ⊇ <code>{e(r['subset'])}</code>(+{r['added_lines']} 行)" if r["kind"] == "SUPERSET" else f"<code>{e(r['a'])}</code> ↔ <code>{e(r['b'])}</code>(獨有 {r['only_a']} / {r['only_b']} 行)") + "</li>" for r in F["relations"])
        secs.append(f"<h2>{e(fam)} <span class='lamp {lc(F['lamp'])}'>{e(F['lamp'])}</span></h2><p>{e(F['summary'])}</p>"
                    f"<div class='scroll'><table><thead><tr><th>副本</th><th>慣例</th><th>sha8</th><th>行</th><th>位元相同於</th><th>載入者(靜態落點)</th><th>建議</th></tr></thead><tbody>{rows}</tbody></table></div>"
                    + (f"<ul>{rels}</ul>" if rels else ""))
    lrows = "".join(f"<tr><td><code>{e(lr['loader'])}</code></td><td>{e(lr['lane'])}</td><td>{e(lr['family'])}</td><td>{e(lr['how'])}</td><td>{e(lr['layout'])}</td><td>{lr['line']}</td><td>{e(lr['resolved'][:110])}</td><td>{e(lr['confidence'])}</td></tr>" for lr in D["loader_rows"][:120])
    layout = "".join(f"<li><b>{e(k)}</b>:{e(v)}</li>" for k, v in D["layout_rule"].items())
    nis = "".join(f"<li>{e(x)}</li>" for x in D["not_in_scope"])
    lanes_all = sorted({l for v in D["lane_matrix"].values() for l in v})
    lane_tbl = "<div class='scroll'><table><thead><tr><th>家族</th>" + "".join(f"<th>{e(l)}</th>" for l in lanes_all) + "</tr></thead><tbody>" + "".join(
        f"<tr><td>{e(fam)}</td>" + "".join(f"<td>{v.get(l, 0)}</td>" for l in lanes_all) + "</tr>" for fam, v in D["lane_matrix"].items()) + "</tbody></table></div>"
    R = D["mutation_rights"]
    wrows = "".join(f"<tr><td><code>{e(w['writer'])}</code></td><td>{e(w['lane'])}</td><td>{e(', '.join(w['families']))}</td><td>{e(w['call'])}</td><td>{w['line']}</td><td><span class='lamp {'r' if w['scope'] == 'TREE' else 'k'}'>{e(w['scope'])}</span></td><td>{e(w['func'])}</td><td>{'✔' if w['gated_apply'] else '✘'}</td></tr>" for w in sorted(R["writers"], key=lambda w: (w["scope"] != "TREE", w["writer"])))
    rights_html = (f"<p>TREE(真寫樹上)<b>{R['tree_writers']}</b> · FIXTURE(暫存夾具){R['fixture_writers']}</p><div class='scroll'><table><thead><tr><th>寫入者</th><th>車道</th><th>家族</th><th>呼叫</th><th>行</th><th>範圍</th><th>函式</th><th>有 --apply 閘</th></tr></thead><tbody>{wrows}</tbody></table></div>" if R["writers"]
                   else "<p>活目錄沒有任何程式會寫治理核心檔(靜態偵測 0 筆)。</p>")
    chips = "".join(f"<div class='chip'><b><span class='lamp {lc(F['lamp'])}'>{e(F['lamp'])}</span></b><span>{e(fam)} · 副本 {len(F['copies'])} · 內容組 {F['groups']}</span></div>" for fam, F in D["families"].items())
    return f"""<title>治理核心相依鏈矩陣</title>
<meta name="claude:viewport-fit-sides" content="cover">
<style>
:root{{--vl-bg:#f7f8fa;--vl-white:#fff;--vl-ink:#15181d;--vl-muted:#5b6472;--vl-border:#d8dde5;--vl-border-soft:#eceff4;--vl-row:#fafbfd;
--vl-success-bg:#e8f6ee;--vl-success-ink:#0f5c37;--vl-warning-bg:#fdf4e3;--vl-warning-ink:#7a5410;--vl-danger-bg:#fdecec;--vl-danger-ink:#8d1f1f;--vl-gray-bg:#eef0f3;--vl-gray-ink:#4a5260;
--vl-font-cjk:"Noto Sans TC","PingFang TC","Microsoft JhengHei",sans-serif;--vl-font-mono:ui-monospace,SFMono-Regular,Menlo,monospace;color-scheme:light}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--vl-bg:#111419;--vl-white:#181c22;--vl-ink:#e7ebf1;--vl-muted:#9aa5b4;--vl-border:#2b313a;--vl-border-soft:#22272e;--vl-row:#1d2128;
--vl-success-bg:#12301f;--vl-success-ink:#7fd6a4;--vl-warning-bg:#33270f;--vl-warning-ink:#f0c674;--vl-danger-bg:#3a1717;--vl-danger-ink:#f29c9c;--vl-gray-bg:#232830;--vl-gray-ink:#aab3c0;color-scheme:dark}}}}
:root[data-theme="dark"]{{--vl-bg:#111419;--vl-white:#181c22;--vl-ink:#e7ebf1;--vl-muted:#9aa5b4;--vl-border:#2b313a;--vl-border-soft:#22272e;--vl-row:#1d2128;
--vl-success-bg:#12301f;--vl-success-ink:#7fd6a4;--vl-warning-bg:#33270f;--vl-warning-ink:#f0c674;--vl-danger-bg:#3a1717;--vl-danger-ink:#f29c9c;--vl-gray-bg:#232830;--vl-gray-ink:#aab3c0;color-scheme:dark}}
body{{background:var(--vl-bg);color:var(--vl-ink);font-family:var(--vl-font-cjk);font-size:13px;line-height:1.55;margin:0}}
.wrap{{padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:24px;max-width:1180px;margin:0 auto}}
h1{{font-size:20px;margin:0 0 4px;text-wrap:balance}} h2{{font-size:15px;margin:22px 0 8px;border-bottom:1px solid var(--vl-border);padding-bottom:4px}}
.sub{{color:var(--vl-muted);font-size:11px;margin-bottom:14px}}
.hdr{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:8px;margin:10px 0 18px}}
.chip{{background:var(--vl-white);border:1px solid var(--vl-border);border-radius:8px;padding:8px 12px;min-width:0}} .chip b{{display:block;font-size:14px;margin-bottom:4px}} .chip span{{color:var(--vl-muted);font-size:11px}}
.scroll{{overflow-x:auto}} table{{border-collapse:collapse;width:100%;font-size:12px}} th,td{{text-align:left;padding:6px 8px;border-bottom:1px solid var(--vl-border-soft);vertical-align:top}} th{{color:var(--vl-muted);font-weight:600;font-size:11px;letter-spacing:.03em;text-transform:uppercase}} tr:nth-child(even) td{{background:var(--vl-row)}}
.lamp{{display:inline-block;padding:2px 8px;border-radius:6px;font-family:var(--vl-font-mono);font-size:11px;white-space:nowrap}}
.lamp.g{{background:var(--vl-success-bg);color:var(--vl-success-ink)}} .lamp.y{{background:var(--vl-warning-bg);color:var(--vl-warning-ink)}} .lamp.r{{background:var(--vl-danger-bg);color:var(--vl-danger-ink)}} .lamp.k{{background:var(--vl-gray-bg);color:var(--vl-gray-ink)}}
code{{font-family:var(--vl-font-mono);font-size:11px;background:var(--vl-gray-bg);padding:1px 4px;border-radius:4px;word-break:break-all}}
ul li{{margin-bottom:4px}} .note{{color:var(--vl-muted);font-size:11px}}
</style>
<div class="wrap">
<h1>治理核心相依鏈驗證矩陣 <span class="lamp {lc(D['lamp'])}">{e(D['lamp'])}</span></h1>
<div class="sub">{e(D['engine'])} · {e(D['generated_utc'])} · RC-1 W2 第一項 · 唯讀 · AST 靜態解析(逐列 confidence)· 不動任何檔</div>
<div class="hdr">{chips}</div>
<h2>三種目錄慣例(多頭的根因)</h2><ul>{layout}</ul>
<h2>各獨立系統 × 治理核心(只讀借用 · 互不干涉律 L123)</h2>{lane_tbl}
<h2>改動權 <span class="lamp {lc(R['lamp'])}">{e(R['lamp'])}</span></h2><p>{e(R['rule'])}</p>{rights_html}<p class="note">{e(R['note'])}</p>
{''.join(secs)}
<h2>載入者明細(前 120 列)</h2><div class="scroll"><table><thead><tr><th>載入者</th><th>車道</th><th>家族</th><th>方式</th><th>慣例</th><th>行</th><th>推定落點</th><th>信心</th></tr></thead><tbody>{lrows}</tbody></table></div>
<h2>不在範圍</h2><ul>{nis}</ul>
<p class="note">解法不在這頁:殼 / 版本化轉接件 / _superseded 是操作員裁完正本才做的事(Codex PR 615 P1:不就地改已發布檔)。</p>
</div>
"""


def run(apply: bool) -> int:
    D = build(VIA)
    print(f"[{ENGINE}] 總燈 {D['lamp']} · 家族 {len(D['families'])} · 載入者列 {len(D['loader_rows'])}")
    for fam, F in D["families"].items():
        print(f"  [{F['lamp']}] {fam} · {F['summary'][:220]}")
    if apply:
        OUT_JSON.write_text(json.dumps(D, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        OUT_MD.write_text(to_md(D), encoding="utf-8")
        OUT_UI.write_text(to_ui(D), encoding="utf-8")
        print(f"  [寫] {OUT_JSON.name} · {OUT_MD.name} · {OUT_UI.name}")
    return {"GREEN": 0, "YELLOW": 2, "RED": 1}[D["lamp"]]


# ------------------------------------------------------------------ 自測
def selftest() -> int:
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:260]) if note and not cond else ''}")

    print(f"=== {ENGINE} · 自測(治理核心相依鏈矩陣)===")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        sm = root / "supportive modules"
        (sm / "40_Environment_Health").mkdir(parents=True)
        (sm / "environment").mkdir()
        (sm / "ssot").mkdir()
        (sm / "network").mkdir()
        (root / "functional modules" / "VRN").mkdir(parents=True)
        body = "A = 1\nB = 2\n"
        (sm / "VIA_EnvManager.py").write_text(body, encoding="utf-8")
        (sm / "40_Environment_Health" / "VIA_EnvManager.py").write_text(body, encoding="utf-8")
        (sm / "environment" / "VIA_EnvManager.py").write_text(body, encoding="utf-8")
        (sm / "VIA_SSOT_Unified.py").write_text(body, encoding="utf-8")
        (sm / "ssot" / "VIA_SSOT_Unified.py").write_text(body + "def extra():\n    return 1\n", encoding="utf-8")     # 超集
        (sm / "VIA_Runtime_Bridge_All_in_One.py").write_text("X = 1\nY = 2\n", encoding="utf-8")
        (sm / "network" / "VIA_Runtime_Bridge_All_in_One.py").write_text("X = 1\nZ = 3\n", encoding="utf-8")        # 分岔
        (sm / "network" / "VeritasAegisNexus_v1651.py").write_text("N = 1\n", encoding="utf-8")
        (sm / "network" / "VeritasAegisNexus_v1652.py").write_text("N = 2\n", encoding="utf-8")
        (sm / "20_Registry_SSOT").mkdir()
        (sm / "VIA_RegistryCore_v1.py").write_text("R = 1\n", encoding="utf-8")
        (sm / "20_Registry_SSOT" / "VIA_RegistryCore_v1.py").write_text("R = 1\n", encoding="utf-8")
        (sm / "10_Core_Runtime").mkdir()
        (sm / "10_Core_Runtime" / "VIA_Runtime_Bridge_All_in_One.py").write_text(
            "X = 1\nY = 2\nimport importlib.util\nfrom pathlib import Path\nME = 'VIA_Runtime_Bridge_All_in_One'\n"
            "P = Path(__file__).resolve().parent.parent / '20_Registry_SSOT' / 'VIA_RegistryCore_v1.py'\n"
            "spec = importlib.util.spec_from_file_location('VIA_RegistryCore_v1', str(P))\n", encoding="utf-8")
        (root / "functional modules" / "VRN" / "VRN_X.py").write_text(
            "# ===== [VIA:ACCEL-BRIDGE:v0100]\nimport sys\nsys.path.insert(0, 'supportive modules')\nimport VIA_EnvManager\nfrom VIA_SSOT_Unified import extract\nimport VeritasAegisNexus\n"
            "from pathlib import Path\nP = Path(__file__).parent.parent / '40_Environment_Health' / 'VIA_EnvManager.py'\n"
            "Q = r'C:\\Users\\x\\OneDrive\\supportive_module\\VIA_RegistryCore_v1.py'\nR = 'VIA_Runtime_Bridge_All_in_One'\n", encoding="utf-8")
        (sm / "environment" / "loader.py").write_text("import VIA_EnvManager\n", encoding="utf-8")
        D = build(root)
        env = D["families"]["VIA_EnvManager"]
        chk("① 副本盤點:EnvManager 3 份 · 1 內容組 · 三種慣例 flat / numbered / topic 都認得",
            len(env["copies"]) == 3 and env["groups"] == 1 and {c["layout"] for c in env["copies"]} == {"flat", "numbered", "topic"}, env["summary"])
        rows = [r for r in D["loader_rows"] if r["loader"].endswith("VRN_X.py")]
        imp = [r for r in rows if r["family"] == "VIA_EnvManager" and r["how"] == "IMPORT"]
        chk("② 裸 import + 根插進 sys.path → 落平鋪根 HIGH", imp and imp[0]["resolved"] == "supportive modules/VIA_EnvManager.py" and imp[0]["confidence"] == "HIGH", imp)
        same = [r for r in D["loader_rows"] if r["loader"].endswith("environment/loader.py")]
        chk("③ 同夾裸 import → 落同夾副本(先於根)", same and same[0]["resolved"] == "supportive modules/environment/VIA_EnvManager.py", same)
        lit = [r for r in rows if r["how"] == "PATH_LITERAL"]
        chk("④ BinOp 路徑鏈認出編號夾 → 落 40_Environment_Health 那份 HIGH", lit and lit[0]["layout"] == "numbered" and lit[0]["resolved"].startswith("supportive modules/40_Environment_Health/") and lit[0]["confidence"] == "HIGH", lit)
        dsk = [r for r in rows if r["how"] == "PATH_DESKTOP"]
        chk("⑤ 桌機絕對路徑(OneDrive)→ PATH_DESKTOP,不假裝落到倉內", dsk and dsk[0]["family"] == "VIA_RegistryCore_v1" and dsk[0]["confidence"] == "N/A", dsk)
        nm = [r for r in rows if r["how"] == "NAME_ONLY"]
        chk("⑥ 只給名字 → NAME_ONLY LOW(落點交給搜尋夾)", nm and nm[0]["family"] == "VIA_Runtime_Bridge_All_in_One" and nm[0]["confidence"] == "LOW", nm)
        aeg = [r for r in rows if r["family"] == "VeritasAegisNexus"]
        chk("⑦ import VeritasAegisNexus 在有橋的檔 → 指鎖冊尾版 MEDIUM;尾版 _v1652 標 is_tail · 前版保留", aeg and "v1652" in aeg[0]["resolved"]
            and any(c.get("is_tail") and c["vnum"] == 1652 for c in D["families"]["VeritasAegisNexus"]["copies"])
            and any("保留" in c["advice"] for c in D["families"]["VeritasAegisNexus"]["copies"] if c["vnum"] == 1651), aeg)
        ss = D["families"]["VIA_SSOT_Unified"]
        chk("⑧ 超集:ssot/ 是根的 append-only 超集(+2 行)→ 超集為正本候選、子集可退;家族 YELLOW 不 RED",
            any(r["kind"] == "SUPERSET" and r["superset"].endswith("ssot/VIA_SSOT_Unified.py") and r["added_lines"] == 2 for r in ss["relations"])
            and ss["lamp"] == "YELLOW" and any("正本候選" in c["advice"] for c in ss["copies"] if "ssot/" in c["path"]), (ss["relations"], ss["lamp"]))
        rb = D["families"]["VIA_Runtime_Bridge_All_in_One"]
        net_copy = next(c for c in rb["copies"] if "network/" in c["path"])
        chk("⑨ 分岔:根與 network 兩份各有獨有行 → DIVERGED · 家族 RED · 分岔那份(network)建議『要 diff 裁』;10_Core_Runtime 是根的超集 → 正本候選;總燈取最差 RED",
            any(r["kind"] == "DIVERGED" and r["only_a"] == 1 and r["only_b"] == 1 for r in rb["relations"]) and rb["lamp"] == "RED"
            and "裁" in net_copy["advice"] and any("正本候選" in c["advice"] for c in rb["copies"] if "10_Core_Runtime" in c["path"]) and D["lamp"] == "RED",
            (rb["relations"], rb["lamp"], [c["advice"] for c in rb["copies"]], D["lamp"]))
        rc_ = D["families"]["VIA_RegistryCore_v1"]
        edge = [lr for lr in D["loader_rows"] if lr["family"] == "VIA_RegistryCore_v1" and lr["loader"].endswith("10_Core_Runtime/VIA_Runtime_Bridge_All_in_One.py")]
        chk("⑱ 跨家族邊(Codex PR 616 P2):治理件 10_Core_Runtime 橋以 BinOp 路徑載 20_Registry_SSOT/VIA_RegistryCore_v1 → 算進該副本的載入者(numbered · HIGH);自我引用字串 ME 不算",
            edge and edge[0]["how"] == "PATH_LITERAL" and edge[0]["resolved"].endswith("20_Registry_SSOT/VIA_RegistryCore_v1.py") and edge[0]["confidence"] == "HIGH"
            and next(c for c in rc_["copies"] if "20_Registry_SSOT" in c["path"])["loader_total"] == 1
            and not any(lr["family"] == "VIA_Runtime_Bridge_All_in_One" and lr["loader"].endswith("10_Core_Runtime/VIA_Runtime_Bridge_All_in_One.py") for lr in D["loader_rows"]),
            (edge, [(c["path"], c["loader_total"]) for c in rc_["copies"]]))
        chk("⑩ 建議:三份 EnvManager 都有載入者落到 → 全是『遷呼叫者後再退』;SSOT 子集(根)有 import 載入者 → 『被超集涵蓋:可退(先遷…)』",
            all("遷呼叫者" in c["advice"] for c in env["copies"]) and any("被超集涵蓋:可退(先遷" in c["advice"] for c in ss["copies"] if c["path"] == "supportive modules/VIA_SSOT_Unified.py"),
            [c["advice"] for c in env["copies"]] + [c["advice"] for c in ss["copies"]])
        (root / "functional modules" / "VRN" / "VRN_W.py").write_text(
            "import shutil\nfrom pathlib import Path\nopen('supportive modules/VIA_EnvManager.py', 'w').write('x')\n"
            "Path('supportive modules/ssot/VIA_SSOT_Unified.py').write_text('y')\nshutil.copy('a.py', 'supportive modules/VIA_RegistryCore_v1.py')\n"
            "open('supportive modules/VIA_Runtime_Bridge_All_in_One.py').read()\n"
            "Path('out/VIA_SSOT_Unified_latest.md').write_text('report')\n"
            "def selftest():\n    import tempfile\n    t = Path(tempfile.mkdtemp())\n    (t / 'supportive modules' / 'VIA_EnvManager.py').write_text('fixture')\n", encoding="utf-8")
        D2 = build(root)
        W = D2["mutation_rights"]["writers"]
        tree_w = [w for w in W if w["scope"] == "TREE"]
        chk("⑮ 改動權:寫模式 open · write_text · shutil.copy 三筆 TREE 都抓到;只讀 open 不算;輸出冊 *_latest.md 不算(目標非模組檔);沒 --apply 閘 → 改動權 RED · 總燈 RED",
            len(tree_w) == 3 and {w["call"] for w in tree_w} == {"open(mode=w)", ".write_text()", ".copy()"} and all(w["lane"] == "VRN" for w in tree_w)
            and D2["mutation_rights"]["lamp"] == "RED" and D2["lamp"] == "RED", W)
        chk("⑰ 夾具:所在函式用 tempfile 造暫存夾的寫入 → FIXTURE,另列不計燈", any(w["scope"].startswith("FIXTURE") and w["func"] == "selftest" for w in W) and D2["mutation_rights"]["fixture_writers"] == 1, W)
        chk("⑯ 車道矩陣:VRN 對 EnvManager 的載入列計數 ≥ 2(import + 字面路徑)· SUP 對 EnvManager 1(environment/loader.py)",
            D2["lane_matrix"]["VIA_EnvManager"].get("VRN", 0) >= 2 and D2["lane_matrix"]["VIA_EnvManager"].get("SUP", 0) == 1, D2["lane_matrix"]["VIA_EnvManager"])
        (root / "functional modules" / "VRN" / "VRN_W.py").unlink()
        md, ui = to_md(D), to_ui(D)
        chk("⑪ 輸出:MD 六家族表 · UI 無骨架標籤 · title 在頂 · 色值只用 --vl-* · 逸出",
            md.count("## ") >= 8 and not re.search(r"<(!doctype|html|body)", ui, re.I) and ui.startswith("<title>")
            and not re.search(r'style="[^"]*#[0-9a-fA-F]{3,6}', ui.split("</style>")[1]) and "&lt;" not in md, None)
        snap = {p: sha8(p.read_bytes()) for p in root.rglob("*.py")}
        build(root)
        chk("⑫ 唯讀:整輪跑完,樹上每個 .py 位元不變", snap == {p: sha8(p.read_bytes()) for p in root.rglob("*.py")})
    try:
        real = build(VIA)
        crashed = ""
    except Exception as exc:  # noqa: BLE001
        crashed, real = repr(exc), {}
    chk("⑬ 實樹:六家族都盤到、不炸;AegisNexus 尾版 = network/_v1652;EnvManager 三份位元相同;改動權區在",
        not crashed and len(real.get("families", {})) == 6 and "mutation_rights" in real
        and any(c.get("is_tail") and c["path"].endswith("network/VeritasAegisNexus_v1652.py") for c in real["families"]["VeritasAegisNexus"]["copies"])
        and real["families"]["VIA_EnvManager"]["groups"] == 1, crashed or {f: F["lamp"] for f, F in real.get("families", {}).items()})
    src = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    writes_env = any(isinstance(n, ast.Subscript) and isinstance(getattr(n.value, "attr", None), str) and n.value.attr == "environ" and isinstance(getattr(n, "ctx", None), ast.Store) for n in ast.walk(tree))
    subproc = any(isinstance(n, (ast.Import, ast.ImportFrom)) and any((x.name or "").split(".")[0] == "sub" + "process" for x in n.names) for n in ast.walk(tree))
    chk("⑭ 紀律:加速器橋 · 網路橋在;不碰 TA-Lib;不派子行程;不寫 environ(AST)",
        "VIA:ACCEL-BRIDGE" in src and "VIA:NET-BRIDGE" in src and not re.search(r"^\s*(import|from)\s+talib", src, re.M) and not subproc and not writes_env)
    print(f"  [計] {ENGINE} 自測 OK {sum(ok)} · FAIL {len(ok) - sum(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        return selftest()
    if args and args[0] == "run":
        return run("--apply" in args)
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
