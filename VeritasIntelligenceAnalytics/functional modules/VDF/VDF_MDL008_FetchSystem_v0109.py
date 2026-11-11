#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_MDL008_FetchSystem v0109 — 薄尾:子行程也用本版起(冊 v0108 的 009 → MDL009 v0103 在子行程裡才生效)

桌機實錄(操作員貼回 2026-11-11 08:18 / 08:40,VIA_DesktopOneShot v0100):總控 fetch run MDL009 --apply → [OK] 102.5s / 60.0s,
清單 tw_stock_list_latest.parquet 仍沒有 shares_issued 欄(探針:股數 -1 = 欄不存在)。
根因(容器實測重現):擷取系統每支引擎在子行程裡跑,子行程用的檔由 run 換裝鏈決定 —— v0107 的 run 把子行程指向「v0107 自己」;
v0108 只在父行程換了載冊(009 → v0103),沒把子行程改指本版 → 子行程是 v0107、載 v0107 的冊 → 009 仍是 MDL009 v0102(沒有 T1 欄)。
  重現:父行程冊 009 = VDF_MDL009_TWStockList_v0103.py · 子行程檔 = VDF_MDL008_FetchSystem_v0107.py · 子行程冊 009 = v0102。
本版只改一件事:run 呼叫期間把 v0107 模組的 __file__ 指向本檔(同 v0102 / v0104–v0107 的前例:每層的 run 讀自己模組的 __file__,
外層改了就一路傳下去)→ 子行程 = 本版 → 匯入時裝上 v0108 載冊 → 009 = v0103 → 清單帶 shares_issued 等 T1 欄。
其餘(冊 · live 改道 · curl_cffi · 列上限 · 輸出路徑 · 參數)全照 v0108。不碰 TA-Lib;不讀寫同意閘。
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
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_MDL008_FetchSystem"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"


def _vnum_v0109(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0109(p) < _vnum_v0109(__file__)), key=_vnum_v0109)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
V0107 = PRIOR.PRIOR                                    # v0107:run_v0107 把子行程指向「它自己的 __file__」
V0105, V0101, BASE = PRIOR.V0105, PRIOR.V0101, PRIOR.BASE
_RUN_V0107 = V0107.run_v0107


def __getattr__(name):
    return getattr(PRIOR, name)


def run_v0109(*args, **kwargs):
    """同 v0107 run;呼叫期間 v0107 的 __file__ 指向本檔 → 子行程 = 本版(載冊 v0108 · 009 → MDL009 v0103)。結束還原。"""
    keep = V0107.__dict__.get("__file__")
    V0107.__dict__["__file__"] = str(Path(__file__).resolve())
    try:
        return _RUN_V0107(*args, **kwargs)
    finally:
        V0107.__dict__["__file__"] = keep


def _install_v0109() -> None:
    V0105.PRIOR.run_v0104 = V0101.run_v0101 = V0105.PRIOR.V0102.run_v0102 = BASE.run = run_v0109
    V0105.run_v0105 = V0107.PRIOR.run_v0106 = V0107.run_v0107 = run_v0109


def _restore_v0108() -> None:
    V0107.run_v0107 = _RUN_V0107                       # 先還原名稱:v0107 的換裝讀它自己模組的 run_v0107
    V0107._install_v0107()
    PRIOR._install_v0108()


_install_v0109()


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest(deep=False)
    if args == ["--selftest", "--deep"]:
        return selftest(deep=True)
    return PRIOR.main(args)


_CHILD_PROBE_V0109 = ("import importlib.util,sys;from pathlib import Path;p=Path(sys.argv[1]);"
                      "s=importlib.util.spec_from_file_location('mdl008_child_probe',p);c=importlib.util.module_from_spec(s);"
                      "sys.modules['mdl008_child_probe']=c;s.loader.exec_module(c);"
                      "print(next(r['file'] for r in c.BASE.load_book()['engines'] if r['id']=='009'))")


def _child_cmd_v0109() -> list:
    """實跑一次 run(009 列 · 假 subprocess,不起真子行程、不連網),回子行程指令。"""
    seen = []
    real = subprocess.run

    def fake(cmd, *a, **k):
        if isinstance(cmd, list) and "_child" in cmd:
            seen.append(list(cmd))
            return subprocess.CompletedProcess(cmd, 0, "", "")
        return real(cmd, *a, **k)
    row = next(r for r in BASE.load_book()["engines"] if r["id"] == "009")
    subprocess.run = fake
    try:
        with tempfile.TemporaryDirectory() as td:
            BASE.run([row], "live", Path(td) / "dict", Path(td) / "logs", 5)
    finally:
        subprocess.run = real
    return seen[0] if seen else []


def selftest(deep: bool = False) -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    rc0 = None
    if deep:
        _restore_v0108()
        try:
            rc0 = PRIOR.selftest(deep=False)
        finally:
            _install_v0109()
    print(f"=== {TAG} · 薄尾自測(子行程也用本版 → 冊 v0108 的 009 生效)===")
    if deep:
        chk("① v0108 自測過(冊 v0108 · 009 → v0103 · 載冊換裝)", rc0 == 0, f"rc {rc0}")
    _restore_v0108()
    try:
        before = _child_cmd_v0109()
    finally:
        _install_v0109()
    b_file = Path(before[3]).name if len(before) > 3 else None
    chk("② 重現桌機:v0108 的子行程是 v0107(所以載到舊冊)", b_file == "VDF_MDL008_FetchSystem_v0107.py", b_file)
    after = _child_cmd_v0109()
    a_file = Path(after[3]).name if len(after) > 3 else None
    chk("③ 本版:子行程檔 = 本檔", a_file == Path(__file__).name, a_file)
    r = subprocess.run([sys.executable, "-c", _CHILD_PROBE_V0109, str(Path(__file__).resolve())], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=300)
    got = (r.stdout.strip().splitlines() or ["?"])[-1]
    chk("④ 子行程(乾淨直譯器載本檔)載冊:009 → MDL009 v0103(清單帶 shares_issued)", got == PRIOR.MDL009_FILE_V0108, got)
    r7 = subprocess.run([sys.executable, "-c", _CHILD_PROBE_V0109, str(HERE / "VDF_MDL008_FetchSystem_v0107.py")], capture_output=True,
                        text=True, encoding="utf-8", errors="replace", timeout=300)
    got7 = (r7.stdout.strip().splitlines() or ["?"])[-1]
    chk("⑤ 對照:子行程若是 v0107 → 009 = v0102(本版修的就是這條)", got7 == "VDF_MDL009_TWStockList_v0102.py", got7)
    chk("⑥ run 呼叫完 v0107 的 __file__ 還原(不外洩)", V0107.__dict__.get("__file__") == str(PRIOR_PATH.parent / "VDF_MDL008_FetchSystem_v0107.py")
        or Path(V0107.__dict__.get("__file__", "")).name == "VDF_MDL008_FetchSystem_v0107.py", V0107.__dict__.get("__file__"))
    chk("⑦ 換裝:V0101 / BASE / V0105 / v0106 / v0107 的 run 全指本版 · 載冊仍是 v0108",
        V0101.run_v0101 is run_v0109 and BASE.run is run_v0109 and V0105.run_v0105 is run_v0109 and V0107.run_v0107 is run_v0109
        and BASE.load_book is PRIOR.load_book_v0108)
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 加速器橋 · 網路橋(模組層 VIA_NET_TOOL_PATH + def _via_net)在;不碰 TA-Lib;不寫同意閘", "[VIA:ACCEL-BRIDGE" in text
        and "def _via_net" in text and not re.search(r"^\s*(import|from)\s+talib", text, re.M)
        and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", text))
    names = [n for n in dir(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n, None))]
    chk("⑨ 尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in names), f"{len(names)} 支")
    tail = "" if deep else " · 前版鏈自測另跑(--selftest --deep)"
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · 合計 {'PASS' if all(ok) else 'FAIL'}{tail}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
