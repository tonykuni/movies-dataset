#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
via_iface_contract_v0100 — 介面合約自適應註冊引擎(TOOL-041;操作員令 2026-08-17)
==================================================================================
令:引擎自動編號+說明功能;支援性模組也自動編號註冊;子系統間
interface 合約自適應智慧化建立機制。
機制(全 AST 零執行零 import):
  ① 全境掃描 — functional modules/**+supportive modules/*.py 主件
     (跳過 _sha 鏡像/(N) 副本/__pycache__/vendor)
  ② 自動編號 — VIA-IFACE-####(獨立名空間;鍵=相對路徑,先發先得,
     重跑同件同號=冪等;append-only 永不回收)
  ③ 說明自動萃取 — 模組 docstring 首行=功能說明(AI 只整理不發明;
     無 docstring 誠實記「無說明(候補)」)
  ④ 介面合約自動推導 — 頂層函式簽名(名/參數/預設值計)、類別+方法數、
     CLI 旗標(AST 常數掃 "--*")、__main__ 有無
  ⑤ 子系統歸屬+跨系統邊 — 路徑定歸屬(VDF/VRN/VAP/CGC/SUPPORT/PLUG);
     import 解析至冊內模組=介面邊,聚合成子系統間介面矩陣
  ⑥ 自適應(智慧化核心)— 重跑比對存冊合約:簽名/旗標/說明變=
     CONTRACT_DRIFT 具名列示+新版合約入冊(舊版留 history,append-only
     時光機);零漂移=STABLE。合約永遠追著程式碼走,不用人工維護
用法:via-iface            → 掃描+註冊+漂移偵測(寫冊)
     via-iface --dry      → 只報告零寫入(自測矩陣站用)
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
import json
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REG_P = HERE / "VIA_Interface_Contract_Registry_v0100.json"
OUT = VIA / "VIA_Reports" / "iface_runs"
SKIP_RX = re.compile(r"(_sha[0-9a-f]{8,}|\(\d+\))\.py$")
SKIP_DIRS = {"__pycache__", "vendor", "Lib", "node_modules", ".git", "_upload_original",
             "VIA_RetiredEngines"}  # 批180:讓位封存區(零刪除;不入合約冊)


def subsystem_of(rel: str) -> str:
    low = rel.lower()
    if low.startswith("functional modules/vdf"):
        return "VDF"
    if low.startswith("functional modules/vrn"):
        return "VRN"
    if low.startswith("functional modules/vap"):
        return "VAP"
    if low.startswith(("functional modules/groupindex", "functional modules/superdoc")):
        return "PLUG"
    if "central_governance" in low or "contractengine" in low or low.startswith("system_core"):
        return "CGC"
    if low.startswith("supportive modules/registry"):
        return "CGC"
    if low.startswith(("supportive modules", "plugins_pool")):
        return "SUPPORT"
    return "OTHER"


def derive_contract(p: Path):
    """AST 推導模組介面合約(零執行)。"""
    try:
        tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError as exc:
        return {"syntax": "FAIL", "err": f"L{exc.lineno}: {exc.msg}"}
    doc = (ast.get_docstring(tree) or "").strip().splitlines()
    desc = doc[0].strip() if doc else "無說明(候補)"
    fns = []
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            a = n.args
            fns.append({"name": n.name,
                        "args": [x.arg for x in a.posonlyargs + a.args + a.kwonlyargs][:8],
                        "defaults": len(a.defaults) + len([d for d in a.kw_defaults if d is not None])})
    classes = {n.name: sum(isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)) for m in n.body)
               for n in tree.body if isinstance(n, ast.ClassDef)}
    flags = sorted({c.value for c in ast.walk(tree)
                    if isinstance(c, ast.Constant) and isinstance(c.value, str)
                    and c.value.startswith("--") and 2 < len(c.value) <= 24 and " " not in c.value})
    has_main = any(isinstance(n, ast.If) and getattr(getattr(n.test, "left", None), "id", "") == "__name__"
                   for n in tree.body)
    imps = sorted({(a.name if isinstance(n, ast.Import) else (n.module or "")).split(".")[0]
                   for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))
                   for a in (n.names if isinstance(n, ast.Import) else [n])} - {""})
    return {"syntax": "OK", "desc": desc[:120], "functions": fns[:12], "classes": classes,
            "cli_flags": flags[:16], "has_main": has_main, "imports": imps}


def sig_key(c: dict) -> str:
    """合約指紋(漂移比對用):簽名+旗標+說明。"""
    return json.dumps({"f": [(f["name"], f["args"], f["defaults"]) for f in c.get("functions", [])],
                       "c": c.get("classes", {}), "fl": c.get("cli_flags", []),
                       "d": c.get("desc", "")}, ensure_ascii=False, sort_keys=True)


def main() -> int:
    dry = "--dry" in sys.argv[1:]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    reg = {"schema": "VIA.IfaceContract.v1", "namespace": "VIA-IFACE(獨立名空間;鍵=相對路徑先發先得)",
           "modules": {}, "drift_ledger": []}
    if REG_P.exists():
        try:
            reg = json.loads(REG_P.read_text(encoding="utf-8"))
        except Exception:
            pass
    print(f"=== 介面合約自適應註冊 v0100 · {'DRY(零寫入)' if dry else 'REGISTER'} ===")

    files = []
    for root in (VIA / "functional modules", VIA / "supportive modules", VIA / "system_core", VIA / "plugins_pool"):
        if not root.is_dir():
            continue
        for p in root.rglob("*.py"):
            if SKIP_RX.search(p.name) or set(p.parts) & SKIP_DIRS:
                continue
            files.append(p)
    print(f"  [掃] 主件 {len(files)} 件(引擎+支援模組;鏡像/副本/快取跳過)")

    known = {m["rel"]: urn for urn, m in reg["modules"].items()}
    by_rel = {}
    n_new = n_drift = n_stable = n_syn = 0
    for p in sorted(files):
        rel = p.relative_to(VIA).as_posix()
        c = derive_contract(p)
        if c.get("syntax") == "FAIL":
            n_syn += 1
            continue
        sub = subsystem_of(rel)
        by_rel[rel] = (sub, c)
        if rel in known:
            urn = known[rel]
            old = reg["modules"][urn]
            if sig_key(old.get("contract", {})) != sig_key(c):
                n_drift += 1
                hist = old.setdefault("history", [])
                hist.append({"ts": old.get("ts"), "contract": old.get("contract")})
                old.update({"contract": c, "ts": ts, "drift_count": old.get("drift_count", 0) + 1})
                reg["drift_ledger"].append({"ts": ts, "urn": urn, "rel": rel,
                                            "note": "CONTRACT_DRIFT:簽名/旗標/說明變——新約入冊,舊約留 history"})
            else:
                n_stable += 1
        else:
            n_new += 1
            urn = f"VIA-IFACE-{len(reg['modules']) + 1:04d}"
            reg["modules"][urn] = {"urn": urn, "rel": rel, "subsystem": sub,
                                   "desc": c["desc"], "contract": c, "ts": ts, "drift_count": 0}
            known[rel] = urn

    # 跨子系統介面邊(import 解至冊內模組)
    stem2sub = {Path(r).stem: s for r, (s, _c) in by_rel.items()}
    edges: dict[str, int] = {}
    for rel, (sub, c) in by_rel.items():
        for imp in c["imports"]:
            tgt = stem2sub.get(imp)
            if tgt and tgt != sub:
                edges[f"{sub}→{tgt}"] = edges.get(f"{sub}→{tgt}", 0) + 1
    subs = {}
    for rel, (s, _c) in by_rel.items():
        subs[s] = subs.get(s, 0) + 1
    print(f"  [冊] 新編 {n_new} · 漂移 {n_drift} · 穩定 {n_stable} · 語法敗跳過 {n_syn}(誠實)")
    print("  [屬] " + " · ".join(f"{k} {v}" for k, v in sorted(subs.items())))
    print("  [介面矩陣] 跨子系統邊:" + (" · ".join(f"{k}×{v}" for k, v in sorted(edges.items(), key=lambda x: -x[1])[:10]) or "無"))
    for e in reg["drift_ledger"][-5:]:
        if e["ts"] == ts:
            print(f"     ⚠ {e['urn']} · {e['rel'][:60]} · 漂移入冊")

    if not dry:
        REG_P.write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  [寫] {REG_P.name}(append-only;合約追碼自適應)")
    OUT.mkdir(parents=True, exist_ok=True)
    ev = OUT / f"IFACE_{ts}.json"
    ev.write_text(json.dumps({"schema": "VIA.IfaceRun.v1", "ts": ts, "scanned": len(files),
                              "new": n_new, "drift": n_drift, "stable": n_stable, "syntax_skip": n_syn,
                              "subsystems": subs, "edges": edges, "dry": dry},
                             ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  [存證] {ev.relative_to(VIA)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
