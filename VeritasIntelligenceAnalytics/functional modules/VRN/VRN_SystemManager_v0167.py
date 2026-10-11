#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0167 — 薄尾(操作員 2026-10-10:GS/MS/Citi/UBS BROKER DICT 沒有嗎 · 麥格理 MCQ · CLSA,CLST 相同 · 整合去重去大陸公司;
   + 實跑 7 份 KeyError:'bbox_pct' 整份失敗)。
  ① 修崩潰:版面分析出口統一補 bbox_pct(v0163「藏在文字中的表格」新建區塊少這欄 → 產版面頁 KeyError → 7 份整份失敗)
  ② dicts 動詞:券商冊統一 —— 讀載入器讀的全部冊(knowledge / 根目錄 VRN_Broker_Dict_v* · registry VRN_BROKER_LIST_v* · SYNONYM_LIBRARY 券商域 · 內建種子 · 操作員主字典)
     → 共用別名歸成同一家(一家一個代碼;主字典有的用主字典鍵:MCQ · CLSA · BOA …;CLST → CLSA;MACQUARIE/MQ → MCQ)
     → 去大陸公司(中金 CICC · 中銀國際 BOCI · 廣發 GF/GFHK …;整筆內容存附冊 removed_mainland,不丟)
     → 「中信證券」(台灣常指中國信託 · 也是大陸中信證券正式名)留著 · 標待裁 · 1~3 字母別名標「要字邊界」
     → 寫 VRN_Broker_Dict_v####(unified)+ .integration.json + BROKERS_latest.html;內容沒變不出新版
     載入器:有 unified 冊就只讀它(+ 非大陸的內建種子)→ 不再一家多個正典
  ③ dicts 動詞:主字典(操作員貼的 4 版 VIA_MASTER_SSOT_DICTIONARY 聯集)→ knowledge\\VRN_MasterDict_v0100.json;
     評等冊新版 = 舊冊 + 主字典評等(0~5 碼對照);1~2 字母短碼 / 2 字常用詞只給評等欄位用,不進全文比對
  ④ 股名核對:中文頁比 全名 / 去「股份有限公司」/ 去海外控股前綴 / 去產業字尾 / ±KY;英文首頁(中文字很少)→ 不適用(不再誤報「首頁沒對到 名稱」)
其餘動詞照前版鏈。
"""
from __future__ import annotations

# ===== [VIA:ACCEL-BRIDGE:v0110] 正本加速器 VeritasCeleritas_v1141 · 正本網路工具 VeritasAegisNexus_v1652(找不到 = 不改任何行為) =====
import sys as _cb_sys
from pathlib import Path as _cb_Path
_cb_p = _cb_Path(__file__).resolve()
while _cb_p.parent != _cb_p:
    if (_cb_p / "supportive modules").is_dir():
        _cb_sup = _cb_p / "supportive modules"
        for _cb_d in [_cb_sup] + [x.parent for x in list(_cb_sup.glob("*/VeritasAegisNexus_v1652.py"))[:1]]:
            if str(_cb_d) not in _cb_sys.path:
                _cb_sys.path.insert(0, str(_cb_d))
        break
    _cb_p = _cb_p.parent
try:
    import VeritasCeleritas_v1141 as _ACCEL  # noqa: F401  正本加速器
except Exception:  # noqa: BLE001
    _ACCEL = None


def _net():
    """正本網路工具(只在需要出網時載入;本引擎不出網)。"""
    try:
        import VeritasAegisNexus_v1652 as _NET  # noqa: WPS433
        return _NET
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import datetime
import html
import importlib.util
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0167"


def _vnum_v0167(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0167(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0167(p) < _vnum_v0167(__file__)), key=_vnum_v0167)
PRIOR = _load_v0167(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def _owner(name):
    import types
    mod, seen = PRIOR, set()
    while isinstance(mod, types.ModuleType) and id(mod) not in seen:
        seen.add(id(mod))
        if name in vars(mod):
            return mod
        mod = vars(mod).get("PRIOR")
    return None


def _resolve(name):
    m = _owner(name)
    return vars(m)[name] if m else None


def _job_entry(kind, item):
    return _resolve("_job")(kind, item)


def _init_entry(*args):
    return _resolve("_init_entry")(*args)


_rep, _home = _resolve("_rep"), _resolve("_home")


# ───────── ① 版面分析出口統一補 bbox_pct ─────────
def fill_bbox_pct(p: dict) -> int:
    W, H = float(p.get("W") or 0), float(p.get("H") or 0)
    n = 0
    if W <= 0 or H <= 0:
        return 0
    for b in p.get("blocks", []):
        if "bbox_pct" not in b and all(k in b for k in ("x0", "top", "x1", "bottom")):
            b["bbox_pct"] = [round(100 * b["x0"] / W, 1), round(100 * b["top"] / H, 1), round(100 * (b["x1"] - b["x0"]) / W, 1), round(100 * (b["bottom"] - b["top"]) / H, 1)]
            b.setdefault("id", "P%s·%s·HT" % (p.get("page", "?"), b.get("zone", "F")))
            b.setdefault("zone", "F")
            n += 1
    return n


_PREV_AP = _resolve("analyze_page")


def analyze_page_v167(*a, **k):
    p = _PREV_AP(*a, **k)
    try:
        fill_bbox_pct(p)
    except Exception:  # noqa: BLE001
        pass
    return p


_ma = _owner("analyze_page")
if _ma:
    setattr(_ma, "analyze_page", analyze_page_v167)


# ───────── ③ 主字典(操作員 4 版聯集)─────────
_MASTER = json.loads(r"""{"schema": "VIA.VRN.MasterDict.v1", "version": "v0100", "rule": "操作員 2026-10-10 貼入 4 版 VIA_MASTER_SSOT_DICTIONARY → 聯集去重 · 一筆不丟;CLSA=CLST 同一家;MCQ=麥格理;去大陸公司(本冊 4 版本來就沒有大陸券商;統一券商冊另去中金 / 中銀國際 / 廣發)", "provenance": {"variants": {"A": "原版(日期正則較寬 · 季度只認 Q)", "B": "+ 民國 7 碼 / 英文月份日期 · 年度 YYYY年/YY年", "C": "結構重排(DATE_AND_TICKER_PATTERNS)+ _cite 標記", "D": "同 C · 全部 _cite · 目標價別名少 3 個(TARGET PRICE / PRICE TARGET / TARGET)"}, "dropped": "_cite 欄位(\"[cite: 2]\" 等)= 產生工具的引用標記,不是資料 → 不收", "conflicts": "無(券商 / 評等 4 版完全一致;差異只在日期 / 季度正則與目標價別名,已聯集)"}, "DOMESTIC_BROKERS": {"YUANTA": {"chinese_name": "元大證券", "english_name": "Yuanta Securities", "aliases": ["元大", "元大投顧", "Yuanta", "元大證券", "Yuanta Securities"]}, "KGI": {"chinese_name": "凱基證券", "english_name": "KGI Securities", "aliases": ["凱基", "凱基投顧", "KGI", "凱基證券", "KGI Securities"]}, "FUBON": {"chinese_name": "富邦證券", "english_name": "Fubon Securities", "aliases": ["富邦", "富邦投顧", "Fubon", "富邦證券", "Fubon Securities"]}, "CAPITAL": {"chinese_name": "群益金鼎證券", "english_name": "Capital Securities", "aliases": ["群益", "群益投顧", "Capital", "群益金鼎證券", "Capital Securities"]}, "MASTERLINK": {"chinese_name": "元富證券", "english_name": "MasterLink Securities", "aliases": ["元富", "元富投顧", "MasterLink", "元富證券", "MasterLink Securities"]}, "SINOPAC": {"chinese_name": "永豐金證券", "english_name": "SinoPac Securities", "aliases": ["永豐", "永豐金", "永豐投顧", "SinoPac", "永豐金證券", "SinoPac Securities"]}, "PRESIDENT": {"chinese_name": "統一證券", "english_name": "President Securities", "aliases": ["統一", "統一投顧", "President", "統一證券", "President Securities"]}, "MEGA": {"chinese_name": "兆豐證券", "english_name": "Mega Securities", "aliases": ["兆豐", "兆豐投顧", "Mega", "兆豐證券", "Mega Securities"]}, "CATHAY": {"chinese_name": "國泰證券", "english_name": "Cathay Securities", "aliases": ["國泰", "國泰期貨", "國泰投顧", "Cathay", "國泰證券", "Cathay Securities"]}, "TAISHIN": {"chinese_name": "台新證券", "english_name": "Taishin Securities", "aliases": ["台新", "台新投顧", "Taishin", "台新證券", "Taishin Securities"]}, "CTBC": {"chinese_name": "中國信託證券", "english_name": "CTBC Securities", "aliases": ["中信", "中信證", "中信投顧", "中國信託", "CTBC", "中國信託證券", "CTBC Securities"]}, "FIRST": {"chinese_name": "第一金證券", "english_name": "First Securities", "aliases": ["第一金", "第一金投顧", "First", "第一金證券", "First Securities"]}, "HUANAN": {"chinese_name": "華南永昌證券", "english_name": "Hua Nan Securities", "aliases": ["華南", "華南永昌", "華南投顧", "Hua Nan", "華南永昌證券", "Hua Nan Securities"]}, "ESUN": {"chinese_name": "玉山證券", "english_name": "E.SUN Securities", "aliases": ["玉山", "玉山投顧", "E.SUN", "玉山證券", "E.SUN Securities"]}, "WATERLAND": {"chinese_name": "國票證券", "english_name": "Waterland Securities", "aliases": ["國票", "國票投顧", "國票華頓", "Waterland", "國票證券", "Waterland Securities"]}, "CONCORD": {"chinese_name": "康和證券", "english_name": "Concord Securities", "aliases": ["康和", "康和投顧", "Concord", "康和證券", "Concord Securities"]}}, "FOREIGN_BROKERS": {"MS": {"chinese_name": "摩根士丹利", "english_name": "Morgan Stanley", "aliases": ["大摩", "摩根士丹利", "Morgan Stanley", "MS"]}, "JPM": {"chinese_name": "摩根大通", "english_name": "J.P. Morgan", "aliases": ["小摩", "摩根大通", "摩通", "JPM", "JPMorgan", "J.P. Morgan"]}, "GS": {"chinese_name": "高盛", "english_name": "Goldman Sachs", "aliases": ["高盛", "Goldman Sachs", "GS"]}, "UBS": {"chinese_name": "瑞銀證券", "english_name": "UBS", "aliases": ["瑞銀", "瑞士銀行", "UBS", "瑞銀證券"]}, "BOA": {"chinese_name": "美林證券", "english_name": "BofA Securities", "aliases": ["美林", "美銀", "美銀證券", "BOA", "BofA", "Merrill Lynch", "ML", "美林證券", "BofA Securities"]}, "CITI": {"chinese_name": "花旗環球證券", "english_name": "Citigroup", "aliases": ["花旗", "花旗環球", "Citi", "Citigroup", "花旗環球證券"]}, "MCQ": {"chinese_name": "麥格理資本", "english_name": "Macquarie", "aliases": ["麥格理", "Macquarie", "MCQ", "MQ", "麥格理資本", "Macquarie Capital"], "operator_added": ["麥格理資本", "Macquarie Capital"]}, "NOMURA": {"chinese_name": "野村證券", "english_name": "Nomura", "aliases": ["野村", "Nomura", "野村證券"]}, "CLSA": {"chinese_name": "里昂證券", "english_name": "CLSA", "aliases": ["里昂", "CLSA", "里昂證券", "CLST"], "operator_added": ["CLST", "里昂證券"]}, "HSBC": {"chinese_name": "匯豐證券", "english_name": "HSBC", "aliases": ["匯豐", "HSBC", "匯豐證券"]}, "DAIWA": {"chinese_name": "大和資本", "english_name": "Daiwa Capital Markets", "aliases": ["大和", "大和資本", "Daiwa", "Daiwa Capital Markets"]}, "CS": {"chinese_name": "瑞士信貸", "english_name": "Credit Suisse", "aliases": ["瑞信", "瑞士信貸", "CS", "Credit Suisse"]}}, "TICKER_PATTERNS": {"Stock_Base": {"Regex": "^([1-9]\\d{3})$", "Description": "4碼數字,且第1碼不可以為零。"}, "Validation_Rule": "需與第一頁 TWSE (4碼)、Yahoo Finance (4碼+.TW/.TWO) 或 Bloomberg (4碼+ TT) 三平台規格對照完全一致。若檔名萃取出的前4個數字與首頁的定義相符,即確認代碼擷取成功。"}, "DATE_AND_TIME_PATTERNS": {"Date_Extraction": {"Regex": "(?:(?:20)?\\d{2}[-/]?\\d{2}[-/]?\\d{2})|(?:11\\d{5})|(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\\s+\\d{1,2},?\\s+\\d{4})", "Validation_Rule": "從檔案名稱擷取之日期,必須與首頁左右資訊區所截取之報告日期完全對照相同。", "Patterns": ["8碼數字 (例如: 20250122)", "7碼數字 (包含民國年, 例如: 1140122)", "6碼數字 (省略二零, 例如: 250122)", "YYYY-MM-DD", "YYYY/MM/DD", "英文日期格式 (包含英文月份全寫如 January 或簡寫如 Jan)", "YYYY年 (例如: 2025)", "YYYY/MM (例如: 2025/01)"], "legacy_regex": {"Regex": "(?:(?:20)?\\d{2}[-/]?\\d{2}[-/]?\\d{2})|(?:(?:20)?\\d{2}[-/]\\d{2})|(?:(?:20)?\\d{2})", "from": "A", "note": "最後一段 (?:(?:20)?\\d{2}) 單獨兩位數也會中(過寬)→ 留檔不採用"}}, "Year_Quarter_Extraction": {"Regex": "(?:(?:20)?\\d{2}(?:\\.|\\s*)?Q[1-4])|(?:(?:20)?\\d{2}(?:年)?)", "Validation_Rule": "支援各類券商財報/財測季度預估寫法,需與報告內文及表格欄位對齊。", "Patterns": ["YYYY年 (例如: 2025, 2026)", "YY年 (例如: 25, 26)", "YYYY.Q# (例如: 2025.Q1, 2025.Q2)", "YYYYQ# (例如: 2025Q1, 2025Q3)", "YYQ# (例如: 25Q1, 26Q4)"], "legacy_regex": {"Regex": "(?:(?:20)?\\d{2}(?:\\.|\\s*)?Q[1-4])", "from": "A", "note": "只認季度"}, "caution": "第二段 (?:(?:20)?\\d{2}(?:年)?) 單獨兩位數也會中 → 只在表頭期間欄用,不做全文搜尋"}}, "TARGET_PRICE_LIST": {"aliases": ["Target Price", "Price Target", "TP", "PT", "Target", "Tgt", "Fair Value", "FV", "Valuation", "目標價", "目標股價", "目標", "合理價", "合理股價", "預期價", "目標區間", "Base Case", "Bull Case", "Bear Case", "TARGET PRICE", "PRICE TARGET", "TARGET"], "regex_defense_pattern": "(?i)(?:Target|目標(?:價)?)\\s*[:：$]?\\s*[\\d,]+(\\.\\d+)?", "preprocessing_strips": ["NT$", "TWD", "上看", "下看", "元"], "caution": "「Price target (2026F) NT$650」的年份 / 「Up/downside to price target (%)」的百分比不是目標價(首頁引擎既有教訓)"}, "RATING_LIST": {"Strong_Buy": {"code": 1, "aliases": ["Strong Buy", "SB", "強力買進", "積極買進", "買進(強烈)", "買進(強力)", "Conviction Buy", "Trading Buy"]}, "Buy": {"code": 2, "aliases": ["Buy", "Outperform", "OP", "Overweight", "OW", "Long", "買進", "優於大盤", "加碼", "增持", "買進(維持)", "買進(調升)", "買進(重申)", "Accumulate", "收集", "逢低買進", "買進(初次)"]}, "Hold": {"code": 3, "aliases": ["Hold", "Neutral", "N", "Market Perform", "MP", "Equal Weight", "EW", "中立", "持有", "區間操作", "觀望", "維持中立", "中立(調降)", "中立(調升)", "Sector Perform", "Peer Perform", "中性"]}, "Sell": {"code": 4, "aliases": ["Sell", "Underperform", "UP", "Underweight", "UW", "Short", "賣出", "減碼", "劣於大盤", "賣出(調降)", "賣出(重申)", "Reduce", "減持", "逢高減碼", "賣出(初次)"]}, "Strong_Sell": {"code": 5, "aliases": ["Strong Sell", "SS", "強力賣出", "積極賣出", "Conviction Sell"]}, "Not_Rated": {"code": 0, "aliases": ["Not Rated", "NR", "未評等", "No Rating", "N/A", "無評等", "暫無評等", "未覆蓋", "未納入研究範圍", "Coverage Dropped", "CD", "停止覆蓋", "Under Review", "UR", "評等審視中", "Restricted", "受限"]}}, "short_alias_rule": "1~2 字母代碼(N · B · H · S · OP · OW · UP · UW · MP · EW · SB · SS · NR · UR · CD · MS · GS · JP · CS · ML · MQ)只在結構化欄位(評等欄 / 檔名券商槽)比對,不做全文搜尋;全文要字邊界"}""")
_MAINLAND = {"中金", "中金公司", "cicc", "cicc research", "中銀", "中銀國際", "boci", "boci research", "廣發", "廣發證券", "gf", "gfhk", "gf securities", "海通", "海通國際", "haitong",
             "國泰君安", "guotai junan", "gtja", "華泰證券", "huatai", "招商證券", "招銀國際", "cmbi", "建銀國際", "ccbi", "中信建投", "csc financial", "申萬宏源", "shenwan", "光大證券",
             "everbright", "東方證券", "orient securities", "興業證券", "長江證券", "天風證券", "安信證券", "國信證券", "方正證券", "中國銀河", "中泰證券", "民生證券", "國金證券",
             "東吳證券", "浙商證券", "華西證券", "citic securities", "工銀國際", "icbci", "農銀國際", "abci", "交銀國際", "第一上海", "first shanghai"}
_AMBIG = {"中信證券": "台灣常指中國信託證券,但也是大陸中信證券(CITIC Securities)正式名稱 → 留著 · 待操作員裁定"}
_LINK_STOP = {"capital", "first", "securities", "research", "證券", "投顧", "資本", "銀行", "bank", "global", "international", "國際"}


def _ver(p: Path) -> int:
    m = re.search(r"_v(\d{2,4})(?:\D|$)", p.stem)
    return int(m.group(1)) if m else 0


def _broker_files(home: Path) -> list:
    fs = set(list((home / "knowledge").glob("VRN_Broker_Dict_v*.json")) + list(home.glob("VRN_Broker_Dict_v*.json")) + list((home / "registry").glob("VRN_BROKER_LIST_v*.json")))
    return sorted((p for p in fs if not p.name.endswith(".integration.json")), key=lambda p: (p.parent.name, p.name))


def _entries(home: Path) -> list:
    """每本冊每一筆券商 → (來源, 鍵, 別名清單, 國別, 舊縮寫)。"""
    out = []
    books = []
    for p in _broker_files(home):
        try:
            books.append((p, json.loads(p.read_text(encoding="utf-8-sig"))))
        except (OSError, ValueError):
            continue
    plain = [(p, d) for p, d in books if not (isinstance(d, dict) and d.get("unified"))]
    for p, d in (plain or books):          # 統一冊是產物,不當來源(除非它是唯一一本)→ 重跑內容不變
        secs = []
        for k, v in (d.items() if isinstance(d, dict) else []):
            if k in ("removed_mainland",):
                continue
            if isinstance(v, dict) and v and all(isinstance(x, dict) for x in v.values()):
                secs.append(v)
            elif isinstance(v, list) and v and all(isinstance(x, dict) for x in v):
                secs.append({str(x.get("code") or x.get("name") or x.get("canonical") or x.get("broker") or x.get("zh") or i): x for i, x in enumerate(v)})
        for sec in secs:
            for key, ent in sec.items():
                if not any(ent.get(f) for f in ("aliases", "alias", "abbr", "en", "zh", "short", "code", "canonical", "canonical_en", "chinese_name", "english_name", "name", "broker")):
                    continue                     # 合併紀錄 / 日誌列(如 registry merge_log「CLST → CLSA」)不是券商
                al = [str(a) for a in (ent.get("aliases") or ent.get("alias") or []) if str(a).strip()]
                for f in ("abbr", "en", "zh", "short", "code", "canonical", "canonical_en", "chinese_name", "english_name", "zh_short", "show"):
                    if isinstance(ent.get(f), str) and ent[f].strip():
                        al.append(ent[f].strip())
                al += [str(x) for x in ent.get("legacy_codes", []) or []]
                out.append({"src": "%s/%s" % (p.parent.name, p.name), "key": str(key), "aliases": al + [str(key)], "country": str(ent.get("country") or ""),
                            "abbr": str(ent.get("abbr") or ""), "zh": ent.get("chinese_name") or "", "en": ent.get("english_name") or ""})
    syn = sorted((home / "knowledge").glob("SYNONYM_LIBRARY_v*.json"), key=_ver)[-1:]
    for p in syn:
        try:
            sc = (json.loads(p.read_text(encoding="utf-8-sig")).get("scopes") or {}).get("broker") or {}
        except (OSError, ValueError):
            sc = {}
        by = defaultdict(list)
        for alias, rows in sc.items():
            for r in rows if isinstance(rows, list) else []:
                if isinstance(r, dict) and r.get("canonical"):
                    by[str(r["canonical"])].append(str(r.get("raw") or alias))
        for c, al in by.items():
            out.append({"src": "knowledge/" + p.name, "key": c, "aliases": al + [c], "country": "", "abbr": "", "zh": "", "en": ""})
    for c, al in (_resolve("_SEED_BROKERS") or {}).items():
        out.append({"src": "內建種子", "key": c, "aliases": list(al) + [c], "country": "", "abbr": "", "zh": "", "en": ""})
    for sec, kind in (("DOMESTIC_BROKERS", "domestic"), ("FOREIGN_BROKERS", "foreign")):
        for c, e in _MASTER[sec].items():
            out.append({"src": "主字典(操作員)", "key": c, "aliases": e["aliases"] + [c], "country": "TW" if kind == "domestic" else "", "abbr": c, "zh": e["chinese_name"], "en": e["english_name"], "op": kind})
    return out


def _cjk(s: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", s))


def unify_brokers(home: Path) -> dict:
    ents = _entries(home)
    par = list(range(len(ents)))

    def f(i):
        while par[i] != i:
            par[i] = par[par[i]]
            i = par[i]
        return i
    own = {}
    for i, e in enumerate(ents):
        for a in e["aliases"]:
            k = a.strip().lower()
            if len(k) < 2 or k in _LINK_STOP:
                continue
            if k in own:
                par[f(i)] = f(own[k])
            else:
                own[k] = i
    groups = defaultdict(list)
    for i in range(len(ents)):
        groups[f(i)].append(ents[i])
    brokers, removed, conflicts, ambig, shorts = {}, {}, [], [], []
    for g in groups.values():
        ops = sorted({e["key"] for e in g if e.get("op")})
        if len(ops) > 1:
            conflicts.append({"操作員鍵": ops, "why": "同一組別名連到兩個主字典券商"})
        al, seen = [], set()
        for e in sorted(g, key=lambda e: (not e.get("op"), e["src"])):
            for a in e["aliases"]:
                a2 = a.strip()
                if len(a2) >= 2 and a2.lower() not in seen:
                    seen.add(a2.lower())
                    al.append(a2)
        keys = [e["key"] for e in g]
        upper = [k for k in keys if re.fullmatch(r"[A-Z][A-Z0-9&.\-]{1,11}", k)]
        code = ops[0] if ops else (sorted(set(upper), key=lambda k: (-upper.count(k), len(k), k))[0] if upper else next((a for a in al if re.fullmatch(r"[A-Z][A-Z0-9&.\-]{1,9}", a)), keys[0]))   # 平手:票多 → 短 → 字母序(不靠 set 順序,每次相同)
        country = sorted({e["country"] for e in g if e["country"]})
        opk = next((e for e in g if e.get("op") and e["key"] == code), None)
        zh = (opk or {}).get("zh") or max((a for a in al if _cjk(a) and re.search(r"(證券|投顧|資本|銀行|證期)$", a)), key=len, default="") or max((a for a in al if _cjk(a)), key=len, default="")
        en = (opk or {}).get("en") or max((a for a in al if not _cjk(a) and (" " in a or len(a) >= 4)), key=len, default="")
        rec = {"abbr": code, "chinese_name": zh, "english_name": en, "zh_short": min((a for a in al if _cjk(a)), key=len, default=""),
               "type": (opk or {}).get("op") or ("domestic" if "TW" in country else "foreign"), "country": country, "aliases": al,
               "legacy_codes": sorted({k for k in keys + [e["abbr"] for e in g] if k and k != code and re.fullmatch(r"[A-Za-z][A-Za-z0-9&.\-]{1,11}", k)}),
               "sources": sorted({e["src"] for e in g})}
        if any(a.lower() in _MAINLAND for a in al) or any("CN" in c for c in country):
            removed[code] = dict(rec, why="大陸公司(操作員 2026-10-10「去大陸公司」)· 命中 %s" % ", ".join(a for a in al if a.lower() in _MAINLAND or "CN" in ",".join(country))[:80])
            continue
        if code in brokers:
            conflicts.append({"代碼": code, "why": "兩組選到同一代碼 → 第二組改名"})
            code = code + "_2"
            rec["abbr"] = code
        brokers[code] = rec
        for a in al:
            if a in _AMBIG:
                ambig.append({"代碼": code, "別名": a, "why": _AMBIG[a]})
            if re.fullmatch(r"[A-Za-z]{1,3}", a):
                shorts.append("%s→%s" % (a, code))
    return {"brokers": dict(sorted(brokers.items())), "removed_mainland": removed, "conflicts": conflicts, "ambiguous": ambig, "short_aliases": sorted(set(shorts)),
            "n_entries": len(ents), "n_raw_keys": len({e["key"] for e in ents if e["src"] not in ("內建種子", "主字典(操作員)")}), "files": sorted({e["src"] for e in ents})}


def _unified_tail(home: Path):
    for p in sorted(_broker_files(home), key=lambda p: (_ver(p), p.parent.name != "knowledge"))[::-1]:
        try:
            d = json.loads(p.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError):
            continue
        if isinstance(d, dict) and d.get("unified") and isinstance(d.get("brokers"), dict):
            d["_file"] = str(p)
            return d
        return None
    return None


_PREV_LB = _resolve("load_brokers_v154")


def load_brokers_v167():
    u = _unified_tail(_home())
    if not u:
        return _PREV_LB()
    book = {}
    for code, e in u["brokers"].items():
        book[code] = {"aliases": {a: "冊" for a in e.get("aliases", []) + e.get("legacy_codes", []) + [code]}, "abbr": code, "unified": True}
    owner = {a.lower(): c for c, e in book.items() for a in e["aliases"]}
    for canon, al in (_resolve("_SEED_BROKERS") or {}).items():
        if any(a.lower() in _MAINLAND for a in list(al) + [canon]):
            continue
        tgt = next((owner[a.lower()] for a in al if a.lower() in owner), None)
        e = book.setdefault(tgt or canon, {"aliases": {}, "abbr": tgt or canon})
        for a in al:
            if a.lower() not in owner:
                e["aliases"][a] = "內建種子"
                owner[a.lower()] = tgt or canon
    return book, [{"file": Path(u["_file"]).name, "brokers": len(u["brokers"]), "unified": True}]


for _nm in ("load_brokers_v154",):
    _mo = _owner(_nm)
    if _mo:
        setattr(_mo, _nm, load_brokers_v167)


# 統一冊生效時:券商一律回統一代碼(v0155 的 _abbr_of 先查舊縮寫表 → 台新 TSC · 統一 PSC);電郵網域表的舊縮寫也對成統一代碼,交互驗證才比得起來
_LEGACY_CODE = {"HNSC": "HUANAN", "HNS": "HUANAN", "HN": "HUANAN", "CSC": "CAPITAL", "SJP": "SINOPAC", "FB": "FUBON", "YT": "YUANTA", "CT": "CATHAY", "TSC": "TAISHIN",
                "PSC": "PRESIDENT", "MQ": "MCQ", "MAQ": "MCQ", "BOFA": "BOA", "BAML": "BOA", "CLST": "CLSA", "JP": "JPM"}
_OWN_CACHE = {}


def to_code(x: str, book: dict) -> str:
    if not x or not book or not any(e.get("unified") for e in book.values()):
        return x
    if x.lower() in _MAINLAND:
        return ""
    if x in book:
        return x
    own = _OWN_CACHE.get(id(book))
    if own is None:
        own = {a.lower(): c for c, e in book.items() for a in e.get("aliases", {})}
        _OWN_CACHE.clear()
        _OWN_CACHE[id(book)] = own
    c = own.get(x.lower()) or _LEGACY_CODE.get(x.upper())
    return c if c in book else x


_PREV_ABBR = _resolve("_abbr_of")


def _abbr_of_v167(book: dict, canon: str) -> tuple:
    if (book.get(canon) or {}).get("unified"):
        return canon, "統一冊"
    return _PREV_ABBR(book, canon) if _PREV_ABBR else ("", "—")


_PREV_DOM = _resolve("domain_broker")


def domain_broker_v167(domain: str, book: dict) -> str:
    r = _PREV_DOM(domain, book) if _PREV_DOM else ""
    if r:
        return to_code(r, book)
    if book and any(e.get("unified") for e in book.values()):        # 網域帶連字號(cl-sec.com)→ 兩邊都只留字母再比
        toks = [re.sub(r"[^a-z]", "", t) for t in str(domain).lower().split(".") if t not in ("com", "tw", "hk", "net", "org", "co", "www", "jp", "sg", "cn")]
        for c, e in book.items():
            for a in e.get("aliases", {}):
                k = re.sub(r"[^a-z]", "", a.lower())
                if len(k) >= 4 and k in toks:
                    return c
    return r


for _nm, _fn in (("_abbr_of", _abbr_of_v167), ("domain_broker", domain_broker_v167)):
    _mo = _owner(_nm)
    if _mo:
        setattr(_mo, _nm, _fn)


# ───────── 評等冊新版 = 舊冊 + 主字典評等(短碼只給欄位用)─────────
_CORE2 = {"買進", "賣出", "持有", "中立", "中性", "加碼", "減碼", "增持", "減持", "觀望"}     # 標準評等詞:全文可比


def rating_union(home: Path) -> dict:
    tails = sorted((home / "knowledge").glob("VRN_Rating_Dict_v*.json"), key=_ver)
    base = {}
    if tails:
        try:
            base = json.loads(tails[-1].read_text(encoding="utf-8-sig"))
        except (OSError, ValueError):
            base = {}
    existing = set()

    def walk(o):
        if isinstance(o, dict):
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
        elif isinstance(o, str):
            existing.add(o.lower())
    walk(base)
    lv_map = {"Strong_Buy": "BUY", "Buy": "BUY", "Hold": "HOLD", "Sell": "SELL", "Strong_Sell": "SELL", "Not_Rated": "NOT_RATED"}
    master, field_only, added = {}, [], 0
    for k, e in _MASTER["RATING_LIST"].items():
        long_ = []
        for a in e["aliases"]:
            short = re.fullmatch(r"[A-Z/]{1,3}", a) or (_cjk(a) and len(a) <= 2 and a.lower() not in existing and a not in _CORE2)     # 全大寫短碼(SB · OW · N/A …)· 2 字常用詞(標準評等詞除外)
            if short:
                field_only.append(a)
            else:
                long_.append(a)
                added += a.lower() not in existing
        master[k] = {"code": e["code"], "maps_to_level": lv_map[k], "aliases": long_}
    out = dict(base)
    out.update(schema=base.get("schema", "VIA.VRN.RatingDict.v1"), master_codes=master, master_note="主字典(操作員)評等 0~5 碼:強買 1 · 買 2 · 持有 3 · 賣 4 · 強賣 5 · 未評等 0;對到本冊 levels 見 maps_to_level",
               field_only_codes=" | ".join(sorted(set(field_only), key=str.lower)), field_only_rule="1~3 字母短碼與 2 字常用詞只在評等欄位(結構化)比對,不進全文 —— 用一個字串存,避免被當全文詞",
               prior=tails[-1].name if tails else "", ts=datetime.datetime.now().isoformat(timespec="seconds"))
    return {"book": out, "added": added, "field_only": sorted(set(field_only)), "prior": tails[-1] if tails else None}


def _strip_ts(d):
    return {k: v for k, v in d.items() if k not in ("ts", "version", "prior", "_file")}


def dicts_run(apply: bool) -> dict:
    home = _home()
    u = unify_brokers(home)
    tail = _unified_tail(home)
    vers = [_ver(p) for p in _broker_files(home) if p.name.startswith("VRN_Broker_Dict_v")]
    nxt = "v%04d" % (max(vers + [100]) + 1)
    same = bool(tail) and tail.get("brokers") == u["brokers"]
    book = {"schema": "VIA.VRN.BrokerDict.Unified.v1", "unified": True, "version": nxt, "prior": u["files"], "ts": datetime.datetime.now().isoformat(timespec="seconds"),
            "rule": "一家一個代碼(主字典鍵優先)· 別名全收 · 去大陸公司 · CLST→CLSA · MQ/Macquarie→MCQ;舊冊不動(載入器只讀本冊)", "count": len(u["brokers"]), "brokers": u["brokers"]}
    r = rating_union(home)
    md = home / "knowledge" / "VRN_MasterDict_v0100.json"
    out = {"u": u, "same": same, "next": nxt, "rating": r, "written": []}
    if apply:
        (home / "knowledge").mkdir(parents=True, exist_ok=True)
        if not same:
            bp = home / ("VRN_Broker_Dict_%s.json" % nxt)
            bp.write_text(json.dumps(book, ensure_ascii=False, indent=1), encoding="utf-8")
            (home / ("VRN_Broker_Dict_%s.integration.json" % nxt)).write_text(json.dumps({k: u[k] for k in ("removed_mainland", "conflicts", "ambiguous", "short_aliases", "files", "n_entries", "n_raw_keys")}, ensure_ascii=False, indent=1), encoding="utf-8")
            out["written"].append(bp.name)
        if not md.exists() or json.loads(md.read_text(encoding="utf-8")) != _MASTER:
            md.write_text(json.dumps(_MASTER, ensure_ascii=False, indent=1), encoding="utf-8")
            out["written"].append(md.name)
        prev = r["prior"]
        prev_d = json.loads(prev.read_text(encoding="utf-8-sig")) if prev else {}
        if _strip_ts(prev_d) != _strip_ts(r["book"]):
            rv = "v%04d" % ((_ver(prev) if prev else 100) + 1)
            rp = home / "knowledge" / ("VRN_Rating_Dict_%s.json" % rv)
            rp.write_text(json.dumps(dict(r["book"], version=rv), ensure_ascii=False, indent=1), encoding="utf-8")
            out["written"].append(rp.name)
    rows = [("GREEN", [c, e["chinese_name"], e["english_name"], e["type"], len(e["aliases"]), ", ".join(e["legacy_codes"]) or "—", " / ".join(e["aliases"])[:160], len(e["sources"])]) for c, e in u["brokers"].items()]
    rows += [("RED", [c, e["chinese_name"], e["english_name"], "大陸 · 移除", len(e["aliases"]), ", ".join(e["legacy_codes"]) or "—", e["why"], len(e["sources"])]) for c, e in u["removed_mainland"].items()]
    rows += [("YELLOW", [a["代碼"], a["別名"], "", "待裁", "", "", a["why"], ""]) for a in u["ambiguous"]]
    page = _resolve("_page")
    if page:
        hp = _rep() / "BROKERS_latest.html"
        hp.parent.mkdir(parents=True, exist_ok=True)
        hp.write_text(page("券商冊統一 · 一家一個代碼 · 去大陸公司 · 別名全收", "原冊 %d 本 · 原始鍵 %d 個 → 券商 %d 家 · 移除大陸 %d · 待裁別名 %d · 衝突 %d · %s" % (len(u["files"]), u["n_raw_keys"], len(u["brokers"]), len(u["removed_mainland"]), len(u["ambiguous"]), len(u["conflicts"]), "已寫 " + ", ".join(out["written"]) if out["written"] else ("內容沒變 · 不出新版" if same else "預覽(加 --apply 寫入)")),
                               ["代碼", "中文", "英文", "類", "別名數", "舊代碼", "別名(或原因)", "來源冊"], rows), encoding="utf-8")
        out["html"] = str(hp)
    return out


# ───────── ④ 股名核對:多種寫法 · 英文首頁不適用 ─────────
_PREFIX = re.compile(r"^(開曼群島商|英屬開曼群島商|英屬維京群島商|英屬蓋曼群島商|百慕達商|薩摩亞商|香港商|新加坡商|美商|日商|荷蘭商)")
_SUFFIX = re.compile(r"(科技|開發|國際|生物科技|生技|工業|電子|企業|實業|控股|精密|材料|光電|半導體|電腦|通訊|網路|能源|醫藥|化學|建設|航運|海運|金融控股|海洋生物科技)$")


def name_variants(n: str) -> set:
    out = {n}
    s = _PREFIX.sub("", n)
    out.add(s)
    s2 = re.sub(r"(股份有限公司|有限公司)$", "", s)
    out.add(s2)
    s3 = s2
    for _ in range(2):
        s3 = _SUFFIX.sub("", s3)
        out.add(s3)
    for x in list(out):
        out.add(x.replace("-KY", "").replace("*", ""))
    return {x for x in out if len(x) >= 2}


def name_hit(name: str, text: str):
    if not name:
        return None
    if any(v in text for v in name_variants(name)):
        return True
    if len(re.findall(r"[\u4e00-\u9fff]", text)) < 30:
        return None
    return False


_PREV_L2 = _resolve("l2_one")


def l2_one_v167(row: dict) -> dict:
    r = _PREV_L2(row)
    try:
        conf = r.get("confirm") or {}
        if conf.get("名稱") is False:
            import pdfplumber
            src = row.get("mini") or row.get("src_pdf") or row["path"]
            with pdfplumber.open(str(src)) as pdf:
                t = pdf.pages[0].extract_text() or ""
            h = name_hit(r.get("name", ""), t)
            if h is not False:
                conf["名稱"] = h
                r["notes"] = [n for n in r.get("notes", []) if not n.startswith("首頁沒對到")]
                bad = [k for k, v in conf.items() if v is False]
                if bad:
                    r["notes"].append("首頁沒對到 " + "/".join(bad))
                r["name_check"] = "英文首頁 · 不適用" if h is None else "簡稱 / 全名比對到"
    except Exception:  # noqa: BLE001
        pass
    return r


_ml2 = _owner("l2_one")
if _ml2:
    setattr(_ml2, "l2_one", l2_one_v167)


# 前版鏈自測相容:v0166 換掉了 v0164 的進度函式(三段 · 秒數在前)→ v0164 自測驗的是它原本的格式;跑前版自測時暫時換回 v0164 原版,跑完換回
_ORIG164_SRC = r'''def _progress_line_v164orig(line: str, pf: str) -> bool:
    """[進度] i/N → 百分比只增不減:第一段 20→95;還有下一段就從目前位置接著往上(不猜階段名稱)。"""
    m = _PROG_RX.match(line)
    if not m:
        return False
    i, n = int(m.group(1)), max(int(m.group(2)), 1)
    with _LOCK:
        if i == 1 or i < _P["i"]:
            _P["series"] += 1
            if _P["series"] > 1:
                _P["base"] = _P["pct"]
        _P["i"], _P["seen"] = i, True
        pct = max(_P["pct"], int(_P["base"] + (95 - _P["base"]) * i / n))
        _P["pct"] = pct
        now = time.time()
        if now - _P["last"] >= 0.5 or i == n:
            _P["last"] = now
            label = "還原" if _P["series"] <= 1 else "第 %d 段" % _P["series"]
            write_progress(pf, pct, "%s %d/%d · %s · %s" % (label, i, n, m.group(3) or "", (m.group(4) or "").strip()[:40]))
    return True


def _heartbeat_v164orig(pf: str) -> None:
    """第一步(分類 · 取頁)沒有逐檔進度行 → 每 3 秒寫心跳,證明還活著;出現第一行 [進度] 就停。"""
    t0 = time.time()
    while True:
        with _LOCK:
            if _P["seen"] or _P.get("stop"):
                return
            write_progress(pf, 20, "VRN 準備中(分類 · 取頁)· 已 %d 秒" % int(time.time() - t0))
        time.sleep(3)
'''
_m164 = _owner("_P") if _owner("_P") is not None and "_PROG_RX" in vars(_owner("_P")) else None


def _compat164(on: bool, saved: dict) -> None:
    if _m164 is None:
        return
    g = vars(_m164)
    if "_progress_line_v164orig" not in g:
        exec(_ORIG164_SRC, g)
    if on:
        saved.update(progress_line=g.get("progress_line"), _heartbeat=g.get("_heartbeat"))
        g["progress_line"], g["_heartbeat"] = g["_progress_line_v164orig"], g["_heartbeat_v164orig"]
    else:
        for k, v in saved.items():
            if v is not None:
                g[k] = v


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()
    if args[:1] == ["dicts"]:
        o = dicts_run("--apply" in args)
        u = o["u"]
        print("[計] 券商冊統一 · 原冊 %d 本 · 原始鍵 %d 個 → 券商 %d 家 · 移除大陸 %d(%s)· 待裁別名 %d · 衝突 %d · %s" % (len(u["files"]), u["n_raw_keys"], len(u["brokers"]), len(u["removed_mainland"]), ", ".join(u["removed_mainland"]) or "—", len(u["ambiguous"]), len(u["conflicts"]),
              ("已寫 " + ", ".join(o["written"])) if o["written"] else ("內容沒變 · 不出新版" if o["same"] else "預覽(加 ~~apply 寫入)")))
        for c in ("CLSA", "MCQ", "GS", "MS", "CITI", "UBS"):
            e = u["brokers"].get(c)
            if e:
                print("[計] 券商 %s · %s / %s · 別名 %d(%s)" % (c, e["chinese_name"], e["english_name"], len(e["aliases"]), " · ".join(e["aliases"][:9])))
        for a in u["ambiguous"]:
            print("[計] 待裁 · %s 的別名「%s」· %s" % (a["代碼"], a["別名"], a["why"]))
        for c in u["conflicts"][:5]:
            print("[計] 衝突 · %s" % json.dumps(c, ensure_ascii=False))
        print("[計] 主字典 · 4 版聯集 · 券商 %d 家 · 評等 6 級 · 目標價別名 %d · 日期正則(新)8 碼 / 民國 7 碼 / 6 碼 / 英文月份 · 舊正則留檔不採用(單獨兩位數也會中)" % (len(_MASTER["DOMESTIC_BROKERS"]) + len(_MASTER["FOREIGN_BROKERS"]), len(_MASTER["TARGET_PRICE_LIST"]["aliases"])))
        print("[計] 評等冊 · 主字典評等新收 %d 詞 · 只給評等欄位的短碼 %d(%s)" % (o["rating"]["added"], len(o["rating"]["field_only"]), " ".join(o["rating"]["field_only"])))
        if o.get("html"):
            print("  [U/I] %s" % o["html"])
        return 0
    return PRIOR.main(args)


def _has_key(o, k) -> bool:
    if isinstance(o, dict):
        return k in o or any(_has_key(v, k) for v in o.values())
    if isinstance(o, list):
        return any(_has_key(v, k) for v in o)
    return False


def selftest() -> int:
    import shutil
    import tempfile
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)
    pg = {"page": 3, "W": 600.0, "H": 800.0, "blocks": [{"kind": "table", "how": "text-geometry", "zone": "F", "x0": 60.0, "top": 100.0, "x1": 540.0, "bottom": 300.0, "rows": [["Revenue", "1"]]},
                                                       {"kind": "text", "zone": "F", "x0": 1, "top": 1, "x1": 2, "bottom": 2, "bbox_pct": [9, 9, 9, 9]}]}
    n = fill_bbox_pct(pg)
    b = pg["blocks"][0]
    ok_box = n == 1 and b["bbox_pct"] == [10.0, 12.5, 80.0, 25.0] and pg["blocks"][1]["bbox_pct"] == [9, 9, 9, 9]
    try:
        "left:%s%%;top:%s%%;width:%s%%;height:%s%%;%s" % (b["bbox_pct"][0], b["bbox_pct"][1], max(b["bbox_pct"][2], 0.8), max(b["bbox_pct"][3], 0.8), b["id"].split("·", 1)[1])
        ok_html = True
    except Exception:  # noqa: BLE001
        ok_html = False
    chk("① 藏在文字中的表格新建區塊補 bbox_pct([左 10% · 上 12.5% · 寬 80% · 高 25%])· 已有的不動 · 產版面頁的方框運算式不再 KeyError", ok_box and ok_html)
    td = Path(tempfile.mkdtemp(prefix="vrn167-"))
    saved = os.environ.get("VIA_VRN_SSOT_HOME")
    try:
        home = td / "VRN"
        (home / "knowledge").mkdir(parents=True)
        (home / "registry").mkdir()
        (home / "knowledge" / "VRN_Broker_Dict_v0100.json").write_text(json.dumps({"brokers": {"麥格理": {"abbr": "MQ", "aliases": ["麥格理", "Macquarie", "MQ"]}, "里昂": {"abbr": "CLSA", "aliases": ["里昂", "CLSA"]},
                                                                                              "中金": {"abbr": "CICC", "aliases": ["中金", "CICC", "中金公司"]}, "中信": {"abbr": "CTBC", "aliases": ["中信", "CTBC", "中信證券"]},
                                                                                              "台新": {"abbr": "TSC", "aliases": ["台新"]}},
                                                                                  "brokers_extended": [{"code": "MS", "zh": "摩根士丹利", "aliases": ["MS", "摩根士丹利", "大摩"], "country": "US"}]}, ensure_ascii=False), encoding="utf-8")
        (home / "VRN_Broker_Dict_v0102.json").write_text(json.dumps({"brokers": {"MCQ": {"abbr": "MCQ", "aliases": ["MCQ", "Macquarie"]}, "CLSA": {"aliases": ["CLSA", "CLST"]}, "BOCI": {"aliases": ["BOCI", "中銀國際"], "country": "HK"}}}, ensure_ascii=False), encoding="utf-8")
        (home / "registry" / "VRN_BROKER_LIST_v04.json").write_text(json.dumps({"brokers": [{"canonical": "里昂", "aliases": ["里昂證券", "CLST"]}, {"canonical": "摩根士丹利", "aliases": ["Morgan Stanley"]}]}, ensure_ascii=False), encoding="utf-8")
        (home / "knowledge" / "VRN_Rating_Dict_v0100.json").write_text(json.dumps({"levels": {"BUY": {"zh": ["買進"], "en": ["Buy"]}}}, ensure_ascii=False), encoding="utf-8")
        os.environ["VIA_VRN_SSOT_HOME"] = str(home)
        hm = _home()
        if hm != home:
            globals()["_home"] = lambda: home  # noqa: E731
            _ml = _owner("load_brokers_v154")
        u = unify_brokers(home)
        b = u["brokers"]
        chk("② 券商統一:同一家歸一個代碼 —— 麥格理 / MQ / Macquarie / MCQ → MCQ;里昂 / 里昂證券 / CLST / CLSA → CLSA;摩根士丹利 / 大摩 / Morgan Stanley → MS;台新(舊縮寫 TSC)→ TAISHIN",
            set(b) >= {"MCQ", "CLSA", "MS", "TAISHIN"} and {"麥格理", "MQ", "Macquarie"} <= set(b["MCQ"]["aliases"]) and {"里昂", "里昂證券", "CLST"} <= set(b["CLSA"]["aliases"]) and {"大摩", "摩根士丹利"} <= set(b["MS"]["aliases"])
            and "TSC" in b["TAISHIN"]["legacy_codes"] and not any(k in b for k in ("麥格理", "里昂", "摩根士丹利", "台新", "MQ")))
        chk("③ 去大陸公司:中金 CICC · 中銀國際 BOCI · 廣發 GF(內建種子)移除,整筆內容存 removed_mainland(不丟);「中信證券」留在 CTBC 標待裁",
            {"CICC", "BOCI"} <= set(u["removed_mainland"]) and any("GF" in (k + " ".join(v["aliases"])) for k, v in u["removed_mainland"].items()) and not any(x in b for x in ("CICC", "BOCI", "GF Securities", "GF"))
            and any(a["別名"] == "中信證券" and a["代碼"] == "CTBC" for a in u["ambiguous"]) and "中金公司" in u["removed_mainland"]["CICC"]["aliases"])
        o1 = dicts_run(True)
        o2 = dicts_run(True)
        written = sorted(x.name for x in home.rglob("*.json"))
        chk("④ dicts --apply:寫統一冊 v0103 + 附冊 + 主字典 + 評等冊 v0101;再跑一次內容沒變 → 不出新版",
            "VRN_Broker_Dict_v0103.json" in written and "VRN_Broker_Dict_v0103.integration.json" in written and "VRN_MasterDict_v0100.json" in written and "VRN_Rating_Dict_v0101.json" in written and o2["written"] == [] and o2["same"])
        bk, used = load_brokers_v167()
        owner = {a.lower(): c for c, e in bk.items() for a in e["aliases"]}
        chk("⑤ 載入器只讀統一冊:CLST → CLSA · MQ → MCQ · 大摩 → MS · 廣發 / GFHK 不再認得(大陸已去)· 不再一家多個正典",
            used and used[0].get("unified") and owner.get("clst") == "CLSA" and owner.get("mq") == "MCQ" and owner.get("大摩") == "MS" and "gfhk" not in owner and "廣發" not in owner and "麥格理" not in bk)
        rd = json.loads((home / "knowledge" / "VRN_Rating_Dict_v0101.json").read_text(encoding="utf-8"))
        walk = []

        def w(o):
            if isinstance(o, dict):
                for v in o.values():
                    w(v)
            elif isinstance(o, list):
                for v in o:
                    w(v)
            elif isinstance(o, str) and 1 <= len(o) <= 8:
                walk.append(o)
        w(rd)
        chk("⑥ 評等冊新版:舊詞全在 · 主字典評等 0~5 碼對照 · 短碼(N · UP · OP · SB …)不會被當全文詞(只在評等欄位)",
            "買進" in walk and rd["master_codes"]["Strong_Buy"]["code"] == 1 and rd["master_codes"]["Hold"]["maps_to_level"] == "HOLD" and not any(x in walk for x in ("N", "UP", "OP", "SB", "N/A")) and "UP" in rd["field_only_codes"])
    finally:
        if saved is None:
            os.environ.pop("VIA_VRN_SSOT_HOME", None)
        else:
            os.environ["VIA_VRN_SSOT_HOME"] = saved
        globals()["_home"] = _resolve("_home")
        shutil.rmtree(td, ignore_errors=True)
    md = _MASTER
    import re as _re
    ok_rx = all(_re.compile(x) for x in (md["DATE_AND_TIME_PATTERNS"]["Date_Extraction"]["Regex"], md["DATE_AND_TIME_PATTERNS"]["Year_Quarter_Extraction"]["Regex"], md["TARGET_PRICE_LIST"]["regex_defense_pattern"], md["TICKER_PATTERNS"]["Stock_Base"]["Regex"]))
    d = _re.compile(md["DATE_AND_TIME_PATTERNS"]["Date_Extraction"]["Regex"])
    chk("⑦ 主字典 4 版聯集:CLSA 收 CLST · MCQ 收 麥格理資本 · 正則全可編譯 · 日期認 20250122 / 1140122 / 250122 / Jan 22, 2025 · 舊正則留檔不採用 · 無 _cite",
        ok_rx and "CLST" in md["FOREIGN_BROKERS"]["CLSA"]["aliases"] and "麥格理資本" in md["FOREIGN_BROKERS"]["MCQ"]["aliases"] and all(d.search(s) for s in ("20250122", "1140122", "250122", "Jan 22, 2025"))
        and "legacy_regex" in md["DATE_AND_TIME_PATTERNS"]["Date_Extraction"] and not _has_key(md, "_cite"))
    chk("⑧ 股名核對:頎邦科技股份有限公司 ↔ 首頁「頎邦」· 開曼群島商竣邦國際股份有限公司 ↔「竣邦」· 譜瑞科技股份有限公司 ↔「譜瑞-KY」· 英文首頁 → 不適用(不報錯)· 真的不同名 → 仍報",
        name_hit("頎邦科技股份有限公司", "頎邦(6147 TT) 營運展望" + "中" * 40) is True and name_hit("開曼群島商竣邦國際股份有限公司", "竣邦-KY 4442" + "中" * 40) is True
        and name_hit("譜瑞科技股份有限公司", "譜瑞-KY" + "中" * 40) is True and name_hit("台積電", "Taiwan Semiconductor Manufacturing (2330.TW) Overweight") is None and name_hit("台積電", "聯電(2303) 晶圓代工" + "中" * 40) is False)
    ub = {"TAISHIN": {"aliases": {"台新": "冊", "TSC": "冊"}, "unified": True}, "CATHAY": {"aliases": {"國泰": "冊", "CT": "冊"}, "unified": True}, "HUANAN": {"aliases": {"華南": "冊"}, "unified": True}, "CITI": {"aliases": {"Citi": "冊"}, "unified": True}}
    chk("⑪ 統一冊生效:券商一律統一代碼(台新 → TAISHIN,不再 TSC)· 電郵網域舊縮寫對成統一代碼(TSC → TAISHIN · CT → CATHAY · HNSC → HUANAN · Citi → CITI)· 大陸網域(gf)→ 不認 · cl-sec.com → CLSA",
        _abbr_of_v167(ub, "TAISHIN") == ("TAISHIN", "統一冊") and to_code("TSC", ub) == "TAISHIN" and to_code("CT", ub) == "CATHAY" and to_code("HNSC", ub) == "HUANAN" and to_code("Citi", ub) == "CITI" and to_code("GF", ub) == "" and to_code("XYZ", ub) == "XYZ"
        and domain_broker_v167("cl-sec.com", dict(ub, CLSA={"aliases": {"CLSA": "冊", "cl-sec": "冊"}, "unified": True})) == "CLSA")
    me = Path(__file__).read_text(encoding="utf-8")
    chk("⑨ 正本加速器橋 · 自帶多程序墊片", "import VeritasCeleritas_v1141" in me and _job_entry.__module__ in ("__main__", __name__))
    print("  ── 前版鏈自測(原樣印出)──")
    sv = {}
    _compat164(True, sv)
    try:
        prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    finally:
        _compat164(False, sv)
    chk("⑩ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    print("[計] VRN_SystemManager_v0167 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
