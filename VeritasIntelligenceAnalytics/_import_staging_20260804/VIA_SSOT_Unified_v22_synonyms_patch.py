# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                                                                          ║
# ║  VIA_SSOT_Unified v22 SYNONYM EXTENSION — APPEND-ONLY (功能只增不減)      ║
# ║                                                                          ║
# ║  貼到 VIA_SSOT_Unified.py 末尾即可生效                                    ║
# ║                                                                          ║
# ║  本 patch 補充財務報表會計科目同義字 + 重要比率 + 每股指標,               ║
# ║  共 55 個 canonical key, ~280 個同義詞(中英對照,大小寫不限)。           ║
# ║  來源:VeritasSynonymEngine + FinancialStatementData(使用者文件)。       ║
# ║                                                                          ║
# ║  資料結構:VIA_FIN_SYNONYMS_V22[canonical_key] = [synonym_list]          ║
# ║  公開 API:                                                              ║
# ║    via_fin_synonym(label_text)         -> canonical_key 或 ""           ║
# ║    via_fin_synonyms_all()              -> 整本字典                      ║
# ║    via_fin_category_of(canonical_key)  -> "IS" | "BS" | "CF" | ...      ║
# ║                                                                          ║
# ╚══════════════════════════════════════════════════════════════════════════╝

# ─── INCOME STATEMENT (10 項) ──────────────────────────────────────────────
VIA_FIN_SYNONYMS_IS_V22 = {
    "revenue": [
        "營業收入", "營業收入淨額", "營收", "Net Revenue", "Total Revenue",
        "Revenue", "Sales", "Net Sales", "銷售收入", "Top Line",
    ],
    "cost_of_revenue": [
        "營業成本", "銷貨成本", "Cost of Revenue", "COGS",
        "Cost of Goods Sold", "直接成本",
    ],
    "gross_profit": [
        "營業毛利", "營業毛利淨額", "毛利", "毛利額", "Gross Profit",
    ],
    "operating_expenses": [
        "營業費用", "營業費用合計", "營運費用", "Operating Expenses",
        "OpEx", "SG&A", "Selling, General and Administrative",
    ],
    "rd_expenses": [
        "研究發展費用", "研發支出", "研究開發費", "技術開發費用",
        "R&D Expenses", "R&D", "Research and Development",
    ],
    "operating_income": [
        "營業利益", "營業利益淨額", "營業淨利", "營業獲利", "營運利益",
        "Operating Income", "Operating Profit", "EBIT",
    ],
    "non_operating_income": [
        "營業外收入", "業外收入", "投資收益", "處分利益", "Other Income",
        "Non-operating Income", "業外收支",
    ],
    "pretax_income": [
        "稅前淨利", "稅前利益", "稅前純益", "稅前盈餘", "稅前獲利",
        "Pretax Income", "Income Before Tax", "EBT", "Earnings Before Tax",
    ],
    "tax_expense": [
        "所得稅", "所得稅費用", "稅費", "稅負", "Tax Expense", "Income Tax",
    ],
    "net_income": [
        "本期淨利", "本期純益", "稅後純益", "稅後淨利", "稅後盈餘",
        "純益", "歸屬母公司純益", "Net Income", "Net Profit", "Net Earnings",
    ],
}

# ─── BALANCE SHEET (14 項) ─────────────────────────────────────────────────
VIA_FIN_SYNONYMS_BS_V22 = {
    "cash": [
        "現金及約當現金", "現金", "貨幣資金", "銀行存款",
        "Cash", "Cash & Cash Equivalents", "Cash and Cash Equivalents",
    ],
    "accounts_receivable": [
        "應收帳款", "應收款項", "貿易應收款", "客戶應收款",
        "Accounts Receivable", "A/R", "Trade Receivables",
    ],
    "inventory": [
        "存貨", "庫存", "商品存貨", "製成品", "在製品",
        "Inventory", "Inventories", "Stock",
    ],
    "current_assets": [
        "流動資產合計", "流動資產", "短期資產", "流動資產總額",
        "一年內資產", "Current Assets", "Total Current Assets",
    ],
    "ppe": [
        "不動產廠房設備", "不動產、廠房及設備", "固定資產", "廠房設備",
        "Property Plant and Equipment", "Property, Plant & Equipment",
        "PPE", "PP&E", "Fixed Assets",
    ],
    "total_assets": [
        "資產總計", "資產總額", "資產合計", "總資產", "全部資產",
        "Total Assets",
    ],
    "accounts_payable": [
        "應付帳款", "應付款項", "貿易應付款", "供應商應付款",
        "Accounts Payable", "A/P", "Trade Payables",
    ],
    "short_term_debt": [
        "短期借款", "短期負債", "流動借款", "一年內到期負債",
        "Short-term Debt", "Short-term Borrowings", "Current Debt",
    ],
    "current_liabilities": [
        "流動負債合計", "流動負債", "流動負債總額", "一年內負債",
        "Current Liabilities", "Total Current Liabilities",
    ],
    "long_term_debt": [
        "長期借款", "長期負債", "非流動借款", "長期融資",
        "Long-term Debt", "Long-term Borrowings", "Non-current Debt",
    ],
    "total_liabilities": [
        "負債總計", "負債總額", "負債合計", "總負債", "全部負債",
        "Total Liabilities",
    ],
    "share_capital": [
        "股本", "實收資本", "普通股股本", "股份資本",
        "Share Capital", "Common Stock", "Common Equity", "Paid-in Capital",
    ],
    "retained_earnings": [
        "保留盈餘", "累積盈餘", "未分配盈餘", "累積未分配盈餘",
        "Retained Earnings", "Accumulated Earnings",
    ],
    "shareholders_equity": [
        "股東權益", "權益總計", "權益合計", "股東權益總額", "淨值",
        "Shareholders Equity", "Shareholders' Equity", "Stockholders Equity",
        "Total Equity", "Book Value",
    ],
}

# ─── CASH FLOW (8 項) ──────────────────────────────────────────────────────
VIA_FIN_SYNONYMS_CF_V22 = {
    "operating_cashflow": [
        "營業活動現金流", "營業活動之淨現金流入(流出)",
        "營業活動之現金流量", "營業活動之淨現金流入", "營運現金流",
        "經營活動現金流", "Operating Cash Flow", "Cash Flow from Operations",
        "CFO", "OCF",
    ],
    "investing_cashflow": [
        "投資活動現金流", "投資活動之淨現金流入(流出)",
        "投資活動之現金流量", "投資現金流",
        "Investing Cash Flow", "Cash Flow from Investing", "CFI", "ICF",
    ],
    "financing_cashflow": [
        "籌資活動現金流", "籌資活動之淨現金流入(流出)",
        "融資活動現金流", "資金活動現金流",
        "Financing Cash Flow", "Cash Flow from Financing", "CFF",
    ],
    "depreciation": [
        "折舊費用", "折舊", "折舊與攤提", "固定資產折舊",
        "Depreciation", "D&A",
    ],
    "amortization": [
        "攤提費用", "攤銷費用", "無形資產攤提",
        "Amortization",
    ],
    "capex": [
        "資本支出", "資本性支出", "設備投資", "固定資產投資",
        "取得不動產、廠房及設備",
        "Capital Expenditures", "CapEx", "Capital Expenditure",
    ],
    "free_cashflow": [
        "自由現金流", "自由現金流量",
        "Free Cash Flow", "FCF",
    ],
    "dividends_paid": [
        "發放現金股利", "現金股利支付", "股息發放", "股利分配",
        "Dividends Paid", "Cash Dividends",
    ],
}

# ─── FINANCIAL RATIOS (12 項) ──────────────────────────────────────────────
VIA_FIN_SYNONYMS_RATIO_V22 = {
    "roe": [
        "股東權益報酬率", "權益報酬率", "淨值報酬率", "股東權益收益率",
        "Return on Equity", "ROE",
    ],
    "roa": [
        "資產報酬率", "總資產報酬率", "資產收益率",
        "Return on Assets", "ROA",
    ],
    "gross_margin": [
        "毛利率", "營業毛利率", "毛利潤率",
        "Gross Margin", "Gross Profit Margin",
    ],
    "operating_margin": [
        "營業利益率", "營益率", "營業淨利率", "營運利益率",
        "Operating Margin", "EBIT Margin",
    ],
    "net_margin": [
        "淨利率", "純益率", "稅後淨利率",
        "Net Margin", "Net Profit Margin",
    ],
    "current_ratio": [
        "流動比率", "流動比", "短期償債能力比率",
        "Current Ratio",
    ],
    "quick_ratio": [
        "速動比率", "速動比", "酸性測試比率",
        "Quick Ratio", "Acid Test Ratio", "Acid-Test Ratio",
    ],
    "debt_ratio": [
        "負債比率", "債務比率", "資產負債率", "負債比",
        "Debt Ratio", "Debt to Assets",
    ],
    "debt_to_equity": [
        "負債權益比", "負債對權益比率",
        "Debt-to-Equity", "D/E Ratio", "Debt to Equity",
    ],
    "pe_ratio": [
        "本益比", "股價盈餘比",
        "PE Ratio", "P/E Ratio", "PER", "Price-to-Earnings",
        "Price to Earnings", "Trailing PE",
    ],
    "pb_ratio": [
        "股價淨值比", "市價淨值比",
        "PB Ratio", "P/B Ratio", "PBR", "Price-to-Book", "Price to Book",
    ],
    "ps_ratio": [
        "股價營收比", "市價營收比",
        "PS Ratio", "P/S Ratio", "PSR", "Price-to-Sales", "Price to Sales",
    ],
}

# ─── PER-SHARE METRICS (11 項) ─────────────────────────────────────────────
VIA_FIN_SYNONYMS_PER_SHARE_V22 = {
    "basic_eps": [
        "基本每股盈餘", "每股盈餘", "每股稅後盈餘",
        "Basic EPS", "基本EPS", "Basic Earnings Per Share",
    ],
    "diluted_eps": [
        "稀釋每股盈餘", "稀釋後EPS", "完全稀釋每股盈餘",
        "Diluted EPS", "Diluted Earnings Per Share",
    ],
    "book_value_per_share": [
        "每股淨值", "每股帳面價值", "每股股東權益",
        "BVPS", "Book Value Per Share",
    ],
    "dividend_per_share": [
        "每股現金股利", "每股配息", "現金股息", "股利",
        "DPS", "Dividend Per Share", "Dividends",
    ],
    "cashflow_per_share": [
        "每股現金流", "每股營業現金流",
        "CFPS", "Cash Flow Per Share",
    ],
    "sales_per_share": [
        "每股營收",
        "SPS", "Sales Per Share", "Revenue Per Share",
    ],
    "shares_outstanding": [
        "普通股流通股數", "普通股股數", "流通在外股數", "發行股數",
        "市場流通股", "已發行股數",
        "Shares Outstanding", "Common Shares Outstanding",
    ],
    "weighted_avg_shares": [
        "加權平均股數", "加權平均流通股數", "基本股數",
        "Weighted Average Shares", "Weighted Average Shares Outstanding",
    ],
    "diluted_shares": [
        "完全稀釋後股數", "稀釋後股數", "稀釋後流通股數", "完全稀釋股本",
        "Diluted Shares", "Fully Diluted Shares", "Diluted Average Shares",
    ],
    "dividend_yield": [
        "股利殖利率", "現金殖利率", "殖利率", "股息收益率",
        "Yield", "Dividend Yield",
    ],
    "payout_ratio": [
        "配息率", "股利發放率", "配息比例", "股利支付率",
        "Payout Ratio",
    ],
}

# ─── 整合所有 ──────────────────────────────────────────────────────────────
VIA_FIN_SYNONYMS_V22 = {}
VIA_FIN_SYNONYMS_V22.update(VIA_FIN_SYNONYMS_IS_V22)
VIA_FIN_SYNONYMS_V22.update(VIA_FIN_SYNONYMS_BS_V22)
VIA_FIN_SYNONYMS_V22.update(VIA_FIN_SYNONYMS_CF_V22)
VIA_FIN_SYNONYMS_V22.update(VIA_FIN_SYNONYMS_RATIO_V22)
VIA_FIN_SYNONYMS_V22.update(VIA_FIN_SYNONYMS_PER_SHARE_V22)

# Category mapping
VIA_FIN_CATEGORY_MAP_V22 = {}
for k in VIA_FIN_SYNONYMS_IS_V22:        VIA_FIN_CATEGORY_MAP_V22[k] = "IS"
for k in VIA_FIN_SYNONYMS_BS_V22:        VIA_FIN_CATEGORY_MAP_V22[k] = "BS"
for k in VIA_FIN_SYNONYMS_CF_V22:        VIA_FIN_CATEGORY_MAP_V22[k] = "CF"
for k in VIA_FIN_SYNONYMS_RATIO_V22:     VIA_FIN_CATEGORY_MAP_V22[k] = "RATIO"
for k in VIA_FIN_SYNONYMS_PER_SHARE_V22: VIA_FIN_CATEGORY_MAP_V22[k] = "PER_SHARE"


# ─── 反向索引(預編譯,加速 lookup) ────────────────────────────────────
_VIA_FIN_REVERSE_V22 = {}
for canon, alts in VIA_FIN_SYNONYMS_V22.items():
    for a in alts:
        _VIA_FIN_REVERSE_V22[a.lower()] = canon


# ─── 公開 API ──────────────────────────────────────────────────────────────
def via_fin_synonym(label_text: str) -> str:
    """根據 label_text(任何同義字)回傳 canonical_key。
    比對策略:
      1. 完全相等(大小寫不限) — 最精確
      2. label_text 包含 alt 或 alt 包含 label_text — 寬鬆 fallback
    找不到回 ""。"""
    if not label_text:
        return ""
    s = str(label_text).strip().lower()
    if not s:
        return ""
    # Exact match
    if s in _VIA_FIN_REVERSE_V22:
        return _VIA_FIN_REVERSE_V22[s]
    # Substring containment
    for alt_lower, canon in _VIA_FIN_REVERSE_V22.items():
        if alt_lower in s or s in alt_lower:
            return canon
    return ""


def via_fin_synonyms_all() -> dict:
    """回傳整本同義字字典(canonical_key → [synonym, ...])。"""
    return dict(VIA_FIN_SYNONYMS_V22)


def via_fin_category_of(canonical_key: str) -> str:
    """根據 canonical_key 回傳 category(IS / BS / CF / RATIO / PER_SHARE)。
    找不到回 'UNKNOWN'。"""
    return VIA_FIN_CATEGORY_MAP_V22.get(canonical_key, "UNKNOWN")


def via_fin_synonyms_count() -> dict:
    """回傳統計資訊。"""
    return {
        "canonical_keys": len(VIA_FIN_SYNONYMS_V22),
        "total_synonyms": sum(len(v) for v in VIA_FIN_SYNONYMS_V22.values()),
        "by_category": {
            "IS":        len(VIA_FIN_SYNONYMS_IS_V22),
            "BS":        len(VIA_FIN_SYNONYMS_BS_V22),
            "CF":        len(VIA_FIN_SYNONYMS_CF_V22),
            "RATIO":     len(VIA_FIN_SYNONYMS_RATIO_V22),
            "PER_SHARE": len(VIA_FIN_SYNONYMS_PER_SHARE_V22),
        },
    }


# ─── self-test(import 此模組時不執行,只在直接 run 時跑) ────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("VIA SSOT v22 Synonym Extension — Self-Test")
    print("=" * 60)
    stats = via_fin_synonyms_count()
    print(f"\n[STATS] canonical_keys = {stats['canonical_keys']}")
    print(f"[STATS] total_synonyms = {stats['total_synonyms']}")
    for cat, n in stats['by_category'].items():
        print(f"  {cat:>10s} : {n}")

    test_cases = [
        ("營業收入",             "revenue"),
        ("Revenue",              "revenue"),
        ("NET REVENUE",          "revenue"),
        ("基本每股盈餘",         "basic_eps"),
        ("Basic EPS",            "basic_eps"),
        ("ROE",                  "roe"),
        ("股東權益報酬率",       "roe"),
        ("營業活動之現金流量",   "operating_cashflow"),
        ("Operating Cash Flow",  "operating_cashflow"),
        ("負債權益比",           "debt_to_equity"),
        ("資產總計",             "total_assets"),
        ("Total Assets",         "total_assets"),
        ("XYZ_UNKNOWN_LABEL",    ""),
    ]
    print("\n[LOOKUP TESTS]")
    n_ok = 0
    for label, expected in test_cases:
        result = via_fin_synonym(label)
        cat = via_fin_category_of(result) if result else "-"
        ok = (result == expected)
        if ok: n_ok += 1
        flag = "OK" if ok else "FAIL"
        print(f"  [{flag:>4s}] {label:30s} → {result:25s} ({cat})  expected={expected}")
    print(f"\n[RESULT] {n_ok}/{len(test_cases)} lookup tests passed")
