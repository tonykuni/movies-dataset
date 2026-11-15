#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VRN-2 SystemManager v0274 — 薄尾:引擎矩陣改用作業系統檔案鎖(PR 641 · Codex P2)。

操作員令(2026-11-14):「現在修,開 PR 並盯著」。
問題:v0273 用「O_EXCL 建鎖檔 + 老過 120 秒就刪」排隊。兩個呼叫端同時判定同一個殘留鎖時,後刪的那個會刪掉先到者剛建的新鎖,
兩邊同時進入登記冊的讀 → 算 → 寫(更新互相蓋掉);finally 也可能刪到已經不是自己的鎖。
本版(前版 v0273 一字不動;只換它模組上的 em_locked 一個名字):
  · 改用作業系統檔案鎖:POSIX fcntl.flock(LOCK_EX | LOCK_NB)· Windows msvcrt.locking(LK_NBLCK)。
  · 持有者結束(含被砍)作業系統自動放鎖 → 不會有殘留鎖,不需要「過期就刪」。
  · 鎖檔留著、從不刪 → 刪不到別人的鎖;放鎖只經自己的檔案控制碼 → 只放自己的。
  · 等待規則照前版:自動登記最多等 2 秒(等不到這一輪不登)· engine-matrix 最多等 30 秒(還在忙回 YELLOW rc 2)。
平行 extract · 引擎矩陣其餘行為照前版。零網路 · 不碰 TA-Lib · 不讀寫同意閘。號:前版 v0273(main);本版 v0274。
用法同前版;自測 python VRN_SystemManager_v0274.py --selftest(本版 + 前版 v0273)。
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
import contextlib
import importlib.util
import os
import re
import sys
import tempfile
import time
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA_ROOT = HERE.parents[1]
TAG = "v0274"
DISPLAY_NAME = "VRN-2 SystemManager"
FAMILY = "VRN_SystemManager"
EM_TAG = DISPLAY_NAME + " " + TAG


def _vnum(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load(path: Path, name: str):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


PRIOR_PATH = max((p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
PRIOR = _load(PRIOR_PATH, "vrn_manager_prior_for_" + TAG)


def __getattr__(name):
    """尾版律 TAILAPI:前版公開名稱經本檔轉接。"""
    return getattr(PRIOR, name)


EM_CFG, EM_STATE = PRIOR.EM_CFG, PRIOR.EM_STATE                  # 同一個 dict(前版的設定 / 狀態)
em_out_dir, em_utc, em_read, em_json = PRIOR.em_out_dir, PRIOR.em_utc, PRIOR.em_read, PRIOR.em_json
em_lock_path, em_write = PRIOR.em_lock_path, PRIOR.em_write


def em_default_wait() -> float:
    return PRIOR.EM_LOCK_WAIT                                     # 等待秒數照前版的設定(前版 em_setwait 改的是它)


# ────────────────── 引擎矩陣:作業系統檔案鎖(PR 641 · Codex P2)──────────────────
# 前版用「O_EXCL 建鎖檔 + 老過 120 秒就刪」排隊:兩個呼叫端同時判定同一個殘留鎖時,後刪的那個會刪掉先到者剛建的新鎖,
# 兩邊同時進入登記冊的讀 → 算 → 寫(更新會互相蓋掉);finally 也可能刪到已經不是自己的鎖。
# 本版改用作業系統的檔案鎖:POSIX fcntl.flock(LOCK_EX | LOCK_NB)· Windows msvcrt.locking(LK_NBLCK)。
#   · 持有者結束(含被砍)時作業系統自動放鎖 → 不會再有殘留鎖,也就不需要「過期就刪」。
#   · 鎖檔本身留著、從不刪 → 不可能刪到別人的鎖;放鎖只能經自己的檔案控制碼 → 只放自己的。
#   · 同一行程不同執行緒各自開檔,鎖彼此照樣互斥(flock 以開啟的檔案描述為單位;Windows 以控制碼為單位)。
EM_CHILD_LOCK_CODE = r'''
import os, sys, time
fh = open(sys.argv[1], "a+b")
if os.name == "nt":
    import msvcrt
    fh.seek(0)
    msvcrt.locking(fh.fileno(), msvcrt.LK_LOCK, 1)
else:
    import fcntl
    fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
print("READY", flush=True)
time.sleep(120)
'''


def em_try_lock(fh) -> bool:
    """非阻塞拿鎖:拿到 True;別人持有 False。"""
    if os.name == "nt":
        import msvcrt
        fh.seek(0)
        try:
            msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
            return True
        except OSError:
            return False
    import fcntl
    try:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except BlockingIOError:
        return False


def em_unlock(fh) -> None:
    if os.name == "nt":
        import msvcrt
        fh.seek(0)
        msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        import fcntl
        fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


@contextlib.contextmanager
def em_locked(lock: Path, wait=None, stale=None):
    """作業系統檔案鎖排隊:拿到才往下;等超過 wait 秒 → TimeoutError。鎖檔從不刪(stale 參數只為相容前版呼叫,不再使用)。"""
    wait = em_default_wait() if wait is None else wait
    lock = Path(lock)
    lock.parent.mkdir(parents=True, exist_ok=True)
    fh = open(lock, "a+b")
    try:
        t0 = time.time()
        while not em_try_lock(fh):
            if time.time() - t0 > wait:
                raise TimeoutError("另一個行程正在更新引擎登記冊(%s),等了 %.0f 秒" % (lock.name, wait))
            time.sleep(0.05)
        try:
            yield lock
        finally:
            em_unlock(fh)
    finally:
        fh.close()


def em_oslock_selftest(chk, register, cmd, auto, state: dict, setwait) -> None:
    """作業系統檔案鎖自測(暫存夾)。register / cmd / auto = 本版的登記 · 動詞 · 自動;setwait(lock, auto) 改等待秒數並回舊值。"""
    import io
    import subprocess as _sp
    import threading
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        own = root / EM_CFG["dir"]
        own.mkdir(parents=True)
        pre = EM_CFG["prefixes"][0]
        (own / (pre + "ENG931_Theta_v0100.py")).write_text("t = 1\n", encoding="utf-8")
        od0 = em_out_dir(root)
        od0.mkdir(parents=True, exist_ok=True)
        (od0 / "probe.json.tmp").write_text("舊版固定暫存名(別的行程的)", encoding="utf-8")
        em_write(od0 / "probe.json", '{"ok": 1}')
        left = [x.name for x in od0.iterdir() if x.name.startswith("probe.json.") and x.name != "probe.json.tmp"]
        chk("L0 暫存檔名每個行程 / 每次都不同(照前版):寫完只剩正檔 · 不碰別人的 probe.json.tmp · 自己的暫存不殘留",
            em_read(od0 / "probe.json") == '{"ok": 1}' and (od0 / "probe.json.tmp").is_file() and left == [], left)
        (od0 / "probe.json.tmp").unlink()
        (od0 / "probe.json").unlink()
        lockp = em_lock_path(root)
        lockp.parent.mkdir(parents=True, exist_ok=True)
        lockp.write_bytes(b"")
        ino0 = lockp.stat().st_ino
        inside, peak, errs = [0], [0], []
        guard = threading.Lock()

        def crowd():
            try:
                for _ in range(15):
                    with em_locked(lockp, wait=20):
                        with guard:
                            inside[0] += 1
                            peak[0] = max(peak[0], inside[0])
                        time.sleep(0.002)
                        with guard:
                            inside[0] -= 1
            except Exception as exc:  # noqa: BLE001 — 自測要收集每條執行緒的例外再判
                errs.append("%s:%s" % (type(exc).__name__, exc))
        th = [threading.Thread(target=crowd) for _ in range(6)]
        for t in th:
            t.start()
        for t in th:
            t.join()
        chk("L1 互斥:6 條執行緒 × 15 次搶同一把鎖,任何時刻最多 1 條在裡面 · 零例外 · 鎖檔從沒被刪過(同一個檔)",
            peak[0] == 1 and not errs and lockp.is_file() and (not ino0 or lockp.stat().st_ino == ino0), (peak[0], errs[:2]))
        lockp.write_bytes(b"crashed-run residue")
        t0 = time.time()
        with em_locked(lockp, wait=0.5):
            got = time.time() - t0
        chk("L2 殘留的鎖檔(沒人持有)不擋路:立刻拿到(%.2f 秒)· 不需要「過期就刪」" % got, got < 0.4)
        child = _sp.Popen([sys.executable, "-c", EM_CHILD_LOCK_CODE, str(lockp)], stdout=_sp.PIPE, stdin=_sp.DEVNULL, text=True)
        try:
            ready = (child.stdout.readline() or "").strip()
            blocked = False
            try:
                with em_locked(lockp, wait=0.4):
                    blocked = False
            except TimeoutError:
                blocked = True
            child.kill()
            child.wait(timeout=30)
            t0 = time.time()
            try:
                with em_locked(lockp, wait=10):
                    freed = time.time() - t0
            except TimeoutError:
                freed = 99.0
        finally:
            if child.poll() is None:
                child.kill()
            if child.stdout:
                child.stdout.close()
        chk("L3 跨行程:別的行程持鎖時這邊等不到(TimeoutError)· 那個行程被砍掉後作業系統自動放鎖,這邊 %.2f 秒內拿到(不會有殘留鎖)" % freed,
            ready == "READY" and blocked and freed < 5, (ready, blocked, freed))
        fh = open(lockp, "a+b")
        held = em_try_lock(fh)
        old = setwait(0.3, 0.2)
        buf, buf2 = io.StringIO(), io.StringIO()
        keep = dict(state)
        try:
            with contextlib.redirect_stdout(buf):
                rc = cmd(["--no-git"], root)
            with contextlib.redirect_stdout(buf2):
                auto(root)
            auto_err = state.get("auto_error") or ""
        finally:
            setwait(*old)
            state.clear()
            state.update(keep)
            if held:
                em_unlock(fh)
            fh.close()
        chk("L4 鎖一直被別人持有:engine-matrix 照實回 YELLOW rc 2 + 說「另一個行程正在更新」(不崩)· 自動登記一個字不印、只記下來、不擋",
            held and rc == 2 and "另一個行程正在更新" in buf.getvalue() and buf2.getvalue() == "" and "TimeoutError" in auto_err,
            (held, rc, buf.getvalue()[-160:], buf2.getvalue()[:80], auto_err))
        errs2 = []

        def worker(i):
            try:
                (own / ("%sENG94%d_Iota_v0100.py" % (pre, i))).write_text("i = %d\n" % i, encoding="utf-8")
                register(root, wait=30)
            except Exception as exc:  # noqa: BLE001 — 自測要收集每條執行緒的例外再判
                errs2.append("%s:%s" % (type(exc).__name__, exc))
        th = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
        for t in th:
            t.start()
        for t in th:
            t.join()
        od = em_out_dir(root)
        final = em_json(em_read(od / ("%s_EngineMatrix_latest.json" % EM_CFG.get("stem", EM_CFG["system"])))) or {}
        names = set((final.get("rows") or {}).keys())
        junk = [x.name for x in od.iterdir() if x.name.endswith(".tmp")]
        chk("L5 8 條同時登記(各加一版再登):零例外 · 登記冊 9 版全在(沒有誰的更新被蓋掉)· 不留暫存檔 · 鎖檔還是同一個",
            not errs2 and all("%sENG94%d_Iota_v0100" % (pre, i) in names for i in range(8)) and len(names) == 9 and not junk
            and (not ino0 or lockp.stat().st_ino == ino0), (errs2[:3], len(names), junk))


_ORIG = {}


def install() -> None:
    """把作業系統檔案鎖掛上前版(冪等):前版的 em_register 每次都從自己模組上找 em_locked,換掉它就全換。"""
    if _ORIG:
        return
    _ORIG.update(em_locked=PRIOR.em_locked, manager=EM_CFG["manager"])
    PRIOR.em_locked = em_locked
    EM_CFG["manager"] = EM_TAG


def uninstall() -> None:
    if not _ORIG:
        return
    PRIOR.em_locked = _ORIG["em_locked"]
    EM_CFG["manager"] = _ORIG["manager"]
    _ORIG.clear()


install()


# ────────────────── 動詞 ──────────────────
def collect() -> dict:
    """VCGC 子系統對接口(照前版 · 只讀)· served_by 記本版。"""
    out = PRIOR.collect()
    if isinstance(out, dict):
        out = dict(out)
        sb = dict(out.get("served_by") or {})
        sb["tail"] = FAMILY + "_" + TAG
        out["served_by"] = sb
    return out


def provenance(args: list) -> int:
    """同前版:直送 ENG114 尾版;`--selftest` 之後再跑本版自測,回傳碼取大。"""
    h = PRIOR.host()
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    rc = int(h._load_engine(h.provenance_engine_path()).main(list(args)) or 0)
    if "--selftest" in args:
        print("  ── 來源回歸之後:本版管理器自測 ──", flush=True)
        rc = max(rc, int(selftest() or 0))
    return rc


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] == ["provenance"]:
        return provenance(args[1:])
    if args == ["--selftest"] or "--selftest" in args[:1]:
        return selftest()
    return PRIOR.main(args)                                       # engine-matrix / 自動登記 / extract … 照前版,鎖走本版


def selftest() -> int:
    print("[計] %s %s 自測開始(本版 9 項 · 再前版 %s)" % (DISPLAY_NAME, TAG, PRIOR_PATH.name), flush=True)
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)
    install()
    chk("L-0 換裝在位:前版模組的 em_locked 是本版的作業系統檔案鎖 · 矩陣標頭記本版",
        PRIOR.em_locked is em_locked and EM_CFG["manager"] == EM_TAG)
    em_oslock_selftest(chk, PRIOR.em_register, PRIOR.em_cmd, PRIOR.em_auto, EM_STATE, PRIOR.em_setwait)
    text = Path(__file__).read_text(encoding="utf-8")
    chk("L6 檔面:def main / def selftest / def collect · 第 3 行加速器標記 · __main__ provenance 守門在 --selftest 之前 · 零 TA-Lib · 不寫同意閘",
        "\ndef main(" in text and "\ndef selftest(" in text and "\ndef collect(" in text and text.splitlines()[2].strip() == "# [VIA:ACCEL-BRIDGE:v0111]"
        and text.index('sys.argv[1:2] == ["provenance"]') < text.index('"--selftest" in sys.argv:')
        and "import " + "talib" not in text and "environ[\"VIA_NET" + "_CONSENT\"] =" not in text)
    print("  ── 前版 %s 自測(本版換裝卸下,照前版原行為)──" % PRIOR_PATH.name, flush=True)
    uninstall()
    try:
        prior_rc = int(PRIOR.selftest() or 0)
    finally:
        install()
    chk("L7 前版 %s 自測照過" % PRIOR_PATH.name, prior_rc == 0, prior_rc)
    n = sum(ok)
    print("[計] %s %s(%s_%s.py)自測 %d/%d · %s" % (DISPLAY_NAME, TAG, FAMILY, TAG, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    return 0 if n == len(ok) else 1


if __name__ == "__main__":
    if sys.argv[1:2] == ["provenance"]:     # 同前版:provenance 先於任何 --selftest 攔截
        sys.exit(provenance(sys.argv[2:]))
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.exit(main(sys.argv[1:]))
