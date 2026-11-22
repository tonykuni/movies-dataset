from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "v8"))
from via_consolidated_nlp_v8 import artifact_payloads_v8, process_path_v8  # noqa: E402


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.\-\u3400-\u9fff（）()\[\] ]+", "_", Path(value).name).strip(" .") or "input"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="VIA Consolidated NLP v8; source-preserving and static-only.")
    parser.add_argument("inputs", nargs="+", help="input files")
    parser.add_argument("--out", required=True, help="output directory")
    parser.add_argument("--quality", default="balanced", choices=["fast", "balanced", "deep"])
    args = parser.parse_args(argv)
    out = Path(args.out).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, object]] = []
    for raw in args.inputs:
        path = Path(raw).expanduser().resolve(strict=True)
        if not path.is_file():
            raise SystemExit(f"not a file: {path}")
        target = out / safe_name(path.name)
        target.mkdir(parents=True, exist_ok=True)
        result = process_path_v8(path, quality=args.quality)
        payloads = artifact_payloads_v8(result)
        for filename, payload in payloads.items():
            destination = target / filename
            if isinstance(payload, str):
                destination.write_text(payload, encoding="utf-8")
            else:
                destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        manifest.append({
            "input": path.name,
            "source_sha256": result["projection"]["source"]["source_sha256"],
            "output_directory": str(target),
            "payload_count": len(payloads),
            "modules": len(result["modules"]),
            "ast_parse_status": result["ast_modules"]["parse_status"],
            "source_preserved": result["projection"]["quality"]["v8_source_preserved"],
            "execution_authorized": result["projection"]["quality"]["ast_execution_authorized"],
        })
    (out / "v8_manifest.json").write_text(json.dumps({"schema": "VIA_CONSOLIDATED_NLP_MANIFEST/8.0", "items": manifest}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "items": manifest, "out": str(out)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
