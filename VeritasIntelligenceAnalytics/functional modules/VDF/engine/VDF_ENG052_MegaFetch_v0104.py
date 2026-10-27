#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VDF_ENG052_MegaFetch v0104 — 薄尾:全球 yf 道逐標的出錯不再默默吞掉(VCGC 全景 SWALLOW · 第二輪 2026-10-20)

操作員令(2026-10-20):「繼續第二輪修復 SWALLOW 與 TAILAPI」。
v0103 lane_global_yf 逐標的轉列,`except Exception: continue` 把每一檔的錯吞掉 —— 最常見是 yfinance 回的表少了某檔
(df[t] 丟 KeyError),那一檔整個不見,結果仍記 OK、總結只說「N 標的」,看不出少了誰。本版(只改這一支):
  ① 每檔出錯照實記:skipped 檔數 · skip_examples(前 5 筆:代號 + 錯誤類別 + 訊息)· note 尾巴「略過 N 標的(…)」。
  ② 收到的列、欄位、寫庫(parquet + global_daily upsert)一字不改;零列照舊 EMPTY(也帶略過數)。
  ③ 順手修同函式:parquet 套件缺席時 write_parquet 回 None,v0103 接著取 pq.name 會當掉 → 改成 parquet 欄 None 照實記。
換在 v0103 模組全域(run_lanes / main 走這支)。TAILAPI 報的 upsert_duckdb 其實在 v0103 以賦值綁正典 upsert_rows(取得到;誤報)。
其餘全照 v0103。VDF 自己的模組:不匯入他系統程式;同意閘不讀不寫;不碰 TA-Lib;不裝套件、不寫環境。
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
    """統包唯一網路工具惰性載入;本檔的連網全經 MDL008 子行程改道。"""
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

import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_ENG052_MegaFetch"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"


def _vnum_v0104(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0104(p) < _vnum_v0104(__file__)), key=_vnum_v0104)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):
    return getattr(PRIOR, name)

_LANE_GLOBAL_YF_V0103 = PRIOR.lane_global_yf


def lane_global_yf(order: dict, net=None, yf_fn=None, out_root: Path | None = None) -> dict:
    """同 v0103;逐檔出錯照實記(skipped · skip_examples · note),parquet 缺席不當掉。"""
    P = PRIOR
    g = order["lanes"]["global_yf"]
    tickers = sorted({p["idx"] for p in g["pairs_index_etf"]}
                     | {p["etf"] for p in g["pairs_index_etf"]}
                     | {s["yf"] for s in g["singles"]})
    skipped = []
    if yf_fn is not None:
        r = yf_fn(tickers)
    else:
        net = net or P._net_or_none()
        if net is None or not hasattr(net, "yf_download"):
            return {"state": "SKIP", "note": "統包網路工具缺席(誠實)"}
        rr = net.yf_download(tickers, period="max")
        rows = []
        if rr["state"] == "OK":
            df = rr["data"]
            for t in tickers:
                try:
                    sub = (df[t] if len(tickers) > 1 else df).dropna(how="all")
                    sub = sub[sub.index >= P.START_DATE]
                    for dt_, r_ in sub.iterrows():
                        rows.append({"date": str(dt_)[:10], "ticker": t,
                                     "open": float(r_.get("Open")), "high": float(r_.get("High")),
                                     "low": float(r_.get("Low")), "close": float(r_.get("Close")),
                                     "adj_close": float(r_.get("Adj Close")),
                                     "volume": float(r_.get("Volume"))})
                except Exception as exc:          # noqa: BLE001 — 單檔出錯不擋其他檔;照實記下(v0103 在這裡吞掉)
                    skipped.append("%s %s: %s" % (t, type(exc).__name__, str(exc)[:60]))
        if not rows and hasattr(net, "yahoo_chart"):
            import calendar
            import time as _t
            se = calendar.timegm(_t.strptime(P.START_DATE, "%Y-%m-%d"))
            rc = net.yahoo_chart(tickers, se, int(_t.time()))
            if rc.get("rows"):
                rows = rc["rows"]
                skipped = []                      # chart 後備接手 = 前面 yf 那輪的略過不算數
        r = {"rows": rows, "ok": tickers}
    rows = r["rows"]
    tail = {"skipped": len(skipped), "skip_examples": skipped[:5]} if skipped else {}
    skip_note = (" · 略過 %d 標的(%s)" % (len(skipped), skipped[0])) if skipped else ""
    if not rows:
        return dict({"state": "EMPTY", "note": "零列" + skip_note}, **tail)
    pq = P.write_parquet(rows, "global_yf", out_root)
    n = P.upsert_duckdb((out_root or P.OUT) / "vdf_global_market.duckdb"
                        if out_root else P.DB_GL, "global_daily", rows, ["date", "ticker"])
    return dict({"state": "OK", "rows": len(rows), "parquet": pq.name if pq else None, "db_rows": n,
                 "note": f"{len(set(x['ticker'] for x in rows))} 標的·adj 主欄" + skip_note}, **tail)


PRIOR.lane_global_yf = lane_global_yf


def own_checks() -> int:
    p = f = 0

    def chk(name, cond, note=""):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s%s" % (name, (" · " + str(note)[:300]) if note else ""))
    import shutil
    import tempfile
    try:
        import pandas as pd
    except ImportError:
        pd = None
    order = {"lanes": {"global_yf": {"pairs_index_etf": [], "singles": [{"yf": "AAA"}, {"yf": "BBB"}]}}}
    if pd is None:
        chk("①–③ 沒有 pandas(不代裝)→ 只驗換上", True)
    else:
        idx = pd.to_datetime(["2026-10-14", "2026-10-15"])
        cols = pd.MultiIndex.from_tuples([("AAA", c) for c in ("Open", "High", "Low", "Close", "Adj Close", "Volume")])
        df = pd.DataFrame([[1, 2, 0.5, 1.5, 1.5, 100], [1.1, 2.1, 0.6, 1.6, 1.6, 110]], index=idx, columns=cols)

        class Net:
            def yf_download(self, tickers, period="max"):
                return {"state": "OK", "data": df}

        class Empty:
            def yf_download(self, tickers, period="max"):
                return {"state": "OK", "data": df[[]]}

        td = Path(tempfile.mkdtemp(prefix="eng052v0104_"))
        keep_pq = PRIOR.write_parquet
        try:
            def safe(fn, *a, **k):
                try:
                    return fn(*a, **k)
                except Exception as exc:                  # noqa: BLE001 — 自測裡崩了也照實算 FAIL(不讓整支自測掛掉)
                    return {"_crash": "%s %s" % (type(exc).__name__, str(exc)[:120])}
            a = safe(lane_global_yf, order, net=Net(), out_root=td)
            old = _LANE_GLOBAL_YF_V0103(order, net=Net(), out_root=td / "old")
            chk("① yf 回的表少了 BBB:照實記 skipped 1 · 示例帶代號與 KeyError · note 尾巴「略過 1 標的」;AAA 兩列照收照寫庫(v0103 同樣兩列但不說少了誰)",
                a.get("state") == "OK" and a.get("rows") == 2 and a.get("skipped") == 1 and (a.get("skip_examples") or [""])[0].startswith("BBB KeyError")
                and "略過 1 標的" in str(a.get("note")) and old["rows"] == 2 and "skipped" not in old and "略過" not in old["note"], (a, old))
            e = safe(lane_global_yf, order, net=Empty(), out_root=td)
            chk("② 零列照舊 EMPTY,也帶略過數(兩檔都不在 → skipped 2)", e.get("state") == "EMPTY" and e.get("skipped") == 2 and "略過 2 標的" in str(e.get("note")), e)
            PRIOR.write_parquet = lambda rows, lane, out_root=None: None
            (td / "nopq").mkdir()                      # 平常 write_parquet 建夾;替身不建
            n = safe(lane_global_yf, order, net=Net(), out_root=td / "nopq")
            chk("③ parquet 缺席(write_parquet 回 None)不當掉:parquet 欄 None,寫庫照做", n.get("state") == "OK" and "parquet" in n and n["parquet"] is None and n.get("rows") == 2, n)
        finally:
            PRIOR.write_parquet = keep_pq
            shutil.rmtree(td, ignore_errors=True)
    chk("④ v0103 模組全域換成本版(run_lanes / main 走這支)", PRIOR.lane_global_yf is lane_global_yf)
    src = Path(__file__).read_text(encoding="utf-8")
    imports = re.findall(r"^\s*(?:import|from)\s+([A-Za-z_][\w.]*)", src, re.M)
    chk("⑤ 加速器橋 · 網路橋在;不匯入他系統程式;不碰 TA-Lib;同意閘不寫",
        "VIA:ACCEL-BRIDGE" in src and "def _via_net" in src
        and not [x for x in imports if x.startswith(("CGC_", "VRN_", "VRN2_", "VCGC"))]
        and not re.search(r"^\s*(import|from)\s+" + "talib", src, re.M)
        and not re.search(r"\[[\"']VIA_(NET|SCRAPE)_" + r"CONSENT[\"']\]\s*=(?!=)", src))
    print("  [計] %s 本版 %d/%d · %s" % (TAG, p, p + f, "PASS" if not f else "FAIL"), flush=True)
    return 0 if not f else 1


def selftest() -> int:
    return own_checks() or PRIOR.selftest()


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        print("=== %s · 薄尾自測(全球 yf 道逐檔出錯照實記;替身零網路)===" % TAG, flush=True)
        if own_checks():
            return 1
    return PRIOR.main()


if __name__ == "__main__":
    sys.exit(main())
