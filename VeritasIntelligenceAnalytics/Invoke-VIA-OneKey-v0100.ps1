# ══ VIA 一鍵:進環境 + 解卡 + 收尾 ══════════════════════════════════════════
# 設計上的一條鐵律:git 那一步是**非阻塞**的。拉不動也不擋後面——
# 上一版把後面的事綁在 pull 成功上,於是「拉不下來→檔案不在→腳本跑不了」變成死迴圈。
# 零破壞性指令(無 reset --hard / clean / checkout --force / rm)；不代設任何同意閘；不代合併 PR。
$ErrorActionPreference = 'Continue'
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8; $OutputEncoding = [Text.Encoding]::UTF8 } catch {}
$L = New-Object System.Collections.ArrayList
function Lamp($c, $k, $m) {
  $null = $L.Add([pscustomobject]@{ 燈 = $c; 站 = $k; 說明 = $m })
  $col = 'Gray'
  if ($c -eq 'GREEN') { $col = 'Green' } elseif ($c -eq 'YELLOW') { $col = 'Yellow' } elseif ($c -eq 'RED') { $col = 'Red' }
  Write-Host ("{0,-6} {1,-11} {2}" -f $c, $k, $m) -ForegroundColor $col
}
$Stations = 0
$StationTotal = 12
function Head($t) {
  $global:Stations = $global:Stations + 1
  $pct = [int](100 * ($global:Stations - 1) / $StationTotal)
  Write-Progress -Id 1 -Activity 'VIA 一鍵' -Status $t -PercentComplete $pct
  Write-Host ("`n── {0} ──  [{1}%]" -f $t, $pct) -ForegroundColor Cyan
}

# 不卡斷:子行程邊跑邊把新行吐出來(不是等它跑完才一次 Out-String),
# 逾時就中止並記 TIMEOUT——**只中止本腳本自己啟動的那個子行程**,
# 絕不碰別人的進程(NoStopProcess 講的是別人的)。
# 批423 操作員令「卡斷 加入20個加速器 不卡斷 動態進度條」的同一條紀律。
function RunProc([string]$exe, [string[]]$argv, [int]$TimeoutSec, [string]$Label) {
  $o = [IO.Path]::GetTempFileName()
  $e = [IO.Path]::GetTempFileName()
  $to = $false
  # 含空白的路徑一定要自己加引號:Start-Process 會把 -ArgumentList 用空白串起來,
  # 而這個系統的路徑天天都是「functional modules\VRN」。實測不加引號 → python rc=2
  # (開不了檔),而且是靜默的——RunProc 收到 0 行輸出,燈就報成「沒印出計數」。
  $q = @($argv | ForEach-Object { if ($_ -match '\s') { '"' + $_ + '"' } else { $_ } })
  $p = Start-Process -FilePath $exe -ArgumentList $q -NoNewWindow -PassThru -RedirectStandardOutput $o -RedirectStandardError $e
  $sw = [Diagnostics.Stopwatch]::StartNew()
  $seen = 0
  while (-not $p.HasExited) {
    $lines = @(Get-Content -LiteralPath $o -EA SilentlyContinue)
    if ($lines.Count -gt $seen) {
      foreach ($ln in $lines[$seen..($lines.Count - 1)]) { Write-Host ("    $ln") -ForegroundColor DarkGray }
      $seen = $lines.Count
    }
    $el = [int]$sw.Elapsed.TotalSeconds
    Write-Progress -Id 2 -ParentId 1 -Activity $Label -Status ("跑了 {0} 秒 / 上限 {1} 秒 · 已吐 {2} 行" -f $el, $TimeoutSec, $seen) -PercentComplete ([math]::Min(99, [int](100 * $el / [math]::Max(1, $TimeoutSec))))
    if ($el -ge $TimeoutSec) { try { $p.Kill() } catch { }; $to = $true; break }
    Start-Sleep -Milliseconds 400
  }
  Start-Sleep -Milliseconds 200
  $all = @(Get-Content -LiteralPath $o -EA SilentlyContinue)
  if ($all.Count -gt $seen) { foreach ($ln in $all[$seen..($all.Count - 1)]) { Write-Host ("    $ln") -ForegroundColor DarkGray } }
  $err = (Get-Content -LiteralPath $e -Raw -EA SilentlyContinue)
  Write-Progress -Id 2 -ParentId 1 -Activity $Label -Completed
  $rc = 0
  if ($to) { $rc = -1 } elseif ($null -ne $p.ExitCode) { $rc = $p.ExitCode }
  Remove-Item -LiteralPath $o, $e -EA SilentlyContinue
  return @{ out = ($all -join "`n"); err = $err; rc = $rc; timeout = $to; secs = [int]$sw.Elapsed.TotalSeconds }
}
# 一元逗號會把陣列再包一層:`$x = GitU` 讀得到 0,`@(GitU).Count` 卻回 1。
# 同一個 helper 兩種用法給不同答案 —— 拿掉逗號,呼叫端一律 @() 包。
function GitU { git diff --name-only --diff-filter=U 2>$null | Where-Object { $_ } }

# ① 母庫正本
Head '① 母庫正本'
$Mother = $null
foreach ($m in @('C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics',
                 'C:\Users\tonyk\Downloads\movies-dataset-b381\VeritasIntelligenceAnalytics',
                 'C:\Users\tonyk\Github\movies-dataset\VeritasIntelligenceAnalytics')) {
  if (Test-Path -LiteralPath $m) { $Mother = $m; break }
}
if (-not $Mother) {
  Lamp 'RED' '母庫' '三個副本都找不到'
} else {
  Set-Location -LiteralPath $Mother
  Lamp 'GREEN' '母庫' $Mother
}

# ② 進環境（不需要 pull 成功；先進來,後面才有短令可用）
Head '② 進環境'
if (-not $Mother) {
  Lamp 'YELLOW' '環境' '母庫缺席,跳過'
} else {
  $reg = Get-ChildItem -LiteralPath $Mother -Filter 'Register-VIA-Commands-v*.ps1' -EA SilentlyContinue | Sort-Object Name | Select-Object -Last 1
  if (-not $reg) {
    Lamp 'RED' '環境' '找不到 Register-VIA-Commands-v*.ps1'
  } else {
    . $reg.FullName
    $n = @(Get-Command -Name 'via-*' -CommandType Function -EA SilentlyContinue).Count
    Lamp 'GREEN' '環境' ("$($reg.Name) · 短令 $n 個")
  }
}

# ③ git 解卡（可逆；非阻塞；產物自動解,原始碼不猜）
Head '③ git 解卡'
$pulled = $false
# 產物 = 引擎的輸出,下次跑就重生 → 取遠端版不損失任何東西,可以自動解。
# .zip 不在內:批367 定過「zip 為收容原件=只增不減」,那是來源不是產物。
function IsArtifact([string]$f) {
  if ($f -match '\.(parquet|duckdb|pyc)$') { return $true }
  if ($f -match '(^|/)__pycache__/') { return $true }
  if ($f -match '(^|/)VIA_Reports/') { return $true }
  if ($f -match '(^|/)_warehouse/') { return $true }
  if ($f -match '(^|/)output/.*\.(db|json|html|csv)$') { return $true }
  if ($f -match '_selftest\.db$') { return $true }
  return $false
}
function ResolveArtifacts {
  $u = @(git diff --name-only --diff-filter=U 2>$null | Where-Object { $_ })
  $art = @($u | Where-Object { IsArtifact $_ })
  $src = @($u | Where-Object { -not (IsArtifact $_) })
  foreach ($f in $art) {
    git checkout --theirs -- "$f" 2>&1 | Out-Null
    git add -- "$f" 2>&1 | Out-Null
  }
  return @{ art = $art; src = $src }
}
if (-not $Mother) {
  Lamp 'YELLOW' 'GIT' '母庫缺席,跳過'
} else {
  $br = (git rev-parse --abbrev-ref HEAD 2>$null)
  $gd = (git rev-parse --git-dir 2>$null)
  $U0 = @(GitU)
  Write-Host ("  分支 $br · HEAD $(git rev-parse --short HEAD 2>$null) · 未合併檔 $($U0.Count) 個")
  if ($U0.Count -gt 0) {
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    git branch "via-rescue-$stamp" 2>&1 | Out-Null
    Write-Host ("  保命點 via-rescue-$stamp(分支指標,不動檔案;要回去 git checkout 它)") -ForegroundColor DarkGray
  }
  git fetch origin $br 2>&1 | Out-Null
  # 不在 merge 中但有分岔 → 主動起一次 merge,好讓產物律有東西可解
  if (-not (Test-Path -LiteralPath (Join-Path $gd 'MERGE_HEAD'))) {
    git merge-base --is-ancestor HEAD FETCH_HEAD 2>$null
    $ff = ($LASTEXITCODE -eq 0)
    $remoteOnly = @(git log --oneline FETCH_HEAD --not HEAD 2>$null | Where-Object { $_ })
    if ($ff -and $remoteOnly.Count -eq 0) {
      Lamp 'GREEN' 'GIT' "已是最新 $(git rev-parse --short HEAD 2>$null)"
      $pulled = $true
    } elseif ($ff) {
      $before = (git rev-parse --short HEAD 2>$null)
      git pull --ff-only origin $br 2>&1 | Out-Null
      if ($LASTEXITCODE -eq 0) { Lamp 'GREEN' 'GIT' "$before → $(git rev-parse --short HEAD 2>$null)(快轉 $($remoteOnly.Count) 個)"; $pulled = $true } else { Lamp 'RED' 'GIT' '快轉失敗' }
    } elseif ($U0.Count -eq 0) {
      Write-Host '  兩邊各自往前走了 → 起一次 merge(產物自動解,原始碼不猜)' -ForegroundColor DarkGray
      git merge FETCH_HEAD --no-edit 2>&1 | Out-Null
    }
  }
  # 到這裡若還在 merge 中(本來就卡著,或剛起的)→ 套產物律
  if (-not $pulled) {
    if (Test-Path -LiteralPath (Join-Path $gd 'MERGE_HEAD')) {
      $r = ResolveArtifacts
      Write-Host ("  產物自動取遠端 $($r.art.Count) 個 · 原始碼待決 $($r.src.Count) 個") -ForegroundColor DarkGray
      foreach ($f in ($r.art | Select-Object -First 8)) { Write-Host ("      [產物] $f") -ForegroundColor DarkGray }
      if ($r.src.Count -eq 0) {
        git commit --no-edit 2>&1 | Out-Null
        if (@(GitU).Count -eq 0) {
          Lamp 'GREEN' 'GIT' "解開了 · $(git rev-parse --short HEAD 2>$null) · 產物 $($r.art.Count) 個取遠端(下次跑重生)"
          $pulled = $true
        } else { Lamp 'RED' 'GIT' '產物都解了但 commit 沒成,訊息在上面' }
      } else {
        Lamp 'RED' 'GIT' "原始碼衝突 $($r.src.Count) 個,不猜該留哪邊 → 把下面清單貼給我"
        foreach ($f in $r.src) { Write-Host ("      [原始碼] $f") -ForegroundColor Yellow }
      }
    } elseif (@(GitU).Count -gt 0) {
      Lamp 'RED' 'GIT' "索引有殘留未合併檔但不在 merge 中,不亂動 → 貼給我"
      foreach ($f in @(GitU)) { Write-Host ("      $f") -ForegroundColor Yellow }
    }
  }
  # 保證這一站一定發燈。實測逼出來的漏洞:repo 已解完、本地領先遠端時
  # ——不是快轉、遠端沒新東西、也不在 merge 中——上面三個分支都不成立,
  # 結果一盞燈都沒發,又是一個靜默站。不補 elseif(下次還會漏),
  # 改成**發完才算數**:沒發就在這裡照實況補一盞。
  if (-not (@($L | Where-Object { $_.站 -eq 'GIT' }).Count)) {
    $ahead = @(git log --oneline HEAD --not FETCH_HEAD 2>$null | Where-Object { $_ }).Count
    $behind = @(git log --oneline FETCH_HEAD --not HEAD 2>$null | Where-Object { $_ }).Count
    if ($ahead -gt 0 -and $behind -eq 0) {
      Lamp 'GREEN' 'GIT' "沒東西要拉 · 本地領先遠端 $ahead 個 commit(要送上去就 git push)"
    } else {
      Lamp 'YELLOW' 'GIT' "狀態未歸類:領先 $ahead · 落後 $behind · 未合併 $(@(GitU).Count) → 貼給我"
    }
  }
}

# ④ python
Head '④ python'
$py = Get-Command python -EA SilentlyContinue
if (-not $py) { $py = Get-Command python3 -EA SilentlyContinue }
if (-not $py) { $py = Get-Command py -EA SilentlyContinue }
if ($py) { Lamp 'GREEN' 'PYTHON' $py.Source } else { Lamp 'RED' 'PYTHON' '不在 PATH 上' }

# ⑤ 加速器(綁正典 SUP_MDL737 加速器橋,不另造一套)
Head '⑤ 加速器'
if (-not ($Mother -and $py)) {
  Lamp 'YELLOW' 'ACCEL' '母庫或 python 缺席,跳過'
} else {
  $acc = Get-ChildItem -LiteralPath (Join-Path $Mother 'supportive modules') -Filter 'SUP_MDL737_SuperAccelModule_v*.py' -EA SilentlyContinue | Sort-Object Name | Select-Object -Last 1
  if (-not $acc) {
    Lamp 'YELLOW' 'ACCEL' '找不到 SUP_MDL737 加速器橋'
  } else {
    $ra = RunProc $py.Source @($acc.FullName, '--activate') 180 '加速器啟動'
    $cap = ($ra.out -split "`n" | Where-Object { $_ -match 'lib 冊' } | Select-Object -First 1)
    if ($cap) { $cap = $cap.Trim() } else { $cap = '' }
    if ($ra.timeout) { Lamp 'RED' 'ACCEL' "$($acc.Name) 逾時中止(不卡斷)" } elseif ($cap) { Lamp 'GREEN' 'ACCEL' "$($acc.Name) · $cap" } else { Lamp 'YELLOW' 'ACCEL' "$($acc.Name) 跑了但沒印出 lib 冊(rc=$($ra.rc))" }
  }
}

# ⑤ OCR 安裝器：驗能力,不只驗在位
Head '⑥ OCR 安裝器'
$EM = $null; $EMwhy = ''
$cands = New-Object System.Collections.ArrayList
foreach ($p in @('C:\Users\tonyk\Github\VIA-VDF-VRN', 'C:\Users\tonyk\OneDrive\Documents\VIA-VDF-VRN',
                 'C:\Users\tonyk\Downloads\VIA-VDF-VRN', 'C:\Users\tonyk\VIA-VDF-VRN')) {
  $f = Join-Path $p 'public\via\VIA_EnvManager.py'
  if (Test-Path -LiteralPath $f) { $null = $cands.Add($f) }
}
foreach ($root in @('C:\Users\tonyk\Github', 'C:\Users\tonyk\OneDrive\Documents', 'C:\Users\tonyk\Downloads')) {
  if (-not (Test-Path -LiteralPath $root)) { continue }
  Get-ChildItem -LiteralPath $root -Directory -Depth 2 -EA SilentlyContinue | ForEach-Object {
    $f = Join-Path $_.FullName 'public\via\VIA_EnvManager.py'
    if ((Test-Path -LiteralPath $f) -and ($cands -notcontains $f)) { $null = $cands.Add($f) }
  }
}
if (-not $py) {
  Lamp 'YELLOW' 'ENVMGR' '沒有 python,驗不了能力'
} elseif ($cands.Count -eq 0) {
  Lamp 'RED' 'ENVMGR' 'VIA-VDF-VRN 庫不在這台機器上'
} else {
  foreach ($c in $cands) {
    $h = (& $py.Source $c --help 2>&1 | Out-String)
    if ($h -match '\bocr\b') {
      $EM = $c; break
    } else {
      $cr = (Split-Path (Split-Path (Split-Path $c -Parent) -Parent) -Parent)
      $gu = (git -C $cr remote get-url origin 2>$null)
      $gb = (git -C $cr rev-parse --abbrev-ref HEAD 2>$null)
      if (-not $gu) { $gu = '(不是 git 工作區)' }
      $EMwhy = "$EMwhy`n      舊血脈(--help 無 ocr)：$c`n          origin=$gu 分支=$gb"
    }
  }
  if ($EM) {
    Lamp 'GREEN' 'ENVMGR' "$EM"
  } else {
    Lamp 'RED' 'ENVMGR' "找到 $($cands.Count) 支,沒有一支有 ocr 子命令$EMwhy`n      修法(2026-09-12 PR #8 已併進 main,main 現在就有 ocr 子命令):`n      上面哪個 clone 的分支是 main,到那個夾跑 `"git pull`" 就好;`n      不在 main 的(例如 grok/… 分支)先 git checkout main 再 git pull"
  }
}

# ⑥ OCR 現況
Head '⑦ OCR 現況'
$Prefix = $env:TESSDATA_PREFIX
if (-not $Prefix) { $Prefix = 'C:\Users\tonyk\OneDrive\Desktop\VRN\tessdata_best' }
$langs = @()
if (Get-Command tesseract -EA SilentlyContinue) {
  $langs = @((tesseract --list-langs 2>&1) | Select-Object -Skip 1 | Where-Object { $_ -match '^\w+$' })
  $c6 = 'RED'
  if ($langs.Count) { $c6 = 'GREEN' }
  Lamp $c6 'TESSDATA' "語言 $($langs.Count) 個:$($langs -join ',') · 夾=$Prefix"
} else { Lamp 'RED' 'TESSERACT' '不在 PATH 上' }

# ⑦ 補 OCR 語言檔
Head '⑧ 補 OCR 語言檔'
if ($langs.Count -ge 3) {
  Lamp 'GREEN' 'OCR-FIX' '語言檔本來就齊,不動'
} elseif (-not ($EM -and $py)) {
  Lamp 'YELLOW' 'OCR-FIX' '沒有可用的安裝器,跳過(見 ⑥)'
} else {
  Write-Host '  會從 GitHub 下載 chi_tra/chi_sim/eng(約 41 MB,pinned commit)' -ForegroundColor Yellow
  & $py.Source $EM ocr --repair --tessdata-prefix $Prefix
  $rc = $LASTEXITCODE
  $after = @()
  if (Get-Command tesseract -EA SilentlyContinue) { $after = @((tesseract --list-langs 2>&1) | Select-Object -Skip 1 | Where-Object { $_ -match '^\w+$' }) }
  $need = @('chi_tra', 'chi_sim', 'eng') | Where-Object { $_ -notin $after }
  if ($need.Count -eq 0) { Lamp 'GREEN' 'OCR-FIX' "補齊:$($after -join ',')" } else { Lamp 'RED' 'OCR-FIX' "仍缺 $($need -join ',')(exit $rc)" }
}

# ⑧ 首頁引擎自測
Head '⑨ 首頁引擎自測'
if (-not ($Mother -and $py)) {
  Lamp 'YELLOW' 'ENGINE' '母庫或 python 缺席,跳過'
} else {
  $eng = Get-ChildItem -LiteralPath (Join-Path $Mother 'functional modules\VRN') -Filter 'VIA_VRN_FirstPageEngine_v*.py' -EA SilentlyContinue | Sort-Object Name | Select-Object -Last 1
  if (-not $eng) {
    Lamp 'RED' 'ENGINE' '找不到首頁引擎'
  } else {
    $r = RunProc $py.Source @($eng.FullName, '--selftest') 900 "引擎自測 $($eng.Name)"
    $tally = ($r.out -split "`n" | Where-Object { $_ -match '\[計\]' } | Select-Object -Last 1)
    if ($tally) { $tally = $tally.Trim() } else { $tally = '' }
    # 工作站實錄 2026-09-12:舊寫法是全篇搜 'FAIL 0',而自測輸出裡有子報告
    # 也印 'FAIL 0'(例如「[計] 1 件 · FAIL 0 · NLP 路徑=…」),於是真總計是
    # 「三十九檢 OK 38 · FAIL 1」卻掛綠燈。**又一個假綠**。
    # 只認**最後那一行 [計]** 裡的數字,別的地方寫什麼都不算。
    if ($r.timeout) {
      Lamp 'RED' 'ENGINE' "$($eng.Name) · 逾時被中止(不卡斷)"
    } elseif (-not $tally) {
      Lamp 'RED' 'ENGINE' "$($eng.Name) · 沒印出 [計] 計數,不當它綠"
    } elseif ($tally -match 'FAIL\s+(\d+)') {
      if ([int]$Matches[1] -eq 0) { Lamp 'GREEN' 'ENGINE' "$($eng.Name) · $tally" } else { Lamp 'RED' 'ENGINE' "$($eng.Name) · $tally" }
    } else {
      Lamp 'RED' 'ENGINE' "$($eng.Name) · [計] 讀不到 FAIL 數:$tally"
    }
  }
}

# ⑨ VRN 收尾
Head '⑩ VRN 收尾'
if (Get-Command via-vrnval -EA SilentlyContinue) {
  via-vrnval --run
  Lamp 'GREEN' 'VRNVAL' '已跑(判讀看上面 DONE/FAIL/PENDING)'
} else { Lamp 'YELLOW' 'VRNVAL' '短令未載入,跳過' }

# ⑩ 編碼暴露盤點（唯讀,只量不改）
Head '⑪ 編碼暴露盤點'
if (-not $Mother) {
  Lamp 'YELLOW' 'ENC' '母庫缺席,跳過'
} else {
  $mgr = Get-ChildItem -LiteralPath $Mother -Filter 'VIA_SYSTEM_MANAGER_v*.py' -EA SilentlyContinue | Sort-Object Name | Select-Object -Last 1
  if (-not $mgr) {
    Lamp 'YELLOW' 'ENC' '找不到 VIA_SYSTEM_MANAGER_v*.py'
  } else {
    $enc = [Text.Encoding]::GetEncoding(1252)
    $txt = Get-Content -LiteralPath $mgr.FullName -Raw -Encoding UTF8
    $n = 0
    foreach ($ln in ($txt -split "`n")) {
      if ($ln -notmatch 'print\(|_lamp\(') { continue }
      if ($enc.GetString($enc.GetBytes($ln)) -ne $ln) { $n++ }
    }
    if ($txt -match 'reconfigure\(encoding') { Lamp 'GREEN' 'ENC' "$($mgr.Name) 已有守衛" } elseif ($n -gt 0) { Lamp 'YELLOW' 'ENC' "$($mgr.Name) 無守衛,會 print 的中文 $n 行=潛在地雷(我沒動它)" } else { Lamp 'GREEN' 'ENC' "$($mgr.Name) 無中文輸出" }
  }
}

# ⑪ 總表
Write-Progress -Id 1 -Activity 'VIA 一鍵' -Completed
Head '⑫ 總表'
foreach ($row in $L) { Write-Host ("  {0,-6}  {1,-11}  {2}" -f $row.燈, $row.站, ($row.說明 -split "`n")[0]) }
$red = @($L | Where-Object { $_.燈 -eq 'RED' }).Count
$yel = @($L | Where-Object { $_.燈 -eq 'YELLOW' }).Count
# 完整性閘：⑪ 本身不是工作站,所以應收燈數 = 站數 - 1。
# 工作站實錄 2026-09-12:總表只印出 1 列卻報「總判:GREEN」,而同一次跑的
# 收尾是 RED、ENC 是 YELLOW——**假綠出現在我自己的儀表上**。
# 成因多半是分段貼上讓開頭的 $L 被重建一次,舊燈就沒了。
# 治法不是去猜成因,是立一條規矩:**數不齊就不准給總判**。
# 看不見全部的儀器沒有資格說「全綠」。
$want = $global:Stations - 1
if ($L.Count -lt $want) {
  Write-Host ("`n總判:不給 —— 總表只收到 $($L.Count) 盞燈,應該有 $want 盞。") -ForegroundColor Red
  Write-Host '  少掉的燈多半是分段貼上把 $L 重建了(開頭那行 $L = New-Object … 跑了第二次)。' -ForegroundColor Red
  Write-Host '  上面逐站的即時輸出仍然可信;不可信的是這張總表。請整份一次貼,或存檔用 .\Invoke-VIA-OneKey-v0100.ps1 跑。' -ForegroundColor Red
} else {
  $verdict = 'GREEN'; $vcol = 'Green'
  if ($red) { $verdict = "RED($red 紅 / $yel 黃)"; $vcol = 'Red' } elseif ($yel) { $verdict = "YELLOW($yel 黃)"; $vcol = 'Yellow' }
  Write-Host "`n總判:$verdict（$($L.Count)/$want 盞燈齊）" -ForegroundColor $vcol
}
Write-Host '故意沒做:PR #8 不代你合併;VIA_SYSTEM_MANAGER 守衛不代你加;不代設任何同意閘。' -ForegroundColor DarkGray
Write-Host '全程零破壞性指令:沒有 reset --hard / clean / checkout --force / Remove-Item。' -ForegroundColor DarkGray

