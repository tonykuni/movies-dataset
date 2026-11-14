#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0182 — 薄尾(操作員 2026-10-11「前五年的 PAYOUT RATIO 穩定的話 就有參考價值」)。
  payout 動詞(auto 自動接):資料庫股利 + 稀釋 EPS 歷史(唯讀 · 依欄認欄)→ 前五年配息率兩種對應(DPS ÷ 同年 EPS / ÷ 前一年 EPS)
  → 標準差小的那種 = DPS 對應年度 · 穩定(≥5 年 · 標準差 ≤ 10 個百分點 · 每年 0~150%)才有參考價值
  → 報告預估 DPS ÷ 對應年度稀釋 EPS 要落在 前五年均值 ± max(10, 2σ) · 不穩定 / 年數不足 → 不當參考(照實標)
其餘動詞照前版鏈。
"""
from __future__ import annotations

# ===== [VIA:ACCEL-BRIDGE:v0111] 最新有版號的正本加速器(動態取最高 VeritasCeleritas_v####;退回鎖版 v1141)· 正本網路工具 VeritasAegisNexus_v1652(找不到 = 不改任何行為) =====
import importlib as _cb_il
import re as _cb_re
import sys as _cb_sys
from pathlib import Path as _cb_Path
_ACCEL, _ACCEL_VER = None, ""
_cb_p = _cb_Path(__file__).resolve()
while _cb_p.parent != _cb_p:
    if (_cb_p / "supportive modules").is_dir():
        _cb_sup = _cb_p / "supportive modules"
        _cb_c = sorted(list(_cb_sup.glob("VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")) + list(_cb_sup.glob("*/VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")),
                       key=lambda x: int(_cb_re.search(r"_v(\d{4})", x.name).group(1)))
        for _cb_d in [str(_cb_sup)] + ([str(_cb_c[-1].parent)] if _cb_c else []) + [str(x.parent) for x in list(_cb_sup.glob("*/VeritasAegisNexus_v1652.py"))[:1]]:
            if _cb_d not in _cb_sys.path:
                _cb_sys.path.insert(0, _cb_d)
        if _cb_c:
            try:
                _ACCEL, _ACCEL_VER = _cb_il.import_module(_cb_c[-1].stem), _cb_c[-1].stem
            except Exception:  # noqa: BLE001
                _ACCEL = None
        break
    _cb_p = _cb_p.parent
if _ACCEL is None:
    try:
        import VeritasCeleritas_v1141 as _ACCEL  # noqa: F401  退回鎖版
        _ACCEL_VER = "VeritasCeleritas_v1141"
    except Exception:  # noqa: BLE001
        _ACCEL = None


def _net():
    """正本網路工具(只在需要出網時載入;本引擎不出網)。"""
    try:
        import VeritasAegisNexus_v1652 as _NET  # noqa: WPS433
        return _NET
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import csv
import importlib.util
import json
import os
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0182"
YEARS, SD_MAX = 5, 10.0


def _vnum_v0182(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0182(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0182(p) < _vnum_v0182(__file__)), key=_vnum_v0182)
PRIOR = _load_v0182(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def _owner(name):
    import types
    mod, seen = PRIOR, set()
    while isinstance(mod, types.ModuleType) and id(mod) not in seen:
        seen.add(id(mod))
        if name in vars(mod):
            return mod
        mod = vars(mod).get("PRIOR")
    return None


def _resolve(name):
    m = _owner(name)
    return vars(m)[name] if m else None


def _job_entry(kind, item):
    return _resolve("_job")(kind, item)


def _init_entry(*args):
    return _resolve("_init_entry")(*args)


_rep = _resolve("_rep")


def db_dividends(vdb: Path = None) -> dict:
    """資料庫現金股利歷史(唯讀):{代號: {年(兩位): 每股現金股利}};年的意義(所屬年度 / 發放年度)不假設 → 用穩定度判斷對應。"""
    vdb = vdb or (_resolve("_vdb") or (lambda: Path("")))()
    out = {}
    files = sorted(p for p in vdb.glob("*.parquet") if re.search(r"div|dividend|股利|配息", p.name, re.I)) if vdb and Path(vdb).is_dir() else []
    try:
        import duckdb  # noqa: WPS433
        con = duckdb.connect()
    except Exception:  # noqa: BLE001
        return out
    for p in files:
        try:
            cols = [r[0] for r in con.execute("describe select * from read_parquet('%s')" % str(p).replace("'", "''")).fetchall()]
        except Exception:  # noqa: BLE001
            continue
        dv = next((c for c in cols if re.search(r"(?i)cash.?div|現金股利|cash_dividend|^dps$|dividend_per_share", c)), None)
        code = next((c for c in cols if re.search(r"(?i)^(code|stock_id|ticker|symbol|公司代號|證券代號|代號)$", c)), None)
        per = next((c for c in cols if re.search(r"(?i)^(year|fy|period|年度|股利所屬年度|所屬年度|發放年度)$", c)), None)
        if not (dv and code and per):
            continue
        for row in con.execute('select "%s", "%s", "%s" from read_parquet(\'%s\')' % (code, per, dv, str(p).replace("'", "''"))).fetchall():
            y = re.search(r"(?:19|20)(\d{2})", str(row[1]))
            try:
                v = float(row[2])
            except (TypeError, ValueError):
                continue
            if y:
                out.setdefault(re.sub(r"\.TWO?$", "", str(row[0]).strip()), {})[int(y.group(1))] = v
    return out


def payout_history(eps: dict, dps: dict, years: int = YEARS) -> dict:
    """eps / dps = {年: 值} → 兩種對應的前 N 年配息率 · 標準差小的 = 對應年度 · 穩定才有參考價值。"""
    res = {}
    for name, lag in (("同年 EPS", 0), ("前一年 EPS", 1)):
        ser = {y: dps[y] / eps[y - lag] * 100 for y in sorted(dps) if (y - lag) in eps and eps[y - lag] > 0}
        last = [ser[y] for y in sorted(ser)[-years:]]
        sd = statistics.pstdev(last) if len(last) >= 2 else None
        res[name] = {"series": {("20%02d" % y): round(v, 1) for y, v in sorted(ser.items())[-years:]}, "n": len(last), "mean": round(statistics.mean(last), 1) if last else None,
                     "sd": round(sd, 1) if sd is not None else None, "lag": lag}
    ok = [k for k, v in res.items() if v["n"] >= years and v["sd"] is not None]
    if not ok:
        return {"status": "年數不足", "why": "兩種對應都不到 %d 年" % years, "alts": res}
    best = min(ok, key=lambda k: res[k]["sd"])
    b = res[best]
    stable = b["sd"] <= SD_MAX and all(0 <= v <= 150 for v in b["series"].values())
    return {"status": "穩定" if stable else "不穩定", "align": best, "lag": b["lag"], "mean": b["mean"], "sd": b["sd"], "series": b["series"], "alts": res,
            "why": "前 %d 年 %s 配息率 均值 %.1f%% · 標準差 %.1f 個百分點%s" % (years, best, b["mean"], b["sd"], "" if stable else " · 超過 %.0f → 不當參考" % SD_MAX)}


def payout_run(dbe: dict = None, dbd: dict = None) -> dict:
    rep = _rep()
    dbe = dbe if dbe is not None else (_resolve("db_eps") or (lambda: {}))()
    dbd = dbd if dbd is not None else db_dividends()
    matrix = _resolve("matrix")
    pk = _resolve("_pkey") or (lambda p: None)
    ptype = _resolve("ptype") or (lambda p: "歷史")
    hist, rows_out = {}, []
    for f in sorted((rep / "restore").glob("*.json")) if (rep / "restore").is_dir() else []:
        if f.name.startswith("RESTORE_"):
            continue
        dj = json.loads(f.read_text(encoding="utf-8"))
        meta = dj.get("document_meta") or {}
        fn, code = meta.get("file") or f.stem, str(meta.get("ticker") or "")
        if code not in hist:
            e = {y: (v.get("diluted") if v.get("diluted") is not None else v.get("eps", v.get("basic"))) for y, v in (dbe.get(code) or {}).items()}
            hist[code] = payout_history({y: v for y, v in e.items() if v is not None}, dbd.get(code) or {}) if (dbe.get(code) and dbd.get(code)) else {
                "status": "沒有資料", "why": "資料庫缺 %s%s" % ("EPS " if not dbe.get(code) else "", "股利" if not dbd.get(code) else "")}
        h = hist[code]
        for t in dj.get("tables", []):
            if t.get("status") == "未過" or not matrix:
                continue
            M, _ = matrix(t.get("rows") or [])
            if "dps" not in M or "eps_use" not in M or "payout" in M:
                continue
            eps = {pk(p)[0]: v for p, v in M["eps_use"].items() if pk(p) and not pk(p)[1]}
            for p, d in M["dps"].items():
                k = pk(p)
                if not k or k[1] or ptype(p) != "預估":
                    continue
                if h["status"] != "穩定":
                    rows_out.append({"file": fn, "ticker": code, "period": p, "dps": d, "payout": None, "ref": None, "status": "未驗", "detail": "前五年配息率%s(%s)→ 不當參考" % (h["status"], h["why"])})
                    continue
                y = k[0] - h["lag"]
                if y not in eps or not eps[y]:
                    rows_out.append({"file": fn, "ticker": code, "period": p, "dps": d, "payout": None, "ref": h["mean"], "status": "未驗", "detail": "表裡沒有對應年度(%s)的稀釋 EPS" % ("20%02d" % y)})
                    continue
                po = d / eps[y] * 100
                band = max(10.0, 2 * h["sd"])
                ok = abs(po - h["mean"]) <= band
                rows_out.append({"file": fn, "ticker": code, "period": p, "dps": d, "payout": round(po, 1), "ref": h["mean"], "status": "PASS" if ok else "FAIL",
                                 "detail": "DPS %s ÷ %s 稀釋 EPS %s = %.1f%% vs 前五年 %s 均值 %.1f%% ± %.1f" % (d, "20%02d" % y, eps[y], po, h["align"], h["mean"], band)})
    od = rep / "payout"
    od.mkdir(parents=True, exist_ok=True)
    (od / "PAYOUT_HISTORY_latest.json").write_text(json.dumps({"rule": "前五年穩定才有參考價值 · 標準差 ≤ %.0f 個百分點" % SD_MAX, "history": hist, "checks": rows_out}, ensure_ascii=False, indent=1, default=str),
                                                   encoding="utf-8")
    with (od / "PAYOUT_CHECK_latest.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["file", "ticker", "period", "dps", "payout", "ref", "status", "detail"])
        w.writeheader()
        w.writerows(rows_out)
    return {"tickers": len(hist), "hist": dict(Counter(v["status"] for v in hist.values())), "align": dict(Counter(v.get("align") for v in hist.values() if v["status"] == "穩定")),
            "checks": dict(Counter(x["status"] for x in rows_out)), "db": {"eps": len(dbe), "div": len(dbd)}, "fails": [x for x in rows_out if x["status"] == "FAIL"][:3]}


def _lines_v182(o: dict) -> list:
    L = ["[計] 前五年配息率(資料庫 EPS %d 檔 · 股利 %d 檔)· %d 檔:穩定 %d · 不穩定 %d · 年數不足 %d · 沒有資料 %d · DPS 對應 %s" % (
        o["db"]["eps"], o["db"]["div"], o["tickers"], o["hist"].get("穩定", 0), o["hist"].get("不穩定", 0), o["hist"].get("年數不足", 0), o["hist"].get("沒有資料", 0),
        " · ".join("%s %d" % kv for kv in o["align"].items()) or "—"),
         "[計] 預估配息率 vs 前五年穩定區間 · PASS %d · FAIL %d · 未驗 %d" % (o["checks"].get("PASS", 0), o["checks"].get("FAIL", 0), o["checks"].get("未驗", 0))]
    for x in o["fails"]:
        L.append("[計] 配息率偏離 · %s · %s · %s" % (x["file"][:28], x["period"], x["detail"][:90]))
    if not o["db"]["div"]:
        L.append("[計] 資料庫沒有股利歷史 → 前五年配息率無法判斷(請 VDF 補 · 本版不猜)")
    return L


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()
    if args[:1] == ["payout"] or (args[:1] in (["auto"], ["findata"], ["findata2"], ["valuation"]) and "--resume" not in args):
        rc = PRIOR.main(args) if args[:1] != ["payout"] else 0
        L = _lines_v182(payout_run())
        for l in L:
            print(l)
        if args[:1] == ["auto"]:
            pk = _rep() / "auto" / "VRN_AI_PACK_latest.md"
            if pk.exists():
                old = [l for l in pk.read_text(encoding="utf-8").splitlines() if l.strip()]
                nxt = [l for l in old if l.startswith("NEXT:")] or ["NEXT: 依本包修 → 再跑 auto"]
                pk.write_text("\n".join(([l for l in old if not l.startswith("NEXT:")] + L)[:299] + nxt[:1]) + "\n", encoding="utf-8")
                ac = _resolve("aiverb_compress")
                if ac:
                    print("[計] AI 包(含前五年配息率)· %s" % ac(pk, nxt[0].replace("NEXT: ", ""))[1])
        return rc
    return PRIOR.main(args)


def selftest() -> int:
    import shutil
    import tempfile
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)
    eps = {19: 10.0, 20: 8.0, 21: 12.0, 22: 9.0, 23: 11.0, 24: 10.0}
    dps = {20: 6.0, 21: 4.9, 22: 7.1, 23: 5.5, 24: 6.6}
    h = payout_history(eps, dps)
    chk("① 前五年兩種對應:DPS ÷ 前一年 EPS ≈ 60%%(標準差 %.1f)比 ÷ 同年(標準差 %.1f)穩 → DPS 對應前一年 EPS · 穩定 → 有參考價值" % (h["sd"], h["alts"]["同年 EPS"]["sd"]),
        h["status"] == "穩定" and h["align"] == "前一年 EPS" and abs(h["mean"] - 60) < 2 and h["alts"]["同年 EPS"]["sd"] > h["sd"])
    hu = payout_history(eps, {20: 2.0, 21: 9.0, 22: 3.0, 23: 10.0, 24: 1.0})
    hn = payout_history(eps, {23: 5.5, 24: 6.6})
    chk("② 不穩定(標準差 > 10)→ 不當參考 · 只有 2 年 → 年數不足", hu["status"] == "不穩定" and hn["status"] == "年數不足")
    td = Path(tempfile.mkdtemp(prefix="vrn182-"))
    saved = os.environ.get("VIA_VRN_HEALTH_OUT")
    try:
        import duckdb
        vdb = td / "vdb"
        vdb.mkdir()
        con = duckdb.connect()
        con.execute("create table d as select * from (values ('2330', 2024, 18.0), ('2330', 2025, 20.0)) t(stock_id, year, cash_dividend)")
        con.execute("copy d to '%s' (format parquet)" % (vdb / "tw__tw_dividends.parquet"))
        dd = db_dividends(vdb)
        chk("③ 資料庫股利歷史(唯讀 · 依欄名認欄)→ 2330 {24: 18, 25: 20}", dd.get("2330") == {24: 18.0, 25: 20.0})
        os.environ["VIA_VRN_HEALTH_OUT"] = str(td / "rep")
        (td / "rep" / "restore").mkdir(parents=True)
        R = lambda lab, std, vals: {"label_raw": lab, "std": std, "cells": [{"period": k, "value": v} for k, v in vals.items()]}  # noqa: E731
        for i, d26 in enumerate((18.0, 30.0)):
            (td / "rep" / "restore" / ("0%d_x.json" % i)).write_text(json.dumps({"document_meta": {"file": "R%d.pdf" % i, "ticker": "1111"}, "tables": [{"id": "T1", "status": "還原無誤", "rows": [
                R("Diluted EPS", "eps", {"2025F": 30.0, "2026F": 28.0}), R("DPS (NT$)", "", {"2026F": d26})]}]}, ensure_ascii=False), encoding="utf-8")
        o = payout_run(dbe={"1111": {y: {"diluted": v} for y, v in eps.items()}}, dbd={"1111": dps})
        js = {x["file"]: x for x in json.loads((td / "rep" / "payout" / "PAYOUT_HISTORY_latest.json").read_text(encoding="utf-8"))["checks"]}
        chk("④ 預估配息率:2026F DPS 18 ÷ 2025F(前一年)稀釋 EPS 30 = 60% → 在前五年 60% ± 10 內 → 過 · DPS 30 → 100% → 偏離 → 不符",
            js["R0.pdf"]["status"] == "PASS" and js["R0.pdf"]["payout"] == 60.0 and js["R1.pdf"]["status"] == "FAIL")
        o2 = payout_run(dbe={}, dbd={})
        chk("⑤ 資料庫沒有股利 / EPS → 前五年無法判斷 → 照實標「沒有資料」· 預估配息率不驗(不猜)", o2["hist"].get("沒有資料") == 1 and not o2["checks"].get("PASS") and not o2["checks"].get("FAIL"))
    finally:
        if saved is None:
            os.environ.pop("VIA_VRN_HEALTH_OUT", None)
        else:
            os.environ["VIA_VRN_HEALTH_OUT"] = saved
        shutil.rmtree(td, ignore_errors=True)
    me = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 最新有版號加速器橋 [VIA:ACCEL-BRIDGE:v0111] · 自帶多程序墊片", "[VIA:ACCEL-BRIDGE:v0111]" in me and _job_entry.__module__ in ("__main__", __name__))
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("⑦ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    print("[計] VRN_SystemManager_v0182 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
