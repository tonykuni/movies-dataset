#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Join wrapped lines and cut sentences. Does not invent a character."""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0111] 最新有版號的正本加速器(動態取最高 VeritasCeleritas_v####;退回鎖版 v1141)· 正本網路工具 VeritasAegisNexus_v1652(找不到 = 不改任何行為) =====
import importlib as _cb_il
import re as _cb_re
import sys as _cb_sys
from pathlib import Path as _cb_Path
_ACCEL, _ACCEL_VER = None, ""
_cb_p = _cb_Path(__file__).resolve()
while _cb_p.parent != _cb_p:
    if (_cb_p / "supportive modules").is_dir():
        _cb_sup = _cb_p / "supportive modules"
        _cb_c = sorted(list(_cb_sup.glob("VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")) + list(_cb_sup.glob("*/VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")),
                       key=lambda x: int(_cb_re.search(r"_v(\d{4})", x.name).group(1)))
        for _cb_d in [str(_cb_sup)] + ([str(_cb_c[-1].parent)] if _cb_c else []) + [str(x.parent) for x in list(_cb_sup.glob("*/VeritasAegisNexus_v1652.py"))[:1]]:
            if _cb_d not in _cb_sys.path:
                _cb_sys.path.insert(0, _cb_d)
        if _cb_c:
            try:
                _ACCEL, _ACCEL_VER = _cb_il.import_module(_cb_c[-1].stem), _cb_c[-1].stem
            except Exception:  # noqa: BLE001
                _ACCEL = None
        break
    _cb_p = _cb_p.parent
if _ACCEL is None:
    try:
        import VeritasCeleritas_v1141 as _ACCEL  # noqa: F401  退回鎖版
        _ACCEL_VER = "VeritasCeleritas_v1141"
    except Exception:  # noqa: BLE001
        _ACCEL = None


def _net():
    """正本網路工具(只在需要出網時載入;本引擎不出網)。"""
    try:
        import VeritasAegisNexus_v1652 as _NET  # noqa: WPS433
        return _NET
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:ACCEL-BRIDGE:END] =====

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
