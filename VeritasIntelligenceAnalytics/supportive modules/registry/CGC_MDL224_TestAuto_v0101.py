#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL224_TestAuto v0101 — 薄尾:VCGC 全功能串測(盤點冊驅動 · 不遺漏 · 沿用 · 版本與時間紀錄)

操作員(側線 2026-09-30 b):「VCGC 所有功能盤點 … 用一個 PS 檔案串聯測試啟動一切不遺漏 且 AI 進入系統也會跑這流程
後面生成的指令也會跑這個流程 任何更新留紀錄版本及時間 範圍不發散完成 VCGC」。
v0100 只硬寫 9 支自測(逾時 90 秒)。本版:
  ① 站表的正本是 VIA_VCGC_FunctionInventory_SSOT 尾版(動詞 · 席位 · 必用卡 · 交接案 · 工作流步 · PS 入口 · 舊 9 套自測)。
  ② 自動盤點(不靠記):VCGC 各版 main 比對的動詞(AST)· CGC 家族尾版 · 席位冊 · 必用卡 · 交接案 · VCGC 工作流步;
     冊上沒登的 = 新(黃,照預設測法照跑:所在尾版的 --selftest),冊上有、樹上沒有 = 缺(紅)。
  ③ 全部 CGC 家族尾版在記憶體內 compile(不寫 .pyc)+ 加速器橋標記(L103 ①);帳上沒有或 sha 變了的尾版 = 更新 → 跑它的 --selftest。
  ④ 紀錄:每個盤點項(尾版檔 · 冊 · PS 入口 · 動詞)的版本 · sha16 · UTC 時間寫進 VIA_VCGC_FunctionLedger_v0100.jsonl(只增;
     第一次寫 baseline,之後只寫 added / changed / removed,帶本輪測試燈)。sha 先把 CRLF 換成 LF(工作站 autocrlf 不假變更)。
  ⑤ 沿用:站的相依檔指紋沒變、上次綠、24 小時內 → 沿用(--full 一律重跑)。--quick 只跑冊上標 quick 的站(AI 進場)。
  ⑥ 報告寫 VIA_Reports/vcgc(不入 git);結尾一行總判;rc 0 綠 · 2 黃 · 1 紅。遞迴防護:串測中再叫 test 直接略過。
只收 VCGC 呼叫;不抓網路、不 push、不寫庫;站一律經 VCGC 主控台跑(閘 · 事件 · 教訓照舊)。
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

import ast
import hashlib
import html
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
VIA = HERE.parents[1]
ENGINE = Path(__file__).stem
_STEM = "CGC_MDL224_TestAuto"


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + ENGINE, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)

INVENTORY_GLOB = "VIA_VCGC_FunctionInventory_SSOT_v*.json"
LEDGER_NAME = "VIA_VCGC_FunctionLedger_v0100.jsonl"
CONSOLE_GLOB = "CGC_MDL149_VeritasCentralGovernanceConsole_v*.py"
REPORTS = VIA / "VIA_Reports" / "vcgc"
ACTIVE = "VIA_VCGC_TEST_ACTIVE"
LAMPS = ("GREEN", "YELLOW", "RED")
TAIL_RX = re.compile(r"^(?P<fam>(?:CGC_MDL\d+_\w+?|CGC_SystemManager))_v(?P<v>\d{4})\.py$")


def __getattr__(name: str):
    return getattr(PRIOR, name)


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")


def newest(folder: Path, pattern: str) -> Path | None:
    hits = [p for p in folder.glob(pattern) if p.is_file() and _vnum(p) >= 0]
    return max(hits, key=_vnum) if hits else None


def sha16(path: Path) -> str:
    """Content hash with CRLF folded to LF: a Windows checkout (autocrlf) is not a change."""
    try:
        data = Path(path).read_bytes()
    except OSError:
        return ""
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()[:16]


def _read_json(path: Path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _git_head(via: Path) -> str:
    try:
        r = subprocess.run(["git", "-C", str(via), "rev-parse", "--short=12", "HEAD"], capture_output=True, text=True, timeout=30)
        return r.stdout.strip() if r.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


# ---------------------------------------------------------------- ② discovery (from the primary sources, not from memory)
def _lit(node) -> list:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        return [v for e in node.elts for v in _lit(e)]
    return []


_VERB_EXPR = re.compile(r"(args|argv)\[0\]|(args|argv)\[:1\]|verb")
_VERB_OK = re.compile(r"[a-z][a-z0-9\-]{1,24}")


def verbs_in(source: str) -> set:
    """String literals a console version compares its first argument against (args[0] == 'x', args[:1] == ['x'], verb in VERBS)."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set()
    named = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name) and "VERB" in n.targets[0].id:
            named[n.targets[0].id] = _lit(n.value)
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Compare) and _VERB_EXPR.fullmatch(ast.unparse(n.left)):
            for c in n.comparators:
                vals = named.get(c.id, []) if isinstance(c, ast.Name) else _lit(c)
                if isinstance(c, ast.List) and c.elts:
                    vals = _lit(c.elts[0])
                out.update(v for v in vals if _VERB_OK.fullmatch(v))
    return out


def discover_verbs(reg: Path) -> dict:
    found = {}
    for p in sorted(reg.glob(CONSOLE_GLOB), key=_vnum):
        if _vnum(p) < 0:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue
        for v in verbs_in(text):
            found.setdefault(v, p.name)
    return found


def discover_families(reg: Path) -> dict:
    fam = {}
    for p in reg.glob("*.py"):
        m = TAIL_RX.match(p.name)
        if m and (m.group("fam") not in fam or _vnum(p) > _vnum(fam[m.group("fam")])):
            fam[m.group("fam")] = p
    return fam


def discover(via: Path = VIA) -> dict:
    reg = via / "supportive modules" / "registry"
    seat = (_read_json(reg / "VIA_VCGC_SubsystemSeat_v0100.json", {}) or {}).get("tails") or {}
    card = _read_json(reg / "VIA_AI_FunctionCard_SSOT_v0100.json", {}) or {}
    policy = _read_json(reg / "VIA_Handoff_Continuity_SSOT_v0100.json", {}) or {}
    wf_path = newest(reg, "VIA_Workflow_VCGC_SSOT_v*.json")
    steps = {}
    for w in ((_read_json(wf_path, {}) or {}).get("workflows") or []) if wf_path else []:
        for s in w.get("steps") or []:
            if s.get("code"):
                eng = s.get("engine") or s.get("owner") or ("item:" + s["item"] if s.get("item") else "")
                steps[s["code"]] = eng if isinstance(eng, str) else " ".join(map(str, eng))
    ps = newest(via, "Invoke-VIA-OperatorConsole-v*.ps1")
    return {
        "verb": discover_verbs(reg),
        "seat": dict(seat),
        "card": {s.get("id"): s.get("cmd", "") for s in card.get("must_use") or [] if s.get("id")},
        "case": {k: " ".join(v.get("argv") or []) for k, v in (policy.get("test_cases") or {}).items()},
        "workflow": steps,
        "ps": {"operator_console": ps.name if ps else ""},
        "family": {k: v.name for k, v in discover_families(reg).items()},
    }


def coverage(inv: dict, found: dict) -> list:
    """Every discovered function must be covered by a station or an exemption; the book must not name things that are gone."""
    rows = []
    for kind in ("verb", "seat", "card", "case", "workflow", "ps"):
        book = (inv.get("coverage") or {}).get(kind) or {}
        have = found.get(kind) or {}
        for key in sorted(set(book) | set(have)):
            entry = book.get(key)
            if key in have and entry is not None:
                state = "EXEMPT" if isinstance(entry, dict) and entry.get("exempt") else "COVERED"
            elif key in have:
                state = "NEW"
            else:
                state = "GONE"
            rows.append({"kind": kind, "id": key, "state": state,
                         "by": (entry.get("station") if isinstance(entry, dict) else entry) or "",
                         "why": entry.get("exempt", "") if isinstance(entry, dict) else "",
                         "where": have.get(key, "")})
    return rows


# ---------------------------------------------------------------- ③ every CGC tail: compile in memory + accelerator bridge
def compile_tail(path: Path) -> dict:
    try:
        src = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return {"ok": False, "why": type(exc).__name__, "bridge": False, "selftest": False}
    try:
        compile(src, str(path), "exec", dont_inherit=True)
        ok, why = True, ""
    except SyntaxError as exc:
        ok, why = False, f"SyntaxError L{exc.lineno}: {exc.msg}"
    return {"ok": ok, "why": why, "bridge": "VIA:ACCEL-BRIDGE" in src, "selftest": "--selftest" in src}


# ---------------------------------------------------------------- ④ ledger: version · sha16 · UTC time of every item, only-add
def items_now(via: Path, found: dict) -> dict:
    reg = via / "supportive modules" / "registry"
    out = {}
    for fam, name in (found.get("family") or {}).items():
        p = reg / name
        out["family:" + fam] = {"kind": "family", "file": name, "version": "v%04d" % _vnum(p), "sha16": sha16(p)}
    for pattern, key in ((INVENTORY_GLOB, "book:VIA_VCGC_FunctionInventory_SSOT"),
                         ("VIA_Workflow_VCGC_SSOT_v*.json", "book:VIA_Workflow_VCGC_SSOT")):
        p = newest(reg, pattern)
        if p:
            out[key] = {"kind": "book", "file": p.name, "version": "v%04d" % _vnum(p), "sha16": sha16(p)}
    for name in ("VIA_AI_FunctionCard_SSOT_v0100.json", "VIA_Handoff_Continuity_SSOT_v0100.json", "VIA_VCGC_SubsystemSeat_v0100.json"):
        p = reg / name
        if p.is_file():
            out["book:" + name[:-11]] = {"kind": "book", "file": name, "version": "v0100", "sha16": sha16(p)}
    ps = (found.get("ps") or {}).get("operator_console")
    if ps:
        out["ps:operator_console"] = {"kind": "ps", "file": ps, "version": "v%04d" % _vnum(ps), "sha16": sha16(via / ps)}
    for verb, where in (found.get("verb") or {}).items():
        out["verb:" + verb] = {"kind": "verb", "file": where, "version": "v%04d" % _vnum(where), "sha16": ""}
    return out


def ledger_state(path: Path) -> dict:
    state = {}
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except OSError:
        return state
    for line in lines:
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if row.get("event") == "removed":
            state.pop(row.get("id"), None)
        elif row.get("id"):
            state[row["id"]] = row
    return state


def changes(before: dict, now_items: dict) -> list:
    out = []
    for key, it in sorted(now_items.items()):
        old = before.get(key)
        if old is None:
            out.append(("added", key, it, None))
        elif (old.get("file"), old.get("sha16")) != (it["file"], it["sha16"]):
            out.append(("changed", key, it, {"file": old.get("file"), "sha16": old.get("sha16"), "ts": old.get("ts")}))
    for key in sorted(set(before) - set(now_items)):
        out.append(("removed", key, before[key], None))
    return out


def append_ledger(path: Path, rows: list) -> int:
    if not rows:
        return 0
    path = Path(path)
    tail = ""
    if path.is_file() and path.stat().st_size:
        with path.open("rb") as fh:
            fh.seek(-1, os.SEEK_END)
            tail = fh.read(1).decode("latin-1")
    with path.open("a", encoding="utf-8", newline="\n") as fh:
        if tail and tail != "\n":
            fh.write("\n")
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=False) + "\n")
    return len(rows)


# ---------------------------------------------------------------- ⑤ stations
def dep_files(via: Path, patterns: list) -> list:
    out = set()
    for pat in patterns or []:
        out.update(p for p in via.glob(pat) if p.is_file())
    return sorted(out)


def fingerprint(via: Path, station: dict, inventory_sha: str) -> str:
    h = hashlib.sha256((json.dumps(station, ensure_ascii=False, sort_keys=True) + inventory_sha).encode("utf-8"))
    pats = list(station.get("deps") or []) + ["supportive modules/registry/" + CONSOLE_GLOB]
    for p in dep_files(via, pats):
        h.update((p.relative_to(via).as_posix() + ":" + sha16(p)).encode("utf-8"))
    return h.hexdigest()[:16]


def find_pwsh() -> str | None:
    cand = os.environ.get("VIA_PWSH") or shutil.which("pwsh") or shutil.which("pwsh.exe")
    return cand if cand and Path(cand).exists() else None


def ps_check(via: Path, rel: str, must: list) -> dict:
    """The one PS entry: it must parse (pwsh Parser, when pwsh exists) and must still carry the chain step."""
    path = via / rel
    if not rel or not path.is_file():
        return {"lamp": "RED", "rc": 2, "last": "ABSENT " + (rel or "Invoke-VIA-OperatorConsole-v*.ps1")}
    text = path.read_text(encoding="utf-8", errors="replace")
    missing = [m for m in must if not re.search(m, text)]
    if missing:
        return {"lamp": "RED", "rc": 1, "last": "PS 入口少了串測步:" + " · ".join(missing)}
    pwsh = find_pwsh()
    if not pwsh:
        return {"lamp": "YELLOW", "rc": 2, "last": "沒有 pwsh:語法沒量(不冒充綠;設 VIA_PWSH 或裝 PowerShell 7)· 串測步在"}
    script = ("$e=$null;$t=$null;[void][System.Management.Automation.Language.Parser]::ParseFile("
              + "'" + str(path).replace("'", "''") + "',[ref]$t,[ref]$e);if($e.Count){$e|%{$_.Message};exit 1};exit 0")
    try:
        r = subprocess.run([pwsh, "-NoProfile", "-NonInteractive", "-Command", script], capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.SubprocessError) as exc:
        return {"lamp": "YELLOW", "rc": 2, "last": "pwsh 叫不起來:" + type(exc).__name__}
    if r.returncode != 0:
        return {"lamp": "RED", "rc": 1, "last": "PS 語法錯:" + (r.stdout.strip().splitlines() or ["?"])[0][:120]}
    return {"lamp": "GREEN", "rc": 0, "last": "PS 語法過(pwsh Parser)· 串測步在 · " + path.name}


def _tail_line(text: str) -> str:
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    return lines[-1][:160] if lines else ""


def run_console(via: Path, console: Path, argv: list, timeout: int, log: Path) -> tuple:
    env = os.environ.copy()
    env.update(VIA_FROM_VCGC="YES", VIA_VCGC_PUSH="NO", VIA_NO_OPEN="1", PYTHONIOENCODING="utf-8")
    env[ACTIVE] = "1"
    t0 = time.time()
    try:
        r = subprocess.run([sys.executable, str(console)] + list(argv), cwd=str(via), env=env,
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=timeout, stdin=subprocess.DEVNULL)
        rc, out = r.returncode, (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired as exc:
        rc, out = 124, ((exc.stdout or b"").decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")) + "\nTIMEOUT"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(out, encoding="utf-8")
    return rc, round(time.time() - t0, 1), out


def lamp_for(rc: int, station: dict, out: str) -> str:
    marker = station.get("marker")
    if rc == 0 and (not marker or marker in out):
        return "GREEN"
    if rc == 0 and marker:
        return "YELLOW"
    if rc in (station.get("yellow_rc") or []):
        return "YELLOW"
    return "RED"


# ---------------------------------------------------------------- run
def load_inventory(via: Path = VIA) -> tuple:
    reg = via / "supportive modules" / "registry"
    p = newest(reg, INVENTORY_GLOB)
    return (p, _read_json(p, None)) if p else (None, None)


def _summary(rows: list) -> dict:
    return {lamp: sum(1 for r in rows if r["lamp"] == lamp) for lamp in LAMPS}


def run(argv: list, via: Path = VIA) -> tuple:
    full, quick, record = "--full" in argv, "--quick" in argv, "--no-record" not in argv
    only = argv[argv.index("--only") + 1] if "--only" in argv and argv.index("--only") + 1 < len(argv) else None
    reg = via / "supportive modules" / "registry"
    reports = via / "VIA_Reports" / "vcgc"
    inv_path, inv = load_inventory(via)
    console = newest(reg, CONSOLE_GLOB)
    t_start = time.time()
    run_id = os.environ.get("VIA_HUB_RUN") or f"test-{datetime.now():%Y%m%d-%H%M%S}-{os.getpid()}"
    card = {"via": "vcgc", "door": ENGINE, "run": run_id, "at": now(), "head": _git_head(via), "mode": "full" if full else ("quick" if quick else "reuse"),
            "inventory": inv_path.name if inv_path else "", "console": console.name if console else "", "rows": [], "coverage": [], "families": {}}
    if inv is None or console is None:
        card.update(lamp="RED", why="盤點冊 VIA_VCGC_FunctionInventory_SSOT 或 VCGC 尾版不在")
        return card, 1
    found = discover(via)
    cov = coverage(inv, found)
    card["coverage"] = cov
    # ③ families: compile everything; updated tails (ledger) run their --selftest
    ledger = reg / LEDGER_NAME
    before = ledger_state(ledger)
    baseline = not before
    exempt = inv.get("selftest_exempt") or {}
    fam_rows, fam_updated = [], []
    for fam, name in sorted((found.get("family") or {}).items()):
        c = compile_tail(reg / name)
        old = before.get("family:" + fam)
        updated = (not baseline) and (old is None or old.get("sha16") != sha16(reg / name) or old.get("lamp") not in (None, "GREEN"))
        fam_rows.append({"family": fam, "file": name, **c, "updated": updated})
        if updated:
            fam_updated.append((fam, name, c))
    bad = [r for r in fam_rows if not r["ok"]]
    nobridge = [r["file"] for r in fam_rows if r["ok"] and not r["bridge"] and r["family"] not in (inv.get("bridge_exempt") or {})]
    card["families"] = {"n": len(fam_rows), "compile_fail": [r["file"] + " " + r["why"] for r in bad], "no_bridge": nobridge,
                        "updated": [n for _f, n, _c in fam_updated], "baseline": baseline}
    stations = [s for s in inv.get("stations") or [] if not s.get("disabled")]
    for fam, name, c in fam_updated:
        if fam in exempt or not c["ok"] or not c["selftest"]:
            continue
        stem = name[:-3]
        stations.append({"id": "upd:" + stem, "name": "更新尾版自測 " + stem, "argv": ["run", "--family", "core", fam, "--selftest"],
                         "deps": ["supportive modules/registry/" + name], "timeout": 600, "auto": "updated"})
    for row in cov:
        if row["state"] == "NEW" and row["kind"] == "verb":
            host = row["where"]
            stations.append({"id": "new-verb:" + row["id"], "name": "新動詞(未登錄)所在版自測 " + host,
                             "argv": ["run", "--family", "core", host[:-3].rsplit("_v", 1)[0], "--selftest"],
                             "deps": ["supportive modules/registry/" + host], "timeout": 900, "auto": "new-verb"})
    if quick:
        stations = [s for s in stations if s.get("quick") or s.get("auto")]
    if only:
        stations = [s for s in stations if s["id"] == only or s["id"].startswith(only)]
    state_path = reports / "TEST_STATE_v0101.json"
    state = _read_json(state_path, {}) or {}
    inv_sha = sha16(inv_path)
    for st in stations:
        fp = fingerprint(via, st, inv_sha)
        last = state.get(st["id"]) or {}
        fresh = last.get("fp") == fp and last.get("lamp") == "GREEN" and time.time() - float(last.get("t", 0)) < float(inv.get("reuse_hours", 24)) * 3600
        if fresh and not full:
            row = dict(last, reused=True)
        elif st.get("pending_until") and not (via / st["pending_until"]).is_file():
            row = {"id": st["id"], "name": st.get("name", st["id"]), "lamp": "YELLOW", "rc": 2, "secs": 0.0,
                   "last": "待辦:" + st["pending_until"] + " 還沒出(站已登錄;出了就照 must 驗)", "fp": fp, "t": time.time(), "at": now(), "reused": False}
        elif st.get("kind") == "ps":
            res = ps_check(via, found["ps"].get("operator_console", ""), st.get("must") or [])
            row = {"id": st["id"], "name": st.get("name", st["id"]), "lamp": res["lamp"], "rc": res["rc"], "secs": 0.0,
                   "last": res["last"], "fp": fp, "t": time.time(), "at": now(), "reused": False}
        else:
            log = reports / "test_logs" / (re.sub(r"[^A-Za-z0-9_.-]+", "_", st["id"]) + ".txt")
            rc, secs, out = run_console(via, console, st["argv"], int(st.get("timeout") or 300), log)
            lamp = lamp_for(rc, st, out)
            row = {"id": st["id"], "name": st.get("name", st["id"]), "lamp": lamp, "rc": rc, "secs": secs, "last": _tail_line(out),
                   "fp": fp, "t": time.time(), "at": now(), "reused": False, "log": log.relative_to(via).as_posix()}
        if st.get("auto"):
            row["auto"] = st["auto"]
        state[st["id"]] = {k: v for k, v in row.items() if k != "reused"}
        card["rows"].append(row)
        print(f"  [{row['lamp']:<6}] {st['id']:<34} rc {row['rc']:<3} {row.get('secs', 0):>6}s"
              f"{' 沿用' if row.get('reused') else ''} · {row.get('last', '')[:90]}")
        sys.stdout.flush()
    reports.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    # ④ ledger (versions and time of every item; the updated families carry their selftest lamp)
    lamps = {r["id"][4:]: r["lamp"] for r in card["rows"] if r["id"].startswith("upd:")}
    items = items_now(via, found)
    for key, it in items.items():
        if it["kind"] == "family":
            stem = it["file"][:-3]
            fam_row = next((r for r in fam_rows if r["file"] == it["file"]), {})
            it["lamp"] = lamps.get(stem) or ("RED" if fam_row and not fam_row.get("ok") else ("GREEN" if fam_row else None))
    rows = []
    stamp = now()
    for event, key, it, prev in ([("baseline", k, v, None) for k, v in sorted(items.items())] if baseline else changes(before, items)):
        row = {"ts": stamp, "event": event, "id": key, "kind": it.get("kind"), "file": it.get("file"), "version": it.get("version"),
               "sha16": it.get("sha16"), "lamp": it.get("lamp"), "run": run_id, "head": card["head"], "by": ENGINE}
        if prev:
            row["prev"] = prev
        rows.append({k: v for k, v in row.items() if v not in (None, "")})
    card["ledger"] = {"file": LEDGER_NAME, "appended": append_ledger(ledger, rows) if record else 0, "would": len(rows)}
    # verdict
    counts = _summary(card["rows"])
    new = [r for r in cov if r["state"] == "NEW"]
    gone = [r for r in cov if r["state"] == "GONE"]
    lamp = "RED" if counts["RED"] or bad or gone else ("YELLOW" if counts["YELLOW"] or new or nobridge else "GREEN")
    card.update(lamp=lamp, counts=counts, secs=round(time.time() - t_start, 1), new=[r["kind"] + ":" + r["id"] for r in new],
                gone=[r["kind"] + ":" + r["id"] for r in gone])
    (reports / "TEST_latest.json").write_text(json.dumps(card, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    write_page(card, reports / "VIA_Test_Matrix_v0101.html")
    return card, {"GREEN": 0, "YELLOW": 2, "RED": 1}[lamp]


def verdict_line(card: dict) -> str:
    c = card.get("counts") or {}
    cov = card.get("coverage") or []
    by = {}
    for r in cov:
        by.setdefault(r["kind"], [0, 0])
        by[r["kind"]][1] += 1
        by[r["kind"]][0] += r["state"] in ("COVERED", "EXEMPT")
    fam = card.get("families") or {}
    reused = sum(1 for r in card.get("rows") or [] if r.get("reused"))
    return (f"[VCGC 全功能串測] {card.get('lamp')} · 站 {len(card.get('rows') or [])}(綠 {c.get('GREEN', 0)} · 黃 {c.get('YELLOW', 0)}"
            f" · 紅 {c.get('RED', 0)} · 沿用 {reused})· 盤點 " + " · ".join(f"{k} {v[0]}/{v[1]}" for k, v in by.items())
            + f" · 家族尾版 {fam.get('n', 0)} 支 compile 錯 {len(fam.get('compile_fail') or [])} · 缺橋 {len(fam.get('no_bridge') or [])}"
            f" · 更新 {len(fam.get('updated') or [])} · 新 {len(card.get('new') or [])} · 缺 {len(card.get('gone') or [])}"
            f" · 紀錄 +{(card.get('ledger') or {}).get('appended', 0)} 行 · {card.get('secs', 0)}s")


def write_page(card: dict, page: Path) -> None:
    def tr(cells):
        return "<tr>" + "".join(f"<td>{html.escape(str(c))}</td>" for c in cells) + "</tr>"
    rows = "".join(tr([r["lamp"], r["id"], r.get("name", ""), r["rc"], r.get("secs", 0), "沿用" if r.get("reused") else "", r.get("last", "")])
                   for r in card.get("rows") or [])
    cov = "".join(tr([r["state"], r["kind"], r["id"], r.get("by", ""), r.get("why", ""), r.get("where", "")])
                  for r in card.get("coverage") or [] if r["state"] != "COVERED")
    text = ("<!doctype html><html lang=\"zh-Hant\"><meta charset=\"utf-8\"><title>VCGC 全功能串測</title><style>"
            "body{margin:0;background:#121614;color:#d5ddd6;font:12px/1.4 ui-sans-serif,sans-serif}main{max-width:1200px;margin:auto;padding:14px}"
            "table{border-collapse:collapse;width:100%;margin:8px 0 18px}th,td{border-bottom:1px solid #2c3832;padding:3px 6px;text-align:left;"
            "vertical-align:top;word-break:break-word}h1,h2{font-size:14px}</style><main>"
            f"<h1>{html.escape(verdict_line(card))}</h1><p>{html.escape(card.get('at', ''))} · {html.escape(card.get('head', ''))}"
            f" · {html.escape(card.get('inventory', ''))} · {html.escape(card.get('console', ''))}</p>"
            "<h2>站</h2><table><tr><th>燈</th><th>站</th><th>名</th><th>rc</th><th>秒</th><th></th><th>最後一行</th></tr>" + rows + "</table>"
            "<h2>盤點(非 COVERED)</h2><table><tr><th>狀態</th><th>類</th><th>項</th><th>站</th><th>豁免理由</th><th>出處</th></tr>" + cov + "</table>"
            "</main></html>")
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text(text, encoding="utf-8")


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        return selftest()
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
        return 2
    if os.environ.get(ACTIVE) == "1" and "--nested-ok" not in args:
        print("[VCGC 全功能串測] 已在串測中:不遞迴(外層那一輪就是本流程)")
        return 0
    if args[:1] == ["inventory"]:
        inv_path, inv = load_inventory()
        if inv is None:
            print("[VCGC 全功能盤點] RED · 盤點冊 VIA_VCGC_FunctionInventory_SSOT 不在")
            return 1
        cov = coverage(inv, discover())
        for r in cov:
            if r["state"] != "COVERED":
                print(f"  [{r['state']:<7}] {r['kind']:<8} {r['id']:<28} {r['by'] or r['why'] or r['where']}")
        bad = [r for r in cov if r["state"] in ("NEW", "GONE")]
        print(f"[VCGC 全功能盤點] {'GREEN' if not bad else 'YELLOW'} · {inv_path.name} · 項 {len(cov)} · 新 "
              f"{sum(r['state'] == 'NEW' for r in cov)} · 缺 {sum(r['state'] == 'GONE' for r in cov)} · 豁免 {sum(r['state'] == 'EXEMPT' for r in cov)}")
        return 0 if not bad else 2
    os.environ[ACTIVE] = "1"
    try:
        card, rc = run(args)
    finally:
        os.environ.pop(ACTIVE, None)
    if "--json" in args:
        print(json.dumps(card, ensure_ascii=False, indent=1))
    print(verdict_line(card))
    for key in ("compile_fail", "no_bridge"):
        for item in (card.get("families") or {}).get(key) or []:
            print(f"  [家族 {key}] {item}")
    for item in card.get("new") or []:
        print(f"  [新 · 未登錄盤點冊] {item} → 登進 VIA_VCGC_FunctionInventory_SSOT 新版號(測法或豁免理由)")
    for item in card.get("gone") or []:
        print(f"  [缺 · 冊上有樹上沒有] {item}")
    print(f"  報告 VIA_Reports/vcgc/TEST_latest.json · VIA_Test_Matrix_v0101.html · 紀錄冊 {LEDGER_NAME}")
    return rc


# ---------------------------------------------------------------- selftest
def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    src = "VERBS = ('go', 'all')\ndef main(args):\n    if args[:1] == ['alpha']: pass\n    if args[0] == 'beta': pass\n    if verb in VERBS: pass\n    if x == 'no': pass\n"
    chk("① 動詞從 AST 抽:args[:1] == ['x'] · args[0] == 'x' · verb in VERBS;無關比較不算", verbs_in(src) == {"alpha", "beta", "go", "all"}, sorted(verbs_in(src)))
    inv = {"coverage": {"verb": {"alpha": "st1", "gone": "st2", "go": {"exempt": "PS 本身"}}}}
    cov = {(r["id"], r["state"]) for r in coverage(inv, {"verb": {"alpha": "v1", "go": "v1", "beta": "v2"}})}
    chk("② 盤點:有站 COVERED · 豁免 EXEMPT · 樹上有冊上沒 NEW · 冊上有樹上沒 GONE",
        cov == {("alpha", "COVERED"), ("go", "EXEMPT"), ("beta", "NEW"), ("gone", "GONE")}, sorted(cov))
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        (t / "a.py").write_bytes(b"x = 1\r\n")
        (t / "b.py").write_bytes(b"x = 1\n")
        same = sha16(t / "a.py") == sha16(t / "b.py")
        (t / "bad.py").write_text("def f(:\n", encoding="utf-8")
        (t / "good.py").write_text("# [VIA:ACCEL-BRIDGE:v0100]\nimport sys\nif '--selftest' in sys.argv: pass\n", encoding="utf-8")
        cb, cg = compile_tail(t / "bad.py"), compile_tail(t / "good.py")
        led = t / "ledger.jsonl"
        n0 = append_ledger(led, [{"id": "family:A", "event": "baseline", "file": "A_v0100.py", "sha16": "1"},
                                 {"id": "family:B", "event": "baseline", "file": "B_v0100.py", "sha16": "2"}])
        st = ledger_state(led)
        ch = changes(st, {"family:A": {"kind": "family", "file": "A_v0101.py", "sha16": "3"},
                          "family:C": {"kind": "family", "file": "C_v0100.py", "sha16": "4"}})
        before_bytes = led.read_bytes()
        append_ledger(led, [{"id": "family:A", "event": "changed", "file": "A_v0101.py", "sha16": "3"}])
        grown = led.read_bytes()
        st2 = ledger_state(led)
    chk("③ sha16 把 CRLF 當 LF(工作站 autocrlf 不假變更)", same)
    chk("④ compile 在記憶體:語法錯抓到 · 橋標記與 --selftest 認得", not cb["ok"] and cg["ok"] and cg["bridge"] and cg["selftest"], cb["why"])
    chk("⑤ 紀錄冊只增:changed / added / removed 各一 · 舊行位元不動 · 折疊後取最新",
        n0 == 2 and sorted(e for e, *_ in ch) == ["added", "changed", "removed"] and grown.startswith(before_bytes)
        and st2["family:A"]["file"] == "A_v0101.py", [e + ":" + k for e, k, *_ in ch])
    st_a = {"id": "x", "argv": ["status"], "deps": []}
    chk("⑥ 燈:rc 0 綠 · 標記沒見到 黃 · yellow_rc 黃 · 其餘紅",
        lamp_for(0, st_a, "") == "GREEN" and lamp_for(0, {"marker": "OK"}, "no") == "YELLOW"
        and lamp_for(2, {"yellow_rc": [2]}, "") == "YELLOW" and lamp_for(1, {}, "") == "RED")
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = main([]) == 2
    os.environ["VIA_FROM_VCGC"] = "YES"
    os.environ[ACTIVE] = "1"
    try:
        nested = main([]) == 0
    finally:
        os.environ.pop(ACTIVE, None)
    chk("⑦ 只收 VCGC · 串測中再叫不遞迴", denied and nested)
    inv_path, inv_real = load_inventory()
    found = discover()
    cov_real = coverage(inv_real or {}, found)
    newgone = [r["kind"] + ":" + r["id"] for r in cov_real if r["state"] in ("NEW", "GONE")]
    chk("⑧ 實樹:盤點冊在 · 動詞 / 席位 / 必用卡 / 交接案 / 工作流步 / PS 入口全部有站或豁免(新 0 · 缺 0)",
        inv_path is not None and not newgone, (inv_path.name if inv_path else "ABSENT") + " · " + (" ".join(newgone[:6]) or "0"))
    ids = [s["id"] for s in (inv_real or {}).get("stations") or []]
    chk("⑨ 站號唯一 · PS 入口站守住「串測步在」· 快站存在(AI 進場用)",
        len(ids) == len(set(ids)) and any(s.get("kind") == "ps" and s.get("must") for s in (inv_real or {}).get("stations") or [])
        and any(s.get("quick") for s in (inv_real or {}).get("stations") or []), f"站 {len(ids)}")
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑩ 加速器橋在 · 不碰 TA-Lib · 前版 v0100 的 9 套自測還在盤點冊", "VIA:ACCEL-BRIDGE" in text
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M)
        and all(any(p.split("_v")[0] in " ".join(s.get("argv") or []) for s in (inv_real or {}).get("stations") or []) for _n, p in PRIOR.SUITES))
    print(f"  {ENGINE} selftest {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
