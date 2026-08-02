"""同義字增量展開引擎 —— 多術語收斂到「唯一 SSOT 基準」。

原則：
  - 每個概念只有一個 canonical（唯一 SSOT 基準），跨系統/語言的說法都是它的同義字。
  - 增量展開：add_synonym 只增不減；若同義字已指向別的 canonical → 回報衝突（除非宣告）。
  - resolve(任一術語) → 唯一 canonical；expand(canonical) → 全部同義字。
用途：PLM/PMBOK/SAP/MS Project/中文各自的用語，全部對齊到同一個 SSOT 錨點。
純 stdlib、離線、可測。
"""
from __future__ import annotations


def _norm(s: str) -> str:
    return (s or "").strip().lower()


class SynonymSSOT:
    def __init__(self):
        self.canonical = {}   # canon_id -> {"name":..., "domain":...}
        self.syn = {}         # norm(term) -> canon_id
        self.ledger = []      # append-only 日誌

    def add_canonical(self, canon_id, name, domain="SSOT"):
        if canon_id not in self.canonical:      # 唯一：已存在則不覆寫
            self.canonical[canon_id] = {"name": name, "domain": domain}
            self.syn[_norm(canon_id)] = canon_id
            self.syn[_norm(name)] = canon_id
            self.ledger.append(("CANON", canon_id, name))
        return canon_id

    def add_synonym(self, term, canon_id, declare_override=False):
        """增量加同義字。若已指向別的 canonical → 衝突（不覆寫，除非宣告）。"""
        k = _norm(term)
        if canon_id not in self.canonical:
            return {"ok": False, "reason": f"canonical {canon_id} 不存在"}
        existing = self.syn.get(k)
        if existing and existing != canon_id and not declare_override:
            return {"ok": False, "reason": "conflict",
                    "detail": f"'{term}' 已指向 {existing}，未宣告不可改指 {canon_id}"}
        self.syn[k] = canon_id
        self.ledger.append(("SYN", canon_id, term + (" (override)" if existing and declare_override else "")))
        return {"ok": True, "canonical": canon_id}

    def resolve(self, term):
        """任一術語 → 唯一 canonical（找不到回 None）。"""
        return self.syn.get(_norm(term))

    def expand(self, canon_id):
        """canonical → 全部同義字。"""
        return sorted(t for t, c in self.syn.items() if c == canon_id)

    def registry(self):
        out = []
        for cid, meta in self.canonical.items():
            out.append({"canonical": cid, "name": meta["name"], "domain": meta["domain"],
                        "synonyms": self.expand(cid)})
        return out


# ── 種子：把 PLM / PMBOK / SAP / MS Project / 中文 對齊到唯一 SSOT ──
def build_default() -> SynonymSSOT:
    s = SynonymSSOT()
    seed = [
        ("SSOT-BOM", "物料清單 BOM", "core",
         ["BOM", "Bill of Materials", "Stückliste", "EBOM", "MBOM", "料表", "CS01"]),
        ("SSOT-ITEM", "料號 Item", "core",
         ["Part Number", "Material", "CPN", "MPN", "料號", "品號", "Item Master"]),
        ("SSOT-CHANGE", "工程變更 Change", "plm",
         ["ECO", "ECN", "ECR", "Engineering Change Order", "AENR", "Change Number", "工程變更單"]),
        ("SSOT-REVISION", "版次 Revision", "plm",
         ["Revision", "Rev", "Version", "版次", "修訂", "改版"]),
        ("SSOT-LIFECYCLE", "生命週期 Lifecycle", "plm",
         ["Lifecycle", "PLM", "生命週期", "EOL", "Active", "Deprecated", "Phase-out"]),
        ("SSOT-SCHEDULE", "時程 Schedule", "pmbok",
         ["Schedule", "Timeline", "Task", "Gantt", "甘特", "排程", "時程", "進度", "Schedule Management"]),
        ("SSOT-SCOPE", "範疇 Scope", "pmbok",
         ["Scope", "WBS", "Work Breakdown", "工作分解", "範疇", "Scope Management"]),
        ("SSOT-COST", "成本 Cost", "pmbok",
         ["Cost", "Budget", "成本", "預算", "Cost Roll-up", "Cost Management"]),
        ("SSOT-RESOURCE", "資源 Resource", "pmbok",
         ["Resource", "Assignment", "資源", "人力", "指派", "Resource Management"]),
        ("SSOT-RISK", "風險 Risk", "pmbok",
         ["Risk", "Risk Register", "風險", "風險登錄", "Risk Management"]),
        ("SSOT-QUALITY", "品質 Quality", "pmbok",
         ["Quality", "QA", "品質", "良率", "Quality Management"]),
        ("SSOT-STAKEHOLDER", "利害關係人 Stakeholder", "pmbok",
         ["Stakeholder", "利害關係人", "干係人", "Stakeholder Management"]),
        ("SSOT-INTEGRATION", "整合 Integration", "pmbok",
         ["Integration", "整合", "Integration Management", "Change Control"]),
        ("SSOT-PROCUREMENT", "採購 Procurement", "pmbok",
         ["Procurement", "採購", "Procurement Management", "AVL", "AML"]),
        ("SSOT-COMMS", "溝通 Communications", "pmbok",
         ["Communications", "溝通", "Communications Management", "Reporting"]),
    ]
    for cid, name, dom, syns in seed:
        s.add_canonical(cid, name, dom)
        for t in syns:
            s.add_synonym(t, cid)
    return s
