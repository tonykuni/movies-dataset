# CELERITAS-TEMPLATE-JOIN v1
# Start-VIA-OperatorConsole-v0100.ps1 — VIA 操作台:跑 VDF 實測 → 刷新閘 → 重建頁面 → 自動跳出(CGC_MDL261_UIEngine v0103)
# 操作員 2026-10-10:「啟動 VDF 實測 … 跳出 HTML U/I 左面板為功能 右面板為顯示 … 以後結果都自動跳出使用者介面」
#   ① (-Import <VIA_UI_Input.json>)套用左面板匯出的輸入:預設乾跑,加 -Apply 才寫(起始日 · 財報成員 · 國外個股資料增減)
#   ② VDF 離線整合實測(不連網)→ VIA_Reports\vdf\FETCH_TEST_latest.txt(頁面「結果驗證摘要」讀它)
#   ③ (-Plan)VDF 擷取計畫只列不抓;(-Fetch)VDF 實抓:VIA_NET_CONSENT / VIA_SCRAPE_CONSENT 要操作員先在本視窗設,本檔只檢查、永不代設
#   ④ (-Vrn)VRN 報告擷取(Invoke-VIA-VRN-v0105.ps1,C:\測試樣本報告)
#   ⑤ VDF 資料庫閘 db check · 引擎矩陣 engine matrix(頁面「引擎狀態矩陣」「結果矩陣」讀它們)
#   ⑥ 重建操作台並自動跳出(-NoOpen 不開)
# 全部經 VCGC 唯一入口;不 pip install、不改環境、不提交、不推送。每步印 rc,最後一張總表;任何一步紅照實標,不假綠。
[CmdletBinding()]
param(
    [string]$Via = '',
    [string]$PythonExe = 'python',
    [string]$Import = '',
    [switch]$Apply,
    [switch]$Plan,
    [switch]$Fetch,
    [switch]$Vrn,
    [switch]$NoTest,
    [switch]$NoOpen
)
# ===== [VIA:PS-ACCEL:v0101] PS 25 加速器橋(B531 全樹導入;graceful 缺席零影響) =====
try { $VIAPSAccelProbe = if ($PSScriptRoot) { $PSScriptRoot } else { 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics' }
  while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) { $m = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"; if (Test-Path $m) { . $m; break }; $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent } } catch { }
# ===== [VIA:PS-ACCEL:END] =====
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not $Via) {
    $probe = $PSScriptRoot
    while ($probe -and -not (Test-Path (Join-Path $probe 'supportive modules\registry'))) { $probe = Split-Path $probe -Parent }
    $Via = $probe
}
if (-not $Via -or -not (Test-Path (Join-Path $Via 'supportive modules\registry'))) { Write-Host '[停] 找不到 VeritasIntelligenceAnalytics 根(用 -Via 指定)'; exit 1 }
$registry = Join-Path $Via 'supportive modules\registry'
$vcgc = (Get-ChildItem $registry -Filter 'CGC_MDL149_VeritasCentralGovernanceConsole_v*.py' -File |
    Sort-Object { [int]([regex]::Match($_.BaseName, '_v(\d+)$').Groups[1].Value) } | Select-Object -Last 1).FullName
if (-not $vcgc) { Write-Host '[停] VCGC 入口不在'; exit 1 }
$env:VIA_FROM_VCGC = 'YES'
$env:VIA_VCGC_PUSH = 'NO'
$env:PYTHONIOENCODING = 'utf-8'
if ($NoOpen) { $env:VIA_NO_OPEN = '1' } else { Remove-Item Env:VIA_NO_OPEN -ErrorAction SilentlyContinue }

$rows = New-Object System.Collections.Generic.List[object]
function Invoke-Step([string]$Name, [scriptblock]$Body) {
    Write-Host ''
    Write-Host ('[跑] ' + $Name) -ForegroundColor Cyan
    $t0 = Get-Date
    $rc = 0
    $global:LASTEXITCODE = 0
    try {
        & $Body
        $rc = $global:LASTEXITCODE
        if ($null -eq $rc) { $rc = 0 }
    } catch {
        Write-Host ('  [例外] ' + $_.Exception.Message) -ForegroundColor Red
        $rc = 99
    }
    $sec = [math]::Round(((Get-Date) - $t0).TotalSeconds, 1)
    $rows.Add([pscustomobject]@{ Step = $Name; Rc = $rc; Sec = $sec })
    Write-Host ('  → rc {0} · {1}s' -f $rc, $sec) -ForegroundColor $(if ($rc -eq 0) { 'Green' } else { 'Yellow' })
}

Push-Location $Via
try {
    # ① 左面板輸入(先乾跑)
    if ($Import) {
        if (-not (Test-Path $Import)) { Write-Host ('[停] 找不到輸入檔 ' + $Import); exit 1 }
        $impArgs = @('run', 'CGC_MDL261_UIEngine', 'import', (Resolve-Path $Import).Path)
        if ($Apply) { $impArgs += '--apply' }
        Invoke-Step ('① 套用左面板輸入' + $(if ($Apply) { '(寫入)' } else { '(乾跑;確認後加 -Apply)' })) { & $PythonExe $vcgc @impArgs }
    }

    # ② VDF 離線整合實測(不連網)→ 頁面讀的收據
    if (-not $NoTest) {
        $vdfOut = Join-Path $Via 'VIA_Reports\vdf'
        New-Item -ItemType Directory -Force -Path $vdfOut | Out-Null
        $testFile = Join-Path $vdfOut 'FETCH_TEST_latest.txt'
        Invoke-Step '② VDF 離線整合實測(fetch test)' {
            $out = & $PythonExe $vcgc run VDF_SystemManager fetch test 2>&1 | Out-String
            $code = $LASTEXITCODE
            [System.IO.File]::WriteAllText($testFile, $out, (New-Object System.Text.UTF8Encoding($false)))
            ($out -split "`n" | Where-Object { $_ -match 'PASS|FAIL|\[VDF' } | Select-Object -Last 3) | ForEach-Object { Write-Host ('  ' + $_.TrimEnd()) }
            $global:LASTEXITCODE = $code
        }
    }

    # ③ VDF 擷取(計畫 / 實抓;同意旗標只檢查不代設)
    $fill = Join-Path $Via 'Invoke-VDF-FetchFill-v0100.ps1'
    if ($Plan) { Invoke-Step '③ VDF 擷取計畫(只列,不抓)' { & $fill -Plan } }
    if ($Fetch) {
        if ($env:VIA_NET_CONSENT -ne 'YES') {
            Write-Host '[③ 停] VDF 實抓要操作員先在本視窗設 $env:VIA_NET_CONSENT=''YES''; $env:VIA_SCRAPE_CONSENT=''YES''(本檔永不代設)' -ForegroundColor Yellow
            $rows.Add([pscustomobject]@{ Step = '③ VDF 實抓'; Rc = 4; Sec = 0 })
        } else {
            Invoke-Step '③ VDF 實抓(Invoke-VDF-FetchFill)' { & $fill }
        }
    }

    # ④ VRN 報告擷取
    if ($Vrn) { Invoke-Step '④ VRN 報告擷取(Invoke-VIA-VRN-v0105)' { & (Join-Path $Via 'Invoke-VIA-VRN-v0105.ps1') } }

    # ⑤ 刷新 VDF 閘(頁面的引擎狀態矩陣 / 結果矩陣)
    Invoke-Step '⑤ VDF 資料庫閘(db check)' { & $PythonExe $vcgc run VDF_SystemManager db check | Select-Object -Last 4 }
    Invoke-Step '⑤ VDF 引擎矩陣(engine matrix)' { & $PythonExe $vcgc run VDF_SystemManager engine matrix | Select-Object -Last 4 }

    # ⑥ 重建操作台並自動跳出
    Invoke-Step '⑥ 重建 VIA 操作台並自動跳出' { & $PythonExe $vcgc run CGC_MDL261_UIEngine build --open | Where-Object { $_ -match '^\[ui-engine\]' } }
}
finally {
    Pop-Location
}

Write-Host ''
Write-Host '[總表] VIA 操作台' -ForegroundColor Cyan
$rows | Format-Table -AutoSize | Out-String | Write-Host
$bad = @($rows | Where-Object { $_.Rc -ne 0 })
if ($bad.Count -gt 0) {
    Write-Host ('[判決] 有 {0} 步不是 rc 0(照實標,不假綠;頁面的結果驗證摘要會同步顯示)' -f $bad.Count) -ForegroundColor Yellow
    exit 1
}
Write-Host '[判決] 全部 rc 0 · 頁面已重建' -ForegroundColor Green
exit 0
