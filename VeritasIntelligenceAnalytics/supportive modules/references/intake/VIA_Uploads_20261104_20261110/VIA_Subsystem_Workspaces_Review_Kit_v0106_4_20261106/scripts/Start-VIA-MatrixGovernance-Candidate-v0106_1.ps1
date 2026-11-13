#requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter()]
    [string]$DownloadRoot = 'C:\Users\tonyk\Downloads',

    [Parameter()]
    [string]$OwnerRoot = 'C:\Users\tonyk\OneDrive\Documents\VeritasIntelligenceAnalytics',

    [Parameter()]
    [switch]$LaunchUI
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Script:CommandRecords = [System.Collections.Generic.List[object]]::new()
$Script:Mutex = $null
$Script:MutexHeld = $false
$Script:Candidate = $null
$Script:ReceiptPath = $null
$Script:LogPath = $null
$Script:ReceiptWritten = $false
$Script:RunStatus = 'NOT_STARTED'
$Script:FailureMessage = $null
$Script:VerifiedSources = @()
$Script:CopiedSources = @()
$Script:ProbeInfo = $null
$Script:PythonLauncher = ''
$Script:PythonExecutable = ''

$SourceSet = @(
    [ordered]@{
        label = 'engine_source'
        name = 'VIA_MatrixGovernance_AllInOne_v0100.py'
        expected_sha256 = 'bb8d5911a0e15765b9a4e0ad9d01a6104a78a044878db71b509b326f1f80b7b0'
    },
    [ordered]@{
        label = 'qa_html'
        name = 'VIA_MatrixGovernance_QA_v0100.html'
        expected_sha256 = '5d6ff4c59ca2dea122f86839e396d6abca22cfdb9ce8c63c126faf8ba7e7ac8b'
    },
    [ordered]@{
        label = 'readme'
        name = 'VIA_MatrixGovernance_README_v0100.md'
        expected_sha256 = 'f1d25131e9b11718e1a453f054c272baf27e37c9cb71894a2089b97e6e2b6338'
    }
)

function Get-Sha256Lower {
    param([Parameter(Mandatory = $true)][string]$LiteralPath)
    return (Get-FileHash -LiteralPath $LiteralPath -Algorithm SHA256 -ErrorAction Stop).Hash.ToLowerInvariant()
}

function Get-ByteSha256Lower {
    param([Parameter(Mandatory = $true)][byte[]]$Bytes)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        return ([System.BitConverter]::ToString($sha.ComputeHash($Bytes))).Replace('-', '').ToLowerInvariant()
    }
    finally {
        $sha.Dispose()
    }
}

function Get-TextSha256Lower {
    param([Parameter(Mandatory = $true)][string]$Text)
    $utf8 = [System.Text.UTF8Encoding]::new($false)
    return Get-ByteSha256Lower -Bytes $utf8.GetBytes($Text)
}

function Assert-WindowsHost {
    if ($env:OS -ne 'Windows_NT') {
        throw 'STOP: this launcher is Windows-only; no candidate work was executed on this host.'
    }
}

function Assert-NoTraversal {
    param([Parameter(Mandatory = $true)][string]$PathText)
    if ($PathText -match '(^|[\\/])\.\.?([\\/]|$)') {
        throw "STOP: path traversal segment is not accepted: $PathText"
    }
    if ($PathText -match '^[A-Za-z]:[^\\/]') {
        throw "STOP: drive-relative path is not accepted: $PathText"
    }
}

function Get-ExistingDirectoryNoReparse {
    param([Parameter(Mandatory = $true)][string]$PathText)
    Assert-NoTraversal -PathText $PathText
    if (-not [System.IO.Path]::IsPathRooted($PathText)) {
        throw "STOP: absolute directory path required: $PathText"
    }
    $full = [System.IO.Path]::GetFullPath($PathText)
    $item = Get-Item -LiteralPath $full -ErrorAction Stop
    if (-not ($item -is [System.IO.DirectoryInfo])) {
        throw "STOP: directory required: $full"
    }
    $current = $item
    while ($null -ne $current) {
        if (($current.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "STOP: reparse-point directory is not accepted: $($current.FullName)"
        }
        $parent = $current.Parent
        if ($null -eq $parent -or $parent.FullName -eq $current.FullName) {
            break
        }
        $current = $parent
    }
    return $item.FullName
}

function Get-ExistingFileNoReparse {
    param([Parameter(Mandatory = $true)][string]$PathText)
    Assert-NoTraversal -PathText $PathText
    if (-not [System.IO.Path]::IsPathRooted($PathText)) {
        throw "STOP: absolute file path required: $PathText"
    }
    $full = [System.IO.Path]::GetFullPath($PathText)
    $item = Get-Item -LiteralPath $full -ErrorAction Stop
    if (-not ($item -is [System.IO.FileInfo])) {
        throw "STOP: file required: $full"
    }
    if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "STOP: reparse-point source file is not accepted: $full"
    }
    [void](Get-ExistingDirectoryNoReparse -PathText $item.Directory.FullName)
    return $item.FullName
}

function Get-SafeChildPath {
    param(
        [Parameter(Mandatory = $true)][string]$ExistingBase,
        [Parameter(Mandatory = $true)][string]$ChildPath
    )
    Assert-NoTraversal -PathText $ChildPath
    $base = [System.IO.Path]::GetFullPath($ExistingBase).TrimEnd('\')
    $full = [System.IO.Path]::GetFullPath($ChildPath)
    $prefix = $base + '\'
    if (-not $full.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "STOP: path is outside the existing owner root: $full"
    }
    if ($full.Equals($base, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw 'STOP: child path must not equal owner root.'
    }
    return $full
}

function Write-LogLine {
    param([Parameter(Mandatory = $true)][string]$Message)
    $line = '{0} {1}' -f ([DateTime]::UtcNow.ToString('o')), $Message
    if ($null -ne $Script:LogPath) {
        Add-Content -LiteralPath $Script:LogPath -Value $line -Encoding UTF8
    }
}

function Write-CreateOnceText {
    param(
        [Parameter(Mandatory = $true)][string]$LiteralPath,
        [Parameter(Mandatory = $true)][string]$Content
    )
    if (Test-Path -LiteralPath $LiteralPath) {
        throw "STOP: refusing to overwrite existing file: $LiteralPath"
    }
    $utf8 = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllText($LiteralPath, $Content, $utf8)
}

function Write-CreateOnceJson {
    param(
        [Parameter(Mandatory = $true)][string]$LiteralPath,
        [Parameter(Mandatory = $true)]$Value
    )
    $json = $Value | ConvertTo-Json -Depth 20
    Write-CreateOnceText -LiteralPath $LiteralPath -Content ($json + [Environment]::NewLine)
}

function Quote-WindowsProcessArgument {
    param([AllowNull()][string]$Value)
    if ($null -eq $Value) {
        return '""'
    }
    $builder = [System.Text.StringBuilder]::new()
    [void]$builder.Append([char]34)
    $slashes = 0
    foreach ($character in $Value.ToCharArray()) {
        $code = [int][char]$character
        if ($code -eq 92) {
            $slashes++
            continue
        }
        if ($code -eq 34) {
            for ($i = 0; $i -lt (2 * $slashes + 1); $i++) {
                [void]$builder.Append([char]92)
            }
            [void]$builder.Append([char]34)
            $slashes = 0
            continue
        }
        for ($i = 0; $i -lt $slashes; $i++) {
            [void]$builder.Append([char]92)
        }
        $slashes = 0
        [void]$builder.Append($character)
    }
    for ($i = 0; $i -lt (2 * $slashes); $i++) {
        [void]$builder.Append([char]92)
    }
    [void]$builder.Append([char]34)
    return $builder.ToString()
}

function Invoke-CapturedProcess {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [Parameter(Mandatory = $true)][string]$Name
    )
    $psi = [System.Diagnostics.ProcessStartInfo]::new()
    $psi.FileName = $FilePath
    $psi.Arguments = (($Arguments | ForEach-Object { Quote-WindowsProcessArgument -Value $_ }) -join ' ')
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $strictUtf8 = [System.Text.UTF8Encoding]::new($false, $true)
    $psi.StandardOutputEncoding = $strictUtf8
    $psi.StandardErrorEncoding = $strictUtf8

    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = $psi
    $startedAt = [DateTime]::UtcNow.ToString('o')
    $stdout = ''
    $stderr = ''
    $exitCode = $null
    try {
        if (-not $process.Start()) {
            throw "STOP: could not start child command: $Name"
        }
        $stdoutTask = $process.StandardOutput.ReadToEndAsync()
        $stderrTask = $process.StandardError.ReadToEndAsync()
        $process.WaitForExit()
        $stdout = $stdoutTask.Result
        $stderr = $stderrTask.Result
        $exitCode = [int]$process.ExitCode
    }
    finally {
        $process.Dispose()
    }

    $record = [ordered]@{
        name = $Name
        executable = $FilePath
        arguments = @($Arguments)
        started_at_utc = $startedAt
        finished_at_utc = [DateTime]::UtcNow.ToString('o')
        exit_code = $exitCode
        stdout_utf8 = $true
        stdout_bytes = ([System.Text.UTF8Encoding]::new($false)).GetByteCount($stdout)
        stdout_sha256 = Get-TextSha256Lower -Text $stdout
        stderr_bytes = ([System.Text.UTF8Encoding]::new($false)).GetByteCount($stderr)
        stderr_sha256 = Get-TextSha256Lower -Text $stderr
        stderr_exported = $false
    }
    [void]$Script:CommandRecords.Add([pscustomobject]$record)
    Write-LogLine -Message ("command={0}; exit_code={1}; stdout_utf8=true; stderr_exported=false" -f $Name, $exitCode)
    return [pscustomobject]@{
        Name = $Name
        ExitCode = $exitCode
        Stdout = $stdout
        Stderr = $stderr
        Record = [pscustomobject]$record
    }
}

function ConvertFrom-CapturedJson {
    param(
        [Parameter(Mandatory = $true)]$Result,
        [Parameter(Mandatory = $true)][string]$Name
    )
    if ([string]::IsNullOrWhiteSpace($Result.Stdout)) {
        throw "STOP: $Name returned empty stdout; expected UTF-8 JSON."
    }
    try {
        return ($Result.Stdout | ConvertFrom-Json -ErrorAction Stop)
    }
    catch {
        throw "STOP: $Name stdout was not a single valid JSON document: $($_.Exception.Message)"
    }
}

function Assert-ExactBoolean {
    param(
        [Parameter(Mandatory = $true)]$Object,
        [Parameter(Mandatory = $true)][string]$PropertyName,
        [Parameter(Mandatory = $true)][bool]$Expected
    )
    $property = $Object.PSObject.Properties[$PropertyName]
    if ($null -eq $property) {
        throw "STOP: JSON boolean property missing: $PropertyName"
    }
    $value = $property.Value
    if (-not ($value -is [bool]) -or $value -ne $Expected) {
        throw "STOP: JSON boolean $PropertyName was not exact Boolean $Expected."
    }
}

function Get-UserMutexName {
    $sid = [System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value
    $material = 'VIA-MatrixGovernance-v0106.1|user-sid=' + $sid + '|source-set=engine+qa+readme'
    $hash = Get-TextSha256Lower -Text $material
    return 'Local\VIA-MatrixGovernance-v0106.1-' + $hash.Substring(0, 32)
}

function Acquire-UserMutex {
    $name = Get-UserMutexName
    $createdNew = $false
    $Script:Mutex = [System.Threading.Mutex]::new($false, $name, [ref]$createdNew)
    try {
        $Script:MutexHeld = $Script:Mutex.WaitOne(0)
    }
    catch [System.Threading.AbandonedMutexException] {
        $Script:MutexHeld = $true
        Write-LogLine -Message 'mutex_abandoned=true; ownership recovered for this process'
    }
    if (-not $Script:MutexHeld) {
        throw 'STOP: another v0106.1 bootstrap for this Windows user and source set is already running; no second output root was touched.'
    }
    Write-LogLine -Message 'mutex_scope=Local_per_user_sid; machine-wide_Global_mutex=false; acquired=true'
}

function Release-UserMutex {
    if ($null -ne $Script:Mutex) {
        try {
            if ($Script:MutexHeld) {
                $Script:Mutex.ReleaseMutex()
            }
        }
        finally {
            $Script:MutexHeld = $false
            $Script:Mutex.Dispose()
            $Script:Mutex = $null
        }
    }
}

function New-CandidateDirectory {
    param([Parameter(Mandatory = $true)][string]$ValidatedOwnerRoot)
    $parentPath = Get-SafeChildPath -ExistingBase $ValidatedOwnerRoot -ChildPath (Join-Path $ValidatedOwnerRoot 'VIA_Review_Candidates')
    if (Test-Path -LiteralPath $parentPath) {
        [void](Get-ExistingDirectoryNoReparse -PathText $parentPath)
    }
    else {
        New-Item -ItemType Directory -LiteralPath $parentPath -ErrorAction Stop | Out-Null
        [void](Get-ExistingDirectoryNoReparse -PathText $parentPath)
    }

    $guid = [Guid]::NewGuid().ToString('N')
    $candidatePath = Get-SafeChildPath -ExistingBase $ValidatedOwnerRoot -ChildPath (Join-Path $parentPath ('MatrixGovernance_v0106.1_' + $guid))
    if (Test-Path -LiteralPath $candidatePath) {
        throw "STOP: generated candidate path unexpectedly exists: $candidatePath"
    }
    New-Item -ItemType Directory -LiteralPath $candidatePath -ErrorAction Stop | Out-Null
    return Get-ExistingDirectoryNoReparse -PathText $candidatePath
}

function New-DependencyReviewPlan {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$PythonExecutable,
        [Parameter(Mandatory = $true)][string]$CandidatePath
    )
    $content = @"
# Matrix Governance v0106.1 dependency review plan

Status: BLOCKED_BEFORE_ENGINE_EXECUTION
Scope: this candidate only; no installation, upgrade, admin action, or network action was attempted.

The existing `py.exe -3` interpreter resolved to:

`$PythonExecutable`

The required `pyarrow` module was not present in that interpreter. The launcher therefore did not run `--doctor`, `--self-test`, or the UI, and it did not execute any package-manager command. An owner must review the existing VCGC EnvManager / approved dependency process and make the dependency available in the already-approved environment before rerunning this launcher.

`psutil` is optional. If it is absent in a later run, the engine may record telemetry as unmeasured; that is not a reason to install it here.

Candidate path: `$CandidatePath`
"@
    Write-CreateOnceText -LiteralPath $Path -Content $content
}

function Write-ReceiptIfAbsent {
    param(
        [Parameter(Mandatory = $true)][string]$ValidatedDownloadRoot,
        [Parameter(Mandatory = $true)][string]$ValidatedOwnerRoot,
        [Parameter(Mandatory = $true)]$VerifiedSources,
        [Parameter(Mandatory = $true)]$CopiedSources,
        [Parameter(Mandatory = $true)]$ProbeInfo,
        [Parameter(Mandatory = $true)][string]$PythonLauncher,
        [Parameter(Mandatory = $true)][string]$PythonExecutable,
        [Parameter(Mandatory = $true)][string]$ScopeStatus,
        [Parameter()][string]$Reason,
        [Parameter()][object]$DoctorSummary,
        [Parameter()][object]$SelfTestSummary,
        [Parameter()][object]$UiSummary
    )
    if ($null -eq $Script:ReceiptPath -or $Script:ReceiptWritten) {
        return
    }
    $psutilAvailable = $false
    if ($null -ne $ProbeInfo -and $null -ne $ProbeInfo.psutil) {
        $psutilAvailable = [bool]$ProbeInfo.psutil
    }
    $receipt = [ordered]@{
        schema = 'VIA.MatrixGovernance.CandidateBootstrap.v0106.1'
        created_at_utc = [DateTime]::UtcNow.ToString('o')
        status = $ScopeStatus
        reason = $Reason
        candidate_path = $Script:Candidate
        download_root = $ValidatedDownloadRoot
        owner_root = $ValidatedOwnerRoot
        source_set = @($VerifiedSources)
        copied_source_set = @($CopiedSources)
        original_source_preserved = $true
        no_overwrite_policy = $true
        python = [ordered]@{
            launcher = $PythonLauncher
            executable = $PythonExecutable
            required_major = 3
            required_minor = 11
            pyarrow_present = if ($null -ne $ProbeInfo) { [bool]$ProbeInfo.pyarrow } else { $false }
            psutil_present = $psutilAvailable
            telemetry = if ($psutilAvailable) { 'psutil_available' } else { 'psutil_unmeasured_optional_missing' }
        }
        commands = @($Script:CommandRecords)
        doctor = $DoctorSummary
        self_test = $SelfTestSummary
        launch_ui_requested = [bool]$LaunchUI
        launch_ui = $UiSummary
        scope = [ordered]@{
            os_test_scope = 'Windows actual launcher invocation only'
            formal_registration = $false
            vcgc_endpoint_registry_used = $false
            vcgc_token_exported = $false
            mcp_pc_registration = $false
            github_write_or_registration = $false
            external_network_enabled = $false
            test_input = 'engine built-in SAMPLE_ROWS only; no governance matrix input supplied'
        }
    }
    try {
        Write-CreateOnceJson -LiteralPath $Script:ReceiptPath -Value $receipt
        $Script:ReceiptWritten = $true
    }
    catch {
        throw "STOP: could not create-once write outer receipt: $($_.Exception.Message)"
    }
}

try {
    Assert-WindowsHost
    $downloadFull = Get-ExistingDirectoryNoReparse -PathText $DownloadRoot
    $ownerFull = Get-ExistingDirectoryNoReparse -PathText $OwnerRoot
    Acquire-UserMutex

    $verifiedSources = [System.Collections.Generic.List[object]]::new()
    foreach ($source in $SourceSet) {
        $sourcePath = Get-ExistingFileNoReparse -PathText (Join-Path $downloadFull $source.name)
        $actualSha = Get-Sha256Lower -LiteralPath $sourcePath
        if ($actualSha -ne $source.expected_sha256) {
            throw "STOP: SHA-256 mismatch for $($source.name); expected $($source.expected_sha256), actual $actualSha."
        }
        [void]$verifiedSources.Add([pscustomobject][ordered]@{
            label = $source.label
            name = $source.name
            path = $sourcePath
            sha256 = $actualSha
            verified = $true
        })
    }
    $Script:VerifiedSources = @($verifiedSources)

    $Script:Candidate = New-CandidateDirectory -ValidatedOwnerRoot $ownerFull
    $Script:LogPath = Join-Path $Script:Candidate 'bootstrap.log'
    $Script:ReceiptPath = Join-Path $Script:Candidate 'bootstrap_receipt.json'
    Write-LogLine -Message 'candidate_created=true; source_set_sha256_verified=true; downloaded_html_and_readme_will_not_be_executed'

    $pyCommand = Get-Command py.exe -CommandType Application -ErrorAction Stop
    $pyLauncher = $pyCommand.Source
    $Script:PythonLauncher = $pyLauncher
    if ([string]::IsNullOrWhiteSpace($pyLauncher)) {
        throw 'STOP: py.exe resolved without an executable path.'
    }
    $probeCode = 'import importlib.util,json,sys; info={"python":sys.executable,"version":[sys.version_info[0],sys.version_info[1],sys.version_info[2]],"pyarrow":importlib.util.find_spec("pyarrow") is not None,"psutil":importlib.util.find_spec("psutil") is not None}; print(json.dumps(info,separators=(",",":"))); raise SystemExit(0 if info["version"] >= [3,11,0] and info["pyarrow"] else 2)'
    $probeResult = Invoke-CapturedProcess -FilePath $pyLauncher -Arguments @('-3', '-X', 'utf8', '-c', $probeCode) -Name 'python-resolve-and-dependency-probe'
    $probeInfo = ConvertFrom-CapturedJson -Result $probeResult -Name 'python-resolve-and-dependency-probe'
    if ($null -eq $probeInfo.python -or [string]::IsNullOrWhiteSpace([string]$probeInfo.python)) {
        throw 'STOP: py.exe probe did not return an actual Python executable.'
    }
    $pythonExecutable = Get-ExistingFileNoReparse -PathText ([string]$probeInfo.python)
    $Script:ProbeInfo = $probeInfo
    $Script:PythonExecutable = $pythonExecutable
    if ($null -eq $probeInfo.version -or [int]$probeInfo.version[0] -lt 3 -or ([int]$probeInfo.version[0] -eq 3 -and [int]$probeInfo.version[1] -lt 11)) {
        throw 'STOP: existing py -3 interpreter is older than Python 3.11; no installation was attempted.'
    }
    if ($probeResult.ExitCode -ne 0 -and [bool]$probeInfo.pyarrow) {
        throw "STOP: Python dependency probe exited $($probeResult.ExitCode) for an otherwise complete environment."
    }
    if (-not [bool]$probeInfo.pyarrow) {
        New-DependencyReviewPlan -Path (Join-Path $Script:Candidate 'dependency-review.md') -PythonExecutable $pythonExecutable -CandidatePath $Script:Candidate
        $Script:RunStatus = 'BLOCKED_MISSING_PYARROW'
        $Script:FailureMessage = 'pyarrow is missing; owner-reviewed VCGC EnvManager dependency request required; no installation attempted.'
        Write-LogLine -Message 'status=BLOCKED_MISSING_PYARROW; engine_execution=false; install_attempted=false'
        throw "STOP: $($Script:FailureMessage)"
    }
    Write-LogLine -Message ("python_resolved=true; pyarrow_present=true; psutil_present={0}" -f [bool]$probeInfo.psutil)

    $copiedSources = [System.Collections.Generic.List[object]]::new()
    foreach ($source in $verifiedSources) {
        $destination = Get-SafeChildPath -ExistingBase $Script:Candidate -ChildPath (Join-Path $Script:Candidate $source.name)
        if (Test-Path -LiteralPath $destination) {
            throw "STOP: refusing to overwrite candidate source: $destination"
        }
        [System.IO.File]::Copy($source.path, $destination, $false)
        $copiedSha = Get-Sha256Lower -LiteralPath $destination
        if ($copiedSha -ne $source.sha256) {
            throw "STOP: copied SHA-256 mismatch for $($source.name); original preserved and candidate is not runnable."
        }
        [void]$copiedSources.Add([pscustomobject][ordered]@{
            label = $source.label
            name = $source.name
            path = $destination
            sha256 = $copiedSha
            verified = $true
        })
    }
    $Script:CopiedSources = @($copiedSources)
    $candidateSource = [string](($copiedSources | Where-Object { $_.label -eq 'engine_source' }).path)
    $candidateOutput = Get-SafeChildPath -ExistingBase $Script:Candidate -ChildPath (Join-Path $Script:Candidate 'output')
    Write-LogLine -Message 'copy3_filecopy_nooverwrite=true; copied_hashes_rechecked=true; original_source_preserved=true'

    $doctorResult = Invoke-CapturedProcess -FilePath $pythonExecutable -Arguments @('-X', 'utf8', '-B', $candidateSource, '--doctor') -Name 'doctor'
    if ($doctorResult.ExitCode -ne 0) {
        throw "STOP: doctor exit code $($doctorResult.ExitCode)."
    }
    $doctorJson = ConvertFrom-CapturedJson -Result $doctorResult -Name 'doctor'
    Assert-ExactBoolean -Object $doctorJson.network -PropertyName 'external_enabled' -Expected $false
    Assert-ExactBoolean -Object $doctorJson.network -PropertyName 'approved_by_vcgc' -Expected $false
    $doctorSummary = [ordered]@{
        exit_code = [int]$doctorResult.ExitCode
        stdout_json_valid = $true
        network_external_enabled = [bool]$doctorJson.network.external_enabled
        network_approved_by_vcgc = [bool]$doctorJson.network.approved_by_vcgc
        no_external_network_asserted = $true
    }
    Write-LogLine -Message 'doctor_pass=true; network.external_enabled=false; network.approved_by_vcgc=false'

    $selfTestResult = Invoke-CapturedProcess -FilePath $pythonExecutable -Arguments @('-X', 'utf8', '-B', $candidateSource, '--self-test', '--output', $candidateOutput) -Name 'self-test'
    if ($selfTestResult.ExitCode -ne 0) {
        throw "STOP: self-test exit code $($selfTestResult.ExitCode)."
    }
    $selfTestJson = ConvertFrom-CapturedJson -Result $selfTestResult -Name 'self-test'
    Assert-ExactBoolean -Object $selfTestJson.gate -PropertyName 'local_reference_pass' -Expected $true
    Assert-ExactBoolean -Object $selfTestJson.gate -PropertyName 'go_live' -Expected $false
    if ($null -eq $selfTestJson.cases -or (-not ($selfTestJson.cases -is [int]) -and -not ($selfTestJson.cases -is [long]))) {
        throw 'STOP: self-test JSON cases is not an actual integer count.'
    }
    $caseCount = [int]$selfTestJson.cases
    if ($caseCount -lt 1) {
        throw 'STOP: self-test JSON reported no executed cases.'
    }
    if ($null -eq $selfTestJson.output -or -not [System.IO.Directory]::Exists([string]$selfTestJson.output)) {
        throw 'STOP: self-test output directory was not created.'
    }
    $reportedOutput = [System.IO.Path]::GetFullPath([string]$selfTestJson.output)
    if (-not $reportedOutput.StartsWith(([System.IO.Path]::GetFullPath($candidateOutput).TrimEnd('\') + '\'), [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "STOP: self-test output escaped candidate output root: $reportedOutput"
    }
    $selfTestSummary = [ordered]@{
        exit_code = [int]$selfTestResult.ExitCode
        stdout_json_valid = $true
        status = [string]$selfTestJson.status
        cases = $caseCount
        local_reference_pass = [bool]$selfTestJson.gate.local_reference_pass
        go_live = [bool]$selfTestJson.gate.go_live
        output = $reportedOutput
        fixture_scope = 'local HTTP fixture only'
    }
    $Script:RunStatus = 'PASS_FINITE_LOCAL_REFERENCE'
    Write-LogLine -Message ("self_test_pass=true; cases={0}; local_reference_pass=true; go_live=false; formal_registration=false" -f $caseCount)

    $uiSummary = $null
    if ($LaunchUI) {
        $candidateUi = Get-SafeChildPath -ExistingBase $Script:Candidate -ChildPath (Join-Path $Script:Candidate 'UI')
        if (Test-Path -LiteralPath $candidateUi) {
            throw "STOP: UI output path unexpectedly exists; refusing overwrite: $candidateUi"
        }
        Write-Host ''
        Write-Host 'Fixture PASS. Starting the optional UI in the foreground only.'
        Write-Host 'Copy the printed http://127.0.0.1:<port> URL manually. No browser will be opened; press Ctrl+C to exit.'
        $uiArgs = @('-X', 'utf8', '-B', $candidateSource, '--no-browser', '--port', '0', '--output', $candidateUi)
        $uiStartedAt = [DateTime]::UtcNow.ToString('o')
        & $pythonExecutable @uiArgs
        $uiExitCode = $LASTEXITCODE
        $uiRecord = [ordered]@{
            name = 'launch-ui-foreground'
            executable = $pythonExecutable
            arguments = @($uiArgs)
            started_at_utc = $uiStartedAt
            finished_at_utc = [DateTime]::UtcNow.ToString('o')
            exit_code = [int]$uiExitCode
            stdout_utf8 = $true
            stdout_capture = 'foreground_console_loopback_url_manual_copy'
            stderr_exported = $false
        }
        [void]$Script:CommandRecords.Add([pscustomobject]$uiRecord)
        Write-LogLine -Message ("ui_foreground_exit_code={0}; browser_open=false; persistent_background_process=false" -f $uiExitCode)
        if ($uiExitCode -ne 0) {
            throw "STOP: foreground UI exit code $uiExitCode."
        }
        $uiSummary = [ordered]@{
            exit_code = [int]$uiExitCode
            foreground = $true
            no_browser = $true
            port = 0
            output = $candidateUi
            loopback_url_manual_copy = $true
            persistent_background_process = $false
        }
    }

    Write-ReceiptIfAbsent -ValidatedDownloadRoot $downloadFull -ValidatedOwnerRoot $ownerFull -VerifiedSources @($verifiedSources) -CopiedSources @($copiedSources) -ProbeInfo $probeInfo -PythonLauncher $pyLauncher -PythonExecutable $pythonExecutable -ScopeStatus $Script:RunStatus -Reason 'Finite local candidate doctor and self-test completed; formal registration remains blocked.' -DoctorSummary $doctorSummary -SelfTestSummary $selfTestSummary -UiSummary $uiSummary
    Write-LogLine -Message 'receipt_create_once=true; completed=true'
    Write-Host ("PASS: finite candidate evidence saved under {0}" -f $Script:Candidate)
    Write-Host ("Receipt: {0}" -f $Script:ReceiptPath)
}
catch {
    $Script:FailureMessage = $_.Exception.Message
    if ($Script:RunStatus -eq 'NOT_STARTED') {
        $Script:RunStatus = 'FAILED_BEFORE_COMPLETION'
    }
    if ($null -ne $Script:LogPath) {
        try { Write-LogLine -Message ('failure=' + $Script:FailureMessage) } catch { }
    }
    if ($null -ne $Script:Candidate -and $null -ne $Script:ReceiptPath -and -not $Script:ReceiptWritten) {
        try {
            $fallbackProbe = [pscustomobject]@{ pyarrow = $false; psutil = $false }
            $receiptProbe = if ($null -ne $Script:ProbeInfo) { $Script:ProbeInfo } else { $fallbackProbe }
            Write-ReceiptIfAbsent -ValidatedDownloadRoot ([string]$DownloadRoot) -ValidatedOwnerRoot ([string]$OwnerRoot) -VerifiedSources $Script:VerifiedSources -CopiedSources $Script:CopiedSources -ProbeInfo $receiptProbe -PythonLauncher $Script:PythonLauncher -PythonExecutable $Script:PythonExecutable -ScopeStatus $Script:RunStatus -Reason $Script:FailureMessage -DoctorSummary $null -SelfTestSummary $null -UiSummary $null
        }
        catch { }
    }
    throw
}
finally {
    Release-UserMutex
}
