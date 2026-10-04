"""Evidence-first functional classification for statically extracted symbols."""

from __future__ import annotations

import hashlib
import re
from typing import Any


FUNCTION_CLASSIFICATION_SCHEMA = "VIA_FUNCTION_CLASSIFICATION/1.0"
MIN_SECONDARY_SCORE = 2

CATEGORY_LABELS = {
    "ingestion": {"zh": "資料匯入", "en": "Ingestion"},
    "network": {"zh": "網路擷取", "en": "Network / Fetching"},
    "parsing": {"zh": "解析", "en": "Parsing"},
    "normalization": {"zh": "正規化", "en": "Normalization"},
    "validation": {"zh": "驗證", "en": "Validation"},
    "transformation": {"zh": "轉換", "en": "Transformation"},
    "analytics_nlp": {"zh": "分析與 NLP", "en": "Analytics / NLP"},
    "persistence_io": {"zh": "儲存與輸出入", "en": "Persistence / I/O"},
    "orchestration": {"zh": "流程編排", "en": "Orchestration"},
    "configuration": {"zh": "設定", "en": "Configuration"},
    "security_governance": {"zh": "安全與治理", "en": "Security / Governance"},
    "concurrency_performance": {"zh": "平行與效能", "en": "Concurrency / Performance"},
    "ui_reporting": {"zh": "介面與報告", "en": "UI / Reporting"},
    "testing_debug": {"zh": "測試與除錯", "en": "Testing / Debug"},
    "utility": {"zh": "通用工具", "en": "Utility"},
}

CATEGORY_PATTERNS = {
    "ingestion": r"(?:ingest|load|read|import|intake|decode|upload|匯入|讀取)",
    "network": r"(?:fetch|crawl|scrape|request|http|download|url|api|socket|抓取|爬蟲|下載)",
    "parsing": r"(?:parse|parser|extract|tokenize|ast|cst|selector|解析|抽取)",
    "normalization": r"(?:normaliz|clean|sanitize|repair|canonical|dedup|正規|清理|修復|去重)",
    "validation": r"(?:valid|verify|check|assert|schema|contract|guard|驗證|檢查|合約)",
    "transformation": r"(?:transform|convert|map|merge|split|reconstruct|build|project|轉換|重建|合併)",
    "analytics_nlp": r"(?:analy|classif|cluster|keyword|topic|embed|summar|nlp|mind.?map|知識|主題|分類|摘要)",
    "persistence_io": r"(?:save|write|export|persist|cache|database|sqlite|duckdb|file|archive|儲存|輸出|檔案)",
    "orchestration": r"(?:run|main|route|dispatch|pipeline|workflow|process|execute|orchestrat|流程|路由|編排)",
    "configuration": r"(?:config|setting|environment|registry|ssot|parameter|設定|環境|參數)",
    "security_governance": r"(?:security|auth|policy|govern|audit|permission|compliance|risk|安全|治理|稽核)",
    "concurrency_performance": r"(?:async|thread|process.?pool|parallel|batch|accelerat|stream|lazy|memory|cpu|效能|平行|批次)",
    "ui_reporting": r"(?:render|dashboard|plot|chart|report|html|view|display|ui|matrix|報告|圖表|介面)",
    "testing_debug": r"(?:test|debug|trace|log|mock|fixture|diagnos|測試|除錯|日誌)",
    "utility": r"(?:util|helper|hash|id|format|serialize|通用|輔助)",
}


def _stable_id(*values: str) -> str:
    payload = "\0".join(values)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16].upper()


class FunctionClassifier:
    """Classify functions and blocks from AST/CST evidence without execution."""

    def build(self, code_reconstruction: dict[str, Any]) -> dict[str, Any]:
        records: list[dict[str, Any]] = []
        for block in code_reconstruction.get("code_blocks", []):
            spec = block.get("engine_spec", {})
            contracts = {str(item.get("name")): item for item in spec.get("function_contracts", [])}
            functions = [str(item) for item in spec.get("functions", [])]
            if functions:
                for name in functions:
                    records.append(self._classify_symbol(block, name, contracts.get(name, {}), "function"))
            else:
                records.append(self._classify_symbol(block, f"block:{block['code_id']}", {}, "code_block"))
        counts = {category: sum(item["primary_category"] == category for item in records) for category in CATEGORY_LABELS}
        return {
            "schema": FUNCTION_CLASSIFICATION_SCHEMA,
            "languages": ["zh", "en"],
            "category_labels": CATEGORY_LABELS,
            "records": records,
            "statistics": {
                "classified_records": len(records),
                "functions": sum(item["symbol_kind"] == "function" for item in records),
                "code_blocks_without_functions": sum(item["symbol_kind"] == "code_block" for item in records),
                "primary_category_counts": counts,
                "review_required": sum(item["review_required"] for item in records),
            },
            "quality_gates": {
                "source_traceability": "pass" if all(item["source_segments"] for item in records) or not records else "fail",
                "classification_is_candidate": True,
                "code_execution_authorized": False,
                "automatic_code_write": False,
                "automatic_canonical_promotion": False,
            },
        }

    def _classify_symbol(
        self,
        block: dict[str, Any],
        name: str,
        contract: dict[str, Any],
        symbol_kind: str,
    ) -> dict[str, Any]:
        spec = block.get("engine_spec", {})
        evidence_text = " ".join(
            [name, str(contract.get("docstring", ""))]
            + [str(item) for item in contract.get("calls", [])]
            + [str(item) for item in spec.get("imports", [])]
            + [str(item) for item in spec.get("dependencies", [])]
            + [str(item) for item in block.get("hydra_risks", [])]
        )
        scores: dict[str, int] = {}
        evidence: dict[str, list[str]] = {}
        for category, pattern in CATEGORY_PATTERNS.items():
            hits = sorted({item.casefold() for item in re.findall(pattern, evidence_text, flags=re.I)})
            if hits:
                name_bonus = 2 if re.search(pattern, name, flags=re.I) else 0
                scores[category] = len(hits) + name_bonus
                evidence[category] = hits[:12]
        if not scores:
            scores = {"utility": 1}
            evidence = {"utility": ["fallback_no_strong_marker"]}
        ordered = sorted(scores, key=lambda key: (-scores[key], key))
        primary = ordered[0]
        categories = [item for item in ordered if item == primary or scores[item] >= MIN_SECONDARY_SCORE]
        confidence = min(0.98, 0.48 + 0.10 * scores[primary] + (0.08 if len(ordered) == 1 else 0.0))
        return {
            "function_id": f"FUNC-{_stable_id(str(block['code_id']), name)}",
            "symbol_name": name,
            "symbol_kind": symbol_kind,
            "language": block.get("language", "unknown"),
            "code_id": block["code_id"],
            "family_id": block.get("family_id"),
            "primary_category": primary,
            "primary_label": CATEGORY_LABELS[primary],
            "categories": [
                {
                    "category": item,
                    "label": CATEGORY_LABELS[item],
                    "score": scores[item],
                    "evidence": evidence[item],
                }
                for item in categories
            ],
            "confidence": round(confidence, 4),
            "review_required": confidence < 0.75 or symbol_kind == "code_block",
            "contract": contract,
            "source_segments": block.get("source_segments", []),
            "source_code_sha256": block.get("sha256"),
        }
