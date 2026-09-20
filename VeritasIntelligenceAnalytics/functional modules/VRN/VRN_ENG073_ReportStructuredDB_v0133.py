#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v0128→v0129(批558 操作員令「加入同義字 第一頁周圍訊息區塊及中間本文標題區修復後尋找」)
  同義字補齊之後的下一題是**在哪裡找**。兩個區,都修復後再找:
  ① **第一頁周圍訊息區塊**(頁首帶/右資訊區/**頁尾**)——這裡有一個**量出來的真漏**:
     `extract_one` 的主 join 從批237 起就寫 `("header","right","body")`,**沒有 `footer`**,
     於是頁尾的目標價/評等/代碼一直看不見。而同一支檔六百行外的另一處 join 是有 footer 的
     ——**兩處對同一件事的定義不一致,其中一處漏了一個鍵**。缺鍵不報錯,只安靜地少一區,
     長得跟「那裡本來就沒東西」一模一樣,所以擺了三百多批沒人看見。
  ② **中間本文標題區**——研報常把「【投資評等】增加持股」「二、目標價 250 元」寫在段落標題上,
     不在右邊資訊欄裡。只掃資訊欄會漏;整段本文亂掃會撿到敘述句裡的假評等(LL68)。
     標題區是中間那個剛好的粒度;偵測實作放在樞紐(四支引擎之後拿同一份,不各寫一份)。
  補進來的兩區一律**接在既有搜尋序之後**:先命中的仍然先贏,所以這一批對既有命中是
  **純增量、零改判**(檢 ㊶ 直接量這件事,不是用講的)。
v0127→v0128(批554 操作員令「評等以同義字為主 · 本文修復後本文也可擷取到評等同義字跟目標價」)
  評等第四道:**向 SUP_MDL749 規則樞紐要實作**(不是再抄一份 38 詞的詞表——那是第二顆頭)。
  量過的落差(不是假設):正本 38 詞裡本器判不出 14 個(accumulate/add/equal-weight/equalweight/
  market perform/reduce/區間/同步大盤/增加持股/弱於大盤/強於大盤/減少持股/與大盤同步/逢低),
  樞紐 14 個全判得出。守衛一起繼承(本土尺度只看前段 · 線索詞 · 整行等於),
  所以「本文也可擷取」不等於「全文亂掃」:六條內文假朋友(外資持有比重/增持庫藏股/營收區間/
  新增產能/add capacity/持股比重)放進本文第 47 行實測,樞紐六條全部不命中。
  樞紐缺席=回到 v0127 的三道(誠實退路,零行為變更)。
v0125→v0126(批521 工作站實錄 via-ryg vrn RED ㉞:Windows 上 Path('/tmp/_d_') 印成 \\tmp\\_d_,字串比對永遠不等=判錯的紅燈;改 as_posix 比對;程式行為零改)
v0124→v0125(批508):目標價/現價成對契約 ㊱ 改用三組自生文字夾具，不再依賴
工作站 VIA_Reports 裡三份私人 sidecar；fresh clone 仍實證新舊守衛差異。
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
用法:python3 VRN_ENG073_ReportStructuredDB_v0117.py run [--dir 報告夾] [--db 庫檔] [--open]
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
    r"""批244:庫路徑誠實解析(工作站雙 clone 債——mega 庫可能在
    Downloads\movies-dataset 替根)。顯式 db=信任直用(selftest 建新
    庫);預設=主路徑→替根探測;全缺=None 誠實停 rc2 不 traceback。"""
    if db is not None:
        return Path(db)
    # 批490 資料家優先(操作員宣告 C:\\Users\\tonyk\\VIA System\\via_database;啟動層把目錄放進 env):
    #   VIA_DB_VDF_TW_MARKET(目錄頁按名解出的路徑)> VIA_DATA_HOME 家內按名找(單檔家也認)> 舊路徑鏈。
    _env_db = os.environ.get("VIA_DB_VDF_TW_MARKET")
    if _env_db and Path(_env_db).exists():
        print(f"[庫解析] 資料家目錄頁→{_env_db}")
        return Path(_env_db)
    _home = os.environ.get("VIA_DATA_HOME")
    if _home and Path(_home).exists():
        _hp = Path(_home)
        try:
            _hits = [_hp] if (_hp.is_file() and _hp.name == "vdf_tw_market.duckdb") else \
                    [x for x in _hp.rglob("vdf_tw_market.duckdb")] if _hp.is_dir() else []
            if _hits:
                _best = max(_hits, key=lambda x: x.stat().st_mtime)
                print(f"[庫解析] 資料家 {_hp} 內尋獲 {len(_hits)} 本,用最新的:{_best}")
                return _best
            print(f"[庫解析] 資料家 {_hp} 內無 vdf_tw_market.duckdb(誠實;續用舊路徑鏈)")
        except Exception as _exc:
            print(f"[庫解析] 資料家探查失敗 {type(_exc).__name__}:{str(_exc)[:60]}(續用舊路徑鏈)")
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
    # 批489 操作員實錄:他的 vdf_tw_market.duckdb 既不在 output_hub/mega/ 也不在兩個寫死的替根
    # (~/Downloads、~/)——寫死路徑正是批452/453 三副本病。最後一道:在 VIA 樹裡**找**同名庫
    # (排除 references / SCOPE_COPY / 自測沙盒 / _repo_ 副本),多本取最新修改的,並印出用了哪本。
    try:
        hits = []
        for h in VIA.rglob("vdf_tw_market.duckdb"):
            sp = str(h).replace("\\", "/")
            if any(m in sp for m in ("/references/", "SCOPE_COPY", "/engine_bus/_cwd/", "/selftest_grid/", "/vdfout_runs/selftest_out/", "_self_test", "_repo_")):
                continue
            hits.append(h)
        if hits:
            best = max(hits, key=lambda x: x.stat().st_mtime)
            print(f"[庫解析] 主路徑與替根皆缺→樹內尋獲 {len(hits)} 本,用最新的:{best}(誠實提示;冊上該寫路徑)")
            return best
    except Exception:
        pass
    print(f"[庫缺] {DB_TW} 不在且替根未尋獲=誠實停(rc2)。"
          "先跑 VDF_ENG065_DbImport 三包匯入,或確認 clone 根。")
    return None


import contextlib
import io
import json
import os
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
ZONES_DIR = VIA / "VIA_Reports" / "first_page_text"

# =====================================================================
# 檔名層正典橋(批442 操作員令「兩邊工具都要一致化,邏輯一致化」)
# ---------------------------------------------------------------------
# 量過才改:庫內 64 份跑完入庫,與首頁全能引擎逐檔比對——
#   型別不一致 38/64 · 代號不一致 37/64
# 根因不是啟發式微調,是**兩個引擎讀不同的名冊表**:
#   首頁引擎  NameReconciler 階梯 → tw_listings_industry(1978 檔),6873 **在**
#   本引擎    寫死 tw_listings(891 檔),6873 **不在**
# 代號查不到 → 型別掉成「其他」 → BASIC INFO 整片是空的。
# 零九頭龍:不抄一份過去,**綁首頁引擎的公開契約** filename_facts()。
# 橋缺席就退本檔原邏輯,並把因由印出來——靜默退後備是批419e 記過的病。
# =====================================================================
_FN_BRIDGE = {"mod": None, "eng": None, "why": "未嘗試"}


def _fn_bridge():
    """回 (FirstPageEngine 實例 | None, 因由)。只掛一次。"""
    if _FN_BRIDGE["why"] != "未嘗試":
        return _FN_BRIDGE["eng"], _FN_BRIDGE["why"]
    hits = sorted((VIA / "functional modules" / "VRN").glob(
        "VIA_VRN_FirstPageEngine_v*.py"))
    if not hits:
        _FN_BRIDGE["why"] = "首頁全能引擎缺檔=退本檔原檔名層(名冊仍為 tw_listings)"
        return None, _FN_BRIDGE["why"]
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("via_fpe_for_eng073", hits[-1])
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        if not hasattr(mod.FirstPageEngine, "filename_facts"):
            _FN_BRIDGE["why"] = (f"{hits[-1].name} 尚無 filename_facts 契約"
                                 "(需 v0119+)=退本檔原檔名層")
            return None, _FN_BRIDGE["why"]
        eng = mod.FirstPageEngine()
        f = eng.filename_facts("x.pdf")
        _FN_BRIDGE["eng"] = eng
        _FN_BRIDGE["why"] = (f"綁 {hits[-1].name} filename_facts · "
                             f"名冊 {f.get('roster_n')} 檔({f.get('roster_state')})")
    except Exception as exc:
        _FN_BRIDGE["why"] = (f"橋載入失敗 {type(exc).__name__}:{str(exc)[:70]}"
                             "=退本檔原檔名層")
    return _FN_BRIDGE["eng"], _FN_BRIDGE["why"]
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
def _tp_terms() -> tuple:
    """目標價的詞表**取自正典機構 SSOT**(批472 操作員令「中央控管的 ssot regx 同義字」)。

    v0121 以前這裡寫死四個詞(`Target price|Price Target|目標價|PT`),
    而 `supportive modules/ssot/VIA_Financial_Institution_SSOT_v0100.json` 的
    `registries.research_fields.TARGET_PRICE.aliases` 有 **16 條**——
    多出來的是 `目標股價` `合理價` `合理股價` `預期價` `Fair Value` `FV` `Tgt`
    `Valuation` `Target` `目標` `目標區間`。**同義字有中央冊,引擎卻各寫各的**,
    那本冊就永遠只是一份沒人跟的文件。
    次序:長詞在前(`目標股價` 不可以被 `目標` 先吃掉)。
    冊缺=退回 v0121 那四個詞,並在 `_TP_SRC` 講明走了退路(不假裝綁了冊)。
    """
    import json as _json
    base = ["Target price", "Price Target", "目標價", "PT"]
    d = VIA / "supportive modules" / "ssot"
    try:
        hits = sorted(d.glob("VIA_Financial_Institution_SSOT_v*.json"))
        if not hits:
            return tuple(base), "冊缺(supportive modules/ssot/)=退本地四詞"
        reg = _json.loads(hits[-1].read_text(encoding="utf-8")).get("registries") or {}
        al = ((reg.get("research_fields") or {}).get("TARGET_PRICE") or {}).get("aliases")
        # 疊加層若也帶了 research_fields 就疊上去(它現在沒有,但形狀留著)
        for ov in sorted(d.glob("VIA_FinancialInstitution_Overlay_v*.json")):
            oreg = (_json.loads(ov.read_text(encoding="utf-8")).get("registries") or {})
            oal = ((oreg.get("research_fields") or {}).get("TARGET_PRICE") or {}).get("aliases")
            if oal:
                al = list(al or []) + [x for x in oal if x not in (al or [])]
        if not al:
            return tuple(base), f"冊在但無 TARGET_PRICE 別名({hits[-1].name})=退本地四詞"
        terms = sorted({str(x).strip() for x in al if str(x).strip()}, key=len, reverse=True)
        return tuple(terms), f"冊 {hits[-1].name} · {len(terms)} 詞"
    except Exception as exc:
        return tuple(base), f"讀冊失敗 {type(exc).__name__}=退本地四詞"


_TP_TERMS, _TP_SRC = _tp_terms()
#: 純英數的短詞(PT/FV/TP/Tgt)要加詞界,否則會在別的字中間命中;
#: 中文詞不加 \b(中文沒有詞界,加了反而不匹配)。
_TP_ALT = "|".join(
    (r"\b" + re.escape(t) + r"\b") if re.fullmatch(r"[A-Za-z][A-Za-z .]*", t)
    else re.escape(t).replace(r"\ ", r"\s*")
    for t in _TP_TERMS)
TP_RX = re.compile(r"(?:" + _TP_ALT + r")"
                   r"[^\d]{0,20}(?:NT\$|新台幣)?\s*"
                   r"([\d,]+(?:\.\d+)?)", re.I)
#: 目標價也要一條**帶幣別記號**的優先車道(與 PX_CUR_RX 同律)。
#: 真檔實測(不是我新造的迴歸,v0121 同樣中):
#:     `Price Target (Dec-26):NT$3,650.00` → 舊式的 `[^\d]{0,20}` 先撞到
#:     括號裡的年份碎片「26」,3,650 整個漏掉。
#: 分辨的憑據一樣是幣別記號:真價格旁邊有 NT$/US$/$,日期旁邊沒有。
TP_CUR_RX = re.compile(r"(?:" + _TP_ALT + r")"
                       r"[^\n]{0,40}?\(?\s*(?:NT\$|US\$|\$|新台幣)\s*\)?\s*"
                       r"([\d,]+(?:\.\d+)?)", re.I)
# 批471:`(?<![Ss]pot )(?<![Cc]ontract )` 與新車道同律——商品現貨/合約報價
# 不是個股收盤價(MS-Memory:`spot price of US$45.5`)。舊車道是退路,
# 退路也要守同一條律,否則正道擋掉的它又撿回來(實測就是這樣漏的)。
PX_RX = re.compile(r"(?<![Tt]arget )(?<![Tt]arget\n)(?<![Tt]ARGET )"
                   r"(?<![Ss]pot )(?<![Cc]ontract )(?:\b[Pp]rice\b(?![ \t]*"
                   r"[Tt]arget)|現價|收盤價)\s*(?:\([^)]*\))?[^\d]{0,20}"
                   r"(?:NT\$)?\s*([\d,]+(?:\.\d+)?)", re.M)
#: 批471(迴歸閘 ENG076 照出來的**我方真缺陷**):
#: PX_RX 的 `[^\d]{0,20}` 會先撞到標籤與數字之間那個**日期裡的日**——
#:     `Shr price, close (Dec 2, 2025) NT$885.00`  → 抓到「2」,漏掉 885
#:     `收盤價 May 19 (NT$) 320.0`                  → 抓到「19」,漏掉 320
#: 六份 MS/凱基真報告全中,而且**基準包當年掉進同一個洞**(它的 close_price 記的正是
#: 那些日),所以兩邊看起來「一致」——同一個錯,對照組驗不出來。
#: 分辨的憑據不是位置,是**幣別記號**:真價格旁邊一定有 NT$ / US$ / $,
#: 日期旁邊沒有。所以先找有幣別記號的那一個,找不到才退回舊式。
#: `(?<!spot )(?<!contract )` —— 真檔實測:MS-Memory 產業報告寫著
#: `spot pricing as high as US$100, compared to spot price of US$45.5`,
#: 那是 **DRAM 現貨報價**不是股票收盤價。基準包抓了 45.5、我方抓了 100,
#: **兩個都不對**,正確答案是 None(產業報告沒有單一個股價)。
#: **`Target` 守衛要照抄舊車道的三種**(批471 自審修:檢 ⑰ 抓到的真迴歸)。
#: 我第一版只擋了 `spot`/`contract`,忘了 PX_RX 本來就有的
#: `(?<![Tt]arget )(?<![Tt]arget\n)(?<![Tt]ARGET )`——而 fixture 正是
#: `Target↵price↵NT$250.00`(斷行修復道,批239b)。少一個換行版的守衛,
#: 目標價就被當成現價收進候選集第一位,配對律取首對得到 (250,250),
#: 再被「同一個數讀兩次」律把 TP 歸零 → TP=None P=250,兩個都錯。
#: **新車道排在舊車道前面,就必須把舊車道的每一道守衛都帶齊**,
#: 否則等於用一條沒穿衣服的規則去覆蓋一條穿好的。
PX_CUR_RX = re.compile(
    r"(?:(?<![Ss]pot )(?<![Cc]ontract )(?<![Tt]arget )(?<![Tt]arget\n)(?<![Tt]ARGET )"
    r"\b[Pp]rice\b(?![ \t\n]*[Tt]arget)|現價|收盤價)"
    r"[^\n]{0,40}?\(?\s*(?:NT\$|US\$|\$|新台幣)\s*\)?\s*"
    r"([\d,]+(?:\.\d+)?)", re.I)
# 批471(真報告逼出來的):`upside_calc = TP/價 - 1` 是**純股價**報酬,
# 而 v0120 的 UPS_RX 第一個選擇就是 `Expected total return`——**含息總報酬**。
# Citi-3231 首頁逐字印著:
#     Price NT$114.00 · Target price NT$165.00
#     Expected share price return 44.7%      ← (165/114-1)=44.74%,就是它
#     Expected dividend yield 3.3%
#     Expected total return 48.1%            ← 44.7 + 3.3,v0120 抓的是這個
# 報告一個字都沒錯,是我們拿兩個**不同指標**去對,判成 FORMULA_MISMATCH。
# 「名字像不等於語意像」——Upside 這個詞底下有兩種完全不同的數。
# 更糟的是本檔自測第 ③ 檢**把這個錯釘成了規格**(「48.1 vs 44.7=FORMULA_MISMATCH
# 誠實列示」),所以它不但沒被抓到,還被保護了三十幾批。檢釘錯了,比沒有檢更難救。
#
# 判法(次序有意義,先要可直接比的那一個):
#   ① 股價報酬 share price return  → 與 upc 同語意,直接比
#   ② 泛稱 Upside / 上漲空間        → 沿用舊行為
#   ③ 總報酬 total return          → 與 upc **不同語意**;報告自己印了殖利率的話,
#                                    就用報告自己的加法 upc + yield 去比(零發明)
UPS_PRICE_RX = re.compile(
    r"(?:Expected\s*)?share\s*price\s*return|股價報酬(?:率)?|價格報酬(?:率)?", re.I)
UPS_TOTAL_RX = re.compile(
    r"(?:Expected\s*)?total\s*return|總報酬(?:率)?|整體報酬(?:率)?", re.I)
_PCT_TAIL = r"[^\d\-]{0,15}(-?[\d.]+)\s*%"
# **括號不可省**(批471 自審修):`a|b|c` 直接接尾段,`|` 是最外層,
# 尾段只會黏到最後一個選項上——Citi 那句 `Expected share price return 44.7%`
# 因此一個都不命中,upr 回 None。拼 pattern 時一定要先包成 (?:…)。
UPS_PRICE_FULL = re.compile("(?:" + UPS_PRICE_RX.pattern + ")" + _PCT_TAIL, re.I)
UPS_TOTAL_FULL = re.compile("(?:" + UPS_TOTAL_RX.pattern + ")" + _PCT_TAIL, re.I)
#: 泛稱(不含 total return——那一支獨立走 ③)
UPS_RX = re.compile(r"(?:上漲空間|Upside|漲跌空間)" + _PCT_TAIL, re.I)
YLD_RX = re.compile(r"(?:dividend\s*yield|殖利率)[^\d]{0,15}([\d.]+)\s*%", re.I)
EPS_RX = re.compile(r"(20\d{2}|1[01]\d)\s*[EFA]?\s*(?:年)?\s*"
                    r"(?:Diluted\s+)?EPS[^\d\-]{0,15}(-?[\d,]+(?:\.\d+)?)", re.I)
# 批466 邊界律(真檔實測):`(?<!\d)(\d{4})(?!\d)` 只擋相鄰**數字**,不擋
# 相鄰字母,於是上傳雜湊 `1379b53b-…` 的 1379 照樣被當代號——而 1379 益缶
# 真的在冊上,名冊對帳擋不住這種。左邊須為邊界;右邊須為邊界,或**已知市場
# 後綴**(TT/TW/TWO/T)再接邊界。這樣 3014TT / 2330.TW 照舊認得(批420 那一課),
# 1379b53b / ab2330cd 不再誤收。首頁引擎 v0124 是同一條律的正主,本式是橋缺席退路。
TICK_RX = re.compile(r"(?<![A-Za-z0-9])(\d{4})(?:TWO|TT|TW|T)?(?![A-Za-z0-9])")


_TP_CACHE: list = []          # 批243:單例快取(避免逐呼重讀 lexicon)


# 批421(操作員令「REGISTER AND IMPLEMENT THESE TWO SYSTEMS AS SUPPORTIVE
# MODULES TO SUPPORT VRN」):NLP 掛載改走支援模組正主 SUP_MDL744_NLPApplicationHub。
# 修的是 v0113 以前的真缺陷——這裡把收容夾**寫死**成 VIA_NLP_OneEngine_v1.1.0
# (只有 18 支模組),而庫裡早有 v1.5.0、批421 又收容了 v1.8.0(39 支)。
# 寫死路徑=尾版律破口,且破在最痛處:table_ops/layout_analysis 這些
# 研報解讀要用的模組 v1.1.0 全缺。
# 零回歸律:橋缺席或掛載失敗 → 原樣退回 v1.1.0 直掛,再退 stdlib NFKC。
# 三段皆留因由,run 尾段印出來(捕捉到卻不顯示=等於沒捕捉)。
NLP_HUB_DIR = VIA / "supportive modules" / "70_VRN_Rules"
_NLPHUB = {"mod": None, "why": "", "tried": False, "src": ""}


def nlp_hub():
    """SUP_MDL744 統轄橋(尾版律 glob);缺檔或掛載失敗=誠實回 None 與因由"""
    if _NLPHUB["tried"]:
        return _NLPHUB["mod"]
    _NLPHUB["tried"] = True
    try:
        hits = sorted(NLP_HUB_DIR.glob("SUP_MDL744_NLPApplicationHub_v*.py"))
        if not hits:
            _NLPHUB["why"] = ("SUP_MDL744 缺檔"
                              "(supportive modules/70_VRN_Rules/)")
            return None
        import importlib.util
        spec = importlib.util.spec_from_file_location("via_nlp_hub_dyn", hits[-1])
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod          # 同 fin_ssot:延後註解要靠這行
        spec.loader.exec_module(mod)
        st = mod.mount()
        if st["state"] in ("ABSENT", "FAILED"):
            _NLPHUB["why"] = f"橋在位但掛載 {st['state']}:{st.get('why', '')}"
            return None
        _NLPHUB["mod"] = mod
        _NLPHUB["src"] = f"{hits[-1].name} → {st.get('dir_name')}({st['state']})"
        return mod
    except Exception as exc:
        _NLPHUB["why"] = f"橋載入失敗 {type(exc).__name__}:{str(exc)[:80]}"
    return None


def _nfkc(s: str) -> str:
    """正規化三段誠實退路:① SUP_MDL744 橋(尾版 v1.8.0 TextProcessor)
    ② 收容件 v1.1.0 直掛(v0104 起的原行為,零回歸)③ stdlib NFKC。"""
    if not _TP_CACHE:
        h = nlp_hub()
        if h is not None:
            tp = h.text_processor()
            if tp is not None:
                _TP_CACHE.append(tp)
                _NLPHUB["route"] = "HUB"
        if not _TP_CACHE:                      # ② 原路退回(不動舊行為)
            try:
                pkg = HERE / "references" / "intake" / "VIA_NLP_OneEngine_v1.1.0"
                sys.path.insert(0, str(pkg / "src"))
                from via_nlp_engine.text_ops import TextProcessor  # noqa
                lex = pkg / "data" / "lexicon" / "ssot_lexicon.json"
                _TP_CACHE.append(TextProcessor(lex) if lex.exists() else None)
                _NLPHUB["route"] = "LEGACY_v1.1.0"
            except Exception:
                _TP_CACHE.append(None)
                _NLPHUB["route"] = "STDLIB"
    tp = _TP_CACHE[0]
    if tp is not None:
        try:
            return tp.normalize(s)
        except Exception:
            pass
    return unicodedata.normalize("NFKC", s)


def nlp_stats() -> dict:
    """NLP 掛載現況(給 run 尾段顯示;不顯示等於沒捕捉)"""
    h = nlp_hub()
    st = h.mount() if h is not None else {}
    return {"route": _NLPHUB.get("route", "(未用)"),
            "src": _NLPHUB.get("src", ""),
            "why": _NLPHUB.get("why", ""),
            "hub_state": st.get("state", ""),
            "hub_dir": st.get("dir_name", ""),
            "services": (h.capability_delta().get("report_services_present", [])
                         if h is not None else [])}


# ===== 批420:檔名拆解律 + 評等全名冊(操作員規格) ======================
# 操作員規格逐字:
#   「FILENAME 拆解方式就是中英文標點符號轉換處切開來,TRIM 過便成為獨立連續的
#     英文/中文/數字的單位。四碼數字是台股的 TICKER,較長的數字為日期。
#     TICKER 去 TWSE/TPEX 找名稱。名字-KY 也是公司名稱。3014TT 是 3014 TT。」
#   「RATING_LIST=() 所有評等中英文名稱,第一頁符合即可。」
#
# 先前是三支各管一段的 regex(TICK_RX 掃裸四碼、parse_date 三種寫法、parse_broker
# 拿字典做子字串掃),彼此不知道對方切到哪裡。`3014TT` 這種**沒有標點、只有字集
# 轉換**的寫法就是它們的共同盲點。改成一支具名的拆解器,三段都吃它的結果。

# 標點:ASCII 與全形一併收(操作員說的「中英文標點」)
_PUNCT_RX = re.compile(
    r"[\s\-_()\[\]{}<>|/\\,.;:!?'\"~+*=@#$%^&"
    r"（）〔〕【】｛｝《》〈〉「」『』,、。;:!?、·…‧－―—～　]+")
# 字集轉換處:數字 / 英文 / 中日韓 各自成段(3014TT → 3014 + TT)
_UNIT_RX = re.compile(r"[0-9]+|[A-Za-z]+|[\u3400-\u4dbf\u4e00-\u9fff]+")
_MARKET_TOKENS = {"TT", "TW", "TWO", "TPE", "TWSE", "TPEX", "OTC"}
ACTIVE_TICKER_RX = re.compile(r"^\d{4}$")


def tokenize_filename(stem: str) -> dict:
    """檔名拆解(操作員規格)。回:
      tokens         逐單位(已 TRIM,英/中/數各自連續)
      digits/latin/cjk  依字集分堆
      ticker_cands   四碼數字=台股代號候選(依出現序)
      date_cands     較長的數字=日期候選(6/7/8 碼)
      market         TT/TW/TWO… 市場後綴(有就記,不當代號也不當日期)
      name_cands     公司名候選;中文段落與其「-KY」合體都收
                     (操作員:「名字-KY 也是公司名稱」)
    純字串處理,零 I/O:名冊查驗仍在 extract_one,這裡只負責切得對。"""
    raw = _nfkc(str(stem or ""))
    tokens: list = []
    for part in _PUNCT_RX.split(raw):
        part = part.strip()
        if part:
            tokens += _UNIT_RX.findall(part)
    digits = [t for t in tokens if t.isdigit()]
    latin = [t for t in tokens if t.isascii() and t.isalpha()]
    cjk = [t for t in tokens if not t.isascii()]
    market = next((t.upper() for t in latin if t.upper() in _MARKET_TOKENS), "")
    ticker_cands = [t for t in digits if ACTIVE_TICKER_RX.match(t)]
    date_cands = [t for t in digits if len(t) > 4]
    # 「名字-KY」:原字串裡中文段後面緊跟 -KY 就合體收進候選(兩種都留,交給名冊決定)
    name_cands: list = []
    for c in cjk:
        name_cands.append(c)
        if re.search(re.escape(c) + r"\s*[-‐－]\s*(?:KY|ky|Ky)", raw):
            name_cands.append(c + "-KY")
    for l in latin:                       # AMAX-KY 這種純英文公司名也收
        if re.search(re.escape(l) + r"\s*[-‐－]\s*(?:KY|ky|Ky)", raw):
            name_cands.append(l + "-KY")
    return {"tokens": tokens, "digits": digits, "latin": latin, "cjk": cjk,
            "market": market, "ticker_cands": ticker_cands, "date_cands": date_cands,
            "name_cands": name_cands}


# 評等全名冊(操作員:「RATING_LIST=() 所有評等中英文名稱,第一頁符合即可」)。
# 這是**掃描詞表**,不是判定表——判定仍走正典/疊加層 resolve_rating,
# 認不出就是認不出(Zero-Hydra:本器不自建第二份「詞→鍵」對照)。
RATING_LIST: tuple = (
    # 英文
    "Strong Buy", "Aggressive Buy", "Active Buy", "Recommended Buy", "Conviction Buy",
    "Buy", "Add", "Accumulate", "Overweight", "Outperform", "Strong Outperform",
    "Long", "Positive", "Attractive",
    "Hold", "Neutral", "Market Perform", "Market Weight", "Sector Weight", "Equal Weight",
    "In Line", "Maintain", "Fair Value", "Wait and see", "Peer Perform",
    "Sell", "Reduce", "Underweight", "Underperform", "Short", "Trim", "Lighten",
    "Avoid", "Below Market", "Downgrade", "Negative", "Sector Underperform",
    "Not Rated", "No Rating", "Not Covered", "No Recommendation", "No Opinion",
    "Not Available", "Coverage Dropped", "Under Review", "Restricted", "Suspended",
    "NR", "N/A", "N.A.",
    # 中文
    "強力買進", "積極買進", "強烈推薦", "極力推薦", "強力推薦", "優先買進", "值得買進",
    "建議買進", "推薦買進", "買進評等", "逢低買進", "逢低加碼",
    "買進", "推薦", "增持", "加碼", "超配", "優於大盤", "看好",
    "中立", "持有", "區間操作", "觀望", "續抱", "維持", "平衡", "持平", "符合大盤",
    "標準配置", "中立評等", "持有評等", "觀望評等",
    "賣出", "減持", "減碼", "低配", "劣於大盤", "建議賣出", "建議減碼", "賣出評等",
    "不推薦", "下調", "避險", "轉弱", "看壞",
    "未評等", "未評級", "尚未評級", "暫無評等", "暫不評等", "不予評等",
    "無覆蓋", "無研究覆蓋", "無評等", "待覆蓋",
)


# ===== [VIA:COMMONUTILS-BRIDGE:v0100] VRN 共用小工具正典橋(批594;正典 SUP_MDL753)=====
# 本處原本的行為:逗號千分位 → float / None
# 批594 量過:VRN 尾版 170 支 · 定義 68 處 · **18 個行為群**(全部在模組層)。
# 差異是真的:`_cel_submit` 兩群差在「有沒有第二層退路」;`_si` 有一群用 **bare `except:`**
# (連 SystemExit 都吞——**那是潛在缺陷不是風格**,正典給選項等價遷移,不代改 LL90);
# `_jwrite` 三群差在 mkdir / default / 吞不吞例外,而且**底下直接接批592 的 SUP_MDL752**,
# 不另造一支 JSON 寫法。綁定不是 def(寫 def 家族數不會掉,LL143);
# 可變預設值由正典 `_fresh()` 保證每次新的一份(L76)。
import importlib.util as _cu_ilu
from pathlib import Path as _cu_Path
_CU_MOD = None
_cu_p = _cu_Path(__file__).resolve()
while _cu_p.parent != _cu_p:
    _cu_hits = sorted((_cu_p / "supportive modules").glob("SUP_MDL753_VIACommonUtils_v*.py"))
    if _cu_hits:
        _cu_spec = _cu_ilu.spec_from_file_location("VIA_COMMONUTILS", _cu_hits[-1])
        _CU_MOD = _cu_ilu.module_from_spec(_cu_spec)
        _cu_spec.loader.exec_module(_CU_MOD)
        break
    _cu_p = _cu_p.parent
if _CU_MOD is None:
    raise RuntimeError("[FAIL] 共用小工具正典缺席:supportive modules/SUP_MDL753_VIACommonUtils_v*.py")
_num = _CU_MOD.num
# ===== [VIA:COMMONUTILS-BRIDGE:END] =====


def date_from_token(tok: str) -> str:
    """把「較長的數字」單位轉成日期(操作員規格)。認得三種寫法:
    8 碼 20251202 · 7 碼民國 1141202 · 6 碼 251209。不合=空(不猜)。"""
    t = str(tok or "")
    if len(t) == 8 and t.startswith("20"):
        return f"{t[:4]}-{t[4:6]}-{t[6:]}"
    if len(t) == 7 and t[:3].isdigit() and 100 <= int(t[:3]) <= 199:
        return f"{int(t[:3]) + 1911}-{t[3:5]}-{t[5:]}"
    if len(t) == 6 and 23 <= int(t[:2]) <= 39:
        return f"20{t[:2]}-{t[2:4]}-{t[4:]}"
    return ""


def parse_date(name: str) -> str:
    """回 `YYYY-MM-DD`;抽不到回空字串(不猜)。

    批628:**先問規則樞紐**(SUP_MDL749 冊上十二式:純數字三式 / 帶分隔 / 中文 /
    民國字樣 / 年月 / 只有年 / 英文月),樞紐缺席或抽不到才走本檔原本那三道
    ——零回歸,只增不減。

    只收 `gran == "DAY"`:年月或只有年是誠實的,但**不是報告日**。
    把 `2025年12月` 補成 `2025-12-01` 是捏造一天出來,寧可留空。
    """
    _h628 = rule_hub()
    if _h628 is not None and hasattr(_h628, "parse_date_any"):
        try:
            _r628 = _h628.parse_date_any(name) or {}
        except Exception:
            _r628 = {}
        if _r628.get("gran") == "DAY" and _r628.get("iso"):
            return _r628["iso"]
    # 批420:先走拆解器的「較長的數字」候選(操作員規格);不中才退回原三道 regex
    for tok in tokenize_filename(name)["date_cands"]:
        d = date_from_token(tok)
        if d:
            return d
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
    # 批442/443:檔名層與目標價都以首頁全能引擎的公開契約為準(邏輯一致化)。
    # 橋在函式最前面取,因為目標價那一段就要用到它——批443 初版放在後面,
    # 直接 UnboundLocalError。
    _fe, _fwhy = _fn_bridge()
    _fn_src = _fwhy
    # 批558:補上 `footer`。原本這裡是 ("header","right","body")——**頁尾整區從來沒被搜過**,
    # 而本檔 1400 行附近的另一處 join 一直都有 footer(同一件事兩個定義,其中一個漏鍵)。
    # 擺在最後=既有命中的順序一位元不變(第一個命中仍先贏),只有「本來全空」的才會多找到。
    text_all = _nfkc("\n".join(str(zones.get(k, ""))
                               for k in ("header", "right", "body", "footer")))
    right = _nfkc(str(zones.get("right", "")))
    # 批239b(操作員令「文字修復後可抓目標價」):斷行修復版=標籤與
    # 數值被換行切開(Target↵price↵NT$165)之救回文本;raw 優先、修復版後備
    right_rep = re.sub(r"\s*\n\s*", " ", right)
    text_rep = re.sub(r"\s*\n\s*", " ", text_all)
    # 批558 操作員令的兩區(都是**修復後**的):
    #   info_z = 第一頁周圍訊息區塊(頁首帶/右資訊區/頁尾)
    #   head_z = 中間本文標題區(章節標題行)
    # 偵測實作向樞紐要(Zero-Hydra);樞紐缺=兩區誠實留空,行為退回 v0128。
    info_z, head_z = zone_blocks(zones)
    # 批238②:候選逐驗官方名冊;全不在=誠實空(研討會/晨報非個股)
    ticker = ""
    yr_rejects = []
    dspans = _date_spans(stem)            # 批418:年份守衛用
    # 批420:四碼數字=台股 TICKER(操作員規格)。拆解器已把 3014TT 切成 3014+TT,
    # 所以「沒有標點、只有字集轉換」的寫法也切得開;年份守衛照舊在下面把關。
    _tk = tokenize_filename(stem)
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
    if not ticker:
        # 批420:代號抽不到時,用「名字/名字-KY」反查名冊(操作員:名字-KY 也是公司名稱)
        _rev = {str(v): k for k, v in (names or {}).items() if v}
        for _nc in _tk["name_cands"]:
            if _nc in _rev:
                ticker, name_official = _rev[_nc], _nc
                conflicts_year = (conflicts_year + ";" if conflicts_year else "") + f"TICKER_FROM_NAME={_nc}"
                break
    tick_z = TICK_RX.search(text_all)
    conflicts = []
    if conflicts_year:
        conflicts.append(conflicts_year)
    if ticker and tick_z and tick_z.group(1) != ticker \
            and names.get(tick_z.group(1)):
        conflicts.append(f"TICKER_ZONE={tick_z.group(1)}(KEEP_BOTH)")
    if name_official and name_official not in text_all:
        conflicts.append("NAME_NOT_IN_PAGE(KEEP_BOTH)")
    rat = (RATING_RX.search(right) or RATING_RX.search(text_all)
           # 批558:同律,接在後面(既有命中不受影響)
           or RATING_RX.search(info_z) or RATING_RX.search(head_z))
    tp = (TP_RX.search(right) or TP_RX.search(right_rep)
          or TP_RX.search(text_all) or TP_RX.search(text_rep)
          # 批558:既有四道全落空,才輪到周圍訊息區塊與本文標題區(純增量)
          or TP_RX.search(info_z) or TP_RX.search(head_z))
    def _first(rx):
        for t in (right, right_rep, text_all, text_rep):
            m = rx.search(t)
            if m:
                return m
        return None

    # 批471:先找**與 upside_calc 同語意**的那一個(股價報酬),
    # 再泛稱,最後才是總報酬(含息,語意不同,要另外換算才比得了)
    ups, ups_basis = _first(UPS_PRICE_FULL), "股價報酬"
    if ups is None:
        ups, ups_basis = _first(UPS_RX), "升幅(泛稱)"
    if ups is None:
        ups, ups_basis = _first(UPS_TOTAL_FULL), "總報酬(含息)"
    if ups is None:
        ups_basis = ""
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
    # 批472:帶幣別記號的目標價候選排前面(與 px_c 同律;舊式候選全數保留在後)
    tp_c = _cands(TP_CUR_RX, right, right_rep, text_all, text_rep)
    for _v in _cands(TP_RX, right, right_rep, text_all, text_rep, info_z, head_z):
        if _v not in tp_c:
            tp_c.append(_v)
    # 批471:**帶幣別記號的候選排在前面**。配對律是「取首對」,所以次序就是優先序;
    # 舊式候選仍全部保留在後面(只增不減,涵蓋不變),只是不再排在真價格前面。
    px_c = _cands(PX_CUR_RX, right, right_rep, text_all, text_rep)
    for _v in _cands(PX_RX, right, right_rep, text_all, text_rep):
        if _v not in px_c:
            px_c.append(_v)
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
    # 批443:目標價也以**首頁全能引擎**為準(邏輯一致化的第二塊)。
    # 工作站實錄,本檔自己抽的值錯得有系統,而首頁引擎同一份都抽對:
    #   中信金 59.0(那是**前次**目標價,本次 63) · MS-2308 38.0(對 1288)
    #   JP-3653 26.0(對 2470) · MS-8210 18.0(對 730)
    # 本檔沒有批429–437 的六道剔除律與文內自洽仲裁,補不完也不該補——
    # 那是第二套實作。綁契約:同一份報告兩支引擎必須給同一個目標價。
    if _fe is not None:
        try:
            _tp_fp = _fe.fv.extract_target_price(text_rep or text_all, ticker=ticker or None)
            _px_pre = _fe.fv.doc_close(text_rep or text_all)
            # ── 批447:契約給的是**一對**,就整對一起收 ─────────────────────
            # 工作站實錄(批446 之後鏈終於跑完整):MS-2308 入庫仍是 TP=38 P=28、
            # JP-3653 仍是 26/60、MS-8210 仍是 18/7 —— 批445 修對的 1288/932、
            # 3650/2470、730/621 一個都沒進來。
            #
            # 根因是底下兩道守衛**互相擋住對方**:新目標價拿**舊現價**去比、
            # 新現價再拿**舊目標價**去比。而這三份的舊值剛好「一起錯得自洽」:
            #     MS-2308  38/28  = 1.36   ← 落在合理帶 0.30–3.2 之內
            #     JP-3653  26/60  = 0.43   ← 也在帶內
            #     MS-8210  18/7   = 2.57   ← 也在帶內
            # 於是 1288÷28=46 判「荒謬」踢掉、932 再拿 38÷932=0.04 判「荒謬」踢掉,
            # **一對錯的值互相作證,把一對對的值擋在門外**。
            #
            # 批239 的配對律沒有錯,錯在拿它去比**混搭的一對**。契約兩個值來自
            # 同一支引擎、同一份文本,本來就該當成一對驗:自己跟自己比得過就整對換。
            _pair_ok = (_tp_fp is not None and _px_pre is not None
                        and _px_pre > 0 and 0.30 <= _tp_fp / _px_pre <= 3.2
                        and _tp_fp != _px_pre)
            if _pair_ok and (_tp_fp != tpv or _px_pre != pxv):
                _fn_src += (f";目標價/現價整對換 {tpv if tpv is not None else '-'}/"
                            f"{pxv if pxv is not None else '-'}→{_tp_fp}/{_px_pre}"
                            f"(首頁引擎;契約自洽比值 {_tp_fp / _px_pre:.2f})")
                tpv, pxv = _tp_fp, _px_pre
            elif _tp_fp is not None and _tp_fp != tpv:
                # 同理:契約的目標價也要過配對律——本檔已有可信現價時,
                # 比值荒謬的目標價不採用(JP-2330 的「PT Dec-25」就是這一型)。
                if pxv and not (0.30 <= _tp_fp / pxv <= 3.2):
                    _fn_src += f";目標價 {_tp_fp} 與現價 {pxv} 配對荒謬=不採用(寧缺勿假)"
                else:
                    _fn_src += (f";目標價 {tpv if tpv is not None else '-'}→{_tp_fp}"
                                "(首頁引擎)")
                    tpv = _tp_fp
            elif _tp_fp is None and tpv is not None:
                # 首頁引擎判「沒有目標價」而本檔抽到一個——**以首頁為準**。
                # 它有 n.a./前次/百分比/量級後綴六道剔除,本檔沒有;
                # 兩邊不一致時信有剔除律的那一邊,否則假值會進正本庫。
                _fn_src += f";目標價 {tpv}→無(首頁引擎判本報告未給目標價)"
                tpv = None
            # 現價同理。目標價綁對了而現價還是本檔自己抽的,比值就荒謬——
            # 實測中信金 63/19、MS-2308 1288/28、MS-8210 730/7 全被判 PARSE_SUSPECT:
            # **一半綁一半不綁比兩邊都不綁更糟**,因為它會把對的值標成可疑。
            # 首頁引擎的 doc_close 會先把日期挖掉再抓數字(批437),本檔沒有這一道。
            _px_fp = _px_pre
            # **契約給值,本檔的配對合理性律仍然當家**(批443 自審:檢 ⑬/⑮/⑱ 逼出來的)。
            # 批239 立的「TP/P 比值要落在 0.30–3.2,否則寧缺勿假」是本檔的正主知識;
            # 我綁契約時把它繞過去了,於是「目標價 367 元 / 收盤價 19」的 19
            # 被當成現價寫進庫(367÷19=19.3,荒謬),而舊碼本來會丟掉它。
            # 綁契約不等於把對方的守衛一起拆掉——那叫換一個錯,不叫一致化。
            if (not _pair_ok) and _px_fp is not None and _px_fp != pxv:
                if tpv and not (0.30 <= tpv / _px_fp <= 3.2):
                    _fn_src += f";現價 {_px_fp} 與目標價 {tpv} 配對荒謬=不採用(寧缺勿假)"
                else:
                    _fn_src += f";現價 {pxv if pxv is not None else '-'}→{_px_fp}(首頁引擎)"
                    pxv = _px_fp
        except Exception as exc:
            _fn_src += f";目標價/現價契約失敗 {type(exc).__name__}"
    # 目標價**等於**現價 ⇒ 同一個數被讀了兩次,其中一個抽錯(批443 自審,檢 ⑮ 逼出來)。
    # 「Price NT$1,130 / PT Dec-25」的目標價那一行只剩日期沒有數字,
    # 裸 NT$ 車道就把現價當成了目標價。券商給「目標價=現價」的報告實務上不存在。
    # 比的是**最終**的 tpv 與 pxv——初版拿契約的 _px_fp 去比,而這一例 doc_close
    # 回 None(它的現價寫成「Price NT$」不是「Price (日期)」),比了等於沒比。
    if tpv is not None and pxv is not None and tpv == pxv:
        _fn_src += f";目標價與現價同值 {tpv}=同一個數讀兩次,目標價不採用(寧缺勿假)"
        tpv = None
    upr = _num(ups.group(1)) if ups else None
    upc = round((tpv / pxv - 1) * 100, 1) if tpv and pxv else None
    # 批471:總報酬要換算成同語意才比得了——換算用的是**報告自己印的殖利率**,
    # 不是我們給的假設值。報告沒印殖利率就**不換算**,而且不判它是錯,
    # 誠實標成 BASIS_DIFF(兩個數都對,只是不同指標,沒有可比的基準)。
    _y = YLD_RX.search(right) or YLD_RX.search(text_all) or YLD_RX.search(text_rep)
    _yld = _num(_y.group(1)) if _y else None
    _cmp, _cmp_why = upc, ""
    if ups_basis == "總報酬(含息)" and upc is not None:
        if _yld is not None:
            _cmp = round(upc + _yld, 1)
            _cmp_why = f"總報酬對帳:股價 {upc}% + 報告殖利率 {_yld}% = {_cmp}%"
        else:
            _cmp, _cmp_why = None, "報告只印總報酬、沒印殖利率=無可比基準(不判錯)"
    if upc is not None and (abs(upc) > 150 or (tpv and pxv
            and (tpv / pxv > 8 or tpv / pxv < 0.15))):
        state = "PARSE_SUSPECT"           # 批238③:荒謬比例=誠實隔離
    elif upr is not None and _cmp is None and upc is not None:
        state = "BASIS_DIFF"              # 批471:指標不同義,兩邊都沒錯
    elif upr is not None and _cmp is not None:
        state = ("EXACT_MATCH" if abs(upr - _cmp) < 0.05 else
                 "ROUNDING_ONLY" if abs(upr - _cmp) <= 0.8 else
                 "FORMULA_MISMATCH")
        if _cmp_why:
            conflicts.append(_cmp_why)
    elif upc is not None or upr is not None:
        state = "SINGLE_SOURCE"
    else:
        state = "MISSING_SOURCE"
    body = str(zones.get("body", ""))
    sents = [x for x in re.split(r"(?<=[。.!?])\s+", body.replace("\n", " "))
             if len(x) > 15][:2]
    _kind, _kind_why = classify_kind(stem, ticker)   # 批418:分得出型別才判得出成敗
    _brk, _rdate = parse_broker(stem), parse_date(stem)
    # 批442:檔名層以**首頁全能引擎的公開契約**為準(邏輯一致化)。
    # 上面本檔原本的解析全部保留(橋缺席時照跑),但橋在位時以橋為準——
    # 兩個引擎對同一個檔名給不同答案,下游就永遠對不齊。
    if _fe is not None:
        try:
            _ff = _fe.filename_facts(stem)
            # 代號:橋查得到就用橋的(它走的是 1978 檔的名冊階梯);
            # 橋查不到而本檔查得到,**不硬蓋掉**——那是涵蓋差不是衝突。
            if _ff.get("ticker"):
                if _ff["ticker"] != ticker:
                    _fn_src += f";代號 {ticker or '-'}→{_ff['ticker']}"
                ticker = _ff["ticker"]
                if names.get(ticker):
                    name_official = names[ticker]
            # 官方證券名也走首頁引擎的**四階梯**(SSOT → VDF庫 → 離線冊 → MDL010);
            # 本檔原本只查 tw_listings(891 檔),所以 66 列 BASIC INFO 的
            # name_official 幾乎整片是空的——代號對了、名字還是沒有,不算正確。
            if ticker and not name_official:
                try:
                    _nr = _fe.nr.reconcile(ticker, _ff.get("name_hint"))
                    if _nr.get("official"):
                        name_official = _nr["official"]
                        _fn_src += f";官方名←{_nr.get('source') or '階梯'}"
                except Exception:
                    pass
            if _ff.get("kind"):
                if _ff["kind"] != _kind:
                    _fn_src += f";型別 {_kind or '-'}→{_ff['kind']}"
                _kind, _kind_why = _ff["kind"], (_ff.get("kind_reason") or "") + "(首頁引擎契約)"
            if _ff.get("broker"):
                _brk = _ff["broker"]
            if _ff.get("date"):
                _rdate = _ff["date"]
        except Exception as exc:
            _fn_src = f"契約呼叫失敗 {type(exc).__name__}:{str(exc)[:50]}=退本檔原檔名層"
    # 批471 **試過、量過、撤掉**(留紀錄,下一個人不必再試一次):
    # 我本來加了一道「非個股且零代號 → 不採計價與目標價」的閘,想擋掉 MS-Memory
    # 那個 DRAM 現貨報價 100.0。64 件真值基準 A/B 完的淨效果是**負的**:
    #   改善 2 件 —— 兆豐晨會 TP=4441(基準把代號當目標價)、MS-Memory P=45.5;
    #              但這兩件迴歸閘的 BASE_SUSPECT 已經各自接住了,閘是重複的。
    #   弄壞 1 件 —— **凱基投顧_鋼鐵產業 TP=20.3**,那是產業報告裡真的點到的目標價,
    #              與基準完全吻合,卻被閘一併丟掉。
    # 為了兩個別處已經接住的化妝分,弄丟一個真資料——不划算,而且違只增不減。
    # MS-Memory 的 100.0 留著:它是產業件、零代號,收尾閘判 DONE_NS,值不進判定。
    basic = {"report_file": stem, "ticker": ticker,
             "name_official": name_official,
             "broker": _brk, "report_date": _rdate,
             "rating_raw": rat.group(0) if rat else "",
             "target_price": tpv, "price": pxv,
             "upside_report": upr, "upside_calc": upc,
             "upside_state": state, "upside_basis": ups_basis,
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
        # 批466:`if tpv:` 看的是**值**,而 `tp.group(0)` 假設本檔 TP_RX 有命中。
        # 兩者可以不同源:批442 起目標價會由首頁引擎橋接管(`tpv = _tp_fp`),
        # 那時 tp 仍是 None → `tp.group(0)` 當場 AttributeError,而 run() 的
        # try 只包住 json 讀取,**整批入庫就死在那一份上**(實測:一份影像件
        # 讓 67 份的批次連「入庫計」都沒印出來)。raw_text 照實寫來源。
        mets.append({"report_file": stem, "metric": "target_price",
                     "period": basic["report_date"][:4], "status": "ESTIMATE",
                     "value": tpv,
                     "raw_text": (tp.group(0)[:80] if tp
                                  else "(首頁引擎綁定;本檔 TP_RX 未命中=無原文可引)")})
    y = YLD_RX.search(text_all) or YLD_RX.search(text_rep)
    if y:
        mets.append({"report_file": stem, "metric": "dividend_yield_pct",
                     "period": basic["report_date"][:4], "status": "ESTIMATE",
                     "value": _num(y.group(1)), "raw_text": y.group(0)[:80]})
    return basic, mets


#: 批659:**同一本庫裡,上市所的價不在 VRN 一直查的那張表。**
#:   量到的實況(容器 mega 庫):
#:       tw_daily_prices   鍵 ticker(`2330.TW` / `2330.TWO` 形)·   892 檔 · **只有上櫃 .TWO**
#:       tw_trading_daily  鍵 code(裸代號 `2330`)· 有 market 欄 TWSE/TPEx · **1,967 檔 · 含上市**
#:   81 份研報裡 42 份有代號有日有目標價,`tw_daily_prices` 一支都查不到——
#:   因為它們幾乎全是上市大型股(2330/2317/2454/2891/3008…),而那張表裡一檔上市都沒有。
#:   於是 VRN 的「上漲空間」**整欄零綠**,四批以來我一直在 VRN 這邊修尺、修字彙、追庫分歧,
#:   那一欄本來就不可能綠(LL293 的跨家族版:VDF 寫進 A 表,VRN 讀 B 表,兩邊都不報錯)。
#:   兩張表存的都是**原始 close**(批240 裁示 CLOSE 非 ADJ),所以第二車道不違裁示。
PRICE_LANES = (
    ("tw_daily_prices", "ticker", ("{t}.TW", "{t}.TWO", "{t}"), "上櫃價表(ticker 形)"),
    ("tw_trading_daily", "code", ("{t}",), "全所日成交表(code 裸碼;含上市 TWSE)"),
)


#: 批659:**「前一交易日」離報告日不能太遠,遠了就不是前一交易日,是舊價。**
#:   這道閘是這一批被自己的乾跑逼出來的。接上第二張表之後乾跑說「新拿到庫價 37 件」,
#:   看起來漂亮極了——逐件去看才發現:報告日 2025-08-19 / 2025-11-28 / 2026-05-19 / 2026-09-09,
#:   拿回來的 close **全部是 `2025-06-30` 那一天的**。
#:   因為 `tw_trading_daily` 裡上市所的 1,056 檔在 2025-06-30 就停了(上櫃 888 檔才到 2026-09-18)。
#:   批644 說的「TWSE 整所缺席」更精確的講法是:**上市所的價停在一年多前,之後沒有再抓。**
#:   沒有這道閘,那 37 筆會用一年前的價算出「合理」的升幅寫進庫,而且四項指標全部變好——
#:   **那才是真正的假綠**(判錯的紅燈和假綠一樣傷,而假綠更難被發現)。
#:   14 天:台股最長連假(農曆年)約 9–10 個日曆天,留一點餘裕;超過就是缺料不是有料。
PRICE_FRESH_DAYS = 14


def _prior_close(con, ticker: str, rdate: str):
    """報告日前一交易日原始 close(批240 裁示:CLOSE 非 ADJ)。
    批659 回 `(價, 出處)`——價從哪張表來、以及**為什麼沒有**,都要說得出來:

        ("", )               沒有代號或沒有報告日
        ("(查無此股)", )      兩張表都沒有這支
        ("(料過期:表名 日期)") 有這支,但最近一筆離報告日超過 PRICE_FRESH_DAYS 天
                              → **這是缺料,不是有料**;要補的是 VDF 的價(`via-price`,要網路同意閘)
        (表名, )             有且新鮮

    另修一個安靜的 bug:舊碼的 `except Exception: return None` 擺在迴圈裡,
    **第一個代號變體一出例外就整個放棄**,後面兩個變體根本沒試到;
    現在是「這張表不合用就換下一張」,不是「查一次不中就收工」。"""
    if not ticker or not rdate:
        return None, ""
    stale = ""
    for tbl, col, forms, _why in PRICE_LANES:
        for f in forms:
            t = f.format(t=ticker)
            try:
                r = con.execute(
                    f'SELECT date, close FROM "{tbl}" WHERE "{col}"=? AND date<? '
                    "ORDER BY date DESC LIMIT 1", [t, rdate]).fetchone()
            except Exception:
                break                      # 表不在/欄不對 → 換下一張車道(不是整個放棄)
            if not (r and r[1]):
                continue
            gap = _days_between(str(r[0]), str(rdate))
            if gap is not None and gap > PRICE_FRESH_DAYS:
                stale = stale or f"(料過期:{tbl} {r[0]} 距報告日 {gap} 天)"
                continue                   # 舊價不拿來充數,繼續找別張表有沒有新的
            return float(r[1]), tbl
    return None, (stale or "(查無此股)")


def _days_between(d1: str, d2: str):
    """兩個 YYYY-MM-DD 相差幾個日曆天;解析不了就回 None(解析不了不當成過期,也不當成新鮮)"""
    import datetime as _dt
    try:
        a = _dt.date.fromisoformat(d1[:10])
        b = _dt.date.fromisoformat(d2[:10])
    except Exception:
        return None
    return abs((b - a).days)


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


def rating_vocab(m) -> list:
    """疊加層自己的評等別名詞表(長詞先試,避免「買進」先咬掉「強力買進」)。
    批419g:抽取器的詞表比正規化器窄——批413 把 59 條別名(增持/加碼/續抱/低配/
    區間操作/未評等…)加進疊加層,但 RATING_RX 只認 8 個英文字加 7 個中文詞,
    掃不到的詞正規化器永遠看不到。**字典已經有了就別再寫第二份詞表**(Zero-Hydra),
    直接拿疊加層的別名當掃描詞表。"""
    try:
        ov = m.overlay() if hasattr(m, "overlay") else {}
        vocab = {a for aliases in (ov.get("rating_alias_add") or {}).values() for a in aliases}
        vocab |= set((ov.get("rating_alias_add") or {}).keys())
    except Exception:
        return []
    vocab |= set(RATING_LIST)          # 批420:操作員給的評等全名冊一併納入掃描詞表
    # 只收 ≥2 字的詞:單字太容易在內文亂咬(「買」「空」)
    return sorted((w for w in vocab if len(str(w)) >= 2), key=lambda w: -len(str(w)))


RATING_HEAD_LINES = 40      # 批554:與 ENG086 正本實作同一個數字(本土尺度只看前 N 行)


def _rating_three(m, raw: str, text: str, stem: str, zone_top: str,
                  head_zone: str = "", skip_vocab: bool = False,
                  only_vocab: bool = False) -> dict:
    """評等前三道(v0127 既有;抽成獨立函式是為了讓自測能拿**真的舊路徑**當對照組)。

    批554 第二道加守衛(這是量出來的真迴歸,不是我新造的假想):
      v0127 的第二道拿 RATING_RX 掃**全文**且沒有線索詞要求,
      於是本文第 47 行的 `Management will add capacity in 2H26 and hold inventory flat.`
      被判成 HOLD——這正是 LL68 那一型假評等,只是它一直住在本器自己的第二道裡,
      在批554 之前沒有任何一檢在量它。改成**只掃前 40 行**(頁首帶/右區與本文起頭),
      本文深處交給第四道的樞紐——那一側有線索詞/整行等於的守衛,才敢看。
      寧缺勿假:第四道缺席時這一道也不放寬回去(假綠與判錯的紅燈一樣傷)。
    """
    r = {"key": ""} if only_vocab else m.resolve_rating((raw or "").strip())
    if only_vocab:
        pass
    elif not r.get("key"):
        # 第二道的乾草堆(批558 改):掃**真正的分區**——周圍訊息區塊 + 中間本文標題區。
        # 批554 我寫的是「全文前 40 行」,那是**分區的代理,不是分區本身**;
        # 本批的負向對照當場打穿它:夾具整份不到 40 行,於是本文第 5 行的
        # 「外資持有比重上升」照樣落在窗內,被判成 HOLD——LL68 那型假評等又回來了。
        # 代理會在「文件比窗短」的時候失效,而短文件正是研報最常見的形狀。
        # 呼叫端沒給分區時(舊呼叫者)才退回前 40 行,行為與 v0128 相同(誠實退路)。
        _zoned = f"{zone_top or ''}\n{head_zone or ''}".strip()
        head = _zoned or "\n".join((text or "").splitlines()[:RATING_HEAD_LINES])
        for w in RATING_RX.findall(head)[:8]:
            w = w if isinstance(w, str) else (w[0] if w else "")
            if w and m.resolve_rating(w).get("key"):
                r = m.resolve_rating(w)
                break
    if not r.get("key") and not skip_vocab:
        # 批419g 第三道:疊加層別名詞表 × 標題帶/右區 + 檔名(範圍收得緊)
        hay = f"{zone_top or ''}\n{stem or ''}\n{head_zone or ''}"
        if hay.strip():
            for w in rating_vocab(m):
                if w in hay:
                    h3 = m.resolve_rating(w)
                    if h3.get("key"):
                        r = h3
                        break
    return r


_HUB = {"mod": None, "why": "", "tried": False}


def rule_hub():
    """向 **VRN 規則樞紐 SUP_MDL749** 要判定**實作**(不是只要詞表)。

    批554 操作員令「評等以同義字為主」。同義字有正本冊(VRN_FieldRules_SSOT),
    但把那 38 個詞再抄一份進本器,就是第二顆會各自漂移的頭(Zero-Hydra 明令禁)。
    更要命的是:批540 量過——**光補詞彙不補守衛會製造假評等**(內文的「外資持有比重」
    含「持有」、「增持庫藏股」含「增持」)。樞紐轉交的是 ENG086 在 64 份真研報上
    打出來的那一整套(本土尺度只看前段 · 引號 · 標題行 · 線索詞/整行等於),
    守衛與詞表一起繼承,才敢放它看本文。
    惰性:不用到就不載;缺=誠實 None(呼叫端退回既有三道,行為零變更)。
    """
    if not _HUB["tried"]:
        _HUB["tried"] = True
        try:
            hits = sorted((VIA / "supportive modules" / "70_VRN_Rules").glob(
                "SUP_MDL749_VRNFieldRuleHub_v*.py"))          # 尾版 glob,不釘版號(L54)
            if not hits:
                _HUB["why"] = "規則樞紐缺:supportive modules/70_VRN_Rules/SUP_MDL749_VRNFieldRuleHub_v*.py"
            else:
                import importlib.util as _il
                sp = _il.spec_from_file_location("_vrn_rule_hub_e73", hits[-1])
                mod = _il.module_from_spec(sp)
                sp.loader.exec_module(mod)
                _HUB["mod"], _HUB["why"] = mod, f"規則樞紐 {hits[-1].name}"
        except Exception as exc:
            _HUB["why"] = f"規則樞紐載不動:{type(exc).__name__}: {str(exc)[:80]}"
    return _HUB["mod"], _HUB["why"]


def zone_blocks(zones: dict) -> tuple:
    """批558 操作員令的兩區,都**修復後**才回:
      ① 第一頁周圍訊息區塊 = 頁首帶 + 右資訊區 + **頁尾**
      ② 中間本文標題區     = 本文裡的章節標題行

    偵測實作**向樞紐要**(`info_block` / `headings`),不在本器自寫一份——
    之後接 首頁全能 與 TW02 時要拿同一份;四支各寫一份標題偵測就是四個會漂的真相。
    樞紐缺=兩區誠實回空字串,呼叫端的搜尋序自然退回 v0128(零行為變更,不編)。
    """
    hub, _w = rule_hub()
    if hub is None or not zones:
        return "", ""
    try:
        return hub.info_block(zones), hub.headings(str(zones.get("body", "") or ""))
    except Exception as exc:
        _FIN["why"] = _FIN["why"] or f"樞紐分區例外 {type(exc).__name__}:{str(exc)[:60]}"
        return "", ""


def hub_rating(m, stem: str, zone_top: str, text: str) -> dict:
    """第四道:樞紐判評等 → 回本器 SSOT 的 {key,code,direction,actionable};判不出=空殼。

    先窄後寬(**窄的先贏**,與前三道同律):
      ① 頁首帶 + 檔名的**斷行修復版**——「評等↵增加持股」被換行切開時,
         線索詞道原本吃不到(批239b 操作員令「文字修復後可抓」,當時只修了目標價)。
      ② 本文——批554 操作員令「本文修復後本文也可擷取到評等同義字」。
         放它看本文的**前提**是守衛在樞紐那一側(見 rule_hub 說明),不是我這裡放行。
    正規化仍走本器既有的 SSOT(L30 一功能一主):先拿樞紐命中的原詞試,
    原詞是整句線索(「投資評等 accumulate」)時退而拿它的正典名(ADD)——
    這兩步都是**問本器自己的正典**,不是在這裡另立一張對映表。
    """
    hub, _hw = rule_hub()
    if hub is None:
        return {"key": "", "src": ""}
    _head = re.sub(r"\s*\n\s*", " ", f"{zone_top or ''}\n{stem or ''}").strip()
    for _hay, _zh in ((_head, "頁首帶+檔名(斷行修復)"), (text or "", "本文(樞紐守衛)")):
        if not _hay.strip():
            continue
        try:
            hit = hub.rating_of(_hay)
        except Exception as exc:
            _FIN["why"] = _FIN["why"] or f"樞紐評等例外 {type(exc).__name__}:{str(exc)[:60]}"
            return {"key": "", "src": ""}
        if not hit:
            continue
        for cand in ((hit.get("raw") or "").strip(), (hit.get("canonical") or "").strip()):
            if not cand:
                continue
            r = m.resolve_rating(cand)
            if r.get("key"):
                return {"key": r["key"], "code": r.get("code"),
                        "direction": r.get("direction", ""), "actionable": r.get("actionable"),
                        "src": f"樞紐·{_zh}·{hit.get('how') or ''}"}
    return {"key": "", "src": ""}


def ssot_rating(raw: str, text: str, stem: str = "", zone_top: str = "",
                head_zone: str = "") -> dict:
    """評等正規化 → {key, code, direction, actionable};認不出=全空。
    次序:raw(RATING_RX 抓到的)→ 內文 RATING_RX 逐詞 → 疊加層別名詞表掃
    「標題帶/右區 + 檔名」(批419g;這一道**只掃頁首帶與檔名,不掃全文**——
    本器自己沒有守衛,掃全文只會把內文敘述裡的『中立』當成評等)→
    **第四道:規則樞紐**(批554;它把守衛一起帶來了,所以這一道才敢看本文)。
    批558:第三/四道的乾草堆多收兩區——`zone_top` 由呼叫端改帶**含頁尾**的周圍訊息區塊,
    另加 `head_zone`(中間本文標題區)。兩區都接在既有之後,先命中的仍先贏=純增量。"""
    m = fin_ssot()
    if m is None:
        return {"key": "", "code": None, "direction": "", "actionable": None}
    try:
        # 批558 換序(這不是純增量,是**優先權修**,所以要講明白):
        #   舊序 ①raw ②分區 RATING_RX ③疊加層詞表**裸子字串**掃 ④樞紐實作
        #   新序 ①raw ②分區 RATING_RX ③**樞紐實作** ④疊加層詞表(降為最後手段)
        # 為什麼換:③ 是 `if w in hay` 的裸子字串比對,沒有詞界也沒有線索詞。
        # 本批負向對照量到:「【投資評等】維持增加持股」裡,疊加層把「維持」當 HOLD 別名,
        # 而更長、更對的「增加持股」在本器 SSOT 裡查不到 → **粗的那一道先贏,給出 HOLD**。
        # 「維持」在研報裡是**動詞**(維持增加持股=維持 BUY),不是評等本身。
        # 樞紐那一道是 64 份真研報驗過的實作,本來就該排在粗詞表前面——
        # 批554 我把它放最後,是因為當時只想「補漏不改判」,結果補了漏也留了錯。
        r = _rating_three(m, raw, text, stem, zone_top, head_zone, skip_vocab=True)
        if not r.get("key"):
            h4 = hub_rating(m, stem, f"{zone_top or ''}\n{head_zone or ''}", text)
            if h4.get("key"):
                return {"key": h4["key"], "code": h4.get("code"),
                        "direction": h4.get("direction", ""), "actionable": h4.get("actionable")}
        if not r.get("key"):
            r = _rating_three(m, raw, text, stem, zone_top, head_zone, only_vocab=True)
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
    for col in ("upside_basis VARCHAR",
                "price_db DOUBLE", "upside_db DOUBLE", "price_state VARCHAR",
                "price_src VARCHAR",        # 批659:庫價出自哪張表(只增不減,不動 price_state)
                # 批659 操作員裁示(L99 操作定義):ADJ 基準的上漲空間,六個新欄各自獨立,誰都不覆寫舊欄
                "adj_factor DOUBLE", "adj_factor_date VARCHAR", "target_price_adj DOUBLE",
                "price_latest_adj DOUBLE", "price_latest_date VARCHAR",
                "upside_adj DOUBLE", "upside_adj_state VARCHAR",
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


#: 自測夾具的 report_file(批442:它們會混進正本庫的 BASIC INFO)
SELFTEST_STEMS = ("fx_report", "fx_twocol", "synthetic_financial_report",
                  "Citi-3231 20250604_fixture", "fx_basic")


def purge_selftest(apply: bool = False, db: Path | None = None) -> int:
    """把自測夾具從正本庫的 VRN 表裡清掉。

    批442:操作員令「自測試自修正 VRN 至 BASIC INFO 正確」。實跑發現 BASIC INFO
    69 列裡混著 fx_report / fx_twocol / synthetic_financial_report ——
    **我自己的自測夾具寫進了正本庫**。測試污染正本,那一段就不算正確。

    紀律與 ENG072 purge-selftest 同律:**預設只列不刪**,--apply 才真的動;
    刪的是我自己造的夾具列,不碰任何一列真報告。
    """
    import duckdb
    dbp = _resolve_db(Path(db) if db else None)
    if dbp is None:
        return 2
    con = duckdb.connect(str(dbp))
    tabs = [t for t in ("vrn_report_basic", "vrn_report_metrics", "vrn_report_financial",
                        "vrn_report_analyst", "vrn_report_crosscheck",
                        "vrn_four_point_digest")
            if t in {r[0] for r in con.execute("SHOW TABLES").fetchall()}]
    ph = ",".join("?" * len(SELFTEST_STEMS))
    tot = 0
    print(f"[fixture 清理] 正本庫 {dbp}")
    for t in tabs:
        n = con.execute(f'SELECT count(*) FROM "{t}" WHERE report_file IN ({ph})',
                        list(SELFTEST_STEMS)).fetchone()[0]
        if not n:
            continue
        tot += n
        print(f"  [{'刪除' if apply else '待刪'}] {t} · {n} 列")
        if apply:
            con.execute(f'DELETE FROM "{t}" WHERE report_file IN ({ph})',
                        list(SELFTEST_STEMS))
    if not tot:
        print("  乾淨:正本庫無自測夾具列")
    elif not apply:
        print("  (只列不刪;要真的刪請加 --apply——刪的只有上列夾具,不碰真報告)")
    con.close()
    return 0


#: 批659(操作員裁示,L99 的**操作定義**):
#:   「報告日前一日若過跟 ADJ CLOSE 不同,則應將目標價調成 ADJ,
#:     然後用最新的 ADJ CLOSE 跟更新後的目標價算上漲空間%」
#:
#:   因子 = adj_close(報告日前一日) / close(報告日前一日)
#:          ——不等於 1 就代表報告日之後除過權息;`tw_prices_adj.factor` 就是這個數(實測吻合到小數六位)
#:   目標價_adj = 目標價 × 因子          ——把券商當時的目標價搬到**今天的基準**
#:   上漲空間%  = (目標價_adj / 最新adj_close − 1) × 100
#:
#:   為什麼這條令解掉了死路:我原本一直在找「報告日附近的價」,卡在上市所的價停在 2025-06-30;
#:   但這個算法的分母是**最新** adj_close,不是報告日當時的價——問的是「從現在看還有多少空間」,
#:   那才是要的數字。報告日那天的價只用來算因子。
#:
#:   與批240 不衝突:`price_db` 是拿來**跟頁上的現價對質**的,那要 raw close(批240 裁示);
#:   上漲空間是**跨除權息的比值**,那要 ADJ。兩個用途、兩組欄,誰都不覆寫誰(只增不減)。
ADJ_RATIO_LO, ADJ_RATIO_HI = 0.2, 5.0        # 沿用批443 的荒謬比值守衛:目標價/現價 落在 0.2–5.0


def _adj_factor(con, ticker: str, rdate: str):
    """報告日前一交易日的 adj_close / close。回 (因子, 那天日期);算不出回 (None, "")。"""
    for sfx in (".TW", ".TWO", ""):
        t = f"{ticker}{sfx}"
        try:
            r = con.execute(
                "SELECT date, close, adj_close FROM tw_daily_prices WHERE ticker=? AND date<? "
                "AND close IS NOT NULL AND close<>0 AND adj_close IS NOT NULL "
                "ORDER BY date DESC LIMIT 1", [t, rdate]).fetchone()
        except Exception:
            return None, ""                   # 這張表不在=算不出,誠實回空(不編一個 1.0 出來)
        if r:
            return float(r[2]) / float(r[1]), str(r[0])
    return None, ""


def _latest_adj(con, ticker: str):
    """最新一筆 adj_close。回 (價, 日期);沒有回 (None, "")。"""
    for sfx in (".TW", ".TWO", ""):
        t = f"{ticker}{sfx}"
        try:
            r = con.execute(
                "SELECT date, adj_close FROM tw_daily_prices WHERE ticker=? AND adj_close IS NOT NULL "
                "ORDER BY date DESC LIMIT 1", [t]).fetchone()
        except Exception:
            return None, ""
        if r:
            return float(r[1]), str(r[0])
    return None, ""


def apply_adj_upside(con, basic: dict) -> dict:
    """批659 操作員裁示的上漲空間算法。只寫六個**新欄**,既有欄一個都不動。
    每一種算不出來都有自己的名字——「算不出」和「算出來是 0」必須分得開(L52 誠實態)。"""
    tk, rd, tp = basic.get("ticker"), basic.get("report_date"), basic.get("target_price")
    for k in ("adj_factor", "adj_factor_date", "target_price_adj",
              "price_latest_adj", "price_latest_date", "upside_adj"):
        basic[k] = None
    if not tk or not rd:
        basic["upside_adj_state"] = "ADJ_NO_KEY"
        return basic
    if tp is None:
        basic["upside_adj_state"] = "ADJ_NO_TARGET"
        return basic
    fac, fdate = _adj_factor(con, tk, rd)
    last, ldate = _latest_adj(con, tk)
    basic["adj_factor"], basic["adj_factor_date"] = fac, fdate
    basic["price_latest_adj"], basic["price_latest_date"] = last, ldate
    if fac is None:
        basic["upside_adj_state"] = "ADJ_NO_FACTOR"      # 報告日前一日沒有 adj/close(上市所整個沒有 adj 價)
        return basic
    if last is None or last == 0:
        basic["upside_adj_state"] = "ADJ_NO_LATEST"
        return basic
    tp_adj = round(tp * fac, 4)
    basic["target_price_adj"] = tp_adj
    ratio = tp_adj / last
    if not (ADJ_RATIO_LO <= ratio <= ADJ_RATIO_HI):
        # 批443 守衛:目標價/現價荒謬=其中一個抽錯(實測 3008 目標價被抽成 1.0 → 升幅 −100%)
        basic["upside_adj_state"] = f"ADJ_ABSURD(目標價adj {tp_adj} / 最新adj {last} = {ratio:.2f})"
        return basic
    basic["upside_adj"] = round((ratio - 1) * 100, 1)
    basic["upside_adj_state"] = "ADJ_OK" if abs(fac - 1) > 1e-6 else "ADJ_OK(因子1;報告日後未除權息)"
    return basic


def apply_db_price(con, basic: dict) -> dict:
    """批659:庫價 / 升幅 / `price_state` / `upside_state` 的**唯一算法**。
    `run`(重新擷取)與 `repair-price`(不擷取、只補庫欄)都走這一支——
    抄第二份的話,下次只改一邊就又是「同一本庫兩種答案」(批658 LL297 同族)。
    只動 price_db / price_src / upside_db / price_state / upside_state 五欄,別的一概不碰。"""
    pdb, pdb_src = _prior_close(con, basic.get("ticker"), basic.get("report_date"))
    tpv2 = basic.get("target_price")
    basic["price_db"] = pdb
    # 批659:出處走**新欄**。`price_state` 的字彙一個字都不動——
    #   supportive modules/ui_support 的 DataCatalog/InputConsole 兩張頁正在讀它,
    #   我上一次改產出端字彙、忘了尺那邊,整欄綠了 0 格(LL292)。
    basic["price_src"] = pdb_src
    basic["upside_db"] = round((tpv2 / pdb - 1) * 100, 1) if tpv2 and pdb else None
    if pdb is None:
        basic["price_state"] = "DB_NO_MATCH" if basic.get("ticker") else ""
    elif basic.get("price") is None:
        basic["price_state"] = "P_FROM_DB"
    elif abs(basic["price"] - pdb) / pdb < 0.01:
        basic["price_state"] = "P_CONFIRMED_DB"
    else:
        basic["price_state"] = "P_DB_CONFLICT(KEEP_BOTH)"
    if basic["upside_db"] is not None:
        if basic.get("upside_report") is not None:
            d0 = abs(basic["upside_report"] - basic["upside_db"])
            basic["upside_state"] = ("EXACT_MATCH_DB" if d0 < 0.05 else
                                     "ROUNDING_ONLY_DB" if d0 <= 0.8 else
                                     "FORMULA_MISMATCH_DB")
        elif basic.get("upside_state") in ("MISSING_SOURCE", "SINGLE_SOURCE"):
            basic["upside_state"] = "DB_DERIVED"
    apply_adj_upside(con, basic)      # 批659 操作員裁示:ADJ 基準的上漲空間(新欄,不覆寫上面任何一欄)
    return basic


def repair_price(db: Path | None = None, apply: bool = False) -> int:
    """批659 `repair-price`:**不重新擷取任何報告**,只拿現有列去庫裡重算價與升幅。

    為什麼要有這個動詞:價的分歧(上市所的價不在 `tw_daily_prices`)是**庫這一側**的事,
    跟報告擷得準不準無關。舊路只有 `run`,而 `run` 要有原始報告夾才跑得動——
    於是「庫已經有 81 列、價接錯了」這種情況,除了整批重跑沒有別的辦法。
    這支只讀價表、只寫五個庫欄,零網路、零擷取、不碰正本報告。

    無 `--apply` = **乾跑**:把改動逐類數出來、印前後對照,一個字都不寫。"""
    import duckdb                       # 懶載入(模組頂不硬相依重庫;缺件=誠實缺料不是假紅)
    dbp = _resolve_db(db)
    if dbp is None or not dbp.is_file():
        print(f"  [repair-price] ABSENT · 庫不在:{dbp}")
        return 3
    con = duckdb.connect(str(dbp))
    try:
        cols = [r[1] for r in con.execute("PRAGMA table_info('vrn_report_basic')").fetchall()]
    except Exception as exc:
        print(f"  [repair-price] ABSENT · 讀不到 vrn_report_basic:{type(exc).__name__}")
        con.close()
        return 3
    for _c, _t in (("price_src", "VARCHAR"), ("adj_factor", "DOUBLE"), ("adj_factor_date", "VARCHAR"),
                   ("target_price_adj", "DOUBLE"), ("price_latest_adj", "DOUBLE"),
                   ("price_latest_date", "VARCHAR"), ("upside_adj", "DOUBLE"),
                   ("upside_adj_state", "VARCHAR")):
        if _c in cols:                          # 舊庫沒有新欄=補上(ALTER 容錯,與 _ensure_tables 同律)
            continue
        try:
            con.execute(f"ALTER TABLE vrn_report_basic ADD COLUMN {_c} {_t}")
            cols.append(_c)
        except Exception:
            pass
    keys = ["report_file", "ticker", "report_date", "target_price", "price",
            "upside_report", "upside_state", "price_db", "upside_db", "price_state"]
    rows = con.execute(f'SELECT {", ".join(keys)} FROM vrn_report_basic').fetchall()
    changed, gained, lost, same = [], 0, 0, 0
    by_src: dict = {}
    adj_tally: dict = {}                        # 批659 操作員裁示:ADJ 上漲空間的誠實態分佈
    adj_rows: list = []
    for r in rows:
        b = dict(zip(keys, r))
        before = (b["price_db"], b["upside_db"], b["price_state"], b["upside_state"])
        apply_db_price(con, b)
        after = (b["price_db"], b["upside_db"], b["price_state"], b["upside_state"])
        _sk = b["price_src"] or "(無代號或無報告日)"
        if _sk.startswith("(料過期"):
            _sk = "(料過期:VDF 價庫沒抓到報告日附近 → via-price,要網路同意閘)"
        by_src[_sk] = by_src.get(_sk, 0) + 1
        if before == after and b.get("price_src") is None:
            same += 1
            continue
        if before == after:
            same += 1
        else:
            changed.append((b["report_file"], b["ticker"], before, after, b["price_src"]))
            if before[0] is None and after[0] is not None:
                gained += 1
            elif before[0] is not None and after[0] is None:
                lost += 1                      # 會變壞才是誠實的尺——真掉了就要數出來
        adj_tally[b.get("upside_adj_state") or "(無)"] = adj_tally.get(b.get("upside_adj_state") or "(無)", 0) + 1
        if b.get("upside_adj") is not None:
            adj_rows.append((b["ticker"], b["report_file"], b["target_price"], b["adj_factor"],
                             b["target_price_adj"], b["price_latest_adj"], b["price_latest_date"], b["upside_adj"]))
        if apply:
            con.execute("UPDATE vrn_report_basic SET price_db=?, price_src=?, upside_db=?, "
                        "price_state=?, upside_state=?, adj_factor=?, adj_factor_date=?, "
                        "target_price_adj=?, price_latest_adj=?, price_latest_date=?, "
                        "upside_adj=?, upside_adj_state=? WHERE report_file=?",
                        [b["price_db"], b["price_src"], b["upside_db"],
                         b["price_state"], b["upside_state"], b["adj_factor"], b["adj_factor_date"],
                         b["target_price_adj"], b["price_latest_adj"], b["price_latest_date"],
                         b["upside_adj"], b["upside_adj_state"], b["report_file"]])
    con.close()
    tag = "APPLIED" if apply else "乾跑(沒有 --apply,一個字都沒寫)"
    print(f"  [repair-price] {tag} · 庫 {dbp}")
    print(f"     列 {len(rows)} · 有改動 {len(changed)} · 不變 {same}"
          f" · **新拿到庫價 {gained}** · 反而掉了 {lost}")
    print(f"     價出自哪張表:" + " · ".join(f"{k} {v}" for k, v in sorted(by_src.items(), key=lambda x: -x[1])))
    for rf, tk, bf, af, src in changed[:8]:
        print(f"       {str(tk):6} {str(rf)[:34]:34} 價 {bf[0]}→{af[0]} ({src}) · 升幅 {bf[1]}→{af[1]} · 態 {bf[3]}→{af[3]}")
    if len(changed) > 8:
        print(f"       …另 {len(changed) - 8} 筆(全部在 --json 或直接查庫)")
    if lost:
        print(f"     ⚠ 有 {lost} 筆原本有庫價、重算後沒有——**先看這幾筆再決定要不要 --apply**")
    print(f"  [ADJ 上漲空間(操作員裁示:目標價×因子 ÷ 最新adj_close)] 算得出 {len(adj_rows)} 筆")
    for k, v in sorted(adj_tally.items(), key=lambda x: -x[1]):
        print(f"       {k:46} {v:>3}")
    for tk, rf, tp, fac, tpa, la, ld, ua in adj_rows[:10]:
        print(f"       {str(tk):6} {str(rf)[:30]:30} 目標 {tp} ×因子 {fac:.4f} = {tpa}"
              f" ÷ 最新adj {la}({ld}) → **{ua:+.1f}%**")
    if len(adj_rows) > 10:
        print(f"       …另 {len(adj_rows) - 10} 筆")
    return 0 if apply or not changed else 0


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
    # ── 批657:**寫的人要說出自己寫到哪一本** ──
    #   `[庫解析]` 那一行講的是「解到哪一本」,讀起來像在講價表——
    #   而 `vrn_report_basic` 其實就寫進同一本。操作員三跑下來,
    #   ENG073 印著 `[EXACT_MATCH_DB]`、矩陣卻 GREEN 0,來回三批才定案:
    #   ENG073 寫 `…\\vdf_tw_market.duckdb`,ENG083 v0112 讀
    #   `functional modules/VRN/output/vrn_reports.duckdb` —— **兩個不同的檔案**。
    #   批655 我量對了;批656 我被一個巧合(舊表的券商計數剛好一樣)說服而自我懷疑,
    #   那是**拿一個吻合的數字去推翻一個結構性的事實**(LL295)。
    #   治法最便宜的一半就在這裡:寫的人印出自己寫到哪裡,一行結案。
    print(f"[結構庫] vrn_report_basic 寫入 → {dbp}")
    con = duckdb.connect(str(dbp))
    _ensure_tables(con)
    # 批468(操作員追令「名稱統一從 VDF 每日 TWSE/TPEX/MOPS 清單更新」):
    # 代號驗證冊改**委派名稱正典冊** CGC_MDL142_TWNameBook(尾版 glob)。
    # 為什麼非換不可——量到的:`tw_listings` 只有 891 列而且存的是**全名**
    # (「茂生農經股份有限公司」),**連 2330 / 2454 / 3008 都不在裡面**;
    # 拿它當代號驗證冊,台積電、聯發科、大立光的報告一律驗不過。
    # 正典 `tw_listings_industry` 是 1,978 列四碼+簡稱,MDL142 已把
    # 「正典表 → 落盤 → 全名補位」三條源收成一本並標得出每家是哪條源答的。
    # 橋缺席=退回本檔原本的 tw_listings 直查(零回歸),並把因由印出來。
    names, _nb_why = {}, ""
    try:
        import importlib.util as _ilu73
        _c73 = sorted((VIA / "supportive modules" / "registry")
                      .glob("CGC_MDL142_TWNameBook_v*.py"))
        if _c73:
            _sp73 = _ilu73.spec_from_file_location("mdl142_eng073", _c73[-1])
            _m73 = _ilu73.module_from_spec(_sp73)
            _sp73.loader.exec_module(_m73)
            names = {code: row["name"] for code, row in _m73.book().items() if row.get("name")}
            _nb_why = f"MDL142 {_c73[-1].name}"
        else:
            _nb_why = "MDL142 缺席"
    except Exception as _e73:
        _nb_why = f"MDL142 載不進 {type(_e73).__name__}:{str(_e73)[:50]}"
    if not names:
        names = dict(con.execute(
            "SELECT code, name FROM tw_listings").fetchall()) \
            if "tw_listings" in {r[0] for r in con.execute("SHOW TABLES").fetchall()} \
            else {}
        _nb_why += f" → 退路 tw_listings {len(names)} 檔"
    print(f"  [代號驗證冊] {len(names)} 檔 ← {_nb_why}")
    nb = nm = na = 0
    _skip = []          # 批466:逐件護欄——壞一份不該讓整批陪葬
    for f in files:
        try:
            zones = json.loads(f.read_text(encoding="utf-8"))
        except Exception as _exc:
            _skip.append((f.stem, f"sidecar 讀不了 {type(_exc).__name__}"))
            continue
        try:
            basic, mets = extract_one(f.stem, zones, names)
        except Exception as _exc:
            # 誠實三態:略過這一份、把因由留下來、繼續跑完其餘的。
            # v0118 沒有這道護欄,一份 AttributeError 就讓整批入庫連
            # 「入庫計」都印不出來——而畫面上沒有任何一行說它死了。
            _skip.append((f.stem, f"{type(_exc).__name__}:{str(_exc)[:70]}"))
            continue
        # 批240:庫驗證道(前日 close 補值/對質)
        apply_db_price(con, basic)      # 批659:庫價/升幅/兩個態的唯一算法(repair-price 走同一支)
        # ── 升幅態升級(批654:**尺與產出端的字彙對不上,那一欄永遠不會綠**)──
        #   實測(操作員 105 份 · 容器 81 份,同一個簽名):
        #       上漲空間  GREEN 0 · YELLOW 30~38 · NODATA 51~67
        #   ENG083 的尺收的是 `EXACT_MATCH_DB / ROUNDING_ONLY_DB`;
        #   而舊碼這一段**只在 MISSING_SOURCE / SINGLE_SOURCE 時才跑**。
        #   於是「頁上的升幅 = 我自己算的 = 庫算的」這個**最強的證據**,
        #   寫出來的是 `EXACT_MATCH`(沒有 _DB)—— 尺不收,整欄 GREEN 0。
        #   一盞裝好、接上、永遠不會亮的燈(LL282 同族)。
        #
        #   改法遵 **只增不減**:不改任何既有狀態字的拼法(下游還在讀),
        #   只把「有沒有跟庫對過」這件事**記全**——
        #   `_DB` 後綴講的是「這一格拿庫對照過」,那是**證據有沒有到位**的事實,
        #   跟它先前是什麼狀態無關。所以條件從「先前態」改成「庫算得出來沒有」。
        #
        #   這不是把燈刷綠:頁與庫對不上的那些會被降成 `FORMULA_MISMATCH_DB`
        #   (例:緯創 CITI 報告 44.7 vs 庫算 50.7,因為頁上的 P 與庫的 P 就差了 4%),
        #   **這一改會讓某些原本 YELLOW 的變成更難看的態**——會變壞才是誠實的尺。
        if basic["upside_db"] is not None:
            if basic["upside_report"] is not None:
                d0 = abs(basic["upside_report"] - basic["upside_db"])
                basic["upside_state"] = ("EXACT_MATCH_DB" if d0 < 0.05 else
                                         "ROUNDING_ONLY_DB" if d0 <= 0.8 else
                                         "FORMULA_MISMATCH_DB")
            elif basic["upside_state"] in ("MISSING_SOURCE", "SINGLE_SOURCE"):
                basic["upside_state"] = "DB_DERIVED"
        # 批238④:派生層重算=同鍵 DELETE+INSERT(ENG063 同例;
        # 正本=input_reports 原件+sidecar 零觸碰)
        # 批412:券商/評等正規化 + 分析師姓名擷取(SSOT 缺席=新欄留空,舊欄不受影響)
        _txt = "\n".join(str(zones.get(k, "")) for k in ("header", "right", "body", "footer"))
        _bk = ssot_broker(f.stem, _txt)
        # 批558:周圍訊息區塊(頁首帶/右/**頁尾**)與中間本文標題區,都修復後才找。
        # 樞紐缺=兩者回空,下面這行自動退回 v0128 的 header+right(誠實退路)。
        _info_z, _head_z = zone_blocks(zones)
        _zone_top = _info_z or "\n".join(str(zones.get(k, "")) for k in ("header", "right"))
        _rt = ssot_rating(basic.get("rating_raw", ""), _txt, f.stem, _zone_top, _head_z)
        _an = ssot_analysts(f.stem, zones)
        basic["broker_ssot_key"] = _bk["key"]
        basic["broker_name_zh"] = _bk["zh"]
        basic["broker_name_en"] = _bk["en"]
        basic["broker_src"] = _bk["src"]
        # 批628:權威(在哪本冊上查到的)要跟通道(走哪條路找到的)一起留下來。
        #   overlay v0102 起 `src` 長成 `FILENAME_MAP+CANON`;舊 overlay 只給 `CANON`
        #   或只給 `FILENAME_MAP`,兩種都照收(不強制下游先升級)。
        if _bk.get("authority") and _bk["authority"] not in str(_bk.get("src", "")):
            basic["broker_src"] = f"{_bk['src']}+{_bk['authority']}"
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
    # 批419c:NULL 不等於 ''——舊列(加欄前寫入)的新欄是 NULL,而 `NULL <> ''` 在 SQL
    # 裡回 NULL 不是 TRUE,那些列一律不被計入。先前印「0/59」時分不出是
    # 「認不出」還是「舊列沒這欄」,兩者差很多。改用 COALESCE 並分開報。
    nbk = con.execute("SELECT count(*) FROM vrn_report_basic WHERE COALESCE(broker_ssot_key,'')<>''").fetchone()[0]
    nrt = con.execute("SELECT count(*) FROM vrn_report_basic WHERE COALESCE(rating_ssot_key,'')<>''").fetchone()[0]
    nnull = con.execute("SELECT count(*) FROM vrn_report_basic WHERE broker_ssot_key IS NULL").fetchone()[0]
    # 批419g:評等 0/59 有兩種可能——抽取階段就沒抓到字串,或抓到了但正規化查不到。
    # 只印後者的分母,就跟先前那個沒有因由的 0 一樣難查。
    nrr = con.execute("SELECT count(*) FROM vrn_report_basic WHERE COALESCE(rating_raw,'')<>''").fetchone()[0]
    try:      # 批418 型別欄:舊庫沒有就誠實跳過
        kind_hist = dict(con.execute(
            "SELECT COALESCE(report_kind,'(空)'), count(*) FROM vrn_report_basic GROUP BY 1 ORDER BY 2 DESC").fetchall())
    except Exception as _exc:
        kind_hist = {"(無此欄)": str(_exc)[:40]}
    # 批419d:診斷取樣**在關庫前**先抓好。v0109 我在關庫後另開一條唯讀連線,
    # 而且傳的是函式參數 db(預設 None)不是解析後的 dbp——組出 "...\None" 直接
    # IOException,整個 vrn_structdb rc=1。診斷程式碼把主流程弄掛,比沒有診斷更糟。
    ssot_sample = [r[0] for r in con.execute(
        "SELECT report_file FROM vrn_report_basic ORDER BY report_file LIMIT 3").fetchall()]
    con.close()
    print(f"[檔名層] {_fn_bridge()[1]}")
    print(f"[入庫計] 檔 {len(files)} · 入 {len(files) - len(_skip)} · 略過 {len(_skip)}"
          f" · basic +{nb}(庫 {tb})· metrics +{nm}"
          f"(庫 {tm})· 官方名冊命中={sum(1 for _ in names) and '在庫'}")
    # 批466:護欄收集了卻不印=吞掉。略過的逐件講出來,誰、為什麼。
    for _st, _wy in _skip:
        print(f"  [略過] {_st} · {_wy}")
    _m = fin_ssot()
    print(f"  [SSOT 正規化] 券商正典鍵 {nbk}/{tb} · 評等正典鍵 {nrt}/{tb}"
          f"(原始評等字串 {nrr} 筆{'=抽取階段就沒有,非正規化問題' if nrr == 0 else ''})· "
          f"分析師 +{na}(庫 {ta})· "
          + (f"NULL 欄 {nnull} 列(加欄前的舊列)· " if nnull else "")
          + ("金融機構 SSOT 在位" if _m is not None else f"**SSOT 缺席**:{_FIN['why']}")
          # 批419e:因由先前**只在模組 None 時才印**。但真實故障是「模組載得起來、
          # 每次查詢都拋例外」——ssot_broker 的 except 把因由存進 _FIN['why'] 之後
          # 就沒人看它,對外只剩一個沒有理由的 0/59。捕捉到卻不顯示,等於沒捕捉。
          + (f" · **查詢期例外**:{_FIN['why']}" if (_m is not None and _FIN["why"]) else ""))
    # 批421:NLP 掛載走哪一條也要看得見。v0113 以前寫死 v1.1.0,對外完全無跡可循;
    # 現在三段退路各自留名,退到哪一段當場說清楚。
    _ns = nlp_stats()
    print(f"  [NLP 掛載] 路徑={_ns['route']}"
          + (f" · 橋={_ns['src']}" if _ns["src"] else "")
          + (f" · 研報服務 {len(_ns['services'])}/6" if _ns["services"] else "")
          + (f" · **為何未走橋**:{_ns['why']}" if _ns["why"] else ""))
    # 批418:型別分佈。分不出型別,收尾閘就會把產業/晨報/研討會當成失敗。
    print("  [報告型別] " + (" · ".join(f"{k} {v}" for k, v in kind_hist.items()) or "(無列)"))
    # 批419c:零命中時把「為什麼」印出來。工作站回過「券商正典鍵 0/59」,
    # 但那一行只給得出數字給不出因由——0 可能是 SSOT 沒載、可能是 token 抽不到、
    # 也可能是抽到了而正典查無。靜默的 0 跟假訊息一樣難查,所以這裡直接取樣三份實跑。
    if _m is not None and nbk == 0 and tb:
        print("  [SSOT 診斷] 券商正典鍵零命中——逐項取樣(非猜測,實跑同一支函式):")
        for _rf in ssot_sample:
            _st = Path(str(_rf)).stem
            _tok = parse_broker(_st) or "(抽不到券商 token)"
            _r = ssot_broker(_st, "")
            print(f"    · {_st[:40]:<42} token={_tok:<10} → key={_r['key'] or '(空)'} src={_r['src'] or '(空)'}")
        print(f"    · 疊加層/正典模組:{getattr(_m, '__file__', '?')}")
        try:      # 批419e:疊加層自己的計數。JSON 沒載/壞掉就會在這裡現形
            print(f"    · 疊加層計數 stats()={_m.stats()}")
        except Exception as _sx:
            print(f"    · 疊加層 stats() 例外 {type(_sx).__name__}:{str(_sx)[:120]}")
        try:
            print(f"    · 疊加層資料檔:{getattr(_m, 'OVERLAY_JSON', '?')} · "
                  f"存在={Path(str(getattr(_m, 'OVERLAY_JSON', ''))).exists()}")
        except Exception as _px:
            print(f"    · 疊加層資料檔查詢例外:{str(_px)[:80]}")
        print(f"    · resolve_broker_filename 可呼叫={hasattr(_m, 'resolve_broker_filename')} · "
              f"resolve_broker 可呼叫={hasattr(_m, 'resolve_broker')}")
    return 0


def status(db: Path | None = None) -> int:
    import duckdb
    dbp = _resolve_db(Path(db) if db else None)
    if dbp is None or not dbp.exists():
        print(f"  [資料庫] {dbp or DB_TW} 不存在(先 run --db <path>)")
        return 2
    con = duckdb.connect(str(dbp), read_only=True)
    print(f"  [資料庫] {dbp}")
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

    done = []

    def chk(name, cond, note=""):
        # 批442 自審:檢數手寫(「三十五檢 OK 34」),與首頁引擎、MDL141 同一個病,
        # 這是第三支。會被忘記的數字就不該用手寫。
        done.append(name)
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
        # 批442:券商改回**首頁全能引擎的正典鍵**(CITI,不是本檔原本的 Citi)。
        # 這不是迴歸,是統一落地——原本兩個引擎連券商字串的大小寫都不一樣,
        # 矩陣上同一家券商會因為是誰寫的列而長得不同。
        and basic["broker"] in ("CITI", "Citi") and basic["report_date"] == "2025-06-04"
        and "Buy" in basic["rating_raw"] and basic["target_price"] == 165.0
        and basic["price"] == 114.0)
    # 批471:**這道檢原本把缺陷釘成了規格**。它寫著「48.1% vs 44.7%=
    # FORMULA_MISMATCH 誠實列示」——而 Citi 那份首頁逐字印的是三行:
    #     Expected share price return 44.7%   ← 與 upside_calc 同語意
    #     Expected dividend yield      3.3%
    #     Expected total return       48.1%   ← 44.7 + 3.3,**含息**
    # 報告一個字都沒錯,是舊 UPS_RX 把第一個選項寫成 `Expected total return`,
    # 拿含息總報酬去對純股價漲幅。檢把這個結果當成正確行為釘住,於是它不但沒被
    # 抓到,還被保護了三十幾批——**檢釘錯了,比沒有檢更難救**。
    # 順帶:上面那份 fixture 是真文的**有損轉錄**,漏抄了「股價報酬」那一行。
    # 兩條路都要驗,所以這裡測兩個案例:
    #   ㈠ fixture(只有總報酬+殖利率)→ 用報告自己的加法 44.7+3.3=48.0 對 48.1
    #   ㈡ 真文三行(補回漏抄的那一行)→ 直接取同語意的 44.7,EXACT_MATCH
    _z3 = dict(zones, right=zones["right"].replace(
        "Expected total return 48.1%",
        "Expected share price return 44.7%\nExpected total return 48.1%"))
    _b3, _ = extract_one("Citi-3231 20250604", _z3, names)
    chk("③ 交互驗證(Citi 首頁三行:股價報酬 44.7% / 殖利率 3.3% / 總報酬 48.1%)。"
        "㈠ 只抄到總報酬時,用**報告自己印的殖利率**換算成同語意再比(44.7+3.3=48.0 對 48.1);"
        "㈡ 抄到股價報酬時,**直接取同語意的那一行**=EXACT_MATCH。"
        "兩條都不是拿含息總報酬去對純股價——那是 v0120 以前判成 FORMULA_MISMATCH 的原因,"
        "而那個錯誤被這道檢本身釘成規格保護了三十幾批",
        basic["upside_calc"] == 44.7 and basic["upside_report"] == 48.1
        and basic["upside_state"] in ("EXACT_MATCH", "ROUNDING_ONLY")
        and basic.get("upside_basis") == "總報酬(含息)"
        and "總報酬對帳" in (basic.get("conflicts") or "")
        and _b3["upside_report"] == 44.7 and _b3["upside_state"] == "EXACT_MATCH"
        and _b3.get("upside_basis") == "股價報酬",
        f"(㈠ {basic['upside_report']}%/{basic.get('upside_basis')}→{basic['upside_state']} · "
        f"㈡ {_b3['upside_report']}%/{_b3.get('upside_basis')}→{_b3['upside_state']})")
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
        # ── ㊹ 批654:**尺與產出端的字彙對不上,那一欄永遠不會綠** ──
        #   實測簽名:上漲空間 GREEN 0(容器 81 份與操作員 105 份都一樣)。
        #   舊碼只在 MISSING_SOURCE/SINGLE_SOURCE 時才升級成 `_DB`,
        #   於是「頁=自算=庫算」這個最強證據寫出來的是 `EXACT_MATCH`,而尺只收 `EXACT_MATCH_DB`。
        #   這一檢造兩份真研報 + 真庫,一份庫價與頁價一致(該升 EXACT_MATCH_DB)、
        #   一份庫價與頁價差很多(**該降 FORMULA_MISMATCH_DB**)。
        #   會變壞的那一半才是重點:證明這不是把燈刷綠。
        c3 = duckdb.connect(str(dbp))
        c3.execute("INSERT INTO tw_listings VALUES ('6873','泓德能源'),('9999','假公司')")
        c3.execute("INSERT INTO tw_daily_prices VALUES "
                   "('2026-08-18','6873.TW',169.5),"      # 與頁上的 P 一致 → 升幅也會一致
                   "('2026-08-18','9999.TW',100.0)")      # 與頁上的 P 差很遠 → 升幅對不上
        c3.close()
        (tdp / "20260819兆豐個股報告-泓德能源(6873).json").write_text(json.dumps(
            {"header": "", "right": "目標價 208 元\n收盤價 169.5 元\n上漲空間 22.7%",
             "body": "", "footer": ""}, ensure_ascii=False), encoding="utf-8")
        (tdp / "20260819兆豐個股報告-假公司(9999).json").write_text(json.dumps(
            {"header": "", "right": "目標價 208 元\n收盤價 169.5 元\n上漲空間 22.7%",
             "body": "", "footer": ""}, ensure_ascii=False), encoding="utf-8")
        run(tdp, dbp)
        c4 = duckdb.connect(str(dbp))
        _g = c4.execute("SELECT upside_state, upside_report, upside_db FROM vrn_report_basic"
                        " WHERE ticker='6873'").fetchone()
        _b = c4.execute("SELECT upside_state, upside_report, upside_db FROM vrn_report_basic"
                        " WHERE ticker='9999'").fetchone()
        c4.close()
        chk("㊹ 庫對得上就要記成 `_DB`,對不上就要降級 —— 不是把燈刷綠。"
            "舊碼只在 MISSING/SINGLE 時才升級,於是「頁=自算=庫算」這個最強證據"
            "寫出來的是 EXACT_MATCH,而 ENG083 的尺只收 EXACT_MATCH_DB → 那一欄實測 GREEN 0",
            (_g is not None and _g[0] == "EXACT_MATCH_DB"
             and _b is not None and _b[0] == "FORMULA_MISMATCH_DB"),
            f"(庫一致 {_g} · 庫不一致 {_b})")
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
    # ── 批419c 一檢:NULL 不等於 ''(統計把舊列漏掉,0 就分不出是認不出還是沒欄)──
    import duckdb as _dd
    with tempfile.TemporaryDirectory() as _td27:
        _db27 = Path(_td27) / "n.duckdb"
        _c = _dd.connect(str(_db27))
        _c.execute("CREATE TABLE t(report_file VARCHAR, broker_ssot_key VARCHAR)")
        _c.execute("INSERT INTO t VALUES ('a.pdf','MS')")        # 認得出
        _c.execute("INSERT INTO t VALUES ('b.pdf','')")          # 認不出(誠實空字串)
        _c.execute("INSERT INTO t VALUES ('c.pdf',NULL)")        # 加欄前的舊列
        _naive = _c.execute("SELECT count(*) FROM t WHERE broker_ssot_key<>''").fetchone()[0]
        _fixed = _c.execute("SELECT count(*) FROM t WHERE COALESCE(broker_ssot_key,'')<>''").fetchone()[0]
        _nulls = _c.execute("SELECT count(*) FROM t WHERE broker_ssot_key IS NULL").fetchone()[0]
        _c.close()
        chk("㉗ 統計不得被 NULL 吞掉(批419c:`NULL <> ''` 在 SQL 回 NULL 不是 TRUE,"
            "加欄前寫入的舊列一律不被計入;先前印「券商正典鍵 0/59」時,分不出是「認不出」"
            "還是「舊列沒這欄」——兩者差很多。改 COALESCE 並把 NULL 列數分開報)",
            _naive == 1 and _fixed == 1 and _nulls == 1,
            f"(直算 {_naive} · COALESCE {_fixed} · NULL 列 {_nulls}=分得出來)")

    # ── 批419d 一檢:零命中診斷分支本身必須跑得完(它把主流程弄掛過)──
    with tempfile.TemporaryDirectory() as _td28:
        _t28 = Path(_td28)
        (_t28 / "NoBroker-9999 20260101.json").write_text(
            json.dumps({"header": "", "right": "", "body": "x", "footer": ""}, ensure_ascii=False),
            encoding="utf-8")
        _db28 = _t28 / "d.duckdb"
        _c28 = duckdb.connect(str(_db28))
        _c28.execute("CREATE TABLE tw_listings(code VARCHAR, name VARCHAR)")
        _c28.close()

        class _StubSSOT:                       # SSOT「在位」但一律查無=重現工作站的 0/59
            __file__ = "(stub)"

            @staticmethod
            def resolve_broker_filename(_tok):
                return {"key": "", "deny": ""}

            @staticmethod
            def resolve_broker(_x):
                return {"key": "", "deny": ""}

            @staticmethod
            def resolve_rating(_x):
                return {"key": ""}

        _keep = (_FIN["mod"], _FIN["tried"])
        _FIN["mod"], _FIN["tried"] = _StubSSOT, True
        _buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(_buf):
                _rc28 = run(_t28, _db28)
        finally:
            _FIN["mod"], _FIN["tried"] = _keep
        _out28 = _buf.getvalue()
        chk("㉘ 零命中診斷分支跑得完(批419d:v0109 我在關庫後另開一條唯讀連線,而且傳的是"
            "函式參數 db(預設 None)不是解析後的 dbp,組出 \"…\\None\" 直接 IOException,"
            "整個 vrn_structdb rc=1——**診斷程式碼把主流程弄掛,比沒有診斷更糟**。"
            "改成關庫前先取樣、完全不再開第二條連線)",
            _rc28 == 0
            and "[SSOT 診斷]" in _out28          # 分支真的有走到(不是繞過)
            and "[報告型別]" in _out28
            and "Traceback" not in _out28,
            f"(rc={_rc28} · 診斷行={'有' if '[SSOT 診斷]' in _out28 else '無'})")

    # ── 批419e 一檢:捕捉到的因由必須被顯示(捕捉到卻不顯示等於沒捕捉)──
    with tempfile.TemporaryDirectory() as _td29:
        _t29 = Path(_td29)
        (_t29 / "MS-2308 20251128.json").write_text(
            json.dumps({"header": "", "right": "", "body": "x", "footer": ""}, ensure_ascii=False),
            encoding="utf-8")
        _db29 = _t29 / "e.duckdb"
        _c29 = duckdb.connect(str(_db29))
        _c29.execute("CREATE TABLE tw_listings(code VARCHAR, name VARCHAR)")
        _c29.execute("INSERT INTO tw_listings VALUES ('2308','台達電')")
        _c29.close()

        class _BoomSSOT:                     # 模組在位,但每次查詢都炸=工作站的真實故障形狀
            __file__ = "(boom)"
            OVERLAY_JSON = _t29 / "not-there.json"

            @staticmethod
            def resolve_broker_filename(_tok):
                raise RuntimeError("疊加層資料檔讀不到")

            @staticmethod
            def resolve_broker(_x):
                raise RuntimeError("疊加層資料檔讀不到")

            @staticmethod
            def resolve_rating(_x):
                raise RuntimeError("疊加層資料檔讀不到")

            @staticmethod
            def stats():
                raise RuntimeError("疊加層資料檔讀不到")

        _keep29 = (_FIN["mod"], _FIN["tried"], _FIN["why"])
        _FIN["mod"], _FIN["tried"], _FIN["why"] = _BoomSSOT, True, ""
        _buf29 = io.StringIO()
        try:
            with contextlib.redirect_stdout(_buf29):
                _rc29 = run(_t29, _db29)
        finally:
            _FIN["mod"], _FIN["tried"], _FIN["why"] = _keep29
        _o29 = _buf29.getvalue()
        chk("㉙ 捕捉到的因由必須被顯示(批419e:工作站回「券商正典鍵 0/59 · 金融機構 SSOT 在位」"
            "——真實故障是模組載得起來但每次查詢都拋例外,ssot_broker 的 except 把因由存進 "
            "_FIN['why'] 之後就沒人看它,因為那個變數**只在模組 None 時才印**。"
            "捕捉到卻不顯示,等於沒捕捉)",
            _rc29 == 0
            and "查詢期例外" in _o29                 # 因由真的印出來了
            and "疊加層資料檔讀不到" in _o29           # 而且是**原始**因由,不是重述
            and "stats() 例外" in _o29               # 疊加層計數炸掉也照實說
            and "Traceback" not in _o29,
            f"(rc={_rc29} · 因由={'有' if '查詢期例外' in _o29 else '無'})")

    # ── 批419g 一檢:抽取器詞表比正規化器窄,59 條別名等於白加 ──
    _m30 = fin_ssot()
    if _m30 is None:
        chk("㉚ 評等別名詞表掃描(批419g)", False, f"(金融機構 SSOT 缺席:{_FIN['why']})")
    else:
        _vocab = rating_vocab(_m30)
        # 這些都在批413 的 59 條別名裡,但 RATING_RX 一個都認不出來
        # 「增持」本來就在 RATING_RX 裡,其餘四個不在——判準對著事實寫,不對著假設寫
        _narrow = [w for w in ("加碼", "續抱", "低配", "未評等") if not RATING_RX.search(w)]
        # 用「加碼」不用「增持」:操作員裁決「增持=加碼」,而疊加層原本只帶「增持」,
        # 「加碼」靠正典——正典缺席時裁決就掉了一半,批419g 已把它補進疊加層自帶
        _r_add = ssot_rating("", "", "凱基投顧_2891 中信金_20260519 加碼", "")
        _r_nr = ssot_rating("", "", "瑞基(4171,NR_未評等)-CTBC251208", "")
        _r_zone = ssot_rating("", "", "", "投資評等:加碼\n目標價 300 元")
        _r_none = ssot_rating("", "", "MS-Thermal Solutions 20251007", "")
        _r_raw = ssot_rating("Buy", "", "", "")          # 原路照舊優先
        chk("㉚ 評等別名詞表掃描(批419g:批413 把 59 條別名加進疊加層,但 RATING_RX 只認"
            " 8 個英文字加 7 個中文詞——增持/加碼/續抱/低配/未評等一個都掃不到,"
            "字典加了等於白加。改用**疊加層自己的別名**當掃描詞表(Zero-Hydra,不寫第二份),"
            "且只掃標題帶/右區與檔名——掃全文會把內文敘述裡的『中立』當成評等)",
            len(_narrow) == 4                                   # 證明舊詞表真的漏掉這四個
            and len(_vocab) >= 40 and all(len(w) >= 2 for w in _vocab)
            and _r_add["key"] == "BUY" and _r_nr["key"] == "NOT_RATED"
            and _r_zone["key"] == "BUY"
            and _r_none["key"] == ""                            # 沒有評等就是沒有,不硬塞
            and _r_raw["key"] == "BUY",
            f"(舊詞表漏 {len(_narrow)}/4 · 詞表 {len(_vocab)} 條 · 加碼→{_r_add['key']} · "
            f"未評等→{_r_nr['key']} · 無評等→{_r_none['key'] or '空'})")

    # ── 批420 二檢:檔名拆解律 + 評等全名冊(操作員規格,fixture 全取自真檔名)──
    _t1 = tokenize_filename("3014TT-20231005")
    _t2 = tokenize_filename("凱基投顧_3665 貿聯-KY_李承泰_20260519")
    _t3 = tokenize_filename("【國泰證期研究部】神達(3706 TT)-初次評等買進(+30.4_)-大顯神威,營運騰達-20250822")
    _t4 = tokenize_filename("華南投顧-2637-慧洋-KY-1141202")
    _t5 = tokenize_filename("6933_AMAX-KY_個股介紹報告")
    chk("㉛ 檔名拆解律(操作員規格:中英文標點與**字集轉換處**切開,TRIM 後成為獨立連續的"
        "英/中/數單位;四碼數字=台股 TICKER,較長的數字=日期;名字-KY 也是公司名稱)。"
        "關鍵在 3014TT——沒有標點、只有數字↔英文的轉換,舊的三支 regex 各管一段,誰也切不開",
        _t1["ticker_cands"] == ["3014"] and _t1["date_cands"] == ["20231005"]
        and _t1["market"] == "TT" and "TT" in _t1["tokens"]
        and _t2["ticker_cands"] == ["3665"] and _t2["date_cands"] == ["20260519"]
        and "貿聯-KY" in _t2["name_cands"] and "貿聯" in _t2["name_cands"]
        and _t3["ticker_cands"] == ["3706"] and _t3["market"] == "TT"
        and _t4["ticker_cands"] == ["2637"] and _t4["date_cands"] == ["1141202"]
        and "慧洋-KY" in _t4["name_cands"]
        and "AMAX-KY" in _t5["name_cands"] and _t5["ticker_cands"] == ["6933"],
        f"(3014TT→代號 {_t1['ticker_cands']} 日期 {_t1['date_cands']} 市場 {_t1['market']} · "
        f"貿聯-KY 在候選={'是' if '貿聯-KY' in _t2['name_cands'] else '否'})")

    chk("㉜ 較長的數字=日期(三種寫法);四碼數字不得被當日期",
        date_from_token("20251202") == "2025-12-02"
        and date_from_token("1141202") == "2025-12-02"          # 民國 114 → 2025
        and date_from_token("251209") == "2025-12-09"
        and date_from_token("3014") == "" and date_from_token("") == ""
        and parse_date("3014TT-20231005") == "2023-10-05"
        and parse_date("華南投顧-2637-慧洋-KY-1141202") == "2025-12-02"
        and parse_date("6933_AMAX-KY_個股介紹報告") == "",       # 沒有日期就是沒有
        f"(8碼 {date_from_token('20251202')} · 民國 {date_from_token('1141202')} · "
        f"6碼 {date_from_token('251209')} · 四碼 {date_from_token('3014') or '空'})")

    # 批421:NLP 掛載改走支援模組 SUP_MDL744。這檢要證的是「真的走到尾版」,
    # 不是「有東西可用」——所以用判別輸入(連續空白 stdlib NFKC 不併、正主會併),
    # 全形轉半形兩者答案相同=測不出差別,不能拿來當證據。
    _h = nlp_hub()
    _ns = nlp_stats()
    _probe = "台積電  的的的營收"
    _via_hub = _nfkc(_probe) == "台積電 的的的營收"
    _std = unicodedata.normalize("NFKC", _probe)
    chk("㉝ NLP 走支援模組尾版(批421;判別輸入證明非 stdlib 後備;"
        "六項研報服務在位;橋缺席時仍有 v1.1.0→stdlib 三段退路)",
        _h is not None and _ns["route"] == "HUB"
        and _ns["hub_state"] == "VERIFIED" and _ns["hub_dir"].endswith("v1.8.0")
        and len(_ns["services"]) == 6
        and _via_hub and _std != "台積電 的的的營收"
        and callable(globals().get("nlp_stats")),
        f"(路徑={_ns['route']} 夾={_ns['hub_dir'] or '-'} "
        f"服務 {len(_ns['services'])}/6;正主={_nfkc(_probe)!r} vs stdlib={_std!r}"
        + (f";why={_ns['why']}" if _ns["why"] else "") + ")")

    # 批425:--dir/--db 必須真的傳進 run()。用攔截真實呼叫來證明,
    # 不用「原始碼裡有這串字」那種掃法(那只證明字在,不證明會生效)。
    _seen = {}
    _real_run, _real_argv = globals()["run"], sys.argv
    try:
        globals()["run"] = lambda zdir=None, db=None: (_seen.update(
            {"zdir": zdir, "db": db}) or 0)
        sys.argv = ["x", "run", "--dir", "/tmp/_d_", "--db", "/tmp/_b_.duckdb"]
        _rc = main()
        sys.argv = ["x", "run", "--dir"]            # 缺值對照組:不得 IndexError
        _seen2 = {}
        globals()["run"] = lambda zdir=None, db=None: (_seen2.update(
            {"zdir": zdir, "db": db}) or 0)
        _rc2 = main()
    finally:
        globals()["run"], sys.argv = _real_run, _real_argv
    chk("㉞ CLI 旗標真的接到 run()(批425:v0114 以前 main() 是光禿禿的 `return run()`,"
        "--dir/--db 從不解析,傳了不生效也不吭聲;兄弟引擎 ENG072 認 --dir、"
        "ENG074 認 --db,只有本器兩個都不認=無法把鏈指向別的報告夾或別的庫。"
        "缺值時誠實忽略,不得 IndexError)",
        _rc == 0 and Path(str(_seen.get("zdir"))).as_posix() == "/tmp/_d_"      # 批521:Windows 反斜線同義
        and Path(str(_seen.get("db"))).as_posix() == "/tmp/_b_.duckdb"
        and _rc2 == 0 and _seen2.get("zdir") is None,
        f"(dir={_seen.get('zdir')} db={_seen.get('db')};缺值→{_seen2.get('zdir')})")

    # 批442 ㉟:檔名層綁首頁全能引擎的公開契約(邏輯一致化)
    _e442, _w442 = _fn_bridge()
    _b442, _ = extract_one("20250819兆豐個股報告-泓德能源(6873)", {"body": "x"}, {})
    _s442, _ = extract_one("第一場 2026年投資大趨勢 - 華南投顧 -1141201", {"body": "x"}, {})
    chk("㉟ 檔名層綁首頁全能引擎的公開契約(批442 操作員令「兩邊工具都要一致化,"
        "邏輯一致化」。**先量再改**:庫內 64 份跑完入庫再與首頁引擎逐檔比對,"
        "型別不一致 38/64、代號不一致 37/64。根因不是啟發式微調,是**兩個引擎讀不同的"
        "名冊表**——首頁走 NameReconciler 階梯到 tw_listings_industry(1978 檔,6873 在),"
        "本檔寫死 tw_listings(891 檔,6873 不在);代號查不到→型別掉成「其他」→"
        "BASIC INFO 整片是空的。零九頭龍:不抄一份過去,綁 filename_facts() 公開契約。"
        "綁完 64/64 型別/代號/券商/報告日**四項全一致**。橋缺席就退本檔原邏輯並印因由)",
        (_b442["ticker"] == "6873" and _b442["report_kind"] == "個股"
         and _s442["report_kind"] == "研討會" and not _s442["ticker"]
         and "filename_facts" in _w442) if _e442 is not None
        else ("退本檔原檔名層" in _w442 or "缺檔" in _w442),
        f"({_w442[:72]} · 6873→{_b442['ticker'] or '-'}/{_b442['report_kind']} · "
        f"研討會→{_s442['report_kind']}/{_s442['ticker'] or '無代號'})")

    # ㊱ 批447:一對錯的值不得互相作證把一對對的值擋在門外
    _fe47, _fewhy47 = _fn_bridge()
    _cases47 = [
        ("MS-2308 20251128", 38.0, 28.0, 1288.0, 932.0,
         "Target Price 1,288\nPrice (Nov 28, 2025): 932"),
        ("JP-3653 20251003", 26.0, 60.0, 3650.0, 2470.0,
         "Target Price 3,650\nPrice (02 Oct 25): 2,470"),
        ("MS-8210 20251007", 18.0, 7.0, 730.0, 621.0,
         "Target Price 730\nClose 621"),
    ]
    _rows47, _seen47 = [], 0
    if _fe47 is not None:
        for _nm, _otp, _opx, _wtp, _wpx, _t47 in _cases47:
            _seen47 += 1
            _tp47 = _fe47.fv.extract_target_price(_t47)
            _px47 = _fe47.fv.doc_close(_t47)
            _pair = (_tp47 is not None and _px47 is not None and _px47 > 0
                     and 0.30 <= _tp47 / _px47 <= 3.2 and _tp47 != _px47)
            # 舊守衛(新 TP 拿**舊**現價比)會不會把它踢掉
            _old_kick = bool(_opx and _tp47 and not (0.30 <= _tp47 / _opx <= 3.2))
            # 舊值自己成對時**落在合理帶內**=它有本事自我辯護,這才是關鍵
            _self_def = bool(_opx and 0.30 <= _otp / _opx <= 3.2)
            _rows47.append((_nm, _tp47 == _wtp and _px47 == _wpx, _pair, _old_kick, _self_def))
    chk("㊱ 契約給的是**一對**就整對收——一對錯的值不得互相作證(批447 工作站實錄:"
        "批446 讓鏈終於跑完整,而 MS-2308 入庫仍是 TP=38 P=28、JP-3653 仍是 26/60、"
        "MS-8210 仍是 18/7,批445 修對的值一個都沒進來。根因是兩道守衛**互相擋住對方**:"
        "新目標價拿**舊現價**比、新現價再拿**舊目標價**比;而這三份的舊值剛好一起錯得"
        "自洽(38/28=1.36、26/60=0.43、18/7=2.57 全落在合理帶 0.30–3.2 之內),"
        "於是 1288÷28=46 判荒謬踢掉、932 再拿 38÷932=0.04 判荒謬踢掉。"
        "批239 的配對律沒錯,錯在拿它去比**混搭的一對**)",
        _seen47 >= 2 and all(ok and pair and kick and selfdef
                             for _, ok, pair, kick, selfdef in _rows47),
        f"(真的驗過 {_seen47}/{len(_cases47)} 份 · "
        + " · ".join(f"{n[:8]}:{'契約對' if ok else '值不合'}"
                     f"/{'舊守衛會踢' if kick else '舊守衛不踢'}"
                     f"/{'舊值自洽' if sd else '舊值不自洽'}"
                     for n, ok, _, kick, sd in _rows47) + ")")

    # ── 批554 ㊲㊳㊴:評等第四道(規則樞紐)+ 第二道的本文守衛。
    #    ㊲ 正向、㊳ 負向、㊴ 真迴歸——**三檢綁一組**:只有 ㊲ 會被「什麼都收」騙過去。
    _hub54, _hw54 = rule_hub()
    _m54 = fin_ssot()
    if _hub54 is None or _m54 is None:
        for _n54 in ("㊲ 評等第四道補上正本詞(批554)",
                     "㊳ 第四道負向對照:內文假朋友不得被判成評等(批554)",
                     "㊴ 第二道本文守衛(批554)"):
            chk(_n54, False, f"(樞紐或金融機構 SSOT 缺席:{_hw54 or _FIN['why']})")
    else:
        # ㊲ 正向:正本 38 詞逐詞放進「投資評等 X」的頁首帶。
        #    對照組是 **_rating_three 本尊**(v0127 的前三道),不是我另寫一份近似品——
        #    我第一版真的另寫了一份,它報「舊路徑漏 7 個」,真值是 14 個(LL85 同型:尺子先錯)。
        _canon54 = _hub54.rating_words()
        _old54, _new54 = [], []
        for _w54 in _canon54:
            _zt54 = f"投資評等 {_w54}\n目標價 250 元"
            _txt54 = _zt54 + "\n本文段落照舊。"
            if not _rating_three(_m54, "", _txt54, "2330_TW_20250101", _zt54).get("key"):
                _old54.append(_w54)                                     # 前三道判不出
            if not ssot_rating("", _txt54, "2330_TW_20250101", _zt54).get("key"):
                _new54.append(_w54)                                     # 四道全開仍判不出
        _gain54 = [w for w in _old54 if w not in _new54]
        chk("㊲ 評等第四道真的補上了正本詞(批554 操作員令「評等以同義字為主」:"
            "**不抄詞表,向樞紐要實作**——抄一份 38 詞進來就是第二顆會漂移的頭,"
            "而且批540 量過光補詞彙不補守衛會製造假評等)",
            len(_new54) == 0 and len(_gain54) >= 10,
            f"(正本 {len(_canon54)} 詞 · 前三道判不出 {len(_old54)} 個 · 四道全開判不出 {len(_new54)} 個 · "
            f"第四道補起 {len(_gain54)} 個:{'、'.join(_gain54[:6])}{'…' if len(_gain54) > 6 else ''})")

        # ㊳ 負向:六條內文假朋友放到本文第 47 行(遠離頁首帶),一條都不准命中。
        #    這才是「本文也可擷取」與「全文亂掃」的分界線。
        _bad54 = ("外資持有比重上升至 23%,投信同步調節。",
                  "公司宣布增持庫藏股 5000 張,董事會通過。",
                  "法人持股比重下降,融資餘額增加。",
                  "本季營收區間落在 120~130 億元。",
                  "該廠新增產能將於明年加入量產。",
                  "Management will add capacity in 2H26 and hold inventory flat.")
        _zt54b = "台積電 2330 法說會紀要\n日期 2025-01-01"
        _fire54 = [b[:14] for b in _bad54
                   if ssot_rating("", _zt54b + "\n" + ("內文段落。\n" * 45) + b,
                                  "2330_TW_20250101", _zt54b).get("key")]
        chk("㊳ 第四道負向對照:內文假朋友放到本文第 47 行,一條都不准被判成評等"
            "(LL68:「外資持有比重」含『持有』、「增持庫藏股」含『增持』;"
            "守衛在樞紐那一側,不是我這裡放行——這一檢就是在量那道守衛還在不在)",
            len(_fire54) == 0,
            f"(假朋友 {len(_bad54)} 條 · 誤命中 {len(_fire54)} 條"
            + (f":{'、'.join(_fire54)}" if _fire54 else "") + ")")

        # ㊴ 真迴歸:上面那六條裡,`hold inventory flat` 這一條 **v0127 真的判成 HOLD**。
        #    不是我造的假想例——載上一版當場跑給你看;它證明 ㊳ 不是自動綠的裝飾檢。
        # 批558 修:v0128 起這個 bug 已經沒了,所以「上一版」不再是對照組——
        # 批554 我把對照組釘成「上一版」,那是**會自己過期的尺**(v0129 一出來就 FAIL)。
        # 改成:找**最後一個還沒有這道守衛的版本**(檔裡沒有 RATING_HEAD_LINES 這個印記)。
        # 一個都找不到=誠實說「對照組已不存在」,不是 FAIL——歷史檔被清掉不等於迴歸回來了。
        _prev54 = [q for q in sorted((VIA / "functional modules" / "VRN").glob(
            "VRN_ENG073_ReportStructuredDB_v*.py"))
            if q.name < Path(__file__).name
            and "RATING_HEAD_LINES" not in q.read_text(encoding="utf-8", errors="replace")]
        _en54 = "Management will add capacity in 2H26 and hold inventory flat."
        _doc54 = _zt54b + "\n" + ("內文段落。\n" * 45) + _en54
        if not _prev54:
            chk("㊴ 第二道的本文守衛(批554 真迴歸修;批558 改尺)", True,
                "(無守衛的舊版已不在樹上=對照組不存在,誠實 SKIP;"
                "本版行為仍由 ㊳ 六條假朋友負向對照在量)")
        else:
            try:
                import importlib.util as _il54
                _sp54 = _il54.spec_from_file_location("_e73_prev_b554", _prev54[-1])
                _pm54 = _il54.module_from_spec(_sp54)
                _sp54.loader.exec_module(_pm54)
                _was54 = _pm54.ssot_rating("", _doc54, "2330_TW_20250101", _zt54b).get("key") or ""
            except Exception as _ex54:
                _was54 = f"載不動:{type(_ex54).__name__}"
            _now54 = ssot_rating("", _doc54, "2330_TW_20250101", _zt54b).get("key") or ""
            chk("㊴ 第二道的本文守衛是**真迴歸修**,不是假想(v0127 的第二道拿 RATING_RX 掃全文、"
                "沒有線索詞要求,本文第 47 行的 `hold inventory flat` 就被判成 HOLD。"
                "這型假評等 LL68 早就寫過,只是它一直住在本器自己的第二道裡,批554 之前沒有一檢在量它。"
                "改成只掃前 40 行,本文深處交給有守衛的第四道)",
                _was54 == "HOLD" and _now54 == "",
                f"(對照組 {_prev54[-1].name} → {_was54 or '空'} · 本版 → {_now54 or '空'})")

    # ── 批558 ㊵㊶㊷:操作員令「第一頁周圍訊息區塊及中間本文標題區修復後尋找」。
    #    ㊵ 正向(三區各一)· ㊶ **純增量**(對 v0128 逐格比,零改判)· ㊷ 負向(標題區不收敘述句)。
    _hub58, _hw58 = rule_hub()
    _Z = {"header": "凱基投顧 研究部\n2330 台積電",
          "right": "投資\n評等\n增加持股",                      # 標籤與值被換行切開
          "body": ("公司近況說明如下,本季營收表現穩健。\n"
                   "【投資評等】維持增加持股\n"
                   "本公司預期明年毛利率將持續改善,主要受惠於產品組合優化。\n"
                   "二、目標價 1250 元\n"
                   "外資持有比重上升至 23%,投信同步調節,籌碼面轉趨分散。\n"),
          "footer": "風險聲明 · 本報告目標價 1250 元 · 資料來源:公司、凱基投顧"}
    if _hub58 is None:
        for _n58 in ("㊵ 兩區修復後尋找(批558)", "㊶ 兩區是純增量(批558)", "㊷ 標題區負向對照(批558)"):
            chk(_n58, False, f"(樞紐缺席:{_hw58})")
    else:
        _info58, _head58 = zone_blocks(_Z)
        # ㊵-a 頁尾真的進了搜尋範圍(v0128 的主 join 沒有 footer,所以這一格本來是看不見的)
        _foot_in = "風險聲明" in _info58 and "1250" in _info58
        # ㊵-b 標題區挑到了兩個標題,而且沒把三句敘述句收進來
        _head_ok = ("【投資評等】維持增加持股" in _head58 and "目標價 1250 元" in _head58
                    and "外資持有比重" not in _head58 and "毛利率將持續改善" not in _head58)
        # ㊵-c 斷行修復:右區「投資↵評等↵增加持股」接回來才有線索詞
        _rep_ok = "投資 評等 增加持股" in _info58
        _rt58 = ssot_rating("", "\n".join(str(_Z[k]) for k in ("header", "right", "body", "footer")),
                            "2330_TW_20250101", _info58, _head58)
        chk("㊵ 兩區**修復後**尋找都通了(批558 操作員令):"
            "①頁尾進了範圍(v0128 的主 join 只有 header+right+body,**footer 整區從來沒被搜過**)· "
            "②標題區挑到章節標題、沒收敘述句 · ③斷行修復把『投資↵評等↵增加持股』接回來",
            _foot_in and _head_ok and _rep_ok and _rt58.get("key") == "BUY",
            f"(頁尾在={_foot_in} · 標題區={_head_ok} · 斷行修復={_rep_ok} · 評等={_rt58.get('key') or '空'})")

        # ㊶ 純增量:拿 v0128 當對照組,同一批夾具逐格比——**v0128 有值的格,本版必須一模一樣**。
        #    新增的搜尋區是「接在既有之後」,所以理論上不可能改判;理論要被量,不是被相信。
        _prev58 = [q for q in sorted((VIA / "functional modules" / "VRN").glob(
            "VRN_ENG073_ReportStructuredDB_v*.py")) if q.name < Path(__file__).name]
        _zoo58 = [_Z,
                  {"header": "美系外資 · TSMC (2330.TW): Buy", "right": "Target Price NT$1,400.00\nPrice NT$1,180.00",
                   "body": "We raise estimates on AI demand.\n1. Valuation\nOur TP is based on 22x 2027 EPS.\n", "footer": ""},
                  {"header": "產業報告 · 半導體展望", "right": "", "body": "展望2026半導體產業趨勢持續向上。\n", "footer": "免責聲明"},
                  # 這一格是**專門用來量頁尾**的:目標價只寫在 footer,別的區一個數字都沒有。
                  # v0128 的主 join 沒有 footer → 它只能回空;本版回 888。這就是那一區的價值。
                  {"header": "某某投顧 個股速報\n2330 台積電", "right": "評等 買進",
                   "body": "本季展望維持樂觀,產品組合持續優化。\n", "footer": "目標價 888 元 · 免責聲明"}]
        _same58, _gain58, _diff58 = 0, 0, []
        if not _prev58:
            chk("㊶ 兩區是純增量(批558)", False, "(找不到舊版可當對照組)")
        else:
            import importlib.util as _il58
            _sp58 = _il58.spec_from_file_location("_e73_prev_b558", _prev58[-1])
            _pm58 = _il58.module_from_spec(_sp58)
            _sp58.loader.exec_module(_pm58)
            for _i58, _z58 in enumerate(_zoo58):
                _o58, _ = _pm58.extract_one(f"2330_TW_2025010{_i58}", _z58, {})
                _n58b, _ = extract_one(f"2330_TW_2025010{_i58}", _z58, {})
                for _k58 in ("target_price", "price", "rating_raw", "ticker", "report_type"):
                    _ov, _nv = _o58.get(_k58), _n58b.get(_k58)
                    if _ov in (None, "", 0):
                        _gain58 += 1 if _nv not in (None, "", 0) else 0
                    elif _ov == _nv:
                        _same58 += 1
                    else:
                        _diff58.append(f"夾具{_i58}.{_k58}:{_ov}→{_nv}")
            chk("㊶ **這四格夾具上**兩區沒有改判(批558:新增的搜尋區接在既有搜尋序之後)。"
                "注意這一檢只證明這四格——本批另有一處**是刻意改判的**(評等的優先權換序),"
                "由 ㊸ 單獨量給你看。一檢只能擔保它真的跑過的那些格,不能擔保全體(L57 誠實分母)",
                not _diff58,
                f"(對照 {_prev58[-1].name} · 相同 {_same58} 格 · 本來空現在有值 {_gain58} 格 · "
                f"改判 {len(_diff58)} 格" + (f":{'、'.join(_diff58)}" if _diff58 else "") + ")")

        # ㊷ 負向:標題區只縮小範圍,不做判定——敘述句不准進來,進來了守衛也得擋住。
        _bad58 = ("外資持有比重上升至 23%,投信同步調節。",
                  "公司宣布增持庫藏股 5000 張。",
                  "目標市場規模 2026 年上看 100 億元。",
                  "Management will add capacity and hold inventory flat.")
        _z58n = {"header": "某某投顧 法說會紀要", "right": "", "footer": "免責聲明",
                 "body": "\n".join(_bad58) + "\n"}
        _i58n, _h58n = zone_blocks(_z58n)
        _rt58n = ssot_rating("", "\n".join(str(_z58n[k]) for k in ("header", "right", "body", "footer")),
                             "2330_TW_20250101", _i58n, _h58n)
        _tp58n, _ = extract_one("2330_TW_20250101", _z58n, {})
        chk("㊷ 標題區負向對照:四條敘述句型的假朋友(外資持有比重/增持庫藏股/目標市場規模/"
            "add capacity…hold inventory)——標題區只負責縮小範圍,**不做判定**;"
            "就算被收進來,評等與目標價都不准因此生出值",
            not _rt58n.get("key") and _tp58n.get("target_price") in (None, "", 0),
            f"(標題區收到 {len(_h58n)} 字 · 評等={_rt58n.get('key') or '空'} · "
            f"目標價={_tp58n.get('target_price') if _tp58n.get('target_price') not in (None, '', 0) else '空'})")

    # ㊸ 批558 的**刻意改判**:評等優先權換序。這一格必須自己站出來被看見,
    #    不能藏在「純增量」四個字底下——藏起來的改判,下次就是別人的假綠。
        _v58 = ("凱基投顧 2330 台積電\n投資評等\n【投資評等】維持增加持股\n目標價 1250 元")
        # ═══ 批628:這一檢在 v0130 出版的當下自己失效了 ═══════════════════
        # 它原本寫 `if q.name < Path(__file__).name` 取**上一版**當對照組。
        # 批558 寫的時候本檔是 v0129,上一版是 v0128(還沒換序)→ 對照組回 HOLD,檢成立。
        # 批628 出了 v0130,上一版變成 **v0129(已經換過序)** → 對照組也回 BUY,
        # 「改判」看起來消失了,這一檢當場紅——**而程式一個字都沒改**。
        # 教訓:量「這一批刻意改了什麼」的差分檢,對照組要**釘在被改的那一版**,
        # 不能寫成「上一版」;寫成上一版的,下一次出版就會自己失效。
        # (㊶ 那種「不准改判」的零回歸檢相反,它本來就該比**最近的**上一版。)
        _B558_BASE = "VRN_ENG073_ReportStructuredDB_v0128.py"
        _prev58b = [q for q in [(VIA / "functional modules" / "VRN" / _B558_BASE)] if q.is_file()]
        _was58, _now58 = "?", (ssot_rating("", _v58, "2330_TW_20250101", _v58).get("key") or "空")
        if _prev58b:
            try:
                import importlib.util as _il58b
                _sp = _il58b.spec_from_file_location("_e73_prev_b558b", _prev58b[-1])
                _pm = _il58b.module_from_spec(_sp)
                _sp.loader.exec_module(_pm)
                _was58 = _pm.ssot_rating("", _v58, "2330_TW_20250101", _v58).get("key") or "空"
            except Exception as _ex:
                _was58 = f"載不動:{type(_ex).__name__}"
        chk("㊸ 本批**刻意改判**的那一格(批558 評等優先權換序:疊加層裸子字串詞表 → 降為最後手段,"
            "樞紐實作提前到它前面)。「【投資評等】維持增加持股」裡,疊加層把**動詞**「維持」登記成 "
            "HOLD 別名,而更長更對的「增加持股」在本器 SSOT 查不到 → 粗的那一道先贏,給出 HOLD。"
            "維持增加持股 = 維持 BUY,不是 HOLD。**這是改判,不是增量**,所以單獨列一檢",
            (_was58 == "HOLD" and _now58 == "BUY") if _prev58b else (_now58 == "BUY"),
            f"(對照 {_prev58b[-1].name if _prev58b else _B558_BASE + ' 不在樹上→只驗本版'}"
            f" → {_was58} · 本版 → {_now58})")

    # ── 批659 ㊺:價有兩張表,上市所的價不在 VRN 一直查的那張 ──
    import duckdb as _dd
    _c = _dd.connect(":memory:")
    _c.execute("CREATE TABLE tw_daily_prices(date VARCHAR, ticker VARCHAR, close DOUBLE)")
    _c.execute("INSERT INTO tw_daily_prices VALUES ('2025-06-27','6488.TWO',480.0)")
    _c.execute("CREATE TABLE tw_trading_daily(date VARCHAR, code VARCHAR, market VARCHAR, close DOUBLE)")
    _c.execute("INSERT INTO tw_trading_daily VALUES ('2025-06-27','2330','TWSE',1080.0),"
               "('2025-06-27','6488','TPEx',479.0)")
    _otc = _prior_close(_c, "6488", "2025-06-30")      # 上櫃:第一張就中
    _twse = _prior_close(_c, "2330", "2025-06-30")     # 上市:第一張沒有 → 要走到第二張
    _none = _prior_close(_c, "9999", "2025-06-30")     # 兩張都沒有 → 誠實 None
    _fut = _prior_close(_c, "2330", "2024-01-01")      # 報告日早於全部資料 → None
    _stale = _prior_close(_c, "2330", "2026-09-09")    # 有這支,但最近一筆是一年多前=**料過期不是有料**
    chk("㊺ 批659 庫價兩車道(上市所的價不在 tw_daily_prices 裡):上櫃 6488 走 tw_daily_prices · "
        "上市 2330 在那張表 0 列,**要走到 tw_trading_daily(code 裸碼,含 TWSE)**才拿得到 1080;"
        "出處回得出表名;而且「查無此股」與「有這支但料過期」**要分得開**——"
        "報告日 2026-09-09 卻只有 2025-06-27 的價,那是缺料,不是拿舊價來充數",
        _otc == (480.0, "tw_daily_prices") and _twse == (1080.0, "tw_trading_daily")
        and _none == (None, "(查無此股)") and _fut == (None, "(查無此股)")
        and _stale[0] is None and _stale[1].startswith("(料過期:")
        and "tw_trading_daily" in _stale[1],
        f"(上櫃 {_otc} · 上市 {_twse} · 查無 {_none[1]} · 過期 {_stale[1]})")
    chk("㊺b 批659 這道新鮮度閘是被自己的乾跑逼出來的:接上第二張表後乾跑說「新拿到庫價 37 件」,"
        "逐件看才發現報告日 2025-08~2026-09 拿回來的 close **全是 2025-06-30 那天的**"
        "(上市所 1,056 檔停在該日)。沒有這道閘,37 筆會用一年前的價算出『合理』的升幅寫進庫,"
        "四項指標全部變好——**那才是真正的假綠**",
        PRICE_FRESH_DAYS == 14 and _days_between("2025-06-27", "2025-06-30") == 3
        and _days_between("2025-06-30", "2026-09-09") == 436
        and _days_between("壞日期", "2025-06-30") is None,
        f"(閘 {PRICE_FRESH_DAYS} 天 · 3 天=新鮮 · 436 天=過期 · 解析不了=None 不當過期也不當新鮮)")
    _c.execute("DROP TABLE tw_daily_prices")           # 反例:第一張表整個不在
    _drop = _prior_close(_c, "2330", "2025-06-30")
    chk("㊻ 批659 反例——第一張表出例外就整個放棄的舊 bug:舊碼 `except: return None` 擺在迴圈裡,"
        "第一張表一炸後面全不試;現在第一張表不存在時,第二張**仍要試到**並拿回 1080",
        _drop == (1080.0, "tw_trading_daily"), f"({_drop})")
    _c.close()
    chk("㊼ 批659 只增不減:出處走**新欄** price_src,`price_state` 的字彙一個字不動"
        "(ui_support 的 DataCatalog/InputConsole 兩張頁正在讀它;LL292 改產出端忘了尺,整欄綠 0 格)",
        '"price_src VARCHAR"' in src and 'basic["price_src"] = pdb_src' in src
        and '"DB_NO_MATCH"' in src and '"P_FROM_DB"' in src and '"P_CONFIRMED_DB"' in src
        and '"P_DB_CONFLICT(KEEP_BOTH)"' in src)
    # ── 批659 ㊽㊾㊿:操作員裁示的 ADJ 上漲空間(L99 的操作定義)──
    _c2 = _dd.connect(":memory:")
    _c2.execute("CREATE TABLE tw_daily_prices(date VARCHAR, ticker VARCHAR, close DOUBLE, adj_close DOUBLE)")
    _c2.execute("INSERT INTO tw_daily_prices VALUES "
                "('2026-05-18','6147.TWO',207.0,204.4523),"      # 報告日前一日:除過權息,因子 0.98769
                "('2026-09-18','6147.TWO',229.0,229.0),"          # 最新:adj==close(往回調,最新日因子恆 1)
                "('2026-05-18','9001.TWO',100.0,100.0),"          # 沒除權息:因子 1.0
                "('2026-09-18','9001.TWO',120.0,120.0)")
    _b = apply_adj_upside(_c2, {"ticker": "6147", "report_date": "2026-05-19", "target_price": 280.0})
    _b1 = apply_adj_upside(_c2, {"ticker": "9001", "report_date": "2026-05-19", "target_price": 150.0})
    chk("㊽ 批659 操作員裁示:目標價×因子 ÷ **最新** adj_close(不是報告日當時的價)。"
        "6147 實料手算:前一日 close 207.0 / adj 204.4523 → 因子 0.987692;280×0.987692=276.5538;"
        "÷ 最新 adj 229.0 = +20.8%(引擎與手算逐位吻合)",
        _b["upside_adj"] == 20.8 and abs(_b["adj_factor"] - 0.987692) < 1e-5
        and _b["target_price_adj"] == 276.5538 and _b["price_latest_adj"] == 229.0
        and _b["price_latest_date"] == "2026-09-18" and _b["upside_adj_state"] == "ADJ_OK",
        f"(因子 {_b['adj_factor']:.6f} · 目標adj {_b['target_price_adj']} · {_b['upside_adj']:+.1f}%)")
    chk("㊾ 批659 沒除權息時因子=1,目標價不動,但**仍用最新 adj 當分母**"
        "(150 ÷ 120 − 1 = +25.0%;算的是「從現在看還有多少空間」,不是報告當天的空間)",
        _b1["upside_adj"] == 25.0 and abs(_b1["adj_factor"] - 1.0) < 1e-9
        and _b1["target_price_adj"] == 150.0 and "因子1" in _b1["upside_adj_state"],
        f"({_b1['upside_adj']:+.1f}% · 態 {_b1['upside_adj_state']})")
    _n1 = apply_adj_upside(_c2, {"ticker": "6147", "report_date": "2026-05-19", "target_price": None})
    _n2 = apply_adj_upside(_c2, {"ticker": "7777", "report_date": "2026-05-19", "target_price": 100.0})
    _n3 = apply_adj_upside(_c2, {"ticker": "", "report_date": "", "target_price": 100.0})
    _n4 = apply_adj_upside(_c2, {"ticker": "6147", "report_date": "2026-05-19", "target_price": 1.0})
    _c2.close()
    chk("㊿ 批659 反例——四種「算不出」各有自己的名字,絕不編一個數字出來:"
        "沒目標價=ADJ_NO_TARGET · 沒這支股=ADJ_NO_FACTOR(上市所整個沒有 adj 價,30 件是這個) · "
        "沒代號/沒報告日=ADJ_NO_KEY · **目標價抽錯到荒謬比值=ADJ_ABSURD**"
        "(實測 3008 目標價被抽成 1.0,不擋就寫出 −100% 的升幅)",
        _n1["upside_adj_state"] == "ADJ_NO_TARGET" and _n1["upside_adj"] is None
        and _n2["upside_adj_state"] == "ADJ_NO_FACTOR" and _n2["upside_adj"] is None
        and _n3["upside_adj_state"] == "ADJ_NO_KEY" and _n3["upside_adj"] is None
        and _n4["upside_adj_state"].startswith("ADJ_ABSURD") and _n4["upside_adj"] is None,
        f"({_n1['upside_adj_state']} · {_n2['upside_adj_state']} · {_n3['upside_adj_state']} · {_n4['upside_adj_state'][:22]})")
    chk("⓫ 批659 兩個用途兩組欄,誰都不覆寫誰(只增不減):`price_db` 仍是 raw close(批240 裁示,"
        "拿來跟頁上現價對質);ADJ 走 upside_adj 等六個新欄;`price_state`/`upside_state` 字彙一個字不動",
        "SELECT close FROM tw_daily_prices" in src and '"upside_adj DOUBLE"' in src
        and "apply_adj_upside(con, basic)" in src and '"EXACT_MATCH_DB"' in src)
    # ── 批659 ⓬:動詞接得到 + 四面登錄在位(LL199;動詞宣告了沒接線 = 批425 那個家族)──
    _via = Path(__file__).resolve().parent.parent.parent
    _reg = sorted(_via.glob("Register-VIA-Commands-v*.ps1"))
    _cmd = _via / "via-repairprice.cmd"
    _reg_txt = _reg[-1].read_text(encoding="utf-8", errors="replace") if _reg else ""
    _real_argv = sys.argv
    try:                                        # 真的走一遍 CLI:動詞認不認得、乾跑會不會誤寫
        sys.argv = ["x", "repair-price", "--db", "/tmp/_nope_659_.duckdb"]
        _rc = main()
    finally:
        sys.argv = _real_argv
    chk("⓬ 批659 `repair-price` 動詞真的接得到(不是宣告了沒接線):庫不在=誠實 ABSENT rc3,不當綠也不爆;"
        "而且四面登錄在位——Register 尾版有 via-repairprice、根目錄有同名梭、梭不釘死版號",
        _rc == 3 and "via-repairprice" in _reg_txt and "repair-price" in _reg_txt
        and _cmd.is_file() and "_v0" not in _cmd.read_text(encoding="utf-8", errors="replace").split("setlocal")[-1],
        f"(rc={_rc} · 冊 {_reg[-1].name if _reg else '缺'} · 梭 {'在' if _cmd.is_file() else '缺'})")
    print(f"  [計] 四十四檢({len(done)} 檢) OK {len(done) - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


_argval = _CU_MOD.bind_argval(as_path=True)


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 報告結構化入庫引擎(VRN_ENG073 v0129)· 四十三檢自測(零網路)===")
        return selftest()
    if "--status" in args:
        return status(db=_argval(args, "--db"))
    if args and args[0] in ("repair-price", "repair_price"):
        # 批659:不擷取、零網路,只補庫價欄;沒有 --apply 一律乾跑(不代操作員決定寫庫)
        return repair_price(db=_argval(args, "--db"), apply="--apply" in args)
    if args and args[0] in ("purge-selftest", "purge"):
        return purge_selftest(apply="--apply" in args,
                              db=Path(args[args.index("--db") + 1]) if "--db" in args else None)
    if args and args[0] == "run":
        # 批425(實跑沙盒鏈時發現):v0114 以前這裡是 `return run()`——
        # run(zdir, db) 的簽名擺著,但 CLI 從來沒有解析過 --dir / --db,
        # 傳了不生效**也不吭聲**。兄弟引擎都有:ENG072 認 --dir、ENG074 認 --db,
        # 只有本器兩個都不認=無法把鏈指向另一個報告夾或另一個庫。
        # 與批423 的 $StageTimeoutSec 同一家族:宣告了、沒接線。
        return run(zdir=_argval(args, "--dir"), db=_argval(args, "--db"))
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
