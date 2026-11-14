#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN2_OutputStore v0105 — v0104 薄尾(v0104 ~ v0100 一字不改):主題與摘要換成千分位兩位小數後 · 庫裡舊列就地整理成新寫法(不追加)。

操作員 2026-11-03:「數字小數點兩位要有千分位號」→ VRN2_BookSource v0102 把 Combined「TOPIC & SUMMARY」的算法句寫成
「調整後目標價 1,234.50 ÷ 調整後收盤 1,000.00 = 上漲空間 23.45%」。v0104 的規則照用:主題與摘要不算進列雜湊 → 不重複追加;
舊列由同夾最高版 BookSource 的 compose 就地重組(先備份 · restore-fill)→ 換版後庫裡舊列也是新寫法。
本版行為與 v0104 相同;只改兩件:
  ① v0104 的自測情境是照 BookSource v0101 的寫法(18.0%)寫死的 → 本版跑 v0104 自測時,讓它用 v0101(只在自測裡 · 跑完還原)。
  ② 加一段 v0102 情境:舊庫(v0101 寫法)→ 換 v0102 → 0 列追加 · 舊列整理成 1,234.50 / 23.45% 寫法 · 再跑 0 列整理。
動詞同 v0104:sync · fill-source · restore-fill · purge-mops / restore-purge · tidy-summary · --selftest
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import sys
import tempfile
from pathlib import Path

TAG = "v0105"
DISPLAY_NAME = "VRN2_OutputStore"
PRIOR_NAME = "VRN2_OutputStore_v0104.py"
HERE = Path(__file__).resolve().parent


def _load(name: str, alias: str):
    path = HERE / name
    if not path.is_file():
        raise FileNotFoundError("前版 %s 不在 %s" % (name, HERE))
    spec = importlib.util.spec_from_file_location(alias, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PRIOR = _load(PRIOR_NAME, "vrn2_outputstore_prior_v0104")       # v0104(它再載 v0103 → v0102 → v0101 → v0100)
for _name in dir(PRIOR):
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = getattr(PRIOR, _name)
V0103 = PRIOR.PRIOR
V0100 = PRIOR.V0100
V0100.TAG = PRIOR.V0101.TAG = PRIOR.V0102.TAG = V0103.TAG = PRIOR.TAG = TAG + "(v0104 / v0103 / v0102 / v0101 / v0100 薄尾)"
sync = PRIOR.sync
tidy_summary = PRIOR.tidy_summary
read_config = PRIOR.read_config
write_config = PRIOR.write_config


def _booksource(version: str):
    path = HERE / ("VRN2_BookSource_%s.py" % version)
    return V0103._load(path.name, "vrn2_booksource_for_store105_" + version) if path.is_file() else None


# ── 自測 ──────────────────────────────────────────────────────────────────────────────────────────────
def _scenario(eng: str, chk, bs101, bs102) -> None:
    real_engine = V0100._engine
    if eng == "pyarrow":
        V0100._engine = lambda: ("pyarrow", None)
    saved = PRIOR._BS.get("m", None), ("m" in PRIOR._BS)
    try:
        with tempfile.TemporaryDirectory(prefix="vrn2-store105-%s-" % eng) as td:
            root = Path(td)
            v2 = root / "VIA_Reports" / "vrn2"
            (v2 / "output").mkdir(parents=True)
            (v2 / "scope_in").mkdir()
            (v2 / "scope_in" / "a.pdf").write_bytes(b"A")
            out = root / "OneDrive" / "out"
            V0100.write_config(v2, str(out), "selftest")
            PRIOR._books(v2, adj_close="1000")
            PRIOR._BS["m"] = bs101
            bs101.apply(v2)
            with contextlib.redirect_stdout(io.StringIO()):
                sync(v2, None, "r1")                                          # 庫:v0101 寫法(18.0% 這種)
            c1 = V0103._rows_of(out, eng, "Combined")
            PRIOR._BS["m"] = bs102
            bs102.apply(v2)
            book = json.loads((v2 / "output" / "VRN2_Combined_latest.json").read_text(encoding="utf-8"))[0]
            r2 = sync(v2, None, "r2")
            c2 = V0103._rows_of(out, eng, "Combined")
            tidy = r2.get("summary_tidy") or {}
            chk("%s ⑨ v0101 → v0102 換寫法:Combined 0 列追加(仍 %d 列)· 舊列就地整理成 千分位兩位小數 · 與冊上同一段字" % (eng, len(c1)),
                r2["appended"].get("Combined") == 0 and len(c2) == len(c1) == 1 and (tidy.get("changed") or {}).get("Combined") == 1
                and "調整後收盤 1,000.00" in str(c2[0].get(PRIOR.TOPIC)) and str(c2[0].get(PRIOR.TOPIC)) == book[PRIOR.TOPIC] and "調整後收盤 1000 " in str(c1[0].get(PRIOR.TOPIC)))
            bs102.apply(v2)
            r3 = sync(v2, None, "r3")
            chk("%s ⑩ 再跑:0 列追加 · 0 列整理(冪等)" % eng, sum(r3["appended"].values()) == 0 and not any(((r3.get("summary_tidy") or {}).get("changed") or {}).values()))
    finally:
        V0100._engine = real_engine
        if saved[1]:
            PRIOR._BS["m"] = saved[0]
        else:
            PRIOR._BS.pop("m", None)


def selftest() -> int:
    bad = []

    def chk(label, cond):
        print(("[PASS] " if cond else "[FAIL] ") + label, flush=True)
        if not cond:
            bad.append(label)
    bs101, bs102 = _booksource("v0101"), _booksource("v0102")
    saved = PRIOR._BS.get("m", None), ("m" in PRIOR._BS)
    if bs101 is not None:
        PRIOR._BS["m"] = bs101                                              # v0104 的情境照 v0101 寫法寫死
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            rc = PRIOR.selftest()
    finally:
        if saved[1]:
            PRIOR._BS["m"] = saved[0]
        else:
            PRIOR._BS.pop("m", None)
    chk("⓪ v0104 自測(含 v0103 → v0100)照過 · 用它寫死的 BookSource v0101 寫法 · %s" % (buf.getvalue().strip().splitlines() or ["—"])[-1][:70], rc == 0)
    chk("⑦b 薄尾:sync / tidy_summary 就是 v0104 的 · 版號 v0105", sync is PRIOR.sync and tidy_summary is PRIOR.tidy_summary and V0100.sync is PRIOR.sync and V0100.TAG.startswith("v0105"))
    engines = []
    if bs101 is None or bs102 is None:
        print("[SKIP] 同夾沒有 BookSource v0101 + v0102 · 情境 ⑨ ⑩ 不驗", flush=True)
    else:
        eng, _mod = V0100._engine()
        engines = ["duckdb"] if eng == "duckdb" else []
        try:
            import pyarrow.parquet  # noqa: F401,WPS433
            engines.append("pyarrow")
        except ImportError as error:
            print("[SKIP] 這個 Python 的 pyarrow 用不了(%s)· 情境 ⑨ ⑩ 不驗" % type(error).__name__, flush=True)
            engines = []
    for e in engines:
        _scenario(e, chk, bs101, bs102)
    print("[%s] %s %s --selftest · 引擎 %s · 不過 %d" % ("PASS" if not bad else "FAIL", DISPLAY_NAME, TAG, "+".join(engines) or "none", len(bad)), flush=True)
    return 0 if not bad else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv:
        return selftest()
    return PRIOR.main(argv)


if __name__ == "__main__":
    sys.exit(main())
