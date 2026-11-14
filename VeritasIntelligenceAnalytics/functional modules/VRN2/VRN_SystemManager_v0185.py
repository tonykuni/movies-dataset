#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0185 — 薄尾(操作員 2026-10-11「VRN SYSTEM MANAGER 根據目前的報告代碼提供給 VDF SYSTEM MANAGER 去擷取 FACTSET CONSENSUS
   TARGET PRICE LOW MEAN MEDIAN HIGH · EPS 預估值 · ANALYST COUNT · YAHOO.INFO CONSENSUS TARGET PRICE LOW MEAN MEDIAN HIGH · RATING · ANALYST COUNT 做參考合理性」)。
  consensus 動詞(auto 自動接):① 請求清單寫 VRN 自己的夾 VIA_Reports/vrn/contract/VRN_CONSENSUS_REQUEST_latest.json(代號 / yf / bbg / 名稱 / 券商 / 報告日 /
  券商目標價 / 券商預估 EPS · 附融合引擎 --codes 字串)· 三系統獨立:VRN 不寫 VDF 的檔 ② 唯讀 VDF 資料庫共識(VIA_CNYES_FactSet_YFinance_Consensus_Fusion_Engine
  輸出 consensus_long / *consensus*.parquet · 長表 / 寬表都認)③ 合理性:券商目標價 vs 共識 low~high(超出 → 紅)· 偏離中位數 >15% → 黃 · 券商 EPS vs 共識同年 >10% → 黃 ·
  分析師人數 / 評等列參考 · 沒有共識 → 灰(等 VDF 接共識動詞)
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
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0185"
METRICS = ("target_low", "target_mean", "target_median", "target_high", "target_analyst_count", "analyst_count", "recommendation_key", "recommendation_mean", "rating")


def _vnum_v0185(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0185(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0185(p) < _vnum_v0185(__file__)), key=_vnum_v0185)
PRIOR = _load_v0185(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


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


def _src(s: str) -> str:
    s = str(s or "").lower()
    return "FactSet(鉅亨)" if re.search(r"factset|cnyes", s) else ("Yahoo" if re.search(r"yahoo|yf|yfinance", s) else "")


def consensus_request() -> dict:
    rep = _rep()
    fin = rep / "basicinfo" / "BASIC_INFO_FINAL_latest.json"
    recs = (json.loads(fin.read_text(encoding="utf-8")).get("records", []) if fin.exists() else [])
    v = lambda r, k: ((r.get("fields") or {}).get(k) or {}).get("value")  # noqa: E731
    eps = defaultdict(dict)
    fp = rep / "findata" / "FINANCIAL_DATA_FINAL_latest.json"
    if fp.exists():
        for r in json.loads(fp.read_text(encoding="utf-8")).get("rows", []):
            if r.get("ACCOUNT") in ("diluted_eps", "eps") and "預估" in str(r.get("ADDSUB_TEST", "")) and r.get("DATE"):
                eps[r["FILENAME"]].setdefault(r["DATE"][:4], r["VALUE"])
    items = [{"code": str(v(r, "TICKER") or ""), "yf": v(r, "YF_TICKER"), "bbg": v(r, "BBG_TICKER"), "name": v(r, "NAME"), "broker": v(r, "BROKER"), "report_date": v(r, "REPORT_DATE"),
              "file": v(r, "FILENAME"), "rating": v(r, "RATING"), "tp": v(r, "TP_ORIGINAL"), "eps": eps.get(v(r, "FILENAME"), {})} for r in recs if v(r, "TICKER")]
    codes = sorted({x["code"] for x in items if re.fullmatch(r"\d{4,6}[A-Z]?", x["code"])})
    body = {"from": "VRN_SystemManager", "to": "VDF_SystemManager", "ts": datetime.datetime.now().isoformat(timespec="seconds"), "purpose": "共識目標價 / EPS / 評等 / 分析師人數 → VRN 合理性比對",
            "want": {"FactSet(鉅亨)": ["target_low", "target_mean", "target_median", "target_high", "target_analyst_count", "eps 各年", "rating"],
                     "Yahoo(.info)": ["targetLowPrice", "targetMeanPrice", "targetMedianPrice", "targetHighPrice", "recommendationKey", "recommendationMean", "numberOfAnalystOpinions", "earnings_estimate"]},
            "codes": codes, "fusion_cli": "--codes " + ",".join(codes), "items": items}
    od = rep / "contract"
    od.mkdir(parents=True, exist_ok=True)
    (od / "VRN_CONSENSUS_REQUEST_latest.json").write_text(json.dumps(body, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return body


def read_consensus(root: Path = None) -> dict:
    """唯讀 VDF 共識:{代號: {來源: {指標: 值, "eps": {年: 值}}}};長表(code / source / metric / value [/ period])與寬表(target_mean … · 前綴 cnyes_ / yf_)都認。"""
    root = root or (_resolve("_vdb") or (lambda: Path("")))()
    out = defaultdict(lambda: defaultdict(lambda: {"eps": {}}))
    files = sorted(p for p in Path(root).rglob("*.parquet") if re.search(r"consensus", p.name, re.I)) if root and Path(root).is_dir() else []
    try:
        import duckdb  # noqa: WPS433
        con = duckdb.connect()
    except Exception:  # noqa: BLE001
        return {}
    for p in files:
        try:
            cur = con.execute("select * from read_parquet('%s')" % str(p).replace("'", "''"))
            cols = [d[0] for d in cur.description]
            rows = cur.fetchall()
        except Exception:  # noqa: BLE001
            continue
        lc = {c.lower(): c for c in cols}
        code_c = next((lc[k] for k in ("code", "stock_id", "symbol", "ticker", "yfinance_ticker") if k in lc), None)
        if not code_c:
            continue
        met_c = next((lc[k] for k in ("metric", "item", "field", "key") if k in lc), None)
        val_c = next((lc[k] for k in ("value", "val", "num_value", "value_num") if k in lc), None)
        src_c = next((lc[k] for k in ("source", "provider", "origin", "data_source") if k in lc), None)
        per_c = next((lc[k] for k in ("period", "year", "fiscal_year", "fy") if k in lc), None)
        for r in rows:
            d = dict(zip(cols, r))
            code = re.sub(r"\.TWO?$", "", str(d.get(code_c) or "").strip())
            if not code:
                continue
            if met_c and val_c:
                m, val = str(d.get(met_c) or "").lower(), d.get(val_c)
                s = _src(d.get(src_c)) or _src(m) or "FactSet(鉅亨)"
                m2 = re.sub(r"^(cnyes_|factset_|yf_|yfinance_)", "", m)
                if m2.startswith("eps"):
                    yr = re.search(r"(20\d{2})", str(d.get(per_c) or m2))
                    if yr:
                        try:
                            out[code][s]["eps"][yr.group(1)] = float(val)
                        except (TypeError, ValueError):
                            pass
                elif m2 in METRICS:
                    out[code][s][m2] = val
            else:
                for c in cols:
                    m = c.lower()
                    s = _src(m) or _src(d.get(src_c)) or "FactSet(鉅亨)"
                    m2 = re.sub(r"^(cnyes_|factset_|yf_|yfinance_)", "", m)
                    m2 = {"targetlowprice": "target_low", "targetmeanprice": "target_mean", "targetmedianprice": "target_median", "targethighprice": "target_high",
                          "numberofanalystopinions": "analyst_count", "recommendationkey": "recommendation_key", "recommendationmean": "recommendation_mean"}.get(m2.replace("_", ""), m2)
                    if m2 in METRICS and d.get(c) is not None:
                        out[code][s][m2] = d[c]
                    ey = re.fullmatch(r"eps_?(20\d{2})", m2)
                    if ey and d.get(c) is not None:
                        out[code][s]["eps"][ey.group(1)] = d[c]
    return {k: {s: dict(v2) for s, v2 in v.items()} for k, v in out.items()}


def judge(item: dict, cons: dict) -> dict:
    tp, res = item.get("tp"), []
    for s, m in (cons or {}).items():
        try:
            lo, md, hi = (float(m[k]) if m.get(k) is not None else None for k in ("target_low", "target_median", "target_high"))
            mn = float(m["target_mean"]) if m.get("target_mean") is not None else None
        except (TypeError, ValueError):
            continue
        md = md if md is not None else mn
        n = m.get("target_analyst_count") or m.get("analyst_count")
        if not isinstance(tp, (int, float)) or None in (lo, hi):
            res.append({"source": s, "lamp": "GRAY", "detail": "缺券商目標價或共識 low / high"})
            continue
        dev = (tp / md - 1) * 100 if md else None
        pos = "低於共識最低" if tp < lo else ("高於共識最高" if tp > hi else "在共識區間內")
        lamp = "RED" if tp < lo or tp > hi else ("YELLOW" if dev is not None and abs(dev) > 15 else "GREEN")
        ed = []
        for y, e in sorted((item.get("eps") or {}).items()):
            ce = (m.get("eps") or {}).get(y)
            if isinstance(e, (int, float)) and isinstance(ce, (int, float)) and ce:
                d = (e / ce - 1) * 100
                ed.append("%s EPS %s vs 共識 %s(%+.1f%%)" % (y, e, ce, d))
                if abs(d) > 10 and lamp == "GREEN":
                    lamp = "YELLOW"
        res.append({"source": s, "lamp": lamp, "low": lo, "median": md, "mean": mn, "high": hi, "count": n, "rating": m.get("recommendation_key") or m.get("rating"),
                    "detail": "目標價 %s %s(%s~%s · 中位數 %s%s · %s 位分析師)%s" % (tp, pos, lo, hi, md, "" if dev is None else " · 偏離 %+.1f%%" % dev, n if n is not None else "—", (" · " + " · ".join(ed)) if ed else "")})
    if not res:
        res.append({"source": "—", "lamp": "GRAY", "detail": "VDF 還沒有這檔共識(等 VDF 接上共識動詞)"})
    return {"lamp": max((x["lamp"] for x in res), key=lambda l: {"RED": 3, "YELLOW": 2, "GREEN": 1, "GRAY": 0}[l]), "by_source": res}


def consensus_run(root: Path = None) -> dict:
    req = consensus_request()
    cons = read_consensus(root)
    out = [dict(it, **judge(it, cons.get(it["code"]))) for it in req["items"]]
    od = _rep() / "consensus"
    od.mkdir(parents=True, exist_ok=True)
    (od / "CONSENSUS_CHECK_latest.json").write_text(json.dumps({"rule": "目標價超出共識 low~high → 紅 · 偏離中位數 >15% → 黃 · EPS 差 >10% → 黃 · 沒有共識 → 灰", "rows": out},
                                                               ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    with (od / "CONSENSUS_CHECK_latest.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["file", "code", "broker", "report_date", "tp", "lamp", "source", "low", "median", "mean", "high", "analyst_count", "consensus_rating", "detail"])
        for x in out:
            for s in x["by_source"]:
                w.writerow([x["file"], x["code"], x["broker"], x["report_date"], x["tp"], s["lamp"], s["source"], s.get("low"), s.get("median"), s.get("mean"), s.get("high"), s.get("count"), s.get("rating"), s["detail"]])
    page, L = _resolve("_page"), _resolve("_L") or {}
    if page:
        (od / "CONSENSUS_CHECK_latest.html").write_text(page("共識合理性 · 券商目標價 / EPS vs FactSet(鉅亨)與 Yahoo 共識(VDF 資料庫 · 唯讀)", "%d 份 · 請求清單 %s" % (len(out), req["fusion_cli"][:120]),
                                                             ["檔名", "代號", "券商", "目標價", "來源", "共識 low~high", "中位數", "人數", "評等", "說明"],
                                                             [(s["lamp"], [html.escape(str(x["file"]))[:40], x["code"], html.escape(str(x["broker"])), x["tp"], s["source"], "%s~%s" % (s.get("low", "—"), s.get("high", "—")),
                                                               s.get("median", "—"), s.get("count", "—"), html.escape(str(s.get("rating") or "—")), html.escape(s["detail"])]) for x in out for s in x["by_source"]]), encoding="utf-8")
    return {"n": len(out), "codes": len(req["codes"]), "cli": req["fusion_cli"], "have": len(cons), "lamps": dict(Counter(x["lamp"] for x in out)),
            "reds": [x for x in out if x["lamp"] == "RED"][:4], "html": str(od / "CONSENSUS_CHECK_latest.html")}


def _lines_v185(o: dict) -> list:
    L = ["[計] 共識合理性 · 請求清單 %d 檔(VIA_Reports/vrn/contract/VRN_CONSENSUS_REQUEST_latest.json · VDF 讀)· VDF 已有共識 %d 檔 · %d 份報告:綠 %d 黃 %d 紅 %d 灰 %d" % (
        o["codes"], o["have"], o["n"], o["lamps"].get("GREEN", 0), o["lamps"].get("YELLOW", 0), o["lamps"].get("RED", 0), o["lamps"].get("GRAY", 0))]
    for x in o["reds"]:
        s = next((s for s in x["by_source"] if s["lamp"] == "RED"), x["by_source"][0])
        L.append("[計] 共識外 · %s · %s · %s" % (str(x["file"])[:28], s["source"], s["detail"][:100]))
    if not o["have"]:
        L.append("[計] VDF 還沒有共識資料 → VDF SystemManager 尚無共識動詞(融合引擎在 VDF references 收容區)· 融合引擎參數 %s" % o["cli"][:120])
    return L


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()
    if args[:1] == ["consensus"] or (args[:1] == ["auto"] and "--resume" not in args):
        rc = PRIOR.main(args) if args[:1] != ["consensus"] else 0
        o = consensus_run()
        L = _lines_v185(o)
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
                    print("[計] AI 包(含共識合理性)· %s" % ac(pk, nxt[0].replace("NEXT: ", ""))[1])
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
    td = Path(tempfile.mkdtemp(prefix="vrn185-"))
    saved = os.environ.get("VIA_VRN_HEALTH_OUT")
    try:
        import duckdb
        os.environ["VIA_VRN_HEALTH_OUT"] = str(td / "rep")
        (td / "rep" / "basicinfo").mkdir(parents=True)
        (td / "rep" / "findata").mkdir(parents=True)
        F = lambda v: {"value": v, "status": "GREEN"}  # noqa: E731
        recs = [{"fields": {"TICKER": F(c), "YF_TICKER": F(c + ".TW"), "BBG_TICKER": F(c + " TT"), "NAME": F(n), "BROKER": F("MS"), "REPORT_DATE": F("2025-12-01"), "FILENAME": F("MS-%s.pdf" % c),
                            "RATING": F("Overweight"), "TP_ORIGINAL": F(tp)}} for c, n, tp in (("2308", "台達電", 1288.0), ("3661", "世芯-KY", 6000.0), ("2330", "台積電", 1500.0), ("9999", "無共識", 50.0))]
        (td / "rep" / "basicinfo" / "BASIC_INFO_FINAL_latest.json").write_text(json.dumps({"records": recs}, ensure_ascii=False), encoding="utf-8")
        (td / "rep" / "findata" / "FINANCIAL_DATA_FINAL_latest.json").write_text(json.dumps({"rows": [{"FILENAME": "MS-2330.pdf", "ACCOUNT": "diluted_eps", "ADDSUB_TEST": "預估·未驗",
                                                                                                    "DATE": "2026-12-31", "VALUE": 80.0}]}), encoding="utf-8")
        vdb = td / "vdb"
        vdb.mkdir()
        con = duckdb.connect()
        con.execute("""create table l as select * from (values ('2308','cnyes_factset','target_low',1100.0,null), ('2308','cnyes_factset','target_median',1250.0,null),
                       ('2308','cnyes_factset','target_high',1400.0,null), ('2308','cnyes_factset','target_analyst_count',24.0,null),
                       ('3661','cnyes_factset','target_low',3000.0,null), ('3661','cnyes_factset','target_median',4200.0,null), ('3661','cnyes_factset','target_high',5200.0,null),
                       ('2330','cnyes_factset','target_low',1200.0,null), ('2330','cnyes_factset','target_median',1450.0,null), ('2330','cnyes_factset','target_high',1700.0,null),
                       ('2330','cnyes_factset','eps',68.0,'2026')) t(code, source, metric, value, period)""")
        con.execute("copy l to '%s' (format parquet)" % (vdb / "consensus_long_current.parquet"))
        con.execute("""create table w as select * from (values ('2308.TW', 1150.0, 1260.0, 1255.0, 1380.0, 'buy', 30)) t(yfinance_ticker, "yf_targetLowPrice", "yf_targetMeanPrice",
                       "yf_targetMedianPrice", "yf_targetHighPrice", "yf_recommendationKey", "yf_numberOfAnalystOpinions")""")
        con.execute("copy w to '%s' (format parquet)" % (vdb / "yf_consensus_raw.parquet"))
        cs = read_consensus(vdb)
        chk("① 唯讀 VDF 共識:長表(FactSet 鉅亨)+ 寬表(Yahoo · targetMeanPrice 等)都認 → 2308 兩個來源 · 2330 共識 EPS 2026 = 68",
            set(cs.get("2308", {})) == {"FactSet(鉅亨)", "Yahoo"} and cs["2308"]["Yahoo"]["target_high"] == 1380.0 and cs["2330"]["FactSet(鉅亨)"]["eps"].get("2026") == 68.0)
        o = consensus_run(vdb)
        rq = json.loads((td / "rep" / "contract" / "VRN_CONSENSUS_REQUEST_latest.json").read_text(encoding="utf-8"))
        chk("② 請求清單寫 VRN 自己的夾(VDF 讀)· 4 檔 · 附融合引擎參數 %s" % rq["fusion_cli"], rq["codes"] == ["2308", "2330", "3661", "9999"] and rq["fusion_cli"] == "--codes 2308,2330,3661,9999"
            and rq["to"] == "VDF_SystemManager")
        rows = {x["code"]: x for x in json.loads((td / "rep" / "consensus" / "CONSENSUS_CHECK_latest.json").read_text(encoding="utf-8"))["rows"]}
        chk("③ 合理性:2308 目標價 1288 在共識 1100~1400 · 偏離中位數 +3% → 綠(兩來源)· 3661 6000 > 共識最高 5200 → 紅 · 2330 1500 在區間但 EPS 80 vs 共識 68(+17.6%)→ 黃 · 9999 沒共識 → 灰",
            rows["2308"]["lamp"] == "GREEN" and len(rows["2308"]["by_source"]) == 2 and rows["3661"]["lamp"] == "RED" and rows["2330"]["lamp"] == "YELLOW" and "+17.6%" in rows["2330"]["by_source"][0]["detail"]
            and rows["9999"]["lamp"] == "GRAY")
        chk("④ 不寫 VDF 的檔(只讀 vdf 資料庫)· 輸出都在 VRN 自己的夾", sorted(x.name for x in vdb.iterdir()) == ["consensus_long_current.parquet", "yf_consensus_raw.parquet"])
    finally:
        if saved is None:
            os.environ.pop("VIA_VRN_HEALTH_OUT", None)
        else:
            os.environ["VIA_VRN_HEALTH_OUT"] = saved
        shutil.rmtree(td, ignore_errors=True)
    me = Path(__file__).read_text(encoding="utf-8")
    chk("⑤ 最新有版號加速器橋 [VIA:ACCEL-BRIDGE:v0111] · 自帶多程序墊片", "[VIA:ACCEL-BRIDGE:v0111]" in me and _job_entry.__module__ in ("__main__", __name__))
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("⑥ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    print("[計] VRN_SystemManager_v0185 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
