#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CGC_MDL054_IfaceContract v0103 — 介面合約自適應(批514:--need 寬收;九檢)
v0102→v0103(批514 操作員實錄 connect need ['首頁 ocr'] 命中 0):split_need() 逗號/空白/分號/全形逗號/頓號皆可;Register v0203 端亦以逗號合回陣列;+⑨。
CGC_MDL054_IfaceContract v0102(批513) — 介面合約自適應註冊引擎(TOOL-041;批513 +綁定合約層 sync/connect/graft)
v0101→v0102(批513 操作員令「未來所有引擎會因為不同需求彈性調配嫁接,interface 合約自適應式 connect sync 功能要強大完善」;L30 整合:不另起第四套,
  在冊的擁有者 MDL054 上加綁定合約層):主控台冊 VIA_InputConsole_Spec(id→引擎 glob/verb/params/outputs=匯流排真正執行的合約)× 尾版引擎 AST 合約——
  sync(VERB_DRIFT/PARAM_DRIFT/ENGINE_ABSENT/VERSION_BUMP/未暴露旗標;--apply 只增 contract+contract_history)· connect --need(嫁接候選,只列)·
  graft --item --engine(換引擎前驗相容;--apply 只增 graft_candidates)· status;九檢自測。舊 scan/--dry 照舊。
  執行期模組對模組自湊(mapping/connecting/syncing)= via_iface_autosync(TOOL-089)既有站,互補不重疊。
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
用法:via-iface [scan]     → 掃描+註冊+漂移偵測(寫冊)
     via-iface --dry      → 只報告零寫入(自測矩陣站用)
     via-iface sync [--apply] · connect --need a,b [--family vdf] · graft --item ID --engine GLOB [--dir D] [--apply] · status · --selftest
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


def do_scan(dry: bool) -> int:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    reg = {"schema": "VIA.IfaceContract.v1", "namespace": "VIA-IFACE(獨立名空間;鍵=相對路徑先發先得)",
           "modules": {}, "drift_ledger": []}
    if REG_P.exists():
        try:
            reg = json.loads(REG_P.read_text(encoding="utf-8"))
        except Exception:
            pass
    print(f"=== 介面合約自適應註冊 v0102 · {'DRY(零寫入)' if dry else 'REGISTER'} ===")

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


# ═════════════════════════════════════════════════════════
# v0102(批513 操作員令「未來所有引擎會因為不同需求彈性調配嫁接,interface 合約自適應式 connect sync 功能要強大完善」)
#   綁定合約層:主控台冊 VIA_InputConsole_Spec(id→引擎 glob/verb/params/outputs=匯流排真正執行的合約)× 尾版引擎 AST 合約(cli_flags)
#   sync   逐項比對:verb 旗標/params 旗標是否真在尾版引擎裡(VERB_DRIFT/PARAM_DRIFT)、引擎不在(ENGINE_ABSENT)、版號跳(VERSION_BUMP)、
#          引擎有旗標冊沒暴露(UNEXPOSED);--apply 只增:項下加 contract{engine_file,flags,ts,state,drift}+contract_history
#   connect --need 關鍵字 [--family]:依合約(路徑/說明/旗標/冊 zh/outputs)找可嫁接的引擎,列綁定 argv(只列不寫)
#   graft --item ID --engine GLOB [--dir]:換引擎前先驗相容(verb/params 旗標在不在候選引擎裡);--apply 只增 graft_candidates
#   status:讀 BINDING_SYNC_latest.json。全 AST 零執行零 import;寫入只在 --apply 且 append-only。
# ═════════════════════════════════════════════════════════
SPEC_GLOB = "VIA_InputConsole_Spec_v*.json"
FAMILY_SCAN_DIRS = {"vdf": ["functional modules/VDF/engine", "functional modules/VDF"], "vrn": ["functional modules/VRN"], "vap": ["functional modules/VAP/engine"]}
COMMON_FLAGS = {"--selftest", "--self-test", "--json", "--help", "--quiet", "--dry", "--dry-run", "--force", "--verbose"}
_VER_RX = re.compile(r"_v\d{3,4}(?=\.py$)")
_FLAG_RX = re.compile(r"--[a-z0-9][a-z0-9-]*")


def _newest_in(d: Path, pat: str):
    hits = sorted(d.glob(pat)) if d.is_dir() else []
    return hits[-1] if hits else None


def load_spec(path: Path | None = None) -> tuple[dict, Path | None]:
    p = path or _newest_in(HERE, SPEC_GLOB)
    if not p or not p.exists():
        return {}, None
    try:
        return json.loads(p.read_text(encoding="utf-8")), p
    except Exception:
        return {}, p


def spec_items(spec: dict) -> list:
    out = []
    for fam, fv in (spec.get("families") or {}).items():
        groups = fv.get("groups") or []
        for g in (groups if isinstance(groups, list) else groups.values()):
            for it in (g.get("items") or []):
                out.append((fam, g.get("id", ""), it))
    return out


def resolve_engine(item: dict, root: Path | None = None):
    eng = item.get("engine") or {}
    d = (root or VIA) / str(eng.get("dir") or "")
    return _newest_in(d, str(eng.get("glob") or "")) if eng.get("glob") else None


def param_flags(kind: str, spec: dict) -> list:
    txt = (spec.get("param_kinds") or {}).get(kind, "")
    fl = _FLAG_RX.findall(txt)
    if fl:
        return sorted(set(fl))
    if kind in ("code", "codes"):
        return []                                  # 位置參數/代碼冊:不以旗標驗
    return [f"--{kind}"]


def sync_item(fam: str, item: dict, spec: dict, root: Path | None = None) -> dict:
    rec = {"id": item.get("id"), "family": fam, "engine_file": "", "state": "OK", "drift": [], "flags": [], "unexposed": []}
    p = resolve_engine(item, root)
    if not p:
        rec.update(state="ENGINE_ABSENT", drift=[f"尾版引擎不在:{(item.get('engine') or {}).get('dir')}/{(item.get('engine') or {}).get('glob')}"])
        return rec
    rec["engine_file"] = p.name
    c = derive_contract(p)
    if c.get("syntax") != "OK":
        rec.update(state="SYNTAX_FAIL", drift=[f"AST 解析失敗:{c.get('err')}"])
        return rec
    flags = set(c.get("cli_flags") or [])
    rec["flags"] = sorted(flags)[:24]
    verb = [v for v in ((item.get("engine") or {}).get("verb") or []) if isinstance(v, str) and v.startswith("--")]
    miss_v = [v for v in verb if v not in flags]
    if miss_v:
        rec["drift"].append("VERB_DRIFT:冊 verb 旗標不在引擎裡 " + ",".join(miss_v))
    miss_p = []
    for k in (item.get("params") or []):
        kind = k if isinstance(k, str) else str((k or {}).get("kind", ""))
        for f in param_flags(kind, spec):
            if f not in flags:
                miss_p.append(f"{kind}→{f}")
    if miss_p:
        rec["drift"].append("PARAM_DRIFT:冊 params 旗標不在引擎裡 " + ",".join(miss_p))
    prev = (item.get("contract") or {}).get("engine_file")
    if prev and prev != p.name:
        rec["drift"].append(f"VERSION_BUMP:上次綁 {prev} → 尾版 {p.name}(合約自動追尾版;請看 UNEXPOSED)")
    exposed = set(verb) | {f for k in (item.get("params") or []) for f in param_flags(k if isinstance(k, str) else str((k or {}).get("kind", "")), spec)}
    rec["unexposed"] = sorted(flags - exposed - COMMON_FLAGS)[:12]
    if any(d.startswith(("VERB_DRIFT", "PARAM_DRIFT")) for d in rec["drift"]):
        rec["state"] = "DRIFT"
    elif rec["drift"]:
        rec["state"] = "BUMP"
    return rec


def do_sync(apply: bool, spec_path: Path | None = None, root: Path | None = None, do_print: bool = True) -> dict:
    spec, sp = load_spec(spec_path)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    rep = {"schema": "VIA.IfaceBindingSync.v1", "ts": ts, "spec": (sp.name if sp else None), "items": [], "counts": {}, "applied": False}
    if not spec:
        rep["state"] = "ABSENT"
        if do_print:
            print("  [綁定合約] 主控台冊缺(VIA_InputConsole_Spec_v*.json)")
        return rep
    for fam, gid, it in spec_items(spec):
        r = sync_item(fam, it, spec, root)
        r["group"] = gid
        rep["items"].append(r)
        rep["counts"][r["state"]] = rep["counts"].get(r["state"], 0) + 1
        if apply:
            hist = it.setdefault("contract_history", [])
            if it.get("contract"):
                hist.append(it["contract"])
            it["contract"] = {"engine_file": r["engine_file"], "flags": r["flags"], "ts": ts, "state": r["state"], "drift": r["drift"], "unexposed": r["unexposed"]}
    if apply and sp:
        spec["contract_sync_ts"] = ts
        sp.write_text(json.dumps(spec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        rep["applied"] = True
    rep["state"] = "DRIFT" if rep["counts"].get("DRIFT") else ("ABSENT" if rep["counts"].get("ENGINE_ABSENT") else "OK")
    try:
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "BINDING_SYNC_latest.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
        (OUT / f"BINDING_SYNC_{ts}.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception:
        pass
    if do_print:
        print(f"=== 綁定合約同步 MDL054 v0102 · 冊 {rep['spec']} · 項 {len(rep['items'])} · {rep['counts']} · {'APPLIED(只增 contract/contract_history)' if rep['applied'] else 'plan(唯讀;--apply 才寫)'} ===")
        for r in rep["items"]:
            if r["state"] != "OK" or r["unexposed"]:
                print(f"  [{r['state']:13s}] {r['family']}/{r['id']:22s} {r['engine_file'] or '—':44s} " + (" | ".join(r["drift"])[:110] if r["drift"] else "") + (f" · 未暴露 {','.join(r['unexposed'][:6])}" if r["unexposed"] else ""))
        print(f"  [存證] {OUT / 'BINDING_SYNC_latest.json'}")
    return rep


def _engine_universe(family: str | None, root: Path | None = None) -> list:
    root = root or VIA
    out = {}
    for fam, dirs in FAMILY_SCAN_DIRS.items():
        if family and fam != family:
            continue
        for d in dirs:
            dp = root / d
            if not dp.is_dir():
                continue
            for p in sorted(dp.glob("*.py")):
                if SKIP_RX.search(p.name):
                    continue
                stem = _VER_RX.sub("", p.name)
                key = (fam, stem)
                if key not in out or p.name > out[key].name:
                    out[key] = p
    return [(fam, p) for (fam, _s), p in sorted(out.items(), key=lambda kv: (kv[0][0], kv[1].name))]


def split_need(s: str) -> list:
    """批514 操作員實錄:`via-iface connect -Need 首頁,ocr` → PowerShell 先把 `首頁,ocr` 拆成陣列,Register 再用空白合回 → 引擎收到 ['首頁 ocr'] 命中 0。
    引擎端寬收:逗號/空白/分號/全形逗號/頓號皆為分隔;去空;保序去重。"""
    out = []
    for x in re.split(r"[,\s;，、]+", str(s or "")):
        x = x.strip()
        if x and x not in out:
            out.append(x)
    return out


def do_connect(need: list, family: str | None, spec_path: Path | None = None, root: Path | None = None, do_print: bool = True) -> dict:
    spec, sp = load_spec(spec_path)
    bound = {}
    for fam, gid, it in spec_items(spec):
        p = resolve_engine(it, root)
        if p:
            bound.setdefault(p.name, []).append(it)
    kws = [k.strip().lower() for k in need if k.strip()]
    uni = {(fam, p.name): p for fam, p in _engine_universe(family, root)}
    for fam, gid, it in spec_items(spec):                       # 冊上綁定的引擎永遠是候選(嫁接的起點是冊,不是夾)
        if family and fam != family:
            continue
        p = resolve_engine(it, root)
        if p:
            uni.setdefault((fam, p.name), p)
    rows = []
    for (fam, _n), p in sorted(uni.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        c = derive_contract(p)
        if c.get("syntax") != "OK":
            continue
        hay = " ".join([p.name.lower(), c.get("desc", "").lower(), " ".join(c.get("cli_flags") or []).lower()] +
                       [str(it.get("zh", "")).lower() + " " + " ".join(map(str, it.get("outputs") or [])).lower() for it in bound.get(p.name, [])])
        hits = [k for k in kws if k in hay]
        if not hits:
            continue
        its = bound.get(p.name, [])
        verb = list(((its[0].get("engine") or {}).get("verb") or [])) if its else (["--selftest"] if "--selftest" in (c.get("cli_flags") or []) else [])
        rows.append({"family": fam, "engine": p.name, "score": len(hits), "hits": hits, "desc": c.get("desc", "")[:80], "flags": (c.get("cli_flags") or [])[:10],
                     "bound_items": [it.get("id") for it in its], "argv": ["<" + fam + " python>", p.name, *verb]})
    rows.sort(key=lambda r: (-r["score"], r["family"], r["engine"]))
    rep = {"schema": "VIA.IfaceConnect.v1", "ts": datetime.now().strftime("%Y%m%d_%H%M%S"), "need": kws, "family": family, "candidates": rows[:8], "n": len(rows)}
    try:
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "CONNECT_latest.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception:
        pass
    if do_print:
        print(f"=== 嫁接候選 connect · 需求 {kws} · 族 {family or '全'} · 命中 {len(rows)}(只列不寫;綁定改冊走 graft) ===")
        for r in rows[:8]:
            print(f"  [{r['score']}] {r['family']}/{r['engine']:46s} 冊 {','.join(r['bound_items']) or '未綁'} · {r['desc'][:50]} · argv {' '.join(r['argv'])}")
    return rep


def do_graft(item_id: str, glob: str, dir_: str | None, apply: bool, spec_path: Path | None = None, root: Path | None = None, do_print: bool = True) -> dict:
    spec, sp = load_spec(spec_path)
    hit = next(((fam, it) for fam, gid, it in spec_items(spec) if it.get("id") == item_id), None)
    if not hit:
        rep = {"state": "ITEM_ABSENT", "item": item_id}
        if do_print:
            print(f"  [graft] 冊上無此項 {item_id}")
        return rep
    fam, it = hit
    d = dir_ or (it.get("engine") or {}).get("dir") or ""
    cand = _newest_in((root or VIA) / d, glob)
    if not cand:
        rep = {"state": "ENGINE_ABSENT", "item": item_id, "dir": d, "glob": glob}
        if do_print:
            print(f"  [graft] 候選引擎不在:{d}/{glob}")
        return rep
    c = derive_contract(cand)
    flags = set(c.get("cli_flags") or [])
    verb = [v for v in ((it.get("engine") or {}).get("verb") or []) if isinstance(v, str) and v.startswith("--")]
    need = set(verb) | {f for k in (it.get("params") or []) for f in param_flags(k if isinstance(k, str) else str((k or {}).get("kind", "")), spec)}
    missing = sorted(need - flags)
    rep = {"schema": "VIA.IfaceGraft.v1", "ts": datetime.now().strftime("%Y%m%d_%H%M%S"), "item": item_id, "family": fam, "from": (it.get("engine") or {}).get("glob"),
           "to": {"dir": d, "glob": glob, "file": cand.name}, "need_flags": sorted(need), "missing": missing,
           "state": "COMPATIBLE" if not missing else "INCOMPATIBLE", "applied": False,
           "proposal": {**(it.get("engine") or {}), "dir": d, "glob": glob}}
    if apply and sp and rep["state"] == "COMPATIBLE":
        it.setdefault("graft_candidates", []).append({"ts": rep["ts"], "dir": d, "glob": glob, "file": cand.name, "state": rep["state"]})
        sp.write_text(json.dumps(spec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        rep["applied"] = True
    if do_print:
        print(f"=== 嫁接相容 graft · {fam}/{item_id} · {rep['from']} → {cand.name} · {rep['state']}" + (f" · 缺旗標 {','.join(missing)}" if missing else "") + (" · APPLIED(只增 graft_candidates;engine.glob 換不換=冊主/操作員)" if rep["applied"] else " · 只列(--apply 只增候選;不改 engine.glob)") + " ===")
    return rep


def do_status() -> int:
    p = OUT / "BINDING_SYNC_latest.json"
    if not p.exists():
        print("  [綁定合約] 未跑;via-iface sync(唯讀)")
        return 2
    j = json.loads(p.read_text(encoding="utf-8"))
    print(f"  [綁定合約] {j.get('state')} · {j.get('ts')} · 冊 {j.get('spec')} · 項 {len(j.get('items', []))} · {j.get('counts')}")
    return 0 if j.get("state") == "OK" else 1


def _arg(a: list, flag: str, default=None):
    if flag in a and a.index(flag) + 1 < len(a):
        return a[a.index(flag) + 1]
    return default


def selftest() -> int:
    import tempfile
    global OUT
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)
    keep_out = OUT
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        OUT = root / "out"
        (root / "e").mkdir()
        (root / "e" / "X_ENG001_A_v0100.py").write_text('"""X_ENG001 A — 抓價\n"""\nimport sys\nif "--selftest" in sys.argv: pass\nif "--start" in sys.argv: pass\nif "--days" in sys.argv: pass\nif "--tickers" in sys.argv: pass\n', encoding="utf-8")
        (root / "e" / "Y_ENG002_B_v0100.py").write_text('"""Y_ENG002 B — 報告首頁\n"""\nimport sys\nif "--selftest" in sys.argv: pass\nif "--dir" in sys.argv: pass\n', encoding="utf-8")
        spec = {"param_kinds": {"start": "--start YYYY-MM-DD", "days": "--days N", "dir": "--dir <夾>", "codes": "代碼冊(positional|--tickers)"},
                "families": {"vdf": {"groups": [{"id": "g", "items": [
                    {"id": "a_ok", "zh": "抓價", "engine": {"dir": "e", "glob": "X_ENG001_A_v*.py", "verb": ["run", "--start"]}, "params": ["days"], "outputs": ["tw_daily_prices"]},
                    {"id": "a_drift", "zh": "抓價舊冊", "engine": {"dir": "e", "glob": "X_ENG001_A_v*.py", "verb": ["--nosuch"]}, "params": ["dir"], "outputs": []},
                    {"id": "gone", "zh": "沒引擎", "engine": {"dir": "e", "glob": "Z_ENG999_v*.py", "verb": []}, "params": []}]}]},
                             "vrn": {"groups": [{"id": "g2", "items": [{"id": "b_ok", "zh": "首頁", "engine": {"dir": "e", "glob": "Y_ENG002_B_v*.py", "verb": ["run"]}, "params": ["dir"], "outputs": ["first_page"]}]}]}}}
        sp = root / "VIA_InputConsole_Spec_v0100.json"
        sp.write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
        rep = do_sync(False, sp, root, do_print=False)
        by = {r["id"]: r for r in rep["items"]}
        chk("① sync 判態:verb/params 旗標都在=OK;冊 verb --nosuch 與 params dir 不在=DRIFT(VERB+PARAM);引擎 glob 沒檔=ENGINE_ABSENT",
            by["a_ok"]["state"] == "OK" and by["b_ok"]["state"] == "OK" and by["a_drift"]["state"] == "DRIFT"
            and any(d.startswith("VERB_DRIFT") for d in by["a_drift"]["drift"]) and any(d.startswith("PARAM_DRIFT") for d in by["a_drift"]["drift"]) and by["gone"]["state"] == "ENGINE_ABSENT",
            f"({rep['counts']})")
        chk("② 未暴露旗標=引擎有、冊沒開(--tickers);共用旗標 --selftest 不算", by["a_ok"]["unexposed"] == ["--tickers"])
        chk("③ plan 唯讀:冊檔不動、報告落 OUT", json.loads(sp.read_text(encoding="utf-8")) == spec and (OUT / "BINDING_SYNC_latest.json").exists())
        rep2 = do_sync(True, sp, root, do_print=False)
        s2 = json.loads(sp.read_text(encoding="utf-8"))
        it_ok = s2["families"]["vdf"]["groups"][0]["items"][0]
        chk("④ --apply 只增:項下多 contract{engine_file,flags,state}+contract_sync_ts;原 engine/params/outputs 一字不動",
            rep2["applied"] and it_ok["contract"]["engine_file"] == "X_ENG001_A_v0100.py" and it_ok["contract"]["state"] == "OK"
            and it_ok["engine"] == spec["families"]["vdf"]["groups"][0]["items"][0]["engine"] and it_ok["params"] == ["days"] and s2.get("contract_sync_ts"))
        (root / "e" / "X_ENG001_A_v0101.py").write_text('"""X_ENG001 A — 抓價 v0101\n"""\nimport sys\nif "--selftest" in sys.argv: pass\nif "--start" in sys.argv: pass\nif "--days" in sys.argv: pass\nif "--tickers" in sys.argv: pass\nif "--lanes" in sys.argv: pass\n', encoding="utf-8")
        rep3 = do_sync(True, sp, root, do_print=False)
        b3 = {r["id"]: r for r in rep3["items"]}
        s3 = json.loads(sp.read_text(encoding="utf-8"))
        it3 = s3["families"]["vdf"]["groups"][0]["items"][0]
        chk("⑤ 尾版律自適應:引擎出 v0101 → 合約自動追尾版(engine_file=v0101)、記 VERSION_BUMP、舊約進 contract_history、新旗標 --lanes 列未暴露",
            b3["a_ok"]["engine_file"] == "X_ENG001_A_v0101.py" and any(d.startswith("VERSION_BUMP") for d in b3["a_ok"]["drift"]) and b3["a_ok"]["state"] == "BUMP"
            and it3["contract"]["engine_file"] == "X_ENG001_A_v0101.py" and it3["contract_history"] and it3["contract_history"][-1]["engine_file"] == "X_ENG001_A_v0100.py"
            and "--lanes" in b3["a_ok"]["unexposed"])
        cn = do_connect(["首頁", "dir"], None, sp, root, do_print=False)
        cn2 = do_connect(["抓價"], "vdf", sp, root, do_print=False)
        chk("⑥ connect 嫁接候選:關鍵字對 路徑/說明/旗標/冊 zh/outputs 打分;首頁+dir → Y_ENG002 第一且 argv 帶冊 verb;族過濾只留 vdf",
            cn["candidates"] and cn["candidates"][0]["engine"] == "Y_ENG002_B_v0100.py" and cn["candidates"][0]["argv"][-1] == "run" and "b_ok" in cn["candidates"][0]["bound_items"]
            and cn2["candidates"] and all(c["family"] == "vdf" for c in cn2["candidates"]) and cn2["candidates"][0]["engine"].startswith("X_ENG001"))
        g1 = do_graft("a_ok", "Y_ENG002_B_v*.py", None, False, sp, root, do_print=False)
        g2 = do_graft("b_ok", "Y_ENG002_B_v*.py", None, True, sp, root, do_print=False)
        s4 = json.loads(sp.read_text(encoding="utf-8"))
        itb = s4["families"]["vrn"]["groups"][0]["items"][0]
        chk("⑦ graft 相容驗:a_ok 換到 Y(缺 --start/--days)=INCOMPATIBLE 不寫;b_ok 換到 Y=COMPATIBLE,--apply 只增 graft_candidates、engine.glob 不動",
            g1["state"] == "INCOMPATIBLE" and set(g1["missing"]) == {"--start", "--days"} and g2["state"] == "COMPATIBLE" and g2["applied"]
            and itb["graft_candidates"][-1]["file"] == "Y_ENG002_B_v0100.py" and itb["engine"]["glob"] == "Y_ENG002_B_v*.py")
        chk("⑧ status 讀報告;缺冊誠實 ABSENT", do_status() in (0, 1) and do_sync(False, root / "none.json", root, do_print=False).get("state") == "ABSENT")
    OUT = keep_out
    chk("⑨ 批514 --need 寬收(逗號/空白/分號/全形逗號/頓號;PowerShell 陣列合回的空白也吃得下;保序去重)",
        split_need("首頁 ocr,表格;ocr，首頁、x") == ["首頁", "ocr", "表格", "x"] and split_need("") == [] and split_need(" ,a, ") == ["a"])
    print(f"  [計] 九檢 OK {9 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 介面合約自適應(CGC_MDL054 v0102)· 九檢自測(零執行零網路;暫存冊)===")
        return selftest()
    verb = next((x for x in a if not x.startswith("-")), "scan")
    if verb == "scan":
        return do_scan("--dry" in a)
    if verb == "sync":
        rep = do_sync("--apply" in a)
        return 0 if rep.get("state") == "OK" else (2 if rep.get("state") == "ABSENT" else 1)
    if verb == "connect":
        need = split_need(_arg(a, "--need") or "")      # 批514:逗號/空白/分號/頓號皆可(PowerShell 把 a,b 拆成陣列再以空白合回=實錄 need ['首頁 ocr'] 命中 0)
        if not need:
            print("  [connect] 要 --need 關鍵字(逗號合寫;對路徑/說明/旗標/冊 zh/outputs)")
            return 2
        rep = do_connect(need, _arg(a, "--family"))
        return 0 if rep["candidates"] else 1
    if verb == "graft":
        item, glob = _arg(a, "--item"), _arg(a, "--engine")
        if not item or not glob:
            print("  [graft] 要 --item <冊 id> --engine <glob> [--dir 夾] [--apply]")
            return 2
        rep = do_graft(item, glob, _arg(a, "--dir"), "--apply" in a)
        return 0 if rep.get("state") == "COMPATIBLE" else 1
    if verb == "status":
        return do_status()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
