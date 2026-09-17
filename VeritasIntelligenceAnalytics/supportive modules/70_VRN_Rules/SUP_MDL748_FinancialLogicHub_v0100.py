#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
SUP_MDL748_FinancialLogicHub v0100 — 財務邏輯統轄橋(批504)
====================================================================
操作員上傳五件財務邏輯(2026-09-14)。量過:三件與倉內同本(CRLF/橋頭差),新的是
  ① VIA_VRNLogic_AllInOne_v0201.py(VIA-VRN-LOGIC-001 2.1.0;純標準庫;離線;十六檢 16/16)
  ② vdf_fetchers_financials.py(網路件→VDF references 只收不掛線;批494 律:網路只認 AegisNexus)
本橋只掛不搬(Zero-Hydra;正本零觸碰):
  · AllInOne 從收容夾尾版 import(sys.modules 登錄;它有 --install apply 自裝功能,**永不呼叫**)
  · financial_data_standardization(倉內同本;合併損傷件——class 先於 imports,靠 __future__ annotations 撐著;
    import 要先登錄 sys.modules,否則 dataclass 解析註記時 NoneType.__dict__ 炸——這就是 finlex 走 AST 的原因)
給誰用:
  · ENG074 財報頁:SSOT normalize_metric 未命中(UNKNOWN)時要**第二意見**——AllInOne FINANCIAL_SYNONYMS + FDS 28 欄對照表;
    二見只寫在 raw_text 註記與「候 register」清單,**不改 canonical**(單一真相仍是 VRN_Financial_Synonyms_SSOT;登錄=操作員決定)
  · ENG082 邏輯庫:policy_rows() 把兩本冊(券商/評等/科目同義/單位倍率/來源優先序/驗證規則/正則)攤平入 via_policy_factors
  · 評等正典 rating_of()、檔名解析 parse_filename()、公式檢 validate_formulas()
用法:python3 SUP_MDL748_FinancialLogicHub_v0100.py [status|opinion <科目>|rating <字>] | --selftest
律:只增不減;誠實三態(OK/ABSENT/BROKEN);零網路;零寫入(status/opinion 唯讀)。
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
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
INTAKE = VIA / "functional modules" / "VRN" / "references" / "intake"
FDS_PATH = VIA / "functional modules" / "VRN" / "financial_data_standardization.py"
VERSION = "0100"
_M: dict = {"allinone": None, "fds": None, "why": {}, "tried": set()}


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m                      # dataclass/annotations 要找得到模組
    spec.loader.exec_module(m)
    return m


def allinone():
    """AllInOne 尾版(收容夾 VIA_VRNLogic_AllInOne_v*_b*/VIA_VRNLogic_AllInOne_v*.py);缺=None + why。"""
    if "allinone" in _M["tried"]:
        return _M["allinone"]
    _M["tried"].add("allinone")
    hits = sorted(INTAKE.glob("VIA_VRNLogic_AllInOne_v*_b*/VIA_VRNLogic_AllInOne_v*.py"))
    if not hits:
        _M["why"]["allinone"] = f"收容夾無 VIA_VRNLogic_AllInOne_v*(ABSENT):{INTAKE}"
        return None
    try:
        m = _load("via_vrnlogic_allinone", hits[-1])
        for fn in ("canonical_financial_name", "canonicalize_rating", "parse_filename", "validate_financial_formulas", "FINANCIAL_SYNONYMS"):
            if not hasattr(m, fn):
                raise AttributeError(f"缺 {fn}")
        _M["allinone"] = m
        _M["why"]["allinone"] = f"OK {hits[-1].name} {getattr(m, 'MODULE_VERSION', '?')}"
    except Exception as exc:
        _M["why"]["allinone"] = f"BROKEN {hits[-1].name}:{type(exc).__name__}:{str(exc)[:80]}"
    return _M["allinone"]


def fds():
    """financial_data_standardization 的 FinancialDataStandardizer(倉內同本);缺/壞=None + why。"""
    if "fds" in _M["tried"]:
        return _M["fds"]
    _M["tried"].add("fds")
    if not FDS_PATH.is_file():
        _M["why"]["fds"] = f"ABSENT {FDS_PATH.name}"
        return None
    try:
        m = _load("via_fds_std", FDS_PATH)
        s = m.FinancialDataStandardizer()
        _M["fds"] = {"mod": m, "std": s}
        n = sum(len(getattr(s.mapper, c)) for c in ("income_statement_fields", "balance_sheet_fields", "cashflow_fields", "ratio_fields"))
        _M["why"]["fds"] = f"OK {FDS_PATH.name} · {n} 欄 · 合併損傷件(__main__ 示範缺 5 法,程式庫面可用)"
    except Exception as exc:
        _M["why"]["fds"] = f"BROKEN {FDS_PATH.name}:{type(exc).__name__}:{str(exc)[:80]}"
    return _M["fds"]


def _cjk_first(aliases) -> str:
    for a in aliases:
        if any("一" <= ch <= "鿿" for ch in str(a)):
            return str(a)
    return str(aliases[0]) if aliases else ""


def second_opinion(label: str) -> dict:
    """SSOT 未命中的科目名 → 兩本冊的第二意見(只建議,不改 canonical)。回 {label, alts:[{src,canonical,zh}]}。"""
    out = {"label": str(label), "alts": []}
    lab = str(label or "").strip()
    if not lab:
        return out
    m = allinone()
    if m is not None:
        try:
            cf = m.canonical_financial_name(lab)
            if cf in m.FINANCIAL_SYNONYMS:
                out["alts"].append({"src": "allinone", "canonical": cf, "zh": _cjk_first(m.FINANCIAL_SYNONYMS[cf])})
        except Exception:
            pass
    f = fds()
    if f is not None:
        try:
            k = f["std"].standardize_field_name(lab)
            if k:
                mp = None
                for c in ("income_statement_fields", "balance_sheet_fields", "cashflow_fields", "ratio_fields"):
                    mp = getattr(f["std"].mapper, c).get(k) or mp
                out["alts"].append({"src": "fds", "canonical": k, "zh": getattr(mp, "chinese_name", "") if mp else ""})
        except Exception:
            pass
    return out


def rating_of(text: str) -> str:
    """評等正典:AllInOne canonicalize_rating(BUY/HOLD/SELL/NOT_RATED);缺=FDS KeywordRules 退路;都無=''。"""
    m = allinone()
    if m is not None:
        try:
            r = str(m.canonicalize_rating(text) or "")
            if r:
                return r
        except Exception:
            pass
    f = fds()
    if f is not None:
        try:
            t = str(text or "").lower()
            for k, kws in f["mod"].KeywordRules.RATING_KEYWORDS.items():
                if any(str(w).lower() in t for w in kws):
                    return {"strong_buy": "BUY", "buy": "BUY", "hold": "HOLD", "sell": "SELL", "strong_sell": "SELL", "not_rated": "NOT_RATED"}.get(k, k.upper())
        except Exception:
            pass
    return ""


def parse_filename(name: str) -> dict:
    m = allinone()
    if m is None:
        return {"state": "ABSENT", "why": _M["why"].get("allinone", "")}
    try:
        d = dict(m.parse_filename(name))
        d["state"] = "OK"
        return d
    except Exception as exc:
        return {"state": "BROKEN", "why": f"{type(exc).__name__}:{str(exc)[:60]}"}


def validate_formulas(rows: list) -> list:
    """rows=[{dataName, period, value}];AllInOne 公式檢(|毛利|≤|營收|、|營益|≤|營收|);缺=[]。"""
    m = allinone()
    if m is None:
        return []
    try:
        return list(m.validate_financial_formulas(rows))
    except Exception:
        return []


def policy_rows() -> list:
    """兩本冊攤平成 (source, key, value) 列——給 ENG082 via_policy_factors。"""
    rows = []
    m = allinone()
    if m is not None:
        src = f"SUP_MDL748:allinone {getattr(m, 'MODULE_VERSION', '?')}"
        for k in ("BROKER_ALIASES", "BROKER_NAMES", "RATING_ALIASES", "FINANCIAL_SYNONYMS", "UNIT_MULTIPLIERS_TO_MILLION"):
            for kk, vv in (getattr(m, k, None) or {}).items():
                rows.append({"source": src, "key": f"{k.lower()}.{kk}", "value": json.dumps(vv, ensure_ascii=False)[:2000]})
        for k in ("SOURCE_PRIORITY", "VALIDATION_STATES", "FINANCIAL_GRADES", "REPORT_TYPES", "DEFAULT_CONFIDENCE", "MATCH_CONFIDENCE_BONUS",
                  "UNRESOLVED_CONFIDENCE_PENALTY", "MIN_TARGET_PRICE", "MAX_TARGET_PRICE", "SCHEMA_VERSION"):
            if hasattr(m, k):
                rows.append({"source": src, "key": k.lower(), "value": json.dumps(getattr(m, k), ensure_ascii=False)[:2000]})
    f = fds()
    if f is not None:
        src = "SUP_MDL748:financial_data_standardization"
        s = f["std"]
        for c in ("income_statement_fields", "balance_sheet_fields", "cashflow_fields", "ratio_fields"):
            for k, mp in getattr(s.mapper, c).items():
                rows.append({"source": src, "key": f"field.{c}.{k}",
                             "value": json.dumps({"zh": mp.chinese_name, "en": mp.english_name, "twse": mp.twse_tpex_field, "yf": mp.yfinance_field,
                                                  "synonyms": list(mp.synonyms), "rules": list(mp.validation_rules)}, ensure_ascii=False)[:2000]})
        KR = f["mod"].KeywordRules
        for k, v in KR.RATING_KEYWORDS.items():
            rows.append({"source": src, "key": f"rating_keywords.{k}", "value": json.dumps(v, ensure_ascii=False)})
        for k, v in KR.TIME_PERIOD_KEYWORDS.items():
            rows.append({"source": src, "key": f"time_period_keywords.{k}", "value": json.dumps(v, ensure_ascii=False)})
        RP = f["mod"].RegexPatterns
        for k in [a for a in dir(RP) if a.isupper()]:
            rows.append({"source": src, "key": f"regex.{k}", "value": str(getattr(RP, k))[:2000]})
    return rows


def status() -> int:
    allinone(); fds()
    print(f"[財務邏輯橋] SUP_MDL748 v{VERSION} · 收容夾 {INTAKE.name}")
    for k in ("allinone", "fds"):
        print(f"  {k:9s} {_M['why'].get(k, '?')}")
    n = len(policy_rows())
    print(f"  政策因子 {n} 列(ENG082 sync-db 入 via_policy_factors)· 二見範例 總資產 → {[a['canonical'] + '@' + a['src'] for a in second_opinion('總資產')['alts']]}")
    return 0


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)
    m = allinone()
    chk("① AllInOne 掛載(收容夾尾版;版本 2.x;十六檢件)", m is not None and str(getattr(m, "MODULE_VERSION", "")).startswith("2."), f"({_M['why'].get('allinone', '')[:60]})")
    f = fds()
    chk("② financial_data_standardization 掛載(sys.modules 登錄後 dataclass 解析得過;28 欄)", f is not None and "28 欄" in _M["why"].get("fds", ""), f"({_M['why'].get('fds', '')[:70]})")
    so = second_opinion("總資產")
    chk("③ 第二意見:SSOT 沒有的「總資產」兩本冊都認(allinone total_assets · fds total_assets),只建議不改 canonical",
        {(a["src"], a["canonical"]) for a in so["alts"]} >= {("allinone", "total_assets"), ("fds", "total_assets")}, f"({so['alts']})")
    chk("④ 第二意見:胡亂科目=空(零硬套)", second_opinion("神秘特殊科目")["alts"] == [])
    chk("⑤ 評等正典:Overweight→BUY · 中立→HOLD · 未評等→NOT_RATED", rating_of("Overweight") == "BUY" and rating_of("中立") == "HOLD" and rating_of("未評等") == "NOT_RATED",
        f"({rating_of('Overweight')}/{rating_of('中立')}/{rating_of('未評等')})")
    pr = policy_rows()
    srcs = {r["source"].split(":")[1].split(" ")[0] for r in pr}
    chk("⑥ 政策因子攤平:兩本冊皆入(券商/評等/科目同義/單位倍率/28 欄/正則)≥ 80 列", len(pr) >= 80 and srcs >= {"allinone", "financial_data_standardization"}, f"({len(pr)} 列 · {sorted(srcs)})")
    pf = parse_filename("6873_2024-05-06_元大.pdf")
    chk("⑦ 檔名解析走 AllInOne(6873 · 2024-05-06 · 元大→YUANTA 在結果裡)", pf.get("state") == "OK" and "6873" in json.dumps(pf, ensure_ascii=False) and "YUANTA" in json.dumps(pf, ensure_ascii=False).upper(), f"({json.dumps(pf, ensure_ascii=False)[:100]})")
    fm = validate_formulas([{"dataName": "revenue", "period": "2024", "value": 100.0}, {"dataName": "gross_profit", "period": "2024", "value": 150.0}])
    chk("⑧ 公式檢:毛利 150 > 營收 100 → FAIL 一列(誠實;不改值)", any(x.get("status") == "FAIL" for x in fm), f"({fm})")
    src_txt = Path(__file__).read_text(encoding="utf-8")
    code = src_txt.split("def _load", 1)[1].split("def selftest", 1)[0]     # 不讀自測本身的字串
    chk("⑨ 零網路 · 永不呼叫 AllInOne --install apply / deploy_self(正本零觸碰)", all(("import " + k) not in src_txt for k in ("requests", "httpx")) and "deploy_self(" not in code and "--install" not in code)
    print(f"  [計] 九檢 OK {9 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print(f"=== 財務邏輯統轄橋(SUP_MDL748 v{VERSION})· 九檢自測(零網路)===")
        return selftest()
    if a and a[0] == "opinion":
        print(json.dumps(second_opinion(" ".join(a[1:])), ensure_ascii=False))
        return 0
    if a and a[0] == "rating":
        print(rating_of(" ".join(a[1:])) or "(無)")
        return 0
    return status()


if __name__ == "__main__":
    sys.exit(main())
