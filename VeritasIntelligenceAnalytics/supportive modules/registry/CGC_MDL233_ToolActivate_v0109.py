#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL233_ToolActivate v0109 — 薄尾:GRAPHIFY · PLAYWRIGHT · DUCKDB 三家掛進工具鎖冊(席位候選)

操作員 2026-11-10:「先做 Graphify Playwright DuckDB 席位候選 自動完成以上全部」。鎖冊原有九家
(accelerator · network · layout · nlp · token · frame · praddle · pdfplumber · ocr);本版加三家,全部是 VCGC 自己的工具檔:
  graphify   = VIA_GraphifyLane(docs/handoff/ai;隔離境探測 · 收據 · 圖譜統計;Graphify 本體在隔離境,不進主境、不進鎖冊)
               必備 API probe_env · run · selftest · main
  playwright = VIA_PlaywrightProbe(docs/handoff/ai;VCGC 離線頁實測:錯誤 · 外連攔截 · 手機溢出;Playwright 套件由操作員裝)
               必備 API probe · run · selftest · main
  duckdb     = VIA_LakeMatrix(docs/handoff/ai;VCGC 自己的湖寫入 · 他系統只讀盤點 · DuckDB 管家;尾版 v0101 是轉接薄尾)
               必備 API run · selftest · main
檢查照前版原樣(夾 · 四位版號 · AST · 零 TA-Lib · 加速器橋 · 匯入層不開子行程 · 必備 API · 公開名稱不少於現役 · 參數只增不減 ·
冊上已登錄 · 席位恰一列 · 轉接鏈)。引擎版本冊同批登 role=candidate,**編號欄留白**(L125 ②:衝突解完、VCGC 偵測無誤才發號;
「冊上已登錄」只認列在不在,不要求號)。`via-vcgc tools activate graphify|playwright|duckdb <檔> --apply` 才寫鎖冊。
套件本身(graphifyy · playwright · duckdb)不進鎖冊、本行程不載。只有 VCGC 能啟用。零網路。其餘照 v0108。
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
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL233_ToolActivate"
ENGINE = Path(__file__).stem


def _vnum_v0109(path: Path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0109(p) < _vnum_v0109(Path(__file__))), key=_vnum_v0109)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR)
_PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _PRIOR
_spec.loader.exec_module(_PRIOR)
BASE = _PRIOR.BASE
AI_DIR = BASE.VIA / "docs" / "handoff" / "ai"
NEW_FAMILIES_V0109 = {
    "graphify": ("VIA_GraphifyLane", AI_DIR, ("probe_env", "run", "selftest", "main"), ()),
    "playwright": ("VIA_PlaywrightProbe", AI_DIR, ("probe", "run", "selftest", "main"), ()),
    "duckdb": ("VIA_LakeMatrix", AI_DIR, ("run", "selftest", "main"), ()),
}
BASE.FAMILIES.update(NEW_FAMILIES_V0109)
FAMILIES = BASE.FAMILIES
REGISTERED = "冊上已登錄(VCGC 工具號)"


def __getattr__(name: str):
    return getattr(_PRIOR, name)


def main(argv=None) -> int:
    return _PRIOR.main(argv)


def selftest() -> int:
    for k in NEW_FAMILIES_V0109:               # 前版自測量前版那九家
        FAMILIES.pop(k, None)
    try:
        rc = _PRIOR.selftest()
    finally:
        FAMILIES.update(NEW_FAMILIES_V0109)
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {ENGINE} · 薄尾自測(GRAPHIFY · PLAYWRIGHT · DUCKDB 掛進工具鎖冊)===")
    chk("㊶ 前版鏈自測過(九家)", rc == 0, f"rc {rc}")
    chk("㊷ 十二家同一把尺", set(FAMILIES) >= {"accelerator", "network", "layout", "nlp", "token", "frame", "praddle", "pdfplumber", "ocr",
                                              "graphify", "playwright", "duckdb"}, ", ".join(sorted(FAMILIES)))
    reg = BASE._json(HERE / "VIA_EngineVersion_Register_v0100.json")
    for fam, (stem, folder, _api, _) in NEW_FAMILIES_V0109.items():
        tails = sorted(folder.glob(stem + "_v*.py"), key=_vnum_v0109)
        if not tails:
            chk(f"㊸ {fam} 尾版不在 → 照實失敗(不冒充)", False, f"{stem}_v*.py 不在")
            continue
        res = BASE.checks(fam, tails[-1].name)
        bad = [c["check"] + ":" + c["detail"] for c in res if not c["ok"]]
        chk(f"㊸ {fam} 尾版過全部啟用檢查({tails[-1].name} · {len(res)} 檢;含冊上已登錄 · 席位恰一列)",
            not bad and any(c["check"] == REGISTERED for c in res), "; ".join(bad)[:240])
        row = next((r for r in reg.get("rows") or [] if r.get("file") == tails[-1].name), {})
        blank_ok = (row.get("role") == "candidate" and row.get("code", "") == "") or row.get("role") == "engine"
        chk(f"㊹ {fam} 候選列編號留白(L125 ②:不自行發號;已啟用則是席位列)", blank_ok, f"role {row.get('role')} · code {row.get('code')!r}")
    wrong = BASE.checks("playwright", "VIA_GraphifyLane_v0100.py")
    chk("㊺ 家別不對的檔擋下(Graphify 車道檔不能當 Playwright 啟用)", not all(c["ok"] for c in wrong))
    text = Path(__file__).read_text(encoding="utf-8")
    chk("㊻ 加速器橋在 · 不碰 TA-Lib · 本行程沒載 graphify / playwright / duckdb",
        "VIA:ACCEL-BRIDGE" in text and not re.search(r"^\s*(import|from)\s+talib", text, re.M)
        and not {"graphify", "playwright", "duckdb"} & {m.split(".")[0] for m in sys.modules})
    ok = rc == 0 and all(results)
    print(f"  {ENGINE} selftest +{sum(results)}/{len(results)} {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
