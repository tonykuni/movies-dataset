# VeritasReportNova(VRN)v0169 驗證紀錄(2026-11-01 · Workbench v0104 · 套件 v0169 · RoundAll v0125 · Handle-All v0117)

## 1. 要求

操作員 2026-11-01:「呈現在 HTML U/I 上的子系統名稱還原為 VeritasReportNova · 成為 VRN 唯一系統」「印章 logo 為透明去背無框無特效 ·
以紅字大小為依據跟 header 文字做 header 大小 logo 最佳化調節加入」(附印章圖)。另:桌機貼 v0168 那行得 `[RED] boot SHA-256 mismatch` ——
原因是 AI 在對話裡手打的雜湊打錯(發行夾 md 裡程式產生的那一行是對的);這一輪的一行一律從檔案複製。

## 2. 做了什麼

| 檔 | 版本 | SHA-256 | 說明 |
|---|---|---|---|
| Workbench | v0104(runtime 內)| `1c72604db204` | v0103 薄尾:畫面名稱 VeritasReportNova / VRN · 00 只讀互看列 VDF · VCGC · 內建印章 · 主印框高 = 頁首文字區塊高 |
| 內建印章 | VRN2_Logo_Seal_v0100.png | `d2ac60ec3a8b` | 操作員附圖原樣(本來就透明去背 · 無白底 · 無框)· 裁到印泥範圍 · 218 × 240 |
| runtime | v0160 | `b53ab11f4a31` | v0159 的 198 個成員逐位元組不動 + 上面兩檔 |
| 啟動器 | v0169 | `6a0b63643f84` | 只換 WORKBENCH / runtime / 收據名 / 自測一段 |
| 套件 | VRN2_Closeout_v0169.zip | `e71ba31e628f` | 其他成員跟 v0168 逐位元組相同 |
| RoundAll | v0125 | `099f62ca06a1` | Workbench 鏈 + 印章只增補放 · 收尾頁沒有 v0104 標記 → 重渲染 · 取件分支 `claude/vrn2-closeout-authorization-y4ixl7`(退路 main)|
| Handle-All | v0117 | 一行 `8d1e06b5fbfb` · 開機檔 `0b9eb106465d` | 指向 RoundAll v0125 |

不改:檔名與指令(ActivateVRN-2_v#### · VRN2_* · vrn2://)· 收據 · 輸出冊 · 內嵌的輸出冊資料 window.VRN2_DATA(U/I 匯出 = 輸出冊逐字)· 左面板 Gate 按鈕。

## 3. 測試(雲端容器 · Linux · Python 3.13)

```text
[PASS] VRN2_Workbench v0104 --selftest · 10 項 · 不過 0
[PASS] v0169: Workbench v0104 is the active Workbench (VeritasReportNova names on screen · data untouched · page 00 read-only VDF / VCGC · built-in transparent seal sized to the header text) · v0103 kept as PRIOR
[PASS] VRN2_RoundAll v0125 --selftest · 89 項 · 不過 0
```

### 3.1 端到端沙盒(仿桌機:runtime 夾只有 v0102 鏈 · 收據 v0166)

```text
[GREEN] ① 套件 · 套件就位 <scratch>/e2e9/pkgdir(SHA-256 e71ba31e628f · 11 檔逐檔相符) · 舊套件夾改名備份 → <scratch>/e2e9/pkgdir.bak_20261101_185853
    [U/I] [GREEN] VRN2_Workbench v0104 · <scratch>/e2e9/VIA/VIA_Reports/vrn2/VRN2_Workbench_latest.html
[GREEN] ⑤ 修 · Workbench 重渲染(最新收據) · VRN2_Workbench v0104 · <scratch>/e2e9/VIA/VIA_Reports/vrn2/VRN2_Workbench_latest.html
```

結果:runtime 夾補放 Workbench v0103 · v0104 · 內建印章(v0102 雜湊不變)· 收尾頁標題「VeritasReportNova · VRN Workbench」· 印章 data URI · 00 頁在。

### 3.2 瀏覽器(Chromium)

1440 寬:文字區塊 20–79 px · 主印框 20–79 px(上下緣對齊)· 小印垂到 85 px · 印章 box-shadow / filter 皆 none · 底色透明 · JS 錯誤 0。
390 寬:頁首原本就換行(印章一列、文字一列),主印框高 = 文字區塊高 72 px。

## 4. 限制

- 容器沒有 PowerShell:這一行沒在 pwsh 實跑(雜湊鏈在 Python 端照 PowerShell 的算法核過)。
- 桌機有自己的 VRN2_Logo.* 時照舊用桌機的(先後順序不變);要用這顆印章:把本機那張拿開,或放同一張圖。
- 「VRN 唯一系統」只改 VRN 自己畫面上的名字;CLAUDE.md / AGENTS.md 的四系統命名規則(政策 L123)是 VCGC 的冊,這裡不改,待 VCGC 收。
