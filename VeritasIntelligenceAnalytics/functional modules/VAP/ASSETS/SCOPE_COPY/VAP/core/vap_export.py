#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  APM-006: vap_export.py - Export Engine                                    ║
║  Module ID: APM-006 | Version: 4.0.0                                       ║
║  PNG export (kaleido @2x) + Standalone HTML (Object.freeze, data locked)   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import json
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

from vap_config import VAPPaths, EXPORT_DEFAULTS

logger = logging.getLogger(__name__)


class VAPExportEngine:
    """Handles PNG and HTML export with data freezing."""

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or VAPPaths.OUTPUT
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_png(self, fig, filename: str = None, width: int = None,
                   height: int = None, scale: int = None) -> Path:
        """Export Plotly figure to high-res PNG via kaleido."""
        width = width or EXPORT_DEFAULTS.png_width
        height = height or EXPORT_DEFAULTS.png_height
        scale = scale or EXPORT_DEFAULTS.png_scale

        if not filename:
            filename = f"VAP_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        if not filename.endswith(".png"):
            filename += ".png"

        path = self.output_dir / filename
        fig.write_image(str(path), width=width, height=height, scale=scale,
                        engine="kaleido")
        logger.info(f"PNG exported: {path} ({width}x{height} @{scale}x)")
        return path

    def export_html(self, fig, filename: str = None, freeze_data: bool = True,
                    include_plotlyjs: str = "cdn") -> Path:
        """
        Export Plotly figure to standalone HTML.
        If freeze_data=True, injects Object.freeze on chart data.
        """
        if not filename:
            filename = f"VAP_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        if not filename.endswith(".html"):
            filename += ".html"

        path = self.output_dir / filename

        html_content = fig.to_html(
            include_plotlyjs=include_plotlyjs,
            full_html=True,
            config={"displayModeBar": True, "responsive": True},
        )

        if freeze_data:
            freeze_script = """
<script>
(function() {
    var plots = document.querySelectorAll('.plotly-graph-div');
    plots.forEach(function(plot) {
        if (plot.data) { Object.freeze(plot.data); }
        if (plot.layout) { Object.freeze(plot.layout); }
    });
    console.log('VeritasAutoPlot: Data frozen (immutable)');
})();
</script>
"""
            html_content = html_content.replace("</body>", freeze_script + "</body>")

        # Add metadata header
        meta = f"""
<!-- VeritasAutoPlot Export
     Generated: {datetime.now().isoformat()}
     Data: FROZEN (Object.freeze applied)
     System: Veritas Intelligence Analytics
-->
"""
        html_content = html_content.replace("<html>", meta + "<html>")

        path.write_text(html_content, encoding="utf-8")
        logger.info(f"HTML exported: {path} (freeze={freeze_data})")
        return path

    def export_both(self, fig, base_name: str = None, **kwargs) -> dict:
        """Export both PNG and HTML."""
        if not base_name:
            base_name = f"VAP_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        png_path = self.export_png(fig, f"{base_name}.png", **kwargs)
        html_path = self.export_html(fig, f"{base_name}.html")
        return {"png": png_path, "html": html_path}
