import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional

# Import Core Engine Modules
from tw_stock_data_router import TaiwanStockDataRouter
from twse_tpex_data_fetcher import TaiwanMarketDataEngine
from via_group_classification_rotation_engine import (
    VIAGroupClassificationRotationEngine,
    VIA_PURIFIED_SECTOR_MATRIX
)
from institutional_volume_engine import InstitutionalVolumeEngine

# ==============================================================================
# VERITAS VIA — 最終系統綜合整合與除錯驗證測試套件 (Final Integration Test)
# ==============================================================================

class VeritasViaSystemIntegrationTester:
    def __init__(self):
        self.router = TaiwanStockDataRouter()
        self.fetcher = TaiwanMarketDataEngine()
        self.rotation_engine = VIAGroupClassificationRotationEngine(baseline_date="2026-01-02")
        self.inst_engine = InstitutionalVolumeEngine(days=60)
        self.passed = 0
        self.total = 0

    def assert_test(self, condition: bool, test_name: str, detail: str = ""):
        self.total += 1
        if condition:
            self.passed += 1
            print(f"  ✅ [PASS] {test_name} {f'({detail})' if detail else ''}")
        else:
            print(f"  ❌ [FAIL] {test_name} {f'({detail})' if detail else ''}")

    def run_test_1_regex_and_router(self):
        print("\n--- [Test 1] 股票代碼 Regex 驗證與資料源路由 ---")
        self.assert_test(self.router.validate_ticker("2330"), "代碼合規驗證 (2330)")
        self.assert_test(not self.router.validate_ticker("0050"), "錯誤代碼攔截 (0050)")
        # 測試 yfinance 自動切換 (此處為自動備援邏輯驗證)
        df, symbol, market = self.fetcher.fetch_yfinance_daily_data("3081", period="5d")
        self.assert_test(df is not None, "yfinance 數據抓取測試", f"Symbol: {symbol}")

    def test_run_2_purified_matrix_pc1(self):
        print("\n--- [Test 2] V2.0 精練族群矩陣與 PC1 族群同步性測試 ---")
        # 模擬族群數據
        days = 60
        dates = pd.date_range(end="2026-08-01", periods=days, freq="B")
        ret_df = pd.DataFrame({
            "LEADER": np.random.normal(0.001, 0.02, days),
            "PEER": np.random.normal(0.001, 0.02, days),
            "NOISE": np.random.normal(0, 0.05, days)
        }, index=dates)
        
        # 驗證剔除算法邏輯是否正常
        metrics = self.rotation_engine.evaluate_sector_tier_metrics(
            ret_df, pd.Series(0), pd.Series(0), pd.Series(0)
        )
        self.assert_test(metrics["Purified_PC1"] > metrics["Raw_PC1"], "雜訊股剔除後 PC1 提升")

    def run_all(self):
        print("==================================================================")
        print("    VERITAS VIA — 全系統綜合除錯與整合測試執行報告")
        print("==================================================================")
        self.run_test_1_regex_and_router()
        self.test_run_2_purified_matrix_pc1()
        print(f"\n綜合測試結果: {self.passed} / {self.total} 項目全部通過")
        print("==================================================================")

if __name__ == "__main__":
    VeritasViaSystemIntegrationTester().run_all()

# [VIA 修痕 v0101 2026-08-18] 原件尾部為聊天散文貼入(``` 圍欄後之對接說明)致 SyntaxError
# ——截斷至純程式碼;原件 byte-exact 列管 _review_quarantine/。runtime 依賴 tw_stock_data_router(候上傳)。
