# =====================================================================================
# VIA AutoCoder Engine v0100 — 全域編碼註冊中心(自動識別編號器)
# 八大架構類別: SYS 系統 / SPT 支援性工具 / FNT 功能性工具 / SPJ 專案子系統
#               MDL 模組 / ENG 引擎 / CLS 類別 / FNC 函數庫
# 泛用狀態類別: DEV/STG/UAT/PROD · INIT/RUN/PEND/SUSP/TERM/DONE · ERR/WARN/CRIT/INFO · AUTH/DENY
# 治理: 持久化(registry JSON) · 只增不減(append-only ledger,已給之號永不回收/改寫)
#       冪等(同類別+同名 → 恆返同號) · 前綴唯一(九頭龍防治) · 語意 suffix(SPJ-VRN / FNC-SEABORN)
# 既有編號域共存登錄: VIA-DS- / VIA-GRP- / VRN MDL### / SAM-(Note Pro) — 本引擎不重發不侵入
# CLI:
#   py via_autocoder_engine_v0100.py <類別> <元件名> [suffix]   給號(冪等)
#   py via_autocoder_engine_v0100.py --register <類別> <前綴> [padding]
#   py via_autocoder_engine_v0100.py --list
# =====================================================================================
import os, sys, json, datetime

_HERE = os.path.dirname(os.path.abspath(__file__))
REGISTRY = os.path.join(_HERE, "VIA_AutoCode_Registry_v0100.json")

_SEED_CATEGORIES = {
    "系統": {"prefix": "SYS", "padding": 3}, "支援性工具": {"prefix": "SPT", "padding": 3},
    "功能性工具": {"prefix": "FNT", "padding": 3}, "專案子系統": {"prefix": "SPJ", "padding": 3},
    "模組": {"prefix": "MDL", "padding": 3}, "引擎": {"prefix": "ENG", "padding": 3},
    "類別": {"prefix": "CLS", "padding": 3}, "函數庫": {"prefix": "FNC", "padding": 3},
    "開發環境": {"prefix": "DEV", "padding": 4}, "測試環境": {"prefix": "STG", "padding": 4},
    "驗收環境": {"prefix": "UAT", "padding": 4}, "正式環境": {"prefix": "PROD", "padding": 4},
    "初始化狀態": {"prefix": "INIT", "padding": 4}, "運行狀態": {"prefix": "RUN", "padding": 4},
    "等待任務": {"prefix": "PEND", "padding": 4}, "掛起狀態": {"prefix": "SUSP", "padding": 4},
    "終止狀態": {"prefix": "TERM", "padding": 4}, "完成狀態": {"prefix": "DONE", "padding": 4},
    "錯誤日誌": {"prefix": "ERR", "padding": 4}, "系統警告": {"prefix": "WARN", "padding": 4},
    "嚴重警告": {"prefix": "CRIT", "padding": 4}, "監控資訊": {"prefix": "INFO", "padding": 4},
    "認證授權": {"prefix": "AUTH", "padding": 4}, "權限拒絕": {"prefix": "DENY", "padding": 4},
}
_COEXISTING_NAMESPACES = {
    "VIA-DS-": "資料集登錄(擷取矩陣 77 項,nexus register-check)",
    "VIA-GRP-": "台股族群分類(36 群)",
    "VRN_MDL": "VRN 模組歷史編號(MDL001-264 家族)",
    "SAM-": "VIA_Note_Pro 資產編碼(SAM-SSOT/PRMT/CODE/RSCH/ASSET)",
    "BNR-": "封面圖庫(BNR-類別-序號)",
    "ISS-": "VMT CPM 議題編號",
}

class CentralRegistrationEngine:
    def __init__(self, path=REGISTRY):
        self.path = path
        if os.path.exists(path):
            d = json.load(open(path, encoding="utf-8"))
        else:
            d = {"registry_id": "VIA_AutoCode_Registry_v0100", "append_only": True,
                 "coexisting_namespaces": _COEXISTING_NAMESPACES,
                 "categories": {k: dict(v, current=0) for k, v in _SEED_CATEGORIES.items()},
                 "components": {}, "ledger": []}
        self.d = d

    def _save(self):
        tmp = self.path + ".tmp"
        json.dump(self.d, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        os.replace(tmp, self.path)

    def register_category(self, name, prefix, padding=3):
        cats = self.d["categories"]
        if name in cats:
            return "EXISTS %s (%s)" % (name, cats[name]["prefix"])
        clash = [k for k, v in cats.items() if v["prefix"] == prefix]
        ns = [p for p in self.d["coexisting_namespaces"] if p.rstrip("-_").endswith(prefix) or prefix in p]
        if clash or ns:
            return "REJECT prefix %s 與既有域衝突: %s" % (prefix, clash or ns)
        cats[name] = {"prefix": prefix, "padding": int(padding), "current": 0}
        self.d["ledger"].append({"ts": datetime.datetime.now().isoformat(timespec="seconds"),
                                 "op": "REGISTER_CATEGORY", "name": name, "prefix": prefix})
        self._save()
        return "OK 註冊類別 %s (%s)" % (name, prefix)

    def generate_code(self, category, component, suffix=None):
        cats = self.d["categories"]
        if category not in cats:
            raise ValueError("未知類別 %s — 先 --register" % category)
        key = category + "|" + component
        if key in self.d["components"]:
            return self.d["components"][key]
        cfg = cats[category]
        if suffix:
            code = "%s-%s" % (cfg["prefix"], suffix)
            if code in self.d["components"].values():
                raise ValueError("語意編碼 %s 已被占用(只增不減,不重發)" % code)
        else:
            cfg["current"] += 1
            code = "%s-%s" % (cfg["prefix"], str(cfg["current"]).zfill(cfg["padding"]))
        self.d["components"][key] = code
        self.d["ledger"].append({"ts": datetime.datetime.now().isoformat(timespec="seconds"),
                                 "op": "ASSIGN", "category": category, "component": component, "code": code})
        self._save()
        return code

    def listing(self):
        out = ["=== VIA 全域編碼註冊清單 (%d 件) ===" % len(self.d["components"])]
        for k, v in sorted(self.d["components"].items(), key=lambda x: x[1]):
            cat, name = k.split("|", 1)
            out.append("%-14s [%s] %s" % (v, cat, name))
        out.append("--- 共存編號域(本引擎不侵入) ---")
        for p, desc in self.d["coexisting_namespaces"].items():
            out.append("%-10s %s" % (p, desc))
        return "\n".join(out)

def main(argv):
    e = CentralRegistrationEngine()
    if not argv or argv[0] == "--list":
        print(e.listing()); return
    if argv[0] == "--register":
        print(e.register_category(argv[1], argv[2], int(argv[3]) if len(argv) > 3 else 3)); return
    cat, comp = argv[0], argv[1]
    sfx = argv[2] if len(argv) > 2 else None
    print(e.generate_code(cat, comp, sfx))

if __name__ == "__main__":
    main(sys.argv[1:])
