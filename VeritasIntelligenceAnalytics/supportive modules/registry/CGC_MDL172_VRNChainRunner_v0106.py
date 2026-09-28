#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL172_VRNChainRunner v0106 — 薄尾:逐節點逾時冊(有理由才放寬;沒有自測門照舊 NODATA)

工作站 2026-09-28 兩次全景實測:VRN_ENG072_FirstPageText 與 VRN_AutoTestLoop 每次都在 180s 逾時 → NODATA(沒跑完=沒有結論)。
v0105 的逾時寫死 DEFAULT_TIMEOUT=180,沒有逐節點的口。本尾版讀 `VIA_VRN_ChainNodeLedger_v*.json`(取尾版)的 timeouts:
  · 只在一般 run(逾時 = DEFAULT_TIMEOUT)才放寬到冊上的秒數;--fast 不放寬;冊上沒列的照舊。
  · 每一筆都必須有 why(L87);沒有 why 的那筆不採用,照實列在 skipped。
  · 放寬過的節點,結果 detail 前面註明「逾時冊放寬到 Ns」,報告看得到。
不收免測:沒有自測門的節點照 v0105 報 NODATA(要補門,不開後門)。其餘全照 v0105(L04 舊版一字不動)。
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

import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL172_VRNChainRunner"
PRIOR_PATH = [p for p in sorted(HERE.glob(_STEM + "_v*.py")) if p.name < Path(__file__).name][-1]
_spec = importlib.util.spec_from_file_location("vrnchain_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
VERSION = Path(__file__).stem.rsplit("_v", 1)[-1]


def ledger_path() -> Path | None:
    hits = sorted(HERE.glob("VIA_VRN_ChainNodeLedger_v*.json"))
    return hits[-1] if hits else None


def load_timeouts(path: Path | None = None) -> tuple[dict, list]:
    """回 (family → 秒數, 沒採用的列)。沒有 why 或秒數不是正整數 = 不採用(L87)。"""
    path = path if path is not None else ledger_path()
    if path is None or not Path(path).is_file():
        return {}, []
    raw = json.loads(Path(path).read_text(encoding="utf-8")).get("timeouts") or {}
    ok, skipped = {}, []
    for fam, v in raw.items():
        sec = (v or {}).get("sec")
        why = str((v or {}).get("why") or "").strip()
        if isinstance(sec, int) and sec > 0 and why:
            ok[fam] = sec
        else:
            skipped.append(f"{fam}:{'缺 why' if not why else '秒數不對'}")
    return ok, skipped


_PRIOR_RUN_NODE = PRIOR.run_node
_LEDGER_CACHE: list = []


def run_node(layer: str, node: dict, timeout: int) -> dict:
    if not _LEDGER_CACHE:
        _LEDGER_CACHE.append(load_timeouts())
    table, _skipped = _LEDGER_CACHE[0]
    fam = node.get("family") or ""
    sec = table.get(fam)
    if sec and timeout == PRIOR.DEFAULT_TIMEOUT and sec > timeout:
        got = _PRIOR_RUN_NODE(layer, node, sec)
        got["detail"] = f"逾時冊放寬到 {sec}s / " + str(got.get("detail") or "")
        return got
    return _PRIOR_RUN_NODE(layer, node, timeout)


PRIOR.run_node = run_node        # v0105 的 collect / main 一律走本尾版


def __getattr__(name):
    return getattr(PRIOR, name)


def selftest() -> int:
    rc = PRIOR.selftest()
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + note) if note else ''}")

    print(f"=== {_STEM} v{VERSION} 薄尾加檢(逐節點逾時冊)===")
    real, skipped = load_timeouts()
    chk("⓪ 逾時冊在、每筆都有理由(L87)", ledger_path() is not None and real and not skipped,
        f"{ledger_path().name if ledger_path() else '不在'} · {len(real)} 筆 · 不採用 {len(skipped)}")
    with tempfile.TemporaryDirectory() as td:
        bad = Path(td) / "ledger.json"
        bad.write_text(json.dumps({"timeouts": {"A": {"sec": 600}, "B": {"sec": "x", "why": "w"}, "C": {"sec": 300, "why": "有理由"}}}), encoding="utf-8")
        t2, s2 = load_timeouts(bad)
        chk("⓪ 沒有 why / 秒數不對的那筆不採用,照實列出", t2 == {"C": 300} and len(s2) == 2, "; ".join(s2))
    probe = PRIOR.VIA / "VIA_Reports" / "_vrnchain_probe_v0106"
    probe.mkdir(parents=True, exist_ok=True)
    slow = probe / "slowgate_probe.py"
    slow.write_text('import sys, time\nif "--selftest" in sys.argv:\n    time.sleep(3)\n    print("  [OK] slow probe")\n', encoding="utf-8")
    node = {"family": "PROBE_SLOW", "tail": str(slow.relative_to(PRIOR.VIA))}
    keep_default = PRIOR.DEFAULT_TIMEOUT
    try:
        PRIOR.DEFAULT_TIMEOUT = 1
        _LEDGER_CACHE[:] = [({"PROBE_SLOW": 20}, [])]
        g1 = run_node("L9_試", node, 1)
        chk("① 冊上有列、一般 run:放寬後跑完 = GREEN,detail 註明放寬", g1["state"] == "GREEN" and "逾時冊放寬到 20s" in g1["detail"], g1["state"])
        g2 = run_node("L9_試", dict(node, family="PROBE_OTHER"), 1)
        chk("② 冊上沒列:照舊逾時 = NODATA(不是紅)", g2["state"] == "NODATA" and "逾時冊" not in g2["detail"], g2["state"])
        g3 = run_node("L9_試", node, 0)
        chk("③ --fast(逾時 ≠ 預設)不放寬", "逾時冊" not in str(g3.get("detail")), g3["state"])
    finally:
        PRIOR.DEFAULT_TIMEOUT = keep_default
        _LEDGER_CACHE[:] = []
        slow.unlink()
        probe.rmdir()
    nodoor = PRIOR.selftest_door
    with tempfile.TemporaryDirectory() as td:
        nd = Path(td) / "nodoor_probe.py"
        nd.write_text("print('x')\n", encoding="utf-8")
        chk("④ 沒有自測門照舊判「沒有自測門」(本尾版不開免測後門)", nodoor(nd)[0] is False)
    ok = rc == 0 and all(results)
    print(f"  [計] {_STEM} v{VERSION} 薄尾 {sum(results)}/{len(results)} · v0105 本體 {'PASS' if rc == 0 else 'FAIL'} · 合計 {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        print(f"=== VRN 六層鏈 v{VERSION} · v0105 廿六檢 + 薄尾加檢(沙盒零網路)===")
        return selftest()
    return PRIOR.main(a)


if __name__ == "__main__":
    sys.exit(main())
