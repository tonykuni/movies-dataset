# VRN-1 / VRN-2 操作員一鍵 v0106(cmd / PowerShell 都能貼 · v0105 + ② 改指 VRN-2 一鍵 v0145:管理器 v0255 冪等閘並行 · 心跳 · 階段計時)

桌機 2026-10-29 08:14 實跑 v0144(52 份 · 2422 秒):前後端已連結,慢在 ⑦ 的冪等閘序跑(約 1050 秒無輸出)。v0106 = v0105 + ② 改指 **VRN-2 一鍵 v0145**(套件 v0145 = 啟動器 v0145 + runtime v0145 = v0144 + 管理器 v0255);其餘一字不改。

操作員 2026-10-29 政策(三系統獨立 · SSOT-ID 由 VCGC 核號子系統補填 · VRN-2 快速收尾:輸出位置 Windows I/O / 雲端 · Parquet 增量擷取 · DuckDB 管理)。v0106 = v0104 + ② 改指 **VRN-2 一鍵 v0145**(套件 v0144 = 啟動器 v0144 + runtime v0144:處理器 v0108 · OutputStore · SSOTSync · Workbench v0101);其餘一字不改。

操作員 2026-10-29 桌機實跑貼回:同一 VIA 根兩個啟動器重疊 → RAM 0.16 GB → ⑦ / ⑪ / ⑫b 全逾時 → ⑤b 紅;v0103 的橫幅還印「操作員一鍵 v0102」。v0106 = v0103 + ② 改指 **VRN-2 一鍵 v0145**(套件 v0143 = 啟動器 v0143 + runtime v0142 不動:單機閘 · ⑫b 600 秒且本支補放 · ⑦ 無輸出 3600 秒 · ⑪ 3600 秒)+ 橫幅版號修正;其餘(① VRN-1 pull · ③ VRN-1 MAIN · ⑤b / ⑤c · 總結)一字不改。

操作員令(2026-10-28):本地實測貼回(v0136 線)+「模板視覺鎖定 … 整合為一個系統 … 透明去背 logo」。v0106 = v0102 + ② 改指 **VRN-2 一鍵 v0145**(套件 v0142:摘要器 v0117 四點開頭不帶頁首 / 標題 / 小標題 · Workbench U/I v0100 範本視覺鎖定、綁本輪收據與輸出冊、收尾後自動開啟 · `VRN2_Logo.png` 自動去背;v0141 的冪等閘 / 四點補齊 / 原文核對 v0106 / 驗證器 v0110 照舊);v0102 原文:v0101 + ② 改指 VRN-2 一鍵 v0136(驗證器 v0106:DUPKEY 看位置證據 · 對調診斷 · EPS 格 · 貼給 AI 每類錯值都出現;啟動器 ⑫a 自己把 VRN-1 倉 fast-forward 到 main)。一段貼上去:VRN-1 倉拉到最新 → VRN-2 v0136 全流程(U/I 自己跳出)→ VRN-1 MAIN → 總結 + 要人判。v0101 的開關全部照舊。Codex #564 修正:① 切不到 main 就不拉(不會把別的分支快轉、也不會把分岔的分支當最新)· 未追蹤的檔另外數、留著不動 · ④ 用 `VRN_PAIR_SKIP` 跳過一邊 → 最多黃、不說「兩邊都跑完」· 一行的 boot 紅燈 `exit 1`、最後 `exit` 最終燈(cmd 的 `%ERRORLEVEL%` = GREEN 0 / YELLOW 2 / RED 1)。

操作員令(2026-10-20):「INTEGRATE ABOVE INTO ONE CODE TO HANDLE ALL ABOVE. git pull」·「INTEGRATED INTO ONE CODE TO HANDLE ALL.」。v0101 = v0100 + 該你手動做的也自己處理(VRN-1 倉不在 → 複製 · 沒有 PowerShell 7 → winget 自動裝 · 樣本夾自動找 · 總結列出要人判的項目與 GitHub Actions 狀態):

| 步驟 | 做什麼 | 出事時 |
|---|---|---|
| ① VRN-1 倉 | **不在 → 從 GitHub 複製**(`https://github.com/tonykuni/VIA-VDF-VRN` · main)· 在 → `C:\Users\tonyk\VIA-VDF-VRN`(`$env:VIA_VRN1_ROOT`)切到 `main`、只快轉拉到最新(第十三 / 十四輪 · 借出工具冊)· 有沒提交的改動 → 先 `git stash` 保存(名稱「VRN1_VRN2_OneClick 自動暫存 …」· `git stash pop` 拿回來)| 讀不到 GitHub / 不能快轉 → 黃 · 照本機現狀繼續 |
| ② VRN-2 一鍵 v0145 | 從 GitHub 讀 `vrn2_release_v0145/VRN2_OneClick_v0145.md` → **核對 SHA-256 `c834b06e8702`** → 執行 VRN-2 自己的一鍵(取啟動器 v0136 · ①~⑫ · ② 寫 VRN-2 借出工具冊 · ⑪ 驗證器 v0106 · ⑫a 同步 VRN-1 倉 · ⑫ 借 VRN-1 的 PIVOT · U/I 自己跳出)| 雜湊不對 → 紅、不執行 · VRN-1 照常跑 |
| ③ VRN-1 MAIN | `artifacts\VRN-1.ps1`(PowerShell 7 · **沒有就 winget 自動安裝**)`check` → `run --no-cache`(**樣本夾自動找**:`VRN1_SAMPLES` → `VIA_VRN_INPUT` → `C:\測試樣本報告`,兩邊讀同一批 · G23 借 VRN-2 的段落標題 / OCR · 只寫輸出夾,不寫倉 —— 下次 git pull 不會卡)| 裝不起來 → 紅 + 手動指令 |
| ④ 總結 | 每一步的燈 · ⑫ 借到什麼 · G23 借到幾支 · G21 / G22 · 收尾 · **要人判**(P21 待修的報告 · 待修清單的位置 · 有 `gh` 就加 VRN-1 倉 main 的 GitHub Actions 結果)· NEXT | 結束碼 GREEN 0 / YELLOW 2 / RED 1 |

本段**只呼叫**兩邊自己的入口,不改任何一邊的程式 / 冊 / 號;VCGC 與 VDF 不碰。開關:`$env:VRN1_SAMPLES`(VRN-1 樣本夾 · 不設 = VRN-1 自己的預設)·
`$env:VRN1_OUT`(VRN-1 輸出夾)· `$env:VRN1_ARGS`(多給 VRN-1 run 的旗標)· `$env:VRN_PAIR_NO_PULL = '1'` 不拉 · `$env:VRN_PAIR_NO_STASH = '1'` 有改動就不拉 ·
`$env:VRN_PAIR_SKIP = 'VRN-1'` 或 `'VRN-2'` 這次跳過那一邊 · `$env:VRN_PAIR_NO_INSTALL = '1'` 不自動裝 PowerShell 7 · `$env:VRN_PAIR_NO_CLONE = '1'` 不自動複製 VRN-1。容器實測見 `VRN1_VRN2_Verification_v0106.md`。v0100 / v0101 照舊留著。

程式碼決定不了、要你判的(總結會列出來):VRN-1 P21 待修的報告(列標對不到科目 · 報告本來沒有年度表 · 影像 PDF)· `EV/EBITDA (excl. leases)` 要不要給它自己的科目 · GitHub Actions 帳號層級的設定。

## 在「命令提示字元(cmd)」或 PowerShell 都能貼的一行(建議用這個)

它開 Windows PowerShell → 從 GitHub 分支 `claude/optimistic-goodall-yhalc5`(讀不到 → `main`)讀本檔的程式碼 → **核對 SHA-256 `b625cfbc6a3de4c41dd73082021f49585157974cc6b9e232d2f1c9b943ef29ca`** → 相符才執行(不相符就停)。
**不要把下面整段程式碼貼進 cmd**(cmd 不認得 PowerShell)。

```bat
powershell -NoProfile -ExecutionPolicy Bypass -EncodedCommand JABFAHIAcgBvAHIAQQBjAHQAaQBvAG4AUAByAGUAZgBlAHIAZQBuAGMAZQAgAD0AIAAnAEMAbwBuAHQAaQBuAHUAZQAnAAoAdAByAHkAIAB7ACAAWwBDAG8AbgBzAG8AbABlAF0AOgA6AE8AdQB0AHAAdQB0AEUAbgBjAG8AZABpAG4AZwAgAD0AIABbAFQAZQB4AHQALgBFAG4AYwBvAGQAaQBuAGcAXQA6ADoAVQBUAEYAOAAgAH0AIABjAGEAdABjAGgAIAB7ACAAfQAKACQAUgAgACAAPQAgAGkAZgAgACgAJABlAG4AdgA6AFYAUgBOADIAXwBSAE8ATwBUACkAIAB7ACAAJABlAG4AdgA6AFYAUgBOADIAXwBSAE8ATwBUACAAfQAgAGUAbABzAGUAIAB7ACAAJwBDADoAXABVAHMAZQByAHMAXAB0AG8AbgB5AGsAXABPAG4AZQBEAHIAaQB2AGUAXABEAG8AYwB1AG0AZQBuAHQAcwBcAG0AbwB2AGkAZQBzAC0AZABhAHQAYQBzAGUAdABcAFYAZQByAGkAdABhAHMASQBuAHQAZQBsAGwAaQBnAGUAbgBjAGUAQQBuAGEAbAB5AHQAaQBjAHMAJwAgAH0ACgAkAEIAcgAgAD0AIAAnAGMAbABhAHUAZABlAC8AbwBwAHQAaQBtAGkAcwB0AGkAYwAtAGcAbwBvAGQAYQBsAGwALQB5AGgAYQBsAGMANQAnAAoAJABQACAAIAA9ACAAJwBWAGUAcgBpAHQAYQBzAEkAbgB0AGUAbABsAGkAZwBlAG4AYwBlAEEAbgBhAGwAeQB0AGkAYwBzAC8AZABvAGMAcwAvAGgAYQBuAGQAbwBmAGYALwBhAGkALwB2AHIAbgAxAF8AdgByAG4AMgBfAG8AbgBlAGMAbABpAGMAawBfAHYAMAAxADAANgAnAAoAJABIACAAIAA9ACAAJwBiADYAMgA1AGMAZgBiAGMANgBhADMAZABlADQAYwA0ADEAZABkADcAMwAwADgAMgAwADIAMQBmADQAOQA1ADgANQAxADUANwA5ADcANABjAGMANgBiADkAZQAyADMAMgBkADIAZgAxAGMAOQBiADkANAAzAGUAZgAyADkAYwBhACcACgBXAHIAaQB0AGUALQBIAG8AcwB0ACAAKAAnAFsAVgBSAE4ALQAxACAALwAgAFYAUgBOAC0AMgBdACAAUABvAHcAZQByAFMAaABlAGwAbAAgACcAIAArACAAJABQAFMAVgBlAHIAcwBpAG8AbgBUAGEAYgBsAGUALgBQAFMAVgBlAHIAcwBpAG8AbgAgACsAIAAnACAAtwAgAJ5fIABHAGkAdABIAHUAYgAgAICLzWRcT+FUAE51kyAAdgAwADEAMAA2ACgAOGgNXCAAUwBIAEEALQAyADUANgAgAIxf91dMiCkAJwApACAALQBGAG8AcgBlAGcAcgBvAHUAbgBkAEMAbwBsAG8AcgAgAFkAZQBsAGwAbwB3AAoAJAB0AG8AcAAgAD0AIABnAGkAdAAgAC0AQwAgACQAUgAgAHIAZQB2AC0AcABhAHIAcwBlACAALQAtAHMAaABvAHcALQB0AG8AcABsAGUAdgBlAGwAIAAyAD4AJABuAHUAbABsAAoAaQBmACAAKAAtAG4AbwB0ACAAJAB0AG8AcAApACAAewAgAFcAcgBpAHQAZQAtAEgAbwBzAHQAIAAiAFsAUgBFAEQAXQAgACQAUgAgAA1OL2YgAGcAaQB0ACAACVAWYn5iDU4wUiAAZwBpAHQAIgAgAC0ARgBvAHIAZQBnAHIAbwB1AG4AZABDAG8AbABvAHIAIABSAGUAZAA7ACAAZQB4AGkAdAAgADEAIAB9AAoAJAB0AG8AcAAgAD0AIAAiACQAdABvAHAAIgAuAFQAcgBpAG0AKAApAAoAJAB0ACAAPQAgAEoAbwBpAG4ALQBQAGEAdABoACAAKABbAEkATwAuAFAAYQB0AGgAXQA6ADoARwBlAHQAVABlAG0AcABQAGEAdABoACgAKQApACAAKAAnAHYAcgBuADEAMgBfAGIAbwBvAHQAXwAnACAAKwAgACgARwBlAHQALQBEAGEAdABlACkALgBUAG8AUwB0AHIAaQBuAGcAKAAnAHkAeQB5AHkATQBNAGQAZABfAEgASABtAG0AcwBzACcAKQApAAoATgBlAHcALQBJAHQAZQBtACAALQBJAHQAZQBtAFQAeQBwAGUAIABEAGkAcgBlAGMAdABvAHIAeQAgAC0ARgBvAHIAYwBlACAALQBQAGEAdABoACAAJAB0ACAAfAAgAE8AdQB0AC0ATgB1AGwAbAAKACQAegAgAD0AIABKAG8AaQBuAC0AUABhAHQAaAAgACQAdAAgACcAcABhAGkAcgAuAHoAaQBwACcAOwAgACQAbwBrAHoAIAA9ACAAJABmAGEAbABzAGUACgBmAG8AcgBlAGEAYwBoACAAKAAkAGIAIABpAG4AIAAkAEIAcgAsACAAJwBtAGEAaQBuACcAKQAgAHsACgAgACAAZgBvAHIAZQBhAGMAaAAgACgAJAB3ACAAaQBuACAAMAAsACAAMgAsACAANAAsACAAOAAsACAAMQA2ACkAIAB7ACAAaQBmACAAKAAkAHcAKQAgAHsAIABTAHQAYQByAHQALQBTAGwAZQBlAHAAIAAtAFMAZQBjAG8AbgBkAHMAIAAkAHcAIAB9ADsAIABnAGkAdAAgAC0AQwAgACQAdABvAHAAIABmAGUAdABjAGgAIAAtAHEAIABvAHIAaQBnAGkAbgAgACQAYgAgADIAPgAmADEAIAB8ACAATwB1AHQALQBOAHUAbABsADsAIABpAGYAIAAoACQATABBAFMAVABFAFgASQBUAEMATwBEAEUAIAAtAGUAcQAgADAAKQAgAHsAIABiAHIAZQBhAGsAIAB9ACAAfQAKACAAIABnAGkAdAAgAC0AQwAgACQAdABvAHAAIABhAHIAYwBoAGkAdgBlACAALQAtAGYAbwByAG0AYQB0AD0AegBpAHAAIAAtAG8AIAAkAHoAIAAoACcAbwByAGkAZwBpAG4ALwAnACAAKwAgACQAYgAgACsAIAAnADoAJwAgACsAIAAkAFAAKQAgAFYAUgBOADEAXwBWAFIATgAyAF8ATwBuAGUAQwBsAGkAYwBrAF8AdgAwADEAMAA2AC4AbQBkACAAMgA+ACYAMQAgAHwAIABPAHUAdAAtAE4AdQBsAGwACgAgACAAaQBmACAAKAAkAEwAQQBTAFQARQBYAEkAVABDAE8ARABFACAALQBlAHEAIAAwACAALQBhAG4AZAAgACgAVABlAHMAdAAtAFAAYQB0AGgAIAAtAEwAaQB0AGUAcgBhAGwAUABhAHQAaAAgACQAegApACkAIAB7ACAAJABvAGsAegAgAD0AIAAkAHQAcgB1AGUAOwAgAFcAcgBpAHQAZQAtAEgAbwBzAHQAIAAoACcAWwAIil0AIAAATnWTC3oPX7x4hk+QbiAARwBpAHQASAB1AGIAIAAnACAAKwAgACQAYgApACAALQBGAG8AcgBlAGcAcgBvAHUAbgBkAEMAbwBsAG8AcgAgAEQAYQByAGsARwByAGEAeQA7ACAAYgByAGUAYQBrACAAfQAKAH0ACgBpAGYAIAAoAC0AbgBvAHQAIAAkAG8AawB6ACkAIAB7ACAAVwByAGkAdABlAC0ASABvAHMAdAAgACIAWwBSAEUARABdACAAgIsNTjBSIABHAGkAdABIAHUAYgAgAAZSL2UgACQAQgByACAAFmIgAG0AYQBpAG4AIACEds1kXE/hVABOdZMoALJ9740gAC8AIABnAGkAdAApACIAIAAtAEYAbwByAGUAZwByAG8AdQBuAGQAQwBvAGwAbwByACAAUgBlAGQAOwAgAGUAeABpAHQAIAAxACAAfQAKAEUAeABwAGEAbgBkAC0AQQByAGMAaABpAHYAZQAgAC0ATABpAHQAZQByAGEAbABQAGEAdABoACAAJAB6ACAALQBEAGUAcwB0AGkAbgBhAHQAaQBvAG4AUABhAHQAaAAgACQAdAAgAC0ARgBvAHIAYwBlAAoAJABtAGQAIAA9ACAAWwBJAE8ALgBGAGkAbABlAF0AOgA6AFIAZQBhAGQAQQBsAGwAVABlAHgAdAAoACgASgBvAGkAbgAtAFAAYQB0AGgAIAAkAHQAIAAnAFYAUgBOADEAXwBWAFIATgAyAF8ATwBuAGUAQwBsAGkAYwBrAF8AdgAwADEAMAA2AC4AbQBkACcAKQAsACAAWwBUAGUAeAB0AC4ARQBuAGMAbwBkAGkAbgBnAF0AOgA6AFUAVABGADgAKQAgAC0AcgBlAHAAbABhAGMAZQAgACIAYAByAGAAbgAiACwAIAAiAGAAbgAiAAoAJABjAG8AZABlACAAPQAgAFsAcgBlAGcAZQB4AF0AOgA6AE0AYQB0AGMAaAAoACQAbQBkACwAIAAnACgAPwBzACkAYABgAGAAcABvAHcAZQByAHMAaABlAGwAbABcAG4AKAAuACoAPwApAFwAbgBgAGAAYAAnACkALgBHAHIAbwB1AHAAcwBbADEAXQAuAFYAYQBsAHUAZQAKACQAcwBoAGEAIAA9ACAALQBqAG8AaQBuACAAKABbAFMAZQBjAHUAcgBpAHQAeQAuAEMAcgB5AHAAdABvAGcAcgBhAHAAaAB5AC4AUwBIAEEAMgA1ADYAXQA6ADoAQwByAGUAYQB0AGUAKAApAC4AQwBvAG0AcAB1AHQAZQBIAGEAcwBoACgAWwBUAGUAeAB0AC4ARQBuAGMAbwBkAGkAbgBnAF0AOgA6AFUAVABGADgALgBHAGUAdABCAHkAdABlAHMAKAAkAGMAbwBkAGUAKQApACAAfAAgAEYAbwByAEUAYQBjAGgALQBPAGIAagBlAGMAdAAgAHsAIAAkAF8ALgBUAG8AUwB0AHIAaQBuAGcAKAAnAHgAMgAnACkAIAB9ACkACgBpAGYAIAAoACQAcwBoAGEAIAAtAG4AZQAgACQASAApACAAewAgAFcAcgBpAHQAZQAtAEgAbwBzAHQAIAAiAFsAUgBFAEQAXQAgAABOdZMLeg9fvHggAFMASABBAC0AMgA1ADYAIAANTg1cKAAkAHMAaABhACkAtwAgAA1O91dMiCIAIAAtAEYAbwByAGUAZwByAG8AdQBuAGQAQwBvAGwAbwByACAAUgBlAGQAOwAgAGUAeABpAHQAIAAxACAAfQAKAFcAcgBpAHQAZQAtAEgAbwBzAHQAIAAoACcAWwBHAFIARQBFAE4AXQAgAABOdZMLeg9fvHggAFMASABBAC0AMgA1ADYAIAAnACAAKwAgACQASAAuAFMAdQBiAHMAdAByAGkAbgBnACgAMAAsACAAMQAyACkAIAArACAAJwAgAPh2JnsgAJIhIAD3V0yIJwApACAALQBGAG8AcgBlAGcAcgBvAHUAbgBkAEMAbwBsAG8AcgAgAEcAcgBlAGUAbgAKACQAZwBsAG8AYgBhAGwAOgBMAEEAUwBUAEUAWABJAFQAQwBPAEQARQAgAD0AIAAxAAoAdAByAHkAIAB7ACAAJgAgACgAWwBzAGMAcgBpAHAAdABiAGwAbwBjAGsAXQA6ADoAQwByAGUAYQB0AGUAKAAkAGMAbwBkAGUAKQApACAAfQAgAGMAYQB0AGMAaAAgAHsAIABXAHIAaQB0AGUALQBIAG8AcwB0ACAAKAAnAFsAUgBFAEQAXQAgAABOdZP3V0yILU63ZSgAKmcUZSpihHaLTxZZKQA6ACcAIAArACAAJABfAC4ARQB4AGMAZQBwAHQAaQBvAG4ALgBNAGUAcwBzAGEAZwBlACkAIAAtAEYAbwByAGUAZwByAG8AdQBuAGQAQwBvAGwAbwByACAAUgBlAGQAOwAgACQAZwBsAG8AYgBhAGwAOgBMAEEAUwBUAEUAWABJAFQAQwBPAEQARQAgAD0AIAAxACAAfQAKAGUAeABpAHQAIAAkACgAaQBmACAAKAAkAG4AdQBsAGwAIAAtAG4AZQAgACQAZwBsAG8AYgBhAGwAOgBMAEEAUwBUAEUAWABJAFQAQwBPAEQARQApACAAewAgAFsAaQBuAHQAXQAkAGcAbABvAGIAYQBsADoATABBAFMAVABFAFgASQBUAEMATwBEAEUAIAB9ACAAZQBsAHMAZQAgAHsAIAAxACAAfQApACAAIAAgACMAIABDAG8AZABlAHgAIAAjADUANgA0ADoAAGdCfchxNl7eViAAYwBtAGQAIACEdiAAJQBFAFIAUgBPAFIATABFAFYARQBMACUAKABHAFIARQBFAE4AIAAwACAAtwAgAFkARQBMAEwATwBXACAAMgAgALcAIABSAEUARAAgADEAKQC3ACAABX3IcSAALwAgAItPFlkgAJIhIAAxAAoA
```

或:在 cmd 先輸入 `powershell` 按 Enter(提示字元變成 `PS C:\Users\tonyk>`),再貼下面整段程式碼。

程式碼 SHA-256(本文 · 一行核對的就是這個):`b625cfbc6a3d`

```powershell
& {
  # ===== VRN-1 / VRN-2 操作員一鍵 v0106(2026-10-29 · ② 改指 VRN-2 一鍵 v0145:管理器 v0255 冪等閘並行 · 心跳 · 階段計時;v0105 · ② 改指 VRN-2 一鍵 v0144:輸出位置 window I/O · DuckDB 增量 Parquet 庫 · SSOT-ID 協作;v0104 · ② 改指 VRN-2 一鍵 v0143:單機閘 · 子行程上限加寬 · ⑫b 補放;橫幅版號修正;v0103 2026-10-28 · ② 改指 VRN-2 一鍵 v0145:套件 · 摘要器 v0117 · Workbench U/I v0100;v0102 2026-10-21 · 操作員「ONE CODE TO HANDLE ALL.」· v0101 2026-10-20「INTEGRATE ABOVE INTO ONE CODE TO HANDLE ALL ABOVE. git pull」)=====
  # VRN-1 與 VRN-2 是兩個獨立系統、各有自己的 MAIN;本段只依序呼叫兩邊自己的入口,不改任何一邊的程式 / 冊 / 號(VCGC · VDF 不碰):
  #   ① VRN-1 倉:不在 → 從 GitHub 複製 · 在 → git pull(main · 只快轉 · 有沒提交的改動 → 先 git stash 保存,不丟)
  #   ② VRN-2 一鍵 v0145(從 GitHub 讀 · SHA-256 相符才執行 · 套件 v0145 = 啟動器 v0145 + runtime v0145:③ 取套件雜湊核對 · ④ ActivateVRN-2_v0145 單機閘 → ①~⑫(⑨ ⑩ ⑫ 灰 · 收尾驗證不上船)· 四點原文核對 · Workbench U/I 自動產出開啟 · ⑪ 驗證器 v0110 的 PIVOT)
  #   ③ VRN-1 MAIN(artifacts\VRN-1.ps1 · PowerShell 7 · 沒有就 winget 自動安裝):check → run --no-cache(樣本夾自動找 · G23 借 VRN-2 的段落標題 / OCR · 只寫輸出夾,不寫倉)
  #   ④ 總結:每一步的燈 · 借用結果 · 要人判(P21 待修的報告 · 待修清單)· GitHub Actions(有 gh 才查)· 結束碼(GREEN 0 / YELLOW 2 / RED 1)
  # 開關:$env:VIA_VRN1_ROOT(VRN-1 倉)· $env:VRN2_ROOT(VIA 根)· $env:VRN1_SAMPLES(VRN-1 樣本夾 · 不設 → $env:VIA_VRN_INPUT → C:\測試樣本報告)· $env:VRN1_OUT(VRN-1 輸出夾)
  #       $env:VRN1_ARGS(多給 VRN-1 run 的旗標 · 例 '--no-open')· $env:VRN_PAIR_NO_PULL = '1' 不拉 · $env:VRN_PAIR_NO_STASH = '1' 有改動就不拉
  #       $env:VRN_PAIR_SKIP = 'VRN-1' 或 'VRN-2' 這次跳過那一邊(另一邊照常)· $env:VRN_PAIR_NO_INSTALL = '1' 不自動裝 PowerShell 7 · $env:VRN_PAIR_NO_CLONE = '1' 不自動複製 VRN-1
  $ErrorActionPreference = 'Continue'
  try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch { }
  $V1 = if ($env:VIA_VRN1_ROOT) { $env:VIA_VRN1_ROOT } else { 'C:\Users\tonyk\VIA-VDF-VRN' }
  $R  = if ($env:VRN2_ROOT) { $env:VRN2_ROOT } else { 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics' }
  $Br = 'claude/optimistic-goodall-yhalc5'                                         # VRN-2 發行所在的 GitHub 分支(只讀取 · 讀不到 → main)
  $P2 = 'VeritasIntelligenceAnalytics/docs/handoff/ai/vrn2_release_v0145'
  $H2 = 'c834b06e87024a94b1bf143288542422429604cb5ffca8ff4086252625a96b12'   # VRN-2 一鍵 v0145 程式碼 SHA-256
  $U1 = 'https://github.com/tonykuni/VIA-VDF-VRN.git'                            # VRN-1 倉(只在本機沒有時複製)
  $env:VIA_VRN1_ROOT = $V1; $env:VIA_VRN2_ROOT = $R                                # 兩邊找對方都看同一個位置
  $skip = "$env:VRN_PAIR_SKIP"
  $res = [ordered]@{}
  $col = @{ GREEN = 'Green'; YELLOW = 'Yellow'; RED = 'Red'; GRAY = 'DarkGray' }
  $t0 = Get-Date
  function Say([string]$k, [string]$lamp, [string]$msg) {
    $res[$k] = @($lamp, $msg)
    Write-Host ("[{0}] {1} · {2}" -f $lamp, $k, $msg) -ForegroundColor $col[$lamp]
  }
  Write-Host ("══════ VRN-1 / VRN-2 操作員一鍵 v0106 · {0} · VRN-1 {1} · VIA {2} ══════" -f $t0.ToString('yyyy-MM-dd HH:mm:ss'), $V1, $R) -ForegroundColor Cyan

  # ① VRN-1 git pull
  $k1 = '① VRN-1 git pull'
  if ($skip -eq 'VRN-1') { Say $k1 GRAY '跳過(VRN_PAIR_SKIP=VRN-1)' }
  elseif (-not (Get-Command git -ErrorAction SilentlyContinue)) { Say $k1 RED '找不到 git(裝 Git for Windows 後再跑)' }
  elseif (-not (Test-Path -LiteralPath (Join-Path $V1 '.git')) -and (Test-Path -LiteralPath $V1) -and @(Get-ChildItem -Force -LiteralPath $V1 -ErrorAction SilentlyContinue).Count -gt 0) {
    Say $k1 RED "$V1 有東西但不是 git 倉(不動它)· 設 `$env:VIA_VRN1_ROOT = '<VRN-1 倉>' 後再跑" }
  elseif (-not (Test-Path -LiteralPath (Join-Path $V1 '.git'))) {
    if ($env:VRN_PAIR_NO_CLONE -eq '1') { Say $k1 RED "$V1 沒有 VRN-1 的倉 · VRN_PAIR_NO_CLONE=1 → 不複製 · 設 `$env:VIA_VRN1_ROOT 後再跑" }
    else {
      Write-Host "[計] $V1 沒有 VRN-1 的倉 → 從 GitHub 複製 $U1(main)" -ForegroundColor Yellow
      $okc = $false
      foreach ($w in 0, 2, 4, 8, 16) { if ($w) { Start-Sleep -Seconds $w }; git clone -q --branch main $U1 $V1 2>&1 | Out-Null; if ($LASTEXITCODE -eq 0) { $okc = $true; break } }
      if ($okc) { Say $k1 GREEN ("複製好了 · main {0} → {1}" -f "$(git -C $V1 rev-parse --short HEAD 2>$null)".Trim(), $V1) }
      else { Say $k1 RED "從 GitHub 複製 VRN-1 失敗(網路 / 權限)· 手動:git clone $U1 `"$V1`"" }
    }
  }
  elseif ($env:VRN_PAIR_NO_PULL -eq '1') { Say $k1 GRAY '不拉(VRN_PAIR_NO_PULL=1)· 照現狀跑' }
  else {
    $okf = $false
    foreach ($w in 0, 2, 4, 8, 16) { if ($w) { Start-Sleep -Seconds $w }; git -C $V1 fetch -q origin main 2>&1 | Out-Null; if ($LASTEXITCODE -eq 0) { $okf = $true; break } }
    $cur = "$(git -C $V1 rev-parse --abbrev-ref HEAD 2>$null)".Trim()
    $old = "$(git -C $V1 rev-parse --short HEAD 2>$null)".Trim()
    $dirty = @(git -C $V1 status --porcelain --untracked-files=no 2>$null | Where-Object { $_ })
    $untr = @(git -C $V1 status --porcelain --untracked-files=all 2>$null | Where-Object { $_ -like '??*' })   # Codex #564:未追蹤的檔另外數(留著不動 · 擋到 checkout 時 git 會拒絕 → 下面照實報)
    $note = @()
    if ($untr.Count -gt 0) { $note += "未追蹤的檔 $($untr.Count) 個留著不動(擋到切換時下面會說)" }
    if (-not $okf) { Say $k1 YELLOW "讀不到 GitHub(網路 / git)· 照本機現狀 $cur@$old 跑" }
    else {
      $go = $true
      if ($dirty.Count -gt 0) {
        if ($env:VRN_PAIR_NO_STASH -eq '1') { $go = $false; Say $k1 YELLOW "有 $($dirty.Count) 個沒提交的改動 · VRN_PAIR_NO_STASH=1 → 不拉 · 照現狀 $cur@$old 跑" }
        else {
          $tag = 'VRN1_VRN2_OneClick 自動暫存 ' + (Get-Date).ToString('yyyyMMdd_HHmmss')
          git -C $V1 stash push -q -m $tag 2>&1 | Out-Null
          if ($LASTEXITCODE -eq 0) { $note += "沒提交的改動 $($dirty.Count) 個已暫存「$tag」(要拿回來:git -C `"$V1`" stash pop)" }
          else { $go = $false; Say $k1 YELLOW "有 $($dirty.Count) 個沒提交的改動,暫存失敗 · 不拉 · 照現狀 $cur@$old 跑" }
        }
      }
      if ($go) {
        $onMain = ($cur -eq 'main')
        if (-not $onMain) {
          $sw = git -C $V1 switch -q main 2>&1
          if ($LASTEXITCODE -ne 0) { $sw2 = git -C $V1 switch -q -c main --track origin/main 2>&1; if ($LASTEXITCODE -ne 0 -and -not "$sw") { $sw = $sw2 } }   # 第一次失敗的理由優先(例:main 在別的 worktree)
          if ($LASTEXITCODE -eq 0 -and "$(git -C $V1 rev-parse --abbrev-ref HEAD 2>$null)".Trim() -eq 'main') { $onMain = $true; $note += "分支 $cur → main(原分支還在 · git switch - 切回)" }
          else { $note += ("切不到 main(" + ("$sw" -replace '\s+', ' ').Trim().Substring(0, [Math]::Min(120, ("$sw" -replace '\s+', ' ').Trim().Length)) + ")") }
        }
        $tail = $(if ($note.Count) { ' · ' + ($note -join ' · ') } else { '' })
        if (-not $onMain) { Say $k1 YELLOW ("切不到 main → 不拉 · 照現狀 {0}@{1} 跑{2}" -f $cur, $old, $tail) }   # Codex #564 P1:沒真的站在 main 就不 pull(不會把別的分支快轉到 main、也不會把分岔的分支當成最新)
        else {
          git -C $V1 pull -q --ff-only origin main 2>&1 | Out-Null
          $pr = $LASTEXITCODE
          $new = "$(git -C $V1 rev-parse --short HEAD 2>$null)".Trim()
          if ($pr -eq 0) { Say $k1 GREEN ("main {0} → {1}{2}" -f $old, $new, $tail) }
          else { Say $k1 YELLOW ("不能快轉(本機 main 有自己的提交 · 或未追蹤的檔擋住)· 照現狀 {0} 跑{1}" -f $new, $tail) }
        }
      }
    }
    $mf1 = Join-Path $V1 'functional modules\VRN\ssot\VRN_ToolManifest_v0100.json'
    if (Test-Path -LiteralPath $mf1) { Write-Host "    [計] VRN-1 借出工具冊在 $mf1" -ForegroundColor DarkGray }
    else { Write-Host '    [計] VRN-1 這一版沒有借出工具冊 → ② 的 ⑫ 會灰(VRN-2 照常)' -ForegroundColor Yellow }
  }

  # ② VRN-2 一鍵 v0145
  $k2 = '② VRN-2 一鍵 v0145'
  if ($skip -eq 'VRN-2') { Say $k2 GRAY '跳過(VRN_PAIR_SKIP=VRN-2)' }
  else {
    $top = "$(git -C $R rev-parse --show-toplevel 2>$null)".Trim()
    if (-not $top) { Say $k2 RED "$R 不是 git 倉或找不到 git · 設 `$env:VRN2_ROOT = '<VIA 根>' 後再跑" }
    else {
      $tmp = Join-Path ([IO.Path]::GetTempPath()) ('vrn12_' + (Get-Date).ToString('yyyyMMdd_HHmmss'))
      New-Item -ItemType Directory -Force -Path $tmp | Out-Null
      $z = Join-Path $tmp 'vrn2.zip'; $src = ''
      foreach ($b in $Br, 'main') {
        foreach ($w in 0, 2, 4, 8, 16) { if ($w) { Start-Sleep -Seconds $w }; git -C $top fetch -q origin $b 2>&1 | Out-Null; if ($LASTEXITCODE -eq 0) { break } }
        git -C $top archive --format=zip -o $z ('origin/' + $b + ':' + $P2) VRN2_OneClick_v0145.md 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $z)) { $src = $b; break }
      }
      if (-not $src) { Say $k2 RED "讀不到 GitHub 分支 $Br 或 main 的 VRN-2 一鍵 v0145(網路 / git)" }
      else {
        Expand-Archive -LiteralPath $z -DestinationPath $tmp -Force
        $md2 = [IO.File]::ReadAllText((Join-Path $tmp 'VRN2_OneClick_v0145.md'), [Text.Encoding]::UTF8) -replace "`r`n", "`n"
        $code2 = [regex]::Match($md2, '(?s)```powershell\n(.*?)\n```').Groups[1].Value
        $sha2 = -join ([Security.Cryptography.SHA256]::Create().ComputeHash([Text.Encoding]::UTF8.GetBytes($code2)) | ForEach-Object { $_.ToString('x2') })
        if ($sha2 -ne $H2) { Say $k2 RED ("VRN-2 一鍵程式碼 SHA-256 不對({0})· 不執行" -f $sha2.Substring(0, 12)) }
        else {
          Write-Host ("[計] VRN-2 一鍵 v0145 程式碼 SHA-256 {0} 相符(GitHub {1})→ 執行 VRN-2 自己的流程" -f $H2.Substring(0, 12), $src) -ForegroundColor DarkGray
          $global:LASTEXITCODE = 1
          & ([scriptblock]::Create($code2))
          $rc2 = [int]$global:LASTEXITCODE
          $l2 = if ($rc2 -eq 0) { 'GREEN' } elseif ($rc2 -eq 2) { 'YELLOW' } else { 'RED' }
          $pb = Join-Path $R 'VIA_Reports\vrn2\pivot\VRN2_Pivot_Borrow_latest.json'
          $p12 = '⑫ PIVOT 本輪沒寫(VRN-1 的工具借不到或不借 · 看上面 ⑫ 那行)'
          if ((Test-Path -LiteralPath $pb) -and (Get-Item -LiteralPath $pb).LastWriteTime -ge $t0.AddSeconds(-5)) {
            try { $pj = Get-Content -Raw -Encoding UTF8 -LiteralPath $pb | ConvertFrom-Json
                  $p12 = "⑫ PIVOT 借到 VRN-1 {0}(sha256 {1})· 事實 {2}/{3} · 年度 {4} 列 · 衝突 {5}" -f $pj.borrow.id, "$($pj.borrow.sha256)".Substring(0, 12), $pj.counts.kept, $pj.counts.facts, $pj.counts.pivot_report_annual, $pj.counts.conflicts } catch { }
          }
          Say $k2 $l2 ("結束碼 {0} · {1}" -f $rc2, $p12)
        }
      }
    }
  }

  # ③ VRN-1 MAIN
  $k3 = '③ VRN-1 MAIN'
  $todo = @()
  $ps1 = Join-Path $V1 'artifacts\VRN-1.ps1'
  if ($skip -eq 'VRN-1') { Say $k3 GRAY '跳過(VRN_PAIR_SKIP=VRN-1)' }
  elseif (-not (Test-Path -LiteralPath $ps1)) { Say $k3 RED "找不到 $ps1 · VRN-1 倉不在 $($V1) 的話設 `$env:VIA_VRN1_ROOT = '<VRN-1 倉>'" }
  else {
    $pwx = "$((Get-Command pwsh -ErrorAction SilentlyContinue | Select-Object -First 1).Source)"
    if (-not $pwx -and $env:ProgramFiles -and (Test-Path -LiteralPath (Join-Path $env:ProgramFiles 'PowerShell\7\pwsh.exe'))) { $pwx = Join-Path $env:ProgramFiles 'PowerShell\7\pwsh.exe' }
    if (-not $pwx -and $env:VRN_PAIR_NO_INSTALL -ne '1' -and (Get-Command winget -ErrorAction SilentlyContinue)) {
      Write-Host '[計] VRN-1 要 PowerShell 7 · 這台沒有 → winget 安裝 Microsoft.PowerShell(只裝一次)' -ForegroundColor Yellow
      winget install --id Microsoft.PowerShell --exact --silent --accept-source-agreements --accept-package-agreements 2>&1 | ForEach-Object { Write-Host "    $_" }
      if ($env:ProgramFiles -and (Test-Path -LiteralPath (Join-Path $env:ProgramFiles 'PowerShell\7\pwsh.exe'))) { $pwx = Join-Path $env:ProgramFiles 'PowerShell\7\pwsh.exe' }
    }
    $smp = ''
    foreach ($c in @($env:VRN1_SAMPLES, $env:VIA_VRN_INPUT, 'C:\測試樣本報告')) { if ($c -and (Test-Path -LiteralPath $c)) { $smp = $c; break } }
    if (-not $pwx) {
      $why = if ($env:VRN_PAIR_NO_INSTALL -eq '1') { 'VRN_PAIR_NO_INSTALL=1 → 不自動裝' } elseif (-not (Get-Command winget -ErrorAction SilentlyContinue)) { '這台沒有 winget(Microsoft Store 的「應用程式安裝程式」)· 到 https://aka.ms/powershell 下載安裝' } else { 'winget 安裝沒成功' }
      Say $k3 RED ('VRN-1 要 PowerShell 7(pwsh)· ' + $why + ' · 手動:winget install --id Microsoft.PowerShell · 裝好再貼一次') }
    else {
      $pw = [pscustomobject]@{ Source = $pwx }
      if ($smp) { Write-Host "    [計] VRN-1 樣本夾 $smp" -ForegroundColor DarkGray } else { Write-Host '    [計] 找不到樣本夾(VRN1_SAMPLES / VIA_VRN_INPUT / C:\測試樣本報告 都不在)→ 交給 VRN-1 自己決定' -ForegroundColor Yellow }
      Write-Host '──── VRN-1 check ────' -ForegroundColor Cyan
      & $pw.Source -NoProfile -ExecutionPolicy Bypass -WorkingDirectory $V1 -File $ps1 check 2>&1 | ForEach-Object { Write-Host "$_" }
      $rcC = [int]$LASTEXITCODE
      $a1 = @('run', '--no-cache')
      if ($smp) { $a1 += @('--samples', $smp) }
      if ($env:VRN1_OUT) { $a1 += @('--out', $env:VRN1_OUT) }
      if ($env:VRN1_ARGS) { $a1 += @($env:VRN1_ARGS -split ' ' | Where-Object { $_ }) }
      Write-Host ('──── VRN-1 ' + ($a1 -join ' ') + ' ────') -ForegroundColor Cyan
      $runL = New-Object System.Collections.Generic.List[string]
      & $pw.Source -NoProfile -ExecutionPolicy Bypass -WorkingDirectory $V1 -File $ps1 @a1 2>&1 | ForEach-Object { Write-Host "$_"; $runL.Add("$_") }
      $rcR = [int]$LASTEXITCODE
      $done = "$($runL | Where-Object { $_ -match '\[收尾\]' } | Select-Object -Last 1)".Trim()
      $gate = ''
      $rp = [regex]::Match(($runL -join "`n"), '\[DONE\][^\n]*?·\s*([^·\n]*?VRN_AutoTest_Report\.json)').Groups[1].Value
      if ($rp -and (Test-Path -LiteralPath $rp)) {
        try {
          $rows = @((Get-Content -Raw -Encoding UTF8 -LiteralPath $rp | ConvertFrom-Json).rounds[-1].rows)
          $b23 = @($rows | Where-Object { "$($_.gate)" -like 'G23*' -and "$($_.name)" -like '借 *' })
          $gate = ' · G23 借到 {0}/{1} · G21 {2} · G22 {3}' -f @($b23 | Where-Object { $_.status -eq 'PASS' }).Count, $b23.Count,
                  "$(@($rows | Where-Object { "$($_.gate)" -like 'G21*' } | ForEach-Object { $_.status }) -join '/')",
                  "$(@($rows | Where-Object { "$($_.gate)" -like 'G22*' } | ForEach-Object { $_.status }) -join '/')"
          $mr = Join-Path (Split-Path -Parent (Split-Path -Parent $rp)) 'VRN_Main_Report_v0100.json'
          if (Test-Path -LiteralPath $mr) {
            $p21 = @((Get-Content -Raw -Encoding UTF8 -LiteralPath $mr | ConvertFrom-Json).rows | Where-Object { "$($_.gate)" -like 'P21*' } | Select-Object -First 1)
            if ($p21.Count -and $p21[0].status -ne 'PASS') { $todo += ('VRN-1 P21 ' + "$($p21[0].item)" + ' · ' + "$($p21[0].detail)") }
          }
          $fx = Get-ChildItem -LiteralPath (Split-Path -Parent $rp) -Recurse -Filter 'VRN_FixList_Paste_v0100.txt' -ErrorAction SilentlyContinue | Select-Object -First 1
          if ($fx) { $todo += ('VRN-1 待修清單(要人判的列標 · 沒有年度表的報告 · 影像檔)' + $fx.FullName) }
        } catch { }
      }
      $l3 = if ($rcR -ne 0) { 'RED' } elseif ($done -match '完成' -and $rcC -eq 0) { 'GREEN' } else { 'YELLOW' }
      Say $k3 $l3 ("check rc {0} · run rc {1}{2} · {3}" -f $rcC, $rcR, $gate, $(if ($done) { $done } else { '沒看到收尾那行' }))
    }
  }

  # ④ 總結
  $d = [int]((Get-Date) - $t0).TotalSeconds
  Write-Host ('══════ 總結 · {0} 秒 ══════' -f $d) -ForegroundColor Cyan
  foreach ($k in $res.Keys) { Write-Host ("[{0}] {1} · {2}" -f $res[$k][0], $k, $res[$k][1]) -ForegroundColor $col[$res[$k][0]] }
  $gh = Get-Command gh -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($gh) {
    $ga = ''
    try {
      $gj = (& $gh.Source run list -R tonykuni/VIA-VDF-VRN --branch main -L 1 --json conclusion,status,createdAt,workflowName 2>$null) -join "`n"
      if ($gj) { $g0 = @($gj | ConvertFrom-Json)[0]; if ($g0) { $ga = '{0} · {1} · {2} · {3}' -f $g0.workflowName, $g0.status, $g0.conclusion, $g0.createdAt } }
    } catch { }
    if ($ga) { $todo += ('VRN-1 倉 main 最近一次 GitHub Actions:' + $ga + $(if ($ga -match 'failure') { ' → 若一直幾秒就失敗(沒有日誌),到 GitHub 倉 Settings → Actions 與 Billing 看是不是額度用完或被停用' } else { '' })) }
  }
  if ($todo.Count) {
    Write-Host '──── 要人判(程式不替你決定)────' -ForegroundColor Yellow
    foreach ($x in $todo) { Write-Host "  · $x" -ForegroundColor Yellow }
  }
  $lamps = @($res.Values | ForEach-Object { $_[0] })
  $final = if ($lamps -contains 'RED') { 'RED' } elseif ($lamps -contains 'YELLOW' -or $skip) { 'YELLOW' } else { 'GREEN' }   # Codex #564 P2:有一邊被 VRN_PAIR_SKIP 跳過 → 不是「兩邊都跑完」· 最多黃
  $msg = @{ GREEN = '兩個系統都跑完 · VRN-1 已是最新 main · VRN-2 ⑫ 借 VRN-1 的 PIVOT · VRN-1 G23 借 VRN-2 的段落標題 / OCR · 把總結這幾行貼回'
            YELLOW = $(if ($skip) { "這次只跑了 $(if ($skip -eq 'VRN-1') { 'VRN-2' } else { 'VRN-1' })(VRN_PAIR_SKIP=$skip)· 不算兩邊都完成 · 把總結這幾行貼回" } else { '跑完但有黃燈 · 看上面黃的那一步(說明裡有下一步)· 把總結這幾行貼回' })
            RED = '有一步是紅的 · 照那一行的說明修好再貼一次(另一邊照常跑完)· 把總結這幾行貼回' }[$final]
  Write-Host ("NEXT: [{0}] {1}" -f $final, $msg) -ForegroundColor $col[$final]
  $global:LASTEXITCODE = @{ GREEN = 0; YELLOW = 2; RED = 1 }[$final]
}
```

## 一行的原始碼(`-EncodedCommand` 解碼後 · 只讀取並核對 · 不改任何檔)

```text
$ErrorActionPreference = 'Continue'
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch { }
$R  = if ($env:VRN2_ROOT) { $env:VRN2_ROOT } else { 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics' }
$Br = 'claude/optimistic-goodall-yhalc5'
$P  = 'VeritasIntelligenceAnalytics/docs/handoff/ai/vrn1_vrn2_oneclick_v0106'
$H  = 'b625cfbc6a3de4c41dd73082021f49585157974cc6b9e232d2f1c9b943ef29ca'
Write-Host ('[VRN-1 / VRN-2] PowerShell ' + $PSVersionTable.PSVersion + ' · 從 GitHub 讀操作員一鍵 v0106(核對 SHA-256 後執行)') -ForegroundColor Yellow
$top = git -C $R rev-parse --show-toplevel 2>$null
if (-not $top) { Write-Host "[RED] $R 不是 git 倉或找不到 git" -ForegroundColor Red; exit 1 }
$top = "$top".Trim()
$t = Join-Path ([IO.Path]::GetTempPath()) ('vrn12_boot_' + (Get-Date).ToString('yyyyMMdd_HHmmss'))
New-Item -ItemType Directory -Force -Path $t | Out-Null
$z = Join-Path $t 'pair.zip'; $okz = $false
foreach ($b in $Br, 'main') {
  foreach ($w in 0, 2, 4, 8, 16) { if ($w) { Start-Sleep -Seconds $w }; git -C $top fetch -q origin $b 2>&1 | Out-Null; if ($LASTEXITCODE -eq 0) { break } }
  git -C $top archive --format=zip -o $z ('origin/' + $b + ':' + $P) VRN1_VRN2_OneClick_v0106.md 2>&1 | Out-Null
  if ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $z)) { $okz = $true; Write-Host ('[計] 一鍵程式碼來源 GitHub ' + $b) -ForegroundColor DarkGray; break }
}
if (-not $okz) { Write-Host "[RED] 讀不到 GitHub 分支 $Br 或 main 的操作員一鍵(網路 / git)" -ForegroundColor Red; exit 1 }
Expand-Archive -LiteralPath $z -DestinationPath $t -Force
$md = [IO.File]::ReadAllText((Join-Path $t 'VRN1_VRN2_OneClick_v0106.md'), [Text.Encoding]::UTF8) -replace "`r`n", "`n"
$code = [regex]::Match($md, '(?s)```powershell\n(.*?)\n```').Groups[1].Value
$sha = -join ([Security.Cryptography.SHA256]::Create().ComputeHash([Text.Encoding]::UTF8.GetBytes($code)) | ForEach-Object { $_.ToString('x2') })
if ($sha -ne $H) { Write-Host "[RED] 一鍵程式碼 SHA-256 不對($sha)· 不執行" -ForegroundColor Red; exit 1 }
Write-Host ('[GREEN] 一鍵程式碼 SHA-256 ' + $H.Substring(0, 12) + ' 相符 → 執行') -ForegroundColor Green
$global:LASTEXITCODE = 1
try { & ([scriptblock]::Create($code)) } catch { Write-Host ('[RED] 一鍵執行中斷(未攔截的例外):' + $_.Exception.Message) -ForegroundColor Red; $global:LASTEXITCODE = 1 }
exit $(if ($null -ne $global:LASTEXITCODE) { [int]$global:LASTEXITCODE } else { 1 })   # Codex #564:最終燈帶回 cmd 的 %ERRORLEVEL%(GREEN 0 · YELLOW 2 · RED 1)· 紅燈 / 例外 → 1
```
