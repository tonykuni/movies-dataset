#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""CGC_MDL170_VDFChainRunner v0106 — 薄尾:自測只驗本版與直接前版 v0105(裁定甲);真樹依賴判準 = 未審 0

實錄(2026-11-28,交接閘 VCGC 紅列 vdf_chain_runner):v0103 ⑳ / v0104 ㉖ 要求真樹「ENG063 · ENG094 兩處命中都已審」(已審 ≥ 2)。
量到的:VDF_ENG094_ActiveETFActivity 從 v0101 起已不再呼叫 VRN_ENG090(v0101 … v0104 都沒有 VRN 字樣,v0104 不是 v0100 的薄尾),
真樹只剩 ENG063 一處,而且已審、未審 0。功能沒有壞,是自測釘著當時的世界(兩處依賴);又因每一版都重跑前版鏈 → v0105 也紅。
操作員 2026-11-19 裁定「甲」、2026-11-28「前版鏈比照裁定甲」:尾版自測只驗本版與直接前版。
本版只改自測(v0102 … v0105 一字不動;run · 進度行 · 判燈 · 報告 · --resume 照前版):
  ① 直接前版 v0105 自己的三檢在本行程重跑:站執行格換成 v0105 的 run_one · 逐站進度行(假站,不真跑)· 橋在。
  ② 真樹依賴:未審 0 才算過;已審的照列;豁免冊有、真樹已不再命中的列 → INFO「豁免冊多一列」(不刪冊、不當紅)。
  ③ 負控:暫存夾造一支沒登豁免的跨系統讀取 → 未審 1(紅)。
  前版鏈(v0104 以前)的自測沒有刪,要看仍可各自 --selftest;它們的結果不再算進本版。零網路 · 不用 TA-Lib · 只收 VCGC 呼叫照前版。
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
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL170_VDFChainRunner"


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
ENGINE_TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
_V0104 = PRIOR.PRIOR                       # classify(沿薄尾鏈取文)住在這一層
_V0103 = _V0104.PRIOR                      # VDF_ENG · _waivers 住在這一層


def __getattr__(name):
    return getattr(PRIOR, name)


def dependency_check(eng_dir: Path | None = None, waivers: list | None = None) -> dict:
    """真樹依賴:open 未審(紅)· reviewed 已審 · stale_waivers 豁免冊有、真樹已不命中的家族(INFO)。"""
    eng = Path(eng_dir or _V0103.VDF_ENG)
    ws = list(_V0103._waivers() if waivers is None else waivers)
    r = _V0104.classify(eng, ws)
    hit = {x.split("→", 1)[0] for x in r["reviewed"]}
    r["stale_waivers"] = sorted({w.get("family") for w in ws if w.get("family") and w.get("family") not in hit})
    return r


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    return PRIOR.main()


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {ENGINE_TAG} · 薄尾自測(裁定甲:本版 + 直接前版 v0105)===")
    body = PRIOR.BODY
    chk("① 前版 v0105:本體的站執行格是 v0105 的 run_one;站數從本體 CHAIN 讀",
        body is not None and body.run_one is PRIOR.run_one and len(body.CHAIN) >= 1, len(body.CHAIN) if body else "-")
    seen, lines = [], []
    keep_run, keep_say = PRIOR._RUN_ONE0, PRIOR.say
    PRIOR._RUN_ONE0 = lambda *a: seen.append(a[0]) or {"id": a[0], "state": "GREEN"}
    PRIOR.say = lambda line: lines.append(line)
    PRIOR._STATE["done"] = 0
    try:
        r1 = PRIOR.run_one("1", "參數", "x", [], 1, "", "", "2023-07-01")
        PRIOR.run_one("2", "邏輯", "x", [], 1, "", "", "2023-07-01")
    finally:
        PRIOR._RUN_ONE0, PRIOR.say = keep_run, keep_say
        PRIOR._STATE["done"] = 0
    n = len(body.CHAIN)
    chk("② 前版 v0105:每站一行開始、一行完成(k/N · 燈 · 秒);結果原樣回傳(假站,不真跑)",
        len(lines) == 4 and lines[0] == f"[進度] VDF 1/{n} 開始 1 參數" and lines[1].startswith(f"[進度] VDF 1/{n} 完成 1 參數 · GREEN · ")
        and lines[3].startswith(f"[進度] VDF 2/{n} 完成 2 邏輯") and r1 == {"id": "1", "state": "GREEN"} and seen == ["1", "2"], lines[:2])
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        (d / "VDF_ENG950_Chain_v0100.py").write_text("ME = 'VDF_ENG950_Chain_v*.py'\np = VIA / 'functional modules/VRN'\nx.read_it()\n",
                                                     encoding="utf-8")
        neg = dependency_check(d, [])
        pos = dependency_check(d, [{"family": "VDF_ENG950_Chain", "target": "functional modules/VRN", "module_glob": "VDF_ENG950_Chain_v*.py",
                                    "calls": ["read_it"], "direction": "read-only", "why": "test"},
                                   {"family": "VDF_ENG951_Gone", "target": "functional modules/VRN", "why": "test"}])
    chk("③ 負控:沒登豁免的跨系統讀取 → 未審 1;登了 → 已審;豁免冊有、樹上不命中 → stale(INFO)",
        neg["open"] == ["VDF_ENG950_Chain→functional modules/VRN"] and not pos["open"]
        and pos["reviewed"] == ["VDF_ENG950_Chain→functional modules/VRN"] and pos["stale_waivers"] == ["VDF_ENG951_Gone"], f"{neg['open']} · {pos}")
    real = dependency_check()
    chk("④ 真樹:未審依賴 0(已審照列)", not real["open"], f"已審 {real['reviewed']} · 未審 {real['open']}")
    print(f"  [INFO] 豁免冊多一列(真樹已不再命中,冊照只增不刪):{real['stale_waivers']}")
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑤ 加速器橋在且執行時載到(本支不觸網,無網路橋)· 不碰 TA-Lib", "VIA:ACCEL-BRIDGE" in src and VIA_ACCEL is not None
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M))
    pub = [k for k in vars(PRIOR) if not k.startswith("_") and callable(vars(PRIOR)[k])]
    chk("⑥ 前版 v0105 的公開名稱從本版都拿得到(TAILAPI)", all(hasattr(sys.modules[__name__], k) for k in pub), len(pub))
    print("  [INFO] 前版鏈(v0104 以前)的自測不再算進本版(裁定甲);要看仍可各自 --selftest")
    print(f"  [計] {ENGINE_TAG} 本版 {sum(ok)}/{len(ok)} · 合計 {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
