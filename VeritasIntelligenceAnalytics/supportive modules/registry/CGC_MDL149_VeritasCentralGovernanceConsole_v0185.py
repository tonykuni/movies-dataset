#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC v0185 — 薄尾:全綠閘 `gate` · 上下自動連接 `link` · closeout 收尾必過全綠閘(黃不是綠)

操作員(2026-10-01):「VCGC SSOT regex 同義字 workflow for VCGC VRN VDF 只增不減但要編號 · 相同數據不同來源也是不同編號 ·
  引擎 模組 系統 子系統 邏輯 參數 應該全都自動編號優化 · 不衝突只增不減 · 子系統跟母系統如何自動連接 ·
  所有邏輯參數下放到子系統由母系統擷取檢查衝突或透過 GitHub 檢查 · 自動化相互檢測的能力建構在 VCGC ·
  VCGC 所有功能全亮綠燈檢查才往下」
既有的(不重做):中央編號 CGC_MDL237(MDL · ENG · FNC · CLS · LGC · PRMT · RGX · SYN · SSOT · REQ · WKF · STP · SRC · XSRC 來源分立 …,只增稽核)·
  SSOT 全景 CGC_MDL247(正則 · 同義字 · 編號 · 命名 · 註冊 · 上下連結 × VCGC / VDF / VRN / SUP)· 參數樞紐(X-CONFLICT)· SDD · 交接 · 串測。
本版補三件:
  ① gate [--json]:全綠閘。七個探針並行(加速器 accel_map)——交接 · 全功能串測 · SSOT 全景 · SDD · 編號稽核 · GitHub 對齊(落後 main /
     與 main 撞號:同檔名兩邊都新增 · 同家族 main 版號已到或超過本分支新檔 · 需求代碼同號異義)· 母子連接(需求 ↔ 工作流單向)。
     全部 GREEN 才 GREEN;任何非綠逐條列出並分類:AUTO(VCGC 指令就能補,附指令)· RUN(要實跑 / 工作站)· ENV(環境缺件)·
     OPERATOR(要操作員裁定)· REVIEW(其他)。落 VIA_Reports/gate/GATE_latest.json + gate_ledger.jsonl(只增)。rc:綠 0 · 黃 2 · 紅 1。
  ② link [--apply]:母子自動連接 —— 需求指到工作流(或其步)而工作流沒回指的,補進該子系統工作流冊新版的 spec.requirements
     (只增:出新版號檔 · prior 指回 · why 寫明;舊版不動)。沒加 --apply = 乾跑。
  ③ closeout:--apply 時先跑 link --apply(新冊隨同輪註冊 · 編號 · 測試)· 收尾後跑 ⑩ 全綠閘;
     收尾綠但閘不綠 = 總判 YELLOW(rc 2,黃不是綠),--strict 時 = RED(rc 1)。
其餘照 v0184。
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
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_v0185", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
GATE_OUT = VIA / "VIA_Reports" / "gate"
LAMPS = ("GREEN", "YELLOW", "RED")
ORDER = {"GREEN": 0, "NODATA": 1, "YELLOW": 2, "RED": 3}
GATE_LINE = "gate [--json] [--only 探針,…]  全綠閘:交接 · 串測 · SSOT 全景 · SDD · 編號 · GitHub 對齊 · 母子連接 全綠才往下;非綠逐條分 AUTO / RUN / ENV / OPERATOR"
LINK_LINE = "link [--apply]  母子自動連接:需求 → 工作流沒回指的補進子系統工作流冊新版(只增)"


def __getattr__(name):
    return getattr(PRIOR, name)


def _chain() -> list:
    mods, m = [], PRIOR
    while m is not None and m not in mods:
        mods.append(m)
        m = vars(m).get("PRIOR")
    return mods


def _owner(name: str):
    return next((m for m in _chain() if callable(vars(m).get(name))), None)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------------------------------------------------------------- help: current entry is this tail
_PREV_CATALOG = PRIOR.help_catalog
_PREV_SHOW = vars(PRIOR).get("_show_help_v0184")
_PATCHED: list = []


def help_catalog():
    card = _PREV_CATALOG()
    card.update(entry=Path(__file__).name, previous=PRIOR_PATH.name, gate=GATE_LINE, link=LINK_LINE)
    return card


def _show_help_v0185():
    if _PREV_SHOW is not None:
        _PREV_SHOW()
    print("  " + GATE_LINE)
    print("  " + LINK_LINE)


def _patch_help(on: bool = True) -> None:
    """v0184 把舊版的 help 接到它身上;本版接回自己(v0184 本身不動)。on=False 還原(跑前版自測時用)。"""
    if on:
        for _m in _chain():
            if vars(_m).get("help_catalog") is _PREV_CATALOG:
                _m.help_catalog = help_catalog
                _PATCHED.append((_m, "help_catalog", _PREV_CATALOG))
            if _PREV_SHOW is not None and vars(_m).get("show_current_help") is _PREV_SHOW:
                _m.show_current_help = _show_help_v0185
                _PATCHED.append((_m, "show_current_help", _PREV_SHOW))
    else:
        for _m, attr, orig in _PATCHED:
            setattr(_m, attr, orig)
        _PATCHED.clear()


_patch_help(True)


# ---------------------------------------------------------------- 分類:非綠是誰能補
KIND_RULES = (
    ("ENV", r"pwsh|PowerShell 7|沒裝|未安裝|ABSENT"),
    ("RUN", r"X-LOCK|待重驗鎖 [1-9]|lock --apply|實跑|Windows"),
    ("AUTO", r"單向|X-REQ-BACK|link --apply|registry-sync|註冊冊待同步|MODULE_UNREGISTERED|待 CGC_MDL237|缺號 [1-9]|落後 main|CHANGED_CODE_WITHOUT_TEST|EVIDENCE_INVALID|closeout"),
    ("OPERATOR", r"裁定|同詞多義|同號異名|DISAGREE|NONCANONICAL|X-REQ-OPEN|未全落地|PARTIAL|MISSING|操作員|撞號|同號異義"),
)
REMEDY = {"ENV": "工作站(有 pwsh / 主機)上跑 via-vcgc gate", "RUN": "via-vcgc sdd real → via-vcgc run CGC_MDL245_SDDValidator lock --apply(要實跑)",
          "AUTO": "via-vcgc closeout --apply --push(含 link · registry-sync · 編號 · 重測)", "OPERATOR": "操作員裁定後登錄需求冊 / 命名冊,再 closeout",
          "REVIEW": "看該探針的完整記錄"}


def classify(text: str) -> str:
    for kind, rx in KIND_RULES:
        if re.search(rx, text):
            return kind
    return "REVIEW"


# ---------------------------------------------------------------- 探針
def _lamp(s: str | None) -> str:
    s = (s or "").upper()
    return s if s in ORDER else "NODATA"


def _sub(argv: list, name: str, run: str, timeout: int = 900) -> tuple:
    log = GATE_OUT / run / f"{name}.log"
    return PRIOR.sub(argv, log, timeout=timeout)


def probe_handoff(run: str) -> dict:
    rc, txt = _sub(["handoff", "check"], "handoff", run)
    m = re.search(r"\[交接防遺漏\] (\w+) · 驗收 (\w+)", txt)
    items = [ln.strip() for ln in txt.splitlines() if ln.startswith(("[RED]", "[YELLOW]"))]
    lamp = _lamp(m.group(1)) if m else ("GREEN" if rc == 0 else "RED")
    return {"probe": "交接", "lamp": lamp, "note": (f"交接 {m.group(1)} · 驗收 {m.group(2)}" if m else f"rc {rc}"), "items": items}


def probe_test(run: str) -> dict:
    rc, txt = _sub(["test", "--quick"], "test", run)
    m = re.search(r"\[VCGC 全功能串測\] (\w+) · (站 [^·]+)", txt)
    items = [re.sub(r"\s+", " ", ln.strip()) for ln in txt.splitlines() if re.match(r"\s+\[(YELLOW|RED)\s*\]", ln)]
    return {"probe": "全功能串測", "lamp": _lamp(m.group(1)) if m else ("GREEN" if rc == 0 else "RED"), "note": m.group(2).strip() if m else f"rc {rc}", "items": items}


def probe_ssot(run: str) -> dict:
    rc, txt = _sub(["ssot", "panorama"], "ssot", run)
    m = re.search(r"\[SSOT 全景\] (\w+)", txt)
    items = [re.sub(r"\s+", " ", ln.strip()) for ln in txt.splitlines() if re.match(r"\s+\[(YELLOW|RED)\] \S+@", ln)]
    return {"probe": "SSOT 全景", "lamp": _lamp(m.group(1)) if m else ("GREEN" if rc == 0 else "RED"),
            "note": "正則 · 同義字 · 編號 · 命名 · 註冊 · 上下連結 × VCGC / VDF / VRN / SUP", "items": items}


def probe_sdd(run: str) -> dict:
    rc, txt = _sub(["run", "CGC_MDL245_SDDValidator", "check"], "sdd", run)
    m = re.search(r"\[SDD 驗證\] (\w+)", txt)
    items = [re.sub(r"\s+", " ", ln.strip()) for ln in txt.splitlines() if re.match(r"\s+(YELLOW|RED)\s+X-", ln)]
    return {"probe": "SDD", "lamp": _lamp(m.group(1)) if m else ("GREEN" if rc == 0 else "RED"), "note": "工作流 · 需求 · 參數衝突 X-CONFLICT · 鎖", "items": items}


def probe_numbering(run: str) -> dict:
    rc, txt = _sub(["run", "CGC_MDL237_NumberingSystem", "audit"], "numbering", run)
    a = re.search(r"遺失 (\d+) · 改身分 (\d+) · 重號 (\d+)", txt)
    bad = bool(a) and any(int(x) for x in a.groups())
    note = f"遺失 {a.group(1)} · 改身分 {a.group(2)} · 重號 {a.group(3)}" if a else "稽核讀不到"
    return {"probe": "編號稽核", "lamp": "RED" if bad or not a else "GREEN", "note": note + "(只增:相同數據不同來源各自編號)", "items": [note] if bad else []}


def _git(*args, timeout=120) -> tuple:
    try:
        p = subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, timeout=timeout, stdin=subprocess.DEVNULL)
        return p.returncode, (p.stdout + p.stderr).decode("utf-8", "replace")
    except subprocess.TimeoutExpired:
        return 124, "逾時"


VER_RX = re.compile(r"^(?P<stem>.+)_v(?P<v>\d{4})\.(?P<ext>py|json|jsonl|ps1|psm1)$")


def collisions(added_here: list, added_main: list, main_files: list) -> list:
    """本分支新增的檔 vs main 自分叉後新增的檔:同路徑兩邊都新增 = 撞號;同家族 main 的版號已到 / 超過本分支新檔 = 要改編。"""
    out, main_set = [], set(added_main)
    fam_main: dict = {}
    for f in main_files:
        m = VER_RX.match(Path(f).name)
        if m and f in main_set:
            k = (str(Path(f).parent), m["stem"], m["ext"])
            fam_main[k] = max(fam_main.get(k, 0), int(m["v"]))
    for f in added_here:
        if f in main_set:
            out.append(f"撞號(兩邊都新增){Path(f).name}")
            continue
        m = VER_RX.match(Path(f).name)
        if m:
            top = fam_main.get((str(Path(f).parent), m["stem"], m["ext"]))
            if top is not None and top >= int(m["v"]):
                out.append(f"撞號(main 已到 v{top:04d}){Path(f).name} → 改編到 v{top + 1:04d} 以後")
    return out


def req_clash(here: dict, main: dict) -> list:
    """需求代碼同號異義:兩邊都有同一代碼但題目不同(不同來源不得因值相同合併編號)。"""
    a = {r.get("code"): r.get("topic") for r in here.get("requirements") or []}
    b = {r.get("code"): r.get("topic") for r in main.get("requirements") or []}
    return [f"同號異義 {c}" for c in sorted(set(a) & set(b)) if a[c] != b[c]]


def probe_github(run: str, fetch: bool = True) -> dict:
    if fetch:
        rc, out = _git("fetch", "-q", "origin", "main", timeout=120)
        if rc != 0:
            return {"probe": "GitHub 對齊", "lamp": "NODATA", "note": f"fetch 失敗(照實):{out.strip()[-100:]}", "items": [f"GitHub fetch 失敗 {out.strip()[-80:]}"]}
    rc, base = _git("merge-base", "HEAD", "origin/main")
    if rc != 0:
        return {"probe": "GitHub 對齊", "lamp": "NODATA", "note": "沒有 origin/main", "items": []}
    base = base.strip()
    behind = int(_git("rev-list", "--count", "HEAD..origin/main")[1].strip() or 0)
    ahead = int(_git("rev-list", "--count", "origin/main..HEAD")[1].strip() or 0)
    here = [x for x in _git("diff", "--name-only", "--diff-filter=A", base, "HEAD")[1].splitlines() if x]
    mainadd = [x for x in _git("diff", "--name-only", "--diff-filter=A", base, "origin/main")[1].splitlines() if x]
    hits = collisions(here, mainadd, mainadd)
    req_rel = "VeritasIntelligenceAnalytics/supportive modules/registry/"
    def newest_req(ref):
        names = [x for x in _git("ls-tree", "--name-only", ref, req_rel)[1].splitlines() if "VIA_Requirements_SSOT_v" in x]
        if not names:
            return {}
        try:
            return json.loads(_git("show", f"{ref}:{sorted(names)[-1]}")[1])
        except ValueError:
            return {}
    if ahead:
        hits += req_clash(newest_req("HEAD"), newest_req("origin/main"))
    items = hits + ([f"落後 main {behind} 提交(先合 main:git merge origin/main)"] if behind else [])
    lamp = "RED" if hits else ("YELLOW" if behind else "GREEN")
    return {"probe": "GitHub 對齊", "lamp": lamp, "note": f"領先 {ahead} · 落後 {behind} · 撞號 {len(hits)}", "items": items}


def _sdd_state():
    """SDD 正主尾版的冊狀態(工作流冊 · 需求冊)與 back_links;不在 = None。"""
    tails = sorted(HERE.glob("CGC_MDL245_SDDValidator_v*.py"))
    if not tails:
        return None, None
    spec = importlib.util.spec_from_file_location("CGC_MDL245_for_v0185", tails[-1])
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    base = mod
    while "PRIOR" in vars(base):
        base = vars(base)["PRIOR"]
    state = base.load_books()
    state["req"] = base._json(base.newest("VIA_Requirements_SSOT_v*.json"))
    return mod, state


def probe_link(run: str) -> dict:
    mod, state = _sdd_state()
    if mod is None or not hasattr(mod, "back_links"):
        return {"probe": "母子連接", "lamp": "NODATA", "note": "SDD back_links 不在", "items": []}
    miss = mod.back_links(state)
    return {"probe": "母子連接", "lamp": "YELLOW" if miss else "GREEN",
            "note": f"需求 ↔ 工作流單向 {len(miss)} 條" + (" → link --apply 補回指" if miss else "(真雙向)"),
            "items": [f"單向 {x}(link --apply)" for x in miss]}


PROBES = (("交接", probe_handoff), ("全功能串測", probe_test), ("SSOT 全景", probe_ssot), ("SDD", probe_sdd),
          ("編號稽核", probe_numbering), ("GitHub 對齊", probe_github), ("母子連接", probe_link))


def _par(fn, items):
    if VIA_ACCEL is not None and hasattr(VIA_ACCEL, "accel_map"):
        try:
            return [r if ok else {"err": str(r)[:200]} for ok, r in VIA_ACCEL.accel_map(fn, items)]
        except Exception as e:  # 加速器失敗照實退序跑
            print(f"  [加速] accel_map 失敗,退序跑:{e}", file=sys.stderr)
    out = []
    for it in items:
        try:
            out.append(fn(it))
        except Exception as e:
            out.append({"err": str(e)[:200]})
    return out


TEST_ACTIVE = "VIA_VCGC_TEST_ACTIVE"


def pick(args: list, probes) -> list:
    """--only a,b 只跑點名的探針;串測中(VIA_VCGC_TEST_ACTIVE=1)不跑「全功能串測」探針(防遞迴:串測 → gate → 串測)。"""
    keep = list(probes)
    if "--only" in args and args.index("--only") + 1 < len(args):
        want = args[args.index("--only") + 1].split(",")
        keep = [p for p in keep if p[0] in want]
    if os.environ.get(TEST_ACTIVE) == "1":
        keep = [p for p in keep if p[0] != "全功能串測"]
    return keep


def gate(args: list | None = None, probes=PROBES) -> int:
    args = args or []
    probes = pick(args, probes)
    run = "gate-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    t0 = time.time()
    res = _par(lambda p: p[1](run), list(probes))
    rows = []
    for (name, _), r in zip(probes, res):
        if "err" in r:
            r = {"probe": name, "lamp": "RED", "note": f"探針崩:{r['err']}", "items": [f"探針崩 {r['err']}"]}
        r["items"] = [{"kind": classify(x), "text": x} for x in r.get("items") or []]
        rows.append(r)
    verdict = "GREEN" if all(r["lamp"] == "GREEN" for r in rows) else ("RED" if any(r["lamp"] == "RED" for r in rows) else "YELLOW")
    kinds: dict = {}
    for r in rows:
        if r["lamp"] != "GREEN":
            for it in r["items"] or [{"kind": classify(r["note"]), "text": r["note"]}]:
                kinds.setdefault(it["kind"], []).append(f"{r['probe']}:{it['text']}")
    rep = {"schema": "VIA.VCGC.Gate.v1", "engine": Path(__file__).name, "run": run, "at": _now(), "verdict": verdict,
           "secs": round(time.time() - t0, 1), "head": _git("rev-parse", "--short=12", "HEAD")[1].strip(), "probes": rows,
           "blockers": kinds, "remedy": {k: REMEDY[k] for k in kinds},
           "rule": "全部 GREEN 才 GREEN(黃不是綠);非綠逐條分 AUTO / RUN / ENV / OPERATOR / REVIEW;只讀(gate 不寫冊)"}
    GATE_OUT.mkdir(parents=True, exist_ok=True)
    (GATE_OUT / "GATE_latest.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    with open(GATE_OUT / "gate_ledger.jsonl", "a", encoding="utf-8") as f:  # 只增
        f.write(json.dumps({k: rep[k] for k in ("run", "at", "verdict", "secs", "head")} | {"lamps": {r["probe"]: r["lamp"] for r in rows},
                            "blockers": {k: len(v) for k, v in kinds.items()}}, ensure_ascii=False) + "\n")
    if "--json" in args:
        print(json.dumps(rep, ensure_ascii=False, indent=1))
    else:
        print(f"[VCGC 全綠閘] {verdict} · {rep['secs']}s · " + " · ".join(f"{r['probe']} {r['lamp']}" for r in rows))
        for r in rows:
            print(f"  {r['lamp']:<6} {r['probe']:<8} {r['note']}"[:200])
        for k in ("AUTO", "RUN", "ENV", "OPERATOR", "REVIEW"):
            if k in kinds:
                print(f"  [{k}] {len(kinds[k])} 條 → {REMEDY[k]}")
                for x in kinds[k][:6]:
                    print(f"     · {x}"[:220])
        print(f"  記錄 {GATE_OUT / run} · {GATE_OUT / 'GATE_latest.json'}")
    return {"GREEN": 0, "YELLOW": 2}.get(verdict, 1)


# ---------------------------------------------------------------- link:母子自動連接(只增)
def next_version(p: Path) -> Path:
    m = re.search(r"_v(\d{4})\.json$", p.name)
    return p.with_name(re.sub(r"_v\d{4}\.json$", f"_v{int(m.group(1)) + 1:04d}.json", p.name))


def plan_links(state: dict, miss: list) -> dict:
    """單向 'REQ→WKF' → {工作流冊路徑: {工作流代碼: [補的需求]}}。"""
    where = {w.get("code"): state["books"][sub][0] for sub, w in state.get("wkfs") or []}
    plan: dict = {}
    for x in miss:
        req, wkf = x.split("→", 1)
        p = where.get(wkf)
        if p is not None:
            plan.setdefault(Path(p), {}).setdefault(wkf, []).append(req)
    return plan


def write_links(plan: dict, apply: bool) -> list:
    done = []
    for p, adds in plan.items():
        book = json.loads(p.read_text(encoding="utf-8"))
        tgt = next_version(p)
        n = 0
        for w in book.get("workflows") or []:
            for req in adds.get(w.get("code"), []):
                reqs = w.setdefault("spec", {}).setdefault("requirements", [])
                if req not in reqs:
                    reqs.append(req)
                    n += 1
        if not n:
            continue
        v = re.search(r"_v(\d{4})\.json$", tgt.name).group(1)
        book.update(version=f"v{v}", prior=p.name, ts=_now())
        book[f"why_v{v}"] = ("VCGC link(母子自動連接):需求冊歸屬指到本冊工作流 / 步而工作流沒回指 → 補進 spec.requirements(只增):"
                             + " · ".join(f"{k} ← {', '.join(v_)}" for k, v_ in adds.items()) + ";其餘一字不動")
        done.append({"book": p.name, "new": tgt.name, "added": n, "links": adds})
        if apply:
            if tgt.exists():
                raise FileExistsError(f"{tgt.name} 已在(不覆寫;只增)")
            indent = 1 if p.read_text(encoding="utf-8").startswith("{\n \"") else 2
            tgt.write_text(json.dumps(book, ensure_ascii=False, indent=indent) + "\n", encoding="utf-8")
    return done


def link(args: list) -> int:
    apply = "--apply" in args
    mod, state = _sdd_state()
    if mod is None or not hasattr(mod, "back_links"):
        print("[VCGC link] NODATA · SDD back_links 不在")
        return 2
    miss = mod.back_links(state)
    if not miss:
        print("[VCGC link] GREEN · 需求 ↔ 工作流真雙向,沒有要補的")
        return 0
    done = write_links(plan_links(state, miss), apply)
    for d in done:
        print(f"  {d['book']} → {d['new']} · 補回指 {d['added']} 條:" + " · ".join(f"{k} ← {', '.join(v)}" for k, v in d["links"].items()))
    unplaced = len(miss) - sum(d["added"] for d in done)
    print(f"[VCGC link] {'已寫' if apply else '乾跑(--apply 才寫新版冊)'} · 單向 {len(miss)} · 新冊 {len(done)}" + (f" · 找不到工作流冊 {unplaced}" if unplaced else ""))
    return 0 if apply else 2


# ---------------------------------------------------------------- closeout:先連接 · 後全綠閘
def closeout(args: list) -> int:
    strict = "--strict" in args
    args = [a for a in args if a != "--strict"]
    if "--apply" in args:
        print("  ⓪  link(母子自動連接 · 只增)", flush=True)
        link(["--apply"])
    rc = PRIOR.closeout(args)
    if rc == 1:
        return rc
    if os.environ.get(TEST_ACTIVE) == "1":
        print("  ⑩  全綠閘 略過:串測中(防遞迴;串測自己就是全功能檢查)")
        return rc
    print("  ⑩  全綠閘(VCGC 所有功能全綠才往下)", flush=True)
    g = gate([])
    if g == 0:
        print(f"[VCGC closeout + 全綠閘] GREEN · 收尾 rc {rc} · 閘 GREEN")
        return rc
    final = 1 if strict else 2
    print(f"[VCGC closeout + 全綠閘] {'RED' if strict else 'YELLOW'} · 收尾 rc {rc} · 閘 {'YELLOW' if g == 2 else 'RED'} → 黃不是綠:看 [AUTO]/[RUN]/[ENV]/[OPERATOR] 清單")
    return final


# ---------------------------------------------------------------- main
def _auto_monitor(args):
    owner = _owner("auto_monitor")
    if owner is not None:
        try:
            owner.auto_monitor(args)
        except Exception as e:  # 監控不擋
            print(f"  [監控] 略過:{e}", file=sys.stderr)


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] in (["gate"], ["link"], ["closeout"]):
        try:
            if os.environ.get("VIA_FROM_VCGC") != "YES":
                print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
                return 2
            return {"gate": gate, "link": link, "closeout": closeout}[args[0]](args[1:])
        finally:
            _auto_monitor(args)
    return PRIOR.main(args)


# ---------------------------------------------------------------- selftest
def selftest():
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    chk("分類:pwsh = ENV · 鎖 = RUN · 單向 = AUTO · 同詞多義 = OPERATOR · 其他 = REVIEW",
        [classify(x) for x in ("沒有 pwsh:語法沒量", "X-LOCK 已鎖工作流的尾版換了", "單向 VCGC-REQ1→VCGC-WKF001", "同詞多義 10 條", "怪事")]
        == ["ENV", "RUN", "AUTO", "OPERATOR", "REVIEW"])
    here = ["r/A_v0103.py", "r/B_v0102.json", "r/C_v0100.py", "r/D_v0106.json"]
    main_add = ["r/A_v0103.py", "r/B_v0102.json", "r/B_v0105.json", "r/D_v0105.json"]
    got = collisions(here, main_add, main_add)
    chk("GitHub 對齊:同檔兩邊新增 = 撞號;同家族 main 已到 / 超過 = 改編;main 較舊 / 沒碰 = 不算",
        len(got) == 2 and "A_v0103" in got[0] and "B_v0102" in got[1] and not any("C_v0100" in g or "D_v0106" in g for g in got), got)
    clash = req_clash({"requirements": [{"code": "R1", "topic": "x"}, {"code": "R2", "topic": "y"}]},
                      {"requirements": [{"code": "R1", "topic": "x"}, {"code": "R2", "topic": "z"}]})
    chk("需求代碼同號異義 = 撞號(不同來源不合併編號);同號同義不算", clash == ["同號異義 R2"], clash)
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "VIA_Workflow_X_SSOT_v0103.json"
        p.write_text(json.dumps({"version": "v0103", "workflows": [{"code": "X-WKF001", "spec": {"requirements": ["X-REQ001"]}, "steps": [{"code": "X-WKF001-STP001"}]}]},
                                ensure_ascii=False, indent=1), encoding="utf-8")
        state = {"books": {"X": (p, {})}, "wkfs": [("X", {"code": "X-WKF001"})]}
        plan = plan_links(state, ["X-REQ009→X-WKF001", "X-REQ001→X-WKF001", "Y-REQ1→Y-WKF9"])
        dry = write_links(plan, False)
        none_written = not (Path(td) / "VIA_Workflow_X_SSOT_v0104.json").exists()
        done = write_links(plan, True)
        nb = json.loads((Path(td) / "VIA_Workflow_X_SSOT_v0104.json").read_text(encoding="utf-8"))
        old = json.loads(p.read_text(encoding="utf-8"))
        try:
            write_links(plan, True)
            refused = False
        except FileExistsError:
            refused = True
    chk("link:乾跑不寫 · --apply 出新版號檔(prior 指回 · why 寫明)· 只補缺的 · 舊版不動 · 新版已在不覆寫",
        dry and none_written and done[0]["added"] == 1 and nb["workflows"][0]["spec"]["requirements"] == ["X-REQ001", "X-REQ009"]
        and nb["prior"] == p.name and nb["version"] == "v0104" and "why_v0104" in nb and old["workflows"][0]["spec"]["requirements"] == ["X-REQ001"]
        and refused, done)
    global GATE_OUT
    keep = GATE_OUT
    with tempfile.TemporaryDirectory() as td:
        GATE_OUT = Path(td)
        fake = (("a", lambda r: {"probe": "a", "lamp": "GREEN", "note": "ok", "items": []}),
                ("b", lambda r: {"probe": "b", "lamp": "YELLOW", "note": "y", "items": ["沒有 pwsh", "單向 X→Y"]}))
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()):
            rc_y = gate([], fake)
            rep = json.loads((GATE_OUT / "GATE_latest.json").read_text(encoding="utf-8"))
            rc_g = gate([], fake[:1])
            rc_r = gate([], (("c", lambda r: (_ for _ in ()).throw(RuntimeError("boom"))),))
        led = (GATE_OUT / "gate_ledger.jsonl").read_text(encoding="utf-8").splitlines()
    GATE_OUT = keep
    chk("全綠閘:全綠才 rc 0 · 有黃 rc 2 · 探針崩 = 紅 rc 1 · 非綠分類(ENV · AUTO)· 帳只增 3 行",
        rc_g == 0 and rc_y == 2 and rc_r == 1 and set(rep["blockers"]) == {"ENV", "AUTO"} and len(led) == 3, (rc_g, rc_y, rc_r))
    env_t = os.environ.get(TEST_ACTIVE)
    os.environ[TEST_ACTIVE] = "1"
    names_t = [p[0] for p in pick([], PROBES)]
    os.environ.pop(TEST_ACTIVE, None)
    if env_t is not None:
        os.environ[TEST_ACTIVE] = env_t
    names_o = [p[0] for p in pick(["--only", "編號稽核,母子連接"], PROBES)]
    chk("防遞迴:串測中不跑串測探針 · --only 只跑點名的", "全功能串測" not in names_t and len(names_t) == len(PROBES) - 1
        and names_o == ["編號稽核", "母子連接"], (names_t, names_o))
    chk("分類:待重驗鎖 0 不算 RUN(只有單向 = AUTO)", classify("單向 2:VDF-REQ014→VDF-WKF006 · 待重驗鎖 0") == "AUTO")
    src = Path(__file__).read_text(encoding="utf-8")
    chk("closeout:--apply 先 link · 收尾後 ⑩ 全綠閘 · 閘不綠 = YELLOW(--strict = RED)· 不經 VCGC 拒跑",
        "⓪  link" in src and "⑩  全綠閘" in src and "串測中(防遞迴" in src and "final = 1 if strict else 2" in src and 'os.environ.get("VIA_FROM_VCGC") != "YES"' in src)
    env = os.environ.get("VIA_FROM_VCGC")
    seen, real = [], PRIOR.main
    try:
        os.environ.pop("VIA_FROM_VCGC", None)
        PRIOR.main = lambda a: seen.append(list(a)) or 0
        owner = _owner("auto_monitor")
        real_auto = owner.auto_monitor if owner else None
        if owner:
            owner.auto_monitor = lambda a, launcher=None: "stub"
        denied = main(["gate"])
        passthru = main(["status"])
    finally:
        PRIOR.main = real
        if owner:
            owner.auto_monitor = real_auto
        if env is not None:
            os.environ["VIA_FROM_VCGC"] = env
    chk("gate / link 不經 VCGC 拒跑 · 其他動詞原樣轉交 v0184", denied == 2 and passthru == 0 and seen == [["status"]], seen)
    card = help_catalog()
    chk("help 目前生效入口 = 本版 · 多 gate / link 兩行", card.get("entry") == Path(__file__).name and "gate" in card and "link" in card)
    chk("加速器橋 · 網路橋在 · 探針並行走 accel_map", "[VIA:ACCEL-BRIDGE" in src and "[VIA:NET-BRIDGE" in src and "accel_map" in src)
    print(f"  VCGC v0185 selftest {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}")
    if not all(ok):
        return 1
    _patch_help(False)
    try:
        return PRIOR.selftest()
    finally:
        _patch_help(True)


if __name__ == "__main__":
    raise SystemExit(selftest() if sys.argv[1:] == ["--selftest"] else main())
