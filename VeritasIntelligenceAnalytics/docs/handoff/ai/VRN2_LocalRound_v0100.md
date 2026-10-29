# VRN-2 本地實測一輪 v0100(一段 PowerShell 貼上:logo → 補船 → 跑 v0147(開 Workbench)→ 打包貼回材料)

操作員令(2026-10-28):「回到電腦本地實測修正」→「generate a ps code to handle all above」。
雲端工作階段碰不到桌機(Remote Control 只接 Mac / Linux),所以本地實測由這一段在桌機跑完,把要貼回的東西打包成一個 zip,上傳給 AI 接著修。

> **2026-10-29 v0147 改指(操作員「generate a py code to handle all above and fix all test all debug all」):** 本段現在指 操作員一鍵 **v0108** → VRN-2 一鍵 **v0147**(長線 Parquet 庫收 Combined / FinancialAligned / Deleted 並補缺 · ⑬b 在 ⑬ 前 · 舊資料庫掃描限深 + 只問像 VRN-2 的檔 · ⑥e 用擷取 Python · 自測從 runtime zip 取模組)。另有一支 Python **`vrn2_release_v0147/VRN2_RoundAll_v0100.py`** 跑全流程(取套件 → 診斷 → 全部自測 → 跑 → 自動修 → 除錯 → 貼回包 · 用法見同夾 `VRN2_RoundAll_v0100.md`);本段 ④ 貼回包多收 `VRN2_RoundAll_latest.json`。
> **2026-10-29 v0146 改指(桌機 10:25 實跑 v0145 貼回:2546 秒 · CPU 被佔 87.5% → 1 路 · 冪等閘並行有效 · ⑬ duckdb 綠;操作員 U/I 與資料需求 + 上傳共識引擎 v0120):** 本段當時指 操作員一鍵 **v0107** → VRN-2 一鍵 **v0146**(Workbench v0102:雙語表頭 · 靠上 · 百萬台幣千分位 · 自動縮放 · 左欄輸出夾 · 右欄去重矩陣 + 引擎狀態 · logo 180%;⑥e 市場擷取(借共用 MarketFetch)· ⑥f 共識 Combined(FactSet / YFinance 中位數 · 真實年度 EPS / PER)· ⑬b 歷史對齊 · ⑬c 舊資料庫整合;其餘同 v0145)。④ 貼回包多收 `VRN2_HistoryAlign_latest.json` · `VRN2_Integrate_latest.json` · `market\VRN2_Market_latest.json` · `consensus\VRN2_Consensus_latest.json` · `output\VRN2_Combined_latest.csv`。
> **2026-10-29 v0145 改指(桌機 08:14 實跑 v0144 貼回:前後端已連結 · 2422 秒慢在 ⑦ 冪等閘序跑約 1050 秒無輸出;操作員問「是第一次啟動還是加速器沒作用」→ 都不是):** 本段當時指 操作員一鍵 **v0106** → VRN-2 一鍵 **v0145**(管理器 v0255:冪等閘每波 3 份並行 · 30 秒心跳 · 階段計時 `VRN2_Phase_Timing_latest.json`;其餘同 v0144)。④ 貼回包改收 `VRN2_Closeout_v0145.json` 與 `VRN2_Phase_Timing_latest.json`,不再把前一版收據與(跑完本來就會移除的)鎖檔算成「缺」。
> **2026-10-29 v0144 改指(操作員:「先把這兩天有更新的部分抓下來再 PC 測試 · 先不要讓 GitHub 影響 · 這是獨立系統」):** 本段當時指 操作員一鍵 **v0105** → VRN-2 一鍵 **v0144**(⑤b SSOT-ID 核號同步 · ⑬ 輸出位置 / DuckDB 增量庫 · 處理器 v0108 · Workbench v0101)。GitHub 只當 git 遠端用來**抓**這兩天更新的檔(`git fetch` + `git archive`,逐檔 SHA-256 核對);CI 紅綠不影響本機實測。只測不推:先設 `$env:VRN_ROUND_NO_SHIP = '1'`(② 不補船、不 commit、不 push;套件啟動器 ⑨ 本來就只驗證不推),再貼頂端那一行。
> **2026-10-29 第一次桌機實跑(01:33 · 7305 秒)貼回後本段改指:** ChainShip **v0101**(缺的環先在本機別處找)· 操作員一鍵 **v0104** → VRN-2 一鍵 **v0143**(單機閘 · 子行程上限加寬 · ⑫b 補放)· ① 印章改找 `OneDrive\Pictures\seal-logo-square.png`。那一輪的結果:① 黃(當時沒指定印章檔)· ② 紅(ship 後仍缺 v0248 / v0253 → v0101 的 recover)· ③ 紅(同一 VIA 根兩個啟動器重疊 → RAM 0.16 GB → ⑦ / ⑪ / ⑫b 逾時 → ⑤b 紅;⑧ 其實完成 紅 0 黃 4 · 冪等 GREEN · 四點原文 PASS 203 FAIL 1)· ④ 綠(13 收據 + 7 PDF)。

做的事(每步有燈,任一步紅不擋下一步,最後總結):

| 步 | 做什麼 | 開關 |
|---|---|---|
| ① logo | 找印章圖:`$env:VRN2_LOGO` 指定的檔 → `OneDrive\Pictures\seal-logo-square.png`(操作員 2026-10-28 指定)→ `Downloads` / `Desktop` / `Pictures` / `OneDrive\Pictures` 裡的 `VRN2_Logo.(png|jpg|jpeg|webp)` → 複製到 `<VIA>\functional modules\VRN\SSOT\VRN2_Logo.<副檔名>`(Workbench 渲染時自動去白底;沒找到就用範本「理」字,不擋) | `$env:VRN2_LOGO = 'C:\...\seal.png'` |
| ② 補船 | 從 GitHub 讀 `VRN2_ChainShip_v0101.md` 的程式碼(核對 SHA-256)→ 綁到本輪的倉(`$REPO` ← VIA 根所在的 git 倉;結束碼 = 它的綜合燈,push 被拒 = 黃)→ 執行:`check` → `ship --commit --push`(**v0101:先 recover** —— 缺的 v0248 / v0253 / SSOT 冊在 VIA 樹、`functional modules\VRN2`、備份夾、`Downloads\VRN2_*` 夾與 zip 裡找同名檔,內容唯一就複製進 VRN 夾再推;兩份不同內容只列 `[FIND?]`)→ `check` | `$env:VRN_ROUND_NO_SHIP = '1'` 跳過 |
| ③ 跑 | 從 GitHub 讀操作員一鍵 `VRN1_VRN2_OneClick_v0108.md` 的程式碼(核對 SHA-256)→ 執行(預設只跑 VRN-2:**v0147 套件**(啟動器 v0147 → 長線庫收新冊並補缺 · ⑬b 在 ⑬ 前 · 整合掃描限深;v0146 的 Workbench v0102 · ⑥e 市場擷取 · ⑥f 共識 Combined · ⑬b 歷史對齊 · ⑬c 舊資料庫整合;v0145 的管理器 v0255:冪等閘每波 3 份並行 · 30 秒心跳 · 階段計時;v0144 的 ⑤b SSOT-ID 核號同步 · ⑬ 輸出位置 / DuckDB 增量庫 · 處理器 v0108(v0105 / v0107 是桌機線的號)· Workbench v0101 與 v0143 的單機閘 / 上限 / ⑫b 補放照舊;可先 `$env:VRN2_OUTPUT_DIR = 'C:\Users\tonyk\OneDrive\VRN2_out'` 預設輸出夾,或之後在 Workbench 按「選擇輸出夾…」)→ ①~⑫ → 四點原文核對 → **Workbench 自動開**;VRN-1 那段跳過) | `$env:VRN_ROUND_WITH_VRN1 = '1'` 連 VRN-1 一起跑 · `$env:VRN2_SOURCE` 來源夾(預設 `C:\測試樣本報告`) |
| ④ 打包 | `Downloads\VRN2_PasteBack_<時間>.zip`:整段逐字稿(transcript)· 最後 300 行貼包 · `VRN2_Closeout_v0147.json` · `VRN2_RoundAll_latest.json` · `VRN2_HistoryAlign_latest.json` · `VRN2_Integrate_latest.json` · `market\VRN2_Market_latest.json` · `consensus\VRN2_Consensus_latest.json` · `VRN2_Phase_Timing_latest.json` · `VRN2_OutputStore_latest.json` · `IDEMPOTENCE_latest.json` · `VRN2_VerbatimVerify_latest.json` · `VRN2_Completion_latest.json` · `VRN2_Workbench_latest.html` · 四本輸出冊 csv · 最新的 `verify_independent\*.digest.txt` · 補船收據 · **來源夾裡這五份報告的 PDF**(神達 3706 兆豐訪談速報 · GFHK Apple update · 欣銓 3264 · 6933 AMAX · 凱基 2891)→ 上傳這個 zip 給 AI 就夠 | `$env:VRN_ROUND_NO_PDF = '1'` 不裝 PDF |

## 一行啟動(桌機 PowerShell 貼這一行就好;從 GitHub 分支讀本檔的程式碼區塊再執行,不必複製整段)

```text
& { $r = if ($env:VRN2_REPO) { $env:VRN2_REPO } else { 'C:\Users\tonyk\OneDrive\Documents\movies-dataset' }; $b = 'claude/optimistic-goodall-yhalc5'; $t = Join-Path ([IO.Path]::GetTempPath()) 'vrn2_round_boot'; New-Item -ItemType Directory -Force -Path $t | Out-Null; git -C $r fetch -q origin $b; git -C $r archive --format=zip -o (Join-Path $t 'doc.zip') ('origin/' + $b + ':VeritasIntelligenceAnalytics/docs/handoff/ai') VRN2_LocalRound_v0100.md; if ($LASTEXITCODE -ne 0) { Write-Host "[RED] 讀不到 GitHub 分支 $b 的 VRN2_LocalRound_v0100.md(倉 $r · 網路 / git)" -ForegroundColor Red; return }; Expand-Archive -LiteralPath (Join-Path $t 'doc.zip') -DestinationPath $t -Force; $m = [IO.File]::ReadAllText((Join-Path $t 'VRN2_LocalRound_v0100.md'), [Text.Encoding]::UTF8) -replace "`r`n", "`n"; $c = [regex]::Match($m, '(?s)```powershell\n(.*?)\n```').Groups[1].Value; Write-Host ("[啟動] VRN2_LocalRound_v0100 · {0} 行 · 自 origin/{1}" -f ($c -split "`n").Count, $b) -ForegroundColor Yellow; & ([scriptblock]::Create($c)) }
```

倉不在預設路徑就先 `$env:VRN2_REPO = 'D:\...\movies-dataset'`;乾跑先加 `$env:VRN_ROUND_DRY = '1'`。整段程式碼(同一份,下面)供人讀與核對:

```powershell
& {
  # ===== VRN-2 本地實測一輪 v0100(2026-10-28 · 操作員「回到電腦本地實測修正」「generate a ps code to handle all above」)=====
  $ErrorActionPreference = 'Continue'
  try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch { }
  $R   = if ($env:VRN2_ROOT) { $env:VRN2_ROOT } else { 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics' }
  $Br  = 'claude/optimistic-goodall-yhalc5'
  $SRC = if ($env:VRN2_SOURCE) { $env:VRN2_SOURCE } else { 'C:\測試樣本報告' }
  $H_OP = 'ecb2176c2e622e45adb275e178fd67025b6b6943381e8700378cd14c69f3b39b'   # 操作員一鍵 v0108 程式碼 SHA-256(VRN1_VRN2_OneClick_v0108.md powershell 區塊 · ② 指 VRN-2 一鍵 v0147)
  $H_CS = '78ef9852c1dc1a902f342f10d7a0b37e03531ae34c72a7010dd350a85607bcd6'   # VRN2_ChainShip_v0101.md §3 程式碼 SHA-256(ship 先 recover:缺的環在本機別處找)
  $PDFS = @('3706', 'GFHK', '3264', '6933', '2891')                             # 要裝進貼回包的五份(檔名含這些字)
  $t0 = Get-Date; $stamp = $t0.ToString('yyyyMMdd_HHmmss')
  $Dl = Join-Path $env:USERPROFILE 'Downloads'; $out = Join-Path $Dl ('VRN2_PasteBack_' + $stamp); New-Item -ItemType Directory -Force -Path $out | Out-Null
  $log = Join-Path $out 'transcript.txt'; try { Start-Transcript -LiteralPath $log -Force | Out-Null } catch { }
  $res = [ordered]@{}; $col = @{ GREEN = 'Green'; YELLOW = 'Yellow'; RED = 'Red'; GRAY = 'DarkGray' }
  function Say([string]$k, [string]$lamp, [string]$msg) { $res[$k] = @($lamp, $msg); Write-Host ("[{0}] {1} · {2}" -f $lamp, $k, $msg) -ForegroundColor $col[$lamp] }
  function Sha([string]$s) { -join ([Security.Cryptography.SHA256]::Create().ComputeHash([Text.Encoding]::UTF8.GetBytes($s)) | ForEach-Object { $_.ToString('x2') }) }
  function FetchCode([string]$rel, [string]$name, [string]$want) {   # 從 GitHub 分支(讀不到 → main)讀 md 的 powershell 區塊 · 核對 SHA-256 · 回程式碼或 $null
    $top = "$(git -C $R rev-parse --show-toplevel 2>$null)".Trim(); if (-not $top) { Write-Host "  [RED] $R 不是 git 倉或找不到 git" -ForegroundColor Red; return $null }
    $tmp = Join-Path ([IO.Path]::GetTempPath()) ('vrn2_round_' + $stamp + '_' + [IO.Path]::GetFileNameWithoutExtension($name)); New-Item -ItemType Directory -Force -Path $tmp | Out-Null
    $z = Join-Path $tmp 'doc.zip'; $src = ''
    foreach ($b in $Br, 'main') {
      foreach ($w in 0, 2, 4, 8, 16) { if ($w) { Start-Sleep -Seconds $w }; git -C $top fetch -q origin $b 2>&1 | Out-Null; if ($LASTEXITCODE -eq 0) { break } }
      git -C $top archive --format=zip -o $z ('origin/' + $b + ':' + $rel) $name 2>&1 | Out-Null
      if ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $z)) { $src = $b; break }
    }
    if (-not $src) { Write-Host "  [RED] 讀不到 GitHub 分支 $Br 或 main 的 $name(網路 / git)" -ForegroundColor Red; return $null }
    Expand-Archive -LiteralPath $z -DestinationPath $tmp -Force
    $md = [IO.File]::ReadAllText((Join-Path $tmp $name), [Text.Encoding]::UTF8) -replace "`r`n", "`n"
    $code = [regex]::Match($md, '(?s)```powershell\n(.*?)\n```').Groups[1].Value
    $sha = Sha $code
    if ($sha -ne $want) { Write-Host ("  [RED] {0} 程式碼 SHA-256 不對({1} ≠ {2})· 不執行(GitHub 上的版本換了 → 重新取得本段)" -f $name, $sha.Substring(0, 12), $want.Substring(0, 12)) -ForegroundColor Red; return $null }
    Write-Host ("  [計] {0} 程式碼 SHA-256 {1} 相符(GitHub {2})" -f $name, $sha.Substring(0, 12), $src) -ForegroundColor DarkGray
    return $code
  }
  function BindChainShip([string]$c) {   # 雜湊相符後再綁(Codex #571 P1/P2):$REPO ← $R 所在的倉 · 早退與綜合燈都寫進 $global:LASTEXITCODE(0 綠 · 2 黃 · 1 紅)
    $top = "$(git -C $R rev-parse --show-toplevel 2>$null)".Trim(); if (-not $top) { Write-Host "  [RED] $R 不在 git 倉內 · ChainShip 不執行" -ForegroundColor Red; return $null }
    if ($top -notmatch '^/') { $top = $top -replace '/', '\' }
    $mRepo = [regex]::Match($c, '(?m)^[ \t]*\$REPO = "[^"\n]*"[ \t]*$'); $nRepo = [regex]::Matches($c, '(?m)^[ \t]*\$REPO = "[^"\n]*"[ \t]*$').Count
    $nRet = [regex]::Matches($c, '; return \}').Count
    $mLamp = [regex]::Match($c, '(?m)^([ \t]*)\$lamp = if .*$'); $nLamp = [regex]::Matches($c, '(?m)^[ \t]*\$lamp = if .*$').Count
    if ($nRepo -ne 1 -or $nRet -ne 4 -or $nLamp -ne 1) { Write-Host ("  [RED] ChainShip 程式碼結構不如預期(REPO {0} · return {1} · lamp {2};要 1 · 4 · 1)· 不執行" -f $nRepo, $nRet, $nLamp) -ForegroundColor Red; return $null }
    $q = [regex]::Match($mRepo.Value, '"[^"]*"').Value
    $c = $c.Replace($mRepo.Value, $mRepo.Value.Replace($q, '"' + $top + '"'))
    $c = $c.Replace('; return }', '; $global:LASTEXITCODE = 1; return }')
    $c = $c.Replace($mLamp.Value, $mLamp.Value + "`n" + $mLamp.Groups[1].Value + '$global:LASTEXITCODE = @{ GREEN = 0; YELLOW = 2; RED = 1 }[$lamp]')
    Write-Host ("  [綁] ChainShip 倉 {0} · 結束碼 = 綜合燈" -f $top) -ForegroundColor DarkGray
    return $c
  }
  $dry = ($env:VRN_ROUND_DRY -eq '1')
  Write-Host ("[VRN-2 本地實測一輪 v0100] VIA 根 {0} · 來源 {1} · 貼回包 {2}{3}" -f $R, $SRC, $out, $(if ($dry) { ' · 乾跑(不執行子段)' } else { '' })) -ForegroundColor Yellow
  if (-not (Test-Path -LiteralPath $R)) { Say '⓪ VIA 根' RED "找不到 $R · 設 `$env:VRN2_ROOT 後再貼" } else { Say '⓪ VIA 根' GREEN $R }

  # ① logo:找圖 → 放到 SSOT(渲染時自動去白底)
  $k1 = '① logo'
  $cands = @(); if ($env:VRN2_LOGO) { $cands += $env:VRN2_LOGO }
  $cands += (Join-Path $env:USERPROFILE 'OneDrive\Pictures\seal-logo-square.png')   # 操作員 2026-10-28 指定的印章檔
  foreach ($d in (Join-Path $env:USERPROFILE 'Downloads'), (Join-Path $env:USERPROFILE 'Desktop'), (Join-Path $env:USERPROFILE 'OneDrive\Desktop'), (Join-Path $env:USERPROFILE 'Pictures'), (Join-Path $env:USERPROFILE 'OneDrive\Pictures')) { foreach ($e in 'png', 'jpg', 'jpeg', 'webp') { $cands += (Join-Path $d ('VRN2_Logo.' + $e)) } }
  $logo = $cands | Where-Object { $_ -and (Test-Path -LiteralPath $_ -PathType Leaf) } | Select-Object -First 1
  $ssot = Join-Path $R 'functional modules\VRN\SSOT'
  $have = Get-ChildItem -LiteralPath $ssot -Filter 'VRN2_Logo.*' -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($logo) {
    New-Item -ItemType Directory -Force -Path $ssot | Out-Null
    $dst = Join-Path $ssot ('VRN2_Logo' + [IO.Path]::GetExtension($logo).ToLower())
    if ($dry) { Say $k1 GREEN "乾跑:會把 $logo 複製到 $dst" }
    else { Copy-Item -LiteralPath $logo -Destination $dst -Force; Say $k1 GREEN "$logo → $dst(Workbench 渲染時自動去白底 · 無框無特效)" }
  } elseif ($have) { Say $k1 GREEN "SSOT 已有 $($have.Name) · 沿用" }
  else { Say $k1 YELLOW "沒找到印章圖(`$env:VRN2_LOGO 或 Downloads / Desktop / Pictures 的 VRN2_Logo.png|jpg)· Workbench 先用範本「理」字 · 之後放了再跑一次即可" }

  # ② 補船:VRN2_ChainShip check → ship --commit --push → check
  $k2 = '② 補船 ChainShip'
  if ($env:VRN_ROUND_NO_SHIP -eq '1') { Say $k2 GRAY '跳過(VRN_ROUND_NO_SHIP=1)' }
  else {
    $code = FetchCode 'VeritasIntelligenceAnalytics/docs/handoff/ai' 'VRN2_ChainShip_v0101.md' $H_CS
    if ($code) { $code = BindChainShip $code }
    if (-not $code) { Say $k2 RED '取不到、雜湊不符或結構不如預期 · 沒跑' }
    elseif ($dry) { Say $k2 GREEN '乾跑:程式碼已核對,不執行' }
    else {
      $global:LASTEXITCODE = 1
      try { & ([scriptblock]::Create($code)) } catch { Write-Host ('  [RED] 補船中斷:' + $_.Exception.Message) -ForegroundColor Red; $global:LASTEXITCODE = 1 }
      $rc2 = [int]$global:LASTEXITCODE
      $rcp = Join-Path $R 'VIA_Reports\vrn2\VRN2_ChainShip_latest.json'
      Say $k2 $(if ($rc2 -eq 0) { 'GREEN' } elseif ($rc2 -eq 2) { 'YELLOW' } else { 'RED' }) ("rc {0} · 收據 {1}" -f $rc2, $(if (Test-Path -LiteralPath $rcp) { $rcp } else { '(沒寫出)' }))
    }
  }

  # ③ 跑:操作員一鍵 v0103(→ VRN-2 一鍵 v0142 → 套件 → 全流程 → Workbench)
  $k3 = '③ 跑 VRN-2 v0147'
  $code = FetchCode 'VeritasIntelligenceAnalytics/docs/handoff/ai/vrn1_vrn2_oneclick_v0108' 'VRN1_VRN2_OneClick_v0108.md' $H_OP
  if (-not $code) { Say $k3 RED '取不到或雜湊不符 · 沒跑' }
  elseif ($dry) { Say $k3 GREEN '乾跑:程式碼已核對,不執行' }
  else {
    if (Test-Path -LiteralPath $SRC -PathType Container) { $env:VRN2_SOURCE = $SRC } else { Write-Host "  [YELLOW] 來源夾 $SRC 不在 · 一鍵用上次 U/I 選的輸入" -ForegroundColor Yellow }
    $skip0 = $env:VRN_PAIR_SKIP; if ($env:VRN_ROUND_WITH_VRN1 -ne '1') { $env:VRN_PAIR_SKIP = 'VRN-1' }
    $global:LASTEXITCODE = 1
    try { & ([scriptblock]::Create($code)) } catch { Write-Host ('  [RED] 一鍵中斷:' + $_.Exception.Message) -ForegroundColor Red; $global:LASTEXITCODE = 1 }
    $rc3 = [int]$global:LASTEXITCODE
    if ($null -ne $skip0) { $env:VRN_PAIR_SKIP = $skip0 } else { Remove-Item Env:\VRN_PAIR_SKIP -ErrorAction SilentlyContinue }
    Say $k3 $(if ($rc3 -eq 0) { 'GREEN' } elseif ($rc3 -eq 2) { 'YELLOW' } else { 'RED' }) ("結束碼 {0}(0 綠 · 2 黃:待核對 · 1 紅)" -f $rc3)
  }

  # ④ 打包貼回材料
  $k4 = '④ 貼回包'
  $v2 = Join-Path $R 'VIA_Reports\vrn2'; $n = 0; $miss = @()
  foreach ($rel in 'VRN2_Closeout_v0147.json', 'VRN2_RoundAll_latest.json', 'VRN2_HistoryAlign_latest.json', 'VRN2_Integrate_latest.json', 'market\VRN2_Market_latest.json', 'consensus\VRN2_Consensus_latest.json', 'output\VRN2_Combined_latest.csv', 'VRN2_Phase_Timing_latest.json', 'VRN2_OutputStore_latest.json', 'VRN2_Output_Config.json', 'IDEMPOTENCE_latest.json', 'VRN2_VerbatimVerify_latest.json', 'VRN2_Completion_latest.json', 'VRN2_Activate_latest.json', 'VRN2_Input_latest.json', 'VRN2_ChainShip_latest.json', 'VRN2_Workbench_latest.html', 'output\VRN2_Summary_latest.csv', 'output\VRN2_BasicInfo_latest.csv', 'output\VRN2_Rejected_latest.csv', 'output\VRN2_FinancialData_latest.csv') {
    $p = Join-Path $v2 $rel; if (Test-Path -LiteralPath $p) { Copy-Item -LiteralPath $p -Destination (Join-Path $out ($rel -replace '\\', '_')) -Force; $n++ } else { $miss += $rel }
  }
  $dg = Get-ChildItem -LiteralPath (Join-Path $v2 'verify_independent') -Filter '*.digest.txt' -ErrorAction SilentlyContinue | Sort-Object LastWriteTime | Select-Object -Last 1
  if ($dg) { Copy-Item -LiteralPath $dg.FullName -Destination $out -Force; $n++ } else { $miss += 'verify_independent\*.digest.txt' }
  $npdf = 0
  if ($env:VRN_ROUND_NO_PDF -ne '1' -and (Test-Path -LiteralPath $SRC -PathType Container)) {
    $pd = Join-Path $out 'pdf'; New-Item -ItemType Directory -Force -Path $pd | Out-Null
    foreach ($key in $PDFS) { Get-ChildItem -LiteralPath $SRC -Filter '*.pdf' -ErrorAction SilentlyContinue | Where-Object { $_.Name -like ('*' + $key + '*') } | ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination $pd -Force; $npdf++ } }
  }
  try { Stop-Transcript | Out-Null } catch { }
  if (Test-Path -LiteralPath $log) { $lines = Get-Content -LiteralPath $log -Encoding UTF8; ($lines | Select-Object -Last 300) | Set-Content -LiteralPath (Join-Path $out 'NEXT_last300.txt') -Encoding UTF8 }
  $zip = $out + '.zip'; try { Compress-Archive -LiteralPath (Get-ChildItem -LiteralPath $out | ForEach-Object { $_.FullName }) -DestinationPath $zip -Force } catch { Write-Host ('  [YELLOW] 壓縮失敗:' + $_.Exception.Message) -ForegroundColor Yellow }
  Say $k4 $(if ($miss.Count -eq 0) { 'GREEN' } else { 'YELLOW' }) ("收據 / 輸出冊 {0} 份 · PDF {1} 份 · 缺 {2}{3}" -f $n, $npdf, $miss.Count, $(if ($miss.Count) { '(' + ($miss -join ' · ') + ')' } else { '' }))

  # 總結
  Write-Host ''; Write-Host ('===== 本地實測一輪 · {0:N0} 秒 ====='.Replace('{0:N0}', [string][int]((Get-Date) - $t0).TotalSeconds)) -ForegroundColor Yellow
  foreach ($k in $res.Keys) { Write-Host ("  [{0}] {1} · {2}" -f $res[$k][0], $k, $res[$k][1]) -ForegroundColor $col[$res[$k][0]] }
  $lamps = @($res.Values | ForEach-Object { $_[0] })
  $final = if ($lamps -contains 'RED') { 'RED' } elseif ($lamps -contains 'YELLOW') { 'YELLOW' } else { 'GREEN' }
  Write-Host ("[結果] {0} · 要貼回 / 上傳的只有這一個:{1}" -f $final, $(if (Test-Path -LiteralPath $zip) { $zip } else { $out })) -ForegroundColor $col[$final]
  Write-Host 'NEXT: 把上面那個 zip 上傳給 AI(裡面有貼包 · 收據 · 輸出冊 · Workbench 頁 · 五份 PDF)· Workbench 若沒自動開:VIA_Reports\vrn2\VRN2_Workbench_latest.html' -ForegroundColor Yellow
  try { Start-Process -FilePath 'explorer.exe' -ArgumentList ('/select,"' + $zip + '"') -ErrorAction SilentlyContinue } catch { }
  $global:LASTEXITCODE = @{ GREEN = 0; YELLOW = 2; RED = 1 }[$final]
}
```

開關一覽:`$env:VRN2_ROOT`(VIA 根)· `$env:VRN2_SOURCE`(來源夾)· `$env:VRN2_LOGO`(印章圖路徑)· `$env:VRN_ROUND_NO_SHIP='1'` 不補船 · `$env:VRN_ROUND_WITH_VRN1='1'` 連 VRN-1 一起跑 · `$env:VRN_ROUND_NO_PDF='1'` 不裝 PDF · `$env:VRN_ROUND_DRY='1'` 乾跑(只取碼、核對雜湊,不執行)。
程式碼只讀 GitHub 上已核對 SHA-256 的兩段(操作員一鍵 v0103 · ChainShip 一鍵),GitHub 上那兩段若換版,本段會紅並停,不會跑到未核對的碼。
ChainShip 那段核對後只做三處確定性改寫(`$REPO` 行 1 處 → 本輪的倉 · 4 處早退補 `$global:LASTEXITCODE = 1` · `$lamp` 行後加一行把綜合燈寫成結束碼);三處數目不符(1 · 4 · 1)就紅不執行。
