#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
VDF_ENG053_ParamEngineMap v0103 — v0102 薄尾(v0102 一字不動):車道→引擎的「源碼實證」要看穿薄尾,看到它載入的前版本體。

實錄(2026-11-13 容器全量重跑 VDF_SystemManager v0171 test:VDF_ENG053 FAIL rc 1):十一檢只紅 ⑦(未映 READY 1 = cnyes_consensus)。
根因:在役面只收家族尾版(對);ENG050_OrderFetch 尾版 v0102 是薄尾,只換 fetch_twse_lane,
  'cnyes_consensus' 這個字面在它載入的前版 v0101 本體裡 → 只掃尾版原文就找不到 → 誤判「沒有引擎接這條車道」。
  不是車道沒人接,是掃描看不穿薄尾(同型:ENG089 v0109 薄尾漏帶 CATALOG)。
本版只換 derive_string_consumers:尾版若是薄尾(檔內有 PRIOR_PATH + spec_from_file_location 載前版),
  就把同夾同家族、版號比它小的檔一併當成它的原文來比對;命中照記在尾版名下(在役面不變、舊版不入工作面)。
  不是薄尾 → 照 v0102 只看自己。字面比對規則(前綴收斂)一字照 v0102。
VDF 自己的引擎;唯讀 · 零網路 · 零寫庫 · 不用 TA-Lib · 不寫同意閘。用法同 v0102:run | --selftest
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)。本版不出網。"""
    return None if VIA_NET_TOOL_PATH is None else VIA_NET_TOOL_PATH
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import re
import sys
import tempfile
from pathlib import Path

VERSION = "0103"
HERE = Path(__file__).resolve().parent
_STEM = "VDF_ENG053_ParamEngineMap"


def _vnum(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_v0103", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
_DERIVE_V0102 = PRIOR.derive_string_consumers

_TAIL_RX = re.compile(r"PRIOR_PATH\s*=.*?spec_from_file_location", re.S)
_FAM_RX = re.compile(r"^(.*)_v(\d{4})$")


def __getattr__(name: str):
    return getattr(PRIOR, name)


def is_thin_tail(src: str) -> bool:
    """薄尾 = 檔內用 PRIOR_PATH 找前版再 spec_from_file_location 載進來。"""
    return bool(_TAIL_RX.search(src))


def prior_chain(path: Path) -> list:
    """同夾同家族、版號比它小的檔(由新到舊)。不是版號檔 → 空。"""
    m = _FAM_RX.match(path.stem)
    if not m:
        return []
    fam, me = m.group(1), int(m.group(2))
    out = []
    for p in path.parent.glob(fam + "_v*.py"):
        mm = _FAM_RX.match(p.stem)
        if mm and mm.group(1) == fam and int(mm.group(2)) < me:
            out.append(p)
    return sorted(out, key=_vnum, reverse=True)


def source_with_chain(path: Path) -> str:
    """尾版原文;是薄尾就接上前版本體原文(一路往回,直到某版不是薄尾)。"""
    src = path.read_text(encoding="utf-8", errors="replace")
    parts = [src]
    cur = src
    for p in prior_chain(path):
        if not is_thin_tail(cur):
            break
        cur = p.read_text(encoding="utf-8", errors="replace")
        parts.append(cur)
    return "\n".join(parts)


def derive_string_consumers(engines: dict, tokens: list) -> dict:
    """同 v0102(前綴收斂 · 字面量含即中),只差在薄尾的原文 = 尾版 + 前版本體。"""
    srcs = {rel: source_with_chain(PRIOR.VDF / rel) for rel in engines}
    hits = {t: [] for t in tokens}
    for t in tokens:
        probes = [t]
        parts = t.split("_")
        while len(parts) > 1:
            parts = parts[:-1]
            probes.append("_".join(parts))
        for probe in probes:
            rx = re.compile(r"['\"][A-Za-z0-9_./-]*" + re.escape(probe) + r"[A-Za-z0-9_./-]*['\"]")
            got = [rel for rel, src in srcs.items() if rx.search(src)]
            if got:
                hits[t] = got
                break
    return hits


PRIOR.derive_string_consumers = derive_string_consumers   # v0102 build_map 用模組全域名 → 換成本版


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}", flush=True)

    print(f"=== VDF_ENG053 參數映射器 v{VERSION} · 薄尾自測(車道源碼實證看穿薄尾;其餘照 v0102)===", flush=True)
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        (d / "FAM_X_v0101.py").write_text("LANE = 'lane_only_in_body'\n", encoding="utf-8")
        (d / "FAM_X_v0102.py").write_text(
            "PRIOR_PATH = max(HERE.glob('FAM_X_v*.py'))\n_spec = importlib.util.spec_from_file_location('p', PRIOR_PATH)\n", encoding="utf-8")
        (d / "FAM_Y_v0101.py").write_text("LANE = 'zzoldonly'\n", encoding="utf-8")
        (d / "FAM_Y_v0102.py").write_text("X = 1  # 完整本體,不是薄尾\n", encoding="utf-8")
        old_vdf = PRIOR.VDF
        try:
            PRIOR.VDF = d
            eng = {"FAM_X_v0102.py": {}, "FAM_Y_v0102.py": {}}
            old = _DERIVE_V0102(eng, ["lane_only_in_body"])
            new = derive_string_consumers(eng, ["lane_only_in_body", "zzoldonly"])
        finally:
            PRIOR.VDF = old_vdf
        chk("① 重現:v0102 只看尾版原文 → 薄尾前版本體裡的車道字面找不到", old["lane_only_in_body"] == [], old)
        chk("② 本版:薄尾 → 接前版本體一起比 → 命中記在尾版名下", new["lane_only_in_body"] == ["FAM_X_v0102.py"], new["lane_only_in_body"])
        chk("③ 不是薄尾的完整本體 → 不往回看舊版(舊版不入工作面)", new["zzoldonly"] == [], new["zzoldonly"])
    real = PRIOR.VDF / "engine" / "VDF_ENG050_OrderFetch_v0102.py"
    if real.is_file():
        chk("④ 實檔:ENG050 v0102 是薄尾 · 接上前版後看得到 'cnyes_consensus'",
            is_thin_tail(real.read_text(encoding="utf-8")) and "'cnyes_consensus'" in source_with_chain(real).replace('"', "'"))
    print("  ── 前版 v0102 十一檢(換裝本版 derive_string_consumers 後)──", flush=True)
    rc = PRIOR.selftest()
    chk("⑤ v0102 十一檢(原本只紅 ⑦)換裝後全過", rc == 0, f"rc {rc}")
    chk("⑥ 換裝:v0102 模組的 derive_string_consumers 指本版", PRIOR.derive_string_consumers is derive_string_consumers)
    n = sum(ok)
    print(f"  [計] VDF_ENG053 v{VERSION} 薄尾 {n}/{len(ok)} · 合計 {'PASS' if n == len(ok) else 'FAIL'}", flush=True)
    return 0 if n == len(ok) else 1


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    return PRIOR.main()


if __name__ == "__main__":
    sys.exit(main())
