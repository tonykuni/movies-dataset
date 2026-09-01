"""FastAPI application factory. The API extra is optional."""

from __future__ import annotations

import hmac
import os
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from .engine import VIAEngine


class TokenBucketLimiter:
    def __init__(self, per_minute: int) -> None:
        self.capacity = max(1, per_minute)
        self.rate = self.capacity / 60.0
        self._buckets: dict[str, tuple[float, float]] = {}
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        with self._lock:
            tokens, updated = self._buckets.get(key, (float(self.capacity), now))
            tokens = min(float(self.capacity), tokens + (now - updated) * self.rate)
            allowed = tokens >= 1.0
            self._buckets[key] = (tokens - 1.0 if allowed else tokens, now)
            if len(self._buckets) > 10_000:
                cutoff = now - 600
                self._buckets = {name: value for name, value in self._buckets.items() if value[1] >= cutoff}
            return allowed


def create_app(config_path: str | None = None, overrides: dict[str, Any] | None = None) -> Any:
    try:
        from fastapi import Depends, FastAPI, Header, HTTPException, Request
        from fastapi.responses import FileResponse, HTMLResponse
        from pydantic import BaseModel, Field
    except ImportError as exc:
        raise RuntimeError("Install the 'api' extra to run FastAPI") from exc

    engine = VIAEngine(config_path=config_path, overrides=overrides, auto_start=False)
    security = engine.config["security"]
    limiter = TokenBucketLimiter(int(security["rate_limit_per_minute"]))

    class ProcessBody(BaseModel):
        text: str = Field(min_length=1, max_length=int(engine.config["engine"]["max_text_chars"]))
        task: str = "auto"
        language: str = "auto"
        quality: str = "balanced"
        tier: int | None = Field(default=None, ge=1, le=4)
        options: dict[str, Any] = Field(default_factory=dict)
        request_id: str | None = None

    class BatchBody(BaseModel):
        requests: list[ProcessBody] = Field(min_length=1, max_length=int(engine.config["engine"]["max_batch_items"]))
        job_id: str | None = None
        resume: bool = True

    class FeedbackBody(BaseModel):
        request_id: str
        task: str
        text: str = Field(min_length=1, max_length=int(engine.config["engine"]["max_text_chars"]))
        predicted_label: str | None = None
        corrected_label: str | None = None
        corrected_text: str | None = None
        accepted: bool = True
        note: str = ""

    @asynccontextmanager
    async def lifespan(app: Any):
        engine.start()
        app.state.engine = engine
        yield
        engine.close()

    app = FastAPI(title=engine.config["engine"]["name"], version="1.5.0", lifespan=lifespan)
    dashboard_path = Path(engine.config["_meta"]["project_root"]) / "dashboard" / "index.html"

    @app.middleware("http")
    async def resource_and_rate_guard(request: Request, call_next: Any) -> Any:
        client = request.client.host if request.client else "unknown"
        if not limiter.allow(client):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        content_length = request.headers.get("content-length")
        maximum_body = int(engine.config["engine"]["max_text_chars"]) * 4 + 1_000_000
        try:
            body_too_large = bool(content_length and int(content_length) > maximum_body)
        except ValueError:
            body_too_large = True
        if body_too_large:
            raise HTTPException(status_code=413, detail="Request body too large")
        return await call_next(request)

    def authorize(x_api_key: str | None = Header(default=None)) -> None:
        if not security["require_api_key"]:
            return
        expected = os.environ.get(str(security["api_key_env"]), "")
        if not expected or not x_api_key or not hmac.compare_digest(expected, x_api_key):
            raise HTTPException(status_code=401, detail="Invalid API key")

    @app.get("/health")
    def health() -> dict[str, Any]:
        return engine.health()

    @app.get("/", include_in_schema=False)
    def dashboard() -> Any:
        if dashboard_path.exists():
            return FileResponse(dashboard_path)
        return HTMLResponse("<h1>VIA NLP One Engine</h1><p>Dashboard file is unavailable.</p>")

    @app.post("/v1/process", dependencies=[Depends(authorize)])
    def process(body: ProcessBody) -> dict[str, Any]:
        try:
            return engine.process(body.model_dump()).to_dict()
        except (ValueError, TypeError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    @app.post("/v1/batch", dependencies=[Depends(authorize)])
    def batch(body: BatchBody) -> dict[str, Any]:
        requests = [item.model_dump() for item in body.requests]
        return {"results": engine.process_batch(requests, job_id=body.job_id, resume=body.resume)}

    @app.post("/v1/feedback", dependencies=[Depends(authorize)])
    def feedback(body: FeedbackBody) -> dict[str, Any]:
        return engine.submit_feedback(body.model_dump())

    @app.post("/v1/evolve", dependencies=[Depends(authorize)])
    def evolve(promote: bool = False) -> dict[str, Any]:
        return engine.evolve(promote=promote)

    @app.get("/v1/models", dependencies=[Depends(authorize)])
    def models() -> dict[str, Any]:
        return {"loaded": engine.pool.status(), "machine_learning": engine.classifier.status()}

    @app.post("/v1/jobs", dependencies=[Depends(authorize)])
    def submit_job(body: ProcessBody) -> dict[str, Any]:
        job_id = engine.submit_job(body.model_dump())
        return {"job_id": job_id, "status": "pending"}

    @app.get("/v1/jobs/{job_id}", dependencies=[Depends(authorize)])
    def job_status(job_id: str) -> dict[str, Any]:
        value = engine.jobs.status(job_id)
        if value is None:
            raise HTTPException(status_code=404, detail="Job not found")
        return value

    return app


try:
    app = create_app()
except (RuntimeError, FileNotFoundError):
    app = None
