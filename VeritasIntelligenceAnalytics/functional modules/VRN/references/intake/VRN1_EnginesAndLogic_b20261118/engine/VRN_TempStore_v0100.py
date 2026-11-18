#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===== [VRN:ID:v0100] VRN-ENG008 · VRN_TempStore_v0100 v0100 · RUNTIME TEMP 與刪除原則 =====
# AST 注入（只加註解，AST 不變）：類別 0 · 函式 19；逐一編號在 ssot/VRN_ID_SSOT_v0100.json
# ===== [VRN:ID:END] =====
"""
VRN_TempStore v0100 -- TEMP takes load off memory, under written deletion rules.

Operator 2026-10-10: 「善用TEMP補強記憶體 但刪除原則要建立」.

Same convention as the mother's SUP_MDL867_TempSpill (L107 · R-TEMP-01), so VRN and the rest of VIA share one TEMP
root and one purge ledger: VIA_TEMP_ROOT (default %LOCALAPPDATA%\\Temp\\VIA_progress) / <tool> / run_<time>_<pid>,
TMP / TEMP / TMPDIR / POLARS_TEMP_DIR / VIA_DUCKDB_TEMP_DIR point into the run folder while it is open, the last N
runs are kept, and every deletion is appended to purge_ledger.jsonl.  VRN's own code, stdlib only; the rules
are written in ssot/VRN_TEMP_POLICY_v0100.json and enforced here:

  1. only run_* folders of VRN's own tools under the TEMP root are ever deleted
  2. a folder is deleted only when it carries VRN's owner marker (.vrn_temp_owner.json) naming that tool
  3. links are never followed; a folder that resolves outside the TEMP root is never touched
  4. never-delete words (mother L107 + VRN): VIA_Reports, supportive modules, functional modules, .git, registry, ssot
  5. rolling: when a run opens, only the newest N runs of that tool stay (VIA_TEMP_KEEP, default 5, this run included)
  6. size cap: above VIA_TEMP_MAX_GB (default 10) the oldest runs go first; a run that is open is never deleted --
     every open run holds an exclusive lock on <run>/.vrn_temp_lock (taken before its marker is written), and a
     sweep skips any run whose lock it cannot take, whichever process owns it
  7. every deletion is one line in purge_ledger.jsonl (time, tool, folder, MB, rule, result); a delete that did not
     remove the folder (a file in use on Windows) is recorded as FAILED, never as done
  8. samples, reports and truth files never go to TEMP; TEMP holds only what can be computed again
  9. closing a run puts TMP / TEMP back as they were

LIVE off, no network.
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

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

TEMP_VERSION = "v0100"
ENGINE = "VRN_TempStore_v0100"
MARKER = ".vrn_temp_owner.json"
LOCK = ".vrn_temp_lock"
LEDGER = "purge_ledger.jsonl"
ENV_KEYS = ("TMP", "TEMP", "TMPDIR", "POLARS_TEMP_DIR", "VIA_DUCKDB_TEMP_DIR")
NEVER_DELETE = ("VIA_Reports", "supportive modules", "functional modules", ".git", "registry", "ssot")
DEFAULT_KEEP = 5
DEFAULT_MAX_GB = 10.0
POLICY_BOOK = Path(__file__).resolve().parents[1] / "ssot" / "VRN_TEMP_POLICY_v0100.json"
_SAVED_ENV: dict = {}
LAST_SWEEP: list = []
_HELD: dict = {}                                       # this process's open runs -> their locked handle


# [VRN-ID] VRN-ENG008-FNC017 · LOGIC
def _try_lock(handle) -> bool:
    """Exclusive, non-blocking lock on byte 0 (flock on POSIX, msvcrt.locking on Windows).  Never signals a process."""
    try:
        handle.seek(0)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except OSError:
        return False


# [VRN-ID] VRN-ENG008-FNC018 · LOGIC
def _unlock(handle) -> None:
    try:
        handle.seek(0)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    except OSError:
        pass


# [VRN-ID] VRN-ENG008-FNC019 · LOGIC
def _in_use(run: Path) -> bool:
    """True while some process (this one included) holds the run's lock; a lock we cannot even open counts as held."""
    if str(run) in _HELD:
        return True
    lock = run / LOCK
    if not lock.is_file():
        return False
    try:
        handle = open(lock, "r+b")
    except OSError:
        return True
    try:
        if _try_lock(handle):
            _unlock(handle)
            return False
        return True
    finally:
        handle.close()


# [VRN-ID] VRN-ENG008-FNC001 · LOGIC
def temp_root() -> Path:
    """The shared TEMP root (same rule as the mother's SUP_MDL867)."""
    r = os.environ.get("VIA_TEMP_ROOT")
    if not r:
        base = os.environ.get("LOCALAPPDATA") or tempfile.gettempdir()
        r = str(Path(base) / "Temp" / "VIA_progress")
    p = Path(r)
    p.mkdir(parents=True, exist_ok=True)
    return p


# [VRN-ID] VRN-ENG008-FNC002 · LOGIC
def policy() -> dict:
    """keep / max_gb from the policy book, overridden by VIA_TEMP_KEEP / VIA_TEMP_MAX_GB."""
    book = {}
    try:
        book = json.loads(POLICY_BOOK.read_text(encoding="utf-8")).get("limits", {})
    except Exception:
        book = {}
    keep = int(os.environ.get("VIA_TEMP_KEEP") or book.get("keep_last_runs") or DEFAULT_KEEP)
    max_gb = float(os.environ.get("VIA_TEMP_MAX_GB") or book.get("max_gb") or DEFAULT_MAX_GB)
    return {"keep": max(1, keep), "max_gb": max(0.1, max_gb)}


# [VRN-ID] VRN-ENG008-FNC003 · LOGIC
def current_run():
    """The open run (shared with in-process engines through VRN_TEMP_RUN), or None."""
    path = os.environ.get("VRN_TEMP_RUN")
    if path and (Path(path) / MARKER).is_file():
        return Path(path)
    return None


# [VRN-ID] VRN-ENG008-FNC004 · LOGIC
def _size(path: Path) -> int:
    total = 0
    for dirpath, _dirs, files in os.walk(path, followlinks=False):
        for f in files:
            try:
                total += os.lstat(os.path.join(dirpath, f)).st_size
            except OSError:
                pass
    return total


# [VRN-ID] VRN-ENG008-FNC005 · LOGIC
def _deletable(run: Path, tool: str, root: Path):
    """Why a folder may NOT be deleted (None = it may)."""
    if run.is_symlink():
        return "link"
    try:
        resolved = run.resolve()
        resolved.relative_to(root.resolve())
    except (OSError, ValueError):
        return "outside TEMP root"
    if any(word.casefold() in str(resolved).casefold() for word in NEVER_DELETE):
        return "never-delete word in path"
    try:
        owner = json.loads((run / MARKER).read_text(encoding="utf-8"))
    except Exception:
        return "no VRN owner marker"
    if owner.get("tool") != tool or owner.get("engine") != ENGINE:
        return "marker names another tool"
    if _in_use(run):
        return "active run (lock held)"
    return None


# [VRN-ID] VRN-ENG008-FNC006 · LOGIC
def _ledger(root: Path, row: dict) -> None:
    with open(root / LEDGER, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


# [VRN-ID] VRN-ENG008-FNC007 · LOGIC
def sweep(tool: str, keep: int, max_gb: float, current=None) -> list:
    """Rules 5 and 6; rules 1-4 decide each folder; rule 7 records it.  Returns the deletions."""
    root = temp_root()
    tdir = root / tool
    if not tdir.is_dir():
        return []
    runs = sorted((p for p in tdir.iterdir() if p.name.startswith("run_") and (p.is_dir() or p.is_symlink())), key=lambda p: p.name)
    gone = []

    # [VRN-ID] VRN-ENG008-FNC008 · LOGIC
    def drop(run: Path, rule: str) -> None:
        why_not = _deletable(run, tool, root)
        if why_not:
            gone.append({"folder": run.name, "deleted": False, "rule": rule, "kept_because": why_not})
            return
        mb = round(_size(run) / 1048576, 2)
        shutil.rmtree(run, ignore_errors=True)
        done = not run.exists()                       # rmtree hides errors: the folder itself says whether it went
        row = {"at": datetime.now().isoformat(timespec="seconds"), "tool": tool, "purged": run.name, "mb": mb,
               "rule": rule, "by": ENGINE, "result": "DELETED" if done else "FAILED"}
        _ledger(root, row)
        gone.append(dict(row, folder=run.name, deleted=done, **({} if done else {"kept_because": "delete failed (file in use?)"})))

    others = [r for r in runs if current is None or r.name != current.name]
    for run in others[:max(0, len(others) - (keep - 1 if current is not None else keep))]:
        drop(run, f"keep_last={keep}")
    cap = max_gb * 1024 ** 3
    left = [r for r in others if r.exists()]
    while left and _size(tdir) > cap:
        run = left.pop(0)
        drop(run, f"max_gb={max_gb:g}")
        if run.exists():                     # kept on purpose (no marker / link): the cap cannot be reached by force
            continue
    return gone


# [VRN-ID] VRN-ENG008-FNC009 · IO
def open_run(tool: str = "VRN_Main", redirect: bool = True, keep=None, max_gb=None) -> Path:
    """Open this process's run folder (marker first), point TMP / TEMP at it, then sweep the older runs."""
    pol = policy()
    keep = int(keep or pol["keep"])
    max_gb = float(max_gb or pol["max_gb"])
    tdir = temp_root() / tool
    tdir.mkdir(parents=True, exist_ok=True)
    # Windows 的系統時鐘一格約 15.6 ms，同一個 process 連開兩次 run 會拿到同一個 %f，
    # 名字就撞了，mkdir(exist_ok=False) 直接丟 FileExistsError 把整輪帶走
    # （2026-10-19 Windows CI 實際紅過：run_20261019_072539_803660_6732）。
    # 撞了就在後面補序號。時間戳在最前面，所以 sweep 照名字排序的「舊的在前」不受影響，
    # 同一格時間內也還是先建的排前面。exist_ok=True 不能用 —— 那會讓兩個 run 共用一個資料夾。
    stem = "run_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f") + f"_{os.getpid()}"
    for attempt in range(1, 1000):
        run = tdir / (stem if attempt == 1 else f"{stem}_{attempt}")
        try:
            run.mkdir(parents=True, exist_ok=False)
            break
        except FileExistsError:
            continue
    else:
        raise RuntimeError(f"cannot find a free TEMP run name under {tdir} (tried {stem} and 998 more)")
    handle = open(run / LOCK, "w+b")                 # lock first, marker second: no sweep ever sees it marked and idle
    handle.write(b"\0")
    handle.flush()
    if not _try_lock(handle):
        handle.close()
        raise RuntimeError(f"cannot lock new TEMP run {run}")
    _HELD[str(run)] = handle
    (run / MARKER).write_text(json.dumps({"tool": tool, "engine": ENGINE, "pid": os.getpid(),
                                          "created": datetime.now().isoformat(timespec="seconds"),
                                          "policy": str(POLICY_BOOK.name)}, ensure_ascii=False), encoding="utf-8")
    os.environ["VRN_TEMP_RUN"] = str(run)
    if redirect:
        _SAVED_ENV.clear()
        for key in ENV_KEYS:
            _SAVED_ENV[key] = os.environ.get(key)
            os.environ[key] = str(run)
        _SAVED_ENV["__tempdir__"] = tempfile.tempdir
        tempfile.tempdir = str(run)
    LAST_SWEEP[:] = sweep(tool, keep, max_gb, current=run)
    return run


# [VRN-ID] VRN-ENG008-FNC010 · IO
def close_run(drop: bool = False) -> dict:
    """Rule 9: TMP / TEMP back as they were.  drop=True (or VRN_TEMP_DROP_AT_END=1) also deletes this run now."""
    run = current_run()
    for key, value in list(_SAVED_ENV.items()):
        if key == "__tempdir__":
            tempfile.tempdir = value
        elif value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
    _SAVED_ENV.clear()
    out = {"run": str(run) if run else None, "mb": round(_size(run) / 1048576, 2) if run else 0.0, "dropped": False}
    os.environ.pop("VRN_TEMP_RUN", None)
    handle = _HELD.pop(str(run), None) if run is not None else None
    if handle is not None:                            # the run is over: its lock goes, so a later sweep may roll it
        _unlock(handle)
        handle.close()
    if run is not None and (drop or os.environ.get("VRN_TEMP_DROP_AT_END") == "1"):
        tool = run.parent.name
        if _deletable(run, tool, temp_root()) is None:
            shutil.rmtree(run, ignore_errors=True)
            out["dropped"] = not run.exists()
            _ledger(temp_root(), {"at": datetime.now().isoformat(timespec="seconds"), "tool": tool, "purged": run.name,
                                  "mb": out["mb"], "rule": "drop_at_end", "by": ENGINE,
                                  "result": "DELETED" if out["dropped"] else "FAILED"})
    return out


# [VRN-ID] VRN-ENG008-FNC011 · LOGIC
def _slot(bucket: str, key: str):
    run = current_run()
    if run is None:
        return None
    folder = run / bucket
    folder.mkdir(parents=True, exist_ok=True)
    return folder / (hashlib.sha1(key.encode("utf-8")).hexdigest()[:20] + ".json")


# [VRN-ID] VRN-ENG008-FNC012 · IO
def put_json(bucket: str, key: str, obj) -> str:
    """Write obj to this run (atomic rename); returns the reference, or '' when no run is open (caller keeps it in memory)."""
    path = _slot(bucket, key)
    if path is None:
        return ""
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)
    return str(path)


# [VRN-ID] VRN-ENG008-FNC013 · IO
def get_json(ref: str, default=None):
    try:
        return json.loads(Path(ref).read_text(encoding="utf-8")) if ref else default
    except Exception:
        return default


# [VRN-ID] VRN-ENG008-FNC014 · LOGIC
def status() -> dict:
    run = current_run()
    return {"engine": ENGINE, "root": str(temp_root()), "run": str(run) if run else None,
            "mb": round(_size(run) / 1048576, 2) if run else 0.0, "policy": policy(),
            "env": {k: os.environ.get(k) for k in ENV_KEYS}}


# [VRN-ID] VRN-ENG008-FNC015 · ENTRY
def selftest() -> int:
    checks = []
    saved = {k: os.environ.get(k) for k in ("VIA_TEMP_ROOT", "VRN_TEMP_RUN", "VIA_TEMP_KEEP", "VIA_TEMP_MAX_GB") + ENV_KEYS}
    old_tempdir = tempfile.tempdir
    try:
        with tempfile.TemporaryDirectory() as td:
            os.environ["VIA_TEMP_ROOT"] = td
            runs = []
            for _ in range(4):
                runs.append(open_run("selftest_tool", keep=2))
                close_run()
                time.sleep(0.002)
            left = sorted(p.name for p in (Path(td) / "selftest_tool").iterdir())
            checks.append(("rolling keeps the newest 2", left == sorted(r.name for r in runs[-2:])))
            stray = Path(td) / "selftest_tool" / "run_00000000_000000_000000_1"
            stray.mkdir()
            temp_before, tempdir_before = os.environ.get("TEMP"), tempfile.gettempdir()
            run = open_run("selftest_tool", keep=1)
            checks.append(("a folder without the VRN marker is never deleted", stray.is_dir()))
            checks.append(("TMP / TEMP point into the open run", os.environ["TEMP"] == str(run) and tempfile.gettempdir() == str(run)))
            ref = put_json("pages", "a.pdf", {"lines": ["x"]})
            checks.append(("spill and read back", get_json(ref) == {"lines": ["x"]}))
            close_run()
            checks.append(("closing puts TEMP back", os.environ.get("TEMP") == temp_before and tempfile.gettempdir() == tempdir_before))
            led = (Path(td) / LEDGER).read_text(encoding="utf-8").splitlines()
            checks.append(("every deletion is in the ledger", len(led) >= 3 and all(json.loads(l)["by"] == ENGINE for l in led)))
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        tempfile.tempdir = old_tempdir
    for name, ok in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    failed = sum(1 for _, ok in checks if not ok)
    print(f"[TEMPSTORE] {TEMP_VERSION} · {len(checks) - failed}/{len(checks)}")
    return 1 if failed else 0


# [VRN-ID] VRN-ENG008-FNC016 · ENTRY
def main(argv=None):
    parser = argparse.ArgumentParser(description="VRN TEMP store and its deletion rules")
    parser.add_argument("command", nargs="?", default="selftest", choices=("selftest", "status"))
    args = parser.parse_args(argv)
    if args.command == "status":
        print(json.dumps(status(), ensure_ascii=False, indent=1))
        return 0
    return selftest()


if __name__ == "__main__":
    sys.exit(main())
