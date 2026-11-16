#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VDF_SSOTSync v0101 — v0100 薄尾(v0100 一字不動):同義字收割看穿薄尾,尾版是薄尾就往前版本體收 UNIFIED_ALIAS。

實錄(2026-11-13 容器 VDF_SystemManager v0171 test --max 200:VDF_SSOTSync FAIL rc 1):自測 ① 實樹沒掃到任何 SYN(同義字)。
根因:v0100 只讀「家族尾版」原文裡的 UNIFIED_ALIAS 字面字典;VDF_ENG053_ParamEngineMap 的尾版今天換成 v0103 薄尾
  (本輪修 ENG053 ⑦ 出的,只換一支函式),字典留在前版 v0102 本體 → 收不到 → 同義字整批消失(本輪自己造成的回歸)。
  同型:ENG053 v0103 的車道源碼實證也是「只看尾版原文 → 看不到薄尾載入的前版本體」。
本版只換 harvest:先照 v0100 收;再把「原文沒有 UNIFIED_ALIAS 的薄尾」(檔內 PRIOR_PATH + spec_from_file_location 載前版)
  沿同夾同家族往前找,第一個帶 UNIFIED_ALIAS 字面字典的本體照 v0100 同一格式補收(來源記本體檔名,與換薄尾前完全一樣)。
  任何引擎以後出薄尾都不會再掉同義字。register / request / apply / sync 全照 v0100(它們都經 harvest)。
VDF 自己的模組;零網路 · 不寫他系統 · 號只由 VCGC 中央發 · 不用 TA-Lib · 不寫同意閘。用法同 v0100。
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

import ast
import contextlib
import importlib.util
import io
import re
import sys
import tempfile
from pathlib import Path

VERSION = "v0101"
HERE = Path(__file__).resolve().parent
_STEM = "VDF_SSOTSync"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
_HARVEST_V0100 = PRIOR.harvest
_TAIL_RX = re.compile(r"PRIOR_PATH\s*=.*?spec_from_file_location", re.S)
_FAM_RX = re.compile(r"^(.*)_v(\d{4})$")


def __getattr__(name):
    return getattr(PRIOR, name)


def is_thin_tail(src: str) -> bool:
    return bool(_TAIL_RX.search(src))


def _alias_dict(src: str):
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "UNIFIED_ALIAS" for t in n.targets) and isinstance(n.value, ast.Dict):
            try:
                return ast.literal_eval(n.value)
            except ValueError:
                return None
    return None


def body_alias(tail: Path):
    """薄尾 → 沿同夾同家族往前找第一個帶 UNIFIED_ALIAS 的本體;回 (本體路徑, dict) 或 (None, None)。"""
    m = _FAM_RX.match(tail.stem)
    if not m:
        return None, None
    fam, me = m.group(1), int(m.group(2))
    chain = sorted((p for p in tail.parent.glob(fam + "_v*.py") if _FAM_RX.match(p.stem) and _FAM_RX.match(p.stem).group(1) == fam
                    and int(_FAM_RX.match(p.stem).group(2)) < me), key=_vnum, reverse=True)
    for q in chain:
        src = q.read_text(encoding="utf-8", errors="replace")
        if "UNIFIED_ALIAS" in src:
            d = _alias_dict(src)
            return (q, d) if d else (None, None)
        if not is_thin_tail(src):
            break
    return None, None


def harvest(vdf: Path = HERE) -> dict:
    items = _HARVEST_V0100(vdf)
    pys = PRIOR._tails([p for p in list(Path(vdf).glob("VDF_*_v[0-9][0-9][0-9][0-9].py"))
                        + list((Path(vdf) / "engine").glob("VDF_*_v[0-9][0-9][0-9][0-9].py"))])
    for p in pys:
        src = p.read_text(encoding="utf-8", errors="replace")
        if "UNIFIED_ALIAS" in src or not is_thin_tail(src):
            continue
        body, alias = body_alias(p)
        if not alias:
            continue
        for a, c in sorted(alias.items()):
            key = "VDF:SYN:%s" % a
            it = items.setdefault(key, {"kind": "SYN", "key": key, "fp": PRIOR._sha16("%s=%s" % (a, c)), "version": None,
                                        "src": [], "content": {"alias": a, "canonical": c}, "note": ""})
            if body.name not in it["src"]:
                it["src"].append(body.name)
    return items


PRIOR.harvest = harvest            # v0100 的 register / request / apply / sync / selftest 用模組全域名 → 換成本版


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""), flush=True)

    print("=== %s %s · 薄尾自測(同義字收割看穿薄尾;其餘照 v0100)===" % (_STEM, VERSION), flush=True)
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        (d / "engine").mkdir()
        (d / "engine" / "VDF_ENG900_X_v0101.py").write_text("UNIFIED_ALIAS = {'ZZ_ALIAS': 'zz.canon'}\n", encoding="utf-8")
        (d / "engine" / "VDF_ENG900_X_v0102.py").write_text(
            "PRIOR_PATH = max(HERE.glob('VDF_ENG900_X_v*.py'))\n_spec = importlib.util.spec_from_file_location('p', PRIOR_PATH)\n", encoding="utf-8")
        (d / "engine" / "VDF_ENG901_Y_v0101.py").write_text("UNIFIED_ALIAS = {'YY_OLD': 'yy.canon'}\n", encoding="utf-8")
        (d / "engine" / "VDF_ENG901_Y_v0102.py").write_text("X = 1  # 完整本體,不是薄尾\n", encoding="utf-8")
        old = _HARVEST_V0100(d)
        new = harvest(d)
    chk("① 重現:v0100 只看尾版 → 薄尾的前版字典收不到", "VDF:SYN:ZZ_ALIAS" not in old)
    chk("② 本版:薄尾 → 往前版本體補收 · 來源記本體檔名", new.get("VDF:SYN:ZZ_ALIAS", {}).get("content", {}).get("canonical") == "zz.canon"
        and new["VDF:SYN:ZZ_ALIAS"]["src"] == ["VDF_ENG900_X_v0101.py"])
    chk("③ 完整本體(不是薄尾)不往回看舊版", "VDF:SYN:YY_OLD" not in new)
    real = harvest(HERE)
    syn = {k: v for k, v in real.items() if v["kind"] == "SYN"}
    chk("④ 實樹:同義字回來了 · START_DATE → time.start_date", bool(syn) and real.get("VDF:SYN:START_DATE", {}).get("content", {}).get("canonical") == "time.start_date",
        "SYN %d" % len(syn))
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = PRIOR.selftest()
    print(buf.getvalue(), end="")
    chk("⑤ v0100 自測(原本只紅 ① 沒有 SYN)換裝後全過", rc == 0, "rc %s" % rc)
    chk("⑥ 換裝:v0100 的 harvest 指本版", PRIOR.harvest is harvest)
    n = sum(ok)
    print("[計] %s %s 薄尾 %d/%d · %s" % (_STEM, VERSION, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    return 0 if n == len(ok) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["--selftest"]:
        return selftest()
    return PRIOR.main(a)


if __name__ == "__main__":
    sys.exit(main())
