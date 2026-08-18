import json
from pathlib import Path
from datetime import datetime

out = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_SELECTOR_GATE_v027_20260610_141147\\runtime\\vdf_akshare_selector_gate_result_v027.json")
selector_map = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_SELECTOR_GATE_v027_20260610_141147\\registry\\VDF_AkShare_SelectorMap_v027.json")

result = {
    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "status": "VDF_AKSHARE_SELECTOR_GATE_READY",
    "risk": "LOW",
    "policy": "Local introspection only. No API call. No fetch. No DB write.",
    "akshare_import": False,
    "akshare_version": "",
    "total_functions": 0,
    "candidate_count": 0,
    "categories": {},
    "selectors": [],
    "recommendation": "UNKNOWN"
}

targets = [
    {
        "category": "BDI_FREIGHT",
        "priority": "P0",
        "keywords": ["bdi", "baltic", "freight", "shipping", "dry", "bulk", "波罗的海", "航运", "干散货", "运价"]
    },
    {
        "category": "IRON_ORE",
        "priority": "P0",
        "keywords": ["iron", "ore", "mineral", "铁矿", "铁矿石", "矿石"]
    },
    {
        "category": "COKING_COAL",
        "priority": "P0",
        "keywords": ["coking", "coal", "焦煤", "焦炭", "煤炭"]
    },
    {
        "category": "STEEL",
        "priority": "P1",
        "keywords": ["steel", "rebar", "hot", "coil", "螺纹钢", "热卷", "钢材", "钢铁", "线材"]
    },
    {
        "category": "COMMODITY_FUTURES",
        "priority": "P1",
        "keywords": ["futures", "commodity", "期货", "商品", "现货", "spot"]
    },
    {
        "category": "MACRO_CHINA",
        "priority": "P2",
        "keywords": ["macro", "china", "index", "宏观", "中国", "经济", "指数"]
    }
]

try:
    import akshare as ak
    result["akshare_import"] = True
    result["akshare_version"] = str(getattr(ak, "__version__", "unknown"))

    names = [n for n in dir(ak) if not n.startswith("_")]
    funcs = []
    for n in names:
        try:
            obj = getattr(ak, n)
            if callable(obj):
                funcs.append(n)
        except Exception:
            pass

    result["total_functions"] = len(funcs)

    selectors = []
    for f in funcs:
        low = f.lower()
        score = 0
        hit_categories = []
        hit_keywords = []

        for t in targets:
            hits = [kw for kw in t["keywords"] if kw.lower() in low]
            if hits:
                hit_categories.append(t["category"])
                hit_keywords.extend(hits)
                if t["priority"] == "P0":
                    score += 100 * len(hits)
                elif t["priority"] == "P1":
                    score += 50 * len(hits)
                else:
                    score += 20 * len(hits)

        if score > 0:
            selectors.append({
                "function": f,
                "score": score,
                "categories": sorted(list(set(hit_categories))),
                "hit_keywords": sorted(list(set(hit_keywords))),
                "mode": "LOCAL_INTROSPECTION_ONLY",
                "status": "CANDIDATE",
                "risk": "LOW",
                "next_action": "v027.1 signature/doc probe only; do not fetch yet"
            })

    selectors = sorted(selectors, key=lambda x: (-x["score"], x["function"]))
    result["selectors"] = selectors[:200]
    result["candidate_count"] = len(selectors)

    cats = {}
    for s in selectors:
        for c in s["categories"]:
            cats[c] = cats.get(c, 0) + 1
    result["categories"] = cats

    if len(selectors) == 0:
        result["status"] = "VDF_AKSHARE_SELECTOR_GATE_READY_WITH_REVIEW"
        result["risk"] = "MEDIUM"
        result["recommendation"] = "NO_MATCH_FOUND_REVIEW_AKSHARE_VERSION_OR_KEYWORDS"
    else:
        result["recommendation"] = "ALLOW_V0271_AKSHARE_SIGNATURE_DOC_PROBE_ONLY"

except Exception as e:
    result["status"] = "VDF_AKSHARE_SELECTOR_GATE_WITH_REVIEW"
    result["risk"] = "HIGH"
    result["error"] = str(e)
    result["recommendation"] = "BLOCK_AKSHARE_IMPORT_OR_ENV_REPAIR"

selector_map.parent.mkdir(parents=True, exist_ok=True)
selector_map.write_text(json.dumps({
    "generated_at": result["generated_at"],
    "policy": result["policy"],
    "akshare_import": result["akshare_import"],
    "akshare_version": result["akshare_version"],
    "total_functions": result["total_functions"],
    "candidate_count": result["candidate_count"],
    "categories": result["categories"],
    "selectors": result["selectors"]
}, ensure_ascii=False, indent=2), encoding="utf-8")

out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({
    "status": result["status"],
    "risk": result["risk"],
    "akshare_import": result["akshare_import"],
    "akshare_version": result["akshare_version"],
    "total_functions": result["total_functions"],
    "candidate_count": result["candidate_count"],
    "categories": result["categories"],
    "recommendation": result["recommendation"]
}, ensure_ascii=False))
