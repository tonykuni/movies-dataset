from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:8766"
ROOT = Path(__file__).resolve().parents[1]


def request(path: str, method: str = "GET", payload: dict | None = None) -> tuple[int, dict | bytes]:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=30) as response:
        body = response.read()
        content_type = response.headers.get("Content-Type", "")
        if "json" in content_type:
            return response.status, json.loads(body.decode("utf-8"))
        return response.status, body


def main() -> int:
    checks: dict[str, str] = {}
    status, health = request("/api/health")
    assert status == 200 and health["version"] == "8.0.0" and health["source_write"] is False
    checks["health"] = "PASS"

    status, catalog = request("/api/catalog")
    assert status == 200 and catalog["schema"] == "VIA_NLP_CONTROL_CATALOG/8.0"
    engine_ids = {item["engine_id"] for item in catalog["engines"]}
    assert {"VIA-ENG-022", "VIA-MOD-001", "VIA-MOD-007"}.issubset(engine_ids)
    assert len(catalog["engines"]) == 8
    assert "v8_unified" in {item["id"] for item in catalog["output_formats"]}
    checks["catalog"] = "PASS"

    source = "# v8 API fixture\n\n這是一段  混合文字。\n\nimport os\ndef demo(value):\n    return value\n"
    payload = {
        "source_text": source,
        "filename": "v8_api_fixture.py",
        "command_threshold": 0.45,
        "engine_ids": ["VIA-ENG-022", "VIA-MOD-001", "VIA-MOD-002", "VIA-MOD-003", "VIA-MOD-004", "VIA-MOD-005", "VIA-MOD-006", "VIA-MOD-007"],
        "output_formats": ["markdown", "html", "record", "v8_unified", "v8_ast_modules", "v8_mind_map", "v7_unified"],
        "output_to_downloads": False,
    }
    status, created = request("/api/reconstruct", method="POST", payload=payload)
    assert status == 202 and created.get("job_id")
    job_id = created["job_id"]
    for _ in range(80):
        _, job = request(f"/api/job/{job_id}")
        if job["status"] in {"completed", "failed"}:
            break
        time.sleep(0.25)
    assert job["status"] == "completed", job
    assert job["metrics"]["v8_modules"] == 7
    assert job["metrics"]["v8_source_preserved"] is True
    checks["reconstruct"] = "PASS"

    for logical in ("v8_unified", "v8_ast_modules", "v8_mind_map", "v7_unified", "markdown", "html", "record"):
        status, body = request(f"/api/artifact/{job_id}/{urllib.parse.quote(logical)}")
        assert status == 200 and body
    checks["artifacts"] = "PASS"

    try:
        request(f"/api/artifact/{job_id}/../../via_nlp_control_api_v8.py")
    except urllib.error.HTTPError as exc:
        assert exc.code == 404
    else:
        raise AssertionError("path traversal was not blocked")
    checks["path_safety"] = "PASS"

    result = {"schema": "VIA_V8_CONTROL_CENTER_E2E/1.0", "status": "PASS", "job_id": job_id, "checks": checks, "artifact_count": len(job.get("artifacts", {}))}
    output = ROOT / "v8" / "v8_control_center_e2e.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
