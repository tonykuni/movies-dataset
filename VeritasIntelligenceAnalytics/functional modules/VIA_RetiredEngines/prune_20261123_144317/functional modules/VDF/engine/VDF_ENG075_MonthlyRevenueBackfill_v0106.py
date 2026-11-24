#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VDF_ENG075_MonthlyRevenueBackfill v0106 — 薄尾:補前版鏈公開名稱轉接(VCGC 全景 TAILAPI · 第二輪 2026-10-20)

操作員令(2026-10-20):「繼續第二輪修復 SWALLOW 與 TAILAPI」。
v0105 只轉 main / selftest(或只蓋自己改的幾個名稱),前版鏈其他公開名稱(decode_page, fetch_hosts, fetch_one, gate_open, is_stub, month_seq …)
從尾版取不到 —— 呼叫端照慣例「取本族尾版」載入後再取這些名稱會 AttributeError(全景 TAILAPI;執行期實測確認取不到)。
本版(不改任何行為,只補轉接):
  ① 模組層 __getattr__:沿實際委派鏈(v0105 → v0104 → v0103 → v0100)由新到舊逐支找,回最新的那個定義(雙底線名稱不轉;找不到照實 AttributeError)。
  ② 直接執行 = 原樣交給 v0105(runpy 當 __main__ 跑:參數 · 輸出 · 結束碼 · 同意閘行為一字不改);
     --selftest 先跑本版轉接檢查(前版鏈每個公開名稱都取得到),過了再跑前版自測。
VDF 自己的模組:不匯入他系統程式;同意閘不讀不寫;不碰 TA-Lib;不裝套件、不寫環境。
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


def _via_net():
    """統包唯一網路工具惰性載入;本檔的連網全經 MDL008 子行程改道。"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None

import ast
import importlib.util
import re
import runpy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_ENG075_MonthlyRevenueBackfill"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"



CHAIN_VERSIONS = ('0105', '0104', '0103', '0100')       # 照 CGC_MDL158 chain 圖的實際委派鏈(尾版 → 本體);更舊、已被本體重寫取代的版不轉
CHAIN = [HERE / ("%s_v%s.py" % (_STEM, v)) for v in CHAIN_VERSIONS]
PRIOR_PATH = CHAIN[0]
_MODS: dict = {}


def _module(p: Path):
    """前版鏈某一支(惰性載入一次;模組名帶雙方版號,不和別處載入的同一支撞名)。"""
    if p not in _MODS:
        name = "%s_fwd_v%s_from_v%s" % (_STEM, p.stem.rsplit("_v", 1)[-1], Path(__file__).stem.rsplit("_v", 1)[-1])
        spec = importlib.util.spec_from_file_location(name, p)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
        _MODS[p] = mod
    return _MODS[p]


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    for p in CHAIN:
        mod = _module(p)
        if name in vars(mod):
            return vars(mod)[name]
    raise AttributeError("%s:前版鏈 %s 都沒有 %s" % (TAG, [q.name for q in CHAIN], name))


def public_names() -> list:
    """前版鏈每支檔的頂層公開名稱(def / class / 賦值;不以底線開頭)。"""
    out = set()
    for p in CHAIN:
        for node in ast.parse(p.read_text(encoding="utf-8")).body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                out.add(node.name)
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                for t in (node.targets if isinstance(node, ast.Assign) else [node.target]):
                    if isinstance(t, ast.Name):
                        out.add(t.id)
    return sorted(n for n in out if not n.startswith("_"))


def check_forwarding() -> int:
    """本版轉接檢查;回 0 = 全過。"""
    p = f = 0

    def chk(label, cond, note=""):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % label)
        else:
            f += 1
            print("  [FAIL] %s%s" % (label, (" · " + str(note)[:300]) if note else ""))

    me = sys.modules[__name__]
    names = public_names()
    miss = [n for n in names if not hasattr(me, n)]
    chk("① 前版鏈 %d 支的公開名稱 %d 個全取得到(由新到舊取最新定義)" % (len(CHAIN), len(names)), names and not miss, miss)
    newest = {}
    for q in reversed(CHAIN):
        for n in public_names_of(q):
            newest[n] = q
    wrong = [n for n, q in newest.items() if n not in vars(me) and getattr(me, n) is not vars(_module(q)).get(n)]
    chk("② 同名取最新那一支的定義(不是更舊的)", not wrong, wrong)
    probe = _module(CHAIN[0])
    probe.__fwd_probe__ = 1                       # 鏈上真的有的雙底線名稱也不准轉
    try:
        getattr(me, "__fwd_probe__")
        dunder = False
    except AttributeError:
        dunder = True
    finally:
        del probe.__fwd_probe__
    try:
        getattr(me, "no_such_name_fwd_check")
        unknown = False
    except AttributeError as exc:
        unknown = "前版鏈" in str(exc)
    chk("③ 雙底線名稱不轉 · 鏈上沒有的名稱照實 AttributeError(說明找過哪幾支)", dunder and unknown)
    globs_prior = re.compile(r"glob\([^)\n]*(?:%s|_STEM)[^)\n]*_v\*\.py" % re.escape(_STEM))   # glob 取本族前版(不是網路橋那種 glob)
    links = []
    for a, b in zip(CHAIN, CHAIN[1:]):
        ta = a.read_text(encoding="utf-8")
        if b.stem not in ta and not globs_prior.search(ta):
            links.append("%s 沒連到 %s" % (a.name, b.name))
    body = CHAIN[-1]
    tb = body.read_text(encoding="utf-8")
    older = [q.name for q in HERE.glob(_STEM + "_v*.py")
             if q.stem.rsplit("_v", 1)[-1] < body.stem.rsplit("_v", 1)[-1] and q.stem in tb]
    if older or globs_prior.search(tb):
        links.append("%s 還連更舊的 %s(不是本體)" % (body.name, older or "glob"))
    chk("⑤ 委派鏈完整:每支都連到下一支(檔名或 glob 取前版)· 最後一支 %s 是本體(不再連更舊的)" % body.name, not links, links)
    src = Path(__file__).read_text(encoding="utf-8")
    imports = re.findall(r"^\s*(?:import|from)\s+([A-Za-z_][\w.]*)", src, re.M)
    chk("④ 加速器橋 · 網路橋在;不匯入他系統程式;不碰 TA-Lib;同意閘不寫",
        "VIA:ACCEL-BRIDGE" in src and "def _via_net" in src
        and not [x for x in imports if x.startswith(("CGC_", "VRN_", "VRN2_", "VCGC"))]
        and not re.search(r"^\s*(import|from)\s+" + "talib", src, re.M)
        and not re.search(r"\[[\"']VIA_(NET|SCRAPE)_" + r"CONSENT[\"']\]\s*=(?!=)", src))
    print("  [計] %s 轉接 %d 名 · 本版 %d/%d · %s" % (TAG, len(names), p, p + f, "PASS" if not f else "FAIL"), flush=True)
    return 0 if not f else 1


def public_names_of(p: Path) -> list:
    out = set()
    for node in ast.parse(p.read_text(encoding="utf-8")).body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.add(node.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            for t in (node.targets if isinstance(node, ast.Assign) else [node.target]):
                if isinstance(t, ast.Name):
                    out.add(t.id)
    return sorted(n for n in out if not n.startswith("_"))


def selftest() -> int:
    """程式呼叫的自測:本版轉接檢查 + 前版鏈自己的 selftest(有的話)。"""
    rc = check_forwarding()
    if rc:
        return rc
    prior = __getattr__("selftest") if "selftest" in public_names() else None
    return prior() if callable(prior) else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv[1:]:
        print("=== %s · 薄尾自測(前版鏈公開名稱轉接;零網路)===" % TAG, flush=True)
        if check_forwarding():
            raise SystemExit(1)
    runpy.run_path(str(PRIOR_PATH), run_name="__main__")
