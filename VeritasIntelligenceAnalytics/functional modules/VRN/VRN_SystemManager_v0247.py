#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN-2 SystemManager v0247 — 薄尾(前版 = v0246)。資料處理與計算規範 V2(操作員 2026-10-27)。

① 市場填值改用最新版 VRN2_MarketFetch(v0246 寫死 v0100)· 百分比一律純小數:UPSIDE_ADJ(= TP(ADJ)/最新還原收盤 - 1)· ROE_AVG_EQUITY · PER_DILUTED_ADJ
② 歷史真實數據蓋過預估:年度數據冊逐列對 VDF 年度實際(MOPS)· 銜接處「一期重複核對」= 減法(差額)+ 除法(比率 · 自動辨單位 元 / 千元 / 百萬)·
   核對過的代號 → 預估列(F / E)同年有實際時 VALUE_FINAL = 實際(原 VALUE 不刪 · VALUE_SOURCE 記來源)· 核對不過 → 不蓋 · STATUS 寫原因 → VRN2_Reconcile_latest.json
③ 評價 / 收盤 / 目標價 / 報告前一日一律調整後(TARGET_PRICE(ADJ) · ADJ_CLOSE · ADJ_CLOSE_BEFORE_REPORT)· 摘要第一點上漲空間用調整後重算(純小數)
④ PER 嚴格用稀釋 EPS · ROE 分母 = 前期與當期權益平均 · DPS 已宣告未發放遞延往後一年(VDF v036 無股利資料集 → STATUS 註記)
⑤ STATUS 移到每本冊最末欄(DPS 最近發放日 · 特殊會計項目 · 配息異常 · 無法驗證的除外項目)
不改 v0246 / 另一線任何函式。
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
TAG = "v0247"
DISPLAY_NAME = "VRN-2 SystemManager"
PRIOR_NAME = "VRN_SystemManager_v0246.py"
PRIOR_PATH = HERE / PRIOR_NAME
if not PRIOR_PATH.exists():
    raise FileNotFoundError("前版 %s 不在 · v0247 不接" % PRIOR_NAME)
_spec = importlib.util.spec_from_file_location("vrn_manager_prior_for_v0247", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
for _name, _value in vars(PRIOR).items():
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = _value


def _rebind(fn):
    return types.FunctionType(fn.__code__, globals(), fn.__name__, fn.__defaults__, fn.__closure__)


_STDI = {"revenue": ("營業收入", "營收", "Revenue", "Net sales", "Sales", "Total revenue"), "operating_income": ("營業利益", "營業淨利", "Operating income", "Operating profit", "EBIT"),
         "net_income": ("稅後淨利", "本期淨利", "稅後純益", "淨利", "Net income", "Net profit"), "eps_diluted": ("稀釋每股盈餘", "稀釋EPS", "Diluted EPS"), "eps_basic": ("每股盈餘", "EPS", "基本每股盈餘")}


def _std_item(item: str) -> str:
    a = str(item or "").replace(" ", "").lower()
    for k, names in _STDI.items():
        if any(n.replace(" ", "").lower() in a for n in names):
            return k
    return ""


def _status_last(row: dict) -> dict:
    """STATUS 移到最末欄(⑤)。"""
    st = row.pop("_STATUS", None)
    if isinstance(st, dict):
        row["STATUS"] = " · ".join("%s:%s" % (k, v) for k, v in st.items()) if st else ""
    elif st is not None:
        row["STATUS"] = str(st)
    else:
        row["STATUS"] = row.pop("STATUS", "")
    return row


def _market_fill(v2: Path, basic_path: Path) -> dict:
    cands = sorted(HERE.glob("VRN2_MarketFetch_v[0-9][0-9][0-9][0-9].py"))
    eng = cands[-1] if cands else None
    mk = Path(v2) / "market"
    if not eng:
        return {}
    try:
        r = subprocess.run([sys.executable, "-W", "ignore", str(eng), "--fill", "--basic", str(basic_path), "--out", str(mk)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600, cwd=str(HERE))
        line = next((l for l in (r.stdout + r.stderr).splitlines() if "市場填值" in l), "")
        if line:
            print("  " + line.strip() + " · " + eng.name, flush=True)
    except Exception as exc:  # noqa: BLE001
        print("  [計] 市場填值未完成 %s" % type(exc).__name__, flush=True)
    try:
        return json.loads((mk / "VRN2_Market_latest.json").read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def _apply_v2(basic: list, summ: list, market: dict) -> tuple:
    pf = market.get("per_file") or {}
    nb = ns = 0
    for row in basic:
        rec = pf.get(row.get("FILENAME")) or {}
        st = row.get("_STATUS") if isinstance(row.get("_STATUS"), dict) else {}
        if rec:
            row["UPSIDE_ADJ"] = rec.get("upside_adj") if rec.get("upside_adj") is not None else ""
            rt = rec.get("ratios") or {}
            roe = rt.get("roe_avg_equity") or {}
            row["ROE_AVG_EQUITY"] = roe[max(roe)] if roe else ""
            row["ROE_YEAR"] = max(roe) if roe else ""
            row["PER_DILUTED_ADJ"] = rt.get("per_diluted") if rt.get("per_diluted") is not None else ""
            row["PER_YEAR"] = rt.get("per_year") or ""
            for n in rt.get("notes") or []:
                st.setdefault("RATIOS", []).append(n) if isinstance(st.get("RATIOS"), list) else st.__setitem__("RATIOS", [n])
            if isinstance(st.get("RATIOS"), list):
                st["RATIOS"] = " / ".join(st["RATIOS"])
            nb += 1
        row["_STATUS"] = st
        _status_last(row)
    for row in summ:
        rec = pf.get(row.get("FILENAME")) or {}
        if rec.get("upside_adj") is not None:
            row["UPSIDE_ADJ"] = rec["upside_adj"]
            if "上漲空間(調整後)" in (row.get("POINT_1") or "") and "純小數" not in row["POINT_1"]:
                row["POINT_1"] = re.sub(r"上漲空間\(調整後\)[-\d.]+%", "上漲空間(調整後)%.9g(純小數 · %.1f%%)" % (rec["upside_adj"], rec["upside_adj"] * 100), row["POINT_1"])
            ns += 1
        _status_last(row)
    return nb, ns


def _reconcile(fin: list, market: dict) -> tuple:
    """② 歷史真實蓋過預估 · 一期重複核對(減法 + 除法 · 自動辨單位)。回 (改了幾列, 核對紀錄)."""
    pf = market.get("per_file") or {}
    actual = {}                                                              # (FILENAME, year, std) → (value_k, unit)
    for f, rec in pf.items():
        for x in rec.get("financial_annual") or []:
            if x.get("basis") == "ANNUAL" and x.get("value") is not None:
                actual[(f, int(x["year"]), x["std"])] = (float(x["value"]), x.get("unit") or "")
    if not actual:
        return 0, {"files": {}, "note": "VDF 年度實際未就緒"}
    checks, trusted, changed = {}, {}, 0
    for row in fin:                                                          # 第一遍:實際列核對 → 決定每檔的單位倍率是否可信
        f, std = row.get("FILENAME"), _std_item(row.get("ITEM"))
        y = str(row.get("PERIOD_STD") or "")[:4]
        if not (f and std and y.isdigit()):
            continue
        a = actual.get((f, int(y), std)) or (actual.get((f, int(y), "eps_basic")) if std == "eps_diluted" else None)
        v = row.get("VALUE_NUM")
        if a is None or v in (None, "", 0):
            continue
        av, unit = a
        if bool(re.search(r"[FEfe]\)?$|預估|\(F\)|\(E\)", str(row.get("PERIOD") or ""))) or str(row.get("PERIOD_KIND") or "").upper().startswith("F"):
            continue                                                           # 預估列不在第一遍核對 · 交第二遍決定是否被實際蓋過
        if std.startswith("eps"):
            scale = 1.0
        else:
            cands = {"TWD_THOUSAND": {"千元": 1.0, "百萬": 0.001, "元": 1000.0, "十億": 0.000001}}.get(unit, {"同單位": 1.0})
            scale, best = None, None
            for name, k in cands.items():
                r_ = (av * k) / float(v) if float(v) else None
                if r_ and 0.97 <= r_ <= 1.03 and (best is None or abs(r_ - 1) < abs(best - 1)):
                    scale, best = k, r_
        rec_ = checks.setdefault(f, {"verified": 0, "failed": 0, "overridden": 0, "scale": None})
        if std.startswith("eps") or scale is not None:
            k = 1.0 if std.startswith("eps") else scale
            r_ = (av * k) / float(v)
            diff = round(av * k - float(v), 6)
            row["RECON_RATIO"] = round(r_, 9); row["RECON_DIFF"] = diff; row["VALUE_ACTUAL"] = round(av * k, 6); row["VALUE_ACTUAL_SRC"] = "VDF/MOPS 年度(ANNUAL)"
            if 0.97 <= r_ <= 1.03:
                rec_["verified"] += 1; trusted[f] = k if not std.startswith("eps") else trusted.get(f)
                row["VALUE_FINAL"] = row.get("VALUE_FINAL") or float(v)
                row["VALUE_SOURCE"] = "報告值 · 與實際核對通過(除法 %.4f · 減法 %s)" % (r_, diff)
            else:
                rec_["failed"] += 1
                row["VALUE_FINAL"] = float(v); row["VALUE_SOURCE"] = "報告值 · 與實際核對不過(除法 %.4f)· 不蓋" % r_
    for row in fin:                                                          # 第二遍:預估列同年有實際且該檔單位可信 → 實際蓋過預估
        f, std = row.get("FILENAME"), _std_item(row.get("ITEM"))
        y = str(row.get("PERIOD_STD") or "")[:4]
        if not (f and std and y.isdigit()) or row.get("VALUE_FINAL") is not None:
            continue
        a = actual.get((f, int(y), std))
        is_forecast = bool(re.search(r"[FEfe]\)?$|預估|\(F\)|\(E\)", str(row.get("PERIOD") or ""))) or str(row.get("PERIOD_KIND") or "").upper().startswith("F")
        if a is None or not is_forecast:
            continue
        k = 1.0 if std.startswith("eps") else trusted.get(f)
        if k is None:
            row["VALUE_SOURCE"] = "預估 · 同年有實際但本檔單位未核對(無通過的一期重複核對)· 不蓋"
            continue
        row["VALUE_ACTUAL"] = round(a[0] * k, 6); row["VALUE_ACTUAL_SRC"] = "VDF/MOPS 年度(ANNUAL)"
        row["VALUE_FINAL"] = row["VALUE_ACTUAL"]; row["VALUE_SOURCE"] = "實際蓋過預估(VDF/MOPS · 單位倍率 %g · 原預估 %s 保留於 VALUE)" % (k, row.get("VALUE_NUM"))
        checks.setdefault(f, {"verified": 0, "failed": 0, "overridden": 0, "scale": None})["overridden"] += 1; changed += 1
    for f in checks:
        checks[f]["scale"] = trusted.get(f)
    for row in fin:
        row.setdefault("VALUE_FINAL", row.get("VALUE_NUM")); row.setdefault("VALUE_SOURCE", "報告值")
        _status_last(row)
    return changed, {"files": checks, "rule": "一期重複核對:減法 = 實際 - 報告 · 除法 = 實際 / 報告 ∈ [0.97, 1.03] 通過 · 通過才允許同檔預估列被實際蓋過 · 原值不刪"}


def _out_books(res, acc, st, v2):
    basic, fin, summ, gaps, made = PRIOR._out_books(res, acc, st, v2)
    try:
        od = Path(v2) / "output"
        market = _market_fill(v2, od / "VRN2_BasicInfo_latest.json")
        if market:
            nb, ns = _apply_v2(basic, summ, market)
            chg, rep = _reconcile(fin, market)
            (Path(v2) / "output" / "VRN2_Reconcile_latest.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
            _rewrite_book(od, "BasicInfo", basic); _rewrite_book(od, "Summary", summ); _rewrite_book(od, "FinancialData", fin)
            nf = sum(1 for f in rep.get("files", {}).values())
            print("  [計] v0247 V2 規範:基本資料 %d 份(UPSIDE_ADJ / ROE 平均權益 / PER 稀釋 · 純小數 · STATUS 末欄)· 摘要 %d · 年度數據核對 %d 檔(通過 %d · 不過 %d)· 實際蓋過預估 %d 列 → VRN2_Reconcile_latest.json" % (
                nb, ns, nf, sum(v["verified"] for v in rep.get("files", {}).values()), sum(v["failed"] for v in rep.get("files", {}).values()), chg), flush=True)
        else:
            for b_ in basic:
                _status_last(b_)
            _rewrite_book(od, "BasicInfo", basic)
            print("  [計] v0247 市場資料未就緒(⑥e 失敗)· 僅 STATUS 移末欄", flush=True)
    except Exception as exc:  # noqa: BLE001
        print("  [計] v0247 V2 規範未完成 %s %s" % (type(exc).__name__, str(exc)[:80]), flush=True)
    return basic, fin, summ, gaps, made


def completion(*args, **kwargs):
    result = PRIOR.completion(*args, **kwargs)
    try:
        result["manager"] = "%s %s" % (DISPLAY_NAME, TAG)
    except Exception:  # noqa: BLE001
        pass
    return result


_MY_SIG = hashlib.sha1("|".join(inspect.getsource(f) for f in (_apply_v2, _reconcile)).encode("utf-8")).hexdigest()[:12]
for _n in ("_base_acceptance", "_acc_parallel", "_acc_shard_main", "_acc_one", "_acc_one_core", "_acc_basic", "acceptance", "_acc_sig", "_native_vrn2", "vrn2", "_idem_check", "main", "_success_register", "_ui_panel_html", "_out_html"):
    globals()[_n] = _rebind(getattr(PRIOR, _n))


def selftest() -> int:
    ok = [0, 0]
    def chk(name, cond):
        ok[0 if cond else 1] += 1
        print("  [%s] %s" % ("OK" if cond else "FAIL", name))
    market = {"per_file": {"x.pdf": {"upside_adj": 0.236747897, "ratios": {"roe_avg_equity": {"2024": 0.18, "2025": 0.2}, "per_diluted": 22.444444444, "per_year": 2025, "notes": ["DPS 遞延規則未套用:VDF v036 無股利資料集"]},
                                     "financial_annual": [{"year": 2024, "std": "revenue", "value": 2894308000.0, "unit": "TWD_THOUSAND", "basis": "ANNUAL"}, {"year": 2025, "std": "revenue", "value": 3500000000.0, "unit": "TWD_THOUSAND", "basis": "ANNUAL"}, {"year": 2025, "std": "eps_diluted", "value": 45.0, "unit": "TWD_PER_SHARE", "basis": "ANNUAL"}]}}}
    basic = [{"FILENAME": "x.pdf", "TICKER": "2330", "_STATUS": {"ADJ_CLOSE": "ok"}, "TITLE": "t"}]
    summ = [{"FILENAME": "x.pdf", "POINT_1": "維持買進 · 目標價(調整後)1176 · 最新還原收盤 1010(2026-05-20)· 上漲空間(調整後)16.4%", "_STATUS": {}}]
    nb, ns = _apply_v2(basic, summ, market)
    b = basic[0]
    chk("⓪ v0247 基本資料:UPSIDE_ADJ %s · ROE %s(%s)· PER %s · STATUS 末欄 %s" % (b["UPSIDE_ADJ"], b["ROE_AVG_EQUITY"], b["ROE_YEAR"], b["PER_DILUTED_ADJ"], list(b.keys())[-1]),
        b["UPSIDE_ADJ"] == 0.236747897 and b["ROE_AVG_EQUITY"] == 0.2 and b["PER_DILUTED_ADJ"] == 22.444444444 and list(b.keys())[-1] == "STATUS" and "DPS" in b["STATUS"])
    chk("⓪ v0247 摘要第一點純小數 %s" % summ[0]["POINT_1"][-40:], "0.236747897(純小數 · 23.7%)" in summ[0]["POINT_1"])
    fin = [{"FILENAME": "x.pdf", "ITEM": "營業收入淨額", "PERIOD": "2024A", "PERIOD_STD": "2024", "VALUE_NUM": 2894308.0, "_STATUS": {}},
           {"FILENAME": "x.pdf", "ITEM": "營業收入淨額", "PERIOD": "2025F", "PERIOD_STD": "2025", "VALUE_NUM": 3400000.0, "_STATUS": {}},
           {"FILENAME": "x.pdf", "ITEM": "稀釋每股盈餘", "PERIOD": "2025F", "PERIOD_STD": "2025", "VALUE_NUM": 44.0, "_STATUS": {}},
           {"FILENAME": "x.pdf", "ITEM": "營業收入淨額", "PERIOD": "2026F", "PERIOD_STD": "2026", "VALUE_NUM": 4000000.0, "_STATUS": {}}]
    chg, rep = _reconcile(fin, market)
    c = fin[0]["RECON_RATIO"] == 1.0 and "核對通過" in fin[0]["VALUE_SOURCE"] and fin[1]["VALUE_FINAL"] == 3500000.0 and "蓋過預估" in fin[1]["VALUE_SOURCE"] and fin[1]["VALUE_NUM"] == 3400000.0 and fin[2]["VALUE_FINAL"] == 45.0 and fin[3]["VALUE_FINAL"] == 4000000.0 and "報告值" in fin[3]["VALUE_SOURCE"] and list(fin[0].keys())[-1] == "STATUS"
    chk("⓪ v0247 一期重複核對:2024A 千元→百萬 除法 %s 通過 · 2025F 營收 %s → 實際 %s(原值保留)· 2025F 稀釋 EPS → 45 · 2026F 無實際不動 · 蓋 %d 列" % (fin[0]["RECON_RATIO"], fin[1]["VALUE_NUM"], fin[1]["VALUE_FINAL"], chg), c and chg == 2)
    chk("⓪ v0247 綁定:acceptance / 分片 全綁本版 %s · vrn2 內部 _out_books / completion 走本版 %s %s" % (all(f.__globals__ is globals() for f in (_base_acceptance, _acc_parallel, _acc_shard_main, _acc_one, _acc_one_core)), _native_vrn2.__globals__["_out_books"] is _out_books, _native_vrn2.__globals__["completion"] is completion),
        all(f.__globals__ is globals() for f in (_base_acceptance, _acc_parallel, _acc_shard_main, _acc_one, _acc_one_core)) and _native_vrn2.__globals__["_out_books"] is _out_books and _native_vrn2.__globals__["completion"] is completion)
    import os
    if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") != "1":
        print("          ── 前版鏈(v0246)自測 ──")
        rc = PRIOR.selftest()
        chk("③ 前版鏈 v0246 自測 rc %s" % rc, rc == 0)
    p, f = ok
    print("[計] VRN-2 SystemManager v0247(VRN_SystemManager_v0247.py)自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.exit(main(sys.argv[1:]))
