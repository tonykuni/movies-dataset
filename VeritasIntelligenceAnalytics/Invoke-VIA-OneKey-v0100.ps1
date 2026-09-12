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
function Head($t) {
  $global:Stations = $global:Stations + 1
  Write-Host "`n── $t ──" -ForegroundColor Cyan
}
function GitU { , @(git diff --name-only --diff-filter=U 2>$null | Where-Object { $_ }) }

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

# ③ git 解卡（可逆；非阻塞）
Head '③ git 解卡'
$pulled = $false
if (-not $Mother) {
  Lamp 'YELLOW' 'GIT' '母庫缺席,跳過'
} else {
  $br = (git rev-parse --abbrev-ref HEAD 2>$null)
  $gd = (git rev-parse --git-dir 2>$null)
  $U = GitU
  Write-Host ("  分支 $br · HEAD $(git rev-parse --short HEAD 2>$null) · 未合併檔 $($U.Count) 個")
  foreach ($f in ($U | Select-Object -First 12)) { Write-Host ("      $f") -ForegroundColor Yellow }
  if ($U.Count -gt 0) {
    # 先存保命點：只是一個分支指標,不動任何檔,隨時 git checkout 回來
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    git branch "via-rescue-$stamp" 2>&1 | Out-Null
    Write-Host ("  保命點 via-rescue-$stamp(只是個分支指標,不動檔案)") -ForegroundColor DarkGray
    if (Test-Path -LiteralPath (Join-Path $gd 'MERGE_HEAD')) {
      git merge --abort 2>&1 | Out-Null
      Write-Host '  merge --abort(完全可逆,還原成 pull 之前)' -ForegroundColor DarkGray
    }
  }
  $U2 = GitU
  if ($U2.Count -gt 0) {
    Lamp 'RED' 'GIT' "仍有 $($U2.Count) 個未合併檔,不硬拉(硬拉只會再卡一次)；把上面清單貼給我"
  } else {
    git fetch origin $br 2>&1 | Out-Null
    git merge-base --is-ancestor HEAD FETCH_HEAD 2>$null
    $ff = ($LASTEXITCODE -eq 0)
    $localOnly = @(git log --oneline HEAD --not FETCH_HEAD 2>$null | Where-Object { $_ })
    $remoteOnly = @(git log --oneline FETCH_HEAD --not HEAD 2>$null | Where-Object { $_ })
    if ($ff -and $remoteOnly.Count -eq 0) {
      Lamp 'GREEN' 'GIT' "已是最新 $(git rev-parse --short HEAD 2>$null)"
      $pulled = $true
    } elseif ($ff) {
      $before = (git rev-parse --short HEAD 2>$null)
      git pull --ff-only origin $br 2>&1 | Out-Null
      if ($LASTEXITCODE -eq 0) {
        Lamp 'GREEN' 'GIT' "$before → $(git rev-parse --short HEAD 2>$null)（快轉 $($remoteOnly.Count) 個 commit）"
        $pulled = $true
      } else { Lamp 'RED' 'GIT' '快轉失敗' }
    } else {
      $mt = (git merge-tree HEAD FETCH_HEAD 2>&1 | Out-String)
      $conf = @([regex]::Matches($mt, 'CONFLICT[^\r\n]*') | ForEach-Object { $_.Value } | Select-Object -Unique)
      if ($conf.Count -eq 0) {
        $mb = (git merge-base HEAD FETCH_HEAD 2>$null)
        $old = (git merge-tree $mb HEAD FETCH_HEAD 2>&1 | Out-String)
        $conf = @([regex]::Matches($old, 'changed in both\r?\n\s+base\s+\S+\s+\S+\s+(\S.*)') | ForEach-Object { '兩邊都改過：' + $_.Groups[1].Value.Trim() } | Select-Object -Unique)
      }
      Lamp 'YELLOW' 'GIT' "分岔:你獨有 $($localOnly.Count) · 遠端獨有 $($remoteOnly.Count) · 會打架 $($conf.Count) 處 → 不猜該留哪邊,貼給我"
      foreach ($c in ($conf | Select-Object -First 10)) { Write-Host ("      $c") -ForegroundColor Yellow }
      foreach ($c in ($localOnly | Select-Object -First 6)) { Write-Host ("      本地 $c") -ForegroundColor DarkYellow }
    }
  }
}

# ④ python
Head '④ python'
$py = Get-Command python -EA SilentlyContinue
if (-not $py) { $py = Get-Command python3 -EA SilentlyContinue }
if (-not $py) { $py = Get-Command py -EA SilentlyContinue }
if ($py) { Lamp 'GREEN' 'PYTHON' $py.Source } else { Lamp 'RED' 'PYTHON' '不在 PATH 上' }

# ⑤ OCR 安裝器：驗能力,不只驗在位
Head '⑤ OCR 安裝器'
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
    Lamp 'RED' 'ENVMGR' "找到 $($cands.Count) 支,沒有一支有 ocr 子命令$EMwhy`n      修法:origin 若是 tonykuni/VIA-VDF-VRN,到該夾 git fetch origin claude/vrn-tp-candidate-scoring 再 git checkout 它"
  }
}

# ⑥ OCR 現況
Head '⑥ OCR 現況'
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
Head '⑦ 補 OCR 語言檔'
if ($langs.Count -ge 3) {
  Lamp 'GREEN' 'OCR-FIX' '語言檔本來就齊,不動'
} elseif (-not ($EM -and $py)) {
  Lamp 'YELLOW' 'OCR-FIX' '沒有可用的安裝器,跳過(見 ⑤)'
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
Head '⑧ 首頁引擎自測'
if (-not ($Mother -and $py)) {
  Lamp 'YELLOW' 'ENGINE' '母庫或 python 缺席,跳過'
} else {
  $eng = Get-ChildItem -LiteralPath (Join-Path $Mother 'functional modules\VRN') -Filter 'VIA_VRN_FirstPageEngine_v*.py' -EA SilentlyContinue | Sort-Object Name | Select-Object -Last 1
  if (-not $eng) {
    Lamp 'RED' 'ENGINE' '找不到首頁引擎'
  } else {
    $out = & $py.Source $eng.FullName --selftest 2>&1 | Out-String
    $tally = ($out -split "`n" | Where-Object { $_ -match '\[計\]' } | Select-Object -Last 1)
    if ($tally) { $tally = $tally.Trim() } else { $tally = '(沒印出計數)' }
    if ($out -match 'FAIL 0') { Lamp 'GREEN' 'ENGINE' "$($eng.Name) · $tally" } else { Lamp 'RED' 'ENGINE' "$($eng.Name) · $tally" }
  }
}

# ⑨ VRN 收尾
Head '⑨ VRN 收尾'
if (Get-Command via-vrnval -EA SilentlyContinue) {
  via-vrnval --run
  Lamp 'GREEN' 'VRNVAL' '已跑(判讀看上面 DONE/FAIL/PENDING)'
} else { Lamp 'YELLOW' 'VRNVAL' '短令未載入,跳過' }

# ⑩ 編碼暴露盤點（唯讀,只量不改）
Head '⑩ 編碼暴露盤點'
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
Head '⑪ 總表'
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

