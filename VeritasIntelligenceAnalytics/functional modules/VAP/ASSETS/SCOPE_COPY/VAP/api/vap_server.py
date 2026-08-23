#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  APM-012: vap_server.py - FastAPI Backend Server                           ║
║  Module ID: APM-012 | Version: 4.0.0                                       ║
║  REST endpoints: /data, /chart, /template, /export, /health               ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
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

import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from vap_config import VAPPaths
from vap_data_adapter import VAPDataAdapter
from vap_indicators import VAPIndicatorEngine
from vap_templates import VAPTemplateManager
from vap_export import VAPExportEngine

logger = logging.getLogger(__name__)

app = FastAPI(
    title="VeritasAutoPlot API",
    version="4.0.0",
    description="Financial charting & dashboard automation API",
)

# Singletons
adapter = VAPDataAdapter()
template_mgr = VAPTemplateManager()
export_engine = VAPExportEngine()


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "version": "4.0.0",
        "root": str(VAPPaths.ROOT),
        "vdf_root": str(VAPPaths.VDF_ROOT),
        "templates": len(template_mgr.list_templates()),
    }


@app.get("/data/sources")
def list_data_sources():
    return adapter.list_vdf_sources()


@app.get("/data/load")
def load_data(source: str, rows: Optional[int] = Query(None)):
    try:
        df = adapter.auto_load(source)
        if rows:
            df = df.tail(rows)
        return JSONResponse({
            "shape": list(df.shape),
            "columns": list(df.columns),
            "index_start": str(df.index[0]) if len(df) > 0 else None,
            "index_end": str(df.index[-1]) if len(df) > 0 else None,
            "dtypes": {c: str(df[c].dtype) for c in df.columns},
            "sample": df.tail(5).to_dict(orient="records"),
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/data/demo")
def get_demo_data(ticker: str = "2330.TW", days: int = 500):
    df = adapter.generate_demo_data(ticker=ticker, days=days)
    return JSONResponse({
        "shape": list(df.shape),
        "columns": list(df.columns),
        "data": df.tail(10).reset_index().to_dict(orient="records"),
    })


@app.get("/indicators/compute")
def compute_indicators(source: str = "demo", indicators: str = "standard"):
    """
    Compute indicators on data.
    indicators: "standard" | "all" | comma-separated list (e.g. "sma,rsi,macd")
    """
    try:
        if source == "demo":
            df = adapter.generate_demo_data()
        else:
            df = adapter.auto_load(source)

        engine = VAPIndicatorEngine(df)

        if indicators == "standard":
            engine.compute_standard_set()
        elif indicators == "all":
            engine.compute_all()
        else:
            for ind in indicators.split(","):
                ind = ind.strip().upper()
                try:
                    engine.compute_by_name(ind)
                except ValueError:
                    logger.warning(f"Unknown indicator: {ind}")

        result = engine.get_result()
        computed_cols = [c for c in result.columns if c not in df.columns]

        return JSONResponse({
            "original_columns": list(df.columns),
            "computed_columns": computed_cols,
            "total_columns": len(result.columns),
            "rows": len(result),
            "close_column_used": engine.col_map["close"],
            "sample": result[computed_cols].tail(5).to_dict(orient="records"),
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/templates")
def list_templates():
    return template_mgr.list_templates()


@app.get("/templates/{name}")
def get_template(name: str):
    try:
        return template_mgr.load(name)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Template not found: {name}")


@app.post("/templates/{name}")
def save_template(name: str, config: dict):
    path = template_mgr.save(name, config)
    return {"status": "saved", "path": str(path)}


@app.delete("/templates/{name}")
def delete_template(name: str):
    if template_mgr.delete(name):
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Template not found")


def run_server(host: str = "0.0.0.0", port: int = 8080):
    """Launch the API server."""
    # Mount frontend static files if available
    frontend_dir = VAPPaths.FRONTEND
    if frontend_dir.exists():
        app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")

    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    run_server()
