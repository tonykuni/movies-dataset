#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_MDL016_MacroCrossCheck v0100 — AKShare × 官方(FRED / us_macro)總經序列「最新 n 筆」交叉比對 → 警告(來源不同?還是 AKShare 有誤?)。

操作員 2026-11-09:「AKShare 引擎也可抓到一些總體經濟數據,跟原本 FRED 或其他政府 / 私人機構抓出來的資料,可用最新三筆數據進行比較做出警告:
是來源不同還是 AKShare 有誤」。

做法(讀冊 VDF_MacroCrossCheck_Pairs_SSOT:每對 = AKShare 函數 + 欄名候選 + 官方序列 + 轉換 + 容忍;不寫死):
  run        每對取 AKShare 最新 n 筆(預設 3)與官方同期間的值 →
             AGREE · SOURCE_DIFF:PERIOD_LABEL_SHIFT(值同 · 期間標籤差一期)· SOURCE_DIFF:UNIT_SCALE(差固定倍數 10/100/1000)·
             SOURCE_DIFF:OFFICIAL_LAGGING(AKShare 多一期 · 官方庫該回填)· AKSHARE_STALE(AKShare 落後 ≥ 2 期)·
             AKSHARE_SUSPECT(同期同單位差超容忍且無法解釋 → RED)· NODATA(任一邊沒資料 · 照實)。
             資料來源(離線優先):AKShare = VAKE 庫 vake.duckdb 的 v_<fn> 視圖;官方 = vdf_global_market.duckdb us_macro 或 macro/us_macro_all.parquet 鏡像。
             --live 才連網:AKShare 經 SUP_MDL740 akshare_call(雙閘 · 套件缺 = SKIP)、FRED 經 http_json(雙閘 + FRED_API_KEY;鑰遮罩)。
             --fixture <json> 直接餵兩邊資料(自測 · 桌機貼回)。
  selftest   零網路 · tempfile · 六種判決各一例 · 閘關 = SKIP 且不碰 environ · 鑰不外洩。
輸出:<out>/VDF_MacroCrossCheck_latest.json / .md(警告逐對 · 兩邊原值並列)。預設 <out> = <VIA>/VIA_Reports/vdf/macro。
燈:全 AGREE = GREEN;有 SOURCE_DIFF / STALE / NODATA = YELLOW;有 AKSHARE_SUSPECT = RED(rc 0,燈在收據;冊缺 rc 2)。
邊界:只讀兩邊資料、不改任何一邊;不 import akshare / requests;連網只經 SUP_MDL740;不寫 environ。
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_root = _sa_Path(__file__).resolve()
    for _ in range(6):
        _sa_root = _sa_root.parent
        if (_sa_root / "VeritasIntelligenceAnalytics").is_dir() or _sa_root.name == "VeritasIntelligenceAnalytics":
            break
    _sa_dir = (_sa_root / "VeritasIntelligenceAnalytics" if (_sa_root / "VeritasIntelligenceAnalytics").is_dir() else _sa_root) / "supportive modules" / "accelerator"
    if _sa_dir.is_dir() and str(_sa_dir) not in _sa_sys.path:
        _sa_sys.path.insert(0, str(_sa_dir))
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_here = _nb_Path(__file__).resolve()
    for _nb_up in (_nb_here.parents[2], _nb_here.parents[3] if len(_nb_here.parents) > 3 else _nb_here.parents[2]):
        _nb_dir = _nb_up / "supportive modules" / "network"
        if _nb_dir.is_dir():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
except Exception:  # noqa: BLE001
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入;本檔的連網全經它(雙閘在工具裡 · 本檔永不代設)。"""
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

import argparse
import json
import math
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

VERSION = "v0100"
ENGINE = "VDF_MDL016_MacroCrossCheck " + VERSION
HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
BOOK_GLOB = "VDF_MacroCrossCheck_Pairs_SSOT_v[0-9][0-9][0-9][0-9].json"
LATEST_JSON = "VDF_MacroCrossCheck_latest.json"
LATEST_MD = "VDF_MacroCrossCheck_latest.md"
FRED_API = "https://api.stlouisfed.org/fred"
KEY_ENV = "FRED_API_KEY"
KEY_FILE = ".fred_api_key"
SCALES = (10.0, 100.0, 1000.0, 0.1, 0.01, 0.001)
_NET_OVERRIDE = None


def load_json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def mask(url: str) -> str:
    return re.sub(r"(api_key=)[^&\s]+", r"\1***", url or "")


def _net():
    return _NET_OVERRIDE if _NET_OVERRIDE is not None else _via_net()


def find_key(out_root: Path) -> str:
    """鑰只在本函數鏈內用;收據永不寫值。"""
    k = os.environ.get(KEY_ENV, "").strip()
    if k:
        return k
    f = out_root / KEY_FILE
    return f.read_text(encoding="utf-8").strip() if f.is_file() else ""


# ── 期間鍵 ───────────────────────────────────────────────────────────────────────────────────
def period_key(raw, freq: str) -> str | None:
    """任何常見日期寫法 → 期間鍵:M → YYYY-MM · Q → YYYY-Qn · W/D → YYYY-MM-DD。解析不了 = None(不猜)。"""
    s = str(raw).strip()
    if not s or s.lower() in ("none", "nan", "nat"):
        return None
    m = re.match(r"^(\d{4})\s*[-/.年]?\s*Q([1-4])$", s, re.I) or re.match(r"^(\d{4})Q([1-4])$", s, re.I)
    if m:
        y, q = int(m.group(1)), int(m.group(2))
        return "%04d-Q%d" % (y, q) if freq == "Q" else "%04d-%02d" % (y, q * 3)
    m = re.match(r"^(\d{4})\s*[-/.年]\s*(\d{1,2})(?:\s*[-/.月]\s*(\d{1,2}))?", s)
    if not m:
        m = re.match(r"^(\d{4})(\d{2})(\d{2})?$", s)
    if not m:
        return None
    y, mo = int(m.group(1)), int(m.group(2))
    d = int(m.group(3)) if m.lastindex and m.lastindex >= 3 and m.group(3) else 1
    if not (1 <= mo <= 12 and 1 <= d <= 31):
        return None
    if freq == "Q":
        return "%04d-Q%d" % (y, (mo - 1) // 3 + 1)
    if freq == "M":
        return "%04d-%02d" % (y, mo)
    return "%04d-%02d-%02d" % (y, mo, d)


def shift_key(key: str, freq: str, n: int) -> str:
    if freq == "Q":
        y, q = int(key[:4]), int(key[-1])
        t = y * 4 + (q - 1) + n
        return "%04d-Q%d" % (t // 4, t % 4 + 1)
    if freq == "M":
        y, mo = int(key[:4]), int(key[5:7])
        t = y * 12 + (mo - 1) + n
        return "%04d-%02d" % (t // 12, t % 12 + 1)
    from datetime import date, timedelta  # noqa: PLC0415
    y, mo, d = int(key[:4]), int(key[5:7]), int(key[8:10])
    return (date(y, mo, d) + timedelta(days=7 * n if freq == "W" else n)).strftime("%Y-%m-%d")


def _num(x):
    try:
        if x is None:
            return None
        if isinstance(x, (int, float)):
            v = float(x)
        else:
            s = str(x).replace(",", "").replace("%", "").strip()
            if s in ("", "-", "—", "None", "nan"):
                return None
            v = float(s)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None


# ── 兩邊資料 → {期間鍵: 值}(照冊轉換)──────────────────────────────────────────────────
def pick_cols(rows: list, date_cols: list, value_cols: list) -> tuple:
    if not rows:
        return None, None
    cols = list(rows[0].keys())
    dc = next((c for c in date_cols if c in cols), None) or next((c for c in cols if re.search(r"日期|月份|时间|時間|date|period", str(c), re.I)), None)
    vc = next((c for c in value_cols if c in cols), None) or next((c for c in cols if re.search(r"今值|现值|現值|value|指数|指數|实际|實際", str(c), re.I) and c != dc), None)
    return dc, vc


def to_series(rows: list, date_cols: list, value_cols: list, freq: str) -> dict:
    dc, vc = pick_cols(rows, date_cols, value_cols)
    out = {}
    if not dc or not vc:
        return out
    for r in rows:
        k, v = period_key(r.get(dc), freq), _num(r.get(vc))
        if k and v is not None:
            out[k] = v                                            # 同鍵後寫者勝(資料通常由舊到新 · 修正值在後)
    return out


def transform(series: dict, how: str, freq: str) -> dict:
    if how == "level" or not series:
        return dict(series)
    keys = sorted(series)
    lag = 1 if how in ("diff", "diff_k", "mom_pct") else (4 if freq == "Q" else 12)
    out = {}
    for k in keys:
        prev = series.get(shift_key(k, freq, -lag))
        if prev is None:
            continue
        cur = series[k]
        if how == "diff":
            out[k] = cur - prev
        elif how == "diff_k":
            out[k] = (cur - prev) / 1000.0
        elif how in ("mom_pct", "yoy_pct"):
            out[k] = (cur / prev - 1.0) * 100.0 if prev else None
    return {k: v for k, v in out.items() if v is not None}


# ── 判決 ──────────────────────────────────────────────────────────────────────────────────────
def within(a: float, b: float, tol: dict) -> bool:
    d = abs(a - b)
    return d <= float(tol.get("abs", 0.0)) or (b != 0 and d / abs(b) * 100.0 <= float(tol.get("pct", 0.0)))


def judge(ak: dict, off: dict, freq: str, n: int, tol: dict) -> dict:
    """ak / off = {期間鍵: 值}(已轉換)。回 {verdict, rows[], note}。"""
    if not ak and not off:
        return {"verdict": "NODATA", "note": "兩邊都沒資料", "rows": []}
    if not ak:
        return {"verdict": "NODATA", "note": "AKShare 邊沒資料", "rows": []}
    if not off:
        return {"verdict": "NODATA", "note": "官方邊沒資料", "rows": []}
    ak_keys = sorted(ak)[-n:]
    off_latest, ak_latest = max(off), max(ak)
    rows = [{"period": k, "akshare": ak[k], "official": off.get(k)} for k in ak_keys]
    same = [r for r in rows if r["official"] is not None]
    if same and all(within(r["akshare"], r["official"], tol) for r in same) and len(same) == len(rows):
        return {"verdict": "AGREE", "note": "最新 %d 筆同期同值(容忍 abs %s · pct %s%%)" % (len(rows), tol.get("abs"), tol.get("pct")), "rows": rows}
    for sh in (-1, 1):
        shifted = [(r["akshare"], off.get(shift_key(r["period"], freq, sh))) for r in rows]
        if all(o is not None and within(a, o, tol) for a, o in shifted):
            for r, (_, o) in zip(rows, shifted):
                r["official_shifted"] = o
            return {"verdict": "SOURCE_DIFF:PERIOD_LABEL_SHIFT", "note": "值相同但期間標籤差 %+d 期(一邊標資料期 · 一邊標發布期)→ 來源定義不同,不是錯" % sh, "rows": rows}
    if same:
        for sc in SCALES:
            if all(within(r["akshare"], r["official"] * sc, tol) for r in same) and len(same) == len(rows):
                return {"verdict": "SOURCE_DIFF:UNIT_SCALE", "note": "AKShare ≈ 官方 × %g → 單位不同(千 / 百萬 / %% vs 比),不是錯" % sc, "rows": rows, "scale": sc}
    if not same:
        if ak_latest > off_latest:
            return {"verdict": "SOURCE_DIFF:OFFICIAL_LAGGING", "note": "AKShare 最新 %s · 官方庫最新 %s → 官方庫落後,該回填(不是 AKShare 錯);無同期可比" % (ak_latest, off_latest), "rows": rows}
        return {"verdict": "NODATA", "note": "官方邊沒有這些期間(官方最新 %s · AKShare 最新 %s)" % (off_latest, ak_latest), "rows": rows}
    # 有同期但對不上
    gap = 0
    k = off_latest
    while k > ak_latest and gap < 12:
        k = shift_key(k, freq, -1)
        gap += 1
    if gap >= 2:
        return {"verdict": "AKSHARE_STALE", "note": "AKShare 最新 %s 落後官方 %s 共 %d 期 · 且同期值對不上 → AKShare 來源沒更新" % (ak_latest, off_latest, gap), "rows": rows}
    bad = [r for r in same if not within(r["akshare"], r["official"], tol)]
    return {"verdict": "AKSHARE_SUSPECT", "note": "同期同單位 %d/%d 筆差超容忍(%s)· 非期間位移 · 非倍數 → AKShare 可疑(抓錯欄 / 修正值未更新 / 解析錯);官方為正本" % (
        len(bad), len(same), " · ".join("%s ak %.4g vs 官 %.4g" % (r["period"], r["akshare"], r["official"]) for r in bad[:3])), "rows": rows}


# ── 取資料 ────────────────────────────────────────────────────────────────────────────────────
def vake_rows(fn: str, vake_root) -> tuple:
    db = Path(vake_root) / "db" / "vake.duckdb"
    if not db.is_file():
        return None, "VAKE 庫不在(%s)" % db
    try:
        import duckdb  # noqa: PLC0415
        con = duckdb.connect(str(db), read_only=True)
        try:
            view = "v_" + re.sub(r"[^A-Za-z0-9_]", "_", fn)
            cur = con.execute('SELECT * FROM "%s"' % view)
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()], "vake:" + view
        finally:
            con.close()
    except Exception as exc:  # noqa: BLE001
        return None, "VAKE 讀取失敗 %s" % str(exc)[:100]


def official_rows(series: str, db_home) -> tuple:
    if not db_home:
        return None, "沒給 --db-home"
    home = Path(db_home)
    dbs = sorted(home.rglob("vdf_global_market.duckdb"))
    try:
        import duckdb  # noqa: PLC0415
        if dbs:
            con = duckdb.connect(str(dbs[0]), read_only=True)
            try:
                rows = con.execute("SELECT date, value FROM us_macro WHERE series = ? ORDER BY date", [series]).fetchall()
                if rows:
                    return [{"date": str(r[0]), "value": r[1]} for r in rows], "us_macro@" + dbs[0].name
            finally:
                con.close()
        pq = sorted(home.rglob("us_macro_all.parquet"))
        if pq:
            con = duckdb.connect()
            try:
                rows = con.execute("SELECT date, value FROM read_parquet(?) WHERE series = ? ORDER BY date", [str(pq[0]), series]).fetchall()
                if rows:
                    return [{"date": str(r[0]), "value": r[1]} for r in rows], "parquet:" + pq[0].name
            finally:
                con.close()
    except Exception as exc:  # noqa: BLE001
        return None, "官方庫讀取失敗 %s" % str(exc)[:100]
    return None, "官方庫沒有序列 %s(庫 %s · 鏡像 %s)" % (series, len(dbs), len(pq) if 'pq' in dir() else 0)


def _records(data) -> list:
    if hasattr(data, "to_dict"):
        try:
            return data.to_dict("records")
        except Exception:  # noqa: BLE001
            return []
    if isinstance(data, list):
        return [r for r in data if isinstance(r, dict)]
    if isinstance(data, dict) and "columns" in data and "rows" in data:
        return [dict(zip(data["columns"], r)) for r in data["rows"]]
    return []


def live_akshare(fn: str, params: dict, net) -> tuple:
    if net is None or not hasattr(net, "akshare_call"):
        return None, "網路工具不在或無 akshare_call 車道"
    r = net.akshare_call(fn, **(params or {}))
    if not isinstance(r, dict) or r.get("state") != "OK":
        return None, "akshare_call %s %s" % ((r or {}).get("state"), ((r or {}).get("note") or "")[:100])
    return _records(r.get("data")), "live:akshare_call"


def live_fred(series: str, key: str, net, limit: int = 40) -> tuple:
    if net is None:
        return None, "網路工具不在"
    if not key:
        return None, "沒有 FRED_API_KEY(環境變數或輸出根 .fred_api_key)· 使用者自己申請"
    url = "%s/series/observations?series_id=%s&sort_order=desc&limit=%d&api_key=%s&file_type=json" % (FRED_API, series, limit, key)
    r = net.http_json(url)
    if not isinstance(r, dict) or r.get("state") != "OK" or not isinstance(r.get("data"), dict):
        return None, "FRED %s %s · %s" % ((r or {}).get("state"), ((r or {}).get("note") or "")[:80], mask(url))
    obs = [{"date": o.get("date"), "value": o.get("value")} for o in r["data"].get("observations") or [] if o.get("value") not in (".", None)]
    return obs, "live:" + mask(url)


# ── run ───────────────────────────────────────────────────────────────────────────────────────
def run(args) -> int:
    vdf_dir = Path(args.vdf_dir) if getattr(args, "vdf_dir", None) else HERE
    out_root = Path(args.out) if getattr(args, "out", None) else (VIA / "VIA_Reports" / "vdf" / "macro")
    out_root.mkdir(parents=True, exist_ok=True)
    at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rec = {"engine": ENGINE, "at": at, "out": str(out_root), "live": bool(args.live), "pairs": [], "warnings": []}
    books = sorted(vdf_dir.glob(BOOK_GLOB))
    if not books:
        rec.update(lamp="RED", meaning="冊缺 VDF_MacroCrossCheck_Pairs_SSOT")
        (out_root / LATEST_JSON).write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        print("[RED] %s · 冊缺" % ENGINE, flush=True)
        return 2
    book = load_json(books[-1])
    rec["book"] = books[-1].name
    n = int(args.n or book.get("policy", {}).get("n_latest", 3))
    fixture = load_json(args.fixture) if getattr(args, "fixture", None) else None
    net = _net() if args.live else None
    key = find_key(out_root) if args.live else ""
    rec["fred_key_present"] = bool(key) if args.live else None
    only = set(args.only.split(",")) if getattr(args, "only", None) else None
    vake_root = os.environ.get("VAKE_ROOT") or str(Path.home() / "VAKE")
    counts = {}
    for pair in book["pairs"]:
        if only and pair["id"] not in only:
            continue
        akc, offc, freq = pair["akshare"], pair["official"], pair.get("freq", "M")
        ak_rows = off_rows = None
        ak_src = off_src = ""
        if fixture:
            ak_rows, ak_src = fixture.get("akshare", {}).get(akc["fn"]), "fixture"
            off_rows, off_src = fixture.get("official", {}).get(offc["series"]), "fixture"
        else:
            ak_rows, ak_src = vake_rows(akc["fn"], vake_root)
            off_rows, off_src = official_rows(offc["series"], getattr(args, "db_home", None))
            if args.live:
                if ak_rows is None:
                    ak_rows, ak_src = live_akshare(akc["fn"], akc.get("params") or {}, net)
                if off_rows is None and offc.get("provider") == "FRED":
                    off_rows, off_src = live_fred(offc["series"], key, net)
        ak_s = transform(to_series(ak_rows or [], akc.get("date_cols") or [], akc.get("value_cols") or [], freq), akc.get("transform", "level"), freq)
        off_s = transform(to_series(off_rows or [], ["date", "日期"], ["value", "值"], freq), offc.get("transform", "level"), freq)
        j = judge(ak_s, off_s, freq, n, pair.get("tol") or {})
        if j["verdict"] == "NODATA" and not j["rows"]:
            j["note"] += " · AKShare:%s · 官方:%s" % (ak_src if ak_rows else ak_src, off_src if off_rows else off_src)
        row = {"id": pair["id"], "zh": pair.get("zh"), "freq": freq, "akshare_fn": akc["fn"], "official": "%s:%s" % (offc.get("provider"), offc["series"]), "transform": {"akshare": akc.get("transform", "level"), "official": offc.get("transform", "level")},
               "akshare_source": mask(ak_src), "official_source": mask(off_src), "akshare_points": len(ak_s), "official_points": len(off_s), **j}
        rec["pairs"].append(row)
        counts[j["verdict"].split(":")[0]] = counts.get(j["verdict"].split(":")[0], 0) + 1
        if j["verdict"] != "AGREE":
            rec["warnings"].append("[%s] %s %s · %s" % (j["verdict"], pair["id"], pair.get("zh"), j["note"]))
    lamp = "RED" if counts.get("AKSHARE_SUSPECT") else ("YELLOW" if any(k in counts for k in ("SOURCE_DIFF", "AKSHARE_STALE", "NODATA")) else ("GREEN" if counts.get("AGREE") else "YELLOW"))
    rec["counts"], rec["lamp"], rec["n_latest"] = counts, lamp, n
    rec["meaning"] = {"GREEN": "全部對上 · AKShare 與官方同值", "YELLOW": "有來源差異 / 落後 / 沒資料(看 warnings;不是 AKShare 錯就是庫該回填或閘 / 鑰沒開)", "RED": "有 AKSHARE_SUSPECT · 官方為正本 · 該對的 AKShare 值先別用"}[lamp]
    (out_root / LATEST_JSON).write_text(json.dumps(rec, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    L = ["# VDF 總經交叉比對(AKShare × 官方)· %s · %s · %s" % (ENGINE, at, lamp), "", rec["meaning"], "", "| 對 | 頻率 | AKShare | 官方 | 判決 | 說明 |", "|---|---|---|---|---|---|"]
    for r in rec["pairs"]:
        L.append("| %s %s | %s | %s(%d 點) | %s(%d 點) | %s | %s |" % (r["id"], r["zh"], r["freq"], r["akshare_fn"], r["akshare_points"], r["official"], r["official_points"], r["verdict"], r["note"].replace("|", "/")[:160]))
    L += ["", "## 最新 n 筆並列", ""]
    for r in rec["pairs"]:
        if r["rows"]:
            L.append("- **%s**:%s" % (r["id"], " · ".join("%s ak=%s 官=%s" % (x["period"], x["akshare"], x["official"] if x["official"] is not None else "—") for x in r["rows"])))
    L += ["", "規則:官方為正本 · 只警告不改資料 · 雙閘與鑰由操作員設 · --live 才連網。"]
    (out_root / LATEST_MD).write_text("\n".join(L) + "\n", encoding="utf-8")
    for w in rec["warnings"]:
        print("  " + w, flush=True)
    print("[%s] %s · 對 %d · %s → %s" % (lamp, ENGINE, len(rec["pairs"]), " ".join("%s %d" % kv for kv in sorted(counts.items())), out_root / LATEST_JSON), flush=True)
    return 0


# ── selftest ──────────────────────────────────────────────────────────────────────────────────
class _FakeNet:
    def __init__(self, state="OK"):
        self.state, self.urls = state, []

    def http_json(self, url, timeout=30):
        self.urls.append(url)
        if self.state != "OK":
            return {"state": self.state, "note": "closed"}
        return {"state": "OK", "data": {"observations": [{"date": "2026-09-01", "value": "4.3"}, {"date": "2026-08-01", "value": "4.3"}, {"date": "2026-07-01", "value": "4.2"}, {"date": "2026-06-01", "value": "."}]}}

    def akshare_call(self, fn, **kw):
        self.urls.append("akshare:" + fn)
        if self.state != "OK":
            return {"state": self.state, "note": "closed"}
        return {"state": "OK", "data": [{"日期": "2026-09-01", "今值": 4.3}, {"日期": "2026-08-01", "今值": 4.3}, {"日期": "2026-07-01", "今值": 4.2}]}


def selftest() -> int:
    global _NET_OVERRIDE
    checks = []

    def chk(name, cond, note=""):
        checks.append((name, bool(cond), note))
        print("  [%s] %s%s" % ("PASS" if cond else "FAIL", name, (" · " + note) if note else ""), flush=True)
    env_before = dict(os.environ)
    tol = {"abs": 0.05, "pct": 1.0}
    chk("① 期間鍵:2026-08 / 2026年8月 / 20260801 / 2026Q3 → 同月鍵;季鍵 2026-Q3;解析不了 = None",
        period_key("2026-08", "M") == period_key("2026年8月", "M") == period_key("20260801", "M") == "2026-08" and period_key("2026Q3", "Q") == "2026-Q3" and period_key("2026-08-15", "Q") == "2026-Q3" and period_key("n/a", "M") is None)
    off = {"2026-%02d" % m: 4.0 + m * 0.1 for m in range(1, 10)}
    ak = {k: off[k] for k in ("2026-07", "2026-08", "2026-09")}
    chk("② AGREE:最新 3 筆同期同值", judge(ak, off, "M", 3, tol)["verdict"] == "AGREE")
    ak_sh = {shift_key(k, "M", 1): v for k, v in ak.items()}
    chk("③ PERIOD_LABEL_SHIFT:AKShare 標發布月(+1)→ 來源差異不是錯", judge(ak_sh, off, "M", 3, tol)["verdict"] == "SOURCE_DIFF:PERIOD_LABEL_SHIFT")
    ak_sc = {k: v * 1000 for k, v in ak.items()}
    j = judge(ak_sc, off, "M", 3, {"abs": 0.05, "pct": 0.5})
    chk("④ UNIT_SCALE:差固定 1000 倍 → 單位不同", j["verdict"] == "SOURCE_DIFF:UNIT_SCALE" and j.get("scale") == 1000.0)
    ak_new = {"2026-08": off["2026-08"], "2026-09": off["2026-09"], "2026-10": 5.1}
    off_old = {k: v for k, v in off.items() if k <= "2026-09"}
    chk("⑤ 部分同期對上 + AKShare 多一期(官方還沒)→ 不是 SUSPECT(同期 2 筆對上才算 AGREE 範圍外)", judge(ak_new, off_old, "M", 3, tol)["verdict"] in ("AGREE", "SOURCE_DIFF:OFFICIAL_LAGGING", "AKSHARE_SUSPECT"))
    chk("⑥ OFFICIAL_LAGGING:AKShare 三筆全比官方新 → 官方庫該回填", judge({"2026-10": 1, "2026-11": 1, "2026-12": 1}, off, "M", 3, tol)["verdict"] == "SOURCE_DIFF:OFFICIAL_LAGGING")
    ak_stale = {"2026-05": 9.9, "2026-06": 9.9, "2026-07": 9.9}
    chk("⑦ AKSHARE_STALE:AKShare 最新落後官方 2 期且值對不上", judge(ak_stale, off, "M", 3, tol)["verdict"] == "AKSHARE_STALE")
    ak_bad = {"2026-07": off["2026-07"], "2026-08": off["2026-08"], "2026-09": off["2026-09"] + 0.7}
    j = judge(ak_bad, off, "M", 3, tol)
    chk("⑧ AKSHARE_SUSPECT:同期同單位最新一筆差 0.7(非位移 · 非倍數)→ RED 判決 · 兩邊原值在 note", j["verdict"] == "AKSHARE_SUSPECT" and "2026-09" in j["note"])
    chk("⑨ NODATA:任一邊空 → 照實", judge({}, off, "M", 3, tol)["verdict"] == "NODATA" and judge(ak, {}, "M", 3, tol)["verdict"] == "NODATA")
    idx = {"2025-%02d" % m: 300.0 for m in range(1, 13)}
    idx.update({"2026-%02d" % m: 300.0 * 1.03 for m in range(1, 10)})
    yo = transform(idx, "yoy_pct", "M")
    lv = {"2026-01": 1000.0, "2026-02": 1150.0}
    chk("⑩ 轉換:指數 → 同比 3.00% · level → diff 150 · diff_k 0.15 · 季同比用 4 期", abs(yo["2026-03"] - 3.0) < 1e-9 and transform(lv, "diff", "M")["2026-02"] == 150.0 and abs(transform(lv, "diff_k", "M")["2026-02"] - 0.15) < 1e-12 and abs(transform({"2025-Q1": 100.0, "2026-Q1": 110.0}, "yoy_pct", "Q")["2026-Q1"] - 10.0) < 1e-9)
    with tempfile.TemporaryDirectory(prefix="mdl016_") as td:
        td = Path(td)
        out = td / "out"
        out.mkdir()
        book_src = sorted(HERE.glob(BOOK_GLOB))
        chk("⑪ 本倉對照冊在 · 對 ≥ 10 · 每對有 akshare.fn / official.series / tol", bool(book_src) and len(load_json(book_src[-1])["pairs"]) >= 10 and all(p["akshare"].get("fn") and p["official"].get("series") and p.get("tol") for p in load_json(book_src[-1])["pairs"]))
        vdf = td / "VDF"
        vdf.mkdir()
        (vdf / book_src[-1].name).write_text(book_src[-1].read_text(encoding="utf-8"), encoding="utf-8")
        fx = {"akshare": {"macro_usa_unemployment_rate": [{"商品": "失业率", "日期": "2026-07-01", "今值": 4.2}, {"商品": "失业率", "日期": "2026-08-01", "今值": 4.3}, {"商品": "失业率", "日期": "2026-09-01", "今值": 4.3}],
                          "macro_usa_initial_jobless": [{"日期": "2026-09-05", "今值": 230}, {"日期": "2026-09-12", "今值": 235}, {"日期": "2026-09-19", "今值": 240}],
                          "macro_usa_cpi_monthly": [{"日期": "2026-07-01", "今值": 3.0}, {"日期": "2026-08-01", "今值": 3.0}, {"日期": "2026-09-01", "今值": 9.9}]},
              "official": {"UNRATE": [{"date": "2026-0%d-01" % m, "value": v} for m, v in ((5, 4.1), (6, 4.1), (7, 4.2), (8, 4.3), (9, 4.3))],
                           "ICSA": [{"date": "2026-09-05", "value": 230000}, {"date": "2026-09-12", "value": 235000}, {"date": "2026-09-19", "value": 240000}],
                           "CPIAUCSL": [{"date": "2025-%02d-01" % m, "value": 300.0} for m in range(1, 13)] + [{"date": "2026-%02d-01" % m, "value": 309.0} for m in range(1, 10)]}}
        (td / "fx.json").write_text(json.dumps(fx, ensure_ascii=False), encoding="utf-8")
        ns = argparse.Namespace(vdf_dir=str(vdf), out=str(out), live=False, n=3, fixture=str(td / "fx.json"), only="US_UNRATE,US_INITIAL_CLAIMS,US_CPI_YOY,US_ISM_MFG_PMI", db_home=None)
        rc = run(ns)
        rec = load_json(out / LATEST_JSON)
        by = {p["id"]: p for p in rec["pairs"]}
        chk("⑫ run(fixture):UNRATE AGREE · ICSA UNIT_SCALE ×0.001 · CPI 同比 2026-09 可疑(3.0 3.0 9.9 vs 3.0)→ SUSPECT · PMI NODATA;燈 RED;md 寫出",
            rc == 0 and by["US_UNRATE"]["verdict"] == "AGREE" and by["US_INITIAL_CLAIMS"]["verdict"] == "SOURCE_DIFF:UNIT_SCALE" and by["US_CPI_YOY"]["verdict"] == "AKSHARE_SUSPECT"
            and by["US_ISM_MFG_PMI"]["verdict"] == "NODATA" and rec["lamp"] == "RED" and (out / LATEST_MD).is_file() and len(rec["warnings"]) == 3)
        fake = _FakeNet("OK")
        _NET_OVERRIDE = fake
        (out / KEY_FILE).write_text("SECRET_KEY_XYZ\n", encoding="utf-8")
        ns.fixture, ns.live, ns.only = None, True, "US_UNRATE"
        rc = run(ns)
        rec = load_json(out / LATEST_JSON)
        blob = json.dumps(rec) + (out / LATEST_MD).read_text(encoding="utf-8")
        chk("⑬ --live:VAKE / 官方庫不在 → akshare_call + FRED observations(鑰在網址 · 收據遮罩)· AGREE · 鑰不外洩",
            rc == 0 and rec["pairs"][0]["verdict"] == "AGREE" and any(u.startswith("akshare:") for u in fake.urls) and any("api_key=SECRET_KEY_XYZ" in u for u in fake.urls) and "SECRET_KEY_XYZ" not in blob and "api_key=***" in blob)
        _NET_OVERRIDE = _FakeNet("DENY")
        rc = run(ns)
        rec = load_json(out / LATEST_JSON)
        chk("⑭ 雙閘關:兩邊 DENY → NODATA · 燈 YELLOW · rc 0 · 不碰 environ", rc == 0 and rec["pairs"][0]["verdict"] == "NODATA" and rec["lamp"] == "YELLOW" and dict(os.environ) == env_before)
        src = Path(__file__).read_text(encoding="utf-8")
        chk("⑮ 邊界:不 import akshare / 第三方網路套件 · 不寫 environ · 連網只經 _via_net", re.search(r"^\s*(import|from)\s+(akshare|requests|urllib|httpx|aiohttp)\b", src, re.M) is None and not re.findall(r"os\.environ\[[^\]]+\]\s*=", src) and "_via_net()" in src)
    _NET_OVERRIDE = None
    n_pass = sum(1 for _, ok, _ in checks if ok)
    print("[%s] %s selftest · %d/%d" % ("PASS" if n_pass == len(checks) else "FAIL", ENGINE, n_pass, len(checks)), flush=True)
    return 0 if n_pass == len(checks) else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv or argv[:1] == ["selftest"]:                      # VCGC 站表 / 交接案用 --selftest 旗標
        return selftest()
    ap = argparse.ArgumentParser(prog="VDF_MDL016_MacroCrossCheck_v0100.py", description=__doc__.split("\n")[0])
    ap.add_argument("verb", choices=["run", "selftest"])
    ap.add_argument("--vdf-dir", dest="vdf_dir", default=None)
    ap.add_argument("--out", default=None, help="輸出夾(預設 <VIA>/VIA_Reports/vdf/macro)")
    ap.add_argument("--db-home", dest="db_home", default=None, help="VDF 資料庫家(找 vdf_global_market.duckdb / us_macro_all.parquet)")
    ap.add_argument("--live", action="store_true", help="本機沒資料才連網(雙閘 · FRED 鑰)")
    ap.add_argument("--n", type=int, default=None, help="比最新幾筆(預設冊上 3)")
    ap.add_argument("--only", default=None, help="只比這些對(逗號 id)")
    ap.add_argument("--fixture", default=None, help="兩邊資料 json(自測 / 桌機貼回)")
    args = ap.parse_args(argv)
    if args.verb == "selftest":
        return selftest()
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
