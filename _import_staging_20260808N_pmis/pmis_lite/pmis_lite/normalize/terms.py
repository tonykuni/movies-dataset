"""術語正規化 SSOT（同義字 / 簡寫對照）。

解決：行內人寫信滿是簡寫與專有名詞，系統難識別、新人壓力大。

安全設計（對應你「只增不減 / append-only」治理）：
  種子層  config 已知對照（PSU→電源供應器…）
  探勘層  掃全部文字，用三種訊號找『候選同義對』：
            1) 頻率   ：常出現、像簡寫的 token（全大寫英文縮寫、被括號標註者）
            2) 共現   ：候選詞與某正規詞常出現在同一筆 → 疑似同義
            3) 近似   ：與正規詞字串相近（錯字/全半形/大小寫）
  候選佇列 每個候選附『信心分數 + 證據（出現在哪幾筆）』
  人工核可 confirm / reject / rewrite —— 系統不自作主張合併
  鎖定    核可後寫入正規化 SSOT，只增不減

預設保守：寧可少併也不要錯併。沒把握的，兩個詞先各自存在。
"""
from __future__ import annotations

import json
import os
import re
from collections import defaultdict
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Iterable


# 像「行內簡寫」的樣子：2-6 個英文字母全大寫(可含數字)，或被全形括號標註的詞
_ABBR_RE = re.compile(r"\b([A-Z][A-Z0-9]{1,5})\b")
_PAREN_RE = re.compile(r"[（(]\s*([^（）()]{1,20}?)\s*[）)]")

# 內建停用清單：常見『組織單位/角色/通用』縮寫，本質不是領域術語同義詞。
# 這些就算共現再高也不該被當成產品/專案的同義詞 → 直接排除，避免過度合併。
DEFAULT_STOPWORDS = {
    "RD", "PM", "QA", "QC", "PE", "ME", "EE", "IE", "HR", "IT", "MFG",
    "SCM", "BU", "BG", "CEO", "CTO", "VP", "ALL", "FYI", "TBD", "ASAP",
    "OK", "NG", "PO", "PR", "BOM", "ECN", "ECR",
}


@dataclass
class Candidate:
    surface: str            # 候選詞（信裡看到的簡寫/別名）
    canonical: str          # 提議對應到的正規詞
    confidence: float       # 信心分數 0-1
    signals: list[str] = field(default_factory=list)   # 命中哪些訊號
    evidence: list[str] = field(default_factory=list)  # 出現在哪幾筆（uid/source_ref）
    status: str = "pending"  # pending / confirmed / rejected


class TermStore:
    """正規化 SSOT 本體：正規詞 -> 同義集合。append-only。"""

    def __init__(self, seed: dict[str, list[str]] | None = None):
        # surface(小寫) -> canonical
        self._map: dict[str, str] = {}
        self._canon: set[str] = set()
        if seed:
            for canon, aliases in seed.items():
                self.add(canon, canon)
                for a in aliases:
                    self.add(canon, a)

    def add(self, canonical: str, surface: str) -> None:
        self._canon.add(canonical)
        self._map[surface.strip().lower()] = canonical

    def normalize(self, text: str) -> str:
        """把文字中的已知別名換成正規詞（只換已核可的）。"""
        out = text
        for surface, canon in self._map.items():
            if surface and surface != canon.lower():
                out = re.sub(re.escape(surface), canon, out, flags=re.IGNORECASE)
        return out

    def knows(self, surface: str) -> bool:
        return surface.strip().lower() in self._map

    @property
    def canonicals(self) -> set[str]:
        return set(self._canon)

    def save(self, path: str) -> None:
        grouped: dict[str, list[str]] = defaultdict(list)
        for surface, canon in self._map.items():
            if surface != canon.lower():
                grouped[canon].append(surface)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(grouped, f, ensure_ascii=False, indent=2)


def _similar(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def mine_candidates(
    records: Iterable,
    store: TermStore,
    min_frequency: int = 2,
    min_confidence: float = 0.55,
    stopwords: set[str] | None = None,
) -> list[Candidate]:
    """探勘候選同義對。records 需有 .title .body .raw_keys .uid 屬性。"""
    stop = {s.upper() for s in (stopwords or set())} | DEFAULT_STOPWORDS
    # 收集候選詞 -> 出現的筆 + 同筆出現的正規詞
    freq: dict[str, int] = defaultdict(int)
    where: dict[str, list[str]] = defaultdict(list)
    cooccur: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    paren_pairs: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    canon_list = list(store.canonicals)

    for rec in records:
        text = " ".join([getattr(rec, "title", ""), getattr(rec, "body", ""), getattr(rec, "raw_keys", "")])
        ref = getattr(rec, "uid", "") or getattr(rec, "source_ref", "")

        # 1) 全大寫縮寫候選
        abbrs = set(_ABBR_RE.findall(text))
        # 2) 括號標註： 諧振轉換器(LLC) 這種 —— 括號內外互為別名
        for inner in _PAREN_RE.findall(text):
            before = text.split(f"({inner}")[0] if f"({inner}" in text else text.split(f"（{inner}")[0]
            tail = before.strip().split()[-1] if before.strip() else ""
            if tail and inner:
                paren_pairs[inner.strip()][tail.strip()] += 1
                abbrs.add(inner.strip())

        for ab in abbrs:
            if store.knows(ab) or ab.upper() in stop:
                continue
            freq[ab] += 1
            if ref:
                where[ab].append(ref)
            for canon in canon_list:
                if canon.lower() in text.lower():
                    cooccur[ab][canon] += 1

    candidates: list[Candidate] = []
    seen: set[tuple[str, str]] = set()

    for surface, n in freq.items():
        if n < min_frequency and surface not in paren_pairs:
            continue

        best_canon, best_conf, signals = None, 0.0, []

        # 訊號 a：括號標註（最強訊號）
        if surface in paren_pairs and paren_pairs[surface]:
            tgt = max(paren_pairs[surface], key=paren_pairs[surface].get)
            best_canon, best_conf = tgt, max(best_conf, 0.85)
            signals.append("括號標註")

        # 訊號 b：共現（弱證據，且加上『專一性』懲罰）
        # 若候選詞同時與多個正規詞共現 → 它八成不是任一者的同義詞（像通用詞），降信心。
        if surface in cooccur and cooccur[surface]:
            tgt = max(cooccur[surface], key=cooccur[surface].get)
            share = cooccur[surface][tgt] / max(freq[surface], 1)
            distinct = len(cooccur[surface])              # 與幾個不同正規詞共現
            specificity = 1.0 / distinct                  # 只跟一個共現才高
            conf = (0.4 + 0.25 * share) * specificity     # 共現上限明顯低於括號標註
            if conf > best_conf:
                best_canon, best_conf = tgt, conf
            signals.append(f"共現x{cooccur[surface][tgt]}/{distinct}類")

        # 訊號 c：字串近似
        for canon in canon_list:
            s = _similar(surface, canon)
            if s >= 0.8 and s > best_conf:
                best_canon, best_conf = canon, s
                signals.append(f"近似{s:.2f}")

        if best_canon and best_conf >= min_confidence and (surface, best_canon) not in seen:
            seen.add((surface, best_canon))
            candidates.append(Candidate(
                surface=surface,
                canonical=best_canon,
                confidence=round(best_conf, 2),
                signals=signals,
                evidence=where.get(surface, [])[:5],
            ))

    candidates.sort(key=lambda c: c.confidence, reverse=True)
    return candidates
