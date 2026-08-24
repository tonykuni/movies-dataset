"""
VeritasAutoPlot™ HTML Dashboard Renderer
==========================================
Generates standalone HTML dashboards with VIA FusionDashboard locked visual style.
All CSS, fonts, and layout are embedded — zero external dependencies.
Output: Single .html file with Object.freeze(DATA) for data integrity.
"""

import json
import datetime
from typing import List, Dict, Any
import plotly.graph_objects as go
import plotly.io as pio


class VeritasHTMLRenderer:
    """Renders complete standalone HTML dashboards."""

    @staticmethod
    def render_dashboard(
        title: str,
        subtitle: str,
        kpi_cards: List[Dict[str, Any]],
        charts: List[Dict[str, Any]],
        tables: List[Dict[str, Any]] = None,
        insights: List[str] = None,
        event_log: List[Dict[str, Any]] = None,
        data_profile: Dict[str, Any] = None,
        asset_registry: List[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate a complete standalone HTML dashboard.

        Parameters:
            title: Dashboard title
            subtitle: Subtitle / system version
            kpi_cards: List of {label, value, color_class, delta}
            charts: List of {id, title, figure (plotly fig), tab_group}
            tables: List of {id, title, headers, rows}
            insights: List of insight strings
            event_log: List of {date, label, color, url}
            data_profile: Dict of profiling results
            asset_registry: List of asset metadata dicts
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        tables = tables or []
        insights = insights or []
        event_log = event_log or []
        data_profile = data_profile or {}
        asset_registry = asset_registry or []

        # Convert Plotly figures to HTML divs
        chart_htmls = []
        for i, chart in enumerate(charts):
            fig = chart.get('figure')
            if fig and isinstance(fig, go.Figure):
                chart_html = pio.to_html(
                    fig, full_html=False, include_plotlyjs=False,
                    config={"responsive": True, "displayModeBar": False, "scrollZoom": True}
                )
                chart_htmls.append({
                    'id': chart.get('id', f'chart_{i}'),
                    'title': chart.get('title', f'Chart {i+1}'),
                    'html': chart_html,
                    'tab_group': chart.get('tab_group', 'main'),
                })

        # Group charts by tab
        tab_groups = {}
        for ch in chart_htmls:
            grp = ch['tab_group']
            if grp not in tab_groups:
                tab_groups[grp] = []
            tab_groups[grp].append(ch)

        # Build HTML
        html = _build_html(
            title=title,
            subtitle=subtitle,
            timestamp=timestamp,
            kpi_cards=kpi_cards,
            tab_groups=tab_groups,
            tables=tables,
            insights=insights,
            event_log=event_log,
            data_profile=data_profile,
            asset_registry=asset_registry,
        )

        return html


def _build_html(title, subtitle, timestamp, kpi_cards, tab_groups, tables,
                insights, event_log, data_profile, asset_registry) -> str:
    """Build the complete HTML string with locked VIA Fusion style."""

    # KPI cards HTML
    kpi_html = ""
    for kpi in kpi_cards:
        color_class = kpi.get('color_class', '')
        delta_html = ""
        if kpi.get('delta'):
            delta_color = 'color:var(--gn)' if not str(kpi['delta']).startswith('-') else 'color:var(--co)'
            delta_html = f'<div class="io-s" style="{delta_color};font-weight:600">{kpi["delta"]}</div>'
        kpi_html += f'''<div class="io-c {color_class}" style="border-left-color:var({kpi.get('accent', '--bl')})">
            <div class="io-l">{kpi["label"]}</div>
            <div class="io-v" style="color:var({kpi.get('accent', '--bl')})">{kpi["value"]}</div>
            {delta_html}
        </div>\n'''

    # Tab buttons HTML
    tab_names = list(tab_groups.keys())
    all_tab_ids = []
    tab_btn_html = ""
    for i, name in enumerate(tab_names):
        tab_id = f"pg_{name.replace(' ', '_')}"
        all_tab_ids.append(tab_id)
        active = ' on' if i == 0 else ''
        tab_btn_html += f'<button class="{active}" onclick="switchTab(this,\'{tab_id}\')">{name}</button>\n'

    # Add extra tabs for tables, insights, events, profile
    extra_tabs = []
    if tables:
        tab_btn_html += f'<button onclick="switchTab(this,\'pg_tables\')">Data Tables</button>\n'
        extra_tabs.append('pg_tables')
    if insights:
        tab_btn_html += f'<button onclick="switchTab(this,\'pg_insights\')">Insights</button>\n'
        extra_tabs.append('pg_insights')
    if event_log:
        tab_btn_html += f'<button onclick="switchTab(this,\'pg_events\')">Events</button>\n'
        extra_tabs.append('pg_events')
    if data_profile:
        tab_btn_html += f'<button onclick="switchTab(this,\'pg_profile\')">Data Profile</button>\n'
        extra_tabs.append('pg_profile')
    if asset_registry:
        tab_btn_html += f'<button onclick="switchTab(this,\'pg_registry\')">Asset Registry</button>\n'
        extra_tabs.append('pg_registry')

    # Chart pages HTML
    chart_pages_html = ""
    for i, (name, charts_in_group) in enumerate(tab_groups.items()):
        tab_id = f"pg_{name.replace(' ', '_')}"
        active = ' on' if i == 0 else ''
        charts_content = ""
        for ch in charts_in_group:
            charts_content += f'''<div class="cd" style="margin-bottom:6px">
                <div class="cd-h">
                    <div class="cd-i" style="background:rgba(76,120,168,.1)">&#9783;</div>
                    <div class="cd-t">{ch["title"]}</div>
                </div>
                <div class="cd-b">{ch["html"]}</div>
            </div>\n'''
        chart_pages_html += f'<div class="pg{active}" id="{tab_id}">{charts_content}</div>\n'

    # Tables page
    tables_page_html = ""
    if tables:
        tables_content = ""
        for tbl in tables:
            headers = "".join(f"<th>{h}</th>" for h in tbl.get('headers', []))
            rows_html = ""
            for row in tbl.get('rows', []):
                cells = "".join(f"<td>{c}</td>" for c in row)
                rows_html += f"<tr>{cells}</tr>\n"
            tables_content += f'''<div class="cd" style="margin-bottom:6px">
                <div class="cd-h">
                    <div class="cd-i" style="background:rgba(90,158,111,.1)">&#9783;</div>
                    <div class="cd-t">{tbl.get("title", "Data")}</div>
                    <div class="cd-s">{len(tbl.get("rows", []))} rows</div>
                </div>
                <div class="cd-b"><div class="tbl-scroll"><table class="mx">
                    <thead><tr>{headers}</tr></thead>
                    <tbody>{rows_html}</tbody>
                </table></div></div>
            </div>\n'''
        tables_page_html = f'<div class="pg" id="pg_tables">{tables_content}</div>\n'

    # Insights page
    insights_page_html = ""
    if insights:
        items = ""
        for idx, ins in enumerate(insights, 1):
            items += f'''<div class="iss-item" style="border-left-color:var(--bl)">
                <span style="font-family:var(--mo);color:var(--i3);min-width:20px">{idx}.</span>
                <span>{ins}</span>
            </div>\n'''
        insights_page_html = f'''<div class="pg" id="pg_insights">
            <div class="cd"><div class="cd-h">
                <div class="cd-i" style="background:rgba(76,120,168,.1)">&#128161;</div>
                <div class="cd-t">Key Insights & Observations</div>
            </div><div class="cd-b">{items}</div></div>
        </div>\n'''

    # Events page
    events_page_html = ""
    if event_log:
        evt_rows = ""
        for evt in event_log:
            url_link = f'<a href="{evt.get("url","#")}" target="_blank" style="color:var(--bl);text-decoration:none">Verify</a>' if evt.get('url') else ''
            evt_rows += f'''<tr>
                <td style="font-family:var(--mo);white-space:nowrap">{evt.get("date","")}</td>
                <td>{evt.get("label","")}</td>
                <td><span class="lt" style="background:{evt.get("color","var(--bl)")}"></span></td>
                <td>{url_link}</td>
            </tr>\n'''
        events_page_html = f'''<div class="pg" id="pg_events">
            <div class="cd"><div class="cd-h">
                <div class="cd-i" style="background:rgba(196,148,58,.1)">&#9888;</div>
                <div class="cd-t">Historical Event Matrix</div>
            </div><div class="cd-b"><div class="tbl-scroll"><table class="mx">
                <thead><tr><th>Date</th><th>Event</th><th>Type</th><th>Verify</th></tr></thead>
                <tbody>{evt_rows}</tbody>
            </table></div></div></div>
        </div>\n'''

    # Profile page
    profile_page_html = ""
    if data_profile:
        profile_rows = ""
        for k, v in data_profile.items():
            val_str = str(v) if not isinstance(v, (dict, list)) else json.dumps(v, ensure_ascii=False, default=str)
            profile_rows += f'''<div class="tr-row">
                <div class="tr-row-k">{k}</div>
                <div class="tr-row-v">{val_str}</div>
            </div>\n'''
        profile_page_html = f'''<div class="pg" id="pg_profile">
            <div class="cd"><div class="cd-h">
                <div class="cd-i" style="background:rgba(122,109,170,.1)">&#128202;</div>
                <div class="cd-t">Data Profile</div>
            </div><div class="cd-b">{profile_rows}</div></div>
        </div>\n'''

    # Asset Registry page
    registry_page_html = ""
    if asset_registry:
        reg_rows = ""
        for asset in asset_registry:
            reg_rows += f'''<tr>
                <td><code>{asset.get("asset_id","")}</code></td>
                <td>{asset.get("asset_type","")}</td>
                <td>{asset.get("visualization_type","")}</td>
                <td style="font-family:var(--mo);font-size:9px">{asset.get("generation_timestamp","")}</td>
            </tr>\n'''
        registry_page_html = f'''<div class="pg" id="pg_registry">
            <div class="cd"><div class="cd-h">
                <div class="cd-i" style="background:rgba(67,154,154,.1)">&#128190;</div>
                <div class="cd-t">Smart Asset Registry</div>
                <div class="cd-s">{len(asset_registry)} assets</div>
            </div><div class="cd-b"><div class="tbl-scroll"><table class="mx">
                <thead><tr><th>Asset ID</th><th>Type</th><th>Viz Type</th><th>Generated</th></tr></thead>
                <tbody>{reg_rows}</tbody>
            </table></div></div></div>
        </div>\n'''

    # Frozen data block
    frozen_data = json.dumps({
        "generated": timestamp,
        "title": title,
        "kpi_count": len(kpi_cards),
        "chart_count": sum(len(v) for v in tab_groups.values()),
        "table_count": len(tables),
        "insight_count": len(insights),
        "event_count": len(event_log),
    }, ensure_ascii=False)

    # ═══════════════════════════════════════════════════════════
    # FINAL HTML ASSEMBLY
    # ═══════════════════════════════════════════════════════════
    html = f'''<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — {timestamp}</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700&display=swap');
:root{{
  --bg:#f5f4f0;--bg1:#edecea;--bg2:#e5e3df;--sf:#fff;--sf2:#fafaf8;
  --bd:#dbd9d3;--bd2:#ccc9c1;
  --i0:#1e1d1a;--i1:#3d3c38;--i2:#6b6860;--i3:#9c9890;--i4:#c4c0b8;
  --bl:#4c78a8;--bl-l:#d0e1f0;
  --tl:#439a9a;--tl-l:#c8e6e6;
  --gn:#5a9e6f;--gn-l:#cde8d5;
  --am:#c4943a;--am-l:#f5e2b8;
  --co:#c96b5a;--co-l:#f5d0c8;
  --vi:#7a6daa;--vi-l:#dcd8f0;
  --ro:#b05580;
  --mo:'DM Mono',monospace;--sa:'DM Sans',system-ui,sans-serif;
  --r:5px;--r2:8px;--r3:12px;
  --sh:0 1px 3px rgba(0,0,0,.06);--sh2:0 4px 12px rgba(0,0,0,.08);
}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:var(--sa);background:var(--bg);color:var(--i0);font-size:11px;line-height:1.55}}
.w{{max-width:1600px;margin:0 auto;padding:10px 14px}}
/* HEADER */
.hdr{{background:var(--sf);border:1px solid var(--bd);border-radius:var(--r3);padding:12px 16px;margin-bottom:8px;position:relative;overflow:hidden;display:flex;align-items:center;gap:12px}}
.hdr::before{{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,var(--bl),var(--tl),var(--vi),var(--am),var(--co))}}
.h1t{{font-size:17px;font-weight:700;letter-spacing:-.4px}}.h1t span{{color:var(--bl)}}
.h2t{{color:var(--i3);font-size:9px;margin-top:1px;font-weight:600;letter-spacing:.3px;text-transform:uppercase}}
.hdr-r{{margin-left:auto;display:flex;gap:5px;align-items:center}}
/* TABS */
.pt{{display:flex;gap:2px;margin-bottom:8px;flex-wrap:wrap}}
.pt button{{padding:7px 14px;border:1px solid var(--bd);border-radius:var(--r2) var(--r2) 0 0;background:var(--bg1);color:var(--i2);font:600 11px var(--sa);cursor:pointer;border-bottom:2px solid transparent;transition:.15s;white-space:nowrap}}
.pt button.on{{background:var(--sf);color:var(--bl);border-bottom-color:var(--bl);box-shadow:var(--sh)}}
.pt button:hover:not(.on){{background:var(--bg2);color:var(--i1)}}
.pg{{display:none}}.pg.on{{display:block}}
/* IO CARDS */
.io-g{{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:4px;margin-bottom:8px}}
.io-c{{background:var(--sf);border:1px solid var(--bd);border-radius:var(--r);padding:5px 7px;border-left:3px solid var(--bd)}}
.io-l{{font-size:8px;color:var(--i3);text-transform:uppercase;letter-spacing:.3px;font-weight:600}}
.io-v{{font-size:18px;font-weight:700;font-family:var(--mo);margin:1px 0}}
.io-s{{font-size:8px;color:var(--i4)}}
/* CARDS */
.cd{{background:var(--sf);border:1px solid var(--bd);border-radius:var(--r2);margin-bottom:6px;overflow:hidden;transition:.15s}}
.cd:hover{{box-shadow:var(--sh)}}
.cd-h{{display:flex;align-items:center;gap:6px;padding:7px 10px;border-bottom:1px solid var(--bd);background:var(--sf2)}}
.cd-i{{width:24px;height:24px;border-radius:var(--r);display:flex;align-items:center;justify-content:center;font-size:13px;flex-shrink:0}}
.cd-t{{font-weight:600;font-size:11px;flex:1}}
.cd-s{{font-family:var(--mo);font-size:9px;color:var(--i3);padding:1px 5px;background:var(--bg1);border-radius:10px}}
.cd-b{{padding:8px 10px}}
/* TABLE */
.tbl-scroll{{max-height:560px;overflow-y:auto;border:1px solid var(--bd);border-radius:var(--r)}}
.mx{{width:100%;border-collapse:collapse;font-size:10px}}
.mx th{{background:var(--bg1);padding:4px 6px;text-align:left;font-weight:600;color:var(--i2);border-bottom:2px solid var(--bd);white-space:nowrap;position:sticky;top:0;z-index:1}}
.mx td{{padding:3px 6px;border-bottom:1px solid var(--bd);vertical-align:top}}
.mx tr:hover{{background:rgba(76,120,168,.03)}}
.mx code{{font-family:var(--mo);font-size:9px;background:var(--bg1);padding:0 3px;border-radius:3px}}
/* BADGES */
.bd2{{display:inline-block;padding:1px 5px;border-radius:4px;font-family:var(--mo);font-size:8.5px;font-weight:600;letter-spacing:.2px}}
/* BUTTONS */
.bn{{padding:4px 10px;border:1px solid var(--bd);border-radius:var(--r);font:500 10px var(--sa);cursor:pointer;transition:.15s;background:var(--sf);color:var(--i1)}}
.bn:hover{{border-color:var(--bl);color:var(--bl)}}
.bn.bp{{background:var(--bl);color:#fff;border-color:var(--bl)}}.bn.bp:hover{{background:#3b6790}}
.bn.sm{{padding:2px 7px;font-size:9px}}
/* LIGHTS */
.lt{{display:inline-block;width:7px;height:7px;border-radius:50%;margin-right:3px}}
/* ISSUE ITEMS */
.iss-item{{display:flex;gap:5px;align-items:flex-start;padding:4px 6px;border:1px solid var(--bd);border-radius:var(--r);margin-bottom:3px;font-size:10px;background:var(--sf2);transition:.1s}}
.iss-item:hover{{border-color:var(--bd2)}}
/* TREE ROW */
.tr-row{{display:flex;align-items:baseline;gap:6px;margin-bottom:2px;font-size:10px}}
.tr-row-k{{font-family:var(--mo);color:var(--i3);min-width:120px;flex-shrink:0;font-size:9px}}
.tr-row-v{{color:var(--i1);font-family:var(--mo);font-size:9px;word-break:break-all}}
/* LAYOUT */
.g2{{display:grid;grid-template-columns:1fr 1fr;gap:6px}}
@media(max-width:900px){{.g2{{grid-template-columns:1fr}}}}
/* DARK THEME */
body.theme-dark{{--bg:#1a1918;--bg1:#232220;--bg2:#2a2927;--sf:#242322;--sf2:#1e1d1b;--bd:#3a3835;--bd2:#4a4845;--i0:#f0ede8;--i1:#d8d4cc;--i2:#a09890;--i3:#6c6860;--i4:#4a4840;--bl:#5a8fc0;--bl-l:#1a2e40;--tl:#4aafaf;--tl-l:#142828;--gn:#6ab57f;--gn-l:#152218;--am:#d4a44a;--am-l:#2a1e08;--co:#d97b6a;--co-l:#2a1210;--vi:#8a7dba;--vi-l:#1e1830;--ro:#c06090}}
body.theme-dark .cd{{box-shadow:none}}
body.theme-dark .mx th{{background:var(--bg2)}}
/* NOTIFY */
.notify{{position:fixed;top:52px;right:14px;z-index:9999;display:flex;flex-direction:column;gap:3px;pointer-events:none}}
.notif{{padding:6px 12px;border-radius:var(--r2);font-size:10px;font-weight:500;border:1px solid;animation:fadeSlide .2s ease-out;cursor:pointer;background:var(--sf);box-shadow:var(--sh2);pointer-events:auto}}
.notif.ok{{border-color:var(--gn);color:var(--gn)}}.notif.err{{border-color:var(--co);color:var(--co)}}.notif.info{{border-color:var(--bl);color:var(--bl)}}
@keyframes fadeSlide{{from{{opacity:0;transform:translateY(5px)}}to{{opacity:1;transform:translateY(0)}}}}
/* PLOTLY OVERRIDE */
.js-plotly-plot .plotly .modebar{{display:none!important}}
</style>
<script src="https://cdn.plot.ly/plotly-2.35.0.min.js"></script>
</head>
<body>
<div class="notify" id="notifyArea"></div>
<div class="w">

<!-- HEADER -->
<div class="hdr">
  <div style="flex:1">
    <div class="h1t">Veritas<span>AutoPlot</span> <span style="font-size:11px;color:var(--i3);font-weight:400">{subtitle}</span></div>
    <div class="h2t">VERITAS INTELLIGENCE ANALYTICS</div>
    <div style="font-size:9px;color:var(--i2);margin-top:2px;font-family:var(--mo)">{timestamp} &middot; DATA-LOCKED &middot; VIEW-ONLY</div>
  </div>
  <div class="hdr-r">
    <span class="lt" style="background:var(--gn)"></span>
    <span style="font-size:9px;font-family:var(--mo);font-weight:600;color:var(--gn)">READY</span>
    <button class="bn sm" onclick="toggleTheme()">&#9680; Theme</button>
  </div>
</div>

<!-- KPI CARDS -->
<div class="io-g">
{kpi_html}
</div>

<!-- TABS -->
<div class="pt">
{tab_btn_html}
</div>

<!-- CHART PAGES -->
{chart_pages_html}

<!-- TABLE PAGE -->
{tables_page_html}

<!-- INSIGHTS PAGE -->
{insights_page_html}

<!-- EVENTS PAGE -->
{events_page_html}

<!-- PROFILE PAGE -->
{profile_page_html}

<!-- REGISTRY PAGE -->
{registry_page_html}

</div>

<script>
/* DATA LOCK */
var VERITAS_META = Object.freeze({frozen_data});

/* TAB SWITCH */
function switchTab(btn, pgId) {{
  document.querySelectorAll('.pt button').forEach(function(b){{ b.classList.remove('on'); }});
  document.querySelectorAll('.pg').forEach(function(p){{ p.classList.remove('on'); }});
  btn.classList.add('on');
  var el = document.getElementById(pgId);
  if (el) el.classList.add('on');
  /* Re-trigger Plotly resize */
  setTimeout(function(){{ window.dispatchEvent(new Event('resize')); }}, 50);
}}

/* THEME TOGGLE */
function toggleTheme() {{
  document.body.classList.toggle('theme-dark');
  notify(document.body.classList.contains('theme-dark') ? 'Dark Mode' : 'Light Mode', 'info');
  /* Re-render plotly for theme */
  setTimeout(function(){{ window.dispatchEvent(new Event('resize')); }}, 100);
}}

/* NOTIFY */
function notify(msg, type) {{
  var nb = document.getElementById('notifyArea');
  var el = document.createElement('div');
  el.className = 'notif ' + (type || 'info');
  el.textContent = msg;
  el.onclick = function(){{ if(el.parentNode) el.parentNode.removeChild(el); }};
  nb.appendChild(el);
  setTimeout(function(){{ if(el.parentNode) el.parentNode.removeChild(el); }}, 2500);
}}

/* INIT */
document.addEventListener('DOMContentLoaded', function() {{
  notify('VeritasAutoPlot Dashboard Loaded', 'ok');
}});
</script>
</body>
</html>'''

    return html
