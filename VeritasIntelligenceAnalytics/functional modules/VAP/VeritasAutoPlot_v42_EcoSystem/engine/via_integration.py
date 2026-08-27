"""
VeritasAutoPlot™ VIA Ecosystem Integration Module
=====================================================
# ANCHOR[VIA:ANCHOR:VIZ-001] — VIA Integration Entry
# ANCHOR[VIA:ANCHOR:VIZ-002] — AST SmartAsset Bridge
# ANCHOR[VIA:ANCHOR:VIZ-003] — SSOT Compatibility Layer
# ANCHOR[VIA:ANCHOR:VIZ-004] — VPN Pipeline Connector
# ANCHOR[VIA:ANCHOR:VIZ-005] — Export & Registry

Asset: VIA-SA-VIZ-001-AUTOPLOT  Lang: PY  CLS: VIZ
Version: 4.0.0  Risk: LOW (visualization output only)

Bridges VeritasAutoPlot with the full VIA ecosystem:
- VIA AST SmartAsset Architecture (ANC-A~K, DOMAIN-KIND-SEQ)
- SSOT Engine (Single Source of Truth)
- VPN Pipeline (M01~M07 PanoramicIntelligence)
- VIA UltimateTemplate v3 anchor system
- VDF CentralHub LEGO v6 (7 CAT)
"""

import os
import json
import hashlib
import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# ▸▸▸ INSERT:ANC-B:VIZ-DOMAIN ◄◄◄
# Register VIZ as a new AST domain for VeritasAutoPlot
D_VIZ = "VIZ"


# ============================================================
# ANCHOR[VIA:ANCHOR:VIZ-001] — VIA ASSET ID SYSTEM
# ============================================================

class VIAAssetBridge:
    """
    VIZ-C001 | Bridge between VeritasAutoPlot and VIA AST SmartAsset system.

    Generates VIA-compatible asset IDs:
    - VIA-SA-VIZ-{SEQ:03d}-{TYPE}  (Smart Asset format)
    - VIZ-C{SEQ:03d} / VIZ-F{SEQ:03d}  (AST registry format)
    - AST-{SHA1_10}  (VDF/VRN SHA1 format)
    """

    _seq: Dict[str, int] = {}
    _registry: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def register_asset(cls,
                       kind: str = "F",
                       name: str = "",
                       anchor: str = "",
                       tags: Optional[List[str]] = None,
                       meta: Optional[Dict] = None) -> str:
        """
        Register a VIZ asset in VIA AST format.
        Returns ast_id like VIZ-F001.
        """
        dk = f"VIZ-{kind.upper()}"
        if dk not in cls._seq:
            cls._seq[dk] = 0
        cls._seq[dk] += 1
        seq = cls._seq[dk]

        ast_id = f"VIZ-{kind.upper()}{seq:03d}"

        cls._registry[ast_id] = {
            "domain": "VIZ",
            "kind": kind.upper(),
            "name": name,
            "anchor": anchor,
            "tags": tags or [],
            "meta": meta or {},
            "timestamp": datetime.datetime.now().isoformat(),
            "healthy": True,
        }

        return ast_id

    @classmethod
    def generate_smart_asset_id(cls, asset_type: str, seq: int) -> str:
        """Generate VIA Smart Asset ID: VIA-SA-VIZ-{SEQ:03d}-{TYPE}"""
        return f"VIA-SA-VIZ-{seq:03d}-{asset_type.upper()}"

    @classmethod
    def generate_sha1_id(cls, content: str) -> str:
        """Generate VDF/VRN compatible SHA1 asset ID: AST-{SHA1_10}"""
        sha1 = hashlib.sha1(content.encode('utf-8')).hexdigest()[:10].upper()
        return f"AST-{sha1}"

    @classmethod
    def get_registry(cls) -> Dict[str, Dict[str, Any]]:
        return dict(cls._registry)

    @classmethod
    def get_seq_state(cls) -> Dict[str, int]:
        return dict(cls._seq)

    @classmethod
    def export_registry(cls, output_path: str) -> str:
        """Export VIZ AST registry in VIA-compatible format."""
        report = {
            "module": "VeritasAutoPlot",
            "version": "4.0.0",
            "domain": "VIZ",
            "timestamp": datetime.datetime.now().isoformat(),
            "total_assets": len(cls._registry),
            "seq_state": cls._seq,
            "assets": cls._registry,
        }
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        return output_path


# ============================================================
# ANCHOR[VIA:ANCHOR:VIZ-002] — SSOT COMPATIBILITY LAYER
# ============================================================

class SSOTBridge:
    """
    VIZ-C002 | SSOT (Single Source of Truth) compatibility layer.
    Allows AutoPlot to read from and write to the SSOT JSON structure.
    """

    SSOT_SCHEMA_KEYS = [
        "meta", "status", "files", "ast", "assets", "bricks",
        "dependencies", "issues", "violations", "intelligence",
        "decisions", "actions", "failures", "execution_log", "registry"
    ]

    @staticmethod
    def read_ssot(ssot_path: str) -> Optional[Dict]:
        """Read SSOT.json and return parsed structure."""
        if not os.path.exists(ssot_path):
            return None
        try:
            with open(ssot_path, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)
            return data
        except Exception as e:
            print(f"[SSOT] Read error: {e}")
            return None

    @staticmethod
    def extract_assets_for_viz(ssot: Dict) -> List[Dict]:
        """Extract visualization-relevant assets from SSOT."""
        assets = ssot.get('assets', [])
        files = ssot.get('files', [])
        issues = ssot.get('issues', [])

        viz_data = {
            "assets": assets,
            "files": files,
            "issues": issues,
            "intelligence": ssot.get('intelligence', []),
            "meta": ssot.get('meta', {}),
        }
        return viz_data

    @staticmethod
    def write_viz_results_to_ssot(ssot: Dict,
                                   viz_assets: List[Dict],
                                   insights: List[str]) -> Dict:
        """Append AutoPlot results to SSOT structure."""
        # Add VIZ assets to the assets list
        for asset in viz_assets:
            ssot_asset = {
                "id": asset.get('asset_id', ''),
                "type": "VIZ_PLOT",
                "source": "VeritasAutoPlot",
                "visualization_type": asset.get('visualization_type', ''),
                "timestamp": asset.get('generation_timestamp', ''),
                "healthy": True,
            }
            ssot.setdefault('assets', []).append(ssot_asset)

        # Add insights to intelligence
        for insight in insights:
            ssot.setdefault('intelligence', []).append({
                "source": "VeritasAutoPlot",
                "type": "VIZ_INSIGHT",
                "content": insight,
                "timestamp": datetime.datetime.now().isoformat(),
            })

        # Update execution log
        ssot.setdefault('execution_log', []).append({
            "module": "VeritasAutoPlot",
            "action": "viz_generation",
            "timestamp": datetime.datetime.now().isoformat(),
            "assets_generated": len(viz_assets),
            "insights_generated": len(insights),
        })

        return ssot


# ============================================================
# ANCHOR[VIA:ANCHOR:VIZ-003] — VPN PIPELINE CONNECTOR
# ============================================================

class VPNConnector:
    """
    VIZ-C003 | Connector for VPN Pipeline (M01~M07) JSON outputs.
    Reads VPN scan/AST/asset JSONs and converts to AutoPlot-compatible format.
    """

    VPN_JSON_FILES = {
        "scan": "vpn_scan_files.json",
        "ast": "vpn_ast_features.json",
        "assets": "vpn_smart_assets.json",
        "bricks": "vpn_brick_registry.json",
        "dep": "vpn_dep_graph.json",
        "issues": "vpn_aio_issues.json",
        "intelligence": "vpn_aio_intelligence.json",
        "matrix": "vpn_matrix.json",
        "std_violations": "vpn_aio_std_violations.json",
        "dedup_matrix": "vpn_aio_dedup_matrix.json",
    }

    @classmethod
    def load_vpn_data(cls, vpn_root: str) -> Dict[str, Any]:
        """Load all available VPN JSON outputs."""
        data = {}
        for key, filename in cls.VPN_JSON_FILES.items():
            filepath = os.path.join(vpn_root, filename)
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8-sig') as f:
                        data[key] = json.load(f)
                except Exception:
                    data[key] = None
        return data

    @classmethod
    def build_vpn_kpi_cards(cls, vpn_data: Dict) -> List[Dict]:
        """Build KPI cards from VPN scan data."""
        cards = []

        scan = vpn_data.get('scan')
        if scan and isinstance(scan, list):
            cards.append({"label": "SCANNED FILES", "value": str(len(scan)), "accent": "--bl"})

            py_files = [f for f in scan if f.get('ext', '').lower() in ['.py', 'py']]
            ps_files = [f for f in scan if f.get('ext', '').lower() in ['.ps1', 'ps1']]
            html_files = [f for f in scan if f.get('ext', '').lower() in ['.html', 'html']]

            cards.append({"label": "PYTHON FILES", "value": str(len(py_files)), "accent": "--gn"})
            cards.append({"label": "POWERSHELL", "value": str(len(ps_files)), "accent": "--vi"})
            cards.append({"label": "HTML FILES", "value": str(len(html_files)), "accent": "--tl"})

        assets = vpn_data.get('assets')
        if assets and isinstance(assets, list):
            cards.append({"label": "SMART ASSETS", "value": str(len(assets)), "accent": "--am"})

        issues = vpn_data.get('issues')
        if issues and isinstance(issues, list):
            high = len([i for i in issues if i.get('severity', '').lower() in ['high', 'critical']])
            cards.append({
                "label": "ISSUES (HIGH)",
                "value": str(high),
                "accent": "--co" if high > 0 else "--gn",
            })

        return cards

    @classmethod
    def build_vpn_tables(cls, vpn_data: Dict) -> List[Dict]:
        """Build tables from VPN data for dashboard display."""
        tables = []

        # Assets table
        assets = vpn_data.get('assets')
        if assets and isinstance(assets, list):
            rows = []
            for a in assets[:50]:  # Limit to 50
                rows.append([
                    a.get('id', a.get('smart_id', '')),
                    a.get('file', a.get('filename', '')),
                    a.get('type', a.get('category', '')),
                    a.get('lang', ''),
                    str(a.get('lines', '')),
                ])
            if rows:
                tables.append({
                    "id": "vpn_assets",
                    "title": "VPN Smart Assets",
                    "headers": ["ID", "File", "Type", "Lang", "Lines"],
                    "rows": rows,
                })

        # Issues table
        issues = vpn_data.get('issues')
        if issues and isinstance(issues, list):
            rows = []
            for i in issues[:30]:
                rows.append([
                    i.get('id', ''),
                    i.get('file', ''),
                    i.get('severity', ''),
                    i.get('type', i.get('category', '')),
                    i.get('message', i.get('description', ''))[:80],
                ])
            if rows:
                tables.append({
                    "id": "vpn_issues",
                    "title": "VPN Issues",
                    "headers": ["ID", "File", "Severity", "Type", "Message"],
                    "rows": rows,
                })

        return tables


# ============================================================
# ANCHOR[VIA:ANCHOR:VIZ-004] — UNIFIED PIPELINE ENTRY
# ============================================================

class VeritasAutoPlotVIA:
    """
    VIZ-C004 | VIA-integrated AutoPlot pipeline.
    Extends the base AutoPlot with full VIA ecosystem support.

    Usage:
        via_engine = VeritasAutoPlotVIA()

        # From VPN data
        html = via_engine.run_from_vpn("/path/to/VPN/root")

        # From SSOT
        html = via_engine.run_from_ssot("/path/to/SSOT.json")

        # Standard file (delegates to base AutoPlot)
        html = via_engine.run("data.csv")
    """

    def __init__(self, output_dir: str = None):
        from .autoplot import VeritasAutoPlot
        from .html_renderer import VeritasHTMLRenderer

        self.base_engine = VeritasAutoPlot(output_dir=output_dir)
        self.renderer = VeritasHTMLRenderer
        self.asset_bridge = VIAAssetBridge
        self.ssot_bridge = SSOTBridge
        self.vpn_connector = VPNConnector
        self.output_dir = output_dir or os.path.join(os.path.dirname(__file__), '..', 'output')
        os.makedirs(self.output_dir, exist_ok=True)

    def run(self, filepath: str, asset_name: str = None) -> str:
        """Standard file pipeline (delegates to base AutoPlot)."""
        html = self.base_engine.run(filepath, asset_name=asset_name)

        # Register assets in VIA format
        for asset in self.base_engine._asset_registry:
            self.asset_bridge.register_asset(
                kind="F",
                name=asset.get('visualization_type', ''),
                anchor="VIA:ANCHOR:VIZ-004",
                tags=["autoplot", "chart", asset.get('visualization_type', '')],
                meta=asset,
            )

        return html

    def run_from_vpn(self, vpn_root: str, title: str = "VPN System Analysis") -> str:
        """
        # ANCHOR:VAP_VIA_VPN_ENTRY
        Generate dashboard from VPN Pipeline JSON outputs.
        """
        vpn_data = self.vpn_connector.load_vpn_data(vpn_root)

        kpi_cards = self.vpn_connector.build_vpn_kpi_cards(vpn_data)
        tables = self.vpn_connector.build_vpn_tables(vpn_data)

        # Register VPN visualization assets
        self.asset_bridge.register_asset(
            kind="F", name="vpn_dashboard",
            anchor="VIA:ANCHOR:VIZ-004",
            tags=["vpn", "dashboard", "system"],
        )

        html = self.renderer.render_dashboard(
            title=title,
            subtitle="VPN Pipeline Visualization",
            kpi_cards=kpi_cards,
            charts=[],
            tables=tables,
        )

        return html

    def run_from_ssot(self, ssot_path: str, title: str = "SSOT Analysis") -> str:
        """
        # ANCHOR:VAP_VIA_SSOT_ENTRY
        Generate dashboard from SSOT.json.
        """
        ssot = self.ssot_bridge.read_ssot(ssot_path)
        if ssot is None:
            raise FileNotFoundError(f"SSOT not found: {ssot_path}")

        viz_data = self.ssot_bridge.extract_assets_for_viz(ssot)

        # Build KPIs from SSOT meta
        meta = viz_data.get('meta', {})
        kpi_cards = [
            {"label": "SYSTEM", "value": meta.get('system', 'VIA'), "accent": "--bl"},
            {"label": "VERSION", "value": meta.get('version', ''), "accent": "--tl"},
            {"label": "ASSETS", "value": str(len(viz_data.get('assets', []))), "accent": "--gn"},
            {"label": "FILES", "value": str(len(viz_data.get('files', []))), "accent": "--vi"},
            {"label": "ISSUES", "value": str(len(viz_data.get('issues', []))), "accent": "--co"},
        ]

        # Build tables
        tables = []
        assets = viz_data.get('assets', [])
        if assets:
            rows = [[
                a.get('id', ''),
                a.get('type', ''),
                a.get('source', ''),
                str(a.get('healthy', '')),
            ] for a in assets[:50]]
            tables.append({
                "id": "ssot_assets",
                "title": "SSOT Assets",
                "headers": ["ID", "Type", "Source", "Healthy"],
                "rows": rows,
            })

        html = self.renderer.render_dashboard(
            title=title,
            subtitle="SSOT Visualization",
            kpi_cards=kpi_cards,
            charts=[],
            tables=tables,
        )

        return html

    def save(self, filepath: str = None) -> str:
        """Save generated HTML."""
        return self.base_engine.save(filepath)

    def export_via_registry(self, output_path: str = None) -> str:
        """Export VIA-compatible AST registry."""
        if output_path is None:
            output_path = os.path.join(self.output_dir, 'VAP_VIA_AST_Registry.json')
        return self.asset_bridge.export_registry(output_path)

    def get_structured_output(self) -> dict:
        """Return VIA-compatible structured output."""
        base_output = self.base_engine.get_structured_output()
        base_output['via_registry'] = self.asset_bridge.get_registry()
        base_output['via_seq_state'] = self.asset_bridge.get_seq_state()
        return base_output
