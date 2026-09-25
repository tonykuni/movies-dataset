# Local CPU NLP Stack Verification Report

## Scope

The two supplied code paths are now combined into a CPU-first local stack:

| Module | Responsibility |
|---|---|
| `npl_preprocessor.py` | OpenCC normalization, local spaCy parsing, tokenizer-aware NPL EntityRuler rules, offsets, and batch parsing. |
| `knowledge_extraction_engine.py` | Metric, trend, numeric, causation, policy-action, influence, keyword, alias, and graph extraction. |
| `local_knowledge_engine.py` | One-process orchestration, CPU limits, ten-library diagnostics, segmentation adapters, and JSON-safe graph output. |

## Native capability smoke test

The smoke test executed the complete local pipeline and reported **2 extracted triples** and **4 graph nodes**. It identified the metric relation `NPL Ratio --攀升至--> 1.85%` and the causation relation `房地產市場波動 --causes (受影響)--> 其 NPL Ratio 攀升至 1.85%`.

| # | Library | Status in validation environment | Integration |
|---:|---|---|---|
| 1 | spaCy | Native | Local Chinese model, POS, dependency parsing, NER, EntityRuler, `nlp.pipe`. |
| 2 | OpenCC | Native | `s2twp` normalization with `.json` suffix compatibility. |
| 3 | pkuseg | Fallback | Adapter and user-dictionary hook implemented; legacy release did not build cleanly on Python 3.12. |
| 4 | jieba | Native | Local segmentation fallback. |
| 5 | `regex` | Native | Unicode-aware extraction patterns. |
| 6 | RapidFuzz | Native | Fuzzy alias canonicalization. |
| 7 | dateparser | Native | Optional DATE metadata enrichment. |
| 8 | quantulum3 | Native | Optional quantity/unit metadata enrichment. |
| 9 | scikit-learn | Native | Local TF-IDF keyword ranking. |
| 10 | NetworkX | Native | Directed in-process graph export. |

## Tests

Both suites passed:

| Suite | Result |
|---|---:|
| `test_npl_preprocessor.py` | 8/8 passed |
| `test_knowledge_extraction_engine.py` | 8/8 passed |
| Syntax compilation | Passed |
| End-to-end local model smoke test | Passed |
| One-command CLI (`--status`, `--segment`, `--demo --json`) | Passed |

The tests cover input validation, full-width normalization, punctuation and newline modes, entity offsets, NPL aliases, numeric percentages and currencies, causation and policy parsing, deduplication, graph output, keyword ranking, CPU defaults, optional-library status, segmentation, batch order, CLI behavior, and end-to-end local model execution. The CLI status command reported all ten library entries, with nine native capabilities and pkuseg in fallback mode in this Python 3.12 environment.

## Installation caveat

`pkuseg` is included as an optional adapter. The current legacy release available in the environment failed to build under Python 3.12 because its isolated build did not declare NumPy correctly. The application therefore keeps pkuseg optional, uses spaCy's local Chinese tokenizer/model path when available, and falls back to jieba or a deterministic regex segmenter. The other optional native paths were installed and exercised successfully.

## References

[1]: https://spacy.io/usage/models "spaCy Models & Languages"
[2]: https://github.com/BYVoid/OpenCC "OpenCC official repository"
[3]: https://github.com/lancopku/pkuseg-python "pkuseg official repository"
[4]: https://pypi.org/project/jieba/ "jieba on PyPI"
[5]: https://pypi.org/project/regex/ "regex on PyPI"
[6]: https://rapidfuzz.github.io/RapidFuzz/ "RapidFuzz documentation"
[7]: https://dateparser.readthedocs.io/ "dateparser documentation"
[8]: https://github.com/nielstron/quantulum3 "quantulum3 official repository"
[9]: https://scikit-learn.org/stable/ "scikit-learn documentation"
[10]: https://networkx.org/documentation/stable/ "NetworkX documentation"
