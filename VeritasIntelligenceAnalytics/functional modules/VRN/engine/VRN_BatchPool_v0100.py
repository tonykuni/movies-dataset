#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
VRN_BatchPool v0100 — 研報整批入庫的平行池(批731;操作員 2026-09-24「PS PY檔案都要依規定裝加速器  剛剛跑好慢」)
======================================================================
工作站實錄:106 份實檔整批入庫(自測迴圈 G06)一檔約 11 秒、全部排在**一顆核心**上跑 20 分鐘——
加速器的橋一直在,但沒有一行碼用到它的執行緒預算。一份報告的擷取(process_one_pdf)只讀不寫,
檔與檔彼此無關,所以整批可以分給幾個工作行程:

  · 工作行程數 = VRN_BATCH_WORKERS(1 = 照舊序跑)> 加速器的執行緒預算 VIA_ACCEL_ACTIVE_THREADS
    (VIA_ACCEL.activate() 設的)> CPU 數 − 1;上限 6;檔數不到 6 份照舊序跑(開一個行程比跑幾份還貴)。
  · 結果依**原本的檔序**交回:落庫的每一列、每一份輸出都跟序跑一樣,只是快。
  · 每個工作行程讀過的附錄小字(小,幾十 KB)一併帶回,放進主行程的快取——自測迴圈接著跑的首頁閘不必重讀。
  · 池開不起來或中途壞掉 → 呼叫端把沒跑完的檔改回序跑,並印一行原因(不擋跑、不假裝)。
  · spawn 起動(Windows 的預設;Linux 也用它,兩邊行為一樣);工作行程的 stdout 丟掉(主行程管主控台),
    錯誤以結果帶回。

律:只讀不寫(寫庫仍在主行程、整批一次);零網路;不設同意閘;尾版律(本件無版號檔名 = 穩定匯入名,
工作行程要能用名字 import 它;內部版號見 POOL_VERSION)。

v0100→v0101(批732;工作站實跑 G06 105 份 2 個行程 675 秒):加速器的執行緒預算在那台機器上是 2(實體核心 ×
記憶體壓力),池照它開 2 個——這是加速器的治理,不是池的錯,池不越權改它。但主控台那一行只印「2 個」,看不出為什麼。
+workers_reason():哪一個設定決定的 · 上限 · 本機邏輯/實體核心 · 怎麼改(VRN_BATCH_WORKERS=N),印在平行池那一行。
======================================================================
"""
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

import concurrent.futures as _cf
import importlib.util
import multiprocessing as _mp
import os
import re
import sys
import traceback
from pathlib import Path

POOL_VERSION = "v0101"
MIN_FILES = 6            # fewer files than this: starting worker processes costs more than it saves
MAX_WORKERS = 6
CORE_MODNAMES = ("vrn_engine_evidence_core",)   # the evidence core both engines share (its appendix cache)
_STATE = {}


def _spawn_safe():
    """Workers start by re-importing the main script (spawn).  That is safe only from the main process and when the
    main script guards its entry point (if __name__ == "__main__") -- otherwise every worker would run the whole
    script again (found in the container: an unguarded test script ran its batch four times).  Unsure = no pool."""
    if _mp.current_process().name != "MainProcess":
        return False
    main_file = getattr(sys.modules.get("__main__"), "__file__", None)
    if not main_file:
        return True                          # python -c / interactive: nothing is re-imported
    try:
        src = Path(main_file).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return bool(re.search(r"""if\s+__name__\s*==\s*['"]__main__['"]""", src))


def workers_for(n_files):
    """Worker processes for a batch of n files (1 = run in this process)."""
    if not _spawn_safe():
        return 1
    wanted = None
    for key in ("VRN_BATCH_WORKERS", "VIA_ACCEL_ACTIVE_THREADS"):
        raw = (os.environ.get(key) or "").strip()
        if raw.isdecimal():                  # not a count (empty, "auto", "-1") -> the next source decides
            wanted = int(raw)
            break
    if wanted is None:
        wanted = (os.cpu_count() or 2) - 1
    if wanted <= 1 or n_files < MIN_FILES:
        return 1
    return max(1, min(wanted, MAX_WORKERS, n_files // 2))


def workers_reason(n_files):
    """v0101 (批732; the workstation ran with 2 because the accelerator's budget said 2): where the number came from,
    in one line -- which setting decided, the caps, and this machine's cores -- so a small pool explains itself."""
    if not _spawn_safe():
        return "本行程序跑(主程式沒有 __main__ 守衛或不在主行程,開池會重跑整支)"
    src = next((f"{k}={os.environ[k].strip()}" for k in ("VRN_BATCH_WORKERS", "VIA_ACCEL_ACTIVE_THREADS")
                if (os.environ.get(k) or "").strip().isdecimal()), f"CPU−1={(os.cpu_count() or 2) - 1}")
    if src.startswith("VIA_ACCEL_ACTIVE_THREADS"):
        src += "(加速器執行緒預算:實體核心 × 記憶體壓力)"
    phys = ""
    try:
        import psutil  # type: ignore
        phys = f" · 實體 {psutil.cpu_count(logical=False)}"
    except Exception:  # noqa: BLE001 -- psutil is optional; logical count still printed
        phys = ""
    return (f"來源 {src} · 本機 邏輯 {os.cpu_count()}{phys} · 上限 {MAX_WORKERS} · 份數÷2={n_files // 2}"
            f" → {workers_for(n_files)};要改:VRN_BATCH_WORKERS=N")


def _init(engine_path, lookups):
    """Runs once in each worker: load the batch engine by path (the parent may hold it under a private name)."""
    import logging
    logging.getLogger("pdfminer").setLevel(logging.ERROR)
    sys.stdout = open(os.devnull, "w", encoding="utf-8")    # the parent owns the console
    spec = importlib.util.spec_from_file_location("vrn_batch_pool_engine", engine_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    _STATE.update(engine=module, lookups=lookups)


def _one(idx, path_str, run_id):
    """One report in a worker: (idx, status, basic | error, financial, appendix cache entries of this file)."""
    engine = _STATE["engine"]
    ticker_lookup, broker_alias, rating_alias = _STATE["lookups"]
    try:
        basic, financial = engine.process_one_pdf(Path(path_str), ticker_lookup, broker_alias, rating_alias, run_id)
        out = (idx, "OK", basic, financial)
    except Exception as exc:  # noqa: BLE001 -- per-file isolation, the same as the sequential loop
        out = (idx, "FAIL", f"{exc}\n{traceback.format_exc()}", None)
    wanted = os.path.abspath(path_str)
    prime = []
    for name in CORE_MODNAMES:
        cache = getattr(sys.modules.get(name), "_APPENDIX_CACHE", None)
        if cache:
            prime += [(k, v) for k, v in list(cache.items()) if k and k[0] == wanted]
    return out + (prime,)


def map_reports(todo, engine_path, lookups, run_id, workers, on_done):
    """todo = [(idx, Path)] in the batch numbering.  Returns {idx: (status, basic | error, financial)};
    on_done(idx) is called as each report finishes (progress line).  Raises when the pool cannot run;
    the caller then runs the unfinished files itself."""
    results, prime = {}, []
    with _cf.ProcessPoolExecutor(max_workers=workers, mp_context=_mp.get_context("spawn"),
                                 initializer=_init, initargs=(str(engine_path), lookups)) as pool:
        futures = [pool.submit(_one, idx, str(path), run_id) for idx, path in todo]
        for future in _cf.as_completed(futures):
            idx, status, first, second, entries = future.result()
            results[idx] = (status, first, second)
            prime += entries
            on_done(idx)
    prime_parent(prime)
    return results


def prime_parent(entries):
    """Put the workers' appendix readings into this process's evidence-core cache (same file-version keys)."""
    for name in CORE_MODNAMES:
        core = sys.modules.get(name)
        cache = getattr(core, "_APPENDIX_CACHE", None)
        if cache is None:
            continue
        cap = int(getattr(core, "_APPENDIX_CACHE_MAX", 512))
        for key, value in entries:
            cache[key] = value
            while len(cache) > cap:
                cache.popitem(last=False)


if __name__ == "__main__":
    print(f"VRN_BatchPool {POOL_VERSION} · workers for 106 files here: {workers_for(106)} "
          f"(VRN_BATCH_WORKERS={os.environ.get('VRN_BATCH_WORKERS', '')!r} · "
          f"VIA_ACCEL_ACTIVE_THREADS={os.environ.get('VIA_ACCEL_ACTIVE_THREADS', '')!r} · cpu={os.cpu_count()})")
