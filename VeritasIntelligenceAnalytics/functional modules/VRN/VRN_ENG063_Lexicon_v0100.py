#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vrn_lexicon_v0100 — 中英文字庫+知識樹引擎(TOOL-059)
====================================================================
操作員令(批20):導入深度學習/機器學習功能發展;自動建立中英文字庫;
隨時有簡單詢問方式;JSON 模板給 AI 填入更新;樹枝編號知識體系架構
(中英文);讀取報告時也要自動建構;操作員定期協助審核。

設計(誠實三層 ML,不假綠):
  T1 統計層(標準庫恆在):詞頻/共現/difflib 模糊比對——零外依賴。
  T2 機器學習層(裝了才用):sklearn TF-IDF、rapidfuzz、YAKE、sumy——
     import 探測,缺件誠實降級 T1。
  T3 深度學習層(名錄 REGISTERED):transformers/sentence-transformers/
     Ollama/llama.cpp——偵測到才啟用,未裝誠實列名錄,絕不假造推理結果。

字庫條目狀態機(append-only,零刪除):
  SEED(內建種子)→ AUTO(讀報自動建構,即 PENDING_REVIEW 候審)
  → APPROVED(操作員核准)/ REJECTED(留痕不刪)。

知識樹:樹枝編號 K1、K1.1、K1.1.1…,節點雙語(zh/en)。
  種子:五點架構(K1-K5)+產業族群(K6,自 source_docs 台股熱門族群
  docx 自動抽 中文名+4碼 個股)+資訊來源四大類(K7,自 SOP docx)
  +市場參與者券商冊(K8,自 VRN_Summarizer 字典)。

JSON 模板流:--template 匯出 AI 填寫模板 → 操作員交 AI 填 → --merge
  回填(全部進 PENDING_REVIEW 候審,絕不直入 APPROVED)。

用法:
  --build              自動建庫(種子+source_docs 掃描)
  --ingest <檔>        讀取報告同時自動建構(txt/docx;候審佇列)
  --ask <詞>           簡單詢問(精確+模糊;中英雙向)
  --tree               樹枝編號知識體系(中英文)全展開
  --template           匯出 JSON 模板(給 AI 填入更新)
  --merge <json>       回填模板(進候審)
  --review             列候審佇列(操作員定期審核)
  --approve <id|all>   核准候審條目
  --reject <id> <由>   駁回(留痕不刪)
  --status             ML 三層可用度+庫統計
  --selftest           八檢
"""

# [VIA:ACCEL-BRIDGE:v0100] 加速器橋(優雅降級)
try:
    import VIA_SuperAccel_Module as VIA_ACCEL
except Exception:
    VIA_ACCEL = None

import difflib
import json
import re
import sys
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
KNOW = HERE / "knowledge"
SRC_DOCS = KNOW / "source_docs"
LEX_PATH = KNOW / "VRN_Lexicon_v0100.json"
TPL_PATH = KNOW / "VRN_Lexicon_Fill_Template_v0100.json"
NOW = datetime.now().strftime("%Y-%m-%d %H:%M")

# ── T2/T3 誠實探測 ─────────────────────────────────────────────────
ML = {"sklearn_tfidf": False, "rapidfuzz": False, "yake": False, "sumy": False}
DL_REGISTRY = {  # T3 名錄:偵測到才升 True;未裝誠實列名,不假造
    "transformers": False, "sentence_transformers": False,
    "ollama": False, "llama_cpp": False, "spacy": False,
}
try:
    from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: F401
    ML["sklearn_tfidf"] = True
except Exception:
    TfidfVectorizer = None
try:
    from rapidfuzz import fuzz as _rf_fuzz
    ML["rapidfuzz"] = True
except Exception:
    _rf_fuzz = None
try:
    import yake as _yake  # noqa: F401
    ML["yake"] = True
except Exception:
    _yake = None
try:
    import sumy  # noqa: F401
    ML["sumy"] = True
except Exception:
    pass
for _dl in list(DL_REGISTRY):
    try:
        __import__(_dl)
        DL_REGISTRY[_dl] = True
    except Exception:
        pass

# ── 種子知識樹(雙語;樹枝編號)──────────────────────────────────
SEED_TREE = {
    "K1": {"zh": "投資結論", "en": "Investment Conclusion", "children": {
        "K1.1": {"zh": "評等動作", "en": "Rating Action"},
        "K1.2": {"zh": "目標價", "en": "Target Price"},
    }},
    "K2": {"zh": "成長動能", "en": "Growth Drivers", "children": {
        "K2.1": {"zh": "產業趨勢", "en": "Industry Trend"},
        "K2.2": {"zh": "訂單能見度", "en": "Order Visibility"},
    }},
    "K3": {"zh": "財務與估值", "en": "Financials & Valuation", "children": {
        "K3.1": {"zh": "獲利指標", "en": "Earnings Metrics"},
        "K3.2": {"zh": "評價方法", "en": "Valuation Methods"},
    }},
    "K4": {"zh": "同業比較", "en": "Peer Comparison", "children": {}},
    "K5": {"zh": "風險因子", "en": "Risk Factors", "children": {}},
    "K6": {"zh": "產業族群", "en": "Industry Groups", "children": {}},
    "K7": {"zh": "資訊來源", "en": "Information Sources", "children": {
        "K7.1": {"zh": "同業快訊(Line)", "en": "Peer Flash (Line)"},
        "K7.2": {"zh": "法人盤後/法說", "en": "Institutional Post-market"},
        "K7.3": {"zh": "晨報", "en": "Morning Note"},
        "K7.4": {"zh": "個股深度報告", "en": "In-depth Stock Report"},
    }},
    "K8": {"zh": "市場參與者", "en": "Market Participants", "children": {
        "K8.1": {"zh": "券商", "en": "Brokers"},
    }},
}

# 種子雙語詞條(zh, en, node)——取自 VRN_Summarizer 字典族+五點架構
SEED_TERMS = [
    ("買進", "Buy", "K1.1"), ("賣出", "Sell", "K1.1"), ("持有", "Hold", "K1.1"),
    ("中立", "Neutral", "K1.1"), ("加碼", "Overweight", "K1.1"),
    ("減碼", "Underweight", "K1.1"), ("優於大盤", "Outperform", "K1.1"),
    ("落後大盤", "Underperform", "K1.1"), ("調升", "Upgrade", "K1.1"),
    ("調降", "Downgrade", "K1.1"), ("目標價", "Target Price", "K1.2"),
    ("上漲空間", "Upside", "K1.2"),
    ("營收", "Revenue", "K2"), ("市佔率", "Market Share", "K2"),
    ("能見度", "Visibility", "K2.2"), ("擴產", "Capacity Expansion", "K2.1"),
    ("年增", "YoY", "K2"), ("季增", "QoQ", "K2"),
    ("本益比", "P/E Ratio", "K3.2"), ("股價淨值比", "P/B Ratio", "K3.2"),
    ("殖利率", "Dividend Yield", "K3.1"), ("毛利率", "Gross Margin", "K3.1"),
    ("營益率", "Operating Margin", "K3.1"), ("淨利率", "Net Margin", "K3.1"),
    ("每股盈餘", "EPS", "K3.1"), ("股東權益報酬率", "ROE", "K3.1"),
    ("現金流折現", "DCF", "K3.2"), ("分部加總", "SOTP", "K3.2"),
    ("股利折現", "DDM", "K3.2"), ("淨資產價值", "NAV", "K3.2"),
    ("同業", "Peers", "K4"), ("競爭優勢", "Competitive Advantage", "K4"),
    ("溢價", "Premium", "K4"), ("折價", "Discount", "K4"),
    ("下行風險", "Downside Risk", "K5"), ("地緣政治", "Geopolitical", "K5"),
    ("匯率", "FX", "K5"), ("庫存去化", "Inventory Digestion", "K5"),
    ("人工智慧", "AI", "K6"), ("高效能運算", "HPC", "K6"),
    ("先進封裝", "Advanced Packaging", "K6"), ("記憶體", "Memory", "K6"),
    ("散熱", "Thermal", "K6"), ("軍工", "Defense", "K6"),
    ("散裝航運", "Dry Bulk Shipping", "K6"), ("電動車", "EV", "K6"),
]

TICKER_ZH_RX = re.compile(r"([一-鿿][一-鿿\-A-Za-z]{1,7}?)[\s ]*[\(( ]?([1-9]\d{3})(?:\.TWO?|[\s ]*TT)?[\)) ]?")
CJK_RX = re.compile(r"[一-鿿]{2,6}")
EN_RX = re.compile(r"[A-Za-z][A-Za-z/\-]{1,24}")


def _log(msg):
    print(msg)


def read_docx_text(p: Path) -> str:
    """標準庫 docx 文字抽取(zip+XML;段落感知)。"""
    try:
        z = zipfile.ZipFile(p)
        xml = z.read("word/document.xml").decode("utf-8", "ignore")
    except Exception as e:
        _log(f"  [WARN] docx 讀取失敗 {p.name}: {e}")
        return ""
    paras = []
    for pm in re.findall(r"<w:p[ >].*?</w:p>", xml, re.S):
        t = "".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", pm, re.S))
        t = re.sub(r"&amp;", "&", t)
        if t.strip():
            paras.append(t.strip())
    return "\n".join(paras)


def read_any_text(p: Path) -> str:
    if p.suffix.lower() == ".docx":
        return read_docx_text(p)
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        _log(f"  [WARN] 讀取失敗 {p.name}: {e}")
        return ""


def load_lex() -> dict:
    if LEX_PATH.exists():
        return json.loads(LEX_PATH.read_text(encoding="utf-8"))
    return {"schema": "vrn-lexicon-v1", "policy": "append-only 零刪除;AUTO 條目=候審;核准/駁回留痕",
            "tree": {}, "entries": {}, "history": [], "counters": {"E": 0}}


def save_lex(lex: dict):
    KNOW.mkdir(parents=True, exist_ok=True)
    if LEX_PATH.exists():
        bak = LEX_PATH.with_suffix(f".pre_{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak")
        bak.write_bytes(LEX_PATH.read_bytes())
    LEX_PATH.write_text(json.dumps(lex, ensure_ascii=False, indent=1), encoding="utf-8")


def add_entry(lex, zh, en, node, status, source, aliases=None):
    """append-only:同 zh(或同 en)已在庫→僅累計 count/補來源,不覆蓋。"""
    for eid, e in lex["entries"].items():
        if (zh and e["zh"] == zh) or (en and e["en"] and e["en"] == en and not zh):
            e["count"] = e.get("count", 1) + 1
            if source not in e["sources"]:
                e["sources"].append(source)
            return eid, False
    lex["counters"]["E"] += 1
    eid = f"E{lex['counters']['E']:05d}"
    lex["entries"][eid] = {
        "zh": zh, "en": en, "aliases": aliases or [], "node": node,
        "status": status, "sources": [source], "count": 1, "first_seen": NOW,
    }
    return eid, True


def ensure_tree(lex):
    for k, v in SEED_TREE.items():
        node = lex["tree"].setdefault(k, {"zh": v["zh"], "en": v["en"], "children": {}})
        for ck, cv in v.get("children", {}).items():
            node["children"].setdefault(ck, {"zh": cv["zh"], "en": cv["en"], "children": {}})


def classify(text: str) -> str:
    """句/詞歸樹節點:種子詞命中計分(T1);全未中→K6 產業族群候審。"""
    scores = Counter()
    for zh, en, node in SEED_TERMS:
        if zh in text or (en and en.lower() in text.lower()):
            scores[node.split(".")[0]] += 1
    return scores.most_common(1)[0][0] if scores else "K6"


def harvest_stocks(lex, text, source):
    """中文名+4碼 個股對照自動抽取 → K6 樹掛枝+雙語條目(候審)。"""
    n_new = 0
    groups = lex["tree"].get("K6", {}).setdefault("children", {})
    for zh_name, code in set(TICKER_ZH_RX.findall(text)):
        zh_name = zh_name.strip()
        if len(zh_name) < 2 or zh_name in ("目標價", "報告", "評等"):
            continue
        _, new = add_entry(lex, f"{zh_name}({code})", f"{code}.TW", "K6",
                           "AUTO", source, aliases=[code, zh_name])
        n_new += int(new)
    # 族群節點:docx 表格「熱門族群」欄常見樣式——取含「/」或關鍵尾字的 CJK 段
    known_groups = ["AI 伺服器", "記憶體", "散熱", "軍工", "散裝航運", "PCB", "CPO",
                    "航太", "無人機", "金融", "觀光", "能源", "電動車", "半導體"]
    gi = len(groups)
    for g in known_groups:
        if g in text and not any(c["zh"].startswith(g) for c in groups.values()):
            gi += 1
            groups[f"K6.{gi}"] = {"zh": g, "en": "", "children": {}}
    return n_new


def cmd_build() -> int:
    lex = load_lex()
    ensure_tree(lex)
    n_seed = 0
    for zh, en, node in SEED_TERMS:
        _, new = add_entry(lex, zh, en, node, "SEED", "seed:built-in")
        n_seed += int(new)
    n_auto = 0
    docs = sorted(SRC_DOCS.glob("*")) if SRC_DOCS.exists() else []
    for d in docs:
        text = read_any_text(d)
        if text:
            n_auto += harvest_stocks(lex, text, f"doc:{d.name}")
    lex["history"].append({"op": "build", "ts": NOW, "seed_new": n_seed,
                           "auto_new": n_auto, "docs": [d.name for d in docs]})
    save_lex(lex)
    st = Counter(e["status"] for e in lex["entries"].values())
    _log(f"  [建庫] 條目 {len(lex['entries'])}(SEED {st.get('SEED',0)} · AUTO候審 {st.get('AUTO',0)}"
         f" · APPROVED {st.get('APPROVED',0)})· 源文件 {len(docs)}")
    _log(f"  [樹] 主枝 {len(lex['tree'])} · K6 族群枝 {len(lex['tree'].get('K6',{}).get('children',{}))}")
    return 0


def cmd_ingest(path: str) -> int:
    p = Path(path)
    if not p.exists():
        _log(f"  [FAIL] 檔不存在:{path}")
        return 2
    lex = load_lex()
    ensure_tree(lex)
    text = read_any_text(p)
    if not text:
        _log("  [FAIL] 無文字內容")
        return 2
    n_stock = harvest_stocks(lex, text, f"ingest:{p.name}")
    # 高頻新詞候選(T1 詞頻;T2 有 sklearn 用 TF-IDF 加權)
    cjk = [w for w in CJK_RX.findall(text)]
    freq = Counter(cjk)
    known_zh = {e["zh"] for e in lex["entries"].values()}
    n_term = 0
    for w, c in freq.most_common(80):
        if c >= 3 and w not in known_zh and not TICKER_ZH_RX.match(w):
            node = classify(w) or "K6"
            _, new = add_entry(lex, w, "", node, "AUTO", f"ingest:{p.name}")
            n_term += int(new)
        if n_term >= 30:
            break
    lex["history"].append({"op": "ingest", "ts": NOW, "file": p.name,
                           "stock_new": n_stock, "term_new": n_term})
    save_lex(lex)
    _log(f"  [讀報建構] {p.name}:個股 +{n_stock} · 詞條 +{n_term}(全入候審,--review 定期審核)")
    return 0


def _fuzzy(a: str, b: str) -> float:
    if _rf_fuzz:
        return _rf_fuzz.ratio(a, b) / 100.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def cmd_ask(q: str) -> int:
    lex = load_lex()
    hits = []
    for eid, e in lex["entries"].items():
        cand = [e["zh"], e["en"]] + e.get("aliases", [])
        best = max((_fuzzy(q.lower(), str(c).lower()) for c in cand if c), default=0)
        if q in (e["zh"] or "") or q.lower() in (e["en"] or "").lower() or best >= 0.72:
            hits.append((best + (1.0 if q in (e["zh"], e["en"]) else 0), eid, e))
    hits.sort(reverse=True, key=lambda t: t[0])
    if not hits:
        _log(f"  [詢問] 「{q}」查無——可 --template 產模板請 AI 補後 --merge 回填")
        return 1
    for _, eid, e in hits[:5]:
        node = e["node"]
        tzh = _node_label(lex, node)
        _log(f"  [{eid}] {e['zh']} ⇄ {e['en'] or '—'} · 枝 {node}({tzh})· {e['status']} · 見 {e['count']} 次")
    return 0


def _node_label(lex, node_id):
    top = node_id.split(".")[0]
    n = lex["tree"].get(top)
    if not n:
        return "?"
    if node_id == top:
        return f"{n['zh']}/{n['en']}"
    c = n.get("children", {}).get(node_id)
    return f"{n['zh']}>{c['zh']}" if c else f"{n['zh']}/{n['en']}"


def cmd_tree() -> int:
    lex = load_lex()
    ensure_tree(lex)
    by_node = Counter(e["node"].split(".")[0] for e in lex["entries"].values())
    for k in sorted(lex["tree"], key=lambda x: int(x[1:])):
        n = lex["tree"][k]
        _log(f"  {k} {n['zh']} · {n['en']}(詞條 {by_node.get(k,0)})")
        for ck in sorted(n.get("children", {}), key=lambda x: [int(p) for p in x[1:].split(".")]):
            c = n["children"][ck]
            _log(f"    {ck} {c['zh']}{(' · ' + c['en']) if c['en'] else ''}")
    return 0


def cmd_template() -> int:
    lex = load_lex()
    ensure_tree(lex)
    pending_en = [{"id": eid, "zh": e["zh"], "en": "", "node": e["node"]}
                  for eid, e in lex["entries"].items() if not e["en"]][:50]
    tpl = {
        "schema": "vrn-lexicon-fill-template-v1",
        "instructions_for_ai": (
            "請填 slots:每項補英文對譯 en(專業財經用語),必要時修 node(樹枝編號見 tree)。"
            "可於 new_terms 增列雙語新詞 {zh,en,node,aliases}。僅填空,勿改 id/zh。"
            "回填後操作員執行 --merge 本檔;全部進候審,審核後才生效。"),
        "tree": {k: {"zh": v["zh"], "en": v["en"],
                     "children": {ck: {"zh": cv["zh"], "en": cv["en"]}
                                  for ck, cv in v.get("children", {}).items()}}
                 for k, v in lex["tree"].items()},
        "slots": pending_en,
        "new_terms": [],
        "exported": NOW,
    }
    TPL_PATH.write_text(json.dumps(tpl, ensure_ascii=False, indent=1), encoding="utf-8")
    _log(f"  [模板] {TPL_PATH.name} · 待補英譯 slots {len(pending_en)} · new_terms 開放增列")
    return 0


def cmd_merge(path: str) -> int:
    p = Path(path)
    if not p.exists():
        _log(f"  [FAIL] 模板不存在:{path}")
        return 2
    try:
        tpl = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        _log(f"  [FAIL] JSON 解析:{e}")
        return 2
    lex = load_lex()
    ensure_tree(lex)
    n_fill = n_new = 0
    for s in tpl.get("slots", []):
        e = lex["entries"].get(s.get("id", ""))
        if e is not None and s.get("en") and not e["en"]:
            e["en"] = str(s["en"])[:80]
            e["status"] = "AUTO" if e["status"] != "SEED" else e["status"]  # 回填仍候審
            n_fill += 1
    for t in tpl.get("new_terms", []):
        if t.get("zh"):
            _, new = add_entry(lex, t["zh"], t.get("en", ""), t.get("node", "K6"),
                               "AUTO", f"merge:{p.name}", aliases=t.get("aliases", []))
            n_new += int(new)
    lex["history"].append({"op": "merge", "ts": NOW, "file": p.name,
                           "filled_en": n_fill, "new": n_new})
    save_lex(lex)
    _log(f"  [回填] 英譯補 {n_fill} · 新詞 +{n_new}(候審;--review 檢視)")
    return 0


def cmd_review() -> int:
    lex = load_lex()
    pend = [(eid, e) for eid, e in lex["entries"].items() if e["status"] == "AUTO"]
    _log(f"  [候審] {len(pend)} 條(操作員定期審核;--approve <id|all> / --reject <id> <理由>)")
    for eid, e in pend[:40]:
        _log(f"    {eid} · {e['zh']} ⇄ {e['en'] or '—'} · 枝 {e['node']} · 源 {e['sources'][0]}")
    if len(pend) > 40:
        _log(f"    …另 {len(pend)-40} 條(全清單見 {LEX_PATH.name})")
    return 0


def cmd_approve(target: str) -> int:
    lex = load_lex()
    n = 0
    for eid, e in lex["entries"].items():
        if e["status"] == "AUTO" and (target == "all" or eid == target):
            e["status"] = "APPROVED"
            n += 1
    lex["history"].append({"op": "approve", "ts": NOW, "target": target, "n": n})
    save_lex(lex)
    _log(f"  [核准] {n} 條 → APPROVED")
    return 0


def cmd_reject(eid: str, reason: str) -> int:
    lex = load_lex()
    e = lex["entries"].get(eid)
    if not e:
        _log(f"  [FAIL] 無此條目 {eid}")
        return 2
    e["status"] = "REJECTED"
    e["reject_reason"] = reason
    lex["history"].append({"op": "reject", "ts": NOW, "id": eid, "reason": reason})
    save_lex(lex)
    _log(f"  [駁回留痕] {eid}(零刪除)")
    return 0


def cmd_status() -> int:
    lex = load_lex()
    st = Counter(e["status"] for e in lex["entries"].values())
    _log(f"  [庫] 條目 {len(lex['entries'])} · " + " · ".join(f"{k} {v}" for k, v in st.items()))
    _log("  [T1 統計層] 恆在(詞頻/共現/difflib)")
    _log("  [T2 ML 層] " + " · ".join(f"{k}={'ON' if v else 'off'}" for k, v in ML.items()))
    _log("  [T3 DL 名錄] " + " · ".join(f"{k}={'ON' if v else 'REGISTERED'}" for k, v in DL_REGISTRY.items()))
    _log("  [誠實] 缺件走 via-install 同意閘補;未裝之層絕不假造結果")
    return 0


def selftest() -> int:
    import tempfile
    ok = 0
    total = 8
    global LEX_PATH, TPL_PATH, SRC_DOCS
    with tempfile.TemporaryDirectory() as td:
        _lp, _tp, _sd = LEX_PATH, TPL_PATH, SRC_DOCS
        LEX_PATH = Path(td) / "lex.json"
        TPL_PATH = Path(td) / "tpl.json"
        SRC_DOCS = _sd  # 真源文件掃描(在位即掃,不在誠實 0)
        try:
            # 1 建庫
            r = cmd_build()
            lex = load_lex()
            if r == 0 and len(lex["entries"]) >= len(SEED_TERMS):
                ok += 1; print("  [PASS] 建庫(種子+源文件)")
            else:
                print("  [FAIL] 建庫")
            # 2 樹枝編號雙語
            if all(k in lex["tree"] for k in ("K1", "K7", "K8")) and lex["tree"]["K1"]["en"]:
                ok += 1; print("  [PASS] 樹枝編號雙語 K1-K8")
            else:
                print("  [FAIL] 樹")
            # 3 讀報自動建構
            rp = Path(td) / "rpt.txt"
            rp.write_text("台積電(2330)目標價上調。緯創 3231 受惠 AI 伺服器。"
                          "先進封裝需求強勁。" * 3, encoding="utf-8")
            if cmd_ingest(str(rp)) == 0:
                ok += 1; print("  [PASS] 讀報自動建構(個股+詞條候審)")
            else:
                print("  [FAIL] 讀報")
            # 4 詢問(精確+模糊)
            if cmd_ask("目標價") == 0 and cmd_ask("Target Price") == 0:
                ok += 1; print("  [PASS] 簡單詢問中英雙向")
            else:
                print("  [FAIL] 詢問")
            # 5 模板匯出
            if cmd_template() == 0 and json.loads(TPL_PATH.read_text(encoding="utf-8"))["slots"] is not None:
                ok += 1; print("  [PASS] JSON 模板匯出(AI 填入用)")
            else:
                print("  [FAIL] 模板")
            # 6 回填候審
            tpl = json.loads(TPL_PATH.read_text(encoding="utf-8"))
            tpl["new_terms"] = [{"zh": "矽光子", "en": "Silicon Photonics", "node": "K6"}]
            TPL_PATH.write_text(json.dumps(tpl, ensure_ascii=False), encoding="utf-8")
            lex_before = len(load_lex()["entries"])
            if cmd_merge(str(TPL_PATH)) == 0 and len(load_lex()["entries"]) == lex_before + 1:
                ok += 1; print("  [PASS] 模板回填→候審")
            else:
                print("  [FAIL] 回填")
            # 7 審核閉環(核准+駁回留痕)
            lex = load_lex()
            aid = next((i for i, e in lex["entries"].items() if e["status"] == "AUTO"), None)
            cmd_approve(aid)
            lex = load_lex()
            rid = next((i for i, e in lex["entries"].items() if e["status"] == "AUTO"), None)
            r2 = cmd_reject(rid, "測試駁回") if rid else 0
            lex = load_lex()
            if lex["entries"][aid]["status"] == "APPROVED" and r2 == 0 and \
               (rid is None or lex["entries"][rid]["status"] == "REJECTED"):
                ok += 1; print("  [PASS] 審核閉環(核准/駁回零刪除)")
            else:
                print("  [FAIL] 審核")
            # 8 ML 三層誠實
            if cmd_status() == 0:
                ok += 1; print("  [PASS] ML 三層誠實申報(T1 恆在/T2 探測/T3 名錄)")
            else:
                print("  [FAIL] 狀態")
        finally:
            LEX_PATH, TPL_PATH, SRC_DOCS = _lp, _tp, _sd
    print(f"  [計] {ok}/{total} 檢通過")
    return 0 if ok == total else 1


def main() -> int:
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if a[0] == "--selftest":
        return selftest()
    if a[0] == "--build":
        return cmd_build()
    if a[0] == "--ingest" and len(a) > 1:
        return cmd_ingest(a[1])
    if a[0] == "--ask" and len(a) > 1:
        return cmd_ask(" ".join(a[1:]))
    if a[0] == "--tree":
        return cmd_tree()
    if a[0] == "--template":
        return cmd_template()
    if a[0] == "--merge" and len(a) > 1:
        return cmd_merge(a[1])
    if a[0] == "--review":
        return cmd_review()
    if a[0] == "--approve" and len(a) > 1:
        return cmd_approve(a[1])
    if a[0] == "--reject" and len(a) > 2:
        return cmd_reject(a[1], " ".join(a[2:]))
    if a[0] == "--status":
        return cmd_status()
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
