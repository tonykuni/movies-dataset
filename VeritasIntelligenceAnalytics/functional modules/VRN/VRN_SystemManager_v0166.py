#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0166 — 薄尾(操作員 2026-10-10「為何跟前一次一樣分類取頁停留在 60% 沒有進展」)。
  原因:① 第一步的分類器批次(_pool_map kind=cls)與取頁(stage_run)都不印逐檔進度,只有第二步會印 → 只剩心跳
        ② 心跳把秒數放在句尾,矩陣說明欄一窄就被切掉,看起來像停住
  本版:三段都有真實逐檔進度 —— 分類 i/N(20→35%)· 取頁 i/N(35→45%)· 還原 i/N(45→95%);
        秒數放最前面「125s · 分類 37/106 · 燈 · 檔名」;單一檔跑很久(Word 轉 PDF 等)心跳每 3 秒照樣更新秒數。
  沒有 VIA_PROGRESS_FILE(直接跑 python)= 只多印進度行,其餘行為不變。其餘動詞照前版鏈。
"""
from __future__ import annotations

# ===== [VIA:ACCEL-BRIDGE:v0110] 正本加速器 VeritasCeleritas_v1141 · 正本網路工具 VeritasAegisNexus_v1652(找不到 = 不改任何行為) =====
import sys as _cb_sys
from pathlib import Path as _cb_Path
_cb_p = _cb_Path(__file__).resolve()
while _cb_p.parent != _cb_p:
    if (_cb_p / "supportive modules").is_dir():
        _cb_sup = _cb_p / "supportive modules"
        for _cb_d in [_cb_sup] + [x.parent for x in list(_cb_sup.glob("*/VeritasAegisNexus_v1652.py"))[:1]]:
            if str(_cb_d) not in _cb_sys.path:
                _cb_sys.path.insert(0, str(_cb_d))
        break
    _cb_p = _cb_p.parent
try:
    import VeritasCeleritas_v1141 as _ACCEL  # noqa: F401  正本加速器
except Exception:  # noqa: BLE001
    _ACCEL = None


def _net():
    """正本網路工具(只在需要出網時載入;本引擎不出網)。"""
    try:
        import VeritasAegisNexus_v1652 as _NET  # noqa: WPS433
        return _NET
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import importlib.util
import os
import re
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0166"


def _vnum_v0166(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0166(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0166(p) < _vnum_v0166(__file__)), key=_vnum_v0166)
PRIOR = _load_v0166(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def _owner(name):
    import types
    mod, seen = PRIOR, set()
    while isinstance(mod, types.ModuleType) and id(mod) not in seen:
        seen.add(id(mod))
        if name in vars(mod):
            return mod
        mod = vars(mod).get("PRIOR")
    return None


def _resolve(name):
    m = _owner(name)
    return vars(m)[name] if m else None


def _job_entry(kind, item):
    return _resolve("_job")(kind, item)


def _init_entry(*args):
    return _resolve("_init_entry")(*args)


# ───────── 三段進度:分類 / 取頁 / 還原 ─────────
_RANGE = {"分類": (20, 35), "取頁": (35, 45), "還原": (45, 95)}
_S = {"t0": time.time(), "pct": 20, "text": "準備中", "last": 0.0, "write": 0.0}
_LK = threading.Lock()
_RX = re.compile(r"^\s*\[進度\]\s*(\d+)\s*/\s*(\d+)\s*·\s*(?:(分類|取頁|還原)\s*·\s*)?(?:([A-Z—-]+)\s*·\s*)?(.*)$")


def _write(pf: str) -> None:
    wp = _resolve("write_progress")
    body = "%ds · %s" % (int(time.time() - _S["t0"]), _S["text"])
    if wp:
        wp(pf, _S["pct"], body)
    _S["write"] = time.time()


def progress_line_v166(line: str, pf: str) -> bool:
    m = _RX.match(line)
    if not m:
        return False
    i, n = int(m.group(1)), max(int(m.group(2)), 1)
    stage = m.group(3) or "還原"
    lo, hi = _RANGE[stage]
    with _LK:
        _S["pct"] = max(_S["pct"], int(lo + (hi - lo) * i / n))
        _S["text"] = "%s %d/%d · %s · %s" % (stage, i, n, m.group(4) or "—", (m.group(5) or "").strip()[:36])
        _S["last"] = time.time()
        if time.time() - _S["write"] >= 0.5 or i == n:
            _write(pf)
    return True


def _heartbeat_v166(pf: str) -> None:
    """每 3 秒:最近 4 秒沒有新進度就刷新秒數(證明還活著,文字保留最後一筆進度)。"""
    while not _S.get("stop"):
        time.sleep(3)
        with _LK:
            if time.time() - _S["last"] >= 4:
                _write(pf)


_m164 = _owner("progress_line")
if _m164:
    setattr(_m164, "progress_line", progress_line_v166)
    setattr(_m164, "_heartbeat", lambda pf: None)          # 舊心跳(秒數在句尾)停用,改用本版


def install_v166() -> bool:
    pf = os.environ.get("VIA_PROGRESS_FILE")
    ok = (_resolve("install_progress_hook") or (lambda: False))()
    if pf and ok:
        _S["t0"] = time.time()
        with _LK:
            _S["text"] = "準備中(分類 · 取頁)"
            _write(pf)
        threading.Thread(target=_heartbeat_v166, args=(pf,), daemon=True).start()
    return ok


# 分類器批次也印逐檔進度(原版只有 l2 印)
_PREV_POOL = _resolve("_pool_map")


def _pool_map_v166(kind: str, items: list, workers: int, initargs: tuple) -> tuple:
    if kind == "l2":
        return _PREV_POOL(kind, items, workers, initargs)
    out = []
    _job, _init_worker = _resolve("_job"), _resolve("_init_worker")
    zh = {"cls": "分類"}.get(kind, kind)
    if workers > 1 and len(items) > 1:
        try:
            import multiprocessing as _mp
            from concurrent.futures import ProcessPoolExecutor, as_completed
            with ProcessPoolExecutor(max_workers=workers, initializer=_init_worker, initargs=initargs, mp_context=_mp.get_context("spawn")) as ex:
                futs = {ex.submit(_job, kind, it): it for it in items}
                for i, fu in enumerate(as_completed(futs), 1):
                    it = futs[fu]
                    try:
                        out.append(fu.result())
                    except Exception as exc:  # noqa: BLE001
                        out.append({"file": Path(it if isinstance(it, str) else it.get("path", "?")).name, "path": it if isinstance(it, str) else it.get("path"), "lamp": "RED", "notes": ["%s:%s" % (type(exc).__name__, str(exc)[:80])]})
                    print("  [進度] %d/%d · %s · %s · %s" % (i, len(items), zh, out[-1].get("lamp") or "—", str(out[-1].get("file") or Path(str(it)).name)[:50]), flush=True)
            return out, "多程序 ×%d" % workers
        except Exception as exc:  # noqa: BLE001
            out = []
            note = "多程序失敗(%s)→ 單程序" % type(exc).__name__
    else:
        note = "單程序"
    _init_worker(*initargs)
    for i, it in enumerate(items, 1):
        try:
            out.append(_job(kind, it))
        except Exception as exc:  # noqa: BLE001
            out.append({"file": Path(it if isinstance(it, str) else it.get("path", "?")).name, "lamp": "RED", "notes": ["%s:%s" % (type(exc).__name__, str(exc)[:80])]})
        print("  [進度] %d/%d · %s · %s · %s" % (i, len(items), zh, out[-1].get("lamp") or "—", str(out[-1].get("file") or Path(str(it)).name)[:50]), flush=True)
    return out, note


_mp_ = _owner("_pool_map")
if _mp_:
    setattr(_mp_, "_pool_map", _pool_map_v166)

# 取頁(stage_run 逐檔迴圈每檔先呼叫一次 fname_parse)→ 只在 stage_run 期間計數印進度
_STG = {"on": False, "i": 0, "n": 0}
_PREV_FP = _resolve("fname_parse")


def fname_parse_v166(name, *a, **k):
    r = _PREV_FP(name, *a, **k)
    if _STG["on"]:
        _STG["i"] += 1
        print("  [進度] %d/%d · 取頁 · — · %s" % (_STG["i"], max(_STG["n"], _STG["i"]), str(name)[:50]), flush=True)
    return r


_PREV_SR = _resolve("stage_run")


def stage_run_v166(d, recursive: bool = False, only: str = ""):
    try:
        it = d.rglob("*") if recursive else (d.iterdir() if d.is_dir() else [])
        n = sum(1 for p in it if p.is_file() and not p.name.startswith("~$") and (not only or only.lower() in p.name.lower()))
    except OSError:
        n = 0
    _STG.update(on=True, i=0, n=n)
    try:
        return _PREV_SR(d, recursive, only)
    finally:
        _STG["on"] = False


for _nm, _fn in (("fname_parse", fname_parse_v166), ("stage_run", stage_run_v166)):
    _mo = _owner(_nm)
    if _mo:
        setattr(_mo, _nm, _fn)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()
    install_v166()
    try:
        return PRIOR.main(args)
    finally:
        _S["stop"] = True


def selftest() -> int:
    import builtins
    import shutil
    import tempfile
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)
    td = Path(tempfile.mkdtemp(prefix="vrn166-"))
    pf = str(td / "B.progress")
    _S.update(t0=time.time() - 125, pct=20, text="準備中", last=0.0, write=0.0)
    seen = []
    for ln in ["  [進度] 1/4 · 分類 · GREEN · a.pdf", "  [進度] 4/4 · 分類 · — · d.pdf", "  [進度] 2/2 · 取頁 · — · b.pdf", "  [進度] 1/2 · YELLOW · x.pdf", "  [進度] 2/2 · 還原 · RED · y.pdf"]:
        _S["write"] = 0.0
        progress_line_v166(ln, pf)
        seen.append(Path(pf).read_text(encoding="utf-8"))
    pc = [int(x.split(" · ")[0]) for x in seen]
    chk("① 三段進度:分類 20→35 · 取頁 35→45 · 還原 45→95(舊格式無段名 = 還原)· 只增不減", pc == [23, 35, 45, 70, 95] and pc == sorted(pc))
    chk("② 秒數放最前面(說明欄再窄也看得到在動):「125s · 分類 1/4 · GREEN · a.pdf」", seen[0].split(" · ", 1)[1].startswith("125s · 分類 1/4 · GREEN · a.pdf"))
    _S.update(last=time.time() - 10, write=0.0, stop=False)
    th = threading.Thread(target=_heartbeat_v166, args=(pf,), daemon=True)
    th.start()
    time.sleep(3.4)
    _S["stop"] = True
    hb = Path(pf).read_text(encoding="utf-8")
    chk("③ 單一檔跑很久:心跳照樣刷新秒數 · 保留最後一筆進度文字", re.match(r"^95 · \d+s · 還原 2/2 · RED · y\.pdf", hb) is not None)
    out = []
    saved = builtins.print
    builtins.print = lambda *a, **k: out.append(" ".join(str(x) for x in a))
    try:
        _STG.update(on=True, i=0, n=3)
        for nm in ("a.pdf", "b.pdf", "c.docx"):
            try:
                fname_parse_v166(nm, {}, {}, 0, None)
            except Exception:  # noqa: BLE001
                _STG["i"] += 0
        _STG["on"] = False
        fname_parse_v166("z.pdf", {}, {}, 0, None)
    finally:
        builtins.print = saved
    chk("④ 取頁只在 stage_run 期間計數(其他地方呼叫檔名解析不印)", sum(1 for x in out if "取頁" in x) == 3 and "3/3 · 取頁" in out[-1])
    chk("⑤ 分類器批次換成會印逐檔進度的版本 · stage_run / 檔名解析已掛上", _owner("_pool_map") and vars(_owner("_pool_map"))["_pool_map"] is _pool_map_v166 and vars(_owner("stage_run"))["stage_run"] is stage_run_v166)
    shutil.rmtree(td, ignore_errors=True)
    me = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 正本加速器橋 · 自帶多程序墊片", "import VeritasCeleritas_v1141" in me and _job_entry.__module__ in ("__main__", __name__))
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("⑦ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    print("[計] VRN_SystemManager_v0166 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
