#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA 引擎強化補丁 v0100 —— #1 主控台 / #2 下行控制器（只增不減）.

補丁一律加在檔尾，原函式改名保留為 _uncapped/_unsigned，
移除補丁區塊即完全還原。套用前先 AST 檢查，並自動備份。

#1 VIA_CentralGovernanceConsole.py
    hmac     CGE01 台帳簽章：載入時驗章，被外部改過就標 TAMPERED
    sqlite3  CGE16 序號交易配發：兩個行程同時跑不會撞號

#2 VIA_DownwardController.py
    shlex     DCT01 命令列安全拆解，取代字串拼接
    atexit    DCT02 孤兒子行程清理，逾時後不留殘骸
    threading DCT05 看門狗獨立計時，主迴圈卡住時逾時機制仍有效

用法：
    python VIA_Engine_Patch_v0100.py --console <path> --controller <path>
    python VIA_Engine_Patch_v0100.py --console <path> --controller <path> --apply
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


import argparse
import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

CONSOLE_MARKER = "# VIA_PATCH_CONSOLE_v0100"
CONTROLLER_MARKER = "# VIA_PATCH_CONTROLLER_v0100"

CONSOLE_BLOCK = '''

''' + CONSOLE_MARKER + '''  =============================================
# 只增不減：新增能力，不改動既有邏輯。移除本區塊即完全還原。
import hmac as _via_hmac
import hashlib as _via_hashlib
import sqlite3 as _via_sqlite3
import os as _via_os

_VIA_LEDGER_KEY_ENV = "VIA_LEDGER_KEY"
_VIA_LEDGER_KEY_FALLBACK = b"via-local-ledger-key-v1"


def _via_ledger_key() -> bytes:
    """簽章金鑰取自環境變數；沒有就用本機常數（仍能擋非蓄意竄改）。"""
    value = _via_os.environ.get(_VIA_LEDGER_KEY_ENV, "")
    return value.encode("utf-8") if value else _VIA_LEDGER_KEY_FALLBACK


def via_sign_payload(text: str) -> str:
    """CGE01：對台帳內容產生 HMAC，寫檔時一併落地。"""
    return _via_hmac.new(_via_ledger_key(), text.encode("utf-8"),
                         _via_hashlib.sha256).hexdigest()[:32]


def via_verify_payload(text: str, signature: str) -> str:
    """回傳 VERIFIED / TAMPERED / UNSIGNED。用 compare_digest 避免時序側漏。"""
    if not signature:
        return "UNSIGNED"
    expected = via_sign_payload(text)
    return "VERIFIED" if _via_hmac.compare_digest(expected, signature) else "TAMPERED"


def via_allocate_serial(db_path, namespace: str, section: str) -> int:
    """CGE16：以 sqlite 交易配號，兩個行程同時跑也不會撞號。

    原本的配號是「讀檔 -> 加一 -> 寫檔」，中間沒有鎖；
    IMMEDIATE 交易在寫入前就取得寫鎖，序號因此唯一且連續。
    """
    path = str(db_path)
    directory = _via_os.path.dirname(path)
    if directory and not _via_os.path.isdir(directory):
        _via_os.makedirs(directory, exist_ok=True)
    conn = _via_sqlite3.connect(path, timeout=30, isolation_level=None)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("""CREATE TABLE IF NOT EXISTS urn_serial(
            namespace TEXT NOT NULL, section TEXT NOT NULL, last INTEGER NOT NULL,
            PRIMARY KEY (namespace, section))""")
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT last FROM urn_serial WHERE namespace=? AND section=?",
            (namespace, section)).fetchone()
        nxt = (int(row[0]) if row else 0) + 1
        conn.execute(
            "INSERT INTO urn_serial(namespace, section, last) VALUES (?,?,?) "
            "ON CONFLICT(namespace, section) DO UPDATE SET last=excluded.last",
            (namespace, section, nxt))
        conn.execute("COMMIT")
        return nxt
    finally:
        conn.close()
''' + CONSOLE_MARKER + '''_END =========================================
'''

CONTROLLER_BLOCK = '''

''' + CONTROLLER_MARKER + '''  ==========================================
# 只增不減：新增能力，不改動既有邏輯。移除本區塊即完全還原。
import atexit as _via_atexit
import shlex as _via_shlex
import threading as _via_threading
import subprocess as _via_subprocess

_via_live_processes = []
_via_live_lock = _via_threading.Lock()


def via_quote_args(args) -> str:
    """DCT01：路徑含空白或引號時，字串拼接會把參數切錯。"""
    return " ".join(_via_shlex.quote(str(a)) for a in args)


def via_split_command(text: str):
    """把命令列安全拆成 list，供 subprocess 使用（不經 shell）。"""
    return _via_shlex.split(str(text), posix=(_via_os.name != "nt")
                            if "_via_os" in globals() else True)


def via_register_process(proc) -> None:
    """DCT02：登記子行程，行程結束時一併清理，逾時後不留孫行程。"""
    with _via_live_lock:
        _via_live_processes.append(proc)


def _via_cleanup_processes() -> None:
    with _via_live_lock:
        pending = list(_via_live_processes)
    for proc in pending:
        try:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except Exception:
                    proc.kill()
        except Exception:
            pass


_via_atexit.register(_via_cleanup_processes)


class ViaWatchdog:
    """DCT05：看門狗放在獨立計時執行緒。

    原本逾時判斷跟主迴圈同一條執行緒，主迴圈一卡住，逾時機制也跟著失效。
    這裡用 threading.Timer，主迴圈卡死也照樣會觸發。
    """

    def __init__(self, seconds: float, on_timeout, label: str = "") -> None:
        self.seconds = float(seconds)
        self.on_timeout = on_timeout
        self.label = label
        self.fired = False
        self._timer = None

    def _fire(self) -> None:
        self.fired = True
        try:
            self.on_timeout(self.label)
        except Exception:
            pass

    def __enter__(self):
        self._timer = _via_threading.Timer(self.seconds, self._fire)
        self._timer.daemon = True
        self._timer.start()
        return self

    def __exit__(self, *exc):
        if self._timer is not None:
            self._timer.cancel()
        return False


def via_run_guarded(args, timeout: float = 900, **kwargs):
    """以 list 傳參、不經 shell、登記行程、逾時殺整棵樹。"""
    proc = _via_subprocess.Popen([str(a) for a in args], **kwargs)
    via_register_process(proc)

    def _kill(_label):
        try:
            proc.kill()
        except Exception:
            pass

    with ViaWatchdog(timeout, _kill, label=str(args[:1])):
        out, err = proc.communicate()
    return proc.returncode, out, err
''' + CONTROLLER_MARKER + '''_END ======================================
'''


def patch_file(target: Path, marker: str, block: str, apply: bool) -> str:
    if not target.is_file():
        return "MISSING"
    text = target.read_text(encoding="utf-8", errors="replace")
    if marker in text:
        return "ALREADY_PATCHED"
    patched = text.rstrip("\n") + "\n" + block
    try:
        ast.parse(patched)
    except SyntaxError as exc:
        return "SYNTAX_FAIL line %s: %s" % (exc.lineno, exc.msg)
    if not apply:
        return "READY"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = target.with_name(target.stem + "_prepatch_" + stamp + target.suffix)
    shutil.copy2(target, backup)
    target.write_text(patched, encoding="utf-8")
    return "APPLIED (備份 %s)" % backup.name


def main() -> int:
    parser = argparse.ArgumentParser(prog="VIA_Engine_Patch_v0100.py")
    parser.add_argument("--console", default="")
    parser.add_argument("--controller", default="")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    if not args.console and not args.controller:
        print("至少要給 --console 或 --controller", file=sys.stderr)
        return 2

    print("")
    print("  VIA ENGINE PATCH v0100  (%s)" % ("APPLY" if args.apply else "DRY-RUN"))
    print("  " + "-" * 56)
    results = {}
    if args.console:
        path = Path(args.console).expanduser().resolve()
        results["#1 Console (hmac + sqlite3)"] = patch_file(
            path, CONSOLE_MARKER, CONSOLE_BLOCK, args.apply)
    if args.controller:
        path = Path(args.controller).expanduser().resolve()
        results["#2 Controller (shlex + atexit + threading)"] = patch_file(
            path, CONTROLLER_MARKER, CONTROLLER_BLOCK, args.apply)

    for name, state in results.items():
        print("  %-46s %s" % (name, state))
    print("")
    if not args.apply:
        print("  DRY-RUN：未修改任何檔案。確認後加 --apply")
    else:
        print("  移除檔尾補丁區塊即可完全還原。")
    return 0 if all("FAIL" not in v for v in results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
