# VRN-1 / VRN-2 操作員一鍵 v0100(cmd / PowerShell 都能貼 · git pull → VRN-2 → VRN-1 · 兩個獨立系統各跑自己的 MAIN)

操作員令(2026-10-20):「INTEGRATE ABOVE INTO ONE CODE TO HANDLE ALL ABOVE. git pull」。PR tonykuni/VIA-VDF-VRN#79 合併後要做的三件事收成一行:

| 步驟 | 做什麼 | 出事時 |
|---|---|---|
| ① VRN-1 git pull | `C:\Users\tonyk\VIA-VDF-VRN`(`$env:VIA_VRN1_ROOT`)切到 `main`、只快轉拉到最新(第十三 / 十四輪 · 借出工具冊)· 有沒提交的改動 → 先 `git stash` 保存(名稱「VRN1_VRN2_OneClick 自動暫存 …」· `git stash pop` 拿回來)| 讀不到 GitHub / 不能快轉 → 黃 · 照本機現狀繼續 |
| ② VRN-2 一鍵 v0132 | 從 GitHub 讀 `vrn2_release_v0132/VRN2_OneClick_v0132.md` → **核對 SHA-256 `c68b66b0ddf4`** → 執行 VRN-2 自己的一鍵(取啟動器 v0132 · ①~⑫ · ② 寫 VRN-2 借出工具冊 · ⑫ 借 VRN-1 的 PIVOT)| 雜湊不對 → 紅、不執行 · VRN-1 照常跑 |
| ③ VRN-1 MAIN | `artifacts\VRN-1.ps1`(PowerShell 7)`check` → `run --no-cache`(G23 借 VRN-2 的段落標題 / OCR · 只寫輸出夾,不寫倉 —— 下次 git pull 不會卡)| 沒有 pwsh → 紅 + `winget install --id Microsoft.PowerShell` |
| ④ 總結 | 每一步的燈 · ⑫ 借到什麼 · G23 借到幾支 · G21 / G22 · 收尾 · NEXT | 結束碼 GREEN 0 / YELLOW 2 / RED 1 |

本段**只呼叫**兩邊自己的入口,不改任何一邊的程式 / 冊 / 號;VCGC 與 VDF 不碰。開關:`$env:VRN1_SAMPLES`(VRN-1 樣本夾 · 不設 = VRN-1 自己的預設)·
`$env:VRN1_OUT`(VRN-1 輸出夾)· `$env:VRN1_ARGS`(多給 VRN-1 run 的旗標)· `$env:VRN_PAIR_NO_PULL = '1'` 不拉 · `$env:VRN_PAIR_NO_STASH = '1'` 有改動就不拉 ·
`$env:VRN_PAIR_SKIP = 'VRN-1'` 或 `'VRN-2'` 這次跳過那一邊。容器實測見 `VRN1_VRN2_Verification_v0100.md`。

## 在「命令提示字元(cmd)」或 PowerShell 都能貼的一行(建議用這個)

它開 Windows PowerShell → 從 GitHub 分支 `claude/optimistic-goodall-yhalc5`(讀不到 → `main`)讀本檔的程式碼 → **核對 SHA-256 `60e5515615e0cb96fa1c532ec280d28a91d8dd61d49f91de203a1b393519134a`** → 相符才執行(不相符就停)。
**不要把下面整段程式碼貼進 cmd**(cmd 不認得 PowerShell)。

```bat
powershell -NoProfile -ExecutionPolicy Bypass -EncodedCommand JABFAHIAcgBvAHIAQQBjAHQAaQBvAG4AUAByAGUAZgBlAHIAZQBuAGMAZQAgAD0AIAAnAEMAbwBuAHQAaQBuAHUAZQAnAAoAdAByAHkAIAB7ACAAWwBDAG8AbgBzAG8AbABlAF0AOgA6AE8AdQB0AHAAdQB0AEUAbgBjAG8AZABpAG4AZwAgAD0AIABbAFQAZQB4AHQALgBFAG4AYwBvAGQAaQBuAGcAXQA6ADoAVQBUAEYAOAAgAH0AIABjAGEAdABjAGgAIAB7ACAAfQAKACQAUgAgACAAPQAgAGkAZgAgACgAJABlAG4AdgA6AFYAUgBOADIAXwBSAE8ATwBUACkAIAB7ACAAJABlAG4AdgA6AFYAUgBOADIAXwBSAE8ATwBUACAAfQAgAGUAbABzAGUAIAB7ACAAJwBDADoAXABVAHMAZQByAHMAXAB0AG8AbgB5AGsAXABPAG4AZQBEAHIAaQB2AGUAXABEAG8AYwB1AG0AZQBuAHQAcwBcAG0AbwB2AGkAZQBzAC0AZABhAHQAYQBzAGUAdABcAFYAZQByAGkAdABhAHMASQBuAHQAZQBsAGwAaQBnAGUAbgBjAGUAQQBuAGEAbAB5AHQAaQBjAHMAJwAgAH0ACgAkAEIAcgAgAD0AIAAnAGMAbABhAHUAZABlAC8AbwBwAHQAaQBtAGkAcwB0AGkAYwAtAGcAbwBvAGQAYQBsAGwALQB5AGgAYQBsAGMANQAnAAoAJABQACAAIAA9ACAAJwBWAGUAcgBpAHQAYQBzAEkAbgB0AGUAbABsAGkAZwBlAG4AYwBlAEEAbgBhAGwAeQB0AGkAYwBzAC8AZABvAGMAcwAvAGgAYQBuAGQAbwBmAGYALwBhAGkALwB2AHIAbgAxAF8AdgByAG4AMgBfAG8AbgBlAGMAbABpAGMAawBfAHYAMAAxADAAMAAnAAoAJABIACAAIAA9ACAAJwA2ADAAZQA1ADUAMQA1ADYAMQA1AGUAMABjAGIAOQA2AGYAYQAxAGMANQAzADIAZQBjADIAOAAwAGQAMgA4AGEAOQAxAGQAOABkAGQANgAxAGQANAA5AGYAOQAxAGQAZQAyADAAMwBhADEAYgAzADkAMwA1ADEAOQAxADMANABhACcACgBXAHIAaQB0AGUALQBIAG8AcwB0ACAAKAAnAFsAVgBSAE4ALQAxACAALwAgAFYAUgBOAC0AMgBdACAAUABvAHcAZQByAFMAaABlAGwAbAAgACcAIAArACAAJABQAFMAVgBlAHIAcwBpAG8AbgBUAGEAYgBsAGUALgBQAFMAVgBlAHIAcwBpAG8AbgAgACsAIAAnACAAtwAgAJ5fIABHAGkAdABIAHUAYgAgAICLzWRcT+FUAE51kyAAdgAwADEAMAAwACgAOGgNXCAAUwBIAEEALQAyADUANgAgAIxf91dMiCkAJwApACAALQBGAG8AcgBlAGcAcgBvAHUAbgBkAEMAbwBsAG8AcgAgAFkAZQBsAGwAbwB3AAoAJAB0AG8AcAAgAD0AIABnAGkAdAAgAC0AQwAgACQAUgAgAHIAZQB2AC0AcABhAHIAcwBlACAALQAtAHMAaABvAHcALQB0AG8AcABsAGUAdgBlAGwAIAAyAD4AJABuAHUAbABsAAoAaQBmACAAKAAtAG4AbwB0ACAAJAB0AG8AcAApACAAewAgAFcAcgBpAHQAZQAtAEgAbwBzAHQAIAAiAFsAUgBFAEQAXQAgACQAUgAgAA1OL2YgAGcAaQB0ACAACVAWYn5iDU4wUiAAZwBpAHQAIgAgAC0ARgBvAHIAZQBnAHIAbwB1AG4AZABDAG8AbABvAHIAIABSAGUAZAA7ACAAcgBlAHQAdQByAG4AIAB9AAoAJAB0AG8AcAAgAD0AIAAiACQAdABvAHAAIgAuAFQAcgBpAG0AKAApAAoAJAB0ACAAPQAgAEoAbwBpAG4ALQBQAGEAdABoACAAKABbAEkATwAuAFAAYQB0AGgAXQA6ADoARwBlAHQAVABlAG0AcABQAGEAdABoACgAKQApACAAKAAnAHYAcgBuADEAMgBfAGIAbwBvAHQAXwAnACAAKwAgACgARwBlAHQALQBEAGEAdABlACkALgBUAG8AUwB0AHIAaQBuAGcAKAAnAHkAeQB5AHkATQBNAGQAZABfAEgASABtAG0AcwBzACcAKQApAAoATgBlAHcALQBJAHQAZQBtACAALQBJAHQAZQBtAFQAeQBwAGUAIABEAGkAcgBlAGMAdABvAHIAeQAgAC0ARgBvAHIAYwBlACAALQBQAGEAdABoACAAJAB0ACAAfAAgAE8AdQB0AC0ATgB1AGwAbAAKACQAegAgAD0AIABKAG8AaQBuAC0AUABhAHQAaAAgACQAdAAgACcAcABhAGkAcgAuAHoAaQBwACcAOwAgACQAbwBrAHoAIAA9ACAAJABmAGEAbABzAGUACgBmAG8AcgBlAGEAYwBoACAAKAAkAGIAIABpAG4AIAAkAEIAcgAsACAAJwBtAGEAaQBuACcAKQAgAHsACgAgACAAZgBvAHIAZQBhAGMAaAAgACgAJAB3ACAAaQBuACAAMAAsACAAMgAsACAANAAsACAAOAAsACAAMQA2ACkAIAB7ACAAaQBmACAAKAAkAHcAKQAgAHsAIABTAHQAYQByAHQALQBTAGwAZQBlAHAAIAAtAFMAZQBjAG8AbgBkAHMAIAAkAHcAIAB9ADsAIABnAGkAdAAgAC0AQwAgACQAdABvAHAAIABmAGUAdABjAGgAIAAtAHEAIABvAHIAaQBnAGkAbgAgACQAYgAgADIAPgAmADEAIAB8ACAATwB1AHQALQBOAHUAbABsADsAIABpAGYAIAAoACQATABBAFMAVABFAFgASQBUAEMATwBEAEUAIAAtAGUAcQAgADAAKQAgAHsAIABiAHIAZQBhAGsAIAB9ACAAfQAKACAAIABnAGkAdAAgAC0AQwAgACQAdABvAHAAIABhAHIAYwBoAGkAdgBlACAALQAtAGYAbwByAG0AYQB0AD0AegBpAHAAIAAtAG8AIAAkAHoAIAAoACcAbwByAGkAZwBpAG4ALwAnACAAKwAgACQAYgAgACsAIAAnADoAJwAgACsAIAAkAFAAKQAgAFYAUgBOADEAXwBWAFIATgAyAF8ATwBuAGUAQwBsAGkAYwBrAF8AdgAwADEAMAAwAC4AbQBkACAAMgA+ACYAMQAgAHwAIABPAHUAdAAtAE4AdQBsAGwACgAgACAAaQBmACAAKAAkAEwAQQBTAFQARQBYAEkAVABDAE8ARABFACAALQBlAHEAIAAwACAALQBhAG4AZAAgACgAVABlAHMAdAAtAFAAYQB0AGgAIAAtAEwAaQB0AGUAcgBhAGwAUABhAHQAaAAgACQAegApACkAIAB7ACAAJABvAGsAegAgAD0AIAAkAHQAcgB1AGUAOwAgAFcAcgBpAHQAZQAtAEgAbwBzAHQAIAAoACcAWwAIil0AIAAATnWTC3oPX7x4hk+QbiAARwBpAHQASAB1AGIAIAAnACAAKwAgACQAYgApACAALQBGAG8AcgBlAGcAcgBvAHUAbgBkAEMAbwBsAG8AcgAgAEQAYQByAGsARwByAGEAeQA7ACAAYgByAGUAYQBrACAAfQAKAH0ACgBpAGYAIAAoAC0AbgBvAHQAIAAkAG8AawB6ACkAIAB7ACAAVwByAGkAdABlAC0ASABvAHMAdAAgACIAWwBSAEUARABdACAAgIsNTjBSIABHAGkAdABIAHUAYgAgAAZSL2UgACQAQgByACAAFmIgAG0AYQBpAG4AIACEds1kXE/hVABOdZMoALJ9740gAC8AIABnAGkAdAApACIAIAAtAEYAbwByAGUAZwByAG8AdQBuAGQAQwBvAGwAbwByACAAUgBlAGQAOwAgAHIAZQB0AHUAcgBuACAAfQAKAEUAeABwAGEAbgBkAC0AQQByAGMAaABpAHYAZQAgAC0ATABpAHQAZQByAGEAbABQAGEAdABoACAAJAB6ACAALQBEAGUAcwB0AGkAbgBhAHQAaQBvAG4AUABhAHQAaAAgACQAdAAgAC0ARgBvAHIAYwBlAAoAJABtAGQAIAA9ACAAWwBJAE8ALgBGAGkAbABlAF0AOgA6AFIAZQBhAGQAQQBsAGwAVABlAHgAdAAoACgASgBvAGkAbgAtAFAAYQB0AGgAIAAkAHQAIAAnAFYAUgBOADEAXwBWAFIATgAyAF8ATwBuAGUAQwBsAGkAYwBrAF8AdgAwADEAMAAwAC4AbQBkACcAKQAsACAAWwBUAGUAeAB0AC4ARQBuAGMAbwBkAGkAbgBnAF0AOgA6AFUAVABGADgAKQAgAC0AcgBlAHAAbABhAGMAZQAgACIAYAByAGAAbgAiACwAIAAiAGAAbgAiAAoAJABjAG8AZABlACAAPQAgAFsAcgBlAGcAZQB4AF0AOgA6AE0AYQB0AGMAaAAoACQAbQBkACwAIAAnACgAPwBzACkAYABgAGAAcABvAHcAZQByAHMAaABlAGwAbABcAG4AKAAuACoAPwApAFwAbgBgAGAAYAAnACkALgBHAHIAbwB1AHAAcwBbADEAXQAuAFYAYQBsAHUAZQAKACQAcwBoAGEAIAA9ACAALQBqAG8AaQBuACAAKABbAFMAZQBjAHUAcgBpAHQAeQAuAEMAcgB5AHAAdABvAGcAcgBhAHAAaAB5AC4AUwBIAEEAMgA1ADYAXQA6ADoAQwByAGUAYQB0AGUAKAApAC4AQwBvAG0AcAB1AHQAZQBIAGEAcwBoACgAWwBUAGUAeAB0AC4ARQBuAGMAbwBkAGkAbgBnAF0AOgA6AFUAVABGADgALgBHAGUAdABCAHkAdABlAHMAKAAkAGMAbwBkAGUAKQApACAAfAAgAEYAbwByAEUAYQBjAGgALQBPAGIAagBlAGMAdAAgAHsAIAAkAF8ALgBUAG8AUwB0AHIAaQBuAGcAKAAnAHgAMgAnACkAIAB9ACkACgBpAGYAIAAoACQAcwBoAGEAIAAtAG4AZQAgACQASAApACAAewAgAFcAcgBpAHQAZQAtAEgAbwBzAHQAIAAiAFsAUgBFAEQAXQAgAABOdZMLeg9fvHggAFMASABBAC0AMgA1ADYAIAANTg1cKAAkAHMAaABhACkAtwAgAA1O91dMiCIAIAAtAEYAbwByAGUAZwByAG8AdQBuAGQAQwBvAGwAbwByACAAUgBlAGQAOwAgAHIAZQB0AHUAcgBuACAAfQAKAFcAcgBpAHQAZQAtAEgAbwBzAHQAIAAoACcAWwBHAFIARQBFAE4AXQAgAABOdZMLeg9fvHggAFMASABBAC0AMgA1ADYAIAAnACAAKwAgACQASAAuAFMAdQBiAHMAdAByAGkAbgBnACgAMAAsACAAMQAyACkAIAArACAAJwAgAPh2JnsgAJIhIAD3V0yIJwApACAALQBGAG8AcgBlAGcAcgBvAHUAbgBkAEMAbwBsAG8AcgAgAEcAcgBlAGUAbgAKACYAIAAoAFsAcwBjAHIAaQBwAHQAYgBsAG8AYwBrAF0AOgA6AEMAcgBlAGEAdABlACgAJABjAG8AZABlACkAKQAKAA==
```

或:在 cmd 先輸入 `powershell` 按 Enter(提示字元變成 `PS C:\Users\tonyk>`),再貼下面整段程式碼。

程式碼 SHA-256(本文 · 一行核對的就是這個):`60e5515615e0`

```powershell
& {
  # ===== VRN-1 / VRN-2 操作員一鍵 v0100(2026-10-20 · 操作員「INTEGRATE ABOVE INTO ONE CODE TO HANDLE ALL ABOVE. git pull」)=====
  # VRN-1 與 VRN-2 是兩個獨立系統、各有自己的 MAIN;本段只依序呼叫兩邊自己的入口,不改任何一邊的程式 / 冊 / 號(VCGC · VDF 不碰):
  #   ① VRN-1 倉 git pull(main · 只快轉 · 有沒提交的改動 → 先 git stash 保存,不丟)
  #   ② VRN-2 一鍵 v0132(從 GitHub 讀 · SHA-256 相符才執行 · 啟動器 ①~⑫:② 寫 VRN-2 借出工具冊 · ⑫ 借 VRN-1 的 PIVOT)
  #   ③ VRN-1 MAIN(artifacts\VRN-1.ps1 · PowerShell 7):check → run --no-cache(G23 借 VRN-2 的段落標題 / OCR · 只寫輸出夾,不寫倉)
  #   ④ 總結:每一步的燈 · 借用結果 · 結束碼(GREEN 0 / YELLOW 2 / RED 1)
  # 開關:$env:VIA_VRN1_ROOT(VRN-1 倉)· $env:VRN2_ROOT(VIA 根)· $env:VRN1_SAMPLES(VRN-1 樣本夾 · 不設 = VRN-1 自己的預設)· $env:VRN1_OUT(VRN-1 輸出夾)
  #       $env:VRN1_ARGS(多給 VRN-1 run 的旗標 · 例 '--no-open')· $env:VRN_PAIR_NO_PULL = '1' 不拉 · $env:VRN_PAIR_NO_STASH = '1' 有改動就不拉
  #       $env:VRN_PAIR_SKIP = 'VRN-1' 或 'VRN-2' 這次跳過那一邊(另一邊照常)
  $ErrorActionPreference = 'Continue'
  try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch { }
  $V1 = if ($env:VIA_VRN1_ROOT) { $env:VIA_VRN1_ROOT } else { 'C:\Users\tonyk\VIA-VDF-VRN' }
  $R  = if ($env:VRN2_ROOT) { $env:VRN2_ROOT } else { 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics' }
  $Br = 'claude/optimistic-goodall-yhalc5'                                         # VRN-2 發行所在的 GitHub 分支(只讀取 · 讀不到 → main)
  $P2 = 'VeritasIntelligenceAnalytics/docs/handoff/ai/vrn2_release_v0132'
  $H2 = 'c68b66b0ddf428821f57a694f890c607393b0530700bb8e4ad2ea8003089b3f4'   # VRN-2 一鍵 v0132 程式碼 SHA-256
  $env:VIA_VRN1_ROOT = $V1; $env:VIA_VRN2_ROOT = $R                                # 兩邊找對方都看同一個位置
  $skip = "$env:VRN_PAIR_SKIP"
  $res = [ordered]@{}
  $col = @{ GREEN = 'Green'; YELLOW = 'Yellow'; RED = 'Red'; GRAY = 'DarkGray' }
  $t0 = Get-Date
  function Say([string]$k, [string]$lamp, [string]$msg) {
    $res[$k] = @($lamp, $msg)
    Write-Host ("[{0}] {1} · {2}" -f $lamp, $k, $msg) -ForegroundColor $col[$lamp]
  }
  Write-Host ("══════ VRN-1 / VRN-2 操作員一鍵 v0100 · {0} · VRN-1 {1} · VIA {2} ══════" -f $t0.ToString('yyyy-MM-dd HH:mm:ss'), $V1, $R) -ForegroundColor Cyan

  # ① VRN-1 git pull
  $k1 = '① VRN-1 git pull'
  if ($skip -eq 'VRN-1') { Say $k1 GRAY '跳過(VRN_PAIR_SKIP=VRN-1)' }
  elseif (-not (Get-Command git -ErrorAction SilentlyContinue)) { Say $k1 RED '找不到 git(裝 Git for Windows 後再跑)' }
  elseif (-not (Test-Path -LiteralPath (Join-Path $V1 '.git'))) { Say $k1 RED "$V1 不是 VRN-1 的 git 倉 · 設 `$env:VIA_VRN1_ROOT = '<VRN-1 倉>' 後再跑" }
  elseif ($env:VRN_PAIR_NO_PULL -eq '1') { Say $k1 GRAY '不拉(VRN_PAIR_NO_PULL=1)· 照現狀跑' }
  else {
    $okf = $false
    foreach ($w in 0, 2, 4, 8, 16) { if ($w) { Start-Sleep -Seconds $w }; git -C $V1 fetch -q origin main 2>&1 | Out-Null; if ($LASTEXITCODE -eq 0) { $okf = $true; break } }
    $cur = "$(git -C $V1 rev-parse --abbrev-ref HEAD 2>$null)".Trim()
    $old = "$(git -C $V1 rev-parse --short HEAD 2>$null)".Trim()
    $dirty = @(git -C $V1 status --porcelain --untracked-files=no 2>$null | Where-Object { $_ })
    $note = @()
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
        if ($cur -ne 'main') {
          git -C $V1 switch -q main 2>&1 | Out-Null
          if ($LASTEXITCODE -ne 0) { git -C $V1 switch -q -c main --track origin/main 2>&1 | Out-Null }
          if ($LASTEXITCODE -eq 0) { $note += "分支 $cur → main(原分支還在)" } else { $note += "切不到 main(留在 $cur)" }
        }
        git -C $V1 pull -q --ff-only origin main 2>&1 | Out-Null
        $pr = $LASTEXITCODE
        $new = "$(git -C $V1 rev-parse --short HEAD 2>$null)".Trim()
        $tail = $(if ($note.Count) { ' · ' + ($note -join ' · ') } else { '' })
        if ($pr -eq 0) { Say $k1 GREEN ("main {0} → {1}{2}" -f $old, $new, $tail) }
        else { Say $k1 YELLOW ("不能快轉(本機 main 有自己的提交)· 照現狀 {0} 跑{1}" -f $new, $tail) }
      }
    }
    $mf1 = Join-Path $V1 'functional modules\VRN\ssot\VRN_ToolManifest_v0100.json'
    if (Test-Path -LiteralPath $mf1) { Write-Host "    [計] VRN-1 借出工具冊在 $mf1" -ForegroundColor DarkGray }
    else { Write-Host '    [計] VRN-1 這一版沒有借出工具冊 → ② 的 ⑫ 會灰(VRN-2 照常)' -ForegroundColor Yellow }
  }

  # ② VRN-2 一鍵 v0132
  $k2 = '② VRN-2 一鍵 v0132'
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
        git -C $top archive --format=zip -o $z ('origin/' + $b + ':' + $P2) VRN2_OneClick_v0132.md 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $z)) { $src = $b; break }
      }
      if (-not $src) { Say $k2 RED "讀不到 GitHub 分支 $Br 或 main 的 VRN-2 一鍵 v0132(網路 / git)" }
      else {
        Expand-Archive -LiteralPath $z -DestinationPath $tmp -Force
        $md2 = [IO.File]::ReadAllText((Join-Path $tmp 'VRN2_OneClick_v0132.md'), [Text.Encoding]::UTF8) -replace "`r`n", "`n"
        $code2 = [regex]::Match($md2, '(?s)```powershell\n(.*?)\n```').Groups[1].Value
        $sha2 = -join ([Security.Cryptography.SHA256]::Create().ComputeHash([Text.Encoding]::UTF8.GetBytes($code2)) | ForEach-Object { $_.ToString('x2') })
        if ($sha2 -ne $H2) { Say $k2 RED ("VRN-2 一鍵程式碼 SHA-256 不對({0})· 不執行" -f $sha2.Substring(0, 12)) }
        else {
          Write-Host ("[計] VRN-2 一鍵 v0132 程式碼 SHA-256 {0} 相符(GitHub {1})→ 執行 VRN-2 自己的流程" -f $H2.Substring(0, 12), $src) -ForegroundColor DarkGray
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
  $ps1 = Join-Path $V1 'artifacts\VRN-1.ps1'
  if ($skip -eq 'VRN-1') { Say $k3 GRAY '跳過(VRN_PAIR_SKIP=VRN-1)' }
  elseif (-not (Test-Path -LiteralPath $ps1)) { Say $k3 RED "找不到 $ps1 · VRN-1 倉不在 $($V1) 的話設 `$env:VIA_VRN1_ROOT = '<VRN-1 倉>'" }
  else {
    $pw = Get-Command pwsh -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $pw) { Say $k3 RED 'VRN-1 要 PowerShell 7(pwsh)· 安裝:winget install --id Microsoft.PowerShell · 裝好再貼一次' }
    else {
      Write-Host '──── VRN-1 check ────' -ForegroundColor Cyan
      & $pw.Source -NoProfile -ExecutionPolicy Bypass -WorkingDirectory $V1 -File $ps1 check 2>&1 | ForEach-Object { Write-Host "$_" }
      $rcC = [int]$LASTEXITCODE
      $a1 = @('run', '--no-cache')
      if ($env:VRN1_SAMPLES) { $a1 += @('--samples', $env:VRN1_SAMPLES) }
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
  $lamps = @($res.Values | ForEach-Object { $_[0] })
  $final = if ($lamps -contains 'RED') { 'RED' } elseif ($lamps -contains 'YELLOW') { 'YELLOW' } else { 'GREEN' }
  $msg = @{ GREEN = '兩個系統都跑完 · VRN-1 已是最新 main · VRN-2 ⑫ 借 VRN-1 的 PIVOT · VRN-1 G23 借 VRN-2 的段落標題 / OCR · 把總結這幾行貼回'
            YELLOW = '跑完但有黃燈 · 看上面黃的那一步(說明裡有下一步)· 把總結這幾行貼回'
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
$P  = 'VeritasIntelligenceAnalytics/docs/handoff/ai/vrn1_vrn2_oneclick_v0100'
$H  = '60e5515615e0cb96fa1c532ec280d28a91d8dd61d49f91de203a1b393519134a'
Write-Host ('[VRN-1 / VRN-2] PowerShell ' + $PSVersionTable.PSVersion + ' · 從 GitHub 讀操作員一鍵 v0100(核對 SHA-256 後執行)') -ForegroundColor Yellow
$top = git -C $R rev-parse --show-toplevel 2>$null
if (-not $top) { Write-Host "[RED] $R 不是 git 倉或找不到 git" -ForegroundColor Red; return }
$top = "$top".Trim()
$t = Join-Path ([IO.Path]::GetTempPath()) ('vrn12_boot_' + (Get-Date).ToString('yyyyMMdd_HHmmss'))
New-Item -ItemType Directory -Force -Path $t | Out-Null
$z = Join-Path $t 'pair.zip'; $okz = $false
foreach ($b in $Br, 'main') {
  foreach ($w in 0, 2, 4, 8, 16) { if ($w) { Start-Sleep -Seconds $w }; git -C $top fetch -q origin $b 2>&1 | Out-Null; if ($LASTEXITCODE -eq 0) { break } }
  git -C $top archive --format=zip -o $z ('origin/' + $b + ':' + $P) VRN1_VRN2_OneClick_v0100.md 2>&1 | Out-Null
  if ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $z)) { $okz = $true; Write-Host ('[計] 一鍵程式碼來源 GitHub ' + $b) -ForegroundColor DarkGray; break }
}
if (-not $okz) { Write-Host "[RED] 讀不到 GitHub 分支 $Br 或 main 的操作員一鍵(網路 / git)" -ForegroundColor Red; return }
Expand-Archive -LiteralPath $z -DestinationPath $t -Force
$md = [IO.File]::ReadAllText((Join-Path $t 'VRN1_VRN2_OneClick_v0100.md'), [Text.Encoding]::UTF8) -replace "`r`n", "`n"
$code = [regex]::Match($md, '(?s)```powershell\n(.*?)\n```').Groups[1].Value
$sha = -join ([Security.Cryptography.SHA256]::Create().ComputeHash([Text.Encoding]::UTF8.GetBytes($code)) | ForEach-Object { $_.ToString('x2') })
if ($sha -ne $H) { Write-Host "[RED] 一鍵程式碼 SHA-256 不對($sha)· 不執行" -ForegroundColor Red; return }
Write-Host ('[GREEN] 一鍵程式碼 SHA-256 ' + $H.Substring(0, 12) + ' 相符 → 執行') -ForegroundColor Green
& ([scriptblock]::Create($code))
```
