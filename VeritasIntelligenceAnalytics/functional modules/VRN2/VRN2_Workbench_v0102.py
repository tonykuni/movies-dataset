#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN2_Workbench v0102 — v0101 薄尾(v0101 留著一字不改):操作員 2026-10-29 10:25 貼回後的 U/I 需求。

操作員令(2026-10-29):
  「HEADER 用空格取代底線 · 內容全部靠上對齊 · 數值呈現在 U/I 上都是以百萬台幣為單位 除每股 / 倍數 · 要有千分位號」
  「為何字體常爆出格子不會自動調整自動優化嗎」
  「左邊 VRN-1 GATE 要有一格輸出檔案夾來存長線資料庫 增量維護一律用 PARQUET 儲存」
  「若使用者已有舊的資料庫(CSV / Google Sheet)主動提醒要不要進行資料整合 · 整合成功前千萬不要刪掉原有資料」
  「一定要擷取歷史資料去做數字對齊 至少有一期要對 · 歷史覆蓋預估 · 加減法 / 乘除法檢驗 · 被歷史數據刪掉的部分放刪除區」
  「右面板第一區要有輸入去重矩陣 · 目前引擎狀態」

做法(只增不減 · 前端範本視覺不動 · 後端收據照舊):
  ① 表頭:資料冊分頁的欄名顯示時底線 → 空格(匯出 CSV / JSON 仍用原欄名 · 滑鼠停留看原欄名)。
  ② 對齊:所有 th / td vertical-align: top;長文字格可換行(overflow-wrap)不再撐破;數字格靠右、等寬字。
  ③ 數值:金額欄(VALUE · VALUE_FINAL · VALUE_REPORT · HISTORY_VALUE · RECON_DIFF)依該列 ITEM / TABLE / UNIT_FINAL 判單位
     (bn / 十億 → ×1000 · thousand / 千元 → ÷1000 · mn / 百萬 / 沒標 → 視為百萬)→ 一律以「百萬台幣」顯示 + 千分位;
     每股(EPS / DPS / BVPS / 每股 / 目標價 / 收盤)、倍數(P/E · PBR · EV/EBITDA · 倍 · x)、百分比(% · 率 · margin · ROE…)保留原值 + 千分位;
     滑鼠停留看原值與判到的單位;表頭註明「金額欄 百萬台幣」。瀏覽器端做,輸出冊的值不動。
  ④ 自動縮放:統計磚的大數字 clamp() + 載入 / 改變視窗大小時逐格量 scrollWidth,超出就逐 px 縮到放得進去(最小 11px);長文字格換行。
  ⑤ 左欄(其他系統 Gate 之上)新一格「輸出檔案夾 · 長線資料庫(Parquet 增量)」:目前輸出夾 · 增量庫引擎 / 累計 · 開啟輸出夾 · 選擇 / 取消(vrn2://)·
     舊資料庫整合提示:VRN2_Integrate_latest.json 有候選(CSV / XLSX / Google Sheet 匯出)→ 問「要不要整合?」(vrn2://integrate?apply=1 · 不要 → dismiss=1)· 已整合 → 顯示新檔與 TEMP 原檔位置。
  ⑥ 右欄第一區(統計磚之前):「輸入去重矩陣」(格式 × 唯一 / 完全重複多餘副本 / 候選重複 / 範圍外)+「目前引擎狀態」(本輪收據每一步的燈 · ⑥e 市場擷取 · ⑬b 歷史對齊 · ⑬c 資料整合 · ⑬ 增量庫)。
  ⑧ 表頭雙語(操作員清單):REPORT_DATE → Report Date / 報告日期 … TARGET_PRICE(ADJ) → Adjusted Target Price / 調整後目標價 · <年>_DILUTED_EPS_FACTSET → <年> Diluted EPS (FactSet) / 稀釋每股盈餘 · 不在清單的欄底線 → 空格;原欄名留在 title。
  ⑨ logo:留白從 4% 縮到 1.5%(以 alpha 內容框裁 · 不砍到字)· LANCZOS 高畫質放大 180%(44 → 79 px)· 仍去背透明、無框無特效無底色;頁首高度 88 → 100 px。
  ⑦ 資料冊分頁多兩冊:FinancialAligned(歷史對齊後 · VALUE_FINAL / VALUE_SOURCE / RECON_*)· Deleted(刪除區 · 被歷史數據否定的列 · 帶理由);資料分頁多一塊「歷史對齊」收據表。
動詞同 v0101:render [--root] [--out] [--logo] · logo <來源> <輸出> · --selftest
[VIA:AST-CLASS] 類別 = 前端渲染器(VRN-2 工作台 · 薄尾)· 入口 = ActivateVRN-2 收尾後 / 本檔 CLI
"""
from __future__ import annotations

import html as _html
import importlib.util
import json
import os
import re
import sys
import tempfile
from pathlib import Path

VERSION = "v0102"
DISPLAY_NAME = "VRN2_Workbench"
PRIOR_NAME = "VRN2_Workbench_v0101.py"
HERE = Path(__file__).resolve().parent
NEW_BOOKS = ("FinancialAligned", "Deleted")
NEW_KEYS = {"FinancialAligned": "FILENAME · ITEM · PERIOD · PAGE · TABLE(VALUE_FINAL 歷史優先)", "Deleted": "FILENAME · ITEM · PERIOD(被歷史數據否定 · DELETED_REASON)"}


def _load_prior():
    candidates = [HERE / PRIOR_NAME, HERE.parent / "v144" / "new" / PRIOR_NAME]
    for path in candidates:
        if path.is_file():
            spec = importlib.util.spec_from_file_location("vrn2_workbench_prior_v0101", path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            return module
    raise FileNotFoundError("前版 %s 不在 %s" % (PRIOR_NAME, HERE))


PRIOR = _load_prior()
for _name in dir(PRIOR):
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = getattr(PRIOR, _name)
esc = PRIOR.esc
jread = PRIOR.jread
file_uri = PRIOR.file_uri
pill = PRIOR.pill
LAMP_CLS = PRIOR.LAMP_CLS

# ===== ① ⑦ 資料冊:兩本新冊只在檔案存在時才進分頁(v0101 collect 本來就跳過不存在的冊)=====
PRIOR.BOOKS = tuple(PRIOR.BOOKS) + tuple(b for b in NEW_BOOKS if b not in PRIOR.BOOKS)
PRIOR.KEYS.update(NEW_KEYS)
PRIOR.KEYS["Combined"] = "FILENAME(每份報告一列 · 目標價後接 調整後目標價 · FactSet / YFinance 中位數 · 真實年度 EPS / PER)"
LOGO_MARGIN = 0.015
LOGO_SCALE = 1.8
_native_logo_data_uri = PRIOR.logo_data_uri   # 先存本尊,包裝內只叫本尊(不經 PRIOR 屬性 → 不遞迴)


def logo_data_uri(source: Path, work: Path) -> tuple:
    """v0102:先走 v0101(去背 / 原樣)→ 以 alpha 內容框重裁(留白 1.5% · 不砍到字)→ LANCZOS 放大 180% → data URI。PIL 不在就退回 v0101 的結果。"""
    uri, note = _native_logo_data_uri(source, work)
    try:
        import base64 as _b64
        import io as _io
        from PIL import Image
        raw = _b64.b64decode(uri.split(",", 1)[1])
        im = Image.open(_io.BytesIO(raw)).convert("RGBA")
        r_, g_, b_, a_ = im.split()
        a_ = a_.point(lambda v: 0 if v < 24 else v)   # JPEG 白底的微量雜訊 alpha 歸零(不碰字:字的 alpha 遠高於 24)
        im = Image.merge("RGBA", (r_, g_, b_, a_))
        bbox = a_.getbbox()
        if bbox:
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            pad = max(1, int(round(max(w, h) * LOGO_MARGIN)))
            im = im.crop((max(0, bbox[0] - pad), max(0, bbox[1] - pad), min(im.width, bbox[2] + pad), min(im.height, bbox[3] + pad)))
        im = im.resize((max(1, int(round(im.width * LOGO_SCALE))), max(1, int(round(im.height * LOGO_SCALE)))), Image.LANCZOS)
        buf = _io.BytesIO()
        im.save(buf, format="PNG", optimize=True)
        return "data:image/png;base64," + _b64.b64encode(buf.getvalue()).decode("ascii"), note + " · v0102 留白 1.5%% · LANCZOS 180%% · %dx%d" % (im.width, im.height)
    except Exception as error:  # noqa: BLE001
        return uri, note + " · v0102 重裁略過(%s)" % type(error).__name__


PRIOR.logo_data_uri = logo_data_uri   # v0101 的 render 走它自己 globals 裡的 logo_data_uri

# ===== ② ④ CSS(加在範本與 v0101 之後 · 不改前面任何一行)=====
CSS_V0102 = r"""
/* v0102 操作員 2026-10-29:靠上對齊 · 長字換行不撐破 · 統計磚自動縮放 · 表頭空格 · logo 180% */
:root{--hd:100px}
header.vh .logo.img{width:79px;height:79px}header.vh .logo.img img{width:79px;height:79px}
th,td{vertical-align:top}
td{white-space:normal;overflow-wrap:anywhere;max-width:520px}
td.n{white-space:nowrap;text-align:right;font-variant-numeric:tabular-nums}
td.k{white-space:nowrap}
.stat{display:flex;flex-direction:column;align-items:flex-start;overflow:hidden}
.stat b{font-size:clamp(13px,1.3vw + 8px,24px);white-space:nowrap;max-width:100%;overflow:hidden;text-overflow:clip}
.stat small{white-space:normal;overflow-wrap:anywhere}
.kv{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:8px}
.kv .cell{padding:8px 10px;background:var(--paper2);border:1px solid var(--line);border-radius:7px;min-width:0;overflow:hidden}
.kv .cell small{display:block;font:500 9px "DM Mono",monospace;letter-spacing:.5px;color:var(--mut);text-transform:uppercase}
.kv .cell b{display:block;font:700 12.5px "DM Sans","Noto Sans TC",sans-serif;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.kv .cell .d{font-size:10.5px;color:var(--ink2);white-space:normal;overflow-wrap:anywhere;line-height:1.4}
.lamps{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:4px 10px;font-size:10.5px;line-height:1.35}
.lamps div{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.dedup th,.dedup td{padding:4px 8px;font-size:11px}
.outfolder{border:1px solid var(--line);border-left:3px solid var(--teal);border-radius:0 8px 8px 0;padding:10px;background:var(--paper2);margin-bottom:8px}
.outfolder h3{margin:0 0 6px}
.outfolder .path{font:500 10.5px "DM Mono",monospace;color:var(--ink2);overflow-wrap:anywhere;white-space:normal;line-height:1.4}
.outfolder a.action{margin:4px 0 0;font-size:11px;padding:5px 9px;white-space:normal;text-align:left}
.ask{border:1px solid var(--am);background:rgba(196,148,58,.10);border-radius:8px;padding:9px 11px;margin:6px 0;font-size:11.5px;line-height:1.5}
.ask b{display:block;margin-bottom:4px}
.ask a.action{margin:4px 4px 0 0;display:inline-block;width:auto}
.unitnote{font-size:10.5px;color:var(--mut)}
"""
PRIOR.EXTRA_CSS = PRIOR.EXTRA_CSS + CSS_V0102

# ===== ① ③ ④ JS:只替換 v0101 渲染資料冊的兩個字串 · 加入格式化與縮放函式(其餘前端程式一字不動)=====
JS_V0102 = r"""
  var UNIT_NOTE = ' · 金額欄顯示為百萬台幣(千分位 · 依列 ITEM / TABLE 判原單位 · 沒標視為百萬)· 每股 / 倍數 / % 原值 · 滑鼠停留看原值';
  var HDR = {REPORT_DATE:'Report Date / 報告日期', FILENAME:'File Name / 檔案名稱', TICKER:'Ticker Symbol / 股票代號', YFINANCE_TICKER:'Yahoo Finance Ticker / Yahoo 財經代號', BLOOMBERG_TICKER:'Bloomberg Ticker / 彭博代號', NAME:'Company Name / 公司名稱', ENGLISH_NAME:'English Name / 英文名稱', BROKER:'Broker / 券商', ANALYST:'Analyst / 分析師', EMAIL:'Email / 電郵', TEL:'Tel / 電話', TITLE:'Title / 標題', RATING:'Rating / 評等', TARGET_PRICE:'Target Price / 目標價', 'TARGET_PRICE(ADJ)':'Adjusted Target Price / 調整後目標價', CURRENT_PRICE_REPORT:'Current Price at Report / 報告發布時股價', UPSIDE_PCT:'Upside Percentage / 潛在上漲空間', 'UPSIDE_PCT(ADJ)':'Adjusted Upside Percentage / 調整後潛在上漲空間', ADJ_CLOSE:'Adjusted Close / 調整後收盤價', ADJ_CLOSE_BEFORE_REPORT:'Adjusted Close Before Report / 報告前調整後收盤價', 'TOPIC & SUMMARY':'Topic and Summary / 主題與摘要', STATUS:'Status / 狀態', _STATUS:'Status / 狀態', FACTSET_TARGET_PRICE_MEDIAN:'FactSet Target Price Median / FactSet 目標價中位數', YFINANCE_TARGET_PRICE_MEDIAN:'YFinance Target Price Median / Yahoo 財經目標價中位數', PAGE:'Page / 頁碼', TABLE:'Table / 表格', ITEM:'Item / 科目', PERIOD:'Period / 期間', VALUE:'Value / 數值', VERIFY:'Verify / 驗證', ROW:'Row / 列', SECTION:'Section / 段落', POINT_1:'Point 1 / 重點一', POINT_2:'Point 2 / 重點二', POINT_3:'Point 3 / 重點三', POINT_4:'Point 4 / 重點四', POINTS_OK:'Points OK / 重點數', VALUE_REPORT:'Report Value / 報告值', VALUE_FINAL:'Final Value / 最終值', UNIT_FINAL:'Unit / 單位', VALUE_SOURCE:'Value Source / 值來源', RECON_RATIO:'Recon Ratio / 核對比值', RECON_DIFF:'Recon Diff / 核對差', SCALE:'Scale / 倍率', STD:'Std Item / 標準科目', YEAR:'Year / 年度', KIND:'Kind / 類別', DELETED_REASON:'Deleted Reason / 刪除理由', HISTORY_VALUE:'History Value / 歷史值', UNIT_HISTORY:'History Unit / 歷史單位', BOOK:'Book / 冊', REASON:'Reason / 理由'};
  function hdr(c){ var k = String(c), m; var h = HDR[k]; if (!h && (m = k.match(/^(\d{4})_DILUTED_EPS_FACTSET$/))) h = m[1] + ' Diluted EPS (FactSet) / ' + m[1] + ' 稀釋每股盈餘(FactSet)'; if (!h && (m = k.match(/^(\d{4})_PER_FACTSET$/))) h = m[1] + ' PER (FactSet) / ' + m[1] + ' 本益比(FactSet)'; if (!h) h = k.replace(/_/g, ' '); if (/^(VALUE|VALUE_FINAL|VALUE_REPORT|HISTORY_VALUE)$/.test(k)) h += '(金額欄 百萬台幣)'; return h; }
  function num(v){ if (v == null) return null; var s = String(v).trim(); if (!s) return null; var neg = /^\(.*\)$/.test(s) || /^-/.test(s); s = s.replace(/[(),%\sxX倍]/g, '').replace(/^-/, '').replace(/^NT\$|^TWD|^\$/i, ''); if (!/^\d+(\.\d+)?$/.test(s)) return null; var n = parseFloat(s); return neg ? -n : n; }
  function unitOf(r){ var t = String((r.ITEM || '') + ' ' + (r.TABLE || '') + ' ' + (r.SECTION || '') + ' ' + (r.UNIT_FINAL || '') + ' ' + (r.NOTE || '')); if (/百萬台幣|NT\$ ?mn|NT\$ ?m\b|million|百萬/i.test(t)) return ['百萬', 1]; if (/\bbn\b|billion|十億/i.test(t)) return ['十億', 1000]; if (/thousand|千元|NT\$ ?k\b|'000|仟元/i.test(t)) return ['千元', 0.001]; return ['未標(視為百萬)', 1]; }
  function kindOf(c, r){ if (/^(PAGE|ROW|ROWS|POINTS_OK|SOURCE_ROW|BULLETS|MATCHED_PERIODS)$/.test(c)) return 'int'; if (/_PCT|UPSIDE/.test(c)) return 'pct'; if (/PRICE|CLOSE|_EPS_|^EPS$|DPS/.test(c)) return 'pershare'; if (/^(RECON_RATIO|SCALE)$|_PER_|^PER$|PBR/.test(c)) return 'multiple';
    if (/^(VALUE|VALUE_FINAL|VALUE_REPORT|HISTORY_VALUE|RECON_DIFF)$/.test(c)) { var t = String((r.ITEM || '') + ' ' + (r.UNIT_FINAL || '')); if (/每股|EPS|DPS|BVPS|per share|NT\$\/sh|\(元\)|元\/股/i.test(t)) return 'pershare'; if (/\(x\)|倍|P\/E|\bPER\b|PBR|P\/B|EV\/EBITDA|multiple/i.test(t)) return 'multiple'; if (/%|率|margin|growth|yoy|qoq|ROE|ROA|yield|ratio|\bGM\b|\bOpM\b|\bNM\b/i.test(t)) return 'pct'; return 'money'; } return ''; }
  function fmt(n, d, fixed){ return n.toLocaleString('en-US', {minimumFractionDigits: fixed ? d : 0, maximumFractionDigits: d}); }
  function cell(r, c, ds){ var v = r[c], k = kindOf(c, r), n = num(v), raw = String(v == null ? '' : v);
    if (k === 'money' && n !== null) { var u = unitOf(r); var m = n * u[1]; return '<td class="n" title="原值 ' + hx(raw) + ' · 判到的單位 ' + hx(u[0]) + ' → 百萬台幣">' + hx(fmt(m, Math.abs(m) < 10 ? 2 : 1)) + '</td>'; }
    if (k === 'pershare' && n !== null) return '<td class="n" title="每股 · 原值 ' + hx(raw) + '">' + hx(fmt(n, 2, true)) + '</td>';
    if (k === 'multiple' && n !== null) return '<td class="n" title="倍數 · 原值 ' + hx(raw) + '">' + hx(fmt(n, 2, true)) + (/x|倍/i.test(raw) ? 'x' : '') + '</td>';
    if (k === 'pct' && n !== null) return '<td class="n" title="百分比 · 原值 ' + hx(raw) + '">' + hx(fmt(n, 2)) + (/%/.test(raw) ? '%' : '') + '</td>';
    if (k === 'int' && n !== null) return '<td class="n">' + hx(raw) + '</td>';
    if (k && n === null && raw) return '<td class="n" title="非數值 · 原值照印">' + hx(raw) + '</td>';
    var cl = /POINT_|TITLE|REASON|DETAIL|BULLET|NOTE|DELETED_REASON|VALUE_SOURCE/.test(c) ? ' class="wrap"' : /FILENAME|TICKER|PERIOD|REPORT_DATE/.test(c) ? ' class="k"' : '';
    return '<td' + cl + '>' + hx(raw) + '</td>'; }
  function fitOne(el, min){ el.style.fontSize = ''; el.style.whiteSpace = ''; el.style.overflowWrap = ''; var fs = parseFloat(getComputedStyle(el).fontSize) || 24, guard = 0; while (el.scrollWidth > el.clientWidth + 1 && fs > min && guard++ < 40) { fs -= 1; el.style.fontSize = fs + 'px'; } if (el.scrollWidth > el.clientWidth + 1) { el.style.whiteSpace = 'normal'; el.style.overflowWrap = 'anywhere'; } }
  function fitStats(){ $$('.stat b').forEach(function(el){ fitOne(el, 12); }); $$('.kv .cell b').forEach(function(el){ fitOne(el, 10); }); }
  if (document.fonts && document.fonts.ready) { document.fonts.ready.then(function(){ setTimeout(fitStats, 50); }); }
  var _ft; window.addEventListener('resize', function(){ clearTimeout(_ft); _ft = setTimeout(fitStats, 120); });
"""
_JS = PRIOR.JS
_OLD_TH = "'<th>' + hx(c) + '</th>'"
_NEW_TH = "'<th title=\"' + hx(c) + '\">' + hx(hdr(c)) + '</th>'"
_OLD_TD = ("var tb = page.map(function(r){ return '<tr>' + C.map(function(c){ var v = r[c]; var cl = /PRICE|VALUE|UPSIDE|PAGE|ROWS|BULLETS|EPS|MEAN|CLOSE|_PCT/.test(c) ? ' class=\"n\"' : /POINT_|TITLE|REASON|DETAIL|BULLET/.test(c) ? ' class=\"wrap\"' : ''; "
           "return '<td' + cl + '>' + hx(v) + '</td>'; }).join('') + '</tr>'; }).join('');")
_NEW_TD = "var tb = page.map(function(r){ return '<tr>' + C.map(function(c){ return cell(r, c, st.ds); }).join('') + '</tr>'; }).join('');"
_OLD_META = "$('#dsMeta').textContent = meta;"
_NEW_META = "$('#dsMeta').textContent = meta + UNIT_NOTE;"
_OLD_BOOT = "  setTab('overview'); renderData(); renderX(); selCount();"
_NEW_BOOT = "  setTab('overview'); renderData(); renderX(); selCount(); fitStats(); setTimeout(fitStats, 300);"
for _old, _new in ((_OLD_TH, _NEW_TH), (_OLD_TD, _NEW_TD), (_OLD_META, _NEW_META), (_OLD_BOOT, _NEW_BOOT)):
    if _JS.count(_old) != 1:
        raise RuntimeError("v0101 前端字串找不到(恰一次):%s" % _old[:60])
    _JS = _JS.replace(_old, _new)
_JS = _JS.replace(_NEW_BOOT, JS_V0102.replace("%", "%%") + _NEW_BOOT)   # v0101 的 JS 是 %-格式字串:新段落的 % 要逃脫
PRIOR.JS = _JS


# ===== ⑤ ⑥ ⑦ 新區塊 =====
def _steps(data: dict) -> list:
    close = data.get("closeout") or {}
    act = data.get("activate") or {}
    return [s for s in (close.get("steps") or act.get("steps") or []) if isinstance(s, dict)]


def _step(steps: list, prefix: str) -> dict:
    for s in steps:
        if str(s.get("step", "")).startswith(prefix):
            return s
    return {}


def extra_receipts(root: Path, data: dict) -> dict:
    v2 = data["v2"]
    close = data.get("closeout") or {}
    return {"market": jread(v2 / "market" / "VRN2_Market_latest.json", {}) or {},
            "history": jread(v2 / "VRN2_HistoryAlign_latest.json", {}) or {},
            "integrate": jread(v2 / "VRN2_Integrate_latest.json", {}) or {},
            "market_step": close.get("market") or {}, "history_step": close.get("history_align") or {}, "integrate_step": close.get("integrate") or {}}


def dedup_matrix(files: list, scope: dict) -> str:
    stock = set(scope.get("stock") or [])
    non_stock = set(scope.get("non_stock") or [])
    rows = {}
    seen_sha = set()
    for f in files:
        ext = (f.get("ext") or "?").upper()
        r = rows.setdefault(ext, {"unique": 0, "extra": 0, "candidate": 0, "out": 0, "total": 0})
        r["total"] += 1
        if f.get("exact"):
            if f["sha"] in seen_sha:
                r["extra"] += 1
            else:
                seen_sha.add(f["sha"])
                r["unique"] += 1
        elif f.get("group"):
            r["candidate"] += 1
        else:
            r["unique"] += 1
        if f.get("name") in non_stock or (stock and f.get("name") not in stock and f.get("name") not in non_stock and ext == "PDF"):
            r["out"] += 1
    body = "".join('<tr><td class="k">%s</td><td class="n">%d</td><td class="n">%d</td><td class="n">%d</td><td class="n">%d</td><td class="n">%d</td></tr>' % (esc(k), v["unique"], v["extra"], v["candidate"], v["out"], v["total"]) for k, v in sorted(rows.items()))
    if not body:
        body = '<tr><td colspan="6" class="subtle">scope_in 沒有檔案(先選輸入並跑一輪)</td></tr>'
    tot = {k: sum(v[k] for v in rows.values()) for k in ("unique", "extra", "candidate", "out", "total")}
    foot = '<tr><td class="k"><b>合計</b></td><td class="n"><b>%d</b></td><td class="n"><b>%d</b></td><td class="n"><b>%d</b></td><td class="n"><b>%d</b></td><td class="n"><b>%d</b></td></tr>' % (tot["unique"], tot["extra"], tot["candidate"], tot["out"], tot["total"]) if rows else ""
    return ('<table class="dedup"><thead><tr><th>格式</th><th>唯一</th><th>完全重複 多餘副本</th><th>候選重複</th><th>個股範圍外</th><th>合計</th></tr></thead><tbody>%s%s</tbody></table>' % (body, foot))


def engine_status(data: dict, extra: dict) -> str:
    steps = _steps(data)
    close = data.get("closeout") or {}
    comp = data.get("completion") or {}
    idem = data.get("idem") or {}
    verbatim = data.get("verbatim") or {}
    cells = [
        ("啟動器", close.get("version") or (data.get("activate") or {}).get("version") or "—", {0: "GREEN", 2: "YELLOW"}.get(close.get("rc"), "RED" if close else "GRAY"), "rc %s · %s 秒 · %d 輪" % (close.get("rc", "—"), close.get("elapsed_s", "—"), len(close.get("passes") or [])) if close else "尚未跑過"),
        ("管理器", comp.get("manager") or "—", "GREEN" if comp.get("verdict") == "完成" else ("GRAY" if not comp else "YELLOW"), "完成判定 %s · 紅 %s 黃 %s" % (comp.get("verdict", "—"), comp.get("red", "—"), comp.get("yellow", "—"))),
        ("冪等閘", idem.get("classification") or "—", {"GREEN": "GREEN", "STALE_RECORD": "YELLOW", "NONDETERMINISTIC": "RED"}.get(idem.get("classification"), "GRAY"), (idem.get("method") or "")[:70] or "—"),
        ("四點原文核對", verbatim.get("verdict") or "—", {"PASS": "GREEN", "REVIEW_MISSING": "YELLOW", "REVIEW_OCR": "YELLOW", "FAIL": "RED"}.get(verbatim.get("verdict"), "GRAY"), json.dumps(verbatim.get("counts") or {}, ensure_ascii=False)[:70]),
    ]
    for label, prefix, key in (("⑥e 市場擷取 TWSE / TPEX / Yahoo", "⑥e", "market_step"), ("⑬ 輸出位置 · 增量庫", "⑬ ", "output_store"), ("⑬b 歷史對齊(歷史覆蓋預估)", "⑬b", "history_step"), ("⑬c 舊資料庫整合", "⑬c", "integrate_step"), ("⑤b SSOT-ID 核號同步", "⑤b", "ssot_sync")):
        s = _step(steps, prefix)
        rec = extra.get(key) if key in extra else (close.get(key) or {})
        lamp = s.get("lamp") or (rec or {}).get("lamp") or "GRAY"
        detail = str(s.get("detail") or (rec or {}).get("detail") or (rec or {}).get("why") or "本輪沒有這一步(啟動器版本較舊)")
        cells.append((label, lamp, lamp, detail[:150]))
    kv = "".join('<div class="cell"><small>%s</small><b>%s %s</b><div class="d">%s</div></div>' % (esc(k), pill(l, LAMP_CLS.get(l, "")), esc(v), esc(d)) for k, v, l, d in cells)
    lamps = "".join('<div title="%s">%s%s</div>' % (esc(str(s.get("detail", ""))[:200]), '<span class="lamp %s"></span>' % esc(s.get("lamp", "GRAY")), esc(str(s.get("step", ""))[:28])) for s in steps) or '<div class="subtle">尚無本輪步驟收據</div>'
    return '<div class="kv">%s</div><h3>本輪每一步的燈(%d 步)</h3><div class="lamps">%s</div>' % (kv, len(steps), lamps)


def first_section(data: dict, extra: dict) -> str:
    integ = extra.get("integrate") or {}
    ask = ""
    if integ.get("state") == "PENDING_USER" and integ.get("candidates"):
        ask = ('<div class="ask"><b>偵測到 %d 份舊資料庫(%s)· 要不要進行資料整合?</b>整合會讀取舊檔、自適應對齊欄位後建立<strong>新的</strong>整合 Parquet;原有資料在整合成功前絕不刪除,成功後原檔複製到 TEMP(%s)由你自行處理。'
               '<a class="action primary" href="vrn2://integrate?apply=1">✔ 要,建立整合檔</a><a class="action" href="vrn2://integrate?dismiss=1">✖ 不要,這輪跳過</a><a class="action" href="vrn2://integrate?scan=1">↻ 重新掃描</a></div>'
               % (len(integ["candidates"]), esc(" · ".join(sorted({str(c.get("kind", "")) for c in integ["candidates"]})) or "CSV / XLSX"), esc(integ.get("temp_dir") or "%TEMP%\\VRN2_Integrate")))
    return ('<div class="box" id="first"><h2>輸入去重矩陣 · 目前引擎狀態</h2>%s<div class="split"><div><h3>輸入去重矩陣(scope_in · SHA-256 完全重複 / 大小 + 時間候選)</h3>%s</div><div><h3>目前引擎狀態(本輪收據)</h3>%s</div></div></div>'
            % (ask, dedup_matrix(data.get("files") or [], data.get("scope") or {}), engine_status(data, extra)))


def outfolder_block(data: dict, extra: dict) -> str:
    ocfg = data.get("outcfg") or {}
    store = data.get("store") or {}
    out_dir = ocfg.get("output_dir") or ""
    totals = store.get("totals") or {}
    integ = extra.get("integrate") or {}
    h = ['<div class="outfolder" id="outfolder"><h3>輸出檔案夾 · 長線資料庫(Parquet 增量維護)</h3>']
    if out_dir:
        h.append('<div class="path">%s<br><span class="subtle">%s · %s</span></div>' % (esc(out_dir), esc(ocfg.get("cloud_hint", "")), esc(ocfg.get("how", ""))))
        h.append('<div class="subtle">增量庫 %s · 累計 %s · 新檔 %d / 已知 %d(本輪)</div>' % (esc(store.get("store_engine") or "—"), esc(" / ".join("%s %s" % (k, v) for k, v in totals.items()) or "—"), len(store.get("new_files") or []), len(store.get("known_files") or [])))
        h.append('<a class="action" href="%s" target="_blank">📂 開啟輸出夾(VRN2\\latest · parquet\\)</a>' % esc(file_uri(out_dir)))
        h.append('<a class="action" href="vrn2://pick?kind=outdir">📤 換輸出夾…</a><a class="action" href="vrn2://outdir?reset=1">↩ 取消(回 VIA_Reports\\vrn2\\output)</a>')
    else:
        h.append('<div class="subtle">未設定 · 輸出留在 VIA_Reports\\vrn2\\output;設定後每輪收尾鏡像四本冊 + 增量 Parquet 庫(DuckDB · 以原檔 SHA-256 判新舊)到那裡</div>')
        h.append('<a class="action primary" href="vrn2://pick?kind=outdir">📤 選擇輸出夾…(Windows 對話框 · 本機 / OneDrive / Google Drive)</a>')
    st = integ.get("state")
    if st == "PENDING_USER" and integ.get("candidates"):
        h.append('<div class="ask"><b>舊資料庫 %d 份待決定</b>%s<a class="action primary" href="vrn2://integrate?apply=1">✔ 整合</a><a class="action" href="vrn2://integrate?dismiss=1">✖ 不要</a></div>'
                 % (len(integ["candidates"]), esc("、".join(Path(str(c.get("path", ""))).name for c in integ["candidates"][:3]) + (" …" if len(integ["candidates"]) > 3 else ""))))
    elif st == "APPLIED":
        h.append('<div class="subtle">已整合 %d 份 → %s<br>原檔已複製到 TEMP:%s(原位置未刪)</div>' % (len(integ.get("applied") or []), esc(integ.get("integrated_dir") or "—"), esc(integ.get("temp_dir") or "—")))
    elif st == "DISMISSED":
        h.append('<div class="subtle">舊資料庫整合:使用者本輪跳過 · <a href="vrn2://integrate?scan=1">重新掃描</a></div>')
    else:
        h.append('<div class="subtle">舊資料庫整合:%s · <a href="vrn2://integrate?scan=1">掃描 CSV / XLSX / Google Sheet 匯出</a></div>' % esc(integ.get("why") or "尚未掃描"))
    h.append("</div>")
    return "".join(h)


def history_block(data: dict, extra: dict) -> str:
    hist = extra.get("history") or {}
    market = extra.get("market") or {}
    files = hist.get("files") or {}
    rows = []
    for name, f in sorted(files.items()):
        rows.append('<tr><td class="k">%s</td><td class="n">%s</td><td class="n">%s</td><td class="n">%s</td><td class="n">%s</td><td class="n">%s</td><td class="lampcell">%s %s</td></tr>' % (
            esc(name), esc(f.get("matched_periods", 0)), esc(f.get("scale_label", "—")), esc(f.get("overrides", 0)), esc(f.get("deleted", 0)), esc(f.get("checks_pass", "—")), '<span class="lamp %s"></span>' % esc(f.get("lamp", "GRAY")), esc(str(f.get("why", ""))[:160])))
    body = "".join(rows) or '<tr><td colspan="7" class="subtle">%s</td></tr>' % esc(hist.get("why") or ("尚未跑歷史對齊(⑬b)" if not market else "市場資料有了,但 ⑬b 還沒跑"))
    totals = hist.get("totals") or {}
    head = ('<div class="toolbar"><span class="pill %s">歷史對齊 %s</span><span class="subtle">規則:每份至少一期(年度)報告值與 TWSE / MOPS 歷史對上(比值 0.97 ~ 1.03 · 單位自動對)才覆蓋;歷史覆蓋預估、報告值保留在 VALUE_REPORT;加減法(毛利 = 營收 − 成本 · 稅前 − 稅 = 稅後)與乘除法(淨利率 · ROE · EPS × 股數)檢驗;被歷史數據否定的列進刪除區 Deleted。'
            '合計:對上 %s 份 · 沒對上 %s 份 · 覆蓋 %s 格 · 刪除區 %s 列 · 市場資料 %s</span></div>'
            % (LAMP_CLS.get(hist.get("lamp", "GRAY"), "gray"), esc(hist.get("lamp", "尚未")), esc(totals.get("files_matched", "—")), esc(totals.get("files_unmatched", "—")), esc(totals.get("overrides", "—")), esc(totals.get("deleted", "—")), esc((market.get("ts") or "無")[:19])))
    return ('<div class="box"><h2>歷史對齊 · 歷史覆蓋預估(⑬b)</h2>%s<div class="matrix"><table><thead><tr><th>檔案</th><th>對上期數</th><th>單位倍率</th><th>覆蓋格</th><th>刪除區</th><th>檢驗通過</th><th>燈 / 說明</th></tr></thead><tbody>%s</tbody></table></div></div>' % (head, body))


# ===== render:v0101 渲染 → 插三塊(左欄輸出夾 · 右欄第一區 · 資料分頁歷史對齊)=====
_ANCHOR_GATE = "      <h3>其他系統 Gate</h3>"
_ANCHOR_FIRST = '    <section class="tabsec on" data-tab="overview">\n'
_ANCHOR_POLICY = '      <div class="box">\n        <h2>資料正確性政策</h2>'


def render(root: Path, out_path: Path | None = None, logo: str | None = None, assets_zip: Path | None = None) -> Path:
    root = Path(root).resolve()
    out = PRIOR.render(root, out_path, logo, assets_zip)
    page = Path(out).read_text(encoding="utf-8")
    data = PRIOR.collect(root)
    extra = extra_receipts(root, data)
    for anchor, block, where in ((_ANCHOR_GATE, outfolder_block(data, extra), "before"), (_ANCHOR_FIRST, first_section(data, extra), "after"), (_ANCHOR_POLICY, history_block(data, extra), "before")):
        if page.count(anchor) != 1:
            raise RuntimeError("v0101 頁面錨點找不到(恰一次):%s" % anchor.strip()[:40])
        page = page.replace(anchor, (block + "\n" + anchor) if where == "before" else (anchor + block + "\n"))
    page = page.replace("<title>VRN-2 Workbench</title>", "<title>VRN-2 Workbench</title><!-- VRN2_Workbench %s over v0101 -->" % VERSION, 1)
    tmp = Path(out).with_suffix(".tmp")
    tmp.write_text(page, encoding="utf-8")
    tmp.replace(Path(out))
    return Path(out)


# ===== selftest =====
def _fixture_v0102(root: Path) -> None:
    PRIOR._fixture(root)
    v2 = root / "VIA_Reports" / "vrn2"
    out = v2 / "output"
    (v2 / "market").mkdir(parents=True, exist_ok=True)
    json.dump({"version": "v0112", "ts": "2026-10-29T12:00:00", "per_file": {"A-2330 20260101.pdf": {"ticker": "2330", "adj_close": 1000.5, "financial_annual": [{"year": 2025, "std": "revenue", "value": 2894307699.0, "unit": "千元", "basis": "ANNUAL"}]}}}, open(v2 / "market" / "VRN2_Market_latest.json", "w", encoding="utf-8"), ensure_ascii=False)
    json.dump({"lamp": "YELLOW", "files": {"A-2330 20260101.pdf": {"lamp": "GREEN", "matched_periods": 1, "scale_label": "×1(百萬)", "overrides": 3, "deleted": 1, "checks_pass": "4/5", "why": "2025A 營收 2,894,308 對 MOPS 2,894,307.7"},
              "B-2454 20260102.pdf": {"lamp": "YELLOW", "matched_periods": 0, "scale_label": "—", "overrides": 0, "deleted": 0, "checks_pass": "—", "why": "沒有一期對上 · 不覆蓋"}},
              "totals": {"files_matched": 1, "files_unmatched": 1, "overrides": 3, "deleted": 1}}, open(v2 / "VRN2_HistoryAlign_latest.json", "w", encoding="utf-8"), ensure_ascii=False)
    json.dump({"state": "PENDING_USER", "temp_dir": "C:\\Users\\x\\AppData\\Local\\Temp\\VRN2_Integrate", "candidates": [{"path": "C:\\old\\舊資料庫.csv", "kind": "CSV", "rows": 120, "target_book": "FinancialData"}, {"path": "C:\\old\\Sheet1.csv", "kind": "Google Sheet 匯出 CSV", "rows": 9, "target_book": "BasicInfo"}]},
              open(v2 / "VRN2_Integrate_latest.json", "w", encoding="utf-8"), ensure_ascii=False)
    aligned = [{"REPORT_DATE": "2026-01-01", "FILENAME": "A-2330 20260101.pdf", "TICKER": "2330", "ITEM": "Revenue (NT$ bn)", "PERIOD": "2025A", "VALUE_REPORT": "2,894.3", "VALUE_FINAL": 2894307.699, "UNIT_FINAL": "百萬台幣", "VALUE_SOURCE": "HISTORY(MOPS)", "RECON_DIFF": -0.001, "RECON_RATIO": 1.0, "SCALE": 1000, "PAGE": 3}]
    deleted = [{"REPORT_DATE": "2026-01-01", "FILENAME": "A-2330 20260101.pdf", "TICKER": "2330", "ITEM": "Net income", "PERIOD": "2025A", "VALUE": "9,999", "HISTORY_VALUE": 1173268.0, "DELETED_REASON": "與歷史數據差 > 3%(比值 0.0085)", "PAGE": 3}]
    json.dump(aligned, open(out / "VRN2_FinancialAligned_latest.json", "w", encoding="utf-8"), ensure_ascii=False)
    json.dump(deleted, open(out / "VRN2_Deleted_latest.json", "w", encoding="utf-8"), ensure_ascii=False)
    (out / "VRN2_FinancialAligned_latest.parquet").write_bytes(b"PAR1")
    json.dump({"output_dir": "C:\\Users\\x\\OneDrive\\VRN2_out", "how": "U/I 選的", "ts": "2026-10-29T10:00:00", "cloud_hint": "OneDrive 同步夾"}, open(v2 / "VRN2_Output_Config.json", "w", encoding="utf-8"), ensure_ascii=False)
    json.dump({"lamp": "GREEN", "store_engine": "duckdb", "totals": {"BasicInfo": 52, "FinancialData": 10908}, "new_files": [], "known_files": ["a", "b"]}, open(v2 / "VRN2_OutputStore_latest.json", "w", encoding="utf-8"), ensure_ascii=False)
    close = json.load(open(v2 / "VRN2_Closeout_v0142.json", encoding="utf-8"))
    close["steps"] += [{"step": "⑥e 市場擷取(TWSE / TPEX / Yahoo · 借共用 MarketFetch)", "lamp": "GREEN", "detail": "代號 2 · 完整 1 · 部分 1"}, {"step": "⑬ 輸出位置 · 增量庫(DuckDB)", "lamp": "GREEN", "detail": "duckdb · 新檔 0 / 已知 2"},
                       {"step": "⑬b 歷史對齊", "lamp": "YELLOW", "detail": "對上 1 / 2 份"}, {"step": "⑬c 舊資料庫整合掃描", "lamp": "YELLOW", "detail": "候選 2 份 · 等使用者決定"}]
    json.dump(close, open(v2 / "VRN2_Closeout_v0146.json", "w", encoding="utf-8"), ensure_ascii=False)


def selftest() -> int:
    bad = []

    def chk(label, cond):
        print(("[PASS] " if cond else "[FAIL] ") + label)
        if not cond:
            bad.append(label)

    chk("⓪ 薄尾:前版 v0101 載入 · 前端字串四處已替換 · 兩本新冊進 BOOKS", PRIOR.VERSION == "v0101" and "hdr(c)" in PRIOR.JS and "cell(r, c, st.ds)" in PRIOR.JS and "UNIT_NOTE" in PRIOR.JS and "fitStats()" in PRIOR.JS and "FinancialAligned" in PRIOR.BOOKS and "Deleted" in PRIOR.BOOKS)
    with tempfile.TemporaryDirectory(prefix="vrn2-wb102-") as td:
        root = Path(td)
        _fixture_v0102(root)
        page = render(root)
        h = page.read_text(encoding="utf-8")
        chk("① 表頭空格:JS hdr() 把底線換空格 · 金額欄註明百萬台幣 · 原欄名留在 title", "replace(/_/g, ' ')" in h and "(金額欄 百萬台幣)" in h and "'<th title=\"' + hx(c) + '\">' + hx(hdr(c))" in h)
        chk("② 靠上對齊 CSS · 長字換行 · 數字格靠右等寬", "th,td{vertical-align:top}" in h and "td{white-space:normal;overflow-wrap:anywhere" in h and "td.n{white-space:nowrap;text-align:right" in h)
        chk("③ 數值:cell() 依 ITEM / TABLE 判單位 → 百萬台幣千分位 · 每股 / 倍數 / % 原值 · 滑鼠停留看原值", "function unitOf(r)" in h and "function kindOf(c, r)" in h and "toLocaleString('en-US'" in h and "判到的單位" in h and "每股 · 原值" in h)
        chk("④ 自動縮放:clamp + fitOne 逐 px 縮(最小 12px 仍不夠就換行)· resize / 字型載入後重算", "font-size:clamp(13px,1.3vw + 8px,24px)" in h and "function fitOne(el, min)" in h and "el.style.whiteSpace = 'normal'; el.style.overflowWrap = 'anywhere';" in h and "addEventListener('resize'" in h and "document.fonts.ready" in h and "fitStats(); setTimeout(fitStats, 300);" in h)
        gate_i, outf_i = h.index("<h3>其他系統 Gate</h3>"), h.index('id="outfolder"')
        chk("⑤ 左欄輸出檔案夾在其他系統 Gate 之上:目前輸出夾 · OneDrive · duckdb 累計 · 開啟 / 換 / 取消 · 舊資料庫 2 份待決定(整合 / 不要)", outf_i < gate_i and "C:\\Users\\x\\OneDrive\\VRN2_out" in h and "增量庫 duckdb · 累計 BasicInfo 52 / FinancialData 10908" in h and 'href="vrn2://pick?kind=outdir">📤 換輸出夾' in h and "舊資料庫 2 份待決定" in h and 'href="vrn2://integrate?apply=1"' in h and 'href="vrn2://integrate?dismiss=1"' in h)
        first_i, stats_i = h.index('id="first"'), h.index('<div class="stats">')
        chk("⑥ 右欄第一區在統計磚之前:去重矩陣(PDF 唯一 2 · 多餘副本 1 · 合計 3)· 引擎狀態含 ⑥e / ⑬ / ⑬b / ⑬c / ⑤b · 每一步的燈", first_i < stats_i and '<td class="k">PDF</td><td class="n">2</td><td class="n">1</td><td class="n">0</td>' in h and "⑥e 市場擷取 TWSE / TPEX / Yahoo" in h and "⑬b 歷史對齊(歷史覆蓋預估)" in h and "⑬c 舊資料庫整合" in h and "候選 2 份 · 等使用者決定" in h and "本輪每一步的燈(" in h)
        chk("⑥b 整合提問在第一區最上面:偵測到 2 份舊資料庫 · 整合成功前絕不刪除 · TEMP", "偵測到 2 份舊資料庫(CSV · Google Sheet 匯出 CSV)· 要不要進行資料整合?" in h and "原有資料在整合成功前絕不刪除" in h and "Temp\\VRN2_Integrate" in h)
        chk("⑦ 資料冊多 FinancialAligned / Deleted · 歷史對齊表(對上 1 · 沒對上 1 · 覆蓋 3 · 刪除區 1 · B 檔黃「沒有一期對上」)", '"FinancialAligned"' in h and '"Deleted"' in h and '"VALUE_SOURCE": "HISTORY(MOPS)"' in h and "歷史對齊 · 歷史覆蓋預估(⑬b)" in h and "對上 1 份 · 沒對上 1 份 · 覆蓋 3 格 · 刪除區 1 列" in h and "沒有一期對上 · 不覆蓋" in h and h.index("歷史對齊 · 歷史覆蓋預估") < h.index("<h2>資料正確性政策</h2>"))
        chk("⑧ v0101 的東西都還在:四分頁 · vrn2:// 動作 · Gate · 矩陣一 / 二 · 沒有殘留 {{ }}", h.count('data-act="tab"') == 4 and "vrn2://run\"" in h and "VDF Gate" in h and "矩陣一 · 輸入清單與去重審查" in h and "矩陣二 · 引擎與輸入" in h and "{{" not in h and "VRN2_Workbench v0102 over v0101" in h)
        h2 = render(root).read_text(encoding="utf-8")
        strip = lambda s: re.sub(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2})?", "", s)  # noqa: E731
        chk("⑨ 冪等:同輸入再渲染除時間戳外逐字相同", strip(h) == strip(h2))
        from html.parser import HTMLParser

        class P(HTMLParser):
            n = 0

            def handle_starttag(self, tag, attrs):
                self.n += 1
        p = P(); p.feed(h)
        chk("⑩ HTML 可解析(標籤 > 300)", p.n > 300)
        import shutil
        for name in ("VRN2_HistoryAlign_latest.json", "VRN2_Integrate_latest.json", "VRN2_Output_Config.json", "VRN2_OutputStore_latest.json", "VRN2_Closeout_v0146.json"):
            (root / "VIA_Reports" / "vrn2" / name).unlink()
        shutil.rmtree(root / "VIA_Reports" / "vrn2" / "market")
        h3 = render(root).read_text(encoding="utf-8")
        chk("⑪ 沒有新收據也能渲染:未設定輸出夾 · 尚未掃描 · 尚未跑歷史對齊 · 引擎狀態灰「本輪沒有這一步」", "未設定 · 輸出留在" in h3 and "尚未掃描" in h3 and "尚未跑歷史對齊(⑬b)" in h3 and "本輪沒有這一步" in h3 and 'id="first"' in h3)
        chk("⑫ 表頭雙語表:Report Date / 報告日期 · Adjusted Target Price / 調整後目標價 · Topic and Summary / 主題與摘要 · 年度 EPS / PER 以真實年份組字 · --hd 100px · logo 79px", "REPORT_DATE:'Report Date / 報告日期'" in h3 and "'TARGET_PRICE(ADJ)':'Adjusted Target Price / 調整後目標價'" in h3 and "'TOPIC & SUMMARY':'Topic and Summary / 主題與摘要'" in h3 and "Diluted EPS (FactSet) / " in h3 and ":root{--hd:100px}" in h3 and "header.vh .logo.img{width:79px;height:79px}" in h3)
        try:
            from PIL import Image
            import base64 as _b64
            import io as _io
            src = root / "VRN2_Logo.jpg"
            im = Image.new("RGB", (200, 120), (255, 255, 255))
            for x in range(60, 140):
                for y in range(30, 90):
                    im.putpixel((x, y), (180, 20, 20))
            im.save(src, "JPEG", quality=95)
            h5 = render(root, logo=str(src)).read_text(encoding="utf-8")
            data = re.search(r'<div class="logo img"><img src="data:image/png;base64,([^"]+)"', h5).group(1)
            out = Image.open(_io.BytesIO(_b64.b64decode(data))).convert("RGBA")
            bbox = out.split()[3].getbbox()
            margin_l, margin_t = bbox[0], bbox[1]
            chk("⑬ logo:去背透明 · 內容框留白 ≤ 3%%(左 %d 上 %d px of %dx%d)· 放大 180%% 後比 v0101 的 4%% 裁切大(寬 ≥ 140)· 角落透明 · 中心仍紅" % (margin_l, margin_t, out.width, out.height), out.getpixel((0, 0))[3] == 0 and out.getpixel((out.width // 2, out.height // 2))[3] == 255 and out.getpixel((out.width // 2, out.height // 2))[0] > 150 and margin_l <= max(2, int(out.width * 0.03)) and margin_t <= max(2, int(out.height * 0.03)) and out.width >= 140)
        except ImportError:
            print("[SKIP] ⑬ logo 重裁:沒有 PIL")
    print("[%s] %s %s --selftest · %d 項 · 不過 %d" % ("PASS" if not bad else "FAIL", DISPLAY_NAME, VERSION, 13, len(bad)))
    return 0 if not bad else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv:
        return selftest()
    if argv and argv[0] == "logo":
        return PRIOR.main(argv)
    import argparse
    ap = argparse.ArgumentParser(prog="VRN2_Workbench_v0102")
    ap.add_argument("verb", nargs="?", default="render")
    ap.add_argument("--root", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--logo", default=None)
    a = ap.parse_args(argv)
    if a.verb != "render":
        return PRIOR.main(argv)
    root = Path(a.root) if a.root else (os.environ.get("VIA_ROOT") and Path(os.environ["VIA_ROOT"])) or HERE.parent.parent
    path = render(root, a.out, a.logo)
    print("[GREEN] %s %s · %s" % (DISPLAY_NAME, VERSION, path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
