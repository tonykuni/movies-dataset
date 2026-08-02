# PMIS-Lite · 個人工作 SSOT 引擎

把「自己有權限的郵件 / Excel / 專案資料」自動**擷取 → 治亂碼 → 編號 → 分類 → 進度比對 → 簡報草稿**，
全程**本機處理、不外傳**。降低文書整理時間，把時間留給思考與決策。

> 萬用 / 可分享：朋友只要改 `config.json` 一個檔，套上自己的資料就能跑。引擎一份，各公司各自用。

---

## ⚠ 合規前提（務必先讀）

本工具僅讀取**您自己有權限**的資料，於**本機**處理、**不外傳**、**不繞過稽核**。
使用前請確認符合貴公司**可接受使用規範 (AUP)**、個資法與保密義務。
（程式每次啟動會在畫面印出此提醒。）

- 只處理你自己帳號 / 自己有權限的資料
- 不建立同事的私人檔案，只記錄工作事實（負責人、進度、風險、日期）
- 產出是**草稿**，你看過、認可才對外

---

## 快速開始

```bash
pip install pandas openpyxl pyarrow chardet python-pptx
python make_sample_data.py     # 產生測試資料（可略過，用你自己的）
python run_demo.py             # 跑完整流程
```

輸出在 `ssot_store/`：
- `ssot.parquet` — SSOT 主檔（增量、append-only）
- `weekly_summary_YYYYMMDD.md` — Markdown 摘要（可貼進 Notion）
- `weekly_deck_YYYYMMDD.pptx` — 簡報草稿
- `term_candidates.json` — 術語同義字候選（待你核可）

---

## 你只需要改 `config.json`

| 區塊 | 改什麼 |
|------|--------|
| `numbering.prefix / domain` | 編號前綴。換職位 / 換領域只改這兩段 |
| `classification` | 分類維度與關鍵字（產品 / 主題 / 狀態…），資料驅動，可自由增減 |
| `terms.seed` | 已知的簡寫 / 同義字種子表（PSU→電源供應器…） |
| `mining` | 同義字探勘參數；`auto_merge` 預設 false（系統不自動合併） |
| `sources` | 啟用哪些來源；先給 Excel/CSV，Outlook / Gmail 之後接上 |
| `output.pptx_template` | 指定你自己的 pptx 範本，草稿就會沿用你的版面字體 |

---

## 架構（萬用 = adapter 模式）

```
config.json（只動這個）
   │
擷取層 adapters：Excel/CSV │ Outlook 桌面 │ Gmail │ MS Project … → 統一 SSOT 格式
   │
SSOT 層：治亂碼 + 自動編號(穩定身分) + 術語正規化 + 分類
   │
追蹤層：增量入庫(Parquet) + 與上一版比對(新增/變更/消失) + 風險偵測
   │
產出層：Markdown(Notion) + pptx 草稿
```

核心引擎只認得統一格式。新增來源只要寫一個 adapter 回傳統一 Record，引擎一行都不用改。

---

## 兩個關鍵設計（為什麼這樣做）

**1. 穩定編號 vs 變動偵測分離**
編號 (uid) 來自「標題+負責人」這種**身分**資訊 → 同一件事內容變了，編號不變。
另算一個**變動指紋**（含狀態+內文）→ 用來判斷「這件事這週變了沒」。
所以你週五看到的是「**哪件事從逾期變已結、哪件新增、哪件沒人回**」，而不是一堆看不出差異的清單。

**2. 同義字：提議，不自動合併（append-only）**
行內人寫信滿是簡寫（PSU / LLC / VFD），對系統與新人都是壓力。
探勘層用三種訊號找候選：**括號標註**（最準）、**共現**（弱證據+專一性懲罰）、**字串近似**。
但**絕不自動合併** —— 每個候選附信心分數與證據，進佇列等你核可。
內建停用清單（RD/PM/QA… 這類單位角色縮寫）避免把組織縮寫誤當產品同義詞。
> 預設保守：寧可少併，也不要錯併污染 SSOT。

---

## 接真實郵件（之後）

- **Outlook 桌面**：Windows 裝 `pywin32`，透過你已登入的 Outlook 讀取（權限與你本人一致）。在 `config.json` 把 `outlook_desktop` 的 `enabled` 設 true。
- **個人 Gmail**：Gmail API + OAuth `readonly` 授權給本機程式。

兩者都只是多一個 adapter，核心流程不變。

---

## 設定產生器（config_builder.html）

不想手改 JSON？用 `config_builder.html` —— 手機可開、**全程下拉/勾選、免打字**：
選產業 → 選編號 → 勾來源 → 勾分類 → 下載 `config.json`。
帶著客戶點一遍就完成客製；**引擎本身不改**，客製只發生在這份設定。
產業預設已內建分類關鍵字與簡寫對照（電源/機構/半導體/軟體/通用），PLM 廠牌自動帶欄位對應（Windchill/Teamcenter/Agile/SAP）。
