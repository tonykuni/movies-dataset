#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG117_ForwardVintage v0103 — 薄尾:merge_asof 的日期鍵對齊同一時間單位(pandas 3 起 to_datetime 會推出不同單位)

導入 PR #439 後實測(2026-10-03,VCGC-REQ139;pandas 3.0.6):v0102 --selftest → v0101 run_self_test → apply_index_vintages 的
pd.merge_asof 丟 MergeError「incompatible merge keys dtype('<M8[us]') and dtype('<M8[s]')」——v0101 _prepare_asof_inputs 對
observation_date / available_from_date / source_as_of_date 各自 pd.to_datetime,pandas 3 依輸入推單位,兩邊鍵不同型就拒合。
本版只換 v0101 的 _prepare_asof_inputs 一格:照原樣轉完再一律 astype('datetime64[ns]')(值不變,只統一單位);
計算 · 排序 · 欄位全照 v0101 / v0102。pandas 2 的行為不變(本來就是 ns)。只收 VCGC 呼叫;零網路;不碰 TA-Lib。
"""
from __future__ import annotations
import importlib.util, json, os, re, sys
from pathlib import Path
HERE = Path(__file__).resolve()
PRIOR_PATH = HERE.with_name("VDF_ENG117_ForwardVintage_v0102.py")
ENGINE = HERE.stem
DATE_COLS_V0103 = {"obs": ("observation_date",), "anc": ("available_from_date", "source_as_of_date")}
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(VDF 全導入令;惰性載入=import 時零網路、零行為變更) =====
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT;網路只認 AegisNexus);缺席回 None(誠實)"""
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
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全樹導入令;graceful 零行為變更) =====
try:
    _sa_p = HERE
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====


def _load_v0103(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


PRIOR = _load_v0103(PRIOR_PATH, "forward_vintage_v0102_for_v0103")
_BODY_V0103 = PRIOR.prior()                              # v0101 本體(v0102 已把 parquet 寫手換上)
_PREPARE_V0101 = _BODY_V0103._prepare_asof_inputs


def __getattr__(name):
    return getattr(PRIOR, name)


def _prepare_asof_inputs(observations, anchors, entity_column):
    obs, anc = _PREPARE_V0101(observations, anchors, entity_column)
    for c in DATE_COLS_V0103["obs"]:
        obs[c] = obs[c].astype("datetime64[ns]")
    for c in DATE_COLS_V0103["anc"]:
        anc[c] = anc[c].astype("datetime64[ns]")
    return obs, anc


_BODY_V0103._prepare_asof_inputs = _prepare_asof_inputs  # v0101 apply_* 經模組全域取 → 走本版


def selftest() -> int:
    import pandas as pd
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    obs = pd.DataFrame({"index_id": ["TAIEX"], "observation_date": ["2026-10-01"]})
    anc = pd.DataFrame({"index_id": ["TAIEX"], "available_from_date": [pd.Timestamp("2026-09-30").to_datetime64().astype("datetime64[s]")],
                        "source_as_of_date": ["2026-09-30"]})
    o, a = _prepare_asof_inputs(obs, anc, "index_id")
    chk("① 日期鍵統一 datetime64[ns](一邊 [s] 一邊字串也對齊;值不變)",
        str(o["observation_date"].dtype) == str(a["available_from_date"].dtype) == "datetime64[ns]"
        and a["available_from_date"].iloc[0] == pd.Timestamp("2026-09-30"), (o["observation_date"].dtype, a["available_from_date"].dtype))
    rc = PRIOR.selftest()
    chk("② v0102 → v0101 run_self_test 過(本機 pandas " + pd.__version__ + ")", rc == 0, f"rc {rc}")
    text = HERE.read_text(encoding="utf-8")
    chk("③ 加速器橋 · 網路橋在 · 不碰 TA-Lib · 換裝在位", "[VIA:ACCEL-BRIDGE" in text and "[VIA:NET-BRIDGE" in text
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M) and _BODY_V0103._prepare_asof_inputs is _prepare_asof_inputs)
    print(f"  [計] {ENGINE} 本版 {sum(ok)}/{len(ok)} · 合計 {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[GATED] ONLY_VIA_ENTRY")
        return 2
    if sys.argv[1:] in (["--selftest"], ["--self-test"]):
        try:
            return selftest()
        except ImportError as exc:
            print("[ABSENT] " + str(exc))
            return 3
    return PRIOR.main()


if __name__ == "__main__":
    raise SystemExit(main())
