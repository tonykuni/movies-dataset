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
import http.server
import json
import os
import pathlib
import socketserver
import sys


def load_manifest(path: str) -> dict:
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8-sig"))


def health(manifest_path: str) -> int:
    data = load_manifest(manifest_path)
    rows = data.get("libraries", [])
    missing = [r for r in rows if not pathlib.Path(r.get("path", "")).exists()]
    bad = [r for r in rows if not bool(r.get("parse_ok", False))]
    result = {
        "status": "OK" if not missing and not bad else "REVIEW",
        "library_count": len(rows),
        "missing_count": len(missing),
        "parse_bad_count": len(bad),
        "import_executed": False,
    }
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "OK" else 2


def serve(root: str, port: int) -> int:
    os.chdir(root)
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("127.0.0.1", port), handler) as httpd:
        print(f"VIA UI serving at http://127.0.0.1:{port}", flush=True)
        httpd.serve_forever()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest")
    parser.add_argument("--health", action="store_true")
    parser.add_argument("--serve-root")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    if args.health:
        if not args.manifest:
            print("--manifest is required", file=sys.stderr)
            return 2
        return health(args.manifest)
    if args.serve_root:
        return serve(args.serve_root, args.port)
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
