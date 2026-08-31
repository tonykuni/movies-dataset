"""中文文本正規化與 NPL 領域 NLP 預處理。

此模組提供兩個可獨立使用的元件：

* :class:`LanguageNormalizer`：以 OpenCC 進行簡繁轉換，並安全處理全形
  ASCII 字元與空白。
* :class:`NLPPreprocessor`：載入 spaCy 中文模型，掛載 NPL 領域
  EntityRuler，輸出句子、Token 與實體的 JSON 相容資料。

安裝依賴後即可直接執行：

    python npl_preprocessor.py --demo --json

或將原始文字透過標準輸入傳入：

    cat input.txt | python npl_preprocessor.py --json
"""

from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import argparse
import json
import logging
import re
import sys
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

try:  # 讓只需要正規化以外功能的環境也能得到清楚錯誤訊息
    import opencc  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - 依環境而定
    opencc = None  # type: ignore[assignment]

try:  # spaCy 可能只在部署 NLP 服務時才安裝
    import spacy  # type: ignore[import-not-found]
    from spacy.symbols import ORTH  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - 依環境而定
    spacy = None  # type: ignore[assignment]
    ORTH = "ORTH"


LOGGER = logging.getLogger(__name__)
DEFAULT_MODEL = "zh_core_web_sm"
DEFAULT_OPENCC_CONFIG = "s2twp"

# 僅轉換全形 ASCII 區段，避免 unicodedata.NFKC 對其他相容字元做過度變形。
_FULLWIDTH_ASCII_RE = re.compile(r"[\uFF01-\uFF5E]")
_WHITESPACE_RE = re.compile(r"\s+")

# 中文標點預設保留；只有呼叫端明確選擇 ascii 樣式時才會套用此表。
_CJK_TO_ASCII_PUNCTUATION = str.maketrans(
    {
        "。": ".",
        "，": ",",
        "、": ",",
        "；": ";",
        "：": ":",
        "？": "?",
        "！": "!",
        "（": "(",
        "）": ")",
        "【": "[",
        "】": "]",
        "「": '"',
        "」": '"',
        "『": '"',
        "』": '"',
        "％": "%",
    }
)


@dataclass(frozen=True, slots=True)
class NormalizationConfig:
    """文字正規化選項。

    ``punctuation_style="preserve"`` 是非破壞性預設值；若下游系統只接受
    ASCII 標點，可改成 ``"ascii"``。保留換行則適合需要維持段落邊界的文件。
    """

    opencc_config: str = DEFAULT_OPENCC_CONFIG
    punctuation_style: str = "preserve"
    preserve_newlines: bool = False
    strip: bool = True

    def __post_init__(self) -> None:
        if self.punctuation_style not in {"preserve", "ascii"}:
            raise ValueError("punctuation_style 必須是 'preserve' 或 'ascii'")
        if not self.opencc_config:
            raise ValueError("opencc_config 不可為空")


class LanguageNormalizer:
    """簡繁轉換與基礎字元清理器。

    OpenCC 物件在初始化時建立一次，避免每次呼叫 ``normalize`` 都重載配置。
    """

    def __init__(
        self,
        config: NormalizationConfig | None = None,
        *,
        opencc_converter: Any | None = None,
    ) -> None:
        self.config = config or NormalizationConfig()

        if opencc_converter is not None:
            self.cc = opencc_converter
        elif opencc is None:
            raise RuntimeError(
                "缺少 OpenCC 依賴。請執行：pip install opencc-python-reimplemented"
            ) from None
        else:
            try:
                # opencc-python-reimplemented 會自動補上 .json；移除使用者
                # 傳入的尾綴可同時兼容 "s2twp" 與 "s2twp.json"。
                config_name = self.config.opencc_config.removesuffix(".json")
                self.cc = opencc.OpenCC(config_name)
            except (OSError, ValueError) as exc:
                raise RuntimeError(
                    f"無法載入 OpenCC 配置 '{self.config.opencc_config}'：{exc}"
                ) from exc

    @staticmethod
    def _to_halfwidth_ascii(text: str) -> str:
        """只將 U+FF01–U+FF5E 的全形 ASCII 字元轉為半形。"""

        return _FULLWIDTH_ASCII_RE.sub(
            lambda match: chr(ord(match.group(0)) - 0xFEE0), text
        )

    def normalize(self, text: str | None) -> str:
        """回傳正規化後文字。

        ``None`` 與空字串會回傳空字串；其他非字串輸入則明確拋出
        ``TypeError``，避免錯誤資料悄悄流入 NLP 管線。
        """

        if text is None or text == "":
            return ""
        if not isinstance(text, str):
            raise TypeError(f"text 必須是 str 或 None，不可使用 {type(text).__name__}")

        normalized = self.cc.convert(text)
        normalized = self._to_halfwidth_ascii(normalized)

        if self.config.punctuation_style == "ascii":
            normalized = normalized.translate(_CJK_TO_ASCII_PUNCTUATION)

        # 統一 Windows/老式 Mac 換行；是否保留換行由設定決定。
        normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
        if self.config.preserve_newlines:
            normalized = "\n".join(
                _WHITESPACE_RE.sub(" ", line).strip() for line in normalized.split("\n")
            )
            return normalized.strip() if self.config.strip else normalized

        normalized = _WHITESPACE_RE.sub(" ", normalized)
        return normalized.strip() if self.config.strip else normalized


# 領域規則集中管理，便於 code review、版本控制與外部覆寫。
DEFAULT_NPL_PATTERNS: tuple[dict[str, Any], ...] = (
    # 多數模型會將英文片語切成兩個 token；字元級 fallback 則兼容 zh
    # blank pipeline 將連續拉丁字母逐字切分的情況。
    {"label": "INDICATOR", "pattern": [{"LOWER": "npl"}, {"LOWER": "ratio"}]},
    {"label": "INDICATOR", "pattern": "NPL Ratio"},
    {
        "label": "INDICATOR",
        "pattern": [
            {"LOWER": "n"},
            {"LOWER": "p"},
            {"LOWER": "l"},
            {"LOWER": "r"},
            {"LOWER": "a"},
            {"LOWER": "t"},
            {"LOWER": "i"},
            {"LOWER": "o"},
        ],
    },
    {"label": "INDICATOR", "pattern": "不良貸款率"},
    {"label": "INDICATOR", "pattern": "不良贷款率"},
    {"label": "INDICATOR", "pattern": "逾期放款比率"},
    {"label": "INDICATOR", "pattern": "備抵呆帳覆蓋率"},
    {"label": "INDICATOR", "pattern": "備抵呆賬覆蓋率"},
    {"label": "INDICATOR", "pattern": "資本適足率"},
    {"label": "CONCEPT", "pattern": "資產品質"},
    {"label": "CONCEPT", "pattern": "系統性風險"},
    {"label": "CONCEPT", "pattern": "信用違約"},
    {"label": "POLICY_ORG", "pattern": "金管會"},
    {"label": "POLICY_ORG", "pattern": "中央銀行"},
)


@dataclass(frozen=True, slots=True)
class NLPConfig:
    """spaCy、輸出與 CPU 執行選項。"""

    model_name: str = DEFAULT_MODEL
    include_punctuation: bool = False
    include_spaces: bool = False
    overwrite_domain_entities: bool = False
    batch_size: int = 64
    n_process: int = 1
    disable_components: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.model_name:
            raise ValueError("model_name 不可為空")
        if self.batch_size < 1:
            raise ValueError("batch_size 必須大於 0")
        if self.n_process < 1:
            raise ValueError("n_process 必須大於 0")


def _pattern_key(pattern: Mapping[str, Any]) -> str:
    """產生穩定鍵值，用於移除重複規則而不改變順序。"""

    return json.dumps(pattern, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


class NLPPreprocessor:
    """spaCy 中文 NLP 與 NPL 領域規則處理器。"""

    def __init__(
        self,
        config: NLPConfig | None = None,
        *,
        nlp: Any | None = None,
        domain_patterns: Sequence[Mapping[str, Any]] | None = None,
    ) -> None:
        self.config = config or NLPConfig()

        if nlp is not None:
            self.nlp = nlp
        else:
            if spacy is None:
                raise RuntimeError(
                    "缺少 spaCy 依賴。請執行：pip install 'spacy>=3.7,<4'"
                ) from None
            try:
                self.nlp = spacy.load(
                    self.config.model_name,
                    disable=list(self.config.disable_components),
                )
            except OSError as exc:
                raise RuntimeError(
                    f"找不到 spaCy 模型 '{self.config.model_name}'。請先執行："
                    f"python -m spacy download {self.config.model_name}"
                ) from exc

        patterns = tuple(domain_patterns or DEFAULT_NPL_PATTERNS)
        self._validate_patterns(patterns)
        self._add_domain_rules(patterns)

    @staticmethod
    def _validate_patterns(patterns: Sequence[Mapping[str, Any]]) -> None:
        for index, pattern in enumerate(patterns):
            if not isinstance(pattern, Mapping):
                raise TypeError(f"第 {index} 條領域規則必須是 mapping")
            if not pattern.get("label") or not pattern.get("pattern"):
                raise ValueError(f"第 {index} 條領域規則必須包含 label 與 pattern")

    def _add_domain_rules(self, patterns: Sequence[Mapping[str, Any]]) -> None:
        """掛載或重用 EntityRuler，並以穩定順序加入去重後的規則。"""

        self._register_phrase_special_cases(patterns)
        self._register_pkuseg_terms(patterns)

        if "entity_ruler" in self.nlp.pipe_names:
            ruler = self.nlp.get_pipe("entity_ruler")
        else:
            if "ner" in self.nlp.pipe_names:
                ruler = self.nlp.add_pipe(
                    "entity_ruler",
                    before="ner",
                    config={"overwrite_ents": self.config.overwrite_domain_entities},
                )
            else:
                ruler = self.nlp.add_pipe(
                    "entity_ruler",
                    config={"overwrite_ents": self.config.overwrite_domain_entities},
                )

        # 對 phrase string 使用目前管線的 tokenizer 編譯，避免模型版本或
        # 中文分詞器把同一片語切成不同 token 後導致規則失效。
        compiled_patterns = []
        for pattern in patterns:
            copied = dict(pattern)
            phrase = copied.get("pattern")
            if isinstance(phrase, str):
                phrase_doc = self.nlp.make_doc(phrase)
                copied["pattern"] = [
                    {"LOWER": token.lower_} for token in phrase_doc if not token.is_space
                ]
            compiled_patterns.append(copied)

        existing = {_pattern_key(item) for item in getattr(ruler, "patterns", [])}
        new_patterns: list[dict[str, Any]] = []
        for copied in compiled_patterns:
            key = _pattern_key(copied)
            if key not in existing:
                new_patterns.append(copied)
                existing.add(key)
        if new_patterns:
            ruler.add_patterns(new_patterns)

    def _register_phrase_special_cases(
        self, patterns: Sequence[Mapping[str, Any]]
    ) -> None:
        """讓領域片語在中文 tokenizer 中保持完整 token 邊界。

        部分中文分詞器會依左右文脈合併字元，例如把「將」與「備」合成
        同一 token，導致實體從 token 中間開始而無法被 EntityRuler 命中。
        對字串型規則註冊 tokenizer special case，可在不改動一般分詞的前提下
        保留領域詞的完整邊界。
        """

        for pattern in patterns:
            phrase = pattern.get("pattern")
            if not isinstance(phrase, str) or not phrase.strip():
                continue
            try:
                self.nlp.tokenizer.add_special_case(phrase, [{ORTH: phrase}])
            except (AttributeError, ValueError):
                # 自訂 tokenizer 可能不支援 special case；token pattern 仍會生效。
                LOGGER.debug("Tokenizer 不支援領域片語 special case：%s", phrase)

    def _register_pkuseg_terms(
        self, patterns: Sequence[Mapping[str, Any]]
    ) -> None:
        """將字串型領域詞加入 pkuseg user dictionary（若目前模型使用 pkuseg）。"""

        tokenizer = getattr(self.nlp, "tokenizer", None)
        if getattr(tokenizer, "segmenter", None) != "pkuseg":
            return
        terms = [
            phrase.strip()
            for pattern in patterns
            if isinstance((phrase := pattern.get("pattern")), str)
            and phrase.strip()
            and not any(char.isspace() for char in phrase.strip())
        ]
        if not terms:
            return
        try:
            tokenizer.pkuseg_update_user_dict(sorted(set(terms)))
        except (AttributeError, ValueError):
            # 若模型的 tokenizer 尚未 initialize，EntityRuler token pattern 仍可使用。
            LOGGER.debug("pkuseg user dictionary 尚未可用，略過領域詞註冊")

    def process(self, text: str | None) -> dict[str, Any]:
        """解析單段文字，輸出 JSON 相容的句子、Token 與實體資料。"""

        if text is None or text == "":
            return {"text": "", "sentences": [], "tokens": [], "entities": []}
        if not isinstance(text, str):
            raise TypeError(f"text 必須是 str 或 None，不可使用 {type(text).__name__}")

        return self._serialize_doc(self.nlp(text))

    def process_many(
        self,
        texts: Iterable[str | None],
        *,
        batch_size: int | None = None,
        n_process: int | None = None,
    ) -> list[dict[str, Any]]:
        """以 ``nlp.pipe`` 批次處理文字；順序與輸入保持一致。"""

        items = list(texts)
        if any(item is not None and not isinstance(item, str) for item in items):
            raise TypeError("texts 中的每個元素都必須是 str 或 None")

        effective_batch_size = (
            self.config.batch_size if batch_size is None else batch_size
        )
        if effective_batch_size < 1:
            raise ValueError("batch_size 必須大於 0")
        effective_n_process = self.config.n_process if n_process is None else n_process
        if effective_n_process < 1:
            raise ValueError("n_process 必須大於 0")

        # 空字串不送入模型，既避免無意義計算，也維持 process() 的一致輸出。
        empty_result = {"text": "", "sentences": [], "tokens": [], "entities": []}
        results: list[dict[str, Any] | None] = [None] * len(items)
        non_empty_indexes: list[int] = []
        non_empty_texts: list[str] = []
        for index, item in enumerate(items):
            if item:
                non_empty_indexes.append(index)
                non_empty_texts.append(item)
            else:
                results[index] = dict(empty_result)

        if not non_empty_texts:
            return [item or dict(empty_result) for item in results]

        parsed = list(
            self.nlp.pipe(
                non_empty_texts,
                batch_size=effective_batch_size,
                n_process=effective_n_process,
            )
        )
        by_index = dict(zip(non_empty_indexes, parsed))
        return [
            self._serialize_doc(by_index[index]) if index in by_index else results[index] or dict(empty_result)
            for index in range(len(items))
        ]

    def _serialize_doc(self, doc: Any) -> dict[str, Any]:
        try:
            sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
        except (AttributeError, ValueError):
            # blank pipeline 未必包含 parser/sentencizer；退回整段文字而非中斷整個服務。
            sentences = [doc.text.strip()] if doc.text.strip() else []
        tokens: list[dict[str, Any]] = []
        for token in doc:
            if not self.config.include_spaces and token.is_space:
                continue
            if not self.config.include_punctuation and token.is_punct:
                continue
            tokens.append(
                {
                    "text": token.text,
                    "lemma": token.lemma_,
                    "pos": token.pos_,
                    "tag": token.tag_,
                    "dep": token.dep_,
                    "is_stop": bool(token.is_stop),
                    "start_char": token.idx,
                    "end_char": token.idx + len(token.text),
                }
            )

        entities = [
            {
                "text": ent.text,
                "label": ent.label_,
                "start": ent.start,
                "end": ent.end,
                "start_char": ent.start_char,
                "end_char": ent.end_char,
            }
            for ent in doc.ents
        ]

        return {
            "text": doc.text,
            "sentences": sentences,
            "tokens": tokens,
            "entities": entities,
        }


def analyze_text(
    text: str | None,
    *,
    normalizer: LanguageNormalizer | None = None,
    preprocessor: NLPPreprocessor | None = None,
) -> dict[str, Any]:
    """便利函式：先正規化，再進行 NLP 解析。"""

    active_normalizer = normalizer or LanguageNormalizer()
    active_preprocessor = preprocessor or NLPPreprocessor()
    normalized = active_normalizer.normalize(text)
    return active_preprocessor.process(normalized)


DEMO_TEXT = """
２０２６年Ｑ１，根据中国某大型商业银行的财报显示，
受房地产市场波动影响，其 NPL Ratio 攀升至 1.85％。
为防范系统性风险，金管会要求将备抵呆账覆盖率提升。
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="中文正規化與 NPL 領域 NLP 預處理器")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="spaCy 模型名稱")
    parser.add_argument("--text", help="直接指定輸入文字；未指定時讀取 stdin")
    parser.add_argument("--demo", action="store_true", help="執行內建示範文字")
    parser.add_argument(
        "--ascii-punctuation",
        action="store_true",
        help="將常見中文標點轉為 ASCII；預設保留中文標點",
    )
    parser.add_argument(
        "--preserve-newlines",
        action="store_true",
        help="保留原始換行與段落邊界",
    )
    parser.add_argument("--json", action="store_true", help="輸出完整 JSON 結果")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    raw_text = (
        DEMO_TEXT
        if args.demo
        else args.text
        if args.text is not None
        else sys.stdin.read()
    )

    if not raw_text.strip():
        print("請透過 --text、--demo 或 stdin 提供文字。", file=sys.stderr)
        return 2

    try:
        normalizer = LanguageNormalizer(
            NormalizationConfig(
                punctuation_style="ascii" if args.ascii_punctuation else "preserve",
                preserve_newlines=args.preserve_newlines,
            )
        )
        preprocessor = NLPPreprocessor(NLPConfig(model_name=args.model))
        result = analyze_text(
            raw_text,
            normalizer=normalizer,
            preprocessor=preprocessor,
        )
    except (RuntimeError, TypeError, ValueError) as exc:
        LOGGER.error("處理失敗：%s", exc)
        return 1

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["text"])
        print("\n辨識到的實體：")
        for entity in result["entities"]:
            print(f"- [{entity['label']}] {entity['text']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "DEFAULT_MODEL",
    "DEFAULT_NPL_PATTERNS",
    "LanguageNormalizer",
    "NLPConfig",
    "NLPPreprocessor",
    "NormalizationConfig",
    "analyze_text",
]
