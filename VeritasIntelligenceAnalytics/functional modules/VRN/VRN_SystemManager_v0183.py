#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0183 — 薄尾(操作員 2026-10-11「BVPS 最新值跟股價形成 PBR · PB BAND 形成」)。
  pbband 動詞(auto 自動接):PBR = 最新收盤 ÷ 最新 BVPS(資料庫 → 報告實際期 → 報告預估期 · 標來源 / 期間)·
  PB Band = 每天收盤 ÷ 當時最新 BVPS(階梯)→ 均值 / ±1σ / ±2σ 倍數 × BVPS = 五條河道 · 目前 PBR 百分位 · 用原始收盤(PBR 比當時股價 / 當時淨值;adj 會低估過去 PBR)
  燈 = 資料品質(綠:資料庫 BVPS 序列 ≥ 3 年 · 黃:只有報告 BVPS / 歷史短 · 灰:沒有 BVPS)· 靜態 HTML 內嵌 SVG(零伺服器 · 零外部套件)
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

import bisect
import csv
import datetime
import html
import importlib.util
import json
import os
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0183"


def _vnum_v0183(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0183(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0183(p) < _vnum_v0183(__file__)), key=_vnum_v0183)
PRIOR = _load_v0183(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


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


def db_bvps(vdb: Path = None) -> dict:
    """資料庫每股淨值(唯讀 · 依欄名認欄)→ {代號: [(期末日, BVPS)]}。"""
    vdb = vdb or (_resolve("_vdb") or (lambda: Path("")))()
    out = {}
    files = sorted(p for p in Path(vdb).glob("*.parquet") if re.search(r"bvps|book|balance|fin|fundamental|statement|淨值", p.name, re.I)) if vdb and Path(vdb).is_dir() else []
    pdate = _resolve("period_date") or (lambda s: "")
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
        bv = next((c for c in cols if re.search(r"(?i)bvps|每股淨值|book_value_per_share|nav_per_share", c)), None)
        code = next((c for c in cols if re.search(r"(?i)^(code|stock_id|ticker|symbol|公司代號|證券代號|代號)$", c)), None)
        per = next((c for c in cols if re.search(r"(?i)^(date|period|quarter|year|fy|年度|年季|期別)$", c)), None)
        if not (bv and code and per):
            continue
        for row in con.execute('select "%s", "%s", "%s" from read_parquet(\'%s\')' % (code, per, bv, str(p).replace("'", "''"))).fetchall():
            s = str(row[1])
            d = s[:10] if re.fullmatch(r"\d{4}-\d{2}-\d{2}.*", s) else pdate(s)
            try:
                v = float(row[2])
            except (TypeError, ValueError):
                continue
            if d and v > 0:
                out.setdefault(re.sub(r"\.TWO?$", "", str(row[0]).strip()), []).append((d, v))
    return {k: sorted(set(v)) for k, v in out.items()}


def report_bvps(rep: Path) -> dict:
    """報告表格的 BVPS(名稱規則 · 詞庫沒有 bvps 鍵)→ {代號: [(期末日, BVPS, 期間, 預估?)]}。"""
    matrix, pdate, ptype = _resolve("matrix"), _resolve("period_date") or (lambda s: ""), _resolve("ptype") or (lambda p: "歷史")
    out = {}
    for f in sorted((rep / "restore").glob("*.json")) if (rep / "restore").is_dir() else []:
        if f.name.startswith("RESTORE_") or not matrix:
            continue
        dj = json.loads(f.read_text(encoding="utf-8"))
        code = str((dj.get("document_meta") or {}).get("ticker") or "")
        for t in dj.get("tables", []):
            if t.get("status") == "未過":
                continue
            for per, v in (matrix(t.get("rows") or [])[0].get("bvps") or {}).items():
                d = pdate(per)
                if d and v > 0:
                    out.setdefault(code, {})[d] = (d, v, per, ptype(per) == "預估")
    return {k: sorted(v.values()) for k, v in out.items()}


def pb_band(prices: list, bv_hist: list, years: int = 5) -> dict:
    """prices = [(日期, close, adj)] · bv_hist = [(期末日, BVPS)] 由舊到新 → 每天 PBR(當時最新 BVPS 階梯)· 均值 / ±1σ / ±2σ · 目前百分位。"""
    if not bv_hist:
        return {"status": "沒有 BVPS"}
    ds = [d for d, _ in bv_hist]
    pts = []
    for d, c, _a in prices or []:
        i = bisect.bisect_right(ds, d) - 1
        if i >= 0 and isinstance(c, (int, float)) and c > 0:
            pts.append((d, c, bv_hist[i][1]))
    if not pts:
        return {"status": "股價期間沒有可用 BVPS"}
    cut = (datetime.date.fromisoformat(pts[-1][0]) - datetime.timedelta(days=365 * years)).isoformat()
    pts = [x for x in pts if x[0] >= cut]
    pbr = [c / b for _, c, b in pts]
    mu = statistics.mean(pbr)
    sd = statistics.pstdev(pbr) if len(pbr) > 1 else 0.0
    ks = {"-2σ": max(mu - 2 * sd, 0.0), "-1σ": max(mu - sd, 0.0), "均值": mu, "+1σ": mu + sd, "+2σ": mu + 2 * sd}
    cur = pbr[-1]
    pct = round(sum(1 for x in pbr if x <= cur) / len(pbr) * 100, 1)
    return {"status": "OK", "points": len(pts), "from": pts[0][0], "to": pts[-1][0], "price": pts[-1][1], "bvps": pts[-1][2], "pbr": round(cur, 2), "mean": round(mu, 2), "sd": round(sd, 2),
            "min": round(min(pbr), 2), "max": round(max(pbr), 2), "pct": pct, "k": {k: round(v, 2) for k, v in ks.items()},
            "band_now": {k: round(v * pts[-1][2], 2) for k, v in ks.items()}, "series": [(d, round(c, 2), round(b, 4)) for d, c, b in pts]}


def svg_band(r: dict, w: int = 640, h: int = 220) -> str:
    s = r.get("series") or []
    if len(s) < 2:
        return ""
    xs = list(range(len(s)))
    ys = [c for _, c, _ in s] + [k * b for _, _, b in s for k in r["k"].values()]
    lo, hi = min(ys), max(ys)
    X = lambda i: 30 + i * (w - 40) / max(len(s) - 1, 1)  # noqa: E731
    Y = lambda v: h - 20 - (v - lo) * (h - 30) / ((hi - lo) or 1)  # noqa: E731
    col = {"-2σ": "#93c5fd", "-1σ": "#60a5fa", "均值": "#9ca3af", "+1σ": "#f59e0b", "+2σ": "#ef4444"}
    lines = ["<polyline fill='none' stroke='%s' stroke-width='1' stroke-dasharray='4 3' points='%s'/>" % (col[k], " ".join("%.1f,%.1f" % (X(i), Y(m * b)) for i, (_, _, b) in zip(xs, s)))
             for k, m in r["k"].items()]
    lines.append("<polyline fill='none' stroke='currentColor' stroke-width='1.6' points='%s'/>" % " ".join("%.1f,%.1f" % (X(i), Y(c)) for i, (_, c, _) in zip(xs, s)))
    lab = "".join("<text x='%d' y='%.1f' font-size='9' fill='%s'>%s %.2fx</text>" % (w - 8, Y(m * s[-1][2]), col[k], html.escape(k), m) for k, m in r["k"].items())
    return "<svg viewBox='0 0 %d %d' style='width:100%%;max-width:%dpx;height:auto' xmlns='http://www.w3.org/2000/svg' text-anchor='end'>%s%s<text x='30' y='%d' font-size='9' text-anchor='start'>%s</text><text x='%d' y='%d' font-size='9'>%s</text></svg>" % (
        w, h, w, "".join(lines), lab, h - 4, s[0][0], w - 10, h - 4, s[-1][0])


def pbband_run(px: dict = None, dbb: dict = None) -> dict:
    rep = _rep()
    rb = report_bvps(rep)
    dbb = dbb if dbb is not None else db_bvps()
    codes = sorted({c for c in rb if c} | set(dbb))
    if px is None:
        try:
            px = (_resolve("prices_for") or (lambda c: {}))(set(codes))
        except Exception:  # noqa: BLE001
            px = {}
    out = []
    for code in codes:
        if dbb.get(code):
            hist, src = dbb[code], "資料庫"
        else:
            act = [(d, v) for d, v, _, est in rb.get(code, []) if not est]
            hist, src = (act, "報告實際期") if act else ([(d, v) for d, v, _, _ in rb.get(code, [])], "報告預估期")
        r = pb_band((px or {}).get(code) or [], hist)
        yrs = (datetime.date.fromisoformat(r["to"]) - datetime.date.fromisoformat(r["from"])).days / 365 if r.get("status") == "OK" else 0
        lamp = "GRAY" if r.get("status") != "OK" else ("GREEN" if src == "資料庫" and yrs >= 3 else "YELLOW")
        latest = hist[-1] if hist else None
        out.append(dict(r, ticker=code, bvps_src=src, bvps_latest=latest[1] if latest else None, bvps_date=latest[0] if latest else "", years=round(yrs, 1), lamp=lamp))
    od = rep / "pbband"
    od.mkdir(parents=True, exist_ok=True)
    (od / "PB_BAND_latest.json").write_text(json.dumps({"rule": "PBR = 收盤 ÷ 當時最新 BVPS · 均值 ±1σ ±2σ · 近 5 年", "rows": [{k: v for k, v in x.items() if k != "series"} for x in out]},
                                                       ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    cols = ["ticker", "lamp", "bvps_latest", "bvps_date", "bvps_src", "price", "pbr", "pct", "mean", "sd", "min", "max", "years", "status"]
    with (od / "PB_BAND_latest.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(out)
    L = _resolve("_L") or {}
    cards = "".join("<div style='border:1px solid #e5e7eb;border-radius:8px;padding:8px;margin:6px 0'><b><i style='background:%s;display:inline-block;width:9px;height:9px;border-radius:50%%;margin-right:4px'></i>%s</b>"
                    " · PBR %s(近 %s 年第 %s 百分位 · 均值 %s · σ %s)· BVPS %s(%s · %s)· 收盤 %s%s</div>" % (
                        L.get(x["lamp"], "#9ca3af"), html.escape(x["ticker"]), x.get("pbr", "—"), x.get("years", "—"), x.get("pct", "—"), x.get("mean", "—"), x.get("sd", "—"), x.get("bvps_latest", "—"),
                        html.escape(x.get("bvps_src", "")), x.get("bvps_date", ""), x.get("price", "—"), svg_band(x) or "<div style='color:#6b7280'>%s</div>" % html.escape(x.get("status", ""))) for x in out)
    (od / "PB_BAND_latest.html").write_text("<!doctype html><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>PB Band</title>"
                                            "<body style='font:13px system-ui,-apple-system,Segoe UI,Microsoft JhengHei,sans-serif;max-width:900px;margin:12px auto;padding:0 10px'>"
                                            "<h3>PB Band · PBR = 收盤 ÷ 當時最新 BVPS · 河道 = 均值 / ±1σ / ±2σ 倍數 × BVPS(近 5 年 · 原始收盤)</h3>"
                                            "<div style='color:#6b7280'>燈 = 資料品質(綠:資料庫 BVPS ≥ 3 年 · 黃:只有報告 BVPS 或歷史短 · 灰:沒有 BVPS)· 不是投資建議</div>%s</body>" % cards, encoding="utf-8")
    return {"n": len(out), "lamps": dict(Counter(x["lamp"] for x in out)), "src": dict(Counter(x["bvps_src"] for x in out if x["lamp"] != "GRAY")), "db": len(dbb),
            "html": str(od / "PB_BAND_latest.html"), "sample": [x for x in out if x.get("status") == "OK"][:3]}


def _lines_v183(o: dict) -> list:
    L = ["[計] PB Band · %d 檔 · 綠 %d 黃 %d 灰 %d · BVPS 來源 %s · 資料庫 BVPS %d 檔%s" % (o["n"], o["lamps"].get("GREEN", 0), o["lamps"].get("YELLOW", 0), o["lamps"].get("GRAY", 0),
                                                                              " · ".join("%s %d" % kv for kv in o["src"].items()) or "—", o["db"], "" if o["db"] else "(沒有 → 只用報告 BVPS · 請 VDF 補)")]
    for x in o["sample"]:
        L.append("[計] PBR · %s · %s 倍(第 %s 百分位 · 均值 %s · ±1σ %s~%s)· BVPS %s(%s %s)" % (x["ticker"], x["pbr"], x["pct"], x["mean"], x["k"]["-1σ"], x["k"]["+1σ"], x["bvps_latest"], x["bvps_src"], x["bvps_date"]))
    return L


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()
    if args[:1] == ["pbband"] or (args[:1] == ["auto"] and "--resume" not in args):
        rc = PRIOR.main(args) if args[:1] != ["pbband"] else 0
        o = pbband_run()
        L = _lines_v183(o)
        for l in L:
            print(l)
        print("  [U/I] %s" % o["html"])
        if args[:1] == ["auto"]:
            pk = _rep() / "auto" / "VRN_AI_PACK_latest.md"
            if pk.exists():
                old = [l for l in pk.read_text(encoding="utf-8").splitlines() if l.strip()]
                nxt = [l for l in old if l.startswith("NEXT:")] or ["NEXT: 依本包修 → 再跑 auto"]
                pk.write_text("\n".join(([l for l in old if not l.startswith("NEXT:")] + L)[:299] + nxt[:1]) + "\n", encoding="utf-8")
                ac = _resolve("aiverb_compress")
                if ac:
                    print("[計] AI 包(含 PB Band)· %s" % ac(pk, nxt[0].replace("NEXT: ", ""))[1])
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
    px = []
    d0 = datetime.date(2021, 1, 4)
    for i in range(0, 1800, 7):
        d = d0 + datetime.timedelta(days=i)
        px.append((d.isoformat(), 100 + i * 0.05, 100.0))
    bv = [("2020-12-31", 50.0), ("2021-12-31", 55.0), ("2022-12-31", 60.0), ("2023-12-31", 64.0), ("2024-12-31", 70.0)]
    r = pb_band(px, bv)
    last = px[-1][1] / 70.0
    chk("① PBR = 收盤 ÷ 當時最新 BVPS(階梯):最新 %.2f ÷ 70 = %.2f · 2021 年用 BVPS 50" % (px[-1][1], last), r["status"] == "OK" and abs(r["pbr"] - round(last, 2)) < 0.01 and r["series"][0][2] == 50.0)
    chk("② 河道:均值 %s · ±1σ %s~%s · ±2σ %s~%s · 目前第 %s 百分位 · 河道價 = 倍數 × 最新 BVPS" % (r["mean"], r["k"]["-1σ"], r["k"]["+1σ"], r["k"]["-2σ"], r["k"]["+2σ"], r["pct"]),
        r["k"]["-2σ"] <= r["k"]["-1σ"] <= r["k"]["均值"] <= r["k"]["+1σ"] <= r["k"]["+2σ"] and abs(r["band_now"]["均值"] - r["k"]["均值"] * 70) <= 70 * 0.005 + 0.01 and 0 <= r["pct"] <= 100)
    chk("③ 沒有 BVPS → 灰(不硬算)· 股價早於所有 BVPS → 不可用", pb_band(px, [])["status"] == "沒有 BVPS" and pb_band([("2019-01-02", 10.0, 10.0)], bv)["status"] != "OK")
    td = Path(tempfile.mkdtemp(prefix="vrn183-"))
    saved = os.environ.get("VIA_VRN_HEALTH_OUT")
    try:
        import duckdb
        vdb = td / "vdb"
        vdb.mkdir()
        con = duckdb.connect()
        con.execute("create table b as select * from (values ('2330', '2023-12-31', 140.0), ('2330', '2024-12-31', 165.5)) t(stock_id, date, bvps)")
        con.execute("copy b to '%s' (format parquet)" % (vdb / "tw__tw_balance.parquet"))
        chk("④ 資料庫 BVPS(唯讀 · 依欄名認欄)→ 2330 兩期", db_bvps(vdb).get("2330") == [("2023-12-31", 140.0), ("2024-12-31", 165.5)])
        os.environ["VIA_VRN_HEALTH_OUT"] = str(td / "rep")
        (td / "rep" / "restore").mkdir(parents=True)
        R = lambda lab, vals: {"label_raw": lab, "std": "", "cells": [{"period": k, "value": v} for k, v in vals.items()]}  # noqa: E731
        (td / "rep" / "restore" / "01_x.json").write_text(json.dumps({"document_meta": {"file": "X.pdf", "ticker": "1111"}, "tables": [{"id": "T1", "status": "還原無誤", "rows": [
            R("每股淨值 BVPS (NT$)", {"2020A": 50.0, "2021A": 55.0, "2022A": 60.0, "2023A": 64.0, "2024A": 70.0, "2025F": 76.0})]}]}, ensure_ascii=False), encoding="utf-8")
        o = pbband_run(px={"1111": px, "2330": px}, dbb={"2330": [("2020-12-31", 100.0), ("2024-12-31", 165.5)]})
        rows = {x["ticker"]: x for x in json.loads((td / "rep" / "pbband" / "PB_BAND_latest.json").read_text(encoding="utf-8"))["rows"]}
        htm = (td / "rep" / "pbband" / "PB_BAND_latest.html").read_text(encoding="utf-8")
        chk("⑤ BVPS 來源優先:資料庫(2330 綠)> 報告實際期(1111 黃 · 用 2024A 70 · 不拿 2025F 預估)· HTML 內嵌 SVG 河流圖(零伺服器)",
            rows["2330"]["bvps_src"] == "資料庫" and rows["2330"]["lamp"] == "GREEN" and rows["1111"]["bvps_src"] == "報告實際期" and rows["1111"]["bvps_latest"] == 70.0
            and rows["1111"]["lamp"] == "YELLOW" and htm.count("<svg") == 2 and "polyline" in htm)
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
    print("[計] VRN_SystemManager_v0183 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
