#!/usr/bin/env python3
r"""VDF_ENG069_RevenueConsensusAnalysis v0111 — 薄尾:自測在沒有「建立符號連結」權限的 Windows 帳號也跑得完(引擎行為一字不動)

工作站實跑(2026-11-15 ActivateVDF engine_launch):本支 RED —— v0110 自測 ①b 用 Path.symlink_to 造「斷掉的連結」候選;
Windows 一般帳號沒有建符號連結的權限 → OSError [WinError 1314] 用戶端沒有這項特殊權限 → 自測整支崩(引擎本身沒錯)。
容器重現:把 Path.symlink_to 換成丟 WinError 1314 → v0110 自測同樣崩在 symlink_to。
本版(v0100 … v0110 一字不動;只換自測期間的測具,跑完還原):
  · 自測期間 Path.symlink_to 先照常建;建不了(WinError 1314 / PermissionError)→ 改建同名一般檔,並讓這個路徑的 stat()
    丟 FileNotFoundError(= stat 一個斷掉的連結時拿到的同一個例外)→ v0110 ①b 要驗的「壞候選略過照記」照樣被驗到。
  · 能建連結的機器(Linux · 開了開發人員模式的 Windows)照用真連結。
自測:① 模擬沒有權限 → 前版鏈 rc 0 ② 照常 → 前版鏈 rc 0 ③ 測具還原 ④ 兩座橋 · 不匯入他系統 · 不碰 TA-Lib · 同意閘不讀不寫。
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

_STEM = "VDF_ENG069_RevenueConsensusAnalysis"
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


_REAL_LINK = pathlib.Path.symlink_to
_REAL_STAT = pathlib.Path.stat


def _no_privilege(exc: OSError) -> bool:
    return getattr(exc, "winerror", None) == 1314 or isinstance(exc, PermissionError)


@contextlib.contextmanager
def symlink_fallback(force: bool = False):
    """自測測具:建不了符號連結 → 同名一般檔 + 該路徑 stat() 丟 FileNotFoundError(斷連結的同一個例外)。"""
    fake, used = set(), []

    def link(self, target, target_is_directory=False):
        try:
            if force:
                exc = OSError(22, "模擬:沒有建符號連結的權限")
                exc.winerror = 1314
                raise exc
            return _REAL_LINK(self, target, target_is_directory)
        except OSError as exc:
            if not _no_privilege(exc):
                raise
            self.write_bytes(b"")
            fake.add(os.path.abspath(str(self)))
            used.append(str(self))
            return None

    def stat(self, *a, **k):
        p = os.path.abspath(str(self))
        if p in fake and os.path.lexists(p):
            raise FileNotFoundError(2, "模擬斷掉的連結", str(self))
        return _REAL_STAT(self, *a, **k)

    pathlib.Path.symlink_to, pathlib.Path.stat = link, stat
    try:
        yield used
    finally:
        pathlib.Path.symlink_to, pathlib.Path.stat = _REAL_LINK, _REAL_STAT


def selftest() -> int:
    chk = _Checks()
    print("=== %s · 薄尾自測(沒有建連結權限也跑得完;零網路)===" % TAG, flush=True)
    with symlink_fallback(force=True) as used:
        rc1 = PRIOR.selftest()
    chk("① 模擬 Windows 沒有建符號連結權限(WinError 1314):測具接手 %d 次 · 前版鏈自測 rc 0" % len(used), rc1 == 0 and len(used) >= 1, rc1)
    with symlink_fallback() as used2:
        rc2 = PRIOR.selftest()
    chk("② 照常跑(這台%s建符號連結):前版鏈自測 rc 0" % ("不能" if used2 else "能"), rc2 == 0, rc2)
    chk("③ 測具還原:Path.symlink_to / Path.stat 回原物件", pathlib.Path.symlink_to is _REAL_LINK and pathlib.Path.stat is _REAL_STAT)
    chk("④ 兩座橋在 · 不匯入他系統程式 · 不碰 TA-Lib · 同意閘不讀不寫", _own_src_ok())
    return chk.done()


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    return PRIOR.main()


if __name__ == "__main__":
    sys.exit(main())
