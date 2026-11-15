#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VDF_SSOTSync v0102 — 薄尾:VDF 夾下 SSOT/ 子夾的冊也申請中央號(冊號;操作員令 2026-11-14「SSOT 子夾四本也發號」)。

v0100 只掃 VDF 夾第一層的 VDF_*_v####.json;PR 631 收進的 SSOT/ 子夾冊(VDF_Regex_SSOT · VDF_Synonym_SSOT ·
VDF_Workflow_SSOT · VDF_Config_TESTOVERLAY)與更早就在子夾的 VDF_Config 都沒登記、沒中央號。
本版在 v0101(v0100 + 擷取總冊 390 項)之後,多收 SSOT/ 子夾每個冊家族的尾版一條「冊」條目:
  鍵 VDF:SSOT:<家族>(跟第一層同名時改用 VDF:SSOT:SSOT.<家族>,不撞)· 指紋 = 冊內容 · 來源 SSOT/<檔名> · 型別照 v0100(SSOT / 名含 Rule 為 CFG)。
只登冊本身,不逐條登冊內的正則 / 同義字(VDF_Regex_SSOT 是 VCGC 正本的 VDF 自有副本,內 167 條不另發號)。
其餘照 v0101 / v0100:只寫 VDF 自己的登記冊與申請檔;號只由 VCGC 中央編號發;零網路;不碰 TA-Lib。
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

import importlib.util
import json
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_SSOTSync"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
SUBDIRS = ("SSOT",)


def _vnum_v0102(p) -> int:
    m = re.search(r"_v(\d{4})\.py$", str(p))
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0102(p) < _vnum_v0102(__file__)), key=_vnum_v0102)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
P1 = importlib.util.module_from_spec(_spec)                # v0101(薄尾)
sys.modules[_spec.name] = P1
_spec.loader.exec_module(P1)
BASE = P1.PRIOR                                            # v0100 本體(sync / register / request 都在這)
_HARVEST_V0101 = P1.harvest


def __getattr__(name):
    """尾版律 TAILAPI:前版公開名稱經本檔轉接(先 v0101 再 v0100)。"""
    for mod in (P1, BASE):
        if hasattr(mod, name):
            return getattr(mod, name)
    raise AttributeError(f"{TAG}:前版鏈沒有 {name}")


def subdir_books(vdf: Path = HERE, taken=()) -> dict:
    """SSOT/ 子夾每個冊家族的尾版 → 一條冊條目(只登冊,不逐條登冊內項)。"""
    out = {}
    for sub in SUBDIRS:
        for p in BASE._tails(list((vdf / sub).glob("VDF_*_v[0-9][0-9][0-9][0-9].json"))):
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                BASE.SKIPPED.append("%s/%s(%s)" % (sub, p.name, type(exc).__name__))
                continue
            fam = re.sub(r"_v\d{4}$", "", p.stem)
            kind = "CFG" if "Rule" in fam else "SSOT"
            key = "VDF:%s:%s" % (BASE.SHORT[kind], fam)
            if key in taken or key in out:
                key = "VDF:%s:%s.%s" % (BASE.SHORT[kind], sub, fam)
            out[key] = {"kind": kind, "key": key, "fp": BASE._sha16(BASE._canon(d)), "version": p.stem[-5:], "src": ["%s/%s" % (sub, p.name)],
                        "content": {"family": fam}, "note": "%s 子夾冊" % sub}
    return out


def harvest(vdf: Path = HERE) -> dict:
    items = _HARVEST_V0101(vdf)
    for k, e in subdir_books(vdf, taken=set(items)).items():
        items.setdefault(k, e)
    return items


BASE.harvest = harvest                                     # v0100 register() 依模組全域名找 harvest → 本版接手


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["--selftest"]:
        return selftest()
    return BASE.main(a)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:300]) if note and not cond else ''}", flush=True)

    print(f"=== {TAG} · 薄尾自測(SSOT/ 子夾冊也申請中央號)===", flush=True)
    real = subdir_books(HERE, taken=set())
    fams = sorted(e["content"]["family"] for e in real.values())
    chk("① 真倉 SSOT/ 子夾:五個冊家族各一條(TESTOVERLAY 取尾版 v0102)· 只登冊 · %s" % fams,
        {"VDF_Regex_SSOT", "VDF_Synonym_SSOT", "VDF_Workflow_SSOT", "VDF_Config_TESTOVERLAY"} <= set(fams)
        and all(e["kind"] in ("SSOT", "CFG") for e in real.values())
        and real.get("VDF:SSOT:VDF_Config_TESTOVERLAY", {}).get("version") == "v0102", real.keys())
    with tempfile.TemporaryDirectory(prefix="vdfsync_v0102_") as td:
        d = Path(td)
        (d / "SSOT").mkdir()
        (d / "VDF_Same_SSOT_v0100.json").write_text('{"top": 1}', encoding="utf-8")
        (d / "SSOT" / "VDF_Same_SSOT_v0100.json").write_text('{"sub": 1}', encoding="utf-8")
        (d / "SSOT" / "VDF_Demo_SSOT_v0100.json").write_text('{"a": 1}', encoding="utf-8")
        (d / "SSOT" / "VDF_Demo_SSOT_v0101.json").write_text('{"a": 2, "rx": "^[0-9]{4}$"}', encoding="utf-8")
        it = harvest(d)
        chk("② 子夾同家族取尾版 v0101 · 跟第一層同名改鍵不撞 · 子夾冊不逐條登內部正則",
            it["VDF:SSOT:VDF_Demo_SSOT"]["version"] == "v0101" and it["VDF:SSOT:VDF_Demo_SSOT"]["src"] == ["SSOT/VDF_Demo_SSOT_v0101.json"]
            and "VDF:SSOT:SSOT.VDF_Same_SSOT" in it and it["VDF:SSOT:VDF_Same_SSOT"]["src"] == ["VDF_Same_SSOT_v0100.json"]
            and not any(k.startswith("VDF:RGX:VDF_Demo_SSOT") for k in it), sorted(it))
        r = BASE.register(d)
        book = json.loads((d / "registry" / r["register"]).read_text(encoding="utf-8"))
        e1 = book["entries"]["VDF:SSOT:VDF_Demo_SSOT"]
        r2 = BASE.register(d)
        a = BASE.build_asset(dict(e1, semver="1.0.0", supersedes=None))
        chk("③ 登記冊(夾具):子夾冊暫編 · 待 VCGC 核號;申請列照 v0100 冊型(SSOT · 中央號欄空白);內容沒變再登記不出新版",
            "待 VCGC 核號" in e1["status"] and e1["vcgc_kind"] == BASE.VCGC_KIND["SSOT"] and a["asset_type"] == BASE.ASSET_TYPE["SSOT"]
            and a["ssot_code"] is None and a["semantic_key"] == "VDF_Demo_SSOT" and r2["written"] is False, (e1, r2))
    chk("④ 接手鏈:v0100 的 harvest 指到本版 · v0101 擷取總冊照收(390)", BASE.harvest is harvest and len(P1.fetchone_entries(HERE)) == 390)
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    chk("⑤ 加速器橋 · 網路工具橋在;本檔不另寫檔;零網路;不碰 TA-Lib",
        "[VIA:ACCEL-BRIDGE" in src and "[VIA:NET-BRIDGE" in src and ".write_text(" not in body and not re.search(r"^\s*(import|from)\s+talib", src, re.M))
    print("  前版鏈 %s selftest ↓" % PRIOR_PATH.name, flush=True)
    keep = BASE.harvest
    BASE.harvest = _HARVEST_V0101
    try:
        prior_rc = P1.selftest()
    finally:
        BASE.harvest = keep
    chk("⑥ 前版鏈 v0101 → v0100 自測照過", prior_rc == 0, prior_rc)
    good = all(ok)
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · 合計 {'PASS' if good else 'FAIL'}", flush=True)
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())
