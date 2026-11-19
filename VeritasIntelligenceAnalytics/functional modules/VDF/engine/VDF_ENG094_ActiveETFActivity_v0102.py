#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VDF_ENG094_ActiveETFActivity v0102 — 薄尾:系統獨立 —— VCGC 的 ScrapeGate 尺檔不在或壞掉時,改用 VDF 自己的同一把尺。

2026-11-18 演練(整棵樹拿掉 CGC_*.py 後啟動 VDF):v0101 的 consent_open() 找不到尺就一律回「關」,
兩道同意都給了也不抓;尺檔若壞掉(語法錯)則直接丟例外。等於 VCGC 少一個檔,VDF 這支就停工。
本版只換 consent_open:VCGC 的尺在而且載得起來 → 用它(行為與 v0101 相同);不在或載不起來 → 用 VDF 自己的尺
(判法逐字相同:VIA_NET_CONSENT=YES 且 VIA_SCRAPE_CONSENT 是 YES 或責任字串才開;其餘一律關)。
v0101 一字不動;其餘公開名稱、main、指令列原樣轉交。
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
import os
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_ENG094_ActiveETFActivity"
VERSION = Path(__file__).stem.rsplit("_v", 1)[-1]
_TOKEN = "I_ACCEPT_RESPONSIBLE_" + "SCRAPING"
_NK, _SK = "VIA_NET_" + "CONSENT", "VIA_SCRAPE_" + "CONSENT"


def _vnum(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location("eng094_prior_for_v" + VERSION, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
_PRIOR_CONSENT = PRIOR.consent_open
REGISTRY = PRIOR.VDF.parent.parent / "supportive modules" / "registry"


def __getattr__(name: str):
    return getattr(PRIOR, name)


def vdf_gate_open(env=None) -> bool:
    """VDF 自己的同一把尺:兩道同意都在才開,其餘一律關(與 CGC_MDL224 v0100 判法逐字相同)。"""
    env = os.environ if env is None else env
    return env.get(_NK) == "YES" and (env.get(_SK) or "") in ("YES", _TOKEN)


def ruler(reg: Path | None = None):
    """回 (函式, 來源說明):VCGC 的尺在且載得起來用它;不在或壞掉用 VDF 自己的。"""
    folder = Path(reg) if reg is not None else REGISTRY
    hits = sorted(folder.glob("CGC_MDL224_ScrapeGate_v*.py"), key=_vnum) if folder.is_dir() else []
    if not hits:
        return vdf_gate_open, "VDF 自己的尺(VCGC 尺檔不在)"
    try:
        spec = importlib.util.spec_from_file_location("scrape_gate_for_eng094_v" + VERSION, hits[-1])
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if callable(getattr(mod, "gate_open", None)):
            return mod.gate_open, "VCGC 尺 " + hits[-1].name
    except Exception as exc:  # 尺檔壞了也不讓引擎倒
        return vdf_gate_open, "VDF 自己的尺(VCGC 尺載不起來:" + type(exc).__name__ + ")"
    return vdf_gate_open, "VDF 自己的尺(VCGC 尺檔沒有 gate_open)"


def consent_open(env=None, reg: Path | None = None) -> bool:
    env = os.environ if env is None else env
    return bool(ruler(reg)[0](env))


PRIOR.consent_open = consent_open        # 本體的 fetch 以模組全域叫 consent_open()


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    return PRIOR.main(argv)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""))

    print("=== %s v%s 薄尾自測(系統獨立:VCGC 的尺不在也能判同意;零網路)===" % (_STEM, VERSION))
    combos = [{}, {_NK: "YES"}, {_SK: "YES"}, {_NK: "YES", _SK: "OFF"}, {_NK: "YES", _SK: "YES"}, {_NK: "YES", _SK: _TOKEN}, {_NK: "NO", _SK: "YES"}, {_NK: "YES", _SK: "maybe"}]
    expect = [False, False, False, False, True, True, False, False]
    fn, src_now = ruler()
    chk("① VDF 自己的尺八種同意組合都照規格;這台現在用的尺也一樣", [vdf_gate_open(c) for c in combos] == expect and [fn(c) for c in combos] == expect, src_now)
    with tempfile.TemporaryDirectory(prefix="eng094_gate_") as td:
        t = Path(td)
        f_missing, s_missing = ruler(t / "nope")
        (t / "CGC_MDL224_ScrapeGate_v9999.py").write_text("def broken(:\n", encoding="utf-8")
        f_broken, s_broken = ruler(t)
        open_missing = consent_open({_NK: "YES", _SK: "YES"}, t / "nope")
        closed_broken = consent_open({_NK: "YES"}, t)
    chk("② VCGC 尺檔不在 → 用 VDF 自己的尺:兩道同意都在就開(前版是一律關)", f_missing is vdf_gate_open and open_missing is True and "不在" in s_missing, s_missing)
    chk("③ VCGC 尺檔壞掉(語法錯)→ 不丟例外,用 VDF 自己的尺;沒同意照樣關", f_broken is vdf_gate_open and closed_broken is False and "載不起來" in s_broken, s_broken)
    with tempfile.TemporaryDirectory(prefix="eng094_gate_neg_") as td:
        neg = None
        saved = PRIOR.VDF
        try:
            PRIOR.VDF = Path(td) / "functional modules" / "VDF"      # 前版從這裡往上找 registry:找不到
            neg = _PRIOR_CONSENT({_NK: "YES", _SK: "YES"})
        finally:
            PRIOR.VDF = saved
    chk("④ 負控:前版在尺檔不在時,兩道同意都給了也回關(本版要修的就是這個)", neg is False)
    chk("⑤ 裝進本體:本體 fetch 叫到的就是本版的 consent_open", PRIOR.consent_open is consent_open)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 加速器橋真的匯入 · 不含本機路徑 · 不寫同意值", "import VIA_SuperAccel_Module as VIA_ACCEL" in src and ("C:" + "\\Users") not in src and ("environ[" + "_NK") not in src)
    rc = PRIOR.selftest()
    chk("⑦ 前版自測照過(假網路擷取那一檢在沒有 VCGC 尺的機器上也過得了)", rc == 0, "rc %s" % rc)
    good = all(ok)
    print("[計] %s v%s 本版 %d/%d · %s" % (_STEM, VERSION, sum(ok), len(ok), "PASS" if good else "FAIL"))
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())
