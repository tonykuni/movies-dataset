#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Use the recorded repair and the recorded result check.

Repair is ENG392's R0–R3 loop: a round that drops coverage is rolled back,
and a missing number is red. The cross-check is ENG082's bag and sequence
test, with the thresholds in the extraction-logic book. This file does not
carry a second copy of either rule. OCR is not run; a disagreement is sent
to review and the next ladder step is only named.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_PRIOR = HERE / "VRN_ENG115_HeaderFrameTemp_v0100.py"
_REPAIR = HERE / "VRN_ENG392_TextCompleteness_v0100.py"
_LOGIC = max(HERE.glob("VRN_ENG082_ExtractionLogic_v*.py"))


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


PRIOR = _load(_PRIOR, "vrn_eng115_v0100")
REPAIR = _load(_REPAIR, "vrn_eng392_repair")
LOGIC = _load(_LOGIC, "vrn_eng082_logic")
PARAMS = PRIOR.PARAMS + ("second_text",)


def _restore_left(blocks: list) -> dict:
    parts, rounds = [], []
    for block in blocks:
        src = str(block.get("text") or "")
        fixed, rec = REPAIR.repair_loop(src, src)
        parts.append(fixed.strip())
        rounds.extend(rec)
    kept = [row["round"] for row in rounds if row.get("kept")]
    return {"text": "\n".join(part for part in parts if part), "how": kept, "rounds": rounds}


def _source(params: dict) -> str:
    lines = []
    for block in params.get("blocks") or []:
        if block.get("text"):
            lines.append(str(block["text"]))
        for row in block.get("rows") or []:
            lines.extend("" if cell is None else str(cell) for cell in row)
    return "\n".join(lines)


def _restored(result: dict) -> str:
    lines = [((result.get("left") or {}).get("text") or "")]
    for item in result.get("frame_objects") or []:
        frame = item.get("frame")
        if frame is None:
            continue
        lines.extend(str(cell) for cell in item.get("columns") or [])
        for row in frame.itertuples(index=False):
            lines.extend("" if value is None else str(value) for value in row)
    return "\n".join(lines)


def verify(source: str, restored: str, second: str | None = None) -> dict:
    """Result check from the two books already on the tree. No new threshold."""
    cov, missing, _extra = REPAIR.coverage(source, restored)
    lost = REPAIR.numbers(source) - REPAIR.numbers(restored)
    quality = REPAIR.quality(restored)
    cross = LOGIC.xcheck(restored, second) if second else {"bag": None, "seq": None, "state": "SINGLE"}
    chars = len(REPAIR.norm(restored))
    verdict = LOGIC.verdict_of(chars, cross, True, "text")
    if not REPAIR.norm(source):
        page = "EMPTY"
    elif cov < REPAIR.COVER_MIN or lost:
        page = "PARTIAL"
    elif quality["grade"] == "D" and cov >= REPAIR.COVER_MIN:
        page = "REPAIRED"
    else:
        changed = restored != source
        page = "REPAIRED" if changed else "INTACT"
    if page == "EMPTY":
        status = "FAIL"
    elif page == "PARTIAL" or verdict == "FAIL":
        status = "FAIL"
    elif cross.get("state") == "DISAGREE":
        status = "REVIEW_REQUIRED"
    elif quality["grade"] in ("C", "D"):
        status = "WARN"
    elif page in ("INTACT", "REPAIRED") and verdict == "SUCCESS":
        status = "PASS"
    else:
        status = "WARN"
    ladder = (LOGIC.ssot().get("ladder") or [{}])[0]
    return {
        "page_state": page,
        "verdict": verdict,
        "status": status,
        "coverage": round(cov, 5),
        "cover_min": REPAIR.COVER_MIN,
        "numbers_missing": sorted(lost.elements())[:20],
        "quality": quality,
        "xcheck": cross,
        "min_chars": LOGIC.ssot().get("min_chars"),
        "chars": chars,
        "ocr": {
            "ran": False,
            "next": None if status == "PASS" else {"stage": ladder.get("stage"), "adapters": ladder.get("adapters")},
        },
    }


def run(params: dict | None) -> dict:
    if not isinstance(params, dict):
        return PRIOR.run(params)
    old = PRIOR._restore_left
    PRIOR._restore_left = _restore_left
    try:
        result = PRIOR.run(params)
    finally:
        PRIOR._restore_left = old
    if result.get("state") == "NODATA":
        return result
    card = verify(_source(params), _restored(result), params.get("second_text") or None)
    result["verify"] = card
    result["state"] = card["page_state"]
    if card["status"] != "PASS":
        result["summary"] = None
    return result


def selftest() -> int:
    fails = []

    def chk(name, ok):
        print(("  [OK] " if ok else "  [FAIL] ") + name)
        if not ok:
            fails.append(name)

    chk("舊尺仍過", PRIOR.selftest() == 0)
    fixed, rounds = REPAIR.repair_loop("營\u200b收 １００", "營\u200b收 １００")
    chk("R1 去零寬全形", "100" in fixed and "\u200b" not in fixed and rounds[-1]["kept"])
    chk("掉字退回", REPAIR.repair_loop("營收100", "營收100")[1][0]["kept"] and REPAIR.coverage("營收100", "營收")[0] < REPAIR.COVER_MIN)
    lost = verify("營收100", "營收")
    chk("少一個數字就紅", lost["status"] == "FAIL" and lost["numbers_missing"] == ["100"] and lost["ocr"]["ran"] is False)
    same = "台積電本季營收成長來自先進製程，毛利率持穩且資本支出高於去年同期水準，並再補充一句。"
    clash = verify(same, same, "zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz")
    chk("兩法不合送審", clash["status"] == "REVIEW_REQUIRED" and clash["xcheck"]["state"] == "DISAGREE" and clash["ocr"]["next"]["stage"] == "simple")
    import tempfile
    from pathlib import Path as P
    body = "\n".join([
        "台積電 2330",
        "我們維持買進評等，目標價為 1275 元。",
        "本季營收成長來自先進製程擴產。",
        "毛利率於本季持穩，優於同業。",
        "資本支出高於去年同期水準。",
    ])
    with tempfile.TemporaryDirectory() as td:
        result = run({
            "temp_dir": td,
            "blocks": [
                {"kind": "text", "x": 10, "y": 0, "text": body},
                {"kind": "table", "x": 400, "y": 20, "rows": [["科目", "2025"], ["營收", "100"]]},
            ],
        })
        verify_card = result.get("verify") or {}
        summary = result.get("summary") or {}
        chk("完整才摘要", verify_card.get("status") == "PASS" and summary.get("n") == 4 and "1275" in result["left"]["text"])
        held = run({
            "temp_dir": str(P(td) / "hold"),
            "second_text": "zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz",
            "blocks": [{"kind": "text", "x": 0, "y": 0, "side": "left", "text": body}],
        })
        chk("不合不摘要", (held.get("verify") or {}).get("status") == "REVIEW_REQUIRED" and held.get("summary") is None)
    print(f"  [計] {7 - len(fails)} 檢 OK · FAIL {len(fails)}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else run({}))
