import re

# ==========================================
# 台北市話 國內/國際 整合版 Regex
# ==========================================
# (?P<country_code>0|\+886) : 匹配國內開頭 0 或 國際碼 +886
# -?                        : 可選連字號
# (?P<area_code>2)          : 台北區碼 2
# -?                        : 可選連字號
# (?P<num1>\d{4})           : 號碼前 4 碼
# -?                        : 可選連字號
# (?P<num2>\d{4})           : 號碼後 4 碼
# (?:\s*(?:#|ext\.?)\s*(?P<ext>\d+))? : 可選分機 (支援 # 或 ext)
UNIFIED_TAIPEI_PHONE_REGEX = r'^(?P<country_code>0|\+886)-?(?P<area_code>2)-?(?P<num1>\d{4})-?(?P<num2>\d{4})(?:\s*(?:#|ext\.?)\s*(?P<ext>\d+))?$'

def parse_taipei_phone(phone):
    # 移除前後空白
    clean_phone = phone.strip()

    # 使用 re.IGNORECASE 讓 ext, EXT, Ext 都能被識別
    match = re.match(UNIFIED_TAIPEI_PHONE_REGEX, clean_phone, re.IGNORECASE)

    if match:
        data = match.groupdict()

        # 組合基礎號碼
        local_base = f"02-{data['num1']}-{data['num2']}"
        global_base = f"+886-2-{data['num1']}-{data['num2']}"

        # 處理分機 (如果有填寫的話)
        ext_str = f" #{data['ext']}" if data['ext'] else ""

        return {
            "is_valid": True,
            "local_format": f"{local_base}{ext_str}",
            "global_format": f"{global_base}{ext_str}",
            "extension": data['ext']
        }

    return {
        "is_valid": False,
        "local_format": None,
        "global_format": None,
        "extension": None
    }

# ==========================================
# 測試區塊
# ==========================================
if __name__ == "__main__":
    test_numbers = [
        # --- 國內格式測試 ---
        "02-2771-2171",          # 標準國內格式
        "0227712171",            # 無連字號
        "02-2771-2171 #551",     # 帶分機 (#)
        "02-2771-2171 Ext. 12",  # 帶分機 (Ext.)

        # --- 國際格式測試 ---
        "+886-2-2771-2171",      # 標準國際格式
        "+886227712171",         # 無連字號國際格式
        "+886-2-2771-2171#88",   # 國際格式帶分機 (無空格)

        # --- 錯誤格式測試 (預期失敗) ---
        "03-571-2121",           # 新竹區碼
        "+886-3-571-2121",       # 國際碼 + 新竹區碼
        "0912-345-678"           # 行動電話
    ]

    print(f"{'輸入號碼':<22} | {'狀態':<4} | {'國內格式轉換':<20} | {'國際格式轉換'}")
    print("-" * 75)
    for num in test_numbers:
        result = parse_taipei_phone(num)
        status = "✅" if result['is_valid'] else "❌"
        local = result['local_format'] or "N/A"
        global_fmt = result['global_format'] or "N/A"

        print(f"{num:<22} | {status:<4} | {local:<20} | {global_fmt}")
