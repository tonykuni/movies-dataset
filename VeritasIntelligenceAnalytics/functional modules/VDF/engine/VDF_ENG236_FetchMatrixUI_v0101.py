#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG236_FetchMatrixUI v0101 — 薄尾(v0100 留著一字不改):VeritasReportNova Workbench 範本(模板冊 v0104)· 印章頁首 · DataFrame 表頭欄

操作員 2026-11-01:「taiwan_stock_data_matrix.html 顯現部分資料擷取的端點來源 但並未顯示 DATAFRAME HEADERS」
  「VRN-2 完成上述工作後 … 完成後開始針對 VDF / VCGC CLOSE OUT · 擁有相同的 U/I 模板視覺或動畫視覺鎖定 · 功能全面完成 ·
   印章 logo 為透明去背無框無特效 · 以紅字大小為依據跟 header 文字做 header 大小 logo 最佳化調節加入」。
做法(只增不減 · v0100 的模型 / 版面 / 規格冊 VDF_UI_VisualSpec_SSOT_v0100 / 舊頁籤一字不改 · 只在頁尾追加一段範本覆蓋):
  ① 擷取矩陣頁多一欄「表頭 / DataFrame Headers」(在庫況之前):欄名 = VDF 自己的取資料引擎 ENG237 尾版 list_tables()(唯讀 ATTACH · information_schema.columns ·
     家照 ENG237 resolve_home)讀到的真實欄;讀到就存 VIA_Reports/vdf/FETCH_MATRIX_columns_latest.json(下次庫被佔用 / 沒 duckdb 時沿用 · 標「快取 時間」);
     都沒有 → 那格寫「未讀到(原因)」不猜;冊上已有的欄(v0100 的 columns)照用。矩陣格顯示前 10 欄、其餘「+N 欄」· 點列明細列出全部欄。
  ② 印章頁首:擷取矩陣頁 .hdr 左邊加印章;VDF 操作頁 VDF_UI_latest.html(經 apply_spec,v0165 起每頁都會呼叫)的 <header> 換成範本頁首
     (大寫等寬小字 systems.VDF.caps → h1 systems.VDF.title → 原頁首說明 / 燈號圖例原樣)· 主印框高 = 文字區塊高(實量 · 44 ~ 120px · 小印垂右下)·
     印章 / 字型取模板冊尾版 assets(共用資產 · 雜湊鎖 · 對不上就不嵌 · 照實)。
  ③ 視覺:顏色 / 字型 / 字級階層 = 模板冊尾版 tokens + systems.VDF(VRN Workbench 範本);追加段放在 </body> 前(頁首那段 v0100 規格與 bridge 不動 · 冪等換新)。
動詞同 v0100:build [--out 夾] [--db-check DB_CHECK.json] [--json] · --selftest
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0111] SuperAccel 加速器橋(graceful 零行為變更) =====
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(graceful 零行為變更 · 本檔零網路) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None

import base64
import datetime
import hashlib
import html
import importlib.util
import json
import re
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TAG = "VDF_ENG236_FetchMatrixUI v0101"
PRIOR_NAME = "VDF_ENG236_FetchMatrixUI_v0100.py"
_sp = importlib.util.spec_from_file_location("vdf_eng236_prior_for_v0101", HERE / PRIOR_NAME)
PRIOR = importlib.util.module_from_spec(_sp)
sys.modules[_sp.name] = PRIOR
_sp.loader.exec_module(PRIOR)
for _n in dir(PRIOR):
    if not _n.startswith("__") and _n not in globals():
        globals()[_n] = getattr(PRIOR, _n)
VIA, VDF = PRIOR.VIA, PRIOR.VDF
ASSET_DIR = "via_ui_assets"
COLS_CACHE = "FETCH_MATRIX_columns_latest.json"
MARK = "<!-- VDF_ENG236 v0101 workbench header -->"
WB_ID = "via-wb-vdf-v0101"
SHOW_N = 10


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _e(s) -> str:
    return html.escape("" if s is None else str(s), quote=True)


# ---------------------------------------------------------------- 模板冊(共用 · 只讀)
def template(via: Path | None = None) -> dict:
    """模板冊尾版 tokens + systems.VDF + assets(印章 · 字型 · 雜湊鎖)。讀不到 → ok False(照 v0100)。"""
    via = Path(via or VIA)
    reg = via / "supportive modules" / "registry"
    hits = sorted(reg.glob("VIA_UI_Template_SSOT_v*.json"), key=PRIOR._vnum) if reg.is_dir() else []
    out = {"ok": False, "book": hits[-1].name if hits else None, "tokens": {}, "caps": "", "title": "", "seal_uri": "", "main_frac": 1.0, "fonts_zip": None, "why": None}
    if not hits:
        out["why"] = "找不到 VIA_UI_Template_SSOT_v*.json"
        return out
    try:
        d = json.loads(hits[-1].read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        out["why"] = "讀不了 %s:%s" % (hits[-1].name, type(exc).__name__)
        return out
    sysd = (d.get("systems") or {}).get("VDF") or {}
    toks = dict(d.get("tokens") or {})
    toks.update({k: v for k, v in sysd.items() if isinstance(v, str) and k in toks})
    for k in d.get("locked") or []:
        toks[k] = (d.get("tokens") or {}).get(k, toks.get(k))
    out.update({"tokens": toks, "caps": str(sysd.get("caps") or "VERITAS INTELLIGENCE ANALYTICS · VERITAS DATA FORGE · VDF"), "title": str(sysd.get("title") or "Veritas Data Forge")})
    why = []
    a = d.get("assets") or {}
    seal, fonts = a.get("seal") or {}, a.get("fonts") or {}
    sp, fp = via / str(seal.get("file") or "-"), via / str(fonts.get("file") or "-")
    if seal and sp.is_file() and _sha(sp.read_bytes()) == seal.get("sha256"):
        out["seal_uri"] = "data:image/png;base64," + base64.b64encode(sp.read_bytes()).decode("ascii")
        out["main_frac"] = float(seal.get("main_frac") or 1.0)
    else:
        why.append("印章 %s" % ("冊沒有 assets.seal" if not seal else ("檔不在" if not sp.is_file() else "雜湊對不上")))
    if fonts and fp.is_file() and _sha(fp.read_bytes()) == fonts.get("sha256"):
        out["fonts_zip"] = fp
    else:
        why.append("字型 %s" % ("冊沒有 assets.fonts" if not fonts else ("檔不在" if not fp.is_file() else "雜湊對不上")))
    out["ok"] = bool(toks.get("bg"))
    out["why"] = ";".join(why) or None
    return out


def fonts_place(out_dir: Path, fonts_zip) -> bool:
    if not fonts_zip:
        return False
    target = Path(out_dir) / ASSET_DIR
    stamp, want = target / ".sha256", _sha(Path(fonts_zip).read_bytes())
    if stamp.is_file() and stamp.read_text(encoding="utf-8").strip() == want and (target / "fonts.css").is_file():
        return True
    target.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(fonts_zip) as z:
        for n in z.namelist():
            if n.endswith("/") or ".." in n or n.startswith("/"):
                continue
            (target / n).parent.mkdir(parents=True, exist_ok=True)
            (target / n).write_bytes(z.read(n))
    stamp.write_text(want + "\n", encoding="utf-8")
    return (target / "fonts.css").is_file()


def wb_css(t: dict) -> str:
    k = dict({"bg": "#f5f4f0", "panel": "#ffffff", "line": "#dbd9d3", "txt": "#1e1d1a", "dim": "#6b6a66", "chip": "#faf9f6", "soft": "#eceae2", "mut2": "#9c9890", "ink2": "#44423c",
              "seal": "#b5291a", "am": "#c4943a", "blue": "#4c78a8", "teal": "#439a9a", "font": '"DM Sans","Noto Sans TC",sans-serif', "mono": '"DM Mono","Noto Sans TC",monospace',
              "serif": '"Syne","DM Sans",sans-serif'}, **{x: y for x, y in (t or {}).items() if isinstance(y, str)})
    k = {x: re.sub(r"[<>{};\\]", "", str(y)) for x, y in k.items()}
    return """:root{--bg:%(bg)s;--surface:%(panel)s;--border:%(soft)s;--border2:%(line)s;--panel:%(chip)s;--th:%(chip)s;--text:%(txt)s;--muted:%(dim)s;--dim:%(mut2)s;--mono:%(mono)s;--sans:%(font)s}
body{font-family:%(font)s;background:%(bg)s;color:%(txt)s}
.hdr{align-items:center;gap:20px;border-bottom:1px solid %(line)s}
.hdr .via-seal{height:var(--seal-main,72px);flex:none;display:block;overflow:visible}
.hdr .via-seal img,header.via-wb .via-seal img{height:var(--seal-full,80px);width:auto;display:block;border:none;box-shadow:none;filter:none;background:transparent}
.hdr-badge{font:500 10px %(mono)s;letter-spacing:.14em;text-transform:uppercase;color:%(seal)s;background:rgba(181,41,26,.06);border:1px solid rgba(181,41,26,.22);padding:3px 8px;border-radius:3px}
.hdr h1{font:800 22px/1.2 %(serif)s;letter-spacing:-.01em;margin:4px 0 2px}
.hdr-sub{font:400 11px %(mono)s;color:%(dim)s}
.stat-n{font:500 20px/1 %(mono)s}.stat-l{font-size:11px;color:%(dim)s}
.leg{font:500 11.5px %(font)s;transition:all .18s}.leg.active{background:%(chip)s;border-color:%(line)s;color:%(txt)s}
.section-title{font:500 10px %(mono)s;letter-spacing:.12em;text-transform:uppercase;color:%(mut2)s}
.matrix{grid-template-columns:minmax(170px,1.1fr) minmax(120px,.8fr) minmax(150px,1fr) minmax(220px,1.6fr) 92px;border:1px solid %(line)s;border-radius:8px;background:%(panel)s}
.col-hdr{font:500 10px %(mono)s;letter-spacing:.1em;text-transform:uppercase;color:%(mut2)s;background:%(chip)s;border-bottom:1px solid %(line)s}
.row>.cell{border-bottom:1px solid %(soft)s;transition:background .15s}.row:hover>.cell{background:%(soft)s}
.cell-label{font:500 13px/1.3 %(font)s;color:%(txt)s}.cell-sub,.cell-db{font-family:%(mono)s}
.hs{display:flex;flex-wrap:wrap;gap:4px}.hs .h{font:500 10px/1 %(mono)s;color:%(ink2)s;background:%(chip)s;border:1px solid %(line)s;border-radius:3px;padding:3px 6px;white-space:nowrap}
.hs .h.more{color:%(dim)s;border-style:dashed}.hs-note{font:400 10px %(mono)s;color:%(mut2)s;margin-top:4px}
.detail-panel.open{animation:viaDown .2s ease}@keyframes viaDown{from{opacity:0;transform:translateY(-6px)}to{opacity:1;transform:none}}
.sum-card{border-color:%(line)s}.sum-n{font:500 22px/1 %(mono)s}
header.via-wb{display:flex;align-items:center;gap:14px;padding:10px 20px;min-height:100px;flex-wrap:wrap;position:relative;background:%(panel)s;border-bottom:1px solid %(line)s}
header.via-wb::after{content:"";position:absolute;left:0;right:0;bottom:-1px;height:4px;background:linear-gradient(90deg,%(seal)s,%(am)s,%(blue)s,%(teal)s)}
header.via-wb .via-seal{height:var(--seal-main,56px);flex:none;display:block;overflow:visible}
header.via-wb .via-hdtxt{min-width:0;flex:1}
header.via-wb small{display:block;font:700 10px %(mono)s;letter-spacing:2px;text-transform:uppercase;color:%(dim)s}
header.via-wb h1{font:800 20px %(serif)s;margin:1px 0 2px;color:%(txt)s}
header.via-wb .via-tag{font-size:12px;color:%(dim)s;overflow-wrap:anywhere}
@media(max-width:640px){.matrix{grid-template-columns:minmax(0,1fr)}}
""" % k


JS_FIT = """<script id="via-seal-fit-vdf-v0101">(function(){var F=%s,MIN=44,MAX=120;function fit(){document.querySelectorAll('.via-seal').forEach(function(s){var t=s.nextElementSibling;if(!t)return;
var m=Math.max(MIN,Math.min(MAX,Math.round(t.getBoundingClientRect().height)));s.style.setProperty('--seal-main',m+'px');s.style.setProperty('--seal-full',Math.round(m/F)+'px');});}
if(document.fonts&&document.fonts.ready)document.fonts.ready.then(fit);window.addEventListener('load',fit);var tm;window.addEventListener('resize',function(){clearTimeout(tm);tm=setTimeout(fit,80)});fit();})();</script>"""


def _tail_block(t: dict, fonts: bool) -> str:
    link = '<link rel="stylesheet" id="via-fonts-vdf-v0101" href="%s/fonts.css">' % ASSET_DIR if fonts else ""
    return '%s<style id="%s">%s</style>%s' % (link, WB_ID, wb_css(t.get("tokens") or {}), JS_FIT % t.get("main_frac", 1.0))


def _clean(page: str) -> str:
    page = re.sub(r'<link rel="stylesheet" id="via-fonts-vdf-v0101"[^>]*>', "", page)
    page = re.sub(r'<style id="%s">.*?</style>' % WB_ID, "", page, flags=re.S)
    return re.sub(r'<script id="via-seal-fit-vdf-v0101">.*?</script>', "", page, flags=re.S)


def _put_tail(page: str, block: str) -> str:
    j = page.lower().rfind("</body>")
    return (page[:j] + block + page[j:]) if j >= 0 else (page + block)


def _seal(t: dict) -> str:
    return '<div class="via-seal"><img alt="seal" src="%s"></div>' % t["seal_uri"] if t.get("seal_uri") else ""


# ---------------------------------------------------------------- ① DataFrame 表頭
def table_columns(out_dir: Path, home: str | None = None) -> dict:
    """{(db, table): [欄]} + 來源說明。ENG237 尾版 list_tables(唯讀)→ 成功就寫快取;失敗 → 快取;都沒有 → 空 + 原因。"""
    cache = Path(out_dir) / COLS_CACHE
    why, cols, src = "", {}, ""
    ex = None
    try:
        hits = sorted((VDF / "engine").glob("VDF_ENG237_DataExport_v*.py"), key=PRIOR._vnum)
        if hits:
            spec = importlib.util.spec_from_file_location("vdf_eng237_for_eng236_v0101", hits[-1])
            ex = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(ex)
    except Exception as exc:  # noqa: BLE001 — 取資料引擎載不起來 → 照實
        why = "ENG237 載不起來(%s)" % type(exc).__name__
    if ex is not None:
        try:
            h, how = ex.resolve_home(home)
            rows = ex.list_tables(h)
            for r in rows:
                if r.get("columns"):
                    cols[(str(r.get("db")), str(r.get("table")))] = list(r["columns"])
            errs = [r for r in rows if r.get("error")]
            src = "庫 %s(%s)· %d 表%s" % (h, how, len(cols), (" · 打不開 %d 本" % len(errs)) if errs else "")
            if cols:
                cache.parent.mkdir(parents=True, exist_ok=True)
                cache.write_text(json.dumps({"ts": datetime.datetime.now().isoformat(timespec="seconds"), "source": src,
                                             "tables": [{"db": d, "table": t, "columns": c} for (d, t), c in sorted(cols.items())]}, ensure_ascii=False, indent=1), encoding="utf-8")
            elif not why:
                why = "庫裡沒讀到表(%s)" % src
        except ModuleNotFoundError as exc:
            why = "這台沒有 %s(表頭要在有 duckdb 的機器讀)" % exc.name
        except Exception as exc:  # noqa: BLE001 — 庫被佔用 / 家不在 → 照實
            why = "讀庫失敗(%s: %s)" % (type(exc).__name__, str(exc)[:80])
    if not cols and cache.is_file():
        try:
            c = json.loads(cache.read_text(encoding="utf-8"))
            cols = {(x["db"], x["table"]): x["columns"] for x in c.get("tables") or []}
            src = "快取 %s · %s" % (c.get("ts"), c.get("source"))
        except (OSError, ValueError, KeyError):
            pass
    return {"cols": cols, "source": src, "why": why if not cols else ""}


def _cols_for(r: dict, tc: dict) -> list:
    got = tc["cols"].get((r["db"], r["table"]))
    if got is None:
        for (d, t), c in tc["cols"].items():
            if t == r["table"] and (d.lower() == r["db"].lower() or not r["db"].endswith(".duckdb")):
                got = c
                break
    return list(got or r.get("columns") or [])


def _hcell(cols: list, tc: dict) -> str:
    if not cols:
        return '<div class="cell"><div class="hs-note" title="%s">未讀到</div></div>' % _e(tc.get("why") or "頁首那行寫原因")   # 原因只在頁首寫一次 · 這裡滑鼠停留看
    chips = "".join('<span class="h" title="%s">%s</span>' % (_e(c), _e(str(c).replace("_", " "))) for c in cols[:SHOW_N])
    more = '<span class="h more">+%d 欄</span>' % (len(cols) - SHOW_N) if len(cols) > SHOW_N else ""
    return '<div class="cell"><div class="hs">%s%s</div></div>' % (chips, more)


def render_html(m: dict, spec: dict | None = None, tc: dict | None = None, t: dict | None = None) -> str:
    """v0100 的頁 + 表頭欄 + 範本覆蓋 + 印章(順序照 v0100 的列序一格一格補)。"""
    tc = tc if tc is not None else {"cols": {}, "source": "", "why": "沒有讀庫"}
    t = t if t is not None else template()
    rows = [r for s in m["sections"] for r in s["rows"]]
    for r in rows:                                          # 明細(data-detail)裡的欄位跟著補(只補 v0100 是空的 · 先補再產頁)
        cols = _cols_for(r, tc)
        if cols and not r.get("columns"):
            r["columns"] = cols
    page = PRIOR.render_html(m, spec)
    page = page.replace('<div class="col-hdr">庫況</div>', '<div class="col-hdr">表頭 / DataFrame Headers</div><div class="col-hdr">庫況</div>')
    parts = page.split('<div class="cell"><span class="status status-')
    if len(parts) - 1 == len(rows):
        out = [parts[0]]
        for r, rest in zip(rows, parts[1:]):
            out.append(_hcell(_cols_for(r, tc), tc) + '<div class="cell"><span class="status status-' + rest)
        page = "".join(out)
    page = page.replace('<div class="hdr"><div><div class="hdr-badge">VDF · DATA FETCH MATRIX</div>',
                        '<div class="hdr">%s<div><div class="hdr-badge">VERITAS DATA FORGE · VDF · DATA FETCH MATRIX</div>' % _seal(t), 1)
    note = ("表頭:%s" % tc["source"]) if tc.get("source") else ("表頭:未讀到(%s)" % (tc.get("why") or "—"))
    page = page.replace('<div class="hdr-sub">', '<div class="hdr-sub">%s</div><div class="hdr-sub">' % _e(note), 1)
    page = page.replace("<title>VDF 擷取矩陣</title>", "<title>Veritas Data Forge · VDF 擷取矩陣</title>", 1)
    fonts = False
    return _put_tail(_clean(page), _tail_block(t, fonts))


def build(out: Path | None = None, db_check: Path | None = None, via: Path | None = None, launch: Path | None = None) -> dict:
    via = Path(via or VIA)
    out = Path(out or (via / "VIA_Reports" / "vdf"))
    rep = via / "VIA_Reports" / "vdf"
    dbc = PRIOR._load(Path(db_check) if db_check else rep / "DB_CHECK_latest.json")
    lch = PRIOR._load(Path(launch) if launch else rep / "RESULT_engine_launch_latest.json")
    m = PRIOR.build_model(PRIOR.load_books(via), dbc, lch)
    out.mkdir(parents=True, exist_ok=True)
    tc = table_columns(out, (dbc or {}).get("home"))
    t = template(via)
    page = render_html(m, None, tc, t)
    if fonts_place(out, t.get("fonts_zip")):
        page = _put_tail(_clean(page), _tail_block(t, True))
    fh, fj = out / "FETCH_MATRIX_latest.html", out / "FETCH_MATRIX_latest.json"
    fh.write_text(page, encoding="utf-8")
    m["columns_source"] = tc.get("source") or tc.get("why")
    fj.write_text(json.dumps(m, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    c = m["counts"]
    with_cols = sum(1 for s in m["sections"] for r in s["rows"] if r.get("columns"))
    return {"html": str(fh), "json": str(fj), "counts": c, "lamp": "RED" if c["RED"] else ("YELLOW" if c["YELLOW"] or c["NONE"] else "GREEN"),
            "line": "[擷取矩陣] 表 %d(他系統 %d)· 庫 %d · 族群 %d · 引擎 %d · 到齊 %d · 待補 %d · 缺 %d · 未量 %d · 端點實測 %d/%d · 表頭 %d 表(%s)· 頁 %s" % (
                c["tables"], c["other_system"], c["dbs"], c["groups"], c["engines"], c["GREEN"], c["YELLOW"], c["RED"], c["NONE"],
                c["endpoints_verified"], c["endpoints"], with_cols, tc.get("source") or tc.get("why") or "—", fh)}


# ---------------------------------------------------------------- ② VDF 操作頁頁首(經 apply_spec)
_RX_HDR = re.compile(r"(?:%s)?<header(?: class=\"via-wb\")?>(?:<h1>(?P<h1>VDF[^<]*)</h1><small>(?P<small>.*?)</small>|.*?<div class=\"via-tag\">(?P<tag>.*?)</div></div>)</header>" % re.escape(MARK), re.S)


def upgrade_page(h: str, out_dir: Path, t: dict) -> str:
    h = _clean(h)
    m = _RX_HDR.search(h)
    if m:
        tag = m.group("tag") if m.group("tag") is not None else ("%s · %s" % (_e(m.group("h1")), m.group("small")))
        new = '%s<header class="via-wb">%s<div class="via-hdtxt"><small>%s</small><h1>%s</h1><div class="via-tag">%s</div></div></header>' % (
            MARK, _seal(t), _e(t.get("caps")), _e(t.get("title")), tag)
        h = h[:m.start()] + new + h[m.end():]
    return _put_tail(h, _tail_block(t, fonts_place(out_dir, t.get("fonts_zip"))))


def apply_spec(page, spec: dict | None = None) -> str:
    """v0100 照套規格(回 inserted / replaced / same / missing / lock-bad · 語意不變)→ 有 VDF 頁首的頁再換範本頁首 + 印章 + 字型(</body> 前 · 冪等)。"""
    how = PRIOR.apply_spec(page, spec)
    p = Path(page)
    if how in ("missing", "lock-bad") or not p.is_file():
        return how
    h = p.read_text(encoding="utf-8")
    if "<header" not in h or 'id="vdf-fetchmatrix-layout"' in h:
        return how
    new = upgrade_page(h, p.parent, template())
    if new != h:
        p.write_text(new, encoding="utf-8")
    return how


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["--selftest"]:
        return selftest()
    if not a or a[0] not in ("build",):
        print("用法:python %s build [--out 夾] [--db-check DB_CHECK.json] [--json] · --selftest" % Path(__file__).name)
        return 2

    def opt(k):
        return a[a.index(k) + 1] if k in a and a.index(k) + 1 < len(a) else None
    r = build(out=opt("--out"), db_check=opt("--db-check"))
    print(json.dumps(r, ensure_ascii=False, indent=1) if "--json" in a else r["line"])
    return 0


def selftest() -> int:
    import os
    import shutil
    import tempfile
    ok = bad = 0

    def chk(name, cond, note=""):
        nonlocal ok, bad
        if cond:
            ok += 1
            print("  [OK] %s" % name)
        else:
            bad += 1
            print("  [FAIL] %s%s" % (name, (" · " + str(note)[:240]) if note else ""))

    print("=== %s · 自測(DataFrame 表頭欄 · 印章頁首 · 範本覆蓋)===" % TAG)
    t = template()
    chk("① 模板冊尾版 ≥ v0104:tokens(米白 #f5f4f0)· systems.VDF caps / title · assets 印章 + 字型雜湊對上(%s)" % t.get("book"),
        t["ok"] and t["tokens"].get("bg") == "#f5f4f0" and "VDF" in t["caps"] and t["title"] and t["seal_uri"] and t["fonts_zip"] is not None, t.get("why"))
    tmp = Path(tempfile.mkdtemp(prefix="vdf_eng236_v0101_"))
    try:
        m = PRIOR.build_model(PRIOR.load_books(), None, None)
        rows = [r for s in m["sections"] for r in s["rows"]]
        fake = {"cols": {(rows[0]["db"], rows[0]["table"]): ["date", "ticker", "open", "high", "low", "close", "volume", "adj_close", "source", "fetched_at", "turnover", "trades"]},
                "source": "庫 測試(替身)· 1 表", "why": ""}
        page = render_html(m, None, fake, t)
        n_sec = len(m["sections"])
        chk("② 每段矩陣多一欄「表頭 / DataFrame Headers」(在庫況之前)· 每列一格(%d 列)" % len(rows),
            page.count('<div class="col-hdr">表頭 / DataFrame Headers</div>') == n_sec and page.count('<div class="hs">') + page.count('<div class="hs-note"') == len(rows)
            and page.index("表頭 / DataFrame Headers") < page.index('<div class="col-hdr">庫況</div>'))
        chk("② 讀到的欄名照列(前 10 · 底線 → 空格 · title 原名)· 其餘 +N 欄 · 沒讀到的寫原因不猜",
            'title="adj_close">adj close</span>' in page and '+2 欄' in page and "未讀到" in page)
        chk("③ 印章頁首:.hdr 左邊印章 data URI · 徽章 VERITAS DATA FORGE · 標題名 · 頁首說明照舊", '<div class="hdr"><div class="via-seal"><img alt="seal" src="data:image/png;base64,' in page
            and "VERITAS DATA FORGE · VDF · DATA FETCH MATRIX" in page and "<h1>VDF 擷取矩陣</h1>" in page and "表頭:庫 測試(替身)" in page)
        chk("③ 範本覆蓋在 </body> 前一段(v0100 規格段與版面段原樣在頁首)· 五欄格線 · 窄螢幕一欄", page.count('<style id="%s">' % WB_ID) == 1 and page.index(WB_ID) > page.index("vdf-fetchmatrix-layout")
            and 'id="vrn2-professional' in page.split("</head>")[0] and "minmax(220px,1.6fr) 92px" in page and page.rstrip().endswith("</html>"))
        nocache = table_columns(tmp)
        chk("④ 這台沒有 duckdb / 庫不在 → 不當掉 · 寫原因(%s)" % (nocache.get("why") or nocache.get("source")), isinstance(nocache["cols"], dict) and (nocache["why"] or nocache["source"]))
        (tmp / COLS_CACHE).write_text(json.dumps({"ts": "2026-11-01T00:00:00", "source": "庫 x", "tables": [{"db": rows[0]["db"], "table": rows[0]["table"], "columns": ["date", "close"]}]}), encoding="utf-8")
        cached = table_columns(tmp)
        chk("④ 讀庫失敗 → 沿用快取(標快取時間)", cached["cols"].get((rows[0]["db"], rows[0]["table"])) == ["date", "close"] and cached["source"].startswith("快取 2026-11-01"), cached)
        r = build(out=tmp)
        chk("⑤ build:頁 + json 寫出 · 一行報表頭來源", Path(r["html"]).is_file() and "表頭" in r["line"] and (tmp / ASSET_DIR / "fonts.css").is_file()
            and 'id="via-fonts-vdf-v0101"' in Path(r["html"]).read_text(encoding="utf-8"), r["line"])
        ui = tmp / "VDF_UI_latest.html"
        ui.write_text('<!doctype html><html><head><title>VDF U/I</title><style>body{margin:0}</style></head><body><header><h1>VDF · VDF_SystemManager_v0166</h1><small>2026-11-01 · 左:輸入介面 · <span style="color:#16a34a">●</span>綠</small></header>'
                      '<aside><div class="card">x</div></aside><main>y</main></body></html>', encoding="utf-8")
        h1 = apply_spec(ui)
        u1 = ui.read_text(encoding="utf-8")
        h2 = apply_spec(ui)
        u2 = ui.read_text(encoding="utf-8")
        chk("⑥ VDF 操作頁:apply_spec 語意照 v0100(inserted → same)· 頁首換範本(印章 · caps · Veritas Data Forge · 原說明原樣)· 冪等", h1 == "inserted" and h2 == "same" and u1 == u2
            and '<header class="via-wb"><div class="via-seal"><img' in u1 and "<h1>Veritas Data Forge</h1>" in u1 and "VDF · VDF_SystemManager_v0166 · 2026-11-01 · 左:輸入介面" in u1
            and u1.count(MARK) == 1 and 'id="vrn2-professional-v0242"' in u1 and "vdf-vrn2-bridge" in u1, (h1, h2))
        chk("⑦ 印章無框無陰影無濾鏡 · 主印框高 = 文字區塊高(44 ~ 120px)", "box-shadow:none;filter:none" in wb_css({}) and "MIN=44,MAX=120" in u1 and ("var F=%s," % t["main_frac"]) in u1)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 不匯入他系統程式(CGC_ / VRN_)· 兩座橋在 · 零網路 · 不寫模板冊", not re.search(r"^\s*(import|from)\s+(CGC_|VRN_|VCGC|requests|httpx|urllib\.request)", src, re.M)
        and "VIA:ACCEL-BRIDGE" in src and "VIA:NET-BRIDGE" in src and "VIA_UI_Template_SSOT_v*.json\").write" not in src)
    print("  ── 前版 v0100 自測 ──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("⑨ 前版 v0100 自測 rc 0", prc == 0)
    print("[計] %s 自測 %d/%d · %s" % (TAG, ok, ok + bad, "PASS" if not bad else "FAIL"))
    return 0 if not bad else 1


if __name__ == "__main__":
    raise SystemExit(main())
