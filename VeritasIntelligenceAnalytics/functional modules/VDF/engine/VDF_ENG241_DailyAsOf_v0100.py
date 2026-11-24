#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG241_DailyAsOf v0100 — 低頻序列(週 / 月 / 不定期)轉日資料:as-of 向後取值,證據誠實。

VDF-REQ051(操作員 2026-11-23):「AAII 情緒 / CNN 恐懼貪婪 / MSCI 全球前 20 大與 FactSet 各指數 Forward PER · PBR
→ 轉換為日資料」。
規則:
- 不內插、不前視:每個營業日取「當日以前最近一次發布值」(merge_asof backward);
- 每列帶 source_date(值實際發布日)· stale_days · source_freq(由觀測間距中位數推:D / W / M / Q / IRR);
- 沿用上限 stale_cap = max(3, ceil(2.5 × 間距中位數)) 天,超過即值留空、status=STALE(照實,不硬撐);
- status:OBSERVED(當日有原值)· ASOF_FFILL(沿用)· STALE(超過上限)。
輸入:資料家的 gl__sentiment_daily / gl__index_valuation_proxy / gl__factset_earnings(可 --sources 增減)。
輸出:資料家 gl__valuation_sentiment_daily.parquet(ZSTD;暫存檔 + os.replace 原子替換;舊檔不刪,整檔重算可重現)。
只讀本機資料、零網路;不碰 TA-Lib、不碰 MOPS;資料家路徑由 VDF_DataPlane_SSOT 尾版 data_home 或 --home 決定。
用法:run [--home DIR] [--start 2018-01-01] [--end YYYY-MM-DD] [--sources a,b] [--dry] | --list | --selftest
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
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更;本支零網路,只掛橋) =====
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
# ===== [VIA:NET-BRIDGE:END] =====

import json
import math
import os
import re
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
VDF_DIR = HERE.parent
TAG = "VDF_ENG241_DailyAsOf v0100"
DEFAULT_START = "2018-01-01"
DEFAULT_SOURCES = ["gl__sentiment_daily", "gl__index_valuation_proxy", "gl__factset_earnings"]
OUT_NAME = "gl__valuation_sentiment_daily"
DATE_CANDIDATES = ("date", "as_of", "asof", "obs_date", "report_date", "trade_date", "Date", "日期")
DATE_RX = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


def data_home() -> Path | None:
    """VDF_DATA_HOME 環境變數 > DataPlane 尾版 data_home(依作業系統取對應鍵)。"""
    env = os.environ.get("VDF_DATA_HOME")
    if env:
        return Path(env)
    books = sorted(VDF_DIR.glob("VDF_DataPlane_SSOT_v*.json"), key=_vnum)
    if not books:
        return None
    dh = json.loads(books[-1].read_text(encoding="utf-8")).get("data_home") or {}
    key = "workstation" if os.name == "nt" else "container"
    p = dh.get(key) or (dh.get("workstation") if os.name == "nt" else None)
    return Path(p) if p else None


# ---------------------------------------------------------------- 轉換核心(純 pandas,可夾具自測)
def to_long(df, dataset: str):
    """寬表 → 長表(date, series_id, dataset, value)。日期欄取第一個命中者;非數值欄當鍵;數值欄當值。"""
    import pandas as pd
    dcol = next((c for c in DATE_CANDIDATES if c in df.columns), None)
    if dcol is None:
        raise ValueError(f"{dataset}: 找不到日期欄(候選 {DATE_CANDIDATES})")
    d = df.copy()
    d["_date"] = pd.to_datetime(d[dcol], errors="coerce").dt.normalize()
    d = d[d["_date"].notna()]
    num = [c for c in d.columns if c not in (dcol, "_date") and pd.api.types.is_numeric_dtype(d[c])]
    keys = [c for c in d.columns if c not in (dcol, "_date") and c not in num]
    if not num:
        return pd.DataFrame(columns=["date", "series_id", "dataset", "value"])
    long = d.melt(id_vars=["_date"] + keys, value_vars=num, var_name="_col", value_name="value")
    long = long[long["value"].notna()]
    parts = [long[k].astype(str).radd(f"{k}=") for k in keys] + [long["_col"].astype(str)]
    sid = pd.Series([dataset] * len(long), index=long.index).str.cat(parts, sep="|")
    out = pd.DataFrame({"date": long["_date"], "series_id": sid, "dataset": dataset, "value": long["value"].astype(float)})
    # 同日同序列多筆 → 取最後一筆(來源去重;不平均、不捏造)
    return out.sort_values(["series_id", "date"]).drop_duplicates(["series_id", "date"], keep="last")


def infer_freq(gap_days: float) -> str:
    if gap_days != gap_days:            # NaN:只有一筆
        return "IRR"
    for lab, lim in (("D", 3), ("W", 10), ("M", 40), ("Q", 120)):
        if gap_days <= lim:
            return lab
    return "IRR"


def expand_daily(long, start: str, end: str):
    """長表 → 營業日日資料(as-of backward;不前視;超過沿用上限標 STALE 並留空值)。"""
    import pandas as pd
    rows = []
    start_ts, end_ts = pd.Timestamp(start), pd.Timestamp(end)
    for sid, g in long.groupby("series_id", sort=True):
        g = g.sort_values("date")
        gaps = g["date"].diff().dt.days.dropna()
        med = float(gaps.median()) if len(gaps) else float("nan")
        cap = 3 if med != med else max(3, math.ceil(2.5 * med))
        first = max(g["date"].iloc[0], start_ts)
        if first > end_ts:
            continue
        cal = pd.DataFrame({"date": pd.bdate_range(first, end_ts)})
        src = g[["date", "value"]].rename(columns={"date": "source_date"})
        src["date"] = src["source_date"]
        m = pd.merge_asof(cal, src.sort_values("date"), on="date", direction="backward")
        m["stale_days"] = (m["date"] - m["source_date"]).dt.days
        m["status"] = "ASOF_FFILL"
        m.loc[m["stale_days"] == 0, "status"] = "OBSERVED"
        stale = m["stale_days"] > cap
        m.loc[stale, "status"] = "STALE"
        m.loc[stale, "value"] = float("nan")
        m["series_id"] = sid
        m["dataset"] = g["dataset"].iloc[0]
        m["source_freq"] = infer_freq(med)
        rows.append(m)
    cols = ["date", "series_id", "dataset", "value", "source_date", "stale_days", "source_freq", "status"]
    if not rows:
        return pd.DataFrame(columns=cols)
    return pd.concat(rows, ignore_index=True)[cols]


def write_parquet_atomic(df, path: Path) -> None:
    """ZSTD Parquet;寫暫存檔(.sdd_tmp)後 os.replace 原子替換。"""
    tmp = path.with_name(path.name + ".sdd_tmp")
    out = df.copy()
    for c in ("date", "source_date"):
        out[c] = out[c].dt.strftime("%Y-%m-%d")
    out.to_parquet(tmp, index=False, compression="zstd")
    os.replace(tmp, path)


# ---------------------------------------------------------------- 執行
def run(home: Path | None, start: str, end: str, sources: list[str], dry: bool) -> int:
    import pandas as pd
    if not (DATE_RX.match(start) and DATE_RX.match(end)):
        print(f"[FAIL] 日期格式錯:start={start} end={end}")
        return 2
    if home is None or not home.exists():
        print(f"[FAIL] 資料家不在:{home}(設 VDF_DATA_HOME 或 --home)")
        return 2
    longs, report = [], []
    for name in sources:
        p = home / f"{name}.parquet"
        if not p.exists():
            report.append((name, "MISSING", 0, 0))
            continue
        df = pd.read_parquet(p)
        lg = to_long(df, name)
        longs.append(lg)
        report.append((name, "OK", len(df), lg["series_id"].nunique()))
    for name, st, n, s in report:
        print(f"  [來源] {name:30} {st:8} 列 {n:>8} · 序列 {s}")
    if not longs:
        print("[FAIL] 沒有任何來源可轉")
        return 1
    daily = expand_daily(pd.concat(longs, ignore_index=True), start, end)
    by = daily.groupby("status").size().to_dict()
    print(f"  [日資料] {len(daily)} 列 · 序列 {daily['series_id'].nunique()} · {by} · "
          f"{daily['date'].min().date() if len(daily) else '-'} → {daily['date'].max().date() if len(daily) else '-'}")
    if dry:
        print("  [乾跑] 不寫檔")
        return 0
    out = home / f"{OUT_NAME}.parquet"
    write_parquet_atomic(daily, out)
    print(f"  [寫入] {out.name}(ZSTD · 原子替換)")
    return 0


def selftest() -> int:
    import pandas as pd
    ok = fail = skip = 0

    def chk(name, cond, note=""):
        nonlocal ok, fail
        ok += bool(cond)
        fail += not cond
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")

    weekly = pd.DataFrame({"date": ["2026-01-01", "2026-01-08", "2026-01-15"],
                           "index": ["AAII"] * 3, "bullish": [40.0, 35.0, 30.0]})
    monthly = pd.DataFrame({"as_of": ["2025-10-31", "2025-11-28"], "region": ["MSCI_ACWI"] * 2,
                            "fwd_pe": [18.0, 18.6], "pbr": [3.1, 3.2]})
    lg = pd.concat([to_long(weekly, "gl__sentiment_daily"), to_long(monthly, "gl__index_valuation_proxy")])
    chk("① 寬→長:鍵欄進序列名、數值欄各成序列", set(lg["series_id"]) == {
        "gl__sentiment_daily|index=AAII|bullish", "gl__index_valuation_proxy|region=MSCI_ACWI|fwd_pe",
        "gl__index_valuation_proxy|region=MSCI_ACWI|pbr"}, f"({lg['series_id'].nunique()} 序列)")
    d = expand_daily(lg, "2025-12-01", "2026-02-27")
    w = d[d["series_id"].str.endswith("bullish")].set_index("date")
    chk("② 週資料:發布日 OBSERVED、其後 ASOF_FFILL", w.loc["2026-01-08", "status"] == "OBSERVED"
        and w.loc["2026-01-09", "status"] == "ASOF_FFILL" and w.loc["2026-01-09", "value"] == 35.0)
    chk("③ 不前視:發布前一天仍是前值", w.loc["2026-01-07", "value"] == 40.0
        and str(w.loc["2026-01-07", "source_date"].date()) == "2026-01-01")
    chk("④ 推頻:週 → W、月 → M", w["source_freq"].iloc[0] == "W"
        and set(d[d["series_id"].str.contains("fwd_pe")]["source_freq"]) == {"M"})
    cap_w = max(3, math.ceil(2.5 * 7))
    late = w.loc["2026-02-27"]
    chk("⑤ 超過沿用上限 → STALE 且值留空", late["status"] == "STALE" and late["value"] != late["value"]
        and late["stale_days"] > cap_w, f"(上限 {cap_w} 天 · 第 {late['stale_days']} 天)")
    chk("⑥ 只有營業日", set(pd.to_datetime(d["date"]).dt.dayofweek) <= {0, 1, 2, 3, 4})
    chk("⑦ 起點不早於序列首發布日(不往前捏造)", w.index.min() == pd.Timestamp("2026-01-01"))
    d2 = expand_daily(lg, "2025-12-01", "2026-02-27")
    chk("⑧ 重算可重現(冪等)", d.equals(d2))
    dup = pd.DataFrame({"date": ["2026-01-01", "2026-01-01"], "index": ["AAII", "AAII"], "bullish": [1.0, 2.0]})
    chk("⑨ 同日同序列去重(取最後)", to_long(dup, "x")["value"].tolist() == [2.0])
    try:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            weekly.to_parquet(home / "gl__sentiment_daily.parquet", index=False)
            rc = run(home, "2025-12-01", "2026-01-31", DEFAULT_SOURCES, dry=False)
            out = pd.read_parquet(home / f"{OUT_NAME}.parquet")
            chk("⑩ 端到端:缺來源照列 MISSING、其餘照寫 ZSTD parquet、無暫存殘檔",
                rc == 0 and len(out) > 0 and not list(home.glob("*.sdd_tmp")), f"({len(out)} 列)")
    except ImportError:
        skip += 1
        print("  [SKIP] ⑩ 端到端需 pyarrow(本機缺件)→ 黃,工作站實跑")
    print(f"  [計] {TAG} 自測 OK {ok} · FAIL {fail} · SKIP {skip}")
    return 1 if fail else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        return selftest()

    def opt(k, default=None):
        return a[a.index(k) + 1] if k in a and a.index(k) + 1 < len(a) else default

    if "--list" in a:
        print(f"{TAG} · 來源 {DEFAULT_SOURCES} → {OUT_NAME}.parquet · 資料家 {data_home()}")
        return 0
    if a[:1] == ["run"]:
        home = Path(opt("--home")) if opt("--home") else data_home()
        srcs = opt("--sources")
        return run(home, opt("--start", DEFAULT_START), opt("--end", date.today().isoformat()),
                   srcs.split(",") if srcs else DEFAULT_SOURCES, "--dry" in a)
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
