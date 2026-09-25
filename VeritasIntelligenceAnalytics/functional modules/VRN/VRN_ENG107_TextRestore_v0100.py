#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Join wrapped lines and cut sentences. Does not invent a character."""
from __future__ import annotations

import re

_ENDS = "。！？!?；;"
_LABELS = (
    "目標價", "評等", "投資建議", "投資評等", "分析師", "日期",
    "Target Price", "Rating", "TP", "PT",
)
_BULLET = re.compile(r"^[➢◆●■▲►•\-]")
_WIDE = str.maketrans("０１２３４５６７８９．，：", "0123456789.,:")
_PROTECT = re.compile(r"\d+\.\d+|\d{4}\.TWO|\d{4}\.TW|20\d{2}[./-]\d{1,2}[./-]\d{1,2}")


def _clean(text: str) -> str:
    text = str(text or "").replace("\u3000", " ").replace("\u00ad", "").replace("\ufeff", "")
    return text.translate(_WIDE)


def _is_label(line: str) -> bool:
    stripped = line.strip()
    return any(stripped == label or stripped.startswith(label + " ") or stripped.startswith(label + ":") for label in _LABELS)


def restore(text: str) -> dict:
    lines = [line.strip() for line in _clean(text).splitlines() if line.strip()]
    out: list[str] = []
    joins = 0
    for line in lines:
        if not out:
            out.append(line)
            continue
        prev = out[-1]
        if prev[-1] in _ENDS or _BULLET.match(line) or _is_label(line):
            out.append(line)
            continue
        if _is_label(prev):
            out[-1] = prev + " " + line
        elif prev.endswith("-") and line[:1].isascii() and line[:1].isalpha():
            out[-1] = prev[:-1] + line
        elif prev[-1].isascii() and line[:1].isascii():
            out[-1] = prev + " " + line
        else:
            out[-1] = prev + line
        joins += 1
    merged = "\n".join(out)
    return {"text": merged, "joins": joins, "sentences": sentences(merged)}


def sentences(text: str) -> list[str]:
    raw = _clean(text).strip()
    if not raw:
        return []
    held: list[str] = []

    def park(match: re.Match) -> str:
        held.append(match.group(0))
        return f"\u0000{len(held) - 1}\u0000"

    parked = _PROTECT.sub(park, raw)
    parts = re.split(r"(?<=[。！？!?])\s*|(?<=[a-z])\.\s+(?=[A-Z])", parked)
    out = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        for index, token in enumerate(held):
            part = part.replace(f"\u0000{index}\u0000", token)
        out.append(part)
    return out


def selftest() -> int:
    joined = restore("我們維持\n買進。")
    card = restore("目標價\n1275")
    kept = sentences("收盤 2475.0 元。代號 2330.TW。")
    wide = restore("目標價 １２７５")
    ok = (
        joined["text"] == "我們維持買進。"
        and joined["joins"] == 1
        and card["text"] == "目標價 1275"
        and kept == ["收盤 2475.0 元。", "代號 2330.TW。"]
        and "1275" in wide["text"]
        and "１２" not in wide["text"]
    )
    print("  [OK]" if ok else f"  [FAIL] {joined} {card} {kept} {wide}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest())
