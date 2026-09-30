#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL248_FullCheck v0100 — 整合全景實測:VCGC → VDF → VRN → SUP 一條跑到底 · 紅了照跑下一段 · 一頁 HTML 總報告

操作員(側線 2026-09-30 b):「先把這個面檢視實測的工具整合為一」「給我一個整合後的 POWERSHELL 跳出 HTML 報告如今天清晨」。
面檢視實測原本散在五支正主,本支只編排、不重寫它們的判定(一把尺:燈讀各正主剛寫的報告):
  ⓪ 三橋覆蓋與最新版   console run CGC_MDL124_BridgeSweeper --subsystems / --ps --ps-tail(乾跑)+ 載入的 Celeritas / Aegis 對樹上最新  正主 CGC_MDL124
     (L103 最高政策:PY 導入加速器 · VDF 導入網路工具 · PS 導入模板與加速器;缺一支 = 紅並列出哪一支;補缺由操作員或 AI 經 --apply,本支不寫)
  ① VCGC 指令串測      console test(--full 全部重跑)             → VIA_Reports/vcgc/TEST_latest.json            正主 CGC_MDL224
  ② SSOT 全景          console ssot panorama(--full)              → VIA_Reports/ssot_panorama/…latest.json       正主 CGC_MDL247
  ③ 單一路徑驗證       console run CGC_MDL242_PathVerify run       → VIA_Reports/path_verify/…latest.json         正主 CGC_MDL242
  ④ 自測格子           預設讀最新格子存證(不重跑,標存證時間);--grid 才整張重跑(會重寫已追蹤檔,CLAUDE.md)  正主 CGC_MDL064
  ⑤ 交接防遺漏         console handoff check                       → docs/handoff/HANDOFF_latest.json             正主 CGC_MDL140
每段:rc · 秒數 · 燈(報告的總判;這輪沒更新的報告 = 紅「報告沒更新」,不拿舊的冒充)· 問題清單(非綠逐條:在哪 · 什麼 · 誰的手 · 下一步)。
紀錄:每段一行 + 總判一行只增寫 registry/VIA_VCGC_FullCheck_Ledger_v0100.jsonl(UTC 帶時區 · 正主尾版檔名 · 版號 · sha16 · 秒數 · HEAD)。
頁:CGC_MDL241 呈現套件(與單一路徑驗證頁同一版型)→ VIA_Reports/fullcheck/FULLCHECK_latest.html(+ .json · 時間戳副本)。
只收 VCGC 呼叫;零網路;不寫庫、不 push。用法:run [--full] [--grid] [--no-record] [--only 1,2] | --selftest
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

import hashlib
import html as _html
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
VIA = HERE.parents[1]
ENGINE = Path(__file__).stem
LEDGER_NAME = "VIA_VCGC_FullCheck_Ledger_v0100.jsonl"
CONSOLE_GLOB = "CGC_MDL149_VeritasCentralGovernanceConsole_v*.py"
ORDER = {"RED": 0, "YELLOW": 1, "NODATA": 2, "GREEN": 3}
KIT_LAMP = {"GREEN": "GREEN", "YELLOW": "AMBER", "RED": "RED", "NODATA": "NODATA"}

# 六段(順序即執行序;layer 是上下單向的哪一層)
STEPS = [
    {"n": 0, "id": "bridges", "name": "三橋覆蓋與最新版(PY 加速器 · VDF 網路工具 · PS 加速器;載入的是不是樹上最新)", "layer": "VCGC→VDF→VRN→SUP",
     "argv": ["run", "--family", "core", "CGC_MDL124_BridgeSweeper", "--subsystems"], "argv2": ["run", "--family", "core", "CGC_MDL124_BridgeSweeper", "--ps", "--ps-tail"],
     "full": [], "report": "VIA_Reports/fullcheck/BRIDGES_latest.json", "owner": "CGC_MDL124_BridgeSweeper", "timeout": 900},
    {"n": 1, "id": "vcgc-test", "name": "VCGC 指令串測(全部動詞 · 席位 · 必用卡 · 交接案 · 工作流步 · PS 入口 · 家族尾版)", "layer": "VCGC",
     "argv": ["test"], "full": ["--full"], "report": "VIA_Reports/vcgc/TEST_latest.json", "owner": "CGC_MDL224_TestAuto", "timeout": 1800},
    {"n": 2, "id": "ssot-panorama", "name": "SSOT 全景(正則 · 同義字 · 編號 · 命名 · 註冊 · 上下連結)VCGC → VDF → VRN → SUP", "layer": "VCGC→SUP",
     "argv": ["ssot", "panorama"], "full": ["--full"], "report": "VIA_Reports/ssot_panorama/SSOT_PANORAMA_latest.json",
     "owner": "CGC_MDL247_SSOTPanorama", "timeout": 900},
    {"n": 3, "id": "path-verify", "name": "單一路徑驗證 VCGC → VDF → VRN(執行版本 × 編號 × 註冊 × 鎖)", "layer": "VCGC→VDF→VRN",
     "argv": ["run", "--family", "core", "CGC_MDL242_PathVerify", "run", "--no-record"], "full": [],
     "report": "VIA_Reports/path_verify/PATH_VERIFY_latest.json", "owner": "CGC_MDL242_PathVerify", "timeout": 900},
    {"n": 4, "id": "selftest-grid", "name": "自測格子(VCGC / VDF / VRN / SUP 引擎自測)", "layer": "VDF · VRN · SUP",
     "argv": ["run", "--family", "core", "CGC_MDL064_SelftestGrid"], "full": [], "report": "VIA_Reports/selftest_runs/GRID_*.json",
     "owner": "CGC_MDL064_SelftestGrid", "timeout": 3600, "evidence_unless": "grid"},
    {"n": 5, "id": "handoff", "name": "交接防遺漏(需求 · 待辦 · 收據 · 相依變更)", "layer": "VCGC",
     "argv": ["handoff", "check"], "full": [], "report": "docs/handoff/HANDOFF_latest.json", "owner": "CGC_MDL140_HandoverConsole", "timeout": 900},
]


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")


def _vnum(p) -> int:
    m = re.search(r"[_-]v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


def newest(folder: Path, pattern: str) -> Path | None:
    hits = [p for p in Path(folder).glob(pattern) if p.is_file() and _vnum(p) >= 0]
    return max(hits, key=_vnum) if hits else None


def sha16(path: Path) -> str:
    try:
        return hashlib.sha256(Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()[:16]
    except OSError:
        return ""


def _json(path: Path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _head(via: Path) -> str:
    try:
        return subprocess.run(["git", "-C", str(via), "rev-parse", "--short=9", "HEAD"], capture_output=True, text=True, timeout=10).stdout.strip() or "—"
    except (OSError, subprocess.SubprocessError):
        return "—"


def _lamp(v) -> str:
    v = str(v or "").upper()
    return {"GREEN": "GREEN", "OK": "GREEN", "PASS": "GREEN", "YELLOW": "YELLOW", "AMBER": "YELLOW", "SKIP": "YELLOW",
            "RED": "RED", "FAIL": "RED", "NODATA": "NODATA", "UNTESTED": "NODATA"}.get(v, "NODATA")


def console_runner(via: Path, argv: list, timeout: int) -> tuple:
    """One VCGC console call (gate · events · lessons as usual). Never raises: a crash is rc 1 with the reason."""
    console = newest(via / "supportive modules" / "registry", CONSOLE_GLOB)
    if console is None:
        return 1, "VCGC 主控台尾版不在"
    env = dict(os.environ, VIA_FROM_VCGC="YES", VIA_VCGC_PUSH="NO", VIA_NO_OPEN="1", PYTHONIOENCODING="utf-8")
    try:
        r = subprocess.run([sys.executable, str(console)] + list(argv), cwd=str(via), env=env, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout, stdin=subprocess.DEVNULL)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired:
        return 124, f"TIMEOUT {timeout}s"
    except OSError as exc:
        return 1, f"{type(exc).__name__}: {exc}"


# ---------------------------------------------------------------- each report → lamp + summary + problems
def read_test(d: dict) -> tuple:
    c = d.get("counts") or {}
    probs = [{"where": "VCGC", "item": r.get("id"), "lamp": _lamp(r.get("lamp")), "detail": (r.get("name") or "") + " · " + (r.get("last") or ""),
              "next": "via-vcgc test --only " + str(r.get("id"))} for r in d.get("rows") or [] if _lamp(r.get("lamp")) != "GREEN"]
    probs += [{"where": "VCGC", "item": x, "lamp": "YELLOW", "detail": "新指令沒登盤點冊", "next": "登進 VIA_VCGC_FunctionInventory_SSOT 新版號"} for x in d.get("new") or []]
    probs += [{"where": "VCGC", "item": x, "lamp": "RED", "detail": "盤點冊有、樹上沒有", "next": "查是誰刪的;冊出新版號"} for x in d.get("gone") or []]
    summ = f"站 {sum(c.values()) if c else len(d.get('rows') or [])} · 綠 {c.get('GREEN', 0)} · 黃 {c.get('YELLOW', 0)} · 紅 {c.get('RED', 0)} · 模式 {d.get('mode', '?')}"
    return _lamp(d.get("lamp")), summ, probs


def read_panorama(d: dict) -> tuple:
    cells = d.get("cells") or []
    probs = [{"where": c.get("layer"), "item": c.get("key") or f"{c.get('family')}@{c.get('layer')}", "lamp": _lamp(c.get("state")),
              "detail": c.get("detail") or "", "next": c.get("next") or "", "owner": c.get("owner") or ""}
             for c in cells if _lamp(c.get("state")) not in ("GREEN", "NODATA")]
    n = {k: sum(1 for c in cells if _lamp(c.get("state")) == k) for k in ORDER}
    return _lamp(d.get("verdict")), f"格 {len(cells)} · 綠 {n['GREEN']} · 黃 {n['YELLOW']} · 紅 {n['RED']} · 探針 {len(d.get('probes') or [])}", probs


def read_path(d: dict) -> tuple:
    steps = d.get("steps") or []
    vers = d.get("versions") or []
    probs = [{"where": "路徑", "item": s.get("step"), "lamp": _lamp(s.get("state")), "detail": s.get("note") or "", "next": ""}
             for s in steps if _lamp(s.get("state")) not in ("GREEN",)]
    probs += [{"where": v.get("where") or "版本", "item": v.get("file"), "lamp": _lamp(v.get("state")), "detail": v.get("why") or "", "next": "編號 / 註冊 / 鎖冊對齊"}
              for v in vers if _lamp(v.get("state")) != "GREEN"]
    bad = sum(1 for v in vers if _lamp(v.get("state")) != "GREEN")
    return _lamp(d.get("verdict")), f"路徑 {len(steps)} 步 · 版本 {len(vers)} 支(不齊 {bad})", probs


def read_grid(d: dict) -> tuple:
    rows = d.get("results") or []
    probs = [{"where": "格子", "item": r.get("name"), "lamp": "RED" if r.get("state") in ("FAIL", "TIMEOUT") else "YELLOW",
              "detail": (r.get("note") or "")[:300], "next": "via-selftest --only " + str(r.get("name") or "")[:24]}
             for r in rows if r.get("state") not in ("OK",)]
    fail = int(d.get("fail") or 0) + int(d.get("timeout") or 0)
    lamp = "RED" if fail else ("YELLOW" if d.get("skip") or d.get("not_run") or d.get("interrupted") else "GREEN")
    return lamp, f"{d.get('done', len(rows))}/{d.get('total', len(rows))} 站 · OK {d.get('ok', 0)} · FAIL {d.get('fail', 0)} · SKIP {d.get('skip', 0)} · 逾時 {d.get('timeout', 0)}", probs


def read_handoff(d: dict) -> tuple:
    s = d.get("summary") or {}
    probs = [{"where": "交接", "item": f.get("code") or f.get("id") or "finding", "lamp": "RED", "detail": f.get("message") or json.dumps(f, ensure_ascii=False)[:200], "next": "via-vcgc handoff check"}
             for f in d.get("findings") or [] if isinstance(f, dict)]
    lamp = "RED" if s.get("findings") else "GREEN"
    close = _lamp(d.get("closeout_lamp"))
    if close != "GREEN":
        probs.append({"where": "交接", "item": "closeout_lamp", "lamp": close, "detail": f"驗收燈 {d.get('closeout_lamp')}(交接綠只代表資料完整,不是驗收)", "next": "sdd closeout"})
    return lamp, f"需求 {s.get('requirements', '?')} · 待辦 {s.get('pending', '?')} · 收據可沿用 {s.get('reusable', '?')} · findings {s.get('findings', '?')} · 驗收燈 {d.get('closeout_lamp', '?')}", probs


READERS = {"vcgc-test": read_test, "ssot-panorama": read_panorama, "path-verify": read_path, "selftest-grid": read_grid, "handoff": read_handoff}


def report_path(via: Path, step: dict) -> Path | None:
    rel = step["report"]
    if "*" in rel:
        hits = sorted((via / rel).parent.glob(Path(rel).name))
        return hits[-1] if hits else None
    return via / rel


BRIDGE_RX = re.compile(r"\[橋掃\]\s+(ACCEL|NET|PS-ACCEL)\s+root=(\S.*?)\s·\s掃\s(\d+)\s·\s已掛\s(\d+)\s·\s缺\s(\d+)")
LOADED_RX = re.compile(r"\[加速\]\s+(引擎|網路)\s+(\S+?\.py)")


def newest_anywhere(via: Path, pattern: str) -> str:
    hits = [p for p in via.rglob(pattern) if p.is_file() and _vnum(p) >= 0 and "SCOPE_COPY" not in p.parts and ".git" not in p.parts]
    return max(hits, key=_vnum).name if hits else ""


def bridges_report(via: Path, out1: str, out2: str) -> dict:
    """Coverage lines of the sweeper (dry run) + which accelerator / net tool the bridges actually load vs the newest on disk."""
    rows, plans = [], []
    for text in (out1, out2):
        for m in BRIDGE_RX.finditer(text):
            rows.append({"kind": m.group(1), "root": m.group(2).strip(), "scanned": int(m.group(3)), "hooked": int(m.group(4)), "missing": int(m.group(5))})
        plans += [ln.strip()[4:].strip() for ln in text.splitlines() if ln.strip().startswith("PLAN")]
    loaded = {}
    for m in LOADED_RX.finditer(out1 + "\n" + out2):
        loaded.setdefault(m.group(1), m.group(2))
    latest = {"引擎": newest_anywhere(via, "VeritasCeleritas_v*.py"), "網路": newest_anywhere(via, "VeritasAegisNexus_v*.py")}
    return {"rows": rows, "plans": plans, "loaded": loaded, "latest": latest, "at": now_utc()}


def read_bridges(d: dict) -> tuple:
    probs = [{"where": r["root"], "item": f"{r['kind']} 缺 {r['missing']}", "lamp": "RED", "detail": f"掃 {r['scanned']} · 已掛 {r['hooked']} · 缺 {r['missing']}",
              "next": "via-bridge-sweep " + ("--ps --ps-tail" if r["kind"] == "PS-ACCEL" else "--subsystems") + " --apply(補缺;橋是零行為變更的標準插入)"}
             for r in d.get("rows") or [] if r["missing"]]
    probs += [{"where": "補缺計畫", "item": p.split(" · ")[0], "lamp": "RED", "detail": p, "next": "同上 --apply"} for p in (d.get("plans") or [])[:80]]
    for k, want in (d.get("latest") or {}).items():
        got = (d.get("loaded") or {}).get(k, "")
        if not want or not got:
            probs.append({"where": "最新版", "item": k, "lamp": "YELLOW", "detail": f"量不到(載入 {got or '?'} · 樹上最新 {want or '?'})", "next": "via-vcgc status"})
        elif got != want:
            probs.append({"where": "最新版", "item": k, "lamp": "RED", "detail": f"載入 {got} ≠ 樹上最新 {want}", "next": "換版經 SUP_MDL737 / SUP_MDL740 尾版"})
    kinds = {}
    for r in d.get("rows") or []:
        a = kinds.setdefault(r["kind"], [0, 0])
        a[0] += r["hooked"] + r["missing"]
        a[1] += r["missing"]
    summ = " · ".join(f"{k} {n - m}/{n}" for k, (n, m) in kinds.items()) or "沒有覆蓋行"
    summ += " · 載入 " + " / ".join(f"{k} {v}" for k, v in (d.get("loaded") or {}).items())
    lamp = "RED" if any(p["lamp"] == "RED" for p in probs) else ("YELLOW" if probs or not d.get("rows") else "GREEN")
    return lamp, summ, probs


READERS_EXTRA = {"bridges": read_bridges}


def run_step(via: Path, step: dict, full: bool, grid: bool, runner) -> dict:
    t0, at = time.time(), now_utc()
    if step["id"] == "bridges":
        rc1, out1 = runner(via, step["argv"], step["timeout"])
        rc2, out2 = runner(via, step["argv2"], step["timeout"])
        rp = via / step["report"]
        rp.parent.mkdir(parents=True, exist_ok=True)
        rp.write_text(json.dumps(bridges_report(via, out1, out2), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        rc = rc1 or rc2
        return _finish(via, step, t0, at, rc, (out1 + out2), False)
    evidence_only = step.get("evidence_unless") == "grid" and not grid
    rc, out = (0, "沿用最新格子存證(整張重跑加 --grid / -Grid)") if evidence_only else runner(via, step["argv"] + (step["full"] if full else []), step["timeout"])
    return _finish(via, step, t0, at, rc, out, evidence_only)


def _finish(via: Path, step: dict, t0: float, at: str, rc: int, out: str, evidence_only: bool) -> dict:
    secs = round(time.time() - t0, 1)
    rp = report_path(via, step)
    d = _json(rp) if rp else None
    owner = newest(via / "supportive modules" / "registry", step["owner"] + "_v*.py")
    row = {"n": step["n"], "id": step["id"], "name": step["name"], "layer": step["layer"], "at": at, "secs": secs, "rc": rc,
           "owner": owner.name if owner else "", "version": ("v%04d" % _vnum(owner)) if owner else "", "sha16": sha16(owner) if owner else "",
           "report": str(rp.relative_to(via)) if rp and rp.is_file() else "", "evidence_only": evidence_only, "tail": (out or "").strip().splitlines()[-1:] }
    fresh = rp is not None and rp.is_file() and (evidence_only or rp.stat().st_mtime >= t0 - 1)
    if d is None or not fresh:
        why = "報告不在" if d is None else "這輪報告沒更新(不拿舊的冒充)"
        row.update(lamp="RED", summary=f"{why} · rc {rc}", problems=[{"where": step["layer"], "item": step["id"], "lamp": "RED", "detail": why + " · " + " ".join(row["tail"]), "next": "單跑 via-vcgc " + " ".join(step["argv"])}])
        return row
    try:
        lamp, summ, probs = {**READERS, **READERS_EXTRA}[step["id"]](d)
    except Exception as exc:  # 讀不動照實紅,不中斷後面的段
        lamp, summ, probs = "RED", f"報告讀不動 {type(exc).__name__}", [{"where": step["layer"], "item": step["id"], "lamp": "RED", "detail": str(exc)[:200], "next": ""}]
    if evidence_only:
        ts = d.get("ts") or datetime.fromtimestamp(rp.stat().st_mtime).strftime("%Y%m%d_%H%M%S")
        age_h = round((time.time() - rp.stat().st_mtime) / 3600, 1)
        summ = f"存證 {ts}(距今 {age_h} 小時,本輪沒重跑)· " + summ
        if lamp == "GREEN" and age_h > 24:
            lamp = "YELLOW"
    elif rc not in (0, 2) and lamp == "GREEN":
        lamp = "RED"  # rc 說壞了,報告卻綠 = 不一致,照紅
    row.update(lamp=lamp, summary=summ, problems=probs)
    return row


def verdict(rows: list) -> str:
    lamps = [r["lamp"] for r in rows]
    return "RED" if "RED" in lamps else ("YELLOW" if "YELLOW" in lamps or "NODATA" in lamps else "GREEN")


def run(via: Path = VIA, full: bool = False, grid: bool = False, only: set | None = None, record: bool = True, write: bool = True,
        runner=console_runner, kit=None) -> dict:
    via = Path(via)
    run_id = f"fullcheck-{datetime.now(timezone.utc):%Y%m%d-%H%M%S}-{os.getpid()}"
    t0, rows = time.time(), []
    for step in STEPS:
        if only and step["n"] not in only:
            continue
        print(f"  [進度] {step['n']}/{len(STEPS)} {step['name']} …", flush=True)
        row = run_step(via, step, full, grid, runner)
        print(f"        {row['lamp']:<6} {row['secs']:>7.1f}s · {row['summary']}", flush=True)
        rows.append(row)
    rep = {"schema": "VIA.VCGC.FullCheck.v1", "engine": ENGINE, "run": run_id, "at": now_utc(), "head": _head(via), "mode": "full" if full else "reuse",
           "grid": "rerun" if grid else "evidence", "secs": round(time.time() - t0, 1), "verdict": verdict(rows), "steps": rows,
           "problems": sorted([dict(p, step=r["n"]) for r in rows for p in r["problems"]], key=lambda p: (ORDER.get(p["lamp"], 9), p["step"]))}
    if write:
        out = via / "VIA_Reports" / "fullcheck"
        out.mkdir(parents=True, exist_ok=True)
        body = json.dumps(rep, ensure_ascii=False, indent=1)
        (out / "FULLCHECK_latest.json").write_text(body + "\n", encoding="utf-8")
        (out / f"FULLCHECK_{run_id[10:25]}.json").write_text(body + "\n", encoding="utf-8")
        (out / "FULLCHECK_latest.html").write_text(page(rep, kit if kit is not None else _kit(via)), encoding="utf-8")
        rep["page"] = str((out / "FULLCHECK_latest.html").relative_to(via))
    if record:
        rep["ledger"] = append_ledger(via / "supportive modules" / "registry" / LEDGER_NAME, rep)
    return rep


def append_ledger(path: Path, rep: dict) -> int:
    """Only-add: one line per step and one verdict line (UTC with offset · owner tail · version · sha16 · seconds · HEAD)."""
    lines = [{"ts": s["at"], "run": rep["run"], "event": "step", "step": s["n"], "id": s["id"], "owner": s["owner"], "version": s["version"],
              "sha16": s["sha16"], "rc": s["rc"], "lamp": s["lamp"], "secs": s["secs"], "evidence_only": s["evidence_only"],
              "summary": s["summary"], "head": rep["head"], "by": ENGINE} for s in rep["steps"]]
    lines.append({"ts": rep["at"], "run": rep["run"], "event": "verdict", "lamp": rep["verdict"], "secs": rep["secs"], "mode": rep["mode"],
                  "grid": rep["grid"], "problems": len(rep["problems"]), "head": rep["head"], "by": ENGINE})
    with Path(path).open("a", encoding="utf-8") as fh:
        for ln in lines:
            fh.write(json.dumps(ln, ensure_ascii=False) + "\n")
    return len(lines)


# ---------------------------------------------------------------- page (same kit as the path-verify page)
def _kit(via: Path):
    p = newest(via / "supportive modules" / "registry", "CGC_MDL241_TemplateAdapter_v*.py")
    if p is None:
        return None
    try:
        spec = importlib.util.spec_from_file_location("CGC_MDL241_for_fullcheck", p)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    except Exception:
        return None


def page(rep: dict, kit) -> str:
    e = _html.escape

    def lamp(state, text=""):
        if kit is not None:
            return kit.lamp(KIT_LAMP.get(state, "NODATA"), text or state)
        color = {"GREEN": "#1a7f37", "YELLOW": "#b58100", "RED": "#c62828"}.get(state, "#777")
        return f"<span style='display:inline-block;width:.8em;height:.8em;border-radius:50%;background:{color};margin-right:.4em'></span>{e(text or state)}"

    st = "".join(f"<tr><td>{lamp(r['lamp'])}</td><td>{r['n']}</td><td>{e(r['name'])}</td><td>{e(r['layer'])}</td><td>{e(r['owner'])}</td>"
                 f"<td style='text-align:right'>{r['secs']:.1f}</td><td>{r['rc']}</td><td>{e(r['summary'])}</td></tr>" for r in rep["steps"])
    pr = "".join(f"<tr><td>{lamp(p['lamp'])}</td><td>{p['step']}</td><td>{e(str(p.get('where') or ''))}</td><td>{e(str(p.get('item') or ''))}</td>"
                 f"<td>{e(str(p.get('detail') or '')[:400])}</td><td>{e(str(p.get('next') or '')[:200])}</td></tr>" for p in rep["problems"])
    vr = "".join(f"<tr><td>{e(r['owner'])}</td><td>{e(r['version'])}</td><td><code>{e(r['sha16'])}</code></td><td>{e(r['at'])}</td>"
                 f"<td style='text-align:right'>{r['secs']:.1f}</td><td>{e(r['report'])}</td></tr>" for r in rep["steps"])
    n = {k: sum(1 for p in rep["problems"] if p["lamp"] == k) for k in ("RED", "YELLOW")}
    links = [("VCGC 串測頁", "../vcgc/VIA_Test_Matrix_v0101.html"), ("SSOT 全景頁", "../ssot_panorama/SSOT_PANORAMA_latest.html"),
             ("單一路徑驗證頁", "../path_verify/PATH_VERIFY_latest.html"), ("本輪 JSON", "FULLCHECK_latest.json")]
    side = (f"<div class='via-card'>{lamp(rep['verdict'], '總判 ' + rep['verdict'])}</div>"
            f"<div class='via-note'>{e(rep['at'])}</div><div class='via-note'>全程 {rep['secs']:.1f} 秒 · HEAD {e(rep['head'])}</div>"
            f"<div class='via-note'>{len(rep['steps'])} 段 · 問題 紅 {n['RED']} · 黃 {n['YELLOW']}</div>"
            f"<div class='via-note'>模式 {e(rep['mode'])} · 格子 {e(rep['grid'])}</div>"
            + "".join(f"<div><a href='{e(h)}' target='_blank'>{e(t)}</a></div>" for t, h in links))
    body = (f"<h3>① 六段依序結果(⓪ 三橋 → VCGC → VDF → VRN → SUP;紅了照跑下一段)</h3><table class='via'><tr><th>燈</th><th>#</th><th>段</th><th>層</th>"
            f"<th>正主(尾版)</th><th>秒</th><th>rc</th><th>摘要</th></tr>{st}</table>"
            f"<h3>② 問題清單(紅在前 · 不遺漏:每段非綠逐條)</h3><table class='via'><tr><th>燈</th><th>段</th><th>在哪</th><th>項</th><th>現象</th><th>下一步</th></tr>"
            f"{pr or '<tr><td colspan=6>沒有非綠項</td></tr>'}</table>"
            f"<h3>③ 版本與耗時(本輪實際執行的正主尾版)</h3><table class='via'><tr><th>正主</th><th>版號</th><th>sha16</th><th>開始(UTC)</th><th>秒</th><th>報告</th></tr>{vr}</table>"
            f"<div class='via-note'>燈讀各正主本輪剛寫的報告,不重判;這輪沒更新的報告照紅。黃 = 缺料 / 閘未開 / 待裁定,紅 = 壞掉或對不上。"
            f"紀錄只增寫 registry/{LEDGER_NAME}。</div>")
    title = "整合全景實測 · VCGC → VDF → VRN → SUP"
    if kit is not None:
        return kit.page(title, body, side, module={"id": "vcgc-fullcheck", "name": "整合全景實測"})
    return (f"<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><title>{e(title)}</title></head><body>"
            f"<h2>{e(title)}</h2>{side}{body}</body></html>")


# ---------------------------------------------------------------- CLI
def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        return selftest()
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
        return 2
    only = None
    if "--only" in args and args.index("--only") + 1 < len(args):
        only = {int(x) for x in re.findall(r"\d+", args[args.index("--only") + 1])}
    rep = run(full="--full" in args, grid="--grid" in args, only=only, record="--no-record" not in args)
    print(f"[整合全景實測] {rep['verdict']} · {len(rep['steps'])} 段 · 問題 紅 {sum(p['lamp'] == 'RED' for p in rep['problems'])} · "
          f"黃 {sum(p['lamp'] == 'YELLOW' for p in rep['problems'])} · {rep['secs']:.1f}s · 紀錄 +{rep.get('ledger', 0)} 行")
    print(f"  頁 VIA_Reports/fullcheck/FULLCHECK_latest.html · 紀錄冊 registry/{LEDGER_NAME}")
    return {"GREEN": 0, "YELLOW": 2, "RED": 1}[rep["verdict"]]


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    with tempfile.TemporaryDirectory() as tmp:
        via = Path(tmp)
        (via / "supportive modules" / "registry").mkdir(parents=True)
        for f in ("CGC_MDL124_BridgeSweeper_v0108.py", "CGC_MDL224_TestAuto_v0102.py", "CGC_MDL247_SSOTPanorama_v0100.py", "CGC_MDL242_PathVerify_v0102.py", "CGC_MDL064_SelftestGrid_v0504.py",
                  "CGC_MDL140_HandoverConsole_v0102.py"):
            (via / "supportive modules" / "registry" / f).write_text("# stub\n", encoding="utf-8")
        (via / "supportive modules" / "VeritasCeleritas_v1141.py").write_text("#\n", encoding="utf-8")
        (via / "supportive modules" / "VeritasAegisNexus_v1652.py").write_text("#\n", encoding="utf-8")
        grid_dir = via / "VIA_Reports" / "selftest_runs"
        grid_dir.mkdir(parents=True)
        (grid_dir / "GRID_20260929_004242.json").write_text(json.dumps({"ts": "20260929_004242", "done": 3, "total": 3, "ok": 2, "fail": 1, "skip": 0,
            "results": [{"name": "a", "state": "OK"}, {"name": "b", "state": "FAIL", "note": "boom"}, {"name": "c", "state": "OK"}]}), encoding="utf-8")
        calls = []

        def fake(v, argv, timeout):
            calls.append(argv)
            if "CGC_MDL124_BridgeSweeper" in argv:
                head = "  [加速] 引擎 VeritasCeleritas_v1141.py · 由 SUP_MDL737 載入\n  [加速] 網路 VeritasAegisNexus_v1652.py · 由 SUP_MDL740 載入\n"
                if "--ps" in argv:
                    return 0, head + "[橋掃] PS-ACCEL root=. · 掃 10 · 已掛 8 · 缺 1 · 版史 1 · 計畫 1(dry-run)\n    PLAN     Invoke-X-v0101.ps1 · 插入於第 4 行\n"
                return 0, head + "[橋掃] ACCEL root=functional modules/VDF · 掃 5 · 已掛 5 · 缺 0 · 排除 0\n[橋掃] NET   root=functional modules/VDF · 掃 5 · 已掛 5 · 缺 0\n"
            if argv[:1] == ["test"]:
                raise_it = False
                p = v / "VIA_Reports" / "vcgc"
                p.mkdir(parents=True, exist_ok=True)
                (p / "TEST_latest.json").write_text(json.dumps({"lamp": "YELLOW", "mode": "full" if "--full" in argv else "reuse",
                    "counts": {"GREEN": 2, "YELLOW": 1, "RED": 0}, "rows": [{"id": "V-x", "lamp": "YELLOW", "name": "x", "last": "yy"}]}), encoding="utf-8")
                return (2, "ok") if not raise_it else (1, "")
            if argv[:1] == ["ssot"]:
                return 1, "Traceback: crashed before writing"  # 不寫報告 → 本段紅,但後面照跑
            if argv[:2] == ["run", "--family"] and "CGC_MDL242_PathVerify" in argv:
                p = v / "VIA_Reports" / "path_verify"
                p.mkdir(parents=True, exist_ok=True)
                (p / "PATH_VERIFY_latest.json").write_text(json.dumps({"verdict": "GREEN", "steps": [{"step": "s", "state": "GREEN"}], "versions": []}), encoding="utf-8")
                return 0, ""
            if argv[:1] == ["handoff"]:
                p = v / "docs" / "handoff"
                p.mkdir(parents=True, exist_ok=True)
                (p / "HANDOFF_latest.json").write_text(json.dumps({"summary": {"findings": 0, "pending": 27}, "closeout_lamp": "YELLOW"}), encoding="utf-8")
                return 0, ""
            return 0, ""

        rep = run(via, full=True, runner=fake, kit=None)
        ids = [s["id"] for s in rep["steps"]]
        lamps = {s["id"]: s["lamp"] for s in rep["steps"]}
        chk("① 六段依序全跑:全景壞掉(沒寫報告)照跑後面各段", ids == [s["id"] for s in STEPS] and len(calls) == 6, ids)
        chk("② 燈讀正主報告:三橋缺 1 = 紅 · 串測黃 · 全景沒報告 = 紅(不冒充)· 路徑綠 · 格子存證有 FAIL = 紅 · 交接綠",
            lamps == {"bridges": "RED", "vcgc-test": "YELLOW", "ssot-panorama": "RED", "path-verify": "GREEN", "selftest-grid": "RED", "handoff": "GREEN"}, lamps)
        chk("③ --full 帶給會重量的段;格子沒 --grid 只讀存證、不呼叫格子", ["test", "--full"] in calls and ["ssot", "panorama", "--full"] in calls
            and not any("CGC_MDL064_SelftestGrid" in a for a in calls) and rep["steps"][4]["evidence_only"] and "存證" in rep["steps"][4]["summary"])
        probs = rep["problems"]
        chk("④ 問題清單不遺漏且紅在前:全景 · 格子 b 紅,串測 V-x · 驗收燈黃", [p["lamp"] for p in probs][:2] == ["RED", "RED"]
            and {p["item"] for p in probs} >= {"ssot-panorama", "b", "V-x", "closeout_lamp"}, len(probs))
        html_text = (via / "VIA_Reports" / "fullcheck" / "FULLCHECK_latest.html").read_text(encoding="utf-8")
        led = via / "supportive modules" / "registry" / LEDGER_NAME
        first = led.read_bytes()
        rows = [json.loads(x) for x in first.decode("utf-8").splitlines()]
        rep2 = run(via, runner=fake, kit=None, only={5})
        grown = led.read_bytes()
        chk("⑤ 紀錄冊只增:每段一行 + 總判一行 · UTC 帶時區 · 正主尾版 · 版號 · sha16 · 秒數;再跑只往後加",
            len(rows) == 7 and all(r["ts"].endswith("+00:00") for r in rows) and rows[1]["owner"] == "CGC_MDL224_TestAuto_v0102.py"
            and rows[1]["version"] == "v0102" and len(rows[1]["sha16"]) == 16 and "secs" in rows[0] and rows[-1]["event"] == "verdict"
            and grown.startswith(first) and len(rep2["steps"]) == 1, len(rows))
        chk("⑥ 頁:六段 · 問題清單 · 版本與耗時三張表都在;總判寫進側欄", all(s["name"][:10] in html_text for s in STEPS)
            and "問題清單" in html_text and "版本與耗時" in html_text and "總判 RED" in html_text)
        d0 = {"rows": [{"kind": "ACCEL", "root": "r", "scanned": 3, "hooked": 3, "missing": 0}, {"kind": "NET", "root": "r", "scanned": 3, "hooked": 3, "missing": 0}],
              "plans": [], "loaded": {"引擎": "VeritasCeleritas_v1141.py", "網路": "VeritasAegisNexus_v1652.py"},
              "latest": {"引擎": "VeritasCeleritas_v1141.py", "網路": "VeritasAegisNexus_v1652.py"}}
        g0 = read_bridges(d0)[0]
        stale = read_bridges(dict(d0, loaded={"引擎": "VeritasCeleritas_v1140.py", "網路": "VeritasAegisNexus_v1652.py"}))
        bplan = [p for p in rep["problems"] if p["step"] == 0]
        chk("⑦ 三橋:全接且載入最新 = 綠 · 載入舊版 = 紅(點名)· 缺橋 = 紅並列出補缺計畫那一支", g0 == "GREEN" and stale[0] == "RED"
            and any("v1140" in p["detail"] for p in stale[2]) and any(p["item"].startswith("Invoke-X-v0101.ps1") for p in bplan), [p["item"] for p in bplan])
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = main([]) == 2
    os.environ["VIA_FROM_VCGC"] = "YES"
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 只收 VCGC · 加速器橋在 · 不碰 TA-Lib · 呈現套件在樹上可載", denied and "VIA:ACCEL-BRIDGE" in src
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M) and _kit(VIA) is not None)
    print(f"  {ENGINE} selftest {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
