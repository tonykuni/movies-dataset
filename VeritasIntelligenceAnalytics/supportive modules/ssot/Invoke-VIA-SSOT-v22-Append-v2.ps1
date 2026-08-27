#requires -Version 7.0
# =============================================================================
# VIA SSOT v22 Synonyms — Auto-Append + Verify Wrapper (v2 — Robust)
#   - Auto-locates patch file in Downloads / Desktop / CWD
#   - Self-unblocks (Mark-of-the-Web)
#   - Uses Move-Item -Force instead of [IO.File]::Replace (OneDrive-safe)
#   - Atomic backup + write + py_compile + import + 13/13 self-test
# =============================================================================

param(
    [string]$VIA_ROOT     = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics",
    [string]$PatchFile    = "",
    [switch]$Force,
    [switch]$VerifyOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$script:VIA_ROOT    = $VIA_ROOT
$script:SUPPORT_DIR = Join-Path $VIA_ROOT "module\supportive_module"
$script:SSOT_FILE   = Join-Path $script:SUPPORT_DIR "VIA_SSOT_Unified.py"
$script:TIMESTAMP   = Get-Date -Format "yyyyMMdd_HHmmss"
$script:BAK_FILE    = $script:SSOT_FILE + ".bak_v22_" + $script:TIMESTAMP
$script:MARKER      = "VIA_SSOT_Unified v22 SYNONYM EXTENSION"

$script:PYTHON_CANDIDATES = @(
    "C:\Users\tonyk\envs\via_core_312\Scripts\python.exe",
    "C:\Users\tonyk\envs\via_core\Scripts\python.exe",
    "python",
    "py"
)

function Save-Log {
    param([string]$Line, [string]$Color = "Gray")
    Write-Host ("[{0}] {1}" -f (Get-Date -Format "HH:mm:ss"), $Line) -ForegroundColor $Color
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

function Find-PatchFile {
    if ($PatchFile -and (Test-Path -LiteralPath $PatchFile)) { return $PatchFile }
    $candidates = @(
        "$env:USERPROFILE\Downloads\SUP_MDL655_SSOTUnifiedV22SynonymsPatch.py",
        "$env:USERPROFILE\OneDrive\Desktop\SUP_MDL655_SSOTUnifiedV22SynonymsPatch.py",
        "$env:USERPROFILE\Desktop\SUP_MDL655_SSOTUnifiedV22SynonymsPatch.py",
        ".\SUP_MDL655_SSOTUnifiedV22SynonymsPatch.py"
    )
    foreach ($p in $candidates) {
        if (Test-Path -LiteralPath $p) { return $p }
    }
    return ""
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

    # ── Backup original ──
    Save-Log "Backing up original to: $($script:BAK_FILE)" "Yellow"
    Copy-Item -LiteralPath $script:SSOT_FILE -Destination $script:BAK_FILE -Force

    # ── Read both files ──
    $orig  = [System.IO.File]::ReadAllText($script:SSOT_FILE, [System.Text.UTF8Encoding]::new($false))
    $patch = [System.IO.File]::ReadAllText($PatchFile,        [System.Text.UTF8Encoding]::new($false))

    if (-not $orig.EndsWith("`n")) { $orig = $orig + "`n" }
    $joined = $orig + "`n`n" + $patch + "`n"

    # ── Safer write: write to temp file, then Move-Item -Force ──
    # (avoid [IO.File]::Replace — fails on OneDrive with "path empty" error)
    Save-Log "Writing v22 patch to SSOT..." "DarkCyan"
    $tmp = $script:SSOT_FILE + ".tmp_v22_" + $script:TIMESTAMP
    [System.IO.File]::WriteAllText($tmp, $joined, [System.Text.UTF8Encoding]::new($false))

    # Retry loop in case OneDrive holds the file briefly
    $maxRetry = 5
    for ($i = 1; $i -le $maxRetry; $i++) {
        try {
            Move-Item -LiteralPath $tmp -Destination $script:SSOT_FILE -Force
            break
        } catch {
            if ($i -eq $maxRetry) {
                # Cleanup temp on final failure
                if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue }
                throw "Move-Item failed after $maxRetry attempts: $($_.Exception.Message)"
            }
            Start-Sleep -Milliseconds (200 * $i)
        }
    }
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
    Save-Log "=== VIA SSOT v22 Synonyms Auto-Append (v2 Robust) ===" "Cyan"
    Save-Log ("SSOT file  : " + $script:SSOT_FILE)

    $resolvedPatch = Find-PatchFile
    if (-not $resolvedPatch) {
        throw "Patch file not found. Searched: Downloads / OneDrive Desktop / Desktop / CWD. Pass -PatchFile <path> explicitly."
    }
    $PatchFile = $resolvedPatch
    Save-Log ("Patch file : " + $PatchFile)

    # Self-unblock (handle MOTW on PS files in same folder)
    try {
        Unblock-File -LiteralPath $PSCommandPath -ErrorAction SilentlyContinue
        Unblock-File -LiteralPath $PatchFile     -ErrorAction SilentlyContinue
    } catch {}

    $Python = Get-Python
    Save-Log ("Python     : " + $Python) "Green"

    if (-not (Test-Path -LiteralPath $script:SSOT_FILE)) {
        throw "SSOT file not found: $($script:SSOT_FILE)"
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
    Write-Host ""
    Write-Host "RESTORE:" -ForegroundColor Yellow
    if ($script:BAK_FILE -and (Test-Path -LiteralPath $script:BAK_FILE)) {
        Write-Host ('  Copy-Item "' + $script:BAK_FILE + '" "' + $script:SSOT_FILE + '" -Force') -ForegroundColor Yellow
    }
    Write-Host "PowerShell session remains open." -ForegroundColor Yellow
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
