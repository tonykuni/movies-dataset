#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL233_ToolActivate v0109 — 薄尾(v0108 以前一字不動):系統庫 syscat 掛進工具鎖冊(第十家)

操作員 2026-11-26:附件「DuckDB 管系統文件 · 引擎版本 · 檔案資產 · 系統庫呢」+「token-saving +」。
系統庫是 VCGC 資料庫管理器的動詞(CGC_MDL228_VIADBManager v0105 起 `syscat`);本版只把它登成省 Token 工具的一家,
讓 `tools` 清單看得到、啟用照同一把尺:
  syscat = CGC_MDL228_VIADBManager(supportive modules/registry;必備 API build · query · syscat · guard · main · selftest)
檢查照前版原樣(夾 · 四位版號 · AST · 零 TA-Lib · 加速器橋 · 匯入層不開子行程 · 必備 API · 公開名稱不少於現役 · 參數只增不減 ·
冊上已登錄 · 席位恰一列);引擎版本冊席位列 VIA-TOOL-0264(syscat)與本版同批登錄(role=engine,照 REQ187 / REQ188 前例取號)。
只有 VCGC 能啟用;零網路;不碰 TA-Lib;不讀寫同意閘。
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
NEW_FAMILIES_V0109 = {
    "syscat": ("CGC_MDL228_VIADBManager", BASE.HERE, ("build", "query", "syscat", "guard", "main", "selftest"), ()),
}
BASE.FAMILIES.update(NEW_FAMILIES_V0109)
FAMILIES = BASE.FAMILIES
TEN = {"accelerator", "network", "layout", "nlp", "token", "frame", "praddle", "pdfplumber", "ocr", "syscat"}


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

    print(f"=== {ENGINE} · 薄尾自測(系統庫 syscat 掛進工具鎖冊)===")
    chk("㊿ 直接前版 v0108 自測過(甲 裁定:只驗自己與直接前版)", rc == 0, f"rc {rc}")
    chk("51 十家同一把尺:" + " · ".join(sorted(TEN)), set(FAMILIES) >= TEN, ", ".join(sorted(FAMILIES)))
    stem, folder, api, _ = NEW_FAMILIES_V0109["syscat"]
    tails = sorted(folder.glob(stem + "_v*.py"), key=_vnum_v0109)
    first = [p for p in tails if _vnum_v0109(p) >= 105]
    if not first:
        chk("52 syscat 第一支(CGC_MDL228_VIADBManager_v0105 以上)不在 → 照實失敗(不冒充)", False)
    else:
        res = BASE.checks("syscat", first[-1].name)
        bad = [c["check"] + ":" + c["detail"] for c in res if not c["ok"]]
        chk(f"52 syscat 尾版過全部啟用檢查({first[-1].name} · {len(res)} 檢;含冊上已登錄 · 席位恰一列)", not bad, "; ".join(bad)[:240])
    old = [p for p in tails if _vnum_v0109(p) == 104]
    if old:
        res = BASE.checks("syscat", old[0].name)
        chk("53 沒有系統庫的前版(v0104,缺 build · query · syscat · guard)擋下", not all(c["ok"] for c in res))
    wrong = BASE.checks("syscat", "CGC_MDL158_VIAPanoramaAuditRepair_v0121.py")
    chk("54 家別不對的檔擋下(token 工具不能當 syscat 啟用)", not all(c["ok"] for c in wrong))
    ok = all(results)
    print(f"[{'PASS' if ok else 'FAIL'}] {ENGINE} selftest · {sum(results)}/{len(results)}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
