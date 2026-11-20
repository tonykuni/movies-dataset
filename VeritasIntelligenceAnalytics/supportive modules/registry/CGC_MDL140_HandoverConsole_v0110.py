#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL140_HandoverConsole v0110 — 薄尾:舊版號檔的加速器橋改看家族尾版(版史不算缺)· 尾版本身照舊判
操作員 2026-11-20 裁定(a)「a 同意 開PR 自動完成」:
  交接閘 ACCEL_BRIDGE_MISSING 列了 7 支,其中 5 支是舊版號檔(VDF_TW_TickerClass v0100 · VDF_ENG238 v0101 ·
  VQG_AllInOne v0104 · VQG_SectorActiveWeight v0100 · VRN2_UIAction v0100);它們的家族尾版都已掛橋,
  其中 4 支被後版或交接冊以 SHA-256 釘住(就地注入會打破釘值),且 AGENTS.md 第 4 條要求「修改開新版、已鎖成功來源維持原樣」。
  VCGC 自己的尺(CGC_MDL124 BridgeSweeper)早就把「前版 = 版史(不算缺)」;只有交接閘把有改動的前版也算缺,三把尺各說各的。
本版只動 ACCEL_BRIDGE_MISSING 一條,四條件全中才移出紅列、記進 report["version_history"](逐檔 · 尾版 · 證據):
  ① 檔名帶版號 _vNNNN,而且同夾同家族有版號更大的檔(本檔不是尾版)
  ② 家族尾版(同夾版號最大)有 v0101 同一把尺的加速器橋標記(本檔常數 MARKER)
  ③ 家族尾版的語法樹裡真的 import VIA_SuperAccel_Module(以生效計,只有標記不算)
  ④ 尾版讀得懂(語法樹解析得過);解析不過 → 不放行
尾版本身、無版號檔、家族尾版沒掛橋的一律照舊紅;其他規則一條不動;監看範圍不變。
其餘照 v0109(停用檔名冊 · 被取代工作項 · Z281 雙胞移交 · 凍結收容件具名豁免 · 家族已登)。只收 VCGC 呼叫。零網路 · 不 import 他系統 · 不碰 TA-Lib。
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
import ast
import importlib.util
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL140_HandoverConsole"
ENGINE = Path(__file__).stem
VERSION = "v0110"
MARKER = "[VIA:ACCEL-BRIDGE:"          # 與 v0101 判 ACCEL_BRIDGE_MISSING 同一把尺


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + ENGINE, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)                 # v0109:停用檔名冊已裝進 v0101 的 audit
VIA = PRIOR.VIA
POLICY = PRIOR.POLICY
BASE = PRIOR.BASE


def family_tail(path: Path):
    """同夾同家族(去掉 _vNNNN 後同名)版號最大的那支;本檔沒版號回 None。"""
    path = Path(path)
    if _vnum(path) < 0:
        return None
    fam = path.stem.rsplit("_v", 1)[0]
    sib = [q for q in path.parent.glob(fam + "_v*.py") if q.stem.rsplit("_v", 1)[0] == fam and _vnum(q) >= 0]
    return max(sib, key=_vnum) if sib else None


def accel_live(path: Path) -> tuple:
    """(有標記, 語法樹真的匯入, 讀得懂)。"""
    try:
        text = Path(path).read_text(encoding="utf-8-sig")
        tree = ast.parse(text)
    except (OSError, UnicodeDecodeError, SyntaxError, ValueError):
        return False, False, False
    imp = any((isinstance(n, ast.Import) and any(a.name == "VIA_SuperAccel_Module" for a in n.names))
              or (isinstance(n, ast.ImportFrom) and n.module == "VIA_SuperAccel_Module") for n in ast.walk(tree))
    return MARKER in text, imp, True


def apply_version_history(report: dict, via=VIA) -> dict:
    """ACCEL_BRIDGE_MISSING 裡的舊版號檔:家族尾版真的掛橋才移出紅列(版史);尾版本身與其餘一律照舊。"""
    kept, history = [], []
    for row in report.get("rows", []):
        rel = row.get("detail")
        if row.get("rule") != "ACCEL_BRIDGE_MISSING" or not isinstance(rel, str):
            kept.append(row)
            continue
        p = Path(via) / rel
        tail = family_tail(p)
        if tail is None or tail.resolve() == p.resolve():
            kept.append(row)
            continue
        mark, imp, ok = accel_live(tail)
        if not (mark and imp and ok):
            kept.append(row)
            continue
        history.append({"path": rel, "tail": tail.relative_to(Path(via)).as_posix(), "marker": mark, "ast_import": imp})
    lamps = [x["lamp"] for x in kept]
    lamp = "RED" if "RED" in lamps else "YELLOW" if lamps else "GREEN"
    report["rows"] = kept
    report["lamp"] = lamp
    report["closeout_lamp"] = ("RED" if lamp == "RED" else "YELLOW"
                               if report.get("pending") or lamp == "YELLOW" or report.get("z281_handover") else "GREEN")
    report["version_history"] = history
    s = report.setdefault("summary", {})
    s["findings"] = len(kept)
    s["version_history"] = len(history)
    return report


_V0109_AUDIT = BASE.audit


def audit(via=VIA, policy=None, baseline=None, require_baseline=True):
    return apply_version_history(_V0109_AUDIT(via, policy, baseline, require_baseline), via)


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
    import tempfile
    BASE.audit = _V0109_AUDIT                   # 前版自測驗「v0109 裝在 v0101 全域」:跑前版時還原,跑完裝回本版
    try:
        rc = PRIOR.selftest()
    finally:
        BASE.audit = audit
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    bridged = ("# " + MARKER + "v0100] x\ntry:\n    import VIA_SuperAccel_Module as VIA_ACCEL\n"
               "except Exception:\n    VIA_ACCEL = None\n")
    with tempfile.TemporaryDirectory(prefix="mdl140_v0110_") as td:
        via = Path(td)
        files = {
            "a/Fam_v0100.py": "x = 1\n",                 # 舊版沒橋,尾版有橋 → 版史
            "a/Fam_v0101.py": bridged,
            "b/Only_v0100.py": "x = 1\n",                # 沒有更新版 → 自己就是尾版
            "c/Mark_v0100.py": "x = 1\n",                # 尾版只有標記、沒真的匯入 → 不放行
            "c/Mark_v0101.py": "# " + MARKER + "v0100]\nx = 1\n",
            "d/Bad_v0100.py": "x = 1\n",                 # 尾版語法壞 → 不放行
            "d/Bad_v0101.py": bridged + "def (:\n",
            "e/plain.py": "x = 1\n",                     # 無版號 → 照舊
            "f/Fam_v0100.py": "x = 1\n",                 # 別夾同名家族不算(只看同夾)
        }
        for rel, txt in files.items():
            (via / rel).parent.mkdir(parents=True, exist_ok=True)
            (via / rel).write_text(txt, encoding="utf-8")
        ab = lambda p: {"lamp": "RED", "rule": "ACCEL_BRIDGE_MISSING", "detail": p}

        def rep(rows, **kw):
            return apply_version_history({"rows": [dict(r) for r in rows], "pending": [], "summary": {}, **kw}, via)
        r = rep([ab("a/Fam_v0100.py")])
        chk("ⓐ 舊版號檔 · 家族尾版有標記且真的匯入 → 移出紅列 · 記進 version_history · 燈 GREEN",
            r["lamp"] == "GREEN" and r["version_history"] == [{"path": "a/Fam_v0100.py", "tail": "a/Fam_v0101.py", "marker": True, "ast_import": True}]
            and r["summary"]["version_history"] == 1, r)
        r = rep([ab("b/Only_v0100.py")])
        chk("ⓑ 本檔就是尾版 → 照舊 RED(尾版自己要掛橋)", r["lamp"] == "RED" and r["rows"] == [ab("b/Only_v0100.py")] and not r["version_history"], r)
        r = rep([ab("c/Mark_v0100.py")])
        chk("ⓒ 尾版只有標記、語法樹沒匯入 → 不放行(以生效計)", r["lamp"] == "RED" and not r["version_history"], r)
        r = rep([ab("d/Bad_v0100.py")])
        chk("ⓓ 尾版語法樹解析不過 → 不放行", r["lamp"] == "RED" and not r["version_history"], r)
        r = rep([ab("e/plain.py")])
        chk("ⓔ 無版號檔 → 照舊 RED", r["lamp"] == "RED" and not r["version_history"], r)
        r = rep([ab("f/Fam_v0100.py")])
        chk("ⓕ 別夾同名家族的尾版不算(只看同夾)→ 照舊 RED", r["lamp"] == "RED" and not r["version_history"], r)
        r = rep([{"lamp": "RED", "rule": "CHANGED_CODE_WITHOUT_TEST", "detail": "a/Fam_v0100.py"}, ab("a/Fam_v0100.py")])
        chk("ⓖ 其他規則的紅一條不動(同一檔的改了沒測照舊紅)",
            r["lamp"] == "RED" and r["rows"] == [{"lamp": "RED", "rule": "CHANGED_CODE_WITHOUT_TEST", "detail": "a/Fam_v0100.py"}], r)
        r = rep([ab("a/Fam_v0100.py")], z281_handover=[{"path": "z.py"}])
        chk("ⓗ 前版判的驗收燈不被洗:有 Z281 移交 → 交接燈 GREEN · 驗收燈 YELLOW", r["lamp"] == "GREEN" and r["closeout_lamp"] == "YELLOW", r)
    chk("ⓘ 已裝進 v0101 模組全域(check / checkpoint 經本版 audit)", BASE.audit is audit)
    text = Path(__file__).read_text(encoding="utf-8")
    chk("ⓙ 檔頭:加速器橋 · 網路橋在(__future__ 之後)· 不碰 TA-Lib · 不含本機路徑",
        "VIA:ACCEL-BRIDGE" in text and "VIA:NET-BRIDGE" in text and text.index("from __future__") < text.index("[VIA:ACCEL-BRIDGE")
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M) and ("C:" + "\\Users") not in text)
    passed = rc == 0 and all(ok)
    print(f"[交接 {VERSION}] 本版 {sum(ok)}/{len(ok)} · 前版 {'PASS' if rc == 0 else 'FAIL'} · 舊版號檔看家族尾版 · {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
