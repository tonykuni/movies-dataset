# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
<#
Start-VCGC-v0101.ps1 — 一支 PS 啟用 VCGC(只啟 VCGC;VDF / VRN 各自的入口不經這支 · L119)。
v0101(2026-11-28 主機實錄):v0100 照 VIA_REPO 取到另一份副本(C:\Users\<你>\movies-dataset),那份沒有 CGC_SystemManager 前版,
  v0122 一載入就倒。本版:只認 registry 裡有直接前版 CGC_SystemManager_v0121.py 的倉;每個候選印一行「用 / 不用 · 為什麼」;
  前一次放錯倉的 v0122(雜湊是本批出的那兩版才算)從那份副本移除。作廢:Start-VCGC-v0100.ps1。

操作員 2026-11-28:「activate the system with a py code with accelerating module, and activate py with a ps code」。
PS 只做三件事(L117 · VCGC-REQ266):
  ① 落檔:VCGC 管理器尾版 CGC_SystemManager_v0122.py 不在倉裡時,從本檔同一夾 / 下載夾取來放進 registry
     (先把 CRLF 統一成 LF 再核 SHA-256,對不上就不放;倉裡已有同名檔 → 不覆蓋)
  ② 叫一個 python 動詞:CGC_SystemManager 尾版 launch(順序 · 道數 · 心跳 · 燈 · 收據全在 Python)
  ③ 開它產的頁:由 python 開 VCGC_Overview_latest.html(--no-open 可關)
倉根自己找:VIA_REPO → 本檔所在夾 → 家目錄下 OneDrive\Documents\movies-dataset → 家目錄下 movies-dataset;只認 registry 有直接前版的那份。不用打路徑。
用法:pwsh -NoProfile -File Start-VCGC-v0101.ps1 [--plan] [--full] [--lanes 3..6] [--no-open] [--timeout 秒]
與 Start-VIA-v0100.ps1 的關係:那支是 VCGC + 備份 + VDF 一起跑(HostBoot up),照舊可用;這支只啟 VCGC。
#>
param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Rest)
# ===== [VIA:PS-ACCEL:v0101] PS 25 加速器橋(B531 全樹導入;graceful 缺席零影響) =====
try {
    $VIAPSAccelProbe = $PSScriptRoot
    while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) {
        $VIAPSAccelMod = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"
        if (Test-Path $VIAPSAccelMod) { . $VIAPSAccelMod; break }
        $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent
    }
} catch { Write-Verbose 'PS accel bridge absent (graceful)' }
# ===== [VIA:PS-ACCEL:END] =====
$SmName = 'CGC_SystemManager_v0122.py'
$SmPrior = 'CGC_SystemManager_v0121.py'
$SmSha = '3f8c1ed8379a0742d8db5cf9303e05d23de09e34c51b2f05eed1f321b257562b'
$OurOld = @('0556e4353533bc4b5e55ebe232105687d5973d7adbc7744fceb174911b8d71d8', $SmSha)   # 本批出過的位元組(放錯倉時才准移除)
$env:PYTHONUTF8 = '1'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { Write-Verbose 'console encoding unchanged' }
function Get-LfSha([string]$p) {
    $lf = ([IO.File]::ReadAllText($p, [Text.Encoding]::UTF8)) -replace "`r`n", "`n"
    -join ([Security.Cryptography.SHA256]::Create().ComputeHash([Text.UTF8Encoding]::new($false).GetBytes($lf)) | ForEach-Object { $_.ToString('x2') })
}
$cands = @($env:VIA_REPO, $PSScriptRoot, (Join-Path $HOME 'OneDrive\Documents\movies-dataset'), (Join-Path $HOME 'movies-dataset')) | Where-Object { $_ } | Select-Object -Unique
$via = $null
foreach ($c in $cands) {
    foreach ($v in @($c, (Join-Path $c 'VeritasIntelligenceAnalytics'))) {
        $r = Join-Path $v 'supportive modules\registry'
        if (-not (Test-Path -LiteralPath $r)) { continue }
        $orphan = Join-Path $r $SmName
        if (Test-Path -LiteralPath (Join-Path $r $SmPrior)) {
            if (-not $via) { $via = (Resolve-Path -LiteralPath $v).Path; Write-Host "[倉] 用 $via(有 $SmPrior)" -ForegroundColor Green }
            else { Write-Host "[倉] 不用 $v(已選定 $via)" -ForegroundColor DarkGray }
        } else {
            Write-Host "[倉] 不用 $v(registry 沒有 $SmPrior;不是主工作倉)" -ForegroundColor Yellow
            if ((Test-Path -LiteralPath $orphan) -and ($OurOld -contains (Get-LfSha $orphan))) {
                Remove-Item -LiteralPath $orphan -Force
                Write-Host "[清] 移除上次放錯倉的 $orphan(雜湊是本批的)" -ForegroundColor Yellow
            }
        }
    }
}
if (-not $via) { Write-Host "[RED] 沒有一份倉的 registry 有 $SmPrior(先在主工作倉 git pull;或設 VIA_REPO 指向它)" -ForegroundColor Red; exit 1 }
$reg = Join-Path $via 'supportive modules\registry'
$dst = Join-Path $reg $SmName
$have = if (Test-Path -LiteralPath $dst) { Get-LfSha $dst } else { $null }
if ($have -ne $SmSha) {
    if ($have -and ($OurOld -notcontains $have)) { Write-Host "[RED] $dst 已存在且不是本批的位元組,不覆蓋" -ForegroundColor Red; exit 1 }
    $src = @($PSScriptRoot, (Join-Path $HOME 'Downloads')) | Where-Object { $_ } | ForEach-Object { Join-Path $_ $SmName } |
        Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    if (-not $src) { Write-Host "[RED] 本檔同夾與下載夾都沒有 $SmName" -ForegroundColor Red; exit 1 }
    if ((Get-LfSha $src) -ne $SmSha) { Write-Host "[RED] $src 的 SHA-256 對不上(要下載新的那一份),不放進倉" -ForegroundColor Red; exit 1 }
    $lf = ([IO.File]::ReadAllText($src, [Text.Encoding]::UTF8)) -replace "`r`n", "`n"
    [IO.File]::WriteAllText($dst, $lf, [Text.UTF8Encoding]::new($false))
    Write-Host "[落檔] $SmName → $reg(SHA-256 已核;未追蹤的新檔,PR 合併後先刪掉它再 git pull)" -ForegroundColor Yellow
}
$sm = Get-ChildItem -LiteralPath $reg -Filter 'CGC_SystemManager_v*.py' | Sort-Object Name | Select-Object -Last 1
$py = @(if (Get-Command py -ErrorAction SilentlyContinue) { 'py', '-3' } else { 'python' })
if (-not $Rest) { $Rest = @() }
if (-not $Host.UI.SupportsVirtualTerminal) { $Rest += '--plain' }
$pyArgs = @($py | Select-Object -Skip 1) + @('-X', 'utf8', $sm.FullName, 'launch') + $Rest
$rc = 1
Push-Location -LiteralPath (Split-Path $via -Parent)
try {
    & $py[0] @pyArgs
    $rc = $LASTEXITCODE
} finally { Pop-Location }
exit $rc
