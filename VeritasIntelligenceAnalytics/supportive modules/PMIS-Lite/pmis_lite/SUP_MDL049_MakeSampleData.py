"""產生測試資料：模擬跨單位回信 + Excel 工作底稿。
故意埋入：簡寫(PSU/LLC/EVT)、同義詞(電源/電供)、括號標註、big5 編碼 CSV。
"""
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
import os
import pandas as pd
from openpyxl import Workbook

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_data")
os.makedirs(HERE, exist_ok=True)

# 1) Excel 工作底稿（多欄位，含負責人/狀態/日期）
wb = Workbook()
ws = wb.active
ws.title = "本週進度"
ws.append(["工作項目", "產品線", "負責人", "對口單位", "狀態", "更新日期", "進度說明"])
rows = [
    ["PSU 新案電路設計審查", "電源供應器", "Alex", "RD;PM", "進行中", "2026-06-25", "LLC 拓樸初版完成，待 layout"],
    ["變頻器 EVT 測試排程", "變頻器", "Ben", "QA;PE", "待辦", "2026-06-26", "EVT 樣品下週到，需先排測試櫃"],
    ["散熱模組風扇噪音客訴", "散熱模組", "Cathy", "QA;客戶", "逾期", "2026-06-20", "RMA 件分析中，8D 報告延遲"],
    ["電供 DVT 驗證結果彙整", "電源供應器", "Alex", "RD", "進行中", "2026-06-27", "DVT 三輪測試，效率達標"],
    ["變頻器量產出貨確認", "變頻器", "Ben", "PM;業務", "已結", "2026-06-24", "MP 首批已出貨"],
]
for r in rows:
    ws.append(r)
wb.save(os.path.join(HERE, "weekly_worksheet.xlsx"))

# 2) 模擬郵件匯出 CSV（utf-8-sig）—— 跨單位回信、隨意簡寫
mail = pd.DataFrame([
    {"日期": "2026-06-27 16:40", "寄件人": "RD_Lin", "收件人": "PM_Wang;QA_Chen",
     "主旨": "Re: PSU 新案 LLC 效率問題",
     "內容": "諧振轉換器(LLC)在輕載效率偏低，建議下週 EVT 一起看，電源這案要追。"},
    {"日期": "2026-06-27 18:05", "寄件人": "QA_Chen", "收件人": "RD_Lin",
     "主旨": "Re: 散熱模組 RMA",
     "內容": "客訴風扇噪音，RMA 件已收，8D 我這邊在做，散熱這邊先別出貨。"},
    {"日期": "2026-06-28 09:12", "寄件人": "PM_Wang", "收件人": "ALL",
     "主旨": "本週 VFD 量產進度",
     "內容": "變頻器(VFD) MP 首批 OK，下批 PVT 還沒排，請 PE 回覆。"},
])
mail.to_csv(os.path.join(HERE, "mailbox_export.csv"), index=False, encoding="utf-8-sig")

# 3) 一個 big5 編碼的 CSV，測治亂碼
big5 = pd.DataFrame([
    {"項目": "電供老化測試", "狀態": "進行中", "說明": "PSU burn-in 48 小時，溫升正常"},
])
big5.to_csv(os.path.join(HERE, "legacy_big5.csv"), index=False, encoding="cp950")

print("sample data written to", HERE)
for n in sorted(os.listdir(HERE)):
    print("  -", n)
