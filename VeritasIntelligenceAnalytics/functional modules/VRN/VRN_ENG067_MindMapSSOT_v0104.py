#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_ENG067_MindMapSSOT v0104 — 自測 ① 拆兩半:程式依賴缺 = 壞掉(FAIL);台股清單庫不在 = 缺料(SKIP)

v0103→v0104(R24 實測收尾,容器 2026-09-28:VRN 鏈 L2 把本支判 RED):v0103 的 ① 把四件綁成一條——
  ENG066 NLP 樞紐 · ENG063 詞庫 · 產業冊 · **vdf_tw_market.duckdb**。容器裡前三件都在(個股冊照樣載到 1978 家),
  只因為那本庫不在就整條 FAIL → 鏈判 RED。庫不在是缺料不是壞掉(L16 / L57;同鏈 VRN_ENG068 v0106 起的三態約定):
  ①a 程式與冊依賴(ENG066 · ENG063 · 產業冊)缺一 = FAIL;
  ①b 台股清單庫不在 = SKIP 並指路(庫在照舊算 OK)。
  其餘八檢照 v0103 原樣跑(攝入 · 簡繁 · 英中 · 分類 · 漸進 · K 枝 · mind map · 紀律)。
rc:有 FAIL=1;無 FAIL 有 SKIP=2(NODATA);全過=0(與 ENG068 同約定,鏈跑器據此記缺料不記紅)。
用法照 v0103:python3 VRN_ENG067_MindMapSSOT_v0104.py --selftest | --status | --map | ingest --text/--file
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

import contextlib
import importlib.util
import io
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "VRN_ENG067_MindMapSSOT"


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", path.stem)
    return int(m.group(1)) if m else -1


PRIOR = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(STEM + "_prior_for_" + Path(__file__).stem, PRIOR)
_PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _PRIOR
_spec.loader.exec_module(_PRIOR)
ENGINE = Path(__file__).stem
FIRST = "① 依賴鏈在位"


def split_first(text: str, deps_ok: bool, db_ok: bool) -> tuple:
    """Rewrite v0103's combined ① line into ①a (code deps) and ①b (list store); return (lines, fails, skips)."""
    out, fails, skips = [], 0, 0
    for line in text.splitlines():
        if FIRST in line and line.lstrip().startswith("["):
            out.append(f"  [{'OK' if deps_ok else 'FAIL'}] ①a 程式與冊依賴在位(ENG066 / ENG063 / 產業冊)")
            if db_ok:
                out.append("  [OK] ①b 台股清單庫在位(vdf_tw_market.duckdb)")
            else:
                out.append("  [SKIP] ①b 台股清單庫不在=缺料(誠實),非本引擎缺陷;補法:via-vdffetch / via-price 建庫後複判")
                skips += 1
            fails += 0 if deps_ok else 1
            continue
        if line.lstrip().startswith("[計]"):
            continue
        if line.lstrip().startswith("[FAIL]"):
            fails += 1
        out.append(line)
    return out, fails, skips


def selftest() -> int:
    deps_ok = _PRIOR._hub() is not None and _PRIOR._lex063() is not None and _PRIOR.IND_MAP.exists()
    db_ok = _PRIOR.DB_TW.exists()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        _PRIOR.selftest()
    lines, fails, skips = split_first(buf.getvalue(), deps_ok, db_ok)
    for line in lines:
        print(line)
    sample = "  [FAIL] ① 依賴鏈在位(ENG066/ENG063/產業冊/清單庫) \n  [OK] ② x\n  [計] 九檢 OK 8 · FAIL 1"
    a, fa, sa = split_first(sample, True, False)
    b, fb, sb = split_first(sample, False, True)
    own = (fa == 0 and sa == 1 and any("[SKIP] ①b" in x for x in a)) and (fb == 1 and sb == 0)
    print(f"  [{'OK' if own else 'FAIL'}] ⑩ ① 拆兩半:庫不在 = SKIP、程式依賴缺 = FAIL(不放寬)")
    fails += 0 if own else 1
    total = sum(1 for x in lines if re.match(r"\s*\[(OK|FAIL|SKIP)\]", x)) + 1
    print(f"  [計] {total} 檢 OK {total - fails - skips} · FAIL {fails} · SKIP {skips}(誠實三態;缺料不是壞掉)")
    return 1 if fails else (2 if skips else 0)


def __getattr__(name: str):
    return getattr(_PRIOR, name)


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        print("=== 三語關鍵字 SSOT×Mind map(VRN_ENG067 v0104)· 自測(零網路)===")
        return selftest()
    return _PRIOR.main()


if __name__ == "__main__":
    sys.exit(main())
