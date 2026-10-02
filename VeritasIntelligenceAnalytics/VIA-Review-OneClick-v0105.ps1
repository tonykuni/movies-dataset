&{
# =====================================================================================
# VIA-Review-OneClick-v0105.ps1 — 一貼可用 · 一個指令整合全部檢視 · 不關 PS 視窗
#   操作員(2026-10-02):「VIA-Review-OneClick-v0104 + VIA_PanoramaCheck_ALL_v0160 整合優化 指令整合為一」
#   v0104 把 Invoke-VIA-Review / Register v0266 內嵌寫檔再推;v0105 起兩支(含 v0105 總檢)已在 GitHub(main),本檔不再內嵌、不寫檔:
#   ① 進倉 → git pull --ff-only(只快轉;不 force、不 reset;-Sync 才交拉齊醫生 CGC_MDL143 sync --apply)
#   ② 本視窗載入短指令(Register-VIA-Commands 尾版,≥ v0266:via-review / 總檢)
#   ③ 跑 via-review 尾版(≥ v0105)= 一個指令同時做
#        VIA 倉:⓪ 進入環境 · ① Git · ② 撞名 · ③ 環境(-Install 才補裝)· ④ SDD / SSOT / 編號註冊 · ⑤ AST 錨點 · ⑥ 清單 · ⑦ 全部優化一回 · ⑧ 多頁矩陣 + 貼回包
#        VIA-VERB-ENGINE:⑨a health · ⑨b global_read · ⑨c fullcheck · ⑨d 收尾鎖(原五支獨立入口併進同一輪、同一張矩陣)
#   全程不 exit 主控台;跑完 via-review / 總檢 在本視窗可直接再打。
# =====================================================================================
$Install    = $false   # $true = 環境總判非 GREEN 時接 MDL135 → MDL137 補裝(= 你親手開閘)
$Sync       = $false   # $true = Git 有分叉交拉齊醫生 MDL143 sync --apply(零 force)
$Lists      = $false   # $true = 加跑清單七步(v0108 原表,經 VCGC)
$Optimize   = $true    # 再優化一次:全部優化一回(RealTestCore 尾版,上限 20 分鐘);不要就改 $false
$VerbEngine = ''       # VIA-VERB-ENGINE 的 verb-engine 夾;留空 = VIA_VERB_ENGINE 環境變數 → %USERPROFILE%\VIA-VERB-ENGINE\verb-engine
$NoVerb     = $false   # $true = 不檢 VIA-VERB-ENGINE
$ErrorActionPreference = 'Continue'
$VIA = if ($env:VIA_CELERITAS_ROOT) { Split-Path $env:VIA_CELERITAS_ROOT -Parent } else { 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics' }
if (-not (Test-Path -LiteralPath (Join-Path $VIA 'supportive modules\registry'))) { Write-Host ("找不到 VIA 倉根(要有 supportive modules\registry):{0}" -f $VIA) -ForegroundColor Red; return }
$Repo = Split-Path $VIA -Parent
Set-Location -LiteralPath $VIA; $env:VIA_ROOT = $VIA; $env:PYTHONUTF8 = '1'
Write-Host ("=== [VIA-Review-OneClick v0105] 倉根 " + $VIA + "(已 Set-Location 進倉)===") -ForegroundColor Cyan

# ---------------------------------------------------------------- ① 只快轉拉取(不 force · 不 reset)
$branch = (& git -C $Repo rev-parse --abbrev-ref HEAD 2>&1 | Select-Object -Last 1)
$pl = @(& git -C $Repo pull --ff-only 2>&1 | ForEach-Object { '' + $_ })
if ($LASTEXITCODE -eq 0) { Write-Host ("  [拉] " + $branch + " 已快轉:" + ((@($pl) | Select-Object -Last 1) -join '')) -ForegroundColor Green }
elseif ($Sync) {
    Write-Host "  [拉齊] 不能快轉 → 交拉齊醫生 CGC_MDL143 sync --apply(零 force / 零 reset)" -ForegroundColor Yellow
    $reg = Join-Path $VIA 'supportive modules\registry'
    $vc = Get-ChildItem -LiteralPath $reg -Filter 'CGC_MDL149_VeritasCentralGovernanceConsole_v*.py' -File -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
    $pyExe = (Get-Command python -ErrorAction SilentlyContinue | Where-Object { $_.Source -notmatch 'WindowsApps' } | Select-Object -First 1).Source
    $keepFrom = $env:VIA_FROM_VCGC; $env:VIA_FROM_VCGC = 'YES'
    if ($vc -and $pyExe) { $mm = @(& $pyExe $vc.FullName run --family core CGC_MDL143_MergeMedic sync --apply 2>&1 | ForEach-Object { '' + $_ }); Write-Host ('  [拉齊] MergeMedic rc ' + $LASTEXITCODE + ' · ' + ((@($mm) | Select-Object -Last 2) -join ' | ')) -ForegroundColor Yellow }
    else { Write-Host '  [紅] 找不到 VCGC 或 python,拉齊沒跑' -ForegroundColor Red }
    $env:VIA_FROM_VCGC = $keepFrom
}
else { Write-Host ("  [黃] 不能快轉(本機有分叉或改動):" + ((@($pl) | Select-Object -Last 2) -join ' | ') + " → 照本機現有版本檢;要拉齊把上面 `$Sync 改 `$true") -ForegroundColor Yellow }

# ---------------------------------------------------------------- ② 本視窗載入短指令(Register 尾版)
$regFile = Get-ChildItem -LiteralPath $VIA -Filter 'Register-VIA-Commands-v*.ps1' -File -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
$rvFile  = Get-ChildItem -LiteralPath $VIA -Filter 'Invoke-VIA-Review-v*.ps1' -File -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
if (-not $rvFile -or $rvFile.Name -lt 'Invoke-VIA-Review-v0105.ps1') {
    Write-Host ("  [紅] 總檢尾版不是 v0105 以上(" + $(if ($rvFile) { $rvFile.Name } else { '不在' }) + "):先讓 git 拉到 main(把 `$Sync 改 `$true 再貼一次)") -ForegroundColor Red
    return
}
if ($regFile) { $null = . $regFile.FullName; Write-Host ("  [載] " + $regFile.Name + " → via-review / 總檢 已可在本視窗直接打") -ForegroundColor Green }
else { Write-Host '  [黃] 找不到 Register-VIA-Commands-v*.ps1,只跑這一次總檢(短指令沒載)' -ForegroundColor Yellow }

# ---------------------------------------------------------------- ③ 一個指令跑全部(VIA 倉 + VIA-VERB-ENGINE)
$rvArgs = @{}
if ($Install)    { $rvArgs['Install']    = $true }
if ($Sync)       { $rvArgs['Sync']       = $true }
if ($Lists)      { $rvArgs['Lists']      = $true }
if ($Optimize)   { $rvArgs['Optimize']   = $true }
if ($NoVerb)     { $rvArgs['NoVerb']     = $true }
if ($VerbEngine) { $rvArgs['VerbEngine'] = $VerbEngine }
Write-Host ("=== 跑 " + $rvFile.Name + " " + (($rvArgs.Keys | ForEach-Object { '-' + $_ }) -join ' ') + " ===") -ForegroundColor Cyan
& $rvFile.FullName @rvArgs
$rc = $LASTEXITCODE
Write-Host ("=== [VIA-Review-OneClick v0105] 畢 · via-review rc " + $rc + "(0 全綠 · 2 有發現 · 1 有紅)· 本視窗已可直接打 via-review / 總檢 ===") -ForegroundColor $(if ($rc -eq 0) { 'Green' } elseif ($rc -eq 2) { 'Yellow' } else { 'Red' })
}
