"""npl_preprocessor.py 的單元測試。"""

from __future__ import annotations

import unittest

from npl_preprocessor import (
    LanguageNormalizer,
    NLPConfig,
    NLPPreprocessor,
    NormalizationConfig,
)


class FakeConverter:
    def __init__(self, replacement: str = "") -> None:
        self.replacement = replacement

    def convert(self, text: str) -> str:
        return text.replace("简", "簡") + self.replacement


def build_test_pipeline() -> NLPPreprocessor:
    try:
        import spacy
    except ImportError as exc:  # pragma: no cover - 只在缺依賴環境執行
        raise unittest.SkipTest(f"spaCy 未安裝：{exc}")

    nlp = spacy.blank("zh")
    nlp.add_pipe("sentencizer")
    return NLPPreprocessor(nlp=nlp)


class LanguageNormalizerTests(unittest.TestCase):
    def test_normalizes_fullwidth_ascii_and_whitespace(self) -> None:
        normalizer = LanguageNormalizer(opencc_converter=FakeConverter())
        actual = normalizer.normalize("  ２０２６年Ｑ１，简\n體  ")
        self.assertEqual(actual, "2026年Q1,簡 體")

    def test_can_convert_common_cjk_punctuation_to_ascii(self) -> None:
        config = NormalizationConfig(punctuation_style="ascii")
        normalizer = LanguageNormalizer(config, opencc_converter=FakeConverter())
        self.assertEqual(normalizer.normalize("你好，世界％。"), "你好,世界%.")

    def test_preserve_newlines_keeps_paragraph_boundaries(self) -> None:
        config = NormalizationConfig(preserve_newlines=True)
        normalizer = LanguageNormalizer(config, opencc_converter=FakeConverter())
        self.assertEqual(normalizer.normalize(" 第一行\n\n 第二行 "), "第一行\n\n第二行")

    def test_empty_and_invalid_inputs(self) -> None:
        normalizer = LanguageNormalizer(opencc_converter=FakeConverter())
        self.assertEqual(normalizer.normalize(None), "")
        self.assertEqual(normalizer.normalize(""), "")
        with self.assertRaises(TypeError):
            normalizer.normalize(123)  # type: ignore[arg-type]


class NLPPreprocessorTests(unittest.TestCase):
    def test_domain_entities_include_offsets_and_metadata(self) -> None:
        processor = build_test_pipeline()
        result = processor.process("NPL Ratio 攀升，金管會關注系統性風險。")
        entities = {(item["text"], item["label"]) for item in result["entities"]}
        self.assertIn(("NPL Ratio", "INDICATOR"), entities)
        self.assertIn(("金管會", "POLICY_ORG"), entities)
        self.assertIn(("系統性風險", "CONCEPT"), entities)
        for entity in result["entities"]:
            self.assertLess(entity["start_char"], entity["end_char"])
            self.assertLess(entity["start"], entity["end"])

    def test_process_empty_text_is_stable(self) -> None:
        processor = build_test_pipeline()
        self.assertEqual(
            processor.process(None),
            {"text": "", "sentences": [], "tokens": [], "entities": []},
        )

    def test_process_many_preserves_positions_of_empty_items(self) -> None:
        processor = build_test_pipeline()
        results = processor.process_many(["金管會", "", None, "NPL Ratio"])
        self.assertEqual(len(results), 4)
        self.assertEqual(results[1]["text"], "")
        self.assertEqual(results[2]["text"], "")
        self.assertEqual(results[0]["text"], "金管會")
        self.assertEqual(results[3]["text"], "NPL Ratio")
        self.assertEqual(results[0]["entities"][0]["label"], "POLICY_ORG")
        self.assertEqual(results[3]["entities"][0]["label"], "INDICATOR")
        with self.assertRaises(ValueError):
            processor.process_many(["金管會"], batch_size=0)

    def test_configuration_validation(self) -> None:
        with self.assertRaises(ValueError):
            NormalizationConfig(punctuation_style="unknown")  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            NLPConfig(batch_size=0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
