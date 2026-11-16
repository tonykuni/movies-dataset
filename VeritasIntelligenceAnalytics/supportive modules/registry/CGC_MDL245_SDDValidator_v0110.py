#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL245_SDDValidator v0110 — 薄尾:位移對照放行時,號冊列的紅燈若正是「冊上代碼 X ≠ 發出的號 Y」本身(X,Y 在對照冊)也認。

實錄(2026-11-16 · v0109 上線後 sdd check):X-NUM 仍紅 —— 位移的 8 列在號冊上 lamp = RED,note = 「冊上代碼 VCGC-REQ240 ≠ 發出的號
  VIA-VCGC-REQ239(不改任何一邊;SDD 驗證器 X-NUM)」。這個紅燈就是位移本身的旗子,v0109 規則 ④(號冊列紅 → 不放行)把它也擋了。
本版只換 v0109 的 reconcile 一格(v0100 … v0109 一字不動):號冊列 lamp RED 時,只有 note 正好是「冊上代碼 X ≠ 發出的號 Y」而且
  (X, Y) 在對照冊 pairs 內才放行;其他原因的紅照舊擋。只讀,不寫冊。
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
_STEM = "CGC_MDL245_SDDValidator"
ENGINE = Path(__file__).stem
NOTE_RX = re.compile(r"^冊上代碼 (\S+) ≠ 發出的號 (\S+)(/|$)")


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location("_sdd_prior_v0110", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR
while "PRIOR" in vars(BASE):
    BASE = vars(BASE)["PRIOR"]


def _flag_is_offset(x: dict, pairs: set) -> bool:
    m = NOTE_RX.match(str(x.get("note") or "").replace("(", "/"))
    return bool(m) and (m.group(1), m.group(2)) in pairs and x.get("declared") == m.group(1) and x.get("code") == m.group(2)


def reconcile(rows: list, start: int, folder: Path = HERE) -> None:
    pairs = PRIOR.alias_pairs(folder)
    num = None
    for r in rows[start:]:
        if r.get("rule") != "X-NUM" or r.get("lamp") != "RED" or not str(r.get("msg", "")).startswith("編號冊號碼 ≠ 冊上代碼"):
            continue
        num = num if num is not None else PRIOR._num_rows(folder)
        bad = [c for c, x in num.items() if c and (x.get("code") != "VIA-" + c or x.get("lamp") == "RED")]
        unknown = [c for c in bad if (c, num[c].get("code")) not in pairs
                   or (num[c].get("lamp") == "RED" and not _flag_is_offset(num[c], pairs))]
        if unknown:
            r["msg"] = "編號冊號碼 ≠ 冊上代碼(不在位移對照冊):%s" % unknown[:6]
        else:
            r["lamp"] = "GREEN"
            r["msg"] = "WKF · STP · REQ 全編號;號碼 = VIA- + 冊上代碼,另有已知位移 %d 對(VIA_REQ_CodeAlias_SSOT · REQ239 跳號;號冊上的位移紅旗照留)" % len(bad)


PRIOR.reconcile = reconcile                     # v0109 的 check_registration 以模組全域叫 reconcile()


def __getattr__(name: str):
    return getattr(PRIOR, name)


def main(argv=None):
    return PRIOR.main(argv)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:300]) if note and not cond else ''}")

    print(f"=== {ENGINE} · 薄尾自測(位移紅旗本身可放行)===")
    import tempfile
    tmp = Path(tempfile.mkdtemp(prefix="sdd0110_"))
    (tmp / "VIA_NumberBooks").mkdir()
    (tmp / "VIA_REQ_CodeAlias_SSOT_v0100.json").write_text(json.dumps({"pairs": [{"declared": "VCGC-REQ003", "issued": "VIA-VCGC-REQ002"}]}), encoding="utf-8")

    def run(book):
        (tmp / "VIA_NumberBooks" / "VIA_NumberBook_REQ_v0100.jsonl").write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in book) + "\n", encoding="utf-8")
        rows = [{"lamp": "RED", "rule": "X-NUM", "msg": "編號冊號碼 ≠ 冊上代碼:[...]", "ref": ""}]
        reconcile(rows, 0, tmp)
        return rows[0]

    flag = "冊上代碼 VCGC-REQ003 ≠ 發出的號 VIA-VCGC-REQ002(不改任何一邊;SDD 驗證器 X-NUM)"
    r = run([{"code": "VIA-VCGC-REQ001", "declared": "VCGC-REQ001"}, {"code": "VIA-VCGC-REQ002", "declared": "VCGC-REQ003", "lamp": "RED", "note": flag}])
    chk("① 位移紅旗(note 正是 X ≠ Y 且在對照冊)→ 綠", r["lamp"] == "GREEN" and "已知位移 1 對" in r["msg"], r)
    r = run([{"code": "VIA-VCGC-REQ002", "declared": "VCGC-REQ003", "lamp": "RED", "note": "別的原因"}])
    chk("② 紅燈是別的原因 → 照舊紅", r["lamp"] == "RED", r)
    r = run([{"code": "VIA-VCGC-REQ002", "declared": "VCGC-REQ004", "lamp": "RED", "note": flag}])
    chk("③ note 跟這列的代碼 / 號碼對不上 → 紅", r["lamp"] == "RED", r)
    r = run([{"code": "VIA-VCGC-REQ005", "declared": "VCGC-REQ006", "lamp": "RED", "note": "冊上代碼 VCGC-REQ006 ≠ 發出的號 VIA-VCGC-REQ005"}])
    chk("④ 不在對照冊 → 紅", r["lamp"] == "RED", r)
    chk("⑤ v0109 的 check_registration 走得到本版 reconcile", PRIOR.reconcile is reconcile and BASE.check_registration is PRIOR.check_registration)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 檔面:加速器橋 · 網路橋 · 零 TA-Lib · 不寫冊", "[VIA:ACCEL-BRIDGE:v0100]" in src and "[VIA:NET-BRIDGE:v0100]" in src
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M) and ".write_text(" not in src.split("def selftest", 1)[0])
    n = sum(ok)
    print(f"[計] {ENGINE} 本版 {n}/{len(ok)}{' PASS' if n == len(ok) else ' FAIL'}")
    rc = PRIOR.selftest()
    print(f"[計] {ENGINE} 合計 {'PASS' if n == len(ok) and rc == 0 else 'FAIL'}(前版 rc {rc})")
    return 0 if n == len(ok) and rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if sys.argv[1:] == ["--selftest"] else main())
