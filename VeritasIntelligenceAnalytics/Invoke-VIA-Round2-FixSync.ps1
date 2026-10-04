# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
# AI 產出必須接入模板。只動 $PID,關閉即還原。L106:PS 帶兩章 · PY 帶 ACCEL-BRIDGE。
# ===== [VIA:PS-ACCEL:v0101] PS 25 加速器橋(B531 全樹導入;graceful 缺席零影響) =====
try { $VIAPSAccelProbe = if ($PSScriptRoot) { $PSScriptRoot } else { 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics' }
  while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) { $m = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"; if (Test-Path $m) { . $m; break }; $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent } } catch { }
# ===== [VIA:PS-ACCEL:END] =====
# Invoke-VIA-Round2-FixSync.ps1 — 全景式檢試(AST 定位)→ 修一輪 → 備份 → 更新 → sync all(操作員 2026-10-03)
#   根因 ①(本輪最大):鎖冊 token 工具 CGC_MDL158 v0117 的 sha 是 LF 位元組(8172249d5137),工作站 git autocrlf 在合併時把它改成 CRLF(e24773d34d96)
#            → CGC_MDL253 ToolingInventory 擋下 → VDF / VRN 兩個 SystemManager 自測全紅。修法:.gitattributes 把鎖冊七件標 -text(倉裡 VTR / v0160A 早有同樣先例),
#            並用 git 物件原始位元組重寫工作樹那幾支(不經 smudge),tools status 要回 sha_ok 全 true。
#   根因 ②:交接閘「未登 2 支」→ FunctionInventory v0135(+C-github_panorama · +P-step1;只增)。
#   根因 ③(我的):上一輪 Step 函數用 $script:rows += 在一次貼區塊裡撞到外層同名物件 → 改 List.Add。
&{
$ErrorActionPreference = 'Continue'
$VIA = 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'; $Repo = Split-Path $VIA -Parent
$dl = "$env:USERPROFILE\Downloads"; $reg = "$VIA\supportive modules\registry"
Set-Location -LiteralPath $VIA; $env:PYTHONUTF8 = '1'; $env:PYTHONWARNINGS = 'ignore'; $env:VIA_NO_OPEN = '1'
$stamp = Get-Date -Format yyyyMMdd_HHmmss; $Out = "$VIA\VIA_Reports\review\round"; New-Item -ItemType Directory -Force -Path $Out | Out-Null
$log = "$Out\ROUND2_$stamp.log"; $rows = [System.Collections.Generic.List[object]]::new()
function Step([string]$id, [string]$name, [scriptblock]$b) { $t = Get-Date; $o = @(& $b 2>&1 | ForEach-Object { "" + $_ }); $rc = $LASTEXITCODE
  "=== [$id] $name ===" | Add-Content $log; $o | Add-Content $log
  $last = (@($o | Where-Object { $_ -match '\[(GREEN|RED|YELLOW|OK|FAIL|WARN|NODATA|計)|總判|sha_ok|RuntimeError|Traceback' } | Select-Object -Last 1) -join '')
  $lamp = if ($rc -eq 0) { 'GREEN' } elseif ($rc -eq 2) { 'YELLOW' } elseif ($rc -eq 3) { 'ABSENT' } elseif ($rc -eq 4) { 'GATE' } else { 'RED' }
  $rows.Add([pscustomobject]@{ 步=$id; 名=$name; 燈=$lamp; rc=$rc; 秒=[int]((Get-Date)-$t).TotalSeconds; 判決=$last.Substring(0,[Math]::Min(140,$last.Length)) })
  Write-Host ("  [$id] $name · $lamp · rc $rc · " + [int]((Get-Date)-$t).TotalSeconds + "s") -ForegroundColor $(if ($lamp -eq 'GREEN') {'Green'} elseif ($lamp -eq 'RED') {'Red'} else {'Yellow'}) }

# ⓪ 備份(改之前):鎖冊 + registry 冊 + .gitattributes + 兩個 SystemManager
$bk = "$env:USERPROFILE\VIA_Backups\round2_$stamp"; New-Item -ItemType Directory -Force -Path $bk | Out-Null
Copy-Item "$Repo\.gitattributes" $bk -Force -ErrorAction SilentlyContinue; Copy-Item "$reg\VIA_ToolVersion_Lock_v*.json" $bk -Force; Copy-Item "$reg\VIA_VCGC_FunctionInventory_SSOT_v0134.json" $bk -Force
git -C $Repo tag -f "pre-round2/$stamp" HEAD | Out-Null
Write-Host "  [備份] $bk · tag pre-round2/$stamp" -ForegroundColor DarkGray

# ① 根因:鎖冊位元組 vs CRLF。讀鎖冊路徑 → .gitattributes 追加 -text(空白照倉慣例寫成 *)→ 用 git 物件原始位元組重寫工作樹 → 驗 sha
$lock = Get-Content "$reg\VIA_ToolVersion_Lock_v0100.json" -Raw -Encoding UTF8 | ConvertFrom-Json
$pinned = @('accelerator','network','layout','nlp','token','frame','praddle') | ForEach-Object { $lock.$_.path } | Where-Object { $_ }
$ga = "$Repo\.gitattributes"; $gaText = if (Test-Path $ga) { Get-Content $ga -Raw -Encoding UTF8 } else { '' }
$added = @()
foreach ($p in $pinned) { $pat = ($p -replace ' ', '*'); if ($gaText -notmatch [regex]::Escape($pat)) { $added += "$pat -text" } }
if ($added.Count) { Add-Content $ga -Value (@("", "# 側線 2026-10-03:鎖冊七件(VIA_ToolVersion_Lock)位元鎖 —— 鎖的 sha 是原始位元,autocrlf 轉 CRLF 就對不上(VTR / v0160A 同理)") + $added) -Encoding UTF8; Write-Host ("  [.gitattributes] +" + $added.Count + " 行 -text") -ForegroundColor Cyan }
$fixed = 0
foreach ($p in $pinned) {
  $full = Join-Path $Repo $p; if (-not (Test-Path -LiteralPath $full)) { continue }
  $want = ($lock.PSObject.Properties.Value | Where-Object { $_.path -eq $p }).sha256
  $have = (Get-FileHash -LiteralPath $full -Algorithm SHA256).Hash.ToLower()
  if ($want -and $have -ne $want) {
    cmd /c ("git -C ""$Repo"" show HEAD:""$p"" > ""$full.lf"" 2>nul") | Out-Null
    $lf = (Get-FileHash -LiteralPath "$full.lf" -Algorithm SHA256).Hash.ToLower()
    if ($lf -eq $want) { Move-Item -LiteralPath "$full.lf" -Destination $full -Force; $fixed++; Write-Host ("  [位元還原] " + (Split-Path $p -Leaf) + " CRLF→LF · sha 對上鎖冊") -ForegroundColor Green }
    else { Remove-Item -LiteralPath "$full.lf" -Force -ErrorAction SilentlyContinue; Write-Host ("  [紅] " + (Split-Path $p -Leaf) + " 連 git 物件都對不上鎖(鎖 " + $want.Substring(0,12) + " · 物件 " + $lf.Substring(0,12) + ")→ 真的換過版,要走 via-vcgc tools activate") -ForegroundColor Red }
  }
}
Write-Host ("  [鎖冊] 七件:還原 " + $fixed + " 支") -ForegroundColor Cyan
Step '1' 'tools status(sha_ok 應全 true)' { via-vcgc tools status }

# ② 登冊:FunctionInventory v0135(+C-github_panorama · +P-step1)
if (Test-Path "$dl\VIA_VCGC_FunctionInventory_SSOT_v0135.json") { Copy-Item "$dl\VIA_VCGC_FunctionInventory_SSOT_v0135.json" "$reg\" -Force; Write-Host "  [登冊] FunctionInventory v0135 進 registry" -ForegroundColor Cyan }
else { Write-Host "  [登冊] Downloads 沒有 v0135,略過(交接閘會繼續說未登 2 支)" -ForegroundColor Yellow }

# ③ 重跑上一輪紅的:兩個 SystemManager 自測 · DataFrameLock check
Step '3a' 'VDF_SystemManager --selftest' { via-vcgc run --family vdf VDF_SystemManager --selftest }
Step '3b' 'VRN_SystemManager --selftest' { via-vcgc run --family vrn VRN_SystemManager --selftest }
Step '3c' 'CGC_MDL249 DataFrameLock check' { via-vcgc run --family core CGC_MDL249_DataFrameLock check }
Step '3d' 'test --only C-github_panorama' { via-vcgc test --only C-github_panorama }

# ④ 全景式檢試(AST 定位):GitHub 全景(origin/main)+ 本機 via-review(PS Parser / PAN / Python compile 錨點)
Step '4a' 'GitHub 全景 scan' { via-vcgc run --family core CGC_MDL255_GitHubPanorama scan --ref origin/main --no-open }
Step '4b' 'via-review(錨點 · 多頁矩陣)' { via-review -NoEnter -NoClipboard -NoOpen }
Step '4c' 'handoff check(交接閘)' { via-vcgc handoff check }

# ⑤ 更新 · sync all:衝突閘 → 拉齊 → 推(只帶 .gitattributes · 鎖冊七件位元還原 · FunctionInventory v0135)
Step '5a' 'guard' { via-vcgc guard }
$files = @('.gitattributes', 'VeritasIntelligenceAnalytics/supportive modules/registry/VIA_VCGC_FunctionInventory_SSOT_v0135.json') + @($pinned) | Where-Object { Test-Path (Join-Path $Repo $_) }
& git -C $Repo add -- @files 2>&1 | Out-Null
& git -C $Repo commit -q -m "Round2 ($stamp): .gitattributes -text for the 7 locked tools (CRLF broke lock sha), locked tools restored byte-exact, FunctionInventory v0135 (+C-github_panorama, +P-step1); append-only" -- @files 2>&1 | Out-Null
Step '5b' 'via-medic sync --apply' { via-medic sync --apply }
$branch = (& git -C $Repo rev-parse --abbrev-ref HEAD); $pu = & git -C $Repo push origin $branch 2>&1
if ($LASTEXITCODE -eq 0) { Write-Host ("  [推] " + $branch + " · " + (& git -C $Repo rev-parse --short=12 HEAD)) -ForegroundColor Green }
else { $side = "round2-$stamp"; & git -C $Repo push origin "HEAD:refs/heads/$side" 2>&1 | Out-Null; Write-Host ("  [推] 改推側線 " + $side + "(衝突要你解)") -ForegroundColor Yellow }

$pack = @("# ROUND2 $stamp") + ($rows | ForEach-Object { "- [" + $_.燈 + "] " + $_.步 + " " + $_.名 + " · rc " + $_.rc + " · " + $_.秒 + "s · " + $_.判決 })
$pack | Set-Content "$Out\ROUND2_${stamp}_paste.md" -Encoding UTF8; try { ($pack -join "`n") | Set-Clipboard } catch { }
$rows | Format-Table 步,名,燈,rc,秒 -AutoSize | Out-String -Width 160 | Write-Host
Write-Host "貼回包已進剪貼簿 · 全文 $log · 鎖冊備份 $bk" -ForegroundColor Green
}
