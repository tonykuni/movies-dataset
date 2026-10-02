#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC v0186 — 薄尾:寫入前衝突阻擋 `guard` · 每個動詞執行監控 `exec` · 子系統邊界(VCGC 不改 VDF / VRN 正本)

操作員(2026-10-01):「對 VCGC 進行整合不要影響 VDF VRN · 所有參數庫及邏輯下放到 VDF VRN · 監控能力增強到 VCGC ·
  自動將 VCGC 整合收尾 · 一切功能都要有執行監控及實施阻擋衝突的能力 · 授權跟 GitHub 的互動及 PowerShell 的互動自動完成並實測驗證上傳 GitHub」
操作員裁定(同日):下放 = 正本歸子系統、不搬檔(VDF / VRN 的參數冊 · 邏輯冊是唯一正本;VCGC 只讀、只查衝突並阻擋,不持副本、不改 VDF / VRN 檔)·
  PowerShell 實測接進 GitHub CI 的 Windows · 阻擋範圍 = 所有寫入動作(唯讀動作只監控不擋)。
本版:
  ① guard:寫入動作(--apply · --push · handoff checkpoint)前先過衝突閘 —— 衝突哨兵 via_conflict_guard(中央參數跨冊 · canonical 未裁 ·
     裁決冊 · 存證 · 寫死路徑 · 壞環境 · 13 道;FAIL = 擋)· GitHub 對齊(同檔兩邊新增 · 同家族 main 版號超前 · 需求同號異義 = 擋;落後 main 只警示)·
     子系統邊界(本動作明指要寫 VDF / VRN 正本 = 擋)。擋 = 不執行、rc 1、印衝突與補法。沒有繞過開關。`guard` 動詞單獨乾跑同一道閘。
  ② exec:每個 VCGC 動詞執行都記一筆(動詞 · 寫入與否 · 閘判 · rc · 秒數 · 動作後 VDF / VRN 正本有沒有被改 = 越界)→
     VIA_Reports/vcgc/exec/exec_ledger.jsonl(只增)+ EXEC_latest.json;`exec [--last N]` 印最近 N 筆。越界 = 該筆 rc 1 並記紅。
  ③ 全綠閘多兩探針:衝突哨兵 · 執行監控(最近寫入動作有被擋 / 越界 / 失敗 = 黃,列出)。
  ④ link:只寫 VCGC 自己的工作流冊;VDF / VRN 工作流冊的回指只出提案(VIA_Reports/link/PROPOSAL_latest.json)由子系統自己出新版。
     (本裁定前 v0185 已寫的 VIA_Workflow_VDF v0101 / VRN v0104 照只增律保留,不刪 —— 刪了編號稽核會記遺失。)
  ⑤ closeout --apply:先比對總控頁(VIA_UI_MasterControl)與正主管理器輸出 —— 用契約測試同一把尺(test_master_control_contract 的
     normalized_generated_page);落後才重產並提交(新尾版一進來 CI test_11 就不再紅;R48 實錄)。
其餘照 v0185。
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
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
REPO = VIA.parent
_STEM = "CGC_MDL149_VeritasCentralGovernanceConsole"
PRIOR_PATH = max(p for p in HERE.glob(_STEM + "_v*.py") if p.name < Path(__file__).name)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_v0186", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
EXEC_OUT = VIA / "VIA_Reports" / "vcgc" / "exec"
LINK_OUT = VIA / "VIA_Reports" / "link"
SUBSYS = ("VDF", "VRN")
GUARD_LINE = "guard  寫入前衝突閘(乾跑):衝突哨兵 · GitHub 對齊 · 子系統邊界;寫入動作(--apply / --push / checkpoint)自動先過,有衝突就擋"
EXEC_LINE = "exec [--last N]  執行監控:每個動詞的 寫入 · 閘判 · rc · 秒數 · 越界(只增帳)"


def __getattr__(name):
    return getattr(PRIOR, name)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------------------------------------------------------------- help
_PREV_CATALOG = PRIOR.help_catalog
_PREV_SHOW = vars(PRIOR).get("_show_help_v0185")
_PATCHED: list = []


def help_catalog():
    card = _PREV_CATALOG()
    card.update(entry=Path(__file__).name, previous=PRIOR_PATH.name, guard=GUARD_LINE, exec=EXEC_LINE)
    return card


def _show_help_v0186():
    if _PREV_SHOW is not None:
        _PREV_SHOW()
    print("  " + GUARD_LINE)
    print("  " + EXEC_LINE)


def _chain() -> list:
    mods, m = [], PRIOR
    while m is not None and m not in mods:
        mods.append(m)
        m = vars(m).get("PRIOR")
    return mods


def _patch_help(on: bool = True) -> None:
    if on:
        for _m in _chain():
            if vars(_m).get("help_catalog") is _PREV_CATALOG:
                _m.help_catalog = help_catalog
                _PATCHED.append((_m, "help_catalog", _PREV_CATALOG))
            if _PREV_SHOW is not None and vars(_m).get("show_current_help") is _PREV_SHOW:
                _m.show_current_help = _show_help_v0186
                _PATCHED.append((_m, "show_current_help", _PREV_SHOW))
    else:
        for _m, attr, orig in _PATCHED:
            setattr(_m, attr, orig)
        _PATCHED.clear()


_patch_help(True)


# ---------------------------------------------------------------- 子系統正本(VDF / VRN 擁有;VCGC 只讀)
OWNED_RX = re.compile(r"^VeritasIntelligenceAnalytics/(functional modules/(VDF|VRN)/|supportive modules/registry/"
                      r"(VIA_Workflow_(VDF|VRN)_SSOT_v\d{4}\.json|(VIA_)?(VDF|VRN)_[^/]+))")


def owned_by(path: str) -> str | None:
    """VDF / VRN 正本路徑 → 子系統名;其他 None(中央編號簿 · 收據 · VCGC 冊不算)。"""
    m = OWNED_RX.match(path.replace("\\", "/"))
    if not m:
        return None
    return m.group(2) or m.group(4) or m.group(6)


def owned_dirty() -> dict:
    """VDF / VRN 正本目前未提交的變動 {路徑: 狀態}(git status;動作前後各量一次,差集 = 本動作改的)。"""
    rc, out = PRIOR._git("status", "--porcelain", "-uall", "--", "VeritasIntelligenceAnalytics", timeout=120)
    res = {}
    for ln in out.splitlines() if rc == 0 else []:
        p = ln[3:].strip().strip('"')
        if " -> " in p:
            p = p.split(" -> ", 1)[1].strip('"')
        try:
            p = p.encode("latin-1").decode("unicode_escape").encode("latin-1").decode("utf-8") if "\\" in p else p
        except (UnicodeError, ValueError):
            pass
        if owned_by(p):
            res[p] = ln[:2]
    return res


# ---------------------------------------------------------------- guard:寫入前衝突閘
def is_write(args: list) -> bool:
    return "--apply" in args or "--push" in args or args[:2] == ["handoff", "checkpoint"]


def g_conflict() -> dict:
    tails = sorted(HERE.glob("via_conflict_guard_v*.py"))
    if not tails:
        return {"probe": "衝突哨兵", "lamp": "NODATA", "note": "via_conflict_guard 不在", "items": [], "block": False}
    env = {**os.environ, "VIA_FROM_VCGC": "YES", "VIA_PANORAMA_AUTO": "0"}
    try:
        p = subprocess.run([sys.executable, str(tails[-1])], cwd=str(REPO), capture_output=True, timeout=300, env=env, stdin=subprocess.DEVNULL)
        rc, txt = p.returncode, (p.stdout + p.stderr).decode("utf-8", "replace")
    except subprocess.TimeoutExpired:
        rc, txt = 124, "逾時"
    fails = [re.sub(r"\s+", " ", ln.strip()) for ln in txt.splitlines() if "[FAIL]" in ln]
    warns = [re.sub(r"\s+", " ", ln.strip()) for ln in txt.splitlines() if "[WARN]" in ln]
    m = re.search(r"\[計\] (.+?) · 存證", txt)
    lamp = "RED" if fails or rc not in (0,) else ("YELLOW" if warns else "GREEN")
    return {"probe": "衝突哨兵", "lamp": lamp, "note": (m.group(1) if m else f"rc {rc}") + f" · {tails[-1].name}",
            "items": fails + warns, "block": bool(fails) or rc not in (0,)}


def g_github() -> dict:
    r = PRIOR.probe_github("guard")
    hits = [x for x in r.get("items") or [] if x.startswith(("撞號", "同號異義"))]
    r["block"] = bool(hits)
    return r


def g_boundary(args: list) -> dict:
    """動作明指要寫 VDF / VRN 正本(例:run VDF_… --apply 由 VCGC 代寫)= 擋;VDF / VRN 自己的管理器經 run 自理不在此列。"""
    words = " ".join(args)
    hit = [a for a in args if owned_by("VeritasIntelligenceAnalytics/supportive modules/registry/" + Path(a).name) and Path(a).suffix in (".json", ".jsonl")]
    return {"probe": "子系統邊界", "lamp": "RED" if hit else "GREEN",
            "note": ("本動作要寫 VDF / VRN 正本:" + ", ".join(hit)) if hit else "本動作不指名寫 VDF / VRN 正本(動作後再量一次越界)",
            "items": [f"越界 {h}" for h in hit], "block": bool(hit), "words": words[:80]}


def guard(args: list | None = None, verbose: bool = True) -> dict:
    t0 = time.time()
    rows = PRIOR._par(lambda f: f(), [g_conflict, g_github, lambda: g_boundary(args or [])])
    out = []
    for name, r in zip(("衝突哨兵", "GitHub 對齊", "子系統邊界"), rows):
        if "err" in r:
            r = {"probe": name, "lamp": "RED", "note": f"探針崩:{r['err']}", "items": [], "block": True}
        out.append(r)
    blocked = any(r.get("block") for r in out)
    rep = {"at": _now(), "args": (args or [])[:6], "blocked": blocked, "secs": round(time.time() - t0, 1),
           "probes": [{k: r.get(k) for k in ("probe", "lamp", "note", "items", "block")} for r in out]}
    if verbose:
        print(f"[VCGC 衝突閘] {'BLOCK 擋下' if blocked else 'PASS 放行'} · {rep['secs']}s · " + " · ".join(f"{r['probe']} {r['lamp']}" for r in out))
        for r in out:
            if r["lamp"] != "GREEN":
                print(f"  {r['lamp']:<6} {r['probe']}:{r['note']}"[:220])
                for x in (r.get("items") or [])[:5]:
                    print(f"     · {x}"[:220])
    return rep


# ---------------------------------------------------------------- exec:執行監控(只增帳)
def record(row: dict) -> None:
    EXEC_OUT.mkdir(parents=True, exist_ok=True)
    with open(EXEC_OUT / "exec_ledger.jsonl", "a", encoding="utf-8") as f:  # 只增
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    try:
        rows = [json.loads(x) for x in (EXEC_OUT / "exec_ledger.jsonl").read_text(encoding="utf-8").splitlines()[-50:] if x.strip()]
    except (OSError, ValueError):
        rows = [row]
    (EXEC_OUT / "EXEC_latest.json").write_text(json.dumps({"at": _now(), "last": rows[-20:],
        "blocked": sum(1 for r in rows if r.get("blocked")), "crossed": sum(1 for r in rows if r.get("crossed")),
        "failed": sum(1 for r in rows if r.get("rc") == 1)}, ensure_ascii=False, indent=1), encoding="utf-8")


def recent(n: int = 20) -> list:
    p = EXEC_OUT / "exec_ledger.jsonl"
    if not p.is_file():
        return []
    rows = []
    for x in p.read_text(encoding="utf-8").splitlines()[-n:]:
        try:
            rows.append(json.loads(x))
        except ValueError:
            continue
    return rows


def exec_verb(args: list) -> int:
    n = int(args[args.index("--last") + 1]) if "--last" in args and args.index("--last") + 1 < len(args) else 15
    rows = recent(n)
    if not rows:
        print("[VCGC 執行監控] NODATA · 還沒有記錄(任何 via-vcgc 動作都會記一筆)")
        return 2
    bad = [r for r in rows if r.get("blocked") or r.get("crossed") or r.get("rc") == 1]
    print(f"[VCGC 執行監控] {'YELLOW' if bad else 'GREEN'} · 最近 {len(rows)} 筆 · 擋 {sum(1 for r in rows if r.get('blocked'))} · "
          f"越界 {sum(1 for r in rows if r.get('crossed'))} · 失敗 {sum(1 for r in rows if r.get('rc') == 1)}")
    for r in rows:
        mark = "BLOCK" if r.get("blocked") else ("CROSS" if r.get("crossed") else ("FAIL " if r.get("rc") == 1 else "ok   "))
        print(f"  {mark} {r.get('at', '')[11:19]} {'W' if r.get('write') else 'R'} rc {r.get('rc')} {r.get('secs')}s · {' '.join(r.get('args') or [])}"[:200])
    return 2 if bad else 0


def probe_exec(run: str) -> dict:
    rows = [r for r in recent(30) if r.get("write")]
    bad = [r for r in rows if r.get("blocked") or r.get("crossed") or r.get("rc") == 1]
    return {"probe": "執行監控", "lamp": "YELLOW" if bad else ("GREEN" if rows else "NODATA"),
            "note": f"最近寫入動作 {len(rows)} 筆 · 擋 / 越界 / 失敗 {len(bad)}",
            "items": [f"{'擋下' if r.get('blocked') else ('越界' if r.get('crossed') else '失敗')} {' '.join(r.get('args') or [])}(REVIEW)" for r in bad[-5:]]}


def probe_conflict(run: str) -> dict:
    r = g_conflict()
    r.pop("block", None)
    return r


GATE_PROBES = tuple(PRIOR.PROBES) + (("衝突哨兵", probe_conflict), ("執行監控", probe_exec))
_GATE0 = PRIOR.gate


def gate(args: list | None = None, probes=GATE_PROBES) -> int:
    return _GATE0(args, probes)


PRIOR.gate = gate  # v0185 的 closeout ⑩ 叫的 gate 也多這兩探針


# ---------------------------------------------------------------- link:VDF / VRN 只出提案
_WRITE_LINKS0 = PRIOR.write_links


def write_links(plan: dict, apply: bool) -> list:
    own = {p: v for p, v in plan.items() if not owned_by("VeritasIntelligenceAnalytics/supportive modules/registry/" + Path(p).name)}
    sub = {p: v for p, v in plan.items() if p not in own}
    done = _WRITE_LINKS0(own, apply)
    if sub:
        LINK_OUT.mkdir(parents=True, exist_ok=True)
        prop = {"at": _now(), "rule": "VDF / VRN 工作流冊是子系統正本:VCGC 只出提案,由子系統管理器出新版(只增)",
                "proposals": [{"book": Path(p).name, "subsystem": owned_by("VeritasIntelligenceAnalytics/supportive modules/registry/" + Path(p).name),
                               "add_requirements": v} for p, v in sub.items()]}
        (LINK_OUT / "PROPOSAL_latest.json").write_text(json.dumps(prop, ensure_ascii=False, indent=1), encoding="utf-8")
        for x in prop["proposals"]:
            print(f"  提案(不寫)· {x['subsystem']} · {x['book']} · " + " · ".join(f"{k} ← {', '.join(v)}" for k, v in x["add_requirements"].items()))
    return done


PRIOR.write_links = write_links  # v0185 的 link 寫冊走這支


# ---------------------------------------------------------------- 總控頁同步(契約測試同一把尺)
MASTER_HTML = VIA / "supportive modules" / "ui_support" / "VIA_UI_MasterControl_v0100.html"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def mastercontrol_sync(apply: bool) -> str:
    tests = sorted((HERE / "tests").glob("test_master_control_contract_v*.py"))
    mgrs = sorted(VIA.glob("VIA_SYSTEM_MANAGER_v*.py"))
    if not tests or not mgrs or not MASTER_HTML.is_file():
        return "ABSENT(契約測試 / 管理器 / 總控頁不在)"
    path0 = sys.path[:]
    try:
        t = _load(tests[-1], "via_mc_contract_for_v0186")
        mgr = t.load_module(t.MANAGER_PATH, "via_mc_manager_for_v0186")
        deck = t.load_module(t.latest_deck_path(), "via_mc_deck_for_v0186")
        page = mgr._build_page(mgr.do_list(do_print=False), deck.task_registry())
        old = MASTER_HTML.read_text(encoding="utf-8")
        if t.normalized_generated_page(old) == t.normalized_generated_page(page):
            return "同步(不重產)"
        if not apply:
            return "落後(乾跑不寫)"
        MASTER_HTML.write_text(page, encoding="utf-8")
        rel = str(MASTER_HTML.relative_to(REPO))
        PRIOR._git("add", "--", rel)
        rc, out = PRIOR._git("commit", "-q", "-m", "vcgc closeout: 總控頁依正主管理器重產(契約 test_11 同一把尺)", "--", rel)
        return "落後 → 已重產並提交" if rc == 0 else f"已重產,提交失敗:{out.strip()[-80:]}"
    except Exception as e:  # 照實回報,不擋收尾
        return f"比對失敗:{type(e).__name__}: {str(e)[:80]}"
    finally:
        sys.path[:] = path0


_CLOSEOUT0 = PRIOR.closeout


def closeout(args: list) -> int:
    if "--apply" in args:
        print(f"  ⓪+ 總控頁同步 · {mastercontrol_sync(True)}", flush=True)
    return _CLOSEOUT0(args)


# ---------------------------------------------------------------- main:每個動詞都監控 · 寫入先過閘
def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] in (["guard"], ["exec"]):
        if os.environ.get("VIA_FROM_VCGC") != "YES":
            print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
            return 2
        if args[0] == "guard":
            return 1 if guard(args[1:])["blocked"] else 0
        return exec_verb(args[1:])
    write = is_write(args)
    t0 = time.time()
    before = owned_dirty() if write else {}
    g = None
    if write and os.environ.get("VIA_FROM_VCGC") == "YES":
        g = guard(args)
        if g["blocked"]:
            print("[VCGC 衝突閘] 擋下:有衝突不寫入(先解衝突;沒有繞過開關)")
            record({"at": _now(), "args": args[:6], "write": True, "blocked": True, "rc": 1, "secs": round(time.time() - t0, 1),
                    "guard": [(p["probe"], p["lamp"]) for p in g["probes"]]})
            return 1
    rc = None
    try:
        rc = closeout(args[1:]) if args[:1] == ["closeout"] and os.environ.get("VIA_FROM_VCGC") == "YES" else PRIOR.main(args)
        return rc
    finally:
        crossed = sorted(set(owned_dirty()) - set(before)) if write else []
        if crossed:
            print(f"[VCGC 子系統邊界] RED · 本動作改到 VDF / VRN 正本 {len(crossed)} 檔(VCGC 不改子系統正本;收尾不提交這些檔):" + ", ".join(crossed[:5]))
        record({"at": _now(), "args": args[:6], "write": write, "blocked": False, "rc": 1 if crossed else rc,
                "secs": round(time.time() - t0, 1), "crossed": crossed[:20],
                "guard": [(p["probe"], p["lamp"]) for p in g["probes"]] if g else None})


# ---------------------------------------------------------------- selftest
def selftest():
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    V = "VeritasIntelligenceAnalytics/"
    cases = {V + "functional modules/VDF/engine/VDF_ENG072_X_v0105.py": "VDF", V + "functional modules/VRN/a.py": "VRN",
             V + "supportive modules/registry/VIA_Workflow_VDF_SSOT_v0101.json": "VDF", V + "supportive modules/registry/VRN_SourceProvenance_SSOT_v0100.json": "VRN",
             V + "supportive modules/registry/VIA_NumberBooks/VIA_NumberBook_FNC_VDF_v0100.jsonl": None,
             V + "supportive modules/registry/VIA_Workflow_VCGC_SSOT_v0109.json": None, V + "docs/handoff/evidence/vdf.json": None}
    got = {k: owned_by(k) for k in cases}
    chk("子系統正本判定:VDF / VRN 模組與冊 = 子系統;中央編號簿 · VCGC 冊 · 收據 = 不是", got == cases, [k for k in cases if got[k] != cases[k]])
    chk("寫入動作判定:--apply · --push · handoff checkpoint = 寫;其他 = 讀",
        is_write(["registry-sync", "--apply"]) and is_write(["closeout", "--apply", "--push"]) and is_write(["handoff", "checkpoint"])
        and not is_write(["status"]) and not is_write(["handoff", "check"]) and not is_write(["gate"]))
    import contextlib
    import io
    import tempfile
    global EXEC_OUT
    keep_out, keep = EXEC_OUT, (globals()["guard"], PRIOR.main, globals()["owned_dirty"])
    calls = []
    with tempfile.TemporaryDirectory() as td:
        EXEC_OUT = Path(td)
        env = os.environ.get("VIA_FROM_VCGC")
        os.environ["VIA_FROM_VCGC"] = "YES"
        try:
            PRIOR.main = lambda a: calls.append(list(a)) or 0
            globals()["guard"] = lambda a, verbose=True: {"blocked": True, "probes": [{"probe": "衝突哨兵", "lamp": "RED"}]}
            with contextlib.redirect_stdout(io.StringIO()):
                rc_b = main(["registry-sync", "--apply"])
            globals()["guard"] = lambda a, verbose=True: {"blocked": False, "probes": [{"probe": "衝突哨兵", "lamp": "GREEN"}]}
            dirty = iter([{}, {V + "functional modules/VDF/x.py": " M"}])
            globals()["owned_dirty"] = lambda: next(dirty)
            with contextlib.redirect_stdout(io.StringIO()):
                rc_x = main(["run", "X", "--apply"])
            globals()["owned_dirty"] = lambda: {}
            rc_r = main(["status"])
            led = [json.loads(x) for x in (EXEC_OUT / "exec_ledger.jsonl").read_text(encoding="utf-8").splitlines()]
            with contextlib.redirect_stdout(io.StringIO()):
                rc_e = exec_verb(["--last", "5"])
            pe = probe_exec("t")
        finally:
            globals()["guard"], PRIOR.main, globals()["owned_dirty"] = keep
            if env is None:
                os.environ.pop("VIA_FROM_VCGC", None)
            else:
                os.environ["VIA_FROM_VCGC"] = env
        EXEC_OUT = keep_out
    chk("寫入先過閘:有衝突 = 不執行(rc 1)· 帳記擋下", rc_b == 1 and ["registry-sync", "--apply"] not in calls and led[0]["blocked"], (rc_b, calls))
    chk("越界:寫入動作改到 VDF / VRN 正本 = 記越界 · 該筆 rc 1", led[1]["crossed"] == [V + "functional modules/VDF/x.py"] and led[1]["rc"] == 1, led[1])
    chk("唯讀動作只監控不擋:照轉前版 · 記一筆 R", rc_r == 0 and ["status"] in calls and led[2]["write"] is False and led[2]["guard"] is None)
    chk("exec 卡 · 執行監控探針:有擋 / 越界 = 黃並列出", rc_e == 2 and pe["lamp"] == "YELLOW" and len(pe["items"]) == 2, pe)
    with tempfile.TemporaryDirectory() as td:
        global LINK_OUT
        keep_l = LINK_OUT
        LINK_OUT = Path(td) / "link"
        pv = Path(td) / "VIA_Workflow_VCGC_SSOT_v0103.json"
        pd = Path(td) / "VIA_Workflow_VDF_SSOT_v0100.json"
        for p, c in ((pv, "VCGC-WKF001"), (pd, "VDF-WKF001")):
            p.write_text(json.dumps({"version": p.stem[-5:], "workflows": [{"code": c, "spec": {"requirements": []}}]}, indent=1), encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            done = write_links({pv: {"VCGC-WKF001": ["VCGC-REQ1"]}, pd: {"VDF-WKF001": ["VDF-REQ1"]}}, True)
        prop = json.loads((LINK_OUT / "PROPOSAL_latest.json").read_text(encoding="utf-8"))
        wrote_vdf = (Path(td) / "VIA_Workflow_VDF_SSOT_v0101.json").exists()
        wrote_vcgc = (Path(td) / "VIA_Workflow_VCGC_SSOT_v0104.json").exists()
        LINK_OUT = keep_l
    chk("link:VCGC 冊照寫新版;VDF 冊只出提案不寫(正本歸子系統)", wrote_vcgc and not wrote_vdf and len(done) == 1
        and prop["proposals"][0]["subsystem"] == "VDF", (wrote_vcgc, wrote_vdf, prop))
    src0 = Path(__file__).read_text(encoding="utf-8")
    chk("closeout --apply 先比對總控頁(契約測試同一把尺)· 落後才重產 · 只提交那一檔", "normalized_generated_page" in src0
        and "⓪+ 總控頁同步" in src0 and '"commit", "-q", "-m"' in src0 and mastercontrol_sync.__code__.co_argcount == 1)
    names = [p[0] for p in GATE_PROBES]
    chk("全綠閘多兩探針(衝突哨兵 · 執行監控)· v0185 closeout ⑩ 用到的 gate 已換成本版", names[-2:] == ["衝突哨兵", "執行監控"] and PRIOR.gate is gate)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("沒有繞過開關 · guard / exec 不經 VCGC 拒跑 · 加速器橋 · 網路橋",
        ("GUARD" + "=0") not in src and ("VIA_VCGC_" + "NOGUARD") not in src and 'os.environ.get("VIA_FROM_VCGC") != "YES"' in src
        and "[VIA:ACCEL-BRIDGE" in src and "[VIA:NET-BRIDGE" in src)
    card = help_catalog()
    chk("help 目前生效入口 = 本版 · 多 guard / exec", card.get("entry") == Path(__file__).name and "guard" in card and "exec" in card)
    print(f"  VCGC v0186 selftest {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}")
    if not all(ok):
        return 1
    _patch_help(False)
    try:
        return PRIOR.selftest()
    finally:
        _patch_help(True)


if __name__ == "__main__":
    raise SystemExit(selftest() if sys.argv[1:] == ["--selftest"] else main())
