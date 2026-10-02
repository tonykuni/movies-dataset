#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL254_ReviewOnePage v0101 — 薄尾:過期判定用未捨入的年齡(自測 ⑥ 收尾後必紅的根因)

實測(2026-10-02 全功能串測 C-onepage 紅,教訓帳同簽名第 5 次):
  v0100 read_source() 先把年齡捨入到 0.1 小時(row["age_h"] = round(..., 1)),再拿捨入值跟時限比。
  自測 ⑥ 用真檔 VIA_Reports/gate/GATE_latest.json、時限 0.0001 小時 —— 收尾閘剛寫過那檔(3 分鐘內)時年齡捨成 0.0,
  0.0 > 0.0001 不成立 → 判「沒過期」→ ⑥ 紅。不是偶發:只要時限小於 0.05 小時,或年齡剛好落在時限上下 3 分鐘內,判定都會錯。
本版只改這一件:年齡照原式算出未捨入值來比時限;row["age_h"] 顯示值照 v0100 捨入(頁面一字不動)。
其餘(燈號口徑 · 來源冊 · 下一步 · 頁面)照 v0100。只收 VCGC。零網路。
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

import importlib.util
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR_PATH = HERE / "CGC_MDL254_ReviewOnePage_v0100.py"
ENGINE = Path(__file__).stem
_spec = importlib.util.spec_from_file_location("CGC_MDL254_ReviewOnePage_prior_v0101", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
_READ_V0100 = PRIOR.read_source


def __getattr__(name: str):
    return getattr(PRIOR, name)


def _exact_age_h_v0101(src: dict, row: dict, now: datetime) -> float | None:
    """照 v0100 同一條時間來源(冊上 time 欄 → 檔案 mtime)算未捨入的年齡(小時)。"""
    d = row.get("_data")
    p = PRIOR.VIA / src["path"]
    if not isinstance(d, dict) or not p.is_file():
        return None
    t = next((PRIOR.parse_time(d.get(k)) for k in src.get("time") or [] if PRIOR.parse_time(d.get(k))), None) or \
        datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
    return (now - t).total_seconds() / 3600


def read_source(src: dict, lamp_map: dict, stale_default: float, head: str, now: datetime) -> dict:
    row = _READ_V0100(src, lamp_map, stale_default, head, now)
    if row.get("age_h") is None:
        return row
    age = _exact_age_h_v0101(src, row, now)
    if age is not None:
        row["stale"] = age > float(src.get("stale_h") or stale_default)
    return row


PRIOR.read_source = read_source          # build() / 前版自測都從前版模組全域取 read_source


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    return PRIOR.main(argv)


def selftest() -> int:
    rc = PRIOR.selftest()
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    chk("⑩ 前版 v0100 自測全過(⑥ 改走本版 read_source)", rc == 0)
    lm = PRIOR.book()["lamp_map"]
    with tempfile.TemporaryDirectory(dir=str(PRIOR.VIA / "VIA_Reports")) as tmp:
        rel = Path(tmp).relative_to(PRIOR.VIA).as_posix()
        now = datetime.now(timezone.utc)
        (Path(tmp) / "fresh.json").write_text(json.dumps({"verdict": "GREEN", "at": now.isoformat()}), encoding="utf-8")
        old = (now - timedelta(minutes=2)).isoformat()
        (Path(tmp) / "twomin.json").write_text(json.dumps({"verdict": "RED", "at": old}), encoding="utf-8")
        src = {"id": "S98", "title": "t", "area": "a", "owner": "o", "lamp": ["verdict"], "time": ["at"]}
        fresh = read_source(dict(src, path=rel + "/fresh.json", stale_h=1), lm, 48, "", now)
        two = read_source(dict(src, path=rel + "/twomin.json", stale_h=0.01), lm, 48, "", now)
        old_rounded = round(2 / 60, 1) > 0.01
    chk("⑪ 剛寫的檔(年齡 0)不過期;2 分鐘前的結果在 0.01 小時(36 秒)時限下判過期 —— 前版捨成 0.0 判不出",
        fresh["stale"] is False and two["stale"] is True and two["age_h"] == 0.0 and not old_rounded,
        (fresh["stale"], two["stale"], two["age_h"]))
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑫ 加速器橋 · 網路橋在;只收 VCGC(照前版 main);不碰 TA-Lib;頁面顯示的 age_h 仍照前版捨入",
        "[VIA:ACCEL-BRIDGE" in text and "[VIA:NET-BRIDGE" in text and "VIA_FROM_VCGC" in PRIOR_PATH.read_text(encoding="utf-8")
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M))
    print(f"[唯一頁 v0101] 自測 {sum(ok)}/{len(ok)}")
    return 0 if rc == 0 and all(ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
