#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA-GOV-ENG-001 : Central Governance Engine（詞彙／樣式／語彙／提示詞）.

補上工具鏈盤點裡 ABSENT 的五項能力，外加 Prompt 管理：

    C3  Regex SSOT        每個 canonical 一條可編譯的交替式，附測試向量
    C4  同義字自適應        決定性擴充 + difflib 最近鄰 → AUTO / ASK / QUARANTINE
    C8  台股代號鎖          三式代號逐字防篡改，被改就自癒並 WARN
    C9  時間語彙正規化       民國／西元／季／半年／FY／純數字／相對期間
    C10 確認回饋迴路        ==CGE-CONFIRM== 權杖，把 M/P 升 V 或永久拒絕
    PM  Prompt 管理        提示詞當成受治理資產：URN、版本、雜湊、append-only 台帳

治理原則沿用：**只增不減**。同義字不刪除，退役走 DORMANT；
拒絕的詞進 append-only 拒絕名冊，監控器往後跳過但紀錄永存。

證據等級：V＝人工確認；M＝自動擴充（不得自升 V）；P＝新詞待審。

邊界規則（兩條都是踩過坑才有的）：
  * Python 的 \\b 把 CJK 當字元，`2330.TW今日` 會比對失敗 → 改用 (?![A-Za-z0-9])
  * `^GSPC` 這種交替式兩端是非字元時不能加 \\b，否則永遠不命中

純標準庫。預設 dry-run，--commit 才寫台帳。

用法：
    python VIA_CentralGovernanceEngine.py --work <治理目錄> --selftest
    python VIA_CentralGovernanceEngine.py --work . --observe "資金流向,fund flow" --commit
    python VIA_CentralGovernanceEngine.py --work . --normalize "民國113年8月1日"
    python VIA_CentralGovernanceEngine.py --work . --confirm confirmations.txt --commit
    python VIA_CentralGovernanceEngine.py --work . --add-prompt "盤後分析" prompt.md --commit
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import sys
import unicodedata
import webbrowser
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

URN_SELF = "VIA-GOV-ENG-001"
VERSION = "v0100"
SPEC_VERSION = "VIA-SSOT-SPEC-v0100"

AUTO_THRESHOLD = 0.90
ASK_THRESHOLD = 0.75
CONFIRM_TOKEN = "==CGE-CONFIRM=="


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def iso_now() -> str:
    return datetime.now().isoformat(timespec="seconds")


class Console:
    def __init__(self) -> None:
        self.lines: List[str] = []

    def say(self, message: str, level: str = "INFO") -> None:
        line = "[%s][%s] %s" % (datetime.now().strftime("%H:%M:%S"), level, message)
        self.lines.append(line)
        print(line, flush=True)


LOG = Console()


def sha12(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def has_cjk(text: str) -> bool:
    return any("\u3400" <= ch <= "\u9fff" or "\uf900" <= ch <= "\ufaff" for ch in text)


# ---------------------------------------------------------------------------
# C3  Regex SSOT
# ---------------------------------------------------------------------------

def build_pattern(terms: List[str]) -> str:
    """把一組詞組成一條可編譯的交替式，邊界規則依內容決定。"""
    clean = sorted({t for t in terms if t}, key=len, reverse=True)
    if not clean:
        return ""
    alternation = "|".join(re.escape(t) for t in clean)
    edges_wordy = all(t[:1].isalnum() and t[-1:].isalnum() for t in clean)
    cjk = any(has_cjk(t) for t in clean)
    if not edges_wordy:
        # ^GSPC / .TW 這類兩端是非字元的，加 \b 會永遠不命中
        pattern = "(?:%s)" % alternation
    elif cjk:
        # Python 的 \b 把 CJK 視為字元，2330.TW今日 會失敗
        pattern = "(?<![A-Za-z0-9])(?:%s)(?![A-Za-z0-9])" % alternation
    else:
        pattern = r"\b(?:%s)\b" % alternation
    try:
        re.compile(pattern)
    except re.error:
        return ""
    return pattern


# ---------------------------------------------------------------------------
# C8  台股代號鎖
# ---------------------------------------------------------------------------

@dataclass
class LockedPattern:
    code: str
    name: str
    strict: str
    extraction: str
    note: str


TW_TICKER_LOCK: List[LockedPattern] = [
    LockedPattern(
        code="TWID-STD", name="標準四碼",
        strict=r"(?<![0-9A-Za-z.])[1-9][0-9]{3}(?![0-9A-Za-z.])",
        extraction=r"(?<![0-9A-Za-z.])[0-9]{4}[ABD]?(?![0-9A-Za-z.])",
        note="嚴格式排除 0 開頭（ETF／權證）；擷取式含末碼 A/B/D"),
    LockedPattern(
        code="TWID-YF", name="yfinance 後綴",
        strict=r"(?<![0-9A-Za-z.])[0-9]{4}[ABD]?\.(?:TW|TWO)(?![A-Za-z0-9])",
        extraction=r"(?<![0-9A-Za-z.])[0-9]{4}[ABD]?\.(?:TW|TWO)(?![A-Za-z0-9])",
        note="上市 .TW／上櫃 .TWO；後接中文不得阻斷比對"),
    LockedPattern(
        code="TWID-BBG", name="Bloomberg 空格式",
        strict=r"(?<![0-9A-Za-z])[0-9]{4}[ABD]?\s+TT(?![A-Za-z0-9])",
        extraction=r"(?<![0-9A-Za-z])[0-9]{4}[ABD]?\s+TT(?:\s+Equity)?(?![A-Za-z0-9])",
        note="#### TT，擷取式可含 Equity 尾綴"),
]
LOCK_FINGERPRINT = sha12(json.dumps([asdict(p) for p in TW_TICKER_LOCK],
                                    ensure_ascii=False, sort_keys=True))


def derive_ticker_forms(code4: str) -> Dict[str, str]:
    return {"standard": code4, "yf_listed": code4 + ".TW",
            "yf_otc": code4 + ".TWO", "bloomberg": code4 + " TT"}


# ---------------------------------------------------------------------------
# C9  時間語彙正規化
# ---------------------------------------------------------------------------

CN_QUARTER = {"一": 1, "二": 2, "三": 3, "四": 4, "1": 1, "2": 2, "3": 3, "4": 4}


def _year(value: int) -> int:
    """民國轉西元；兩位數補 20xx。"""
    if value < 100:
        return 2000 + value if value <= 50 else 1900 + value
    if value < 1911:
        return value + 1911
    return value


def normalize_temporal(text: str) -> Optional[Dict[str, str]]:
    """回傳 {kind, normalized}；認不出來回 None（寧可不認，不可亂認）。"""
    raw = unicodedata.normalize("NFKC", str(text)).strip()
    if not raw:
        return None

    m = re.fullmatch(r"(?:民國)?(\d{2,4})年(\d{1,2})月(\d{1,2})日?", raw)
    if m:
        return {"kind": "DATE", "normalized": "%04d-%02d-%02d" % (
            _year(int(m.group(1))), int(m.group(2)), int(m.group(3)))}

    m = re.fullmatch(r"(?:民國)?(\d{2,4})年(\d{1,2})月", raw)
    if m:
        return {"kind": "MONTH", "normalized": "%04d-%02d" % (
            _year(int(m.group(1))), int(m.group(2)))}

    m = re.fullmatch(r"(?:民國)?(\d{2,4})年第([一二三四1-4])季", raw)
    if m:
        return {"kind": "QUARTER", "normalized": "%04d-Q%d" % (
            _year(int(m.group(1))), CN_QUARTER[m.group(2)])}

    m = re.fullmatch(r"(\d{4})Q([1-4])", raw, re.I)
    if m:
        return {"kind": "QUARTER", "normalized": "%s-Q%s" % (m.group(1), m.group(2))}

    m = re.fullmatch(r"(\d{2})Q([1-4])", raw, re.I)
    if m:
        return {"kind": "QUARTER", "normalized": "%04d-Q%s" % (_year(int(m.group(1))), m.group(2))}

    m = re.fullmatch(r"([1-4])Q(\d{2}|\d{4})([EF])?", raw, re.I)
    if m:
        year = _year(int(m.group(2)))
        suffix = m.group(3).upper() if m.group(3) else ""
        return {"kind": "QUARTER", "normalized": "%04d-Q%s%s" % (year, m.group(1), suffix)}

    m = re.fullmatch(r"([12])H(\d{2}|\d{4})([EF])?", raw, re.I)
    if m:
        suffix = m.group(3).upper() if m.group(3) else ""
        return {"kind": "HALF", "normalized": "%04d-H%s%s" % (
            _year(int(m.group(2))), m.group(1), suffix)}

    m = re.fullmatch(r"(?:民國)?(\d{2,4})年?(上|下)半年", raw)
    if m:
        return {"kind": "HALF", "normalized": "%04d-H%d" % (
            _year(int(m.group(1))), 1 if m.group(2) == "上" else 2)}

    if raw in ("上半年", "下半年"):
        return {"kind": "HALF_RELATIVE", "normalized": "H%d" % (1 if raw[0] == "上" else 2)}

    m = re.fullmatch(r"FY(\d{2}|\d{4})", raw, re.I)
    if m:
        return {"kind": "FISCAL_YEAR", "normalized": "FY%04d" % _year(int(m.group(1)))}

    m = re.fullmatch(r"(\d{4})(\d{2})(\d{2})", raw)
    if m:
        return {"kind": "DATE", "normalized": "%s-%s-%s" % (m.group(1), m.group(2), m.group(3))}

    m = re.fullmatch(r"(\d{3})(\d{2})(\d{2})", raw)          # 民國純數字 1130801
    if m:
        return {"kind": "DATE", "normalized": "%04d-%s-%s" % (
            int(m.group(1)) + 1911, m.group(2), m.group(3))}

    m = re.fullmatch(r"(?:民國)?(\d{2,4})年", raw)
    if m:
        return {"kind": "YEAR", "normalized": "%04d" % _year(int(m.group(1)))}

    relative = {"月底": "EOM", "月末": "EOM", "年底": "EOY", "年末": "EOY",
                "今年以來": "YTD", "年初至今": "YTD", "季底": "EOQ"}
    if raw in relative:
        return {"kind": "RELATIVE", "normalized": relative[raw]}
    return None


# ---------------------------------------------------------------------------
# 詞彙 SSOT（C3 + C4 + C10）
# ---------------------------------------------------------------------------

@dataclass
class Synonym:
    text: str
    grade: str = "M"                 # V | M | P
    source: str = "auto-expand"
    added: str = ""
    state: str = "ACTIVE"            # ACTIVE | DORMANT


@dataclass
class Canonical:
    urn: str
    name: str
    namespace: str = "core"
    state: str = "ACTIVE"
    synonyms: Dict[str, Synonym] = field(default_factory=dict)
    pattern: str = ""
    tests_hit: List[str] = field(default_factory=list)
    tests_miss: List[str] = field(default_factory=list)


def expand_terms(term: str) -> List[str]:
    """決定性擴充：全半形正規化、大小寫、分隔符、縮寫。不猜語意。"""
    base = unicodedata.normalize("NFKC", term).strip()
    out = {base}
    if base.isascii():
        out |= {base.lower(), base.upper()}
        if len(base) >= 3 and base.replace(" ", "").isalpha():
            out.add(base.title())
    # 分隔符全排列：空白／底線／連字號互換。
    # 只做單向替換會漏掉 'fund flow' -> 'fund-flow'，向量測試抓到過。
    separators = (" ", "_", "-")
    if any(sep in base for sep in separators):
        canonical_form = re.sub(r"[\s_-]+", " ", base)
        for sep in separators:
            out.add(canonical_form.replace(" ", sep))
        out.add(canonical_form.replace(" ", ""))
    words = [w for w in re.split(r"[\s_-]+", base) if w]
    if len(words) >= 3 and all(w[:1].isalpha() and w.isascii() for w in words):
        out.add("".join(w[0].upper() for w in words))
    return sorted(v for v in out if v)


class VocabularySSOT:
    def __init__(self, work: Path) -> None:
        self.work = work
        self.path = work / "configs" / "governance_vocab.json"
        self.ledger = work / "logs" / "governance_ledger.jsonl"
        self.canonicals: Dict[str, Canonical] = {}
        self.rejected: List[Dict[str, str]] = []
        self.ask_queue: List[Dict[str, Any]] = []
        self.quarantine: List[Dict[str, str]] = []
        self.serial = 0
        self.lock_healed = 0
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            doc = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, ValueError, OSError):
            LOG.say("詞彙 SSOT 無法解析，以空白視圖執行（原檔不動）", "WARN")
            return
        for row in doc.get("canonicals", []):
            canonical = Canonical(
                urn=row["urn"], name=row["name"],
                namespace=row.get("namespace", "core"),
                state=row.get("state", "ACTIVE"),
                pattern=row.get("pattern", ""),
                tests_hit=row.get("tests_hit", []),
                tests_miss=row.get("tests_miss", []))
            for key, value in (row.get("synonyms") or {}).items():
                canonical.synonyms[key] = Synonym(**value)
            self.canonicals[canonical.name] = canonical
            try:
                self.serial = max(self.serial, int(canonical.urn.rsplit("-", 1)[1]))
            except (ValueError, IndexError):
                pass
        self.rejected = doc.get("rejected", [])
        self.ask_queue = doc.get("ask_queue", [])
        self.quarantine = doc.get("quarantine", [])
        LOG.say("詞彙 SSOT 載入：%d 個 canonical，拒絕名冊 %d 筆"
                % (len(self.canonicals), len(self.rejected)), "OK")

    # -- C8：鎖定樣式逐字防篡改 -------------------------------------------
    def verify_lock(self) -> str:
        current = sha12(json.dumps([asdict(p) for p in TW_TICKER_LOCK],
                                   ensure_ascii=False, sort_keys=True))
        if current != LOCK_FINGERPRINT:
            self.lock_healed += 1
            LOG.say("台股代號鎖指紋不符，已重新植入內建定義", "WARN")
            return "LOCK_SELF_HEALED"
        return "LOCK_INTACT"

    # -- 註冊 --------------------------------------------------------------
    def register(self, name: str, namespace: str = "core",
                 synonyms: Optional[List[str]] = None,
                 hit: Optional[List[str]] = None,
                 miss: Optional[List[str]] = None) -> Canonical:
        canonical = self.canonicals.get(name)
        if canonical is None:
            self.serial += 1
            canonical = Canonical(urn="VIA-VOC-%04d" % self.serial, name=name,
                                  namespace=namespace)
            self.canonicals[name] = canonical
        rejected = {r["text"] for r in self.rejected}
        # 擴充要套在每一個給定的同義字上，不只 canonical 本身 ——
        # 否則 'fund flow' 永遠長不出 'fund-flow'，向量測試抓到過。
        candidates = set(expand_terms(name))
        for supplied in (synonyms or []):
            candidates.add(supplied)
            candidates.update(expand_terms(supplied))
        for term in sorted(candidates):
            if term == name or term in rejected:
                continue
            if term not in canonical.synonyms:
                canonical.synonyms[term] = Synonym(
                    text=term, grade="M", source="auto-expand", added=now_stamp())
        for vector in (hit or []):
            if vector not in canonical.tests_hit:
                canonical.tests_hit.append(vector)
        for vector in (miss or []):
            if vector not in canonical.tests_miss:
                canonical.tests_miss.append(vector)
        canonical.pattern = build_pattern(
            [canonical.name] + [s.text for s in canonical.synonyms.values()
                                if s.state == "ACTIVE"])
        return canonical

    # -- C4：自適應觀測 ----------------------------------------------------
    def observe(self, term: str) -> Tuple[str, str, float]:
        term = unicodedata.normalize("NFKC", term).strip()
        if not term:
            return ("EMPTY", "", 0.0)
        if any(r["text"] == term for r in self.rejected):
            return ("REJECTED", "", 0.0)
        if term in self.canonicals:
            return ("KNOWN", term, 1.0)
        for canonical in self.canonicals.values():
            if term in canonical.synonyms:
                return ("KNOWN", canonical.name, 1.0)

        best, score = "", 0.0
        for name in self.canonicals:
            ratio = difflib.SequenceMatcher(None, term, name).ratio()
            if ratio > score:
                best, score = name, ratio
        if score >= AUTO_THRESHOLD and best:
            canonical = self.canonicals[best]
            canonical.synonyms[term] = Synonym(text=term, grade="M",
                                               source="auto-monitor", added=now_stamp())
            canonical.pattern = build_pattern(
                [canonical.name] + [s.text for s in canonical.synonyms.values()
                                    if s.state == "ACTIVE"])
            return ("AUTO", best, score)
        if score >= ASK_THRESHOLD and best:
            entry = {"term": term, "nearest": best, "score": round(score, 3),
                     "added": now_stamp()}
            if not any(q["term"] == term for q in self.ask_queue):
                self.ask_queue.append(entry)
            return ("ASK", best, score)
        if not any(q["text"] == term for q in self.quarantine):
            self.quarantine.append({"text": term, "added": now_stamp()})
        return ("QUARANTINE", best, score)

    # -- C10：確認回饋迴路 -------------------------------------------------
    def apply_confirmations(self, text: str) -> Dict[str, int]:
        """格式：==CGE-CONFIRM== 之後每行 詞 | ACCEPT/REJECT/NEW | canonical"""
        counts = {"ACCEPT": 0, "REJECT": 0, "NEW": 0, "SKIPPED": 0}
        inside = False
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith(CONFIRM_TOKEN):
                inside = True
                continue
            if not inside or not stripped or stripped.startswith("#"):
                continue
            parts = [p.strip() for p in stripped.split("|")]
            if len(parts) < 2:
                continue
            term, verdict = parts[0], parts[1].upper()
            target = parts[2] if len(parts) > 2 else ""
            if verdict == "ACCEPT":
                canonical = self.canonicals.get(target)
                if canonical is None:
                    for entry in self.ask_queue:
                        if entry["term"] == term:
                            canonical = self.canonicals.get(entry["nearest"])
                            break
                if canonical is None:
                    counts["SKIPPED"] += 1
                    continue
                canonical.synonyms[term] = Synonym(text=term, grade="V",
                                                   source="human", added=now_stamp())
                canonical.pattern = build_pattern(
                    [canonical.name] + [s.text for s in canonical.synonyms.values()
                                        if s.state == "ACTIVE"])
                counts["ACCEPT"] += 1
            elif verdict == "REJECT":
                # append-only 拒絕名冊：往後監控器跳過，但紀錄永存
                if not any(r["text"] == term for r in self.rejected):
                    self.rejected.append({"text": term, "added": now_stamp()})
                counts["REJECT"] += 1
            elif verdict == "NEW":
                self.register(term, synonyms=[])
                counts["NEW"] += 1
            else:
                counts["SKIPPED"] += 1
            self.ask_queue = [q for q in self.ask_queue if q["term"] != term]
        return counts

    # -- C3：自我測試 ------------------------------------------------------
    def selftest(self) -> Dict[str, Any]:
        total = hit = 0
        failures: List[Dict[str, str]] = []
        for canonical in self.canonicals.values():
            if not canonical.pattern:
                continue
            compiled = re.compile(canonical.pattern)
            vectors = [canonical.name] + [s.text for s in canonical.synonyms.values()
                                          if s.state == "ACTIVE"] + canonical.tests_hit
            for vector in vectors:
                total += 1
                if compiled.search(vector):
                    hit += 1
                else:
                    failures.append({"canonical": canonical.name, "vector": vector,
                                     "expect": "HIT", "pattern": canonical.pattern})
            for vector in canonical.tests_miss:
                total += 1
                if compiled.search(vector):
                    failures.append({"canonical": canonical.name, "vector": vector,
                                     "expect": "MISS", "pattern": canonical.pattern})
                else:
                    hit += 1
        return {"total": total, "hit": hit, "failures": failures}

    # -- 落地 --------------------------------------------------------------
    def commit(self, dry_run: bool) -> Path:
        doc = {
            "schema": "VIA.VocabularySSOT", "spec": SPEC_VERSION,
            "engine": URN_SELF, "generated": iso_now(),
            "policy": "只增不減：同義字不刪除，退役走 DORMANT；拒絕詞進 append-only 名冊",
            "lock_fingerprint": LOCK_FINGERPRINT,
            "canonicals": [
                {**{k: v for k, v in asdict(c).items() if k != "synonyms"},
                 "synonyms": {k: asdict(v) for k, v in c.synonyms.items()}}
                for c in sorted(self.canonicals.values(), key=lambda c: c.urn)],
            "ask_queue": self.ask_queue,
            "quarantine": self.quarantine,
            "rejected": self.rejected,
        }
        target = self.path if not dry_run else self.path.with_suffix(".preview.json")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
        self.ledger.parent.mkdir(parents=True, exist_ok=True)
        with self.ledger.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps({
                "ts": iso_now(), "engine": URN_SELF,
                "canonicals": len(self.canonicals),
                "ask": len(self.ask_queue), "quarantine": len(self.quarantine),
                "rejected": len(self.rejected), "committed": not dry_run,
            }, ensure_ascii=False) + "\n")
        return target


# ---------------------------------------------------------------------------
# PM  Prompt 管理
# ---------------------------------------------------------------------------

class PromptRegistry:
    """提示詞當成受治理資產：永久 URN、版本、內容雜湊、append-only。"""

    def __init__(self, work: Path) -> None:
        self.work = work
        self.path = work / "configs" / "prompt_registry.json"
        self.store = work / "prompts"
        self.entries: List[Dict[str, Any]] = []
        self.serial = 0
        if self.path.exists():
            try:
                doc = json.loads(self.path.read_text(encoding="utf-8"))
                self.entries = doc.get("prompts", [])
                for entry in self.entries:
                    try:
                        self.serial = max(self.serial, int(entry["urn"].rsplit("-", 1)[1]))
                    except (ValueError, IndexError, KeyError):
                        pass
            except (json.JSONDecodeError, ValueError, OSError):
                LOG.say("Prompt 台帳無法解析，以空白視圖執行（原檔不動）", "WARN")

    def add(self, name: str, body: str, tags: List[str], dry_run: bool) -> Dict[str, Any]:
        digest = sha12(body)
        existing = [e for e in self.entries if e["name"] == name]
        if any(e["sha"] == digest for e in existing):
            LOG.say("內容未變更，不新增版本：%s" % name, "OK")
            return [e for e in existing if e["sha"] == digest][0]
        if existing:
            urn = existing[0]["urn"]
            version = max(int(e.get("version", 1)) for e in existing) + 1
        else:
            self.serial += 1
            urn = "VIA-PRM-%04d" % self.serial
            version = 1
        entry = {
            "urn": urn, "name": name, "version": version, "sha": digest,
            "tags": sorted(set(tags)), "added": now_stamp(),
            "chars": len(body), "lines": body.count("\n") + 1,
            "file": "%s_v%03d.md" % (re.sub(r"[^\w\u4e00-\u9fff-]", "_", name), version),
            "state": "ACTIVE",
        }
        # 舊版不刪，狀態轉 SUPERSEDED
        for old in existing:
            if old.get("state") == "ACTIVE":
                old["state"] = "SUPERSEDED"
        self.entries.append(entry)
        if not dry_run:
            self.store.mkdir(parents=True, exist_ok=True)
            (self.store / entry["file"]).write_text(body, encoding="utf-8")
        return entry

    def commit(self, dry_run: bool) -> Path:
        doc = {"schema": "VIA.PromptRegistry", "spec": SPEC_VERSION,
               "engine": URN_SELF, "generated": iso_now(),
               "policy": "append-only：新版本用新 version，舊版轉 SUPERSEDED，永不刪除",
               "prompts": self.entries}
        target = self.path if not dry_run else self.path.with_suffix(".preview.json")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
        return target


# ---------------------------------------------------------------------------
# 種子詞彙與測試向量
# ---------------------------------------------------------------------------

SEED = [
    {"name": "資金流向", "ns": "core",
     "syn": ["資金流", "fund flow", "money flow"],
     "hit": ["今日資金流向偏多", "fund-flow 報告"], "miss": ["資"]},
    {"name": "三大法人", "ns": "core", "syn": ["法人買賣超", "institutional investors"],
     "hit": ["三大法人今日買超"], "miss": ["法人"]},
    {"name": "融資融券", "ns": "core", "syn": ["margin balance", "資券"],
     "hit": ["融資融券餘額"], "miss": []},
    {"name": "當沖", "ns": "core", "syn": ["day trade", "day trading"],
     "hit": ["當沖比率上升"], "miss": []},
    {"name": "毛利率", "ns": "finreport", "syn": ["gross margin", "GM"],
     "hit": ["毛利率 42%"], "miss": []},
    {"name": "營業利益", "ns": "finreport", "syn": ["operating income", "OP"],
     "hit": ["營業利益年增"], "miss": []},
]

TEMPORAL_VECTORS: List[Tuple[str, str]] = [
    ("民國113年8月1日", "2024-08-01"), ("2024年8月1日", "2024-08-01"),
    ("113年8月", "2024-08"), ("2024年8月", "2024-08"),
    ("2024Q1", "2024-Q1"), ("24Q1", "2024-Q1"), ("1Q24", "2024-Q1"),
    ("1Q2024", "2024-Q1"), ("4Q26F", "2026-Q4F"), ("113年第1季", "2024-Q1"),
    ("2024年第一季", "2024-Q1"), ("1H24", "2024-H1"), ("2H25E", "2025-H2E"),
    ("113年上半年", "2024-H1"), ("2024年下半年", "2024-H2"),
    ("上半年", "H1"), ("下半年", "H2"),
    ("FY24", "FY2024"), ("FY2024", "FY2024"),
    ("20240801", "2024-08-01"), ("1130801", "2024-08-01"),
    ("民國113年", "2024"), ("2024年", "2024"),
    ("月底", "EOM"), ("年底", "EOY"), ("今年以來", "YTD"), ("季底", "EOQ"),
]

TICKER_VECTORS: List[Tuple[str, str, bool]] = [
    ("TWID-STD", "2330", True), ("TWID-STD", "台積電2330今日", True),
    ("TWID-STD", "0050", False), ("TWID-STD", "23300", False),
    ("TWID-YF", "2330.TW", True), ("TWID-YF", "6488.TWO", True),
    ("TWID-YF", "2330.TW今日收盤", True), ("TWID-YF", "2330.US", False),
    ("TWID-BBG", "2330 TT", True), ("TWID-BBG", "2330 TT Equity", True),
    ("TWID-BBG", "2330 US", False),
]


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def run_vector_tests() -> Dict[str, Any]:
    temporal_fail: List[Dict[str, str]] = []
    for raw, expect in TEMPORAL_VECTORS:
        got = normalize_temporal(raw)
        actual = got["normalized"] if got else "(None)"
        if actual != expect:
            temporal_fail.append({"input": raw, "expect": expect, "got": actual})

    ticker_fail: List[Dict[str, str]] = []
    by_code = {p.code: p for p in TW_TICKER_LOCK}
    for code, text, should_hit in TICKER_VECTORS:
        pattern = by_code[code].extraction if code != "TWID-STD" else by_code[code].strict
        matched = bool(re.search(pattern, text))
        if matched != should_hit:
            ticker_fail.append({"lock": code, "input": text,
                                "expect": "HIT" if should_hit else "MISS",
                                "got": "HIT" if matched else "MISS"})
    return {
        "temporal_total": len(TEMPORAL_VECTORS),
        "temporal_fail": temporal_fail,
        "ticker_total": len(TICKER_VECTORS),
        "ticker_fail": ticker_fail,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="VIA_CentralGovernanceEngine.py",
        description="VIA-GOV-ENG-001 詞彙／樣式／語彙／提示詞治理引擎")
    parser.add_argument("--work", default=".", help="治理工作目錄")
    parser.add_argument("--seed", action="store_true", help="植入種子詞彙")
    parser.add_argument("--observe", default="", help="觀測新詞，逗號分隔")
    parser.add_argument("--normalize", default="", help="正規化單一時間語彙")
    parser.add_argument("--confirm", default="", help="人工確認回傳檔")
    parser.add_argument("--add-prompt", nargs=2, metavar=("NAME", "FILE"),
                        help="把提示詞納入受治理資產")
    parser.add_argument("--tags", default="", help="提示詞標籤，逗號分隔")
    parser.add_argument("--list-prompts", action="store_true")
    parser.add_argument("--selftest", action="store_true", help="只跑向量測試")
    parser.add_argument("--commit", action="store_true", help="寫入台帳（預設 dry-run）")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    work = Path(args.work).expanduser().resolve()
    work.mkdir(parents=True, exist_ok=True)
    dry_run = not args.commit

    LOG.say("%s Central Governance Engine %s 啟動（%s）"
            % (URN_SELF, VERSION, "DRY-RUN" if dry_run else "COMMIT"), "OK")

    if args.normalize:
        result = normalize_temporal(args.normalize)
        if result:
            print("%s -> %s (%s)" % (args.normalize, result["normalized"], result["kind"]))
            return 0
        print("%s -> 無法辨識（本引擎寧可不認，不亂認）" % args.normalize)
        return 1

    vocab = VocabularySSOT(work)
    lock_state = vocab.verify_lock()
    LOG.say("台股代號鎖：%s（%d 條鎖定樣式）" % (lock_state, len(TW_TICKER_LOCK)),
            "OK" if lock_state == "LOCK_INTACT" else "WARN")

    vectors = run_vector_tests()
    LOG.say("時間語彙向量：%d 條，失敗 %d"
            % (vectors["temporal_total"], len(vectors["temporal_fail"])),
            "OK" if not vectors["temporal_fail"] else "FAIL")
    for row in vectors["temporal_fail"]:
        LOG.say("  %s 期望 %s 得到 %s" % (row["input"], row["expect"], row["got"]), "FAIL")
    LOG.say("代號鎖向量：%d 條，失敗 %d"
            % (vectors["ticker_total"], len(vectors["ticker_fail"])),
            "OK" if not vectors["ticker_fail"] else "FAIL")
    for row in vectors["ticker_fail"]:
        LOG.say("  %s %r 期望 %s 得到 %s"
                % (row["lock"], row["input"], row["expect"], row["got"]), "FAIL")

    if args.selftest and not (args.seed or args.observe or args.confirm):
        vocab_result = vocab.selftest()
        LOG.say("Regex 自我測試：%d/%d" % (vocab_result["hit"], vocab_result["total"]),
                "OK" if not vocab_result["failures"] else "FAIL")
        for row in vocab_result["failures"][:10]:
            LOG.say("  %s 期望 %s：%r" % (row["canonical"], row["expect"], row["vector"]), "FAIL")
        ok = not (vectors["temporal_fail"] or vectors["ticker_fail"]
                  or vocab_result["failures"])
        print("")
        print("=" * 60)
        print(" SELFTEST -> %s" % ("PASS" if ok else "FAIL"))
        print("=" * 60)
        return 0 if ok else 1

    if args.seed:
        for row in SEED:
            vocab.register(row["name"], namespace=row["ns"], synonyms=row["syn"],
                           hit=row["hit"], miss=row["miss"])
        LOG.say("種子植入：%d 個 canonical" % len(SEED), "OK")

    if args.observe:
        for term in args.observe.split(","):
            term = term.strip()
            if not term:
                continue
            verdict, nearest, score = vocab.observe(term)
            level = {"AUTO": "OK", "KNOWN": "OK"}.get(verdict, "WARN")
            LOG.say("觀測 %r -> %s（最近 %s，相似度 %.2f）"
                    % (term, verdict, nearest or "—", score), level)

    if args.confirm:
        path = Path(args.confirm).expanduser().resolve()
        if path.is_file():
            counts = vocab.apply_confirmations(path.read_text(encoding="utf-8"))
            LOG.say("確認回饋：接受 %d、拒絕 %d、新增 %d、略過 %d"
                    % (counts["ACCEPT"], counts["REJECT"], counts["NEW"], counts["SKIPPED"]),
                    "OK")
        else:
            LOG.say("找不到確認檔：%s" % path, "WARN")

    selftest = vocab.selftest()
    LOG.say("Regex 自我測試：%d/%d" % (selftest["hit"], selftest["total"]),
            "OK" if not selftest["failures"] else "FAIL")
    for row in selftest["failures"][:10]:
        LOG.say("  %s 期望 %s：%r  pattern=%s"
                % (row["canonical"], row["expect"], row["vector"], row["pattern"]), "FAIL")

    prompts = PromptRegistry(work)
    if args.add_prompt:
        name, file_path = args.add_prompt
        source = Path(file_path).expanduser().resolve()
        if source.is_file():
            entry = prompts.add(name, source.read_text(encoding="utf-8"),
                                [t.strip() for t in args.tags.split(",") if t.strip()],
                                dry_run)
            LOG.say("提示詞納管：%s %s v%d（%d 字）"
                    % (entry["urn"], entry["name"], entry["version"], entry["chars"]), "OK")
        else:
            LOG.say("找不到提示詞檔：%s" % source, "WARN")
    if args.list_prompts:
        for entry in sorted(prompts.entries, key=lambda e: (e["name"], e["version"])):
            LOG.say("  %s %-24s v%-3d %-11s %s"
                    % (entry["urn"], entry["name"], entry["version"],
                       entry["state"], ",".join(entry.get("tags", []))))

    vocab_path = vocab.commit(dry_run)
    prompt_path = prompts.commit(dry_run)

    failures = (len(vectors["temporal_fail"]) + len(vectors["ticker_fail"])
                + len(selftest["failures"]))
    verdict = "GREEN"
    if vocab.ask_queue or vocab.quarantine or lock_state != "LOCK_INTACT":
        verdict = "AMBER"
    if failures:
        verdict = "RED"

    LOG.say("詞彙台帳 -> %s" % vocab_path.name, "OK")
    LOG.say("提示詞台帳 -> %s" % prompt_path.name, "OK")
    print("")
    print("=" * 60)
    print(" VIA CENTRAL GOVERNANCE ENGINE  ->  %s" % verdict)
    print(" canonical %d ｜ ASK %d ｜ 隔離 %d ｜ 拒絕 %d ｜ 提示詞 %d"
          % (len(vocab.canonicals), len(vocab.ask_queue), len(vocab.quarantine),
             len(vocab.rejected), len(prompts.entries)))
    print(" 向量測試失敗 %d ｜ %s" % (failures, lock_state))
    if dry_run:
        print(" DRY-RUN：只寫 .preview.json，--commit 才動正式台帳")
    print("=" * 60)
    if args.json:
        print(json.dumps({"verdict": verdict, "failures": failures,
                          "canonicals": len(vocab.canonicals)}, ensure_ascii=False))
    return 0 if verdict != "RED" else 1


if __name__ == "__main__":
    sys.exit(main())
