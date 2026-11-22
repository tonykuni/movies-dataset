#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""CGC_SystemManager v0119 — 薄尾:toolbox 擴成四群(開發支援 · 中央控管 · U/I 顯示 · 標準視覺鎖定)+ 每支程式核「獨立性」

操作員 2026-11-22 09:35:「VCGC SYSTEM MANAGER 控有開發支援工具 / 中央控管工具 / U/I 顯示工具及標準視覺鎖定模組 · 獨立系統不可直接影響其他系統 · 收尾」。
  toolbox [check]   四群逐支核:
                      程式(.py)= 尾版在 · 有編號 · 有登錄 · 有交接案 · 有盤點站 · (工具類)引擎版本冊 / 鎖冊 · **獨立性**
                      冊(.json)= 尾版在 · 需求冊有登記(編號系統只給程式與律條發號,冊本身靠需求冊管)· JSON 讀得懂 · (格式鎖)四色燈 token 在
                    獨立性(只看尾版本身,逐函式):import 他系統模組 = 紅;同一個函式(或模組頂層)裡有寫檔動作又寫著他系統資料夾路徑 = 黃
                    (待人工確認只讀);自測 / 假倉夾具函式不算(它們寫在暫存夾);其餘綠。互相只讀監控是允許的(L123)。
  toolbox run / help / install、connect、guard、fuse、omniroute 照前版;run 與 check 用同一份四群目錄。
不改任何工具本身;不改 VDF / VRN 的檔。
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

import ast
import importlib.util
import json
import re
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA_ROOT = HERE.parents[1]
_STEM = "CGC_SystemManager"
TAG = "CGC_SystemManager v0119"
REG = "supportive modules/registry"
AI = "docs/handoff/ai"


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
if "cgc_prior_for_v0119" in sys.modules:
    PRIOR = sys.modules["cgc_prior_for_v0119"]
else:
    _spec = importlib.util.spec_from_file_location("cgc_prior_for_v0119", PRIOR_PATH)
    PRIOR = importlib.util.module_from_spec(_spec)
    sys.modules["cgc_prior_for_v0119"] = PRIOR
    _spec.loader.exec_module(PRIOR)


def __getattr__(name):
    return getattr(PRIOR, name)


def _v117():
    m = PRIOR
    while m is not None and "TOOLBOX" not in vars(m):  # 不用 hasattr:薄尾的 __getattr__ 會把前版名稱轉接過來
        m = getattr(m, "PRIOR", None)
    return m


V117 = _v117()
GROUPS = ["開發支援", "中央控管", "U/I 顯示", "標準視覺鎖定"]
CENTRAL = [
    {"key": "console", "name": "VCGC 主控台(中央入口 · 串測 · 交接)", "stem": "CGC_MDL149_VeritasCentralGovernanceConsole", "dir": REG, "route": "via-vcgc …"},
    {"key": "mcp", "name": "VCGC MCP 伺服器(唯讀門面 · 17 工具)", "stem": "CGC_MDL279_MCPServer", "dir": REG, "route": "connect · omniroute"},
    {"key": "regexdict", "name": "SSOT 正則字典", "stem": "CGC_MDL115_SSOTRegexDict", "dir": REG, "route": "via-vcgc ssot panorama"},
    {"key": "synonym", "name": "同義字聯集", "stem": "CGC_MDL176_SynonymUnion", "dir": REG, "route": "via-vcgc ssot panorama"},
    {"key": "regexparam", "name": "正則 / 參數同步", "stem": "CGC_MDL219_RegexParamSync", "dir": REG, "route": "via-vcgc run CGC_MDL219_RegexParamSync"},
    {"key": "constitution", "name": "憲法檢查", "stem": "VIA_ConstitutionCheck", "dir": AI, "route": "python VIA_ConstitutionCheck check"},
    {"key": "fivesys", "name": "五系統憲法矩陣(只讀各系統自報)", "stem": "VIA_FiveSystemConstitution", "dir": AI, "route": "python VIA_FiveSystemConstitution run"},
    {"key": "policy", "name": "政策冊(律 L###)", "stem": "VIA_Policy_Laws_SSOT", "dir": REG, "route": "via-vcgc token(卡尾)", "ext": ".json"},
    {"key": "synbook", "name": "中央同義字 / 正則冊", "stem": "VIA_Central_Synonym_Regex", "dir": REG, "route": "via-vcgc ssot panorama", "ext": ".json"},
]
UI = [
    {"key": "uiengine", "name": "U/I 引擎(VCGC 頁 · 卡片 · 矩陣)", "stem": "CGC_MDL261_UIEngine", "dir": REG, "route": "via-vcgc overview / page"},
    {"key": "visuallock-ui", "name": "標準視覺鎖定 U/I", "stem": "VIA_VisualLock", "dir": AI, "route": "python VIA_VisualLock"},
]
LOCK = [
    {"key": "formatlock", "name": "U/I 格式鎖(四色燈 token · 字型)", "stem": "VIA_UI_FormatLock", "dir": REG, "route": "各頁 _lamp_css 讀它", "ext": ".json", "lamp_tokens": True},
    {"key": "template", "name": "U/I 模板冊(共用 typekit 色與版面)", "stem": "VIA_UI_Template_SSOT", "dir": REG, "route": "各系統 ui 動詞讀它", "ext": ".json"},
    {"key": "wplock", "name": "工作平台模板鎖", "stem": "VIA_UI_WorkPlatform_TemplateLock", "dir": REG, "route": "工作平台頁讀它", "ext": ".json"},
]
OTHER_SYS = re.compile(r"^(VDF|VRN|VQG|VAP)[_A-Za-z0-9]*$")
OTHER_PATH = re.compile(r"functional modules[\\/]+(VDF|VRN|VQG|VAP)\b")
WRITE_OPS = re.compile(r"\.write_text\(|\.write_bytes\(|open\([^)]*['\"][wa]b?['\"]|shutil\.(copy|move|rmtree)|os\.(replace|remove|rename|unlink)\(|\.unlink\(")


def catalog() -> list:
    dev = [dict(t, group="開發支援") for t in V117.TOOLBOX]
    return dev + [dict(t, group="中央控管") for t in CENTRAL] + [dict(t, group="U/I 顯示") for t in UI] + [dict(t, group="標準視覺鎖定") for t in LOCK]


def tail_any(via: Path, d: str, stem: str, ext: str = ".py"):
    hits = [p for p in (via / d).glob(stem + "_v*" + ext) if _vnum(p) >= 0 and p.stem.rsplit("_v", 1)[0] == stem]
    return max(hits, key=_vnum) if hits else None


FIXTURE = re.compile(r"^(selftest|_?fixture|_?self_test|test_)", re.I)


def _scopes(tree: ast.AST, src: str):
    """逐函式 + 模組頂層(不含 def / class 本體);自測 / 夾具函式略過。"""
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and not FIXTURE.match(n.name):
            yield n.name, n, ast.get_source_segment(src, n) or ""
    top = [st for st in getattr(tree, "body", []) if not isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
    yield "<模組頂層>", ast.Module(body=top, type_ignores=[]), "\n".join(ast.get_source_segment(src, st) or "" for st in top)


def independence(path: Path) -> tuple:
    """只看尾版本身:import 他系統 = RED;同一函式內寫檔 + 他系統路徑 = YELLOW;其餘 GREEN。"""
    try:
        src = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(src)
    except (OSError, SyntaxError, ValueError) as e:
        return "YELLOW", "剖析不了:%s" % type(e).__name__
    imps = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imps += [a.name.split(".")[0] for a in n.names]
        elif isinstance(n, ast.ImportFrom) and n.module and not n.level:
            imps.append(n.module.split(".")[0])
    bad = sorted({m for m in imps if OTHER_SYS.match(m)})
    if bad:
        return "RED", "直接 import 他系統:" + ",".join(bad)
    refs, hits = 0, []
    for name, node, seg in _scopes(tree, src):
        lits = [c for c in ast.walk(node) if isinstance(c, ast.Constant) and isinstance(c.value, str) and OTHER_PATH.search(c.value)]
        refs += len(lits)
        if lits and WRITE_OPS.search(seg):
            hits.append(name)
    if hits:
        return "YELLOW", "函式 %s 裡有寫檔動作又寫著他系統路徑(待人工確認只讀)" % "、".join(hits[:5])
    return "GREEN", "只讀 / 不碰他系統" + (" · 引用他系統路徑 %d 處(只讀監控)" % refs if refs else "")


def check(via: Path = VIA_ROOT) -> dict:
    nums = V117._number_sources(via)
    try:
        comp = (via / REG / "VIA_Component_Inventory_SSOT_v0100.json").read_text(encoding="utf-8")
    except OSError:
        comp = ""
    try:
        cases = json.dumps(json.loads((via / REG / "VIA_Handoff_Continuity_SSOT_v0100.json").read_text(encoding="utf-8")).get("test_cases", {}), ensure_ascii=False)
    except (OSError, ValueError):
        cases = ""
    req_p = V117._latest(via, "VIA_Requirements_SSOT_v*.json")
    reqs = req_p.read_text(encoding="utf-8") if req_p else ""
    inv_p = V117._latest(via, "VIA_VCGC_FunctionInventory_SSOT_v*.json")
    inv = inv_p.read_text(encoding="utf-8") if inv_p else ""
    try:
        eng = json.loads((via / REG / "VIA_EngineVersion_Register_v0100.json").read_text(encoding="utf-8")).get("rows", [])
    except (OSError, ValueError):
        eng = []
    rows = []
    for t in catalog():
        g = t["group"]
        if t.get("stem") is None:
            p = V117.lock_path(via, t["lock"])
            items = {"尾版在": bool(p), "鎖冊": bool(p)}
        elif t.get("ext") == ".json":
            p = tail_any(via, t["dir"], t["stem"], ".json")
            rel = p.relative_to(via).as_posix() if p else ""
            try:
                body = json.loads(p.read_text(encoding="utf-8-sig")) if p else None
            except (OSError, ValueError):
                body = None
            items = {"尾版在": bool(p), "需求冊有登記": bool(p) and t["stem"] in reqs, "JSON 讀得懂": body is not None}
            if t.get("lamp_tokens"):
                txt = json.dumps(body, ensure_ascii=False) if body is not None else ""
                items["四色燈 token"] = all(("lamp_" + c) in txt.lower() for c in ("red", "yellow", "green", "gray"))
        else:
            p = tail_any(via, t["dir"], t["stem"])
            rel = p.relative_to(via).as_posix() if p else ""
            items = {"尾版在": bool(p), "有編號": bool(p) and rel in nums, "有登錄": bool(p) and p.name in comp,
                     "有交接案": bool(p) and (p.name in cases or t["stem"] in cases), "有盤點站": bool(p) and t["stem"] in inv}
            if t.get("family"):
                items["引擎版本冊"] = any(r.get("family") == t["family"] and r.get("file") == (p.name if p else None) for r in eng)
            if t.get("lock"):
                lp = V117.lock_path(via, t["lock"])
                items["鎖冊指到尾版"] = bool(p and lp and lp.resolve() == p.resolve())
        ind = independence(p) if (p and p.suffix == ".py") else ("GRAY", "冊 / 加速器:不適用")
        if p and p.suffix == ".py":
            items["獨立性"] = ind[0] == "GREEN"
        miss = [k for k, v in items.items() if not v]
        lamp = "RED" if (not p or ind[0] == "RED") else ("GREEN" if not miss else "YELLOW")
        rows.append({"group": g, "key": t["key"], "name": "〔%s〕%s" % (g, t["name"]), "tail": p.name if p else None, "items": items,
                     "route": t["route"], "lamp": lamp, "missing": miss, "independence": ind[1]})
    lamps = [r["lamp"] for r in rows]
    return {"tag": TAG, "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "tools": len(rows), "rows": rows,
            "groups": {g: [r["lamp"] for r in rows if r["group"] == g].count("GREEN") for g in GROUPS},
            "lamp": "RED" if "RED" in lamps else "YELLOW" if "YELLOW" in lamps else "GREEN", "inventory": inv_p.name if inv_p else None}


def main() -> int:
    argv = sys.argv[1:]
    if argv[:1] == ["toolbox"]:
        keep = V117.check, V117.TAG
        V117.check, V117.TAG = check, TAG
        try:
            return _toolbox(argv)
        finally:
            V117.check, V117.TAG = keep
    return PRIOR.main()


def _toolbox(argv) -> int:
    sub = argv[1] if len(argv) > 1 else "check"
    if sub == "check":
        res = check()
        extra = ["## 獨立性(只看尾版本身)"] + ["[%s] %s · %s" % ("GREEN" if r["items"].get("獨立性", True) else "RED" if r["lamp"] == "RED" else "YELLOW",
                                                             r["key"], r["independence"]) for r in res["rows"] if r["tail"] and r["tail"].endswith(".py")]
        bad = [r["key"] for r in res["rows"] if r["lamp"] != "GREEN"]
        res["next"] = ("NEXT: 先補缺件:" + "、".join(bad[:12])) if bad else "NEXT: 四群全綠"
        out = V117.write_report(VIA_ROOT, res, extra)
        print((out / "TOOLBOX_latest.txt").read_text(encoding="utf-8"), flush=True)
        return 0 if res["lamp"] == "GREEN" else 2 if res["lamp"] == "YELLOW" else 1
    sys.argv = [sys.argv[0]] + list(argv)
    return V117.main()


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print("[計] %s 自測開始(本版 9 項 · 前版 %s)" % (TAG, PRIOR_PATH.name), flush=True)
    with tempfile.TemporaryDirectory(prefix="csm119_") as td:
        d, fm = Path(td), "functional modules/"
        (d / "a.py").write_text("import json\nfrom pathlib import Path\nP = '" + fm + "VDF/x.json'\nprint(Path(P).read_text())\n", encoding="utf-8")
        (d / "b.py").write_text("import VDF_SystemManager\n", encoding="utf-8")
        (d / "c.py").write_text("from pathlib import Path\nPath('" + fm + "VRN/out.json').write_text('x')\n", encoding="utf-8")
        (d / "e.py").write_text("x = 1\n", encoding="utf-8")
        (d / "f.py").write_text("from pathlib import Path\ndef selftest():\n    Path('" + fm + "VDF/x.py').write_text('x')\n", encoding="utf-8")
        chk("T1 只讀引用他系統路徑 → 綠(互相只讀監控允許)", independence(d / "a.py")[0] == "GREEN", independence(d / "a.py"))
        chk("T2 直接 import 他系統 → 紅", independence(d / "b.py")[0] == "RED", independence(d / "b.py"))
        chk("T3 寫檔 + 指到他系統路徑 → 黃(待人工確認)", independence(d / "c.py")[0] == "YELLOW", independence(d / "c.py"))
        chk("T4 乾淨 → 綠 · 自測夾具裡寫他系統假路徑 → 不算(綠)", independence(d / "e.py")[0] == "GREEN" and independence(d / "f.py")[0] == "GREEN", independence(d / "f.py"))
    cat = catalog()
    chk("T5 四群都有工具 · 開發支援 = 前版十個", {t["group"] for t in cat} == set(GROUPS) and sum(t["group"] == "開發支援" for t in cat) == len(V117.TOOLBOX))
    res = check()
    books = [r for r in res["rows"] if r["tail"] and r["tail"].endswith(".json")]
    chk("T6 真倉:每個工具都找得到尾版 · 冊核「需求冊有登記」不核編號", all(r["tail"] for r in res["rows"]) and books
        and all("需求冊有登記" in r["items"] and "有編號" not in r["items"] for r in books), [r["key"] for r in res["rows"] if not r["tail"]])
    src = Path(__file__).read_text(encoding="utf-8")
    chk("T7 檔面:第 3 行加速器標記 · 零 TA-Lib · 不設同意閘 · 本檔獨立性綠",
        src.splitlines()[2].strip() == "# [VIA:ACCEL-BRIDGE:v0111]" and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src) and independence(Path(__file__))[0] == "GREEN", independence(Path(__file__)))
    chk("T8 鏈:指到真正的 v0117 模組(不是靠 __getattr__ 轉接的那層)", "TOOLBOX" in vars(V117) and V117.TAG.endswith("v0117"), getattr(V117, "TAG", None))
    prior_rc = PRIOR.selftest()
    chk("T9 前版 %s 自測照過" % PRIOR_PATH.name, prior_rc == 0, prior_rc)
    n = sum(ok)
    print("[計] %s 自測 %d/%d · %s" % (TAG, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    return 0 if n == len(ok) else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
