#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""CGC_MDL237_NumberingSystem v0121 — 薄尾:候選契約多收三類(總經 MRC · 市場 FM · 財報 FD),給子系統依大類申請中央號

操作員令(2026-11-14):「依大類發中央號,總經 MRC · 市場 FM · 財報 FD」(對象:VDF-390 擷取總冊 390 項)。
VCGC 衝突閘「子系統邊界」不讓 VCGC 指定 VDF 冊發號(VDF 的冊歸 VDF);正路 = VDF 提申請 → VCGC 收件(CGC_MDL278)
→ 候選冊 → 本系統中央檢測與發號 → 發號回執 → VDF 自己把號寫回自己的冊。原候選契約(v0114)只收
參數 / 邏輯 / 正則 / 同義字 / 政策 / 冊,本版只增(v0100 … v0120 一字不動):
  ① 候選型別多三種:MACRO → MRC(總體經濟)· INSTRUMENT → FM(金融市場商品)· FINDATA → FD(財務數據欄位)。
  ② MRC / FM 是帶地區的號(<類>-<地區>-四碼):候選列沒有地區欄,地區取申請的 scope 最後一段
     (例 vdf.fetchone.mrc.us → US · vdf.fetchone.fm.tw → TW);沒有就 GLB。FD 不帶地區。
其餘檢測(欄位 · 身分 · 版本 · 同字異義 · 撞號)全照 v0114 起的既有規則;發號仍只由既有分配器(只增)做;本檔不寫檔。
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

import copy
import importlib.util
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = Path(__file__).stem
_STEM = "CGC_MDL237_NumberingSystem"


def _vnum_v0121(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


def _load_v0121(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0121(p) < _vnum_v0121(__file__)), key=_vnum_v0121)
PRIOR = _load_v0121(PRIOR_PATH, _STEM + "_prior_for_" + ENGINE)        # v0120:舊同義字列 scope 投影 · .py 常數正則
BASE = PRIOR.BASE
BASE.ENGINE = ENGINE


def _own(name: str):
    m, seen = PRIOR, []
    while m is not None and m not in seen:
        if name in getattr(m, "__dict__", {}):
            return m
        seen.append(m)
        m = getattr(m, "__dict__", {}).get("PRIOR")
    return None


INTAKE = _own("TYPE_KIND")                                              # v0114:候選契約 · 檢測 · candidate_items
NEW_TYPES = {"MACRO": "MRC", "INSTRUMENT": "FM", "FINDATA": "FD"}
INTAKE.TYPE_KIND.update(NEW_TYPES)                                      # 只增:舊型別一個不動
_CAND_V0114 = INTAKE.candidate_items


def region_from_scope(scope: str) -> str:
    seg = str(scope or "").rsplit(".", 1)[-1].upper()
    return seg if re.fullmatch(r"[A-Z]{2,3}", seg) and seg not in ("MRC", "FM", "FD") else "GLB"


def candidate_items(candidates, source, registered=(), legacy=()):
    items, plan = _CAND_V0114(candidates, source, registered, legacy)
    for it in items:
        if it.get("kind") in BASE.REGIONAL and not it.get("region"):
            it["region"] = region_from_scope(it.get("scope"))
    return items, plan


INTAKE.candidate_items = candidate_items


def __getattr__(name):
    return getattr(PRIOR, name)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    return PRIOR.main(args)


def _fixture(cid, atype, scope, skey, value):
    raw = INTAKE.fixture(cid, asset_type=atype, scope=scope, semantic_key=skey, value=value)
    return copy.deepcopy(raw)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:300]) if note and not cond else ''}", flush=True)

    print(f"=== {ENGINE} · 薄尾自測(候選契約多收 MACRO → MRC · INSTRUMENT → FM · FINDATA → FD)===", flush=True)
    chk("① 候選型別:三個新型別對到 MRC / FM / FD;舊型別(INPT · REGEX · SYNONYM · SSOT …)照舊",
        all(INTAKE.TYPE_KIND[k] == v for k, v in NEW_TYPES.items()) and INTAKE.TYPE_KIND["REGEX"] == "RGX" and INTAKE.TYPE_KIND["SYNONYM"] == "SYN"
        and INTAKE.TYPE_KIND["SSOT"] == "SSOT" and INTAKE.TYPE_KIND["INPT"] == "PRMT")
    a = _fixture("VDF_FETCH_US-L01", "MACRO", "vdf.fetchone.mrc.us", "US-L01", {"id": "US-L01", "name": "ISM 製造業 PMI"})
    b = _fixture("VDF_FETCH_PX-01", "INSTRUMENT", "vdf.fetchone.fm.tw", "PX-01", {"id": "PX-01", "name": "台股上市 OHLCV"})
    c = _fixture("VDF_FETCH_FN-01", "FINDATA", "vdf.fetchone.fd", "FN-01", {"id": "FN-01", "name": "損益表 · 單季"})
    d = _fixture("VDF_FETCH_GL-01", "MACRO", "vdf.fetchone.mrc", "GL-01", {"id": "GL-01"})
    bad = _fixture("x_bad", "NOPE", "vdf.x", "x", "x")
    try:
        INTAKE.validate_candidate(bad)
        rejected = False
    except ValueError as exc:
        rejected = "TYPE_OR_OWNER" in str(exc)
    valid = [INTAKE.validate_candidate(x) for x in (a, b, c, d)]
    chk("② 新型別候選過檢測(欄位 · 身分 · 版本規則照 v0114);不認得的型別照樣退件 TYPE_OR_OWNER", len(valid) == 4 and rejected)
    items, plan = INTAKE.candidate_items([a, b, c, d], "fixture:fetchone")
    by = {it["semantic_key"]: it for it in items}
    chk("③ 收件成列:US-L01 → MRC 地區 US · PX-01 → FM 地區 TW · FN-01 → FD 不帶地區 · GL-01 沒地區段 → GLB;全 READY",
        plan["ready"] == 4 and by["US-L01"]["kind"] == "MRC" and by["US-L01"]["region"] == "US" and by["PX-01"]["kind"] == "FM"
        and by["PX-01"]["region"] == "TW" and by["FN-01"]["kind"] == "FD" and "region" not in by["FN-01"] and by["GL-01"]["region"] == "GLB",
        (plan, {k: (v["kind"], v.get("region")) for k, v in by.items()}))
    chk("④ 地區碼對到既有號格式:<類>-<地區>-(MRC-US- · FM-TW-);FD 照一般格式",
        BASE.region_of("MRC", by["US-L01"]) == "US" and str(BASE.prefix_of("FM", by["PX-01"])) == "FM-TW-" if hasattr(BASE, "prefix_of") else
        BASE.region_of("MRC", by["US-L01"]) == "US" and BASE.region_of("FM", by["PX-01"]) == "TW")
    text = Path(__file__).read_text(encoding="utf-8")
    body = text.split("def _fixture", 1)[0]
    chk("⑤ 加速器橋 · 網路橋在 · 不碰 TA-Lib · 本檔不寫任何檔", "[VIA:ACCEL-BRIDGE" in text and "[VIA:NET-BRIDGE" in text
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M) and ".write_text(" not in body and "open(" not in body)
    rc_prior = 0
    if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") != "1":
        keep = (BASE.ENGINE, INTAKE.candidate_items)
        BASE.ENGINE, INTAKE.candidate_items = PRIOR.ENGINE, _CAND_V0114
        for k in NEW_TYPES:
            INTAKE.TYPE_KIND.pop(k, None)
        try:
            rc_prior = PRIOR.selftest()
        finally:
            BASE.ENGINE, INTAKE.candidate_items = keep
            INTAKE.TYPE_KIND.update(NEW_TYPES)
        chk("⑥ 前版鏈 v0120 → … 自測 rc 0(暫時拿掉本版補丁跑);跑完新型別與收件補丁都補回",
            rc_prior == 0 and BASE.ENGINE == ENGINE and INTAKE.candidate_items is candidate_items and all(k in INTAKE.TYPE_KIND for k in NEW_TYPES), f"rc {rc_prior}")
    print(f"  [計] {ENGINE} 本版 {sum(ok)}/{len(ok)} · 前版鏈 {'PASS' if rc_prior == 0 else 'FAIL'} · 合計 {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
