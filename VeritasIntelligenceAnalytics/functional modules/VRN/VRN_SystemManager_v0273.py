#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VRN-2 SystemManager v0273 — 薄尾:引擎矩陣同時執行不互撞(PR 640 · Codex P2)。

操作員令(2026-11-14):「現在修,開 PR 並盯著」。
問題(容器重現):v0272 的引擎矩陣每個行程都寫同一個 `<檔>.tmp`;兩個行程同時更新登記冊時,後改名的那個 FileNotFoundError,
而且同時登的更新會互相蓋掉(6 條同時登 90 版:v0178 同一套程式 5 次 FileNotFoundError、登記冊只剩 22 版)。
本版(前版 v0272 一字不動;只換它模組上的 em_write · em_register · em_auto · em_cmd 四個名字):
  ① 暫存檔名帶行程號 + 亂數(各寫各的,寫完 os.replace,失敗也清)。
  ② 登記冊「讀 → 算 → 寫」整段用鎖檔排隊(O_EXCL 建檔,跨行程 / 跨執行緒都有效;鎖檔老過 120 秒 = 殘留,自動清)。
  ③ 自動登記最多等 2 秒,等不到這一輪不登(別的行程正在登同一份),一個字不印、不擋主動詞;
     engine-matrix 最多等 30 秒,還在忙就照實回 YELLOW(rc 2)不崩。
平行 extract · 進度 · 全列 · 與上次比 · 引擎矩陣其餘行為照前版。零網路 · 不碰 TA-Lib · 不讀寫同意閘。
號:前版 v0272(main);本版取下一個空號 v0273。
用法同 v0272;自測 python VRN_SystemManager_v0273.py --selftest(本版 + 前版 v0272)。
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
TAG = "v0273"
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


# ────────────────── 引擎矩陣:同時執行不互撞(PR 640 · Codex P2)──────────────────
# 舊版每個行程都寫同一個 `<檔>.tmp`,兩個行程同時更新登記冊時,後改名的那個會 FileNotFoundError。
# 本版:暫存檔名帶行程號 + 亂數(各寫各的)· 登記冊的「讀 → 算 → 寫」整段用鎖檔排隊(O_EXCL 建檔,跨行程 / 跨執行緒都有效)。
# 自動登記最多等 EM_AUTO_WAIT 秒,等不到就這一輪不登(別的行程正在登同一份),不擋主動詞;
# engine-matrix 動詞最多等 EM_LOCK_WAIT 秒,還在忙就照實回 YELLOW(rc 2)不崩。鎖檔超過 EM_LOCK_STALE 秒視為殘留(行程被砍)→ 清掉再拿。
EM_LOCK_WAIT, EM_AUTO_WAIT, EM_LOCK_STALE = 30.0, 2.0, 120.0


def em_lock_path(root, out_dir=None) -> Path:
    return em_out_dir(root, out_dir) / ("%s_EngineMatrix.lock" % EM_CFG.get("stem", EM_CFG["system"]))


def em_unlink(p) -> bool:
    try:
        Path(p).unlink()
        return True
    except FileNotFoundError:
        return False
    except OSError as exc:
        EM_STATE["unlink_error"] = "%s:%s" % (type(exc).__name__, str(exc)[:120])
        return False


def em_age(p):
    try:
        return time.time() - Path(p).stat().st_mtime
    except OSError:
        return None


def em_write(p: Path, text: str, bom: bool = False) -> None:
    """原子寫入:暫存檔名每個行程 / 每次都不同,寫完 os.replace;失敗時暫存檔照清。"""
    p = Path(p)
    tmp = p.with_name("%s.%d.%s.tmp" % (p.name, os.getpid(), uuid.uuid4().hex[:8]))
    try:
        tmp.write_text(text, encoding="utf-8-sig" if bom else "utf-8", newline="\n")
        os.replace(tmp, p)
    finally:
        em_unlink(tmp)


@contextlib.contextmanager
def em_locked(lock: Path, wait=None, stale=None):
    """鎖檔排隊:拿到才往下;等超過 wait 秒 → TimeoutError;鎖檔老過 stale 秒 → 視為殘留,清掉再拿。"""
    wait = EM_LOCK_WAIT if wait is None else wait
    stale = EM_LOCK_STALE if stale is None else stale
    lock = Path(lock)
    lock.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    fd = None
    while fd is None:
        try:
            fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            age = em_age(lock)
            if age is not None and age > stale:
                em_unlink(lock)
            elif time.time() - t0 > wait:
                raise TimeoutError("另一個行程正在更新引擎登記冊(%s),等了 %.0f 秒" % (lock.name, wait)) from None
            else:
                time.sleep(0.05)
    try:
        os.write(fd, ("%d %s" % (os.getpid(), em_utc())).encode("utf-8"))
        os.close(fd)
        yield lock
    finally:
        em_unlink(lock)


def em_safe_selftest(chk, register, cmd, auto, state: dict, setwait) -> None:
    """同時執行自測(暫存夾)。register / cmd / auto = 本版的登記 · 動詞 · 自動;setwait(lock, auto) 改等待秒數並回舊值。"""
    import io
    import threading
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        own = root / EM_CFG["dir"]
        own.mkdir(parents=True)
        pre = EM_CFG["prefixes"][0]
        (own / (pre + "ENG911_Gamma_v0100.py")).write_text("g = 1\n", encoding="utf-8")
        od = em_out_dir(root)
        od.mkdir(parents=True)
        target = od / "probe.json"
        (od / "probe.json.tmp").write_text("舊版固定暫存名(別的行程的)", encoding="utf-8")
        em_write(target, '{"ok": 1}')
        left = [x.name for x in od.iterdir() if x.name.startswith("probe.json.") and x.name != "probe.json.tmp"]
        chk("S1 暫存檔名每個行程 / 每次都不同:寫完只剩正檔 · 不碰別人的 probe.json.tmp · 自己的暫存不殘留",
            em_read(target) == '{"ok": 1}' and (od / "probe.json.tmp").is_file() and left == [], left)
        lock = em_lock_path(root)
        lock.write_text("held", encoding="utf-8")
        threading.Timer(0.6, lambda: em_unlink(lock)).start()
        t0 = time.time()
        s2 = register(root, wait=5)
        waited = time.time() - t0
        chk("S2 鎖在別人手上 → 排隊等(%.1f 秒)· 對方放鎖後照常登記 · 鎖檔用完就清" % waited,
            waited >= 0.5 and s2.get("versions") == 1 and not lock.exists(), (waited, s2.get("versions"), lock.exists()))
        lock.write_text("crashed", encoding="utf-8")
        os.utime(lock, (time.time() - 1000, time.time() - 1000))
        t0 = time.time()
        s3 = register(root, wait=0.5)
        chk("S3 殘留鎖(行程被砍,老過 %d 秒)→ 清掉直接登,不卡" % EM_LOCK_STALE,
            time.time() - t0 < 0.5 and s3.get("versions") == 1 and not lock.exists())
        lock.write_text("busy", encoding="utf-8")
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
            em_unlink(lock)
        chk("S4 鎖一直被佔:engine-matrix 照實回 YELLOW rc 2 + 說「另一個行程正在更新」(不崩)· 自動登記一個字不印、只記下來、不擋",
            rc == 2 and "另一個行程正在更新" in buf.getvalue() and buf2.getvalue() == "" and "TimeoutError" in auto_err,
            (rc, buf.getvalue()[-160:], buf2.getvalue()[:80], auto_err))
        errs = []

        def worker(i):
            try:
                (own / ("%sENG92%d_Delta_v0100.py" % (pre, i))).write_text("d = %d\n" % i, encoding="utf-8")
                register(root, wait=20)
            except Exception as exc:  # noqa: BLE001 — 自測要收集每條執行緒的例外再判
                errs.append("%s:%s" % (type(exc).__name__, exc))
        th = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
        for t in th:
            t.start()
        for t in th:
            t.join()
        final = em_json(em_read(od / ("%s_EngineMatrix_latest.json" % EM_CFG.get("stem", EM_CFG["system"])))) or {}
        names = set((final.get("rows") or {}).keys())
        junk = [x.name for x in od.iterdir() if x.name.endswith((".tmp", ".lock")) and x.name != "probe.json.tmp"]
        chk("S5 8 條同時登記(各加一版再登):零例外 · 最後的登記冊 8 版全在(沒有誰的更新被蓋掉)· 不留暫存 / 鎖檔",
            not errs and all("%sENG92%d_Delta_v0100" % (pre, i) in names for i in range(8)) and not junk, (errs[:3], len(names), junk))


_ORIG = {}
_PATCHED = ("em_write", "em_register", "em_auto", "em_cmd")


def em_register(root, out_dir=None, use_git=False, now=None, wait=None) -> dict:
    """登記冊的「讀 → 算 → 寫」整段排隊(同時執行不互撞 · 不丟別人的更新);算法照前版。"""
    with em_locked(em_lock_path(root, out_dir), wait=wait):
        return _ORIG["em_register"](root, out_dir=out_dir, use_git=use_git, now=now)


def em_auto(root):
    """每次執行的靜默登記:別的行程正在登 → 最多等 EM_AUTO_WAIT 秒,等不到這一輪不登;一個字不印、不擋主動詞。"""
    try:
        EM_STATE["auto"] = em_register(root, wait=EM_AUTO_WAIT)
    except Exception as exc:  # noqa: BLE001 — 自動登記壞了不擋主流程,照實記下
        EM_STATE["auto_error"] = "%s:%s" % (type(exc).__name__, str(exc)[:160])
    return EM_STATE.get("auto")


def em_cmd(args: list, root) -> int:
    try:
        return _ORIG["em_cmd"](args, root)
    except TimeoutError as exc:
        print("[%s] 引擎矩陣 YELLOW · %s · 等一下再跑一次" % (EM_CFG["manager"], exc))
        return 2


def em_setwait(lock_wait, auto_wait) -> tuple:
    """自測用:暫時改等待秒數,回舊值。"""
    global EM_LOCK_WAIT, EM_AUTO_WAIT
    old = (EM_LOCK_WAIT, EM_AUTO_WAIT)
    EM_LOCK_WAIT, EM_AUTO_WAIT = lock_wait, auto_wait
    return old


def install() -> None:
    """把同時執行修掛上前版的引擎矩陣(冪等);前版的 em_cmd / em_auto / 主程式照常呼叫,改走本版。"""
    if _ORIG:
        return
    _ORIG.update({n: getattr(PRIOR, n) for n in _PATCHED})
    _ORIG["manager"] = EM_CFG["manager"]
    for n, f in (("em_write", em_write), ("em_register", em_register), ("em_auto", em_auto), ("em_cmd", em_cmd)):
        setattr(PRIOR, n, f)
    EM_CFG["manager"] = EM_TAG


def uninstall() -> None:
    if not _ORIG:
        return
    for n in _PATCHED:
        setattr(PRIOR, n, _ORIG[n])
    EM_CFG["manager"] = _ORIG["manager"]
    _ORIG.clear()


@contextlib.contextmanager
def prior_world(family: str):
    """跑前版自測時,讓前版看到「當年的夾」:比前版新的同家族管理器檔先藏起來(前版 E6 要求自己就是尾版)。只影響前版的 em_files。"""
    orig = PRIOR.em_files
    cap = _vnum(PRIOR_PATH)
    PRIOR.em_files = lambda root: [p for p in orig(root) if not (p.name.startswith(family + "_v") and _vnum(p) > cap)]
    try:
        yield
    finally:
        PRIOR.em_files = orig


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
    return PRIOR.main(args)                                       # engine-matrix / 自動登記 / extract … 照前版,走本版換上的四個名字


def selftest() -> int:
    print("[計] %s %s 自測開始(本版 8 項 · 再前版 %s)" % (DISPLAY_NAME, TAG, PRIOR_PATH.name), flush=True)
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)
    install()
    chk("S0 換裝在位:前版模組的 em_write · em_register · em_auto · em_cmd 都是本版 · 矩陣標頭記本版",
        all(getattr(PRIOR, n) is globals()[n] for n in _PATCHED) and EM_CFG["manager"] == EM_TAG)
    em_safe_selftest(chk, em_register, em_cmd, em_auto, EM_STATE, em_setwait)
    text = Path(__file__).read_text(encoding="utf-8")
    chk("S6 檔面:def main / def selftest / def collect · 第 3 行加速器標記 · __main__ provenance 守門在 --selftest 之前 · 零 TA-Lib · 不寫同意閘",
        "\ndef main(" in text and "\ndef selftest(" in text and "\ndef collect(" in text and text.splitlines()[2].strip() == "# [VIA:ACCEL-BRIDGE:v0111]"
        and text.index('sys.argv[1:2] == ["provenance"]') < text.index('"--selftest" in sys.argv:')
        and "import " + "talib" not in text and "environ[\"VIA_NET" + "_CONSENT\"] =" not in text)
    print("  ── 前版 %s 自測(本版換裝卸下,照前版原行為)──" % PRIOR_PATH.name, flush=True)
    uninstall()
    try:
        with prior_world(FAMILY):
            prior_rc = int(PRIOR.selftest() or 0)
    finally:
        install()
    chk("S7 前版 %s 自測照過" % PRIOR_PATH.name, prior_rc == 0, prior_rc)
    n = sum(ok)
    print("[計] %s %s(%s_%s.py)自測 %d/%d · %s" % (DISPLAY_NAME, TAG, FAMILY, TAG, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    return 0 if n == len(ok) else 1


if __name__ == "__main__":
    if sys.argv[1:2] == ["provenance"]:     # 同前版:provenance 先於任何 --selftest 攔截
        sys.exit(provenance(sys.argv[2:]))
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.exit(main(sys.argv[1:]))
