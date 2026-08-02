"""使用者回饋擷取（離線、滑鼠優先、append-only）。

把「20 驚艷點 + 20 失望點」做成點選式標籤——使用者測試後點一下對應標籤即回報，
不用打字。全本機 append-only 寫入 feedback.jsonl，無網路無 AI；
summarize() 把回饋彙整成「最被讚的點 / 最被嫌的點」，直接驅動補強優先序。

設計：回饋標籤 = 驚艷/失望點本身，故收集到的回饋天然對齊改進清單。
"""
from __future__ import annotations

import json
import os
import time
from collections import Counter

# 20 驚艷點（正向標籤）
DELIGHT = {
    "D01": "滑鼠三回合完成客製，不用工程師",
    "D02": "一鍵自動偵測來源，不用填路徑/伺服器",
    "D03": "完整性給可信數字（未解釋遺漏=0，不假裝完整）",
    "D04": "歸類率自動爬升，系統自己挖關鍵字",
    "D05": "全景一眼看完數月來回 + 停滯預警",
    "D06": "斷網/無 AI 也能跑（末日場景）",
    "D07": "編號穩定，內容改了還是同碼好追蹤",
    "D08": "自動抓追蹤事項+負責人+期限",
    "D09": "利害關係人自動建檔，免複製貼上",
    "D10": "自動生成週報 PPT 草稿",
    "D11": "全本機資料不外傳，資安安心",
    "D12": "免費開源庫，無授權費",
    "D13": "開工先看綠/黃/紅燈健檢，壞了自己舉手",
    "D14": "同一引擎跨行業通吃（泛用）",
    "D15": "append-only 只增不減，歷史可回溯審計",
    "D16": "治亂碼自動修復（big5/mojibake）",
    "D17": "關鍵字/同義字核可制，嚴謹不亂合併",
    "D18": "備援鏈：一條路不通自動換下一條",
    "D19": "Notion 級 UI + PMBOK 十圖示導覽",
    "D20": "置信度分流：高信心自動鎖定，只有猶豫才請你點",
}

# 20 失望點（負向標籤）
DISAPPOINT = {
    "X01": "首次跑大量歷史很慢",
    "X02": ".mpp 原生需 Java 才能讀",
    "X03": "純圖傳真 OCR 辨識率不穩",
    "X04": "歸類率冷啟動初期偏低",
    "X05": "繁中斷詞有碎片（成度/載效）",
    "X06": "Outlook 連線需 Windows+已登入",
    "X07": "Gmail 仍要貼一次 App Password",
    "X08": "加密附件要人工輸密碼",
    "X09": "重型 CAD 庫安裝重",
    "X10": "大 Excel 空白列吃記憶體",
    "X11": "雲端連結權限牆抓不到",
    "X12": "沒有現成 BOM 管理，要自建",
    "X13": "pm4py 是 AGPL，商用要評估",
    "X14": "門外漢看到太多術語會怕",
    "X15": "失敗清單看不懂原因",
    "X16": "跨機器搬移設定麻煩",
    "X17": "沒有手機 App",
    "X18": "缺多人協作/權限分級",
    "X19": "客製深度有限（只動參數）",
    "X20": "報表美觀度/品牌套用不足",
}

# 每個失望點的補強方案（驅動 roadmap）
REMEDIES = {
    "X01": "增量同步 + 背景排程 + 進度條，首跑只抓近 N 月",
    "X02": "預設支援『另存 XML』免 Java；打包內嵌 JRE 或清楚提示",
    "X03": "Tesseract→RapidOCR→PaddleOCR 三引擎接力 + 人工複核旗",
    "X04": "桶從資料自舉 + 引導核可前幾個自動關鍵字，當場見效",
    "X05": "接 CKIP 繁中斷詞取代 bigram，候選更乾淨",
    "X06": "備援鏈：COM 不行改 libpff 讀 PST/OST",
    "X07": "引導畫面 + QR，一次貼上後自動連",
    "X08": "清楚提示請有權者輸入；絕不自動猜密碼（合規）",
    "X09": "獨立 venv 隔離；讀不到降級為『僅料件清單，無幾何』",
    "X10": "Polars 惰性掃描，載入前切除空列",
    "X11": "用授權憑證；遇牆標記+意圖快照，不規避",
    "X12": "networkx 重建 BOM 樹 + where-only 反查，並明說無現成庫",
    "X13": "輕量版用 NetworkX 自建 directly-follows graph 避 AGPL",
    "X14": "雙模式：簡單模式藏術語，進階模式才顯細節",
    "X15": "失敗原因白話化 + 建議動作（已在 selfcheck 雛形）",
    "X16": "config.json 一檔帶走，丟入即生效",
    "X17": "先做響應式 HTML 手機可看；原生 App 列 roadmap",
    "X18": "單機定位明說；協作/權限列為下一階段",
    "X19": "門外漢動參數、進階者可改 adapter，雙層客製",
    "X20": "Visual Lock 主題 + 可換 logo/字體，品牌套用",
}


def record_feedback(path: str, tag: str, note: str = "", user: str = "anon") -> dict:
    """append-only 寫入一筆回饋（離線）。tag 為 D## 或 X##。"""
    label = DELIGHT.get(tag) or DISAPPOINT.get(tag) or "(自訂)"
    kind = "delight" if tag in DELIGHT else ("disappoint" if tag in DISAPPOINT else "other")
    entry = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "tag": tag, "kind": kind,
             "label": label, "note": note, "user": user}
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def summarize(path: str) -> dict:
    """彙整回饋 → 最被讚/最被嫌的點 + 補強優先序。"""
    if not os.path.exists(path):
        return {"total": 0, "delight": [], "disappoint": [], "priority": []}
    counts = Counter()
    kinds = Counter()
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except Exception:
                continue
            counts[e["tag"]] += 1
            kinds[e["kind"]] += 1
    delight = [(t, DELIGHT[t], c) for t, c in counts.most_common() if t in DELIGHT]
    disappoint = [(t, DISAPPOINT[t], c) for t, c in counts.most_common() if t in DISAPPOINT]
    # 補強優先序：被嫌越多越優先，附補強方案
    priority = [{"tag": t, "issue": DISAPPOINT[t], "count": c, "remedy": REMEDIES.get(t, "")}
                for t, _, c in disappoint]
    return {"total": sum(counts.values()), "kinds": dict(kinds),
            "delight": delight, "disappoint": disappoint, "priority": priority}
