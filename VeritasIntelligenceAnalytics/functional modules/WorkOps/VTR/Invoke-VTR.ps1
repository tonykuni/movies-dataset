#Requires -Version 5.1
<#
.SYNOPSIS
    VTR 會議紀錄修復引擎 · 單一進入點（operator workstation）。

.DESCRIPTION
    一個檔案處理全部 VTR 操作：環境檢查、詞庫驗證、引擎測試、manifest 稽核、
    逐字稿修復、待裁決檢視、版本回滾。

    設計約束（皆源自本 repo 踩過的坑）：
      * 不使用 Start-Process。本 repo 的路徑含空白（"functional modules"），
        Start-Process 的 ArgumentList 會在空白處把參數拆開。一律用呼叫運算子
        搭配陣列參數（& $exe @args），由 PowerShell 直接處理引號。
      * 強制 UTF-8。輸出含中文與遮罩符 ⟦⟧，未設定編碼會變成亂碼。
      * 本檔以 UTF-8 **含 BOM** 儲存。Windows PowerShell 5.1 對無 BOM 的檔案
        假設為 ANSI，會把中文字串解析成亂碼 —— 這是 5.1 相容性的硬性要求。
      * 零第三方模組相依。

.PARAMETER Action
    All      （預設）Doctor + Lexicon + Test + Manifest 全套驗證
    Doctor   只檢查環境
    Lexicon  驗證 SSOT 詞庫（-UpdateIndex 可同時重建索引）
    Test     跑引擎測試
    Manifest 稽核 artifact SHA-256（-Update 可重算）
    Restore  對逐字稿跑 Preprocessing Pipeline（-Path 可為檔案或資料夾）
    Inspect  檢視已修復文件與待裁決佇列
    Replay   回滾到指定 rev（-ToRev）

.EXAMPLE
    .\Invoke-VTR.ps1
    全套驗證。CI 或每日檢查用。

.EXAMPLE
    .\Invoke-VTR.ps1 -Action Restore -Path .\input\ -OutDir .\out\
    批次修復整個資料夾的逐字稿。

.EXAMPLE
    .\Invoke-VTR.ps1 -Action Replay -DocId MTG-001 -ToRev 1
    把 MTG-001 回滾到 rev 1。

.NOTES
    退出碼：0 全部通過 · 2 契約/schema 錯誤 · 3 SSOT 或 sentinel 違反
            4 改壞率超標 · 5 manifest 不一致 · 10 環境不符 · 1 其他錯誤
#>
[CmdletBinding()]
param(
    [ValidateSet('All', 'Doctor', 'Lexicon', 'Test', 'Manifest', 'Restore', 'Inspect', 'Replay')]
    [string] $Action = 'All',

    [string] $Path,
    [string] $DocId,
    [string] $OutDir,
    [int]    $ToRev = -1,

    [switch] $UpdateIndex,
    [switch] $Update,
    [switch] $StrictPipeline,
    [switch] $ShowReview,
    [switch] $NoColor
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# --------------------------------------------------------------------------- #
# 全域狀態
# --------------------------------------------------------------------------- #

$script:Root       = $PSScriptRoot
$script:EngineDir  = Join-Path $script:Root 'engine'
$script:PythonExe  = $null
$script:PythonArgs = @()
$script:Results    = New-Object System.Collections.ArrayList
$script:ExitCode   = 0

# --------------------------------------------------------------------------- #
# 輸出
# --------------------------------------------------------------------------- #

function Write-Line {
    param([string] $Text = '', [string] $Colour = 'Gray')
    if ($NoColor) { Write-Host $Text } else { Write-Host $Text -ForegroundColor $Colour }
}

function Write-Head {
    param([string] $Text)
    Write-Line ''
    Write-Line ("── {0} {1}" -f $Text, ('─' * [Math]::Max(0, 62 - $Text.Length))) 'Cyan'
}

function Write-Ok    { param([string] $T) Write-Line ("  [OK]   {0}" -f $T) 'Green' }
function Write-Fail  { param([string] $T) Write-Line ("  [FAIL] {0}" -f $T) 'Red' }
function Write-Warn2 { param([string] $T) Write-Line ("  [WARN] {0}" -f $T) 'Yellow' }
function Write-Info  { param([string] $T) Write-Line ("         {0}" -f $T) 'DarkGray' }

function Add-Result {
    param([string] $Step, [int] $Code, [string] $Detail = '')
    $null = $script:Results.Add([pscustomobject]@{
        Step   = $Step
        Status = if ($Code -eq 0) { 'PASS' } else { "FAIL($Code)" }
        Code   = $Code
        Detail = $Detail
    })
    if ($Code -ne 0 -and $script:ExitCode -eq 0) { $script:ExitCode = $Code }
}

# --------------------------------------------------------------------------- #
# 環境
# --------------------------------------------------------------------------- #

function Initialize-Utf8 {
    <#
        輸出含中文與遮罩符 ⟦⟧（U+27E6/U+27E7）。不設定編碼時，
        Windows 主控台會把它們顯示成亂碼或問號。
    #>
    try {
        [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
        $global:OutputEncoding    = New-Object System.Text.UTF8Encoding($false)
    } catch {
        Write-Warn2 "無法設定主控台編碼：$($_.Exception.Message)"
    }
    # 讓 Python 也用 UTF-8 輸出，不受 Windows 預設 cp950 影響
    $env:PYTHONUTF8      = '1'
    $env:PYTHONIOENCODING = 'utf-8'
}

function Get-IsWindows {
    # $IsWindows 只存在於 PowerShell 6+；5.1 一律是 Windows。
    $v = Get-Variable -Name 'IsWindows' -ErrorAction SilentlyContinue
    if ($null -eq $v) { return $true }
    return [bool] $v.Value
}

function Resolve-Python {
    <#
        依序嘗試 py -3 / python3 / python，取第一個版本 >= 3.9 的。
        回傳 $true 表示找到並已設定 $script:PythonExe / $script:PythonArgs。
    #>
    $candidates = @(
        @{ Exe = 'py';      Args = @('-3') },
        @{ Exe = 'python3'; Args = @() },
        @{ Exe = 'python';  Args = @() }
    )
    foreach ($c in $candidates) {
        $cmd = Get-Command $c.Exe -ErrorAction SilentlyContinue
        if ($null -eq $cmd) { continue }
        try {
            # 探針的 -c 字串**不含雙引號、不含 %**。原本用
            # 'print("%d.%d" % ...)' 在 Windows PowerShell 5.1 的原生參數引號
            # 處理下會被拆壞（5.1 對傳給外部程式、含內嵌雙引號的引數有已知 bug；
            # pwsh 7 的 PSNativeCommandArgumentPassing 已修正）。改用兩個獨立
            # print，各印一個整數，完全避開特殊字元。
            $code  = 'import sys;print(sys.version_info[0]);print(sys.version_info[1])'
            $probe = @($c.Args) + @('-c', $code)
            $out = & $c.Exe @probe 2>$null
            if ($LASTEXITCODE -ne 0) { continue }
            $nums = @($out) | ForEach-Object { ([string]$_).Trim() } |
                    Where-Object { $_ -match '^\d+$' }
            if ($nums.Count -lt 2) { continue }
            $major = [int] $nums[0]
            $minor = [int] $nums[1]
            $ver = "$major.$minor"
            if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 9)) {
                Write-Warn2 "$($c.Exe) 版本為 $ver，需要 3.9 以上，略過"
                continue
            }
            $script:PythonExe  = $c.Exe
            $script:PythonArgs = $c.Args
            $script:PythonVer  = $ver
            return $true
        } catch {
            continue
        }
    }
    return $false
}

function Invoke-Py {
    <#
        在指定工作目錄執行 Python。回傳退出碼。

        刻意不用 Start-Process：本 repo 路徑含空白，ArgumentList 會被空白拆開
        （git log 有兩次修這個 bug 的紀錄）。呼叫運算子 + 陣列不會有這問題。
    #>
    param(
        [Parameter(Mandatory)] [string[]] $Arguments,
        [string] $WorkingDirectory = $script:Root
    )
    $previous = Get-Location
    try {
        Set-Location -LiteralPath $WorkingDirectory
        $full = @($script:PythonArgs) + $Arguments

        # `| Out-Host` 是這裡的關鍵，不是排版選擇。
        # 原生命令的 stdout 預設進入**輸出串流**，會和 `return $code` 一起成為
        # 函式的回傳值 —— 呼叫端拿到的是 Object[]（整包輸出 + 退出碼），而不是 int。
        # 這是 PowerShell 最常見的一類 bug：函式回傳值被輸出污染。
        # Out-Host 讓輸出直接寫到主控台，永遠不進管線。
        & $script:PythonExe @full | Out-Host
        return $LASTEXITCODE
    } finally {
        Set-Location -LiteralPath $previous
    }
}

# --------------------------------------------------------------------------- #
# 動作
# --------------------------------------------------------------------------- #

function Invoke-Doctor {
    Write-Head '環境檢查'

    # $PSVersionTable 是 Hashtable，不能用 PSObject.Properties 探鍵 —— 那樣永遠取不到。
    $edition = if ($PSVersionTable.ContainsKey('PSEdition')) {
        [string] $PSVersionTable['PSEdition']
    } else { 'Desktop' }   # PowerShell 5.1 之前沒有這個鍵
    Write-Info ("PowerShell   {0} ({1})" -f $PSVersionTable.PSVersion, $edition)
    Write-Info ("Windows      {0}" -f (Get-IsWindows))
    Write-Info ("VTR Root     {0}" -f $script:Root)

    if (-not (Resolve-Python)) {
        Write-Fail '找不到 Python 3.9+（已嘗試 py -3 / python3 / python）'
        Write-Info '安裝 Python 3.11+ 後重試；確定性層不需要任何第三方套件。'
        Add-Result 'Doctor' 10 'Python 未找到'
        return 10
    }
    Write-Info ("Python       {0} {1} (v{2})" -f $script:PythonExe,
                ($script:PythonArgs -join ' '), $script:PythonVer)

    if ([int]($script:PythonVer.Split('.')[1]) -lt 11) {
        Write-Warn2 "建議使用 Python 3.11 以上（目前 $($script:PythonVer)）"
    }

    $required = @(
        'engine/vtr_py/__init__.py',
        'engine/tests/test_engine.py',
        'lexicon/tools/VIA_ENG047_ValidateLexicon.py',
        'tools/VIA_ENG048_BuildManifest.py',
        'contracts/vtr-document.schema.json',
        'config/vtr.json'
    )
    $missing = @()
    foreach ($rel in $required) {
        $p = Join-Path $script:Root ($rel -replace '/', [IO.Path]::DirectorySeparatorChar)
        if (-not (Test-Path -LiteralPath $p)) { $missing += $rel }
    }
    if ($missing.Count -gt 0) {
        Write-Fail ("子系統檔案缺失：{0}" -f ($missing -join ', '))
        Add-Result 'Doctor' 10 '檔案缺失'
        return 10
    }

    Write-Ok '環境與子系統檔案齊備'
    Add-Result 'Doctor' 0
    return 0
}

function Invoke-Lexicon {
    Write-Head 'SSOT Lexicon 驗證'
    $args1 = @('lexicon/tools/VIA_ENG047_ValidateLexicon.py')
    if ($UpdateIndex) { $args1 += '--write-index' }
    $code = Invoke-Py -Arguments $args1
    if ($code -eq 0) { Write-Ok '詞庫通過' }
    elseif ($code -eq 2) { Write-Fail '詞庫 schema 錯誤' }
    elseif ($code -eq 3) { Write-Fail '詞庫 SSOT 一致性錯誤（id 重複 / 別名衝突 / 治理違反）' }
    else { Write-Fail "驗證器非預期退出碼 $code" }
    Add-Result 'Lexicon' $code
    return $code
}

function Invoke-EngineTest {
    Write-Head '引擎測試'
    $code = Invoke-Py -Arguments @('-m', 'unittest', 'discover', '-s', 'tests', '-t', '.') `
                      -WorkingDirectory $script:EngineDir
    if ($code -eq 0) { Write-Ok '全部測試通過' } else { Write-Fail "測試失敗（退出碼 $code）" }
    Add-Result 'Test' $code
    return $code
}

function Invoke-ManifestCheck {
    Write-Head 'Manifest 稽核'

    $manifestPath = Join-Path $script:Root 'VTR_Subsystem_Manifest.json'
    if (-not (Test-Path -LiteralPath $manifestPath)) {
        Write-Fail 'VTR_Subsystem_Manifest.json 不存在'
        Add-Result 'Manifest' 5 '檔案不存在'
        return 5
    }

    # 稽核交給 VIA_ENG048_BuildManifest.py（單一權威）。它以「正規化行尾後的內容」計算
    # SHA-256，因此在 Windows(CRLF) 與 Linux(LF) 上結果一致。
    #
    # 這裡刻意**不**用純 PowerShell 的 Get-FileHash 逐檔比對：Get-FileHash 雜湊
    # 原始位元組，會把 Git for Windows 在 checkout 時產生的 CRLF 當成不同內容，
    # 在 Windows 上對每一個文字檔誤報「內容已變更」。維護兩套必須逐位元組相符
    # 的雜湊實作本身也是缺陷來源，故收斂為一套。
    # NEW / CHANGED / REMOVED 明細由 VIA_ENG048_BuildManifest.py 印到 stderr。
    $manifestArgs = @('tools/VIA_ENG048_BuildManifest.py', '--quiet')
    if ($Update) { $manifestArgs = @('tools/VIA_ENG048_BuildManifest.py', '--write') }

    $code = Invoke-Py -Arguments $manifestArgs

    if ($code -eq 0) {
        if ($Update) { Write-Ok 'manifest 已重算並寫回' }
        else { Write-Ok 'artifact 內容雜湊全部相符' }
    } elseif ($code -eq 5) {
        Write-Fail 'manifest 與實際檔案不一致'
        Write-Info '加上 -Update 可重算（重算後需重新 commit）'
    } else {
        Write-Fail "build_manifest 非預期退出碼 $code"
    }
    Add-Result 'Manifest' $code
    return $code
}

function Get-TranscriptFiles {
    param([string] $InputPath)
    if (-not (Test-Path -LiteralPath $InputPath)) {
        throw "找不到路徑：$InputPath"
    }
    $item = Get-Item -LiteralPath $InputPath
    if ($item.PSIsContainer) {
        return @(Get-ChildItem -LiteralPath $InputPath -File |
                 Where-Object { $_.Extension -in @('.txt', '.md', '.log') } |
                 Sort-Object Name)
    }
    return @($item)
}

function Invoke-Restore {
    Write-Head '逐字稿修復（Preprocessing Pipeline）'

    if ([string]::IsNullOrWhiteSpace($Path)) {
        Write-Fail '需要 -Path（逐字稿檔案或資料夾）'
        Write-Info '想先看範例：Run-VTR.cmd -Action Restore -Path .\samples\'
        Add-Result 'Restore' 1 '缺少 -Path'
        return 1
    }

    if (-not (Test-Path -LiteralPath $Path)) {
        Write-Fail "找不到這個路徑：$Path"
        $samples = Join-Path $script:Root 'samples'
        if (Test-Path -LiteralPath $samples) {
            Write-Info '想先看內建範例跑起來，執行：'
            Write-Info '  Run-VTR.cmd -Action Restore -Path .\samples\'
        } else {
            Write-Info '請確認資料夾存在，或先自己建一個資料夾、把 .txt 逐字稿放進去。'
        }
        Add-Result 'Restore' 1 '路徑不存在'
        return 1
    }

    # @() 強制陣列：函式 return 會把單元素陣列拆成純量，呼叫端不包 @() 就會
    # 在只有一個逐字稿時，讓後面的 .Count 爆「property 'Count' cannot be found」。
    $files = @(Get-TranscriptFiles -InputPath $Path)
    if ($files.Count -eq 0) {
        Write-Warn2 "$Path 底下沒有 .txt / .md / .log 檔案"
        Add-Result 'Restore' 0 '無輸入'
        return 0
    }

    $baseOut = if ([string]::IsNullOrWhiteSpace($OutDir)) {
        Join-Path $script:Root 'output'
    } else { $OutDir }

    $worst = 0
    foreach ($f in $files) {
        $id = if ($files.Count -eq 1 -and -not [string]::IsNullOrWhiteSpace($DocId)) {
            $DocId
        } else {
            $f.BaseName
        }
        $target = Join-Path $baseOut $id
        Write-Line ("  ▸ {0}  →  {1}" -f $f.Name, $target) 'White'

        $restoreArgs = @('-m', 'vtr_py.cli', 'restore', $f.FullName,
                         '--doc-id', $id, '--out', $target)
        if ($StrictPipeline) { $restoreArgs += '--strict' }
        $cfg = Join-Path $script:Root 'config/vtr.json'
        if (Test-Path -LiteralPath $cfg) { $restoreArgs += @('--config', $cfg) }

        $code = Invoke-Py -Arguments $restoreArgs -WorkingDirectory $script:EngineDir
        if ($code -ne 0 -and $worst -eq 0) { $worst = $code }
        if ($code -eq 0) { Write-Ok $id }
        elseif ($code -eq 3) { Write-Fail "$id —— sentinel 完整性違反（有 Stage 被回退）" }
        else { Write-Fail "$id —— 退出碼 $code" }
    }

    Add-Result 'Restore' $worst ("{0} 份逐字稿" -f $files.Count)
    return $worst
}

function Resolve-DocDir {
    if (-not [string]::IsNullOrWhiteSpace($Path)) { return $Path }
    $baseOut = if ([string]::IsNullOrWhiteSpace($OutDir)) {
        Join-Path $script:Root 'output'
    } else { $OutDir }
    if ([string]::IsNullOrWhiteSpace($DocId)) { return $null }
    return (Join-Path $baseOut $DocId)
}

function Invoke-Inspect {
    Write-Head '文件檢視'
    $dir = Resolve-DocDir
    if ($null -eq $dir) {
        Write-Fail '需要 -DocId（或用 -Path 直接指定輸出資料夾）'
        Add-Result 'Inspect' 1 '缺少 -DocId'
        return 1
    }
    $inspectArgs = @('-m', 'vtr_py.cli', 'inspect', $dir)
    if ($ShowReview) { $inspectArgs += '--review' }
    $code = Invoke-Py -Arguments $inspectArgs -WorkingDirectory $script:EngineDir
    Add-Result 'Inspect' $code
    return $code
}

function Invoke-Replay {
    Write-Head '版本回滾'
    $dir = Resolve-DocDir
    if ($null -eq $dir) {
        Write-Fail '需要 -DocId（或用 -Path 直接指定輸出資料夾）'
        Add-Result 'Replay' 1 '缺少 -DocId'
        return 1
    }
    if ($ToRev -lt 0) {
        Write-Fail '需要 -ToRev（>= 0）'
        Add-Result 'Replay' 1 '缺少 -ToRev'
        return 1
    }
    $code = Invoke-Py -Arguments @('-m', 'vtr_py.cli', 'replay', $dir,
                                   '--to-rev', "$ToRev") `
                      -WorkingDirectory $script:EngineDir
    if ($code -eq 0) { Write-Ok "已回滾到 rev $ToRev" }
    Add-Result 'Replay' $code
    return $code
}

# --------------------------------------------------------------------------- #
# 主流程
# --------------------------------------------------------------------------- #

Initialize-Utf8

Write-Line ''
Write-Line '  VTR · DG-IN Meeting Transcript Restoration Engine' 'White'
Write-Line '  中英文會議紀錄修復引擎 · 單一進入點' 'DarkGray'

try {
    # Doctor 之外的動作都需要先解析 Python
    if ($Action -ne 'Doctor') {
        if (-not (Resolve-Python)) {
            Invoke-Doctor | Out-Null
            throw '環境不符，無法繼續'
        }
    }

    switch ($Action) {
        'Doctor'   { Invoke-Doctor        | Out-Null }
        'Lexicon'  { Invoke-Lexicon       | Out-Null }
        'Test'     { Invoke-EngineTest    | Out-Null }
        'Manifest' { Invoke-ManifestCheck | Out-Null }
        'Restore'  { Invoke-Restore       | Out-Null }
        'Inspect'  { Invoke-Inspect       | Out-Null }
        'Replay'   { Invoke-Replay        | Out-Null }
        'All' {
            if ((Invoke-Doctor) -eq 0) {
                Invoke-Lexicon       | Out-Null
                Invoke-EngineTest    | Out-Null
                Invoke-ManifestCheck | Out-Null
            }
        }
    }
} catch {
    Write-Line ''
    Write-Fail $_.Exception.Message
    if ($script:ExitCode -eq 0) { $script:ExitCode = 1 }
}

# --------------------------------------------------------------------------- #
# 摘要
# --------------------------------------------------------------------------- #

if ($script:Results.Count -gt 0) {
    Write-Head '摘要'
    foreach ($r in $script:Results) {
        $colour = if ($r.Code -eq 0) { 'Green' } else { 'Red' }
        $detail = if ([string]::IsNullOrWhiteSpace($r.Detail)) { '' } else { "  $($r.Detail)" }
        Write-Line ("  {0,-10} {1,-10}{2}" -f $r.Step, $r.Status, $detail) $colour
    }
}

Write-Line ''
if ($script:ExitCode -eq 0) {
    Write-Line '  全部通過。' 'Green'
} else {
    Write-Line ("  未通過（退出碼 {0}）。" -f $script:ExitCode) 'Red'
    Write-Info '2=契約/schema · 3=SSOT或sentinel · 4=改壞率 · 5=manifest · 10=環境'
}
Write-Line ''

exit $script:ExitCode
