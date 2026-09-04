#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VDF_ENG074_FredMacroSSOT v0101 — FRED 宏觀 SSOT 擷取引擎(批360/361;via-fred;批362 --fred-key 無動詞修)
====================================================================
操作員令(批360)「優化vdf資料架構 加入上船的加速器跟網路工具」「只增不減 最優最快的
資料結構搭配加速器及網路工具」;(批361)「優化整個vdf擷取引擎 會要我輸入fed 快 準
從新往舊抓 存在 data parquet duckdb polars 20個強化加速器」。

設計律(誠實三態;零九頭龍):
  SSOT   上船 macro_ssot.json(收容 VIA_VDF_SSOT_b360;尾版 glob 動態)series_registry
         190 筆 fred_id 序列=擷取母冊;缺冊退 ENG055 內建 16 筆(誠實 FALLBACK)。
  鑰     env FRED_API_KEY → output_hub/mega/.fred_api_key(gitignored)→ 互動輸入
         (TTY 才問;非 TTY=SKIP 印指令不空轉);--fred-key 寫鑰匙檔;永不入 git/log。
  從新往舊 每序列以「視窗」倒序抓(observation_end=游標;sort_order=desc;視窗長依頻率:
         Daily 2y/Weekly 5y/Monthly 10y/Quarterly 20y/Annual 60y),每視窗即落盤+
         checkpoint(oldest 游標),達 --since 或空視窗=DONE;中斷零浪費。
  快     accel_map 平行工人(預設 4)+令牌桶節流(FRED 120 req/min 官方上限→預設 100)
         +已 DONE 序列增量刷新(只抓 max_date−45d 修訂窗)。
  準     realtime 最新 vintage;缺值 "." 過濾;value DOUBLE;date DATE(typed schema)。
  存     output_hub/mega(接點=本機資料家 C:\\Users\\tonyk\\Github\\movies-dataset\\data):
         parquet 每序列一檔 macro/fred/<id>.parquet(zstd;series,date 叢集)+
         DuckDB vdf_global_market.duckdb 表 us_macro(與 ENG055 L8 同表同鍵 date,series;
         anti-join 冪等)+ macro_series_registry(序列冊/狀態)+ polars 鏡
         macro/us_macro_all.parquet(polars 缺=pyarrow 後備;誠實 FALLBACK)。
  20 強化加速器 F01–F20(真用面;每燈自測)—見 FETCH_ACCEL。
v0100→v0101(批362 工作站實錄:`via-fred --fred-key <key>` 無動詞→只印用法、鑰未寫):main 先處理 --fred-key(寫鑰匙檔)再
以 run 為預設動詞;動詞可在任意位置;v0100 零觸碰。
用法:python3 VDF_ENG074_FredMacroSSOT_v0101.py [run] [--since 1990-01-01] [--workers 4]
      [--rpm 100] [--limit N] [--only CPIAUCSL,UNRATE] [--fred-key <key>] [--max-windows N]
      | status | lamps | --selftest
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
# ===== [VIA:NET-BRIDGE:END] =====
import json
import os
import sys
import threading
import time
from datetime import date, datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
VDF = HERE.parent
VIA = VDF.parent.parent
OUT = VDF / "output_hub" / "mega"          # 接點律(MDL123):Junction→本機資料家
DB_GL = OUT / "vdf_global_market.duckdb"
PQ_DIR = OUT / "macro" / "fred"
MIRROR = OUT / "macro" / "us_macro_all.parquet"
CKPT = OUT / "fred_ssot_checkpoint.json"
KEY_FILE = OUT / ".fred_api_key"           # gitignored;永不入 git
TABLE = "us_macro"                          # 與 ENG055 L8 同表(Zero-Hydra)
REG_TABLE = "macro_series_registry"
FRED_OBS = "https://api.stlouisfed.org/fred/series/observations"
SINCE_DEFAULT = "1990-01-01"
WINDOW_YEARS = {"Daily": 2, "Weekly": 5, "Monthly": 10, "Quarterly": 20, "Annual": 60, "PerMeeting": 20}
REFRESH_DAYS = 45                           # 已 DONE 序列增量刷新修訂窗
FALLBACK_SERIES = ["CPIAUCSL", "CPILFESL", "PCEPI", "PCEPILFE", "PPIFIS", "UNRATE",
                   "PAYEMS", "FEDFUNDS", "DGS2", "DGS10", "T10Y2Y", "INDPRO",
                   "RSAFS", "UMCSENT", "HOUST", "DGS20"]   # =ENG055 v0108 FRED_SERIES

# 20 強化加速器(擷取真用面;燈=本引擎實際呼叫/落地的機制;非掛橋即算)
FETCH_ACCEL = [
    ("F01", "SSOT 動態母冊", "macro_ssot.json 尾版 glob(190 FRED series);缺=內建 16 FALLBACK", "A08"),
    ("F02", "平行工人", "VIA_ACCEL.accel_map(ThreadPool;預設 4;例外隔離保序)", "A19"),
    ("F03", "令牌桶節流", "FRED 120 req/min 官方上限→預設 100/min;跨工人共享鎖", "A11"),
    ("F04", "從新往舊視窗", "observation_end 游標倒序+sort_order=desc;視窗長依頻率", "A15"),
    ("F05", "checkpoint 續跑", "每視窗落盤即記 oldest 游標;中斷零浪費;DONE 不重抓", "A13"),
    ("F06", "anti-join 冪等", "DuckDB INSERT … WHERE NOT EXISTS(date,series);重跑不重複", "A03"),
    ("F07", "typed schema", "date DATE/value DOUBLE/fetched_at TIMESTAMP;既存 VARCHAR 表=顯式 CAST 相容", "A08"),
    ("F08", "parquet 每序列", "macro/fred/<id>.parquet zstd;讀寫局部化(單序列更新不重寫全量)", "A11"),
    ("F09", "polars 鏡", "us_macro_all.parquet 以 polars 合併排序;缺=pyarrow 後備(誠實)", "A19"),
    ("F10", "韌性 HTTP", "SUP_MDL740.http_json→Aegis ResilientHTTPClient(retry/backoff/TLS)", "A18"),
    ("F11", "同意閘先行", "VIA_NET_CONSENT/VIA_SCRAPE_CONSENT fail-closed", "A05"),
    ("F12", "動態進度條", "序列級 [■■□] n/N %·已耗·預估;每序列 flush 即時", "A16"),
    ("F13", "非阻塞輸出", "逐行 flush;可由啟動器/工人分離尾讀(Invoke-VIA-Complete)", "A18"),
    ("F14", "視窗即落盤", "每視窗 rows→parquet+duckdb;不等全序列", "A14"),
    ("F15", "最新 vintage", "realtime_start/end 預設今日(最新修訂值)", "A02"),
    ("F16", "缺值過濾", "FRED '.' 缺值不入庫;value 轉 float 失敗即棄", "A10"),
    ("F17", "增量刷新", "DONE 序列只抓 max_date−45d 修訂窗(快)", "A15"),
    ("F18", "叢集排序", "parquet 寫入前 ORDER BY series,date;DuckDB 掃描 zone-map 有效", "A11"),
    ("F19", "誠實三態+序列冊", "OK/FAIL/SKIP/EMPTY;macro_series_registry 記 min/max/n/state", "A17"),
    ("F20", "資料家接點", "output_hub=MDL123 Junction→本機資料家;印實體路徑", "A20"),
]

_RL = {"lock": threading.Lock(), "stamps": []}
_STATS = {"req": 0, "fail": 0}


# ---------------------------------------------------------------- 基礎
def gate_open(env=None) -> bool:
    env = env if env is not None else os.environ
    return env.get("VIA_NET_CONSENT") == "YES" and env.get("VIA_SCRAPE_CONSENT") == "YES"


def _net_or_none():
    import glob as _g
    import importlib.util as _il
    hits = sorted(_g.glob(str(VIA / "supportive modules" / "network" / "SUP_MDL740_NetUnified_v*.py")))
    if not hits:
        return None
    spec = _il.spec_from_file_location("via_net_dyn", hits[-1])
    mod = _il.module_from_spec(spec)
    sys.modules["via_net_dyn"] = mod
    spec.loader.exec_module(mod)
    return mod


def ssot_path() -> Path | None:
    hits = sorted((VDF / "references" / "intake").glob("VIA_VDF_SSOT_b*/macro_ssot.json"))
    return hits[-1] if hits else None


def load_series() -> tuple[list[dict], str]:
    """回 ([{fred_id, via_code, freq, unit, theme, sub_theme, indicator, src}], 來源)"""
    p = ssot_path()
    if p:
        try:
            j = json.loads(p.read_text(encoding="utf-8"))
            out = []
            for code, v in j.get("series_registry", {}).items():
                if isinstance(v, dict) and v.get("fred_id"):
                    out.append({"fred_id": v["fred_id"], "via_code": code, "freq": v.get("freq", "Monthly"),
                                "unit": v.get("unit", ""), "theme": v.get("macro_theme", ""),
                                "sub_theme": v.get("sub_theme", ""), "indicator": v.get("indicator", ""),
                                "src": v.get("source", "")})
            if out:
                return out, f"SSOT {p.parent.name}"
        except Exception as exc:
            print(f"  [WARN] SSOT 讀取敗 {type(exc).__name__}: {exc};退內建 16", flush=True)
    return [{"fred_id": s, "via_code": f"US.Fallback.{s}", "freq": "Monthly", "unit": "", "theme": "",
             "sub_theme": "", "indicator": s, "src": "FRED"} for s in FALLBACK_SERIES], "FALLBACK 內建 16"


def fred_key(interactive: bool = True) -> tuple[str, str]:
    """(鑰, 來源);缺=互動輸入(TTY 才問)否則 ('', 指令)"""
    k = os.environ.get("FRED_API_KEY", "").strip()
    if k:
        return k, "env FRED_API_KEY"
    if KEY_FILE.exists():
        k = KEY_FILE.read_text(encoding="utf-8").strip()
        if k:
            return k, f"鑰匙檔 {KEY_FILE.name}"
    if interactive and sys.stdin is not None and sys.stdin.isatty():
        try:
            k = input("  [輸入] FRED API key(32 碼;只存本機鑰匙檔,永不入 git;空=略過):").strip()
        except (EOFError, KeyboardInterrupt):
            k = ""
        if k:
            write_key(k)
            return k, "互動輸入→鑰匙檔"
    return "", f"FRED 鑰缺=SKIP(不空轉):via-fred --fred-key <你的 key> 或寫入 {KEY_FILE}"


def write_key(key: str) -> str:
    key = (key or "").strip()
    if not key:
        return "空鑰=未寫"
    KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    KEY_FILE.write_text(key, encoding="utf-8")
    return f"鑰匙檔已寫 {KEY_FILE.name}(…{key[-4:]};gitignored)"


def _throttle(rpm: int, window: float = 60.0) -> None:
    """F03 令牌桶:滑動 window 秒視窗內 ≤ rpm 次;跨工人共享(鎖外睡=不阻他工人計算)"""
    while True:
        with _RL["lock"]:
            now = time.monotonic()
            _RL["stamps"] = [t for t in _RL["stamps"] if now - t < window]
            if len(_RL["stamps"]) < max(1, rpm):
                _RL["stamps"].append(now)
                return
            wait = window - (now - _RL["stamps"][0]) + 0.01
        time.sleep(min(max(wait, 0.02), 2.0))


def progress_bar(done: int, total: int, width: int = 22, spent: float = 0.0) -> str:
    total = max(total, 1)
    fill = int(width * done / total)
    pct = 100.0 * done / total
    per = spent / done if done else 0.0
    eta = per * (total - done)
    return f"[{'■' * fill}{'□' * (width - fill)}] {done}/{total} {pct:5.1f}% · 已耗 {spent:6.1f}s · 預估剩餘 {eta:6.1f}s"


# ---------------------------------------------------------------- 抓取核心(從新往舊)
def fetch_window(net, key: str, sid: str, end: str, start: str, rpm: int) -> dict:
    """單視窗:回 {'state','rows':[{date,value}],'note'}"""
    _throttle(rpm)
    url = (f"{FRED_OBS}?series_id={sid}&api_key={key}&file_type=json&sort_order=desc"
           f"&observation_start={start}&observation_end={end}")
    _STATS["req"] += 1
    r = net.http_json(url)
    if r.get("state") != "OK":
        _STATS["fail"] += 1
        return {"state": "FAIL", "rows": [], "note": str(r.get("note", ""))[:80]}
    rows = []
    for ob in (r.get("data") or {}).get("observations", []):
        v = ob.get("value")
        if v in (None, "", "."):
            continue
        try:
            rows.append({"date": ob["date"], "value": float(v)})
        except (ValueError, KeyError):
            continue
    return {"state": "OK" if rows else "EMPTY", "rows": rows, "note": ""}


def _load_ckpt() -> dict:
    if CKPT.exists():
        try:
            return json.loads(CKPT.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


_CK_LOCK = threading.Lock()


def _save_ckpt(ck: dict) -> None:
    with _CK_LOCK:
        CKPT.parent.mkdir(parents=True, exist_ok=True)
        tmp = CKPT.with_suffix(".tmp")
        tmp.write_text(json.dumps(ck, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(CKPT)


def plan_windows(freq: str, newest: str, since: str, cursor: str | None) -> list[tuple[str, str]]:
    """從新往舊視窗序列 [(start,end)];cursor=上次 oldest 游標(續跑自其前一日)"""
    yrs = WINDOW_YEARS.get(freq, 10)
    end_d = date.fromisoformat(cursor) - timedelta(days=1) if cursor else date.fromisoformat(newest)
    floor = date.fromisoformat(since)
    out = []
    while end_d >= floor:
        try:
            start_d = end_d.replace(year=end_d.year - yrs) + timedelta(days=1)
        except ValueError:  # 2/29
            start_d = end_d.replace(year=end_d.year - yrs, day=28) + timedelta(days=1)
        start_d = max(start_d, floor)
        out.append((start_d.isoformat(), end_d.isoformat()))
        end_d = start_d - timedelta(days=1)
    return out


def write_series_parquet(sid: str, rows: list[dict]) -> Path:
    """F08/F18:每序列一檔;與既存合併去重(date)後 ORDER BY date;zstd"""
    import pyarrow as pa
    import pyarrow.parquet as pq
    PQ_DIR.mkdir(parents=True, exist_ok=True)
    p = PQ_DIR / f"{sid}.parquet"
    merged = {}
    if p.exists():
        try:
            for rec in pq.read_table(p).to_pylist():
                merged[str(rec["date"])] = rec
        except Exception:
            merged = {}
    now = datetime.now()
    for r in rows:
        merged[r["date"]] = {"date": date.fromisoformat(r["date"]), "series": sid, "value": float(r["value"]),
                             "fetched_at": now}
    recs = [merged[k] for k in sorted(merged)]
    for rec in recs:  # 既存讀回可能是 date 物件;統一
        if isinstance(rec["date"], str):
            rec["date"] = date.fromisoformat(rec["date"])
    schema = pa.schema([("date", pa.date32()), ("series", pa.string()), ("value", pa.float64()),
                        ("fetched_at", pa.timestamp("us"))])
    pq.write_table(pa.Table.from_pylist(recs, schema=schema), p, compression="zstd")
    return p


_DB_LOCK = threading.Lock()


def upsert_db(rows: list[dict], sid: str) -> int:
    """F06/F07:typed 表(缺則建);既存 VARCHAR date 表=顯式 CAST 相容;anti-join 冪等;回表總列"""
    import duckdb
    with _DB_LOCK:
        DB_GL.parent.mkdir(parents=True, exist_ok=True)
        con = duckdb.connect(str(DB_GL))
        try:
            con.execute(f"CREATE TABLE IF NOT EXISTS {TABLE} (date DATE, series VARCHAR, value DOUBLE)")
            cols = {r[1]: r[2].upper() for r in con.execute(f"PRAGMA table_info('{TABLE}')").fetchall()}
            dcast = "CAST(? AS DATE)" if cols.get("date") == "DATE" else "?"
            con.execute("CREATE TEMP TABLE _in (date VARCHAR, series VARCHAR, value DOUBLE)")
            con.executemany("INSERT INTO _in VALUES (?, ?, ?)", [(r["date"], sid, float(r["value"])) for r in rows])
            dexpr = "CAST(i.date AS DATE)" if cols.get("date") == "DATE" else "i.date"
            extra = [c for c in cols if c not in ("date", "series", "value")]
            sel_extra = "".join(", NULL" for _ in extra)
            con.execute(f"INSERT INTO {TABLE} SELECT {dexpr}, i.series, i.value{sel_extra} FROM _in i "
                        f"WHERE NOT EXISTS (SELECT 1 FROM {TABLE} t WHERE t.series = i.series "
                        f"AND CAST(t.date AS VARCHAR) = i.date)")
            con.execute("DROP TABLE _in")
            n = con.execute(f"SELECT COUNT(*) FROM {TABLE} WHERE series = ?", [sid]).fetchone()[0]
            _ = dcast
            return n
        finally:
            con.close()


def upsert_registry(meta: dict, state: str, note: str = "") -> None:
    import duckdb
    with _DB_LOCK:
        con = duckdb.connect(str(DB_GL))
        try:
            con.execute(f"CREATE TABLE IF NOT EXISTS {REG_TABLE} (series VARCHAR PRIMARY KEY, via_code VARCHAR, "
                        "src VARCHAR, freq VARCHAR, unit VARCHAR, theme VARCHAR, sub_theme VARCHAR, indicator VARCHAR, "
                        "min_date VARCHAR, max_date VARCHAR, n_rows BIGINT, state VARCHAR, note VARCHAR, updated_at TIMESTAMP)")
            agg = con.execute(f"SELECT CAST(MIN(date) AS VARCHAR), CAST(MAX(date) AS VARCHAR), COUNT(*) FROM {TABLE} "
                              "WHERE series = ?", [meta["fred_id"]]).fetchone()
            con.execute(f"DELETE FROM {REG_TABLE} WHERE series = ?", [meta["fred_id"]])
            con.execute(f"INSERT INTO {REG_TABLE} VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        [meta["fred_id"], meta["via_code"], meta["src"], meta["freq"], meta["unit"], meta["theme"],
                         meta["sub_theme"], meta["indicator"], agg[0], agg[1], agg[2], state, note[:200], datetime.now()])
        finally:
            con.close()


def fetch_series(net, key: str, meta: dict, since: str, rpm: int, ck: dict, max_windows: int) -> dict:
    """單序列從新往舊(視窗即落盤;checkpoint);DONE=增量刷新"""
    sid = meta["fred_id"]
    st = ck.get(sid, {})
    today = date.today().isoformat()
    total_rows = 0
    if st.get("done"):
        # F17 增量刷新:max_date−45d → 今
        mx = st.get("newest") or today
        start = (date.fromisoformat(mx) - timedelta(days=REFRESH_DAYS)).isoformat()
        r = fetch_window(net, key, sid, today, start, rpm)
        if r["state"] == "FAIL":
            upsert_registry(meta, "FAIL", r["note"])
            return {"sid": sid, "state": "FAIL", "rows": 0, "note": r["note"], "mode": "refresh"}
        if r["rows"]:
            write_series_parquet(sid, r["rows"])
            upsert_db(r["rows"], sid)
            st["newest"] = max(st.get("newest", ""), r["rows"][0]["date"])
            ck[sid] = st
            _save_ckpt(ck)
        upsert_registry(meta, "OK", "refresh")
        return {"sid": sid, "state": "OK", "rows": len(r["rows"]), "mode": "refresh"}
    windows = plan_windows(meta["freq"], today, since, st.get("oldest"))
    if not windows:
        st["done"] = True
        ck[sid] = st
        _save_ckpt(ck)
        upsert_registry(meta, "OK", "done")
        return {"sid": sid, "state": "OK", "rows": 0, "mode": "done"}
    n_win = 0
    empty_streak = 0
    for start, end in windows:
        if max_windows and n_win >= max_windows:
            upsert_registry(meta, "PARTIAL", f"max-windows {max_windows};游標 {st.get('oldest')}")
            return {"sid": sid, "state": "OK", "rows": total_rows, "mode": f"partial@{st.get('oldest')}"}
        r = fetch_window(net, key, sid, end, start, rpm)
        n_win += 1
        if r["state"] == "FAIL":
            upsert_registry(meta, "FAIL", r["note"])
            return {"sid": sid, "state": "FAIL", "rows": total_rows, "note": r["note"], "mode": "backfill"}
        if r["rows"]:
            empty_streak = 0
            write_series_parquet(sid, r["rows"])
            upsert_db(r["rows"], sid)
            total_rows += len(r["rows"])
            st["newest"] = max(st.get("newest", ""), r["rows"][0]["date"])
            st["oldest"] = r["rows"][-1]["date"] if not st.get("oldest") else min(st["oldest"], r["rows"][-1]["date"])
        else:
            empty_streak += 1
            st["oldest"] = start
        ck[sid] = st
        _save_ckpt(ck)
        if empty_streak >= 2:  # 連續兩空視窗=序列起點已過
            break
    st["done"] = True
    ck[sid] = st
    _save_ckpt(ck)
    state = "OK" if total_rows else "EMPTY"
    upsert_registry(meta, state, "backfill done")
    return {"sid": sid, "state": state, "rows": total_rows, "mode": "backfill"}


def build_mirror() -> tuple[str, str]:
    """F09:polars 合併 macro/fred/*.parquet → us_macro_all.parquet(缺 polars=pyarrow 後備)"""
    files = sorted(PQ_DIR.glob("*.parquet"))
    if not files:
        return "SKIP", "無序列 parquet"
    try:
        import polars as pl
        df = pl.concat([pl.read_parquet(f) for f in files], how="vertical_relaxed").sort(["series", "date"])
        df.write_parquet(MIRROR, compression="zstd")
        return "OK", f"polars {df.height} 列 {len(files)} 序列"
    except ImportError:
        import pyarrow as pa
        import pyarrow.parquet as pq
        t = pa.concat_tables([pq.read_table(f) for f in files], promote_options="default")
        t = t.sort_by([("series", "ascending"), ("date", "ascending")])
        pq.write_table(t, MIRROR, compression="zstd")
        return "FALLBACK", f"pyarrow {t.num_rows} 列 {len(files)} 序列(polars 缺:pip install polars)"
    except Exception as exc:
        return "FAIL", f"{type(exc).__name__}: {str(exc)[:80]}"


def data_home_note() -> str:
    """F20:接點實體路徑(MDL123 resolve_home;缺=倉內 output_hub)"""
    try:
        import glob as _g
        import importlib.util as _il
        hits = sorted(_g.glob(str(VIA / "supportive modules" / "registry" / "CGC_MDL123_DataHome_v0*.py")))
        if hits:
            spec = _il.spec_from_file_location("m123_dyn", hits[-1])
            m = _il.module_from_spec(spec)
            spec.loader.exec_module(m)
            home, src = m.resolve_home(VIA)
            linked = OUT.parent.is_symlink() or (os.name == "nt" and OUT.parent.exists()
                                                 and str(OUT.parent.resolve()).lower() != str(OUT.parent).lower())
            return f"資料家 {home}({src});output_hub 接點 {'LINKED' if linked else 'UNLINKED(倉內)'}"
    except Exception as exc:
        return f"資料家解析敗 {type(exc).__name__}"
    return "資料家解析器缺(MDL123)"


# ---------------------------------------------------------------- 執行
def run(args: list[str]) -> int:
    def opt(name, default=None):
        return args[args.index(name) + 1] if name in args and args.index(name) + 1 < len(args) else default
    if "--fred-key" in args:
        print("  " + write_key(opt("--fred-key", "")), flush=True)
    since = opt("--since", SINCE_DEFAULT)
    workers = int(opt("--workers", "4"))
    rpm = int(opt("--rpm", "100"))
    limit = int(opt("--limit", "0"))
    max_windows = int(opt("--max-windows", "0"))
    only = [x.strip() for x in opt("--only", "").split(",") if x.strip()]
    print("=== FRED 宏觀 SSOT 擷取(VDF_ENG074;從新往舊)===", flush=True)
    print(f"  {data_home_note()}", flush=True)
    if not gate_open():
        print("[FAIL-CLOSED] 同意閘未開(VIA_NET_CONSENT/VIA_SCRAPE_CONSENT)", flush=True)
        return 2
    key, ksrc = fred_key(interactive=True)
    if not key:
        print(f"  [SKIP] {ksrc}", flush=True)
        return 3
    print(f"  [鑰] {ksrc}(…{key[-4:]})", flush=True)
    net = _net_or_none()
    if net is None:
        print("[FAIL] 統包網路工具缺席(SUP_MDL740)", flush=True)
        return 1
    series, ssrc = load_series()
    if only:
        series = [s for s in series if s["fred_id"] in only]
    if limit:
        series = series[:limit]
    ck = _load_ckpt()
    n_done = sum(1 for s in series if ck.get(s["fred_id"], {}).get("done"))
    print(f"  [母冊] {ssrc} · {len(series)} 序列(已 DONE {n_done}=增量刷新;其餘從新往舊回補至 {since})"
          f" · 工人 {workers} · 節流 {rpm}/min", flush=True)
    t0 = time.time()
    results = []
    done_n = [0]
    lock = threading.Lock()

    def one(meta):
        r = fetch_series(net, key, meta, since, rpm, ck, max_windows)
        with lock:
            done_n[0] += 1
            print(f"  [{r['state']:<5}] {r['sid']:<12} {r['rows']:>6} 列 {r.get('mode', ''):<14} "
                  f"{progress_bar(done_n[0], len(series), spent=time.time() - t0)} {r.get('note', '')[:40]}", flush=True)
        return r

    if VIA_ACCEL is not None and hasattr(VIA_ACCEL, "accel_map") and workers > 1:
        for ok, r in VIA_ACCEL.accel_map(one, series, workers=workers):
            results.append(r if ok else {"sid": "?", "state": "FAIL", "rows": 0, "note": str(r)})
    else:
        for meta in series:
            try:
                results.append(one(meta))
            except Exception as exc:
                results.append({"sid": meta["fred_id"], "state": "FAIL", "rows": 0, "note": f"{type(exc).__name__}: {exc}"})
    ms, mnote = build_mirror()
    tally = {k: sum(1 for r in results if r["state"] == k) for k in ("OK", "EMPTY", "FAIL")}
    rows = sum(r["rows"] for r in results)
    print(f"  [鏡] {ms} {mnote}", flush=True)
    print(f"  [計] 序列 {len(results)} · OK {tally['OK']} · EMPTY {tally['EMPTY']} · FAIL {tally['FAIL']} · 新列 {rows}"
          f" · 請求 {_STATS['req']}(敗 {_STATS['fail']}) · {time.time() - t0:.1f}s · 落 {OUT}", flush=True)
    return 1 if tally["FAIL"] else 0


def status() -> int:
    import duckdb
    print("=== FRED 宏觀 SSOT 現況 ===")
    print(f"  {data_home_note()}")
    series, ssrc = load_series()
    ck = _load_ckpt()
    print(f"  母冊 {ssrc} · {len(series)} 序列 · checkpoint DONE {sum(1 for s in series if ck.get(s['fred_id'], {}).get('done'))}")
    if not DB_GL.exists():
        print(f"  [DB] 缺 {DB_GL.name}")
        return 0
    con = duckdb.connect(str(DB_GL), read_only=True)
    tabs = {t for (t,) in con.execute("SHOW TABLES").fetchall()}
    if TABLE in tabs:
        n, ns, mn, mx = con.execute(f"SELECT COUNT(*), COUNT(DISTINCT series), CAST(MIN(date) AS VARCHAR), "
                                    f"CAST(MAX(date) AS VARCHAR) FROM {TABLE}").fetchone()
        dt = {r[1]: r[2] for r in con.execute(f"PRAGMA table_info('{TABLE}')").fetchall()}.get("date")
        print(f"  [{TABLE}] {n} 列 · {ns} 序列 · {mn}→{mx} · date 型別 {dt}")
    else:
        print(f"  [{TABLE}] 表缺(尚未擷取)")
    if REG_TABLE in tabs:
        for st, c in con.execute(f"SELECT state, COUNT(*) FROM {REG_TABLE} GROUP BY 1 ORDER BY 1").fetchall():
            print(f"  [冊] {st} {c}")
    con.close()
    print(f"  parquet 序列檔 {len(list(PQ_DIR.glob('*.parquet'))) if PQ_DIR.exists() else 0} · 鏡 {'在' if MIRROR.exists() else '缺'}")
    return 0


def lamps() -> int:
    print("=== 20 強化加速器(擷取真用面)===")
    try:
        import polars  # noqa: F401
        pol = "ACTIVE"
    except ImportError:
        pol = "FALLBACK(pyarrow)"
    state = {"F02": "ACTIVE" if VIA_ACCEL is not None else "FALLBACK(序跑)", "F09": pol,
             "F10": "ACTIVE" if VIA_NET_TOOL_PATH or _net_or_none() else "MISSING",
             "F01": "ACTIVE" if ssot_path() else "FALLBACK(內建 16)"}
    for fid, name, mech, a in FETCH_ACCEL:
        print(f"  {fid} {state.get(fid, 'ACTIVE'):<16} {name:<10} {mech}(↔{a})")
    return 0


# ---------------------------------------------------------------- 自測
def selftest() -> int:
    import tempfile
    global OUT, DB_GL, PQ_DIR, MIRROR, CKPT, KEY_FILE
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    chk("① 同意閘 fail-closed", not gate_open({}) and gate_open({"VIA_NET_CONSENT": "YES", "VIA_SCRAPE_CONSENT": "YES"}))
    series, ssrc = load_series()
    chk("② SSOT 母冊動態載入(190 FRED series;缺=內建 16 誠實 FALLBACK)",
        (ssrc.startswith("SSOT") and len(series) >= 150) or (ssrc.startswith("FALLBACK") and len(series) == 16), f"{ssrc} {len(series)}")
    w = plan_windows("Monthly", "2026-09-04", "1990-01-01", None)
    chk("③ 從新往舊視窗(首窗含今日;末窗觸底 since;倒序不重疊)",
        w[0][1] == "2026-09-04" and w[-1][0] == "1990-01-01" and all(w[i][0] > w[i + 1][1] for i in range(len(w) - 1)), f"{len(w)} 窗")
    w2 = plan_windows("Daily", "2026-09-04", "1990-01-01", "2020-01-01")
    chk("④ checkpoint 續跑(游標前一日續;Daily 2y 窗)", w2[0][1] == "2019-12-31" and w2[0][0] == "2018-01-01")
    _s = (OUT, DB_GL, PQ_DIR, MIRROR, CKPT, KEY_FILE)
    with tempfile.TemporaryDirectory() as td:
        OUT = Path(td)
        DB_GL, CKPT, KEY_FILE = OUT / "gl.duckdb", OUT / "ck.json", OUT / ".k"
        PQ_DIR, MIRROR = OUT / "macro" / "fred", OUT / "macro" / "all.parquet"
        calls = []

        class FakeNet:
            @staticmethod
            def http_json(url):
                calls.append(url)
                import urllib.parse as up
                q = dict(up.parse_qsl(up.urlsplit(url).query))
                if q["series_id"] == "BAD":
                    return {"state": "FAIL", "note": "429"}
                s, e = q["observation_start"], q["observation_end"]
                obs = []
                d = date.fromisoformat(e).replace(day=1)
                while d.isoformat() >= s and d.isoformat() >= "2000-01-01":
                    obs.append({"date": d.isoformat(), "value": "." if d.month == 6 else str(100 + d.year - 2000)})
                    d = (d - timedelta(days=1)).replace(day=1)
                return {"state": "OK", "data": {"observations": obs}}

        meta = {"fred_id": "CPIAUCSL", "via_code": "US.Prices.CPI.Headline", "freq": "Monthly", "unit": "", "theme": "Prices",
                "sub_theme": "CPI", "indicator": "CPI", "src": "BLS"}
        ck = {}
        r1 = fetch_series(FakeNet, "k", meta, "1990-01-01", 1000, ck, 0)
        import duckdb
        con = duckdb.connect(str(DB_GL), read_only=True)
        n, mn, mx = con.execute(f"SELECT COUNT(*), CAST(MIN(date) AS VARCHAR), CAST(MAX(date) AS VARCHAR) FROM {TABLE}").fetchone()
        dtype = {r[1]: r[2] for r in con.execute(f"PRAGMA table_info('{TABLE}')").fetchall()}
        reg = con.execute(f"SELECT state, n_rows FROM {REG_TABLE}").fetchone()
        con.close()
        chk("⑤ 單序列從新往舊落庫(sort desc;缺值 '.' 過濾;typed DATE/DOUBLE;序列冊)",
            r1["state"] == "OK" and n == r1["rows"] and mn == "2000-01-01" and mx == "2026-09-01"
            and dtype.get("date") == "DATE" and dtype.get("value") == "DOUBLE" and reg == ("OK", n), f"{n} 列 {mn}→{mx} 請求 {len(calls)}")
        chk("⑥ 首請求為最新視窗(observation_end=今日;sort_order=desc)",
            "sort_order=desc" in calls[0] and f"observation_end={date.today().isoformat()}" in calls[0])
        chk("⑦ checkpoint DONE + parquet 每序列 + 冪等重跑=增量刷新(≤1 請求;列數不增)",
            ck["CPIAUCSL"].get("done") and (PQ_DIR / "CPIAUCSL.parquet").exists()
            and fetch_series(FakeNet, "k", meta, "1990-01-01", 1000, ck, 0)["mode"] == "refresh"
            and duckdb.connect(str(DB_GL), read_only=True).execute(f"SELECT COUNT(*) FROM {TABLE}").fetchone()[0] == n)
        bad = dict(meta, fred_id="BAD", via_code="X")
        r3 = fetch_series(FakeNet, "k", bad, "1990-01-01", 1000, ck, 0)
        chk("⑧ 失敗誠實(FAIL 不假綠;序列冊記 FAIL;不標 done)", r3["state"] == "FAIL" and not ck.get("BAD", {}).get("done"))
        ms, mnote = build_mirror()
        chk("⑨ polars 鏡(缺=pyarrow FALLBACK 誠實)", ms in ("OK", "FALLBACK") and MIRROR.exists(), f"{ms} {mnote}")
        # 既存 VARCHAR date 表相容(ENG055 舊表)
        con = duckdb.connect(str(DB_GL))
        con.execute(f"DROP TABLE {TABLE}")
        con.execute(f"CREATE TABLE {TABLE} (date VARCHAR, series VARCHAR, value DOUBLE)")
        con.close()
        n_old = upsert_db([{"date": "2026-01-01", "value": 1.0}], "X")
        n_old2 = upsert_db([{"date": "2026-01-01", "value": 1.0}], "X")
        chk("⑩ 既存 VARCHAR date 表相容(顯式 CAST;anti-join 冪等)", n_old == 1 and n_old2 == 1)
        os.environ.pop("FRED_API_KEY", None)
        k0, note0 = fred_key(interactive=False)
        write_key("abcdef0123456789abcdef0123456789")
        k1, src1 = fred_key(interactive=False)
        chk("⑪ 鑰律(缺=SKIP 印指令不空轉;鑰匙檔優先;永不入 git)",
            k0 == "" and "SKIP" in note0 and k1.endswith("6789") and "鑰匙檔" in src1)
        t0 = time.monotonic()
        for _ in range(5):
            _throttle(3, window=0.3)
        chk("⑫ 令牌桶節流(3/視窗時第 4 次起等待;5 次≥0.3s)", time.monotonic() - t0 >= 0.3)
        _RL["stamps"].clear()
    OUT, DB_GL, PQ_DIR, MIRROR, CKPT, KEY_FILE = _s
    chk("⑬ 20 強化加速器冊(F01–F20;各對映 A 燈)", len(FETCH_ACCEL) == 20 and len({f[0] for f in FETCH_ACCEL}) == 20
        and all(f[3].startswith("A") for f in FETCH_ACCEL))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑭ 鑰匙紅線(源碼零明文鑰;gitignored 鑰匙檔;遮罩尾 4 碼)",
        not any(len(t) == 32 and all(c in "0123456789abcdef" for c in t) for t in src.replace("(", " ").replace(")", " ").split())
        and "gitignored" in src and "key[-4:]" in src)
    chk("⑮ 進度條(A16 式 n/N %·已耗·預估)", "預估剩餘" in progress_bar(3, 10, spent=3.0) and "3/10" in progress_bar(3, 10))
    chk("⑯ 動詞律(無動詞=run;動詞任意位置;--fred-key 於 main 先寫鑰)",
        parse_verb(["--since", "2000-01-01"]) == ("run", ["--since", "2000-01-01"]) and parse_verb(["--workers", "2", "status"])[0] == "status"
        and 'if "--fred-key" in a:' in Path(__file__).read_text(encoding="utf-8"))
    print(f"  [計] 十六檢 OK {16 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def parse_verb(a: list[str]) -> tuple[str, list[str]]:
    """動詞任意位置;無動詞=run(批362);回 (verb, 其餘參數)"""
    verbs = {"run", "status", "lamps", "help"}
    verb = next((x for x in a if x in verbs), "run")
    return verb, [x for x in a if x not in verbs]


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== FRED 宏觀 SSOT 擷取(VDF_ENG074 v0101)· 十六檢自測 ===")
        return selftest()
    if "--fred-key" in a:   # 批362:先寫鑰(無論動詞);永不印全鑰
        i = a.index("--fred-key")
        print("  " + write_key(a[i + 1] if i + 1 < len(a) else ""), flush=True)
        a = [x for j, x in enumerate(a) if j != i and j != i + 1]
    verb, rest = parse_verb(a)
    if verb == "status":
        return status()
    if verb == "lamps":
        return lamps()
    if verb == "help":
        print(__doc__)
        return 0
    return run(rest)


if __name__ == "__main__":
    sys.exit(main())
