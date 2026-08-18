# -*- coding: utf-8 -*-
"""
VERITAS INTELLIGENCE ANALYTICS
VIA_LiveWire_ContractAdapter_v0100.py

接真值合約轉接層(LiveWire Contract Adapter)——外部模組匯入之工程化收斂。

本模組將十份外部交付模組中可用的概念收斂為一個可驗證、fail-closed 的
資料接線層,並修復其缺陷:

  匯入審計(Intake Audit)
  ----------------------
  A01 taiwan_stock_data_fetcher   : yfinance .TW/.TWO 切換 + TWSE/TPEx 端點概念保留;
                                    【缺陷修復】原版把寫死的假三大法人/融資/當沖數字
                                    標成 SUCCESS 回傳 → 本版嚴禁編造,無真值即
                                    fail-closed 回報 UNAVAILABLE 狀態。
  A02 ssot_matching_testing_engine: Schema 中立化 + 三段式比對(ticker 精確→名稱模糊
                                    →UNMAPPED fail-closed)概念保留;rapidfuzz/pydantic/
                                    deepdiff 相依全缺 → 以 stdlib difflib 重寫。
  A03 veritas_via_exact_dataset   : VIA v1.1 三十一族群名冊 → 轉為 mother-SSOT 對帳
                                    測試 fixture(input/VIA_v11_MotherSSOT_Fixture.json)。
  A04 engine_verification_suite   : Beta 中性化/PC1 驗證概念 → 改為對本套件
                                    def_residualize_panel 的性質測試。
  A05 rotation_plug_in_engine     : 盤中 VWAP 固定門檻(+0.8%/LUSI 0.5/信心 93.5%)
                                    違反動態 Criteria 治理 → 不併入,僅留介面紀錄。
  A06 integration_test_suite      : 內嵌 markdown + 幽靈 import,無法編譯 → 退回。
  A07 code_artifact_1             : 語法錯誤(雙括號 def)→ 退回。
  A08 stock_sector_analysis_engine: 無法編譯 + statsmodels 相依缺 → 退回
                                    (PCA/共整合概念已由 v0200 PC1Ratio 覆蓋)。

治理不變項:引擎核心永遠零網路;本轉接層是唯一允許碰網路的邊界模組,
且在無網路/無套件時 fail-closed,絕不以假資料冒充真值。
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple
import datetime as dt
import json
import re

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
MODULE_DIR = SCRIPT_DIR.parent
DEFAULT_FIXTURE = MODULE_DIR / "input" / "VIA_v11_MotherSSOT_Fixture.json"
DEFAULT_SSOT = MODULE_DIR / "input" / "VIA_TW_SubGroup_SSOT_v0100.xlsx"
DEFAULT_OUT = MODULE_DIR / "evidence" / "RUN_LIVEWIRE_ADAPTER_V0100"

VERSION = "0.1.00"

# 台股普通股代碼:四碼數字且首位非 0(00 開頭為 ETF/受益憑證)。
TICKER_REGEX = re.compile(r"^[1-9]\d{3}$")

# 引擎資料契約(def_generate_sector_panel 的替換介面)。
PANEL_CONTRACT_COLUMNS = [
    "Date", "Ticker", "Group", "Market", "AdjClose", "Turnover",
    "DaytradeTurnover", "ForeignNet", "TrustNet", "DealerNet", "WhaleNet",
]
MACRO_CONTRACT_COLUMNS = [
    "Date", "SOXRet", "TWSERet", "VIXLevel", "US10YDiff", "JPYDiff", "TWDResidual", "OilDiff",
]


def def_validate_ticker(ticker: object) -> bool:
    return bool(TICKER_REGEX.match(str(ticker).strip()))


# =============================================================================
# def 01 UNIVERSAL SCHEMA NEUTRALIZER(stdlib 重寫)
# =============================================================================


def def_normalize_stock_entry(raw: Mapping[str, Any]) -> Dict[str, Any]:
    ticker = raw.get("ticker") or raw.get("symbol") or raw.get("code") or raw.get("id") or ""
    name = raw.get("name") or raw.get("stock_name") or raw.get("title") or raw.get("company") or ""
    role = raw.get("role") or raw.get("type") or raw.get("category") or "PEER"
    market = raw.get("market") or raw.get("exchange") or ""
    return {
        "ticker": str(ticker).strip(),
        "name": str(name).strip(),
        "role": str(role).strip().upper(),
        "market": str(market).strip().upper(),
    }


def def_normalize_database(raw_db: Any) -> Dict[str, Dict[str, Any]]:
    """接受 list-of-sectors 或 dict-of-sectors(members/stocks/components 任一鍵)。"""
    out: Dict[str, Dict[str, Any]] = {}
    if isinstance(raw_db, list):
        for idx, item in enumerate(raw_db):
            sec = item.get("sector") or item.get("group") or f"Sector_{idx + 1}"
            members = item.get("members") or item.get("stocks") or item.get("components") or []
            out[str(sec)] = {"members": [def_normalize_stock_entry(m) for m in members]}
    elif isinstance(raw_db, dict):
        for sec, data in raw_db.items():
            if isinstance(data, dict):
                members = data.get("members") or data.get("stocks") or data.get("components") or []
            elif isinstance(data, list):
                members = data
            else:
                continue
            out[str(sec)] = {"members": [def_normalize_stock_entry(m) for m in members]}
    return out


# =============================================================================
# def 02 SSOT MATCHING(三段式:精確 ticker → difflib 模糊名稱 → fail-closed)
# =============================================================================


def def_name_similarity(a: str, b: str) -> float:
    return 100.0 * SequenceMatcher(None, a, b).ratio()


@dataclass
class MatchResult:
    matched: List[Dict[str, Any]] = field(default_factory=list)
    unmapped: List[str] = field(default_factory=list)
    fuzzy_resolved: List[str] = field(default_factory=list)


def def_reconcile_against_local(
    mother_raw: Any,
    local_members: pd.DataFrame,
    similarity_threshold: float = 60.0,
) -> Tuple[pd.DataFrame, MatchResult]:
    """
    以本地 SSOT(local_members: Ticker/Name/Group/Market)為 canonical,
    對未知母系統名冊做三段式對帳。母系統永不覆蓋本地 canonical(fail-closed)。
    """
    mother = def_normalize_database(mother_raw)
    local_by_ticker = local_members.drop_duplicates("Ticker").set_index("Ticker")
    local_names = local_by_ticker["Name"].astype(str).tolist()
    local_tickers = local_by_ticker.index.astype(str).tolist()

    rows: List[Dict[str, Any]] = []
    result = MatchResult()
    for sec, data in mother.items():
        for m in data["members"]:
            tk, nm = m["ticker"], m["name"]
            entry: Dict[str, Any] = {
                "MotherSector": sec, "MotherTicker": tk, "MotherName": nm,
                "MotherRole": m["role"], "TickerValid": def_validate_ticker(tk),
            }
            if tk in local_by_ticker.index:
                loc = local_by_ticker.loc[tk]
                entry.update({
                    "MatchType": "EXACT_TICKER_MATCH",
                    "LocalTicker": tk,
                    "LocalName": str(loc["Name"]),
                    "LocalGroup": str(loc["Group"]),
                    "NameAgrees": str(loc["Name"]) == nm,
                })
                result.matched.append(entry)
            else:
                best_score, best_i = -1.0, -1
                for i, ln in enumerate(local_names):
                    sc = def_name_similarity(nm, ln)
                    if sc > best_score:
                        best_score, best_i = sc, i
                if best_score >= similarity_threshold and best_i >= 0:
                    entry.update({
                        "MatchType": f"FUZZY_NAME_MATCH({best_score:.0f})",
                        "LocalTicker": local_tickers[best_i],
                        "LocalName": local_names[best_i],
                        "LocalGroup": str(local_by_ticker.iloc[best_i]["Group"]),
                        "NameAgrees": False,
                    })
                    result.fuzzy_resolved.append(f"{nm}({tk})→{local_names[best_i]}({local_tickers[best_i]})")
                    result.matched.append(entry)
                else:
                    entry.update({
                        "MatchType": "UNMAPPED_FAIL_CLOSED",
                        "LocalTicker": "", "LocalName": "", "LocalGroup": "",
                        "NameAgrees": False,
                    })
                    result.unmapped.append(f"{nm}({tk})")
            rows.append(entry)
    return pd.DataFrame(rows), result


# =============================================================================
# def 03 HONEST MARKET DATA FETCHER(fail-closed;修復 A01 假資料缺陷)
# =============================================================================


@dataclass
class FetchStatus:
    status: str          # LIVE / UNAVAILABLE_DEPENDENCY / UNAVAILABLE_NETWORK / INVALID_TICKER
    detail: str
    data: Optional[pd.DataFrame] = None
    symbol: str = ""


class HonestMarketDataFetcher:
    """
    唯一允許碰網路的邊界模組。原則:
    1. 無 yfinance 套件 → UNAVAILABLE_DEPENDENCY(不嘗試編造)。
    2. 網路被阻斷 → UNAVAILABLE_NETWORK(不回退到假數字)。
    3. 三大法人/當沖等籌碼欄位【永不】以預設值填充 —— 缺值就是缺值,
       上游引擎的 fail-closed 治理會處理缺值列。
    """

    def __init__(self, allow_network: bool = False):
        self.allow_network = allow_network

    def fetch_daily(self, ticker: str, period: str = "1y") -> FetchStatus:
        if not def_validate_ticker(ticker):
            return FetchStatus("INVALID_TICKER", f"'{ticker}' 不符 ^[1-9]\\d{{3}}$")
        if not self.allow_network:
            return FetchStatus("UNAVAILABLE_NETWORK", "network disabled by policy (engines are zero-network)")
        try:
            import yfinance as yf  # optional dependency
        except ImportError:
            return FetchStatus("UNAVAILABLE_DEPENDENCY", "yfinance not installed")
        for suffix in (".TW", ".TWO"):
            symbol = f"{ticker}{suffix}"
            try:
                df = yf.Ticker(symbol).history(period=period, interval="1d")
            except Exception as exc:
                return FetchStatus("UNAVAILABLE_NETWORK", f"{symbol}: {type(exc).__name__}")
            if df is not None and not df.empty and "Close" in df.columns:
                out = pd.DataFrame({
                    "Date": df.index.tz_localize(None) if getattr(df.index, "tz", None) is not None else df.index,
                    "AdjClose": df.get("Adj Close", df["Close"]).to_numpy(),
                    "Volume": df["Volume"].to_numpy(),
                })
                return FetchStatus("LIVE", f"fetched {len(out)} rows", out, symbol)
        return FetchStatus("UNAVAILABLE_NETWORK", "no data on .TW nor .TWO")


# =============================================================================
# def 04 PANEL CONTRACT VALIDATION(引擎替換介面的守門檢核)
# =============================================================================


def def_validate_panel_contract(panel: pd.DataFrame) -> List[str]:
    """回傳缺陷清單;空清單 = 契約合格,可直接替換 def_generate_sector_panel 輸出。"""
    faults: List[str] = []
    missing = [c for c in PANEL_CONTRACT_COLUMNS if c not in panel.columns]
    if missing:
        faults.append(f"MISSING_COLUMNS:{missing}")
        return faults
    if not pd.api.types.is_datetime64_any_dtype(panel["Date"]):
        faults.append("DATE_NOT_DATETIME")
    bad_ticker = panel.loc[~panel["Ticker"].astype(str).str.fullmatch(r"\d{4,6}"), "Ticker"].unique()
    if len(bad_ticker):
        faults.append(f"BAD_TICKERS:{list(bad_ticker)[:5]}")
    for col in ["AdjClose", "Turnover", "DaytradeTurnover"]:
        v = pd.to_numeric(panel[col], errors="coerce")
        if v.isna().any():
            faults.append(f"NON_NUMERIC:{col}")
        elif (v < 0).any():
            faults.append(f"NEGATIVE_VALUES:{col}")
    day = pd.to_numeric(panel["DaytradeTurnover"], errors="coerce")
    tot = pd.to_numeric(panel["Turnover"], errors="coerce")
    if ((day - tot) > 1e-6).any():
        faults.append("DAYTRADE_EXCEEDS_TURNOVER")
    dup = int(panel.duplicated(["Date", "Ticker"]).sum())
    if dup:
        faults.append(f"DUPLICATE_DATE_TICKER:{dup}")
    return faults


# =============================================================================
# def 05 EVIDENCE PIPELINE — v1.1 名冊 × 本地 SSOT 實測對帳
# =============================================================================


def def_load_local_ssot_members(ssot_path: Path) -> pd.DataFrame:
    import importlib.util
    import sys
    base_path = SCRIPT_DIR / "VIA_SectorFlow_AdaptiveChainedIndex_v0100.py"
    spec = importlib.util.spec_from_file_location("via_sectorflow_for_adapter", base_path)
    base = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = base
    assert spec.loader is not None
    spec.loader.exec_module(base)
    roster = base.def_extract_sector_membership(ssot_path)
    return roster[["Ticker", "Name", "Group", "Market", "CountingFlag"]]


def def_run_adapter_evidence(out_dir: Path = DEFAULT_OUT) -> Dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    tests: List[Dict[str, Any]] = []

    def add(tid: str, name: str, ok: bool, sev: str, ev: str) -> None:
        tests.append({"TestID": tid, "TestName": name,
                      "Status": "PASS" if ok else "FAIL", "Severity": sev, "Evidence": ev})

    # L01 ticker regex 契約
    cases = {"2330": True, "3081": True, "0050": False, "23300": False, "030001": False, "9999A": False}
    regex_ok = all(def_validate_ticker(k) == v for k, v in cases.items())
    add("L01", "台股普通股代碼 Regex 契約", regex_ok, "HARD", json.dumps(cases))

    # L02 schema 中立化:異鍵名/巢狀/清單 三種形態
    variants = [
        {"S": {"components": [{"symbol": "2330", "company": "台積電", "type": "LEADER"}]}},
        {"S": {"stocks": [{"code": "3037", "stock_name": "欣興"}]}},
        [{"group": "S", "members": [{"id": "1519", "title": "華城", "category": "leader"}]}],
    ]
    norm_ok = True
    for v in variants:
        nd = def_normalize_database(v)
        m = nd.get("S", {}).get("members", [])
        norm_ok &= bool(m) and def_validate_ticker(m[0]["ticker"]) and bool(m[0]["name"]) and m[0]["role"].isupper()
    add("L02", "UniversalSchemaNeutralizer 異形態正規化", norm_ok, "HARD", f"variants={len(variants)}")

    # L03 fail-closed fetcher:無網路授權 → 絕不編造(修復 A01 缺陷)
    fetcher = HonestMarketDataFetcher(allow_network=False)
    st = fetcher.fetch_daily("2330")
    honest_ok = st.status != "LIVE" and st.data is None
    add("L03", "Fetcher fail-closed(無真值即回報 UNAVAILABLE,零編造)", honest_ok, "HARD",
        f"status={st.status} detail={st.detail}")
    st_bad = fetcher.fetch_daily("0050")
    add("L04", "Fetcher 攔截非普通股代碼", st_bad.status == "INVALID_TICKER", "HARD", st_bad.status)

    # L05 契約守門:合格面板通過、缺陷面板被攔截
    good = pd.DataFrame({
        "Date": pd.to_datetime(["2026-01-02", "2026-01-03"]),
        "Ticker": ["2330", "2330"], "Group": ["C", "C"], "Market": ["TWSE", "TWSE"],
        "AdjClose": [1000.0, 1010.0], "Turnover": [5e9, 6e9], "DaytradeTurnover": [1e9, 2e9],
        "ForeignNet": [1e8, -2e8], "TrustNet": [5e7, 5e7], "DealerNet": [0.0, 0.0], "WhaleNet": [0.0, 0.0],
    })
    faults_good = def_validate_panel_contract(good)
    bad = good.copy()
    bad.loc[0, "DaytradeTurnover"] = 9e9  # 當沖 > 總成交:必攔
    faults_bad = def_validate_panel_contract(bad)
    add("L05", "面板契約守門(合格通過/當沖>成交攔截)", not faults_good and bool(faults_bad), "HARD",
        f"good={faults_good} bad={faults_bad}")

    # L06 對帳實測:VIA v1.1 名冊(76 檔/15 群) × 本地 SSOT(378 列)
    mother = json.loads(DEFAULT_FIXTURE.read_text("utf-8"))
    local = def_load_local_ssot_members(DEFAULT_SSOT)
    ledger, result = def_reconcile_against_local(mother, local)
    exact = int((ledger["MatchType"] == "EXACT_TICKER_MATCH").sum())
    fuzzy = len(result.fuzzy_resolved)
    unmapped = len(result.unmapped)
    add("L06", "v1.1 母名冊對帳:多數成員以 ticker 精確命中本地 SSOT",
        exact > len(ledger) * 0.5 and exact + fuzzy + unmapped == len(ledger), "HARD",
        f"total={len(ledger)} exact={exact} fuzzy={fuzzy} unmapped={unmapped}")
    tests.append({
        "TestID": "L07", "TestName": "未命中成員保留為 Review Warning(fail-closed,不覆蓋 canonical)",
        "Status": "WARN" if unmapped else "PASS", "Severity": "REVIEW",
        "Evidence": f"unmapped={result.unmapped[:10]}",
    })

    # L08 殘差化性質測試(A04 概念 → 對本套件 def_residualize_panel)
    import importlib.util
    import sys
    base_path = SCRIPT_DIR / "VIA_SectorFlow_AdaptiveChainedIndex_v0100.py"
    spec = importlib.util.spec_from_file_location("via_sectorflow_for_adapter2", base_path)
    base = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = base
    spec.loader.exec_module(base)
    rng = np.random.default_rng(42)
    n = 120
    dates = pd.bdate_range("2026-01-02", periods=n)
    twse = rng.normal(0.001, 0.015, n)
    sox = rng.normal(0.001, 0.016, n)
    stock = 1.5 * twse + rng.normal(0.0, 0.003, n)
    clean = pd.DataFrame({
        "Date": list(dates), "Ticker": "9990", "Group": "T", "Ret": stock,
    })
    macro = pd.DataFrame({"Date": dates, "SOXRet": sox, "TWSERet": twse})
    resid = base.def_residualize_panel(clean, macro)
    r = float(np.corrcoef(resid["PureRet"], twse)[0, 1])
    add("L08", "OLS 殘差化性質:Beta 1.5 個股殘差對大盤相關 ≈ 0", abs(r) < 0.05, "HARD", f"resid_corr={r:.5f}")

    # ---- CONSOLIDATE + Gate ----
    test_df = pd.DataFrame(tests)
    hard = int(((test_df["Status"] == "FAIL") & (test_df["Severity"] == "HARD")).sum())
    warn = int((test_df["Status"] == "WARN").sum())
    status = "ADAPTER_VERIFIED_FAIL_CLOSED" if hard == 0 else "ADAPTER_BLOCKED"
    summary = {
        "Engine": "VIA_LiveWire_ContractAdapter", "Version": VERSION,
        "GeneratedAt": dt.datetime.now().isoformat(timespec="seconds"),
        "Status": status, "HardFailures": hard, "ReviewWarnings": warn,
        "IntakeAudit": {
            "integrated": ["A01(修復假資料後)", "A02(stdlib 重寫)", "A03(對帳 fixture)", "A04(性質測試)"],
            "rejected": ["A05(固定市場門檻違反治理)", "A06(無法編譯)", "A07(語法錯誤)", "A08(無法編譯)"],
        },
        "ReconcileSummary": {"total": len(ledger), "exact": exact, "fuzzy": fuzzy, "unmapped": unmapped},
        "Policy": "adapter-is-the-only-network-boundary / engines-zero-network / no-fabricated-data",
    }
    ledger.to_csv(out_dir / "mother_ssot_reconcile_ledger.csv", index=False, encoding="utf-8-sig")
    test_df.to_csv(out_dir / "adapter_test_ledger.csv", index=False, encoding="utf-8-sig")
    (out_dir / "adapter_run_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"summary": summary, "tests": test_df, "ledger": ledger}


if __name__ == "__main__":
    result = def_run_adapter_evidence()
    s = result["summary"]
    print("=" * 88)
    print(f"VIA LiveWire Contract Adapter v{VERSION}")
    print("Status      :", s["Status"])
    print("Hard Fail   :", s["HardFailures"], "| Review Warn:", s["ReviewWarnings"])
    print("Reconcile   :", s["ReconcileSummary"])
    print("=" * 88)
    for _, t in result["tests"].iterrows():
        print(f"  [{t['Status']}] {t['TestID']} {t['TestName']} :: {str(t['Evidence'])[:90]}")
    raise SystemExit(0 if s["HardFailures"] == 0 else 2)
