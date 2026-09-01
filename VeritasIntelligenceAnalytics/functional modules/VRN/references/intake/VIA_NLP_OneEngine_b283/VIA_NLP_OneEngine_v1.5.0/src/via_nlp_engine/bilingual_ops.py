"""Conservative Chinese/English structural projection without invented translation."""

from __future__ import annotations

import copy
import re
from typing import Any


PAIR_RE = re.compile(
    r"(?P<zh>[\u3400-\u9fff][\u3400-\u9fff·\-/／ ]{0,40})\s*[（(]\s*"
    r"(?P<en>[A-Za-z][A-Za-z0-9 ._+&/\-]{0,70})\s*[）)]"
)
CJK_RE = re.compile(r"[\u3400-\u9fff]")
LATIN_RE = re.compile(r"[A-Za-z]")

BASE_GLOSSARY_ZH_EN = {
    "知識體": "Knowledge Body",
    "知識圖譜": "Knowledge Graph",
    "心智圖": "Mind Map",
    "動態心智圖": "Dynamic Mind Map",
    "自然語言處理": "Natural Language Processing",
    "指令": "Instruction",
    "命令": "Command",
    "程序": "Procedure",
    "步驟": "Step",
    "前置條件": "Prerequisite",
    "需求": "Requirement",
    "決策": "Decision",
    "問題": "Question",
    "風險": "Risk",
    "參數": "Parameter",
    "驗證": "Verification",
    "輸入": "Input",
    "輸出": "Output",
    "安裝": "Installation",
    "執行": "Execution",
    "測試": "Test",
    "修復": "Repair",
    "來源": "Source",
    "證據": "Evidence",
    "治理": "Governance",
    "主題": "Topic",
    "主題片段": "Topic Episode",
    "知識單元": "Knowledge Unit",
    "知識衝突": "Knowledge Conflict",
    "程式版本族": "Code Family",
    "來源片段": "Source Segment",
    "結構化表格": "Structured Table",
    "知識根節點": "Knowledge Root",
    "新增": "Added",
    "保留": "Retained",
    "更新": "Updated",
    "待淘汰": "Deprecation Candidate",
    "需人工審查": "Human Review Required",
    "禁止自動執行": "Automatic Execution Forbidden",
    "不可變來源": "Immutable Source",
    "逐字還原": "Verbatim Reconstruction",
    "中英文": "Chinese and English",
    "繁體中文": "Traditional Chinese",
    "英文": "English",
}

ROLE_LABELS = {
    "decision": {"zh": "決策", "en": "Decision"},
    "requirement": {"zh": "需求", "en": "Requirement"},
    "question": {"zh": "問題", "en": "Question"},
    "issue": {"zh": "議題", "en": "Issue"},
    "action": {"zh": "行動", "en": "Action"},
    "parameter": {"zh": "參數", "en": "Parameter"},
    "context": {"zh": "背景", "en": "Context"},
    "prerequisite": {"zh": "前置條件", "en": "Prerequisite"},
    "verification": {"zh": "驗證", "en": "Verification"},
    "prohibition": {"zh": "禁止事項", "en": "Prohibition"},
    "command": {"zh": "命令", "en": "Command"},
}

NODE_TYPE_LABELS = {
    "knowledge_root": {"zh": "知識根節點", "en": "Knowledge Root"},
    "topic": {"zh": "主題", "en": "Topic"},
    "topic_episode": {"zh": "主題片段", "en": "Topic Episode"},
    "source_segment": {"zh": "來源片段", "en": "Source Segment"},
    "structured_table": {"zh": "結構化表格", "en": "Structured Table"},
    "knowledge_unit": {"zh": "知識單元", "en": "Knowledge Unit"},
    "knowledge_conflict": {"zh": "知識衝突", "en": "Knowledge Conflict"},
    "code_family": {"zh": "程式版本族", "en": "Code Family"},
    "instruction": {"zh": "指令", "en": "Instruction"},
    "command": {"zh": "命令", "en": "Command"},
    "procedure": {"zh": "程序", "en": "Procedure"},
}

RELATION_LABELS = {
    "contains_topic": {"zh": "包含主題", "en": "Contains Topic"},
    "contains_episode": {"zh": "包含主題片段", "en": "Contains Episode"},
    "episode_grounded_by": {"zh": "片段依據", "en": "Episode Grounded By"},
    "grounded_by": {"zh": "依據來源", "en": "Grounded By"},
    "contains_structured_table": {"zh": "包含結構化表格", "en": "Contains Structured Table"},
    "supports_knowledge_unit": {"zh": "支持知識單元", "en": "Supports Knowledge Unit"},
    "conflicting_candidate": {"zh": "衝突候選", "en": "Conflicting Candidate"},
    "contains_code_family": {"zh": "包含程式版本族", "en": "Contains Code Family"},
    "contains_instruction": {"zh": "包含指令", "en": "Contains Instruction"},
    "contains_command": {"zh": "包含命令", "en": "Contains Command"},
    "source_next": {"zh": "來源下一段", "en": "Source Next"},
    "switches_to": {"zh": "切換至", "en": "Switches To"},
    "returns_to_topic": {"zh": "返回主題", "en": "Returns To Topic"},
    "follows_in_source": {"zh": "依來源順序接續", "en": "Follows In Source"},
    "requires": {"zh": "需要", "en": "Requires"},
    "verifies": {"zh": "驗證", "en": "Verifies"},
}


def detect_language(text: str) -> str:
    """Return a deterministic coarse language tag for evidence metadata."""

    cjk = len(CJK_RE.findall(text))
    latin = len(LATIN_RE.findall(text))
    if cjk and latin:
        return "mixed"
    if cjk:
        return "zh"
    if latin:
        return "en"
    return "und"


def build_glossary(source_text: str = "") -> dict[str, str]:
    """Merge fixed technical terms with only explicitly paired source terms."""

    glossary = dict(BASE_GLOSSARY_ZH_EN)
    for match in PAIR_RE.finditer(source_text):
        zh = re.sub(r"\s+", " ", match.group("zh")).strip()
        en = re.sub(r"\s+", " ", match.group("en")).strip()
        if zh and en and len(zh) <= 40 and len(en) <= 70:
            glossary.setdefault(zh, en)
    return glossary


def bilingual_label(text: str, glossary: dict[str, str] | None = None) -> dict[str, str]:
    """Project a label conservatively and expose unresolved translation honestly."""

    value = re.sub(r"\s+", " ", str(text)).strip()
    terms = glossary or BASE_GLOSSARY_ZH_EN
    reverse = {english.casefold(): chinese for chinese, english in terms.items()}
    language = detect_language(value)
    if not value:
        return {"source": "", "source_language": "und", "zh": "", "en": "", "translation_status": "empty"}
    if value in terms:
        return {
            "source": value,
            "source_language": language,
            "zh": value,
            "en": terms[value],
            "translation_status": "verified_glossary",
        }
    if value.casefold() in reverse:
        return {
            "source": value,
            "source_language": language,
            "zh": reverse[value.casefold()],
            "en": value,
            "translation_status": "verified_glossary",
        }
    if language in {"und", "mixed"} and not CJK_RE.search(value):
        return {
            "source": value,
            "source_language": language,
            "zh": value,
            "en": value,
            "translation_status": "shared_technical_term",
        }

    translated = value
    replacements = 0
    for zh, en in sorted(terms.items(), key=lambda item: len(item[0]), reverse=True):
        if zh in translated:
            translated = translated.replace(zh, en)
            replacements += 1
    if language == "zh":
        return {
            "source": value,
            "source_language": language,
            "zh": value,
            "en": translated,
            "translation_status": "partial_glossary" if replacements and not CJK_RE.search(translated) else "needs_translation",
        }

    translated_zh = value
    for english, chinese in sorted(reverse.items(), key=lambda item: len(item[0]), reverse=True):
        translated_zh = re.sub(re.escape(english), chinese, translated_zh, flags=re.I)
    return {
        "source": value,
        "source_language": language,
        "zh": translated_zh,
        "en": value,
        "translation_status": "partial_glossary" if translated_zh != value and not LATIN_RE.search(translated_zh) else "needs_translation",
    }


def decorate_mind_map(mind_map: dict[str, Any], source_text: str) -> dict[str, Any]:
    """Add bilingual human/AI projections while retaining original labels."""

    output = copy.deepcopy(mind_map)
    glossary = build_glossary(source_text)
    root = output["root"]
    root["bilingual_label"] = bilingual_label(str(root.get("name", "")), glossary)
    for topic in root.get("children", []):
        topic["bilingual_label"] = bilingual_label(str(topic.get("name", "")), glossary)
        for episode in topic.get("episodes", []):
            episode["bilingual_label"] = bilingual_label(str(episode.get("name", "")), glossary)
        for branch in topic.get("branches", []):
            role = str(branch.get("name", "context"))
            branch["bilingual_label"] = ROLE_LABELS.get(role, bilingual_label(role, glossary))
    for node in output["ai_view"].get("nodes", []):
        node["type_label"] = NODE_TYPE_LABELS.get(
            str(node.get("node_type", "")), bilingual_label(str(node.get("node_type", "")), glossary)
        )
        node["bilingual_label"] = bilingual_label(str(node.get("label", "")), glossary)
    for edge in output["ai_view"].get("edges", []):
        relation = str(edge.get("relation", ""))
        edge["relation_label"] = RELATION_LABELS.get(relation, bilingual_label(relation, glossary))
    output["format"] = "VIA_MIND_MAP_JSON/3.0"
    output["ai_view"]["schema"] = "VIA_KNOWLEDGE_GRAPH/3.0"
    output["human_view"] = {
        "zh": _human_projection(root, "zh"),
        "en": _human_projection(root, "en"),
        "source_preserved": True,
    }
    statuses = [
        node["bilingual_label"]["translation_status"]
        for node in output["ai_view"].get("nodes", [])
    ]
    output["bilingual_contract"] = {
        "schema": "VIA_BILINGUAL_PROJECTION/1.0",
        "languages": ["zh", "en"],
        "structural_labels_complete": True,
        "semantic_labels_total": len(statuses),
        "semantic_labels_verified_or_shared": sum(
            status in {"verified_glossary", "shared_technical_term", "partial_glossary"}
            for status in statuses
        ),
        "semantic_labels_needing_translation": sum(status == "needs_translation" for status in statuses),
        "unknown_term_policy": "preserve_source_and_mark_needs_translation",
        "automatic_fabricated_translation": False,
    }
    return output


def _human_projection(node: dict[str, Any], language: str) -> dict[str, Any]:
    label = node.get("bilingual_label", {})
    projected = {
        "id": node.get("id", "ROOT"),
        "name": label.get(language, node.get("name", "")),
        "source_name": node.get("name", ""),
    }
    children = []
    for child in node.get("children", []):
        if not isinstance(child, dict):
            continue
        child_label = child.get("bilingual_label", {})
        children.append(
            {
                "id": child.get("id"),
                "name": child_label.get(language, child.get("name", "")),
                "source_name": child.get("name", ""),
                "segment_ids": child.get("segment_ids", []),
                "episodes": [
                    {
                        "id": episode.get("id"),
                        "name": episode.get("bilingual_label", {}).get(language, episode.get("name", "")),
                        "source_name": episode.get("name", ""),
                    }
                    for episode in child.get("episodes", [])
                ],
            }
        )
    projected["children"] = children
    return projected
