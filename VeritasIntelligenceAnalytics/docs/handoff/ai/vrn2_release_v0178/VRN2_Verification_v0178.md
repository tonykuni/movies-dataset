# VRN-2 v0178 驗證紀錄(2026-11-04 · 撤回自製 VerbatimVerifier v0106 · ④ 前同名檢查 · Workbench v0111 · 套件 v0178 · RoundAll v0134 · Handle-All v0126)

## 1. 桌機回報 → 根因 → 做法

| 回報 | 根因 / 做法 |
|---|---|
| 桌機 11/03 23:32 / 23:43 兩次:啟動器 v0177 2-3 秒 rc 1 · 收尾「VRN-2 3 項」· 錯誤比上一輪多 | 啟動器印 `Existing VRN-2 runtime differs; retained without overwrite: functional modules\\VRN2\\VRN2_VerbatimVerifier_v0106.py`。桌機那支是**啟動器自己 ④ 加速器注入**的 v0105 副本(v0149 起每輪都在 · 檔頭照 v0105 · 第 13 行後多一段 ACCEL-BRIDGE)· v0177 的 runtime 卻帶了另一支同名 v0106 → 只增不覆寫 → 拒裝 → 主跑沒跑 · 收尾沿用 v0175 收據(⑦ 逾時那一輪)· 多出「④ 跑啟動器 紅」與「頁面分割檔 黃(算 VRN-2)」|
| 改善有沒有遺失 | 沒有:同一輪 ⑤ 自動修已在桌機套上 BookSource v0102(主題與摘要 42 列千分位)· Workbench v0110 · 四點 / 主題與摘要 綠 · 增量庫 Combined 521 列就地整理(0 列追加)|
| 為什麼 v0177 沒在容器抓到 | 第一次 e2e 其實抓到了(同一句錯誤)· 我誤判成「沙盒底版的草稿」而把沙盒那支刪掉 —— 錯在這裡。v0178 的 e2e **保留**注入版 v0106(= 桌機現況)|
| 修法 | 套件 v0178:啟動器 VERBATIM 回 v0105(④ 照舊注入 v0106)· runtime v0167 不帶 v0106 · 管理器 v0260 / BookSource v0102 / OutputStore v0105 / Workbench v0110 跟 v0166 逐位元組相同 · RoundAll v0134 ④ 前同名檢查 |

## 2. 測試

| 項目 | 結果 |
|---|---|
| Workbench v0111 自測 | [GREEN] VRN2_Workbench v0111 自測 全過(5 項) |
| 啟動器 v0178 自測 | 26 段全過 · [PASS] v0178: VerbatimVerifier back to v0105 (the desktop v0106 is step 4's own accelerator injection · runtime v0167 sh |
| RoundAll v0134 自測 | [PASS] VRN2_RoundAll v0134 --selftest · 107 項 · 不過 0(新增 104 同名不同內容 → 紅 · 不跑啟動器 · 負責方 VRN-2;104b 套件 / 清單)|
| PowerShell | pwsh 剖析錯 [0, 0, 0, 0, 0, 0](含開閘一行)· Handle-All 一行 = 可讀版 · 開機行 = 可讀版 · 模式規則實跑:bad=full good=repair datared=repair |
| e2e(最短一行 · 沙盒**保留注入版 v0106** + 先放桌機已補放的 v0166 成員)| auto1 rc 0 · confirm list rc 0 · auto2 rc 0 · tamper rc 0 · 啟動器 v0178 實跑 154 秒(v0177 在同樣狀態 2 秒拒裝)· 注入版 v0106 原封不動:True · 同名衝突列 0 |
| e2e 資料面 | 範圍夾分割頁 0 份 · 主題與摘要新寫法 11 / 11 列 · auto2 追加 {"BasicInfo": 0, "FinancialData": 0, "Summary": 0, "Combined": 0, "Rejected": 0, "FinancialAligned": 0, "Deleted": 0} · 整理 {"Summary": 0, "Co · 頁首第三行:Transform investment reports into structured database intelligence. |
| 收尾負責方 | auto1 {"VCGC": 8, "VRN-2": 3, "人工": 8} · auto2 {"VCGC": 6, "VRN-2": 3, "人工": 8}(VRN-2 項 = v0176 基準 · 沙盒限定)|
| Workbench 4 視窗稽核(操作員給的跨裝置規格 · 頁寬 / 可讀名稱 / 表格捲動 / 主控台 / 外連)| v0110:{"desktop": {"overflow_px": 0, "unnamed_controls": 2, "tables_without_scroller": 0}, "laptop": {"overflow_px": 0, "unnamed_controls": 2, "tables_without_scroller": 0}, "tablet": {"overflow_px": 201, "unnamed_controls": 2, "tables_without_scroller": 0}, "mobile": {"overflow_px": 11, "unnamed_controls": 2, "tables_without_scroller": 1}} → **v0111:{"desktop": {"overflow_px": 0, "unnamed_controls": 0, "tables_without_scroller": 0, "console_errors": 0, "external_requests": 0}, "laptop": {"overflow_px": 0, "unnamed_controls": 0, "tables_without_scroller": 0, "console_errors": 0, "external_requests": 0}, "tablet": {"overflow_px": 0, "unnamed_controls": 0, "tables_without_scroller": 0, "console_errors": 0, "external_requests": 0}, "mobile": {"overflow_px": 0, "unnamed_controls": 0, "tables_without_scroller": 0, "console_errors": 0, "external_requests": 0}}** |
| 視覺鎖定(同一頁 v0110 vs v0111 · 每個元件 位置 · 大小 · 字級 · 顏色 · 背景)| {"1920": {"elements": 3678, "identical": true, "control_stable": true}, "1440": {"elements": 3678, "identical": true, "control_stable": true}, "1366": {"elements": 3678, "identical": true, "control_stable": true}, "1100": {"elements": 3678, "identical": true, "control_stable": true}, "1000": {"elements": 3678, "identical": true, "control_stable": true}, "999": {"elements": 3678, "identical": false, "control_stable": true}, "768": {"elements": 3678, "identical": false, "control_stable": true}} |
| 前輪瀏覽器項目(1,366 / 1,100)| {"1100": {"buttons_px": [28], "overflow": 0, "view_copy_rows": 5232, "thousands": ["4,200.00", "2,037.00"], "header_line3": ["Transform investment reports into structured database intelligence."], "tab_bar_px": [27, 29], "errors": []}, "1366": {"buttons_px": [28], "overflow": 0, "view_copy_rows": 5232, "thousands": ["4,200.00", "2,037.00"], "header_line3": ["Transform investment reports into struc |

## 3. 他系統驗收燈(只讀 · 四系統對等 · 不代修)

| 系統 | 驗收燈 | 依據 | 下一步 · 誰 |
|---|---|---|---|
| **VRN-2** | **OPEN(未結案)** | 桌機最後一次 11/03 23:43:11/03 23:43 RoundAll v0133:OPEN · VRN-2 3(⑦ 7201 秒是 v0175 收據 · ⑧ 沒本輪結果 · 頁面分割檔)· 人工 3 · 資料源 2 —— 啟動器 v0177 2-3 秒拒裝(v0106 同名) | 桌機貼 v0178 開閘一行(自動整輪)(**操作員**)|
| **VCGC** | **RED** | 2026-11-04 handoff check:交接閘 RED · 驗收 RED · 需求 226 · 待辦 217 · 發現 357(桌機頁面讀到的是倉裡 10/02 舊快照:GREEN / YELLOW)· 本輪:registry-sync --apply(新 119 · 變更 129 · AST 錯 0 · 撞號 0)· 編號 VIA Agent OS +118 列 · audit 遺失 0 · 改身分 0 · 重號 0 · 冊內不一致 1 · ssot panorama:元件冊乾跑 新 0 變 0 | VCGC 那一線在桌機逐案 handoff test → checkpoint(待辦 217)· 冊內不一致 / 命名同號異名要操作員裁 |
| **VDF** | **灰(沒有自報收據)** · 自測 RED | 固定位置沒有 VDF 自報收據(VIA_Reports/vdf/VDF_Closeout_latest.json)→ 灰 · 不猜 · 容器 run VDF_SystemManager --selftest:RED(v0122 鏈 DuckDB ResourceInUseException · 容器 DuckDB 版本 · 第 2 次) · 桌機 ⑥e:⑥e 借 VDF_TW_AllInOne_v039:rc 2 PARTIAL(不是失敗 · 價格照收)· 日線 COMPLETE 709 / REVIEW 26 / PARTIAL 11 · Yahoo≠TWSE 3706 19 列 · 6669 7 列 | VDF 那一線:自報收據 · AllInOne 改經 VIA 網路工具 + 加速器標記 · DuckDB 連線用完要 fetch / close |


## 4. 桌機下一步

1. 貼 `vrn2_release_v0178/VRN2_HandleAll_v0126.md` 的**開閘一行**(前面兩個同意閘是你貼 = 你開 · Handle-All 就不會停下來問)—— 上一輪收據仍是 v0175(⑦ 沒跑完)→ 自動整輪。
2. 收尾頁看:「④ 跑啟動器」不再 2 秒 rc 1 · 「頁面分割檔」綠 · ⑦ 遠低於 7,200 秒 · ⑧ 有本輪完成判定。
3. MQ-1560:`python "%USERPROFILE%\\Downloads\\VRN2_RoundAll_v0134.py" --confirm H-fd2ea35f --note "你核對的結論"`(只有你打才算)。
