#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VDF_ENG070_GroupClassificationIndex v0114 — 薄尾(v0113 以前一字不動):自測不吃本機資料(暫存夾隔離)

桌機 2026-11-26 19:20 實錄(HostBoot vdfcheck):VDF test 裡只有本引擎 TIMEOUT(rc 124,VDF 管理器每支 120 秒),UNIT 格因此紅。
病因:v0112 的自測看到真庫(output_hub/mega/vdf_tw_market.duckdb 有三張表)就切「全檢」,對全市場真資料跑完整 run(),
  還把報告寫進真的 VIA_Reports/group_class 與 U/I 頁;容器沒有庫只跑「誠實缺料二檢」0 秒 → 同一支自測兩邊結果不同。
  違反 CLAUDE.md「自測不吃本機狀態:自測一律在暫存夾造資料」。
本版只改自測:
  --selftest        前版鏈上每一個模組的 DB_TW / REP / OUT_UI 暫時指到暫存夾(庫不存在)→ 前版鏈一律走「誠實缺料」路徑
                    (驗誠實停 rc 2 · 靜態紀律),再加 v0113 的 FRAME 守門三檢;跑完全部還原、暫存夾刪乾淨(零足跡)。
  --selftest-full   照舊(v0113 原樣):資料在位就對真資料全檢 —— 只給要手動深驗的人,VDF test 不跑它。
正式動詞(run · CLI)全部交給 v0113,行為一字不改。零網路;不設同意閘;不用 TA-Lib。
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
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_ENG070_GroupClassificationIndex"
ISOLATE = ("DB_TW", "REP", "OUT_UI")                 # 前版鏈的自測 / run() 在呼叫當下讀這三個模組全域


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", path.stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def guard() -> dict:                                 # 必備 API 照前版
    return PRIOR.guard()


def main() -> int:
    return PRIOR.main()


def chain_modules() -> list:
    """已載入的本家族前版模組(含 v0113 釘名載入的 v0108 等):任何帶 DB_TW / REP / OUT_UI 的都算。"""
    mods = []
    for name, m in list(sys.modules.items()):
        if m is None or not name.startswith(_STEM):
            continue
        if any(hasattr(m, k) and isinstance(getattr(m, k), Path) for k in ISOLATE):
            mods.append(m)
    return mods


def isolated_selftest() -> tuple:
    """前版鏈自測在暫存夾隔離下跑:庫路徑指到不存在的暫存檔 → 誠實缺料路徑;報告 / 頁寫暫存夾。回 (rc, 改了幾個模組, 暫存夾留下的檔)。"""
    box = Path(tempfile.mkdtemp(prefix="eng070_iso_"))
    saved = []
    try:
        for m in chain_modules():
            for k in ISOLATE:
                if hasattr(m, k) and isinstance(getattr(m, k), Path):
                    saved.append((m, k, getattr(m, k)))
                    setattr(m, k, box / ("missing.duckdb" if k == "DB_TW" else (k.lower() + (".html" if k == "OUT_UI" else ""))))
        rc = PRIOR.selftest()
    finally:
        for m, k, v in saved:
            setattr(m, k, v)
        left = sorted(str(p.relative_to(box)) for p in box.rglob("*"))
        shutil.rmtree(box, ignore_errors=True)
    return rc, len({id(m) for m, _, _ in saved}), left


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}", flush=True)

    print(f"=== {Path(__file__).stem} · 薄尾自測(前版鏈在暫存夾隔離下跑;不吃本機資料)===", flush=True)
    chk("① 加速器真的載到(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    chk("② 網路工具橋在位(載入不出網)", VIA_NET_TOOL_PATH is not None)
    before = {(id(m), k): getattr(m, k) for m in chain_modules() for k in ISOLATE if hasattr(m, k)}
    rc, n_mod, left = isolated_selftest()
    after = {(id(m), k): getattr(m, k) for m in chain_modules() for k in ISOLATE if hasattr(m, k)}
    chk("③ 前版鏈自測(v0113 FRAME 守門 + 誠實缺料路徑)在隔離下照過", rc == 0, f"rc={rc}")
    chk("④ 隔離真的生效(至少一個前版模組的 DB_TW 被換)· 跑完路徑全部還原", n_mod >= 1 and before == after, (n_mod, len(before)))
    db_tw = [v for (i, k), v in after.items() if k == "DB_TW"]
    chk("⑤ 跑完 DB_TW 指回真庫位置(不是暫存夾)", db_tw and all("eng070_iso_" not in str(v) for v in db_tw))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 檔面:第 3 行加速器標記 · glob 取前版 · --selftest-full 保留舊全檢 · 零 TA-Lib · 不設同意閘",
        src.splitlines()[2].startswith("# [VIA:ACCEL-BRIDGE") and "HERE.glob(_STEM" in src and '"--selftest-full"' in src
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"^\s*os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src, re.M))
    print(f"  {Path(__file__).stem} 薄尾 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'} · 隔離夾殘留 {len(left)}", flush=True)
    return 0 if all(ok) else 1


if __name__ == "__main__":
    if "--selftest-full" in sys.argv[1:]:
        raise SystemExit(PRIOR.selftest())
    raise SystemExit(selftest() if "--selftest" in sys.argv[1:] else main())
