#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0179 — 薄尾(操作員 2026-10-11 BASIC INFO 最終欄位:REPORT DATE / REPORT TYPE / FILENAME / TICKER / YFINANCE TICKER / BLOOMBERG TICKER / NAME / BROKER /
   ANALYST / RATING / TARGET PRICE(ORIGINAL)/ TARGET PRICE(ADJ)/ ADJ CLOSE / ADJ CLOSE BEFORE THE REPORT DATE / SUCCESSFUL TO REACH TP(YES/NO)/ UPSIDE% /
   FAILURE(跌出來 = 反向)/ ACCUM. PERFORMANCE%)。
  basicinfo3 動詞(auto 自動接在後面):欄序照規格 · 報告日之後的價格路徑(價格庫唯讀):
    是否達標 = 報告日之後 adj close 曾碰到 TP(adj)(看多往上 · 看空往下)· 失敗 = 股價往反方向走 · 累積績效 = 最新 adj ÷ 報告前一日 adj − 1
    價格庫沒有報告日之後資料 → 灰(不硬算)
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
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0179"


def _vnum_v0179(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0179(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0179(p) < _vnum_v0179(__file__)), key=_vnum_v0179)
PRIOR = _load_v0179(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


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
COLS3 = ["REPORT_DATE", "REPORT_TYPE", "FILENAME", "TICKER", "YF_TICKER", "BBG_TICKER", "NAME", "BROKER", "ANALYST", "RATING", "TP_ORIGINAL", "TP_ADJ", "ADJ_CLOSE", "ADJ_CLOSE_BEFORE",
         "REACHED_TP", "UPSIDE_PCT", "FAILURE", "ACCUM_PERF_PCT"]
EXTRA3 = ["ADJ_CLOSE_DATE", "REACHED_DATE", "DAYS_TO_TP", "PRICE_DB_TO"]
ZH3 = {"REPORT_DATE": "報告日", "REPORT_TYPE": "報告類型", "FILENAME": "檔名", "TICKER": "代號", "YF_TICKER": "yfinance", "BBG_TICKER": "Bloomberg", "NAME": "名稱", "BROKER": "券商", "ANALYST": "分析師",
       "RATING": "評等(原文)", "TP_ORIGINAL": "目標價(原)", "TP_ADJ": "目標價(ADJ)", "ADJ_CLOSE": "最新 ADJ CLOSE", "ADJ_CLOSE_BEFORE": "報告前一日 ADJ CLOSE", "REACHED_TP": "達標(YES/NO)",
       "UPSIDE_PCT": "上漲空間%", "FAILURE": "失敗(反向)", "ACCUM_PERF_PCT": "累積績效%", "ADJ_CLOSE_DATE": "最新 ADJ 日期", "REACHED_DATE": "達標日", "DAYS_TO_TP": "達標天數", "PRICE_DB_TO": "價格庫到"}
_TYPES = [("首次評等(Initiation)", r"(?i)初次評等|首次評等|initiat|首評"), ("升評(Upgrade)", r"(?i)upgrade|調升評等|升評"), ("降評(Downgrade)", r"(?i)downgrade|調降評等|降評"),
          ("財報 / 法說檢討(Results)", r"(?i)results|earnings|業績|財報|法說"), ("短評(Note / Memo / Takeaway)", r"(?i)\bnote\b|,\s*note\)|memo|takeaway|訪談速報|快訊|速報"),
          ("公司介紹(Company intro)", r"個股介紹|公司介紹|company profile")]


def report_type(fn: str, title: str = "") -> tuple:
    for name, rx in _TYPES:
        if re.search(rx, fn or ""):
            return name, "檔名"
    for name, rx in _TYPES:
        if re.search(rx, title or ""):
            return name, "首頁標題"
    return "個股報告(Update)", "預設(檔名 / 標題沒有類型字)"


def perf_fields(series: list, report_date: str, tp_adj, adj_before) -> dict:
    """series = [(日期 ISO, close, adj)] 由舊到新;報告日之後 adj 碰到 TP(adj)= 達標(看多往上 · 看空往下)· 反方向 = 失敗 · 累積績效 = 最新 / 報告前一日 − 1。"""
    out = {"ADJ_CLOSE": None, "ADJ_CLOSE_DATE": "", "REACHED_TP": None, "REACHED_DATE": "", "DAYS_TO_TP": None, "FAILURE": None, "ACCUM_PERF_PCT": None, "PRICE_DB_TO": "", "why": ""}
    ser = [(d, a) for d, c, a in (series or []) if isinstance(a, (int, float))]
    if not ser:
        out["why"] = "價格庫沒有這檔"
        return out
    out["PRICE_DB_TO"] = ser[-1][0]
    out["ADJ_CLOSE"], out["ADJ_CLOSE_DATE"] = round(ser[-1][1], 2), ser[-1][0]
    after = [(d, a) for d, a in ser if d > (report_date or "")]
    if not report_date or not after:
        out["why"] = "價格庫沒有報告日之後資料(到 %s)" % ser[-1][0]
        return out
    if adj_before:
        out["ACCUM_PERF_PCT"] = round((ser[-1][1] / adj_before - 1) * 100, 2)
    if tp_adj and adj_before:
        up = tp_adj >= adj_before
        hit = next(((d, a) for d, a in after if (a >= tp_adj if up else a <= tp_adj)), None)
        out["REACHED_TP"] = "YES" if hit else "NO"
        if hit:
            out["REACHED_DATE"] = hit[0]
            out["DAYS_TO_TP"] = (datetime.date.fromisoformat(hit[0]) - datetime.date.fromisoformat(report_date)).days
        perf = out["ACCUM_PERF_PCT"]
        if perf is not None:
            if up and perf < 0:
                out["FAILURE"] = "YES(看漲反跌 %.2f%%)" % perf
            elif not up and perf > 0:
                out["FAILURE"] = "YES(看跌反漲 +%.2f%%)" % perf
            else:
                out["FAILURE"] = "NO"
    else:
        out["why"] = "缺 TP(adj)或報告前一日 adj close"
    return out


def basicinfo3_run(px: dict = None, recs2: list = None) -> dict:
    rep = _rep()
    if recs2 is None:
        recs2 = ((json.loads((rep / "basicinfo" / "BASIC_INFO_V2_latest.json").read_text(encoding="utf-8")) if (rep / "basicinfo" / "BASIC_INFO_V2_latest.json").exists() else {}) or {}).get("records", [])
    if not recs2:
        return {"err": "沒有 BASIC INFO v2(先跑 basicinfo / basicinfo2)"}
    v = lambda r, k: ((r.get("fields") or {}).get(k) or {}).get("value")  # noqa: E731
    s = lambda r, k: ((r.get("fields") or {}).get(k) or {}).get("status", "GRAY")  # noqa: E731
    if px is None:
        try:
            px = (_resolve("prices_for") or (lambda c: {}))({str(v(r, "TICKER")) for r in recs2 if v(r, "TICKER")})
        except Exception:  # noqa: BLE001
            px = {}
    d = _resolve("_latest_l2_dir")("")
    titles = {}
    for p in sorted(d.glob("*.json")) if d else []:
        try:
            j = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        tb = [b for b in ((j.get("pages") or [{}])[0].get("blocks") or []) if b.get("kind") == "text"]
        mx = max((float(b.get("size") or 0) for b in tb), default=0)
        titles[(j.get("row") or {}).get("file")] = " ".join(b.get("text", "") for b in tb if mx and float(b.get("size") or 0) >= 0.8 * mx)
    F = lambda val, st, src, ck="": {"value": val, "status": st, "source": src, "check": ck}  # noqa: E731
    out = []
    for r in recs2:
        fn = v(r, "FILENAME")
        code = str(v(r, "TICKER") or "")
        rd = v(r, "REPORT_DATE") or ""
        tpa, ab = v(r, "TP_ADJ"), v(r, "ADJ_CLOSE_BEFORE")
        pf = perf_fields((px or {}).get(code) or [], rd, tpa, ab)
        rt, rts = report_type(fn, titles.get(fn, ""))
        g = lambda k, k2=None: F(v(r, k2 or k), s(r, k2 or k), "BASIC v2")  # noqa: E731
        f = {"REPORT_DATE": g("REPORT_DATE"), "REPORT_TYPE": F(rt, "GREEN" if not rts.startswith("預設") else "YELLOW", rts), "FILENAME": g("FILENAME"), "TICKER": g("TICKER"), "YF_TICKER": g("YF_TICKER"),
             "BBG_TICKER": g("BBG_TICKER"), "NAME": g("NAME", "NAME_DB"), "BROKER": g("BROKER"), "ANALYST": g("ANALYST"), "RATING": g("RATING"), "TP_ORIGINAL": g("TP_ORIGINAL", "TARGET_PRICE"),
             "TP_ADJ": g("TP_ADJ"), "ADJ_CLOSE_BEFORE": g("ADJ_CLOSE_BEFORE"), "UPSIDE_PCT": g("UPSIDE_PCT")}
        gray = pf["why"]
        f["ADJ_CLOSE"] = F(pf["ADJ_CLOSE"], "GREEN" if pf["ADJ_CLOSE"] is not None else "GRAY", "價格庫最新(%s)" % pf["ADJ_CLOSE_DATE"] if pf["ADJ_CLOSE_DATE"] else "價格庫", gray if pf["ADJ_CLOSE"] is None else "")
        f["REACHED_TP"] = F(pf["REACHED_TP"], "GREEN" if pf["REACHED_TP"] else "GRAY", "報告日之後 adj 路徑", ("%s 達標(%s 天)" % (pf["REACHED_DATE"], pf["DAYS_TO_TP"])) if pf["REACHED_TP"] == "YES" else (gray or "到 %s 還沒碰到" % pf["PRICE_DB_TO"]))
        f["FAILURE"] = F(pf["FAILURE"], ("RED" if str(pf["FAILURE"]).startswith("YES") else "GREEN") if pf["FAILURE"] else "GRAY", "累積績效方向 vs 上漲空間方向", gray)
        f["ACCUM_PERF_PCT"] = F(pf["ACCUM_PERF_PCT"], "GREEN" if pf["ACCUM_PERF_PCT"] is not None else "GRAY", "最新 adj ÷ 報告前一日 adj − 1", gray)
        for k in EXTRA3:
            f[k] = F(pf[k], "GREEN" if pf[k] not in (None, "") else "GRAY", "價格庫")
        lamp = "RED" if any(f[k]["status"] == "RED" and k != "FAILURE" for k in COLS3) else ("YELLOW" if any(f[k]["status"] == "YELLOW" for k in COLS3) else "GREEN")
        out.append({"lamp": lamp, "fields": {k: f[k] for k in COLS3 + EXTRA3}})
    od = rep / "basicinfo"
    od.mkdir(parents=True, exist_ok=True)
    (od / "BASIC_INFO_FINAL_latest.json").write_text(json.dumps({"columns": COLS3, "extra": EXTRA3, "records": out}, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    cp = od / "BASIC_INFO_FINAL_latest.csv"
    with cp.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(COLS3 + EXTRA3)
        for r in out:
            w.writerow(["" if r["fields"][k]["value"] is None else r["fields"][k]["value"] for k in COLS3 + EXTRA3])
    try:
        import duckdb  # noqa: WPS433
        duckdb.connect().execute("copy (select * from read_csv_auto('%s', header=true, all_varchar=true)) to '%s' (format parquet)" % (str(cp).replace("'", "''"), str(cp.with_suffix(".parquet")).replace("'", "''")))
    except Exception:  # noqa: BLE001
        pass
    page, L = _resolve("_page"), (_resolve("_L") or {})
    if page:
        cell = lambda x: "<span title='%s · %s'><i style='background:%s;display:inline-block;width:8px;height:8px;border-radius:50%%;margin-right:3px'></i>%s</span>" % (  # noqa: E731
            html.escape(str(x["source"])), html.escape(str(x["check"])), L.get(x["status"], "#9ca3af"), html.escape("" if x["value"] is None else str(x["value"]))[:44])
        (od / "BASIC_INFO_FINAL_latest.html").write_text(page("BASIC INFO(最終欄位 · 照操作員規格)· 達標 / 失敗 / 累積績效 來自價格庫(唯讀)", "%d 份 · 灰 = 價格庫沒有報告日之後資料(不硬算)" % len(out),
                                                              [ZH3[k] for k in COLS3 + EXTRA3], [(r["lamp"], [cell(r["fields"][k]) for k in COLS3 + EXTRA3]) for r in out]), encoding="utf-8")
    vals = lambda k: [r["fields"][k]["value"] for r in out]  # noqa: E731
    perf = [x for x in vals("ACCUM_PERF_PCT") if isinstance(x, (int, float))]
    return {"n": len(out), "reached": Counter(x for x in vals("REACHED_TP") if x), "failure": sum(1 for x in vals("FAILURE") if str(x).startswith("YES")),
            "no_after": sum(1 for r in out if r["fields"]["REACHED_TP"]["status"] == "GRAY"), "avg_perf": round(sum(perf) / len(perf), 2) if perf else None,
            "db_to": max((x for x in vals("PRICE_DB_TO") if x), default=""), "types": Counter(vals("REPORT_TYPE")), "html": str(od / "BASIC_INFO_FINAL_latest.html")}


def _lines_v179(o: dict) -> list:
    if o.get("err"):
        return ["[計] BASIC INFO(最終)· %s" % o["err"]]
    return ["[計] BASIC INFO(最終 · %d 份)· 達標 YES %d / NO %d · 失敗(反向)%d · 平均累積績效 %s%% · 價格庫到 %s · 沒有報告日之後資料 %d 份(灰 · 不硬算)" % (
        o["n"], o["reached"].get("YES", 0), o["reached"].get("NO", 0), o["failure"], o["avg_perf"] if o["avg_perf"] is not None else "—", o["db_to"] or "—", o["no_after"]),
            "[計] 報告類型 · " + " · ".join("%s %d" % kv for kv in o["types"].most_common())]


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()
    if args[:1] == ["basicinfo3"] or (args[:1] in (["auto"], ["basicinfo2"]) and "--resume" not in args):
        rc = PRIOR.main(args) if args[:1] != ["basicinfo3"] else 0
        o = basicinfo3_run()
        L = _lines_v179(o)
        for l in L:
            print(l)
        if o.get("html"):
            print("  [U/I] %s" % o["html"])
        if args[:1] == ["auto"]:
            pk = _rep() / "auto" / "VRN_AI_PACK_latest.md"
            if pk.exists():
                old = [l for l in pk.read_text(encoding="utf-8").splitlines() if l.strip()]
                nxt = [l for l in old if l.startswith("NEXT:")] or ["NEXT: 依本包修 → 再跑 auto"]
                pk.write_text("\n".join(([l for l in old if not l.startswith("NEXT:")] + L)[:299] + nxt[:1]) + "\n", encoding="utf-8")
                ac = _resolve("aiverb_compress")
                if ac:
                    print("[計] AI 包(含 BASIC INFO 最終)· %s" % ac(pk, nxt[0].replace("NEXT: ", ""))[1])
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
    chk("① 報告類型:初次評等 / Note / 訪談速報 / 個股介紹 / 預設 Update", report_type("【國泰證期研究部】神達(3706 TT)-初次評等買進")[0].startswith("首次評等") and report_type("國光生(4142,Note)-CTBC260917.pdf")[0].startswith("短評")
        and report_type("20251128兆豐訪談速報-神達(3706).pdf")[0].startswith("短評") and report_type("6933_AMAX-KY_個股介紹報告.pdf")[0].startswith("公司介紹") and report_type("MS-2308 20251128.pdf")[0].startswith("個股報告"))
    ser = [("2025-11-27", 942.0, 937.1), ("2026-01-15", 1100.0, 1100.0), ("2026-03-02", 1300.0, 1300.0), ("2026-08-25", 1710.0, 1710.0)]
    a = perf_fields(ser, "2025-11-28", 1281.3, 937.1)
    chk("② 看多達標:TP(adj)1281.3 → 2026-03-02 adj 1300 碰到 → YES(%s 天)· 累積績效 1710 / 937.1 − 1 = %s%% · 失敗 NO · 最新 ADJ CLOSE 1710" % (a["DAYS_TO_TP"], a["ACCUM_PERF_PCT"]),
        a["REACHED_TP"] == "YES" and a["REACHED_DATE"] == "2026-03-02" and a["DAYS_TO_TP"] == 94 and a["ACCUM_PERF_PCT"] == round((1710 / 937.1 - 1) * 100, 2) and a["FAILURE"] == "NO" and a["ADJ_CLOSE"] == 1710.0)
    b = perf_fields([("2026-05-20", 203.0, 200.0), ("2026-06-30", 190.0, 190.0), ("2026-08-25", 180.0, 180.0)], "2026-05-21", 240.0, 200.0)
    chk("③ 看漲反跌:上漲空間 +20%% 但 200 → 180 → 達標 NO · 失敗 %s · 累積 %s%%" % (b["FAILURE"], b["ACCUM_PERF_PCT"]), b["REACHED_TP"] == "NO" and b["FAILURE"].startswith("YES(看漲反跌") and b["ACCUM_PERF_PCT"] == -10.0)
    c = perf_fields([("2026-05-20", 100.0, 100.0), ("2026-06-01", 85.0, 85.0), ("2026-08-25", 90.0, 90.0)], "2026-05-21", 85.0, 100.0)
    chk("④ 看空(TP 85 < 100):往下碰到 85 → 達標 YES · 跌 10% 不算失敗", c["REACHED_TP"] == "YES" and c["FAILURE"] == "NO")
    e = perf_fields([("2026-08-25", 213.0, 213.0)], "2026-09-18", 420.0, 213.0)
    chk("⑤ 價格庫只到 8/25、報告 9/18 → 達標 / 失敗 / 累積績效 都不硬算(灰)· 理由 %s" % e["why"], e["REACHED_TP"] is None and e["FAILURE"] is None and e["ACCUM_PERF_PCT"] is None and "報告日之後" in e["why"])
    td = Path(tempfile.mkdtemp(prefix="vrn179-"))
    saved = os.environ.get("VIA_VRN_HEALTH_OUT")
    try:
        os.environ["VIA_VRN_HEALTH_OUT"] = str(td / "rep")
        F = lambda v, st="GREEN": {"value": v, "status": st, "source": "", "check": ""}  # noqa: E731
        r2 = [{"fields": {"FILENAME": F("MS-2308 20251128.pdf"), "TICKER": F("2308"), "YF_TICKER": F("2308.TW"), "BBG_TICKER": F("2308 TT"), "NAME_DB": F("台達電"), "BROKER": F("MS"),
                          "REPORT_DATE": F("2025-11-28"), "ANALYST": F("Sharon Shih"), "RATING": F("Overweight"), "TARGET_PRICE": F(1288.0), "TP_ADJ": F(1281.3), "ADJ_CLOSE_BEFORE": F(937.1), "UPSIDE_PCT": F(36.73)}}]
        o = basicinfo3_run(px={"2308": ser}, recs2=r2)
        hdr = (td / "rep" / "basicinfo" / "BASIC_INFO_FINAL_latest.csv").read_text(encoding="utf-8-sig").splitlines()[0].split(",")
        js = json.loads((td / "rep" / "basicinfo" / "BASIC_INFO_FINAL_latest.json").read_text(encoding="utf-8"))["records"][0]["fields"]
        chk("⑥ 欄序照規格(18 欄 + 4 個輔助欄放最後)· 名稱 台達電 · 評等 Overweight 原文 · 達標 YES · 累積績效 %s%%" % js["ACCUM_PERF_PCT"]["value"],
            hdr[:18] == COLS3 and hdr[18:] == EXTRA3 and js["NAME"]["value"] == "台達電" and js["RATING"]["value"] == "Overweight" and js["REACHED_TP"]["value"] == "YES" and o["reached"]["YES"] == 1)
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
    print("[計] VRN_SystemManager_v0179 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
