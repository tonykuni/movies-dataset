#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG053_ParamEngineMap v0103 — 薄尾:車道 → 引擎「源碼實證」沿薄尾前版鏈一起看。

VDF 啟動實測(2026-11-14 · 引擎啟動檢查)本支自測 ⑦ 紅:READY 車道 cnyes_consensus「未映」。
根因:v0101 起在役面只收各家族尾版;VDF_ENG050_OrderFetch 尾版 v0102 是薄尾(只修 TWSE 逐日錯誤記法,
`PRIOR = …` 載入 v0101),車道分派(含 cnyes_consensus)寫在 v0101 → 尾版原文沒有車道字面 → 誤判沒人接單。
本版(v0102 一字不動;只換 derive_string_consumers):
  · 引擎是薄尾(原文有 `PRIOR… = …` 且自己載前版)時,把它實際載入的前版鏈原文一起掃(一路往回到第一支非薄尾為止);
    非薄尾的整版重寫照舊只看自己(舊版有、新版拿掉的車道不會被算回來)。
  · 命中仍記在「尾版」那一列(映射冊的在役面不變)。
其餘(收割 · 四冊 · 治理五態 · 映射冊)照 v0102。唯讀收割零觸碰引擎原件;不碰 TA-Lib;零網路。
用法同 v0102:python VDF_ENG053_ParamEngineMap_v0103.py run | --selftest
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
STEM = "VDF_ENG053_ParamEngineMap"
VERSION = "v0103"
_VER_RX = re.compile(r"^(.*)_v(\d{4})$")
_THIN_RX = re.compile(r"^\s*PRIOR\w*\s*=\s*(?:importlib|max\()", re.M)


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})\.py$", str(p))
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(STEM + "_prior_for_" + VERSION, PRIOR_PATH)
P = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = P
_spec.loader.exec_module(P)
_DERIVE_V0102 = P.derive_string_consumers
# 別名表照 v0102 原文再宣告一次(字面字典):VDF_SSOTSync 只從家族尾版收割 UNIFIED_ALIAS(同義字中央號 VDF:SYN:*),
# 尾版沒有這張字面表 → 13 個同義字會被判退役。內容須與 v0102 一字不差(自測 ④ 核對)。
UNIFIED_ALIAS = {
    "START_DATE": "time.start_date", "END_DATE": "time.end_date",
    "BATCH_SIZE": "fetch.batch_size", "MAX_RETRIES": "fetch.max_retries",
    "RETRY_DELAY": "fetch.retry_delay_s", "RETRY_DELAY_S": "fetch.retry_delay_s",
    "TIMEOUT": "fetch.timeout_s", "TIMEOUT_S": "fetch.timeout_s",
    "HTTP_TIMEOUT": "fetch.timeout_s", "OUTPUT_DIR": "output.root",
    "OUTPUT_ROOT": "output.root", "CSV_ENCODING": "output.csv_encoding",
    "MARKETS": "markets",
}


def __getattr__(name):
    """尾版律 TAILAPI:前版公開名稱經本檔轉接。"""
    return getattr(P, name)


def is_thin(src: str) -> bool:
    """薄尾 = 自己載前版(模組層 `PRIOR… = importlib… / max(…)`)。"""
    return bool(_THIN_RX.search(src))


def chain_source(path: Path) -> str:
    """尾版原文 + 它實際載入的前版鏈原文(薄尾才往回;遇到非薄尾停)。"""
    path = Path(path)
    src = path.read_text(encoding="utf-8", errors="replace")
    m = _VER_RX.match(path.stem)
    if not m:
        return src
    fam, cur, cur_src = m.group(1), int(m.group(2)), src
    olders = sorted((q for q in path.parent.glob(fam + "_v*.py") if "_sha" not in q.name.lower() and 0 <= _vnum(q) < cur), key=_vnum, reverse=True)
    for q in olders:
        if not is_thin(cur_src):
            break
        cur_src = q.read_text(encoding="utf-8", errors="replace")
        src += "\n" + cur_src
    return src


def derive_string_consumers(engines: dict, tokens: list) -> dict:
    """同 v0102 的源碼實證(含前綴收斂後備),但每支引擎掃「尾版 + 薄尾前版鏈」原文;命中記在尾版列。"""
    srcs = {rel: chain_source(P.VDF / rel) for rel in engines}
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


P.derive_string_consumers = derive_string_consumers               # v0102 build_map 依模組全域名找 → 本版接手


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:300]) if note and not cond else ''}", flush=True)
    print(f"=== {STEM} {VERSION} · 薄尾自測(車道映通沿薄尾前版鏈)===", flush=True)
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        (d / "VDF_ENG900_Demo_v0100.py").write_text("LANES = {'demo_lane': 1}\n", encoding="utf-8")
        (d / "VDF_ENG900_Demo_v0101.py").write_text("PRIOR = importlib.util.module_from_spec(x)\n", encoding="utf-8")
        (d / "VDF_ENG901_Full_v0100.py").write_text("LANES = {'gone_lane': 1}\n", encoding="utf-8")
        (d / "VDF_ENG901_Full_v0101.py").write_text("LANES = {'new_lane': 1}\n", encoding="utf-8")
        thin_src, full_src = chain_source(d / "VDF_ENG900_Demo_v0101.py"), chain_source(d / "VDF_ENG901_Full_v0101.py")
        chk("① 薄尾往回併前版原文(demo_lane 看得到)· 整版重寫只看自己(舊版的 gone_lane 不算回來)",
            "'demo_lane'" in thin_src and "'gone_lane'" not in full_src and "'new_lane'" in full_src)
    m = P.build_map()
    ready = P._ready_lanes()
    un = [ln for ln in m["gaps"]["lanes_unmapped"] if ln in m["lane_engines"] and ln in ready]
    cn = m["lane_engines"].get("cnyes_consensus") or []
    chk("② 真倉:READY 車道零未映 · cnyes_consensus 映到 ENG050 尾版(v0102 薄尾 → v0101 分派)",
        not un and any("VDF_ENG050_OrderFetch_v0102" in h for h in cn), (un, cn))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("③ 加速器橋 · 網路工具橋在;不碰 TA-Lib;本檔不寫檔(映射冊照 v0102 run 寫)",
        "[VIA:ACCEL-BRIDGE" in src and "[VIA:NET-BRIDGE" in src and "import " + "talib" not in src
        and ".write_text(" not in src.split("def selftest", 1)[0])
    chk("④ 尾版別名表(字面字典)與 v0102 一字不差 · 13 個同義字照收割(VDF_SSOTSync 只看尾版)",
        UNIFIED_ALIAS == P.UNIFIED_ALIAS and len(UNIFIED_ALIAS) == 13 and "UNIFIED_ALIAS = {" in src)
    print(f"  前版 {PRIOR_PATH.name} selftest ↓(在役面映通用本版)", flush=True)
    prior_rc = P.selftest()
    chk("⑤ 前版 v0102 自測照過(含 ⑦ READY 車道零缺)", prior_rc == 0, prior_rc)
    print(f"[計] {STEM} {VERSION} 本版 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


def main() -> int:
    a = sys.argv[1:]
    if a[:1] == ["--selftest"]:
        return selftest()
    sys.argv = [sys.argv[0]] + a
    return P.main()


if __name__ == "__main__":
    sys.exit(main())
