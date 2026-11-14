#!/usr/bin/env python3
r"""VDF_ENG088_ConsensusFusionBridge v0106 — 薄尾:自測不再被「本機有沒有來源庫」左右 · 自測只掃樹一次(引擎行為一字不動)

工作站實跑(2026-11-15 ActivateVDF engine_launch):本支 RED 177.6 秒 ——
  · v0105 只把「正典庫」換成測資,「來源庫」(consensus_history.duckdb)照讀本機真的;工作站真的有(consensus_daily 11,974 列)
    → plan 走「來源在」那條路,步驟沒有 why 欄 → 前版 ④ KeyError: 'why' 整支崩。容器重現:樹裡放一份 consensus_history.duckdb
    → v0105 自測 ④ ⑤ FAIL。
  · source_db() 每呼叫一次就把整棵樹 glob 一遍(**/consensus_history.duckdb);自測呼叫好幾次 → OneDrive 上的工作站很慢。
本版(v0100 … v0105 一字不動;只換自測期間的測具,跑完還原):
  ① 本境真實檢:真的 source_db() 只跑一次(結果暫存給這一檢);來源在 → plan 只列真表、每步 COPY_ONLY 反連結、不編對映;
     來源不在 → 只給兩步、不猜(兩種環境都照實判,不假綠)。
  ② 測具檢:source_db 換成「刻意不在」(不掃樹)→ 跑 v0105 自測(它再把正典庫換成暫存測資)→ 前版鏈 rc 0。
零網路 · 零寫正式庫(sync 只寫進 v0105 的暫存測資庫)· 不碰 TA-Lib · 同意閘不讀不寫。
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

_STEM = "VDF_ENG088_ConsensusFusionBridge"
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


def _bridge_module():
    """source_db / plan / status / sync 定義在哪一版(v0104 本體);plan 從那版的模組全域找 source_db。"""
    m, seen = PRIOR, []
    while m is not None and m not in seen:
        if "plan" in vars(m) and "source_db" in vars(m):
            return m
        seen.append(m)
        m = vars(m).get("PRIOR")
    return None


BODY = _bridge_module()
_SRC_ORIG = BODY.source_db if BODY else None


@contextlib.contextmanager
def source_as(fn):
    BODY.source_db = fn
    try:
        yield
    finally:
        BODY.source_db = _SRC_ORIG


def selftest() -> int:
    chk = _Checks()
    print("=== %s · 薄尾自測(來源庫測具 · 只掃樹一次;零網路 · 零寫正式庫)===" % TAG, flush=True)
    walks = [0]

    def counted():
        walks[0] += 1
        return _SRC_ORIG()
    real = counted()
    with source_as(lambda: real):
        p = BODY.plan(do_print=False)
    steps = p.get("steps") or []
    if real[0] is None:
        ok1 = len(steps) == 2 and "我不猜" in str(steps[0].get("why", ""))
        how = "來源庫不在 → 兩步、不猜對映"
    else:
        ok1 = all(s.get("from") in BODY.SRC_TABLES and s.get("to") in BODY.CANON_TABLES and "COPY_ONLY" in str(s.get("how", "")) for s in steps)
        how = "來源庫在(%s)→ %d 步,只列真表 · COPY_ONLY 反連結" % (Path(real[0]).name, len(steps))
    chk("① 本境真實來源庫照實:%s" % how, ok1, steps[:2])
    with source_as(lambda: (None, "測具:來源庫刻意不在(自測不讀本機真庫)")):
        rc = PRIOR.selftest()
    chk("② 測具下(來源庫刻意不在 · 正典庫由 v0105 換成暫存測資)前版鏈自測 rc 0", rc == 0, rc)
    chk("③ 測具還原(source_db 回原函式)· 本自測真的掃樹只 %d 次" % walks[0], BODY.source_db is _SRC_ORIG and walks[0] == 1)
    chk("④ 兩座橋在 · 不匯入他系統程式 · 不碰 TA-Lib · 同意閘不讀不寫", _own_src_ok())
    return chk.done()


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    return PRIOR.main()


if __name__ == "__main__":
    sys.exit(main())
