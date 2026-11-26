#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VDF_ENG242_ThreePeriodDistill v0100 — VDF 各引擎個別啟動抓最新三期 · 跨來源核對 · 名稱同義 · 蒸餾入湖(不重複)· 準備檢查 · 最快排程

操作員 2026-11-25:「VDF 引擎是獨立的,確認都有導入加速器及網路工具 100% 覆蓋 · 工具都透過 VCGC 安裝 · 參數可編輯且整合好可被管理 ·
個別啟動抓最新三期 · 不同來源有相同資料就抓最新三期來核對 · 順便把名稱同義建立起來 · 準備完成檢查完成 → 引擎測試到整體最快最佳化 ·
蒸餾輸出,一定不能重複輸出 · 要先看資料庫有什麼 · 輸出 DataFrame 最佳化對齊」。逐題定案:期 = 依頻率各取三期;實抓只在桌機;
蒸餾寫進現有 Parquet 湖(主鍵差集,核對另存);排程器 APScheduler(掛在 VDF_SystemManager schedule)。
本支只調度 VDF 自己的既有引擎(不重寫擷取):族群冊 VDF_FetchGroups_SSOT 尾版(14 組 · cadence · sources · start_args)→
VDF_MDL012_FetchGroups 尾版 plan_rows()(每支引擎的指令)→ 子行程個別啟動 → VDF_ENG239_ParquetLakeBuild 尾版入湖(只增)→ 本支蒸餾 / 核對。
動詞:
  ready                 準備檢查(每支族群引擎):能單獨啟動(__main__)· 加速器生效(語法樹匯入 + 執行時載得到)· 網路橋 · 第三方件找得到且在
                        VCGC 安裝帳(VIA_Lib_Registry,只讀;缺帳 = 灰)· 不頂層匯入他系統 · 在 Param_Engine_Map → DataFrame + 燈
  inventory             先看資料庫有什麼:每組每個來源表 列數 · 鍵數 · 不同期數 · 最新三期;湖目錄 VIEW 列數(只讀,不出網)
  plan [--groups G,..]  三期窗:daily 往前 buffer 天 · monthly 月 · quarterly 季 · macro / event 天(參數冊)→ 每支引擎的指令({start} / start_args 換成窗起)
  run [--groups ..] [--live] [--lanes N]
                        依 bench 的最長優先(LPT)排 N 道並行(預設參數 three.lanes = 3);組內照冊上順序逐支個別啟動;每支一行心跳 · 逾時另計。
                        沒 --live = 只列指令不執行(容器 / 乾跑)。--live:子行程才開兩道同意閘(已裁定 1;不寫進檔)。跑完叫 ENG239 入湖(--skip-fetch,只增)。
  distill               每組每表:每個鍵最新三期(dense_rank)· 欄名照同義冊對齊 · 完全相同的列去掉 · 同主鍵不同值不猜(列出、不輸出)
                        → <湖>/_distill/<組>__<表>.parquet(整份原子換新 = 不重複輸出)+ <湖>/VDF_distill_catalog.duckdb VIEW
  reconcile             同組多來源:對齊後的共同數值欄 × (鍵, 期) → 相對差 > three.tolerance_rel = MISMATCH → <湖>/_distill/reconcile__<組>.parquet
  names [--apply]       欄名同義:全形轉半形 · 去空白 · 小寫後查 VDF_NameSynonym_SSOT 尾版;沒對到的列 UNMAPPED;--apply 出新版(只增)
  bench                 運作帳每組 / 每支秒數 → 最長優先順序 · 估總時間(N 道)· 最慢那支
  params-init [--apply] 把本支參數登進 VDF 正本(ParamControl_SSOT;經 ENG053 寫新版號,再 derive 寫回統一參數冊)
輸出:VIA_Reports/vdf_three/<UTC>/ 的 DataFrame(polars,退 pandas)parquet + SUMMARY.json;運作帳 RUN_LEDGER.jsonl 只增。
rc:0 綠 · 2 黃 · 1 紅。不用 TA-Lib · 不 import 他系統(VCGC 安裝帳只讀 JSON)· 不刪任何湖分片。
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0111] SuperAccel 加速器橋(從 TEMP 跑時改由工作目錄 / VIA_REPO 找倉;graceful) =====
try:
    import os as _sa_os
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_hit = None
    _sa_roots = [_sa_Path(__file__).resolve(), _sa_Path.cwd().resolve()]
    if _sa_os.environ.get("VIA_REPO"):
        _sa_roots.append(_sa_Path(_sa_os.environ["VIA_REPO"]).resolve())
    for _sa_r in _sa_roots:
        for _sa_q in (_sa_r, *_sa_r.parents):
            for _sa_c in (_sa_q / "supportive modules", _sa_q / "VeritasIntelligenceAnalytics" / "supportive modules"):
                if (_sa_c / "VIA_SuperAccel_Module.py").exists():
                    _sa_hit = _sa_c
                    break
            if _sa_hit:
                break
        if _sa_hit:
            break
    if _sa_hit and str(_sa_hit) not in _sa_sys.path:
        _sa_sys.path.insert(0, str(_sa_hit))
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響(自測會把它記成黃)
# ===== [VIA:ACCEL-BRIDGE:END] =====
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(操作員 2026-11-25「網路工具也要強制加入」;從 TEMP 跑時改由工作目錄 / VIA_REPO 找倉;graceful) =====
VIA_NET_TOOL_PATH = None
try:
    import os as _nb_os
    from pathlib import Path as _nb_Path
    _nb_roots = [_nb_Path(__file__).resolve(), _nb_Path.cwd().resolve()]
    if _nb_os.environ.get("VIA_REPO"):
        _nb_roots.append(_nb_Path(_nb_os.environ["VIA_REPO"]).resolve())
    for _nb_r in _nb_roots:
        for _nb_q in (_nb_r, *_nb_r.parents):
            for _nb_dir in (_nb_q / "supportive modules" / "network", _nb_q / "VeritasIntelligenceAnalytics" / "supportive modules" / "network"):
                _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py")) if _nb_dir.is_dir() else []
                if _nb_hits:
                    VIA_NET_TOOL_PATH = str(_nb_hits[-1])
                    break
            if VIA_NET_TOOL_PATH:
                break
        if VIA_NET_TOOL_PATH:
            break
except Exception:  # noqa: BLE001
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT:載入不出網,真的連線才看閘);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import ast
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

STEM = "VDF_ENG242_ThreePeriodDistill"
VERSION = "v0100"
TAG = f"{STEM} {VERSION}"
HERE = Path(__file__).resolve().parent
VDF = HERE.parent
VIA = VDF.parent.parent
_T0 = time.time()
PY_VDF = sys.executable
DEFAULTS = {"three.periods": 3, "three.lanes": 3, "three.tolerance_rel": 0.001, "three.engine_timeout_s": 1800,
            "three.buffer": {"daily": 10, "monthly": 4, "quarterly": 4, "macro": 400, "event": 30},
            "schedule.timezone": "Asia/Taipei",
            "schedule.jobs": [{"id": "vdf_three_run", "cron": "35 18 * * 1-5", "cmd": ["VDF_ENG242_ThreePeriodDistill", "run", "--live"]},
                              {"id": "vdf_three_distill", "cron": "55 18 * * 1-5", "cmd": ["VDF_ENG242_ThreePeriodDistill", "distill"]}]}
ACCEPT = ("VIA_SuperAccel_Module", "VeritasCeleritas_v1141")
ENTRY_ENV = {"VIA_CENTRAL_ENTRY": "1", "VIA_ENTRY_CONTROL": STEM}
LEDGER_BAD = {"n": 0}
SEED_NAMES = {   # 欄名同義的種子(VDF 自己的冊尾版會蓋過 / 補上)
    "date": ["date", "日期", "trade_date", "交易日期", "資料日期", "datetime", "period"],
    "code": ["code", "stock_id", "證券代號", "股票代號", "ticker", "symbol", "公司代號", "代號"],
    "name": ["name", "stock_name", "證券名稱", "公司名稱", "名稱"],
    "open": ["open", "開盤價", "開盤"], "high": ["high", "最高價", "最高"], "low": ["low", "最低價", "最低"],
    "close": ["close", "收盤價", "收盤", "adj_close_raw"], "volume": ["volume", "成交股數", "成交量", "vol"],
    "amount": ["amount", "成交金額", "turnover", "value"], "revenue": ["revenue", "營業收入", "當月營收", "monthly_revenue"],
}


def say(msg: str) -> None:
    print(f"[{time.time() - _T0:6.1f}s] {msg}", flush=True)


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(str(p)).stem)
    return int(m.group(1)) if m else -1


def newest(d: Path, pat: str):
    c = [p for p in d.glob(pat) if _vnum(p) >= 0] if d.is_dir() else []
    return max(c, key=_vnum) if c else None


def load_mod(path: Path, name: str):
    sp = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(sp)
    sys.modules[name] = m
    sp.loader.exec_module(m)
    return m


# ---------------------------------------------------------------- 參數(VDF 正本)
def params(vdf: Path = VDF) -> dict:
    """VDF 正本 ParamControl_SSOT 尾版裡 three.* / schedule.* 的值;沒登記的用預設並標出(params-init 補登)。"""
    out, src = dict(DEFAULTS), {k: "DEFAULT" for k in DEFAULTS}
    mt = newest(vdf, "VDF_ParamControl_SSOT_v*.json")
    if mt:
        for e in json.loads(mt.read_text(encoding="utf-8")).get("params", []):
            if str(e.get("path", "")).startswith(("three.", "schedule.")):
                out[e["path"]] = e.get("value")
                src[e["path"]] = e.get("id")
    out["_src"] = src
    out["_master"] = mt.name if mt else None
    return out


# ---------------------------------------------------------------- 三期窗
def window(cadence: str, as_of: date, buf: dict) -> date:
    n = int(buf.get(cadence, buf.get("event", 30)))
    if cadence == "monthly":
        y, m = as_of.year, as_of.month - n
        while m <= 0:
            y, m = y - 1, m + 12
        return date(y, m, 1)
    if cadence == "quarterly":
        q = (as_of.month - 1) // 3 - n
        y = as_of.year
        while q < 0:
            y, q = y - 1, q + 4
        return date(y, q * 3 + 1, 1)
    return as_of - timedelta(days=n)


def subst(args: list, start: date, as_of: date) -> list:
    out, i = [], 0
    while i < len(args):
        a = str(args[i]).replace("{start}", start.isoformat()).replace("{end}", as_of.isoformat()).replace("{years}", "1")
        if a in ("--start", "--since") and i + 1 < len(args):
            out += [a, start.isoformat()]
            i += 2
            continue
        out.append(a)
        i += 1
    return out


def m012(vdf: Path = VDF):
    t = newest(vdf, "VDF_MDL012_FetchGroups_v*.py")
    if t is None:
        raise FileNotFoundError("VDF_MDL012_FetchGroups 尾版不在")
    return load_mod(t, f"{STEM}_m012")


def tail_file(f, vdf: Path = VDF) -> str:
    """尾版律:擷取冊上的檔 → 同家族尾版(VDF 夾與 engine 夾都找);不是版號檔就原樣。"""
    if not f:
        return f
    p = Path(f)
    m = re.match(r"(.+)_v\d{4}$", p.stem)
    if not m:
        return str(f)
    c = [q for d in {p.parent if p.is_absolute() else vdf, vdf, vdf / "engine"} for q in Path(d).glob(m.group(1) + "_v*.py") if _vnum(q) >= 0]
    return str(max(c, key=_vnum)) if c else str(f)


def plan(mod, prm: dict, gids=None, as_of: date | None = None) -> list:
    book = mod.load_book()
    fb_name = str(book.get("fetch_book", "")).split("(")[0].strip()
    fb = mod._json(mod.tail(fb_name)) if fb_name else {}
    as_of = as_of or (mod.latest_trading_day() if hasattr(mod, "latest_trading_day") else date.today())
    rows = []
    for g in book["groups"]:
        if gids and g["id"] not in gids:
            continue
        start = window(g.get("cadence", "daily"), as_of, prm["three.buffer"])
        sa = g.get("start_args") or {}
        for r in mod.plan_rows(book, fb, [g["id"]], as_of.isoformat(), None):
            args = list(r.get("run_args") or [])
            if r["id"] in sa:
                args += [x for x in sa[r["id"]]]
            tf = tail_file(r.get("file"))
            rows.append({"group": g["id"], "zh": g.get("zh"), "cadence": g.get("cadence"), "engine": r["id"], "file": tf,
                         "book_file": Path(str(r.get("file"))).name, "stale_in_book": Path(tf).name != Path(str(r.get("file"))).name,
                         "start": start.isoformat(), "as_of": as_of.isoformat(), "args": subst(args, start, as_of),
                         "needs": r.get("needs") or [], "sources": g.get("sources") or []})
    return rows


# ---------------------------------------------------------------- ready(準備檢查)
def _top_imports(src: str) -> set:
    out = set()
    for n in ast.parse(src).body:
        if isinstance(n, ast.Import):
            out.update(a.name.split(".")[0] for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module and not n.level:
            out.add(n.module.split(".")[0])
    return out


def _accel_imported(src: str) -> bool:
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.Import) and any(a.name in ACCEPT or a.name.startswith("SUP_MDL737") for a in n.names):
            return True
        if isinstance(n, ast.ImportFrom) and n.module and (n.module in ACCEPT or n.module.startswith("SUP_MDL737")):
            return True
    return False


def ledger_pkgs(via: Path = VIA):
    p = via / "supportive modules" / "registry" / "VIA_Lib_Registry_v0100.json"
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None                                                     # 沒有安裝帳 = 灰(照實)
    s = set()
    for row in d.get("ledger", []):
        for pk in row.get("packages", []) or []:
            s.add(re.split(r"[=<>!~\[ ]", str(pk.get("name") if isinstance(pk, dict) else pk))[0].lower().replace("_", "-"))
    return s


def ready(rows: list, vdf: Path = VDF) -> dict:
    from importlib.util import find_spec
    led = ledger_pkgs(vdf.parent.parent)
    emap = newest(vdf, "VDF_Param_Engine_Map_v*.json")
    mapped = {Path(k).name for k in (json.loads(emap.read_text(encoding="utf-8")).get("by_engine") or {})} if emap else set()
    std = set(getattr(sys, "stdlib_module_names", ())) | {"__future__"}
    local = {p.stem for p in vdf.rglob("*.py")} | {p.stem for p in (vdf.parent.parent / "supportive modules").rglob("*.py")} if vdf.is_dir() else set()
    accel_rt = VIA_ACCEL is not None
    out, seen = [], set()
    for r in rows:
        f = Path(r["file"]) if r.get("file") else None
        if f is None or str(f) in seen:
            continue
        seen.add(str(f))
        if not f.is_absolute():
            f = vdf / f
        row = {"group": r["group"], "engine": r["engine"], "file": f.name}
        if not f.is_file():
            out.append(dict(row, lamp="RED", why="檔不在"))
            continue
        src = f.read_text(encoding="utf-8-sig", errors="replace")
        try:
            tree = ast.parse(src)
        except SyntaxError as e:
            out.append(dict(row, lamp="RED", why=f"SyntaxError L{e.lineno}"))
            continue
        imps = _top_imports(src)
        third = sorted(m for m in imps if m not in std and m not in local and not m.startswith("_"))
        missing = [m for m in third if find_spec(m) is None]
        not_gate = [m for m in third if led is not None and m.lower().replace("_", "-") not in led]
        other_sys = sorted(m for m in imps if m.startswith(("CGC_", "VRN_", "VAP_", "VQG_")))
        row.update(standalone=any(isinstance(n, ast.If) and "__main__" in ast.dump(n.test) for n in tree.body),
                   accel=_accel_imported(src) and accel_rt, net="[VIA:NET-BRIDGE" in src or "def _via_net" in src,
                   third_party=third, missing=missing, not_via_vcgc=not_gate if led is not None else "GRAY(無安裝帳)",
                   other_system_imports=other_sys, in_param_map=f.name in mapped)
        bad = (not row["standalone"]) or (not row["accel"]) or (not row["net"]) or missing or other_sys
        row["lamp"] = "RED" if bad else ("YELLOW" if (led is not None and not_gate) or not row["in_param_map"] else "GREEN")
        out.append(row)
    n = len(out)
    cov = {k: f"{sum(1 for x in out if x.get(k))}/{n}" for k in ("standalone", "accel", "net", "in_param_map")}
    lamps = [x["lamp"] for x in out]
    return {"rows": out, "coverage": cov, "lamp": "RED" if "RED" in lamps else ("YELLOW" if "YELLOW" in lamps else "GREEN")}


# ---------------------------------------------------------------- inventory(先看資料庫)
def _duck():
    import duckdb
    return duckdb


def table_stats(con, table: str, date_col, key_col, n: int = 3) -> dict:
    q = lambda c: '"' + str(c).replace('"', '""') + '"'  # noqa: E731
    cols = [r[0] for r in con.execute(f"DESCRIBE {table}").fetchall()]
    st = {"rows": con.execute(f"SELECT count(*) FROM {table}").fetchone()[0], "columns": cols}
    if date_col and date_col in cols:
        ds = [str(r[0]) for r in con.execute(f"SELECT DISTINCT {q(date_col)} d FROM {table} WHERE {q(date_col)} IS NOT NULL ORDER BY d DESC LIMIT {n}").fetchall()]
        st.update(latest=ds, periods=con.execute(f"SELECT count(DISTINCT {q(date_col)}) FROM {table}").fetchone()[0])
    if key_col and key_col in cols:
        st["keys"] = con.execute(f"SELECT count(DISTINCT {q(key_col)}) FROM {table}").fetchone()[0]
    return st


def inventory(mod, rows_or_book, roots=None, lake: Path | None = None) -> dict:
    duckdb = _duck()
    book = mod.load_book()
    roots = roots or [mod.default_home()] if hasattr(mod, "default_home") else (roots or [])
    out = []
    for g in book["groups"]:
        for s in g.get("sources") or []:
            if s.get("type") != "duckdb":
                out.append({"group": g["id"], "db": s.get("db"), "table": s.get("table"), "state": "NOT_DUCKDB"})
                continue
            p = mod.find_db(s["db"], roots) if hasattr(mod, "find_db") else None
            if p is None:
                out.append({"group": g["id"], "db": s["db"], "table": s["table"], "state": "DB_MISSING"})
                continue
            try:
                con = duckdb.connect(str(p), read_only=True)
                try:
                    st = table_stats(con, '"' + s["table"] + '"', s.get("date_col"), s.get("key_col"))
                finally:
                    con.close()
                out.append({"group": g["id"], "db": s["db"], "table": s["table"], "state": "OK", **st})
            except Exception as e:  # noqa: BLE001 - 鎖住 / 表不在照實記
                out.append({"group": g["id"], "db": s["db"], "table": s["table"], "state": f"ERROR {type(e).__name__}: {str(e)[:100]}"})
    lake = lake or (VIA / "VIA_Reports" / "vdf_lake")
    cat = lake / "VDF_catalog.duckdb"
    views = []
    if cat.is_file():
        try:
            con = duckdb.connect(str(cat), read_only=True)
            for (v,) in con.execute("SELECT view_name FROM duckdb_views() WHERE NOT internal").fetchall():
                try:
                    views.append({"view": v, "rows": con.execute(f'SELECT count(*) FROM "{v}"').fetchone()[0]})
                except Exception as e:  # noqa: BLE001
                    views.append({"view": v, "rows": None, "error": type(e).__name__})
            con.close()
        except Exception as e:  # noqa: BLE001
            views.append({"view": "(catalog)", "error": f"{type(e).__name__}: {str(e)[:100]}"})
    bad = [r for r in out if r["state"] != "OK"]
    return {"rows": out, "lake_views": views, "lamp": "GREEN" if not bad else "YELLOW",
            "counts": {"sources": len(out), "ok": len(out) - len(bad), "missing_or_error": len(bad), "lake_views": len(views)}}


# ---------------------------------------------------------------- names(欄名同義)
def norm_name(s: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", str(s))).lower()


def name_book(vdf: Path = VDF) -> dict:
    m = {k: list(v) for k, v in SEED_NAMES.items()}
    t = newest(vdf, "VDF_NameSynonym_SSOT_v*.json")
    if t:
        for k, v in (json.loads(t.read_text(encoding="utf-8")).get("canonical") or {}).items():
            m.setdefault(k, [])
            m[k] += [x for x in v if x not in m[k]]
    rev = {}
    for k, v in m.items():
        for a in v + [k]:
            rev[norm_name(a)] = k
    return {"canonical": m, "rev": rev, "book": t.name if t else None}


def names(cols_by_src: dict, nb: dict) -> dict:
    rows = []
    for src, cols in cols_by_src.items():
        for c in cols:
            k = nb["rev"].get(norm_name(c))
            rows.append({"source": src, "column": c, "canonical": k, "state": "MAPPED" if k else "UNMAPPED"})
    un = sorted({r["column"] for r in rows if r["state"] == "UNMAPPED"})
    return {"rows": rows, "unmapped": un, "lamp": "GREEN" if not un else "YELLOW",
            "counts": {"columns": len(rows), "mapped": len(rows) - sum(1 for r in rows if r["state"] == "UNMAPPED"), "unmapped": len(un)}}


def write_name_book(vdf: Path, nb: dict, unmapped: list) -> Path:
    t = newest(vdf, "VDF_NameSynonym_SSOT_v*.json")
    old = json.loads(t.read_text(encoding="utf-8")) if t else {"schema": "VIA.VDF.NameSynonym.v1", "canonical": {}, "pending": []}
    new = dict(old)
    new["canonical"] = {k: list(dict.fromkeys(nb["canonical"].get(k, []) + (old.get("canonical") or {}).get(k, []))) for k in nb["canonical"]}
    new["pending"] = sorted(set(old.get("pending") or []) | set(unmapped))          # 沒對到的只增列待裁,不猜
    nv = (_vnum(t) + 1) if t else 100
    vs = f"v{nv:04d}"
    new.update(version=vs, prior=t.name if t else None, ts=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
               owner="VDF", policy="欄名同義:全形轉半形 · 去空白 · 小寫後查;pending = 待操作員裁定歸哪個正名")
    new[f"why_{vs}"] = f"{TAG} names --apply:種子 + 前版合併 · pending {len(new['pending'])}"
    dest = vdf / f"VDF_NameSynonym_SSOT_{vs}.json"
    tmp = dest.with_name(dest.name + f".{os.getpid()}.sdd_tmp")
    tmp.write_text(json.dumps(new, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    os.replace(tmp, dest)
    return dest


# ---------------------------------------------------------------- distill / reconcile
def _canon_cols(cols: list, nb: dict) -> dict:
    out, used = {}, set()
    for c in cols:
        k = nb["rev"].get(norm_name(c)) or c
        if k in used:
            k = c                                                       # 兩欄同名同義 → 保留原名,不覆蓋
        used.add(k)
        out[c] = k
    return out


def distill_one(con, rel: str, date_col, key_col, nb: dict, n: int, out_path: Path) -> dict:
    q = lambda c: '"' + str(c).replace('"', '""') + '"'  # noqa: E731
    cols = [r[0] for r in con.execute(f"DESCRIBE SELECT * FROM {rel}").fetchall()]
    if not date_col or date_col not in cols:
        return {"state": "NO_DATE_COL", "rows": 0}
    part = f"PARTITION BY {q(key_col)} " if key_col and key_col in cols else ""
    ren = _canon_cols(cols, nb)
    sel = ", ".join(f"{q(c)} AS {q(ren[c])}" for c in cols)
    base = (f"SELECT DISTINCT {sel} FROM (SELECT *, dense_rank() OVER ({part}ORDER BY {q(date_col)} DESC) AS _rk "
            f"FROM {rel} WHERE {q(date_col)} IS NOT NULL) WHERE _rk <= {int(n)}")
    kc, dc = ren.get(key_col) if key_col else None, ren[date_col]
    pk = [x for x in (kc, dc) if x]
    dup = con.execute(f"SELECT count(*) FROM (SELECT {', '.join(q(x) for x in pk)} FROM ({base}) GROUP BY ALL HAVING count(*) > 1)").fetchone()[0]
    final = base if not dup else (f"SELECT * FROM ({base}) WHERE ({', '.join(q(x) for x in pk)}) NOT IN "
                                  f"(SELECT ({', '.join(q(x) for x in pk)}) FROM ({base}) GROUP BY ALL HAVING count(*) > 1)")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_name(out_path.name + f".{os.getpid()}.sdd_tmp")
    con.execute(f"COPY ({final} ORDER BY ALL) TO '{tmp.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)")
    os.replace(tmp, out_path)                                           # 整份原子換新 = 不重複輸出
    rows = con.execute(f"SELECT count(*) FROM read_parquet('{out_path.as_posix()}')").fetchone()[0]
    return {"state": "OK" if not dup else "PK_CONFLICT", "rows": rows, "pk": pk, "pk_conflicts": dup, "renamed": {k: v for k, v in ren.items() if k != v}}


def reconcile_pair(con, a_rel: str, b_rel: str, pk: list, tol: float, out_path: Path) -> dict:
    q = lambda c: '"' + str(c).replace('"', '""') + '"'  # noqa: E731
    ca = {r[0]: r[1] for r in con.execute(f"DESCRIBE SELECT * FROM {a_rel}").fetchall()}
    cb = {r[0]: r[1] for r in con.execute(f"DESCRIBE SELECT * FROM {b_rel}").fetchall()}
    if not all(k in ca and k in cb for k in pk):
        return {"state": "NO_COMMON_KEY", "pk": pk}
    num = [c for c in ca if c in cb and c not in pk and any(t in str(ca[c]).upper() for t in ("INT", "DOUBLE", "FLOAT", "DECIMAL", "REAL"))]
    if not num:
        return {"state": "NO_COMMON_NUMERIC", "pk": pk}
    on = " AND ".join(f"a.{q(k)} = b.{q(k)}" for k in pk)
    cmp = " UNION ALL ".join(
        f"SELECT {', '.join('a.' + q(k) for k in pk)}, '{c}' AS col, a.{q(c)}::DOUBLE AS a_val, b.{q(c)}::DOUBLE AS b_val FROM {a_rel} a JOIN {b_rel} b ON {on}"
        for c in num)
    sql = (f"SELECT *, abs(a_val - b_val) / nullif(greatest(abs(a_val), abs(b_val)), 0) AS rel_diff FROM ({cmp})")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_name(out_path.name + f".{os.getpid()}.sdd_tmp")
    con.execute(f"COPY ({sql} ORDER BY ALL) TO '{tmp.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)")
    os.replace(tmp, out_path)
    r = con.execute(f"SELECT count(*), count(*) FILTER (WHERE rel_diff > {float(tol)}) FROM read_parquet('{out_path.as_posix()}')").fetchone()
    return {"state": "OK", "compared": r[0], "mismatch": r[1], "columns": num, "pk": pk}


# ---------------------------------------------------------------- run(個別啟動 · LPT · N 道)
def vdf_python() -> str:
    """派別支 VDF 引擎用 VDF 家族境的 python(照 Get-VIAEnvPython:VIA_PY_VDF → 境名 via_vdf_312 · via_vdf · via_vdf_313 × 根);
    找不到才退回本解譯器(照實標在收據)。"""
    ov = os.environ.get("VIA_PY_VDF", "")
    if ov and Path(ov).is_file():
        return ov
    home = Path.home()
    roots = [os.environ.get("VIA_ENV_ROOT", "")] + os.environ.get("VIA_ENV_ROOTS", "").split(";") + [
        str(home / "envs"), str(home / "miniconda3" / "envs"), str(home / "Miniconda3" / "envs"), str(home / "anaconda3" / "envs"), str(VIA / "Environments")]
    for r in roots:
        for n in ("via_vdf_312", "via_vdf", "via_vdf_313"):
            for sub in (("Scripts", "python.exe"), ("python.exe",), ("bin", "python3"), ("bin", "python")):
                q = Path(r, n, *sub) if r else None
                if q is not None and q.is_file():
                    return str(q)
    return sys.executable


def append_line(path: Path, line: str) -> None:
    """只增帳:檔尾不是換行先補一個(別的工具寫的帳可能沒收尾),再寫一列。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    pre = ""
    if path.is_file() and path.stat().st_size:
        with path.open("rb") as f:
            f.seek(-1, 2)
            pre = "" if f.read(1) == b"\n" else "\n"
    with path.open("a", encoding="utf-8") as f:
        f.write(pre + line + "\n")


def lpt_order(groups: list, ledger: Path) -> list:
    secs, bad = {}, 0
    if ledger.is_file():
        for ln in ledger.read_text(encoding="utf-8").splitlines():
            try:
                d = json.loads(ln)
            except ValueError:
                bad += 1                                                    # 壞列照實數(摘要帶出),不算時間
                d = {}
            if d.get("kind") == "group" and d.get("secs") is not None:
                secs[d["group"]] = float(d["secs"])                      # 最新一次為準
    LEDGER_BAD["n"] = bad
    return sorted(groups, key=lambda g: (-secs.get(g, 1e9), g))          # 沒量過的先跑(未知 = 當最長)


def run_groups(rows: list, prm: dict, live: bool, lanes: int, out: Path, runner=None) -> list:
    groups = list(dict.fromkeys(r["group"] for r in rows))
    ledger = out.parent / "RUN_LEDGER.jsonl"
    order = lpt_order(groups, ledger)
    res, lock = [], threading.Lock()

    def one_group(g):
        t0, recs = time.time(), []
        for r in [x for x in rows if x["group"] == g]:
            cmd = [PY_VDF, str(r["file"]), *r["args"]]
            if not live:
                recs.append({"engine": r["engine"], "cmd": " ".join(cmd[1:])[:300], "rc": None, "secs": 0, "state": "DRY"})
                continue
            env = dict(os.environ, **{k: os.environ.get(k, v) for k, v in ENTRY_ENV.items()}, PYTHONUTF8="1",
                       VIA_NET_CONSENT="YES", VIA_SCRAPE_CONSENT="YES")       # 同意閘只在這一步的子行程裡(已裁定 1)
            e0 = time.time()
            try:
                if runner:
                    rc = runner(cmd, env)
                else:
                    rc = subprocess.run(cmd, cwd=str(Path(r["file"]).parent), env=env, capture_output=True, text=True,
                                        timeout=int(prm["three.engine_timeout_s"])).returncode
            except subprocess.TimeoutExpired:
                rc = 124
            recs.append({"engine": r["engine"], "rc": rc, "secs": round(time.time() - e0, 2), "state": "OK" if rc == 0 else f"RC {rc}"})
            say(f"  {g} · {r['engine']} · rc {rc} · {recs[-1]['secs']}s")
        rec = {"kind": "group", "group": g, "secs": round(time.time() - t0, 2), "engines": recs, "live": live,
               "utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        with lock:
            res.append(rec)
            if live:
                append_line(ledger, json.dumps(rec, ensure_ascii=False))
        return rec

    stop = threading.Event()

    def heart():
        while not stop.wait(30):
            say(f"心跳 · 完成 {len(res)}/{len(order)} 組")

    threading.Thread(target=heart, daemon=True).start()
    with ThreadPoolExecutor(max_workers=max(1, int(lanes))) as ex:
        list(ex.map(one_group, order))
    stop.set()
    return res


# ---------------------------------------------------------------- DataFrame · 收據
def frame(rows: list):
    cols = sorted({k for r in rows for k in r}) or ["state"]
    norm = [{c: (None if r.get(c) is None else (r.get(c) if isinstance(r.get(c), str) else json.dumps(r.get(c), ensure_ascii=False, default=str)))
             for c in cols} for r in rows]
    try:
        import polars as pl
        return pl.DataFrame(norm, schema={c: pl.Utf8 for c in cols}) if norm else pl.DataFrame(schema={c: pl.Utf8 for c in cols})
    except ImportError:
        try:
            import pandas as pd
            return pd.DataFrame(norm, columns=cols).astype("string")
        except ImportError:
            return None


def save(verb: str, res: dict, root: Path = VIA) -> Path:
    base = root / "VIA_Reports" / "vdf_three"
    od = base / datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    od.mkdir(parents=True, exist_ok=True)
    df = frame(res.get("rows", []))
    fmt = "none"
    if df is not None:
        try:
            df.write_parquet(od / f"{verb}.parquet", compression="zstd") if hasattr(df, "write_parquet") else df.to_parquet(od / f"{verb}.parquet", compression="zstd", index=False)
            fmt = "parquet"
        except Exception:  # noqa: BLE001 - 沒有 parquet 寫手 → jsonl 退路
            (od / f"{verb}.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False, default=str) + "\n" for r in res.get("rows", [])), encoding="utf-8")
            fmt = "jsonl(退路)"
    summ = {k: v for k, v in res.items() if k != "rows"}
    summ.update(tool=TAG, verb=verb, utc=datetime.now(timezone.utc).isoformat(timespec="seconds"), format=fmt,
                accel=VIA_ACCEL is not None, net=VIA_NET_TOOL_PATH is not None,
                three={"should": len(res.get("rows", [])), "done": len(res.get("rows", [])), "skipped": res.get("skipped", [])})
    (od / "SUMMARY.json").write_text(json.dumps(summ, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    append_line(base / "RUN_LEDGER.jsonl", json.dumps({"kind": "verb", "verb": verb, "utc": summ["utc"], "lamp": res.get("lamp"),
                                                       "secs": round(time.time() - _T0, 2), "counts": res.get("counts")}, ensure_ascii=False, default=str))
    return od


# ---------------------------------------------------------------- 主流程
def lake_dir() -> Path:
    return VIA / "VIA_Reports" / "vdf_lake"


def do_distill(mod, prm: dict, nb: dict, lake: Path) -> dict:
    duckdb = _duck()
    cat = lake / "VDF_catalog.duckdb"
    if not cat.is_file():
        return {"lamp": "YELLOW", "note": f"湖目錄不在:{cat}(先 run --live 或 ENG239 run)", "rows": []}
    book = mod.load_book()
    con = duckdb.connect(str(cat), read_only=True)
    views = {v for (v,) in con.execute("SELECT view_name FROM duckdb_views() WHERE NOT internal").fetchall()}
    rows, rec, made = [], [], []
    for g in book["groups"]:
        srcs = [s for s in g.get("sources") or [] if s.get("type") == "duckdb"]
        done = []
        for s in srcs:
            v = f"v_{Path(s['db']).stem}__{s['table']}"
            if v not in views:
                rows.append({"group": g["id"], "view": v, "state": "VIEW_MISSING"})
                continue
            outp = lake / "_distill" / f"{g['id']}__{s['table']}.parquet"
            r = distill_one(con, f'"{v}"', s.get("date_col"), s.get("key_col"), nb, int(prm["three.periods"]), outp)
            rows.append({"group": g["id"], "view": v, **r, "file": outp.name})
            if r["state"] in ("OK", "PK_CONFLICT"):
                done.append((outp, r.get("pk") or []))
                made.append((f"d_{g['id']}__{s['table']}", outp))
        for i in range(len(done)):
            for j in range(i + 1, len(done)):
                pk = [k for k in done[i][1] if k in done[j][1]]
                rp = lake / "_distill" / f"reconcile__{g['id']}__{i}_{j}.parquet"
                r = reconcile_pair(con, f"read_parquet('{done[i][0].as_posix()}')", f"read_parquet('{done[j][0].as_posix()}')", pk,
                                   float(prm["three.tolerance_rel"]), rp)
                rec.append({"group": g["id"], "pair": f"{done[i][0].name} × {done[j][0].name}", **r})
    con.close()
    dc = lake / "VDF_distill_catalog.duckdb"
    c2 = duckdb.connect(str(dc))
    for name, p in made:
        c2.execute(f"CREATE OR REPLACE VIEW \"{name}\" AS SELECT * FROM read_parquet('{p.as_posix()}')")
    c2.close()
    bad = [r for r in rows if r["state"] not in ("OK",)]
    mism = sum(int(r.get("mismatch") or 0) for r in rec)
    return {"rows": rows, "reconcile": rec, "lamp": "RED" if any(r["state"] == "PK_CONFLICT" for r in rows) else ("YELLOW" if bad or mism else "GREEN"),
            "counts": {"tables": len(rows), "ok": len(rows) - len(bad), "pk_conflict": sum(1 for r in rows if r["state"] == "PK_CONFLICT"),
                       "pairs": len(rec), "mismatch": mism}}


def main() -> int:
    a = sys.argv[1:]
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    verb = a[0] if a else "ready"
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a and a.index(k) + 1 < len(a) else d  # noqa: E731
    prm = params()
    gids = [x for x in (opt("--groups") or "").split(",") if x] or None
    global PY_VDF
    PY_VDF = vdf_python()
    say(f"派別支引擎的 python:{PY_VDF}" + ("(VDF 境沒找到,退回本解譯器 · 黃)" if PY_VDF == sys.executable else ""))
    say(f"{TAG} {verb} · 正本 {prm['_master']} · 期數 {prm['three.periods']} · 道數 {prm['three.lanes']} · 加速器 {'載入' if VIA_ACCEL is not None else '沒載到(黃)'} · 網路工具 {'在' if VIA_NET_TOOL_PATH else '不在'}")
    mod = m012()
    if verb == "ready":
        pr = plan(mod, prm, gids)
        res = ready(pr)
        stale = sorted({f"{r['book_file']} → {Path(r['file']).name}" for r in pr if r.get("stale_in_book")})
        res["stale_in_fetch_book"] = stale
        if stale and res["lamp"] == "GREEN":
            res["lamp"] = "YELLOW"
        say("覆蓋:" + " · ".join(f"{k} {v}" for k, v in res["coverage"].items()) + f" · 擷取冊釘舊版 {len(stale)} 支(本支改跑尾版)")
        for x in stale:
            say("  擷取冊釘舊版:" + x)
    elif verb == "inventory":
        res = inventory(mod, None)
    elif verb == "plan":
        rows = plan(mod, prm, gids)
        res = {"rows": [{k: (" ".join(v) if k == "args" else v) for k, v in r.items() if k != "sources"} for r in rows], "lamp": "GREEN",
               "counts": {"groups": len({r["group"] for r in rows}), "engines": len(rows)}}
    elif verb == "run":
        rows = plan(mod, prm, gids)
        live = "--live" in a
        od = VIA / "VIA_Reports" / "vdf_three" / "run"
        od.mkdir(parents=True, exist_ok=True)
        recs = run_groups(rows, prm, live, int(opt("--lanes", prm["three.lanes"])), od / "x")
        flat = [{"group": g["group"], **e} for g in recs for e in g["engines"]]
        res = {"rows": flat, "counts": {"groups": len(recs), "engines": len(flat), "fail": sum(1 for e in flat if e["rc"] not in (0, None))}}
        if live:
            t = newest(HERE, "VDF_ENG239_ParquetLakeBuild_v*.py")
            start = min(r["start"] for r in rows) if rows else date.today().isoformat()
            r = subprocess.run([PY_VDF, str(t), "run", "--skip-fetch", "--start", start], cwd=str(HERE),
                               env=dict(os.environ, **ENTRY_ENV, PYTHONUTF8="1"), capture_output=True, text=True)
            res["ingest_rc"] = r.returncode
            say(f"入湖(ENG239 --skip-fetch,只增)rc {r.returncode}")
        res["lamp"] = "RED" if res["counts"]["fail"] or res.get("ingest_rc") not in (None, 0) else ("GREEN" if live else "YELLOW")
    elif verb in ("distill", "reconcile"):
        res = do_distill(mod, prm, name_book(), lake_dir())
        if verb == "reconcile":
            res = {"rows": res.get("reconcile", []), "lamp": res["lamp"], "counts": res.get("counts")}
    elif verb == "names":
        duckdb = _duck()
        book, cols = mod.load_book(), {}
        roots = [mod.default_home()] if hasattr(mod, "default_home") else []
        for g in book["groups"]:
            for s in g.get("sources") or []:
                p = mod.find_db(s.get("db", ""), roots) if s.get("type") == "duckdb" else None
                if p:
                    try:
                        con = duckdb.connect(str(p), read_only=True)
                        cols[f"{s['db']}:{s['table']}"] = [r[0] for r in con.execute(f'DESCRIBE "{s["table"]}"').fetchall()]
                        con.close()
                    except Exception as e:  # noqa: BLE001
                        cols[f"{s['db']}:{s['table']}"] = []
                        say(f"  {s['db']}:{s['table']} 讀不到({type(e).__name__})")
        nb = name_book()
        res = names(cols, nb)
        if "--apply" in a:
            res["written"] = write_name_book(VDF, nb, res["unmapped"]).name
    elif verb == "bench":
        led = VIA / "VIA_Reports" / "vdf_three" / "run" / "RUN_LEDGER.jsonl"
        recs = [json.loads(x) for x in led.read_text(encoding="utf-8").splitlines() if x.strip()] if led.is_file() else []
        last = {}
        for r in recs:
            if r.get("kind") == "group":
                last[r["group"]] = r
        order = lpt_order(list(last), led)
        lanes, loads = int(prm["three.lanes"]), [0.0] * int(prm["three.lanes"])
        for g in order:
            loads[loads.index(min(loads))] += last[g]["secs"]
        slow = max((e for r in last.values() for e in r["engines"]), key=lambda e: e.get("secs") or 0, default=None)
        res = {"rows": [{"group": g, "secs": last[g]["secs"]} for g in order], "lamp": "GREEN" if last else "GRAY",
               "counts": {"groups": len(last), "serial_s": round(sum(r["secs"] for r in last.values()), 1), "est_wall_s": round(max(loads), 1) if last else 0,
                          "lanes": lanes, "slowest_engine": slow}}
    elif verb == "params-init":
        e53 = load_mod(newest(HERE, "VDF_ENG053_ParamEngineMap_v*.py"), f"{STEM}_e53")
        mt = e53.tail_of(VDF, e53.MASTER)
        m = json.loads(mt.read_text(encoding="utf-8"))
        have = {e["path"] for e in m["params"]}
        ut = e53.tail_of(VDF, e53.UNIFIED)
        add = [(k, v) for k, v in DEFAULTS.items() if k not in have]
        res = {"rows": [{"path": k, "value": v, "state": "ADD"} for k, v in add], "lamp": "GREEN" if not add else "YELLOW", "counts": {"add": len(add)}}
        if add and "--apply" in a:
            nums = [int(x["id"].rsplit("-", 1)[1]) for x in m["params"] if re.fullmatch(r"VDF-PAR-\d+", str(x.get("id")))]
            n, at = max(nums or [0]), datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            for k, v in add:
                n += 1
                m["params"].append({"name": f"三期蒸餾 · {k.split('.', 1)[1]}", "book": ut.name, "path": k, "value": v, "class": "時間範圍" if ("buffer" in k or "periods" in k or k.startswith("schedule.")) else "規則",
                                    "mutable": True, "why": f"{TAG} params-init", "id": f"VDF-PAR-{n:03d}", "version": "v0100", "registered_at": at, "derive_pending": at})
            res["written"] = e53.write_next(mt, m, f"{TAG} params-init:補登 {len(add)} 個三期參數(值待 derive 寫回 {ut.name})").name
            d = subprocess.run([PY_VDF, str(newest(HERE, "VDF_ENG053_ParamEngineMap_v*.py")), "derive", "--apply"], cwd=str(HERE), capture_output=True, text=True)
            res["derive_rc"] = d.returncode
            res["lamp"] = "GREEN" if d.returncode in (0, 2) else "RED"
    else:
        say(f"[RED] 未知動詞 {verb}")
        return 1
    od = save(verb, res)
    say(f"{verb} · {res['lamp']} · " + " · ".join(f"{k} {v}" for k, v in (res.get("counts") or {}).items()) + (f" · 寫 {res['written']}" if res.get("written") else "")
        + (f" · {res['note']}" if res.get("note") else ""))
    say(f"DataFrame → {od}")
    return {"GREEN": 0, "YELLOW": 2, "GRAY": 2}.get(res["lamp"], 1)


# ---------------------------------------------------------------- 自測(全在暫存夾造資料)
def selftest() -> int:
    ok, bad = [], []

    def chk(name, cond, note=""):
        (ok if cond else bad).append(name)
        print(("  [OK] " if cond else "  [NG] ") + name + (f" · {note}" if note else ""), flush=True)

    chk("加速器載入(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    chk("網路工具載入(_via_net() is not None · 載入不出網)", _via_net() is not None, str(VIA_NET_TOOL_PATH))
    b = DEFAULTS["three.buffer"]
    asof = date(2026, 11, 24)
    chk("三期窗:日 −10 天 · 月 −4 月 · 季 −4 季", window("daily", asof, b) == date(2026, 11, 14) and window("monthly", asof, b) == date(2026, 7, 1)
        and window("quarterly", asof, b) == date(2025, 10, 1))
    chk("起日換成窗起({start} · --start · --since · {years})", subst(["run", "--start", "{start}", "--end", "{end}", "--since", "2018-01-01", "--years", "{years}"],
                                                               date(2026, 11, 14), asof) == ["run", "--start", "2026-11-14", "--end", "2026-11-24", "--since", "2026-11-14", "--years", "1"])
    with tempfile.TemporaryDirectory() as tdx:
        v = Path(tdx)
        (v / "engine").mkdir()
        for n in ("VDF_ENG900_X_v0101.py", "VDF_ENG900_X_v0104.py"):
            (v / "engine" / n).write_text("x = 1\n", encoding="utf-8")
        chk("尾版律:冊上釘舊版 → 換成同家族尾版", Path(tail_file(str(v / "engine" / "VDF_ENG900_X_v0101.py"), v)).name == "VDF_ENG900_X_v0104.py")
    nb = name_book(Path(tempfile.gettempdir()) / "no_such_vdf")
    n = names({"twse:tw_daily_prices": ["日期", "證券代號", "收盤價 ", "ＣＬＯＳＥ", "怪欄"]}, nb)
    chk("名稱同義:全形 / 空白 / 大小寫正規化 · 沒對到列 UNMAPPED", [r["canonical"] for r in n["rows"]] == ["date", "code", "close", "close", None] and n["unmapped"] == ["怪欄"])
    try:
        duckdb = _duck()
    except ImportError:
        duckdb = None
        chk("duckdb 可用(缺 = 黃)", False, "duckdb 沒裝")
    if duckdb:
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            con = duckdb.connect(str(td / "a.duckdb"))
            con.execute("CREATE TABLE p(date DATE, stock_id VARCHAR, close DOUBLE)")
            rows = [(f"2026-11-{d:02d}", c, float(d) + (0.5 if c == "2330" else 0)) for d in range(10, 25) for c in ("2330", "2317")]
            con.executemany("INSERT INTO p VALUES (?, ?, ?)", rows + [rows[-1]])          # 一列完全重複
            con.execute("CREATE TABLE q(日期 DATE, 證券代號 VARCHAR, 收盤價 DOUBLE)")
            con.executemany("INSERT INTO q VALUES (?, ?, ?)", [(d, c, v + (1.0 if (c == "2317" and d == "2026-11-24") else 0)) for d, c, v in rows])
            st = table_stats(con, "p", "date", "stock_id")
            chk("先看資料庫:列數 · 鍵數 · 期數 · 最新三期", st["rows"] == 31 and st["keys"] == 2 and st["periods"] == 15 and st["latest"][0] == "2026-11-24")
            r1 = distill_one(con, "p", "date", "stock_id", nb, 3, td / "out" / "p.parquet")
            r2 = distill_one(con, "q", "日期", "證券代號", nb, 3, td / "out" / "q.parquet")
            chk("蒸餾:每鍵最新三期 · 完全重複的去掉 · 欄名對齊", r1["rows"] == 6 and r1["state"] == "OK" and r1["pk"] == ["code", "date"] and r2["renamed"] == {"日期": "date", "證券代號": "code", "收盤價": "close"}, str(r1))
            r1b = distill_one(con, "p", "date", "stock_id", nb, 3, td / "out" / "p.parquet")
            chk("重跑 = 整份換新不重複(列數不變)", r1b["rows"] == 6 and len(list((td / "out").glob("p*.parquet"))) == 1)
            con.execute("INSERT INTO p VALUES ('2026-11-24', '2330', 999)")
            r1c = distill_one(con, "p", "date", "stock_id", nb, 3, td / "out" / "p2.parquet")
            chk("同主鍵不同值 = PK_CONFLICT(不猜,那一鍵期不輸出)", r1c["state"] == "PK_CONFLICT" and r1c["pk_conflicts"] == 1 and r1c["rows"] == 5)
            rc = reconcile_pair(con, f"read_parquet('{(td / 'out' / 'p.parquet').as_posix()}')", f"read_parquet('{(td / 'out' / 'q.parquet').as_posix()}')",
                                ["code", "date"], 0.001, td / "out" / "rec.parquet")
            chk("跨來源核對:同鍵同期比數值 · 超出容差 = MISMATCH", rc["compared"] == 6 and rc["mismatch"] == 1 and rc["columns"] == ["close"], str(rc))
            con.close()
            led = td / "RUN_LEDGER.jsonl"
            led.write_text("\n".join(json.dumps({"kind": "group", "group": g, "secs": s}) for g, s in (("A", 5), ("B", 50), ("C", 20))), encoding="utf-8")
            chk("最快排程:最長優先(LPT)· 沒量過的先跑", lpt_order(["A", "B", "C", "D"], led) == ["D", "B", "C", "A"])
            calls = []
            rows3 = [{"group": "B", "engine": "e1", "file": str(td / "e1.py"), "args": ["run"]}, {"group": "A", "engine": "e2", "file": str(td / "e2.py"), "args": ["run"]}]
            dry = run_groups(rows3, DEFAULTS, False, 2, td / "x")
            chk("沒 --live = 只列指令不執行", all(e["state"] == "DRY" for g in dry for e in g["engines"]))
            live = run_groups(rows3, DEFAULTS, True, 2, td / "x", runner=lambda c, env: (calls.append((c[1], env.get("VIA_NET_CONSENT"), env.get("VIA_ENTRY_CONTROL"))), 0)[1])
            chk("--live:每支個別啟動 · 同意閘只在子行程 · 帶入口標記 · 寫運作帳", len(calls) == 2 and all(x[1] == "YES" and x[2] for x in calls)
                and os.environ.get("VIA_NET_CONSENT") != "YES" and len((td / "RUN_LEDGER.jsonl").read_text(encoding="utf-8").splitlines()) == 5)
            (td / "ok.py").write_text("# [VIA:ACCEL-BRIDGE:v0111]\ntry:\n    import VIA_SuperAccel_Module as VIA_ACCEL\nexcept Exception:\n    VIA_ACCEL = None\n"
                                      "def _via_net():\n    return None\nimport json\nif __name__ == '__main__':\n    pass\n", encoding="utf-8")
            (td / "bad.py").write_text("import CGC_MDL001_X\nx = 1\n", encoding="utf-8")
            rd = ready([{"group": "G", "engine": "ok", "file": str(td / "ok.py")}, {"group": "G", "engine": "bad", "file": str(td / "bad.py")}], td)
            lm = {r["engine"]: r for r in rd["rows"]}
            chk("準備檢查:單獨啟動 · 加速器生效 · 網路橋 · 不匯入他系統", lm["ok"]["standalone"] and lm["ok"]["accel"] and lm["ok"]["net"]
                and lm["bad"]["lamp"] == "RED" and lm["bad"]["other_system_imports"] == ["CGC_MDL001_X"] and rd["coverage"]["accel"] == "1/2", str(rd["coverage"]))
    chk("輸出 DataFrame", frame([{"a": 1, "b": [1]}]) is not None)
    print(f"{TAG} selftest {len(ok)}/{len(ok) + len(bad)}" + (" · 不過:" + " · ".join(bad) if bad else ""), flush=True)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
