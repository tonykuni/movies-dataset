#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""CGC_MDL149_SourceLane v0103 — 薄尾:雙名活檢的貼回包不帶市場數值(資料邊界)

實錄(2026-11-28,PR #775 Codex P1):v0102 把 VDF_ENG102 live() 的整列原樣印進貼回包 —— 收盤價 · 成交量 · 還原價,
交接收據的日誌又照原樣進倉。AGENTS.md §5 / CLAUDE.md:能離開本機的只有程式碼結構與 schema,市場資料不送任何外部模型或代理。
本版(v0102 一字不動):活檢照 v0102 跑(同一支 VDF_ENG102 · 同一支網路工具 · 不開同意閘,閘關著 = fail-closed),
貼回包每列只留 code · symbol · state · overlap · yahoo_volume_used,與「數值欄名單」和「數值的 sha256」(可比對、看不到值);
判燈照 v0102:兩列 state 都是 OK 才 rc 0。
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

import hashlib
import importlib.util
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR_PATH = HERE / "CGC_MDL149_SourceLane_v0102.py"
_spec = importlib.util.spec_from_file_location("cgc_mdl149_sourcelane_v0102_for_v0103", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
KEEP = ("code", "symbol", "state", "note", "overlap", "yahoo_volume_used")


def __getattr__(name):
    return getattr(PRIOR, name)


def redact_row(row: dict) -> dict:
    """只留狀態欄;其餘(價格 · 量 · 任何數值)只交欄名與 sha256。"""
    out = {k: row[k] for k in KEEP if k in row}
    hidden = {k: row[k] for k in row if k not in KEEP}
    if hidden:
        out["values_redacted"] = sorted(hidden)
        out["values_sha256"] = hashlib.sha256(json.dumps(hidden, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    return out


def redact_live(live: dict) -> dict:
    return {**{k: v for k, v in live.items() if k != "rows"}, "rows": [redact_row(r) for r in live.get("rows") or []]}


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print("=== CGC_MDL149_SourceLane v0103 · 自測(零網路 · 合成列)===")
    row = {"code": "1234", "symbol": "1234.TW", "state": "OK", "exchange_close": 12.5, "exchange_volume": 100,
           "yahoo_close": 12.5, "adj_close": 12.4, "overlap": True, "yahoo_volume_used": False}
    r = redact_row(row)
    text = json.dumps(r, ensure_ascii=False)
    chk("① 貼回列只留狀態欄;價格 · 量不出現(只交欄名與 sha256)", "12.5" not in text and "100" not in text and r["state"] == "OK"
        and r["values_redacted"] == ["adj_close", "exchange_close", "exchange_volume", "yahoo_close"] and len(r["values_sha256"]) == 64, text)
    r2 = redact_row(dict(row, exchange_close=13.0))
    chk("② 值變了 sha256 跟著變(可比對、看不到值)", r2["values_sha256"] != r["values_sha256"])
    chk("③ 閘關著的 DENY 列(只有狀態)原樣保留", redact_row({"code": "1", "state": "DENY", "note": "fail-closed"}) == {"code": "1", "state": "DENY", "note": "fail-closed"})
    src = Path(__file__).read_text(encoding="utf-8")
    chk("④ 加速器橋在且執行時載到 · 不碰 TA-Lib · 不設同意閘", "[VIA:ACCEL-BRIDGE" in src and VIA_ACCEL is not None
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src))
    print(f"  [計] CGC_MDL149_SourceLane v0103 自測 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VDF] 拒絕。只能經 via-vcgc。")
        return 2
    mod = _load("src_live", PRIOR.ENG)
    net_path = sorted((PRIOR.VIA / "supportive modules" / "network").glob("via_net_unified_v*.py"))[-1]
    net = _load("via_net", net_path)
    live = mod.live(net)
    body = {"via": "vcgc", "live": redact_live(live), "data_boundary": "市場數值不進貼回包(只留狀態 · 欄名 · sha256)",
            "do_not": ["full-market backfill", "hand-edit the policy book"], "next": "none",
            "logged_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    print("BEGIN_PASTE")
    print(json.dumps(body, ensure_ascii=False, indent=1))
    print("END_PASTE")
    states = [row.get("state") for row in live.get("rows") or []]
    return 0 if states == ["OK", "OK"] else 2


if __name__ == "__main__":
    sys.exit(main())
