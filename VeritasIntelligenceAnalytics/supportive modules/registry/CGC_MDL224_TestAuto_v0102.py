#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL224_TestAuto v0102 — 薄尾:PS 入口版號認得 -vNNNN(PS 入口站不再誤判 ABSENT)

實測(側線 2026-09-30 b 第二段,VCGC-REQ085:ps-entry):唯一入口 Invoke-VIA-OperatorConsole-v0108.ps1 出了之後,
pwsh 實跑 ①g 串測 → P-entry 站 RED「ABSENT Invoke-VIA-OperatorConsole-v*.ps1」。
根因:v0101 的 _vnum 只認 `_vNNNN`(Python 檔的寫法),PS 入口檔名是 `-vNNNN`,newest() 把它當「沒版號」丟掉,
discover() 的 ps 永遠是空字串;v0101 首輪 P-entry 被 pending_until 蓋成「待辦黃」,所以沒露出來。
連帶:紀錄冊 VIA_VCGC_FunctionLedger 從來沒記到 PS 入口的版本與時間(items_now 的 ps 項因為空而跳過)。
  ① 版號同時認 `_vNNNN` 與 `-vNNNN`(只在檔名結尾;沒版號照舊 -1)。換裝進前版,前版的 discover · items_now · run 一起用。
  ② 串測自開輪號:v0101 沿用入口的 VIA_HUB_RUN,75 站經主控台的事件全記進操作台那一輪(go-…),
     結尾 workflow 拿去核 SSOT 順序 → 實測「H3 宣告在 H4 之前,實跑在後」等 6 紅 · 不在冊上的步 61(pwsh 實跑 v0108)。
     本版串測期間 VIA_HUB_RUN 換成自己的 test-…(報告 run),入口那一輪記在報告 hub 欄;跑完原樣還原。
  ③ 其餘照 v0101(盤點冊驅動 · 新 / 缺 · 家族尾版 compile · 沿用 · 紀錄冊只增 · 遞迴防護)。只收 VCGC 呼叫;零網路。
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
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = Path(__file__).stem
_STEM = "CGC_MDL224_TestAuto"
VNUM_RX = re.compile(r"[_-]v(\d+)$")


def _vnum(path) -> int:
    """Version number at the end of a file stem: `_v0101` (Python) or `-v0108` (PowerShell); -1 when there is none."""
    m = VNUM_RX.search(Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + ENGINE, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
PRIOR_ENGINE = PRIOR.ENGINE
PRIOR._vnum = _vnum  # 前版 newest · items_now · run 都經模組全域 _vnum → 一起認 -vNNNN


_PRIOR_RUN = PRIOR.run
HUB = "VIA_HUB_RUN"


def __getattr__(name: str):
    return getattr(PRIOR, name)


def run(argv: list, via: Path = PRIOR.VIA) -> tuple:
    """The chain test runs under its own hub run id, so its station events never land in the caller's go run."""
    parent = os.environ.get(HUB)
    os.environ[HUB] = f"test-{datetime.now():%Y%m%d-%H%M%S}-{os.getpid()}"
    try:
        card, rc = _PRIOR_RUN(argv, via)
    finally:
        if parent is None:
            os.environ.pop(HUB, None)
        else:
            os.environ[HUB] = parent
    card["hub"] = parent or ""
    return card, rc


_PRIOR_RUN_REAL = _PRIOR_RUN
PRIOR.run = run  # 前版 main 經模組全域 run → 走本版


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        return selftest()
    PRIOR.ENGINE = ENGINE  # 報告的 door 記本版
    return PRIOR.main(args)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    got = [_vnum("Invoke-VIA-OperatorConsole-v0108.ps1"), _vnum("CGC_MDL224_TestAuto_v0101.py"),
           _vnum("VIA_Workflow_VCGC_SSOT_v0105.json"), _vnum("Invoke-VIA-OperatorConsole.ps1"), _vnum("x_v0101_old.py")]
    chk("① 版號認 -vNNNN(PS)與 _vNNNN(py / json);沒版號或不在結尾 = -1", got == [108, 101, 105, -1, -1], got)
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        for n in ("Invoke-VIA-OperatorConsole-v0107.ps1", "Invoke-VIA-OperatorConsole-v0108.ps1", "Invoke-VIA-OperatorConsole.ps1"):
            (t / n).write_text("$tArgs = @(\"test\")\n", encoding="utf-8")
        pick = PRIOR.newest(t, "Invoke-VIA-OperatorConsole-v*.ps1")
        items = PRIOR.items_now(t, {"ps": {"operator_console": pick.name if pick else ""}})
        row = items.get("ps:operator_console") or {}
    chk("② 前版 newest 換裝後挑到最新 PS 入口 · 紀錄冊項帶版本 v0108 與 sha16",
        pick is not None and pick.name.endswith("-v0108.ps1") and row.get("version") == "v0108" and len(row.get("sha16", "")) == 16, row)
    via = PRIOR.VIA
    ps_tail = max((p for p in via.glob("Invoke-VIA-OperatorConsole-v*.ps1") if _vnum(p) >= 0), key=_vnum, default=None)
    found = PRIOR.discover(via).get("ps", {}).get("operator_console", "")
    chk("③ 實樹:discover 的 PS 入口 = 樹上最新那支(不再是空字串)", ps_tail is not None and found == ps_tail.name, found or "空")
    inv_path, inv = PRIOR.load_inventory(via)
    st = next((s for s in (inv or {}).get("stations") or [] if s.get("kind") == "ps"), {})
    res = PRIOR.ps_check(via, found, st.get("must") or [])
    chk("④ 實樹 PS 入口站:不是 ABSENT · 串測步在(沒 pwsh 照實黃,有 pwsh 驗語法)",
        not res["last"].startswith("ABSENT") and res["lamp"] in ("GREEN", "YELLOW") and "少了串測步" not in res["last"], res["last"][:80])
    seen, had = {}, os.environ.get(HUB)

    def fake(argv, via):
        seen["run"] = os.environ.get(HUB)
        return {"run": seen["run"]}, 0

    try:
        globals()["_PRIOR_RUN"] = fake
        os.environ[HUB] = "go-20260930-120000-1"
        card, _rc = run([])
        back = os.environ.get(HUB)
        os.environ.pop(HUB, None)
        card2, _rc = run([])
        gone = HUB not in os.environ
    finally:
        globals()["_PRIOR_RUN"] = _PRIOR_RUN_REAL
        if had is None:
            os.environ.pop(HUB, None)
        else:
            os.environ[HUB] = had
    chk("⑤ 串測自開輪號 test-…:站的事件不進入口的 go 輪 · 報告 hub 記入口輪 · 跑完還原(沒有就不留)",
        seen["run"].startswith("test-") and card["hub"] == "go-20260930-120000-1" and back == "go-20260930-120000-1"
        and card2["hub"] == "" and gone and PRIOR.run is run, card)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 加速器橋在 · 不碰 TA-Lib", "VIA:ACCEL-BRIDGE" in src and not re.search(r"^\s*(import|from)\s+talib", src, re.M))
    mine = all(ok)
    PRIOR.ENGINE = PRIOR_ENGINE  # 前版自測照它自己的名字報
    prior_rc = PRIOR.selftest()
    print(f"  {ENGINE} selftest {sum(ok)}/{len(ok)} {'PASS' if mine and prior_rc == 0 else 'FAIL'}(前版 {PRIOR_PATH.stem} rc={prior_rc})")
    return 0 if mine and prior_rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
