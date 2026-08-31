#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
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
用法:python3 VRN_ENG071_CnyesFusion_v0100.py run [codes…] |
      --status | --selftest
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

import importlib.util
import os
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
DB_TW = VIA / "functional modules" / "VDF" / "output_hub" / "mega" / "vdf_tw_market.duckdb"
NET_DIR = VIA / "supportive modules" / "network"
DEFAULT_CODES = ["2330", "2317", "2454"]
BASE = "https://marketinfo.api.cnyes.com/mi/api/v1/financialIndicator"


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
    if not isinstance(d, dict) or d.get("feMedian") is None:
        return None
    return {"target_high": d.get("feHigh"), "target_low": d.get("feLow"),
            "target_mean": d.get("feMean"), "target_median": d.get("feMedian"),
            "n_analysts": d.get("numEst"), "last": d.get("last"),
            "rate_date": d.get("rateDate")}


def parse_eps(rows: list | None) -> dict:
    """estimateProfit eps 列(financialYear 序)→fy0/fy1=最近兩年度
    (年度升冪取前二;缺=None 誠實)"""
    out = {"eps_fy0": None, "eps_fy1": None}
    if not isinstance(rows, list):
        return out
    ys = sorted((r for r in rows if isinstance(r, dict)
                 and r.get("financialYear") and r.get("feMean") is not None),
                key=lambda r: r["financialYear"])
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


def run(codes: list[str]) -> int:
    if os.environ.get("VIA_NET_CONSENT") != "YES":
        print("[鉅亨共識] 同意閘未開(VIA_NET_CONSENT≠YES)=拒跑(fail-closed 誠實)")
        return 2
    net = _net()
    import duckdb
    DB_TW.parent.mkdir(parents=True, exist_ok=True)  # 工作站自舉
    con = duckdb.connect(str(DB_TW))
    date = datetime.now().strftime("%Y-%m-%d")
    ok, failed = 0, []
    for c in codes:
        sym = f"TWS:{c}:STOCK"
        tp = parse_target(_get(net, f"{BASE}/targetPrice/{sym}"))
        if tp is None:
            sym = f"TWO:{c}:STOCK"  # 上櫃後備(誠實探測)
            tp = parse_target(_get(net, f"{BASE}/targetPrice/{sym}"))
        if tp is None:
            failed.append(c)
            continue
        eps = parse_eps(_get(net, f"{BASE}/estimateProfit/{sym}?type=eps"))
        upsert(con, date, c, tp, eps)
        print(f"  [OK  ] {c} 目標中位 {tp['target_median']} · 高 {tp['target_high']}"
              f"/低 {tp['target_low']} · 分析師 {tp['n_analysts']}"
              f" · FY0 EPS {eps['eps_fy0']} · 現價 {tp['last']}")
        ok += 1
    con.close()
    if failed:
        print(f"  [FAIL] {'、'.join(failed)}:鉅亨無共識面/缺載=誠實列敗不假數")
    print(f"[鉅亨共識] 成 {ok} · 敗 {len(failed)} · source=CNYES_FACTSET 入 consensus_daily"
          f"(統包道;非阻塞不卡斷;雙同意閘)")
    return 0


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
    con = duckdb.connect(str(DB_TW))
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
    boot_sh = (VIA / "supportive modules" / "registry" / "via_boot_update.sh").read_text(encoding="utf-8")
    boot_ps = (VIA / "supportive modules" / "registry" / "via_boot_update.ps1").read_text(encoding="utf-8")
    chk("⑨ 雙載體 boot 接線+紀律宣告(統包正主/不卡斷/fail-closed/冪等)",
        "VRN_ENG071" in boot_sh and "VRN_ENG071" in boot_ps
        and all(k in src for k in ("統包唯一正主", "不卡斷", "fail-closed", "冪等")))
    print(f"  [計] 九檢 OK {9 - len(fails)} · FAIL {len(fails)}")
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
