# CPU-Friendly Local Knowledge Extraction Stack

This upgrade combines the existing `npl_preprocessor.py` with the new `knowledge_extraction_engine.py` and `local_knowledge_engine.py`. It is designed for a small CPU host, runs in one process by default, and does not require a cloud API or a remote inference endpoint at runtime.

> The required path remains deterministic: OpenCC normalizes text, spaCy performs local parsing and entity recognition, and the extraction engine produces metric, causation, policy-action, and influence triples.

## Ten implemented local libraries

| # | Library | Implemented role | Runtime mode |
|---:|---|---|---|
| 1 | spaCy | Local pipeline, POS, dependency parsing, NER, and EntityRuler. The default is `zh_core_web_sm`. [1] | Required |
| 2 | OpenCC | Simplified/Traditional Chinese conversion. [2] | Required |
| 3 | pkuseg | Domain-aware Chinese segmentation and user dictionary integration when available. [3] | Optional |
| 4 | jieba | Lightweight local segmentation fallback. [4] | Optional |
| 5 | `regex` | Unicode-aware regular-expression engine for numeric and causation patterns. [5] | Optional |
| 6 | RapidFuzz | CPU-friendly fuzzy alias matching for indicators and entities. [6] | Optional |
| 7 | dateparser | Local date normalization for DATE entities. [7] | Optional |
| 8 | quantulum3 | Local quantity and unit enrichment. [8] | Optional |
| 9 | scikit-learn | CPU TF-IDF keyword ranking. [9] | Optional |
| 10 | NetworkX | In-process directed graph representation of extracted triples. [10] | Optional |

Optional libraries are detected at runtime. If one is missing, the system uses a standard-library or built-in fallback instead of failing the entire pipeline. This means the stack remains usable in restricted/offline environments after dependencies and local spaCy model files have been provisioned.

## Installation

```bash
pip install -r requirements_local_nlp.txt
python -m spacy download zh_core_web_sm
```

For a completely disconnected deployment, download the wheels and the spaCy model on a connected build machine, copy them into the target environment, and install from the local files. Runtime code does not initiate network access.

The `pkuseg` package is marked as a Python-version-conditional optional dependency because its legacy release may not build on Python 3.12+. The spaCy Chinese model can still use its own pkuseg adapter where configured, and `jieba` plus the deterministic regex segmenter provide local fallbacks.

## One-shot local pipeline

```python
from local_knowledge_engine import CPUSettings, LocalKnowledgePipeline

pipeline = LocalKnowledgePipeline(
    model_name="zh_core_web_sm",
    cpu=CPUSettings(
        threads=1,
        n_process=1,
        batch_size=32,
    ),
)

result = pipeline.analyze(
    "２０２６年Ｑ１，根据中国银行财报，NPL Ratio 攀升至 1.85％。"
)

print(result["normalized_text"])
print(result["triples"])
print(result["graph"])
```

For multiple documents, use `pipeline.analyze_many(texts)`. It normalizes and parses in order, preserves empty items, and uses spaCy's local batch API with `n_process=1` by default to avoid process-spawn overhead on a CPU-only host.

## One-command CLI

```bash
# Show all ten native/fallback capability states
python local_knowledge_cli.py --status

# Run the complete local extractor
python local_knowledge_cli.py --demo --json

# Use a dependency-free segmentation fallback
python local_knowledge_cli.py --segment --segmenter regex --text "NPL Ratio 1.85% 風險"
```

## Capability diagnostics

```python
from local_knowledge_engine import library_status

for item in library_status():
    print(item["library"], item["mode"], item["installed"])
```

The diagnostic list always contains exactly ten entries. Each entry reports whether the native library is installed and whether the implementation is currently using `native` or `fallback` mode.

## What changed in the extraction engine

The original extraction code has been upgraded in several important areas. It now accepts configurable span limits and confidence thresholds, uses named regex groups, handles both Traditional and Simplified Chinese causation cues, normalizes percentage and currency values with `Decimal`, adds numeric entities when the upstream parser did not provide them, and retains source offsets where available.

Policy extraction now prefers a recognized organization entity and avoids incorrectly using a preceding purpose clause as the actor. Domain aliases can be canonicalized with RapidFuzz. The engine can export triples to NetworkX or to a JSON-safe `{nodes, edges}` fallback, and it can rank local keywords with scikit-learn TF-IDF or a standard-library frequency fallback.

## Tests

```bash
python test_npl_preprocessor.py
python test_knowledge_extraction_engine.py
python local_stack_smoke.py
```

The test suite covers normalization, tokenizer-aware entity rules, batch order, numeric enrichment, causation and policy extraction, graph export, keyword ranking, CPU defaults, ten-library diagnostics, regex segmentation, CLI behavior, and end-to-end local model execution.

## Delivered files

| File | Purpose |
|---|---|
| `npl_preprocessor.py` | Existing upgraded normalizer and spaCy preprocessor. |
| `knowledge_extraction_engine.py` | Upgraded deterministic extraction engine. |
| `local_knowledge_engine.py` | CPU settings, ten-library adapters, orchestration, and fallbacks. |
| `local_knowledge_cli.py` | One-command status, segmentation, and extraction interface. |
| `requirements_local_nlp.txt` | Core and optional dependencies. |
| `test_npl_preprocessor.py` | Preprocessor tests. |
| `test_knowledge_extraction_engine.py` | Engine and local-stack tests. |

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
