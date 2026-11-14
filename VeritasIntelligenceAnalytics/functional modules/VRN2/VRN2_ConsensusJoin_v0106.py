#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN2_ConsensusJoin v0106 — v0105 薄尾(v0105 ~ v0100 一字不改):同意閘未開的輪次用碟上最新共識快照補位 Combined 共識欄(不連外 · 不代設閘)。

操作員 2026-11-02:「開閘共識欄 … 要有共識資料」。同意閘(VIA_NET_CONSENT / VIA_SCRAPE_CONSENT)是操作員的環境變數,VRN-2 不代設、不繞道;
閘關著的輪次引擎 DENY(v0104 起 per_code 會被清空 · v0110 規則「引擎這次沒有產出 → 上次的矩陣不沿用」)→ Combined 共識欄整批空白。
本版在「不沿用」與「全空白」之間補一條寫實的路:
  ① run:前版 run 照跑(引擎照 DENY · 收據照記);只有「net_deny.gate_closed = True(同意閘未開)且 per_code 空」才找碟上快照
     consensus/factset_yfinance_consensus_matrix.csv(引擎上次成功落盤的矩陣 · 本版只讀)→ parse_matrix 補回 per_code,
     收據寫 snapshot_reused{asof(列上最大台北日)· source · codes · why},燈維持 YELLOW、why 明寫「快照補位 · ASOF <日> · 要最新:開閘再 repair」。
     合規 DENY(gate_closed = False · VCGC 的判定)不補位;快照裡沒有這批代號也不補位(原因寫實)。VIA_VRN2_NO_SNAPSHOT=1 關掉本功能。
  ② join:前版 join 照跑;收據有 snapshot_reused → join 收據的 why 也帶同一句(收尾頁 / Workbench 看得到 ASOF)。
  ③ 開閘後的輪次(引擎真抓到 → per_code 是今天的)完全走前版路徑,快照補位不會蓋掉新抓的。
資料日期寫實:補位列的 fetched_at / date 都是快照當天(不是本輪),Combined / 資料集照 v0105 規則落盤。
動詞同 v0105:run · join · --selftest · --engine-shim。
"""
from __future__ import annotations

import csv
import datetime
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile

VERSION = "v0106"
DISPLAY_NAME = "VRN2_ConsensusJoin"
TAG = "共識合併 v0106"
PRIOR_NAME = "VRN2_ConsensusJoin_v0105.py"
HERE = Path(__file__).resolve().parent
SNAPSHOT_OFF = "VIA_VRN2_NO_SNAPSHOT"


def _load(path: Path, alias: str):
    spec = importlib.util.spec_from_file_location(alias, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _prior():
    path = HERE / PRIOR_NAME
    if not path.is_file():
        raise FileNotFoundError("前版 %s 不在 %s" % (PRIOR_NAME, HERE))
    return _load(path, "vrn2_consensus_join_prior_v0105")


PRIOR = _prior()                       # v0105(它再載 v0104 → v0103 → v0102 → v0101 → v0100)
for _name in dir(PRIOR):
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = getattr(PRIOR, _name)
V0104 = PRIOR.PRIOR
V0103, V0102, V0101, V0100 = PRIOR.V0103, PRIOR.V0102, PRIOR.V0101, PRIOR.V0100
for _mod in (PRIOR, V0104, V0103, V0102, V0101, V0100):
    _mod.TAG = TAG
_v0105_run = PRIOR.run                 # = v0104 的 run(v0105 沒改 run)
_v0105_join = PRIOR.join               # v0105 的 join(同步還原 + 資料集)


# ── ① 碟上快照 ───────────────────────────────────────────────────────────────────────────────────────────
def snapshot_state(out: Path) -> dict:
    """consensus/factset_yfinance_consensus_matrix.csv(引擎上次成功落盤 · 只讀)→ {per_code, asof, source}。沒有 / 讀不出列 → {}。"""
    path = Path(out) / V0100.MATRIX_CSV
    if not path.is_file():
        return {}
    try:
        per = V0100.parse_matrix(path)
    except (OSError, csv.Error, UnicodeError):
        return {}
    if not per:
        return {}
    days = sorted(d for d in (PRIOR._taipei_day(str(c.get("fetched_at_utc") or "")) for c in per.values()) if d)
    asof = days[-1].isoformat() if days else datetime.date.fromtimestamp(path.stat().st_mtime).isoformat()
    return {"per_code": per, "asof": asof, "source": str(path)}


def snapshot_fill(rec: dict, out: Path) -> dict:
    """只在「同意閘未開 DENY 且 per_code 空」補位(純函式 · 可測):改 rec 並回它。合規 DENY / 有新抓 / 關掉 / 沒快照 / 代號對不上 → 不動。"""
    if os.environ.get(SNAPSHOT_OFF) == "1":
        return rec
    if not bool((rec.get("net_deny") or {}).get("gate_closed")) or rec.get("per_code"):
        return rec
    snap = snapshot_state(out)
    if not snap:
        rec["snapshot_reused"] = None
        rec["snapshot_note"] = "碟上沒有可用的共識快照(%s)· Combined 共識欄留空" % V0100.MATRIX_CSV
        return rec
    codes = [str(c) for c in (rec.get("codes") or [])]
    got = sorted(c for c in snap["per_code"] if (not codes) or c in codes)
    if not got:
        rec["snapshot_reused"] = None
        rec["snapshot_note"] = "碟上快照(ASOF %s)沒有這批代號 · 不補位" % snap["asof"]
        return rec
    rec["per_code"] = {c: snap["per_code"][c] for c in got}
    rec["codes_got"] = got
    rec["codes_missing"] = sorted(set(codes) - set(got)) if codes else []
    why = ("同意閘未開(操作員決定 · VRN-2 不代設)· 引擎這輪 DENY 沒有新抓 → 先用碟上 ASOF %s 快照補位 Combined 共識欄(%d 檔)"
           "· 要最新共識:開閘後再跑一次(auto = repair)會重抓並蓋掉快照" % (snap["asof"], len(got)))
    rec["snapshot_reused"] = {"asof": snap["asof"], "source": snap["source"], "codes": len(got), "why": why}
    rec["lamp"] = "YELLOW"
    rec["why"] = ("快照補位:%s · 原 DENY:%s" % (why, rec.get("why"))) if rec.get("why") else ("快照補位:%s" % why)   # 補位放最前(收尾列 220 字截斷也看得到)
    return rec


def run(v2: Path, root: Path | None = None, fixtures: list | None = None, timeout: int = 900, engine: str | None = None) -> dict:
    rec = _v0105_run(v2, root, fixtures, timeout, engine)
    out = Path(v2) / "consensus"
    try:
        before = rec.get("snapshot_reused")
        rec = snapshot_fill(rec, out)
        if rec.get("snapshot_reused") and rec["snapshot_reused"] is not before:
            print("    [⑥f] [YELLOW] %s" % rec["snapshot_reused"]["why"], flush=True)
            rec = V0100._finish(out, rec)                                   # 收據重寫一次(帶補位後的 per_code 與 snapshot_reused)
        elif rec.get("snapshot_note"):
            print("    [⑥f] [計] %s" % rec["snapshot_note"], flush=True)
            rec = V0100._finish(out, rec)
    except Exception as error:  # noqa: BLE001  補位失敗不擋收據(照前版的結果走)
        rec["snapshot_error"] = "%s: %s" % (type(error).__name__, str(error)[:160])
    return rec


def join(v2: Path) -> dict:
    got = _v0105_join(v2)
    try:
        cons = V0100._jread(Path(v2) / "consensus" / V0100.CONSENSUS_JSON, {}) or {}
        snap = cons.get("snapshot_reused")
        if isinstance(snap, dict) and snap.get("asof"):
            got["snapshot_reused"] = snap
            note = "共識 = 碟上快照 ASOF %s(同意閘未開 · 非本輪抓)" % snap["asof"]
            got["why"] = ("%s · %s" % (got["why"], note)) if got.get("why") else note
    except Exception as error:  # noqa: BLE001
        got["snapshot_join_note"] = "%s: %s" % (type(error).__name__, str(error)[:120])
    return got


def _wire6(run_fn, join_fn) -> None:
    for mod in (PRIOR, V0104, V0103, V0102, V0101, V0100):
        mod.run, mod.join = run_fn, join_fn


_wire6(run, join)


# ── 自測 ──────────────────────────────────────────────────────────────────────────────────────────────────
_MATRIX_HEAD = ["code", "symbol", "company_name", "fetched_at_utc", "current_price", "target_median", "target_mean", "target_analyst_count",
                "target_rate_date", "yf_target_median", "yf_target_mean", "yf_target_analyst_count", "yf_current_price",
                "eps_2026_median", "eps_2026_forward_pe", "source_agreement_gate", "source_page", "source_yfinance"]


def _matrix_fixture(out: Path, codes: list, asof_utc: str) -> Path:
    """合成快照(形狀同引擎矩陣 · 數字是合成的,不是任何原文 / 桌機值)。"""
    out.mkdir(parents=True, exist_ok=True)
    p = out / V0100.MATRIX_CSV
    with p.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(_MATRIX_HEAD)
        for i, c in enumerate(codes):
            base = 100.0 + 10 * i
            w.writerow([c, "TWS:%s:STOCK" % c, "合成公司%d" % i, asof_utc, base, base * 1.2, base * 1.21, 5 + i,
                        "2026-10-30", base * 1.1, base * 1.12, 7 + i, base, 9.5 + i, 14.0 + i, "PASS", "https://example.invalid/%s" % c, "yfinance"])
    return p


def selftest(engine: str | None = None) -> int:
    fails = []

    def chk(label, cond):
        print("[%s] %s" % ("PASS" if cond else "FAIL", label))
        if not cond:
            fails.append(label)

    chk("① 版鏈:v0106 → 前版 v0105 → v0104 → v0100", VERSION == "v0106" and PRIOR.VERSION == "v0105" and V0104.VERSION == "v0104" and V0100.VERSION == "v0100")
    chk("② 改接:v0100 ~ v0105 的 run / join 都指到 v0106", all(m.run is run and m.join is join for m in (PRIOR, V0104, V0103, V0102, V0101, V0100)))
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "consensus"
        chk("③ 沒快照 → 不補位(原因寫實)", snapshot_state(out) == {} and snapshot_fill({"net_deny": {"gate_closed": True}, "per_code": {}, "codes": ["1101"]}, out).get("snapshot_reused") is None)
        _matrix_fixture(out, ["1101", "2330", "3034"], "2026-11-01T01:19:00+00:00")
        snap = snapshot_state(out)
        chk("④ 快照讀得出:3 檔 · ASOF = 台北 2026-11-01", len(snap.get("per_code") or {}) == 3 and snap.get("asof") == "2026-11-01")
        rec = snapshot_fill({"net_deny": {"gate_closed": True}, "per_code": {}, "codes": ["1101", "2330", "9999"], "why": "VIA 網路工具 DENY(同意閘未開)", "lamp": "YELLOW"}, out)
        chk("⑤ 閘未開 DENY → 補位:per_code 2 檔(交集)· 缺 9999 · snapshot_reused.asof 2026-11-01 · why 帶「快照補位」與「開閘」",
            sorted(rec.get("per_code") or {}) == ["1101", "2330"] and rec.get("codes_missing") == ["9999"]
            and (rec.get("snapshot_reused") or {}).get("asof") == "2026-11-01" and "快照補位" in str(rec.get("why")) and "開閘" in str(rec.get("why")))
        chk("⑥ 補位列的 fetched_at 是快照當天(不是本輪)", str((rec["per_code"]["1101"] or {}).get("fetched_at_utc")) == "2026-11-01T01:19:00+00:00")
        comp = snapshot_fill({"net_deny": {"gate_closed": False, "note": "合規 DENY"}, "per_code": {}, "codes": ["1101"]}, out)
        chk("⑦ 合規 DENY(gate_closed = False · VCGC 的判定)→ 不補位", not comp.get("per_code") and comp.get("snapshot_reused") is None and "snapshot_note" not in comp)
        fresh = snapshot_fill({"net_deny": {"gate_closed": True}, "per_code": {"8069": {"code": "8069"}}, "codes": ["8069"]}, out)
        chk("⑧ 本輪有新抓(per_code 非空)→ 不動", sorted(fresh["per_code"]) == ["8069"] and "snapshot_reused" not in fresh)
        miss = snapshot_fill({"net_deny": {"gate_closed": True}, "per_code": {}, "codes": ["7777"]}, out)
        chk("⑨ 快照沒有這批代號 → 不補位(原因寫實)", miss.get("snapshot_reused") is None and "沒有這批代號" in str(miss.get("snapshot_note")))
        os.environ[SNAPSHOT_OFF] = "1"
        try:
            off = snapshot_fill({"net_deny": {"gate_closed": True}, "per_code": {}, "codes": ["1101"]}, out)
        finally:
            os.environ.pop(SNAPSHOT_OFF, None)
        chk("⑩ VIA_VRN2_NO_SNAPSHOT=1 → 關掉補位", not off.get("per_code") and "snapshot_reused" not in off)
        v2 = Path(td)
        rec2 = dict(rec, yf_ticker_map={"tpex": []}, at="2026-11-02T13:00:00")
        V0100._finish(out, rec2)
        (v2 / "market").mkdir(parents=True, exist_ok=True)
        (v2 / "market" / "VRN2_Market_latest.json").write_text(json.dumps({"per_ticker": {}}, ensure_ascii=False), encoding="utf-8")
        main_rows, est_rows = PRIOR.consensus_rows(v2)
        chk("⑪ consensus_rows 用補位收據出列:2 檔 · date = 快照台北日 2026-11-01 · 兩家中位數在",
            len(main_rows) == 2 and all(r["date"] == datetime.date(2026, 11, 1) for r in main_rows)
            and all(r.get("factset_target_price_median") and r.get("yfinance_target_price_median") for r in main_rows) and len(est_rows) == 4)
    print("[%s] VRN2_ConsensusJoin v0106 自測 %s(%d 項)" % ("GREEN" if not fails else "RED", "全過" if not fails else "不過:%s" % "; ".join(fails), 11))
    return 0 if not fails else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--selftest"]:
        return selftest(argv[1] if len(argv) > 1 else None)
    return PRIOR.main(argv)


if __name__ == "__main__":
    sys.exit(main())
