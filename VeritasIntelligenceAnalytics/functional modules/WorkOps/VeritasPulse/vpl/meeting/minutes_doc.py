"""VPL-MIN · professional, visual-locked Meeting Minutes (HTML + PDF).

Pipeline: confirmed/classified transcript → DuckDB aggregation (archive) →
strict speaker-aligned minutes → VIA Visual-Lock HTML → PDF (weasyprint).

PROMPT modes: 'concise' (Summary + Actions + Decisions) or
'comprehensive' (+ Discussion + Risks + full speaker-aligned transcript).
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
import datetime as _dt
import html as _h
import os
from pathlib import Path

# --- strict generation spec (reusable when wired to a real LLM) ---
PROMPT_STRICT = (
    "生成會議紀錄,規則(嚴格):\n"
    "1. 每個 Action 必須標明負責人(發話人對齊),不可遺漏。\n"
    "2. 每個 Decision 逐條列出,不可遺漏、不可改寫原意。\n"
    "3. 發言人對齊:所有引述對齊原始發話人。\n"
    "4. 模式=精簡 → 僅 Summary + Actions + Decisions;模式=全面 → 再加 Discussion + Risks + 完整逐字稿。\n"
    "5. 內容為繁體中文,保持原語言。"
)

CAT_COLOR = {"Decision": "#35506b", "Action": "#8a3b2e", "Risk": "#9a6b2f", "Discussion": "#8f897c"}
CAT_TC = {"Decision": "決議", "Action": "行動", "Risk": "風險", "Discussion": "討論"}


def _doc_css() -> str:
    # CJK-safe stack; Syne/DM Sans load on-screen, Noto CJK guarantees PDF glyphs
    return """
@page{size:A4;margin:18mm 16mm 16mm;
  @bottom-right{content:"VeritasPulse · 機密 Confidential · 第 " counter(page) " 頁";
    font-family:'DM Mono','Noto Sans CJK TC';font-size:8pt;color:#8f897c}}
*{box-sizing:border-box}
body{font-family:'DM Sans','Noto Sans CJK TC',sans-serif;color:#1a1916;font-size:10.5pt;line-height:1.6;margin:0}
.eyebrow{font-family:'DM Mono','Noto Sans CJK TC';font-size:8.5pt;letter-spacing:.22em;text-transform:uppercase;color:#5e7032}
h1{font-family:'Syne','Noto Sans CJK TC';font-weight:800;font-size:25pt;letter-spacing:-.01em;margin:6px 0 10px}
.head{border-left:5px solid #5e7032;padding-left:16px;margin-bottom:18px}
.meta{font-family:'DM Mono','Noto Sans CJK TC';font-size:9pt;color:#56524a}
.meta b{color:#1a1916;font-weight:500}
.badge{display:inline-block;font-family:'DM Mono','Noto Sans CJK TC';font-size:8pt;letter-spacing:.1em;text-transform:uppercase;
  background:#e2e6d0;color:#5e7032;padding:3px 10px;border-radius:20px;margin-left:8px}
.summary{background:#fbfaf7;border:1px solid #e2dfd6;border-left:4px solid #5e7032;border-radius:8px;padding:13px 16px;margin:14px 0 22px;font-size:11pt}
h2{font-family:'Syne','Noto Sans CJK TC';font-weight:700;font-size:14pt;margin:22px 0 9px;display:flex;align-items:center;gap:9px}
h2 .num{width:22px;height:22px;border-radius:6px;background:#5e7032;color:#fff;font-family:'DM Mono';font-size:11pt;display:inline-grid;place-items:center}
table{width:100%;border-collapse:collapse;margin-top:6px;font-size:10pt}
th{background:#f0eee8;text-align:left;font-family:'DM Mono','Noto Sans CJK TC';font-size:8pt;letter-spacing:.08em;text-transform:uppercase;color:#8f897c;padding:7px 9px;border-bottom:1px solid #cfcabd}
td{padding:8px 9px;border-bottom:1px solid #e2dfd6;vertical-align:top}
td.n{font-family:'DM Mono';color:#8f897c;width:26px}
td.owner{font-family:'DM Mono','Noto Sans CJK TC';color:#5e7032;white-space:nowrap}
ol{margin:6px 0 0;padding-left:22px}li{margin:6px 0}
.dlog li::marker{color:#35506b;font-weight:700}
.risk li::marker{color:#9a6b2f}
.seg{display:flex;gap:10px;padding:7px 0;border-bottom:1px solid #efeee9;font-size:9.5pt}
.seg .t{font-family:'DM Mono';color:#8f897c;width:42px;flex:none}
.seg .sp{font-weight:600;width:90px;flex:none}
.seg .ct{font-family:'DM Mono';font-size:7.5pt;padding:1px 6px;border-radius:10px;height:fit-content;white-space:nowrap}
.foot{margin-top:26px;padding-top:10px;border-top:1px solid #e2dfd6;font-family:'DM Mono','Noto Sans CJK TC';font-size:8pt;color:#8f897c;display:flex;justify-content:space-between}
"""


def _render_html(meeting, mins, segs, mode) -> str:
    e = _h.escape
    actions = mins["actions"]; decisions = mins["decisions"]
    discussion = mins["discussion"]; risks = mins["risks"]
    act_rows = "".join(
        f'<tr><td class="n">{i+1}</td><td>{e(a["text"])}</td><td class="owner">{e(a["owner"])}</td>'
        f'<td class="owner">+7d</td></tr>' for i, a in enumerate(actions)) or '<tr><td colspan="4">—</td></tr>'
    dec = "".join(f"<li>{e(d)}</li>" for d in decisions) or "<li>—</li>"

    extra = ""
    if mode == "comprehensive":
        dis = "".join(f"<li>{e(d)}</li>" for d in discussion) or "<li>—</li>"
        rsk = "".join(f"<li>{e(r)}</li>" for r in risks) or "<li>—</li>"
        seg_rows = "".join(
            f'<div class="seg"><span class="t">{e(s["at_time"])}</span>'
            f'<span class="sp">{e(s.get("speaker") or "—")}</span>'
            f'<span class="ct" style="background:{CAT_COLOR.get(s.get("category"),"#eee")}22;'
            f'color:{CAT_COLOR.get(s.get("category"),"#56524a")}">{CAT_TC.get(s.get("category"),"")}</span>'
            f'<span>{e(s["text"])}</span></div>' for s in segs)
        extra = (f'<h2><span class="num">4</span>Discussion 討論</h2><ol>{dis}</ol>'
                 f'<h2><span class="num">5</span>Risks 風險</h2><ol class="risk">{rsk}</ol>'
                 f'<h2><span class="num">6</span>完整逐字稿 Transcript</h2><div>{seg_rows}</div>')

    gen = _dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    mode_tc = "全面 Comprehensive" if mode == "comprehensive" else "精簡 Concise"
    return f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<title>Meeting Minutes · {e(meeting['title'])}</title>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;500;600&family=DM+Mono&display=swap" rel="stylesheet">
<style>{_doc_css()}</style></head><body>
<div class="head"><div class="eyebrow">Meeting Minutes · 會議紀錄</div>
<h1>{e(meeting['title'])}</h1>
<div class="meta"><b>日期</b> {e(meeting['day'])} &nbsp;·&nbsp; <b>出席</b> {e(meeting['attendees'])}
<span class="badge">{mode_tc}</span></div></div>
<div class="summary">{e(mins['summary'])}</div>
<h2><span class="num">1</span>Action Items 行動項目</h2>
<table><tr><th>#</th><th>行動</th><th>負責人</th><th>期限</th></tr>{act_rows}</table>
<h2><span class="num">2</span>Decision Log 決議</h2><ol class="dlog">{dec}</ol>
{extra if mode=='comprehensive' else ''}
<div class="foot"><span>VIA Visual Lock v1 · VeritasPulse</span><span>generated {gen} · 發言人對齊</span></div>
</body></html>"""


def build(db_path: str, out_dir: str, mode: str = "comprehensive", meeting_id: int = 1) -> dict:
    from ..core import archive, store
    os.makedirs(out_dir, exist_ok=True)
    mins = archive.generate_minutes(db_path, out_dir, meeting_id)
    proj = store.load_project(db_path)
    meeting = next((m for m in proj["meetings"] if m["id"] == meeting_id), proj["meetings"][0])
    segs = [s for s in proj["segments"] if s["meeting_id"] == meeting_id]
    html = _render_html(meeting, mins, segs, mode)
    html_path = os.path.join(out_dir, "VRN_Meeting_Minutes.html")
    Path(html_path).write_text(html, encoding="utf-8")
    pdf_path = os.path.join(out_dir, "VRN_Meeting_Minutes.pdf")
    try:
        from weasyprint import HTML
        HTML(string=html).write_pdf(pdf_path)
        pdf_path = _optimize_pdf(pdf_path)
    except Exception as e:  # graceful — HTML still produced
        pdf_path = f"(pdf skipped: {e})"
    return {"html": html_path, "pdf": pdf_path, "mode": mode,
            "actions": len(mins["actions"]), "decisions": len(mins["decisions"])}


def _optimize_pdf(path: str) -> str:
    """改檔最佳化:linearize + recompress object streams to shrink the PDF."""
    try:
        import pikepdf
        before = os.path.getsize(path)
        tmp = path + ".opt"
        with pikepdf.open(path) as pdf:
            pdf.save(tmp, linearize=True,
                     object_stream_mode=pikepdf.ObjectStreamMode.generate,
                     compress_streams=True)
        if os.path.getsize(tmp) <= before:
            os.replace(tmp, path)
        else:
            os.remove(tmp)
    except Exception:
        pass
    return path
