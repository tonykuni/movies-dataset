"""分類層（多道遞進，目標：泛用地提高歸類率）。

單靠手刻關鍵字，歸類率上不去也不泛用。改成三道遞進，每筆事件依序嘗試：

  第1道 關鍵字/種子比對  —— 正規化後直接命中（最可靠）
  第2道 討論串傳播      —— 同一討論串(主旨去 Re:/Fw: + 參與者)只要有一筆分了類，
                          其餘未分類者繼承之（最適合幾個月的來回信件）
  第3道 最近桶模糊指派   —— 仍未分類者，用詞彙重疊度比對各分類桶，
                          超過門檻且領先第二名才指派；否則維持未分類（寧缺勿錯）

回傳每筆的分類來源(provenance)與整體歸類率，讓你看得到是哪一道救回來的。
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

import re
from collections import defaultdict, Counter

_CJK = r"\u4e00-\u9fff"
_TOKEN_RE = re.compile(rf"[A-Za-z][A-Za-z0-9]+|[{_CJK}]{{2,4}}")


def _norm_subject(s: str) -> str:
    s = re.sub(r"^(re|fw|fwd)[:：]\s*", "", (s or "").strip(), flags=re.IGNORECASE)
    s = re.sub(r"^(re|fw|fwd)[:：]\s*", "", s, flags=re.IGNORECASE)
    return s.strip().lower()


def _tokens(text: str) -> list[str]:
    out = []
    for m in _TOKEN_RE.findall(text or ""):
        if m.isascii():
            out.append(m.lower())
        else:
            # CJK：滑動 2-gram，增加覆蓋
            for i in range(len(m) - 1):
                out.append(m[i:i + 2])
    return out


def _kw_match(text_low: str, buckets: dict) -> str:
    for label, keywords in buckets.items():
        if str(label).startswith("_"):
            continue
        for kw in [label] + list(keywords):
            if str(kw).lower() in text_low:
                return label
    return ""


def classify_all(records, classification: dict, normalize_fn=None,
                 fuzzy_threshold: float = 0.18, advanced_dims=None) -> dict:
    """就地填入分類欄位；回傳 {dim: {kw, thread, fuzzy, unclassified, rate}}。

    advanced_dims：哪些維度套用第2/3道（討論串傳播+模糊）。預設 product/topic。
    狀態(status)是『狀態』非『主題』，不該跨討論串傳播，故只走第1道。
    """
    dims = [d for d in classification if not str(d).startswith("_")]
    if advanced_dims is None:
        advanced_dims = [d for d in dims if d in ("product", "topic")]
    prov = {d: {} for d in dims}        # uid -> 來源
    stats = {}

    # ---- 第1道：關鍵字 ----
    for rec in records:
        text = " ".join([rec.title, rec.body, rec.raw_keys])
        if normalize_fn:
            text = normalize_fn(text)
        low = text.lower()
        rec._cls_text = low             # 暫存供後續道使用
        for dim in dims:
            if getattr(rec, dim, ""):
                prov[dim][rec.uid] = "source"   # 來源已給
                continue
            hit = _kw_match(low, classification[dim])
            if hit:
                setattr(rec, dim, hit)
                prov[dim][rec.uid] = "kw"

    # ---- 第2道：討論串傳播 ----
    threads = defaultdict(list)
    for rec in records:
        key = rec.thread_id or _norm_subject(rec.title)
        threads[key].append(rec)
    for dim in dims:
        if dim not in advanced_dims:
            continue
        for key, group in threads.items():
            if len(group) < 2:
                continue
            labels = [getattr(r, dim) for r in group if getattr(r, dim)]
            if not labels:
                continue
            majority = Counter(labels).most_common(1)[0][0]
            for r in group:
                if not getattr(r, dim):
                    setattr(r, dim, majority)
                    prov[dim][r.uid] = "thread"

    # ---- 第3道：最近桶模糊指派 ----
    for dim in dims:
        if dim not in advanced_dims:
            continue
        buckets = classification[dim]
        # 桶向量：標籤+關鍵字的 token 集
        bucket_tokens = {}
        for label, kws in buckets.items():
            if str(label).startswith("_"):
                continue
            toks = set(_tokens(label))
            for kw in kws:
                toks |= set(_tokens(str(kw)))
            bucket_tokens[label] = toks
        for rec in records:
            if getattr(rec, dim, ""):
                continue
            rt = set(_tokens(rec._cls_text))
            if not rt:
                continue
            scored = []
            for label, btoks in bucket_tokens.items():
                if not btoks:
                    continue
                overlap = len(rt & btoks)
                score = overlap / (len(btoks) ** 0.5 + 1e-9)
                scored.append((score, label))
            scored.sort(reverse=True)
            if scored and scored[0][0] >= fuzzy_threshold:
                # 需領先第二名（避免兩桶都沾一點就亂分）
                if len(scored) == 1 or scored[0][0] >= scored[1][0] * 1.3:
                    setattr(rec, dim, scored[0][1])
                    prov[dim][rec.uid] = "fuzzy"

    # ---- 統計 ----
    for dim in dims:
        c = Counter(prov[dim].get(r.uid, "unclassified") for r in records)
        total = len(records)
        classified = total - c.get("unclassified", 0)
        stats[dim] = {
            "kw": c.get("kw", 0) + c.get("source", 0),
            "thread": c.get("thread", 0),
            "fuzzy": c.get("fuzzy", 0),
            "unclassified": c.get("unclassified", 0),
            "rate": round(100 * classified / total, 1) if total else 100.0,
        }

    for rec in records:
        if hasattr(rec, "_cls_text"):
            del rec._cls_text
    return {"provenance": prov, "stats": stats}


# 向後相容：單筆分類（第1道）
def seed_buckets_from_data(records, classification: dict, dims=("product", "topic")) -> dict:
    """泛用自舉：分類桶從『來源已提供的值』自動長出來，不靠手刻。

    例：Excel 的「產品線」欄、PLM 的 Product 欄已標了「電源供應器」，
    就自動把它建成一個桶（標籤本身即關鍵字）。之後關鍵字生成再為它長出 PSU/LLC… 等別名。
    這是『泛用』的根：同一引擎，桶與關鍵字都由各公司自己的資料決定。
    """
    for dim in dims:
        buckets = classification.setdefault(dim, {})
        seen = {str(v).strip() for r in records
                for v in [getattr(r, dim, "")] if str(v).strip()}
        for label in seen:
            if label not in buckets and not label.startswith("_"):
                buckets[label] = []     # 標籤即關鍵字；別名待生成
    return classification


def classify_record(rec, classification: dict, normalize_fn=None) -> None:
    text = " ".join([rec.title, rec.body, rec.raw_keys])
    if normalize_fn:
        text = normalize_fn(text)
    low = text.lower()
    for dim, buckets in classification.items():
        if str(dim).startswith("_") or getattr(rec, dim, ""):
            continue
        hit = _kw_match(low, buckets)
        if hit and hasattr(rec, dim):
            setattr(rec, dim, hit)
