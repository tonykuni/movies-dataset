#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0285 — 薄尾(v0284 以前一字不動):備份整段串行化(PR 715 Codex P2:兩個 launch 同時跑會刪掉對方的暫存夾)

  v0284 發布後會清掉備份夾裡所有 .partial —— 另一個同時在跑的 launch --run 正在驗證的暫存夾也被刪 → 對方 FileNotFoundError,
  刪在「驗完、發布前」那一刻時例外還會跑出例外處理範圍、整個 launch 中斷。
  本版:備份整段(複製 · 驗 · 發布 · 修剪 · 清舊暫存)用作業系統檔案鎖 <備份夾>\\.vrn_backup.lock 串行化(CLAUDE.md「共用冊寫入要鎖」);
  等鎖最多 VIA_VRN_BACKUP_WAIT_S 秒(預設 600)· 等不到 = 這輪不備份(黃)、不碰任何暫存夾;拿到鎖時沒有別人在備份,剩下的 .partial 才是當掉留下的。
  備份階段任何 OSError(含發布那一步)一律回紅、不讓 launch 中斷;舊備份照樣不動。其餘全照 v0284。用法同 v0283。
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
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import importlib.util
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAMILY = "VRN_SystemManager"
TAG = "VRN_SystemManager v0285"
LOCK_NAME = ".vrn_backup.lock"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0285", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
_BACKUP_V0284 = PRIOR.backup_db                     # v0284 本體(驗過才發布)
V0283 = PRIOR.PRIOR                                 # launch_run 叫的是 v0283 模組全域 backup_db


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


class BackupLock:
    """作業系統檔案鎖(Windows msvcrt · 其他 fcntl);鎖檔不刪(刪了別人可能正鎖著另一個 inode)。"""

    def __init__(self, base: Path):
        self.path = Path(base) / LOCK_NAME
        self.fh = None

    def acquire(self, wait_s: float) -> bool:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.fh = open(self.path, "a+b")
        end = time.time() + max(0.0, wait_s)
        while True:
            try:
                if os.name == "nt":
                    import msvcrt
                    self.fh.seek(0)
                    msvcrt.locking(self.fh.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(self.fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                return True
            except OSError:
                if time.time() >= end:
                    self.fh.close()
                    self.fh = None
                    return False
                time.sleep(0.2)

    def release(self) -> None:
        if self.fh is None:
            return
        try:
            if os.name == "nt":
                import msvcrt
                self.fh.seek(0)
                msvcrt.locking(self.fh.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.fh.fileno(), fcntl.LOCK_UN)
        except OSError:
            pass
        self.fh.close()
        self.fh = None


def _wait_s() -> float:
    try:
        return float(os.environ.get("VIA_VRN_BACKUP_WAIT_S") or 600)
    except ValueError:
        return 600.0


def backup_db(out, dest_base: Path, now=None, keep: int = PRIOR.KEEP_BACKUPS, wait_s: float | None = None) -> dict:
    if out is None or not Path(out).is_dir():
        return _BACKUP_V0284(out, dest_base, now=now, keep=keep)          # 沒輸出夾 → 灰(不必拿鎖)
    lk = BackupLock(dest_base)
    try:
        got = lk.acquire(_wait_s() if wait_s is None else wait_s)
    except OSError as exc:
        return {"lamp": "YELLOW", "why": f"備份鎖開不了:{type(exc).__name__}: {str(exc)[:100]} · 這輪不備份"}
    if not got:
        return {"lamp": "YELLOW", "why": "另一個 launch --run 正在備份(等鎖逾時)· 這輪不備份 · 不碰任何暫存夾"}
    try:
        return _BACKUP_V0284(out, dest_base, now=now, keep=keep)          # 拿到鎖 = 沒有別人在備份 → 剩下的 .partial 才是當掉留下的
    except OSError as exc:
        return {"lamp": "RED", "why": f"備份階段出錯:{type(exc).__name__}: {str(exc)[:120]} · 舊備份不動"}
    finally:
        lk.release()


V0283.backup_db = backup_db                          # v0283 launch_run 叫模組全域 backup_db → 換上本版
PRIOR.backup_db = backup_db


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    PRIOR.TAG = TAG
    return PRIOR.main(a)


def selftest() -> int:
    import tempfile
    import threading
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    keep = (V0283.backup_db, PRIOR.backup_db)
    V0283.backup_db = PRIOR.backup_db = _BACKUP_V0284
    try:
        rc0 = PRIOR.selftest()
    finally:
        V0283.backup_db, PRIOR.backup_db = keep
    print(f"=== {TAG} · 薄尾自測(備份串行化 · 不刪別人的暫存 · 出錯回紅;暫存夾 · 零網路)===")
    chk("⓪ 直接前版 %s 自測過" % PRIOR_PATH.name, rc0 == 0, f"rc {rc0}")
    with tempfile.TemporaryDirectory() as td:
        t = Path(td)
        out = t / "db"
        out.mkdir()
        (out / "vrn.duckdb").write_bytes(b"D" * 4000)
        bb = t / "bk"
        bb.mkdir()
        other = bb / "20261122_080000.partial"                        # 另一個 launch 正在驗的暫存
        other.mkdir()
        (other / "vrn.duckdb").write_bytes(b"D" * 4000)
        holder = BackupLock(bb)
        chk("① 別人拿著備份鎖", holder.acquire(1))
        r = backup_db(out, bb, now=datetime(2026, 11, 22, 9, 0, 0), wait_s=0.5)
        chk("② Codex 重現:別人正在備份 → 本輪等鎖逾時 = 黃 · 不發布 · 別人的 .partial 原封不動", r["lamp"] == "YELLOW" and other.is_dir()
            and (other / "vrn.duckdb").is_file() and not (bb / "20261122_090000").exists(), r)
        res = {}

        def late():
            res["r"] = backup_db(out, bb, now=datetime(2026, 11, 22, 10, 0, 0), wait_s=10)
        th = threading.Thread(target=late)
        th.start()
        time.sleep(0.6)
        chk("③ 等鎖期間別人的暫存還在(本輪還沒動手)", other.is_dir() and "r" not in res)
        holder.release()
        th.join(15)
        chk("④ 別人放鎖後本輪接著做完 · 綠 · 發布", res.get("r", {}).get("lamp") == "GREEN" and (bb / "20261122_100000" / "MANIFEST.json").is_file(), res)
        chk("⑤ 拿到鎖時沒有別人在備份 → 當掉留下的 .partial 才清", not other.exists())

        class _Boom:
            def __getattr__(self, n):
                return getattr(os, n)

            @staticmethod
            def replace(a, b):
                raise PermissionError("被防毒軟體鎖住")
        real_os = PRIOR.os
        PRIOR.os = _Boom()
        try:
            r2 = backup_db(out, bb, now=datetime(2026, 11, 22, 11, 0, 0), wait_s=1)
        finally:
            PRIOR.os = real_os
        chk("⑥ 發布那一步出錯(OSError)→ 紅 · 不丟例外 · 舊備份還在", r2["lamp"] == "RED" and (bb / "20261122_100000" / "MANIFEST.json").is_file(), r2)
        chk("⑦ 鎖檔留著(不刪鎖)· 鎖已放開(下一輪拿得到)", (bb / LOCK_NAME).is_file() and BackupLock(bb).acquire(0.5))
        chk("⑧ 沒輸出夾 → 灰,不必拿鎖", backup_db(None, t / "nolock")["lamp"] == "GRAY" and not (t / "nolock").exists())
    chk("⑨ 換裝:v0283 launch_run 叫到的 backup_db = 本版", V0283.backup_db is backup_db and PRIOR.backup_db is backup_db)
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    peer = [k for k in ("VIA_FROM_VCGC", "VIA_FROM_VDFSM") if re.search(r"environ(?:\[[\"']%s[\"']\]\s*=|\.setdefault\([\"']%s)" % (k, k), body)]
    chk("⑩ 系統獨立:不設他系統的入口旗標(本檔是 VRN 自己的入口;VCGC 只支援不干涉)", not peer, peer)
    chk("⑪ 加速器橋在;不出網 · 不碰 TA-Lib · 不寫契約檔 / 資產冊", "[VIA:ACCEL-BRIDGE:v0100]" in src and "_via_net()." not in body
        and "talib" not in body.lower() and "VRN_NUMBER_REQUEST" not in body and "Asset_Register" not in body)
    pub = [n for n in dir(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n, None))]
    chk("⑫ 尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in pub), f"{len(pub)} 支")
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
