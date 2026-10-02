&{
# ===== Step 1 · 定住現在狀態 → 同步 main → 找兩週內 VDF/VRN 最成功狀態 → 釘 LKGC(只讀;本機只備查,不混成果) =====
#   ① 備份:本機 HEAD + 全部本機獨有提交打成 git bundle、工作樹改動 stash(不丟)、VIA_Reports 證據 zip → %USERPROFILE%\VIA_Backups
#   ② 同步:via-medic sync --apply(零 force);被衝突閘擋 → 本機獨有提交推側線分支 local-<時戳>(GitHub 留底),列出衝突檔,不硬合
#   ③ 兩週內最成功狀態:讀本機 VIA_Reports\vdf_chain · vrn_chain 的 *_latest.json / 時戳 json / LEDGER.tsv,排 GREEN 多 RED 少;每筆對回 git sha,
#      sha 在 origin/main 上 = 有依據 → 打 tag lkgc/vdf-<日期> lkgc/vrn-<日期>(只增;push tag 到 GitHub 備查)並 git worktree 到 C:\VIA_LKGC\<sha>(唯讀參照,不混入工作樹)
$ErrorActionPreference = 'Continue'
$VIA = 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'; $Repo = Split-Path $VIA -Parent
Set-Location -LiteralPath $VIA; $env:VIA_ROOT = $VIA; $env:PYTHONUTF8 = '1'; $env:PYTHONWARNINGS = 'ignore'
$stamp = Get-Date -Format yyyyMMdd_HHmmss; $bk = Join-Path $env:USERPROFILE 'VIA_Backups'; New-Item -ItemType Directory -Force -Path $bk | Out-Null
$log = Join-Path $bk "step1_$stamp.log"; function L([string]$s, [string]$c = 'Gray') { $s | Tee-Object -FilePath $log -Append | Write-Host -ForegroundColor $c }

# ① 定住現在狀態
$head0 = (git -C $Repo rev-parse --short=12 HEAD); $br = (git -C $Repo rev-parse --abbrev-ref HEAD)
git -C $Repo fetch -q origin 2>$null
$aheadBehind = (git -C $Repo rev-list --left-right --count HEAD...origin/main) -replace '\s+', '/'
L "=== ① 定住:HEAD $head0 · 分支 $br · 領先/落後 origin/main $aheadBehind ===" Cyan
git -C $Repo tag -f "pre-sync/$stamp" HEAD | Out-Null
$bundle = Join-Path $bk "local_$stamp.bundle"; git -C $Repo bundle create $bundle --all 2>&1 | Select-Object -Last 1 | Out-Null
L ("  [bundle] 全部分支與 tag → " + $bundle + " · " + [Math]::Round((Get-Item $bundle).Length / 1MB, 1) + " MB(還原:git clone " + $bundle + ")")
$dirty = @(git -C $Repo status --porcelain -uall); L ("  [工作樹] 改動/未追蹤 " + $dirty.Count + " 件" + $(if ($dirty.Count) { " → stash 'pre-sync $stamp'(不丟;git stash list 可見)" } else { "" }))
if ($dirty.Count) { git -C $Repo stash push -u -m "pre-sync $stamp" | Out-Null }
$ev = Join-Path $bk "evidence_$stamp.zip"; Compress-Archive -Path @("$VIA\VIA_Reports\vdf_chain", "$VIA\VIA_Reports\vrn_chain", "$VIA\VIA_Reports\gate", "$VIA\VIA_Reports\vcgc", "$VIA\VIA_Reports\review" | Where-Object { Test-Path $_ }) -DestinationPath $ev -CompressionLevel Fastest -ErrorAction SilentlyContinue
L ("  [證據] VIA_Reports(vdf_chain/vrn_chain/gate/vcgc/review)→ " + $ev)

# ② 同步 main
L "=== ② 同步 ===" Cyan
$mm = via-medic sync --apply 2>&1 | ForEach-Object { "" + $_ }; $mm | Where-Object { $_ -match '醫生|OK\]|RUN\]|衝突|分歧|HEAD|stash|擋下' } | ForEach-Object { L ("  " + $_) }
$head1 = (git -C $Repo rev-parse --short=12 HEAD); $ab1 = (git -C $Repo rev-list --left-right --count HEAD...origin/main) -replace '\s+', '/'
if ($ab1 -match '^0/0$') { L "  [同步] HEAD $head1 = origin/main · 完成" Green }
else {
  L "  [同步] 仍不齊:領先/落後 $ab1 → 本機獨有提交推側線分支留底,衝突檔列出(要你親手解;不 force)" Yellow
  $side = "local-$stamp"; git -C $Repo push -q origin "HEAD:refs/heads/$side" 2>&1 | Select-Object -Last 1 | ForEach-Object { L ("  [側線] " + $side + " · " + $_) }
  git -C $Repo diff --name-only --diff-filter=U 2>$null | ForEach-Object { L ("  [衝突檔] " + $_) Red }
  git -C $Repo merge-tree (git -C $Repo merge-base HEAD origin/main) HEAD origin/main 2>$null | Select-String '^changed in both|^<<<<<<<' | Select-Object -First 10 | ForEach-Object { L ("  [預測] " + $_.Line) Yellow }
}
if ($dirty.Count) { git -C $Repo stash pop 2>&1 | Select-Object -Last 1 | ForEach-Object { L ("  [stash 還原] " + $_) } }

# ③ 兩週內最成功狀態
L "=== ③ 兩週內 VDF / VRN 最成功狀態(本機證據 → 對回 origin/main 的 sha)===" Cyan
$since = (Get-Date).AddDays(-14)
function Dig($o, [string[]]$keys) { if ($null -eq $o) { return $null }; foreach ($k in $keys) { if ($o.PSObject.Properties.Name -contains $k) { return $o.$k } }; foreach ($p in $o.PSObject.Properties) { if ($p.Value -is [psobject] -and -not ($p.Value -is [string])) { $r = Dig $p.Value $keys; if ($null -ne $r) { return $r } } }; $null }
$cands = @()
foreach ($chain in @('vdf_chain', 'vrn_chain')) {
  $dir = Join-Path $VIA "VIA_Reports\$chain"; if (-not (Test-Path $dir)) { L "  [$chain] 本機沒有紀錄夾" Yellow; continue }
  foreach ($f in (Get-ChildItem $dir -Filter '*.json' -File | Where-Object { $_.LastWriteTime -ge $since -and $_.Name -notlike '*latest*' })) {
    try { $j = Get-Content $f.FullName -Raw -Encoding UTF8 | ConvertFrom-Json } catch { continue }
    $g = Dig $j @('green', 'GREEN', 'n_green', 'greens'); $r = Dig $j @('red', 'RED', 'n_red', 'reds'); $sha = Dig $j @('head', 'sha', 'sha16', 'commit', 'git_head'); $v = Dig $j @('verdict', 'lamp', 'state')
    if ($null -eq $g -and $null -eq $v) { continue }
    $cands += [pscustomobject]@{ 鏈 = $chain; 檔 = $f.Name; 時間 = $f.LastWriteTime; 綠 = [int]("0" + $g); 紅 = [int]("0" + $r); 判 = "" + $v; sha = ("" + $sha).Substring(0, [Math]::Min(12, ("" + $sha).Length)) }
  }
}
if ($cands.Count -eq 0) { L "  沒有可排名的 json(欄位名不在猜測清單;把一個 VDFCHAIN_<時戳>.json 的前 30 行貼給我,我對準欄位)" Yellow }
$best = @()
foreach ($chain in @('vdf_chain', 'vrn_chain')) {
  $top = $cands | Where-Object 鏈 -eq $chain | Sort-Object -Property @{e = '綠'; desc = $true }, @{e = '紅'; desc = $false }, @{e = '時間'; desc = $true } | Select-Object -First 3
  $top | ForEach-Object { L ("  [$chain] 綠 " + $_.綠 + " 紅 " + $_.紅 + " 判 " + $_.判 + " · " + $_.時間.ToString('MM-dd HH:mm') + " · sha " + $_.sha + " · " + $_.檔) }
  if ($top) { $best += $top[0] }
}
foreach ($b in $best) {
  if (-not $b.sha) { L ("  [" + $b.鏈 + "] 最佳那筆沒記 sha → 無法對回 main,不釘(只列)") Yellow; continue }
  git -C $Repo merge-base --is-ancestor $b.sha origin/main 2>$null; $onMain = ($LASTEXITCODE -eq 0)
  if (-not $onMain) { L ("  [" + $b.鏈 + "] sha " + $b.sha + " 不在 origin/main 上(本機獨有或被改寫)→ 不釘,有疑") Yellow; continue }
  $tag = "lkgc/" + ($b.鏈 -replace '_chain', '') + "-" + $b.時間.ToString('yyyyMMdd')
  git -C $Repo tag -f $tag $b.sha | Out-Null; git -C $Repo push -q origin $tag 2>&1 | Out-Null
  $wt = "C:\VIA_LKGC\" + $b.sha; if (-not (Test-Path $wt)) { git -C $Repo worktree add -q --detach $wt $b.sha 2>&1 | Select-Object -Last 1 | Out-Null }
  L ("  [LKGC] " + $tag + " → " + $b.sha + "(在 main 上,有依據)· 唯讀參照 " + $wt + " · 綠 " + $b.綠 + " 紅 " + $b.紅) Green
}
L "=== 畢 · 紀錄 $log · 還原依據:tag pre-sync/$stamp · bundle · stash · evidence zip ===" Cyan
}
