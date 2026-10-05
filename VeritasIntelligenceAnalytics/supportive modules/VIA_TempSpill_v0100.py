#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_TempSpill v0100 — TEMP 律(L115)的 Python 側:記憶體不足時把中間資料溢寫到 TEMP,分塊處理;只寫自家夾、不改環境、一行帳。

引擎用法(任何 .py,零相依;pandas/pyarrow 有就用,沒有退 pickle):
    from VIA_TempSpill_v0100 import TempSpill
    ts = TempSpill()                       # 讀 VIA_SPILL_DIR / VIA_LOW_RAM(骨架 v0110 Initialize-VCTemp 設);沒設就用 %TEMP%/VIA_spill/<pid>
    for chunk in ts.chunks(rows, 50_000):  # 分塊
        path = ts.spill(df_chunk, "fin_tables")   # 溢寫(低 RAM 或 force=True 才真寫;否則回 None 讓你留在記憶體)
    for df in ts.iter_spilled("fin_tables"): ...
    ts.close()                             # 清自家夾(保留最後一輪供貼回),記帳
律:① 只寫 VIA_SPILL_DIR 底下自家子夾;② 總量上限 VIA_SPILL_CAP_GB(預設 2)超過先清最舊自家塊;③ 不改 TEMP 環境變數、不碰別人;④ 每次 close 一行帳 spill_ledger.jsonl(寫了幾塊、幾 MB、當時可用 RAM)。
動詞: --selftest · --demo(溢寫 30MB 再讀回)· --law-append(把 L115 附進 VIA_Policy_Laws_SSOT 尾版出新版;VCGC 自己的冊)
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
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: F401
except ImportError:
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import datetime
import json
import os
import pickle
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path

ME = Path(__file__).resolve()
TAG = "v0100"

L115 = {
    "id": "L115", "batch": "側線 2026-10-06", "cat": "治理 / TEMP 與記憶體", "key": "TEMP_LAW",
    "zh": ("【TEMP 律】① TEMP 是記憶體的延伸不是垃圾場:PS 只寫 %LOCALAPPDATA%\\Temp\\VIA_progress\\ps_<run>\\,PY 只寫其下 spill\\(VIA_SPILL_DIR),每輪一夾、夾名 = run stamp;"
           "② 清理只清自家夾:滾動留 N 輪(預設 5)+ 總量上限(預設 2 GB)超過從最舊自家夾清;帶 RUNNING 鎖或 2 小時內的不清;絕不碰非 VIA 的 Temp;"
           "③ 不弄亂紀錄:每清一夾、每次溢寫 close 各一行帳(purge_ledger.jsonl / spill_ledger.jsonl,含 bytes 與當時可用 RAM),只增不覆寫;"
           "④ 記憶體不足支援:可用 RAM 低於門檻(預設 2 GB)時骨架設 VIA_LOW_RAM=1,引擎經 VIA_TempSpill 分塊 + 溢寫 TEMP(parquet / pickle),不改 pagefile、不 EmptyWorkingSet、不動他人行程;"
           "⑤ 不改現有環境:TEMP/TMP 只在本行程內改並於退出還原(骨架 EnvBackup);⑥ 夾留到滾動期滿才清,供事後貼回;崩潰夾(RUNNING 殘留)多留 2 輪。"),
    "status": "ACTIVE", "origin": "操作員原文下令 2026-10-06(有效的 TEMP 使用清除規範 · 不影響現環境與紀錄 · 不可大幅增加 · 充分支援記憶體不足)",
    "enforcement": "VeritasCeleritas.PS7.Skeleton-v0110 Initialize-VCTemp(② 段)· VIA_TempSpill_v0100.py(PY 側)· 全景 K7/K3 可加 TEMP 夾總量檢查",
}


def _now() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


def free_ram_gb() -> float:
    """可用 RAM(GB);Windows 走 GlobalMemoryStatusEx,Linux 讀 /proc/meminfo,都沒有回 -1(不裝猜)。"""
    try:
        if os.name == "nt":
            import ctypes

            class _MS(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong), ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong), ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong), ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
            ms = _MS()
            ms.dwLength = ctypes.sizeof(_MS)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(ms))
            return round(ms.ullAvailPhys / (1024 ** 3), 2)
        mi = Path("/proc/meminfo")
        if mi.exists():
            for ln in mi.read_text().splitlines():
                if ln.startswith("MemAvailable:"):
                    return round(int(ln.split()[1]) / (1024 ** 2), 2)
    except Exception:  # noqa: BLE001
        pass
    return -1.0


class TempSpill:
    def __init__(self, name: str | None = None, cap_gb: float | None = None, low_ram_gb: float | None = None, force: bool = False):
        base = os.environ.get("VIA_SPILL_DIR") or str(Path(os.environ.get("TEMP") or os.environ.get("TMP") or tempfile.gettempdir()) / "VIA_spill" / ("py_%d" % os.getpid()))
        self.root = Path(base)
        self.name = re.sub(r"[^A-Za-z0-9_]+", "_", name or Path(sys.argv[0]).stem or "engine")
        self.dir = self.root / self.name
        self.dir.mkdir(parents=True, exist_ok=True)
        self.cap = float(cap_gb if cap_gb is not None else os.environ.get("VIA_SPILL_CAP_GB", "2"))
        self.low_ram_gb = float(low_ram_gb if low_ram_gb is not None else os.environ.get("VIA_LOW_RAM_GB", "2"))
        self.force = force
        self.low = (os.environ.get("VIA_LOW_RAM") == "1") or (0 <= free_ram_gb() < self.low_ram_gb)
        self.written = 0
        self.bytes = 0
        self.purged = 0
        self._seq = 0

    @staticmethod
    def chunks(seq, n: int):
        """任何可切序列 / DataFrame 分塊。"""
        if hasattr(seq, "iloc"):
            for i in range(0, len(seq), n):
                yield seq.iloc[i:i + n]
        else:
            for i in range(0, len(seq), n):
                yield seq[i:i + n]

    def should_spill(self) -> bool:
        return self.force or self.low or (0 <= free_ram_gb() < self.low_ram_gb)

    def _enforce_cap(self) -> None:
        files = sorted(self.root.rglob("*.spill.*"), key=lambda q: q.stat().st_mtime)
        total = sum(f.stat().st_size for f in files)
        while len(files) > 1 and total > self.cap * (1024 ** 3):   # 最新一塊永遠留著,不然讀不回
            f = files.pop(0)
            try:
                sz = f.stat().st_size
                f.unlink()
                total -= sz
                self.purged += 1
            except OSError:
                break

    def spill(self, obj, tag: str = "part"):
        """低 RAM(或 force)才真寫;否則回 None。DataFrame + pyarrow → parquet;其餘 pickle。"""
        if not self.should_spill():
            return None
        self._seq += 1
        tag = re.sub(r"[^A-Za-z0-9_]+", "_", tag)
        if hasattr(obj, "to_parquet"):
            try:
                p = self.dir / ("%s_%05d.spill.parquet" % (tag, self._seq))
                obj.to_parquet(p, index=False)
            except Exception:  # noqa: BLE001 — 無 pyarrow 退 pickle
                p = self.dir / ("%s_%05d.spill.pkl" % (tag, self._seq))
                with open(p, "wb") as fh:
                    pickle.dump(obj, fh, protocol=pickle.HIGHEST_PROTOCOL)
        else:
            p = self.dir / ("%s_%05d.spill.pkl" % (tag, self._seq))
            with open(p, "wb") as fh:
                pickle.dump(obj, fh, protocol=pickle.HIGHEST_PROTOCOL)
        self.written += 1
        self.bytes += p.stat().st_size
        self._enforce_cap()
        return p

    def iter_spilled(self, tag: str = "part"):
        tag = re.sub(r"[^A-Za-z0-9_]+", "_", tag)
        for p in sorted(self.dir.glob(tag + "_*.spill.*")):
            if p.suffix == ".parquet":
                import pandas as pd  # noqa: WPS433
                yield pd.read_parquet(p)
            else:
                with open(p, "rb") as fh:
                    yield pickle.load(fh)  # noqa: S301 — 自家 TEMP 夾,自己寫的

    def close(self, keep: bool = False) -> dict:
        """清自家夾(keep=True 留給貼回),一行帳。"""
        rec = {"at": _now(), "engine": self.name, "dir": str(self.dir), "written": self.written, "mb": round(self.bytes / 1048576, 2), "purged_by_cap": self.purged, "free_ram_gb": free_ram_gb(), "low_ram": self.low, "kept": keep}
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            with open(self.root / "spill_ledger.jsonl", "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except OSError:
            pass
        if not keep:
            shutil.rmtree(self.dir, ignore_errors=True)
        return rec


def law_append(registry: Path, apply: bool = True) -> dict:
    hits = sorted(registry.glob("VIA_Policy_Laws_SSOT_v*.json"), key=lambda q: int(re.search(r"_v(\d{4})", q.name).group(1)))
    if not hits:
        return {"status": "NO_BOOK", "lamp": "RED"}
    tail = hits[-1]
    d = json.loads(tail.read_text(encoding="utf-8-sig"))
    laws = d.get("laws", [])
    if any(l.get("id") == "L115" for l in laws):
        return {"status": "SKIP", "tail": tail.name, "lamp": "GREEN"}
    nv = "v%04d" % (int(re.search(r"_v(\d{4})", tail.name).group(1)) + 1)
    new = registry / ("VIA_Policy_Laws_SSOT_%s.json" % nv)
    if new.exists():
        return {"status": "CONFLICT", "new": new.name, "lamp": "RED"}
    d["laws"] = laws + [L115]
    d["prior"] = tail.name
    d["version"] = nv
    d["ts"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    d["why_" + nv] = "%s 已發布 → 出新版;+L115 TEMP 律(操作員原文下令 2026-10-06,ACTIVE,無 rank,附於陣列尾);其餘一字不動。VIA_TempSpill_%s" % (tail.name, TAG)
    d["law_order_note"] = (d.get("law_order_note", "") + " 側線 2026-10-06:+L115 TEMP 律(只清自家夾 · 總量上限 · 低 RAM 溢寫 · 一行帳),無 rank,附於陣列尾。").strip()
    if apply:
        new.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"status": "WRITTEN" if apply else "PLAN", "tail": tail.name, "new": new.name, "laws": len(d["laws"]), "lamp": "GREEN"}


def demo(mb: int = 30) -> int:
    td = Path(tempfile.mkdtemp(prefix="viaspill-demo-"))
    os.environ["VIA_SPILL_DIR"] = str(td)
    t0 = time.time()
    ts = TempSpill("demo", force=True, cap_gb=0.02)
    rows = [{"i": i, "v": "x" * 100} for i in range(int(mb * 10_000))]
    n = 0
    for ch in TempSpill.chunks(rows, 50_000):
        ts.spill(ch, "rows")
        n += 1
    back = sum(len(c) for c in ts.iter_spilled("rows"))
    rec = ts.close()
    print("[計] tempspill demo · 寫 %d 塊 %.1f MB · 上限 0.02 GB 清 %d 塊 · 讀回 %d 列 · 可用 RAM %s GB · %.1fs · %s" % (rec["written"], rec["mb"], rec["purged_by_cap"], back, rec["free_ram_gb"], time.time() - t0, "GREEN" if rec["written"] == n else "RED"))
    shutil.rmtree(td, ignore_errors=True)
    return 0


def selftest() -> int:
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)

    td = Path(tempfile.mkdtemp(prefix="viaspill-"))
    saved = {k: os.environ.get(k) for k in ("VIA_SPILL_DIR", "VIA_LOW_RAM")}
    os.environ["VIA_SPILL_DIR"] = str(td)
    os.environ["VIA_LOW_RAM"] = "0"
    ts = TempSpill("eng_a", low_ram_gb=0)          # 門檻 0 → 不低 RAM → 不溢寫
    chk("① RAM 探針回數字或 -1(不裝猜)", isinstance(free_ram_gb(), float))
    chk("② 非低 RAM:spill 回 None,不寫檔", ts.spill([1, 2, 3]) is None and not list(ts.dir.glob("*.spill.*")))
    os.environ["VIA_LOW_RAM"] = "1"
    ts2 = TempSpill("eng_b", cap_gb=0.001)         # 1 MB 上限
    paths = [ts2.spill([("%d-" % j) * 10 for j in range(50_000)], "blk") for i in range(6)]
    left = list(ts2.dir.glob("*.spill.*"))
    chk("③ 低 RAM:真寫 · 總量上限 1 MB → 最舊自動清(剩 %d 塊 · 清 %d)" % (len(left), ts2.purged), all(paths) and ts2.purged >= 1 and len(left) < 6)
    back = list(ts2.iter_spilled("blk"))
    chk("④ 讀回剩餘塊順序正確", back and all(len(b) == 50_000 for b in back))
    rec = ts2.close()
    chk("⑤ close:自家夾清掉 · 一行帳 spill_ledger.jsonl", not ts2.dir.exists() and (td / "spill_ledger.jsonl").exists() and rec["written"] == 6)
    chk("⑥ 只寫自家夾:spill 根只有 eng_a 夾與帳本", sorted(q.name for q in td.iterdir()) == ["eng_a", "spill_ledger.jsonl"])
    chunks = list(TempSpill.chunks(list(range(10)), 4))
    chk("⑦ chunks 分塊 4/4/2", [len(c) for c in chunks] == [4, 4, 2])
    reg = td / "registry"
    reg.mkdir()
    (reg / "VIA_Policy_Laws_SSOT_v0107.json").write_text(json.dumps({"laws": [{"id": "L114", "zh": "x"}], "law_order_note": "n"}, ensure_ascii=False), encoding="utf-8")
    r1 = law_append(reg)
    r2 = law_append(reg)
    chk("⑧ law append:v0107 → v0108 +L115 · 再跑 SKIP · 原冊不動", r1["status"] == "WRITTEN" and r2["status"] == "SKIP" and json.loads((reg / "VIA_Policy_Laws_SSOT_v0108.json").read_text(encoding="utf-8"))["laws"][-1]["id"] == "L115" and len(json.loads((reg / "VIA_Policy_Laws_SSOT_v0107.json").read_text(encoding="utf-8"))["laws"]) == 1)
    body = ME.read_text(encoding="utf-8")
    chk("⑨ 帶加速器橋 · L115 條文含 ①–⑥", "[VIA:ACCEL-BRIDGE:v0100]" in body and all(k in L115["zh"] for k in "①②③④⑤⑥"))
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    shutil.rmtree(td, ignore_errors=True)
    print("[計] VIA_TempSpill_%s 自測 %d/%d · %s" % (TAG, p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a[:2]:
        return selftest()
    if "--demo" in a[:2]:
        return demo()
    if "--law-append" in a[:2]:
        reg = Path(os.environ.get("VIA_ROOT") or ME.parents[1]) / "supportive modules" / "registry"
        r = law_append(reg, apply=("--dry" not in a))
        print("[計] law append L115 · %s · %s → %s · %s" % (r["status"], r.get("tail"), r.get("new", "—"), r["lamp"]))
        return 1 if r["lamp"] == "RED" else 0
    print("[拒跑] --selftest | --demo | --law-append [--dry]")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
