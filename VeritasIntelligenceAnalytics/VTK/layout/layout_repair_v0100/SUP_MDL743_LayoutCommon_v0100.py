"""Shared geometry and source references; no second PDF extraction engine.

SYSTEM MANAGER: private module of SUP_MDL743, configured by
VIA_Layout_Capabilities_SSOT_v0100.json. Original values are immutable evidence.
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
import copy
import hashlib
import json
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path
from statistics import median
from . import VIA_ACCEL

# def 01_PARAMETERS — thresholds and regex are owned by the one capability SSOT.
VIA = Path(__file__).resolve().parents[3]
SSOT_PATH = VIA / "supportive modules/registry/VIA_Layout_Capabilities_SSOT_v0100.json"
SSOT = json.loads(SSOT_PATH.read_text(encoding="utf-8"))
PARAMS = SSOT["parameters"]
RX = {key: re.compile(value, re.I) for key, value in SSOT["regex"].items()}
# [VIA:ACCEL-BRIDGE] Runtime is inherited from the owning GenericLayoutHub.


def def_id(kind, *values):
    """Stable local evidence IDs; central component IDs are allocated by VCGC."""
    raw = json.dumps(values, ensure_ascii=False, sort_keys=True, default=str)
    return kind + "-" + hashlib.sha256(raw.encode()).hexdigest()[:16]


def def_box(items):
    boxes = [x["bbox"] for x in items]
    return [min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes)] if boxes else [0, 0, 0, 0]


def def_overlap(a, b, axis=0):
    intersection = max(0, min(a[axis+2], b[axis+2]) - max(a[axis], b[axis]))
    return intersection / max(min(a[axis+2]-a[axis], b[axis+2]-b[axis]), PARAMS["epsilon"])


def def_inside(inner, outer):
    x = (inner[0]+inner[2])/2; y = (inner[1]+inner[3])/2
    return outer[0] <= x <= outer[2] and outer[1] <= y <= outer[3]


def def_number(value):
    """Parse only explicit numeric tokens. Keep zero, blank and dash distinct."""
    text = re.sub(r"\s+", "", "" if value is None else str(value))
    if not RX["number"].fullmatch(text):
        return None
    if (text.startswith("(") and not text.endswith(")")) or (text.startswith("（") and not text.endswith("）")):
        return None
    text = text.replace(",", "").replace("，", "").replace("−", "-").replace("％", "%")
    negative = text.startswith(("(", "（")) and text.endswith((")", "）"))
    text = text.strip("()（）").rstrip("%")
    try:
        return -Decimal(text) if negative else Decimal(text)
    except InvalidOperation:
        return None


def def_join(left, right):
    """Preserve punctuation; only repair a clear ASCII word hyphenation."""
    if not left:
        return right
    if RX["hyphen_word"].search(left) and re.match(r"^[a-z]", right):
        return left[:-1] + right
    separator = " " if left[-1:].isascii() and right[:1].isascii() else ""
    return left + separator + right


def def_words(document):
    words = []
    for i, value in enumerate(document.get("native_geometry", [])):
        if not value.get("bbox") or not value.get("text"):
            continue
        w = copy.deepcopy(value)
        w["id"] = def_id("W", document["input_sha256"], i)
        w["size"] = w.get("metadata", {}).get("font_size") or (w["bbox"][3]-w["bbox"][1])
        words.append(w)
    return words


def def_word_rows(words):
    """Cluster baselines without concatenating words across a column gutter."""
    rows = []
    for word in sorted(words, key=lambda w: ((w["bbox"][1]+w["bbox"][3])/2, w["bbox"][0])):
        cy = (word["bbox"][1]+word["bbox"][3])/2
        tolerance = max(PARAMS["row_tolerance"], word["size"] * PARAMS["row_height_ratio"])
        if rows and abs(cy-rows[-1]["cy"]) <= tolerance:
            rows[-1]["words"].append(word)
            rows[-1]["cy"] = median((w["bbox"][1]+w["bbox"][3])/2 for w in rows[-1]["words"])
        else:
            rows.append({"cy": cy, "words": [word]})
    for row in rows:
        row["words"].sort(key=lambda w: w["bbox"][0])
        row["bbox"] = def_box(row["words"])
        row["text"] = " ".join(w["text"] for w in row["words"])
    return rows


def def_lines(document):
    """Reuse GLE's native lines; retain noise, source IDs, font and page geometry."""
    lines = []
    for page in document["layout"]["pages"]:
        for element in page["elements"]:
            if element.get("source_method") not in {"pymupdf.native_line", "tesseract.tsv_line"}:
                continue
            text = element.get("raw_text") or ""
            if not text.strip():
                continue
            font = element.get("font") or {}
            lines.append({"id": element["element_id"], "text": text, "raw_text": text,
                          "bbox": list(element["bbox_pt"]), "page": page["physical_page"],
                          "width": page["width"], "height": page["height"],
                          "size": font.get("size") or document["layout"].get("body_font_size") or PARAMS["font_fallback"],
                          "bold": bool(font.get("is_bold")), "font": font,
                          "base_role": element["subtype"], "source_ids": [element["element_id"]]})
    return lines


def def_context(asset, lines, assets):
    """At most five lines each way; clamp to same corridor and other assets."""
    box = asset["bbox"]; page = asset["page"]
    others = [x for x in assets if x["id"] != asset["id"] and x["page"] == page and
              def_overlap(box, x["bbox"]) >= PARAMS["corridor_overlap"]]
    lower = max((x["bbox"][3] for x in others if x["bbox"][3] <= box[1]), default=0)
    upper = min((x["bbox"][1] for x in others if x["bbox"][1] >= box[3]), default=float("inf"))
    candidates = [l for l in lines if l["page"] == page and def_overlap(l["bbox"], box) >= PARAMS["corridor_overlap"]]
    above = sorted([l for l in candidates if lower <= l["bbox"][3] <= box[1]], key=lambda l: l["bbox"][1], reverse=True)
    below = sorted([l for l in candidates if box[3] <= l["bbox"][1] < upper], key=lambda l: l["bbox"][1])
    result = {"above": [], "below": []}
    for direction, pool in (("above", above), ("below", below)):
        for line in pool[:PARAMS["context_lines"]]:
            text = line["text"].strip()
            if direction == "above" and RX["source"].match(text):
                break
            if direction == "below" and (RX["caption"].match(text) or RX["unit"].match(text)):
                break
            if line.get("role") in {"REPORT_TITLE", "H1", "H2", "H3"} and not RX["caption"].match(text):
                break
            result[direction].append({"id": line["id"], "text": text, "bbox": line["bbox"]})
            if direction == "above" and RX["caption"].match(text):
                break
    result["above"].reverse()
    return result


def def_assets(document):
    assets = []
    for page in document["layout"]["pages"]:
        for e in page["elements"]:
            if e["element_type"] in {"TABLE", "FIGURE"} and e["subtype"] == "CONTENT":
                assets.append({"id": e["element_id"], "kind": e["element_type"], "page": page["physical_page"],
                               "bbox": list(e["bbox_pt"]), "width": page["width"], "height": page["height"],
                               "source_ids": [e["element_id"]], "metadata": copy.deepcopy(e.get("metadata", {}))})
    return assets
