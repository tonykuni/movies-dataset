#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL170_VDFChainRunner v0103 — 薄尾:0c 獨立性認得「審過的單向讀取」

工作站 2026-09-28 15:41 VDF 鏈 rc=2(NODATA 1 · GREEN 9):只差 0c。v0102 把 VDF_ENG063(讀 VRN_ENG069 的名冊)與
VDF_ENG094(呼叫 VRN_ENG090.pkg_integrity)都算成「真依賴」→ NODATA;它自己的修法句卻寫「單向讀取可接受,回寫兄弟家族就不是獨立」,
只是沒有地方記「已審過、是單向讀取」。本尾版只換 0c 這一站:

  · 依賴仍逐支量(v0102 的掃描原樣跑),再對照 VIA_VDF_OneWayRead_Waivers_v0100.json
  · 該家族每一處命中都指向豁免登記的目標,且豁免列的每個函式名仍出現在原始碼 → 算「單向讀取(已審)」
  · 有任何一處沒登記、或登記的呼叫名不見了(= 程式改了,要重審)→ 照 v0102 回 NODATA
  · 全部是已審單向讀取 → GREEN,細節照列(不藏),並提醒日後解耦(Z252)
其餘各站、rc 對照、紀錄檔全照 v0102(L04 舊版一字不動;L05 不另立尺)。
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
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL170_VDFChainRunner"
PRIOR_PATH = [p for p in sorted(HERE.glob(_STEM + "_v*.py")) if p.name < Path(__file__).name][-1]
_spec = importlib.util.spec_from_file_location("cgc_mdl170_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)

WAIVERS = HERE / "VIA_VDF_OneWayRead_Waivers_v0100.json"
_BASE_STANDALONE = PRIOR.standalone_check


def __getattr__(name):
    return getattr(PRIOR, name)


def _waivers(path: Path = WAIVERS) -> list:
    try:
        return list(json.loads(path.read_text(encoding="utf-8")).get("waivers") or [])
    except Exception:
        return []


def _tails(eng_dir: Path) -> dict:
    fams = {}
    for p in sorted(eng_dir.glob("*.py")):
        base = re.sub(r"_v\d{4}\.py$", "", p.name).replace(".py", "")
        if base not in fams or p.name > fams[base].name:
            fams[base] = p
    return fams


def classify(eng_dir: Path, waivers: list) -> dict:
    """逐家族把指向兄弟家族的命中分成:收容件 · 已審單向讀取 · 未審依賴。"""
    fams = _tails(eng_dir)
    filed, reviewed, open_dep = [], [], []
    for base, p in fams.items():
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore").replace("\\", "/")
        except OSError as e:
            open_dep.append(f"{base}→(讀不動:{type(e).__name__};量不到不算獨立)")
            continue
        mine = [w for w in waivers if w.get("family") == base]
        for sib in PRIOR._SIBLING:
            for m in re.finditer(re.escape(sib) + r"[^\"\'\n]*", txt):
                seg = m.group(0)
                if "/references/intake/" in seg:
                    filed.append(f"{base}→{seg[:64]}")
                    continue
                ok = next((w for w in mine if w.get("target") == sib and w.get("direction") == "read-only"
                           and w.get("module_glob", "").split("_v")[0] in txt
                           and all(c in txt for c in w.get("calls") or [])), None)
                (reviewed if ok else open_dep).append(f"{base}→{seg[:64]}")
    return {"families": len(fams), "filed": sorted(set(filed)), "reviewed": sorted(set(reviewed)), "open": sorted(set(open_dep))}


def standalone_check() -> dict:
    eng = PRIOR.VDF_ENG
    if not eng.is_dir():
        return _BASE_STANDALONE()
    c = classify(eng, _waivers())
    st = "GREEN" if not c["open"] else "NODATA"
    det = (f"{c['families']} 個 ENG 家族 · **真依賴兄弟家族 {len(c['open'])}**"
           + (f":{' · '.join(c['open'][:4])}" if c["open"] else " —— **VDF 這一側是獨立的**")
           + (f" · 單向讀取(已審,登在 {WAIVERS.name}){len(c['reviewed'])}:{' · '.join(c['reviewed'][:3])}" if c["reviewed"] else "")
           + (f" · 另有 {len(c['filed'])} 處是收容件路徑(讀它不等於依賴那個家族)" if c["filed"] else ""))
    fix = ("" if not c["open"] else "逐支看那幾行:確認只讀不回寫就登進單向讀取豁免冊(附理由);回寫兄弟家族就不是獨立,要改碼")
    return PRIOR.stage("0c", "VDF 獨立性", st, det, fix, evidence=PRIOR.rel(eng))


PRIOR.standalone_check = standalone_check     # v0102 的 collect / main 用本尾版的 0c


def selftest() -> int:
    rc = PRIOR.selftest()
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' (' + note + ')') if note else ''}")

    print("=== VDF 鏈跑器 v0103 薄尾加檢(0c 單向讀取豁免)===")
    real = classify(PRIOR.VDF_ENG, _waivers())
    chk("⑳ 真樹:ENG063 / ENG094 兩處命中都對上豁免冊,未審依賴 0", not real["open"] and len(real["reviewed"]) >= 2,
        f"已審 {real['reviewed']} · 未審 {real['open']}")
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        (d / "VDF_ENG900_Fake_v0100.py").write_text("p = VIA / 'functional modules/VRN'\nimport x  # VRN_ENG001_Thing_v*.py\nx.read_it()\n", encoding="utf-8")
        (d / "VDF_ENG901_Other_v0100.py").write_text("q = 'functional modules/VAP/y'\n", encoding="utf-8")
        w = [{"family": "VDF_ENG900_Fake", "target": "functional modules/VRN", "module_glob": "VRN_ENG001_Thing_v*.py",
              "calls": ["read_it"], "direction": "read-only", "why": "test"}]
        a = classify(d, w)
        chk("㉑ 負控:沒登記的依賴(ENG901→VAP)仍是未審依賴", a["open"] == ["VDF_ENG901_Other→functional modules/VAP/y"], str(a["open"]))
        chk("㉒ 登記的單向讀取算已審", a["reviewed"] == ["VDF_ENG900_Fake→functional modules/VRN"], str(a["reviewed"]))
        (d / "VDF_ENG900_Fake_v0101.py").write_text("p = VIA / 'functional modules/VRN'\nimport x  # VRN_ENG001_Thing_v*.py\nx.write_back()\n", encoding="utf-8")
        b = classify(d, w)
        chk("㉓ 程式改了(豁免列的呼叫名不見了)→ 回未審,要重審", "VDF_ENG900_Fake→functional modules/VRN" in b["open"], str(b["open"]))
    s = standalone_check()
    chk("㉔ 0c 本站輸出仍帶「真依賴兄弟家族」字樣(v0102 ⑩ 契約)且狀態合法", "真依賴兄弟家族" in s["detail"] and s["state"] in PRIOR.STATE_ORDER,
        f"{s['state']} · {s['detail'][:90]}")
    ok = rc == 0 and all(results)
    print(f"  [計] v0103 薄尾 {sum(results)}/{len(results)} · v0102 本體 {'PASS' if rc == 0 else 'FAIL'} · 合計 {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    return PRIOR.main(a)


if __name__ == "__main__":
    raise SystemExit(main())
