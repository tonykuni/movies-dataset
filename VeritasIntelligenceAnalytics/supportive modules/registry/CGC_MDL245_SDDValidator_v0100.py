#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""CGC_MDL245_SDDValidator v0100 — SDD 驗證器:工作流 SSOT 的自測 · 交叉測 · 實測 · 加鎖 · 收尾(只收 VIA_FROM_VCGC 呼叫)

操作員 R33:「Implement SDD structures and build up workflow SSOT … keep them a code VCGC-WKF001 … integrate and consolidate and
removing redundancy … SSOT without conflict … build up complete self testing, cross testing, output validating SSOT … a fixed
successful versions registered auto sync synchronizing with SSOT to prevent any missing … when the results and output are validated
by the validation process SSOT, indicating we close out this project.」
SDD 五層:spec(目標 · 需求 REQ · 驗收)→ plan(進出口 · 順序 · 正主)→ steps(STP 代碼 · 引擎 · 動詞 · 中樞觀測鍵)→ tests(self · cross · real)
→ validation(本支)。冊 = 中樞組成冊 VIA_Workflow_Hub_SSOT 尾版 + 它 books 指名的子系統工作流冊(VCGC · VDF · VRN · VAP)+ 需求冊。
動詞:
  check        靜態自測 + 交叉測(X-COL 欄位齊 · X-CODE 代碼 · X-COMP 組成 · X-ENGINE 正主尾版 · X-ACCEL 標準橋 · X-REG 註冊 ·
               X-NUM 編號 · X-ITEM 項鏈 · X-OLD 舊冊整併 · X-OWNER 引用正主一致 · X-REQ 需求雙向 · X-CONFLICT SSOT 衝突(中央參數樞紐正主重算)·
               X-PARAM 參數冗餘(只報)· X-LOCK 已鎖尾版有沒有換)→ VIA_Reports/sdd/SDD_CHECK_latest.json;紅 rc 1 · 黃 rc 2 · 綠 rc 0
  selftests    每一步正主的尾版 --selftest,一律經 VCGC run(閘只跑一次,事件帶輪號 sdd-self-…)→ SDD_SELF_latest.json
  real [輪號]  讀唯一入口那一輪(go-…)的中樞事件,逐工作流逐步:有跑 · 結果類 · 時間;VDF / VRN 迴圈附鏈上未綠項與是不是操作員端
  lock [--apply]     靜態不紅且 OK 的工作流 → 燈鎖冊下一版 wkf 區(步正主尾版 · 編號 · 註冊時間);其餘進 wkf_open 附原因
  closeout [--apply] 收尾判定:CLOSED / CLOSED_WITH_OPERATOR_ITEMS(剩下的都是同意閘 · 缺套件 · 沒料)/ OPEN;--apply 寫 docs 報告
不改任何正主;只寫 VIA_Reports/sdd(不入 git)與 lock / closeout 的 --apply 產出(燈鎖冊下一版 · docs 報告)。
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
ENGINE = Path(__file__).stem
OUT = VIA / "VIA_Reports" / "sdd"
EVENTS = VIA / "VIA_Reports" / "vcgc" / "events"
CONSOLE = "CGC_MDL149_VeritasCentralGovernanceConsole"
WKF_RX = re.compile(r"^(VCGC|VDF|VRN|VAP)-WKF(\d{3})$")
REQ_RX = re.compile(r"^(VCGC|VDF|VRN|VAP|SUP|CORE)-REQ(\d{3})$")
LAW_RX = re.compile(r"^L\d{2,3}$")
WKF_COLS = ("code", "alias", "name", "kind", "spec", "plan", "steps", "tests")
EVIDENCE_RX = re.compile(r"^(step:[A-Z]+-WKF\d{3}-STP\d{3}|self:(all|[A-Za-z0-9_]+)|chain:(vdf|vrn):\S+|git:pushed)$")
CHAIN_STATE = {"GREEN": "OK", "INFO": "OK", "GATED": "FINDING", "ABSENT": "FINDING", "NODATA": "FINDING", "SKIP": "FINDING"}
SPEC_COLS = ("goal", "requirements", "acceptance")
TEST_COLS = ("self", "cross", "real")
OPERATOR_HAND = {"CANON": "正本唯讀(不改、無獨立自測門;實測走匯流排 call --item,需資料家)","GATED": "同意閘沒開(L07/L08:只有操作員能開)", "ABSENT": "缺套件或缺件(裝件是操作員的手)",
                 "NODATA": "沒料或逾時(資料家空 · 樣本不在 · 工作站逾時)", "SKIP": "本次略過"}


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", path.stem)
    return int(m.group(1)) if m else -1


def newest(pattern: str, folder: Path = HERE) -> Path | None:
    hits = sorted(folder.glob(pattern), key=_vnum)
    return hits[-1] if hits else None


def _json(p: Path | None, default=None):
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p else default
    except (OSError, ValueError):
        return default


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def rel(p: Path) -> str:
    return p.resolve().relative_to(VIA.resolve()).as_posix()


def stem_of(p: Path | str) -> str:
    return re.sub(r"_v\d+$", "", Path(str(p)).stem)


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _head() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=VIA, capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception:
        return ""


# ------------------------------------------------------------------ books and composition (the one place both VCGC and this engine read)
def load_books() -> dict:
    hub_p = newest("VIA_Workflow_Hub_SSOT_v*.json")
    comp = _json(hub_p, {}) or {}
    books = {}
    for sub, pattern in (comp.get("books") or {}).items():
        p = newest(Path(pattern).name)
        books[sub] = (p, _json(p, {}) or {})
    wkfs = [(sub, w) for sub, (p, b) in books.items() for w in b.get("workflows") or []]
    return {"hub_path": hub_p, "comp": comp, "books": books, "wkfs": wkfs, "by_code": {w.get("code"): (sub, w) for sub, w in wkfs}}


def compose(state: dict | None = None) -> dict:
    """Hub-compatible book (hub · loop_vdf · loop_vrn · exit · conformance) assembled from the composition's sequence;
    step id = its alias (H1 … X4, what the conformance messages name), code = its STP code."""
    s = state or load_books()
    comp = s["comp"]
    if "sequence" not in comp:                      # an older hub book with inline steps: use it as it is
        return comp
    out = {k: comp[k] for k in ("model", "executor", "conformance", "grading") if k in comp}
    for part in comp["sequence"]:
        _, w = s["by_code"].get(part["wkf"], (None, None))
        steps = []
        for st in (w or {}).get("steps") or []:
            x = {"id": st.get("alias") or st["code"], "code": st["code"], "name": st.get("name", ""), "alias": st.get("alias")}
            for k in ("match", "inside", "after_gate", "engine", "verb"):
                if k in st:
                    x[k] = st[k]
            steps.append(x)
        if part["section"] in ("loop_vdf", "loop_vrn"):
            out[part["section"]] = {"wkf": part["wkf"], "steps": steps}
        else:
            out[part["section"]] = steps
    return out


# ------------------------------------------------------------------ resolution
def resolve(pattern: str) -> Path | None:
    """An engine pattern (relative to VIA; `_v*` = tail) → the file; None when absent. Non-path owners (git · GitHub) → None."""
    if not pattern or "/" not in pattern or not pattern.endswith((".py", ".ps1", ".json")):
        return None
    if "*" in pattern:
        return newest(Path(pattern).name, VIA / Path(pattern).parent)
    p = VIA / pattern
    return p if p.exists() else None


def is_external(pattern: str) -> bool:
    return not pattern or "/" not in pattern or not pattern.endswith((".py", ".ps1", ".json"))


def spec_items() -> dict:
    spec = _json(newest("VIA_InputConsole_Spec_v*.json"), {}) or {}
    out = {}
    for fam, f in (spec.get("families") or {}).items():
        for g in f.get("groups") or []:
            for it in g.get("items") or []:
                if it.get("id"):
                    out[it["id"]] = dict(it, _family=fam)
    return out


def item_tail(it: dict) -> Path | None:
    eng = it.get("engine") or {}
    if isinstance(eng, dict) and eng.get("glob"):
        return newest(eng["glob"], VIA / (eng.get("dir") or "."))
    return None


def step_targets(state: dict, items: dict | None = None) -> list:
    """Every (wkf code, step code, pattern-or-item, tail path | None, family) the books name."""
    items = spec_items() if items is None else items
    out = []
    for sub, w in state["wkfs"]:
        for st in w.get("steps") or []:
            if st.get("item"):
                it = items.get(st["item"]) or {}
                out.append((w["code"], st["code"], "item:" + st["item"], item_tail(it) if it else None, it.get("_family") or sub.lower()))
            elif st.get("engine"):
                for p in (st["engine"] if isinstance(st["engine"], list) else [st["engine"]]):
                    fam = "vdf" if "/VDF/" in "/" + p else ("vrn" if "/VRN/" in "/" + p else "core")
                    out.append((w["code"], st["code"], p, resolve(p), fam))
    return out


# ------------------------------------------------------------------ static checks (self + cross)
def _row(rows, lamp, rule, msg, ref=""):
    rows.append({"lamp": lamp, "rule": rule, "msg": msg, "ref": ref})


def check_columns(state, rows):
    for sub, w in state["wkfs"]:
        miss = [c for c in WKF_COLS if not w.get(c)]
        miss += ["spec." + c for c in SPEC_COLS if c not in (w.get("spec") or {})]
        miss += ["tests." + c for c in TEST_COLS if not (w.get("tests") or {}).get(c)]
        for st in w.get("steps") or []:
            if not st.get("code") or not st.get("alias"):
                miss.append(f"{st.get('code') or '?'}.code/alias")
            if not (st.get("item") or st.get("station") or st.get("layer") or st.get("engine")):
                miss.append(f"{st.get('code')}.engine|item|station|layer")
            if st.get("engine") and not (st.get("verb") and st.get("what") and (st.get("match") or st.get("inside"))):
                miss.append(f"{st.get('code')}.verb/what/match|inside")
            if (st.get("inside") or st.get("station") or st.get("layer")) and not EVIDENCE_RX.match(str(st.get("evidence") or "")):
                miss.append(f"{st.get('code')}.evidence(step:|self:|chain:|git:pushed)")
        if miss:
            _row(rows, "RED", "X-COL", f"{w.get('code')} 欄位不齊:{', '.join(miss[:6])}", w.get("code"))
    if not any(r["rule"] == "X-COL" for r in rows):
        _row(rows, "GREEN", "X-COL", f"{len(state['wkfs'])} 條工作流 · 每條 spec/plan/steps/tests 欄位齊 · 每步代碼 · alias · 正主齊")


def check_codes(state, rows):
    seen, bad = {}, []
    for sub, (p, b) in state["books"].items():
        codes = [w.get("code") for w in b.get("workflows") or []]
        for i, c in enumerate(codes, 1):
            m = WKF_RX.match(c or "")
            if not m or m.group(1) != sub or int(m.group(2)) != i:
                bad.append(f"{c}(冊 {sub} 第 {i} 條)")
        for w in b.get("workflows") or []:
            got = sorted(st.get("code") or "" for st in w.get("steps") or [])      # codes are identity (append-only); list order is the plan
            want = [f"{w.get('code')}-STP{j:03d}" for j in range(1, len(w.get("steps") or []) + 1)]
            if got != want:
                bad.append(f"{w.get('code')} 步代碼不連續 {sorted(set(want) ^ set(got))[:3]}")
            for c in [w.get("code")] + [st.get("code") for st in w.get("steps") or []]:
                if c in seen:
                    bad.append(f"{c} 重複({seen[c]} · {sub})")
                seen[c] = sub
    aliases = {}
    for sub, w in state["wkfs"]:
        aliases.setdefault(w.get("alias"), []).append(w.get("code"))
    bad += [f"alias {a} 重複 {c}" for a, c in aliases.items() if len(c) > 1]
    if bad:
        _row(rows, "RED", "X-CODE", "代碼不合格式 / 跳號 / 重複:" + " · ".join(bad[:6]))
    else:
        _row(rows, "GREEN", "X-CODE", f"代碼 {len(seen)} 個:<子系統>-WKF### 各冊從 001 連續 · 步 -STP### 集合連續(代碼是身分,清單順序是執行序)· 全域唯一 · alias 唯一")


def check_composition(state, rows):
    comp = state["comp"]
    seq = comp.get("sequence") or []
    bad = [p["wkf"] for p in seq if p.get("wkf") not in state["by_code"]]
    secs = [p.get("section") for p in seq]
    if bad or sorted(secs) != sorted(["hub", "loop_vdf", "loop_vrn", "exit"]):
        _row(rows, "RED", "X-COMP", f"組成冊 sequence 指到不存在的工作流 {bad} 或段不齊 {secs}")
        return
    book = compose(state)
    hub = book.get("hub") or []
    gate_first = any(st.get("alias") == "H1" or any(m[1] == "status" for m in st.get("match") or []) for st in hub)
    no_key = [st["id"] for sec in ("hub", "exit") for st in book.get(sec) or []] + []
    no_key = [st["id"] for sec in ("hub", "exit") for st in book.get(sec) or [] if not (st.get("match") or st.get("inside"))]
    no_key += [st["id"] for sec in ("loop_vdf", "loop_vrn") for st in (book.get(sec) or {}).get("steps") or [] if not (st.get("match") or st.get("inside"))]
    if not gate_first or no_key:
        _row(rows, "RED", "X-COMP", f"組成後中樞段沒有流程閘步 或 步沒有中樞觀測鍵:{no_key[:5]}")
    else:
        _row(rows, "GREEN", "X-COMP", "組成 = " + " → ".join(f"{p['section']}:{p['wkf']}" for p in seq) + " · 有流程閘 · 每步有 match 或 inside")


_EXEMPT: dict = {}


def exemption(p: Path) -> str:
    """Why a tail is out of scope for bridges / numbering — asked of the owners (bridge sweeper _excluded · numbering NOT_LIVE)."""
    key = str(p)
    if key not in _EXEMPT:
        why = ""
        try:
            sw = _EXEMPT.get("_sweeper") or _load(newest("CGC_MDL124_BridgeSweeper_v*.py"), "sweeper_for_sdd")
            _EXEMPT["_sweeper"] = sw
            why = sw._excluded(p) if p.suffix == ".py" else ""
        except Exception:
            why = ""
        if str(why).startswith("未在冊"):          # not committed yet is not an exemption: the check after commit must see it
            why = ""
        if not why and any(x in rel(p) for x in ("references/", "VIA_RetiredEngines")):
            why = "正本唯讀(references/;編號系統 NOT_LIVE)"
        _EXEMPT[key] = why
    return _EXEMPT[key]


def check_engines(state, rows, targets):
    miss, accel, net, ps, exempt = [], [], [], [], set()
    for wkf, stp, pat, p, fam in targets:
        if p is None:
            if pat.startswith("item:") or not is_external(pat):
                miss.append(f"{stp} {pat}")
            continue
        if p.suffix == ".json":
            continue
        if exemption(p):
            exempt.add(f"{p.name}({exemption(p)})")
            continue
        txt = p.read_text(encoding="utf-8", errors="replace")
        if p.suffix == ".py":
            if "[VIA:ACCEL-BRIDGE" not in txt:
                accel.append(p.name)
            if rel(p).startswith("functional modules/VDF/") and "[VIA:NET-BRIDGE" not in txt:
                net.append(p.name)
        elif p.suffix == ".ps1" and "CELERITAS-TEMPLATE-JOIN" not in txt:
            ps.append(p.name)
    n = len({str(t[3]) for t in targets if t[3]})
    _row(rows, "RED" if miss else "GREEN", "X-ENGINE", f"步的正主尾版找不到:{miss[:6]}" if miss else f"每步正主都找得到尾版({n} 支,含項鏈經輸入台規格冊解析)")
    bad = sorted(set(accel)) + [f"{x}(網路橋)" for x in sorted(set(net))] + [f"{x}(PS 模板章)" for x in sorted(set(ps))]
    _row(rows, "RED" if bad else "GREEN", "X-ACCEL",
         ("缺標準橋:" + " · ".join(bad[:8])) if bad else "每支 .py 尾版帶加速器橋 · VDF .py 帶網路橋 · .ps1 帶 PS 模板章(最新加速器由橋載入)"
         + (f";豁免 {len(exempt)} 支(橋掃正主判定):{' · '.join(sorted(exempt))[:200]}" if exempt else ""))


def _registers():
    reg = _json(HERE / "VIA_Component_Inventory_SSOT_v0100.json", {}) or {}
    by_id = {}
    for r in reg.get("records") or []:
        if r.get("category") in ("module", "engine", "tool") and r.get("state") == "ACTIVE":
            by_id.setdefault(r.get("identity"), r)
    num = {}
    for kind in ("MDL", "ENG", "PLCY"):
        p = newest(f"VIA_NumberBook_{kind}_v*.jsonl", HERE / "VIA_NumberBooks")
        for line in (p.read_text(encoding="utf-8").splitlines() if p else []):
            if line.strip():
                r = json.loads(line)
                if not r.get("gone_since"):
                    num[r.get("source")] = r
    nssot = _json(newest("VIA_Numbering_SSOT_v*.json"), {}) or {}
    for r in (nssot.get("rows") or {}).get("SSOT") or []:
        num.setdefault(r.get("source"), r)
    return by_id, num


def check_registration(state, rows, targets, versions: dict):
    by_id, num = _registers()
    unreg, stale, unnum, canon = [], [], [], []
    for wkf, stp, pat, p, fam in {(None, None, None, t[3], None) for t in targets if t[3]}:
        r = rel(p)
        if exemption(p) and not by_id.get(stem_of(p)) and not num.get(r):
            canon.append(p.name)
            versions[r] = {"tail": p.name, "exempt": exemption(p)}
            continue
        if p.suffix != ".json":
            reg = by_id.get(stem_of(p))
            if not reg:
                unreg.append(p.name)
            elif reg.get("source") != r:
                stale.append(f"{p.name}(冊上 {Path(str(reg.get('source'))).name})")
        n = num.get(r)
        if not n:
            unnum.append(p.name)
        versions[r] = {"tail": p.name, "code": (n or {}).get("code"), "numbered_at": (n or {}).get("numbered_at"),
                       "registered": (by_id.get(stem_of(p)) or {}).get("code"),
                       "first_seen": (by_id.get(stem_of(p)) or {}).get("first_seen"),
                       "changed_at": (by_id.get(stem_of(p)) or {}).get("changed_at")}
    if unreg or stale:
        _row(rows, "RED", "X-REG", f"未註冊 {unreg[:4]} · 註冊冊不是尾版(待 registry-sync --apply){stale[:4]}")
    else:
        _row(rows, "GREEN", "X-REG", f"步的正主都在元件註冊冊且登記的就是尾版({len(versions) - len(canon)} 支;帶註冊碼與時間)"
             + (f";正本唯讀不入冊 {len(canon)} 支:{' · '.join(canon)}" if canon else ""))
    if unnum:
        _row(rows, "RED", "X-NUM", f"尾版沒編號(待 CGC_MDL237 --apply):{unnum[:6]}")
    else:
        _row(rows, "GREEN", "X-NUM", f"步的正主尾版都有編號與編號時間({len(versions) - len(canon)} 支)" + (f";正本唯讀 {len(canon)} 支不編(NOT_LIVE)" if canon else ""))
    sdd_num = {}
    for kind in ("WKF", "STP", "REQ"):
        p = newest(f"VIA_NumberBook_{kind}_v*.jsonl", HERE / "VIA_NumberBooks")
        for line in (p.read_text(encoding="utf-8").splitlines() if p else []):
            if line.strip():
                r = json.loads(line)
                sdd_num[r.get("declared")] = r
    codes = [w["code"] for _, w in state["wkfs"]] + [s["code"] for _, w in state["wkfs"] for s in w.get("steps") or []]
    codes += [r.get("code") for r in (state.get("req") or {}).get("requirements") or []]
    missing = [c for c in codes if c not in sdd_num]
    wrong = [c for c in codes if c in sdd_num and (sdd_num[c].get("code") != "VIA-" + c or sdd_num[c].get("lamp") == "RED")]
    if wrong:
        _row(rows, "RED", "X-NUM", f"編號冊號碼 ≠ 冊上代碼:{wrong[:6]}")
    elif missing:
        _row(rows, "RED", "X-NUM", f"WKF/STP/REQ 還沒編號(待 CGC_MDL237 v0104 --apply):{len(missing)} 個,例 {missing[:4]}")
    else:
        _row(rows, "GREEN", "X-NUM", f"WKF · STP · REQ {len(codes)} 個全編號,號碼 = VIA- + 冊上代碼")


def check_items_and_old(state, rows, items):
    old = _json(HERE / "VIA_Workflow_SSOT_v0100.json", {}) or {}
    bad_item = [f"{w['code']}:{st['item']}" for _, w in state["wkfs"] for st in w.get("steps") or [] if st.get("item") and st["item"] not in items]
    _row(rows, "RED" if bad_item else "GREEN", "X-ITEM", f"項鏈指到輸入台規格冊沒有的項:{bad_item[:6]}" if bad_item else "項鏈每一項都在輸入台規格冊(引擎與參數的正主)")
    by_alias = {w.get("alias"): w for _, w in state["wkfs"]}
    drift = []
    for ow in old.get("workflows") or []:
        w = by_alias.get(ow["id"])
        if not w:
            drift.append(f"{ow['id']} 沒被整併")
        elif [st.get("item") for st in w.get("steps") or []] != ow.get("nodes"):
            drift.append(f"{ow['id']} 項序不一致")
    hub0 = _json(HERE / "VIA_Workflow_Hub_SSOT_v0100.json", {}) or {}
    old_steps = (hub0.get("hub") or []) + (hub0.get("loop_vdf") or {}).get("steps", []) + (hub0.get("loop_vrn") or {}).get("steps", []) + (hub0.get("exit") or [])
    new_by = {(w["code"].split("-")[0], st.get("alias")): st for _, w in state["wkfs"] for st in w.get("steps") or [] if w.get("kind") == "hub_steps"}
    for os_ in old_steps:
        sub = "VDF" if os_["id"].startswith("D") else ("VRN" if os_["id"].startswith("R") else "VCGC")
        ns = new_by.get((sub, os_["id"]))
        if not ns:
            drift.append(f"中樞冊 v0100 {os_['id']} 沒有對應步")
        elif any(ns.get(k) != os_.get(k) for k in ("engine", "verb", "match", "inside")):
            drift.append(f"{os_['id']} → {ns['code']} 引擎/動詞/觀測鍵不一致")
    _row(rows, "RED" if drift else "GREEN", "X-OLD", ("整併有落差:" + " · ".join(drift[:6])) if drift else
         f"舊冊整併無落差:VIA_Workflow_SSOT_v0100 {len(old.get('workflows') or [])} 條項序一致 · 中樞冊 v0100 {len(old_steps)} 步引擎/動詞/觀測鍵一致(舊冊凍結,讀舊冊的引擎照舊)")


def check_owners(state, rows):
    probs = []
    runner = newest("CGC_MDL170_VDFChainRunner_v*.py")
    try:
        chain = ["0a", "0b", "0c"] + [c[0] for c in _load(runner, "vdf_runner_for_sdd").CHAIN]
    except Exception as exc:
        chain, probs = None, [f"讀不到 VDF 跑器站表:{type(exc).__name__}"]
    for _, w in state["wkfs"]:
        if w.get("kind") != "owner_ref":
            continue
        mine = [st.get("station") or st.get("layer") for st in w.get("steps") or []]
        if any(st.get("station") for st in w.get("steps") or []):
            if chain is not None and mine != chain:
                probs.append(f"{w['code']} 站表 {mine} ≠ 跑器 {chain}")
        else:
            arch = _json(newest("VIA_VRN_LogicArchitecture_SSOT_v*.json"), {}) or {}
            layers = [k.split("_")[0] for k in (arch.get("layers") or {})]
            if mine != layers:
                probs.append(f"{w['code']} 層序 {mine} ≠ 邏輯架構冊 {layers}")
    _row(rows, "RED" if probs else "GREEN", "X-OWNER", " · ".join(probs) if probs else "引用正主的清單一致:VDF 站表 = 跑器 CHAIN · VRN 層序 = 邏輯架構冊 layers")


def check_requirements(state, rows):
    req = state.get("req")
    if not req:
        _row(rows, "YELLOW", "X-REQ", "需求冊 VIA_Requirements_SSOT 尾版不在")
        return
    reqs = req.get("requirements") or []
    by_sub, bad, orphan_home = {}, [], []
    codes = {r.get("code") for r in reqs}
    all_codes = set(state["by_code"]) | {st["code"] for _, w in state["wkfs"] for st in w.get("steps") or []}
    laws = {l.get("id") for l in (_json(HERE / "VIA_Policy_Laws_SSOT_v0100.json", {}) or {}).get("laws") or [] if isinstance(l, dict)}
    for r in reqs:
        m = REQ_RX.match(r.get("code") or "")
        if not m:
            bad.append(str(r.get("code")))
            continue
        by_sub.setdefault(m.group(1), []).append(int(m.group(2)))
        for h in r.get("homes") or []:
            if not (h in all_codes or (LAW_RX.match(h) and (not laws or h in laws)) or h.startswith(("VIA_", "CLAUDE.md", "docs/", "Master"))):
                orphan_home.append(f"{r['code']}→{h}")
        if not r.get("homes"):
            orphan_home.append(f"{r['code']}→(無)")
    for sub, ns in by_sub.items():
        if sorted(ns) != list(range(1, len(ns) + 1)):
            bad.append(f"{sub}-REQ 跳號")
    back = [f"{w['code']}→{c}" for _, w in state["wkfs"] for c in (w.get("spec") or {}).get("requirements") or [] if c not in codes]
    no_req = [w["code"] for _, w in state["wkfs"] if w.get("kind") in ("hub_steps", "procedure") and not (w.get("spec") or {}).get("requirements")]
    open_ = [r["code"] for r in reqs if r.get("status") not in ("COVERED", "RECORDED")]
    if bad or orphan_home or back:
        _row(rows, "RED", "X-REQ", f"需求代碼不合 {bad[:4]} · 歸屬指到不存在 {orphan_home[:4]} · 工作流引用不存在的需求 {back[:4]}")
    elif no_req:
        _row(rows, "YELLOW", "X-REQ", f"主流程工作流還沒掛需求:{no_req}")
    else:
        _row(rows, "GREEN", "X-REQ", f"需求 {len(reqs)} 條 · 代碼連續唯一 · 每條有歸屬(工作流步 / 律 / 冊)· 主流程工作流都掛需求(雙向)")
    if open_:
        _row(rows, "YELLOW", "X-REQ-OPEN", f"需求未全落地 {len(open_)} 條(PARTIAL / MISSING,各有歸屬與下一步):{open_[:10]}")


def check_conflicts(state, rows):
    p = newest("via_params_central_v*.py")
    try:
        m = _load(p, "params_central_for_sdd")
        import io
        import contextlib
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            recs = [m.scan_book(b, VIA) for b in m.BOOKS]
            conf = m.find_conflicts(recs)
            locked = m.locked_alignment(recs)
        drift = [a["name"] for a in locked if a.get("state") == "DRIFT"]
        fail = [r["id"] for r in recs if r.get("state") == "FAIL"]
        if conf or drift or fail:
            _row(rows, "RED", "X-CONFLICT", f"SSOT 衝突 {len(conf)}(例 {[c['key'] for c in conf[:3]]})· 鎖定正規式漂移 {drift[:3]} · 冊讀不動 {fail[:3]}")
        else:
            _row(rows, "GREEN", "X-CONFLICT", f"SSOT 無衝突:中央參數樞紐 {p.name} 重算 {len(recs)} 本 · 衝突 0 · 鎖定正規式 {len(locked)} 條全對齊")
    except Exception as exc:
        _row(rows, "YELLOW", "X-CONFLICT", f"中央參數樞紐讀不動:{type(exc).__name__}: {str(exc)[:80]}")


def param_redundancy(rows):
    p = newest("VIA_NumberBook_PRMT_v*.jsonl", HERE / "VIA_NumberBooks")
    live = [json.loads(l) for l in (p.read_text(encoding="utf-8").splitlines() if p else []) if l.strip()]
    live = [r for r in live if not r.get("gone_since")]
    by = {}
    for r in live:
        by.setdefault(r.get("name"), set()).add(str(r.get("note")))
    dup = {k: v for k, v in by.items() if sum(1 for r in live if r.get("name") == k) > 1}
    same = sum(1 for v in dup.values() if len(v) == 1)
    _row(rows, "INFO", "X-PARAM", f"參數 {len(live)} 列 · 同名出現在多支模組 {len(dup)} 名(同值 {same} · 值不同 {len(dup) - same});"
         "模組內常數同名不是 SSOT 衝突(各自作用域),收進中央冊要逐支開新版,Master Prompt 禁止自動套 AST 修補 → 列為建議不自動改")


def check_lock(state, rows, versions):
    lk = newest("VIA_LampLock_v*.json")
    book = _json(lk, {}) or {}
    wkf = book.get("wkf") or {}
    if not wkf:
        _row(rows, "INFO", "X-LOCK", f"燈鎖冊 {lk.name if lk else '-'} 還沒有 wkf 區(第一次 lock 之後才有)")
        return
    moved = []
    for code, rec in wkf.items():
        for r, v in (rec.get("versions") or {}).items():
            cur = (versions.get(r) or {}).get("tail")
            if cur and cur != v:
                moved.append(f"{code}:{v}→{cur}")
    _row(rows, "YELLOW" if moved else "GREEN", "X-LOCK", f"已鎖工作流的尾版換了,要重驗:{moved[:6]}" if moved else
         f"已鎖 {len(wkf)} 條工作流,尾版都沒換({lk.name})")


def check(write: bool = True) -> dict:
    t0 = time.time()
    state = load_books()
    state["req"] = _json(newest("VIA_Requirements_SSOT_v*.json"))
    items = spec_items()
    targets = step_targets(state, items)
    rows, versions = [], {}
    check_columns(state, rows)
    check_codes(state, rows)
    check_composition(state, rows)
    check_engines(state, rows, targets)
    check_registration(state, rows, targets, versions)
    check_items_and_old(state, rows, items)
    check_owners(state, rows)
    check_requirements(state, rows)
    check_conflicts(state, rows)
    param_redundancy(rows)
    check_lock(state, rows, versions)
    lamp = "RED" if any(r["lamp"] == "RED" for r in rows) else ("YELLOW" if any(r["lamp"] == "YELLOW" for r in rows) else "GREEN")
    rep = {"schema": "VIA.SDD.Check.v1", "engine": ENGINE, "ts": _now(), "head": _head()[:12], "lamp": lamp, "secs": round(time.time() - t0, 1),
           "books": {s: p.name for s, (p, _) in state["books"].items() if p}, "hub": state["hub_path"].name if state["hub_path"] else None,
           "workflows": len(state["wkfs"]), "steps": sum(len(w.get("steps") or []) for _, w in state["wkfs"]),
           "requirements": len((state.get("req") or {}).get("requirements") or []), "rows": rows, "versions": versions}
    if write:
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "SDD_CHECK_latest.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    return rep


# ------------------------------------------------------------------ self tests of every step engine (through the hub) and the real run
def _console() -> Path | None:
    return newest(CONSOLE + "_v*.py")


def _gate_env() -> dict:
    """Run the flow gate once (VCGC status) and hand the pass to the children (same HEAD, 15 min) — the entry's own rule."""
    env = dict(os.environ, VIA_FROM_VCGC="YES", VIA_VCGC_PUSH=os.environ.get("VIA_VCGC_PUSH", "NO"))
    head = _head()
    if env.get("VIA_GATE_PASSED_HEAD") == head and time.time() - float(env.get("VIA_GATE_PASSED_AT") or 0) < 900:
        return env
    r = subprocess.run([sys.executable, str(_console()), "status"], cwd=str(HERE), env=env, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=1800)
    line = next((l.strip() for l in r.stdout.splitlines() if re.search(r"\[流程\]\s*政策過", l)), "")
    if not line:
        raise SystemExit("  [SDD] 流程閘沒過(沒讀到「[流程] 政策過」)→ 依 PSGATE-1 停")
    env.update(VIA_GATE_PASSED_HEAD=head, VIA_GATE_PASSED_AT=str(time.time()), VIA_GATE_PASSED_LINE=line)
    return env


def selftests(only: str | None = None, timeout: int = 600, write: bool = True) -> dict:
    state = load_books()
    targets = [t for t in step_targets(state) if t[3] is not None and t[3].suffix == ".py" and (not only or t[0] == only)]
    env = _gate_env()
    run = "sdd-self-" + datetime.now().strftime("%Y%m%d-%H%M%S")
    env["VIA_HUB_RUN"] = run
    done, per_wkf = {}, {}
    for wkf, stp, pat, p, fam in targets:
        key = str(p)
        if key not in done:
            if exemption(p):                      # read-only canon: not run standalone, not changed (its item runs through the bus)
                done[key] = {"tail": p.name, "rel": rel(p), "rc": None, "outcome": "CANON", "secs": 0, "last": exemption(p)}
            else:
                t0 = time.time()
                try:
                    r = subprocess.run([sys.executable, str(_console()), "run", "--family", fam, str(p), "--selftest"], cwd=str(HERE), env=env,
                                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
                    rc, tail = r.returncode, [l for l in (r.stdout + r.stderr).splitlines() if l.strip()][-1:]
                except subprocess.TimeoutExpired:
                    rc, tail = 124, ["逾時"]
                done[key] = {"tail": p.name, "rel": rel(p), "rc": rc, "outcome": "OK" if rc == 0 else ("FINDING" if rc in (2, 3, 4) else "FAIL"),
                             "secs": round(time.time() - t0, 1), "last": (tail[0] if tail else "")[:160]}
            print(f"  [自測] {done[key]['outcome']:<10} rc={done[key]['rc']} {done[key]['secs']:>6}s {p.name}")
            sys.stdout.flush()
        per_wkf.setdefault(wkf, {})[stp] = done[key]["outcome"]
    rep = {"schema": "VIA.SDD.Self.v1", "engine": ENGINE, "ts": _now(), "head": _head()[:12], "run": run, "engines": list(done.values()),
           "wkf": {w: ("FAIL" if "FAIL" in s.values() else "FINDING" if "FINDING" in s.values() else "OK") for w, s in per_wkf.items()},
           "per_step": per_wkf}
    if write:
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / ("SDD_SELF_latest.json" if not only else f"SDD_SELF_{only}.json")).write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    return rep


def run_events(run: str | None, prefix: str = "go-") -> tuple:
    rows = []
    for f in sorted(EVENTS.glob("EVENTS_*.jsonl"))[-3:]:
        for line in f.read_text(encoding="utf-8").splitlines():
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if e.get("run"):
                rows.append(e)
    if not run:
        gos = [e for e in rows if str(e.get("run")).startswith(prefix)]
        run = max(gos, key=lambda e: e.get("t0") or 0)["run"] if gos else ""
    return run, sorted((e for e in rows if e.get("run") == run), key=lambda e: e.get("t0") or 0)


def _chain_states() -> dict:
    out = {}
    for name, f in (("vdf", "vdf_chain/VDFCHAIN_latest.json"), ("vrn", "vrn_chain/VRNCHAIN_latest.json")):
        d = _json(VIA / "VIA_Reports" / f, {}) or {}
        rows = d.get("stages") or d.get("nodes") or []
        out[name] = {"generated": d.get("generated"), "tally": d.get("tally"),
                     "open": [{"id": r.get("id") or r.get("name"), "state": r.get("state"), "why": OPERATOR_HAND.get(r.get("state"), "要修"),
                               "detail": str(r.get("detail") or "")[:100]} for r in rows if isinstance(r, dict) and r.get("state") not in ("GREEN", "INFO")]}
    return out


WORST = {"FAIL": 3, "FINDING": 2, "OK": 1}


def _act(e: dict) -> tuple:
    """(act, act with its sub-verb): run → target's first non-dash arg; console verbs → the verb (and `verb sub`)."""
    if e.get("verb") == "run":
        return e.get("act"), e.get("act")
    args = [a for a in e.get("args") or [] if not str(a).startswith("-")]
    return e.get("verb"), f"{e.get('verb')} {args[0]}" if args else e.get("verb")


def real(run: str | None = None, write: bool = True, ai_run: str | None = None) -> dict:
    state = load_books()
    selfrep = _json(OUT / "SDD_SELF_latest.json", {}) or {}
    run, evs = run_events(run)
    ai_run, ai_evs = run_events(ai_run, "ai-")
    head = _head()[:12]
    self_fresh = bool(selfrep) and selfrep.get("head") == head
    start = (evs[0].get("ts") if evs else "") or "9999"
    chains_full = {}
    for name, f in (("vdf", "vdf_chain/VDFCHAIN_latest.json"), ("vrn", "vrn_chain/VRNCHAIN_latest.json")):
        d = _json(VIA / "VIA_Reports" / f, {}) or {}
        gen = str(d.get("generated") or "").replace("T", " ")[:19]
        chains_full[name] = {"fresh": bool(evs) and gen >= start[:19], "rows": d.get("stages") or d.get("nodes") or []}
    chains = _chain_states()
    res = {}
    skip = set((state["comp"].get("scope") or {}).get("registered_only") or [])
    for sub, w in state["wkfs"]:
        if sub in skip:
            res[w["code"]] = {"alias": w.get("alias"), "level": "registered_only", "state": "REGISTERED_ONLY", "steps": {}}
            continue
        steps = {}
        mine = ai_evs if (w.get("tests") or {}).get("real_run") == "ai" else evs
        for st in w.get("steps") or []:
            if st.get("match"):
                hit = [e for e in mine for tgt, vb in st["match"]
                       if (e.get("target") or CONSOLE) == tgt and (vb is None or vb in _act(e))]
                if hit:
                    worst = max(hit, key=lambda e: WORST.get(e["outcome"], 0))      # a step that ran twice is as good as its worst run
                    steps[st["code"]] = {"state": worst["outcome"], "rc": worst["rc"], "at": worst["ts"], "secs": worst.get("secs"), "runs": len(hit)}
                    if worst["outcome"] == "FINDING" and st.get("finding_hand"):
                        steps[st["code"]]["hand"] = st["finding_hand"]
                else:
                    steps[st["code"]] = {"state": "NOT_RUN"}
            elif st.get("evidence"):
                steps[st["code"]] = {"state": "EVIDENCE", "evidence": st["evidence"], "hand_hint": st.get("finding_hand")}
            else:
                got = (selfrep.get("per_step") or {}).get(w["code"], {}).get(st["code"]) if self_fresh else None
                steps[st["code"]] = {"state": got or "NOT_RUN", "by": "selftest" if got else ("自測存證不是當前 HEAD" if selfrep else "沒有自測存證")}
        res[w["code"]] = {"alias": w.get("alias"), "steps": steps, "_w": w}
    flat = {c: s for r in res.values() for c, s in (r.get("steps") or {}).items()}

    def resolve(code: str, depth: int = 0) -> dict:
        s = flat.get(code) or {"state": "NOT_RUN", "why": "沒有這一步"}
        if s.get("state") != "EVIDENCE" or depth > 5:
            return s
        ev = s["evidence"]
        kind, _, arg = ev.partition(":")
        if kind == "step":
            src = resolve(arg, depth + 1)
            out = {"state": src.get("state"), "by": ev}
            if src.get("hand"):
                out["hand"] = src["hand"]
        elif kind == "self":
            eng = [e for e in selfrep.get("engines") or [] if arg == "all" or stem_of(e.get("tail") or "") == arg] if self_fresh else []
            outs = {e.get("outcome") for e in eng}
            out = {"state": ("NOT_RUN" if not eng else "FAIL" if "FAIL" in outs else "FINDING" if "FINDING" in outs else
                             "NOSELFTEST" if "NOSELFTEST" in outs else "OK"), "by": ev + ("" if self_fresh else "(自測存證不是當前 HEAD)")}
        elif kind == "chain":
            name, _, node = arg.partition(":")
            ch = chains_full.get(name) or {}
            if not ch.get("fresh"):
                out = {"state": "NOT_RUN", "by": ev + "(鏈報告不是本輪)"}
            else:
                rows = [r for r in ch["rows"] if str(r.get("id")) == node or str(r.get("layer", "")).startswith(node)]
                sts = [CHAIN_STATE.get(r.get("state"), "FAIL") for r in rows]
                out = {"state": "NOT_RUN" if not rows else "FAIL" if "FAIL" in sts else "FINDING" if "FINDING" in sts else "OK", "by": ev}
                if out["state"] == "FINDING":
                    out["hand"] = " · ".join(sorted({OPERATOR_HAND[r.get("state")] for r in rows if r.get("state") in OPERATOR_HAND}))
        elif ev == "git:pushed":
            r = subprocess.run(["git", "branch", "-r", "--contains", "HEAD"], cwd=VIA, capture_output=True, text=True)
            out = {"state": "OK" if r.stdout.strip() else "NOT_RUN", "by": ev + ("" if r.stdout.strip() else "(HEAD 還沒推上遠端)")}
        else:
            out = {"state": "NOT_RUN", "by": ev}
        if out.get("state") == "FINDING" and not out.get("hand") and s.get("hand_hint"):
            out["hand"] = s["hand_hint"]
        return out

    known = {st["code"]: st["known_open"] for _, w in state["wkfs"] for st in w.get("steps") or [] if st.get("known_open")}
    for code, s in flat.items():
        if s.get("state") == "CANON":
            s["hand"] = OPERATOR_HAND["CANON"]
        k = known.get(code)
        if k and s.get("state") in ("FAIL", "FINDING", "NOSELFTEST", "CANON"):
            s["known_open"] = k
            if k.get("hand") == "operator":
                s["hand"] = k.get("why")
            else:
                s.pop("hand", None)
                s["ai_open"] = k.get("why")
    for code in [c for c, s in flat.items() if s.get("state") == "EVIDENCE"]:
        flat[code].update(resolve(code))
        flat[code].pop("hand_hint", None)
    for code, r in res.items():
        if r.get("state") == "REGISTERED_ONLY":
            continue
        w = r.pop("_w")
        steps = r["steps"]
        states = [s["state"] for s in steps.values()]
        level = "real" if any(st.get("match") for st in w.get("steps") or []) else "selftest"
        lamp = ("FAIL" if "FAIL" in states else "NOT_RUN" if "NOT_RUN" in states else "FINDING" if "FINDING" in states
                else "NOSELFTEST" if "NOSELFTEST" in states else "CANON" if "CANON" in states else "OK")
        r.update({"level": level, "state": lamp, "run": ai_run if (w.get("tests") or {}).get("real_run") == "ai" else run})
    for code, chain in (("VDF-WKF001", "vdf"), ("VRN-WKF001", "vrn")):
        if code in res:
            res[code]["chain"] = chains.get(chain)
            if any(o["state"] not in OPERATOR_HAND for o in chains[chain]["open"]):   # a chain node that is RED / CRASH is ours to fix
                for s in res[code]["steps"].values():
                    s.pop("hand", None)
    for code, r in res.items():
        bad = [s for s in r["steps"].values() if s.get("state") != "OK"]
        if r["state"] in ("FINDING", "FAIL", "CANON", "NOSELFTEST") and bad and all(s.get("hand") for s in bad):
            r["operator_hand"] = True
        ai = [s.get("ai_open") for s in bad if s.get("ai_open")]
        if ai:
            r["ai_open"] = sorted(set(ai))
    rep = {"schema": "VIA.SDD.Real.v1", "engine": ENGINE, "ts": _now(), "head": _head()[:12], "run": run, "events": len(evs), "ai_run": ai_run, "ai_events": len(ai_evs),
           "self_run": selfrep.get("run"), "wkf": res}
    if write:
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "SDD_REAL_latest.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    return rep


# ------------------------------------------------------------------ lock (fixed successful versions + times) and closeout
def plan_lock(chk: dict, rl: dict) -> dict:
    locked, opened = {}, {}
    ok_static = chk.get("lamp") != "RED"
    vers = chk.get("versions") or {}
    state = load_books()
    targets = step_targets(state)
    for code, r in (rl.get("wkf") or {}).items():
        if r.get("state") == "REGISTERED_ONLY":
            continue
        mine = {rel(t[3]): t[3].name for t in targets if t[0] == code and t[3] is not None}
        if ok_static and r["state"] == "OK":
            locked[code] = {"alias": r.get("alias"), "level": r.get("level"), "locked_at": _now(), "head": chk.get("head"), "run": rl.get("run"),
                            "versions": mine, "numbered": {k: (vers.get(k) or {}).get("code") for k in mine},
                            "registered": {k: (vers.get(k) or {}).get("changed_at") or (vers.get(k) or {}).get("first_seen") for k in mine}}
        else:
            why = "靜態驗證紅" if not ok_static else r["state"]
            opened[code] = {"state": why, "operator_hand": bool(r.get("operator_hand")), "ai_open": r.get("ai_open"),
                            "open": ((r.get("chain") or {}).get("open") or [])[:12],
                            "steps": {k: v for k, v in r["steps"].items() if v.get("state") not in ("OK", "INSIDE") and v.get("by") not in ("OK",)}}
    return {"wkf": locked, "wkf_open": opened}


def stale_reasons(chk: dict, rl: dict) -> list:
    """Evidence must be about the code that is here now: same HEAD for check · real · selftests, and no uncommitted code."""
    head, why = _head()[:12], []
    selfrep = _json(OUT / "SDD_SELF_latest.json", {}) or {}
    if not chk or not rl:
        why.append("check / real 存證不齊")
    for name, rep_ in (("check", chk), ("real", rl), ("selftests", selfrep)):
        if rep_ and rep_.get("head") != head:
            why.append(f"{name} 存證是 {rep_.get('head')} 不是當前 HEAD {head}")
    if not selfrep:
        why.append("沒有自測存證")
    dirty = subprocess.run(["git", "status", "--porcelain", "--", "*.py", "*.ps1", "*Workflow*_SSOT_v*.json", "*Requirements_SSOT_v*.json"],
                           cwd=VIA, capture_output=True, text=True).stdout.strip().splitlines()
    if dirty:
        why.append(f"有未提交的程式 / 冊改動 {len(dirty)} 個(例 {dirty[0][3:][:60]})")
    return why


def lock(apply: bool = False) -> dict:
    chk, rl = _json(OUT / "SDD_CHECK_latest.json", {}) or {}, _json(OUT / "SDD_REAL_latest.json", {}) or {}
    why = stale_reasons(chk, rl)
    if why:
        print("  [鎖] 拒寫:" + " · ".join(why))
        return None
    plan = plan_lock(chk, rl)
    prev_p = newest("VIA_LampLock_v*.json")
    book = _json(prev_p, {}) or {}
    new_v = f"v{_vnum(prev_p) + 1:04d}" if prev_p else "v0100"
    old = book.get("wkf") or {}
    keep = {c: r for c, r in old.items() if c not in plan["wkf"] and c not in plan["wkf_open"]}
    book.update({"schema": book.get("schema") or "VIA.LampLock.v2", "prior": prev_p.name if prev_p else None,
                 "wkf_rule": "SDD 工作流過關(CGC_MDL245:靜態不紅 · 自測 / 實測 OK)= 鎖:記步正主的尾版 · 編號 · 註冊時間;之後尾版換了 = X-LOCK 要重驗,狀態退步 = 回歸紅",
                 "wkf_measured_at": _now(), "wkf_head": chk.get("head"), "wkf_run": rl.get("run"), "wkf_ai_run": rl.get("ai_run"),
                 "wkf": {**keep, **plan["wkf"]}, "wkf_open": plan["wkf_open"]})
    target = HERE / f"VIA_LampLock_{new_v}.json"
    print(f"  [鎖] 可鎖 {len(plan['wkf'])} 條 · 未鎖 {len(plan['wkf_open'])} 條 → {'寫 ' + target.name if apply else '乾跑(--apply 才寫下一版燈鎖冊)'}")
    if apply:
        target.write_text(json.dumps(book, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return plan


def closeout(apply: bool = False) -> dict:
    chk, rl = _json(OUT / "SDD_CHECK_latest.json", {}) or {}, _json(OUT / "SDD_REAL_latest.json", {}) or {}
    lk = _json(newest("VIA_LampLock_v*.json"), {}) or {}
    wk, op = lk.get("wkf") or {}, lk.get("wkf_open") or {}
    state = load_books()
    scope = set((state["comp"].get("scope") or {}).get("closeout") or [s for s in state["books"]])
    in_scope = [w["code"] for s, w in state["wkfs"] if s in scope]
    uncovered = [c for c in in_scope if c not in wk and c not in op]
    why = [x for x in stale_reasons(chk, rl) if not x.startswith("有未提交")]
    if lk.get("wkf_head") and lk.get("wkf_head") != chk.get("head"):
        why.append(f"燈鎖冊 wkf 區是 {lk.get('wkf_head')} 驗的,不是這次 check {chk.get('head')}")
    red = [r for r in chk.get("rows") or [] if r["lamp"] == "RED"]
    fail = {c: r for c, r in op.items() if not r.get("operator_hand")}
    not_run = [c for c, r in op.items() if r.get("state") == "NOT_RUN"]
    if red or fail or not chk or not rl or why or uncovered:
        verdict = "OPEN"
    elif op:
        verdict = "CLOSED_WITH_OPERATOR_ITEMS" if all(r.get("operator_hand") for r in op.values()) else "OPEN"
    else:
        verdict = "CLOSED"
    rep = {"verdict": verdict, "check": chk.get("lamp"), "locked": len(wk), "open": len(op), "red_rows": red, "fail": list(fail), "not_run": not_run,
           "stale": why, "uncovered": uncovered}
    for x in why + ([f"範圍內沒加鎖也沒列未鎖:{uncovered[:6]}"] if uncovered else []):
        print(f"  [收尾] 不成立:{x}")
    print(f"  [收尾] {verdict} · 靜態 {chk.get('lamp')} · 已鎖 {len(wk)} · 未鎖 {len(op)}(操作員端 {sum(1 for r in op.values() if r.get('operator_hand'))} · 本輪沒跑 {len(not_run)} · 要修 {len(fail)})")
    if apply:
        doc = VIA / "docs" / "VIA_SDD_Closeout_R33_v0100.md"
        lines = [f"# VIA SDD 收尾報告(R33)· {verdict}", "", f"- 產生:{_now()} · HEAD {chk.get('head')} · 引擎 {ENGINE}",
                 f"- 靜態驗證(自測 + 交叉測):**{chk.get('lamp')}** · 工作流 {chk.get('workflows')} · 步 {chk.get('steps')} · 需求 {chk.get('requirements')}",
                 f"- 實測輪:{rl.get('run')} · 事件 {rl.get('events')} · 自測輪 {rl.get('self_run')}", ""] + ten_steps(chk, rl, verdict) + ["", "## 交叉規則", "",
                 "| 燈 | 規則 | 內容 |", "|---|---|---|"]
        lines += [f"| {r['lamp']} | {r['rule']} | {r['msg']} |" for r in chk.get("rows") or []]
        lines += ["", "## 已鎖工作流(成功版本 · 編號 · 註冊時間)", "", "| 工作流 | 層級 | 鎖定時間 | 正主尾版 |", "|---|---|---|---|"]
        lines += [f"| {c} {r.get('alias')} | {r.get('level')} | {r.get('locked_at')} | {' · '.join(sorted(r.get('versions', {}).values()))[:300]} |" for c, r in sorted(wk.items())]
        lines += ["", "## 未鎖工作流(原因與下一步)", "", "| 工作流 | 狀態 | 操作員端 | 未綠項 |", "|---|---|---|---|"]
        for c, r in sorted(op.items()):
            items = "; ".join(f"{o['id']} {o['state']}({o['why']})" for o in r.get("open") or [])[:300] or \
                    "; ".join(f"{k} {v.get('state') or v.get('by')}" for k, v in (r.get("steps") or {}).items())[:300]
            lines.append(f"| {c} | {r.get('state')} | {'是' if r.get('operator_hand') else '否'} | {items} |")
        doc.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"  [收尾] 報告 {rel(doc)}")
    return rep


def ten_steps(chk: dict, rl: dict, verdict: str) -> list:
    """Master Prompt 回答格式十步(VCGC-WKF004 spec.report_format):每一步只引正主已寫的存證。"""
    by = {r["rule"]: r for r in chk.get("rows") or []}
    selfrep = _json(OUT / "SDD_SELF_latest.json", {}) or {}
    eng = selfrep.get("engines") or []
    w = rl.get("wkf") or {}
    hub = (w.get("VCGC-WKF001") or {}).get("steps") or {}
    g = lambda k: (by.get(k) or {}).get("lamp", "-") + " " + (by.get(k) or {}).get("msg", "")[:160]
    step = lambda code: (hub.get(code) or {}).get("state", "NOT_RUN")
    tally = {}
    for c, x in w.items():
        tally[x["state"]] = tally.get(x["state"], 0) + 1
    return ["## Master Prompt 十步(VCGC-WKF004 report_format)", "",
            f"1. Step 1 政策確認結果:流程閘 {step('VCGC-WKF001-STP002')}(本輪 {rl.get('run')})· {g('X-CONFLICT')}",
            f"2. Step 2 工具完整性檢查結果:ENV MANAGER {step('VCGC-WKF001-STP004')} · {g('X-ACCEL')}",
            f"3. Step 3 換行/哈希檢查結果:流程閘內鎖冊哈希比對(EOL 感知)隨 Step 1 · 註冊 {g('X-REG')}",
            f"4. Step 4 掃描結果(輕量/全面):省 Token 索引 {step('VCGC-WKF001-STP003')} · TA-Lib 與模板 {step('VCGC-WKF001-STP006')} · {g('X-ENGINE')}",
            f"5. Step 5 AST 定位結果:{g('X-COL')} · {g('X-OLD')}",
            f"6. Step 6 建議 patch:不自動套(Master Prompt)· {g('X-PARAM')}",
            "7. Step 7 是否需要 via 審核:任何程式改動都開新版檔,經 VCGC 自測與本驗證器;燈鎖冊寫入只在 lock --apply",
            f"8. Step 8 測試結果:自測 {len(eng)} 支(OK {sum(1 for e in eng if e['outcome'] == 'OK')} · FAIL {sum(1 for e in eng if e['outcome'] == 'FAIL')} · "
            f"FINDING {sum(1 for e in eng if e['outcome'] == 'FINDING')} · 無自測 {sum(1 for e in eng if e['outcome'] == 'NOSELFTEST')})· 實測 {tally}",
            f"9. Step 9 是否允許部署:{'是' if verdict != 'OPEN' else '否'}(靜態 {chk.get('lamp')};部署 = 合併到 main 並由工作站 via-vcgc go)",
            f"10. Step 10 VCGC 最終判定:**{verdict}**"]


def show_check(rep: dict) -> None:
    for r in rep["rows"]:
        print(f"  {r['lamp']:<6} {r['rule']:<11} {r['msg']}")
    print(f"[SDD 驗證] {rep['lamp']} · 工作流 {rep['workflows']} · 步 {rep['steps']} · 需求 {rep['requirements']} · {rep['secs']}s · 存證 VIA_Reports/sdd/SDD_CHECK_latest.json")


# ------------------------------------------------------------------ selftest
def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    state = load_books()
    chk("組成冊與四本工作流冊讀得到", state["hub_path"] and len(state["books"]) >= 3 and state["wkfs"], f"{len(state['wkfs'])} 條")
    book = compose(state)
    chk("組成 = 中樞相容冊(hub · loop_vdf · loop_vrn · exit · conformance)", all(k in book for k in ("hub", "loop_vdf", "loop_vrn", "exit", "conformance")))
    chk("組成後每步帶 STP 代碼,id 用 alias(中樞一致性訊息照舊 H1…X4)", book["hub"][1]["code"] == "VCGC-WKF001-STP002" and book["hub"][1]["id"] == "H1", book["hub"][1]["code"])
    rows = []
    fake = {"wkfs": [("VCGC", {"code": "VCGC-WKF001", "alias": "a", "name": "n", "kind": "procedure", "spec": {"goal": 1, "requirements": [], "acceptance": [1]},
                               "plan": {"x": 1}, "steps": [{"code": "VCGC-WKF001-STP001", "alias": "s", "name": "n", "engine": "a/b.py", "verb": "v"}],
                               "tests": {"self": 1, "cross": 1, "real": 1}})]}
    check_columns(fake, rows)
    chk("X-COL:步缺 what / match|inside = 紅", rows and rows[0]["lamp"] == "RED" and "verb/what" in rows[0]["msg"], rows[0]["msg"][:60] if rows else "")
    rows = []
    fake2 = {"books": {"VDF": (None, {"workflows": [{"code": "VDF-WKF002", "steps": []}]})}, "wkfs": [("VDF", {"code": "VDF-WKF002", "alias": "x"})]}
    check_codes(fake2, rows)
    chk("X-CODE:冊內跳號(從 002 起)= 紅", rows[0]["lamp"] == "RED" and "VDF-WKF002" in rows[0]["msg"])
    rows = []
    check_owners(state, rows)
    chk("X-OWNER:VDF 站表 = 跑器 CHAIN · VRN 層序 = 邏輯架構冊", rows[0]["lamp"] == "GREEN", rows[0]["msg"][:80])
    items = spec_items()
    rows = []
    check_items_and_old(state, rows, items)
    chk("X-ITEM / X-OLD:舊 18 條與中樞冊 v0100 整併無落差", all(r["lamp"] == "GREEN" for r in rows), " | ".join(r["msg"][:50] for r in rows if r["lamp"] != "GREEN"))
    rows = []
    check_engines(state, rows, step_targets(state, items))
    chk("X-ENGINE / X-ACCEL:正主尾版都在 · 帶標準橋", all(r["lamp"] == "GREEN" for r in rows), " | ".join(r["msg"][:80] for r in rows if r["lamp"] != "GREEN"))
    rl = {"run": "go-x", "wkf": {"VCGC-WKF001": {"alias": "hub", "state": "OK", "level": "real", "steps": {}},
                                 "VDF-WKF001": {"alias": "loop_vdf", "state": "FINDING", "level": "real", "operator_hand": True, "steps": {"s": {"state": "FINDING"}},
                                                "chain": {"open": [{"id": "3a", "state": "NODATA", "why": "x"}]}},
                                 "VRN-WKF001": {"alias": "loop_vrn", "state": "FAIL", "level": "real", "steps": {"s": {"state": "FAIL"}}}}}
    plan = plan_lock({"lamp": "GREEN", "head": "h", "versions": {}}, rl)
    chk("加鎖:只鎖 OK;FINDING(操作員端)與 FAIL 留在 wkf_open 附原因", list(plan["wkf"]) == ["VCGC-WKF001"] and plan["wkf_open"]["VDF-WKF001"]["operator_hand"]
        and not plan["wkf_open"]["VRN-WKF001"]["operator_hand"])
    plan2 = plan_lock({"lamp": "RED", "head": "h", "versions": {}}, rl)
    chk("靜態驗證紅 = 一條都不鎖", not plan2["wkf"] and plan2["wkf_open"]["VCGC-WKF001"]["state"] == "靜態驗證紅")
    ev = [{"verb": "status", "target": CONSOLE, "act": "status", "outcome": "OK", "rc": 0, "ts": "t"}]
    hit = [e for e in ev for tgt, vb in [[CONSOLE, "status"]] if e["target"] == tgt and vb == e["verb"]]
    chk("實測對事件:主控台動詞以動詞比 · run 以目標引擎 + 子動詞比", hit)
    r0 = real("no-such-run-zzz", write=False, ai_run="ai-no-such-run-zzz")
    chained = ((r0["wkf"].get("VDF-WKF003") or {}).get("steps") or {}).get("VDF-WKF003-STP002") or {}
    selfed = ((r0["wkf"].get("VRN-WKF003") or {}).get("steps") or {}).get("VRN-WKF003-STP002") or {}
    chk("Codex #365 P1:inside 步要有證據 — 鏈證據沒有本輪 = NOT_RUN;自測證據只認當前 HEAD 的存證",
        chained.get("state") == "NOT_RUN" and (selfed.get("state") == "NOT_RUN" or selfed.get("by", "").startswith("self:")),
        f"{chained.get('state')} · {selfed.get('state')} {selfed.get('by', '')}")
    chk("Codex #365 P2:不存在的輪 → 範圍內工作流是 NOT_RUN(CLI 回非 0)",
        any(w["state"] == "NOT_RUN" for c, w in r0["wkf"].items() if c.startswith(("VCGC-WKF001", "VDF-WKF001", "VRN-WKF001"))))
    stale = stale_reasons({"head": "000000000000"}, {"head": "000000000000"})
    chk("Codex #365 P1:存證不是當前 HEAD = 拒絕加鎖", any("不是當前 HEAD" in x for x in stale), stale[:1])
    chk("Codex #365 P1:沒有實測 / 鎖 = 收尾不成立", "check / real 存證不齊" in stale_reasons({}, {}))
    body = Path(__file__).read_text(encoding="utf-8")
    chk("本支帶加速器橋 · VIA_FROM_VCGC 標記", "[VIA:ACCEL-BRIDGE" in body and "VIA_FROM_VCGC" in body)
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["--selftest"]:
        return selftest()
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc(VIA_FROM_VCGC=YES)"}, ensure_ascii=False))
        return 2
    verb = a[0] if a else "check"
    if verb == "check":
        rep = check()
        show_check(rep)
        return {"GREEN": 0, "YELLOW": 2, "RED": 1}[rep["lamp"]]
    if verb == "selftests":
        only = a[a.index("--wkf") + 1] if "--wkf" in a else None
        rep = selftests(only)
        bad = [e for e in rep["engines"] if e["outcome"] == "FAIL"]
        print(f"[SDD 自測] 引擎 {len(rep['engines'])} · OK {sum(1 for e in rep['engines'] if e['outcome'] == 'OK')} · FAIL {len(bad)}"
              f" · FINDING {sum(1 for e in rep['engines'] if e['outcome'] == 'FINDING')} · 無自測 {sum(1 for e in rep['engines'] if e['outcome'] == 'NOSELFTEST')} · 輪 {rep['run']}")
        return 1 if bad else 0
    if verb == "real":
        rep = real(a[1] if len(a) > 1 and not a[1].startswith("-") else None)
        for c, r in rep["wkf"].items():
            print(f"  {r['state']:<10} {c:<11} {r['alias']:<30} 層級 {r['level']}" + (" · 操作員端" if r.get("operator_hand") else ""))
        print(f"[SDD 實測] 輪 {rep['run']} · 事件 {rep['events']} · 自測輪 {rep['self_run']}")
        states = {r["state"] for r in rep["wkf"].values()}
        return 1 if "FAIL" in states else (2 if states & {"NOT_RUN", "NOSELFTEST"} else 0)
    if verb == "lock":
        return 0 if lock("--apply" in a) is not None else 1
    if verb == "closeout":
        rep = closeout("--apply" in a)
        return {"CLOSED": 0, "CLOSED_WITH_OPERATOR_ITEMS": 0, "OPEN": 2}[rep["verdict"]]
    print("  用法:check | selftests [--wkf CODE] | real [輪號] | lock [--apply] | closeout [--apply] | --selftest")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
