#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL237_NumberingSystem v0104 — 薄尾:SDD 工作流 · 步 · 需求三類編號(WKF · STP · REQ)

操作員 R33:「build up workflow SSOT and register them and keep them a code VCGC-WKF001 like that … VRN and VDF」。
新增三類(只增;K22 WKF 工作流 · K23 STP 工作流步 · K24 REQ 需求):
  WKF  來自工作流冊尾版(VIA_Workflow_<子系統>_SSOT_v*.json,中樞組成冊 books 指名的那幾本)每一條 workflows[].code
  STP  每條工作流的 steps[].code,掛在所屬 WKF 之下(VIA-VCGC-WKF001-STP001;階層號沿用 v0100 parent_key)
  REQ  需求冊尾版(VIA_Requirements_SSOT_v*.json)每一條 requirements[].code
號碼 = 冊上宣告的代碼加 VIA- 前綴:冊上代碼只增、依序,編號系統照同一順序發號,第一次就對齊;之後同鍵同號。
工作流身分是代碼、不是冊版號,所以三類的版本欄固定 v0100(冊版號記在 book 欄),冊升版不會換號。
對不上(冊上代碼 ≠ 發出的號)不改任何一邊,列上 lamp=RED · note 寫明(SDD 驗證器 X-NUM 判紅)。其餘整支照 v0103。
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

STEM = "CGC_MDL237_NumberingSystem"

import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", path.stem)
    return int(m.group(1)) if m else -1


PRIOR = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(STEM + "_prior_for_" + Path(__file__).stem, PRIOR)
_PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _PRIOR
_spec.loader.exec_module(_PRIOR)
ENGINE = Path(__file__).stem


def __getattr__(name: str):
    return getattr(_PRIOR, name)


_BASE = _PRIOR._BASE
NEW_KINDS = [("WKF", "工作流"), ("STP", "工作流步"), ("REQ", "需求")]
for _k, _zh in NEW_KINDS:
    if _k not in _BASE.KIND_NO:
        _BASE.KINDS.append((_k, _zh))
        _BASE.KIND_NO[_k] = f"K{len(_BASE.KINDS):02d}"
CODE_RX = re.compile(r"^(?P<sub>[A-Z]+)-(?P<kind>WKF|REQ)(?P<n>\d{3})(?:-STP(?P<s>\d{3}))?$")
_V0103_COLLECT = _BASE.collect
_V0103_ASSIGN = _BASE.assign


def _newest(pattern: str) -> Path | None:
    hits = sorted(HERE.glob(pattern), key=_vnum)
    return hits[-1] if hits else None


def workflow_books() -> list:
    """(subsystem, path, book) for every book the newest hub composition names."""
    hub = _newest("VIA_Workflow_Hub_SSOT_v*.json")
    comp = json.loads(hub.read_text(encoding="utf-8")) if hub else {}
    out = []
    for sub, pattern in (comp.get("books") or {}).items():
        p = _newest(Path(pattern).name)
        if p:
            out.append((sub, p, json.loads(p.read_text(encoding="utf-8"))))
    return out


def sdd_items() -> list:
    out = []
    for sub, p, book in workflow_books():
        rel = _BASE._rel(p)
        upd = _BASE.updated(rel)
        for w in book.get("workflows") or []:
            wkey = "wkf|" + w["code"]
            out.append(_BASE.item("WKF", wkey, f"{w['code']} {w.get('name', '')}"[:120], "工作流/" + sub, rel, w.get("kind") or "—", upd, sub,
                                  "v0100", "GREEN", "", declared=w["code"], alias=w.get("alias"), book=p.stem))
            for s in sorted(w.get("steps") or [], key=lambda x: x.get("code") or ""):   # code = identity; list order is the plan
                out.append(_BASE.item("STP", "stp|" + s["code"], f"{s['code']} {s.get('name') or s.get('alias') or ''}"[:120],
                                      "工作流步/" + w["code"], rel, s.get("verb") or s.get("item") or s.get("station") or s.get("layer") or "—",
                                      upd, sub, "v0100", "GREEN", "", declared=s["code"], alias=s.get("alias"), parent_key=wkey, book=p.stem))
    req = _newest("VIA_Requirements_SSOT_v*.json")
    if req:
        rel = _BASE._rel(req)
        for r in json.loads(req.read_text(encoding="utf-8")).get("requirements") or []:
            m = CODE_RX.match(r.get("code") or "")
            out.append(_BASE.item("REQ", "req|" + r["code"], f"{r['code']} {r.get('topic') or ''}"[:120], "需求/" + (r.get("status") or "—"), rel,
                                  " · ".join(r.get("homes") or [])[:160] or "—", _BASE.updated(rel), m.group("sub") if m else "VCGC",
                                  "v0100", "GREEN" if r.get("status") == "COVERED" else "AMBER", r.get("status") or "", declared=r["code"], book=req.stem))
    return out


def collect() -> tuple:
    items, notes = _V0103_COLLECT()
    return items + sdd_items(), notes


def assign(items: list, state: dict) -> dict:
    state = _V0103_ASSIGN(items, state)
    for (kind, _), r in state["rows"].items():
        if kind in ("WKF", "STP", "REQ") and r.get("declared") and not r.get("gone_since"):
            if r["code"] != "VIA-" + r["declared"]:
                r["lamp"], r["note"] = "RED", f"冊上代碼 {r['declared']} ≠ 發出的號 {r['code']}(不改任何一邊;SDD 驗證器 X-NUM)"
    return state


_BASE.collect, _BASE.assign = collect, assign


def main(argv=None) -> int:
    if "--selftest" in (sys.argv[1:] if argv is None else argv):
        return selftest()
    return _PRIOR.main(argv)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    chk("三類入類表(只增;K22 WKF · K23 STP · K24 REQ)", [_BASE.KIND_NO.get(k) for k, _ in NEW_KINDS] == ["K22", "K23", "K24"], [_BASE.KIND_NO.get(k) for k, _ in NEW_KINDS])
    items = sdd_items()
    w = [i for i in items if i["kind"] == "WKF"]
    s = [i for i in items if i["kind"] == "STP"]
    chk("工作流冊有料(組成冊 books 指名的冊)", w and s, f"WKF {len(w)} · STP {len(s)}")
    state = {"rows": {}, "subs": ["VCGC", "VDF", "VRN", "VAP", "SUP", "CORE"], "cats": {}}
    state = assign(w + s, state)
    rows = list(state["rows"].values())
    bad = [r["declared"] for r in rows if r["code"] != "VIA-" + r["declared"]]
    chk("第一次發號就等於冊上代碼(VIA- 前綴 · 步掛在工作流下)", not bad, bad[:3] or f"{len(rows)} 列")
    state2 = assign(w + s, {"rows": {k: dict(v) for k, v in state["rows"].items()}, "subs": state["subs"], "cats": state["cats"]})
    chk("再跑一次同鍵同號(只增)", all(state2["rows"][k]["code"] == v["code"] for k, v in state["rows"].items()))
    fake = dict(w[0], key="wkf|VCGC-WKF999", declared="VCGC-WKF999")
    st3 = assign([fake], {"rows": {}, "subs": state["subs"], "cats": {}})
    r3 = next(iter(st3["rows"].values()))
    chk("冊上代碼跳號 = 紅燈記下,不改任何一邊", r3["lamp"] == "RED" and r3["code"] == "VIA-VCGC-WKF001", r3["code"])
    if not all(ok):
        return 1
    return _PRIOR.selftest()


if __name__ == "__main__":
    raise SystemExit(main())
