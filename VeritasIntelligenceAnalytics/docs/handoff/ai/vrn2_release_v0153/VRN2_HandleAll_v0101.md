# VRN-2 · PowerShell 7 一段碼處理全部 · VRN2_HandleAll_v0101(2026-10-30 · 套件 v0153)

v0101 = v0100(桌機 18:34 跑通:auto → verify → 收尾 BLOCKED · VRN-2 0)+ 套件 v0153(管理器 v0257)+ RoundAll v0109;auto 改成:上一輪收據不是啟動器 v0153 → 整輪(輸出冊要由管理器 v0257 重做)。

操作員 2026-10-30「GENERATE A PS CODE TO HANDLE ALL」:一段 **PowerShell 7** 碼(7.0 以上 · 例 7.6.9),貼在 PowerShell 7 視窗按 Enter,其他它自己做:

① 工具(git · python · VIA 倉)→ ② 有沒有別的 VRN-2 在跑(兩輪重疊會互搶鎖)→ ③ `Downloads` 的舊套件夾讀不讀得到(讀不到:列出來、問你要不要以系統管理員身分還原權限 · 不擋)
→ ④ 選模式(預設 auto)→ ⑤ 從 GitHub 取 `VRN2_RoundAll_v0109.py` **核對 SHA-256**(`716bfe2bd911`)→ ⑥ 執行 → ⑦ 印**收尾狀態**、各負責方的待辦、貼回包位置(收尾頁 HTML 由 RoundAll 開)。

整段包在 `& { … }` 裡,錯了用 `return` —— **視窗不會關**。不是 PowerShell 7 會印 RED 停下。cmd 裝不下這段(超過 8191 字元)→ 先開 PowerShell 7(`pwsh`)再貼。

## 貼這一行(PowerShell 7 視窗)

```powershell
& { $ErrorActionPreference = 'Continue'; $ProgressPreference = 'SilentlyContinue'; if ($PSVersionTable.PSVersion.Major -lt 7) { Write-Host '[RED] 這段要 PowerShell 7 以上(pwsh · 例 7.6.9)' -ForegroundColor Red; return }; try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch { }; $T0 = Get-Date; $R = $env:VRN2_ROOT ?? 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'; $P = 'VeritasIntelligenceAnalytics/docs/handoff/ai/vrn2_release_v0153'; $F = 'VRN2_RoundAll_v0109.py'; $H = '716bfe2bd911710d4c3ce06271404b4466f004428a10044910dab379d2884e89'; $DL = Join-Path ($env:USERPROFILE ?? $HOME) 'Downloads'; $V2 = Join-Path $R 'VIA_Reports' 'vrn2'; $Mode = "$($env:VRN2_MODE ?? 'auto')".Trim().ToLowerInvariant(); if ($Mode -notin 'auto', 'full', 'verify', 'report') { Write-Host "[RED] VRN2_MODE = $($Mode) 不認得(auto / full / verify / report)" -ForegroundColor Red; return }; Write-Host "[VRN-2] Handle-All v0101 · PowerShell $($PSVersionTable.PSVersion) · 模式 $($Mode) · VIA $($R)" -ForegroundColor Yellow; $git = (Get-Command git -ErrorAction SilentlyContinue | Select-Object -First 1).Source; if (-not $git) { Write-Host '[RED] ① 找不到 git(裝 Git for Windows 後重開 PowerShell 7)' -ForegroundColor Red; return }; $top = "$(git -C $R rev-parse --show-toplevel 2>$null)".Trim(); if (-not $top) { Write-Host "[RED] ① $($R) 不是 git 倉(先設 `$env:VRN2_ROOT = '<VIA 根>')" -ForegroundColor Red; return }; $py = $env:VRN2_PY ?? (Get-Command python, py -ErrorAction SilentlyContinue | Where-Object Source -NotMatch 'WindowsApps' | Select-Object -First 1).Source; if (-not $py) { Write-Host '[RED] ① 找不到 python(不要用 WindowsApps 的假 python · 或先設 $env:VRN2_PY)' -ForegroundColor Red; return }; Write-Host "[GREEN] ① 工具 · git 倉 $($top) · $("$(& $py --version 2>&1)".Trim())($($py))" -ForegroundColor Green; if ($IsWindows) { $busy = @(Get-CimInstance Win32_Process -Filter "Name like 'python%'" -ErrorAction SilentlyContinue | Where-Object CommandLine -Match 'ActivateVRN-2|VRN2_RoundAll'); if ($busy) { Write-Host "[YELLOW] ② 已經有 $($busy.Count) 個 VRN-2 在跑(PID $($busy.ProcessId -join ', '))· 兩輪重疊會互搶鎖、變慢" -ForegroundColor Yellow; if (($env:VRN2_YES ?? (Read-Host '    等它跑完再貼比較好;還是要繼續嗎?(y/N)')) -notmatch '^[yY]') { Write-Host '[計] 沒有繼續(視窗不會關)'; return } } else { Write-Host '[GREEN] ② 沒有別的 VRN-2 在跑' -ForegroundColor Green } }; $bad = @(Get-ChildItem -LiteralPath $DL -Directory -Filter 'VRN2_Closeout_v0*' -ErrorAction SilentlyContinue | Where-Object { $ok = $true; try { foreach ($x in @(Get-ChildItem -LiteralPath $_.FullName -File -ErrorAction Stop)) { [IO.File]::OpenRead($x.FullName).Dispose() } } catch { $ok = $false }; -not $ok }); if ($bad) { Write-Host "[YELLOW] ③ $($bad.Count) 個舊套件夾目前的身分讀不到(以前用系統管理員身分跑過 · 權限只剩 Administrators):" -ForegroundColor Yellow; $bad | ForEach-Object { Write-Host "    $($_.FullName)" }; Write-Host '    不擋:RoundAll 會改用讀得到的夾 · 套件 v0153 裝在新夾 VRN2_Closeout_v0153' -ForegroundColor DarkGray; if ($IsWindows -and (($env:VRN2_FIX_ACL ?? (Read-Host '    要用系統管理員身分把它們的權限還原成跟 Downloads 一樣嗎?會跳 UAC(y/N)')) -match '^[yY]')) { $cmd = (@($bad | ForEach-Object { "icacls '" + ($_.FullName -replace "'", "''") + "' /reset /T /C /Q" }) -join '; '); try { Start-Process -FilePath (Get-Process -Id $PID).Path -Verb RunAs -Wait -ArgumentList ('-NoProfile -EncodedCommand ' + [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($cmd))) -ErrorAction Stop; foreach ($d in $bad) { $ok = $true; try { foreach ($x in @(Get-ChildItem -LiteralPath $d.FullName -File -ErrorAction Stop)) { [IO.File]::OpenRead($x.FullName).Dispose() } } catch { $ok = $false }; Write-Host "    [$(if ($ok) { 'GREEN' } else { 'YELLOW' })] $($d.FullName) $(if ($ok) { '讀得到了' } else { '還是讀不到(不擋)' })" -ForegroundColor ($ok ? 'Green' : 'Yellow') } } catch { Write-Host "[YELLOW] ③ 沒有以系統管理員身分執行($($_.Exception.Message))· 不擋" -ForegroundColor Yellow } } } else { Write-Host '[GREEN] ③ Downloads 的 VRN-2 套件夾都讀得到' -ForegroundColor Green }; $rcp = Get-ChildItem -LiteralPath $V2 -File -Filter 'VRN2_Closeout_v0*.json' -ErrorAction SilentlyContinue | Where-Object Name -Match '^VRN2_Closeout_v\d{4}\.json$' | Sort-Object Name | Select-Object -Last 1; $last = ($rcp -and $rcp.Name -match '_v(\d{4})\.json$') ? [int]$Matches[1] : 0; $haveOut = (Test-Path -LiteralPath (Join-Path $V2 'output' 'VRN2_FinancialData_latest.json')) -and (Test-Path -LiteralPath (Join-Path $V2 'scope_in')); if ($Mode -eq 'auto') { $Mode = ($last -ge 153 -and $haveOut) ? 'verify' : 'full'; Write-Host "[計] ④ 自動選模式 $($Mode) · 上一輪收據 $($rcp.Name ?? '沒有') · 上一輪輸出冊 $($haveOut ? '有' : '沒有')$(($Mode -eq 'full' -and $last -gt 0 -and $haveOut) ? '(上一輪輸出冊是啟動器 v0153 以前做的 · 管理器 v0257 要重做輸出冊)' : '')(只重驗:先貼 `$env:VRN2_MODE = 'verify')" -ForegroundColor DarkGray }; if ($Mode -ne 'full' -and -not $haveOut) { Write-Host "[YELLOW] ④ 模式 $($Mode) 要上一輪的輸出冊 · 這裡沒有 → 改跑整輪" -ForegroundColor Yellow; $Mode = 'full' }; $ra = @(switch ($Mode) { 'verify' { '--only'; 'package,verify,report,closeout,pasteback' } 'report' { '--only'; 'report,closeout,pasteback' } }); $ra += @(($env:VRN2_ROUNDALL_ARGS ?? '') -split '\s+' | Where-Object { $_ }); $what = @{ full = '整輪(取套件 v0153 → 診斷 → 全部自測 → 跑啟動器 v0153(管理器 v0257 重做輸出冊)→ 自動修 → 除錯報告 → 收尾頁 → 貼回包 · 桌機約 66 分鐘)'; verify = '只重跑 ⑪ 獨立驗證(套件 v0153 的 IndependentVerifier v0114 · 用上一輪的輸出冊)→ 除錯報告 → 收尾頁 → 貼回包(約 10 分鐘)'; report = '只重做除錯報告 → 收尾頁 → 貼回包(用上一輪的結果 · 幾秒)' }[$Mode]; Write-Host "[計] ④ 模式 $($Mode):$($what)" -ForegroundColor Cyan; $t = Join-Path ([IO.Path]::GetTempPath()) "vrn2_handleall_$(Get-Date -Format yyyyMMdd_HHmmss)"; New-Item -ItemType Directory -Force -Path $t | Out-Null; $z = Join-Path $t 'roundall.zip'; $src = $null; foreach ($b in 'claude/optimistic-goodall-yhalc5', 'main') { foreach ($w in 0, 2, 4, 8, 16) { if ($w) { Start-Sleep -Seconds $w }; git -C $top fetch -q origin $b 2>&1 | Out-Null; if ($LASTEXITCODE -eq 0) { break } }; git -C $top archive --format=zip -o $z "origin/$($b):$($P)" $F 2>&1 | Out-Null; if ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $z)) { $src = $b; break } }; if (-not $src) { Write-Host "[RED] ⑤ 讀不到 GitHub 分支或 main 的 $($F)(網路 / git)" -ForegroundColor Red; return }; Expand-Archive -LiteralPath $z -DestinationPath $t -Force; $code = [IO.File]::ReadAllText((Join-Path $t $F), [Text.Encoding]::UTF8) -replace "`r`n", "`n"; $bytes = [Text.UTF8Encoding]::new($false).GetBytes($code); $sha = ([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash($bytes)) -replace '-', '').ToLowerInvariant(); if ($sha -ne $H) { Write-Host "[RED] ⑤ $($F) SHA-256 不對($($sha))· 不執行" -ForegroundColor Red; return }; New-Item -ItemType Directory -Force -Path $DL | Out-Null; $dst = Join-Path $DL $F; [IO.File]::WriteAllBytes($dst, $bytes); Write-Host "[GREEN] ⑤ $($F) SHA-256 $($H.Substring(0, 12)) 相符(GitHub $($src))→ $($dst)" -ForegroundColor Green; Write-Host "[計] ⑥ 執行 $($py) $($F) --root $($R) $($ra -join ' ')" -ForegroundColor DarkGray; & $py $dst --root $R @ra; $rc = $LASTEXITCODE; $cj = Join-Path $V2 'VRN2_CloseoutUI_latest.json'; if (-not (Test-Path -LiteralPath $cj) -or (Get-Item -LiteralPath $cj).LastWriteTime -lt $T0) { Write-Host "[YELLOW] ⑦ 這輪沒有寫出收尾頁($($cj))· 看上面 RoundAll 的最後幾行" -ForegroundColor Yellow } else { $c = Get-Content -LiteralPath $cj -Raw -Encoding utf8 | ConvertFrom-Json; $col = @{ OPEN = 'Red'; BLOCKED = 'Yellow'; REVIEW = 'Yellow'; DATA_GAP = 'Cyan'; PASS = 'Green' }[$c.state] ?? 'White'; Write-Host ''; Write-Host "===== 收尾 · $($c.state) · $($c.state_label) · $($c.state_text)" -ForegroundColor $col; foreach ($o in 'VRN-2', 'VCGC', '人工', '資料源') { $its = @($c.items | Where-Object owner -EQ $o); if ($its) { Write-Host "  [$($o)] $($its.Count) 項" -ForegroundColor (@{ 'VRN-2' = 'Red'; 'VCGC' = 'Yellow'; '人工' = 'Yellow'; '資料源' = 'Cyan' }[$o]); foreach ($i in $its) { $d = "$($i.detail)"; Write-Host "    · $($i.step) · $($d.Substring(0, [Math]::Min(150, $d.Length)))" } } }; $nx = @{ OPEN = '下一步:把貼回包上傳給 AI(VRN-2 要修的項目 · 出新版號修)'; BLOCKED = '下一步:VRN-2 側已結案 · 剩下是 VCGC 的決定 / 安裝(上面 [VCGC] 那幾項 · 例:MOPS 經 VIA 網路工具被 DENY)→ 交 VCGC,VRN-2 不繞道'; REVIEW = '下一步:VRN-2 側已結案 · 打開收尾頁看「人工核對」那幾項的原 PDF'; DATA_GAP = '下一步:VRN-2 側已結案 · 剩外部來源本來沒有的(已附證據)'; PASS = '全綠 · 結案' }[$c.state]; Write-Host "  $($nx)" -ForegroundColor $col; Write-Host '  BLOCKED / REVIEW / DATA_GAP 都不是成功;VCGC 的 closeout_lamp 才是 VCGC 驗收(四系統對等 · 只讀互看)' -ForegroundColor DarkGray; Write-Host "  收尾頁 $(Join-Path $V2 'VRN2_CloseoutUI_latest.html')"; $pb = @($c.links | Where-Object { "$($_.label)" -like '貼回包*' } | Select-Object -First 1).path; if ($pb -and (Test-Path -LiteralPath $pb)) { Write-Host "  貼回包 $($pb)(上傳給 AI)" -ForegroundColor Green } }; Write-Host "[計] Handle-All 結束 · RoundAll 結束碼 $($rc) · $([int]((Get-Date) - $T0).TotalSeconds) 秒(視窗不會關)" }
```

一行版 SHA-256 `c4374130f9f6`(UTF-8 · 不含結尾換行)· 下面「可讀版」是同一段碼(語法樹逐詞相同,只差換行 / 分號)。

## 模式(預設 auto)

| 模式 | 怎麼指定 | 做什麼 | 桌機時間 |
|---|---|---|---|
| `auto` | (不用設) | 上一輪的收據是啟動器 **v0153**、而且輸出冊在 → `verify`;不然 → `full`(管理器 v0257 要重做輸出冊) | — |
| `full` | `$env:VRN2_MODE = 'full'` | 整輪:取套件 v0153 → 診斷 → 全部自測 → 跑啟動器 v0153(管理器 v0257)→ 自動修 → 除錯報告 → 收尾頁 → 貼回包 | 約 66 分鐘 |
| `verify` | `$env:VRN2_MODE = 'verify'` | 取套件 v0153 → **只重跑 ⑪ 獨立驗證**(IndependentVerifier v0114 · 上一輪的輸出冊)→ 收據 ⑪ 換成這次結果(先備份)→ 除錯報告 → 收尾頁 → 貼回包 | 約 10 分鐘 |
| `report` | `$env:VRN2_MODE = 'report'` | 只重做除錯報告 → 收尾頁 → 貼回包(上一輪的結果) | 幾秒 |

先在同一個視窗貼 `$env:VRN2_MODE = 'full'` 再貼那一行;用完 `Remove-Item Env:VRN2_MODE`。要用的模式需要上一輪輸出冊、但沒有 → 自動改跑整輪。

## 這次桌機(2026-10-30 18:34 之後)貼下去會怎樣

上一輪收據是 `VRN2_Closeout_v0151.json`(啟動器 v0151 做的輸出冊)→ auto 選 **full**(整輪 · 桌機約 66 分鐘):
套件 v0153 從 GitHub 取、裝到新夾 `Downloads\VRN2_Closeout_v0153` → 啟動器 v0153 用管理器 **v0257** 重做輸出冊 →
`6933_AMAX-KY_個股介紹報告.pdf` 第 8 頁並排兩張表:右表的值不再掛在左表科目下(同一列找得到右表科目名 → 改名 · 找不到 → 移剔除冊帶理由)·
凱基 2891 第 5 頁 8 筆沒有列號的同鍵兩值 → 移剔除冊 → ⑪ 驗證器的 DUPKEY 應該從 45 變 0。
收尾頁同一件事只列一次:18:34 那 14 列用 v0109 的規則重算 = **BLOCKED · VCGC 1 · 人工 3 · 資料源 2**(整輪後以桌機收尾頁為準;DUPKEY 還在就是 OPEN · VRN-2 1)。
容器裡用同樣的流程試過 auto(full / verify)與 report,結果在 `VRN2_Verification_v0153.md`。

## 環境變數(都可不設)

| 變數 | 用途 |
|---|---|
| `$env:VRN2_ROOT` | VIA 根(預設 `C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics`) |
| `$env:VRN2_PY` | 指定 python(預設找 `python` / `py`,不用 WindowsApps 的假 python) |
| `$env:VRN2_MODE` | `auto` · `full` · `verify` · `report` |
| `$env:VRN2_ROUNDALL_ARGS` | 多帶給 RoundAll 的參數(例 `'--integrate yes'`、`'--no-open'`) |
| `$env:VRN2_YES` | ② 有別的 VRN-2 在跑時不問、直接回答(`y` 繼續 · `n` 停) |
| `$env:VRN2_FIX_ACL` | ③ 舊套件夾讀不到時不問、直接回答(`y` 以系統管理員身分 `icacls /reset` · `n` 不動) |
| `$env:VRN2_NO_UI` | `1` = 跑完不開收尾頁 |

## 每一步

| 步 | 做什麼 | 不過時 |
|---|---|---|
| ① | `git` 在 · `$env:VRN2_ROOT` 是 git 倉 · 找得到真的 python | RED 停(說缺什麼) |
| ② | (Windows)找命令列有 `ActivateVRN-2` / `VRN2_RoundAll` 的 python | YELLOW · 問要不要繼續(預設不繼續) |
| ③ | `Downloads\VRN2_Closeout_v0*` 每個夾的檔都開得起來嗎 | YELLOW 列出來 · 不擋;你答 y 才跳 UAC 跑 `icacls "<夾>" /reset /T /C /Q`(只還原成跟 Downloads 一樣的繼承權限 · 不刪檔)· 跑完再測一次 |
| ④ | 選模式(上表) | — |
| ⑤ | `git fetch` 分支 `claude/optimistic-goodall-yhalc5`(讀不到 → `main`)→ `git archive` 取 `vrn2_release_v0153/VRN2_RoundAll_v0109.py` → 換行統一成 LF 後算 SHA-256 → 相符才存到 `Downloads` | RED 停 · 不執行 |
| ⑥ | `python VRN2_RoundAll_v0109.py --root <VIA> <模式參數>`(RoundAll 自己取套件 v0153 並核對 `4beed2bc7a84`、跑、寫收尾頁與貼回包) | RoundAll 每一步都包起來 · 出例外那步記紅、其他照跑 |
| ⑦ | 讀這輪的 `VIA_Reports\vrn2\VRN2_CloseoutUI_latest.json` → 狀態 + 綠黃紅灰 + 各負責方的項目 + 下一步 + 貼回包 | 這輪沒寫出收尾頁 → YELLOW(看 RoundAll 最後幾行) |

**收尾狀態**:OPEN = VRN-2 還有要修的(貼回包給 AI)· BLOCKED = VRN-2 側結案、剩 VCGC 的決定 · REVIEW = 剩要人看原文的 · DATA_GAP = 剩外部來源本來沒有的(已附證據)· PASS = 全綠。
**BLOCKED / REVIEW / DATA_GAP 都不是成功**;VCGC 的 `closeout_lamp` 才是 VCGC 驗收(四系統對等 · 只讀互看)。

## 程式碼決定不了的(收尾頁會分好)

- **交 VCGC**:⑥e MOPS 財報 —— VIA 鎖版網路工具的合規層拒絕(DENY),VRN-2 / VDF 不繞道;在那之前 ⑬b 是「無歷史」。
- **人工核對**:MQ-1560 影像頁 OCR 摘錄對原圖(基本資料 2 · 四點 5)· 凱基 6147 分析師名從 Email 帳號推算(EST 1)· 年度數據缺項 3 份(原文真的沒有年度表就是沒有)。
- **資料源沒有**:GFHK Apple(代號 AAPL,不是台股)沒有台股市場資料 · 神達 3706 / 緯穎 6669 五份報告的報告日前一週沒有還原價(那幾個日線視窗 VDF 引擎回 PARTIAL)· 鉅亨沒有 FactSet 頁(404)。
- 舊套件夾權限:只有你答 y 才動(UAC);不動也不擋。

## 可讀版(跟一行版同一段碼)

```powershell
& {
$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'
if ($PSVersionTable.PSVersion.Major -lt 7) { Write-Host '[RED] 這段要 PowerShell 7 以上(pwsh · 例 7.6.9)' -ForegroundColor Red; return }
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch { }
$T0 = Get-Date
$R = $env:VRN2_ROOT ?? 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
$P = 'VeritasIntelligenceAnalytics/docs/handoff/ai/vrn2_release_v0153'
$F = 'VRN2_RoundAll_v0109.py'
$H = '716bfe2bd911710d4c3ce06271404b4466f004428a10044910dab379d2884e89'
$DL = Join-Path ($env:USERPROFILE ?? $HOME) 'Downloads'
$V2 = Join-Path $R 'VIA_Reports' 'vrn2'
$Mode = "$($env:VRN2_MODE ?? 'auto')".Trim().ToLowerInvariant()
if ($Mode -notin 'auto', 'full', 'verify', 'report') { Write-Host "[RED] VRN2_MODE = $($Mode) 不認得(auto / full / verify / report)" -ForegroundColor Red; return }
Write-Host "[VRN-2] Handle-All v0101 · PowerShell $($PSVersionTable.PSVersion) · 模式 $($Mode) · VIA $($R)" -ForegroundColor Yellow
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
Write-Host '    不擋:RoundAll 會改用讀得到的夾 · 套件 v0153 裝在新夾 VRN2_Closeout_v0153' -ForegroundColor DarkGray
if ($IsWindows -and (($env:VRN2_FIX_ACL ?? (Read-Host '    要用系統管理員身分把它們的權限還原成跟 Downloads 一樣嗎?會跳 UAC(y/N)')) -match '^[yY]')) {
$cmd = (@($bad | ForEach-Object { "icacls '" + ($_.FullName -replace "'", "''") + "' /reset /T /C /Q" }) -join '; ')
try { Start-Process -FilePath (Get-Process -Id $PID).Path -Verb RunAs -Wait -ArgumentList ('-NoProfile -EncodedCommand ' + [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($cmd))) -ErrorAction Stop; foreach ($d in $bad) { $ok = $true; try { foreach ($x in @(Get-ChildItem -LiteralPath $d.FullName -File -ErrorAction Stop)) { [IO.File]::OpenRead($x.FullName).Dispose() } } catch { $ok = $false }; Write-Host "    [$(if ($ok) { 'GREEN' } else { 'YELLOW' })] $($d.FullName) $(if ($ok) { '讀得到了' } else { '還是讀不到(不擋)' })" -ForegroundColor ($ok ? 'Green' : 'Yellow') } } catch { Write-Host "[YELLOW] ③ 沒有以系統管理員身分執行($($_.Exception.Message))· 不擋" -ForegroundColor Yellow }
}
} else { Write-Host '[GREEN] ③ Downloads 的 VRN-2 套件夾都讀得到' -ForegroundColor Green }
$rcp = Get-ChildItem -LiteralPath $V2 -File -Filter 'VRN2_Closeout_v0*.json' -ErrorAction SilentlyContinue | Where-Object Name -Match '^VRN2_Closeout_v\d{4}\.json$' | Sort-Object Name | Select-Object -Last 1
$last = ($rcp -and $rcp.Name -match '_v(\d{4})\.json$') ? [int]$Matches[1] : 0
$haveOut = (Test-Path -LiteralPath (Join-Path $V2 'output' 'VRN2_FinancialData_latest.json')) -and (Test-Path -LiteralPath (Join-Path $V2 'scope_in'))
if ($Mode -eq 'auto') { $Mode = ($last -ge 153 -and $haveOut) ? 'verify' : 'full'; Write-Host "[計] ④ 自動選模式 $($Mode) · 上一輪收據 $($rcp.Name ?? '沒有') · 上一輪輸出冊 $($haveOut ? '有' : '沒有')$(($Mode -eq 'full' -and $last -gt 0 -and $haveOut) ? '(上一輪輸出冊是啟動器 v0153 以前做的 · 管理器 v0257 要重做輸出冊)' : '')(只重驗:先貼 `$env:VRN2_MODE = 'verify')" -ForegroundColor DarkGray }
if ($Mode -ne 'full' -and -not $haveOut) { Write-Host "[YELLOW] ④ 模式 $($Mode) 要上一輪的輸出冊 · 這裡沒有 → 改跑整輪" -ForegroundColor Yellow; $Mode = 'full' }
$ra = @(switch ($Mode) { 'verify' { '--only'; 'package,verify,report,closeout,pasteback' } 'report' { '--only'; 'report,closeout,pasteback' } })
$ra += @(($env:VRN2_ROUNDALL_ARGS ?? '') -split '\s+' | Where-Object { $_ })
$what = @{ full = '整輪(取套件 v0153 → 診斷 → 全部自測 → 跑啟動器 v0153(管理器 v0257 重做輸出冊)→ 自動修 → 除錯報告 → 收尾頁 → 貼回包 · 桌機約 66 分鐘)'; verify = '只重跑 ⑪ 獨立驗證(套件 v0153 的 IndependentVerifier v0114 · 用上一輪的輸出冊)→ 除錯報告 → 收尾頁 → 貼回包(約 10 分鐘)'; report = '只重做除錯報告 → 收尾頁 → 貼回包(用上一輪的結果 · 幾秒)' }[$Mode]
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
