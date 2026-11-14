#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN2_Workbench v0109 — v0108 薄尾(v0108 與它的前版一字不改):字型字級以「細節 / Detail」為準 · 系統摘要矩陣燈號化 · 表頭雙行 · 左欄步驟。

操作員 2026-11-03:
  「字體大小及格式一致性 · 以 細節 / Detail 的字型及字體大小為主 · 整字小一點比較專業 · 資料不可超過卡片及格子」
  「資料驗證狀況放入系統現況並將名稱改為系統摘要 · 所有資訊都矩陣化、燈號化 · 尚未跨越的驗收條件特別亂」
  「不用括號說明 · 若有備註說明放底下 · 全形中文字及標點符號 · header 呈現方式要統一、寫完整 · 中英文並存太長可換行
    (FactSet 目標價中位數 · FactSet 分析師人數)」
  「左面板文字說明雜亂 · 用不突兀的步驟編號帶領使用者逐步完成輸入設定」
  「BROKER 一律英文縮寫 · 輸出冊和增量庫也實體加 Source 欄」(實體欄由 VRN2_BookSource v0100 / OutputStore v0103 寫;本版顯示時優先用實體欄)
  「輸入資料夾的 Word / 影像有處理嗎 · 有分 STOCK REPORT / NON-STOCK REPORT / NEWS 嗎」(01 頁新增輸入分類矩陣)

做法(window.VRN2_DATA 一字不改 · 前版規則:U/I 匯出 = 輸出冊):
  ① 字型:全頁內文 = 細節欄字型 Consolas + 微軟正黑體(中文後援)10.45px;區段標題 11px;表頭 / 標籤 9px;標記 8px;
     只有頁首品牌與系統摘要大標、統計數字保留模板的 Cormorant Garamond 19px。顏色只用 ENG049 模板 15 色。CSS SHA-256 釘在本檔。
  ② 00 頁改名「系統摘要」;原本在頁首上方的「資料驗證狀況」改成系統摘要裡的一段矩陣(燈號 · 項目 · 細節)+ 共識矩陣
     (FactSet 目標價中位數 · Yahoo 目標價中位數 · FactSet 分析師人數 · Yahoo 分析師人數 · 兩源檢核)· 說明一律放在矩陣下方的「註」。
  ③ 04 頁「尚未跨越的驗收條件」改成「待驗收項目」矩陣(燈號 · 類別 · 項目 · 細節 · 次數 · 同項合併計次 · 紅先黃後)。
  ④ 表頭統一:英文一行 + 中文一行(資料頁、各表、系統摘要欄頭、卡片標籤都一樣);括號說明移到表下的註;
     標題括號說明移到該卡片底下的註;中文旁的半形括號、冒號、逗號改全形(檔名、路徑、資料值不動)。
  ⑤ 左欄:步驟 1 選擇報告來源 → 2 確認輸入 → 3 啟動處理 → 4 輸出位置 → 5 開啟資料夾 → 6 其他系統;
     小圓圈編號(完成的步驟綠框)· 按鈕去掉圖示與括號 · 說明文字移到左欄最底下的註。
  ⑥ 資料頁:冊裡已有 SOURCE / BROKER_EN 實體欄 → 直接用(不重複加欄 · BROKER_EN 不另列 · 券商欄顯示縮寫);
     MarketConsensus 自己的 SOURCE 欄照原位原值;匯出不重複 SOURCE。
  ⑦ 01 頁輸入分類矩陣:個股報告 · 非個股報告 · 新聞與盤勢 · 頁面影像 · 未分類 × PDF / Word / TXT / 影像 / 其他 · 處理方式
     (檔名初判 · 候選規則 · 個股範圍仍以 VRN SystemManager 的判定為準 · 本版主體只擷取 PDF)。
動詞同前版:render · logo · --selftest。
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import html
import importlib.util
import json
import re
import sys
from pathlib import Path

VERSION = "v0109"
DISPLAY_NAME = "VRN2_Workbench"
PRIOR_NAME = "VRN2_Workbench_v0108.py"
HERE = Path(__file__).resolve().parent


def _load_prior():
    path = HERE / PRIOR_NAME
    if not path.is_file():
        raise FileNotFoundError("前版 %s 不在 %s" % (PRIOR_NAME, HERE))
    spec = importlib.util.spec_from_file_location("vrn2_workbench_prior_v0108_for109", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PRIOR = _load_prior()               # v0108
W107 = PRIOR.PRIOR                  # v0107(驗證列 · 共識 · 欄註)
PALETTE = PRIOR.PALETTE
SIZES_PX = (19, 11, 10.45, 9, 8)
F_TEXT = 'Consolas,"Microsoft JhengHei","Segoe UI",monospace'

_CSS = """<style id="wb109-tpl">/* VRN2_Workbench v0109 · 字型字級以「細節 / Detail」為準(Consolas + 微軟正黑體 10.45px)· 色票照 ENG049 模板 15 色 · 字級 19 / 11 / 10.45 / 9 / 8 px */
:root{--w9f:Consolas,"Microsoft JhengHei","Segoe UI",monospace;--w9s:10.45px;--w9l:9px;--w9t:8px}
body,main,aside,.box,table,td,button,a.action,input,select,textarea,.subtle,.ask,.dialog-note,.unitnote,.kv .cell b,.kv .cell .d,.sm-lb,.sm-dt,.sm-l,.sm-sl,.sm-leg,.sm-state,.sm-empty,.sm-ep,.sm-sb,.sm-db,.sm-sub,.sm-mut,.lamps div,#drop,pre,.outfolder .path,td.n,.mono,.w9-mx td{font-family:var(--w9f)!important}
body,main,aside,.box,td,.subtle,.ask,.dialog-note,.unitnote,.kv .cell b,.kv .cell .d,.sm-lb,.sm-dt,.sm-l,.sm-sl,.sm-leg,.sm-state,.sm-ep,.sm-sb,.sm-db,.sm-sub,.sm-mut,.lamps div,#drop,pre,.outfolder .path,td.n,.mono,button,a.action,input,select{font-size:var(--w9s)!important;line-height:1.45}
h2{font:700 11px var(--w9f)!important;color:#1b1a17;letter-spacing:.02em}
h3,.sm-sect,.sm-colh,.kv .cell small,.stat small,.frm label,th,.tabs button{font-family:var(--w9f)!important;font-size:var(--w9l)!important}
.pill,.w8tag,.sm-badge,.sm-st,.sm-src,.sm-h,.w9-st{font-family:var(--w9f)!important;font-size:var(--w9t)!important}
.sm-lb{font-weight:700!important;color:#1b1a17}
header.vh h1,.sm-title,.sm-sn,.sm-n,.stat b{font-size:19px!important}
.w9h{display:inline-flex;flex-direction:column;gap:1px;line-height:1.25;white-space:normal}
.w9en{font:700 var(--w9l) var(--w9f);letter-spacing:.05em;text-transform:uppercase;color:#6b6860}
.w9zh{font:400 var(--w9l) var(--w9f);letter-spacing:.02em;text-transform:none;color:#6b6860;word-break:keep-all}
.box,.sm,.sm-sec,.sm-mx,.matrix,.kv,.kv .cell,.sm-c,.sm-card,.sm-stat,.cards>*,.stat,.lamps div,.outfolder,aside,.w9-wrap{min-width:0;box-sizing:border-box}
.kv .cell,.kv .cell .d,.kv .cell b,.sm-c,.sm-ep,.sm-lb,.sm-sb,.sm-db,.sm-l,.subtle,.dialog-note,.outfolder,.outfolder .path,.w9-mx td,.lamps div,#drop,.sm-card,.stat,td,.w9-src{overflow-wrap:anywhere;word-break:break-word}
.matrix,.sm-mx,.w9-wrap{max-width:100%;overflow-x:auto}
#dsBody td{max-width:30em;white-space:normal}
.w9-sec{margin:0 0 16px}
.w9-sect{display:flex;justify-content:space-between;align-items:baseline;gap:12px;margin:0 0 6px;flex-wrap:wrap}
.w9-wrap{border:1px solid #dbd9d3;border-radius:8px;background:#ffffff}
table.w9-mx{width:100%;border-collapse:collapse;table-layout:auto;background:#ffffff}
table.w9-mx th{background:#ffffff;text-align:left;vertical-align:bottom;padding:6px 8px;border-bottom:1px solid #dbd9d3;position:sticky;top:0}
table.w9-mx td{padding:5px 8px;border-bottom:1px solid #ebe9e3;vertical-align:top;font-weight:400;font-size:var(--w9s);line-height:1.45;color:#33403f}
table.w9-mx tr:last-child td{border-bottom:none}
table.w9-mx td.w9-k{white-space:nowrap;width:1%}
table.w9-mx td.n{text-align:right;white-space:nowrap;width:1%}
table.w9-mx tr.w9-tot td{border-top:1px solid #dbd9d3;font-weight:700;color:#1b1a17}
table.w9-mx th .w9en,table.w9-mx th .w9zh{white-space:nowrap}
#wb107b .w9-notes{margin-top:6px}
.w9-item b{display:block;font-weight:700;color:#1b1a17}
.w9-item span{display:block;font-size:var(--w9l);letter-spacing:.04em;text-transform:uppercase;color:#6b6860}
.w9-det{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;cursor:pointer}
tr.w9-open .w9-det{display:block;-webkit-line-clamp:unset}
.w9-st{display:inline-flex;align-items:center;gap:5px;padding:1px 7px;border-radius:9px;font-weight:700;letter-spacing:.05em;white-space:nowrap;background:#ebe9e3;color:#6b6860}
.w9-st i{width:6px;height:6px;border-radius:50%;background:currentColor;display:inline-block}
.w9-st.GREEN{background:#e6efec;color:#2c4f4a}.w9-st.YELLOW{background:#f2ecdd;color:#6f5c31}.w9-st.RED{background:#f3e7e6;color:#9e2b25}.w9-st.GRAY{background:#ebe9e3;color:#6b6860}
.w9-cnt{font:400 var(--w9l) var(--w9f);letter-spacing:.04em;color:#6b6860}
.w9-e{font:700 var(--w9t) var(--w9f);letter-spacing:.08em;text-transform:uppercase;color:#6b6860;margin-left:6px}
.w9-notes{margin:8px 0 0;padding:6px 0 0 18px;border-top:1px dashed #dcdad3;font:400 var(--w9l)/1.55 var(--w9f);color:#6b6860}
.w9-notes li{margin:1px 0}.w9-notes b{color:#33403f}
.w9-ptitle{display:inline-flex;align-items:baseline;gap:8px}
.w9-ptitle b{font:700 11px var(--w9f);color:#1b1a17}
.w9-ptitle span{font:700 var(--w9t) var(--w9f);letter-spacing:.08em;text-transform:uppercase;color:#6b6860}
.w9-stepbox{padding:9px 0 10px;border-top:1px solid #ebe9e3}
.w9-step{display:flex;align-items:center;gap:7px;margin:0 0 7px}
.w9-n{width:16px;height:16px;border:1px solid #dcdad3;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;flex:none;font:700 var(--w9t) var(--w9f);color:#6b6860;background:#ffffff}
.w9-step.done .w9-n{border-color:#3d7a52;color:#3d7a52}
.w9-t{font:700 var(--w9s) var(--w9f);color:#1b1a17}
.w9-step .w9-e{margin-left:auto}
.w9-row2,.w9-row3{display:grid;gap:5px;margin-top:5px}
.w9-row2{grid-template-columns:repeat(2,minmax(0,1fr))}
.w9-row3{grid-template-columns:repeat(3,minmax(0,1fr))}
.w9-row2 a.action,.w9-row3 a.action{margin:0;padding:5px 4px;text-align:center;font-size:var(--w9l)!important;font-weight:600}
.w9-kv{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:4px;margin:6px 0 0}
.w9-kv div{border:1px solid #ebe9e3;border-radius:6px;padding:3px 5px;background:#ffffff;min-width:0}
.w9-kv small{display:block;font:700 var(--w9t) var(--w9f);letter-spacing:.05em;text-transform:uppercase;color:#6b6860}
.w9-kv b{font:700 var(--w9s) var(--w9f);color:#1b1a17}
.w9-src{font:400 var(--w9l) var(--w9f);color:#6b6860;margin-top:5px}
</style>"""
CSS_SHA256 = "739a2a9d93198a422ba2ac9e47ee395b3b2a30aa3fddda2bf3becae28fab54f5"      # 建置時填(鎖定:CSS 一改就對不上 → 自測紅 → 要出新版)

# ── 表頭字典(英文一行 + 中文一行 · 第三格 = 放到表下的註)─────────────────────────────────────────────
_MONEY = "金額欄以百萬台幣顯示"
CODE_HDR = {
    "REPORT_DATE": ["Report Date", "報告日期"], "FILENAME": ["File Name", "檔案名稱"], "TICKER": ["Ticker", "股票代號"],
    "YFINANCE_TICKER": ["Yahoo Ticker", "Yahoo 代號"], "BLOOMBERG_TICKER": ["Bloomberg Ticker", "彭博代號"], "NAME": ["Company Name", "公司名稱"],
    "ENGLISH_NAME": ["English Name", "英文名稱"], "BROKER": ["Broker", "券商"], "BROKER_EN": ["Broker Abbreviation", "券商英文縮寫"],
    "ANALYST": ["Analyst", "分析師"], "EMAIL": ["Email", "電子郵件"], "TEL": ["Telephone", "電話"], "TITLE": ["Title", "標題"], "RATING": ["Rating", "評等"],
    "TARGET_PRICE": ["Target Price", "目標價"], "TARGET_PRICE(ADJ)": ["Adjusted Target Price", "調整後目標價"],
    "CURRENT_PRICE_REPORT": ["Price at Report", "報告發布時股價"], "UPSIDE_PCT": ["Upside %", "潛在上漲空間百分比"],
    "UPSIDE_PCT(ADJ)": ["Adjusted Upside %", "調整後上漲空間百分比"], "UPSIDE_ADJ": ["Adjusted Upside", "調整後上漲空間"],
    "ADJ_CLOSE": ["Adjusted Close", "調整後收盤價"], "ADJ_CLOSE_BEFORE_REPORT": ["Adjusted Close Before Report", "報告前調整後收盤價"],
    "TOPIC & SUMMARY": ["Topic and Summary", "主題與摘要"], "STATUS": ["Status", "狀態"], "_STATUS": ["Status", "狀態"],
    "FACTSET_TARGET_PRICE_MEDIAN": ["FactSet TP Median", "FactSet 目標價中位數"], "YFINANCE_TARGET_PRICE_MEDIAN": ["Yahoo TP Median", "Yahoo 目標價中位數"],
    "FACTSET_ANALYST_COUNT": ["FactSet Analysts", "FactSet 分析師人數"], "YFINANCE_ANALYST_COUNT": ["Yahoo Analysts", "Yahoo 分析師人數"],
    "MEDIAN_GAP_PCT": ["Median Gap %", "兩源中位數差距百分比"], "UPSIDE_FACTSET_PCT": ["Upside vs FactSet %", "FactSet 上漲空間百分比"],
    "UPSIDE_YFINANCE_PCT": ["Upside vs Yahoo %", "Yahoo 上漲空間百分比"], "SOURCE_AGREEMENT_GATE": ["Source Check", "兩源檢核"], "QUALITY": ["Quality", "品質"],
    "FETCHED_AT": ["Fetched At", "擷取時間"], "DATE": ["Date", "日期"], "MARKET": ["Market", "市場"], "PRICE_DATE": ["Price Date", "價格日期"],
    "CLOSE": ["Close", "收盤價"], "VOLUME": ["Volume", "成交量"], "ADJUSTMENT_STATUS": ["Adjustment Status", "還原狀態"],
    "PAGE": ["Page", "頁碼"], "TABLE": ["Table", "表格"], "ITEM": ["Item", "科目"], "PERIOD": ["Period", "期間"], "VALUE": ["Value", "數值", _MONEY],
    "VERIFY": ["Verify", "驗證"], "ROW": ["Row", "列號"], "SECTION": ["Section", "段落"], "ITEM_RAW": ["Item Raw", "科目原文"], "SUBCOL": ["Sub Column", "子欄"],
    "POINT_1": ["Point 1", "重點一"], "POINT_2": ["Point 2", "重點二"], "POINT_3": ["Point 3", "重點三"], "POINT_4": ["Point 4", "重點四"], "POINTS_OK": ["Points OK", "重點數"],
    "VALUE_REPORT": ["Report Value", "報告值", _MONEY], "VALUE_FINAL": ["Final Value", "最終值", _MONEY], "UNIT_FINAL": ["Unit", "單位"],
    "VALUE_SOURCE": ["Value Source", "值來源"], "RECON_RATIO": ["Recon Ratio", "核對比值"], "RECON_DIFF": ["Recon Difference", "核對差"], "SCALE": ["Scale", "倍率"],
    "STD": ["Standard Item", "標準科目"], "YEAR": ["Year", "年度"], "KIND": ["Kind", "類別"], "DELETED_REASON": ["Deleted Reason", "刪除理由"],
    "HISTORY_VALUE": ["History Value", "歷史值", _MONEY], "UNIT_HISTORY": ["History Unit", "歷史單位"], "BOOK": ["Book", "冊別"], "REASON": ["Reason", "理由"],
    "FIELD": ["Field", "欄位"], "FRESH": ["Freshness", "時效"], "TICKER_YF": ["Ticker / YFinance", "股票代號\uff0fYahoo 代號"], "SOURCE": ["Source", "來源"],
}
TXT_HDR = {      # 頁面上寫死的表頭原文 → (英文, 中文)
    "FactSet Median": ["FactSet TP Median", "FactSet 目標價中位數"], "YFinance Median": ["Yahoo TP Median", "Yahoo 目標價中位數"],
    "FactSet 中位數": ["FactSet TP Median", "FactSet 目標價中位數"], "Yahoo 中位數": ["Yahoo TP Median", "Yahoo 目標價中位數"],
    "FactSet 人數": ["FactSet Analysts", "FactSet 分析師人數"], "Yahoo 人數": ["Yahoo Analysts", "Yahoo 分析師人數"], "兩源閘": ["Source Check", "兩源檢核"],
    "Upside (Adj) / 上漲空間(還原)": ["Adjusted Upside", "調整後上漲空間"], "上漲空間(還原)": ["Adjusted Upside", "調整後上漲空間"],
    "目標價(還原)": ["Adjusted Target Price", "調整後目標價"], "還原收盤": ["Adjusted Close", "調整後收盤價"], "報告日": ["Report Date", "報告日期"],
    "Ticker / YFinance": ["Ticker / YFinance", "股票代號\uff0fYahoo 代號"],
}
ZH2EN = {
    "格式": "Format", "唯一": "Unique", "完全重複 多餘副本": "Exact Duplicates", "候選重複": "Candidate Duplicates", "個股範圍外": "Out of Scope", "合計": "Total",
    "版本": "Version", "提交時間": "Committed At", "狀態": "Status", "修改時間": "Modified At", "候選群組": "Candidate Group", "刪除區": "Deleted Zone", "勾選": "Select",
    "單位倍率": "Unit Scale", "報告名稱": "Report", "完全重複指紋": "Exact Fingerprint", "容量 bytes": "Size", "對上期數": "Matched Periods", "引擎／功能": "Engine",
    "檢驗通過": "Checks Passed", "燈 / 說明": "Lamp and Note", "版本與狀態": "Version and Status", "生產／驗證": "Production and Verification", "覆蓋格": "Overridden Cells",
    "規格": "Specification", "輸入": "Input", "輸出": "Output", "檔案": "File", "代號": "Ticker", "名稱": "Name", "券商": "Broker", "評等": "Rating", "目標價": "Target Price",
    "① 計算驗證": "① Calculation", "② 覆蓋": "② Coverage", "③ 回原文": "③ Source Trace", "⑤ 一標題四重點": "⑤ Title and Points", "⑦ 基本資料雙讀": "⑦ Dual Read",
    "已登記入口": "Registered Entry", "啟動器": "Launcher", "管理器": "Manager", "冪等閘": "Idempotence Gate", "四點原文核對": "Verbatim Points",
    "⑥e 市場擷取 TWSE / TPEX / Yahoo": "Market Fetch ⑥e", "⑬ 輸出位置 · 增量庫": "Output and Store ⑬", "⑬b 歷史對齊": "History Alignment ⑬b",
    "⑬c 舊資料庫整合": "Legacy Integration ⑬c", "⑤b SSOT-ID 核號同步": "SSOT-ID Sync ⑤b",
}
EN2ZH = {"BasicInfo": "基本資料", "FinancialData": "年度數據", "Summary": "一標題四重點", "Combined": "合併摘要", "Rejected": "剔除冊", "FinancialAligned": "歷史對齊",
         "Deleted": "刪除區", "MarketConsensus": "市場共識", "UPSIDE ADJ": "調整後上漲空間", "Ticker / YFinance": "股票代號\uff0fYahoo 代號"}

VNAME = {   # v0107 驗證列名 → (英文, 中文 · 不帶括號)
    "原文值核對(VerbatimVerify)": ("Verbatim Check", "原文值核對"), "獨立驗證(IndependentVerifier)": ("Independent Verification", "獨立驗證"),
    "冪等(同輸入同輸出)": ("Idempotence", "冪等 · 同輸入同輸出"), "完成判定": ("Completion", "完成判定"),
    "市場資料 ⑥e(TWSE / TPEX / Yahoo)": ("Market Data ⑥e", "市場資料 TWSE/TPEX/Yahoo"), "共識 ⑥f(FactSet × Yahoo)": ("Consensus ⑥f", "共識 FactSet × Yahoo"),
    "歷史對齊 ⑬b": ("History Alignment ⑬b", "歷史對齊"), "增量庫 ⑬(DuckDB / Parquet)": ("Incremental Store ⑬", "增量庫 DuckDB/Parquet"),
    "Combined 共識欄": ("Combined Consensus", "Combined 共識欄"), "Basic Info · 合併檢視": ("Basic Info Merge", "基本資料合併檢視"),
    "上漲空間 新欄 × 舊欄": ("Upside Columns", "上漲空間新舊欄互核"), "歷史對齊 Parquet": ("History Parquet", "歷史對齊 Parquet"),
}
LAMPS = ("RED", "YELLOW", "GRAY", "GREEN")

# ── 輸入分類(檔名初判 · 候選規則)────────────────────────────────────────────────────────────────────
NEWS_KW = ("晨會", "晨報", "早報", "盤後", "盤勢", "盤前", "晨間", "解盤", "新聞", "快訊", "市場觀察", "日股分析", "港股分析", "美股分析", "陸股分析", "籌碼追蹤",
           "morning", "daily", "news", "flash")
PAGE_IMG = re.compile(r"^(page|p)[_-]?\d{1,4}\.(png|jpe?g|tiff?|bmp|gif|webp)$", re.I)
_EXT = {"pdf": "PDF", "doc": "WORD", "docx": "WORD", "rtf": "WORD", "odt": "WORD", "txt": "TXT", "md": "TXT",
        "png": "IMG", "jpg": "IMG", "jpeg": "IMG", "tif": "IMG", "tiff": "IMG", "bmp": "IMG", "gif": "IMG", "webp": "IMG", "heic": "IMG"}
CLASSES = (("STOCK", "Stock Report", "個股報告"), ("NONSTOCK", "Non-Stock Report", "非個股報告"), ("NEWS", "News and Market Notes", "新聞與盤勢"),
           ("PAGE", "Page Image", "頁面影像"), ("UNCLASSIFIED", "Unclassified", "未分類"))
TYPES = (("PDF", "PDF", "PDF"), ("WORD", "Word", "Word"), ("TXT", "TXT", "文字檔"), ("IMG", "Image", "影像"), ("OTHER", "Other", "其他型別"))
PROCESS = {"STOCK": "PDF 進入擷取 · 非 PDF 收下未擷取", "NONSTOCK": "範圍外 · 不擷取", "NEWS": "範圍外 · 不擷取", "PAGE": "衍生頁面影像 · 不擷取",
           "UNCLASSIFIED": "收下未擷取 · Word 需轉 PDF · 影像需 OCR"}


def ftype(name: str) -> str:
    return _EXT.get(name.rsplit(".", 1)[-1].lower(), "OTHER") if "." in name else "OTHER"


def classify(name: str, judged: str = "") -> str:
    """STOCK / NONSTOCK / NEWS / PAGE / UNCLASSIFIED。judged = VRN SystemManager 的判定(stock / out / "")。"""
    low = name.lower()
    if PAGE_IMG.match(name):
        return "PAGE"
    if judged == "stock":
        return "STOCK"
    if any(k in low for k in NEWS_KW):
        return "NEWS"
    if judged == "out":
        return "NONSTOCK"
    bare = re.sub(r"(19|20)\d{2}[01]\d[0-3]\d", "", name)
    if re.search(r"(?<!\d)\d{4}(?!\d)(?!年)", bare):
        return "STOCK"
    return "UNCLASSIFIED"


def input_classes(audit: dict) -> dict:
    """VRN2_Input_latest.json 的 audit → {類別: {型別: 份數}} + 名單截斷數。"""
    grid = {c: {t: 0 for t, _, _ in TYPES} for c, _, _ in CLASSES}
    by_type = {str(k).upper(): int(v or 0) for k, v in (audit.get("by_type") or {}).items()}
    grid["STOCK"]["PDF"] = int(audit.get("stock") or 0)
    outs = [str(n) for n in audit.get("out_names") or []]
    for n in outs:
        grid[classify(n, "out")]["PDF"] += 1
    rest_out = max(0, int(audit.get("out_of_scope") or 0) - len(outs))
    grid["NONSTOCK"]["PDF"] += rest_out
    listed = {t: 0 for t, _, _ in TYPES}
    for n in audit.get("non_pdf_names") or []:
        t = ftype(str(n))
        t = "OTHER" if t == "PDF" else t
        listed[t] += 1
        grid[classify(str(n))][t] += 1
    cut = 0
    for t in ("WORD", "TXT", "IMG"):
        left = max(0, by_type.get(t, 0) - listed[t])
        grid["UNCLASSIFIED"][t] += left
        cut += left
    other = int(audit.get("other_type") or 0)
    left_o = max(0, other - listed["OTHER"])
    grid["UNCLASSIFIED"]["OTHER"] += left_o
    cut += left_o
    return {"grid": grid, "truncated": cut, "files": int(audit.get("files") or 0), "rest_out": rest_out}


# ── 小工具 ───────────────────────────────────────────────────────────────────────────────────────────
_e = html.escape
_PATHY = re.compile(r"[A-Za-z]:\\|/[\w.\-]+/|\.(pdf|docx?|txt|png|jpe?g|json|csv|parquet|html?|py|zip|ps1)\b", re.I)
_FTAIL = re.compile(r"[^\s\u00b7,\uff0c]*\.(pdf|docx?|txt|png|jpe?g|json|csv|parquet|html?|py|zip|ps1)\b", re.I)
FW_L, FW_R, FW_COLON, FW_COMMA, FW_SEMI = "\uff08", "\uff09", "\uff1a", "\uff0c", "\uff1b"


def punct(s) -> str:
    """中文旁的半形括號 / 冒號 / 逗號 / 分號 → 全形(括號裡是路徑、或緊接著是檔名的不動 · 英文旁的不動)。"""
    s = "" if s is None else str(s)

    def par(m):
        pre = re.search(r"[^\s\u00b7]*$", s[:m.start()]).group(0)
        if _PATHY.search(m.group(1)) or _FTAIL.match(s, m.end()) or "\\" in pre or "://" in pre or pre.startswith("/"):
            return m.group(0)
        return FW_L + m.group(1) + FW_R
    s = re.sub(r"\(([^()]*[\u3400-\u9fff][^()]*)\)", par, s)
    s = re.sub("([\u3400-\u9fff\uff09])\\s*:\\s*", "\\1" + FW_COLON, s)
    s = re.sub("([\u3400-\u9fff\uff09]),\\s*", "\\1" + FW_COMMA, s)
    s = re.sub("([\u3400-\u9fff\uff09]);\\s*", "\\1" + FW_SEMI, s)
    return s


def zh(s: str) -> str:
    """本模組自己寫的中文說明:半形 : , ; ( ) 一律換全形(不含路徑與檔名才用)。"""
    return str(s).translate({ord(":"): FW_COLON, ord(","): FW_COMMA, ord(";"): FW_SEMI, ord("("): FW_L, ord(")"): FW_R})


def split_dot(t: str) -> list:
    """用「 · 」切段,括號裡的「 · 」不切。"""
    out, buf, depth, i = [], "", 0, 0
    while i < len(t):
        c = t[i]
        if c in "(\uff08":
            depth += 1
        elif c in ")\uff09":
            depth = max(0, depth - 1)
        if depth == 0 and t.startswith(" · ", i):
            out.append(buf.strip())
            buf, i = "", i + 3
            continue
        buf += c
        i += 1
    out.append(buf.strip())
    return [x for x in out if x != ""] or [""]


def w9h(en: str, zh: str) -> str:
    return '<span class="w9h">%s%s</span>' % (('<span class="w9en">%s</span>' % _e(en)) if en else "", ('<span class="w9zh">%s</span>' % _e(zh)) if zh else "")


def chip(lamp: str) -> str:
    lp = lamp if lamp in LAMPS else "GRAY"
    return '<span class="w9-st %s"><i></i>%s</span>' % (lp, lp)


def matrix(heads: list, rows: list, scroll: str = "") -> str:
    th = "".join("<th>%s</th>" % w9h(en, zh) for en, zh in heads)
    style = (' style="max-height:%s;overflow:auto"' % scroll) if scroll else ""
    return '<div class="w9-wrap"%s><table class="w9-mx"><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (style, th, "".join(rows))


def notes_html(items: list) -> str:
    items = [i for i in items if i]
    return ('<ol class="w9-notes">%s</ol>' % "".join("<li>%s</li>" % punct(i) for i in items)) if items else ""


def counts_line(lamps: list) -> str:
    n = {lp: sum(1 for x in lamps if x == lp) for lp in ("GREEN", "YELLOW", "RED", "GRAY")}
    return "綠 %d · 黃 %d · 紅 %d · 灰 %d" % (n["GREEN"], n["YELLOW"], n["RED"], n["GRAY"])


def _item(en: str, zh: str) -> str:
    return '<div class="w9-item"><b>%s</b><span>%s</span></div>' % (_e(zh), _e(en))


def _det(text: str) -> str:
    t = punct(str(text or "—"))
    return '<div class="w9-det" title="%s">%s</div>' % (_e(t[:1200]), _e(t[:1200]))


# ── ③ 待驗收項目 ─────────────────────────────────────────────────────────────────────────────────────
_ACC_BOX = re.compile(r'<div class="box">\s*<h2>尚未跨越的驗收條件</h2>(.*?)</div>', re.S)


def acceptance_rows(page: str) -> list | None:
    """04 頁「尚未跨越的驗收條件」→ [(燈, 類別, 項目, 細節, 次數)] · 同項合併計次 · 紅先黃後;沒有這格 → None。"""
    m = _ACC_BOX.search(page)
    if not m:
        return None
    seen, order = {}, []
    for raw in re.findall(r"<p[^>]*>(.*?)</p>", m.group(1), re.S):
        t = html.unescape(re.sub(r"<[^>]+>", "", raw)).strip().lstrip("·").strip()
        if not t:
            continue
        parts = split_dot(t)
        if parts[0] in LAMPS:
            lamp, cat, rest = parts[0], "完成判定", parts[1:]
        elif parts[0] == "輸出缺項":
            lamp, cat, rest = "YELLOW", "輸出缺項", parts[1:]
        else:
            lamp, cat, rest = "YELLOW", "其他", parts
        item = rest[0] if rest else ""
        detail = " · ".join(rest[1:])
        if cat == "其他" and "原文核對" in item:
            cat = "原文核對"
        elif cat == "其他" and re.search(r"缺必裝|缺選裝|環境", item):
            cat = "環境"
        item = re.sub(r"^VRN2_(\w+?)_latest$", r"\1", item)
        key = (lamp, cat, item, detail)
        if key not in seen:
            seen[key] = 0
            order.append(key)
        seen[key] += 1
    rank = {lp: i for i, lp in enumerate(LAMPS)}
    return [k + (seen[k],) for k in sorted(order, key=lambda k: rank.get(k[0], 9))]


def acceptance_html(rows: list) -> str:
    body = ['<tr><td class="w9-k">%s</td><td class="w9-k">%s</td><td>%s</td><td>%s</td><td class="n">%s</td></tr>' % (
        chip(lp), _e(cat), _e(punct(item)), _det(detail), ("× %d" % n) if n > 1 else "1") for lp, cat, item, detail, n in rows]
    if not body:
        body = ['<tr><td class="w9-k">%s</td><td colspan="4">沒有待驗收項目</td></tr>' % chip("GREEN")]
    return ('<div class="box" id="wb109a"><h2 data-w9="1">待驗收項目<span class="w9-e">Open Acceptance Items</span></h2>'
            '<div class="w9-sect"><span class="w9-cnt">%s · 共 %d 項</span></div>%s%s</div>' % (
                counts_line([r[0] for r in rows]), len(rows),
                matrix([("Status", "燈號"), ("Category", "類別"), ("Item", "項目"), ("Detail", "細節"), ("Count", "次數")], body),
                notes_html([zh("同一項目重複出現只列一次,次數欄記出現幾次。"), zh("細節過長只顯示兩行,點一下展開。"),
                            zh("綠燈只代表交接資料完整;驗收以 VCGC 的 closeout_lamp 為準,BLOCKED、REVIEW、缺證據都不是成功。")])))


# ── ② 系統摘要:資料驗證 + 共識 ───────────────────────────────────────────────────────────────────────
def _vname(name: str) -> tuple:
    if name in VNAME:
        return VNAME[name]
    m = re.match(r"^(.*?)\s*\(([^()]*)\)\s*$", name)
    return (m.group(2), m.group(1)) if m else ("", name)


def verification_rows(v2: Path, acc: list | None) -> list:
    rows = []
    store = W107.jread107(Path(v2) / "VRN2_OutputStore_latest.json", {}) or {}
    fill = store.get("derived_fill") if isinstance(store.get("derived_fill"), dict) else {}
    for name, lamp, detail in W107.verification_rows(Path(v2)):
        en, zh_ = _vname(name)
        if name.startswith("增量庫") and fill.get("why"):
            detail = "%s · 補欄:%s" % (detail, fill["why"])
        detail = str(detail or "").replace("FactSet 中位數", "FactSet 目標價中位數").replace("Yahoo 中位數", "Yahoo 目標價中位數")
        rows.append((en, zh_, lamp, detail))
    bs = W107.jread107(Path(v2) / "VRN2_BookSource_latest.json", {}) or {}
    rows.append(("Book Source Columns ⑬a", "輸出冊 SOURCE/BROKER_EN", W107._lamp(bs) if bs else "GRAY", str(bs.get("why") or "還沒有 VRN2_BookSource 收據 · 下一輪 ⑬a 寫入")))
    if acc is not None:
        lamps = [r[0] for r in acc]
        lamp = "RED" if "RED" in lamps else ("YELLOW" if lamps else "GREEN")
        rows.append(("Open Acceptance Items", "待驗收項目", lamp, "紅 %d · 黃 %d · 共 %d 項 · 明細見 04 政策與交接" % (lamps.count("RED"), lamps.count("YELLOW"), len(acc))))
    return rows


def consensus_rows(v2: Path) -> tuple:
    """(列 [(代號, 名稱, FactSet 中位數, Yahoo 中位數, FactSet 人數, Yahoo 人數, 兩源檢核)], 來源說明, 註)。"""
    cons = W107.jread107(Path(v2) / "consensus" / "VRN2_Consensus_latest.json", {}) or {}
    per = cons.get("per_code") if isinstance(cons.get("per_code"), dict) else {}
    snap = cons.get("snapshot_reused") if isinstance(cons.get("snapshot_reused"), dict) else None
    out = []
    for code, c in sorted(per.items()):
        if isinstance(c, dict):
            out.append((str(code), str(c.get("company_name") or ""), W107._fmt2(c.get("factset_target_median")), W107._fmt2(c.get("yf_target_median")),
                        str(c.get("factset_analyst_count") or "—"), str(c.get("yf_analyst_count") or "—"), str(c.get("source_agreement_gate") or "—")))
    how = "共識收據 per_code"
    if not out:
        latest = {}
        for r in W107._book(Path(v2), "MarketConsensus") or []:
            tk = str(r.get("TICKER") or "").strip()
            if tk and str(r.get("DATE") or "") >= str((latest.get(tk) or {}).get("DATE") or ""):
                latest[tk] = r
        for tk, r in sorted(latest.items()):
            out.append((tk, str(r.get("NAME") or ""), W107._fmt2(r.get("FACTSET_TARGET_PRICE_MEDIAN")), W107._fmt2(r.get("YFINANCE_TARGET_PRICE_MEDIAN")),
                        str(r.get("FACTSET_ANALYST_COUNT") or "—"), str(r.get("YFINANCE_ANALYST_COUNT") or "—"), str(r.get("SOURCE_AGREEMENT_GATE") or "—")))
        how = "MarketConsensus 冊最新一天"
    meta = "引擎 %s · 網路工具 %s · %s" % (Path(str(cons.get("engine") or "—")).name, cons.get("net_tool") or "—",
                                       (snap["why"] if snap else str(cons.get("why") or "這輪沒有共識收據")[:240]))
    if snap:
        meta = "快照 ASOF %s · %s" % (snap.get("asof"), meta)
    return out, how, meta


def summary_section(v2: Path, acc: list | None) -> str:
    vr = verification_rows(v2, acc)
    body = ['<tr><td class="w9-k">%s</td><td>%s</td><td>%s</td></tr>' % (chip(lp), _item(en, zh), _det(dt)) for en, zh, lp, dt in vr]
    crow, how, meta = consensus_rows(v2)
    fs_n = sum(1 for r in crow if r[2] not in ("—", ""))
    yf_n = sum(1 for r in crow if r[3] not in ("—", ""))
    cbody = ['<tr><td class="w9-k">%s</td><td>%s</td><td class="n">%s</td><td class="n">%s</td><td class="n">%s</td><td class="n">%s</td><td class="w9-k">%s</td></tr>' % tuple(
        _e(x) for x in r) for r in crow[:80]]
    if not cbody:
        cbody = ['<tr><td colspan="7">本輪沒有共識資料 · 共識欄留空</td></tr>']
    return ('<div class="sm-sec w9-sec" id="wb109v">'
            '<div class="w9-sect"><div class="sm-sect" data-w9="1">資料驗證 · Verification</div><div class="w9-cnt">%s</div></div>%s'
            '<div class="w9-sect" style="margin-top:14px"><div class="sm-sect" data-w9="1">共識資料 · Consensus</div><div class="w9-cnt">%d 檔 · FactSet %d · Yahoo %d</div></div>%s%s</div>') % (
        counts_line([r[2] for r in vr]), matrix([("Status", "燈號"), ("Item", "項目"), ("Detail", "細節")], body),
        len(crow), fs_n, yf_n,
        matrix([("Ticker", "代號"), ("Company", "名稱"), ("FactSet TP Median", "FactSet 目標價中位數"), ("Yahoo TP Median", "Yahoo 目標價中位數"),
                ("FactSet Analysts", "FactSet 分析師人數"), ("Yahoo Analysts", "Yahoo 分析師人數"), ("Source Check", "兩源檢核")], cbody, "34vh"),
        notes_html([zh("燈號逐項讀本輪收據,只讀不重算;細節過長只顯示兩行,點一下展開。"), zh("共識資料來源:") + _e(how), _e(punct(meta)),
                    zh("待驗收項目明細在 04 政策與交接;綠燈不等於驗收,驗收以 VCGC 的 closeout_lamp 為準。")]))


# ── ⑦ 01 頁輸入分類矩陣 ─────────────────────────────────────────────────────────────────────────────
def input_section(v2: Path) -> str:
    rec = W107.jread107(Path(v2) / "VRN2_Input_latest.json", {}) or {}
    audit = rec.get("audit") if isinstance(rec.get("audit"), dict) else None
    head = '<div class="box" id="wb109i"><h2 data-w9="1">輸入分類<span class="w9-e">Input Classification</span></h2>'
    if not audit:
        return head + '<div class="subtle">還沒有輸入稽核收據 VRN2_Input_latest.json · 按左欄步驟 2 確認輸入後出現</div></div>'
    got = input_classes(audit)
    grid = got["grid"]
    rows, col_tot = [], {t: 0 for t, _, _ in TYPES}
    for key, en, zh_c in CLASSES:
        tot = sum(grid[key].values())
        for t in col_tot:
            col_tot[t] += grid[key][t]
        lamp = ("GREEN" if grid[key]["PDF"] else "GRAY") if key == "STOCK" else ("YELLOW" if (key == "UNCLASSIFIED" and tot) else "GRAY")
        rows.append('<tr><td class="w9-k">%s</td><td>%s</td>%s<td class="n"><b>%d</b></td><td>%s</td></tr>' % (
            chip(lamp), _item(en, zh_c), "".join('<td class="n">%d</td>' % grid[key][t] for t, _, _ in TYPES), tot, _e(PROCESS[key])))
    rows.append('<tr class="w9-tot"><td></td><td>%s</td>%s<td class="n">%d</td><td></td></tr>' % (
        _item("Total", "合計"), "".join('<td class="n">%d</td>' % col_tot[t] for t, _, _ in TYPES), sum(col_tot.values())))
    src = str(rec.get("source_dir") or "")
    notes = [zh("分類是檔名初判的候選規則:個股報告以 VRN SystemManager 的檔名規則與上輪判定為準;範圍外的 PDF 依檔名分成非個股報告(產業、策略、總經、專題)與新聞與盤勢(晨會、早報、盤後、市場觀察)。"),
             zh("本版主體只擷取 PDF:Word、文字檔、影像已收下但未擷取;Word 需先轉 PDF,影像需 OCR,環境交 VCGC 安裝。"),
             zh("頁面影像是 PDF 拆出的 page_0001 類衍生圖檔,不是原始報告。")]
    if got["truncated"]:
        notes.append(zh("輸入收據的非 PDF 名單只列前 %d 筆,其餘 %d 份依型別計入未分類。" % (len(audit.get("non_pdf_names") or []), got["truncated"])))
    if got["rest_out"]:
        notes.append(zh("範圍外名單沒列出的 %d 份 PDF 計入非個股報告。" % got["rest_out"]))
    if src:
        notes.append("輸入來源 · %s" % _e(src))
    return head + '<div class="w9-sect"><span class="w9-cnt">輸入 %d 份 · 檔名規則 %s</span></div>%s%s</div>' % (
        got["files"], _e(str(audit.get("rule") or "—")),
        matrix([("Status", "燈號"), ("Category", "類別")] + [(en, zh) for _, en, zh in TYPES] + [("Total", "合計"), ("Processing", "處理方式")], rows),
        notes_html(notes))


# ── JS ───────────────────────────────────────────────────────────────────────────────────────────────
_LIB = r"""<script id="wb109-lib">window.w9lib = (function(){
  var P = window.VRN2_WB109 || {}, CJK = /[\u3400-\u9fff\uf900-\ufaff]/;
  function hx(v){ return String(v == null ? '' : v).replace(/[&<>"]/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }
  var PATHY = /[A-Za-z]:\\|\/[\w.\-]+\/|\.(pdf|docx?|txt|png|jpe?g|json|csv|parquet|html?|py|zip|ps1)\b/i, FTAIL = /^[^\s\u00b7,\uff0c]*\.(pdf|docx?|txt|png|jpe?g|json|csv|parquet|html?|py|zip|ps1)\b/i;
  function punct(t){ var s = String(t == null ? '' : t);
    s = s.replace(/\(([^()]*[\u3400-\u9fff][^()]*)\)/g, function(m, x, off){ var pre = s.slice(0, off).match(/[^\s\u00b7]*$/)[0]; return (PATHY.test(x) || FTAIL.test(s.slice(off + m.length)) || /\\|:\/\/|^\//.test(pre)) ? m : '\uff08' + x + '\uff09'; });
    return s.replace(/([\u3400-\u9fff\uff09])\s*:\s*/g, '$1\uff1a').replace(/([\u3400-\u9fff\uff09]),\s*/g, '$1\uff0c').replace(/([\u3400-\u9fff\uff09]);\s*/g, '$1\uff1b'); }
  function split(t){ var s = String(t == null ? '' : t).replace(/\s+/g, ' ').trim(), note = [], hit = (P.txt || {})[s], en = '', zh = '';
    if (hit) return [hit[0], hit[1], hit[2] || ''];
    s = s.replace(/\s*[\uff08(]([^()\uff08\uff09]*)[)\uff09]/g, function(m, x){ note.push(x); return ''; }).trim();
    hit = (P.txt || {})[s]; if (hit) return [hit[0], hit[1], note.join('\uff1b')];
    var parts = s.split(' / ');
    if (parts.length === 2 && CJK.test(parts[0]) !== CJK.test(parts[1])) { if (CJK.test(parts[0])) { zh = parts[0]; en = parts[1]; } else { en = parts[0]; zh = parts[1]; } }
    else if (CJK.test(s)) { zh = s; en = (P.en || {})[s] || ''; }
    else { en = s; zh = (P.zh || {})[s] || ''; }
    return [en, zh, note.join('\uff1b')]; }
  function head(en, zh){ return '<span class="w9h">' + (en ? '<span class="w9en">' + hx(en) + '</span>' : '') + (zh ? '<span class="w9zh">' + hx(zh) + '</span>' : '') + '</span>'; }
  function code(c){ var o = (P.code || {})[c], m; if (o) return [o[0], o[1], o[2] || ''];
    if ((m = String(c).match(/^(\d{4})_DILUTED_EPS_FACTSET$/))) return ['FactSet ' + m[1] + ' Diluted EPS', 'FactSet ' + m[1] + ' \u7a00\u91cb\u6bcf\u80a1\u76c8\u9918', ''];
    if ((m = String(c).match(/^(\d{4})_PER_FACTSET$/))) return ['FactSet ' + m[1] + ' PER', 'FactSet ' + m[1] + ' \u672c\u76ca\u6bd4', ''];
    return null; }
  return {hx: hx, punct: punct, split: split, head: head, code: code};
})();</script>
"""

_JS = r"""
  /* VRN2_Workbench v0109:實體 SOURCE / BROKER_EN 優先(不重複加欄)· 表頭英文一行 + 中文一行 · 欄註放表下 */
  var W9N = {};
  function w9xc(C){ return C.indexOf('SOURCE') >= 0 ? C : C.concat(['SOURCE']); }
  function w9hdr(c){ var o = w9lib.code(c) || w9lib.split(w8hdr(c)); if (o[2]) W9N[c] = o[2]; return w9lib.head(o[0], o[1]); }
  function w8cols(ds, C){ var tk = w8key(C, /^ticker$/i), yf = w8key(C, /^yfinance_ticker$/i), nm = w8key(C, /^name$/i), out = [], nat = ds === 'MarketConsensus' && C.indexOf('SOURCE') >= 0;
    C.forEach(function(c){ if (c === 'BROKER_EN') return; if (tk && (c === yf || c === nm)) return; if (c === 'REPORT_DATE') out.push('FRESH');
      if (c === tk) { out.push('TICKER_YF'); out.push(nm || 'NAME'); return; } if (c === 'SOURCE' && !nat) return; out.push(c); });
    if (!nat) out.push('SOURCE'); return out; }
  function w8src(R, ds){ return (R || []).map(function(r){ var o = {}, k; for (k in r) o[k] = r[k]; if (o.SOURCE == null || o.SOURCE === '') o.SOURCE = w8source(r, ds); return o; }); }
  function w8cell(r, c, ds){
    if (c === 'FRESH') { var f = w8fresh(r.REPORT_DATE); return '<td class="k">' + (f[0] ? w8tag(f[0], f[0] === '過期' ? 'r' : 'g', w9lib.punct(f[1])) : '<span class="w8dim" title="' + hx(f[1]) + '">—</span>') + '</td>'; }
    if (c === 'TICKER_YF') { var t = w8tk(r), y = String(r.YFINANCE_TICKER || r.yfinance_ticker || (W8.yf || {})[t] || '').trim(); return '<td class="k">' + hx(t) + ' <span class="w8dim">/ ' + hx(y || '—') + '</span></td>'; }
    if (/^name$/i.test(c)) { var nm = String(r[c] || '').trim(), how = '冊內'; if (!nm) { nm = (W8.nf || {})[r.FILENAME] || (W8.nt || {})[w8tk(r)] || ''; how = 'Combined/基本資料對照'; } return '<td title="' + hx(nm ? '名稱來源\uff1a' + how : '') + '">' + hx(nm) + '</td>'; }
    if (c === 'BROKER') { var raw = String(r.BROKER == null ? '' : r.BROKER).trim(), en = String(r.BROKER_EN == null ? '' : r.BROKER_EN).trim(), b = en ? [en, 1] : w8br(raw);
      return '<td class="k' + (b[1] ? '' : ' w8unk') + '" title="' + hx(b[1] ? '原文 ' + raw : '沒有英文縮寫對照\uff1a候選表\uff0c等 VCGC 核發') + '">' + hx(b[0]) + '</td>'; }
    if (c === 'PERIOD') { var p = w8period(r.PERIOD, r.REPORT_DATE); return '<td class="k" title="原文 ' + hx(r.PERIOD) + '">' + hx(p[0]) + '</td>'; }
    if (c === 'REPORT_DATE' || /(^|_)DATE$|^date$|_AT_UTC$|_at_utc$/.test(c)) { var dd = w8d(r[c]); return '<td class="k"' + (dd && dd !== String(r[c]) ? ' title="原文 ' + hx(r[c]) + '"' : '') + '>' + hx(dd || r[c]) + '</td>'; }
    if (c === 'SOURCE') { var s = (r.SOURCE != null && r.SOURCE !== '') ? String(r.SOURCE) : w8source(r, ds); return '<td>' + w8tag(s, /^歷史|TWSE \/ TPEX/.test(s) ? 'g' : /預估/.test(s) ? 'o' : 'n') + '</td>'; }
    return cell(r, c, ds); }
  (function(){ var h = document.getElementById('dsHead'); if (!h) return;
    function notes(){ var tb = h.closest ? h.closest('table') : null, box = tb ? (tb.closest('.matrix') || tb) : null; if (!box || !box.parentNode) return;
      var el = document.getElementById('w9dsNotes'); if (!el) { el = document.createElement('ol'); el.id = 'w9dsNotes'; el.className = 'w9-notes'; box.parentNode.insertBefore(el, box.nextSibling); }
      var seen = {}, li = []; Array.prototype.forEach.call(h.querySelectorAll('th[title]'), function(t){ var c = t.getAttribute('title'), n = W9N[c]; if (n && !seen[c]) { seen[c] = 1; var o = w9lib.code(c);
        li.push('<li><b>' + w9lib.hx(o ? o[1] : c) + '</b>\uff1a' + w9lib.hx(n) + '</li>'); } });
      el.innerHTML = li.join(''); el.style.display = li.length ? '' : 'none'; }
    if (window.MutationObserver) new MutationObserver(notes).observe(h, {childList: true}); setTimeout(notes, 0); })();
"""

_DOM = r"""<script id="wb109-dom">(function(){
  var L = window.w9lib; if (!L) return;
  var SKIP = 'script,style,pre,code,textarea,input,select,#dsBody,#wb107b tbody,#files,.w9-raw,.sm-hs,#xPreview';
  var EMO = /[\uD83C-\uD83E][\uDC00-\uDFFF]\uFE0F?|[\u2190-\u21FF\u2300-\u23FF\u25A0-\u27BF\u2600-\u26FF\u2B00-\u2BFF]\uFE0F?/g;
  function box(el){ return (el.closest && el.closest('.box, .sm-sec, .w9-sec, aside, section')) || el.parentNode; }
  function addNote(b, head, txt){ if (!b || !txt) return; var ol = null, i; for (i = 0; i < b.children.length; i++) if (b.children[i].className === 'w9-notes w9-auto') ol = b.children[i];
    if (!ol) { ol = document.createElement('ol'); ol.className = 'w9-notes w9-auto'; b.appendChild(ol); }
    var li = document.createElement('li'); li.innerHTML = (head ? '<b>' + L.hx(head) + '</b>\uff1a' : '') + L.hx(L.punct(txt)); ol.appendChild(li); }
  function headers(root){ Array.prototype.forEach.call(root.querySelectorAll('th:not([data-w9]), .sm-colh:not([data-w9]), .kv .cell small:not([data-w9])'), function(h){
    if (h.closest('#dsHead')) return; h.setAttribute('data-w9', '1'); if (h.children.length) return;
    var o = L.split(h.textContent); if (!o[0] && !o[1]) return; h.innerHTML = L.head(o[0], o[1]); if (o[2]) h.title = L.punct(o[2]); }); }
  function headings(root){ Array.prototype.forEach.call(root.querySelectorAll('h2:not([data-w9]), h3:not([data-w9]), .sm-sect:not([data-w9])'), function(h){
    h.setAttribute('data-w9', '1');
    Array.prototype.forEach.call(h.querySelectorAll('.pill'), function(p){ if (/^Workbench v\d+/.test(p.textContent.trim())) p.parentNode.removeChild(p); });
    var tn = null, i; for (i = 0; i < h.childNodes.length; i++) if (h.childNodes[i].nodeType === 3 && h.childNodes[i].nodeValue.trim()) { tn = h.childNodes[i]; break; }
    if (!tn) return; var m = tn.nodeValue.match(/^(.*?)\s*[\uff08(]([^()\uff08\uff09]+)[)\uff09]\s*$/); if (!m) return;
    var head = m[1].trim(), inner = m[2].trim();
    if (/^\d[\d,]*\s*\S{0,3}$/.test(inner)) { tn.nodeValue = head + ' \u00b7 ' + inner; return; }
    tn.nodeValue = head; addNote(box(h), head, inner); }); }
  function punct(root){ var w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null), n, todo = [];
    while ((n = w.nextNode())) { var v = n.nodeValue; if (!v || !/[\u3400-\u9fff]/.test(v) || !/[():,;]/.test(v)) continue; var p = n.parentNode; if (p && p.closest && p.closest(SKIP)) continue; todo.push(n); }
    todo.forEach(function(x){ var t = L.punct(x.nodeValue); if (t !== x.nodeValue) x.nodeValue = t; }); }
  function aside(){
    var A = document.querySelector('aside'); if (!A || A.getAttribute('data-w9')) return; A.setAttribute('data-w9', '1');
    function q(s){ return A.querySelector(s); } function qa(s){ return Array.prototype.slice.call(A.querySelectorAll(s)); }
    var LBL = {'vrn2://pick?kind=folder&cat=stock': '\u9078\u64c7\u8cc7\u6599\u593e', 'vrn2://pick?kind=files&cat=stock': '\u9078\u64c7\u6a94\u6848', 'vrn2://audit': '\u78ba\u8a8d\u8f38\u5165\u4e26\u7a3d\u6838\u7f3a\u6f0f',
      'vrn2://run': '\u555f\u52d5\u8655\u7406', 'vrn2://run?nopush=1': '\u91cd\u8dd1 \u00b7 \u4e0d\u4e0a\u8239', 'vrn2://run-clean': '\u6e05\u5feb\u53d6\u5f8c\u91cd\u8dd1', 'vrn2://restore-archive': '\u9084\u539f\u5c01\u5b58\u820a\u7248',
      'vrn2://pick?kind=outdir': '\u66f4\u63db\u8f38\u51fa\u593e', 'vrn2://outdir?reset=1': '\u6062\u5fa9\u9810\u8a2d\u8f38\u51fa\u593e'};
    var notes = [];
    function note(head, t){ t = L.punct(String(t || '').replace(/\s+/g, ' ').trim()); if (t) notes.push((head ? '<b>' + L.hx(head) + '</b>\uff1a' : '') + L.hx(t)); }
    qa('a.action').forEach(function(a){ var h = a.getAttribute('href') || '', t = a.textContent.replace(/\s+/g, ' ').trim(), nl = LBL[h];
      if (!nl) nl = t.replace(EMO, '').replace(/\s*[\uff08(][^()\uff08\uff09]*[)\uff09]\s*/g, ' ').replace(/\u2026/g, '').replace(/\s*Gate\s*\u00b7\s*UNCONFIGURED/i, ' \u00b7 \u672a\u8a2d\u5b9a').replace(/\s+/g, ' ').trim();
      if (nl && nl !== t) { if (!a.title) a.title = t; a.textContent = nl; } });
    var fold = q('.foldbtn'); if (fold) fold.textContent = fold.textContent.replace(EMO, '').replace(/^[\u27e8\u3008<]\s*/, '').trim();
    var drop = q('#drop'), pf = q('a[href^="vrn2://pick?kind=folder"]'), pfi = q('a[href^="vrn2://pick?kind=files"]'), audit = q('a[href="vrn2://audit"]'), dn = q('.dialog-note'),
        run = q('a[href="vrn2://run"]'), r1 = q('a[href="vrn2://run?nopush=1"]'), r2 = q('a[href="vrn2://run-clean"]'), r3 = q('a[href="vrn2://restore-archive"]'), outf = q('#outfolder'), gates = q('.gates');
    if (!drop && !pf && !run) return;
    var srcPath = '';
    qa('.subtle').forEach(function(s){ if ((outf && outf.contains(s)) || (drop && drop.contains(s))) return; var t = s.textContent.replace(/\s+/g, ' ').trim();
      var m = t.match(/\u76ee\u524d\u4f86\u6e90[:\uff1a]\s*(.+?)(\s*vrn2:\/\/.*)?$/); if (m) { srcPath = m[1].trim(); if (m[2]) note('\u4f86\u6e90', m[2]); } else note('', t);
      if (s.parentNode) s.parentNode.removeChild(s); });
    if (drop) { var dsub = drop.querySelector('.subtle'); if (dsub) { note('\u62d6\u66f3', dsub.textContent.replace(/[()\uff08\uff09]/g, '')); dsub.parentNode.removeChild(dsub); } Array.prototype.forEach.call(drop.querySelectorAll('br'), function(b){ b.parentNode.removeChild(b); }); }
    var kv = null, nFiles = 0;
    if (dn) { var t = dn.textContent.replace(/\s+/g, ' '), g = function(re){ var m = t.match(re); return m ? m[1] : null; };
      var cells = [['\u6a94\u6848', g(/\u6a94\s*(\d[\d,]*)/)], ['PDF', g(/PDF\s*(\d[\d,]*)/)], ['Word', g(/Word\s*(\d[\d,]*)/)], ['TXT', g(/TXT\s*(\d[\d,]*)/)], ['\u5f71\u50cf', g(/\u5f71\u50cf\s*(\d[\d,]*)/)],
        ['\u5176\u4ed6', g(/\u5176\u4ed6\u578b\u5225\s*(\d[\d,]*)/)], ['\u500b\u80a1', g(/\u500b\u80a1\u7bc4\u570d\s*(\d[\d,]*)/)], ['\u7bc4\u570d\u5916', g(/\u7bc4\u570d\u5916\s*(\d[\d,]*)/)]].filter(function(c){ return c[1] !== null; });
      if (cells.length >= 3) { kv = document.createElement('div'); kv.className = 'w9-kv'; kv.innerHTML = cells.map(function(c){ return '<div><small>' + L.hx(c[0]) + '</small><b>' + L.hx(c[1]) + '</b></div>'; }).join('');
        nFiles = +String(cells[0][1]).replace(/,/g, ''); note('\u8f38\u5165\u7a3d\u6838', t); dn.parentNode.removeChild(dn); } else kv = dn; }
    var srcEl = null; if (srcPath) { srcEl = document.createElement('div'); srcEl.className = 'w9-src'; srcEl.textContent = '\u4f86\u6e90 \u00b7 ' + srcPath; }
    function row(cls, list){ list = list.filter(Boolean); if (!list.length) return null; var d = document.createElement('div'); d.className = cls; list.forEach(function(x){ d.appendChild(x); }); return d; }
    var pickRow = row('w9-row2', [pf, pfi]), runRow = row('w9-row3', [r1, r2, r3]);
    if (outf) { var oh = outf.querySelector('h3'); if (oh) { var om = oh.textContent.match(/[\uff08(]([^()\uff08\uff09]+)[)\uff09]/); if (om) note('\u8f38\u51fa\u4f4d\u7f6e', om[1]); oh.parentNode.removeChild(oh); }
      Array.prototype.forEach.call(outf.querySelectorAll('.subtle'), function(s){ var st = s.textContent.replace(/\s+/g, ' ').trim(); if (/\u5df2\u6574\u5408|\u539f\u6a94\u5df2\u8907\u88fd|TEMP/.test(st) && !s.closest('.path')) { note('\u820a\u8cc7\u6599\u5eab\u6574\u5408', st); s.parentNode.removeChild(s); } });
      var oacts = Array.prototype.slice.call(outf.querySelectorAll('a.action')); if (oacts.length > 1) outf.appendChild(row('w9-row3', oacts)); }
    var opens = [], gl = [];
    if (gates) { Array.prototype.forEach.call(gates.children, function(x){ if (x.tagName === 'A') { if (x.classList.contains('off') || x.getAttribute('data-act') === 'gateOff' || /Gate|\u672a\u8a2d\u5b9a/.test(x.textContent + (x.title || ''))) gl.push(x); else opens.push(x); } });
      Array.prototype.slice.call(gates.children).forEach(function(x){ if (x.tagName === 'H3') x.parentNode.removeChild(x); else if (x.tagName === 'SMALL') { note('\u5176\u4ed6\u7cfb\u7d71', x.textContent); x.parentNode.removeChild(x); } }); }
    var wrap = document.createElement('div'); wrap.className = 'w9-steps'; var n = 0;
    function step(zh, en, nodes, done){ nodes = nodes.filter(Boolean); if (!nodes.length) return; n++; var s = document.createElement('section'); s.className = 'w9-stepbox';
      s.innerHTML = '<div class="w9-step' + (done ? ' done' : '') + '"><span class="w9-n">' + n + '</span><span class="w9-t">' + L.hx(zh) + '</span><span class="w9-e">' + L.hx(en) + '</span></div>';
      nodes.forEach(function(x){ s.appendChild(x); }); wrap.appendChild(s); }
    step('\u9078\u64c7\u5831\u544a\u4f86\u6e90', 'Source', [drop, pickRow, srcEl], !!srcPath);
    step('\u78ba\u8a8d\u8f38\u5165', 'Confirm', [audit, kv], nFiles > 0);
    step('\u555f\u52d5\u8655\u7406', 'Run', [run, runRow], false);
    step('\u8f38\u51fa\u4f4d\u7f6e', 'Output', [outf], !!(outf && outf.querySelector('.path')));
    step('\u958b\u555f\u8cc7\u6599\u593e', 'Open', [row('w9-row2', opens)], false);
    step('\u5176\u4ed6\u7cfb\u7d71', 'Gates', [row('w9-row3', gl)], false);
    var h2 = q('h2'); if (h2) { h2.innerHTML = '<span class="w9-ptitle"><b>\u8f38\u5165\u8a2d\u5b9a</b><span>Input Setup</span></span>'; h2.setAttribute('data-w9', '1'); }
    var at = h2 || fold; if (at && at.parentNode === A) A.insertBefore(wrap, at.nextSibling); else A.insertBefore(wrap, A.firstChild);
    if (gates && !gates.querySelector('a, div, table')) gates.parentNode.removeChild(gates);
    if (notes.length) { var ol = document.createElement('ol'); ol.className = 'w9-notes'; ol.innerHTML = notes.map(function(x){ return '<li>' + x + '</li>'; }).join(''); A.appendChild(ol); }
  }
  function tabs(){ Array.prototype.forEach.call(document.querySelectorAll('.tabs button'), function(b){ if (/\u7cfb\u7d71\u73fe\u6cc1/.test(b.textContent)) b.textContent = b.textContent.replace('\u7cfb\u7d71\u73fe\u6cc1', '\u7cfb\u7d71\u6458\u8981'); }); }
  function legends(){ Array.prototype.forEach.call(document.querySelectorAll('#wb107b > .subtle:not([data-w9]), #wb107b > .leg:not([data-w9])'), function(s){ s.setAttribute('data-w9', '1');
    var b = s.parentNode; addNote(b, '', s.textContent.replace(/\s+/g, ' ').trim()); b.removeChild(s); }); }
  function run(){ try { aside(); tabs(); legends(); ['main', 'aside'].forEach(function(s){ var r = document.querySelector(s); if (r) { headings(r); headers(r); punct(r); } }); } catch (e) { if (window.console) console.warn('wb109', e); } }
  run();
  document.addEventListener('click', function(e){ var d = e.target && e.target.closest ? e.target.closest('.w9-det') : null; if (d) { var tr = d.closest('tr'); if (tr) tr.classList.toggle('w9-open'); } setTimeout(run, 0); });
  var mm = document.querySelector('main'), busy = 0; if (mm && window.MutationObserver) new MutationObserver(function(){ if (busy) return; busy = 1; setTimeout(function(){ run(); busy = 0; }, 40); }).observe(mm, {childList: true, subtree: true});
})();</script>
"""

_REPL = (("hx(w8hdr(c))", "w9hdr(c)", 1),
         ("cols(st.ds).concat(['SOURCE'])", "w9xc(cols(st.ds))", 2),
         ("cols(ds).concat(['SOURCE'])", "w9xc(cols(ds))", 1),
         ("cols($('#xDs').value).concat(['SOURCE'])", "w9xc(cols($('#xDs').value))", 1))
_BOOT = PRIOR._BOOT
_DATA_ANCHOR = PRIOR._DATA_ANCHOR
_WB107 = re.compile(r'\n?<section class="box" id="wb107">.*?</section>\n?', re.S)


def payload(v2: Path) -> dict:
    code = {k: list(v) for k, v in CODE_HDR.items()}
    try:
        for col, note in (W107.column_notes(Path(v2)) or {}).items():
            if col in code and len(code[col]) < 3:
                code[col] = code[col] + [punct(note)]
    except Exception:  # noqa: BLE001
        pass
    return {"v": VERSION, "code": code, "txt": TXT_HDR, "en": ZH2EN, "zh": EN2ZH}


def augment109(page: str, root: Path, v2: Path) -> tuple:
    """(頁面, 說明)· 純函式可測 · 重入不重複。"""
    if 'id="wb109-tpl"' in page:
        return page, "已是 v0109"
    notes = []
    if page.count("</head>") == 1:
        page = page.replace("</head>", _CSS + "\n</head>", 1)
    if page.count("</title>") >= 1:
        page = page.replace("</title>", "</title><!-- VRN2_Workbench %s over v0108 · 字型以細節欄為準 %s -->" % (VERSION, CSS_SHA256[:12]), 1)
    acc = acceptance_rows(page)
    if acc is not None:
        page = _ACC_BOX.sub(lambda _m: acceptance_html(acc), page, count=1)
    else:
        notes.append("沒有「尚未跨越的驗收條件」格")
    page, n_old = _WB107.subn("\n", page, count=1)
    sec = summary_section(v2, acc)
    i_sm = page.find('<div class="box sm" id="sysmatrix">')
    j = page.find('<div class="sm-sec">', i_sm) if i_sm >= 0 else -1
    if j >= 0:
        page = page[:j] + sec + page[j:]
    else:
        m = re.search(r'<section class="tabsec[^"]*" data-tab="summary">', page)
        if m:
            page = page[:m.end()] + '<div class="box">%s</div>' % sec + page[m.end():]
        elif page.count("<main>") == 1:
            page = page.replace("<main>", '<main><div class="box">%s</div>' % sec, 1)
        else:
            notes.append("找不到系統摘要位置")
    page = page.replace(">00 系統現況</button>", ">00 系統摘要</button>").replace("系統現況 Summary", "系統摘要 Summary")
    m = re.search(r'<section class="tabsec[^"]*" data-tab="overview">', page)
    if m:
        page = page[:m.end()] + input_section(v2) + page[m.end():]
    else:
        notes.append("沒有 01 輸入總覽頁")
    js_ok = page.count(_DATA_ANCHOR) == 1 and len(_BOOT.findall(page)) == 1 and all(page.count(a) == n for a, _, n in _REPL)
    if js_ok:
        for a, b, n in _REPL:
            page = page.replace(a, b, n)
        data = json.dumps(payload(v2), ensure_ascii=False).replace("</", "<\\/")
        page = page.replace(_DATA_ANCHOR, "<script>window.VRN2_WB109 = %s;</script>\n%s%s" % (data, _LIB, _DATA_ANCHOR), 1)
        mb = _BOOT.search(page)
        page = page[:mb.start()] + "\n" + _JS + page[mb.start():]
    else:
        notes.append("資料頁顯示層沒接上(前版版型變了 · 照 v0108 顯示)")
        if page.count(_DATA_ANCHOR) == 1:
            data = json.dumps(payload(v2), ensure_ascii=False).replace("</", "<\\/")
            page = page.replace(_DATA_ANCHOR, "<script>window.VRN2_WB109 = %s;</script>\n%s%s" % (data, _LIB, _DATA_ANCHOR), 1)
    if 'id="wb109-lib"' not in page:
        data = json.dumps(payload(v2), ensure_ascii=False).replace("</", "<\\/")
        lib = "<script>window.VRN2_WB109 = %s;</script>\n%s" % (data, _LIB)
        page = page.replace("</body>", lib + "</body>", 1) if page.count("</body>") == 1 else page + lib
    page = page.replace("</body>", _DOM + "</body>", 1) if page.count("</body>") == 1 else page + _DOM
    return page, " · ".join(notes) or "細節字型 + 系統摘要矩陣 + 待驗收矩陣 + 輸入分類 + 表頭雙行 + 左欄步驟都套上"


def render(root: Path, out_path: Path | None = None, logo: str | None = None, assets_zip: Path | None = None) -> Path:
    root = Path(root).resolve()
    out = PRIOR.render(root, out_path, logo, assets_zip)
    v2 = root / "VIA_Reports" / "vrn2"
    page = Path(out).read_text(encoding="utf-8")
    try:
        page, note = augment109(page, root, v2)
    except Exception as error:  # noqa: BLE001  後處理失敗不毀 v0108 頁
        print("    [U/I] [YELLOW] Workbench v0109 後處理沒做成(v0108 頁照出):%s: %s" % (type(error).__name__, str(error)[:160]), flush=True)
        return Path(out)
    if "沒接上" in note or "找不到" in note:
        print("    [U/I] [YELLOW] Workbench v0109 · %s" % note, flush=True)
    tmp = Path(out).with_suffix(".v0109.tmp")
    tmp.write_text(page, encoding="utf-8")
    tmp.replace(Path(out))
    return Path(out)


# ── 自測 ──────────────────────────────────────────────────────────────────────────────────────────────
_FIX_ACC = ('<div class="box"> <h2>尚未跨越的驗收條件</h2> <p style="margin:4px 0;">· YELLOW · 輸出值驗證(第二讀取器逐值回查 · 年度數據對欄) · 基本資料 欄 139 · 剔除 3</p>'
            '<p style="margin:4px 0;">· RED · ⑤ 一標題四重點 · 紅 3 · 黃 0 · 綠 14</p><p style="margin:4px 0;">· 輸出缺項 · VRN2_BasicInfo_latest · TITLE</p>'
            '<p style="margin:4px 0;">· 輸出缺項 · VRN2_BasicInfo_latest · TITLE</p><p style="margin:4px 0;">· 四點原文核對 · REVIEW_MISSING · {&quot;PASS&quot;: 52}</p>'
            '<p style="margin:4px 0;">· ③ 缺必裝 · numba · 交 VCGC 裝</p> </div>')


def _fixture_page(prior107) -> str:
    aside = ('<aside><button class="foldbtn" data-act="fold">⟨ 折疊輸入面板</button><h2>報告輸入</h2><div id="drop">將 Windows 檔案拖曳到這裡<br><span class="subtle">(瀏覽器拖曳只讀檔名)</span></div>'
             '<a class="action" href="vrn2://pick?kind=folder&amp;cat=stock">📁 選擇檔案夾…(Windows 原生對話框)</a><a class="action" href="vrn2://pick?kind=files&amp;cat=stock">📄 選擇檔案…</a>'
             '<div class="subtle">保留原始來源,工作副本匯入專屬目錄。</div><a class="action primary" href="vrn2://audit">確定輸入 · 先查資料庫缺漏(重新稽核)</a>'
             '<div class="dialog-note">檔 22(PDF 22 · Word 0 · TXT 0 · 影像 0)· 個股範圍 17 · 範圍外 5</div><a class="action primary" href="vrn2://run">啟動系統</a>'
             '<a class="action" href="vrn2://run?nopush=1">▶ 重跑(不上船)</a><a class="action" href="vrn2://run-clean">↻ 清快取後重跑</a><a class="action" href="vrn2://restore-archive">↩ 還原封存舊版</a>'
             '<div class="subtle">目前來源:/x/samples<br>vrn2:// 沒反應 → PowerShell</div><div class="gates"><h3>開啟</h3><a class="action" href="file:///x/out">📂 輸出冊</a>'
             '<div class="outfolder" id="outfolder"><h3>輸出檔案夾 · 長線資料庫(Parquet 增量維護)</h3><div class="path">/x/OneDrive</div><a class="action" href="vrn2://pick?kind=outdir">📤 換輸出夾…</a>'
             '<a class="action" href="vrn2://outdir?reset=1">↩ 取消</a></div><h3>其他系統 Gate</h3><a class="action off" href="#" data-act="gateOff">VRN-1 Gate · UNCONFIGURED</a>'
             '<small class="subtle">只開啟本機已註冊入口。</small></div></aside>')
    base = ('<!DOCTYPE html><html><head><title>VRN</title><style>:root{}</style></head><body>' + aside + '<main><div class="tabs"><button data-tab="summary">00 系統現況</button></div>'
            '<section class="tabsec on" data-tab="summary"><div class="box sm" id="sysmatrix"><div class="sm-title">系統現況 Summary</div><div class="sm-sec"><div class="sm-sect">VRN · 輸出冊</div></div></div></section>'
            '<section class="tabsec" data-tab="overview"><div class="box" id="first"><h2>輸入去重矩陣 · 目前引擎狀態</h2></div></section>'
            '<section class="tabsec" data-tab="data"><table><thead id="dsHead"></thead></table></section><section class="tabsec" data-tab="handover">' + _FIX_ACC + '</section></main>'
            '<script>window.VRN2_DATA = {"dsOrder":[],"books":{}};</script><script>(function(){\n'
            "  var HDR = {TICKER:'Ticker Symbol / 股票代號'}; function hdr(c){ return HDR[c] || c; } function cell(r, c, ds){ return '<td>' + r[c] + '</td>'; }\n"
            "  function renderData(){ var R = rows(st.ds), C = cols(st.ds), n = 1; var th = C.map(function(c){ return hx(hdr(c)); }); var tb = R.map(function(r){ return C.map(function(c){ return cell(r, c, st.ds); }); }); }\n"
            "  if (a === 'csvAll') { dl('x', csv(R, cols(st.ds), true)); } else if (a === 'extract') { X = 1; dl(nm, JSON.stringify({rows: X}, null, 1)); dl(nm, csv(X, cols(ds), true)); }\n"
            "  if (st.tab === 'data') { data = rows(st.ds); C = cols(st.ds); } else if (st.tab === 'export') { data = xrows(); C = cols($('#xDs').value); }\n"
            "  setTab('summary'); renderData(); renderX(); selCount(); fitStats();\n})();</script></body></html>")
    return base


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
    chk("① 前版 v0108 自測照過(%s)" % (buf.getvalue().strip().splitlines() or ["—"])[-1][:60], rc_prior == 0)
    src = Path(__file__).read_text(encoding="utf-8")
    css_sha = hashlib.sha256(_CSS.encode("utf-8")).hexdigest()
    colors = {c.lower() for c in re.findall(r"#[0-9a-fA-F]{6}\b", _CSS)}
    sizes = {float(x) for x in re.findall(r"(?:font(?:-size)?:[^;}]*?|--w9[slt]:)(\d+(?:\.\d+)?)px", _CSS)}
    chk("② 鎖定:CSS SHA-256 = 釘住的值 · 只用模板 15 色 · 字級只用 19 / 11 / 10.45 / 9 / 8 · 內文字型 = Consolas + 微軟正黑體 · 第 3 行加速器標記",
        css_sha == CSS_SHA256 and colors <= set(PALETTE) and sizes == {float(x) for x in SIZES_PX} and F_TEXT in _CSS and src.splitlines()[2].strip() == "# [VIA:ACCEL-BRIDGE:v0111]")
    cjk = re.compile(r"[\u3400-\u9fff]")
    hdr_ok = all(len(v) >= 2 and v[0] and v[1] and not cjk.search(v[0]) and cjk.search(v[1]) and "(" not in v[0] + v[1] and "(" not in v[1] for v in list(CODE_HDR.values()) + list(TXT_HDR.values()))
    chk("③ 表頭字典完整:每一欄英文一行(無中文)+ 中文一行 · 不帶括號 · FactSet 目標價中位數 / FactSet 分析師人數 · 券商英文縮寫欄",
        hdr_ok and CODE_HDR["FACTSET_TARGET_PRICE_MEDIAN"][1] == "FactSet 目標價中位數" and CODE_HDR["FACTSET_ANALYST_COUNT"][1] == "FactSet 分析師人數" and "BROKER_EN" in CODE_HDR
        and all(not cjk.search(v) for v in ZH2EN.values()))
    chk("④ 全形標點:中文旁括號 / 冒號 / 逗號改全形 · 英文旁不動 · 路徑與檔名不動",
        punct("目前引擎狀態(本輪收據):OK, 好") == "目前引擎狀態" + FW_L + "本輪收據" + FW_R + FW_COLON + "OK, 好" and punct("說明:a,b") == "說明" + FW_COLON + "a,b"
        and punct("檔案 報告(一)-新聞.pdf") == "檔案 報告(一)-新聞.pdf" and punct("C:\\測試(舊)\\x") == "C:\\測試(舊)\\x" and punct("中信,凱基") == "中信" + FW_COMMA + "凱基")
    acc = acceptance_rows(_FIX_ACC)
    chk("⑤ 待驗收:六行 → 五項(同項合併 × 2)· 紅先 · 類別 完成判定 / 輸出缺項 / 原文核對 / 環境 · 冊名去 VRN2_ / _latest · 括號裡的「·」不切",
        acc is not None and len(acc) == 5 and acc[0][0] == "RED" and ("YELLOW", "輸出缺項", "BasicInfo", "TITLE", 2) in acc
        and any(r[1] == "原文核對" for r in acc) and any(r[1] == "環境" and r[2] == "③ 缺必裝" for r in acc)
        and any(r[2] == "輸出值驗證(第二讀取器逐值回查 · 年度數據對欄)" and r[3] == "基本資料 欄 139 · 剔除 3" for r in acc))
    audit = {"files": 534, "by_type": {"PDF": 97, "TXT": 1, "IMG": 201, "WORD": 7}, "stock": 52, "out_of_scope": 45, "other_type": 228,
             "out_names": ["20251205兆豐晨會報告(一)-當日新聞與重要訊息評論.pdf", "MS-Memory 20251204.pdf", "凱基期貨晨間解盤20251205.pdf", "群益專題報告-台股投資與操作策略_20260917.pdf"],
             "non_pdf_names": ["3653健策凱基投顧 向子慧 (3).txt", "926708.jpg", "page_0001.png", "page_0002.png"]}
    g = input_classes(audit)["grid"]
    chk("⑥ 輸入分類:個股 PDF 52 · 範圍外 → 新聞 2(晨會 / 晨間解盤)+ 非個股 2 + 名單外 41 · TXT 帶代號 → 個股 · page_000N → 頁面影像 · Word 7 / 影像 200 名單外 → 未分類 · 其他型別 228",
        g["STOCK"]["PDF"] == 52 and g["NEWS"]["PDF"] == 2 and g["NONSTOCK"]["PDF"] == 43 and g["STOCK"]["TXT"] == 1 and g["PAGE"]["IMG"] == 2
        and g["UNCLASSIFIED"]["IMG"] == 199 and g["UNCLASSIFIED"]["WORD"] == 7 and g["UNCLASSIFIED"]["OTHER"] == 228
        and sum(sum(r.values()) for r in g.values()) == 52 + 45 + 1 + 201 + 7 + 228)
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "VIA"
        v2 = root / "VIA_Reports" / "vrn2"
        W107._fixture_v2(v2)
        (v2 / "VRN2_Input_latest.json").write_text(json.dumps({"source_dir": "C:\\樣本", "audit": audit}, ensure_ascii=False), encoding="utf-8")
        (v2 / "VRN2_BookSource_latest.json").write_text(json.dumps({"lamp": "GREEN", "why": "7 冊 · 改寫 17 檔"}, ensure_ascii=False), encoding="utf-8")
        page = W107.augment(_fixture_page(W107), v2)
        p108, _n = PRIOR.augment108(page, root, v2, _dt.date(2026, 11, 3))
        got, note = augment109(p108, root, v2)
        chk("⑦ 頁面:v0109 CSS 在 v0108 之後 · 頁首上方的驗證區塊移除 · 驗證矩陣在系統摘要第一段之前 · 00 頁改名系統摘要 · 大標改名",
            got.count('id="wb109-tpl"') == 1 and got.index('id="wb108-tpl"') < got.index('id="wb109-tpl"') and 'id="wb107"' not in got
            and got.index('id="sysmatrix"') < got.index('id="wb109v"') < got.index('<div class="sm-sec">') and ">00 系統摘要</button>" in got and "系統摘要 Summary" in got
            and "系統現況" not in got.split("</style>")[-1].split("<script")[0])
        chk("⑧ 驗證矩陣:燈號 / 項目 / 細節 · 多 BookSource ⑬a 與待驗收兩列 · 共識矩陣表頭 FactSet 目標價中位數 / FactSet 分析師人數 · 說明在矩陣下方的註",
            "輸出冊 SOURCE/BROKER_EN" in got and "待驗收項目" in got and "FactSet 目標價中位數" in got and "FactSet 分析師人數" in got
            and got.index('id="wb109v"') < got.index('class="w9-notes"') and "資料驗證狀況(紅黃綠燈" not in got)
        chk("⑨ 04 頁「尚未跨越的驗收條件」→ 待驗收項目矩陣 · 01 頁輸入分類矩陣(個股報告 / 非個股報告 / 新聞與盤勢 / 頁面影像 / 未分類)",
            "尚未跨越的驗收條件" not in got and got.count('id="wb109a"') == 1 and got.count('id="wb109i"') == 1
            and all(z in got for z in ("個股報告", "非個股報告", "新聞與盤勢", "頁面影像", "未分類")) and got.index('data-tab="overview"') < got.index('id="wb109i"'))
        chk("⑩ 資料頁:表頭換 w9hdr · 匯出 SOURCE 不重複(四處 w9xc)· 函式庫在 VRN2_DATA 前 · 顯示層在開機前 · 左欄與標點腳本在 </body> 前 · VRN2_DATA 一字不改",
            "w9hdr(c)" in got and "hx(w8hdr(c))" not in got and got.count("w9xc(cols(st.ds))") == 2 and "w9xc(cols(ds))" in got and "w9xc(cols($('#xDs').value))" in got
            and all(x not in got for x, _, _ in _REPL[1:]) and got.count(".concat(['SOURCE'])") == 1 and got.index('id="wb109-lib"') < got.index("window.VRN2_DATA") and got.index("function w9hdr(") < got.index("setTab('summary')")
            and got.index('id="wb109-dom"') < got.index("</body>") and '{"dsOrder":[],"books":{}}' in got and "沒接上" not in note)
        chk("⑪ 實體欄:BROKER_EN 不另列 · 券商欄用 BROKER_EN · SOURCE 已在冊裡就不加 · MarketConsensus 原生 SOURCE 照原位 · 匯出保留冊裡的 SOURCE",
            "if (c === 'BROKER_EN') return;" in _JS and "r.BROKER_EN" in _JS and "if (c === 'SOURCE' && !nat) return;" in _JS and "ds === 'MarketConsensus'" in _JS
            and "if (o.SOURCE == null || o.SOURCE === '') o.SOURCE" in _JS)
        chk("⑫ 重入不重複 · 前版版型變了(錨點不在)→ 顯示層不接 · 頁照出並寫原因", augment109(got, root, v2)[0] == got
            and "沒接上" in augment109("<html><head><title>x</title></head><body><main>y</main></body></html>", root, v2)[1])
    n = 12
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
    ap = argparse.ArgumentParser(prog="VRN2_Workbench_v0109")
    ap.add_argument("verb", nargs="?", default="render")
    ap.add_argument("--root", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--logo", default=None)
    a = ap.parse_args(argv)
    if a.verb != "render":
        return PRIOR.main(argv)
    root = Path(a.root) if a.root else (os.environ.get("VIA_ROOT") and Path(os.environ["VIA_ROOT"])) or HERE.parent.parent
    path = render(root, a.out, a.logo)
    print("[GREEN] %s %s(前版 v0108)· %s" % (DISPLAY_NAME, VERSION, path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
