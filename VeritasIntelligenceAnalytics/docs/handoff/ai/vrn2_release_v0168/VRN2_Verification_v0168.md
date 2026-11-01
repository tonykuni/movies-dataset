# VRN-2 v0168 驗證紀錄(2026-11-01 · Workbench v0103「00 系統現況」· 套件 v0168 · RoundAll v0124 · Handle-All v0116)

## 1. 要求

操作員 2026-11-01 上傳 `taiwan_stock_data_matrix.html`(VDS · VIA DATA MATRIX):「顯現部分資料擷取的端點來源 但並未顯示 DATAFRAME HEADERS ·
這種呈現方式更詳細更整合更優化可讓人一目了然 · 放在右面板第一個頁面的系統現況 SUMMARY 供 VRN-2 / VDF / VCGC 參考 · 以目前 HTML U/I 為基礎 ·
附件根據 LAYOUT 及字體階層大小視覺鎖定進行更新 · 原有功能設定不改」。附件原樣存在本夾 `VRN2_UI_Reference_taiwan_stock_data_matrix.html`(只當版面參考 · 不被任何程式載入)。

## 2. 做了什麼

| 檔 | 版本 | SHA-256 | 說明 |
|---|---|---|---|
| Workbench | v0103(runtime 內)| `fa9a90bfa6d4` | v0102 薄尾:右面板最前面「00 系統現況」· 開頁預設 · 01 ~ 04 不動 |
| runtime | v0159 | `476d774b7fd3` | v0158 的 197 個成員逐位元組不動 + Workbench v0103 |
| 啟動器 | v0168 | `7d8745214ed4` | 只換 WORKBENCH / runtime / 收據名 / 自測一段 |
| 套件 | VRN2_Closeout_v0168.zip | `f421ca132e9e` | 其他成員跟 v0166 逐位元組相同 |
| RoundAll | v0124 | `e6767575617f` | ⑤ 先只增補放 Workbench 鏈再重渲染 · 收尾頁沒有 v0103 標記 → 重渲染 · 取件分支 `claude/vrn2-closeout-authorization-y4ixl7`(退路 main)|
| Handle-All | v0116 | 一行 `2941e8392252` · 開機檔 `d50fd1ac12b3` | 指向 RoundAll v0124 |

00 頁內容:VRN-2 輸出冊矩陣(資料冊 · 來源 · 端點 · **DataFrame 表頭 = 冊裡真實欄名** · 燈)· 本輪流程步驟矩陣 · 其他系統只讀互看(VCGC 交接快照自報的燈 ·
VDF 固定位置有自報收據才讀 · 沒有就灰燈寫原因 · VRN-1 只看已登記入口)· 收尾狀態照 RoundAll 收尾頁收據(REVIEW 不寫成成功)· 點一列看全部欄(雙語名稱沿用 v0102 對照表)·
圖例篩選 · 摘要卡 · 窄螢幕一列一卡。版面 / 字體階層照附件;色盤與字型仍是範本鎖定的(不引外部字型 · 不新增色碼)。

## 3. 測試(雲端容器 · Linux · Python 3.13)

```text
[PASS] VRN2_Workbench v0103 --selftest · 15 項 · 不過 0
[PASS] v0168: Workbench v0103 is the active Workbench (page 00 系統現況 SUMMARY first and open by default · output books × source × endpoint × real DataFrame headers · step matrix · other systems read-only) · v0102 kept as PRIOR (tabs 01 – 04 unchanged)
[PASS] VRN2_RoundAll v0124 --selftest · 88 項 · 不過 0
```

### 3.1 端到端沙盒(仿桌機:runtime 夾只有 v0102 鏈 · 收據 v0166 · 收尾頁是 v0102 渲染的)

`VRN2_RoundAll_v0124.py --only package,fix,report,closeout --offline --package <夾>`:

```text
[GREEN] ① 套件 · 套件就位 <scratch>/e2e/pkgdir(SHA-256 f421ca132e9e · 11 檔逐檔相符) · 舊套件夾改名備份 → <scratch>/e2e/pkgdir.bak_20261101_184632
    [U/I] [GREEN] VRN2_Workbench v0103 · <scratch>/e2e/VIA/VIA_Reports/vrn2/VRN2_Workbench_latest.html
[GREEN] ⑤ 修 · Workbench 重渲染(最新收據) · VRN2_Workbench v0103 · <scratch>/e2e/VIA/VIA_Reports/vrn2/VRN2_Workbench_latest.html
```

結果:runtime 夾補放 `VRN2_Workbench_v0103.py`(v0102 雜湊不變)· 收尾頁標記 `VRN2_Workbench v0103 over v0102` · 有「00 系統現況」分頁。
沙盒收尾 rc 2 是假資料的黃燈(不是本輪改動)。

### 3.2 瀏覽器(Chromium · 本容器)

1440 × 1000:開頁 = 00 系統現況 · 點 FinancialData 一列 → 明細列出全部 7 欄 · ESC 關 · 圖例 TWSE → 14 列裡 10 列淡出 · 01 ~ 04 切換照舊 · 02 資料冊表格照舊 · JS 錯誤 0。
390 寬:00 頁一列一卡、沒有溢出;整頁的水平捲動(513 px)來自原本的頁首,v0102 一樣(原有設定不改 · 沒動)。

## 4. 沒做 / 限制

- 容器沒有 PowerShell:Handle-All / 開機行**沒在 pwsh 剖析或實跑**(前幾輪有);它們是 v0115 原始檔逐字替換(取件分支 · 版號 · 雜湊),一行版用同一支 join_ps 產生,雜湊在 Python 端核過。
- RoundAll 自測在本容器實跑 88 項(其餘要 pwsh 的項目本機不跑)· 不過 0。
- 桌機的 `VRN2_Workbench_latest.html` 要桌機跑一次 repair 才會換成 v0103(收尾狀態仍以桌機收尾頁為準 · 目前 REVIEW)。
