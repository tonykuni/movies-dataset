#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  APM-005: vap_templates.py - Template Manager                              ║
║  Module ID: APM-005 | Version: 4.0.0                                       ║
║  Save/Load/Delete/Export JSON templates, auto-update pipeline              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from vap_config import VAPPaths

logger = logging.getLogger(__name__)


class VAPTemplateManager:
    """CRUD manager for chart configuration templates (JSON)."""

    def __init__(self, template_dir: Optional[Path] = None):
        self.template_dir = template_dir or VAPPaths.TEMPLATES
        self.template_dir.mkdir(parents=True, exist_ok=True)

    def save(self, name: str, config: dict) -> Path:
        config["_meta"] = {
            "name": name,
            "created": datetime.now().isoformat(),
            "version": "4.0.0",
        }
        path = self.template_dir / f"{name}.json"
        path.write_text(json.dumps(config, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
        logger.info(f"Template saved: {path}")
        return path

    def load(self, name: str) -> dict:
        path = self.template_dir / f"{name}.json"
        if not path.exists():
            raise FileNotFoundError(f"Template not found: {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    def delete(self, name: str) -> bool:
        path = self.template_dir / f"{name}.json"
        if path.exists():
            path.unlink()
            logger.info(f"Template deleted: {name}")
            return True
        return False

    def list_templates(self) -> List[dict]:
        templates = []
        for f in sorted(self.template_dir.glob("*.json")):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                meta = data.get("_meta", {})
                templates.append({
                    "name": meta.get("name", f.stem),
                    "file": f.name,
                    "created": meta.get("created", ""),
                    "version": meta.get("version", ""),
                    "size_kb": round(f.stat().st_size / 1024, 1),
                })
            except Exception:
                templates.append({"name": f.stem, "file": f.name, "error": True})
        return templates

    def export(self, name: str, output_path: Path) -> Path:
        config = self.load(name)
        output_path.write_text(json.dumps(config, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
        return output_path

    def import_template(self, json_path: Path) -> str:
        data = json.loads(Path(json_path).read_text(encoding="utf-8"))
        name = data.get("_meta", {}).get("name", Path(json_path).stem)
        self.save(name, data)
        return name
