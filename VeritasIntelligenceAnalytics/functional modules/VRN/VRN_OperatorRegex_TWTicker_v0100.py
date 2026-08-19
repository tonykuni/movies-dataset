import re

# ==========================================
# 台灣股票代碼 終極整合版 Regex
# ==========================================
# ^\s*                       : 允許開頭有空白
# (?P<code_num>\d{4,5})      : 擷取 4-5 碼的核心數字代碼
# \s*                        : 允許數字與後綴之間有空白
# (?i:\.TWO|\.TW|TT)?        : 可選的後綴 (忽略大小寫，支援 .TWO, .TW, TT)
# \s*$                       : 允許結尾有空白
TW_TICKER_UNIFIED_PATTERN = r'^\s*(?P<code_num>\d{4,5})\s*(?i:\.TWO|\.TW|TT)?\s*$'

# 上櫃/興櫃代碼簡易判斷區段 (3, 4, 5, 6, 8 開頭)
OTC_PREFIXES = ('3', '4', '5', '6', '8')

def parse_taiwan_ticker(input_ticker):
    # 轉為字串並移除兩側多餘空白
    clean_input = str(input_ticker).strip()
    match = re.match(TW_TICKER_UNIFIED_PATTERN, clean_input)

    if match:
        # 1. 取得乾淨的純數字代碼
        code_num = match.group("code_num")

        # 2. 判斷所屬市場 (上市/上櫃) 以決定 Yahoo Finance 的後綴
        # 邏輯：5 碼 (如 0050) 或 開頭不在 OTC_PREFIXES 內的，視為上市 (.TW)
        if len(code_num) == 5 or not code_num.startswith(OTC_PREFIXES):
            market_type = "上市 (TWSE)"
            yf_suffix = ".TW"
        else:
            market_type = "上櫃 (OTC)"
            yf_suffix = ".TWO"

        # 3. 組裝標準格式
        yfinance_format = f"{code_num}{yf_suffix}"
        bloomberg_format = f"{code_num} TT"

        # 4. 偵測使用者是否輸入了「錯誤的後綴」或「非標準格式」
        # 把輸入轉大寫來比對，如果輸入包含字母，但與我們計算出的標準格式不同，代表有被修正
        input_upper = clean_input.upper()
        has_been_corrected = False
        if any(c.isalpha() for c in input_upper): # 輸入帶有英文字母
            if input_upper != yfinance_format and input_upper != bloomberg_format:
                has_been_corrected = True

        return {
            "is_valid": True,
            "original_input": input_ticker,
            "core_ticker": code_num,
            "market_type": market_type,
            "yfinance_format": yfinance_format,
            "bloomberg_format": bloomberg_format,
            "was_corrected": has_been_corrected
        }

    # 若格式完全不符
    return {
        "is_valid": False,
        "original_input": input_ticker,
        "core_ticker": None,
        "market_type": None,
        "yfinance_format": None,
        "bloomberg_format": None,
        "was_corrected": False
    }

# ==========================================
# 測試區塊
# ==========================================
if __name__ == "__main__":
    test_cases = [
        "2330",          # 純數字上市
        "5347",          # 純數字上櫃
        "0050",          # ETF 0 開頭
        "2317.TW",       # 標準 Yahoo 上市格式
        "2317.TWO",      # 錯誤的 Yahoo 格式 (鴻海是上市，預期被校正)
        "5347.tw",       # 小寫且錯誤的 Yahoo 格式 (世界是上櫃，預期被校正)
        " 2330TT ",      # 彭博格式 (無空格且前後帶有髒空白)
        "2330 tt",       # 彭博格式 (小寫)
        "AAPL"           # 非法輸入 (非台灣代碼)
    ]

    print(f"{'輸入字串':<12} | {'核心碼':<6} | {'Yahoo 格式':<12} | {'Bloomberg 格式':<14} | {'自動校正'}")
    print("-" * 65)
    for case in test_cases:
        res = parse_taiwan_ticker(case)
        if res["is_valid"]:
            core = res["core_ticker"]
            yf = res["yfinance_format"]
            bbg = res["bloomberg_format"]
            corrected = "⚠️ 校正" if res["was_corrected"] else "✅ 標準"
            print(f"{case:<12} | {core:<6} | {yf:<12} | {bbg:<14} | {corrected}")
        else:
            print(f"{case:<12} | ❌ 無效的台灣股票代碼")
