#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_VCGC ConvergeEngine v0100 — 類似功能全景收斂引擎:清點 → AST 分類編號說明註冊 → 模組化簡化體檢 → 複製到 TEMP(影子區)→ 整合去重(零遺失證明)→ 一個最強模組候選。

操作員 2026-11-13:「系統類似功能全景式模組引擎清點 注入AST分類編號清點說明 註冊 引擎進行模組化 簡化後測試無誤後複製到TEMP
進行整合去重清點無誤後修正測試更新為一個最強模組 這個引擎應該已經完成 搭配CLAUDE若有關聯工具整合完成 授權自動解決上述問題」。
零件早已分散在 VCGC(L116 不重寫):CGC_MDL281 ShadowMerge(影子區 · 逐定義六類 · 零遺失證明)· VIA_VCGC_MDL258 ToolMatrix
(converge 13 步體檢 · prune 驗證後刪舊)· CGC_MDL092 / MDL161(整併盤點 · PEIS)。本支只把它們串成一條、補上「全景找類似功能群」。
  census [--json]          VCGC 尾版逐支 AST 頂層定義 → 類似群(定義名重疊 Jaccard ≥ 0.5 且共用 ≥ 3 · 或英文名相同);只讀
  pair <家族A> <家族B>     兩族:13 步體檢 → 影子區(VIA_Reports/converge/…)比對 + 零遺失證明 → 收斂帳只增;原檔不動
  all [--top N]            census → 每群前兩支跑 pair → VIA_Reports/converge/CONVERGE_latest.html / .json(操作員視覺鎖定 U/I)
  --selftest
證不出零損失 = BLOCKED_NEEDS_RULING(L75);PROVEN_ZERO_LOSS 才是「可升一個最強模組」的候選,升版仍走 WKF045 ⑨–⑫(測試 · 清點 · 啟動 · prune)。
只寫 VIA_Reports/converge/ 與收斂帳 VIA_VCGC_ConvergeLedger_v0100.jsonl;他系統只讀(L123);零網路;不碰 TA-Lib(L50)。
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
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
import ast
import importlib.util
import json
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
_STEM = re.match(r"(.+?)_v(\d{4})$", Path(__file__).stem)
NAME = _STEM.group(1) if _STEM else Path(__file__).stem
VERSION = "v" + (_STEM.group(2) if _STEM else "0000")
OUT = VIA / "VIA_Reports" / "converge"
LEDGER = "VIA_VCGC_ConvergeLedger_v0100.jsonl"
SKIP_DEFS = {"main", "selftest", "__getattr__", "chk", "_vnum", "rel", "utc_now", "load_json", "sha256", "_h"}


def _load(pattern: str, alias: str, folder: Path = HERE):
    hits = [q for q in folder.glob(pattern) if re.search(r"_v\d{4}\.py$", q.name)]
    if not hits:
        return None
    p = max(hits, key=lambda q: int(re.search(r"_v(\d{4})\.py$", q.name).group(1)))
    spec = importlib.util.spec_from_file_location(alias, p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[alias] = mod
    spec.loader.exec_module(mod)
    return mod


def tm():
    return sys.modules.get("_cv_toolmatrix") or _load("VIA_VCGC_MDL258_ToolMatrix_v*.py", "_cv_toolmatrix")


def shadow():
    return sys.modules.get("_cv_shadow") or _load("CGC_MDL281_ShadowMerge_v*.py", "_cv_shadow")


def defs_of(path: Path) -> set:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return set()
    return {n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))} - SKIP_DEFS


def census(via: Path = VIA) -> dict:
    """VCGC 自己的家族(含工具鎖席位)兩兩比:定義名 Jaccard ≥ 0.5 且共用 ≥ 3,或英文名相同 → 同群(並查集)。"""
    T = tm()
    fams, _sk, _ex = T.discover(via)
    items = {f: {"tail": i["tail"], "defs": defs_of(i["tail"]), "eng": T.english_of(f)} for f, i in fams.items() if i.get("tail")}
    names = sorted(items)
    parent = {f: f for f in names}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    links = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            da, db = items[a]["defs"], items[b]["defs"]
            inter = len(da & db)
            jac = inter / len(da | db) if (da | db) else 0.0
            same_name = items[a]["eng"] == items[b]["eng"]
            if same_name or (jac >= 0.5 and inter >= 3):
                links.append({"a": a, "b": b, "jaccard": round(jac, 2), "shared": inter, "same_name": same_name})
                parent[find(a)] = find(b)
    groups = {}
    for f in names:
        groups.setdefault(find(f), []).append(f)
    clusters = sorted((sorted(g) for g in groups.values() if len(g) > 1), key=lambda g: (-len(g), g))
    return {"families": len(names), "links": links, "clusters": clusters}


def pair(a: str, b: str, via: Path = VIA, ledger: Path | None = None) -> dict:
    T, SM = tm(), shadow()
    fams, _sk, _ex = T.discover(via)
    if a not in fams or b not in fams:
        return {"a": a, "b": b, "verdict": "ABSENT", "why": "家族不在(用家族名,不含 _vNNNN)"}
    ta, tb = fams[a]["tail"], fams[b]["tail"]
    OUT.mkdir(parents=True, exist_ok=True)
    res = SM.run(ta, tb, OUT / "pairs")
    verdict = (res.get("proof") or {}).get("verdict") or "?"
    cnt = res.get("counts") or {}
    rec = {"ts": T.utc_now(), "event": "pair", "a": a, "b": b, "a_tail": ta.name, "b_tail": tb.name,
           "verdict": verdict, "classes": cnt,
           "shadow": str(res.get("shadow") or res.get("out") or res.get("dir") or ""), "originals_unchanged": res.get("originals_unchanged"),
           "next": "PROVEN_ZERO_LOSS → WKF045 ⑨–⑫ 升一個最強模組" if verdict == "PROVEN_ZERO_LOSS" else "BLOCKED → 逐群裁定(L75);原檔不動",
           "by": "%s %s" % (NAME, VERSION)}
    if ledger is not None:
        with open(ledger, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def render(rep: dict) -> str:
    T = tm()
    vl = T.visual_lock(VIA)
    t, pill = T.t, T.pill
    lamp = {"PROVEN_ZERO_LOSS": "GREEN", "BLOCKED_NEEDS_RULING": "YELLOW"}
    h = ['<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">',
         '<title>VCGC 類似功能收斂</title><style>', vl.get("kit", ""), T.EXTRA_CSS, '</style></head><body>',
         '<header class="vl-topbar"><h1>VCGC 類似功能收斂</h1><div class="vl-kpis">']
    for label, val in (("家族", rep["census"]["families"]), ("類似群", len(rep["census"]["clusters"])), ("比對", len(rep["pairs"])),
                       ("零遺失可合", sum(1 for p in rep["pairs"] if p["verdict"] == "PROVEN_ZERO_LOSS")),
                       ("待裁定", sum(1 for p in rep["pairs"] if p["verdict"] != "PROVEN_ZERO_LOSS"))):
        h.append('<div class="vl-kpi"><span class="vl-label">%s</span><span class="vl-value">%s</span></div>' % (t(label), t(val)))
    h.append('</div></header><p class="vl-sub">%s %s · %s · 清點 → AST / 編號 / 註冊體檢 → 複製到 TEMP 影子區 → 逐定義比對 → 零遺失證明 → 一個最強模組候選</p>'
             % (t(NAME), t(VERSION), t(rep["at"])))
    h.append('<div class="vl-board"><div class="vl-panel" data-span="12"><div class="vl-head"><h2>比對結果(卡片)</h2></div><div class="vl-grid">')
    for p in rep["pairs"]:
        h.append('<div class="vl-cell"><span class="vl-label">%s × %s</span><span class="vl-value">%s %s</span><span class="vl-note">%s</span></div>'
                 % (t(p["a"]), t(p["b"]), pill(lamp.get(p["verdict"], "RED"), p["verdict"]), t(" · ".join("%s %s" % kv for kv in sorted(p["classes"].items()))), t(p["next"])))
    h.append('</div></div><div class="vl-panel" data-span="12"><div class="vl-head"><h2>類似群(全景清點)</h2></div><div class="vl-scroll"><table><thead><tr>'
             '<th>群</th><th>家族</th></tr></thead><tbody>')
    for i, g in enumerate(rep["census"]["clusters"], 1):
        h.append('<tr><td class="vl-num">%d</td><td class="vm-mono">%s</td></tr>' % (i, t(" · ".join(g))))
    h.append('</tbody></table></div></div></div><footer class="vl-foot">原檔不動 · 只寫 VIA_Reports/converge/ 與收斂帳 · 證不出零遺失 = 不合(L75)</footer></body></html>')
    return "".join(h), vl


def run_all(top: int = 20, via: Path = VIA) -> tuple:
    T = tm()
    cen = census(via)
    led = HERE / LEDGER if via == VIA else via / "supportive modules" / "registry" / LEDGER
    pairs = []
    for g in cen["clusters"][:top]:
        try:
            pairs.append(pair(g[0], g[1], via, led))
        except Exception as exc:  # noqa: BLE001 — 一對出錯只記那一對,整輪照跑(照實列 ERROR,不冒充)
            pairs.append({"a": g[0], "b": g[1], "verdict": "ERROR", "classes": {}, "next": "%s: %s" % (type(exc).__name__, exc)})
    rep = {"tool": "%s %s" % (NAME, VERSION), "at": T.utc_now(), "census": cen, "pairs": pairs}
    OUT.mkdir(parents=True, exist_ok=True)
    page, vl = render(rep)
    hp = OUT / "CONVERGE_latest.html"
    hp.write_text(page, encoding="utf-8")
    gate = vl["mod"].check_page(hp, vl["sha256"]) if vl.get("mod") else {"lamp": "RED", "findings": ["視覺鎖定不可用"]}
    rep["visual_lock_gate"] = gate["lamp"]
    (OUT / "CONVERGE_latest.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=list), encoding="utf-8")
    return rep, gate


def selftest() -> int:
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""), flush=True)
    with tempfile.TemporaryDirectory(prefix="via_converge_") as td:
        p = Path(td) / "x_v0100.py"
        p.write_text("def a():\n    return 1\nclass B:\n    pass\ndef main():\n    pass\n", encoding="utf-8")
        chk("① AST 頂層定義(去掉 main / selftest 等共用名)", defs_of(p) == {"a", "B"}, defs_of(p))
    cen = census()
    chk("② 真樹全景清點:家族 ≥ 280 · 找得到類似群 · 同英文名的兩支(AccelCoverage)在同一群",
        cen["families"] >= 280 and cen["clusters"] and any({"CGC_MDL103_AccelCoverage", "CGC_MDL117_AccelCoverage"} <= set(g) for g in cen["clusters"]),
        "家族 %d · 群 %d" % (cen["families"], len(cen["clusters"])))
    fams, _a, _b = tm().discover()
    before = {f: fams[f]["tail"].read_bytes() for f in ("CGC_MDL103_AccelCoverage", "CGC_MDL117_AccelCoverage")}
    rec = pair("CGC_MDL103_AccelCoverage", "CGC_MDL117_AccelCoverage")
    after = {f: fams[f]["tail"].read_bytes() for f in before}
    chk("③ pair:複製到影子區比對、給判決(PROVEN / BLOCKED)· 原檔位元組不變",
        rec["verdict"] in ("PROVEN_ZERO_LOSS", "BLOCKED_NEEDS_RULING") and before == after, rec["verdict"])
    page, vl = render({"at": "t", "census": cen, "pairs": [rec]})
    with tempfile.TemporaryDirectory(prefix="via_converge_html_") as td:
        hp = Path(td) / "c.html"
        hp.write_text(page, encoding="utf-8")
        gate = vl["mod"].check_page(hp, vl["sha256"]) if vl.get("mod") else {"lamp": "RED"}
    chk("④ 出頁走操作員視覺鎖定 U/I · 鎖定閘 GREEN", gate["lamp"] == "GREEN", gate.get("findings"))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑤ 加速器橋在 · 不碰 TA-Lib · 不直派子行程", "[VIA:ACCEL-BRIDGE" in src and not re.search(r"^\s*(import|from)\s+(talib|subprocess)\b", src, re.M))
    bad = len(ok) - sum(ok)
    print("[%s] %s %s --selftest · %d/%d" % ("PASS" if not bad else "FAIL", NAME, VERSION, len(ok) - bad, len(ok)), flush=True)
    return 0 if not bad else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in ("-h", "help"):
        print(__doc__)
        return 0
    if "--selftest" in args:
        return selftest()
    if args[0] == "census":
        cen = census()
        if "--json" in args:
            print(json.dumps(cen, ensure_ascii=False, indent=1))
        else:
            print("[%s census] 家族 %d · 類似群 %d · 連結 %d" % (NAME, cen["families"], len(cen["clusters"]), len(cen["links"])), flush=True)
            for i, g in enumerate(cen["clusters"], 1):
                print("  群%02d %s" % (i, " · ".join(g)), flush=True)
        return 0
    if args[0] == "pair" and len(args) >= 3:
        rec = pair(args[1], args[2], ledger=HERE / LEDGER)
        print(json.dumps(rec, ensure_ascii=False, indent=1), flush=True)
        return 0 if rec["verdict"] == "PROVEN_ZERO_LOSS" else 1
    if args[0] == "all":
        top = int(args[args.index("--top") + 1]) if "--top" in args else 20
        rep, gate = run_all(top)
        print("[%s all] 群 %d · 比對 %d · 零遺失可合 %d · 待裁定 %d · 鎖定閘 %s\n  頁 %s" % (
            NAME, len(rep["census"]["clusters"]), len(rep["pairs"]), sum(1 for p in rep["pairs"] if p["verdict"] == "PROVEN_ZERO_LOSS"),
            sum(1 for p in rep["pairs"] if p["verdict"] != "PROVEN_ZERO_LOSS"), gate["lamp"], OUT / "CONVERGE_latest.html"), flush=True)
        return 0 if gate["lamp"] == "GREEN" else 1
    print("[%s] 不認得:%s(census · pair · all · --selftest)" % (NAME, args[0]), flush=True)
    return 2


if __name__ == "__main__":
    sys.exit(main())
