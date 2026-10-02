#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""CGC_MDL058_Lessons v0103 — 薄尾:教訓帳跨行程鎖 + 原子寫入 + 讀壞不當空帳(並行串測的前提)

實測(2026-10-02,操作員「全部系統在 CPU 架構下最大加速化」):VCGC 全功能串測 133 站一站接一站跑,4 核只用約 23%。
要讓互不相依的站並行,先量共用寫入點,教訓帳是最危險的一個:
  · v0101 load_ledger() 讀到不是完整 JSON(另一個行程正寫到一半)就回「空帳」;record_event 接著 save → **整本只增帳被一筆蓋掉**。
  · save_ledger() 直接 write_text:寫到一半被砍,留下半截檔;下一次讀又落回「空帳」。
  · 讀 → 改 → 寫之間沒有鎖:兩個 VCGC 子行程同時失敗,後寫的把先寫的那筆吃掉。
本版只改這三件(行為照前版,帳目格式一字不動):
  ① 讀:檔不在 = 新帳(照前版);**檔在但讀不懂 = 丟例外**,不回空帳、不寫。
  ② 寫:同夾暫存檔 → fsync → os.replace(一次換上,不會半截)。
  ③ 鎖:record_event 與 --record 整段「讀 → 改 → 寫」持跨行程鎖(POSIX fcntl.flock · Windows msvcrt.locking);
     鎖檔放系統暫存夾(依帳本路徑雜湊命名),倉內不多檔。
其餘(簽名正規化 · 重複出錯 · 報告)照 v0102。只收 VCGC 呼叫的規矩照前版。零網路。
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

import contextlib
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "CGC_MDL058_Lessons"


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(STEM + "_prior_for_" + Path(__file__).stem, PRIOR)
_PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _PRIOR
_spec.loader.exec_module(_PRIOR)
_STORE = _PRIOR._PRIOR                      # v0101:LEDGER · load_ledger · save_ledger 住在這一層
_RECORD_V0102 = _PRIOR.record_event


def __getattr__(name: str):
    return getattr(_PRIOR, name)


class LedgerUnreadable(RuntimeError):
    """帳本檔在但讀不懂:不當空帳、不寫(寧可這一筆記不進去,也不蓋掉整本只增帳)。"""


def _lock_path_v0103(ledger: Path) -> Path:
    key = hashlib.sha256(str(Path(ledger).resolve()).encode("utf-8")).hexdigest()[:16]
    return Path(tempfile.gettempdir()) / f"via_lessons_{key}.lock"


@contextlib.contextmanager
def ledger_lock(ledger: Path | None = None, timeout: float = 60.0):
    """跨行程互斥:同一本帳同時只有一個行程在「讀 → 改 → 寫」。"""
    lp = _lock_path_v0103(ledger or _STORE.LEDGER)
    fh = open(lp, "a+b")
    try:
        if os.name == "nt":
            import msvcrt
            t0 = time.time()
            while True:
                try:
                    fh.seek(0)
                    msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError:
                    if time.time() - t0 > timeout:
                        raise
                    time.sleep(0.05)
        else:
            import fcntl
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        yield lp
    finally:
        try:
            if os.name == "nt":
                import msvcrt
                fh.seek(0)
                msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        finally:
            fh.close()


def load_ledger() -> dict:
    p = _STORE.LEDGER
    if not p.is_file():
        return {"schema": "VIA.Lessons.v1", "append_only": True, "entries": []}
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise LedgerUnreadable(f"{p.name} 讀不懂({type(exc).__name__});不當空帳、不寫") from exc
    if not isinstance(d, dict) or not isinstance(d.get("entries"), list):
        raise LedgerUnreadable(f"{p.name} 沒有 entries 清單;不當空帳、不寫")
    return d


def save_ledger(d: dict) -> None:
    p = _STORE.LEDGER
    fd, tmp = tempfile.mkstemp(prefix=p.name + ".", suffix=".tmp", dir=str(p.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(d, ensure_ascii=False, indent=1))
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, p)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


_STORE.load_ledger, _STORE.save_ledger = load_ledger, save_ledger     # v0101 / v0102 的讀寫都走這兩支


def record_event(ev: dict, save: bool = True) -> dict:
    if not save:
        return _RECORD_V0102(ev, save)
    with ledger_lock():
        return _RECORD_V0102(ev, save)


_PRIOR.record_event = record_event


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        return selftest()
    if "--record" in a:
        with ledger_lock():
            return _PRIOR.main()
    return _PRIOR.main()


_CHILD_V0103 = r"""
import importlib.util, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location("lessons_child", sys.argv[1])
m = importlib.util.module_from_spec(spec); sys.modules["lessons_child"] = m; spec.loader.exec_module(m)
m._STORE.LEDGER = Path(sys.argv[2])
for i in range(int(sys.argv[4])):
    m.record_event({"verb": "run", "error": "worker " + sys.argv[3] + " event " + str(i), "rc": 1})
"""


def selftest() -> int:
    rc = _PRIOR.selftest()
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    chk("① 前版 v0102 自測過(簽名 · 重複出錯 · 只增)", rc == 0)
    keep = _STORE.LEDGER
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        try:
            _STORE.LEDGER = t / "L.json"
            fresh = load_ledger()
            _STORE.LEDGER.write_text('{"entries": [{"id": "A"}', encoding="utf-8")
            try:
                load_ledger()
                bad_raised = False
            except LedgerUnreadable:
                bad_raised = True
            try:
                record_event({"verb": "run", "error": "x", "rc": 1})
                wrote = True
            except LedgerUnreadable:
                wrote = False
            half_kept = _STORE.LEDGER.read_text(encoding="utf-8") == '{"entries": [{"id": "A"}'
        finally:
            _STORE.LEDGER = keep
        chk("② 檔不在 = 新帳;檔在但半截 = 丟例外、不寫(前版會當空帳 → 蓋掉整本)",
            fresh["entries"] == [] and bad_raised and not wrote and half_kept)
        led = t / "C.json"
        save_tmp = _STORE.LEDGER
        try:
            _STORE.LEDGER = led
            save_ledger({"schema": "VIA.Lessons.v1", "append_only": True, "entries": []})
        finally:
            _STORE.LEDGER = save_tmp
        leftovers = [p.name for p in t.iterdir() if p.suffix == ".tmp"]
        chk("③ 原子寫入:暫存檔換上,不留 .tmp", led.is_file() and not leftovers, leftovers)
        workers, each = 6, 5
        procs = [subprocess.Popen([sys.executable, "-c", _CHILD_V0103, str(Path(__file__)), str(led), str(w), str(each)],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.PIPE) for w in range(workers)]
        errs = [p.communicate(timeout=300)[1].decode("utf-8", "replace")[-200:] for p in procs]
        rows = json.loads(led.read_text(encoding="utf-8"))["entries"]
        ids = [r["id"] for r in rows]
        chk(f"④ 並行:{workers} 個行程各記 {each} 筆同時寫同一本帳 → {workers * each} 筆一筆不少 · 編號不重",
            len(rows) == workers * each and len(set(ids)) == len(ids) and all(p.returncode == 0 for p in procs),
            f"{len(rows)} 筆 · 重號 {len(ids) - len(set(ids))} · {[e for e in errs if e.strip()][:1]}")
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑤ 加速器橋 · 網路橋在;鎖檔在系統暫存夾(倉內不多檔);不碰 TA-Lib",
        "[VIA:ACCEL-BRIDGE" in text and "[VIA:NET-BRIDGE" in text and _lock_path_v0103(_STORE.LEDGER).parent == Path(tempfile.gettempdir())
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M))
    print(f"  [計] CGC_MDL058 v0103 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if rc == 0 and all(ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
