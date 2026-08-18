#requires -Version 7.0
# =============================================================================
# VIA SSOT v22 Synonyms — Auto-Append + Verify Wrapper
#   - 自動把 patch 檔 append 到 VIA_SSOT_Unified.py 末尾
#   - 自動備份原檔(.bak_v22_<timestamp>)
#   - 自動用 via_core_312 Python 驗證 patch 載入 + self-test 13/13
#   - Idempotent:已 append 過會跳過(不會重複貼)
# =============================================================================

param(
    [string]$VIA_ROOT     = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics",
    [string]$PatchFile    = "",
    [switch]$Force,
    [switch]$VerifyOnly,
    [switch]$NoOpenHtml
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$script:VIA_ROOT     = $VIA_ROOT
$script:SUPPORT_DIR  = Join-Path $VIA_ROOT "module\supportive_module"
$script:SSOT_FILE    = Join-Path $script:SUPPORT_DIR "VIA_SSOT_Unified.py"
$script:TIMESTAMP    = Get-Date -Format "yyyyMMdd_HHmmss"
$script:BAK_FILE     = $script:SSOT_FILE + ".bak_v22_" + $script:TIMESTAMP
$script:MARKER       = "# VIA_SSOT_Unified v22 SYNONYM EXTENSION"

$script:PYTHON_CANDIDATES = @(
    "C:\Users\tonyk\envs\via_core_312\Scripts\python.exe",
    "C:\Users\tonyk\envs\via_core\Scripts\python.exe",
    "python",
    "py"
)

if (-not $PatchFile) {
    # Auto-locate patch file in common spots
    $candidates = @(
        "C:\Users\tonyk\OneDrive\Desktop\SUP_MDL655_SSOTUnifiedV22SynonymsPatch.py",
        "C:\Users\tonyk\Downloads\SUP_MDL655_SSOTUnifiedV22SynonymsPatch.py",
        ".\SUP_MDL655_SSOTUnifiedV22SynonymsPatch.py"
    )
    foreach ($p in $candidates) {
        if (Test-Path -LiteralPath $p) { $PatchFile = $p; break }
    }
}

function Save-Log {
    param([string]$Line, [string]$Color = "Gray")
    $msg = "[{0}] {1}" -f (Get-Date -Format "HH:mm:ss"), $Line
    Write-Host $msg -ForegroundColor $Color
}

function Get-Python {
    foreach ($p in $script:PYTHON_CANDIDATES) {
        try {
            if ($p -eq "python" -or $p -eq "py") {
                if (Get-Command $p -ErrorAction SilentlyContinue) { return $p }
            } elseif (Test-Path -LiteralPath $p) {
                return $p
            }
        } catch {}
    }
    throw "no usable python"
}

function Test-AlreadyAppended {
    if (-not (Test-Path -LiteralPath $script:SSOT_FILE)) { return $false }
    $content = Get-Content -LiteralPath $script:SSOT_FILE -Raw -Encoding UTF8
    return $content -like "*$($script:MARKER)*"
}

function Invoke-Append {
    Save-Log "Reading SSOT file: $($script:SSOT_FILE)" "DarkCyan"
    if (-not (Test-Path -LiteralPath $script:SSOT_FILE)) {
        throw "SSOT file not found: $($script:SSOT_FILE)"
    }
    if (-not (Test-Path -LiteralPath $PatchFile)) {
        throw "Patch file not found: $PatchFile"
    }

    Save-Log "Backing up original to: $($script:BAK_FILE)" "Yellow"
    Copy-Item -LiteralPath $script:SSOT_FILE -Destination $script:BAK_FILE -Force

    $orig  = [System.IO.File]::ReadAllText($script:SSOT_FILE, [System.Text.UTF8Encoding]::new($false))
    $patch = [System.IO.File]::ReadAllText($PatchFile,        [System.Text.UTF8Encoding]::new($false))

    if (-not $orig.EndsWith("`n")) { $orig = $orig + "`n" }
    $joined = $orig + "`n`n" + $patch + "`n"

    Save-Log "Appending v22 patch to SSOT (atomic write)..." "DarkCyan"
    $tmp = $script:SSOT_FILE + ".tmp_v22"
    [System.IO.File]::WriteAllText($tmp, $joined, [System.Text.UTF8Encoding]::new($false))
    [System.IO.File]::Replace($tmp, $script:SSOT_FILE, $null)
    Save-Log "Append complete." "Green"
}

function Invoke-Verify {
    param([string]$Python)
    Save-Log "py_compile syntax check on SSOT..." "DarkCyan"
    & $Python -m py_compile $script:SSOT_FILE
    if ($LASTEXITCODE -ne 0) {
        throw "SSOT py_compile FAILED after append. Restore from: $($script:BAK_FILE)"
    }
    Save-Log "py_compile OK" "Green"

    Save-Log "Running v22 self-test via Python..." "DarkCyan"
    $verifyScript = @"
import sys, builtins
builtins.true  = True
builtins.false = False
builtins.null  = None
sys.path.insert(0, r'$($script:SUPPORT_DIR)')
try:
    import VIA_SSOT_Unified as ssot
    stats = ssot.via_fin_synonyms_count()
    print(f"[STATS] canonical_keys = {stats['canonical_keys']}")
    print(f"[STATS] total_synonyms = {stats['total_synonyms']}")
    for cat, n in stats['by_category'].items():
        print(f"  {cat:>10s} : {n}")
    tests = [
        ('營業收入',             'revenue'),
        ('Revenue',              'revenue'),
        ('NET REVENUE',          'revenue'),
        ('基本每股盈餘',         'basic_eps'),
        ('Basic EPS',            'basic_eps'),
        ('ROE',                  'roe'),
        ('股東權益報酬率',       'roe'),
        ('營業活動之現金流量',   'operating_cashflow'),
        ('Operating Cash Flow',  'operating_cashflow'),
        ('負債權益比',           'debt_to_equity'),
        ('資產總計',             'total_assets'),
        ('Total Assets',         'total_assets'),
        ('XYZ_UNKNOWN_LABEL',    ''),
    ]
    ok = 0
    print()
    print('[LOOKUP TESTS]')
    for label, exp in tests:
        result = ssot.via_fin_synonym(label)
        cat = ssot.via_fin_category_of(result) if result else '-'
        flag = 'OK' if result == exp else 'FAIL'
        if result == exp: ok += 1
        print(f'  [{flag:>4s}] {label:30s} -> {result:25s} ({cat})')
    print()
    print(f'[RESULT] {ok}/{len(tests)} lookup tests passed')
    sys.exit(0 if ok == len(tests) else 1)
except Exception as exc:
    import traceback
    print(f'[FAIL] {type(exc).__name__}: {exc}')
    traceback.print_exc()
    sys.exit(2)
"@
    $tmpPy = Join-Path $env:TEMP "via_ssot_verify_$($script:TIMESTAMP).py"
    [System.IO.File]::WriteAllText($tmpPy, $verifyScript, [System.Text.UTF8Encoding]::new($false))
    & $Python -u $tmpPy
    $rc = $LASTEXITCODE
    Remove-Item -LiteralPath $tmpPy -Force -ErrorAction SilentlyContinue
    if ($rc -ne 0) {
        throw "Self-test FAILED (exit $rc). Restore from: $($script:BAK_FILE)"
    }
    Save-Log "Self-test ALL PASS" "Green"
}

# =============================================================================
# MAIN
# =============================================================================
try {
    Save-Log "=== VIA SSOT v22 Synonyms Auto-Append ===" "Cyan"
    Save-Log ("SSOT file  : " + $script:SSOT_FILE)
    Save-Log ("Patch file : " + $PatchFile)

    $Python = Get-Python
    Save-Log ("Python     : " + $Python) "Green"

    if (-not (Test-Path -LiteralPath $script:SSOT_FILE)) {
        throw "SSOT file not found: $($script:SSOT_FILE)"
    }
    if (-not $PatchFile -or -not (Test-Path -LiteralPath $PatchFile)) {
        throw "Patch file not provided / not found. Use -PatchFile <path>."
    }

    if ($VerifyOnly) {
        Save-Log "VerifyOnly mode (no append)" "Yellow"
        Invoke-Verify -Python $Python
    } else {
        if (Test-AlreadyAppended) {
            if ($Force) {
                Save-Log "Marker found — but -Force specified, will append again" "Yellow"
                Invoke-Append
            } else {
                Save-Log "Marker '$($script:MARKER)' already exists in SSOT" "Yellow"
                Save-Log "Skipping append (use -Force to override). Running verify only..." "Yellow"
            }
        } else {
            Invoke-Append
        }
        Invoke-Verify -Python $Python
    }

    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host " DONE · VIA SSOT v22 Synonyms APPENDED & VERIFIED" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ("[SSOT]    " + $script:SSOT_FILE) -ForegroundColor Green
    if (Test-Path -LiteralPath $script:BAK_FILE) {
        Write-Host ("[BACKUP]  " + $script:BAK_FILE) -ForegroundColor Green
    }
    Write-Host "PowerShell session remains open." -ForegroundColor Cyan
} catch {
    Write-Host ""
    Write-Host ("[FATAL] " + $_.Exception.Message) -ForegroundColor Red
    if ($_.ScriptStackTrace) {
        Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
    }
    Write-Host "PowerShell session remains open." -ForegroundColor Yellow
}
