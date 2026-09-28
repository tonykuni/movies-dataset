#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
VDF_ENG082_FinStatements v0106 — 三大報表擷取引擎:網路本體改問鎖冊(R20c 舊檔名全景探針抓到的遺漏)

v0105→v0106(R20c 2026-09-28,操作員「舊檔案名稱全景式檢視探針找到指令中的部分替換物遺漏」):
  探針(AST 掃治理尾版的字串常數,只算真的拿去開檔/組路徑的)抓到本引擎兩處寫死無版號舊本體
  `supportive modules/network/VeritasAegisNexus.py`:aegis_session()(給 yfinance 注入的 session)與
  _lane_pull()(注入車道子行程載入的本體)。VDF 其他路線早就經 SUP_MDL740 取鎖冊指定的網路工具
  (R20c 起 = VCGC 啟用的 VeritasAegisNexus_v1652),只有這兩處還在用 1.2.0 舊本體。
  v0106 兩處都改問 CGC_MDL233 pinned('network')(與啟動層 · SUP_MDL740 同一把尺);鎖冊讀不到才退回舊路徑。
  其餘一字不動(MOPS 車道、計畫、台帳、自測二十二檢全照 v0105);本檔不在匯入時連網。
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
STEM = "VDF_ENG082_FinStatements"


def _vnum(path: Path) -> int:
    match = re.search(r"_v(\d+)$", path.stem)
    return int(match.group(1)) if match else -1


def _load_as(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


PRIOR = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_PRIOR = _load_as(PRIOR, "eng082_prior_for_" + Path(__file__).stem)
VIA = _PRIOR.VIA
LEGACY_BODY = VIA / "supportive modules" / "network" / "VeritasAegisNexus.py"


def aegis_path() -> Path:
    """The network tool the lock book names (CGC_MDL233 pinned). Lock unreadable: the v0105 body path."""
    reg = VIA / "supportive modules" / "registry"
    hits = [p for p in reg.glob("CGC_MDL233_ToolActivate_v*.py") if _vnum(p) >= 0]
    if hits:
        try:
            pinned = _load_as(max(hits, key=_vnum), "tool_activate_for_eng082").pinned("network")
            if pinned:
                return pinned
        except Exception as exc:
            LOCK_NOTE.append(f"lock unreadable: {type(exc).__name__}")
    return LEGACY_BODY


LOCK_NOTE: list = []


def aegis_session():
    """AegisNexus ResilientHTTPClient 的 requests session(給 yfinance 注入);缺=None + why。"""
    p = aegis_path()
    if not p.is_file():
        return None, f"{p.name} 缺"
    try:
        m = _load_as(p, "via_aegis_for_eng082")
        cli = m.ResilientHTTPClient()
        s = cli._get_session()
        return s, f"AegisNexus {p.name} session {type(s).__name__}"
    except Exception as exc:
        return None, f"AegisNexus session 取不到 {type(exc).__name__}:{str(exc)[:50]}"


def _lane_pull(ticker: str, inject: bool, timeout_s: float) -> tuple:
    """同 v0105:一條車道 = 一個子行程;注入車道載入的網路本體改成鎖冊指定的那一支。"""
    import json as _json
    import subprocess as _sp
    f = _PRIOR.fetcher()
    fp = getattr(f, "__file__", "") or ""
    if not fp:
        return [], "no-fetcher"
    try:
        r = _sp.run([sys.executable, "-c", _PRIOR._LANE_CODE, fp, ticker, "1" if inject else "0", str(aegis_path())],
                    capture_output=True, text=True, timeout=timeout_s, stdin=_sp.DEVNULL,
                    env=dict(os.environ, PYTHONUTF8="1"))
    except _sp.TimeoutExpired:
        return [], "timeout"
    except Exception as exc:
        return [], f"spawn-failed:{type(exc).__name__}"
    if r.returncode != 0:
        return [], f"rc{r.returncode}"
    line = (r.stdout or "").strip().splitlines()
    try:
        d = _json.loads(line[-1]) if line else {}
    except ValueError:
        return [], "bad-json"
    return list(d.get("rows") or []), str(d.get("tag") or "")


_PRIOR.aegis_session = aegis_session
_PRIOR._lane_pull = _lane_pull

for _name, _value in vars(_PRIOR).items():
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = _value


def __getattr__(name: str):
    return getattr(_PRIOR, name)


def selftest() -> int:
    p = aegis_path()
    checks = [
        ("網路本體 = 鎖冊指定(帶版號),不是無版號舊本體", p != LEGACY_BODY and bool(re.search(r"_v\d{4}\.py$", p.name))),
        ("v0105 的呼叫點都換到本版", _PRIOR.aegis_session is aegis_session and _PRIOR._lane_pull is _lane_pull),
        ("本檔碼裡(自測之前)沒有寫死任何網路工具版號檔名",
         re.search(r"VeritasAegisNexus_v\d{4}\.py", Path(__file__).read_text(encoding="utf-8").split("def selftest")[0]) is None),
    ]
    for name, ok in checks:
        print(f"  [{'OK' if ok else 'FAIL'}] {name}")
    print(f"  [註] 網路本體 {p.name}")
    try:
        rc = _PRIOR.selftest()
    except Exception as exc:                                  # v0105 自測在本境中斷:照實報,不吞
        print(f"  [FAIL] v0105 二十二檢在本境中斷:{type(exc).__name__}: {str(exc)[:120]}")
        rc = 1
    return 0 if rc == 0 and all(ok for _n, ok in checks) else 1


def main() -> int:
    if "--selftest" in sys.argv[1:2] or sys.argv[1:2] == ["selftest"]:
        return selftest()
    return _PRIOR.main()


if __name__ == "__main__":
    sys.exit(main())
