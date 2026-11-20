#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL140_HandoverConsole v0109 — 薄尾:已停用的舊版號檔(具名名冊)不再判「改了沒測」· 接手者此刻有效綠才放行
操作員 2026-11-20「兩件都同意 補橋 UIEngine標停用 VCGC收尾」:
  CGC_MDL261_UIEngine v0101–v0107 已被裁定甲取代(工作項早已 SUPERSEDED → VCGC-REQ236:ui_engine_v0109),
  但 v0108 明定「退役項的舊相依不算測過」,這 7 支檔的自測本身就不過(舊判決行已不印),交接閘永遠判
  CHANGED_CODE_WITHOUT_TEST 紅,checkpoint 永遠拒寫。
本版只動一件事:CHANGED_CODE_WITHOUT_TEST 那一條,檔在交接冊 `retired_files` 具名名冊上、且四條件全中,才移出紅列、
  記進 report["retired_files"](逐檔 · 接手者 · 理由 · 時間 · 誰同意):
  ① 名冊列有 successor(工作項 id)· why · at · by                         缺 → RED RETIRED_FILE_INCOMPLETE
  ② 接手工作項存在 · 狀態 VERIFIED                                          否 → RED RETIRED_FILE_SUCCESSOR_INVALID
  ③ 接手工作項 id 在這一輪的 reusable_successes(收據此刻有效)             否 → RED RETIRED_FILE_SUCCESSOR_INVALID
  ④ 檔還在(停用 = 留檔標停用,不刪;操作員待裁定 2 裁定前不刪)          不在 → 照 FILE_REMOVED 等前版規則判
不在名冊上的檔一律照舊紅;監看範圍不變(檔仍在 state.files,改字 = CHECKPOINT_STALE 照舊);名冊外不放寬任何規則。
其餘照 v0108(被取代工作項 · Z281 雙胞移交 · 凍結收容件具名豁免 · 家族已登)。只收 VCGC 呼叫。零網路 · 不 import 他系統 · 不碰 TA-Lib。
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
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL140_HandoverConsole"
ENGINE = Path(__file__).stem
VERSION = "v0109"
ROSTER_KEY = "retired_files"
NEED = ("successor", "why", "at", "by")


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + ENGINE, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)                 # v0108:被取代工作項已裝進 v0101 的 audit
VIA = PRIOR.VIA
POLICY = PRIOR.POLICY
BASE = PRIOR.BASE


def apply_retired_files(report: dict, policy: dict, via=VIA) -> dict:
    """CHANGED_CODE_WITHOUT_TEST 裡、名冊具名的停用檔:接手工作項此刻有效綠才移出紅列;其餘一律照舊。"""
    roster = (policy or {}).get(ROSTER_KEY) or {}
    items = {x.get("id"): x for x in (policy or {}).get("work_items", []) if isinstance(x, dict)}
    reusable = set(report.get("reusable_successes") or [])
    kept, retired, bad = [], [], []
    for row in report.get("rows", []):
        rel = row.get("detail")
        ent = roster.get(rel) if row.get("rule") == "CHANGED_CODE_WITHOUT_TEST" and isinstance(rel, str) else None
        if ent is None or not (Path(via) / rel).is_file():
            kept.append(row)
            continue
        miss = [k for k in NEED if not (ent or {}).get(k)]
        succ_id = (ent or {}).get("successor")
        succ = items.get(succ_id) if isinstance(succ_id, str) else None
        if miss:
            bad.append({"lamp": "RED", "rule": "RETIRED_FILE_INCOMPLETE", "detail": {"path": rel, "missing": miss}})
        elif not succ or succ.get("state") != "VERIFIED" or succ_id not in reusable:
            why = ("接手工作項不存在" if not succ else "接手工作項狀態 %s(要 VERIFIED)" % succ.get("state")
                   if succ.get("state") != "VERIFIED" else "接手工作項收據此刻失效(先重跑它的案)")
            bad.append({"lamp": "RED", "rule": "RETIRED_FILE_SUCCESSOR_INVALID", "detail": {"path": rel, "successor": succ_id, "why": why}})
        else:
            retired.append({"path": rel, "successor": succ_id, "why": ent["why"], "at": ent["at"], "by": ent["by"]})
    rows = kept + bad
    lamps = [x["lamp"] for x in rows]
    lamp = "RED" if "RED" in lamps else "YELLOW" if lamps else "GREEN"
    report["rows"] = rows
    report["lamp"] = lamp
    report["closeout_lamp"] = ("RED" if lamp == "RED" else "YELLOW"
                               if report.get("pending") or lamp == "YELLOW" or report.get("z281_handover") else "GREEN")
    report["retired_files"] = retired
    s = report.setdefault("summary", {})
    s["findings"] = len(rows)
    s["retired_files"] = len(retired)
    return report


_V0108_AUDIT = BASE.audit


def audit(via=VIA, policy=None, baseline=None, require_baseline=True):
    pol = policy or BASE.read(Path(via) / POLICY.relative_to(VIA))
    return apply_retired_files(_V0108_AUDIT(via, policy, baseline, require_baseline), pol, via)


BASE.audit = audit


def __getattr__(name: str):
    return getattr(PRIOR, name)


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        if os.environ.get("VIA_FROM_VCGC") != "YES":
            print("[DENY] VCGC entry required")
            return 2
        return selftest()
    return PRIOR.main(argv)


def selftest():
    import tempfile
    BASE.audit = _V0108_AUDIT                   # 前版自測驗「v0108 裝在 v0101 全域」:跑前版時還原,跑完裝回本版
    try:
        rc = PRIOR.selftest()
    finally:
        BASE.audit = audit
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    with tempfile.TemporaryDirectory(prefix="mdl140_v0109_") as td:
        via = Path(td)
        for rel in ("a/Old_v0101.py", "a/Old_v0102.py", "a/Other_v0101.py"):
            (via / rel).parent.mkdir(parents=True, exist_ok=True)
            (via / rel).write_text("x = 1\n", encoding="utf-8")
        full = {"successor": "S", "why": "裁定甲取代", "at": "2026-11-20T00:00:00Z", "by": "操作員 2026-11-20"}

        def rep(rows, roster, items, reusable, **kw):
            pol = {ROSTER_KEY: roster, "work_items": [{"id": k, **v} for k, v in items.items()]}
            return apply_retired_files({"rows": [dict(r) for r in rows], "pending": [], "summary": {},
                                        "reusable_successes": list(reusable), **kw}, pol, via)
        cc = lambda p: {"lamp": "RED", "rule": "CHANGED_CODE_WITHOUT_TEST", "detail": p}
        good_items = {"S": {"state": "VERIFIED"}}
        r = rep([cc("a/Old_v0101.py"), cc("a/Old_v0102.py")], {"a/Old_v0101.py": full, "a/Old_v0102.py": full}, good_items, {"S"})
        chk("ⓐ 名冊具名 · 接手者 VERIFIED 且收據有效 → 移出紅列 · 列進 retired_files · 燈 GREEN",
            r["lamp"] == "GREEN" and [x["path"] for x in r["retired_files"]] == ["a/Old_v0101.py", "a/Old_v0102.py"]
            and r["summary"]["retired_files"] == 2, r)
        r = rep([cc("a/Other_v0101.py")], {"a/Old_v0101.py": full}, good_items, {"S"})
        chk("ⓑ 不在名冊上的檔照舊 RED CHANGED_CODE_WITHOUT_TEST(本版不放寬名冊外)",
            r["lamp"] == "RED" and r["rows"] == [cc("a/Other_v0101.py")] and not r["retired_files"], r)
        r = rep([cc("a/Old_v0101.py")], {"a/Old_v0101.py": full}, good_items, set())
        chk("ⓒ 接手者收據此刻失效 → RED RETIRED_FILE_SUCCESSOR_INVALID(不放行)",
            r["lamp"] == "RED" and r["rows"][0]["rule"] == "RETIRED_FILE_SUCCESSOR_INVALID", r)
        r = rep([cc("a/Old_v0101.py")], {"a/Old_v0101.py": full}, {"S": {"state": "SUPERSEDED"}}, {"S"})
        chk("ⓓ 接手者不是 VERIFIED(含它自己也被取代)→ RED", r["lamp"] == "RED" and r["rows"][0]["rule"] == "RETIRED_FILE_SUCCESSOR_INVALID", r)
        r = rep([cc("a/Old_v0101.py")], {"a/Old_v0101.py": {"successor": "S"}}, good_items, {"S"})
        chk("ⓔ 名冊缺 why / at / by → RED RETIRED_FILE_INCOMPLETE",
            r["rows"][0]["rule"] == "RETIRED_FILE_INCOMPLETE" and set(r["rows"][0]["detail"]["missing"]) == {"why", "at", "by"}, r)
        r = rep([cc("a/Gone_v0101.py")], {"a/Gone_v0101.py": full}, good_items, {"S"})
        chk("ⓕ 名冊上的檔不在了 → 不豁免(照舊紅;停用 = 留檔,不是刪檔)", r["lamp"] == "RED" and r["rows"] == [cc("a/Gone_v0101.py")], r)
        r = rep([{"lamp": "RED", "rule": "EVIDENCE_INVALID", "detail": {"id": "X"}}, cc("a/Old_v0101.py")],
                {"a/Old_v0101.py": full}, good_items, {"S"})
        chk("ⓖ 其他規則的紅一條不動(只動 CHANGED_CODE_WITHOUT_TEST)", r["lamp"] == "RED" and r["rows"][0]["rule"] == "EVIDENCE_INVALID"
            and len(r["rows"]) == 1, r)
        r = rep([cc("a/Old_v0101.py")], {"a/Old_v0101.py": full}, good_items, {"S"}, z281_handover=[{"path": "z.py"}])
        chk("ⓗ 前版判的驗收燈不被洗:有 Z281 移交 → 交接燈 GREEN · 驗收燈 YELLOW", r["lamp"] == "GREEN" and r["closeout_lamp"] == "YELLOW", r)
    chk("ⓘ 已裝進 v0101 模組全域(check / checkpoint 經本版 audit)", BASE.audit is audit)
    text = Path(__file__).read_text(encoding="utf-8")
    chk("ⓙ 檔頭:加速器橋 · 網路橋在(__future__ 之後)· 不碰 TA-Lib · 不含本機路徑",
        "VIA:ACCEL-BRIDGE" in text and "VIA:NET-BRIDGE" in text and text.index("from __future__") < text.index("[VIA:ACCEL-BRIDGE")
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M) and ("C:" + "\\Users") not in text)
    passed = rc == 0 and all(ok)
    print(f"[交接 {VERSION}] 本版 {sum(ok)}/{len(ok)} · 前版 {'PASS' if rc == 0 else 'FAIL'} · 停用檔名冊 · {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
