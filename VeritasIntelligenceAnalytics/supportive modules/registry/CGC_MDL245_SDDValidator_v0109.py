#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL245_SDDValidator v0109 — 薄尾:X-NUM 認得需求代碼位移對照冊(VIA_REQ_CodeAlias_SSOT)

實錄(2026-11-16 · sdd check):X-NUM RED「編號冊號碼 ≠ 冊上代碼:VCGC-REQ240 … 246 · 247」。
  根因:需求冊從沒用過 VCGC-REQ239(跳號);中央號冊照「同父層同類下一號(連續)」發號,從 VCGC-REQ240 起每個都晚一號
  (VIA-VCGC-REQ239 = 冊上 VCGC-REQ240 …)。號冊身分與冊上代碼兩邊都不可改(只增;改身分 = 紅)。
  操作員 2026-11-16 授權 AI 全權裁定:接受位移 + 對照冊(VIA_REQ_CodeAlias_SSOT,只增)+ 需求冊 v0264 補 REQ239 佔號列讓之後重新對齊。
本版只換一格(v0100 … v0108 一字不動):本體 check_registration 跑完後,若 X-NUM 紅列只因「號碼 ≠ VIA- + 冊上代碼」,
  而且每一個不合的 (冊上代碼, 號碼) 都在對照冊 pairs 內 → 改綠並寫明「已知位移 N 對(對照冊)」;有任何一個不在冊上 → 照舊紅,
  訊息只列不在冊上的那些。lamp RED 的號冊列不放行。其餘整支照 v0108(樹外正主 rel)。只讀,不寫冊。
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
ALIAS_GLOB = "VIA_REQ_CodeAlias_SSOT_v*.json"


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location("_sdd_prior_v0109", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR
while "PRIOR" in vars(BASE):
    BASE = vars(BASE)["PRIOR"]
_V0100_CHECK_REGISTRATION = BASE.check_registration


def alias_pairs(folder: Path = HERE) -> set:
    """對照冊尾版的 (冊上代碼, 號碼) 集合;冊不在 = 空集合(照舊紅,不放行)。"""
    c = [p for p in folder.glob(ALIAS_GLOB) if _vnum(p) >= 0]
    if not c:
        return set()
    d = json.loads(max(c, key=_vnum).read_text(encoding="utf-8"))
    return {(x.get("declared"), x.get("issued")) for x in d.get("pairs") or []}


def _num_rows(folder: Path) -> dict:
    out = {}
    for kind in ("WKF", "STP", "REQ"):
        p = BASE.newest(f"VIA_NumberBook_{kind}_v*.jsonl", folder / "VIA_NumberBooks")
        for line in (p.read_text(encoding="utf-8").splitlines() if p else []):
            if line.strip():
                r = json.loads(line)
                out[r.get("declared")] = r
    return out


def reconcile(rows: list, start: int, folder: Path = HERE) -> None:
    """只看本輪 check_registration 新加的列;X-NUM「號碼 ≠ 冊上代碼」紅列 → 用對照冊重判。"""
    pairs = alias_pairs(folder)
    num = None
    for r in rows[start:]:
        if r.get("rule") != "X-NUM" or r.get("lamp") != "RED" or not str(r.get("msg", "")).startswith("編號冊號碼 ≠ 冊上代碼"):
            continue
        num = num if num is not None else _num_rows(folder)
        bad = [c for c, x in num.items() if c and (x.get("code") != "VIA-" + c or x.get("lamp") == "RED")]
        unknown = [c for c in bad if (c, num[c].get("code")) not in pairs or num[c].get("lamp") == "RED"]
        if unknown:
            r["msg"] = "編號冊號碼 ≠ 冊上代碼(不在位移對照冊):%s" % unknown[:6]
        else:
            r["lamp"] = "GREEN"
            r["msg"] = "WKF · STP · REQ 全編號;號碼 = VIA- + 冊上代碼,另有已知位移 %d 對(VIA_REQ_CodeAlias_SSOT · REQ239 跳號)" % len(bad)


def check_registration(state, rows, targets, versions: dict):
    start = len(rows)
    out = _V0100_CHECK_REGISTRATION(state, rows, targets, versions)
    reconcile(rows, start)
    return out


BASE.check_registration = check_registration          # 本體 check() 以模組全域叫 check_registration()


def __getattr__(name: str):
    return getattr(PRIOR, name)


def main(argv=None):
    return PRIOR.main(argv)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:300]) if note and not cond else ''}")

    print(f"=== {ENGINE} · 薄尾自測(X-NUM 認得需求代碼位移對照冊)===")
    import tempfile
    tmp = Path(tempfile.mkdtemp(prefix="sdd0109_"))
    (tmp / "VIA_NumberBooks").mkdir()
    book = [{"code": "VIA-VCGC-REQ001", "declared": "VCGC-REQ001"}, {"code": "VIA-VCGC-REQ002", "declared": "VCGC-REQ003"}]
    (tmp / "VIA_NumberBooks" / "VIA_NumberBook_REQ_v0100.jsonl").write_text("\n".join(json.dumps(x) for x in book) + "\n", encoding="utf-8")
    red = lambda: [{"lamp": "RED", "rule": "X-NUM", "msg": "編號冊號碼 ≠ 冊上代碼:['VCGC-REQ003']", "ref": ""}]
    rows = red()
    reconcile(rows, 0, tmp)
    chk("① 對照冊不在 → 照舊紅(不放行)", rows[0]["lamp"] == "RED" and "不在位移對照冊" in rows[0]["msg"], rows)
    (tmp / "VIA_REQ_CodeAlias_SSOT_v0100.json").write_text(json.dumps({"pairs": [{"declared": "VCGC-REQ003", "issued": "VIA-VCGC-REQ002"}]}), encoding="utf-8")
    rows = red()
    reconcile(rows, 0, tmp)
    chk("② 不合的都在對照冊 → 綠,寫明已知位移 1 對", rows[0]["lamp"] == "GREEN" and "已知位移 1 對" in rows[0]["msg"], rows)
    book.append({"code": "VIA-VCGC-REQ004", "declared": "VCGC-REQ009"})
    (tmp / "VIA_NumberBooks" / "VIA_NumberBook_REQ_v0100.jsonl").write_text("\n".join(json.dumps(x) for x in book) + "\n", encoding="utf-8")
    rows = red()
    reconcile(rows, 0, tmp)
    chk("③ 有一對不在對照冊 → 紅,只列不在冊上的", rows[0]["lamp"] == "RED" and "VCGC-REQ009" in rows[0]["msg"] and "VCGC-REQ003" not in rows[0]["msg"], rows)
    book[1]["lamp"] = "RED"
    book.pop()
    (tmp / "VIA_NumberBooks" / "VIA_NumberBook_REQ_v0100.jsonl").write_text("\n".join(json.dumps(x) for x in book) + "\n", encoding="utf-8")
    rows = red()
    reconcile(rows, 0, tmp)
    chk("④ 號冊列本身 lamp RED → 對照冊也不放行", rows[0]["lamp"] == "RED", rows)
    other = [{"lamp": "RED", "rule": "X-NUM", "msg": "尾版沒編號(待 CGC_MDL237 --apply):['a.py']", "ref": ""}]
    reconcile(other, 0, tmp)
    chk("⑤ 別種 X-NUM 紅(尾版沒編號)不碰", other[0]["lamp"] == "RED")
    chk("⑥ 本體 check_registration 已換成本版(check() 走得到)", BASE.check_registration is check_registration)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑦ 檔面:加速器橋 · 網路橋 · 零 TA-Lib · 不寫冊", "[VIA:ACCEL-BRIDGE:v0100]" in src and "[VIA:NET-BRIDGE:v0100]" in src
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M) and ".write_text(" not in src.split("def selftest", 1)[0])
    n = sum(ok)
    print(f"[計] {ENGINE} 本版 {n}/{len(ok)}{' PASS' if n == len(ok) else ' FAIL'}")
    rc = PRIOR.selftest()
    print(f"[計] {ENGINE} 合計 {'PASS' if n == len(ok) and rc == 0 else 'FAIL'}(前版 rc {rc})")
    return 0 if n == len(ok) and rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if sys.argv[1:] == ["--selftest"] else main())
