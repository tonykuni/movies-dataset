#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""Parameter hub v0112 — 薄尾(v0111 以前一字不動):VCGC 只讀匯總 VDF 參數正本 · 跨系統同名參數比對 · 索引冊出新版號

操作員 2026-11-25:「繼續做 VCGC 只讀匯總 VDF 正本」(前一批定案:VDF 正本 = VDF_ParamControl_SSOT 尾版;VCGC 只讀匯總)。
前版實況(本版要修的兩件):
  ① 冊單裡 VDF 的冊寫死 v0100(VDF_Unified_Params_v0100 · VDF_Param_Registry_v0100 …),VDF 正本 ParamControl_SSOT 不在冊單。
  ② v0109 的 run_scan 用本體自己的 BOOKS(尾版加的冊沒掃到),而且把結果覆寫回 VIA_Central_Params_SSOT_v0100.json(不是出新版)。
本版新動詞(其餘照前版 main):
  vdf-master [--apply]
    冊單:前版冊單 + VDF 的版號冊改接尾版(glob,不釘版號)+ VDF_PARAM_MASTER = VDF_ParamControl_SSOT 尾版(只讀,不進衝突圈)。
    跨系統:VDF 正本每個參數的路徑末段(start_date · batch_size · timeout_s …;太通用的 root / items / tol 不比)
            對 VDF 以外、衝突圈內(conflict_scope)各冊的同名葉 → ALIGNED(同值)/ DIFFERENT(值不同 = 建議燈,候操作員裁決;系統獨立,各自可不同)。
    VDF 自報:讀 VDF 自己的 unify 收據(VIA_Reports/vdf_params/*/SUMMARY.json);沒有 = 灰(VCGC 不代 VDF 重算,只攤開)。
    --apply:索引冊出新版號 VIA_Central_Params_SSOT_v####(max 本機 ∪ origin/main + 1;暫存檔原子換名;前版不覆寫)。
    VCGC 不寫 VDF 任何檔。輸出 DataFrame(polars,退 pandas)→ VIA_Reports/vcgc/central_params/<UTC>/ + 運作帳 RUN_LEDGER.jsonl。
rc:0 綠 · 2 黃(有 DIFFERENT / VDF 未自報)· 1 紅(VDF 正本不在 / 冊 FAIL)
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0111] SuperAccel 加速器橋(從 TEMP 跑時改由工作目錄 / VIA_REPO 找倉;graceful) =====
try:
    import os as _sa_os
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_hit = None
    _sa_roots = [_sa_Path(__file__).resolve(), _sa_Path.cwd().resolve()]
    if _sa_os.environ.get("VIA_REPO"):
        _sa_roots.append(_sa_Path(_sa_os.environ["VIA_REPO"]).resolve())
    for _sa_r in _sa_roots:
        for _sa_q in (_sa_r, *_sa_r.parents):
            for _sa_c in (_sa_q / "supportive modules", _sa_q / "VeritasIntelligenceAnalytics" / "supportive modules"):
                if (_sa_c / "VIA_SuperAccel_Module.py").exists():
                    _sa_hit = _sa_c
                    break
            if _sa_hit:
                break
        if _sa_hit:
            break
    if _sa_hit and str(_sa_hit) not in _sa_sys.path:
        _sa_sys.path.insert(0, str(_sa_hit))
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響(自測會把它記成黃)
# ===== [VIA:ACCEL-BRIDGE:END] =====
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(操作員 2026-11-25「網路工具也要強制加入」;從 TEMP 跑時改由工作目錄 / VIA_REPO 找倉;graceful) =====
VIA_NET_TOOL_PATH = None
try:
    import os as _nb_os
    from pathlib import Path as _nb_Path
    _nb_roots = [_nb_Path(__file__).resolve(), _nb_Path.cwd().resolve()]
    if _nb_os.environ.get("VIA_REPO"):
        _nb_roots.append(_nb_Path(_nb_os.environ["VIA_REPO"]).resolve())
    for _nb_r in _nb_roots:
        for _nb_q in (_nb_r, *_nb_r.parents):
            for _nb_dir in (_nb_q / "supportive modules" / "network", _nb_q / "VeritasIntelligenceAnalytics" / "supportive modules" / "network"):
                _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py")) if _nb_dir.is_dir() else []
                if _nb_hits:
                    VIA_NET_TOOL_PATH = str(_nb_hits[-1])
                    break
            if VIA_NET_TOOL_PATH:
                break
        if VIA_NET_TOOL_PATH:
            break
except Exception:  # noqa: BLE001
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT:載入不出網,真的連線才看閘);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

VERSION = "v0112"
TAG = f"via_params_central {VERSION}"
HERE = Path(__file__).resolve().parent
_T0 = time.time()
_PRIOR_PATH = [p for p in sorted(HERE.glob("via_params_central_v*.py")) if p.name < Path(__file__).name][-1]
_spec = importlib.util.spec_from_file_location("via_params_central_prior_of_v0112", _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
IMPL = getattr(PRIOR, "IMPL", getattr(PRIOR, "prev", PRIOR))               # v0109 本體(scan_book · find_conflicts · build_index …)
VIA = HERE.parent.parent
VDF_DIR = "functional modules/VDF"
MASTER_FAM = "VDF_ParamControl_SSOT"
INDEX_FAM = "VIA_Central_Params_SSOT"
GENERIC = {"root", "items", "tol", "start", "end", "batch", "path", "name", "value", "id", "version", "book", "class", "mode", "type"}
WRAPPERS = {"ruling", "display", "value", "rationale", "note", "variants", "apply", "default", "authority", "batch_no", "why"}   # 欄位外殼:往上一段取真名


def semantic(path: str) -> str:
    """參數真名:去掉 list 索引與外殼段(canonical.START_DATE.ruling → start_date);小寫比。"""
    segs = [x for x in re.split(r"\.", re.sub(r"\[\d+\]", "", str(path))) if x]
    while segs and segs[-1].lower() in WRAPPERS:
        segs.pop()
    return segs[-1].lower() if segs else ""


def norm_val(v) -> str:
    t = json.dumps(v, ensure_ascii=False, sort_keys=True, default=str)
    return t.strip('"').strip("'") if isinstance(v, str) else t


def __getattr__(name: str):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def say(msg: str) -> None:
    print(f"[{time.time() - _T0:6.1f}s] {msg}", flush=True)


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(str(p)).stem)
    return int(m.group(1)) if m else -1


def tail_rel(root: Path, rel: str) -> str:
    """版號冊 → 同夾同家族尾版(glob;不釘版號)。不是版號冊就原樣。"""
    p = Path(rel)
    m = re.match(r"(.+)_v\d{4}$", p.stem)
    if not m:
        return rel
    c = [q for q in (root / p.parent).glob(f"{m.group(1)}_v*{p.suffix}") if _vnum(q) >= 0]
    return (p.parent / max(c, key=_vnum).name).as_posix() if c else rel


def master_rel(root: Path):
    c = [q for q in (root / VDF_DIR).rglob(MASTER_FAM + "_v*.json") if _vnum(q) >= 0]
    return max(c, key=_vnum).relative_to(root).as_posix() if c else None


def is_vdf(b: dict) -> bool:
    return b["id"].startswith("VDF_") or VDF_DIR in b["path"]


def books_v0112(root: Path) -> list:
    out = []
    for b in PRIOR.BOOKS:
        nb = dict(b)
        if is_vdf(b):
            nb["path"] = tail_rel(root, b["path"])
        out.append(nb)
    mr = master_rel(root)
    if mr and not any(b["id"] == "VDF_PARAM_MASTER" for b in out):
        out.append({"id": "VDF_PARAM_MASTER", "domain": "MASTER", "conflict_scope": False, "path": mr,
                    "note": "VDF 參數唯一正本(VDF 自己管;VCGC 只讀匯總)"})
    return out


def vdf_self_report(root: Path) -> dict:
    """VDF 自報的 unify 收據(ENG053 寫);VCGC 只讀,不代算。"""
    best, bad = None, []
    for p in (root / "VIA_Reports" / "vdf_params").glob("2*/SUMMARY.json"):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            bad.append(f"{p.parent.name}: {type(e).__name__}")              # 壞收據照實記,不算自報
            d = {}
        if d.get("verb") == "unify" and (best is None or str(d.get("utc")) > str(best.get("utc"))):
            best = d
    if best is None:
        return {"lamp": "GRAY", "note": "VDF 未自報(桌機跑 vdfp 或 ENG053 unify 後才有)", "unreadable": bad}
    return {"lamp": best.get("lamp", "GRAY"), "utc": best.get("utc"), "counts": best.get("counts"), "engine": best.get("engine"), "unreadable": bad}


def cross_check(master: dict, records: list) -> list:
    rows = []
    others = [r for r in records if r.get("state") == "OK" and not is_vdf(r) and r.get("_leaves")
              and r.get("conflict_scope")]                                  # 照本體的衝突圈:參數冊才比;知識冊 / 清冊(關鍵字次數等)不比
    for e in master.get("params", []):
        seg = semantic(e.get("path", ""))
        if not seg or seg in GENERIC or (len(seg) < 6 and "_" not in seg):
            continue
        mv = norm_val(e.get("value"))
        for r in others:
            for k, v in r["_leaves"].items():
                if "[" in k or semantic(k) != seg:
                    continue
                ov = norm_val(v)
                rows.append({"param_id": e.get("id"), "name": e.get("name"), "key": seg, "master_value": mv[:120],
                             "other_book": r["id"], "other_key": k, "other_value": ov[:120],
                             "state": "ALIGNED" if ov == mv else "DIFFERENT"})
    return rows


def published_max(root: Path) -> int:
    try:
        repo = root.parent
        r = subprocess.run(["git", "-C", str(repo), "ls-tree", "--name-only", "origin/main", "VeritasIntelligenceAnalytics/supportive modules/registry/"],
                           capture_output=True, text=True, timeout=30)
        return max([_vnum(x) for x in r.stdout.splitlines() if Path(x).name.startswith(INDEX_FAM + "_v")] or [-1])
    except Exception:  # noqa: BLE001
        return -1


def vdf_master(root: Path = VIA, apply: bool = False) -> dict:
    mr = master_rel(root)
    if mr is None:
        return {"lamp": "RED", "note": f"VDF 正本 {MASTER_FAM} 不在", "rows": []}
    books = books_v0112(root)
    records = [IMPL.scan_book(b, root) for b in books]
    conflicts = IMPL.find_conflicts(records)
    locked = IMPL.locked_alignment(records)
    idx = IMPL.build_index(records, conflicts, locked)
    master = json.loads((root / mr).read_text(encoding="utf-8"))
    rows = cross_check(master, records)
    rep = vdf_self_report(root)
    diff = [r for r in rows if r["state"] == "DIFFERENT"]
    repointed = [{"id": b["id"], "from": o["path"], "to": b["path"]} for o, b in zip(PRIOR.BOOKS, books) if o["path"] != b["path"]]
    idx["vdf_master"] = {"book": mr, "params": len(master.get("params", [])), "by_class": (master.get("counts") or {}).get("by_class"),
                         "open_conflicts": [c for c in master.get("conflicts", []) if str(c.get("status", "")).startswith("OPEN")],
                         "vdf_self_report": rep, "cross_system": {"checked": len(rows), "aligned": len(rows) - len(diff), "different": diff},
                         "repointed_books": repointed, "policy": "VCGC 只讀匯總;VDF 正本由 VDF 自己寫;DIFFERENT = 建議燈候操作員裁決"}
    fail = idx["books_fail"]
    lamp = "RED" if fail else ("YELLOW" if diff or rep["lamp"] != "GREEN" or idx["vdf_master"]["open_conflicts"] else "GREEN")
    res = {"lamp": lamp, "rows": rows, "index": idx, "counts": {"books": idx["books_total"], "ok": idx["books_ok"], "missing": idx["books_missing"],
                                                                 "fail": fail, "cross_checked": len(rows), "different": len(diff),
                                                                 "repointed": len(repointed), "conflicts": len(conflicts)}}
    if apply:
        reg = root / "supportive modules" / "registry"
        nv = max(max((_vnum(p) for p in reg.glob(INDEX_FAM + "_v*.json")), default=-1), published_max(root)) + 1
        vs = f"v{nv:04d}"
        dest = reg / f"{INDEX_FAM}_{vs}.json"
        if dest.exists():
            raise FileExistsError(dest.name)
        prev = max((p for p in reg.glob(INDEX_FAM + "_v*.json")), key=_vnum, default=None)
        out = dict(idx, version=vs, prior=prev.name if prev else None, ts=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
        out[f"why_{vs}"] = f"{TAG} vdf-master:VDF 正本只讀匯總 · VDF 冊接尾版 {len(repointed)} 本 · 跨系統同名 {len(rows)} 列(不同 {len(diff)})· 前版不覆寫"
        tmp = dest.with_name(dest.name + f".{os.getpid()}.sdd_tmp")
        tmp.write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8")
        json.loads(tmp.read_text(encoding="utf-8"))
        os.replace(tmp, dest)
        res["written"] = dest.name
    return res


def frame(rows: list):
    cols = sorted({k for r in rows for k in r}) or ["state"]
    norm = [{c: (None if r.get(c) is None else str(r.get(c))) for c in cols} for r in rows]
    try:
        import polars as pl
        return pl.DataFrame(norm, schema={c: pl.Utf8 for c in cols}) if norm else pl.DataFrame(schema={c: pl.Utf8 for c in cols})
    except ImportError:
        try:
            import pandas as pd
            return pd.DataFrame(norm, columns=cols).astype("string")
        except ImportError:
            return None


def save(res: dict, root: Path) -> Path:
    base = root / "VIA_Reports" / "vcgc" / "central_params"
    od = base / datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    od.mkdir(parents=True, exist_ok=True)
    df = frame(res.get("rows", []))
    fmt = "none"
    if df is not None:
        try:
            df.write_parquet(od / "cross_system.parquet", compression="zstd") if hasattr(df, "write_parquet") else df.to_parquet(od / "cross_system.parquet", compression="zstd", index=False)
            fmt = "parquet"
        except Exception:  # noqa: BLE001 - 沒有 parquet 寫手 → jsonl 退路
            (od / "cross_system.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in res.get("rows", [])), encoding="utf-8")
            fmt = "jsonl(退路)"
    summ = {"tool": TAG, "verb": "vdf-master", "utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "lamp": res["lamp"],
            "counts": res.get("counts"), "written": res.get("written"), "format": fmt, "accel": VIA_ACCEL is not None, "net": VIA_NET_TOOL_PATH is not None,
            "vdf_master": (res.get("index") or {}).get("vdf_master")}
    (od / "SUMMARY.json").write_text(json.dumps(summ, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    with (base / "RUN_LEDGER.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps({k: summ[k] for k in ("utc", "lamp", "counts", "written")} | {"secs": round(time.time() - _T0, 2)}, ensure_ascii=False) + "\n")
    return od


def main() -> int:
    a = sys.argv[1:]
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    if a[:1] != ["vdf-master"]:
        return PRIOR.main() if hasattr(PRIOR, "main") else IMPL.main()
    apply = "--apply" in a
    say(f"{TAG} vdf-master{' --apply' if apply else ''} · 加速器 {'載入' if VIA_ACCEL is not None else '沒載到(黃)'} · 網路工具 {'在' if VIA_NET_TOOL_PATH else '不在'}")
    res = vdf_master(VIA, apply)
    od = save(res, VIA)
    vm = (res.get("index") or {}).get("vdf_master") or {}
    say(f"vdf-master · {res['lamp']} · " + " · ".join(f"{k} {v}" for k, v in (res.get("counts") or {}).items())
        + (f" · 寫 {res['written']}" if res.get("written") else "") + (f" · {res['note']}" if res.get("note") else ""))
    say(f"  VDF 正本 {vm.get('book')} · {vm.get('params')} 參數 · 未決衝突 {len(vm.get('open_conflicts') or [])} · VDF 自報 {((vm.get('vdf_self_report') or {}).get('lamp'))}")
    for r in vm.get("repointed_books", [])[:10]:
        say(f"  接尾版 {r['id']}:{Path(r['from']).name} → {Path(r['to']).name}")
    for r in [r for r in res.get("rows", []) if r["state"] == "DIFFERENT"][:15]:
        say(f"  DIFFERENT {r['param_id']} {r['key']}:VDF {r['master_value'][:40]} ≠ {r['other_book']} {r['other_key']} {r['other_value'][:40]}")
    say(f"DataFrame → {od}")
    return {"GREEN": 0, "YELLOW": 2}.get(res["lamp"], 1)


# ---------------------------------------------------------------- 自測(全在暫存夾造資料)
def selftest() -> int:
    ok, bad = [], []

    def chk(name, cond, note=""):
        (ok if cond else bad).append(name)
        print(("  [OK] " if cond else "  [NG] ") + name + (f" · {note}" if note else ""), flush=True)

    chk("加速器載入(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    chk("網路工具載入(_via_net() is not None · 載入不出網)", _via_net() is not None, str(VIA_NET_TOOL_PATH))
    chk("前版經 glob 載入(v0111)· 本體可叫", _PRIOR_PATH.name == "via_params_central_v0111.py" and callable(getattr(IMPL, "scan_book", None)))
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "VIA"
        vdf = root / VDF_DIR
        reg = root / "supportive modules" / "registry"
        vdf.mkdir(parents=True)
        reg.mkdir(parents=True)
        w = lambda p, o: p.write_text(json.dumps(o, ensure_ascii=False), encoding="utf-8")  # noqa: E731
        w(vdf / "VDF_Unified_Params_v0100.json", {"time": {"start_date": "2022-01-01"}})
        w(vdf / "VDF_Unified_Params_v0102.json", {"time": {"start_date": "2018-01-01"}})
        w(vdf / "VDF_ParamControl_SSOT_v0105.json", {"params": [
            {"id": "VDF-PAR-023", "name": "起始日", "path": "time.start_date", "value": "2018-01-01"},
            {"id": "VDF-PAR-025", "name": "batch", "path": "fetch.batch_size", "value": 5},
            {"id": "VDF-PAR-031", "name": "輸出根", "path": "output.root", "value": "x"},
            {"id": "VDF-PAR-037", "name": "起始日裁定", "path": "canonical.START_DATE.ruling", "value": "'2018-01-01'"}],
            "counts": {"by_class": {"時間範圍": 1}}, "conflicts": [{"id": "PC-002", "status": "OPEN(待裁)"}]})
        w(reg / "VRN_Params_v0100.json", {"run": {"start_date": "2018-01-01", "batch_size": 10, "root": "y"},
                                          "canonical": {"ENGINE_NAME": {"ruling": "'X'"}, "END_DATE": {"ruling": "TODAY"}}})
        keep = PRIOR.BOOKS
        PRIOR.BOOKS = [{"id": "VDF_UNIFIED", "domain": "CONFIG", "conflict_scope": True, "path": f"{VDF_DIR}/VDF_Unified_Params_v0100.json", "note": "n"},
                       {"id": "VRN_PARAMS", "domain": "CONFIG", "conflict_scope": True, "path": "supportive modules/registry/VRN_Params_v0100.json", "note": "n"}]
        try:
            b = books_v0112(root)
            chk("VDF 冊接尾版 · 加 VDF 正本(只讀不進衝突圈)", b[0]["path"].endswith("VDF_Unified_Params_v0102.json")
                and b[-1]["id"] == "VDF_PARAM_MASTER" and b[-1]["conflict_scope"] is False and b[1]["path"].endswith("VRN_Params_v0100.json"))
            r = vdf_master(root)
            st = {(x["key"], x["other_book"]): x["state"] for x in r["rows"]}
            ks = [(x["param_id"], x["other_key"], x["state"]) for x in r["rows"]]
            chk("跨系統:真名比(外殼段剝掉 · 大小寫不分 · 引號不算)· 同值 ALIGNED · 不同 DIFFERENT · 通用名不比",
                ("VDF-PAR-023", "run.start_date", "ALIGNED") in ks and ("VDF-PAR-037", "run.start_date", "ALIGNED") in ks
                and ("VDF-PAR-025", "run.batch_size", "DIFFERENT") in ks and not any("ENGINE_NAME" in k[1] or "END_DATE" in k[1] for k in ks)
                and not any(k[1].endswith(".root") for k in ks), str(ks))
            vm = r["index"]["vdf_master"]
            chk("VDF 沒自報 = 灰 · 未決衝突照列 · 黃燈", vm["vdf_self_report"]["lamp"] == "GRAY" and len(vm["open_conflicts"]) == 1 and r["lamp"] == "YELLOW")
            chk("只查不寫 · VCGC 不寫 VDF 任何檔", not list(reg.glob("VIA_Central_Params_SSOT_v*.json"))
                and sorted(p.name for p in vdf.iterdir()) == ["VDF_ParamControl_SSOT_v0105.json", "VDF_Unified_Params_v0100.json", "VDF_Unified_Params_v0102.json"])
            w(reg / "VIA_Central_Params_SSOT_v0100.json", {"old": True})
            r2 = vdf_master(root, apply=True)
            nb = json.loads((reg / "VIA_Central_Params_SSOT_v0101.json").read_text(encoding="utf-8")) if (reg / "VIA_Central_Params_SSOT_v0101.json").exists() else {}
            chk("--apply:索引冊出 v0101 · 前版不覆寫 · prior / why", r2.get("written") == "VIA_Central_Params_SSOT_v0101.json" and nb.get("prior") == "VIA_Central_Params_SSOT_v0100.json"
                and nb.get("why_v0101") and json.loads((reg / "VIA_Central_Params_SSOT_v0100.json").read_text(encoding="utf-8")) == {"old": True}
                and nb.get("vdf_master", {}).get("cross_system", {}).get("checked") == 3)
            (root / "VIA_Reports" / "vdf_params" / "20261125_000000Z").mkdir(parents=True)
            w(root / "VIA_Reports" / "vdf_params" / "20261125_000000Z" / "SUMMARY.json", {"verb": "unify", "lamp": "GREEN", "utc": "2026-11-25T00:00:00Z"})
            chk("讀 VDF 自報 unify 收據", vdf_self_report(root)["lamp"] == "GREEN")
            chk("沒有殘留暫存檔 · 輸出 DataFrame", not list(reg.glob("*.sdd_tmp")) and frame(r["rows"]) is not None)
        finally:
            PRIOR.BOOKS = keep
    print(f"{TAG} selftest {len(ok)}/{len(ok) + len(bad)}" + (" · 不過:" + " · ".join(bad) if bad else ""), flush=True)
    return 0 if not bad else 1


if __name__ == "__main__":
    raise SystemExit(main())
