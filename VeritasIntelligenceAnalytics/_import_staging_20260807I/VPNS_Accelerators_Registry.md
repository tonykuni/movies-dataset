# VPNS 加速器登錄簿 · 20 Accelerators(不卡斷 + 提速)

> **編號勘誤(只增不減)**:過去場(VeritasEngineForge)已有已驗證加速器 **A01–A18**(A13 throttled ThreadJob pool、A14 heartbeat+watchdog、A15 write-set 衝突偵測、A16 lane 診斷包、A17 跨階段快取、A18 dry-run 預設)。本檔 A1–A20 為**本場新系列,正名 B01–B20**,與舊 A 系列並存不覆蓋;下表 A1..A20 讀作 B01..B20。

> 治理:**已套用 = 5 個低風險項**(v3);其餘 15 個列冊帶錨點,**首跑成功後按序啟用**——未測補丁一次打滿正是九頭龍製造法。
> 每項:做什麼 · 錨點(接哪裡)· 風險 · 預期增益。

## ✅ 已套用(v3)

| # | 加速器 | 錨點 | 風險 | 增益 |
|---|---|---|---|---|
| A1 | **SHA 快取**(path+size+mtime → 免重算) | `Get-Sha12` + `sha_cache.json` | 低 | 重掃 **5–50×**(大樹最有感) |
| A2 | **目錄剪枝**(`.git/node_modules/__pycache__/VIA_RUNS/backup_` 不進掃描) | L1/L2 `Where-Object` | 低 | 檔數大減,全程等比快 |
| A3 | **大檔跳雜湊**(>50MB 標 `SKIP>50MB`) | L1/L2 sha 欄 | 低 | 免 I/O 卡死(不卡斷) |
| A4 | **py_compile 批次**(單一 python 行程吃清單,免每檔 spawn) | L6 | 中低 | N 檔 = **N× → 1×** 行程成本 |
| A5 | **lane 碼錶 + LL-17 旗標**(<0.5s+空 → 即時警告路徑錯) | 順序 lane runner | 低 | 不卡斷的**可見性**;假成功秒抓 |

## 📋 列冊待啟用(首跑後,依序)

| # | 加速器 | 錨點 | 風險 | 增益 |
|---|---|---|---|---|
| A6 | `[IO.Directory]::EnumerateFiles` 取代 `Get-ChildItem -Recurse` | L1/L2 | 中 | 大樹枚舉 **2–10×** |
| A7 | Provider 級 `-Filter *.ps1`(免後過濾) | L5 | 低 | 掃描面縮小 |
| A8 | **AST 解析快取**(path+mtime → L4/L5/三輪共用,免重 parse) | `Test-ParseClean`/`Get-Ps1Facts` | 中 | 三輪迴圈 **~3×** |
| A9 | **全景第 1 輪重用 L5 結果**(免再走磁碟) | `Invoke-PanoramicScan` | 低 | 省一整輪 I/O |
| A10 | **只讀檔頭 KB**做關鍵字分類(非全文) | 分類器(回合1接 Read_Me 後) | 低 | 大檔分類 10×+ |
| A11 | **StringBuilder 組報告**(免字串串接 O(n²)) | matrix HTML 組裝 | 低 | 大報告顯著 |
| A12 | ThreadJob `-ThrottleLimit` = CPU 核數 | 並行分支 | 低 | 避免過度排程 |
| A13 | **node --check 批次**(單 node 行程吃清單,同 A4) | 語法檢查(回合1) | 中低 | 同 A4 |
| A14 | **增量模式**(mtime > 上次 SSOT 時間才重掃) | 掃描入口 + SSOT meta | 中 | 日常 delta 跑 **10×+** |
| A15 | `ConvertTo-Json -Compress` + 深度調校(大清單) | 各 JSON 落盤 | 低 | 落盤/載入快 |
| A16 | **>500 檔時雜湊並行**(`ForEach-Object -Parallel`,opt-in) | L1/L2 | 中 | I/O bound 樹 2–4× |
| A17 | **失敗跳過名單**(連續 parse fail 的檔列冊,免每輪重試) | 三輪迴圈 | 低 | 壞檔不拖全場 |
| A18 | **檢查點續跑**(進度落盤,中斷後從斷點續)——「不卡斷」的字面解 | orchestrator | 中 | 中斷零重工 |
| A19 | **Runspace 池重用**(長跑多批次時) | 並行分支 | 中 | 免重建 runspace 開銷 |
| A20 | **看門狗計時器**(單 lane 順序模式也有硬逾時 → 跳過該 lane 標 TIMEOUT,繼續其餘) | lane runner | 中 | 單點卡住不拖全場(不卡斷核心) |

## 啟用順序建議
首跑成功 → A9/A7/A15(零風險)→ A8/A10(快取類)→ A14/A18/A20(增量/續跑/看門狗)→ A6/A16/A13(枚舉/並行/批次)→ A11/A12/A17/A19。
每啟用一批 → 跑一次三輪全景 + 回歸閘(count invariants 不倒退)→ 才啟用下一批。
