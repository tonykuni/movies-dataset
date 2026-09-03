#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VDF_ENG072_StoryRotationBridge v0100 — 故事族群輪動引擎 v0.5 橋接(批325)
======================================================================
操作員令(批325):上傳 VIA_TW_Story_Group_Rotation_v0500_FULL 「請完成自動完成以下的
整合」+「核准自行完成的權限」。
包=外部 PIT 契約引擎(fail-closed;16 引擎+53 測;原件收容於
supportive modules/references/intake/VIA_StoryGroupRotation_b325/,零改動)。
本橋=VIA 庫 → 包契約六主線輸入+候選 cohort+選配月營收 → preflight-real → run-real,
每一欄的來源與衍生律誠實標註於缺口冊(GAP);缺口=BLOCKED/HOLD 如實列,不捏造。
輸入映射(REAL_DATA_SCHEMA v0.5):
  trading_calendar   ← tw_prices_adj 交易日 + 下一週日曆日(契約要求 as-of 後至少一交易日;DERIVED)
  market_universe    ← 庫內各標的首末日(舊格式單版本相容模式;KnownAt=ValidFrom 08:30=DERIVED 非真知悉時)
  full_market_daily  ← Adj_Close(tw_prices_adj)·TurnoverValue=close×volume(DERIVED)
                       ·DayTradeTurnover=TurnoverValue×市場當沖比(tw_daytrade_market;TPEX 22 日;TWSE 無=缺值)
                       ·MarketCap=缺(庫無流通股數=GAP-01)·漲跌停鎖定=未知(缺值,不當 False)
                       ·法人淨額=淨股數×收盤(DERIVED)·融資融券餘額值=餘額股×收盤(DERIVED)
                       ·AvailableAt:量價 15:00 / 法人 16:30 / 融資融券 21:30(+08:00;公告慣例=DERIVED)
  membership_events  ← VDF_StoryGroup_Registry 尾版(ADD·PENDING;統計驗證先於人工核准=包治理律)
  candidate cohort   ← 同冊(CandidateGroupId/GroupName/Ticker/Name/Market/CandidateRole/…)
  macro_vintages     ← USDTWD(global_daily TWD=X);DXY=缺;TW10Y=缺(官方 TPEX 雜湊來源未備=Sharpe HOLD)
  active_etf_holdings← ENG051 holdings_daily parquet(AvailableAt=fetched_at 真時戳)
  monthly_revenue    ← tw_monthly_revenue(選配;AvailableAt=fetched_at)
輸出:VIA_Reports/story_rotation/{data/input,config,data/output/RUN_*}+GAP_<stamp>.json
      +VIA_UI_StoryRotation_v0100.html(零 CDN;預檢表/執行狀態/缺口冊/包自測)
用法:python VDF_ENG072_StoryRotationBridge_v0100.py [export|preflight|run|--pkgtest|--selftest]
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
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import glob
import html
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent.parent
MEGA = VIA / "functional modules" / "VDF" / "output_hub" / "mega"
DB_TW = MEGA / "vdf_tw_market.duckdb"
DB_GL = MEGA / "vdf_global_market.duckdb"
HOLD_DIR = VIA / "functional modules" / "VDF" / "output_hub" / "active_tw_etf" / "active_tw_etf_holdings" / "parquet" / "holdings_daily"
INTAKE = VIA / "supportive modules" / "references" / "intake" / "VIA_StoryGroupRotation_b325"
WORK = VIA / "VIA_Reports" / "story_rotation"
INP = WORK / "data" / "input"
CFG = WORK / "config" / "system_config.json"
UI = VIA / "supportive modules" / "ui_support" / "VIA_UI_StoryRotation_v0100.html"
TZ = "+08:00"
T_PRICE, T_INST, T_MARGIN, T_FX = "15:00:00", "16:30:00", "21:30:00", "17:00:00"
RUN_TIMEOUT = 1800

GAP_BOOK = [
    ("GAP-01", "MarketCap", "庫無流通股數/市值;LaggedCap 因子 lane 無法成立",
     "補源:TWSE t187ap03_L「已發行普通股數」+TPEX 對應欄→shares 表(快照非 PIT=標 DERIVED_CURRENT_SHARES)×收盤"),
    ("GAP-02", "DayTradeTurnover", "個股當沖僅市場級比例代位(TPEX 22 日;TWSE 無)=多數日期缺值→契約阻擋",
     "補源:TWSE 當沖逐股(WAF 候源 L12)+TPEX 逐股;缺值日引擎 fail-closed=誠實"),
    ("GAP-03", "IsLimitUpLocked/IsLimitDownLocked", "未知=缺值(契約:不得當 False);注意力 lane 鎖定修正不啟用",
     "補源:漲跌停旗標(TWSE MI_INDEX 或由 prev_close×1.1 推導=DERIVED 需明令)"),
    ("GAP-04", "DXY", "全球庫無 DXY 序列(僅 TWD=X)", "補源:OmniFetch 加 DX-Y.NYB 車道"),
    ("GAP-05", "Taiwan10YYield", "無 TPEX 官方 URL+64hex payload 雜湊之 PIT 序列;Sharpe/Sortino 保持 HOLD(契約禁固定利率)",
     "補源:ENG071 同意閘 TW10Y intake 正本→附 SourceURL/PayloadHash"),
    ("GAP-06", "KnownAt/AvailableAt", "庫無擷取時戳;以公告慣例時刻衍生(DERIVED)非真知悉時",
     "補源:入庫層記 ingested_at(ENG054/056 增欄)"),
    ("GAP-07", "membership ApprovedAt", "故事冊=操作員上傳(批308);事件以 PENDING 入 ledger=先統計驗證後人工核准(包治理律);歷史 PIT 成分無",
     "人工核准後追加 APPROVED 事件(append-only)"),
]


def _con(db: Path, read_only: bool = True):
    import duckdb
    return duckdb.connect(str(db), read_only=read_only)


def pkg_root() -> Path | None:
    hits = sorted(INTAKE.glob("VIA_TW_Story_Group_Rotation_v*"))
    return hits[-1] if hits else None


def _ts(date_s: str, hms: str) -> str:
    return f"{date_s} {hms}{TZ}"


def _yf(code: str, market: str) -> str:
    return f"{code}.TWO" if str(market).upper() == "TPEX" else f"{code}.TW"


def load_stories() -> tuple[list[dict], str]:
    hits = sorted((VIA / "supportive modules" / "registry").glob("VDF_StoryGroup_Registry_v*.json"))
    if not hits:
        return [], ""
    d = json.loads(hits[-1].read_text(encoding="utf-8"))
    return d.get("stories", []), hits[-1].name


def export(do_print: bool = True) -> dict:
    """VIA 庫→契約輸入(七檔+選配);回各檔列數與缺口統計"""
    import pandas as pd
    INP.mkdir(parents=True, exist_ok=True)
    (WORK / "config").mkdir(parents=True, exist_ok=True)
    out: dict = {"files": {}, "stats": {}}
    if not DB_TW.exists():
        out["err"] = "DB_TW 缺"
        return out
    c = _con(DB_TW)
    lst = c.execute("SELECT code, name, market, yf_ticker FROM tw_listings "
                    "WHERE length(code)=4 AND regexp_matches(code,'^[0-9]{4}$')").df()
    lst = lst.drop_duplicates("code")
    px = c.execute("""
        SELECT CAST(a.date AS VARCHAR) AS date, a.ticker, a.adj_close, p.close, p.volume
        FROM tw_prices_adj a JOIN tw_daily_prices p ON p.date=a.date AND p.ticker=a.ticker
        WHERE a.ticker <> '_NOOP_' AND a.adj_close IS NOT NULL
        ORDER BY 1,2""").df()
    dt = c.execute("SELECT CAST(date AS VARCHAR) AS date, market, dt_volume_pct FROM tw_daytrade_market").df()
    inst = c.execute("SELECT CAST(date AS VARCHAR) AS date, code, foreign_net, trust_net, dealer_net FROM tw_chip_inst").df()
    mg = c.execute("SELECT CAST(date AS VARCHAR) AS date, code, margin_bal, short_bal FROM tw_chip_margin").df()
    rev = c.execute("SELECT code, ym, revenue, CAST(fetched_at AS VARCHAR) AS fetched_at FROM tw_monthly_revenue").df() \
        if "tw_monthly_revenue" in {r[0] for r in c.execute("show tables").fetchall()} else pd.DataFrame()
    c.close()
    # --- 日曆 ---
    days = sorted(px["date"].unique())
    nxt = datetime.strptime(days[-1], "%Y-%m-%d") + timedelta(days=1)
    while nxt.weekday() >= 5:
        nxt += timedelta(days=1)
    cal = pd.DataFrame({"Date": days + [nxt.strftime("%Y-%m-%d")]})
    cal.to_csv(INP / "trading_calendar.csv", index=False)
    out["files"]["trading_calendar"] = len(cal)
    # --- 母體(舊格式單版本相容) ---
    px["code"] = px["ticker"].str.split(".").str[0]
    px["Market"] = px["ticker"].str.endswith(".TWO").map({True: "TPEX", False: "TWSE"})
    # 實錄批325:契約要求每日 roster 與觀測雙向完全一致;標的序列有洞(如 1227/2417)=以連續段拆多列
    # (舊格式相容律:Ticker+ValidFrom 唯一、區間不重疊)→每段一列
    didx = {d_: i for i, d_ in enumerate(days)}
    seg_rows = []
    for tkr, grp in px.groupby("ticker"):
        mk = grp["Market"].iloc[0]
        idxs = sorted(didx[d_] for d_ in grp["date"].unique())
        start = prev = idxs[0]
        for i in idxs[1:] + [None]:
            if i is None or i != prev + 1:
                seg_rows.append({"Ticker": tkr, "Market": mk, "AssetType": "COMMON_STOCK",
                                 "ValidFrom": days[start],
                                 "ValidTo": "" if days[prev] == days[-1] else days[prev],
                                 "KnownAt": _ts(days[start], "08:30:00")})
                if i is not None:
                    start = i
            if i is not None:
                prev = i
    uni = pd.DataFrame(seg_rows)
    uni.to_csv(INP / "market_universe_history.csv", index=False)
    out["files"]["universe_history"] = len(uni)
    # --- 全市場日表 ---
    fm = px.rename(columns={"date": "Date", "ticker": "Ticker", "adj_close": "Adj_Close"}).copy()
    fm["TurnoverValue"] = fm["close"] * fm["volume"]
    dt["dt_pct"] = dt["dt_volume_pct"] / 100.0
    fm = fm.merge(dt[["date", "market", "dt_pct"]].rename(columns={"date": "Date", "market": "Market"}),
                  on=["Date", "Market"], how="left")
    fm["DayTradeTurnover"] = fm["TurnoverValue"] * fm["dt_pct"]
    fm["MarketCap"] = float("nan")
    fm["MarketDataAvailableAt"] = [_ts(d, T_PRICE) for d in fm["Date"]]
    fm["IsLimitUpLocked"] = pd.array([None] * len(fm), dtype="boolean")
    fm["IsLimitDownLocked"] = pd.array([None] * len(fm), dtype="boolean")
    inst = inst.rename(columns={"date": "Date"})
    fm = fm.merge(inst, on=["Date", "code"], how="left")
    for src, col in (("foreign_net", "ForeignNetAmount"), ("trust_net", "InvestmentTrustNetAmount"),
                     ("dealer_net", "DealerNetAmount")):
        fm[col] = fm[src] * fm["close"]
        fm[col + "AvailableAt"] = [_ts(d, T_INST) if pd.notna(v) else None for d, v in zip(fm["Date"], fm[col])]
    mg = mg.rename(columns={"date": "Date"})
    fm = fm.merge(mg, on=["Date", "code"], how="left")
    fm["MarginBalanceValue"] = fm["margin_bal"] * fm["close"]
    fm["ShortBalanceValue"] = fm["short_bal"] * fm["close"]
    for col in ("MarginBalanceValue", "ShortBalanceValue"):
        fm[col + "AvailableAt"] = [_ts(d, T_MARGIN) if pd.notna(v) else None for d, v in zip(fm["Date"], fm[col])]
    # 契約:Market 由母體 metadata 併入(日表自帶=merge 撞欄 KeyError;實錄批325)→日表不含 Market
    keep = ["Date", "Ticker", "Adj_Close", "TurnoverValue", "DayTradeTurnover", "MarketCap",
            "MarketDataAvailableAt", "IsLimitUpLocked", "IsLimitDownLocked",
            "ForeignNetAmount", "ForeignNetAmountAvailableAt", "InvestmentTrustNetAmount",
            "InvestmentTrustNetAmountAvailableAt", "DealerNetAmount", "DealerNetAmountAvailableAt",
            "MarginBalanceValue", "MarginBalanceValueAvailableAt", "ShortBalanceValue", "ShortBalanceValueAvailableAt"]
    fm = fm[keep].copy()
    fm["Date"] = pd.to_datetime(fm["Date"]).dt.date
    fm.to_parquet(INP / "full_market_daily.parquet", index=False)
    out["files"]["full_market_daily"] = len(fm)
    out["stats"] = {"tickers": int(fm["Ticker"].nunique()), "days": len(days),
                    "daytrade_cover_rows": int(fm["DayTradeTurnover"].notna().sum()),
                    "inst_cover_rows": int(fm["ForeignNetAmount"].notna().sum()),
                    "margin_cover_rows": int(fm["MarginBalanceValue"].notna().sum()),
                    "marketcap_cover_rows": 0}
    # --- 故事冊→事件 ledger(PENDING)+候選 cohort ---
    stories, reg_name = load_stories()
    lmap = lst.set_index("code")
    ev, cand = [], []
    seq = 0
    now_s = datetime.now().strftime("%Y-%m-%d %H:%M:%S") + TZ
    for s in stories:
        gid = f"S{s.get('story_id', '')}"
        gname = s.get("story_group", "")
        for code in s.get("tickers", []):
            if code not in lmap.index:
                continue
            mk = lmap.loc[code, "market"]
            t = _yf(code, mk)
            seq += 1
            ev.append({"Sequence": seq, "EventId": f"EVT-{gid}-{code}", "EventType": "ADD", "GroupId": gid,
                       "GroupName": gname, "Ticker": t, "ExposureShare": "", "ApprovalStatus": "PENDING",
                       "ApprovedAt": "", "ValidFrom": "", "ValidTo": "",
                       "Reason": "VDF story registry (operator upload b308); awaiting statistical validation + human approval",
                       "SourceVersion": reg_name, "SupersedesEventId": "", "RecordedAt": now_s, "KnownAt": now_s,
                       "AvailableAt": now_s, "IngestedAt": now_s})
            cand.append({"CandidateGroupId": gid, "GroupName": gname, "Ticker": code,
                         "Name": lmap.loc[code, "name"], "Market": mk, "CandidateRole": "P",
                         "SourceVersion": reg_name, "EvidenceTier": "OPERATOR_UPLOAD_b308", "VerificationIssue": ""})
    pd.DataFrame(ev).to_csv(INP / "membership_events.csv", index=False)
    cdf = pd.DataFrame(cand)
    cdf.to_csv(INP / "candidate_story_membership_via.csv", index=False)
    out["files"]["membership_events"] = len(ev)
    out["files"]["candidate"] = len(cdf)
    out["stats"]["candidate_shape"] = {"groups": int(cdf["CandidateGroupId"].nunique()) if len(cdf) else 0,
                                       "membership_rows": int(len(cdf)),
                                       "distinct_tickers": int(cdf["Ticker"].nunique()) if len(cdf) else 0}
    # --- 巨觀 vintages ---
    mac = pd.DataFrame(columns=["ObservationDate", "AvailableAt", "USDTWD", "DXY", "Taiwan10YYield", "Source",
                                "SourceAuthority", "SourceURL", "SourcePayloadHash", "YieldUnit", "InstrumentId",
                                "OfficialSourceVerified"])
    if DB_GL.exists():
        gc = _con(DB_GL)
        fx = gc.execute("SELECT CAST(date AS VARCHAR) AS d, close FROM global_daily WHERE ticker='TWD=X' "
                        "AND close IS NOT NULL ORDER BY 1").df()
        gc.close()
        mac = pd.DataFrame({"ObservationDate": fx["d"], "AvailableAt": [_ts(d, T_FX) for d in fx["d"]],
                            "USDTWD": fx["close"], "DXY": float("nan"), "Taiwan10YYield": float("nan"),
                            "Source": "yahoo_chart:TWD=X", "SourceAuthority": "", "SourceURL": "",
                            "SourcePayloadHash": "", "YieldUnit": "PERCENT", "InstrumentId": "",
                            "OfficialSourceVerified": False})
    mac.to_csv(INP / "macro_vintages.csv", index=False)
    out["files"]["macro_vintages"] = len(mac)
    # --- 主動 ETF 持股快照 ---
    hold_files = sorted(glob.glob(str(HOLD_DIR / "**" / "*.parquet"), recursive=True))
    if hold_files:
        h = pd.concat([pd.read_parquet(f) for f in hold_files], ignore_index=True)
        h["PortfolioDate"] = pd.to_datetime(h["portfolio_date"]).dt.strftime("%Y-%m-%d")
        h["AvailableAt"] = pd.to_datetime(h["fetched_at"]).dt.strftime("%Y-%m-%d %H:%M:%S") + TZ
        snap = pd.DataFrame({"ETFId": h["etf_ticker"], "ETFName": h["etf_name"], "PortfolioDate": h["PortfolioDate"],
                             "AvailableAt": h["AvailableAt"], "Ticker": h["holding_yf_ticker"],
                             "Shares": h["shares"], "WeightPct": h["weight_pct"], "ETFUnits": "", "NAV": "",
                             "AUM": "", "Price": "", "IsComplete": True, "CompletenessReason": "",
                             "SourceType": h["source_type"], "SourceURL": h["source_url"], "SourcePayloadHash": "",
                             "FetchedAt": h["AvailableAt"],
                             "SnapshotId": h["etf_ticker"].astype(str) + "_" + h["PortfolioDate"]})
    else:
        snap = pd.DataFrame(columns=["ETFId", "ETFName", "PortfolioDate", "AvailableAt", "Ticker", "Shares", "WeightPct",
                                     "ETFUnits", "NAV", "AUM", "Price", "IsComplete", "CompletenessReason", "SourceType",
                                     "SourceURL", "SourcePayloadHash", "FetchedAt", "SnapshotId"])
    snap.to_csv(INP / "active_etf_holding_snapshots.csv", index=False)
    out["files"]["active_etf_holdings"] = len(snap)
    # --- 選配月營收 ---
    if len(rev):
        rv = pd.DataFrame({"Ticker": [_yf(c_, lmap.loc[c_, "market"]) if c_ in lmap.index else f"{c_}.TW" for c_ in rev["code"]],
                           "ReportMonth": rev["ym"].astype(str).str.replace(r"^(\d{4})(\d{2})$", r"\1-\2", regex=True),
                           "AvailableAt": rev["fetched_at"].astype(str).str.slice(0, 19) + TZ,
                           "Revenue": rev["revenue"], "ReportingPeriodMonths": 1, "Source": "MOPS(tw_monthly_revenue)",
                           "EvidenceTier": "OFFICIAL_MOPS"})
        rv.to_csv(INP / "monthly_revenue_vintages.csv", index=False)
        out["files"]["monthly_revenue"] = len(rv)
    # --- 設定檔(包正本→VIA 工作區;相對路徑=base_dir=WORK) ---
    pk = pkg_root()
    if pk is None:
        out["err"] = "包缺(intake VIA_StoryGroupRotation_b325)"
        return out
    cfg = json.loads((pk / "config" / "system_config.json").read_text(encoding="utf-8"))
    cfg["local_inputs"] = {k: f"data/input/{Path(v).name}" for k, v in cfg["local_inputs"].items()}
    cfg["candidate_story_membership"] = "data/input/candidate_story_membership_via.csv"
    cfg["candidate_shape"] = dict(out["stats"]["candidate_shape"], meaning="VIA_STORY_REGISTRY_VALIDATION_COHORT_NOT_APPROVED")
    cfg["_via_bridge"] = {"engine": Path(__file__).name, "package": pk.name, "exported_at": now_s,
                          "derivations": [g[1] + ":" + g[2] for g in GAP_BOOK]}
    CFG.write_text(json.dumps(cfg, ensure_ascii=False, indent=1), encoding="utf-8")
    out["config"] = str(CFG)
    if do_print:
        print(f"[橋接] 輸出 {len(out['files'])} 檔 → {INP} · 標的 {out['stats']['tickers']} · 交易日 {out['stats']['days']}"
              f" · 當沖覆蓋列 {out['stats']['daytrade_cover_rows']} · 法人覆蓋列 {out['stats']['inst_cover_rows']}"
              f" · 候選 {out['stats']['candidate_shape']}")
    return out


def _run_pkg(args: list[str], timeout: int) -> dict:
    pk = pkg_root()
    if pk is None:
        return {"rc": 127, "out": "", "err": "包缺"}
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    try:
        r = subprocess.run([sys.executable, str(pk / "run_system.py"), *args, "--config", str(CFG)],
                           capture_output=True, text=True, timeout=timeout, cwd=str(pk), env=env)
        return {"rc": r.returncode, "out": r.stdout, "err": r.stderr}
    except subprocess.TimeoutExpired:
        return {"rc": 124, "out": "", "err": f"逾時 {timeout}s"}


def preflight(do_print: bool = True) -> dict:
    if not CFG.exists():
        export(do_print=False)
    r = _run_pkg(["preflight-real"], 300)
    rows = []
    try:
        rows = json.loads(r["out"])
    except Exception:
        pass
    res = {"rc": r["rc"], "rows": rows, "err": (r["err"] or "")[-800:]}
    if do_print:
        print(f"=== preflight-real(rc={r['rc']})===")
        for x in rows:
            print(f"  [{x.get('PreflightStatus')}] {x.get('InputName')} ({x.get('InputRole')})")
        if not rows:
            print("  [FAIL] 無預檢輸出:" + res["err"][-300:])
    return res


def _block_reason(txt: str) -> str:
    lines = [ln.strip() for ln in (txt or "").splitlines() if ln.strip()]
    for ln in reversed(lines):
        if any(k in ln for k in ("Error", "BLOCK", "block", "ValueError", "KeyError", "HOLD")):
            return ln[:400]
    return (lines[-1] if lines else "")[:400]


def run(do_print: bool = True) -> int:
    t0 = time.time()
    ex = export(do_print=do_print)
    if "err" in ex:
        print(f"[FAIL] {ex['err']}")
        return 2
    pf = preflight(do_print=do_print)
    core_ok = bool(pf["rows"]) and all(not x.get("BlocksCorePipeline") for x in pf["rows"])
    state, reason, run_out = "BLOCKED_PREFLIGHT", "", {}
    if core_ok:
        run_out = _run_pkg(["run-real"], RUN_TIMEOUT)
        if run_out["rc"] == 0:
            state = "PASS"
        else:
            state = "BLOCKED_RUN_REAL"
            reason = _block_reason(run_out["err"] or run_out["out"])
    else:
        reason = "預檢主線輸入缺:" + ", ".join(x["InputName"] for x in pf["rows"] if x.get("BlocksCorePipeline"))
    attribution = []
    full = (run_out.get("err") or run_out.get("out") or "")[-6000:] + reason   # 歸因掃全尾流(原因欄僅 400 字)
    if "'ExpectedTPEX': 0" in full:
        attribution.append("母體無 TPEX 標的(本庫殘庫僅 TWSE;工作站全量庫應有 .TWO)=契約雙市場閘阻擋")
    if "InvalidETRRows" in full and "'InvalidETRRows': 0" not in full:
        attribution.append("GAP-02 個股當沖缺值→ETR 無效列(契約不截零=阻擋)")
    if "MissingOrdinaryStocks" in full and "'MissingOrdinaryStocks': 0" not in full:
        attribution.append("每日 roster 與觀測不一致(母體分段律已處理連續洞;殘留=資料缺日)")
    if "KeyError" in full:
        attribution.append("欄位契約不合(橋接映射待修)")
    runs = sorted((WORK / "data" / "output").glob("RUN_*")) if (WORK / "data" / "output").exists() else []
    stamp = time.strftime("%Y%m%d_%H%M%S")
    gap = {"ts": stamp, "engine": Path(__file__).name, "package": (pkg_root() or Path("")).name,
           "state": state, "reason": reason, "attribution": attribution, "elapsed_s": round(time.time() - t0, 1),
           "export": ex, "preflight": pf["rows"], "run_rc": run_out.get("rc"),
           "run_tail": (run_out.get("err") or run_out.get("out") or "")[-1500:],
           "latest_run_dir": str(runs[-1]) if runs else "",
           "gap_book": [{"id": g[0], "field": g[1], "gap": g[2], "fix": g[3]} for g in GAP_BOOK]}
    WORK.mkdir(parents=True, exist_ok=True)
    (WORK / f"GAP_{stamp}.json").write_text(json.dumps(gap, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    render(gap)
    if do_print:
        print(f"=== 故事族群輪動橋接 · 狀態 {state} · {gap['elapsed_s']}s ===")
        if reason:
            print(f"  [阻擋原因] {reason[:300]}")
        for a_ in attribution:
            print(f"  [歸因] {a_}")
        print(f"  缺口冊 {len(GAP_BOOK)} 條(誠實;補源見頁)· 存證 GAP_{stamp}.json · 頁 {UI.name}")
    return 0 if state == "PASS" else 2


def pkgtest(do_print: bool = True) -> dict:
    pk = pkg_root()
    if pk is None:
        return {"rc": 127, "summary": "包缺"}
    r = subprocess.run([sys.executable, str(pk / "run_tests.py")], capture_output=True, text=True,
                       timeout=900, cwd=str(pk))
    tail = (r.stderr or r.stdout).strip().splitlines()
    summ = next((ln for ln in reversed(tail) if ln.startswith(("Ran ", "OK", "FAILED"))), "")
    ran = next((ln for ln in tail if ln.startswith("Ran ")), "")
    res = {"rc": r.returncode, "ran": ran, "summary": summ,
           "missing_sibling": "candidate_membership_v21.csv" in (r.stderr or "")}
    for d in pk.rglob("__pycache__"):
        pass  # 收容件內 pycache 由 .gitignore 全域規則忽略;不刪不動
    if do_print:
        print(f"[包自測] {ran} · {summ} · 缺姊妹包檔={res['missing_sibling']}")
    return res


def render(gap: dict) -> None:
    rows = "".join(
        f"<tr><td>{html.escape(str(x.get('InputName')))}</td><td>{html.escape(str(x.get('InputRole')))}</td>"
        f"<td class='{ 'ok' if x.get('PreflightStatus') == 'PASS' else 'bad'}'>{html.escape(str(x.get('PreflightStatus')))}</td></tr>"
        for x in gap.get("preflight", []))
    gaps = "".join(f"<tr><td>{g['id']}</td><td>{html.escape(g['field'])}</td><td>{html.escape(g['gap'])}</td>"
                   f"<td>{html.escape(g['fix'])}</td></tr>" for g in gap.get("gap_book", []))
    st = gap.get("export", {}).get("stats", {})
    files = gap.get("export", {}).get("files", {})
    frows = "".join(f"<tr><td>{html.escape(k)}</td><td class='mono'>{v}</td></tr>" for k, v in files.items())
    cls = "ok" if gap["state"] == "PASS" else "bad"
    page = f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>VIA · 故事族群輪動橋接</title>
<style>
:root{{--bg:#f5f5f2;--paper:#fff;--ink:#1f2530;--mut:#6d7688;--line:#dcdfe6;--ok:#4f8f6b;--bad:#b05c4d;--acc:#3e6b8f}}
body{{margin:0;background:var(--bg);color:var(--ink);font:12px/1.5 "Segoe UI","Noto Sans TC",system-ui,sans-serif;padding:16px 22px}}
h1{{font-size:20px;margin:0 0 4px}} h2{{font-size:13px;margin:16px 0 6px;letter-spacing:.04em}}
.sub{{color:var(--mut);font-size:11px}} .card{{background:var(--paper);border:1px solid var(--line);border-radius:7px;padding:12px 14px;margin:10px 0}}
table{{border-collapse:collapse;width:100%;font-size:11.5px}} th{{text-align:left;font-size:10px;letter-spacing:.14em;color:var(--mut);border-bottom:1px solid var(--line);padding:4px 8px 4px 0}}
td{{border-bottom:1px solid #eef0ee;padding:4px 8px 4px 0;vertical-align:top}} .ok{{color:var(--ok);font-weight:700}} .bad{{color:var(--bad);font-weight:700}}
.mono{{font-family:Consolas,ui-monospace,monospace}} .wrap{{overflow-x:auto}} pre{{font-size:10.5px;white-space:pre-wrap;color:var(--mut)}}
.state{{display:inline-block;padding:2px 10px;border-radius:4px;border:1px solid var(--line);font-weight:700}}
</style></head><body>
<h1>故事族群輪動橋接 <span class="sub">STORY GROUP ROTATION BRIDGE · {html.escape(gap.get('package',''))} × VDF_ENG072</span></h1>
<div class="sub">產於 {gap['ts']} · 狀態 <span class="state {cls}">{html.escape(gap['state'])}</span> · {gap['elapsed_s']}s · 零 CDN 零外網 · 誠實三態</div>
{('<div class="card"><b>阻擋原因</b><pre>' + html.escape(gap.get('reason','')) + '</pre>' + ''.join('<div class="bad">▸ ' + html.escape(a_) + '</div>' for a_ in gap.get('attribution', [])) + '</div>') if gap.get('reason') else ''}
<div class="card"><h2>輸出輸入檔 EXPORTED INPUTS</h2><div class="wrap"><table><tr><th>檔 FILE</th><th>列 ROWS</th></tr>{frows}</table></div>
<div class="sub">標的 {st.get('tickers')} · 交易日 {st.get('days')} · 當沖覆蓋列 {st.get('daytrade_cover_rows')} · 法人覆蓋列 {st.get('inst_cover_rows')} · 融資融券覆蓋列 {st.get('margin_cover_rows')} · 市值覆蓋列 {st.get('marketcap_cover_rows')} · 候選 {html.escape(json.dumps(st.get('candidate_shape', {}), ensure_ascii=False))}</div></div>
<div class="card"><h2>預檢 PREFLIGHT-REAL</h2><div class="wrap"><table><tr><th>輸入 INPUT</th><th>角色 ROLE</th><th>狀態 STATUS</th></tr>{rows}</table></div></div>
<div class="card"><h2>缺口冊 GAP BOOK(誠實;補源後重跑即通)</h2><div class="wrap"><table><tr><th>ID</th><th>欄位 FIELD</th><th>缺口 GAP</th><th>補源 FIX</th></tr>{gaps}</table></div></div>
<div class="card"><h2>執行尾流 RUN TAIL</h2><pre>{html.escape(gap.get('run_tail','') or '(無)')}</pre>
<div class="sub">最新 run 目錄:{html.escape(gap.get('latest_run_dir','') or '(無)')}</div></div>
<div class="sub">VIA · VERITAS DATA FORGE · 包原件收容 intake/VIA_StoryGroupRotation_b325(零改動)· 每欄衍生律見引擎頭註</div>
</body></html>"""
    UI.parent.mkdir(parents=True, exist_ok=True)
    UI.write_text(page, encoding="utf-8")


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src = Path(__file__).read_text(encoding="utf-8")
    pk = pkg_root()
    man = INTAKE / "manifest.json"
    chk("① 包在位+收容 manifest(hash 冊)", pk is not None and man.exists()
        and len(json.loads(man.read_text(encoding="utf-8")).get("files", {})) >= 30)
    ex = export(do_print=False)
    need = {"trading_calendar", "universe_history", "full_market_daily", "membership_events", "candidate",
            "macro_vintages", "active_etf_holdings"}
    chk("② 七輸入檔全產出+契約必要欄", "err" not in ex and need <= set(ex["files"])
        and (INP / "full_market_daily.parquet").exists(), str({k: ex['files'][k] for k in ex['files']}))
    import pandas as pd
    fm = pd.read_parquet(INP / "full_market_daily.parquet", columns=["Date", "Ticker", "Adj_Close", "TurnoverValue",
                                                                    "DayTradeTurnover", "MarketCap",
                                                                    "MarketDataAvailableAt", "IsLimitUpLocked",
                                                                    "ForeignNetAmountAvailableAt"])
    chk("③ 衍生律誠實(市值全缺=不捏造;鎖定=未知非 False;AvailableAt 帶 +08:00)",
        fm["MarketCap"].isna().all() and fm["IsLimitUpLocked"].isna().all()
        and fm["MarketDataAvailableAt"].str.endswith("+08:00").all())
    pf = preflight(do_print=False)
    chk("④ preflight-real 六主線+候選 PASS(檔在位)", bool(pf["rows"])
        and all(not x.get("BlocksCorePipeline") for x in pf["rows"]), f"(rc={pf['rc']})")
    chk("⑤ 缺口冊七條+成分事件 PENDING(先驗證後核准)+包原件零觸碰",
        len(GAP_BOOK) == 7 and (INP / "membership_events.csv").read_text(encoding="utf-8").count("PENDING") >= 1
        and "cwd=str(pk)" in src and ("shu" + "til") not in src)
    render({"ts": "selftest", "package": pk.name if pk else "", "state": "SELFTEST", "reason": "", "elapsed_s": 0,
            "export": ex, "preflight": pf["rows"], "run_tail": "", "latest_run_dir": "",
            "gap_book": [{"id": g[0], "field": g[1], "gap": g[2], "fix": g[3]} for g in GAP_BOOK]})
    page = UI.read_text(encoding="utf-8")
    chk("⑥ 頁零 CDN+加速橋+誠實三態宣告", '<script src="http' not in page and "ACCEL-BRIDGE" in src and "誠實" in page)
    print(f"  [計] 六檢 OK {6 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 故事族群輪動橋接(VDF_ENG072)· 六檢自測(零外網)===")
        return selftest()
    if "--pkgtest" in a:
        return 0 if pkgtest()["rc"] == 0 else 1
    if "export" in a:
        return 0 if "err" not in export() else 2
    if "preflight" in a:
        return preflight()["rc"]
    return run()


if __name__ == "__main__":
    sys.exit(main())
