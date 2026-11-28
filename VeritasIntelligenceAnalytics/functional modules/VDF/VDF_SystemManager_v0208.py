#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF SystemManager v0208 — 薄尾(v0207 以前一字不動):hostrun 四件事(PR #777 Codex P2 ×4,其中一件在 PS 新版)

① check-db 回 1 一律當「欄型要處理」(黃)—— ENG232 匯不進 duckdb、開不了庫、表不在而崩,也是 rc 1 → 本該紅卻變黃。
   → 本版:rc 1 只有在輸出裡真的有那一行「] check-db · … 整數型」而且沒有 Traceback 才算黃;其餘 rc 1 照實紅。
② 逾時檢查放在「讀到下一行輸出之後」:子行程卡住不印字,逾時永遠輪不到,後面的步驟與摘要都出不來。
   → 本版:另開執行緒讀輸出,主迴圈每 0.5 秒看一次期限;到期就砍掉並收屍(wait),照實回 124。
③ v0207 自測 T3 要求「沒有資料家 → check-db 略過」,在真的有 tw_index 庫的主機上必紅(吃本機狀態)。
   → 本版自測用環境變數 VIA_VDF_DB_HOME 指到暫存夾:不存在 → 略過;夾具裡放一本庫 → 排進 check-db;
     跑前版 v0207 自測時也讓資料家指到不存在的路徑(它那一檢就只驗「沒有資料家」那條路)。
④(PS)舊摘要會被當成這一輪的:在 Invoke-VDF-HostRun-v0101.ps1 修(開跑前先刪舊摘要)。本版 hostrun 開跑時也先刪。
其餘照 v0207。零網路 · 不碰 TA-Lib · 不設同意閘 · 不 import VCGC。
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(VDF 全導入令;惰性載入=import 時零網路、零行為變更) =====
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
except Exception:  # noqa: BLE001
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT;網路只認 AegisNexus);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import os
import queue
import re
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

VERSION = "v0208"
STEM = "VDF_SystemManager"
TAG = f"VDF_SystemManager {VERSION}"
HERE = Path(__file__).resolve().parent
CHECKDB_SIG = "] check-db ·"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)                 # v0207
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


V207 = PRIOR
V194 = V207.V194


def stream(cmd: list, timeout: float, out: list) -> int:
    """輸出逐行照印並收下;期限另外看(子行程不印字也砍得掉),到期砍掉並收屍,回 124。"""
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    for k in ("VIA_NET_CONSENT", "VIA_SCRAPE_CONSENT"):
        env.pop(k, None)
    p = subprocess.Popen(cmd, cwd=tempfile.gettempdir(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                         encoding="utf-8", errors="replace", env=env, stdin=subprocess.DEVNULL)
    q: queue.Queue = queue.Queue()

    def reader():
        for ln in p.stdout:
            q.put(ln)
        q.put(None)

    th = threading.Thread(target=reader, daemon=True)
    th.start()
    deadline = time.time() + timeout
    done = False
    while True:
        try:
            ln = q.get(timeout=0.5)
        except queue.Empty:
            ln = ""
        if ln is None:
            done = True
        elif ln:
            print(ln, end="", flush=True)
            out.append(ln.rstrip("\n"))
        if done:
            try:
                return p.wait(timeout=60)
            except subprocess.TimeoutExpired:
                p.kill()
                p.wait(timeout=10)
                return 124
        if time.time() > deadline:
            p.kill()
            try:
                p.wait(timeout=10)
            except subprocess.TimeoutExpired:
                pass
            out.append(f"[hostrun] 逾時 {timeout}s → 砍掉")
            return 124


def classify(name: str, rc: int, lines: list) -> str:
    if name.startswith("④") and rc == 1:
        text = "\n".join(lines)
        if "Traceback" not in text and any(CHECKDB_SIG in ln and "整數型" in ln for ln in lines):
            return "YELLOW"                                    # 真的檢查完、看到整數型欄 = 要處理(不是程式壞)
        return "RED"
    return V207.LAMP_RC.get(rc, "RED")


def data_home(via: Path) -> Path | None:
    try:
        h, _why = V207.V198.V195.dataplane(via).P.resolve_home(None)
        return Path(h) if h else None
    except Exception:  # noqa: BLE001 — 解析不了 = 當沒有資料家
        return None


def plan_steps(args: list) -> list:
    steps = V207.plan_steps(args)[:3]
    via = V194._p("sm_via_root")()
    e232 = V207.tail_of(via / "functional modules" / "VDF" / "engine", "VDF_ENG232_TWIndexOfficial")
    h = data_home(via)
    db = h / "output_hub" / "tw_index" / "VDF_TWIndex_Daily.duckdb" if h else None
    if e232 and db and db.is_file():
        steps.append(("④ ENG232 check-db", [sys.executable, str(e232), "--check-db", str(db)], 300))
    else:
        steps.append(("④ ENG232 check-db", None, 0))
    return steps


def cmd_hostrun(args: list) -> int:
    via = V194._p("sm_via_root")()
    out_dir = V194._p("v73_out")(via)
    f = out_dir / "HOSTRUN_latest.txt"
    try:
        f.unlink()                                             # 舊摘要先刪:這一輪沒寫完就不會留著舊的
    except OSError:
        pass
    t0 = time.time()
    summary = [f"[hostrun] {TAG} · {time.strftime('%Y-%m-%d %H:%M:%S')} · 唯讀(tidy 只乾跑 · 不擷取 · 不搬)"]
    worst = "GREEN"
    for name, cmd, to in plan_steps(args):
        print(f"\n[hostrun] ==== {name} ====", flush=True)
        if cmd is None:
            msg = f"[hostrun] {name} · 略過(找不到資料家或庫 VDF_TWIndex_Daily.duckdb)"
            print(msg, flush=True)
            summary.append(msg)
            continue
        lines: list = []
        rc = stream(cmd, to, lines)
        lamp = classify(name, rc, lines)
        worst = V194.worst([worst, lamp]) if lamp != "GRAY" else worst
        summary.append(f"[hostrun] {name} · rc {rc} · {lamp}")
        summary += V207.summarize(lines)
    summary.append(f"[hostrun] 總燈 {worst} · {round(time.time() - t0, 1)}s")
    f.write_text("\n".join(summary) + "\n", encoding="utf-8")
    print("\n" + summary[-1] + f"\n[收據] {f.relative_to(via)}", flush=True)
    return {"GREEN": 0, "YELLOW": 2}.get(worst, 1)


class home_env:
    def __init__(self, value):
        self.value = value

    def __enter__(self):
        self.keep = os.environ.get("VIA_VDF_DB_HOME")
        os.environ["VIA_VDF_DB_HOME"] = str(self.value)
        return self

    def __exit__(self, *exc):
        if self.keep is None:
            os.environ.pop("VIA_VDF_DB_HOME", None)
        else:
            os.environ["VIA_VDF_DB_HOME"] = self.keep


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:240]) if note and not cond else ""), flush=True)

    print(f"[計] {TAG} 自測開始(本版 4 項 + 前版 {PRIOR_PATH.name} 自測 · 暫存資料家 · 零網路)", flush=True)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("T1 加速器真的載到 · 第 3 行標記 · 網路橋在", VIA_ACCEL is not None and src.splitlines()[2] == "# [VIA:ACCEL-BRIDGE:v0111]"
        and VIA_NET_TOOL_PATH is not None)
    lines: list = []
    t0 = time.time()
    rc = stream([sys.executable, "-c", "import time;time.sleep(5)"], 0.6, lines)
    dt = time.time() - t0
    lines2: list = []
    rc2 = stream([sys.executable, "-c", "print('a');print('b')"], 30, lines2)
    chk("T2 (Codex P2)子行程不印字也砍得掉:期限 0.6 秒 → 回 124、不等到它睡完 · 一般輸出照收",
        rc == 124 and dt < 4 and lines2 == ["a", "b"] and rc2 == 0, (rc, round(dt, 2), lines2))
    good = ["[VDF_ENG232_TWIndexOfficial v0108] check-db · x.duckdb · tw_index_daily · 數字欄 9 · 整數型 volume=INTEGER(寫入的小數可能已被四捨五入)"]
    crash = ["Traceback (most recent call last):", "RuntimeError: boom"]
    chk("T3 (Codex P2)check-db:真的看到整數型欄 → 黃;崩潰(Traceback)/ 沒有那一行的 rc 1 → 紅;其他步驟照 rc",
        classify("④ ENG232 check-db", 1, good) == "YELLOW" and classify("④ ENG232 check-db", 1, crash) == "RED"
        and classify("④ ENG232 check-db", 1, ["x"]) == "RED" and classify("② vv", 2, []) == "YELLOW", None)
    with tempfile.TemporaryDirectory(prefix="vdf_sm208_") as td:
        d = Path(td)
        with home_env(d / "missing"):
            s_missing = plan_steps([])
        (d / "home" / "output_hub" / "tw_index").mkdir(parents=True)
        (d / "home" / "output_hub" / "tw_index" / "VDF_TWIndex_Daily.duckdb").write_bytes(b"x")
        with home_env(d / "home"):
            s_present = plan_steps([])
    chk("T4 (Codex P2)資料家用暫存夾隔離:不存在 → check-db 略過;夾具裡有庫 → 排進 check-db(帶那本庫的路徑)",
        s_missing[3][1] is None and s_present[3][1] is not None and "--check-db" in s_present[3][1]
        and s_present[3][1][-1].endswith("VDF_TWIndex_Daily.duckdb"), (s_missing[3], s_present[3]))
    with tempfile.TemporaryDirectory(prefix="vdf_sm208b_") as td, home_env(Path(td) / "missing"):
        rc = PRIOR.selftest() if callable(getattr(PRIOR, "selftest", None)) else 1
    chk("T5 前版 v0207 自測照過(資料家指到不存在的路徑;它的 T3 只驗那條路)", rc == 0, rc)
    print(f"[計] {TAG} 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    if a[:1] == ["hostrun"]:
        return cmd_hostrun(a[1:])
    return PRIOR.main(a)


if __name__ == "__main__":
    raise SystemExit(main())
