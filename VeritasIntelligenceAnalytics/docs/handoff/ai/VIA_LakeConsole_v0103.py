#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_LakeConsole v0103 — 薄尾(v0102 · v0101 · v0100 一字不動):三系統平行收尾 + 燈號合理性稽核 + 九頭龍防護。

操作員 2026-11-16:「ONE PS TO HANDLE ALL · 記住要裝加速器 · 要三的獨立流程同步 · 在不影響電腦正常運作 ·
在不發生九頭龍風險前提下 · 改成自動完成 · 回來希望看到輸出驗證過跳出 HTML」「紅黃綠燈去檢查其合理性」。

closeout 改成:
  · 三條獨立流程同時跑(各系統自己的入口;流程內依序):
      VCGC:啟動(主控台自測)→ SSOT 覆蓋 → 交接檢查
      VDF :啟動(管理器自測)→ 自報 → 自檢
      VRN :啟動(管理器自測)→ 自報 → 自檢
  · 不影響電腦正常運作:子行程低優先權(Windows BELOW_NORMAL;其他系統 nice 10)· 同時最多 3 個子行程
  · 九頭龍防護:單一執行鎖(第二輪拒跑;持有者死了才接手)· 每個子行程開新行程群組,逾時整棵樹一起收掉 ·
                不留背景常駐 · 結束時確認自己生出的子行程都已收掉
  · 跑完 → VIA_LampAudit 尾版稽核每顆燈合不合理 → 寫 CLOSEOUT_3SYS_latest.{json,html}(含稽核表)→ 全部跑完才開頁
用法:python docs/handoff/ai/VIA_LakeConsole_v0103.py closeout [--no-open] [--quick] [--serial]
      其餘(serve · selftest …)照前版。
"""
from __future__ import annotations
# [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(graceful 零行為變更)
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
    VIA_ACCEL = None
# [VIA:ACCEL-BRIDGE:END]

import importlib.util
import json
import os
import re
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

VERSION = "v0103"
ENGINE = "VIA_LakeConsole " + VERSION
HERE = Path(__file__).resolve().parent


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


_PRIOR_FILE = max((p for p in HERE.glob("VIA_LakeConsole_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location("VIA_LakeConsole_prior_for_v0103", _PRIOR_FILE)
R = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = R
_spec.loader.exec_module(R)
P, VIA = R.P, R.VIA
LANES = {"VCGC": ["activate_vcgc", "ssot_domains", "vcgc_handoff"],
         "VDF": ["activate_vdf", "vdf_collect", "vdf_health"],
         "VRN": ["activate_vrn2", "vrn_collect", "vrn_health"]}
MAX_CHILDREN = 3
LOCK = "VIA_Reports/lake/closeout.lock"
OUT_KEEP = 60000                                   # 每步保留的輸出字數(稽核用;報告頁只印最後一行)
_LIVE: dict[int, subprocess.Popen] = {}
_LIVE_LOCK = threading.Lock()
_SLOTS = threading.BoundedSemaphore(MAX_CHILDREN)
P.CHAINS["closeout_3sys"] = ("三系統收尾(三條流程平行:VCGC · VDF · VRN 各自啟動 → 自報 · 自檢 → SSOT 覆蓋 → 交接檢查)",
                             [s for lane in LANES.values() for s in lane])


# ───────────────────────── 九頭龍防護 ─────────────────────────
def _alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        out = subprocess.run(["tasklist", "/FI", "PID eq %d" % pid, "/NH"], capture_output=True, text=True, errors="replace").stdout
        return str(pid) in out
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    try:                                            # Linux:已結束只差回收的殭屍(Z)不算活著
        with open("/proc/%d/stat" % pid, encoding="utf-8", errors="replace") as fh:
            return fh.read().rsplit(")", 1)[-1].split()[0] != "Z"
    except OSError:
        return True


def acquire_lock(via: Path) -> tuple:
    """單一執行鎖:有人正在跑 → 拒跑(回 False, 持有者);持有者已死 → 接手。"""
    p = via / LOCK
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():
        try:
            held = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            held = {}
        if _alive(int(held.get("pid") or 0)) and int(held.get("pid") or 0) != os.getpid():
            return False, held
    p.write_text(json.dumps({"pid": os.getpid(), "at": P._now(), "engine": ENGINE}), encoding="utf-8")
    return True, None


def release_lock(via: Path) -> None:
    p = via / LOCK
    try:
        held = json.loads(p.read_text(encoding="utf-8"))
        if int(held.get("pid") or 0) == os.getpid():
            p.unlink()
    except (OSError, ValueError) as exc:
        print("  [note] 收尾鎖沒能釋放:%s(下次啟動會判斷持有者是否還活著)" % type(exc).__name__)


def _popen_kwargs() -> dict:
    if os.name == "nt":
        return {"creationflags": getattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS", 0x4000) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x200)}
    return {"start_new_session": True, "preexec_fn": (lambda: os.nice(10))}


def _kill_tree(p: subprocess.Popen) -> None:
    """整棵行程樹一起收(不留孤兒 = 不長九頭龍)。"""
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)], capture_output=True)
        else:
            os.killpg(os.getpgid(p.pid), signal.SIGKILL)
    except (OSError, ProcessLookupError) as exc:
        print("  [note] 收子行程 %s:%s" % (p.pid, type(exc).__name__))


def run_one(via: Path, s: str) -> dict:
    zh, pat, args, receipt = P.ACTIONS[s]
    eng = P.tail_glob(via, pat)
    row = {"step": s, "zh": zh, "system": R.SYSTEM_OF.get(s, "VCGC"), "entry": eng.name if eng else None}
    if not eng:
        row.update(rc=127, lamp="RED", secs=0, tail="入口不在:" + pat, out="入口不在:" + pat)
        return row
    timeout = R.TIMEOUTS.get(s) or R.Q.TIMEOUTS.get(s, 900)
    with _SLOTS:
        t0 = time.time()
        p = subprocess.Popen([sys.executable, str(eng)] + list(args), cwd=str(via), stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL,
                             text=True, encoding="utf-8", errors="replace", env={**os.environ, "PYTHONIOENCODING": "utf-8", "VIA_FROM_VCGC": "YES"}, **_popen_kwargs())
        with _LIVE_LOCK:
            _LIVE[p.pid] = p
        try:
            so, se = p.communicate(timeout=timeout)
            rc = p.returncode
            txt = (so or "") + (("\n[stderr]\n" + se) if (se or "").strip() else "")
        except subprocess.TimeoutExpired:
            _kill_tree(p)
            so, se = p.communicate()
            rc, txt = 124, "逾時 %ds(整棵行程樹已收掉)\n" % timeout + (so or "")[-4000:]
        finally:
            with _LIVE_LOCK:
                _LIVE.pop(p.pid, None)
    lines = [l for l in txt.splitlines() if l.strip() and not l.startswith("<unknown>")]
    tally = [l.strip() for l in lines if re.search(r"\[計\]|\[(GREEN|YELLOW|RED|PASS|FAIL)\]|^\[SSOT 領域涵蓋\]", l.strip())]
    row.update(rc=rc, secs=round(time.time() - t0, 1), lamp=P.step_lamp(via, s, rc, txt, receipt),
               tail=(tally[-1] if tally else (lines[-1] if lines else ""))[:300], out=txt[-OUT_KEEP:])
    return row


def run_lanes(via: Path, lanes: dict, echo=print, serial: bool = False) -> list:
    results: dict[str, list] = {k: [] for k in lanes}

    def lane(name, steps):
        for s in steps:
            r = run_one(via, s)
            results[name].append(r)
            echo("  [%-6s] %-5s %-14s %6.1fs · %s" % (r["lamp"], name, s, r["secs"], r["tail"][:100]))
    if serial:
        for k, v in lanes.items():
            lane(k, v)
    else:
        ths = [threading.Thread(target=lane, args=(k, v), daemon=False) for k, v in lanes.items()]
        for t in ths:
            t.start()
        for t in ths:
            t.join()
    with _LIVE_LOCK:
        left = list(_LIVE.values())
    for p in left:                                  # 理論上不會有;有就收掉,不留背景
        _kill_tree(p)
    return [r for k in lanes for r in results[k]]


def _lamp_audit(via: Path):
    hits = sorted((via / "docs" / "handoff" / "ai").glob("VIA_LampAudit_v*.py"), key=_vnum)
    if not hits:
        return None
    spec = importlib.util.spec_from_file_location("via_lampaudit_for_console", hits[-1])
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m


def report_html(rep: dict) -> str:
    base = R.report_html(rep)
    a = rep.get("audit")
    if not a:
        return base
    zh = {"GREEN": "綠", "YELLOW": "黃", "RED": "紅", "GRAY": "灰"}
    rows = "".join('<tr><td>%s</td><td>%s</td><td><span class="p %s">%s</span></td><td><span class="p %s">%s</span></td><td>%s</td><td>%s</td><td class="tl">%s%s</td></tr>' % (
        R._esc(r["system"]), R._esc(r["step"]), r["actual"], zh.get(r["actual"], r["actual"]), r["expected"], zh.get(r["expected"], r["expected"]),
        "✓ 合理" if r["reasonable"] else "<b>✗ 不合理</b>", R._esc(r["owner_zh"]), R._esc(r["why"]),
        (" · %s %s → %s" % (r["mode"]["id"], R._esc(r["mode"]["situation"]), R._esc(r["mode"]["fix"]))) if r["mode"] and not r["reasonable"] else "") for r in a["rows"])
    side = '<div class="m">同意閘:%s · %s</div>' % (zh.get(a["side"]["consent"]["lamp"]), R._esc(a["side"]["consent"]["why"]))
    side += "".join('<div class="m">新鮮度:%s · %s</div>' % (f["id"], R._esc(f["why"])) for f in a["side"]["freshness"])
    own = " · ".join("%s:%s" % (R._esc(k), R._esc("、".join(v))) for k, v in a["non_green_by_owner"].items()) or "沒有"
    block = ('<div class="v %s"><b>燈號合理性稽核:%s</b><div>合理 %d / %d · 非綠燈由誰處理 —— %s</div></div>'
             '<div class="c t"><table><thead><tr><th>系統</th><th>步驟</th><th>實際燈</th><th>應有燈</th><th>判定</th><th>誰處理</th><th>依據</th></tr></thead><tbody>%s</tbody></table>%s</div>'
             % (a["lamp"], R._esc(a["verdict"]), a["counts"]["reasonable"], a["counts"]["steps"], own, rows, side))
    return base.replace('<div class="sys">', block + '<div class="sys">', 1).replace("三系統收尾報告</h1>", "三系統收尾報告(平行 · 含燈號稽核)</h1>", 1)


def closeout(via: Path = None, open_page: bool = True, quick: bool = False, serial: bool = False, echo=print) -> dict:
    via = via or VIA
    ok, held = acquire_lock(via)
    if not ok:
        echo("[GRAY] %s · 另一輪收尾正在跑(pid %s · %s 開始)→ 本輪不跑,避免互相蓋收據(九頭龍防護)" % (ENGINE, held.get("pid"), held.get("at")))
        return {"lamp": "GRAY", "verdict": "另一輪正在跑", "steps": [], "systems": {}, "locked_by": held}
    try:
        lanes = {k: [s for s in v if not (quick and s.startswith("activate_"))] for k, v in LANES.items()}
        echo("[%s] 三系統收尾 · %s · 三條流程%s · 子行程低優先權 · 最多 %d 個同時" % (ENGINE, "快速(略過啟動)" if quick else "含各自啟動", "依序" if serial else "平行", MAX_CHILDREN))
        t0 = time.time()
        res = run_lanes(via, lanes, echo, serial)
        systems = {}
        for r in res:
            s = systems.setdefault(r["system"], {"lamp": "GREEN", "notes": []})
            if R._WORST.get(r["lamp"], 2) > R._WORST.get(s["lamp"], 2):
                s["lamp"] = r["lamp"]
            s["notes"].append("%s %s" % (r["step"], r["lamp"]))
        worst = max((R._WORST.get(r["lamp"], 2) for r in res), default=3)
        lamp = ["GREEN", "YELLOW", "GRAY", "RED"][worst]
        verdict = {"GREEN": "三系統收尾:全部通過", "YELLOW": "三系統收尾:可用,有待處理的黃燈", "GRAY": "三系統收尾:有步驟沒有資料", "RED": "三系統收尾:有紅燈,未驗收"}[lamp]
        why = ("紅:" + "、".join(r["step"] for r in res if r["lamp"] == "RED")) if lamp == "RED" else (
            ("黃:" + "、".join(r["step"] for r in res if r["lamp"] == "YELLOW")) if lamp == "YELLOW" else "每一步都綠")
        rep = {"engine": ENGINE, "at": P._now(), "lamp": lamp, "verdict": verdict, "why": why, "secs": round(time.time() - t0, 1),
               "mode": "serial" if serial else "parallel", "steps": res, "systems": systems}
        la = _lamp_audit(via)
        if la:
            rep["audit"] = la.audit(rep, via=via)
            echo("[%s] 燈號合理性稽核 · %s · 合理 %d / %d" % (rep["audit"]["lamp"], rep["audit"]["verdict"], rep["audit"]["counts"]["reasonable"], rep["audit"]["counts"]["steps"]))
            for r in rep["audit"]["rows"]:
                if not r["reasonable"]:
                    echo("  ✗ %s 實際 %s 應有 %s · %s → %s" % (r["step"], r["actual"], r["expected"], r["mode"]["id"], r["mode"]["fix"]))
        (via / R.REPORT_JSON).parent.mkdir(parents=True, exist_ok=True)
        slim = dict(rep, steps=[{k: v for k, v in s.items() if k != "out"} for s in res])
        (via / R.REPORT_JSON).write_text(json.dumps(slim, ensure_ascii=False, indent=1), encoding="utf-8")
        (via / R.REPORT_HTML).write_text(report_html(rep), encoding="utf-8")
        echo("[%s] %s · %s · %.0f 秒 · %s" % (lamp, verdict, why, rep["secs"], R.REPORT_HTML))
        if open_page:
            rep["opened"] = R._open(via / R.REPORT_HTML, echo)
        return rep
    finally:
        release_lock(via)


def selftest() -> int:
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note and not cond else ""))
    print("[%s selftest]" % ENGINE)
    chk("① 前版 v0102 在 · 三條流程的每一步都在白名單", all(s in P.ACTIONS for v in LANES.values() for s in v) and _vnum(_PRIOR_FILE) == 102)
    with tempfile.TemporaryDirectory() as td:
        via = Path(td)
        a1, _ = acquire_lock(via)
        held = json.loads((via / LOCK).read_text(encoding="utf-8"))
        (via / LOCK).write_text(json.dumps(dict(held, pid=1 if os.name != "nt" else 4)), encoding="utf-8")   # 模擬「別人正在跑」(pid 1 / 4 必定活著)
        a2, h2 = acquire_lock(via)
        (via / LOCK).write_text(json.dumps(dict(held, pid=999999)), encoding="utf-8")                      # 持有者已死
        a3, _ = acquire_lock(via)
        release_lock(via)
        chk("② 單一執行鎖:自己拿得到 · 別人活著 → 拒跑 · 持有者已死 → 接手 · 結束釋放", a1 and not a2 and a3 and not (via / LOCK).exists(), (a1, a2, a3))
        # 逾時整棵樹收掉:子行程再生一個孫行程,逾時後兩個都不在
        script = via / "sleeper.py"
        script.write_text("import subprocess,sys,time\nc=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'])\nprint(c.pid,flush=True)\ntime.sleep(60)\n", encoding="utf-8")
        p = subprocess.Popen([sys.executable, str(script)], stdout=subprocess.PIPE, text=True, **_popen_kwargs())
        child = int(p.stdout.readline().strip() or 0)
        try:
            p.communicate(timeout=1)
        except subprocess.TimeoutExpired:
            _kill_tree(p)
            p.communicate()
        time.sleep(0.5)
        chk("③ 逾時收整棵樹:子行程與孫行程都不在(不留孤兒)", not _alive(p.pid) and not _alive(child), (p.pid, child))
        nice = os.getpriority(os.PRIO_PROCESS, 0) if hasattr(os, "getpriority") else None
        q = subprocess.Popen([sys.executable, "-c", "import os;print(os.getpriority(os.PRIO_PROCESS,0) if hasattr(os,'getpriority') else 'nt')"],
                             stdout=subprocess.PIPE, text=True, **_popen_kwargs())
        got = q.communicate()[0].strip()
        chk("④ 子行程低優先權(POSIX nice 比本行程大;Windows 用 BELOW_NORMAL 旗標)", got == "nt" or (nice is not None and int(got) > nice), (nice, got))
    # 平行:三條流程同時跑,總時間接近最慢一條而不是三條相加
    calls = []

    def fake(via, s):
        calls.append((s, time.time()))
        time.sleep(0.3)
        return {"step": s, "system": R.SYSTEM_OF.get(s, "VCGC"), "lamp": "GREEN", "rc": 0, "secs": 0.3, "tail": "[計] x PASS", "out": "[計] x PASS"}
    global run_one
    real = run_one
    run_one = fake
    try:
        t0 = time.time()
        res = run_lanes(VIA, {"A": ["activate_vcgc", "ssot_domains"], "B": ["activate_vdf", "vdf_collect"], "C": ["activate_vrn2", "vrn_collect"]}, lambda *_: None)
        dt = time.time() - t0
    finally:
        run_one = real
    chk("⑤ 三條流程平行:6 步 × 0.3 秒,總時間 < 1.2 秒(依序要 1.8 秒)· 流程內順序不變", dt < 1.2 and [r["step"] for r in res][:2] == ["activate_vcgc", "ssot_domains"], round(dt, 2))
    la = _lamp_audit(VIA)
    chk("⑥ 燈號稽核引擎在(VIA_LampAudit 尾版)", la is not None and hasattr(la, "audit"))
    rep = {"engine": ENGINE, "at": P._now(), "lamp": "YELLOW", "verdict": "v", "why": "w", "secs": 1.0, "steps": [
        {"step": "vdf_collect", "zh": "z", "system": "VDF", "lamp": "YELLOW", "rc": 2, "secs": 0.1, "tail": "t",
         "out": "collect · 七處 7/7 · 燈 {'upstream': 'GREEN', 'health': 'GREEN', 'conform': 'GREEN'} · 啟動 YELLOW"}],
        "systems": {"VDF": {"lamp": "YELLOW", "notes": ["vdf_collect YELLOW"]}}}
    rep["audit"] = la.audit(rep, env={}, via=Path("/nonexistent")) if la else None
    h = report_html(rep)
    chk("⑦ 報告頁含燈號稽核表(實際燈 · 應有燈 · 合理 · 誰處理)", "燈號合理性稽核" in h and "應有燈" in h and "操作員的手" in h)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 本檔:不設同意閘 · 不出網 · 子行程不走 shell", not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src)
        and not re.search(r"shell\s*=\s*True", src) and not re.search(r"^\s*(import|from)\s+(requests|urllib|socket)\b", src, re.M))
    n = sum(ok)
    print("[計] %s 自測 %d/%d %s" % (ENGINE, n, len(ok), "PASS" if n == len(ok) else "FAIL"))
    return 0 if n == len(ok) else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args or args[:1] == ["selftest"]:
        return selftest()
    if args[:1] == ["closeout"]:
        rep = closeout(VIA, open_page="--no-open" not in args, quick="--quick" in args, serial="--serial" in args)
        return {"GREEN": 0, "YELLOW": 0, "GRAY": 2}.get(rep["lamp"], 1)
    return R.main(args)


def __getattr__(name):
    return getattr(R, name)


if __name__ == "__main__":
    sys.exit(main())
