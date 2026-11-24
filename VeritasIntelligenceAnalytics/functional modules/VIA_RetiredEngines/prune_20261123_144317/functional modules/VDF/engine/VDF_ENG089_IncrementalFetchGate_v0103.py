#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
VDF_ENG089_IncrementalFetchGate v0103 — 增量擷取閘(批569)
v0102→v0103(側線 2026-09-24 第六段;主線批號由併線的手指定 L25;操作員令「擷取資料前要先檢查資料庫缺啥 … VDF加速器跟網路工具都要導入並覆蓋深入所有指令細節動作」):
  `audit` 這把尺本身量不準——第五段實跑報「重抓風險 4」,逐支查:ENG058(產業冊)與 ENG072(故事輪動橋)**根本不出網**,
  只是帶著網路橋樣板碼(字樣裡有 SUP_MDL740)、說明文字裡有「擷取(」就被算進去;另兩支 ENG047 · ENG050 真的出網重抓,
  但**沒有任何啟動入口掛它們**(VIA 根目錄每一族 .ps1 尾版 + VDF_ENG093 啟動台都找不到)——跟有短令天天在跑的,不是同一種風險。
  ① 觸網改看**語法樹上真的呼叫**網路工具(車道方法 http_json / curl_json / curl_bytes / yf_history … 或取用 _via_net() / _net_or_none()),
     不再看字樣;帶橋不呼叫的另列 `bridge_only`(不出網)。
  ② 抓取型改看**識別字**(函式名 / 呼叫名含 fetch/backfill/download/抓取/回補/擷取),說明文字與註解不算;資料庫的 fetchall/fetchone… 排除。
  ③ **直連**另列(操作員令⑤:網路工具要覆蓋所有動作):yf.download / yf.Ticker / requests.get / urlopen / ["curl", …] 命令清單
     (兩個元素以上才算命令——單獨的 ["curl"] 是比較用的字面值;本支自測就有一個,第一版把自己量成直連,實跑抓到)。
  ④ 每支標**有沒有啟動入口掛著**(`wired`):重抓風險分「有入口(真的會跑)」與「休眠」。
  程式碼層代理指標的誠實話照舊寫在 note(不冒充行為證明)。自測 +㉑㉒(合成六檔正負控 · 實樹結構性質)。
v0101→v0102(側線 2026-09-24 第三段;主線批號由併線的手指定 L25;操作員令「請繼續完成用中文說明」· 掉球 Z162):
  plan 以前一律用「日」算缺口:月營收(ym=202301…202608)`_d()` 認不得 → 被丟進「無日期欄」;財報(tw_financial 最新 2026-06-30)
  照日算尾段 → 「缺 2026-07-01→今天 86 天」——Q3 財報 11/14 才到期,那不是缺,是還沒到期。狀況頁 VDF_ENG093 的缺口表就是讀這裡。
  v0102(期別讀正典 SUP_MDL753 v0107,本支不另寫清單):
  ① 冊上的月/季表(cadence_of)→ 尾段改看法定期限(period_lag):期限未到=不缺;過了=「下一期已過期限 N 日」。
     頭段缺口照算,起點用期初(月表月初、季表季初);另列 periods 一段給人看最新期與期限。
  ② 民國/緊湊日期(etf_book 1150824…)兩端先換 ISO 再照日算(以前一律「無日期欄」)。
  ③ --deep 逐日反連結:日期欄先認自己那份,認不到才用正典補位欄(寫入時間戳不補);月/季表不逐日比(報 PERIOD)。
  ④ 紀錄表判準讀冊 record_only(ts · snapshot_at · run_at),本支原份 ("ts",) 照舊在前。
  正典缺席=照 v0101 算(具名退路,out.period_canon 帶因由)。自測 +⑳。
v0100→v0101(側線 2026-09-23;主線批號由併線的手指定 L25;操作員「更新 VDF」):工作站 09-21 實錄——`via-vdffetch` 兩跑都回 OK、庫多了 499 列,
  `via-vdfinc plan` 前後兩次**一字不差**(tw_daily_prices 仍「已有 …→2026-09-14」)。根因不在引擎:本閘讀的是 MDL123 的**目錄快照**
  `DATAHOME_CATALOG_latest.json`,那份快照是抓之前做的,而 v0100 從來不說它看的是幾點的目錄。三件修在「怎麼講」,算法一字不動:
  ① **目錄新鮮度**:目錄時間 vs 目錄裡每一個庫檔的最後寫入時間;有庫比目錄新 → 態 STALE(rc 2,過期≠壞),第一行就說「先 via-datahome catalog」,
     計畫照算照印(那是目錄時間的真相),但不冒充現在。`catalog_freshness()` 是唯一出處,VDF_SystemManager launch 也委派它(LL316)。
  ② **紀錄表不算缺口**:日期欄是 `ts`、或最早/最晚帶了非零時刻的表(via_handover · via_policy_sync · vrn_extraction_logic 這類)是「某次寫入的時間戳」,
     不是資料覆蓋——另列 records,不進缺口(量的不是釘名單)。
  ③ **哨兵日不當真**:最早 = 1900-01-01 / 1970-01-01 / 0001-01-01 / 1899-12-30 這種預設日 → 另列 sentinel;頭段缺口算不出來就說算不出來
     (真最早要 --deep 或在庫裡查),最早最晚都是哨兵 = 等同空表。每一行帶庫名(同名表在三個庫各一份,不帶庫名看不出是哪一份)。
  自測 16 → 19(⑰ 紀錄表 · ⑱ 哨兵 · ⑲ 目錄新鮮度正負控)。零網路 · 零寫庫 · 無 --apply 照舊。

操作員令(批569):「VDF 自2023年後到最新的資料庫增量擷取,**不要重複 BATCH FETCHING**」。
同一句話操作員在批383 就說過一次:「抓過的資料不必再抓」。說第二次=**還在重抓**。

【這一批只做第一步:把真相攤開,零改線(L61)】
  不改任何現役擷取引擎的行為。本閘只回答三個問題,答完操作員才決定誰改:
    ① 庫裡**已經有什麼**(每張表的日期涵蓋)
    ② 從 2023-01-01 到最新,**真正缺的是哪幾段**(只列缺口,不列已有)
    ③ 哪幾支擷取引擎**抓之前沒看庫**(那就是重抓的來源)

【誠實四態】
  0=GREEN(算得出缺口,或本來就沒缺口)· 1=RED(壞了)
  · 2=NODATA(庫在但空/沒有日期欄,算不出水位——不是紅燈)
  · 3=ABSENT(目錄或庫不在;附上要先跑哪一句)

【紀律】
  · **零網路**:本閘一個位元組都不抓,只讀庫與目錄。
  · **零寫入**:不建表、不寫庫、不改任何擷取引擎。沒有 --apply。
  · **不代設同意閘**:要真的去抓是操作員的手。
  · **零九頭龍**:庫的清點**複用 CGC_MDL123 資料家 catalog**,本閘不自己再寫一份掃庫。

用法:
  via-vdfinc scan                     每張表的水位(列/日期欄/最早/最新)
  via-vdfinc plan  [--since 2023-01-01] [--until YYYY-MM-DD]
                                      只列缺口:頭段缺、尾段缺;有庫可讀時 --deep 逐日反連結
  via-vdfinc plan --deep              逐日反連結(真正的「不要重抓」清單;要庫讀得到)
  via-vdfinc audit                    哪幾支尾版擷取引擎抓之前沒看庫
  via-vdfinc --selftest
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
import argparse
import ast
import json
import os
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent.parent
VERSION = Path(__file__).stem.rsplit("_v", 1)[-1]
REPORTS = VIA / "VIA_Reports" / "vdf" / "incremental"
CATALOG = VIA / "VIA_Reports" / "datahome" / "DATAHOME_CATALOG_latest.json"
DEFAULT_SINCE = "2023-01-01"        # 操作員令:自 2023 年後
ENGINE_DIR = VIA / "functional modules" / "VDF" / "engine"

# 抓網的正典口(L:網路只認 AegisNexus,740 留作橋)
NET_MARKS = ("SUP_MDL740", "AegisNexus", "NetUnified", "net_unified")
# 「抓之前有看庫」的證據:水位查詢 / 反連結 / checkpoint
WATERMARK_MARKS = (
    r"max\s*\(\s*[\"'`]?\w*date", r"MAX\s*\(", r"watermark", r"高水位", r"last_date",
    r"checkpoint", r"anti[-_]?join", r"NOT\s+IN\s*\(\s*SELECT", r"LEFT\s+JOIN[\s\S]{0,120}IS\s+NULL",
    r"已在庫", r"existing_dates", r"have_dates",
)
_WM_RX = re.compile("|".join(WATERMARK_MARKS), re.I)
# v0101:哨兵日——資料不可能真的從這幾天開始,出現在「最早」就是預設值/空值被寫進日期欄(工作站 tw_daily_prices / global_daily 實錄 1900-01-01)
SENTINEL_DATES = ("1900-01-01", "1970-01-01", "0001-01-01", "1899-12-30")
# v0101:紀錄表的日期欄——MDL123 _DATE_COLS 裡只有 ts 是「寫入時間戳」而不是資料日
RECORD_DATE_COLS = ("ts",)
STALE_TOLERANCE_S = 120
_CANON: dict = {}


def _canon():
    """v0102:期別正典(SUP_MDL753 尾版經 VIA_LibCanon;要 cadence_of / period_bounds / roc_to_iso)。缺席=None,因由在 _CANON['why']。"""
    if not _CANON:
        try:
            sup = str(VIA / "supportive modules")
            if sup not in sys.path:
                sys.path.insert(0, sup)
            import VIA_LibCanon as _lib
            u = _lib.UTILS
            for fn in ("cadence_of", "period_bounds", "period_lag", "roc_to_iso", "fallback_date_columns"):
                if not hasattr(u, fn):
                    raise AttributeError(f"{_lib.CANONICAL.get('utils', '')} 無 {fn}(要 v0107+)")
            u.load_period_rules()
            _CANON.update(u=u, why="OK:" + _lib.CANONICAL.get("utils", ""))
        except Exception as exc:
            _CANON.update(u=None, why=f"ABSENT:{type(exc).__name__}:{str(exc)[:80]}")
    return _CANON["u"]


def _record_cols() -> tuple:
    """紀錄表日期欄:本支原份在前,冊上 record_only 補在後(只增)。正典缺席=原份。"""
    u = _canon()
    extra = tuple(u.load_period_rules()["date_columns"].get("record_only") or ()) if u is not None else ()
    return RECORD_DATE_COLS + tuple(c for c in extra if c not in RECORD_DATE_COLS)        # 目錄寫完到庫檔 mtime 的正常時差(同一跑內 checkpoint 收尾);超過才算庫比目錄新


# ────────────────────────── 小工具 ──────────────────────────
def _d(s) -> date | None:
    s = str(s or "").strip()[:10]
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None


def _json(p: Path):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:
        return None


def tails(dirpath: Path, pat: str = "VDF_ENG*_v*.py") -> dict:
    out = {}
    for p in sorted(dirpath.glob(pat)):
        fam = p.stem.rsplit("_v", 1)[0]
        if fam not in out or p.stem > out[fam].stem:
            out[fam] = p
    return out


# ────────────────────────── v0101:目錄新鮮度 · 紀錄表 · 哨兵 ──────────────────────────
def _ts(s) -> datetime | None:
    s = str(s or "").strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y%m%d_%H%M%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s[:19] if "%H" in fmt else s[:10], fmt)
        except Exception:
            continue
    return None


def catalog_freshness(cat: dict | None = None, now: datetime | None = None) -> dict:
    """目錄時間 vs 目錄裡每個庫檔的最後寫入時間。**唯一出處**(VDF_SystemManager launch 委派這一支)。
    FRESH=沒有庫比目錄新 · STALE=有庫在目錄之後被寫過(計畫講的是舊庫)· UNKNOWN=目錄沒時間或庫檔都不在(量不到不猜)。"""
    cat = _json(CATALOG) if cat is None else cat
    now = now or datetime.now()
    if not cat:
        return {"state": "ABSENT", "why": f"{CATALOG.name} 不在(via-datahome catalog)", "catalog": str(CATALOG)}
    ct = _ts(cat.get("ts") or cat.get("updated_at"))
    out = {"catalog_ts": str(cat.get("ts") or cat.get("updated_at") or ""), "age_h": (round((now - ct).total_seconds() / 3600.0, 1) if ct else None),
           "dbs": [], "newer": []}
    for ent in (cat.get("dbs") or cat.get("entries") or []):
        p = Path(str(ent.get("path") or ""))
        if not str(ent.get("path") or "") or not p.is_file():
            continue
        mt = datetime.fromtimestamp(p.stat().st_mtime)
        row = {"db": ent.get("name") or p.name, "mtime": mt.strftime("%Y-%m-%d %H:%M:%S")}
        out["dbs"].append(row)
        if ct and (mt - ct).total_seconds() > STALE_TOLERANCE_S:
            out["newer"].append({**row, "lag_min": int((mt - ct).total_seconds() // 60)})
    if ct is None or not out["dbs"]:
        out["state"], out["why"] = "UNKNOWN", ("目錄沒有時間戳" if ct is None else "目錄裡的庫檔在本機都找不到(換了機器或路徑?)")
    elif out["newer"]:
        w = max(out["newer"], key=lambda r: r["lag_min"])
        out["state"] = "STALE"
        out["why"] = (f"目錄 {out['catalog_ts']} 之後 {len(out['newer'])} 個庫被寫過(最晚 {w['db']} {w['mtime']},晚 {w['lag_min']} 分鐘)"
                      "——計畫講的是目錄那一刻的庫;先 `via-datahome catalog` 再 plan")
    else:
        out["state"], out["why"] = "FRESH", f"目錄 {out['catalog_ts']} 之後沒有庫被寫過({len(out['dbs'])} 庫)"
    return out


def is_record_table(r: dict) -> bool:
    """紀錄表:日期欄是寫入時間戳(ts),或最早/最晚帶非零時刻——那是「某次寫入的時間」,不是資料覆蓋。"""
    if str(r.get("date_col") or "").lower() in _record_cols():       # v0102:冊上 record_only 也算
        return True
    for k in ("lo", "hi"):
        v = str(r.get(k) or "")
        if len(v) > 10 and v[10:].strip() not in ("", "00:00:00", "T00:00:00", "00:00:00.000000"):
            return True
    return False


def sentinel_kind(r: dict) -> str:
    """''=正常 · 'lo'=最早是哨兵(真最早未知)· 'only'=最早最晚都是哨兵(等同空表)。"""
    lo, hi = str(r.get("lo") or "")[:10], str(r.get("hi") or "")[:10]
    if lo in SENTINEL_DATES:
        return "only" if hi in SENTINEL_DATES else "lo"
    return ""


# ────────────────────────── ① scan:庫裡已經有什麼 ──────────────────────────
def scan() -> dict:
    cat = _json(CATALOG)
    if not cat:
        return {"state": "ABSENT",
                "why": f"資料家目錄不在:{CATALOG.name} → 先跑 `via-datahome catalog`(唯讀清點,不觸網)",
                "catalog": str(CATALOG)}
    rows = []
    for ent in (cat.get("dbs") or cat.get("entries") or []):
        for t in (ent.get("tables") or []):
            rows.append({"db": ent.get("name") or ent.get("path", ""), "table": t.get("table", ""),
                         "rows": t.get("rows", -1), "date_col": t.get("date_col", ""),
                         "lo": t.get("lo", ""), "hi": t.get("hi", ""), "err": t.get("err", "")})
    if not rows:
        # 目錄在但沒有表:誠實 NODATA,不編
        by = cat.get("by_table") or {}
        rows = [{"db": v.get("db", ""), "table": k, "rows": -1, "date_col": "", "lo": "", "hi": "",
                 "err": "目錄只記了表名,沒有列數/日期範圍"} for k, v in by.items()]
    dated = [r for r in rows if r.get("date_col") and _d(r.get("lo"))]
    return {"state": "OK" if dated else ("NODATA" if rows else "ABSENT"),
            "why": "" if dated else "目錄裡沒有任何帶日期欄且有列的表(庫空或還沒 catalog)",
            "n_tables": len(rows), "n_dated": len(dated), "tables": rows,
            "catalog_ts": cat.get("ts") or cat.get("updated_at", "")}


# ────────────────────────── ② plan:只列缺口 ──────────────────────────
def plan(since: str = DEFAULT_SINCE, until: str = "", deep: bool = False) -> dict:
    s = _d(since) or _d(DEFAULT_SINCE)
    u = _d(until) or date.today()
    sc = scan()
    if sc["state"] in ("ABSENT", "NODATA"):
        return {**sc, "since": str(s), "until": str(u)}
    gaps, covered, nodate, records, sentinels, periods = [], [], [], [], [], []
    u_ = _canon()
    for r in sc["tables"]:
        lo, hi = _d(r.get("lo")), _d(r.get("hi"))
        cad = u_.cadence_of(r["table"], db=str(r.get("db") or "")) if (u_ is not None and r.get("date_col")) else None
        if cad and r.get("lo") and r.get("hi"):          # v0102 ①:冊上的月/季表——尾段看法定期限,不逐日算
            pl = u_.period_lag(r["table"], r.get("hi"), db=str(r.get("db") or ""), today=u)
            if pl["state"] == "PERIOD_DUE":
                b0 = u_.period_bounds(r.get("lo"))
                start = _d(b0[0]) if b0 else None
                if start and pl.get("period") == "quarter":
                    start = date(start.year, 3 * ((start.month - 1) // 3) + 1, 1)        # 季表頭段從季初算
                miss, days = [], 0
                if start and start > s:
                    miss.append(f"{s}→{start - timedelta(days=1)}")
                    days += (start - s).days
                if (pl.get("lag_days") or 0) > 0:
                    miss.append(f"下一期已過期限 {pl['due']}(逾 {pl['lag_days']} 日)")
                    days += int(pl["lag_days"])
                periods.append({"db": r["db"], "table": r["table"], "have": f"{r['lo']}→{r['hi']}", "rule": pl["rule"],
                                "period": pl["period"], "latest": pl["iso"], "due": pl["due"], "lag_days": pl["lag_days"]})
                if miss:
                    gaps.append({"db": r["db"], "table": r["table"], "have": f"{r['lo']}→{r['hi']}", "rows": r["rows"],
                                 "missing": miss, "missing_days": days, "sentinel": "", "period": pl["period"], "due": pl["due"]})
                else:
                    covered.append({"table": r["table"], "have": f"{r['lo']}→{r['hi']}", "rows": r["rows"], "period": pl["period"], "due": pl["due"]})
                continue
        if u_ is not None and r.get("date_col") and (lo is None or hi is None):   # v0102 ②:民國/緊湊日期兩端先換 ISO
            lo = lo or _d(u_.roc_to_iso(r.get("lo")))
            hi = hi or _d(u_.roc_to_iso(r.get("hi")))
        if not r.get("date_col") or lo is None or hi is None:
            nodate.append(r["table"])
            continue
        if is_record_table(r):          # v0101:寫入時間戳≠資料覆蓋
            records.append({"db": r["db"], "table": r["table"], "date_col": r.get("date_col"), "have": f"{r['lo']}→{r['hi']}", "rows": r["rows"]})
            continue
        sk = sentinel_kind(r)
        if sk:
            sentinels.append({"db": r["db"], "table": r["table"], "kind": sk, "have": f"{r['lo']}→{r['hi']}", "rows": r["rows"],
                              "why": ("最早最晚都是哨兵日=等同空表" if sk == "only" else "最早是哨兵日=真最早未知(頭段缺口不算;--deep 或庫裡查)")})
            if sk == "only":
                lo = hi = None
        if lo is None and hi is None:   # 只有哨兵列:整段都缺
            gaps.append({"db": r["db"], "table": r["table"], "have": f"{r['lo']}→{r['hi']}", "rows": r["rows"], "sentinel": "only",
                         "missing": [f"{s}→{u}"], "missing_days": (u - s).days + 1})
            continue
        head = (str(s), str(min(lo - timedelta(days=1), u))) if (lo > s and not sk) else None
        tail = (str(max(hi + timedelta(days=1), s)), str(u)) if hi < u else None
        wins = [w for w in (head, tail) if w and _d(w[0]) <= _d(w[1])]
        if wins:
            gaps.append({"db": r["db"], "table": r["table"], "have": f"{r['lo']}→{r['hi']}",
                         "rows": r["rows"], "missing": [f"{a}→{b}" for a, b in wins], "sentinel": sk,
                         "missing_days": sum((_d(b) - _d(a)).days + 1 for a, b in wins)})
        else:
            covered.append({"table": r["table"], "have": f"{r['lo']}→{r['hi']}", "rows": r["rows"]})
    fr = catalog_freshness()
    out = {"state": "STALE" if fr.get("state") == "STALE" else "OK", "since": str(s), "until": str(u),
           "n_tables": sc["n_tables"], "n_gap": len(gaps), "n_covered": len(covered),
           "gaps": gaps, "covered": covered, "no_date_col": nodate, "periods": periods, "period_canon": _CANON.get("why", ""),
           "records": records, "sentinels": sentinels, "catalog": fr, "catalog_ts": sc.get("catalog_ts", ""),
           "note": ("目錄只看得到最早/最新兩點,**中間的洞看不到**;要真正的逐日缺口用 --deep"
                    if not deep else "")}
    if deep:
        out["deep"] = deep_gaps(s, u)
        out["note"] = "逐日反連結:列出的日期是庫裡**真的沒有**的,照這份抓就不會重抓"
    return out


def _db_paths() -> list:
    cat = _json(CATALOG) or {}
    ps = []
    for ent in (cat.get("dbs") or cat.get("entries") or []):
        p = ent.get("path")
        if p and str(p).endswith(".duckdb"):
            ps.append(Path(p))
    return ps


def deep_gaps(s: date, u: date) -> dict:
    """逐日反連結:庫裡 distinct 日期 vs [s,u] 的差集。庫讀不到就誠實說,不猜。"""
    try:
        import duckdb  # noqa
    except Exception:
        return {"state": "ABSENT", "why": "本境沒有 duckdb 模組(不代裝;在工作站跑)"}
    res = {"state": "OK", "tables": []}
    for db in _db_paths():
        if not db.exists():
            res["tables"].append({"db": str(db), "state": "ABSENT", "why": "庫檔不在"})
            continue
        con = None
        try:
            import duckdb
            con = duckdb.connect(str(db), read_only=True)   # 唯讀:零寫入
            u_ = _canon()
            own = ("date", "obs_date", "trade_date", "dt", "ts", "datadate")
            fb = tuple(u_.fallback_date_columns(own)) if u_ is not None else ()
            for (t,) in con.execute("SELECT table_name FROM information_schema.tables").fetchall():
                cols = [r[1] for r in con.execute(f'PRAGMA table_info("{t}")').fetchall()]
                dc = next((c for c in cols if str(c).lower() in own), "") or next((c for c in cols if str(c).lower() in fb), "")
                if not dc:
                    continue
                if u_ is not None and u_.cadence_of(t, db=db.name):          # v0102 ③:月/季表不逐日比
                    res["tables"].append({"db": db.name, "table": t, "date_col": dc, "state": "PERIOD",
                                          "why": "月/季表不逐日比;缺期看 plan 的 periods(法定期限)"})
                    continue
                have = {str(r[0])[:10] for r in con.execute(
                    f'SELECT DISTINCT "{dc}" FROM "{t}" WHERE "{dc}" >= ? AND "{dc}" <= ?',
                    [str(s), str(u)]).fetchall()}
                want, d = [], s
                while d <= u:
                    if d.weekday() < 5 and str(d) not in have:   # 週末不算缺(非交易日)
                        want.append(str(d))
                    d += timedelta(days=1)
                res["tables"].append({"db": db.name, "table": t, "date_col": dc,
                                      "have_days": len(have), "missing_days": len(want),
                                      "missing_head": want[:10], "missing_tail": want[-10:]})
        except Exception as exc:
            res["tables"].append({"db": str(db), "state": "FAIL",
                                  "why": f"{type(exc).__name__}: {exc}"})   # L62:不截斷
        finally:
            if con is not None:
                try:
                    con.close()
                except Exception:
                    pass
    return res


# ────────────────────────── ③ audit:誰抓之前沒看庫 ──────────────────────────
def _calls_net(tree, src: str) -> bool:
    return any(m in src for m in NET_MARKS)


#: v0103:觸網看「真的呼叫」——統包車道方法名與取用函式名(v0102 只看字樣,帶橋不呼叫的也算)
NET_LANE_ATTRS = frozenset({"http_json", "http_bytes", "http_text", "curl_json", "curl_bytes", "post_json", "yf_history",
                            "yahoo_chart", "yahoo_quote_summary", "yahoo_quote_summary_raw"})
NET_GETTERS = frozenset({"_via_net", "_net_or_none"})
#: v0103:直連(不經統包網路工具;操作員令⑤)
DIRECT_ATTRS = frozenset({("yf", "download"), ("yfinance", "download"), ("yf", "Ticker"), ("yfinance", "Ticker"),
                          ("requests", "get"), ("requests", "post"), ("request", "urlopen"), ("urllib", "urlopen")})
DIRECT_NAMES = frozenset({"urlopen"})
_FETCH_RX = re.compile(r"(fetch|backfill|download|crawl|scrape|抓取|回補|擷取)", re.I)
_DB_FETCH = frozenset({"fetchall", "fetchone", "fetchmany", "fetchdf", "fetch_df", "fetchnumpy", "fetch_arrow_table",
                       "fetch_record_batch", "fetch_df_chunk"})


def code_facts(src: str) -> dict:
    """v0103:語法樹上的事實(不讀說明文字、不讀註解):真的呼叫統包幾次、直連哪幾種、抓取型識別字有哪些。"""
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        return {"parse_ok": False, "net_calls": 0, "direct": [], "fetch_names": [], "why": f"語法樹讀不出來 line {exc.lineno}"}
    net_calls, direct, names = 0, set(), set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and _FETCH_RX.search(node.name):
            names.add(node.name)
        elif (isinstance(node, ast.List) and len(node.elts) >= 2 and isinstance(node.elts[0], ast.Constant)
              and node.elts[0].value == "curl"):                       # 帶參數的命令才算;單獨 ["curl"] 是比較用的字面值
            direct.add("curl")
        elif isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Name):
                if f.id in NET_GETTERS or f.id in NET_LANE_ATTRS:
                    net_calls += 1
                elif f.id in DIRECT_NAMES:
                    direct.add(f.id)
                if _FETCH_RX.search(f.id) and f.id not in _DB_FETCH:
                    names.add(f.id)
            elif isinstance(f, ast.Attribute):
                if f.attr in NET_LANE_ATTRS:
                    net_calls += 1
                base = f.value.id if isinstance(f.value, ast.Name) else (f.value.attr if isinstance(f.value, ast.Attribute) else "")
                if (base, f.attr) in DIRECT_ATTRS:
                    direct.add(f"{base}.{f.attr}")
                if _FETCH_RX.search(f.attr) and f.attr not in _DB_FETCH:
                    names.add(f.attr)
    return {"parse_ok": True, "net_calls": net_calls, "direct": sorted(direct), "fetch_names": sorted(names)}


def launch_surfaces(via: Path | None = None) -> dict:
    """v0103:操作員實際的啟動入口 = VIA 根目錄每一族 .ps1 的尾版 + VDF_ENG093 啟動台尾版 → {檔名: 全文}。"""
    via = via or VIA
    fam: dict = {}
    for p in via.glob("*.ps1"):
        m = re.match(r"(.+?)[-_]v(\d+)\.ps1$", p.name)
        k, v = (m.group(1), int(m.group(2))) if m else (p.stem, -1)
        if k not in fam or v > fam[k][0]:
            fam[k] = (v, p)
    out = {p.name: p.read_text(encoding="utf-8", errors="ignore") for _, p in fam.values()}
    lc = sorted((via / "functional modules" / "VDF").glob("VDF_ENG093_LaunchConsole_v*.py"))
    if lc:
        out[lc[-1].name] = lc[-1].read_text(encoding="utf-8", errors="ignore")
    return out


def audit(engine_dir: Path | None = None, surfaces: dict | None = None) -> dict:
    """靜態稽核:尾版 VDF 引擎裡,**真的出網**的那些,抓之前有沒有看庫。

    誠實話:這是**程式碼層的代理指標**,不是行為證明。它只能說「這支檔裡找不到看庫的痕跡」,
    不能說「它一定重抓」。真憑實據是 plan --deep 在工作站跑出來的逐日缺口。
    v0103:觸網/抓取看語法樹(不看字樣與說明文字);直連另列;每支標有沒有啟動入口掛著(wired)。
    """
    surf = launch_surfaces() if surfaces is None else surfaces
    rows, bridge_only = [], []
    for fam, p in sorted(tails(engine_dir or ENGINE_DIR).items()):
        src = p.read_text(encoding="utf-8", errors="ignore")
        fx = code_facts(src)
        eng = fam.replace("VDF_", "")
        if not (fx["net_calls"] or fx["direct"]):
            if _calls_net(None, src):
                bridge_only.append(eng)          # 帶網路橋樣板、一次都沒呼叫=不出網(v0102 會算進來)
            continue
        wm = bool(_WM_RX.search(src))
        fetchy = bool(fx["fetch_names"])
        rows.append({"engine": eng, "version": p.stem.rsplit("_v", 1)[1], "watermark": wm, "fetchy": fetchy,
                     "parse_ok": fx["parse_ok"], "net_calls": fx["net_calls"], "direct": fx["direct"],
                     "wired": sorted(k for k, t in surf.items() if fam in t),
                     "risk": ("重抓風險" if (fetchy and not wm) else ("看庫" if wm else "非擷取"))})
    risky = [r for r in rows if r["risk"] == "重抓風險"]
    return {"state": "OK", "n_net": len(rows), "n_watermark": sum(1 for r in rows if r["watermark"]),
            "n_risky": len(risky), "n_risky_live": sum(1 for r in risky if r["wired"]), "risky": risky,
            "direct": [r for r in rows if r["direct"]], "bridge_only": sorted(bridge_only), "rows": rows,
            "n_surfaces": len(surf),
            "note": "程式碼層代理指標:只說『找不到看庫的痕跡』,不等於『一定重抓』。真憑實據看 plan --deep"}


def write_out(name: str, payload: dict) -> Path:
    REPORTS.mkdir(parents=True, exist_ok=True)
    p = REPORTS / name
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    return p


# ────────────────────────── 自測 ──────────────────────────
def selftest() -> int:
    import tempfile
    n, fails = [0], []

    def chk(name, ok, note=""):
        n[0] += 1
        if not ok:
            fails.append(name)
        print(f"  [{'OK' if ok else 'FAIL'}] {name}" + (f" ({note})" if note else ""))

    print(f"=== VDF_ENG089 增量擷取閘 v{VERSION} · 自測(零網路;零寫庫) ===")
    code = Path(__file__).read_text(encoding="utf-8").split("def selftest", 1)[0]
    chk("① 零網路(不 import requests/httpx/urllib;不呼叫任何抓取)",
        not any(k in code for k in ("import requests", "import httpx", "import urllib",
                                    "urlopen(", "\n    fetch(")))
    chk("② 零寫庫(連線一律 read_only;無 CREATE/INSERT/UPDATE/DELETE)",
        "read_only=True" in code and not re.search(r"\b(CREATE|INSERT|UPDATE|DELETE)\s+", code))
    chk("③ 沒有 --apply(本閘只算缺口,不代抓)", '"--apply"' not in code and "'--apply'" not in code)
    chk("④ 零九頭龍:庫清點複用 MDL123 資料家 catalog,不自己再寫一份掃庫",
        "DATAHOME_CATALOG_latest.json" in code)

    g = globals()
    sc0 = scan()
    chk("⑤ 目錄不在=誠實 ABSENT 且講得出要先跑哪一句(不是空表假綠)",
        sc0["state"] in ("ABSENT", "NODATA", "OK")
        and (sc0["state"] != "ABSENT" or "via-datahome catalog" in sc0.get("why", "")),
        f"{sc0['state']} · {sc0.get('why','')[:60]}")

    # 合成目錄:一張頭缺、一張尾缺、一張全覆蓋、一張沒有日期欄
    with tempfile.TemporaryDirectory() as td:
        fake = Path(td) / "DATAHOME_CATALOG_latest.json"
        fake.write_text(json.dumps({"ts": "2026-09-17", "dbs": [{"name": "t.duckdb", "path": str(Path(td) / "t.duckdb"), "tables": [
            # 夾具寫法要「純」:hi 必須等於 until,否則它同時有頭缺**和**一天尾缺,
            # 斷言就會為了錯的理由紅(第一版我把 hi 寫成 2026-09-16,自己被自己的夾具騙了一次)。
            {"table": "head_gap", "rows": 10, "date_col": "date", "lo": "2024-01-01", "hi": "2026-09-17"},
            {"table": "tail_gap", "rows": 10, "date_col": "date", "lo": "2023-01-01", "hi": "2025-06-30"},
            {"table": "full", "rows": 10, "date_col": "date", "lo": "2022-12-01", "hi": "2026-09-17"},
            {"table": "both_gap", "rows": 10, "date_col": "date", "lo": "2024-01-01", "hi": "2026-09-16"},
            {"table": "nodate", "rows": 10, "date_col": "", "lo": "", "hi": ""}]}]},
            ensure_ascii=False), encoding="utf-8")
        old = g["CATALOG"]
        g["CATALOG"] = fake
        try:
            sc = scan()
            chk("⑥ scan 讀得出五張表,帶日期欄的算四張", sc["state"] == "OK" and sc["n_tables"] == 5 and sc["n_dated"] == 4,
                f"表 {sc['n_tables']} · 帶日期 {sc['n_dated']}")
            pl = plan("2023-01-01", "2026-09-17")
            byt = {x["table"]: x for x in pl["gaps"]}
            chk("⑦ plan 只列缺口:頭缺算頭段、尾缺算尾段、頭尾都缺列兩段、全覆蓋的不列",
                set(byt) == {"head_gap", "tail_gap", "both_gap"}
                and byt["head_gap"]["missing"] == ["2023-01-01→2023-12-31"]
                and byt["tail_gap"]["missing"] == ["2025-07-01→2026-09-17"]
                and byt["both_gap"]["missing"] == ["2023-01-01→2023-12-31", "2026-09-17→2026-09-17"]
                and [c["table"] for c in pl["covered"]] == ["full"],
                f"缺 {pl['n_gap']} · 覆蓋 {pl['n_covered']} · 無日期欄 {pl['no_date_col']}")
            chk("⑧ 缺口天數算得對(純頭缺 2023 整年=365;頭尾都缺=365+1=366)",
                byt["head_gap"]["missing_days"] == 365 and byt["both_gap"]["missing_days"] == 366,
                f"頭 {byt['head_gap']['missing_days']} · 頭尾 {byt['both_gap']['missing_days']}")
            chk("⑨ 沒有日期欄的表誠實列在 no_date_col,不當成「沒缺」",
                pl["no_date_col"] == ["nodate"])
            chk("⑩ 不 --deep 時明說『中間的洞看不到』(不假裝這份是完整答案)",
                "中間的洞看不到" in pl["note"])
        finally:
            g["CATALOG"] = old

    # 真庫逐日反連結
    with tempfile.TemporaryDirectory() as td2:
        try:
            import duckdb
            dbp = Path(td2) / "x.duckdb"
            con = duckdb.connect(str(dbp))
            con.execute("CREATE TABLE px(date DATE, v INT)")
            con.execute("INSERT INTO px VALUES ('2026-09-14',1),('2026-09-15',1),('2026-09-17',1)")
            con.close()
            fake2 = Path(td2) / "DATAHOME_CATALOG_latest.json"
            fake2.write_text(json.dumps({"dbs": [{"name": "x.duckdb", "path": str(dbp), "tables": [
                {"table": "px", "rows": 3, "date_col": "date", "lo": "2026-09-14", "hi": "2026-09-17"}]}]},
                ensure_ascii=False), encoding="utf-8")
            old = g["CATALOG"]
            g["CATALOG"] = fake2
            try:
                dg = deep_gaps(date(2026, 9, 14), date(2026, 9, 17))
                t0 = dg["tables"][0]
                chk("⑪ --deep 逐日反連結:2026-09-16(週三)在庫裡沒有→列為缺;週末不算缺",
                    dg["state"] == "OK" and t0["missing_days"] == 1
                    and t0["missing_head"] == ["2026-09-16"],
                    f"有 {t0['have_days']} 天 · 缺 {t0['missing_days']} 天 {t0['missing_head']}")
                before = dbp.stat().st_mtime
                deep_gaps(date(2026, 9, 14), date(2026, 9, 17))
                chk("⑫ --deep 唯讀:跑完庫檔 mtime 不變(不是看旗標,是真的比)",
                    dbp.stat().st_mtime == before)
            finally:
                g["CATALOG"] = old
        except ImportError:
            chk("⑪ --deep 需要 duckdb:本境沒有=誠實跳過(不代裝、不假綠)", True, "duckdb 缺席")
            chk("⑫ --deep 唯讀:同上誠實跳過", True, "duckdb 缺席")

    a = audit()
    chk("⑬ audit 掃得到真的出網的尾版引擎", a["state"] == "OK" and a["n_net"] >= 10,
        f"觸網尾版 {a['n_net']} · 有看庫 {a['n_watermark']} · 重抓風險 {a['n_risky']}")
    chk("⑭ audit 明講自己只是程式碼層代理指標(不冒充行為證明)",
        "代理指標" in a["note"] and "不等於" in a["note"])
    chk("⑮ 預設起日照操作員令 2023-01-01", DEFAULT_SINCE == "2023-01-01")
    chk("⑯ 帶加速器橋(MDL156 覆蓋閘)", "[VIA:ACCEL-BRIDGE" in Path(__file__).read_text(encoding="utf-8"))

    # v0101:紀錄表 · 哨兵 · 目錄新鮮度(正負控;全在暫存)
    with tempfile.TemporaryDirectory() as td3:
        fake3 = Path(td3) / "DATAHOME_CATALOG_latest.json"
        dbf = Path(td3) / "tw.duckdb"
        dbf.write_bytes(b"x")
        mt = datetime.fromtimestamp(dbf.stat().st_mtime)
        tabs = [{"table": "via_handover", "rows": 3, "date_col": "ts", "lo": "2026-09-16 03:56:08", "hi": "2026-09-16 03:56:08"},
                {"table": "run_log", "rows": 3, "date_col": "date", "lo": "2026-09-14 17:03:02", "hi": "2026-09-15 15:21:15"},
                {"table": "tw_daily_prices", "rows": 9, "date_col": "date", "lo": "1900-01-01", "hi": "2026-09-14"},
                {"table": "global_daily", "rows": 1, "date_col": "date", "lo": "1900-01-01", "hi": "1900-01-01"},
                {"table": "px", "rows": 9, "date_col": "date", "lo": "2023-01-01 00:00:00", "hi": "2026-09-14 00:00:00"}]
        old = g["CATALOG"]
        g["CATALOG"] = fake3
        try:
            fake3.write_text(json.dumps({"ts": (mt - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"),
                                         "dbs": [{"name": "tw.duckdb", "path": str(dbf), "tables": tabs}]}), encoding="utf-8")
            p3 = plan("2023-01-01", "2026-09-21")
            g3 = {x["table"]: x for x in p3["gaps"]}
            chk("⑰ 紀錄表不算缺口:日期欄 ts、或最早最晚帶非零時刻的表另列 records;午夜時刻的正常表照算",
                {x["table"] for x in p3["records"]} == {"via_handover", "run_log"} and "via_handover" not in g3 and "run_log" not in g3
                and g3.get("px", {}).get("missing") == ["2026-09-15→2026-09-21"],
                f"紀錄表 {[x['table'] for x in p3['records']]} · px 缺 {g3.get('px', {}).get('missing')}")
            chk("⑱ 哨兵日不當真:最早=1900 不算頭段缺口只算尾段並標 lo;最早最晚都是 1900=只有哨兵列=整段缺",
                g3["tw_daily_prices"]["missing"] == ["2026-09-15→2026-09-21"] and g3["tw_daily_prices"]["sentinel"] == "lo"
                and g3["global_daily"]["sentinel"] == "only" and g3["global_daily"]["missing"] == ["2023-01-01→2026-09-21"]
                and {x["table"]: x["kind"] for x in p3["sentinels"]} == {"tw_daily_prices": "lo", "global_daily": "only"},
                f"{[(x['table'], x['kind']) for x in p3['sentinels']]}")
            stale = p3["catalog"]
            fake3.write_text(json.dumps({"ts": (mt + timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S"),
                                         "dbs": [{"name": "tw.duckdb", "path": str(dbf), "tables": tabs}]}), encoding="utf-8")
            fresh = catalog_freshness()
            fake3.write_text(json.dumps({"ts": "", "dbs": [{"name": "gone.duckdb", "path": str(Path(td3) / "gone.duckdb"), "tables": tabs}]}), encoding="utf-8")
            unk = catalog_freshness()
            chk("⑲ 目錄新鮮度:庫比目錄晚寫 2 小時 → STALE(plan 態 STALE、rc 2、說得出晚多久與先跑哪句)· 目錄比庫新 → FRESH · 目錄沒時間/庫檔不在 → UNKNOWN 不猜",
                stale["state"] == "STALE" and p3["state"] == "STALE" and stale["newer"][0]["lag_min"] >= 119 and "via-datahome catalog" in stale["why"]
                and fresh["state"] == "FRESH" and unk["state"] == "UNKNOWN",
                f"{stale['state']} 晚 {stale['newer'][0]['lag_min'] if stale.get('newer') else '-'} 分 · {fresh['state']} · {unk['state']}")
        finally:
            g["CATALOG"] = old

    # ── v0102 ⑳:月/季表看法定期限、民國日期換 ISO、紀錄表讀冊(負控:正典缺席=照 v0101)──
    with tempfile.TemporaryDirectory() as td20:
        fake20 = Path(td20) / "cat.json"
        tabs20 = [{"table": "tw_monthly_revenue", "rows": 9, "date_col": "ym", "lo": "202301", "hi": "202608"},
                  {"table": "tw_financial", "rows": 9, "date_col": "date", "lo": "2025-03-31", "hi": "2026-06-30"},
                  {"table": "etf_book", "rows": 9, "date_col": "as_of", "lo": "1150824", "hi": "2026-09-12"},
                  {"table": "tw_daily_prices", "rows": 9, "date_col": "date", "lo": "2023-01-02", "hi": "2026-09-23"},
                  {"table": "snap_t", "rows": 9, "date_col": "snapshot_at", "lo": "2026-09-01", "hi": "2026-09-20"}]
        fake20.write_text(json.dumps({"ts": "", "dbs": [{"name": "tw.duckdb", "path": str(Path(td20) / "tw.duckdb"), "tables": tabs20}]}), encoding="utf-8")
        old20 = g["CATALOG"]
        g["CATALOG"] = fake20
        try:
            p20 = plan("2023-01-01", "2026-09-24")
            saved20 = dict(_CANON)
            _CANON.clear()
            _CANON.update(u=None, why="ABSENT:selftest")
            p20b = plan("2023-01-01", "2026-09-24")
            _CANON.clear()
            _CANON.update(saved20)
        finally:
            g["CATALOG"] = old20
    gm = {x["table"]: x for x in p20["gaps"]}
    cv = {x["table"] for x in p20["covered"]}
    pe = {x["table"]: x for x in p20["periods"]}
    gb = {x["table"]: x for x in p20b["gaps"]}
    chk("⑳ v0102 月/季表看法定期限:月營收 202301…202608 期限 10/10 未到=不缺;財報 2025-03-31…2026-06-30 頭段從 2025 Q1 季初算"
        "(2023-01-01→2024-12-31)、尾段 Q3 期限 11/14 未到=不報 86 天;etf_book 民國 1150824 換 ISO 照日算(頭段到 2026-08-23、尾段 2026-09-13→24);"
        "snapshot_at 表算紀錄表;**負控**:正典缺席=照 v0101(月營收進無日期欄、財報尾段報 86 天、etf_book 無日期欄)",
        "tw_monthly_revenue" in cv and pe.get("tw_monthly_revenue", {}).get("due") == "2026-10-10"
        and gm.get("tw_financial", {}).get("missing") == ["2023-01-01→2024-12-31"] and pe.get("tw_financial", {}).get("due") == "2026-11-14"
        and gm.get("etf_book", {}).get("missing") == ["2023-01-01→2026-08-23", "2026-09-13→2026-09-24"] and "snap_t" in {x["table"] for x in p20["records"]}
        and p20["period_canon"].startswith("OK:")
        and "tw_monthly_revenue" in p20b["no_date_col"] and (gb.get("tw_financial", {}).get("missing") or [""])[-1] == "2026-07-01→2026-09-24"
        and "etf_book" in p20b["no_date_col"],
        f"正典 缺 {[(k, v['missing']) for k, v in gm.items()]} · 期別 {[(k, v['due']) for k, v in pe.items()]} · 負控 財報 {gb.get('tw_financial', {}).get('missing')}")

    # v0103 ㉑:合成六檔正負控(暫存引擎夾 + 假啟動入口;零網路)
    _e24 = ""
    try:
        with tempfile.TemporaryDirectory() as td24:
            ed = Path(td24)
            bridge = "# SUP_MDL740 NetUnified 統包網路工具橋\ndef _via_net():\n    return None\n"
            (ed / "VDF_ENG901_BridgeOnly_v0100.py").write_text(
                '"""說明文字:擷取(每日)回補(三年)"""\n' + bridge + "def build(con):\n    return con.execute('x').fetchall()\n", encoding="utf-8")
            (ed / "VDF_ENG902_LiveRefetch_v0100.py").write_text(
                bridge + "def fetch_day(net, d):\n    return net.http_json(d)\n"
                "def run(net):\n    for d in range(3):\n        fetch_day(net, d)\n", encoding="utf-8")
            (ed / "VDF_ENG903_Watermarked_v0100.py").write_text(
                bridge + "CKPT = 'checkpoint.json'\ndef backfill(net):\n    return net.curl_json('u')\n", encoding="utf-8")
            (ed / "VDF_ENG904_Direct_v0100.py").write_text(
                "import yfinance as yf\ndef download_all(t):\n    return yf.download(t)\n", encoding="utf-8")
            (ed / "VDF_ENG905_Dormant_v0100.py").write_text(
                "def fetch_all(net):\n    return _via_net().http_json('u')\n", encoding="utf-8")
            (ed / "VDF_ENG907_CurlDirect_v0100.py").write_text(
                "import subprocess\ndef fetch_page(u):\n    return subprocess.run([\"curl\", \"-sS\", u])\n", encoding="utf-8")
            (ed / "VDF_ENG908_GetterOnly_v0100.py").write_text(         # 用的車道不在清單上:只有「取用 _via_net()」這個訊號
                "def pull(u):\n    n = _via_net()\n    return n.stream(u)\n", encoding="utf-8")
            (ed / "VDF_ENG909_CurlLiteral_v0100.py").write_text(       # 負控:比較用的 ["curl"] 字面值不是命令
                "def check(net, xs):\n    net.http_json('u')\n    return xs == [\"curl\"]\n", encoding="utf-8")
            (ed / "VDF_ENG906_DbOnly_v0100.py").write_text(
                "def summarize(net, con):\n    net.http_json('u')\n    return con.execute('x').fetchone()\n", encoding="utf-8")
            a24 = audit(ed, {"Register-VIA-Commands-v0999.ps1": "VDF_ENG902_LiveRefetch_v*.py VDF_ENG904_Direct"})
            by = {r["engine"]: r for r in a24["rows"]}
    except Exception as exc:
        _e24, a24, by = f"{type(exc).__name__}: {str(exc)[:90]}", {}, {}
    chk("㉑ v0103 audit 看語法樹不看字樣:只帶網路橋、說明文字寫「擷取(」的不算出網(列 bridge_only);真呼叫 http_json 又逐日抓、沒看庫=重抓風險且標出掛它的啟動入口;"
        "有 checkpoint=看庫;yf.download 與自己開 curl 子行程=直連(沒看庫也照樣算重抓風險);沒有任何入口掛它=休眠;資料庫 fetchone 不算抓取",
        not _e24 and a24.get("bridge_only") == ["ENG901_BridgeOnly"] and "ENG901_BridgeOnly" not in by
        and by.get("ENG902_LiveRefetch", {}).get("risk") == "重抓風險"
        and by["ENG902_LiveRefetch"]["wired"] == ["Register-VIA-Commands-v0999.ps1"]
        and by.get("ENG903_Watermarked", {}).get("risk") == "看庫"
        and by.get("ENG904_Direct", {}).get("direct") == ["yf.download"] and by["ENG904_Direct"]["wired"]
        and by["ENG904_Direct"]["risk"] == "重抓風險"                    # 直連又沒看庫,照樣是重抓風險
        and by.get("ENG905_Dormant", {}).get("risk") == "重抓風險" and by["ENG905_Dormant"]["wired"] == []
        and by.get("ENG906_DbOnly", {}).get("risk") == "非擷取"
        and by.get("ENG907_CurlDirect", {}).get("direct") == ["curl"] and by["ENG907_CurlDirect"]["wired"] == []
        and by.get("ENG908_GetterOnly", {}).get("net_calls") == 1 and by["ENG908_GetterOnly"]["risk"] == "非擷取"
        and by.get("ENG909_CurlLiteral", {}).get("direct") == []
        and a24.get("n_risky") == 4 and a24.get("n_risky_live") == 2,
        f"({_e24 or 'ok'} · 風險 {[(r['engine'], r['wired']) for r in a24.get('risky', [])]} · 只帶橋 {a24.get('bridge_only')})")
    # v0103 ㉒:實樹結構性質(不寫死哪幾支——別的線修好了,這一檢不該因此紅)
    a25 = audit()
    _rows25 = a25["rows"]
    chk("㉒ v0103 實樹:每一支列進來的都真的呼叫統包或直連;只帶網路橋的不在列內;啟動入口讀得到(VIA 根目錄 .ps1 尾版 + ENG093);"
        "重抓風險逐支標了有沒有入口",
        a25["state"] == "OK" and all(r["net_calls"] or r["direct"] for r in _rows25)
        and not ({r["engine"] for r in _rows25} & set(a25["bridge_only"])) and a25["n_surfaces"] >= 5
        and all(isinstance(r["wired"], list) for r in a25["risky"]),
        f"真出網 {a25['n_net']} · 重抓風險 {a25['n_risky']}(有入口 {a25['n_risky_live']})· 直連 {len(a25['direct'])} · 只帶橋 {len(a25['bridge_only'])} · 入口 {a25['n_surfaces']}")

    # LL112:分子分母同一個計數來源
    print(f"  [計] {n[0]} 檢 OK {n[0] - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="VDF_ENG089_IncrementalFetchGate", description="增量擷取閘(零網路;零寫庫)")
    ap.add_argument("verb", nargs="?", default="scan", choices=["scan", "plan", "audit"])
    ap.add_argument("--since", default=DEFAULT_SINCE)
    ap.add_argument("--until", default="")
    ap.add_argument("--deep", action="store_true", help="逐日反連結(要庫讀得到)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    r = {"scan": scan, "plan": (lambda: plan(a.since, a.until, a.deep)), "audit": audit}[a.verb]()
    p = write_out(f"VDFINC_{a.verb.upper()}_{ts}.json", r)
    write_out(f"VDFINC_{a.verb.upper()}_latest.json", r)
    if a.json:
        print(json.dumps(r, ensure_ascii=False))
    else:
        print(f"[VDF_ENG089 v{VERSION}] {a.verb} · {r.get('state')}")
        if a.verb == "plan" and r.get("state") in ("OK", "STALE"):
            fr = r.get("catalog") or {}
            print(f"  目錄 {fr.get('catalog_ts') or '?'}({fr.get('age_h')} h 前)· {fr.get('state')}:{fr.get('why', '')}")
            if r.get("state") == "STALE":
                print("  [過期] 下面是**目錄那一刻**的庫,不是現在的庫——先跑 `via-datahome catalog`,再 `via-vdfinc plan`")
            print(f"  區間 {r['since']} → {r['until']} · 表 {r['n_tables']} · 有缺 {r['n_gap']} · 已覆蓋 {r['n_covered']} · 紀錄表 {len(r.get('records') or [])} · 哨兵 {len(r.get('sentinels') or [])}")
            for gp in r["gaps"][:30]:
                tag = {"lo": " [最早=哨兵]", "only": " [只有哨兵列]"}.get(gp.get("sentinel") or "", "")
                print(f"   [缺] {Path(str(gp['db'])).name[:24]:<24} {gp['table']:<26} 已有 {gp['have']:<24} 缺 {' · '.join(gp['missing'])}({gp['missing_days']} 天){tag}")
            for rr in (r.get("records") or [])[:12]:
                print(f"   [紀錄表] {Path(str(rr['db'])).name[:24]:<24} {rr['table']:<26} {rr['have']}(日期欄 {rr['date_col']}=寫入時間戳,不算資料缺口)")
            for pe in (r.get("periods") or [])[:12]:
                print(f"   [期別] {Path(str(pe['db'])).name[:24]:<24} {pe['table']:<26} 已有 {pe['have']:<24} 最新期 {pe['latest']} · 下一期期限 {pe['due']}"
                      + (f" · 逾 {pe['lag_days']} 日" if pe.get("lag_days") else " · 未到期"))
            for sn in (r.get("sentinels") or [])[:12]:
                print(f"   [哨兵] {Path(str(sn['db'])).name[:24]:<24} {sn['table']:<26} {sn['have']}:{sn['why']}")
            if r.get("no_date_col"):
                print(f"   [無日期欄] {r['no_date_col']}")
            if r.get("note"):
                print(f"   註:{r['note']}")
        elif a.verb == "audit":
            print(f"  真出網尾版 {r['n_net']} · 有看庫 {r['n_watermark']} · **重抓風險 {r['n_risky']}**(有啟動入口 {r['n_risky_live']})"
                  f" · 直連 {len(r['direct'])} · 只帶網路橋不出網 {len(r['bridge_only'])} · 啟動入口 {r['n_surfaces']} 支")
            for x in r["risky"]:
                where = "、".join(x["wired"][:3]) if x["wired"] else "**休眠**:沒有任何啟動入口掛它"
                print(f"   [重抓風險] {x['engine']} v{x['version']} · {where}")
            for x in r["direct"]:
                print(f"   [直連] {x['engine']} v{x['version']} · {', '.join(x['direct'])}(不經統包網路工具)")
            if r["bridge_only"]:
                print(f"   [只帶網路橋] {', '.join(r['bridge_only'])}(樣板碼在、一次都沒呼叫=不出網)")
            print(f"   註:{r['note']}")
        else:
            for k in ("n_tables", "n_dated", "why", "catalog_ts"):
                if r.get(k) not in (None, ""):
                    print(f"  {k:>12} : {r[k]}")
        print(f"  存證 {p.name}")
    return {"OK": 0, "NODATA": 2, "STALE": 2, "ABSENT": 3}.get(r.get("state"), 1)


if __name__ == "__main__":
    sys.exit(main())
