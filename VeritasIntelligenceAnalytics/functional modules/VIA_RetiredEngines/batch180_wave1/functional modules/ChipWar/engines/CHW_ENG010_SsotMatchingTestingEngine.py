# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
import json
import sys
from typing import Dict, List, Tuple, Any, Optional
from pydantic import BaseModel, Field, ValidationError
from rapidfuzz import process, fuzz
from deepdiff import DeepDiff


# ==============================================================================
# 1. UNIVERSAL SCHEMA NEUTRALIZER (For Parking into Unknown Mother SSOTs)
# ==============================================================================

class UniversalSchemaNeutralizer:
    """
    Schema Neutralizer for Unknown Mother Systems.
    Flexibly normalizes diverse Mother System SSOT structures (different key names,
    nested/flat lists, ticker vs symbol vs code) into a clean internal contract.
    """

    @staticmethod
    def normalize_stock_entry(raw_stock: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maps unknown field variants (e.g. symbol/code/ticker, stock_name/name)
        to standard keys: ticker, name, role, basePrice
        """
        ticker = (
            raw_stock.get("ticker")
            or raw_stock.get("symbol")
            or raw_stock.get("code")
            or raw_stock.get("id")
            or ""
        )
        name = (
            raw_stock.get("name")
            or raw_stock.get("stock_name")
            or raw_stock.get("title")
            or raw_stock.get("company")
            or ""
        )
        role = (
            raw_stock.get("role")
            or raw_stock.get("type")
            or raw_stock.get("category")
            or "PEER"
        )
        price = (
            raw_stock.get("basePrice")
            or raw_stock.get("price")
            or raw_stock.get("close")
            or raw_stock.get("adj_close")
            or 100.0
        )

        return {
            "ticker": str(ticker).strip(),
            "name": str(name).strip(),
            "role": str(role).strip().upper(),
            "basePrice": float(price) if price else 100.0
        }

    @classmethod
    def normalize_database(cls, raw_db: Dict[str, Any]) -> Dict[str, Any]:
        """
        Accepts dict or nested JSON from Mother System and converts it into a standard structure.
        """
        normalized_db = {}

        # Handle Mother DBs formatted as a List of Sectors vs Dict of Sectors
        if isinstance(raw_db, list):
            for idx, item in enumerate(raw_db):
                sec_name = item.get("sector") or item.get("group") or f"Sector_{idx+1}"
                members_raw = item.get("members") or item.get("stocks") or []
                color = item.get("color") or "#10B981"
                normalized_db[sec_name] = {
                    "color": color,
                    "members": [cls.normalize_stock_entry(m) for m in members_raw]
                }
        elif isinstance(raw_db, dict):
            for sec_name, sec_data in raw_db.items():
                if isinstance(sec_data, dict):
                    members_raw = sec_data.get("members") or sec_data.get("stocks") or sec_data.get("components") or []
                    color = sec_data.get("color") or "#10B981"
                elif isinstance(sec_data, list):
                    members_raw = sec_data
                    color = "#10B981"
                else:
                    continue

                normalized_db[sec_name] = {
                    "color": color,
                    "members": [cls.normalize_stock_entry(m) for m in members_raw]
                }

        return normalized_db


# ==============================================================================
# 2. HYBRID MATCHING & ADAPTER ENGINE (Non-Invasive)
# ==============================================================================

class SSOTMatchingEngine:
    """
    Standalone Engine for Auto-Matching and Synchronizing Local VIA Matrices with 
    Unknown Mother System SSOTs without altering the Mother System DB.
    """

    def __init__(self, local_via_matrix: Dict[str, Any]):
        self.local_via_matrix = UniversalSchemaNeutralizer.normalize_database(local_via_matrix or {})
        self.mother_master_db: Dict[str, Any] = {}
        self.unmapped_tickers: List[str] = []
        self.disambiguated_tickers: List[str] = []

    def load_mother_ssot(self, mother_ssot_raw: Dict[str, Any]) -> bool:
        """
        [Step 1] Ingests and normalizes raw Mother System SSOT data.
        """
        try:
            self.mother_master_db = UniversalSchemaNeutralizer.normalize_database(mother_ssot_raw)
            print(f"✅ [SSOT Ingestion] Successfully ingested and normalized {len(self.mother_master_db)} sectors from Mother System SSOT.")
            return True
        except Exception as e:
            print(f"❌ [SSOT Ingestion Error]: {e}")
            return False

    def auto_match_and_reconcile(self, similarity_threshold: float = 72.0) -> Dict[str, Any]:
        """
        [Step 2] Runs hybrid C++ accelerated fuzzy entity matching locally (RapidFuzz).
        """
        self.unmapped_tickers.clear()
        self.disambiguated_tickers.clear()

        reconciled_shadow_db = {}
        mother_ticker_map = {}
        mother_names_list = []
        mother_tickers_list = []

        # 1. Build Index of Mother SSOT
        for sec_name, sec_data in self.mother_master_db.items():
            for m in sec_data.get("members", []):
                tk = m["ticker"]
                nm = m["name"]
                if tk and tk not in mother_ticker_map:
                    mother_ticker_map[tk] = {
                        "name": nm,
                        "mother_sector": sec_name,
                        "role": m.get("role", "PEER"),
                        "basePrice": m.get("basePrice", 100.0)
                    }
                    if nm:
                        mother_names_list.append(nm)
                        mother_tickers_list.append(tk)

        # 2. Reconcile Local VIA Matrix with Mother SSOT
        for local_sec_name, local_sec_data in self.local_via_matrix.items():
            reconciled_members = []
            local_members = local_sec_data.get("members", [])

            for local_m in local_members:
                loc_ticker = local_m.get("ticker", "").strip()
                loc_name = local_m.get("name", "").strip()

                # Strategy A: Exact Ticker Match
                if loc_ticker in mother_ticker_map:
                    mother_info = mother_ticker_map[loc_ticker]
                    reconciled_members.append({
                        "ticker": loc_ticker,
                        "name": mother_info["name"],  # Adopt official Mother SSOT name
                        "role": local_m.get("role", mother_info["role"]),
                        "basePrice": mother_info["basePrice"],
                        "match_type": "EXACT_TICKER_MATCH"
                    })
                elif mother_names_list:
                    # Strategy B: Hybrid Fuzzy Match (WRatio + Token Sort Ratio)
                    fuzzy_result = process.extractOne(loc_name, mother_names_list, scorer=fuzz.WRatio)

                    if fuzzy_result and fuzzy_result[1] >= similarity_threshold:
                        matched_name = fuzzy_result[0]
                        matched_idx = fuzzy_result[2]
                        matched_ticker = mother_tickers_list[matched_idx]
                        mother_info = mother_ticker_map[matched_ticker]

                        reconciled_members.append({
                            "ticker": matched_ticker,
                            "name": matched_name,
                            "role": local_m.get("role", mother_info["role"]),
                            "basePrice": mother_info["basePrice"],
                            "match_type": f"FUZZY_NAME_MATCH ({fuzzy_result[1]:.1f}%)"
                        })
                        self.disambiguated_tickers.append(f"{loc_name} ({loc_ticker}) -> {matched_name} ({matched_ticker})")
                    else:
                        # Strategy C: Mark as Unmapped Local Stock
                        self.unmapped_tickers.append(f"{loc_name} ({loc_ticker})")
                        reconciled_members.append({
                            "ticker": loc_ticker,
                            "name": loc_name,
                            "role": local_m.get("role", "LAGGARD"),
                            "basePrice": float(local_m.get("basePrice", 100.0)),
                            "match_type": "UNMAPPED_LOCAL_ONLY"
                        })
                else:
                    self.unmapped_tickers.append(f"{loc_name} ({loc_ticker})")
                    reconciled_members.append({
                        "ticker": loc_ticker,
                        "name": loc_name,
                        "role": local_m.get("role", "LAGGARD"),
                        "basePrice": float(local_m.get("basePrice", 100.0)),
                        "match_type": "UNMAPPED_LOCAL_ONLY"
                    })

            reconciled_shadow_db[local_sec_name] = {
                "color": local_sec_data.get("color", "#10B981"),
                "members": reconciled_members
            }

        return reconciled_shadow_db

    def run_failure_audit_test(self, reconciled_shadow_db: Dict[str, Any]) -> Dict[str, Any]:
        """
        [Step 3] Automated Mismatch & Failure Audit.
        Tests structural differences and identifies potential sync risks.
        """
        diff = DeepDiff(self.local_via_matrix, reconciled_shadow_db, ignore_order=True)

        return {
            "Total_Unmapped_Tickers": len(self.unmapped_tickers),
            "Unmapped_List": self.unmapped_tickers,
            "Disambiguated_Fuzzy_Matches": self.disambiguated_tickers,
            "Structural_Variations_Diff": diff.to_dict() if hasattr(diff, "to_dict") else str(diff),
            "Sync_Health_Status": "EXCELLENT" if len(self.unmapped_tickers) == 0 else "WARNING_UNMAPPED_ITEMS"
        }


# ==============================================================================
# 3. AUTOMATED TEST SUITE (Tests All Edge-Cases Until All Pass)
# ==============================================================================

def run_engine_tests():
    print("==================================================================")
    print("      VERITAS VIA — STANDALONE SSOT MATCHING ENGINE TESTS")
    print("==================================================================")

    # Mock Mother System with Unknown Key Names & Nested Structure (Test Edge Case 1)
    unknown_mother_ssot_raw = {
        "Semiconductor_Fab": {
            "color": "#10B981",
            "components": [
                {"symbol": "2330", "company": "台灣積體電路製造股份有限公司", "type": "LEADER", "close": 980.0},
                {"symbol": "2327", "company": "國巨股份有限公司", "type": "LEADER", "close": 520.0},
                {"symbol": "3081", "company": "聯亞光電股份有限公司", "type": "LEADER", "close": 180.0},
                {"symbol": "6442", "company": "光聖科技股份有限公司", "type": "PEER", "close": 210.0}
            ]
        }
    }

    # Mock Local VIA Matrix (Test Edge Case 2: Stock Name Aliases & Ticker Errors)
    local_via_matrix_raw = {
        "CPO 共封裝光學": {
            "color": "#10B981",
            "members": [
                {"ticker": "3081", "name": "聯亞", "role": "LEADER", "basePrice": 180.0},         # Exact Match
                {"ticker": "2330", "name": "台積電", "role": "PEER", "basePrice": 980.0},        # Alias -> Name Updated to Official
                {"ticker": "6442-ERR", "name": "光聖科技", "role": "PEER", "basePrice": 210.0},  # Ticker Error -> RapidFuzz Match
                {"ticker": "8888", "name": "未上市新新創", "role": "LAGGARD", "basePrice": 30.0}  # Unmapped Stock
            ]
        }
    }

    # Test 1: Instantiation & Ingestion
    engine = SSOTMatchingEngine(local_via_matrix_raw)
    ingest_ok = engine.load_mother_ssot(unknown_mother_ssot_raw)
    assert ingest_ok is True, "Ingestion should succeed with UniversalSchemaNeutralizer"

    # Test 2: Matching
    shadow_db = engine.auto_match_and_reconcile(similarity_threshold=70.0)
    cpo_members = shadow_db["CPO 共封裝光學"]["members"]

    assert cpo_members[0]["match_type"] == "EXACT_TICKER_MATCH"
    assert cpo_members[1]["name"] == "台灣積體電路製造股份有限公司", "Name should be normalized to official Mother SSOT name"
    assert "FUZZY_NAME_MATCH" in cpo_members[2]["match_type"], "Incorrect ticker should be resolved via name match"
    assert cpo_members[3]["match_type"] == "UNMAPPED_LOCAL_ONLY"

    print("\n[Test 1 & 2: Reconciled Shadow DB Output]:")
    for m in cpo_members:
        print(f"  • {m['ticker']} | {m['name']} | Match: {m['match_type']}")

    # Test 3: Failure Audit
    audit_report = engine.run_failure_audit_test(shadow_db)
    print("\n[Test 3: Failure Audit Report]:")
    print(f"  ├─ Sync Health Status   : {audit_report['Sync_Health_Status']}")
    print(f"  ├─ Fuzzy Matches Count  : {len(audit_report['Disambiguated_Fuzzy_Matches'])} item(s)")
    print(f"  └─ Unmapped Items Count : {audit_report['Total_Unmapped_Tickers']} item(s)")

    print("\n------------------------------------------------------------------")
    print("✅ All Unit Tests Passed Successfully! Engine is fully functional.")
    print("==================================================================")

if __name__ == "__main__":
    run_engine_tests()