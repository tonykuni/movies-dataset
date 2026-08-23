# -*- coding: utf-8 -*-
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

import html
import json
import sys
from datetime import datetime
from pathlib import Path


VERSION = "VRN_FLOW_B_UI_TEXT_SPEC_PACK_V061549"


def def_write_json(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def def_write_markdown(path: Path, spec: dict) -> None:
    lines = []
    lines.append("# VRN Final U/I Text Specification Pack v0.6.15.4.9")
    lines.append("")
    lines.append("def 視覺定位：機構級、乾淨、矩陣式、不可可愛、不可重疊。")
    lines.append("def 安全定位：U/I 文字規格，不修改資料、不寫 DB、不改 canonical、不改 SSOT。")
    lines.append("")
    for page in spec["pages"]:
        lines.append(f"## def {page['id']} · {page['title']}")
        lines.append(f"def purpose: {page['purpose']}")
        lines.append("def required blocks:")
        for b in page["blocks"]:
            lines.append(f"- {b}")
        lines.append("def required columns:")
        for c in page["columns"]:
            lines.append(f"- {c}")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def def_write_html(path: Path, spec: dict) -> None:
    css = """
body{margin:0;background:#07111f;color:#eef6ff;font-family:Segoe UI,'Microsoft JhengHei',Arial,sans-serif}
header{padding:28px 34px;background:#0d1b2f;border-bottom:1px solid #1f3557}
h1{margin:0;font-size:25px}.sub{color:#9fb3c8;margin-top:8px}
main{padding:24px 34px}.card{background:#0d1b2f;border:1px solid #1f3557;border-radius:18px;padding:18px;margin:18px 0}
h2{margin-top:0}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px}
.item{border:1px solid #1f3557;border-radius:14px;padding:12px;background:#0a1728}
code{color:#b8e1ff}
li{margin:6px 0}
"""
    pages = []
    for p in spec["pages"]:
        blocks = "".join(f"<li>{html.escape(x)}</li>" for x in p["blocks"])
        cols = "".join(f"<li><code>{html.escape(x)}</code></li>" for x in p["columns"])
        pages.append(f"""
<section class='card'>
<h2>def {html.escape(p['id'])} · {html.escape(p['title'])}</h2>
<p>{html.escape(p['purpose'])}</p>
<div class='grid'>
<div class='item'><h3>Blocks</h3><ul>{blocks}</ul></div>
<div class='item'><h3>Columns</h3><ul>{cols}</ul></div>
</div>
</section>
""")
    rules = "".join(f"<li>{html.escape(x)}</li>" for x in spec["rules"])
    doc = f"""<!doctype html><html><head><meta charset='utf-8'><title>VRN Final UI Spec v061549</title><style>{css}</style></head>
<body><header><h1>VRN · Final U/I Text Specification Pack v0.6.15.4.9</h1>
<div class='sub'>BasicInfo · FinancialData · Repair Queue · Table Restore Dry Run · no mutation</div></header>
<main><section class='card'><h2>def Global Rules</h2><ul>{rules}</ul></section>{''.join(pages)}</main></body></html>"""
    path.write_text(doc, encoding="utf-8")


def def_main() -> None:
    run_dir = Path(sys.argv[1])
    spec = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "mode": "UI_SPEC_ONLY_NO_DATA_MUTATION",
        "rules": [
            "所有頁面頁首固定：VERITAS INTELLIGENCE ANALYTICS · VRN Company Report Intelligence。",
            "所有矩陣第一欄固定 Status Lights，燈號格式為 INPUT / DB / TRUST 三段。",
            "百分比一律顯示 33.33% 並可換行顯示 10/30。",
            "金額與數字一律千分位，小數點後兩位數；空值不假填。",
            "YFinance 欄位不可再出現 TFinance。",
            "Target Price 來自報告，不可用 YFinance consensus 假填。",
            "FinancialData repair queue 不阻擋 BasicInfo final pack。",
            "表格修復流程要先 row/column/header/body/source-note 驗證，才可轉 DB。",
            "U/I 不可重疊，table 使用 sticky header + horizontal scroll + max-height。",
        ],
        "pages": [
            {
                "id": "P01",
                "title": "Executive Seal Dashboard",
                "purpose": "一眼確認 Final PASS、BasicInfo、FinancialData、Repair Queue、No Mutation 狀態。",
                "blocks": ["KPI cards", "Gate matrix", "Latest run links", "Next action panel"],
                "columns": ["Status Lights", "Gate", "Value", "Severity", "Evidence Path"],
            },
            {
                "id": "P02",
                "title": "BasicInfo Final Matrix",
                "purpose": "個股報告主表，僅顯示封版後可用欄位。",
                "blocks": ["Company active matrix", "GS target review queue", "Optional target missing queue"],
                "columns": ["Report date", "filename", "broker", "analyst", "ticker", "yfinance ticker", "bloomberg ticker", "name", "rating", "target price", "valuation method", "YFinance target low", "YFinance target mean", "YFinance target median", "YFinance target high", "YFinance rating", "YFinance analyst count", "YFinance beta", "validation status"],
            },
            {
                "id": "P03",
                "title": "FinancialData Matrix",
                "purpose": "顯示已抽取財務資料與 validation status，不與 BasicInfo 混淆。",
                "blocks": ["Financial account matrix", "Statement type filter", "Year window filter", "Confidence band"],
                "columns": ["filename", "ticker", "name", "year", "statement type", "account", "value", "unit", "historical validation", "add/sub validation", "division validation", "final trust", "final band"],
            },
            {
                "id": "P04",
                "title": "Repair Queue Control",
                "purpose": "只管理未完成項，不污染正式資料。",
                "blocks": ["Year quarantine", "Alias staging", "Formula context queue", "Table-section restore plan"],
                "columns": ["route", "rows", "reason", "recommended next step", "restore execution", "canonical mutation"],
            },
            {
                "id": "P05",
                "title": "Targeted Table Dry Run",
                "purpose": "檢查 PDF/table/page locator 與 table candidate，不直接 restore。",
                "blocks": ["Page locator matrix", "Table candidate matrix", "Reconstruction route summary"],
                "columns": ["filename", "ticker", "page", "strategy", "table no", "rows", "cols", "density", "header score", "source score", "quality score", "statement type", "reconstruction route", "preview"],
            },
        ],
        "outputs": {},
    }

    outputs = {
        "html": str(run_dir / "FlowB_UI_Text_Spec_Pack_v061549.html"),
        "json": str(run_dir / "flow_b_ui_text_spec_pack_v061549.json"),
        "markdown": str(run_dir / "flow_b_ui_text_spec_pack_v061549.md"),
    }
    spec["outputs"] = outputs

    def_write_json(Path(outputs["json"]), spec)
    def_write_markdown(Path(outputs["markdown"]), spec)
    def_write_html(Path(outputs["html"]), spec)

    print(json.dumps({
        "version": VERSION,
        "system_pass": True,
        "counts": {
            "Flow B": "PASS",
            "UI Pages": len(spec["pages"]),
            "Global Rules": len(spec["rules"]),
            "Data Mutation": "NO",
        },
        "outputs": outputs,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    def_main()