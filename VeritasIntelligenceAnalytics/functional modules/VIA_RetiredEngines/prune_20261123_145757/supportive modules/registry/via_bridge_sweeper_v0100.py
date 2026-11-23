#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
via_bridge_sweeper — 雙橋統包清掃器(批127;via-sweep)
====================================================================
操作員令(批127,2026-08-24):「每個模組引擎都要掛加速器;凡向外部
API 要資料的都要用網路工具;整合、自動化」。
本器=單一自動工具,一次掃描全樹活動圈:
  ① ACCEL 橋 — 缺 [VIA:ACCEL-BRIDGE] 的活動 py 補掛(graceful 零行為)
  ② NET 橋 — 有外呼 import(urllib/requests/yfinance/akshare/playwright
     /httpx/aiohttp/websocket)而缺 [VIA:NET-BRIDGE] 的活動 py 補掛
     (統包 SUP_MDL740 惰性定位;法遵雙閘在統包端)
豁免圈(誠實列示,零觸碰):
  · EXEMPT_INTAKE — 原件收容區(new modules engines/v42 生態包/爬蟲
    雙引擎包/TALib vendor/dict/50_Protection/Standalone/docs history/
    references intake/_rebuilds/_from_vap_iso_cleanup):正本不就地修改
  · EXEMPT_SELF — 網路/加速統包家族自身(SUP_MDL737/740/Celeritas/
    AegisNexus/via_net_unified/VIA_SuperAccel_Module/VIA_NetSupport)
  · EXEMPT_LEGACY_NET — supportive modules/network 收容 legacy(統包涵蓋)
鐵則:注入前後雙 ast.parse,後驗敗不落檔;manifest+--undo 可逆;冪等。
用法:
  via-sweep --audit     → 只量測覆蓋(零寫入)
  via-sweep --run       → 雙橋補掛
  via-sweep --undo <manifest>
  via-sweep --selftest  → 八檢(沙盒零網路)
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
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
RUNS = VIA / "VIA_Reports" / "bridge_sweep_runs"

SKIP_FRAGS = ("_sha", "__pycache__", ".venv", "site-packages", "quarantine",
              "_review_quarantine", "rename_runs", "rollback", "_syntaxfix_",
              "evidence", "SCOPE_COPY", "backup_", "VIA_Reports",
              "_via_mother_root_reconciliation_runs", "package_samples", "_vdf_envs")
EXEMPT_INTAKE = ("new modules engines", "VeritasAutoPlot_v42_EcoSystem",
                 "webscraping_dualengine", "TALib/vendor", "/dict/",
                 "50_Protection_Acceleration", "VIA_Standalone_Package",
                 "docs/history", "references/intake", "_rebuilds_superseded",
                 "_from_vap_iso_cleanup", "_inbox_to_classify")
EXEMPT_SELF = ("SUP_MDL737_SuperAccelModule", "SUP_MDL740_NetUnified",
               "via_net_unified", "VIA_SuperAccel_Module", "VeritasCeleritas",
               "VeritasAegisNexus", "VIA_NetSupport", "via_bridge_sweeper")
EXEMPT_LEGACY_NET = ("supportive modules/network/",)

NET_IMPORT_RX = re.compile(
    r"^\s*(?:import|from)\s+(urllib|requests|httpx|aiohttp|yfinance|akshare|playwright|websockets?)\b", re.M)
ACCEL_MARK = "[VIA:ACCEL-BRIDGE"
NET_MARK = "[VIA:NET-BRIDGE"
ACCEL_END = "# ===== [VIA:ACCEL-BRIDGE:END] ====="

ACCEL_BRIDGE = '''# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
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
'''

NET_BRIDGE = '''# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====
'''


def _sha16(t: str) -> str:
    return hashlib.sha256(t.encode("utf-8", "replace")).hexdigest()[:16]


def classify(rp: str) -> str:
    """回 ACTIVE / SKIP / EXEMPT_*(誠實圈)"""
    r = rp.replace("\\", "/")
    if any(f in r for f in SKIP_FRAGS):
        return "SKIP"
    if any(f in r for f in EXEMPT_INTAKE):
        return "EXEMPT_INTAKE"
    if any(Path(r).name.startswith(x) or x in Path(r).stem for x in EXEMPT_SELF):
        return "EXEMPT_SELF"
    if any(r.startswith(x) or f"/{x}" in "/" + r for x in EXEMPT_LEGACY_NET):
        return "EXEMPT_LEGACY_NET"
    return "ACTIVE"


def audit(root: Path = VIA) -> dict:
    """覆蓋量測(零寫入)"""
    out = {"active": 0, "accel_have": 0, "accel_miss": [], "net_need": 0,
           "net_have": 0, "net_miss": [], "exempt": {"EXEMPT_INTAKE": 0,
           "EXEMPT_SELF": 0, "EXEMPT_LEGACY_NET": 0}}
    for p in root.rglob("*.py"):
        rp = str(p.relative_to(root))
        cls = classify(rp)
        if cls == "SKIP":
            continue
        if cls != "ACTIVE":
            out["exempt"][cls] += 1
            continue
        try:
            t = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        out["active"] += 1
        if ACCEL_MARK in t:
            out["accel_have"] += 1
        else:
            out["accel_miss"].append(rp)
        if NET_IMPORT_RX.search(t):
            out["net_need"] += 1
            if NET_MARK in t:
                out["net_have"] += 1
            else:
                out["net_miss"].append(rp)
    return out


def _insert_line(text: str, tree, after_accel: bool) -> int:
    lines = text.splitlines()
    if after_accel:
        for i, ln in enumerate(lines):
            if ACCEL_END in ln:
                return i + 1
    last = 0
    for i, ln in enumerate(lines[:3]):
        s = ln.strip()
        if s.startswith("#!") or ("coding" in s and s.startswith("#")):
            last = i + 1
    if tree.body and isinstance(tree.body[0], ast.Expr) and \
            isinstance(getattr(tree.body[0], "value", None), ast.Constant) and \
            isinstance(tree.body[0].value.value, str):
        last = max(last, tree.body[0].end_lineno)
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            last = max(last, node.end_lineno)
    return last


def inject_one(p: Path, rp: str, bridge: str, mark: str, after_accel: bool) -> dict:
    text = p.read_text(encoding="utf-8", errors="ignore")
    if mark in text:
        return {"rel": rp, "bridge": mark, "state": "SKIP", "note": "已橋"}
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return {"rel": rp, "bridge": mark, "state": "SKIP", "note": f"不可解析:{str(exc)[:40]}"}
    at = _insert_line(text, tree, after_accel)
    lines = text.splitlines(keepends=True)
    new = "".join(lines[:at]) + bridge + "".join(lines[at:])
    try:
        ast.parse(new)
    except SyntaxError:
        return {"rel": rp, "bridge": mark, "state": "FAIL", "note": "後驗敗,不落檔"}
    pre = _sha16(text)
    p.write_text(new, encoding="utf-8")
    return {"rel": rp, "bridge": mark, "state": "OK", "pre": pre, "post": _sha16(new)}


def run(root: Path = VIA, out_runs: Path | None = None) -> int:
    a = audit(root)
    print(f"=== 雙橋清掃器(批127)· 活動 {a['active']} · 補加速 {len(a['accel_miss'])}"
          f" · 補網路 {len(a['net_miss'])} · 豁免 {a['exempt']} ===")
    results = []
    n_ok = n_skip = n_fail = 0
    for rp in a["accel_miss"]:
        r = inject_one(root / rp, rp, ACCEL_BRIDGE, ACCEL_MARK, after_accel=False)
        results.append(r)
        n_ok += r["state"] == "OK"; n_skip += r["state"] == "SKIP"; n_fail += r["state"] == "FAIL"
    for rp in a["net_miss"]:
        r = inject_one(root / rp, rp, NET_BRIDGE, NET_MARK, after_accel=True)
        results.append(r)
        n_ok += r["state"] == "OK"; n_skip += r["state"] == "SKIP"; n_fail += r["state"] == "FAIL"
    rd = out_runs or RUNS
    rd.mkdir(parents=True, exist_ok=True)
    mf = rd / f"SWEEP_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    mf.write_text(json.dumps({"schema": "via.bridgesweep.v1", "audit_before": {
        k: (len(v) if isinstance(v, list) else v) for k, v in a.items()},
        "results": results}, ensure_ascii=False, indent=1), encoding="utf-8")
    a2 = audit(root)
    print(f"  [計] 注入 {n_ok} · 跳 {n_skip} · 敗 {n_fail} · manifest {mf.name}")
    print(f"  [後測] 活動 {a2['active']} · 加速缺 {len(a2['accel_miss'])}"
          f" · 網路缺 {len(a2['net_miss'])}(0=全覆蓋)")
    return 1 if n_fail else 0


def undo(manifest: str) -> int:
    d = json.loads(Path(manifest).read_text(encoding="utf-8"))
    n_un = n_skip = 0
    for r in d["results"]:
        if r["state"] != "OK":
            continue
        p = VIA / r["rel"]
        if not p.exists():
            n_skip += 1
            continue
        t = p.read_text(encoding="utf-8", errors="ignore")
        if _sha16(t) != r["post"]:
            n_skip += 1
            continue
        mark = r["bridge"]
        start = "# ===== [VIA:NET-BRIDGE:v0100]" if mark == NET_MARK else "# ===== [VIA:ACCEL-BRIDGE:v0100]"
        endtag = "# ===== [VIA:NET-BRIDGE:END] =====" if mark == NET_MARK else ACCEL_END
        i0 = t.index(start)
        i1 = t.index(endtag) + len(endtag) + 1
        p.write_text(t[:i0] + t[i1:], encoding="utf-8")
        n_un += 1
    print(f"  [undo] 還原 {n_un} · 略過 {n_skip}(已變動/缺=誠實不動)")
    return 0


def selftest() -> int:
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    chk("① 豁免分類(收容/自身/legacy/SKIP/ACTIVE)",
        classify("new modules engines/x.py") == "EXEMPT_INTAKE"
        and classify("supportive modules/SUP_MDL737_SuperAccelModule_v0100.py") == "EXEMPT_SELF"
        and classify("supportive modules/network/SUP_MDL620_x.py") == "EXEMPT_LEGACY_NET"
        and classify("functional modules/VAP/ASSETS/SCOPE_COPY/y.py") == "SKIP"
        and classify("functional modules/VRN/a.py") == "ACTIVE")
    with tempfile.TemporaryDirectory() as td:
        sand = Path(td)
        (sand / "functional modules/X").mkdir(parents=True)
        f1 = sand / "functional modules/X/eng_net.py"
        f1.write_text('"""doc"""\nimport urllib.request\n', encoding="utf-8")
        f2 = sand / "functional modules/X/eng_plain.py"
        f2.write_text('"""doc"""\nx = 1\n', encoding="utf-8")
        f3 = sand / "functional modules/X/broken.py"
        f3.write_text("def broken(:\n", encoding="utf-8")
        a0 = audit(sand)
        chk("② audit(2 缺加速·1 外呼缺網)", len(a0["accel_miss"]) >= 2
            and len(a0["net_miss"]) == 1 and a0["net_need"] == 1)
        rc = run(sand, out_runs=sand / "runs")
        t1 = f1.read_text(encoding="utf-8")
        chk("③ 雙橋注入(net 件=雙橋·先 ACCEL 後 NET)", rc == 0
            and ACCEL_MARK in t1 and NET_MARK in t1
            and t1.index(ACCEL_MARK) < t1.index(NET_MARK))
        chk("④ 純件只掛加速橋", ACCEL_MARK in f2.read_text(encoding="utf-8")
            and NET_MARK not in f2.read_text(encoding="utf-8"))
        chk("⑤ 壞檔誠實 SKIP+後驗 ast 全過",
            all(bool(ast.parse(f.read_text(encoding="utf-8"))) for f in (f1, f2))
            and ACCEL_MARK not in f3.read_text(encoding="utf-8"))
        a1 = audit(sand)
        chk("⑥ 後測全覆蓋(缺=0;壞檔除外)",
            [x for x in a1["accel_miss"] if "broken" not in x] == [] and a1["net_miss"] == [])
        rc2 = run(sand, out_runs=sand / "runs")
        chk("⑦ 冪等(再跑零注入)", rc2 == 0
            and f1.read_text(encoding="utf-8").count(ACCEL_MARK) == 2)  # 塊頭+END 各含 MARK 前綴一次
        ns = {"__file__": str(f1)}
        exec(compile(f1.read_text(encoding="utf-8").split("import urllib")[0], "x", "exec"), ns)
        chk("⑧ 沙盒橋 graceful(兩態合法·NET 統包缺=None)",
            "VIA_ACCEL" in ns and ns["VIA_NET_TOOL_PATH"] is None
            and ns["_via_net"]() is None)
    n = 8 - len(fails)
    print(f"  [計] 八檢 OK {n} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 雙橋清掃器 · 八檢自測(沙盒零網路)===")
        return selftest()
    if "--undo" in args:
        i = args.index("--undo")
        return undo(args[i + 1])
    if "--audit" in args:
        a = audit()
        print(json.dumps({k: (len(v) if isinstance(v, list) else v) for k, v in a.items()},
                         ensure_ascii=False, indent=1))
        print("加速缺件:", *a["accel_miss"][:10], sep="\n  ")
        return 0
    return run()


if __name__ == "__main__":
    sys.exit(main())
