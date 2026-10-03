#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_SystemManager v0128 — 薄尾:獨立運作,VDF System Manager 是 VDF 的總控

操作員 2026-10-03:「改為獨立運作由 VDF SYSTEM MANAGER 總控」「產生兩個自動生成清單驗證過引擎為第一步」。
  ① 獨立啟動:python "functional modules/VDF/VDF_SystemManager_v0128.py" <動詞> 不經 VCGC 也能跑(VCGC 呼叫照收)。
     本版是 VDF 的總控入口:對下發總控標記 VIA_FROM_VDFSM=YES(MDL008 v0101 起認它);前版鏈的入口檢查只在本次呼叫內看到已核准,結束還原。
  ② fetch 一律交最新尾版的 VDF_MDL008_FetchSystem(第一步 = 兩支清單引擎 MDL009 全台股 · MDL010 主動式 ETF;冊上排序)。
  ③ 抬頭印「總控 = 本版 · 入口來源(獨立 / VCGC)」。
其餘動詞全照 v0128。同意閘(VIA_NET_CONSENT / VIA_SCRAPE_CONSENT)是操作員的手,本版不讀不寫。不碰 TA-Lib。
"""
from __future__ import annotations# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
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

# ===== [VIA:LIB-BRIDGE:v0100] 三庫正典橋(批597;缺席大聲拋,不 graceful) =====
import sys as _lb_sys
from pathlib import Path as _lb_Path
_lb_p = _lb_Path(__file__).resolve()
while _lb_p.parent != _lb_p:
    if (_lb_p / "supportive modules").is_dir():
        _lb_sys.path.insert(0, str(_lb_p / "supportive modules"))
        break
    _lb_p = _lb_p.parent
import VIA_LibCanon as _LIB          # 正典缺席=大聲拋,不假裝有(LL151)
# ===== [VIA:LIB-BRIDGE:END] =====

import contextlib
import importlib.util
import io
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_SystemManager"
SUB = "VDF"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
VERBS_v0128 = ('status', 'catalog', 'links', 'records', 'engines', 'bridges', 'tools', 'read', 'sync', 'page', 'launch', 'record', 'matrix', 'measure', 'universe', 'engine', 'params', 'prep', 'start', 'test', 'register', 'policy', 'update', 'ps', 'fetch')


def _vnum_v0128(path) -> int:            # 版本專屬名:元件冊以函式登記,共用名會把前版的紀錄搶走
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0128(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0128(p) < _vnum_v0128(__file__)), key=_vnum_v0128)
PRIOR = _load_v0128(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def verb_problem_v0128(args) -> str:
    """回空字串 = 放行;首詞不是旗標又不在動詞表 → 拒跑理由(中文)。子動詞交各版自己判。"""
    if not args or args[0].startswith("-") or args[0] in VERBS_v0128:
        return ""
    return f"未知動詞 '{args[0]}'(已知:{' · '.join(VERBS_v0128)};旗標 --json · --standalone · --selftest 等照前版)"


def _with_argv_v0128(args, fn):
    """前版多數 main() 讀 sys.argv:暫換成本次參數再交棒,交完還原。"""
    keep = sys.argv
    sys.argv = [keep[0] if keep else str(Path(__file__)), *args]
    try:
        return fn()
    finally:
        sys.argv = keep


FETCH_SYSTEM_V0127 = HERE / "VDF_MDL008_FetchSystem_v0100.py"


def fetch_v0128(rest: list) -> int:
    """fetch 動詞 → MDL008 獨立擷取系統(子系統大引擎);缺席誠實 ABSENT rc3。"""
    tails = sorted(HERE.glob("VDF_MDL008_FetchSystem_v*.py"), key=_vnum_v0128)
    if not tails:
        print(f"[ABSENT] {TAG}:VDF_MDL008_FetchSystem_v*.py 不在這棵樹")
        return 3
    mod = _load_v0128(tails[-1], "vdf_fetch_system_for_v0128")
    return mod.main(rest or ["list"])


ENTRY_VDFSM_V0128 = "VIA_FROM_VDFSM"


def _entry_v0128() -> str:
    return "VCGC" if os.environ.get("VIA_FROM_VCGC") == "YES" else "獨立"


def main(argv=None) -> int:
    """VDF 總控:獨立啟動或經 VCGC 都收;對下發總控標記,前版入口檢查只在本次呼叫內看到已核准。"""
    args = list(sys.argv[1:] if argv is None else argv)
    why = verb_problem_v0128(args)
    if why:
        print(f"[拒跑] {TAG}:{why}")
        return 2
    had_vc, keep_vc = "VIA_FROM_VCGC" in os.environ, os.environ.get("VIA_FROM_VCGC")
    had_sm, keep_sm = ENTRY_VDFSM_V0128 in os.environ, os.environ.get(ENTRY_VDFSM_V0128)
    src = _entry_v0128()
    os.environ[ENTRY_VDFSM_V0128] = "YES"
    os.environ["VIA_FROM_VCGC"] = "YES"
    try:
        if args[:1] == ["fetch"]:
            return fetch_v0128(args[1:])
        if (not args or args[0] == "status") and "--json" not in args:
            print(f"[{_STEM}] 總控 {TAG} · 入口 {src}(下行抬頭的版號是狀態讀器本體的版,不是尾版)")
        return _with_argv_v0128(args, lambda: PRIOR.main(args))
    finally:
        for k, had, keep in (("VIA_FROM_VCGC", had_vc, keep_vc), (ENTRY_VDFSM_V0128, had_sm, keep_sm)):
            if had:
                os.environ[k] = keep
            else:
                os.environ.pop(k, None)


def selftest() -> int:
    prior_rc = PRIOR.selftest()
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {TAG} · 薄尾自測(獨立運作 · VDF System Manager 總控)===")
    saved = {k: os.environ.pop(k, None) for k in ("VIA_FROM_VCGC", ENTRY_VDFSM_V0128)}
    try:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc_l = main(["fetch", "list"])
            rc_p = main(["fetch", "plan"])
            rc_u = main(["foo"])
        out = buf.getvalue()
        left = [k for k in ("VIA_FROM_VCGC", ENTRY_VDFSM_V0128) if k in os.environ]
        chk("① 不經 VCGC 獨立啟動:fetch list / plan rc0(總控標記下發到 MDL008)· 未知動詞仍 rc2", rc_l == 0 and rc_p == 0 and rc_u == 2, (rc_l, rc_p, rc_u))
        pl = out[out.find("計畫"):]
        chk("② 擷取計畫第一步 = 兩支清單引擎(MDL009 全台股 · MDL010 主動式 ETF),MDL001–007 在後",
            "MDL009" in pl and "MDL010" in pl and pl.index("MDL009") < pl.index("MDL001") and pl.index("MDL010") < pl.index("MDL001"))
        chk("③ 呼叫結束環境還原(不留 VIA_FROM_VCGC / VIA_FROM_VDFSM)", not left, left)
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    text = Path(__file__).read_text(encoding="utf-8")
    chk("④ 加速器橋 · 網路工具橋 · 正典橋在;不碰 TA-Lib;不寫同意閘", "[VIA:ACCEL-BRIDGE" in text and "[VIA:NET-BRIDGE" in text and "[VIA:LIB-BRIDGE" in text
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M) and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", text))
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · 前版 {'PASS' if prior_rc == 0 else 'FAIL'} · 合計 {'PASS' if all(ok) and prior_rc == 0 else 'FAIL'}")
    return 0 if all(ok) and prior_rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if sys.argv[1:] == ["--selftest"] else main())
