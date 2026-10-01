#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG082_FinStatements v0107 — 薄尾:自測的假同意代碼跟上網路工具 v0116 收緊後的第二道閘(引擎行為一字不動)

v0106→v0107(R46 2026-10-02 · 操作員令「單獨測試vdf所有引擎」「實際測試修正至成功」):VDF 74 支逐支經 VCGC 自測,本支紅:
「v0105 二十二檢在本境中斷:CatalogException: tw_financial does not exist」。量到的:v0105 自測 ⑤ 用假車道端到端,
先把 VIA_SCRAPE_CONSENT 設成假代碼 "x" 代表「操作員開過閘」;可是網路工具 SUP_MDL740 v0116 把第二道閘收緊成只認
掃描閘冊上的代碼(`_GATE.OPEN`)—— "x" 不再算開,run() 照律 FAIL-CLOSED、一列都沒寫,下一句查表就崩。
引擎沒錯(閘收緊是對的),錯在自測的假代碼過期。
v0107 的自測:只在跑前版自測的那段時間,把本體 gate_open() 包一層 —— 真閘說關、且自測自己設了 NET=YES 與一個非空的
假代碼時,視同自測已開閘(假車道零網路;⑭ 起用假網路物件的閘照舊由它自己判);跑完立刻拿掉。正式 run 永遠走真閘。
零網路 · 不代設同意閘(只在自測行程內、對假車道)· 不用 TA-Lib。
"""
from __future__ import annotations

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(VDF 全導入令;惰性載入=import 時零網路、零行為變更) =====
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT;網路只認 AegisNexus);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

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
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_ENG082_FinStatements"


def _vnum(p: Path) -> int:
    m = re.search(r"_v(\d+)$", p.stem)
    return int(m.group(1)) if m else -1


_PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location("finstmt_prior_for_" + Path(__file__).stem, _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def _owner(attr: str):
    m, seen = PRIOR, set()
    while m is not None and id(m) not in seen:
        seen.add(id(m))
        if callable(vars(m).get(attr)) and "MOPS_TABLE" in vars(m) and "def gate_open" in Path(m.__file__).read_text(encoding="utf-8"):
            return m
        m = vars(m).get("_PRIOR") or vars(m).get("PRIOR") if isinstance(vars(m).get("_PRIOR") or vars(m).get("PRIOR"), type(sys)) else None
    return None


BODY = _owner("gate_open")


def _selftest_gate(real):
    def gate_open():
        ok, why = real()
        env = os.environ
        if not ok and env.get("VIA_NET_CONSENT") == "YES" and env.get("VIA_SCRAPE_CONSENT"):
            return True, why + " · 自測假代碼(假車道零網路)視同已開"
        return ok, why
    return gate_open


def main() -> int:
    if "--selftest" in sys.argv[1:2] or sys.argv[1:2] == ["selftest"]:
        return selftest()
    return PRIOR.main()


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print("=== VDF_ENG082 三大報表 v0107 · 薄尾自測(假代碼跟上收緊後的第二道閘;零網路)===")
    chk("① 找得到本體(持有 gate_open / MOPS_TABLE 的那一版)", BODY is not None, getattr(BODY, "__file__", "?").rsplit("/", 1)[-1])
    real = BODY.gate_open
    keep = {k: os.environ.get(k) for k in ("VIA_NET_CONSENT", "VIA_SCRAPE_CONSENT")}
    os.environ.pop("VIA_NET_CONSENT", None)
    os.environ.pop("VIA_SCRAPE_CONSENT", None)
    try:
        closed = real()[0]
    finally:
        for k, v in keep.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    chk("② 正式路徑的真閘在本行程是關的(沒人代設同意閘)", closed is False)
    BODY.gate_open = _selftest_gate(real)
    try:
        rc = PRIOR.selftest()
    finally:
        BODY.gate_open = real
    chk("③ 前版自測(v0106 三檢 + v0105 二十二檢)在假車道全過", rc == 0, f"rc {rc}")
    chk("④ 跑完拿掉自測閘,正式 run 走真閘", BODY.gate_open is real)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑤ 本支帶加速器橋 · 網路橋;不含 TA-Lib 匯入;本支沒有任何地方設 VIA_NET_CONSENT=YES 給正式路徑",
        re.search(r"^# ===== \[VIA:ACCEL-BRIDGE:v\d+\]", src, re.M) and re.search(r"^# ===== \[VIA:NET-BRIDGE:v\d+\]", src, re.M)
        and not re.search(r"^\s*(?:import|from)\s+" + "ta" + r"lib\b", src, re.M)
        and ("os.environ[" + '"VIA_NET' + '_CONSENT"]') not in src)
    good = all(ok)
    print(f"  [計] VDF_ENG082 v0107 薄尾 {sum(ok)}/{len(ok)} · 合計 {'PASS' if good else 'FAIL'}")
    return 0 if good else 1


if __name__ == "__main__":
    sys.exit(main())
