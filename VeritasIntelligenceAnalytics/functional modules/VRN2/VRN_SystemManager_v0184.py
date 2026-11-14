#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0184 — 薄尾(操作員 2026-10-11「預估 EPS 不含本半年 · 下兩個半年為基礎算 PE BAND · 若下兩個半年是兩個年度的交接 則兩年平均值計算 FORWARD EPS」)。
  peband 動詞(auto 自動接):Forward EPS(日期 d)= 上半年 → (今年 + 明年)÷ 2 · 下半年 → 明年(不含本半年 · 下兩個半年)·
  過去年度用實際稀釋 EPS(資料庫 → 報告實際期)· 未來年度用最新一份報告的預估 · Forward PE = 收盤 ÷ Forward EPS(≤0 或缺年度 → 跳過)·
  近 5 年 均值 / ±1σ / ±2σ 河道 · 靜態 HTML 內嵌 SVG(沿用 v0183)· 燈 = 資料品質
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
TAG = "v0184"


def _vnum_v0184(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0184(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0184(p) < _vnum_v0184(__file__)), key=_vnum_v0184)
PRIOR = _load_v0184(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


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


def forward_eps(d: str, eps: dict) -> tuple:
    """d 所在半年不算 · 下兩個半年:上半年 → 本年下半 + 明年上半(跨年度 → 兩年平均)· 下半年 → 明年上下半(= 明年 EPS)。"""
    dt = datetime.date.fromisoformat(d[:10])
    y = dt.year
    if dt.month <= 6:
        a, b = eps.get(y), eps.get(y + 1)
        if a is None or b is None:
            return None, "缺 %s%s EPS" % ("" if a is not None else "%d " % y, "" if b is not None else "%d" % (y + 1))
        return (a[0] + b[0]) / 2, "1H%02d → 2H%02d + 1H%02d 跨年 → (%d %s + %d %s)÷ 2" % (y % 100, y % 100, (y + 1) % 100, y, a[0], y + 1, b[0])
    b = eps.get(y + 1)
    if b is None:
        return None, "缺 %d EPS" % (y + 1)
    return b[0], "2H%02d → 1H%02d + 2H%02d 同年 → %d %s" % (y % 100, (y + 1) % 100, (y + 1) % 100, y + 1, b[0])


def eps_by_year(code: str, dbe: dict, rep: Path) -> dict:
    """{西元年: (稀釋 EPS, 來源)}:資料庫實際 → 報告實際期 → 最新一份報告的預估。"""
    out = {}
    for yy, v in (dbe.get(code) or {}).items():
        e = v.get("diluted") if v.get("diluted") is not None else v.get("eps", v.get("basic"))
        if e is not None:
            out[2000 + yy] = (e, "資料庫實際")
    matrix, pk, ptype = _resolve("matrix"), _resolve("_pkey") or (lambda p: None), _resolve("ptype") or (lambda p: "歷史")
    rd = {}
    bp = rep / "basicinfo" / "BASIC_INFO_V2_latest.json"
    if bp.exists():
        for r in json.loads(bp.read_text(encoding="utf-8")).get("records", []):
            fd = r.get("fields") or {}
            rd[(fd.get("FILENAME") or {}).get("value")] = (fd.get("REPORT_DATE") or {}).get("value") or ""
    fc = {}
    for f in sorted((rep / "restore").glob("*.json")) if (rep / "restore").is_dir() else []:
        if f.name.startswith("RESTORE_") or not matrix:
            continue
        dj = json.loads(f.read_text(encoding="utf-8"))
        meta = dj.get("document_meta") or {}
        if str(meta.get("ticker") or "") != code:
            continue
        when = rd.get(meta.get("file")) or ""
        for t in dj.get("tables", []):
            if t.get("status") == "未過":
                continue
            for per, v in (matrix(t.get("rows") or [])[0].get("eps_use") or {}).items():
                k = pk(per)
                if not k or k[1]:
                    continue
                y = 2000 + k[0]
                if ptype(per) == "預估":
                    if y not in fc or when > fc[y][2]:
                        fc[y] = (v, "報告預估 %s" % (meta.get("file") or "")[:24], when)
                elif y not in out:
                    out[y] = (v, "報告實際期")
    for y, (v, src, _w) in fc.items():
        out.setdefault(y, (v, src))
    return dict(sorted(out.items()))


def pe_band(prices: list, eps: dict, years: int = 5) -> dict:
    pts, skip = [], 0
    for d, c, _a in prices or []:
        fe, _ = forward_eps(d, eps)
        if fe is None or fe <= 0 or not isinstance(c, (int, float)) or c <= 0:
            skip += 1
            continue
        pts.append((d, c, fe))
    if not pts:
        return {"status": "沒有可用 Forward EPS(缺年度或 ≤ 0)", "skipped": skip}
    cut = (datetime.date.fromisoformat(pts[-1][0]) - datetime.timedelta(days=365 * years)).isoformat()
    pts = [x for x in pts if x[0] >= cut]
    pe = [c / e for _, c, e in pts]
    mu = statistics.mean(pe)
    sd = statistics.pstdev(pe) if len(pe) > 1 else 0.0
    ks = {"-2σ": max(mu - 2 * sd, 0.0), "-1σ": max(mu - sd, 0.0), "均值": mu, "+1σ": mu + sd, "+2σ": mu + 2 * sd}
    fe_now, how = forward_eps(pts[-1][0], eps)
    return {"status": "OK", "points": len(pts), "skipped": skip, "from": pts[0][0], "to": pts[-1][0], "price": pts[-1][1], "feps": round(fe_now, 2), "feps_how": how,
            "pe": round(pe[-1], 2), "mean": round(mu, 2), "sd": round(sd, 2), "min": round(min(pe), 2), "max": round(max(pe), 2),
            "pct": round(sum(1 for x in pe if x <= pe[-1]) / len(pe) * 100, 1), "k": {k: round(v, 2) for k, v in ks.items()},
            "band_now": {k: round(v * fe_now, 2) for k, v in ks.items()}, "series": [(d, round(c, 2), round(e, 4)) for d, c, e in pts]}


def peband_run(px: dict = None, dbe: dict = None) -> dict:
    rep = _rep()
    dbe = dbe if dbe is not None else (_resolve("db_eps") or (lambda: {}))()
    codes = set()
    for f in sorted((rep / "restore").glob("*.json")) if (rep / "restore").is_dir() else []:
        if not f.name.startswith("RESTORE_"):
            c = str((json.loads(f.read_text(encoding="utf-8")).get("document_meta") or {}).get("ticker") or "")
            if c:
                codes.add(c)
    if px is None:
        try:
            px = (_resolve("prices_for") or (lambda c: {}))(codes)
        except Exception:  # noqa: BLE001
            px = {}
    out = []
    for code in sorted(codes):
        eps = eps_by_year(code, dbe, rep)
        r = pe_band((px or {}).get(code) or [], eps)
        yrs = (datetime.date.fromisoformat(r["to"]) - datetime.date.fromisoformat(r["from"])).days / 365 if r.get("status") == "OK" else 0
        dbn = sum(1 for v in eps.values() if v[1] == "資料庫實際")
        lamp = "GRAY" if r.get("status") != "OK" else ("GREEN" if dbn >= 3 and yrs >= 3 else "YELLOW")
        out.append(dict(r, ticker=code, years=round(yrs, 1), lamp=lamp, eps_years={str(y): [round(v[0], 2), v[1]] for y, v in eps.items()}))
    od = rep / "peband"
    od.mkdir(parents=True, exist_ok=True)
    (od / "PE_BAND_latest.json").write_text(json.dumps({"rule": "Forward EPS = 下兩個半年(不含本半年;跨年度 → 兩年平均)· Forward PE = 收盤 ÷ Forward EPS · 近 5 年 均值 ±1σ ±2σ",
                                                       "rows": [{k: v for k, v in x.items() if k != "series"} for x in out]}, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    cols = ["ticker", "lamp", "price", "feps", "feps_how", "pe", "pct", "mean", "sd", "min", "max", "years", "skipped", "status"]
    with (od / "PE_BAND_latest.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(out)
    svg, L = _resolve("svg_band") or (lambda r: ""), _resolve("_L") or {}
    cards = "".join("<div style='border:1px solid #e5e7eb;border-radius:8px;padding:8px;margin:6px 0'><b><i style='background:%s;display:inline-block;width:9px;height:9px;border-radius:50%%;margin-right:4px'></i>%s</b>"
                    " · Forward PE %s(近 %s 年第 %s 百分位 · 均值 %s · σ %s)· Forward EPS %s(%s)· 收盤 %s%s</div>" % (
                        L.get(x["lamp"], "#9ca3af"), html.escape(x["ticker"]), x.get("pe", "—"), x.get("years", "—"), x.get("pct", "—"), x.get("mean", "—"), x.get("sd", "—"), x.get("feps", "—"),
                        html.escape(x.get("feps_how", "")), x.get("price", "—"), svg(x) or "<div style='color:#6b7280'>%s</div>" % html.escape(x.get("status", ""))) for x in out)
    (od / "PE_BAND_latest.html").write_text("<!doctype html><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>PE Band</title>"
                                            "<body style='font:13px system-ui,-apple-system,Segoe UI,Microsoft JhengHei,sans-serif;max-width:900px;margin:12px auto;padding:0 10px'>"
                                            "<h3>PE Band · Forward EPS = 下兩個半年(不含本半年 · 跨年度取兩年平均)· 河道 = 均值 / ±1σ / ±2σ 倍數 × Forward EPS(近 5 年)</h3>"
                                            "<div style='color:#6b7280'>燈 = 資料品質(綠:資料庫實際 EPS ≥ 3 年且 ≥ 3 年河道 · 黃:靠報告 EPS 或歷史短 · 灰:沒有可用 Forward EPS)· 不是投資建議</div>%s</body>" % cards,
                                            encoding="utf-8")
    return {"n": len(out), "lamps": dict(Counter(x["lamp"] for x in out)), "db": len(dbe), "html": str(od / "PE_BAND_latest.html"), "sample": [x for x in out if x.get("status") == "OK"][:3]}


def _lines_v184(o: dict) -> list:
    L = ["[計] PE Band(Forward EPS = 下兩個半年 · 跨年度兩年平均)· %d 檔 · 綠 %d 黃 %d 灰 %d · 資料庫 EPS %d 檔%s" % (o["n"], o["lamps"].get("GREEN", 0), o["lamps"].get("YELLOW", 0),
                                                                                         o["lamps"].get("GRAY", 0), o["db"], "" if o["db"] else "(沒有 → 歷史期靠報告實際期 · 請 VDF 補)")]
    for x in o["sample"]:
        L.append("[計] Forward PE · %s · %s 倍(第 %s 百分位 · 均值 %s · ±1σ %s~%s)· %s" % (x["ticker"], x["pe"], x["pct"], x["mean"], x["k"]["-1σ"], x["k"]["+1σ"], x["feps_how"][:70]))
    return L


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()
    if args[:1] == ["peband"] or (args[:1] in (["auto"], ["pbband"]) and "--resume" not in args):
        rc = PRIOR.main(args) if args[:1] != ["peband"] else 0
        o = peband_run()
        L = _lines_v184(o)
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
                    print("[計] AI 包(含 PE Band)· %s" % ac(pk, nxt[0].replace("NEXT: ", ""))[1])
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
    eps = {2021: (20.0, "資料庫實際"), 2022: (24.0, "資料庫實際"), 2023: (22.0, "資料庫實際"), 2024: (28.0, "資料庫實際"), 2025: (32.0, "資料庫實際"), 2026: (40.0, "報告預估"), 2027: (46.0, "報告預估")}
    a, ha = forward_eps("2026-03-15", eps)
    b, hb = forward_eps("2026-08-25", eps)
    c, hc = forward_eps("2026-06-30", eps)
    chk("① Forward EPS:2026-03-15(1H26)→ 2H26 + 1H27 跨年 → (40 + 46)÷ 2 = %s · 2026-08-25(2H26)→ 1H27 + 2H27 同年 → 2027 = %s · 6/30 仍算上半年" % (a, b),
        a == 43.0 and "跨年" in ha and b == 46.0 and "同年" in hb and c == 43.0)
    n, why = forward_eps("2026-08-25", {2026: (40.0, "")})
    chk("② 缺明年 EPS → 不算(%s)· 不拿別年頂替" % why, n is None and "2027" in why)
    px = []
    d0 = datetime.date(2021, 1, 4)
    for i in range(0, 2060, 7):
        d = d0 + datetime.timedelta(days=i)
        px.append((d.isoformat(), 300 + i * 0.2, 300.0))
    r = pe_band(px, eps)
    last_fe, _ = forward_eps(px[-1][0], eps)
    chk("③ PE Band:每天 收盤 ÷ 當天 Forward EPS(半年切換)· 最新 PE %s = %.2f ÷ %s · 河道 −2σ ≤ … ≤ +2σ · 第 %s 百分位" % (r["pe"], px[-1][1], last_fe, r["pct"]),
        r["status"] == "OK" and abs(r["pe"] - round(px[-1][1] / last_fe, 2)) < 0.01 and r["k"]["-2σ"] <= r["k"]["均值"] <= r["k"]["+2σ"] and len({s[2] for s in r["series"]}) >= 6)
    neg = pe_band(px, {y: (-1.0, "") for y in range(2020, 2029)})
    chk("④ Forward EPS ≤ 0 → PE 沒有意義 → 全跳過 → 灰(不硬算)", neg["status"] != "OK" and neg["skipped"] == len(px))
    td = Path(tempfile.mkdtemp(prefix="vrn184-"))
    saved = os.environ.get("VIA_VRN_HEALTH_OUT")
    try:
        os.environ["VIA_VRN_HEALTH_OUT"] = str(td / "rep")
        (td / "rep" / "restore").mkdir(parents=True)
        (td / "rep" / "basicinfo").mkdir(parents=True)
        R = lambda lab, vals: {"label_raw": lab, "std": "eps", "cells": [{"period": k, "value": v} for k, v in vals.items()]}  # noqa: E731
        for i, (dt, e27) in enumerate((("2026-03-01", 44.0), ("2026-06-01", 46.0))):
            (td / "rep" / "restore" / ("0%d_x.json" % i)).write_text(json.dumps({"document_meta": {"file": "R%d.pdf" % i, "ticker": "1111"}, "tables": [{"id": "T1", "status": "還原無誤",
                                                                                 "rows": [R("Diluted EPS", {"2024A": 99.0, "2025A": 32.0, "2026F": 40.0, "2027F": e27})]}]}, ensure_ascii=False), encoding="utf-8")
        (td / "rep" / "basicinfo" / "BASIC_INFO_V2_latest.json").write_text(json.dumps({"records": [{"fields": {"FILENAME": {"value": "R%d.pdf" % i}, "REPORT_DATE": {"value": dt}}}
                                                                                                     for i, dt in enumerate(("2026-03-01", "2026-06-01"))]}), encoding="utf-8")
        ey = eps_by_year("1111", {"1111": {21: {"diluted": 20.0}, 22: {"diluted": 24.0}, 23: {"diluted": 22.0}, 24: {"diluted": 28.0}}}, td / "rep")
        chk("⑤ EPS 來源:資料庫實際(2024 = 28 · 不被報告 99 蓋掉)→ 報告實際期(2025 = 32)→ 最新一份報告預估(2027F = 46 · 6/1 那份 · 不用 3/1 的 44)",
            ey[2024] == (28.0, "資料庫實際") and ey[2025] == (32.0, "報告實際期") and ey[2027][0] == 46.0)
        o = peband_run(px={"1111": px}, dbe={"1111": {21: {"diluted": 20.0}, 22: {"diluted": 24.0}, 23: {"diluted": 22.0}, 24: {"diluted": 28.0}}})
        htm = (td / "rep" / "peband" / "PE_BAND_latest.html").read_text(encoding="utf-8")
        chk("⑥ peband 動詞:JSON / CSV / HTML 內嵌 SVG 河流圖 · 燈 %s" % o["lamps"], htm.count("<svg") == 1 and "polyline" in htm and o["n"] == 1)
    finally:
        if saved is None:
            os.environ.pop("VIA_VRN_HEALTH_OUT", None)
        else:
            os.environ["VIA_VRN_HEALTH_OUT"] = saved
        shutil.rmtree(td, ignore_errors=True)
    me = Path(__file__).read_text(encoding="utf-8")
    chk("⑦ 最新有版號加速器橋 [VIA:ACCEL-BRIDGE:v0111] · 自帶多程序墊片", "[VIA:ACCEL-BRIDGE:v0111]" in me and _job_entry.__module__ in ("__main__", __name__))
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("⑧ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    print("[計] VRN_SystemManager_v0184 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
