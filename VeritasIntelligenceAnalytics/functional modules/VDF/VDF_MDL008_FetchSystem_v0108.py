#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_MDL008_FetchSystem v0108 — 薄尾:擷取冊按尾版 glob 取(VDF_FetchSystem_SSOT_v*.json;本輪 v0107)· 子行程從本版起

R78(操作員 2026-10-14 在地測試 FG_20261012T113922Z):冊 v0107 把 e077 → v0106(退役冊生效)、e232 → v0102 + timeout_s 14400。
v0107 以前的 MDL008 把冊名釘死(BOOK_V0106),MDL012 卻按尾版 glob 讀同一家冊 → 兩邊會各讀一本、子行程(_child)照舊冊的檔跑。
v0108 起 MDL008 也按尾版 glob 取冊;fill / run / MDL012 launch_child 起的子行程都從本檔起,讀同一本尾版冊。
其餘(live curl_cffi 改道 · 列上限 timeout_s · nodata 標記 · 同意閘只讀)全沿用 v0107。不碰 TA-Lib。
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


import importlib.util
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_MDL008_FetchSystem"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"


def _vnum_v0108(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0108(p) < _vnum_v0108(__file__)), key=_vnum_v0108)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
V0105, V0101, BASE = PRIOR.V0105, PRIOR.V0101, PRIOR.BASE


def __getattr__(name):
    return getattr(PRIOR, name)


_RUN_V0107 = PRIOR.run_v0107
_LOAD_V0107 = PRIOR.load_book_v0107
_LOAD_V0106 = PRIOR._LOAD_V0106
BOOK_GLOB_V0108 = "VDF_FetchSystem_SSOT_v*.json"


def book_path_v0108() -> Path:
    """擷取冊 = 本夾 VDF_FetchSystem_SSOT_v*.json 的尾版(出新冊不必再出 MDL008)。"""
    return max(HERE.glob(BOOK_GLOB_V0108), key=_vnum_v0108)


BOOK_V0107 = book_path_v0108()


def load_book_v0108(path: Path | None = None) -> dict:
    return _LOAD_V0106(path or book_path_v0108())


def run_v0108(*args, **kwargs):
    """同 v0107 run(列上限 timeout_s · live curl_cffi 改道);子行程改從本版起(子行程讀尾版冊),呼叫完還原。"""
    keep = PRIOR.__dict__.get("__file__")
    PRIOR.__dict__["__file__"] = str(Path(__file__).resolve())
    try:
        return _RUN_V0107(*args, **kwargs)
    finally:
        PRIOR.__dict__["__file__"] = keep


def _install_v0108() -> None:
    V0101.load_book_v0101, V0101.BOOK_V0101, BASE.load_book = load_book_v0108, BOOK_V0107, load_book_v0108
    V0105.PRIOR.load_book_v0104 = V0105.load_book_v0105 = PRIOR.PRIOR.load_book_v0106 = PRIOR.load_book_v0107 = load_book_v0108
    V0105.PRIOR.run_v0104 = V0101.run_v0101 = V0105.PRIOR.V0102.run_v0102 = BASE.run = run_v0108
    V0105.run_v0105 = PRIOR.PRIOR.run_v0106 = PRIOR.run_v0107 = run_v0108


def _restore_v0107() -> None:
    PRIOR.run_v0107 = _RUN_V0107
    PRIOR.load_book_v0107 = _LOAD_V0107
    PRIOR._install_v0107()


_install_v0108()


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    return PRIOR.main(args)


_PROBE_V0108 = r'''
import importlib.util, sys
sp = importlib.util.spec_from_file_location("m108", sys.argv[1]); m = importlib.util.module_from_spec(sp); sys.modules["m108"] = m; sp.loader.exec_module(m)
bk = m.BASE.load_book(); E = {r["id"]: r for r in bk["engines"]}
print("PROBE", bk.get("version"), E["e077"]["file"], E["e232"]["file"], E["e232"].get("timeout_s"), m.V0101.BOOK_V0101.name)
'''


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    _restore_v0107()
    try:
        rc0 = PRIOR.selftest()
    finally:
        _install_v0108()
    print(f"=== {TAG} · 薄尾自測(擷取冊按尾版 glob · 子行程從本版起)===")
    chk("① v0107 自測過(live curl_cffi 改道 · 冊 v0106 · 列上限)", rc0 == 0, f"rc {rc0}")
    bk = load_book_v0108()
    E = {r["id"]: r for r in bk["engines"]}
    prev = _LOAD_V0106(PRIOR.BOOK_V0106)
    P = {r["id"]: r for r in prev["engines"]}
    chk("② 冊按尾版 glob = v0107(BOOK_V0107 · version 欄 · prior 指 v0106)", BOOK_V0107.name == "VDF_FetchSystem_SSOT_v0107.json" and bk.get("version") == "v0107"
        and bk.get("prior") == "VDF_FetchSystem_SSOT_v0106.json", BOOK_V0107.name)
    others = [i for i in P if i not in ("e077", "e232") and P[i] != E.get(i)]
    chk("③ 冊 v0107:e077 → v0106(退役冊)· e232 → v0102 + timeout_s 14400 · 檔都在;其他 34 支與 v0106 相同;e054 仍指 v0109 回補工人",
        E["e077"]["file"] == "engine/VDF_ENG077_ActiveETFUniverse_v0106.py" and E["e232"]["file"] == "engine/VDF_ENG232_TWIndexOfficial_v0102.py"
        and E["e232"].get("timeout_s") == 14400 and all((HERE / E[i]["file"]).is_file() for i in ("e077", "e232")) and not others
        and len(bk["engines"]) == len(prev["engines"]) and E["e054"]["file"].endswith("_v0109.py"), others[:3])
    chk("④ 換裝:BASE.run / BASE.load_book / V0101.load_book_v0101 / PRIOR.run_v0107 / PRIOR.load_book_v0107 全指本版",
        BASE.run is run_v0108 and BASE.load_book is load_book_v0108 and V0101.load_book_v0101 is load_book_v0108
        and PRIOR.run_v0107 is run_v0108 and PRIOR.load_book_v0107 is load_book_v0108 and V0101.BOOK_V0101 == BOOK_V0107)
    seen = {}
    keep_run = PRIOR.__dict__["_RUN_V0106"]
    PRIOR.__dict__["_RUN_V0106"] = lambda rows, *a, **k: seen.update(
        f107=PRIOR.__dict__.get("__file__"), f106=PRIOR.PRIOR.__dict__.get("__file__"), t=k.get("timeout", a[3] if len(a) > 3 else None)) or []
    try:
        run_v0108([E["e232"]], "live", HERE, logs=None, timeout=1800)
        t_232, f107, f106 = seen.get("t"), seen.get("f107"), seen.get("f106")
        run_v0108([E["009"]], "live", HERE, logs=None, timeout=1800)
        t_def = seen.get("t")
    finally:
        PRIOR.__dict__["_RUN_V0106"] = keep_run
    me = str(Path(__file__).resolve())
    chk("⑤ 子行程從本版起:呼叫中 v0107 / v0106 的 __file__ 都指本檔,呼叫完還原", f107 == me and f106 == me
        and PRIOR.__dict__.get("__file__") != me and PRIOR.PRIOR.__dict__.get("__file__") != me, Path(f107 or "—").name)
    chk("⑥ 列上限經本版照 v0107:e232 timeout_s 14400 蓋過 1800;沒帶 timeout_s 的列照 1800", t_232 == 14400 and t_def == 1800, (t_232, t_def))
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    pr = subprocess.run([sys.executable, "-c", _PROBE_V0108, me], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600, env=env)
    line = next((x for x in pr.stdout.splitlines() if x.startswith("PROBE ")), "")
    chk("⑦ 新行程(= _child 的起法)載本檔:BASE.load_book 讀到 v0107(e077 v0106 · e232 v0102 · 14400)",
        line == f"PROBE v0107 engine/VDF_ENG077_ActiveETFUniverse_v0106.py engine/VDF_ENG232_TWIndexOfficial_v0102.py 14400 VDF_FetchSystem_SSOT_v0107.json",
        line or pr.stderr.strip()[-200:])
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 加速器橋 · 網路橋在;不碰 TA-Lib;不寫同意閘", "[VIA:ACCEL-BRIDGE" in text and "def _via_net" in text
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M) and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", text))
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · v0107 {'PASS' if rc0 == 0 else 'FAIL'} · 合計 {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
