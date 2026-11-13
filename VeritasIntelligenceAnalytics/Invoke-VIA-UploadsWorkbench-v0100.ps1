#Requires -Version 7.0
# =====================================================================================
# Invoke-VIA-UploadsWorkbench v0100 — 下載夾 → 挑必要檔 → 暫存 → 加速器包住跑 VIA_UploadsWorkbench 尾版 → 離線 HTML(0 token)
#   操作員 2026-11-10:「整合在一起 自建HTML U/I不燒任何TOKEN」「你覺得必要的用 ps 加加速器抓取」「activate vcgc mcp to files」「ps 7.6.9」
#   ① 加速器:PS-ACCEL 橋 + VeritasCeleritas.PS7(點源);有 Invoke-VIACeleritasScoped(短令冊)就包住 Python 那一步,沒有就照實說直接跑。
#   ② 只挑 20 份正本(含 Windows「 (n)」複本)複製到暫存夾;下載夾本身不動、不刪、不改名。
#   ③ 跑 docs\handoff\ai\VIA_UploadsWorkbench_v*.py 尾版:SHA-256 · 側檔 / 交接收據釘選核對 · 審查包包內 SHA256SUMS ·
#      xlsx → 鎖定 U/I(review\VIA_Workbench_LockSite_v0106_4,位元組鎖)各系統頁 + index.html。不執行任何上傳的 .py / .ps1 / .html。
#   ④ 收據複製到 VIA_Reports\uploads\UPLOADS_latest.json → VCGC MCP(CGC_MDL279 v0103 起)資源 via://uploads/latest 讀得到。
#   ⑤ -McpConfig 只印 VCGC MCP 用戶端設定;-ActivateMcp 才合併進 Claude Desktop 設定(先備份原檔)。
#   邊界(L123 · L125):只讀證據、不寫任何系統的冊 / 正本 / 號;不連網;不代開同意閘。
# 用法(PowerShell 7.x;腳本在 VIA 根,從哪個資料夾執行都可以):
#   & "C:\Users\tonyk\OneDrive\Documents\VeritasIntelligenceAnalytics\Invoke-VIA-UploadsWorkbench-v0100.ps1"
#   參數:-Downloads <夾> · -Out <夾> · -NoOpen · -KeepStage · -McpConfig · -ActivateMcp
# 結束碼:0 = 出頁且無 RED · 1 = 出頁但有 RED(同名異內容 / 側檔或釘選值不符)· 2 = 沒出頁(缺檔 / 鎖站不過 / Python 錯)
# =====================================================================================
[CmdletBinding()]
param(
    [string]$Downloads = (Join-Path $HOME 'Downloads'),
    [string]$Out = (Join-Path (Join-Path $HOME 'Downloads') 'VIA_Uploads_Workbench'),
    [switch]$NoOpen,
    [switch]$KeepStage,
    [switch]$McpConfig,
    [switch]$ActivateMcp
)
# ===== [VIA:PS-ACCEL:v0101] PS 25 加速器橋(B531 全樹導入;graceful 缺席零影響) =====
try {
    $VIAPSAccelProbe = $PSScriptRoot
    while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) {
        $VIAPSAccelMod = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"
        if (Test-Path $VIAPSAccelMod) { . $VIAPSAccelMod; break }
        $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent
    }
} catch { }
# ===== [VIA:PS-ACCEL:END] =====

$ErrorActionPreference = 'Stop'
$VIA = $PSScriptRoot
$StartDir = (Get-Location).Path
$Stage = $null
$rc = 2
try {
    Set-Location -LiteralPath $VIA
    $accelNote = "正主缺,略過"
    try {
        $join = Join-Path $VIA "supportive modules\ps7\VeritasCeleritas.PS7.ps1"
        if (Test-Path -LiteralPath $join) { . $join; $accelNote = "套對 $($script:CeleritasPS7.Version) · 已套" }
    } catch { $accelNote = "正主載入失敗,略過" }
    $hasScoped = [bool](Get-Command Invoke-VIACeleritasScoped -ErrorAction SilentlyContinue)
    Write-Host ("  [加速器] " + $accelNote + " · Scoped " + ($(if ($hasScoped) { "有,包住 Python 步" } else { "沒載短令冊,直接跑" })))
    Write-Host ("  [PS] " + $PSVersionTable.PSVersion.ToString())

    $env:PYTHONUTF8 = "1"
    $env:PYTHONIOENCODING = "utf-8"
    $env:VIA_FROM_VCGC = "YES"

    # Python:先 py launcher,再 python
    if (Get-Command py -ErrorAction SilentlyContinue) { $PyExe = (Get-Command py).Source; $PyPre = @('-3', '-B') }
    elseif (Get-Command python -ErrorAction SilentlyContinue) { $PyExe = (Get-Command python).Source; $PyPre = @('-B') }
    else { throw "STOP: 找不到 py / python" }

    $Tool = Get-ChildItem -LiteralPath (Join-Path $VIA 'docs\handoff\ai') -Filter 'VIA_UploadsWorkbench_v*.py' -File -ErrorAction SilentlyContinue |
        Sort-Object Name | Select-Object -Last 1
    if (-not $Tool) { throw "STOP: 找不到 docs\handoff\ai\VIA_UploadsWorkbench_v*.py(先 git pull 分支 claude/practical-pasteur-p67i78)" }
    $LockDir = Join-Path $VIA 'review\VIA_Workbench_LockSite_v0106_4'
    if (-not (Test-Path -LiteralPath $LockDir)) { throw "STOP: 鎖站 review\VIA_Workbench_LockSite_v0106_4 不在(先 git pull)" }
    if (-not (Test-Path -LiteralPath $Downloads)) { throw "STOP: 下載夾不在:$Downloads" }
    Write-Host ("  [工具] " + $Tool.Name + " · 鎖站 v0106_4 · 來源 " + $Downloads)

    # ② 挑檔:20 份正本 + Windows「 (n)」複本(只比檔名,不讀內容)
    $Wanted = @(
        'VIA v0105 實際ZIP完整矩陣與欄位燈號稽核 v0105.2.md',
        'VIA_Matrix_Audit_v0105_1_20261106.xlsx',
        'VIA VCGC · AI handover · v0106.4.md',
        'subsystem_v0106_4_final_actual_zip_receipt.json',
        'VIA_Subsystem_Workspaces_Review_Kit_v0106_4_20261106.zip.sha256',
        'VIA 六系統獨立工作台與 AI 交接指南 v0106.4.md',
        'viaatlas.zip',
        'VIA_Subsystem_Workspaces_Review_Kit_v0106_4_20261106.zip',
        'VIA_Workbench_Hub_latest.html',
        'VIA_MatrixGovernance_Review_Addon_v0105_20261106.zip.sha256',
        'VIA Matrix Governance v0105 — 現況與安全接入.md',
        'VIA Governance MCP v0105 — Windows 手動接入.md',
        'mcp_stdio_smoke_v0105_2.py',
        'VIA_Matrix_Audit_v0105_1_20261106.json',
        'VIA 五系統 RED 阻礙與安全修復計畫 v0105.2.md',
        'matrix_detail_v0105_2_final_receipt.json',
        'VIA_Matrix_Governance_Full_Model_v0105_1_20261106.json.gz',
        'VIA_MatrixGovernance_AllInOne_v0100.py',
        'VIA_MatrixGovernance_QA_v0100.html',
        'VIA_MatrixGovernance_README_v0100.md'
    )
    $rxList = foreach ($w in $Wanted) {
        $ext = [IO.Path]::GetExtension($w)
        $stem = $w.Substring(0, $w.Length - $ext.Length)
        '^' + [regex]::Escape($stem) + '( \(\d+\))?' + [regex]::Escape($ext) + '$'
    }
    $picked = [System.Collections.Generic.List[System.IO.FileInfo]]::new()
    foreach ($f in (Get-ChildItem -LiteralPath $Downloads -File)) {
        foreach ($rx in $rxList) { if ($f.Name -match $rx) { $picked.Add($f); break } }
    }
    $hitNames = @($Wanted | Where-Object { $w = $_; $ext = [IO.Path]::GetExtension($w); $stem = $w.Substring(0, $w.Length - $ext.Length)
            $picked | Where-Object { $_.Name -match ('^' + [regex]::Escape($stem) + '( \(\d+\))?' + [regex]::Escape($ext) + '$') } })
    Write-Host ("  [挑檔] " + $picked.Count + " 個檔 → " + $hitNames.Count + "/" + $Wanted.Count + " 份正本 · " +
        [math]::Round((($picked | Measure-Object Length -Sum).Sum) / 1MB, 1) + " MB")
    foreach ($w in $Wanted) { if ($hitNames -notcontains $w) { Write-Host ("    缺 " + $w) -ForegroundColor Yellow } }
    if ($picked.Count -eq 0) { throw "STOP: 下載夾裡一份都沒有" }

    $Stage = Join-Path ([IO.Path]::GetTempPath()) ("VIA_UploadsStage_" + (Get-Date).ToString('yyyyMMdd_HHmmss') + "_" + $PID)
    New-Item -ItemType Directory -Path $Stage | Out-Null
    foreach ($f in $picked) { Copy-Item -LiteralPath $f.FullName -Destination (Join-Path $Stage $f.Name) }

    # ③ 加速器包住 Python 那一步
    $argList = @($PyPre) + @($Tool.FullName, '--in', $Stage, '--out', $Out)
    $body = { & $PyExe @argList 2>&1 }.GetNewClosure()
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $raw = if ($hasScoped) { Invoke-VIACeleritasScoped $body } else { & $body }
    $pyRc = $global:LASTEXITCODE
    $sw.Stop()
    @($raw) | ForEach-Object { Write-Host ("    " + $_) }
    Write-Host ("  [整合] rc " + $pyRc + " · " + [math]::Round($sw.Elapsed.TotalSeconds, 1) + " s")
    $hub = Join-Path $Out 'index.html'
    $receipt = Join-Path $Out 'uploads_receipt.json'
    if (-not (Test-Path -LiteralPath $hub) -or -not (Test-Path -LiteralPath $receipt)) { throw "STOP: 沒出頁(rc $pyRc)" }
    $lamp = (Get-Content -LiteralPath $receipt -Raw -Encoding utf8 | ConvertFrom-Json).lamp
    $rc = if ($lamp -eq 'RED') { 1 } else { 0 }

    # ④ 收據給 VCGC MCP(VIA_Reports 在 .gitignore 內,只留本機)
    $mcpDir = Join-Path $VIA 'VIA_Reports\uploads'
    New-Item -ItemType Directory -Path $mcpDir -Force | Out-Null
    Copy-Item -LiteralPath $receipt -Destination (Join-Path $mcpDir 'UPLOADS_latest.json') -Force
    Write-Host ("  [MCP] 收據 → VIA_Reports\uploads\UPLOADS_latest.json(資源 via://uploads/latest)· 總燈 " + $lamp)

    # ⑤ VCGC MCP 用戶端設定
    if ($McpConfig -or $ActivateMcp) {
        $Mcp = Get-ChildItem -LiteralPath (Join-Path $VIA 'supportive modules\registry') -Filter 'CGC_MDL279_MCPServer_v*.py' -File |
            Sort-Object Name | Select-Object -Last 1
        if (-not $Mcp) { throw "STOP: 找不到 CGC_MDL279_MCPServer_v*.py" }
        $cfgText = (& $PyExe @PyPre $Mcp.FullName --client-config --root $VIA) -join "`n"
        $cfg = $cfgText | ConvertFrom-Json -AsHashtable
        $srv = $cfg['mcpServers']['vcgc']
        $srv['command'] = $PyExe
        $srv['args'] = @($PyPre) + @($srv['args'])
        Write-Host "  [MCP] VCGC 用戶端設定(只讀伺服器 · stdio):"
        Write-Host (@{ mcpServers = @{ vcgc = $srv } } | ConvertTo-Json -Depth 10)
        if ($ActivateMcp) {
            $desk = Join-Path $env:APPDATA 'Claude\claude_desktop_config.json'
            New-Item -ItemType Directory -Path (Split-Path $desk -Parent) -Force | Out-Null
            $conf = @{}
            if (Test-Path -LiteralPath $desk) {
                $bak = $desk + '.bak_' + (Get-Date).ToString('yyyyMMdd_HHmmss')
                Copy-Item -LiteralPath $desk -Destination $bak
                Write-Host ("  [MCP] 原設定已備份 → " + $bak)
                $txt = Get-Content -LiteralPath $desk -Raw -Encoding utf8
                if ($txt.Trim()) { $conf = $txt | ConvertFrom-Json -AsHashtable }
            }
            if (-not $conf.ContainsKey('mcpServers')) { $conf['mcpServers'] = @{} }
            $conf['mcpServers']['vcgc'] = $srv
            Set-Content -LiteralPath $desk -Value ($conf | ConvertTo-Json -Depth 20) -Encoding utf8NoBOM
            Write-Host ("  [MCP] 已寫入 " + $desk + " 的 mcpServers.vcgc · 重開 Claude Desktop 才生效") -ForegroundColor Green
        }
    }

    Write-Host ("  [完成] " + $hub) -ForegroundColor $(if ($rc -eq 0) { 'Green' } else { 'Yellow' })
    if (-not $NoOpen) { Invoke-Item -LiteralPath $hub }
}
catch {
    Write-Host ("  " + $_.Exception.Message) -ForegroundColor Red
    $rc = 2
}
finally {
    if ($Stage -and -not $KeepStage -and (Test-Path -LiteralPath $Stage)) { Remove-Item -LiteralPath $Stage -Recurse -Force -ErrorAction SilentlyContinue }
    Set-Location -LiteralPath $StartDir
}
exit $rc
