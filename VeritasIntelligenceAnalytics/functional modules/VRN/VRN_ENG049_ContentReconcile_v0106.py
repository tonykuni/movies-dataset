#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_ENG049_ContentReconcile v0106 — v0105 薄尾(前版一字不動):ADJ CLOSE 改讀 VDF 已對官方的台股日價(只讀互監)

操作員 2026-11-21:「三個都是獨立系統 授權給你做到 … VRN 輸出資料且快且驗證無誤」「輸出驗證」。
容器實跑(VRN 啟動器 MDL260 v0103 · 2026-11-21 07:17–07:21):個股統一矩陣 42 份 ADJ CLOSE 全空 → 全部進不了綠
(12 份只缺 ADJ CLOSE;其餘另缺 目標價 / 評等 / 代號,屬研報抽取)。
根因:v0105 load_vdf 只從 VDF 1-6-FinancialModel/daily_history.parquet 讀「ticker · Adj Close」兩欄;
VDF 那個檔現在是 yf_ticker · Close(而且只收財報範圍的少數檔)→ 一列都對不上。
VDF 另有全市場台股日價 output_hub/mega/vdf_tw_market.duckdb · tw_daily_prices(2026-11-21 起每輪經 VDF_MDL032 對證交所 / 櫃買官方;
close = 官方原始收盤 · adj_close = 還原收盤)。
本版只改一件事:load_vdf 讀完前版之後,還沒有 adj 的代號補:
  ① 台股:tw_daily_prices 每檔最新一天(唯讀開;adj_close,沒有就 close)· 代號去 .TW / .TWO 對 VRN 的代號;
  ② 海外(例 NVDA):FinancialModel daily_history 的新欄位 yf_ticker · Close(每檔最新一天)。
前版已讀到的 adj 不蓋;VDF 庫不在 / 被鎖 → 照前版(不猜、不出網)。其餘(矩陣欄位 · 燈 · 推算 · 頁)全照 v0105。
只讀 VDF 的檔,不改 VDF 任何檔(L123 互不干涉 · 互相只讀)。零網路;不用 TA-Lib;不寫同意閘。
用法同 v0105:matrix [--vdf-dir D] … · --selftest
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
# [VIA:NET-BRIDGE] 留名:本版不出網
import importlib.util
import re
import sys
import tempfile
from pathlib import Path

VERSION = "v0106"
HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
STEM = "VRN_ENG049_ContentReconcile"
TW_DB_REL = Path("output_hub") / "mega" / "vdf_tw_market.duckdb"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
_LOAD_V0105 = PRIOR.load_vdf


def __getattr__(name):
    return getattr(PRIOR, name)


def _key(t) -> str:
    return re.sub(r"\.(TW|TWO)$", "", str(t or "").strip().upper())


def tw_latest(vdf_dir: Path) -> dict:
    """{代號: (日期, 價)} —— VDF 台股日價每檔最新一天(唯讀;庫不在 / 被鎖 = {})。"""
    db = Path(vdf_dir) / TW_DB_REL
    if not db.is_file():
        return {}
    try:
        import duckdb
        con = duckdb.connect(str(db), read_only=True)
    except Exception:
        return {}
    try:
        rows = con.execute("""SELECT ticker, CAST(date AS VARCHAR), coalesce(adj_close, close) FROM (
            SELECT ticker, date, adj_close, close, row_number() OVER (PARTITION BY ticker ORDER BY date DESC) rn
            FROM tw_daily_prices WHERE close > 0) WHERE rn = 1""").fetchall()
    except Exception:
        return {}
    finally:
        con.close()
    return {_key(t): (str(d)[:10], float(v)) for t, d, v in rows if v is not None}


def fm_latest(vdf_dir: Path) -> dict:
    """{代號: (日期, 價)} —— FinancialModel daily_history 新欄位 yf_ticker · Close(每檔最新一天)。"""
    out = {}
    for r in PRIOR._read_table(Path(vdf_dir) / "1-6-FinancialModel" / "daily_history.parquet"):
        t, c, d = _key(r.get("yf_ticker") or r.get("ticker")), PRIOR.num(r.get("Close")), str(r.get("date") or "")[:10]
        if t and c is not None and d >= out.get(t, ("", 0))[0]:
            out[t] = (d, c)
    return out


def load_vdf_v0106(vdf_dir: Path) -> dict:
    out = _LOAD_V0105(vdf_dir)
    for src in (tw_latest(vdf_dir), fm_latest(vdf_dir)):
        for t, dv in src.items():
            s = out.setdefault(t, {"hist": {}})
            if not s.get("adj"):
                s["adj"] = dv
    return out


PRIOR.load_vdf = load_vdf_v0106                   # v0105 matrix 以模組全域叫 load_vdf


def main() -> int:
    if sys.argv[1:2] == ["--selftest"]:
        return selftest()
    return PRIOR.main()


def selftest() -> int:
    import duckdb
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    PRIOR.load_vdf = _LOAD_V0105
    try:
        rc0 = PRIOR.selftest()
    finally:
        PRIOR.load_vdf = load_vdf_v0106
    print(f"=== {STEM} {VERSION} · 薄尾自測(ADJ CLOSE 讀 VDF 已對官方的台股日價)===")
    chk("⓪ 前版 v0105 自測過", rc0 == 0, f"rc {rc0}")
    with tempfile.TemporaryDirectory(prefix="vrn049_v0106_") as td:
        vd = Path(td) / "dict"
        db = vd / TW_DB_REL
        db.parent.mkdir(parents=True)
        con = duckdb.connect(str(db))
        con.execute("CREATE TABLE tw_daily_prices(date VARCHAR, ticker VARCHAR, open DOUBLE, high DOUBLE, low DOUBLE, close DOUBLE, adj_close DOUBLE, volume DOUBLE)")
        con.executemany("INSERT INTO tw_daily_prices VALUES (?, ?, 1, 1, 1, ?, ?, 1)",
                        [("2026-11-19", "2330.TW", 2400, 2390), ("2026-11-20", "2330.TW", 2405, 2405), ("2026-11-20", "6488.TWO", 410, None),
                         ("2026-11-20", "1111.TW", 0, 0)])
        con.close()
        fm = vd / "1-6-FinancialModel"
        fm.mkdir(parents=True)
        try:
            import pandas as pd
            pd.DataFrame([{"date": "2026-11-19", "Close": 180.0, "yf_ticker": "NVDA"}, {"date": "2026-11-20", "Close": 182.5, "yf_ticker": "NVDA"}]
                         ).to_parquet(fm / "daily_history.parquet")
            have_pq = True
        except Exception:
            have_pq = False
        old = _LOAD_V0105(vd)
        new = load_vdf_v0106(vd)
        chk("① 重現:前版只讀 FinancialModel 舊欄位(ticker · Adj Close)→ 新版 VDF 檔一檔 adj 都沒有",
            not any(v.get("adj") for v in old.values()), {k: v.get("adj") for k, v in old.items()})
        chk("② 台股:取 tw_daily_prices 每檔最新一天 adj_close(2330 → 2026-11-20 2405)· adj 空 → close(6488 → 410)· close ≤ 0 不取",
            new.get("2330", {}).get("adj") == ("2026-11-20", 2405.0) and new.get("6488", {}).get("adj") == ("2026-11-20", 410.0)
            and not new.get("1111", {}).get("adj"), {k: new.get(k, {}).get("adj") for k in ("2330", "6488", "1111")})
        chk("③ 海外:FinancialModel 新欄位 yf_ticker · Close → NVDA 2026-11-20 182.5" + ("" if have_pq else "(本機沒有 parquet 寫入器 · 略)"),
            (not have_pq) or new.get("NVDA", {}).get("adj") == ("2026-11-20", 182.5), new.get("NVDA"))
        pre = {"2330": {"hist": {}, "adj": ("2026-11-18", 1.0)}}
        keep = PRIOR.load_vdf
        orig = globals()["_LOAD_V0105"]
        globals()["_LOAD_V0105"] = lambda d: {k: dict(v) for k, v in pre.items()}
        try:
            mixed = load_vdf_v0106(vd)
        finally:
            globals()["_LOAD_V0105"] = orig
            PRIOR.load_vdf = keep
        chk("④ 前版已讀到的 adj 不蓋(2330 仍 2026-11-18 1.0)", mixed["2330"]["adj"] == ("2026-11-18", 1.0), mixed["2330"])
        chk("⑤ VDF 庫不在 → 照前版(不猜)", tw_latest(Path(td) / "nohome") == {} and fm_latest(Path(td) / "nohome") == {})
        rows = PRIOR.build_matrix([], {}, new, [2026, 2027, 2028], __import__("datetime").date(2026, 11, 21), [])
        chk("⑥ 換裝:v0105 matrix 叫到的 load_vdf = 本版 · build_matrix 照前版可跑", PRIOR.load_vdf is load_vdf_v0106 and isinstance(rows, dict))
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    chk("⑦ 加速器橋在 · 網路橋留名(本版不出網);不碰 TA-Lib;不寫同意閘;不寫 VDF 的檔",
        "[VIA:ACCEL-BRIDGE" in src and "[VIA:NET-BRIDGE" in src and not re.search(r"^\s*(import|from)\s+(talib|requests|urllib)", body, re.M)
        and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", body) and "read_only=True" in body)
    names = [n for n in dir(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n, None))]
    chk("⑧ 尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in names), f"{len(names)} 支")
    print(f"  [計] {STEM} {VERSION} 本版 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
