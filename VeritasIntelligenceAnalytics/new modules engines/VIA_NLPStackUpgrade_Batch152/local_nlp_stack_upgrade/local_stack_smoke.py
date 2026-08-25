from __future__ import annotations

import json

from local_knowledge_engine import CPUSettings, LocalKnowledgePipeline, library_status

pipeline = LocalKnowledgePipeline(cpu=CPUSettings(threads=1, n_process=1, batch_size=8))
result = pipeline.analyze(
    "２０２６年Ｑ１，根据中国某大型商业银行的财报显示，"
    "受房地产市场波动影响，其 NPL Ratio 攀升至 1.85％。"
)
print(json.dumps({
    "libraries": library_status(),
    "normalized_text": result["normalized_text"],
    "triple_count": len(result["triples"]),
    "triples": result["triples"],
    "graph_node_count": len(result["graph"]["nodes"]),
    "segments": LocalKnowledgePipeline.segment("NPL Ratio 1.85% 風險", backend="auto"),
    "keywords": pipeline.rank_keywords([result["normalized_text"]], top_k=5),
}, ensure_ascii=False, indent=2))
