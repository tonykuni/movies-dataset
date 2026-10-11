#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL237_NumberingSystem v0118 — 薄尾:audit 的 IMMUT 不把交接收據(docs/handoff/evidence/)當「已發布版號冊」

實錄(2026-10-11 VCGC 全功能串測 E-number-audit 紅 rc 1):
  [註冊完整性] RED IMMUT 6 · 已發布版號冊就地改(要出新版號檔) · docs/handoff/evidence/vdf_fetch_groups_v0100.json ; …v0101 ; … ; …v0105
  交接案 vdf_fetch_groups_v0100–v0105 重跑後收據改了;v0109 的 immut_violations 看檔名 *_vNNNN.json + 同夾同家族 ≥ 2 版就當版號冊,
  可是收據的 _vNNNN 是案名(案釘的版),不是冊的版;收據依設計每次重跑都覆寫(CGC_MDL140 先按 SHA 封存到 history/ 再寫)。
  凡基準上已有、之後又重跑的 *_vNNNN 案,稽核就紅一次 —— 規則誤判,不是冊被就地改。
本版只加一格(v0100–v0117 一字不動):immut_violations 先去掉 docs/handoff/evidence/ 底下的路徑(具名豁免:交接收據),
  其餘(registry 冊 · 快照冊 · 同夾多版冊)照 v0109 判。活冊 / 快照家族的規則與 arch 冊(mutability)不動。
只收 VCGC 呼叫(經 via-vcgc run);零網路;不碰 TA-Lib。
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
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = Path(__file__).stem
_STEM = "CGC_MDL237_NumberingSystem"
RECEIPT_PREFIX_V0118 = "docs/handoff/evidence/"       # 交接收據夾:活檔(每次重跑覆寫;舊版按 SHA 封存在 history/),不是版號冊


def _vnum_v0118(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


def _load_v0118(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0118(p) < _vnum_v0118(__file__)), key=_vnum_v0118)
PRIOR = _load_v0118(PRIOR_PATH, _STEM + "_prior_for_" + ENGINE)        # v0117:動詞 / 旗標守門 · door 報尾版
BASE = PRIOR.BASE                                                       # v0100:build() · door
BASE.ENGINE = ENGINE                                                    # door / SSOT engine 報實際尾版(同 v0117 ②)


def _chain_v0118() -> list:
    """前版鏈:從 PRIOR 起,沿每版全域裡「同家族的模組物件」(不限名稱叫 PRIOR / BASE)廣度搜尋,同一版只收一次。"""
    import types
    mods, todo = [], [PRIOR]
    while todo:
        m = todo.pop(0)
        if not isinstance(m, types.ModuleType) or m in mods:
            continue
        mods.append(m)
        for v in list(vars(m).values()):
            if isinstance(v, types.ModuleType) and _STEM in str(getattr(v, "__file__", "")) and v not in mods:
                todo.append(v)
    return mods


def _immut_owner():
    """沿前版鏈找到自己定義 immut_violations 與 registry_checks 的那一版(v0109 本體)。"""
    for m in _chain_v0118():
        fn = vars(m).get("immut_violations")
        if callable(fn) and getattr(fn, "__module__", None) == m.__name__ and callable(vars(m).get("registry_checks")):
            return m
    return None


V0109 = _immut_owner()
_IMMUT_V0109 = vars(V0109)["immut_violations"] if V0109 is not None else None


def immut_violations(changed, base_versions: dict, arch_doc: dict) -> list:
    """同 v0109,但 docs/handoff/evidence/ 底下的交接收據不算版號冊(具名豁免);其餘照舊。"""
    kept = [rel for rel in changed if not Path(rel).as_posix().startswith(RECEIPT_PREFIX_V0118)]
    return _IMMUT_V0109(kept, base_versions, arch_doc)


if V0109 is not None:
    V0109.immut_violations = immut_violations          # registry_checks 讀模組全域 → audit 走本版


def __getattr__(name):
    return getattr(PRIOR, name)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    return PRIOR.main(args)                             # v0117 的動詞 / 旗標守門照舊


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    print(f"=== {ENGINE} · 薄尾自測(IMMUT 不算交接收據)===")
    chk("① 沿鏈找到 immut_violations / registry_checks 的本體(v0109)並換裝;door 報本尾版",
        V0109 is not None and Path(getattr(V0109, "__file__", "")).stem.endswith("_v0109") and V0109.immut_violations is immut_violations and BASE.ENGINE == ENGINE,
        getattr(V0109, "__file__", None))
    changed = ["docs/handoff/evidence/vdf_fetch_groups_v0100.json", "docs/handoff/evidence/vdf_fetch_groups_v0105.json",
               "r/Multi_v0101.json", "r/Single_v0100.json", "r/Req_SSOT_v0104.json"]
    base_versions = {"docs/handoff/evidence|vdf_fetch_groups": 6, "r|Multi": 2, "r|Single": 1}
    arch_doc = {"mutability": {"snapshot_families": ["Req_SSOT"], "living_books": []}}
    mine = immut_violations(changed, base_versions, arch_doc)
    orig = _IMMUT_V0109(changed, base_versions, arch_doc) if _IMMUT_V0109 else None
    chk("② 收據(docs/handoff/evidence/*_vNNNN.json,同夾 6 版)不算;同夾多版冊 · 快照家族冊照抓;單版冊照舊不算;v0109 原版會誤抓收據",
        mine == ["r/Multi_v0101.json", "r/Req_SSOT_v0104.json"] and orig is not None and any(x.startswith("docs/handoff/evidence/") for x in orig),
        (mine, orig))
    try:
        rows = V0109.registry_checks()
        immut_row = next((r for r in rows if r.get("rule") == "IMMUT"), {})
        hits = list(immut_row.get("hits") or [])
        chk("③ 真倉 audit 的 IMMUT 列:沒有交接收據(其餘命中照實列)", not any(str(h).startswith("docs/handoff/evidence/") for h in hits),
            (immut_row.get("lamp"), hits[:4]))
    except Exception as exc:                                   # 沒有 git 基準時量不到,照實不算過
        chk("③ 真倉 audit 的 IMMUT 列:沒有交接收據", False, f"{type(exc).__name__}: {exc}")
    text = Path(__file__).read_text(encoding="utf-8")
    chk("④ 加速器橋 · 網路橋在 · 不碰 TA-Lib", "[VIA:ACCEL-BRIDGE" in text and "[VIA:NET-BRIDGE" in text
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M))
    keep_engine = BASE.ENGINE
    BASE.ENGINE = PRIOR.ENGINE                                  # v0117 ⑤ 驗 door 報它自己 → 跑前版鏈期間換回,跑完換上本版
    try:
        rc_prior = PRIOR.selftest()                             # 前版鏈照印(交接案 numbering 的標記在鏈上)
    finally:
        BASE.ENGINE = keep_engine
    chk("⑤ 前版鏈 v0117 → … 自測 rc 0;跑完 door 仍報本尾版", rc_prior == 0 and BASE.ENGINE == ENGINE, f"rc {rc_prior}")
    print(f"  [計] {ENGINE} 本版 {sum(ok)}/{len(ok)} · 前版鏈 {'PASS' if rc_prior == 0 else 'FAIL'} · 合計 {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
