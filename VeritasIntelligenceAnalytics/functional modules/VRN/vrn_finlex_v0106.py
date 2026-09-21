#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vrn_finlex_v0106 — 財務字庫收割引擎(TOOL-072)
====================================================================
v0105→v0106(批665 操作員授權「你決定 你覆核 你完成字洞」)
  批663 留下 19 欄辨識式 0 條、兩條車道都接不上,掛在 pending_operator。
  操作員把裁定權交下來。逐欄攤開之後,**19 個洞不是同一種洞** ——
  有些洞本來就不該有東西,填進去才是錯的。四條車道:

  ㉕ BRIDGE 10 欄 —— 冊上已經有一個「同一件事」而且帶著辨識式,接過去。
     憑據全部取自冊本身(共有中文同義字/en/field_map),零新造詞。
     其中兩欄要人判,不是機器判得出來的:
       · non_current_liabilities「非流動負債」——**候選演算法給錯了**。
         它算出來最像的是 other_noncurrent_liabilities「其他非流動負債」,
         因為這一欄的 synonyms_zh 誤收了「其他非流動負債」。**把總額接到子科目會算錯**。
         正解是 total_non_current_liabilities「非流動負債合計」。
       · shareholders_equity → total_equity 是**含非控制權益**的口徑;
         ROE 的分母要用 parent_equity(ENG074 v0112 docstring 記過這個坑)。已註記。
  ㉖ SYNTH 5 欄 —— 冊上沒有對應的有式鍵,就用**這一欄自己既有的同義字**合成辨識式。
     字全部是冊上本來就有的,一個新詞都沒造(長的排前面,免得
     「母公司業主權益」先吃掉「歸屬母公司業主權益」)。
  ㉗ DERIVED 3 欄 —— ebit / eps_qoq / sales_qoq 是**算出來的**,不是頁面上抓的。
     台灣財報沒有「EBIT」那一行;季增率也沒有一行印在那裡。
     給它們辨識式等於宣稱認得出一個不存在的東西 —— **那是假綠**。
     (年增率相反:eps_growth / revenue_growth 在冊上是有式的,研報真的會印,所以走 BRIDGE。)
  ㉘ DIMENSION 1 欄 —— period「年份/期間」不是財務數字,是維度;
     期間解析有 ENG074 的 PERIOD_RX 專門在做,這裡不該再開第二扇門(L101)。

  ㉙ same_as 改成**迭代收斂**:cfps → cashflow_per_share → operating_cf_per_share
     要走兩跳。單跳版本會讓 cfps 永遠接不上(它指到的那個自己也沒有式)。
     patterns_of 跟著鏈走,帶 visited 防迴圈,並回**整條路徑**不是只回終點 ——
     借了幾手要看得見。
====================================================================
v0104→v0105(批663 操作員令「分類整合同意自只增不減 ssot regex 同義字」):
  先量:操作員附的 InvestmentRegexPattern_VALIDATED.py 與倉內 functional
  modules/VRN/ 那一支**逐行相同**(只差 VIA 自己加的 14 行加速器橋),
  2026-08-05 已有 PROMOTION_RECORD。正本 141 PatternDef 499 式 + 6 條
  數字格式式,收割**一條不缺**——「缺 8 條」是我上一輪用鍵名直比的誤判
  (eps_basic 的 4 式早就在 basic_eps 底下,冊自己記著 merged_from)。
  真缺口在**下游**:VRN_Financial_Synonyms_SSOT 的 18 個正規名拿去冊裡
  查辨識式,**6 個走不到**(ebit/eps/ocf/op_profit 在冊但 patterns 0 條;
  eps_basic/eps_diluted 冊裡叫 basic_eps/diluted_eps)。料在 A,門開在 B,
  兩者沒有橋——L101「一個名字只能有一扇門」的反面。
  ㉑ 同一件事兩個鍵搭橋(只增不減:只寫新欄,既有值一個字不動;零新造詞):
     · A 車道 alias_index — 冊記 merged_from 反查(鍵被摺掉了,名字還在被喊)
     · B 車道 same_as    — 同中文名**逐字相同**、一邊有式一邊空
     兩條都只取冊上既有的字,不發明同義(LL90 裁定權在操作員)。
  ㉒ patterns_of() 查詢跟橋走,回「借自哪個鍵」,借來的看得見不假裝自有。
  ㉓ --reconcile 對帳動詞:正本↔冊逐條比 + 18 正規名走不走得到辨識式 +
     PENDING_OPERATOR 逐欄列名。晉升紀錄自報 525、正本實有 505——
     **一個沒有對帳器的數字,就只是一個看起來很負責的數字**。
  ㉔ 新冊 VRN_NumberFormat_Regex_v0100.json — 正本 NUMBER_PATTERNS 那 6 條
     是帶 capture group 的**擷取式**不是同義字,v0104 line 219 誠實跳過
     但沒給下一步(L92)。本版給它自己的冊,歸位但不混進同義冊。
     (NOTES 群 items 仍為 0:正本對財報附註本來就沒有式,那是誠實 NODATA)
====================================================================
v0103→v0104(批49 操作員核定回填):
  ⑪ 三語補齊冊 VRN_Canonical_Trilingual_Fill_v0100.json(操作員與
     AI 協作核定 195 條 canonical/中/英/報表)為權威回填源:
     zh/en 空欄或 backfilled 猜值→以核定值覆寫(operator_filled
     標註);statement 空→補;非空原源值不覆寫(單一真相不搶位)。
====================================================================
v0102→v0103(批48 Mega-Prompt Pipeline 2 SSOT 校準令):
  ① 退化條目摺疊 — CANON_MERGE:pe→pe_ratio/pb→pb_ratio/
     eps_basic→basic_eps/eps_diluted→diluted_eps(同義/來源/field_map
     全數併入目標條,零丟失;僅摺疊實證同義者,不發明)。
  ② 空欄回填 — zh/en 空者自同義清單首字補(zh 取首中文同義、
     en 取首英文同義),標 backfilled 註記。
  ③ 載入器消音 — 匯入 Summarizer 等正本時抑制 SyntaxWarning
     (docstring 逃逸字元屬正本原貌,不就地改;警訊在載入器端
     隔離,不再洗版工作站終端)。
====================================================================
v0101→v0102(批47:「可以一口氣問全部嗎」):
  ① --ask 多詞批查 — 一次給多個詞(空白/逗號分隔),一張 rich
     矩陣回全部命中(BROKER/RATING/FINDATA/FINSTMT 四域同掃)。
  ② --all 全冊總覽 — 五冊一口氣:rich 總覽矩陣+理印 HTML 全覽頁
     VIA_Reports/VIA_UI_FinLex.html(196 canonical 全表/broker 雙層
     /評等四級/報表七類/regex 38 式;銘言刊頭;--no-open 不開)。
====================================================================
操作員令(批44,2026-08-19):「broker dict / 財務數據中英文同義字庫
/ 財務報表同義字庫」。
v0100→v0101(批45 五件上傳擴源):
  ⑥ financial_classification_rules(VeritasSynonymEngine v3.0):
     52 指標×四源欄位(twse_tpex/twstock/yfinance/synonyms)併入
     財務數據冊 field_map;BROKER_LIST 32 家(code/en/zh/aliases/
     country/type)入 brokers_extended;RATING_DICT 四級+TickerRegex
     18 式+DateTimeRegex 20 式各立新冊。
  ⑦ financial_data_standardization:合併損傷件(class 先於 imports,
     import 即 NameError)→ AST 零執行收割 FinancialFieldMapping
     kwargs(synonyms+validation_rules)+RATING_KEYWORDS 六集。
  ⑧ financial_metrics_mapping.md:57 指標對照表(pipe table)解析
     併入(截斷尾「...」token 誠實丟棄)。
  新冊:VRN_Rating_Dict_v0100.json / VRN_TickerDate_Regex_v0100.json。
  CamelCase→snake+別名折疊(cost_of_revenue→cogs 等,僅折疊到既存
  canonical,不發明)。
原則:
  ① AI 只整理不發明 — 三字庫全部收割自倉內既有正本,逐條標來源:
     · broker dict ← VRN_ENG062 Summarizer BROKER_ABBR_DICT(29 家)
     · 財務數據同義 ← InvestmentRegexPattern 庫 141 項(zh/en/regex)
       + MDL007 MOPS_ACCOUNT_MAP(官方科目名)+ MDL008
       SYNONYM_FALLBACK(canonical 別名)+ 方法冊 def05
     · 財務報表同義 ← pattern 庫 StatementType×七 dict 歸屬
  ② 單一真相 — 三冊落 knowledge/ 為 SSOT,入中央參數樞紐;
     來源引擎不改(唯讀收割)。
  ③ 衝突誠實 — 同 canonical 多源並列保存(sources 欄),不仲裁。
用法:
  via-finlex --build       → 收割並落三冊+rich 矩陣
  via-finlex --ask <詞>    → 跨三冊查詢(中英同義反查 canonical)
  via-finlex --reconcile   → 正本↔冊對帳(批663;誠實 rc 0/1/2/3/4)
  via-finlex --rulings     → 批665 十九欄裁定逐欄攤開(車道/去向/憑據)
  via-finlex --selftest    → 三十檢(沙盒零網路)
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

import importlib.util
import json
import ast
import re
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
KNOW = HERE / "knowledge"
BOOK_BROKER = KNOW / "VRN_Broker_Dict_v0100.json"
BOOK_FINDATA = KNOW / "VRN_FinData_Synonym_v0100.json"
BOOK_FINSTMT = KNOW / "VRN_FinStatement_Synonym_v0100.json"
BOOK_RATING = KNOW / "VRN_Rating_Dict_v0100.json"
BOOK_TICKDATE = KNOW / "VRN_TickerDate_Regex_v0100.json"
BOOK_NUMFMT = KNOW / "VRN_NumberFormat_Regex_v0100.json"   # 批663 新冊

# CamelCase→snake 後的別名折疊表(僅折疊到既存 canonical,不發明)
CANON_ALIAS = {"cost_of_revenue": "cogs", "operating_profit": "operating_income",
               "pre_tax_income": "pretax_income", "operating_cash_flow": "operating_cf",
               "investing_cash_flow": "investing_cf", "financing_cash_flow": "financing_cf",
               "cap_ex": "capex", "income_before_tax": "pretax_income",
               "operating_cashflow": "operating_cf", "investing_cashflow": "investing_cf",
               "financing_cashflow": "financing_cf", "return_on_equity": "roe",
               "return_on_assets": "roa"}


def camel2snake(k: str) -> str:
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", "_", k).lower()


def _metric_rec(metrics: dict, key: str) -> dict:
    return metrics.setdefault(key, {"zh": "", "en": "", "synonyms_zh": [],
                                    "synonyms_en": [], "patterns": [],
                                    "statement": "", "category": "", "unit": "",
                                    "validation_level": "", "sources": []})


def _merge_syns(rec: dict, syns, src: str) -> None:
    for s in syns:
        s = str(s).strip()
        if not s or s.endswith("..."):  # md 截斷尾 token 誠實丟棄
            continue
        tgt = "synonyms_zh" if _CJK.search(s) else "synonyms_en"
        if s not in rec[tgt]:
            rec[tgt].append(s)
    if src not in rec["sources"]:
        rec["sources"].append(src)

STMT_ZH = {"BALANCE_SHEET": ("資產負債表", "Balance Sheet",
                             ["資產負債表", "Balance Sheet", "財務狀況表", "Statement of Financial Position"]),
           "INCOME_STATEMENT": ("損益表", "Income Statement",
                                ["損益表", "綜合損益表", "Income Statement", "P&L", "Statement of Comprehensive Income"]),
           "CASH_FLOW": ("現金流量表", "Cash Flow Statement",
                         ["現金流量表", "Cash Flow Statement", "Statement of Cash Flows"]),
           "EQUITY_CHANGE": ("權益變動表", "Statement of Changes in Equity",
                             ["權益變動表", "股東權益變動表", "Statement of Changes in Equity"]),
           "RATIO": ("財務比率", "Financial Ratios", ["財務比率", "比率分析", "Financial Ratios"]),
           "PER_SHARE": ("每股分析", "Per-Share Metrics", ["每股分析", "每股指標", "Per Share"]),
           "NOTES": ("附註", "Notes", ["附註", "Notes"])}

_CJK = re.compile(r"[一-鿿]")


def _load(name: str, path: Path):
    import warnings
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod  # dataclass 解析需先掛名(MDL 家族 loader 同法)
    with warnings.catch_warnings():
        # 正本 docstring 逃逸字元屬原貌(不就地改);警訊載入器端隔離
        warnings.simplefilter("ignore", SyntaxWarning)
        spec.loader.exec_module(mod)
    return mod


# 批48 Pipeline 2:退化條目摺疊表(僅摺疊實證同義者,不發明)
CANON_MERGE = {"pe": "pe_ratio", "pb": "pb_ratio",
               "eps_basic": "basic_eps", "eps_diluted": "diluted_eps"}


def fold_degenerates(metrics: dict) -> int:
    """同義/來源/field_map 全併入目標條(零丟失);空 zh/en 自同義回填"""
    n = 0
    for src, dst in CANON_MERGE.items():
        if src in metrics and dst in metrics:
            s, d = metrics.pop(src), metrics[dst]
            for f in ("synonyms_zh", "synonyms_en", "patterns", "sources"):
                for x in s.get(f, []):
                    if x not in d.setdefault(f, []):
                        d[f].append(x)
            for k, v in s.get("field_map", {}).items():
                d.setdefault("field_map", {}).setdefault(k, v)
            for f in ("zh", "en", "unit", "statement", "category"):
                if not d.get(f) and s.get(f):
                    d[f] = s[f]
            d.setdefault("merged_from", []).append(src)
            n += 1
    for m in metrics.values():  # 空欄回填
        if not m.get("zh") and m.get("synonyms_zh"):
            m["zh"] = m["synonyms_zh"][0]
            m["zh_backfilled"] = True
        if not m.get("en") and m.get("synonyms_en"):
            m["en"] = m["synonyms_en"][0]
            m["en_backfilled"] = True
    return n



# ═══ 批663:同一件事兩個鍵,料在 A、門開在 B —— 搭橋(只增不減,零新造詞)═══
def derive_same_as(metrics: dict) -> tuple[int, dict, list]:
    """辨識式空的鍵 → 指向有式的同一件事。

    兩條車道,**都只取冊上既有的字**,一個同義詞也不發明(LL90 裁定權在操作員):
      · A alias_index — 冊自己記的 merged_from 反查。鍵被 fold_degenerates 摺掉了,
        名字卻還在被上游喊(SSOT 吐 eps_basic,冊裡叫 basic_eps)。
      · B same_as     — 同中文名**逐字相同**、一邊有辨識式一邊空。
        逐字相同才算:「營業現金流」≠「營業活動現金流」,那是操作員的裁定,不是我的。
    只寫 same_as / same_as_basis 兩個新欄,既有欄位一個字不動。
    兩條車道都接不上的,入 pending_operator 逐欄列名——待裁定要有人讀得到(LL305)。
    """
    alias_index: dict = {}
    for dst, rec in metrics.items():
        if not rec.get("patterns"):
            continue
        for old in rec.get("merged_from", []) or []:
            if old not in metrics:                    # 鍵真的被摺掉了才需要這座橋
                alias_index.setdefault(old, dst)
    by_zh: dict = {}
    for k, v in metrics.items():
        if v.get("zh") and v.get("patterns"):
            by_zh.setdefault(v["zh"], k)
    # 批665:單跳不夠。cfps →(同名)cashflow_per_share →(同義)operating_cf_per_share,
    #   要走兩跳。第一版只認「指到的那個有式」,於是 cfps 永遠接不上——
    #   它指到的那個自己也沒式。**迭代到不動點**:剛接好的也算「走得到式」。
    n = 0
    for _round in range(8):                       # 上限是防呆,不是期待;8 跳還沒收斂就是有環
        moved = 0
        reach = {k for k, v in metrics.items() if v.get("patterns")}
        reach |= {k for k, v in metrics.items() if v.get("same_as")}
        by_zh2 = dict(by_zh)
        for k, v in metrics.items():
            if k in reach and v.get("zh") and v["zh"] not in by_zh2:
                by_zh2[v["zh"]] = k
        for k, v in metrics.items():
            if v.get("patterns") or v.get("same_as"):
                continue
            tgt = by_zh2.get(v.get("zh") or "\u0000")
            if tgt and tgt != k:
                v["same_as"] = tgt
                v["same_as_basis"] = "同中文名逐字相同"
                n += 1
                moved += 1
        if not moved:
            break
    pending = sorted(k for k, v in metrics.items()
                     if not v.get("patterns") and not v.get("same_as"))
    return n, alias_index, pending


# ═══ 批665:十九個字洞的裁定(操作員授權「你決定 你覆核 你完成」)═══
# 每一筆都帶憑據,而且**每一筆都能被一眼推翻** —— 看 why 那一行就夠(LL90 的精神:
# 裁定權轉手了,留痕的義務沒有轉手)。推不出憑據的我不填。
#
# 車道四種,因為**19 個洞不是同一種洞**:
#   BRIDGE     冊上已經有一個「同一件事」而且帶辨識式 → 接過去(單一出處最好)
#   SYNTH      冊上沒有對應的有式鍵 → 用這一欄**自己既有的同義字**合成(零新造詞)
#   DERIVED    推導欄:算出來的,頁面上本來就沒有那一行 → **不給辨識式**
#   DIMENSION  維度欄:不是財務數字 → 不在這本冊開第二扇門
RULED_B665 = {
    # ── BRIDGE 10:去向 + 憑據 ──────────────────────────────────────────
    "capital_expenditure": ("BRIDGE", "capex",
                            "冊上 capex(購置不動產廠房設備·7 式)的同義字本來就含「資本支出」"),
    "cashflow_per_share": ("BRIDGE", "operating_cf_per_share",
                           "本欄 synonyms_zh 自己就寫著「每股營業現金流」——冊自己認的,不是我認的"),
    "cfps": ("BRIDGE", "cashflow_per_share",
             "與 cashflow_per_share 中文名逐字相同(都是「每股現金流」);"
             "它自己也沒式,所以要**再跳一手**到 operating_cf_per_share"),
    "eps_yoy": ("BRIDGE", "eps_growth",
                "共有字「eps年增率」;年增率研報真的會印,eps_growth 有 3 式"),
    "operating_cost": ("BRIDGE", "cost_of_sales",
                       "共有「營業成本」「銷貨成本」兩個字;cost_of_sales 5 式 > cogs 1 式"),
    "sales_yoy": ("BRIDGE", "revenue_growth",
                  "共有字「營收年增率」;revenue_growth 5 式"),
    "share_capital": ("BRIDGE", "common_stock",
                      "共有三個字「股本」「實收資本」「普通股股本」;common_stock 7 式"),
    "shareholders_equity": ("BRIDGE", "total_equity",
                            "共有「權益合計」「股東權益」「淨值」。**口徑註記:total_equity 是"
                            "「權益總計」= 含非控制權益**;ROE 的分母要用 parent_equity,"
                            "拿總權益當分母 ROE 會偏低而且看起來完全正常"
                            "(ENG074 v0112 docstring 記過這個坑)"),
    "ocf": ("BRIDGE", "operating_cash_flow",
            "三個名字指同一件事(ocf「營業現金流」· operating_cf「營業活動現金流」1 式 ·"
            " operating_cash_flow「營業活動淨現金流入(出)」4 式)。取式最多、而且它的中文名"
            "正是財報上那一行的正式寫法"),
    "non_current_liabilities": ("BRIDGE", "total_non_current_liabilities",
                                "**候選演算法在這裡給錯了**:它算出最像的是"
                                "other_noncurrent_liabilities「其他非流動負債」,因為本欄的"
                                "synonyms_zh 誤收了那五個字。**總額接到子科目會算錯。**"
                                "「非流動負債」對應的是「非流動負債合計」(3 式)"),
    # ── SYNTH 5:冊上沒有對應有式鍵,用自己既有的同義字合成 ──────────────
    "debt_change": ("SYNTH", "",
                    "現金流量表真的有這一行,但正本沒給式;冊上也沒有「長借公司債變動」的有式鍵"
                    "(long_term_borrowings 是**餘額**不是**變動**,接過去會把存量當流量)"),
    "long_term_investment_change": ("SYNTH", "",
                                    "冊上 long_term_investment「長期投資」是**餘額**,"
                                    "本欄是**變動**;接過去會把存量當流量"),
    "working_capital_change": ("SYNTH", "", "冊上零對應鍵;自冊上既有同義字合成"),
    "diluted_shares": ("SYNTH", "",
                       "field_map 已有 twse_tpex「稀釋後股數」;diluted_eps 是**每股盈餘**"
                       "不是**股數**,不接"),
    "parent_equity": ("SYNTH", "",
                      "**不接 total_equity** —— 那是含非控制權益的總額,本欄是歸屬母公司。"
                      "接過去會讓 ROE 分母悄悄換掉(同 shareholders_equity 那一條的反面)"),
    # ── DERIVED 3:算出來的,頁面上沒有那一行 ────────────────────────────
    "ebit": ("DERIVED", "operating_income + 營業外收支(非利息非稅)",
             "台灣財報**沒有「EBIT」這一行**。給它辨識式等於宣稱認得出一個不存在的東西,"
             "那是假綠。接到 operating_income 也不對:兩者不相等(差在營業外收支)"),
    "eps_qoq": ("DERIVED", "eps 本季 ÷ eps 上季 − 1",
                "季增率沒有一行印在報表上(年增率相反,研報會印「每股盈餘成長率」,"
                "所以 eps_yoy 走 BRIDGE)"),
    "sales_qoq": ("DERIVED", "revenue 本季 ÷ revenue 上季 − 1",
                  "同 eps_qoq:季增率沒有一行印在報表上。「同上」這種憑據在單獨看這一列時"
                  "等於沒有憑據(L96 舉證要能整份帶走),所以寫全"),
    # ── DIMENSION 1:不是財務數字 ───────────────────────────────────────
    "period": ("DIMENSION", "VRN_ENG074 PERIOD_RX",
               "「年份/期間」是**維度**不是科目。期間解析已經有專門的一扇門,"
               "這本冊再開一扇就是 L101 的反面"),
}
_RULE_LANES = ("BRIDGE", "SYNTH", "DERIVED", "DIMENSION")


def synth_pattern(rec: dict) -> str:
    """用這一欄**自己既有的**同義字合成辨識式。一個新詞都不造。

    長的排前面:不然「母公司業主權益」會先吃掉「歸屬母公司業主權益」,
    交替比對的結果是**比較短的那個贏**,而短的那個常常是錯的科目。
    """
    meta = set(r"\^$.|?*+()[]{}")
    words = list(rec.get("synonyms_zh") or [])
    words += list(rec.get("synonyms_en") or [])
    words += [v for v in (rec.get("field_map") or {}).values() if isinstance(v, str)]
    words += list(rec.get("mops_official") or [])
    if rec.get("zh"):
        words.append(rec["zh"])
    seen, clean = set(), []
    for w in words:
        w = str(w).strip()
        if not w or w in seen or any(c in meta for c in w):
            continue                       # 已經是 regex 的不重複包、帶元字元的不進來
        seen.add(w)
        clean.append(w)
    clean.sort(key=lambda x: (-len(x), x))
    return "(" + "|".join(re.escape(w) for w in clean) + ")" if clean else ""


def apply_rulings(metrics: dict) -> dict:
    """把批665 的裁定落到冊上。只增不減:只寫新欄,既有值一個字不動。"""
    tally = {k: 0 for k in _RULE_LANES}
    for key, (lane, tgt, why) in RULED_B665.items():
        rec = metrics.get(key)
        if rec is None:
            continue
        rec["ruled_b665"] = {"lane": lane, "target": tgt, "why": why,
                             "ruled_by": "AI 代裁(批665 操作員授權「你決定 你覆核 你完成字洞」)"}
        if lane == "BRIDGE" and tgt and tgt in metrics:
            if not rec.get("patterns"):
                rec["same_as"] = tgt
                rec["same_as_basis"] = "批665 裁定:" + why[:60]
        elif lane == "SYNTH":
            if not rec.get("patterns"):
                px = synth_pattern(rec)
                if px:
                    rec["patterns"] = [px]
                    rec["patterns_synth_b665"] = True   # 合成的看得見,不假裝是正本給的
        # DERIVED / DIMENSION:**刻意不給辨識式**,理由寫在 ruled_b665.why
        tally[lane] += 1
    return tally


def patterns_of(book: dict, key: str) -> tuple[list, str]:
    """查一個鍵的辨識式,跟橋走。回 (式, 借自哪個鍵);自有式時借自為空字串。

    借來的**看得見**——不把別人的式當成自己的,免得下游以為這一欄本來就認得出。
    """
    metrics = book.get("metrics", {})
    src = ""
    if key not in metrics:
        tgt = book.get("alias_index", {}).get(key)
        if not tgt:
            return [], ""
        key, src = tgt, tgt
    # 批665:跟**整條鏈**走(cfps → cashflow_per_share → operating_cf_per_share),
    #   帶 visited 防迴圈,回的是整條路徑不是只回終點——借了幾手要看得見。
    seen, hops = {key}, ([src] if src else [])
    cur = key
    for _ in range(8):
        rec = metrics.get(cur, {})
        pats = rec.get("patterns") or []
        if pats:
            return list(pats), "→".join(hops) if hops else ""
        nxt = rec.get("same_as")
        if not nxt or nxt in seen or nxt not in metrics:
            break
        seen.add(nxt)
        hops.append(nxt)
        cur = nxt
    return [], "→".join(hops) if hops else src


def _numfmt_harvest(irp_path: Path) -> dict:
    """正本 NUMBER_PATTERNS 那 6 條是帶 capture group 的**擷取式**,不是欄位同義字。

    AST 讀 re.compile(r'…') 的第一個引數,零執行(正本自帶一套加速器注入,
    執行等於在樹上引進第二套加速器 —— Zero-Hydra)。
    """
    out: dict = {}
    if not irp_path.exists():
        return out
    try:
        tree = ast.parse(irp_path.read_text(encoding="utf-8-sig"))
    except Exception:
        return out
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        tgts = [t.id for t in node.targets if isinstance(t, ast.Name)]
        if "NUMBER_PATTERNS" not in tgts or not isinstance(node.value, ast.Dict):
            continue
        for k_, v_ in zip(node.value.keys, node.value.values):
            if not isinstance(k_, ast.Constant) or not isinstance(v_, ast.Call):
                continue
            if not v_.args or not isinstance(v_.args[0], ast.Constant):
                continue
            rx = v_.args[0].value
            try:
                re.compile(rx)
            except re.error:
                continue                              # 編不過的不入冊(誠實)
            out[str(k_.value)] = rx
    return out

def newest(pattern: str) -> Path | None:
    hits = sorted(HERE.glob(pattern))
    return hits[-1] if hits else None


def harvest() -> tuple[dict, dict, dict, dict]:
    """回 (broker冊, 財務數據冊, 財務報表冊, 來源盤點)"""
    srcs = {}
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ── 來源一:Summarizer broker dict ──
    sum_p = newest("VRN_ENG062_Summarizer*.py") or newest("VRN_Summarizer_v*.py")
    summ = _load("vrn_sum_lex", sum_p)
    srcs["broker"] = sum_p.name
    brokers = {zh: {"abbr": ab, "source": sum_p.name}
               for zh, ab in summ.BROKER_ABBR_DICT.items()}
    book_broker = {"schema": "VIA.VRN.BrokerDict.v1", "generated": ts,
                   "policy": "AI 只整理不發明;逐條標來源;正本=Summarizer BROKER_ABBR_DICT",
                   "count": len(brokers), "brokers": brokers}

    # ── 來源二:InvestmentRegexPattern 庫(141 項)──
    irp_p = HERE / "InvestmentRegexPattern_VALIDATED.py"
    irp = _load("vrn_irp_lex", irp_p)
    srcs["patterns"] = irp_p.name
    dict_stmt = [("BALANCE_SHEET_PATTERNS", "BALANCE_SHEET"),
                 ("INCOME_STATEMENT_PATTERNS", "INCOME_STATEMENT"),
                 ("CASH_FLOW_PATTERNS", "CASH_FLOW"),
                 ("EQUITY_CHANGE_PATTERNS", "EQUITY_CHANGE"),
                 ("RATIO_PATTERNS", "RATIO"),
                 ("PER_SHARE_PATTERNS", "PER_SHARE"),
                 ("NUMBER_PATTERNS", "NUMBER")]
    metrics: dict[str, dict] = {}
    stmt_items: dict[str, list] = {}
    for dname, stmt in dict_stmt:
        for key, pd_ in getattr(irp, dname).items():
            if not hasattr(pd_, "patterns"):  # NUMBER_PATTERNS=裸 regex(數字格式非同義字),誠實跳過
                continue
            zh_syn = sorted({p for p in pd_.patterns if _CJK.search(p)})
            en_syn = sorted({p for p in pd_.patterns if not _CJK.search(p)})
            metrics[key] = {
                "zh": pd_.name, "en": pd_.name_en,
                "synonyms_zh": zh_syn, "synonyms_en": en_syn,
                "patterns": list(pd_.patterns),
                "statement": stmt, "category": pd_.category.name,
                "unit": pd_.unit,
                "validation_level": pd_.validation_level.name,
                "sources": [irp_p.name],
            }
            stmt_items.setdefault(stmt, []).append(key)

    # ── 來源三:MDL007 MOPS 官方科目名 ──
    m7p = HERE / "VRN_MDL007_APIDataFetcher.py"
    if m7p.exists():
        m7 = _load("vrn_m7_lex", m7p)
        srcs["mops"] = m7p.name
        for official, canon in m7.MOPS_ACCOUNT_MAP.items():
            rec = metrics.setdefault(canon, {"zh": "", "en": "", "synonyms_zh": [],
                                             "synonyms_en": [], "patterns": [],
                                             "statement": "", "category": "",
                                             "unit": "", "validation_level": "",
                                             "sources": []})
            if official not in rec["synonyms_zh"]:
                rec["synonyms_zh"].append(official)
            rec.setdefault("mops_official", []).append(official)
            if m7p.name not in rec["sources"]:
                rec["sources"].append(m7p.name)

    # ── 來源四:MDL008 canonical 別名 ──
    m8p = HERE / "VRN_MDL008_CrossValidator.py"
    if m8p.exists():
        m8 = _load("vrn_m8_lex", m8p)
        srcs["aliases"] = m8p.name
        for canon, aliases in m8.SYNONYM_FALLBACK.items():
            rec = metrics.setdefault(canon, {"zh": "", "en": "", "synonyms_zh": [],
                                             "synonyms_en": [], "patterns": [],
                                             "statement": "", "category": "",
                                             "unit": "", "validation_level": "",
                                             "sources": []})
            for a in aliases:
                if a not in rec["synonyms_en"]:
                    rec["synonyms_en"].append(a)
            rec.setdefault("mdl008_aliases", []).extend(aliases)
            if m8p.name not in rec["sources"]:
                rec["sources"].append(m8p.name)

    # ── 來源五:方法冊 def05 ──
    mth_p = KNOW / "VRN_Method_SSOT_v0100.json"
    if mth_p.exists():
        mth = json.loads(mth_p.read_text(encoding="utf-8-sig"))
        srcs["method"] = mth_p.name
        for canon, syns in mth["def05_canonical_fields"].items():
            if not isinstance(syns, list):
                continue
            rec = metrics.setdefault(canon, {"zh": "", "en": "", "synonyms_zh": [],
                                             "synonyms_en": [], "patterns": [],
                                             "statement": "", "category": "",
                                             "unit": "", "validation_level": "",
                                             "sources": []})
            for s in syns:
                tgt = "synonyms_zh" if _CJK.search(s) else "synonyms_en"
                if s not in rec[tgt]:
                    rec[tgt].append(s)
            if mth_p.name not in rec["sources"]:
                rec["sources"].append(mth_p.name)

    # ── 來源六:financial_classification_rules(VeritasSynonymEngine v3.0)──
    book_rating = {"schema": "VIA.VRN.RatingDict.v1", "generated": ts,
                   "policy": "評等字庫;收割自倉內正本,逐節標來源", "levels": {}, "keyword_sets": {}}
    book_tickdate = {"schema": "VIA.VRN.TickerDateRegex.v1", "generated": ts,
                     "policy": "多市場 ticker+日期時間 regex 冊;TW 寬鬆式不入 LOCKED 圈(LOCKED 正本在 Regex 治理中心)",
                     "ticker_patterns": {}, "datetime_patterns": {}}
    fcr_p = HERE / "financial_classification_rules.py"
    if fcr_p.exists():
        fcr = _load("vrn_fcr_lex", fcr_p)
        srcs["classification"] = fcr_p.name
        for key, feat in fcr.get_all_features().items():
            snake = camel2snake(key)
            canon = CANON_ALIAS.get(snake, snake)
            if canon not in metrics and snake in metrics:
                canon = snake
            rec = _metric_rec(metrics, canon)
            _merge_syns(rec, feat.get("synonyms", []), fcr_p.name)
            fm = rec.setdefault("field_map", {})
            for src_col in ("twse_tpex", "twstock", "yfinance"):
                v = feat.get(src_col, "")
                if v and v != "--" and src_col not in fm:
                    fm[src_col] = v
            if not rec["patterns"] and feat.get("regex"):
                rec["patterns"] = [feat["regex"]]
        book_broker["brokers_extended"] = fcr.BROKER_LIST
        book_broker["extended_source"] = fcr_p.name
        for b in fcr.BROKER_LIST:  # zh 相符者 aliases 併回主冊
            zh_short = next((z for z in brokers if z and z in b["zh"]), None)
            if zh_short:
                brokers[zh_short].setdefault("aliases", [])
                for a in b["aliases"]:
                    if a not in brokers[zh_short]["aliases"]:
                        brokers[zh_short]["aliases"].append(a)
        book_broker["count_extended"] = len(fcr.BROKER_LIST)
        for cat, d in fcr.RATING_DICT.items():
            book_rating["levels"][cat] = {"level": d["level"], "sentiment": d["sentiment"],
                                          "score_range": list(d["score_range"]),
                                          "zh": d["zh"], "en": d["en"],
                                          "source": fcr_p.name}
        # TW_* 寬鬆式掛 LOOSE_ 前綴:非 LOCKED 定義競爭者,避免與治理中心
        # 同名撞鍵誤觸 DRIFT(LOCKED 嚴格式正本在 Regex 治理中心)
        book_tickdate["ticker_patterns"] = {
            (f"LOOSE_{k}" if k.startswith("TW_") else k): p.pattern
            for k, p in fcr.TickerRegex.get_all_patterns().items()}
        book_tickdate["datetime_patterns"] = {k: p.pattern for k, p in
                                              fcr.DateTimeRegex.get_all_patterns().items()}
        book_tickdate["source"] = fcr_p.name

    # ── 來源七:financial_data_standardization(合併損傷件→AST 零執行收割)──
    fds_p = HERE / "financial_data_standardization.py"
    if fds_p.exists():
        import ast as _ast
        try:
            tree = _ast.parse(fds_p.read_text(encoding="utf-8", errors="replace"))
            srcs["standardization"] = f"{fds_p.name}(AST)"
            n_fds = 0
            for node in _ast.walk(tree):
                if (isinstance(node, _ast.Call) and isinstance(node.func, _ast.Name)
                        and node.func.id == "FinancialFieldMapping"):
                    kw = {k.arg: k.value for k in node.keywords}
                    try:
                        zh = _ast.literal_eval(kw.get("chinese_name")) if "chinese_name" in kw else ""
                        syns = _ast.literal_eval(kw.get("synonyms")) if "synonyms" in kw else []
                        rules = _ast.literal_eval(kw.get("validation_rules")) if "validation_rules" in kw else []
                        yff = _ast.literal_eval(kw.get("yfinance_field")) if "yfinance_field" in kw else ""
                    except Exception:
                        continue
                    hit = next((c for c, m in metrics.items()
                                if m.get("zh") == zh or zh in m.get("synonyms_zh", [])
                                or m.get("field_map", {}).get("yfinance") == yff), None)
                    if hit is None:
                        continue  # 只併既存 canonical,不發明
                    rec = metrics[hit]
                    _merge_syns(rec, [zh, *syns], f"{fds_p.name}(AST)")
                    vr = rec.setdefault("validation_rules", [])
                    for r_ in rules:
                        if r_ not in vr:
                            vr.append(r_)
                    n_fds += 1
                if (isinstance(node, _ast.Assign) and node.targets
                        and isinstance(node.targets[0], _ast.Name)
                        and node.targets[0].id == "RATING_KEYWORDS"):
                    try:
                        book_rating["keyword_sets"] = _ast.literal_eval(node.value)
                        book_rating["keyword_sets_source"] = f"{fds_p.name}(AST)"
                    except Exception:
                        pass
            srcs["standardization"] += f"·併 {n_fds} 欄"
        except SyntaxError:
            srcs["standardization"] = f"{fds_p.name}(SKIP:語法敗,誠實)"

    # ── 來源八:financial_metrics_mapping.md(57 指標 pipe table)──
    md_p = KNOW / "source_docs" / "financial_metrics_mapping.md"
    if md_p.exists():
        n_md = 0
        for line in md_p.read_text(encoding="utf-8-sig").splitlines():
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 6 or cells[0] in ("中文名稱", "") or set(cells[0]) <= {"-"}:
                continue
            zh, en, twse, twstock, yf_, syn_raw = cells[:6]
            snake = CANON_ALIAS.get(twstock, twstock)
            canon = snake if snake in metrics else (twstock if twstock in metrics else None)
            if canon is None:
                canon = snake  # 新指標(如 payout_ratio/sps)以 twstock snake 名立條
            rec = _metric_rec(metrics, canon)
            if not rec["zh"]:
                rec["zh"] = zh
            if not rec["en"]:
                rec["en"] = en
            syns = [s for s in re.split(r"[,、]", syn_raw) if s.strip()]
            _merge_syns(rec, [zh, en, *syns], md_p.name)
            fm = rec.setdefault("field_map", {})
            for col, v in [("twse_tpex", twse), ("twstock", twstock), ("yfinance", yf_)]:
                if v and v not in ("--", "（計算值）", "（市場數據）", "（期間識別）") and col not in fm:
                    fm[col] = v
            n_md += 1
        srcs["mapping_md"] = f"{md_p.name}·{n_md} 列"

    # ── 來源九:70_VRN_Rules 帳目 SSOT(動態解析最新版;list/dict 雙形容)──
    rules_dir = VIA_RULES if (VIA_RULES := HERE.parent.parent / "supportive modules" / "70_VRN_Rules").exists() else None
    if rules_dir:
        hits9 = sorted(rules_dir.glob("VIS_VRN_FinancialSSOT_v0*.py"))
        if hits9:
            try:
                m9 = _load("vrn_v0608_lex", hits9[-1])
                raw9 = next((getattr(m9, a) for a in dir(m9)
                             if a.startswith("VRN_FINANCIAL_ACCOUNT_SSOT") and not a.endswith("_VERSION")), None)
                accounts = raw9.get("accounts", []) if isinstance(raw9, dict) else (raw9 or [])
                n9 = 0
                for acc in accounts:
                    name = acc.get("data_official_en") or acc.get("canonical", "")
                    if not name:
                        continue
                    snake = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
                    canon = {"p_e": "pe_ratio", "p_b": "pb_ratio",
                             "cash_and_cash_equivalents": "cash",
                             "property_plant_and_equipment": "ppe"}.get(snake, snake)
                    canon = CANON_ALIAS.get(canon, canon)
                    if canon not in metrics and snake in metrics:
                        canon = snake
                    rec = _metric_rec(metrics, canon)
                    _merge_syns(rec, [name, *acc.get("aliases", [])], hits9[-1].name)
                    if not rec["unit"]:
                        rec["unit"] = acc.get("default_unit", acc.get("unit", ""))
                    if acc.get("uid") and "vrn_uid" not in rec:
                        rec["vrn_uid"] = acc["uid"]
                    n9 += 1
                srcs["account_ssot"] = f"{hits9[-1].name}·{n9} 科目(唯讀;凍結件零觸碰)"
            except Exception as exc:
                srcs["account_ssot"] = f"{hits9[-1].name}(SKIP:{str(exc)[:40]})"

    # ── 來源十:VRN_Financial_Synonyms_SSOT(METRIC_SYNONYMS alias→canonical)──
    syn_p = HERE / "VRN_Financial_Synonyms_SSOT.py"
    if syn_p.exists():
        try:
            m10 = _load("vrn_syn_ssot_lex", syn_p)
            n10 = 0
            for alias, canon0 in m10.METRIC_SYNONYMS.items():
                canon = CANON_ALIAS.get(canon0, canon0)
                if canon not in metrics and canon0 in metrics:
                    canon = canon0
                rec = _metric_rec(metrics, canon)
                _merge_syns(rec, [alias], syn_p.name)
                n10 += 1
            srcs["synonyms_ssot"] = f"{syn_p.name}·{n10} 別名(另載 SECTOR/CURRENCY/UNIT/REPORT_TYPE 四錨)"
        except Exception as exc:
            srcs["synonyms_ssot"] = f"{syn_p.name}(SKIP:{str(exc)[:40]})"

    n_fold = fold_degenerates(metrics)  # 批48 Pipeline 2:摺疊+回填
    # ── 來源十一:操作員核定三語補齊冊(批49;權威回填)──
    fill_p = KNOW / "VRN_Canonical_Trilingual_Fill_v0100.json"
    if fill_p.exists():
        fills = json.loads(fill_p.read_text(encoding="utf-8-sig"))["fills"]
        n11 = 0
        for canon, f in fills.items():
            if canon not in metrics:
                continue
            m = metrics[canon]
            hit = False
            if f["zh"] and (not m.get("zh") or m.pop("zh_backfilled", None)):
                m["zh"] = f["zh"]; hit = True
            if f["en"] and (not m.get("en") or m.pop("en_backfilled", None)):
                m["en"] = f["en"]; hit = True
            if f["statement"] and not m.get("statement"):
                m["statement"] = f["statement"]; hit = True
            if hit:
                m["operator_filled"] = True
                if fill_p.name not in m["sources"]:
                    m["sources"].append(fill_p.name)
                n11 += 1
        srcs["operator_fill"] = f"{fill_p.name}·核定回填 {n11} 條(權威源)"

    # ── 批665:先落裁定(BRIDGE 指去向 / SYNTH 合成式 / DERIVED·DIMENSION 刻意不給式)
    #    再讓批663 的通用搭橋收尾。次序不能反:通用搭橋會把「同中文名」的接走,
    #    而 non_current_liabilities 那一欄同中文名接到的是**錯的子科目**。
    ruled = apply_rulings(metrics)
    # ── 批663:搭橋(只增不減;alias_index+same_as,零新造詞)──
    n_bridge, alias_index, pending_op = derive_same_as(metrics)
    # DERIVED / DIMENSION 是**刻意留白**,不是待裁定。留在 pending 裡會讓
    #   「待裁定 N」這個數字永遠降不到 0,而那 4 欄其實已經判完了(判的是「不該有式」)。
    _intentional = {k for k, (lane, _t, _w) in RULED_B665.items()
                    if lane in ("DERIVED", "DIMENSION")}
    pending_op = [k for k in pending_op if k not in _intentional]
    srcs["rulings"] = ("批665 十九欄裁定:" + " · ".join(f"{k} {v}" for k, v in ruled.items()))
    srcs["bridge"] = (f"批663 搭橋:同中文名 {n_bridge} 組 · merged_from 反查 "
                      f"{len(alias_index)} 筆 · 仍待裁定 {len(pending_op)} 欄")

    n_multi = sum(1 for m in metrics.values() if len(m["sources"]) > 1)
    book_findata = {"schema": "VIA.VRN.FinDataSynonym.v1", "generated": ts,
                    "policy": "中英文同義字庫;多源並列 sources 標註不仲裁;收割自倉內正本",
                    "count": len(metrics), "multi_source": n_multi,
                    "folded": n_fold,
                    "bridge_policy": ("批663 只增不減搭橋:辨識式空的鍵指向有式的同一件事;"
                                      "alias_index=冊記 merged_from 反查(鍵被摺掉、名字還在被喊)、"
                                      "same_as=同中文名逐字相同。兩條車道只取冊上既有的字,"
                                      "零新造詞;接不上的入 pending_operator 待裁定(LL90)"),
                    "same_as_count": n_bridge,
                    "ruled_b665": ruled,
                    "intentionally_no_pattern": sorted(_intentional),
                    "intentionally_no_pattern_why": (
                        "批665 裁定:DERIVED 是算出來的(頁面上沒有那一行)、DIMENSION 不是財務數字。"
                        "給它們辨識式等於宣稱認得出一個不存在的東西——那是假綠。"
                        "**刻意留白不等於待裁定**,所以不進 pending_operator"),
                    "alias_index": alias_index,
                    "pending_operator": pending_op,
                    "metrics": metrics}

    statements = {}
    for code, (zh, en, aliases) in STMT_ZH.items():
        statements[code] = {"zh": zh, "en": en, "aliases": aliases,
                            "items": sorted(stmt_items.get(code, []))}
    book_finstmt = {"schema": "VIA.VRN.FinStatementSynonym.v1", "generated": ts,
                    "policy": "報表層同義字庫;科目歸屬自 pattern 庫 StatementType",
                    "count": len(statements),
                    "item_total": sum(len(s["items"]) for s in statements.values()),
                    "statements": statements}
    nf = _numfmt_harvest(HERE / "InvestmentRegexPattern_VALIDATED.py")
    book_numfmt = {"schema": "VIA.VRN.NumberFormatRegex.v1", "generated": ts,
                   "policy": ("數字格式**擷取式**冊(帶 capture group),非欄位同義字——"
                              "混進同義冊會讓『認得出欄位名』與『抓得出數字』變成同一件事;"
                              "收割自 InvestmentRegexPattern_VALIDATED.py NUMBER_PATTERNS,AST 零執行"),
                   "count": len(nf), "number_patterns": nf}
    srcs["numfmt"] = f"NUMBER_PATTERNS·{len(nf)} 式(批663 新冊;v0104 誠實跳過但沒給下一步)"
    book_broker["count"] = len(brokers)
    return (book_broker, book_findata, book_finstmt, book_rating,
            book_tickdate, book_numfmt, srcs)


def rich_matrix(title, columns, rows, state_col=None) -> bool:
    try:
        from rich import box
        from rich.console import Console
        from rich.table import Table
        t = Table(title=title, box=box.SIMPLE_HEAVY, title_style="bold",
                  header_style="bold cyan", pad_edge=False)
        for c in columns:
            t.add_column(c, overflow="fold", no_wrap=False)
        for r in rows:
            t.add_row(*[str(x) for x in r])
        Console().print(t)
        return True
    except Exception:
        for r in rows:
            print("  " + " | ".join(str(x) for x in r))
        return False


def build(out_dir: Path = KNOW) -> int:
    bb, bf, bs, br, bt, bn, srcs = harvest()
    out_dir.mkdir(parents=True, exist_ok=True)
    for p, b in [(out_dir / BOOK_BROKER.name, bb), (out_dir / BOOK_FINDATA.name, bf),
                 (out_dir / BOOK_FINSTMT.name, bs), (out_dir / BOOK_RATING.name, br),
                 (out_dir / BOOK_TICKDATE.name, bt), (out_dir / BOOK_NUMFMT.name, bn)]:
        p.write_text(json.dumps(b, ensure_ascii=False, indent=1), encoding="utf-8")
    rich_matrix("財務字庫收割結果 v0105(AI 只整理不發明;逐條標來源)",
                ["冊", "條目", "註"],
                [[BOOK_BROKER.name, f"{bb['count']}+擴 {bb.get('count_extended', 0)}",
                  "券商縮寫+extended(code/en/zh/aliases/country)"],
                 [BOOK_FINDATA.name, bf["count"],
                  f"canonical 中英同義+field_map(twse/twstock/yf);多源 {bf['multi_source']} 項"],
                 [BOOK_FINSTMT.name, f"{bs['count']} 表/{bs['item_total']} 科目",
                  "報表名同義+科目歸屬"],
                 [BOOK_RATING.name, f"{len(br['levels'])} 級+{len(br['keyword_sets'])} 集",
                  "評等四級 zh/en+score_range+關鍵字六集"],
                 [BOOK_TICKDATE.name,
                  f"{len(bt['ticker_patterns'])}+{len(bt['datetime_patterns'])} 式",
                  "多市場 ticker+日期時間 regex(TW 寬鬆式不入 LOCKED 圈)"],
                 [BOOK_NUMFMT.name, f"{bn['count']} 式",
                  "批663 數字格式擷取式(帶 capture group;非同義字,另立冊不混)"],
                 ["(橋)", f"same_as {bf['same_as_count']} · alias {len(bf['alias_index'])}"
                          f" · 待裁定 {len(bf['pending_operator'])}",
                  "批663 只增不減搭橋;待裁定逐欄列名於 --reconcile"]])
    print(f"  [源] {' · '.join(f'{k}={v}' for k, v in srcs.items())}")
    return 0


def ask(term: str) -> int:
    hits = []
    if BOOK_RATING.exists():
        br = json.loads(BOOK_RATING.read_text(encoding="utf-8-sig"))
        for cat, d in br.get("levels", {}).items():
            if any(term.lower() == t.lower() for t in d["zh"] + d["en"]):
                hits.append(f"[RATING] {term} → {cat}(level {d['level']} · {d['sentiment']})")
    for p, kind in [(BOOK_BROKER, "BROKER"), (BOOK_FINDATA, "FINDATA"), (BOOK_FINSTMT, "FINSTMT")]:
        if not p.exists():
            continue
        b = json.loads(p.read_text(encoding="utf-8-sig"))
        if kind == "BROKER":
            for zh, rec in b["brokers"].items():
                if term in zh or term.upper() == rec["abbr"] or any(
                        term.lower() in a.lower() for a in rec.get("aliases", [])):
                    hits.append(f"[BROKER] {zh} → {rec['abbr']}"
                                + (f" · 別名 {len(rec.get('aliases', []))}" if rec.get("aliases") else ""))
            for eb in b.get("brokers_extended", []):
                if any(term.lower() in a.lower() for a in eb["aliases"]):
                    hits.append(f"[BROKER+] {eb['zh']}({eb['en']}) → {eb['code']} · {eb['country']}")
        elif kind == "FINDATA":
            for canon, m in b["metrics"].items():
                hay = [canon, m["zh"], m["en"], *m["synonyms_zh"], *m["synonyms_en"]]
                if any(term.lower() in str(h).lower() for h in hay):
                    hits.append(f"[FINDATA] {canon}({m['zh']}/{m['en']}) · {m['statement']}"
                                f" · 同義 zh{len(m['synonyms_zh'])}/en{len(m['synonyms_en'])}"
                                f" · 源:{','.join(m['sources'])}")
        else:
            for code, s in b["statements"].items():
                if any(term in a for a in s["aliases"]) or term.upper() in code:
                    hits.append(f"[FINSTMT] {code}({s['zh']}/{s['en']}) · 科目 {len(s['items'])}")
    if not hits:
        print(f"  [查] 「{term}」零命中(誠實;先 --build 落冊)")
        return 0
    for h in hits[:20]:
        print("  " + h)
    print(f"  [計] {len(hits)} 命中")
    return 0



# ═══ 批663:對帳器 —— 一個沒有對帳器的數字,就只是一個看起來很負責的數字 ═══
def _irp_ast_census(irp_path: Path) -> tuple[dict, dict]:
    """AST **零執行**數正本,回 (欄位→式清單, 數字格式名→式)。

    對帳要有第二把尺:收割器是執行正本再取屬性,這裡用 AST 純讀。
    同一份正本、兩條不同的路 —— 不然就是自己跟自己核對。
    """
    fields: dict = {}
    if not irp_path.exists():
        return fields, {}
    tree = ast.parse(irp_path.read_text(encoding="utf-8-sig"))
    for node in tree.body:
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Dict):
            continue
        names = [t.id for t in node.targets if isinstance(t, ast.Name)]
        if not any(n.endswith("_PATTERNS") for n in names) or "NUMBER_PATTERNS" in names:
            continue
        for k_, v_ in zip(node.value.keys, node.value.values):
            if not isinstance(k_, ast.Constant) or not isinstance(v_, ast.Call):
                continue
            pats = []
            for kw in v_.keywords:
                if kw.arg == "patterns" and isinstance(kw.value, (ast.List, ast.Tuple)):
                    pats = [e.value for e in kw.value.elts if isinstance(e, ast.Constant)]
            fields[str(k_.value)] = pats
    return fields, _numfmt_harvest(irp_path)


def rulings() -> int:
    """批665 十九欄裁定逐欄攤開。誰要推翻哪一欄,看 why 那一行就夠。"""
    if not BOOK_FINDATA.exists():
        print("  [ABSENT] 冊不在(先 via-finlex --build)")
        return 3
    book = json.loads(BOOK_FINDATA.read_text(encoding="utf-8-sig"))
    m = book.get("metrics", {})
    rows = []
    for k in sorted(RULED_B665, key=lambda x: (_RULE_LANES.index(RULED_B665[x][0]), x)):
        lane, tgt, why = RULED_B665[k]
        rec = m.get(k, {})
        pats, via = patterns_of(book, k)
        if lane in ("DERIVED", "DIMENSION"):
            got = "(刻意留白)"
        elif pats:
            got = f"{len(pats)} 式" + (f" 借道 {via}" if via else " 自有")
        else:
            got = "★ 還是拿不到式"
        rows.append([lane, k, str(rec.get("zh") or ""), tgt or "—", got, why])
    rich_matrix("批665 十九欄裁定(操作員授權「你決定 你覆核 你完成字洞」;每筆都能被一眼推翻)",
                ["車道", "欄位", "中文名", "去向", "拿得到式?", "憑據"], rows)
    tally = {ln: sum(1 for r_ in rows if r_[0] == ln) for ln in _RULE_LANES}
    stuck = [r_[1] for r_ in rows if r_[4].startswith("★")]
    print(f"  [計] " + " · ".join(f"{k} {v}" for k, v in tally.items())
          + f" = {len(rows)} 欄 · 仍拿不到式 {len(stuck)}{stuck if stuck else ''}")
    print("  [律] DERIVED/DIMENSION 是**刻意留白**不是待裁定:頁面上沒有那一行,"
          "給它辨識式等於宣稱認得出一個不存在的東西。")
    return 1 if stuck else 0


def reconcile() -> int:
    """正本 ↔ 冊 逐條對帳。誠實 rc:0 全帳平 · 1 有未命中或斷鏈 · 2 缺料 · 3 冊缺席。"""
    irp_p = HERE / "InvestmentRegexPattern_VALIDATED.py"
    if not BOOK_FINDATA.exists():
        print("  [ABSENT] 冊 VRN_FinData_Synonym 不在(先 via-finlex --build)")
        return 3
    if not irp_p.exists():
        print("  [NODATA] 正本 InvestmentRegexPattern_VALIDATED.py 不在樹上")
        return 2
    book = json.loads(BOOK_FINDATA.read_text(encoding="utf-8-sig"))
    fields, numfmt = _irp_ast_census(irp_p)
    n_field = len(fields)
    n_pat = sum(len(v) for v in fields.values())
    in_book = set()
    for m in book.get("metrics", {}).values():
        in_book |= set(m.get("patterns") or [])
        in_book |= set(m.get("synonyms_zh") or [])
        in_book |= set(m.get("synonyms_en") or [])
    missing = [(f, x) for f, ps in fields.items() for x in ps if x not in in_book]

    rows = [["正本欄位(AST 零執行)", n_field, "PatternDef"],
            ["正本辨識式", n_pat, "不含數字格式"],
            ["正本數字格式式", len(numfmt), "帶 capture group,另立冊"],
            ["正本合計", n_pat + len(numfmt),
             "晉升紀錄 2026-08-05 自報 525 —— 差額看下一列"],
            ["紀錄自報 vs 實有", f"525 vs {n_pat + len(numfmt)}",
             "GREEN" if n_pat + len(numfmt) == 525 else
             f"★ 差 {525 - n_pat - len(numfmt)} 條,紀錄的數字沒有對帳器"],
            ["冊內欄位", book.get("count", 0), "多源合併後"],
            ["正本式落冊", f"{n_pat - len(missing)}/{n_pat}",
             "GREEN 一條不缺" if not missing else f"★ 未命中 {len(missing)} 條"]]
    rich_matrix("批663 正本↔冊對帳(兩把尺:收割器執行取屬性 · 對帳器 AST 純讀)",
                ["項", "數", "註"], rows)

    # 下游才是真戰場:SSOT 正規名走不走得到辨識式
    syn_p = HERE / "VRN_Financial_Synonyms_SSOT.py"
    dead, ok_, borrowed = [], 0, []
    canon: list = []
    if syn_p.exists():
        try:
            tree = ast.parse(syn_p.read_text(encoding="utf-8-sig"))
            for n_ in tree.body:
                tg = (n_.targets[0] if isinstance(n_, ast.Assign)
                      else getattr(n_, "target", None)) if isinstance(
                          n_, (ast.Assign, ast.AnnAssign)) else None
                if isinstance(tg, ast.Name) and tg.id == "METRIC_SYNONYMS":
                    canon = sorted(set(ast.literal_eval(n_.value).values()))
        except Exception as exc:
            print(f"  [NODATA] METRIC_SYNONYMS 讀不到:{str(exc)[:60]}")
    for c in canon:
        pats, via = patterns_of(book, c)
        if pats:
            ok_ += 1
            if via:
                borrowed.append(f"{c}→{via}")
        else:
            dead.append(c)
    if canon:
        rich_matrix("批663 下游實走:VRN_Financial_Synonyms_SSOT 正規名 → 查得到辨識式?",
                    ["項", "數", "註"],
                    [["正規名", len(canon), "METRIC_SYNONYMS 的值域"],
                     ["走得到辨識式", ok_, f"其中 {len(borrowed)} 個是**借來的**(橋接上了)"],
                     ["借道明細", len(borrowed), " · ".join(borrowed) or "(無)"],
                     ["仍然斷鏈", len(dead),
                      "GREEN 零斷鏈" if not dead else "★ " + " · ".join(dead)]])

    pend = book.get("pending_operator", []) or []
    if pend:
        print(f"\n  [PENDING_OPERATOR] {len(pend)} 欄辨識式 0 條、三條車道都接不上,"
              f"裁定權在操作員(LL90),AI 不自己填:")
        for i in range(0, len(pend), 6):
            print("    " + " · ".join(pend[i:i + 6]))
        print("    (要接的話請指名『A 併到 B』;同中文名逐字相同的已自動搭橋,"
              "剩下的都是中文名不同、需要人裁的)")
    intentional = book.get("intentionally_no_pattern", []) or []
    if intentional:
        print(f"\n  [刻意留白] {len(intentional)} 欄:{' · '.join(intentional)}"
              f"\n    批665 裁定 DERIVED/DIMENSION——頁面上沒有那一行,給式就是假綠。"
              f"逐欄憑據:via-finlex --rulings")

    # 誠實態:等人裁 ≠ 壞掉。判錯的紅燈和假綠一樣傷。
    #   RED   — 正本的式沒落冊(收割真的漏了),或斷鏈的名字**不在**待裁定名單上
    #           (那代表橋該接沒接上,是引擎的錯,不是缺人裁)
    #   GATED — 斷鏈的名字全都在待裁定名單上:料齊、橋的規則接不上、裁定權在操作員
    #   GREEN — 一條不缺、零斷鏈
    if missing:
        print(f"\n  [未命中前 10] " + " · ".join(f"{f}:{x[:24]}" for f, x in missing[:10]))
    # 批665:斷鏈現在有**三種**,不是兩種。少認一種就會判錯燈:
    #   · 刻意留白(DERIVED/DIMENSION)—— 已經判完了,判的是「不該有式」。不是壞也不是等人。
    #   · 待裁定(pending)—— 料齊、規則接不上、等人裁 → GATED
    #   · 都不是 —— 橋的規則該接沒接上,引擎的錯 → RED
    ruled_blank = set(book.get("intentionally_no_pattern", []) or [])
    blanked = [c for c in dead if c in ruled_blank]
    unbridged = [c for c in dead if c not in pend and c not in ruled_blank]
    if blanked:
        print(f"\n  [刻意留白] 正規名 {len(blanked)} 個:{' · '.join(blanked)}"
              f"\n        —— 批665 裁定:頁面上沒有那一行,給式就是假綠。"
              f"**判完了,不是待辦。**逐欄憑據:via-finlex --rulings")
    if unbridged:
        print(f"\n  [RED] 斷鏈、不在待裁定名單、也不是刻意留白 {len(unbridged)}:"
              f"{' · '.join(unbridged)}\n        —— 橋的規則該接沒接上,引擎的錯")
    if missing or unbridged:
        state, rc = "RED", 1
    elif pend and [c for c in dead if c in pend]:
        state, rc = "GATED", 4
    else:
        state, rc = "GREEN", 0
    print(f"\n  [計] 正本式 {n_pat + len(numfmt)} · 落冊 {n_pat - len(missing)}/{n_pat}"
          f" · 正規名走得到 {ok_}/{len(canon)}(借道 {len(borrowed)}"
          f" · 刻意留白 {len(blanked)})· 待裁定 {len(pend)} 欄 → {state}")
    if rc == 4:
        print("  [律] GATED≠壞掉:同中文名逐字相同的橋已自動接上,剩下的中文名不同,"
              "同義的裁定權在操作員(LL90),AI 不自己填")
    if rc == 0 and blanked:
        print("  [律] 全綠不等於「每一欄都有式」——**有些欄位本來就不該有式**。"
              "17/18 走得到,剩下那一個是判過的留白,不是漏掉的洞。")
    return rc

MOTTO2 = "VERITAS INTELLIGENCE ANALYTICS · OBSERVA · INTELLEGE · PRAEVIDE"
UI_CSS = """
body{background:#f2f1ec;color:#1b1a17;font-family:'Cormorant Garamond','Noto Serif CJK TC','Microsoft JhengHei',serif;margin:0;padding:24px}
.card{background:#fbfaf7;border:1px solid #dbd9d3;border-radius:6px;padding:18px 22px;margin:14px auto;max-width:1280px}
h1{font-size:20px;margin:0 0 2px}
.motto{color:#9e2b25;letter-spacing:.14em;font-size:11px;margin-bottom:14px}
table{border-collapse:collapse;width:100%;font-size:12px}
th{color:#3c6660;text-align:left;border-bottom:1.5px solid #3c6660;padding:3px 7px}
td{border-bottom:1px solid #dbd9d3;padding:3px 7px;vertical-align:top}
.mono{font-family:Consolas,monospace;font-size:11px}.dim{color:#6b6a64}
.g{color:#3d7a52;font-weight:bold}.y{color:#8a6420;font-weight:bold}
"""


def _load_books() -> dict:
    out = {}
    for key, p in [("broker", BOOK_BROKER), ("findata", BOOK_FINDATA),
                   ("finstmt", BOOK_FINSTMT), ("rating", BOOK_RATING),
                   ("tickdate", BOOK_TICKDATE)]:
        if p.exists():
            out[key] = json.loads(p.read_text(encoding="utf-8-sig"))
    return out


def ask_many(terms: list[str]) -> int:
    """批47:一口氣問全部——多詞一矩陣"""
    rows = []
    for t in terms:
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            ask(t)
        hits = [l.strip() for l in buf.getvalue().splitlines()
                if l.strip().startswith("[")]
        if hits:
            for h in hits:
                dom = h[1:h.index("]")]
                rows.append([t, dom, h[h.index("]") + 1:].strip()])
        else:
            rows.append([t, "—", "零命中(誠實)"])
    rich_matrix(f"字庫批查矩陣({len(terms)} 詞一口氣)",
                ["詞", "域", "命中"], rows)
    n_hit = sum(1 for r in rows if r[1] != "—")
    print(f"  [計] {len(terms)} 詞 · 命中列 {n_hit} · 未中 {sum(1 for r in rows if r[1] == '—')}")
    return 0


def all_view(no_open: bool = True, out_path: Path | None = None) -> int:
    """批47:--all 全五冊總覽(rich+理印 HTML 全覽頁)"""
    books = _load_books()
    if not books:
        print("  [SKIP] 冊未落地(先 via-finlex --build)")
        return 0
    bf = books.get("findata", {})
    bb = books.get("broker", {})
    br = books.get("rating", {})
    bs = books.get("finstmt", {})
    bt = books.get("tickdate", {})
    rich_matrix("財務字庫全覽(五冊一口氣)",
                ["冊", "規模", "內容"],
                [["FINDATA", f"{bf.get('count', 0)} canonical",
                  f"多源 {bf.get('multi_source', 0)} 項·field_map 三制式"],
                 ["BROKER", f"{bb.get('count', 0)}+擴 {bb.get('count_extended', 0)}",
                  "縮寫+extended(aliases/country)"],
                 ["RATING", f"{len(br.get('levels', {}))} 級+{len(br.get('keyword_sets', {}))} 集",
                  "/".join(br.get("levels", {}).keys())],
                 ["FINSTMT", f"{bs.get('count', 0)} 表/{bs.get('item_total', 0)} 科目",
                  "/".join(s['zh'] for s in bs.get('statements', {}).values())],
                 ["TICKDATE", f"{len(bt.get('ticker_patterns', {}))}+{len(bt.get('datetime_patterns', {}))} 式",
                  "多市場 ticker+日期時間 regex"]])
    # 理印 HTML 全覽
    mrows = []
    for canon, m in sorted(bf.get("metrics", {}).items()):
        fm = m.get("field_map", {})
        mrows.append(
            f"<tr><td class='mono'>{canon}</td><td>{m.get('zh', '')}</td><td>{m.get('en', '')}</td>"
            f"<td>{m.get('statement', '') or '—'}</td>"
            f"<td class='g'>{len(m.get('synonyms_zh', []))}/{len(m.get('synonyms_en', []))}</td>"
            f"<td class='dim'>{' · '.join(f'{k}:{v}' for k, v in fm.items()) or '—'}</td>"
            f"<td class='dim'>{len(m.get('sources', []))} 源</td></tr>")
    brows = "".join(f"<tr><td>{zh}</td><td class='mono'>{r['abbr']}</td>"
                    f"<td class='dim'>{', '.join(r.get('aliases', [])[:6])}</td></tr>"
                    for zh, r in bb.get("brokers", {}).items())
    berows = "".join(f"<tr><td>{b['zh']}</td><td>{b['en']}</td><td class='mono'>{b['code']}</td>"
                     f"<td>{b['country']}</td><td class='dim'>{', '.join(b['aliases'][:6])}</td></tr>"
                     for b in bb.get("brokers_extended", []))
    rrows = "".join(f"<tr><td class='mono'>{c}</td><td>{d['level']}</td><td>{d['sentiment']}</td>"
                    f"<td class='dim'>{'、'.join(d['zh'][:8])}…</td><td class='dim'>{', '.join(d['en'][:6])}…</td></tr>"
                    for c, d in br.get("levels", {}).items())
    srows = "".join(f"<tr><td class='mono'>{c}</td><td>{s['zh']}</td><td>{s['en']}</td>"
                    f"<td class='g'>{len(s['items'])}</td></tr>"
                    for c, s in bs.get("statements", {}).items())
    trows = "".join(f"<tr><td class='mono'>{k}</td><td class='mono dim'>{v[:70]}</td></tr>"
                    for k, v in {**bt.get("ticker_patterns", {}),
                                 **bt.get("datetime_patterns", {})}.items())
    html = f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<title>VRN 財務字庫全覽</title><style>{UI_CSS}</style></head><body>
<div class="card"><h1>財務字庫全覽 · FinLex Atlas</h1><div class="motto">{MOTTO2}</div>
<div class="dim">五冊一口氣 · FINDATA {bf.get('count', 0)} canonical(多源 {bf.get('multi_source', 0)})· BROKER {bb.get('count', 0)}+{bb.get('count_extended', 0)} · RATING {len(br.get('levels', {}))} 級 · FINSTMT {bs.get('item_total', 0)} 科目 · REGEX {len(trows and bt.get('ticker_patterns', {}))}+{len(bt.get('datetime_patterns', {}))} 式</div></div>
<div class="card"><h1>財務數據中英同義({bf.get('count', 0)} canonical)</h1>
<table><tr><th>canonical</th><th>中</th><th>英</th><th>報表</th><th>同義 zh/en</th><th>field_map</th><th>源</th></tr>{''.join(mrows)}</table></div>
<div class="card"><h1>券商字典({bb.get('count', 0)} 縮寫)</h1>
<table><tr><th>券商</th><th>縮寫</th><th>別名</th></tr>{brows}</table></div>
<div class="card"><h1>券商 extended({bb.get('count_extended', 0)} 家)</h1>
<table><tr><th>中</th><th>英</th><th>code</th><th>國</th><th>別名</th></tr>{berows}</table></div>
<div class="card"><h1>評等字典</h1>
<table><tr><th>級</th><th>level</th><th>情緒</th><th>中</th><th>英</th></tr>{rrows}</table></div>
<div class="card"><h1>財務報表({bs.get('count', 0)} 表)</h1>
<table><tr><th>代碼</th><th>中</th><th>英</th><th>科目數</th></tr>{srows}</table></div>
<div class="card"><h1>Ticker+日期 Regex({len(bt.get('ticker_patterns', {}))}+{len(bt.get('datetime_patterns', {}))} 式)</h1>
<table><tr><th>名</th><th>pattern</th></tr>{trows}</table></div>
</body></html>"""
    out = out_path or (VIA / "VIA_Reports" / "VIA_UI_FinLex.html")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"  [頁] 全覽 U/I:{out.name}")
    if not no_open:
        try:
            import webbrowser
            webbrowser.open(out.as_uri())
        except Exception:
            pass
    return 0


def selftest() -> int:
    import tempfile
    t0 = time.time()
    fails = []

    def chk(name, cond, note=""):
        if not cond:
            fails.append(name)
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")

    bb, bf, bs, br, bt, bn, srcs = harvest()
    # ① broker dict:29 家、元大→YT、逐條標來源
    chk("broker dict 收割", bb["count"] >= 25 and bb["brokers"].get("元大", {}).get("abbr") == "YT"
        and all(r.get("source") for r in bb["brokers"].values()), f"({bb['count']} 家)")
    # ② 財務數據冊:cash 中英同義齊
    cash = bf["metrics"].get("cash", {})
    chk("cash 中英同義", cash.get("zh") == "現金及約當現金"
        and "現金及約當現金" in cash.get("synonyms_zh", [])
        and any("cash" in s for s in cash.get("synonyms_en", [])))
    # ③ MOPS 官方名併入:營業收入合計→revenue
    rev = bf["metrics"].get("revenue", {})
    chk("MOPS 官方名併入", "營業收入合計" in rev.get("mops_official", []) if "mops" in srcs else True)
    # ④ MDL008 別名併入:ebit→operating_income
    oi = bf["metrics"].get("operating_income", {})
    chk("MDL008 別名併入", "ebit" in oi.get("mdl008_aliases", []) if "aliases" in srcs else True)
    # ⑤ 多源並列不仲裁(sources ≥2 存在且來源全標)
    chk("多源並列標註", bf["multi_source"] >= 3
        and all(m["sources"] for m in bf["metrics"].values()))
    # ⑥ 報表冊:四大表+科目歸屬(BS 科目≥40)
    chk("報表冊四大表", all(k in bs["statements"] for k in
        ["BALANCE_SHEET", "INCOME_STATEMENT", "CASH_FLOW", "EQUITY_CHANGE"])
        and len(bs["statements"]["BALANCE_SHEET"]["items"]) >= 40)
    # ⑦ 中英分類器:zh 進 zh 欄
    chk("CJK 分類器", all(_CJK.search(s) for s in cash.get("synonyms_zh", []))
        and not any(_CJK.search(s) for s in cash.get("synonyms_en", [])))
    # ⑧ 沙盒落冊+讀回 schema(五冊齊)
    with tempfile.TemporaryDirectory() as td:
        rc = build(Path(td))
        back = json.loads((Path(td) / BOOK_FINDATA.name).read_text(encoding="utf-8"))
        chk("沙盒落冊讀回(五冊)", rc == 0 and back["schema"] == "VIA.VRN.FinDataSynonym.v1"
            and back["count"] == bf["count"]
            and all((Path(td) / n_).exists() for n_ in
                    [BOOK_RATING.name, BOOK_TICKDATE.name]))
    # ⑨ v0101 分類規則併入:revenue field_map 三源+別名折疊(CostOfRevenue→cogs)
    rev = bf["metrics"].get("revenue", {})
    chk("分類規則 field_map 併入", rev.get("field_map", {}).get("twstock") == "revenue"
        and rev.get("field_map", {}).get("yfinance") == "totalRevenue"
        and "cost_of_revenue" not in bf["metrics"]
        and "營業成本" in bf["metrics"].get("cogs", {}).get("synonyms_zh", []))
    # ⑩ broker extended:32 家、大摩 alias 查得 MS
    ms = next((b_ for b_ in bb.get("brokers_extended", []) if "大摩" in b_["aliases"]), None)
    chk("broker extended 併入", bb.get("count_extended", 0) >= 30
        and ms is not None and ms["code"] == "MS")
    # ⑪ 評等冊四級+標準化件 AST 收割(keyword_sets 或誠實 SKIP 記錄)
    chk("評等冊+AST 收割", set(br["levels"]) == {"BUY", "HOLD", "SELL", "NOT_RATED"}
        and "買進" in br["levels"]["BUY"]["zh"]
        and ("standardization" in srcs))
    # ⑫ md 對照表+ticker/date regex 冊
    chk("md 表+regex 冊", "mapping_md" in srcs
        and len(bt["ticker_patterns"]) >= 15 and len(bt["datetime_patterns"]) >= 15
        and "payout_ratio" in bf["metrics"])
    # ⑬ 帳目 SSOT 併入(批46):61 科目級、revenue 得「營收」alias、uid 標記
    chk("帳目 SSOT 併入", "account_ssot" in srcs
        and "營收" in bf["metrics"].get("revenue", {}).get("synonyms_zh", [])
        and any("vrn_uid" in m_ for m_ in bf["metrics"].values()))
    # ⑭ Synonyms_SSOT 併入(批46):target_price 建條含「目標價」
    chk("Synonyms_SSOT 併入", "synonyms_ssot" in srcs
        and "目標價" in bf["metrics"].get("target_price", {}).get("synonyms_zh", []))
    # ⑮ 批查一口氣(批47):多詞一矩陣 rc0(冊在位時實查,缺冊誠實過)
    rc15 = ask_many(["毛利", "大摩", "Outperform", "不存在的詞XYZ"])
    chk("多詞批查一口氣", rc15 == 0)
    # ⑯ 全覽頁(批47):沙盒落 HTML 含銘言+五冊區
    with tempfile.TemporaryDirectory() as td2:
        up = Path(td2) / "ui.html"
        rc16 = all_view(no_open=True, out_path=up)
        ok16 = rc16 == 0 and (not up.exists() or (
            MOTTO2 in up.read_text(encoding="utf-8")
            and "財務數據中英同義" in up.read_text(encoding="utf-8")))
        chk("全覽 HTML 頁", ok16)
    # ⑰ 摺疊+回填(批48):退化條目歸零、目標條同義零丟失、空欄補齊
    pe_gone = "pe" not in bf["metrics"] and "eps_basic" not in bf["metrics"]
    pr = bf["metrics"].get("pe_ratio", {})
    be = bf["metrics"].get("basic_eps", {})
    no_empty = all(m.get("zh") or not m.get("synonyms_zh")
                   for m in bf["metrics"].values())
    chk("摺疊+回填", pe_gone and "pe" in pr.get("merged_from", [])
        and "eps_basic" in be.get("merged_from", []) and no_empty
        and bf.get("folded", 0) >= 4)
    # ⑱ 操作員核定回填(批49):ebit 得 en/報表、eps_yoy 得中文、零空 statement 於核定圈
    eb = bf["metrics"].get("ebit", {})
    ey = bf["metrics"].get("eps_yoy", {})
    chk("操作員核定回填", "operator_fill" in srcs
        and eb.get("en") == "EBIT" and eb.get("statement") == "INCOME_STATEMENT"
        and ey.get("zh") == "eps年增率" and ey.get("operator_filled"))
    # ── 批663 五檢 ───────────────────────────────────────────────────
    # ⑲ 搭橋 B 車道:同中文名逐字相同,空的那邊拿得到指標,而且**鍵沒被刪掉**
    eps_ = bf["metrics"].get("eps", {})
    opp_ = bf["metrics"].get("op_profit", {})
    chk("B 車道 same_as(同中文名逐字相同)",
        eps_.get("same_as") == "basic_eps" and opp_.get("same_as") == "operating_income"
        and eps_.get("same_as_basis") == "同中文名逐字相同"
        and not eps_.get("patterns") and "eps" in bf["metrics"]
        and bf.get("same_as_count", 0) >= 10,
        f"(same_as {bf.get('same_as_count', 0)} 組;只增不減:鍵全留著)")
    # ⑳ 搭橋 A 車道:被摺掉的鍵名還在被上游喊 → alias_index 反查得到
    ai = bf.get("alias_index", {})
    chk("A 車道 alias_index(merged_from 反查)",
        ai.get("eps_basic") == "basic_eps" and ai.get("eps_diluted") == "diluted_eps"
        and ai.get("pe") == "pe_ratio" and all(k not in bf["metrics"] for k in ai),
        f"({len(ai)} 筆)")
    # ㉑ patterns_of 跟橋走,而且**借來的看得見**(不把別人的式當自己的)
    p_eps, via_eps = patterns_of(bf, "eps")
    p_eb, via_eb = patterns_of(bf, "eps_basic")
    p_own, via_own = patterns_of(bf, "revenue")
    chk("patterns_of 跟橋走且標明借自",
        len(p_eps) >= 4 and via_eps == "basic_eps"
        and len(p_eb) >= 4 and via_eb == "basic_eps"
        and p_own and via_own == "",
        f"(eps 借 {len(p_eps)} 式 · revenue 自有 {len(p_own)} 式)")
    # ㉒ 數字格式另立冊:6 式、全部編得過、**一條都沒混進同義冊**
    nf = bn.get("number_patterns", {})
    leaked = [k for k, v in nf.items()
              if any(v in (m.get("patterns") or []) for m in bf["metrics"].values())]
    ok22 = (bn["count"] >= 6 and "amount_tw" in nf and "percentage" in nf
            and not leaked)
    for _v in nf.values():
        try:
            re.compile(_v)
        except re.error:
            ok22 = False
    chk("數字格式冊(擷取式不混同義冊)", ok22, f"({bn['count']} 式 · 外洩 {len(leaked)})")
    # ㉓ 待裁定名單具名可讀:有就得列得出名字,不能只給一個數(LL305)
    pend = bf.get("pending_operator", [])
    chk("待裁定逐欄具名", isinstance(pend, list)
        and all(isinstance(x, str) and x for x in pend)
        and all(not bf["metrics"][x].get("patterns") and not bf["metrics"][x].get("same_as")
                for x in pend if x in bf["metrics"]),
        f"({len(pend)} 欄:{' · '.join(pend[:4])}…)")
    # ── 批665 七檢 ───────────────────────────────────────────────────
    M = bf["metrics"]
    # ㉔ 十九欄全部判完,而且車道數對得起來(摘要與明細對不上是最難發現的假綠)
    r665 = bf.get("ruled_b665", {})
    chk("十九欄裁定齊(車道合計=19)",
        sum(r665.values()) == 19 and len(RULED_B665) == 19
        and r665.get("BRIDGE") == 10 and r665.get("SYNTH") == 5
        and r665.get("DERIVED") == 3 and r665.get("DIMENSION") == 1,
        f"({r665})")
    # ㉕ 每一筆裁定都帶憑據,而且說得出是誰裁的(裁定權轉手了,留痕的義務沒有)
    nowhy = [k for k, (_l, _t, w) in RULED_B665.items() if len(str(w).strip()) < 12]
    noby = [k for k in RULED_B665
            if "授權" not in str(M.get(k, {}).get("ruled_b665", {}).get("ruled_by", ""))]
    chk("逐筆帶憑據且標明誰裁的", not nowhy and not noby,
        f"(缺憑據 {nowhy[:3]} · 缺署名 {noby[:3]})")
    # ㉖ 總額不准接到子科目:non_current_liabilities 是本批最容易錯的一筆,
    #    候選演算法給的是 other_noncurrent_liabilities(子科目)。拿實例咬死。
    ncl = M.get("non_current_liabilities", {})
    chk("總額不接子科目(非流動負債↛其他非流動負債)",
        ncl.get("same_as") == "total_non_current_liabilities"
        and ncl.get("same_as") != "other_noncurrent_liabilities",
        f"(接到 {ncl.get('same_as')})")
    # ㉗ ROE 分母那一對:shareholders_equity 接總權益(含非控制),
    #    parent_equity **不准**接過去,否則分母會被悄悄換掉
    pe = M.get("parent_equity", {})
    se = M.get("shareholders_equity", {})
    chk("母公司權益不被併進總權益(ROE 分母)",
        se.get("same_as") == "total_equity" and not pe.get("same_as")
        and bool(pe.get("patterns")) and pe.get("patterns_synth_b665") is True,
        f"(parent_equity same_as={pe.get('same_as')} 式={len(pe.get('patterns', []))})")
    # ㉘ SYNTH 零新造詞:合成式裡的每一個字,都要能在這一欄**原本**的同義字裡找到
    bad_synth = []
    for k, (lane, _t, _w) in RULED_B665.items():
        if lane != "SYNTH":
            continue
        rec = M.get(k, {})
        if not rec.get("patterns_synth_b665"):
            bad_synth.append(k + ":沒合成")
            continue
        pool = set(rec.get("synonyms_zh") or []) | set(rec.get("synonyms_en") or [])
        pool |= set(str(v) for v in (rec.get("field_map") or {}).values())
        pool |= set(rec.get("mops_official") or []) | {rec.get("zh")}
        inner = rec["patterns"][0][1:-1]
        for w in inner.split("|"):
            if re.sub(r"\\(.)", r"\1", w) not in pool:
                bad_synth.append(f"{k}:{w[:14]}")
                break
    chk("SYNTH 零新造詞(每個字都在本欄原有同義字裡)", not bad_synth, f"({bad_synth[:3]})")
    # ㉙ 長的排前面:不然「母公司業主權益」會先吃掉「歸屬母公司業主權益」
    inner = M.get("parent_equity", {}).get("patterns", [""])[0][1:-1].split("|")
    lens = [len(x) for x in inner]
    chk("合成式長的排前面(短的先比對會咬到錯科目)", lens == sorted(lens, reverse=True),
        f"({inner[:3]})")
    # ㉚ 迭代收斂:cfps 要走兩跳才拿得到式,而且**借了幾手看得見**
    pats_cfps, via_cfps = patterns_of(bf, "cfps")
    chk("same_as 迭代收斂且回整條路徑(cfps 兩跳)",
        len(pats_cfps) >= 1 and via_cfps.count("→") >= 1
        and via_cfps.endswith("operating_cf_per_share"),
        f"(cfps 借道 {via_cfps})")
    n = 30 - len(fails)
    print(f"  [計] 三十檢 OK {n} · FAIL {len(fails)} · {round(time.time() - t0, 1)}s")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 財務字庫收割引擎 v0106 · 三十檢(沙盒零網路)===")
        return selftest()
    if "--all" in args:
        print("=== 財務字庫全覽(五冊一口氣;數字格式冊走 --reconcile)===")
        return all_view(no_open="--no-open" in args)
    if "--ask" in args:
        i = args.index("--ask")
        terms = []
        for a in args[i + 1:]:
            if a.startswith("--"):
                break
            terms += [t for t in re.split(r"[,、]", a) if t.strip()]
        if not terms:
            print("[用法] via-finlex --ask 詞1 詞2 …(空白/逗號分隔,一口氣批查)")
            return 2
        return ask_many(terms) if len(terms) > 1 else ask(terms[0])
    if "--rulings" in args:
        print("=== 批665 十九欄裁定(零網路)===")
        return rulings()
    if "--reconcile" in args:
        print("=== 批663 正本↔冊對帳(零網路;誠實 rc 0/1/2/3)===")
        return reconcile()
    if "--build" in args:
        print("=== 財務三字庫收割 · broker dict+財務數據中英同義+財務報表同義 ===")
        return build()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
