#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL237_NumberingSystem v0116 — 薄尾:中央編號的可選依賴(pydantic · duckdb · re2 · polars · pandera)缺件不崩

導入 PR #439(2026-10-03,VCGC-REQ139)後實測:容器 / CI 直譯器沒有 pydantic,`--apply --scope` 一進 collect() 就在
v0112 validate_definition 的 `from pydantic import …` ModuleNotFoundError —— 中央編號(全樹發號的唯一寫手)整支停擺;
`--selftest` 也在 v0115 clean_managed 的 `import re2` 崩。中央發號不能因為可選套件不在就停。本版只換三格(v0111–v0115 一字不動):
  ① v0112 validate_definition:pydantic 在 → 照 v0112(strict · extra=forbid);不在 → 標準庫同規則嚴格驗(五鍵皆 str 且非空 ·
     library == POLARS · stable_id == 'VQG.IND.' + id.upper()),不合一樣 ValueError('INVALID_INDICATOR_IDENTITY')。
  ② v0114 regex_check:duckdb 在 → 照 v0114;不在 → 回 'REGEX_PROOF_ENGINE_ABSENT'(該 Regex 候選留 REVIEW、不發號;不拿 re 冒充證明)。
  ③ v0115 clean_managed(manager sync --input 的 L1 清洗):要 re2 + L1 三件(polars · pydantic · pandera)+ ahocorasick;
     缺 → ValueError('ABSENT_PACKAGES: …'),manager 照 v0115 印 BLOCKED + 缺件(不代裝)。
自測:先跑 v0111 核心鏈(交接案 numbering 的標記在那裡);可選套件全齊才跑 v0115 的 28 項,否則照實「略過 + 列缺件」並驗 ①②③ 的缺件路徑。
只收 VCGC 呼叫;零網路;不碰 TA-Lib。
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

import contextlib
import importlib.util
import io
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL237_NumberingSystem"
ENGINE = Path(__file__).stem
OPTIONAL_V0116 = ("pydantic", "duckdb", "re2", "polars", "pandera", "ahocorasick", "flashtext", "rapidfuzz")
CLEAN_NEEDS_V0116 = ("re2", "polars", "pydantic", "pandera", "ahocorasick")
IND_KEYS_V0116 = ("id", "stable_id", "family", "source_identity", "library")


def _vnum_v0116(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


def _load_v0116(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0116(p) < _vnum_v0116(__file__)), key=_vnum_v0116)
PRIOR = _load_v0116(PRIOR_PATH, _STEM + "_prior_for_" + ENGINE)        # v0115:單一 SSOT 管理引擎
BASE = PRIOR.BASE


def _chain_v0116() -> dict:
    """{版號: 模組}:沿 PRIOR 往回走(v0115 → v0114 → … → v0111 …)。"""
    out, m, seen = {}, PRIOR, set()
    while m is not None and id(m) not in seen:
        seen.add(id(m))
        f = getattr(m, "__file__", "") or ""
        if _vnum_v0116(f) >= 0:
            out[_vnum_v0116(f)] = m
        nxt = vars(m).get("PRIOR")
        m = nxt if isinstance(nxt, type(sys)) else None    # 有的版把 PRIOR 寫成路徑:鏈到此為止
    return out


CHAIN_V0116 = _chain_v0116()
M112, M114, M111 = CHAIN_V0116.get(112), CHAIN_V0116.get(114), CHAIN_V0116.get(111)
_VALIDATE_V0112 = M112.validate_definition
_REGEX_CHECK_V0114 = M114.regex_check
_CLEAN_V0115 = PRIOR.clean_managed


def __getattr__(name):
    return getattr(PRIOR, name)


def missing_v0116(mods) -> list:
    return [m for m in dict.fromkeys(mods) if importlib.util.find_spec(m) is None]


def validate_definition(row):
    if not missing_v0116(["pydantic"]):
        return _VALIDATE_V0112(row)
    if not isinstance(row, dict) or any(k not in row for k in IND_KEYS_V0116):
        raise ValueError("INVALID_INDICATOR_IDENTITY")
    result = {k: row[k] for k in IND_KEYS_V0116}
    if not all(isinstance(v, str) and v for v in result.values()) or result["library"] != "POLARS" \
            or result["stable_id"] != "VQG.IND." + result["id"].upper():
        raise ValueError("INVALID_INDICATOR_IDENTITY")
    return result


def regex_check(row):
    if missing_v0116(["duckdb"]):
        return "REGEX_PROOF_ENGINE_ABSENT"
    return _REGEX_CHECK_V0114(row)


def clean_managed(records, catalog, owner):
    miss = missing_v0116(CLEAN_NEEDS_V0116)
    if miss:
        raise ValueError("ABSENT_PACKAGES: " + ",".join(miss) + "(L1 清洗要的套件不在本直譯器;不代裝)")
    return _CLEAN_V0115(records, catalog, owner)


M112.validate_definition = validate_definition          # v0112 / v0113 indicator_items 經模組全域取 → 走本版
M114.regex_check = regex_check                          # v0114 make_plan 與 v0115 make_plan(PRIOR.regex_check)都經這一格
PRIOR.clean_managed = clean_managed                     # v0115 manage() 經模組全域取


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    return PRIOR.main(args)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    rc111 = M111.selftest()                             # 核心鏈(交接案 numbering / numbering_dup_r34 的標記在這裡)
    miss = missing_v0116(OPTIONAL_V0116 + tuple(sorted(set(PRIOR.l1().TOOL_MODULES.values()))))
    print(f"=== {ENGINE} · 薄尾自測(可選依賴缺件不崩)===")
    chk("① v0111 核心鏈自測過(重號歸位 · 只增稽核 · 發號)", rc111 == 0, f"rc {rc111}")
    if miss:
        print(f"  [略過] v0112–v0115 自測要可選套件;本直譯器缺 {len(miss)} 件:{' · '.join(miss)} → 照實略過(不算過、不算錯)")
    else:
        rc115 = PRIOR.selftest()
        chk("② v0115 單一管理引擎 28 項自測過(套件齊)", rc115 == 0, f"rc {rc115}")
    good = {"id": "rsi_14", "stable_id": "VQG.IND.RSI_14", "family": "momentum", "source_identity": "fixture:A", "library": "POLARS"}
    bad = [dict(good, library="PANDAS"), dict(good, stable_id="VQG.IND.rsi_14"), dict(good, family=""),
           {k: v for k, v in good.items() if k != "family"}, dict(good, id=14)]
    real = importlib.util.find_spec
    try:
        importlib.util.find_spec = lambda name, *a, **k: None if name in ("pydantic", "duckdb", "re2") else real(name, *a, **k)
        rej = 0
        for b in bad:
            try:
                validate_definition(b)
            except (ValueError, AttributeError):
                rej += 1
        acc = validate_definition(good) == {k: good[k] for k in IND_KEYS_V0116}
        rx = regex_check({"value": r"^[1-9][0-9]{3}\.TW$", "positive": ["2330.TW"], "negative": ["x"]})
        try:
            clean_managed([], {"rules": [], "holds": [], "rules_sha256": ""}, "VDF")
            absent = ""
        except ValueError as e:
            absent = str(e)
    finally:
        importlib.util.find_spec = real
    chk("③ 缺 pydantic:標準庫同規則嚴格驗(合格照收;library / stable_id / 空值 / 缺鍵 / 非字串 五種全擋)", acc and rej == len(bad), (acc, rej))
    if not missing_v0116(["pydantic"]):
        same = all((lambda r: (r[0] == r[1]))((_safe_v0116(_VALIDATE_V0112, x), _safe_v0116(validate_definition, x))) for x in [good] + bad)
        chk("③b pydantic 在時兩把尺判法一致", same)
    chk("④ 缺 duckdb:Regex 候選回 REGEX_PROOF_ENGINE_ABSENT(留 REVIEW 不發號,不拿 re 冒充)", rx == "REGEX_PROOF_ENGINE_ABSENT", rx)
    chk("⑤ 缺 re2 等:L1 清洗回 ABSENT_PACKAGES 點名缺件(manager 印 BLOCKED,不崩)", absent.startswith("ABSENT_PACKAGES") and "re2" in absent, absent[:80])
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rows, notes = BASE.collect()
    ind = [r for r in rows if str(r.get("cat", "")).startswith("VQG/Indicator/")]
    chk("⑥ 真樹 collect():本直譯器照樣收齊(含 VQG 指標候選 · 不因可選套件停擺)", len(rows) > 1000 and len(ind) > 0, f"列 {len(rows)} · 指標 {len(ind)}")
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑦ 加速器橋 · 網路橋在 · 不碰 TA-Lib · 換裝在位", "[VIA:ACCEL-BRIDGE" in text and "[VIA:NET-BRIDGE" in text
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M) and M112.validate_definition is validate_definition
        and M114.regex_check is regex_check and PRIOR.clean_managed is clean_managed)
    print(f"  [計] {ENGINE} 本版 {sum(ok)}/{len(ok)} · v0111 {'PASS' if rc111 == 0 else 'FAIL'} · v0112–v0115 {'略過(缺件)' if miss else '已跑'} · 合計 {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


def _safe_v0116(fn, x):
    try:
        return fn(x)
    except Exception as e:                               # 兩把尺都拒 = 判法一致;回例外類別比對
        return type(e).__name__


if __name__ == "__main__":
    sys.exit(main())
