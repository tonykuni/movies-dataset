"""Command-line interface for local operation and testing."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .bundle_ops import export_reconstruction_package, read_document_bundle
from .engine import VIAEngine
from .ingest import read_local_document
from .mindmap_evolution import build_mind_map_evolution, load_previous_reconstruction
from .provider_registry import LocalProviderRegistry


def _read_input(args: argparse.Namespace) -> str:
    if args.text is not None:
        return args.text
    if args.file is not None:
        return str(read_local_document(args.file)["text"])
    if not sys.stdin.isatty():
        return sys.stdin.read()
    raise ValueError("Provide --text, --file, or pipe text through stdin")


def _json_print(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="via-nlp", description="VIA NLP One Engine")
    parser.add_argument("--config", help="Path to JSON configuration")
    sub = parser.add_subparsers(dest="command", required=True)

    process = sub.add_parser("process", help="Process one article or text")
    process.add_argument("--task", default="auto")
    process.add_argument("--quality", choices=["fast", "balanced", "deep"], default="balanced")
    process.add_argument("--tier", type=int, choices=[1, 2, 3, 4])
    source = process.add_mutually_exclusive_group()
    source.add_argument("--text")
    source.add_argument("--file", type=Path)
    process.add_argument("--top-k", type=int, default=10)
    process.add_argument("--backend", choices=["argos", "google_cloud", "ollama"])
    process.add_argument("--source-language", default="zh")
    process.add_argument("--target-language", default="en")
    process.add_argument("--max-chunk-chars", type=int, default=4500)
    process.add_argument("--allow-network", action="store_true")

    reconstruct = sub.add_parser(
        "reconstruct-bundle",
        help="Reconstruct knowledge and code from many discussion files",
    )
    reconstruct.add_argument("--input", type=Path, nargs="+", required=True, help="One or more files or directories")
    reconstruct.add_argument("--output-dir", type=Path, default=Path("VIA_Reconstruction_Output"))
    reconstruct.add_argument("--task", choices=["knowledge", "govern"], default="knowledge")
    reconstruct.add_argument("--quality", choices=["fast", "balanced"], default="balanced")
    reconstruct.add_argument("--recursive", action=argparse.BooleanOptionalAction, default=True)
    reconstruct.add_argument("--max-files", type=int, default=1000)
    reconstruct.add_argument("--max-total-bytes", type=int, default=512 * 1024 * 1024)
    reconstruct.add_argument("--max-file-bytes", type=int, default=50 * 1024 * 1024)
    reconstruct.add_argument(
        "--markitdown",
        action="store_true",
        help="Use installed Microsoft MarkItDown for local conversion; plugins, LLMs and URLs stay disabled",
    )
    reconstruct.add_argument(
        "--previous-package",
        type=Path,
        help="Optional previous VIA_Knowledge_Full.json or VIA_MindMap.json for append-only evolution diff",
    )

    sub.add_parser("health", help="Show health and capability status")
    sub.add_parser("providers", help="Show read-only availability of optional local providers")

    serve = sub.add_parser("serve", help="Run the local FastAPI server")
    serve.add_argument("--host")
    serve.add_argument("--port", type=int)

    feedback = sub.add_parser("feedback", help="Record classification feedback")
    feedback.add_argument("--request-id", required=True)
    feedback.add_argument("--task", default="classify")
    feedback.add_argument("--text", required=True)
    feedback.add_argument("--predicted-label")
    feedback.add_argument("--corrected-label")
    feedback.add_argument("--accepted", action=argparse.BooleanOptionalAction, default=True)

    evolve = sub.add_parser("evolve", help="Train and validate a candidate ML model")
    evolve.add_argument("--promote", action="store_true", help="Promote only when all quality gates pass")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "serve":
        try:
            import uvicorn
        except ImportError as exc:
            raise RuntimeError("Install the 'api' extra to run the server") from exc
        engine = VIAEngine(config_path=args.config, auto_start=False)
        security = engine.config["security"]
        host = args.host or security["bind_host"]
        port = args.port or int(security["bind_port"])
        if host not in {"127.0.0.1", "localhost", "::1"} and not security["allow_remote_bind"]:
            raise RuntimeError("Remote bind is blocked; explicitly set security.allow_remote_bind=true")
        engine.close()
        from .api import create_app

        uvicorn.run(create_app(args.config), host=host, port=port, workers=1)
        return 0

    if args.command == "providers":
        _json_print(LocalProviderRegistry().status())
        return 0

    with VIAEngine(config_path=args.config) as engine:
        if args.command == "health":
            _json_print(engine.health())
        elif args.command == "process":
            text = _read_input(args)
            result = engine.process(
                {
                    "text": text,
                    "task": args.task,
                    "quality": args.quality,
                    "tier": args.tier,
                    "options": {
                        "top_k": args.top_k,
                        "backend": args.backend,
                        "source_language": args.source_language,
                        "target_language": args.target_language,
                        "max_chunk_chars": args.max_chunk_chars,
                        "allow_network": args.allow_network,
                    },
                }
            )
            _json_print(result.to_dict())
        elif args.command == "reconstruct-bundle":
            bundle = read_document_bundle(
                args.input,
                recursive=args.recursive,
                max_files=args.max_files,
                max_total_bytes=args.max_total_bytes,
                max_file_bytes=args.max_file_bytes,
                use_markitdown=args.markitdown,
            )
            text = bundle["text"]
            maximum = int(engine.config["engine"]["max_text_chars"])
            if len(text) > maximum:
                raise ValueError(
                    f"Combined extracted text has {len(text)} characters; configured maximum is {maximum}. "
                    "Split the inputs into multiple reviewed bundles instead of silently truncating."
                )
            result = engine.process(
                {
                    "text": text,
                    "task": args.task,
                    "quality": args.quality,
                    "options": {"bundle_mode": True, "source_record_count": len(bundle["source_record_ledger"])},
                }
            )
            result_payload = result.to_dict()
            if args.previous_package is not None:
                previous = load_previous_reconstruction(args.previous_package)
                output = result_payload["output"]
                output["mind_map_evolution"] = build_mind_map_evolution(
                    output["mind_map"],
                    previous=previous,
                    conflict_register=output["knowledge_object_registry"]["conflict_register"],
                )
            package = export_reconstruction_package(args.output_dir, bundle, result_payload)
            _json_print(
                {
                    "output_directory": package["output_directory"],
                    "archive": package["archive"],
                    "archive_sha256": package["archive_sha256"],
                    "summary": package["summary"],
                }
            )
        elif args.command == "feedback":
            _json_print(
                engine.submit_feedback(
                    {
                        "request_id": args.request_id,
                        "task": args.task,
                        "text": args.text,
                        "predicted_label": args.predicted_label,
                        "corrected_label": args.corrected_label,
                        "accepted": args.accepted,
                    }
                )
            )
        elif args.command == "evolve":
            _json_print(engine.evolve(promote=args.promote))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
