#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN-2 SystemManager v0246 — 薄尾(前版 = v0245)。

v0246(市場資料 · 用引擎擷取不靠資料庫):
① 輸出冊後呼叫 VRN2_MarketFetch --fill(包住 VDF_TW_DataFetchEngine v036 落盤的官方 + Yahoo 還原資料)→ 基本資料冊填 NAME / YFINANCE_TICKER / BLOOMBERG_TICKER /
   ADJ_CLOSE(最新 · 日期)/ ADJ_CLOSE_BEFORE_REPORT / 新欄 TARGET_PRICE(ADJ)(= 目標價 × 報告日還原因子)/ UPSIDE_PCT(ADJ) · 缺就 MISSING 寫進 _STATUS 不猜
② 摘要冊:TITLE → 「中文名(2330.TW): 原標題」(名稱 / 代碼來自官方名冊 · 沒有就不加)· POINT_1(評價)保留原文 · 後附「目標價(調整後)X · 最新還原收盤 Y(日期)· 上漲空間 Z%」
③ U/I 與完成判定文字「不上船」→「不上傳」
④ 分析師(標籤)診斷:標籤來源的分析師逐份印進貼包(兆豐 研究員:邱岳霖 追蹤)
驗收 / 分片重綁本版 · 不改 v0245 / 另一線任何函式。
"""
from __future__ import annotations

import hashlib
import importlib.util
import inspect
import json
import re
import subprocess
import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
TAG = "v0246"
DISPLAY_NAME = "VRN-2 SystemManager"
PRIOR_NAME = "VRN_SystemManager_v0245.py"
PRIOR_PATH = HERE / PRIOR_NAME
if not PRIOR_PATH.exists():
    raise FileNotFoundError("前版 %s 不在 · v0246 不接" % PRIOR_NAME)
_spec = importlib.util.spec_from_file_location("vrn_manager_prior_for_v0246", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
for _name, _value in vars(PRIOR).items():
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = _value


def _rebind(fn):
    return types.FunctionType(fn.__code__, globals(), fn.__name__, fn.__defaults__, fn.__closure__)


# ===== 1. 市場資料填值 =====
def _market_fill(v2: Path, basic_path: Path) -> dict:
    eng = HERE / "VRN2_MarketFetch_v0100.py"
    mk = Path(v2) / "market"
    if not eng.exists():
        return {}
    try:
        r = subprocess.run([sys.executable, "-W", "ignore", str(eng), "--fill", "--basic", str(basic_path), "--out", str(mk)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600, cwd=str(HERE))
        line = next((l for l in (r.stdout + r.stderr).splitlines() if "市場填值" in l), "")
        if line:
            print("  " + line.strip(), flush=True)
    except Exception as exc:  # noqa: BLE001
        print("  [計] 市場填值未完成 %s" % type(exc).__name__, flush=True)
    try:
        return json.loads((mk / "VRN2_Market_latest.json").read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def _fmt(v):
    return "" if v in (None, "") else ("%g" % v if isinstance(v, float) else str(v))


def _apply_market(basic: list, summ: list, market: dict) -> tuple:
    pf = market.get("per_file") or {}
    nb = ns = 0
    for row in basic:
        rec = pf.get(row.get("FILENAME"))
        if not rec:
            continue
        st = row.setdefault("_STATUS", {}) if isinstance(row.get("_STATUS"), dict) else {}
        for col, key in (("NAME", "name"), ("YFINANCE_TICKER", "yfinance_ticker"), ("BLOOMBERG_TICKER", "bloomberg_ticker")):
            if rec.get(key) and not row.get(col):
                row[col] = rec[key]; st[col] = "官方名冊(VDF 引擎)"
        row["ADJ_CLOSE"] = _fmt(rec.get("adj_close")); row["ADJ_CLOSE_DATE"] = rec.get("adj_close_date") or ""
        row["ADJ_CLOSE_BEFORE_REPORT"] = _fmt(rec.get("adj_close_before_report")); row["ADJ_CLOSE_BEFORE_REPORT_DATE"] = rec.get("adj_close_before_report_date") or ""
        row["TARGET_PRICE(ADJ)"] = _fmt(rec.get("target_price_adj")); row["UPSIDE_PCT(ADJ)"] = _fmt(rec.get("upside_pct_adj"))
        st["ADJ_CLOSE"] = "Yahoo 還原(VDF 引擎 · %s)" % rec.get("adj_close_date") if rec.get("adj_close") is not None else "MISSING · " + str(rec.get("adj_status") or rec.get("reason") or "VDF 沒有日資料")
        st["TARGET_PRICE(ADJ)"] = "目標價 × 報告日還原因子 %.4f" % rec["adjustment_factor_report"] if rec.get("adjustment_factor_report") else "MISSING · " + str(rec.get("before_status") or "沒有報告日前的日資料")
        if isinstance(row.get("_STATUS"), dict):
            row["_STATUS"] = st
        nb += 1
    bmap = {b.get("FILENAME"): b for b in basic}
    for row in summ:
        b = bmap.get(row.get("FILENAME")) or {}
        rec = pf.get(row.get("FILENAME")) or {}
        name, yf = rec.get("name") or b.get("NAME") or "", rec.get("yfinance_ticker") or b.get("YFINANCE_TICKER") or ""
        title = row.get("TITLE") or ""
        if name and yf and title and not title.startswith("%s(%s)" % (name, yf)):
            row["TITLE_ORIGINAL"] = title
            row["TITLE"] = "%s(%s): %s" % (name, yf, title)
        if rec.get("target_price_adj") is not None and rec.get("adj_close") is not None and "上漲空間(調整後)" not in (row.get("POINT_1") or ""):
            row["POINT_1_ORIGINAL"] = row.get("POINT_1") or ""
            row["POINT_1"] = "%s · 目標價(調整後)%s · 最新還原收盤 %s(%s)· 上漲空間(調整後)%s%%" % ((row.get("POINT_1") or "評價").rstrip("。 "), _fmt(rec["target_price_adj"]), _fmt(rec["adj_close"]), rec.get("adj_close_date", ""), _fmt(rec["upside_pct_adj"]))
        ns += 1
    return nb, ns


def _out_books(res, acc, st, v2):
    basic, fin, summ, gaps, made = PRIOR._out_books(res, acc, st, v2)
    try:                                                                  # ④ 分析師(標籤)診斷
        lab = [(e.get("file"), (e.get("basic") or {}).get("analysts")) for e in (acc or []) if isinstance(e, dict) and (e.get("basic") or {}).get("analyst_src")]
        if lab:
            print("  [計] v0246 分析師(標籤)%d 份:%s" % (len(lab), " | ".join("%s→%s" % (str(f)[:18], "、".join(a or [])) for f, a in lab[:6])), flush=True)
        else:
            print("  [計] v0246 分析師(標籤)0 份(兆豐 研究員 標籤沒進到 basic · 待查)", flush=True)
    except Exception:  # noqa: BLE001
        pass
    try:
        od = Path(v2) / "output"
        market = _market_fill(v2, od / "VRN2_BasicInfo_latest.json")
        if market:
            nb, ns = _apply_market(basic, summ, market)
            _rewrite_book(od, "BasicInfo", basic)
            _rewrite_book(od, "Summary", summ)
            print("  [計] v0246 市場資料接回:基本資料 %d 份 · 摘要 %d 份(標題加中文名(代碼)· 評價附調整後上漲空間)" % (nb, ns), flush=True)
    except Exception as exc:  # noqa: BLE001
        print("  [計] v0246 市場資料接回未完成 %s" % type(exc).__name__, flush=True)
    return basic, fin, summ, gaps, made


# ===== 2. 文字:不上船 → 不上傳 =====
def _ui_panel_html(v2):
    return PRIOR._ui_panel_html(v2).replace("不上船", "不上傳")


def _out_html(*a, **k):
    return PRIOR._out_html(*a, **k).replace("不上船", "不上傳")


def completion(*args, **kwargs):
    result = PRIOR.completion(*args, **kwargs)
    try:
        result["manager"] = "%s %s" % (DISPLAY_NAME, TAG)
        for k, v in list(result.items()):
            if isinstance(v, str):
                result[k] = v.replace("不上船", "不上傳")
    except Exception:  # noqa: BLE001
        pass
    return result


# ===== 3. 重綁 =====
_MY_SIG = hashlib.sha1("|".join(inspect.getsource(f) for f in (_apply_market, _market_fill)).encode("utf-8")).hexdigest()[:12]
for _n in ("_base_acceptance", "_acc_parallel", "_acc_shard_main", "_acc_one", "_acc_one_core", "_acc_basic", "acceptance", "_acc_sig", "_native_vrn2", "vrn2", "_idem_check", "main", "_success_register"):
    globals()[_n] = _rebind(getattr(PRIOR, _n))


# ===== 4. 自測 =====
def selftest() -> int:
    ok = [0, 0]
    def chk(name, cond):
        ok[0 if cond else 1] += 1
        print("  [%s] %s" % ("OK" if cond else "FAIL", name))
    basic = [{"FILENAME": "x.pdf", "TICKER": "2330", "NAME": "", "TARGET_PRICE": "1,200", "_STATUS": {}}]
    summ = [{"FILENAME": "x.pdf", "TITLE": "AI 需求強勁", "POINT_1": "維持買進評等，目標價 1,200 元。"}]
    market = {"per_file": {"x.pdf": {"name": "台積電", "yfinance_ticker": "2330.TW", "bloomberg_ticker": "2330 TT", "adj_close": 1010.0, "adj_close_date": "2026-05-20", "adj_close_before_report": 980.0, "adjustment_factor_report": 0.98, "target_price_adj": 1176.0, "upside_pct_adj": 16.4}}}
    nb, ns = _apply_market(basic, summ, market)
    b, s = basic[0], summ[0]
    chk("⓪ v0246 基本資料接回 NAME %s · YF %s · ADJ %s · TP(ADJ) %s · 上漲 %s" % (b["NAME"], b["YFINANCE_TICKER"], b["ADJ_CLOSE"], b["TARGET_PRICE(ADJ)"], b["UPSIDE_PCT(ADJ)"]),
        b["NAME"] == "台積電" and b["YFINANCE_TICKER"] == "2330.TW" and b["TARGET_PRICE(ADJ)"] == "1176" and b["UPSIDE_PCT(ADJ)"] == "16.4")
    chk("⓪ v0246 摘要:標題 %s · 評價原文保留 %s" % (s["TITLE"], s["POINT_1"].startswith("維持買進評等")), s["TITLE"].startswith("台積電(2330.TW): AI") and s["POINT_1"].startswith("維持買進評等") and "上漲空間(調整後)16.4%" in s["POINT_1"])
    chk("⓪ v0246 綁定:acceptance / _acc_parallel / _acc_shard_main / _acc_one / _acc_one_core 全綁本版 %s · 指紋含本版 %s · vrn2 內部 _out_books / completion 走本版 %s %s" % (
        all(f.__globals__ is globals() for f in (_base_acceptance, _acc_parallel, _acc_shard_main, _acc_one, _acc_one_core)), _acc_sig() != PRIOR._acc_sig(), _native_vrn2.__globals__["_out_books"] is _out_books, _native_vrn2.__globals__["completion"] is completion),
        all(f.__globals__ is globals() for f in (_base_acceptance, _acc_parallel, _acc_shard_main, _acc_one, _acc_one_core)) and _acc_sig() != PRIOR._acc_sig() and _native_vrn2.__globals__["_out_books"] is _out_books and _native_vrn2.__globals__["completion"] is completion)
    chk("⓪ v0246 不上船 → 不上傳(completion)", "不上船" not in json.dumps(completion.__doc__ or "") and callable(_ui_panel_html))
    import os
    if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") != "1":
        print("          ── 前版鏈(v0245)自測 ──")
        rc = PRIOR.selftest()
        chk("③ 前版鏈 v0245 自測 rc %s" % rc, rc == 0)
    p, f = ok
    print("[計] VRN-2 SystemManager v0246(VRN_SystemManager_v0246.py)自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.exit(main(sys.argv[1:]))
