#!/usr/bin/env python3
r"""VDF_MDL015_MacroHierarchy v0101 — 薄尾:自測不再被「本機 VAKE_ROOT / ~/VAKE」左右,也不再刪掉操作員自己的 VAKE_ROOT(引擎行為一字不動)

工作站實跑(2026-11-15 ActivateVDF engine_launch):本支 RED 12/14 —— ⑭「環境變數原樣」FAIL(另一項同源)。
v0100 自測 ⑫ 先 os.environ["VAKE_ROOT"] = 暫存夾,跑完 os.environ.pop("VAKE_ROOT") —— 操作員機器本來就設了 VAKE_ROOT 時,
這一 pop 把操作員的值刪掉 → ⑭ 比對「自測前後環境一樣」必 FAIL(而且自測行程裡的 VAKE_ROOT 真的被刪了)。
另外 akshare 車道在 VAKE_ROOT 沒設時退回 ~/VAKE:工作站有真的 VAKE 知識庫 → ⑪「知識庫不在 = ABSENT」判 FAIL。
容器重現:VAKE_ROOT 設成任一路徑 → v0100 自測 13/14 · ⑭ FAIL;不設 → 14/14。
本版(v0100 一字不動;只換自測期間的環境,跑完還原):
  ① 測具:自測期間先把 VAKE_ROOT 拿掉、Path.home() 指向空暫存夾(看不到本機 ~/VAKE)→ 跑 v0100 自測 → rc 0。
  ② 自測跑完 VAKE_ROOT 還是操作員原本的值(模擬工作站:先設一個有知識庫的 VAKE_ROOT 再跑)。
  ③ Path.home 與環境全數還原。④ 兩座橋 · 不匯入他系統 · 不碰 TA-Lib · 同意閘不讀不寫。零網路。
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

_STEM = "VDF_MDL015_MacroHierarchy"
import contextlib
import importlib.util
import os
import pathlib
import re
import sys
import tempfile
import warnings
from pathlib import Path

HERE = Path(__file__).resolve().parent
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"


def _vnum_tail(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_tail(p) < _vnum_tail(__file__)), key=_vnum_tail)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
with warnings.catch_warnings():
    warnings.simplefilter("ignore", SyntaxWarning)
    warnings.simplefilter("ignore", DeprecationWarning)
    _spec.loader.exec_module(PRIOR)


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def _own_src_ok() -> bool:
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    return ("[VIA:ACCEL-BRIDGE" in src and "[VIA:NET-BRIDGE" in src and "_CONSENT" not in body
            and not re.search(r"^\s*(import|from)\s+(CGC_|VRN_|VCGC|ta" + r"lib\b)", src, re.M))


class _Checks:
    def __init__(self):
        self.ok = []

    def __call__(self, name, cond, note=""):
        self.ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)[:300]) if (note and not cond) else ""), flush=True)

    def done(self) -> int:
        good = all(self.ok)
        print("[計] %s 薄尾 %d/%d · %s" % (TAG, sum(self.ok), len(self.ok), "PASS" if good else "FAIL"), flush=True)
        return 0 if good else 1


_HOME_OWN = vars(pathlib.Path).get("home")          # 3.13:home 定義在 PathBase(Path 自己沒有)→ 還原時刪掉本版放上去的那個


@contextlib.contextmanager
def vake_sandbox():
    """自測測具:VAKE_ROOT 拿掉 · Path.home() 指向空暫存夾(看不到本機 ~/VAKE);跑完全數還原。"""
    keep = os.environ.pop("VAKE_ROOT", None)
    td = tempfile.mkdtemp(prefix="vdf_vake_box_")
    pathlib.Path.home = classmethod(lambda cls: cls(td))
    try:
        yield td
    finally:
        if _HOME_OWN is None:
            del pathlib.Path.home
        else:
            pathlib.Path.home = _HOME_OWN
        if keep is not None:
            os.environ["VAKE_ROOT"] = keep
        import shutil
        shutil.rmtree(td, ignore_errors=True)


def selftest() -> int:
    chk = _Checks()
    print("=== %s · 薄尾自測(VAKE 測具;零網路)===" % TAG, flush=True)
    real_home = pathlib.Path.home()
    before = os.environ.get("VAKE_ROOT")
    op = Path(tempfile.mkdtemp(prefix="vdf_vake_operator_"))
    try:
        (op / "VAKE" / "knowledge").mkdir(parents=True)
        (op / "VAKE" / "knowledge" / "vake_registry.json").write_text('[{"fn": "macro_usa_ism_pmi", "title": "ISM PMI", "category": "macro"}]', encoding="utf-8")
        os.environ["VAKE_ROOT"] = str(op / "VAKE")                       # 模擬工作站:操作員自己設了 VAKE_ROOT,且有知識庫
        with vake_sandbox():
            rc = PRIOR.selftest()
        after = os.environ.get("VAKE_ROOT")
    finally:
        if before is None:
            os.environ.pop("VAKE_ROOT", None)
        else:
            os.environ["VAKE_ROOT"] = before
        import shutil
        shutil.rmtree(op, ignore_errors=True)
    chk("① 操作員設了 VAKE_ROOT(有知識庫)的機器:測具下前版自測 rc 0", rc == 0, rc)
    chk("② 自測跑完 VAKE_ROOT 還是操作員原本的值(前版會把它 pop 掉)", after == str(op / "VAKE"), after)
    chk("③ Path.home 與 VAKE_ROOT 還原成自測前", pathlib.Path.home() == real_home and os.environ.get("VAKE_ROOT") == before
        and vars(pathlib.Path).get("home") is _HOME_OWN)
    chk("④ 兩座橋在 · 不匯入他系統程式 · 不碰 TA-Lib · 同意閘不讀不寫", _own_src_ok())
    return chk.done()


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv or argv[:1] == ["selftest"]:
        return selftest()
    return PRIOR.main(argv)


if __name__ == "__main__":
    sys.exit(main())
