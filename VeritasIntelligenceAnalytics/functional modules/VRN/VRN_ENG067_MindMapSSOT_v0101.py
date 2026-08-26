#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VRN_ENG067_MindMapSSOT — 三語關鍵字 SSOT×分類×漸進知識體 Mind map(批158;via-mindmap)
====================================================================
操作員令:讀懂繁中/簡中/英文文章→抓關鍵字 SSOT→分類→逐漸形成知識體
Mind map。
去重紀律(引擎不重造):
  三語讀入=VRN_ENG066 NLP 樞紐(glob 尾版;OpenCC 簡→繁統一+實體+
    關鍵詞+三元組);英文詞面=token 擷取+ENG063 雙語字庫對照
  K 枝知識體系=VRN_ENG063 Lexicon SEED_TREE(TOOL-059 樹枝編號)掛載
  分類=庫內冊命中制(誠實可溯,零發明):INDICATOR/POLICY_ORG(ENG064
    實體)、INDUSTRY(批155 VIA-IND 冊)、GROUP(v0202 族群名冊)、
    TICKER(tw_listings)、RATING(ENG063 K1.1 詞面)、CONCEPT、GENERAL
SSOT 冊=dict/VRN_KeywordSSOT_v0100.json(append-only;canonical=繁體
正字;zh-CN/en 別名收斂;freq/sources/共現累積)——每次 ingest 增量
合併=「逐漸形成」;mind map HTML 每次由 SSOT 全量重生(放射樹:
分類八枝→關鍵字節點+跨枝共現虛線;淺色主控台風,行動裝置自適應)。
用法:via-mindmap ingest --text T|--file F [--lang auto]
     | --map(重生 HTML)| --status | --selftest
v0100→v0101(批164):spaCy 正主上線後 ENG066 keywords 車道輸出改變,
  冊內詞(毛利率/買進/調升…)失撿=只增不減破口 → ①掃描視圖納入
  ENG063 SEED_TERMS 中文詞(冊內零發明;NLP 後端升級不再丟冊內命中)
  ②EN 多詞 token 剝冠詞頭(The Fed→Fed 專名保留,The 存別名)。
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
from datetime import date, datetime
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
DICT = HERE / "dict"
SSOT_PATH = DICT / "VRN_KeywordSSOT_v0100.json"
MAP_PATH = VIA / "supportive modules" / "ui_support" / "VIA_MindMap_KnowledgeBody_v0100.html"
IND_MAP = VIA / "supportive modules" / "registry" / "VIA_IndustryUnifiedMap_v0100.json"
DB_TW = VIA / "functional modules" / "VDF" / "output_hub" / "mega" / "vdf_tw_market.duckdb"

# 大寫頭才允許多詞延伸(小寫頭吞大寫詞=「the Target Price」整串被棄之 QA 實錘)
_EN_TOKEN_RX = re.compile(
    r"[A-Z][A-Za-z&\-\.]*(?:\s+[A-Z][A-Za-z\-]+)*|[a-z][A-Za-z&\-\.]{2,}")
_EN_STOP = {"the", "and", "for", "with", "that", "this", "from", "are", "was",
            "has", "have", "its", "will", "would", "but", "not", "which", "than"}
CATEGORIES = ("INDICATOR", "POLICY_ORG", "TICKER", "INDUSTRY", "GROUP",
              "RATING", "CONCEPT", "GENERAL")


def _load_latest(pattern: str, name: str):
    hits = sorted(HERE.glob(pattern))
    if not hits:
        return None
    spec = importlib.util.spec_from_file_location(name, hits[-1])
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


_HUB = None
_LEX = None


def _hub():
    global _HUB
    if _HUB is None:
        _HUB = _load_latest("VRN_ENG066_NLPSupportHub_v*.py", "via_eng066_dyn")
    return _HUB


def _lex063():
    global _LEX
    if _LEX is None:
        _LEX = _load_latest("VRN_ENG063_Lexicon_v*.py", "via_eng063_dyn")
    return _LEX


# ---------------------------------------------------------------- 分類冊(庫內命中制)
_BOOKS = None


def _books() -> dict:
    """分類對照冊(誠實可溯:全由既有冊/庫載入,零發明)"""
    global _BOOKS
    if _BOOKS is not None:
        return _BOOKS
    b = {"industry": {}, "group": set(), "ticker": {}, "rating": set(),
         "en2zh": {}, "zh2en": {}}
    if IND_MAP.exists():
        for it in json.loads(IND_MAP.read_text(encoding="utf-8"))["items"]:
            b["industry"][it["unified_name"]] = it["via_id"]
            for al in it.get("aliases", {}).values():
                b["industry"][al] = it["via_id"]
    grp = VIA / "functional modules" / "GroupIndex"
    pkgs = sorted(grp.glob("VIA_TW_Grouping_LatestCommand_v*"))
    if pkgs:
        mm = sorted(pkgs[-1].glob("VIA_ThreeList_CanonicalMembershipInput_v*.csv"))
        if mm:
            import csv
            for r in csv.DictReader(open(mm[-1], encoding="utf-8-sig")):
                b["group"].add(r["Group"])
    try:
        import duckdb
        con = duckdb.connect(str(DB_TW), read_only=True)
        for code, name in con.execute("SELECT code, name FROM tw_listings").fetchall():
            b["ticker"][name] = code
        con.close()
    except Exception:
        pass
    lx = _lex063()
    if lx is not None and hasattr(lx, "SEED_TERMS"):
        for zh, en, k in lx.SEED_TERMS:
            b["en2zh"][en.lower()] = zh
            b["zh2en"][zh] = en
            if k.startswith("K1.1"):
                b["rating"] |= {zh, en}
    # 掃描視圖:冊名+其正規化變體(OpenCC 台→臺 類正字漂移之同義收斂;
    # QA 實錘:norm「臺積電」對冊名「台積電」失配)→ 皆映回冊上 canonical
    # v0101:+ENG063 SEED_TERMS 中文詞(冊內;NLP 後端換代不丟冊內命中)
    seed_zh = list(b["zh2en"])
    hub = _hub()
    scan = {}
    for name in list(b["ticker"]) + list(b["industry"]) + list(b["group"]) + seed_zh:
        if not name or len(name) < 2:
            continue
        scan[name] = name
        if hub is not None:
            try:
                v = hub.normalize(name)
                if v and v != name:
                    scan[v] = name
            except Exception:
                pass
    b["scan"] = scan
    _BOOKS = b
    return b


def classify(kw: str, ent_label: str | None = None) -> str:
    b = _books()
    if ent_label == "INDICATOR":
        return "INDICATOR"
    if ent_label == "POLICY_ORG":
        return "POLICY_ORG"
    if kw in b["ticker"]:
        return "TICKER"
    if kw in b["industry"]:
        return "INDUSTRY"
    if kw in b["group"]:
        return "GROUP"
    if kw in b["rating"] or kw.lower() in {r.lower() for r in b["rating"]}:
        return "RATING"
    if ent_label == "CONCEPT":
        return "CONCEPT"
    return "GENERAL"


# ---------------------------------------------------------------- 擷取
def extract_keywords(text: str) -> dict:
    """三語擷取:中文經 ENG066(簡→繁統一);英文 token+雙語冊收斂。
    回 {canonical: {"label":…, "aliases": set}}"""
    hub = _hub()
    if hub is None:
        raise RuntimeError("ENG066 樞紐缺席")
    enr = hub.enrich_for_summary(text)
    b = _books()
    out: dict[str, dict] = {}

    def add(canonical, label=None, alias=None):
        e = out.setdefault(canonical, {"label": label, "aliases": set()})
        if label and not e["label"]:
            e["label"] = label
        if alias and alias != canonical:
            e["aliases"].add(alias)

    for e in enr["entities"]:
        if e.get("label") in ("INDICATOR", "POLICY_ORG", "CONCEPT"):
            add(e["text"], e["label"])
    for k in enr["keywords"]:
        add(k)
    norm = enr["normalized_text"]
    for variant, canonical in b["scan"].items():   # 冊名+正規化變體雙鍵(台↔臺)
        if variant in norm:
            add(canonical, alias=variant if variant != canonical else None)
    for m in _EN_TOKEN_RX.finditer(text):
        tok = m.group(0).strip().strip(".,;:!?)('\"")
        # v0101:多詞剝冠詞頭(The Fed→Fed;冠詞非專名成分,整串存別名)
        head, _, rest = tok.partition(" ")
        if rest and head in ("The", "A", "An"):
            tok = rest
        low = tok.lower()
        if low in _EN_STOP or len(tok) < 3:
            continue
        zh = b["en2zh"].get(low)
        if zh:
            add(zh, alias=tok)          # 英文詞收斂到繁體正字
        elif tok[0].isupper() or tok.isupper():
            add(tok)                     # 專名/縮寫(EPS、Fed…)保留原文
    return {"keywords": out, "normalized_text": norm,
            "sentences": [s for s in re.split(r"(?<=[。!?!?.])\s*", norm) if s.strip()]}


# ---------------------------------------------------------------- SSOT(append-only)
def _load_ssot() -> dict:
    if SSOT_PATH.exists():
        d = json.loads(SSOT_PATH.read_text(encoding="utf-8"))
        for e in d["keywords"].values():
            e["aliases"] = set(e.get("aliases", []))
            e["cooccur"] = dict(e.get("cooccur", {}))
        return d
    return {"schema": "VRN_KEYWORD_SSOT_V1", "append_only": True,
            "next_id": 1, "keywords": {}, "ingest_log": []}


def _save_ssot(d: dict):
    DICT.mkdir(parents=True, exist_ok=True)
    ser = {**d, "keywords": {k: {**e, "aliases": sorted(e["aliases"]),
                                 "cooccur": e["cooccur"]}
                             for k, e in d["keywords"].items()}}
    SSOT_PATH.write_text(json.dumps(ser, ensure_ascii=False, indent=1),
                         encoding="utf-8")


def ingest(text: str, source: str = "direct_text") -> dict:
    """增量攝入=「逐漸形成」:合併同 canonical、別名收斂、freq/共現累積;
    既有條目零刪除(分類一經人審不降級;新見別名只增)"""
    r = extract_keywords(text)
    ssot = _load_ssot()
    lx = _lex063()
    k_of = {}
    if lx is not None and hasattr(lx, "SEED_TERMS"):
        k_of = {zh: k for zh, en, k in lx.SEED_TERMS}
    new_n = upd_n = 0
    seen = []
    for kw, meta in r["keywords"].items():
        e = ssot["keywords"].get(kw)
        if e is None:
            ssot["keywords"][kw] = e = {
                "kw_id": f"KW-{ssot['next_id']:04d}", "canonical": kw,
                "category": classify(kw, meta["label"]),
                "k_branch": k_of.get(kw), "aliases": set(meta["aliases"]),
                "freq": 0, "sources": [], "cooccur": {},
                "first_seen": str(date.today())}
            ssot["next_id"] += 1
            new_n += 1
        else:
            e["aliases"] |= meta["aliases"]
            upd_n += 1
        e["freq"] += 1
        if source not in e["sources"]:
            e["sources"].append(source)
        seen.append(kw)
    for s in r["sentences"]:                       # 同句共現累積
        ins = [k for k in seen if k in s]
        for a, bkw in combinations(sorted(set(ins)), 2):
            ssot["keywords"][a]["cooccur"][bkw] = ssot["keywords"][a]["cooccur"].get(bkw, 0) + 1
            ssot["keywords"][bkw]["cooccur"][a] = ssot["keywords"][bkw]["cooccur"].get(a, 0) + 1
    ssot["ingest_log"].append({"ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
                               "source": source, "keywords": len(seen),
                               "new": new_n})
    _save_ssot(ssot)
    return {"extracted": len(seen), "new": new_n, "merged": upd_n,
            "ssot_total": len(ssot["keywords"])}


# ---------------------------------------------------------------- Mind map
_CAT_META = {
    "INDICATOR": ("財務指標", "#2563eb"), "POLICY_ORG": ("政策機構", "#7c3aed"),
    "TICKER": ("個股", "#0f766e"), "INDUSTRY": ("產業", "#b45309"),
    "GROUP": ("族群", "#be185d"), "RATING": ("評等動作", "#4d7c0f"),
    "CONCEPT": ("概念風險", "#b91c1c"), "GENERAL": ("一般詞", "#64748b")}


def build_map() -> Path:
    """SSOT 全量→放射狀 mind map HTML(分類八枝;跨枝共現虛線 Top20)"""
    import math
    ssot = _load_ssot()
    kws = ssot["keywords"]
    cats = {c: [] for c in CATEGORIES}
    for e in kws.values():
        cats.get(e["category"], cats["GENERAL"]).append(e)
    W = H = 980
    cx = cy = W / 2
    pos = {}
    svg = []
    live = [c for c in CATEGORIES if cats[c]]
    for ci, cat in enumerate(live):
        ang = 2 * math.pi * ci / max(len(live), 1) - math.pi / 2
        bx, by = cx + 200 * math.cos(ang), cy + 200 * math.sin(ang)
        name, color = _CAT_META[cat]
        svg.append(f'<line x1="{cx}" y1="{cy}" x2="{bx}" y2="{by}" stroke="{color}" stroke-width="2.4" opacity="0.55"/>')
        members = sorted(cats[cat], key=lambda e: -e["freq"])[:14]
        for mi, e in enumerate(members):
            spread = 0.9
            a2 = ang + (mi - (len(members) - 1) / 2) * spread / max(len(members), 1) * 2
            r2 = 320 + 46 * (mi % 3)
            x, y = cx + r2 * math.cos(a2), cy + r2 * math.sin(a2)
            pos[e["canonical"]] = (x, y)
            svg.append(f'<line x1="{bx}" y1="{by}" x2="{x}" y2="{y}" stroke="{color}" stroke-width="1" opacity="0.4"/>')
            label = e["canonical"][:10]
            kb = f"·{e['k_branch']}" if e.get("k_branch") else ""
            svg.append(f'<g><circle cx="{x}" cy="{y}" r="{min(6 + e["freq"], 14)}" fill="{color}" opacity="0.82"/>'
                       f'<text x="{x}" y="{y - 12}" text-anchor="middle" font-size="11" fill="#1f2937">{label}{kb}</text></g>')
        svg.append(f'<g><circle cx="{bx}" cy="{by}" r="30" fill="{color}"/>'
                   f'<text x="{bx}" y="{by + 4}" text-anchor="middle" font-size="12" fill="#fff">{name}</text>'
                   f'<text x="{bx}" y="{by + 44}" text-anchor="middle" font-size="10" fill="#475569">{len(cats[cat])} 詞</text></g>')
    edges = []
    for a, e in kws.items():
        for bkw, n in e["cooccur"].items():
            if a < bkw and a in pos and bkw in pos:
                edges.append((n, a, bkw))
    for n, a, bkw in sorted(edges, reverse=True)[:20]:
        (x1, y1), (x2, y2) = pos[a], pos[bkw]
        svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#94a3b8" '
                   f'stroke-width="{min(0.6 + n * 0.4, 2.4)}" stroke-dasharray="4 4" opacity="0.6"/>')
    svg.append(f'<g><circle cx="{cx}" cy="{cy}" r="46" fill="#111827"/>'
               f'<text x="{cx}" y="{cy - 2}" text-anchor="middle" font-size="13" fill="#fff">VIA 知識體</text>'
               f'<text x="{cx}" y="{cy + 16}" text-anchor="middle" font-size="10" fill="#cbd5e1">{len(kws)} 關鍵字</text></g>')
    n_ing = len(ssot["ingest_log"])
    html = f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA 知識體 Mind Map v0100</title><style>
body{{margin:0;background:#f6f7f9;font-family:'Segoe UI','Noto Sans TC',sans-serif;color:#1f2937}}
.wrap{{max-width:1060px;margin:0 auto;padding:clamp(8px,2vw,20px)}}
h1{{font-size:clamp(1.05rem,2.4vw,1.5rem);margin:.4em 0 .1em}}
.meta{{color:#64748b;font-size:clamp(.72rem,1.6vw,.85rem)}}
svg{{width:100%;height:auto;background:#fff;border:1px solid #e5e7eb;border-radius:14px;margin-top:10px}}
.note{{font-size:.75rem;color:#64748b;margin-top:8px;overflow-wrap:anywhere}}
</style></head><body><div class="wrap">
<h1>VIA 知識體 Mind Map(三語關鍵字 SSOT)</h1>
<div class="meta">SSOT {len(kws)} 關鍵字 · 攝入 {n_ing} 次 · 生成 {datetime.now().strftime('%Y-%m-%d %H:%M')} ·
分類=庫內冊命中制 · 虛線=同句共現 Top20 · 節點尾碼=ENG063 K 枝</div>
<svg viewBox="0 0 {W} {H}" role="img">{''.join(svg)}</svg>
<div class="note">漸進制:每次 via-mindmap ingest 增量合併(append-only)後由本頁全量重生;
繁/簡/英三語收斂至繁體正字(OpenCC s2twp+ENG063 雙語冊)。</div>
</div></body></html>"""
    MAP_PATH.write_text(html, encoding="utf-8")
    return MAP_PATH


def status() -> int:
    ssot = _load_ssot()
    from collections import Counter
    c = Counter(e["category"] for e in ssot["keywords"].values())
    print(f"SSOT {len(ssot['keywords'])} 關鍵字 · 攝入 {len(ssot['ingest_log'])} 次 · "
          f"分類 {dict(c)} · map={'在' if MAP_PATH.exists() else '未生'}")
    return 0


DEMO_ZH_TW = ("2026年Q1,受房地產市場波動影響,NPL Ratio 攀升至 1.85%,"
              "金管會要求提高備抵呆帳覆蓋率;台積電獲外資調升評等至買進。")
DEMO_ZH_CN = "半导体产业链景气回升,联发科毛利率优于预期,分析师上调目标价。"
DEMO_EN = ("The Fed kept rates unchanged. Analysts raised the Target Price on TSMC, "
           "citing strong EPS growth in the Semiconductor sector; rating Upgrade to Buy.")


def selftest() -> int:
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    chk("① 依賴鏈在位(ENG066/ENG063/產業冊/清單庫)",
        _hub() is not None and _lex063() is not None and IND_MAP.exists()
        and DB_TW.exists())

    global SSOT_PATH, MAP_PATH
    _sp, _mp = SSOT_PATH, MAP_PATH
    with tempfile.TemporaryDirectory() as td:
        SSOT_PATH = Path(td) / "ssot.json"
        MAP_PATH = Path(td) / "map.html"
        r1 = ingest(DEMO_ZH_TW, "demo_zh_tw")
        chk("② 繁中攝入(實體+個股+機構)", r1["extracted"] >= 5 and r1["new"] >= 5,
            f"(抽 {r1['extracted']})")
        r2 = ingest(DEMO_ZH_CN, "demo_zh_cn")
        ss = _load_ssot()
        chk("③ 簡中→繁體正字收斂(联发科→聯發科入冊)",
            "聯發科" in ss["keywords"] and "毛利率" in ss["keywords"],
            f"(+{r2['new']})")
        r3 = ingest(DEMO_EN, "demo_en")
        ss = _load_ssot()
        tp = ss["keywords"].get("目標價")
        chk("④ 英文→雙語冊收斂(Target Price→目標價別名;Fed/EPS 專名保留)",
            tp is not None and any("Target" in a for a in tp["aliases"])
            and ("Fed" in ss["keywords"] or "EPS" in ss["keywords"]))
        cats = {e["category"] for e in ss["keywords"].values()}
        chk("⑤ 分類冊命中制(≥4 類出現;台積電=TICKER)",
            len(cats) >= 4 and ss["keywords"].get("台積電", {}).get("category") == "TICKER",
            f"({sorted(cats)})")
        chk("⑥ 漸進 SSOT(append-only:三次攝入 freq/共現累積+log 3 筆)",
            len(ss["ingest_log"]) == 3
            and any(e["cooccur"] for e in ss["keywords"].values()))
        kb = [e for e in ss["keywords"].values() if e.get("k_branch")]
        chk("⑦ ENG063 K 枝掛載(評等/目標價類詞掛 K1.x)", len(kb) >= 1,
            f"({len(kb)} 詞掛枝)")
        p = build_map()
        h = p.read_text(encoding="utf-8")
        chk("⑧ mind map HTML(放射樹+共現虛線+行動自適應)",
            "svg" in h and "stroke-dasharray" in h and "viewport" in h
            and "知識體" in h)
    SSOT_PATH, MAP_PATH = _sp, _mp
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑨ 紀律宣告(append-only/庫內冊命中零發明/引擎不重造)",
        all(k in src for k in ("append-only", "零發明", "引擎不重造")))
    print(f"  [計] 九檢 OK {9 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 三語關鍵字 SSOT×Mind map(VRN_ENG067)· 九檢自測(零網路)===")
        return selftest()
    if "--status" in args:
        return status()
    if "--map" in args:
        p = build_map()
        print(f"[map] {p}")
        return 0
    if "ingest" in args:
        text = None
        if "--text" in args:
            text = args[args.index("--text") + 1]
        elif "--file" in args:
            text = Path(args[args.index("--file") + 1]).read_text(encoding="utf-8")
        if not text:
            print("ingest 需 --text 或 --file")
            return 1
        r = ingest(text, source=args[args.index("--file") + 1] if "--file" in args else "direct_text")
        print(f"[攝入] 抽 {r['extracted']} · 新 {r['new']} · 併 {r['merged']} · SSOT 累計 {r['ssot_total']}")
        build_map()
        print(f"[map] 已重生 {MAP_PATH.name}")
        return 0
    print(__doc__.split("用法:")[1])
    return 0


if __name__ == "__main__":
    sys.exit(main())
