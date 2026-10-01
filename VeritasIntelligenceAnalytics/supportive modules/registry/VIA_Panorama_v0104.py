#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_Panorama v0104 — 碰到 VCGC 就自動開監控 · VCGC ↔ 子系統 AUTO SYNC(薄尾;前版 v0103(第一步監控 first · monitor)→ v0102 → v0101 → 本體 v0100)

合併註(2026-10-01):本版原在側線編為 v0103,與 main 的 VIA_Panorama_v0103(R34 第一步監控)撞號(一號不得兩主)→ 改編 v0104,
  前版釘 main 的 v0103;v0102 用 v0103 自己載入的那一份(同一個模組物件,補丁兩邊都生效)。first / monitor 動詞照 v0103。

操作員(側線 2026-09-30):「上傳擋入 VCGC 起任何碰到 VCGC 就自動開啟他來監控 · 與 VCGC 高度 AUTO SYNC ·
  VCGC 與子系統高度 AUTO SYNC」「導入加速器」
本版加三件,其餘全部轉交前版:
  ① autostart [--from <VCGC 動詞>] [--interval 30] [--idle 1800]
     VCGC v0182 每個動作收尾都叫這支(背景、非阻塞):記一筆觸碰(vcgc_touch.jsonl,只增)→ 監控沒在跑就起一支背景 watch
     (pid 鎖單例;Windows 第一次起會開儀表板,VIA_NO_OPEN=1 不開)。約 0.3 秒回來,不等掃描。
  ② watch --autosync [--idle 秒]:每輪照 v0102(304 不重掃 · 教訓 · 全函式記錄);有新觸碰或樹變了,且距上次同步 ≥ VIA_PANORAMA_SYNC_GAP
     (預設 120 秒),就經 VCGC 中央入口跑兩支唯讀同步探針 —— sync-check(座位 · 註冊冊乾跑 · SDD)與 ssot panorama(六族 × 四層:
     VCGC → VDF → VRN → SUP)—— 用加速器 accel_map 並行、run_fast 逾時保護。結果寫 autosync_latest.json,燈變化記成教訓(S 段)。
     最後一次觸碰超過 --idle 秒(預設 30 分)自己停,pid 鎖跟著清。
  ③ sync:手動跑一次同步探針,印 ≤ 10 行卡。儀表板加「AUTO SYNC」卡(族 × 層矩陣 · 座位 · 註冊冊 · SDD · 待批准指令 · 最近觸碰)。
不自動 --apply:registry-sync --apply / 編號 --apply 是同意閘,只列出待批准的指令,由操作員下(黃不是綠)。
防遞迴:背景監控與同步探針都帶 VIA_PANORAMA_ACTIVE=1,VCGC v0182 看到就不再觸發;VIA_PANORAMA_AUTO=0 整個關掉。
加速器:子行程一律 VIA_ACCEL.run_fast(逾時誠實回 TIMEOUT);兩支探針 VIA_ACCEL.accel_map 並行;缺席退回標準庫序跑。
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

import html as _html
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR_NAME = "VIA_Panorama_v0103.py"  # 釘名:前版(main 的第一步監控);不自己取尾版
_spec = importlib.util.spec_from_file_location("VIA_Panorama_v0103", HERE / PRIOR_NAME)
V103 = importlib.util.module_from_spec(_spec)
sys.modules["VIA_Panorama_v0103"] = V103
_spec.loader.exec_module(V103)
V102 = V103.PRIOR  # v0103 自己載入的 v0102(同一個物件:本版對 v0102 的補丁 v0103 的 first 也吃得到)
V101, BASE = V102.V101, V102.BASE
PRIOR = V103
_SKIP = ("main", "selftest", "VERSION", "ENGINE", "HERE", "PRIOR", "PRIOR_NAME")
globals().update({k: v for k, v in vars(V102).items() if not k.startswith("_") and k not in _SKIP})
globals().update({k: v for k, v in vars(V103).items() if not k.startswith("_") and k not in _SKIP})


def __getattr__(name: str):
    """PEP 562:本版沒有的名稱轉給前版 v0103(再往下 v0102 → v0101 → 本體 v0100)。"""
    for m in (V103, V102):
        try:
            return getattr(m, name)
        except AttributeError:
            pass
    raise AttributeError(f"{__name__} 與前版都沒有 {name}")


VERSION = "v0104"
ENGINE = Path(__file__).stem
TOUCH = "vcgc_touch.jsonl"
PIDF = "watch.pid"
SYNC = "autosync_latest.json"
ACTIVE_ENV = "VIA_PANORAMA_ACTIVE"
CONSOLE_GLOB = "CGC_MDL149_VeritasCentralGovernanceConsole_v*.py"
SSOT_REPORT = Path("VIA_Reports") / "ssot_panorama" / "SSOT_PANORAMA_latest.json"


# ───────────────────────── 子行程(加速器)──────────────────────────

def run_fast(argv: list, timeout: int, env: dict | None = None, cwd: str | None = None) -> tuple:
    """VIA_ACCEL.run_fast(env/cwd 需要時退標準庫);回 (rc, 全部輸出)。逾時 rc = 'TIMEOUT'。"""
    if VIA_ACCEL is not None and hasattr(VIA_ACCEL, "run_fast") and env is None and cwd is None:
        try:
            return VIA_ACCEL.run_fast(argv, timeout=timeout)
        except Exception as e:
            BASE.note(f"run_fast 失敗,退標準庫:{e}")
    try:
        p = subprocess.run(argv, capture_output=True, timeout=timeout, stdin=subprocess.DEVNULL, env=env, cwd=cwd)
        return p.returncode, (p.stdout + p.stderr).decode("utf-8", "replace")
    except subprocess.TimeoutExpired:
        return "TIMEOUT", f"逾時 {timeout}s(誠實)"


def amap(fn, items: list) -> list:
    """VIA_ACCEL.accel_map 並行(保序 · 例外隔離);缺席序跑。"""
    if VIA_ACCEL is not None and hasattr(VIA_ACCEL, "accel_map"):
        try:
            return [r if ok else {"err": str(r)[:120]} for ok, r in VIA_ACCEL.accel_map(fn, items)]
        except Exception as e:
            BASE.note(f"accel_map 失敗,退序跑:{e}")
    out = []
    for it in items:
        try:
            out.append(fn(it))
        except Exception as e:
            out.append({"err": str(e)[:120]})
    return out


# ───────────────────────── 單例 · 觸碰 ─────────────────────────

def pid_alive(pid: int) -> bool:
    ps = V102.lib("psutil")
    if ps is not None:
        try:
            if not ps.pid_exists(pid):
                return False
            return "VIA_Panorama" in " ".join(ps.Process(pid).cmdline())  # pid 被別的行程重用 = 不算
        except Exception:
            return False
    if os.name == "nt":  # Windows 不用 os.kill(0):它會結束行程
        rc, out = run_fast(["tasklist", "/FI", f"PID eq {pid}", "/NH"], timeout=10)
        return rc == 0 and str(pid) in out
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def watcher_pid(out: Path) -> int | None:
    try:
        pid = int(json.loads((out / PIDF).read_text(encoding="utf-8"))["pid"])
    except (OSError, ValueError, KeyError, TypeError):
        return None
    return pid if pid_alive(pid) else None


def touch(out: Path, verb: str) -> dict:
    rec = {"ts": BASE.now_utc(), "verb": (verb or "?")[:40], "pid": os.getpid()}
    out.mkdir(parents=True, exist_ok=True)
    with open(out / TOUCH, "a", encoding="utf-8") as f:  # 只增
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def last_touch(out: Path) -> dict:
    lines = V101.tail_lines(out / TOUCH, 1)
    try:
        return json.loads(lines[-1]) if lines else {}
    except ValueError:
        return {}


def autostart(target: str | None, opts: dict) -> int:
    out = V101.resolve_out(target, opts)
    rec = touch(out, opts.get("from") or "manual")
    pid = watcher_pid(out)
    if pid:
        print(f"[監控] 背景全景監控中 pid {pid} · 觸碰 {rec['verb']} · 頁 {out / V101.PAGE_NAME}")
        return 0
    argv = [sys.executable, str(Path(__file__).resolve()), "watch", "--autosync", "--interval", str(int(opts.get("interval") or 30)),
            "--idle", str(int(opts.get("idle") or 1800))]
    if target:
        argv.insert(3, target)
    for k in ("profile", "scope", "out"):
        if opts.get(k):
            argv += [f"--{k}", str(opts[k])]
    env = {**os.environ, ACTIVE_ENV: "1", "VIA_NO_OPEN": "1"}
    kw = {"creationflags": 0x00000008 | 0x00000200} if os.name == "nt" else {"start_new_session": True}  # DETACHED | NEW_GROUP
    with open(out / "watch.out", "a", encoding="utf-8") as log:
        p = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, env=env, close_fds=True, **kw)
    (out / PIDF).write_text(json.dumps({"pid": p.pid, "ts": BASE.now_utc(), "argv": argv[2:]}, ensure_ascii=False), encoding="utf-8")
    page = out / V101.PAGE_NAME
    if os.name == "nt" and os.environ.get("VIA_NO_OPEN") != "1":
        try:
            os.startfile(str(page))  # noqa: S606 — 只開本機報告頁
        except OSError as e:
            BASE.note(f"開頁失敗:{e}")
    print(f"[監控] 已在背景起全景監控 pid {p.pid} · 每 {argv[argv.index('--interval') + 1]} 秒 · 閒置 "
          f"{argv[argv.index('--idle') + 1]} 秒自停 · 頁 {page}")
    return 0


# ───────────────────────── AUTO SYNC(經 VCGC 中央入口 · 唯讀)──────────────────────────

def console() -> Path | None:
    via = BASE.via_root()
    hits = sorted(via.joinpath("supportive modules", "registry").glob(CONSOLE_GLOB)) if via else []
    return hits[-1] if hits else None


def _first_json(text: str) -> dict | None:
    dec = json.JSONDecoder()
    for i, ln in enumerate(text.splitlines()):
        if ln.startswith("{"):
            try:
                return dec.raw_decode("\n".join(text.splitlines()[i:]))[0]
            except ValueError:
                BASE.note(f"探針輸出第 {i + 1} 行不是完整 JSON,往下找")
                continue
    return None


def probe(kind: str) -> dict:
    if os.environ.get("VIA_PANORAMA_NO_PROBE") == "1":  # 自測用:不碰真 VCGC
        return {"probe": kind, "lamp": "ABSENT", "why": "VIA_PANORAMA_NO_PROBE=1", "rc": None, "sec": 0}
    con = console()
    if con is None:
        return {"probe": kind, "lamp": "ABSENT", "why": "VCGC 尾版不在"}
    argv = {"sync-check": ["sync-check"], "ssot": ["ssot", "panorama"]}[kind]
    env = {**os.environ, "VIA_FROM_VCGC": "YES", "VIA_VCGC_PUSH": "NO", "VIA_NO_OPEN": "1", ACTIVE_ENV: "1"}
    t0 = time.time()
    rc, txt = run_fast([sys.executable, str(con), *argv], timeout=900, env=env, cwd=str(con.parents[3]))
    res = {"probe": kind, "rc": rc, "sec": round(time.time() - t0, 1), "console": con.name}
    if kind == "sync-check":
        j = _first_json(txt) or {}
        reg = j.get("registry") or {}
        seat = j.get("seat") or {}
        sdd = j.get("sdd") or {}
        res.update(seat_ok=bool(seat.get("lock_success")) and not seat.get("missing"), seat_missing=seat.get("missing") or [],
                   registry={k: reg.get(k, 0) for k in ("new", "changed", "stale", "recode")}, expected=reg.get("expected"),
                   sdd=sdd.get("lamp", "NODATA"), sdd_red=sdd.get("red") or [], aligned=j.get("aligned"), pending=j.get("pending"))
        res["lamp"] = "ABSENT" if not j else ("RED" if not res["seat_ok"] or sdd.get("lamp") == "RED" else
                                              ("YELLOW" if j.get("pending") or any(res["registry"].values()) or sdd.get("lamp") != "GREEN" else "GREEN"))
    else:
        try:
            d = json.loads((con.parents[2] / SSOT_REPORT).read_text(encoding="utf-8"))
            res.update(lamp=d.get("verdict", "NODATA"), families=d.get("families"), layers=d.get("layers"), ts=d.get("ts"),
                       cells=[{"family": c.get("family"), "layer": c.get("layer"), "state": c.get("state"), "detail": str(c.get("detail", ""))[:120]}
                              for c in d.get("cells", [])])
        except (OSError, ValueError) as e:
            res.update(lamp="ABSENT", why=f"SSOT 全景報告讀不到:{type(e).__name__}")
    return res


def autosync(out: Path, trigger: str, rep: dict | None = None) -> dict:
    t0 = time.time()
    got = amap(probe, ["sync-check", "ssot"])  # 加速器並行
    sc, sp = got[0], got[1]
    res = {"ts": BASE.now_utc(), "trigger": trigger, "sec": round(time.time() - t0, 1), "sync_check": sc, "ssot": sp,
           "lamp": BASE.worst([sc.get("lamp", "ABSENT"), sp.get("lamp", "ABSENT")]),
           "accel": "accel_map" if VIA_ACCEL is not None else "序跑", "approve": approvals(sc, sp)}
    old = None
    try:
        old = json.loads((out / SYNC).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        old = None
    tmp = out / (SYNC + ".tmp")
    tmp.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(out / SYNC)
    if rep is not None:
        V102.append_lessons(out, sync_lessons(old, res, rep))
    V102.LOG.info("AUTO SYNC", extra={"extra_json": {"trigger": trigger, "lamp": res["lamp"], "sec": res["sec"],
                                                     "registry": sc.get("registry"), "sdd": sc.get("sdd"), "ssot": sp.get("lamp")}})
    return res


def approvals(sc: dict, sp: dict) -> list:
    """同意閘:只列待批准的指令,不自動下。"""
    out = []
    reg = sc.get("registry") or {}
    if any(reg.get(k) for k in ("new", "changed", "stale")):
        out.append({"why": f"註冊冊待同步 新 {reg.get('new')} · 變 {reg.get('changed')} · 過期 {reg.get('stale')}",
                    "cmd": "via-vcgc registry-sync --apply  → 提交後 via-vcgc run CGC_MDL237_NumberingSystem --apply --scope"})
    if sc.get("seat_missing"):
        out.append({"why": f"座位缺 {len(sc['seat_missing'])}", "cmd": "via-vcgc status(看座位)"})
    if sc.get("sdd") not in (None, "GREEN", "NODATA"):
        out.append({"why": f"SDD {sc.get('sdd')}", "cmd": "via-vcgc run CGC_MDL245_SDDValidator check"})
    bad = [c for c in sp.get("cells") or [] if c.get("state") in ("RED", "YELLOW")]
    if bad:
        out.append({"why": f"SSOT 全景非綠 {len(bad)} 格(RED {sum(1 for c in bad if c['state'] == 'RED')})",
                    "cmd": "via-vcgc ssot panorama --full(全部重量)· 看 VIA_Reports/ssot_panorama/SSOT_PANORAMA_latest.html"})
    return out


def sync_rows(res: dict) -> dict:
    rows = {}
    sc, sp = res.get("sync_check") or {}, res.get("ssot") or {}
    rows["S:sync-check"] = sc.get("lamp", "ABSENT")
    rows["S:SDD"] = sc.get("sdd", "NODATA")
    rows["S:座位"] = "GREEN" if sc.get("seat_ok") else ("ABSENT" if "seat_ok" not in sc else "RED")
    reg = sc.get("registry") or {}
    rows["S:註冊冊"] = "YELLOW" if any(reg.get(k) for k in ("new", "changed", "stale")) else ("GREEN" if reg else "ABSENT")
    for c in sp.get("cells") or []:
        rows[f"S:{c['family']}@{c['layer']}"] = c.get("state", "NODATA")
    return rows


def sync_lessons(old: dict | None, new: dict, rep: dict) -> list:
    if not old:
        return []
    a, b = sync_rows(old), sync_rows(new)
    base = {"ts": BASE.now_utc(), "run": f"sync-{new['ts']}", "target_key": rep.get("target_key"), "target": rep.get("target"),
            "sha16": rep.get("sha16"), "etag": rep.get("etag"), "section": "S", "sig": "sync"}
    out = []
    for k in sorted(set(a) | set(b)):
        fa, fb = a.get(k), b.get(k)
        kind = None
        if fa in V102.BAD and fb not in V102.BAD:
            kind = "FIXED"
        elif fb in V102.BAD and fa not in V102.BAD:
            kind = "NEW"
        elif fa in V102.BAD and fb in V102.BAD and fa != fb:
            kind = "ESCALATED" if BASE.SEVER.get(fb, 0) > BASE.SEVER.get(fa, 0) else "EASED"
        if kind:
            out.append(dict(base, kind=kind, key=k, **{"from": fa or "—", "to": fb or "—"}, note=f"AUTO SYNC · 觸發 {new.get('trigger')}"))
    return out


# ───────────────────────── 儀表板:AUTO SYNC 卡 ─────────────────────────

def sync_card(out: Path) -> tuple:
    e = _html.escape
    try:
        res = json.loads((out / SYNC).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        res = None
    touches = []
    for ln in V101.tail_lines(out / TOUCH, 12)[::-1]:
        try:
            x = json.loads(ln)
            touches.append({"時間": x["ts"][5:19].replace("T", " "), "VCGC 動作": x.get("verb", "")})
        except (ValueError, KeyError):
            BASE.note("觸碰紀錄壞行略過")
            continue
    pid = watcher_pid(out)
    head = (f"監控 {'pid ' + str(pid) if pid else '沒在背景跑(單次產頁)'} · 觸碰 {len(V101.tail_lines(out / TOUCH, 100000))} 次"
            f" · 探針並行 {res.get('accel') if res else '—'}")
    if not res:
        body = "<div class='nop'>還沒同步過:碰一下 VCGC(任何動作)或跑 sync</div>"
        return (f"<div class='grid'><div class='card'><h2>AUTO SYNC · VCGC ↔ 子系統<span class='c'>{e(head)}</span></h2>{body}</div>"
                f"<div class='card'><h2>最近觸碰 VCGC</h2>{V101.tbl(['時間', 'VCGC 動作'], touches, lamp_cols=())}</div></div>", "")
    sc, sp = res.get("sync_check") or {}, res.get("ssot") or {}
    reg = sc.get("registry") or {}
    kv = [{"項": "sync-check", "lamp": sc.get("lamp", "ABSENT"), "值": f"rc {sc.get('rc')} · {sc.get('sec')}s"},
          {"項": "座位", "lamp": "GREEN" if sc.get("seat_ok") else "RED", "值": f"缺 {len(sc.get('seat_missing') or [])}"},
          {"項": "註冊冊(乾跑)", "lamp": "YELLOW" if any(reg.get(k) for k in ("new", "changed", "stale")) else "GREEN",
           "值": f"新 {reg.get('new', 0)} · 變 {reg.get('changed', 0)} · 過期 {reg.get('stale', 0)} · 應有 {sc.get('expected', '—')}"},
          {"項": "SDD", "lamp": sc.get("sdd", "NODATA"), "值": f"紅 {len(sc.get('sdd_red') or [])}"},
          {"項": "SSOT 全景", "lamp": sp.get("lamp", "ABSENT"), "值": f"{sp.get('ts', '')} · {sp.get('sec', '')}s"}]
    appr = "".join(f"<li>{e(a['why'])}<br><span class='mono'>{e(a['cmd'])}</span></li>" for a in res.get("approve", [])) or "<li>沒有待批准的</li>"
    fams = list((sp.get("families") or {}).keys()) or sorted({c["family"] for c in sp.get("cells") or []})
    layers = sp.get("layers") or sorted({c["layer"] for c in sp.get("cells") or []})
    cell = {(c["family"], c["layer"]): c for c in sp.get("cells") or []}
    order = {"GREEN": 0.5, "HOLD": 1.5, "ABSENT": 1.5, "NODATA": 1.5, "YELLOW": 2.5, "RED": 3.5}
    z = [[order.get((cell.get((f, l)) or {}).get("state", "NODATA"), 1.5) for l in layers] for f in fams]
    txt = [[((cell.get((f, l)) or {}).get("state") or "·")[:1] for l in layers] for f in fams]
    hov = [[f"{f}@{l} · {(cell.get((f, l)) or {}).get('state', '—')}<br>{e((cell.get((f, l)) or {}).get('detail', '')[:80])}" for l in layers] for f in fams]
    S = V101.STATUS
    fig = {"data": [{"type": "heatmap", "x": layers, "y": fams, "z": z, "text": txt, "texttemplate": "%{text}", "customdata": hov,
                     "textfont": {"size": 10, "color": "#0b0b0b"}, "zmin": 0, "zmax": 4, "showscale": False, "xgap": 2, "ygap": 2,
                     "colorscale": [[0, S["GREEN"]], [0.25, S["GREEN"]], [0.25, S["HOLD"]], [0.5, S["HOLD"]], [0.5, S["YELLOW"]],
                                    [0.75, S["YELLOW"]], [0.75, S["RED"]], [1, S["RED"]]], "hovertemplate": "%{customdata}<extra></extra>"}],
           "layout": {"margin": {"l": 46, "r": 6, "t": 4, "b": 22}, "paper_bgcolor": "#fcfcfb", "plot_bgcolor": "#fcfcfb",
                      "font": {"size": 10, "color": "#52514e"}, "yaxis": {"autorange": "reversed"}, "xaxis": {"side": "bottom"}}}
    html = ("<div class='grid'>"
            f"<div class='card'><h2>AUTO SYNC · VCGC ↔ 子系統 {V101.pill(res.get('lamp'))}<span class='c'>{e(head)}</span></h2>"
            f"<div class='meta' style='margin-bottom:4px'>上次同步 <span class='mono'>{e(res['ts'][11:19])}Z</span> · 觸發 {e(res.get('trigger', ''))}"
            f" · {res.get('sec')}s · 只讀探針(sync-check · ssot panorama);--apply 不自動下</div>"
            + V101.tbl(["項", "lamp", "值"], kv, widths=["96px", "84px", "auto"])
            + f"<div class='meta' style='margin:6px 0 2px'>待批准(同意閘)</div><ul style='margin:0 0 0 16px;padding:0;overflow-wrap:anywhere'>{appr}</ul></div>"
            f"<div class='card'><h2>SSOT 族 × 層(VCGC → VDF → VRN → SUP)<span class='c'>{len(cell)} 格</span></h2><div id='fig_sync' class='plot tall'></div></div>"
            f"<div class='card'><h2>最近觸碰 VCGC<span class='c'>{len(touches)} 筆</span></h2>{V101.tbl(['時間', 'VCGC 動作'], touches, lamp_cols=(), widths=['110px', 'auto'])}</div>"
            "</div>")
    js = ("<script>(function(){var f=" + json.dumps(fig, ensure_ascii=False) + ",el=document.getElementById('fig_sync');if(!el)return;"
          "if(window.Plotly){Plotly.newPlot(el,f.data,f.layout,{displayModeBar:false,responsive:true})}else{el.innerHTML=\"<div class='nop'>沒有 Plotly</div>\"}})();</script>")
    return html, js


def add_sync_card(out: Path) -> None:
    page_p = out / V101.PAGE_NAME
    try:
        page = page_p.read_text(encoding="utf-8")
    except OSError:
        return
    html, js = sync_card(out)
    i = page.find("<div class='grid'>")
    page = (page[:i] + html + page[i:]) if i > 0 else page.replace("<footer>", html + "<footer>", 1)  # 放在 KPI 列正下方、第一排圖之前
    page = page.replace("</body>", js + "</body>", 1).replace(f"VIA_Panorama {V102.VERSION}(前版 v0101", f"VIA_Panorama {VERSION}(前版 v0102 · v0101", 1)
    tmp = out / (V101.PAGE_NAME + ".tmp")
    tmp.write_text(page, encoding="utf-8")
    tmp.replace(page_p)


# ───────────────────────── 動詞 ─────────────────────────

def one_round(target: str | None, opts: dict, out: Path, interval: int, state: dict) -> tuple:
    rc, line = V102.one_round(target, opts, out, interval)
    if opts.get("autosync"):
        gap = int(os.environ.get("VIA_PANORAMA_SYNC_GAP", "120"))
        tch = last_touch(out)
        rep = V102._latest(out) or {}
        changed = rep.get("etag") != state.get("etag")
        new_touch = tch.get("ts") and tch.get("ts") != state.get("touch")
        if (changed or new_touch) and time.time() - state.get("at", 0) >= gap:
            trig = f"VCGC {tch.get('verb')}" if new_touch else "樹變了"
            res = autosync(out, trig, rep)
            state.update(at=time.time(), etag=rep.get("etag"), touch=tch.get("ts"))
            line += f"  AUTO SYNC {res['lamp']} {res['sec']}s({trig})"
    add_sync_card(out)
    return rc, line


def watch(target: str | None, opts: dict) -> int:
    interval = max(5, int(opts.get("interval") or 30))
    rounds, idle = int(opts.get("rounds") or 0), int(opts.get("idle") or 0)
    out = V101.resolve_out(target, opts)
    out.mkdir(parents=True, exist_ok=True)
    other = watcher_pid(out)
    if other and other != os.getpid():
        print(f"[{ENGINE} watch] 已有監控 pid {other} · 不重複起(單例)")
        return 0
    (out / PIDF).write_text(json.dumps({"pid": os.getpid(), "ts": BASE.now_utc()}), encoding="utf-8")
    print(f"[{ENGINE} watch] 每 {interval} 秒 · AUTO SYNC {'開' if opts.get('autosync') else '關'} · 閒置 {idle or '∞'} 秒自停 · 頁 {out / V101.PAGE_NAME}", flush=True)
    n, rc, state = 0, 2, {}
    try:
        while True:
            n += 1
            t0 = time.time()
            rc, line = one_round(target, opts, out, interval, state)
            print("  " + line, flush=True)
            if rounds and n >= rounds:
                break
            if idle:
                ts = last_touch(out).get("ts")
                age = (datetime.now(timezone.utc) - datetime.fromisoformat(ts)).total_seconds() if ts else idle + 1
                if age > idle:
                    print(f"  閒置 {int(age)} 秒 > {idle} · 自停", flush=True)
                    break
            time.sleep(max(0.0, interval - (time.time() - t0)))
    except KeyboardInterrupt:
        print(f"  停 · {n} 輪")
    finally:
        try:
            if json.loads((out / PIDF).read_text(encoding="utf-8")).get("pid") == os.getpid():
                (out / PIDF).unlink()
        except (OSError, ValueError):
            BASE.note("pid 鎖清不掉(已被別支取代)")
    return rc


def dashboard(target: str | None, opts: dict) -> int:
    out = V101.resolve_out(target, opts)
    out.mkdir(parents=True, exist_ok=True)
    rc, line = one_round(target, opts, out, 0, {})
    print(f"[{ENGINE} dashboard] {line}\n  頁 {out / V101.PAGE_NAME}")
    return rc


def sync_verb(target: str | None, opts: dict) -> int:
    out = V101.resolve_out(target, opts)
    V102.setup_logging(out)
    res = autosync(out, "手動 sync", V102._latest(out))
    add_sync_card(out)
    sc, sp = res["sync_check"], res["ssot"]
    reg = sc.get("registry") or {}
    bad = [c for c in sp.get("cells") or [] if c.get("state") in ("RED", "YELLOW")]
    lines = [f"[{ENGINE} sync] AUTO SYNC {res['lamp']} · {res['sec']}s(並行 {res['accel']})",
             f"  sync-check {sc.get('lamp')} · 座位 {'齊' if sc.get('seat_ok') else '缺'} · 註冊冊 新 {reg.get('new', 0)} 變 {reg.get('changed', 0)} "
             f"過期 {reg.get('stale', 0)} · SDD {sc.get('sdd')}",
             f"  SSOT 全景 {sp.get('lamp')} · {len(sp.get('cells') or [])} 格 · 非綠 {len(bad)}:" + " · ".join(f"{c['family']}@{c['layer']}" for c in bad[:6])]
    lines += [f"  待批准 {a['why']} → {a['cmd']}" for a in res["approve"][:5]]
    print("\n".join(lines[:10]))
    return 0 if res["lamp"] == "GREEN" else (1 if res["lamp"] == "RED" else 2)


def _opts(rest: list) -> tuple:
    extra = {}
    for key in ("--interval", "--rounds", "--idle"):
        if key in rest:
            i = rest.index(key)
            extra[key[2:]] = int(rest[i + 1]) if i + 1 < len(rest) and rest[i + 1].isdigit() else 0
            del rest[i:i + 2]
    for flag in ("--autosync",):
        if flag in rest:
            extra["autosync"] = True
            rest.remove(flag)
    if "--from" in rest:
        i = rest.index("--from")
        extra["from"] = rest[i + 1] if i + 1 < len(rest) else ""
        del rest[i:i + 2]
    opts, pos = BASE.parse_opts(rest)
    opts.update(extra)
    return opts, (pos[0] if pos else None)


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a and a[0] in ("--selftest", "selftest"):
        return selftest()
    if a and a[0] in ("autostart", "watch", "dashboard", "sync"):
        opts, target = _opts(a[1:])
        if a[0] == "autostart":
            return autostart(target, opts)  # 快路徑:不包記錄,0.3 秒回
        V102.instrument()
        return {"watch": watch, "dashboard": dashboard, "sync": sync_verb}[a[0]](target, opts)
    return V103.main(a)  # first · monitor 與其餘動詞照前版 v0103(再往下 v0102 …)


# ───────────────────────── 自測 ─────────────────────────

def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  {'✓' if cond else '✗'} {name}" + (f" · {note}" if note and not cond else ""))
    import contextlib
    import io
    print(f"=== {ENGINE} 自測(薄尾;先跑前版 v0103 → v0102 → v0101 → 本體 v0100)===")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        prc = V103.selftest()
    for ln in buf.getvalue().splitlines():  # 前版鏈的判決行照印(交接案的標記看得到,例:VIA_Panorama_v0103 selftest 13/13 PASS)
        if re.search(r"selftest \d+/\d+ (PASS|FAIL)", ln):
            print(ln)
    chk("前版 v0103(含 v0102 · v0101 · v0100)自測", prc == 0, (buf.getvalue().strip().splitlines() or [""])[-1])
    miss = [k for k in list(vars(V102)) + list(vars(V103)) if not k.startswith("_") and k not in globals() and k != "PRIOR_NAME"]
    chk("尾版不少公開名稱(TAILAPI)", not miss, " · ".join(miss[:5]))
    rc, txt = run_fast([sys.executable, "-c", "print('{\"a\": 1}')"], timeout=20)
    chk("加速器:run_fast 子行程 · accel_map 並行保序", rc == 0 and _first_json("pre\n" + txt) == {"a": 1}
        and amap(lambda x: x * 3, [1, 2, 3]) == [3, 6, 9] and (VIA_ACCEL is None or hasattr(VIA_ACCEL, "accel_map")))
    tmp = Path(tempfile.mkdtemp(prefix="via_pan103_"))
    saved = os.environ.get("VIA_PANORAMA_NO_PROBE")
    os.environ["VIA_PANORAMA_NO_PROBE"] = "1"  # 背景監控繼承:自測不碰真 VCGC
    try:
        t, out = tmp / "t", tmp / "out"
        t.mkdir()
        (t / "a_v0100.py").write_text('"""a"""\n', encoding="utf-8")
        opts = {"out": str(out), "no_git": True, "profile": "generic", "interval": 5, "idle": 6, "from": "selftest"}
        with contextlib.redirect_stdout(io.StringIO()) as b1:
            autostart(str(t), dict(opts))
        pid = watcher_pid(out)
        chk("autostart:記觸碰 · 起背景 watch(pid 鎖)", pid is not None and len(V101.tail_lines(out / TOUCH, 10)) == 1, b1.getvalue()[:120])
        with contextlib.redirect_stdout(io.StringIO()) as b2:
            autostart(str(t), dict(opts))
        chk("單例:第二次觸碰不重起,只記一筆", watcher_pid(out) == pid and "監控中" in b2.getvalue()
            and len(V101.tail_lines(out / TOUCH, 10)) == 2, b2.getvalue()[:120])
        deadline = time.time() + 40
        while time.time() < deadline and not ((out / V101.PAGE_NAME).is_file()
                                               and "AUTO SYNC" in (out / V101.PAGE_NAME).read_text(encoding="utf-8")):
            time.sleep(0.5)  # 同一輪頁面依序被 v0101 → v0102 → v0103 重寫;等到最後一層
        chk("背景監控產出儀表板(含 AUTO SYNC 卡)", (out / V101.PAGE_NAME).is_file()
            and "AUTO SYNC" in (out / V101.PAGE_NAME).read_text(encoding="utf-8"))
        deadline = time.time() + 40
        while time.time() < deadline and watcher_pid(out):
            time.sleep(0.5)
        chk("閒置超過 --idle 自停 · pid 鎖清掉", watcher_pid(out) is None and not (out / PIDF).exists())
        os.environ[ACTIVE_ENV] = "1"
        chk("防遞迴旗標存在(VCGC v0182 看它不觸發)", os.environ.get(ACTIVE_ENV) == "1")
        os.environ.pop(ACTIVE_ENV, None)
        old = {"ts": "t0", "sync_check": {"lamp": "GREEN", "sdd": "GREEN", "seat_ok": True, "registry": {"new": 0}},
               "ssot": {"cells": [{"family": "REG", "layer": "VCGC", "state": "GREEN"}]}}
        new = {"ts": "t1", "trigger": "VCGC registry-sync", "sync_check": {"lamp": "YELLOW", "sdd": "GREEN", "seat_ok": True, "registry": {"new": 3}},
               "ssot": {"cells": [{"family": "REG", "layer": "VCGC", "state": "YELLOW"}]}}
        ls = sync_lessons(old, new, {"target_key": "k"})
        chk("同步燈變化記成教訓(S 段:註冊冊 · REG@VCGC · sync-check)", {x["key"] for x in ls} >= {"S:註冊冊", "S:REG@VCGC", "S:sync-check"}
            and all(x["kind"] == "NEW" for x in ls))
        ap = approvals(new["sync_check"], new["ssot"])
        chk("同意閘:只列待批准指令(registry-sync --apply)不自動下", any("registry-sync --apply" in a["cmd"] for a in ap))
        src = Path(__file__).read_text(encoding="utf-8")
        chk("本體:加速器橋 · 用 run_fast / accel_map · 不在 Windows 用 os.kill(0)", "[VIA:ACCEL-BRIDGE" in src
            and "VIA_ACCEL.run_fast" in src and "VIA_ACCEL.accel_map" in src and 'if os.name == "nt":  # Windows 不用 os.kill(0)' in src)
    finally:
        if saved is None:
            os.environ.pop("VIA_PANORAMA_NO_PROBE", None)
        else:
            os.environ["VIA_PANORAMA_NO_PROBE"] = saved
        pid = watcher_pid(tmp / "out") if (tmp / "out").exists() else None
        if pid:
            ps = V102.lib("psutil")
            if ps is not None:
                ps.Process(pid).kill()
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"  {ENGINE} selftest {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
