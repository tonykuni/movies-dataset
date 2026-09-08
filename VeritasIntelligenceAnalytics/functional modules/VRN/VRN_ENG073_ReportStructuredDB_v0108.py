#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VRN_ENG073_ReportStructuredDB v0105 — 報告結構化入庫引擎(批237 立;批244 庫解析)
====================================================================
操作員令:「個股名稱用四碼台股 TICKER 去 TWSE/TPEX 擷取;NLP 工具
引擎協助文字處理;VRN BASIC INFO & SUMMARY & FINANCIAL DATA 都可
抓出交互驗證整理成資料庫;收官所有」。
機制(規格書 b236 契約:決定性擷取為主;NLP 只協助不創造):
  輸入=ENG072 v0101 分區 sidecar(first_page_text/*.json)+檔名
  ①Basic Info:ticker(檔名四碼 rx)→官方名=tw_listings 名冊
    (TWSE+TPEX 1,979 檔在庫=零網路正主);券商字典;日期多格式
    (西元 8 碼/民國 1141202/6 碼);評等/目標價/現價 rx(右資訊區優先)
  ②交互驗證:Upside_calc=TP/Price-1 對報告明示值→EXACT/
    ROUNDING_ONLY/FORMULA_MISMATCH/MISSING_SOURCE;檔名 ticker↔
    區文 ticker;官方名↔區文名——衝突=KEEP_BOTH 列示不覆寫(雙 SSOT)
  ③Summary:標題帶+本文(修復)前二句=決定性摘要頭(證據連回 sidecar)
  ④Financial:EPS/目標價/殖利率/總報酬 rx;期間 24E→2024·ESTIMATE
    (三層隔離:REPORT_ESTIMATE 永不冒充 OFFICIAL_ACTUAL)
  ⑤NLP 掛載:收容件 via_nlp_engine.TextProcessor(NFKC 正規化)
    graceful 缺席零影響。批243 修債:v0103 建構漏 lexicon_path=
    永遠 fallback;v0104 帶 ssot_lexicon 正掛+快取單例
落庫:vrn_report_basic+vrn_report_metrics(anti-join 只增不減;
每列帶 raw 證據片段)。
批238 真件四修(工作站 59 件實錄揭露):
  ①美系格式:TP_RX +「Price Target/PT」;PX_RX 否定前瞻拒「Price
    Target」誤入現價(MS/GS 誤植修)
  ②ticker 驗證:檔名四碼候選逐一對官方名冊,不在冊=試下一候選;
    全不在=空(研討會/晨報誠實非個股,杜絕 2026 誤當代號)
  ③荒謬升幅防呆:|升幅|>150% 或 TP/P 比例失真=PARSE_SUSPECT
    誠實隔離(杜絕 凱基 P=19→1831% 笑話;值保留供查)
  ④run=派生層重算(同 report_file DELETE+INSERT=ENG063 同例;
    v0100 首寫鎖=修正永不生效之債)
批239 配對收斂(第二輪 59 件實錄:MS P 抓小雜數/JP TP=25/Daiwa
TP=2=標籤誤中他數):TP/P 改「候選集+合理性配對」——右區優先收集
全部候選(>0),取比例落 [0.30,3.2] 之首對;無合理對=僅留可信單值,
不可信者=None 誠實(寧缺勿假;PARSE_SUSPECT 網保留為最後防線)。
批240 裁示落實(操作員:「報告上漲空間=目標價÷報告前一日 CLOSE,
非 ADJ CLOSE」):資料庫補值/驗證道——
  price_db=tw_daily_prices 報告日前一交易日 close(原始 close 正主;
  雲端實證:JP 台積電 2025-07-18 前日 close=1130=頁面 P 全吻合)
  ①頁 P 缺→P_FROM_DB 補值(升幅得算)②頁 P 在→對質:差<1%=
  P_CONFIRMED_DB;差大=P_DB_CONFLICT(KEEP_BOTH;升幅以庫值軌另計)
  新欄 price_db/upside_db/price_state(ALTER 容錯補欄)。
用法:python3 VRN_ENG073_ReportStructuredDB_v0105.py run [--open]
      | --status | --selftest
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


def _resolve_db(db: Path | None) -> Path | None:
    """批244:庫路徑誠實解析(工作站雙 clone 債——mega 庫可能在
    Downloads\movies-dataset 替根)。顯式 db=信任直用(selftest 建新
    庫);預設=主路徑→替根探測;全缺=None 誠實停 rc2 不 traceback。"""
    if db is not None:
        return Path(db)
    cands = [DB_TW]
    try:
        home = Path.home()
        rel = Path("movies-dataset/VeritasIntelligenceAnalytics/functional modules/VDF/output_hub/mega/vdf_tw_market.duckdb")
        cands += [home / "Downloads" / rel, home / rel]
    except Exception:
        pass
    for c in cands:
        if c and Path(c).exists():
            if Path(c) != DB_TW:
                print(f"[庫解析] 主路徑缺→改用替根庫:{c}(誠實提示)")
            return Path(c)
    print(f"[庫缺] {DB_TW} 不在且替根未尋獲=誠實停(rc2)。"
          "先跑 VDF_ENG065_DbImport 三包匯入,或確認 clone 根。")
    return None


import json
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
ZONES_DIR = VIA / "VIA_Reports" / "first_page_text"
DB_TW = VIA / "functional modules" / "VDF" / "output_hub" / "mega" / "vdf_tw_market.duckdb"

BROKER_DICT = {"MS": "摩根士丹利", "GS": "高盛", "JP": "摩根大通",
               "Citi": "花旗", "UBS": "瑞銀", "Daiwa": "大和",
               "CLST": "里昂", "MQ": "麥格理", "GF": "廣發",
               "凱基": "凱基投顧", "兆豐": "兆豐", "華南": "華南投顧",
               "統一": "統一投顧", "台新": "台新", "國泰": "國泰證期",
               "CTBC": "中國信託"}
RATING_RX = re.compile(
    r"\b(Buy|Sell|Hold|Neutral|Overweight|Underweight|Outperform|"
    r"Underperform)\b|買進|賣出|中立|增持|減持|優於大盤|強力買進", re.I)
TP_RX = re.compile(r"(?:Target\s*price|Price\s*Target|目標價|\bPT\b)"
                   r"[^\d]{0,20}(?:NT\$|新台幣)?\s*"
                   r"([\d,]+(?:\.\d+)?)", re.I)
PX_RX = re.compile(r"(?<![Tt]arget )(?<![Tt]arget\n)(?<![Tt]ARGET )(?:\b[Pp]rice\b(?![ \t]*"
                   r"[Tt]arget)|現價|收盤價)\s*(?:\([^)]*\))?[^\d]{0,20}"
                   r"(?:NT\$)?\s*([\d,]+(?:\.\d+)?)", re.M)
UPS_RX = re.compile(r"(?:Expected\s*total\s*return|上漲空間|Upside|漲跌空間)"
                    r"[^\d\-]{0,15}(-?[\d.]+)\s*%", re.I)
YLD_RX = re.compile(r"(?:dividend\s*yield|殖利率)[^\d]{0,15}([\d.]+)\s*%", re.I)
EPS_RX = re.compile(r"(20\d{2}|1[01]\d)\s*[EFA]?\s*(?:年)?\s*"
                    r"(?:Diluted\s+)?EPS[^\d\-]{0,15}(-?[\d,]+(?:\.\d+)?)", re.I)
TICK_RX = re.compile(r"(?<!\d)(\d{4})(?!\d)")


_TP_CACHE: list = []          # 批243:單例快取(避免逐呼重讀 lexicon)


def _nfkc(s: str) -> str:
    """NLP 掛載:收容件 TextProcessor graceful;缺席=stdlib NFKC。
    批243 修債:v0103 漏 lexicon_path=建構必拋=永遠 fallback;
    v0104 帶 ssot_lexicon 正掛(收容件原地不動)。"""
    if not _TP_CACHE:
        try:
            pkg = HERE / "references" / "intake" / "VIA_NLP_OneEngine_v1.1.0"
            sys.path.insert(0, str(pkg / "src"))
            from via_nlp_engine.text_ops import TextProcessor  # noqa
            lex = pkg / "data" / "lexicon" / "ssot_lexicon.json"
            _TP_CACHE.append(TextProcessor(lex) if lex.exists() else None)
        except Exception:
            _TP_CACHE.append(None)
    tp = _TP_CACHE[0]
    if tp is not None:
        try:
            return tp.normalize(s)
        except Exception:
            pass
    return unicodedata.normalize("NFKC", s)


def _num(s: str) -> float | None:
    try:
        return float(s.replace(",", ""))
    except Exception:
        return None


def parse_date(name: str) -> str:
    m = re.search(r"(20\d{2})[-_]?(\d{2})[-_]?(\d{2})", name)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    m = re.search(r"(?<!\d)(1[01]\d)(\d{2})(\d{2})(?!\d)", name)  # 民國 1141202
    if m:
        return f"{int(m.group(1)) + 1911}-{m.group(2)}-{m.group(3)}"
    m = re.search(r"(?<!\d)(2[3-9])(\d{2})(\d{2})(?!\d)", name)   # 251208
    if m:
        return f"20{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return ""


def parse_broker(name: str) -> str:
    for k in BROKER_DICT:
        if k in name:
            return k
    return ""


# ===== 批418:報告型別分類 + 年份守衛 =====================================
# 操作員給了 63 份真報告當 INPUT FOR TEST。逐檔名跑過既有擷取器後看到兩件事:
#   ① 「第三場 AI潮流下展望2026半導體產業趨勢」被抽出代號 2026——那是**年份**,
#      但 2026 恰好也是真實上市代號(聚亨),所以連「逐驗官方名冊」都擋不住。
#      把產業展望簡報歸到聚亨名下,比沒有代號更糟(假資料比缺資料難查)。
#   ② 63 份裡有 19 份**本來就不是個股報告**:產業報告(Thermal Solutions/ABF/
#      Memory/PCB/CCL/Automation/鋼鐵產業)、大盤晨報(盤勢分析/投資早報/晨會報告/
#      日美港股分析/期貨晨間解盤)、研討會(第一~三場)。它們沒有代號是**正確**的,
#      但收尾閘看到「無代號」會當成失敗,操作員就會看到一整面假紅。
# 所以本批做兩件事:年份不得當代號、報告型別要分得出來。

YEAR_TAIL_RX = re.compile(r"^\s*(?:年|年度|年報|上半年?|下半年?|[Hh][12]|[Qq][1-4]|全年)")
OUTLOOK_WORDS = ("展望", "趨勢", "前瞻", "回顧", "年度", "大趨勢", "投資策略", "策略會", "論壇", "研討")
TICKER_MARKS = ("(", "（", ")", "）", "TT", "tt", "代號", "股號")

# 報告型別:先判最「窄」的,再往外退。每型的關鍵詞都取自操作員這 63 份真檔名,
# 不是憑空想的;新型別出現時照樣會落到「其他」而不是被硬塞進個股。
KIND_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("研討會", ("第一場", "第二場", "第三場", "第四場", "研討會", "論壇", "說明會", "法說會")),
    ("大盤晨報", ("盤勢", "投資早報", "早報", "晨會", "晨間", "解盤", "收盤", "盤後", "盤前",
                  "日報", "週報", "月報", "市場評論", "新聞與重要訊息")),
    ("海外", ("日股", "美股", "港股", "陸股", "海外", "Asia", "asia", "US ", "Japan", "China",
              "Global", "global")),
    ("產業", ("產業", "類股", "Thermal", "thermal", "ABF", "abf", "Memory", "memory", "PCB", "pcb",
              "CCL", "ccl", "Automation", "automation", "Solutions", "Insights", "Hardware",
              "TPU", "GPU", "AI ", "半導體", "供應鏈", "鋼鐵", "面板", "航運")),
]


def _is_year_like(stem: str, m: "re.Match[str]", date_spans: list[tuple[int, int]]) -> str:
    """4 碼候選讀起來是年份就不准當代號;回傳否決理由(空字串=不是年份)。
    三道,由結構到語意,愈前面愈硬:
      ① 落在本檔名的日期字串裡 → 那本來就是日期的一部分(結構事實,永遠對)
      ② 後面緊接 年/年度/H1/Q3… → 語言事實,永遠對
      ③ 值在 1990–2099、檔名帶展望/趨勢/年度這類詞、且候選旁沒有代號記號
         (括號/TT/代號) → 這是判斷不是事實,所以條件收得緊;
         擋錯的代價是「誠實無代號」,擋不住的代價是「假代號入正本庫」,不對稱。"""
    a, b = m.span(1)
    for x, y in date_spans:
        if a >= x and b <= y:
            return "落在日期字串內"
    if YEAR_TAIL_RX.match(stem[b:b + 4]):
        return f"後接年份詞「{stem[b:b + 2].strip()}」"
    try:
        v = int(m.group(1))
    except ValueError:
        return ""
    if 1990 <= v <= 2099 and any(w in stem for w in OUTLOOK_WORDS):
        near = stem[max(0, a - 2):a] + stem[b:b + 2]
        if not any(t in near for t in TICKER_MARKS):
            return "年份值+展望/趨勢類標題+旁無代號記號"
    return ""


def _date_spans(name: str) -> list[tuple[int, int]]:
    """parse_date 認得的三種日期寫法在檔名裡的位置(給年份守衛第①道用)。"""
    out = []
    for rx in (r"(20\d{2})[-_]?(\d{2})[-_]?(\d{2})",
               r"(?<!\d)(1[01]\d)(\d{2})(\d{2})(?!\d)",
               r"(?<!\d)(2[3-9])(\d{2})(\d{2})(?!\d)"):
        for m in re.finditer(rx, name):
            out.append(m.span())
    return out


def classify_kind(stem: str, ticker: str) -> tuple[str, str]:
    """報告型別 + 判準理由。有代號一律先算個股(代號是最硬的證據);
    沒有代號才按關鍵詞分,全不中=「其他」誠實留白,不硬塞。"""
    if ticker:
        return "個股", f"檔名帶可驗證代號 {ticker}"
    for kind, words in KIND_RULES:
        for w in words:
            if w in stem:
                return kind, f"檔名含「{w.strip()}」"
    return "其他", "無代號且無型別關鍵詞=誠實留白(不硬塞個股)"


def kind_expects_ticker(kind: str) -> bool:
    """只有個股型才「應該」有代號。其餘型別沒有代號是對的,不是失敗——
    收尾閘拿這支判,免得 19 份產業/晨報/研討會報告被當成一整面紅。"""
    return kind == "個股"


def extract_one(stem: str, zones: dict, names: dict) -> tuple[dict, list]:
    """回 (basic row, metrics rows);全決定性;衝突=KEEP_BOTH 列示"""
    text_all = _nfkc("\n".join(str(zones.get(k, ""))
                               for k in ("header", "right", "body")))
    right = _nfkc(str(zones.get("right", "")))
    # 批239b(操作員令「文字修復後可抓目標價」):斷行修復版=標籤與
    # 數值被換行切開(Target↵price↵NT$165)之救回文本;raw 優先、修復版後備
    right_rep = re.sub(r"\s*\n\s*", " ", right)
    text_rep = re.sub(r"\s*\n\s*", " ", text_all)
    # 批238②:候選逐驗官方名冊;全不在=誠實空(研討會/晨報非個股)
    ticker = ""
    yr_rejects = []
    dspans = _date_spans(stem)            # 批418:年份守衛用
    for cand in TICK_RX.finditer(stem):
        why = _is_year_like(stem, cand, dspans)
        if why:
            yr_rejects.append(f"{cand.group(1)}({why})")
            continue
        if names.get(cand.group(1)):
            ticker = cand.group(1)
            break
    if not ticker and not names:          # 名冊缺(測試環境)=首候選(仍過年份守衛)
        for m0 in TICK_RX.finditer(stem):
            if not _is_year_like(stem, m0, dspans):
                ticker = m0.group(1)
                break
    if yr_rejects:
        conflicts_year = "YEAR_NOT_TICKER=" + ";".join(yr_rejects)
    else:
        conflicts_year = ""
    name_official = names.get(ticker, "")
    tick_z = TICK_RX.search(text_all)
    conflicts = []
    if conflicts_year:
        conflicts.append(conflicts_year)
    if ticker and tick_z and tick_z.group(1) != ticker \
            and names.get(tick_z.group(1)):
        conflicts.append(f"TICKER_ZONE={tick_z.group(1)}(KEEP_BOTH)")
    if name_official and name_official not in text_all:
        conflicts.append("NAME_NOT_IN_PAGE(KEEP_BOTH)")
    rat = RATING_RX.search(right) or RATING_RX.search(text_all)
    tp = (TP_RX.search(right) or TP_RX.search(right_rep)
          or TP_RX.search(text_all) or TP_RX.search(text_rep))
    ups = (UPS_RX.search(right) or UPS_RX.search(right_rep)
           or UPS_RX.search(text_all) or UPS_RX.search(text_rep))
    # 批239:候選集+合理性配對(右區優先;比例 [0.30,3.2] 取首對;
    # 無合理對=僅留可信單值,不可信=None 寧缺勿假)
    def _cands(rx, *texts):
        out = []
        for t in texts:
            for m in rx.finditer(t):
                v = _num(m.group(1))
                if v and v > 0 and v not in out:
                    out.append(v)
        return out
    tp_c = _cands(TP_RX, right, right_rep, text_all, text_rep)
    px_c = _cands(PX_RX, right, right_rep, text_all, text_rep)
    tpv = pxv = None
    for a in tp_c:
        for b in px_c:
            if 0.30 <= a / b <= 3.2:
                tpv, pxv = a, b
                break
        if tpv:
            break
    if tpv is None and pxv is None:
        # 無合理對:僅單側有候選=取之;雙側衝突=取值大者(小值=標籤
        # 誤中日期/點數碎片之經驗律:MS 1130vs2/JP 25vs1130/Daiwa 2vs2470)
        cand = [(tp_c[0], "tp")] if tp_c else []
        cand += [(px_c[0], "px")] if px_c else []
        if cand:
            v, side = max(cand)
            if side == "tp":
                tpv = v
            else:
                pxv = v
    upr = _num(ups.group(1)) if ups else None
    upc = round((tpv / pxv - 1) * 100, 1) if tpv and pxv else None
    if upc is not None and (abs(upc) > 150 or (tpv and pxv
            and (tpv / pxv > 8 or tpv / pxv < 0.15))):
        state = "PARSE_SUSPECT"           # 批238③:荒謬比例=誠實隔離
    elif upr is not None and upc is not None:
        state = ("EXACT_MATCH" if abs(upr - upc) < 0.05 else
                 "ROUNDING_ONLY" if abs(upr - upc) <= 0.8 else
                 "FORMULA_MISMATCH")
    elif upc is not None or upr is not None:
        state = "SINGLE_SOURCE"
    else:
        state = "MISSING_SOURCE"
    body = str(zones.get("body", ""))
    sents = [x for x in re.split(r"(?<=[。.!?])\s+", body.replace("\n", " "))
             if len(x) > 15][:2]
    _kind, _kind_why = classify_kind(stem, ticker)   # 批418:分得出型別才判得出成敗
    basic = {"report_file": stem, "ticker": ticker,
             "name_official": name_official,
             "broker": parse_broker(stem), "report_date": parse_date(stem),
             "rating_raw": rat.group(0) if rat else "",
             "target_price": tpv, "price": pxv,
             "upside_report": upr, "upside_calc": upc,
             "upside_state": state,
             "title_head": str(zones.get("header", ""))[:200],
             "summary_head": " ".join(sents)[:400],
             "conflicts": ";".join(conflicts),
             "report_kind": _kind, "kind_reason": _kind_why,
             "extracted_at": datetime.now().strftime("%Y-%m-%d %H:%M")}
    mets = []
    for m in EPS_RX.finditer(text_all):
        yraw = m.group(1)
        yr = str(int(yraw) + 1911) if len(yraw) == 3 else yraw
        seg = text_all[m.start():m.end() + 4]
        status = "ESTIMATE" if re.search(r"[EF]", seg) else "STATED"
        mets.append({"report_file": stem, "metric": "eps", "period": yr,
                     "status": status, "value": _num(m.group(2)),
                     "raw_text": m.group(0)[:80]})
    if tpv:
        mets.append({"report_file": stem, "metric": "target_price",
                     "period": basic["report_date"][:4], "status": "ESTIMATE",
                     "value": tpv, "raw_text": tp.group(0)[:80]})
    y = YLD_RX.search(text_all) or YLD_RX.search(text_rep)
    if y:
        mets.append({"report_file": stem, "metric": "dividend_yield_pct",
                     "period": basic["report_date"][:4], "status": "ESTIMATE",
                     "value": _num(y.group(1)), "raw_text": y.group(0)[:80]})
    return basic, mets


def _prior_close(con, ticker: str, rdate: str) -> float | None:
    """報告日前一交易日原始 close(批240 裁示:CLOSE 非 ADJ)"""
    if not ticker or not rdate:
        return None
    for t in (f"{ticker}.TW", f"{ticker}.TWO", ticker):
        try:
            r = con.execute(
                "SELECT close FROM tw_daily_prices WHERE ticker=? AND date<? "
                "ORDER BY date DESC LIMIT 1", [t, rdate]).fetchone()
            if r and r[0]:
                return float(r[0])
        except Exception:
            return None
    return None


# ---------------------------------------------------------------- 批412:金融機構 SSOT 接線
# 操作員令「SSOT補充報告分析師姓名擷取 BROKER / RATING DICTS」。
# 現況缺口(v0105 為止):
#   · BROKER_DICT 只有 16 條寫死鍵,而且鍵是「檔名子字串」(MS/Citi/凱基…),
#     不是正典鍵;外資 12 家與國內 16 家的中英別名、舊鍵遷移(BOA→BOFA、
#     MCQ/MQ→MACQUARIE)全都沒有。
#   · rating_raw 只存正則抓到的原字串,從不正規化(Outperform 與 買進 是兩筆)。
#   · **分析師姓名完全沒有抽取**——整條 VRN 鏈沒有任何一處在做這件事。
# 治法(Zero-Hydra:只調度不改寫):綁正典
# `supportive modules/ssot/VIA_Financial_Institution_SSOT_v0100.py`,
# 用它的 resolve_broker / resolve_rating / analyze_contact_document,
# 本器不自建任何第二份券商或評等字典。
# 只增不減:`broker` 與 `rating_raw` 兩欄語意與值**完全不動**(下游 MDL141/ENG080
# 仍讀得到原樣),新事實一律走新欄新表。
FIN_SSOT_DIR = VIA / "supportive modules" / "ssot"
_FIN = {"mod": None, "why": "", "tried": False}


def fin_ssot():
    """動態載入正典金融機構 SSOT(尾版律 glob;缺檔或缺 pydantic=誠實回 None 與因由)"""
    if _FIN["tried"]:
        return _FIN["mod"]
    _FIN["tried"] = True
    try:
        # 批413:改載**疊加層**(它內部再載正典)。理由:操作員裁決(去摩通/陸券刪除/
        # CLST 都可/增持加碼)與 Grok 冊補進來的 59 條評等別名都在那一層;
        # 正典依其 alias_governance 為 READ_ONLY,一個字都不動。
        hits = sorted(FIN_SSOT_DIR.glob("VIA_FinancialInstitution_Overlay_v*.py")) \
            or sorted(FIN_SSOT_DIR.glob("VIA_Financial_Institution_SSOT_v*.py"))
        if not hits:
            _FIN["why"] = "正典/疊加層皆缺檔(supportive modules/ssot/)"
            return None
        import importlib.util
        import sys as _sys
        spec = importlib.util.spec_from_file_location("via_fin_ssot_dyn", hits[-1])
        mod = importlib.util.module_from_spec(spec)
        # 這一行不能省:SSOT 用 `from __future__ import annotations`,pydantic 要靠
        # sys.modules[cls.__module__].__dict__ 才解得開延後註解(Optional 等)。
        # 少了它,模型建得起來但一 validate 就丟
        # 「`TextBlock` is not fully defined」——而且只在動態載入時發生,
        # 直接 `python SSOT.py` 跑自測不會重現(那時 __main__ 在 sys.modules 裡)。
        _sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        _FIN["mod"] = mod
        return mod
    except ImportError as exc:                    # 幾乎必然是 pydantic 未安裝
        _FIN["why"] = f"SSOT 載入失敗({exc});vrn 境補庫:uv pip install pydantic"
    except Exception as exc:
        _FIN["why"] = f"SSOT 載入失敗 {type(exc).__name__}:{str(exc)[:80]}"
    return None


def ssot_broker(stem: str, text: str) -> dict:
    """券商正規化 → {key, zh, en, src};認不出=全空(誠實,不硬猜)。
    次序:① 檔名(最可靠,報告命名慣例就是券商在前)② 內文。"""
    m = fin_ssot()
    if m is None:
        return {"key": "", "zh": "", "en": "", "src": ""}
    try:
        # 批413:疊加層回 dict(含 deny 因由);兩三字母檔名 token 走 filename 命名空間。
        tok = parse_broker(stem) or ""
        r = m.resolve_broker_filename(tok) if tok else {"key": "", "deny": ""}
        if r.get("deny"):                     # 操作員裁決不得採用(如 GF 廣發=陸券)
            return {"key": "", "zh": "", "en": "", "src": "DENY:" + r["deny"][:60]}
        if not r.get("key"):
            r = m.resolve_broker(stem)        # 檔名整串試別名
        if not r.get("key"):
            r = m.resolve_broker(text or "")  # 內文後備
        if r.get("deny"):
            return {"key": "", "zh": "", "en": "", "src": "DENY:" + r["deny"][:60]}
        if not r.get("key"):
            return {"key": "", "zh": "", "en": "", "src": ""}
        return {"key": r["key"], "zh": r.get("zh", ""), "en": r.get("en", ""),
                "src": r.get("src", "")}
    except Exception as exc:
        _FIN["why"] = _FIN["why"] or f"券商正規化例外 {type(exc).__name__}:{str(exc)[:70]}"
        return {"key": "", "zh": "", "en": "", "src": ""}


def ssot_rating(raw: str, text: str) -> dict:
    """評等正規化 → {key, code, direction, actionable};認不出=全空。
    raw 先查(那是本器既有 RATING_RX 抓到的字串),不中再掃內文。"""
    m = fin_ssot()
    if m is None:
        return {"key": "", "code": None, "direction": "", "actionable": None}
    try:
        r = m.resolve_rating((raw or "").strip())
        if not r.get("key"):
            # 內文逐詞試(疊加層沒有 extract_ratings;用本器既有 RATING_RX 詞表掃)
            for w in RATING_RX.findall(text or "")[:8]:
                w = w if isinstance(w, str) else (w[0] if w else "")
                if w and m.resolve_rating(w).get("key"):
                    r = m.resolve_rating(w)
                    break
        if not r.get("key"):
            return {"key": "", "code": None, "direction": "", "actionable": None}
        return {"key": r["key"], "code": r.get("code"),
                "direction": r.get("direction", ""), "actionable": r.get("actionable")}
    except Exception as exc:
        _FIN["why"] = _FIN["why"] or f"評等正規化例外 {type(exc).__name__}:{str(exc)[:70]}"
        return {"key": "", "code": None, "direction": "", "actionable": None}


def ssot_analysts(stem: str, zones: dict) -> list[dict]:
    """報告分析師姓名擷取(批412 新)。以 SSOT 的 analyze_contact_document 為引擎:
    它用 Email／電話當錨點,取鄰近行的中英文姓名候選,再以 local part 對姓名
    做相似度比對,並用網域反查機構;頁尾/附錄小字區另行分類。
    本器只做「調度 + 落表」,判準與正則全在 SSOT 那一份,不另立第二套。
    抽不到=回空清單(誠實;不把任何人名硬塞)。"""
    m = fin_ssot()
    if m is None:
        return []
    txt = "\n".join(str(zones.get(k, "")) for k in ("header", "right", "body", "footer"))
    if not txt.strip():
        return []
    try:
        canon = m.ssot() if hasattr(m, "ssot") else m      # 批413:分析師引擎在正典那一層
        if canon is None:
            _FIN["why"] = _FIN["why"] or (m.why() if hasattr(m, "why") else "正典缺席")
            return []
        res = canon.analyze_contact_document(txt)
    except Exception as exc:
        # 靜默回空=看起來像「這份報告沒有分析師」,那是假訊息。記因由,讓入庫計印出來。
        _FIN["why"] = f"分析師擷取例外 {type(exc).__name__}:{str(exc)[:90]}"
        return []
    # SSOT 給的是四個**語意不同**的欄:matched_*(與本錨點比對到的)與 *_guess
    # (自 email local part 還原、或英轉中音譯)。把它們併成一欄就是把「驗到的」
    # 和「猜的」混為一談,所以這裡分欄保留並記來源。
    rows = []
    zh_count: dict = {}
    for c in res.contacts:
        z = c.matched_chinese_name or ""
        if z:
            zh_count[z] = zh_count.get(z, 0) + 1
    for c in res.contacts:
        en, en_src = ((c.matched_english_name, "MATCHED") if c.matched_english_name
                      else (c.english_name_guess, "EMAIL_LOCALPART_GUESS") if c.english_name_guess
                      else ("", ""))
        zh, zh_src = ((c.matched_chinese_name, "NEARBY_MATCHED") if c.matched_chinese_name
                      else (c.chinese_name_guess, "TRANSLITERATION_GUESS") if c.chinese_name_guess
                      else ("", ""))
        if not (en or zh or c.email):
            continue                       # 連錨點都沒有的不留
        # 同一份報告裡同一個中文名被配給兩位以上=鄰近視窗誤配的典型徵狀。
        # 不刪(那是 SSOT 的判斷),但要標出來,不能讓它看起來像確定的事實。
        rows.append({"report_file": stem,
                     "analyst_en": en or "", "analyst_en_src": en_src,
                     "analyst_zh": zh or "", "analyst_zh_src": zh_src,
                     "zh_shared": bool(zh and zh_src == "NEARBY_MATCHED" and zh_count.get(zh, 0) > 1),
                     "email": c.email or "", "phones": ";".join(c.phones or []),
                     "domain": c.domain or "", "institution": c.institution or "",
                     "broker_ssot_key": c.broker_ssot_key or "",
                     "is_research": bool(c.is_research), "zone": c.zone or "",
                     "anchor_type": c.anchor_type or "",
                     "name_match_score": float(c.name_match_score or 0.0),
                     "confidence": float(c.confidence or 0.0),
                     "extracted_at": datetime.now().strftime("%Y-%m-%d %H:%M")})
    return rows


def _ensure_tables(con):
    con.execute("""CREATE TABLE IF NOT EXISTS vrn_report_basic(
        report_file VARCHAR, ticker VARCHAR, name_official VARCHAR,
        broker VARCHAR, report_date VARCHAR, rating_raw VARCHAR,
        target_price DOUBLE, price DOUBLE, upside_report DOUBLE,
        upside_calc DOUBLE, upside_state VARCHAR, title_head VARCHAR,
        summary_head VARCHAR, conflicts VARCHAR, extracted_at VARCHAR)""")
    for col in ("price_db DOUBLE", "upside_db DOUBLE", "price_state VARCHAR",
                # 批412:正典化新欄。舊欄 broker/rating_raw 保留原值不動(只增不減)
                "broker_ssot_key VARCHAR", "broker_name_zh VARCHAR",
                "broker_name_en VARCHAR", "broker_src VARCHAR",
                "rating_ssot_key VARCHAR", "rating_code INTEGER",
                "rating_direction VARCHAR", "analyst_names VARCHAR",
                "analyst_n INTEGER", "ssot_state VARCHAR",
                # 批418:報告型別。63 份真報告裡 19 份本來就不是個股報告,
                # 分不出型別就會被當成失敗——這兩欄讓收尾閘判得出來
                "report_kind VARCHAR", "kind_reason VARCHAR"):
        try:
            con.execute(f"ALTER TABLE vrn_report_basic ADD COLUMN {col}")
        except Exception:
            pass
    con.execute("""CREATE TABLE IF NOT EXISTS vrn_report_analyst(
        report_file VARCHAR, analyst_en VARCHAR, analyst_en_src VARCHAR,
        analyst_zh VARCHAR, analyst_zh_src VARCHAR, zh_shared BOOLEAN,
        email VARCHAR, phones VARCHAR, domain VARCHAR, institution VARCHAR,
        broker_ssot_key VARCHAR, is_research BOOLEAN, zone VARCHAR,
        anchor_type VARCHAR, name_match_score DOUBLE, confidence DOUBLE,
        extracted_at VARCHAR)""")
    con.execute("""CREATE TABLE IF NOT EXISTS vrn_report_metrics(
        report_file VARCHAR, metric VARCHAR, period VARCHAR,
        status VARCHAR, value DOUBLE, raw_text VARCHAR)""")


def run(zdir: Path | None = None, db: Path | None = None) -> int:
    import duckdb
    zdir = zdir or ZONES_DIR
    files = sorted(zdir.glob("*.json")) if zdir.exists() else []
    if not files:
        print(f"[入庫] {zdir} 無分區 sidecar(先跑 ENG072 v0101)")
        return 2
    dbp = _resolve_db(Path(db) if db else None)
    if dbp is None:
        return 2
    con = duckdb.connect(str(dbp))
    _ensure_tables(con)
    names = dict(con.execute(
        "SELECT code, name FROM tw_listings").fetchall()) \
        if "tw_listings" in {r[0] for r in con.execute("SHOW TABLES").fetchall()} \
        else {}
    nb = nm = na = 0
    for f in files:
        try:
            zones = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        basic, mets = extract_one(f.stem, zones, names)
        # 批240:庫驗證道(前日 close 補值/對質)
        pdb = _prior_close(con, basic["ticker"], basic["report_date"])
        tpv2 = basic["target_price"]
        basic["price_db"] = pdb
        basic["upside_db"] = round((tpv2 / pdb - 1) * 100, 1) \
            if tpv2 and pdb else None
        if pdb is None:
            basic["price_state"] = "DB_NO_MATCH" if basic["ticker"] else ""
        elif basic["price"] is None:
            basic["price_state"] = "P_FROM_DB"
        elif abs(basic["price"] - pdb) / pdb < 0.01:
            basic["price_state"] = "P_CONFIRMED_DB"
        else:
            basic["price_state"] = "P_DB_CONFLICT(KEEP_BOTH)"
        # 升幅態升級:頁無 P 但庫有=可判
        if basic["upside_state"] in ("MISSING_SOURCE", "SINGLE_SOURCE") \
                and basic["upside_db"] is not None:
            if basic["upside_report"] is not None:
                d0 = abs(basic["upside_report"] - basic["upside_db"])
                basic["upside_state"] = ("EXACT_MATCH_DB" if d0 < 0.05 else
                                         "ROUNDING_ONLY_DB" if d0 <= 0.8 else
                                         "FORMULA_MISMATCH_DB")
            else:
                basic["upside_state"] = "DB_DERIVED"
        # 批238④:派生層重算=同鍵 DELETE+INSERT(ENG063 同例;
        # 正本=input_reports 原件+sidecar 零觸碰)
        # 批412:券商/評等正規化 + 分析師姓名擷取(SSOT 缺席=新欄留空,舊欄不受影響)
        _txt = "\n".join(str(zones.get(k, "")) for k in ("header", "right", "body", "footer"))
        _bk = ssot_broker(f.stem, _txt)
        _rt = ssot_rating(basic.get("rating_raw", ""), _txt)
        _an = ssot_analysts(f.stem, zones)
        basic["broker_ssot_key"] = _bk["key"]
        basic["broker_name_zh"] = _bk["zh"]
        basic["broker_name_en"] = _bk["en"]
        basic["broker_src"] = _bk["src"]
        basic["rating_ssot_key"] = _rt["key"]
        basic["rating_code"] = _rt["code"]
        basic["rating_direction"] = _rt["direction"]
        basic["analyst_names"] = ";".join(
            [(x["analyst_en"] or x["analyst_zh"]) for x in _an if (x["analyst_en"] or x["analyst_zh"])])[:400]
        basic["analyst_n"] = len(_an)
        basic["ssot_state"] = "OK" if fin_ssot() is not None else f"SSOT_ABSENT:{_FIN['why'][:60]}"
        na += len(_an)
        # 批238④:派生層重算=同鍵 DELETE+INSERT(ENG063 同例;
        # 正本=input_reports 原件+sidecar 零觸碰)
        con.execute("DELETE FROM vrn_report_basic WHERE report_file=?",
                    [basic["report_file"]])
        con.execute("DELETE FROM vrn_report_metrics WHERE report_file=?",
                    [basic["report_file"]])
        con.execute("DELETE FROM vrn_report_analyst WHERE report_file=?",
                    [basic["report_file"]])
        # 批412:改具名欄位 INSERT。舊版是 `VALUES (?×18)` 位置式,一旦 ALTER 加欄
        # 就會欄數不合而整批爆掉——加欄與位置式 INSERT 天生互斥,這是必須一起改的。
        _cols = list(basic.keys())
        con.execute(f"INSERT INTO vrn_report_basic ({','.join(_cols)}) VALUES ("
                    + ",".join("?" * len(_cols)) + ")", [basic[c] for c in _cols])
        for _a in _an:
            _ac = list(_a.keys())
            con.execute(f"INSERT INTO vrn_report_analyst ({','.join(_ac)}) VALUES ("
                        + ",".join("?" * len(_ac)) + ")", [_a[c] for c in _ac])
        nb += 1
        for m in mets:
            con.execute("INSERT INTO vrn_report_metrics VALUES (?,?,?,?,?,?)",
                        list(m.values()))
            nm += 1
        flag = basic["upside_state"]
        print(f"  [{flag}] {basic['ticker']} {basic['name_official'] or '?'} "
              f"{basic['broker']} TP={basic['target_price']} "
              f"P={basic['price']} 庫P={basic['price_db']}"
              f"({basic['price_state']}) 升幅 報告={basic['upside_report']} "
              f"算={basic['upside_calc']} 庫算={basic['upside_db']}")
    tb = con.execute("SELECT count(*) FROM vrn_report_basic").fetchone()[0]
    tm = con.execute("SELECT count(*) FROM vrn_report_metrics").fetchone()[0]
    ta = con.execute("SELECT count(*) FROM vrn_report_analyst").fetchone()[0]
    nbk = con.execute("SELECT count(*) FROM vrn_report_basic WHERE broker_ssot_key<>''").fetchone()[0]
    nrt = con.execute("SELECT count(*) FROM vrn_report_basic WHERE rating_ssot_key<>''").fetchone()[0]
    con.close()
    print(f"[入庫計] 檔 {len(files)} · basic +{nb}(庫 {tb})· metrics +{nm}"
          f"(庫 {tm})· 官方名冊命中={sum(1 for _ in names) and '在庫'}")
    _m = fin_ssot()
    print(f"  [SSOT 正規化] 券商正典鍵 {nbk}/{tb} · 評等正典鍵 {nrt}/{tb} · "
          f"分析師 +{na}(庫 {ta})· "
          + ("金融機構 SSOT 在位" if _m is not None else f"**SSOT 缺席**:{_FIN['why']}"))
    return 0


def status() -> int:
    import duckdb
    con = duckdb.connect(str(DB_TW), read_only=True)
    for t in ("vrn_report_basic", "vrn_report_metrics"):
        try:
            n = con.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
            print(f"  [{t}] {n:,} 列")
        except Exception:
            print(f"  [{t}] 未建(先 run)")
    con.close()
    return 0


def selftest() -> int:
    import tempfile
    import duckdb
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src = Path(__file__).read_text(encoding="utf-8")
    chk("① 官方名冊正主宣告(ticker→tw_listings=TWSE/TPEX;零網路)",
        "tw_listings" in src and all(("import " + k) not in src
                                     for k in ("requests", "httpx")))
    zones = {"header": "Earnings Upside; Reiterate Buy",
             "right": "Buy\nTarget price NT$165.00\nPrice (04 Jun) NT$114.00\n"
                      "Expected total return 48.1%\nExpected dividend yield 3.3%",
             "body": "Wistron 3231 reported strong sales. We expect 2025E EPS 9.8 "
                     "to grow further. Momentum continues into 2H25.",
             "footer": "disclaimer"}
    names = {"3231": "緯創"}
    basic, mets = extract_one("Citi-3231 20250604", zones, names)
    chk("② Basic Info(ticker/官方名/券商/日期/評等/TP/現價)",
        basic["ticker"] == "3231" and basic["name_official"] == "緯創"
        and basic["broker"] == "Citi" and basic["report_date"] == "2025-06-04"
        and "Buy" in basic["rating_raw"] and basic["target_price"] == 165.0
        and basic["price"] == 114.0)
    chk("③ 交互驗證(Upside 報告 48.1% vs 算 44.7%=FORMULA_MISMATCH 誠實列示)",
        basic["upside_calc"] == 44.7
        and basic["upside_state"] == "FORMULA_MISMATCH")
    chk("④ Financial(EPS 2025E=9.8 ESTIMATE+殖利率+TP;帶 raw 證據)",
        any(m["metric"] == "eps" and m["value"] == 9.8
            and m["status"] == "ESTIMATE" and m["period"] == "2025"
            for m in mets)
        and any(m["metric"] == "dividend_yield_pct" for m in mets)
        and all(m["raw_text"] for m in mets))
    chk("⑤ Summary 頭=決定性(標題帶+本文前二句;零 LLM 創造)",
        "Reiterate Buy" in basic["title_head"]
        and "strong sales" in basic["summary_head"])
    b2, _ = extract_one("華南投顧-2606-裕民-1141202", {"header": "", "right": "",
                                                      "body": "", "footer": ""},
                        {"2606": "裕民"})
    chk("⑥ 民國日期+缺值誠實(1141202→2025-12-02;無 TP=MISSING_SOURCE)",
        b2["report_date"] == "2025-12-02"
        and b2["upside_state"] == "MISSING_SOURCE")
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        (tdp / "Citi-3231 20250604.json").write_text(
            json.dumps(zones, ensure_ascii=False), encoding="utf-8")
        dbp = tdp / "t.duckdb"
        c0 = duckdb.connect(str(dbp))
        c0.execute("CREATE TABLE tw_listings(code VARCHAR, name VARCHAR)")
        c0.execute("INSERT INTO tw_listings VALUES ('3231','緯創')")
        c0.close()
        rc1 = run(tdp, dbp)
        rc2 = run(tdp, dbp)
        con = duckdb.connect(str(dbp))
        nb = con.execute("SELECT count(*) FROM vrn_report_basic").fetchone()[0]
        nm = con.execute("SELECT count(*) FROM vrn_report_metrics").fetchone()[0]
        con.close()
        chk("⑦ 落庫+重跑冪等(派生層重算=同鍵重寫;basic 恆 1 列)",
            rc1 == 0 and rc2 == 0 and nb == 1 and nm >= 3)
        c2 = duckdb.connect(str(dbp))
        c2.execute("INSERT INTO tw_listings VALUES ('1476','儒鴻')")
        c2.execute("CREATE TABLE tw_daily_prices(date VARCHAR, ticker VARCHAR,"
                   " close DOUBLE)")
        c2.execute("INSERT INTO tw_daily_prices VALUES "
                   "('2025-06-03','3231.TW',113.5),"
                   "('2026-05-18','1476.TW',350.0)")
        c2.close()
        (tdp / "凱基投顧_1476 儒鴻_20260519.json").write_text(json.dumps(
            {"header": "", "right": "目標價 367 元\n收盤價 19",
             "body": "", "footer": ""}, ensure_ascii=False), encoding="utf-8")
        run(tdp, dbp)
        con = duckdb.connect(str(dbp))
        r1 = con.execute("SELECT price_db, upside_db, price_state, upside_state"
                         " FROM vrn_report_basic WHERE ticker='1476'").fetchone()
        r2 = con.execute("SELECT price_db, price_state FROM vrn_report_basic "
                         "WHERE ticker='3231'").fetchone()
        con.close()
        chk("⑱ 庫補值道(批240:凱基 P 缺→前日 close 350 補;升幅 4.9=DB_DERIVED)",
            r1 is not None and r1[0] == 350.0 and r1[1] == 4.9
            and r1[2] == "P_FROM_DB" and r1[3] == "DB_DERIVED")
        chk("⑲ 庫對質道(Citi 頁 P=114 vs 庫 113.5 差<1%=P_CONFIRMED_DB)",
            r2 is not None and r2[0] == 113.5 and r2[1] == "P_CONFIRMED_DB")
        chk("⑧ 空夾誠實 rc2", run(tdp / "none_x", dbp) == 2)
    b3, _ = extract_one("MS-3661 20251203",
                        {"header": "", "right": "Price Target NT$4,388.00",
                         "body": "", "footer": ""}, {"3661": "世芯-KY"})
    chk("⑪ 美系 Price Target(批238①:TP=4388 且不誤入現價)",
        b3["target_price"] == 4388.0 and b3["price"] is None)
    b4, _ = extract_one("第一場 2026年投資大趨勢 - 華南投顧 -1141201",
                        {"header": "", "right": "", "body": "", "footer": ""},
                        {"3661": "世芯-KY"})
    chk("⑫ 研討會檔誠實非個股(批238②:2026 不當 ticker)",
        b4["ticker"] == "")
    b5, _ = extract_one("凱基投顧_1476 儒鴻_20260519",
                        {"header": "", "right": "目標價 367 元\n收盤價 19",
                         "body": "", "footer": ""}, {"1476": "儒鴻"})
    chk("⑬ 配對收斂(批239:TP=367 留/P=19 碎片丟=寧缺勿假)",
        b5["target_price"] == 367.0 and b5["price"] is None
        and b5["upside_state"] == "MISSING_SOURCE")
    b6, _ = extract_one("MS-1590 20251202",
                        {"header": "", "right": "Price Target NT$1,130.00",
                         "body": "share price fell 2. points", "footer": ""},
                        {"1590": "亞德客-KY"})
    chk("⑭ MS 型(TP=1130 可信;P 小雜數 2 落配對外=None)",
        b6["target_price"] == 1130.0 and b6["price"] is None)
    b7, _ = extract_one("JP-2330 20250718",
                        {"header": "", "right": "Price NT$1,130\nPT Dec-25",
                         "body": "", "footer": ""}, {"2330": "台積電"})
    chk("⑮ JP 型(TP 候選 25 對 P=1130 失真=丟;P=1130 存)",
        b7["price"] == 1130.0 and b7["target_price"] is None)
    b8, _ = extract_one("Citi-3231 20250604", zones, {"3231": "緯創"})
    chk("⑯ 正常對照不退化(Citi TP=165/P=114 配對成立)",
        b8["target_price"] == 165.0 and b8["price"] == 114.0)
    b9, _ = extract_one("GS-2317 20251205",
                        {"header": "", "right": "Target\nprice\nNT$250.00\n"
                                                "Price\nNT$205.00",
                         "body": "", "footer": ""}, {"2317": "鴻海"})
    chk("⑳ CLOSE 正主宣告(批240 裁示:原始 close 非 adj_close)",
        "SELECT close FROM tw_daily_prices" in src
        and "adj_close" not in src.split("def _prior_close")[1]
                                  .split("def _ensure_tables")[0])
    chk("⑰ 斷行修復救回(批239b:Target↵price 切開仍抓 TP=250/P=205)",
        b9["target_price"] == 250.0 and b9["price"] == 205.0)
    chk("⑨ 雙 SSOT 紀律(KEEP_BOTH 衝突列示;REPORT_ESTIMATE 隔離宣告)",
        "KEEP_BOTH" in src and "ESTIMATE" in src and "不覆寫" in src)
    chk("⑩ NLP 掛載 graceful+加速橋",
        "TextProcessor" in src and "ACCEL-BRIDGE" in src)
    # ---------------- 批412:金融機構 SSOT 接線三檢 ----------------
    _mod = fin_ssot()
    if _mod is None:
        # 誠實三態:SSOT 缺席不是綠也不是啞;明說缺什麼、怎麼補,三檢一律紅。
        for _n in ("㉑ 券商正典化", "㉒ 評等正典化", "㉓ 分析師姓名擷取"):
            chk(f"{_n}(批412)", False, f"(金融機構 SSOT 缺席:{_FIN['why']})")
    else:
        b1 = ssot_broker("Citi_2330_20250604", "")
        b2 = ssot_broker("MQ_2454_251208", "")              # 舊鍵 MQ → 正典 MACQUARIE
        b3 = ssot_broker("凱基_2317_1141202", "")
        b4 = ssot_broker("no_such_house_2330", "")          # 認不出=誠實空
        chk("㉑ 券商正典化(批412:綁正典 SSOT,本器不自建第二份字典;舊鍵遷移;認不出=空)",
            b1["key"] == "CITI" and b1["zh"] == "花旗環球證券"
            and b2["key"] == "MACQUARIE" and b3["key"] == "KGI"
            and b4["key"] == "" and b4["zh"] == "",
            f"({b1['key']}/{b2['key']}/{b3['key']}/空={b4['key'] == ''})")
        r_buy, r_out, r_ow = ssot_rating("Buy", ""), ssot_rating("Outperform", ""), ssot_rating("增持", "")
        r_nr, r_ss = ssot_rating("NR", ""), ssot_rating("強力買進", "")
        r_no = ssot_rating("", "本頁無任何評等字樣")
        chk("㉒ 評等正典化(批412:英中同義歸一鍵;NR=NOT_RATED code0;認不出=空)",
            r_buy["key"] == r_out["key"] == "BUY" and r_buy["code"] == 2
            and r_buy["direction"] == "POSITIVE"
            and r_nr["key"] == "NOT_RATED" and r_nr["code"] == 0 and r_nr["actionable"] is False
            and r_ss["key"] == "STRONG_BUY" and r_no["key"] == "",
            f"(Buy/Outperform→{r_buy['key']} · 增持→{r_ow['key']} · NR→{r_nr['key']})")
        z = {"header": "台積電 (2330 TT) — Buy, Target Price NT$1,500",
             "body": "Morgan Stanley Research",
             "footer": ("Analyst Certification\nJohn Smith    Equity Analyst\n"
                        "john.smith@morganstanley.com   +886 2 2345 6789\n"
                        "王小明  研究員\nhsiaoming.wang@kgi.com.tw   02-2345-6789\n")}
        an = ssot_analysts("MS_2330_20260908", z)
        by_mail = {x["email"]: x for x in an}
        ms = by_mail.get("john.smith@morganstanley.com", {})
        kgi = by_mail.get("hsiaoming.wang@kgi.com.tw", {})
        an0 = ssot_analysts("EMPTY", {"header": "", "body": "", "footer": ""})
        chk("㉓ 分析師姓名擷取(批412 新能力:email 錨點→姓名/電話/網域→機構與正典鍵;"
            "matched 與 guess 分欄記來源;同一中文名配給多人即標 zh_shared;無錨點=誠實空)",
            len(an) == 2
            and ms.get("analyst_en") == "John Smith"
            and ms.get("analyst_en_src") == "EMAIL_LOCALPART_GUESS"
            and ms.get("institution") == "摩根士丹利" and ms.get("broker_ssot_key") == "MS"
            and kgi.get("broker_ssot_key") == "KGI" and kgi.get("institution") == "凱基證券"
            and ms.get("zh_shared") is True and kgi.get("zh_shared") is True
            and an0 == [],
            f"({len(an)} 位 · {ms.get('broker_ssot_key')}/{kgi.get('broker_ssot_key')} · "
            f"zh_shared={ms.get('zh_shared')})")
    # ── 批418 三檢:年份守衛 + 報告型別。fixture 全部取自操作員給的 63 份真檔名 ──
    REAL = {
        "conf": "第三場 AI潮流下展望2026半導體產業趨勢 - 陳子昂",
        "conf2": "第一場 2026年投資大趨勢 - 華南投顧 -1141201",
        "stock": "凱基投顧_3665 貿聯-KY_李承泰_20260519",
        "ind": "MS-Thermal Solutions 20251007",
        "morn": "20251205兆豐晨會報告(一)-當日新聞與重要訊息評論",
        "os": "凱基日股分析20251205-軍工股及機器人股上漲推升日股收漲",
        "datey": "GS-2382 20231012",
    }
    # 2026 是**真實上市代號**(聚亨),所以名冊逐驗擋不住——必須靠年份守衛
    roster = {"2026": "聚亨", "3665": "貿聯-KY", "2382": "廣達", "2023": "X"}
    r_conf, _ = extract_one(REAL["conf"], {}, roster)
    r_conf2, _ = extract_one(REAL["conf2"], {}, roster)
    r_stock, _ = extract_one(REAL["stock"], {}, roster)
    r_date, _ = extract_one(REAL["datey"], {}, roster)
    chk("㉔ 年份守衛(批418:「展望2026半導體產業趨勢」的 2026 是年份不是代號——"
        "而 2026 恰好也是真實上市代號 聚亨,連逐驗名冊都擋不住;假代號入正本庫比缺代號更糟)",
        r_conf["ticker"] == "" and r_conf2["ticker"] == ""
        and "YEAR_NOT_TICKER" in r_conf["conflicts"]
        and r_stock["ticker"] == "3665"          # 真個股不得被誤殺
        and r_date["ticker"] == "2382",          # 日期 20231012 內的 2023 不得被當代號
        f"(研討會 {r_conf['ticker'] or '空'}/{r_conf2['ticker'] or '空'} · 個股 {r_stock['ticker']} · 日期件 {r_date['ticker']})")

    kinds = {k: extract_one(v, {}, roster)[0]["report_kind"] for k, v in REAL.items()}
    chk("㉕ 報告型別分類(批418:63 份真報告有 19 份本來就不是個股——產業/大盤晨報/"
        "海外/研討會;分不出型別就會被當成一整面失敗)",
        kinds["stock"] == "個股" and kinds["ind"] == "產業"
        and kinds["morn"] == "大盤晨報" and kinds["os"] == "海外"
        and kinds["conf"] == "研討會",
        " · ".join(f"{k}={v}" for k, v in kinds.items()))

    chk("㉖ 只有個股型才「應該」有代號(收尾閘拿這支判,免得產業/晨報/研討會被算成紅);"
        "認不出型別=誠實「其他」不硬塞個股",
        kind_expects_ticker("個股") is True
        and all(kind_expects_ticker(k) is False for k in ("產業", "大盤晨報", "海外", "研討會", "其他"))
        and classify_kind("某某不明檔案", "")[0] == "其他"
        and classify_kind("某某不明檔案", "")[1].startswith("無代號"),
        f"(個股 True · 其餘 False · 不明={classify_kind('某某不明檔案', '')[0]})")
    print(f"  [計] 二十六檢 OK {26 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 報告結構化入庫引擎(VRN_ENG073 v0108)· 二十六檢自測(零網路)===")
        return selftest()
    if "--status" in args:
        return status()
    if args and args[0] == "run":
        return run()
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
