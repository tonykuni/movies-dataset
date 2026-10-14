#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0153 — 薄尾:+metrics-resolve 直送 VRN_ENG073 尾版(掉球 Z298;PR #523 審查:測試要經 VRN 自己的 manager,AGENTS 5)。
  VRN_ENG073 v0140 的研報指標多候選收斂(`metrics-resolve [--db 庫] [--apply] | --selftest`)由本口轉送,
  交接案 metrics_resolve 經 VRN_SystemManager 跑(不再由 VCGC 直呼引擎)。
  本版只加這一個動詞,放在自測攔截之前(與 v0152 provenance 同一理由:`metrics-resolve --selftest` 不能被吃成管理器自測鏈);
  其餘動詞(含 provenance、--selftest)照前版鏈。VRN 自己的 manager(L120)。
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
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: F401
except ImportError:
    VIA_ACCEL = None
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
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

import importlib.util
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0153"
METRICS_STEM = "VRN_ENG073_ReportStructuredDB"


def _vnum_v0153(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0153(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0153(p) < _vnum_v0153(__file__)), key=_vnum_v0153)
PRIOR = _load_v0153(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def metrics_engine_path() -> Path:
    """VRN_ENG073 研報結構化入庫引擎尾版(版號最大)。"""
    return max(HERE.glob(METRICS_STEM + "_v*.py"), key=_vnum_v0153)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if args[:1] == ["metrics-resolve"]:
        # ENG073 的 main 讀 sys.argv:轉送期間換成引擎自己的引數,完了還原
        engine = _load_v0153(metrics_engine_path(), "_vrn_eng073_for_" + Path(__file__).stem)
        saved = sys.argv
        sys.argv = [str(metrics_engine_path())] + args
        try:
            return engine.main()
        finally:
            sys.argv = saved
    if args[:1] == ["--selftest"]:
        return selftest()
    return PRIOR.main(args)          # provenance 等其餘動詞照前版鏈(v0152 把 provenance 放在它自己的攔截之前)


def selftest() -> int:
    from unittest.mock import Mock, patch
    p = f = 0

    def chk(name, cond, note=""):
        nonlocal p, f
        if cond:
            p += 1
        else:
            f += 1
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""))

    seen = {}
    fake = Mock()
    fake.main.side_effect = lambda: seen.setdefault("argv", list(sys.argv[1:])) and 5
    before = list(sys.argv)
    with patch.dict(os.environ, {"VIA_FROM_VCGC": "YES"}), patch.dict(globals(), {"_load_v0153": Mock(return_value=fake)}):
        rc = main(["metrics-resolve", "--selftest"])
    chk("① metrics-resolve --selftest 直送 ENG073 尾版(引數照傳 · 回傳碼照引擎 · sys.argv 還原)· 不被管理器自測攔下",
        rc == 5 and seen.get("argv") == ["metrics-resolve", "--selftest"] and sys.argv == before, str(seen.get("argv")))
    with patch.object(PRIOR, "main", Mock(return_value=7)) as pm:
        rc2 = main(["provenance", "--selftest"])
        rc3 = main(["status"])
    chk("② 其他動詞照前版鏈(provenance / status → 前版 main)",
        rc2 == 7 and rc3 == 7 and [c.args[0] for c in pm.call_args_list] == [["provenance", "--selftest"], ["status"]])
    chk("③ ENG073 尾版找得到", metrics_engine_path().exists(), metrics_engine_path().name)
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.main(["--selftest"])
    chk("④ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    chk("⑤ 帶加速器橋 · 網路工具橋", "[VIA:ACCEL-BRIDGE:v0100]" in Path(__file__).read_text(encoding="utf-8")
        and "[VIA:NET-BRIDGE:v0100]" in Path(__file__).read_text(encoding="utf-8"))
    print("[計] VRN_SystemManager_v0153 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
