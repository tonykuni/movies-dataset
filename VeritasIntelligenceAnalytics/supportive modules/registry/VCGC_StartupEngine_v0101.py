#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC_StartupEngine v0101 — 薄尾(v0100 已鎖在 main,一字不動):典籍檔案鎖 + 暫存檔各自唯一

PR #734 Codex P2:兩個 launch / resume 同時用預設典籍時,兩邊寫同一個 `.tmp`、沒有鎖 →
  一邊 os.replace 丟 FileNotFoundError(在完成回呼裡 → 排程中斷),另一邊的完成被蓋掉 → resume 重跑成功過的擷取。
本版:
  ① journal_lock:同一份典籍一次只准一個 launch / resume(作業系統檔案鎖 fcntl / msvcrt · 不等待);
     初始化 · 每件完成 · 收尾都在鎖裡;被占用 → BUSY rc 2,一件都不跑、不碰典籍。
  ② save_journal:暫存檔名帶 pid + uuid,寫手互不搶;其餘照 v0100(只記完成 · 連前置一起的指紋 · 原子換名)。
其餘全照 v0100(動詞表面 15 個不變;演練 / 混單 / 狀態碼不變)。換的是 v0100 模組全域的 save_journal 與 launch_run,
v0100 的 main 叫到的就是本版。不 import 他系統;零 TA-Lib。
"""
from __future__ import annotations

# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102;樹上沒有就誠實缺席,不另造本體) =====
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
except Exception:  # noqa: BLE001
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import contextlib
import importlib.util
import json
import os
import re
import sys
import tempfile
import threading
import uuid
from pathlib import Path

HERE = Path(__file__).resolve()
FAMILY = "VCGC_StartupEngine"
TAG = "VCGC_StartupEngine v0101"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.parent.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(HERE)), key=_vnum)
if PRIOR_PATH.stem in sys.modules:
    PRIOR = sys.modules[PRIOR_PATH.stem]
else:
    _spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem, PRIOR_PATH)
    PRIOR = importlib.util.module_from_spec(_spec)
    sys.modules[PRIOR_PATH.stem] = PRIOR                 # dataclass 要在 sys.modules 找得到自己的模組
    _spec.loader.exec_module(PRIOR)
_PRIOR_SAVE, _PRIOR_LAUNCH = PRIOR.save_journal, PRIOR.launch_run


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


@contextlib.contextmanager
def journal_lock(path):
    """同一份典籍同一時間只准一個 launch / resume(作業系統檔案鎖 · 不等待)。被占用 → BlockingIOError。"""
    lock = Path(path).with_name(Path(path).name + ".lock")
    lock.parent.mkdir(parents=True, exist_ok=True)
    fh = open(lock, "a+b")
    try:
        try:
            if os.name == "nt":
                import msvcrt
                fh.seek(0)
                msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise BlockingIOError(f"典籍 {path} 正被另一個 launch / resume 使用") from exc
        try:
            yield
        finally:
            if os.name == "nt":
                import msvcrt
                fh.seek(0)
                msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
    finally:
        fh.close()


def save_journal(path, result: dict, verb: str, jobs=None) -> None:
    """同 v0100(只記完成 · 連前置一起的指紋 · 原子換名),但暫存檔名帶 pid + uuid,寫手互不搶。"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    by_name, memo = {j.name: j for j in (jobs or [])}, {}
    marks = {j.name: PRIOR.chain_fingerprint(j, by_name, memo) for j in (jobs or []) if j.name in result["journal"]}
    tmp = path.with_name(f"{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
    try:
        tmp.write_text(json.dumps({"engine": PRIOR.ENGINE_ID, "verb": verb, "journal": result["journal"], "fingerprints": marks,
                                   "failed": result["failed"], "skipped": result["skipped"]}, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def launch_run(verb: str, jobs: list, hw, gated: list, jpath, fail_name=None, runner=None):
    """真清單:整輪(初始化 · 每件完成 · 收尾)在典籍鎖裡跑 v0100 的 launch_run;已被占用 → BUSY rc 2。
    演練清單 / 演練與真任務混單:照 v0100(不讀不寫典籍),不用鎖。"""
    if any(job.rehearsal for job in jobs):
        return _PRIOR_LAUNCH(verb, jobs, hw, gated, jpath, fail_name=fail_name, runner=runner)
    try:
        with journal_lock(jpath):
            return _PRIOR_LAUNCH(verb, jobs, hw, gated, jpath, fail_name=fail_name, runner=runner)
    except BlockingIOError as exc:
        return {"status": "BUSY", "runs": [], "journal": [], "failed": None, "skipped": [], "pending": [], "journal_file": str(jpath),
                "resumed_from": [], "stale_journal_names": [], "rehearsal": False, "note": f"{exc};這輪一件都沒跑"}, 2


def install() -> None:
    PRIOR.save_journal = save_journal                    # v0100 的 launch_run / 完成回呼查模組全域 → 用本版
    PRIOR.launch_run = launch_run                        # v0100 的 main 查模組全域 → 用本版


def _restore() -> None:
    PRIOR.save_journal, PRIOR.launch_run = _PRIOR_SAVE, _PRIOR_LAUNCH


def selftest() -> list:
    """先照 v0100 原樣跑它的整套自測(本版還沒換任何全域),再跑本版 4 條。回傳與 v0100 同格式的列。"""
    _restore()
    try:
        prior_rows = PRIOR.selftest()
    finally:
        install()
    rows = []
    check = PRIOR._check
    ok_run = lambda job: {"name": job.name, "ok": True, "rc": 0, "why": ""}   # noqa: E731
    hw = PRIOR.detect_hardware(65536, 16)
    with tempfile.TemporaryDirectory(prefix="vcgc_se101_") as d:
        d = Path(d)
        cj, errs = d / "conc.json", []

        def writer(tag):
            for k in range(40):
                try:
                    save_journal(cj, {"journal": [f"{tag}{k}"], "failed": None, "skipped": []}, "launch", [])
                except Exception as exc:                 # noqa: BLE001
                    errs.append(repr(exc))
        ts = [threading.Thread(target=writer, args=(t,)) for t in "ab"]
        for t in ts:
            t.start()
        for t in ts:
            t.join()
        left = [p.name for p in d.glob("conc.json.*.tmp")]
        check("① 兩個寫手同時寫典籍 80 次:暫存檔各自唯一 · 不丟例外 · 不留暫存檔", not errs and not left and cj.is_file(),
              f"例外 {errs[:2]} · 殘留 {left[:2]}", rows)
        bj, ran = d / "busy.json", []
        with journal_lock(bj):
            busy, busy_rc = PRIOR.launch_run("launch", [PRIOR.Job("B_real", ["python", "-c", "b"], 100, "VCGC")], hw, [], bj,
                                             runner=lambda job: ran.append(job.name) or ok_run(job))
        check("② 同一份典籍已有人在跑:經 v0100 的入口(模組全域)也是 BUSY rc 2 · 一件都不跑 · 不碰典籍",
              busy["status"] == "BUSY" and busy_rc == 2 and ran == [] and not bj.exists(), f"{busy['status']} rc {busy_rc} · 跑了 {ran}", rows)
        fj = d / "free.json"
        full, full_rc = PRIOR.launch_run("launch", [PRIOR.Job("F_real", ["python", "-c", "f"], 100, "VCGC")], hw, [], fj, runner=ok_run)
        again, again_rc = PRIOR.launch_run("resume", [PRIOR.Job("F_real", ["python", "-c", "f"], 100, "VCGC")], hw, [], fj, runner=ok_run)
        check("③ 沒人占用:照常 COMPLETE rc 0、寫典籍;鎖放掉後 resume 讀得到、0 件重跑",
              full["status"] == "COMPLETE" and full_rc == 0 and again["resumed_from"] == ["F_real"] and again["runs"] == [] and again_rc == 0,
              f"{full['status']} rc {full_rc} · resume 抵掉 {again['resumed_from']} · 跑 {len(again['runs'])}", rows)
    src = HERE.read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    check("④ 檔面:加速器橋 · 零 TA-Lib · 不 import 他系統 · 前版 v0100 原封不動(本版只換模組全域)",
          "[VIA:ACCEL-BRIDGE:v0100]" in src and not re.search(r"^\s*(?:import|from)\s+(talib|CGC_|VDF_|VRN_|VQG_|VAP_)", body, re.M)
          and PRIOR.save_journal is save_journal and PRIOR.launch_run is launch_run and PRIOR_PATH.name < HERE.name, PRIOR_PATH.name, rows)
    return prior_rows + rows


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    install()
    if a[:1] in (["selftest"], ["test"], ["--selftest"]):
        rows = selftest()
        n_prior = len(rows) - 4
        failed = [r for r in rows if not r["ok"]]
        for row in rows:
            flag = "PASS" if row["ok"] else row.get("lamp", "FAIL")
            print(f"[{flag}] {row['name']} — {row['detail']}")
        mine_ok = sum(1 for r in rows[n_prior:] if r["ok"])
        prior_ok = sum(1 for r in rows[:n_prior] if r["ok"])
        print(f"[計] {TAG} 本版 {mine_ok}/4 · 前版 {PRIOR_PATH.stem} {prior_ok}/{n_prior}")
        print(f"{len(rows) - len(failed)}/{len(rows)}")
        return 1 if failed else 0
    return PRIOR.main(a)


if __name__ == "__main__":
    sys.exit(main())
