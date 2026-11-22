from __future__ import annotations

import hashlib
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from v5.via_nlp_reconstruction_v5 import load_lexicon, merge_similar_commands, reconstruct_v5_file, reconstruct_v5_paths  # noqa: E402


def test_lexicon_and_command_merge() -> None:
    lexicon = load_lexicon()
    commands = [
        {"command_id": "A", "goal": "請整合 NLP 模組並驗證", "actions": ["整合 NLP"], "parameters": ["mode"], "constraints": ["不得刪除原文"], "verification": ["驗證"]},
        {"command_id": "B", "goal": "請合併 NLP 模組並測試", "actions": ["合併 NLP"], "parameters": ["--mode"], "constraints": ["不得刪除原文"], "verification": ["測試"]},
    ]
    result = merge_similar_commands(commands, lexicon, threshold=0.4)
    assert result["original_command_count"] == 2
    assert result["merged_command_count"] == 1
    assert result["deduplicated_candidate_count"] == 1
    assert result["source_commands_preserved"] is True
    assert result["groups"][0]["executable"] is False


def test_v5_record_preserves_source_and_enhances_projection() -> None:
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp) / "dialogue.txt"
        source = (
            "09:00 Alice：請重構 NLP 參數 mode=balanced，並驗證 https://example.com/spec。\n"
            "09:10 Bob：請整合 NLP 參數 --mode balanced，測試後產生摘要。\n\n"
            "規格：不得刪除原文；輸出 SUMMARY、topic、mind map。\n"
            "如何合併相似指令？\n"
        )
        path.write_text(source, encoding="utf-8")
        before = path.read_bytes()
        expected_hash = hashlib.sha256(before).hexdigest()
        record = reconstruct_v5_file(path, load_lexicon(), command_threshold=0.42)
        assert path.read_bytes() == before
        assert record["source"]["source_sha256"] == expected_hash
        assert record["quality_gates"]["v5_source_preserved"] is True
        assert record["quality_gates"]["v5_semantic_rewrite_executable"] is False
        assert record["projections"]["nlp_v5"]["synonym_normalization"] is True
        assert record["projections"]["topic_reconstruction"]["episode_count"] >= 1
        assert record["projections"]["summary"]["key_points"]
        assert record["projections"]["summary"]["source_unit_traceable"] is True
        assert record["projections"]["command_reconstruction"]["similarity_merge"]["source_commands_preserved"] is True
        assert "https://example.com/spec" in record["projections"]["corrected_text"]
        assert record["projections"]["parameter_reconstruction"]["parameters"]
        assert record["projections"]["mindmap_projection"]["source_unit_traceable"] is True
        assert record["projections"]["mindmap_projection"]["markdown"].startswith("# 文章脈絡心智圖")
        assert record["projections"]["mindmap_projection"]["mermaid"].startswith("flowchart LR")
        assert record["projections"]["prompt_projection"]["executable"] is False


def test_bundle_gate_is_source_preserving() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        first = root / "a.txt"
        second = root / "b.md"
        first.write_text("請整合文章並摘要。", encoding="utf-8")
        second.write_text("規格：mode=balanced\n請驗證。", encoding="utf-8")
        before = {p.name: p.read_bytes() for p in (first, second)}
        bundle = reconstruct_v5_paths([first, second], load_lexicon())
        assert bundle["quality_gates"]["source_preserved"] is True
        assert bundle["quality_gates"]["source_deleted"] is False
        assert bundle["quality_gates"]["source_mutated"] is False
        assert bundle["quality_gates"]["original_commands_preserved"] is True
        assert {p.name: p.read_bytes() for p in (first, second)} == before
        assert bundle["summary"]["topics"] >= 1


if __name__ == "__main__":
    test_lexicon_and_command_merge()
    test_v5_record_preserves_source_and_enhances_projection()
    test_bundle_gate_is_source_preserving()
    print("PASS")
