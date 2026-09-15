# ============================================================================
#   VeritasDataForge v4.2 — ONE-SHOT ACTIVATOR
#   · Veritas Intelligence Analytics ·
#
#   Consolidates all SSOT, supportive modules, fetchers, tests, cockpit
#   into a single launchable system. Runs in 6 phases:
#
#     PHASE 1  PREFLIGHT          — env probe, python detect, paths
#     PHASE 2  SUPPORTIVE         — verify 3 supportive modules import
#     PHASE 3  CONSOLIDATE        — copy all VDF files into module root
#     PHASE 4  HEALTH CHECK       — bridge.is_alive() + env_health()
#     PHASE 5  TEST SUITE         — run vdf_tests_v4.py + parse results
#     PHASE 6  ACTIVATE           — start API + open cockpit
#
#   Usage:
#     .\Invoke-VDF-OneShot.ps1                         # full activation
#     .\Invoke-VDF-OneShot.ps1 -Mode TestOnly          # just tests
#     .\Invoke-VDF-OneShot.ps1 -Mode CheckOnly         # checklist only
#     .\Invoke-VDF-OneShot.ps1 -SkipNetwork            # no live tests
#     .\Invoke-VDF-OneShot.ps1 -Verbose                # detailed output
#
#   Author: Tony / VIA Intelligence Analytics
#   Build:  2026-05-26
# ============================================================================

[CmdletBinding()]
param(
    [ValidateSet('Full','TestOnly','CheckOnly','CockpitOnly')]
    [string] $Mode = 'Full',

    [switch] $SkipNetwork,
    [switch] $StrictMode,
    [int]    $ApiPort = 8765
)

$ErrorActionPreference = 'Stop'

# ============================================================================
# CONFIG — these paths match your environment
# ============================================================================
$Script:VIA_ROOT          = 'C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module'
$Script:VDF_ROOT          = Join-Path $Script:VIA_ROOT 'VeritasDataForge'
$Script:SUPPORTIVE_ROOT   = Join-Path $Script:VIA_ROOT 'supportive_module'

# Critical supportive modules — MUST exist
$Script:REQUIRED_SUPPORTIVE = @(
    'VIA_EnvManager.py',
    'VeritasAegisNexus.py',
    'VeritasCeleritas.py'
)

# Optional supportive modules (load if present)
$Script:OPTIONAL_SUPPORTIVE = @(
    'VIA_SSOT_Unified.py',
    'VIA_RegistryCore_v1.py',
    'VIA_Runtime_Bridge_All_in_One.py',
    'VIA_Panorama_AST_RuntimeInjector.py'
)

# Python interpreter candidates (in priority order)
$Script:PYTHON_CANDIDATES = @(
    'C:\Users\tonyk\envs\via_core_312\Scripts\python.exe',
    'C:\Users\tonyk\envs\via_core\Scripts\python.exe',
    'C:\Python313\python.exe',
    'C:\Python312\python.exe',
    'python'
)

# VDF source layout (relative to VDF_ROOT)
$Script:VDF_LAYOUT = @{
    'config'  = @('via_master_ssot.json', 'macro_ssot.json', 'tw_consensus_ssot.json', 'vdf_fetch_matrix.json')
    'src'     = @('vdf_supportive_bridge.py', 'vdf_fetchers_market.py', 'vdf_fetchers_macro.py',
                  'vdf_fetchers_financials.py', 'vdf_fetchers_fiscal.py', 'vdf_fetchers_sentiment.py',
                  'vdf_fetchers_etf_holdings.py', 'vdf_fetchers_consensus.py', 'vdf_fetchers_derived.py',
                  'vdf_fetchers_tdcc.py', 'vdf_fetchers_fed.py',
                  'vdf_tests_v4.py', 'vdf_core.py', 'vdf_api.py')
    'cockpit' = @('index.html', 'cockpit.css', 'cockpit.js')
}

# Color palette for output
$Script:COLOR_OK     = 'Green'
$Script:COLOR_WARN   = 'Yellow'
$Script:COLOR_FAIL   = 'Red'
$Script:COLOR_INFO   = 'Cyan'
$Script:COLOR_DIM    = 'DarkGray'
$Script:COLOR_TITLE  = 'Magenta'

# Checklist state (used across all phases)
$Script:CHECKLIST = [ordered]@{}

# ============================================================================
# Helper functions
# ============================================================================

function Write-Banner {
    param([string]$Text, [string]$Char = '═')
    $line = $Char * 78
    Write-Host ""
    Write-Host $line -ForegroundColor $Script:COLOR_TITLE
    Write-Host "  $Text" -ForegroundColor $Script:COLOR_TITLE
    Write-Host $line -ForegroundColor $Script:COLOR_TITLE
}

function Write-Step {
    param([string]$Label, [int]$Step, [int]$Total)
    Write-Host ""
    Write-Host "  ┌─ PHASE $Step/$Total · $Label" -ForegroundColor $Script:COLOR_INFO
    Write-Host "  │" -ForegroundColor $Script:COLOR_INFO
}

function Write-Check {
    param(
        [string]$Name,
        [ValidateSet('OK','FAIL','WARN','SKIP','INFO')]
        [string]$Status = 'INFO',
        [string]$Detail = ''
    )
    $marker = switch ($Status) {
        'OK'   { '✓' ; $color = $Script:COLOR_OK }
        'FAIL' { '✗' ; $color = $Script:COLOR_FAIL }
        'WARN' { '⚠' ; $color = $Script:COLOR_WARN }
        'SKIP' { '○' ; $color = $Script:COLOR_DIM }
        'INFO' { 'ℹ' ; $color = $Script:COLOR_INFO }
    }
    $padded = $Name.PadRight(50)
    if ($Detail) {
        Write-Host "  │  $marker $padded " -NoNewline -ForegroundColor $color
        Write-Host "$Detail" -ForegroundColor $Script:COLOR_DIM
    } else {
        Write-Host "  │  $marker $padded" -ForegroundColor $color
    }
    $Script:CHECKLIST[$Name] = $Status
}

function Resolve-Python {
    foreach ($candidate in $Script:PYTHON_CANDIDATES) {
        if ($candidate -eq 'python') {
            $cmd = Get-Command python -ErrorAction SilentlyContinue
            if ($cmd) { return $cmd.Source }
        } elseif (Test-Path -LiteralPath $candidate) {
            return $candidate
        }
    }
    throw 'No usable Python interpreter found. Tried: ' + ($Script:PYTHON_CANDIDATES -join ', ')
}

function Invoke-PythonCheck {
    param(
        [string]$Python,
        [string]$Code,
        [int]$TimeoutSec = 30
    )
    $tempFile = [IO.Path]::GetTempFileName() + '.py'
    try {
        Set-Content -LiteralPath $tempFile -Value $Code -Encoding UTF8
        $proc = Start-Process -FilePath $Python -ArgumentList $tempFile `
            -NoNewWindow -PassThru -RedirectStandardOutput "$tempFile.out" -RedirectStandardError "$tempFile.err"
        if (-not $proc.WaitForExit($TimeoutSec * 1000)) {
            $proc.Kill()
            throw "Python check timed out after $TimeoutSec sec"
        }
        $stdout = if (Test-Path "$tempFile.out") { Get-Content -Raw "$tempFile.out" } else { '' }
        $stderr = if (Test-Path "$tempFile.err") { Get-Content -Raw "$tempFile.err" } else { '' }
        return @{
            ExitCode = $proc.ExitCode
            Stdout   = $stdout
            Stderr   = $stderr
        }
    } finally {
        Remove-Item -LiteralPath $tempFile -ErrorAction SilentlyContinue
        Remove-Item -LiteralPath "$tempFile.out" -ErrorAction SilentlyContinue
        Remove-Item -LiteralPath "$tempFile.err" -ErrorAction SilentlyContinue
    }
}

# ============================================================================
# PHASE 1 — PREFLIGHT
# ============================================================================
function Invoke-Phase1-Preflight {
    Write-Step -Label 'PREFLIGHT — environment probe' -Step 1 -Total 6

    # Module root exists
    if (Test-Path -LiteralPath $Script:VIA_ROOT) {
        Write-Check 'VIA module root exists' 'OK' $Script:VIA_ROOT
    } else {
        Write-Check 'VIA module root exists' 'FAIL' "Not found: $Script:VIA_ROOT"
        throw "VIA module root not found"
    }

    # Supportive root exists
    if (Test-Path -LiteralPath $Script:SUPPORTIVE_ROOT) {
        Write-Check 'Supportive module root exists' 'OK' $Script:SUPPORTIVE_ROOT
    } else {
        Write-Check 'Supportive module root exists' 'FAIL' "Not found: $Script:SUPPORTIVE_ROOT"
        throw "Supportive root not found"
    }

    # VDF root (create if missing)
    if (-not (Test-Path -LiteralPath $Script:VDF_ROOT)) {
        New-Item -ItemType Directory -Force -Path $Script:VDF_ROOT | Out-Null
        Write-Check 'VDF root created' 'OK' $Script:VDF_ROOT
    } else {
        Write-Check 'VDF root exists' 'OK' $Script:VDF_ROOT
    }

    # Python interpreter
    try {
        $py = Resolve-Python
        $Script:PYTHON = $py
        $version = & $py --version 2>&1
        Write-Check 'Python interpreter found' 'OK' "$py [$version]"
    } catch {
        Write-Check 'Python interpreter found' 'FAIL' $_.Exception.Message
        throw
    }

    # PowerShell version
    $psVer = $PSVersionTable.PSVersion.ToString()
    if ($PSVersionTable.PSVersion.Major -ge 7) {
        Write-Check 'PowerShell version' 'OK' "v$psVer"
    } else {
        Write-Check 'PowerShell version' 'WARN' "v$psVer (recommend PS7+)"
    }
}

# ============================================================================
# PHASE 2 — SUPPORTIVE MODULES
# ============================================================================
function Invoke-Phase2-Supportive {
    Write-Step -Label 'SUPPORTIVE — verify 3 required + check optional' -Step 2 -Total 6

    # Required modules — must all exist
    $missingRequired = @()
    foreach ($name in $Script:REQUIRED_SUPPORTIVE) {
        $path = Join-Path $Script:SUPPORTIVE_ROOT $name
        if (Test-Path -LiteralPath $path) {
            $size = (Get-Item $path).Length
            $kb = [math]::Round($size / 1024, 0)
            Write-Check "Required: $name" 'OK' "$kb KB"
        } else {
            Write-Check "Required: $name" 'FAIL' "Not found at $path"
            $missingRequired += $name
        }
    }

    if ($missingRequired.Count -gt 0) {
        throw "Missing required supportive modules: $($missingRequired -join ', ')"
    }

    # Optional modules — report status but don't fail
    foreach ($name in $Script:OPTIONAL_SUPPORTIVE) {
        $path = Join-Path $Script:SUPPORTIVE_ROOT $name
        if (Test-Path -LiteralPath $path) {
            Write-Check "Optional: $name" 'OK' 'available'
        } else {
            Write-Check "Optional: $name" 'SKIP' 'not present (OK)'
        }
    }

    # Python import probe — actually load the 3 required modules
    Write-Host "  │" -ForegroundColor $Script:COLOR_INFO
    Write-Host "  │  Probing import of 3 required supportive modules..." -ForegroundColor $Script:COLOR_DIM

    $importCode = @"
import sys
sys.path.insert(0, r'$Script:SUPPORTIVE_ROOT')
results = {}
for mod in ['VIA_EnvManager', 'VeritasAegisNexus', 'VeritasCeleritas']:
    try:
        __import__(mod)
        results[mod] = 'LOADED'
    except Exception as e:
        results[mod] = f'FAIL: {type(e).__name__}: {e}'
for k, v in results.items():
    print(f'{k}={v}')
"@
    $probe = Invoke-PythonCheck -Python $Script:PYTHON -Code $importCode -TimeoutSec 60

    foreach ($line in ($probe.Stdout -split "`n")) {
        $line = $line.Trim()
        if (-not $line) { continue }
        if ($line -match '^(\S+)=(.+)$') {
            $mod = $matches[1]; $status = $matches[2]
            if ($status -eq 'LOADED') {
                Write-Check "Python import: $mod" 'OK' 'live import successful'
            } else {
                Write-Check "Python import: $mod" 'FAIL' $status
            }
        }
    }
}

# ============================================================================
# PHASE 3 — CONSOLIDATE
# ============================================================================
function Invoke-Phase3-Consolidate {
    Write-Step -Label 'CONSOLIDATE — ensure VDF files in place' -Step 3 -Total 6

    foreach ($subdir in $Script:VDF_LAYOUT.Keys) {
        $target = Join-Path $Script:VDF_ROOT $subdir
        if (-not (Test-Path -LiteralPath $target)) {
            New-Item -ItemType Directory -Force -Path $target | Out-Null
            Write-Check "Created $subdir/" 'OK' $target
        } else {
            Write-Check "Subdirectory $subdir/" 'OK' "exists"
        }

        # Verify expected files are present
        $missing = @()
        foreach ($file in $Script:VDF_LAYOUT[$subdir]) {
            $filePath = Join-Path $target $file
            if (-not (Test-Path -LiteralPath $filePath)) {
                $missing += $file
            }
        }
        if ($missing.Count -eq 0) {
            Write-Check "  ${subdir}: all files present" 'OK' "$($Script:VDF_LAYOUT[$subdir].Count) files"
        } else {
            Write-Check "  ${subdir}: missing files" 'WARN' "$($missing -join ', ')"
        }
    }

    # Create runtime dirs
    foreach ($d in @('temp', 'output', 'logs')) {
        $path = Join-Path $Script:VDF_ROOT $d
        if (-not (Test-Path -LiteralPath $path)) {
            New-Item -ItemType Directory -Force -Path $path | Out-Null
        }
        Write-Check "Runtime dir: $d/" 'OK' $path
    }
}

# ============================================================================
# PHASE 4 — HEALTH CHECK
# ============================================================================
function Invoke-Phase4-HealthCheck {
    Write-Step -Label 'HEALTH — bridge.is_alive() + env_health()' -Step 4 -Total 6

    $healthCode = @"
import sys, json
sys.path.insert(0, r'$Script:SUPPORTIVE_ROOT')
sys.path.insert(0, r'$Script:VDF_ROOT' + '\\src')

try:
    import vdf_supportive_bridge as bridge
    health = bridge.is_alive()
    env = bridge.env_health()
    py = bridge.detect_python()
    print('=== BRIDGE OK ===')
    print(json.dumps(health, indent=2, ensure_ascii=False, default=str))
    print('=== ENV HEALTH ===')
    print(json.dumps(env, indent=2, ensure_ascii=False, default=str))
    print('=== PYTHON ===')
    print(json.dumps(py, indent=2, ensure_ascii=False, default=str))
except Exception as e:
    print(f'BRIDGE_FAIL: {type(e).__name__}: {e}')
"@
    $check = Invoke-PythonCheck -Python $Script:PYTHON -Code $healthCode -TimeoutSec 60

    if ($check.Stdout -match 'BRIDGE_FAIL') {
        $errLine = ($check.Stdout -split "`n" | Where-Object { $_ -match 'BRIDGE_FAIL' }) -join ''
        Write-Check 'Bridge import' 'FAIL' $errLine
        return
    }

    # Parse output sections
    $sections = $check.Stdout -split '=== ' | Where-Object { $_.Trim() }
    foreach ($section in $sections) {
        if ($section -match '^BRIDGE OK ===\s*(.*)$' -or $section -match '^BRIDGE OK\s*===([\s\S]*)$') {
            try {
                $jsonText = $section -replace '^BRIDGE OK\s*===\s*', ''
                $bridgeData = $jsonText | ConvertFrom-Json
                $aegisOK   = $bridgeData.aegis.loaded
                $celOK     = $bridgeData.celeritas.loaded
                $envOK     = $bridgeData.envmanager.loaded
                if ($aegisOK)   { Write-Check 'Bridge: VeritasAegisNexus'  'OK' 'ResilientHTTPClient ready' } else { Write-Check 'Bridge: VeritasAegisNexus' 'FAIL' 'module not loaded' }
                if ($celOK)     { Write-Check 'Bridge: VeritasCeleritas'   'OK' 'parallel_map + cache ready' } else { Write-Check 'Bridge: VeritasCeleritas' 'FAIL' 'module not loaded' }
                if ($envOK)     { Write-Check 'Bridge: VIA_EnvManager'     'OK' 'env_health + detect_python ready' } else { Write-Check 'Bridge: VIA_EnvManager' 'FAIL' 'module not loaded' }

                if ($bridgeData.celeritas.recommended_threads) {
                    Write-Check 'Recommended thread budget' 'INFO' "$($bridgeData.celeritas.recommended_threads) workers"
                }
            } catch {
                Write-Check 'Bridge JSON parse' 'WARN' $_.Exception.Message
            }
        }
    }
}

# ============================================================================
# PHASE 5 — TEST SUITE
# ============================================================================
function Invoke-Phase5-Tests {
    Write-Step -Label 'TEST SUITE — vdf_tests_v4.py' -Step 5 -Total 6

    $testScript = Join-Path $Script:VDF_ROOT 'src\vdf_tests_v4.py'
    if (-not (Test-Path -LiteralPath $testScript)) {
        Write-Check 'Test suite file' 'FAIL' "Not found: $testScript"
        return $false
    }

    Write-Check 'Running vdf_tests_v4.py...' 'INFO' '(this takes 5-15 seconds)'
    Write-Host "  │" -ForegroundColor $Script:COLOR_INFO

    $env:PYTHONIOENCODING = 'utf-8'
    $args = @($testScript)
    if (-not $SkipNetwork) { $args += '--report' }

    $output = & $Script:PYTHON $args 2>&1 | Out-String
    $exitCode = $LASTEXITCODE

    # Parse summary
    $totalLine = $output -split "`n" | Where-Object { $_ -match 'TOTAL:\s+(\d+)\s+pass.*?(\d+)\s+fail.*?(\d+)\s+skip' } | Select-Object -First 1
    if ($totalLine -match 'TOTAL:\s+(\d+)\s+pass.*?(\d+)\s+fail.*?(\d+)\s+skip\s*\((\d+)') {
        $pass = [int]$matches[1]; $fail = [int]$matches[2]; $skip = [int]$matches[3]; $total = [int]$matches[4]
        if ($fail -eq 0) {
            Write-Check "Test result: $pass/$total pass" 'OK' "($skip skipped)"
        } else {
            Write-Check "Test result: $fail failed" 'FAIL' "$pass passed of $total"
        }
    } else {
        Write-Check 'Test result parse' 'WARN' 'Could not parse summary'
    }

    # Parse per-category
    $categoryLines = $output -split "`n" | Where-Object { $_ -match '^\s+(\w+)\s+(\d+)\s+/\s+(\d+)\s+passed' }
    foreach ($cl in $categoryLines) {
        if ($cl -match '^\s+(\w+)\s+(\d+)\s+/\s+(\d+)\s+passed') {
            $cat = $matches[1]; $p = [int]$matches[2]; $t = [int]$matches[3]
            $status = if ($p -eq $t) { 'OK' } else { 'FAIL' }
            Write-Check "  Category: $cat" $status "$p/$t passed"
        }
    }

    return ($exitCode -eq 0)
}

# ============================================================================
# PHASE 6 — ACTIVATE
# ============================================================================
function Invoke-Phase6-Activate {
    Write-Step -Label 'ACTIVATE — start API + open cockpit' -Step 6 -Total 6

    if ($Mode -eq 'TestOnly' -or $Mode -eq 'CheckOnly') {
        Write-Check 'Activation skipped' 'SKIP' "Mode=$Mode"
        return
    }

    # Start API (background)
    $apiScript = Join-Path $Script:VDF_ROOT 'src\vdf_api.py'
    if (Test-Path -LiteralPath $apiScript) {
        $logFile = Join-Path $Script:VDF_ROOT "logs\api_$((Get-Date).ToString('yyyyMMdd_HHmmss')).log"
        try {
            $apiProc = Start-Process -FilePath $Script:PYTHON -ArgumentList @($apiScript, '--port', $ApiPort) `
                -PassThru -WindowStyle Hidden `
                -RedirectStandardOutput $logFile `
                -RedirectStandardError "$logFile.err"
            Start-Sleep -Seconds 2
            if ($apiProc.HasExited) {
                Write-Check 'API server' 'FAIL' "exited immediately, see $logFile.err"
            } else {
                Write-Check 'API server started' 'OK' "PID=$($apiProc.Id) port=$ApiPort log=$logFile"
                $Script:API_PID = $apiProc.Id
            }
        } catch {
            Write-Check 'API server' 'FAIL' $_.Exception.Message
        }
    } else {
        Write-Check 'API server' 'SKIP' 'vdf_api.py not found'
    }

    # Open cockpit
    $cockpitFile = Join-Path $Script:VDF_ROOT 'cockpit\index.html'
    if (Test-Path -LiteralPath $cockpitFile) {
        if ($Mode -ne 'CockpitOnly') {
            Start-Sleep -Seconds 1
        }
        Start-Process $cockpitFile
        Write-Check 'Cockpit opened' 'OK' $cockpitFile
    } else {
        Write-Check 'Cockpit' 'FAIL' "Not found: $cockpitFile"
    }
}

# ============================================================================
# FINAL SUMMARY
# ============================================================================
function Show-Summary {
    Write-Banner 'VDF v4.2 ACTIVATION COMPLETE — CHECKLIST'

    $okCount   = ($Script:CHECKLIST.Values | Where-Object { $_ -eq 'OK'   }).Count
    $failCount = ($Script:CHECKLIST.Values | Where-Object { $_ -eq 'FAIL' }).Count
    $warnCount = ($Script:CHECKLIST.Values | Where-Object { $_ -eq 'WARN' }).Count
    $skipCount = ($Script:CHECKLIST.Values | Where-Object { $_ -eq 'SKIP' }).Count
    $infoCount = ($Script:CHECKLIST.Values | Where-Object { $_ -eq 'INFO' }).Count
    $total = $Script:CHECKLIST.Count

    Write-Host ""
    Write-Host "  Total checks: $total" -ForegroundColor $Script:COLOR_INFO
    Write-Host "    ✓ OK:    $okCount"   -ForegroundColor $Script:COLOR_OK
    if ($warnCount -gt 0) { Write-Host "    ⚠ WARN:  $warnCount" -ForegroundColor $Script:COLOR_WARN }
    if ($failCount -gt 0) { Write-Host "    ✗ FAIL:  $failCount" -ForegroundColor $Script:COLOR_FAIL }
    if ($skipCount -gt 0) { Write-Host "    ○ SKIP:  $skipCount" -ForegroundColor $Script:COLOR_DIM }
    if ($infoCount -gt 0) { Write-Host "    ℹ INFO:  $infoCount" -ForegroundColor $Script:COLOR_INFO }
    Write-Host ""

    # Verdict
    if ($failCount -eq 0) {
        Write-Host "  STATUS: ✓ ALL SYSTEMS GO" -ForegroundColor $Script:COLOR_OK
    } elseif ($failCount -le 2) {
        Write-Host "  STATUS: ⚠ DEGRADED — $failCount failures (system usable)" -ForegroundColor $Script:COLOR_WARN
    } else {
        Write-Host "  STATUS: ✗ FAULT — $failCount failures (intervention required)" -ForegroundColor $Script:COLOR_FAIL
    }

    # Failed checks detail
    if ($failCount -gt 0) {
        Write-Host ""
        Write-Host "  FAILED CHECKS:" -ForegroundColor $Script:COLOR_FAIL
        $Script:CHECKLIST.GetEnumerator() | Where-Object { $_.Value -eq 'FAIL' } | ForEach-Object {
            Write-Host "    ✗ $($_.Key)" -ForegroundColor $Script:COLOR_FAIL
        }
    }

    # Active resources
    Write-Host ""
    Write-Host "  ACTIVE RESOURCES:" -ForegroundColor $Script:COLOR_INFO
    Write-Host "    VDF root:    $Script:VDF_ROOT"
    Write-Host "    Python:      $Script:PYTHON"
    if ($Script:API_PID) {
        Write-Host "    API PID:     $Script:API_PID (port $ApiPort)"
    }
    Write-Host ""
    Write-Host "  Press Enter to keep window open, Ctrl+C to exit..." -ForegroundColor $Script:COLOR_DIM
}

# ============================================================================
# MAIN — phase orchestration
# ============================================================================

Clear-Host
Write-Banner 'VeritasDataForge v4.2 — ONE-SHOT ACTIVATOR'
Write-Host "  Mode:       $Mode"             -ForegroundColor $Script:COLOR_INFO
Write-Host "  SkipNetwork: $SkipNetwork"     -ForegroundColor $Script:COLOR_INFO
Write-Host "  VIA root:   $Script:VIA_ROOT"  -ForegroundColor $Script:COLOR_INFO

$startTime = Get-Date

try {
    # Always run preflight + supportive (these are required)
    Invoke-Phase1-Preflight
    Invoke-Phase2-Supportive

    if ($Mode -ne 'CheckOnly') {
        Invoke-Phase3-Consolidate
        Invoke-Phase4-HealthCheck
    }

    if ($Mode -ne 'CheckOnly' -and $Mode -ne 'CockpitOnly') {
        $testsPassed = Invoke-Phase5-Tests
        if (-not $testsPassed -and $StrictMode) {
            throw "Tests failed and StrictMode enabled"
        }
    }

    if ($Mode -eq 'Full' -or $Mode -eq 'CockpitOnly') {
        Invoke-Phase6-Activate
    }

    $elapsed = (Get-Date) - $startTime
    Show-Summary
    Write-Host "  Elapsed: $([math]::Round($elapsed.TotalSeconds, 1)) sec" -ForegroundColor $Script:COLOR_DIM

    if ($Mode -eq 'Full' -or $Mode -eq 'CockpitOnly') {
        Read-Host | Out-Null
    }
}
catch {
    Write-Host ""
    Write-Host "  ╳ FATAL ERROR" -ForegroundColor $Script:COLOR_FAIL
    Write-Host "    $($_.Exception.Message)" -ForegroundColor $Script:COLOR_FAIL
    Show-Summary
    Write-Host ""
    Read-Host "  Press Enter to exit"
    exit 1
}
