"""VIA 統一引擎門面 —— 把 50 個底層模組整合為 7 大引擎(單一入口)。

只增不減:底層模組全部保留不動,本檔僅提供整合門面,讓呼叫端(或消費者的 AI)
用一致的 7 引擎 API 操作,不必逐一認識 50 個模組。

    from pmis_lite.via_engines import VIA
    via = VIA()
    via.intake.run(paths)          # 擷取→修復→驗證→智慧資產庫
    via.ssot.resolve("ECO")        # 同義字→唯一基準
    via.sync.sync(ssot, tasks)     # SSOT↔MS Project
    via.bom.classify(text)         # Super BOM 品類
    via.finance.verify(d)          # 財務驗證閘門
    via.gov.scan(root)             # 治理掃描
    via.knowledge.tcode("CS15")    # SAP/PLM/PMBOK 知識
"""
from __future__ import annotations

from . import ingest_engine, ingest_plus, code_parse, table_repair, smart_asset
from . import ssot_synonyms, plm_pmbok_ref, sap_bom_ref, autocode
from . import sync_ssot
from . import super_bom, bom_template
from . import fin_verify
from . import module_scan


class IntakeEngine:
    """① 擷取引擎:全格式讀取→修復→可驗證幅度→智慧資產庫。
    整合 ingest_engine · ingest_plus · code_parse · table_repair · smart_asset · adapters。"""
    name = "IntakeEngine 擷取"
    modules = ["ingest_engine", "ingest_plus", "code_parse", "table_repair",
               "smart_asset", "adapters.*"]

    def run(self, paths, out_json=None):
        return ingest_plus.doomsday_intake(paths, out_json=out_json)

    def parse_code(self, text, path=""):
        return code_parse.parse_structure(text, path=path)

    def repair_table(self, rows):
        return table_repair.repair_table(rows)

    def assets(self, units):
        return smart_asset.build_asset_db(units)

    def guarantee(self, audits):
        return ingest_engine.guarantee_report(audits)

    def ocr(self, path, engine="auto", official_list=None):
        """影像/掃描 OCR:有 surya 則真辨識,否則 VRN 檔名備援錨點(不中斷)。"""
        from . import ocr_intake
        return ocr_intake.ocr_image(path, engine=engine, official_list=official_list)

    def decompose_filename(self, path, official_list=None):
        """VRN no-OCR 路線:從檔名抽 broker/ticker/date 錨點。"""
        from . import ocr_intake
        return ocr_intake.decompose_filename(path, official_list)


class SSOTEngine:
    """② SSOT 引擎:同義字增量展開→唯一基準,PLM/PMBOK/SAP 對齊,自動編碼。
    整合 ssot_synonyms · plm_pmbok_ref · autocode。"""
    name = "SSOTEngine 歸一"
    modules = ["ssot_synonyms", "plm_pmbok_ref", "autocode"]

    def __init__(self):
        self.syn = ssot_synonyms.build_default()
        self.alignment = plm_pmbok_ref.sync_frameworks(self.syn)

    def resolve(self, term):
        return self.syn.resolve(term)

    def add_synonym(self, term, canon, declare=False):
        return self.syn.add_synonym(term, canon, declare_override=declare)

    def registry(self):
        return self.syn.registry()

    def autocode(self, record, source_type, category="auto"):
        return autocode.mint_universal_id(record, source_type, category)


class SyncEngine:
    """③ 同步引擎:SSOT↔MS Project append-only 版本化 + 衝突偵測 + 任務↔BOM 橋接。
    整合 sync_ssot · adapters.msproject · adapters.plm。"""
    name = "SyncEngine 同步"
    modules = ["sync_ssot", "adapters.msproject", "adapters.plm"]

    def sync(self, ssot, tasks):
        return sync_ssot.sync_tasks(ssot, tasks)

    def conflicts(self, tasks):
        return sync_ssot.detect_conflicts(tasks)

    def link_bom(self, tasks, bom_parts):
        return sync_ssot.link_task_bom(tasks, bom_parts)

    def ms_anchor(self, project, task, ts=""):
        return sync_ssot.ms_anchor(project, task, ts)

    def bom_anchor(self, part, rev, state=""):
        return sync_ssot.bom_anchor(part, rev, state)

    def writeback(self, ssot, tasks, approved_only=True):
        """雙向回寫:從 SSOT 產出可回寫集(active + 核可閘門)。"""
        return sync_ssot.writeback_set(ssot, tasks, approved_only=approved_only)

    def to_xml(self, tasks, project_name="VIA_SSOT_Export"):
        """SSOT 任務 → 可匯入 MS Project 的 XML。"""
        return sync_ssot.to_msproject_xml(tasks, project_name)

    def roundtrip(self, tasks):
        """SSOT → XML → 反解析 逐欄對帳(無資料流失驗證)。"""
        return sync_ssot.roundtrip_check(tasks)


class BOMEngine:
    """④ 料表引擎:Super BOM 品類分類 + 成本滾算 + where-used。
    整合 super_bom · bom_template · psu_taxonomy。"""
    name = "BOMEngine 料表"
    modules = ["super_bom", "bom_template", "psu_taxonomy"]

    def classify(self, text):
        return super_bom.classify_commodity_super(text)

    def taxonomy(self):
        return super_bom.merged_commodity_taxonomy()

    def validate(self, rows):
        return super_bom.validate_super_bom(rows)

    def rollup(self, rows):
        return bom_template.cost_rollup(rows)

    def where_used(self, rows, part):
        return bom_template.where_used(rows, part)


class FinanceEngine:
    """⑤ 財務引擎:會計恆等式驗證閘門 + 成本結構 + 校準 + 同業。
    整合 fin_verify。"""
    name = "FinanceEngine 財務"
    modules = ["fin_verify"]

    def verify(self, d):
        return fin_verify.verify_report(d)

    def cost(self, unit_variable, fixed_cost, price, volume):
        return fin_verify.cost_structure(unit_variable, fixed_cost, price, volume)

    def calibrate(self, bottom_up, reported, tol=0.05):
        return fin_verify.calibrate(bottom_up, reported, tol)

    def peers(self, companies, metrics):
        return fin_verify.peer_table(companies, metrics)


class KnowledgeEngine:
    """⑥ 知識引擎:SAP BOM(T-codes/Q-D-V/不展開)+ PLM + PMBOK 參照。
    整合 sap_bom_ref · plm_pmbok_ref。"""
    name = "KnowledgeEngine 知識"
    modules = ["sap_bom_ref", "plm_pmbok_ref"]

    def tcode(self, code):
        return sap_bom_ref.tcode(code)

    def select_bom(self, has_pv, lot_size_ranges):
        return sap_bom_ref.select_bom_method(has_pv, lot_size_ranges)

    def plm_concepts(self):
        return plm_pmbok_ref.PLM_CONCEPTS

    def pmbok_areas(self):
        return plm_pmbok_ref.PMBOK_AREAS


class GovernanceEngine:
    """⑦ 治理引擎:專案掃描 fan-in 分類 + 載入順序 + 完整性。
    整合 module_scan · completeness · selfcheck。"""
    name = "GovernanceEngine 治理"
    modules = ["module_scan", "completeness", "selfcheck"]

    def scan(self, root, exts=(".py",)):
        return module_scan.scan_project(root, exts)

    def import_order(self, inventory):
        return module_scan.import_guide(inventory)


class VIA:
    """VIA 七大引擎統一入口。50 模組 → 7 引擎,一個物件全操作。"""

    def __init__(self):
        self.intake = IntakeEngine()
        self.ssot = SSOTEngine()
        self.sync = SyncEngine()
        self.bom = BOMEngine()
        self.finance = FinanceEngine()
        self.knowledge = KnowledgeEngine()
        self.gov = GovernanceEngine()

    def engines(self):
        """列出七大引擎與其整合的底層模組(供矩陣/文件用)。"""
        out = []
        for attr in ("intake", "ssot", "sync", "bom", "finance", "knowledge", "gov"):
            e = getattr(self, attr)
            out.append({"engine": e.name, "key": attr, "modules": e.modules,
                        "ops": [m for m in dir(e) if not m.startswith("_")
                                and callable(getattr(e, m)) and m not in ("name", "modules")]})
        return out
