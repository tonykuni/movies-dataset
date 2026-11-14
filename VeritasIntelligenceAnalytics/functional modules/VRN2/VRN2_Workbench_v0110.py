#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN2_Workbench v0110 — v0109 薄尾(v0109 與它的前版一字不改):左右面板同字級 · 按鍵同高 · 卡片字不超框 · 矩陣化 · 檢視副本 · 千分位。

操作員 2026-11-03(桌機截圖三張):
  「附件照片部分鎖死不動」(第一張:分頁列 00–04 + 匯出格式 + 匯出本頁完整內容)→ main > div.bar 一個字都不碰(CSS 選擇器不含 .bar)。
  「第二圖超出格子」(03 頁卡片:鎖定版本 · Parquet 輸出冊 · 收尾收據 VRN2_Closeout_v0175.json · 備份快照)→ 大字值會斷行 + 自動縮字(19px 起 · 最小 11px)。
  「左右面板字體大小一致」→ 左欄按鍵 9px → 10.45px(= 右側內文 · 細節欄字級)· 「按鍵高度要一致」→ 左欄與各頁內的按鍵一律 28px(不換行 · 太長先縮字再省略)。
  「左右面板矩陣化不夠仍亂」→ 左欄 ② 的檔案數小格 → 4 欄矩陣(表頭一列 · 數字一列);④ 輸出位置的一段字 → 路徑 / 同步 / 增量庫 / 累計 / 本輪 矩陣;
     04 頁交接快照(一段 key: value 純文字)→ 項目 / 內容矩陣(純文字照留在頁內 · 匯出照舊)。
  「擷取特定資料 · 特定日期 → 檢視副本」→ 03 頁那一格多一個「檢視副本」:同一套條件(資料冊 · 起訖日 · 標的 / 關鍵字)在新分頁開一份唯讀表格副本。
  「數字小數點兩位要有千分位號」→ 畫面上 1234.50 這種(兩位小數 · 四位以上整數)顯示成 1,234.50(資料冊與匯出不改 · 只改顯示)。
  「HEADER 第三行:Transform investment reports into structured database intelligence.」→ 頁首第三行(header.vh 的 .tag)換成這句(只換字 · 樣式不動)。
  「html u/i 自動最佳化 · 字體偏小較佳」→ 不放大字級(維持 10.45 / 9 / 8)· 自動縮字只往小縮 · 視窗改大小 / 換分頁時重算。
做法:render = v0109 render → 後處理加一段 CSS(id="wb110-tpl" · 只用模板 15 色 · 字級 19 / 11 / 10.45 / 9 / 8)與一段腳本(id="wb110-dom")。
window.VRN2_DATA 一字不改;U/I 匯出 = 輸出冊(前版規則)。動詞同前版:render · logo · --selftest。
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

VERSION = "v0110"
DISPLAY_NAME = "VRN2_Workbench"
PRIOR_NAME = "VRN2_Workbench_v0109.py"
HERE = Path(__file__).resolve().parent


def _load_prior():
    path = HERE / PRIOR_NAME
    if not path.is_file():
        raise FileNotFoundError("前版 %s 不在 %s" % (PRIOR_NAME, HERE))
    spec = importlib.util.spec_from_file_location("vrn2_workbench_prior_v0109", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PRIOR = _load_prior()               # v0109
TAGLINE = "Transform investment reports into structured database intelligence."   # 操作員 2026-11-04:HEADER 第三行
_TAG_RE = re.compile(r'(<header class="vh">.*?<div class="tag">)([^<]*)(</div>)', re.S)
PALETTE = PRIOR.PALETTE
SIZES_PX = PRIOR.SIZES_PX
BTN_H = 28

_CSS = """<style id="wb110-tpl">/* VRN2_Workbench v0110 · 左右面板同字級 10.45px · 按鍵同高 28px · 卡片字不超框 · 左欄 / 交接矩陣 · 分頁列 .bar 不動(操作員鎖定)*/
aside a.action,aside button,section.tabsec .box a.action,section.tabsec .box button,section.tabsec .toolbar button,section.tabsec .toolbar a.action{box-sizing:border-box;height:28px!important;min-height:28px;max-height:28px;padding:0 8px!important;margin:0;display:inline-flex!important;align-items:center;justify-content:center;white-space:nowrap!important;overflow:hidden;text-overflow:ellipsis;line-height:1!important;font-size:var(--w9s)!important;vertical-align:middle}
aside a.action,aside button.foldbtn{display:flex!important;width:100%}
aside .w9-row2,aside .w9-row3{grid-template-columns:repeat(auto-fit,minmax(74px,1fr))!important}
aside .w9-row2 a.action,aside .w9-row3 a.action{font-size:var(--w9s)!important;font-weight:600;padding:0 4px!important}
.cards>.box{min-width:0;overflow:hidden}
.cards>.box>div:nth-child(2){font-size:19px!important;line-height:1.2;overflow-wrap:anywhere;word-break:break-all;white-space:normal}
.cards>.box>.subtle{overflow-wrap:anywhere;word-break:break-all}
table.w10-kv{width:100%;border-collapse:collapse;table-layout:fixed;margin:6px 0 0;background:#ffffff;border:1px solid #dbd9d3}
table.w10-kv th{font:700 var(--w9t) var(--w9f);letter-spacing:.05em;text-transform:uppercase;color:#6b6860;text-align:left;padding:3px 5px;border:1px solid #ebe9e3;background:#f2f1ec;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
table.w10-kv td{font:700 var(--w9s) var(--w9f);color:#1b1a17;padding:3px 5px;border:1px solid #ebe9e3;text-align:right;white-space:nowrap}
table.w10-kv td.w10-e{color:#dbd9d3}
table.w10-of{width:100%;border-collapse:collapse;table-layout:fixed;margin:0 0 6px;background:#ffffff}
table.w10-of th{font:700 var(--w9t) var(--w9f);letter-spacing:.05em;color:#6b6860;text-align:left;vertical-align:top;padding:3px 5px;border-bottom:1px solid #ebe9e3;width:4.6em;white-space:nowrap}
table.w10-of td{font:400 var(--w9s) var(--w9f);color:#33403f;padding:3px 5px;border-bottom:1px solid #ebe9e3;overflow-wrap:anywhere;word-break:normal}
table.w10-of tr:last-child th,table.w10-of tr:last-child td{border-bottom:none}
.w10-ho{margin:6px 0 0}
.w10-ho pre{display:none}
.w10-num{font-variant-numeric:tabular-nums}
</style>"""
CSS_SHA256 = "608555d95efebcadee84a6aba6092f5d796a35e9d034e6f383d223086633c290"      # 建置時填(鎖定:CSS 一改就對不上 → 自測紅 → 要出新版)

HO_KEYS = {"root": ("Root", "根目錄"), "ui": ("U/I", "介面"), "logo": ("Logo", "標誌"), "inputs": ("Inputs", "輸入"), "closeout": ("Close-out", "收尾"),
           "completion": ("Completion", "完成判定"), "idempotence": ("Idempotence", "冪等"), "books": ("Books", "輸出冊"), "lock": ("Lock", "鎖定"),
           "generated": ("Generated", "產生時間")}

_DOM = r"""<script id="wb110-dom">(function(){
  var KEYS = %(keys)s, MIN_CARD = 11, MIN_BTN = 9;
  function q(s, r){ return Array.prototype.slice.call((r || document).querySelectorAll(s)); }
  function esc(s){ return String(s == null ? '' : s).replace(/[&<>"]/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }
  var N2 = /^([-+]?)(\d{4,})(\.\d{2})$/;
  function money(t){ var m = N2.exec(String(t).trim()); return m ? m[1] + m[2].replace(/\B(?=(\d{3})+(?!\d))/g, ',') + m[3] : null; }
  function numCells(root){ q('td', root).forEach(function(td){ if (td.children.length || td.getAttribute('data-w10n')) return; var m = money(td.textContent); if (m) { td.textContent = m; td.setAttribute('data-w10n', '1'); td.className += ' w10-num'; } }); }
  function fs(el, s){ el.style.setProperty('font-size', s + 'px', 'important'); }
  function fit(el, max, min){ if (!el || !el.clientWidth) return; var s = max; fs(el, s); while (el.scrollWidth > el.clientWidth + 1 && s > min) { s -= 0.5; fs(el, s); } }
  function fitAll(){
    q('.cards>.box>div:nth-child(2)').forEach(function(v){ v.style.whiteSpace = 'nowrap'; fit(v, 19, MIN_CARD); if (v.scrollWidth > v.clientWidth + 1) v.style.whiteSpace = 'normal'; });
    q('aside a.action, aside button, section.tabsec .box a.action, section.tabsec .box button, section.tabsec .toolbar button').forEach(function(b){
      if (!b.clientWidth) return; b.style.removeProperty('font-size'); var cs = parseFloat(getComputedStyle(b).fontSize) || 10.45; if (b.scrollWidth > b.clientWidth + 1) { fit(b, cs, MIN_BTN); b.title = b.title || b.textContent.trim(); } });
  }
  function kvMatrix(){ q('aside .w9-kv').forEach(function(kv){ var cells = q(':scope > div', kv).map(function(d){ var s = d.querySelector('small'), b = d.querySelector('b'); return [s ? s.textContent : '', b ? b.textContent : '']; });
      if (!cells.length) return; var h = '<table class="w10-kv" data-w10="kv"><tbody>';
      for (var i = 0; i < cells.length; i += 4) { var row = cells.slice(i, i + 4); while (row.length < 4) row.push(['', '']);
        h += '<tr>' + row.map(function(c){ return '<th data-w9="1">' + esc(c[0]) + '</th>'; }).join('') + '</tr><tr>' + row.map(function(c){ return '<td' + (c[0] ? '' : ' class="w10-e"') + '>' + esc(c[1] || (c[0] ? '0' : '—')) + '</td>'; }).join('') + '</tr>'; }
      var t = document.createElement('div'); t.innerHTML = h + '</tbody></table>'; kv.parentNode.replaceChild(t.firstChild, kv); }); }
  function outMatrix(){ q('aside .outfolder').forEach(function(of){ if (of.querySelector('table.w10-of')) return; var p = of.querySelector('.path'); if (!p) return;
      var sub = p.querySelector('.subtle'), path = '', rows = [];
      Array.prototype.forEach.call(p.childNodes, function(n){ if (n.nodeType === 3) path += n.nodeValue; });
      rows.push(['路徑', path.trim()]); if (sub) rows.push(['同步', sub.textContent.trim()]);
      var info = q(':scope > div.subtle', of)[0];
      if (info) { info.textContent.split(' · ').forEach(function(seg){ seg = seg.trim(); if (!seg) return;
          var m = /^(增量庫|累計|新檔)\s*(.*)$/.exec(seg);
          if (m) rows.push([m[1] === '新檔' ? '本輪' : m[1], (m[1] === '新檔' ? '新檔 ' : '') + m[2]]); else rows.push(['', seg]); }); }
      var t = document.createElement('table'); t.className = 'w10-of'; t.setAttribute('data-w10', 'of');
      t.innerHTML = '<tbody>' + rows.map(function(r){ return '<tr><th data-w9="1">' + esc(r[0]) + '</th><td>' + esc(r[1]) + '</td></tr>'; }).join('') + '</tbody>';
      of.insertBefore(t, p); p.style.display = 'none'; if (info) info.style.display = 'none'; }); }
  function handover(){ q('section.tabsec .box').forEach(function(bx){ var pre = bx.querySelector(':scope > pre'); if (!pre || bx.querySelector('table[data-w10="ho"]')) return;
      var lines = pre.textContent.split('\n').filter(function(l){ return l.trim(); }), rows = [];
      lines.forEach(function(l){ var m = /^([A-Za-z_]+):\s*(.*)$/.exec(l); if (m) rows.push([m[1], m[2]]); else if (rows.length) rows[rows.length - 1][1] += ' ' + l.trim(); });
      if (rows.length < 3 || rows.length < lines.length * 0.6) return;
      var h = '<div class="w9-wrap w10-ho"><table class="w9-mx" data-w10="ho"><thead><tr><th data-w9="1"><span class="w9h"><span class="w9en">ITEM</span><span class="w9zh">項目</span></span></th><th data-w9="1"><span class="w9h"><span class="w9en">DETAIL</span><span class="w9zh">內容</span></span></th></tr></thead><tbody>';
      rows.forEach(function(r){ var k = KEYS[r[0]] || [r[0], '']; h += '<tr><td class="w9-k w9-item"><b>' + esc(k[1] || k[0]) + '</b><span>' + esc(k[0]) + '</span></td><td>' + esc(r[1]) + '</td></tr>'; });
      var d = document.createElement('div'); d.innerHTML = h + '</tbody></table></div>'; bx.insertBefore(d.firstChild, pre); bx.className += ' w10-ho'; }); }
  function xview(){ var D = window.VRN2_DATA || {books: {}}, ds = (document.getElementById('xDs') || {}).value || '', from = (document.getElementById('xFrom') || {}).value || '',
      to = (document.getElementById('xTo') || {}).value || '', kw = ((document.getElementById('xQ') || {}).value || '').trim(), B = D.books[ds] || {cols: [], rows: []};
    var R = (B.rows || []).filter(function(r){ var d = String(r.REPORT_DATE || r.LATEST_REPORT_DATE || r.DATE || ''); return (!from || d >= from) && (!to || d <= to) && (!kw || JSON.stringify(r).indexOf(kw) >= 0); });
    var C = B.cols || [], head = '<tr>' + C.map(function(c){ return '<th>' + esc(c) + '</th>'; }).join('') + '</tr>';
    var body = R.map(function(r){ return '<tr>' + C.map(function(c){ var v = r[c]; var m = money(v == null ? '' : v); return '<td' + (m ? ' class="n"' : '') + '>' + esc(m || (v == null ? '' : v)) + '</td>'; }).join('') + '</tr>'; }).join('');
    var title = 'VRN-2 檢視副本 · ' + ds + ' · ' + (from || '—') + ' → ' + (to || '—') + (kw ? ' · ' + kw : '');
    var css = 'body{margin:16px;background:#f2f1ec;color:#33403f;font:10.45px Consolas,"Microsoft JhengHei",monospace}h1{font:700 11px Consolas,"Microsoft JhengHei",monospace;color:#1b1a17;margin:0 0 4px}p{color:#6b6860;margin:0 0 8px}'
      + 'table{border-collapse:collapse;background:#ffffff;border:1px solid #dbd9d3}th{font:700 9px Consolas,"Microsoft JhengHei",monospace;text-align:left;color:#6b6860;background:#ffffff;position:sticky;top:0;padding:4px 6px;border-bottom:1px solid #dbd9d3}'
      + 'td{padding:3px 6px;border-bottom:1px solid #ebe9e3;vertical-align:top;max-width:36em;overflow-wrap:anywhere}td.n{text-align:right;white-space:nowrap}';
    var html = '<!DOCTYPE html><html><head><meta charset="utf-8"><title>' + esc(title) + '</title><style>' + css + '</style></head><body><h1>' + esc(title) + '</h1><p>'
      + R.length.toLocaleString('en-US') + ' 列 · 唯讀副本 · 資料來自本頁的輸出冊(不改任何檔)</p><table><thead>' + head + '</thead><tbody>' + body + '</tbody></table></body></html>';
    var url = URL.createObjectURL(new Blob([html], {type: 'text/html;charset=utf-8'})); var w = window.open(url, '_blank'); if (!w) location.href = url; return R.length; }
  window.w10xview = xview;
  function addView(){ var bt = document.querySelector('button[data-act="extract"]'); if (!bt || document.querySelector('button[data-w10="xview"]')) return;
    var v = document.createElement('button'); v.type = 'button'; v.setAttribute('data-w10', 'xview'); v.textContent = '檢視副本'; v.title = '同一套條件在新分頁開一份唯讀表格';
    v.addEventListener('click', function(e){ e.preventDefault(); e.stopPropagation(); xview(); }); bt.parentNode.insertBefore(v, bt.nextSibling); }
  function run(){ try { kvMatrix(); outMatrix(); handover(); addView(); numCells(document); fitAll(); } catch (e) { if (window.console) console.warn('wb110', e); } }
  run();
  var body = document.getElementById('dsBody');
  if (body && window.MutationObserver) new MutationObserver(function(){ numCells(body); }).observe(body, {childList: true, subtree: true});
  q('.tabs button').forEach(function(b){ b.addEventListener('click', function(){ setTimeout(function(){ numCells(document); fitAll(); }, 60); }); });
  var tm = null; window.addEventListener('resize', function(){ clearTimeout(tm); tm = setTimeout(fitAll, 120); });
})();</script>""" % {"keys": json.dumps({k: list(v) for k, v in HO_KEYS.items()}, ensure_ascii=False)}


def augment110(page: str) -> tuple:
    """(頁面, 說明)· 純函式可測 · 重入不重複 · 不動 main > div.bar。"""
    if 'id="wb110-tpl"' in page:
        return page, "已是 v0110"
    notes = []
    has_x = 'data-act="extract"' in page                     # 先看(腳本本身也含這串字)
    if page.count("</head>") == 1:
        page = page.replace("</head>", _CSS + "\n</head>", 1)
    else:
        notes.append("沒有 </head>(CSS 接在頁尾)")
        page = page + _CSS
    if page.count("</title>") >= 1:
        page = page.replace("</title>", "</title><!-- VRN2_Workbench %s over v0109 · 同字級 · 同按鍵高 · 矩陣化 · 檢視副本 %s -->" % (VERSION, CSS_SHA256[:12]), 1)
    page = page.replace("</body>", _DOM + "</body>", 1) if page.count("</body>") == 1 else page + _DOM
    page, n_tag = _TAG_RE.subn(lambda m: m.group(1) + TAGLINE + m.group(3), page, count=1)
    if not n_tag:
        notes.append("沒有頁首第三行(.tag)· 標語不換")
    if not has_x:
        notes.append("沒有 03 頁擷取格(檢視副本不加)")
    return page, " · ".join(notes) or "同字級 + 同按鍵高 + 卡片自動縮字 + 左欄 / 交接矩陣 + 千分位 + 檢視副本 + 頁首第三行都套上"


def render(root: Path, out_path: Path | None = None, logo: str | None = None, assets_zip: Path | None = None) -> Path:
    root = Path(root).resolve()
    out = PRIOR.render(root, out_path, logo, assets_zip)
    page = Path(out).read_text(encoding="utf-8")
    try:
        page, note = augment110(page)
    except Exception as error:  # noqa: BLE001  後處理失敗不毀 v0109 頁
        print("    [U/I] [YELLOW] Workbench v0110 後處理沒做成(v0109 頁照出):%s: %s" % (type(error).__name__, str(error)[:160]), flush=True)
        return Path(out)
    if "沒有" in note:
        print("    [U/I] [YELLOW] Workbench v0110 · %s" % note, flush=True)
    tmp = Path(out).with_suffix(".v0110.tmp")
    tmp.write_text(page, encoding="utf-8")
    tmp.replace(Path(out))
    return Path(out)


# ── 自測 ──────────────────────────────────────────────────────────────────────────────────────────────
def selftest() -> int:
    import contextlib
    import io
    import tempfile
    fails = []

    def chk(label, cond):
        print("[%s] %s" % ("PASS" if cond else "FAIL", label))
        if not cond:
            fails.append(label)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc_prior = PRIOR.selftest()
    chk("① 前版 v0109 自測照過(%s)" % (buf.getvalue().strip().splitlines() or ["—"])[-1][:60], rc_prior == 0)
    src = Path(__file__).read_text(encoding="utf-8")
    css_sha = hashlib.sha256(_CSS.encode("utf-8")).hexdigest()
    colors = {c.lower() for c in re.findall(r"#[0-9a-fA-F]{6}\b", _CSS + _DOM)}
    sizes = {float(x) for x in re.findall(r"font(?:-size)?:[^;}\"']*?(\d+(?:\.\d+)?)px", _CSS + _DOM)}
    chk("② 鎖定:CSS SHA-256 = 釘住的值 · 只用模板 15 色 · 字級只用 19 / 11 / 10.45 / 9 / 8(按鍵高 28)· 第 3 行加速器標記",
        css_sha == CSS_SHA256 and colors <= set(PALETTE) and sizes <= {float(x) for x in SIZES_PX} and src.splitlines()[2].strip() == "# [VIA:ACCEL-BRIDGE:v0111]")
    sel = re.sub(r"\{[^}]*\}", "\n", re.sub(r"/\*.*?\*/", "", _CSS.split(">", 1)[1].rsplit("</style>", 1)[0], flags=re.S))
    chk("③ 分頁列(main > div.bar · 操作員鎖定)一個選擇器都不碰 · 按鍵規則只在左欄與各頁區塊內 · 按鍵同高 28px · 左欄按鍵字級 = 內文 10.45(var(--w9s))",
        ".bar" not in sel and not re.search(r"\.tabs(?!ec)", sel) and "header" not in sel and "height:28px!important" in _CSS and "aside .w9-row2 a.action,aside .w9-row3 a.action{font-size:var(--w9s)!important" in _CSS)
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "VIA"
        v2 = root / "VIA_Reports" / "vrn2"
        W107 = PRIOR.W107
        W107._fixture_v2(v2)
        page = W107.augment(PRIOR._fixture_page(W107), v2)
        p108, _n = PRIOR.PRIOR.augment108(page, root, v2, _dt.date(2026, 11, 3))
        p109, _n9 = PRIOR.augment109(p108, root, v2)
        got, note = augment110(p109)
        chk("④ 頁面:v0110 CSS 在 v0109 之後 · 腳本在 </body> 前 · 版號註記 · v0109 內容一字不少(只多兩段)",
            got.count('id="wb110-tpl"') == 1 and got.index('id="wb109-tpl"') < got.index('id="wb110-tpl"') < got.index("</head>")
            and got.count('id="wb110-dom"') == 1 and got.index('id="wb110-dom"') < got.index("</body>") and "VRN2_Workbench v0110 over v0109" in got
            and _TAG_RE.sub(lambda m: m.group(1) + _TAG_RE.search(p109).group(2) + m.group(3), got.replace(_CSS + "\n", "", 1).replace(_DOM, "", 1).replace("<!-- VRN2_Workbench %s over v0109 · 同字級 · 同按鍵高 · 矩陣化 · 檢視副本 %s -->" % (VERSION, CSS_SHA256[:12]), "", 1), count=1) == p109)
        old_tag = "AI-Powered System to Transform the Investment Reports into Database Intelligence Asset."
        sample = ('<html><head><title>x</title></head><body><header class="vh">\n  <div class="logo">L</div>\n  <div>\n    <small>VERITAS INTELLIGENCE ANALYTICS · VRN-2 WORKBENCH</small>\n'
                  '    <h1>VeritasReportNova</h1>\n    <div class="tag">%s</div>\n  </div>\n  <div class="meta">m</div>\n</header>\n'
                  '<main><div class="bar"><button>00</button><select><option>CSV</option></select></div><section class="tabsec"><div class="tag">keep</div>'
                  '<button data-act="extract">x</button></section></main></body></html>') % old_tag
        out, _note = augment110(sample)
        head = lambda x: re.findall(r'<header class="vh">.*?</header>', x, re.S)
        bar = lambda x: re.findall(r'<div class="bar">.*?</div>', x, re.S)
        v100 = HERE / "VRN2_Workbench_v0100.py"
        tpl_ok = (not v100.is_file()) or bool(_TAG_RE.search(v100.read_text(encoding="utf-8")))
        chk("⑦ 頁首第三行 = 「%s」(只換頁首那一處 · 第一 / 二行 · 頁內其他 .tag · 分頁列 .bar 原樣)· 原模板(v0100)的頁首對得上" % TAGLINE,
            len(head(out)) == 1 and head(out)[0].count(TAGLINE) == 1 and old_tag not in out and out.count('<div class="tag">keep</div>') == 1
            and head(out)[0].replace(TAGLINE, old_tag) == head(sample)[0] and bar(out) == bar(sample) and tpl_ok)
        chk("⑤ 重入不重複 · 沒有 03 頁擷取格 / 頁首第三行 → 照出並寫原因", augment110(got)[0] == got and "沒有 03 頁擷取格" in augment110("<html><head><title>x</title></head><body></body></html>")[1]
            and "沒有頁首第三行" in augment110("<html><head><title>x</title></head><body><button data-act=\"extract\">x</button></body></html>")[1]
            and augment110('<html><head><title>x</title></head><body><header class="vh"><div class="tag">a</div></header><button data-act="extract">x</button></body></html>')[1].startswith("同字級"))
    chk("⑥ 腳本:千分位只動兩位小數 · 四位以上整數(顯示)· 左欄小格 → 4 欄矩陣 · 輸出位置 → 路徑 / 同步 / 增量庫 / 累計 / 本輪 · 交接快照 → 項目 / 內容 · 檢視副本走同一套條件 · 自動縮字只往小(卡片 19 → 11 · 按鍵 → 9)",
        "N2 = /^([-+]?)(\\d{4,})(\\.\\d{2})$/" in _DOM and "w10-kv" in _DOM and "w10-of" in _DOM and 'data-w10="ho"' in _DOM and "REPORT_DATE || r.LATEST_REPORT_DATE" in _DOM
        and "MIN_CARD = 11, MIN_BTN = 9" in _DOM and "s -= 0.5" in _DOM and "'important'" in _DOM and all(k in _DOM for k in HO_KEYS))
    n = 7
    print("[%s] %s %s 自測 %s(%d 項)" % ("GREEN" if not fails else "RED", DISPLAY_NAME, VERSION, "全過" if not fails else "不過:%s" % "; ".join(fails), n))
    return 0 if not fails else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv:
        return selftest()
    if argv and argv[0] == "logo":
        return PRIOR.main(argv)
    import argparse
    import os
    ap = argparse.ArgumentParser(prog="VRN2_Workbench_v0110")
    ap.add_argument("verb", nargs="?", default="render")
    ap.add_argument("--root", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--logo", default=None)
    a = ap.parse_args(argv)
    if a.verb != "render":
        return PRIOR.main(argv)
    root = Path(a.root) if a.root else (os.environ.get("VIA_ROOT") and Path(os.environ["VIA_ROOT"])) or HERE.parent.parent
    path = render(root, a.out, a.logo)
    print("[GREEN] %s %s(前版 v0109)· %s" % (DISPLAY_NAME, VERSION, path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
