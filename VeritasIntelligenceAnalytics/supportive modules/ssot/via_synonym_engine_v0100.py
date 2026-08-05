# =====================================================================================
# VIA Synonym Engine v0100 — 平台同義字引擎轉接器
# 唯一實作 = PMIS-Lite SynonymSSOT(九頭龍防治:不複製、不另造,直接 import)
# 種子 = VIA_Synonym_Seed_v0100.json(canonical 錨點自 VRN 資料契約抽取;同義字增量登錄)
# 消費端:VRN account_canonical mapper(account_alias_registry)、VDF 欄位正規化
# =====================================================================================
import os, sys, json

_HERE = os.path.dirname(os.path.abspath(__file__))
_PMIS = os.path.join(_HERE, "..", "PMIS-Lite", "pmis_lite", "pmis_lite")
if _PMIS not in sys.path:
    sys.path.insert(0, os.path.abspath(_PMIS))
from ssot_synonyms import SynonymSSOT  # noqa: E402

SEED = os.path.join(_HERE, "VIA_Synonym_Seed_v0100.json")

def build():
    eng = SynonymSSOT()
    seed = json.load(open(SEED, encoding="utf-8"))
    for c in seed["canonicals"]:
        eng.add_canonical(c["canon_id"], c["name"], c.get("domain", "SSOT"))
    for s in seed.get("synonyms", []):
        eng.add_synonym(s["term"], s["canon_id"])
    return eng

if __name__ == "__main__":
    e = build()
    n = len(e.canonical)
    ok = e.syn.get("ticker") is not None
    print("[VIA Synonym Engine] canonicals=%d resolve('ticker')->%s ledger=%d" % (n, e.syn.get("ticker"), len(e.ledger)))
    print("SMOKE " + ("PASS" if (n >= 40 and ok) else "FAIL"))
