#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""CGC_MDL149_VeritasCentralGovernanceConsole v0168 — 薄尾:中樞自動同步 · 每個動作留事件 · 失敗進教訓帳 · 任何引擎都從中樞跑

操作員 R32:「AI will do any action, including reviewing and any changes through the process of VCGC; all of the action and feedback
through the hub will trigger auto synchronizing mechanism in all functions in VCGC, and logging function with lesson learned engine
should be generated. Please implement auto synchronizing checking testing mechanism in all VCGC engines.」
設計(一把尺,不逐支改 269 支引擎 —— L04 / L05):所有動作本來就經 VCGC 主控台(v0159 起每個動詞先過流程閘);本尾版在主控台外包一層:
  ① 事件:每個動詞(含新動詞 run)記一筆 {時間 · 動詞 · 參數 · 結束碼 · 秒數 · HEAD · 樹指紋前後 · 結果類},落 VIA_Reports/vcgc/events/(不入 git)。
     結果類:OK(rc 0)· FINDING(rc 2/3/4 = 誠實的缺料 / 缺件 / 閘未開)· FAIL(rc 1 或其他 · 例外)。
  ② 自動同步檢查:動作前後樹指紋不同(有檔變了)→ 立刻做 座位對齊(CGC_MDL222)+ 註冊同步乾跑(活元件盤點走 v0167 快取);
     有待同步只印一行提示 —— 寫入(registry-sync --apply)依 Master Prompt 仍要操作員明確批准,不自動寫。樹沒變 = 零成本跳過。
  ③ 教訓:FAIL 事件交給教訓帳本引擎尾版(CGC_MDL058 v0102 起 record_event):同一簽名第二次出現標「重複出錯」,只增。
  ④ 新動詞:run <引擎 stem 或檔> [參數…] —— 任何引擎都從中樞跑(找尾版 · 家族 python 走 EngineBus python_for · 子行程帶 VIA_FROM_VCGC=YES);
     同一 HEAD、15 分鐘內已過閘(唯一入口設的 VIA_GATE_PASSED_*)就不重跑閘。events [N] 看最近事件;sync-check 立刻做一次同步檢查。
  ⑤ 工作流一致性(Codex #364 P2:SSOT 要真的管到執行者):事件帶輪號(入口設的 VIA_HUB_RUN)與目標引擎 stem;
     workflow [輪號] 讀工作流 SSOT 尾版(VIA_Workflow_Hub_SSOT_v*)的 conformance / match,拿本輪事件核:
     第一筆是 H1 閘 · 中樞段 → 兩迴圈 → 出口段、段內照 id 首次出現不倒置 · 宣告步有沒有跑 → 紅 / 黃 / 綠(只讀)。
  VIA_VCGC_NOSYNC=1 關自動同步(事件照記)。其餘動詞原樣轉給前一版。只收 VCGC 呼叫(VIA_FROM_VCGC=YES)。
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

import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
_STEM = "CGC_MDL149_VeritasCentralGovernanceConsole"
EVENTS = VIA / "VIA_Reports" / "vcgc" / "events"
SYNC_STATE = VIA / "VIA_Reports" / "vcgc" / "cache" / "LAST_SYNC.json"
LAST: dict = {}
NO_SYNC_VERBS = {"registry-sync", "events", "--selftest", "selftest", "sync-check", "workflow"}
ROOTS = ("supportive modules/registry", "functional modules/VDF/engine", "functional modules/VDF", "functional modules/VRN",
         "functional modules/VRN/engine", "supportive modules", "supportive modules/network", "supportive modules/70_VRN_Rules")


def _vnum(path: Path) -> int:
    match = re.search(r"_v(\d+)$", path.stem)
    return int(match.group(1)) if match else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location("vcgc_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    return getattr(PRIOR, name)


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def _tail(stem: str) -> Path | None:
    p = Path(stem)
    if p.suffix == ".py" and (p.is_file() or (VIA / p).is_file()):
        return p if p.is_file() else VIA / p
    hits = []
    for r in ROOTS:
        hits += [q for q in (VIA / r).glob(stem + "_v*.py") if _vnum(q) >= 0]
        q = VIA / r / (stem + ".py")
        if q.is_file() and not hits:
            hits.append(q)
    return max(hits, key=_vnum) if hits else None


def _head() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=VIA, capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception:
        return ""


def outcome(rc) -> str:
    return "OK" if rc == 0 else ("FINDING" if rc in (2, 3, 4) else "FAIL")


def write_event(ev: dict, folder: Path = EVENTS) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    f = folder / f"EVENTS_{datetime.now():%Y%m%d}.jsonl"
    with f.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(ev, ensure_ascii=False, sort_keys=True) + "\n")
    return f


def sync_check(key: str | None = None) -> dict:
    """Seat alignment + registry-sync dry run. Cheap when the inventory cache hits; never writes the register."""
    out = {"key": key, "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    try:
        probes = sorted(HERE.glob("CGC_MDL222_SubsystemProbe_v*.py"), key=_vnum)       # seat probe tail (not a pinned name)
        seat = _load(probes[-1], "seat_for_v0168").check()
        out["seat"] = {"lock_success": seat.get("lock_success"), "missing": seat.get("missing")}
    except Exception as exc:
        out["seat"] = {"error": f"{type(exc).__name__}: {str(exc)[:120]}"}
    try:
        rs = None
        for m in list(sys.modules.values()):
            f = getattr(m, "__dict__", {}).get("registry_sync")
            if callable(f) and _STEM in str(getattr(m, "__file__", "")):
                rs = f
                break
        r = rs(False) if rs else {}
        out["registry"] = {"new": r.get("new"), "changed": r.get("changed"), "stale": r.get("stale"), "expected": r.get("expected")}
    except Exception as exc:
        out["registry"] = {"error": f"{type(exc).__name__}: {str(exc)[:120]}"}
    reg = out.get("registry") or {}
    out["pending"] = bool((reg.get("new") or 0) or (reg.get("changed") or 0) or (reg.get("stale") or 0))
    out["aligned"] = bool((out.get("seat") or {}).get("lock_success"))
    return out


def lesson_verb(ev: dict) -> str:
    """What failed, for the lesson signature: `run <engine stem>` or `<verb> <sub-verb>` (live R32: two different engines
    both read "run · rc=1" and would have been booked as one repeat)."""
    what = ev.get("target") if ev.get("verb") == "run" else next((a for a in ev.get("args") or [] if not str(a).startswith("-")), "")
    return f"{ev.get('verb')} {what or ''}".strip()


def _lessons(ev: dict) -> dict | None:
    hits = sorted(HERE.glob("CGC_MDL058_Lessons_v*.py"), key=_vnum)
    if not hits:
        return None
    try:
        m = _load(hits[-1], "lessons_for_v0168")
        return m.record_event(dict(ev, verb=lesson_verb(ev))) if hasattr(m, "record_event") else None
    except Exception as exc:
        return {"error": f"{type(exc).__name__}: {str(exc)[:120]}"}


def _gate_ok() -> tuple:
    """Same HEAD and < 15 min since the entry passed the gate → reuse; else run the gate (CGC_MDL223 via v0159's door)."""
    head = _head()
    try:
        age = time.time() - float(os.environ.get("VIA_GATE_PASSED_AT") or 0)
    except ValueError:
        age = 1e9
    if head and os.environ.get("VIA_GATE_PASSED_HEAD") == head and 0 <= age <= 900:
        return True, "沿用上層入口剛過的閘"
    doors = sorted(HERE.glob("CGC_MDL223_FlowConsistency_v*.py"), key=_vnum)       # the gate's own owner (v0159 reads the same door)
    if not doors:
        return False, "流程閘門 CGC_MDL223 不在"
    card = _load(doors[-1], "flow_for_v0168").gate()
    return bool(card.get("lock_success")), ("[流程] 政策過" if card.get("lock_success") else json.dumps(card.get("missing"), ensure_ascii=False))


def run_engine(args: list) -> int:
    fam_given = None
    if args[:1] == ["--family"] and len(args) >= 2:                 # keep the caller's family env (entry / sweep pass it)
        fam_given, args = args[1], args[2:]
    if not args:
        print("  用法:via-vcgc run [--family vdf|vrn|vap|core] <引擎 stem 或檔路徑> [參數…]")
        return 2
    ok, why = _gate_ok()
    if not ok:
        print(json.dumps({"via": "vcgc", "verb": "run", "state": "GATE", "why": why}, ensure_ascii=False))
        return 2
    eng = _tail(args[0])
    if eng is None:
        print(json.dumps({"via": "vcgc", "verb": "run", "state": "ABSENT", "why": f"找不到 {args[0]} 的尾版"}, ensure_ascii=False))
        return 3
    fam = fam_given or ("vdf" if eng.name.startswith("VDF_") else "vrn" if eng.name.startswith(("VRN_", "VIA_VRN")) else "core")
    py = sys.executable
    try:
        bus = sorted(HERE.glob("CGC_MDL148_EngineBus_v*.py"), key=_vnum)
        if bus:
            py = (_load(bus[-1], "bus_for_v0168").python_for(fam) or {}).get("python") or py
    except Exception:
        pass
    env = dict(os.environ, VIA_FROM_VCGC="YES")
    print(f"  [via-vcgc run] {why} · {eng.name}(家族 {fam})")
    sys.stdout.flush()
    r = subprocess.run([py, str(eng)] + [str(a) for a in args[1:]], cwd=str(eng.parent), env=env, stderr=subprocess.PIPE,
                       text=True, encoding="utf-8", errors="replace")
    if r.stderr:
        sys.stderr.write(r.stderr)
        sys.stderr.flush()
    LAST["target"] = re.sub(r"_v\d+$", "", eng.stem)
    LAST["act"] = next((str(a) for a in args[1:] if not str(a).startswith("-")), None)
    tail = [ln for ln in (r.stderr or "").splitlines() if ln.strip()]
    LAST["error"] = tail[-1].strip()[:200] if (r.returncode and tail) else ""       # the child's last error line → lesson signature
    return r.returncode


def show_events(n: int = 20) -> int:
    files = sorted(EVENTS.glob("EVENTS_*.jsonl"))
    rows = []
    for f in files[-3:]:
        rows += [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
    for e in rows[-n:]:
        s = e.get("sync") or {}
        print(f"  {e['ts']} {e['outcome']:<7} rc={e['rc']} {e['secs']:>6}s {e['verb']:<16} {' '.join(e.get('args') or [])[:50]}"
              + (f" · 同步待辦 {s.get('registry')}" if s.get("pending") else "") + (" · 教訓" if e.get("lesson") else ""))
    print(f"[事件] 近 {min(n, len(rows))} 筆 / 共 {len(rows)} 筆 · {EVENTS}")
    return 0


def _flow_book() -> tuple:
    hits = sorted(HERE.glob("VIA_Workflow_Hub_SSOT_v*.json"), key=_vnum)
    return (hits[-1], json.loads(hits[-1].read_text(encoding="utf-8"))) if hits else (None, None)


def run_events(run: str | None = None, folder: Path = EVENTS) -> tuple:
    rows = []
    for f in sorted(folder.glob("EVENTS_*.jsonl"))[-3:]:
        for line in f.read_text(encoding="utf-8").splitlines():
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if e.get("run"):
                rows.append(e)
    if not run:
        run = max(rows, key=lambda e: e.get("t0") or 0)["run"] if rows else ""
    return run, sorted((e for e in rows if e.get("run") == run), key=lambda e: e.get("t0") or 0)


def conformance(book: dict, events: list) -> dict:
    """Pure check of one run's events against the workflow SSOT (rules in book["conformance"])."""
    sections = [("hub", book.get("hub") or [])] + [(k, (book.get(k) or {}).get("steps") or []) for k in ("loop_vdf", "loop_vrn")] \
        + [("exit", book.get("exit") or [])]
    rank = {"hub": 0, "loop_vdf": 1, "loop_vrn": 1, "exit": 2}
    steps = [(sec, i, s) for sec, lst in sections for i, s in enumerate(lst)]
    first, observed = {}, []
    for n, e in enumerate(events):
        tgt, act = e.get("target") or _STEM, e.get("act") if e.get("verb") == "run" else e.get("verb")
        hit = [s["id"] for sec, i, s in steps for st, vb in (s.get("match") or []) if st == tgt and (vb is None or vb == act)]
        for sid in hit:
            first.setdefault(sid, n)
        observed.append(hit)
    red, yellow = [], []
    h1 = next((s["id"] for sec, i, s in steps if sec == "hub" and any(m[1] == "status" for m in s.get("match") or [])), "H1")
    if not events or h1 not in observed[0]:
        red.append(f"本輪第一筆不是 {h1} 流程閘(第一筆:{(events[0].get('target') or events[0].get('verb')) if events else '無事件'})")
    pos = {s["id"]: (sec, i, s) for sec, i, s in steps}
    for a in first:
        for b in first:
            sa, ia, xa = pos[a]
            sb, ib, xb = pos[b]
            if xa.get("after_gate") or xb.get("after_gate"):
                continue
            before = rank[sa] < rank[sb] or (sa == sb and ia < ib)
            if before and first[a] > first[b]:
                red.append(f"{a} 宣告在 {b} 之前,實跑在後(事件 #{first[a]} > #{first[b]})")
    for sid, (sec, i, s) in pos.items():
        if s.get("after_gate") and sid in first and h1 in first and first[sid] < first[h1]:
            red.append(f"{sid} 在 {h1} 閘之前寫入")
        if sid not in first and not s.get("inside") and s.get("match"):
            yellow.append(f"{sid} {s.get('name')} 本輪沒出現")
    lamp = "RED" if red else ("YELLOW" if yellow else "GREEN")
    return {"lamp": lamp, "rc": {"RED": 1, "YELLOW": 2, "GREEN": 0}[lamp], "red": red, "yellow": yellow,
            "seen": {k: first[k] for k in sorted(first, key=first.get)}, "events": len(events),
            "unmatched": sum(1 for h in observed if not h)}


def workflow(run: str | None = None) -> int:
    path, book = _flow_book()
    if not book:
        print("  [工作流] ABSENT:VIA_Workflow_Hub_SSOT 尾版不在")
        return 3
    run, evs = run_events(run)
    r = conformance(book, evs)
    print(f"  [工作流] {r['lamp']} · 輪 {run or '-'} · 事件 {r['events']}(不在冊上的步 {r['unmatched']})· 實跑順序 {' → '.join(r['seen'])}"
          f" · 冊 {path.name}")
    for x in r["red"]:
        print(f"    紅 {x}")
    for x in r["yellow"]:
        print(f"    黃 {x}")
    return r["rc"]


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    verb = args[0] if args else "(help)"
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        return PRIOR.main(argv)
    if verb == "events":
        return show_events(int(args[1]) if len(args) > 1 and args[1].isdigit() else 20)
    if verb == "workflow":
        return workflow(args[1] if len(args) > 1 else None)
    tk0 = PRIOR.tree_key() if verb not in NO_SYNC_VERBS else None
    t0 = time.time()
    err = ""
    LAST.clear()
    try:
        if verb == "run":
            rc = run_engine(args[1:])
            err = LAST.get("error", "")
        elif verb == "sync-check":
            r = sync_check(PRIOR.tree_key())
            print(json.dumps(r, ensure_ascii=False, indent=1))
            rc = 0 if r["aligned"] else 2
        else:
            rc = PRIOR.main(argv)
    except SystemExit as exc:
        rc = exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)
    except Exception as exc:
        rc, err = 1, f"{type(exc).__name__}: {str(exc)[:200]}"
    rc = int(rc or 0)
    ev = {"ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "verb": verb, "args": [str(a)[:80] for a in args[1:7]],
          "rc": rc, "outcome": outcome(rc), "secs": round(time.time() - t0, 1), "head": _head()[:12], "error": err,
          "engine": Path(__file__).stem, "run": os.environ.get("VIA_HUB_RUN", ""), "t0": round(t0, 3),
          "target": LAST.get("target") or _STEM, "act": LAST.get("act") if verb == "run" else verb}
    if verb not in NO_SYNC_VERBS and os.environ.get("VIA_VCGC_NOSYNC") != "1":
        tk1 = PRIOR.tree_key()
        ev["tree_before"], ev["tree_after"] = tk0, tk1
        last = {}
        try:
            last = json.loads(SYNC_STATE.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass
        if tk1 and (tk1 != tk0 or last.get("key") != tk1):
            s = sync_check(tk1)
            ev["sync"] = s
            try:
                SYNC_STATE.parent.mkdir(parents=True, exist_ok=True)
                SYNC_STATE.write_text(json.dumps(s, ensure_ascii=False), encoding="utf-8")
            except OSError:
                pass
            if s["pending"] or not s["aligned"]:
                print(f"  [同步] 樹有變 · 註冊冊待同步 {s.get('registry')} · 座位 {'對齊' if s['aligned'] else '沒對齊 ' + str((s.get('seat') or {}).get('missing'))}"
                      " → 批准寫入:via-vcgc registry-sync --apply")
        else:
            ev["sync"] = {"skipped": "樹沒變(上次同步檢查同一指紋)"}
    if ev["outcome"] == "FAIL":
        ev["lesson"] = _lessons(ev)
        if ev["lesson"] and ev["lesson"].get("repeat"):
            print(f"  [教訓] 重複出錯:{ev['lesson'].get('sig')} · 第 {ev['lesson'].get('count')} 次 · 帳本 CGC_MDL058(via-lessons)")
    try:
        write_event(ev)
    except OSError:
        pass
    return rc


def selftest() -> int:
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    chk("結果類:0=OK · 2/3/4=FINDING · 其他=FAIL", [outcome(x) for x in (0, 2, 3, 4, 1, 9)] == ["OK", "FINDING", "FINDING", "FINDING", "FAIL", "FAIL"])
    with tempfile.TemporaryDirectory() as td:
        f = write_event({"ts": "t", "verb": "x", "rc": 0}, Path(td))
        chk("事件只增寫進 VIA_Reports/vcgc/events(不入 git)", f.exists() and len(f.read_text(encoding="utf-8").splitlines()) == 1)
    chk("run 找尾版:stem → 最新版號檔", (_tail("CGC_MDL237_NumberingSystem") or Path("x")).name.startswith("CGC_MDL237_NumberingSystem_v"),
        (_tail("CGC_MDL237_NumberingSystem") or Path("-")).name)
    chk("run 找不到 = ABSENT(不猜)", _tail("NO_SUCH_ENGINE_ZZZ") is None)
    s = sync_check(PRIOR.tree_key())
    chk("同步檢查:座位 + 註冊乾跑都有結果(只讀,不寫冊)", "seat" in s and "registry" in s and "error" not in (s.get("registry") or {}), {k: s[k] for k in ("aligned", "pending")})
    keep = {k: os.environ.get(k) for k in ("VIA_GATE_PASSED_HEAD", "VIA_GATE_PASSED_AT")}
    os.environ["VIA_GATE_PASSED_HEAD"], os.environ["VIA_GATE_PASSED_AT"] = _head(), str(time.time())
    try:
        g = _gate_ok()
    finally:
        for k, v in keep.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    chk("同一 HEAD 15 分鐘內沿用入口剛過的閘(不重跑)", g[0] and "沿用" in g[1])
    keep = {k: os.environ.pop(k, None) for k in ("VIA_GATE_PASSED_HEAD", "VIA_GATE_PASSED_AT")}
    try:
        g2 = _gate_ok()
    finally:
        for k, v in keep.items():
            if v is not None:
                os.environ[k] = v
    chk("沒有上層閘時自己跑流程閘(CGC_MDL223 正主)", isinstance(g2[0], bool) and g2[1], g2[1][:60])
    body = Path(__file__).read_text(encoding="utf-8")
    chk("抬頭 raw · 帶 VIA_FROM_VCGC 標記(座位探針要)", body.split("\n", 3)[2].startswith('r"""') and "VIA_FROM_VCGC" in body)
    chk("教訓簽名帶目標:run 帶引擎 stem · 主控台動詞帶子動詞(不同引擎不併成一個重複)",
        lesson_verb({"verb": "run", "target": "CGC_MDL242_PathVerify", "args": ["--family", "vrn", "x", "run"]}) == "run CGC_MDL242_PathVerify"
        and lesson_verb({"verb": "dbm", "args": ["panel", "--quiet"]}) == "dbm panel" and lesson_verb({"verb": "status", "args": []}) == "status")
    _, book = _flow_book()
    chk("工作流 SSOT 尾版在 · 每個非 inside 步都有 match", book is not None and all(
        s.get("match") or s.get("inside") for s in (book.get("hub") or []) + (book.get("exit") or [])
        + [x for k in ("loop_vdf", "loop_vrn") for x in (book.get(k) or {}).get("steps") or []]))

    def ev(tgt, act):
        return {"verb": "run", "target": tgt, "act": act} if tgt != _STEM else {"verb": act, "target": _STEM, "act": act}
    good = [ev(_STEM, "status"), ev("CGC_MDL238_OperatorConsole", "paths"), ev("CGC_MDL158_VIAPanoramaAuditRepair", "pack"),
            ev("CGC_MDL240_EnvManager", None), ev("CGC_MDL238_OperatorConsole", "sync-check"), ev("CGC_MDL243_TalibCommandScan", "scan"),
            ev("CGC_MDL239_DataBroker", "build"), ev("CGC_MDL172_VRNChainRunner", "run"), ev("CGC_MDL170_VDFChainRunner", "run"),
            ev("VRN_ENG113_LogicRollup", None), ev("CGC_MDL238_OperatorConsole", "parquet"), ev("CGC_MDL238_OperatorConsole", "page"),
            ev("CGC_MDL242_PathVerify", "run"), ev("CGC_MDL058_Lessons", None)]
    r = conformance(book or {}, good)
    chk("實跑照冊(H0 在閘後 · VRN 迴圈先於 VDF 迴圈也可)= 綠", r["lamp"] == "GREEN", r["red"] + r["yellow"])
    r = conformance(book or {}, good[1:])
    chk("第一筆不是 H1 閘 = 紅", r["lamp"] == "RED" and any("第一筆" in x for x in r["red"]))
    r = conformance(book or {}, good[:3] + [good[5], good[3]] + good[4:5] + good[6:])
    chk("H5 跑在 H3 之前(段內倒置)= 紅", r["lamp"] == "RED" and any(x.startswith("H3") for x in r["red"]), r["red"][:1])
    r = conformance(book or {}, good[:4])
    chk("宣告步本輪沒出現(例 -SkipSweep)= 黃不紅", r["lamp"] == "YELLOW" and not r["red"], len(r["yellow"]))
    r = conformance(book or {}, good[:11] + [good[12], good[11], good[13]])
    chk("出口段倒置(X2 驗證在 X1 頁之前)= 紅", r["lamp"] == "RED" and any(x.startswith("X1") for x in r["red"]), r["red"][:1])
    if not all(ok):
        return 1
    return PRIOR.selftest()


if __name__ == "__main__":
    a = sys.argv[1:]
    raise SystemExit(selftest() if a == ["--selftest"] else main())
