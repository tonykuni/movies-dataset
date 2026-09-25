#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v0103（2026-09-25）：全名冊／正確市場、來源 rateDate 與抓取時點分存、完整回包、當年/次年 EPS 對映與同日增量。
VRN_ENG071_CnyesFusion — 鉅亨 FactSet 共識融合引擎(批199;操作員令)
====================================================================
血統:操作員上傳 VIA_CNYES_FactSet_YFinance_Consensus_Fusion_Engine
v0120(4,791 行單體;工作站「卡斷」)→原件收容 references/intake 零
改動;本引擎=統包道輕鑄正主(整合去重:端點知識擷取自原件,網路
一律經 SUP_MDL740 統包唯一正主=非阻塞不卡斷;雙同意閘 fail-closed)。
端點(marketinfo.api.cnyes.com;批199 雲端實測三通):
  targetPrice/{sym}          → 目標價共識(高/低/均/中位/numEst/last)
  estimateProfit/{sym}?type=eps   → 年度 EPS 預估(financialYear 序)
  estimateProfit/{sym}?type=sales → 年度營收預估
落庫:consensus_daily 多源共存 source='CNYES_FACTSET'(與
EXTERNAL_ANALYST/YAHOO_QS 並列;同鍵先刪後插冪等;close=端點 last
現價,upside=target_median/last-1);工作站空庫自舉(mkdir+DDL)。
用法:python3 VRN_ENG071_CnyesFusion_v0101.py run [codes…] |
      --status | --selftest
v0101→v0102(側線 2026-09-24;主線批號由併線的手指定 L25;全景三回第三回實測):自測改在**暫存庫**跑(L17 自測只寫暫存)。
  v0101 自測開 output_hub/mega/vdf_tw_market.duckdb(工作站是資料家接點=正式庫)拿寫鎖、BEGIN 插 TEST71、ROLLBACK——
  不留列,但自測期間正式庫被鎖:日更鏈正在寫庫時自測撞鎖紅,反過來自測持鎖時別步寫不進去。建表挪到交易外
  (暫存空庫的 CREATE 若在 BEGIN 裡會被 ROLLBACK 一起撤,⑧ 會查不到表);+⑩ 靜態釘住「自測不碰正式庫」。
  其餘一字未動;v0101 留作版史 L04。
v0100→v0101(側線 2026-09-23;主線批號由併線的手指定 L25;操作員「VDF 都要導入網路工具 · 逐一引擎邊測邊修正到成功」):
本引擎在 VDF 擷取鏈(consensus 步)裡觸網;網路本來就走統包 SUP_MDL740(自帶 _net 載入 + 雙同意閘),
只是沒掛標準的統包網路工具橋。v0101 由正主清掃器 via_bridge_sweeper.inject_one 掛上標準橋(純增量、零行為變更,L56 ①;
說明文字刻意不寫橋的標記字樣——寫了,標記尺就會把沒掛橋的檔判成已掛,L102 ① 的假綠);
其餘一字不動,v0100 留作版史 L04。
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

import importlib.util
import os
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
DB_TW = VIA / "functional modules" / "VDF" / "output_hub" / "mega" / "vdf_tw_market.duckdb"
NET_DIR = VIA / "supportive modules" / "network"
DEFAULT_CODES = None  # 正式雙所名冊；不再默抓三檔
BASE = "https://marketinfo.api.cnyes.com/mi/api/v1/financialIndicator"



def _store():
    """共識 schema／擷取契約正主 ENG069 尾版。"""
    p = sorted(HERE.glob('VRN_ENG069_ConsensusDB_v*.py'))[-1]
    spec = importlib.util.spec_from_file_location('_consensus_store', p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _net():
    p = sorted(NET_DIR.glob("SUP_MDL740_NetUnified_v*.py"))[-1]
    spec = importlib.util.spec_from_file_location("net740_e71", p)
    m = importlib.util.module_from_spec(spec)
    sys.modules["net740_e71"] = m
    spec.loader.exec_module(m)
    return m


def _get(net, url):
    r = net.http_json(url)
    if (r.get("ok") or r.get("state") == "OK") and isinstance(r.get("data"), dict):
        d = r["data"]
        if d.get("statusCode") == 200:
            return d.get("data")
    return None


def parse_target(d: dict | None) -> dict | None:
    """targetPrice 回包→共識欄(零發明:僅收端點實回值)"""
    if not isinstance(d, dict) or (d.get("feMedian") is None and d.get("feMean") is None):
        return None
    return {"target_high": d.get("feHigh"), "target_low": d.get("feLow"),
            "target_mean": d.get("feMean"), "target_median": d.get("feMedian"),
            "n_analysts": d.get("numEst"), "last": d.get("last"),
            "rate_date": d.get("rateDate")}


def parse_eps(rows: list | None, asof_year: int | None = None) -> dict:
    """estimateProfit eps 列(financialYear 序)→fy0/fy1=最近兩年度
    (年度升冪取前二;缺=None 誠實)"""
    out = {"eps_fy0": None, "eps_fy1": None}
    if not isinstance(rows, list):
        return out
    ys = sorted((r for r in rows if isinstance(r, dict)
                 and r.get("financialYear") and r.get("feMean") is not None),
                key=lambda r: r["financialYear"])
    if asof_year is not None:
        by_year = {int(r["financialYear"]): r["feMean"] for r in ys}
        return {"eps_fy0": by_year.get(asof_year), "eps_fy1": by_year.get(asof_year + 1)}
    if ys:
        out["eps_fy0"] = ys[0]["feMean"]
    if len(ys) > 1:
        out["eps_fy1"] = ys[1]["feMean"]
    return out


def _ensure_schema(con):
    con.execute("""CREATE TABLE IF NOT EXISTS consensus_daily(
        date VARCHAR, code VARCHAR, source VARCHAR,
        target_high DOUBLE, target_low DOUBLE, target_mean DOUBLE,
        target_median DOUBLE, n_analysts BIGINT,
        eps_fy0 DOUBLE, eps_fy1 DOUBLE, adopted_eps DOUBLE,
        close DOUBLE, upside_pct DOUBLE, validated VARCHAR)""")


def upsert(con, date: str, code: str, tp: dict, eps: dict) -> None:
    """同鍵(date,code,source)先刪後插=冪等;close=端點 last 現價"""
    _ensure_schema(con)
    last = tp.get("last")
    upside = (tp["target_median"] / last - 1) if (tp.get("target_median") and last) else None
    con.execute("DELETE FROM consensus_daily WHERE date=? AND code=? AND source='CNYES_FACTSET'",
                [date, code])
    con.execute(
        "INSERT INTO consensus_daily VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [date, code, "CNYES_FACTSET", tp["target_high"], tp["target_low"],
         tp["target_mean"], tp["target_median"], tp["n_analysts"],
         eps["eps_fy0"], eps["eps_fy1"],
         eps["eps_fy1"] if eps["eps_fy1"] is not None else eps["eps_fy0"],
         last, upside, "CNYES_FACTSET_DIRECT"])


def run(codes: list[str] | None = None) -> int:
    if os.environ.get('VIA_NET_CONSENT') != 'YES':
        print('[鉅亨共識] 同意閘未開(VIA_NET_CONSENT≠YES)=拒跑(fail-closed 誠實)')
        return 2
    store = _store()
    universe = store.fetch_universe(DB_TW, codes)
    if not universe or (codes and set(map(str, codes)) - set(universe)):
        print('[鉅亨共識] ABSENT：正式雙所名冊缺席或所選股票沒有交易所對映；零擷取')
        return 3
    day = store.snapshot_day()
    todo = store.pending_codes(DB_TW, universe, 'CNYES_FACTSET', day)
    if not todo:
        print(f'[鉅亨共識] {day} 已查 {len(universe)} 檔；零重抓')
        return 0
    net = _net()
    import duckdb
    con = duckdb.connect(str(DB_TW))
    ok = failed = 0
    try:
        for c in todo:
            sym = ('TWS:' if universe[c]['market'] == 'TWSE' else 'TWO:') + c + ':STOCK'
            urls = [f'{BASE}/targetPrice/{sym}', f'{BASE}/estimateProfit/{sym}?type=eps']
            raw_tp, raw_eps = _get(net, urls[0]), _get(net, urls[1])
            tp = parse_target(raw_tp)
            eps = parse_eps(raw_eps, int(day[:4]))
            # 只取得 EPS 也保存；未取得目標價不編數。空回包未提供可靠無覆蓋碼，保留重試權。
            has_eps = any(v is not None for v in eps.values())
            partial = tp is None or not isinstance(raw_eps, list)
            state = 'OK' if tp is not None and not partial else 'ERROR'
            con.execute('BEGIN')
            try:
                if tp is not None or has_eps:
                    target = tp or dict(target_high=None, target_low=None, target_mean=None,
                                        target_median=None, n_analysts=None, last=None, rate_date=None)
                    upsert(con, day, c, target, eps)
                store.record_observation(con, day=day, code=c, source='CNYES_FACTSET', symbol=sym,
                    urls=urls, payload={'targetPrice': raw_tp, 'estimateProfit': raw_eps},
                    provider_asof=(raw_tp or {}).get('rateDate') if isinstance(raw_tp, dict) else None,
                    state=state)
                con.execute('COMMIT')
            except Exception:
                con.execute('ROLLBACK')
                raise
            ok += state == 'OK'; failed += state == 'ERROR'
        print(f'[鉅亨共識] 全名冊 {len(universe)} · 本輪 {len(todo)} · 完整回包 {ok} · 待補 {failed}')
    finally:
        con.close()
    return 2 if failed else 0


def status() -> int:
    import duckdb
    if not DB_TW.exists():
        print("  [共識庫] 庫缺(誠實;先 run)")
        return 0
    con = duckdb.connect(str(DB_TW), read_only=True)
    try:
        for s, n, mx in con.execute(
                "SELECT source, count(*), max(date) FROM consensus_daily "
                "GROUP BY source ORDER BY source").fetchall():
            print(f"  [{s}] {n:,} 筆 · 最新 {mx}")
    except Exception:
        print("  [共識庫] 未建(誠實)")
    con.close()
    return 0


def selftest() -> int:
    import duckdb
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src = Path(__file__).read_text(encoding="utf-8")
    chk("① 統包唯一網路道+原件收容血統宣告(零自建 http 庫/外部行程)",
        "SUP_MDL740_NetUnified_v*" in src and "references/intake" in src
        and ("import " + "requests") not in src
        and ("sub" + "process") not in src)
    intake = (VIA / "functional modules" / "VRN" / "references" / "intake" /
              "VIA_CNYES_FactSet_YFinance_Consensus_Fusion_Engine_v0120.py")
    chk("② 原件收容在位(4,791 行單體零改動存檔)",
        intake.exists() and len(intake.read_text(encoding="utf-8",
                                                 errors="ignore").splitlines()) > 4000)
    saved = os.environ.pop("VIA_NET_CONSENT", None)
    rc = run(["2330"])
    if saved is not None:
        os.environ["VIA_NET_CONSENT"] = saved
    chk("③ 同意閘 fail-closed(閘未開=拒跑 rc2 零觸網)", rc == 2)
    fx_tp = {"feHigh": 4200.0, "feLow": 2700.0, "feMean": 3232.0,
             "feMedian": 3175.0, "numEst": 34, "last": 2415.0,
             "rateDate": "2026-08-26"}
    tp = parse_target(fx_tp)
    chk("④ targetPrice 剖析(批199 實測回包 fixture:中位 3175×34 分析師)",
        tp is not None and tp["target_median"] == 3175.0
        and tp["n_analysts"] == 34 and tp["last"] == 2415.0)
    eps = parse_eps([{"financialYear": 2027, "feMean": 90.0},
                     {"financialYear": 2026, "feMean": 75.5},
                     {"financialYear": 2029, "feMean": 221.5}])
    chk("⑤ EPS 年度升冪取前二(fy0=最近年度;亂序入列自校)",
        eps == {"eps_fy0": 75.5, "eps_fy1": 90.0})
    chk("⑥ 無共識面=誠實跳過(feMedian 缺→None 不假列)",
        parse_target({"feHigh": 1.0}) is None and parse_eps(None) == {"eps_fy0": None, "eps_fy1": None})
    import tempfile
    _td = tempfile.TemporaryDirectory()
    con = duckdb.connect(str(Path(_td.name) / "tw_selftest.duckdb"))   # v0102:暫存庫(L17);不再拿正式庫寫鎖
    _ensure_schema(con)                                                # 建表在交易外:ROLLBACK 只撤測試列
    con.execute("BEGIN")
    upsert(con, "1900-01-01", "TEST71", tp, eps)
    upsert(con, "1900-01-01", "TEST71", tp, eps)
    n, up = con.execute(
        "SELECT count(*), max(upside_pct) FROM consensus_daily "
        "WHERE code='TEST71' AND source='CNYES_FACTSET'").fetchone()
    chk("⑦ 同鍵冪等+upside=中位/last-1 手算對合",
        n == 1 and abs(up - (3175.0 / 2415.0 - 1)) < 1e-12, f"(upside {up:.4f})")
    con.execute("ROLLBACK")
    left = con.execute(
        "SELECT count(*) FROM consensus_daily WHERE code='TEST71'").fetchone()[0]
    chk("⑧ fixture 零殘留(ROLLBACK 後正表無測試列)", left == 0)
    con.close()
    _td.cleanup()
    boot_sh = (VIA / "supportive modules" / "registry" / "via_boot_update.sh").read_text(encoding="utf-8")
    boot_ps = (VIA / "supportive modules" / "registry" / "via_boot_update.ps1").read_text(encoding="utf-8")
    chk("⑨ 雙載體 boot 接線+紀律宣告(統包正主/不卡斷/fail-closed/冪等)",
        "VRN_ENG071" in boot_sh and "VRN_ENG071" in boot_ps
        and all(k in src for k in ("統包唯一正主", "不卡斷", "fail-closed", "冪等")))
    import inspect as _insp
    chk("⑩ 自測只寫暫存庫(v0102;v0101 開正式庫拿寫鎖,日更鏈寫庫時兩邊互撞)",
        ("connect(str(" + "DB_" + "TW") not in _insp.getsource(selftest))   # 拆字拼:整句寫在自測裡的話,尺會量到自己(初稿就是這樣自紅)
    print(f"  [計] 十檢 OK {10 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 鉅亨 FactSet 共識融合(VRN_ENG071)· 九檢自測(零網路)===")
        return selftest()
    if "--status" in args:
        return status()
    if args and args[0] == "run":
        return run(args[1:] or DEFAULT_CODES)
    return status()


if __name__ == "__main__":
    sys.exit(main())
