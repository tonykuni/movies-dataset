#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL233_ToolActivate v0103 — 六件工具同一把尺:+Polars 表格層(記憶體不足轉 temp)經 VCGC 啟用、鎖版號

操作員 2026-09-29:「go on add polars to all necessary engines 記憶體不足可用temp替代用」。
SUP_MDL755 VIAPolarsFrame 是 11 支必要引擎(撈大表 4 · 全歷史重算 7)都要載的共用件;它們的 FRAME 橋先問鎖冊 frame,
沒有才取尾版 —— 所以它和加速器、網路、LAYOUT、NLP、省 Token 一樣,要經 VCGC 啟用才算數(R20c:誰往夾裡放一支更大的版號,
不該就被 11 支引擎直接載進去)。v0103 把它加成第六家 frame,檢查照 v0100 原樣(檔在該在的夾 · 四位版號 · AST · 零 TA-Lib ·
加速器橋 · 匯入層不開子行程、不載二進位 · 必備 API · 公開名稱不少於現役 · 參數只增不減 · 冊上已登錄 VIA-TOOL-0195);
`via-vcgc tools activate frame <SUP_MDL755_…_vNNNN.py> --apply` 才寫鎖冊。
必備 API:polars · budget · spill_dir · sweep · duck_guard · install_duckdb_guard · frame · coverage · main · selftest。
其餘照 v0102。只收 VCGC 呼叫。零網路。
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

import hashlib
import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL233_ToolActivate"


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", path.stem)
    return int(m.group(1)) if m else -1


PRIOR = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR)
_PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _PRIOR
_spec.loader.exec_module(_PRIOR)
ENGINE = Path(__file__).stem
NEW_FAMILIES = {
    "frame": ("SUP_MDL755_VIAPolarsFrame", HERE.parent,
              ("polars", "budget", "spill_dir", "sweep", "duck_guard", "install_duckdb_guard", "frame", "coverage",
               "main", "selftest"), ()),
}
_PRIOR.FAMILIES.update(NEW_FAMILIES)          # 同一本 dict:v0100 的 checks / plan / apply / status / main 都讀它
FAMILIES = _PRIOR.FAMILIES


def __getattr__(name: str):
    return getattr(_PRIOR, name)


def main(argv=None) -> int:
    return _PRIOR.main(argv)


def selftest() -> int:
    for k in NEW_FAMILIES:                         # v0102 以前的自測量的是它們自己那幾家
        FAMILIES.pop(k, None)
    try:
        rc = _PRIOR.selftest()
    finally:
        FAMILIES.update(NEW_FAMILIES)
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + note) if note else ''}")

    chk("⑱ 六家同一把尺:accelerator · network · layout · nlp · token · frame",
        set(FAMILIES) >= {"accelerator", "network", "layout", "nlp", "token", "frame"}, ", ".join(sorted(FAMILIES)))
    fn = _PRIOR._registered("frame") or ""
    res = _PRIOR.checks("frame", fn) if fn else []
    bad = [c["check"] + ":" + c["detail"] for c in res if not c["ok"]]
    chk(f"⑲ frame 冊上那一支過 v0100 的全部檢查({fn or '冊上沒有 frame engine 列'})", fn and res and not bad,
        "; ".join(bad)[:160] or f"{len(res)} 檢")
    wrong = _PRIOR.checks("frame", "CGC_MDL158_VIAPanoramaAuditRepair_v0116.py")
    wrong2 = _PRIOR.checks("token", fn) if fn else [{"ok": False}]
    chk("⑳ 家別不對的檔擋下(全景檔不能當 frame 啟用;表格層不能當 token 啟用)",
        not all(c["ok"] for c in wrong) and not all(c["ok"] for c in wrong2))
    lock = _PRIOR._json(_PRIOR.lock_path()).get("frame") or {}
    pin = _PRIOR.pinned("frame")
    raw = pin.read_bytes() if pin else b""
    shas = {hashlib.sha256(raw).hexdigest(), hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()} if pin else set()
    chk("㉑ 已經 VCGC 啟用:鎖冊 frame 指到冊上那一支、檔在、位元吻合(CRLF 工作複本照 CGC_MDL225 v0102 容忍)",
        pin is not None and pin.name == fn and lock.get("sha256") in shas and "VCGC" in str(lock.get("activated_by", "")),
        f"鎖 {lock.get('version', '-')} · {pin.name if pin else '未啟用:via-vcgc tools activate frame ' + (fn or '<檔>') + ' --apply'}")
    ok = rc == 0 and all(results)
    print(f"  {ENGINE} selftest +{sum(results)}/{len(results)} {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
