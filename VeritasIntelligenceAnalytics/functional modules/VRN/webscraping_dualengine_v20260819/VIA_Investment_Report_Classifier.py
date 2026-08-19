#!/usr/bin/env python3
from __future__ import annotations
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

SSOT_PATH = Path(__file__).with_name("VIA_Investment_Report_Type_SSOT.json")

@dataclass
class ReportClassification:
    report_type_code: str
    report_type_zh: str
    report_type_en: str
    report_scope: str
    confidence: float
    evidence: list[str]
    classifier_version: str

def def_load_report_type_ssot(path: Path = SSOT_PATH) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data.get("types"), dict) or data.get("default_type") not in data["types"]:
        raise ValueError("INVALID_REPORT_TYPE_SSOT")
    return data

def def_normalize_report_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip()).upper()

def def_classify_investment_report(title: str, content: str = "", ssot: dict[str, Any] | None = None) -> ReportClassification:
    ssot = ssot or def_load_report_type_ssot()
    title_norm = def_normalize_report_text(title)
    content_head = def_normalize_report_text(content[:3000])
    candidates = []
    for code, spec in ssot["types"].items():
        evidence = []
        for pattern in spec.get("patterns", []):
            if re.search(pattern, title_norm, re.I): evidence.append(f"TITLE:{pattern}")
            elif re.search(pattern, content_head, re.I): evidence.append(f"CONTENT:{pattern}")
        if evidence:
            title_hits = sum(x.startswith("TITLE:") for x in evidence)
            score = int(spec.get("priority", 0)) + title_hits * 25 + (len(evidence) - title_hits) * 8
            candidates.append((score, int(spec.get("priority", 0)), code, evidence))
    if candidates:
        score, _, code, evidence = max(candidates, key=lambda x: (x[0], x[1], x[2]))
        confidence = min(0.99, 0.55 + 0.12 * sum(x.startswith("TITLE:") for x in evidence) + 0.06 * sum(x.startswith("CONTENT:") for x in evidence))
    else:
        code, evidence, confidence = ssot["default_type"], ["NO_RULE_MATCH"], 0.20
    spec = ssot["types"][code]
    return ReportClassification(code, spec["zh"], spec["en"], spec["scope"], round(confidence, 2), evidence, ssot["schema_version"])

def def_split_morning_brief(title: str, content: str, parent_url: str = "", ssot: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    ssot = ssot or def_load_report_type_ssot()
    parent = def_classify_investment_report(title, content, ssot)
    if parent.report_type_code != "DAILY_MORNING_BRIEF": return []
    matches = []
    for pattern in ssot.get("morning_section_patterns", []): matches.extend(re.finditer(pattern, content, re.I))
    matches = sorted({(m.start(), m.end(), m.group(0).strip()) for m in matches})
    sections = []
    for index, (start, end, heading) in enumerate(matches):
        next_start = matches[index + 1][0] if index + 1 < len(matches) else len(content)
        body = content[end:next_start].strip()
        if len(body) < 40: continue
        ticker_match = re.search(r"(?<!\d)(\d{4})(?:\.(?:TWO|TW)|\s+TT)?(?!\d)", heading, re.I)
        child_type = def_classify_investment_report(heading, body, ssot)
        if child_type.report_type_code in {"UNCLASSIFIED_RESEARCH", "DAILY_MORNING_BRIEF"}:
            memo = ssot["types"]["RESEARCH_MEMO"]
            child_type = ReportClassification("RESEARCH_MEMO", memo["zh"], memo["en"], memo["scope"], 0.65,
                                               ["PARENT_DAILY_MORNING_BRIEF", "SECTION_BOUNDARY"], ssot["schema_version"])
        child_id = hashlib.sha256(f"{parent_url}|{index}|{heading}".encode()).hexdigest()
        sections.append({"child_id": child_id, "parent_url": parent_url, "section_index": index,
                         "heading": heading, "ticker_raw": ticker_match.group(1) if ticker_match else "",
                         "content": body, "classification": asdict(child_type)})
    return sections

def def_self_test() -> None:
    cases = {
        "【元大投顧晨訊】2026/08/20 盤前重點": "DAILY_MORNING_BRIEF",
        "台積電 2Q26 Earnings Preview": "EARNINGS_PREVIEW",
        "半導體產業 2027 展望": "INDUSTRY_OUTLOOK",
        "2027 年度投資展望": "ANNUAL_OUTLOOK",
        "台積電法說會後財報評析": "EARNINGS_REVIEW",
        "研究備忘錄：聯發科客戶拜訪": "RESEARCH_MEMO"
    }
    for title, expected in cases.items(): assert def_classify_investment_report(title).report_type_code == expected, title
    brief = "◆ 台積電(2330) 展望\n" + "內容與財務數據說明。" * 12 + "\n◆ 鴻海(2317) 更新\n" + "伺服器出貨與展望說明。" * 10
    assert len(def_split_morning_brief("晨報", brief)) == 2

if __name__ == "__main__":
    def_self_test(); print("def REPORT_CLASSIFIER_SELF_TEST: PASS")
