#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL245_SDDValidator v0106 — 薄尾:X-PEER 三方對等組成檢 + X-PEER-TEXT 唯一入口舊字檢(政策 L120)

操作員 2026-10-10:「不再視為一入口 三系統獨立 政策及全部寫入 VCGC VRN VDF SYSTEM MANAGER獨立互不影響但互相監控而獨立運作功能」。
X-COMP 驗的是 VCGC 編排一輪的組成(hub → loop_vdf → loop_vrn → exit),照舊;本版在它後面多兩列:
  X-PEER       組成冊尾版 model.shape = three_peers_mutual_monitor,VCGC · VDF · VRN 三系統都列在 model.peers,
               各自的入口尾版找得到、各自的工作流在冊 → GREEN;舊形狀 / 少一系統 / 入口找不到 = RED。
  X-PEER-TEXT  組成冊與各系統工作流冊的現行字(版史欄 why_* · *_before_v* · prior · source 除外)還寫
               「唯一入口 / 唯一接觸口 / 唯一編排 / 只經 VCGC / 一對二」= YELLOW(不擋鎖;否定句「不是唯一入口」不算)。
其餘整支照 v0105(selftests 進度暫存 · check / real / lock / closeout)。只讀,不寫冊。
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
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL245_SDDValidator"
ENGINE = Path(__file__).stem


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location("_sdd_prior_v0106", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR
while "PRIOR" in vars(BASE):
    BASE = vars(BASE)["PRIOR"]
_V0105_COMP = BASE.check_composition

PEERS = ("VCGC", "VDF", "VRN")
SHAPE = "three_peers_mutual_monitor"
# 「唯一入口」類舊字樣;前面是「不是 / 不再是 / 不再有」的否定句不算(L120 ① 舊字樣留作版史)
SOLE = re.compile(r"(?<!不是)(?<!不再是)(?<!不再有)(唯一入口|唯一接觸口|唯一編排)|只經 VCGC|只能經 VCGC|一對二")
_HISTORY_KEYS = ("prior", "source", "supersedes", "batch", "ts")


def _live_text(obj, path=""):
    """(路徑, 字串) — 跳過版史欄位(why_* · *_before_v* · prior · source · supersedes)。"""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.startswith("why") or "_before_v" in k or k in _HISTORY_KEYS:
                continue
            yield from _live_text(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _live_text(v, f"{path}[{i}]")
    elif isinstance(obj, str):
        yield path, obj


def sole_phrases(state: dict) -> list:
    """組成冊與各系統工作流冊的現行字裡,還寫「唯一入口 / 只經 VCGC / 一對二」的地方(否定句不算)。"""
    hits = [f"hub{p}" for p, s in _live_text(state.get("comp") or {}) if SOLE.search(s)]
    for sub, w in state.get("wkfs") or []:
        hits += [f"{w.get('code')}{p}" for p, s in _live_text(w) if SOLE.search(s)]
    return hits


def check_peers(state, rows):
    """X-PEER(L120):組成冊 model 宣告三方對等、三系統各有自己的入口尾版與工作流;現行字不再寫唯一入口。"""
    model = (state.get("comp") or {}).get("model") or {}
    peers = {p.get("id"): p for p in model.get("peers") or [] if isinstance(p, dict)}
    bad = []
    if model.get("shape") != SHAPE:
        bad.append(f"model.shape = {model.get('shape')}(要 {SHAPE})")
    for pid in PEERS:
        p = peers.get(pid)
        if not p:
            bad.append(f"{pid} 沒列在 model.peers")
            continue
        if BASE.resolve(p.get("entry") or "") is None:
            bad.append(f"{pid} 入口 {p.get('entry')} 找不到尾版")
        if p.get("workflow") not in (state.get("by_code") or {}):
            bad.append(f"{pid} 工作流 {p.get('workflow')} 不在冊")
    if bad:
        BASE._row(rows, "RED", "X-PEER", "三方對等組成不齊(L120):" + " · ".join(bad))
    else:
        BASE._row(rows, "GREEN", "X-PEER", "三方對等(L120):" + " · ".join(f"{pid} 入口 {Path(peers[pid]['entry']).name} → {peers[pid]['workflow']}" for pid in PEERS)
                  + " · 互相只讀監控")
    hits = sole_phrases(state)
    if hits:
        BASE._row(rows, "YELLOW", "X-PEER-TEXT", f"現行字還寫唯一入口 / 只經 VCGC / 一對二 {len(hits)} 處(L120 ①:改成各系統自己的入口;舊字留版史欄):{hits[:6]}")
    else:
        BASE._row(rows, "GREEN", "X-PEER-TEXT", "組成冊與各系統工作流冊的現行字不再寫唯一入口 / 只經 VCGC / 一對二(版史欄除外)")


def check_composition(state, rows):
    _V0105_COMP(state, rows)
    check_peers(state, rows)


BASE.check_composition = check_composition


def __getattr__(name: str):
    return getattr(PRIOR, name)


def main(argv=None):
    return PRIOR.main(argv)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:300]) if note and not cond else ''}")

    print(f"=== {ENGINE} · 薄尾自測(X-PEER 三方對等組成 · X-PEER-TEXT 唯一入口舊字)===")
    entries = {"VCGC": "supportive modules/registry/CGC_MDL149_VeritasCentralGovernanceConsole_v*.py",
               "VDF": "functional modules/VDF/VDF_SystemManager_v*.py", "VRN": "functional modules/VRN/VRN_SystemManager_v*.py"}
    by = {"VCGC-WKF001": ("VCGC", {}), "VDF-WKF001": ("VDF", {}), "VRN-WKF001": ("VRN", {})}

    def st(shape=SHAPE, drop=None, goal="VDF 從自己的入口進出", hub_extra=None):
        peers = [{"id": k, "entry": v, "workflow": k + "-WKF001"} for k, v in entries.items() if k != drop]
        comp = {"model": {"shape": shape, "peers": peers, "rules_before_v0103": ["外部世界只經 VCGC 進出"]}, "why_v0103": "唯一入口 → 對等"}
        comp.update(hub_extra or {})
        w = {"code": "VDF-WKF001", "name": "VDF 迴圈", "spec": {"goal": goal}, "why_v0105": "只經 VCGC 進出(舊)"}
        return {"comp": comp, "by_code": by, "wkfs": [("VDF", w)]}

    def lamps(s):
        rows = []
        check_peers(s, rows)
        return {r["rule"]: r["lamp"] for r in rows}

    chk("① 三方對等齊 + 現行字乾淨 → X-PEER GREEN · X-PEER-TEXT GREEN(版史欄的舊字不算)",
        lamps(st()) == {"X-PEER": "GREEN", "X-PEER-TEXT": "GREEN"}, lamps(st()))
    chk("② 舊形狀 hub_and_two_loops 或少一系統 → X-PEER RED", lamps(st(shape="hub_and_two_loops"))["X-PEER"] == "RED" and lamps(st(drop="VRN"))["X-PEER"] == "RED")
    chk("③ 現行字寫「只經 VCGC 進出」→ X-PEER-TEXT YELLOW(不擋鎖);「不是唯一入口」否定句不算",
        lamps(st(goal="VDF 只經 VCGC 進出"))["X-PEER-TEXT"] == "YELLOW"
        and lamps(st(goal="VCGC 這側的一個入口,L120 起不是唯一入口;不再有唯一入口"))["X-PEER-TEXT"] == "GREEN")
    real = BASE.load_books()
    rr = []
    check_peers(real, rr)
    got = {r["rule"]: r["lamp"] for r in rr}
    chk("④ 實樹:組成冊尾版 three_peers_mutual_monitor · 三系統入口尾版在 · 工作流在冊 → X-PEER GREEN;現行字乾淨 → X-PEER-TEXT GREEN",
        got == {"X-PEER": "GREEN", "X-PEER-TEXT": "GREEN"}, [(r["rule"], r["lamp"], r["msg"][:200]) for r in rr])
    chk("⑤ 裝進本體:本體 check() 呼叫的 check_composition 就是本版(X-COMP 照舊先跑)", BASE.check_composition is check_composition)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 加速器橋 · 網路橋在;不碰 TA-Lib", "VIA:ACCEL-BRIDGE" in src and "VIA:NET-BRIDGE" in src
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M))
    print(f"  [{ENGINE}] 薄尾 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}")
    rc = PRIOR.selftest()
    return rc if all(ok) else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if sys.argv[1:] == ["--selftest"] else main())
