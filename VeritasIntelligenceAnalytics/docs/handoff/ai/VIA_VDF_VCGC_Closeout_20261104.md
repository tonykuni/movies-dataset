# VDF / VCGC 收尾 · 2026-11-04

> 操作員 2026-11-04:「開始 VDF / VCGC CLOSE OUT」「繼續完成 VDF / VCGC CLOSE OUT」。
> 依收尾規格 `VIA_Closeout_Spec_20261103.md` §8 第 3、4 項。只增:每個修正都是新版號檔,前版一字不改;四系統各自負責,VRN 的檔不動。
> 環境:雲端容器(Linux · Python 3.13)。為了能真跑 VDF 的自測,容器裡補裝了 duckdb 1.5.6 · pyarrow 26 · polars 2.1 · yfinance 1.8(**只在容器**;桌機本來就有)。沒有 PowerShell。

## 1. VDF

| # | 發現 | 根因 | 修正(新版號) | 測試 |
|---|---|---|---|---|
| 1 | 外連沒經 VIA 網路工具(L103 · 規格 §8-3) | 全景 AST 稽核:擷取矩陣列的 23 支現役引擎裡,ENG113 · ENG115 · ENG116 · MDL011 的 v0100 直接 `urlopen` / `requests.get`(MDL011 檔頭寫「經鎖版網路工具」,程式裡沒有接線) | `VDF_ENG113_MacroMethod_v0103` · `VDF_ENG115_SentimentFetch_v0103` · `VDF_ENG116_AAIIWorkbook_v0103` · `VDF_MDL011_AkshareFetcher_v0104`:只把那幾個直連函數換成經 NetUnified(`http_json` / `http_bytes` / `http_text`)· 雙閘先行 · 工具不在或閘沒開 → 照實失敗,不退回直連 | 各 6/6(前版自測照跑 · 假網路工具 · 直連 0 次 · DENY · 工具不在);經 VDF 管理器 `engine run` 實跑:閘沒開 → FAIL「網路工具 DENY」、0.2 秒、零網路 |
| 2 | 其餘 18 支現役引擎 | — | 不用改:ENG055 一支就有 323 處網路工具呼叫,其他都已經經網路工具 | 同一次稽核 |

**沒改、照實列出:**
- `VDF_MDL006_FinancialModel`:`yf.Ticker` 一次取歷史 + 損益 / 資產負債 / 現金流量表 + info;NetUnified 沒有財報這條道(只有 `yf_history` 價格)→ 要在共用網路工具加一條道,是 VCGC / 共用工具的設計決定,不從 VDF 硬改。
- `VDF_TW_AllInOne_v039`:只在 VRN 的夾(`functional modules/VRN/_vdf_fetch/`),是 VRN MarketFetch 釘版借用的副本 → VRN 負責。
- `VDF_MDL012_FetchGroups` 的瀏覽器尋找:不認新版 Playwright 的 `chrome-linux64/` 夾(只影響 Linux 容器;桌機 Windows 用 chrome.exe / msedge)→ 容器測試用 `VIA_BROWSER_EXE` 指 headless shell,沒改程式。

## 2. VCGC

| # | 發現 | 根因 | 修正 | 測試 |
|---|---|---|---|---|
| 1 | 交接案 `engine_params` 紅:ToolingInventory v0101 ⑦b —— ENG055 備料卡鏈只有 `['v0123']`(0 參數 · 0 旗標) | ENG055 v0122 / v0123 照 VDF「尾版律」在執行期取本體、自己 `exec`;VCGC 的靜態鏈走法只認字面版號,看不到就當本體停 → 備料卡讀不到真正的參數 | `CGC_MDL253_ToolingInventory_v0103`:鏈尾那支若自己 exec 又照同族 `_v*.py` 找 → 照同一條尾版律取本體接著走(真本體裡只是用 exec 的不算) | 6/6 · 實樹 ENG055 鏈 `['v0123','v0118']` · 前版 v0101 11/11 · v0102 8/8 |
| 2 | 交接閘 `EVIDENCE_INVALID` 86 項(66 案) | 相依檔改過、收據過期 | 經 VCGC `handoff test` 逐案重跑(兩批) | 見第 3 節 |
| 3 | 9 案 rc 0 但標記對不上 | 測試真的過,只是總行字樣變了(檢查數增加 · 尾版換版 · 薄尾不再印前版總行) | 改釘目前的 PASS 總行(條件:收據 rc 0 · 沒有 `[FAIL]` 檢查行 · 沒有非零 FAIL 總行);舊標記留在 `repinned_before` | 第二批重跑 |
| 4 | 3 案釘舊版單跑就紅(UIEngine v0107 · VDF 管理器 v0155 / v0156) | 舊版自測寫死模板冊 v0103 的色值,讀到尾冊 v0104 就紅(不是功能壞) | 改經尾版跑(UIEngine v0108 · VDF 管理器 v0168 把前版自測照 v0103 那一代驗);舊指令留在 `repinned_before` | 第二批重跑 |
| 5 | `handoff checkpoint` | 交接閘紅時 checkpoint 會拒絕(不能拿來蓋掉「改了沒測」)| 沒有硬做 | — |

## 3. 交接案重跑結果

(第二批跑完後填)

## 4. 給 VRN(只讀 · 不代修)

- `VRN2_UIAction_v0100` · `_vdf_fetch/VDF_TW_AllInOne_v039`:缺加速器橋 / 未註冊(VCGC 交接閘列的)—— VRN 的檔 · 在 VRN 版本鎖內。
- 交接案 `vrn_logic_index`:VRN `logic` 動詞回 `updated_n: 1`(預期 0)→ VRN 的邏輯索引有 1 筆過期;這個動詞會寫 VRN 自己的檔(功能盤點冊 v0181 已列豁免)。容器測試寫出的未追蹤檔已刪除。

## 5. 要操作員 / 桌機的

- 桌機同步 + 實跑:`VRN2_Handover_latest.md` 第 13 節 SettleAll v0101 一行。
- MDL006 要不要加 NetUnified 財報道:操作員 / VCGC 決定。
- 規格 §8 第 4 項(SSOT 核號 500 待核 · 衝突裁定 · Auto Deploy)要操作員裁,本輪不代做。
