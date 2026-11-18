#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_ENG070_YahooConsensus v0106 — v0105 薄尾(v0105 一字不動):呼叫端設在尾版上的 os / DB_TW / _store / _net 要落到本體。

實錄(2026-11-18 PR 629 的 Windows 檢查「VDF · manager and daily data contracts」:test_via_consensus_daily_v0100 四案紅):
  測試照 v0104 的慣例,在載入的模組上設假環境、暫存庫、假網路(m.os · m.DB_TW · m._store · m._net)再叫 m.run()。
  v0105 只用模組 __getattr__ 轉接前版:這四個名稱落在 v0105 自己身上,本體 v0104 的 run 讀的還是自己的全域,
  → 同意閘看的是真的環境(沒開 → rc 2,四案因此紅)。
  同一個坑在同意閘開著的機器上更糟:本體會去讀真的庫、走真的網路(測試以為自己隔離了,其實沒有)。
修法(只改這一件;同 VDF_ENG089 v0110 的做法):這四個名稱由本版自己持有(呼叫端設它就落在這裡);
  run() / status() / main() 每次進來先把它們寫到本體 v0104,再照 v0105 走。其餘(剖析 · upsert · 冪等 · 多源共存 ·
  網路一律經 SUP_MDL740 統包 · 雙同意閘 fail-closed)全照 v0105。本版不讀真環境的同意閘以外的東西,也不寫它。
VRN-2 自己的引擎;零網路自測;不用 TA-Lib;不寫同意閘。
用法同 v0105:python VRN_ENG070_YahooConsensus_v0106.py run [codes…] | --status | --selftest
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
# [VIA:NET-BRIDGE] 留名:本版不出網;run 的網路照 v0104 經 SUP_MDL740 統包(雙同意閘 fail-closed)

import importlib.util
import re
import sys
from pathlib import Path
from types import SimpleNamespace as _NS

VERSION = "v0106"
TAG = "VRN_ENG070_YahooConsensus " + VERSION
HERE = Path(__file__).resolve().parent
_STEM = "VRN_ENG070_YahooConsensus"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BODY = PRIOR.PRIOR                         # v0104:run / status 在它身上,讀它自己的全域
HELD = ("os", "DB_TW", "_store", "_net")   # 呼叫端會設的四個名稱;本版持有,進門時寫到本體
os, DB_TW, _store, _net = BODY.os, BODY.DB_TW, BODY._store, BODY._net


def __getattr__(name):
    return getattr(PRIOR, name)


def _push() -> None:
    """呼叫端設在本版的值 → 本體 v0104(沒設過就是本體原值,等於沒動)。"""
    g = globals()
    for k in HELD:
        setattr(BODY, k, g[k])


def run(codes=None) -> int:
    _push()
    return BODY.run(codes)


def status() -> int:
    _push()
    return BODY.status()


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""), flush=True)

    print("=== %s 自測(呼叫端設的名稱落到本體;零網路 · 不碰真庫)===" % TAG, flush=True)
    g = globals()
    keep = {k: g[k] for k in HELD}
    real_env = BODY.os.environ.get("VIA_NET_CONSENT")
    chk("① 本體是 v0105 載入的那一份 v0104(run 在它身上)", _vnum(BODY.__file__) == 104 and callable(getattr(BODY, "run", None)), Path(BODY.__file__).name)
    chk("② 沒人設過:四個名稱就是本體原值(行為同 v0105)", all(keep[k] is getattr(BODY, k) for k in HELD))
    seen = {"universe": [], "net": 0}

    def fake_store(universe, pending):
        return lambda: _NS(fetch_universe=lambda db, codes=None: seen["universe"].append(db) or universe,
                           snapshot_day=lambda: "1900-01-01", pending_codes=lambda db, uni, source, day: pending)

    def fake_net():
        seen["net"] += 1
        raise AssertionError("自測不該走到網路")

    try:
        g["DB_TW"], g["_net"] = Path("/__selftest__/none.duckdb"), fake_net
        g["os"], g["_store"] = _NS(environ={}), fake_store({"2330": {"symbol": "2330.TW"}}, ["2330"])
        r3 = run()
        chk("③ 設在本版的假環境沒開同意閘 → 本體拒跑 rc 2,庫與網路都沒碰", r3 == 2 and not seen["universe"] and not seen["net"], r3)
        g["os"], g["_store"] = _NS(environ={"VIA_NET_CONSENT": "YES"}), fake_store({}, [])
        r4 = run(["9999"])
        chk("④ 假環境開閘 + 設在本版的庫與名冊:本體讀到的是呼叫端給的庫;名冊缺 → rc 3,沒碰網路",
            r4 == 3 and seen["universe"] == [Path("/__selftest__/none.duckdb")] and not seen["net"], (r4, seen["universe"]))
        g["_store"] = fake_store({"2330": {"symbol": "2330.TW"}}, [])
        r5 = run()
        chk("⑤ 今天都查過(沒有待補)→ rc 0 零重抓,沒碰網路", r5 == 0 and not seen["net"], r5)
        chk("⑥ 真的行程環境沒被動到(同意閘照舊,本版不寫它)", BODY.os is g["os"] and keep["os"].environ.get("VIA_NET_CONSENT") == real_env)
    finally:
        for k in HELD:
            g[k] = keep[k]
        _push()
    chk("⑦ 還原後本體回到原值", all(getattr(BODY, k) is keep[k] for k in HELD))
    chk("⑧ v0105 的 upsert(取價前先查表)仍裝在本體上", BODY.upsert is PRIOR.upsert)
    try:
        import duckdb
        has_db = True
    except ImportError:
        has_db = False
    skipped = ""
    if has_db:
        import contextlib
        import io
        print("  ── 前版 v0105 自測 ──", flush=True)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = PRIOR.selftest()
        text = buf.getvalue()
        print(text, end="", flush=True)
        fails = [x for x in text.splitlines() if x.strip().startswith("[FAIL]") and "selftest ·" not in x]
        if rc != 0 and fails and all("重現" in x for x in fails):
            # v0105 的 ① 是「重現 v0104 的舊炸法」;那個炸法看 duckdb 版本,這裡沒重現不是壞。其餘項都過才算。
            skipped = " · 另 1 項 SKIP(duckdb %s 沒重現舊炸法)" % duckdb.__version__
            print("  [SKIP] ⑨ 前版 v0105 自測只有「重現舊炸法」那一項沒重現(duckdb %s);它的其餘項都過" % duckdb.__version__, flush=True)
        else:
            chk("⑨ 前版 v0105 自測照過", rc == 0, "rc %s" % rc)
    else:
        skipped = " · 另 1 項 SKIP(沒有 duckdb)"
        print("  [SKIP] ⑨ 前版 v0105 自測要 duckdb,這個環境沒有(缺料不是壞掉;有 duckdb 的環境會跑)", flush=True)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑩ 不用 TA-Lib · 不寫同意閘 · 本版不自建網路", not re.search(r"^\s*(?:import|from)\s+(talib|requests|urllib)", src, re.M)
        and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src))
    n = sum(ok)
    print("[%s] %s selftest · %d/%d%s" % ("PASS" if n == len(ok) else "FAIL", TAG, n, len(ok), skipped), flush=True)
    return 0 if n == len(ok) else 1


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    _push()
    return PRIOR.main()


if __name__ == "__main__":
    sys.exit(main())
