#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL140_HandoverConsole v0108 — 薄尾:工作項新增「SUPERSEDED(被取代)」狀態 · 接手者必須此刻有效綠才放行

操作員 2026-11-17「既有範疇全面全景式檢查 · 全面修正問題到綠燈 且檢查綠燈是有效的 · 你決定 · 授權自動完成」;
桌機 PCAlign 重跑實錄(20261117_195330):VDF_SystemManager --selftest 一條指令掛了 25 個交接案,每案釘一個舊版判決行
(v0121 … v0163 · v0182)。VDF_SystemManager v0169 起「全原生 · 不轉交前版」,尾版自測只印自己的
「[計] VDF_SystemManager v0183 全原生 39/39 PASS」→ 舊判決行永遠等不到;舊版單檔跑又讀到新冊就紅(沙盒實測 20 支全 rc 1,
v0126 本版 5/5 但前版鏈 FAIL)。這 24 案(27 個工作項)不是程式壞,是「舊版行為」已被尾版接手 → 證據該退役,不該無限重跑
(桌機每案 200–580 秒),也不該改釘成尾版標記(那會讓「v0126 拒跑未知動詞」被尾版 39/39 冒充證明 = 假綠)。

本版只動一件事:audit 判 INVALID_WORK_STATE 的工作項,若 state == "SUPERSEDED" 且三條件全中,移出紅列、記進 report["superseded"]:
  ① 有 superseded_by(工作項 id)· superseded_why · superseded_at          缺 → RED SUPERSEDED_INCOMPLETE
  ② 接手者存在 · 狀態 VERIFIED(不能是另一個 SUPERSEDED,不串鏈)         否 → RED SUPERSEDED_SUCCESSOR_INVALID
  ③ 接手者 id 在這一輪的 reusable_successes(收據此刻有效:標記 · 相依雜湊 · 日誌全對)否 → RED SUPERSEDED_SUCCESSOR_INVALID
退役項的舊收據與舊測試案一筆不刪(歷史);「改了沒測」照舊判(退役項的舊相依不算測過,要由其他有效案涵蓋)。
其餘照 v0107(Z281 雙胞移交 · 凍結收容件具名豁免 · 家族已登)。只收 VCGC 呼叫。零網路 · 不 import 他系統 · 不碰 TA-Lib。
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
VERSION = "v0108"
SUPERSEDED = "SUPERSEDED"
NEED = ("superseded_by", "superseded_why", "superseded_at")


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + ENGINE, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)                 # v0107:Z281 雙胞移交已裝進 v0101 的 audit
VIA = PRIOR.VIA
POLICY = PRIOR.POLICY
BASE = PRIOR.BASE


def apply_supersede(report: dict) -> dict:
    """INVALID_WORK_STATE 裡的 SUPERSEDED 工作項:接手者此刻有效綠才移出紅列;其餘一律照舊。"""
    items = report.get("work_items") or {}
    reusable = set(report.get("reusable_successes") or [])
    kept, retired, bad = [], [], []
    for row in report.get("rows", []):
        wid = row.get("detail")
        it = items.get(wid) if row.get("rule") == "INVALID_WORK_STATE" and isinstance(wid, str) else None
        if not it or it.get("state") != SUPERSEDED:
            kept.append(row)
            continue
        miss = [k for k in NEED if not it.get(k)]
        succ_id = it.get("superseded_by")
        succ = items.get(succ_id) if isinstance(succ_id, str) else None
        if miss:
            bad.append({"lamp": "RED", "rule": "SUPERSEDED_INCOMPLETE", "detail": {"id": wid, "missing": miss}})
        elif not succ or succ.get("state") != "VERIFIED" or succ_id not in reusable:
            why = ("接手者不存在" if not succ else "接手者狀態 %s(要 VERIFIED)" % succ.get("state")
                   if succ.get("state") != "VERIFIED" else "接手者收據此刻失效(先重跑它的案)")
            bad.append({"lamp": "RED", "rule": "SUPERSEDED_SUCCESSOR_INVALID", "detail": {"id": wid, "successor": succ_id, "why": why}})
        else:
            retired.append({"id": wid, "case": it.get("case"), "successor": succ_id, "why": it.get("superseded_why"),
                            "at": it.get("superseded_at"), "from_state": it.get("superseded_from_state")})
    rows = kept + bad
    lamps = [x["lamp"] for x in rows]
    lamp = "RED" if "RED" in lamps else "YELLOW" if lamps else "GREEN"
    report["rows"] = rows
    report["lamp"] = lamp
    report["closeout_lamp"] = ("RED" if lamp == "RED" else "YELLOW"
                               if report.get("pending") or lamp == "YELLOW" or report.get("z281_handover") else "GREEN")
    report["superseded"] = retired
    s = report.setdefault("summary", {})
    s["findings"] = len(rows)
    s["superseded"] = len(retired)
    return report


_V0107_AUDIT = BASE.audit


def audit(via=VIA, policy=None, baseline=None, require_baseline=True):
    return apply_supersede(_V0107_AUDIT(via, policy, baseline, require_baseline))


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
    BASE.audit = _V0107_AUDIT                   # 前版自測驗「v0107 裝在 v0101 全域」:跑前版時還原,跑完裝回本版
    try:
        rc = PRIOR.selftest()
    finally:
        BASE.audit = audit
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    def rep(items, reusable, extra_rows=(), **kw):
        rows = [{"lamp": "RED", "rule": "INVALID_WORK_STATE", "detail": i} for i, x in items.items()
                if x["state"] not in {"VERIFIED", "PENDING", "BLOCKED", "REVIEW"}] + list(extra_rows)
        return apply_supersede({"rows": rows, "pending": [], "summary": {}, "work_items": items,
                                "reusable_successes": list(reusable), **kw})
    full = {"superseded_by": "S", "superseded_why": "舊判決行已不印 · 尾版接手", "superseded_at": "2026-11-17T00:00:00Z",
            "superseded_from_state": "VERIFIED"}
    ok_items = {"S": {"state": "VERIFIED"}, "O1": {"state": SUPERSEDED, **full}, "O2": {"state": SUPERSEDED, **full}}
    r = rep(ok_items, {"S"})
    chk("ⓐ 接手者 VERIFIED 且收據此刻有效 → 退役項移出紅列 · 列進 superseded · 燈 GREEN",
        r["lamp"] == "GREEN" and [x["id"] for x in r["superseded"]] == ["O1", "O2"] and r["summary"]["superseded"] == 2, r)
    r = rep(ok_items, set())
    chk("ⓑ 接手者收據失效(不在 reusable)→ 每個退役項都 RED SUPERSEDED_SUCCESSOR_INVALID(不放行)",
        r["lamp"] == "RED" and sum(x["rule"] == "SUPERSEDED_SUCCESSOR_INVALID" for x in r["rows"]) == 2 and not r["superseded"], r)
    r = rep({"S": {"state": "PENDING"}, "O1": {"state": SUPERSEDED, **full}}, {"S"})
    chk("ⓒ 接手者不是 VERIFIED → RED", r["lamp"] == "RED" and r["rows"][0]["rule"] == "SUPERSEDED_SUCCESSOR_INVALID", r)
    r = rep({"S": {"state": SUPERSEDED, **full}, "O1": {"state": SUPERSEDED, **full}}, {"S"})
    chk("ⓓ 不串鏈:接手者自己也是 SUPERSEDED → RED", r["lamp"] == "RED" and not r["superseded"], r)
    r = rep({"S": {"state": "VERIFIED"}, "O1": {"state": SUPERSEDED, "superseded_by": "S"}}, {"S"})
    chk("ⓔ 缺 why / at → RED SUPERSEDED_INCOMPLETE", r["rows"][0]["rule"] == "SUPERSEDED_INCOMPLETE"
        and set(r["rows"][0]["detail"]["missing"]) == {"superseded_why", "superseded_at"}, r)
    r = rep({"S": {"state": "VERIFIED"}, "X": {"state": "DONE"}}, {"S"})
    chk("ⓕ 其他不認得的狀態照舊 RED INVALID_WORK_STATE(本版不放寬)", r["rows"] == [{"lamp": "RED", "rule": "INVALID_WORK_STATE", "detail": "X"}], r)
    r = rep(ok_items, {"S"}, [{"lamp": "RED", "rule": "CHANGED_CODE_WITHOUT_TEST", "detail": "functional modules/VDF/X_v0101.py"}])
    chk("ⓖ 改了沒測照舊紅(退役不抵測試)", r["lamp"] == "RED" and r["rows"][0]["rule"] == "CHANGED_CODE_WITHOUT_TEST", r)
    r = rep(ok_items, {"S"}, z281_handover=[{"path": "a.py"}])
    chk("ⓗ 前版判的驗收燈不被洗:有 Z281 移交 → 交接燈 GREEN · 驗收燈 YELLOW", r["lamp"] == "GREEN" and r["closeout_lamp"] == "YELLOW", r)
    chk("ⓘ 已裝進 v0101 模組全域(check / checkpoint 經本版 audit)", BASE.audit is audit)
    text = Path(__file__).read_text(encoding="utf-8")
    chk("ⓙ 檔頭:加速器橋 · 網路橋在(__future__ 之後)· 不碰 TA-Lib",
        "VIA:ACCEL-BRIDGE" in text and "VIA:NET-BRIDGE" in text and text.index("from __future__") < text.index("[VIA:ACCEL-BRIDGE")
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M))
    passed = rc == 0 and all(ok)
    print(f"[交接 {VERSION}] 本版 {sum(ok)}/{len(ok)} · 前版 {'PASS' if rc == 0 else 'FAIL'} · 被取代工作項 · {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
