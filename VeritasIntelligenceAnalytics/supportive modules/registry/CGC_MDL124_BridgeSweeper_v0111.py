#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL124_BridgeSweeper v0111 — 薄尾:PY 掃描也豁免 `_sha<12 位十六進位>.py` 存證副本(與交接閘同一條規則)

操作員 2026-10-10 問「PS / PY 覆蓋率 100%?有沒有導入網路工具?」→ 經 VCGC 掃:VDF 網路橋 144/145,缺的那一支是
`VDF_AutoCodeRegistryEngine_shad7fd781ac69f.py` —— 存證副本(CGC_MDL140 v0106 `SHA_COPY`:「不是待測程式」,凍結來源不改)。
v0109 的 PS 排除早就有「凍結副本(_sha)」,PY 的 `_excluded()` 沒有,所以照 `--apply` 會把橋寫進凍結檔。
本版只在 PY `_excluded()` 前面加這一條(具名理由,可查),其餘一字照 v0110 / v0109;補丁打在 `scan` 真正查名的那一份全域
(`scan.__globals__`,即本體 v0109),不靠猜鏈上哪一版是本體。只收 12 位十六進位的 `_sha` 副本,`_sha256_util.py` 這類一般檔名不受影響。
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
STEM = "CGC_MDL124_BridgeSweeper"


def _vnum_v0111(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum_v0111(p) < _vnum_v0111(__file__)), key=_vnum_v0111)
_spec = importlib.util.spec_from_file_location(STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
for _n, _v in vars(PRIOR).items():
    if not _n.startswith("__") and _n not in globals():
        globals()[_n] = _v

# 與 CGC_MDL140 v0106 SHA_COPY 同一條(存證副本 = 操作員 2026-10-10 令還原的 FILE_REMOVED 同類)
SHA_COPY = re.compile(r"_sha[0-9a-f]{12}\.py$")
SHA_COPY_WHY = "存證副本(_sha<12 碼>;凍結來源不改,與交接閘 SHA_COPY 同一規則)"
_BODY = PRIOR.scan.__globals__            # scan / inject 真正查 _excluded 的那一份全域(本體)
_EXCLUDED_BEFORE_V0111 = _BODY["_excluded"]


def _excluded(p: Path) -> str:
    if SHA_COPY.search(Path(p).name):
        return SHA_COPY_WHY
    return _EXCLUDED_BEFORE_V0111(p)


_BODY["_excluded"] = _excluded


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    return PRIOR.main()


def selftest() -> int:
    rc0 = PRIOR.selftest()
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    print("=== CGC_MDL124_BridgeSweeper v0111 · 薄尾自測(PY 掃描豁免 _sha 存證副本)===")
    chk("① v0110 自測過(連 v0109 本體鏈)", rc0 == 0, f"rc {rc0}")
    via = _BODY["VIA"]
    fake = via / "functional modules" / "VDF" / "VDF_X_shad7fd781ac69f.py"
    plain = via / "functional modules" / "VDF" / "VDF_sha256_util.py"
    chk("② `_sha` + 12 位十六進位 = 存證副本 → 排除(具名理由);`_sha256_util.py` 這類一般檔名不算",
        _excluded(fake) == SHA_COPY_WHY and not SHA_COPY.search(plain.name), _excluded(fake))
    chk("③ 補丁打在 scan 真正查名的全域(本體),不是只換本版的名字", _BODY["_excluded"] is _excluded and PRIOR.scan.__globals__["_excluded"] is _excluded)
    rows = PRIOR.scan("functional modules/VDF", "net")
    sha_rows = [r for r in rows if SHA_COPY.search(Path(r["file"]).name)]
    missing = [r["file"] for r in rows if r["state"] == "MISSING"]
    chk("④ 真樹 VDF 網路橋:_sha 存證副本全部 EXCLUDED、帶本條理由;缺 0(現役引擎照掃)",
        sha_rows and all(r["state"] == "EXCLUDED" and r.get("why") == SHA_COPY_WHY for r in sha_rows) and not missing,
        f"缺 {missing[:3]} · 副本 {len(sha_rows)}")
    live = [r for r in rows if r["state"] == "HAS"]
    chk("⑤ 現役檔照舊算(不是靠排除把分母掃空)", len(live) >= 100, f"HAS {len(live)}")
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 加速器橋在(__future__ 之後);不碰 TA-Lib",
        "[VIA:ACCEL-BRIDGE" in text and text.index("from __future__") < text.index("[VIA:ACCEL-BRIDGE")
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M))
    print(f"  [計] CGC_MDL124_BridgeSweeper v0111 本版 {sum(ok)}/{len(ok)} · v0110 {'PASS' if rc0 == 0 else 'FAIL'} · 合計 {'PASS' if all(ok) and rc0 == 0 else 'FAIL'}")
    return 0 if all(ok) and rc0 == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
