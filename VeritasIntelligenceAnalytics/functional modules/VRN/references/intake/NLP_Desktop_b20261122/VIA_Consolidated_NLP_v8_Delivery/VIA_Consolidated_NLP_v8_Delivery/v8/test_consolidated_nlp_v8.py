from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "v8"))
from via_consolidated_nlp_v8 import (  # noqa: E402
    CONSOLIDATED_MODULES,
    artifact_payloads_v8,
    ast_inventory,
    normalize_text,
    process_text_v8,
)


def main() -> None:
    source = """# Test input\n\n請整理  這段文字。\n\n```python\nimport os\ndef demo(x):\n    return x\n```\n\n執行命令：不要直接執行，只產生建議。"""
    ast_result = ast_inventory("fixture.py", "import os\nclass Demo:\n    def run(self, value):\n        return value\n")
    assert ast_result["parse_status"] == "PASS"
    assert ast_result["statistics"]["classes"] == 1
    assert ast_result["statistics"]["functions"] == 1
    assert ast_result["execution_authorized"] is False

    normalized = normalize_text("A  B\u00a0C\n\n\nD")
    assert normalized["normalized_text"] == "A B C\n\nD"
    assert normalized["source_preserved"] is True

    result = process_text_v8("fixture.txt", source)
    assert result["schema"] == "VIA_CONSOLIDATED_NLP_RESULT/8.0"
    assert len(result["modules"]) == 7
    assert result["projection"]["quality"]["v8_source_preserved"] is True
    assert result["projection"]["quality"]["v8_source_mutated"] is False
    assert result["projection"]["quality"]["ast_execution_authorized"] is False
    assert result["knowledge_mindmap"]["mind_map"] is not None
    assert result["discussion_commands"]["command_execution_authorized"] is False
    payloads = artifact_payloads_v8(result)
    required = {
        "v8_unified.json", "v8_source_ledger.json", "v8_text_nlp.json",
        "v8_discussion_commands.json", "v8_knowledge_mindmap.json",
        "v8_ast_modules.json", "v8_governance.json", "v8_module_registry.json",
        "v8_mind_map.mmd", "compat_v7_unified.json",
    }
    assert required.issubset(payloads), sorted(payloads)
    json.dumps(result, ensure_ascii=False)
    print(json.dumps({
        "status": "PASS",
        "modules": len(CONSOLIDATED_MODULES),
        "payloads": len(payloads),
        "ast": ast_result["statistics"],
        "source_preserved": result["projection"]["quality"]["v8_source_preserved"],
        "execution_authorized": result["projection"]["quality"]["ast_execution_authorized"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
