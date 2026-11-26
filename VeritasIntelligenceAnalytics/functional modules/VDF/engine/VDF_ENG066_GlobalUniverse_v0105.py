#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VDF_ENG066_GlobalUniverse v0105 — 薄尾(v0104 以前一字不動):前版自測在「合併冊卸下」的狀態下跑

病因(2026-11-26 VDF 輸出驗證 · 容器實錄):VDF test 裡 ENG066 rc 1。
  v0104 在模組載入時把 v0102 本體的 load_roster 換成「基本冊 + VDF 擴充冊」合併版(VDF-REQ050,正確行為),
  它的 ⑧ 卻在合併版還裝著時叫前版鏈自測;v0102 的 ① 要求類別「恰好」是操作員批226 的 11 類 →
  合併後多了擴充類別,① 必然不過(v0102 / v0103 單獨跑都 8/8)。引擎的擷取行為沒有錯,錯在自測的量法。
本版只改自測:前版鏈自測那一段暫時換回基本冊的 load_roster,跑完立刻裝回合併版;
v0104 自己的 ①~⑦(合併冊邏輯)照跑。正式動詞(run · --list)全部交給 v0104,行為一字不改。
零網路(自測);不設同意閘;不用 TA-Lib。用法同前:run [--cats …] [--start …] [--end …] | --list | --selftest
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
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_ENG066_GlobalUniverse"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def load_roster() -> dict:                       # 必備 API 照前版(合併冊)
    return PRIOR.load_roster()


def run(*a, **k):
    return PRIOR.PRIOR.run(*a, **k)


_V0103_SELFTEST = PRIOR.PRIOR.selftest          # 前版鏈自測本身(載入時記下,不會被下面的換裝影響)


def chain_selftest_base_roster() -> int:
    """前版鏈(v0103 → v0102)自測:暫時換回基本冊的 load_roster,跑完立刻裝回合併版。"""
    base_mod = PRIOR._BASE_MOD
    current = base_mod.load_roster
    base_mod.load_roster = PRIOR._BASE_LOAD
    try:
        return _V0103_SELFTEST()
    finally:
        base_mod.load_roster = current


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    return PRIOR.main()


def selftest() -> int:
    ok = fail = 0

    def chk(name, cond, note=""):
        nonlocal ok, fail
        ok += bool(cond)
        fail += not cond
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}", flush=True)

    print(f"=== {TAG} · 薄尾自測(前版鏈自測在基本冊下跑;零網路)===", flush=True)
    chk("① 加速器真的載到(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    chk("② 網路工具橋在位(鎖冊網路工具路徑找得到;載入不出網)", VIA_NET_TOOL_PATH is not None)
    base_mod = PRIOR._BASE_MOD
    chk("③ 平常狀態裝的是合併冊(VDF-REQ050 行為不變)", base_mod.load_roster is PRIOR.load_roster)
    # v0104 自己的合併冊檢查(①~⑦)照跑;它的 ⑧ 叫的前版鏈自測換成「基本冊下跑」
    v0103 = PRIOR.PRIOR
    orig = v0103.selftest
    v0103.selftest = chain_selftest_base_roster
    try:
        rc = PRIOR.selftest()
    finally:
        v0103.selftest = orig
    chk("④ v0104 自測(合併冊 ①~⑦ + 前版鏈在基本冊下跑)照過", rc == 0, f"(rc {rc})")
    chk("⑤ 跑完合併冊已裝回、前版自測函式已還原", base_mod.load_roster is PRIOR.load_roster and v0103.selftest is orig)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 檔面:第 3 行加速器標記 · glob 取前版 · 零 TA-Lib · 不設同意閘",
        src.splitlines()[2].startswith("# [VIA:ACCEL-BRIDGE") and "HERE.glob(_STEM" in src
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"^\s*os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src, re.M))
    print(f"  [計] {TAG} 自測 OK {ok} · FAIL {fail}", flush=True)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
