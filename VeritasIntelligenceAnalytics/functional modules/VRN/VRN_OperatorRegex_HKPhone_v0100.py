import re

# 支援有無國碼（+852 或 852），並精準擷取本地 8 碼電話
# (?:\+?(?P<country_code>852)[- ]?)? : 可選的國碼 (支援 +852 或 852，可帶空格或連字號)
# (?P<local_number>[2-9]\d{7})       : 香港本地 8 碼 (2,3 固網，4-9 行動/其他)
HK_PHONE_REGEX = r'^(?:\+?(?P<country_code>852)[- ]?)?(?P<local_number>[2-9]\d{7})$'

def parse_hk_phone(phone_number):
    # 移除前後空白
    clean_phone = phone_number.strip()
    match = re.match(HK_PHONE_REGEX, clean_phone)

    if match:
        data = match.groupdict()
        local_num = data["local_number"]

        # 香港電話 2, 3 開頭為固網，4-9 為手機/個人號碼
        is_mobile = bool(re.match(r'^[4-9]', local_num))

        return {
            "is_valid": True,
            "type": "Mobile" if is_mobile else "Landline",
            "local_format": local_num,
            "global_format": f"+852-{local_num}"
        }

    return {
        "is_valid": False,
        "type": None,
        "local_format": None,
        "global_format": None
    }

# ==========================================
# 測試區塊
# ==========================================
if __name__ == "__main__":
    test_numbers = [
        "91234567",         # 本地手機號碼
        "21234567",         # 本地固網市話
        "+852-61234567",    # 帶國碼與連字號手機
        "852 31234567",     # 帶國碼 (無+) 與空格市話
        "0912345678",       # 台灣手機號碼 (預期失敗)
        "9123456"           # 長度不足 8 碼 (預期失敗)
    ]

    print(f"{'輸入號碼':<16} | {'狀態':<4} | {'類型':<10} | {'國際格式轉換'}")
    print("-" * 55)
    for num in test_numbers:
        result = parse_hk_phone(num)
        status = "✅" if result['is_valid'] else "❌"
        phone_type = result['type'] or "N/A"
        global_fmt = result['global_format'] or "N/A"

        print(f"{num:<16} | {status:<4} | {phone_type:<10} | {global_fmt}")
