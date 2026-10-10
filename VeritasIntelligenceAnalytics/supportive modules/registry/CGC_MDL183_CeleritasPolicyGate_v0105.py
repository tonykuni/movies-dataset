#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL183_CeleritasPolicyGate v0105 — 薄尾:VRN 側收容件 = 凍結收容(INFO)· 唯讀本名冊照工具鎖冊扣掉退場座位 · 既有債扣 PS 退役帳

實錄(2026-10-10,PR #518 交接收據 celeritas_gate_v0104 重跑 FAIL):
  ① main 收進 functional modules/VRN/intake/VRN_v0108_Annual/(凍結收容件,CLAUDE.md:凍結來源不改)。
     v0104 只認 supportive modules/intake/ 為收容 → 它的 .py 缺橋與 .ps1 缺章都被算成「基線外新缺」紅。
     本版:收容前綴加 functional modules/VRN/intake/;PY 缺橋與 PS 缺章裡在收容夾下的,都移到 intake(INFO 照列,不消失)。
  ② ⑦ 唯讀本名冊(基線資料檔 py_readonly)裡的 supportive modules/accelerator/VeritasCeleritas.py
     已登在工具版本鎖冊 VIA_ToolVersion_Lock_v0100.json 的 removed(退場座位);
     操作員 2026-10-10:加速器 / 網路工具 / PS 模板統一用鎖冊上的版號正本(VeritasCeleritas_v1141 · AegisNexus_v1652)。
     本版:有效唯讀本 = 基線 py_readonly − 鎖冊 removed;基線資料檔一個字都不改(批709)。
  ③ v0101 ④ 既有債棘輪要求「樹上既有債支數 = 有效基線支數」。main 894779cb 以 CGC_MDL274 --retire-ps 把 22 支
     無加速器舊 .ps1 退役到 _superseded(記帳 VIA_PsRetire_Ledger_v0100.jsonl),基線卻仍把它們算債 → 50 ≠ 28 假紅。
     本版:有效既有債再扣「退役帳登記退役且原位已不在」的 .ps1(只讀帳,不改帳、不改基線)。
  其餘(活檔沒章 · 版史規則 · 已還債棘輪 · PS 稽核委派引擎)全照 v0104。只收 VCGC 呼叫。零網路。
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
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL183_CeleritasPolicyGate"
PRIOR_PATH = [p for p in sorted(HERE.glob(_STEM + "_v*.py")) if p.name < Path(__file__).name][-1]
_spec = importlib.util.spec_from_file_location("cgc_mdl183_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
V0101 = PRIOR.V0101
VERSION = "v" + Path(__file__).stem.rsplit("_v", 1)[-1]
PS_MARK = PRIOR.PS_MARK
_SCAN_V0104 = PRIOR.scan
_BASELINE_PRIOR = V0101.baseline
INTAKE_PREFIXES = ("supportive modules/intake/", "functional modules/VRN/intake/")
TOOL_LOCK = HERE / "VIA_ToolVersion_Lock_v0100.json"
PS_RETIRE_LEDGER = HERE / "VIA_PsRetire_Ledger_v0100.jsonl"


def __getattr__(name):
    return getattr(PRIOR, name)


def is_intake(rel: str) -> bool:
    """路徑前綴是收容夾(supportive 側或 VRN 側)才算;只是含 intake 字樣不算。"""
    r = str(rel).replace("\\", "/")
    return any(r.startswith(p) for p in INTAKE_PREFIXES)


def lock_removed() -> set:
    """工具版本鎖冊的退場座位(相對 VIA 樹根);讀不到就空集合(照舊,不自己列一張)。"""
    try:
        d = json.loads(TOOL_LOCK.read_text(encoding="utf-8"))
    except Exception:
        return set()
    return {str(x).replace("\\", "/") for x in (d.get("removed") or [])}


def ps_retired() -> set:
    """PS 退役帳(CGC_MDL274 --retire-ps,只增)登記退役、且樹上確實已不在原位的 .ps1(相對 VIA 樹根)。"""
    out = set()
    try:
        lines = PS_RETIRE_LEDGER.read_text(encoding="utf-8").splitlines()
    except Exception:
        return out
    for line in lines:
        try:
            r = json.loads(line)
        except Exception:
            continue
        rel = str(r.get("path") or "").replace("\\", "/")
        if str(r.get("action", "")).startswith("RETIRE_PS") and rel and not (V0101.VIA / rel).exists():
            out.add(rel)
    return out


def baseline() -> dict:
    """同前版有效基線;py_readonly 扣掉鎖冊 removed(退場座位不是正典唯讀本);
    ps1_debt 扣掉 PS 退役帳上已退役且不在原位的(退役 = 債已了結,不是債也不是新缺)。"""
    b = dict(_BASELINE_PRIOR() or {})
    debt = dict(b.get("ps1_debt") or {})
    dfiles = list(debt.get("files") or [])
    gone_ps = ps_retired()
    if dfiles and gone_ps:
        debt["files"] = [f for f in dfiles if f not in gone_ps]
        debt["retired_by_ps_ledger"] = sorted(set(dfiles) & gone_ps)
        b["ps1_debt"] = debt
    ro = dict(b.get("py_readonly") or {})
    files = list(ro.get("files") or [])
    gone = lock_removed()
    if files and gone:
        ro["files"] = [f for f in files if f not in gone]
        ro["retired_by_tool_lock"] = sorted(set(files) & gone)
        b["py_readonly"] = ro
    return b


def scan(root: Path | None = None) -> dict:
    """同 v0104;PY 缺橋與 PS 基線外新缺裡在收容夾下的 → intake(INFO 照列),其餘照紅。"""
    s = _SCAN_V0104(root)
    for side, key in (("py", "missing"), ("ps", "new_missing")):
        d = s.get(side)
        if not isinstance(d, dict):
            return s
        miss = d.get(key) or []
        d["intake"] = sorted(set(d.get("intake") or []) | {r for r in miss if is_intake(r)})
        d[key] = [r for r in miss if not is_intake(r)]
        d["state"] = "GREEN" if not d[key] else "RED"
    s["state"] = "GREEN" if s["py"]["state"] == "GREEN" and s["ps"]["state"] == "GREEN" else "RED"
    return s


def _install_v0105() -> None:
    V0101.baseline = baseline        # v0101 的 scan / ⑦ 讀有效唯讀本
    V0101.scan = scan                # v0101 的 report 讀模組層 scan
    PRIOR.PRIOR.PRIOR.scan = scan    # v0102
    PRIOR.PRIOR.scan = scan          # v0103
    PRIOR.scan = scan                # v0104 的 ⑱ 與各層同一把尺


_install_v0105()
report = V0101.report


def selftest() -> int:
    rc = PRIOR.selftest()            # v0101 八檢 + v0102 + v0103 + v0104 加檢照跑(實樹以本版規則量)
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' (' + note + ')') if note else ''}")

    print(f"=== {_STEM} {VERSION} 薄尾加檢(VRN 收容件 INFO · 唯讀本扣鎖冊退場座位)===")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        pack = root / "functional modules" / "VRN" / "intake" / "Pack_v9999"
        pack.mkdir(parents=True)
        (pack / "Run.ps1").write_text("Write-Host 1\n", encoding="utf-8")
        (pack / "tool.py").write_text("x = 1\n", encoding="utf-8")
        live = root / "functional modules" / "VRN" / "intake_like"
        live.mkdir(parents=True)
        (live / "Run.ps1").write_text("Write-Host 2\n", encoding="utf-8")
        s = scan(root)
        ps, py = s.get("ps") or {}, s.get("py") or {}
        chk("⑳ VRN 收容夾 .ps1 / .py → intake(INFO 照列);收容夾外同名、只含 intake 字樣的活檔照紅(負控)",
            s.get("state") != "NODATA"
            and "functional modules/VRN/intake/Pack_v9999/Run.ps1" in (ps.get("intake") or [])
            and "functional modules/VRN/intake/Pack_v9999/tool.py" in (py.get("intake") or [])
            and ps.get("new_missing") == ["functional modules/VRN/intake_like/Run.ps1"] and ps.get("state") == "RED",
            f"ps.intake {ps.get('intake')} · py.intake {py.get('intake')} · 新缺 {ps.get('new_missing')}")
    gone = lock_removed()
    b = baseline()
    ro = (b.get("py_readonly") or {}).get("files") or []
    chk("㉑ 有效唯讀本 = 基線 − 鎖冊 removed(退場座位不算正典唯讀本;基線資料檔不改)",
        bool(gone) and not (set(ro) & gone) and bool(ro), f"唯讀本 {len(ro)} · 鎖冊退場 {len(gone)}")
    pdebt = (b.get("ps1_debt") or {}).get("retired_by_ps_ledger") or []
    chk("㉒a 有效既有債 = 基線 − 已還 − PS 退役帳(已退役且不在原位);退役件不再列債",
        all(not (V0101.VIA / f).exists() for f in pdebt) and not (set(pdebt) & set((b.get("ps1_debt") or {}).get("files") or [])),
        f"退役扣除 {len(pdebt)}")
    real = scan()
    chk("㉒ 實樹:PY 缺 0 · PS 基線外新缺 0(收容件照列不消失)",
        not (real.get("py") or {}).get("missing") and not (real.get("ps") or {}).get("new_missing"),
        f"PY 缺 {(real.get('py') or {}).get('missing')} · PS 新缺 {(real.get('ps') or {}).get('new_missing')}")
    chk("㉓ report 與各層 scan / baseline 同一把尺", V0101.scan is scan and PRIOR.scan is scan and V0101.baseline is baseline)
    ok = rc == 0 and all(results)
    print(f"  [計] {_STEM} {VERSION} 本版 {sum(results)}/{len(results)} · 前版 {'PASS' if rc == 0 else 'FAIL'} · 合計 {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    print(f"=== Celeritas 產出契約閘 {VERSION}(薄尾 · 收容件(supportive / VRN)= 凍結收容 INFO · 執法 L102)===")
    return report()


if __name__ == "__main__":
    raise SystemExit(main())
