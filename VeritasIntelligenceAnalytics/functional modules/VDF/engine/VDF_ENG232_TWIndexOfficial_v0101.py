#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG232_TWIndexOfficial v0101 — 薄尾:增量擷取(不給 --start = 從庫內最新日的下一天接著抓)

操作員(R50 2026-10-02):「輸出PARQUET由DUCKDB管理 增量擷取」。
v0100 的 run 一定要 --start;v0101 起不給 --start 就算增量起點:
  兩個指數(TAIEX · TPEX)各自的 MAX(date) 取較早那個 + 1 天(兩個都要補齊);庫空 / 少一個指數 = 從 BOOT(2023-01-01,
  與 VDF-WKF010 市場清單同一個起日)開始。起點晚於迄日 = 已最新(UP_TO_DATE,零外呼)。
其餘(收容件只讀、網路只經 SUP_MDL740 curl_bytes、同意閘在工具裡、upsert 只增)全沿用 v0100。

用法(經 VCGC;VIA_FROM_VCGC=YES):
  status                                       唯讀:各指數列數 · 最早 · 最新 · 下一個增量起點
  run [--start YYYY-MM-DD] [--end YYYY-MM-DD] [--dry]
  --selftest
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
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import json
import os
import re
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
BOOT = "2023-01-01"
NEED = ("TAIEX", "TPEX")


def _vnum(path) -> int:
    m = re.search(r"_v(\d{4})\.py$", Path(path).name)
    return int(m.group(1)) if m else -1


_ME = _vnum(__file__)
_PRIOR_PATH = max((p for p in HERE.glob("VDF_ENG232_TWIndexOfficial_v*.py") if 0 <= _vnum(p) < _ME), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"_vdf_eng232_prior_{_vnum(_PRIOR_PATH):04d}", _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
ENGINE_TAG = "VDF_ENG232_TWIndexOfficial_v" + Path(__file__).stem.rsplit("_v", 1)[-1]


def __getattr__(name):
    return getattr(PRIOR, name)


def next_start(db: Path | None = None) -> str:
    """增量起點:兩個指數各自 MAX(date) 取較早那個 + 1 天;庫空或少一個指數 = BOOT。"""
    c = PRIOR.count(db or PRIOR.DB_IDX)
    if not all(k in c for k in NEED):
        return BOOT
    lo = min(str(c[k][2])[:10] for k in NEED)
    return (date.fromisoformat(lo) + timedelta(days=1)).isoformat()


def run(start: str | None = None, end: str | None = None, net=None, db: Path | None = None, dry: bool = False) -> dict:
    db = db or PRIOR.DB_IDX
    end = end or date.today().isoformat()
    incremental = not start
    start = start or next_start(db)
    if start > end:
        return {"state": "UP_TO_DATE", "start": start, "end": end, "fetched": 0, "added": 0, "calls": 0,
                "incremental": True, "note": "庫已到最新日;零外呼"}
    r = PRIOR.run(start, end, net=net, db=db, dry=dry)
    r["incremental"] = incremental
    return r


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    if not PRIOR._allowed():
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "只經 VCGC(VIA_FROM_VCGC=YES)"}, ensure_ascii=False))
        return 2
    verb = next((x for x in a if not x.startswith("-")), "status")
    if verb == "status":
        c = PRIOR.count()
        print(f"  [TW 指數] {PRIOR.DB_IDX.name} · {PRIOR.TABLE} · "
              + (" · ".join(f"{k} {n} 列 {lo} → {hi}" for k, (n, lo, hi) in c.items()) or "空")
              + f" · 下一個增量起點 {next_start()}")
        return 0 if c else 2
    if verb == "run":
        r = run(PRIOR._arg(a, "--start"), PRIOR._arg(a, "--end"), dry="--dry" in a)
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return {"OK": 0, "UP_TO_DATE": 0, "DENY": 4, "EMPTY": 2}.get(r["state"], 1)
    print(__doc__)
    return 2


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {ENGINE_TAG} · 薄尾自測(增量起點;零外呼)===")
    os.environ["VIA_ENG232_NOSLEEP"] = "1"
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "idx.duckdb"
        chk("① 庫空 = 從 BOOT 起(2023-01-01)", next_start(db) == BOOT)
        PRIOR._LIB.UTILS.upsert_rows(db, PRIOR.TABLE, [{"date": "2026-09-30", "index_code": "TAIEX", "close": 1.0}], PRIOR.KEYS, counts=True)
        chk("② 少一個指數(只有 TAIEX)= 仍從 BOOT 起(兩個都要補齊)", next_start(db) == BOOT)
        PRIOR._LIB.UTILS.upsert_rows(db, PRIOR.TABLE, [{"date": "2026-09-25", "index_code": "TPEX", "close": 1.0}], PRIOR.KEYS, counts=True)
        chk("③ 兩個都在 = 取較早的最新日 + 1 天", next_start(db) == "2026-09-26", next_start(db))
        net = PRIOR._FakeNet()
        r = run(None, "2026-09-20", net=net, db=db)
        chk("④ 起點晚於迄日 = UP_TO_DATE、零外呼", r["state"] == "UP_TO_DATE" and not net.urls, r["state"])
        r2 = run(None, "2026-10-01", net=PRIOR._FakeNet(), db=db, dry=True)
        chk("⑤ 增量跑把起點交給 v0100(incremental 標記)", r2["start"] == "2026-09-26" and r2["incremental"] is True, (r2["start"], r2["state"]))
        r3 = run("2026-10-01", "2026-10-01", net=PRIOR._FakeNet(), db=db)
        chk("⑥ 給 --start = 照 v0100 原樣(非增量)", r3["incremental"] is False and r3["state"] == "OK", r3["state"])
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑦ 加速器橋 · 網路橋在;不代設同意閘", "VIA:ACCEL-BRIDGE" in src and "VIA:NET-BRIDGE" in src and "VIA_NET_CONSENT\"] =" not in src)
    prior = PRIOR.selftest()
    chk("⑧ 前版自測 PASS", prior == 0)
    good = all(ok)
    print(f"  [計] {ENGINE_TAG} 薄尾 {sum(ok)}/{len(ok)} · {'PASS' if good else 'FAIL'}")
    return 0 if good else 1


if __name__ == "__main__":
    sys.exit(main())
