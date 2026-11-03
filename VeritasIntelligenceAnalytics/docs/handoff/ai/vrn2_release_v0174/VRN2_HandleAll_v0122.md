# VRN-2 · 一行處理全部 · VRN2_HandleAll_v0122(2026-11-03 · Workbench v0108:ENG049 視覺模板鎖定 · 時效 / Ticker / YFinance / 券商縮寫 / YYYY 日期 / Source · 套件 v0174 · RoundAll v0130)

操作員 2026-11-03 U/I 要求 → 做法(資料冊一個字都不改 · 只改畫面 · 匯出最後多一欄 SOURCE):

| 要求 | Workbench v0108 |
|---|---|
| Ticker Symbol / 股票代號 → Ticker / YFinance · 兩個同步顯示 · 代號下一欄接 Name | 資料頁每一冊:TICKER 欄顯示「2330 / 2330.TW」(冊裡沒有 Yahoo 代號就用 Combined / 基本資料 / 市場冊對)· 下一欄一定是 Name(沒有 NAME 的冊用 Combined 合併後的名稱補)|
| Broker 一律英文縮寫 | KGI · GS · MS · JPM · CTBC · MQ · Cathay · Mega · HNS …(滑過看原文 · 縮寫表是候選 · 等 VCGC 核發)|
| 報告日左邊加一欄:法定財報日之前或超過 30 個交易日 → 過期 | 「Freshness / 時效」:早於最近一個已過的法定公布期限(3/31 · 5/15 · 8/14 · 11/14)或距今 > 30 個交易日 → **過期**;交易日 = 週一到五 − VDF 台股休市表(唯讀借用)|
| ENG049 對帳頁當靜態視覺模板 · 字體大小與顏色一致且鎖定 · 左右面板與其他部分加上去 | 底 `#f2f1ec` · 字 `#33403f` · 標題 Cormorant Garamond 19px · 內文 Microsoft JhengHei 9.5–11px · 表頭 / 標籤 Consolas 9px 大寫 · 綠 / 琥珀 / 紅淡底標籤;整頁(左欄 · 頁首 · 分頁 · 卡片 · 矩陣 · 00 系統現況)一起套 · CSS SHA-256 釘在模組 |
| 擷取下來的時間一律 YYYY · YYYY-MM · YYYY-MM-DD | 2026E → 2026 · Dec-26F → 2026-12 · 12/25 → 2025-12 · FY26E → 2026 · 2026/5/2 → 2026-05-02(滑過看原文)|
| 所有資料最後加一欄 Source(歷史 vs 報告預估)| 每一冊最後一欄:歷史 TWSE/TPEX · 報告預估 · 報告實際 · 報告 …;CSV / JSON 匯出也帶(值照輸出冊原樣)|

| 項目 | 現在 |
|---|---|
| 套件 | `vrn2_release_v0174/VRN2_Closeout_v0174.zip`(SHA-256 `3f87bee1bda5` · 啟動器 v0174 · runtime v0163 = v0162 + Workbench v0108 · 跳過 v0173 啟動器號)|
| 一支 Python | `VRN2_RoundAll_v0130.py`(SHA-256 `93762c0f8ad7` · 自測 100 項 · 頁不是 v0108 → ⑤ 補放 v0108 + v0107 → 重渲染)|
| 自動選模式 | 收據 ≥ v0170 → **repair(一分鐘上下)**:只重渲染 Workbench |

## PowerShell 7 視窗(443 字元)

```powershell
$r="$HOME\OneDrive\Documents\movies-dataset";git -C $r fetch -q origin claude/optimistic-goodall-yhalc5;$c=(git -C $r show "FETCH_HEAD:VeritasIntelligenceAnalytics/docs/handoff/ai/vrn2_release_v0174/VRN2_HandleAll_v0122_boot.txt")-join"`n";if((Get-FileHash -InputStream ([IO.MemoryStream]::new([byte[]][char[]]$c))).Hash-eq'922c3656ff40081c7f85d8f4715d444f45ac2f9d0c76bc14ad8ba4a6a64cd3c7'){iex $c}else{'[RED] boot SHA-256 mismatch - not run'}
```

第一行應是 `[GREEN] boot: Handle-All v0122 SHA-256 OK`(開機檔 SHA-256 `922c3656ff40` · Handle-All 那一行 `d1f7fdcf68c6` · RoundAll v0130 `93762c0f8ad7`)。

## cmd 視窗(1240 字元)

```bat
pwsh -NoProfile -ExecutionPolicy Bypass -EncodedCommand JAByAD0AIgAkAEgATwBNAEUAXABPAG4AZQBEAHIAaQB2AGUAXABEAG8AYwB1AG0AZQBuAHQAcwBcAG0AbwB2AGkAZQBzAC0AZABhAHQAYQBzAGUAdAAiADsAZwBpAHQAIAAtAEMAIAAkAHIAIABmAGUAdABjAGgAIAAtAHEAIABvAHIAaQBnAGkAbgAgAGMAbABhAHUAZABlAC8AbwBwAHQAaQBtAGkAcwB0AGkAYwAtAGcAbwBvAGQAYQBsAGwALQB5AGgAYQBsAGMANQA7ACQAYwA9ACgAZwBpAHQAIAAtAEMAIAAkAHIAIABzAGgAbwB3ACAAIgBGAEUAVABDAEgAXwBIAEUAQQBEADoAVgBlAHIAaQB0AGEAcwBJAG4AdABlAGwAbABpAGcAZQBuAGMAZQBBAG4AYQBsAHkAdABpAGMAcwAvAGQAbwBjAHMALwBoAGEAbgBkAG8AZgBmAC8AYQBpAC8AdgByAG4AMgBfAHIAZQBsAGUAYQBzAGUAXwB2ADAAMQA3ADQALwBWAFIATgAyAF8ASABhAG4AZABsAGUAQQBsAGwAXwB2ADAAMQAyADIAXwBiAG8AbwB0AC4AdAB4AHQAIgApAC0AagBvAGkAbgAiAGAAbgAiADsAaQBmACgAKABHAGUAdAAtAEYAaQBsAGUASABhAHMAaAAgAC0ASQBuAHAAdQB0AFMAdAByAGUAYQBtACAAKABbAEkATwAuAE0AZQBtAG8AcgB5AFMAdAByAGUAYQBtAF0AOgA6AG4AZQB3ACgAWwBiAHkAdABlAFsAXQBdAFsAYwBoAGEAcgBbAF0AXQAkAGMAKQApACkALgBIAGEAcwBoAC0AZQBxACcAOQAyADIAYwAzADYANQA2AGYAZgA0ADAAMAA4ADEAYwA3AGYAOAA1AGQAOABmADQANwAxADUAZAA0ADQANABmADQANQBhAGMAMgBmADkAZAAwAGMANwA2AGIAYwAxADQAYQBkADgAYgBhADQAYQA2AGEANgA0AGMAZAAzAGMANwAnACkAewBpAGUAeAAgACQAYwB9AGUAbABzAGUAewAnAFsAUgBFAEQAXQAgAGIAbwBvAHQAIABTAEgAQQAtADIANQA2ACAAbQBpAHMAbQBhAHQAYwBoACAALQAgAG4AbwB0ACAAcgB1AG4AJwB9AA==
```

## 人工核對(看過原文之後 · 收尾只剩這件在你手上)

```bat
python "%USERPROFILE%\\Downloads\\VRN2_RoundAll_v0130.py" --confirm list
python "%USERPROFILE%\\Downloads\\VRN2_RoundAll_v0130.py" --confirm H-fd2ea35f --note "MQ-1560 原圖四點與摘錄一致"
```

## 開機行(1,719 字元)

```powershell
& { $R = $env:VRN2_ROOT ?? 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'; $P = 'VeritasIntelligenceAnalytics/docs/handoff/ai/vrn2_release_v0174'; $F = 'VRN2_HandleAll_v0122.md'; $H = 'd1f7fdcf68c6b0f790c233036a2d3b637fe185b67798c7204b10c45da9584a3d'; $top = "$(git -C $R rev-parse --show-toplevel 2>$null)".Trim(); if (-not $top) { Write-Host "[RED] boot: $R is not a git repo (set `$env:VRN2_ROOT)" -ForegroundColor Red; return }; $t = Join-Path ([IO.Path]::GetTempPath()) "vrn2_boot_$(Get-Date -Format yyyyMMddHHmmss)"; $z = Join-Path $t 'ha.zip'; New-Item -ItemType Directory -Force -Path $t | Out-Null; $ok = $false; foreach ($b in 'claude/optimistic-goodall-yhalc5', 'main') { foreach ($w in 0, 3, 9) { Start-Sleep -Seconds $w; git -C $top fetch -q origin $b 2>&1 | Out-Null; if ($LASTEXITCODE -eq 0) { break } }; git -C $top archive --format=zip -o $z "origin/$($b):$($P)" $F 2>&1 | Out-Null; if ($LASTEXITCODE -eq 0) { $ok = $true; break } }; if (-not $ok) { Write-Host "[RED] boot: cannot read $F from GitHub" -ForegroundColor Red; return }; Expand-Archive -LiteralPath $z -DestinationPath $t -Force; $md = [IO.File]::ReadAllText((Join-Path $t $F), [Text.Encoding]::UTF8) -replace "`r`n", "`n"; $c = [regex]::Match($md, '(?s)<!-- handle-all line -->\n```powershell\n(.*?)\n```').Groups[1].Value; $s = ([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash([Text.UTF8Encoding]::new($false).GetBytes($c))) -replace '-', '').ToLowerInvariant(); if ($s -ne $H) { Write-Host "[RED] boot: SHA-256 $s is not $H - not run" -ForegroundColor Red; return }; Write-Host "[GREEN] boot: Handle-All v0122 SHA-256 OK ($b)" -ForegroundColor Green; Invoke-Expression $c }
```

## Handle-All 那一行(開機行從 GitHub 取這段、核對 SHA-256 才執行 · 不用貼它)

<!-- handle-all line -->
```powershell
& { $ErrorActionPreference = 'Continue'; $ProgressPreference = 'Continue'; $pw0 = $null; try { if ($PSStyle) { $pw0 = $PSStyle.Progress.MaxWidth; $PSStyle.Progress.MaxWidth = [Math]::Max(30, [int][Math]::Floor(($Host.UI.RawUI.WindowSize.Width - 2) / 2)) } } catch { }; if ($PSVersionTable.PSVersion.Major -lt 7) { Write-Host '[RED] 這段要 PowerShell 7 以上(pwsh · 例 7.6.9)' -ForegroundColor Red; return }; try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch { }; $T0 = Get-Date; $R = $env:VRN2_ROOT ?? 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'; $P = 'VeritasIntelligenceAnalytics/docs/handoff/ai/vrn2_release_v0174'; $F = 'VRN2_RoundAll_v0130.py'; $H = '93762c0f8ad72b633721aac498a4f4ed871a7032fb97d27cc49741fd5366d697'; $DL = Join-Path ($env:USERPROFILE ?? $HOME) 'Downloads'; $V2 = Join-Path $R 'VIA_Reports' 'vrn2'; $Mode = "$($env:VRN2_MODE ?? 'auto')".Trim().ToLowerInvariant(); if ($Mode -notin 'auto', 'full', 'repair', 'verify', 'report') { Write-Host "[RED] VRN2_MODE = $($Mode) 不認得(auto / full / repair / verify / report)" -ForegroundColor Red; return }; Write-Host "[VRN-2] Handle-All v0122 · PowerShell $($PSVersionTable.PSVersion) · 模式 $($Mode) · VIA $($R)" -ForegroundColor Yellow; $am = Join-Path $R 'supportive modules' 'VIA_PS_PyProgress_Module.ps1'; if (-not (Get-Command Invoke-VIAPython -ErrorAction SilentlyContinue) -and (Test-Path -LiteralPath $am)) { try { . $am } catch { Write-Host "[YELLOW] ⓪ VIA 加速器進度模組載入失敗($($_.Exception.Message))· 改用內建進度條" -ForegroundColor Yellow } }; $viaProg = [bool](Get-Command Invoke-VIAPython -ErrorAction SilentlyContinue); $Stage = { param($p, $s) if (Get-Command Write-VIAProgress -ErrorAction SilentlyContinue) { Write-VIAProgress -Activity 'VRN-2 Handle-All v0122' -Status $s -Percent $p -Id 10 } else { Write-Progress -Id 10 -Activity 'VRN-2 Handle-All v0122' -Status $s -PercentComplete $p } }; if ($viaProg) { Write-Host "[GREEN] ⓪ VIA 加速器進度模板 $($am)(Invoke-VIAPython · 25 加速器 · 真百分比 · 經過 / 剩約 · 心跳 · 逾時不卡)" -ForegroundColor Green } else { Write-Host "[YELLOW] ⓪ 找不到 VIA 加速器進度模板($($am))· 改用內建進度條(一樣照 RoundAll 的 [進度] n/N 畫真百分比)" -ForegroundColor Yellow }; & $Stage 5 '① 工具(git / python)'; $git = (Get-Command git -ErrorAction SilentlyContinue | Select-Object -First 1).Source; if (-not $git) { Write-Host '[RED] ① 找不到 git(裝 Git for Windows 後重開 PowerShell 7)' -ForegroundColor Red; return }; $top = "$(git -C $R rev-parse --show-toplevel 2>$null)".Trim(); if (-not $top) { Write-Host "[RED] ① $($R) 不是 git 倉(先設 `$env:VRN2_ROOT = '<VIA 根>')" -ForegroundColor Red; return }; $py = $env:VRN2_PY ?? (Get-Command python, py -ErrorAction SilentlyContinue | Where-Object Source -NotMatch 'WindowsApps' | Select-Object -First 1).Source; if (-not $py) { Write-Host '[RED] ① 找不到 python(不要用 WindowsApps 的假 python · 或先設 $env:VRN2_PY)' -ForegroundColor Red; return }; Write-Host "[GREEN] ① 工具 · git 倉 $($top) · $("$(& $py --version 2>&1)".Trim())($($py))" -ForegroundColor Green; & $Stage 10 '② 有沒有別的 VRN-2 在跑'; if ($IsWindows) { $busy = @(Get-CimInstance Win32_Process -Filter "Name like 'python%'" -ErrorAction SilentlyContinue | Where-Object CommandLine -Match 'ActivateVRN-2|VRN2_RoundAll'); if ($busy) { Write-Host "[YELLOW] ② 已經有 $($busy.Count) 個 VRN-2 在跑(PID $($busy.ProcessId -join ', '))· 兩輪重疊會互搶鎖、變慢" -ForegroundColor Yellow; if (($env:VRN2_YES ?? (Read-Host '    等它跑完再貼比較好;還是要繼續嗎?(y/N)')) -notmatch '^[yY]') { Write-Host '[計] 沒有繼續(視窗不會關)'; return } } else { Write-Host '[GREEN] ② 沒有別的 VRN-2 在跑' -ForegroundColor Green } }; & $Stage 15 '③ Downloads 套件夾讀得到嗎'; $bad = @(Get-ChildItem -LiteralPath $DL -Directory -Filter 'VRN2_Closeout_v0*' -ErrorAction SilentlyContinue | Where-Object { $ok = $true; try { foreach ($x in @(Get-ChildItem -LiteralPath $_.FullName -File -ErrorAction Stop)) { [IO.File]::OpenRead($x.FullName).Dispose() } } catch { $ok = $false }; -not $ok }); if ($bad) { Write-Host "[YELLOW] ③ $($bad.Count) 個舊套件夾目前的身分讀不到(以前用系統管理員身分跑過 · 權限只剩 Administrators):" -ForegroundColor Yellow; $bad | ForEach-Object { Write-Host "    $($_.FullName)" }; Write-Host '    不擋:RoundAll 會改用讀得到的夾 · 套件 v0174 裝在新夾 VRN2_Closeout_v0174' -ForegroundColor DarkGray; if ($IsWindows -and (($env:VRN2_FIX_ACL ?? (Read-Host '    要用系統管理員身分把它們的權限還原成跟 Downloads 一樣嗎?會跳 UAC(y/N)')) -match '^[yY]')) { $cmd = (@($bad | ForEach-Object { "icacls '" + ($_.FullName -replace "'", "''") + "' /reset /T /C /Q" }) -join '; '); try { Start-Process -FilePath (Get-Process -Id $PID).Path -Verb RunAs -Wait -ArgumentList ('-NoProfile -EncodedCommand ' + [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($cmd))) -ErrorAction Stop; foreach ($d in $bad) { $ok = $true; try { foreach ($x in @(Get-ChildItem -LiteralPath $d.FullName -File -ErrorAction Stop)) { [IO.File]::OpenRead($x.FullName).Dispose() } } catch { $ok = $false }; Write-Host "    [$(if ($ok) { 'GREEN' } else { 'YELLOW' })] $($d.FullName) $(if ($ok) { '讀得到了' } else { '還是讀不到(不擋)' })" -ForegroundColor ($ok ? 'Green' : 'Yellow') } } catch { Write-Host "[YELLOW] ③ 沒有以系統管理員身分執行($($_.Exception.Message))· 不擋" -ForegroundColor Yellow } } } else { Write-Host '[GREEN] ③ Downloads 的 VRN-2 套件夾都讀得到' -ForegroundColor Green }; & $Stage 20 '③b VIA 網路工具同意閘(只讀)'; $g1 = "$env:VIA_NET_CONSENT"; $g2 = "$env:VIA_SCRAPE_CONSENT"; $gate = ($g1 -ceq 'YES') -and ($g2 -cin 'YES', 'I_ACCEPT_RESPONSIBLE_SCRAPING'); if ($gate) { Write-Host "[GREEN] ③b VIA 網路工具同意閘 開(VIA_NET_CONSENT=$($g1) · VIA_SCRAPE_CONSENT=$($g2) · 操作員設的)· ⑥f 共識經 VIA 網路工具 + 加速器重抓(共識引擎 v0122)" -ForegroundColor Green } else { Write-Host "[YELLOW] ③b VIA 網路工具同意閘 未開(VIA_NET_CONSENT=$(($g1) ? $g1 : '(未設)') · VIA_SCRAPE_CONSENT=$(($g2) ? $g2 : '(未設)'))· 不重抓 ⑥f;被 DENY 的輪次碟上有共識快照 → ConsensusJoin v0106 用 ASOF 快照補位 Combined 共識欄(收尾頁列「提醒」)· 沒有快照 → 留空(列「人工」)" -ForegroundColor Yellow; Write-Host "    要經網路工具抓:在同一個視窗先貼 `$env:VIA_NET_CONSENT = 'YES'; `$env:VIA_SCRAPE_CONSENT = 'YES' 再貼那一行 · cmd 視窗是 set VIA_NET_CONSENT=YES 跟 set VIA_SCRAPE_CONSENT=YES(操作員決定 · VRN-2 只讀 · 不代設)" -ForegroundColor DarkGray }; & $Stage 25 '④ 選模式'; $rcp = Get-ChildItem -LiteralPath $V2 -File -Filter 'VRN2_Closeout_v0*.json' -ErrorAction SilentlyContinue | Where-Object Name -Match '^VRN2_Closeout_v\d{4}\.json$' | Sort-Object Name | Select-Object -Last 1; $last = ($rcp -and $rcp.Name -match '_v(\d{4})\.json$') ? [int]$Matches[1] : 0; $haveOut = (Test-Path -LiteralPath (Join-Path $V2 'output' 'VRN2_FinancialData_latest.json')) -and (Test-Path -LiteralPath (Join-Path $V2 'scope_in')); if ($Mode -eq 'auto') { $Mode = ($last -ge 170 -and $haveOut) ? 'repair' : 'full'; Write-Host "[計] ④ 自動選模式 $($Mode) · 上一輪收據 $($rcp.Name ?? '沒有') · 上一輪輸出冊 $($haveOut ? '有' : '沒有')$(($Mode -eq 'full' -and $last -gt 0 -and $haveOut) ? '(上一輪輸出冊是啟動器 v0170 以前做的 → 整輪:新啟動器 v0172 重做)' : '')$(($Mode -eq 'repair') ? '(輸出冊是啟動器 v0170 以後做的 → 不整輪:VRN P0 三項由 ⑤ 自動修幾分鐘補上)' : '')(整輪:先貼 `$env:VRN2_MODE = 'full')" -ForegroundColor DarkGray }; if ($Mode -ne 'full' -and -not $haveOut) { Write-Host "[YELLOW] ④ 模式 $($Mode) 要上一輪的輸出冊 · 這裡沒有 → 改跑整輪" -ForegroundColor Yellow; $Mode = 'full' }; if ($Mode -eq 'full' -and -not $gate) { Write-Host '[YELLOW] ④ 同意閘未開 + 整輪:⑥f 共識會被 DENY(碟上有共識快照 → ConsensusJoin v0106 用 ASOF 快照補位 Combined 共識欄 · 收尾頁列「提醒」;沒有快照 → 留空 · 列「人工」)' -ForegroundColor Yellow; $a4 = $env:VRN2_YES; if (-not $a4) { try { $a4 = Read-Host '    要先中止、自己把同意閘設好再重貼嗎?(A = 中止 · Enter 或其他 = 照跑 · 閘保持關 · VRN-2 不代設)' } catch { $a4 = '' } }; if ("$a4" -match '^[aA]$') { Write-Host "    已中止(視窗不會關)· 在這個視窗貼(PowerShell):`$env:VIA_NET_CONSENT = 'YES'; `$env:VIA_SCRAPE_CONSENT = 'YES'(cmd 視窗:set VIA_NET_CONSENT=YES 與 set VIA_SCRAPE_CONSENT=YES)· 設好再重貼同一行(操作員決定 · VRN-2 不代設)" -ForegroundColor Cyan; return } }; $ra = @(switch ($Mode) { 'repair' { '--only'; 'package,fix,report,closeout,pasteback' } 'verify' { '--only'; 'package,verify,report,closeout,pasteback' } 'report' { '--only'; 'report,closeout,pasteback' } }); $ra += @(($env:VRN2_ROUNDALL_ARGS ?? '') -split '\s+' | Where-Object { $_ }); $what = @{ full = '整輪(取套件 v0174 → 診斷 → 全部自測 → 跑啟動器 v0174(③ / ③b 不 pip · 缺的經 VCGC · 管理器 v0259 · Workbench v0108(ENG049 視覺模板鎖定 · 時效 / Ticker / YFinance / 券商縮寫 / YYYY 日期 / Source · 含 v0107) · ⑬b HistoryAlign v0103(Parquet 依欄位型別寫) · ⑥f ConsensusJoin v0107(UPSIDE_ADJ 小數欄 · 舊欄 UPSIDE_PCT(ADJ) 保留標註 · v0106 閘未開快照補位 · v0105 同步還原 · TWSE / TPEX 格式合併)· 共識引擎 v0122 經 VIA 網路工具 + 加速器)→ 自動修 → 除錯報告 → 收尾頁 → 貼回包 · 桌機約 40 分鐘)'; repair = '取套件 v0174 → ⑤ 自動修(只修輸入有變 / 還缺的 · 都齊了就不動;Workbench v0108 模板鎖定 + 時效 / Ticker / Source;VRN P0 三項:⑬b HistoryAlign v0103 重寫沒寫成的 Parquet · Combined 加 UPSIDE_ADJ 小數欄(ConsensusJoin v0107 · 舊欄保留)· Workbench v0107 Basic Info 合併檢視;同意閘開:⑥f 共識改經 VIA 網路工具重抓 · ConsensusJoin v0106 + 引擎 v0122 · ⑥e 不用 MOPS(MOPS 財報移開 · 只用 TWSE / TPEX)· 擷取鎖過期 → 移開後重抓 ⑥e · 重組 Combined(同步還原 · 合併)· 增量庫(先清 MOPS 算的列 · 備份)· SSOT 新提案送核號請求 · Workbench;閘關:碟上有快照 → ConsensusJoin v0106 補位 Combined 共識欄(ASOF 標示) · 沒有 → 現有共識不動)→ 除錯報告 → 收尾頁 → 貼回包(幾分鐘 · 要重抓 ⑥e 時 1 小時上下)'; verify = '只重跑 ⑪ 獨立驗證(套件 v0174 的 IndependentVerifier v0114 · 用上一輪的輸出冊)→ 除錯報告 → 收尾頁 → 貼回包(約 10 分鐘)'; report = '只重做除錯報告 → 收尾頁 → 貼回包(用上一輪的結果 · 幾秒)' }[$Mode]; Write-Host "[計] ④ 模式 $($Mode):$($what)" -ForegroundColor Cyan; & $Stage 30 "⑤ 從 GitHub 取 $($F) · 核對 SHA-256"; $t = Join-Path ([IO.Path]::GetTempPath()) "vrn2_handleall_$(Get-Date -Format yyyyMMdd_HHmmss)"; New-Item -ItemType Directory -Force -Path $t | Out-Null; $z = Join-Path $t 'roundall.zip'; $src = $null; foreach ($b in 'claude/optimistic-goodall-yhalc5', 'main') { foreach ($w in 0, 2, 4, 8, 16) { if ($w) { Start-Sleep -Seconds $w }; git -C $top fetch -q origin $b 2>&1 | Out-Null; if ($LASTEXITCODE -eq 0) { break } }; git -C $top archive --format=zip -o $z "origin/$($b):$($P)" $F 2>&1 | Out-Null; if ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $z)) { $src = $b; break } }; if (-not $src) { Write-Host "[RED] ⑤ 讀不到 GitHub 分支或 main 的 $($F)(網路 / git)" -ForegroundColor Red; return }; $ProgressPreference = 'SilentlyContinue'; Expand-Archive -LiteralPath $z -DestinationPath $t -Force; $ProgressPreference = 'Continue'; $code = [IO.File]::ReadAllText((Join-Path $t $F), [Text.Encoding]::UTF8) -replace "`r`n", "`n"; $bytes = [Text.UTF8Encoding]::new($false).GetBytes($code); $sha = ([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash($bytes)) -replace '-', '').ToLowerInvariant(); if ($sha -ne $H) { Write-Host "[RED] ⑤ $($F) SHA-256 不對($($sha))· 不執行" -ForegroundColor Red; return }; New-Item -ItemType Directory -Force -Path $DL | Out-Null; $dst = Join-Path $DL $F; [IO.File]::WriteAllBytes($dst, $bytes); Write-Host "[GREEN] ⑤ $($F) SHA-256 $($H.Substring(0, 12)) 相符(GitHub $($src))→ $($dst)" -ForegroundColor Green; $ra += '--no-open'; $to = ($Mode -eq 'full') ? 28800 : 14400; if ("$env:VRN2_TIMEOUT_SEC" -match '^[1-9]\d*$') { $to = [int]$env:VRN2_TIMEOUT_SEC } elseif ("$env:VIA_PY_TIMEOUT_SEC" -eq '0') { $to = 0 }; Write-Host "[計] ⑥ 執行 $($py) $($F) --root $($R) $($ra -join ' ') · $($viaProg ? '經 VIA 加速器進度模板 Invoke-VIAPython' : '內建進度條') · 逾時保底 $(($to -gt 0) ? "$($to) 秒" : '不設限')(不卡斷)" -ForegroundColor DarkGray; & $Stage 35 "⑥ RoundAll · 模式 $($Mode)"; Write-Progress -Id 10 -Activity 'VRN-2 Handle-All v0122' -Completed; $ub = $env:PYTHONUNBUFFERED; $env:PYTHONUNBUFFERED = '1'; if ($viaProg) { Invoke-VIAPython -Python $py -TimeoutSec $to -Rest (@($dst, '--root', $R) + $ra) } else { & $py $dst --root $R @ra 2>&1 | ForEach-Object { $l = "$_"; if ($l -match '^\[進度\]\s*(\d+)\s*/\s*(\d+)\s*(.*)$' -and [int]$Matches[2] -gt 0) { Write-Progress -Id 13 -Activity "VRN-2 · $($F)" -Status "$($Matches[1])/$($Matches[2]) · $($Matches[3])" -PercentComplete ([Math]::Min(100, [int](100 * [int]$Matches[1] / [int]$Matches[2]))) }; $l }; Write-Progress -Id 13 -Activity "VRN-2 · $($F)" -Completed }; $rc = $LASTEXITCODE; $env:PYTHONUNBUFFERED = $ub; if ($rc -eq 124 -and $viaProg) { Write-Host "[YELLOW] ⑥ RoundAll 逾 $($to) 秒被停(不卡斷保底 · 只停它自己那棵行程樹)· 真的要更久:先貼 `$env:VRN2_TIMEOUT_SEC = '28800' 再貼那一行" -ForegroundColor Yellow }; & $Stage 97 '⑦ 收尾 · 開收尾頁'; $cj = Join-Path $V2 'VRN2_CloseoutUI_latest.json'; if (-not (Test-Path -LiteralPath $cj) -or (Get-Item -LiteralPath $cj).LastWriteTime -lt $T0) { Write-Host "[YELLOW] ⑦ 這輪沒有寫出收尾頁($($cj))· 看上面 RoundAll 的最後幾行" -ForegroundColor Yellow } else { $c = Get-Content -LiteralPath $cj -Raw -Encoding utf8 | ConvertFrom-Json; $col = @{ OPEN = 'Red'; BLOCKED = 'Yellow'; REVIEW = 'Yellow'; DATA_GAP = 'Cyan'; PASS = 'Green' }[$c.state] ?? 'White'; Write-Host ''; Write-Host "===== 收尾 · $($c.state) · $($c.state_label) · $($c.state_text)" -ForegroundColor $col; foreach ($o in 'VRN-2', 'VCGC', '人工', '資料源') { $its = @($c.items | Where-Object owner -EQ $o); if ($its) { Write-Host "  [$($o)] $($its.Count) 項" -ForegroundColor (@{ 'VRN-2' = 'Red'; 'VCGC' = 'Yellow'; '人工' = 'Yellow'; '資料源' = 'Cyan' }[$o]); foreach ($i in $its) { $d = "$($i.detail)"; Write-Host "    · $($i.step) · $($d.Substring(0, [Math]::Min(150, $d.Length)))" } } }; $nx = @{ OPEN = '下一步:把貼回包上傳給 AI(VRN-2 要修的項目 · 出新版號修)'; BLOCKED = '下一步:VRN-2 側已結案 · 剩下是 VCGC 的決定 / 安裝(上面 [VCGC] 那幾項 · 例:MOPS 經 VIA 網路工具被 DENY)→ 交 VCGC,VRN-2 不繞道'; REVIEW = '下一步:VRN-2 側已結案 · 打開收尾頁看「人工核對」那幾項的原 PDF · 看過原文沒問題 → 照收尾頁那一項的 --confirm 指令記下(只有你打才算)'; DATA_GAP = '下一步:VRN-2 側已結案 · 剩外部來源本來沒有的(已附證據)'; PASS = '全綠 · 結案' }[$c.state]; Write-Host "  $($nx)" -ForegroundColor $col; Write-Host '  BLOCKED / REVIEW / DATA_GAP 都不是成功;VCGC 的 closeout_lamp 才是 VCGC 驗收(四系統對等 · 只讀互看)' -ForegroundColor DarkGray; Write-Host "  收尾頁 $(Join-Path $V2 'VRN2_CloseoutUI_latest.html')"; $pb = @($c.links | Where-Object { "$($_.label)" -like '貼回包*' } | Select-Object -First 1).path; if ($pb -and (Test-Path -LiteralPath $pb)) { Write-Host "  貼回包 $($pb)(上傳給 AI)" -ForegroundColor Green }; $html = Join-Path $V2 'VRN2_CloseoutUI_latest.html'; $nopen = " · VIA_NO_OPEN=1 是 VIA 批次工具的零跳出;這頁是操作員 2026-10-31 指定跑完要跳出的 VRN-2 收尾頁 · 不要跳:先貼 `$env:VRN2_NO_UI = '1'"; if (Test-Path -LiteralPath $html) { if ("$env:VRN2_NO_UI" -eq '1') { Write-Host '  [計] ⑧ VRN2_NO_UI=1 · 不開收尾頁(上面那個檔自己開)' -ForegroundColor DarkGray } elseif (-not $IsWindows) { Write-Host '  [計] ⑧ 不是 Windows · 收尾頁自己開(上面那個檔)' -ForegroundColor DarkGray } else { try { Microsoft.PowerShell.Management\Start-Process -FilePath $html -ErrorAction Stop; Write-Host "  [GREEN] ⑧ 已開收尾頁(預設瀏覽器 · 不擋這個視窗)$(("$env:VIA_NO_OPEN" -eq '1') ? $nopen : '')" -ForegroundColor Green } catch { Write-Host "  [YELLOW] ⑧ 收尾頁沒開成($($_.Exception.Message))· 自己開上面那個檔" -ForegroundColor Yellow } } } }; Write-Progress -Id 10 -Activity 'VRN-2 Handle-All v0122' -Completed; try { if ($null -ne $pw0) { $PSStyle.Progress.MaxWidth = $pw0 } } catch { }; Write-Host "[計] Handle-All 結束 · RoundAll 結束碼 $($rc) · $([int]((Get-Date) - $T0).TotalSeconds) 秒(視窗不會關)" }
```

## 可讀版 · Handle-All

```powershell
& {
$ErrorActionPreference = 'Continue'
$ProgressPreference = 'Continue'
# v0110 進度列不超過視窗一半寬(中文 / ⑥ / · 一個字佔兩格 · 超寬會折行,PowerShell 的進度列重畫算錯行數,舊的那條就一直疊在畫面上)
$pw0 = $null; try { if ($PSStyle) { $pw0 = $PSStyle.Progress.MaxWidth; $PSStyle.Progress.MaxWidth = [Math]::Max(30, [int][Math]::Floor(($Host.UI.RawUI.WindowSize.Width - 2) / 2)) } } catch { }
if ($PSVersionTable.PSVersion.Major -lt 7) { Write-Host '[RED] 這段要 PowerShell 7 以上(pwsh · 例 7.6.9)' -ForegroundColor Red; return }
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch { }
$T0 = Get-Date
$R = $env:VRN2_ROOT ?? 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
$P = 'VeritasIntelligenceAnalytics/docs/handoff/ai/vrn2_release_v0174'
$F = 'VRN2_RoundAll_v0130.py'
$H = '93762c0f8ad72b633721aac498a4f4ed871a7032fb97d27cc49741fd5366d697'
$DL = Join-Path ($env:USERPROFILE ?? $HOME) 'Downloads'
$V2 = Join-Path $R 'VIA_Reports' 'vrn2'
$Mode = "$($env:VRN2_MODE ?? 'auto')".Trim().ToLowerInvariant()
if ($Mode -notin 'auto', 'full', 'repair', 'verify', 'report') { Write-Host "[RED] VRN2_MODE = $($Mode) 不認得(auto / full / repair / verify / report)" -ForegroundColor Red; return }
Write-Host "[VRN-2] Handle-All v0122 · PowerShell $($PSVersionTable.PSVersion) · 模式 $($Mode) · VIA $($R)" -ForegroundColor Yellow
# v0108 VIA 加速器進度模板(VIA 自己的 supportive modules · 只載入不改):25 加速器點亮 · Invoke-VIAPython 真百分比 · 心跳 · 逾時不卡
$am = Join-Path $R 'supportive modules' 'VIA_PS_PyProgress_Module.ps1'
if (-not (Get-Command Invoke-VIAPython -ErrorAction SilentlyContinue) -and (Test-Path -LiteralPath $am)) { try { . $am } catch { Write-Host "[YELLOW] ⓪ VIA 加速器進度模組載入失敗($($_.Exception.Message))· 改用內建進度條" -ForegroundColor Yellow } }
$viaProg = [bool](Get-Command Invoke-VIAPython -ErrorAction SilentlyContinue)
$Stage = { param($p, $s) if (Get-Command Write-VIAProgress -ErrorAction SilentlyContinue) { Write-VIAProgress -Activity 'VRN-2 Handle-All v0122' -Status $s -Percent $p -Id 10 } else { Write-Progress -Id 10 -Activity 'VRN-2 Handle-All v0122' -Status $s -PercentComplete $p } }
if ($viaProg) { Write-Host "[GREEN] ⓪ VIA 加速器進度模板 $($am)(Invoke-VIAPython · 25 加速器 · 真百分比 · 經過 / 剩約 · 心跳 · 逾時不卡)" -ForegroundColor Green } else { Write-Host "[YELLOW] ⓪ 找不到 VIA 加速器進度模板($($am))· 改用內建進度條(一樣照 RoundAll 的 [進度] n/N 畫真百分比)" -ForegroundColor Yellow }
& $Stage 5 '① 工具(git / python)'
$git = (Get-Command git -ErrorAction SilentlyContinue | Select-Object -First 1).Source
if (-not $git) { Write-Host '[RED] ① 找不到 git(裝 Git for Windows 後重開 PowerShell 7)' -ForegroundColor Red; return }
$top = "$(git -C $R rev-parse --show-toplevel 2>$null)".Trim()
if (-not $top) { Write-Host "[RED] ① $($R) 不是 git 倉(先設 `$env:VRN2_ROOT = '<VIA 根>')" -ForegroundColor Red; return }
$py = $env:VRN2_PY ?? (Get-Command python, py -ErrorAction SilentlyContinue | Where-Object Source -NotMatch 'WindowsApps' | Select-Object -First 1).Source
if (-not $py) { Write-Host '[RED] ① 找不到 python(不要用 WindowsApps 的假 python · 或先設 $env:VRN2_PY)' -ForegroundColor Red; return }
Write-Host "[GREEN] ① 工具 · git 倉 $($top) · $("$(& $py --version 2>&1)".Trim())($($py))" -ForegroundColor Green
& $Stage 10 '② 有沒有別的 VRN-2 在跑'
if ($IsWindows) {
$busy = @(Get-CimInstance Win32_Process -Filter "Name like 'python%'" -ErrorAction SilentlyContinue | Where-Object CommandLine -Match 'ActivateVRN-2|VRN2_RoundAll')
if ($busy) {
Write-Host "[YELLOW] ② 已經有 $($busy.Count) 個 VRN-2 在跑(PID $($busy.ProcessId -join ', '))· 兩輪重疊會互搶鎖、變慢" -ForegroundColor Yellow
if (($env:VRN2_YES ?? (Read-Host '    等它跑完再貼比較好;還是要繼續嗎?(y/N)')) -notmatch '^[yY]') { Write-Host '[計] 沒有繼續(視窗不會關)'; return }
} else { Write-Host '[GREEN] ② 沒有別的 VRN-2 在跑' -ForegroundColor Green }
}
& $Stage 15 '③ Downloads 套件夾讀得到嗎'
$bad = @(Get-ChildItem -LiteralPath $DL -Directory -Filter 'VRN2_Closeout_v0*' -ErrorAction SilentlyContinue | Where-Object { $ok = $true; try { foreach ($x in @(Get-ChildItem -LiteralPath $_.FullName -File -ErrorAction Stop)) { [IO.File]::OpenRead($x.FullName).Dispose() } } catch { $ok = $false }; -not $ok })
if ($bad) {
Write-Host "[YELLOW] ③ $($bad.Count) 個舊套件夾目前的身分讀不到(以前用系統管理員身分跑過 · 權限只剩 Administrators):" -ForegroundColor Yellow
$bad | ForEach-Object { Write-Host "    $($_.FullName)" }
Write-Host '    不擋:RoundAll 會改用讀得到的夾 · 套件 v0174 裝在新夾 VRN2_Closeout_v0174' -ForegroundColor DarkGray
if ($IsWindows -and (($env:VRN2_FIX_ACL ?? (Read-Host '    要用系統管理員身分把它們的權限還原成跟 Downloads 一樣嗎?會跳 UAC(y/N)')) -match '^[yY]')) {
$cmd = (@($bad | ForEach-Object { "icacls '" + ($_.FullName -replace "'", "''") + "' /reset /T /C /Q" }) -join '; ')
try { Start-Process -FilePath (Get-Process -Id $PID).Path -Verb RunAs -Wait -ArgumentList ('-NoProfile -EncodedCommand ' + [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($cmd))) -ErrorAction Stop; foreach ($d in $bad) { $ok = $true; try { foreach ($x in @(Get-ChildItem -LiteralPath $d.FullName -File -ErrorAction Stop)) { [IO.File]::OpenRead($x.FullName).Dispose() } } catch { $ok = $false }; Write-Host "    [$(if ($ok) { 'GREEN' } else { 'YELLOW' })] $($d.FullName) $(if ($ok) { '讀得到了' } else { '還是讀不到(不擋)' })" -ForegroundColor ($ok ? 'Green' : 'Yellow') } } catch { Write-Host "[YELLOW] ③ 沒有以系統管理員身分執行($($_.Exception.Message))· 不擋" -ForegroundColor Yellow }
}
} else { Write-Host '[GREEN] ③ Downloads 的 VRN-2 套件夾都讀得到' -ForegroundColor Green }
& $Stage 20 '③b VIA 網路工具同意閘(只讀)'
$g1 = "$env:VIA_NET_CONSENT"; $g2 = "$env:VIA_SCRAPE_CONSENT"
$gate = ($g1 -ceq 'YES') -and ($g2 -cin 'YES', 'I_ACCEPT_RESPONSIBLE_SCRAPING')
if ($gate) { Write-Host "[GREEN] ③b VIA 網路工具同意閘 開(VIA_NET_CONSENT=$($g1) · VIA_SCRAPE_CONSENT=$($g2) · 操作員設的)· ⑥f 共識經 VIA 網路工具 + 加速器重抓(共識引擎 v0122)" -ForegroundColor Green } else { Write-Host "[YELLOW] ③b VIA 網路工具同意閘 未開(VIA_NET_CONSENT=$(($g1) ? $g1 : '(未設)') · VIA_SCRAPE_CONSENT=$(($g2) ? $g2 : '(未設)'))· 不重抓 ⑥f;被 DENY 的輪次碟上有共識快照 → ConsensusJoin v0106 用 ASOF 快照補位 Combined 共識欄(收尾頁列「提醒」)· 沒有快照 → 留空(列「人工」)" -ForegroundColor Yellow; Write-Host "    要經網路工具抓:在同一個視窗先貼 `$env:VIA_NET_CONSENT = 'YES'; `$env:VIA_SCRAPE_CONSENT = 'YES' 再貼那一行 · cmd 視窗是 set VIA_NET_CONSENT=YES 跟 set VIA_SCRAPE_CONSENT=YES(操作員決定 · VRN-2 只讀 · 不代設)" -ForegroundColor DarkGray }
& $Stage 25 '④ 選模式'
$rcp = Get-ChildItem -LiteralPath $V2 -File -Filter 'VRN2_Closeout_v0*.json' -ErrorAction SilentlyContinue | Where-Object Name -Match '^VRN2_Closeout_v\d{4}\.json$' | Sort-Object Name | Select-Object -Last 1
$last = ($rcp -and $rcp.Name -match '_v(\d{4})\.json$') ? [int]$Matches[1] : 0
$haveOut = (Test-Path -LiteralPath (Join-Path $V2 'output' 'VRN2_FinancialData_latest.json')) -and (Test-Path -LiteralPath (Join-Path $V2 'scope_in'))
if ($Mode -eq 'auto') { $Mode = ($last -ge 170 -and $haveOut) ? 'repair' : 'full'; Write-Host "[計] ④ 自動選模式 $($Mode) · 上一輪收據 $($rcp.Name ?? '沒有') · 上一輪輸出冊 $($haveOut ? '有' : '沒有')$(($Mode -eq 'full' -and $last -gt 0 -and $haveOut) ? '(上一輪輸出冊是啟動器 v0170 以前做的 → 整輪:新啟動器 v0172 重做)' : '')$(($Mode -eq 'repair') ? '(輸出冊是啟動器 v0170 以後做的 → 不整輪:VRN P0 三項由 ⑤ 自動修幾分鐘補上)' : '')(整輪:先貼 `$env:VRN2_MODE = 'full')" -ForegroundColor DarkGray }
if ($Mode -ne 'full' -and -not $haveOut) { Write-Host "[YELLOW] ④ 模式 $($Mode) 要上一輪的輸出冊 · 這裡沒有 → 改跑整輪" -ForegroundColor Yellow; $Mode = 'full' }
if ($Mode -eq 'full' -and -not $gate) {
Write-Host '[YELLOW] ④ 同意閘未開 + 整輪:⑥f 共識會被 DENY(碟上有共識快照 → ConsensusJoin v0106 用 ASOF 快照補位 Combined 共識欄 · 收尾頁列「提醒」;沒有快照 → 留空 · 列「人工」)' -ForegroundColor Yellow
$a4 = $env:VRN2_YES
if (-not $a4) { try { $a4 = Read-Host '    要先中止、自己把同意閘設好再重貼嗎?(A = 中止 · Enter 或其他 = 照跑 · 閘保持關 · VRN-2 不代設)' } catch { $a4 = '' } }
if ("$a4" -match '^[aA]$') { Write-Host "    已中止(視窗不會關)· 在這個視窗貼(PowerShell):`$env:VIA_NET_CONSENT = 'YES'; `$env:VIA_SCRAPE_CONSENT = 'YES'(cmd 視窗:set VIA_NET_CONSENT=YES 與 set VIA_SCRAPE_CONSENT=YES)· 設好再重貼同一行(操作員決定 · VRN-2 不代設)" -ForegroundColor Cyan; return }
}
$ra = @(switch ($Mode) { 'repair' { '--only'; 'package,fix,report,closeout,pasteback' } 'verify' { '--only'; 'package,verify,report,closeout,pasteback' } 'report' { '--only'; 'report,closeout,pasteback' } })
$ra += @(($env:VRN2_ROUNDALL_ARGS ?? '') -split '\s+' | Where-Object { $_ })
$what = @{ full = '整輪(取套件 v0174 → 診斷 → 全部自測 → 跑啟動器 v0174(③ / ③b 不 pip · 缺的經 VCGC · 管理器 v0259 · Workbench v0108(ENG049 視覺模板鎖定 · 時效 / Ticker / YFinance / 券商縮寫 / YYYY 日期 / Source · 含 v0107) · ⑬b HistoryAlign v0103(Parquet 依欄位型別寫) · ⑥f ConsensusJoin v0107(UPSIDE_ADJ 小數欄 · 舊欄 UPSIDE_PCT(ADJ) 保留標註 · v0106 閘未開快照補位 · v0105 同步還原 · TWSE / TPEX 格式合併)· 共識引擎 v0122 經 VIA 網路工具 + 加速器)→ 自動修 → 除錯報告 → 收尾頁 → 貼回包 · 桌機約 40 分鐘)'; repair = '取套件 v0174 → ⑤ 自動修(只修輸入有變 / 還缺的 · 都齊了就不動;Workbench v0108 模板鎖定 + 時效 / Ticker / Source;VRN P0 三項:⑬b HistoryAlign v0103 重寫沒寫成的 Parquet · Combined 加 UPSIDE_ADJ 小數欄(ConsensusJoin v0107 · 舊欄保留)· Workbench v0107 Basic Info 合併檢視;同意閘開:⑥f 共識改經 VIA 網路工具重抓 · ConsensusJoin v0106 + 引擎 v0122 · ⑥e 不用 MOPS(MOPS 財報移開 · 只用 TWSE / TPEX)· 擷取鎖過期 → 移開後重抓 ⑥e · 重組 Combined(同步還原 · 合併)· 增量庫(先清 MOPS 算的列 · 備份)· SSOT 新提案送核號請求 · Workbench;閘關:碟上有快照 → ConsensusJoin v0106 補位 Combined 共識欄(ASOF 標示) · 沒有 → 現有共識不動)→ 除錯報告 → 收尾頁 → 貼回包(幾分鐘 · 要重抓 ⑥e 時 1 小時上下)'; verify = '只重跑 ⑪ 獨立驗證(套件 v0174 的 IndependentVerifier v0114 · 用上一輪的輸出冊)→ 除錯報告 → 收尾頁 → 貼回包(約 10 分鐘)'; report = '只重做除錯報告 → 收尾頁 → 貼回包(用上一輪的結果 · 幾秒)' }[$Mode]
Write-Host "[計] ④ 模式 $($Mode):$($what)" -ForegroundColor Cyan
& $Stage 30 "⑤ 從 GitHub 取 $($F) · 核對 SHA-256"
$t = Join-Path ([IO.Path]::GetTempPath()) "vrn2_handleall_$(Get-Date -Format yyyyMMdd_HHmmss)"
New-Item -ItemType Directory -Force -Path $t | Out-Null
$z = Join-Path $t 'roundall.zip'
$src = $null
foreach ($b in 'claude/optimistic-goodall-yhalc5', 'main') { foreach ($w in 0, 2, 4, 8, 16) { if ($w) { Start-Sleep -Seconds $w }; git -C $top fetch -q origin $b 2>&1 | Out-Null; if ($LASTEXITCODE -eq 0) { break } }; git -C $top archive --format=zip -o $z "origin/$($b):$($P)" $F 2>&1 | Out-Null; if ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $z)) { $src = $b; break } }
if (-not $src) { Write-Host "[RED] ⑤ 讀不到 GitHub 分支或 main 的 $($F)(網路 / git)" -ForegroundColor Red; return }
$ProgressPreference = 'SilentlyContinue'; Expand-Archive -LiteralPath $z -DestinationPath $t -Force; $ProgressPreference = 'Continue'
$code = [IO.File]::ReadAllText((Join-Path $t $F), [Text.Encoding]::UTF8) -replace "`r`n", "`n"
$bytes = [Text.UTF8Encoding]::new($false).GetBytes($code)
$sha = ([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash($bytes)) -replace '-', '').ToLowerInvariant()
if ($sha -ne $H) { Write-Host "[RED] ⑤ $($F) SHA-256 不對($($sha))· 不執行" -ForegroundColor Red; return }
New-Item -ItemType Directory -Force -Path $DL | Out-Null
$dst = Join-Path $DL $F
[IO.File]::WriteAllBytes($dst, $bytes)
Write-Host "[GREEN] ⑤ $($F) SHA-256 $($H.Substring(0, 12)) 相符(GitHub $($src))→ $($dst)" -ForegroundColor Green
# v0108 RoundAll 不自己開頁(--no-open)· 跑完由這裡開收尾頁 · v0110 逾時保底:整輪 8 小時 · 其他 4 小時(⑤ 重抓 ⑥e 最長 90 分 + 填值 40 分)($env:VRN2_TIMEOUT_SEC 可調 · VIA_PY_TIMEOUT_SEC=0 = 不設限)
$ra += '--no-open'
$to = ($Mode -eq 'full') ? 28800 : 14400
if ("$env:VRN2_TIMEOUT_SEC" -match '^[1-9]\d*$') { $to = [int]$env:VRN2_TIMEOUT_SEC } elseif ("$env:VIA_PY_TIMEOUT_SEC" -eq '0') { $to = 0 }
Write-Host "[計] ⑥ 執行 $($py) $($F) --root $($R) $($ra -join ' ') · $($viaProg ? '經 VIA 加速器進度模板 Invoke-VIAPython' : '內建進度條') · 逾時保底 $(($to -gt 0) ? "$($to) 秒" : '不設限')(不卡斷)" -ForegroundColor DarkGray
& $Stage 35 "⑥ RoundAll · 模式 $($Mode)"
# v0110 RoundAll 跑的時候只留它那一條真百分比(少一條就少一次重畫)
Write-Progress -Id 10 -Activity 'VRN-2 Handle-All v0122' -Completed
$ub = $env:PYTHONUNBUFFERED
$env:PYTHONUNBUFFERED = '1'
if ($viaProg) { Invoke-VIAPython -Python $py -TimeoutSec $to -Rest (@($dst, '--root', $R) + $ra) } else { & $py $dst --root $R @ra 2>&1 | ForEach-Object { $l = "$_"; if ($l -match '^\[進度\]\s*(\d+)\s*/\s*(\d+)\s*(.*)$' -and [int]$Matches[2] -gt 0) { Write-Progress -Id 13 -Activity "VRN-2 · $($F)" -Status "$($Matches[1])/$($Matches[2]) · $($Matches[3])" -PercentComplete ([Math]::Min(100, [int](100 * [int]$Matches[1] / [int]$Matches[2]))) }; $l }; Write-Progress -Id 13 -Activity "VRN-2 · $($F)" -Completed }
$rc = $LASTEXITCODE
$env:PYTHONUNBUFFERED = $ub
if ($rc -eq 124 -and $viaProg) { Write-Host "[YELLOW] ⑥ RoundAll 逾 $($to) 秒被停(不卡斷保底 · 只停它自己那棵行程樹)· 真的要更久:先貼 `$env:VRN2_TIMEOUT_SEC = '28800' 再貼那一行" -ForegroundColor Yellow }
& $Stage 97 '⑦ 收尾 · 開收尾頁'
$cj = Join-Path $V2 'VRN2_CloseoutUI_latest.json'
if (-not (Test-Path -LiteralPath $cj) -or (Get-Item -LiteralPath $cj).LastWriteTime -lt $T0) { Write-Host "[YELLOW] ⑦ 這輪沒有寫出收尾頁($($cj))· 看上面 RoundAll 的最後幾行" -ForegroundColor Yellow } else {
$c = Get-Content -LiteralPath $cj -Raw -Encoding utf8 | ConvertFrom-Json
$col = @{ OPEN = 'Red'; BLOCKED = 'Yellow'; REVIEW = 'Yellow'; DATA_GAP = 'Cyan'; PASS = 'Green' }[$c.state] ?? 'White'
Write-Host ''
Write-Host "===== 收尾 · $($c.state) · $($c.state_label) · $($c.state_text)" -ForegroundColor $col
foreach ($o in 'VRN-2', 'VCGC', '人工', '資料源') { $its = @($c.items | Where-Object owner -EQ $o); if ($its) { Write-Host "  [$($o)] $($its.Count) 項" -ForegroundColor (@{ 'VRN-2' = 'Red'; 'VCGC' = 'Yellow'; '人工' = 'Yellow'; '資料源' = 'Cyan' }[$o]); foreach ($i in $its) { $d = "$($i.detail)"; Write-Host "    · $($i.step) · $($d.Substring(0, [Math]::Min(150, $d.Length)))" } } }
$nx = @{ OPEN = '下一步:把貼回包上傳給 AI(VRN-2 要修的項目 · 出新版號修)'; BLOCKED = '下一步:VRN-2 側已結案 · 剩下是 VCGC 的決定 / 安裝(上面 [VCGC] 那幾項 · 例:MOPS 經 VIA 網路工具被 DENY)→ 交 VCGC,VRN-2 不繞道'; REVIEW = '下一步:VRN-2 側已結案 · 打開收尾頁看「人工核對」那幾項的原 PDF · 看過原文沒問題 → 照收尾頁那一項的 --confirm 指令記下(只有你打才算)'; DATA_GAP = '下一步:VRN-2 側已結案 · 剩外部來源本來沒有的(已附證據)'; PASS = '全綠 · 結案' }[$c.state]
Write-Host "  $($nx)" -ForegroundColor $col
Write-Host '  BLOCKED / REVIEW / DATA_GAP 都不是成功;VCGC 的 closeout_lamp 才是 VCGC 驗收(四系統對等 · 只讀互看)' -ForegroundColor DarkGray
Write-Host "  收尾頁 $(Join-Path $V2 'VRN2_CloseoutUI_latest.html')"
$pb = @($c.links | Where-Object { "$($_.label)" -like '貼回包*' } | Select-Object -First 1).path
if ($pb -and (Test-Path -LiteralPath $pb)) { Write-Host "  貼回包 $($pb)(上傳給 AI)" -ForegroundColor Green }
# v0108 跑完自動開收尾頁(預設瀏覽器 · 不擋這個視窗)· 這頁是 VRN-2 自己的 · 操作員 2026-10-31 指定要跳出 · 不要跳:$env:VRN2_NO_UI = '1'
$html = Join-Path $V2 'VRN2_CloseoutUI_latest.html'
$nopen = " · VIA_NO_OPEN=1 是 VIA 批次工具的零跳出;這頁是操作員 2026-10-31 指定跑完要跳出的 VRN-2 收尾頁 · 不要跳:先貼 `$env:VRN2_NO_UI = '1'"
if (Test-Path -LiteralPath $html) { if ("$env:VRN2_NO_UI" -eq '1') { Write-Host '  [計] ⑧ VRN2_NO_UI=1 · 不開收尾頁(上面那個檔自己開)' -ForegroundColor DarkGray } elseif (-not $IsWindows) { Write-Host '  [計] ⑧ 不是 Windows · 收尾頁自己開(上面那個檔)' -ForegroundColor DarkGray } else { try { Microsoft.PowerShell.Management\Start-Process -FilePath $html -ErrorAction Stop; Write-Host "  [GREEN] ⑧ 已開收尾頁(預設瀏覽器 · 不擋這個視窗)$(("$env:VIA_NO_OPEN" -eq '1') ? $nopen : '')" -ForegroundColor Green } catch { Write-Host "  [YELLOW] ⑧ 收尾頁沒開成($($_.Exception.Message))· 自己開上面那個檔" -ForegroundColor Yellow } } }
}
Write-Progress -Id 10 -Activity 'VRN-2 Handle-All v0122' -Completed
try { if ($null -ne $pw0) { $PSStyle.Progress.MaxWidth = $pw0 } } catch { }
Write-Host "[計] Handle-All 結束 · RoundAll 結束碼 $($rc) · $([int]((Get-Date) - $T0).TotalSeconds) 秒(視窗不會關)"
}
```

## 可讀版 · 開機行

```powershell
& {
$R = $env:VRN2_ROOT ?? 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
$P = 'VeritasIntelligenceAnalytics/docs/handoff/ai/vrn2_release_v0174'
$F = 'VRN2_HandleAll_v0122.md'
$H = 'd1f7fdcf68c6b0f790c233036a2d3b637fe185b67798c7204b10c45da9584a3d'
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
Write-Host "[GREEN] boot: Handle-All v0122 SHA-256 OK ($b)" -ForegroundColor Green
Invoke-Expression $c
}
```
