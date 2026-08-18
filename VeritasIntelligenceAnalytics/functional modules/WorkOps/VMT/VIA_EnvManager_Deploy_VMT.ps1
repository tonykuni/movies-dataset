#requires -Version 7.0
# ============================================================================
#  VIA_EnvManager (VEGN)  Deploy: VeritasMailTracker Tools  v1.0
# ----------------------------------------------------------------------------
#  目的: 用 VIA 環境隔離原則把郵件追蹤 + 流程探勘工具部署到「專屬 venv」,
#        絕不污染 via_core / venv_core, 不觸發 NumPy 黃金律衝突.
#  治理: 只增不減 -- 只建立/擴充 vmt_pm, 從不修改或刪除任何既有共用環境.
#  隔離: 專屬 venv  vmt_pm (Py3.11)  @  C:\Users\tonyk\envs\vmt_pm
#  黃金律: numpy >=1.24,<2.0  以 constraints 檔強制 (pip -c), 攔截 pm4py 漂移.
#  分層:
#    核心層 (預設)      : pandas 內建探勘, 無 AGPL, 依賴極小
#    完整層 (-WithPM4Py) : + pm4py (AGPL-3.0), numpy 仍鎖 1.26.x
#  Gatekeeper 7 檢查於安裝前執行; 安裝後 import + 黃金律 post-verify.
#  輸出: Visual Lock 風格部署報告 HTML + requirements.lock + 一鍵 runner.
#  慣例: param 首列; 無別名; 無 Read-Host; 無 exit/Stop-Process;
#        ProcessStartInfo 管子程序; UTF8 no-BOM 寫檔; Start-Process 僅開報告.
# ============================================================================
param(
    [string]$EnvRoot    = "C:\Users\tonyk\envs",
    [string]$EnvName    = "vmt_pm",
    [string]$EnginePath = "",
    [string]$PyLauncher = "",
    [switch]$WithPM4Py,
    [switch]$Recreate,
    [switch]$Offline,
    [switch]$NoOpen
)

$ErrorActionPreference = 'Stop'
$script:T0 = Get-Date

# ----- 受保護共用環境: 只增不減, 這些名稱一律禁止作為部署目標 --------------
$script:ProtectedEnvs = @('via_core','venv_core','via_ml','vgf_core','vgf_ml','via_image')

function Write-Step {
    param([string]$Tag, [string]$Msg, [string]$Color = 'Cyan')
    Write-Host ("[{0}] [{1}] {2}" -f (Get-Date).ToString('HH:mm:ss'), $Tag, $Msg) -ForegroundColor $Color
}
function Save-TextFile {
    param([string]$Path, [string]$Text)
    $enc = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllText($Path, $Text, $enc)
}
function ConvertTo-HtmlSafe {
    param([string]$S)
    if ($null -eq $S) { return '' }
    return $S.Replace('&','&amp;').Replace('<','&lt;').Replace('>','&gt;')
}
# ----- ProcessStartInfo 子程序執行 (等程序結束, 非等使用者輸入) -------------
function Invoke-Native {
    param([string]$FilePath, [string[]]$Arguments)
    $psi = [System.Diagnostics.ProcessStartInfo]::new()
    $psi.FileName = $FilePath
    foreach ($a in $Arguments) { [void]$psi.ArgumentList.Add($a) }
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError  = $true
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow  = $true
    $proc = [System.Diagnostics.Process]::new()
    $proc.StartInfo = $psi
    $started = $false
    try { $started = $proc.Start() } catch { return @{ code = -999; out = ''; err = $_.Exception.Message } }
    if (-not $started) { return @{ code = -998; out = ''; err = 'process did not start' } }
    $out = $proc.StandardOutput.ReadToEnd()
    $err = $proc.StandardError.ReadToEnd()
    $proc.WaitForExit()
    return @{ code = $proc.ExitCode; out = $out; err = $err }
}

# ----- Python 3.11 啟動器自動偵測 (LL#16: 優先 py -3.11, 不用 where.exe) -----
function Resolve-PyLauncher {
    param([string]$Preferred)
    $cands = @()
    if ($Preferred) { $cands += ,@($Preferred, @()) }
    $cands += ,@('py',       @('-3.11'))
    $cands += ,@('python3.11', @())
    $cands += ,@('python3',   @())
    $cands += ,@('python',    @())
    foreach ($c in $cands) {
        $r = Invoke-Native -FilePath $c[0] -Arguments (@($c[1]) + @('--version'))
        if ($r.code -eq 0 -and (($r.out + $r.err) -match 'Python\s+3\.')) {
            return @{ file = $c[0]; pre = $c[1]; ver = (($r.out + $r.err).Trim()) }
        }
    }
    return $null
}

Write-Host ''
Write-Host '=============================================================' -ForegroundColor DarkCyan
Write-Host '  VIA_EnvManager (VEGN)  |  部署 VMT 郵件追蹤 + 流程探勘工具' -ForegroundColor Cyan
Write-Host '=============================================================' -ForegroundColor DarkCyan

$script:EnvPath  = Join-Path $EnvRoot $EnvName
$tier = 'core'
if ($WithPM4Py) { $tier = 'full' }

# ---------------------------------------------------------------------------
#  Gatekeeper 7 檢查 (安裝前)
# ---------------------------------------------------------------------------
$checks = [System.Collections.Generic.List[object]]::new()
function Add-Check {
    param([string]$Name, [bool]$Pass, [string]$Detail, [bool]$Hard = $true)
    $checks.Add(@{ name = $Name; pass = $Pass; detail = $Detail; hard = $Hard })
    $c = 'Green'; $mk = 'PASS'
    if (-not $Pass) { if ($Hard) { $c = 'Red'; $mk = 'FAIL' } else { $c = 'Yellow'; $mk = 'WARN' } }
    Write-Host ("    [{0}] {1} -- {2}" -f $mk, $Name, $Detail) -ForegroundColor $c
}

Write-Step '1/6' 'Gatekeeper 7 檢查 (安裝前)' 'Cyan'

# G1: Python 3.11 啟動器
$py = Resolve-PyLauncher -Preferred $PyLauncher
if ($py) { Add-Check 'G1 Python3.11 啟動器' $true ("{0} {1} -> {2}" -f $py.file, ($py.pre -join ' '), $py.ver) }
else     { Add-Check 'G1 Python3.11 啟動器' $false '找不到 Python 3.11 (請安裝或指定 -PyLauncher)' }

# G2: EnvRoot 存在且可寫
$rootOk = Test-Path $EnvRoot
if (-not $rootOk) { try { New-Item -ItemType Directory -Path $EnvRoot -Force | Out-Null; $rootOk = $true } catch { $rootOk = $false } }
Add-Check 'G2 EnvRoot 可用' $rootOk ("{0}" -f $EnvRoot)

# G3: 目標名稱不得為受保護共用環境 (只增不減核心防線)
$notProtected = ($ProtectedEnvs -notcontains $EnvName)
Add-Check 'G3 非受保護環境' $notProtected ("目標 '{0}'; 受保護清單={1}" -f $EnvName, ($ProtectedEnvs -join ','))

# G4: 磁碟空間 >= 2GB
$freeGb = -1.0
try {
    $driveLetter = ([System.IO.Path]::GetPathRoot($EnvRoot)).TrimEnd('\')
    $di = [System.IO.DriveInfo]::new($driveLetter)
    $freeGb = [math]::Round($di.AvailableFreeSpace / 1GB, 1)
} catch { $freeGb = -1.0 }
$diskOk = ($freeGb -lt 0) -or ($freeGb -ge 2.0)
Add-Check 'G4 磁碟空間' $diskOk ("可用 {0} GB (需>=2GB)" -f $freeGb) $false

# G5: 網路 / 離線模式
if ($Offline) { Add-Check 'G5 安裝來源' $true '離線模式: 略過網路安裝' $false }
else {
    $net = Test-Connection -TargetName 'pypi.org' -Count 1 -Quiet -TimeoutSeconds 3 -ErrorAction SilentlyContinue
    Add-Check 'G5 PyPI 連線' ([bool]$net) ('pypi.org ' + ($(if ($net) { '可達' } else { '不可達 (可加 -Offline)' }))) $false
}

# G6: 黃金律 constraints 將被套用
Add-Check 'G6 NumPy 黃金律' $true 'constraints: numpy>=1.24,<2.0 (pip -c 強制)'

# G7: 既有 vmt_pm 狀態 (只增不減: 預設保留, -Recreate 才重建)
$envExists = Test-Path $script:EnvPath
if ($envExists -and -not $Recreate) {
    Add-Check 'G7 目標環境狀態' $true ("已存在 -> 增量更新 (不刪除): {0}" -f $script:EnvPath) $false
} elseif ($envExists -and $Recreate) {
    Add-Check 'G7 目標環境狀態' $true ("已存在 + -Recreate -> 將重建: {0}" -f $script:EnvPath) $false
} else {
    Add-Check 'G7 目標環境狀態' $true ("全新建立: {0}" -f $script:EnvPath) $false
}

$hardFail = @($checks | Where-Object { $_.hard -and -not $_.pass })
if ($hardFail.Count -gt 0) {
    Write-Host ''
    Write-Host ('  Gatekeeper 硬性檢查未過 ({0} 項), 中止部署 (未觸碰任何環境).' -f $hardFail.Count) -ForegroundColor Red
    foreach ($f in $hardFail) { Write-Host ('    - ' + $f.name + ': ' + $f.detail) -ForegroundColor Red }
    Write-Host ''
    return
}
Write-Step '1/6' 'Gatekeeper 通過, 開始隔離部署' 'Green'

# ---------------------------------------------------------------------------
#  建立 / 重建隔離 venv
# ---------------------------------------------------------------------------
if ($envExists -and $Recreate) {
    Write-Step '2/6' ('移除舊環境 (因 -Recreate): {0}' -f $script:EnvPath) 'Yellow'
    Remove-Item -Path $script:EnvPath -Recurse -Force
    $envExists = $false
}
if (-not $envExists) {
    if ($Offline) {
        Write-Host '  離線模式無法建立新 venv (需 Python 建置). 中止.' -ForegroundColor Red
        return
    }
    Write-Step '2/6' ('建立隔離 venv: {0}' -f $script:EnvPath) 'Cyan'
    $mk = Invoke-Native -FilePath $py.file -Arguments (@($py.pre) + @('-m','venv',$script:EnvPath))
    if ($mk.code -ne 0) {
        Write-Host ('  venv 建立失敗: ' + $mk.err) -ForegroundColor Red
        return
    }
} else {
    Write-Step '2/6' '沿用既有隔離 venv (只增不減, 增量更新)' 'Green'
}

# venv 內 python 路徑 (Windows: Scripts\python.exe; POSIX: bin/python)
$venvPy = Join-Path $script:EnvPath 'Scripts\python.exe'
if (-not (Test-Path $venvPy)) { $venvPy = Join-Path $script:EnvPath 'bin/python' }
if (-not (Test-Path $venvPy)) {
    Write-Host '  找不到 venv 內的 python, 中止.' -ForegroundColor Red
    return
}

# ---------------------------------------------------------------------------
#  寫入黃金律 constraints, 安裝套件 (核心層 / 完整層)
# ---------------------------------------------------------------------------
$constraintsPath = Join-Path $script:EnvPath 'via_constraints.txt'
Save-TextFile -Path $constraintsPath -Text "numpy>=1.24,<2.0`n"

$pkgCore = @('numpy>=1.24,<2.0','pandas>=2.0,<2.3')
$pkgFull = @('pm4py')

if ($Offline) {
    Write-Step '3/6' '離線模式: 略過 pip 安裝, 僅驗證既有環境' 'Yellow'
} else {
    Write-Step '3/6' 'pip 升級 + 核心層安裝 (numpy 鎖 <2.0, pandas)' 'Cyan'
    $up = Invoke-Native -FilePath $venvPy -Arguments @('-m','pip','install','--upgrade','pip','--quiet')
    if ($up.code -ne 0) { Write-Host ('    pip 升級警告: ' + $up.err.Trim()) -ForegroundColor Yellow }

    $coreArgs = @('-m','pip','install','--quiet','-c',$constraintsPath) + $pkgCore
    $ci = Invoke-Native -FilePath $venvPy -Arguments $coreArgs
    if ($ci.code -ne 0) {
        Write-Host ('  核心層安裝失敗: ' + $ci.err) -ForegroundColor Red
        return
    }
    Write-Host '    核心層完成 (pandas, 無 AGPL)' -ForegroundColor Green

    if ($WithPM4Py) {
        Write-Step '3/6' '完整層安裝: pm4py (AGPL-3.0), numpy 仍受 constraints 鎖定' 'Cyan'
        $fullArgs = @('-m','pip','install','--quiet','-c',$constraintsPath) + $pkgFull
        $fi = Invoke-Native -FilePath $venvPy -Arguments $fullArgs
        if ($fi.code -ne 0) {
            Write-Host ('    pm4py 安裝失敗 (核心層仍可用): ' + $fi.err.Trim()) -ForegroundColor Yellow
        } else {
            Write-Host '    完整層完成 (pm4py)' -ForegroundColor Green
        }
    }
}

# ---------------------------------------------------------------------------
#  Post-verify: import + 黃金律斷言
# ---------------------------------------------------------------------------
Write-Step '4/6' 'Gatekeeper post-verify (import + numpy<2.0 斷言)' 'Cyan'
$probe = @'
import json
r = {"pandas": None, "numpy": None, "pm4py": None, "golden": False}
try:
    import numpy; r["numpy"] = numpy.__version__
    v = tuple(int(x) for x in numpy.__version__.split(".")[:2])
    r["golden"] = v < (2, 0)
except Exception as e:
    r["numpy"] = "ERR:%s" % e
try:
    import pandas; r["pandas"] = pandas.__version__
except Exception as e:
    r["pandas"] = "ERR:%s" % e
try:
    import pm4py; r["pm4py"] = pm4py.__version__
except Exception:
    r["pm4py"] = None
print(json.dumps(r))
'@
$probePath = Join-Path $script:EnvPath '_probe.py'
Save-TextFile -Path $probePath -Text $probe
$pv = Invoke-Native -FilePath $venvPy -Arguments @($probePath)
$verInfo = @{ pandas = '?'; numpy = '?'; pm4py = $null; golden = $false }
try {
    $jsonLine = ($pv.out -split "`n" | Where-Object { $_.Trim().StartsWith('{') } | Select-Object -Last 1)
    if ($jsonLine) { $verInfo = $jsonLine | ConvertFrom-Json -AsHashtable }
} catch { }
$goldenOk = [bool]$verInfo.golden
if ($goldenOk) { Write-Host ("    numpy={0} pandas={1} pm4py={2} | 黃金律 PASS" -f $verInfo.numpy, $verInfo.pandas, ($verInfo.pm4py)) -ForegroundColor Green }
else { Write-Host ("    numpy={0} | 黃金律 FAIL 或環境未就緒" -f $verInfo.numpy) -ForegroundColor Red }
$pm4pyState = 'not installed (core tier)'
if ($verInfo.pm4py) { $pm4pyState = $verInfo.pm4py }

# ---------------------------------------------------------------------------
#  凍結 lock + 產生一鍵 runner
# ---------------------------------------------------------------------------
Write-Step '5/6' '凍結 requirements.lock + 產生 runner' 'Cyan'
$lockPath = Join-Path $script:EnvPath 'requirements.lock'
$fr = Invoke-Native -FilePath $venvPy -Arguments @('-m','pip','freeze')
if ($fr.code -eq 0) { Save-TextFile -Path $lockPath -Text $fr.out }
$pkgList = @()
if ($fr.code -eq 0) { $pkgList = @($fr.out -split "`n" | Where-Object { $_.Trim().Length -gt 0 }) }

if (-not $EnginePath -or -not (Test-Path $EnginePath)) {
    $guess = Join-Path (Split-Path -Parent $PSCommandPath) 'VIA_ENG024_VmtProcessMining.py'
    if (Test-Path $guess) { $EnginePath = $guess }
}
$runnerPath = Join-Path $EnvRoot ('Run-VMT-ProcessMining.ps1')
$runnerText = @"
#requires -Version 7.0
param([string]`$VmtRoot = "C:\VIA\VeritasMailTracker", [switch]`$NoOpen)
# 一鍵: 用隔離環境 $EnvName 執行流程探勘引擎 (由 VEGN 部署自動產生)
`$venvPy = "$venvPy"
`$engine = "$EnginePath"
`$env:VMT_ROOT = `$VmtRoot
if (-not (Test-Path `$venvPy)) { Write-Host "隔離環境遺失, 請重跑部署腳本" -ForegroundColor Red; return }
if (-not (Test-Path `$engine)) { Write-Host "找不到引擎: `$engine" -ForegroundColor Red; return }
`$psi = [System.Diagnostics.ProcessStartInfo]::new()
`$psi.FileName = `$venvPy
[void]`$psi.ArgumentList.Add(`$engine)
if (`$NoOpen) { [void]`$psi.ArgumentList.Add('--no-open') }
`$psi.UseShellExecute = `$false
`$p = [System.Diagnostics.Process]::new(); `$p.StartInfo = `$psi
[void]`$p.Start(); `$p.WaitForExit()
"@
Save-TextFile -Path $runnerPath -Text $runnerText
Write-Host ('    runner: ' + $runnerPath) -ForegroundColor Green

# ---------------------------------------------------------------------------
#  Visual Lock 部署報告
# ---------------------------------------------------------------------------
Write-Step '6/6' 'Visual Lock 部署報告' 'Cyan'
$chkRows = ''
foreach ($c in $checks) {
    $mk = 'PASS'; $col = '#5a9e6f'
    if (-not $c.pass) { if ($c.hard) { $mk = 'FAIL'; $col = '#b5443a' } else { $mk = 'WARN'; $col = '#c9a13a' } }
    $chkRows += ('<tr><td><span class="pill" style="background:{0}">{1}</span></td><td>{2}</td><td>{3}</td></tr>' -f $col, $mk, (ConvertTo-HtmlSafe $c.name), (ConvertTo-HtmlSafe $c.detail))
}
$pkgRows = ''
foreach ($p in ($pkgList | Sort-Object)) {
    $hl = ''
    if ($p -match '^(numpy|pandas|pm4py)([=<>]|$)') { $hl = ' style="color:#4c78a8;font-weight:700"' }
    $pkgRows += ('<tr><td' + $hl + '>' + (ConvertTo-HtmlSafe $p) + '</td></tr>')
}
if ($pkgRows.Length -eq 0) { $pkgRows = '<tr><td class="empty">離線模式未凍結</td></tr>' }
$goldenBadge = if ($goldenOk) { '<span class="pill" style="background:#5a9e6f">PASS</span>' } else { '<span class="pill" style="background:#b5443a">FAIL</span>' }
$elapsed = [math]::Round(((Get-Date) - $script:T0).TotalSeconds, 1)
$agplNote = ''
if ($verInfo.pm4py) { $agplNote = '<div class="note">完整層含 pm4py = AGPL-3.0。純內部分析可; 若封閉商用併入 VIA 對外交付需另購商業授權, 或改用核心層 (pandas) 免 AGPL。</div>' }

$html = @'
<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="UTF-8"><title>VEGN 部署報告</title><style>
:root{--bg:#f5f4f0;--paper:#fff;--ink:#1e1d1a;--hair:#dbd9d3;--blue:#4c78a8;--teal:#439a9a;}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--ink);font-family:"DM Sans","Microsoft JhengHei",sans-serif;padding:28px}
.seal{display:inline-flex;width:44px;height:44px;background:#439a9a;color:#fff;align-items:center;justify-content:center;font-size:22px;border-radius:3px;margin-right:14px}
header{display:flex;align-items:center;border-bottom:1px solid var(--hair);padding-bottom:16px}
h1{font-size:21px;letter-spacing:1px}
.sub{font-family:"DM Mono",monospace;font-size:12px;color:#777;margin-top:2px}
.strip{height:4px;background:linear-gradient(90deg,#b5443a,#d08343,#c9a13a,#7ba86a,#4d8f63);margin:14px 0 22px;border-radius:2px}
h2{font-size:13px;font-family:"DM Mono",monospace;letter-spacing:2px;color:#555;margin:24px 0 10px;text-transform:uppercase}
.grid{display:flex;gap:12px;flex-wrap:wrap}
.card{background:var(--paper);border:1px solid var(--hair);border-radius:3px;padding:14px 20px;min-width:170px}
.cv{font-size:18px;font-weight:700}.cn{font-size:12px;color:#777;margin-top:2px}
table{width:100%;border-collapse:collapse;background:var(--paper);border:1px solid var(--hair);border-radius:3px;overflow:hidden}
th{font-family:"DM Mono",monospace;font-size:11px;text-align:left;padding:9px 10px;border-bottom:1px solid var(--hair);color:#666;letter-spacing:1px}
td{font-size:13px;padding:8px 10px;border-bottom:1px solid var(--hair)}
tr:last-child td{border-bottom:none}
.pill{color:#fff;font-size:11px;font-family:"DM Mono",monospace;padding:2px 8px;border-radius:2px}
.note{background:#fbf6ee;border:1px solid #e6d8c0;border-left:5px solid #c9a13a;border-radius:3px;padding:10px 14px;font-size:12px;color:#7a5f2e;margin-top:8px}
.cmd{background:#1e1d1a;color:#e8e6e0;font-family:"DM Mono",monospace;font-size:12px;padding:12px 14px;border-radius:3px;margin-top:8px;white-space:pre-wrap}
.empty{color:#999;text-align:center}
footer{margin-top:30px;font-size:11px;color:#999;font-family:"DM Mono",monospace}
</style></head><body>
<header><div class="seal">環</div><div><h1>VIA_EnvManager 部署報告 &mdash; VMT 工具隔離部署</h1>
<div class="sub">VEGN | {{DATE}} | 只增不減 | 未觸碰 via_core / venv_core</div></div></header>
<div class="strip"></div>
<h2>部署摘要</h2>
<div class="grid">
<div class="card"><div class="cv">{{ENVNAME}}</div><div class="cn">隔離環境 (Py3.11)</div></div>
<div class="card"><div class="cv">{{TIER}}</div><div class="cn">安裝層級</div></div>
<div class="card"><div class="cv">{{NUMPY}}</div><div class="cn">numpy (黃金律 {{GOLDEN}})</div></div>
<div class="card"><div class="cv">{{PANDAS}}</div><div class="cn">pandas</div></div>
<div class="card"><div class="cv">{{PM4PY}}</div><div class="cn">pm4py</div></div>
</div>
{{AGPL}}
<h2>Gatekeeper 7 檢查</h2>
<table><tr><th>結果</th><th>檢查項</th><th>細節</th></tr>{{CHECKS}}</table>
<h2>一鍵執行 (隔離環境, 不影響其他工具)</h2>
<div class="cmd">powershell -File "{{RUNNER}}"</div>
<h2>已鎖定套件 (requirements.lock)</h2>
<table><tr><th>package==version</th></tr>{{PKGS}}</table>
<footer>VEGN Deploy v1.0 | 環境: {{ENVPATH}} | constraints: numpy>=1.24,<2.0 | 耗時 {{SEC}}s</footer>
</body></html>
'@
$html = $html.Replace('{{DATE}}', (Get-Date).ToString('yyyy/MM/dd HH:mm')).
    Replace('{{ENVNAME}}', $EnvName).Replace('{{TIER}}', $tier).
    Replace('{{NUMPY}}', "$($verInfo.numpy)").Replace('{{PANDAS}}', "$($verInfo.pandas)").
    Replace('{{PM4PY}}', (ConvertTo-HtmlSafe $pm4pyState)).Replace('{{GOLDEN}}', $goldenBadge).
    Replace('{{AGPL}}', $agplNote).Replace('{{CHECKS}}', $chkRows).
    Replace('{{RUNNER}}', (ConvertTo-HtmlSafe $runnerPath)).Replace('{{PKGS}}', $pkgRows).
    Replace('{{ENVPATH}}', (ConvertTo-HtmlSafe $script:EnvPath)).Replace('{{SEC}}', "$elapsed")
$reportPath = Join-Path $EnvRoot ('VEGN_Deploy_{0}.html' -f $EnvName)
Save-TextFile -Path $reportPath -Text $html

Write-Host ''
Write-Host ('  部署完成 (耗時 {0}s). 環境: {1}' -f $elapsed, $script:EnvPath) -ForegroundColor Green
Write-Host ('  執行探勘:  powershell -File "{0}"' -f $runnerPath) -ForegroundColor Yellow
Write-Host ('  報告:      {0}' -f $reportPath) -ForegroundColor Yellow
Write-Host ''
if (-not $NoOpen) { Start-Process $reportPath }
