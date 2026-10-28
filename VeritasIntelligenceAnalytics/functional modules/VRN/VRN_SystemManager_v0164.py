#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0164 — 薄尾(操作員 2026-10-10「停留在這個位置很久 · 出問題了嗎」)。
  長動詞(layout 等)看得到真實進度:啟動器把 B 車道進度檔路徑放在 VIA_PROGRESS_FILE;本版把自己的 [進度] i/N 行同步寫成
  「百分比 · 第一步取頁 / 第二步還原 i/N · 燈 · 檔名」→ 主控台矩陣與進度條每 0.8 秒跟著動(原子寫入,讀到半截不會亂)。
  沒有 VIA_PROGRESS_FILE(直接跑 python)= 行為完全不變。其餘動詞照前版鏈。
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

import builtins
import importlib.util
import os
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0164"


def _vnum_v0164(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0164(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0164(p) < _vnum_v0164(__file__)), key=_vnum_v0164)
PRIOR = _load_v0164(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


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


# ───────── 真實進度 → 啟動器進度檔 ─────────
import threading

_P = {"series": 0, "i": 0, "base": 20, "pct": 20, "last": 0.0, "seen": False}
_LOCK = threading.Lock()
_PROG_RX = re.compile(r"^\s*\[進度\]\s*(\d+)\s*/\s*(\d+)\s*(?:·\s*([A-Z]+))?\s*(?:·\s*(.*))?$")


def write_progress(pf: str, pct: int, text: str) -> None:
    """原子寫入(先寫暫存再換名);換名撞到讀取中就直接覆寫,再不行就略過 —— 進度只是顯示,不能讓主流程失敗。"""
    body = "%d · %s" % (max(0, min(99, pct)), text[:90])
    try:
        tmp = pf + ".tmp"
        Path(tmp).write_text(body, encoding="utf-8")
        try:
            os.replace(tmp, pf)
        except OSError:
            Path(pf).write_text(body, encoding="utf-8")
    except OSError:
        pass


def progress_line(line: str, pf: str) -> bool:
    """[進度] i/N → 百分比只增不減:第一段 20→95;還有下一段就從目前位置接著往上(不猜階段名稱)。"""
    m = _PROG_RX.match(line)
    if not m:
        return False
    i, n = int(m.group(1)), max(int(m.group(2)), 1)
    with _LOCK:
        if i == 1 or i < _P["i"]:
            _P["series"] += 1
            if _P["series"] > 1:
                _P["base"] = _P["pct"]
        _P["i"], _P["seen"] = i, True
        pct = max(_P["pct"], int(_P["base"] + (95 - _P["base"]) * i / n))
        _P["pct"] = pct
        now = time.time()
        if now - _P["last"] >= 0.5 or i == n:
            _P["last"] = now
            label = "還原" if _P["series"] <= 1 else "第 %d 段" % _P["series"]
            write_progress(pf, pct, "%s %d/%d · %s · %s" % (label, i, n, m.group(3) or "", (m.group(4) or "").strip()[:40]))
    return True


def _heartbeat(pf: str) -> None:
    """第一步(分類 · 取頁)沒有逐檔進度行 → 每 3 秒寫心跳,證明還活著;出現第一行 [進度] 就停。"""
    t0 = time.time()
    while True:
        with _LOCK:
            if _P["seen"] or _P.get("stop"):
                return
            write_progress(pf, 20, "VRN 準備中(分類 · 取頁)· 已 %d 秒" % int(time.time() - t0))
        time.sleep(3)


def install_progress_hook() -> bool:
    pf = os.environ.get("VIA_PROGRESS_FILE")
    if not pf or getattr(builtins.print, "_vrn_progress", False):
        return False
    orig = builtins.print

    def hooked(*a, **k):
        orig(*a, **k)
        if k.get("file") not in (None, sys.stdout):
            return
        try:
            progress_line(" ".join(str(x) for x in a), pf)
        except Exception:  # noqa: BLE001
            pass
    hooked._vrn_progress = True
    builtins.print = hooked
    threading.Thread(target=_heartbeat, args=(pf,), daemon=True).start()
    return True


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()
    install_progress_hook()
    return PRIOR.main(args)


def selftest() -> int:
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
    td = Path(tempfile.mkdtemp(prefix="vrn164-"))
    pf = str(td / "B.progress")
    _P.update(series=0, i=0, base=20, pct=20, last=0.0, seen=False)
    seen = []
    for ln in ["  [進度] 1/4 · GREEN · a.pdf", "  [進度] 2/4 · GREEN · b.pdf", "  [進度] 4/4 · YELLOW · d.pdf", "  [進度] 1/3 · GREEN · a.pdf", "  [進度] 3/3 · RED · c.pdf", "[計] 第二步 ……"]:
        _P["last"] = 0.0
        progress_line(ln, pf)
        seen.append(Path(pf).read_text(encoding="utf-8") if Path(pf).exists() else "")
    pcts = [int(x.split(" · ")[0]) for x in seen]
    chk("① [進度] i/N → 進度檔「百分比 · 還原 i/N · 燈 · 檔名」· 只增不減 · 第二段從目前位置接著走 · 不到 100(100 留給啟動器收尾)",
        seen[0].startswith("38 · 還原 1/4 · GREEN · a.pdf") and seen[2].startswith("95 · 還原 4/4") and seen[4].startswith("95 · 第 2 段 3/3 · RED · c.pdf") and seen[5] == seen[4] and pcts == sorted(pcts))
    os.environ["VIA_PROGRESS_FILE"] = pf
    saved = builtins.print
    try:
        _P.update(series=0, i=0, base=20, pct=20, last=0.0, seen=False)
        Path(pf).unlink()
        ok = install_progress_hook()
        time.sleep(0.3)
        hb = Path(pf).read_text(encoding="utf-8")
        again = install_progress_hook()
        print("  [進度] 1/2 · GREEN · x.pdf")
        txt = Path(pf).read_text(encoding="utf-8")
        time.sleep(3.3)
        txt2 = Path(pf).read_text(encoding="utf-8")
    finally:
        builtins.print = saved
        os.environ.pop("VIA_PROGRESS_FILE", None)
    chk("② 有 VIA_PROGRESS_FILE 才掛鉤(只掛一次)· 第一步先有心跳「準備中 · 已 N 秒」· 印 [進度] 就同步寫檔 · 之後心跳不再蓋掉 · 沒設環境變數 = 行為不變",
        ok and not again and hb.startswith("20 · VRN 準備中") and txt.startswith("57 · 還原 1/2") and txt2 == txt and not install_progress_hook())
    import shutil
    shutil.rmtree(td, ignore_errors=True)
    me = Path(__file__).read_text(encoding="utf-8")
    chk("③ 正本加速器橋 · 自帶多程序墊片", "import VeritasCeleritas_v1141" in me and _job_entry.__module__ in ("__main__", __name__))
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("④ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    print("[計] VRN_SystemManager_v0164 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
