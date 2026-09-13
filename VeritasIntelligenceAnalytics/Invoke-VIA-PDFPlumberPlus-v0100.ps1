param(
    [string]$Pdf     = '',
    [string]$In      = '',
    [string]$Out     = '',
    [string]$Python  = '',
    [int]$Threads    = 0,
    [switch]$NoOcr,
    [switch]$Open,
    [switch]$SelfTest
)

# =====================================================================================
# Invoke-VIA-PDFPlumberPlus-v0100.ps1
# VIA PDFPlumber-Plus 啟動器(批473 收容;操作員令「授權你解決 收引擎即可」)
# -------------------------------------------------------------------------------------
# 引擎本體 VIA_PDFPlumberPlusEngine.py 早在庫內(references/intake/…v1.0.0/),
# 缺的一直是**啟動器**。操作員上傳的那一份三個路徑全寫死,照收會壞:
#
#   ① $VIA_ROOT = 'C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics'
#      —— 那**不是**操作員實際在跑的副本(OneDrive\Documents\movies-dataset\…)。
#      批452/453 那一課:同一分鐘內三個副本,而畫面上沒有任何一行說
#      「你跑的不是你以為的那一份」。**寫死根路徑正是那場災難的起因。**
#      → 改成從腳本自己的位置往上找(不接受任何硬編根)。
#   ② $DefaultIn = $VIA_ROOT\inbox\pdf
#      —— VRN 的收件夾律在**冊**上(VIA_InputConsole_Spec.families.vrn.input),
#      ENG072/ENG074/MDL141/MDL139 四家都讀它。自己另指一個 inbox
#      就是批446 那件事的翻版:同一份冊,消費者各做各的,漏掉的那個靜靜走錯。
#      → 讀冊;而且取**有報告的那個夾**,不是「存在的那個」(指到空夾等於
#        什麼都沒跑還報成功)。
#   ③ $DefaultOut = $VIA_ROOT\outputs\PDFPlumberPlus
#      —— 全系統的產出律是 VIA_Reports/*(已在 .gitignore,衍生物不入 git)。
#      → 落 VIA_Reports\pdfplumber_plus。而且 **--out 一律顯式傳給引擎**,
#        這樣引擎自己 _PARAMS 裡那個寫死的 VIA_ROOT 永遠不會被用到。
#   ④ python 也寫死在 C:\Users\tonyk\envs\via_core
#      → 先用母倉的 Get-VIAEnvPython "vrn"(短令冊載入時就在);沒有才退候選。
#
# 保留上傳件做對的事:ProcessStartInfo、stderr @@PROGRESS 進度條、
# 無 Read-Host、無 exit/Stop-Process、UTF8 no-BOM、結束印報告路徑。
# **零彈窗律**:報告不自動跳出,要看加 -Open(與 via-closeout --open 同慣例)。
# =====================================================================================

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Resolve-VIARoot {
    # 從腳本自己的位置往上找母倉根(VIA 標記=supportive modules + functional modules)
    $probe = if ($PSScriptRoot) { $PSScriptRoot } else { (Get-Location).Path }
    for ($i = 0; $i -lt 8 -and $probe; $i++) {
        if ((Test-Path -LiteralPath (Join-Path $probe 'supportive modules')) -and
            (Test-Path -LiteralPath (Join-Path $probe 'functional modules'))) { return $probe }
        $parent = Split-Path -Parent $probe
        if ($parent -eq $probe) { break }
        $probe = $parent
    }
    return ''
}

function Resolve-Newest {
    param([string]$Dir, [string]$Pattern)
    if (-not (Test-Path -LiteralPath $Dir)) { return '' }
    $hit = Get-ChildItem -LiteralPath $Dir -Filter $Pattern -File -Recurse -ErrorAction SilentlyContinue |
           Sort-Object Name | Select-Object -Last 1
    if ($hit) { return $hit.FullName }
    return ''
}

function Resolve-EnginePython {
    param([string]$Preferred, [string]$Via)
    if ($Preferred) { return $Preferred }
    # 母倉正主:短令冊載入時 Get-VIAEnvPython 就在
    $cmd = Get-Command -Name 'Get-VIAEnvPython' -ErrorAction SilentlyContinue
    if ($null -ne $cmd) {
        try {
            $p = & $cmd 'vrn'
            if ($p -and (Test-Path -LiteralPath $p)) { return $p }
        } catch { }
    }
    foreach ($c in @("$Via\.venv\Scripts\python.exe", "$Via\.venv\bin\python")) {
        if (Test-Path -LiteralPath $c) { return $c }
    }
    foreach ($n in @('python3', 'python')) {
        $g = Get-Command -Name $n -ErrorAction SilentlyContinue
        if ($null -ne $g) { return $g.Source }
    }
    return ''
}

function Resolve-VRNInbox {
    # **讀冊**(與 MDL139/ENG072/ENG074/MDL141 同一個來源),取有報告的那個夾
    param([string]$Via)
    $spec = Resolve-Newest -Dir (Join-Path $Via 'supportive modules\registry') `
                           -Pattern 'VIA_InputConsole_Spec_v*.json'
    $dirs = @()
    if ($spec) {
        try {
            $j = Get-Content -LiteralPath $spec -Raw -Encoding UTF8 | ConvertFrom-Json
            $inp = $j.families.vrn.input
            foreach ($k in @('incoming', 'dir_default')) {
                $v = $inp.$k
                if ($v) { $dirs += (Join-Path $Via ($v -replace '/', '\')) }
            }
        } catch { }
    }
    if ($dirs.Count -eq 0) {
        $dirs = @((Join-Path $Via 'functional modules\VRN\input\incoming'))
    }
    foreach ($d in $dirs) {
        if (Test-Path -LiteralPath $d) {
            $n = @(Get-ChildItem -LiteralPath $d -Filter '*.pdf' -File -ErrorAction SilentlyContinue)
            if ($n.Count -gt 0) { return @{ dir = $d; n = $n.Count; spec = $spec } }
        }
    }
    return @{ dir = ''; n = 0; spec = $spec }
}

$VIA = Resolve-VIARoot
if (-not $VIA) {
    Write-Host '  [FAIL] 找不到母倉根(往上八層都沒看到 supportive modules + functional modules)' -ForegroundColor Red
    Write-Host '         請把本腳本放回母倉根,或先 cd 進母倉再跑。' -ForegroundColor Yellow
    return
}

$enginePath = Resolve-Newest -Dir (Join-Path $VIA 'functional modules\VRN') `
                             -Pattern 'VIA_PDFPlumberPlusEngine*.py'
if (-not $enginePath) {
    Write-Host '  [FAIL] VIA_PDFPlumberPlusEngine*.py 不在位(functional modules\VRN 底下遞迴找過)' -ForegroundColor Red
    return
}

$pythonExe = Resolve-EnginePython -Preferred $Python -Via $VIA
if (-not $pythonExe) {
    Write-Host '  [FAIL] 找不到 python;用 -Python <完整路徑> 指定。' -ForegroundColor Red
    return
}

if (-not $Out) { $Out = Join-Path $VIA 'VIA_Reports\pdfplumber_plus' }
$null = New-Item -ItemType Directory -Path $Out -Force

$engineArgs = [System.Collections.Generic.List[string]]::new()
$engineArgs.Add($enginePath)

$mode = ''
if ($SelfTest) {
    $engineArgs.Add('--selftest'); $mode = 'SELFTEST'
}
elseif ($Pdf) {
    $engineArgs.Add($Pdf); $mode = ('SINGLE: ' + [System.IO.Path]::GetFileName($Pdf))
}
elseif ($In) {
    $engineArgs.Add('--scan-dir'); $engineArgs.Add($In); $mode = ('BATCH: ' + $In)
}
else {
    $box = Resolve-VRNInbox -Via $VIA
    if ($box.n -gt 0) {
        $engineArgs.Add('--scan-dir'); $engineArgs.Add($box.dir)
        $mode = ('BATCH(冊上收件夾): {0} 份 · {1}' -f $box.n, $box.dir)
    }
    else {
        # **缺料誠實停**:收件夾空不是壞掉,但也不要假裝跑了一批真報告
        $engineArgs.Add('--selftest')
        $mode = 'SELFTEST(冊上收件夾沒有 PDF=誠實跳;要跑真檔請 -Pdf <檔> 或 -In <夾>)'
    }
}

$engineArgs.Add('--out');     $engineArgs.Add($Out)     # 顯式傳,引擎寫死的預設永不啟用
$engineArgs.Add('--threads'); $engineArgs.Add([string]$Threads)
if ($NoOcr) { $engineArgs.Add('--no-ocr') }

Write-Host ''
Write-Host '=== VIA PDFPlumber-Plus ===' -ForegroundColor Cyan
Write-Host ("  母倉   : {0}  (自腳本位置解析,非硬編)" -f $VIA)
Write-Host ("  Python : {0}" -f $pythonExe)
Write-Host ("  Engine : {0}" -f $enginePath)
Write-Host ("  Mode   : {0}" -f $mode)
Write-Host ("  Output : {0}" -f $Out)
Write-Host ''

$psi = [System.Diagnostics.ProcessStartInfo]::new()
$psi.FileName               = $pythonExe
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError  = $true
$psi.UseShellExecute        = $false
$psi.CreateNoWindow         = $true
$psi.WorkingDirectory       = $Out          # 引擎的相對預設落在產出夾,不弄髒原始碼樹
$psi.StandardOutputEncoding = [System.Text.UTF8Encoding]::new($false)
$psi.StandardErrorEncoding  = [System.Text.UTF8Encoding]::new($false)
foreach ($a in $engineArgs) { $psi.ArgumentList.Add($a) }

$proc = [System.Diagnostics.Process]::new()
$proc.StartInfo = $psi
$errLines = [System.Collections.Generic.List[string]]::new()
$null = $proc.Start()
$stdoutTask = $proc.StandardOutput.ReadToEndAsync()
$sw = [System.Diagnostics.Stopwatch]::StartNew()

while (-not $proc.StandardError.EndOfStream) {
    $line = $proc.StandardError.ReadLine()
    if ($null -eq $line) { continue }
    if ($line.StartsWith('@@PROGRESS|')) {
        $parts = $line.Split('|')
        if ($parts.Count -ge 3) {
            $pct = 0.0
            $null = [double]::TryParse($parts[1], [ref]$pct)
            Write-Progress -Activity 'VIA PDFPlumber-Plus' -Status $parts[2] -PercentComplete ([int]$pct)
        }
    }
    else {
        $null = $errLines.Add($line)
        Write-Host ("  {0}" -f $line) -ForegroundColor DarkGray
    }
}

$proc.WaitForExit()
$sw.Stop()
Write-Progress -Activity 'VIA PDFPlumber-Plus' -Completed
$stdout = $stdoutTask.GetAwaiter().GetResult()

$summary = $null
try { $summary = $stdout | ConvertFrom-Json } catch { $summary = $null }

Write-Host ''
$reports = [System.Collections.Generic.List[string]]::new()
if ($null -eq $summary) {
    # **缺件 ≠ 缺料 ≠ 壞掉**(操作員原律)。上傳的那一版只會說「輸出不是 JSON」,
    # 而引擎其實**講了實話**——它 stderr 印的是「selftest 需要 reportlab 產生樣本
    # PDF」,rc=2。把一句誠實的缺件講成壞掉,人就會去 debug 一支沒壞的引擎。
    $joined = ($errLines -join ' ')
    $needPkg = [regex]::Match($joined, '需要\s*([A-Za-z0-9_\-]+)|pip install\s+([A-Za-z0-9_\-]+)|No module named\s*.?([A-Za-z0-9_\-]+)')
    if ($needPkg.Success) {
        $pkg = @($needPkg.Groups[1].Value, $needPkg.Groups[2].Value, $needPkg.Groups[3].Value) |
               Where-Object { $_ } | Select-Object -First 1
        Write-Host ("  [缺件] 引擎誠實停:少了 {0}(rc={1})——**不是壞掉**。" -f $pkg, $proc.ExitCode) -ForegroundColor Yellow
        Write-Host ("         補件:via-py vrn -m pip install {0}   然後重跑。" -f $pkg) -ForegroundColor Yellow
        Write-Host  '         或直接餵真檔跳過樣本:-Pdf <檔> / -In <夾>(這條路不需要那個套件)' -ForegroundColor Yellow
    }
    elseif ($proc.ExitCode -ne 0) {
        Write-Host ("  [RED] 引擎 rc={0} 且沒有可辨識的誠實停字樣=真的有問題,原樣列出:" -f $proc.ExitCode) -ForegroundColor Red
        Write-Host $stdout
    }
    else {
        Write-Host '  [WARN] rc=0 但輸出不是 JSON(引擎介面可能變了),原樣列出:' -ForegroundColor Yellow
        Write-Host $stdout
    }
}
else {
    $okColor = if ($summary.ok) { 'Green' } else { 'Yellow' }
    Write-Host ("  結果 ok={0} · 耗時 {1:N2}s" -f $summary.ok, $sw.Elapsed.TotalSeconds) -ForegroundColor $okColor
    if ($summary.PSObject.Properties.Name -contains 'results') {
        foreach ($r in $summary.results) {
            Write-Host ("    - {0} | 頁 {1} 表 {2} (電子 {3}/掃描 {4}) | {5:N2}s" -f `
                $r.file, $r.n_pages, $r.n_tables, $r.n_digital, $r.n_scanned, $r.elapsed_sec)
            if ($r.gates_err.Count  -gt 0) { Write-Host ("      閘 ERR : {0}" -f ($r.gates_err  -join ', ')) -ForegroundColor Red }
            if ($r.gates_warn.Count -gt 0) { Write-Host ("      閘 WARN: {0}" -f ($r.gates_warn -join ', ')) -ForegroundColor Yellow }
            if ($r.report_html) { $reports.Add($r.report_html) }
        }
    }
    else {
        Write-Host ("    run_id={0} 頁 {1} 表 {2}" -f $summary.run_id, $summary.n_pages, $summary.n_tables)
        if ($summary.report_html) { $reports.Add($summary.report_html) }
    }
}

foreach ($rep in $reports) { Write-Host ("  報告: {0}" -f $rep) -ForegroundColor Cyan }
# 零彈窗律:預設不跳出;要看加 -Open(與 via-closeout --open 同慣例)
if ($Open) {
    foreach ($rep in $reports) { if (Test-Path -LiteralPath $rep) { Start-Process -FilePath $rep } }
}
Write-Host ("  產出夾: {0}" -f $Out) -ForegroundColor Cyan
Write-Host ("  台帳  : {0}" -f (Join-Path $Out 'VIA_PDFPlumberPlus_Ledger.jsonl')) -ForegroundColor Cyan
Write-Host ''
