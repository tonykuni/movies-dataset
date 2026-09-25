import importlib.util
import unittest
from pathlib import Path


ADAPTER_PATH = Path(__file__).resolve().parents[1] / "VIA_TW_Official_Data_Adapter.py"
SPEC = importlib.util.spec_from_file_location("official_adapter", ADAPTER_PATH)
ADAPTER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(ADAPTER)


class OfficialAdapterTests(unittest.TestCase):
    def test_normalize_gregorian_and_roc_dates(self):
        self.assertEqual(ADAPTER.def_normalize_date("20260828"), "2026-08-28")
        self.assertEqual(ADAPTER.def_normalize_date("115/08/28"), "2026-08-28")

    def test_tdcc_csv_maps_levels_and_filters_tickers(self):
        content = (
            "資料日期,證券代號,持股分級,人數,股數,占集保庫存數比例%\n"
            "20260828,2330,1,10,2000,0.01\n"
            "20260828,2330,17,100,1000000,100.00\n"
            "20260828,2317,1,20,3000,0.02\n"
        ).encode("utf-8-sig")
        rows = ADAPTER.def_parse_tdcc_holding_csv(content, {"2330"})
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["HoldingSharesLevel"], "1-999")
        self.assertEqual(rows[1]["HoldingSharesLevel"], "合計")
        self.assertEqual(rows[0]["source_provider"], "TDCC")

    def test_twse_block_csv_maps_canonical_schema(self):
        content = (
            "115年08月28日 鉅額交易日成交資訊-單一證券\n"
            "證券代號,證券名稱,交易別,成交價,成交股數,成交金額\n"
            "2330,台積電,配對交易,581.50,347000,201780500\n"
            "2317,鴻海,逐筆交易,200.00,100000,20000000\n"
        ).encode("utf-8-sig")
        rows = ADAPTER.def_parse_twse_block_csv(content, "2026-08-28", {"2330"})
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["volume"], 347000)
        self.assertEqual(rows[0]["source_provider"], "TWSE")

    def test_tpex_block_rows_map_roc_date(self):
        source = [{
            "Date": "1150828",
            "Code": "8069",
            "TransactionType": "逐筆交易",
            "TradePrice": "125.50",
            "NumberOfSharesTraded": "1,000,000",
            "TradeValue": "125,500,000",
        }]
        rows = ADAPTER.def_parse_tpex_block_rows(source, {"8069"})
        self.assertEqual(rows[0]["date"], "2026-08-28")
        self.assertEqual(rows[0]["trading_money"], 125500000.0)

    def test_tpex_price_and_margin_mapping(self):
        price_rows = ADAPTER.def_parse_price_rows([{
            "Date": "1150828",
            "SecuritiesCompanyCode": "8069",
            "Open": "120.0", "High": "128.0", "Low": "119.0", "Close": "125.0",
            "Change": "+5.0", "TradingShares": "1,200,000",
            "TransactionAmount": "150,000,000", "TransactionNumber": "900",
        }], "TPEX", {"8069"})
        self.assertEqual(price_rows[0]["Trading_Volume"], 1200000)
        self.assertEqual(price_rows[0]["close"], 125.0)

        margin_rows = ADAPTER.def_parse_margin_rows([{
            "Date": "1150828", "SecuritiesCompanyCode": "8069",
            "MarginPurchaseBalancePreviousDay": "100", "MarginPurchase": "30",
            "MarginSales": "20", "CashRedemption": "1", "MarginPurchaseBalance": "109",
            "MarginPurchaseQuota": "1000", "ShortSaleBalancePreviousDay": "20",
            "ShortSale": "8", "ShortConvering": "3", "StockRedemption": "1",
            "ShortSaleBalance": "24", "ShortSaleQuota": "500", "Offsetting": "2",
        }], "TPEX", {"8069"})
        self.assertEqual(margin_rows[0]["MarginPurchaseTodayBalance"], 109)
        self.assertEqual(margin_rows[0]["ShortSaleTodayBalance"], 24)


if __name__ == "__main__":
    unittest.main(verbosity=2)
