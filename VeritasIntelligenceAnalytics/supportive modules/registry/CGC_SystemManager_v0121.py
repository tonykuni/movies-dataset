#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""CGC_SystemManager v0121 — 薄尾(v0120 以前一字不動):schedule 動詞(APScheduler;VCGC 自己的排程冊)

操作員 2026-11-25:「最快排程器從 GitHub 加進來掛到 system manager · VCGC 也是一樣」→ 定案 APScheduler(經 VCGC 安裝閘 3.11.3)。
  schedule list                 VCGC 排程冊 VIA_VCGC_Schedule_SSOT 尾版的工作(可編輯:改冊出新版號)
  schedule run <job>            立刻跑一次(子行程;VCGC 核心境 python;工作自帶的 env 只在子行程)
  schedule start [--for 秒]     APScheduler 常駐:cron · 不疊跑 · 合併錯過 · 執行緒池 = 冊上 lanes;--for 只跑幾秒(測試)
只排 VCGC 自己的工作;VDF 的排程在 VDF_SystemManager schedule(系統獨立,不代管)。
每次執行只增寫 VIA_Reports/vcgc_schedule/RUN_LEDGER.jsonl。APScheduler 不在 = 黃(印安裝指令,不 pip)。其餘動詞全部照 v0120。
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0111] SuperAccel 加速器橋(從 TEMP 跑時改由工作目錄 / VIA_REPO 找倉;graceful) =====
try:
    import os as _sa_os
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_hit = None
    _sa_roots = [_sa_Path(__file__).resolve(), _sa_Path.cwd().resolve()]
    if _sa_os.environ.get("VIA_REPO"):
        _sa_roots.append(_sa_Path(_sa_os.environ["VIA_REPO"]).resolve())
    for _sa_r in _sa_roots:
        for _sa_q in (_sa_r, *_sa_r.parents):
            for _sa_c in (_sa_q / "supportive modules", _sa_q / "VeritasIntelligenceAnalytics" / "supportive modules"):
                if (_sa_c / "VIA_SuperAccel_Module.py").exists():
                    _sa_hit = _sa_c
                    break
            if _sa_hit:
                break
        if _sa_hit:
            break
    if _sa_hit and str(_sa_hit) not in _sa_sys.path:
        _sa_sys.path.insert(0, str(_sa_hit))
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響(自測會把它記成黃)
# ===== [VIA:ACCEL-BRIDGE:END] =====
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(操作員 2026-11-25「網路工具也要強制加入」;從 TEMP 跑時改由工作目錄 / VIA_REPO 找倉;graceful) =====
VIA_NET_TOOL_PATH = None
try:
    import os as _nb_os
    from pathlib import Path as _nb_Path
    _nb_roots = [_nb_Path(__file__).resolve(), _nb_Path.cwd().resolve()]
    if _nb_os.environ.get("VIA_REPO"):
        _nb_roots.append(_nb_Path(_nb_os.environ["VIA_REPO"]).resolve())
    for _nb_r in _nb_roots:
        for _nb_q in (_nb_r, *_nb_r.parents):
            for _nb_dir in (_nb_q / "supportive modules" / "network", _nb_q / "VeritasIntelligenceAnalytics" / "supportive modules" / "network"):
                _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py")) if _nb_dir.is_dir() else []
                if _nb_hits:
                    VIA_NET_TOOL_PATH = str(_nb_hits[-1])
                    break
            if VIA_NET_TOOL_PATH:
                break
        if VIA_NET_TOOL_PATH:
            break
except Exception:  # noqa: BLE001
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT:載入不出網,真的連線才看閘);缺席回 None(誠實)"""
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
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_SystemManager"
VERSION = "v0121"
TAG = f"{_STEM} {VERSION}"
VIA = HERE.parent.parent
LEDGER = VIA / "VIA_Reports" / "vcgc_schedule" / "RUN_LEDGER.jsonl"
BOOK_GLOB = "VIA_VCGC_Schedule_SSOT_v*.json"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(str(p)).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"cgc_prior_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def say(msg: str) -> None:
    print(f"[{TAG}] {msg}", flush=True)


def core_python() -> str:
    """VCGC 核心境 python(VIA_PY_CORE → via_core_312 · via_core · venv_core × 根);找不到退回本解譯器。"""
    ov = os.environ.get("VIA_PY_CORE", "")
    if ov and Path(ov).is_file():
        return ov
    home = Path.home()
    roots = [os.environ.get("VIA_ENV_ROOT", "")] + os.environ.get("VIA_ENV_ROOTS", "").split(";") + [
        str(home / "envs"), str(home / "miniconda3" / "envs"), str(home / "anaconda3" / "envs"), str(home / "venvs"), str(VIA / "Environments")]
    for r in roots:
        for n in ("via_core_312", "via_core", "venv_core"):
            for sub in (("Scripts", "python.exe"), ("python.exe",), ("bin", "python3"), ("bin", "python")):
                if r and Path(r, n, *sub).is_file():
                    return str(Path(r, n, *sub))
    return sys.executable


def book(reg: Path = HERE) -> dict:
    c = [p for p in reg.glob(BOOK_GLOB) if _vnum(p) >= 0]
    if not c:
        return {"jobs": [], "timezone": "Asia/Taipei", "lanes": 3, "_book": None}
    p = max(c, key=_vnum)
    d = json.loads(p.read_text(encoding="utf-8"))
    d["_book"] = p.name
    return d


def resolve(fam: str, reg: Path = HERE):
    c = [p for d in (reg, reg.parent.parent) for p in d.glob(fam + "_v*.py") if _vnum(p) >= 0]
    return max(c, key=_vnum) if c else None


def append_line(path: Path, line: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pre = ""
    if path.is_file() and path.stat().st_size:
        with path.open("rb") as f:
            f.seek(-1, 2)
            pre = "" if f.read(1) == b"\n" else "\n"
    with path.open("a", encoding="utf-8") as f:
        f.write(pre + line + "\n")


def run_job(job: dict, reg: Path = HERE, ledger: Path = LEDGER, py: str | None = None) -> int:
    cmd = list(job.get("cmd") or [])
    f = resolve(cmd[0], reg) if cmd else None
    t0 = time.time()
    if f is None:
        rc = 127
        say(f"工作 {job.get('id')}:找不到 {cmd[:1]} 的尾版")
    else:
        env = dict(os.environ, PYTHONUTF8="1", **{k: str(v) for k, v in (job.get("env") or {}).items()})   # 工作自帶 env 只在子行程
        rc = subprocess.run([py or core_python(), str(f), *cmd[1:]], cwd=str(reg.parent.parent.parent), env=env).returncode
    append_line(ledger, json.dumps({"utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "job": job.get("id"), "rc": rc,
                                    "secs": round(time.time() - t0, 2), "file": f.name if f else None}, ensure_ascii=False))
    return rc


def scheduler(cfg: dict, background: bool):
    from apscheduler.executors.pool import ThreadPoolExecutor as APThreads
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.triggers.cron import CronTrigger
    cls = BackgroundScheduler if background else BlockingScheduler
    tz = cfg.get("timezone", "Asia/Taipei")
    s = cls(timezone=tz, executors={"default": APThreads(max_workers=max(1, int(cfg.get("lanes", 3))))},
            job_defaults={"max_instances": 1, "coalesce": True, "misfire_grace_time": 3600})
    for j in cfg.get("jobs", []):
        s.add_job(run_job, CronTrigger.from_crontab(j["cron"], timezone=tz), args=[j], id=j["id"], name=j["id"], replace_existing=True)
    return s


def cmd_schedule(a: list) -> int:
    cfg = book()
    sub = a[1] if len(a) > 1 else "list"
    if sub == "list":
        say(f"排程(冊 {cfg['_book']} · 時區 {cfg.get('timezone')} · 道數 {cfg.get('lanes')}):{len(cfg.get('jobs', []))} 個工作")
        for j in cfg.get("jobs", []):
            f = resolve(j["cmd"][0]) if j.get("cmd") else None
            say(f"  {j['id']} · cron {j['cron']} · {' '.join(j.get('cmd', []))} · 尾版 {f.name if f else '找不到'}")
        return 0 if cfg.get("jobs") else 2
    if sub == "run":
        j = next((x for x in cfg.get("jobs", []) if len(a) > 2 and x["id"] == a[2]), None)
        if j is None:
            say(f"沒有這個工作:{a[2:3]}")
            return 1
        return run_job(j)
    if sub == "start":
        try:
            import apscheduler  # noqa: F401
        except ImportError:
            say("[YELLOW] APScheduler 不在:via-install --yes apscheduler(經 VCGC 安裝閘;不直接 pip)")
            return 2
        dur = float(a[a.index("--for") + 1]) if "--for" in a else None
        s = scheduler(cfg, background=dur is not None)
        say(f"排程啟動:{len(cfg.get('jobs', []))} 個工作 · 時區 {cfg.get('timezone')}" + (f" · 只跑 {dur:.0f} 秒" if dur else " · Ctrl+C 結束"))
        s.start()
        if dur is None:
            return 0
        for jb in s.get_jobs():
            say(f"  下次 {jb.id}:{jb.next_run_time}")
        time.sleep(dur)
        s.shutdown(wait=True)
        return 0
    say(f"schedule 子動詞:list · run <job> · start [--for 秒](收到 {sub})")
    return 1


def main() -> int:
    a = sys.argv[1:]
    if a[:1] == ["--selftest"]:
        return selftest()
    if a[:1] == ["schedule"]:
        return cmd_schedule(a)
    return PRIOR.main()


def selftest() -> int:
    ok, bad = [], []

    def chk(name, cond, note=""):
        (ok if cond else bad).append(name)
        print(("  [OK] " if cond else "  [NG] ") + name + (f" · {note}" if note else ""), flush=True)

    chk("加速器載入(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    chk("網路工具載入(_via_net() is not None · 載入不出網)", _via_net() is not None, str(VIA_NET_TOOL_PATH))
    chk("前版經 glob 載入(v0120)", PRIOR_PATH.name == _STEM + "_v0120.py")
    real = book()
    chk("VCGC 排程冊尾版可讀 · 工作都找得到尾版", real["_book"] is not None and real["jobs"] and all(resolve(j["cmd"][0]) for j in real["jobs"]),
        str([(j["id"], bool(resolve(j["cmd"][0]))) for j in real.get("jobs", [])]))
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "repo" / "VIA"
        reg = root / "supportive modules" / "registry"
        reg.mkdir(parents=True)
        (reg / "CGC_MDL999_Probe_v0101.py").write_text(
            "import os, sys, pathlib\npathlib.Path(sys.argv[1]).write_text(os.environ.get('VIA_FROM_VCGC', '') + ' ' + ' '.join(sys.argv[2:]))\n", encoding="utf-8")
        (reg / "VIA_VCGC_Schedule_SSOT_v0100.json").write_text(json.dumps({"timezone": "Asia/Taipei", "lanes": 2, "jobs": [
            {"id": "probe", "cron": "*/1 * * * *", "cmd": ["CGC_MDL999_Probe", str(Path(td) / "hit.txt"), "--y"], "env": {"VIA_FROM_VCGC": "YES"}}]}), encoding="utf-8")
        cfg = book(reg)
        before = os.environ.get("VIA_FROM_VCGC")
        rc = run_job(cfg["jobs"][0], reg, Path(td) / "L.jsonl", py=sys.executable)
        chk("run:立刻跑一次 · 工作 env 只在子行程 · 參數照傳 · 寫運作帳", rc == 0 and (Path(td) / "hit.txt").read_text() == "YES --y"
            and os.environ.get("VIA_FROM_VCGC") == before and (Path(td) / "L.jsonl").is_file())
        try:
            s = scheduler(cfg, background=True)
            s.start(paused=True)
            jb = s.get_jobs()
            chk("APScheduler:cron · 不疊跑 · 合併錯過", len(jb) == 1 and jb[0].max_instances == 1 and jb[0].coalesce is True)
            s.shutdown(wait=False)
        except ImportError:
            chk("APScheduler 可用(缺 = 黃)", False, "via-install --yes apscheduler")
    print(f"{TAG} selftest {len(ok)}/{len(ok) + len(bad)}" + (" · 不過:" + " · ".join(bad) if bad else ""), flush=True)
    return 0 if not bad else 1


if __name__ == "__main__":
    raise SystemExit(main())
