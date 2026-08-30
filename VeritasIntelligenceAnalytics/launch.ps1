# launch.ps1 — VIA 非阻塞啟動器(批201;Mega-Prompt 令)
# 「不關閉、不阻塞、不卡斷」:boot 全鏈丟背景 Job,終端立即返還;
# UI Matrix+樞紐頁開瀏覽器;進度=背景 log 即時可查。
# ===== [VIA:PS-ACCEL:v0100] PS 20 加速器橋(批255 全樹導入;graceful 缺席零影響) =====
try {
    $VIAPSAccelProbe = $PSScriptRoot
    while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) {
        $VIAPSAccelMod = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"
        if (Test-Path $VIAPSAccelMod) { . $VIAPSAccelMod; break }
        $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent
    }
} catch { }
# ===== [VIA:PS-ACCEL:END] =====
$VIA = $PSScriptRoot
$env:VIA_NET_CONSENT = "YES"; $env:VIA_SCRAPE_CONSENT = "YES"
Write-Host "[launch] VIA 非阻塞啟動:boot 全鏈 → 背景 Job(終端不阻塞)" -ForegroundColor Cyan
$job = Start-Job -Name "VIA_Boot" -ScriptBlock {
    param($root)
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root "supportive modules\registry\via_boot_update.ps1")
} -ArgumentList $VIA
Write-Host ("[launch] 背景 Job Id={0}(查進度:Receive-Job {0} -Keep;log 於 VIA_Reports\boot_update_logs\)" -f $job.Id)
$hub = Join-Path $VIA "supportive modules\ui_support\VIA_UI_SystemHub_v0100.html"
$mtx = Join-Path $VIA "supportive modules\ui_support\VIA_UI_GovernanceMatrix_v0100.html"
$dck = Join-Path $VIA "supportive modules\ui_support\VIA_UI_CommandDeck_v0100.html"
if (Test-Path $hub) { Start-Process $hub }
if (Test-Path $mtx) { Start-Process $mtx }
if (Test-Path $dck) { Start-Process $dck }
Write-Host "[launch] UI 已開(樞紐+治理矩陣);終端可繼續操作=非阻塞" -ForegroundColor Green
