# VRN-2 一鍵 v0133(cmd / PowerShell 都能貼 · 啟動器 v0133 · 前後端連結 · U/I 用 window I/O 選輸入)

v0133 = 操作員令(2026-10-21)「用 ActivateVRN-2.ps1 啟動前後端並連結 · 讓使用者在 HTML 上用 window I/O 輸入檔案夾或檔案(pdf / word / txt / image / 檔案夾)·
分三種:個股報告/訊息 · 產業報告/展望 · 其他投資報告 · 現在進行的是個股報告/訊息,其他功能關閉 · 留意是否都有註冊成功」。
啟動器 `ActivateVRN-2.py` **v0133**(SHA-256 `d9411dcb333ba253dfc5eb640ddcf5ed3ae6a75f5b0000e25708276d06f45c10` · 從 `vrn2_release_v0133` 取)。這份程式碼就是操作員說的 **ActivateVRN-2.ps1**:
存成 `ActivateVRN-2.ps1` 跑也可以;貼進 PowerShell 跑也可以;下面那一行(cmd 也能貼)會從 GitHub 讀本檔再核對 SHA-256 才執行。

| 步驟 | v0133 改了什麼 |
|---|---|
| ③ / ④ | 取得啟動器 v0133(雜湊核對)→ 執行 ①~⑫(前端 = `VIA_Reports\vrn2\VRN2_UI_latest.html` · 後端 = vrn2:// 協定處理器 `VRN2_UIAction_v0103.py` + 啟動器)|
| ②b(啟動器)| 輸入來源:`$env:VRN2_SOURCE` / `--source` > U/I 選的 `VRN2_Input_latest.json` > `VRN2_SSOT` 來源夾 > 預設 `C:\測試樣本報告`;寫新一版 VRN2_SSOT(管理器不動)· 稽核(PDF / Word / TXT / 影像 · 個股範圍 / 範圍外)|
| ⑥c(啟動器)| vrn2:// 註冊到 HKCU 指向處理器 v0103 · **寫完讀回核對** |
| ⑫b(啟動器)| U/I 左側多一塊「輸入(window I/O)」:三類(只有 個股報告/訊息 可選 · 另外兩類灰掉「尚未開放」)· 📁 選擇檔案夾 · 📄 選擇檔案(pdf / word / txt / 影像)· 🔎 重新稽核 |
| ⑤b(本一鍵)| 前後端連結檢查:HKCU 的 vrn2:// 解析成 python + 處理器,處理器整條路徑 = 本機 VRN-2 程式夾的 `VRN2_UIAction_v0103.py` 且檔在、python 檔在 · U/I 有輸入區塊 · 印目前輸入與稽核 · **⑤b 的燈併進最後 NEXT**(紅 → 紅 · 黃 → 最多黃;GREEN / rc 0 只在前後端真的接上時)|

在 U/I 上的用法:左側「輸入」→ 📁 選擇檔案夾…(Windows 對話框)→ 選 `C:\測試樣本報告` → 區塊立刻顯示稽核 → 按「▶ 完整重跑」。
非 PDF(word / txt / 影像)會被收下並照實記「本版主體只擷取 PDF」(不假裝有處理);產業報告/展望 · 其他投資報告 兩類關閉(處理器也拒絕)。
VRN-2 主體(管理器鏈 v0231 → v0239 · ENG397 · 摘要器 · 獨立驗證器 · 工具橋 v0101 · OCR 橋)**一個位元組都不動**;新增處理器 v0103(v0102 留著)。

開關:`$env:VRN2_SOURCE = 'C:\測試樣本報告'` 直接指定來源夾 · 檔頭 `$NoPush = $true` 只實測不上船 · `$Verify = $false` 啟動器沒驗到時 PS 也不補驗 · `$env:VIA_VRN2_NO_VERIFY = '1'` 不跑 ⑪ · `$env:VIA_VRN2_NO_BORROW = '1'` ⑫ 不借 VRN-1。

## 在「命令提示字元(cmd)」或 PowerShell 都能貼的一行(建議用這個)

這一行在 cmd 或 PowerShell 貼上都可以:它開 Windows PowerShell → 從 GitHub 分支 `claude/optimistic-goodall-yhalc5`(讀不到 → `main`)讀本檔的一鍵程式碼 → **核對 SHA-256** → 才執行(不改任何檔 · 不切換分支)。

```bat
powershell -NoProfile -ExecutionPolicy Bypass -EncodedCommand JABFAHIAcgBvAHIAQQBjAHQAaQBvAG4AUAByAGUAZgBlAHIAZQBuAGMAZQAgAD0AIAAnAEMAbwBuAHQAaQBuAHUAZQAnAAoAdAByAHkAIAB7ACAAWwBDAG8AbgBzAG8AbABlAF0AOgA6AE8AdQB0AHAAdQB0AEUAbgBjAG8AZABpAG4AZwAgAD0AIABbAFQAZQB4AHQALgBFAG4AYwBvAGQAaQBuAGcAXQA6ADoAVQBUAEYAOAAgAH0AIABjAGEAdABjAGgAIAB7ACAAfQAKACQAUgAgACAAPQAgAGkAZgAgACgAJABlAG4AdgA6AFYAUgBOADIAXwBSAE8ATwBUACkAIAB7ACAAJABlAG4AdgA6AFYAUgBOADIAXwBSAE8ATwBUACAAfQAgAGUAbABzAGUAIAB7ACAAJwBDADoAXABVAHMAZQByAHMAXAB0AG8AbgB5AGsAXABPAG4AZQBEAHIAaQB2AGUAXABEAG8AYwB1AG0AZQBuAHQAcwBcAG0AbwB2AGkAZQBzAC0AZABhAHQAYQBzAGUAdABcAFYAZQByAGkAdABhAHMASQBuAHQAZQBsAGwAaQBnAGUAbgBjAGUAQQBuAGEAbAB5AHQAaQBjAHMAJwAgAH0ACgAkAEIAcgAgAD0AIAAnAGMAbABhAHUAZABlAC8AbwBwAHQAaQBtAGkAcwB0AGkAYwAtAGcAbwBvAGQAYQBsAGwALQB5AGgAYQBsAGMANQAnAAoAJABQACAAIAA9ACAAJwBWAGUAcgBpAHQAYQBzAEkAbgB0AGUAbABsAGkAZwBlAG4AYwBlAEEAbgBhAGwAeQB0AGkAYwBzAC8AZABvAGMAcwAvAGgAYQBuAGQAbwBmAGYALwBhAGkALwB2AHIAbgAyAF8AcgBlAGwAZQBhAHMAZQBfAHYAMAAxADMAMwAnAAoAJABIACAAIAA9ACAAJwAyADEAYQBiADkAMAAwAGEAYgBmAGQAMAA4ADMAMwBjAGMAYwBhAGUAYgA2ADkAMgA5ADgAZAA4ADAAZQBjADUANwBkAGQAOQBlAGYAZgAxADUAMAAyADcANgAzAGMANwA4ADYAMQA0ADIANgA0ADIAMgA0AGIANgA3ADIAZABkACcACgBXAHIAaQB0AGUALQBIAG8AcwB0ACAAKAAnAFsAVgBSAE4ALQAyAF0AIABQAG8AdwBlAHIAUwBoAGUAbABsACAAJwAgACsAIAAkAFAAUwBWAGUAcgBzAGkAbwBuAFQAYQBiAGwAZQAuAFAAUwBWAGUAcgBzAGkAbwBuACAAKwAgACcAIAC3ACAAnl8gAEcAaQB0AEgAdQBiACAAgIsATnWTIAB2ADAAMQAzADMAIAALeg9fvHgoADhoDVwgAFMASABBAC0AMgA1ADYAIACMX/dXTIgpACcAKQAgAC0ARgBvAHIAZQBnAHIAbwB1AG4AZABDAG8AbABvAHIAIABZAGUAbABsAG8AdwAKACQAdABvAHAAIAA9ACAAZwBpAHQAIAAtAEMAIAAkAFIAIAByAGUAdgAtAHAAYQByAHMAZQAgAC0ALQBzAGgAbwB3AC0AdABvAHAAbABlAHYAZQBsACAAMgA+ACQAbgB1AGwAbAAKAGkAZgAgACgALQBuAG8AdAAgACQAdABvAHAAKQAgAHsAIABXAHIAaQB0AGUALQBIAG8AcwB0ACAAIgBbAFIARQBEAF0AIAAkAFIAIAANTi9mIABnAGkAdAAgAAlQFmJ+Yg1OMFIgAGcAaQB0ACIAIAAtAEYAbwByAGUAZwByAG8AdQBuAGQAQwBvAGwAbwByACAAUgBlAGQAOwAgAHIAZQB0AHUAcgBuACAAfQAKACQAdABvAHAAIAA9ACAAIgAkAHQAbwBwACIALgBUAHIAaQBtACgAKQAKACQAdAAgAD0AIABKAG8AaQBuAC0AUABhAHQAaAAgACgAWwBJAE8ALgBQAGEAdABoAF0AOgA6AEcAZQB0AFQAZQBtAHAAUABhAHQAaAAoACkAKQAgACgAJwB2AHIAbgAyAF8AYgBvAG8AdABfACcAIAArACAAKABHAGUAdAAtAEQAYQB0AGUAKQAuAFQAbwBTAHQAcgBpAG4AZwAoACcAeQB5AHkAeQBNAE0AZABkAF8ASABIAG0AbQBzAHMAJwApACkACgBOAGUAdwAtAEkAdABlAG0AIAAtAEkAdABlAG0AVAB5AHAAZQAgAEQAaQByAGUAYwB0AG8AcgB5ACAALQBGAG8AcgBjAGUAIAAtAFAAYQB0AGgAIAAkAHQAIAB8ACAATwB1AHQALQBOAHUAbABsAAoAJAB6ACAAPQAgAEoAbwBpAG4ALQBQAGEAdABoACAAJAB0ACAAJwBvAG4AZQBjAGwAaQBjAGsALgB6AGkAcAAnADsAIAAkAG8AawB6ACAAPQAgACQAZgBhAGwAcwBlAAoAZgBvAHIAZQBhAGMAaAAgACgAJABiACAAaQBuACAAJABCAHIALAAgACcAbQBhAGkAbgAnACkAIAB7AAoAIAAgAGYAbwByAGUAYQBjAGgAIAAoACQAdwAgAGkAbgAgADAALAAgADIALAAgADQALAAgADgALAAgADEANgApACAAewAgAGkAZgAgACgAJAB3ACkAIAB7ACAAUwB0AGEAcgB0AC0AUwBsAGUAZQBwACAALQBTAGUAYwBvAG4AZABzACAAJAB3ACAAfQA7ACAAZwBpAHQAIAAtAEMAIAAkAHQAbwBwACAAZgBlAHQAYwBoACAALQBxACAAbwByAGkAZwBpAG4AIAAkAGIAIAAyAD4AJgAxACAAfAAgAE8AdQB0AC0ATgB1AGwAbAA7ACAAaQBmACAAKAAkAEwAQQBTAFQARQBYAEkAVABDAE8ARABFACAALQBlAHEAIAAwACkAIAB7ACAAYgByAGUAYQBrACAAfQAgAH0ACgAgACAAZwBpAHQAIAAtAEMAIAAkAHQAbwBwACAAYQByAGMAaABpAHYAZQAgAC0ALQBmAG8AcgBtAGEAdAA9AHoAaQBwACAALQBvACAAJAB6ACAAKAAnAG8AcgBpAGcAaQBuAC8AJwAgACsAIAAkAGIAIAArACAAJwA6ACcAIAArACAAJABQACkAIABWAFIATgAyAF8ATwBuAGUAQwBsAGkAYwBrAF8AdgAwADEAMwAzAC4AbQBkACAAMgA+ACYAMQAgAHwAIABPAHUAdAAtAE4AdQBsAGwACgAgACAAaQBmACAAKAAkAEwAQQBTAFQARQBYAEkAVABDAE8ARABFACAALQBlAHEAIAAwACAALQBhAG4AZAAgACgAVABlAHMAdAAtAFAAYQB0AGgAIAAtAEwAaQB0AGUAcgBhAGwAUABhAHQAaAAgACQAegApACkAIAB7ACAAJABvAGsAegAgAD0AIAAkAHQAcgB1AGUAOwAgAFcAcgBpAHQAZQAtAEgAbwBzAHQAIAAoACcAWwAIil0AIAAATnWTC3oPX7x4hk+QbiAARwBpAHQASAB1AGIAIAAnACAAKwAgACQAYgApACAALQBGAG8AcgBlAGcAcgBvAHUAbgBkAEMAbwBsAG8AcgAgAEQAYQByAGsARwByAGEAeQA7ACAAYgByAGUAYQBrACAAfQAKAH0ACgBpAGYAIAAoAC0AbgBvAHQAIAAkAG8AawB6ACkAIAB7ACAAVwByAGkAdABlAC0ASABvAHMAdAAgACIAWwBSAEUARABdACAAgIsNTjBSIABHAGkAdABIAHUAYgAgAAZSL2UgACQAQgByACAAFmIgAG0AYQBpAG4AIACEdgBOdZMLeg9fvHgoALJ9740gAC8AIABnAGkAdAApACIAIAAtAEYAbwByAGUAZwByAG8AdQBuAGQAQwBvAGwAbwByACAAUgBlAGQAOwAgAHIAZQB0AHUAcgBuACAAfQAKAEUAeABwAGEAbgBkAC0AQQByAGMAaABpAHYAZQAgAC0ATABpAHQAZQByAGEAbABQAGEAdABoACAAJAB6ACAALQBEAGUAcwB0AGkAbgBhAHQAaQBvAG4AUABhAHQAaAAgACQAdAAgAC0ARgBvAHIAYwBlAAoAJABtAGQAIAA9ACAAWwBJAE8ALgBGAGkAbABlAF0AOgA6AFIAZQBhAGQAQQBsAGwAVABlAHgAdAAoACgASgBvAGkAbgAtAFAAYQB0AGgAIAAkAHQAIAAnAFYAUgBOADIAXwBPAG4AZQBDAGwAaQBjAGsAXwB2ADAAMQAzADMALgBtAGQAJwApACwAIABbAFQAZQB4AHQALgBFAG4AYwBvAGQAaQBuAGcAXQA6ADoAVQBUAEYAOAApACAALQByAGUAcABsAGEAYwBlACAAIgBgAHIAYABuACIALAAgACIAYABuACIACgAkAGMAbwBkAGUAIAA9ACAAWwByAGUAZwBlAHgAXQA6ADoATQBhAHQAYwBoACgAJABtAGQALAAgACcAKAA/AHMAKQBgAGAAYABwAG8AdwBlAHIAcwBoAGUAbABsAFwAbgAoAC4AKgA/ACkAXABuAGAAYABgACcAKQAuAEcAcgBvAHUAcABzAFsAMQBdAC4AVgBhAGwAdQBlAAoAJABzAGgAYQAgAD0AIAAtAGoAbwBpAG4AIAAoAFsAUwBlAGMAdQByAGkAdAB5AC4AQwByAHkAcAB0AG8AZwByAGEAcABoAHkALgBTAEgAQQAyADUANgBdADoAOgBDAHIAZQBhAHQAZQAoACkALgBDAG8AbQBwAHUAdABlAEgAYQBzAGgAKABbAFQAZQB4AHQALgBFAG4AYwBvAGQAaQBuAGcAXQA6ADoAVQBUAEYAOAAuAEcAZQB0AEIAeQB0AGUAcwAoACQAYwBvAGQAZQApACkAIAB8ACAARgBvAHIARQBhAGMAaAAtAE8AYgBqAGUAYwB0ACAAewAgACQAXwAuAFQAbwBTAHQAcgBpAG4AZwAoACcAeAAyACcAKQAgAH0AKQAKAGkAZgAgACgAJABzAGgAYQAgAC0AbgBlACAAJABIACkAIAB7ACAAVwByAGkAdABlAC0ASABvAHMAdAAgACIAWwBSAEUARABdACAAAE51kwt6D1+8eCAAUwBIAEEALQAyADUANgAgAA1ODVwoACQAcwBoAGEAKQC3ACAADU73V0yIIgAgAC0ARgBvAHIAZQBnAHIAbwB1AG4AZABDAG8AbABvAHIAIABSAGUAZAA7ACAAcgBlAHQAdQByAG4AIAB9AAoAVwByAGkAdABlAC0ASABvAHMAdAAgACgAJwBbAEcAUgBFAEUATgBdACAAAE51kwt6D1+8eCAAUwBIAEEALQAyADUANgAgACcAIAArACAAJABIAC4AUwB1AGIAcwB0AHIAaQBuAGcAKAAwACwAIAAxADIAKQAgACsAIAAnACAA+HYmeyAAkiEgAChXIABQAG8AdwBlAHIAUwBoAGUAbABsACAA4Yj3V0yIJwApACAALQBGAG8AcgBlAGcAcgBvAHUAbgBkAEMAbwBsAG8AcgAgAEcAcgBlAGUAbgAKACYAIAAoAFsAcwBjAHIAaQBwAHQAYgBsAG8AYwBrAF0AOgA6AEMAcgBlAGEAdABlACgAJABjAG8AZABlACkAKQAKAGUAeABpAHQAIAAkACgAaQBmACAAKAAkAG4AdQBsAGwAIAAtAG4AZQAgACQAZwBsAG8AYgBhAGwAOgBMAEEAUwBUAEUAWABJAFQAQwBPAEQARQApACAAewAgAFsAaQBuAHQAXQAkAGcAbABvAGIAYQBsADoATABBAFMAVABFAFgASQBUAEMATwBEAEUAIAB9ACAAZQBsAHMAZQAgAHsAIAAwACAAfQApACAAIAAgACMAIAB2ADAAMQAzADMAKABDAG8AZABlAHgAIAAjADUANQAwACkAOgBOAEUAWABUACAAhHbIcTZe3lYZkAtQUFtMiAt6hHYgAHIAYwAoAEcAUgBFAEUATgAgADAAIAC3ACAAWQBFAEwATABPAFcAIAAyACAAtwAgAFIARQBEACAAMQAgAJIhIABjAG0AZAAgAIR2IAAlAEUAUgBSAE8AUgBMAEUAVgBFAEwAJQApAAoA
```

或:在 cmd 先輸入 `powershell` 按 Enter(提示字元變成 `PS C:\Users\tonyk>`),再貼下面整段程式碼(或存成 `ActivateVRN-2.ps1` 後 `powershell -ExecutionPolicy Bypass -File ActivateVRN-2.ps1`)。

程式碼 SHA-256(本文 · 一行核對的就是這個):`21ab900abfd0`

```powershell
& {
  # ===== VRN-2 一鍵 v0133(啟動器 v0133 · 前後端連結:U/I 左側「輸入(window I/O)」→ vrn2://pick 開 Windows 對話框選檔案夾 / 檔案(pdf · word · txt · 影像)→ 稽核 → 當來源夾 · 三類只開「個股報告/訊息」· ⑤b 檢查 vrn2:// 註冊與 U/I 區塊 · $env:VRN2_SOURCE 直接指定來源夾)· v0132(工具橋 v0101:借不到 VRN-1 的工具時說清楚下一步 · VRN-1 / VRN-2 / VDF / VCGC 各自獨立)· v0131(工具相互取用:② 借出工具冊 · ⑫ 借 VRN-1 的 PIVOT 資料庫工具 · VRN-2 主體不動)· v0130 判定(⑪ 報告三段都看 · PS 自驗只驗本輪的冊 · 成功看本輪 ⑧ 完成燈)· v0129 一鍵全流程(依 MAIN 登記紀錄定位程式夾 · U/I「驗證過的輸出」· 啟動器 ⑪ 背景獨立驗證寫回 U/I · 一格整列拆開 · 重複列只留一筆 · 表頭列移出 · 段落標題同一欄 · 驗證器 v0102):① CPU / DRAM → ② PS 加速器 → ③ 取得 v0129(GitHub 分支 · SHA-256 驗證 · 舊版留備份)→ ③b 定位 VRN-2 程式夾(VIA 根 · MAIN 成功紀錄 · VIA_ROOT · 倉裡找)→ ④ 執行(啟動器 ①~⑪ · 完成後自動上船 · 驗證寫回後開 U/I)→ ⑤ 摘要 · 印驗證摘要(啟動器沒驗到才自己驗)→ NEXT =====
  # 只增不減:不刪任何檔(舊啟動器改名備份)· 不動別的系統(VCGC / VDF)的檔 · 驗證只讀 · 報告寫在 VIA_Reports\vrn2\verify_independent
  $R      = if ($env:VRN2_ROOT)  { $env:VRN2_ROOT }  else { "C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics" }   # VIA 根
  $A      = if ($env:VRN2_LAUNCHER) { $env:VRN2_LAUNCHER } else { Join-Path $env:USERPROFILE 'Downloads\ActivateVRN-2.py' }                   # 啟動器位置
  $Br     = 'claude/optimistic-goodall-yhalc5'                                    # v0133 發行所在的 GitHub 分支(只讀取 · 不切換分支 · 讀不到 → 改讀 main)
  $RelP   = 'VeritasIntelligenceAnalytics/docs/handoff/ai/vrn2_release_v0133'     # 發行夾(repo 根起算)
  $Want   = 'd9411dcb333ba253dfc5eb640ddcf5ed3ae6a75f5b0000e25708276d06f45c10'   # ActivateVRN-2 v0133 SHA-256
  $NoPush = $false        # $true = 只實測不上船
  $Verify = $true         # 啟動器 ⑪ 沒驗到(例:舊版 / 中斷)時 PS 自己用落地的驗證器驗(只讀)
  $LArgs  = @(); if ($env:VRN2_LAUNCHER_ARGS) { $LArgs = $env:VRN2_LAUNCHER_ARGS -split ' ' }   # 例:--no-install
  if ($env:VRN2_SOURCE) { $LArgs += @('--source', $env:VRN2_SOURCE) }                        # v0133 直接指定來源夾(例:C:\測試樣本報告)· 沒設就用 U/I 選的 / VRN2_SSOT / 預設
  $ErrorActionPreference = 'Continue'
  try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch { }
  $env:PYTHONIOENCODING = 'utf-8'; $env:PYTHONUTF8 = '1'
  $t0 = Get-Date; $tmp = Join-Path ([IO.Path]::GetTempPath()) ("vrn2_v0133_" + $t0.ToString('yyyyMMdd_HHmmss')); New-Item -ItemType Directory -Force -Path $tmp | Out-Null
  function Say($lamp, $msg) { $c = @{ GREEN = 'Green'; YELLOW = 'Yellow'; RED = 'Red'; GRAY = 'DarkGray' }[$lamp]; Write-Host ("[{0}] {1}" -f $lamp, $msg) -ForegroundColor $c }
  $me = Get-Process -Id $PID; $prio0 = $me.PriorityClass; $via0 = $env:VIA_ROOT
  try {
    # ① 第一步:CPU / DRAM(CPU 閒 <60% → 本視窗升「高於標準」· 子行程繼承 · 結束還原)+ 釋放記憶體
    $cpu = $null; $ram = $null
    try { $cpu = [int](Get-CimInstance Win32_Processor -ErrorAction Stop | Measure-Object LoadPercentage -Average).Average } catch { }
    try { $ram = [math]::Round((Get-CimInstance Win32_OperatingSystem -ErrorAction Stop).FreePhysicalMemory / 1MB, 1) } catch { }
    if ($cpu -ne $null -and $cpu -lt 60) { try { $me.PriorityClass = 'AboveNormal' } catch { } }
    [GC]::Collect(); [GC]::WaitForPendingFinalizers()
    Say GREEN ("① CPU / DRAM · CPU {0} · 可用 RAM {1} · 優先權 {2} → {3}" -f $(if ($cpu -ne $null) { "$cpu%" } else { '量不到' }), $(if ($ram -ne $null) { "$ram GB" } else { '量不到' }), $prio0, (Get-Process -Id $PID).PriorityClass)
    # ② PS 加速器(找不到不影響)
    $m = [IO.Path]::Combine($R, 'supportive modules', 'VIA_PS_Accel_Module.ps1')
    if (Test-Path -LiteralPath $m) { . $m; Say GREEN "② PS 加速器已接 · $m" } else { Say GRAY "② 找不到 VIA_PS_Accel_Module.ps1(不影響)" }
    if (-not (Test-Path -LiteralPath $R)) { Say RED "找不到 VIA 根 $R"; return }
    $py = if ($env:VRN2_PY) { $env:VRN2_PY } else { (Get-Command python, py -ErrorAction SilentlyContinue | Where-Object { $_.Source -notmatch 'WindowsApps' } | Select-Object -First 1).Source }
    if (-not $py) { Say RED "找不到 python(不要用 WindowsApps 的假 python)"; return }
    # 每個 python 指令都先接正本加速器(VeritasCeleritas 最新版號 · 找不到 = 不改行為)
    $wrap = Join-Path $tmp 'vrn2_accel_run.py'
    [IO.File]::WriteAllText($wrap, @'
# [VIA:ACCEL-BRIDGE:v0111] 先接正本加速器(找不到 = 不改行為)再執行目標 .py
import re, runpy, sys
from pathlib import Path
root, target = Path(sys.argv[1]), sys.argv[2]
sys.argv = [target] + sys.argv[3:]
sup = root / "supportive modules"
c = sorted(list(sup.glob("VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")) + list(sup.glob("*/VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")), key=lambda x: int(re.search(r"_v(\d{4})", x.name).group(1)))
try:
    if c:
        sys.path.insert(0, str(c[-1].parent))
        __import__(c[-1].stem)
except Exception:  # noqa: BLE001
    pass
sys.path.insert(0, str(Path(target).resolve().parent))
runpy.run_path(target, run_name="__main__")
'@, (New-Object Text.UTF8Encoding $false))
    function Q($s) { '"' + $s + '"' }
    # ③ 取得啟動器 v0133:先看本機那份 · 不是 → 從 GitHub 分支(讀不到 → main)讀發行夾(git fetch + git archive · 不切換分支)· 雜湊對才換 · 舊版改名備份
    $have = if (Test-Path -LiteralPath $A) { (Get-FileHash -LiteralPath $A -Algorithm SHA256).Hash.ToLower() } else { '' }
    $rel = $null
    $top = $null; if (Get-Command git -ErrorAction SilentlyContinue) { $top = (git -C $R rev-parse --show-toplevel 2>$null) }; if ($top) { $top = "$top".Trim() }
    if ($top -and $have -ne $Want) {
      foreach ($b in $Br, 'main') {
        $ok = $false
        foreach ($w in 0, 2, 4, 8, 16) { if ($w) { Start-Sleep -Seconds $w }; git -C $top fetch -q origin $b 2>&1 | Out-Null; if ($LASTEXITCODE -eq 0) { $ok = $true; break } }
        if (-not $ok) { continue }
        $z = Join-Path $tmp 'vrn2_release_v0133.zip'
        git -C $top archive --format=zip -o $z "origin/${b}:$RelP" 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $z)) { $rel = Join-Path $tmp 'rel'; Expand-Archive -LiteralPath $z -DestinationPath $rel -Force; break }
      }
    }
    if ($have -ne $Want) {
      if (-not $rel) { Say RED "③ 本機啟動器不是 v0133,且讀不到 GitHub 分支 $Br 或 main(網路 / git)· 請手動下載 ActivateVRN-2.py v0133 到 $A"; return }
      Expand-Archive -LiteralPath (Join-Path $rel 'ActivateVRN-2_v0133.zip') -DestinationPath (Join-Path $tmp 'l') -Force
      $new = [IO.Path]::Combine($tmp, 'l', 'ActivateVRN-2.py')
      $man = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $rel 'VRN2_Release_v0133.json') | ConvertFrom-Json
      $got = (Get-FileHash -LiteralPath $new -Algorithm SHA256).Hash.ToLower()
      if ($got -ne $Want -or $man.launcher.sha256 -ne $Want) { Say RED "③ 下載的啟動器雜湊不對($got)· 不使用"; return }
      New-Item -ItemType Directory -Force -Path (Split-Path -Parent $A) | Out-Null
      if (Test-Path -LiteralPath $A) {
        $ov = Select-String -LiteralPath $A -Pattern 'VERSION = "ActivateVRN-2 v(\d{4})"' -List
        $bak = Join-Path (Split-Path -Parent $A) ("ActivateVRN-2_v{0}_{1}.py.bak" -f $(if ($ov) { $ov.Matches[0].Groups[1].Value } else { 'old' }), $t0.ToString('yyyyMMdd_HHmmss'))
        Copy-Item -LiteralPath $A -Destination $bak; Say GREEN "③ 舊啟動器已備份 → $bak"
      }
      Copy-Item -LiteralPath $new -Destination $A -Force
      Say GREEN "③ 啟動器 v0133 就位(SHA-256 $($Want.Substring(0,12)) · 來源 GitHub $b)→ $A"
    } else { Say GREEN "③ 本機已是 v0133(SHA-256 $($Want.Substring(0,12)))" }
    # ③b 定位 VRN-2 程式夾(BEGIN):啟動器先看環境變數 VIA_ROOT · 先確認那裡真的有 functional modules\VRN · 沒有就找 · 找到才帶給啟動器(只在這個視窗 · 結束還原)
    $hasV = { param($p) $p -and (Test-Path -LiteralPath ([IO.Path]::Combine($p, 'functional modules', 'VRN')) -PathType Container) }
    $root = $null
    $how = 'VIA 根'
    if (& $hasV $R) { $root = $R }
    else {                                                                   # MAIN VRN-2 SystemManager 上次成功時寫的紀錄:鎖檔在 VRN\registry\ → 程式夾
      $sj = [IO.Path]::Combine($R, 'VIA_Reports', 'vrn2', 'VRN2_Success_latest.json')
      if (Test-Path -LiteralPath $sj) {
        try { $lk = (Get-Content -Raw -Encoding UTF8 -LiteralPath $sj | ConvertFrom-Json).lock; if ($lk) { $vv = Split-Path -Parent (Split-Path -Parent $lk); if (Test-Path -LiteralPath $vv -PathType Container) { $root = Split-Path -Parent (Split-Path -Parent $vv); $how = "MAIN 成功紀錄 $sj" } } } catch { }
      }
    }
    if ($root) { }
    elseif ($via0) { $root = @($via0, [IO.Path]::Combine($via0, 'VeritasIntelligenceAnalytics')) | Where-Object { & $hasV $_ } | Select-Object -First 1; if ($root) { $how = '環境變數 VIA_ROOT' } }
    if (-not $root) {
      $base = if ($top) { $top } else { Split-Path -Parent $R }
      $hit = @(Get-ChildItem -LiteralPath $base -Recurse -Depth 4 -Directory -Filter 'VRN' -ErrorAction SilentlyContinue | Where-Object { $_.Parent.Name -eq 'functional modules' -and $_.FullName -notmatch '_archive|_quarantine' -and @(Get-ChildItem -LiteralPath $_.FullName -Filter 'VRN_SystemManager_v*.py' -ErrorAction SilentlyContinue).Count -gt 0 })
      if ($hit.Count -ge 1) {
        $root = $hit[0].Parent.Parent.FullName; $how = "倉裡找到($base)"
        if ($hit.Count -gt 1) { Say YELLOW ("③b 找到 {0} 個 functional modules\VRN · 用第一個 {1}(其他:{2})" -f $hit.Count, $root, (($hit | Select-Object -Skip 1 | ForEach-Object { $_.FullName }) -join ' · ')) }
      }
    }
    if (-not $root) {
      Say RED ("③b 找不到 VRN-2 程式夾 functional modules\VRN · VIA 根 {0}(存在 {1})· 環境變數 VIA_ROOT = {2}" -f $R, (Test-Path -LiteralPath $R), $(if ($via0) { $via0 } else { '未設' }))
      if (Test-Path -LiteralPath $R) { Say GRAY ("    VIA 根底下的夾:{0}" -f ((Get-ChildItem -LiteralPath $R -Directory -ErrorAction SilentlyContinue | Select-Object -First 30 | ForEach-Object { $_.Name }) -join ' · ')) }
      if ($top) {
        $brn = git -C $top branch --show-current 2>$null
        $ntr = @(git -C $R ls-files -- 'functional modules/VRN' 2>$null).Count
        Say GRAY ("    git:目前分支 {0} · git 記錄裡 functional modules\VRN 有 {1} 個檔(有記錄但夾不在 = 被移走 / 刪除 / 換了分支)" -f $brn, $ntr)
      }
      Say YELLOW "③b 交給啟動器 v0133 依 MAIN 登記紀錄再找一次(它會印出查過的地方)"
    }
    else {
    if ($root -ne $R) { Say YELLOW ("③b VRN-2 程式夾不在 {0} → 改用 {1}(輸出 / 報告也讀這裡)" -f $R, $root); $R = $root }
    if ($via0 -and $via0 -ne $root) { Say YELLOW ("③b 環境變數 VIA_ROOT 原本是 {0}(那裡沒有 functional modules\VRN 或不是這個 VIA 根)→ 這次改成 {1}(只在這個視窗 · 結束還原)" -f $via0, $root) }
    $env:VIA_ROOT = $root
    Say GREEN ("③b VRN-2 程式夾 {0}(來源 {1})" -f [IO.Path]::Combine($root, 'functional modules', 'VRN'), $how)
    }
    # ③b(END)
    # ④ 執行(啟動器自己做 ①~⑪:CPU/DRAM · 定位 · 船包補回 · 落地 v0231→v0239 + 獨立驗證器 · 補裝 · 加速器 · 平行段 · 登記 · 測試 · vrn2 --run · ⑪ 背景驗證 ∥ 完成判定 · 上船 · 封存 · 驗證寫回 U/I → 開 U/I)
    if ($NoPush) { $env:VIA_VRN2_NO_PUSH = '1' } else { Remove-Item Env:\VIA_VRN2_NO_PUSH -ErrorAction SilentlyContinue }
    Write-Host ("[計] VRN-2 一鍵 v0133 · ActivateVRN-2 v0133 · {0}" -f $(if ($NoPush) { '只實測不上船' } else { '完成後自動上船(VRN-2 船包)' })) -ForegroundColor Yellow
    & $py $A @LArgs
    $rcL = $LASTEXITCODE
    # ⑤ 摘要 · 獨立驗證:啟動器 ⑪ 本輪已驗(報告時間 ≥ 開始)→ 直接用;沒有 → 輸出冊是本輪寫的(≥ 開始 - 5 秒 · 同啟動器 ⑪)才由 PS 用落地的驗證器自己驗(與摘要同時跑 · 只讀 · 判決也寫回 U/I)· 舊冊不驗
    $v2 = [IO.Path]::Combine($R, 'VIA_Reports', 'vrn2'); $od = Join-Path $v2 'output'
    $fdj = Join-Path $od 'VRN2_FinancialData_latest.json'
    $fdNew = (Test-Path -LiteralPath $fdj) -and ((Get-Item -LiteralPath $fdj).LastWriteTime -ge $t0.AddSeconds(-5))
    $vp = $null; $vd = Join-Path $v2 'verify_independent'; $vr = $null; $vlog = $null
    $lv = if (Test-Path -LiteralPath $vd) { Get-ChildItem -LiteralPath $vd -Filter 'VRN2_IndependentVerify_*.json' | Where-Object { $_.LastWriteTime -ge $t0.AddSeconds(-5) } | Sort-Object LastWriteTime | Select-Object -Last 1 } else { $null }
    if ($lv) { $vr = $lv.FullName; $vlog = $vr -replace '\.json$', '.txt' }
    elseif ($Verify -and $fdNew) {
      $ver = Get-ChildItem -LiteralPath ([IO.Path]::Combine($R, 'functional modules', 'VRN')) -Filter 'VRN2_IndependentVerifier_v*.py' -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
      if ($ver) {
        New-Item -ItemType Directory -Force -Path $vd | Out-Null
        $vr = Join-Path $vd ("VRN2_IndependentVerify_{0}.json" -f $t0.ToString('yyyyMMdd_HHmmss'))
        $vlog = $vr -replace '\.json$', '.txt'
        $vp = Start-Process -FilePath $py -ArgumentList @((Q $wrap), (Q $R), (Q $ver.FullName), (Q $od), (Q (Join-Path $v2 'scope_in')), (Q $vr), '--ui', (Q (Join-Path $v2 'VRN2_UI_latest.html'))) -NoNewWindow -PassThru -RedirectStandardOutput $vlog -RedirectStandardError ($vlog + '.err')
        Say GRAY "啟動器本輪沒有驗證報告 → PS 用 $($ver.Name) 自己驗本輪的輸出冊(只讀 · 判決寫回 U/I)"
      }
    }
    elseif ($Verify -and (Test-Path -LiteralPath $fdj)) { Say YELLOW "獨立驗證不跑 · 輸出冊不是本輪寫的($((Get-Item -LiteralPath $fdj).LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss')) · ⑦ 沒跑完)· 不驗舊冊、不把舊冊判決寫進 U/I" }
    $sum = Join-Path $tmp 'vrn2_sum.py'
    [IO.File]::WriteAllText($sum, @'
import json, sys, datetime
from collections import Counter
from pathlib import Path
v2, t0 = Path(sys.argv[1]), datetime.datetime.fromisoformat(sys.argv[2])
def j(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None
c = j(v2 / "VRN2_Completion_latest.json") or {}
fresh = bool(c.get("ts")) and datetime.datetime.fromisoformat(c["ts"]) >= t0 - datetime.timedelta(seconds=5)
lamp = "GREEN" if fresh and c.get("verdict") == "完成" and not c.get("red") else "RED"
print("%s|⑧ 完成判定 · %s · 紅 %s · 黃 %s · %s · %s" % (lamp, c.get("verdict", "?"), c.get("red", "?"), c.get("yellow", "?"), c.get("manager", "?"), "本輪" if fresh else "不是本輪寫的(⑦ 沒跑完)"))
for it in c.get("items") or []:
    if it.get("lamp") in ("RED", "YELLOW"):
        print("%s|   %s · %s" % (it["lamp"], it["name"][:24], it["detail"][:150]))
od = v2 / "output"
b, f, s, r = (j(od / ("VRN2_%s_latest.json" % n)) or [] for n in ("BasicInfo", "FinancialData", "Summary", "Rejected"))
sub = [x for x in f if x.get("SUBCOL")]
rc = Counter(str(x.get("REASON", "")).split("(")[0][:10] for x in r)
pq = sorted(p.name for p in od.glob("VRN2_*_latest.parquet"))
st = list((od / "_stale").glob("*.parquet")) if (od / "_stale").is_dir() else []
_fd = od / "VRN2_FinancialData_latest.json"
_new = _fd.exists() and datetime.datetime.fromtimestamp(_fd.stat().st_mtime) >= t0 - datetime.timedelta(seconds=5)
print(("GREEN|" if _new else "YELLOW|(不是本輪寫的舊冊)") + "輸出冊 · 基本資料 %d · 年度數據 %d 筆(子欄 %d · 依子表頭更正 %d)· 一標題四重點 %d · 剔除冊 %d(%s)" % (len(b), len(f), len(sub), sum("更正" in (x.get("VERIFY") or "") for x in sub), len(s), len(r), " · ".join("%s %d" % kv for kv in rc.most_common(4))))
print("%s|Parquet %d / 4%s" % ("GREEN" if len(pq) == 4 else "YELLOW", len(pq), (" · 舊檔移到 output\\_stale %d 個(本輪沒寫 Parquet · 缺 pandas / pyarrow)" % len(st)) if st else ""))
import hashlib, re as _re
up = v2 / "VRN2_UI_latest.html"
pg = up.read_text(encoding="utf-8") if up.exists() else ""
h = hashlib.sha256()
for x in f:
    h.update(("\x1f".join(str(x.get(k, "")) for k in ("FILENAME", "PAGE", "TABLE", "ITEM", "PERIOD", "SUBCOL", "VALUE")) + "\x1e").encode("utf-8"))
m = _re.search(r'window\.VRN2_IV=\{"ver":"[^"]*","ts":"([^"]*)","fp":"([0-9a-f]{16})"', pg)
tab = "id='vrn2vo-h'" in pg
if not tab:
    print("YELLOW|U/I %s · 沒有「驗證過的輸出」分頁(管理器不是 v0237 以後)" % up)
elif m and m.group(2) == h.hexdigest()[:16]:
    print("GREEN|U/I %s · 「驗證過的輸出」分頁 · 獨立驗證判決已寫回(%s · 冊指紋 %s 相同)" % (up, m.group(1), m.group(2)))
else:
    print("YELLOW|U/I %s · 「驗證過的輸出」分頁 · 獨立驗證%s" % (up, "結果是別一輪的(指紋不同)" if m else "尚未寫回"))
tm = j(v2 / "tools" / "VRN2_ToolManifest_v0100.json") or {}
if tm.get("offers"):
    print("GREEN|② 借出工具冊 %s · %s" % (v2 / "tools" / "VRN2_ToolManifest_v0100.json", " · ".join("%s %s" % (t.get("id"), "能用" if t.get("ready") else "不能用") for t in tm["offers"])))
else:
    print("YELLOW|② 借出工具冊沒寫(看啟動器 ② 那行)")
pb = v2 / "pivot" / "VRN2_Pivot_Borrow_latest.json"
pj = j(pb) or {}
if pj and datetime.datetime.fromtimestamp(pb.stat().st_mtime) >= t0 - datetime.timedelta(seconds=5):
    pc = pj.get("counts") or {}
    print("GREEN|⑫ PIVOT 資料庫(借用 %s %s · sha256 %s)· 事實 %s/%s · 年度 %s 列 · 衝突 %s · %s" % (
        (pj.get("borrow") or {}).get("from", "?"), (pj.get("borrow") or {}).get("id", "?"), str((pj.get("borrow") or {}).get("sha256", ""))[:12],
        pc.get("kept"), pc.get("facts"), pc.get("pivot_report_annual"), pc.get("conflicts"), v2 / "pivot" / "VRN_Pivot_v0100.html"))
else:
    print("GRAY|⑫ PIVOT 資料庫本輪沒寫(VRN-1 的工具借不到或不借 · VRN-2 照常 · 看啟動器 ⑫ 那行)")
'@, (New-Object Text.UTF8Encoding $false))
    $sumOut = & $py $wrap $R $sum $v2 $t0.ToString('yyyy-MM-ddTHH:mm:ss') 2>&1
    foreach ($ln in $sumOut) { $p = "$ln" -split '\|', 2; if ($p.Count -eq 2) { Say $p[0] $p[1] } else { Write-Host $ln } }
    # 上船狀態:GitHub 上的 VRN-2 船包是否和本機相同(v0125 起只送 VRN-2 船包 · 本機別的提交不代推)
    if ($top) {
      $u = git -C $R rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>$null
      if ($NoPush) { Say GRAY "⑨ 這次不上船" }
      elseif (-not $u) { Say YELLOW "⑨ 目前分支沒有上游(看不出 GitHub 上的船包)" }
      else {
        $ub = "$u" -split '/', 2; git -C $R fetch -q $ub[0] $ub[1] 2>&1 | Out-Null
        git -C $R diff --quiet $u HEAD -- docs/handoff/ai/vrn2_ship docs/handoff/ai/VRN2_Handover_latest.md 2>$null
        $same = ($LASTEXITCODE -eq 0)
        $ahead = git -C $R rev-list --count "$u..HEAD" -- . ':(exclude)docs/handoff/ai/vrn2_ship' ':(exclude)docs/handoff/ai/VRN2_Handover_latest.md' ':(exclude)docs/handoff/ai/VRN2_Handover_v0133.md' 2>$null
        Say $(if ($same) { 'GREEN' } else { 'YELLOW' }) ("⑨ GitHub {0} 上的 VRN-2 船包 {1}" -f $u, $(if ($same) { '與本機相同(已上船)' } else { '與本機不同(沒推上去 · 看上面 ⑨ 那行的原因)' }))
        if ("$ahead" -match '^\d+$' -and [int]$ahead -gt 0) { Say GRAY ("本機另有 {0} 個動到別的檔的提交沒推到 {1}(不是 VRN-2 的 · VRN-2 不代推)" -f $ahead, $u) }
      }
    }
    $vok = $null
    if ($vp) {
      if (-not $vp.WaitForExit(1800000)) { try { $vp.Kill() } catch { }; Say YELLOW "獨立驗證超過 30 分鐘 · 已停(不影響輸出)"; $vr = $null }
      else { $vok = ($vp.ExitCode -eq 0) }
    } elseif ($vr) {
      # 啟動器 ⑪ 的報告:照驗證器自己的結束碼規則看三段(基本資料 / 一標題四重點 任一欄 FAIL · 年度數據錯值列 fin_bad)+ 日誌的 [FAIL] 行 · 讀不到 = 沒過
      $vok = $false
      try {
        $vj = Get-Content -Raw -Encoding UTF8 -LiteralPath $vr | ConvertFrom-Json
        if (-not $vj.version -or $null -eq $vj.basic -or $null -eq $vj.summary -or $null -eq $vj.fin_bad) { throw '報告缺欄位' }
        $nf = (@($vj.basic) + @($vj.summary) | Where-Object { $_ } | ForEach-Object { $_.checks.PSObject.Properties | Where-Object { "$($_.Value)" -like 'FAIL*' } } | Measure-Object).Count
        $nb = ($vj.fin_bad | Measure-Object).Count
        $lt = Get-Content -Encoding UTF8 -LiteralPath $vlog -ErrorAction SilentlyContinue
        $vok = ($nf -eq 0) -and ($nb -eq 0) -and -not ($lt -match '^\s+\[FAIL\]') -and -not ($lt -match '^\[驗證\] 年度數據 .*(FAIL|MISALIGNED|BADVALUE|BADITEM|SUBFAIL|TRANSFAIL|DUPKEY|QTRCOL|DUPROW|HDRVAL|SECFAIL)')
        if (-not $vok) { Say YELLOW ("獨立驗證報告:基本資料 / 一標題四重點 FAIL 欄 {0} · 年度數據錯值 {1} 筆 · {2}" -f $nf, $nb, $vr) }
      } catch { Say YELLOW "獨立驗證報告讀不到或不完整($vr · $($_.Exception.Message))· 當作沒過" }
    }
    if ($vr -and (Test-Path -LiteralPath $vlog)) {
      $vt = Get-Content -Encoding UTF8 -LiteralPath $vlog
      $ve = if (Test-Path -LiteralPath ($vlog + '.err')) { Get-Content -Encoding UTF8 -LiteralPath ($vlog + '.err') | Where-Object { $_ -notmatch 'FontBBox' } } else { @() }
      if (($ve -join ' ') -match 'ModuleNotFoundError') { $vok = $null; Say GRAY "獨立驗證跳過 · 缺 pdfplumber / pypdfium2(不補裝)" }
      else {
        foreach ($ln in ($vt | Where-Object { $_ -match '^\[驗證\]' })) { Say $(if ($vok) { 'GREEN' } else { 'YELLOW' }) "獨立驗證 $ln" }
        foreach ($ln in ($vt | Where-Object { $_ -match '^\s+\[FAIL\]' } | Select-Object -First 8)) { Say YELLOW $ln.Trim() }
        Say $(if ($vok) { 'GREEN' } else { 'YELLOW' }) ("獨立驗證({0}){1} · 報告 {2}" -f $(if ($lv) { '啟動器 ⑪' } else { 'PS 自己驗' }), $(if ($vok) { ' 錯值 0' } else { ' 有待核對 → U/I「驗證過的輸出」看 ✗ 格(先看原文再判 · 驗證器也要被驗)' }), $vr)
        $dg = "$vr.digest.txt"
        if (Test-Path -LiteralPath $dg) {
          Write-Host "──── 驗證摘要(貼給 AI 只要這份 · 完整在 $dg)────" -ForegroundColor Cyan
          Get-Content -Encoding UTF8 -LiteralPath $dg | Select-Object -First 40 | ForEach-Object { Write-Host $_ }
        }
      }
    } elseif ($Verify -and ($fdNew -or -not (Test-Path -LiteralPath $fdj))) { Say GRAY "獨立驗證跳過 · 啟動器沒驗、也找不到落地的驗證器或輸出冊" }
    # ⑤b 前後端連結檢查(v0133 · Codex #550 修正):HKCU 的 vrn2:// 指令解析成「python」「處理器」兩段 · 處理器要 = 本機 VRN-2 程式夾裡的 VRN2_UIAction_v0103.py(整條路徑 · 檔在;或那一夾有啟動器本輪寫的 VRN2_UIAction_Config.json)· python 檔在 · U/I 有「輸入(window I/O)」區塊 · 有輸入紀錄;⑤b 的燈併進最後 NEXT(紅 → 紅 · 黃 → 最多黃)
    function Chk5b($R, $py, $regCmd, $uiTxt, $inp) {
      $norm = { param($p) try { if ($p) { [IO.Path]::GetFullPath($p).TrimEnd('\', '/').ToLowerInvariant() } else { '' } } catch { '' } }
      $hExp = [IO.Path]::Combine($R, 'functional modules', 'VRN', 'VRN2_UIAction_v0103.py')
      $qa = @([regex]::Matches([string]$regCmd, '"([^"]*)"') | ForEach-Object { $_.Groups[1].Value })
      $regExe = if ($qa.Count -ge 1) { $qa[0] } else { '' }; $regH = if ($qa.Count -ge 2) { $qa[1] } else { '' }
      $hIn = [bool]($regH -and (Test-Path -LiteralPath $regH -PathType Leaf))
      $hSame = [bool]($hIn -and ((& $norm $regH) -eq (& $norm $hExp)))
      $hCfg = $false; $cfgP = if ($regH) { Join-Path (Split-Path -Parent $regH) 'VRN2_UIAction_Config.json' } else { '' }
      if ($hIn -and -not $hSame -and ($regH -match '[\\/]VRN2_UIAction_v0103\.py$') -and (Test-Path -LiteralPath $cfgP)) { try { $cf = Get-Content -Raw -Encoding UTF8 -LiteralPath $cfgP | ConvertFrom-Json; $hCfg = ($cf.version -eq 'ActivateVRN-2 v0133') -and ($cf.handler -eq 'VRN2_UIAction_v0103.py') } catch { } }
      $hOk = $hSame -or $hCfg
      $exeOk = [bool]($regExe -and (Test-Path -LiteralPath $regExe -PathType Leaf))
      $samePy = [bool]($exeOk -and $py -and ((& $norm (Split-Path -Parent $regExe)) -eq (& $norm (Split-Path -Parent $py))))
      $blkOk = [bool](($uiTxt -match "id='vrn2-input'") -and ($uiTxt -match '個股報告/訊息') -and ($uiTxt -match '產業報告/展望') -and ($uiTxt -match '其他投資報告') -and ($uiTxt -match 'vrn2://pick\?kind=folder'))
      if ($hOk -and $exeOk -and $blkOk) { $l = 'GREEN'; $m = '⑤b 前後端已連結:vrn2:// → {0}({1} · 檔在)· python {2}{3} · U/I 有「輸入(window I/O)」區塊(個股報告/訊息 可選 · 產業報告/展望 / 其他投資報告 尚未開放)' -f $regH, $(if ($hSame) { '整條路徑 = 本機 VRN-2 程式夾' } else { '程式夾 = 啟動器本輪登記的(VRN2_UIAction_Config.json v0133)' }), $regExe, $(if ($samePy) { '' } else { '(與本一鍵用的 python 不同夾 · 能跑就好)' }) }
      elseif ($blkOk -and -not $regCmd) { $l = 'YELLOW'; $m = '⑤b U/I 有輸入區塊,但 vrn2:// 沒註冊(HKCU)→ 按鈕不會有反應;在 Windows 重跑一次啟動器(⑥c 會註冊並讀回核對)或用 $env:VRN2_SOURCE' }
      else { $l = 'RED'; $m = '⑤b 前後端沒接上:vrn2:// 註冊 {0} · U/I 輸入區塊 {1}' -f $(if (-not $regCmd) { '沒有' } elseif (-not $regH) { '解析不出處理器(' + $regCmd + ')' } elseif (-not $hIn) { '指向不存在的 ' + $regH + '(要的是 ' + $hExp + ')' } elseif (-not $hOk) { '指向 ' + $regH + '(舊的 / 搬走的檢出 · 要的是 ' + $hExp + ')' } elseif (-not $exeOk) { 'python 不在 ' + $regExe } else { '正確' }), $(if ($blkOk) { '在' } else { '不在(重跑啟動器 ⑫b)' }) }
      $mi = if ($inp) { '⑤b 目前輸入 · {0} · {1}({2})· {3}' -f $inp.cat_label, $inp.source_dir, $inp.how, $inp.audit_line } else { if ($l -eq 'GREEN') { $l = 'YELLOW' }; '⑤b 沒有輸入紀錄(VRN2_Input_latest.json)· 啟動器 ②b 沒跑到' }
      [pscustomobject]@{ lamp = $l; msg = $m; inpMsg = $mi; inpOk = [bool]$inp; hOk = $hOk; hSame = $hSame; hCfg = $hCfg; exeOk = $exeOk; samePy = $samePy; blkOk = $blkOk; regH = $regH; regExe = $regExe }
    }
    $v2p = [IO.Path]::Combine($R, 'VIA_Reports', 'vrn2'); $uiP = Join-Path $v2p 'VRN2_UI_latest.html'
    $regCmd = ''; try { $regCmd = [string](Get-ItemProperty -Path 'HKCU:\Software\Classes\vrn2\shell\open\command' -ErrorAction Stop).'(default)' } catch { }
    $uiTxt = if (Test-Path -LiteralPath $uiP) { [IO.File]::ReadAllText($uiP, [Text.Encoding]::UTF8) } else { '' }
    $inpP = Join-Path $v2p 'VRN2_Input_latest.json'; $inp = $null; try { $inp = Get-Content -Raw -Encoding UTF8 -LiteralPath $inpP | ConvertFrom-Json } catch { }
    $c5 = Chk5b $R $py $regCmd $uiTxt $inp
    Say $c5.lamp $c5.msg
    Say $(if ($c5.inpOk) { 'GREEN' } else { 'YELLOW' }) $c5.inpMsg
    $d = [int]((Get-Date) - $t0).TotalSeconds
    # 成功 = 啟動器 rc 0 且 本輪 ⑧ 完成燈綠(VRN2_Completion_latest.json 是本輪寫的 · 完成 · 紅 0)· 啟動器 v0129 不論 ⑧ 都回 0 → 不能只看 rc
    $ok8 = [bool]($sumOut | Where-Object { "$_" -like 'GREEN|⑧ 完成判定*' } | Select-Object -First 1)
    # v0133(Codex #550):⑤b 併進最後的燈 —— 前後端沒接上(紅)→ 紅;vrn2:// 沒註冊 / 沒輸入紀錄(黃)→ 最多黃;只有 ⑧ 綠 + 驗證錯值 0 + ⑤b 綠 才是 GREEN(rc 0)
    $lamp = if ($rcL -ne 0 -or -not $ok8 -or $c5.lamp -eq 'RED') { 'RED' } elseif ($vok -eq $true -and $c5.lamp -eq 'GREEN' -and $c5.inpOk) { 'GREEN' } else { 'YELLOW' }
    $msg = @{ RED = $(if ($rcL -ne 0 -or -not $ok8) { 'VRN-2 有紅燈(⑧ 完成判定不是本輪的綠 或 啟動器 rc 不是 0)· 把貼包(≤300 行 · 結尾 NEXT)貼回' } else { 'VRN-2 ⑧ 本輪完成,但 ⑤b 前後端沒接上(vrn2:// 指向別的 / 不存在的處理器 · 或 U/I 沒有輸入區塊)→ 重跑啟動器(⑥c 重新註冊並讀回核對 · ⑫b 重放區塊)· 把 ⑤b 那兩行貼回' })
              GREEN = 'VRN-2 一鍵 v0133 跑完 · ⑧ 本輪完成 · 獨立驗證錯值 0 · U/I 已開在「驗證過的輸出」(最後有 PIVOT 資料庫連結 · 左側「輸入」可選檔案夾 / 檔案 · 目前只開個股報告/訊息)· 把 ⑨ / ⑪ / ⑫ 三行 + 驗證摘要貼回'
              YELLOW = $(if ($c5.lamp -eq 'YELLOW' -and -not $c5.hOk) { 'VRN-2 ⑧ 本輪完成 · 但 vrn2:// 沒註冊(HKCU)→ U/I 按鈕不會動 · 在 Windows 重跑一次啟動器(⑥c 會註冊並讀回核對)或用 $env:VRN2_SOURCE · 把 ⑤b 那兩行貼回' } elseif (-not $c5.inpOk) { 'VRN-2 ⑧ 本輪完成 · 但沒有輸入紀錄(②b 沒跑到)→ 把 ②b 那行貼回' } elseif ($vok -eq $false) { 'VRN-2 ⑧ 本輪完成 · 獨立驗證有待核對 → U/I「驗證過的輸出」看 ✗ 格 · 把驗證摘要貼回' } else { 'VRN-2 ⑧ 本輪完成 · 獨立驗證沒跑完 / 沒寫回 → 把 ⑪ 那行貼回' }) }[$lamp]
    Write-Host ("NEXT: [{0}] {1} · 交接報告 {2} · 啟動器 rc {3} · {4} 秒" -f $lamp, $msg, ([IO.Path]::Combine($R, 'docs', 'handoff', 'ai', 'VRN2_Handover_latest.md')), $rcL, $d) -ForegroundColor $(@{ RED = 'Red'; GREEN = 'Cyan'; YELLOW = 'Yellow' }[$lamp])
    $global:LASTEXITCODE = @{ GREEN = 0; YELLOW = 2; RED = 1 }[$lamp]
  } finally {
    try { (Get-Process -Id $PID).PriorityClass = $prio0 } catch { }
    if ($null -ne $via0) { $env:VIA_ROOT = $via0 } else { Remove-Item Env:\VIA_ROOT -ErrorAction SilentlyContinue }
  }
}
```

## 一行的原始碼(`-EncodedCommand` 解碼後 · 只讀取並核對 · 不改任何檔)

```text
$ErrorActionPreference = 'Continue'
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch { }
$R  = if ($env:VRN2_ROOT) { $env:VRN2_ROOT } else { 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics' }
$Br = 'claude/optimistic-goodall-yhalc5'
$P  = 'VeritasIntelligenceAnalytics/docs/handoff/ai/vrn2_release_v0133'
$H  = '21ab900abfd0833cccaeb69298d80ec57dd9eff1502763c78614264224b672dd'
Write-Host ('[VRN-2] PowerShell ' + $PSVersionTable.PSVersion + ' · 從 GitHub 讀一鍵 v0133 程式碼(核對 SHA-256 後執行)') -ForegroundColor Yellow
$top = git -C $R rev-parse --show-toplevel 2>$null
if (-not $top) { Write-Host "[RED] $R 不是 git 倉或找不到 git" -ForegroundColor Red; return }
$top = "$top".Trim()
$t = Join-Path ([IO.Path]::GetTempPath()) ('vrn2_boot_' + (Get-Date).ToString('yyyyMMdd_HHmmss'))
New-Item -ItemType Directory -Force -Path $t | Out-Null
$z = Join-Path $t 'oneclick.zip'; $okz = $false
foreach ($b in $Br, 'main') {
  foreach ($w in 0, 2, 4, 8, 16) { if ($w) { Start-Sleep -Seconds $w }; git -C $top fetch -q origin $b 2>&1 | Out-Null; if ($LASTEXITCODE -eq 0) { break } }
  git -C $top archive --format=zip -o $z ('origin/' + $b + ':' + $P) VRN2_OneClick_v0133.md 2>&1 | Out-Null
  if ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $z)) { $okz = $true; Write-Host ('[計] 一鍵程式碼來源 GitHub ' + $b) -ForegroundColor DarkGray; break }
}
if (-not $okz) { Write-Host "[RED] 讀不到 GitHub 分支 $Br 或 main 的一鍵程式碼(網路 / git)" -ForegroundColor Red; return }
Expand-Archive -LiteralPath $z -DestinationPath $t -Force
$md = [IO.File]::ReadAllText((Join-Path $t 'VRN2_OneClick_v0133.md'), [Text.Encoding]::UTF8) -replace "`r`n", "`n"
$code = [regex]::Match($md, '(?s)```powershell\n(.*?)\n```').Groups[1].Value
$sha = -join ([Security.Cryptography.SHA256]::Create().ComputeHash([Text.Encoding]::UTF8.GetBytes($code)) | ForEach-Object { $_.ToString('x2') })
if ($sha -ne $H) { Write-Host "[RED] 一鍵程式碼 SHA-256 不對($sha)· 不執行" -ForegroundColor Red; return }
Write-Host ('[GREEN] 一鍵程式碼 SHA-256 ' + $H.Substring(0, 12) + ' 相符 → 在 PowerShell 裡執行') -ForegroundColor Green
& ([scriptblock]::Create($code))
exit $(if ($null -ne $global:LASTEXITCODE) { [int]$global:LASTEXITCODE } else { 0 })   # v0133(Codex #550):NEXT 的燈帶回這個子行程的 rc(GREEN 0 · YELLOW 2 · RED 1 → cmd 的 %ERRORLEVEL%)
```
