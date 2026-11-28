#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF_ENG068_ETFConsensusAnalysis v0107 — 薄尾(v0104 / v0106 一字不動):持股改「每檔 ETF 各取自己的最新持股日」

操作員 2026-11-28 定案:「改成各取最新日」。
  v0106 _holdings() 只取全庫 MAX(portfolio_date) 那一天的持股;各檔 ETF 公布持股的日子不一定同一天,
  主機上最新那天只有一檔 ETF 有資料 → 重疊榜(被幾檔 ETF 同時持有)全是 1,自測 ④「首檔被持 ETF 數 ≥ 2」紅。
本版:每檔 ETF 取它自己的最新 portfolio_date;最新日比全體最新日早超過 STALE_DAYS(預設 31 天,可用環境變數
  VIA_ENG068_STALE_DAYS 改)的 ETF 不算(多半是停止公布持股的),照實列出排除幾檔。as-of 改寫成「最早~最晚(各 ETF 最新日)」。
  其餘(共識去重律 · 加權律 · 頁面)照 v0106;換掉的只有 v0106 模組層的 _holdings,analyze / 自測都走本版。
零網路 · 不碰 TA-Lib · 不設同意閘 · 唯讀連庫。
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
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(VDF 全導入令;惰性載入=import 時零網路、零行為變更) =====
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
except Exception:  # noqa: BLE001
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT;網路只認 AegisNexus);缺席回 None(誠實)"""
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

import importlib.util
import os
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAMILY = "VDF_ENG068_ETFConsensusAnalysis"
TAG = "VDF_ENG068_ETFConsensusAnalysis v0107"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0107", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)                 # v0106
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def stale_days() -> int:
    try:
        return max(0, int(os.environ.get("VIA_ENG068_STALE_DAYS", "31")))
    except ValueError:
        return 31


LAST: dict = {}
_ORIG_HOLDINGS = PRIOR._holdings


def _holdings() -> tuple:
    """每檔 ETF 自己的最新 portfolio_date 全持股;太舊(比全體最新早 > STALE_DAYS)的 ETF 不算,照實記。"""
    e = PRIOR._connect_ro(PRIOR.DB_ETF)
    try:
        latest = e.execute("SELECT etf_ticker, MAX(portfolio_date) FROM holdings_daily GROUP BY 1").fetchall()
        if not latest:
            LAST.update(etfs=0, excluded=[], asof="None")
            return "None", []
        days = e.execute("SELECT MAX(TRY_CAST(portfolio_date AS DATE)) FROM holdings_daily").fetchone()[0]
        keep, excluded = [], []
        for etf, d in latest:
            dd = e.execute("SELECT TRY_CAST(? AS DATE)", [str(d)]).fetchone()[0]
            if days is not None and dd is not None and (days - dd).days > stale_days():
                excluded.append((etf, str(d)))
            else:
                keep.append((etf, d))
        rows = []
        for etf, d in sorted(keep, key=lambda x: str(x[0])):
            rows += e.execute(
                "SELECT etf_ticker, etf_name, holding_ticker, holding_name, weight_pct FROM holdings_daily "
                "WHERE etf_ticker = ? AND portfolio_date = ? ORDER BY weight_pct DESC", [etf, d]).fetchall()
    finally:
        e.close()
    ds = sorted(str(d) for _e, d in keep)
    asof = (ds[0] if ds[0] == ds[-1] else f"{ds[0]}~{ds[-1]}(各 ETF 最新日)") if ds else "None"
    LAST.update(etfs=len(keep), excluded=excluded, asof=asof)
    return asof, rows


PRIOR._holdings = _holdings


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:240]) if note and not cond else ""), flush=True)

    print(f"[計] {TAG} 自測開始(本版 4 項 + 前版 {PRIOR_PATH.name} 自測 · 暫存庫 · 零網路)", flush=True)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("T1 加速器真的載到(VIA_ACCEL is not None)· 第 3 行標記 · 網路橋在", VIA_ACCEL is not None
        and src.splitlines()[2] == "# [VIA:ACCEL-BRIDGE:v0111]" and VIA_NET_TOOL_PATH is not None)
    import duckdb
    keep_db = PRIOR.DB_ETF
    with tempfile.TemporaryDirectory(prefix="eng068_v0107_") as td:
        db = Path(td) / "etf.duckdb"
        c = duckdb.connect(str(db))
        c.execute("CREATE TABLE holdings_daily(portfolio_date VARCHAR, etf_ticker VARCHAR, etf_name VARCHAR, holding_ticker VARCHAR,"
                  " holding_name VARCHAR, weight_pct DOUBLE)")
        for r in (("2026-11-27", "00980A", "A", "2330", "x", 9.0), ("2026-11-27", "00980A", "A", "2454", "y", 5.0),
                  ("2026-11-20", "00980A", "A", "9999", "old", 1.0),
                  ("2026-11-26", "00981A", "B", "2330", "x", 8.0), ("2026-11-26", "00981A", "B", "3017", "z", 4.0),
                  ("2026-09-01", "00982A", "C", "2330", "x", 7.0)):
            c.execute("INSERT INTO holdings_daily VALUES (?,?,?,?,?,?)", list(r))
        c.close()
        PRIOR.DB_ETF = db
        try:
            a0, r0 = _ORIG_HOLDINGS()
            a1, r1 = _holdings()
        finally:
            PRIOR.DB_ETF = keep_db
    etfs1 = sorted({r[0] for r in r1})
    chk("T2 重現:舊判法只取全庫最新那一天 → 只剩 1 檔 ETF", a0 == "2026-11-27" and {r[0] for r in r0} == {"00980A"}, (a0, r0))
    chk("T3 本版:每檔各取自己的最新日(A 取 11-27、B 取 11-26;A 舊的 11-20 那列不算)· 太舊的 C(09-01)排除並記下",
        etfs1 == ["00980A", "00981A"] and not any(r[2] == "9999" for r in r1) and LAST["excluded"] == [("00982A", "2026-09-01")]
        and a1 == "2026-11-26~2026-11-27(各 ETF 最新日)", (a1, r1, LAST))
    held = {}
    for r in r1:
        held.setdefault(r[2], set()).add(r[0])
    chk("T4 重疊真的聚合得出來:2330 被 2 檔 ETF 持有", len(held.get("2330", ())) == 2, held)
    rc = PRIOR.selftest() if callable(getattr(PRIOR, "selftest", None)) else 1
    chk("T5 前版 v0106 自測照過(資料在位時 ④ 重疊榜改用本版持股)", rc == 0, rc)
    print(f"[計] {TAG} 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        return selftest()
    rc = PRIOR.main()
    if LAST:
        print(f"[{TAG}] 持股日 {LAST.get('asof')} · 納入 {LAST.get('etfs')} 檔 ETF · 太舊排除 {len(LAST.get('excluded') or [])} 檔"
              + ("(" + ", ".join(f"{e} {d}" for e, d in LAST['excluded'][:8]) + ")" if LAST.get("excluded") else "")
              + f" · 門檻 {stale_days()} 天(VIA_ENG068_STALE_DAYS)")
    return rc


if __name__ == "__main__":
    sys.exit(main())
