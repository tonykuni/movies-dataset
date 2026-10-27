#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VDF_MDL013_ActivateVDF v0105 — 薄尾:PYTHONPATH 去重時空段照留(PR #532 Codex P2)

v0104 的 dedupe_bootstrap 先把空段丟掉再拼回去;Python 把 PYTHONPATH 的空段當「目前目錄」,
所以 `bootstrapA::bootstrapB` 這種(正好是要去重的情況)會連帶拿掉目前目錄,子流程靠目前目錄 import 的就壞。
本版:只拿掉第一份之後的 `supportive modules/bootstrap`,空段與其他路徑原樣、原序保留;
v0104 的 flow_env 與 numexpr 探針都在呼叫時查自己模組的 dedupe_bootstrap → 換上本版即生效。其餘全照 v0104。
VDF 自己的模組:不匯入他系統程式;同意閘不讀不寫;不碰 TA-Lib。
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入;本檔的連網全經 MDL008 子行程改道。"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None

import importlib.util
import os
import re
import sys
import tempfile
import warnings
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_MDL013_ActivateVDF"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"


def _vnum_v0105(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0105(p) < _vnum_v0105(__file__)), key=_vnum_v0105)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
with warnings.catch_warnings():                    # 同 v0102:前版鏈只擋載入那一刻的編譯警告
    warnings.simplefilter("ignore", SyntaxWarning)
    warnings.simplefilter("ignore", DeprecationWarning)
    _spec.loader.exec_module(PRIOR)
V0100 = PRIOR.V0100


def __getattr__(name):
    return getattr(PRIOR, name)


def dedupe_bootstrap(pythonpath: str | None, sep: str = os.pathsep) -> tuple:
    """PYTHONPATH 只留第一份 `supportive modules/bootstrap` → (新值, 拿掉幾份);空段(= 目前目錄)與其他路徑原樣原序保留。"""
    if not pythonpath:
        return pythonpath, 0
    seen, out, dropped = False, [], 0
    for p in pythonpath.split(sep):
        if p and PRIOR._BOOT_RX.search(p):
            if seen:
                dropped += 1
                continue
            seen = True
        out.append(p)
    return (sep.join(out) if dropped else pythonpath), dropped


PRIOR.dedupe_bootstrap = dedupe_bootstrap          # v0104 flow_env / numexpr_probe 呼叫時查模組全域 → 換上本版

_ACTIVATE_V0104 = PRIOR.activate


def activate(opt, manager: Path | None = None, py: str | None = None, temp: Path | None = None) -> dict:
    """同 v0104 activate(標頭與總覽標本版;總覽 JSON 的 schema 不變)。"""
    keep = PRIOR.TAG                               # v0104.activate 把它自己的 TAG 往下傳 → 換成本版
    PRIOR.TAG = TAG
    try:
        return _ACTIVATE_V0104(opt, manager, py, temp)
    finally:
        PRIOR.TAG = keep


for _n in dir(PRIOR):
    if not _n.startswith("__") and _n not in globals():
        globals()[_n] = getattr(PRIOR, _n)


# ---------------------------------------------------------------- 自測
def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {TAG} · 薄尾自測(PYTHONPATH 去重空段照留;沙盒 · 零網路)===")
    a = os.path.join("A", "supportive modules", "bootstrap")
    b = os.path.join("B", "supportive modules", "bootstrap")
    emp, de = dedupe_bootstrap(os.pathsep.join([a, "", b, "", "Z"]))
    lead, dl = dedupe_bootstrap(os.pathsep.join(["", a, "X", b, ""]))
    same, ds = dedupe_bootstrap(os.pathsep.join(["X", "", "X"]))
    with tempfile.TemporaryDirectory(prefix="activatevdf105_") as td:
        res = V0100.optimize_resources(want=3, stamp="20261018_150000", root=Path(td))
        env = V0100.flow_env(res, "engines", base_env={"PYTHONPATH": os.pathsep.join([a, "", b])})
    chk("㉓ 去重只拿第一份之後的 bootstrap:空段(= 目前目錄)、開頭 / 結尾空段、重複的一般路徑都原樣原序保留;"
        "子行程環境(flow_env 經 v0104)同樣保留空段",
        emp == os.pathsep.join([a, "", "", "Z"]) and de == 1
        and lead == os.pathsep.join(["", a, "X", ""]) and dl == 1
        and same == os.pathsep.join(["X", "", "X"]) and ds == 0
        and env["PYTHONPATH"] == os.pathsep.join([a, ""]) and env.get("VIA_BOOTSTRAP_DEDUPED") == "1",
        {"a::b::Z→": emp, "子行程": env["PYTHONPATH"]})
    src = Path(__file__).read_text(encoding="utf-8")
    imports = re.findall(r"^\s*(?:import|from)\s+([A-Za-z_][\w.]*)", src, re.M)
    chk("㉔ 加速器橋 · 網路橋在;不匯入他系統程式;不碰 TA-Lib;同意閘不寫",
        "VIA:ACCEL-BRIDGE" in src and "def _via_net" in src
        and not [x for x in imports if x.startswith(("CGC_", "VRN_", "VCGC"))]
        and not re.search(r"^\s*(import|from)\s+" + "talib", src, re.M)
        and not re.search(r"\[[\"']VIA_(NET|SCRAPE)_" + r"CONSENT[\"']\]\s*=(?!=)", src))
    n = sum(ok)
    print(f"  [計] {TAG} 本版 {n}/{len(ok)} · {'PASS' if n == len(ok) else 'FAIL'}")
    if n != len(ok):
        return 1
    rc1 = PRIOR.selftest()
    return rc1 if rc1 in (0, 1, 2, 3) else 1        # 前版紅照實回(同 v0102;PR #528 Codex P1)


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--selftest"]:
        return selftest()
    opt = V0100.parse(argv)
    if opt.verb != "run":
        return V0100.main(argv)
    card = activate(opt)
    return {"GREEN": 0, "YELLOW": 2, "INTERRUPTED": 130}.get(card["lamp"], 1)


if __name__ == "__main__":
    raise SystemExit(main())
