"""智慧資產庫轉換（把擷取內容 → 可查詢的智慧資產記錄）。

流程:實體萃取(代號/日期/金額/百分比/email/料號) → 型別化資產記錄
     → 擷取幅度 + 正確性驗證 → 資產庫(schema+records+stats) → 匯出。
純 stdlib、離線。
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

import hashlib
import re

# ── 實體樣式 ────────────────────────────────────────────
_PAT = {
    "ticker_tw": re.compile(r"(?<!\d)([1-9]\d{3})(?!\d)"),      # 台股 4 碼(首碼非0)
    "date": re.compile(r"\b(20\d{2}[-/年]\d{1,2}[-/月]\d{1,2}日?|\d{4}Q[1-4]|[1-4]Q\d{2})\b"),
    "amount": re.compile(r"(?<![\w.])[-+]?\d{1,3}(?:,\d{3})+(?:\.\d+)?|\b\d+\.\d{2}\b"),
    "percent": re.compile(r"[-+]?\d+(?:\.\d+)?%"),
    "email": re.compile(r"[\w\.\-]+@[\w\.\-]+\.\w+"),
    "partno": re.compile(r"\b[A-Z]{2,}[A-Z0-9]*-[A-Z0-9\-]{2,}\b"),   # 如 CP-GB200 / RES-0402-10K
}


def extract_entities(text: str) -> dict:
    out = {}
    for k, rx in _PAT.items():
        found = sorted(set(m.group(0) for m in rx.finditer(text)))
        if found:
            out[k] = found[:20]
    return out


def _kind(text, ents):
    if "email" in ents:
        return "communication"
    if "partno" in ents:
        return "bom_item"
    if "ticker_tw" in ents or "amount" in ents or "percent" in ents:
        return "financial"
    if "date" in ents:
        return "event"
    return "document"


def to_assets(units, source_default="ingest"):
    """每個擷取單元 → 智慧資產記錄(型別化)。"""
    assets = []
    for i, u in enumerate(units, 1):
        text = u.get("text", "") if isinstance(u, dict) else str(u)
        ents = extract_entities(text)
        aid = "AST-" + hashlib.blake2s(text.encode("utf-8"), digest_size=5).hexdigest().upper()
        quality = _quality(text, ents)
        assets.append({
            "asset_id": aid,
            "seq": f"AST-{i:05d}",
            "kind": _kind(text, ents),
            "text": text[:500],
            "entities": ents,
            "source": (u.get("source") if isinstance(u, dict) else None) or source_default,
            "hash": (u.get("hash") if isinstance(u, dict) else None) or aid,
            "quality": quality,
        })
    return assets


def _quality(text, ents):
    score = 0
    if text.strip():
        score += 40
    if ents:
        score += 30
    if len(text) > 40:
        score += 20
    if len(ents) >= 2:
        score += 10
    grade = "A" if score >= 90 else "B" if score >= 70 else "C" if score >= 50 else "D"
    return {"score": score, "grade": grade}


def validate_assets(units, assets):
    """擷取幅度 + 正確性驗證。"""
    # 幅度:每個非空單元都要產出一筆資產
    non_empty = sum(1 for u in units if (u.get("text") if isinstance(u, dict) else str(u)).strip())
    coverage = round(100 * len(assets) / non_empty, 1) if non_empty else 100.0
    # 正確性:每筆資產須有 id/source/非空 text
    bad = [a for a in assets if not a["asset_id"] or not a["source"] or not a["text"].strip()]
    # 幅度是否全覆蓋(無沉默漏抽)
    gap = non_empty - len(assets)
    return {"units": len(units), "non_empty": non_empty, "assets": len(assets),
            "coverage_pct": coverage, "coverage_gap": gap,
            "malformed": len(bad), "correctness_pass": len(bad) == 0,
            "verify_pass": gap == 0 and len(bad) == 0}


def build_asset_db(units):
    """組成智慧資產庫:schema + records + stats(可轉 Parquet/CSV/JSON)。"""
    assets = to_assets(units)
    val = validate_assets(units, assets)
    kinds = {}
    grades = {}
    for a in assets:
        kinds[a["kind"]] = kinds.get(a["kind"], 0) + 1
        grades[a["quality"]["grade"]] = grades.get(a["quality"]["grade"], 0) + 1
    return {
        "schema": ["asset_id", "seq", "kind", "text", "entities", "source", "hash", "quality"],
        "records": assets,
        "stats": {"total": len(assets), "by_kind": kinds, "by_grade": grades,
                  "validation": val},
    }


def assets_to_csv(assets, path):
    import csv
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["seq", "asset_id", "kind", "grade", "source", "entities", "text"])
        for a in assets:
            ent = "; ".join(f"{k}:{','.join(v)}" for k, v in a["entities"].items())
            w.writerow([a["seq"], a["asset_id"], a["kind"], a["quality"]["grade"],
                        a["source"], ent, a["text"][:200]])
    return path
