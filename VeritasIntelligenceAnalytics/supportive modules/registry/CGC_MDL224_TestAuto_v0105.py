#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL224_TestAuto v0105 — 薄尾:PS 入口不只一支(Step1 同步 · LKGC 一次貼也有站)· PS 站驗它自己那支檔

實測(2026-10-03 交接 handoff test chain rc 1):main 的盤點冊 v0135 登了 coverage.ps.step1_sync_lkgc → 站 P-step1,
v0101 自測 ⑧「新 0 · 缺 0」報 GONE ps:step1_sync_lkgc —— 本體 discover() 的 PS 入口寫死只有 operator_console 一支,
冊上的第二支永遠被當「已不在」。再往下:run() 的 PS 站一律拿 operator_console 那支檔去對 must,
P-step1 就算進得了串測,驗的也是主控台,不是 Step1。本版三件(v0101–v0104 一字不動,換裝進本體模組):
  ① discover():PS 入口照 PS_ENTRIES_V0105 逐支找(有版號取最新 -vNNNN;只有無版號那支才認它);
     沒有的照舊不列(冊上有、樹上沒有 = GONE,照實)。
  ② ps_check():同一組 must 對回盤點冊上那一個 PS 站,驗那站 deps 指的檔(取最新版);對不回 → 照前版(主控台)。
  ③ items_now():紀錄冊也記每支 PS 入口的版本 + sha16(前版只記主控台)。
case:github_panorama 那一格是交接冊少了案,不是本支的事(交接冊補案)。只收 VCGC 呼叫;零網路;不碰 TA-Lib。
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
import json
import os
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = Path(__file__).stem
_STEM = "CGC_MDL224_TestAuto"
PS_ENTRIES_V0105 = {
    "operator_console": "Invoke-VIA-OperatorConsole-v*.ps1",
    "step1_sync_lkgc": "Invoke-VIA-Step1-SyncAndLKGC*.ps1",
}


def _vnum_v0105(path) -> int:
    m = re.search(r"[-_]v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0105(p) < _vnum_v0105(__file__)), key=_vnum_v0105)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + ENGINE, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)          # v0104:交接案站並行
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BODY = PRIOR.BODY
_DISCOVER_V0101 = BODY.discover
_PS_CHECK_V0101 = BODY.ps_check
_ITEMS_V0101 = BODY.items_now


def __getattr__(name: str):
    return getattr(PRIOR, name)


def pick_ps_v0105(via: Path, pattern: str) -> Path | None:
    """有版號 → 最新 -vNNNN;沒有任何版號檔才認無版號那支;都沒有 = None。"""
    hits = [p for p in Path(via).glob(pattern) if p.is_file()]
    versioned = [p for p in hits if _vnum_v0105(p) >= 0]
    if versioned:
        return max(versioned, key=_vnum_v0105)
    return hits[0] if len(hits) == 1 else None


def discover(via: Path = BODY.VIA) -> dict:
    found = _DISCOVER_V0101(via)
    ps = {}
    for key, pattern in PS_ENTRIES_V0105.items():
        p = pick_ps_v0105(via, pattern)
        if p is not None:
            ps[key] = p.name
    if not ps.get("operator_console"):
        ps["operator_console"] = (found.get("ps") or {}).get("operator_console", "")   # 主控台照前版(空字串也照留,前版的 ABSENT 判法不變)
    found["ps"] = ps
    return found


def ps_check(via: Path, rel: str, must: list) -> dict:
    _, inv = BODY.load_inventory(via)
    st = next((s for s in (inv or {}).get("stations") or [] if s.get("kind") == "ps" and list(s.get("must") or []) == list(must or [])), None)
    if st and st.get("deps"):
        dep = st["deps"][0]
        p = pick_ps_v0105(via, dep if "*" in dep else dep[:-4] + "*.ps1")   # 冊寫死檔名也認它的新版號檔
        if p is not None:
            rel = p.name
    return _PS_CHECK_V0101(via, rel, must)


def items_now(via: Path, found: dict) -> dict:
    out = _ITEMS_V0101(via, found)
    for key, name in (found.get("ps") or {}).items():
        if name and key != "operator_console" and (Path(via) / name).is_file():
            v = _vnum_v0105(name)
            out["ps:" + key] = {"kind": "ps", "file": name, "version": "v%04d" % v if v >= 0 else "", "sha16": BODY.sha16(Path(via) / name)}
    return out


BODY.discover = discover                                  # 本體 run · selftest ⑧ · main 經模組全域 discover → 走本版
BODY.ps_check = ps_check
BODY.items_now = items_now


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        return selftest()
    return PRIOR.main(args)


def selftest() -> int:
    print(f"=== {ENGINE} · 薄尾自測(PS 入口多支 · PS 站驗自己的檔)===")
    rc = PRIOR.selftest()
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    chk("① 前版鏈自測過(v0104 → … → v0101 實樹 ⑧ 新 0 · 缺 0);本版換裝還在",
        rc == 0 and BODY.discover is discover and BODY.ps_check is ps_check and BODY.items_now is items_now, f"rc {rc}")
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        (t / "Invoke-VIA-Step1-SyncAndLKGC.ps1").write_text("old\n", encoding="utf-8")
        only_plain = pick_ps_v0105(t, PS_ENTRIES_V0105["step1_sync_lkgc"])
        for n, body in (("Invoke-VIA-Step1-SyncAndLKGC-v0101.ps1", "# CELERITAS-TEMPLATE-JOIN v1\n# ===== [VIA:PS-ACCEL:v0101] x\n"),
                        ("Invoke-VIA-OperatorConsole-v0110.ps1", "@(\"test\"\n")):
            (t / n).write_text(body, encoding="utf-8")
        newest = pick_ps_v0105(t, PS_ENTRIES_V0105["step1_sync_lkgc"])
        none = pick_ps_v0105(t, "Invoke-VIA-Nothing*.ps1")
    chk("② 挑檔:只有無版號 → 認它 · 有 -vNNNN → 取最新版號 · 沒有 → None",
        only_plain is not None and only_plain.name == "Invoke-VIA-Step1-SyncAndLKGC.ps1"
        and newest is not None and newest.name.endswith("-v0101.ps1") and none is None)
    via = BODY.VIA
    found = discover(via)
    ps = found.get("ps") or {}
    chk("③ 實樹 discover:PS 入口兩支都找到(主控台 · Step1),Step1 取有版號那支", ps.get("operator_console", "").startswith("Invoke-VIA-OperatorConsole-v")
        and ps.get("step1_sync_lkgc", "").startswith("Invoke-VIA-Step1-SyncAndLKGC"), ps)
    _, inv = BODY.load_inventory(via)
    st = next((s for s in (inv or {}).get("stations") or [] if s.get("id") == "P-step1"), {})
    res = ps_check(via, ps.get("operator_console", ""), st.get("must") or [])
    chk("④ 實樹 P-step1 驗的是 Step1 自己那支(不是主控台):兩章在 → 不是 RED(沒 pwsh 照實黃)",
        bool(st) and res["lamp"] in ("GREEN", "YELLOW") and "少了" not in res["last"], res["last"][:90])
    items = items_now(via, found)
    chk("⑤ 紀錄冊項:主控台照前版 · Step1 另記檔名 + 版本 + sha16",
        "ps:operator_console" in items and len((items.get("ps:step1_sync_lkgc") or {}).get("sha16", "")) == 16, items.get("ps:step1_sync_lkgc"))
    src_text = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 加速器橋 · 網路橋在 · 不碰 TA-Lib · 只收 VCGC", "[VIA:ACCEL-BRIDGE" in src_text and "[VIA:NET-BRIDGE" in src_text
        and not re.search(r"^\s*(import|from)\s+talib", src_text, re.M))
    print(f"  [{ENGINE}] 薄尾 {sum(ok)}/{len(ok)} {'PASS' if all(ok) and rc == 0 else 'FAIL'}")
    return 0 if rc == 0 and all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
