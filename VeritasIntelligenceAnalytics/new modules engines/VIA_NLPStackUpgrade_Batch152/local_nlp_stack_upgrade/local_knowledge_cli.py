"""Command-line entry point for the CPU-friendly local knowledge stack."""

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
import sys
from typing import Sequence

from local_knowledge_engine import CPUSettings, LocalKnowledgePipeline, library_status


DEMO_TEXT = """
２０２６年Ｑ１，根据中国某大型商业银行的财报显示，
受房地产市场波动影响，其 NPL Ratio 攀升至 1.85％。
为防范系统性风险，金管会要求将备抵呆账覆盖率提升。
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CPU-friendly offline local knowledge extraction")
    parser.add_argument("--text", help="Input text; otherwise read stdin")
    parser.add_argument("--demo", action="store_true", help="Use built-in demonstration text")
    parser.add_argument("--status", action="store_true", help="Print ten-library capability status")
    parser.add_argument("--segment", action="store_true", help="Print local segmentation instead of extraction")
    parser.add_argument("--segmenter", default="auto", choices=("auto", "pkuseg", "jieba", "regex"))
    parser.add_argument("--model", default="zh_core_web_sm", help="Local spaCy model name")
    parser.add_argument("--threads", type=int, default=1, help="BLAS/OpenMP thread limit")
    parser.add_argument("--batch-size", type=int, default=32, help="spaCy batch size")
    parser.add_argument("--ascii-punctuation", action="store_true")
    parser.add_argument("--preserve-newlines", action="store_true")
    parser.add_argument("--json", action="store_true", help="Print JSON output")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.status:
        print(json.dumps(library_status(), ensure_ascii=False, indent=2))
        return 0

    raw_text = DEMO_TEXT if args.demo else args.text if args.text is not None else sys.stdin.read()
    if not raw_text.strip():
        print("Provide --text, --demo, or stdin input.", file=sys.stderr)
        return 2

    try:
        if args.segment:
            result = LocalKnowledgePipeline.segment(raw_text, backend=args.segmenter)
        else:
            pipeline = LocalKnowledgePipeline(
                model_name=args.model,
                cpu=CPUSettings(threads=args.threads, batch_size=args.batch_size),
                punctuation_style="ascii" if args.ascii_punctuation else "preserve",
                preserve_newlines=args.preserve_newlines,
            )
            result = pipeline.analyze(raw_text)
    except (RuntimeError, TypeError, ValueError) as exc:
        print(f"Processing failed: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    elif args.segment:
        print("\n".join(result))
    else:
        print(result["normalized_text"])
        for triple in result["triples"]:
            print(f"- {triple['subject']} --{triple['predicate']}--> {triple['object']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
