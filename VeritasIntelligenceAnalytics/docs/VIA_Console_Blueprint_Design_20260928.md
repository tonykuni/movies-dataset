# VCGC / VDF / VRN 主控台藍圖(CGC_MDL227)· 設計與對接說明

操作員 2026-09-28 令:左面板參數輸入;右面板以多元展示為主、功能少量;多分頁;
矩陣狀況、邏輯規範、引擎總攬、運作摘要、錯誤摘要都放在分頁 1,結果放後面;第一頁盡量視覺化,現代但專業;
再生成一支引擎收集這些參數與介面需求,和已存檔的標準可調 HTML U/I 快速對接 synchronizer。

引擎:`supportive modules/registry/CGC_MDL227_ConsoleBlueprint_v0100.py`(自測 13/13)。
產出:`VIA_Reports/console_blueprint/`(再生件,永不 commit)。

## 版面

| 區 | 內容 | 資料從哪來(唯一出處) |
|---|---|---|
| 頁首 | 引擎版號 · 建構時間 · 四態圖例 | — |
| 左面板 | 家族切換(VCGC / VDF / VRN / VAP)→ 群組 → 項目勾選 → 只顯示勾選項目用得到的參數 → 指令預覽(PLAN)→ 複製指令 · 下載參數 JSON · 重設 | 項目與參數:`VIA_InputConsole_Spec`;控制項由 `param_kinds` 決定;預設值依序取項目起日、群組起日、冊預設;指令:EngineBus `call(apply=False)`,規則與匯流排的 `_argv_for` 相同 |
| 分頁 1 總覽 | 6 張 KPI 卡 · 矩陣熱圖(5 本 × 5 態)· 最近一次運作甜甜圈 · VRN 六層鏈與律條類別長條 · 引擎總攬(各家族在位率與樹上盤點)· 錯誤摘要前 8 條 · 資料來源四態 | 見下方「分頁 2–6」 |
| 分頁 2 矩陣 | 已修冊複驗 · 收尾鎖冊 · 成功冊 · Celeritas 基線 · 參數冊 × 匯流排在位,可依狀態篩選 | 已修冊的尾版憑據交給 CGC_MDL158 尾版的 `_verify_one` 驗;要全樹掃描才量得到的類別照實標 NODATA |
| 分頁 3 邏輯規範 | VRN 六層節點卡 · 政策律條依位階排(可搜尋) | `VIA_Policy_Laws_SSOT` · `VIA_VRN_LogicArchitecture_SSOT` |
| 分頁 4 引擎 | 參數冊每一項:尾版 · 在位 · 版數 · 觸網 · 參數 · 實際會跑的那一句 | EngineBus `catalog()` · `call(apply=False)` |
| 分頁 5 錯誤與待辦 | 紅燈與待操作員裁定,每條附來源和「看 →」跳轉 | 由分頁 2 / 4 / 6 與資料來源匯總 |
| 分頁 6 執行結果 | 最近一次格子逐站結果(可依狀態篩選、搜尋) | 最新一份 `VIA_Reports/selftest_runs/GRID_*.json` |

**原則**
- 每個數字都帶四態,GREEN / RED / NODATA / ABSENT(另有 AMBER = 待裁)。量不到就照實標,不當綠(L16)。
- 本支不另立第二把尺(L05)。
- 本支不跑任何引擎、不碰網路。真的要跑,一律經 VCGC 唯一入口或匯流排加 `--apply`。

## 對接制式 U/I 與 synchronizer

對接對象是 `VIA_HTML_UI`(manifest 的三個入口:launcher、centralUI、synchronizer)。模板原文一個位元組都不動,自測會驗寫入前後的 sha,並驗「拿掉插入段後等於原文」。

1. **預置模組**:把 `vcgc-console-blueprint` 預置進 synchronizer 的模組冊(`via.sync.state.v2`)。
   - 預置契約沿用 VRN_ENG089 尾版的 `PRESEED_JS`。
   - `DEFAULT_MODULES` 從模板本身抽出。
2. **中央頁外掛**:透過 `VIA_REGISTER_ADDON` 掛上 KPI 卡、「開啟全頁主控台」,以及 6 個分頁的捷徑。
   - 在 synchronizer 開、關、釘選這個模組,中央頁會即時跟著變(BroadcastChannel `via.sync.v2`)。
3. **synchronizer 外掛**:透過 `VIA_REGISTER_SYNC_ADDON` 掛上狀態列、「開啟主控台」、「下載藍圖」。
4. **全頁主控台**:`ui/VIA-Console-Blueprint.html`,零外部資源,可以用 `file://` 直接開。

容器內用 headless Chromium 實測:
- 零 JS 錯誤;手機 390px 無橫向捲動。
- 預置結果 = ADDED;中央頁外掛已掛上。
- 在 synchronizer 停用模組後,中央頁立即隱藏。

## 用法

```
python "supportive modules/registry/CGC_MDL227_ConsoleBlueprint_v0100.py" build       # 收集 → 藍圖 → 全頁 → 對接三入口
python "supportive modules/registry/CGC_MDL227_ConsoleBlueprint_v0100.py" blueprint   # 只收集,印摘要(零寫檔)
python "supportive modules/registry/CGC_MDL227_ConsoleBlueprint_v0100.py" status      # 最近一版還對嗎(OK / STALE / NONE)
python "supportive modules/registry/CGC_MDL227_ConsoleBlueprint_v0100.py" --selftest
```

## 還沒做(候裁定)

- 左面板目前只產生 PLAN 指令與參數 JSON,不直接寫回參數冊的 `user` 區塊。寫回要走 Deck 本地伺服器的 `save_spec`,這一步屬於動手,待操作員裁定。
- 新增模組要登冊(`registry-sync`)需要 VCGC 批准 `--apply`,本批不代跑。
