#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_MDL009_TWStockList v0103 — 薄尾(v0100–v0102 一字不改):清單多留 T1 欄 · ISIN · 全部由官方 API 動態生成。

操作員 2026-11-10 令「補 MDL009 v0103 · 找生成引擎不要找清單,因為清單隨時在變」+ VDF 缺漏檢查(T1 stock_list)。
v0102 已抓的公司基本資料(TWSE t187ap03_L · TPEX mopsfin_t187ap03_O)本來就有下列欄,只是沒留;本版把它們留進同一列:
  listing_date(YYYY-MM-DD)· par_value(元)· shares_issued(股)· capital(元)· isin_code · isin_source
欄名用「候選名單」動態找(中文鍵 / 英文鍵都認),官方欄名改了也不必改程式;找不到就留空並在 V9 照實計數。
ISIN:先讀官方 isin.twse.com.tw(上市 strMode=2 · 上櫃 strMode=4,經鎖版網路工具 http_text;Big5 由網路工具解碼),
讀不到(例:雲端 IP 被擋)才用 ISIN 標準檢查碼演算(TW000 + 代碼 + 00 + Luhn),標 isin_source=computed;
官方值也驗檢查碼,不合就標 official_badcheck。不寫死任何股票清單:股票集合只來自當天的官方報價表。
V9(本版新增)= T1 欄覆蓋率:shares_issued 覆蓋 < 95% → YELLOW(不擋寫入;持股率引擎靠它當分母)。
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_MDL009_TWStockList"


def _vnum_v0103(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0103(p) < _vnum_v0103(__file__)), key=_vnum_v0103)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
P1 = PRIOR.PRIOR                                       # v0101(run_v0101 · collect_v0101 · verify_v0101 所在)
for _n, _v in vars(PRIOR).items():                     # 前版公開名稱全數轉接(TAILAPI)
    if not _n.startswith("__") and _n not in globals():
        globals()[_n] = _v

TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
ISIN_SRC_V0103 = {"TWSE": "https://isin.twse.com.tw/isin/C_public.jsp?strMode=2",
                  "TPEX": "https://isin.twse.com.tw/isin/C_public.jsp?strMode=4"}
FIELD_CANDIDATES_V0103 = {
    "listing_date": ("上市日期", "上櫃日期", "DateOfListing", "ListingDate"),
    "par_value": ("普通股每股面額", "ParValueOfCommonStock", "ParValue"),
    "shares_issued": ("已發行普通股數或TDR原股發行股數", "IssueShares", "NumberOfSharesIssued",
                      "Issued.Shares", "已發行普通股數"),
    "capital": ("實收資本額", "Paidin.Capital.NTDollars", "PaidInCapital", "Paid-inCapital"),
}
T1_FIELDS_V0103 = ("listing_date", "par_value", "shares_issued", "capital", "isin_code", "isin_source")
SHARES_MIN_COVER_V0103 = 0.95
_CACHE_V0103: dict = {}
_CACHE_ON_V0103 = [False]                              # 只在本版 collect 期間開;其他呼叫者(MDL010 / MDL008)照原樣一請求一抓


def _forward_via_net_v0103():
    return globals()["_via_net"]()


_ORIG_VIA_NET_PRIOR_V0103_SAVE = PRIOR._via_net         # v0102 自己的轉接(前版自測要它)
_ORIG_FETCH_V0103 = P1.fetch_json_v0100


def _cached_fetch_v0103(url: str):
    """同一輪同一 URL 只抓一次:collect 抓過的基本資料,本版直接重用(不多打官方)。快取只在本版 collect 期間生效。"""
    if not _CACHE_ON_V0103[0]:
        return _ORIG_FETCH_V0103(url)
    if url not in _CACHE_V0103:
        _CACHE_V0103[url] = _ORIG_FETCH_V0103(url)
    return _CACHE_V0103[url]


# ─────────────────────────────── 欄位解析(動態候選,不寫死) ───────────────────────────────
def pick_v0103(row: dict, field: str) -> str:
    for k in FIELD_CANDIDATES_V0103[field]:
        v = row.get(k)
        if v not in (None, ""):
            return str(v).strip()
    low = {str(k).lower().replace(" ", "").replace(".", ""): v for k, v in row.items()}
    for k in FIELD_CANDIDATES_V0103[field]:
        v = low.get(k.lower().replace(" ", "").replace(".", ""))
        if v not in (None, ""):
            return str(v).strip()
    return ""


def norm_date_v0103(s: str) -> str:
    d = re.sub(r"\D", "", s or "")
    if len(d) == 8:
        return f"{d[:4]}-{d[4:6]}-{d[6:]}"
    if len(d) == 7:                                    # 民國 YYYMMDD
        return f"{int(d[:3]) + 1911:04d}-{d[3:5]}-{d[5:]}"
    return ""


def norm_num_v0103(s: str) -> str:
    m = re.search(r"-?\d[\d,]*(?:\.\d+)?", s or "")
    if not m:
        return ""
    v = m.group(0).replace(",", "")
    return v.rstrip("0").rstrip(".") if "." in v else v


def isin_check_v0103(body: str) -> str:
    digits = "".join(str(int(c, 36)) for c in body)
    s = 0
    for i, ch in enumerate(reversed(digits)):
        d = int(ch)
        if i % 2 == 0:
            d *= 2
            d = d - 9 if d > 9 else d
        s += d
    return str((10 - s % 10) % 10)


def isin_computed_v0103(code: str) -> str:
    body = "TW000" + code + "00"
    return body + isin_check_v0103(body) if re.fullmatch(r"\d{4}", code or "") else ""


def isin_valid_v0103(isin: str) -> bool:
    return bool(re.fullmatch(r"[A-Z]{2}[A-Z0-9]{9}\d", isin or "")) and isin_check_v0103(isin[:-1]) == isin[-1]


def fetch_isin_v0103(market: str) -> tuple:
    """官方 ISIN 頁 → {代碼: ISIN};回 (state, map)。網路工具缺 / 閘關 / 被擋都誠實回狀態,不假裝。"""
    nt = globals()["_via_net"]()
    if nt is None or not hasattr(nt, "http_text"):
        return "ABSENT", {}
    try:
        r = nt.http_text(ISIN_SRC_V0103[market], timeout=60) or {}
    except Exception as exc:  # noqa: BLE001
        return "FAIL:" + type(exc).__name__, {}
    if str(r.get("state") or "") != "OK":
        return ("GATED" if r.get("state") == "DENY" else "FAIL:" + str(r.get("note") or r.get("state"))[:60]), {}
    text = str(r.get("data") or "")
    if "SECURITY REASONS" in text.upper():
        return "BLOCKED", {}
    out = {}
    for code, isin in re.findall(r"<td[^>]*>\s*([0-9A-Z]{4,6})[　\s]+[^<]*</td>\s*<td[^>]*>\s*([A-Z]{2}[A-Z0-9]{10})\s*</td>", text):
        out[code] = isin
    return ("OK" if out else "EMPTY"), out


def enrich_v0103(rows: list) -> dict:
    """把基本資料欄與 ISIN 補進每一列;回統計(給 V9)。"""
    basic = {}
    for key, market in (("twse_basic", "TWSE"), ("tpex_basic", "TPEX")):
        st, data = _CACHE_V0103.get(SRC[key], ("NOT_FETCHED", None))   # collect 剛抓過、尚未清
        for r in data or []:
            code = str(r.get("公司代號") or r.get("SecuritiesCompanyCode") or "").strip()
            if code:
                basic[(market, code)] = r
    isin_state, isin_map = {}, {}
    for market in ("TWSE", "TPEX"):
        isin_state[market], m = fetch_isin_v0103(market)
        isin_map.update(m)
    stat = {"rows": len(rows), "shares": 0, "capital": 0, "listing": 0, "par": 0,
            "isin_official": 0, "isin_computed": 0, "isin_badcheck": 0, "isin_state": isin_state}
    for row in rows:
        b = basic.get((row.get("market"), row.get("ticker")), {})
        row["listing_date"] = norm_date_v0103(pick_v0103(b, "listing_date"))
        row["par_value"] = norm_num_v0103(pick_v0103(b, "par_value"))
        row["shares_issued"] = norm_num_v0103(pick_v0103(b, "shares_issued"))
        row["capital"] = norm_num_v0103(pick_v0103(b, "capital"))
        off = isin_map.get(row.get("ticker"), "")
        if off:
            row["isin_code"], row["isin_source"] = off, ("official" if isin_valid_v0103(off) else "official_badcheck")
        else:
            row["isin_code"] = isin_computed_v0103(row.get("ticker", ""))
            row["isin_source"] = "computed" if row["isin_code"] else ""
        stat["shares"] += bool(row["shares_issued"])
        stat["capital"] += bool(row["capital"])
        stat["listing"] += bool(row["listing_date"])
        stat["par"] += bool(row["par_value"])
        stat["isin_official"] += row["isin_source"] == "official"
        stat["isin_computed"] += row["isin_source"] == "computed"
        stat["isin_badcheck"] += row["isin_source"] == "official_badcheck"
    return stat


_ORIG_COLLECT_V0103 = P1.collect_v0101
_ORIG_VERIFY_V0103 = P1.verify_v0101
_LAST_STAT_V0103: dict = {}


def collect_v0103(day: str) -> tuple:
    _CACHE_V0103.clear()
    _CACHE_ON_V0103[0] = True
    try:
        rows, rejected, states, zone = _ORIG_COLLECT_V0103(day)
    finally:
        _CACHE_ON_V0103[0] = False
    _LAST_STAT_V0103.clear()
    _LAST_STAT_V0103.update(enrich_v0103(rows) if rows else {"rows": 0})
    _CACHE_V0103.clear()
    return rows, rejected, states, zone


def verify_v0103(rows, rejected, states, prev, day, mins, zone) -> dict:
    v = _ORIG_VERIFY_V0103(rows, rejected, states, prev, day, mins, zone)
    s = _LAST_STAT_V0103
    n = max(1, s.get("rows") or len(rows) or 1)
    cover = (s.get("shares", 0) / n) if rows else 0.0
    lamp = "GREEN" if rows and cover >= SHARES_MIN_COVER_V0103 and not s.get("isin_badcheck") else ("YELLOW" if rows else "GREEN")
    v["checks"].append({"id": "V9", "name": "T1 欄覆蓋(股數 / 資本 / 上市日 / 面額 / ISIN)", "lamp": lamp,
                        "note": (f"股數 {s.get('shares', 0)}/{n}({cover:.1%})· 資本 {s.get('capital', 0)} · 上市日 {s.get('listing', 0)} · "
                                 f"面額 {s.get('par', 0)} · ISIN 官方 {s.get('isin_official', 0)} / 演算 {s.get('isin_computed', 0)} / "
                                 f"檢查碼不合 {s.get('isin_badcheck', 0)} · ISIN 來源 {s.get('isin_state')}")})
    v["lamp"] = lamp_v0100(v["checks"])
    return v


_ORIG_VIA_NET_PRIOR_V0103 = _ORIG_VIA_NET_PRIOR_V0103_SAVE


def _wire_v0103(on: bool) -> None:
    """本版的接線(網路入口 · 快取 · collect / verify)開或關;前版自測要看到它們自己的原接線。"""
    global _ORIG_VIA_NET_PRIOR_V0103
    if on:
        P1.fetch_json_v0100 = _cached_fetch_v0103
        P1.collect_v0101 = collect_v0103               # run_v0101 走 v0101 模組全域 → 經本版補欄
        P1.verify_v0101 = verify_v0103
        PRIOR._via_net = _forward_via_net_v0103
    else:
        P1.fetch_json_v0100 = _ORIG_FETCH_V0103
        P1.collect_v0101 = _ORIG_COLLECT_V0103
        P1.verify_v0101 = _ORIG_VERIFY_V0103
        PRIOR._via_net = _ORIG_VIA_NET_PRIOR_V0103


_wire_v0103(True)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    P1.TAG = PRIOR.TAG = TAG                           # 報告與輸出記本版
    return P1.main(args)


def selftest() -> int:
    import tempfile as _tf
    checks = []

    def chk(name, cond, note=""):
        checks.append((name, bool(cond), note))

    for code, known in (("2330", "TW0002330008"), ("2317", "TW0002317005"), ("1101", "TW0001101004")):
        chk(f"ISIN 演算 {code}", isin_computed_v0103(code) == known, isin_computed_v0103(code))
    chk("ISIN 驗檢查碼:改一碼就不合", isin_valid_v0103("TW0002330008") and not isin_valid_v0103("TW0002330007"))
    chk("非 4 碼不演算(不亂編)", isin_computed_v0103("00878") == "")
    chk("民國 / 西元日期", norm_date_v0103("1151109") == "2026-11-09" and norm_date_v0103("19620209") == "1962-02-09")
    chk("面額 / 數字去雜字", norm_num_v0103("新台幣                 10.0000元") == "10" and norm_num_v0103("7,523,181,742") == "7523181742")
    chk("欄位候選:中文鍵與英文鍵都認", pick_v0103({"上市日期": "19620209"}, "listing_date") == "19620209"
        and pick_v0103({"DateOfListing": "20180808"}, "listing_date") == "20180808"
        and pick_v0103({"paidin.capital.ntdollars": "1"}, "capital") == "1")

    quote_tw = [{"Code": "2330", "Name": "台積電"}, {"Code": "1101", "Name": "台泥"}, {"Code": "0050", "Name": "元大台灣50"}]
    quote_tp = [{"SecuritiesCompanyCode": "6488", "CompanyName": "環球晶"}]
    basic_tw = [{"公司代號": "2330", "公司簡稱": "台積電", "產業別": "24", "上市日期": "19940905",
                 "普通股每股面額": "新台幣 10.0000元", "實收資本額": "259327332420", "已發行普通股數或TDR原股發行股數": "25932733242"},
                {"公司代號": "1101", "公司簡稱": "台泥", "產業別": "01", "上市日期": "19620209"}]
    basic_tp = [{"SecuritiesCompanyCode": "6488", "CompanyAbbreviation": "環球晶", "DateOfListing": "20150925",
                 "ParValueOfCommonStock": "新台幣 10.0000元", "Paidin.Capital.NTDollars": "4780823620"}]
    isin_html = "<tr><td>2330　台積電</td><td>TW0002330008</td><td>1994/09/05</td></tr>"
    data = {SRC["twse_quote"]: quote_tw, SRC["tpex_quote"]: quote_tp, SRC["twse_basic"]: basic_tw, SRC["tpex_basic"]: basic_tp}
    calls = []

    class _Net:
        def http_json(self, url, timeout=30):
            calls.append(url)
            return {"state": "OK", "data": data[url]}

        def http_text(self, url, timeout=60):
            return {"state": "OK", "data": isin_html if url.endswith("2") else "FOR SECURITY REASONS, THIS PAGE CAN NOT BE ACCESSED."}

    keep = globals()["_via_net"]
    globals()["_via_net"] = lambda: _Net()
    try:
        rows, rejected, states, zone = P1.collect_v0101("2026-11-10")
        by = {r["ticker"]: r for r in rows}
        chk("collect 走本版(補 T1 欄)", "shares_issued" in by.get("2330", {}))
        chk("同一 URL 只抓一次(基本資料重用)", len(calls) == len(set(calls)) == 4, str(len(calls)))
        calls.clear()
        P1.fetch_json_v0100(SRC["twse_quote"]); P1.fetch_json_v0100(SRC["twse_quote"])
        chk("collect 外不快取(MDL010 / MDL008 照一請求一抓)", len(calls) == 2, str(len(calls)))
        chk("上市股數 / 資本 / 上市日 / 面額", by["2330"]["shares_issued"] == "25932733242" and by["2330"]["capital"] == "259327332420"
            and by["2330"]["listing_date"] == "1994-09-05" and by["2330"]["par_value"] == "10")
        chk("上櫃英文鍵也補到", by["6488"]["capital"] == "4780823620" and by["6488"]["listing_date"] == "2015-09-25")
        chk("ISIN:官方讀到用官方 · 被擋的用演算並標明", by["2330"]["isin_source"] == "official"
            and by["6488"]["isin_source"] == "computed" and by["6488"]["isin_code"] == isin_computed_v0103("6488"))
        chk("缺欄留空不編(1101 無股數)", by["1101"]["shares_issued"] == "")
        chk("清單只來自當天報價表(ETF 0050 照前版規則擋)", "0050" not in by)
        v = P1.verify_v0101(rows, rejected, states, [], "2026-11-10", {"TWSE": 1, "TPEX": 1}, zone)
        v9 = next(c for c in v["checks"] if c["id"] == "V9")
        chk("V9 股數覆蓋 < 95% → YELLOW 且照實計數", v9["lamp"] == "YELLOW" and "股數 1/3" in v9["note"], v9["note"][:80])
        with _tf.TemporaryDirectory() as td:
            rep = P1.run_v0101("2026-11-10", out_root=Path(td), mins={"TWSE": 1, "TPEX": 1})
            chk("run 全程:報告含 V9 · 不因 YELLOW 擋寫入", any(c["id"] == "V9" for c in rep["checks"]) and rep["lamp"] != "RED", rep["lamp"])
    finally:
        globals()["_via_net"] = keep
    _wire_v0103(False)
    try:
        rc_prior = PRIOR.selftest()
    finally:
        _wire_v0103(True)
    chk("v0102 本體自測照過(經本版轉接)", rc_prior == 0, f"rc {rc_prior}")
    chk("尾版保有前版公開名稱(TAILAPI)",
        all(n in globals() for n in dir(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n))))
    ok = sum(1 for _, c, _ in checks if c)
    for n, c, note in checks:
        print(("  [OK]   " if c else "  [FAIL] ") + n + (f" — {note}" if note and not c else ""))
    print(f"  [計] {TAG} 本版 {ok}/{len(checks)} · " + ("PASS" if ok == len(checks) else "FAIL"))
    return 0 if ok == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
