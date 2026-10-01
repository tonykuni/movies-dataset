#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL224_TestAuto v0103 — 薄尾:每一站跑完即落本機暫存檔(CGC_MDL251 進度暫存);中斷 / 記憶體不足後重跑同一指令就接續

操作員(R40 2026-10-01):「增加一個功能 就是記憶體不足有時容易丟進度 善用 temp 檔案放在本機」。
量到的:v0101 每站結果收在記憶體(state dict),整輪(93 站 · 工作站 1240 秒)跑完才寫 TEST_STATE / TEST_latest;
中途 Ctrl+C、行程被砍、記憶體不足當掉 → 已跑完的站全部白跑(沿用只認「上一輪完整寫回」的綠站)。
本尾版只換兩格(前版在自己命名空間呼叫,換掉即生效;盤點 · 指紋 · 沿用 · 燈判 · 紀錄冊 · 報告全照前版):
  ① run:開頭用 CGC_MDL251 開(或接續)一輪進度暫存 —— context = HEAD + 變更中的來源檔 + 這次的參數;正常結束才標完成。
     Ctrl+C / 例外 / 被砍都不標完成 → 下次同一指令、同一份程式 → 接續。報告多 progress 欄(暫存檔 · 接續幾站)。
  ② run_console:每站跑完立刻寫一行(rc · 秒 · 輸出尾 2 萬字 · 當下可用記憶體),fsync 落盤;接續時已跑完的站直接拿結果、
     照寫 log,最後一行照實標「接續:上一輪已跑完這站」(不冒充本輪重跑)。
暫存檔在本機暫存夾 VIA_progress\(VIA_PROGRESS_DIR / VIA_TEMP_ROOT 可指定;不在 OneDrive、不進 git);VIA_PROGRESS=0 = 不接續。
只收 VCGC 呼叫(VIA_FROM_VCGC=YES)的規矩照前一版;零網路;不用 TA-Lib。
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
import json
import os
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = Path(__file__).stem
_STEM = "CGC_MDL224_TestAuto"
VNUM_RX = re.compile(r"[_-]v(\d+)$")


def _vnum(path) -> int:
    m = VNUM_RX.search(Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + ENGINE, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def _load_pj():
    hits = sorted(HERE.glob("CGC_MDL251_ProgressJournal_v*.py"), key=_vnum)
    if not hits:
        return None
    spec = importlib.util.spec_from_file_location("via_progress_journal_for_" + ENGINE, hits[-1])
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


PJ = _load_pj()


def _body():
    m, seen = PRIOR, set()
    while m is not None and id(m) not in seen:
        seen.add(id(m))
        if callable(vars(m).get("run_console")) and callable(vars(m).get("run")) and "fingerprint" in vars(m):
            return m
        m = vars(m).get("PRIOR")
    return None


BODY = _body()
_RC0 = BODY.run_console
_RUN_PRIOR = PRIOR.run                 # v0102 的 run(自開輪號)→ 再進本體
_J: dict = {}
RESUME_MARK = "[進度暫存] 接續:上一輪已跑完這站(結果照錄,本輪沒重跑)"


def __getattr__(name: str):
    return getattr(PRIOR, name)


def run_console(via, console, argv, timeout, log):
    j = _J.get("j")
    key = "console|" + "\x1f".join(str(a) for a in argv)
    hit = j.get(key) if j is not None else None
    if hit is not None:
        out = (hit.get("out") or "") + "\n" + RESUME_MARK
        Path(log).parent.mkdir(parents=True, exist_ok=True)
        Path(log).write_text(out, encoding="utf-8")
        return hit.get("rc"), hit.get("secs", 0.0), out
    rc, secs, out = _RC0(via, console, argv, timeout, log)
    if j is not None:
        j.put(key, {"rc": rc, "secs": secs, "out": (out or "")[-20000:]})
    return rc, secs, out


def run(argv: list, via: Path = BODY.VIA) -> tuple:
    if PJ is None:
        return _RUN_PRIOR(argv, via)
    j = PJ.Journal("TestAuto", scope=via, context=PJ.repo_context(Path(via), "test " + " ".join(argv)))
    j.begin()
    print("  " + PJ.note(j))
    sys.stdout.flush()
    _J["j"] = j
    try:
        card, rc = _RUN_PRIOR(argv, via)
    finally:
        _J.pop("j", None)
    j.finish()                                     # 只有正常回來才標完成;Ctrl+C / 例外 / 被砍 → 下次接續
    card["progress"] = {"journal": str(j.path), "resumed": j.resumed, "attempt": j.attempt}
    return card, rc


BODY.run_console = run_console
BODY.run = run                                     # 本體 main 經模組全域 run → 走本版(本版再進 v0102 → 本體)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        return selftest()
    return PRIOR.main(args)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {ENGINE} · 薄尾自測(逐站落本機暫存 · 中斷接續)===")
    chk("① 進度暫存模組 CGC_MDL251 載得到;本體的站執行格與 run 已換成本版", PJ is not None and BODY.run_console is run_console and BODY.run is run)
    calls = []

    def fake(via, console, argv, timeout, log):
        calls.append(tuple(argv))
        if argv[0] == "boom":
            raise KeyboardInterrupt
        return 0, 0.1, "ok " + argv[0]

    saved_rc, saved_dir = BODY.run_console, os.environ.get("VIA_PROGRESS_DIR")
    global _RC0
    real_rc0 = _RC0
    with tempfile.TemporaryDirectory() as td:
        os.environ["VIA_PROGRESS_DIR"] = td
        _RC0 = fake
        try:
            log = Path(td) / "logs" / "x.txt"
            j = PJ.Journal("TestAutoST", scope=td, context="CTX")
            j.begin()
            _J["j"] = j
            run_console(None, None, ["a"], 1, log)
            run_console(None, None, ["b"], 1, log)
            try:
                run_console(None, None, ["boom"], 1, log)
            except KeyboardInterrupt:
                pass
            _J.pop("j", None)
            calls.clear()
            j2 = PJ.Journal("TestAutoST", scope=td, context="CTX")
            n = j2.begin()
            _J["j"] = j2
            ra = run_console(None, None, ["a"], 1, log)
            text_a = log.read_text(encoding="utf-8")
            rc_ = run_console(None, None, ["c"], 1, log)
            _J.pop("j", None)
            chk("② 中斷(Ctrl+C)後重跑:已跑完的 a · b 接續不重跑,只跑沒跑過的 c;接續的站 log 照寫且標明「接續」",
                n == 2 and calls == [("c",)] and ra[0] == 0 and RESUME_MARK in text_a and rc_[0] == 0, (n, calls))
            j2.finish()
            j3 = PJ.Journal("TestAutoST", scope=td, context="CTX")
            chk("③ 正常跑完標完成 → 下一次重開新一輪(不拿舊結果冒充)", j3.begin() == 0)
            rows = [json.loads(l) for l in j3.path.read_text(encoding="utf-8").splitlines() if l.strip()]
            chk("④ 暫存檔在本機暫存夾(VIA_PROGRESS_DIR 指定處)、不在倉內", str(j3.path).startswith(td) and "VIA_progress" in str(j3.path), j3.path)
        finally:
            _RC0 = real_rc0
            _J.pop("j", None)
            if saved_dir is None:
                os.environ.pop("VIA_PROGRESS_DIR", None)
            else:
                os.environ["VIA_PROGRESS_DIR"] = saved_dir
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑤ 加速器橋 · 網路橋在;不碰 TA-Lib", "VIA:ACCEL-BRIDGE" in src and "VIA:NET-BRIDGE" in src
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M))
    BODY.run, BODY.run_console = PRIOR.run, _RC0          # 前版自測驗的是它自己的裝法(本體 run 是 v0102 那支):先還原,跑完再裝回本版
    try:
        rc = PRIOR.selftest()
    finally:
        BODY.run, BODY.run_console = run, run_console
    chk("⑥ 前版自測跑完後本版換裝還在(站執行格 · run)", BODY.run is run and BODY.run_console is run_console)
    print(f"  [{ENGINE}] 薄尾 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}")
    return rc if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
