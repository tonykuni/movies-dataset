#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG088_ConsensusFusionBridge v0105 — 薄尾:自測不再被「本境有沒有正典庫」左右(引擎行為一字不動)

v0104→v0105(R46 2026-10-02 · 操作員令「單獨測試vdf所有引擎」「實際測試修正至成功」):VDF 74 支逐支經 VCGC 自測,本支 ② ④ 紅。
量到的:容器裡沒有正典庫 output_hub/mega/vdf_tw_market.duckdb → status() 照實回 ABSENT「正典庫或 consensus 兩表不在」;
可是 ② ④ 的期望寫的是「來源缺 → NODATA」—— 它默認正典庫一定在(工作站是在的)。引擎沒錯,錯在測資跟著環境走。
v0105 自測:在暫存夾建一份「兩張正典表都在、0 列」的正典庫,把本體的 CANON_DB 指過去跑前版七檢(來源照樣缺 → 應為 NODATA),
跑完還原;另一檢驗本境真實狀態照實回報(正典庫不在 = ABSENT 且原因點名,不假綠)。零網路 · 零寫正式庫 · 不用 TA-Lib。
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
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_ENG088_ConsensusFusionBridge"


def _vnum(p: Path) -> int:
    m = re.search(r"_v(\d+)$", p.stem)
    return int(m.group(1)) if m else -1


_PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location("consensus_prior_for_" + Path(__file__).stem, _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    return PRIOR.main()


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print("=== VDF_ENG088 共識融合橋 v0105 · 薄尾自測(正典庫測資自帶;零網路 · 零寫正式庫)===")
    real = PRIOR.status(do_print=False)
    real_canon = PRIOR.CANON_DB.is_file()
    chk("① 本境真實狀態照實回:正典庫不在 → ABSENT 且原因點名;在 → 照前版四態(不假綠)",
        (real["state"] == "ABSENT" and ("正典庫" in real["why"] or real.get("source_db") is None)) if not real_canon
        else real["state"] in ("GREEN", "NODATA", "ABSENT"), f"{real['state']} · 正典庫{'在' if real_canon else '不在'}")
    import duckdb
    saved = PRIOR.CANON_DB
    with tempfile.TemporaryDirectory() as td:
        fx = Path(td) / "vdf_tw_market.duckdb"
        con = duckdb.connect(str(fx))
        for t in PRIOR.CANON_TABLES:
            con.execute(f"CREATE TABLE {t} (date DATE, ticker VARCHAR)")
        con.close()
        PRIOR.CANON_DB = fx
        try:
            fx_status = PRIOR.status(do_print=False)
            rc = PRIOR.selftest()
        finally:
            PRIOR.CANON_DB = saved
    chk("② 測資正典庫(兩表在、0 列)下前版七檢全過(來源缺 → NODATA「缺料不是壞掉」· plan 只給兩步不猜對映 · sync 誠實停)",
        rc == 0, f"rc {rc} · 測資下 status={fx_status['state']}")
    chk("③ 跑完正典庫指回原處(不留測資路徑)", PRIOR.CANON_DB == saved, PRIOR.CANON_DB.name)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("④ 本支帶加速器橋 · 網路橋;不含 TA-Lib 匯入", "[VIA:ACCEL-BRIDGE" in src and "[VIA:NET-BRIDGE" in src
        and not re.search(r"^\s*(?:import|from)\s+" + "ta" + r"lib\b", src, re.M))
    good = all(ok)
    print(f"  [計] VDF_ENG088 v0105 薄尾 {sum(ok)}/{len(ok)} · 合計 {'PASS' if good else 'FAIL'}")
    return 0 if good else 1


if __name__ == "__main__":
    sys.exit(main())
