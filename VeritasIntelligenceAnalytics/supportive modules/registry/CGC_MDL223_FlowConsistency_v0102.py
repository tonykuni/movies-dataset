#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL223 FlowConsistency v0102 — 薄尾:母子連接的契約針沿薄尾鏈找(不只看尾版檔面)。

v0101 → v0102(2026-10-06;操作員令「VRN 已是獨立系統、你負責;不重要或與現行程序衝突的就清」):
  問題:VDF_SystemManager v0131–v0146 是薄尾(PRIOR = 前一版,未覆寫的動詞全交前版),
        VCGC 入口契約 VIA_FROM_VCGC 寫在本體鏈(v0130 以前),尾版檔面沒有這個字 →
        v0101 只讀尾版檔面 → VDF 列 RED → 流程閘擋下所有 via-vcgc run(handoff check 也跑不了)。
  修法:管理者列(parent / child)三根針照舊,但 VIA_FROM_VCGC 准許「沿 PRIOR 鏈繼承」
        (判斷正本在座位探針 CGC_MDL222 v0101 的 inherited_contract,本檔直接用,不重寫;
        只認讀進來做比較的版 — 守衛或入口來源判斷,只設值 / 存值不算 → VDF 繼承來源 = v0128 獨立入口判斷):
        從尾版往舊版走,每一版都要有 PRIOR 連結才繼續;走到有針的版 = 繼承(列上記 inherited_from);
        鏈斷(某版沒有 PRIOR)前都沒針 = 照舊 RED。def main / def selftest 仍須在尾版檔面(入口是尾版自己的)。
  不放寬:針不改、族不改、工具列不改、閘的其餘判準(policy_step · book · seat · weak)一字不動;
        不在 VDF 塞假字串過閘。
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
import importlib.util
import os
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL223_FlowConsistency"
CONTRACT = "VIA_FROM_VCGC"


def _vnum(p) -> int:
    m = re.search(r"_v(\d+)\.py$", str(p))
    return int(m.group(1)) if m else -1


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
PRIOR = _load(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)
_FUNCTIONS_PRIOR = PRIOR.functions
NEEDLES = PRIOR.NEEDLES
FAMILIES = PRIOR.FAMILIES
PAGE = PRIOR.PAGE
SEAT = PRIOR.SEAT


def inherited_contract(folder, pattern: str, needle: str = CONTRACT):
    """唯一正本在座位探針 CGC_MDL222 v0101(PRIOR.PROBE = 探針尾版);本檔不另寫一份。"""
    probe = _load(PRIOR.PROBE, "probe_contract_for_" + Path(__file__).stem)
    return probe.inherited_contract(folder, pattern, needle)


def functions() -> list[dict]:
    rows = _FUNCTIONS_PRIOR()
    spec = {system: (folder, pattern) for system, folder, pattern in FAMILIES}
    for row in rows:
        if row.get("role") not in ("parent", "child") or row.get("lamp") == "GREEN" or row["system"] not in spec:
            continue
        own = [n for n in NEEDLES if n != CONTRACT]
        if CONTRACT in row["have"] or not all(n in row["have"] for n in own):
            continue                                      # 缺的是尾版自己的入口(main / selftest)→ 照舊 RED
        src = inherited_contract(*spec[row["system"]])
        if src is not None:
            row["have"] = list(NEEDLES)
            row["lamp"] = "GREEN"
            row["inherited_from"] = src.name
    return rows


PRIOR.functions = functions                               # 前版 gate() 取模組全域 functions → 換上本版


def gate() -> dict:
    card = PRIOR.gate()
    card["door"] = Path(__file__).stem
    return card


def write_page(card: dict) -> None:
    PRIOR.write_page(card)


def publish() -> dict:
    return PRIOR.publish()


def main() -> int:
    return PRIOR.main()


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {_STEM} v0102 · 薄尾自測(契約針沿 PRIOR 鏈繼承)===")
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        (d / "X_SystemManager_v0100.py").write_text("import os\ndef main():\n    if os.environ.get('VIA_FROM_VCGC') != 'YES':\n        return 2\ndef selftest(): pass\n", encoding="utf-8")
        (d / "X_SystemManager_v0101.py").write_text("PRIOR = object()\ndef main(): pass\ndef selftest(): pass\n", encoding="utf-8")
        (d / "X_SystemManager_v0102.py").write_text("PRIOR = object()\ndef main(): pass\ndef selftest(): pass\n", encoding="utf-8")
        got = inherited_contract(d, "X_SystemManager_v*.py")
        chk("① 薄尾鏈 v0102 → v0101 → v0100:繼承到本體的契約針", got is not None and got.name == "X_SystemManager_v0100.py", got)
        (d / "X_SystemManager_v0101.py").write_text("def main(): pass\ndef selftest(): pass\n", encoding="utf-8")
        chk("② 中間一版沒有 PRIOR(鏈斷)→ 不算繼承,照舊紅", inherited_contract(d, "X_SystemManager_v*.py") is None)
        (d / "Y_SystemManager_v0100.py").write_text("def main(): pass\n", encoding="utf-8")
        chk("③ 整條鏈都沒有針 → 不算繼承", inherited_contract(d, "Y_SystemManager_v*.py") is None)
        (d / "Z_SystemManager_v0100.py").write_text("def main(): pass\n", encoding="utf-8")
        (d / "Z_SystemManager_v0101.py").write_text("PRIOR = object()\nimport os\nos.environ['VIA_FROM_VCGC'] = 'YES'\ndef main(): pass\ndef selftest(): pass\n", encoding="utf-8")
        chk("③b 只設值(沒有讀進來比較)→ 不算繼承(PR #518 Codex P1)", inherited_contract(d, "Z_SystemManager_v*.py") is None)
    os.environ["VIA_VCGC_PUSH"] = "NO"
    os.environ["VIA_FROM_VCGC"] = "YES"
    card = gate()
    rows = {r["system"]: r for r in card["rows"]}
    managers = [r for r in card["rows"] if r["role"] in ("parent", "child")]
    chk("④ 管理者列五列全綠(VCGC · VDF · VRN · NLP · LAYOUT)", len(managers) == 5 and all(r["lamp"] == "GREEN" for r in managers),
        [(r["system"], r["lamp"], r.get("inherited_from", "")) for r in managers])
    vdf = rows.get("VDF", {})
    vdf_text = (Path(FAMILIES[1][1]) / vdf.get("tail", "")).read_text(encoding="utf-8", errors="ignore") if vdf.get("tail") else ""
    chk("⑤ VDF 列綠,且照實標出契約來源(尾版自帶或繼承自哪一版)",
        vdf.get("lamp") == "GREEN" and (CONTRACT in vdf_text or bool(vdf.get("inherited_from"))), vdf.get("inherited_from") or "尾版自帶")
    chk("⑥ 管理者列不再出現在 missing(其餘判準 policy_step / book / seat 照前版算)",
        not any(m in ("VCGC", "VDF", "VRN", "NLP", "LAYOUT") for m in card["missing"]), card["missing"])
    chk("⑦ 工具列五列照舊", len([r for r in card["rows"] if r["role"] == "tool"]) == 5)
    chk("⑧ 門卡標本版", card.get("door") == Path(__file__).stem)
    good = all(ok)
    print(f"  [計] {_STEM} v0102 本版 {sum(ok)}/{len(ok)} · 閘 {'放行' if card['lock_success'] else '擋下 ' + ','.join(card['missing'])}"
          f" · {'PASS' if good else 'FAIL'}")
    if not good:
        return 1
    return PRIOR.selftest()


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
