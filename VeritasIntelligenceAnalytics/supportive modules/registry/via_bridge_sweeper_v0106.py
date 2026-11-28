#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""via_bridge_sweeper v0106 — v0105 薄尾(v0103 … v0105 一字不動):各系統 functional modules/<系統>/intake/ 一律算收容件(不注橋)

緣由(2026-11-28,交接閘 VCGC 紅列 C-bridge-sweeper-v0105):v0104 ③ 真樹「加速 1197/1206 · 缺 9」。9 支全在
functional modules/VAP/intake/(操作員 2026-11-13 收進來的 VAP 收件:VAP_Core_SSOT_Bootstrap_v1 · VeritasAutoPlot_v4.2_extras,9df6a710d「frozen」)。
同結構的 functional modules/VRN/intake/ 26 支早就算 EXEMPT_INTAKE,VAP 那一夾卻算活檔 → 同一種夾兩種判法;
照活檔算,清掃器 --apply 會把橋注進別的系統的收件(#728 在凍結原件上注橋 → 轉紅、#742 還原的老坑)。
本版:路徑形如 functional modules/<系統>/intake/… → EXEMPT_INTAKE(收容件 · 不注橋 · 照計數);其餘照 v0104(凍結 · 四類收容夾 · 活檔)。
  掛在定義那一層(v0103 的模組層 classify,audit / apply 都讀它)。
  操作員 2026-11-28「前版鏈比照裁定甲」:本版自測驗本版與直接前版 v0105(它的 ① ② ③);v0105 ④ 那支往下跑 v0104 鏈的子行程不再算進本版。
不連網 · 自測不寫任何檔 · 不碰 TA-Lib。
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

VERSION = "v0106"
STEM = "via_bridge_sweeper"
HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
_SYS_INTAKE = re.compile(r"^functional modules/[^/]+/intake/")


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
V0104 = PRIOR.PRIOR
V0103 = V0104.P                                   # 模組層 classify / audit / apply 住在這一層
_CLASSIFY_V0104 = V0103.classify


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def classify(rp: str) -> str:
    r = str(rp).replace("\\", "/")
    c = _CLASSIFY_V0104(rp)
    if c == "ACTIVE" and _SYS_INTAKE.match(r):
        return "EXEMPT_INTAKE"
    return c


V0103.classify = classify
V0104.classify = classify


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""), flush=True)

    print(f"=== {STEM} {VERSION} 薄尾自測(裁定甲:本版 + 直接前版 v0105)===", flush=True)
    src = Path(__file__).read_text(encoding="utf-8")
    tail, ruler = PRIOR._ruler()
    psrc = PRIOR_PATH.read_text(encoding="utf-8")
    chk("① 本版與前版 v0105 都有標準加速器橋塊(正尺 %s)" % tail.stem,
        ruler.ACCEL_START in src and ruler.ACCEL_END in src and ruler.ACCEL_START in psrc and ruler.ACCEL_END in psrc)
    rel4 = PRIOR.PRIOR_PATH.relative_to(VIA).as_posix()
    want = PRIOR._receipt_sha(rel4)
    have = hashlib.sha256(PRIOR.PRIOR_PATH.read_bytes()).hexdigest()
    chk("② 前版 v0105 的 ②:v0104 一字不動(SHA = 交接收據 C-bridge-sweeper-v0104 記的)", bool(want) and have == want, have[:12])
    rows = {r["file"]: r["state"] for r in ruler.scan(HERE.relative_to(VIA).as_posix(), "accel")}
    me = Path(__file__).resolve().relative_to(VIA).as_posix()
    p5 = PRIOR_PATH.relative_to(VIA).as_posix()
    chk("③ 正尺掃描:本版 = 已掛(HAS)· 前版 v0105 = 版史(不算缺)", rows.get(me) == "HAS" and rows.get(p5) == "EXCLUDED", (rows.get(me), rows.get(p5)))
    cases = {"functional modules/VAP/intake/VAP_Core_SSOT_Bootstrap_v1/check_vap_core.py": "EXEMPT_INTAKE",
             "functional modules/VRN/intake/x/RunAndVerify.py": "EXEMPT_INTAKE",
             "functional modules/VAP/engine/VAP_ENG005_TemplateRunner_v0101.py": "ACTIVE",
             "functional modules/VDF/engine/VDF_ENG054_TWDailyBackfill_v0110.py": "ACTIVE",
             "functional modules/VAP/VAP_intake_reader_v0100.py": "ACTIVE",
             "docs/handoff/ai/VIA_LakeConsole_v0101.py": "ACTIVE"}
    got = {k: classify(k) for k in cases}
    chk("④ functional modules/<系統>/intake/ → 收容;同系統其他夾 · 檔名含 intake 的活檔照算 ACTIVE(負控)", got == cases,
        {k.split("/")[-1]: v for k, v in got.items() if v != cases[k]})
    chk("④ b 前版 v0104 的豁免規則照舊(凍結件 · 四類收容夾不變)", all(classify(x) == "EXEMPT_FROZEN" for x in list(V0104.FROZEN)[:5]))
    a = V0103.audit()
    chk("⑤ 真樹活樹:加速缺 0 · 網路缺 0(豁免另列計數)", not a["accel_miss"] and not a["net_miss"],
        "加速 %d/%d · 網路 %d/%d · 豁免 %s · 缺 %s" % (a["accel_have"], a["active"], a["net_have"], a["net_need"], a["exempt"], a["accel_miss"][:3]))
    chk("⑥ 加速器橋執行時載到 · 不碰 TA-Lib", VIA_ACCEL is not None and not re.search(r"^\s*(import|from)\s+talib", src, re.M))
    print("  [INFO] v0105 ④(子行程往下跑 v0104 鏈)不再算進本版(裁定甲);要看仍可各自 --selftest", flush=True)
    n = sum(ok)
    print("[%s] %s %s selftest · 本版 %d/%d" % ("PASS" if n == len(ok) else "FAIL", STEM, VERSION, n, len(ok)), flush=True)
    return 0 if n == len(ok) else 1


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    return PRIOR.main()


if __name__ == "__main__":
    sys.exit(main())
