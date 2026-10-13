#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_SystemManager v0159 — 薄尾:自測把前版鏈(v0157 → v0128)的判決行照印(v0158 把它吞進緩衝,交接閘 9 案看不到標記)

R78 收尾實錄(2026-10-13 20:12–20:18 UTC):handoff test vdf_master_control · vdf_activate · vdf_universe · vdf_universe_r50 · vdf_engine ·
vdf_engine_params · vdf_unknown_verb · vdf_fetch_verb 的 argv 都是尾版 `VDF_SystemManager --selftest`,標記是 v0128–v0129 那幾行 [計];
v0158 的自測把 v0157 → v0128 整條前版自測的輸出導進緩衝只看 rc → 標記不見 → EVIDENCE_INVALID 9 件(rc 0 · marker False)。
v0159:自測先照印 v0157 的自測(整條鏈的判決行都在),再重做 v0158 的檢查(同一份本體 · 同一組函式,經 PRIOR 取),最後印本版 [計]。
run / all / ask 燈號行為與 v0158 一字不差(main 直通前版;本體 v0155 不動)。
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)。本檔零網路。"""
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
# ===== [VIA:NET-BRIDGE:END] =====


import importlib.util
import re
import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_SystemManager"
TAG = "v" + Path(__file__).stem.rsplit("_v", 1)[-1]


def _vnum_v0159(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0159(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0159(p) < _vnum_v0159(__file__)), key=_vnum_v0159)
PRIOR = _load_v0159(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args[:2]:
        return selftest()
    return PRIOR.main(args)


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)
    V158 = PRIOR
    V157 = PRIOR.PRIOR
    print(f"=== VDF_SystemManager {TAG} · 薄尾自測(前版鏈判決行照印 + v0158 檢查重做)===")
    print("  ── 前版 v0157 自測(整條鏈 v0157 → v0128 照印)──")
    rc157 = V157.selftest() if isinstance(V157, types.ModuleType) else 1
    chk("① 前版鏈 v0157 → v0128 自測 PASS(判決行已照印,交接閘看得到)", rc157 == 0, f"rc={rc157}")
    own, orig = V158._OWN_CMD, V158._ORIG_RUN_CMD
    now = getattr(own, "RUN_CMD", None)
    chk("② v0158 本體鏈:RUN_CMD 本體 v0155 · 本體的 RUN_CMD 是 v0158 替身且只包一層(v0157 自測後仍在)",
        own is not None and Path(own.__file__).stem.endswith("_v0155") and now is not None and now.__name__ == "run_cmd_v0158"
        and getattr(now, "_orig_v0158", None) is orig and getattr(orig, "_orig_v0158", None) is None and callable(orig))
    ask = ["pwsh", "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ". 'C:\\VIA\\Open-VIA-VDF-v0103.ps1'"]
    out = V158.ask_cmd_v0158(ask)
    chk("③ ask 那條 -Command 補 exit $LASTEXITCODE(路徑與其餘參數不動)", out[:-1] == ask[:-1] and out[-1] == ask[-1] + V158.EXIT_SUFFIX_V0158, out[-1])
    chk("④ 已帶 exit 的、不是點源形狀的、非 pwsh 的命令原樣回",
        V158.ask_cmd_v0158(out) == out and V158.ask_cmd_v0158(["pwsh", "-Command", "Get-Date"]) == ["pwsh", "-Command", "Get-Date"]
        and V158.ask_cmd_v0158(["python", "-c", ". 'x'"]) == ["python", "-c", ". 'x'"])
    seen = {}

    def fake_orig(cmd, timeout=None):
        seen["cmd"], seen["timeout"] = list(cmd), timeout
        return {"rc": 2, "secs": 0.1}
    keep = V158._ORIG_RUN_CMD
    V158._ORIG_RUN_CMD = fake_orig
    try:
        r = V158.run_cmd_v0158(ask, timeout=5)
    finally:
        V158._ORIG_RUN_CMD = keep
    chk("⑤ run_cmd:補完交給前版本體,rc 原樣回(2 → _lamp 黃)· timeout 照傳",
        r == {"rc": 2, "secs": 0.1} and seen["cmd"][-1].endswith(V158.EXIT_SUFFIX_V0158) and seen["timeout"] == 5
        and V157._lamp(2, yellow=(2,)) == "YELLOW" and V157._lamp(0, yellow=(2,)) == "GREEN")
    body = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 本檔:橋在(__future__ 之後)· 不碰 TA-Lib · 不代設同意閘 · 不載入 VCGC 程式 · 自測不吞前版輸出(不把輸出導進緩衝)",
        all(x in body for x in ("[VIA:ACCEL-BRIDGE:v0100]", "[VIA:NET-BRIDGE:v0100]")) and body.index("from __future__") < body.index("[VIA:ACCEL-BRIDGE:v0100]")
        and "import " + "talib" not in body and 'environ["VIA_NET_' + 'CONSENT"] = "' not in body and "CGC_MDL" + "1" not in body.replace("CGC_MDL" + "137", "")
        and "redirect_" + "stdout" not in body)
    n = 6
    print(f"  [計] VDF_SystemManager_{TAG} 自測 {n - len(fails)}/{n} · {'PASS' if not fails else 'FAIL ' + ', '.join(fails)}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
