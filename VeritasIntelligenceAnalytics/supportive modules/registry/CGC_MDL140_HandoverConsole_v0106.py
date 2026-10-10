#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL140_HandoverConsole v0106 — 薄尾:凍結收容件不當「待測程式」— 三條變更規則改具名豁免(INFO),監看照舊

操作員裁定(2026-10-10,PR #518;操作員 + AI 雙方同意改閘):
  main 894779cb 帶進 functional modules/VRN/references/(93)與 functional modules/VRN/intake/(26)等凍結收容件。
  它們是正本的收容副本:不能注入加速器橋(正本不碰)、registry-sync 不掃(scan_excluded)、也不是可單元測試的程式,
  v0101 卻把它們當「變更的程式碼」判 CHANGED_CODE_WITHOUT_TEST / MODULE_UNREGISTERED / ACCEL_BRIDGE_MISSING 三種紅,
  交接閘永遠紅、checkpoint 永遠拒寫。
本版:只對「凍結收容件」把這三條規則移出紅列,改記在報告 `frozen_material_exempt`(逐檔 · 規則 · 原因,具名可查),
  summary 帶豁免數。其餘一律照舊:
  · 監看範圍不變(檔仍在 state.files,改字 = CHECKPOINT_STALE、刪檔 = FILE_REMOVED 紅,照舊)
  · frozen_sources / 工具鎖 / 收據 / 待辦 / 需求的所有規則不變
  · 凍結收容件以外的程式一條都不豁免
凍結收容件 = 路徑前綴 FROZEN_MATERIAL_PREFIXES,或檔名是 `_sha<12 位十六進位>.py` 的存證副本(操作員 2026-10-10 令還原的 42 支同類)。
另修一處兩冊口徑不一(不是豁免):中央元件冊(VCGC registry-sync)依設計**只登尾版家族**(「版本變動不重發元件號」),
  v0101 卻要每支變動的版號檔各自出現在冊上 → 同一次新增的舊版號檔(例 HealthMatrix v0100–v0111)永遠「未登」。
  本版:有版號(_vNNNN)的檔,同夾同家族已有任一版登在冊上 = 已登(family_registered 逐檔記);沒版號的檔照舊逐檔判。
裝進 v0101 的模組全域 audit(check / checkpoint 都經它),其餘照 v0105。只收 VCGC 呼叫。零網路。
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
VERSION = "v0106"


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
BASE = PRIOR.BASE                               # v0101:audit / checkpoint / main 都查它的模組全域

FROZEN_MATERIAL_PREFIXES = ("functional modules/VRN/references/", "functional modules/VRN/intake/")
SHA_COPY = re.compile(r"_sha[0-9a-f]{12}\.py$")
EXEMPT_RULES = frozenset({"CHANGED_CODE_WITHOUT_TEST", "MODULE_UNREGISTERED", "ACCEL_BRIDGE_MISSING"})
WHY = {
    "prefix": "凍結收容件(正本收容副本):不注入橋、不入註冊掃描、不是待測程式;監看與刪檔紅照舊(操作員 2026-10-10 裁定)",
    "sha": "存證副本 _sha<hash>(操作員 2026-10-10 令還原的 FILE_REMOVED 同類):不是待測程式;監看與刪檔紅照舊",
}


def frozen_kind(rel) -> str:
    rel = str(rel).replace("\\", "/")
    if rel.startswith(FROZEN_MATERIAL_PREFIXES):
        return "prefix"
    if SHA_COPY.search(rel):
        return "sha"
    return ""


_VERSIONED = re.compile(r"^(?P<fam>.+)_v\d{4}\.(py|ps1)$")


def family_of(rel) -> str:
    """同夾同家族鍵:去掉 _vNNNN 的路徑;沒版號 = 空字串(照舊逐檔判)。"""
    m = _VERSIONED.match(str(rel).replace("\\", "/"))
    return m.group("fam") if m else ""


def registered_families(sources) -> set:
    return {f for f in (family_of(s) for s in sources if s) if f}


def apply_exemption(report: dict, families: set | None = None) -> dict:
    """三條變更規則 × 凍結收容件 → 移出 rows,記進 frozen_material_exempt;
    MODULE_UNREGISTERED × 家族已登 → 移出 rows,記進 family_registered;燈號照 v0101 同一算法重算。"""
    kept, exempt, fam_ok = [], [], []
    families = families or set()
    for row in report.get("rows", []):
        detail = row.get("detail")
        kind = frozen_kind(detail) if row.get("rule") in EXEMPT_RULES and isinstance(detail, str) else ""
        if kind:
            exempt.append({"rule": row["rule"], "path": detail, "why": WHY[kind]})
        elif row.get("rule") == "MODULE_UNREGISTERED" and isinstance(detail, str) and family_of(detail) in families:
            fam_ok.append(detail)
        else:
            kept.append(row)
    lamps = [x["lamp"] for x in kept]
    lamp = "RED" if "RED" in lamps else "YELLOW" if lamps else "GREEN"
    report["rows"] = kept
    report["lamp"] = lamp
    report["closeout_lamp"] = "RED" if lamp == "RED" else "YELLOW" if report.get("pending") or lamp == "YELLOW" else "GREEN"
    report["frozen_material_exempt"] = exempt
    report["family_registered"] = fam_ok
    summary = report.setdefault("summary", {})
    summary["findings"] = len(kept)
    summary["frozen_material_exempt"] = len(exempt)
    summary["family_registered"] = len(fam_ok)
    return report


_V0101_AUDIT = BASE.audit


def _inventory_sources(via=None, policy=None) -> list:
    via = Path(via or VIA)
    policy = policy or BASE.read(via / POLICY.relative_to(VIA))
    inv = BASE.local(via, policy["component_inventory"])
    return [x.get("source") for x in BASE.read(inv).get("records", [])] if inv.exists() else []


def audit(via=VIA, policy=None, baseline=None, require_baseline=True):
    report = _V0101_AUDIT(via, policy, baseline, require_baseline)
    return apply_exemption(report, registered_families(_inventory_sources(via, policy)))


BASE.audit = audit                              # v0101 checkpoint() / main() 以模組全域名呼叫 audit


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
    rc = PRIOR.selftest()
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    ref = "functional modules/VRN/references/x/a.py"
    intake = "functional modules/VRN/intake/b.py"
    shacopy = "functional modules/VDF/VDF_X_shad7fd781ac69f.py"
    live = "supportive modules/registry/CGC_MDL999_Live_v0100.py"
    rep = apply_exemption({"rows": [
        {"lamp": "RED", "rule": "CHANGED_CODE_WITHOUT_TEST", "detail": ref},
        {"lamp": "RED", "rule": "ACCEL_BRIDGE_MISSING", "detail": intake},
        {"lamp": "RED", "rule": "MODULE_UNREGISTERED", "detail": shacopy}], "pending": [], "summary": {}})
    chk("① 凍結收容件三條變更規則 → 豁免;只剩它們時燈 GREEN", rep["lamp"] == "GREEN" and len(rep["frozen_material_exempt"]) == 3
        and rep["summary"]["frozen_material_exempt"] == 3 and rep["summary"]["findings"] == 0)
    rep = apply_exemption({"rows": [{"lamp": "RED", "rule": "FILE_REMOVED", "detail": ref},
                                    {"lamp": "YELLOW", "rule": "CHECKPOINT_STALE", "detail": [ref]}], "pending": [], "summary": {}})
    chk("② 收容件被刪 = FILE_REMOVED 照舊紅;改字 = CHECKPOINT_STALE 照舊", rep["lamp"] == "RED" and len(rep["rows"]) == 2 and not rep["frozen_material_exempt"])
    rep = apply_exemption({"rows": [{"lamp": "RED", "rule": "CHANGED_CODE_WITHOUT_TEST", "detail": live},
                                    {"lamp": "RED", "rule": "ACCEL_BRIDGE_MISSING", "detail": "functional modules/VRN/VRN_ENG400_X_v0100.py"}],
                           "pending": [], "summary": {}})
    chk("③ 收容件以外的程式一條都不豁免", rep["lamp"] == "RED" and len(rep["rows"]) == 2 and not rep["frozen_material_exempt"])
    rep = apply_exemption({"rows": [{"lamp": "RED", "rule": "SUCCESS_LOCK_CHANGED", "detail": ref},
                                    {"lamp": "RED", "rule": "EVIDENCE_INVALID", "detail": {"id": "x", "why": [ref]}}],
                           "pending": [{"id": "p"}], "summary": {}})
    chk("④ 成功鎖 / 收據規則不豁免;待辦在 → 驗收燈不會是 GREEN", rep["lamp"] == "RED" and rep["closeout_lamp"] == "RED" and len(rep["rows"]) == 2)
    rep = apply_exemption({"rows": [], "pending": [{"id": "p"}], "summary": {}})
    chk("⑤ 交接燈 GREEN 時,有待辦 → 驗收燈 YELLOW(照 v0101 算法)", rep["lamp"] == "GREEN" and rep["closeout_lamp"] == "YELLOW")
    fams = registered_families(["supportive modules/registry/CGC_MDL998_Fam_v0112.py", "x/NoVersion.py"])
    rep = apply_exemption({"rows": [
        {"lamp": "RED", "rule": "MODULE_UNREGISTERED", "detail": "supportive modules/registry/CGC_MDL998_Fam_v0100.py"},
        {"lamp": "RED", "rule": "MODULE_UNREGISTERED", "detail": "supportive modules/other/CGC_MDL998_Fam_v0100.py"},
        {"lamp": "RED", "rule": "MODULE_UNREGISTERED", "detail": "x/NoVersion2.py"},
        {"lamp": "RED", "rule": "CHANGED_CODE_WITHOUT_TEST", "detail": "supportive modules/registry/CGC_MDL998_Fam_v0100.py"}],
        "pending": [], "summary": {}}, fams)
    chk("⑥ 家族已登(同夾同家族有版登冊)= 已登;別夾同名 · 沒版號 · 沒測試照舊紅", rep["family_registered"] == ["supportive modules/registry/CGC_MDL998_Fam_v0100.py"]
        and len(rep["rows"]) == 3 and fams == {"supportive modules/registry/CGC_MDL998_Fam"})
    chk("⑦ 已裝進 v0101 模組全域(check / checkpoint 經本版 audit)", BASE.audit is audit)
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 檔頭:加速器橋 · 網路橋在(__future__ 之後)· 不碰 TA-Lib",
        "VIA:ACCEL-BRIDGE" in text and "VIA:NET-BRIDGE" in text and text.index("from __future__") < text.index("[VIA:ACCEL-BRIDGE")
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M))
    passed = rc == 0 and all(ok)
    print(f"[交接 {VERSION}] 本版 {sum(ok)}/{len(ok)} · 前版 {'PASS' if rc == 0 else 'FAIL'} · 凍結收容件具名豁免 · {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
