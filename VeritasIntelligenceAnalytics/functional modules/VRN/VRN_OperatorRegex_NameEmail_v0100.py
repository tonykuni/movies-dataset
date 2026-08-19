import re

# ==========================================
# 1. 姓名驗證 Regex 優化
# ==========================================
# 加入了 ·(·) 與 ．(．)，並將長度放寬至 15
CHINESE_NAME_REGEX = r'^[一-龥・·．]{2,15}$'

# 確保字串中至少包含一個英文字母 (?!^[ .*'-]+$)，避免全是符號或空格
ENGLISH_NAME_REGEX = r"^(?!^[\s,.'-]+$)[a-zA-Z\s,.'-]{2,50}$"

def validate_name(name):
    if re.match(CHINESE_NAME_REGEX, name):
        return "有效的中文姓名"
    elif re.match(ENGLISH_NAME_REGEX, name):
        return "有效的英文姓名"
    else:
        return "無效的姓名格式"


# ==========================================
# 2. Email 解析 Regex 優化
# ==========================================
# name 區塊加入了 0-9，網域部分改成 (\.[a-zA-Z]{2,})+ 確保像是 .com 或 .com.tw 的格式正確
EMAIL_PARSE_REGEX = r'^(?P<name>[a-zA-Z0-9.-]+)@(?P<company>[a-zA-Z0-9-]+)(?P<tld>(\.[a-zA-Z]{2,})+)$'

def parse_corporate_email(email):
    match = re.match(EMAIL_PARSE_REGEX, email)
    if match:
        data = match.groupdict()
        return {
            "is_valid": True,
            "english_name": data["name"],
            "company_name": data["company"],
            "domain_tld": data["tld"] # 額外抓出 .com.tw
        }
    else:
        return {"is_valid": False, "english_name": None, "company_name": None, "domain_tld": None}

# ==========================================
# 測試區塊
# ==========================================
if __name__ == "__main__":
    print("--- 姓名測試 ---")
    print(validate_name("瓦歷斯·諾幹"))      # 有效的中文姓名 (含 ·)
    print(validate_name("O'Connor"))          # 有效的英文姓名
    print(validate_name("   "))               # 無效的姓名格式 (防呆成功)

    print("\n--- Email 測試 ---")
    test_emails = ["tonyhuang@yuanta.com", "tony.huang123@yuanta.com.tw"]
    for email in test_emails:
        result = parse_corporate_email(email)
        print(f"[{email}]")
        print(f"  符合格式: {result['is_valid']}")
        print(f"  英文姓名: {result['english_name']}")
        print(f"  公司名稱: {result['company_name']}")
        print(f"  網域後綴: {result['domain_tld']}\n")
