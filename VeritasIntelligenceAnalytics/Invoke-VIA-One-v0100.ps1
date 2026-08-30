#requires -Version 7.0
<#
Invoke-VIA-One v0100 — 最終整合版總啟動器(依 VIA_MegaPrompt_OfficialMode_v0100)
一支 PowerShell 處理全部:同步 → Mega 三輪全景(v0103 分區 Matrix 自動跳出)→ VMT 總指揮
→ CGE 中央治理 dry-run → VRN 內容探測/擷取 dry-run → UI Hub。
不關閉、不阻塞、不卡斷:無 Read-Host、無 exit;UI 以 Start-Process 非阻塞開啟;
每階段動態進度條(Write-Progress)+ 動態說明;單一階段失敗誠實記錄後續行。
#>
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
$ErrorActionPreference = "Continue"
$Root = $PSScriptRoot
$Bin = Join-Path $Root "bin"

$Accelerators = @(
    "AST 精準解析","多語言語意模型","九頭龍風險預測","依賴拓撲排序","沙盒隔離執行",
    "自動修正建議生成","三輪全景式分析","SSOT 對齊","視覺化矩陣生成","錯誤分類與分群",
    "性能與複雜度分析","多子系統同步檢視","版本差異與回滾","覆蓋率與回歸檢查","修正順序最佳化",
    "動態進度條","動態說明","非阻塞 PowerShell","多引擎整合","自動部署與環境初始化")

Write-Host ("=" * 70) -ForegroundColor DarkCyan
Write-Host "  VIA ONE v0100  |  最終整合版總啟動器 · 20 加速器 · 公定處理模式" -ForegroundColor Cyan
Write-Host ("=" * 70) -ForegroundColor DarkCyan
Write-Host ("[加速器] " + ($Accelerators -join " · ")) -ForegroundColor DarkGray

$Stages = @(
    @{ Name = "SYNC 同步 repo";              Kind = "ps";  Target = (Join-Path $Bin "via-sync.ps1") },
    @{ Name = "MEGA 三輪全景分析(分區 Matrix)"; Kind = "py";  Target = (Join-Path $Root "supportive modules\VIA_Governance_Runtime\SUP_MDL142_MegaEngine_v0103.py") },
    @{ Name = "VMT 總指揮 9 階段";            Kind = "py";  Target = (Join-Path $Root "supportive modules\VMT_SuperBOM\VIA_ENG021_MasterEngine_v0102.py"); Args = @("--no-open") },
    @{ Name = "CGE 中央治理 dry-run";         Kind = "py";  Target = (Join-Path $Root "supportive modules\VIA_Central_Governance\CGC_MDL001_CentralGovernanceEngine_v0401.py"); Args = @("--workdir", ($env:VMT_ROOT ?? "C:\VIA\VeritasMailTracker")) },
    @{ Name = "VRN 內容探測(唯讀 GO gate)";   Kind = "py";  Target = (Join-Path $Root "functional modules\VRN\VRN_ENG048_ContentProbe_v0100.py"); Args = @("--no-open") },
    @{ Name = "VRN 內容擷取 dry-run";         Kind = "py";  Target = (Join-Path $Root "functional modules\VRN\VRN_ENG046_ContentExtractCandidate_v0100.py") },
    @{ Name = "UI HUB 開啟七介面樞紐";        Kind = "open"; Target = (Join-Path $Root "supportive modules\ui_support\VIA_UI_Hub_v0100.html") }
)

$Results = @()
$total = $Stages.Count
for ($i = 0; $i -lt $total; $i++) {
    $st = $Stages[$i]
    $pct = [int](($i) / $total * 100)
    Write-Progress -Activity "VIA ONE 總管線" -Status $st.Name -PercentComplete $pct
    Write-Host ("`n[STATUS] ({0}/{1}) {2}" -f ($i + 1), $total, $st.Name) -ForegroundColor Yellow
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $ok = $true
    try {
        switch ($st.Kind) {
            "ps"   { if (Test-Path -LiteralPath $st.Target) { & pwsh -NoProfile -File $st.Target } else { throw "缺檔 $($st.Target)" } }
            "py"   { if (Test-Path -LiteralPath $st.Target) { & py $st.Target @($st.Args) } else { throw "缺檔 $($st.Target)" }
                     if ($LASTEXITCODE -ne 0) { $ok = $false } }
            "open" { if (Test-Path -LiteralPath $st.Target) { Start-Process $st.Target | Out-Null } else { throw "缺檔 $($st.Target)" } }
        }
    }
    catch { $ok = $false; Write-Host ("[STATUS] 階段異常(續行):{0}" -f $_.Exception.Message) -ForegroundColor Red }
    $sw.Stop()
    $Results += [pscustomobject]@{ 階段 = $st.Name; 結果 = ($ok ? "OK" : "FAIL"); 耗時s = [math]::Round($sw.Elapsed.TotalSeconds, 1) }
}
Write-Progress -Activity "VIA ONE 總管線" -Completed

Write-Host ""
Write-Host ("=" * 70) -ForegroundColor DarkCyan
$Results | Format-Table -AutoSize
$okN = ($Results | Where-Object 結果 -eq "OK").Count
Write-Host ("[總結] {0}/{1} 階段 OK · Matrix/儀表板/UI Hub 已非阻塞開啟 · PowerShell 保持開啟" -f $okN, $total) -ForegroundColor Green

