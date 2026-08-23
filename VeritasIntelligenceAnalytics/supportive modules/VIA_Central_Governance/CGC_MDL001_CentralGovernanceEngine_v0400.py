#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
# =============================================================================
#  CGC_MDL001_CentralGovernanceEngine.py                                    (all-in-one)
#  Veritas Intelligence Analytics — 中央治理引擎 · 同義字 / regex SSOT
# -----------------------------------------------------------------------------
#  一顆 Python 檔管全部(v0200 只增不減擴充,v0100 功能全保留):
#    1) auto-import live state  自動匯入現況(掃 domain_keywords / ssot.json /
#       events.jsonl / *.csv / *.txt,不吃空白模板)
#    2) 自動擴大同義字            正規化 / 全半形 / 大小寫 / 分隔符 / 縮寫 變體
#    3) 自動更新監測同義字        未知 token 就近歸戶(difflib),分 AUTO/ASK/QUARANTINE
#    4) 自動合成 regex           每個 canonical 依同義字集自動生 regex 並驗證可編譯
#    5) 只增不減治理             同義字只增不刪;退場者轉 DORMANT;evidence V/M/P
#    6) 產出 Visual Lock HTML     深色儀表板 + append-only ledger
#  ── v0200 新增(central government 擴編)──
#    7) --import-curated *.py    AST 解析 PatternDef 模式庫(如 InvestmentRegex-
#       Pattern_VALIDATED.py)→ 人工 regex 以 V 級入庫(regex_curated 與 auto
#       regex 並存,互不覆蓋),name_en/類別/報表/validation_level/unit 進 attrs
#    8) --import-matrix *.csv    吃 VIA Extraction Matrix(77 datasets)→ dataset
#       詞條 + instrument 詞條(標的/代碼欄自動拆);內建 provider 字彙自動歸類
#       主要來源(消 UNCLASSIFIED WARN);tier(T1/T4/SSOT/衍生)入 attrs
#    9) namespace 隔離           canonicals 分 core / finreport / dataset /
#       instrument / provider 命名空間(呼應 M03 EAV namespace isolation)
#   10) TW ticker 三重衍生       4 碼 → .TW / .TWO / 「#### TT」Bloomberg
#   11) 憲法稽核 gate checks     重複碼 / regex 編譯 / provider 未歸類 → PASS/WARN
#  ── v0300 功能補強(五項)──
#   12) --confirm 確認迴路       吃 confirmations.jsonl(==CGE-CONFIRM== token 或
#       JSON 行),ACCEPT 升 V 入庫 / REJECT 進拒絕名冊(append-only,監測不再問)
#       / NEW 開新 canonical;HTML ASK 佇列改 mouse-only:預選最佳歸戶、單列
#       接受/拒絕/略過、一鍵全收,自動生成 token 供複製貼回 confirmations.jsonl
#   13) provider 字彙補強        ONCHAIN / INDEX_COMPONENTS / OFFICIAL_POOL,
#       消掉 v0200 剩餘 5 筆未歸類 dataset
#   14) 去重執行計畫             DUPLICATE → dedup_plan.ps1(LL 慣例、預設 dry-run、
#       -Commit 才搬,搬進同層 _to_delete\,絕不刪檔)+ dedup_plan.csv
#   15) Command Center 掛載      每跑必出 cge_state.json(機讀狀態);--cc-registry
#       指向 vcc_registry.json 時 add-only 註冊本引擎(--commit 才寫)
#   16) regex 自測 harness       全體同義字回測 auto+curated regex,未命中列缺口,
#       進 gate check CGE_REGEX_SELFTEST
#
#  治理原則:只增不減(append-only)、dry-run 預設、--commit 才落地、review-only、
#            evidence honesty(human=V / auto=M封頂 / novel=P)、純 stdlib 可跑。
#  無 Read-Host / 無 input() / 一貼即跑,零外部相依。
#  用法:   python CGC_MDL001_CentralGovernanceEngine_v0200.py                # dry-run
#           python CGC_MDL001_CentralGovernanceEngine_v0200.py --commit       # 落地
#           python CGC_MDL001_CentralGovernanceEngine_v0200.py --commit ^
#             --import-curated InvestmentRegexPattern_VALIDATED.py ^
#             --import-matrix "VIA_Extraction_Matrix 8.csv"
# =============================================================================

import argparse
import ast
import datetime as _dt
import glob
import hashlib
import html
import json
import os
import re
import sys
import unicodedata
from difflib import SequenceMatcher

SCHEMA = "VIA-CGE-VOCAB-v4"
ENGINE = "VIA_CentralGovernanceEngine"
VERSION = "v0400"
ID_TYPE = "CGE"

# ---- namespaces (呼應 SuperBOM M03 EAV namespace isolation) -------------------
NS_CORE = "core"           # 原 v0100 詞彙(BOM/VMT 表頭)
NS_FINREPORT = "finreport" # 財報科目(curated 模式庫)
NS_DATASET = "dataset"     # Extraction Matrix 資料集
NS_INSTRUMENT = "instrument"  # 標的/代碼(ticker/index/ETF)
NS_PROVIDER = "provider"   # 資料來源機構
NS_TEMPORAL = "temporal"   # v0400:時間/日期 regex pack(西元/民國/年季/FY…)

# ---- evidence grades (evidence honesty) -------------------------------------
EV_HUMAN = "V"   # Confirmed — 人工確認
EV_AUTO = "M"    # Media/Model-derived — 自動衍生,封頂於 M
EV_PEND = "P"    # Pending — 新詞待歸類
EV_RANK = {EV_HUMAN: 3, EV_AUTO: 2, EV_PEND: 1}

# ---- lifecycle states (只增不減) --------------------------------------------
ST_ACTIVE = "ACTIVE"
ST_DORMANT = "DORMANT"     # 退場但保留(不刪)
ST_ABSORBED = "ABSORBED"   # 併入其他 canonical

# ---- TW 漲跌色 (Visual Lock) -------------------------------------------------
C_UP = "#c96b5a"    # 紅 = 上升 / 新增
C_DN = "#5a9e6f"    # 綠 = 下降 / 穩定

DEFAULT_PARAMS = {
    "auto_attach": 0.90,   # >= → AUTO(自動歸戶)
    "ask": 0.75,           # >= → ASK(候選待確認)
    # < ask → QUARANTINE / novel(新 canonical 候選)
    "min_token_len": 2,
    "max_token_len": 64,
    "min_freq": 1,
    "word_boundary_ascii": True,
}

# 內建種子字典:讓首跑就有意義(不吃空白模板)。curated=人工 → V。
# 只增不減:seed 只會補進 SSOT,不覆蓋既有。
SEED = {
    "item_number":   {"domain": "superbom", "syn": ["料號", "品號", "part number", "part no", "pn", "mpn", "item no", "料件編號"]},
    "quantity":      {"domain": "superbom", "syn": ["數量", "用量", "qty", "usage", "需求量"]},
    "reference_designator": {"domain": "superbom", "syn": ["位號", "refdes", "ref des", "designator", "location"]},
    "manufacturer":  {"domain": "superbom", "syn": ["製造商", "廠商", "mfr", "maker", "vendor", "供應商", "原廠"]},
    "description":   {"domain": "superbom", "syn": ["描述", "品名", "說明", "desc", "spec", "規格"]},
    "case_id":       {"domain": "vmt", "syn": ["案號", "專案編號", "case", "case no", "專案", "project id"]},
    "activity":      {"domain": "vmt", "syn": ["活動", "事件", "作業", "action", "step", "任務"]},
    "timestamp":     {"domain": "vmt", "syn": ["時間", "時戳", "日期時間", "ts", "datetime", "time"]},
    "follow_up":     {"domain": "vmt", "syn": ["跟催", "追蹤", "催辦", "followup", "chase"]},
    "reminder":      {"domain": "vmt", "syn": ["提醒", "提醒信", "remind"]},
    "warning":       {"domain": "vmt", "syn": ["警告", "延誤警示", "warn", "overdue", "延誤"]},
    "quarantine":    {"domain": "seam", "syn": ["隔離", "檢疫", "quarantine", "q01", "待決"]},
    "eta":           {"domain": "vmt", "syn": ["預計完成", "承諾日", "交期", "deadline", "due", "committed date"]},
}

# provider 字彙(NS_PROVIDER,curated=V):用來把 Extraction Matrix 的「主要來源」
# 自動歸類,消掉 register check 的 DS_PROVIDER_CLASSIFICATION UNCLASSIFIED WARN。
PROVIDER_SEED = {
    "TWSE":        ["臺灣證券交易所", "台灣證券交易所", "證交所", "T86", "MI_MARGN", "MI_INDEX", "當日沖銷", "當沖", "PCF", "主動式ETF專頁", "openapi.twse", "STOCK_DAY"],
    "TPEX":        ["櫃買中心", "櫃買", "OTC", "tpex", "上櫃"],
    "MOPS":        ["公開資訊觀測站", "mopsfin"],
    "TDCC":        ["集保", "集保結算所", "股權分散", "借券"],
    "SITCA":       ["投信投顧公會", "公會", "受益人數"],
    "FRED":        ["St. Louis Fed", "stlouisfed", "DGS10", "WALCL", "DTWEXBGS", "DCOILWTICO", "DCOILBRENTEU", "BAMLH0A0HYM2", "BAMLC0A0CM", "殖利率系列"],
    "CBOE":        ["VIX", "Put/Call", "PutCall", "選擇權情緒"],
    "ICI":         ["ICI週度", "ICI 週報", "ICI週報", "貨幣市場基金", "MMF"],
    "EPFR":        ["EPFR Global", "fund flows"],
    "IIF":         ["國際金融協會"],
    "CFTC":        ["COT", "Commitments of Traders", "期貨部位"],
    "EIA":         ["能源資訊署", "週儲", "Cushing", "DHHNGSP"],
    "OPEC":        ["MOMR", "OPEC月報"],
    "USDA":        ["WASDE", "農業部"],
    "LME":         ["倫敦金屬交易所", "LME倉儲"],
    "LBMA":        ["倫敦金銀市場協會", "持金噸數"],
    "WGC":         ["World Gold Council", "世界黃金協會"],
    "COMEX":       ["紐約商品期貨"],
    "SHFE":        ["上期所", "上海期貨交易所"],
    "AAII":        ["散戶多空", "AAII週報", "AAII 週報"],
    "CNN":         ["Fear & Greed", "Fear and Greed", "恐懼貪婪"],
    "NAAIM":       ["投顧情緒"],
    "INVESTORS_INTELLIGENCE": ["Investors Intelligence", "II 投顧"],
    "ICE_BOFA":    ["ICE BofA", "MOVE"],
    "FARSIDE":     ["Farside Investors", "farside.co.uk"],
    "COINGECKO":   ["CoinGecko"],
    "CMC":         ["CoinMarketCap", "市值主導率"],
    "BLS":         ["勞工統計局", "美國勞工部"],
    "NBS":         ["中國統計局", "國家統計局"],
    "CAIXIN":      ["財新", "Caixin PMI"],
    "ISM":         ["供應管理協會"],
    "SP_GLOBAL":   ["S&P Global", "標普全球"],
    "TRUFLATION":  ["民間CPI"],
    "CLEVELAND_FED": ["Cleveland Fed", "Nowcast"],
    "MIT_BPP":     ["MIT BPP", "Billion Prices"],
    "BIS":         ["國際清算銀行", "policy rates"],
    "US_TREASURY": ["美國財政部", "標售", "bid-to-cover", "TIC"],
    "NY_FED":      ["紐約聯儲", "H.4.1", "primary dealer"],
    "BALTIC_EXCHANGE": ["波羅的海交易所", "BDI", "運價"],
    "AKSHARE":     ["北向AKShare", "北向"],
    "NSDL":        ["印度存託"],
    "BOJ":         ["日銀", "日本央行"],
    "ETF_ISSUER":  ["issuer", "發行商", "創贖", "創造贖回", "issuer AUM", "holdings 明細", "issuer 官方", "投組"],
    "YFINANCE":    ["Yahoo Finance", "yahoo", "收盤 adj"],
    "FACTSET":     ["付費"],
    "YARDENI":     ["Yardeni Research", "factsheet"],
    "MOF_TW":      ["財政部", "出口值"],
    "MOEA_TW":     ["經濟部", "出口訂單"],
    "CENTRAL_BANKS": ["各央行", "央行", "Fed", "ECB", "台CBC", "PBOC", "BOK", "RBI"],
    "VIA_INTERNAL": ["File1", "VDF 計算", "計算", "衍生", "harness E3", "grouping", "MI_Code_Appendix"],
    # v0300 補強:消掉 v0200 剩餘未歸類
    "ONCHAIN":     ["鏈上", "on-chain", "onchain", "市值/鏈上", "鏈上數據"],
    "INDEX_COMPONENTS": ["成分 NetFlow", "成分", "NetFlow", "權值", "QQQ 權值", "Mag7", "成分股"],
    "OFFICIAL_POOL": ["官方/機構", "官方/供應商", "官方/公會", "官方", "機構彙總"],
}

# =============================================================================
#  v0400 ── 三種台股代號「鎖死定義」(LOCKED:gate 逐 run 防篡改比對)
#  普通股 4 碼、首碼 1-9(依定義排除 0 開頭之 ETF/權證/特別股)
# =============================================================================
TW_TICKER_LOCK = {
    "tw_ticker": {
        "syn": ["台股代號", "股票代號", "證券代號", "公司代號", "ticker", "stock code", "個股代碼"],
        "patterns": [
            r"^[1-9]\d{3}$",                                   # 嚴格驗證
            r"(?<!\d)[1-9]\d{3}(?!\d)",                        # 文章擷取(前後無數字)
            # 三合一萬用(Group1=純代號);\b 遇中文會失效 → 用 (?![A-Za-z0-9])
            r"(?<!\d)([1-9]\d{3})(?:\.(?:TW|TWO)| TT)?(?![A-Za-z0-9])",
        ],
        "tests_hit": ["2330", "台積電2330大漲", "3293.TWO", "2330 TT"],
        "tests_miss": ["12345", "0050", "234"],
    },
    "tw_ticker_yfinance": {
        "syn": ["yfinance ticker", "yahoo ticker", "雅虎代號", ".TW", ".TWO"],
        "patterns": [
            r"^[1-9]\d{3}\.(?:TW|TWO)$",                       # 嚴格驗證
            r"(?<!\d)[1-9]\d{3}\.(?:TW|TWO)(?![A-Za-z0-9])",   # 文章擷取(中文相鄰亦可)
        ],
        "tests_hit": ["2330.TW", "3293.TWO", "外資買超2330.TW今日"],
        "tests_miss": ["2330.TWX", "0050.TW", "2330"],
    },
    "tw_ticker_bloomberg": {
        "syn": ["bloomberg ticker", "彭博代號", "TT equity", "TT 代號"],
        "patterns": [
            r"^[1-9]\d{3} TT$",                                # 嚴格驗證
            r"(?<!\d)[1-9]\d{3} TT(?![A-Za-z0-9])",            # 文章擷取(中文相鄰亦可)
        ],
        "tests_hit": ["2330 TT", "報告提及3293 TT目標價"],
        "tests_miss": ["2330TT", "0050 TT", "2330 tt"],
    },
}

# =============================================================================
#  v0400 ── 時間/日期 regex pack(NS_TEMPORAL,curated=V,內建測試向量)
#  含西元/民國、年/年月/年月日、年季(2024Q1·24Q1·1Q24·1Q2024·第一季)、
#  半年、會計年度、週數、ISO時間/時區、純數字連寫、相對日期
# =============================================================================
TEMPORAL_SEED = {
    "date_year": {
        "syn": ["年份", "西元年", "民國年", "year"],
        "ssot": "YYYY",
        "patterns": [r"^(?:西元)?(?:19|20)\d{2}年?$|^(?:民國)?\d{1,3}年?$"],
        "tests_hit": ["2024", "西元2024", "2024年", "民國113年", "113"],
        "tests_miss": ["24567", "abc"],
    },
    "date_year_month": {
        "syn": ["年月", "year month"],
        "ssot": "YYYY-MM",
        "patterns": [r"(?:(?:西元)?(?:19|20)\d{2}|(?:民國)?\d{1,3})(?:年|[/\-.])(?:0?[1-9]|1[0-2])月?"],
        "tests_hit": ["2024/08", "113年8月", "2024.08", "民國113年08月"],
        "tests_miss": ["2024/13"],
    },
    "date_ymd": {
        "syn": ["年月日", "完整日期", "date"],
        "ssot": "YYYY-MM-DD (ISO 8601)",
        "patterns": [
            r"(?:(?:西元)?(?:19|20)\d{2}|(?:民國)?\d{1,3})\s*年\s*(?:0?[1-9]|1[0-2])\s*月\s*(?:0?[1-9]|[12]\d|3[01])\s*日",
            r"(?:(?:19|20)\d{2}|\d{2,3})([/\-.])(?:0?[1-9]|1[0-2])\1(?:0?[1-9]|[12]\d|3[01])",
        ],
        "tests_hit": ["2024年8月1日", "民國113年08月01日", "2024/08/01", "113-8-1", "2024.08.01"],
        "tests_miss": ["2024/08-01"],
    },
    "date_quarter": {
        "syn": ["年季", "季度", "quarter", "財報季"],
        "ssot": "YYYY-Qn",
        "patterns": [
            r"(?:(?:西元)?(?:19|20)\d{2}|(?:民國)?\d{1,3}|\d{2})(?:年|[\s/\-.])?(?:[Qq][1-4]|[1-4][Qq]|第[1-4一二三四]季)"
            r"|(?:[Qq][1-4]|[1-4][Qq]|第[1-4一二三四]季)[\s/\-.]?(?:(?:西元)?(?:19|20)\d{2}|(?:民國)?\d{1,3}|\d{2})年?",
        ],
        "tests_hit": ["2024Q1", "24Q1", "1Q24", "1Q2024", "2024年第一季", "113年第1季", "Q1 2024", "第一季2024年"],
        "tests_miss": ["Q5", "5Q24"],
    },
    "date_half": {
        "syn": ["半年期", "上半年", "下半年", "half year"],
        "ssot": "YYYY-Hn",
        "patterns": [
            r"(?:(?:西元)?(?:19|20)\d{2}|(?:民國)?\d{1,3}|\d{2})(?:年|[\s/\-.])?(?:[Hh][12]|[12][Hh]|(?:上|下)半年)"
            r"|(?:[Hh][12]|[12][Hh]|(?:上|下)半年)[\s/\-.]?(?:(?:西元)?(?:19|20)\d{2}|(?:民國)?\d{1,3}|\d{2})年?"
            r"|(?:上|下)半年",   # 單獨出現(年份由上下文補)
        ],
        "tests_hit": ["1H24", "24H1", "2024H2", "2024年上半年", "下半年"],
        "tests_miss": ["3H24"],
    },
    "fiscal_year": {
        "syn": ["會計年度", "財年", "fiscal year"],
        "ssot": "FYYYYY",
        "patterns": [r"FY\s?(?:19|20)?\d{2}|(?:19|20)\d{2}\s?財年|\d{2}/\d{2}\s?財年"],
        "tests_hit": ["FY24", "FY2024", "2024財年", "23/24財年"],
        "tests_miss": ["FY", "財年"],
    },
    "date_week": {
        "syn": ["週數", "week number", "工作週"],
        "ssot": "YYYY-Wnn",
        "patterns": [r"(?:(?:19|20)\d{2}|\d{2})[\s/\-]?[Ww](?:0?[1-9]|[1-4]\d|5[0-3])\b|(?:Wk\s*|第)(?:0?[1-9]|[1-4]\d|5[0-3])\s?週"],
        "tests_hit": ["2024-W15", "24W15", "第15週", "Wk 15週"],
        "tests_miss": ["W54"],
    },
    "date_time_iso": {
        "syn": ["時間", "時分秒", "時區", "timestamp", "ISO 8601 time"],
        "ssot": "hh:mm:ss±TZ",
        "patterns": [
            r"(?:[01]\d|2[0-3]):[0-5]\d(?::[0-5]\d)?(?:\.\d+)?\s*(?:[AaPp][Mm]|上午|下午)?\s*(?:UTC|GMT|CST|EST|[+-]\d{2}:?\d{2})?",
            r"T(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d(?:Z|[+-]\d{2}:?\d{2})",
        ],
        "tests_hit": ["14:30:00", "02:30 PM", "2024-08-01T14:30:00Z", "14:30 UTC+8"],
        "tests_miss": ["25:00"],
    },
    "date_pure_digit": {
        "syn": ["純數字日期", "8碼日期", "7碼民國日期"],
        "ssot": "YYYYMMDD",
        "patterns": [r"(?<!\d)(?:(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])|1[01]\d(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01]))(?!\d)"],
        "tests_hit": ["20240801", "1130801"],
        "tests_miss": ["20241301", "202408012"],
    },
    "date_relative": {
        "syn": ["相對日期", "月底", "年底", "EOM", "EOY", "YTD"],
        "ssot": "resolve-by-context",
        "patterns": [r"(?i)\b(?:EOM|EOY|YTD|YoY|MoM|Today|Tomorrow|Yesterday)\b|(?:今|明|昨|前)(?:天|日|年)|(?:本|上|下)(?:週|星期|個月)|(?:年|月)(?:底|初|中)"],
        "tests_hit": ["月底", "EOM", "今天", "下週", "YTD", "年初"],
        "tests_miss": ["天今"],
    },
}

# TWSE / TPEX OpenAPI(在你的機器上執行 --fetch-tw 即時抓;沙箱離線用 --tw-source 測)
TWSE_API = "https://openapi.twse.com.tw/v1/opendata/t187ap03_L"
TPEX_API = "https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O"
_TW_STRICT = re.compile(r"^[1-9]\d{3}$")


# =============================================================================
#  Normalization / tokenization
# =============================================================================
def norm(s):
    """正規化鍵:NFKC(統一全半形)→ casefold → 收斂分隔符與空白。"""
    if s is None:
        return ""
    s = unicodedata.normalize("NFKC", str(s))
    s = s.casefold().strip()
    s = re.sub(r"[\s_\-/\\.·、,，:：;；()（）\[\]【】]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def variants(term):
    """自動擴大:由一個詞衍生確定式變體(不含模糊猜測)。"""
    out = set()
    raw = str(term).strip()
    if not raw:
        return out
    base = unicodedata.normalize("NFKC", raw)
    cores = {base, base.casefold(), base.upper(), base.lower(), base.title()}
    # 分隔符互換
    seps = re.split(r"[\s_\-/]+", base)
    if len(seps) > 1:
        joined = "".join(seps)
        for j in ("_", "-", " ", ""):
            cores.add(j.join(seps))
        cores.add(joined)
        # 縮寫(取每段首字,僅 ASCII 詞)
        if all(re.match(r"^[A-Za-z0-9]+$", p) for p in seps if p):
            acr = "".join(p[0] for p in seps if p)
            if 3 <= len(acr) <= 6:   # 2 字縮寫過度泛用(如 in/is)→ 不生成
                cores.add(acr)
    for c in cores:
        c = c.strip()
        if c:
            out.add(c)
    return out


def ratio(a, b):
    return SequenceMatcher(None, a, b).ratio()


def token_set_overlap(a, b):
    ta, tb = set(a.split()), set(b.split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def match_score(token_norm, cand_norm):
    """未知 token 對 canonical/synonym 的就近分數。"""
    if token_norm == cand_norm:
        return 1.0
    r = ratio(token_norm, cand_norm)
    o = token_set_overlap(token_norm, cand_norm)
    contain = 0.0
    if token_norm and cand_norm and (token_norm in cand_norm or cand_norm in token_norm):
        contain = 0.85
    return max(r, o, contain)


# =============================================================================
#  ID / code (blake2s;hash input = term,LL#30 可驗證)
# =============================================================================
def code_for(term, first_seen, ns=NS_CORE):
    # LL#30:hash inputs 存於 SSOT(term+namespace 皆在 canonical 記錄內)可驗證
    seed = "CGE|" + str(term) if ns == NS_CORE else "CGE|%s|%s" % (ns, term)
    h = hashlib.blake2s(seed.encode("utf-8"), digest_size=3).hexdigest().upper()
    day = first_seen.replace("-", "")[:8] if first_seen else "00000000"
    return "VIA-%s-%s-%s" % (ID_TYPE, day, h)


def tw_ticker_variants(code):
    """TW 4-5 碼(含債券ETF末碼B/主動末碼A/D)→ .TW/.TWO/Bloomberg TT 三重衍生。"""
    if not re.match(r"^\d{4,6}[ABD]?$", code):
        return set()
    return {code + ".TW", code + ".TWO", code + " TT"}


def now_iso():
    return _dt.datetime.now().replace(microsecond=0).isoformat()


def today():
    return _dt.date.today().isoformat()


# =============================================================================
#  Vocab SSOT I/O
# =============================================================================
def blank_vocab():
    return {
        "meta": {
            "schema": SCHEMA,
            "engine": ENGINE,
            "version": VERSION,
            "id_format": "VIA-%s-YYYYMMDD-HEX6" % ID_TYPE,
            "principle": "only-increase (只增不減)",
            "created": now_iso(),
            "runs": 0,
        },
        "canonicals": {},   # cid -> {term, domain, status, code, synonyms[], regex, regex_source, first_seen}
        "quarantine": [],   # {token, freq, nearest, score, decided_run}
    }


def load_json(path, default):
    if path and os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                return json.load(f)
        except Exception as e:
            print("  ! 讀取失敗 %s: %s" % (path, e))
    return default


def save_json(path, obj):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def append_ledger(path, event):
    line = json.dumps(event, ensure_ascii=False)
    with open(path, "a", encoding="utf-8", newline="\n") as f:
        f.write(line + "\n")


# =============================================================================
#  Corpus harvesting — auto-import live state
# =============================================================================
LIVE_HINTS = [
    "domain_keywords.json", "ssot.json", "events.jsonl", "confirmations.jsonl",
    "convergence_state.json", "master_state.json",
]


def discover_sources(roots, exclude=None):
    """探索語料來源;exclude 為引擎自身產出的絕對路徑(避免回饋汙染)。"""
    exclude = exclude or set()

    def excluded(p):
        ap = os.path.abspath(p)
        if ap in exclude:
            return True
        base = os.path.basename(p)
        return bool(re.match(r"^(governance_(vocab|ledger)|via_cge_)", base) or
                    base.startswith("VIA_CentralGovernance"))

    found = []
    seen = set()
    for root in roots:
        if os.path.isfile(root):
            if root not in seen and not excluded(root):
                found.append(root); seen.add(root)
            continue
        if not os.path.isdir(root):
            continue
        for hint in LIVE_HINTS:
            for p in glob.glob(os.path.join(root, "**", hint), recursive=True):
                if p not in seen and not excluded(p):
                    found.append(p); seen.add(p)
        for ext in ("*.csv", "*.tsv", "*.txt", "*.jsonl"):
            for p in glob.glob(os.path.join(root, "**", ext), recursive=True):
                if p not in seen and not excluded(p):
                    found.append(p); seen.add(p)
    return found


def _walk_strings(obj, out):
    if isinstance(obj, str):
        out.append(obj)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(k, str):
                out.append(k)
            _walk_strings(v, out)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            _walk_strings(v, out)


def harvest(path):
    """回傳該來源的候選 token 清單(原文,尚未正規化)。"""
    toks = []
    low = path.lower()
    try:
        if low.endswith(".json"):
            data = load_json(path, None)
            strs = []
            _walk_strings(data, strs)
            for s in strs:
                toks.extend(re.split(r"[\|,;\t]+", s))
        elif low.endswith(".jsonl"):
            with open(path, "r", encoding="utf-8-sig") as f:
                for ln in f:
                    ln = ln.strip()
                    if not ln:
                        continue
                    try:
                        obj = json.loads(ln)
                        strs = []
                        _walk_strings(obj, strs)
                        toks.extend(strs)
                    except Exception:
                        toks.append(ln)
        elif low.endswith((".csv", ".tsv")):
            sep = "\t" if low.endswith(".tsv") else ","
            with open(path, "r", encoding="utf-8-sig") as f:
                head = f.readline()
                toks.extend(head.split(sep))            # 表頭最重要
                for i, ln in enumerate(f):
                    if i > 500:
                        break
                    toks.extend(ln.split(sep))
        else:  # txt / 其他
            with open(path, "r", encoding="utf-8-sig", errors="ignore") as f:
                for i, ln in enumerate(f):
                    if i > 2000:
                        break
                    toks.extend(re.split(r"[\|,;\t]+", ln))
    except Exception as e:
        print("  ! harvest 失敗 %s: %s" % (path, e))
    # 清洗
    clean = []
    for t in toks:
        t = str(t).strip().strip("\"'")
        if t:
            clean.append(t)
    return clean


# =============================================================================
#  Pipeline
# =============================================================================
def build_lookup(vocab):
    """norm(text) -> cid  (canonical 詞與所有 synonym)"""
    lut = {}
    for cid, c in vocab["canonicals"].items():
        if c.get("status") == ST_ABSORBED:
            continue
        lut[norm(c["term"])] = cid
        for syn in c.get("synonyms", []):
            lut[norm(syn["text"])] = cid
    return lut


def migrate_vocab(vocab):
    """v1→v2 就地補欄位(只增不減:不動既有資料,只補預設)。"""
    for c in vocab["canonicals"].values():
        c.setdefault("namespace", NS_CORE)
        c.setdefault("attrs", {})
        c.setdefault("regex_curated", [])
    vocab["meta"]["schema"] = SCHEMA
    vocab.setdefault("gate_checks", [])


def ensure_canonical(vocab, term, domain, ledger_events, run,
                     ns=NS_CORE, attrs=None):
    key = norm(term)
    for cid, c in vocab["canonicals"].items():
        if c.get("namespace", NS_CORE) == ns and norm(c["term"]) == key:
            if attrs:  # 只增:補上還沒有的屬性,不覆蓋既有
                for k, v in attrs.items():
                    c["attrs"].setdefault(k, v)
            return cid
    fs = today()
    cid = code_for(term, fs, ns)
    vocab["canonicals"][cid] = {
        "term": term,
        "domain": domain or "unassigned",
        "namespace": ns,
        "status": ST_ACTIVE,
        "code": cid,
        "first_seen": fs,
        "synonyms": [],
        "regex": [],
        "regex_source": "",
        "regex_curated": [],
        "attrs": dict(attrs or {}),
    }
    ledger_events.append({"ts": now_iso(), "run": run, "op": "CANONICAL_ADD",
                          "cid": cid, "term": term, "domain": domain, "ns": ns})
    return cid


def add_curated_regex(vocab, cid, patterns, source, run, ledger_events):
    """人工 regex 以 V 級入庫;與 auto regex 並存,只增不減。回傳新增數。"""
    c = vocab["canonicals"][cid]
    added = 0
    have = {r["pattern"] for r in c["regex_curated"]}
    for p in patterns:
        if p in have:
            continue
        try:
            re.compile(p)
            ok = True
        except re.error:
            ok = False
        c["regex_curated"].append({"pattern": p, "evidence": EV_HUMAN,
                                   "source": source, "compiles": ok,
                                   "first_seen": today(), "run": run})
        have.add(p)
        added += 1
        ledger_events.append({"ts": now_iso(), "run": run, "op": "REGEX_CURATED_ADD",
                              "cid": cid, "pattern": p, "compiles": ok})
    return added


def add_synonym(vocab, cid, text, evidence, source, run, ledger_events):
    """append-only:只增不減。回傳 True 若為新增。"""
    c = vocab["canonicals"][cid]
    nkey = norm(text)
    if not nkey or nkey == norm(c["term"]):
        return False
    for syn in c["synonyms"]:
        if norm(syn["text"]) == nkey:
            # 只升不降 evidence
            if EV_RANK.get(evidence, 0) > EV_RANK.get(syn["evidence"], 0):
                syn["evidence"] = evidence
                syn["source"] = source
                ledger_events.append({"ts": now_iso(), "run": run, "op": "SYN_UPGRADE",
                                      "cid": cid, "text": text, "evidence": evidence})
            return False
    c["synonyms"].append({"text": text, "evidence": evidence, "source": source,
                          "first_seen": today(), "run": run})
    ledger_events.append({"ts": now_iso(), "run": run, "op": "SYN_ADD",
                          "cid": cid, "text": text, "evidence": evidence, "source": source})
    return True


def synth_regex(vocab, cid, params):
    """依同義字集自動合成 regex(escape + alternation,長者優先),驗證可編譯。"""
    c = vocab["canonicals"][cid]
    terms = [c["term"]] + [s["text"] for s in c["synonyms"]
                           if s["evidence"] != EV_PEND]
    # 去重(以正規化),保留原文
    seen, uniq = set(), []
    for t in sorted(terms, key=lambda x: -len(x)):
        k = norm(t)
        if k and k not in seen:
            seen.add(k)
            uniq.append(t)
    if not uniq:
        c["regex"] = []
        return
    alts = []
    for t in uniq:
        esc = re.escape(t.strip())
        # 允許 _ - 空白 互換
        esc = re.sub(r"\\[ _\\-]", r"[\\s_\\-]?", esc)
        alts.append(esc)
    body = "|".join(alts)
    ascii_only = all(re.match(r"^[\x00-\x7f]+$", t) for t in uniq)
    # v0300:字首/字尾非 word 字元(如 ^GSPC)時 \b 會失效 → 不加邊界(自測抓到的 bug)
    word_edges = all(re.match(r"^\w.*\w$|^\w$", t) for t in uniq)
    if params["word_boundary_ascii"] and ascii_only and word_edges:
        pat = r"(?i)\b(?:%s)\b" % body
    else:
        pat = r"(?i)(?:%s)" % body
    try:
        re.compile(pat)
        c["regex"] = [pat]
        c["regex_source"] = "auto:alternation(%d)" % len(uniq)
    except re.error as e:
        c["regex"] = []
        c["regex_source"] = "ERROR:%s" % e


# =============================================================================
#  v0200 ── Curated pattern-library import (AST,不 import 不執行對方程式碼)
# =============================================================================
def import_curated(path, vocab, ledger_events, run):
    """AST 解析 PatternDef(name=…, name_en=…, patterns=[…], category=…, statement=…,
    validation_level=…, unit=…)→ NS_FINREPORT 詞條;人工 regex 以 V 級入庫。"""
    stats = {"canon": 0, "regex": 0, "syn": 0, "skipped": 0}
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            tree = ast.parse(f.read())
    except Exception as e:
        print("  ! curated 解析失敗 %s: %s" % (path, e))
        return stats

    def const(node):
        return node.value if isinstance(node, ast.Constant) else None

    def attr_name(node):  # CategoryType.CURRENT_ASSET → CURRENT_ASSET
        return node.attr if isinstance(node, ast.Attribute) else None

    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and
                getattr(node.func, "id", getattr(node.func, "attr", "")) == "PatternDef"):
            continue
        kw = {k.arg: k.value for k in node.keywords}
        name = const(kw.get("name"))
        if not name:
            stats["skipped"] += 1
            continue
        name_en = const(kw.get("name_en")) or ""
        pats = []
        if isinstance(kw.get("patterns"), (ast.List, ast.Tuple)):
            pats = [const(e) for e in kw["patterns"].elts if const(e)]
        attrs = {
            "name_en": name_en,
            "category": attr_name(kw.get("category")) or "",
            "statement": attr_name(kw.get("statement")) or "",
            "validation_level": attr_name(kw.get("validation_level")) or "OPTIONAL",
            "unit": const(kw.get("unit")) or "元",
            "curated_from": os.path.basename(path),
        }
        cid = ensure_canonical(vocab, name, "finreport", ledger_events, run,
                               ns=NS_FINREPORT, attrs=attrs)
        stats["canon"] += 1
        if name_en and add_synonym(vocab, cid, name_en, EV_HUMAN,
                                   "curated:name_en", run, ledger_events):
            stats["syn"] += 1
        # 由 curated regex 反抽「純字面」pattern 當同義字(讓 auto 擴大接手變體)
        for p in pats:
            lit = p
            if re.match(r"^[\w一-鿿 &/\-]+$", lit):
                if add_synonym(vocab, cid, lit, EV_HUMAN, "curated:literal",
                               run, ledger_events):
                    stats["syn"] += 1
        stats["regex"] += add_curated_regex(vocab, cid, pats,
                                            "curated:%s" % os.path.basename(path),
                                            run, ledger_events)
    return stats


# =============================================================================
#  v0200 ── Extraction Matrix import(dataset / instrument / provider 歸類)
# =============================================================================
def classify_provider(vocab, text):
    """用 NS_PROVIDER 字彙掃 primary-source 字串 → 命中的 provider terms(可多個)。"""
    hits = []
    t_norm = norm(text)
    raw = str(text)
    for cid, c in vocab["canonicals"].items():
        if c.get("namespace") != NS_PROVIDER or c.get("status") == ST_ABSORBED:
            continue
        cands = [c["term"]] + [s["text"] for s in c["synonyms"]]
        for cand in cands:
            cn = norm(cand)
            if not cn or len(cn) < 2:
                continue
            if cn in t_norm or cand in raw:
                hits.append(c["term"])
                break
    return sorted(set(hits))


_TICKER_RE = re.compile(r"\^[A-Z0-9]{2,10}|[0-9]{4,6}[ABD]?\.HK|[0-9]{6}|[0-9]{4,6}[ABD]?|[A-Z]{2,5}(?![a-z])")


def import_matrix(path, vocab, ledger_events, run):
    """CSV 欄位:#,大項目,小項目,標的/代碼,主要來源,頻率,多來源並存,證據層,用途,QA。"""
    import csv as _csv
    stats = {"datasets": 0, "instruments": 0, "classified": 0, "unclassified": [],
             "tw_derived": 0}
    try:
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            rows = list(_csv.DictReader(f))
    except Exception as e:
        print("  ! matrix 讀取失敗 %s: %s" % (path, e))
        return stats
    for row in rows:
        cat = (row.get("大項目") or "").strip()
        name = (row.get("小項目") or "").strip()
        if not name:
            continue
        src = (row.get("主要來源") or "").strip()
        providers = classify_provider(vocab, src) or classify_provider(vocab, name)
        attrs = {
            "matrix_no": (row.get("#") or "").strip(),
            "category": cat,
            "primary_source": src,
            "frequency": (row.get("頻率") or "").strip(),
            "tier": (row.get("證據層") or "").strip(),
            "usage": (row.get("用途") or "").strip(),
            "providers": providers,
            "qa": (row.get("QA") or "").strip(),
        }
        term = "%s|%s" % (cat.split("·")[0].strip(), name) if cat else name
        cid = ensure_canonical(vocab, term, "dataset", ledger_events, run,
                               ns=NS_DATASET, attrs=attrs)
        stats["datasets"] += 1
        if providers:
            stats["classified"] += 1
        else:
            stats["unclassified"].append(term)
        if name and add_synonym(vocab, cid, name, EV_HUMAN, "matrix:小項目",
                                run, ledger_events):
            pass
        # ---- instrument 拆解:標的/代碼 以 · 分段,段內 名稱+代碼 互為別名 ----
        targets = (row.get("標的/代碼") or "").strip()
        for seg in re.split(r"[·;]| · ", targets):
            seg = seg.strip()
            if not seg or seg.startswith(("Σ", "—")):
                continue
            codes = [c0 for c0 in _TICKER_RE.findall(seg)
                     if not c0.isdigit() or len(c0) >= 4]
            codes = [c0 for c0 in codes if c0 not in ("EOD", "GICS", "SSOT")]
            if not codes:
                continue
            label = re.split(r"[\s/]", seg)[0].strip()
            term_i = codes[0]
            attrs_i = {"category": cat, "dataset": name}
            cid_i = ensure_canonical(vocab, term_i, "instrument", ledger_events,
                                     run, ns=NS_INSTRUMENT, attrs=attrs_i)
            stats["instruments"] += 1
            aliases = set(codes[1:])
            if label and not _TICKER_RE.fullmatch(label):
                aliases.add(label)
            for c0 in list(codes):
                m = re.match(r"^(\d{4,6}[ABD]?)$", c0)  # TW 代碼三重衍生
                if m:
                    tw = tw_ticker_variants(m.group(1))
                    aliases |= tw
                    stats["tw_derived"] += len(tw)
            for a in aliases:
                add_synonym(vocab, cid_i, a, EV_AUTO if a.endswith((".TW", ".TWO", " TT"))
                            else EV_HUMAN, "matrix:標的", run, ledger_events)
    return stats


# =============================================================================
#  v0200 ── SSOT-of-SSOTs 戶政登記 + 整合去重(review-only,不刪任何檔)
# =============================================================================
def family_of(basename):
    """檔名 → SSOT 家族鍵(去版本號/去 RUN 戳,同族不同版歸同一家族)。"""
    b = os.path.splitext(basename)[0]
    b = re.sub(r"(?i)[._-]?v\d{2,4}[a-z]?\b", "", b)
    b = re.sub(r"(?i)RUN[_-]?[\d][\w-]*", "", b)
    b = re.sub(r"\d{8}[_-]\d{6}", "", b)
    b = re.sub(r"[._-]+$", "", b)
    b = norm(b).replace(" ", "_")
    return b or basename.lower()


def _hash_file(path):
    h = hashlib.blake2s(digest_size=8)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def register_ssot(roots, list_files, vocab, ledger_events, run):
    """掃描/清單收 SSOT 檔 → 戶政登記(append-only;消失者標 MISSING 不移除)、
    content-hash 去重(同內容→DUPLICATE of 最早者)、家族歸戶。"""
    reg = vocab.setdefault("ssot_registry", {})
    stats = {"scanned": 0, "new": 0, "missing": 0, "dup_groups": 0, "duplicates": 0}
    paths = []
    for root in (roots or []):
        if not os.path.isdir(root):
            continue
        for p in glob.glob(os.path.join(root, "**", "*"), recursive=True):
            if os.path.isfile(p) and re.search(r"ssot", os.path.basename(p), re.I):
                paths.append(p)
    for lf in (list_files or []):
        if not os.path.isfile(lf):
            print("  ! ssot-list 不存在:%s" % lf)
            continue
        with open(lf, "r", encoding="utf-8-sig") as f:
            for ln in f:
                p = ln.strip().strip('"').strip()
                if p:
                    paths.append(p)
    seen_now = set()
    for p in paths:
        ap = os.path.abspath(p)
        if ap in seen_now:
            continue
        seen_now.add(ap)
        stats["scanned"] += 1
        exists = os.path.isfile(ap)
        e = reg.get(ap)
        if e is None:
            e = {"path": ap, "family": family_of(os.path.basename(ap)),
                 "first_registered": now_iso(), "status": "ACTIVE",
                 "hash": "", "size": 0, "mtime": ""}
            reg[ap] = e
            stats["new"] += 1
            ledger_events.append({"ts": now_iso(), "run": run,
                                  "op": "SSOT_REGISTER", "path": ap,
                                  "family": e["family"]})
        e["last_seen_run"] = run
        if exists:
            try:
                st = os.stat(ap)
                e["hash"] = _hash_file(ap)
                e["size"] = st.st_size
                e["mtime"] = _dt.datetime.fromtimestamp(st.st_mtime).replace(
                    microsecond=0).isoformat()
                if e["status"] == "MISSING":
                    e["status"] = "ACTIVE"
            except Exception as ex:
                e["status"] = "UNREADABLE"
                e["error"] = str(ex)
        else:
            if e["status"] != "MISSING":
                e["status"] = "MISSING"   # 只標不刪(vcc_registry 同規)
                ledger_events.append({"ts": now_iso(), "run": run,
                                      "op": "SSOT_MISSING", "path": ap})
    # 曾登記但本次沒被掃到且檔案已不存在 → MISSING
    for ap, e in reg.items():
        if ap not in seen_now and not os.path.isfile(ap):
            if e["status"] != "MISSING":
                e["status"] = "MISSING"
    # ---- 去重:同 content-hash 群組,最早 mtime 為 canonical,其餘 DUPLICATE ----
    by_hash = {}
    for ap, e in reg.items():
        if e.get("hash") and e["status"] in ("ACTIVE", "DUPLICATE"):
            by_hash.setdefault(e["hash"], []).append(e)
    for h, group in by_hash.items():
        if len(group) < 2:
            if group and group[0]["status"] == "DUPLICATE":
                group[0]["status"] = "ACTIVE"   # 對手消失,升回 canonical
                group[0].pop("dup_of", None)
            continue
        stats["dup_groups"] += 1
        group.sort(key=lambda x: (x.get("mtime") or "9999", x["path"]))
        canon = group[0]
        canon["status"] = "ACTIVE"
        canon.pop("dup_of", None)
        for d in group[1:]:
            if d["status"] != "DUPLICATE" or d.get("dup_of") != canon["path"]:
                d["status"] = "DUPLICATE"
                d["dup_of"] = canon["path"]
                ledger_events.append({"ts": now_iso(), "run": run,
                                      "op": "SSOT_DUPLICATE", "path": d["path"],
                                      "dup_of": canon["path"], "hash": h})
            stats["duplicates"] += 1
    stats["missing"] = sum(1 for e in reg.values() if e["status"] == "MISSING")
    return stats


# =============================================================================
#  v0400 ── 台股代號鎖死 + temporal pack 入庫與測試
# =============================================================================
def seed_locked_and_temporal(vocab, ledger_events, run):
    n_can = n_rx = 0
    not_first = vocab["meta"].get("runs", 0) > 0
    healed = []
    for term, d in TW_TICKER_LOCK.items():
        cid = ensure_canonical(vocab, term, "tw_ticker", ledger_events, run,
                               ns=NS_CORE, attrs={"locked": True,
                                                  "lock_source": "TW_TICKER_LOCK"})
        n_can += 1
        for s in d["syn"]:
            add_synonym(vocab, cid, s, EV_HUMAN, "locked:tw_ticker", run, ledger_events)
        re_added = add_curated_regex(vocab, cid, d["patterns"], "locked:tw_ticker",
                                     run, ledger_events)
        n_rx += re_added
        if not_first and re_added:   # 非首跑還需要補鎖死 pattern = 曾被動過 → 自癒+上報
            healed.append("%s(+%d)" % (term, re_added))
            ledger_events.append({"ts": now_iso(), "run": run,
                                  "op": "LOCK_SELF_HEALED", "term": term,
                                  "restored": re_added})
    vocab["lock_healed"] = healed
    for term, d in TEMPORAL_SEED.items():
        cid = ensure_canonical(vocab, term, "temporal", ledger_events, run,
                               ns=NS_TEMPORAL,
                               attrs={"ssot_format": d["ssot"]})
        n_can += 1
        for s in d["syn"]:
            add_synonym(vocab, cid, s, EV_HUMAN, "seed:temporal", run, ledger_events)
        n_rx += add_curated_regex(vocab, cid, d["patterns"], "seed:temporal",
                                  run, ledger_events)
    return n_can, n_rx


def run_pack_tests(vocab):
    """鎖死/temporal 測試向量:tests_hit 必中、tests_miss 必不中;
    另做防篡改:vocab 內 locked 詞條的 curated regex 必須含鎖死定義原文。"""
    fails = []

    def canon_by_term(term):
        for c in vocab["canonicals"].values():
            if c["term"] == term:
                return c
        return None

    def pats_of(c):
        out = []
        for r in c.get("regex_curated", []):
            if r.get("compiles"):
                try:
                    out.append(re.compile(r["pattern"]))
                except re.error:
                    pass
        return out

    for pack, locked in ((TW_TICKER_LOCK, True), (TEMPORAL_SEED, False)):
        for term, d in pack.items():
            c = canon_by_term(term)
            if not c:
                fails.append("%s:missing" % term)
                continue
            if locked:  # 防篡改:鎖死 pattern 必須逐字存在
                have = {r["pattern"] for r in c.get("regex_curated", [])}
                for p in d["patterns"]:
                    if p not in have:
                        fails.append("%s:TAMPERED(%s…)" % (term, p[:20]))
            pats = pats_of(c)
            for t in d.get("tests_hit", []):
                if not any(p.search(t) for p in pats):
                    fails.append("%s:should-hit:%s" % (term, t))
            for t in d.get("tests_miss", []):
                strict_only = [p for p in pats if p.pattern.startswith("^")]
                # miss 向量以嚴格式優先驗;無嚴格式則全部都不得命中
                check = strict_only or pats
                if any(p.fullmatch(t) for p in check):
                    fails.append("%s:should-miss:%s" % (term, t))
    return fails


def normalize_temporal(text):
    """SSOT 正規化:民國→西元、2碼年→20xx、各式年季/半年/FY/日期 → 唯一標準。"""
    def yr(y):
        y = int(y)
        if y < 100:
            return 2000 + y
        if y < 1000:
            return 1911 + y   # 民國
        return y

    t = str(text).strip()
    m = re.fullmatch(r"(?:西元|民國)?(\d{2,4})(?:年|[\s/\-.])?(?:[Qq]([1-4])|([1-4])[Qq]|第([1-4一二三四])季)", t)
    if not m:
        m2 = re.fullmatch(r"(?:[Qq]([1-4])|([1-4])[Qq]|第([1-4一二三四])季)[\s/\-.]?(?:西元|民國)?(\d{2,4})年?", t)
        if m2:
            q = m2.group(1) or m2.group(2) or {"一": "1", "二": "2", "三": "3", "四": "4"}.get(m2.group(3), m2.group(3))
            return "%d-Q%s" % (yr(m2.group(4)), q)
    else:
        q = m.group(2) or m.group(3) or {"一": "1", "二": "2", "三": "3", "四": "4"}.get(m.group(4), m.group(4))
        return "%d-Q%s" % (yr(m.group(1)), q)
    m = re.fullmatch(r"(?:西元|民國)?(\d{2,4})(?:年|[\s/\-.])?(?:[Hh]([12])|([12])[Hh]|(上|下)半年)", t)
    if m:
        h = m.group(2) or m.group(3) or {"上": "1", "下": "2"}[m.group(4)]
        return "%d-H%s" % (yr(m.group(1)), h)
    m = re.fullmatch(r"FY\s?(\d{2,4})|(\d{4})\s?財年", t)
    if m:
        return "FY%d" % yr(m.group(1) or m.group(2))
    m = re.fullmatch(r"(?:西元|民國)?(\d{2,4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日", t)
    if m:
        return "%d-%02d-%02d" % (yr(m.group(1)), int(m.group(2)), int(m.group(3)))
    m = re.fullmatch(r"(\d{2,4})([/\-.])(\d{1,2})\2(\d{1,2})", t)
    if m:
        return "%d-%02d-%02d" % (yr(m.group(1)), int(m.group(3)), int(m.group(4)))
    m = re.fullmatch(r"((?:19|20)\d{2}|1[01]\d)(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])", t)
    if m:
        return "%d-%s-%s" % (yr(m.group(1)), m.group(2), m.group(3))
    return None


# =============================================================================
#  v0400 ── 台股全市場清單擷取(上市+上櫃)· 版本 diff · DELISTED 只標不刪
# =============================================================================
def _fetch_json(url):
    import urllib.request
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (VIA-CGE)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def _pick(item, *keys):
    for k in keys:
        v = item.get(k)
        if v not in (None, ""):
            return str(v).strip()
    return ""


def fetch_tw_stocks(vocab, ledger_events, run, workdir, sources=None):
    """sources=本地 JSON 檔清單(離線測試);None 則打 TWSE/TPEX OpenAPI。
    tw_stock_registry append-only:新增 ADD、消失標 DELISTED(不刪)。"""
    stats = {"twse": 0, "tpex": 0, "added": [], "delisted": [], "total": 0, "err": []}
    raw = []
    try:
        if sources:
            for i, p in enumerate(sources):
                data = load_json(p, [])
                market = "TWSE" if i == 0 else "TPEX"
                raw.append((market, data))
        else:
            raw.append(("TWSE", _fetch_json(TWSE_API)))
            raw.append(("TPEX", _fetch_json(TPEX_API)))
    except Exception as e:
        stats["err"].append(str(e))
        return stats

    reg = vocab.setdefault("tw_stock_registry", {})
    seen = set()
    for market, data in raw:
        if not isinstance(data, list):
            continue
        for item in data:
            code = _pick(item, "公司代號", "SecuritiesCompanyCode", "Code")
            if not _TW_STRICT.fullmatch(code):
                continue   # 鎖死定義:僅 4 碼、首碼 1-9 普通股
            name = _pick(item, "公司名稱", "CompanyName", "Name")
            name_en = _pick(item, "英文簡稱", "英文簡稱名稱", "CompanyAbbreviationEnglish")
            seen.add(code)
            stats["twse" if market == "TWSE" else "tpex"] += 1
            e = reg.get(code)
            rec = {
                "TICKER": code, "MARKET": market, "NAME": name, "NAME_EN": name_en,
                "YFINANCE": "%s.%s" % (code, "TW" if market == "TWSE" else "TWO"),
                "BLOOMBERG": "%s TT" % code,
                "status": "ACTIVE", "last_seen": today(),
            }
            if e is None:
                rec["first_seen"] = today()
                reg[code] = rec
                stats["added"].append("%s %s" % (code, name))
                ledger_events.append({"ts": now_iso(), "run": run,
                                      "op": "TWSTOCK_ADD", "ticker": code,
                                      "name": name, "market": market})
            else:
                e.update({k: rec[k] for k in ("MARKET", "NAME", "NAME_EN",
                                              "YFINANCE", "BLOOMBERG", "last_seen")})
                if e.get("status") == "DELISTED":
                    e["status"] = "ACTIVE"   # 重新上市
                else:
                    e["status"] = "ACTIVE"
    for code, e in reg.items():
        if code not in seen and e.get("status") == "ACTIVE":
            e["status"] = "DELISTED"       # 只標不刪(只增不減)
            stats["delisted"].append("%s %s" % (code, e.get("NAME", "")))
            ledger_events.append({"ts": now_iso(), "run": run,
                                  "op": "TWSTOCK_DELIST", "ticker": code})
    stats["total"] = sum(1 for e in reg.values() if e["status"] == "ACTIVE")
    # 輸出 CSV(utf-8-sig 防 Excel 亂碼)
    csv_path = os.path.join(workdir, "tw_stock_tickers_latest.csv")
    with open(csv_path, "w", encoding="utf-8-sig", newline="\n") as f:
        f.write("TICKER,YFINANCE TICKER,BLOOMBERG TICKER,MARKET,NAME,NAME(EN),STATUS\n")
        for code in sorted(reg):
            e = reg[code]
            f.write('%s,%s,%s,%s,"%s","%s",%s\n'
                    % (e["TICKER"], e["YFINANCE"], e["BLOOMBERG"], e["MARKET"],
                       e.get("NAME", ""), e.get("NAME_EN", ""), e["status"]))
    return stats


# =============================================================================
#  v0300 ── 確認迴路(==CGE-CONFIRM== / JSONL,ACCEPT升V · REJECT名冊 · NEW開戶)
# =============================================================================
_CONFIRM_TOKEN_RE = re.compile(r"==CGE-CONFIRM==\s*(.+?)\s*(?:=>|->)\s*(\S.*)$")


def ingest_confirmations(files, vocab, ledger_events, run):
    stats = {"accept": 0, "reject": 0, "new": 0, "bad": 0}
    rejected = vocab.setdefault("rejected", [])
    rej_norms = {norm(r["text"]) for r in rejected}

    def find_canonical(term):
        key = norm(term)
        best = None
        for cid, c in vocab["canonicals"].items():
            if c.get("status") == ST_ABSORBED:
                continue
            if norm(c["term"]) == key or any(norm(s["text"]) == key
                                             for s in c["synonyms"]):
                ns = c.get("namespace", NS_CORE)
                if ns in (NS_CORE, NS_FINREPORT):
                    return cid
                best = best or cid
        return best

    for path in files:
        if not os.path.isfile(path):
            continue
        with open(path, "r", encoding="utf-8-sig") as f:
            for ln in f:
                ln = ln.strip()
                if not ln:
                    continue
                text = canonical = None
                decision = "ACCEPT"
                try:
                    obj = json.loads(ln)
                    text = obj.get("text")
                    canonical = obj.get("canonical")
                    decision = (obj.get("decision") or "ACCEPT").upper()
                except Exception:
                    m = _CONFIRM_TOKEN_RE.search(ln)
                    if m:
                        text, canonical = m.group(1), m.group(2)
                        if norm(canonical) in ("reject", "拒絕"):
                            decision, canonical = "REJECT", None
                        elif norm(canonical) in ("new", "新增"):
                            decision, canonical = "NEW", None
                if not text:
                    stats["bad"] += 1
                    continue
                if decision == "REJECT":
                    if norm(text) not in rej_norms:
                        rejected.append({"text": text, "run": run, "ts": now_iso()})
                        rej_norms.add(norm(text))
                        ledger_events.append({"ts": now_iso(), "run": run,
                                              "op": "CONFIRM_REJECT", "text": text})
                    stats["reject"] += 1
                elif decision == "NEW":
                    ensure_canonical(vocab, text, "confirmed", ledger_events, run)
                    stats["new"] += 1
                else:
                    cid = find_canonical(canonical or "")
                    if cid:
                        add_synonym(vocab, cid, text, EV_HUMAN,
                                    "human:confirm", run, ledger_events)
                        stats["accept"] += 1
                    else:
                        stats["bad"] += 1
    return stats


# =============================================================================
#  v0300 ── regex 自測 harness(同義字回測 auto+curated)
# =============================================================================
def regex_selftest(vocab):
    total = miss_total = 0
    gaps = []
    for cid, c in vocab["canonicals"].items():
        if c.get("namespace") == NS_DATASET:
            continue
        pats = []
        for p in c.get("regex", []):
            try:
                pats.append(re.compile(p))
            except re.error:
                pass
        for r in c.get("regex_curated", []):
            if r.get("compiles"):
                try:
                    pats.append(re.compile(r["pattern"]))
                except re.error:
                    pass
        if not pats:
            continue
        texts = [c["term"]] + [s["text"] for s in c["synonyms"][:50]]
        misses = [t for t in texts if not any(p.search(t) for p in pats)]
        total += len(texts)
        miss_total += len(misses)
        c.setdefault("attrs", {})["selftest"] = {"tested": len(texts),
                                                 "miss": len(misses)}
        for t in misses[:2]:
            gaps.append("%s←%s" % (c["term"], t))
    rate = 100.0 * (total - miss_total) / total if total else 100.0
    return {"tested": total, "miss": miss_total, "rate": round(rate, 2),
            "gaps": gaps[:20]}


# =============================================================================
#  v0300 ── 去重執行計畫(review-only:搬 _to_delete\,絕不刪檔)
# =============================================================================
def emit_dedup_plan(vocab, workdir):
    dups = [e for e in vocab.get("ssot_registry", {}).values()
            if e["status"] == "DUPLICATE"]
    if not dups:
        return 0
    csv_path = os.path.join(workdir, "dedup_plan.csv")
    ps1_path = os.path.join(workdir, "dedup_plan.ps1")
    with open(csv_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("path,dup_of,hash,size,mtime,action\n")
        for e in dups:
            f.write('"%s","%s",%s,%s,%s,MOVE_TO__to_delete\n'
                    % (e["path"], e.get("dup_of", ""), e.get("hash", ""),
                       e.get("size", ""), e.get("mtime", "")))
    lines = [
        "param([switch]$Commit)",
        "# dedup_plan.ps1 — %s %s 產生;LL 慣例:無別名/無 Read-Host/不刪檔" % (ENGINE, VERSION),
        "# 預設 dry-run 只列印;-Commit 才把 DUPLICATE 搬進同層 _to_delete\\(只增不減)",
        "$plan = @(",
    ]
    for e in dups:
        lines.append("  @{ Src = '%s'; DupOf = '%s' }"
                     % (e["path"].replace("'", "''"),
                        e.get("dup_of", "").replace("'", "''")))
    lines += [
        ")",
        "$moved = 0; $skipped = 0",
        "foreach ($item in $plan) {",
        "  $src = $item.Src",
        "  if (-not (Test-Path -LiteralPath $src)) { $skipped++; Write-Output ('SKIP missing: ' + $src); continue }",
        "  $dir = Split-Path -LiteralPath $src -Parent",
        "  $dest = Join-Path $dir '_to_delete'",
        "  if (-not (Test-Path -LiteralPath $dest)) {",
        "    if ($Commit) { New-Item -ItemType Directory -Path $dest | Out-Null }",
        "  }",
        "  $name = Split-Path -LiteralPath $src -Leaf",
        "  $target = Join-Path $dest $name",
        "  $i = 1",
        "  while (Test-Path -LiteralPath $target) { $target = Join-Path $dest ($name + '.' + $i); $i++ }",
        "  if ($Commit) { Move-Item -LiteralPath $src -Destination $target; $moved++; Write-Output ('MOVED: ' + $src + ' -> ' + $target) }",
        "  else { Write-Output ('DRYRUN would move: ' + $src + ' -> ' + $target) }",
        "}",
        "Write-Output ('done. moved=' + $moved + ' skipped=' + $skipped + ' (dry-run 未加 -Commit 時 moved=0)')",
    ]
    with open(ps1_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    return len(dups)


# =============================================================================
#  v0300 ── Command Center 掛載(cge_state.json + vcc_registry add-only)
# =============================================================================
def emit_cc_state(workdir, stats, checks):
    state = {
        "engine": ENGINE, "version": VERSION, "schema": SCHEMA,
        "ts": now_iso(), "stats": stats,
        "gate": {"total": len(checks),
                 "warn": sum(1 for c in checks if c["status"] != "PASS"),
                 "checks": {c["check_id"]: c["status"] for c in checks}},
        "dashboards": ["VIA_CentralGovernance.html"],
        "outputs": ["governance_vocab.json", "governance_ledger.jsonl",
                    "dedup_plan.ps1", "dedup_plan.csv", "cge_state.json"],
    }
    save_json(os.path.join(workdir, "cge_state.json"), state)


def register_cc(cc_path, commit):
    """vcc_registry.json add-only 註冊本引擎;既有條目不動(只增不減)。"""
    reg = load_json(cc_path, None)
    if reg is None:
        return "SKIP(讀不到 %s)" % cc_path
    entries = reg.get("engines") if isinstance(reg, dict) else reg
    if not isinstance(entries, list):
        # 未知結構:不動它(review-only)
        return "SKIP(未知結構,不動)"
    me = os.path.abspath(sys.argv[0])
    for e in entries:
        if isinstance(e, dict) and norm(str(e.get("name", ""))) == norm(ENGINE):
            return "已在籍(不動)"
    entry = {"name": ENGINE, "version": VERSION, "type": "py",
             "path": me, "registered": now_iso(), "status": "OK",
             "registered_by": "%s %s add-only" % (ENGINE, VERSION)}
    if commit:
        entries.append(entry)
        save_json(cc_path, reg)
        return "已 add-only 註冊"
    return "dry-run(--commit 才寫入)"


# =============================================================================
#  v0200 ── 憲法稽核 gate checks
# =============================================================================
def run_gate_checks(vocab):
    checks = []

    def add(cid_, status, count, detail):
        checks.append({"check_id": cid_, "status": status, "count": count,
                       "detail": detail})

    codes = [c["code"] for c in vocab["canonicals"].values()]
    dup = sorted({c for c in codes if codes.count(c) > 1})
    add("CGE_DUP_CODE", "PASS" if not dup else "WARN", len(dup), dup[:10])

    bad_rx = [c["code"] for c in vocab["canonicals"].values()
              if c.get("regex_source", "").startswith("ERROR")]
    bad_cur = [c["code"] for c in vocab["canonicals"].values()
               for r in c.get("regex_curated", []) if not r.get("compiles", True)]
    add("CGE_REGEX_COMPILE", "PASS" if not (bad_rx or bad_cur) else "WARN",
        len(bad_rx) + len(bad_cur), (bad_rx + bad_cur)[:10])

    unc = [c["term"] for c in vocab["canonicals"].values()
           if c.get("namespace") == NS_DATASET and not c["attrs"].get("providers")]
    add("CGE_PROVIDER_CLASSIFIED", "PASS" if not unc else "WARN", len(unc), unc[:10])

    ns_pairs = {}
    for c in vocab["canonicals"].values():
        k = (c.get("namespace", NS_CORE), norm(c["term"]))
        ns_pairs[k] = ns_pairs.get(k, 0) + 1
    coll = [k for k, v in ns_pairs.items() if v > 1]
    add("CGE_NS_UNIQUE_TERM", "PASS" if not coll else "WARN", len(coll),
        [t for _, t in coll][:10])

    empty = [c["term"] for c in vocab["canonicals"].values()
             if not c["synonyms"] and not c.get("regex_curated")
             and c.get("namespace") not in (NS_DATASET, NS_INSTRUMENT)]
    add("CGE_NONEMPTY_VOCAB", "PASS" if not empty else "WARN", len(empty), empty[:10])

    reg = vocab.get("ssot_registry", {})
    dups = [e["path"] for e in reg.values() if e["status"] == "DUPLICATE"]
    add("CGE_SSOT_DEDUP", "PASS" if not dups else "WARN", len(dups),
        [os.path.basename(p) for p in dups[:10]])
    miss = [e["path"] for e in reg.values() if e["status"] == "MISSING"]
    add("CGE_SSOT_PRESENT", "PASS" if not miss else "WARN", len(miss),
        [os.path.basename(p) for p in miss[:10]])

    st = vocab.get("selftest", {})
    add("CGE_REGEX_SELFTEST",
        "PASS" if not st or st.get("miss", 0) == 0 else "WARN",
        st.get("miss", 0), st.get("gaps", [])[:10])

    pk = vocab.get("pack_tests", {}).get("fails", [])
    tamper = [f for f in pk if "TAMPERED" in f or "missing" in f]
    healed = vocab.get("lock_healed", [])
    add("CGE_TW_TICKER_LOCK",
        "PASS" if not (tamper or healed) else "WARN",
        len(tamper) + len(healed),
        (tamper + ["SELF_HEALED:%s" % h for h in healed])[:10])
    add("CGE_TEMPORAL_TESTS", "PASS" if not pk else "WARN", len(pk), pk[:10])

    twreg = vocab.get("tw_stock_registry", {})
    if twreg:
        dl = [c for c, e in twreg.items() if e["status"] == "DELISTED"]
        add("CGE_TWSTOCK_REGISTRY", "PASS",
            sum(1 for e in twreg.values() if e["status"] == "ACTIVE"),
            "ACTIVE=%d DELISTED=%d" % (len(twreg) - len(dl), len(dl)))

    vocab["gate_checks"] = checks
    return checks


def run_pipeline(args):
    root = os.path.abspath(args.workdir)
    vocab_path = args.vocab or os.path.join(root, "governance_vocab.json")
    params_path = args.params or os.path.join(root, "via_cge_params.json")
    ledger_path = args.ledger or os.path.join(root, "governance_ledger.jsonl")
    html_path = args.out_html or os.path.join(root, "VIA_CentralGovernance.html")

    params = dict(DEFAULT_PARAMS)
    params.update(load_json(params_path, {}))
    vocab = load_json(vocab_path, blank_vocab())
    vocab.setdefault("canonicals", {})
    vocab.setdefault("quarantine", [])
    migrate_vocab(vocab)
    run_id = "R%04d" % (vocab["meta"].get("runs", 0) + 1)
    ledger_events = []

    print("=" * 68)
    print(" %s %s  ·  中央治理引擎(同義字/regex SSOT)" % (ENGINE, VERSION))
    print(" mode = %s   run = %s" % ("COMMIT 落地" if args.commit else "DRY-RUN 預覽(不寫)", run_id))
    print("=" * 68)

    # ---- 0) seed (append-only,只補不覆蓋) ----------------------------------
    seed_added = 0
    if not args.no_seed:
        for term, meta in SEED.items():
            cid = ensure_canonical(vocab, term, meta["domain"], ledger_events, run_id)
            for s in meta["syn"]:
                if add_synonym(vocab, cid, s, EV_HUMAN, "seed", run_id, ledger_events):
                    seed_added += 1
        for term, syns in PROVIDER_SEED.items():
            cid = ensure_canonical(vocab, term, "provider", ledger_events, run_id,
                                   ns=NS_PROVIDER)
            for s in syns:
                if add_synonym(vocab, cid, s, EV_HUMAN, "seed:provider",
                               run_id, ledger_events):
                    seed_added += 1
    lk_can, lk_rx = seed_locked_and_temporal(vocab, ledger_events, run_id)
    print(" [0] seed 匯入:canonical=%d,新同義字=%d;鎖死+temporal 詞條 %d(V級regex %d)"
          % (len(vocab["canonicals"]), seed_added, lk_can, lk_rx))

    # ---- 0b) v0200 curated / matrix 匯入 ------------------------------------
    for p in (args.import_curated or []):
        cs = import_curated(p, vocab, ledger_events, run_id)
        print(" [0b] curated 匯入 %s:詞條 %d,V級regex %d,同義字 %d"
              % (os.path.basename(p), cs["canon"], cs["regex"], cs["syn"]))
    for p in (args.import_matrix or []):
        ms = import_matrix(p, vocab, ledger_events, run_id)
        print(" [0c] matrix 匯入 %s:dataset %d(provider已歸類 %d/未歸 %d)"
              "、instrument %d、TW三重衍生 %d"
              % (os.path.basename(p), ms["datasets"], ms["classified"],
                 len(ms["unclassified"]), ms["instruments"], ms["tw_derived"]))
        for u in ms["unclassified"][:6]:
            print("       ? 未歸類:%s" % u)

    # ---- 0d) v0200 SSOT 戶政登記 + 整合去重(review-only) -------------------
    if args.register_ssot or args.ssot_list:
        ss = register_ssot(args.register_ssot, args.ssot_list, vocab,
                           ledger_events, run_id)
        fams = {}
        for e in vocab.get("ssot_registry", {}).values():
            fams.setdefault(e["family"], 0)
        print(" [0d] SSOT 戶政:掃到 %d,新登記 %d,家族 %d;"
              "重複群 %d(重複檔 %d)、MISSING %d — 只標不刪"
              % (ss["scanned"], ss["new"], len(fams), ss["dup_groups"],
                 ss["duplicates"], ss["missing"]))

    # ---- 0f) v0400 台股全市場清單擷取 ---------------------------------------
    tw_stats = None
    if args.fetch_tw or args.tw_source:
        tw_stats = fetch_tw_stocks(vocab, ledger_events, run_id, root,
                                   sources=args.tw_source)
        if tw_stats["err"]:
            print(" [0f] 台股清單:抓取失敗 %s(離線可用 --tw-source 本地 JSON)"
                  % tw_stats["err"][0][:80])
        else:
            print(" [0f] 台股清單:上市 %d + 上櫃 %d,現役 %d;本次新增 %d、下市標記 %d"
                  % (tw_stats["twse"], tw_stats["tpex"], tw_stats["total"],
                     len(tw_stats["added"]), len(tw_stats["delisted"])))
            for a in tw_stats["added"][:5]:
                print("       [+] %s" % a)
            for d in tw_stats["delisted"][:5]:
                print("       [-] %s" % d)

    # ---- 0e) v0300 確認迴路(ACCEPT升V / REJECT名冊 / NEW開戶) --------------
    conf_files = list(args.confirm or [])
    default_conf = os.path.join(root, "confirmations.jsonl")
    if not conf_files and os.path.isfile(default_conf):
        conf_files = [default_conf]
    conf_stats = {"accept": 0, "reject": 0, "new": 0, "bad": 0}
    if conf_files:
        conf_stats = ingest_confirmations(conf_files, vocab, ledger_events, run_id)
        print(" [0e] 確認迴路:ACCEPT升V %d、REJECT %d、NEW %d、無效 %d"
              % (conf_stats["accept"], conf_stats["reject"],
                 conf_stats["new"], conf_stats["bad"]))

    # ---- 1) INGEST live state ----------------------------------------------
    roots = args.corpus or [root]
    own = {os.path.abspath(p) for p in (vocab_path, params_path, ledger_path, html_path)}
    sources = discover_sources(roots, exclude=own)
    freq = {}
    raw_by_norm = {}
    for src in sources:
        for tok in harvest(src):
            tok = tok.strip()
            if not (params["min_token_len"] <= len(tok) <= params["max_token_len"]):
                continue
            if tok.isdigit():          # 純數字不是詞彙
                continue
            nk = norm(tok)
            if not nk:
                continue
            freq[nk] = freq.get(nk, 0) + 1
            raw_by_norm.setdefault(nk, tok.strip())
    print(" [1] 匯入現況:來源 %d 個,唯一 token %d 個" % (len(sources), len(freq)))
    for s in sources[:8]:
        print("       · %s" % os.path.relpath(s, root))

    # ---- 2) EXPAND 自動擴大同義字(確定式變體;dataset 詞條不擴) -----------
    exp_added = 0
    for cid in list(vocab["canonicals"].keys()):
        c = vocab["canonicals"][cid]
        if c.get("namespace") == NS_DATASET:
            continue
        seeds_terms = [c["term"]] + [s["text"] for s in c["synonyms"]]
        gen = set()
        for t in seeds_terms:
            gen |= variants(t)
        for v in gen:
            if add_synonym(vocab, cid, v, EV_AUTO, "auto:variant", run_id, ledger_events):
                exp_added += 1
    print(" [2] 自動擴大:新增變體同義字 %d 個(evidence=M)" % exp_added)

    # ---- 3) MONITOR 未知 token 就近歸戶 ------------------------------------
    lut = build_lookup(vocab)
    rej_norms = {norm(r["text"]) for r in vocab.get("rejected", [])}
    auto_n = ask_n = q_n = known_n = rej_n = 0
    ask_queue = []
    quarantine_new = []
    for nk, f in freq.items():
        if f < params["min_freq"]:
            continue
        if nk in rej_norms:      # 人工已拒絕:不再進 ASK/隔離
            rej_n += 1
            continue
        if nk in lut:
            known_n += 1
            continue
        # 找最近 canonical(監測歸戶只掛 core/finreport,避免污染代碼/來源庫)
        best_cid, best_score = None, 0.0
        for cid, c in vocab["canonicals"].items():
            if c.get("status") == ST_ABSORBED:
                continue
            if c.get("namespace", NS_CORE) not in (NS_CORE, NS_FINREPORT):
                continue
            cands = [norm(c["term"])] + [norm(s["text"]) for s in c["synonyms"]]
            for cand in cands:
                sc = match_score(nk, cand)
                if sc > best_score:
                    best_score, best_cid = sc, cid
        raw = raw_by_norm.get(nk, nk)
        if best_score >= params["auto_attach"] and best_cid:
            add_synonym(vocab, best_cid, raw, EV_AUTO, "auto:monitor(%.2f)" % best_score,
                        run_id, ledger_events)
            auto_n += 1
        elif best_score >= params["ask"] and best_cid:
            ask_n += 1
            ask_queue.append({"token": raw, "freq": f, "nearest": best_cid,
                              "nearest_term": vocab["canonicals"][best_cid]["term"],
                              "score": round(best_score, 3)})
        else:
            q_n += 1
            item = {"token": raw, "freq": f,
                    "nearest": best_cid, "score": round(best_score, 3),
                    "decided_run": run_id, "status": "NOVEL"}
            quarantine_new.append(item)
    # 隔離區 append-only
    existing_q = {norm(x["token"]) for x in vocab["quarantine"]}
    for it in quarantine_new:
        if norm(it["token"]) not in existing_q:
            vocab["quarantine"].append(it)
    print(" [3] 監測歸戶:AUTO=%d  ASK=%d  QUARANTINE=%d  (既知 %d,已拒絕略過 %d)"
          % (auto_n, ask_n, q_n, known_n, rej_n))

    # ---- 4) REGEX 合成(dataset 不合成;curated V 級 regex 並存不覆蓋) ------
    rx_ok = 0
    rx_curated = 0
    rx_eligible = 0
    for cid in vocab["canonicals"]:
        c = vocab["canonicals"][cid]
        rx_curated += len(c.get("regex_curated", []))
        if c.get("namespace") == NS_DATASET:
            continue
        rx_eligible += 1
        synth_regex(vocab, cid, params)
        if c["regex"]:
            rx_ok += 1
    print(" [4] regex 合成:auto %d/%d 可編譯;curated V級 regex %d 條並存"
          % (rx_ok, rx_eligible, rx_curated))

    # ---- 4c) v0300 regex 自測 harness ---------------------------------------
    st = regex_selftest(vocab)
    vocab["selftest"] = st
    print(" [4c] regex 自測:%d 條詞彙回測,命中率 %.2f%%(未命中 %d)"
          % (st["tested"], st["rate"], st["miss"]))

    # ---- 4d) v0400 鎖死/temporal 測試向量 + 防篡改 ---------------------------
    pk = run_pack_tests(vocab)
    vocab["pack_tests"] = {"fails": pk, "ts": now_iso()}
    n_vec = sum(len(d.get("tests_hit", [])) + len(d.get("tests_miss", []))
                for pack in (TW_TICKER_LOCK, TEMPORAL_SEED) for d in pack.values())
    print(" [4d] 鎖死/temporal 測試:%d 向量,%s"
          % (n_vec, "全數通過" if not pk else "FAIL %d:%s" % (len(pk), pk[:3])))
    demo = [(s, normalize_temporal(s)) for s in
            ("24Q1", "1Q2024", "113年第1季", "2024年上半年", "FY24",
             "民國113年8月1日", "1130801")]
    print("       正規化示例:" + " · ".join("%s→%s" % d for d in demo[:4]))

    # ---- 4b) 憲法稽核 gate checks ------------------------------------------
    checks = run_gate_checks(vocab)
    n_warn = sum(1 for ck in checks if ck["status"] != "PASS")
    print(" [4b] gate checks:%d 項,%s"
          % (len(checks), "全 PASS" if n_warn == 0 else "%d 項 WARN" % n_warn))
    for ck in checks:
        if ck["status"] != "PASS":
            print("       WARN %s (%d)" % (ck["check_id"], ck["count"]))

    # ---- 5) 統計 ------------------------------------------------------------
    total_syn = sum(len(c["synonyms"]) for c in vocab["canonicals"].values())
    dormant = sum(1 for c in vocab["canonicals"].values() if c["status"] == ST_DORMANT)
    ns_counts = {}
    for c in vocab["canonicals"].values():
        ns_counts[c.get("namespace", NS_CORE)] = ns_counts.get(c.get("namespace", NS_CORE), 0) + 1
    stats = {
        "run": run_id, "mode": "COMMIT" if args.commit else "DRY-RUN",
        "canonicals": len(vocab["canonicals"]),
        "synonyms": total_syn,
        "new_this_run": seed_added + exp_added + auto_n,
        "ask": ask_n, "quarantine": q_n, "dormant": dormant,
        "regex_cov": rx_ok, "regex_eligible": rx_eligible,
        "regex_curated": rx_curated,
        "gate_warn": n_warn,
        "ns_counts": ns_counts,
        "sources": len(sources), "tokens": len(freq),
        "confirmed": conf_stats["accept"], "rejected_total": len(vocab.get("rejected", [])),
        "selftest_rate": st["rate"], "selftest_miss": st["miss"],
        "pack_test_fails": len(pk),
        "tw_active": sum(1 for e in vocab.get("tw_stock_registry", {}).values()
                         if e["status"] == "ACTIVE") or "—",
        "ts": now_iso(),
    }

    # ---- 5b) v0300 產出:去重計畫 + CC 掛載 ---------------------------------
    n_plan = emit_dedup_plan(vocab, root)
    if n_plan:
        print(" [5b] 去重計畫:dedup_plan.ps1 / .csv(%d 檔;預設 dry-run,-Commit 才搬 _to_delete\\)" % n_plan)
    emit_cc_state(root, stats, checks)
    if args.cc_registry:
        msg = register_cc(args.cc_registry, args.commit)
        print(" [5c] Command Center 註冊:%s" % msg)

    # ---- 6) COMMIT / DRY-RUN ------------------------------------------------
    vocab["meta"]["runs"] = vocab["meta"].get("runs", 0) + 1
    vocab["meta"]["last_run"] = now_iso()
    if args.commit:
        save_json(params_path, params)
        save_json(vocab_path, vocab)
        for ev in ledger_events:
            append_ledger(ledger_path, ev)
        append_ledger(ledger_path, {"ts": now_iso(), "run": run_id, "op": "RUN_COMMIT", "stats": stats})
        print(" [6] COMMIT:已寫入 %s(+ ledger %d 事件)"
              % (os.path.basename(vocab_path), len(ledger_events) + 1))
    else:
        print(" [6] DRY-RUN:未寫入 SSOT(加 --commit 落地);本次會新增 %d 事件"
              % len(ledger_events))

    write_html(html_path, vocab, stats, ask_queue, params)
    print(" [7] 儀表板:%s" % os.path.basename(html_path))
    print("=" * 68)
    print(" 完成。canonical=%d  同義字=%d  regex覆蓋=%d  ASK=%d  隔離=%d"
          % (stats["canonicals"], stats["synonyms"], stats["regex_cov"],
             stats["ask"], stats["quarantine"]))
    return stats


# =============================================================================
#  Visual Lock HTML dashboard
# =============================================================================
def _chip(text, ev):
    color = {EV_HUMAN: C_UP, EV_AUTO: "#7c8aa5", EV_PEND: "#b0883a"}.get(ev, "#7c8aa5")
    return ('<span class="chip" style="border-color:%s;color:%s">%s'
            '<i>%s</i></span>' % (color, color, html.escape(text), ev))


def write_html(path, vocab, stats, ask_queue, params):
    def card(label, val, color):
        return ('<div class="card"><div class="v" style="color:%s">%s</div>'
                '<div class="l">%s</div></div>' % (color, val, label))

    cards = "".join([
        card("Canonical 詞條", stats["canonicals"], "#e6edf6"),
        card("同義字總數", stats["synonyms"], "#e6edf6"),
        card("本次新增", stats["new_this_run"], C_UP),
        card("待確認 ASK", stats["ask"], "#d9b25a"),
        card("隔離 QUARANTINE", stats["quarantine"], C_UP),
        card("auto regex", "%d/%d" % (stats["regex_cov"],
                                      stats.get("regex_eligible", stats["canonicals"])), C_DN),
        card("curated V regex", stats.get("regex_curated", 0), C_DN),
        card("確認升V(本次)", stats.get("confirmed", 0), C_DN),
        card("自測命中率", "%.1f%%" % stats.get("selftest_rate", 100.0),
             C_DN if stats.get("selftest_miss", 0) == 0 else "#d9b25a"),
        card("gate WARN", stats.get("gate_warn", 0),
             C_DN if not stats.get("gate_warn") else C_UP),
        card("台股在籍(現役)", stats.get("tw_active", "—"), "#e6edf6"),
    ])
    ns_line = " · ".join("%s %d" % (k, v)
                         for k, v in sorted(stats.get("ns_counts", {}).items()))

    gate_rows = "".join(
        '<tr><td class="rx">%s</td>'
        '<td><span style="color:%s;font-weight:700">%s</span></td>'
        '<td class="num">%d</td><td class="rx">%s</td></tr>'
        % (html.escape(ck["check_id"]),
           C_DN if ck["status"] == "PASS" else "#d9b25a", ck["status"],
           ck["count"], html.escape(json.dumps(ck["detail"], ensure_ascii=False)[:160]))
        for ck in vocab.get("gate_checks", [])) or \
        '<tr><td colspan="4" class="muted">—</td></tr>'

    # canonical 表(依 namespace 分組)
    rows = []
    for cid, c in sorted(vocab["canonicals"].items(),
                         key=lambda kv: (kv[1].get("namespace", NS_CORE),
                                         kv[1]["domain"], kv[1]["term"])):
        chips = "".join(_chip(s["text"], s["evidence"]) for s in c["synonyms"][:24])
        more = "" if len(c["synonyms"]) <= 24 else '<span class="more">+%d…</span>' % (len(c["synonyms"]) - 24)
        n_cur = len(c.get("regex_curated", []))
        if c.get("regex"):
            rx = html.escape(c["regex"][0][:180])
        elif n_cur:
            rx = '<span style="color:%s">curated×%d</span>' % (C_DN, n_cur)
        else:
            rx = '<span class="muted">—</span>'
        if c.get("regex") and n_cur:
            rx += ' <span style="color:%s">+curated×%d</span>' % (C_DN, n_cur)
        tier = c.get("attrs", {}).get("tier") or c.get("attrs", {}).get("validation_level") or ""
        st_color = {ST_ACTIVE: C_DN, ST_DORMANT: "#7c8aa5", ST_ABSORBED: "#555"}.get(c["status"], "#999")
        rows.append(
            '<tr><td><b>%s</b><div class="code">%s</div></td>'
            '<td><span class="dom">%s</span>%s</td>'
            '<td><span style="color:%s">%s</span></td>'
            '<td class="syn">%s%s</td>'
            '<td class="rx">%s</td></tr>'
            % (html.escape(c["term"]), c["code"],
               html.escape(c.get("namespace", NS_CORE)),
               ('<div class="code">%s</div>' % html.escape(tier)) if tier else "",
               st_color, c["status"], chips, more, rx))
    table = "".join(rows)

    # 台股代號登記簿(前 30 列 + 摘要;完整清單在 tw_stock_tickers_latest.csv)
    twreg = vocab.get("tw_stock_registry", {})
    tw_rows = []
    for code in sorted(twreg)[:30]:
        e = twreg[code]
        col = C_DN if e["status"] == "ACTIVE" else "#7c8aa5"
        tw_rows.append(
            '<tr><td><b>%s</b></td><td class="code">%s</td><td class="code">%s</td>'
            '<td><span class="dom">%s</span></td><td>%s</td>'
            '<td><span style="color:%s">%s</span></td></tr>'
            % (e["TICKER"], e["YFINANCE"], e["BLOOMBERG"], e["MARKET"],
               html.escape(e.get("NAME", "")), col, e["status"]))
    if len(twreg) > 30:
        tw_rows.append('<tr><td colspan="6" class="muted">…共 %d 檔,完整清單見 tw_stock_tickers_latest.csv</td></tr>' % len(twreg))
    tw_table = "".join(tw_rows) or \
        '<tr><td colspan="6" class="muted">尚未擷取(--fetch-tw 需網路;離線用 --tw-source)</td></tr>'

    # SSOT 戶政 / 去重計畫表
    reg = vocab.get("ssot_registry", {})
    ssot_rows = []
    for e in sorted(reg.values(), key=lambda x: (x["family"], x.get("mtime") or "")):
        col = {"ACTIVE": C_DN, "DUPLICATE": "#d9b25a", "MISSING": C_UP,
               "UNREADABLE": C_UP}.get(e["status"], "#999")
        extra = ""
        if e["status"] == "DUPLICATE":
            extra = '<div class="code">dup of %s</div>' % html.escape(
                os.path.basename(e.get("dup_of", "")))
        ssot_rows.append(
            '<tr><td class="rx">%s%s</td><td><span class="dom">%s</span></td>'
            '<td><span style="color:%s;font-weight:700">%s</span></td>'
            '<td class="code">%s</td><td class="num">%s</td><td class="code">%s</td></tr>'
            % (html.escape(os.path.basename(e["path"])),
               '<div class="code">%s</div>' % html.escape(e["path"]),
               html.escape(e["family"][:40]), col, e["status"],
               e.get("hash", ""), e.get("size", ""), e.get("mtime", "")))
    ssot_table = "".join(ssot_rows) or \
        '<tr><td colspan="6" class="muted">本次未執行 SSOT 戶政(--register-ssot / --ssot-list)</td></tr>'

    # ASK 佇列(v0300 mouse-only:預選最佳歸戶、單列一鍵、全收、token 生成)
    aq = sorted(ask_queue, key=lambda x: -x["score"])[:60]
    ask_rows = "".join(
        '<tr data-token="%s" data-canon="%s" data-state="accept">'
        '<td>%s</td><td class="num">%d</td>'
        '<td>→ <b>%s</b></td><td class="num">%.2f</td>'
        '<td class="act">'
        '<button class="btn a on" onclick="setSt(this,\'accept\')">接受</button>'
        '<button class="btn r" onclick="setSt(this,\'reject\')">拒絕</button>'
        '<button class="btn s" onclick="setSt(this,\'skip\')">略過</button>'
        '</td></tr>'
        % (html.escape(a["token"], quote=True), html.escape(a["nearest_term"], quote=True),
           html.escape(a["token"]), a["freq"], html.escape(a["nearest_term"]), a["score"])
        for a in aq) or '<tr><td colspan="5" class="muted">本次無待確認候選</td></tr>'

    doc = """<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA 中央治理 · 同義字/regex SSOT</title>
<style>
*{box-sizing:border-box}
body{margin:0;background:#0b0f17;color:#e6edf6;font:14px/1.5 -apple-system,"Segoe UI","PingFang TC","Microsoft JhengHei",sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:26px 20px 60px}
.hdr{border:1px solid #1c2740;border-radius:14px;padding:18px 22px;margin-bottom:20px;
 background:linear-gradient(135deg,#0f1626,#0b0f17)}
.hdr h1{margin:0;font-size:18px;letter-spacing:.5px}
.hdr .sub{color:#8fa0bd;font-size:12px;margin-top:6px}
.hdr .tag{display:inline-block;margin-top:10px;padding:3px 10px;border:1px solid #294;border-radius:20px;
 color:#5a9e6f;font-size:11px}
.hdr .mode{margin-left:8px;padding:3px 10px;border-radius:20px;font-size:11px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(128px,1fr));gap:12px;margin-bottom:22px}
.card{background:#0f1626;border:1px solid #1c2740;border-radius:12px;padding:14px}
.card .v{font-size:24px;font-weight:700}
.card .l{color:#8fa0bd;font-size:12px;margin-top:2px}
h2{font-size:14px;color:#b7c6e0;border-left:3px solid %(up)s;padding-left:9px;margin:26px 0 12px}
table{width:100%%;border-collapse:collapse;background:#0f1626;border:1px solid #1c2740;border-radius:12px;overflow:hidden}
th,td{text-align:left;padding:10px 12px;border-bottom:1px solid #16203a;vertical-align:top;font-size:13px}
th{background:#111a2e;color:#8fa0bd;font-weight:600;position:sticky;top:0}
tr:last-child td{border-bottom:none}
.code{color:#5c6f8f;font-size:10px;font-family:ui-monospace,Consolas,monospace;margin-top:3px}
.dom{background:#16203a;color:#9db4dc;padding:2px 8px;border-radius:6px;font-size:11px}
.syn .chip{display:inline-block;margin:2px 4px 2px 0;padding:2px 8px;border:1px solid #444;
 border-radius:14px;font-size:11px;white-space:nowrap}
.syn .chip i{opacity:.6;font-style:normal;margin-left:4px;font-size:9px}
.more{color:#7c8aa5;font-size:11px}
.rx{font-family:ui-monospace,Consolas,monospace;font-size:11px;color:#89c0b8;max-width:300px;word-break:break-all}
.num{text-align:right;font-variant-numeric:tabular-nums}
.muted{color:#5c6f8f}
.foot{color:#5c6f8f;font-size:11px;margin-top:24px;text-align:center}
.btn{background:#0f1626;border:1px solid #3a4a66;color:#b7c6e0;border-radius:8px;
 padding:3px 10px;margin-right:4px;cursor:pointer;font-size:11px}
.btn.big{padding:7px 16px;font-size:13px}
.btn.a.on{border-color:%(dn)s;color:%(dn)s;font-weight:700}
.btn.r.on{border-color:%(up)s;color:%(up)s;font-weight:700}
.btn.s.on{border-color:#7c8aa5;color:#7c8aa5;font-weight:700}
.act{white-space:nowrap}
.legend{color:#8fa0bd;font-size:11px;margin:6px 0 0}
.legend b{color:%(up)s}
</style></head><body><div class="wrap">
<div class="hdr">
 <h1>VIA 中央治理引擎 · 同義字 / regex SSOT</h1>
 <div class="sub">Central Governance Engine — 自動擴大 · 自動監測 · 只增不減(append-only)· dry-run 預設 · evidence honesty</div>
 <span class="tag">%(schema)s</span>
 <span class="mode" style="background:%(modebg)s;color:#fff">%(mode)s · %(run)s</span>
 <div class="legend">evidence:&nbsp; <b>V</b>=人工確認&nbsp; <span style="color:#7c8aa5">M</span>=自動衍生(封頂)&nbsp; <span style="color:#b0883a">P</span>=待決</div>
</div>
<div class="grid">%(cards)s</div>
<h2>憲法稽核 Gate Checks</h2>
<table><thead><tr><th>check_id</th><th>status</th><th>count</th><th>detail</th></tr></thead>
<tbody>%(gates)s</tbody></table>
<h2>Canonical 詞條 · 同義字 · regex(auto + curated 並存)</h2>
<div class="legend">namespaces:%(ns_line)s</div>
<table><thead><tr><th>Canonical</th><th>Namespace / Tier</th><th>狀態</th><th>同義字(chips)</th><th>regex</th></tr></thead>
<tbody>%(table)s</tbody></table>
<h2>台股代號登記簿(三種代號鎖死定義:^[1-9]\d{3}$ · .TW/.TWO · 「#### TT」;DELISTED 只標不刪)</h2>
<table><thead><tr><th>TICKER</th><th>YFinance</th><th>Bloomberg</th><th>市場</th><th>名稱</th><th>狀態</th></tr></thead>
<tbody>%(twstock)s</tbody></table>
<h2>SSOT 戶政登記 · 整合去重(review-only:DUPLICATE 只標記,不刪檔)</h2>
<table><thead><tr><th>檔案 / 路徑</th><th>家族</th><th>狀態</th><th>content hash</th><th>bytes</th><th>mtime</th></tr></thead>
<tbody>%(ssot)s</tbody></table>
<h2>ASK 待確認佇列(mouse-only:預設全接受,點一下改判;完成後複製貼回 confirmations.jsonl,下次跑 --confirm 即升 V)</h2>
<div style="margin:0 0 10px">
 <button class="btn a big" onclick="acceptAll()">一鍵全收(接受全部建議)</button>
 <button class="btn s big" onclick="copyOut()">複製 confirmations 內容</button>
 <span id="copymsg" class="legend"></span>
</div>
<table><thead><tr><th>新 token</th><th>頻次</th><th>建議歸戶</th><th>相似度</th><th>判定</th></tr></thead>
<tbody id="askbody">%(ask)s</tbody></table>
<textarea id="out" readonly style="width:100%%;height:120px;margin-top:10px;background:#0f1626;
 color:#89c0b8;border:1px solid #1c2740;border-radius:10px;padding:10px;
 font:11px ui-monospace,Consolas,monospace"></textarea>
<script>
function rowsOf(){return Array.prototype.slice.call(document.querySelectorAll('#askbody tr[data-token]'));}
function setSt(btn,st){var tr=btn.closest('tr');tr.setAttribute('data-state',st);
 tr.querySelectorAll('.btn').forEach(function(b){b.classList.remove('on');});btn.classList.add('on');refresh();}
function acceptAll(){rowsOf().forEach(function(tr){tr.setAttribute('data-state','accept');
 tr.querySelectorAll('.btn').forEach(function(b){b.classList.remove('on');});
 tr.querySelector('.btn.a').classList.add('on');});refresh();}
function refresh(){var out=[];rowsOf().forEach(function(tr){var st=tr.getAttribute('data-state');
 if(st==='skip')return;var o={text:tr.getAttribute('data-token'),decision:st.toUpperCase()};
 if(st==='accept')o.canonical=tr.getAttribute('data-canon');out.push(JSON.stringify(o));});
 document.getElementById('out').value=out.join('\n');}
function copyOut(){var t=document.getElementById('out');t.select();
 try{document.execCommand('copy');document.getElementById('copymsg').textContent='已複製 '+t.value.split('\n').filter(Boolean).length+' 行';}
 catch(e){document.getElementById('copymsg').textContent='請手動全選複製';}}
refresh();
</script>
<div class="foot">%(engine)s %(version)s · %(ts)s · 只增不減:同義字永不刪除,退場者轉 DORMANT · regex 均已通過 re.compile 驗證</div>
</div></body></html>""" % {
        "up": C_UP,
        "dn": C_DN,
        "schema": SCHEMA,
        "mode": stats["mode"],
        "modebg": C_UP if stats["mode"] == "COMMIT" else "#3a4a66",
        "run": stats["run"],
        "cards": cards, "table": table, "ask": ask_rows,
        "gates": gate_rows, "ns_line": html.escape(ns_line),
        "ssot": ssot_table, "twstock": tw_table,
        "engine": ENGINE, "version": VERSION, "ts": stats["ts"],
    }
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(doc)


# =============================================================================
#  CLI
# =============================================================================
def main(argv=None):
    ap = argparse.ArgumentParser(
        prog=ENGINE,
        description="VIA 中央治理引擎:自動擴大/監測同義字 + regex SSOT(只增不減,一貼即跑)")
    ap.add_argument("--workdir", default=".", help="工作根目錄(預設當前)")
    ap.add_argument("--corpus", nargs="*", default=None,
                    help="語料來源(檔或資料夾;預設自動掃 workdir)")
    ap.add_argument("--vocab", default=None, help="governance_vocab.json 路徑")
    ap.add_argument("--params", default=None, help="via_cge_params.json 路徑")
    ap.add_argument("--ledger", default=None, help="governance_ledger.jsonl 路徑")
    ap.add_argument("--out-html", default=None, help="HTML 儀表板輸出路徑")
    ap.add_argument("--commit", action="store_true", help="落地寫入 SSOT(預設 dry-run)")
    ap.add_argument("--no-seed", action="store_true", help="不匯入內建種子字典")
    ap.add_argument("--import-curated", nargs="*", default=None, metavar="PY",
                    help="AST 解析 PatternDef 模式庫(.py),人工 regex 以 V 級入庫")
    ap.add_argument("--import-matrix", nargs="*", default=None, metavar="CSV",
                    help="匯入 VIA Extraction Matrix CSV(dataset/instrument/provider)")
    ap.add_argument("--register-ssot", nargs="*", default=None, metavar="ROOT",
                    help="遞迴掃描根目錄,登記所有 *ssot* 檔並 content-hash 去重(review-only)")
    ap.add_argument("--ssot-list", nargs="*", default=None, metavar="TXT",
                    help="SSOT 路徑清單檔(每行一條,可含引號),與 --register-ssot 併用")
    ap.add_argument("--confirm", nargs="*", default=None, metavar="JSONL",
                    help="確認檔(confirmations.jsonl;預設自動吃 workdir 下同名檔)")
    ap.add_argument("--cc-registry", default=None, metavar="JSON",
                    help="vcc_registry.json 路徑:add-only 註冊本引擎(--commit 才寫)")
    ap.add_argument("--fetch-tw", action="store_true",
                    help="抓 TWSE+TPEX OpenAPI 全市場普通股清單,diff+CSV(需網路)")
    ap.add_argument("--tw-source", nargs="*", default=None, metavar="JSON",
                    help="離線台股清單來源(本地 JSON:第1個=上市,第2個=上櫃)")
    args = ap.parse_args(argv)
    try:
        run_pipeline(args)
        return 0
    except Exception as e:
        print("FATAL: %s" % e)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
