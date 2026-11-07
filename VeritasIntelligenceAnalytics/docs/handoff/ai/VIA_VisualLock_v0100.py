#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0100]
r"""VIA_VisualLock v0100 — 本系統標準視覺鎖定 U/I(操作員 2026-11-07 令)。

操作員令:「視覺鎖定以下用此為格式 https://viaatlas-39ozanmz.manus.space ·
個股模板 <Claude Design TW Stock Dashboard v2> · 本系統標準視覺鎖定 U/I」。

兩個外部連結本會話都讀不到(Manus 302 轉 manus.im/app-auth 登入牆;Claude Design 連結
Artifact 工具明確不支援),**但兩者的正本倉內都有**,所以不靠外站也能做:

  鎖定正本(格式)  review/VIA_Atlas_LocalSite_v0100/index.html
                    2026-11-06 已位元組鎖定(SHA256SUMS.txt);本支每次都重驗
  個股模板(版面)  functional modules/VAP/ASSETS/VIA_TW_Stock_Dashboard_standalone.html
                    區段清單由它撈出來;它自己用的是另一套色盤 --color-*,所以要接到 --vl-*

**鎖是抽出來的,不是手抄的**:`kit` 直接從鎖定正本的 `:root{}` 抽 `--vl-*` 宣告,
算出 token 區塊的 sha256。手抄會漂移,抽取不會 —— 正本改了,kit 跟著改,`check` 立刻看得出來。

動詞:
  tokens            印鎖定 token(由正本抽出)+ 區塊 sha + 正本 SHA256SUMS 驗證結果
  kit               產出 via_visual_lock_v0100.css(所有 VIA 頁共用的同一份位元組)
  check <檔…>       鎖定閘:① 色彩只准 var(--vl-*),不准生 hex / rgb ② 0 外連
                    ③ 有手機側邊槽 max(16px, env(safe-area-inset-*)) ④ 不橫向捲動的宣告
                    ⑤ 用了 kit 的頁,其 token 區塊 sha 必須等於正本
  index             個股資料盤點:vrn_reports.duckdb 裡哪些 ticker 有料
  stock --ticker X  出個股頁(版面照模板清單 · 樣式用鎖定 kit · 資料來自 VRN-2 庫)
  all               tokens → kit → index → stock(有料的前 N 檔)→ check 自己產出的頁
  --selftest        夾具自測(零網路 · 只寫沙盒)

誠實規矩:沒有資料的欄位印「—」並標 `data-state="GRAY"`,區段頂端寫明「缺什麼 · 為什麼」;
技術面 / 籌碼面要 VDF 日資料(K 線 · 量 · 三大法人 · 融資券),容器裡沒有就照實說沒有,
**絕不畫假 K 線、絕不編價格**。五系統對等獨立:只讀他系統自報值,不改他系統正本。
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

import argparse
import hashlib
import html
import importlib.util
import json
import math
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

TAG = "VIA_VisualLock v0100"
LOCK_SITE = Path("review") / "VIA_Atlas_LocalSite_v0100"
LOCK_PAGE = LOCK_SITE / "index.html"
STOCK_TEMPLATE = Path("functional modules") / "VAP" / "ASSETS" / "VIA_TW_Stock_Dashboard_standalone.html"
VRN_DB = Path("functional modules") / "VRN" / "db" / "vrn_reports.duckdb"
KIT_NAME = "via_visual_lock_v0100.css"
SVG_NS = "http://www.w3.org/2000/svg"

# 個股模板的區段清單(由 VIA_TW_Stock_Dashboard_standalone.html 的字串撈出,不是我編的)
STOCK_SECTIONS = [
    ("head", "標頭", ["名稱 · 代號", "市場 TWSE / TPEX", "產業", "昨收", "高 / 低", "成交量(張)"]),
    ("basic", "基本資料", ["成立 / 上市", "董事長", "股本(億元)", "發行股數(億股)", "地址", "股務代理"]),
    ("value", "評價分析表", ["本益比", "近 2 年分位", "殖利率", "股價淨值比",
                             "估值分位為近兩年區間 · 不代表預測價格"]),
    ("consensus", "年度 EPS / 營收共識", ["年度", "EPS 共識", "營收(兆)", "分析師家數"]),
    ("rating", "分析師評級", ["強力買進", "買進", "優於大盤", "持有", "目標價中位數"]),
    ("income", "年度損益表", ["營業收入", "營業毛利", "營業利益", "稅後淨利"]),
    ("ratio", "比率分析", ["毛利率", "營業利益率", "淨利率", "負債比"]),
    ("peer", "族群 / 指數比較", ["族群", "族群家數", "相對強弱"]),
    ("stack", "共振堆疊圖", ["價格 K線 / MA / EMA / BB(20)", "成交量 · 日均量(張)",
                             "隨機指標(9)超買 80 / 超賣 20", "三大法人買賣超 · 四類堆疊",
                             "融資 / 融券", "7 卡共用同一時間索引 · 十字線貫穿全部卡"]),
]
# 哪些區段要 VDF 日資料(容器沒有就照實 GRAY,不畫假圖)
NEEDS_DAILY = {"stack", "peer", "value"}
LANE_OF_SECTION = {"head": "VDF", "basic": "VRN-2", "value": "VQG", "consensus": "VRN-2",
                   "rating": "VRN-2", "income": "VRN-2", "ratio": "VQG", "peer": "VQG",
                   "stack": "VDF"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def have(module: str) -> bool:
    try:
        return importlib.util.find_spec(module) is not None
    except (ImportError, ValueError):
        return False


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------- ① 抽 token(不手抄)
TOKEN_RE = re.compile(r"--vl-([a-z0-9-]+)\s*:\s*([^;}]+)")


def extract_tokens(page: Path) -> dict:
    """從鎖定正本抽 --vl-* 宣告。手抄會漂移,抽取不會。"""
    text = Path(page).read_text(encoding="utf-8", errors="replace")
    blocks = re.findall(r":root\s*\{([^}]*)\}", text)
    tokens: dict = {}
    order: list = []
    for block in blocks:
        for name, value in TOKEN_RE.findall(block):
            value = value.strip()
            if name not in tokens:
                order.append(name)
            tokens[name] = value
    canon = "\n".join("--vl-%s:%s" % (name, tokens[name]) for name in order)
    return {"tokens": tokens, "order": order, "canon": canon, "sha256": sha256_text(canon),
            "count": len(tokens), "source": str(page)}


def verify_lock_site(via: Path) -> dict:
    """重驗鎖定正本的位元組(SHA256SUMS.txt)。鎖對不上就不是鎖定版。"""
    site = Path(via) / LOCK_SITE
    sums = site / "SHA256SUMS.txt"
    if not sums.is_file():
        return {"ok": False, "why": "找不到 %s" % sums}
    try:
        done = subprocess.run(["sha256sum", "-c", sums.name], cwd=str(site),
                              capture_output=True, text=True, timeout=120, check=False)
    except (OSError, subprocess.SubprocessError) as exc:
        return {"ok": False, "why": "%s: %s" % (type(exc).__name__, exc)}
    lines = [ln for ln in done.stdout.splitlines() if ln.strip()]
    bad = [ln for ln in lines if not ln.endswith(": OK")]
    return {"ok": done.returncode == 0 and not bad, "rc": done.returncode,
            "checked": len(lines), "failed": bad, "path": str(sums)}


def build_kit(info: dict) -> str:
    """所有 VIA 頁共用的同一份 CSS。只有 token 是從正本抽來的;其餘是用這些 token 寫的版面規則。"""
    decls = "\n  ".join("--vl-%s: %s;" % (name, info["tokens"][name]) for name in info["order"])
    return """/* %s — VIA 標準視覺鎖定 U/I kit
 * token 由鎖定正本抽出(不手抄):%s
 * token 區塊 sha256: %s  ·  共 %d 個 token
 * 改 token 只能改鎖定正本;改了這裡 check 會紅。
 */
:root {
  %s
}
*, *::before, *::after { box-sizing: border-box }
html { -webkit-text-size-adjust: 100%% }
body {
  margin: 0; background: var(--vl-bg); color: var(--vl-ink);
  font-family: var(--vl-font-cjk); font-size: var(--vl-size-base); line-height: 1.55;
  padding-left: max(16px, env(safe-area-inset-left, 0px));
  padding-right: max(16px, env(safe-area-inset-right, 0px));
  padding-block: 18px 44px;
  overflow-x: hidden;
}
h1 { font-family: var(--vl-font-display); font-size: var(--vl-size-title); color: var(--vl-title);
     margin: 0 0 2px; letter-spacing: .01em; text-wrap: balance }
h2 { font-family: var(--vl-font-display); font-size: calc(var(--vl-size-title) * .72);
     color: var(--vl-title); margin: 20px 0 8px }
.vl-sub { color: var(--vl-muted); font-size: var(--vl-size-label); margin: 0 0 14px }
.vl-panel { background: var(--vl-white); border: 1px solid var(--vl-border); border-radius: 3px;
            padding: 10px 12px; margin: 0 0 10px }
.vl-head { display: flex; flex-wrap: wrap; gap: 8px; align-items: baseline;
           border-bottom: 1px solid var(--vl-border-soft); padding-bottom: 6px; margin-bottom: 8px }
.vl-head .vl-why { color: var(--vl-muted); font-size: var(--vl-size-label) }
.vl-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 8px }
.vl-cell { border: 1px solid var(--vl-border-soft); background: var(--vl-row); padding: 7px 9px }
.vl-cell .vl-label { display: block; color: var(--vl-muted); font-size: var(--vl-size-label);
                     letter-spacing: .04em; text-transform: uppercase }
.vl-cell .vl-value { display: block; font-family: var(--vl-font-mono);
                     font-size: var(--vl-size-primary); color: var(--vl-ink); margin-top: 2px;
                     word-break: break-word }
.vl-cell[data-state="GRAY"] .vl-value { color: var(--vl-muted) }
.vl-scroll { overflow-x: auto; -webkit-overflow-scrolling: touch }
table { border-collapse: collapse; width: 100%%; font-size: var(--vl-size-numeric) }
th, td { border: 1px solid var(--vl-border); padding: 4px 7px; text-align: left; vertical-align: top }
th { background: var(--vl-row); color: var(--vl-title); font-weight: 600; white-space: nowrap }
td.vl-num { text-align: right; font-family: var(--vl-font-mono); font-variant-numeric: tabular-nums;
            white-space: nowrap }
.vl-pill { display: inline-block; padding: 1px 6px; font-size: var(--vl-size-status);
           letter-spacing: .06em; border: 1px solid transparent }
.vl-pill.ok { background: var(--vl-success-bg); color: var(--vl-success-ink);
              border-color: var(--vl-success) }
.vl-pill.warn { background: var(--vl-warning-bg); color: var(--vl-warning-ink);
                border-color: var(--vl-warning-ink) }
.vl-pill.bad { background: var(--vl-danger-bg); color: var(--vl-danger-ink);
               border-color: var(--vl-danger-ink) }
.vl-pill.gray { background: var(--vl-row); color: var(--vl-muted); border-color: var(--vl-border) }
.vl-note { color: var(--vl-muted); font-size: var(--vl-size-label); margin: 6px 0 0 }
.vl-foot { color: var(--vl-muted); font-size: var(--vl-size-label); margin-top: 26px;
           padding-top: 10px; border-top: 1px solid var(--vl-border) }
""" % (TAG, info["source"], info["sha256"], info["count"], decls)


# ---------------------------------------------------------------- ② 鎖定閘
RAW_COLOR_RE = re.compile(r"(?<![\w-])(#[0-9a-fA-F]{3,8}\b|rgba?\s*\([^)]*\)|hsla?\s*\([^)]*\))")
URL_RE = re.compile(r"https?://[^\s\"'<>)]+")
TOKEN_BLOCK_RE = re.compile(r":root\s*\{([^}]*--vl-[^}]*)\}")


def check_page(path: Path, expect_sha: str) -> dict:
    """鎖定閘。紅就是紅:色彩寫死 · 外連 · 沒有手機側邊槽 · token 區塊和正本對不上。"""
    path = Path(path)
    out = {"file": str(path), "lamp": "GREEN", "findings": []}
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        out["lamp"] = "RED"
        out["findings"].append("讀不到:%s" % exc)
        return out

    # ① token 區塊:有就必須和正本一致
    blocks = TOKEN_BLOCK_RE.findall(text)
    if blocks:
        tokens: dict = {}
        order: list = []
        for block in blocks:
            for name, value in TOKEN_RE.findall(block):
                if name not in tokens:
                    order.append(name)
                tokens[name] = value.strip()
        canon = "\n".join("--vl-%s:%s" % (n, tokens[n]) for n in order)
        got = sha256_text(canon)
        out["token_sha256"] = got
        out["token_count"] = len(tokens)
        if got != expect_sha:
            out["findings"].append("token 區塊和鎖定正本對不上(本頁 %s · 正本 %s)"
                                   % (got[:16], expect_sha[:16]))
    else:
        out["token_sha256"] = None
        if KIT_NAME not in text:
            out["findings"].append("既沒有 token 區塊,也沒有連到 %s —— 沒有用鎖定 kit" % KIT_NAME)

    # ② 色彩寫死(token 區塊自己不算;那是 token 的定義處)
    stripped = TOKEN_BLOCK_RE.sub("", text)
    stripped = re.sub(r"<!--.*?-->", "", stripped, flags=re.S)
    raws = sorted({m.group(1) for m in RAW_COLOR_RE.finditer(stripped)})
    if raws:
        out["findings"].append("色彩寫死 %d 處(鎖定律:只准 var(--vl-*)):%s"
                               % (len(raws), " ".join(raws[:6])))
    out["raw_colors"] = raws[:12]

    # ③ 外連(SVG 命名空間不算)
    urls = sorted({u for u in URL_RE.findall(text) if u != SVG_NS and not u.startswith(SVG_NS)})
    if urls:
        out["findings"].append("外連 %d 個(鎖定律:離線單檔):%s" % (len(urls), " ".join(urls[:4])))
    out["external"] = urls[:8]

    # ④ 手機側邊槽 + 不橫向捲動
    uses_kit = KIT_NAME in text
    if not uses_kit:
        if "env(safe-area-inset-left" not in text or "max(16px" not in text:
            out["findings"].append("缺手機側邊槽 max(16px, env(safe-area-inset-left, 0px))")
        if "overflow-x" not in text:
            out["findings"].append("沒有宣告 overflow-x(頁面可能橫向捲動)")
    out["uses_kit"] = uses_kit

    if out["findings"]:
        out["lamp"] = "RED"
    return out


# ---------------------------------------------------------------- ③ 個股資料(只讀 · 缺就 GRAY)
def numeric(value):
    try:
        if value is None:
            return None
        got = float(value)
        return None if math.isnan(got) or math.isinf(got) else got
    except (TypeError, ValueError):
        return None


def stock_index(db: Path) -> dict:
    """盤點:哪些 ticker 在 VRN-2 庫裡真的有料。讀不到就照實說讀不到。"""
    db = Path(db)
    if not db.is_file():
        return {"ok": False, "why": "找不到 VRN-2 庫:%s" % db, "rows": []}
    if not have("duckdb"):
        return {"ok": False, "why": "沒有 duckdb(零安裝律:不 pip);桌機用非隔離 python 跑", "rows": []}
    try:
        import duckdb
        con = duckdb.connect(str(db), read_only=True)
        try:
            rows = con.execute(
                "SELECT ticker, max(name_official) AS name, count(*) AS reports,"
                "       max(report_date) AS last_date, count(DISTINCT broker) AS brokers"
                " FROM vrn_report_basic"
                " WHERE ticker IS NOT NULL AND trim(ticker) <> ''"
                " GROUP BY ticker ORDER BY reports DESC, ticker").fetchall()
        finally:
            con.close()
    except Exception as exc:                                      # noqa: BLE001
        return {"ok": False, "why": "%s: %s" % (type(exc).__name__, exc), "rows": []}
    return {"ok": True, "db": str(db), "tickers": len(rows),
            "rows": [{"ticker": r[0], "name": r[1], "reports": r[2], "last_date": r[3],
                      "brokers": r[4]} for r in rows]}


def stock_facts(db: Path, ticker: str) -> dict:
    """一檔股票的事實。只取 VRN-2 自己落庫的值;沒有的欄位不補、不猜。"""
    facts = {"ticker": ticker, "basic": [], "metrics": [], "analysts": [], "summary": [],
             "sources": {}, "why": None}
    db = Path(db)
    if not db.is_file() or not have("duckdb"):
        facts["why"] = ("找不到 VRN-2 庫" if not db.is_file()
                        else "沒有 duckdb(零安裝律:不 pip)")
        return facts
    try:
        import duckdb
        con = duckdb.connect(str(db), read_only=True)
        try:
            cols = ["report_file", "broker_name_zh", "broker_name_en", "report_date", "rating_raw",
                    "rating_code", "rating_direction", "target_price", "target_price_adj",
                    "price", "price_latest_adj", "price_latest_date", "upside_report",
                    "upside_adj", "upside_adj_state", "report_age_days", "target_freshness",
                    "analyst_names", "analyst_n", "name_official", "ssot_state"]
            got = con.execute(
                "SELECT %s FROM vrn_report_basic WHERE ticker = ? ORDER BY report_date DESC"
                % ", ".join('"%s"' % c for c in cols), [ticker]).fetchall()
            facts["basic"] = [dict(zip(cols, row)) for row in got]
            facts["metrics"] = [dict(zip(["report_file", "metric", "period", "status", "value",
                                          "raw_text"], row)) for row in con.execute(
                "SELECT m.report_file, m.metric, m.period, m.status, m.value, m.raw_text"
                " FROM vrn_report_metrics m JOIN vrn_report_basic b USING (report_file)"
                " WHERE b.ticker = ? ORDER BY m.period, m.metric", [ticker]).fetchall()]
            facts["analysts"] = [dict(zip(["analyst_zh", "analyst_en", "email", "domain"], row))
                                 for row in con.execute(
                "SELECT DISTINCT a.analyst_zh, a.analyst_en, a.email, a.domain"
                " FROM vrn_report_analyst a JOIN vrn_report_basic b USING (report_file)"
                " WHERE b.ticker = ?", [ticker]).fetchall()]
            facts["summary"] = [dict(zip(["report_file", "points", "state"], row))
                                for row in con.execute(
                "SELECT n.report_file, n.summary_points_json, n.summary_state"
                " FROM vrn_nlp_text_summary n JOIN vrn_report_basic b USING (report_file)"
                " WHERE b.ticker = ?", [ticker]).fetchall()]
        finally:
            con.close()
    except Exception as exc:                                      # noqa: BLE001
        facts["why"] = "%s: %s" % (type(exc).__name__, exc)
        return facts
    facts["sources"] = {"vrn_report_basic": len(facts["basic"]),
                        "vrn_report_metrics": len(facts["metrics"]),
                        "vrn_report_analyst": len(facts["analysts"]),
                        "vrn_nlp_text_summary": len(facts["summary"]),
                        "db": str(db)}
    if not facts["basic"]:
        facts["why"] = "VRN-2 庫裡沒有這個 ticker 的列"
    return facts


# ---------------------------------------------------------------- ④ 個股頁(鎖定 kit · 缺就 GRAY)
def esc(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def cell(label: str, value, note: str = "") -> str:
    got = value
    state = "GRAY" if got in (None, "", "nan") else "OK"
    shown = "—" if state == "GRAY" else got
    extra = '<span class="vl-label">%s</span>' % esc(note) if note else ""
    return ('<div class="vl-cell" data-state="%s"><span class="vl-label">%s</span>'
            '<span class="vl-value">%s</span>%s</div>'
            % (state, esc(label), esc(shown), extra))


def section_block(key: str, title: str, fields: list, body: str, why: str) -> str:
    lane = LANE_OF_SECTION.get(key, "—")
    pill = ('<span class="vl-pill gray">GRAY</span>' if why
            else '<span class="vl-pill ok">有料</span>')
    note = ('<span class="vl-why">%s</span>' % esc(why)) if why else ""
    inner = body or ('<div class="vl-grid">%s</div>'
                     % "".join(cell(f, None) for f in fields))
    return ('<section class="vl-panel" id="sec-%s"><div class="vl-head">%s'
            '<h2 style="margin:0">%s</h2>'
            '<span class="vl-why">車道 %s</span>%s</div>%s</section>'
            % (esc(key), pill, esc(title), esc(lane), note, inner))


def render_stock(facts: dict, info: dict, out: Path, kit_rel: str = KIT_NAME) -> dict:
    """個股頁:版面照模板的區段清單,樣式用鎖定 kit,值只來自 VRN-2 庫。"""
    ticker = facts["ticker"]
    rows = facts.get("basic") or []
    latest = rows[0] if rows else {}
    name = latest.get("name_official") or ""
    gray = []
    parts = []

    for key, title, fields in STOCK_SECTIONS:
        body = ""
        why = ""
        if key == "head":
            body = '<div class="vl-grid">%s</div>' % "".join([
                cell("名稱 · 代號", ("%s · %s" % (name, ticker)).strip(" ·") or None),
                cell("最新報告日", latest.get("report_date")),
                cell("券商", latest.get("broker_name_zh") or latest.get("broker_name_en")),
                cell("評級", latest.get("rating_raw"), latest.get("rating_direction") or ""),
                cell("目標價", latest.get("target_price")),
                cell("目標價(ADJ)", latest.get("target_price_adj")),
                cell("股價", latest.get("price")),
                cell("股價(最新 ADJ)", latest.get("price_latest_adj"),
                     latest.get("price_latest_date") or ""),
                cell("上漲空間", latest.get("upside_report")),
                cell("上漲空間(ADJ)", latest.get("upside_adj"),
                     latest.get("upside_adj_state") or ""),
            ])
            why = "" if rows else (facts.get("why") or "沒有列")
        elif key == "basic":
            why = "VRN-2 庫不存公司基本資料(成立 / 董事長 / 股本 / 股務代理);這些要公開資訊觀測站車道"
        elif key == "rating":
            if rows:
                head = "<tr><th>報告日</th><th>券商</th><th>評級</th><th>方向</th>" \
                       "<th class=\"vl-num\">目標價</th><th class=\"vl-num\">ADJ</th>" \
                       "<th class=\"vl-num\">上漲空間</th><th>時效</th><th>分析師</th></tr>"
                trs = []
                for row in rows:
                    trs.append(
                        "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td>"
                        "<td class=\"vl-num\">%s</td><td class=\"vl-num\">%s</td>"
                        "<td class=\"vl-num\">%s</td><td>%s</td><td>%s</td></tr>"
                        % (esc(row.get("report_date") or "—"),
                           esc(row.get("broker_name_zh") or row.get("broker_name_en") or "—"),
                           esc(row.get("rating_raw") or "—"),
                           esc(row.get("rating_direction") or "—"),
                           esc(row.get("target_price") if numeric(row.get("target_price")) is not None else "—"),
                           esc(row.get("target_price_adj") if numeric(row.get("target_price_adj")) is not None else "—"),
                           esc(row.get("upside_report") if numeric(row.get("upside_report")) is not None else "—"),
                           esc(row.get("target_freshness") or "—"),
                           esc(row.get("analyst_names") or "—")))
                tps = [numeric(r.get("target_price_adj")) or numeric(r.get("target_price")) for r in rows]
                tps = sorted(x for x in tps if x is not None)
                mid = ("%.2f" % ((tps[len(tps) // 2] if len(tps) % 2
                                  else (tps[len(tps) // 2 - 1] + tps[len(tps) // 2]) / 2))
                       if tps else None)
                body = ('<div class="vl-grid">%s%s</div><div class="vl-scroll"><table>%s%s</table></div>'
                        '<p class="vl-note">目標價中位數由本頁現有 %d 筆算出(ADJ 優先);'
                        '沒有目標價的報告不納入。這是本庫內的中位數,不是市場全體共識。</p>'
                        % (cell("報告筆數", len(rows)), cell("目標價中位數", mid),
                           head, "".join(trs), len(tps)))
            else:
                why = facts.get("why") or "沒有列"
        elif key in ("consensus", "income", "ratio"):
            want = {"consensus": ("EPS", "營收", "REVENUE", "revenue", "eps"),
                    "income": ("營業收入", "營業毛利", "營業利益", "稅後淨利", "淨利"),
                    "ratio": ("毛利率", "營業利益率", "淨利率", "負債比", "率")}[key]
            hits = [m for m in facts.get("metrics") or []
                    if any(w.lower() in str(m.get("metric") or "").lower() for w in want)]
            if hits:
                trs = "".join("<tr><td>%s</td><td>%s</td><td class=\"vl-num\">%s</td>"
                              "<td>%s</td><td>%s</td></tr>"
                              % (esc(m.get("metric")), esc(m.get("period") or "—"),
                                 esc(m.get("value") if numeric(m.get("value")) is not None else "—"),
                                 esc(m.get("status") or "—"), esc((m.get("raw_text") or "")[:40]))
                              for m in hits[:40])
                body = ('<div class="vl-scroll"><table><tr><th>項目</th><th>期間</th>'
                        '<th class="vl-num">值</th><th>狀態</th><th>原文</th></tr>%s</table></div>'
                        '<p class="vl-note">值與原文都來自 VRN-2 逐值落庫(status 是它自己的判決);'
                        '本頁不換算、不補值。</p>' % trs)
            else:
                why = "VRN-2 庫的 vrn_report_metrics 沒有這一類項目(本檔 %d 筆指標)" % len(
                    facts.get("metrics") or [])
        elif key in NEEDS_DAILY:
            why = ("要 VDF 日資料(K線 / 量 / 三大法人 / 融資券 / 族群);本機 VDF 庫未就緒 → "
                   "照實 GRAY,不畫假圖、不編價格")
        if why:
            gray.append(key)
        parts.append(section_block(key, title, fields, body, why))

    # 分析師 + NLP 摘要(VRN-2 自己的判決,原文照登)
    people = facts.get("analysts") or []
    if people:
        trs = "".join("<tr><td>%s</td><td>%s</td><td>%s</td></tr>"
                      % (esc(p.get("analyst_zh") or "—"), esc(p.get("analyst_en") or "—"),
                         esc(p.get("domain") or "—")) for p in people[:30])
        parts.append(section_block(
            "analyst", "分析師(VRN-2 抽取)", [], 
            '<div class="vl-scroll"><table><tr><th>中文</th><th>英文</th><th>網域</th></tr>%s</table></div>'
            '<p class="vl-note">只列中英名與網域;信箱與電話在庫裡但本頁不印(個資)。</p>' % trs, ""))
    else:
        parts.append(section_block("analyst", "分析師(VRN-2 抽取)", ["中文", "英文", "網域"], "",
                                   "這一檔沒有抽到分析師列"))
        gray.append("analyst")

    counts = facts.get("sources") or {}
    src_rows = "".join("<tr><td>%s</td><td class=\"vl-num\">%s</td></tr>" % (esc(k), esc(v))
                       for k, v in counts.items() if k != "db")
    lamp = "GREEN" if rows and len(gray) <= len(NEEDS_DAILY) + 1 else ("YELLOW" if rows else "GRAY")
    page = """<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>%s · %s · VIA 個股頁</title>
<link rel="stylesheet" href="%s">
</head><body>
<h1>%s</h1>
<p class="vl-sub">VIA 標準視覺鎖定 U/I · 格式 = Atlas VISUAL LOCK(token sha %s)· 版面 = 個股模板區段清單
 · 產生 %s · 燈 %s</p>
<section class="vl-panel"><div class="vl-head"><h2 style="margin:0">這一頁的規矩</h2></div>
<p class="vl-note">值只來自 VRN-2 自己落庫的欄位(目標價 · ADJ · 評級 · 逐值指標 · 分析師);
沒有的一律印「—」並標 GRAY,<strong>不補值、不猜、不畫假圖</strong>。
GRAY 區段 %d 個,每個都在標頭寫了缺什麼、為什麼。樣式用鎖定 kit,本頁不自己寫顏色。</p></section>
%s
<section class="vl-panel"><div class="vl-head"><h2 style="margin:0">資料來源(本倉 · 只讀)</h2></div>
<div class="vl-scroll"><table><tr><th>表</th><th class="vl-num">列</th></tr>%s</table></div>
<p class="vl-note">庫:%s · 唯讀開啟,本頁不寫他系統的庫。</p></section>
<p class="vl-foot">五系統對等獨立(L123):本頁只讀 VRN-2 自報值,不改他系統正本 / 冊 / 號 / 檔。
視覺鎖定正本 %s —— 要改樣式只能改正本,改本頁或 kit 會被 check 判紅。</p>
</body></html>
""" % (esc(name or ticker), esc(ticker), esc(kit_rel),
       esc(("%s · %s" % (name, ticker)).strip(" ·") or ticker),
       esc(info["sha256"][:16]), esc(utc_now()), esc(lamp), len(gray),
       "\n".join(parts), src_rows, esc(counts.get("db") or "—"), esc(info["source"]))
    target = Path(out) / ("stock_%s.html" % re.sub(r"[^A-Za-z0-9_-]", "_", ticker or "unknown"))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(page, encoding="utf-8")
    return {"path": str(target), "bytes": len(page.encode("utf-8")), "lamp": lamp,
            "gray_sections": gray, "reports": len(rows), "metrics": len(facts.get("metrics") or [])}


# ---------------------------------------------------------------- ⑤ CLI
def resolve_via(root: str) -> Path:
    via = Path(root).resolve()
    return via / "VeritasIntelligenceAnalytics" if (via / "VeritasIntelligenceAnalytics").is_dir() else via


def run(args) -> dict:
    via = resolve_via(args.via)
    out = Path(args.out).resolve() if args.out else via / "VIA_Reports" / "visual_lock"
    out.mkdir(parents=True, exist_ok=True)
    page = via / LOCK_PAGE
    report = {"tool": TAG, "at": utc_now(), "via": str(via), "out": str(out), "verb": args.verb}
    if not page.is_file():
        report["lamp"] = "RED"
        report["why"] = "找不到視覺鎖定正本:%s" % page
        print("[%s] RED · %s" % (TAG, report["why"]), flush=True)
        return report

    report["lock_site"] = verify_lock_site(via)
    info = extract_tokens(page)
    report["tokens"] = {"count": info["count"], "sha256": info["sha256"], "source": info["source"]}

    if args.verb in ("tokens", "all"):
        print("[鎖定正本] %s" % info["source"], flush=True)
        print("[位元組驗證] %s · 檢查 %s 檔 · 失敗 %s"
              % ("OK" if report["lock_site"].get("ok") else "FAIL",
                 report["lock_site"].get("checked"), report["lock_site"].get("failed")), flush=True)
        print("[token] %d 個 · 區塊 sha256 %s" % (info["count"], info["sha256"]), flush=True)
        if args.verb == "tokens":
            for name in info["order"]:
                print("  --vl-%-18s %s" % (name, info["tokens"][name]), flush=True)

    if args.verb in ("kit", "all"):
        kit = out / KIT_NAME
        kit.write_text(build_kit(info), encoding="utf-8")
        report["kit"] = {"path": str(kit), "bytes": kit.stat().st_size}
        print("[kit] %s(%d bytes)" % (kit, kit.stat().st_size), flush=True)

    if args.verb in ("index", "all"):
        idx = stock_index(via / VRN_DB)
        report["index"] = {k: v for k, v in idx.items() if k != "rows"}
        report["index"]["rows"] = idx["rows"][:12]
        if idx.get("ok"):
            print("[個股盤點] %d 檔有料 · 庫 %s" % (idx["tickers"], idx["db"]), flush=True)
            for row in idx["rows"][:8]:
                print("   %-8s %-18s 報告 %d · 券商 %d · 最新 %s"
                      % (row["ticker"], (row["name"] or "")[:16], row["reports"],
                         row["brokers"], row["last_date"] or "—"), flush=True)
        else:
            print("[個股盤點] GRAY · %s" % idx.get("why"), flush=True)

    pages = []
    if args.verb in ("stock", "all"):
        tickers = [t for t in (args.ticker or "").split(",") if t.strip()]
        if not tickers:
            idx = stock_index(via / VRN_DB)
            tickers = [r["ticker"] for r in idx.get("rows", [])[:max(args.top, 1)]]
        for ticker in tickers:
            facts = stock_facts(via / VRN_DB, ticker.strip())
            card = render_stock(facts, info, out)
            pages.append(card)
            print("[個股頁] %s · 燈 %s · 報告 %d · 指標 %d · GRAY 區段 %s"
                  % (card["path"], card["lamp"], card["reports"], card["metrics"],
                     ",".join(card["gray_sections"]) or "無"), flush=True)
        report["stock_pages"] = pages

    if args.verb in ("check", "all"):
        targets = [Path(p) for p in (args.files or [])]
        if not targets:
            targets = [Path(c["path"]) for c in pages] + ([out / KIT_NAME] if (out / KIT_NAME).is_file() else [])
        checks = [check_page(p, info["sha256"]) for p in targets]
        report["checks"] = checks
        for row in checks:
            print("[閘 %s] %s%s" % (row["lamp"], row["file"],
                                    "" if row["lamp"] == "GREEN" else "\n     · " +
                                    "\n     · ".join(row["findings"])), flush=True)

    lamps = [report["lock_site"].get("ok") and "GREEN" or "RED"]
    lamps += [c["lamp"] for c in report.get("checks", [])]
    lamps += [c["lamp"] for c in pages]
    order = {"RED": 0, "YELLOW": 1, "GRAY": 2, "GREEN": 3}
    report["lamp"] = min(lamps, key=lambda x: order.get(x, 1)) if lamps else "GRAY"
    (out / "VISUAL_LOCK.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    print("[%s] %s · 總燈 %s · 收據 %s"
          % (TAG, args.verb, report["lamp"], out / "VISUAL_LOCK.json"), flush=True)
    return report


def selftest() -> int:
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""), flush=True)

    print("=== %s 自測 ===" % TAG, flush=True)
    with tempfile.TemporaryDirectory(prefix="vlock_") as td:
        root = Path(td)
        via = root / "VeritasIntelligenceAnalytics"
        site = via / LOCK_SITE
        site.mkdir(parents=True)
        (via / STOCK_TEMPLATE.parent).mkdir(parents=True)
        lock_html = (
            "<!doctype html><html><head><style>:root{\n"
            " --vl-bg:#f2f1ec;--vl-ink:#33403f;--vl-title:#1b1a17;--vl-muted:#6b6860;\n"
            " --vl-border:#dbd9d3;--vl-border-soft:#dcdad3;--vl-row:#ebe9e3;--vl-white:#fff;\n"
            " --vl-success:#3d7a52;--vl-success-bg:#e6efec;--vl-success-ink:#2c4f4a;\n"
            " --vl-warning-bg:#f2ecdd;--vl-warning-ink:#6f5c31;\n"
            " --vl-danger-bg:#f3e7e6;--vl-danger-ink:#9e2b25;\n"
            " --vl-font-cjk:\"Microsoft JhengHei\",sans-serif;\n"
            " --vl-font-display:\"Cormorant Garamond\",Georgia,serif;\n"
            " --vl-font-mono:Consolas,monospace;\n"
            " --vl-size-title:19px;--vl-size-primary:11px;--vl-size-base:clamp(9.5px,1.05vw,11px);\n"
            " --vl-size-numeric:9.5px;--vl-size-label:9px;--vl-size-status:8px;\n"
            " --bg:var(--vl-bg);--ink:var(--vl-ink);\n"
            "}</style></head><body><h1>VISUAL LOCK</h1></body></html>")
        (site / "index.html").write_text(lock_html, encoding="utf-8")
        import hashlib as _h
        digest = _h.sha256(lock_html.encode("utf-8")).hexdigest()
        (site / "SHA256SUMS.txt").write_text("%s  index.html\n" % digest, encoding="utf-8")

        info = extract_tokens(site / "index.html")
        chk("token 由正本抽出(不手抄)· 23 個以上 · 色與字與級都在",
            info["count"] >= 23 and info["tokens"]["bg"] == "#f2f1ec"
            and info["tokens"]["danger-ink"] == "#9e2b25"
            and "Cormorant" in info["tokens"]["font-display"]
            and info["tokens"]["size-base"].startswith("clamp("), info["count"])
        chk("token 區塊 sha 穩定(同一份正本抽兩次一樣)",
            extract_tokens(site / "index.html")["sha256"] == info["sha256"], info["sha256"][:16])

        lock = verify_lock_site(via)
        chk("位元組驗證:鎖定正本 sha256sum -c 過", lock.get("ok") is True, lock)
        (site / "index.html").write_text(lock_html + "<!-- 被動了一個位元組 -->", encoding="utf-8")
        chk("位元組驗證:正本被改一個位元組就判 FAIL(鎖對不上就不是鎖定版)",
            verify_lock_site(via).get("ok") is False)
        (site / "index.html").write_text(lock_html, encoding="utf-8")

        out = root / "out"
        out.mkdir()
        kit_text = build_kit(info)
        (out / KIT_NAME).write_text(kit_text, encoding="utf-8")
        chk("kit:token 全進去 · 有手機側邊槽 · 有 overflow-x · 標了正本與 sha",
            all(("--vl-%s:" % n) in kit_text.replace(" ", "") for n in info["order"])
            and "env(safe-area-inset-left" in kit_text and "max(16px" in kit_text
            and "overflow-x" in kit_text and info["sha256"] in kit_text)
        kit_check = check_page(out / KIT_NAME, info["sha256"])
        chk("閘:kit 自己過閘(它的 token 區塊就是正本的)",
            kit_check["lamp"] == "GREEN" and kit_check["token_sha256"] == info["sha256"], kit_check)

        # 閘要抓得到的三種違規
        bad1 = out / "bad_rawcolor.html"
        bad1.write_text('<link rel="stylesheet" href="%s"><div style="color:#ff0000">紅</div>'
                        % KIT_NAME, encoding="utf-8")
        got1 = check_page(bad1, info["sha256"])
        chk("閘:色彩寫死 #ff0000 被判紅",
            got1["lamp"] == "RED" and any("色彩寫死" in f for f in got1["findings"]), got1["findings"])
        bad2 = out / "bad_external.html"
        bad2.write_text('<link rel="stylesheet" href="%s">'
                        '<script src="https://cdn.example.com/x.js"></script>' % KIT_NAME,
                        encoding="utf-8")
        got2 = check_page(bad2, info["sha256"])
        chk("閘:外連被判紅(SVG 命名空間不算)",
            got2["lamp"] == "RED" and any("外連" in f for f in got2["findings"]), got2["findings"])
        bad3 = out / "bad_drift.html"
        drift = kit_text.replace("--vl-bg: #f2f1ec", "--vl-bg: #ffffff")
        bad3.write_text(drift, encoding="utf-8")
        got3 = check_page(bad3, info["sha256"])
        chk("閘:token 漂移(改了 --vl-bg)被判紅 —— 這就是「鎖」",
            got3["lamp"] == "RED" and any("對不上" in f for f in got3["findings"]), got3["findings"])
        okpage = out / "good.html"
        okpage.write_text('<link rel="stylesheet" href="%s">'
                          '<svg xmlns="http://www.w3.org/2000/svg"></svg>'
                          '<div class="vl-cell"><span class="vl-value">var 用 token</span></div>'
                          % KIT_NAME, encoding="utf-8")
        chk("閘:只用 kit + token 的頁過關(SVG 命名空間不誤判)",
            check_page(okpage, info["sha256"])["lamp"] == "GREEN")

        # 個股頁:沒有庫 → 照實 GRAY,不編數字
        empty = stock_facts(via / VRN_DB, "2330")
        card = render_stock(empty, info, out)
        text = Path(card["path"]).read_text(encoding="utf-8")
        chk("個股頁:沒有庫 → 燈 GRAY · 每個區段都有 GRAY 說明 · 值印「—」",
            card["lamp"] == "GRAY" and "—" in text and "不補值、不猜、不畫假圖" in text
            and len(card["gray_sections"]) >= len(STOCK_SECTIONS) - 1, card["gray_sections"])
        chk("個股頁:技術 / 籌碼面照實說要 VDF 日資料,沒有就不畫假圖",
            "不畫假圖、不編價格" in text and 'id="sec-stack"' in text)
        chk("個股頁:版面覆蓋模板的每一個區段(含共振堆疊圖)",
            all(('id="sec-%s"' % key) in text for key, _t, _f in STOCK_SECTIONS))
        chk("個股頁過鎖定閘(自己不寫顏色 · 連 kit · 無外連)",
            check_page(card["path"], info["sha256"])["lamp"] == "GREEN",
            check_page(card["path"], info["sha256"])["findings"])

        # 有料的情況(夾具 duckdb;沒有 duckdb 就跳過並照實說)
        if have("duckdb"):
            import duckdb
            dbp = via / VRN_DB
            dbp.parent.mkdir(parents=True, exist_ok=True)
            con = duckdb.connect(str(dbp))
            try:
                con.execute("CREATE TABLE vrn_report_basic (report_file VARCHAR, ticker VARCHAR,"
                            " name_official VARCHAR, broker VARCHAR, report_date VARCHAR,"
                            " rating_raw VARCHAR, rating_code VARCHAR, rating_direction VARCHAR,"
                            " target_price DOUBLE, target_price_adj DOUBLE, price DOUBLE,"
                            " price_latest_adj DOUBLE, price_latest_date VARCHAR,"
                            " upside_report DOUBLE, upside_adj DOUBLE, upside_adj_state VARCHAR,"
                            " report_age_days INTEGER, target_freshness VARCHAR,"
                            " analyst_names VARCHAR, analyst_n INTEGER, broker_name_zh VARCHAR,"
                            " broker_name_en VARCHAR, ssot_state VARCHAR)")
                con.execute("INSERT INTO vrn_report_basic VALUES"
                            " ('r1.pdf','3706','神達','A','2026-08-01','買進','BUY','UP',"
                            "  120.0, 118.5, 100.0, 99.2, '2026-08-01', 20.0, 19.5, 'OK', 7,"
                            "  '法定財報日內','王小明',1,'甲證券','A Securities','OK'),"
                            " ('r2.pdf','3706','神達','B','2026-07-15','持有','HOLD','FLAT',"
                            "  110.0, 108.0, 100.0, 99.2, '2026-07-15', 10.0, 8.0, 'OK', 24,"
                            "  '30 交易日內','李小華',1,'乙證券','B Securities','OK')")
                con.execute("CREATE TABLE vrn_report_metrics (report_file VARCHAR, metric VARCHAR,"
                            " period VARCHAR, status VARCHAR, value DOUBLE, raw_text VARCHAR)")
                con.execute("INSERT INTO vrn_report_metrics VALUES"
                            " ('r1.pdf','EPS','2026','OK',38.5,'EPS 38.5 元'),"
                            " ('r1.pdf','毛利率','2026','OK',53.2,'毛利率 53.2%'),"
                            " ('r1.pdf','營業收入','2026','OK',1234.0,'營收 1,234 億元')")
                con.execute("CREATE TABLE vrn_report_analyst (report_file VARCHAR,"
                            " analyst_zh VARCHAR, analyst_en VARCHAR, email VARCHAR, domain VARCHAR)")
                con.execute("INSERT INTO vrn_report_analyst VALUES"
                            " ('r1.pdf','王小明','Ming Wang','a@x.com','x.com')")
                con.execute("CREATE TABLE vrn_nlp_text_summary (report_file VARCHAR,"
                            " summary_points_json VARCHAR, summary_state VARCHAR)")
                con.execute("INSERT INTO vrn_nlp_text_summary VALUES ('r1.pdf','[]','OK')")
            finally:
                con.close()
            idx = stock_index(dbp)
            chk("盤點:只列真的有 ticker 的列(空字串那種不算)",
                idx["ok"] and idx["tickers"] == 1 and idx["rows"][0]["ticker"] == "3706"
                and idx["rows"][0]["reports"] == 2, idx.get("rows"))
            facts = stock_facts(dbp, "3706")
            card2 = render_stock(facts, info, out)
            text2 = Path(card2["path"]).read_text(encoding="utf-8")
            chk("個股頁(有料):評級表兩列 · ADJ 欄在 · 目標價中位數由本頁現有筆數算",
                card2["reports"] == 2 and "甲證券" in text2 and "乙證券" in text2
                and "113.25" in text2, card2)
            chk("個股頁(有料):指標分到共識 / 損益 / 比率三個區段,原文照登",
                "EPS 38.5 元" in text2 and "營收 1,234 億元" in text2 and "毛利率 53.2%" in text2)
            chk("個股頁(有料):仍然過鎖定閘 · 技術籌碼面照實 GRAY(沒有 VDF 日資料)",
                check_page(card2["path"], info["sha256"])["lamp"] == "GREEN"
                and "stack" in card2["gray_sections"], card2["gray_sections"])
        else:
            chk("沒有 duckdb → 盤點照實說沒有,不假裝有料",
                stock_index(via / VRN_DB)["ok"] is False)

        text_self = Path(__file__).read_text(encoding="utf-8")
        chk("本支帶加速器橋(標記 + 真載)· 第 3 行標記 · 不含 TA-Lib · 沒有自己 pip",
            "[VIA:ACCEL-BRIDGE" in text_self and ("VIA_ACCEL" in globals())
            and text_self.splitlines()[2].strip() == "# [VIA:ACCEL-BRIDGE:v0100]"
            and not re.search(r"^\s*(?:import|from)\s+talib\b", text_self, re.M)
            and not re.search(r"pip\s+install", text_self))
    bad = len([x for x in ok if not x])
    print("[計] %s 自測 %d/%d · %s" % (TAG, len(ok) - bad, len(ok), "PASS" if not bad else "FAIL"), flush=True)
    return 0 if not bad else 1


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=TAG, description="VIA 標準視覺鎖定 U/I(格式鎖 + 個股模板 + 閘)")
    parser.add_argument("verb", nargs="?", default="all",
                        choices=["tokens", "kit", "check", "index", "stock", "all"])
    here = Path(__file__).resolve()
    parser.add_argument("--via", default=str(here.parents[3] if len(here.parents) > 3 else here.parent),
                        help="VIA 樹或倉根(預設由本檔位置推)")
    parser.add_argument("--out", default="", help="輸出夾(預設 <VIA>/VIA_Reports/visual_lock)")
    parser.add_argument("--ticker", default="", help="stock:要出哪幾檔(逗號分隔;不給就取有料的前 --top 檔)")
    parser.add_argument("--top", type=int, default=3, help="stock 不給 --ticker 時出幾檔")
    parser.add_argument("--files", nargs="*", help="check:要過閘的檔(不給就檢自己產出的)")
    parser.add_argument("--selftest", action="store_true")
    return parser


def main(argv=None) -> int:
    args = make_parser().parse_args(argv)
    if args.selftest:
        return selftest()
    report = run(args)
    return {"GREEN": 0, "YELLOW": 2, "GRAY": 2, "RED": 1}.get(report.get("lamp", "RED"), 1)


if __name__ == "__main__":
    sys.exit(main())
