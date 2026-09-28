#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""CGC_MDL149_VeritasCentralGovernanceConsole v0169 — 薄尾:工作流 SSOT 改由 SDD 冊組成 · sdd 動詞 · 同步檢查帶 SDD 燈

操作員 R33:「Implement SDD structures … workflow SSOT … code VCGC-WKF001 … auto sync synchronizing with SSOT to prevent any missing」。
  ① 組成:中樞組成冊 VIA_Workflow_Hub_SSOT v0101 起不再內嵌步驟,步驟在子系統工作流冊(VCGC · VDF · VRN · VAP);
     組成的正主是 CGC_MDL245 SDD 驗證器的 compose()(一處組、兩處用),本尾版把前一版的 _flow_book 換成它 ——
     一致性核對(workflow)規則照 v0168,訊息帶 STP 代碼。
  ② workflow [輪號]:一致性核對後,接著 CGC_MDL245 real(逐工作流逐步:有跑 · 結果類 · 時間;迴圈附未綠項是不是操作員端)。
  ③ sdd <動詞…>:= run --family core CGC_MDL245_SDDValidator <動詞…>(check · selftests · real · lock · closeout;事件照記)。
  ④ 自動同步:樹有變時的同步檢查多一盞 SDD 靜態驗證燈(約 1 秒);紅就印一行「[同步] SDD …」。寫入(lock --apply)照舊要批准。
其餘照 v0168(thin tail;__getattr__ 轉接)。只收 VCGC 呼叫(VIA_FROM_VCGC=YES)。
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
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL149_VeritasCentralGovernanceConsole"


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


_SDD: dict = {}


def sdd_module():
    if "m" not in _SDD:
        hits = sorted(HERE.glob("CGC_MDL245_SDDValidator_v*.py"), key=_vnum)
        _SDD["m"] = PRIOR._load(hits[-1], "sdd_for_v0169") if hits else None
    return _SDD["m"]


def _flow_book() -> tuple:
    m = sdd_module()
    if m is None:
        return _V0168_FLOW_BOOK()
    st = m.load_books()
    return st["hub_path"], m.compose(st)


_V0168_FLOW_BOOK = PRIOR._flow_book
_V0168_SYNC = PRIOR.sync_check


def sync_check(key: str | None = None) -> dict:
    out = _V0168_SYNC(key)
    m = sdd_module()
    if m is not None:
        try:
            rep = m.check(write=True)
            out["sdd"] = {"lamp": rep["lamp"], "red": [r["rule"] + " " + r["msg"][:80] for r in rep["rows"] if r["lamp"] == "RED"][:4]}
            if rep["lamp"] == "RED":
                print(f"  [同步] SDD 驗證 RED:{' | '.join(out['sdd']['red'])} → via-vcgc sdd check")
        except Exception as exc:
            out["sdd"] = {"error": f"{type(exc).__name__}: {str(exc)[:120]}"}
    return out


def workflow(run: str | None = None) -> int:
    path, book = _flow_book()
    if not book:
        print("  [工作流] ABSENT:VIA_Workflow_Hub_SSOT 尾版不在")
        return 3
    run, evs = PRIOR.run_events(run)
    r = PRIOR.conformance(book, evs)
    code = {st["id"]: st.get("code") or st["id"] for sec in ("hub", "exit") for st in book.get(sec) or []}
    code.update({st["id"]: st.get("code") or st["id"] for sec in ("loop_vdf", "loop_vrn") for st in (book.get(sec) or {}).get("steps") or []})
    print(f"  [工作流] {r['lamp']} · 輪 {run or '-'} · 事件 {r['events']}(不在冊上的步 {r['unmatched']})· 實跑順序 "
          f"{' → '.join(r['seen'])} · 冊 {path.name if path else '-'} + 子系統工作流冊")
    for x in r["red"]:
        print(f"    紅 {x}")
    for x in r["yellow"]:
        print(f"    黃 {x}")
    print("    代碼 " + " · ".join(f"{k}={v}" for k, v in code.items() if k in r["seen"]))
    m = sdd_module()
    if m is not None and run:
        try:
            rep = m.real(run)
            tally = {}
            for c, w in rep["wkf"].items():
                tally.setdefault(w["state"], []).append(c)
            print("  [SDD 實測] " + " · ".join(f"{k} {len(v)}" for k, v in sorted(tally.items())) + " · 存證 VIA_Reports/sdd/SDD_REAL_latest.json")
            for c in ("VCGC-WKF001", "VDF-WKF001", "VRN-WKF001", "VCGC-WKF002"):
                w = rep["wkf"].get(c) or {}
                print(f"    {c} {w.get('alias')} {w.get('state')}" + (" · 未綠都在操作員端" if w.get("operator_hand") else ""))
        except Exception as exc:
            print(f"  [SDD 實測] 讀不動:{type(exc).__name__}: {str(exc)[:120]}")
    return r["rc"]


PRIOR._flow_book, PRIOR.sync_check, PRIOR.workflow = _flow_book, sync_check, workflow


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] == ["sdd"]:
        args = ["run", "--family", "core", "CGC_MDL245_SDDValidator"] + (args[1:] or ["check"])
    return PRIOR.main(args)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    path, book = _flow_book()
    chk("組成冊由 SDD 驗證器組(hub · loop_vdf · loop_vrn · exit)", path and path.name.startswith("VIA_Workflow_Hub_SSOT_v") and all(k in book for k in ("hub", "loop_vdf", "loop_vrn", "exit")),
        path.name if path else "-")
    chk("每步帶 STP 代碼", all(st.get("code") for st in book["hub"] + book["exit"]), book["hub"][0].get("code"))
    chk("前一版的核對讀到的是組成冊(已換掉 _flow_book)", PRIOR._flow_book is _flow_book and PRIOR.workflow is workflow)
    s = sync_check(PRIOR.tree_key())
    chk("同步檢查帶 SDD 靜態燈", "sdd" in s and ("lamp" in s["sdd"] or "error" in s["sdd"]), s.get("sdd", {}).get("lamp"))
    body = Path(__file__).read_text(encoding="utf-8")
    chk("抬頭 raw · 帶 VIA_FROM_VCGC 標記(座位探針要)", body.split("\n", 3)[2].startswith('r"""') and "VIA_FROM_VCGC" in body)
    if not all(ok):
        return 1
    return PRIOR.selftest()


if __name__ == "__main__":
    a = sys.argv[1:]
    raise SystemExit(selftest() if a == ["--selftest"] else main())
