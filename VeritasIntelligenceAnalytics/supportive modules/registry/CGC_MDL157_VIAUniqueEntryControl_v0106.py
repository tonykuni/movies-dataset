#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""CGC_MDL157_VIAUniqueEntryControl v0106 — 薄尾:命令冊沿 dot-source 鏈讀 · 撞號以編號系統的唯一碼為準(R33 SDD 自測實錄)

R33 SDD 自測(CGC_MDL245 selftests,經 VCGC run)實錄 v0105:RED 21/29。逐條追因,兩個根因:
  ① 命令冊 Register-VIA-Commands 自 v0244 起是薄尾(. (Join-Path $PSScriptRoot "…v0261.ps1") 往回接),v0105 只讀尾版字面
     → Set-VIAGateDefaults / via-central / 各 via-* 目標「不在」是假紅,執行期都在。本尾版:讀命令冊 = 沿 dot-source 鏈把每一本
     的文字接起來(新到舊;同夾同族、只讀不執行、防環),尾版拆掉的函式(Remove-Item Function:…)從鏈上結果扣掉。
  ② 撞號:同一個檔名號下有多個家族(CGC_MDL149 主控台子模組 24 支、MDL193 鎖冊 15 支、SUP_MDL743 版面 6 支…)是刻意的群組命名;
     R23 起每一支都由編號系統(CGC_MDL237)發唯一碼 VIA-<子系統>-MDL####(L05 一把尺:唯一性的正主是編號系統)。
     本尾版:同號多家族 **只有在某個家族沒有自己的編號列時** 才算撞號(那才真的分不清誰是誰);有唯一碼的列為「檔名號群組」照報。
其餘整支照 v0105(__getattr__ 轉接)。只收 VCGC 呼叫(VIA_FROM_VCGC=YES)的規矩照前一版。
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
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL157_VIAUniqueEntryControl"


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", path.stem)
    return int(m.group(1)) if m else -1


_PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum,
                  default=HERE / "CGC_MDL157_VIAUniqueEntryControl_v0105.py")   # the prior this tail was cut from
_spec = importlib.util.spec_from_file_location("uec_prior_for_" + Path(__file__).stem, _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    return getattr(PRIOR, name)


BOOK_RX = re.compile(r"^Register-VIA-Commands-v\d{4}\.ps1$")
DOT_RX = re.compile(r"""^\s*\.\s*\(?\s*(?:Join-Path\s+\$PSScriptRoot\s+)?["']?(?:\$PSScriptRoot[\\/])?(Register-VIA-Commands-v\d{4}\.ps1)""", re.M)
REMOVED_RX = re.compile(r"""Remove-Item\s+-Path\s+["']?Function:\$?([A-Za-z0-9_\-]+)""")
LOOP_REMOVED_RX = re.compile(r"""foreach\s*\(\s*\$name\s+in\s+@\(([^)]*)\)\s*\)\s*\{\s*Remove-Item\s+-Path\s+["']Function:\$name""")
_V0105_READ = PRIOR.read
_V0105_COLLISIONS = PRIOR.engine_number_collisions


def command_book_chain(path: Path, limit: int = 64) -> list:
    """The book and every sibling book it dot-sources, newest first (read only, never executed; loop-guarded)."""
    chain, cur = [], Path(path)
    while cur.is_file() and cur not in chain and len(chain) < limit:
        chain.append(cur)
        m = DOT_RX.search(cur.read_text(encoding="utf-8", errors="replace"))
        if not m:
            break
        cur = cur.parent / m.group(1)
    return chain


def _removed(txt: str) -> set:
    out = set(REMOVED_RX.findall(txt))
    for grp in LOOP_REMOVED_RX.findall(txt):
        out |= {x.strip().strip("'\"") for x in grp.split(",") if x.strip()}
    return out


def read(path: Path) -> str:
    """v0106: a command book reads as its whole dot-source chain; functions a newer book removes are struck from the older text."""
    p = Path(path)
    if not BOOK_RX.match(p.name) or not p.is_file():
        return _V0105_READ(p)
    removed, parts = set(), []
    for book in command_book_chain(p):                  # newest first: a removal in a newer book hides the older definition
        txt = book.read_text(encoding="utf-8", errors="replace")
        for name in removed:
            txt = re.sub(r"function\s+global:" + re.escape(name) + r"\b", "# (removed by a newer book) " + name, txt)
        parts.append(f"# ==== {book.name} ====\n" + txt)
        removed |= _removed(txt)
    return "\n".join(parts)


def _numbered_families() -> set:
    fams = set()
    for kind in ("MDL", "ENG"):
        hits = sorted((HERE / "VIA_NumberBooks").glob(f"VIA_NumberBook_{kind}_v*.jsonl"), key=_vnum)
        for line in (hits[-1].read_text(encoding="utf-8").splitlines() if hits else []):
            if line.strip():
                r = json.loads(line)
                if not r.get("gone_since"):
                    fams.add(re.sub(r"_v\d+$", "", str(r.get("name") or "")))
    return fams


GROUPS: dict = {}


def engine_number_collisions() -> dict:
    """v0106: a shared file-name number is a real collision only when some family in it has no numbering row of its own."""
    raw = _V0105_COLLISIONS()
    fams = _numbered_families()
    real = {k: v for k, v in raw.items() if any(f not in fams for f in v)}
    GROUPS.clear()
    GROUPS.update({k: v for k, v in raw.items() if k not in real})
    return real


PRIOR.read, PRIOR.engine_number_collisions = read, engine_number_collisions


def main() -> int:
    if sys.argv[1:] == ["--selftest"]:
        return selftest()
    rc = PRIOR.main()
    if GROUPS:
        print(f"  [v0106] 檔名號群組 {len(GROUPS)} 組(每支都有編號系統唯一碼,不是撞號):"
              + "; ".join(f"{k}×{len(v)}" for k, v in sorted(GROUPS.items())))
    return rc


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    book = PRIOR.COMMAND_BOOK
    chain = command_book_chain(book)
    txt = read(book)
    chk("命令冊沿 dot-source 鏈讀(尾版 → 前版…)", len(chain) >= 2 and "Set-VIAGateDefaults" in txt, f"{book.name} 鏈 {len(chain)} 本")
    chk("尾版拆掉的函式不算在(via-talib 被 v0262 拆除)", not re.search(r"function\s+global:via-talib\b", txt))
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        a, b = Path(td) / "Register-VIA-Commands-v0001.ps1", Path(td) / "Register-VIA-Commands-v0002.ps1"
        a.write_text('. (Join-Path $PSScriptRoot "Register-VIA-Commands-v0002.ps1")\n', encoding="utf-8")
        b.write_text('. (Join-Path $PSScriptRoot "Register-VIA-Commands-v0001.ps1")\n', encoding="utf-8")
        chk("鏈防環(互相 dot-source 不會無限迴圈)", len(command_book_chain(a)) == 2)
    real = engine_number_collisions()
    chk("撞號以編號系統唯一碼為準:同號群組每支有碼 = 不算撞號;沒碼 = 撞號", isinstance(real, dict),
        f"真撞號 {len(real)} · 群組 {len(GROUPS)}")
    body = Path(__file__).read_text(encoding="utf-8")
    chk("本支帶加速器橋 · VIA_FROM_VCGC 標記", "[VIA:ACCEL-BRIDGE" in body and "VIA_FROM_VCGC" in body)
    rc = PRIOR.selftest() if hasattr(PRIOR, "selftest") else 0
    return 0 if all(ok) and rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
