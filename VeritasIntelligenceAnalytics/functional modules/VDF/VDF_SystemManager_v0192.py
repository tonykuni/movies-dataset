#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VDF SystemManager v0192 — 薄尾(v0191 以前一字不動):schedule 動詞(APScheduler)· three 動詞(轉 VDF_ENG242 三期蒸餾)

操作員 2026-11-25:「啟動器也是用 PY 撰寫加入加速器導入 · 最快排程器從 GitHub 加進來掛到 system manager · VCGC 也是一樣」→ 定案 APScheduler
(GitHub agronholm/apscheduler;經 VCGC 安裝閘 CGC_MDL056 裝,釘版 3.11.3,三鏡像無新增衝突)。
  schedule list                      排程工作(VDF 參數正本 ParamControl_SSOT 尾版的 schedule.jobs · schedule.timezone;可編輯可管理)
  schedule run <job>                 立刻跑一次那個工作(子行程;VDF 家族境 python;帶 VDF 入口標記)
  schedule start [--for 秒]          APScheduler 常駐:cron 觸發 · 同一工作不疊跑(max_instances 1)· 錯過合併成一次(coalesce)·
                                     執行緒池 = three.lanes 道;--for 只跑幾秒(測試用)
  three <動詞…>                      轉 VDF_ENG242_ThreePeriodDistill 尾版(ready · inventory · plan · run · distill · reconcile · names · bench · params-init)
每次執行只增寫 VIA_Reports/vdf_schedule/RUN_LEDGER.jsonl(工作 · rc · 秒 · UTC)。APScheduler 不在 = 黃(印安裝指令,不 pip)。
其餘動詞全部照 v0191。不 import 他系統(VCGC 的排程在 CGC_SystemManager 自己那一支)。
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
STEM = "VDF_SystemManager"
VERSION = "v0192"
TAG = f"VDF SystemManager {VERSION}"
VIA = HERE.parent.parent
LEDGER = VIA / "VIA_Reports" / "vdf_schedule" / "RUN_LEDGER.jsonl"
ENTRY_ENV = {"VIA_CENTRAL_ENTRY": "1", "VIA_ENTRY_CONTROL": f"{STEM}_{VERSION}"}


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(str(p)).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def say(msg: str) -> None:
    print(f"[{TAG}] {msg}", flush=True)


def vdf_python() -> str:
    """VDF 家族境 python(照 Get-VIAEnvPython:VIA_PY_VDF → via_vdf_312 · via_vdf · via_vdf_313 × 根);找不到退回本解譯器。"""
    ov = os.environ.get("VIA_PY_VDF", "")
    if ov and Path(ov).is_file():
        return ov
    home = Path.home()
    roots = [os.environ.get("VIA_ENV_ROOT", "")] + os.environ.get("VIA_ENV_ROOTS", "").split(";") + [
        str(home / "envs"), str(home / "miniconda3" / "envs"), str(home / "Miniconda3" / "envs"), str(home / "anaconda3" / "envs"), str(VIA / "Environments")]
    for r in roots:
        for n in ("via_vdf_312", "via_vdf", "via_vdf_313"):
            for sub in (("Scripts", "python.exe"), ("python.exe",), ("bin", "python3"), ("bin", "python")):
                if r and Path(r, n, *sub).is_file():
                    return str(Path(r, n, *sub))
    return sys.executable


def jobs(vdf: Path = HERE) -> dict:
    mts = [p for p in vdf.glob("VDF_ParamControl_SSOT_v*.json") if _vnum(p) >= 0]
    out = {"jobs": [], "timezone": "Asia/Taipei", "master": None, "lanes": 3}
    if not mts:
        return out
    mt = max(mts, key=_vnum)
    out["master"] = mt.name
    for e in json.loads(mt.read_text(encoding="utf-8")).get("params", []):
        if e.get("path") == "schedule.jobs":
            out["jobs"] = list(e.get("value") or [])
        elif e.get("path") == "schedule.timezone":
            out["timezone"] = e.get("value") or out["timezone"]
        elif e.get("path") == "three.lanes":
            out["lanes"] = int(e.get("value") or 3)
    return out


def resolve(fam: str, vdf: Path = HERE):
    c = [p for d in (vdf, vdf / "engine") for p in d.glob(fam + "_v*.py") if _vnum(p) >= 0]
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


def run_job(job: dict, vdf: Path = HERE, ledger: Path = LEDGER, py: str | None = None) -> int:
    cmd = list(job.get("cmd") or [])
    f = resolve(cmd[0], vdf) if cmd else None
    t0 = time.time()
    if f is None:
        rc = 127
        say(f"工作 {job.get('id')}:找不到 {cmd[:1]} 的尾版")
    else:
        env = dict(os.environ, PYTHONUTF8="1", **{k: os.environ.get(k, v) for k, v in ENTRY_ENV.items()})
        rc = subprocess.run([py or vdf_python(), str(f), *cmd[1:]], cwd=str(f.parent), env=env).returncode
    append_line(ledger, json.dumps({"utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "job": job.get("id"), "rc": rc,
                                    "secs": round(time.time() - t0, 2), "file": f.name if f else None}, ensure_ascii=False))
    return rc


def scheduler(cfg: dict, background: bool):
    from apscheduler.executors.pool import ThreadPoolExecutor as APThreads
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.triggers.cron import CronTrigger
    cls = BackgroundScheduler if background else BlockingScheduler
    s = cls(timezone=cfg["timezone"], executors={"default": APThreads(max_workers=max(1, cfg["lanes"]))},
            job_defaults={"max_instances": 1, "coalesce": True, "misfire_grace_time": 3600})
    for j in cfg["jobs"]:
        s.add_job(run_job, CronTrigger.from_crontab(j["cron"], timezone=cfg["timezone"]), args=[j], id=j["id"], name=j["id"], replace_existing=True)
    return s


def cmd_schedule(a: list) -> int:
    cfg = jobs()
    sub = a[1] if len(a) > 1 else "list"
    if sub == "list":
        say(f"排程(正本 {cfg['master']} · 時區 {cfg['timezone']} · 道數 {cfg['lanes']}):{len(cfg['jobs'])} 個工作")
        for j in cfg["jobs"]:
            f = resolve(j["cmd"][0]) if j.get("cmd") else None
            say(f"  {j['id']} · cron {j['cron']} · {' '.join(j.get('cmd', []))} · 尾版 {f.name if f else '找不到'}")
        if not cfg["jobs"]:
            say("  沒有工作:先 three params-init --apply(把 schedule.jobs 登進 VDF 正本)")
        return 0 if cfg["jobs"] else 2
    if sub == "run":
        j = next((x for x in cfg["jobs"] if len(a) > 2 and x["id"] == a[2]), None)
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
        say(f"排程啟動:{len(cfg['jobs'])} 個工作 · 時區 {cfg['timezone']}" + (f" · 只跑 {dur:.0f} 秒" if dur else " · Ctrl+C 結束"))
        if dur is None:
            s.start()
            return 0
        s.start()
        for jb in s.get_jobs():
            say(f"  下次 {jb.id}:{jb.next_run_time}")
        time.sleep(dur)
        s.shutdown(wait=True)
        return 0
    say(f"schedule 子動詞:list · run <job> · start [--for 秒](收到 {sub})")
    return 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["--selftest"]:
        return selftest()
    if a[:1] == ["schedule"]:
        return cmd_schedule(a)
    if a[:1] == ["three"]:
        f = resolve("VDF_ENG242_ThreePeriodDistill", HERE)
        if f is None:
            say("找不到 VDF_ENG242_ThreePeriodDistill 尾版")
            return 1
        env = dict(os.environ, PYTHONUTF8="1", **{k: os.environ.get(k, v) for k, v in ENTRY_ENV.items()})
        return subprocess.run([vdf_python(), str(f), *a[1:]], cwd=str(f.parent), env=env).returncode
    return PRIOR.main(a)


def selftest() -> int:
    ok, bad = [], []

    def chk(name, cond, note=""):
        (ok if cond else bad).append(name)
        print(("  [OK] " if cond else "  [NG] ") + name + (f" · {note}" if note else ""), flush=True)

    chk("加速器載入(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    chk("網路工具載入(_via_net() is not None · 載入不出網)", _via_net() is not None, str(VIA_NET_TOOL_PATH))
    chk("前版經 glob 載入(v0191)", PRIOR_PATH.name == STEM + "_v0191.py")
    with tempfile.TemporaryDirectory() as td:
        v = Path(td)
        (v / "engine").mkdir()
        (v / "engine" / "VDF_ENG999_Probe_v0101.py").write_text(
            "import os, sys, pathlib\npathlib.Path(sys.argv[1]).write_text(os.environ.get('VIA_ENTRY_CONTROL', '') + ' ' + ' '.join(sys.argv[2:]))\n", encoding="utf-8")
        (v / "VDF_ParamControl_SSOT_v0105.json").write_text(json.dumps({"params": [
            {"path": "schedule.timezone", "value": "Asia/Taipei"}, {"path": "three.lanes", "value": 3},
            {"path": "schedule.jobs", "value": [{"id": "probe", "cron": "*/1 * * * *", "cmd": ["VDF_ENG999_Probe", str(v / "hit.txt"), "--x"]}]}]}), encoding="utf-8")
        cfg = jobs(v)
        chk("排程工作取自 VDF 正本(可編輯可管理)", cfg["master"] == "VDF_ParamControl_SSOT_v0105.json" and cfg["jobs"][0]["id"] == "probe" and cfg["lanes"] == 3)
        rc = run_job(cfg["jobs"][0], v, v / "LEDGER.jsonl", py=sys.executable)
        chk("run:工作立刻跑一次 · 帶 VDF 入口標記 · 參數照傳 · 寫運作帳", rc == 0 and (v / "hit.txt").read_text() == f"{STEM}_{VERSION} --x"
            and json.loads((v / "LEDGER.jsonl").read_text(encoding="utf-8").splitlines()[-1])["job"] == "probe")
        chk("找不到尾版 = rc 127(照實記)", run_job({"id": "x", "cmd": ["VDF_NOPE"]}, v, v / "LEDGER.jsonl") == 127)
        try:
            s = scheduler(cfg, background=True)
            s.start(paused=True)
            jb = s.get_jobs()
            chk("APScheduler:cron 觸發 · 不疊跑 · 合併錯過 · 執行緒池", len(jb) == 1 and jb[0].max_instances == 1 and jb[0].coalesce is True
                and str(jb[0].trigger.timezone) == "Asia/Taipei")
            s.shutdown(wait=False)
        except ImportError:
            chk("APScheduler 可用(缺 = 黃)", False, "via-install --yes apscheduler")
    print(f"{TAG} selftest {len(ok)}/{len(ok) + len(bad)}" + (" · 不過:" + " · ".join(bad) if bad else ""), flush=True)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
