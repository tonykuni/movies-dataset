#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vrn_finlex_v0100 — 財務三字庫收割引擎(TOOL-072)
====================================================================
操作員令(批44,2026-08-19):「broker dict / 財務數據中英文同義字庫
/ 財務報表同義字庫」。
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

import importlib.util
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
KNOW = HERE / "knowledge"
BOOK_BROKER = KNOW / "VRN_Broker_Dict_v0100.json"
BOOK_FINDATA = KNOW / "VRN_FinData_Synonym_v0100.json"
BOOK_FINSTMT = KNOW / "VRN_FinStatement_Synonym_v0100.json"

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
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod  # dataclass 解析需先掛名(MDL 家族 loader 同法)
    spec.loader.exec_module(mod)
    return mod


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

    n_multi = sum(1 for m in metrics.values() if len(m["sources"]) > 1)
    book_findata = {"schema": "VIA.VRN.FinDataSynonym.v1", "generated": ts,
                    "policy": "中英文同義字庫;多源並列 sources 標註不仲裁;收割自倉內正本",
                    "count": len(metrics), "multi_source": n_multi, "metrics": metrics}

    statements = {}
    for code, (zh, en, aliases) in STMT_ZH.items():
        statements[code] = {"zh": zh, "en": en, "aliases": aliases,
                            "items": sorted(stmt_items.get(code, []))}
    book_finstmt = {"schema": "VIA.VRN.FinStatementSynonym.v1", "generated": ts,
                    "policy": "報表層同義字庫;科目歸屬自 pattern 庫 StatementType",
                    "count": len(statements),
                    "item_total": sum(len(s["items"]) for s in statements.values()),
                    "statements": statements}
    return book_broker, book_findata, book_finstmt, srcs


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
    bb, bf, bs, srcs = harvest()
    out_dir.mkdir(parents=True, exist_ok=True)
    for p, b in [(out_dir / BOOK_BROKER.name, bb), (out_dir / BOOK_FINDATA.name, bf),
                 (out_dir / BOOK_FINSTMT.name, bs)]:
        p.write_text(json.dumps(b, ensure_ascii=False, indent=1), encoding="utf-8")
    rich_matrix("財務三字庫收割結果(AI 只整理不發明;逐條標來源)",
                ["冊", "條目", "註"],
                [[BOOK_BROKER.name, bb["count"], "券商→縮寫(正本=Summarizer)"],
                 [BOOK_FINDATA.name, bf["count"],
                  f"canonical 財務數據中英同義;多源並列 {bf['multi_source']} 項"],
                 [BOOK_FINSTMT.name, f"{bs['count']} 表/{bs['item_total']} 科目",
                  "報表名同義+科目歸屬"]])
    print(f"  [源] {' · '.join(f'{k}={v}' for k, v in srcs.items())}")
    return 0


def ask(term: str) -> int:
    hits = []
    for p, kind in [(BOOK_BROKER, "BROKER"), (BOOK_FINDATA, "FINDATA"), (BOOK_FINSTMT, "FINSTMT")]:
        if not p.exists():
            continue
        b = json.loads(p.read_text(encoding="utf-8-sig"))
        if kind == "BROKER":
            for zh, rec in b["brokers"].items():
                if term in zh or term.upper() == rec["abbr"]:
                    hits.append(f"[BROKER] {zh} → {rec['abbr']}")
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


def selftest() -> int:
    import tempfile
    t0 = time.time()
    fails = []

    def chk(name, cond, note=""):
        if not cond:
            fails.append(name)
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")

    bb, bf, bs, srcs = harvest()
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
    # ⑧ 沙盒落冊+讀回 schema
    with tempfile.TemporaryDirectory() as td:
        rc = build(Path(td))
        back = json.loads((Path(td) / BOOK_FINDATA.name).read_text(encoding="utf-8"))
        chk("沙盒落冊讀回", rc == 0 and back["schema"] == "VIA.VRN.FinDataSynonym.v1"
            and back["count"] == bf["count"])
    n = 8 - len(fails)
    print(f"  [計] 八檢 OK {n} · FAIL {len(fails)} · {round(time.time() - t0, 1)}s")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 財務三字庫收割引擎 v0100 · 八檢(沙盒零網路)===")
        return selftest()
    if "--ask" in args:
        i = args.index("--ask")
        return ask(args[i + 1]) if i + 1 < len(args) else 2
    if "--build" in args:
        print("=== 財務三字庫收割 · broker dict+財務數據中英同義+財務報表同義 ===")
        return build()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
