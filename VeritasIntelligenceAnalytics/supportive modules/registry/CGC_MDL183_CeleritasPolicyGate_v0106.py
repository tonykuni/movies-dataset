#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL183_CeleritasPolicyGate v0106 — 薄尾:PY 缺橋照 CGC_MDL156 名冊豁免(INFO 照列)· 版號舊檔有帶橋尾版 = 版史(同 v0103 的 PS 規則)

實錄(2026-11-06,GO ON 回合 · 交接案 celeritas_gate_v0104 重跑 FAIL ㉒「PY 缺 2」):
  ① functional modules/VRN/nonstock_v0310/engine/VIA_NON_STOCK_SUMMARIZER_ENGINE_v0310.py —— 操作員原件(byte-exact · 交接冊 frozen_sources 守 SHA)。
     掃橋器 CGC_MDL156 v0115 的名冊(_ACCEL_EXEMPT)已具名豁免(不准注橋),本閘 v0105 不問名冊 → 同一支檔兩把尺:掃橋器說「不准注」、閘說「缺橋紅」。
     本版:PY 缺橋裡命中 CGC_MDL156 尾版名冊 _ACCEL_EXEMPT 前綴的(AST 讀字面值,不執行名冊模組)→ py.roster_exempt(INFO 照列,帶名冊理由)。名單在冊不在碼。
  ② functional modules/VRN/VRN2_UIAction_v0100.py —— 版號舊檔;同夾同族 v0101 / v0105 / v0107 第 3 行都帶橋。
     已發布的版本不原地改(版本律 · Codex #600 P1),它永遠補不了橋;掃橋器只掃尾版(tails 全覆蓋),閘卻把版史算紅。
     本版:PY 缺橋裡有版號、同夾同族有更高版號且帶橋的尾版、且尾版 SSOT 冊沒有活呼叫(同 v0103 live_callers)→ py.history(INFO 照列,記尾版);
     尾版沒橋 / 仍被冊指名 → 照紅(history_blocked)。
  其餘(收容件 INFO · 唯讀本扣鎖冊退場 · 既有債扣退役帳 · PS 規則)全照 v0105。只收 VCGC 呼叫。零網路。只讀。
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

import ast
import importlib.util
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL183_CeleritasPolicyGate"
PRIOR_PATH = [p for p in sorted(HERE.glob(_STEM + "_v*.py")) if p.name < Path(__file__).name][-1]
_spec = importlib.util.spec_from_file_location("cgc_mdl183_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
V0101 = PRIOR.V0101
VERSION = "v" + Path(__file__).stem.rsplit("_v", 1)[-1]
PY_MARK = V0101.PY_MARK
_SCAN_V0105 = PRIOR.scan
_LIVE_CALLERS = PRIOR.live_callers_v0103          # v0103 的「尾版 SSOT 冊有沒有精確指名」同一把尺
ROSTER_STEM = "CGC_MDL156_VIAAcceleratorControl"  # 掃橋器家族:名冊 _ACCEL_EXEMPT 的正主
ROSTER_NAME = "_ACCEL_EXEMPT"
_VRX = re.compile(r"^(?P<stem>.+)_v(?P<n>\d{4})\.py$")


def __getattr__(name):
    return getattr(PRIOR, name)


def _vnum(p: Path) -> int:
    m = _VRX.match(p.name)
    return int(m.group("n")) if m else -1


def roster_path() -> Path | None:
    """CGC_MDL156 尾版(registry 夾同族最高版號);不在就 None(照舊:不自己列一張名冊)。"""
    hits = [p for p in HERE.glob(ROSTER_STEM + "_v*.py") if _VRX.match(p.name)]
    return max(hits, key=_vnum) if hits else None


def roster_exempt(path: Path | None = None) -> tuple:
    """名冊 _ACCEL_EXEMPT 的字面值((前綴, 理由)…):AST 讀,不執行名冊模組;讀不到 / 不是字面值就回空。"""
    p = path or roster_path()
    if p is None or not p.is_file():
        return ()
    try:
        tree = ast.parse(p.read_text(encoding="utf-8", errors="ignore"))
    except (OSError, SyntaxError, ValueError):
        return ()
    for n in tree.body:
        if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == ROSTER_NAME:
            try:
                return tuple((str(k), str(w)) for k, w in ast.literal_eval(n.value))
            except (ValueError, TypeError):
                return ()
    return ()


def roster_why(rel: str, roster: tuple) -> str | None:
    """同 CGC_MDL156 的比法:前綴 in "/" + 相對路徑;命中回名冊理由,沒中回 None。"""
    r = "/" + str(rel).replace("\\", "/")
    for key, why in roster:
        if key and key in r:
            return why
    return None


def versioned_tail_py(path: Path) -> Path | None:
    """有版號 .py 的同夾同族更高版號尾版;本身無版號 / 已是尾版 / 沒同族 = None。"""
    m = _VRX.match(path.name)
    if not m or not path.parent.is_dir():
        return None
    stem, n = m.group("stem"), int(m.group("n"))
    best = None
    for q in path.parent.iterdir():
        mq = _VRX.match(q.name)
        if q.is_file() and mq and mq.group("stem") == stem and int(mq.group("n")) > n and (best is None or int(mq.group("n")) > _vnum(best)):
            best = q
    return best


def scan(root: Path | None = None) -> dict:
    """同 v0105;PY 缺橋裡命中名冊前綴 → roster_exempt(INFO);版號舊檔有帶橋尾版且冊沒活呼叫 → history(INFO);其餘照紅。"""
    s = _SCAN_V0105(root)
    py = s.get("py")
    if not isinstance(py, dict):
        return s
    base = Path(root) if root else V0101.VIA
    roster = roster_exempt()
    keep, exempt, hist, blocked = [], [], [], []
    for rp in py.get("missing") or []:
        why = roster_why(rp, roster)
        if why:
            exempt.append({"file": rp, "why": why})
            continue
        tail = versioned_tail_py(base / rp)
        if tail is not None and PY_MARK in tail.read_text(encoding="utf-8", errors="ignore"):
            trel = str(tail.relative_to(base)).replace("\\", "/")
            callers = _LIVE_CALLERS(Path(rp).name, base)
            if callers:
                blocked.append({"file": rp, "tail": trel, "callers": callers[:8]})
                keep.append(rp)
            else:
                hist.append({"file": rp, "tail": trel})
        else:
            keep.append(rp)
    py["missing"], py["roster_exempt"], py["history"], py["history_blocked"] = keep, exempt, hist, blocked
    py["state"] = "GREEN" if not keep else "RED"
    ps = s.get("ps") or {}
    s["state"] = "GREEN" if py["state"] == "GREEN" and ps.get("state") == "GREEN" else "RED"
    return s


def _install_v0106() -> None:
    V0101.scan = scan                      # v0101 的 report / 八檢讀模組層 scan
    PRIOR.PRIOR.PRIOR.PRIOR.scan = scan    # v0102
    PRIOR.PRIOR.PRIOR.scan = scan          # v0103
    PRIOR.PRIOR.scan = scan                # v0104
    PRIOR.scan = scan                      # v0105 的 ㉒ ㉓ 與各層同一把尺


_install_v0106()


def report() -> int:
    rc = PRIOR.report()
    py = (scan().get("py") or {})
    for e in py.get("roster_exempt") or []:
        print(f"   · 名冊豁免(INFO){e['file']} —— {e['why'][:70]}")
    for h in py.get("history") or []:
        print(f"   · 版史(INFO){h['file']} → 尾版 {h['tail']} 帶橋")
    for b in py.get("history_blocked") or []:
        print(f"   · 版史仍被冊指名(照紅){b['file']} ← {b['callers'][:3]}")
    return rc


def selftest() -> int:
    rc = PRIOR.selftest()            # v0101 八檢 + v0102 … v0105 加檢照跑(實樹以本版規則量)
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' (' + note + ')') if note else ''}")

    print(f"=== {_STEM} {VERSION} 薄尾加檢(PY 名冊豁免 · 版史)===")
    rp = roster_path()
    roster = roster_exempt()
    chk("㉔ CGC_MDL156 尾版名冊 _ACCEL_EXEMPT 由 AST 讀到(名單在冊不在碼)· 含操作員原件前綴",
        len(roster) >= 4 and any(k == "functional modules/VRN/nonstock_v0310/engine/" for k, _ in roster) and all(w for _, w in roster),
        f"{len(roster)} 條 · {rp.name if rp else '-'}")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        vrn = root / "functional modules" / "VRN"
        (vrn / "nonstock_v0310" / "engine").mkdir(parents=True)
        (vrn / "nonstock_v0310" / "engine" / "X_v0310.py").write_text("x = 1\n", encoding="utf-8")       # 操作員原件:名冊豁免
        (vrn / "Foo_v0100.py").write_text("x = 1\n", encoding="utf-8")                                     # 版史:v0102 帶橋
        (vrn / "Foo_v0102.py").write_text("#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n# [VIA:ACCEL-BRIDGE:v0111]\nx = 2\n", encoding="utf-8")
        (vrn / "Bar_v0100.py").write_text("x = 1\n", encoding="utf-8")                                     # 沒同族尾版 → 照紅
        (vrn / "Baz_v0100.py").write_text("x = 1\n", encoding="utf-8")                                     # 尾版也沒橋 → 兩支都紅
        (vrn / "Baz_v0101.py").write_text("x = 1\n", encoding="utf-8")
        s = scan(root)
        py = s.get("py") or {}
        chk("㉕ 名冊前綴命中 → py.roster_exempt(INFO 照列 · 帶名冊理由),不算紅",
            [e["file"] for e in py.get("roster_exempt") or []] == ["functional modules/VRN/nonstock_v0310/engine/X_v0310.py"]
            and all(e.get("why") for e in py.get("roster_exempt") or []), f"{py.get('roster_exempt')}")
        chk("㉖ 版號舊檔 + 同夾同族更高版號帶橋 → py.history(INFO 照列 · 記尾版)",
            py.get("history") == [{"file": "functional modules/VRN/Foo_v0100.py", "tail": "functional modules/VRN/Foo_v0102.py"}], f"{py.get('history')}")
        chk("㉗ 沒同族尾版 / 尾版也沒橋 → 照紅(負控)",
            sorted(py.get("missing") or []) == ["functional modules/VRN/Bar_v0100.py", "functional modules/VRN/Baz_v0100.py", "functional modules/VRN/Baz_v0101.py"]
            and py.get("state") == "RED" and s.get("state") == "RED", f"缺 {py.get('missing')}")
    real = scan()
    rpy = real.get("py") or {}
    chk("㉘ 實樹:PY 缺 0(名冊豁免與版史照列不消失 · 被指名的照紅)",
        real.get("state") != "NODATA" and not rpy.get("missing"),
        f"缺 {rpy.get('missing')} · 豁免 {[e['file'] for e in rpy.get('roster_exempt') or []]} · 版史 {[h['file'] for h in rpy.get('history') or []]} · 擋 {[b['file'] for b in rpy.get('history_blocked') or []]}")
    chk("㉙ 各層 scan 同一把尺(v0101 … v0105 都讀本版)",
        V0101.scan is scan and PRIOR.scan is scan and PRIOR.PRIOR.scan is scan and PRIOR.PRIOR.PRIOR.scan is scan and PRIOR.PRIOR.PRIOR.PRIOR.scan is scan)
    ok = rc == 0 and all(results)
    print(f"  [計] {_STEM} {VERSION} 本版 {sum(results)}/{len(results)} · 前版 {'PASS' if rc == 0 else 'FAIL'} · 合計 {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    print(f"=== Celeritas 產出契約閘 {VERSION}(薄尾 · PY 名冊豁免 INFO · 版史 INFO · 執法 L102)===")
    return report()


if __name__ == "__main__":
    raise SystemExit(main())
