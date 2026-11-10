#Requires -Version 7.0
# =====================================================================================
# Invoke-VIA-WorkbenchLocal v0100 — 一支 PS 搞定:取碼 → 本機自測 → 上傳檔整合出頁 → (可選)前端伺服器 · VCGC MCP 接上
#   操作員 2026-11-10:「ONE PS CODE TO HANDLE ALL 自建工作臺免去 TOKEN 消耗」「在地整合修正測試」「ps 7.6.9」
#   從任何資料夾都能跑(不必先在 git 倉裡)。
#   加速器:L103 標準 PS 模板 [VIA:PS-TEMPLATE:v0101](腳本單獨下載時找不到正主 = 略過;出頁那步由 UploadsWorkbench 啟動器在倉內再套一次)。
#   ① 取碼:在 $HOME\VIA_Workbench_Local\movies-dataset 建「專用」稀疏 clone(只抓工作台要的 ~25 檔、約 1 MB);
#      已有就 fetch 後對齊分支尾。這個資料夾由本腳本管理,不要在裡面改檔;你原本的工作副本完全不碰。
#      -Full = 改成整倉 checkout(VCGC MCP 的 vcgc_* 動詞要跑主控台,需要整倉)。
#   ② 本機自測:VIA_UploadsWorkbench 尾版 --selftest · CGC_MDL279_MCPServer 尾版 --selftest(連前版鏈)。
#   ③ 出頁:呼叫 Invoke-VIA-UploadsWorkbench 尾版(加速器 · 挑 20 份正本 · 鎖定 U/I · 收據給 MCP)。
#   ④ -Serve:python -m http.server 只綁 127.0.0.1(不對外),瀏覽器開 http://127.0.0.1:<Port>/;不加就直接開 file://。
#   ⑤ -ActivateMcp:VCGC MCP(只讀 stdio)寫進 Claude Desktop 設定(先備份);沒加只印設定。
#   不碰:VRN-1 倉(tonykuni/VIA-VDF-VRN,L123 / L125 倉外只讀:不 clone、不跑);不裝套件;不開網路同意閘;不寫任何系統的冊 / 號。
# 用法:pwsh -File "<存檔位置>\Invoke-VIA-WorkbenchLocal-v0100.ps1" [-Serve] [-ActivateMcp] [-Full] [-Downloads <夾>] [-Out <夾>] [-SkipTest] [-NoOpen]
# 結束碼:0 = 全綠 · 1 = 有黃 / 紅(看最後的總表)· 2 = 卡住(沒 git / 沒 Python / 取碼失敗)
# =====================================================================================
[CmdletBinding()]
param(
    [string]$WorkRoot = (Join-Path $HOME 'VIA_Workbench_Local'),
    [string]$RepoUrl = 'https://github.com/tonykuni/movies-dataset.git',
    [string]$Branch = 'claude/practical-pasteur-p67i78',
    [string]$Downloads = (Join-Path $HOME 'Downloads'),
    [string]$Out = (Join-Path (Join-Path $HOME 'Downloads') 'VIA_Uploads_Workbench'),
    [switch]$Full,
    [switch]$Serve,
    [ValidateRange(1024, 65535)][int]$Port = 8765,
    [switch]$ActivateMcp,
    [switch]$SkipTest,
    [switch]$NoOpen
)
# ===== [VIA:PS-TEMPLATE:v0101] Celeritas PS7 template: this process only, restore on exit, skip when absent, param() untouched =====
$VIACelTplOwn = $false
if ($PSVersionTable.PSVersion.Major -ge 7) {
    try {
        $VIACelTplFile = $null
        $VIACelTplProbe = $PSScriptRoot
        while ($VIACelTplProbe) {
            $VIACelTplTry = Join-Path $VIACelTplProbe 'supportive modules\ps7\VeritasCeleritas.PS7.ps1'
            if (Test-Path -LiteralPath $VIACelTplTry) { $VIACelTplFile = $VIACelTplTry; break }
            $VIACelTplUp = Split-Path $VIACelTplProbe -Parent
            if ((-not $VIACelTplUp) -or ($VIACelTplUp -eq $VIACelTplProbe)) { break }
            $VIACelTplProbe = $VIACelTplUp
        }
        if ($VIACelTplFile -and (-not (Get-Command Restore-CeleritasPS7 -ErrorAction Ignore))) {
            $VIACelTplKeep = @{}
            foreach ($VIACelTplName in 'RestoreOnly', 'Report', 'Body') {
                $VIACelTplVar = Get-Variable -Name $VIACelTplName -Scope 0 -ErrorAction Ignore
                if ($VIACelTplVar) { $VIACelTplKeep[$VIACelTplName] = $VIACelTplVar.Value }
            }
            try { $null = . $VIACelTplFile -RestoreOnly }
            finally {
                Set-StrictMode -Off
                foreach ($VIACelTplName in 'RestoreOnly', 'Report', 'Body') {
                    Remove-Variable -Name $VIACelTplName -Scope 0 -Force -ErrorAction Ignore
                    if ($VIACelTplKeep.ContainsKey($VIACelTplName)) { Set-Variable -Name $VIACelTplName -Value $VIACelTplKeep[$VIACelTplName] -Scope 0 }
                }
            }
            if (Get-Command Start-CeleritasPS7 -ErrorAction Ignore) {
                if (-not (Get-EventSubscriber -Force -ErrorAction Ignore | Where-Object { $_.SourceIdentifier -eq 'PowerShell.Exiting' })) {
                    $null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -SupportEvent -Action { try { Restore-CeleritasPS7 } catch { } }
                }
                [void](Start-CeleritasPS7)
                $VIACelTplOwn = $true
            }
        }
    } catch { }
}
# ===== [VIA:PS-TEMPLATE:END] =====
$ErrorActionPreference = 'Stop'
$StartDir = (Get-Location).Path
$steps = [System.Collections.Generic.List[object]]::new()
function Add-Step([string]$Name, [string]$Lamp, [string]$Note) {
    $steps.Add([pscustomobject]@{ 步驟 = $Name; 燈 = $Lamp; 說明 = $Note })
    $c = @{ GREEN = 'Green'; YELLOW = 'Yellow'; RED = 'Red' }[$Lamp]
    Write-Host ("  [" + $Lamp + "] " + $Name + " · " + $Note) -ForegroundColor $c
}
$Sparse = @(
    '/.mcp.json',
    '/VeritasIntelligenceAnalytics/Invoke-VIA-UploadsWorkbench-v*.ps1',
    '/VeritasIntelligenceAnalytics/Invoke-VIA-WorkbenchLocal-v*.ps1',
    '/VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_UploadsWorkbench_v*.py',
    '/VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_WorkbenchLock_v*.py',
    '/VeritasIntelligenceAnalytics/review/VIA_Workbench_LockSite_v0106_4/',
    '/VeritasIntelligenceAnalytics/supportive modules/VIA_PS_Accel_Module.ps1',
    '/VeritasIntelligenceAnalytics/supportive modules/VIA_SuperAccel_Module.py',
    '/VeritasIntelligenceAnalytics/supportive modules/ps7/',
    '/VeritasIntelligenceAnalytics/supportive modules/registry/CGC_MDL279_MCPServer_v*.py'
)
$rc = 0
try {
    Write-Host ("VIA WorkbenchLocal v0100 · PS " + $PSVersionTable.PSVersion + " · " + (Get-Date).ToString('yyyy-MM-dd HH:mm:ss'))

    # ⓪ 前置:git · Python
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) { Add-Step '前置' 'RED' '找不到 git'; $rc = 2; throw [System.OperationCanceledException]::new("stop") }
    if (Get-Command py -ErrorAction SilentlyContinue) { $PyExe = (Get-Command py).Source; $PyPre = @('-3', '-B') }
    elseif (Get-Command python -ErrorAction SilentlyContinue) { $PyExe = (Get-Command python).Source; $PyPre = @('-B') }
    else { Add-Step '前置' 'RED' '找不到 py / python'; $rc = 2; throw [System.OperationCanceledException]::new("stop") }
    $env:PYTHONUTF8 = '1'; $env:PYTHONIOENCODING = 'utf-8'; $env:VIA_FROM_VCGC = 'YES'
    Add-Step '前置' 'GREEN' ("git " + ((git --version) -replace 'git version ', '') + " · " + $PyExe)

    # ① 取碼(專用稀疏 clone)
    $Dir = Join-Path $WorkRoot 'movies-dataset'
    New-Item -ItemType Directory -Path $WorkRoot -Force | Out-Null
    if (-not (Test-Path -LiteralPath (Join-Path $Dir '.git'))) {
        git clone --filter=blob:none --no-checkout --depth 1 --branch $Branch $RepoUrl $Dir 2>&1 | ForEach-Object { Write-Host ("    " + $_) }
        if ($LASTEXITCODE) { Add-Step '取碼' 'RED' "git clone 失敗(rc $LASTEXITCODE)"; $rc = 2; throw [System.OperationCanceledException]::new("stop") }
    }
    Set-Location -LiteralPath $Dir
    if ($Full) { git sparse-checkout disable 2>&1 | Out-Null }
    else { git sparse-checkout set --no-cone @Sparse 2>&1 | Out-Null }
    git fetch --depth 1 origin $Branch 2>&1 | ForEach-Object { Write-Host ("    " + $_) }
    if ($LASTEXITCODE) { Add-Step '取碼' 'RED' "git fetch 失敗(rc $LASTEXITCODE)"; $rc = 2; throw [System.OperationCanceledException]::new("stop") }
    git -c advice.detachedHead=false checkout --force FETCH_HEAD 2>&1 | Out-Null   # 專用資料夾:一律對齊分支尾
    $head = (git rev-parse --short HEAD).Trim()
    $VIA = Join-Path $Dir 'VeritasIntelligenceAnalytics'
    Add-Step '取碼' 'GREEN' ("$Branch @ $head · " + ($(if ($Full) { '整倉' } else { '稀疏' })) + " · " + $Dir)

    # ② 本機自測
    $tool = Get-ChildItem -LiteralPath (Join-Path $VIA 'docs\handoff\ai') -Filter 'VIA_UploadsWorkbench_v*.py' -File | Sort-Object Name | Select-Object -Last 1
    $mcp = Get-ChildItem -LiteralPath (Join-Path $VIA 'supportive modules\registry') -Filter 'CGC_MDL279_MCPServer_v*.py' -File | Sort-Object Name | Select-Object -Last 1
    if ($SkipTest) { Add-Step '自測' 'YELLOW' '-SkipTest:沒跑(黃不是綠)' }
    else {
        foreach ($t in @($tool, $mcp)) {
            $o = & $PyExe @PyPre $t.FullName --selftest 2>&1
            $ok = ($LASTEXITCODE -eq 0)
            Add-Step ('自測 ' + $t.Name) $(if ($ok) { 'GREEN' } else { 'RED' }) ((@($o) | Select-Object -Last 1) -as [string])
            if (-not $ok) { $rc = 1 }
        }
    }

    # ③ 出頁(加速器 · 挑檔 · 鎖定 U/I · 收據給 MCP)
    $launcher = Get-ChildItem -LiteralPath $VIA -Filter 'Invoke-VIA-UploadsWorkbench-v*.ps1' -File | Sort-Object Name | Select-Object -Last 1
    $largs = @{ Downloads = $Downloads; Out = $Out; NoOpen = $true; McpConfig = $true }
    if ($ActivateMcp) { $largs['ActivateMcp'] = $true }
    & $launcher.FullName @largs
    $lrc = $LASTEXITCODE
    $lamp = @{ 0 = 'GREEN'; 1 = 'RED' }[$lrc]; if (-not $lamp) { $lamp = 'RED' }
    $hub = Join-Path $Out 'index.html'
    if ($lrc -eq 0) {
        $r = Get-Content -LiteralPath (Join-Path $Out 'uploads_receipt.json') -Raw -Encoding utf8 | ConvertFrom-Json
        if ($r.lamp -eq 'YELLOW') { $lamp = 'YELLOW' }
        Add-Step '出頁' $lamp ("已上傳 " + $r.uploaded + "/" + $r.expected + " 份正本 · 系統頁 " + (@($r.pages.PSObject.Properties).Count) + " · " + $hub)
    }
    else { Add-Step '出頁' 'RED' ("rc $lrc(1 = 有同名異內容 / 雜湊不符,頁照出;2 = 沒出頁)") }
    if ($lamp -ne 'GREEN') { $rc = [math]::Max($rc, 1) }

    # ④ 前端伺服器(只綁 127.0.0.1)
    $url = $null
    if ($Serve -and (Test-Path -LiteralPath $hub)) {
        $busy = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
        if ($busy) { Add-Step '前端伺服器' 'YELLOW' "port $Port 已被占用(PID $($busy[0].OwningProcess)),沒另開;換 -Port" }
        else {
            $p = Start-Process -FilePath $PyExe -ArgumentList (@($PyPre) + @('-m', 'http.server', "$Port", '--bind', '127.0.0.1', '--directory', $Out)) -WindowStyle Minimized -PassThru
            $url = "http://127.0.0.1:$Port/index.html"
            Add-Step '前端伺服器' 'GREEN' ("PID " + $p.Id + " · " + $url + " · 停止:Stop-Process -Id " + $p.Id)
        }
    }
    if (-not $NoOpen -and (Test-Path -LiteralPath $hub)) { if ($url) { Start-Process $url } else { Invoke-Item -LiteralPath $hub } }

    # ⑤ MCP
    if ($ActivateMcp) { Add-Step 'VCGC MCP' 'GREEN' '已寫入 Claude Desktop 設定(備份見上方);重開 Claude Desktop 生效' }
    else { Add-Step 'VCGC MCP' 'YELLOW' '只印設定(見上方);要寫入加 -ActivateMcp' }
    if (-not $Full) { Add-Step 'MCP 範圍' 'YELLOW' '稀疏模式:資源 via://uploads/latest 可讀;vcgc_* 動詞要整倉(加 -Full)' }
}
catch {
    if ($_.Exception -isnot [System.OperationCanceledException]) { Add-Step '例外' 'RED' $_.Exception.Message }
    $rc = 2
}
finally {
    Set-Location -LiteralPath $StartDir
    Write-Host ""
    $steps | Format-Table -AutoSize -Wrap
    try {
        if (Test-Path -LiteralPath $Out) {
            @{ engine = 'Invoke-VIA-WorkbenchLocal_v0100'; at_utc = [DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ'); rc = $rc; steps = $steps } |
                ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $Out 'oneshot_receipt.json') -Encoding utf8NoBOM
        }
    } catch { }
}
if ($VIACelTplOwn) { try { Restore-CeleritasPS7 } catch { } }  # [VIA:PS-TEMPLATE] restore on exit
exit $rc
