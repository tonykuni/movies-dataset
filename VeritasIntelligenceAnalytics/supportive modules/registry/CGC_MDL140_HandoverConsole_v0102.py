#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL140_HandoverConsole v0102 — 薄尾:收據沿用前重掃相依樣式(相依檔集合變了 = 證據失效,重跑)

實測(側線 2026-09-29 i 收尾):v0101 判「沿用成功」只比收據上記的相依雜湊;新尾版(CGC_MDL149 v0178 · CGC_MDL245 v0104)
符合 case 宣告的 `_v*.py` 樣式卻不在舊收據裡,entry / sdd 兩案被判沿用,實際沒測到新尾版(交接待辦 VCGC-REQ075:reuse-glob · 風險 R02)。
  ① evidence_status():v0101 的檢查照舊,再把收據相依集合跟「case 宣告樣式 + VCGC 入口樣式」現在掃到的檔案集合比;
     多了或少了檔 = dependency set changed(列出多 / 少各幾支)。check 的 EVIDENCE_INVALID 與 test 的沿用判定都走這一支,
     所以新尾版一落地,check 會紅、test 會照 v0101 原格式把舊收據存進 evidence/history 後重跑。
  ② 其餘照 v0101(政策冊 VIA_Handoff_Continuity_SSOT_v0100 · checkpoint · 收據格式都不動)。只收 VCGC 呼叫。零網路。
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
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL140_HandoverConsole"
ENGINE = Path(__file__).stem
VCGC_GLOB = "supportive modules/registry/CGC_MDL149_VeritasCentralGovernanceConsole_v*.py"


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + ENGINE, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
VIA = PRIOR.VIA
POLICY = PRIOR.POLICY
_V0101_EVIDENCE = PRIOR.evidence_status


def __getattr__(name: str):
    return getattr(PRIOR, name)


def dependency_set(via, case: dict) -> set:
    """VIA-relative files the case's declared patterns (plus the VCGC entry pattern) match right now — what a receipt must cover."""
    via = Path(via)
    out = set()
    for pattern in list(case.get("dependencies") or []) + [VCGC_GLOB]:
        out.update(p.relative_to(via).as_posix() for p in via.glob(pattern) if p.is_file())
    return out


def set_drift(via, receipt: dict, policy: dict | None = None) -> tuple:
    """(new, gone): files the patterns match now but the receipt never hashed, and receipt files that no longer exist."""
    try:
        policy = policy or PRIOR.read(Path(via) / POLICY.relative_to(PRIOR.VIA))
    except (OSError, ValueError):
        return [], []
    case = (policy.get("test_cases") or {}).get(receipt.get("case") or "")
    if not case:
        return [], []
    now, had = dependency_set(via, case), set(receipt.get("dependencies") or {})
    return sorted(now - had), sorted(had - now)


def evidence_status(via, receipt):
    """v0101's exact-marker and hash checks, plus: the dependency set must still be the one the declared patterns match."""
    errors = list(_V0101_EVIDENCE(via, receipt))
    new, gone = set_drift(via, receipt)
    if new or gone:
        errors.append(f"dependency set changed: +{len(new)} new / -{len(gone)} gone "
                      + " ".join(Path(x).name for x in (new + gone)[:4]))
    return errors


PRIOR.evidence_status = evidence_status        # audit()'s EVIDENCE_INVALID and run_case()'s reuse decision both look it up here


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"] and os.environ.get("VIA_FROM_VCGC") == "YES":
        return selftest()
    return PRIOR.main(argv)


def selftest():
    rc = PRIOR.selftest()
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    with tempfile.TemporaryDirectory() as tmp:
        via = Path(tmp)
        reg = via / "supportive modules" / "registry"
        reg.mkdir(parents=True)
        for name in ("CGC_MDL999_Demo_v0100.py", "CGC_MDL149_VeritasCentralGovernanceConsole_v0100.py"):
            (reg / name).write_text("x = 1\n", encoding="utf-8")
        policy = {"test_cases": {"demo": {"argv": ["CGC_MDL999_Demo", "--selftest"], "success_marker": "ok",
                                          "dependencies": ["supportive modules/registry/CGC_MDL999_Demo_v*.py"]}}}
        (reg / POLICY.name).write_text(json.dumps(policy), encoding="utf-8")
        ev = via / "docs" / "handoff" / "evidence"
        ev.mkdir(parents=True)
        (ev / "demo.txt").write_text("ok\n", encoding="utf-8")
        deps = {rel: PRIOR.sha(via / rel) for rel in sorted(dependency_set(via, policy["test_cases"]["demo"]))}
        receipt = {"schema": "VIA.Handoff.TestReceipt.v1", "case": "demo", "command": ["x"], "rc": 0, "target_marker_seen": True,
                   "completed_at": "2026-09-30T00:00:00+00:00", "dependencies": deps, "log": "docs/handoff/evidence/demo.txt",
                   "log_sha256": PRIOR.sha(ev / "demo.txt")}
        clean = evidence_status(via, receipt)
        (reg / "CGC_MDL999_Demo_v0101.py").write_text("x = 2\n", encoding="utf-8")
        grown = evidence_status(via, receipt)
        (reg / "CGC_MDL999_Demo_v0101.py").unlink()
        (reg / "CGC_MDL149_VeritasCentralGovernanceConsole_v0100.py").unlink()
        shrunk = evidence_status(via, receipt)
    chk("① 相依集合沒變:v0101 的檢查照舊、不多報", clean == [], clean)
    chk("② 新尾版落地(符合樣式、不在收據)= 證據失效(沿用擋下)", any(e.startswith("dependency set changed: +1 new") for e in grown), grown)
    chk("③ 收據上的檔不見了 = 證據失效(雜湊檢查與集合檢查都報)",
        any("dependency set changed: +0 new / -1 gone" in e for e in shrunk) and any(e.startswith("dependency changed") for e in shrunk), shrunk)
    chk("④ check 與 test 走同一支:本版裝進 v0101 的模組全域", PRIOR.evidence_status is evidence_status)
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑤ 檔頭 · 加速器橋 · 網路橋在;不碰 TA-Lib", "VIA:ACCEL-BRIDGE" in text and "VIA:NET-BRIDGE" in text
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M))
    print(f"[交接 v0102] 本版 {sum(ok)}/{len(ok)}")
    return 0 if rc == 0 and all(ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
