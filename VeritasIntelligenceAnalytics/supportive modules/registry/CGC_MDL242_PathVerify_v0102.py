#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL242_PathVerify v0102 — 薄尾:涵蓋稽核 C6 SSOT 也量小寫 *ssot*.json(Codex #356 P2 · Z282④)

v0101 的 ssot_rows() 只用 `git ls-files "*SSOT*.json"`;編號收集器(CGC_MDL237 v0100 ssot_items)用的是 "*SSOT*.json" 與 "*ssot*.json"
兩個樣式 —— 倉裡小寫的有幾百本,新的 `macro_ssot.json` 或 `ssot/` 夾下的冊沒號時 C6 還是綠。本尾版照編號收集器同一對樣式與同一組排除
(VIA_Reports/ · RetiredEngines · SCOPE_COPY · ASSETS/ · freeze.lock)重算 C6 第二列;其餘整支照 v0101(thin tail;__getattr__ 轉接)。
只收 VCGC 呼叫(VIA_FROM_VCGC=YES)的規矩照前一版。
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

STEM = "CGC_MDL242_PathVerify"

import importlib.util
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", path.stem)
    return int(m.group(1)) if m else -1


PRIOR = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(STEM + "_prior_for_" + Path(__file__).stem, PRIOR)
_PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _PRIOR
_spec.loader.exec_module(_PRIOR)
ENGINE = Path(__file__).stem


def __getattr__(name: str):
    return getattr(_PRIOR, name)

PATTERNS = ("*SSOT*.json", "*ssot*.json")
EXCLUDE = ("VIA_Reports/", "RetiredEngines", "SCOPE_COPY", "ASSETS/", "freeze.lock", ".local.json")
_V0101_SSOT_ROWS = _PRIOR.ssot_rows


def tracked_ssot(via: Path | None = None) -> list:
    via = via or _PRIOR.VIA
    out = subprocess.run(["git", "ls-files", *PATTERNS], cwd=via, capture_output=True, text=True, timeout=120).stdout.splitlines()
    return sorted({r for r in out if not any(x in r for x in EXCLUDE)})


def ssot_rows(books=None) -> list:
    rows = _V0101_SSOT_ROWS(books)
    books = _PRIOR._books() if books is None else books
    have = {str(r.get("source")) for r in books.get("SSOT", [])}
    tracked = tracked_ssot()
    missing = [t for t in tracked if t not in have]
    new = _PRIOR._row("C6 SSOT", "已追蹤 *SSOT*.json / *ssot*.json 都有號", "GREEN" if not missing else "AMBER",
                      f"{len(tracked)} 檔(大小寫兩樣式 · 同編號收集器的排除)· 沒號 {len(missing)}"
                      + (":" + "、".join(Path(m).name for m in missing[:5]) if missing else ""), "git ls-files × 編號冊")
    own = re.compile(r"(^|/)VIA_Numbering_SSOT_v\d+\.json$|(^|/)VIA_NumberBooks/")          # the numbering system's own output (MDL237 v0103)
    ss = [r for r in books.get("SSOT", []) if not own.search(str(r.get("source") or ""))]
    sha = sum(1 for r in ss if r.get("content_sha"))
    dv = sum(1 for r in ss if r.get("declared_version"))
    first = _PRIOR._row("C6 SSOT", "SSOT 冊編號 · 內容指紋 · 宣告版號", "GREEN" if ss and sha == len(ss) else "AMBER",
                        f"{len(ss)} 本有號 · 帶內容指紋 {sha} · 冊內宣告版號 {dv}(編號系統自己的產出不算指紋,不在分母)", "編號冊 SSOT 列")
    return [first if str(r.get("item", "")).startswith("SSOT 冊編號") else r for r in rows if not str(r.get("item", "")).startswith("已追蹤")] + [new]


_PRIOR.ssot_rows = ssot_rows


def main(argv=None) -> int:
    if "--selftest" in (sys.argv[1:] if argv is None else argv):
        return selftest()
    return _PRIOR.main(argv)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    t = tracked_ssot()
    chk("Z282④ 小寫 *ssot*.json 也在量測面", any("ssot" in Path(x).name and "SSOT" not in Path(x).name for x in t), f"{len(t)} 檔")
    rows = ssot_rows()
    r = [x for x in rows if str(x["item"]).startswith("已追蹤")]
    chk("C6 第二列換成兩樣式版本(只有一列,不重複)", len(r) == 1 and "大小寫兩樣式" in r[0]["note"], r[0]["note"][:80] if r else "")
    if not all(ok):
        return 1
    return _PRIOR.selftest()


if __name__ == "__main__":
    raise SystemExit(main())
