"""關鍵字自動生成（SSOT 自動維護核心）。

泛用的關鍵：不手刻關鍵字，而是從這家公司自己幾個月的資料挖出『有鑑別力』的詞，
提議成某分類桶的新關鍵字 → 人工核可 → 寫回 config（append-only）→ 下次歸類率自動上升。

鑑別力 = 這個詞在某桶的已分類事件裡常出現，但在別桶很少出現。
這樣挖出來的詞才是「能區分桶」的好關鍵字，不是到處都有的通用詞。

產出候選佇列(keyword_candidates)，附 桶/詞/分數/出現次數/證據，等核可。
保守：只提議、不自動加入；門檻可調；停用通用詞。
"""
from __future__ import annotations

import re
from collections import defaultdict, Counter

_CJK = r"\u4e00-\u9fff"
_TOKEN_RE = re.compile(rf"[A-Za-z][A-Za-z0-9]{{1,}}|[{_CJK}]{{2,4}}")

# 通用停用詞（到處都有，沒鑑別力）
_STOP = {"the", "and", "for", "with", "this", "that", "你好", "謝謝", "請問",
         "我們", "你們", "他們", "已經", "目前", "進度", "本週", "下週", "回覆",
         "確認", "問題", "需要", "處理", "提供", "報告"}


def _tokens(text: str):
    out = []
    for m in _TOKEN_RE.findall(text or ""):
        t = m.lower() if m.isascii() else m
        if t in _STOP or len(t) < 2:
            continue
        out.append(t)
        if not m.isascii():
            for i in range(len(m) - 1):
                bg = m[i:i + 2]
                if bg not in _STOP:
                    out.append(bg)
    return out


def generate_keyword_candidates(records, classification: dict, dim: str = "product",
                                min_count: int = 2, min_score: float = 0.6,
                                top_per_bucket: int = 8) -> list[dict]:
    """為某維度的各桶，從已分類事件挖鑑別性關鍵字候選。"""
    buckets = {k: v for k, v in classification.get(dim, {}).items() if not str(k).startswith("_")}
    if not buckets:
        return []

    existing = set()
    for label, kws in buckets.items():
        existing.add(str(label).lower())
        for kw in kws:
            existing.add(str(kw).lower())

    # 每桶的詞頻 + 全體詞頻
    bucket_tf = {label: Counter() for label in buckets}
    bucket_docs = {label: defaultdict(set) for label in buckets}
    total_tf = Counter()

    for rec in records:
        label = getattr(rec, dim, "")
        if not label or label not in buckets:
            continue
        toks = set(_tokens(" ".join([rec.title, rec.body])))
        for t in toks:
            bucket_tf[label][t] += 1
            bucket_docs[label][t].add(rec.uid)
            total_tf[t] += 1

    candidates = []
    for label in buckets:
        for term, c in bucket_tf[label].most_common(60):
            if c < min_count or term.lower() in existing:
                continue
            # 鑑別力：此桶出現次數 / 全體出現次數
            score = c / max(total_tf[term], 1)
            if score < min_score:
                continue
            candidates.append({
                "dim": dim, "bucket": label, "term": term,
                "count": c, "score": round(score, 2),
                "evidence": sorted(bucket_docs[label][term])[:5],
                "status": "pending",
            })
    # 每桶取前 N，整體依分數排序
    by_bucket = defaultdict(list)
    for c in candidates:
        by_bucket[c["bucket"]].append(c)
    out = []
    for label, lst in by_bucket.items():
        lst.sort(key=lambda x: (-x["score"], -x["count"]))
        out.extend(lst[:top_per_bucket])
    out.sort(key=lambda x: -x["score"])
    return out


def apply_approved(classification: dict, approved: list[dict]) -> dict:
    """把已核可的關鍵字寫回 classification（append-only，只增不減）。"""
    for a in approved:
        if a.get("status") != "confirmed":
            continue
        dim, bucket, term = a["dim"], a["bucket"], a["term"]
        buckets = classification.setdefault(dim, {})
        kws = buckets.setdefault(bucket, [])
        if term not in kws:
            kws.append(term)
    return classification
