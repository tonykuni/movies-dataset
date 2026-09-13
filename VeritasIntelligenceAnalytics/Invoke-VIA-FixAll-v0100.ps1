# ── VIA 一貼收尾 v2 ──
# v1 的兩個錯：①貼進互動視窗時 if{...} 自成一句先跑掉、下一行 else 變孤兒指令
#              ②只驗 EnvManager「檔案在不在」，沒驗「它會不會做 ocr」＝在位≠跑得動
# v2：所有 if/else 一律 "} else {" 同一行（貼上去才不會散）；EnvManager 改驗**能力**。
$ErrorActionPreference = 'Continue'
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8; $OutputEncoding = [Text.Encoding]::UTF8 } catch {}
$L = New-Object System.Collections.ArrayList
function Lamp($c, $k, $m) {
  $null = $L.Add([pscustomobject]@{ 燈 = $c; 站 = $k; 說明 = $m })
  $col = 'Gray'
  if ($c -eq 'GREEN') { $col = 'Green' } elseif ($c -eq 'YELLOW') { $col = 'Yellow' } elseif ($c -eq 'RED') { $col = 'Red' }
  Write-Host ("{0,-6} {1,-12} {2}" -f $c, $k, $m) -ForegroundColor $col
}
function Head($t) { Write-Host "`n── $t ──" -ForegroundColor Cyan }

Head '① 母庫正本'
$Mother = $null
foreach ($m in @('C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics',
                 'C:\Users\tonyk\Downloads\movies-dataset-b381\VeritasIntelligenceAnalytics',
                 'C:\Users\tonyk\Github\movies-dataset\VeritasIntelligenceAnalytics')) {
  if (Test-Path -LiteralPath $m) { $Mother = $m; break }
}
if (-not $Mother) {
  Lamp 'RED' '母庫' '三個副本都找不到，後面全部跳過'
} else {
  Set-Location -LiteralPath $Mother
  Lamp 'GREEN' '母庫' $Mother
}

Head '② 拉齊母庫'
if (-not $Mother) {
  Lamp 'YELLOW' 'GIT' '母庫缺席，跳過'
} else {
  $br = (git rev-parse --abbrev-ref HEAD 2>$null)
  if (-not $br) {
    Lamp 'RED' 'GIT' '讀不到分支'
  } else {
    $before = (git rev-parse --short HEAD 2>$null)
    git pull origin $br 2>&1 | Out-String | Write-Host
    $after = (git rev-parse --short HEAD 2>$null)
    if ($LASTEXITCODE -eq 0) { Lamp 'GREEN' 'GIT' "$br  $before → $after" } else { Lamp 'RED' 'GIT' 'pull 失敗（多半是本機有未提交或衝突）；不代你 reset，自己看上面訊息' }
  }
}

Head '③ 短令冊 + via-pin'
if (-not $Mother) {
  Lamp 'YELLOW' 'REGISTER' '母庫缺席，跳過'
} else {
  $reg = Get-ChildItem -LiteralPath $Mother -Filter 'Register-VIA-Commands-v*.ps1' -EA SilentlyContinue | Sort-Object Name | Select-Object -Last 1
  if (-not $reg) {
    Lamp 'RED' 'REGISTER' '找不到 Register-VIA-Commands-v*.ps1'
  } else {
    . $reg.FullName
    Lamp 'GREEN' 'REGISTER' $reg.Name
    if (Get-Command via-pin -EA SilentlyContinue) {
      via-pin --show
      via-pin
      Lamp 'GREEN' 'PIN' 'profile 點源已指向本副本（新視窗才生效）'
    } else { Lamp 'YELLOW' 'PIN' '這版短令冊沒有 via-pin' }
  }
}

Head '④ python'
$py = Get-Command python -EA SilentlyContinue
if (-not $py) { $py = Get-Command python3 -EA SilentlyContinue }
if (-not $py) { $py = Get-Command py -EA SilentlyContinue }
if ($py) { Lamp 'GREEN' 'PYTHON' $py.Source } else { Lamp 'RED' 'PYTHON' '不在 PATH 上' }

Head '⑤ OCR 安裝器（驗能力，不只驗在位）'
# v1 的假綠：找到同名檔就掛綠燈。你那台的 C:\Users\tonyk\Github\... 是另一條血脈的舊檔，
# usage 只有 --task {scan,talib}，根本沒有 ocr 子命令——在位≠跑得動。
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
  Lamp 'YELLOW' 'ENVMGR' '沒有 python，驗不了能力'
} elseif ($cands.Count -eq 0) {
  Lamp 'RED' 'ENVMGR' 'VIA-VDF-VRN 庫不在這台機器上'
} else {
  foreach ($c in $cands) {
    $h = (& $py.Source $c --help 2>&1 | Out-String)
    if ($h -match '\bocr\b') {
      $EM = $c; break
    } else {
      # 不要叫你去 checkout 一個沒人確認過的 clone——把它的 origin 與分支印出來，你自己看
      $cr = (Resolve-Path -LiteralPath (Join-Path (Split-Path (Split-Path $c -Parent) -Parent) '..')).Path
      $gu = (git -C $cr remote get-url origin 2>$null)
      $gb = (git -C $cr rev-parse --abbrev-ref HEAD 2>$null)
      if (-not $gu) { $gu = '(不是 git 工作區)' }
      $EMwhy = "$EMwhy`n    舊血脈（--help 無 ocr）：$c`n        origin=$gu  分支=$gb"
    }
  }
  if ($EM) {
    Lamp 'GREEN' 'ENVMGR' "$EM（--help 認得 ocr）"
  } else {
    Lamp 'RED' 'ENVMGR' "找到 $($cands.Count) 支 EnvManager，沒有一支有 ocr 子命令：$EMwhy`n    修法：上面 origin 若是 tonykuni/VIA-VDF-VRN，到該夾跑`n        git fetch origin claude/vrn-tp-candidate-scoring`n        git checkout claude/vrn-tp-candidate-scoring`n    若 origin 不是它，那支是另一條血脈的同名檔，別動它——改 clone 一份新的"
  }
}

Head '⑥ OCR 現況'
$Prefix = $env:TESSDATA_PREFIX
if (-not $Prefix) { $Prefix = 'C:\Users\tonyk\OneDrive\Desktop\VRN\tessdata_best' }
$langsBefore = @()
if (Get-Command tesseract -EA SilentlyContinue) {
  $langsBefore = @((tesseract --list-langs 2>&1) | Select-Object -Skip 1 | Where-Object { $_ -match '^\w+$' })
  $c6 = 'RED'
  if ($langsBefore.Count) { $c6 = 'GREEN' }
  Lamp $c6 'TESSDATA' "語言 $($langsBefore.Count) 個：$($langsBefore -join ',')  夾=$Prefix"
} else { Lamp 'RED' 'TESSERACT' '不在 PATH 上' }

Head '⑦ 補 OCR 語言檔'
if ($langsBefore.Count -ge 3) {
  Lamp 'GREEN' 'OCR-FIX' '語言檔本來就齊，不動'
} elseif (-not ($EM -and $py)) {
  Lamp 'YELLOW' 'OCR-FIX' '沒有可用的安裝器，跳過（見 ⑤ 的修法）'
} else {
  Write-Host '  這一步會從 GitHub 下載 chi_tra/chi_sim/eng（約 41 MB，pinned commit）。' -ForegroundColor Yellow
  & $py.Source $EM ocr --repair --tessdata-prefix $Prefix
  $rc = $LASTEXITCODE
  $langsAfter = @()
  if (Get-Command tesseract -EA SilentlyContinue) { $langsAfter = @((tesseract --list-langs 2>&1) | Select-Object -Skip 1 | Where-Object { $_ -match '^\w+$' }) }
  $need = @('chi_tra', 'chi_sim', 'eng') | Where-Object { $_ -notin $langsAfter }
  if ($need.Count -eq 0) { Lamp 'GREEN' 'OCR-FIX' "補齊：$($langsAfter -join ',')" } else { Lamp 'RED' 'OCR-FIX' "仍缺 $($need -join ',')（EnvManager exit $rc）" }
}

Head '⑧ 首頁引擎自測'
if (-not ($Mother -and $py)) {
  Lamp 'YELLOW' 'ENGINE' '母庫或 python 缺席，跳過'
} else {
  $eng = Get-ChildItem -LiteralPath (Join-Path $Mother 'functional modules\VRN') -Filter 'VIA_VRN_FirstPageEngine_v*.py' -EA SilentlyContinue | Sort-Object Name | Select-Object -Last 1
  if (-not $eng) {
    Lamp 'RED' 'ENGINE' '找不到首頁引擎'
  } else {
    $out = & $py.Source $eng.FullName --selftest 2>&1 | Out-String
    $tally = ($out -split "`n" | Where-Object { $_ -match '\[計\]' } | Select-Object -Last 1)
    if ($tally) { $tally = $tally.Trim() }
    if ($out -match 'FAIL 0') { Lamp 'GREEN' 'ENGINE' "$($eng.Name)  $tally" } else { Lamp 'RED' 'ENGINE' "$($eng.Name)  $tally" }
  }
}

Head '⑨ VRN 收尾'
if (Get-Command via-vrnval -EA SilentlyContinue) {
  via-vrnval --run
  Lamp 'GREEN' 'VRNVAL' '已跑（判讀看上面 DONE/FAIL/PENDING）'
} else { Lamp 'YELLOW' 'VRNVAL' '短令未載入，跳過' }

Head '⑩ 編碼暴露盤點（唯讀，只量不改）'
if (-not $Mother) {
  Lamp 'YELLOW' 'ENC' '母庫缺席，跳過'
} else {
  $mgr = Get-ChildItem -LiteralPath $Mother -Filter 'VIA_SYSTEM_MANAGER_v*.py' -EA SilentlyContinue | Sort-Object Name | Select-Object -Last 1
  if (-not $mgr) {
    Lamp 'YELLOW' 'ENC' '找不到 VIA_SYSTEM_MANAGER_v*.py'
  } else {
    # 純 PowerShell 做（v1 用 python here-string，貼上去多一個會壞的地方）
    $enc = [Text.Encoding]::GetEncoding(1252)
    $txt = Get-Content -LiteralPath $mgr.FullName -Raw -Encoding UTF8
    $n = 0
    foreach ($ln in ($txt -split "`n")) {
      if ($ln -notmatch 'print\(|_lamp\(') { continue }
      if ($enc.GetString($enc.GetBytes($ln)) -ne $ln) { $n++ }
    }
    if ($txt -match 'reconfigure\(encoding') { Lamp 'GREEN' 'ENC' "$($mgr.Name) 已有守衛" } elseif ($n -gt 0) { Lamp 'YELLOW' 'ENC' "$($mgr.Name) 無守衛，會 print 的中文行 $n 行＝潛在地雷（目前 CI 綠，我沒動它）" } else { Lamp 'GREEN' 'ENC' "$($mgr.Name) 無中文輸出，無暴露" }
  }
}

Head '⑪ 總表'
foreach ($row in $L) { Write-Host ("  {0,-6}  {1,-12}  {2}" -f $row.燈, $row.站, $row.說明) }
$red = @($L | Where-Object { $_.燈 -eq 'RED' }).Count
$yel = @($L | Where-Object { $_.燈 -eq 'YELLOW' }).Count
$verdict = 'GREEN'; $vcol = 'Green'
if ($red) { $verdict = "RED（$red 紅 / $yel 黃）"; $vcol = 'Red' } elseif ($yel) { $verdict = "YELLOW（$yel 黃）"; $vcol = 'Yellow' }
Write-Host "`n總判：$verdict" -ForegroundColor $vcol
Write-Host '沒做的兩件（故意）：PR #8 不代你合併；VIA_SYSTEM_MANAGER 守衛不代你加。' -ForegroundColor DarkGray
Write-Host 'via-pin 改的是新視窗——這個視窗仍跑舊副本，關掉重開才生效。' -ForegroundColor DarkGray
