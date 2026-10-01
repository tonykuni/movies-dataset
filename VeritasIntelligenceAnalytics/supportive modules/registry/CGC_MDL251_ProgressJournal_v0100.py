#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL251_ProgressJournal v0100 — 長流程逐步進度落本機暫存檔:記憶體不足 / 中斷也不丟進度,重跑同一指令就接續

操作員(R40 2026-10-01):「增加一個功能 就是記憶體不足有時容易丟進度 善用 temp 檔案放在本機」。
量到的(R40):VCGC 全功能串測(CGC_MDL224,一輪 93 站 · 456 秒)與 SDD selftests(CGC_MDL245)都把每一步結果放在記憶體,
整輪跑完才一次寫檔;工作站 SDD selftests 中途 Ctrl+C(KeyboardInterrupt)→ 已跑完的步全部白跑,鎖不成。
本模組(一把尺,L05;被兩支薄尾共用,不各寫一套):
  · 位置:VIA_PROGRESS_DIR > VIA_TEMP_ROOT > 系統暫存夾(Windows = %TEMP%,本機磁碟、不在 OneDrive、不進 git)下的 VIA_progress\。
  · 每完成一步就 append 一行 JSON 並 flush + fsync(行程被砍 / 記憶體不足當掉,前面的步都已落盤);讀時跳過寫一半的尾行。
  · 一輪 = 一個 attempt:開頭寫 _begin(context:HEAD · 會影響結果的來源 · 指令模式),正常跑完寫 _done。
    下一次同一 context 的上一輪沒有 _done → 接續:已記錄的步直接拿結果(照實標「接續」),只跑沒跑完的;context 不同(程式改了 / HEAD 換了)→ 重開一輪。
  · 每一步順手記下當下可用記憶體(MB;量不到 = None),事後看得出哪一步開始吃緊。
  · 檔案超過 KEEP_DAYS 天自動清;VIA_PROGRESS=0 一律不接續(照舊從頭跑,但仍記錄)。
零網路 · 不安裝 · 不用 TA-Lib · 只收 VCGC 呼叫(VIA_FROM_VCGC=YES)的規矩由呼叫它的引擎守。
用法(程式內):j = Journal("TestAuto", scope=VIA, context=ctx); j.begin(); r = j.get(key) or run(); j.put(key, r); j.finish()
自測:python CGC_MDL251_ProgressJournal_v0100.py --selftest
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


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====


import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ENGINE = "CGC_MDL251_ProgressJournal v0100"
KEEP_DAYS = 3


def root() -> Path:
    """Local temp root for progress journals (never the repo, never OneDrive unless the operator points it there)."""
    base = os.environ.get("VIA_PROGRESS_DIR") or os.environ.get("VIA_TEMP_ROOT") or tempfile.gettempdir()
    return Path(base) / "VIA_progress"


def free_mb() -> int | None:
    """Available physical memory in MB (Linux /proc/meminfo · Windows GlobalMemoryStatusEx); None when it can't be measured."""
    try:
        if os.name == "nt":
            import ctypes

            class MS(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong), ("ullTotalPhys", ctypes.c_ulonglong),
                            ("ullAvailPhys", ctypes.c_ulonglong), ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong), ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
            m = MS()
            m.dwLength = ctypes.sizeof(MS)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)):
                return int(m.ullAvailPhys // (1024 * 1024))
            return None
        with open("/proc/meminfo", encoding="ascii") as f:
            for line in f:
                if line.startswith("MemAvailable:"):
                    return int(line.split()[1]) // 1024
    except Exception:
        return None
    return None


def sha16(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def repo_context(via: Path, extra: str = "") -> str:
    """HEAD + changed source files (.py/.ps1/.json outside outputs; same rule as VCGC v0181) + extra (e.g. the command mode)."""
    parts = [extra]
    try:
        parts.append(subprocess.run(["git", "rev-parse", "HEAD"], cwd=via, capture_output=True, text=True, timeout=30).stdout.strip())
        st = subprocess.run(["git", "status", "--porcelain", "-uall", "--", "."], cwd=via, capture_output=True, text=True, timeout=120).stdout
    except Exception:
        return sha16("|".join(parts) + "|nogit")
    for line in st.splitlines():
        rel = line[3:].strip().strip('"').split(" -> ")[-1].replace("\\", "/")
        low = rel.lower()
        if not low.endswith((".py", ".ps1", ".psm1", ".json")):
            continue
        if any(seg in low for seg in ("via_reports/", "output_hub/", "docs/handoff/", "__pycache__/")) or "_ledger_v" in low or "via_lamplock_v" in low:
            continue
        try:
            p = (via / rel) if (via / rel).exists() else Path(rel)
            s = p.stat()
            parts.append(f"{rel}|{s.st_size}|{s.st_mtime_ns}")
        except OSError:
            parts.append(rel + "|gone")
    return sha16("\n".join(parts))


class Journal:
    """Append-only, fsync'd JSONL of one long run's finished steps; resumes the last unfinished attempt with the same context."""

    def __init__(self, name: str, scope, context: str, base: Path | None = None):
        self.name, self.context = name, context
        self.dir = Path(base) if base else root()
        self.path = self.dir / f"{name}_{sha16(str(Path(scope).resolve()))}.jsonl"
        self.done: dict = {}
        self.resumed = 0
        self.attempt = ""

    def _lines(self) -> list:
        out = []
        try:
            with open(self.path, encoding="utf-8") as f:
                for line in f:
                    try:
                        out.append(json.loads(line))
                    except ValueError:
                        continue                   # a half-written last line after a crash: skip it
        except OSError:
            pass
        return out

    def _write(self, obj: dict, mode: str = "a") -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        with open(self.path, mode, encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())

    def _sweep(self) -> None:
        cut = time.time() - KEEP_DAYS * 86400
        try:
            for q in self.dir.glob("*.jsonl"):
                if q.stat().st_mtime < cut:
                    q.unlink()
        except OSError:
            pass

    def begin(self) -> int:
        """Resume the last attempt if it never finished and its context matches; else start a new one. Returns steps resumable."""
        self._sweep()
        rows = self._lines()
        last_begin = max((i for i, r in enumerate(rows) if "_begin" in r), default=None)
        resume = (os.environ.get("VIA_PROGRESS") != "0" and last_begin is not None
                  and rows[last_begin].get("context") == self.context
                  and not any("_done" in r for r in rows[last_begin + 1:]))
        if resume:
            self.attempt = rows[last_begin]["_begin"]
            self.done = {r["key"]: r["result"] for r in rows[last_begin + 1:] if "key" in r and "result" in r}
            self.resumed = len(self.done)
            self._write({"_resume": self.attempt, "at": time.strftime("%Y-%m-%dT%H:%M:%S"), "reuse": self.resumed, "free_mb": free_mb()})
        else:
            self.attempt = f"{self.name}-{time.strftime('%Y%m%d-%H%M%S')}-{os.getpid()}"
            self.done = {}
            self._write({"_begin": self.attempt, "context": self.context, "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                         "free_mb": free_mb()}, mode="w")
        return self.resumed

    def get(self, key: str):
        return self.done.get(key)

    def put(self, key: str, result) -> None:
        self.done[key] = result
        self._write({"key": key, "result": result, "t": round(time.time(), 1), "free_mb": free_mb()})

    def finish(self) -> None:
        self._write({"_done": self.attempt, "at": time.strftime("%Y-%m-%dT%H:%M:%S"), "steps": len(self.done), "free_mb": free_mb()})


def note(j: Journal) -> str:
    return (f"[進度暫存] {j.path} · " + (f"接續上一輪沒跑完的 {j.resumed} 步(只跑剩下的)" if j.resumed else "新一輪(每步完成即落本機暫存檔)")
            + f" · 可用記憶體 {free_mb() if free_mb() is not None else '量不到'} MB")


def selftest() -> int:
    ok = []

    def chk(name, cond, detail=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(detail)) if detail else ''}")

    print(f"=== {ENGINE} · 自測(暫存沙盒)===")
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        j = Journal("Demo", scope=td, context="C1", base=base)
        chk("① 新一輪:沒有舊紀錄 → 接續 0", j.begin() == 0 and j.path.is_file())
        j.put("s1", {"rc": 0})
        j.put("s2", {"rc": 2})
        with open(j.path, "a", encoding="utf-8") as f:
            f.write('{"key": "s3", "res')                     # 行程在寫第 3 步時被砍(記憶體不足)
        j2 = Journal("Demo", scope=td, context="C1", base=base)
        chk("② 中斷後重跑同一 context:前兩步接續、寫一半的尾行跳過", j2.begin() == 2 and j2.get("s1") == {"rc": 0}
            and j2.get("s2") == {"rc": 2} and j2.get("s3") is None, j2.done)
        j2.put("s3", {"rc": 0})
        j2.finish()
        j3 = Journal("Demo", scope=td, context="C1", base=base)
        chk("③ 上一輪正常跑完(_done)→ 下一次重開新一輪,不拿舊結果", j3.begin() == 0 and j3.get("s1") is None)
        j3.put("s1", {"rc": 1})
        j4 = Journal("Demo", scope=td, context="C2", base=base)
        chk("④ context 變了(程式改了 / HEAD 換了)→ 不接續", j4.begin() == 0)
        os.environ["VIA_PROGRESS"] = "0"
        try:
            j5 = Journal("Demo", scope=td, context="C2", base=base)
            j5.put("x", 1)
            j6 = Journal("Demo", scope=td, context="C2", base=base)
            chk("⑤ VIA_PROGRESS=0 → 一律從頭(仍記錄)", j6.begin() == 0)
        finally:
            os.environ.pop("VIA_PROGRESS", None)
        rows = [json.loads(l) for l in j6.path.read_text(encoding="utf-8").splitlines() if l.strip()]
        chk("⑥ 每行帶可用記憶體欄(量不到 = None,不編造)", all("free_mb" in r for r in rows))
    m = free_mb()
    chk("⑦ 本機可用記憶體量得到或誠實回 None", m is None or (isinstance(m, int) and m > 0), m)
    old = os.environ.get("VIA_PROGRESS_DIR")
    os.environ["VIA_PROGRESS_DIR"] = "/tmp/x_via"
    try:
        chk("⑧ 位置:VIA_PROGRESS_DIR 優先,否則 VIA_TEMP_ROOT,否則系統暫存夾(本機,不在倉內)", root() == Path("/tmp/x_via") / "VIA_progress")
    finally:
        if old is None:
            os.environ.pop("VIA_PROGRESS_DIR", None)
        else:
            os.environ["VIA_PROGRESS_DIR"] = old
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑨ 加速器橋 · 網路橋在;不碰 TA-Lib", "VIA:ACCEL-BRIDGE" in src and "VIA:NET-BRIDGE" in src
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M))
    print(f"[{ENGINE}] 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    print(json.dumps({"engine": ENGINE, "root": str(root()), "free_mb": free_mb(),
                      "journals": sorted(q.name for q in root().glob("*.jsonl")) if root().is_dir() else []}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
