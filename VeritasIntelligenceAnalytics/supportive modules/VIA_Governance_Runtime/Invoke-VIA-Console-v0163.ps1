<#
================================================================================
 VIA · UNIFIED CONSOLE (VRN + VDF + VAP) — SELF-HOSTED ONE-CLICK · v0163
--------------------------------------------------------------------------------
 一支 PowerShell 同時做三件事：
   1) 開一個本機網頁伺服器 (System.Net.HttpListener, http://localhost:<Port>/)
   2) 內嵌完整 v0159 視覺鎖定 Sidebar UI（六頁），並補齊全部可操作 JS
   3) 提供 REST API 讓 UI 直接呼叫 PowerShell：資料夾/檔案瀏覽、佇列、
      檢視 Basic/Financial HTML、啟動 VRN、輪詢進度與 logs

 真實引擎：可插拔。設定 $EngineCommand（見下方）即接你的 VRN 引擎；
           未設定時自動降級為 DEMO 示範模式，UI 仍全程可操作。

 安全設計（避免九頭龍併發）：單一 listener 迴圈序列處理；唯一背景執行緒
   是 VRN worker runspace，透過 synchronized state + Monitor lock 溝通；
   檔案對話框在專用 STA runspace 執行後即回收。

 注意：本機無需系統管理員；localhost 前綴一般可直接綁定。若被拒，
   腳本會嘗試 Port..Port+11，並印出 netsh urlacl 修復指令。
================================================================================
#>
# requires PowerShell 7 (pwsh). 本檔「整支貼進主控台」或「以檔案執行」皆可 —— 無 param()，貼上不會壞。

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

# ---------------------------------------------------------- paste-safe 可調整項
# 這些是設定值。整支貼進 PowerShell 也能跑；若要改埠號/引擎，貼上前改這裡即可。
# 用 Get-Variable 保護：已在外層設過就沿用，否則給預設值（避免 StrictMode 因未定義而中止）。
if (-not (Get-Variable -Name Port          -ErrorAction SilentlyContinue)) { $Port = 8760 }
if ($null -eq $Port -or 0 -eq $Port)                                       { $Port = 8760 }
if (-not (Get-Variable -Name NoBrowser     -ErrorAction SilentlyContinue)) { $NoBrowser = $false }
if (-not (Get-Variable -Name EngineCommand -ErrorAction SilentlyContinue)) { $EngineCommand = $null }
# 接真實引擎：把下面整段取消註解並填入你的呼叫（$Ctx.Params / $Ctx.Log / $Ctx.SetProgress）：
# $EngineCommand = {
#     param($Ctx)
#     $p = $Ctx.Params    # @{Base;Input;Manifest;Python;Timeout;Recursive;OpenHtml}
#     & $Ctx.SetProgress 10 'invoke launcher'
#     & pwsh -NoProfile -File "$($p.Base)\...\Invoke-VIA-VRN-OneClick-Sidebar-v0159.ps1" 2>&1 |
#         ForEach-Object { & $Ctx.Log ([string]$_) }
#     return @{ Ok = ($LASTEXITCODE -eq 0); Gate = 'GREEN · ENGINE PASS'; ResultPath = $p.Input; RunDir = $p.Base }
# }

# ------------------------------------------------------------------ shared state
$script:State = [hashtable]::Synchronized(@{})
$script:State.Lock            = [object]::new()
$script:State.State           = 'READY'
$script:State.Progress        = 0
$script:State.Message         = '等待執行。'
$script:State.Gate            = '—'
$script:State.Registry        = '執行時驗證、匯入與註冊。'
$script:State.Reports         = 0
$script:State.Drafts          = 0
$script:State.RegisteredFiles = '—'
$script:State.Queue           = [System.Collections.Generic.List[string]]::new()
$script:State.Logs            = [System.Collections.Generic.List[string]]::new()
$script:State.ResultPath      = ''
$script:State.RunDir          = ''
$script:State.Running         = $false
$script:State.Mode            = if ($EngineCommand) { 'ENGINE' } else { 'DEMO' }

$script:Worker = @{ ps = $null; handle = $null; rs = $null }

function Add-Log {
    param([string]$Msg)
    $ts = (Get-Date).ToString('HH:mm:ss')
    [System.Threading.Monitor]::Enter($script:State.Lock)
    try {
        [void]$script:State.Logs.Add("[$ts] $Msg")
        while ($script:State.Logs.Count -gt 800) { $script:State.Logs.RemoveAt(0) }
    } finally { [System.Threading.Monitor]::Exit($script:State.Lock) }
}

# --------------------------------------------------------------- STA file dialog
$script:DialogScript = {
    param([string]$Kind)
    $result = @()
    try {
        Add-Type -AssemblyName System.Windows.Forms -ErrorAction Stop
        if ($Kind -eq 'Folder') {
            $d = New-Object System.Windows.Forms.FolderBrowserDialog
            $d.Description = '選擇資料夾'
            if ($d.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
                $result = @($d.SelectedPath)
            }
        }
        else {
            $d = New-Object System.Windows.Forms.OpenFileDialog
            switch ($Kind) {
                'Files'    { $d.Multiselect = $true;  $d.Title = '選擇投資報告檔案' }
                'Python'   { $d.Title = '選擇 Python Runtime'; $d.Filter = 'Python (python.exe)|python.exe|Executable (*.exe)|*.exe|All files (*.*)|*.*' }
                'Manifest' { $d.Title = '選擇 Manifest JSONL'; $d.Filter = 'Manifest (*.jsonl;*.json)|*.jsonl;*.json|All files (*.*)|*.*' }
                default    { $d.Title = '選擇檔案' }
            }
            if ($d.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
                if ($Kind -eq 'Files') { $result = @($d.FileNames) } else { $result = @($d.FileName) }
            }
        }
    }
    catch { $result = @() }
    ,$result
}

function Invoke-StaDialog {
    param([string]$Kind)
    $rs = [runspacefactory]::CreateRunspace()
    $rs.ApartmentState = [System.Threading.ApartmentState]::STA
    $rs.ThreadOptions  = [System.Management.Automation.Runspaces.PSThreadOptions]::UseNewThread
    $rs.Open()
    $ps = [powershell]::Create()
    $ps.Runspace = $rs
    [void]$ps.AddScript($script:DialogScript).AddArgument($Kind)
    $out = @()
    try { $out = @($ps.Invoke()) }
    catch { $out = @() }
    finally { $ps.Dispose(); $rs.Close(); $rs.Dispose() }
    return @($out)
}

# ------------------------------------------------------------- locate view HTMLs
function Find-ViewHtml {
    param([string]$Base, [string]$Which)
    if ([string]::IsNullOrWhiteSpace($Base) -or -not (Test-Path -LiteralPath $Base)) { return '' }
    $patterns = if ($Which -eq 'basic') {
        @('*basic*info*.html', '*basicinfo*.html', '*basic*.html')
    } else {
        @('*financial*data*.html', '*findata*.html', '*financial*.html')
    }
    $roots = @(
        (Join-Path $Base 'functional modules\VPNS'),
        (Join-Path $Base 'output'),
        $Base
    ) | Where-Object { Test-Path -LiteralPath $_ -ErrorAction SilentlyContinue }
    $hits = [System.Collections.Generic.List[object]]::new()
    foreach ($r in $roots) {
        foreach ($p in $patterns) {
            $found = Get-ChildItem -LiteralPath $r -Recurse -File -Filter $p -ErrorAction SilentlyContinue
            foreach ($f in $found) { [void]$hits.Add($f) }
        }
    }
    if ($hits.Count -eq 0) { return '' }
    $latest = $hits | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    return $latest.FullName
}

# ---------------------------------------------- recommended top-10 local libs
# 每功能 · 每語言 · top-10 本機免費函式庫（分區：MODULE / ENGINE / FUNCTION-LIB / OTHERS）
$script:RecommendLibs = @(
    [ordered]@{ section='FUNCTION-LIB'; func='PDF 解析'; py='pdfplumber, pypdf, pymupdf(fitz), pdfminer.six, camelot, tabula-py, pikepdf, borb, pdf2image, reportlab'; ps='iTextSharp(.NET), PdfPig(.NET), PSWritePDF, itext7(.NET), Ghostscript-CLI, pdftotext-CLI' }
    [ordered]@{ section='FUNCTION-LIB'; func='DOCX / Office'; py='python-docx, docx2txt, python-pptx, openpyxl, xlrd, unstructured, mammoth, olefile, docxtpl, aspose-words'; ps='PSWriteWord, ImportExcel, PSWriteOffice, DocX(.NET), OpenXML-SDK(.NET), COM-Word' }
    [ordered]@{ section='FUNCTION-LIB'; func='Excel / 表格'; py='openpyxl, pandas, xlsxwriter, pyexcel, tablib, csvkit, petl, polars, duckdb, great_expectations'; ps='ImportExcel, PSExcel, EPPlus(.NET), ClosedXML(.NET), Export-Csv, PSParquet' }
    [ordered]@{ section='FUNCTION-LIB'; func='HTML 解析'; py='beautifulsoup4, lxml, selectolax, html5lib, parsel, readability-lxml, trafilatura, pyquery, requests-html, markdownify'; ps='HtmlAgilityPack(.NET), AngleSharp(.NET), PSParseHTML, Invoke-WebRequest-DOM' }
    [ordered]@{ section='ENGINE'; func='JSON / JSONL / SSOT'; py='orjson, ujson, json5, jsonlines, pydantic, jsonschema, jmespath, deepdiff, dataclasses-json, msgspec'; ps='ConvertTo/From-Json, Newtonsoft.Json(.NET), PSYaml, powershell-yaml, Test-Json, PSJsonSchema' }
    [ordered]@{ section='ENGINE'; func='資料/財務處理'; py='pandas, polars, numpy, duckdb, pyarrow, sqlite-utils, statsmodels, yfinance, ta, pandera'; ps='ImportExcel, PSSQLite, dbatools, PSParquet, Math.NET(.NET)' }
    [ordered]@{ section='MODULE'; func='雜湊 / 完整性'; py='hashlib, xxhash, blake3, cryptography, pyhanko, hashid, filehash, checksumdir, merklelib, pycryptodome'; ps='Get-FileHash, Microsoft.PowerShell.Security, PSScriptAnalyzer(AST), BouncyCastle(.NET)' }
    [ordered]@{ section='MODULE'; func='日誌 / 事件'; py='loguru, structlog, logging, rich, coloredlogs, python-json-logger, eliot, sentry-sdk, tqdm, watchdog'; ps='PSFramework, Logging, PoShLog, Write-Information, PSEventViewer' }
    [ordered]@{ section='ENGINE'; func='本機 Web / UI'; py='fastapi+uvicorn, flask, bottle, http.server, waitress, starlette, nicegui, streamlit, pywebview, eel'; ps='System.Net.HttpListener(.NET), Pode, Polaris, Universal-Dashboard' }
    [ordered]@{ section='OTHERS'; func='測試 / AST / 部署'; py='pytest, hypothesis, ast(內建), libcst, coverage, mypy, ruff, tox, pyinstaller, nuitka'; ps='Pester, PSScriptAnalyzer, [Parser]::ParseFile(AST), platyPS, ps2exe, PSDepend' }
)

# ------------------------------------------------ runtime library registration
function Get-RegistryPayload {
    param([string]$Base, [string]$Python)

    $ledger   = [System.Collections.Generic.List[object]]::new()
    $snapshot = ''
    if (-not [string]::IsNullOrWhiteSpace($Base) -and (Test-Path -LiteralPath $Base)) {
        $roots = @(
            (Join-Path $Base 'supportive modules'),
            (Join-Path $Base 'functional modules\VPNS'),
            (Join-Path $Base 'functional modules'),
            $Base
        ) | Where-Object { Test-Path -LiteralPath $_ -ErrorAction SilentlyContinue }
        $seen = @{}
        foreach ($r in $roots) {
            $files = Get-ChildItem -LiteralPath $r -Recurse -File -Include *.ps1, *.psm1, *.psd1, *.py, *.json -ErrorAction SilentlyContinue
            foreach ($f in $files) {
                $key = $f.FullName.ToLowerInvariant()
                if ($seen.ContainsKey($key)) { continue }
                $seen[$key] = $true
                $h = ''
                try { $h = (Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash.ToLowerInvariant() } catch {}
                [void]$ledger.Add([ordered]@{ name = $f.Name; ext = $f.Extension.TrimStart('.'); sha = $h; path = $f.FullName })
            }
        }
        if ($ledger.Count -gt 0) {
            $concat = (($ledger | ForEach-Object { $_.sha }) -join '')
            $sha256 = [System.Security.Cryptography.SHA256]::Create()
            try {
                $bytes    = [System.Text.Encoding]::UTF8.GetBytes($concat)
                $snapshot = ([System.BitConverter]::ToString($sha256.ComputeHash($bytes)) -replace '-', '').ToLowerInvariant()
            } finally { $sha256.Dispose() }
        }
    }

    $psModules = @()
    try {
        $psModules = @(Get-Module -ListAvailable -ErrorAction SilentlyContinue |
            Sort-Object Name -Unique |
            ForEach-Object { [ordered]@{ name = [string]$_.Name; version = [string]$_.Version } })
    } catch {}

    $pyPackages = @()
    if (-not [string]::IsNullOrWhiteSpace($Python) -and (Test-Path -LiteralPath $Python)) {
        try {
            $raw = & $Python -m pip list --format=json 2>$null
            if ($raw) {
                $pyPackages = @(($raw | ConvertFrom-Json) | ForEach-Object { [ordered]@{ name = [string]$_.name; version = [string]$_.version } })
            }
        } catch {}
    }

    return [ordered]@{
        supportCount   = $ledger.Count
        psModuleCount  = @($psModules).Count
        pyPackageCount = @($pyPackages).Count
        snapshot       = $snapshot
        ledger         = @($ledger | Select-Object -First 400)
        psModules      = @($psModules | Select-Object -First 400)
        pyPackages     = @($pyPackages | Select-Object -First 400)
        recommend      = $script:RecommendLibs
    }
}

function Write-RegistrySsot {
    param([string]$Base, [hashtable]$Payload)
    if ([string]::IsNullOrWhiteSpace($Base) -or -not (Test-Path -LiteralPath $Base)) {
        return @{ ok = $false; path = ''; sha = ''; message = 'Base 不存在，未寫入。' }
    }
    $dir = Join-Path $Base 'SSOT_VPNS'
    try {
        if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
        $out = Join-Path $dir 'VIA_VRN_Runtime_Registry.v0163.json'
        ($Payload | ConvertTo-Json -Depth 9) | Set-Content -LiteralPath $out -Encoding UTF8
        $sha = (Get-FileHash -LiteralPath $out -Algorithm SHA256).Hash.ToLowerInvariant()
        return @{ ok = $true; path = $out; sha = $sha; message = 'SSOT registry 已寫入。' }
    }
    catch {
        return @{ ok = $false; path = ''; sha = ''; message = $_.Exception.Message }
    }
}

# ---------------------------------------------------- multi-subsystem registry
# 單一主控台整合多個子系統：VRN 內建於本 server；VDF/VAP 為外部 launcher。
# launcher 路徑用 <User> / <Base> 佔位，執行期展開；第一個存在者即採用。
$script:Systems = @(
    [ordered]@{
        id = 'VRN'; name = 'VRN · Research Report'; kind = 'self'
        desc = '本主控台內建：投資研究報告 SSOT 生成與六頁 Workbench'
        expectedSha = ''; launchers = @()
    }
    [ordered]@{
        id = 'VDF'; name = 'VDF · Data Foundation'; kind = 'external'
        desc = 'VDF One-Click Sidebar v0160A（HTA UI）'
        expectedSha = '778ced5d0c127d61a8d104bfcca77bcb1a6597e010b12dda80d7c23d1e43f021'
        launchers = @(
            '<User>\Downloads\Start-VIA-VDF.ps1',
            '<Base>\supportive modules\VIA_Governance_Runtime\v0160A\bin\Invoke-VIA-VDF-OneClick-Sidebar-v0160A.ps1'
        )
    }
    [ordered]@{
        id = 'VAP'; name = 'VAP · Analytics Platform'; kind = 'external'
        desc = '待安裝 / 尚未提供 launcher（自動偵測 Downloads 與 canonical runtime）'
        expectedSha = ''
        launchers = @(
            '<User>\Downloads\Start-VIA-VAP.ps1',
            '<Base>\supportive modules\VIA_Governance_Runtime\bin\Invoke-VIA-VAP-OneClick-Sidebar.ps1'
        )
    }
)

function Resolve-SystemLauncher {
    param([object]$Sys, [string]$Base)
    $userHome = $env:USERPROFILE
    if ([string]::IsNullOrWhiteSpace($userHome)) { $userHome = [Environment]::GetFolderPath('UserProfile') }
    if ([string]::IsNullOrWhiteSpace($userHome)) { $userHome = $env:HOME }
    foreach ($tpl in @($Sys.launchers)) {
        $p = $tpl -replace '<User>', $userHome
        if ($Base) { $p = $p -replace '<Base>', $Base }
        if ($p -notmatch '<Base>' -and (Test-Path -LiteralPath $p -PathType Leaf)) { return $p }
    }
    return ''
}

function Get-SystemsPayload {
    param([string]$Base)
    $out = [System.Collections.Generic.List[object]]::new()
    foreach ($s in $script:Systems) {
        if ($s.kind -eq 'self') {
            [void]$out.Add([ordered]@{ id=$s.id; name=$s.name; kind=$s.kind; desc=$s.desc; available=$true; launcher='(內建於本主控台)'; sha=''; state='BUILT-IN' })
            continue
        }
        $launcher = Resolve-SystemLauncher -Sys $s -Base $Base
        $sha = ''
        if ($launcher) { try { $sha = (Get-FileHash -LiteralPath $launcher -Algorithm SHA256).Hash.ToLowerInvariant() } catch {} }
        [void]$out.Add([ordered]@{
            id=$s.id; name=$s.name; kind=$s.kind; desc=$s.desc
            available=[bool]$launcher; launcher=$launcher; sha=$sha
            state= if ($launcher) { 'READY' } else { 'NOT-FOUND' }
        })
    }
    return @($out)
}

function Invoke-LaunchSystem {
    param([string]$Id, [string]$Base)
    $s = $script:Systems | Where-Object { $_.id -eq $Id } | Select-Object -First 1
    if (-not $s) { return @{ ok=$false; id=$Id; message="未知子系統：$Id" } }
    if ($s.kind -eq 'self') {
        return @{ ok=$true; id=$Id; message='VRN 即本主控台，已在執行中（見左側 01-06 頁）。'; launcher='(built-in)'; sha='' }
    }
    $launcher = Resolve-SystemLauncher -Sys $s -Base $Base
    if (-not $launcher) { return @{ ok=$false; id=$Id; message="找不到 $Id 的 launcher（請先安裝或確認 Base）。"; launcher=''; sha='' } }

    # AST gate（硬性）—— 以檔案內容解析，跨平台且不受路徑分隔符影響
    $code = ''
    try { $code = Get-Content -LiteralPath $launcher -Raw -ErrorAction Stop }
    catch { return @{ ok=$false; id=$Id; message=("無法讀取 launcher：" + $_.Exception.Message); launcher=$launcher; sha='' } }
    $tok = $null; $err = $null
    [System.Management.Automation.Language.Parser]::ParseInput($code, [ref]$tok, [ref]$err) | Out-Null
    if (@($err).Count -gt 0) {
        return @{ ok=$false; id=$Id; message="AST FAIL，未啟動：$launcher"; launcher=$launcher; sha='' }
    }
    $sha = ''
    try { $sha = (Get-FileHash -LiteralPath $launcher -Algorithm SHA256).Hash.ToLowerInvariant() } catch {}
    $shaNote = ''
    if ($s.expectedSha) {
        if ($sha -eq $s.expectedSha) { $shaNote = ' · SHA MATCH' } else { $shaNote = ' · SHA differs（非 canonical bin，仍以 AST 放行）' }
    }

    $pwshCmd = ''
    $cmd = Get-Command pwsh.exe -ErrorAction SilentlyContinue
    if ($cmd) { $pwshCmd = [string]$cmd.Source }
    if ([string]::IsNullOrWhiteSpace($pwshCmd)) {
        $cmd = Get-Command pwsh -ErrorAction SilentlyContinue
        if ($cmd) { $pwshCmd = [string]$cmd.Source }
    }
    if ([string]::IsNullOrWhiteSpace($pwshCmd)) { $pwshCmd = 'powershell.exe' }
    try {
        Start-Process -FilePath $pwshCmd -ArgumentList @('-NoLogo','-NoProfile','-ExecutionPolicy','Bypass','-NoExit','-File', ('"{0}"' -f $launcher))
        Add-Log ("LAUNCH $Id · GREEN_POWERSHELL_AST_PASS$shaNote · $launcher")
        return @{ ok=$true; id=$Id; message="已於新視窗啟動 $Id（AST PASS$shaNote）。"; launcher=$launcher; sha=$sha }
    }
    catch {
        return @{ ok=$false; id=$Id; message=("啟動失敗：" + $_.Exception.Message); launcher=$launcher; sha=$sha }
    }
}

# ------------------------------------------------------------------- VRN worker
$script:WorkerScript = {
    function _log {
        param([string]$m)
        $ts = (Get-Date).ToString('HH:mm:ss')
        [System.Threading.Monitor]::Enter($State.Lock)
        try {
            [void]$State.Logs.Add("[$ts] $m")
            while ($State.Logs.Count -gt 800) { $State.Logs.RemoveAt(0) }
        } finally { [System.Threading.Monitor]::Exit($State.Lock) }
    }
    function _prog {
        param([int]$pct, [string]$m)
        $State.Progress = $pct
        if ($m) { $State.Message = $m }
    }
    try {
        if ($EngineCommand) {
            $State.Mode = 'ENGINE'
            _log 'ENGINE 模式：呼叫已設定的 $EngineCommand'
            _prog 3 'ENGINE 啟動中…'
            $ctx = @{
                Params      = $P
                State       = $State
                Log         = ${function:_log}
                SetProgress = ${function:_prog}
            }
            $r = & $EngineCommand $ctx
            $ok = $false; $gate = '—'
            if ($r -is [hashtable]) {
                if ($r.ContainsKey('Ok'))         { $ok = [bool]$r['Ok'] }
                if ($r.ContainsKey('Gate'))       { $gate = [string]$r['Gate'] }
                if ($r.ContainsKey('ResultPath')) { $State.ResultPath = [string]$r['ResultPath'] }
                if ($r.ContainsKey('RunDir'))     { $State.RunDir = [string]$r['RunDir'] }
            }
            $State.Progress = 100
            if ($gate -ne '—') { $State.Gate = $gate }
            elseif ($ok)       { $State.Gate = 'GREEN · ENGINE PASS' }
            else               { $State.Gate = 'AMBER · ENGINE RETURNED' }
            $State.State = 'DONE'
            _log 'ENGINE 執行完成。'
        }
        else {
            $State.Mode = 'DEMO'
            _log 'DEMO 模式：未設定 $EngineCommand，執行可操作示範流程。'
            $stages = @(
                @{ p = 8;   m = 'RESOLVE · 由 Base 相對推導 authority/schema/adapter/ledger/runtime' },
                @{ p = 22;  m = 'INTAKE · 掃描 Input 目錄與 Manifest' },
                @{ p = 40;  m = 'REGISTRY · SHA 驗證支援檔與核准 PowerShell modules' },
                @{ p = 58;  m = 'WORKER · Basic Info / Financial Data 生成' },
                @{ p = 76;  m = 'GATE · 全景式三輪分析驗證' },
                @{ p = 90;  m = 'STAGE · 產生 enabled=false 草稿（不改 canonical、不自動核准日期）' },
                @{ p = 100; m = 'DONE · 報告已就緒' }
            )
            foreach ($s in $stages) {
                Start-Sleep -Milliseconds 750
                _prog ([int]$s.p) ([string]$s.m)
                _log ("[{0,3}%] {1}" -f [int]$s.p, [string]$s.m)
            }
            $State.Gate            = 'GREEN · DEMO GATE · 3-round panorama PASS'
            $State.Reports         = 2
            $State.Drafts          = $State.Queue.Count
            $State.RegisteredFiles = '示範模式（未接真實 registry）'
            $State.ResultPath      = [string]$P['Input']
            $State.RunDir          = [string]$P['Base']
            $State.State           = 'DONE'
            _log 'DEMO 執行完成。設定 $EngineCommand 即可接真實 VRN 引擎。'
        }
    }
    catch {
        $State.State = 'ERROR'
        $State.Gate  = 'RED · SAFE CATCH'
        _log ('SAFE CATCH: ' + $_.Exception.Message)
    }
    finally {
        $State.Running = $false
    }
}

function Start-VrnRun {
    param([hashtable]$P)
    if ($script:State.Running) { return }
    $script:State.Running    = $true
    $script:State.State      = 'RUNNING'
    $script:State.Progress   = 1
    $script:State.Message    = '啟動中…'
    $script:State.Gate       = '—'
    $script:State.ResultPath = ''
    $script:State.RunDir     = ''
    Add-Log ('RUN 觸發 · Base=' + [string]$P['Base'])

    $rs = [runspacefactory]::CreateRunspace()
    $rs.Open()
    $rs.SessionStateProxy.SetVariable('State', $script:State)
    $rs.SessionStateProxy.SetVariable('P', $P)
    $rs.SessionStateProxy.SetVariable('EngineCommand', $EngineCommand)
    $ps = [powershell]::Create()
    $ps.Runspace = $rs
    [void]$ps.AddScript($script:WorkerScript)
    $handle = $ps.BeginInvoke()
    $script:Worker.ps     = $ps
    $script:Worker.handle = $handle
    $script:Worker.rs     = $rs
}

# ----------------------------------------------------------------- HTTP helpers
function Send-Response {
    param($Context, [string]$Body, [string]$ContentType = 'application/json; charset=utf-8', [int]$Status = 200)
    $resp  = $Context.Response
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($Body)
    $resp.StatusCode      = $Status
    $resp.ContentType     = $ContentType
    $resp.ContentLength64 = $bytes.Length
    $resp.OutputStream.Write($bytes, 0, $bytes.Length)
    $resp.OutputStream.Close()
}

function Read-Body {
    param($Context)
    $req = $Context.Request
    if (-not $req.HasEntityBody) { return '' }
    $reader = [System.IO.StreamReader]::new($req.InputStream, $req.ContentEncoding)
    try { return $reader.ReadToEnd() } finally { $reader.Close() }
}

function Get-StatusPayload {
    [System.Threading.Monitor]::Enter($script:State.Lock)
    try {
        return [ordered]@{
            state      = $script:State.State
            progress   = $script:State.Progress
            message    = $script:State.Message
            gate       = $script:State.Gate
            registry   = $script:State.Registry
            reports    = $script:State.Reports
            drafts     = $script:State.Drafts
            registered = $script:State.RegisteredFiles
            queueCount = $script:State.Queue.Count
            queue      = @($script:State.Queue)
            result     = $script:State.ResultPath
            rundir     = $script:State.RunDir
            running    = $script:State.Running
            mode       = $script:State.Mode
            logs       = ($script:State.Logs -join "`n")
        }
    } finally { [System.Threading.Monitor]::Exit($script:State.Lock) }
}

function Get-ConfigPayload {
    $userHome = $env:USERPROFILE
    if ([string]::IsNullOrWhiteSpace($userHome)) { $userHome = [Environment]::GetFolderPath('UserProfile') }
    if ([string]::IsNullOrWhiteSpace($userHome)) { $userHome = $env:HOME }
    if ([string]::IsNullOrWhiteSpace($userHome)) { $userHome = '.' }
    $defBase = Join-Path $userHome 'Downloads\VeritasIntelligenceAnalytics'
    return [ordered]@{
        base      = $defBase
        input     = '<Base>\_vrn_research_report_incremental_intake_v0156\incoming'
        manifest  = '<Base>\_vrn_research_report_incremental_intake_v0156\VRN_ResearchReport_Incremental_Manifest.v0156.jsonl'
        python    = (Join-Path $userHome 'envs\via_core_312\Scripts\python.exe')
        timeout   = 2400
        recursive = $true
        openHtml  = $true
        mode      = $script:State.Mode
    }
}

function Convert-Json { param($Obj) return ($Obj | ConvertTo-Json -Depth 8 -Compress) }

function Invoke-Route {
    param($Context)
    $req    = $Context.Request
    $path   = $req.Url.AbsolutePath
    $method = $req.HttpMethod

    switch -Regex ($path) {

        '^/favicon\.ico$' { Send-Response $Context '' 'image/x-icon'; return }

        '^/$' { Send-Response $Context $script:Html 'text/html; charset=utf-8'; return }

        '^/api/config$' { Send-Response $Context (Convert-Json (Get-ConfigPayload)); return }

        '^/api/status$' { Send-Response $Context (Convert-Json (Get-StatusPayload)); return }

        '^/api/browse$' {
            $kind = 'Folder'
            $body = Read-Body $Context
            if ($body) {
                try { $d = $body | ConvertFrom-Json; if ($d.kind) { $kind = [string]$d.kind } } catch {}
            }
            $paths = @(Invoke-StaDialog -Kind $kind)
            Add-Log ("BROWSE $kind -> " + $paths.Count + ' 項')
            Send-Response $Context (Convert-Json @{ paths = $paths })
            return
        }

        '^/api/queue/add$' {
            $body  = Read-Body $Context
            $added = 0
            if ($body) {
                try {
                    $d = $body | ConvertFrom-Json
                    if ($d.paths) {
                        [System.Threading.Monitor]::Enter($script:State.Lock)
                        try {
                            foreach ($p in @($d.paths)) {
                                $sp = [string]$p
                                if ($sp -and -not $script:State.Queue.Contains($sp)) {
                                    [void]$script:State.Queue.Add($sp); $added++
                                }
                            }
                        } finally { [System.Threading.Monitor]::Exit($script:State.Lock) }
                    }
                } catch {}
            }
            Add-Log "QUEUE +$added（總計 $($script:State.Queue.Count)）"
            Send-Response $Context (Convert-Json @{ queueCount = $script:State.Queue.Count })
            return
        }

        '^/api/queue/clear$' {
            [System.Threading.Monitor]::Enter($script:State.Lock)
            try { $script:State.Queue.Clear() } finally { [System.Threading.Monitor]::Exit($script:State.Lock) }
            Add-Log 'QUEUE 已清空'
            Send-Response $Context (Convert-Json @{ queueCount = 0 })
            return
        }

        '^/api/run$' {
            $body = Read-Body $Context
            $P = @{ Base=''; Input=''; Manifest=''; Python=''; Timeout=2400; Recursive=$true; OpenHtml=$true }
            if ($body) {
                try {
                    $d = $body | ConvertFrom-Json
                    if ($d.base)      { $P['Base']      = [string]$d.base }
                    if ($d.input)     { $P['Input']     = [string]$d.input }
                    if ($d.manifest)  { $P['Manifest']  = [string]$d.manifest }
                    if ($d.python)    { $P['Python']    = [string]$d.python }
                    if ($d.timeout)   { $P['Timeout']   = [int]$d.timeout }
                    if ($null -ne $d.recursive) { $P['Recursive'] = [bool]$d.recursive }
                    if ($null -ne $d.openHtml)  { $P['OpenHtml']  = [bool]$d.openHtml }
                } catch {}
            }
            if ($P['Base']) {
                if ($P['Input'])    { $P['Input']    = $P['Input']    -replace '<Base>', $P['Base'] }
                if ($P['Manifest']) { $P['Manifest'] = $P['Manifest'] -replace '<Base>', $P['Base'] }
            }
            Start-VrnRun -P $P
            Send-Response $Context (Convert-Json @{ started = $true; mode = $script:State.Mode })
            return
        }

        '^/api/view$' {
            $which = [string]$req.QueryString['which']
            $base  = [string]$req.QueryString['base']
            if (-not $which) { $which = 'basic' }
            $file = Find-ViewHtml -Base $base -Which $which
            $html = ''
            if ($file -and (Test-Path -LiteralPath $file)) {
                try { $html = Get-Content -LiteralPath $file -Raw -Encoding UTF8 } catch { $html = '' }
            }
            Send-Response $Context (Convert-Json @{ path = $file; html = $html })
            return
        }

        '^/api/open$' {
            $body = Read-Body $Context
            $ok = $false
            if ($body) {
                try {
                    $d = $body | ConvertFrom-Json
                    $target = [string]$d.path
                    if ($target -and (Test-Path -LiteralPath $target)) {
                        Start-Process -FilePath $target
                        $ok = $true
                        Add-Log "OPEN $target"
                    }
                } catch { Add-Log ('OPEN 失敗: ' + $_.Exception.Message) }
            }
            Send-Response $Context (Convert-Json @{ ok = $ok })
            return
        }

        '^/api/systems$' {
            $base = [string]$req.QueryString['base']
            Send-Response $Context (Convert-Json (Get-SystemsPayload -Base $base))
            return
        }

        '^/api/launch$' {
            $body = Read-Body $Context
            $id = ''; $base = ''
            if ($body) {
                try { $d = $body | ConvertFrom-Json; if ($d.id) { $id = [string]$d.id }; if ($d.base) { $base = [string]$d.base } } catch {}
            }
            $res = Invoke-LaunchSystem -Id $id -Base $base
            Send-Response $Context (Convert-Json $res)
            return
        }

        '^/api/registry$' {
            $base = [string]$req.QueryString['base']
            $py   = [string]$req.QueryString['python']
            $payload = Get-RegistryPayload -Base $base -Python $py
            [System.Threading.Monitor]::Enter($script:State.Lock)
            try {
                $script:State.RegisteredFiles = ("{0} 檔 / {1} PS / {2} PY" -f $payload.supportCount, $payload.psModuleCount, $payload.pyPackageCount)
            } finally { [System.Threading.Monitor]::Exit($script:State.Lock) }
            Add-Log ("REGISTRY 掃描 · " + $script:State.RegisteredFiles)
            Send-Response $Context (Convert-Json $payload)
            return
        }

        '^/api/registry/write$' {
            $body = Read-Body $Context
            $base = ''; $py = ''
            if ($body) {
                try { $d = $body | ConvertFrom-Json; if ($d.base) { $base = [string]$d.base }; if ($d.python) { $py = [string]$d.python } } catch {}
            }
            $payload = Get-RegistryPayload -Base $base -Python $py
            $res = Write-RegistrySsot -Base $base -Payload $payload
            Add-Log ("REGISTRY WRITE · " + $res.message + " " + $res.path)
            Send-Response $Context (Convert-Json $res)
            return
        }

        '^/api/shutdown$' {
            Add-Log 'SHUTDOWN 由 UI 觸發'
            Send-Response $Context (Convert-Json @{ ok = $true })
            try { $script:Listener.Stop() } catch {}
            return
        }

        default {
            Send-Response $Context (Convert-Json @{ error = 'not found'; path = $path }) 'application/json; charset=utf-8' 404
            return
        }
    }
}

# ------------------------------------------------------------------- UI (HTML)
$script:Html = @'
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA · Unified Console · v0163</title>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;500;700&family=DM+Mono:wght@400;500&family=Noto+Sans+TC:wght@400;500;700&display=swap" rel="stylesheet">
<style>
:root{
    --bg:#f5f4f0;--paper:#fff;--ink:#1e1d1a;--ink2:#33403f;
    --mut:#6b6860;--mut2:#9c9890;--line:#dbd9d3;--soft:#ecebe6;
    --up:#c96b5a;--down:#5a9e6f;--blue:#4c78a8;--teal:#439a9a;
    --am:#c4943a;--vi:#7a6daa;
    --sidebar:#f8f7f3;
    --reson:linear-gradient(90deg,#c96b5a 0 14.2%,#c4943a 0 28.5%,#5a9e6f 0 42.8%,#439a9a 0 57.1%,#4c78a8 0 71.4%,#7a6daa 0 85.7%,#1e1d1a 0 100%)
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{min-height:100%}
body{
    background:var(--bg);color:var(--ink2);
    font:11px/1.5 "DM Sans","Noto Sans TC","Microsoft JhengHei",sans-serif;
    -webkit-font-smoothing:antialiased
}
.bar{position:fixed;top:0;left:0;right:0;height:4px;background:var(--reson);z-index:100}
.appShell{min-height:100vh}
.sidebar{
    position:fixed;top:4px;left:0;bottom:0;width:232px;
    background:var(--sidebar);border-right:1px solid var(--line);
    padding:18px 14px 16px;overflow:auto;z-index:60
}
.sideBrand{padding:2px 5px 15px;border-bottom:2px solid var(--ink)}
.sideKicker{
    font:700 8px "DM Mono",Consolas,monospace;
    letter-spacing:1.5px;color:var(--mut);text-transform:uppercase
}
.sideTitle{
    margin-top:7px;font:800 17px/1.2 "Syne","Microsoft JhengHei",sans-serif;
    color:var(--ink)
}
.sideTitle span{color:var(--up)}
.sideSub{margin-top:6px;color:var(--mut);font-size:9.5px}
.sideGroup{margin-top:18px}
.sideGroupTitle{
    margin:0 6px 6px;font:700 7.5px "DM Mono",Consolas,monospace;
    color:var(--mut2);letter-spacing:1.2px;text-transform:uppercase
}
.sideNav button{
    display:block;width:100%;text-align:left;margin-bottom:4px;
    border:1px solid transparent;border-radius:4px;background:transparent;
    color:var(--ink2);padding:8px 9px;
    font:700 8.5px "DM Mono",Consolas,monospace;cursor:pointer
}
.sideNav button:hover{background:var(--paper);border-color:var(--line)}
.sideNav button.active{
    background:var(--ink);color:#fff;border-color:var(--ink)
}
.sideNav button .n{
    display:inline-block;min-width:21px;color:var(--mut2)
}
.sideNav button.active .n{color:#fff}
.sideMetrics{
    margin-top:16px;border-top:1px solid var(--line);padding-top:12px
}
.sideMetric{
    display:flex;justify-content:space-between;gap:8px;
    padding:5px 3px;border-bottom:1px solid var(--soft)
}
.sideMetric .k{
    font:700 7.5px "DM Mono",Consolas,monospace;
    color:var(--mut);text-transform:uppercase
}
.sideMetric .v{
    max-width:112px;text-align:right;overflow-wrap:anywhere;
    font:700 8px "DM Mono",Consolas,monospace;color:var(--ink)
}
.sideFooter{margin-top:14px}
.sideFooter button{width:100%}
.workspace{margin-left:232px;min-height:100vh}
.workspaceInner{max-width:1240px;margin:0 auto;padding:0 22px 54px}
header{padding:22px 0 9px;margin-bottom:12px;border-bottom:2px solid var(--ink)}
.kicker{
    font:700 10px "DM Mono",Consolas,monospace;
    letter-spacing:2.2px;color:var(--mut);text-transform:uppercase;margin-bottom:7px
}
h1{
    font:800 20px/1.2 "Syne","Microsoft JhengHei",sans-serif;color:var(--ink)
}
h1 span{color:var(--up)}
.sub{margin-top:6px;font-size:10.5px;color:var(--mut);max-width:1030px}
.sub b{color:var(--ink2)}
.page{display:none}.page.active{display:block}
.hero{display:flex;gap:10px;flex-wrap:wrap;margin:14px 0 4px}
.hc{
    background:var(--paper);border:1px solid var(--line);
    border-radius:5px;padding:10px 16px;min-width:130px
}
.hc .v{
    font:800 18px "Syne","Microsoft JhengHei",sans-serif;
    line-height:1;overflow-wrap:anywhere
}
.hc .l{
    font:600 8px "DM Mono",Consolas,monospace;
    color:var(--mut);text-transform:uppercase;margin-top:4px
}
h2{
    font:800 13px "Syne","Microsoft JhengHei",sans-serif;
    color:var(--ink);margin:24px 0 8px;padding-bottom:5px;
    border-bottom:1px solid var(--line)
}
h2 .en{
    font:600 8px "DM Mono",Consolas,monospace;
    color:var(--mut2);letter-spacing:1px;margin-left:8px;text-transform:uppercase
}
.panel{
    background:var(--paper);border:1px solid var(--line);
    border-radius:6px;padding:14px 16px;margin-top:10px
}
.panel.input{border-left:3px solid var(--up)}
.panel.summary{border-left:3px solid var(--teal)}
.panel.basic{border-left:3px solid var(--blue)}
.panel.financial{border-left:3px solid var(--vi)}
.panel.queuePanel{border-left:3px solid var(--am)}
.panel.registryPanel{border-left:3px solid var(--down)}
.panel.logPanel{border-left:3px solid var(--ink)}
.homeColumns{display:flex;gap:12px;align-items:flex-start}
.homeMain{flex:1;min-width:0}
.homeAside{width:355px;min-width:320px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:9px}
.full{grid-column:1/3}
.field{border-bottom:1px solid var(--soft);padding:8px 0}
.field:last-child{border-bottom:none}
label{
    display:block;font:700 8px "DM Mono",Consolas,monospace;
    color:var(--mut);text-transform:uppercase;margin-bottom:5px
}
.row{display:flex;align-items:center;gap:6px}
input[type=text],input[type=number]{
    width:100%;border:1px solid var(--line);border-radius:4px;padding:7px 9px;
    background:#fafaf8;color:var(--ink2);
    font:500 10px "DM Mono",Consolas,monospace
}
input:focus{outline:1px solid var(--teal);border-color:var(--teal)}
.check{display:flex;align-items:center;gap:7px;min-height:30px}
button{
    border:1px solid var(--line);border-radius:4px;padding:7px 10px;
    background:var(--paper);color:var(--ink2);
    font:700 8px "DM Mono",Consolas,monospace;cursor:pointer
}
button:hover{background:#fafaf8}
button.primary{color:#fff;background:var(--teal);border-color:var(--teal)}
button.danger{color:#fff;background:var(--up);border-color:var(--up)}
button:disabled{opacity:.45;cursor:default}
.hint{color:var(--mut);font-size:9px;margin-top:4px}
.drop{
    border:1px dashed var(--mut2);border-radius:5px;background:#fafaf8;
    padding:18px;text-align:center;color:var(--mut)
}
.drop.active{border-color:var(--teal);background:#eef7f5}
.drop b{
    display:block;color:var(--ink);
    font:800 11px "Syne","Microsoft JhengHei",sans-serif
}
.drop span{display:block;margin-top:4px;font-size:9px}
.actions{display:flex;gap:6px;flex-wrap:wrap;margin-top:9px}
.queue{
    margin-top:10px;border:1px solid var(--line);border-radius:4px;
    max-height:430px;overflow:auto
}
.queueItem{
    display:flex;justify-content:space-between;gap:10px;
    padding:7px 9px;border-bottom:1px solid var(--soft);
    font:500 9px "DM Mono",Consolas,monospace
}
.queueItem:last-child{border-bottom:none}
.progressOuter{
    height:9px;background:var(--soft);border-radius:3px;
    overflow:hidden;margin-top:12px
}
.progressInner{height:100%;width:0%;background:var(--reson);transition:width .3s ease}
.status{
    display:grid;grid-template-columns:118px 1fr;
    gap:5px 10px;margin-top:11px
}
.k{
    font:700 8px "DM Mono",Consolas,monospace;
    color:var(--mut);text-transform:uppercase
}
.code{
    font-family:"DM Mono",Consolas,monospace;
    overflow-wrap:anywhere
}
.log{
    background:#f8f8f5;color:var(--ink2);
    border:1px solid var(--line);border-radius:4px;padding:10px;
    min-height:470px;max-height:650px;overflow:auto;white-space:pre-wrap;
    font:500 9px/1.55 "DM Mono",Consolas,monospace
}
.pill{
    display:inline-block;font:700 7.5px "DM Mono",Consolas,monospace;
    color:#fff;border-radius:3px;padding:2px 7px;letter-spacing:.3px
}
.ok{background:var(--down)}.warn{background:var(--am)}
.blind{background:var(--mut2)}.prov{background:var(--vi)}
.viewerTop{
    display:flex;align-items:center;justify-content:space-between;
    gap:10px;flex-wrap:wrap
}
.viewerPath{
    color:var(--mut);font:500 9px "DM Mono",Consolas,monospace;
    overflow-wrap:anywhere;margin-top:6px
}
.frameWrap{
    margin-top:10px;border:1px solid var(--line);
    background:#fafaf8;min-height:620px
}
iframe{
    display:block;width:100%;height:620px;border:0;background:#fff
}
.emptyView{padding:80px 20px;text-align:center;color:var(--mut)}
.emptyView b{
    display:block;color:var(--ink);
    font:800 14px "Syne","Microsoft JhengHei",sans-serif;margin-bottom:6px
}
.registryGrid{
    display:grid;grid-template-columns:repeat(3,1fr);gap:9px;margin-top:10px
}
.registryCard{
    border:1px solid var(--line);border-radius:5px;background:#fafaf8;
    padding:11px;min-height:88px
}
.registryCard .l{
    font:700 7.5px "DM Mono",Consolas,monospace;
    color:var(--mut);text-transform:uppercase
}
.registryCard .v{
    margin-top:7px;color:var(--ink);
    font:700 10px/1.45 "DM Mono",Consolas,monospace;
    overflow-wrap:anywhere
}
.quickLinks{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-top:10px}
.quickLink{
    border:1px solid var(--line);border-radius:5px;padding:10px;
    cursor:pointer;background:#fafaf8
}
.quickLink:hover{background:var(--paper)}
.quickLink b{
    display:block;color:var(--ink);
    font:800 11px "Syne","Microsoft JhengHei",sans-serif
}
.quickLink span{display:block;color:var(--mut);font-size:9px;margin-top:4px}
.regBar{display:flex;gap:6px;flex-wrap:wrap;margin:12px 0 4px;align-items:center}
.regSection{margin-top:14px}
.regSection h3{font:800 10px "Syne","Microsoft JhengHei",sans-serif;color:var(--ink);margin-bottom:6px;letter-spacing:.4px}
.regTable{width:100%;border-collapse:collapse;background:var(--paper);border:1px solid var(--line);border-radius:5px;overflow:hidden;table-layout:fixed}
.regTable th,.regTable td{text-align:left;padding:5px 8px;border-bottom:1px solid var(--soft);font:500 8.5px/1.45 "DM Mono",Consolas,monospace;overflow-wrap:anywhere;word-break:break-word;vertical-align:top}
.regTable th{background:#faf9f6;color:var(--mut);text-transform:uppercase;font-weight:700;letter-spacing:.4px}
.regTable tr:last-child td{border-bottom:none}
.regTable .cSec{width:88px;color:var(--vi);font-weight:700}
.regTable .cFunc{width:112px;color:var(--ink);font-weight:700}
.regTable .cSmall{width:60px;color:var(--mut)}
.tag{display:inline-block;font:700 7px "DM Mono",Consolas,monospace;color:#fff;background:var(--down);border-radius:3px;padding:1px 6px;margin-left:6px}
.regScroll{max-height:300px;overflow:auto;border:1px solid var(--line);border-radius:5px}
.regScroll .regTable{border:0;border-radius:0}
.footer{
    margin-top:14px;color:var(--mut2);
    font:500 8px "DM Mono",Consolas,monospace
}
@media(max-width:980px){
    .sidebar{width:194px}
    .workspace{margin-left:194px}
    .homeColumns{display:block}
    .homeAside{width:auto;min-width:0}
    .grid{grid-template-columns:1fr}
    .full{grid-column:auto}
    .registryGrid{grid-template-columns:1fr}
}
</style>
</head>
<body>
<div class="bar"></div>
<div class="appShell">
<aside class="sidebar">
<div class="sideBrand">
<div class="sideKicker">VERITAS INTELLIGENCE ANALYTICS</div>
<div class="sideTitle">VRN <span>Workbench</span></div>
<div class="sideSub">Visual Lock · Unified Console · v0163</div>
</div>

<div class="sideGroup">
<div class="sideGroupTitle">Systems</div>
<div class="sideNav">
<button id="nav-systems" onclick="switchPage('systems')"><span class="n">00</span>SYSTEMS · VRN / VDF / VAP</button>
</div>
</div>

<div class="sideGroup">
<div class="sideGroupTitle">Workspace</div>
<div class="sideNav">
<button id="nav-home" onclick="switchPage('home')"><span class="n">01</span>HOME · INPUT + SUMMARY</button>
<button id="nav-basic" onclick="switchPage('basic')"><span class="n">02</span>BASIC INFO</button>
<button id="nav-financial" onclick="switchPage('financial')"><span class="n">03</span>FINANCIAL DATA</button>
</div>
</div>

<div class="sideGroup">
<div class="sideGroupTitle">Operations</div>
<div class="sideNav">
<button id="nav-queue" onclick="switchPage('queue')"><span class="n">04</span>REPORT QUEUE</button>
<button id="nav-registry" onclick="switchPage('registry')"><span class="n">05</span>RUNTIME REGISTRY</button>
<button id="nav-logs" onclick="switchPage('logs')"><span class="n">06</span>EXECUTION LOGS</button>
</div>
</div>

<div class="sideMetrics">
<div class="sideMetric"><div class="k">STATE</div><div id="sideState" class="v">READY</div></div>
<div class="sideMetric"><div class="k">PROGRESS</div><div id="sideProgress" class="v">0%</div></div>
<div class="sideMetric"><div class="k">QUEUE</div><div id="sideQueue" class="v">0</div></div>
<div class="sideMetric"><div class="k">GATE</div><div id="sideGate" class="v">—</div></div>
<div class="sideMetric"><div class="k">MODE</div><div id="sideMode" class="v">—</div></div>
</div>

<div class="sideFooter">
<button class="danger" onclick="closeWorkbench()">CLOSE WORKBENCH</button>
</div>
</aside>

<div class="workspace">
<div class="workspaceInner">
<header>
<div class="kicker">VRN RESEARCH REPORT SSOT · ACTIVE GENERATION · VISUAL LOCK</div>
<h1 id="pageTitle">首頁 · 輸入與摘要</h1>
<p id="pageSubtitle" class="sub">Home · Input + Summary</p>
</header>

<section id="page-home" class="page active">
<div class="hero">
<div class="hc"><div id="summaryState" class="v" style="color:var(--teal)">READY</div><div class="l">WORKBENCH STATE</div></div>
<div class="hc"><div id="summaryProgress" class="v">0%</div><div class="l">PROGRESS</div></div>
<div class="hc"><div id="homeQueue" class="v">0</div><div class="l">INPUT QUEUE</div></div>
<div class="hc"><div id="summaryReports" class="v">0</div><div class="l">STAGED REPORTS</div></div>
<div class="hc"><div id="summaryDrafts" class="v">0</div><div class="l">DISABLED DRAFTS</div></div>
<div class="hc"><div id="summaryRegistry" class="v">—</div><div class="l">REGISTERED FILES</div></div>
<div class="hc" style="min-width:270px"><div id="summaryGate" class="v" style="font:700 9px/1.35 'DM Mono',Consolas,monospace">—</div><div class="l">LATEST GATE</div></div>
</div>

<div class="homeColumns">
<div class="homeMain">
<h2>① 輸入參數 <span class="en">seven runtime parameters</span></h2>
<div class="panel input">
<div class="grid">
<div class="field full">
<label>1. Base · 母系統根目錄</label>
<div class="row"><input id="base" type="text"><button onclick="browseField('Folder','base')">WINDOWS SEARCH</button></div>
<div class="hint">其餘 authority、schema、adapter、ledger 與 runtime 路徑全部由 Base 相對推導。</div>
</div>
<div class="field full">
<label>2. Input · 投資報告輸入目錄</label>
<div class="row"><input id="input" type="text"><button onclick="browseField('Folder','input')">WINDOWS SEARCH</button><button onclick="openManual(document.getElementById('input').value)">OPEN</button></div>
</div>
<div class="field full">
<label>3. Manifest · Operational JSONL</label>
<div class="row"><input id="manifest" type="text"><button onclick="browseField('Manifest','manifest')">WINDOWS SEARCH</button><button onclick="openManual(document.getElementById('manifest').value)">OPEN</button></div>
</div>
<div class="field"><label>4. Python Runtime</label><div class="row"><input id="python" type="text"><button onclick="browseField('Python','python')">SEARCH</button></div></div>
<div class="field"><label>5. Timeout Seconds</label><input id="timeout" type="number" min="60" max="86400" step="60"></div>
<div class="field"><label>6. Recursive Scan</label><div class="check"><input id="recursive" type="checkbox"><span>資料夾輸入採遞迴搜尋</span></div></div>
<div class="field"><label>7. Open Result HTML</label><div class="check"><input id="openHtml" type="checkbox"><span>成功後自動開啟 v0156 結果</span></div></div>
</div>
</div>
</div>

<div class="homeAside">
<h2>② 啟動與摘要 <span class="en">one-click execution</span></h2>
<div class="panel summary">
<div class="actions">
<button id="run" class="primary" onclick="submitRun()">ONE-CLICK START VRN</button>
<button id="result" disabled onclick="openDataPath(this)">RESULT</button>
<button id="runDir" disabled onclick="openDataPath(this)">RUNDIR</button>
</div>
<div class="progressOuter"><div id="bar" class="progressInner"></div></div>
<div class="status">
<div class="k">STATE</div><div id="state"><span class="pill blind">READY</span></div>
<div class="k">MESSAGE</div><div id="message">等待執行。</div>
<div class="k">GATE</div><div id="gate" class="code">—</div>
<div class="k">REGISTRY</div><div id="registry" class="code">執行時驗證、匯入與註冊。</div>
</div>
</div>

<h2>③ 快速拖曳 <span class="en">external report intake</span></h2>
<div id="dropHome" class="drop">
<b>從 Windows 檔案總管拖曳投資報告</b>
<span>詳細佇列請使用左側 REPORT QUEUE</span>
</div>
<div class="actions">
<button onclick="addFiles()">SELECT FILES</button>
<button onclick="addFolder()">SELECT FOLDER</button>
<button onclick="switchPage('queue')">OPEN QUEUE</button>
</div>

<div class="quickLinks">
<div class="quickLink" onclick="switchPage('basic')"><b>Basic Info</b><span>查看最新基本資料頁</span></div>
<div class="quickLink" onclick="switchPage('financial')"><b>Financial Data</b><span>查看最新財務資料頁</span></div>
</div>
</div>
</div>
</section>

<section id="page-systems" class="page">
<h2>整合子系統 <span class="en">one console · start any subsystem</span></h2>
<div class="panel registryPanel">
<div class="regBar">
<button class="primary" onclick="loadSystems()">REFRESH STATUS</button>
<span id="sysLaunchMsg" class="hint" style="margin:0">VRN 內建；VDF/VAP 偵測到 launcher 後可一鍵啟動。</span>
</div>
<div id="sysCards" class="registryGrid"></div>
<div class="regSection">
<h3>子系統啟動矩陣</h3>
<table class="regTable" id="sysMatrix"><tbody></tbody></table>
</div>
<div class="hint" style="margin-top:10px">VRN 內建於本主控台；VDF/VAP 若在 Downloads 或 canonical runtime 找到 launcher，按 START 會先做 AST gate（過關才啟動），並於新視窗執行，不阻塞本主控台。</div>
</div>
</section>

<section id="page-basic" class="page">
<h2>Basic Info <span class="en">independent primary page</span></h2>
<div class="panel basic">
<div class="viewerTop">
<div><span class="pill" style="background:var(--blue)">BASIC INFO</span><div id="basicPath" class="viewerPath"></div></div>
<div class="actions"><button onclick="loadView('basic')">RELOAD</button><button onclick="openView('basic')">OPEN EXTERNAL</button></div>
</div>
<div class="frameWrap">
<div id="basicEmpty" class="emptyView"><b>Basic Info HTML 尚未找到</b>Workbench 會從 Base 的 VRN functional modules、output 與最新 run folders 自動尋找。</div>
<iframe id="basicFrame" style="display:none"></iframe>
</div>
</div>
</section>

<section id="page-financial" class="page">
<h2>Financial Data <span class="en">independent primary page</span></h2>
<div class="panel financial">
<div class="viewerTop">
<div><span class="pill prov">FINANCIAL DATA</span><div id="financialPath" class="viewerPath"></div></div>
<div class="actions"><button onclick="loadView('financial')">RELOAD</button><button onclick="openView('financial')">OPEN EXTERNAL</button></div>
</div>
<div class="frameWrap">
<div id="financialEmpty" class="emptyView"><b>Financial Data HTML 尚未找到</b>Workbench 會從 Base 的 VRN functional modules、output 與最新 run folders 自動尋找。</div>
<iframe id="financialFrame" style="display:none"></iframe>
</div>
</div>
</section>

<section id="page-queue" class="page">
<h2>報告佇列 <span class="en">windows I/O + drag and drop</span></h2>
<div class="panel queuePanel">
<div id="dropQueue" class="drop">
<b>拖曳投資報告至佇列</b>
<span>PDF、DOCX、TXT、HTML、JSON、CSV、Excel、PowerPoint</span>
</div>
<div class="actions">
<button onclick="addFiles()">WINDOWS SELECT FILES</button>
<button onclick="addFolder()">WINDOWS SELECT FOLDER</button>
<button onclick="clearQueue()">CLEAR QUEUE</button>
<button onclick="switchPage('home')">BACK TO HOME</button>
</div>
<div class="status">
<div class="k">QUEUE COUNT</div><div id="queueCount">0</div>
<div class="k">INPUT TARGET</div><div class="code">使用首頁 Input 參數指定的位置</div>
<div class="k">MANIFEST MODE</div><div>只建立 enabled=false 草稿，不自動核准日期。</div>
</div>
<div id="queue" class="queue"></div>
</div>
</section>

<section id="page-registry" class="page">
<h2>Runtime Registry <span class="en">support tools + modules + libraries</span></h2>
<div class="panel registryPanel">
<div class="registryGrid">
<div class="registryCard"><div class="l">SUPPORT FILES</div><div id="registryFiles" class="v">—</div></div>
<div class="registryCard"><div class="l">POWERSHELL IMPORTS</div><div id="psModuleCount" class="v">—</div></div>
<div class="registryCard"><div class="l">PYTHON PACKAGES</div><div id="pythonPackageCount" class="v">—</div></div>
<div class="registryCard"><div class="l">SNAPSHOT SHA256</div><div id="registrySnapshot" class="v">—</div></div>
<div class="registryCard"><div class="l">SUPPORT LEDGER</div><div id="registryLedger" class="v">—</div></div>
<div class="registryCard"><div class="l">SERVER MODE</div><div id="registryMode" class="v">—</div></div>
</div>
<div class="hint" style="margin-top:12px">
支援性工具採 SHA registry；只 Import 核准 PowerShell modules，不會盲目 dot-source 全部 supportive scripts。SCAN 於執行期實際掃描 Base 下支援檔並列舉 PowerShell modules 與 Python packages；WRITE 產生 SSOT registry JSON 至 Base\SSOT_VPNS。
</div>
<div class="regBar">
<button class="primary" onclick="loadRegistry()">SCAN / REGISTER</button>
<button onclick="writeRegistry()">WRITE SSOT JSON</button>
<span id="regMsg" class="hint" style="margin:0">尚未掃描 —— 按 SCAN 開始註冊。</span>
</div>
<div class="regSection">
<h3>推薦 TOP-10 本機免費函式庫 · MODULE / ENGINE / FUNCTION-LIB / OTHERS</h3>
<table class="regTable" id="regRecommend"><tbody></tbody></table>
</div>
<div class="regSection">
<h3>支援檔 SHA Ledger <span id="regLedgerCount" class="tag">0</span></h3>
<div class="regScroll"><table class="regTable" id="regLedger"><tbody></tbody></table></div>
</div>
<div class="regSection">
<h3>PowerShell Modules <span id="regPsCount" class="tag">0</span></h3>
<div class="regScroll"><table class="regTable" id="regPs"><tbody></tbody></table></div>
</div>
<div class="regSection">
<h3>Python Packages <span id="regPyCount" class="tag">0</span></h3>
<div class="regScroll"><table class="regTable" id="regPy"><tbody></tbody></table></div>
</div>
</div>
</section>

<section id="page-logs" class="page">
<h2>Execution Logs <span class="en">worker events + gate evidence</span></h2>
<div class="panel logPanel">
<div class="actions">
<button onclick="document.getElementById('log').textContent='(顯示已清除，伺服器仍保留完整記錄)'">CLEAR DISPLAY</button>
<button onclick="switchPage('home')">BACK TO HOME</button>
</div>
<div id="log" class="log">VIA VRN Sidebar Workbench ready.</div>
</div>
</section>

<div class="footer">VIA VRN Visual Lock · self-hosted HttpListener · six independent pages · no canonical mutation · disabled drafts only · 理</div>
</div>
</div>
</div>

<script>
var sources = [];

function byId(id){ return document.getElementById(id); }
function setText(id,v){ var n=byId(id); if(n){ n.textContent=v; } }

function switchPage(name){
    var pages=["systems","home","basic","financial","queue","registry","logs"];
    var labels={
        systems:["整合子系統 · VRN / VDF / VAP","Unified subsystem console"],
        home:["首頁 · 輸入與摘要","Home · Input + Summary"],
        basic:["Basic Info","Independent primary page"],
        financial:["Financial Data","Independent primary page"],
        queue:["報告佇列","Investment report intake queue"],
        registry:["Runtime Registry","Tools, modules and library registration"],
        logs:["Execution Logs","Worker events and Gate evidence"]
    };
    for(var i=0;i<pages.length;i++){
        var page=pages[i];
        byId("page-"+page).className="page"+(page===name?" active":"");
        byId("nav-"+page).className=page===name?"active":"";
    }
    setText("pageTitle",labels[name][0]);
    setText("pageSubtitle",labels[name][1]);
    if(name==="basic"){ loadView("basic"); }
    if(name==="financial"){ loadView("financial"); }
    if(name==="registry"){ loadRegistry(); }
    if(name==="systems"){ loadSystems(); }
}
function pillFor(state){ if(state==="READY"||state==="BUILT-IN"){ return "ok"; } if(state==="NOT-FOUND"){ return "warn"; } return "blind"; }
async function loadSystems(){
    var base=byId("base").value;
    try{
        var arr=await api("/api/systems?base="+encodeURIComponent(base));
        var box=byId("sysCards"); if(box){ box.innerHTML=""; }
        var html="<tr><th class='cSmall'>ID</th><th class='cFunc'>SYSTEM</th><th class='cSmall'>STATE</th><th>LAUNCHER</th></tr>";
        for(var i=0;i<arr.length;i++){
            var s=arr[i];
            var btn;
            if(s.kind==="self"){ btn="<button class='primary' style='margin-top:8px' onclick=\"switchPage('home')\">OPEN VRN</button>"; }
            else if(s.available){ btn="<button class='primary' style='margin-top:8px' onclick=\"launchSystem('"+esc(s.id)+"')\">START "+esc(s.id)+"</button>"; }
            else { btn="<button disabled style='margin-top:8px'>NOT FOUND</button>"; }
            if(box){
                var card=document.createElement("div"); card.className="registryCard";
                card.innerHTML="<div class='l'>"+esc(s.id)+" <span class='pill "+pillFor(s.state)+"'>"+esc(s.state)+"</span></div>"+
                    "<div class='v' style='font-size:11px'>"+esc(s.name)+"</div>"+
                    "<div class='hint' style='margin-top:4px'>"+esc(s.desc)+"</div>"+btn;
                box.appendChild(card);
            }
            html+="<tr><td class='cSmall'>"+esc(s.id)+"</td><td class='cFunc'>"+esc(s.name)+"</td><td class='cSmall'>"+esc(s.state)+"</td><td>"+esc(s.launcher)+"</td></tr>";
        }
        var mt=tbodyOf("sysMatrix"); if(mt){ mt.innerHTML=html; }
    }catch(e){}
}
async function launchSystem(id){
    var base=byId("base").value;
    setText("sysLaunchMsg","啟動中…");
    try{
        var d=await api("/api/launch", jsonPost({id:id,base:base}));
        setText("sysLaunchMsg",(d.ok?"✓ ":"✗ ")+d.message);
        loadSystems();
    }catch(e){ setText("sysLaunchMsg","啟動失敗："+e.message); }
}
function esc(s){ return String(s==null?"":s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }
function tbodyOf(id){ var t=byId(id); return t?t.getElementsByTagName("tbody")[0]:null; }
function renderRecommend(rows){
    var t=tbodyOf("regRecommend"); if(!t){ return; }
    var html="<tr><th class='cSec'>SECTION</th><th class='cFunc'>FUNCTION</th><th>PYTHON · TOP-10</th><th>POWERSHELL / .NET</th></tr>";
    for(var i=0;i<rows.length;i++){
        var r=rows[i];
        html+="<tr><td class='cSec'>"+esc(r.section)+"</td><td class='cFunc'>"+esc(r.func)+"</td><td>"+esc(r.py)+"</td><td>"+esc(r.ps)+"</td></tr>";
    }
    t.innerHTML=html;
}
function renderLedger(rows){
    var t=tbodyOf("regLedger"); if(!t){ return; }
    var html="<tr><th class='cFunc'>FILE</th><th class='cSmall'>EXT</th><th>SHA256</th></tr>";
    for(var i=0;i<rows.length;i++){
        var r=rows[i];
        html+="<tr><td class='cFunc'>"+esc(r.name)+"</td><td class='cSmall'>"+esc(r.ext)+"</td><td>"+esc(r.sha)+"</td></tr>";
    }
    if(!rows.length){ html+="<tr><td colspan='3'>Base 下未找到支援檔（.ps1/.psm1/.psd1/.py/.json）。</td></tr>"; }
    t.innerHTML=html;
}
function renderKV(id,rows){
    var t=tbodyOf(id); if(!t){ return; }
    var html="<tr><th class='cFunc'>NAME</th><th>VERSION</th></tr>";
    for(var i=0;i<rows.length;i++){
        var r=rows[i];
        html+="<tr><td class='cFunc'>"+esc(r.name)+"</td><td>"+esc(r.version)+"</td></tr>";
    }
    if(!rows.length){ html+="<tr><td colspan='2'>（無 / 執行期未偵測到）</td></tr>"; }
    t.innerHTML=html;
}
async function loadRegistry(){
    var base=byId("base").value, py=byId("python").value;
    setText("regMsg","掃描並註冊中…");
    try{
        var d=await api("/api/registry?base="+encodeURIComponent(base)+"&python="+encodeURIComponent(py));
        setText("registryFiles", d.supportCount);
        setText("psModuleCount", d.psModuleCount);
        setText("pythonPackageCount", d.pyPackageCount);
        setText("registrySnapshot", d.snapshot ? (d.snapshot.substring(0,18)+"…") : "—");
        setText("registryLedger", d.supportCount+" 筆");
        renderRecommend(d.recommend||[]);
        renderLedger(d.ledger||[]); setText("regLedgerCount", d.supportCount);
        renderKV("regPs", d.psModules||[]); setText("regPsCount", d.psModuleCount);
        renderKV("regPy", d.pyPackages||[]); setText("regPyCount", d.pyPackageCount);
        setText("regMsg","已註冊："+d.supportCount+" 檔 / "+d.psModuleCount+" PS modules / "+d.pyPackageCount+" PY packages");
    }catch(e){ setText("regMsg","掃描失敗："+e.message); }
}
async function writeRegistry(){
    var base=byId("base").value, py=byId("python").value;
    setText("regMsg","寫入 SSOT registry JSON…");
    try{
        var d=await api("/api/registry/write", jsonPost({base:base,python:py}));
        setText("regMsg",(d.ok?"✓ ":"✗ ")+d.message+(d.path?(" → "+d.path):""));
    }catch(e){ setText("regMsg","寫入失敗："+e.message); }
}

async function api(path, opts){
    var r = await fetch(path, opts||{});
    if(!r.ok){ throw new Error("HTTP "+r.status); }
    var ct = r.headers.get("content-type")||"";
    return ct.indexOf("application/json")>=0 ? r.json() : r.text();
}
function jsonPost(body){
    return { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(body) };
}

async function browseField(kind, fieldId){
    try{
        var d = await api("/api/browse", jsonPost({kind:kind}));
        if(d.paths && d.paths.length){ byId(fieldId).value = d.paths[0]; }
    }catch(e){ /* dialog cancelled or error */ }
}
async function addFiles(){
    try{
        var d = await api("/api/browse", jsonPost({kind:"Files"}));
        if(d.paths && d.paths.length){ await queueAdd(d.paths); }
    }catch(e){}
}
async function addFolder(){
    try{
        var d = await api("/api/browse", jsonPost({kind:"Folder"}));
        if(d.paths && d.paths.length){ await queueAdd(d.paths); }
    }catch(e){}
}
async function queueAdd(paths){
    try{ await api("/api/queue/add", jsonPost({paths:paths})); refresh(); }catch(e){}
}
async function clearQueue(){
    try{ await api("/api/queue/clear", jsonPost({})); refresh(); }catch(e){}
}
function renderQueue(list){
    var box = byId("queue"); if(!box){ return; }
    box.innerHTML="";
    var arr = list||[];
    for(var i=0;i<arr.length;i++){
        var d=document.createElement("div"); d.className="queueItem";
        var a=document.createElement("span"); a.textContent=arr[i];
        var b=document.createElement("span"); b.className="pill blind"; b.textContent="DRAFT";
        d.appendChild(a); d.appendChild(b); box.appendChild(d);
    }
    setText("queueCount", arr.length);
}
function collectParams(){
    return {
        base: byId("base").value,
        input: byId("input").value,
        manifest: byId("manifest").value,
        python: byId("python").value,
        timeout: Number(byId("timeout").value)||2400,
        recursive: byId("recursive").checked,
        openHtml: byId("openHtml").checked
    };
}
async function submitRun(){
    byId("run").disabled=true;
    try{ await api("/api/run", jsonPost(collectParams())); }
    catch(e){ byId("run").disabled=false; }
}
async function loadView(which){
    var base = byId("base").value;
    try{
        var d = await api("/api/view?which="+encodeURIComponent(which)+"&base="+encodeURIComponent(base));
        var frame=byId(which+"Frame"), empty=byId(which+"Empty"), pathEl=byId(which+"Path");
        if(d.html){ frame.srcdoc=d.html; frame.style.display="block"; empty.style.display="none"; pathEl.textContent=d.path; }
        else { frame.style.display="none"; empty.style.display="block"; pathEl.textContent=""; }
    }catch(e){}
}
function openView(which){
    var p = byId(which+"Path").textContent; if(p){ openManual(p); }
}
async function openManual(path){
    if(!path){ return; }
    try{ await api("/api/open", jsonPost({path:path})); }catch(e){}
}
function openDataPath(btn){
    var p = btn.getAttribute("data-path"); if(p){ openManual(p); }
}
async function closeWorkbench(){
    try{ await api("/api/shutdown", jsonPost({})); }catch(e){}
    try{ window.open("","_self"); window.close(); }catch(e){}
    document.body.innerHTML="<div style='padding:60px;text-align:center;font-family:monospace'>WORKBENCH 已關閉，可關閉此分頁。</div>";
}
function pillClass(st){
    if(st==="DONE"||st==="READY"){ return "ok"; }
    if(st==="RUNNING"){ return "warn"; }
    return "blind";
}
function applyStatus(s){
    setText("sideState", s.state);
    setText("sideProgress", s.progress+"%");
    setText("sideQueue", s.queueCount);
    setText("sideGate", s.gate);
    setText("sideMode", s.mode);
    setText("summaryState", s.state);
    setText("summaryProgress", s.progress+"%");
    setText("homeQueue", s.queueCount);
    setText("summaryReports", s.reports);
    setText("summaryDrafts", s.drafts);
    setText("summaryRegistry", s.registered);
    setText("summaryGate", s.gate);
    setText("registryMode", s.mode);
    byId("bar").style.width = s.progress+"%";
    byId("state").innerHTML = "<span class='pill "+pillClass(s.state)+"'>"+s.state+"</span>";
    setText("message", s.message);
    setText("gate", s.gate);
    setText("registry", s.registry);
    byId("log").textContent = s.logs || "VIA VRN Sidebar Workbench ready.";
    renderQueue(s.queue);
    var rb=byId("result"), rd=byId("runDir");
    if(s.result){ rb.disabled=false; rb.setAttribute("data-path", s.result); } else { rb.disabled=true; }
    if(s.rundir){ rd.disabled=false; rd.setAttribute("data-path", s.rundir); } else { rd.disabled=true; }
    if(!s.running){ byId("run").disabled=false; } else { byId("run").disabled=true; }
}
async function refresh(){
    try{ var s = await api("/api/status"); applyStatus(s); }catch(e){}
}
function setupDrop(id){
    var z=byId(id); if(!z){ return; }
    z.addEventListener("dragover",function(e){ e.preventDefault(); z.classList.add("active"); });
    z.addEventListener("dragleave",function(){ z.classList.remove("active"); });
    z.addEventListener("drop",function(e){
        e.preventDefault(); z.classList.remove("active");
        var names=[];
        if(e.dataTransfer && e.dataTransfer.files){
            for(var i=0;i<e.dataTransfer.files.length;i++){ names.push(e.dataTransfer.files[i].name); }
        }
        if(names.length){ queueAdd(names); }
    });
}
window.onload=function(){
    switchPage("systems");
    fetch("/api/config").then(function(r){ return r.json(); }).then(function(c){
        byId("base").value=c.base;
        byId("input").value=c.input;
        byId("manifest").value=c.manifest;
        byId("python").value=c.python;
        byId("timeout").value=c.timeout;
        byId("recursive").checked=c.recursive;
        byId("openHtml").checked=c.openHtml;
    }).catch(function(){});
    setupDrop("dropHome");
    setupDrop("dropQueue");
    refresh();
    setInterval(refresh, 1200);
};
</script>
</body>
</html>
'@

# ------------------------------------------------------------------- listener
Add-Log 'VIA · VRN Sidebar Workbench 伺服器初始化中…'
Add-Log ("模式：" + $script:State.Mode + "（設定 -EngineCommand 或編輯腳本頂端以接真實引擎）")

$script:Listener = $null
$started = $false
$boundUrl = ''
for ($try = 0; $try -lt 12 -and -not $started; $try++) {
    $p = $Port + $try
    $prefix = "http://localhost:$p/"
    $listener = [System.Net.HttpListener]::new()
    $listener.Prefixes.Add($prefix)
    try {
        $listener.Start()
        $started         = $true
        $Port            = $p
        $boundUrl        = "http://localhost:$p/"
        $script:Listener = $listener
    }
    catch {
        try { $listener.Close() } catch {}
    }
}

if (-not $started) {
    Write-Host ''
    Write-Host 'def HTTP LISTENER 啟動失敗。' -ForegroundColor Red
    Write-Host ("def 已嘗試 Port {0}..{1}。" -f $Port, ($Port + 11)) -ForegroundColor Yellow
    Write-Host 'def 若為權限問題，請在系統管理員 PowerShell 執行一次：' -ForegroundColor Yellow
    Write-Host ("def   netsh http add urlacl url=http://localhost:{0}/ user={1}" -f $Port, $env:USERNAME) -ForegroundColor Cyan
    return
}

Write-Host ''
Write-Host ('=' * 96) -ForegroundColor DarkCyan
Write-Host 'def VIA · UNIFIED CONSOLE (VRN + VDF + VAP) · v0163' -ForegroundColor Cyan
Write-Host ("def URL   : {0}" -f $boundUrl) -ForegroundColor Green
Write-Host ("def MODE  : {0}" -f $script:State.Mode) -ForegroundColor Yellow
Write-Host 'def GATE  : GREEN_POWERSHELL_AST_PASS (see one-click launcher)' -ForegroundColor Green
Write-Host 'def 停止  : 於此視窗按 Ctrl+C，或在 UI 按 CLOSE WORKBENCH' -ForegroundColor DarkGray
Write-Host ('=' * 96) -ForegroundColor DarkCyan

if (-not $NoBrowser) {
    try { Start-Process $boundUrl } catch { Write-Host ("def 無法自動開啟瀏覽器，請手動開啟 {0}" -f $boundUrl) -ForegroundColor Yellow }
}

try {
    while ($script:Listener.IsListening) {
        $ctx = $null
        try { $ctx = $script:Listener.GetContext() }
        catch { break }
        if ($null -eq $ctx) { continue }
        try {
            Invoke-Route -Context $ctx
        }
        catch {
            try { Send-Response $ctx (Convert-Json @{ error = $_.Exception.Message }) 'application/json; charset=utf-8' 500 } catch {}
        }
    }
}
finally {
    try { $script:Listener.Stop() }  catch {}
    try { $script:Listener.Close() } catch {}
    if ($script:Worker.ps)  { try { $script:Worker.ps.Dispose() }  catch {} }
    if ($script:Worker.rs)  { try { $script:Worker.rs.Dispose() }  catch {} }
    Write-Host ''
    Write-Host 'def VRN Workbench 伺服器已停止。Parent PowerShell remains open.' -ForegroundColor Cyan
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
