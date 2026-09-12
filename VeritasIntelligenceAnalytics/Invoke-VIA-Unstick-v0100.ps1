# ── 解卡:母庫工作區有未合併檔,先看清楚再動;只做可逆的 ──
$ErrorActionPreference = 'Continue'
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8; $OutputEncoding = [Text.Encoding]::UTF8 } catch {}
Set-Location -LiteralPath 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'

Write-Host "`n── ① 現況(唯讀) ──" -ForegroundColor Cyan
$br = (git rev-parse --abbrev-ref HEAD 2>$null)
Write-Host ("  分支 = " + $br + "   HEAD = " + (git rev-parse --short HEAD 2>$null))
$U = @(git diff --name-only --diff-filter=U 2>$null)
Write-Host ("  未合併檔 = " + $U.Count + " 個")
foreach ($f in $U) { Write-Host ("      " + $f) -ForegroundColor Yellow }
$gd = (git rev-parse --git-dir 2>$null)
$inMerge = Test-Path -LiteralPath (Join-Path $gd 'MERGE_HEAD')
$inRebase = (Test-Path -LiteralPath (Join-Path $gd 'rebase-merge')) -or (Test-Path -LiteralPath (Join-Path $gd 'rebase-apply'))
Write-Host ("  merge 進行中 = " + $inMerge + " · rebase 進行中 = " + $inRebase)

Write-Host "`n── ② 有沒有你自己的東西會被弄丟(唯讀) ──" -ForegroundColor Cyan
$mod = @(git diff --name-only HEAD 2>$null | Where-Object { $_ -and ($U -notcontains $_) })
Write-Host ("  除了衝突檔之外,還有 " + $mod.Count + " 個檔被改過")
foreach ($f in ($mod | Select-Object -First 15)) { Write-Host ("      " + $f) }
$st = @(git stash list 2>$null)
Write-Host ("  stash = " + $st.Count + " 筆")

Write-Host "`n── ③ 動作 ──" -ForegroundColor Cyan
if ($inRebase) {
  Write-Host '  rebase 進行中。我不替你決定要 --abort 還是 --continue,貼上面的結果給我。' -ForegroundColor Yellow
} elseif ($inMerge) {
  # merge --abort 是完全可逆的:把工作區還原成 pull 之前,一個字都不丟
  Write-Host '  merge 進行中 → git merge --abort(完全可逆,還原成 pull 之前,不丟任何東西)' -ForegroundColor Green
  git merge --abort 2>&1 | Write-Host
  $U2 = @(git diff --name-only --diff-filter=U 2>$null)
  Write-Host ("  還原後未合併檔 = " + $U2.Count + " 個")
} elseif ($U.Count -gt 0) {
  Write-Host '  有未合併檔但不在 merge 中(索引殘留)。我不猜該留哪一邊——貼上面的結果給我。' -ForegroundColor Yellow
} else {
  Write-Host '  索引乾淨,沒有未合併檔。' -ForegroundColor Green
}

Write-Host "`n── ④ 分岔看清楚（唯讀，不碰工作區） ──" -ForegroundColor Cyan
$stillU = @(git diff --name-only --diff-filter=U 2>$null)
$canPull = $false
if ($stillU.Count -gt 0) {
  Write-Host '  仍有未合併檔，不看了也不拉。' -ForegroundColor Red
} else {
  git fetch origin $br 2>&1 | Out-Null
  $mb = (git merge-base HEAD FETCH_HEAD 2>$null)
  $localOnly = @(git log --oneline HEAD --not FETCH_HEAD 2>$null)
  $remoteOnly = @(git log --oneline FETCH_HEAD --not HEAD 2>$null)
  Write-Host ("  你這邊獨有 " + $localOnly.Count + " 個 commit · 遠端獨有 " + $remoteOnly.Count + " 個")
  foreach ($c in ($localOnly | Select-Object -First 8)) { Write-Host ("      本地 " + $c) -ForegroundColor Yellow }
  git merge-base --is-ancestor HEAD FETCH_HEAD 2>$null
  $ff = ($LASTEXITCODE -eq 0)
  Write-Host ("  可以直接快轉(fast-forward) = " + $ff)
  if (-not $ff) {
    # 預覽會打架的檔：merge-tree 只算不寫，工作區一個字不動。
    # 先用新式兩參數(git 2.38+，會直接吐 CONFLICT 行)；舊 git 退回三參數式數
    # 「changed in both」——寧可報得寬，也不要報 0 處那種假綠。
    $mt = (git merge-tree HEAD FETCH_HEAD 2>&1 | Out-String)
    $conf = @([regex]::Matches($mt, 'CONFLICT[^\r\n]*') | ForEach-Object { $_.Value } | Select-Object -Unique)
    if ($conf.Count -eq 0) {
      $old = (git merge-tree $mb HEAD FETCH_HEAD 2>&1 | Out-String)
      $both = @([regex]::Matches($old, 'changed in both\r?\n\s+base\s+\S+\s+\S+\s+(\S.*)') | ForEach-Object { '兩邊都改過：' + $_.Groups[1].Value.Trim() } | Select-Object -Unique)
      $conf = $both
    }
    Write-Host ("  併起來會打架的地方 = " + $conf.Count + " 處")
    foreach ($c in ($conf | Select-Object -First 12)) { Write-Host ("      " + $c) -ForegroundColor Yellow }
  }
  $canPull = $ff
}

Write-Host "`n── ⑤ 拉 ──" -ForegroundColor Cyan
if ($canPull) {
  git pull --ff-only origin $br 2>&1 | Write-Host
  if ($LASTEXITCODE -eq 0) { Write-Host ("  拉到 " + (git rev-parse --short HEAD 2>$null)) -ForegroundColor Green } else { Write-Host '  快轉失敗，訊息在上面。' -ForegroundColor Red }
} else {
  # v1 這裡是盲目重拉，實測會把 repo 再卡回去一次——看起來做了事，其實原地踏步
  Write-Host '  不拉。因為兩邊各自往前走了，硬拉只會再卡一次(v1 就是這樣把你卡回去的)。' -ForegroundColor Yellow
  Write-Host '  把上面 ④ 的分岔結果貼給我，我看完再給你逐檔的解法——不猜該留哪一邊。' -ForegroundColor Yellow
}

Write-Host "`n── ⑥ 腳本到了沒 ──" -ForegroundColor Cyan
if (Test-Path -LiteralPath (Join-Path (Get-Location) 'Invoke-VIA-FixAll-v0100.ps1')) {
  Write-Host '  Invoke-VIA-FixAll-v0100.ps1 在，可以跑：  .\Invoke-VIA-FixAll-v0100.ps1' -ForegroundColor Green
} else {
  Write-Host '  還沒到(pull 還沒成功)。' -ForegroundColor Red
}

