# VRN-2 · PowerShell 7 一段碼處理全部 · VRN2_HandleAll_v0102(2026-10-30 · 套件 v0154)

v0102 = v0101(桌機 20:09 整輪跑通:DUPKEY 0 · 管理器 v0257 改名 37 · 剔除 8 · 收尾 OPEN「VRN-2 2 項」= ⑥f 共識)+ 套件 v0154(ConsensusJoin v0103)+ RoundAll v0110,
再加一條**短的開機行**:PowerShell 7 的輸入列(PSReadLine 2.4.5)在 133 × 33 的視窗裡貼約 8,700 字元的一行會當掉
(`Oops, something went wrong` · `IndexOutOfRangeException` · `ConvertOffsetToPoint`)—— 那是 PowerShell 輸入列的毛病,不是 VRN-2 的碼。
短開機行只有 1,719 個字元(全是 ASCII · 約 13 行),它從 GitHub 取本檔、核對下面「Handle-All 那一行」的 SHA-256(`a3d4dc8b9f8b`)相符才執行。

## PowerShell 7 視窗貼這一行(短 · 不會讓輸入列當掉)

```powershell
& { $R = $env:VRN2_ROOT ?? 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'; $P = 'VeritasIntelligenceAnalytics/docs/handoff/ai/vrn2_release_v0154'; $F = 'VRN2_HandleAll_v0102.md'; $H = 'a3d4dc8b9f8bf3d47eff359ad7c56548f5779a80968db6e3ee6178746c37f34b'; $top = "$(git -C $R rev-parse --show-toplevel 2>$null)".Trim(); if (-not $top) { Write-Host "[RED] boot: $R is not a git repo (set `$env:VRN2_ROOT)" -ForegroundColor Red; return }; $t = Join-Path ([IO.Path]::GetTempPath()) "vrn2_boot_$(Get-Date -Format yyyyMMddHHmmss)"; $z = Join-Path $t 'ha.zip'; New-Item -ItemType Directory -Force -Path $t | Out-Null; $ok = $false; foreach ($b in 'claude/optimistic-goodall-yhalc5', 'main') { foreach ($w in 0, 3, 9) { Start-Sleep -Seconds $w; git -C $top fetch -q origin $b 2>&1 | Out-Null; if ($LASTEXITCODE -eq 0) { break } }; git -C $top archive --format=zip -o $z "origin/$($b):$($P)" $F 2>&1 | Out-Null; if ($LASTEXITCODE -eq 0) { $ok = $true; break } }; if (-not $ok) { Write-Host "[RED] boot: cannot read $F from GitHub" -ForegroundColor Red; return }; Expand-Archive -LiteralPath $z -DestinationPath $t -Force; $md = [IO.File]::ReadAllText((Join-Path $t $F), [Text.Encoding]::UTF8) -replace "`r`n", "`n"; $c = [regex]::Match($md, '(?s)<!-- handle-all line -->\n```powershell\n(.*?)\n```').Groups[1].Value; $s = ([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash([Text.UTF8Encoding]::new($false).GetBytes($c))) -replace '-', '').ToLowerInvariant(); if ($s -ne $H) { Write-Host "[RED] boot: SHA-256 $s is not $H - not run" -ForegroundColor Red; return }; Write-Host "[GREEN] boot: Handle-All v0102 SHA-256 OK ($b)" -ForegroundColor Green; Invoke-Expression $c }
```

## cmd 視窗貼這一行(內容 = 上面那行 · 經 pwsh 執行 · 不經 PowerShell 輸入列)

```bat
pwsh -NoProfile -ExecutionPolicy Bypass -EncodedCommand JgAgAHsAIAAkAFIAIAA9ACAAJABlAG4AdgA6AFYAUgBOADIAXwBSAE8ATwBUACAAPwA/ACAAJwBDADoAXABVAHMAZQByAHMAXAB0AG8AbgB5AGsAXABPAG4AZQBEAHIAaQB2AGUAXABEAG8AYwB1AG0AZQBuAHQAcwBcAG0AbwB2AGkAZQBzAC0AZABhAHQAYQBzAGUAdABcAFYAZQByAGkAdABhAHMASQBuAHQAZQBsAGwAaQBnAGUAbgBjAGUAQQBuAGEAbAB5AHQAaQBjAHMAJwA7ACAAJABQACAAPQAgACcAVgBlAHIAaQB0AGEAcwBJAG4AdABlAGwAbABpAGcAZQBuAGMAZQBBAG4AYQBsAHkAdABpAGMAcwAvAGQAbwBjAHMALwBoAGEAbgBkAG8AZgBmAC8AYQBpAC8AdgByAG4AMgBfAHIAZQBsAGUAYQBzAGUAXwB2ADAAMQA1ADQAJwA7ACAAJABGACAAPQAgACcAVgBSAE4AMgBfAEgAYQBuAGQAbABlAEEAbABsAF8AdgAwADEAMAAyAC4AbQBkACcAOwAgACQASAAgAD0AIAAnAGEAMwBkADQAZABjADgAYgA5AGYAOABiAGYAMwBkADQANwBlAGYAZgAzADUAOQBhAGQANwBjADUANgA1ADQAOABmADUANwA3ADkAYQA4ADAAOQA2ADgAZABiADYAZQAzAGUAZQA2ADEANwA4ADcANAA2AGMAMwA3AGYAMwA0AGIAJwA7ACAAJAB0AG8AcAAgAD0AIAAiACQAKABnAGkAdAAgAC0AQwAgACQAUgAgAHIAZQB2AC0AcABhAHIAcwBlACAALQAtAHMAaABvAHcALQB0AG8AcABsAGUAdgBlAGwAIAAyAD4AJABuAHUAbABsACkAIgAuAFQAcgBpAG0AKAApADsAIABpAGYAIAAoAC0AbgBvAHQAIAAkAHQAbwBwACkAIAB7ACAAVwByAGkAdABlAC0ASABvAHMAdAAgACIAWwBSAEUARABdACAAYgBvAG8AdAA6ACAAJABSACAAaQBzACAAbgBvAHQAIABhACAAZwBpAHQAIAByAGUAcABvACAAKABzAGUAdAAgAGAAJABlAG4AdgA6AFYAUgBOADIAXwBSAE8ATwBUACkAIgAgAC0ARgBvAHIAZQBnAHIAbwB1AG4AZABDAG8AbABvAHIAIABSAGUAZAA7ACAAcgBlAHQAdQByAG4AIAB9ADsAIAAkAHQAIAA9ACAASgBvAGkAbgAtAFAAYQB0AGgAIAAoAFsASQBPAC4AUABhAHQAaABdADoAOgBHAGUAdABUAGUAbQBwAFAAYQB0AGgAKAApACkAIAAiAHYAcgBuADIAXwBiAG8AbwB0AF8AJAAoAEcAZQB0AC0ARABhAHQAZQAgAC0ARgBvAHIAbQBhAHQAIAB5AHkAeQB5AE0ATQBkAGQASABIAG0AbQBzAHMAKQAiADsAIAAkAHoAIAA9ACAASgBvAGkAbgAtAFAAYQB0AGgAIAAkAHQAIAAnAGgAYQAuAHoAaQBwACcAOwAgAE4AZQB3AC0ASQB0AGUAbQAgAC0ASQB0AGUAbQBUAHkAcABlACAARABpAHIAZQBjAHQAbwByAHkAIAAtAEYAbwByAGMAZQAgAC0AUABhAHQAaAAgACQAdAAgAHwAIABPAHUAdAAtAE4AdQBsAGwAOwAgACQAbwBrACAAPQAgACQAZgBhAGwAcwBlADsAIABmAG8AcgBlAGEAYwBoACAAKAAkAGIAIABpAG4AIAAnAGMAbABhAHUAZABlAC8AbwBwAHQAaQBtAGkAcwB0AGkAYwAtAGcAbwBvAGQAYQBsAGwALQB5AGgAYQBsAGMANQAnACwAIAAnAG0AYQBpAG4AJwApACAAewAgAGYAbwByAGUAYQBjAGgAIAAoACQAdwAgAGkAbgAgADAALAAgADMALAAgADkAKQAgAHsAIABTAHQAYQByAHQALQBTAGwAZQBlAHAAIAAtAFMAZQBjAG8AbgBkAHMAIAAkAHcAOwAgAGcAaQB0ACAALQBDACAAJAB0AG8AcAAgAGYAZQB0AGMAaAAgAC0AcQAgAG8AcgBpAGcAaQBuACAAJABiACAAMgA+ACYAMQAgAHwAIABPAHUAdAAtAE4AdQBsAGwAOwAgAGkAZgAgACgAJABMAEEAUwBUAEUAWABJAFQAQwBPAEQARQAgAC0AZQBxACAAMAApACAAewAgAGIAcgBlAGEAawAgAH0AIAB9ADsAIABnAGkAdAAgAC0AQwAgACQAdABvAHAAIABhAHIAYwBoAGkAdgBlACAALQAtAGYAbwByAG0AYQB0AD0AegBpAHAAIAAtAG8AIAAkAHoAIAAiAG8AcgBpAGcAaQBuAC8AJAAoACQAYgApADoAJAAoACQAUAApACIAIAAkAEYAIAAyAD4AJgAxACAAfAAgAE8AdQB0AC0ATgB1AGwAbAA7ACAAaQBmACAAKAAkAEwAQQBTAFQARQBYAEkAVABDAE8ARABFACAALQBlAHEAIAAwACkAIAB7ACAAJABvAGsAIAA9ACAAJAB0AHIAdQBlADsAIABiAHIAZQBhAGsAIAB9ACAAfQA7ACAAaQBmACAAKAAtAG4AbwB0ACAAJABvAGsAKQAgAHsAIABXAHIAaQB0AGUALQBIAG8AcwB0ACAAIgBbAFIARQBEAF0AIABiAG8AbwB0ADoAIABjAGEAbgBuAG8AdAAgAHIAZQBhAGQAIAAkAEYAIABmAHIAbwBtACAARwBpAHQASAB1AGIAIgAgAC0ARgBvAHIAZQBnAHIAbwB1AG4AZABDAG8AbABvAHIAIABSAGUAZAA7ACAAcgBlAHQAdQByAG4AIAB9ADsAIABFAHgAcABhAG4AZAAtAEEAcgBjAGgAaQB2AGUAIAAtAEwAaQB0AGUAcgBhAGwAUABhAHQAaAAgACQAegAgAC0ARABlAHMAdABpAG4AYQB0AGkAbwBuAFAAYQB0AGgAIAAkAHQAIAAtAEYAbwByAGMAZQA7ACAAJABtAGQAIAA9ACAAWwBJAE8ALgBGAGkAbABlAF0AOgA6AFIAZQBhAGQAQQBsAGwAVABlAHgAdAAoACgASgBvAGkAbgAtAFAAYQB0AGgAIAAkAHQAIAAkAEYAKQAsACAAWwBUAGUAeAB0AC4ARQBuAGMAbwBkAGkAbgBnAF0AOgA6AFUAVABGADgAKQAgAC0AcgBlAHAAbABhAGMAZQAgACIAYAByAGAAbgAiACwAIAAiAGAAbgAiADsAIAAkAGMAIAA9ACAAWwByAGUAZwBlAHgAXQA6ADoATQBhAHQAYwBoACgAJABtAGQALAAgACcAKAA/AHMAKQA8ACEALQAtACAAaABhAG4AZABsAGUALQBhAGwAbAAgAGwAaQBuAGUAIAAtAC0APgBcAG4AYABgAGAAcABvAHcAZQByAHMAaABlAGwAbABcAG4AKAAuACoAPwApAFwAbgBgAGAAYAAnACkALgBHAHIAbwB1AHAAcwBbADEAXQAuAFYAYQBsAHUAZQA7ACAAJABzACAAPQAgACgAWwBCAGkAdABDAG8AbgB2AGUAcgB0AGUAcgBdADoAOgBUAG8AUwB0AHIAaQBuAGcAKABbAFMAZQBjAHUAcgBpAHQAeQAuAEMAcgB5AHAAdABvAGcAcgBhAHAAaAB5AC4AUwBIAEEAMgA1ADYAXQA6ADoAQwByAGUAYQB0AGUAKAApAC4AQwBvAG0AcAB1AHQAZQBIAGEAcwBoACgAWwBUAGUAeAB0AC4AVQBUAEYAOABFAG4AYwBvAGQAaQBuAGcAXQA6ADoAbgBlAHcAKAAkAGYAYQBsAHMAZQApAC4ARwBlAHQAQgB5AHQAZQBzACgAJABjACkAKQApACAALQByAGUAcABsAGEAYwBlACAAJwAtACcALAAgACcAJwApAC4AVABvAEwAbwB3AGUAcgBJAG4AdgBhAHIAaQBhAG4AdAAoACkAOwAgAGkAZgAgACgAJABzACAALQBuAGUAIAAkAEgAKQAgAHsAIABXAHIAaQB0AGUALQBIAG8AcwB0ACAAIgBbAFIARQBEAF0AIABiAG8AbwB0ADoAIABTAEgAQQAtADIANQA2ACAAJABzACAAaQBzACAAbgBvAHQAIAAkAEgAIAAtACAAbgBvAHQAIAByAHUAbgAiACAALQBGAG8AcgBlAGcAcgBvAHUAbgBkAEMAbwBsAG8AcgAgAFIAZQBkADsAIAByAGUAdAB1AHIAbgAgAH0AOwAgAFcAcgBpAHQAZQAtAEgAbwBzAHQAIAAiAFsARwBSAEUARQBOAF0AIABiAG8AbwB0ADoAIABIAGEAbgBkAGwAZQAtAEEAbABsACAAdgAwADEAMAAyACAAUwBIAEEALQAyADUANgAgAE8ASwAgACgAJABiACkAIgAgAC0ARgBvAHIAZQBnAHIAbwB1AG4AZABDAG8AbABvAHIAIABHAHIAZQBlAG4AOwAgAEkAbgB2AG8AawBlAC0ARQB4AHAAcgBlAHMAcwBpAG8AbgAgACQAYwAgAH0A
```

還是當掉(很窄的視窗):先在 PowerShell 7 貼 `Remove-Module PSReadLine`(只關這個視窗的輸入列加強 · 關掉視窗就恢復)再貼上面那一行。

## 它會做什麼

① 工具(git · python · VIA 倉)→ ② 有沒有別的 VRN-2 在跑 → ③ `Downloads` 的舊套件夾讀不讀得到(讀不到:列出來、問要不要以系統管理員身分還原權限 · 不擋)
→ ④ 選模式(預設 auto)→ ⑤ 從 GitHub 取 `VRN2_RoundAll_v0110.py` **核對 SHA-256**(`cc1d4b5d7a04`)→ ⑥ 執行 → ⑦ 印**收尾狀態**、各負責方的待辦、貼回包位置。
整段包在 `& { … }` 裡,錯了用 `return` —— **視窗不會關**。

## 模式(預設 auto)

| 模式 | 怎麼指定 | 做什麼 | 桌機時間 |
|---|---|---|---|
| `auto` | (不用設) | 上一輪收據是啟動器 **v0153 以後**、而且輸出冊在 → `repair`;不然 → `full` | — |
| `repair` | `$env:VRN2_MODE = 'repair'` | 取套件 v0154 → **⑤ 自動修**:⑥f 共識閘只因 404 / 一時抓不到 FAIL_CLOSED(ConsensusJoin v0103 以前做的)→ 套件的 ConsensusJoin v0103 只增不覆寫地補放 → 用它重跑 ⑥f(今天抓到的沿用 · 只重抓沒抓到的 · 重試)→ 重組 Combined → 增量庫 · Workbench → 除錯報告 → 收尾頁 → 貼回包 | 幾分鐘 |
| `full` | `$env:VRN2_MODE = 'full'` | 整輪:取套件 v0154 → 診斷 → 全部自測 → 跑啟動器 v0154 → 自動修 → 除錯報告 → 收尾頁 → 貼回包 | 約 40 分鐘 |
| `verify` | `$env:VRN2_MODE = 'verify'` | 取套件 v0154 → 只重跑 ⑪ 獨立驗證(IndependentVerifier v0114)→ 除錯報告 → 收尾頁 → 貼回包 | 約 10 分鐘 |
| `report` | `$env:VRN2_MODE = 'report'` | 只重做除錯報告 → 收尾頁 → 貼回包 | 幾秒 |

先在同一個視窗貼 `$env:VRN2_MODE = 'full'` 再貼那一行;用完 `Remove-Item Env:VRN2_MODE`。要用的模式需要上一輪輸出冊、但沒有 → 自動改跑整輪。

## 這次桌機(2026-10-30 20:09 整輪之後)貼下去會怎樣

上一輪收據是 `VRN2_Closeout_v0153.json`、輸出冊在 → auto 選 **repair**(不整輪):⑤ 看到 ⑥f 共識閘 FAIL_CLOSED 只因 8358 / 2891 一時抓不到(`ASSIGNED_JSON_NOT_FOUND`)
→ 用 ConsensusJoin **v0103** 重跑 ⑥f:今天的 checkpoint 是別份代號清單 → 抓到的 38 份搬進 43 檔清單的 checkpoint(引擎續跑沿用)→ 只重抓 8358 / 2891 / 4171 / 6933 / 7728
→ 還是 404 的不納入閘(鉅亨沒有 FactSet 頁)· 一時抓不到的重試(等 30 / 60 秒)· 還是沒有 → 「鉅亨這次沒給資料」(黃 · 資料源)→ 重組 Combined(那幾列寫它自己的原因)→ 收尾頁。
(明天以後再跑:checkpoint 不是今天的 → 照引擎一天一抓 43 檔;拿掉 404 再跑那次不再上網。)
收尾頁同一件事只列一次:⑥f 步驟列 + 共識閘 FAIL 列 + Combined 的「共識缺」= 一項。容器裡用同樣的流程重演了桌機 20:09 的狀態,結果在 `VRN2_Verification_v0154.md`。

## 環境變數(都可不設)

| 變數 | 用途 |
|---|---|
| `$env:VRN2_ROOT` | VIA 根(預設 `C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics`)· cmd 用 `set VRN2_ROOT=…` |
| `$env:VRN2_PY` | 指定 python(預設找 `python` / `py`,不用 WindowsApps 的假 python) |
| `$env:VRN2_MODE` | `auto` · `repair` · `full` · `verify` · `report` |
| `$env:VRN2_ROUNDALL_ARGS` | 多帶給 RoundAll 的參數(例 `'--integrate yes'`、`'--no-open'`) |
| `$env:VRN2_YES` | ② 有別的 VRN-2 在跑時不問、直接回答(`y` 繼續 · `n` 停) |
| `$env:VRN2_FIX_ACL` | ③ 舊套件夾讀不到時不問、直接回答(`y` 以系統管理員身分 `icacls /reset` · `n` 不動) |
| `$env:VRN2_NO_UI` | `1` = 跑完不開收尾頁 |
| `$env:VIA_VRN2_CONSENSUS_RETRY_WAIT` / `VIA_VRN2_CONSENSUS_RETRIES` | ⑥f 一時抓不到時等幾秒(預設 30 · 第 n 次 × n)/ 重試幾次(預設 2 · 0 = 不重試) |

## 程式碼決定不了的(收尾頁會分好)

- **交 VCGC**:⑥e MOPS 財報 —— VIA 鎖版網路工具的合規層拒絕(DENY),VRN-2 / VDF 不繞道。
- **人工核對**:MQ-1560 影像頁 OCR 摘錄對原圖(四點 4)· 年度數據缺項 3 份(原文真的沒有年度表就是沒有)。
- **資料源沒有**:GFHK Apple(代號 AAPL,不是台股)· 神達 3706 / 緯穎 6669 報告日前沒有還原價(VDF 日線視窗 PARTIAL)· 鉅亨沒有 FactSet 頁(404)· 鉅亨這次沒給資料(重試後仍沒有 · 下輪再抓)。

## Handle-All 那一行(短開機行從 GitHub 取這段、核對 SHA-256 `a3d4dc8b9f8b` 相符才執行 · 不用貼它)

<!-- handle-all line -->
```powershell
& { $ErrorActionPreference = 'Continue'; $ProgressPreference = 'SilentlyContinue'; if ($PSVersionTable.PSVersion.Major -lt 7) { Write-Host '[RED] 這段要 PowerShell 7 以上(pwsh · 例 7.6.9)' -ForegroundColor Red; return }; try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch { }; $T0 = Get-Date; $R = $env:VRN2_ROOT ?? 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'; $P = 'VeritasIntelligenceAnalytics/docs/handoff/ai/vrn2_release_v0154'; $F = 'VRN2_RoundAll_v0110.py'; $H = 'cc1d4b5d7a04783faa6363baf2b9c35cb6f298e32432b32104e0f9b682c49484'; $DL = Join-Path ($env:USERPROFILE ?? $HOME) 'Downloads'; $V2 = Join-Path $R 'VIA_Reports' 'vrn2'; $Mode = "$($env:VRN2_MODE ?? 'auto')".Trim().ToLowerInvariant(); if ($Mode -notin 'auto', 'full', 'repair', 'verify', 'report') { Write-Host "[RED] VRN2_MODE = $($Mode) 不認得(auto / full / repair / verify / report)" -ForegroundColor Red; return }; Write-Host "[VRN-2] Handle-All v0102 · PowerShell $($PSVersionTable.PSVersion) · 模式 $($Mode) · VIA $($R)" -ForegroundColor Yellow; $git = (Get-Command git -ErrorAction SilentlyContinue | Select-Object -First 1).Source; if (-not $git) { Write-Host '[RED] ① 找不到 git(裝 Git for Windows 後重開 PowerShell 7)' -ForegroundColor Red; return }; $top = "$(git -C $R rev-parse --show-toplevel 2>$null)".Trim(); if (-not $top) { Write-Host "[RED] ① $($R) 不是 git 倉(先設 `$env:VRN2_ROOT = '<VIA 根>')" -ForegroundColor Red; return }; $py = $env:VRN2_PY ?? (Get-Command python, py -ErrorAction SilentlyContinue | Where-Object Source -NotMatch 'WindowsApps' | Select-Object -First 1).Source; if (-not $py) { Write-Host '[RED] ① 找不到 python(不要用 WindowsApps 的假 python · 或先設 $env:VRN2_PY)' -ForegroundColor Red; return }; Write-Host "[GREEN] ① 工具 · git 倉 $($top) · $("$(& $py --version 2>&1)".Trim())($($py))" -ForegroundColor Green; if ($IsWindows) { $busy = @(Get-CimInstance Win32_Process -Filter "Name like 'python%'" -ErrorAction SilentlyContinue | Where-Object CommandLine -Match 'ActivateVRN-2|VRN2_RoundAll'); if ($busy) { Write-Host "[YELLOW] ② 已經有 $($busy.Count) 個 VRN-2 在跑(PID $($busy.ProcessId -join ', '))· 兩輪重疊會互搶鎖、變慢" -ForegroundColor Yellow; if (($env:VRN2_YES ?? (Read-Host '    等它跑完再貼比較好;還是要繼續嗎?(y/N)')) -notmatch '^[yY]') { Write-Host '[計] 沒有繼續(視窗不會關)'; return } } else { Write-Host '[GREEN] ② 沒有別的 VRN-2 在跑' -ForegroundColor Green } }; $bad = @(Get-ChildItem -LiteralPath $DL -Directory -Filter 'VRN2_Closeout_v0*' -ErrorAction SilentlyContinue | Where-Object { $ok = $true; try { foreach ($x in @(Get-ChildItem -LiteralPath $_.FullName -File -ErrorAction Stop)) { [IO.File]::OpenRead($x.FullName).Dispose() } } catch { $ok = $false }; -not $ok }); if ($bad) { Write-Host "[YELLOW] ③ $($bad.Count) 個舊套件夾目前的身分讀不到(以前用系統管理員身分跑過 · 權限只剩 Administrators):" -ForegroundColor Yellow; $bad | ForEach-Object { Write-Host "    $($_.FullName)" }; Write-Host '    不擋:RoundAll 會改用讀得到的夾 · 套件 v0154 裝在新夾 VRN2_Closeout_v0154' -ForegroundColor DarkGray; if ($IsWindows -and (($env:VRN2_FIX_ACL ?? (Read-Host '    要用系統管理員身分把它們的權限還原成跟 Downloads 一樣嗎?會跳 UAC(y/N)')) -match '^[yY]')) { $cmd = (@($bad | ForEach-Object { "icacls '" + ($_.FullName -replace "'", "''") + "' /reset /T /C /Q" }) -join '; '); try { Start-Process -FilePath (Get-Process -Id $PID).Path -Verb RunAs -Wait -ArgumentList ('-NoProfile -EncodedCommand ' + [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($cmd))) -ErrorAction Stop; foreach ($d in $bad) { $ok = $true; try { foreach ($x in @(Get-ChildItem -LiteralPath $d.FullName -File -ErrorAction Stop)) { [IO.File]::OpenRead($x.FullName).Dispose() } } catch { $ok = $false }; Write-Host "    [$(if ($ok) { 'GREEN' } else { 'YELLOW' })] $($d.FullName) $(if ($ok) { '讀得到了' } else { '還是讀不到(不擋)' })" -ForegroundColor ($ok ? 'Green' : 'Yellow') } } catch { Write-Host "[YELLOW] ③ 沒有以系統管理員身分執行($($_.Exception.Message))· 不擋" -ForegroundColor Yellow } } } else { Write-Host '[GREEN] ③ Downloads 的 VRN-2 套件夾都讀得到' -ForegroundColor Green }; $rcp = Get-ChildItem -LiteralPath $V2 -File -Filter 'VRN2_Closeout_v0*.json' -ErrorAction SilentlyContinue | Where-Object Name -Match '^VRN2_Closeout_v\d{4}\.json$' | Sort-Object Name | Select-Object -Last 1; $last = ($rcp -and $rcp.Name -match '_v(\d{4})\.json$') ? [int]$Matches[1] : 0; $haveOut = (Test-Path -LiteralPath (Join-Path $V2 'output' 'VRN2_FinancialData_latest.json')) -and (Test-Path -LiteralPath (Join-Path $V2 'scope_in')); if ($Mode -eq 'auto') { $Mode = ($last -ge 153 -and $haveOut) ? 'repair' : 'full'; Write-Host "[計] ④ 自動選模式 $($Mode) · 上一輪收據 $($rcp.Name ?? '沒有') · 上一輪輸出冊 $($haveOut ? '有' : '沒有')$(($Mode -eq 'full' -and $last -gt 0 -and $haveOut) ? '(上一輪輸出冊是啟動器 v0153 以前做的 · 管理器 v0257 要重做輸出冊)' : '')$(($Mode -eq 'repair') ? '(輸出冊是啟動器 v0153 以後做的 · 這版只改 ⑥f 共識 → 不整輪)' : '')(整輪:先貼 `$env:VRN2_MODE = 'full')" -ForegroundColor DarkGray }; if ($Mode -ne 'full' -and -not $haveOut) { Write-Host "[YELLOW] ④ 模式 $($Mode) 要上一輪的輸出冊 · 這裡沒有 → 改跑整輪" -ForegroundColor Yellow; $Mode = 'full' }; $ra = @(switch ($Mode) { 'repair' { '--only'; 'package,fix,report,closeout,pasteback' } 'verify' { '--only'; 'package,verify,report,closeout,pasteback' } 'report' { '--only'; 'report,closeout,pasteback' } }); $ra += @(($env:VRN2_ROUNDALL_ARGS ?? '') -split '\s+' | Where-Object { $_ }); $what = @{ full = '整輪(取套件 v0154 → 診斷 → 全部自測 → 跑啟動器 v0154(管理器 v0257 · ⑥f ConsensusJoin v0103)→ 自動修 → 除錯報告 → 收尾頁 → 貼回包 · 桌機約 40 分鐘)'; repair = '取套件 v0154 → ⑤ 自動修(⑥f 共識閘只因 404 / 一時抓不到 → 用 ConsensusJoin v0103 重跑 · 沿用今天抓到的 · 重組 Combined · 增量庫 · Workbench)→ 除錯報告 → 收尾頁 → 貼回包(幾分鐘)'; verify = '只重跑 ⑪ 獨立驗證(套件 v0154 的 IndependentVerifier v0114 · 用上一輪的輸出冊)→ 除錯報告 → 收尾頁 → 貼回包(約 10 分鐘)'; report = '只重做除錯報告 → 收尾頁 → 貼回包(用上一輪的結果 · 幾秒)' }[$Mode]; Write-Host "[計] ④ 模式 $($Mode):$($what)" -ForegroundColor Cyan; $t = Join-Path ([IO.Path]::GetTempPath()) "vrn2_handleall_$(Get-Date -Format yyyyMMdd_HHmmss)"; New-Item -ItemType Directory -Force -Path $t | Out-Null; $z = Join-Path $t 'roundall.zip'; $src = $null; foreach ($b in 'claude/optimistic-goodall-yhalc5', 'main') { foreach ($w in 0, 2, 4, 8, 16) { if ($w) { Start-Sleep -Seconds $w }; git -C $top fetch -q origin $b 2>&1 | Out-Null; if ($LASTEXITCODE -eq 0) { break } }; git -C $top archive --format=zip -o $z "origin/$($b):$($P)" $F 2>&1 | Out-Null; if ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $z)) { $src = $b; break } }; if (-not $src) { Write-Host "[RED] ⑤ 讀不到 GitHub 分支或 main 的 $($F)(網路 / git)" -ForegroundColor Red; return }; Expand-Archive -LiteralPath $z -DestinationPath $t -Force; $code = [IO.File]::ReadAllText((Join-Path $t $F), [Text.Encoding]::UTF8) -replace "`r`n", "`n"; $bytes = [Text.UTF8Encoding]::new($false).GetBytes($code); $sha = ([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash($bytes)) -replace '-', '').ToLowerInvariant(); if ($sha -ne $H) { Write-Host "[RED] ⑤ $($F) SHA-256 不對($($sha))· 不執行" -ForegroundColor Red; return }; New-Item -ItemType Directory -Force -Path $DL | Out-Null; $dst = Join-Path $DL $F; [IO.File]::WriteAllBytes($dst, $bytes); Write-Host "[GREEN] ⑤ $($F) SHA-256 $($H.Substring(0, 12)) 相符(GitHub $($src))→ $($dst)" -ForegroundColor Green; Write-Host "[計] ⑥ 執行 $($py) $($F) --root $($R) $($ra -join ' ')" -ForegroundColor DarkGray; & $py $dst --root $R @ra; $rc = $LASTEXITCODE; $cj = Join-Path $V2 'VRN2_CloseoutUI_latest.json'; if (-not (Test-Path -LiteralPath $cj) -or (Get-Item -LiteralPath $cj).LastWriteTime -lt $T0) { Write-Host "[YELLOW] ⑦ 這輪沒有寫出收尾頁($($cj))· 看上面 RoundAll 的最後幾行" -ForegroundColor Yellow } else { $c = Get-Content -LiteralPath $cj -Raw -Encoding utf8 | ConvertFrom-Json; $col = @{ OPEN = 'Red'; BLOCKED = 'Yellow'; REVIEW = 'Yellow'; DATA_GAP = 'Cyan'; PASS = 'Green' }[$c.state] ?? 'White'; Write-Host ''; Write-Host "===== 收尾 · $($c.state) · $($c.state_label) · $($c.state_text)" -ForegroundColor $col; foreach ($o in 'VRN-2', 'VCGC', '人工', '資料源') { $its = @($c.items | Where-Object owner -EQ $o); if ($its) { Write-Host "  [$($o)] $($its.Count) 項" -ForegroundColor (@{ 'VRN-2' = 'Red'; 'VCGC' = 'Yellow'; '人工' = 'Yellow'; '資料源' = 'Cyan' }[$o]); foreach ($i in $its) { $d = "$($i.detail)"; Write-Host "    · $($i.step) · $($d.Substring(0, [Math]::Min(150, $d.Length)))" } } }; $nx = @{ OPEN = '下一步:把貼回包上傳給 AI(VRN-2 要修的項目 · 出新版號修)'; BLOCKED = '下一步:VRN-2 側已結案 · 剩下是 VCGC 的決定 / 安裝(上面 [VCGC] 那幾項 · 例:MOPS 經 VIA 網路工具被 DENY)→ 交 VCGC,VRN-2 不繞道'; REVIEW = '下一步:VRN-2 側已結案 · 打開收尾頁看「人工核對」那幾項的原 PDF'; DATA_GAP = '下一步:VRN-2 側已結案 · 剩外部來源本來沒有的(已附證據)'; PASS = '全綠 · 結案' }[$c.state]; Write-Host "  $($nx)" -ForegroundColor $col; Write-Host '  BLOCKED / REVIEW / DATA_GAP 都不是成功;VCGC 的 closeout_lamp 才是 VCGC 驗收(四系統對等 · 只讀互看)' -ForegroundColor DarkGray; Write-Host "  收尾頁 $(Join-Path $V2 'VRN2_CloseoutUI_latest.html')"; $pb = @($c.links | Where-Object { "$($_.label)" -like '貼回包*' } | Select-Object -First 1).path; if ($pb -and (Test-Path -LiteralPath $pb)) { Write-Host "  貼回包 $($pb)(上傳給 AI)" -ForegroundColor Green } }; Write-Host "[計] Handle-All 結束 · RoundAll 結束碼 $($rc) · $([int]((Get-Date) - $T0).TotalSeconds) 秒(視窗不會關)" }
```

一行版 9,009 字元(UTF-8 · 不含結尾換行)· 下面「可讀版」是同一段碼(語法樹逐詞相同,只差換行 / 分號)。

## 可讀版 · Handle-All(跟一行版同一段碼)

```powershell
& {
$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'
if ($PSVersionTable.PSVersion.Major -lt 7) { Write-Host '[RED] 這段要 PowerShell 7 以上(pwsh · 例 7.6.9)' -ForegroundColor Red; return }
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch { }
$T0 = Get-Date
$R = $env:VRN2_ROOT ?? 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
$P = 'VeritasIntelligenceAnalytics/docs/handoff/ai/vrn2_release_v0154'
$F = 'VRN2_RoundAll_v0110.py'
$H = 'cc1d4b5d7a04783faa6363baf2b9c35cb6f298e32432b32104e0f9b682c49484'
$DL = Join-Path ($env:USERPROFILE ?? $HOME) 'Downloads'
$V2 = Join-Path $R 'VIA_Reports' 'vrn2'
$Mode = "$($env:VRN2_MODE ?? 'auto')".Trim().ToLowerInvariant()
if ($Mode -notin 'auto', 'full', 'repair', 'verify', 'report') { Write-Host "[RED] VRN2_MODE = $($Mode) 不認得(auto / full / repair / verify / report)" -ForegroundColor Red; return }
Write-Host "[VRN-2] Handle-All v0102 · PowerShell $($PSVersionTable.PSVersion) · 模式 $($Mode) · VIA $($R)" -ForegroundColor Yellow
$git = (Get-Command git -ErrorAction SilentlyContinue | Select-Object -First 1).Source
if (-not $git) { Write-Host '[RED] ① 找不到 git(裝 Git for Windows 後重開 PowerShell 7)' -ForegroundColor Red; return }
$top = "$(git -C $R rev-parse --show-toplevel 2>$null)".Trim()
if (-not $top) { Write-Host "[RED] ① $($R) 不是 git 倉(先設 `$env:VRN2_ROOT = '<VIA 根>')" -ForegroundColor Red; return }
$py = $env:VRN2_PY ?? (Get-Command python, py -ErrorAction SilentlyContinue | Where-Object Source -NotMatch 'WindowsApps' | Select-Object -First 1).Source
if (-not $py) { Write-Host '[RED] ① 找不到 python(不要用 WindowsApps 的假 python · 或先設 $env:VRN2_PY)' -ForegroundColor Red; return }
Write-Host "[GREEN] ① 工具 · git 倉 $($top) · $("$(& $py --version 2>&1)".Trim())($($py))" -ForegroundColor Green
if ($IsWindows) {
$busy = @(Get-CimInstance Win32_Process -Filter "Name like 'python%'" -ErrorAction SilentlyContinue | Where-Object CommandLine -Match 'ActivateVRN-2|VRN2_RoundAll')
if ($busy) {
Write-Host "[YELLOW] ② 已經有 $($busy.Count) 個 VRN-2 在跑(PID $($busy.ProcessId -join ', '))· 兩輪重疊會互搶鎖、變慢" -ForegroundColor Yellow
if (($env:VRN2_YES ?? (Read-Host '    等它跑完再貼比較好;還是要繼續嗎?(y/N)')) -notmatch '^[yY]') { Write-Host '[計] 沒有繼續(視窗不會關)'; return }
} else { Write-Host '[GREEN] ② 沒有別的 VRN-2 在跑' -ForegroundColor Green }
}
$bad = @(Get-ChildItem -LiteralPath $DL -Directory -Filter 'VRN2_Closeout_v0*' -ErrorAction SilentlyContinue | Where-Object { $ok = $true; try { foreach ($x in @(Get-ChildItem -LiteralPath $_.FullName -File -ErrorAction Stop)) { [IO.File]::OpenRead($x.FullName).Dispose() } } catch { $ok = $false }; -not $ok })
if ($bad) {
Write-Host "[YELLOW] ③ $($bad.Count) 個舊套件夾目前的身分讀不到(以前用系統管理員身分跑過 · 權限只剩 Administrators):" -ForegroundColor Yellow
$bad | ForEach-Object { Write-Host "    $($_.FullName)" }
Write-Host '    不擋:RoundAll 會改用讀得到的夾 · 套件 v0154 裝在新夾 VRN2_Closeout_v0154' -ForegroundColor DarkGray
if ($IsWindows -and (($env:VRN2_FIX_ACL ?? (Read-Host '    要用系統管理員身分把它們的權限還原成跟 Downloads 一樣嗎?會跳 UAC(y/N)')) -match '^[yY]')) {
$cmd = (@($bad | ForEach-Object { "icacls '" + ($_.FullName -replace "'", "''") + "' /reset /T /C /Q" }) -join '; ')
try { Start-Process -FilePath (Get-Process -Id $PID).Path -Verb RunAs -Wait -ArgumentList ('-NoProfile -EncodedCommand ' + [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($cmd))) -ErrorAction Stop; foreach ($d in $bad) { $ok = $true; try { foreach ($x in @(Get-ChildItem -LiteralPath $d.FullName -File -ErrorAction Stop)) { [IO.File]::OpenRead($x.FullName).Dispose() } } catch { $ok = $false }; Write-Host "    [$(if ($ok) { 'GREEN' } else { 'YELLOW' })] $($d.FullName) $(if ($ok) { '讀得到了' } else { '還是讀不到(不擋)' })" -ForegroundColor ($ok ? 'Green' : 'Yellow') } } catch { Write-Host "[YELLOW] ③ 沒有以系統管理員身分執行($($_.Exception.Message))· 不擋" -ForegroundColor Yellow }
}
} else { Write-Host '[GREEN] ③ Downloads 的 VRN-2 套件夾都讀得到' -ForegroundColor Green }
$rcp = Get-ChildItem -LiteralPath $V2 -File -Filter 'VRN2_Closeout_v0*.json' -ErrorAction SilentlyContinue | Where-Object Name -Match '^VRN2_Closeout_v\d{4}\.json$' | Sort-Object Name | Select-Object -Last 1
$last = ($rcp -and $rcp.Name -match '_v(\d{4})\.json$') ? [int]$Matches[1] : 0
$haveOut = (Test-Path -LiteralPath (Join-Path $V2 'output' 'VRN2_FinancialData_latest.json')) -and (Test-Path -LiteralPath (Join-Path $V2 'scope_in'))
if ($Mode -eq 'auto') { $Mode = ($last -ge 153 -and $haveOut) ? 'repair' : 'full'; Write-Host "[計] ④ 自動選模式 $($Mode) · 上一輪收據 $($rcp.Name ?? '沒有') · 上一輪輸出冊 $($haveOut ? '有' : '沒有')$(($Mode -eq 'full' -and $last -gt 0 -and $haveOut) ? '(上一輪輸出冊是啟動器 v0153 以前做的 · 管理器 v0257 要重做輸出冊)' : '')$(($Mode -eq 'repair') ? '(輸出冊是啟動器 v0153 以後做的 · 這版只改 ⑥f 共識 → 不整輪)' : '')(整輪:先貼 `$env:VRN2_MODE = 'full')" -ForegroundColor DarkGray }
if ($Mode -ne 'full' -and -not $haveOut) { Write-Host "[YELLOW] ④ 模式 $($Mode) 要上一輪的輸出冊 · 這裡沒有 → 改跑整輪" -ForegroundColor Yellow; $Mode = 'full' }
$ra = @(switch ($Mode) { 'repair' { '--only'; 'package,fix,report,closeout,pasteback' } 'verify' { '--only'; 'package,verify,report,closeout,pasteback' } 'report' { '--only'; 'report,closeout,pasteback' } })
$ra += @(($env:VRN2_ROUNDALL_ARGS ?? '') -split '\s+' | Where-Object { $_ })
$what = @{ full = '整輪(取套件 v0154 → 診斷 → 全部自測 → 跑啟動器 v0154(管理器 v0257 · ⑥f ConsensusJoin v0103)→ 自動修 → 除錯報告 → 收尾頁 → 貼回包 · 桌機約 40 分鐘)'; repair = '取套件 v0154 → ⑤ 自動修(⑥f 共識閘只因 404 / 一時抓不到 → 用 ConsensusJoin v0103 重跑 · 沿用今天抓到的 · 重組 Combined · 增量庫 · Workbench)→ 除錯報告 → 收尾頁 → 貼回包(幾分鐘)'; verify = '只重跑 ⑪ 獨立驗證(套件 v0154 的 IndependentVerifier v0114 · 用上一輪的輸出冊)→ 除錯報告 → 收尾頁 → 貼回包(約 10 分鐘)'; report = '只重做除錯報告 → 收尾頁 → 貼回包(用上一輪的結果 · 幾秒)' }[$Mode]
Write-Host "[計] ④ 模式 $($Mode):$($what)" -ForegroundColor Cyan
$t = Join-Path ([IO.Path]::GetTempPath()) "vrn2_handleall_$(Get-Date -Format yyyyMMdd_HHmmss)"
New-Item -ItemType Directory -Force -Path $t | Out-Null
$z = Join-Path $t 'roundall.zip'
$src = $null
foreach ($b in 'claude/optimistic-goodall-yhalc5', 'main') { foreach ($w in 0, 2, 4, 8, 16) { if ($w) { Start-Sleep -Seconds $w }; git -C $top fetch -q origin $b 2>&1 | Out-Null; if ($LASTEXITCODE -eq 0) { break } }; git -C $top archive --format=zip -o $z "origin/$($b):$($P)" $F 2>&1 | Out-Null; if ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $z)) { $src = $b; break } }
if (-not $src) { Write-Host "[RED] ⑤ 讀不到 GitHub 分支或 main 的 $($F)(網路 / git)" -ForegroundColor Red; return }
Expand-Archive -LiteralPath $z -DestinationPath $t -Force
$code = [IO.File]::ReadAllText((Join-Path $t $F), [Text.Encoding]::UTF8) -replace "`r`n", "`n"
$bytes = [Text.UTF8Encoding]::new($false).GetBytes($code)
$sha = ([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash($bytes)) -replace '-', '').ToLowerInvariant()
if ($sha -ne $H) { Write-Host "[RED] ⑤ $($F) SHA-256 不對($($sha))· 不執行" -ForegroundColor Red; return }
New-Item -ItemType Directory -Force -Path $DL | Out-Null
$dst = Join-Path $DL $F
[IO.File]::WriteAllBytes($dst, $bytes)
Write-Host "[GREEN] ⑤ $($F) SHA-256 $($H.Substring(0, 12)) 相符(GitHub $($src))→ $($dst)" -ForegroundColor Green
Write-Host "[計] ⑥ 執行 $($py) $($F) --root $($R) $($ra -join ' ')" -ForegroundColor DarkGray
& $py $dst --root $R @ra
$rc = $LASTEXITCODE
$cj = Join-Path $V2 'VRN2_CloseoutUI_latest.json'
if (-not (Test-Path -LiteralPath $cj) -or (Get-Item -LiteralPath $cj).LastWriteTime -lt $T0) { Write-Host "[YELLOW] ⑦ 這輪沒有寫出收尾頁($($cj))· 看上面 RoundAll 的最後幾行" -ForegroundColor Yellow } else {
$c = Get-Content -LiteralPath $cj -Raw -Encoding utf8 | ConvertFrom-Json
$col = @{ OPEN = 'Red'; BLOCKED = 'Yellow'; REVIEW = 'Yellow'; DATA_GAP = 'Cyan'; PASS = 'Green' }[$c.state] ?? 'White'
Write-Host ''
Write-Host "===== 收尾 · $($c.state) · $($c.state_label) · $($c.state_text)" -ForegroundColor $col
foreach ($o in 'VRN-2', 'VCGC', '人工', '資料源') { $its = @($c.items | Where-Object owner -EQ $o); if ($its) { Write-Host "  [$($o)] $($its.Count) 項" -ForegroundColor (@{ 'VRN-2' = 'Red'; 'VCGC' = 'Yellow'; '人工' = 'Yellow'; '資料源' = 'Cyan' }[$o]); foreach ($i in $its) { $d = "$($i.detail)"; Write-Host "    · $($i.step) · $($d.Substring(0, [Math]::Min(150, $d.Length)))" } } }
$nx = @{ OPEN = '下一步:把貼回包上傳給 AI(VRN-2 要修的項目 · 出新版號修)'; BLOCKED = '下一步:VRN-2 側已結案 · 剩下是 VCGC 的決定 / 安裝(上面 [VCGC] 那幾項 · 例:MOPS 經 VIA 網路工具被 DENY)→ 交 VCGC,VRN-2 不繞道'; REVIEW = '下一步:VRN-2 側已結案 · 打開收尾頁看「人工核對」那幾項的原 PDF'; DATA_GAP = '下一步:VRN-2 側已結案 · 剩外部來源本來沒有的(已附證據)'; PASS = '全綠 · 結案' }[$c.state]
Write-Host "  $($nx)" -ForegroundColor $col
Write-Host '  BLOCKED / REVIEW / DATA_GAP 都不是成功;VCGC 的 closeout_lamp 才是 VCGC 驗收(四系統對等 · 只讀互看)' -ForegroundColor DarkGray
Write-Host "  收尾頁 $(Join-Path $V2 'VRN2_CloseoutUI_latest.html')"
$pb = @($c.links | Where-Object { "$($_.label)" -like '貼回包*' } | Select-Object -First 1).path
if ($pb -and (Test-Path -LiteralPath $pb)) { Write-Host "  貼回包 $($pb)(上傳給 AI)" -ForegroundColor Green }
}
Write-Host "[計] Handle-All 結束 · RoundAll 結束碼 $($rc) · $([int]((Get-Date) - $T0).TotalSeconds) 秒(視窗不會關)"
}
```

## 可讀版 · 短開機行(跟最上面那行同一段碼)

```powershell
& {
$R = $env:VRN2_ROOT ?? 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
$P = 'VeritasIntelligenceAnalytics/docs/handoff/ai/vrn2_release_v0154'
$F = 'VRN2_HandleAll_v0102.md'
$H = 'a3d4dc8b9f8bf3d47eff359ad7c56548f5779a80968db6e3ee6178746c37f34b'
$top = "$(git -C $R rev-parse --show-toplevel 2>$null)".Trim()
if (-not $top) { Write-Host "[RED] boot: $R is not a git repo (set `$env:VRN2_ROOT)" -ForegroundColor Red; return }
$t = Join-Path ([IO.Path]::GetTempPath()) "vrn2_boot_$(Get-Date -Format yyyyMMddHHmmss)"
$z = Join-Path $t 'ha.zip'
New-Item -ItemType Directory -Force -Path $t | Out-Null
$ok = $false
foreach ($b in 'claude/optimistic-goodall-yhalc5', 'main') {
foreach ($w in 0, 3, 9) { Start-Sleep -Seconds $w; git -C $top fetch -q origin $b 2>&1 | Out-Null; if ($LASTEXITCODE -eq 0) { break } }
git -C $top archive --format=zip -o $z "origin/$($b):$($P)" $F 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) { $ok = $true; break }
}
if (-not $ok) { Write-Host "[RED] boot: cannot read $F from GitHub" -ForegroundColor Red; return }
Expand-Archive -LiteralPath $z -DestinationPath $t -Force
$md = [IO.File]::ReadAllText((Join-Path $t $F), [Text.Encoding]::UTF8) -replace "`r`n", "`n"
$c = [regex]::Match($md, '(?s)<!-- handle-all line -->\n```powershell\n(.*?)\n```').Groups[1].Value
$s = ([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash([Text.UTF8Encoding]::new($false).GetBytes($c))) -replace '-', '').ToLowerInvariant()
if ($s -ne $H) { Write-Host "[RED] boot: SHA-256 $s is not $H - not run" -ForegroundColor Red; return }
Write-Host "[GREEN] boot: Handle-All v0102 SHA-256 OK ($b)" -ForegroundColor Green
Invoke-Expression $c
}
```
