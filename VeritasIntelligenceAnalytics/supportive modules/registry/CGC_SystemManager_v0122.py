#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""CGC_SystemManager v0122 — 薄尾(v0121 以前一字不動):launch 動詞 = VCGC 一鍵啟用(架構規劃 §3 B 群 launch [--plan])

操作員 2026-11-28 01:09:「activate the system with a py code with accelerating module, and activate py with a ps code」。
launch 只組 VCGC 既有動作,不新寫任何檢查(工具優先 · VCGC-REQ265):
  ⓪ 降壓:gc 一次、量可用記憶體;道數 = 加速器 thread_budget 夾在 3~6(低於 VIA_LAUNCH_MIN_GB 預設 4 GB → 3 道)
  ① 閘(序跑):主控台 token —— 紅就停(CLAUDE.md 第一步:token 紅 VCGC 不往下)
  ② 同時跑(3~6 道 · 每 ≤30 秒一行心跳 · 逾時只殺自己起的子行程樹):
     test --quick(含 functions · handoff check · status · sync-check · mcp · monitor · synchronizer)
     · SDD check · 編號 audit · 本管理器 toolbox check · 省 Token delta · 重工守門 check
  ③ 收尾:主控台 overview --no-open 產 VCGC 頁(既有 U/I,視覺鎖定不動)→ 打開它
  收據 VIA_Reports/vcgc/launch/LAUNCH_latest.json(§3 欄位:系統 · 動詞 · 版本 · UTC · rc · 燈 · 三數 · 證據)
  貼回包 LAUNCH_latest.txt(≤300 行,只列黃紅,最後一行 NEXT:)· 帳 LAUNCH_LEDGER.jsonl(只增)
  rc:0 綠 · 1 紅 · 2 黃(含灰 = 找不到尾版)。容器跑的一律標「容器」;本動詞不寫收尾成功,收尾燈只看 handoff 的 closeout_lamp。
  launch --plan     只印計畫(解析到的尾版 · 指令 · 道數),不起任何子行程、不寫檔
  launch --full     test 換整輪(收尾前用)
  launch --lanes N  指定道數(仍夾在 3~6)· --no-open 不開頁 · --plain 不上色 · --timeout 秒(每道上限,預設 3600)
其餘動詞全部照 v0121。只動 VCGC 自己的檔與 VIA_Reports/vcgc;不碰 VDF / VRN。
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

import gc
import importlib.util
import json
import os
import re
import signal
import subprocess
import sys
import tempfile
import time
import webbrowser
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_SystemManager"
VERSION = "v0122"
TAG = f"{_STEM} {VERSION}"
VIA = HERE.parent.parent
OUT = VIA / "VIA_Reports" / "vcgc" / "launch"
LAMP = {0: "GREEN", 1: "RED", 2: "YELLOW", 3: "GRAY", 4: "YELLOW"}
RANK = {"RED": 3, "YELLOW": 2, "GRAY": 1, "GREEN": 0}
_NOISE = ("[監控]", "[第一步", "[政策]", "[位階]", "[加速]", "[分群]", "[不衝突]", "[靜態]", "[回覆]", "[衝突]", "[還原]", "[環境計畫]")


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(str(p)).stem)
    return int(m.group(1)) if m else -1


_BELOW = [p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)]
if not _BELOW:   # 放錯倉(該倉沒有前版):照實停,不丟例外(2026-11-28 主機實錄:落到另一份副本)
    print(f"[RED] {HERE} 沒有 {_STEM} 前版;這份不是主工作倉。把本檔移到有 {_STEM}_v0121.py 的 registry 夾再跑。", flush=True)
    raise SystemExit(3)
PRIOR_PATH = max(_BELOW, key=_vnum)
_spec = importlib.util.spec_from_file_location(f"cgc_prior_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


_COLOR = {"GREEN": "\033[92m", "YELLOW": "\033[93m", "RED": "\033[91m", "GRAY": "\033[90m", "END": "\033[0m"}
_PLAIN = [not sys.stdout.isatty()]


def say(msg: str, lamp: str | None = None) -> None:
    line = f"[{TAG}] {msg}"
    if lamp and not _PLAIN[0]:
        line = _COLOR.get(lamp, "") + line + _COLOR["END"]
    print(line, flush=True)


def _tail(glob_dir: Path, pattern: str):
    c = [p for p in glob_dir.glob(pattern) if _vnum(p) >= 0]
    return max(c, key=_vnum) if c else None


def _token_tool(via: Path):
    """鎖冊 token 那一支(不自己取尾版;CLAUDE.md「工具換版只經 tools activate」)。"""
    lock = via / "supportive modules" / "registry" / "VIA_ToolVersion_Lock_v0100.json"
    try:
        rel = json.loads(lock.read_text(encoding="utf-8"))["token"]["path"]
    except (OSError, ValueError, KeyError, TypeError):
        return None
    for base in (via.parent, via):
        p = base / rel
        if p.is_file():
            return p
    return None


def plan(via: Path = VIA, reg: Path = HERE, full: bool = False, self_file: Path | None = None, timeout: int = 3600) -> dict:
    """解析每一步的尾版與指令。找不到的步標 file=None(跑時記灰 rc 3,不冒充)。"""
    con = _tail(reg, "CGC_MDL149_VeritasCentralGovernanceConsole_v*.py")
    me = self_file or Path(__file__).resolve()
    guard = _tail(via / "docs" / "handoff" / "ai", "VIA_ReworkGuard_v*.py")
    tok = _token_tool(via)

    def step(name, f, argv, why, cap=timeout):
        return {"name": name, "file": str(f) if f else None, "argv": list(argv), "why": why, "timeout": int(cap)}

    return {
        "gate": step("token", con, ["token"], "第一步:省 Token 卡;紅就停", 600),
        "lanes": [
            step("test", con, ["test"] if full else ["test", "--quick"], "VCGC 全功能串測(含 functions · handoff · status · sync-check · monitor)"),
            step("sdd", con, ["run", "CGC_MDL245_SDDValidator", "check"], "需求 × 工作流 × 編號交叉檢"),
            step("number", con, ["run", "CGC_MDL237_NumberingSystem", "audit"], "編號只增稽核:遺失 · 改身分 · 重號 = 0"),
            step("toolbox", me, ["toolbox", "check"], "四群工具七件事 + 獨立性"),
            step("delta", tok, ["delta"], "全景只看新增 / 已解(TEMP 快取)"),
            step("rework", guard, ["check"], "重工守門(已鎖 · 版號 · 金鑰)"),
        ],
        "post": step("overview", con, ["overview", "--no-open"], "VCGC 頁:卡片 + 矩陣(既有 U/I)", 900),
    }


def lane_count(requested: int | None = None, min_gb: float | None = None) -> tuple:
    """道數:加速器 thread_budget 夾在 3~6;記憶體低於門檻 → 3。回 (道數, 依據)。"""
    gc.collect()
    free = _avail_gb()
    mg = float(min_gb if min_gb is not None else os.environ.get("VIA_LAUNCH_MIN_GB", "4") or 4)
    tb = None
    try:
        cel = VIA_ACCEL.celeritas() if VIA_ACCEL is not None else None
        tb = int(cel.thread_budget()) if cel is not None and hasattr(cel, "thread_budget") else None
    except Exception:  # noqa: BLE001
        tb = None
    if requested:
        n, why = int(requested), "指定"
    elif free is not None and free < mg:
        n, why = 3, f"可用記憶體 {free:.1f} GB < {mg:g} GB"
    else:
        n, why = (tb if tb else (os.cpu_count() or 3)), ("加速器 thread_budget" if tb else "cpu_count(加速器缺)")
    return max(3, min(6, n)), f"{why} · 可用 {('%.1f GB' % free) if free is not None else '量不到'} · 預算 {tb}"


def _avail_gb():
    try:
        if os.name == "nt":
            import ctypes

            class _MS(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong), ("ullTotalPhys", ctypes.c_ulonglong),
                            ("ullAvailPhys", ctypes.c_ulonglong), ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong), ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
            ms = _MS()
            ms.dwLength = ctypes.sizeof(_MS)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(ms))
            return ms.ullAvailPhys / 2 ** 30
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) / 2 ** 20
    except Exception:  # noqa: BLE001
        return None
    return None


def _kill_tree(proc) -> None:
    """只殺自己起的子行程樹(不碰別人的 PID)。"""
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True, check=False)
        else:
            os.killpg(proc.pid, signal.SIGKILL)
    except (OSError, ProcessLookupError):
        try:
            proc.kill()
        except OSError:
            return


def _last(path: Path, n: int = 400) -> list:
    try:
        return path.read_text(encoding="utf-8", errors="replace").splitlines()[-n:]
    except OSError:
        return []


_SUMMARY = re.compile(r"^\[[^\]]+\]\s+(GREEN|YELLOW|RED|GRAY|NODATA)\s+·")


def verdict(lines: list, rc: int | None = None) -> str:
    """總結行:先找「[名稱] 燈 · …」那種總表行;rc 不是 0 時退而找第一行黃紅;再退回最後一行帶燈字的行。"""
    for ln in reversed(lines):
        if _SUMMARY.match(ln.strip()):
            return ln.strip()[:220]
    if rc not in (0, None):
        for ln in lines:
            if re.match(r"^\s*\[(RED|YELLOW|紅|黃)", ln) and not ln.strip().startswith(_NOISE):
                return ln.strip()[:220]
    for ln in reversed(lines):
        s = ln.strip()
        if s.startswith("NEXT:"):
            continue
        if s.startswith("[") and not s.startswith(_NOISE) and re.search(r"GREEN|YELLOW|RED|綠|黃|紅", s):
            return s[:220]
    for ln in reversed(lines):
        if ln.strip():
            return ln.strip()[:220]
    return "(沒有輸出)"


def run_steps(steps: list, lanes: int, py: str, cwd: Path, logdir: Path, every: int = 20, log=say, popen=subprocess.Popen) -> list:
    """同時最多 lanes 道;每 ≤every 秒一行心跳;逾時殺自己的子行程樹。回每步結果(照原順序)。"""
    env = dict(os.environ, VIA_FROM_VCGC="YES", PYTHONUTF8="1", VIA_NO_OPEN="1", PYTHONWARNINGS="ignore")
    pending, running, done = list(enumerate(steps)), {}, {}
    t0, last_hb = time.time(), time.time()
    while pending or running:
        while pending and len(running) < lanes:
            i, st = pending.pop(0)
            lp = logdir / f"{i:02d}_{st['name']}.log"
            if not st.get("file") or not Path(st["file"]).is_file():
                done[i] = dict(st, rc=3, lamp="GRAY", secs=0.0, log=str(lp), verdict="找不到尾版(灰 · 不冒充)")
                log(f"  [GRAY ] {st['name']:<8} 找不到尾版", "GRAY")
                continue
            fh = lp.open("w", encoding="utf-8")
            kw = {"creationflags": getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)} if os.name == "nt" else {"start_new_session": True}
            proc = popen([py, "-X", "utf8", st["file"], *st["argv"]], cwd=str(cwd), env=env, stdout=fh, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, **kw)
            running[i] = (st, proc, fh, time.time(), lp)
            log(f"  [起 ] {st['name']:<8} {Path(st['file']).name} {' '.join(st['argv'])}")
        time.sleep(0.2)
        for i, (st, proc, fh, ts, lp) in list(running.items()):
            rc = proc.poll()
            over = rc is None and time.time() - ts > st["timeout"]
            if over:
                _kill_tree(proc)
                proc.wait()
                rc = 124
            if rc is None:
                continue
            fh.close()
            lamp = "RED" if rc == 124 else LAMP.get(rc, "RED")
            v = ("逾時 %ds 已停(只停自己的子行程)" % st["timeout"]) if over else verdict(_last(lp), rc)
            done[i] = dict(st, rc=rc, lamp=lamp, secs=round(time.time() - ts, 1), log=str(lp), verdict=v)
            del running[i]
            log(f"  [{lamp:<5}] {st['name']:<8} rc {rc} · {done[i]['secs']}s · {v[:120]}", lamp)
        if running and time.time() - last_hb >= every:
            last_hb = time.time()
            pct = int(100 * len(done) / max(1, len(steps)))
            bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
            parts = [f"{st['name']} {int(time.time() - ts)}s ▸ {(_last(lp, 1) or [''])[-1].strip()[:40]}" for st, _p, _f, ts, lp in running.values()]
            log(f"  [心跳] {bar} {pct}% · {int(time.time() - t0)}s · 跑著 {' │ '.join(parts)}")
    return [done[i] for i in sorted(done)]


def pastepack(res: dict, cap: int = 300) -> list:
    """給 AI 的貼回包:只列黃紅,最後一行 NEXT:。"""
    out = [f"[VCGC launch] {res['lamp']} · {res['host']} · 應 {res['counts']['should']} · 已 {res['counts']['ran']} · 略過 {len(res['counts']['skipped'])}"
           + (f"({', '.join(res['counts']['skipped'])})" if res["counts"]["skipped"] else "") + f" · 道數 {res['lanes_used']} · {res['secs']}s"]
    steps = [res.get("gate_result")] + res["results"] + [res.get("post_result")]
    for s in [x for x in steps if x]:
        out.append(f"  [{s['lamp']:<6}] {s['name']:<8} rc {s['rc']} · {s['verdict'][:160]}")
    for s in [x for x in steps if x and x["lamp"] in ("RED", "YELLOW")]:
        hits = [ln.strip() for ln in _last(Path(s["log"]), 2000)
                if re.match(r"^\s*\[(RED|YELLOW|紅|黃)", ln) and not ln.strip().startswith(_NOISE)]
        if hits:
            out.append(f"  ── {s['name']} 黃紅 {len(hits)} 行(列前 12;全文 {s['log']})")
            out.extend("    " + h[:200] for h in hits[:12])
    out = out[:cap - 1]
    out.append("NEXT: " + res["next"])
    return out


def _next(res: dict) -> str:
    steps = [res.get("gate_result")] + res["results"]
    for want in ("RED", "YELLOW", "GRAY"):
        for s in [x for x in steps if x and x["lamp"] == want]:
            f = Path(s["file"]).name if s.get("file") else "?"
            return f"python \"{f}\" {' '.join(s['argv'])}(看 {s['log']})"
    return "via-vcgc handoff daily(收工);收尾燈只看 handoff 的 closeout_lamp"


def launch(argv: list, via: Path = VIA, reg: Path = HERE, self_file: Path | None = None, py: str | None = None,
           out: Path = OUT, opener=webbrowser.open, log=say, every: int | None = None) -> int:
    a = list(argv)
    if "--plain" in a:
        _PLAIN[0] = True
    full = "--full" in a
    req = int(a[a.index("--lanes") + 1]) if "--lanes" in a and a.index("--lanes") + 1 < len(a) else None
    cap = int(a[a.index("--timeout") + 1]) if "--timeout" in a and a.index("--timeout") + 1 < len(a) else 3600
    every = every or max(5, min(30, int(os.environ.get("VIA_HEARTBEAT_SEC", "20") or 20)))
    host = "主機" if os.name == "nt" else "容器"
    p = plan(via, reg, full, self_file, cap)
    lanes, why = lane_count(req)
    py = py or PRIOR.core_python()
    log(f"VCGC 啟用 · {host} · 道數 {lanes}({why})· 加速器 {'載到' if VIA_ACCEL is not None else '沒載到(黃)'} · python {py}")
    if "--plan" in a:
        for s in [p["gate"], *p["lanes"], p["post"]]:
            log(f"  [計畫] {s['name']:<8} {Path(s['file']).name if s['file'] else '找不到(灰)'} {' '.join(s['argv'])} · {s['why']}")
        log("NEXT: 拿掉 --plan 就照這張跑")
        return 0
    t0 = time.time()
    logdir = Path(tempfile.mkdtemp(prefix="VIA_launch_"))
    repo = via.parent
    gate = run_steps([p["gate"]], 1, py, repo, logdir, every, log)[0]
    results, post = [], None
    if gate["lamp"] == "RED" or gate["rc"] not in (0, 2):
        log("第一步 token 不綠:VCGC 停在這裡(CLAUDE.md:token 紅不讀政策、不開子系統)", "RED")
    else:
        results = run_steps(p["lanes"], lanes, py, repo, logdir, every, log)
        post = run_steps([p["post"]], 1, py, repo, logdir, every, log)[0]
    allr = [gate, *results] + ([post] if post else [])
    worst = max((r["lamp"] for r in allr), key=lambda x: RANK[x])
    lamp = {"RED": "RED", "GREEN": "GREEN"}.get(worst, "YELLOW")
    skipped = [s["name"] for s in [p["gate"], *p["lanes"], p["post"]] if s["name"] not in {r["name"] for r in allr}]
    page = via / "VIA_Reports" / "vcgc" / "VCGC_Overview_latest.html"
    res = {"system": "VCGC", "verb": "launch", "version": VERSION, "utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "host": host, "lanes_used": lanes, "lanes_why": why, "accel_loaded": VIA_ACCEL is not None, "secs": round(time.time() - t0, 1),
           "counts": {"should": 2 + len(p["lanes"]), "ran": sum(1 for r in allr if r["rc"] != 3), "skipped": skipped},
           "gate_result": gate, "results": results, "post_result": post, "lamp": lamp,
           "page": str(page) if page.is_file() and post and post["rc"] == 0 else None, "logs": str(logdir),
           "note": "launch 只啟用與彙總;收尾燈只看 handoff 的 closeout_lamp(主機實跑 + 輸出驗證 + U/I)"}
    res["rc"] = {"GREEN": 0, "RED": 1}.get(lamp, 2)
    res["next"] = _next(res)
    pack = pastepack(res)
    out.mkdir(parents=True, exist_ok=True)
    (out / "LAUNCH_latest.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "LAUNCH_latest.txt").write_text("\n".join(pack) + "\n", encoding="utf-8")
    PRIOR.append_line(out / "LAUNCH_LEDGER.jsonl", json.dumps({k: res[k] for k in ("utc", "host", "lamp", "rc", "secs", "lanes_used", "counts")}, ensure_ascii=False))
    print("", flush=True)
    for ln in pack:
        lp = "RED" if "[RED" in ln else ("YELLOW" if ("[YELLOW" in ln or ln.startswith("NEXT:") or ln.startswith("[VCGC launch]")) else None)
        if lp:
            say(ln, lp)
        else:
            print(f"[{TAG}] {ln}", flush=True)
    log(f"收據 {out / 'LAUNCH_latest.json'} · 貼回包 {out / 'LAUNCH_latest.txt'}(黃字整段貼回 AI)")
    if res["page"] and "--no-open" not in a and os.environ.get("VIA_NO_OPEN") != "1":
        try:
            opened = opener(Path(res["page"]).as_uri())
        except Exception:  # noqa: BLE001
            opened = False
        log(f"U/I {res['page']}" + ("(已開)" if opened else "(這台開不了瀏覽器,請手動開)"))
    return res["rc"]


def main() -> int:
    a = sys.argv[1:]
    if a[:1] == ["--selftest"]:
        return selftest()
    if a[:1] == ["launch"]:
        return launch(a[1:])
    return PRIOR.main()


def selftest() -> int:
    ok, bad = [], []

    def chk(name, cond, note=""):
        (ok if cond else bad).append(name)
        print(("  [OK] " if cond else "  [NG] ") + name + (f" · {note}" if note else ""), flush=True)

    chk("加速器載入(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    below = [p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)]
    chk("前版經 glob 載入(本檔之下最大的一版)", PRIOR_PATH == max(below, key=_vnum), PRIOR_PATH.name)
    chk("TAILAPI:前版公開名稱經本檔轉接(cmd_schedule · core_python · book)", all(callable(getattr(sys.modules[__name__], n, None)) for n in ("cmd_schedule", "core_python", "book")))
    n1, _ = lane_count(1)
    n9, _ = lane_count(9)
    nl, why = lane_count(None, min_gb=10 ** 6)
    chk("道數夾在 3~6 · 記憶體低 → 3", (n1, n9, nl) == (3, 6, 3), why)
    real = plan()
    chk("真倉計畫:主控台 · 鎖冊 token 工具 · 重工守門 都解析得到", all(s["file"] for s in [real["gate"], *real["lanes"], real["post"]]),
        str([(s["name"], bool(s["file"])) for s in [real["gate"], *real["lanes"], real["post"]]]))
    saved_no_open = os.environ.pop("VIA_NO_OPEN", None)   # 自測不吃本機狀態:串測殼會設 VIA_NO_OPEN=1
    with tempfile.TemporaryDirectory() as td:
        via = Path(td) / "repo" / "VeritasIntelligenceAnalytics"
        reg = via / "supportive modules" / "registry"
        ai = via / "docs" / "handoff" / "ai"
        reg.mkdir(parents=True)
        ai.mkdir(parents=True)
        fake = ("import os, sys, time, pathlib\n"
                "a = sys.argv[1:]\n"
                "assert os.environ.get('VIA_FROM_VCGC') == 'YES'\n"
                "if a[:1] == ['token']: print('[第一步] x'); sys.exit(int(os.environ.get('FAKE_TOKEN_RC', '0')))\n"
                "if a[:1] == ['overview']:\n"
                "    p = pathlib.Path(__file__).resolve().parents[2] / 'VIA_Reports' / 'vcgc'; p.mkdir(parents=True, exist_ok=True)\n"
                "    (p / 'VCGC_Overview_latest.html').write_text('<html></html>'); print('[U/I] ok'); sys.exit(0)\n"
                "if a[:2] == ['run', 'CGC_MDL245_SDDValidator']: print('[RED] X-FAKE 假紅'); print('[SDD 驗證] RED · fake'); sys.exit(1)\n"
                "if a[:1] == ['test']: time.sleep(1.2); print('[VCGC 全功能串測] YELLOW · fake'); sys.exit(2)\n"
                "if a[:1] == ['delta']: time.sleep(30)\n"
                "print('[編號只增稽核] GREEN · fake'); sys.exit(0)\n")
        (reg / "CGC_MDL149_VeritasCentralGovernanceConsole_v0100.py").write_text(fake, encoding="utf-8")
        (reg / "CGC_MDL158_Fake_v0100.py").write_text(fake, encoding="utf-8")
        (reg / "VIA_ToolVersion_Lock_v0100.json").write_text(json.dumps(
            {"token": {"path": "VeritasIntelligenceAnalytics/supportive modules/registry/CGC_MDL158_Fake_v0100.py"}}), encoding="utf-8")
        me = reg / "CGC_FakeManager_v0100.py"   # 假管理器夾具(不用本家族名,免被當成釘死前版)
        me.write_text(fake, encoding="utf-8")
        out = via / "VIA_Reports" / "vcgc" / "launch"
        env_before = dict(os.environ)
        lines, opened = [], []
        log = lambda m, lamp=None: lines.append(m)  # noqa: E731
        p = plan(via, reg, self_file=me)
        chk("計畫:沒有重工守門 → 那一步 file=None(跑時記灰)", next(s for s in p["lanes"] if s["name"] == "rework")["file"] is None)
        rc_plan = launch(["--plan"], via, reg, me, sys.executable, out, opened.append, log, every=1)
        chk("--plan:rc 0 · 不起子行程 · 不寫檔", rc_plan == 0 and not out.exists())
        os.environ["FAKE_TOKEN_RC"] = "1"
        rc_gate = launch(["--no-open", "--timeout", "8"], via, reg, me, sys.executable, out, opened.append, log, every=1)
        g = json.loads((out / "LAUNCH_latest.json").read_text(encoding="utf-8"))
        chk("閘:token 紅 → 停,後面一步都不跑 · rc 1", rc_gate == 1 and g["results"] == [] and g["post_result"] is None and len(g["counts"]["skipped"]) == 7)
        os.environ["FAKE_TOKEN_RC"] = "0"
        t0 = time.time()
        rc = launch(["--timeout", "4", "--lanes", "6"], via, reg, me, sys.executable, out, opened.append, log, every=1)
        el = time.time() - t0
        r = json.loads((out / "LAUNCH_latest.json").read_text(encoding="utf-8"))
        by = {s["name"]: s for s in r["results"]}
        chk("rc → 燈:test 黃 · sdd 紅 · number 綠 · toolbox 綠 · rework 灰", (by["test"]["lamp"], by["sdd"]["lamp"], by["number"]["lamp"], by["toolbox"]["lamp"], by["rework"]["lamp"])
            == ("YELLOW", "RED", "GREEN", "GREEN", "GRAY"), str({k: v["lamp"] for k, v in by.items()}))
        chk("逾時:delta 4 秒被停 · rc 124 · 紅(只停自己的子行程)", by["delta"]["rc"] == 124 and by["delta"]["lamp"] == "RED")
        chk("並行:六道同時(總時間 < 序跑的和)", el < 4 + 1.2 + 6, f"{el:.1f}s")
        chk("總燈紅 · rc 1 · 收據 §3 欄位齊 · 三數對得上", rc == 1 and r["lamp"] == "RED" and all(k in r for k in ("system", "verb", "version", "utc", "rc", "lamp", "counts", "logs"))
            and r["counts"]["should"] == 8 and r["counts"]["ran"] == 7 and r["counts"]["skipped"] == [])
        pk = (out / "LAUNCH_latest.txt").read_text(encoding="utf-8").splitlines()
        chk("貼回包 ≤300 行 · 帶假紅原文 · 最後一行 NEXT:", len(pk) <= 300 and any("X-FAKE" in x for x in pk) and pk[-1].startswith("NEXT:"), pk[-1][:80])
        chk("心跳:有 [心跳] 行與百分比", any("[心跳]" in x and "%" in x for x in lines))
        chk("U/I:overview 產頁後打開(file://)", r["page"] and opened and opened[-1].startswith("file://"))
        chk("帳只增:LAUNCH_LEDGER 兩列", len((out / "LAUNCH_LEDGER.jsonl").read_text(encoding="utf-8").splitlines()) == 2)
        chk("容器不冒充主機:非 Windows 標「容器」", r["host"] == ("主機" if os.name == "nt" else "容器"))
        os.environ.pop("FAKE_TOKEN_RC", None)
        chk("環境變數沒外溢(子行程 env 只在子行程)", dict(os.environ) == env_before)
        chk("總結行:挑「[名稱] 燈 · …」不挑細項;rc≠0 退而挑第一行黃紅",
            verdict(["[編號只增稽核] YELLOW · x", "[註冊完整性] GREEN  IMMUT 0 · y"]) == "[編號只增稽核] YELLOW · x"
            and verdict(["## h", "[YELLOW] manager · 缺:有編號", "[GREEN] token · ok"], 2) == "[YELLOW] manager · 缺:有編號")
    if saved_no_open is not None:
        os.environ["VIA_NO_OPEN"] = saved_no_open
    pr = subprocess.run([sys.executable, str(PRIOR_PATH), "--selftest"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    last = (pr.stdout.strip().splitlines() or ["?"])[-1]
    print(f"  [INFO] 直接前版 {PRIOR_PATH.name} 自測 rc {pr.returncode} · {last}(裁定甲:只驗本版與直接前版;前版的環境黃不算本版)", flush=True)
    print(f"{TAG} selftest {len(ok)}/{len(ok) + len(bad)}" + (" · 不過:" + " · ".join(bad) if bad else ""), flush=True)
    return 0 if not bad else 1


if __name__ == "__main__":
    raise SystemExit(main())
