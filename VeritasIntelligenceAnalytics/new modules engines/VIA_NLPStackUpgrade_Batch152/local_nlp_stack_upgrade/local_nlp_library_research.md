# Local CPU-Friendly Library Selection Notes

The implementation targets a fully local/offline pipeline and treats optional libraries as adapters with graceful fallbacks.

| Library | Role | Local/CPU rationale | Official source |
|---|---|---|---|
| spaCy | pipeline, POS, dependency parsing, NER, EntityRuler | Local packaged models and pipeline APIs; retain small Chinese model by default. | https://spacy.io/usage/models |
| OpenCC | Simplified/Traditional conversion | Deterministic local conversion; no network dependency at runtime. | https://github.com/BYVoid/OpenCC |
| pkuseg | Chinese segmentation and domain dictionary | Provides local multi-domain Chinese segmentation and user dictionaries. | https://github.com/lancopku/pkuseg-python |
| jieba | lightweight fallback segmentation | Pure-Python/simple fallback when spaCy or pkuseg is unavailable. | https://pypi.org/project/jieba/ |
| regex | Unicode-aware regular expressions | Local drop-in regex engine useful for robust numeric and phrase patterns. | https://pypi.org/project/regex/ |
| RapidFuzz | fuzzy entity/indicator alias matching | Compiled CPU implementation with a Python fallback; suitable for approximate local matching. | https://rapidfuzz.github.io/RapidFuzz/ |
| dateparser | local date/time normalization | Optional parser for date expressions; no hosted API required. | https://dateparser.readthedocs.io/ |
| quantulum3 | local quantity/unit parsing | Optional extraction and normalization of quantities and units. | https://github.com/nielstron/quantulum3 |
| scikit-learn | TF-IDF/keyword scoring | CPU-native sparse-vector utilities; optional ranking layer, not a required model. | https://scikit-learn.org/stable/ |
| NetworkX | local knowledge graph representation | In-process graph storage and traversal; no database or network service required. | https://networkx.org/documentation/stable/ |

Implementation decision: the core pipeline remains usable with only the required baseline dependencies. The ten libraries are exposed through capability adapters; missing optional dependencies are reported in diagnostics and replaced with deterministic standard-library or existing-engine fallbacks. No cloud API, remote inference endpoint, or background service is required at runtime.
