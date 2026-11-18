#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL149_Integrate v0101 — v0100 薄尾(v0100 一字不動):NLP Hub 與 ENG085 不再釘死舊版號,改照 glob 取家族尾版(新舊版整合)。

實錄(2026-11-13 VCGC 全景 read · PINVER 2):v0100 寫死
  HUB    = SUP_MDL744_NLPApplicationHub_v0101.py(尾版已 v0103:v1.9.0 詞庫退路 · TextProcessor 正掛 · 證據型摘要)
  ENG085 = VRN_ENG085_MarkdownRestore_v0104.py(尾版已 v0106)
  → 這扇門一直拿舊版,新版修好的東西進不來(L50 尾版律;同型已由 CGC_MDL216 v0101 出口改成 glob 取尾版)。
本版:兩條路徑改成「同夾同家族版號最大」;v0100 的 nlp_target / selftest / run_folder / main 全部照跑(它們用模組全域名讀路徑 → 換成尾版)。
  舊版檔一支不刪、不搬(仍被前版鏈引用)。唯讀 · 零網路 · 不寫庫 · 不用 TA-Lib · 不寫同意閘。
用法同 v0100:python CGC_MDL149_Integrate_v0101.py [--selftest]
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
# [VIA:NET-BRIDGE] 留名:本版不出網

import contextlib
import importlib.util
import io
import re
import sys
from pathlib import Path

VERSION = "v0101"
HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL149_Integrate"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


def tail(folder: Path, stem: str) -> Path | None:
    """同夾 stem_vNNNN.py 版號最大那支;沒有 → None。"""
    hits = [p for p in Path(folder).glob(stem + "_v*.py") if _vnum(p) >= 0]
    return max(hits, key=_vnum) if hits else None


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_v0101", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
PINNED = {"HUB": PRIOR.HUB, "ENG085": PRIOR.ENG085}          # v0100 寫死的兩條(留作對照)
HUB = tail(PRIOR.HUB.parent, "SUP_MDL744_NLPApplicationHub") or PRIOR.HUB
ENG085 = tail(PRIOR.ENG085.parent, "VRN_ENG085_MarkdownRestore") or PRIOR.ENG085
PRIOR.HUB, PRIOR.ENG085 = HUB, ENG085                         # v0100 的函式用模組全域名 → 換成尾版


def __getattr__(name):
    return getattr(PRIOR, name)


def routes() -> dict:
    return {k: {"pinned": PINNED[k].name, "now": v.name, "changed": PINNED[k] != v} for k, v in (("HUB", HUB), ("ENG085", ENG085))}


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""), flush=True)

    print("=== %s %s · 薄尾自測(Hub / ENG085 取尾版;v0100 自測照跑)===" % (_STEM, VERSION), flush=True)
    r = routes()
    hub_tail = tail(PRIOR.HUB.parent, "SUP_MDL744_NLPApplicationHub")
    eng_tail = tail(PRIOR.ENG085.parent, "VRN_ENG085_MarkdownRestore")
    chk("① Hub = 家族尾版(不寫死)", HUB == hub_tail and PRIOR.HUB == HUB, "%s → %s" % (r["HUB"]["pinned"], r["HUB"]["now"]))
    chk("② ENG085 = 家族尾版(不寫死)", ENG085 == eng_tail and PRIOR.ENG085 == ENG085, "%s → %s" % (r["ENG085"]["pinned"], r["ENG085"]["now"]))
    chk("③ 舊版檔都還在(新舊並存,不刪不搬)", PINNED["HUB"].is_file() and PINNED["ENG085"].is_file())
    t = PRIOR.nlp_target()
    chk("④ NLP 目標照讀(SEEN · 不回寫)· 由尾版 Hub 回報收容件版號", t.get("state") == "SEEN" and t.get("writeback") is False, "%s %s" % (t.get("name"), t.get("version")))
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = PRIOR.selftest()
    print("  ── 前版 v0100 自測(換上尾版 Hub / ENG085)──", flush=True)
    print(buf.getvalue(), end="")
    chk("⑤ v0100 自測(版面門 · 欄序 · ENG085 修文 · 表格分數 · NLP 目標)換上尾版後全過", rc == 0, "rc %s" % rc)
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def tail", 1)[1]
    chk("⑥ 本版不寫死任何版號路徑 · 不出網 · 不用 TA-Lib", not re.search(r'["\'][A-Za-z0-9_]+_v\d{4}\.py["\']', body)
        and not re.search(r"^\s*(?:import|from)\s+(talib|requests|urllib)", src, re.M))
    n = sum(ok)
    print("  [計] %s %s 薄尾 %d/%d · 合計 %s" % (_STEM, VERSION, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    return 0 if n == len(ok) else 1


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    return PRIOR.main()


if __name__ == "__main__":
    sys.exit(main())
