"""Read-only registry for optional local development providers.

The registry never imports, installs, downloads, launches, or executes a
provider.  It only inspects Python distribution metadata, executable paths,
and an already-present ``node_modules`` tree.
"""

from __future__ import annotations

import importlib.metadata
import importlib.util
import json
import shutil
from pathlib import Path
from typing import Any


PROVIDER_SCHEMA = "VIA_LOCAL_PROVIDER_REGISTRY/1.0"
DEFAULT_NODE_ROOT = Path.cwd()

PROVIDER_GROUPS: tuple[dict[str, Any], ...] = (
    {
        "provider_id": "MS01", "label": "Microsoft MarkItDown", "scope": "document_intake_optional",
        "capabilities": ["document_to_markdown", "office_text_extraction", "structure_preservation"],
        "python": [("markitdown", "markitdown")],
        "official_urls": ["https://github.com/microsoft/markitdown"],
        "safety": "Local files only; plugins, LLM clients, remote URLs, and automatic downloads are disabled.",
        "notes": ["Markdown is an analysis projection, not a pixel-perfect layout reconstruction."],
    },
    {
        "provider_id": "PY01", "label": "Python CST / AST", "scope": "core_optional",
        "capabilities": ["lossless_cst", "incremental_ast", "source_positioning"],
        "python": [("libcst", "libcst"), ("tree-sitter", "tree_sitter")],
        "notes": ["Marwood was not verified as the canonical dependency; LibCST and Tree-sitter are the supported adapters."],
        "official_urls": ["https://libcst.readthedocs.io/", "https://tree-sitter.github.io/"],
    },
    {
        "provider_id": "PY02", "label": "Ruff", "scope": "development_optional",
        "capabilities": ["lint", "format", "static_diagnostics"], "executables": ["ruff"],
        "official_urls": ["https://docs.astral.sh/ruff/"],
    },
    {
        "provider_id": "PY03", "label": "IceCream / Loguru", "scope": "development_optional",
        "capabilities": ["debug_trace", "structured_logging"],
        "python": [("icecream", "icecream"), ("loguru", "loguru")],
        "official_urls": ["https://github.com/gruns/icecream", "https://github.com/Delgan/loguru"],
    },
    {
        "provider_id": "PY04", "label": "Polars", "scope": "performance_optional",
        "capabilities": ["columnar_data", "lazy_evaluation", "streaming"],
        "python": [("polars", "polars")], "official_urls": ["https://docs.pola.rs/"],
    },
    {
        "provider_id": "PY05", "label": "uv", "scope": "environment_optional",
        "capabilities": ["environment_resolution", "dependency_management"], "executables": ["uv"],
        "official_urls": ["https://docs.astral.sh/uv/"],
    },
    {
        "provider_id": "PY06", "label": "Pydantic / Typeguard", "scope": "contract_optional",
        "capabilities": ["schema_validation", "runtime_type_checks"],
        "python": [("pydantic", "pydantic"), ("typeguard", "typeguard")],
        "official_urls": ["https://docs.pydantic.dev/", "https://typeguard.readthedocs.io/"],
    },
    {
        "provider_id": "PY07", "label": "Playwright for Python", "scope": "browser_optional",
        "capabilities": ["browser_testing", "authorized_dynamic_page_rendering"],
        "python": [("playwright", "playwright")], "official_urls": ["https://playwright.dev/python/"],
        "safety": "No CAPTCHA, verification, authentication, or site-control bypass.",
    },
    {
        "provider_id": "PY08", "label": "Selectolax", "scope": "parser_optional",
        "capabilities": ["html_parse", "css_selection"],
        "python": [("selectolax", "selectolax")], "official_urls": ["https://github.com/rushter/selectolax"],
    },
    {
        "provider_id": "PY09", "label": "Plotly / Dash", "scope": "reporting_optional",
        "capabilities": ["interactive_chart", "local_dashboard"],
        "python": [("plotly", "plotly"), ("dash", "dash")],
        "official_urls": ["https://plotly.com/python/", "https://dash.plotly.com/"],
    },
    {
        "provider_id": "PY10", "label": "rembg / Pillow", "scope": "non_nlp_optional",
        "capabilities": ["image_background_removal", "image_processing"],
        "python": [("rembg", "rembg"), ("Pillow", "PIL")],
        "official_urls": ["https://github.com/danielgatis/rembg", "https://pillow.readthedocs.io/"],
    },
    {
        "provider_id": "JS01", "label": "Tree-sitter JS bindings", "scope": "core_optional",
        "capabilities": ["incremental_ast", "source_positioning"], "node": ["tree-sitter"],
        "official_urls": ["https://tree-sitter.github.io/"],
    },
    {
        "provider_id": "JS02", "label": "Oxlint / Oxc", "scope": "development_optional",
        "capabilities": ["lint", "static_diagnostics"], "node": ["oxlint"], "executables": ["oxlint"],
        "official_urls": ["https://oxc.rs/docs/guide/usage/linter"],
    },
    {
        "provider_id": "JS03", "label": "Zod", "scope": "contract_optional",
        "capabilities": ["schema_validation", "typescript_contract"], "node": ["zod"],
        "official_urls": ["https://zod.dev/"],
    },
    {
        "provider_id": "JS04", "label": "Bun Shell / zx", "scope": "environment_optional",
        "capabilities": ["script_orchestration", "shell_wrapper"], "node": ["zx"], "executables": ["bun"],
        "official_urls": ["https://bun.com/", "https://github.com/google/zx"],
        "safety": "Detected only; shell commands are never executed by this registry.",
    },
    {
        "provider_id": "JS05", "label": "esbuild", "scope": "development_optional",
        "capabilities": ["bundle", "transform"], "node": ["esbuild"], "executables": ["esbuild"],
        "official_urls": ["https://esbuild.github.io/"],
    },
    {
        "provider_id": "JS06", "label": "Archiver / fs-extra", "scope": "io_optional",
        "capabilities": ["archive_stream", "filesystem_helpers"], "node": ["archiver", "fs-extra"],
        "official_urls": ["https://www.archiverjs.com/", "https://github.com/jprichardson/node-fs-extra"],
    },
    {
        "provider_id": "JS07", "label": "Puppeteer", "scope": "browser_optional",
        "capabilities": ["browser_testing", "authorized_dynamic_page_rendering"], "node": ["puppeteer"],
        "official_urls": ["https://pptr.dev/"],
        "safety": "No CAPTCHA, verification, authentication, or site-control bypass.",
    },
    {
        "provider_id": "JS08", "label": "Cheerio", "scope": "parser_optional",
        "capabilities": ["html_parse", "css_selection"], "node": ["cheerio"],
        "official_urls": ["https://cheerio.js.org/"],
    },
    {
        "provider_id": "JS09", "label": "Ink / neo-blessed", "scope": "reporting_optional",
        "capabilities": ["terminal_ui", "progress_matrix"], "node": ["ink", "neo-blessed"],
        "official_urls": ["https://github.com/vadimdemedes/ink", "https://github.com/embarklabs/neo-blessed"],
        "notes": ["The original blessed package is legacy; neo-blessed is the maintained-compatible candidate."],
    },
    {
        "provider_id": "JS10", "label": "D3 / Chart.js", "scope": "reporting_optional",
        "capabilities": ["data_visualization", "web_chart"], "node": ["d3", "chart.js"],
        "official_urls": ["https://d3js.org/", "https://www.chartjs.org/docs/latest/"],
    },
)


class LocalProviderRegistry:
    """Report optional provider availability without loading provider code."""

    def __init__(self, node_root: str | Path | None = None) -> None:
        self.node_root = Path(node_root or DEFAULT_NODE_ROOT).expanduser().resolve()

    def status(self) -> dict[str, Any]:
        groups = [self._inspect_group(item) for item in PROVIDER_GROUPS]
        return {
            "schema": PROVIDER_SCHEMA,
            "provider_group_count": len(groups),
            "groups": groups,
            "statistics": {
                "available": sum(item["status"] == "available" for item in groups),
                "partial": sum(item["status"] == "partial" for item in groups),
                "unavailable": sum(item["status"] == "unavailable" for item in groups),
                "unverified": sum(item["status"] == "unverified" for item in groups),
            },
            "policy": {
                "core_runtime_dependencies": "none",
                "auto_install": False,
                "auto_import": False,
                "auto_execute": False,
                "network_access": False,
                "browser_launch": False,
                "browser_verification_bypass": False,
                "captcha_bypass": False,
                "canonical_source_write": False,
                "missing_provider_behavior": "deterministic_core_fallback",
            },
        }

    def _inspect_group(self, definition: dict[str, Any]) -> dict[str, Any]:
        candidates: list[dict[str, Any]] = []
        for distribution, module in definition.get("python", []):
            candidates.append(self._python_candidate(str(distribution), str(module)))
        for package in definition.get("node", []):
            candidates.append(self._node_candidate(str(package)))
        for executable in definition.get("executables", []):
            candidates.append(self._executable_candidate(str(executable)))
        installed = sum(bool(item["available"]) for item in candidates)
        if not candidates:
            status = "unverified"
        elif installed == len(candidates):
            status = "available"
        elif installed:
            status = "partial"
        else:
            status = "unavailable"
        return {
            "provider_id": definition["provider_id"],
            "label": definition["label"],
            "scope": definition["scope"],
            "capabilities": definition["capabilities"],
            "status": status,
            "candidates": candidates,
            "official_urls": definition.get("official_urls", []),
            "notes": definition.get("notes", []),
            "safety": definition.get("safety", "Read-only detection; explicit activation is required."),
        }

    @staticmethod
    def _python_candidate(distribution: str, module: str) -> dict[str, Any]:
        try:
            found = importlib.util.find_spec(module) is not None
        except (ImportError, ModuleNotFoundError, ValueError):
            found = False
        version = None
        if found:
            try:
                version = importlib.metadata.version(distribution)
            except importlib.metadata.PackageNotFoundError:
                version = None
        return {"ecosystem": "python", "name": distribution, "module": module, "available": found, "version": version}

    def _node_candidate(self, package: str) -> dict[str, Any]:
        manifest = self.node_root / "node_modules" / Path(*package.split("/")) / "package.json"
        version = None
        if manifest.is_file():
            try:
                payload = json.loads(manifest.read_text(encoding="utf-8"))
                version = str(payload.get("version")) if payload.get("version") else None
            except (OSError, json.JSONDecodeError):
                version = None
        return {
            "ecosystem": "node", "name": package, "available": manifest.is_file(),
            "version": version, "manifest": str(manifest),
        }

    @staticmethod
    def _executable_candidate(name: str) -> dict[str, Any]:
        path = shutil.which(name)
        return {"ecosystem": "executable", "name": name, "available": path is not None, "path": path, "version": None}
