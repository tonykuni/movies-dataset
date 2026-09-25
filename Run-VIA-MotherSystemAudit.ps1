#Requires -Version 7.0
<#
  VIA 母系統唯讀盤點啟動器  VIA-SYS-ENG-006 v0200
  一貼可用。全程唯讀母系統，輸出一律落在母系統之外。

  把 VIA_MotherSystemAudit.py 與 VIA_AutoNumberSSOT.py 放在同一個資料夾，
  預設 C:\VeritasIntelligenceAnalytics\CGE\engines\ ，然後貼上這支腳本。

  LL 慣例：param first、無別名、無 Read-Host、無 exit、UTF8 no-BOM、
           子行程不重導向輸出（LL#26 免假死）、整段包在 &{ } 內（LL#25 貼上安全）
#>

& {
    param(
        [string] $MotherRoot = 'C:\Users\tonyk\Downloads\movies-dataset\VeritasIntelligenceAnalytics',
        [string] $EngineDir  = 'C:\VeritasIntelligenceAnalytics\CGE\engines',
        [string] $OutDir     = 'C:\VeritasIntelligenceAnalytics\CGE\_mother_audit',
        [int]    $MaxKeys    = 400
    )

    $ErrorActionPreference = 'Stop'
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8

    function Write-Line {
        param([string] $Text, [string] $Colour = 'Gray')
        Write-Host $Text -ForegroundColor $Colour
    }

    Write-Line '==================================================================' 'Cyan'
    Write-Line ' VIA 母系統唯讀盤點  VIA-SYS-ENG-006 v0200' 'Cyan'
    Write-Line '==================================================================' 'Cyan'

    $auditPath  = Join-Path $EngineDir 'VIA_MotherSystemAudit.py'
    $numberPath = Join-Path $EngineDir 'VIA_AutoNumberSSOT.py'

    # -- 前置檢查：母系統存在，引擎齊全 ---------------------------------
    if (-not (Test-Path -LiteralPath $MotherRoot)) {
        Write-Line ("找不到母系統：{0}" -f $MotherRoot) 'Red'
        return
    }
    $missing = @()
    foreach ($needed in @($auditPath, $numberPath)) {
        if (-not (Test-Path -LiteralPath $needed)) { $missing += $needed }
    }
    if ($missing.Count -gt 0) {
        Write-Line '引擎檔案不齊，請先放到 EngineDir：' 'Red'
        foreach ($item in $missing) { Write-Line ("  缺 {0}" -f $item) 'Red' }
        Write-Line ("EngineDir 目前是：{0}" -f $EngineDir) 'DarkGray'
        return
    }

    # -- 唯讀護欄：輸出目錄絕不可落在母系統之內 -------------------------
    $rootFull = [System.IO.Path]::GetFullPath($MotherRoot).TrimEnd('\') + '\'
    $outFull  = [System.IO.Path]::GetFullPath($OutDir).TrimEnd('\') + '\'
    if ($outFull.StartsWith($rootFull, [System.StringComparison]::OrdinalIgnoreCase)) {
        Write-Line '輸出目錄位於母系統之內，會破壞唯讀保證。已中止。' 'Red'
        Write-Line ("  root {0}" -f $rootFull) 'DarkGray'
        Write-Line ("  out  {0}" -f $outFull)  'DarkGray'
        return
    }
    if (-not (Test-Path -LiteralPath $OutDir)) {
        New-Item -ItemType Directory -Path $OutDir -Force | Out-Null
    }

    # -- 找 Python ------------------------------------------------------
    $pythonExe = $null
    $candidates = @(
        (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python313\python.exe'),
        'C:\VeritasIntelligenceAnalytics\venv\via_core\Scripts\python.exe'
    )
    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) { $pythonExe = $candidate; break }
    }
    if ($null -eq $pythonExe) {
        $found = Get-Command -Name 'python' -ErrorAction SilentlyContinue
        if ($null -ne $found) { $pythonExe = $found.Source }
    }
    if ($null -eq $pythonExe) {
        $found = Get-Command -Name 'py' -ErrorAction SilentlyContinue
        if ($null -ne $found) { $pythonExe = $found.Source }
    }
    if ($null -eq $pythonExe) {
        Write-Line '找不到 Python 直譯器。' 'Red'
        return
    }
    Write-Line ("Python  {0}" -f $pythonExe) 'DarkGray'
    Write-Line ("母系統  {0}" -f $MotherRoot) 'DarkGray'
    Write-Line ("輸出    {0}" -f $OutDir) 'DarkGray'

    # -- 前導語法檢查：兩支引擎先過 ast.parse，免得跑到一半才炸 --------
    Write-Line ''
    Write-Line '[1/3] 引擎語法前導檢查' 'Cyan'
    $checkCode = 'import ast,sys' + "`n" +
                 'for p in sys.argv[1:]:' + "`n" +
                 '    ast.parse(open(p, encoding="utf-8").read())' + "`n" +
                 'print("engines parse clean")'
    $checkInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $checkInfo.FileName  = $pythonExe
    $checkInfo.UseShellExecute = $false
    $checkInfo.RedirectStandardOutput = $false
    $checkInfo.RedirectStandardError  = $false
    [void]$checkInfo.ArgumentList.Add('-c')
    [void]$checkInfo.ArgumentList.Add($checkCode)
    [void]$checkInfo.ArgumentList.Add($auditPath)
    [void]$checkInfo.ArgumentList.Add($numberPath)
    $checkProc = [System.Diagnostics.Process]::Start($checkInfo)
    $checkProc.WaitForExit()
    if ($checkProc.ExitCode -ne 0) {
        Write-Line '引擎語法檢查未通過，已中止（未觸碰母系統）。' 'Red'
        return
    }

    # -- 自動編號模組自我測試 -------------------------------------------
    Write-Line ''
    Write-Line '[2/3] 自動編號 SSOT 自我測試' 'Cyan'
    $selfInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $selfInfo.FileName = $pythonExe
    $selfInfo.UseShellExecute = $false
    $selfInfo.RedirectStandardOutput = $false
    $selfInfo.RedirectStandardError  = $false
    [void]$selfInfo.ArgumentList.Add($numberPath)
    [void]$selfInfo.ArgumentList.Add('--selftest')
    $selfProc = [System.Diagnostics.Process]::Start($selfInfo)
    $selfProc.WaitForExit()
    if ($selfProc.ExitCode -ne 0) {
        Write-Line '自動編號模組自我測試失敗，已中止。' 'Red'
        return
    }

    # -- 主掃描：不重導向輸出，讓進度即時串流（LL#26） ------------------
    Write-Line ''
    Write-Line '[3/3] 母系統唯讀掃描' 'Cyan'
    $runInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $runInfo.FileName = $pythonExe
    $runInfo.UseShellExecute = $false
    $runInfo.RedirectStandardOutput = $false
    $runInfo.RedirectStandardError  = $false
    $runInfo.WorkingDirectory = $EngineDir
    [void]$runInfo.ArgumentList.Add($auditPath)
    [void]$runInfo.ArgumentList.Add('--root')
    [void]$runInfo.ArgumentList.Add($MotherRoot)
    [void]$runInfo.ArgumentList.Add('--out')
    [void]$runInfo.ArgumentList.Add($OutDir)
    [void]$runInfo.ArgumentList.Add('--max-keys')
    [void]$runInfo.ArgumentList.Add([string]$MaxKeys)
    [void]$runInfo.ArgumentList.Add('--no-open')
    $runProc = [System.Diagnostics.Process]::Start($runInfo)
    $runProc.WaitForExit()
    $verdict = $runProc.ExitCode

    # -- 開報告 ---------------------------------------------------------
    $report = Get-ChildItem -LiteralPath $OutDir -Filter 'VIA_MotherSystemAudit_*.html' |
              Sort-Object -Property @{ e = 'LastWriteTime'; desc = $true } |
              Select-Object -First 1
    Write-Line ''
    if ($null -ne $report) {
        Write-Line ("報告 {0}" -f $report.FullName) 'Green'
        Start-Process -FilePath $report.FullName
    } else {
        Write-Line '未產生報告，請看上方訊息。' 'Yellow'
    }

    if ($verdict -eq 0) {
        Write-Line '閘門全過。' 'Green'
    } else {
        Write-Line '有閘門未過 —— 報告最上方那張表列出是哪幾道。' 'Yellow'
    }
    Write-Line '母系統唯讀，本次執行未寫入母系統任何檔案。' 'DarkGray'
}
