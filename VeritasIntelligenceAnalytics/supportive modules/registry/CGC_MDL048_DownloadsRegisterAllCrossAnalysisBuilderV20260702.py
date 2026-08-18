# -*- coding: utf-8 -*-
"""
VIA Downloads Register All + Cross Analysis Builder
Version: 20260702
Policy: read-only scan, no execution, no source mutation, append-only output.
"""
from __future__ import annotations
from pathlib import Path
import argparse, csv, hashlib, html, json, os, re, sys, time, zipfile
from typing import Dict, List, Any

PATHS = [
  "C:\\Users\\tonyk\\Downloads\\PMIS-Lite (4)",
  "C:\\Users\\tonyk\\Downloads\\VIA_UI_FILE_READER_GAP_AUDITOR_v20260702",
  "C:\\Users\\tonyk\\Downloads\\VIA_UI_MASTER_PARAMETER_LIBRARY_v20260702",
  "C:\\Users\\tonyk\\Downloads\\1743478702766.jpg",
  "C:\\Users\\tonyk\\Downloads\\AUTO_SSOT_Sales_Battlecard.md",
  "C:\\Users\\tonyk\\Downloads\\BOM_Template_Blank (1).csv",
  "C:\\Users\\tonyk\\Downloads\\BOM_Template_Blank.csv",
  "C:\\Users\\tonyk\\Downloads\\BOM_Template_Sample (1).csv",
  "C:\\Users\\tonyk\\Downloads\\BOM_Template_Sample.csv",
  "C:\\Users\\tonyk\\Downloads\\SUP_MDL048_FetchMailbox.py",
  "C:\\Users\\tonyk\\Downloads\\image_thumb51.png",
  "C:\\Users\\tonyk\\Downloads\\launcher_minimal (1).html",
  "C:\\Users\\tonyk\\Downloads\\launcher_minimal.html",
  "C:\\Users\\tonyk\\Downloads\\PMIS-Lite (4).zip",
  "C:\\Users\\tonyk\\Downloads\\PMIS-Lite_PRO_2026.md",
  "C:\\Users\\tonyk\\Downloads\\PMIS-Lite_UX_FEEDBACK_2026.md",
  "C:\\Users\\tonyk\\Downloads\\SAP-MRO-Master-Data-Management.png",
  "C:\\Users\\tonyk\\Downloads\\SuperBOM_Financial_Model.html",
  "C:\\Users\\tonyk\\Downloads\\SuperBOM_Template_Sample.csv",
  "C:\\Users\\tonyk\\Downloads\\VIA_Capability_Matrix (1).html",
  "C:\\Users\\tonyk\\Downloads\\VIA_Capability_Matrix (2).html",
  "C:\\Users\\tonyk\\Downloads\\VIA_Capability_Matrix (3).html",
  "C:\\Users\\tonyk\\Downloads\\VIA_Capability_Matrix.html",
  "C:\\Users\\tonyk\\Downloads\\VIA_Central_Management.html",
  "C:\\Users\\tonyk\\Downloads\\VIA_CostStructure_Peer_Verify.html",
  "C:\\Users\\tonyk\\Downloads\\VIA_Doomsday_Intake.html",
  "C:\\Users\\tonyk\\Downloads\\VIA_Electric_SuperBOM.html",
  "C:\\Users\\tonyk\\Downloads\\VIA_Financial_Statements (1).html",
  "C:\\Users\\tonyk\\Downloads\\VIA_Hierarchy_Index_Valuation.html",
  "C:\\Users\\tonyk\\Downloads\\VIA_Industry_CapexProcessEquipment (1).html",
  "C:\\Users\\tonyk\\Downloads\\VIA_Industry_CapexProcessEquipment.html",
  "C:\\Users\\tonyk\\Downloads\\VIA_Integrated_Platform (1).html",
  "C:\\Users\\tonyk\\Downloads\\VIA_Integrated_Platform (2).html",
  "C:\\Users\\tonyk\\Downloads\\VIA_INTEGRATED_UI_SYSTEM_v20260702.zip",
  "C:\\Users\\tonyk\\Downloads\\VIA_Master_Codex (1).md",
  "C:\\Users\\tonyk\\Downloads\\VIA_Master_Codex (2).md",
  "C:\\Users\\tonyk\\Downloads\\VIA_Master_Codex (3).md",
  "C:\\Users\\tonyk\\Downloads\\VIA_Master_Codex.md",
  "C:\\Users\\tonyk\\Downloads\\VIA_MSProject_SSOT_Sync (1).html",
  "C:\\Users\\tonyk\\Downloads\\VIA_MSProject_SSOT_Sync (2).html",
  "C:\\Users\\tonyk\\Downloads\\VIA_MSProject_SSOT_Sync (3).html",
  "C:\\Users\\tonyk\\Downloads\\VIA_MSProject_SSOT_Sync.html",
  "C:\\Users\\tonyk\\Downloads\\VIA_PMIS_ReadOnly_SuperRegistry_v0100.ps1",
  "C:\\Users\\tonyk\\Downloads\\via_pmis_registry_builder_v0100.py",
  "C:\\Users\\tonyk\\Downloads\\VIA_PowerThermal_Registry.html",
  "C:\\Users\\tonyk\\Downloads\\VIA_PowerThermal_SAP_SuperBOM.html",
  "C:\\Users\\tonyk\\Downloads\\VIA_PSU_Thermal_AllInOne (1).html",
  "C:\\Users\\tonyk\\Downloads\\VIA_PSU_Thermal_AllInOne.html",
  "C:\\Users\\tonyk\\Downloads\\VIA_PSU_Thermal_SSOT.html",
  "C:\\Users\\tonyk\\Downloads\\VIA_SAP_FixedCode_CostObject_Registry_20260702.json",
  "C:\\Users\\tonyk\\Downloads\\VIA_Super_BOM_Dashboard_Delta_AcBel_LiteOn_v20260701.html",
  "C:\\Users\\tonyk\\Downloads\\VIA_Super_BOM_OnePage_SAP_ManagementAccounting_Delta_LiteOn_AcBel_v20260701.html",
  "C:\\Users\\tonyk\\Downloads\\VIA_Super_Engine.html",
  "C:\\Users\\tonyk\\Downloads\\VIA_SuperBOM_Relational_Intelligence_Console_20260702.html",
  "C:\\Users\\tonyk\\Downloads\\VIA_SuperBOM_Relational_SSOT_20260702 (1).json",
  "C:\\Users\\tonyk\\Downloads\\VIA_SuperBOM_Relational_SSOT_20260702.json",
  "C:\\Users\\tonyk\\Downloads\\VIA_Synonym_SSOT_PLM_PMBOK (1).html",
  "C:\\Users\\tonyk\\Downloads\\VIA_Synonym_SSOT_PLM_PMBOK.html",
  "C:\\Users\\tonyk\\Downloads\\VIA_UI_COMPLETE_CHECKLIST_AND_GAP_MATRIX_v20260702 (1).xlsx",
  "C:\\Users\\tonyk\\Downloads\\VIA_UI_COMPLETE_CHECKLIST_AND_GAP_MATRIX_v20260702.xlsx",
  "C:\\Users\\tonyk\\Downloads\\VIA_UI_FILE_READER_GAP_AUDITOR_v20260702 (1).zip",
  "C:\\Users\\tonyk\\Downloads\\VIA_UI_FILE_READER_GAP_AUDITOR_v20260702.zip",
  "C:\\Users\\tonyk\\Downloads\\VIA_UI_MASTER_PARAMETER_LIBRARY_v20260702.zip",
  "C:\\Users\\tonyk\\Downloads\\VIA_Unified_Code_Registry.html",
  "C:\\Users\\tonyk\\Downloads\\VIS_Launch_All.ps1",
  "C:\\Users\\tonyk\\Downloads\\VISWorkbench_AUTO_CODING_SSOT.md",
  "C:\\Users\\tonyk\\Downloads\\VISWorkbench_BOM_TEMPLATE_PLAN (1).md",
  "C:\\Users\\tonyk\\Downloads\\VISWorkbench_BOM_TEMPLATE_PLAN.md",
  "C:\\Users\\tonyk\\Downloads\\VISWorkbench_ENTERPRISE_SSOT.md",
  "C:\\Users\\tonyk\\Downloads\\VISWorkbench_OAUTH_2026.md",
  "C:\\Users\\tonyk\\Downloads\\VISWorkbench_PSU_INDUSTRY_SSOT (1).md",
  "C:\\Users\\tonyk\\Downloads\\VISWorkbench_PSU_INDUSTRY_SSOT.md",
  "C:\\Users\\tonyk\\Downloads\\VISWorkbench_SAP_PLM_REFERENCE.md",
  "C:\\Users\\tonyk\\Downloads\\VISWorkbench_SUPER_BOM_PLAN (1).md",
  "C:\\Users\\tonyk\\Downloads\\VISWorkbench_SUPER_BOM_PLAN.md",
  "C:\\Users\\tonyk\\Downloads\\VISWorkbench_VIA_IMPORT_PROMPT.md",
  "C:\\Users\\tonyk\\Downloads\\1520187732429.jpg",
  "C:\\Users\\tonyk\\Downloads\\Benefits-of-Process-Mining (1).png",
  "C:\\Users\\tonyk\\Downloads\\Benefits-of-Process-Mining.png",
  "C:\\Users\\tonyk\\Downloads\\How-Does-Process-Mining-Work.png",
  "C:\\Users\\tonyk\\Downloads\\indices_flow (1).html",
  "C:\\Users\\tonyk\\Downloads\\indices_flow.html",
  "C:\\Users\\tonyk\\Downloads\\p766 (1).pdf",
  "C:\\Users\\tonyk\\Downloads\\p766.pdf",
  "C:\\Users\\tonyk\\Downloads\\PMIS-Lite (1).zip",
  "C:\\Users\\tonyk\\Downloads\\PMIS-Lite (2).zip",
  "C:\\Users\\tonyk\\Downloads\\PMIS-Lite (3).zip",
  "C:\\Users\\tonyk\\Downloads\\PMIS-Lite.zip",
  "C:\\Users\\tonyk\\Downloads\\VIA_Financial_Statements.html",
  "C:\\Users\\tonyk\\Downloads\\VIA_Industry_BOM_Professional_HTML.html",
  "C:\\Users\\tonyk\\Downloads\\VIA_Industry360_Intelligence_Suite_Professional.html",
  "C:\\Users\\tonyk\\Downloads\\VIA_Integrated_Platform.html",
  "C:\\Users\\tonyk\\Downloads\\VIS_Global_Crude_Oil_Market_v0111.html",
  "C:\\Users\\tonyk\\Downloads\\SUP_MDL166_VpnsAstSymbolEngine.py",
  "C:\\Users\\tonyk\\Downloads\\vpns_rename_map.SAMPLE.json",
  "C:\\Users\\tonyk\\Downloads\\一鍵讀信箱.bat",
  "C:\\Users\\tonyk\\Downloads\\台達電.docx",
  "C:\\Users\\tonyk\\Downloads\\_backup_nettoolkit_20260213_235824",
  "C:\\Users\\tonyk\\Downloads\\_VPN_SAFE_INTEGRATION_OUT",
  "C:\\Users\\tonyk\\Downloads\\backup_20251013_115831",
  "C:\\Users\\tonyk\\Downloads\\circle-flags-gh-pages",
  "C:\\Users\\tonyk\\Downloads\\DRUCK    Macro Terminal",
  "C:\\Users\\tonyk\\Downloads\\files (27)",
  "C:\\Users\\tonyk\\Downloads\\files (33)",
  "C:\\Users\\tonyk\\Downloads\\VDS_Integration_20260226_233923",
  "C:\\Users\\tonyk\\Downloads\\VDS_Integration_20260226_233933",
  "C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics",
  "C:\\Users\\tonyk\\Downloads\\VIA_FlowSystem (2)",
  "C:\\Users\\tonyk\\Downloads\\02-difference-between-median-target-price-and-closing-price-top-and-bottom-10 (1).webp",
  "C:\\Users\\tonyk\\Downloads\\02-difference-between-median-target-price-and-closing-price-top-and-bottom-10.webp",
  "C:\\Users\\tonyk\\Downloads\\2026_macro_investment_engine_v10 (2).pdf",
  "C:\\Users\\tonyk\\Downloads\\circle-flags-gh-pages.zip",
  "C:\\Users\\tonyk\\Downloads\\EarningsInsight_062626.pdf",
  "C:\\Users\\tonyk\\Downloads\\factor_dict_matrix.html",
  "C:\\Users\\tonyk\\Downloads\\flow_monitor.html",
  "C:\\Users\\tonyk\\Downloads\\global_map_sim.html",
  "C:\\Users\\tonyk\\Downloads\\Invoke-VIA-SupportiveFunctionalRegistry-AIO-v0105.ps1",
  "C:\\Users\\tonyk\\Downloads\\perf_trend (1).html",
  "C:\\Users\\tonyk\\Downloads\\perf_trend.html",
  "C:\\Users\\tonyk\\Downloads\\spec.html",
  "C:\\Users\\tonyk\\Downloads\\Veritas Intelligence Analytics Brief.html",
  "C:\\Users\\tonyk\\Downloads\\Veritas Intelligence Analytics Brief.pdf",
  "C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics_OnePage_System_Overview_v0200.html",
  "C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics_Workbench_Enabler_Overview_v0300 (1).html",
  "C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics_Workbench_Enabler_Overview_v0300 (2).html",
  "C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics_Workbench_Enabler_Overview_v0300 (3).html",
  "C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics_Workbench_Enabler_Overview_v0300.html",
  "C:\\Users\\tonyk\\Downloads\\VIA · 族群分類完善化 v1.1.pdf",
  "C:\\Users\\tonyk\\Downloads\\PMIS-Lite (3)"
]

TEXT_EXT = {".html",".htm",".json",".csv",".md",".txt",".py",".ps1",".bat",".cmd",".css",".js"}

def classify(path: str) -> Dict[str, str]:
    low = path.lower()
    ext = Path(path).suffix.lower()
    if re.search(r"superbom|super_bom|bom_template|bom", low): domain="SUPER_BOM"
    elif re.search(r"sap|plm|pmbok", low): domain="SAP_PLM"
    elif re.search(r"pmis|msproject|project", low): domain="PMIS_PROJECT"
    elif re.search(r"financial|valuation|coststructure|statements", low): domain="FINANCIAL_MODEL"
    elif re.search(r"ui|launcher|integrated_platform|central_management", low): domain="UI_PLATFORM"
    elif re.search(r"capability|unified_code|engine|registry|codex", low): domain="REGISTRY_ENGINE"
    elif re.search(r"process-mining|process_mining|flow|benefits-of-process", low): domain="PROCESS_MINING"
    elif re.search(r"oil|macro|earningsinsight|indices|factor", low): domain="MARKET_MACRO"
    elif re.search(r"台達電|delta|powerthermal|psu_thermal|electric", low): domain="COMPANY_INDUSTRY"
    elif ext in [".jpg",".jpeg",".png",".webp"]: domain="IMAGE_REFERENCE"
    elif ext == ".zip": domain="PACKAGE_ARCHIVE"
    elif ext in [".py",".ps1",".bat",".cmd"]: domain="CODE_SCRIPT"
    elif ext in [".md",".txt",".docx",".pdf"]: domain="DOC_SOURCE"
    else: domain="MISC"
    ftype = "folder_or_no_extension" if ext == "" else {
        ".html":"html",".htm":"html",".json":"json",".csv":"csv",".xlsx":"spreadsheet",".md":"markdown",
        ".py":"script",".ps1":"script",".bat":"script",".cmd":"script",".jpg":"image",".jpeg":"image",
        ".png":"image",".webp":"image",".pdf":"pdf",".docx":"docx",".zip":"archive"
    }.get(ext, ext.strip(".") or "unknown")
    return {"domain": domain, "file_type": ftype}

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()

def read_preview(path: Path, file_type: str, max_chars: int = 2000) -> Dict[str, Any]:
    try:
        if path.suffix.lower() in TEXT_EXT:
            for enc in ["utf-8-sig","utf-8","cp950","big5","latin-1"]:
                try:
                    txt = path.read_text(encoding=enc, errors="strict")
                    return {"ok": True, "encoding": enc, "preview": txt[:max_chars], "error": ""}
                except Exception:
                    pass
            return {"ok": True, "encoding": "utf-8-replace", "preview": path.read_text(encoding="utf-8", errors="replace")[:max_chars], "error": ""}
        if file_type == "docx":
            with zipfile.ZipFile(path) as z:
                raw = z.read("word/document.xml").decode("utf-8", errors="replace")
            txt = re.sub(r"<[^>]+>", " ", raw)
            txt = html.unescape(txt)
            txt = re.sub(r"\s+", " ", txt).strip()
            return {"ok": True, "encoding": "docx-xml", "preview": txt[:max_chars], "error": ""}
        return {"ok": False, "encoding": "", "preview": "", "error": "preview_not_supported"}
    except Exception as exc:
        return {"ok": False, "encoding": "", "preview": "", "error": str(exc)}

def write_html(rows: List[Dict[str, Any]], out: Path) -> None:
    trs = []
    for r in rows:
        trs.append("<tr>" + "".join([
            f"<td>{html.escape(str(r.get('record_id','')))} </td>",
            f"<td>{html.escape(str(r.get('status','')))} </td>",
            f"<td>{html.escape(str(r.get('domain','')))} </td>",
            f"<td>{html.escape(str(r.get('file_type','')))} </td>",
            f"<td>{html.escape(str(r.get('name','')))} </td>",
            f"<td>{html.escape(str(r.get('size_bytes','')))} </td>",
            f"<td>{html.escape(str(r.get('sha256',''))[:16])}</td>",
            f"<td>{html.escape(str(r.get('source_path','')))} </td>"
        ]) + "</tr>")
    doc = f"""<!doctype html><html><head><meta charset='utf-8'><title>VIA Register All</title>
<style>body{font-family:Segoe UI,Microsoft JhengHei,sans-serif;background:#F9F9F6;color:#1F2933;font-size:11px}.wrap{max-width:1600px;margin:0 auto;padding:20px}table{width:100%;border-collapse:collapse;background:white}th,td{border:1px solid #DFECEA;padding:6px;vertical-align:top}th{background:#F3F6F4;color:#6B7C78}</style></head>
<body><div class='wrap'><h1>VIA Downloads Register All + Cross Analysis</h1><p>Policy: read-only / no execute / no source mutation / append-only output. Rows: {len(rows)}</p>
<table><thead><tr><th>ID</th><th>Status</th><th>Domain</th><th>Type</th><th>Name</th><th>Bytes</th><th>SHA256</th><th>Path</th></tr></thead><tbody>{''.join(trs)}</tbody></table></div></body></html>"""
    out.write_text(doc, encoding="utf-8")

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(Path.home() / "Downloads" / f"VIA_Downloads_RegisterAll_CrossAnalysis_RUN_{time.strftime('%Y%m%d_%H%M%S')}"))
    args = ap.parse_args()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for idx, p in enumerate(PATHS, 1):
        path = Path(p)
        cls = classify(p)
        row = {
            "record_id": f"VIA-20260702-LOCAL-{idx:04d}",
            "source_path": p,
            "name": path.name,
            "domain": cls["domain"],
            "file_type": cls["file_type"],
            "status": "MISSING",
            "size_bytes": "",
            "sha256": "",
            "preview_ok": False,
            "preview_error": "",
            "preview_excerpt": "",
            "policy": "READ_ONLY_NO_EXECUTE_NO_MUTATION"
        }
        if path.exists():
            row["status"] = "FOUND_DIR" if path.is_dir() else "FOUND_FILE"
            try:
                if path.is_file():
                    row["size_bytes"] = path.stat().st_size
                    row["sha256"] = sha256_file(path)
                    pv = read_preview(path, cls["file_type"])
                    row["preview_ok"] = pv["ok"]
                    row["preview_error"] = pv["error"]
                    row["preview_excerpt"] = pv["preview"]
                else:
                    row["size_bytes"] = sum(1 for _ in path.iterdir())
            except Exception as exc:
                row["status"] = "FOUND_READ_WARN"
                row["preview_error"] = str(exc)
        rows.append(row)
    payload = {
        "run_id": out_dir.name,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "policy": ["read-only","no execution","no source mutation","no delete","append-only output"],
        "rows": rows
    }
    json_path = out_dir / "VIA_Downloads_RegisterAll_CrossAnalysis.registry.json"
    csv_path = out_dir / "VIA_Downloads_RegisterAll_CrossAnalysis.registry.csv"
    html_path = out_dir / "VIA_Downloads_RegisterAll_CrossAnalysis.report.html"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    write_html(rows, html_path)
    print(f"OutputRoot: {out_dir}")
    print(f"JSON: {json_path}")
    print(f"CSV : {csv_path}")
    print(f"HTML: {html_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
