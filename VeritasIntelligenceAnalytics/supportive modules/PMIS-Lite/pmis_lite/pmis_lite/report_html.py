"""產出層：HTML 結果頁（給門外漢看的）。

跑完自動開這頁，使用者完全不用碰終端機/命令列。
自包含、無外部依賴、離線可開。沿用 Visual Lock 色票。
"""
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
from datetime import datetime

import pandas as pd

_CSS = """
:root{--bg:#f5f4f0;--ink:#2a2a2a;--blue:#4c78a8;--teal:#439a9a;--grey:#9c9890;
--red:#c96b5a;--green:#5a9e6f;--line:#e3e0d8;--card:#fffefb;--seal:#b13a2e;}
*{box-sizing:border-box;}body{margin:0;background:var(--bg);color:var(--ink);
font-family:-apple-system,"Noto Sans TC","Microsoft JhengHei",sans-serif;line-height:1.6;}
header{background:var(--card);border-bottom:1px solid var(--line);padding:18px 22px;display:flex;gap:14px;align-items:center;}
.seal{width:44px;height:44px;border:2px solid var(--seal);border-radius:7px;color:var(--seal);
display:flex;align-items:center;justify-content:center;font-size:22px;font-weight:700;}
h1{font-size:17px;margin:0;}header p{margin:2px 0 0;font-size:11px;color:var(--grey);}
.wrap{max-width:920px;margin:0 auto;padding:20px 16px 60px;}
.gate{border-radius:12px;padding:16px 18px;margin:14px 0;font-weight:700;font-size:15px;color:#fff;}
.pass{background:var(--green);}.fail{background:var(--red);}
.gate small{display:block;font-weight:400;font-size:12.5px;opacity:.92;margin-top:4px;}
.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:14px 0;}
@media(max-width:640px){.cards{grid-template-columns:repeat(2,1fr);}}
.stat{background:var(--card);border:1px solid var(--line);border-radius:11px;padding:14px;text-align:center;}
.stat b{display:block;font-size:26px;color:var(--blue);}
.stat span{font-size:11.5px;color:var(--grey);}
h2{font-size:14px;margin:24px 0 8px;border-left:3px solid var(--teal);padding-left:9px;}
table{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);border-radius:10px;overflow:hidden;font-size:12.5px;}
th,td{text-align:left;padding:8px 11px;border-bottom:1px solid var(--line);}
th{background:#efece4;color:#6a665e;font-weight:600;}
tr:last-child td{border-bottom:none;}
.pill{font-size:11px;padding:2px 8px;border-radius:5px;font-weight:700;}
.s逾期{background:#f7e3df;color:var(--red);}.s已結{background:#e1f0e6;color:var(--green);}
.s進行中{background:#e7eef6;color:var(--blue);}.s待辦,.s未標示{background:#eee;color:var(--grey);}
.prod{font-size:13px;font-weight:700;margin:14px 0 4px;}
.uid{font-family:ui-monospace,monospace;font-size:11px;color:var(--grey);}
.foot{font-size:11px;color:var(--grey);margin-top:30px;text-align:center;}
"""


def _pill(status):
    s = html.escape(status or "未標示")
    return f'<span class="pill s{s}">{s}</span>'


def build_html(result: dict, out_path: str) -> str:
    df = result["df"]
    stats = result["stats"]
    audit = result["audit"]
    actions = result.get("actions", [])
    registry = result.get("registry", {})
    candidates = result.get("candidates", [])
    o = audit.overall()

    H = [f"<!DOCTYPE html><html lang='zh-Hant'><head><meta charset='utf-8'>",
         "<meta name='viewport' content='width=device-width,initial-scale=1'>",
         f"<title>本週工作進度</title><style>{_CSS}</style></head><body>"]
    H.append("<header><div class='seal'>觀</div><div><h1>本週工作進度 · SSOT 自動彙整</h1>"
             f"<p>{datetime.now():%Y-%m-%d %H:%M} · 本機處理 · 草稿（複核後對外）</p></div></header>")
    H.append("<div class='wrap'>")

    gate_cls = "pass" if o["status"] == "PASS" else "fail"
    H.append(f"<div class='gate {gate_cls}'>擷取完整性：{o['status']}　涵蓋率 {o['coverage_pct']}%"
             f"<small>來源可見 {o['seen']} · 成功擷取 {o['extracted']} · "
             f"結構性略過 {o['structural_skipped']}(不算漏) · 可救回 {o['recoverable']} · "
             f"未解釋遺漏 {o['unexplained_gap']}</small></div>")

    # 可救回項目（系統建議補強，提高涵蓋率）
    rec = audit.recoverable_items()
    if rec:
        H.append("<h2>可救回項目（讓系統再努力即可提高涵蓋率）</h2><table><tr><th>來源</th><th>項目</th><th>原因</th></tr>")
        for src, ref, reason in rec[:30]:
            H.append(f"<tr><td>{html.escape(src)}</td><td class='uid'>{html.escape(str(ref))}</td>"
                     f"<td>{html.escape(reason)}</td></tr>")
        H.append("</table>")

    H.append("<div class='cards'>")
    for b, s in [(stats['added'], '新增'), (stats['updated'], '變更'),
                 (len(actions), '追蹤事項'), (len(registry), '相關人')]:
        H.append(f"<div class='stat'><b>{b}</b><span>{s}</span></div>")
    H.append("</div>")

    if len(df):
        H.append("<h2>分產品列管</h2>")
        for prod, g in df.groupby("product"):
            H.append(f"<div class='prod'>{html.escape(prod or '未分類')}（{len(g)}）</div><table>")
            for _, r in g.iterrows():
                H.append(f"<tr><td class='uid'>{html.escape(r['uid'])}</td>"
                         f"<td>{html.escape(str(r['title']))}</td>"
                         f"<td>{_pill(r['status'])}</td>"
                         f"<td>{html.escape(str(r['actor']))}</td></tr>")
            H.append("</table>")

    if actions:
        H.append("<h2>追蹤事項（自動擷取）</h2><table><tr><th>編號</th><th>事項</th><th>負責</th><th>期限</th></tr>")
        for a in actions:
            H.append(f"<tr><td class='uid'>{html.escape(a.uid)}</td><td>{html.escape(a.text)}</td>"
                     f"<td>{html.escape(a.owner)}</td><td>{html.escape(a.due or '—')}</td></tr>")
        H.append("</table>")

    if candidates:
        H.append("<h2>術語候選（待核可，系統不自動合併）</h2><table><tr><th>候選詞</th><th>提議正規詞</th><th>信心</th><th>訊號</th></tr>")
        for c in candidates:
            H.append(f"<tr><td>{html.escape(c.surface)}</td><td>{html.escape(c.canonical)}</td>"
                     f"<td>{c.confidence}</td><td>{html.escape(', '.join(c.signals))}</td></tr>")
        H.append("</table>")

    if registry:
        H.append("<h2>相關人（僅工作事實）</h2><table><tr><th>對象</th><th>單位</th><th>寄件</th><th>收件</th><th>參與度</th></tr>")
        for s in sorted(registry.values(), key=lambda x: -x.total())[:20]:
            H.append(f"<tr><td>{html.escape(s.handle)}</td><td>{html.escape(s.unit or '—')}</td>"
                     f"<td>{s.as_sender}</td><td>{s.as_recipient}</td><td>{html.escape(s.engagement)}</td></tr>")
        H.append("</table>")

    H.append("<div class='foot'>PMIS-Lite · 本機處理 · 僅讀取你有權限的資料 · 產出為草稿</div>")
    H.append("</div></body></html>")

    text = "".join(H)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)
    return out_path
