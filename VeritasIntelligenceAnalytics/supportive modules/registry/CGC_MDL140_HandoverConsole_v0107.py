#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL140_HandoverConsole v0107 — 薄尾:無版號檔有「內容相同、已登記」的 _v0100 雙胞 → 未登記改記「等 Z281 移交」待辦

操作員裁定(2026-10-10,PR #518):5 支無版號 .py(VDF_MDL001 · VDF_MDL201 · VDF_MDL303 · VRN financial_data_standardization ·
  VRN vrn_sample_reader)各出內容不變的 `_v0100` 版號檔讓 registry-sync 登冊;舊無版號檔仍被引用就不搬,
  交接閘把它們記「等 Z281 移交」,不列紅。
本版只動 MODULE_UNREGISTERED 一條,三條件全中才移出紅列(記進 z281_handover,逐檔具名):
  ① 無版號 .py   ② 同夾有 `<名>_v0100.py` 雙胞,CRLF 正規化後位元組相同   ③ 雙胞的家族已登在中央元件冊
  「改了沒測」不在此列:原檔要列進交接測試案(CGC_MDL275 Z281TwinProbe 的案)的依賴才算測過,照舊判。
其餘照 v0106(凍結收容件具名豁免 · 家族已登)。只收 VCGC 呼叫。零網路。
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

import hashlib
import importlib.util
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL140_HandoverConsole"
ENGINE = Path(__file__).stem
VERSION = "v0107"


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + ENGINE, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)                 # v0106:已把凍結收容件豁免 + 家族已登裝進 v0101 的 audit
VIA = PRIOR.VIA
POLICY = PRIOR.POLICY
BASE = PRIOR.BASE

_UNVERSIONED = re.compile(r"^(?!.*_v\d{4}\.py$).+\.py$")
WHY = "無版號檔(Z281 命名待逐支判定):內容相同的 _v0100 雙胞已登冊;舊檔仍被引用不搬,等 Z281 移交(操作員 2026-10-10 裁定)"


def _norm_sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def twin_ok(via, rel: str, families: set) -> bool:
    rel = str(rel).replace("\\", "/")
    if not _UNVERSIONED.match(rel):
        return False
    twin = rel[:-3] + "_v0100.py"
    p, t = BASE.local(Path(via), rel), BASE.local(Path(via), twin)
    return p.is_file() and t.is_file() and _norm_sha(p) == _norm_sha(t) and PRIOR.family_of(twin) in families


def apply_z281(report: dict, via, families: set) -> dict:
    kept, moved = [], []
    for row in report.get("rows", []):
        d = row.get("detail")
        if row.get("rule") == "MODULE_UNREGISTERED" and isinstance(d, str) and twin_ok(via, d, families):
            moved.append({"path": d, "twin": d[:-3] + "_v0100.py", "why": WHY})
        else:
            kept.append(row)
    lamps = [x["lamp"] for x in kept]
    lamp = "RED" if "RED" in lamps else "YELLOW" if lamps else "GREEN"
    report["rows"] = kept
    report["lamp"] = lamp
    report["closeout_lamp"] = "RED" if lamp == "RED" else "YELLOW" if report.get("pending") or lamp == "YELLOW" or moved else "GREEN"
    report["z281_handover"] = moved
    s = report.setdefault("summary", {})
    s["findings"] = len(kept)
    s["z281_handover"] = len(moved)
    return report


_V0106_AUDIT = BASE.audit


def audit(via=VIA, policy=None, baseline=None, require_baseline=True):
    report = _V0106_AUDIT(via, policy, baseline, require_baseline)
    return apply_z281(report, via, PRIOR.registered_families(PRIOR._inventory_sources(via, policy)))


BASE.audit = audit


def __getattr__(name: str):
    return getattr(PRIOR, name)


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        if os.environ.get("VIA_FROM_VCGC") != "YES":
            print("[DENY] VCGC entry required")
            return 2
        return selftest()
    return PRIOR.main(argv)


def selftest():
    BASE.audit = _V0106_AUDIT                   # 前版自測驗「v0106 裝在 v0101 全域」:跑前版時還原,跑完裝回本版
    try:
        rc = PRIOR.selftest()
    finally:
        BASE.audit = audit
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        d = t / "functional modules" / "VDF"
        d.mkdir(parents=True)
        # write_bytes:Windows 文字模式會把 "\r\n" 再轉成 "\r\r\n"(PR #518 CI 實錄),夾具要逐位元組寫
        (d / "A.py").write_bytes(b"x = 1\n")
        (d / "A_v0100.py").write_bytes(b"x = 1\r\n")
        (d / "B.py").write_bytes(b"y = 1\n")
        (d / "B_v0100.py").write_bytes(b"y = 2\n")
        (d / "C.py").write_bytes(b"z = 1\n")
        fams = {"functional modules/VDF/A", "functional modules/VDF/B"}
        rows = [{"lamp": "RED", "rule": "MODULE_UNREGISTERED", "detail": "functional modules/VDF/" + n + ".py"} for n in "ABC"]
        rows.append({"lamp": "RED", "rule": "CHANGED_CODE_WITHOUT_TEST", "detail": "functional modules/VDF/A.py"})
        rep = apply_z281({"rows": rows, "pending": [], "summary": {}}, t, fams)
        chk("① 雙胞同內容 + 家族已登 → 未登改記 z281_handover", [m["path"] for m in rep["z281_handover"]] == ["functional modules/VDF/A.py"])
        chk("② 雙胞內容不同 / 沒雙胞 → 照舊紅", sum(r["rule"] == "MODULE_UNREGISTERED" for r in rep["rows"]) == 2)
        chk("③ 改了沒測不在此列(照舊紅)· 有移交 → 驗收燈不是 GREEN", any(r["rule"] == "CHANGED_CODE_WITHOUT_TEST" for r in rep["rows"])
            and rep["lamp"] == "RED")
        rep = apply_z281({"rows": [rows[0]], "pending": [], "summary": {}}, t, fams)
        chk("④ 只剩移交時交接燈 GREEN、驗收燈 YELLOW", rep["lamp"] == "GREEN" and rep["closeout_lamp"] == "YELLOW")
        rep = apply_z281({"rows": [rows[0]], "pending": [], "summary": {}}, t, set())
        chk("⑤ 雙胞家族沒登冊 → 照舊紅", rep["lamp"] == "RED" and not rep["z281_handover"])
    chk("⑥ 已裝進 v0101 模組全域(check / checkpoint 經本版 audit)", BASE.audit is audit)
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑦ 檔頭:加速器橋 · 網路橋在(__future__ 之後)· 不碰 TA-Lib",
        "VIA:ACCEL-BRIDGE" in text and "VIA:NET-BRIDGE" in text and text.index("from __future__") < text.index("[VIA:ACCEL-BRIDGE")
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M))
    passed = rc == 0 and all(ok)
    print(f"[交接 {VERSION}] 本版 {sum(ok)}/{len(ok)} · 前版 {'PASS' if rc == 0 else 'FAIL'} · Z281 雙胞移交 · {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
