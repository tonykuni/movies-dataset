from __future__ import annotations

import unittest

from via_nlp_engine.discourse import CPUHierarchicalTopicOrganizer
from via_nlp_engine.cpu_augmentation import CPUNLPAugmentor
from via_nlp_engine.knowledge import CodeExtractor, LosslessSegmenter


class StubProcessor:
    @staticmethod
    def keywords(text: str, top_k: int = 32) -> list[dict[str, object]]:
        return [{"term": item, "count": 1} for item in text.lower().split()[:top_k]]

    @staticmethod
    def entities(text: str) -> list[dict[str, str]]:
        return []


class V161LayoutSegmentationTests(unittest.TestCase):
    def test_report_and_dual_zone_boundaries_are_lossless(self) -> None:
        source = (
            "個股報告首頁文字擷取總覽(LAYOUT ANALYSIS)\n"
            "20250819兆豐個股報告-泓德能源(6873).pdfDUAL_ZONES · 分區還原\n"
            "本文區(修復)\n營收與 EPS 內容。\n"
            "右資訊區\n日期 2025-08-19。\n"
            "20251128兆豐訪談速報-神達(3706).pdfDUAL_ZONES · 分區還原\n"
            "本文區(修復)\n第二份內容。\n"
        )
        result = LosslessSegmenter().segment(source)
        segments = result["segments"]
        self.assertTrue(result["completeness"]["exact_reconstruction"])
        self.assertEqual("".join(item["text"] for item in segments), source)
        self.assertEqual(sum(item["kind"] == "report_header" for item in segments), 2)
        self.assertEqual(sum(item["kind"] == "layout_body_zone" for item in segments), 2)
        self.assertEqual(sum(item["kind"] == "layout_information_zone" for item in segments), 1)
        first_report = next(item for item in segments if item["kind"] == "report_header")
        first_body = next(item for item in segments if item["kind"] == "layout_body_zone")
        self.assertEqual(first_report["layout_group_id"], first_body["layout_group_id"])

    def test_source_record_boundary_resets_report_group(self) -> None:
        source = (
            "A.pdfDUAL_ZONES · 分區還原\n本文區(修復)\n內容\n"
            "===== END EXTRACTED CONTENT =====\n"
            "===== END VIA SOURCE RECORD RECORD-A =====\n"
            "===== BEGIN VIA SOURCE RECORD RECORD-B =====\n"
            "===== BEGIN EXTRACTED CONTENT =====\n"
            "一般對話\n"
        )
        result = LosslessSegmenter().segment(source)
        final_segment = result["segments"][-1]
        self.assertTrue(result["completeness"]["exact_reconstruction"])
        self.assertEqual(final_segment["kind"], "article")
        self.assertIsNone(final_segment["layout_group_id"])

    def test_chinese_numbered_sections_and_format_markers_split(self) -> None:
        source = (
            "前言\n"
            "一、 資金流方法\n內容 A\n"
            "1. 覆蓋率定義\n內容 B\n"
            "HTML\n<table></table>\n"
            "MD+ 1\n公式說明\n"
        )
        result = LosslessSegmenter().segment(source)
        kinds = [item["kind"] for item in result["segments"]]
        self.assertTrue(result["completeness"]["exact_reconstruction"])
        self.assertEqual(kinds.count("heading_section"), 2)
        self.assertEqual(kinds.count("format_marker"), 2)

    def test_boundaries_inside_fenced_code_do_not_split(self) -> None:
        source = "```text\n一、 這是程式內容\nHTML\n```\n尾端\n"
        result = LosslessSegmenter().segment(source)
        self.assertTrue(result["completeness"]["exact_reconstruction"])
        self.assertEqual(len(result["segments"]), 1)


class V161CodeFragmentTests(unittest.TestCase):
    def test_real_world_python_fragments_are_not_mislabeled_as_toml_or_css(self) -> None:
        fragments = [
            "f_M = 1.0\nelif 1.50 <= margin_ratio <= 1.66:\nf_M = 0.5\nelse:\nf_M = -1.0",
            "raw_flow = t86_net + etf_flow + margin_nominal_dollar\nw_dq = 1.0 - day_trade_ratio\nadjusted_flow_dollar = raw_flow * w_dq",
            "kappa = 1500000000\nfis_intensity = 100 * np.tanh(adjusted_flow_dollar / kappa)\nreturn {",
            "quanta_res = calculate_veritas_flow(\nt86_net=2500000000,\nmargin_ratio=1.85\n)",
            "status = '真吸籌'\nelif row['day_trade_ratio'] >= 0.3:\nstatus = '假吸籌'\nreturn pd.Series([flow, status])",
        ]
        for fragment in fragments:
            with self.subTest(fragment=fragment[:30]):
                self.assertEqual(CodeExtractor._guess_language(fragment), "python")

    def test_incomplete_python_fragment_is_preserved_and_review_required(self) -> None:
        source = "f_M = 1.0\nelif margin_ratio < 1.6:\nf_M = -1.0\n"
        segments = LosslessSegmenter().segment(source)["segments"]
        blocks = CodeExtractor().extract(source, segments)
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0]["language"], "python")
        self.assertEqual(blocks[0]["code"], source.rstrip("\n"))
        self.assertEqual(blocks[0]["fragment_classification"]["status"], "incomplete_python_fragment")
        self.assertTrue(blocks[0]["fragment_classification"]["review_required"])
        self.assertFalse(blocks[0]["fragment_classification"]["auto_repair_applied"])


class V161TopicNoiseTests(unittest.TestCase):
    def test_layout_markers_do_not_become_semantic_keywords(self) -> None:
        organizer = CPUHierarchicalTopicOrganizer(StubProcessor())
        features = organizer._features("HTML\n資金 flow ETF")
        self.assertNotIn("html", features)
        self.assertIn("資金", features)

    def test_calendar_year_is_not_a_ticker_anchor(self) -> None:
        organizer = CPUHierarchicalTopicOrganizer(StubProcessor())
        anchors = organizer._anchors("2026 年報告；公司代碼 6873；report.pdfDUAL_ZONES")
        self.assertNotIn("ticker:2026", anchors)
        self.assertIn("ticker:6873", anchors)
        self.assertNotIn("id:PDFDUAL_ZONES", anchors)

    def test_common_english_aliases_and_substring_acronyms_are_filtered(self) -> None:
        augmentor = CPUNLPAugmentor({"use_available_providers": False})
        result = augmentor._exact_alias_matches("be and AMAX use AI", ["be", "and", "AM", "AI"])
        self.assertEqual(result["matches"], [{"term": "AI", "start": 16, "end": 18}])

    def test_pure_layout_markers_do_not_consume_duplicate_review_budget(self) -> None:
        augmentor = CPUNLPAugmentor({"use_available_providers": False})
        result = augmentor._near_duplicate_candidates(
            [
                {"segment_id": "S1", "text": "HTML\n"},
                {"segment_id": "S2", "text": "HTML\n"},
                {"segment_id": "S3", "text": "真正內容 A B C"},
            ]
        )
        self.assertEqual(result["pair_count"], 0)


if __name__ == "__main__":
    unittest.main()
