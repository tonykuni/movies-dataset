# VRN-2 · PowerShell 7 一行處理全部 · VRN2_HandleAll_v0106(2026-10-31 · 套件 v0158 · RoundAll v0114)

v0106 = v0105 + 套件 **v0158**:操作員 2026-10-31「依照你的建議進行」→ ③b OCR 隔離環境也跟 ③ 一樣,**VRN-2 自己不 pip**。

| 步驟 | 現在 |
|---|---|
| ③ 環境檢查 | 只檢查 · 缺的一個一個交 VCGC 安裝閘 `CGC_MDL056_InstallGate` 最高版號 · 裝完再檢查 · 裝不起來 24 小時不重試(v0157 起) |
| ③b OCR 隔離環境 | 已就緒(`%USERPROFILE%\envs\vrn2_ocr` 匯入得到 rapidocr + wordninja)或有指定(`VIA_VRN2_OCR_PY` + `VIA_VRN2_OCR_BRIDGE`)→ 照用;**沒就緒 → 不建 venv、不裝** · 黃燈列出建法交 VCGC · OCR 照舊排佇列(**v0158**) |
| 為什麼 ③b 不用 VCGC 安裝閘 | 安裝閘只裝進呼叫它的那個 Python(`pip --user`),裝不進另一個 venv → 隔離環境照 via_tw_fetch 的方式交 VCGC 建 |
| 收尾頁 | ③b 沒就緒 → **VCGC**(以前沒有規則,落到預設 VRN-2) |
| 舊行為 | 只有操作員明說:`--pip-install` 或 `$env:VIA_VRN2_PIP_INSTALL = '1'`(③ 和 ③b 一起) |
| 一支 Python | `VRN2_RoundAll_v0114.py`(SHA-256 `425397f5d724`)· 套件 `VRN2_Closeout_v0158.zip`(SHA-256 `dfca4f6b13fb` · runtime v0156 原樣) |

## PowerShell 7 貼這一行(443 字元 · 4 行內)

```powershell
$r="$HOME\OneDrive\Documents\movies-dataset";git -C $r fetch -q origin claude/optimistic-goodall-yhalc5;$c=(git -C $r show "FETCH_HEAD:VeritasIntelligenceAnalytics/docs/handoff/ai/vrn2_release_v0158/VRN2_HandleAll_v0106_boot.txt")-join"`n";if((Get-FileHash -InputStream ([IO.MemoryStream]::new([byte[]][char[]]$c))).Hash-eq'5aba98f6172f0eed0ed292f4f06db0501034889976e89af772e6b66f228b231a'){iex $c}else{'[RED] boot SHA-256 mismatch - not run'}
```

第一行應是 `[GREEN] boot: Handle-All v0106 SHA-256 OK`(開機檔 SHA-256 `5aba98f6172f` · Handle-All 那一行 `99598c668e4b`)。

## 同意閘(操作員決定 · VRN-2 只讀 · 不代設)

桌機 04:55 那輪 ③b 印的還是 `VIA_NET_CONSENT=YES · VIA_SCRAPE_CONSENT=(未設)` → 閘二沒開 → ⑥f 不經網路工具重抓 · 收尾頁「人工」多一項。
要經網路工具抓共識:在同一個視窗先貼下面這行,再貼最上面那一行。

```powershell
$env:VIA_SCRAPE_CONSENT = 'YES'
```

## 這次桌機貼下去會怎樣

上一輪收據 `VRN2_Closeout_v0153.json`、輸出冊在 → auto 選 **repair**(不跑啟動器 · ③ / ③b 這輪都不跑):

- 閘照舊 → 跟 04:55 一樣 **BLOCKED · VRN-2 0 · VCGC 1 · 人工 3 · 資料源 2**。
- 先設 `VIA_SCRAPE_CONSENT` → ⑥f 經 VIA 網路工具重抓 → 預期 **BLOCKED · VRN-2 0 · VCGC 1 · 人工 2 · 資料源 2**。

整輪(`$env:VRN2_MODE = 'full'`)才跑 ③ / ③b:桌機的 OCR 隔離環境以前建好了 → ③b 照用(綠);如果它不見了 → ③b 黃 · 收尾頁 VCGC 一項(建法在那一列)。

## 開機行(1,719 字元)

```powershell
& { $R = $env:VRN2_ROOT ?? 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'; $P = 'VeritasIntelligenceAnalytics/docs/handoff/ai/vrn2_release_v0158'; $F = 'VRN2_HandleAll_v0106.md'; $H = '99598c668e4b3f263365e8a47318821e0341f4cae23caa68d7153cbd687f31a3'; $top = "$(git -C $R rev-parse --show-toplevel 2>$null)".Trim(); if (-not $top) { Write-Host "[RED] boot: $R is not a git repo (set `$env:VRN2_ROOT)" -ForegroundColor Red; return }; $t = Join-Path ([IO.Path]::GetTempPath()) "vrn2_boot_$(Get-Date -Format yyyyMMddHHmmss)"; $z = Join-Path $t 'ha.zip'; New-Item -ItemType Directory -Force -Path $t | Out-Null; $ok = $false; foreach ($b in 'claude/optimistic-goodall-yhalc5', 'main') { foreach ($w in 0, 3, 9) { Start-Sleep -Seconds $w; git -C $top fetch -q origin $b 2>&1 | Out-Null; if ($LASTEXITCODE -eq 0) { break } }; git -C $top archive --format=zip -o $z "origin/$($b):$($P)" $F 2>&1 | Out-Null; if ($LASTEXITCODE -eq 0) { $ok = $true; break } }; if (-not $ok) { Write-Host "[RED] boot: cannot read $F from GitHub" -ForegroundColor Red; return }; Expand-Archive -LiteralPath $z -DestinationPath $t -Force; $md = [IO.File]::ReadAllText((Join-Path $t $F), [Text.Encoding]::UTF8) -replace "`r`n", "`n"; $c = [regex]::Match($md, '(?s)<!-- handle-all line -->\n```powershell\n(.*?)\n```').Groups[1].Value; $s = ([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash([Text.UTF8Encoding]::new($false).GetBytes($c))) -replace '-', '').ToLowerInvariant(); if ($s -ne $H) { Write-Host "[RED] boot: SHA-256 $s is not $H - not run" -ForegroundColor Red; return }; Write-Host "[GREEN] boot: Handle-All v0106 SHA-256 OK ($b)" -ForegroundColor Green; Invoke-Expression $c }
```

## cmd 視窗

```bat
pwsh -NoProfile -ExecutionPolicy Bypass -EncodedCommand JgAgAHsAIAAkAFIAIAA9ACAAJABlAG4AdgA6AFYAUgBOADIAXwBSAE8ATwBUACAAPwA/ACAAJwBDADoAXABVAHMAZQByAHMAXAB0AG8AbgB5AGsAXABPAG4AZQBEAHIAaQB2AGUAXABEAG8AYwB1AG0AZQBuAHQAcwBcAG0AbwB2AGkAZQBzAC0AZABhAHQAYQBzAGUAdABcAFYAZQByAGkAdABhAHMASQBuAHQAZQBsAGwAaQBnAGUAbgBjAGUAQQBuAGEAbAB5AHQAaQBjAHMAJwA7ACAAJABQACAAPQAgACcAVgBlAHIAaQB0AGEAcwBJAG4AdABlAGwAbABpAGcAZQBuAGMAZQBBAG4AYQBsAHkAdABpAGMAcwAvAGQAbwBjAHMALwBoAGEAbgBkAG8AZgBmAC8AYQBpAC8AdgByAG4AMgBfAHIAZQBsAGUAYQBzAGUAXwB2ADAAMQA1ADgAJwA7ACAAJABGACAAPQAgACcAVgBSAE4AMgBfAEgAYQBuAGQAbABlAEEAbABsAF8AdgAwADEAMAA2AC4AbQBkACcAOwAgACQASAAgAD0AIAAnADkAOQA1ADkAOABjADYANgA4AGUANABiADMAZgAyADYAMwAzADYANQBlADgAYQA0ADcAMwAxADgAOAAyADEAZQAwADMANAAxAGYANABjAGEAZQAyADMAYwBhAGEANgA4AGQANwAxADUAMwBjAGIAZAA2ADgANwBmADMAMQBhADMAJwA7ACAAJAB0AG8AcAAgAD0AIAAiACQAKABnAGkAdAAgAC0AQwAgACQAUgAgAHIAZQB2AC0AcABhAHIAcwBlACAALQAtAHMAaABvAHcALQB0AG8AcABsAGUAdgBlAGwAIAAyAD4AJABuAHUAbABsACkAIgAuAFQAcgBpAG0AKAApADsAIABpAGYAIAAoAC0AbgBvAHQAIAAkAHQAbwBwACkAIAB7ACAAVwByAGkAdABlAC0ASABvAHMAdAAgACIAWwBSAEUARABdACAAYgBvAG8AdAA6ACAAJABSACAAaQBzACAAbgBvAHQAIABhACAAZwBpAHQAIAByAGUAcABvACAAKABzAGUAdAAgAGAAJABlAG4AdgA6AFYAUgBOADIAXwBSAE8ATwBUACkAIgAgAC0ARgBvAHIAZQBnAHIAbwB1AG4AZABDAG8AbABvAHIAIABSAGUAZAA7ACAAcgBlAHQAdQByAG4AIAB9ADsAIAAkAHQAIAA9ACAASgBvAGkAbgAtAFAAYQB0AGgAIAAoAFsASQBPAC4AUABhAHQAaABdADoAOgBHAGUAdABUAGUAbQBwAFAAYQB0AGgAKAApACkAIAAiAHYAcgBuADIAXwBiAG8AbwB0AF8AJAAoAEcAZQB0AC0ARABhAHQAZQAgAC0ARgBvAHIAbQBhAHQAIAB5AHkAeQB5AE0ATQBkAGQASABIAG0AbQBzAHMAKQAiADsAIAAkAHoAIAA9ACAASgBvAGkAbgAtAFAAYQB0AGgAIAAkAHQAIAAnAGgAYQAuAHoAaQBwACcAOwAgAE4AZQB3AC0ASQB0AGUAbQAgAC0ASQB0AGUAbQBUAHkAcABlACAARABpAHIAZQBjAHQAbwByAHkAIAAtAEYAbwByAGMAZQAgAC0AUABhAHQAaAAgACQAdAAgAHwAIABPAHUAdAAtAE4AdQBsAGwAOwAgACQAbwBrACAAPQAgACQAZgBhAGwAcwBlADsAIABmAG8AcgBlAGEAYwBoACAAKAAkAGIAIABpAG4AIAAnAGMAbABhAHUAZABlAC8AbwBwAHQAaQBtAGkAcwB0AGkAYwAtAGcAbwBvAGQAYQBsAGwALQB5AGgAYQBsAGMANQAnACwAIAAnAG0AYQBpAG4AJwApACAAewAgAGYAbwByAGUAYQBjAGgAIAAoACQAdwAgAGkAbgAgADAALAAgADMALAAgADkAKQAgAHsAIABTAHQAYQByAHQALQBTAGwAZQBlAHAAIAAtAFMAZQBjAG8AbgBkAHMAIAAkAHcAOwAgAGcAaQB0ACAALQBDACAAJAB0AG8AcAAgAGYAZQB0AGMAaAAgAC0AcQAgAG8AcgBpAGcAaQBuACAAJABiACAAMgA+ACYAMQAgAHwAIABPAHUAdAAtAE4AdQBsAGwAOwAgAGkAZgAgACgAJABMAEEAUwBUAEUAWABJAFQAQwBPAEQARQAgAC0AZQBxACAAMAApACAAewAgAGIAcgBlAGEAawAgAH0AIAB9ADsAIABnAGkAdAAgAC0AQwAgACQAdABvAHAAIABhAHIAYwBoAGkAdgBlACAALQAtAGYAbwByAG0AYQB0AD0AegBpAHAAIAAtAG8AIAAkAHoAIAAiAG8AcgBpAGcAaQBuAC8AJAAoACQAYgApADoAJAAoACQAUAApACIAIAAkAEYAIAAyAD4AJgAxACAAfAAgAE8AdQB0AC0ATgB1AGwAbAA7ACAAaQBmACAAKAAkAEwAQQBTAFQARQBYAEkAVABDAE8ARABFACAALQBlAHEAIAAwACkAIAB7ACAAJABvAGsAIAA9ACAAJAB0AHIAdQBlADsAIABiAHIAZQBhAGsAIAB9ACAAfQA7ACAAaQBmACAAKAAtAG4AbwB0ACAAJABvAGsAKQAgAHsAIABXAHIAaQB0AGUALQBIAG8AcwB0ACAAIgBbAFIARQBEAF0AIABiAG8AbwB0ADoAIABjAGEAbgBuAG8AdAAgAHIAZQBhAGQAIAAkAEYAIABmAHIAbwBtACAARwBpAHQASAB1AGIAIgAgAC0ARgBvAHIAZQBnAHIAbwB1AG4AZABDAG8AbABvAHIAIABSAGUAZAA7ACAAcgBlAHQAdQByAG4AIAB9ADsAIABFAHgAcABhAG4AZAAtAEEAcgBjAGgAaQB2AGUAIAAtAEwAaQB0AGUAcgBhAGwAUABhAHQAaAAgACQAegAgAC0ARABlAHMAdABpAG4AYQB0AGkAbwBuAFAAYQB0AGgAIAAkAHQAIAAtAEYAbwByAGMAZQA7ACAAJABtAGQAIAA9ACAAWwBJAE8ALgBGAGkAbABlAF0AOgA6AFIAZQBhAGQAQQBsAGwAVABlAHgAdAAoACgASgBvAGkAbgAtAFAAYQB0AGgAIAAkAHQAIAAkAEYAKQAsACAAWwBUAGUAeAB0AC4ARQBuAGMAbwBkAGkAbgBnAF0AOgA6AFUAVABGADgAKQAgAC0AcgBlAHAAbABhAGMAZQAgACIAYAByAGAAbgAiACwAIAAiAGAAbgAiADsAIAAkAGMAIAA9ACAAWwByAGUAZwBlAHgAXQA6ADoATQBhAHQAYwBoACgAJABtAGQALAAgACcAKAA/AHMAKQA8ACEALQAtACAAaABhAG4AZABsAGUALQBhAGwAbAAgAGwAaQBuAGUAIAAtAC0APgBcAG4AYABgAGAAcABvAHcAZQByAHMAaABlAGwAbABcAG4AKAAuACoAPwApAFwAbgBgAGAAYAAnACkALgBHAHIAbwB1AHAAcwBbADEAXQAuAFYAYQBsAHUAZQA7ACAAJABzACAAPQAgACgAWwBCAGkAdABDAG8AbgB2AGUAcgB0AGUAcgBdADoAOgBUAG8AUwB0AHIAaQBuAGcAKABbAFMAZQBjAHUAcgBpAHQAeQAuAEMAcgB5AHAAdABvAGcAcgBhAHAAaAB5AC4AUwBIAEEAMgA1ADYAXQA6ADoAQwByAGUAYQB0AGUAKAApAC4AQwBvAG0AcAB1AHQAZQBIAGEAcwBoACgAWwBUAGUAeAB0AC4AVQBUAEYAOABFAG4AYwBvAGQAaQBuAGcAXQA6ADoAbgBlAHcAKAAkAGYAYQBsAHMAZQApAC4ARwBlAHQAQgB5AHQAZQBzACgAJABjACkAKQApACAALQByAGUAcABsAGEAYwBlACAAJwAtACcALAAgACcAJwApAC4AVABvAEwAbwB3AGUAcgBJAG4AdgBhAHIAaQBhAG4AdAAoACkAOwAgAGkAZgAgACgAJABzACAALQBuAGUAIAAkAEgAKQAgAHsAIABXAHIAaQB0AGUALQBIAG8AcwB0ACAAIgBbAFIARQBEAF0AIABiAG8AbwB0ADoAIABTAEgAQQAtADIANQA2ACAAJABzACAAaQBzACAAbgBvAHQAIAAkAEgAIAAtACAAbgBvAHQAIAByAHUAbgAiACAALQBGAG8AcgBlAGcAcgBvAHUAbgBkAEMAbwBsAG8AcgAgAFIAZQBkADsAIAByAGUAdAB1AHIAbgAgAH0AOwAgAFcAcgBpAHQAZQAtAEgAbwBzAHQAIAAiAFsARwBSAEUARQBOAF0AIABiAG8AbwB0ADoAIABIAGEAbgBkAGwAZQAtAEEAbABsACAAdgAwADEAMAA2ACAAUwBIAEEALQAyADUANgAgAE8ASwAgACgAJABiACkAIgAgAC0ARgBvAHIAZQBnAHIAbwB1AG4AZABDAG8AbABvAHIAIABHAHIAZQBlAG4AOwAgAEkAbgB2AG8AawBlAC0ARQB4AHAAcgBlAHMAcwBpAG8AbgAgACQAYwAgAH0A
```

## Handle-All 那一行(開機行從 GitHub 取這段、核對 SHA-256 才執行 · 不用貼它)

<!-- handle-all line -->
```powershell
& { $ErrorActionPreference = 'Continue'; $ProgressPreference = 'SilentlyContinue'; if ($PSVersionTable.PSVersion.Major -lt 7) { Write-Host '[RED] 這段要 PowerShell 7 以上(pwsh · 例 7.6.9)' -ForegroundColor Red; return }; try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch { }; $T0 = Get-Date; $R = $env:VRN2_ROOT ?? 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'; $P = 'VeritasIntelligenceAnalytics/docs/handoff/ai/vrn2_release_v0158'; $F = 'VRN2_RoundAll_v0114.py'; $H = '425397f5d72451619c0247354acc5c7bd7dc387d632522936a49f02145ad1b73'; $DL = Join-Path ($env:USERPROFILE ?? $HOME) 'Downloads'; $V2 = Join-Path $R 'VIA_Reports' 'vrn2'; $Mode = "$($env:VRN2_MODE ?? 'auto')".Trim().ToLowerInvariant(); if ($Mode -notin 'auto', 'full', 'repair', 'verify', 'report') { Write-Host "[RED] VRN2_MODE = $($Mode) 不認得(auto / full / repair / verify / report)" -ForegroundColor Red; return }; Write-Host "[VRN-2] Handle-All v0106 · PowerShell $($PSVersionTable.PSVersion) · 模式 $($Mode) · VIA $($R)" -ForegroundColor Yellow; $git = (Get-Command git -ErrorAction SilentlyContinue | Select-Object -First 1).Source; if (-not $git) { Write-Host '[RED] ① 找不到 git(裝 Git for Windows 後重開 PowerShell 7)' -ForegroundColor Red; return }; $top = "$(git -C $R rev-parse --show-toplevel 2>$null)".Trim(); if (-not $top) { Write-Host "[RED] ① $($R) 不是 git 倉(先設 `$env:VRN2_ROOT = '<VIA 根>')" -ForegroundColor Red; return }; $py = $env:VRN2_PY ?? (Get-Command python, py -ErrorAction SilentlyContinue | Where-Object Source -NotMatch 'WindowsApps' | Select-Object -First 1).Source; if (-not $py) { Write-Host '[RED] ① 找不到 python(不要用 WindowsApps 的假 python · 或先設 $env:VRN2_PY)' -ForegroundColor Red; return }; Write-Host "[GREEN] ① 工具 · git 倉 $($top) · $("$(& $py --version 2>&1)".Trim())($($py))" -ForegroundColor Green; if ($IsWindows) { $busy = @(Get-CimInstance Win32_Process -Filter "Name like 'python%'" -ErrorAction SilentlyContinue | Where-Object CommandLine -Match 'ActivateVRN-2|VRN2_RoundAll'); if ($busy) { Write-Host "[YELLOW] ② 已經有 $($busy.Count) 個 VRN-2 在跑(PID $($busy.ProcessId -join ', '))· 兩輪重疊會互搶鎖、變慢" -ForegroundColor Yellow; if (($env:VRN2_YES ?? (Read-Host '    等它跑完再貼比較好;還是要繼續嗎?(y/N)')) -notmatch '^[yY]') { Write-Host '[計] 沒有繼續(視窗不會關)'; return } } else { Write-Host '[GREEN] ② 沒有別的 VRN-2 在跑' -ForegroundColor Green } }; $bad = @(Get-ChildItem -LiteralPath $DL -Directory -Filter 'VRN2_Closeout_v0*' -ErrorAction SilentlyContinue | Where-Object { $ok = $true; try { foreach ($x in @(Get-ChildItem -LiteralPath $_.FullName -File -ErrorAction Stop)) { [IO.File]::OpenRead($x.FullName).Dispose() } } catch { $ok = $false }; -not $ok }); if ($bad) { Write-Host "[YELLOW] ③ $($bad.Count) 個舊套件夾目前的身分讀不到(以前用系統管理員身分跑過 · 權限只剩 Administrators):" -ForegroundColor Yellow; $bad | ForEach-Object { Write-Host "    $($_.FullName)" }; Write-Host '    不擋:RoundAll 會改用讀得到的夾 · 套件 v0158 裝在新夾 VRN2_Closeout_v0158' -ForegroundColor DarkGray; if ($IsWindows -and (($env:VRN2_FIX_ACL ?? (Read-Host '    要用系統管理員身分把它們的權限還原成跟 Downloads 一樣嗎?會跳 UAC(y/N)')) -match '^[yY]')) { $cmd = (@($bad | ForEach-Object { "icacls '" + ($_.FullName -replace "'", "''") + "' /reset /T /C /Q" }) -join '; '); try { Start-Process -FilePath (Get-Process -Id $PID).Path -Verb RunAs -Wait -ArgumentList ('-NoProfile -EncodedCommand ' + [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($cmd))) -ErrorAction Stop; foreach ($d in $bad) { $ok = $true; try { foreach ($x in @(Get-ChildItem -LiteralPath $d.FullName -File -ErrorAction Stop)) { [IO.File]::OpenRead($x.FullName).Dispose() } } catch { $ok = $false }; Write-Host "    [$(if ($ok) { 'GREEN' } else { 'YELLOW' })] $($d.FullName) $(if ($ok) { '讀得到了' } else { '還是讀不到(不擋)' })" -ForegroundColor ($ok ? 'Green' : 'Yellow') } } catch { Write-Host "[YELLOW] ③ 沒有以系統管理員身分執行($($_.Exception.Message))· 不擋" -ForegroundColor Yellow } } } else { Write-Host '[GREEN] ③ Downloads 的 VRN-2 套件夾都讀得到' -ForegroundColor Green }; $g1 = "$env:VIA_NET_CONSENT"; $g2 = "$env:VIA_SCRAPE_CONSENT"; $gate = ($g1 -ceq 'YES') -and ($g2 -cin 'YES', 'I_ACCEPT_RESPONSIBLE_SCRAPING'); if ($gate) { Write-Host "[GREEN] ③b VIA 網路工具同意閘 開(VIA_NET_CONSENT=$($g1) · VIA_SCRAPE_CONSENT=$($g2) · 操作員設的)· ⑥f 共識經 VIA 網路工具 + 加速器重抓(共識引擎 v0122)" -ForegroundColor Green } else { Write-Host "[YELLOW] ③b VIA 網路工具同意閘 未開(VIA_NET_CONSENT=$(($g1) ? $g1 : '(未設)') · VIA_SCRAPE_CONSENT=$(($g2) ? $g2 : '(未設)'))· repair 不重抓 ⑥f(現有共識不動)· 整輪的 ⑥f 會被 DENY · 收尾頁列「人工」" -ForegroundColor Yellow; Write-Host "    要經網路工具抓:在同一個視窗先貼 `$env:VIA_NET_CONSENT = 'YES'; `$env:VIA_SCRAPE_CONSENT = 'YES' 再貼那一行(操作員決定 · VRN-2 只讀 · 不代設)" -ForegroundColor DarkGray }; $rcp = Get-ChildItem -LiteralPath $V2 -File -Filter 'VRN2_Closeout_v0*.json' -ErrorAction SilentlyContinue | Where-Object Name -Match '^VRN2_Closeout_v\d{4}\.json$' | Sort-Object Name | Select-Object -Last 1; $last = ($rcp -and $rcp.Name -match '_v(\d{4})\.json$') ? [int]$Matches[1] : 0; $haveOut = (Test-Path -LiteralPath (Join-Path $V2 'output' 'VRN2_FinancialData_latest.json')) -and (Test-Path -LiteralPath (Join-Path $V2 'scope_in')); if ($Mode -eq 'auto') { $Mode = ($last -ge 153 -and $haveOut) ? 'repair' : 'full'; Write-Host "[計] ④ 自動選模式 $($Mode) · 上一輪收據 $($rcp.Name ?? '沒有') · 上一輪輸出冊 $($haveOut ? '有' : '沒有')$(($Mode -eq 'full' -and $last -gt 0 -and $haveOut) ? '(上一輪輸出冊是啟動器 v0153 以前做的 · 管理器 v0257 要重做輸出冊)' : '')$(($Mode -eq 'repair') ? '(輸出冊是啟動器 v0153 以後做的 · 這版只改 ⑥f 共識出網 → 不整輪)' : '')(整輪:先貼 `$env:VRN2_MODE = 'full')" -ForegroundColor DarkGray }; if ($Mode -ne 'full' -and -not $haveOut) { Write-Host "[YELLOW] ④ 模式 $($Mode) 要上一輪的輸出冊 · 這裡沒有 → 改跑整輪" -ForegroundColor Yellow; $Mode = 'full' }; $ra = @(switch ($Mode) { 'repair' { '--only'; 'package,fix,report,closeout,pasteback' } 'verify' { '--only'; 'package,verify,report,closeout,pasteback' } 'report' { '--only'; 'report,closeout,pasteback' } }); $ra += @(($env:VRN2_ROUNDALL_ARGS ?? '') -split '\s+' | Where-Object { $_ }); $what = @{ full = '整輪(取套件 v0158 → 診斷 → 全部自測 → 跑啟動器 v0158(③ / ③b 不 pip · 缺的經 VCGC · 管理器 v0257 · ⑥f ConsensusJoin v0104 · 共識引擎 v0122 經 VIA 網路工具 + 加速器)→ 自動修 → 除錯報告 → 收尾頁 → 貼回包 · 桌機約 40 分鐘)'; repair = '取套件 v0158 → ⑤ 自動修(同意閘開:⑥f 共識改經 VIA 網路工具重抓 · ConsensusJoin v0104 + 引擎 v0122 · 重組 Combined · 增量庫 · Workbench;閘關:現有共識不動)→ 除錯報告 → 收尾頁 → 貼回包(幾分鐘)'; verify = '只重跑 ⑪ 獨立驗證(套件 v0158 的 IndependentVerifier v0114 · 用上一輪的輸出冊)→ 除錯報告 → 收尾頁 → 貼回包(約 10 分鐘)'; report = '只重做除錯報告 → 收尾頁 → 貼回包(用上一輪的結果 · 幾秒)' }[$Mode]; Write-Host "[計] ④ 模式 $($Mode):$($what)" -ForegroundColor Cyan; $t = Join-Path ([IO.Path]::GetTempPath()) "vrn2_handleall_$(Get-Date -Format yyyyMMdd_HHmmss)"; New-Item -ItemType Directory -Force -Path $t | Out-Null; $z = Join-Path $t 'roundall.zip'; $src = $null; foreach ($b in 'claude/optimistic-goodall-yhalc5', 'main') { foreach ($w in 0, 2, 4, 8, 16) { if ($w) { Start-Sleep -Seconds $w }; git -C $top fetch -q origin $b 2>&1 | Out-Null; if ($LASTEXITCODE -eq 0) { break } }; git -C $top archive --format=zip -o $z "origin/$($b):$($P)" $F 2>&1 | Out-Null; if ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $z)) { $src = $b; break } }; if (-not $src) { Write-Host "[RED] ⑤ 讀不到 GitHub 分支或 main 的 $($F)(網路 / git)" -ForegroundColor Red; return }; Expand-Archive -LiteralPath $z -DestinationPath $t -Force; $code = [IO.File]::ReadAllText((Join-Path $t $F), [Text.Encoding]::UTF8) -replace "`r`n", "`n"; $bytes = [Text.UTF8Encoding]::new($false).GetBytes($code); $sha = ([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash($bytes)) -replace '-', '').ToLowerInvariant(); if ($sha -ne $H) { Write-Host "[RED] ⑤ $($F) SHA-256 不對($($sha))· 不執行" -ForegroundColor Red; return }; New-Item -ItemType Directory -Force -Path $DL | Out-Null; $dst = Join-Path $DL $F; [IO.File]::WriteAllBytes($dst, $bytes); Write-Host "[GREEN] ⑤ $($F) SHA-256 $($H.Substring(0, 12)) 相符(GitHub $($src))→ $($dst)" -ForegroundColor Green; Write-Host "[計] ⑥ 執行 $($py) $($F) --root $($R) $($ra -join ' ')" -ForegroundColor DarkGray; & $py $dst --root $R @ra; $rc = $LASTEXITCODE; $cj = Join-Path $V2 'VRN2_CloseoutUI_latest.json'; if (-not (Test-Path -LiteralPath $cj) -or (Get-Item -LiteralPath $cj).LastWriteTime -lt $T0) { Write-Host "[YELLOW] ⑦ 這輪沒有寫出收尾頁($($cj))· 看上面 RoundAll 的最後幾行" -ForegroundColor Yellow } else { $c = Get-Content -LiteralPath $cj -Raw -Encoding utf8 | ConvertFrom-Json; $col = @{ OPEN = 'Red'; BLOCKED = 'Yellow'; REVIEW = 'Yellow'; DATA_GAP = 'Cyan'; PASS = 'Green' }[$c.state] ?? 'White'; Write-Host ''; Write-Host "===== 收尾 · $($c.state) · $($c.state_label) · $($c.state_text)" -ForegroundColor $col; foreach ($o in 'VRN-2', 'VCGC', '人工', '資料源') { $its = @($c.items | Where-Object owner -EQ $o); if ($its) { Write-Host "  [$($o)] $($its.Count) 項" -ForegroundColor (@{ 'VRN-2' = 'Red'; 'VCGC' = 'Yellow'; '人工' = 'Yellow'; '資料源' = 'Cyan' }[$o]); foreach ($i in $its) { $d = "$($i.detail)"; Write-Host "    · $($i.step) · $($d.Substring(0, [Math]::Min(150, $d.Length)))" } } }; $nx = @{ OPEN = '下一步:把貼回包上傳給 AI(VRN-2 要修的項目 · 出新版號修)'; BLOCKED = '下一步:VRN-2 側已結案 · 剩下是 VCGC 的決定 / 安裝(上面 [VCGC] 那幾項 · 例:MOPS 經 VIA 網路工具被 DENY)→ 交 VCGC,VRN-2 不繞道'; REVIEW = '下一步:VRN-2 側已結案 · 打開收尾頁看「人工核對」那幾項的原 PDF'; DATA_GAP = '下一步:VRN-2 側已結案 · 剩外部來源本來沒有的(已附證據)'; PASS = '全綠 · 結案' }[$c.state]; Write-Host "  $($nx)" -ForegroundColor $col; Write-Host '  BLOCKED / REVIEW / DATA_GAP 都不是成功;VCGC 的 closeout_lamp 才是 VCGC 驗收(四系統對等 · 只讀互看)' -ForegroundColor DarkGray; Write-Host "  收尾頁 $(Join-Path $V2 'VRN2_CloseoutUI_latest.html')"; $pb = @($c.links | Where-Object { "$($_.label)" -like '貼回包*' } | Select-Object -First 1).path; if ($pb -and (Test-Path -LiteralPath $pb)) { Write-Host "  貼回包 $($pb)(上傳給 AI)" -ForegroundColor Green } }; Write-Host "[計] Handle-All 結束 · RoundAll 結束碼 $($rc) · $([int]((Get-Date) - $T0).TotalSeconds) 秒(視窗不會關)" }
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
$P = 'VeritasIntelligenceAnalytics/docs/handoff/ai/vrn2_release_v0158'
$F = 'VRN2_RoundAll_v0114.py'
$H = '425397f5d72451619c0247354acc5c7bd7dc387d632522936a49f02145ad1b73'
$DL = Join-Path ($env:USERPROFILE ?? $HOME) 'Downloads'
$V2 = Join-Path $R 'VIA_Reports' 'vrn2'
$Mode = "$($env:VRN2_MODE ?? 'auto')".Trim().ToLowerInvariant()
if ($Mode -notin 'auto', 'full', 'repair', 'verify', 'report') { Write-Host "[RED] VRN2_MODE = $($Mode) 不認得(auto / full / repair / verify / report)" -ForegroundColor Red; return }
Write-Host "[VRN-2] Handle-All v0106 · PowerShell $($PSVersionTable.PSVersion) · 模式 $($Mode) · VIA $($R)" -ForegroundColor Yellow
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
Write-Host '    不擋:RoundAll 會改用讀得到的夾 · 套件 v0158 裝在新夾 VRN2_Closeout_v0158' -ForegroundColor DarkGray
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
$what = @{ full = '整輪(取套件 v0158 → 診斷 → 全部自測 → 跑啟動器 v0158(③ / ③b 不 pip · 缺的經 VCGC · 管理器 v0257 · ⑥f ConsensusJoin v0104 · 共識引擎 v0122 經 VIA 網路工具 + 加速器)→ 自動修 → 除錯報告 → 收尾頁 → 貼回包 · 桌機約 40 分鐘)'; repair = '取套件 v0158 → ⑤ 自動修(同意閘開:⑥f 共識改經 VIA 網路工具重抓 · ConsensusJoin v0104 + 引擎 v0122 · 重組 Combined · 增量庫 · Workbench;閘關:現有共識不動)→ 除錯報告 → 收尾頁 → 貼回包(幾分鐘)'; verify = '只重跑 ⑪ 獨立驗證(套件 v0158 的 IndependentVerifier v0114 · 用上一輪的輸出冊)→ 除錯報告 → 收尾頁 → 貼回包(約 10 分鐘)'; report = '只重做除錯報告 → 收尾頁 → 貼回包(用上一輪的結果 · 幾秒)' }[$Mode]
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
$P = 'VeritasIntelligenceAnalytics/docs/handoff/ai/vrn2_release_v0158'
$F = 'VRN2_HandleAll_v0106.md'
$H = '99598c668e4b3f263365e8a47318821e0341f4cae23caa68d7153cbd687f31a3'
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
Write-Host "[GREEN] boot: Handle-All v0106 SHA-256 OK ($b)" -ForegroundColor Green
Invoke-Expression $c
}
```
