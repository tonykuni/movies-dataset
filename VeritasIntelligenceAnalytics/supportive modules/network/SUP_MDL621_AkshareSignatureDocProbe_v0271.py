import json
import csv
import inspect
from pathlib import Path
from datetime import datetime

selector_map_path = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_SELECTOR_GATE_v027_20260610_141147\\registry\\VDF_AkShare_SelectorMap_v027.json")
out = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_SIGNATURE_DOC_PROBE_v0271_20260610_141608\\runtime\\vdf_akshare_signature_doc_probe_result_v0271.json")
signature_map_path = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_SIGNATURE_DOC_PROBE_v0271_20260610_141608\\registry\\VDF_AkShare_SignatureDocMap_v0271.json")
shortlist_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_SIGNATURE_DOC_PROBE_v0271_20260610_141608\\registry\\VDF_AkShare_SignatureDocShortlist_v0271.csv")
top_per_category = int("30")

result = {
    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "status": "VDF_AKSHARE_SIGNATURE_DOC_PROBE_READY",
    "risk": "LOW",
    "policy": "Signature/docstring probe only. No function call. No API. No data fetch. No DB write.",
    "akshare_import": False,
    "akshare_version": "",
    "selector_input_count": 0,
    "signature_probe_count": 0,
    "shortlist_count": 0,
    "categories": {},
    "recommendation": "UNKNOWN",
    "shortlist": []
}

targets = {
    "BDI_FREIGHT": {
        "must": ["bdi", "baltic", "freight", "shipping", "dry", "bulk", "波罗的海", "航运", "干散货"],
        "avoid": ["news", "notice"],
        "preferred": ["index", "daily", "hist", "macro", "futures"]
    },
    "IRON_ORE": {
        "must": ["iron", "ore", "铁矿", "铁矿石", "矿石"],
        "avoid": ["news", "notice"],
        "preferred": ["futures", "spot", "daily", "hist", "price"]
    },
    "COKING_COAL": {
        "must": ["coking", "coal", "焦煤", "焦炭", "煤炭"],
        "avoid": ["news", "notice"],
        "preferred": ["futures", "spot", "daily", "hist", "price"]
    },
    "STEEL": {
        "must": ["steel", "rebar", "hot", "coil", "螺纹钢", "热卷", "钢材", "钢铁", "线材"],
        "avoid": ["news", "notice"],
        "preferred": ["futures", "spot", "daily", "hist", "price"]
    },
    "COMMODITY_FUTURES": {
        "must": ["futures", "commodity", "期货", "商品", "现货", "spot"],
        "avoid": ["news", "notice"],
        "preferred": ["daily", "hist", "price", "symbol"]
    },
    "MACRO_CHINA": {
        "must": ["macro", "china", "index", "宏观", "中国", "经济", "指数"],
        "avoid": ["news", "notice"],
        "preferred": ["daily", "monthly", "hist", "index"]
    }
}

def text_score(text, cats):
    low = text.lower()
    score = 0
    hits = []
    for c in cats:
        rule = targets.get(c, {})
        for kw in rule.get("must", []):
            if kw.lower() in low:
                score += 20
                hits.append(kw)
        for kw in rule.get("preferred", []):
            if kw.lower() in low:
                score += 8
                hits.append(kw)
        for kw in rule.get("avoid", []):
            if kw.lower() in low:
                score -= 30
    return score, sorted(list(set(hits)))

try:
    import akshare as ak
    result["akshare_import"] = True
    result["akshare_version"] = str(getattr(ak, "__version__", "unknown"))

    if not selector_map_path.exists():
        raise RuntimeError("Selector map missing.")

    selector_map = json.loads(selector_map_path.read_text(encoding="utf-8"))
    selectors = selector_map.get("selectors", [])
    result["selector_input_count"] = len(selectors)

    rows = []
    for s in selectors:
        fname = s.get("function", "")
        cats = s.get("categories", [])
        base_score = int(s.get("score", 0))

        item = {
            "function": fname,
            "categories": cats,
            "base_score": base_score,
            "signature": "",
            "doc_head": "",
            "module": "",
            "probe_status": "UNKNOWN",
            "probe_error": "",
            "signature_score": 0,
            "doc_score": 0,
            "total_score": base_score,
            "hit_keywords": s.get("hit_keywords", []),
            "next_action": "v027.2 sample-call gate only; max 1-row, no DB write"
        }

        try:
            obj = getattr(ak, fname)
            item["module"] = str(getattr(obj, "__module__", ""))
            try:
                item["signature"] = str(inspect.signature(obj))
            except Exception as e:
                item["signature"] = f"SIGNATURE_UNAVAILABLE: {e}"

            doc = inspect.getdoc(obj) or ""
            doc_head = " ".join(doc.splitlines()[:8])
            item["doc_head"] = doc_head[:900]

            sig_score, sig_hits = text_score(fname + " " + item["signature"], cats)
            doc_score, doc_hits = text_score(doc_head, cats)
            item["signature_score"] = sig_score
            item["doc_score"] = doc_score
            item["hit_keywords"] = sorted(list(set(item["hit_keywords"] + sig_hits + doc_hits)))
            item["total_score"] = base_score + sig_score + doc_score

            if "SIGNATURE_UNAVAILABLE" in item["signature"]:
                item["probe_status"] = "OK_DOC_ONLY"
            else:
                item["probe_status"] = "OK_SIGNATURE_DOC"

        except Exception as e:
            item["probe_status"] = "PROBE_ERROR"
            item["probe_error"] = str(e)
            item["total_score"] = base_score - 50

        rows.append(item)

    result["signature_probe_count"] = len(rows)

    short = []
    for cat in targets.keys():
        cat_rows = [r for r in rows if cat in r.get("categories", [])]
        cat_rows = sorted(cat_rows, key=lambda x: (-x["total_score"], x["function"]))
        selected = cat_rows[:top_per_category]
        for r in selected:
            rr = dict(r)
            rr["selected_category"] = cat
            short.append(rr)

    # remove duplicate function/category pairs only, keep same function under different category if relevant
    dedup = []
    seen = set()
    for r in short:
        key = (r["selected_category"], r["function"])
        if key not in seen:
            seen.add(key)
            dedup.append(r)

    result["shortlist"] = dedup
    result["shortlist_count"] = len(dedup)

    cats = {}
    for r in dedup:
        cats[r["selected_category"]] = cats.get(r["selected_category"], 0) + 1
    result["categories"] = cats

    signature_map_path.parent.mkdir(parents=True, exist_ok=True)
    signature_map_path.write_text(json.dumps({
        "generated_at": result["generated_at"],
        "policy": result["policy"],
        "akshare_import": result["akshare_import"],
        "akshare_version": result["akshare_version"],
        "selector_input_count": result["selector_input_count"],
        "signature_probe_count": result["signature_probe_count"],
        "shortlist_count": result["shortlist_count"],
        "categories": result["categories"],
        "shortlist": result["shortlist"]
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    shortlist_csv.parent.mkdir(parents=True, exist_ok=True)
    with shortlist_csv.open("w", encoding="utf-8-sig", newline="") as f:
        fieldnames = [
            "selected_category","function","total_score","base_score","signature_score","doc_score",
            "probe_status","signature","module","hit_keywords","next_action","doc_head","probe_error"
        ]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in dedup:
            w.writerow({
                "selected_category": r.get("selected_category",""),
                "function": r.get("function",""),
                "total_score": r.get("total_score",0),
                "base_score": r.get("base_score",0),
                "signature_score": r.get("signature_score",0),
                "doc_score": r.get("doc_score",0),
                "probe_status": r.get("probe_status",""),
                "signature": r.get("signature",""),
                "module": r.get("module",""),
                "hit_keywords": "|".join([str(x) for x in r.get("hit_keywords",[])]),
                "next_action": r.get("next_action",""),
                "doc_head": r.get("doc_head",""),
                "probe_error": r.get("probe_error","")
            })

    if result["shortlist_count"] <= 0:
        result["status"] = "VDF_AKSHARE_SIGNATURE_DOC_PROBE_READY_WITH_REVIEW"
        result["risk"] = "MEDIUM"
        result["recommendation"] = "NO_SHORTLIST_REVIEW_SELECTOR_KEYWORDS"
    else:
        result["recommendation"] = "ALLOW_V0272_AKSHARE_SAMPLE_CALL_GATE_ONLY_MAX_1ROW_NO_DB_WRITE"

except Exception as e:
    result["status"] = "VDF_AKSHARE_SIGNATURE_DOC_PROBE_WITH_REVIEW"
    result["risk"] = "HIGH"
    result["error"] = str(e)
    result["recommendation"] = "BLOCK_SIGNATURE_DOC_PROBE_REPAIR_ENV_OR_SELECTOR_MAP"

out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({
    "status": result["status"],
    "risk": result["risk"],
    "akshare_import": result["akshare_import"],
    "akshare_version": result["akshare_version"],
    "selector_input_count": result["selector_input_count"],
    "signature_probe_count": result["signature_probe_count"],
    "shortlist_count": result["shortlist_count"],
    "categories": result["categories"],
    "recommendation": result["recommendation"]
}, ensure_ascii=False))
