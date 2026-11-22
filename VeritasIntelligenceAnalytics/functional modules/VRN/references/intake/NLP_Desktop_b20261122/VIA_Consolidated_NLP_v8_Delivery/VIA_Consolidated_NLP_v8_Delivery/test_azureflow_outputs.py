from __future__ import annotations

import hashlib
import json
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

BASE = "http://127.0.0.1:8766"
SOURCE = """這是一段   測試文字。\n\n請把內容重新整理，輸出 SUMMARY、程式規格與 HTML UI 規格。\ncommand: python app.py   --mode=test\n\n原文不可刪除，修正後內容必須可追溯。"""
OUTPUTS = [
    "corrected_content",
    "source_preserved",
    "summary_v5",
    "summary_markdown",
    "program_spec",
    "program_structure",
    "dashboard_snapshot",
    "markdown",
    "html",
    "record",
]


def request(path: str, payload: dict | None = None) -> dict | bytes:
    if payload is None:
        req = Request(BASE + path, method="GET")
    else:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = Request(BASE + path, data=raw, method="POST", headers={"Content-Type": "application/json"})
    with urlopen(req, timeout=30) as response:
        body = response.read()
        content_type = response.headers.get("Content-Type", "")
        if "application/json" in content_type:
            return json.loads(body.decode("utf-8"))
        return body


def main() -> int:
    payload = {
        "filename": "azureflow_sample.txt",
        "source_text": SOURCE,
        "engine_ids": ["VIA-ENG-022"],
        "output_formats": OUTPUTS,
        "output_to_downloads": False,
        "command_threshold": 0.45,
    }
    queued = request("/api/reconstruct", payload)
    job_id = queued["job_id"]
    job = None
    for _ in range(120):
        job = request(f"/api/job/{job_id}")
        if job["status"] in {"completed", "failed"}:
            break
        time.sleep(0.25)
    if not job or job["status"] != "completed":
        raise AssertionError({"status": "job_failed", "job": job})
    missing = [name for name in OUTPUTS if name not in job.get("artifacts", {})]
    if missing:
        raise AssertionError({"missing_artifacts": missing, "artifacts": job.get("artifacts")})
    fetched: dict[str, bytes] = {}
    for logical in OUTPUTS:
        fetched[logical] = request(f"/api/artifact/{job_id}/{logical}")
        if not fetched[logical]:
            raise AssertionError(f"empty artifact: {logical}")
    def text(value: bytes | dict) -> str:
        return value.decode("utf-8") if isinstance(value, bytes) else json.dumps(value, ensure_ascii=False)

    corrected = text(fetched["corrected_content"])
    preserved = text(fetched["source_preserved"])
    summary = text(fetched["summary_markdown"])
    program = text(fetched["program_spec"])
    html = text(fetched["html"])
    dashboard = fetched["dashboard_snapshot"] if isinstance(fetched["dashboard_snapshot"], dict) else json.loads(text(fetched["dashboard_snapshot"]))
    record = fetched["record"] if isinstance(fetched["record"], dict) else json.loads(text(fetched["record"]))
    assert "# 修正後重整內容" in corrected
    assert preserved == SOURCE
    assert "# SUMMARY" in summary
    assert "# 程式／模組規格" in program
    assert "VIA Consolidated NLP" in html
    assert dashboard["schema"] == "VIA_AZUREFLOW_DASHBOARD/1.0"
    assert record["source"]["source_sha256"] == hashlib.sha256(SOURCE.encode("utf-8")).hexdigest()
    assert record["quality_gates"].get("v8_source_preserved") is True
    assert record["quality_gates"].get("v8_source_mutated") is False
    print(json.dumps({
        "status": "PASS",
        "job_id": job_id,
        "artifact_count": len(job["artifacts"]),
        "verified_outputs": OUTPUTS,
        "source_preserved": preserved == SOURCE,
        "source_sha256_match": record["source"]["source_sha256"] == hashlib.sha256(SOURCE.encode("utf-8")).hexdigest(),
        "dashboard_schema": dashboard["schema"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
