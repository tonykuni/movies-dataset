# VRN-2 · PowerShell 7 一行處理全部 · VRN2_HandleAll_v0104(2026-10-31 · 套件 v0156 · RoundAll v0112)

v0104 = v0103 + 套件 **v0156**:共識引擎改成**經 VIA 網路工具 + 加速器出網**(操作員 2026-10-31:「新版有版本號 · 加速器跟網路工具最新版都有版本號 ·
直接透過 VCGC 的環境工具管理引擎下載所有不足工具及環境並確認無衝突 · 改成經網路工具和加速器出網再抓」)。

| 項目 | 版本 |
|---|---|
| 共識引擎 | `VIA_CNYES_FactSet_YFinance_Consensus_Fusion_Engine_v0122`(v0121 + 出網經網路工具)· 前版 v0120(直連)留在 runtime 當前版 |
| 網路工具 | `supportive modules\network\SUP_MDL740_NetUnified` 最高版號(倉裡 v0119)· 核心 = 鎖冊 `VeritasAegisNexus_v1652` |
| 加速器 | 引擎的加速器橋載入最高版號 `VeritasCeleritas`(鎖冊 v1141)· 網路工具文字車道用 `VIA_SuperAccel` |
| 鉅亨 FactSet 頁 | 網路工具 `http_bytes` 車道(重試 · 404 不重試) |
| YFinance | 網路工具 `yahoo_quote_summary_raw` 車道(不再用 yfinance 套件 · 要 `requests`) |
| ⑥f 合併 | `VRN2_ConsensusJoin_v0104`(v0103 薄尾) |
| 一支 Python | `VRN2_RoundAll_v0112.py`(SHA-256 `5f032bc73f2f`)· 套件 `VRN2_Closeout_v0156.zip`(SHA-256 `182bc1486bb4`) |

## PowerShell 7 貼這一行(443 字元 · 4 行內 · 不會讓輸入列當掉)

```powershell
$r="$HOME\OneDrive\Documents\movies-dataset";git -C $r fetch -q origin claude/optimistic-goodall-yhalc5;$c=(git -C $r show "FETCH_HEAD:VeritasIntelligenceAnalytics/docs/handoff/ai/vrn2_release_v0156/VRN2_HandleAll_v0104_boot.txt")-join"`n";if((Get-FileHash -InputStream ([IO.MemoryStream]::new([byte[]][char[]]$c))).Hash-eq'5d39098af2673b889769bedb279bf14ee3a3b1478ee23c9b25b4f7272421339e'){iex $c}else{'[RED] boot SHA-256 mismatch - not run'}
```

`git fetch` 分支 → `git show` 取 `VRN2_HandleAll_v0104_boot.txt`(開機行 · ASCII)→ 核對 SHA-256 `5d39098af267` 才執行 →
開機行取本檔、核對 Handle-All 那一行的 SHA-256 `986cdad74e65` 才執行 → auto(上一輪收據 v0153 以後 + 輸出冊在 → repair)。
第一行應是 `[GREEN] boot: Handle-All v0104 SHA-256 OK`。

## 同意閘(操作員決定 · VRN-2 只讀 · 不代設)

網路工具有兩道同意閘:`VIA_NET_CONSENT = YES` **而且** `VIA_SCRAPE_CONSENT = YES`(或 `I_ACCEPT_RESPONSIBLE_SCRAPING`),跟 VCGC 的 `CGC_MDL224_ScrapeGate` 同一套判斷。
Handle-All 的 **③b** 只讀印出現在的狀態:

- **開**(綠):repair 的 ⑤ 會把 ⑥f 改經網路工具重抓(套件的 ConsensusJoin v0104 + 引擎 v0122 只增不覆寫地補放 → 今天的 checkpoint 封存 → 全部經網路工具抓)→ 重組 Combined。
- **未開**(黃):repair **不重抓**(現有共識不動),除錯報告 / 收尾頁列一項「⑥f 共識還沒經 VIA 網路工具 · 同意閘未開」= **人工**;整輪(full)的 ⑥f 會被網路工具 DENY(不換道直連)。
  要抓:**你**在同一個視窗先貼下面這行,再貼最上面那一行(AI / VRN-2 不會替你設):

```powershell
$env:VIA_NET_CONSENT = 'YES'; $env:VIA_SCRAPE_CONSENT = 'YES'
```

用完可 `Remove-Item Env:VIA_NET_CONSENT, Env:VIA_SCRAPE_CONSENT`。合規判定:鉅亨 / Yahoo 在網路工具的合規表裡是「訊號」(放行 · 記錄);MOPS 照舊 DENY(VCGC 的決定)。

## VCGC 環境工具(裝缺的 · 查衝突)

容器裡用 VCGC 的環境工具跑過:`CGC_MDL049_EnvPlan_v0103 --offline`(pip 衝突 0)· `CGC_MDL056_InstallGate_v0101 --check-only`(衝突 0 · 網路工具 / 加速器輔助模組 OK)·
`InstallGate duckdb`(裝進沙盒 venv · 前後衝突 0)。新引擎在擷取 Python 要的是 **`requests`**(Yahoo 車道);桌機缺什麼,⑥f 會黃、收尾頁列 **VCGC**,用 VCGC 的 `via-install <套件>` 裝(VRN-2 不 pip)。

## 這次桌機貼下去會怎樣

上一輪收據 `VRN2_Closeout_v0154.json`、輸出冊在 → auto 選 **repair**:

- 閘**開**:⑤ 排「⑥f 改經 VIA 網路工具重抓」→ 印 `def Net tool : SUP_MDL740_NetUnified_v0119 …` → 抓 43 檔 → 404 的照舊不納入閘 → 重組 Combined → 收尾頁。
  預期跟 v0103 那輪一樣 **BLOCKED · VRN-2 0 · VCGC 1(MOPS DENY)· 人工 2 · 資料源 2**,除錯報告多一列綠的「⑥f 經 VIA 網路工具」。
- 閘**未開**:不重抓 → 預期 **BLOCKED · VRN-2 0 · VCGC 1 · 人工 3(多「同意閘未開」那項)· 資料源 2**。
- 擷取 Python 缺 `requests` → ⑥f 黃 · VCGC 多一項(用 via-install 裝)。

容器做不到的:打開你的同意閘、連到鉅亨 / Yahoo —— 真的抓要在桌機跑(容器裡用本機假伺服器 + 閘替身驗過網路工具車道,真網路工具閘關 = DENY · 0 個請求)。

## 開機行(同一段 · 已經在 PowerShell 7 也可直接貼 · 1,719 字元)

```powershell
& { $R = $env:VRN2_ROOT ?? 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'; $P = 'VeritasIntelligenceAnalytics/docs/handoff/ai/vrn2_release_v0156'; $F = 'VRN2_HandleAll_v0104.md'; $H = '986cdad74e65ef3e106739cfd9ebbeeb7ad287919881585dfb11e11e35597148'; $top = "$(git -C $R rev-parse --show-toplevel 2>$null)".Trim(); if (-not $top) { Write-Host "[RED] boot: $R is not a git repo (set `$env:VRN2_ROOT)" -ForegroundColor Red; return }; $t = Join-Path ([IO.Path]::GetTempPath()) "vrn2_boot_$(Get-Date -Format yyyyMMddHHmmss)"; $z = Join-Path $t 'ha.zip'; New-Item -ItemType Directory -Force -Path $t | Out-Null; $ok = $false; foreach ($b in 'claude/optimistic-goodall-yhalc5', 'main') { foreach ($w in 0, 3, 9) { Start-Sleep -Seconds $w; git -C $top fetch -q origin $b 2>&1 | Out-Null; if ($LASTEXITCODE -eq 0) { break } }; git -C $top archive --format=zip -o $z "origin/$($b):$($P)" $F 2>&1 | Out-Null; if ($LASTEXITCODE -eq 0) { $ok = $true; break } }; if (-not $ok) { Write-Host "[RED] boot: cannot read $F from GitHub" -ForegroundColor Red; return }; Expand-Archive -LiteralPath $z -DestinationPath $t -Force; $md = [IO.File]::ReadAllText((Join-Path $t $F), [Text.Encoding]::UTF8) -replace "`r`n", "`n"; $c = [regex]::Match($md, '(?s)<!-- handle-all line -->\n```powershell\n(.*?)\n```').Groups[1].Value; $s = ([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash([Text.UTF8Encoding]::new($false).GetBytes($c))) -replace '-', '').ToLowerInvariant(); if ($s -ne $H) { Write-Host "[RED] boot: SHA-256 $s is not $H - not run" -ForegroundColor Red; return }; Write-Host "[GREEN] boot: Handle-All v0104 SHA-256 OK ($b)" -ForegroundColor Green; Invoke-Expression $c }
```

## cmd 視窗(內容 = 開機行 · 不經 PowerShell 輸入列)

```bat
pwsh -NoProfile -ExecutionPolicy Bypass -EncodedCommand JgAgAHsAIAAkAFIAIAA9ACAAJABlAG4AdgA6AFYAUgBOADIAXwBSAE8ATwBUACAAPwA/ACAAJwBDADoAXABVAHMAZQByAHMAXAB0AG8AbgB5AGsAXABPAG4AZQBEAHIAaQB2AGUAXABEAG8AYwB1AG0AZQBuAHQAcwBcAG0AbwB2AGkAZQBzAC0AZABhAHQAYQBzAGUAdABcAFYAZQByAGkAdABhAHMASQBuAHQAZQBsAGwAaQBnAGUAbgBjAGUAQQBuAGEAbAB5AHQAaQBjAHMAJwA7ACAAJABQACAAPQAgACcAVgBlAHIAaQB0AGEAcwBJAG4AdABlAGwAbABpAGcAZQBuAGMAZQBBAG4AYQBsAHkAdABpAGMAcwAvAGQAbwBjAHMALwBoAGEAbgBkAG8AZgBmAC8AYQBpAC8AdgByAG4AMgBfAHIAZQBsAGUAYQBzAGUAXwB2ADAAMQA1ADYAJwA7ACAAJABGACAAPQAgACcAVgBSAE4AMgBfAEgAYQBuAGQAbABlAEEAbABsAF8AdgAwADEAMAA0AC4AbQBkACcAOwAgACQASAAgAD0AIAAnADkAOAA2AGMAZABhAGQANwA0AGUANgA1AGUAZgAzAGUAMQAwADYANwAzADkAYwBmAGQAOQBlAGIAYgBlAGUAYgA3AGEAZAAyADgANwA5ADEAOQA4ADgAMQA1ADgANQBkAGYAYgAxADEAZQAxADEAZQAzADUANQA5ADcAMQA0ADgAJwA7ACAAJAB0AG8AcAAgAD0AIAAiACQAKABnAGkAdAAgAC0AQwAgACQAUgAgAHIAZQB2AC0AcABhAHIAcwBlACAALQAtAHMAaABvAHcALQB0AG8AcABsAGUAdgBlAGwAIAAyAD4AJABuAHUAbABsACkAIgAuAFQAcgBpAG0AKAApADsAIABpAGYAIAAoAC0AbgBvAHQAIAAkAHQAbwBwACkAIAB7ACAAVwByAGkAdABlAC0ASABvAHMAdAAgACIAWwBSAEUARABdACAAYgBvAG8AdAA6ACAAJABSACAAaQBzACAAbgBvAHQAIABhACAAZwBpAHQAIAByAGUAcABvACAAKABzAGUAdAAgAGAAJABlAG4AdgA6AFYAUgBOADIAXwBSAE8ATwBUACkAIgAgAC0ARgBvAHIAZQBnAHIAbwB1AG4AZABDAG8AbABvAHIAIABSAGUAZAA7ACAAcgBlAHQAdQByAG4AIAB9ADsAIAAkAHQAIAA9ACAASgBvAGkAbgAtAFAAYQB0AGgAIAAoAFsASQBPAC4AUABhAHQAaABdADoAOgBHAGUAdABUAGUAbQBwAFAAYQB0AGgAKAApACkAIAAiAHYAcgBuADIAXwBiAG8AbwB0AF8AJAAoAEcAZQB0AC0ARABhAHQAZQAgAC0ARgBvAHIAbQBhAHQAIAB5AHkAeQB5AE0ATQBkAGQASABIAG0AbQBzAHMAKQAiADsAIAAkAHoAIAA9ACAASgBvAGkAbgAtAFAAYQB0AGgAIAAkAHQAIAAnAGgAYQAuAHoAaQBwACcAOwAgAE4AZQB3AC0ASQB0AGUAbQAgAC0ASQB0AGUAbQBUAHkAcABlACAARABpAHIAZQBjAHQAbwByAHkAIAAtAEYAbwByAGMAZQAgAC0AUABhAHQAaAAgACQAdAAgAHwAIABPAHUAdAAtAE4AdQBsAGwAOwAgACQAbwBrACAAPQAgACQAZgBhAGwAcwBlADsAIABmAG8AcgBlAGEAYwBoACAAKAAkAGIAIABpAG4AIAAnAGMAbABhAHUAZABlAC8AbwBwAHQAaQBtAGkAcwB0AGkAYwAtAGcAbwBvAGQAYQBsAGwALQB5AGgAYQBsAGMANQAnACwAIAAnAG0AYQBpAG4AJwApACAAewAgAGYAbwByAGUAYQBjAGgAIAAoACQAdwAgAGkAbgAgADAALAAgADMALAAgADkAKQAgAHsAIABTAHQAYQByAHQALQBTAGwAZQBlAHAAIAAtAFMAZQBjAG8AbgBkAHMAIAAkAHcAOwAgAGcAaQB0ACAALQBDACAAJAB0AG8AcAAgAGYAZQB0AGMAaAAgAC0AcQAgAG8AcgBpAGcAaQBuACAAJABiACAAMgA+ACYAMQAgAHwAIABPAHUAdAAtAE4AdQBsAGwAOwAgAGkAZgAgACgAJABMAEEAUwBUAEUAWABJAFQAQwBPAEQARQAgAC0AZQBxACAAMAApACAAewAgAGIAcgBlAGEAawAgAH0AIAB9ADsAIABnAGkAdAAgAC0AQwAgACQAdABvAHAAIABhAHIAYwBoAGkAdgBlACAALQAtAGYAbwByAG0AYQB0AD0AegBpAHAAIAAtAG8AIAAkAHoAIAAiAG8AcgBpAGcAaQBuAC8AJAAoACQAYgApADoAJAAoACQAUAApACIAIAAkAEYAIAAyAD4AJgAxACAAfAAgAE8AdQB0AC0ATgB1AGwAbAA7ACAAaQBmACAAKAAkAEwAQQBTAFQARQBYAEkAVABDAE8ARABFACAALQBlAHEAIAAwACkAIAB7ACAAJABvAGsAIAA9ACAAJAB0AHIAdQBlADsAIABiAHIAZQBhAGsAIAB9ACAAfQA7ACAAaQBmACAAKAAtAG4AbwB0ACAAJABvAGsAKQAgAHsAIABXAHIAaQB0AGUALQBIAG8AcwB0ACAAIgBbAFIARQBEAF0AIABiAG8AbwB0ADoAIABjAGEAbgBuAG8AdAAgAHIAZQBhAGQAIAAkAEYAIABmAHIAbwBtACAARwBpAHQASAB1AGIAIgAgAC0ARgBvAHIAZQBnAHIAbwB1AG4AZABDAG8AbABvAHIAIABSAGUAZAA7ACAAcgBlAHQAdQByAG4AIAB9ADsAIABFAHgAcABhAG4AZAAtAEEAcgBjAGgAaQB2AGUAIAAtAEwAaQB0AGUAcgBhAGwAUABhAHQAaAAgACQAegAgAC0ARABlAHMAdABpAG4AYQB0AGkAbwBuAFAAYQB0AGgAIAAkAHQAIAAtAEYAbwByAGMAZQA7ACAAJABtAGQAIAA9ACAAWwBJAE8ALgBGAGkAbABlAF0AOgA6AFIAZQBhAGQAQQBsAGwAVABlAHgAdAAoACgASgBvAGkAbgAtAFAAYQB0AGgAIAAkAHQAIAAkAEYAKQAsACAAWwBUAGUAeAB0AC4ARQBuAGMAbwBkAGkAbgBnAF0AOgA6AFUAVABGADgAKQAgAC0AcgBlAHAAbABhAGMAZQAgACIAYAByAGAAbgAiACwAIAAiAGAAbgAiADsAIAAkAGMAIAA9ACAAWwByAGUAZwBlAHgAXQA6ADoATQBhAHQAYwBoACgAJABtAGQALAAgACcAKAA/AHMAKQA8ACEALQAtACAAaABhAG4AZABsAGUALQBhAGwAbAAgAGwAaQBuAGUAIAAtAC0APgBcAG4AYABgAGAAcABvAHcAZQByAHMAaABlAGwAbABcAG4AKAAuACoAPwApAFwAbgBgAGAAYAAnACkALgBHAHIAbwB1AHAAcwBbADEAXQAuAFYAYQBsAHUAZQA7ACAAJABzACAAPQAgACgAWwBCAGkAdABDAG8AbgB2AGUAcgB0AGUAcgBdADoAOgBUAG8AUwB0AHIAaQBuAGcAKABbAFMAZQBjAHUAcgBpAHQAeQAuAEMAcgB5AHAAdABvAGcAcgBhAHAAaAB5AC4AUwBIAEEAMgA1ADYAXQA6ADoAQwByAGUAYQB0AGUAKAApAC4AQwBvAG0AcAB1AHQAZQBIAGEAcwBoACgAWwBUAGUAeAB0AC4AVQBUAEYAOABFAG4AYwBvAGQAaQBuAGcAXQA6ADoAbgBlAHcAKAAkAGYAYQBsAHMAZQApAC4ARwBlAHQAQgB5AHQAZQBzACgAJABjACkAKQApACAALQByAGUAcABsAGEAYwBlACAAJwAtACcALAAgACcAJwApAC4AVABvAEwAbwB3AGUAcgBJAG4AdgBhAHIAaQBhAG4AdAAoACkAOwAgAGkAZgAgACgAJABzACAALQBuAGUAIAAkAEgAKQAgAHsAIABXAHIAaQB0AGUALQBIAG8AcwB0ACAAIgBbAFIARQBEAF0AIABiAG8AbwB0ADoAIABTAEgAQQAtADIANQA2ACAAJABzACAAaQBzACAAbgBvAHQAIAAkAEgAIAAtACAAbgBvAHQAIAByAHUAbgAiACAALQBGAG8AcgBlAGcAcgBvAHUAbgBkAEMAbwBsAG8AcgAgAFIAZQBkADsAIAByAGUAdAB1AHIAbgAgAH0AOwAgAFcAcgBpAHQAZQAtAEgAbwBzAHQAIAAiAFsARwBSAEUARQBOAF0AIABiAG8AbwB0ADoAIABIAGEAbgBkAGwAZQAtAEEAbABsACAAdgAwADEAMAA0ACAAUwBIAEEALQAyADUANgAgAE8ASwAgACgAJABiACkAIgAgAC0ARgBvAHIAZQBnAHIAbwB1AG4AZABDAG8AbABvAHIAIABHAHIAZQBlAG4AOwAgAEkAbgB2AG8AawBlAC0ARQB4AHAAcgBlAHMAcwBpAG8AbgAgACQAYwAgAH0A
```

## Handle-All 那一行(開機行從 GitHub 取這段、核對 SHA-256 才執行 · 不用貼它)

<!-- handle-all line -->
```powershell
& { $ErrorActionPreference = 'Continue'; $ProgressPreference = 'SilentlyContinue'; if ($PSVersionTable.PSVersion.Major -lt 7) { Write-Host '[RED] 這段要 PowerShell 7 以上(pwsh · 例 7.6.9)' -ForegroundColor Red; return }; try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch { }; $T0 = Get-Date; $R = $env:VRN2_ROOT ?? 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'; $P = 'VeritasIntelligenceAnalytics/docs/handoff/ai/vrn2_release_v0156'; $F = 'VRN2_RoundAll_v0112.py'; $H = '5f032bc73f2f8bc7608754107dcd4dcede05be4a349f38599a12d0e5bfe18fff'; $DL = Join-Path ($env:USERPROFILE ?? $HOME) 'Downloads'; $V2 = Join-Path $R 'VIA_Reports' 'vrn2'; $Mode = "$($env:VRN2_MODE ?? 'auto')".Trim().ToLowerInvariant(); if ($Mode -notin 'auto', 'full', 'repair', 'verify', 'report') { Write-Host "[RED] VRN2_MODE = $($Mode) 不認得(auto / full / repair / verify / report)" -ForegroundColor Red; return }; Write-Host "[VRN-2] Handle-All v0104 · PowerShell $($PSVersionTable.PSVersion) · 模式 $($Mode) · VIA $($R)" -ForegroundColor Yellow; $git = (Get-Command git -ErrorAction SilentlyContinue | Select-Object -First 1).Source; if (-not $git) { Write-Host '[RED] ① 找不到 git(裝 Git for Windows 後重開 PowerShell 7)' -ForegroundColor Red; return }; $top = "$(git -C $R rev-parse --show-toplevel 2>$null)".Trim(); if (-not $top) { Write-Host "[RED] ① $($R) 不是 git 倉(先設 `$env:VRN2_ROOT = '<VIA 根>')" -ForegroundColor Red; return }; $py = $env:VRN2_PY ?? (Get-Command python, py -ErrorAction SilentlyContinue | Where-Object Source -NotMatch 'WindowsApps' | Select-Object -First 1).Source; if (-not $py) { Write-Host '[RED] ① 找不到 python(不要用 WindowsApps 的假 python · 或先設 $env:VRN2_PY)' -ForegroundColor Red; return }; Write-Host "[GREEN] ① 工具 · git 倉 $($top) · $("$(& $py --version 2>&1)".Trim())($($py))" -ForegroundColor Green; if ($IsWindows) { $busy = @(Get-CimInstance Win32_Process -Filter "Name like 'python%'" -ErrorAction SilentlyContinue | Where-Object CommandLine -Match 'ActivateVRN-2|VRN2_RoundAll'); if ($busy) { Write-Host "[YELLOW] ② 已經有 $($busy.Count) 個 VRN-2 在跑(PID $($busy.ProcessId -join ', '))· 兩輪重疊會互搶鎖、變慢" -ForegroundColor Yellow; if (($env:VRN2_YES ?? (Read-Host '    等它跑完再貼比較好;還是要繼續嗎?(y/N)')) -notmatch '^[yY]') { Write-Host '[計] 沒有繼續(視窗不會關)'; return } } else { Write-Host '[GREEN] ② 沒有別的 VRN-2 在跑' -ForegroundColor Green } }; $bad = @(Get-ChildItem -LiteralPath $DL -Directory -Filter 'VRN2_Closeout_v0*' -ErrorAction SilentlyContinue | Where-Object { $ok = $true; try { foreach ($x in @(Get-ChildItem -LiteralPath $_.FullName -File -ErrorAction Stop)) { [IO.File]::OpenRead($x.FullName).Dispose() } } catch { $ok = $false }; -not $ok }); if ($bad) { Write-Host "[YELLOW] ③ $($bad.Count) 個舊套件夾目前的身分讀不到(以前用系統管理員身分跑過 · 權限只剩 Administrators):" -ForegroundColor Yellow; $bad | ForEach-Object { Write-Host "    $($_.FullName)" }; Write-Host '    不擋:RoundAll 會改用讀得到的夾 · 套件 v0156 裝在新夾 VRN2_Closeout_v0156' -ForegroundColor DarkGray; if ($IsWindows -and (($env:VRN2_FIX_ACL ?? (Read-Host '    要用系統管理員身分把它們的權限還原成跟 Downloads 一樣嗎?會跳 UAC(y/N)')) -match '^[yY]')) { $cmd = (@($bad | ForEach-Object { "icacls '" + ($_.FullName -replace "'", "''") + "' /reset /T /C /Q" }) -join '; '); try { Start-Process -FilePath (Get-Process -Id $PID).Path -Verb RunAs -Wait -ArgumentList ('-NoProfile -EncodedCommand ' + [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($cmd))) -ErrorAction Stop; foreach ($d in $bad) { $ok = $true; try { foreach ($x in @(Get-ChildItem -LiteralPath $d.FullName -File -ErrorAction Stop)) { [IO.File]::OpenRead($x.FullName).Dispose() } } catch { $ok = $false }; Write-Host "    [$(if ($ok) { 'GREEN' } else { 'YELLOW' })] $($d.FullName) $(if ($ok) { '讀得到了' } else { '還是讀不到(不擋)' })" -ForegroundColor ($ok ? 'Green' : 'Yellow') } } catch { Write-Host "[YELLOW] ③ 沒有以系統管理員身分執行($($_.Exception.Message))· 不擋" -ForegroundColor Yellow } } } else { Write-Host '[GREEN] ③ Downloads 的 VRN-2 套件夾都讀得到' -ForegroundColor Green }; $g1 = "$env:VIA_NET_CONSENT"; $g2 = "$env:VIA_SCRAPE_CONSENT"; $gate = ($g1 -ceq 'YES') -and ($g2 -cin 'YES', 'I_ACCEPT_RESPONSIBLE_SCRAPING'); if ($gate) { Write-Host "[GREEN] ③b VIA 網路工具同意閘 開(VIA_NET_CONSENT=$($g1) · VIA_SCRAPE_CONSENT=$($g2) · 操作員設的)· ⑥f 共識經 VIA 網路工具 + 加速器重抓(共識引擎 v0122)" -ForegroundColor Green } else { Write-Host "[YELLOW] ③b VIA 網路工具同意閘 未開(VIA_NET_CONSENT=$(($g1) ? $g1 : '(未設)') · VIA_SCRAPE_CONSENT=$(($g2) ? $g2 : '(未設)'))· repair 不重抓 ⑥f(現有共識不動)· 整輪的 ⑥f 會被 DENY · 收尾頁列「人工」" -ForegroundColor Yellow; Write-Host "    要經網路工具抓:在同一個視窗先貼 `$env:VIA_NET_CONSENT = 'YES'; `$env:VIA_SCRAPE_CONSENT = 'YES' 再貼那一行(操作員決定 · VRN-2 只讀 · 不代設)" -ForegroundColor DarkGray }; $rcp = Get-ChildItem -LiteralPath $V2 -File -Filter 'VRN2_Closeout_v0*.json' -ErrorAction SilentlyContinue | Where-Object Name -Match '^VRN2_Closeout_v\d{4}\.json$' | Sort-Object Name | Select-Object -Last 1; $last = ($rcp -and $rcp.Name -match '_v(\d{4})\.json$') ? [int]$Matches[1] : 0; $haveOut = (Test-Path -LiteralPath (Join-Path $V2 'output' 'VRN2_FinancialData_latest.json')) -and (Test-Path -LiteralPath (Join-Path $V2 'scope_in')); if ($Mode -eq 'auto') { $Mode = ($last -ge 153 -and $haveOut) ? 'repair' : 'full'; Write-Host "[計] ④ 自動選模式 $($Mode) · 上一輪收據 $($rcp.Name ?? '沒有') · 上一輪輸出冊 $($haveOut ? '有' : '沒有')$(($Mode -eq 'full' -and $last -gt 0 -and $haveOut) ? '(上一輪輸出冊是啟動器 v0153 以前做的 · 管理器 v0257 要重做輸出冊)' : '')$(($Mode -eq 'repair') ? '(輸出冊是啟動器 v0153 以後做的 · 這版只改 ⑥f 共識出網 → 不整輪)' : '')(整輪:先貼 `$env:VRN2_MODE = 'full')" -ForegroundColor DarkGray }; if ($Mode -ne 'full' -and -not $haveOut) { Write-Host "[YELLOW] ④ 模式 $($Mode) 要上一輪的輸出冊 · 這裡沒有 → 改跑整輪" -ForegroundColor Yellow; $Mode = 'full' }; $ra = @(switch ($Mode) { 'repair' { '--only'; 'package,fix,report,closeout,pasteback' } 'verify' { '--only'; 'package,verify,report,closeout,pasteback' } 'report' { '--only'; 'report,closeout,pasteback' } }); $ra += @(($env:VRN2_ROUNDALL_ARGS ?? '') -split '\s+' | Where-Object { $_ }); $what = @{ full = '整輪(取套件 v0156 → 診斷 → 全部自測 → 跑啟動器 v0156(管理器 v0257 · ⑥f ConsensusJoin v0104 · 共識引擎 v0122 經 VIA 網路工具 + 加速器)→ 自動修 → 除錯報告 → 收尾頁 → 貼回包 · 桌機約 40 分鐘)'; repair = '取套件 v0156 → ⑤ 自動修(同意閘開:⑥f 共識改經 VIA 網路工具重抓 · ConsensusJoin v0104 + 引擎 v0122 · 重組 Combined · 增量庫 · Workbench;閘關:現有共識不動)→ 除錯報告 → 收尾頁 → 貼回包(幾分鐘)'; verify = '只重跑 ⑪ 獨立驗證(套件 v0156 的 IndependentVerifier v0114 · 用上一輪的輸出冊)→ 除錯報告 → 收尾頁 → 貼回包(約 10 分鐘)'; report = '只重做除錯報告 → 收尾頁 → 貼回包(用上一輪的結果 · 幾秒)' }[$Mode]; Write-Host "[計] ④ 模式 $($Mode):$($what)" -ForegroundColor Cyan; $t = Join-Path ([IO.Path]::GetTempPath()) "vrn2_handleall_$(Get-Date -Format yyyyMMdd_HHmmss)"; New-Item -ItemType Directory -Force -Path $t | Out-Null; $z = Join-Path $t 'roundall.zip'; $src = $null; foreach ($b in 'claude/optimistic-goodall-yhalc5', 'main') { foreach ($w in 0, 2, 4, 8, 16) { if ($w) { Start-Sleep -Seconds $w }; git -C $top fetch -q origin $b 2>&1 | Out-Null; if ($LASTEXITCODE -eq 0) { break } }; git -C $top archive --format=zip -o $z "origin/$($b):$($P)" $F 2>&1 | Out-Null; if ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $z)) { $src = $b; break } }; if (-not $src) { Write-Host "[RED] ⑤ 讀不到 GitHub 分支或 main 的 $($F)(網路 / git)" -ForegroundColor Red; return }; Expand-Archive -LiteralPath $z -DestinationPath $t -Force; $code = [IO.File]::ReadAllText((Join-Path $t $F), [Text.Encoding]::UTF8) -replace "`r`n", "`n"; $bytes = [Text.UTF8Encoding]::new($false).GetBytes($code); $sha = ([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash($bytes)) -replace '-', '').ToLowerInvariant(); if ($sha -ne $H) { Write-Host "[RED] ⑤ $($F) SHA-256 不對($($sha))· 不執行" -ForegroundColor Red; return }; New-Item -ItemType Directory -Force -Path $DL | Out-Null; $dst = Join-Path $DL $F; [IO.File]::WriteAllBytes($dst, $bytes); Write-Host "[GREEN] ⑤ $($F) SHA-256 $($H.Substring(0, 12)) 相符(GitHub $($src))→ $($dst)" -ForegroundColor Green; Write-Host "[計] ⑥ 執行 $($py) $($F) --root $($R) $($ra -join ' ')" -ForegroundColor DarkGray; & $py $dst --root $R @ra; $rc = $LASTEXITCODE; $cj = Join-Path $V2 'VRN2_CloseoutUI_latest.json'; if (-not (Test-Path -LiteralPath $cj) -or (Get-Item -LiteralPath $cj).LastWriteTime -lt $T0) { Write-Host "[YELLOW] ⑦ 這輪沒有寫出收尾頁($($cj))· 看上面 RoundAll 的最後幾行" -ForegroundColor Yellow } else { $c = Get-Content -LiteralPath $cj -Raw -Encoding utf8 | ConvertFrom-Json; $col = @{ OPEN = 'Red'; BLOCKED = 'Yellow'; REVIEW = 'Yellow'; DATA_GAP = 'Cyan'; PASS = 'Green' }[$c.state] ?? 'White'; Write-Host ''; Write-Host "===== 收尾 · $($c.state) · $($c.state_label) · $($c.state_text)" -ForegroundColor $col; foreach ($o in 'VRN-2', 'VCGC', '人工', '資料源') { $its = @($c.items | Where-Object owner -EQ $o); if ($its) { Write-Host "  [$($o)] $($its.Count) 項" -ForegroundColor (@{ 'VRN-2' = 'Red'; 'VCGC' = 'Yellow'; '人工' = 'Yellow'; '資料源' = 'Cyan' }[$o]); foreach ($i in $its) { $d = "$($i.detail)"; Write-Host "    · $($i.step) · $($d.Substring(0, [Math]::Min(150, $d.Length)))" } } }; $nx = @{ OPEN = '下一步:把貼回包上傳給 AI(VRN-2 要修的項目 · 出新版號修)'; BLOCKED = '下一步:VRN-2 側已結案 · 剩下是 VCGC 的決定 / 安裝(上面 [VCGC] 那幾項 · 例:MOPS 經 VIA 網路工具被 DENY)→ 交 VCGC,VRN-2 不繞道'; REVIEW = '下一步:VRN-2 側已結案 · 打開收尾頁看「人工核對」那幾項的原 PDF'; DATA_GAP = '下一步:VRN-2 側已結案 · 剩外部來源本來沒有的(已附證據)'; PASS = '全綠 · 結案' }[$c.state]; Write-Host "  $($nx)" -ForegroundColor $col; Write-Host '  BLOCKED / REVIEW / DATA_GAP 都不是成功;VCGC 的 closeout_lamp 才是 VCGC 驗收(四系統對等 · 只讀互看)' -ForegroundColor DarkGray; Write-Host "  收尾頁 $(Join-Path $V2 'VRN2_CloseoutUI_latest.html')"; $pb = @($c.links | Where-Object { "$($_.label)" -like '貼回包*' } | Select-Object -First 1).path; if ($pb -and (Test-Path -LiteralPath $pb)) { Write-Host "  貼回包 $($pb)(上傳給 AI)" -ForegroundColor Green } }; Write-Host "[計] Handle-All 結束 · RoundAll 結束碼 $($rc) · $([int]((Get-Date) - $T0).TotalSeconds) 秒(視窗不會關)" }
```

## 可讀版 · Handle-All

```powershell
& {
$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'
if ($PSVersionTable.PSVersion.Major -lt 7) { Write-Host '[RED] 這段要 PowerShell 7 以上(pwsh · 例 7.6.9)' -ForegroundColor Red; return }
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch { }
$T0 = Get-Date
$R = $env:VRN2_ROOT ?? 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
$P = 'VeritasIntelligenceAnalytics/docs/handoff/ai/vrn2_release_v0156'
$F = 'VRN2_RoundAll_v0112.py'
$H = '5f032bc73f2f8bc7608754107dcd4dcede05be4a349f38599a12d0e5bfe18fff'
$DL = Join-Path ($env:USERPROFILE ?? $HOME) 'Downloads'
$V2 = Join-Path $R 'VIA_Reports' 'vrn2'
$Mode = "$($env:VRN2_MODE ?? 'auto')".Trim().ToLowerInvariant()
if ($Mode -notin 'auto', 'full', 'repair', 'verify', 'report') { Write-Host "[RED] VRN2_MODE = $($Mode) 不認得(auto / full / repair / verify / report)" -ForegroundColor Red; return }
Write-Host "[VRN-2] Handle-All v0104 · PowerShell $($PSVersionTable.PSVersion) · 模式 $($Mode) · VIA $($R)" -ForegroundColor Yellow
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
Write-Host '    不擋:RoundAll 會改用讀得到的夾 · 套件 v0156 裝在新夾 VRN2_Closeout_v0156' -ForegroundColor DarkGray
if ($IsWindows -and (($env:VRN2_FIX_ACL ?? (Read-Host '    要用系統管理員身分把它們的權限還原成跟 Downloads 一樣嗎?會跳 UAC(y/N)')) -match '^[yY]')) {
$cmd = (@($bad | ForEach-Object { "icacls '" + ($_.FullName -replace "'", "''") + "' /reset /T /C /Q" }) -join '; ')
try { Start-Process -FilePath (Get-Process -Id $PID).Path -Verb RunAs -Wait -ArgumentList ('-NoProfile -EncodedCommand ' + [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($cmd))) -ErrorAction Stop; foreach ($d in $bad) { $ok = $true; try { foreach ($x in @(Get-ChildItem -LiteralPath $d.FullName -File -ErrorAction Stop)) { [IO.File]::OpenRead($x.FullName).Dispose() } } catch { $ok = $false }; Write-Host "    [$(if ($ok) { 'GREEN' } else { 'YELLOW' })] $($d.FullName) $(if ($ok) { '讀得到了' } else { '還是讀不到(不擋)' })" -ForegroundColor ($ok ? 'Green' : 'Yellow') } } catch { Write-Host "[YELLOW] ③ 沒有以系統管理員身分執行($($_.Exception.Message))· 不擋" -ForegroundColor Yellow }
}
} else { Write-Host '[GREEN] ③ Downloads 的 VRN-2 套件夾都讀得到' -ForegroundColor Green }
$g1 = "$env:VIA_NET_CONSENT"; $g2 = "$env:VIA_SCRAPE_CONSENT"
$gate = ($g1 -ceq 'YES') -and ($g2 -cin 'YES', 'I_ACCEPT_RESPONSIBLE_SCRAPING')
if ($gate) { Write-Host "[GREEN] ③b VIA 網路工具同意閘 開(VIA_NET_CONSENT=$($g1) · VIA_SCRAPE_CONSENT=$($g2) · 操作員設的)· ⑥f 共識經 VIA 網路工具 + 加速器重抓(共識引擎 v0122)" -ForegroundColor Green } else { Write-Host "[YELLOW] ③b VIA 網路工具同意閘 未開(VIA_NET_CONSENT=$(($g1) ? $g1 : '(未設)') · VIA_SCRAPE_CONSENT=$(($g2) ? $g2 : '(未設)'))· repair 不重抓 ⑥f(現有共識不動)· 整輪的 ⑥f 會被 DENY · 收尾頁列「人工」" -ForegroundColor Yellow; Write-Host "    要經網路工具抓:在同一個視窗先貼 `$env:VIA_NET_CONSENT = 'YES'; `$env:VIA_SCRAPE_CONSENT = 'YES' 再貼那一行(操作員決定 · VRN-2 只讀 · 不代設)" -ForegroundColor DarkGray }
$rcp = Get-ChildItem -LiteralPath $V2 -File -Filter 'VRN2_Closeout_v0*.json' -ErrorAction SilentlyContinue | Where-Object Name -Match '^VRN2_Closeout_v\d{4}\.json$' | Sort-Object Name | Select-Object -Last 1
$last = ($rcp -and $rcp.Name -match '_v(\d{4})\.json$') ? [int]$Matches[1] : 0
$haveOut = (Test-Path -LiteralPath (Join-Path $V2 'output' 'VRN2_FinancialData_latest.json')) -and (Test-Path -LiteralPath (Join-Path $V2 'scope_in'))
if ($Mode -eq 'auto') { $Mode = ($last -ge 153 -and $haveOut) ? 'repair' : 'full'; Write-Host "[計] ④ 自動選模式 $($Mode) · 上一輪收據 $($rcp.Name ?? '沒有') · 上一輪輸出冊 $($haveOut ? '有' : '沒有')$(($Mode -eq 'full' -and $last -gt 0 -and $haveOut) ? '(上一輪輸出冊是啟動器 v0153 以前做的 · 管理器 v0257 要重做輸出冊)' : '')$(($Mode -eq 'repair') ? '(輸出冊是啟動器 v0153 以後做的 · 這版只改 ⑥f 共識出網 → 不整輪)' : '')(整輪:先貼 `$env:VRN2_MODE = 'full')" -ForegroundColor DarkGray }
if ($Mode -ne 'full' -and -not $haveOut) { Write-Host "[YELLOW] ④ 模式 $($Mode) 要上一輪的輸出冊 · 這裡沒有 → 改跑整輪" -ForegroundColor Yellow; $Mode = 'full' }
$ra = @(switch ($Mode) { 'repair' { '--only'; 'package,fix,report,closeout,pasteback' } 'verify' { '--only'; 'package,verify,report,closeout,pasteback' } 'report' { '--only'; 'report,closeout,pasteback' } })
$ra += @(($env:VRN2_ROUNDALL_ARGS ?? '') -split '\s+' | Where-Object { $_ })
$what = @{ full = '整輪(取套件 v0156 → 診斷 → 全部自測 → 跑啟動器 v0156(管理器 v0257 · ⑥f ConsensusJoin v0104 · 共識引擎 v0122 經 VIA 網路工具 + 加速器)→ 自動修 → 除錯報告 → 收尾頁 → 貼回包 · 桌機約 40 分鐘)'; repair = '取套件 v0156 → ⑤ 自動修(同意閘開:⑥f 共識改經 VIA 網路工具重抓 · ConsensusJoin v0104 + 引擎 v0122 · 重組 Combined · 增量庫 · Workbench;閘關:現有共識不動)→ 除錯報告 → 收尾頁 → 貼回包(幾分鐘)'; verify = '只重跑 ⑪ 獨立驗證(套件 v0156 的 IndependentVerifier v0114 · 用上一輪的輸出冊)→ 除錯報告 → 收尾頁 → 貼回包(約 10 分鐘)'; report = '只重做除錯報告 → 收尾頁 → 貼回包(用上一輪的結果 · 幾秒)' }[$Mode]
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

## 可讀版 · 開機行

```powershell
& {
$R = $env:VRN2_ROOT ?? 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
$P = 'VeritasIntelligenceAnalytics/docs/handoff/ai/vrn2_release_v0156'
$F = 'VRN2_HandleAll_v0104.md'
$H = '986cdad74e65ef3e106739cfd9ebbeeb7ad287919881585dfb11e11e35597148'
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
Write-Host "[GREEN] boot: Handle-All v0104 SHA-256 OK ($b)" -ForegroundColor Green
Invoke-Expression $c
}
```
