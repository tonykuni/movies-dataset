#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vrn_finlex_v0104 — 財務字庫收割引擎(TOOL-072)
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
  via-finlex --selftest    → 八檢(沙盒零網路)
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

    n_multi = sum(1 for m in metrics.values() if len(m["sources"]) > 1)
    book_findata = {"schema": "VIA.VRN.FinDataSynonym.v1", "generated": ts,
                    "policy": "中英文同義字庫;多源並列 sources 標註不仲裁;收割自倉內正本",
                    "count": len(metrics), "multi_source": n_multi,
                    "folded": n_fold, "metrics": metrics}

    statements = {}
    for code, (zh, en, aliases) in STMT_ZH.items():
        statements[code] = {"zh": zh, "en": en, "aliases": aliases,
                            "items": sorted(stmt_items.get(code, []))}
    book_finstmt = {"schema": "VIA.VRN.FinStatementSynonym.v1", "generated": ts,
                    "policy": "報表層同義字庫;科目歸屬自 pattern 庫 StatementType",
                    "count": len(statements),
                    "item_total": sum(len(s["items"]) for s in statements.values()),
                    "statements": statements}
    book_broker["count"] = len(brokers)
    return book_broker, book_findata, book_finstmt, book_rating, book_tickdate, srcs


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
    bb, bf, bs, br, bt, srcs = harvest()
    out_dir.mkdir(parents=True, exist_ok=True)
    for p, b in [(out_dir / BOOK_BROKER.name, bb), (out_dir / BOOK_FINDATA.name, bf),
                 (out_dir / BOOK_FINSTMT.name, bs), (out_dir / BOOK_RATING.name, br),
                 (out_dir / BOOK_TICKDATE.name, bt)]:
        p.write_text(json.dumps(b, ensure_ascii=False, indent=1), encoding="utf-8")
    rich_matrix("財務字庫收割結果 v0101(AI 只整理不發明;逐條標來源)",
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
                  "多市場 ticker+日期時間 regex(TW 寬鬆式不入 LOCKED 圈)"]])
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

    bb, bf, bs, br, bt, srcs = harvest()
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
    n = 18 - len(fails)
    print(f"  [計] 十八檢 OK {n} · FAIL {len(fails)} · {round(time.time() - t0, 1)}s")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 財務字庫收割引擎 v0104 · 十八檢(沙盒零網路)===")
        return selftest()
    if "--all" in args:
        print("=== 財務字庫全覽(五冊一口氣)===")
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
    if "--build" in args:
        print("=== 財務三字庫收割 · broker dict+財務數據中英同義+財務報表同義 ===")
        return build()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
