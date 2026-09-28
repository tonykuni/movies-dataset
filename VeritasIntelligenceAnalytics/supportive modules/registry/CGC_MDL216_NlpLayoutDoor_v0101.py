#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL216_NlpLayoutDoor v0101 — NLP 與 Layout 的單一出口(尾版照 glob 取,門真的派工)

操作員 2026-09-28:「LAYOUT引擎 NLP引擎 都集合成單一出口 確認都有版本號」。
v0100 只「點名」路線,而且十個檔名全寫死(PINVER 10):orchestrator v0103(尾版已 v0105)、
layout 本體 v0104(尾版已 v0109)——門上寫的跟實際會跑的不是同一支,而且門不派工。
v0101:
  · 每條路線都照尾版律取(同族版號最大者);沒有一個版號寫在碼裡。
  · 門會派工:`nlp …` 交給 NLP 編排器尾版(SUP_MDL866)的 main;`layout …` 交給 VCGC 既有的
    layout 路線(同一條,不另寫一條)。操作員端單一出口 = `via-vcgc nlp …` / `via-vcgc layout …`
    / `via-vcgc door`(CGC_MDL149 v0165 把 nlp、door 兩個動詞交給本門)。
  · `routes` 卡:每條路線的尾版檔名、是否帶版號、與 VCGC 座位冊(VIA_VCGC_SubsystemSeat)的
    NLP/LAYOUT 是否一致;不一致或缺 = 指名,不解鎖。
  照舊不做:不刪舊 NLP/Layout 引擎、不把 OneEngine 1.9.0 當 PDF 路線、不下載模型或 tessdata、
  不從門寫財報庫、不動 intake macro_ssot。只收 VCGC 呼叫(VIA_FROM_VCGC=YES)。

用法(經 VCGC):
  via-vcgc door                          路線卡
  via-vcgc nlp text --text "…" --brief   NLP 編排器尾版
  via-vcgc layout --dir <夾>             Layout 審閱(VCGC 既有路線)
  python CGC_MDL216_NlpLayoutDoor_v0101.py --selftest
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
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
RULES = VIA / "supportive modules" / "70_VRN_Rules"
VRN = VIA / "functional modules" / "VRN"
NLP_SYS = VIA / "supportive modules" / "VIA_NLP_System"
STEM = "CGC_MDL216_NlpLayoutDoor"
VERSIONED = re.compile(r"_v\d{4}\.py$")

#: (face, role, folder, family stem) — the family stem is the only name written here
ROUTES = (
    ("nlp", "orchestrator", RULES, "SUP_MDL866_VIAUnifiedNLPOrchestrator"),
    ("nlp", "hub", RULES, "SUP_MDL744_NLPApplicationHub"),
    ("nlp", "file_bridge", VRN, "VRN_ENG087_NLPTextSummaryBridge"),
    ("nlp", "summary_support", VRN, "VRN_ENG066_NLPSupportHub"),
    ("nlp", "register", VRN, "VRN_ENG078_NLPOneBridge"),
    ("nlp", "manager", NLP_SYS, "NLP_SystemManager"),
    ("layout", "hub", RULES, "SUP_MDL743_GenericLayoutHub"),
)
SEAT_KEYS = {("nlp", "orchestrator"): "NLP", ("layout", "hub"): "LAYOUT"}


def _vnum(path: Path) -> int:
    match = re.search(r"_v(\d+)$", path.stem)
    return int(match.group(1)) if match else -1


def tail(folder: Path, stem: str) -> Path | None:
    hits = [p for p in folder.glob(stem + "_v*.py") if _vnum(p) >= 0]
    return max(hits, key=_vnum) if hits else None


def _prior() -> Path:
    mine = _vnum(Path(__file__))
    older = [p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < mine]
    return max(older, key=_vnum)


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def __getattr__(name: str):
    """v0100 public names stay reachable (its check() names the old pinned routes, kept as history)."""
    return getattr(_load(_prior(), "nlp_layout_door_prior"), name)


def seat() -> dict:
    hits = [p for p in HERE.glob("VIA_VCGC_SubsystemSeat_v*.json") if re.search(r"_v\d+$", p.stem)]
    book = max(hits, key=_vnum) if hits else None
    if not book:
        return {}
    try:
        return (json.loads(book.read_text(encoding="utf-8")).get("tails") or {})
    except (OSError, ValueError) as exc:
        return {"_error": f"{book.name}: {type(exc).__name__}"}


def routes(tails: dict | None = None) -> dict:
    tails = seat() if tails is None else tails
    rows, drift = [], []
    for face, role, folder, stem in ROUTES:
        p = tail(folder, stem)
        older = sorted(q.name for q in folder.glob(stem + "_v*.py") if p and _vnum(q) < _vnum(p))
        row = {"face": face, "role": role, "file": p.name if p else "ABSENT",
               "versioned": bool(p and VERSIONED.search(p.name)), "kept": len(older)}
        key = SEAT_KEYS.get((face, role))
        if key:
            row["seat"] = tails.get(key, "ABSENT")
            if row["seat"] != row["file"]:
                drift.append(f"{face}.{role}: 座位 {row['seat']} ≠ 尾版 {row['file']}")
        if not p or not row["versioned"]:
            drift.append(f"{face}.{role}: {row['file']}")
        rows.append(row)
    return {
        "via": "vcgc",
        "door": Path(__file__).stem,
        "enter": "via-vcgc",
        "exit": "via-vcgc",
        "verbs": {"nlp": "via-vcgc nlp <SUP_MDL866 參數>", "layout": "via-vcgc layout <參數>", "door": "via-vcgc door"},
        "routes": rows,
        "drift": drift,
        "oneengine": {"version": "1.9.0", "reads_pdf": False, "note": "registered, not the PDF path, models not downloaded"},
        "do_not": [
            "delete an older NLP or Layout engine",
            "use OneEngine 1.9.0 as the PDF path",
            "download a model or a tessdata pack",
            "write the financial database from this door",
            "edit intake macro_ssot",
        ],
        "next": "none" if not drift else "do not unlock; name the drift",
    }


def nlp(argv: list) -> int:
    """Run the NLP orchestrator tail's own main with these arguments (same process)."""
    p = tail(RULES, "SUP_MDL866_VIAUnifiedNLPOrchestrator")
    if not p:
        print(json.dumps({"via": "vcgc", "state": "ABSENT", "why": "SUP_MDL866 tail"}, ensure_ascii=False))
        return 2
    mod = _load(p, "nlp_door_" + p.stem)
    saved = sys.argv
    sys.argv = [str(p), *argv]
    try:
        return int(mod.main() or 0)
    finally:
        sys.argv = saved


def layout(argv: list) -> int:
    """Hand layout to the VCGC console tail's existing `layout` route (one route, not a second copy)."""
    console = tail(HERE, "CGC_MDL149_VeritasCentralGovernanceConsole")
    if not console:
        print(json.dumps({"via": "vcgc", "state": "ABSENT", "why": "VCGC console tail"}, ensure_ascii=False))
        return 2
    env = dict(os.environ, VIA_FROM_VCGC="YES")
    return subprocess.run([sys.executable, str(console), "layout", *argv], env=env).returncode


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
        return 2
    if args and args[0] == "nlp":
        return nlp(args[1:])
    if args and args[0] == "layout":
        return layout(args[1:])
    card = routes()
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card["next"] == "none" else 2


def selftest() -> int:
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + note) if note else ''}")

    keep = os.environ.pop("VIA_FROM_VCGC", None)
    chk("① 沒從 VCGC 進就拒(門 · nlp · layout 三條都一樣)",
        main([]) == 2 and main(["nlp", "status"]) == 2 and main(["layout", "--selftest"]) == 2)
    os.environ["VIA_FROM_VCGC"] = "YES"
    card = routes()
    chk("② 每條路線都照尾版律取且帶版號", all(r["versioned"] for r in card["routes"]),
        " · ".join(f"{r['face']}.{r['role']}={r['file']}" for r in card["routes"]))
    chk("③ NLP / LAYOUT 尾版與 VCGC 座位冊一致", card["next"] == "none", "; ".join(card["drift"]) or "0 漂移")
    src = Path(__file__).read_text(encoding="utf-8").split('"""', 2)[-1].split("def selftest")[0]
    chk("④ 碼裡沒有寫死任何版號檔名(docstring 與自測負控之外)", re.search(r"_v\d{4}\.py", src) is None)
    bad = routes({"NLP": "SUP_MDL866_VIAUnifiedNLPOrchestrator_v0001.py", "LAYOUT": "ABSENT"})
    chk("⑤ 負控:座位冊與尾版不一致 → 不解鎖且逐條指名", bad["next"] != "none" and len(bad["drift"]) == 2,
        "; ".join(bad["drift"]))
    chk("⑥ nlp 動詞真的派到 SUP_MDL866 尾版(selftest 旗標)", nlp(["--selftest"]) == 0)
    if keep is None:
        os.environ.pop("VIA_FROM_VCGC", None)
    else:
        os.environ["VIA_FROM_VCGC"] = keep
    ok = all(results)
    print(f"  {Path(__file__).stem} selftest {sum(results)}/{len(results)} {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
