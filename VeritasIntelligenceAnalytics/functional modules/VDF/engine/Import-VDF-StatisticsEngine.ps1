#requires -Version 7.0

# =============================================================================
# VDF · IMPORT STATISTICS ENGINE (VRN_TAEngine_v01) INTO VDF
# ADJ-first price layer · formula statistics · TW10Y/US10Y · ^TWII/^GSPC/NVDA
# Fixes the attached flow: child invocation via ProcessStartInfo + ArgumentList
# (never Start-Process for child tools -> that was the EXIT_64 root cause).
# =============================================================================

# ---- PARAMETERS (all on top; $script: scope) --------------------------------

# ===== [VIA:PS-ACCEL:v0100] PS 20 加速器橋(批255 全樹導入;graceful 缺席零影響) =====
try {
    $VIAPSAccelProbe = $PSScriptRoot
    while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) {
        $VIAPSAccelMod = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"
        if (Test-Path $VIAPSAccelMod) { . $VIAPSAccelMod; break }
        $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent
    }
} catch { }
# ===== [VIA:PS-ACCEL:END] =====
$script:RunId = "RUN_{0}_VDF_ENGINE_IMPORT_v0100" -f (Get-Date -Format "yyyyMMdd_HHmmss")

$script:ViaRoot = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics"
$script:VdfDir = Join-Path $script:ViaRoot "functional modules\VDF"

$script:SupportiveDirCanonical = Join-Path $script:ViaRoot "supportive modules"
$script:SupportiveDirAltSpaces = Join-Path $script:ViaRoot "supportive   modules"
$script:FunctionalDir = Join-Path $script:ViaRoot "functional modules"

$script:EngineIntegrationDir = Join-Path $script:VdfDir "_vdf_engine_integration"
$script:RegistryDir = Join-Path $script:VdfDir "_vdf_registry"
$script:InputDir = Join-Path $script:VdfDir "_vdf_inputs"
$script:LogDir = Join-Path $script:VdfDir "_vdf_logs\$script:RunId"
$script:ReportDir = Join-Path $script:VdfDir "_vdf_reports\engine_import"

$script:EngineFileName = "VRN_TAEngine_v01.py"
$script:PriceHelperFileName = "SUP_MDL630_PriceFetch.py"

$script:RegistryJson = Join-Path $script:RegistryDir "VDF_Engine_Registry.json"
$script:RegistryCsv = Join-Path $script:RegistryDir "VDF_Engine_Registry.csv"
$script:EngineConfigJson = Join-Path $script:EngineIntegrationDir "VDF_Engine_Config.json"
$script:PriceHelperPath = Join-Path $script:EngineIntegrationDir $script:PriceHelperFileName
$script:ActivePointerJson = Join-Path $script:EngineIntegrationDir "VDF_Engine_Import_ActivePointer.json"
$script:ReportHtml = Join-Path $script:ReportDir "VDF_Engine_Import_Report.html"
$script:SummaryJson = Join-Path $script:LogDir "VDF_Engine_Import_Summary.json"
$script:LogFile = Join-Path $script:LogDir "VDF_Engine_Import.log"

# Engine configuration requested by Tony (append-only / union semantics)
$script:PriceFetchPriority = @("ADJ_CLOSE", "CLOSE")
$script:StatisticsMode = "FORMULA"
$script:StatWindows = @(20, 60, 120)
$script:RiskFreeRates = @("TW10Y", "US10Y")
$script:Benchmarks = @("^TWII", "^GSPC", "NVDA")

# Python interpreter probe candidates (Exe + leading args)
$script:PythonCandidates = @(
    [ordered]@{ exe = "python"; pre = @() },
    [ordered]@{ exe = "py"; pre = @("-3.13") },
    [ordered]@{ exe = "py"; pre = @("-3.12") },
    [ordered]@{ exe = "python3"; pre = @() }
)
$script:PythonExe = $null
$script:PythonPre = @()

# Policy
$script:PolicyAppendOnly = $true
$script:PolicyNoDelete = $true
$script:PolicyNoOverwriteEngine = $true
$script:ChildTimeoutSeconds = 120
$script:EnableOpenHtmlReport = $true

$script:Utf8NoBom = [System.Text.UTF8Encoding]::new($false)

# ---- BASIC UTILITIES --------------------------------------------------------

function New-VdfDirectory {
    param(
        [string]$Path
    )
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function Write-VdfText {
    param(
        [string]$Path,
        [string]$Content
    )
    $dir = Split-Path -Parent $Path
    New-VdfDirectory -Path $dir
    [System.IO.File]::WriteAllText($Path, $Content, $script:Utf8NoBom)
}

function Write-VdfLine {
    param(
        [string]$Level,
        [string]$Message
    )
    $ts = Get-Date -Format "HH:mm:ss.fff"
    $line = "[{0}] [{1}] {2}" -f $ts, $Level, $Message
    switch ($Level) {
        "OK" {
            Write-Host $line -ForegroundColor Green
        }
        "WARN" {
            Write-Host $line -ForegroundColor Yellow
        }
        "FAIL" {
            Write-Host $line -ForegroundColor Red
        }
        "RUN" {
            Write-Host $line -ForegroundColor Cyan
        }
        default {
            Write-Host $line
        }
    }
    if (Test-Path -LiteralPath $script:LogDir) {
        Add-Content -LiteralPath $script:LogFile -Value $line -Encoding UTF8
    }
}

function Show-VdfProgress {
    param(
        [int]$Step,
        [int]$Total,
        [string]$Status
    )
    $pct = [math]::Round(($Step / [math]::Max($Total, 1)) * 100, 0)
    Write-Progress -Id 1 -Activity "VDF Statistics Engine Import" -Status $Status -PercentComplete $pct
    Write-VdfLine "RUN" ("[{0}/{1}] {2}" -f $Step, $Total, $Status)
}

function Write-VdfJson {
    param(
        [object]$Object,
        [string]$Path,
        [int]$Depth = 40
    )
    $json = $Object | ConvertTo-Json -Depth $Depth
    Write-VdfText -Path $Path -Content $json
}

function Get-VdfSha12 {
    param(
        [string]$Path
    )
    if ([string]::IsNullOrEmpty($Path)) {
        return ""
    }
    if (-not (Test-Path -LiteralPath $Path)) {
        return ""
    }
    try {
        $hash = Get-FileHash -LiteralPath $Path -Algorithm SHA256
        return $hash.Hash.Substring(0, 12).ToLower()
    } catch {
        return ""
    }
}

function Get-VdfUnion {
    param(
        [object[]]$First,
        [object[]]$Second
    )
    $seen = [System.Collections.Generic.List[string]]::new()
    $out = @()
    foreach ($item in @($First) + @($Second)) {
        if ($null -eq $item) {
            continue
        }
        $key = [string]$item
        if (-not $seen.Contains($key)) {
            $seen.Add($key)
            $out += $item
        }
    }
    return $out
}

# ---- PATH RESOLUTION --------------------------------------------------------

function Resolve-VdfFile {
    param(
        [string]$FileName
    )
    $searchRoots = @(
        $script:VdfDir,
        $script:FunctionalDir,
        $script:SupportiveDirCanonical,
        $script:SupportiveDirAltSpaces,
        $script:ViaRoot
    ) | Select-Object -Unique

    foreach ($root in $searchRoots) {
        $direct = Join-Path $root $FileName
        if (Test-Path -LiteralPath $direct) {
            return (Resolve-Path -LiteralPath $direct).Path
        }
    }
    foreach ($root in $searchRoots) {
        if (-not (Test-Path -LiteralPath $root)) {
            continue
        }
        try {
            $found = Get-ChildItem -LiteralPath $root -Filter $FileName -Recurse -File -ErrorAction SilentlyContinue |
                Select-Object -First 1
            if ($found) {
                return $found.FullName
            }
        } catch {
            continue
        }
    }
    return ""
}

# ---- NO-HANG PYTHON INVOCATION (ProcessStartInfo + ArgumentList.Add) --------
# This is the corrected pattern. The attached flow used Start-Process with an
# argument array; paths containing spaces ("supportive modules") were split,
# pwsh could not find the -File target, and every attempt returned EXIT_64.

function Invoke-PythonNoHang {
    param(
        [string]$Exe,
        [string[]]$PreArgs,
        [string[]]$CallArgs,
        [string]$Label,
        [int]$TimeoutSeconds
    )

    $psi = [System.Diagnostics.ProcessStartInfo]::new()
    $psi.FileName = $Exe
    foreach ($a in $PreArgs) {
        $psi.ArgumentList.Add($a)
    }
    foreach ($a in $CallArgs) {
        $psi.ArgumentList.Add($a)
    }
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    if (Test-Path -LiteralPath $script:EngineIntegrationDir) {
        $psi.WorkingDirectory = $script:EngineIntegrationDir
    }

    $proc = [System.Diagnostics.Process]::new()
    $proc.StartInfo = $psi

    try {
        $null = $proc.Start()
    } catch {
        return [ordered]@{
            label = $Label
            status = "LAUNCH_FAIL"
            exit_code = $null
            pid = $null
            stdout = ""
            stderr = $_.Exception.Message
        }
    }

    $outTask = $proc.StandardOutput.ReadToEndAsync()
    $errTask = $proc.StandardError.ReadToEndAsync()
    $exited = $proc.WaitForExit($TimeoutSeconds * 1000)

    if (-not $exited) {
        # No-kill policy: record PID and continue.
        Write-VdfLine "WARN" ("{0} timeout; child not killed. PID={1}" -f $Label, $proc.Id)
        return [ordered]@{
            label = $Label
            status = "TIMEOUT_RUNNING"
            exit_code = $null
            pid = $proc.Id
            stdout = ""
            stderr = ""
        }
    }

    $proc.WaitForExit()
    $stdout = $outTask.GetAwaiter().GetResult()
    $stderr = $errTask.GetAwaiter().GetResult()
    $code = $proc.ExitCode

    $status = "EXIT_$code"
    if ($code -eq 0) {
        $status = "OK"
    }
    return [ordered]@{
        label = $Label
        status = $status
        exit_code = $code
        pid = $proc.Id
        stdout = $stdout
        stderr = $stderr
    }
}

function Resolve-PythonInterpreter {
    foreach ($cand in $script:PythonCandidates) {
        $probe = Invoke-PythonNoHang `
            -Exe $cand.exe `
            -PreArgs ([string[]]$cand.pre) `
            -CallArgs @("-c", "print('VDFPY_OK')") `
            -Label ("probe:" + $cand.exe + " " + ($cand.pre -join " ")) `
            -TimeoutSeconds 20
        $fingerprint = $false
        if ($null -ne $probe.stdout) {
            $fingerprint = ([string]$probe.stdout).Contains("VDFPY_OK")
        }
        if ($probe.status -eq "OK" -and $fingerprint) {
            $script:PythonExe = $cand.exe
            $script:PythonPre = [string[]]$cand.pre
            Write-VdfLine "OK" ("Python interpreter: {0} {1}" -f $cand.exe, ($cand.pre -join " "))
            return $true
        }
    }
    Write-VdfLine "FAIL" "No working Python interpreter found (tried python / py -3.13 / py -3.12 / python3)."
    return $false
}

function Test-PythonParse {
    param(
        [string]$PyPath,
        [string]$Label
    )
    if (-not (Test-Path -LiteralPath $PyPath)) {
        return [ordered]@{ label = $Label; status = "MISSING"; exit_code = $null; stderr = "file not found" }
    }
    return Invoke-PythonNoHang `
        -Exe $script:PythonExe `
        -PreArgs $script:PythonPre `
        -CallArgs @("-m", "py_compile", $PyPath) `
        -Label $Label `
        -TimeoutSeconds $script:ChildTimeoutSeconds
}

# ---- PRICE HELPER (ADJ-first) WRITE + VALIDATE ------------------------------

function Write-PriceHelper {
    $py = @'
# -*- coding: utf-8 -*-
"""VDF price layer (ADJ-first then regular). See VDF_Engine_Config.json."""
from __future__ import annotations
import sys, json

PRICE_PRIORITY = ["Adj Close", "Close"]
YF_AUTO_ADJUST = False
COLUMN_ALIASES = {
    "Date": ["Date", "date", "datetime", "日期"],
    "Open": ["Open", "open", "開盤價", "o"],
    "High": ["High", "high", "最高價", "h"],
    "Low": ["Low", "low", "最低價", "l"],
    "Close": ["Close", "close", "收盤價", "收盤", "c"],
    "Adj Close": ["Adj Close", "adj_close", "還原收盤價", "復權收盤", "adjclose"],
    "Volume": ["Volume", "volume", "成交量", "成交股數", "vol"],
}
SOURCE_ORDER = ["yfinance", "stooq"]


def normalize_columns(df):
    rename = {}
    lower_map = {str(c).strip().lower(): c for c in df.columns}
    for std, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            k = alias.strip().lower()
            if k in lower_map:
                rename[lower_map[k]] = std
                break
    return df.rename(columns=rename)


def select_price_series(df):
    chosen = None
    for col in PRICE_PRIORITY:
        if col in df.columns and df[col].notna().any():
            chosen = col
            break
    out = df.copy()
    if chosen is not None:
        out["PRICE"] = out[chosen]
        out["PRICE_SOURCE"] = chosen
        out["RAW_CLOSE"] = out["Close"] if "Close" in out.columns else out[chosen]
    return chosen, out


def _fetch_yfinance(ticker, start, end):
    import yfinance as yf
    raw = yf.download(ticker, start=start, end=end, auto_adjust=YF_AUTO_ADJUST, progress=False)
    if raw is None or len(raw) == 0:
        return None
    raw = raw.reset_index()
    if hasattr(raw.columns, "nlevels") and raw.columns.nlevels > 1:
        raw.columns = [c[0] if isinstance(c, tuple) else c for c in raw.columns]
    return raw


def _fetch_stooq(ticker, start, end):
    import pandas as pd
    from urllib.request import urlopen
    from io import StringIO
    url = "https://stooq.com/q/d/l/?s={0}&i=d".format(ticker.lower())
    with urlopen(url, timeout=20) as resp:
        text = resp.read().decode("utf-8", errors="ignore")
    df = pd.read_csv(StringIO(text))
    return df if len(df) > 0 else None


def fetch_prices(ticker, start=None, end=None, sources=None):
    use = sources if sources else SOURCE_ORDER
    last_err = None
    for src in use:
        try:
            raw = _fetch_yfinance(ticker, start, end) if src == "yfinance" else (
                _fetch_stooq(ticker, start, end) if src == "stooq" else None)
            if raw is None:
                continue
            ps, out = select_price_series(normalize_columns(raw))
            if ps is None:
                continue
            out.attrs["ticker"] = ticker
            out.attrs["fetch_source"] = src
            out.attrs["price_source"] = ps
            return out
        except Exception as exc:
            last_err = "{0}: {1}".format(src, exc)
            continue
    if last_err is not None:
        sys.stderr.write("fetch_prices failed: {0}\n".format(last_err))
    return None


def to_parquet(df, path):
    df.to_parquet(path, index=False)
    return path


def _selftest():
    import pandas as pd
    passed = 0
    total = 0

    def check(name, cond):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
            print("  PASS  " + name)
        else:
            print("  FAIL  " + name)

    n1 = normalize_columns(pd.DataFrame({
        "date": ["2026-01-01", "2026-01-02"], "open": [100.0, 101.0],
        "high": [102.0, 103.0], "low": [99.0, 100.0], "close": [101.0, 102.0],
        "adj_close": [90.0, 91.0], "volume": [1000, 1200]}))
    s1, o1 = select_price_series(n1)
    check("ADJ-first selects Adj Close", s1 == "Adj Close")
    check("PRICE equals Adj Close", list(o1["PRICE"]) == [90.0, 91.0])
    check("RAW_CLOSE keeps Close", list(o1["RAW_CLOSE"]) == [101.0, 102.0])
    n2 = normalize_columns(pd.DataFrame({"Date": ["2026-01-01"], "Close": [55.0], "Volume": [10]}))
    s2, o2 = select_price_series(n2)
    check("fallback to Close", s2 == "Close")
    check("PRICE equals Close", list(o2["PRICE"]) == [55.0])
    n4 = normalize_columns(pd.DataFrame({"Date": ["2026-01-01"], "Volume": [1]}))
    s4, _ = select_price_series(n4)
    check("no price -> None", s4 is None)
    print("SELFTEST {0}/{1} PASS".format(passed, total))
    print("SELFTEST_JSON " + json.dumps({"passed": passed, "total": total, "ok": passed == total}))
    return 0 if passed == total else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        raise SystemExit(_selftest())
    print("vdf_price_fetch ready. PRICE_PRIORITY={0}".format(PRICE_PRIORITY))
'@
    Write-VdfText -Path $script:PriceHelperPath -Content $py
    Write-VdfLine "OK" ("Price helper written: {0}" -f $script:PriceHelperPath)
}

# ---- ENGINE CONFIG (append-only / union) ------------------------------------

function Write-EngineConfig {
    param(
        [string]$EnginePath
    )

    $existing = [ordered]@{}
    if (Test-Path -LiteralPath $script:EngineConfigJson) {
        try {
            $raw = Get-Content -LiteralPath $script:EngineConfigJson -Raw -Encoding UTF8
            $obj = $raw | ConvertFrom-Json
            foreach ($p in $obj.PSObject.Properties) {
                $existing[$p.Name] = $p.Value
            }
            Write-VdfLine "OK" "Existing engine config loaded; merging append-only."
        } catch {
            Write-VdfLine "WARN" "Existing engine config unreadable; writing fresh."
        }
    }

    $benchPrev = @()
    if ($existing.Contains("benchmarks")) {
        $benchPrev = @($existing["benchmarks"])
    }
    $rfPrev = @()
    if ($existing.Contains("risk_free_rates")) {
        $rfPrev = @($existing["risk_free_rates"])
    }

    $config = [ordered]@{
        schema_version = "VDF_Engine_Config_v0100"
        generated_at = (Get-Date).ToString("s")
        run_id = $script:RunId
        engine_file = $script:EngineFileName
        engine_path = $EnginePath
        price_layer = [ordered]@{
            helper = $script:PriceHelperFileName
            helper_path = $script:PriceHelperPath
            fetch_priority = $script:PriceFetchPriority
            note = "ADJ-first: Adj Close drives returns/indicators; Close kept as RAW_CLOSE for display."
        }
        statistics = [ordered]@{
            mode = $script:StatisticsMode
            note = "Formula-based (not TA-Lib): STDEV/VAR/BETA/CORREL/SHARPE/SORTINO."
            windows = $script:StatWindows
            metrics = @("STDEV", "VAR", "BETA", "CORREL", "SHARPE", "SORTINO")
        }
        risk_free_rates = (Get-VdfUnion -First $rfPrev -Second $script:RiskFreeRates)
        benchmarks = (Get-VdfUnion -First $benchPrev -Second $script:Benchmarks)
        policy = [ordered]@{
            append_only = $script:PolicyAppendOnly
            no_delete = $script:PolicyNoDelete
            no_overwrite_engine_internals = $script:PolicyNoOverwriteEngine
        }
    }

    # preserve any unmanaged keys from existing
    foreach ($k in $existing.Keys) {
        if (-not $config.Contains($k)) {
            $config[$k] = $existing[$k]
        }
    }

    Write-VdfJson -Object $config -Path $script:EngineConfigJson -Depth 40
    Write-VdfLine "OK" ("Engine config written: {0}" -f $script:EngineConfigJson)
    return $config
}

# ---- REGISTRY ---------------------------------------------------------------

function Write-EngineRegistry {
    param(
        [string]$EnginePath,
        [object]$EngineParse,
        [object]$HelperParse
    )

    $engineExists = (-not [string]::IsNullOrEmpty($EnginePath)) -and (Test-Path -LiteralPath $EnginePath)
    $rows = @()

    $rows += [pscustomobject]@{
        order = 1
        component = $script:EngineFileName
        role = "statistics_engine"
        path = $EnginePath
        exists = $engineExists
        sha12 = Get-VdfSha12 -Path $EnginePath
        size_kb = if ($engineExists) { [math]::Round(((Get-Item -LiteralPath $EnginePath).Length / 1KB), 2) } else { 0 }
        parse_status = $EngineParse.status
    }
    $rows += [pscustomobject]@{
        order = 2
        component = $script:PriceHelperFileName
        role = "price_layer_adj_first"
        path = $script:PriceHelperPath
        exists = (Test-Path -LiteralPath $script:PriceHelperPath)
        sha12 = Get-VdfSha12 -Path $script:PriceHelperPath
        size_kb = if (Test-Path -LiteralPath $script:PriceHelperPath) { [math]::Round(((Get-Item -LiteralPath $script:PriceHelperPath).Length / 1KB), 2) } else { 0 }
        parse_status = $HelperParse.status
    }
    $rows += [pscustomobject]@{
        order = 3
        component = "VDF_Engine_Config.json"
        role = "engine_config"
        path = $script:EngineConfigJson
        exists = (Test-Path -LiteralPath $script:EngineConfigJson)
        sha12 = Get-VdfSha12 -Path $script:EngineConfigJson
        size_kb = if (Test-Path -LiteralPath $script:EngineConfigJson) { [math]::Round(((Get-Item -LiteralPath $script:EngineConfigJson).Length / 1KB), 2) } else { 0 }
        parse_status = "config"
    }

    $rows | Export-Csv -LiteralPath $script:RegistryCsv -NoTypeInformation -Encoding UTF8

    $registry = [ordered]@{
        schema_version = "VDF_Engine_Registry_v0100"
        generated_at = (Get-Date).ToString("s")
        run_id = $script:RunId
        rows = $rows
    }
    Write-VdfJson -Object $registry -Path $script:RegistryJson -Depth 40
    Write-VdfLine "OK" ("Registry written: {0}" -f $script:RegistryJson)
    return $rows
}

# ---- HTML REPORT (Visual Lock; single-quoted here-string + .Replace) --------

function Write-EngineImportReport {
    param(
        [array]$Rows,
        [object]$Config,
        [object]$EngineSelftest
    )

    $rowsHtml = ""
    foreach ($row in $Rows) {
        $rowsHtml += "<tr><td>" + $row.order + "</td><td>" +
            [System.Net.WebUtility]::HtmlEncode([string]$row.component) + "</td><td>" +
            [System.Net.WebUtility]::HtmlEncode([string]$row.role) + "</td><td>" +
            [string]$row.exists + "</td><td>" + [string]$row.sha12 + "</td><td>" +
            [System.Net.WebUtility]::HtmlEncode([string]$row.parse_status) + "</td><td>" +
            [System.Net.WebUtility]::HtmlEncode([string]$row.path) + "</td></tr>`n"
    }

    $benchHtml = [System.Net.WebUtility]::HtmlEncode(($Config.benchmarks -join " · "))
    $rfHtml = [System.Net.WebUtility]::HtmlEncode(($Config.risk_free_rates -join " · "))
    $priceHtml = [System.Net.WebUtility]::HtmlEncode(($Config.price_layer.fetch_priority -join " → "))
    $selftestHtml = [System.Net.WebUtility]::HtmlEncode(($EngineSelftest | ConvertTo-Json -Depth 10))

    $template = @'
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>VDF Statistics Engine Import</title>
<style>
:root{ --blue:#4c78a8; --grey:#9c9890; --teal:#439a9a; --up:#c96b5a; --down:#5a9e6f; }
body{ margin:32px; background:#fbfcfd; color:#1f2a30;
  font-family:"DM Sans","Noto Sans TC",Arial,sans-serif; }
h1{ font-family:"Syne","DM Sans",sans-serif; color:var(--blue); font-weight:700; }
h2{ font-family:"Syne","DM Sans",sans-serif; color:var(--teal); font-weight:600; }
.card{ background:#fff; border:1px solid #e3e8ec; border-radius:16px;
  padding:18px 22px; margin:18px 0; box-shadow:0 10px 26px rgba(31,42,48,.05); }
.kpi{ display:grid; grid-template-columns:repeat(4,minmax(170px,1fr)); gap:14px; }
.kpi div{ background:#fff; border-top:4px solid var(--blue); border-radius:14px; padding:16px; }
.kpi.teal div{ border-top-color:var(--teal); }
.big{ font-size:26px; color:var(--grey); font-family:"DM Mono",monospace; }
.mono{ font-family:"DM Mono",monospace; }
table{ width:100%; border-collapse:collapse; background:#fff; }
th,td{ border-bottom:1px solid #eef2f4; padding:9px 10px; text-align:left;
  vertical-align:top; font-size:13px; }
th{ color:var(--blue); background:#f4f7f9; font-family:"DM Mono",monospace; }
td{ font-family:"DM Mono",monospace; }
pre{ white-space:pre-wrap; background:#f5f8f9; padding:14px; border-radius:12px;
  font-family:"DM Mono",monospace; font-size:12px; }
.tag{ display:inline-block; padding:2px 10px; border-radius:999px; font-size:12px;
  background:#eef4f3; color:var(--teal); margin-right:6px; }
</style>
</head>
<body>
<h1>VDF · Statistics Engine Import</h1>
<div class="kpi">
<div><b>Status</b><br><span class="big">READY</span></div>
<div><b>Run ID</b><br><span class="mono">@@RUNID@@</span></div>
<div><b>Components</b><br><span class="big">@@COUNT@@</span></div>
<div><b>Policy</b><br><span>Append-only / No-delete</span></div>
</div>

<div class="card">
<h2>Engine Configuration</h2>
<p><span class="tag">Price</span> @@PRICE@@</p>
<p><span class="tag">Statistics</span> FORMULA · STDEV / VAR / BETA / CORREL / SHARPE / SORTINO · windows 20/60/120</p>
<p><span class="tag">Risk-free</span> @@RF@@</p>
<p><span class="tag">Benchmark</span> @@BENCH@@</p>
</div>

<div class="card">
<h2>Component Registry</h2>
<table>
<thead><tr><th>#</th><th>Component</th><th>Role</th><th>Exists</th><th>SHA12</th><th>Parse</th><th>Path</th></tr></thead>
<tbody>
@@ROWS@@
</tbody>
</table>
</div>

<div class="card">
<h2>Engine Selftest</h2>
<pre>@@SELFTEST@@</pre>
</div>

<div class="card">
<h2>Output Paths</h2>
<pre>
Engine Config : @@CONFIGPATH@@
Price Helper  : @@HELPERPATH@@
Registry JSON : @@REGJSON@@
Registry CSV  : @@REGCSV@@
Pointer JSON  : @@POINTER@@
Summary JSON  : @@SUMMARY@@
Report HTML   : @@REPORT@@
</pre>
</div>
</body>
</html>
'@

    $html = $template.
        Replace('@@RUNID@@', [System.Net.WebUtility]::HtmlEncode($script:RunId)).
        Replace('@@COUNT@@', [string]$Rows.Count).
        Replace('@@PRICE@@', $priceHtml).
        Replace('@@RF@@', $rfHtml).
        Replace('@@BENCH@@', $benchHtml).
        Replace('@@ROWS@@', $rowsHtml).
        Replace('@@SELFTEST@@', $selftestHtml).
        Replace('@@CONFIGPATH@@', [System.Net.WebUtility]::HtmlEncode($script:EngineConfigJson)).
        Replace('@@HELPERPATH@@', [System.Net.WebUtility]::HtmlEncode($script:PriceHelperPath)).
        Replace('@@REGJSON@@', [System.Net.WebUtility]::HtmlEncode($script:RegistryJson)).
        Replace('@@REGCSV@@', [System.Net.WebUtility]::HtmlEncode($script:RegistryCsv)).
        Replace('@@POINTER@@', [System.Net.WebUtility]::HtmlEncode($script:ActivePointerJson)).
        Replace('@@SUMMARY@@', [System.Net.WebUtility]::HtmlEncode($script:SummaryJson)).
        Replace('@@REPORT@@', [System.Net.WebUtility]::HtmlEncode($script:ReportHtml))

    Write-VdfText -Path $script:ReportHtml -Content $html
    Write-VdfLine "OK" ("Report written: {0}" -f $script:ReportHtml)
}

# ---- MAIN -------------------------------------------------------------------

function Invoke-EngineImport {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "VDF · IMPORT STATISTICS ENGINE (ADJ-first / FORMULA stats / TW10Y-US10Y)" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan

    Show-VdfProgress -Step 1 -Total 8 -Status "Prepare directories"
    foreach ($dir in @($script:VdfDir, $script:EngineIntegrationDir, $script:RegistryDir, $script:InputDir, $script:LogDir, $script:ReportDir)) {
        New-VdfDirectory -Path $dir
    }

    Show-VdfProgress -Step 2 -Total 8 -Status "Resolve Python interpreter"
    $hasPython = Resolve-PythonInterpreter

    Show-VdfProgress -Step 3 -Total 8 -Status "Resolve engine file"
    $enginePath = Resolve-VdfFile -FileName $script:EngineFileName
    if ($enginePath -ne "") {
        Write-VdfLine "OK" ("Engine found: {0}" -f $enginePath)
    } else {
        Write-VdfLine "WARN" ("Engine not found: {0} (config still written; drop the file under VDF and re-run)" -f $script:EngineFileName)
    }

    Show-VdfProgress -Step 4 -Total 8 -Status "Write ADJ-first price helper"
    Write-PriceHelper

    Show-VdfProgress -Step 5 -Total 8 -Status "Validate (py_compile) engine + helper"
    $engineParse = [ordered]@{ label = "engine_parse"; status = "SKIPPED_NO_PYTHON"; exit_code = $null; stderr = "" }
    $helperParse = [ordered]@{ label = "helper_parse"; status = "SKIPPED_NO_PYTHON"; exit_code = $null; stderr = "" }
    if ($hasPython) {
        if ($enginePath -ne "") {
            $engineParse = Test-PythonParse -PyPath $enginePath -Label "engine_parse"
            if ($engineParse.status -eq "OK") {
                Write-VdfLine "OK" "Engine py_compile OK"
            } else {
                Write-VdfLine "WARN" ("Engine py_compile {0}: {1}" -f $engineParse.status, $engineParse.stderr)
            }
        } else {
            $engineParse = [ordered]@{ label = "engine_parse"; status = "ENGINE_MISSING"; exit_code = $null; stderr = "" }
        }
        $helperParse = Test-PythonParse -PyPath $script:PriceHelperPath -Label "helper_parse"
        if ($helperParse.status -eq "OK") {
            Write-VdfLine "OK" "Helper py_compile OK"
        } else {
            Write-VdfLine "WARN" ("Helper py_compile {0}: {1}" -f $helperParse.status, $helperParse.stderr)
        }
    }

    Show-VdfProgress -Step 6 -Total 8 -Status "Write engine config + registry"
    $config = Write-EngineConfig -EnginePath $enginePath
    $rows = Write-EngineRegistry -EnginePath $enginePath -EngineParse $engineParse -HelperParse $helperParse

    Show-VdfProgress -Step 7 -Total 8 -Status "Run helper selftest (offline)"
    $helperSelftest = [ordered]@{ label = "helper_selftest"; status = "SKIPPED_NO_PYTHON"; stdout = ""; stderr = "" }
    if ($hasPython -and (Test-Path -LiteralPath $script:PriceHelperPath)) {
        $helperSelftest = Invoke-PythonNoHang `
            -Exe $script:PythonExe `
            -PreArgs $script:PythonPre `
            -CallArgs @($script:PriceHelperPath, "--selftest") `
            -Label "helper_selftest" `
            -TimeoutSeconds $script:ChildTimeoutSeconds
        if ($helperSelftest.status -eq "OK") {
            Write-VdfLine "OK" "Helper selftest PASS"
        } else {
            Write-VdfLine "WARN" ("Helper selftest {0} (pandas may be missing in selected env): {1}" -f $helperSelftest.status, $helperSelftest.stderr)
        }
    }

    Show-VdfProgress -Step 8 -Total 8 -Status "Write pointer / summary / report"

    $pointer = [ordered]@{
        schema_version = "VDF_Engine_Import_ActivePointer_v0100"
        generated_at = (Get-Date).ToString("s")
        run_id = $script:RunId
        status = "VDF_ENGINE_IMPORT_READY"
        engine_path = $enginePath
        engine_config_json = $script:EngineConfigJson
        price_helper_path = $script:PriceHelperPath
        registry_json = $script:RegistryJson
        report_html = $script:ReportHtml
    }
    Write-VdfJson -Object $pointer -Path $script:ActivePointerJson -Depth 30

    $engineParseStatus = "n/a"
    if ($null -ne $engineParse) {
        $engineParseStatus = [string]$engineParse.status
    }

    $risk = "LOW"
    $status = "VDF_ENGINE_IMPORT_READY"
    if ($enginePath -eq "") {
        $risk = "MEDIUM"
        $status = "VDF_ENGINE_IMPORT_READY_ENGINE_MISSING"
    } elseif ($engineParseStatus -ne "OK" -and $engineParseStatus -ne "SKIPPED_NO_PYTHON") {
        $risk = "MEDIUM"
        $status = "VDF_ENGINE_IMPORT_READY_PARSE_REVIEW"
    }

    $summary = [ordered]@{
        schema_version = "VDF_Engine_Import_Summary_v0100"
        generated_at = (Get-Date).ToString("s")
        run_id = $script:RunId
        status = $status
        risk = $risk
        python = ("{0} {1}" -f $script:PythonExe, ($script:PythonPre -join " "))
        engine_path = $enginePath
        engine_parse = $engineParse
        helper_parse = $helperParse
        helper_selftest_status = $helperSelftest.status
        config = $config
        rows = $rows
        outputs = [ordered]@{
            engine_config_json = $script:EngineConfigJson
            price_helper_path = $script:PriceHelperPath
            registry_json = $script:RegistryJson
            registry_csv = $script:RegistryCsv
            active_pointer_json = $script:ActivePointerJson
            report_html = $script:ReportHtml
        }
    }
    Write-VdfJson -Object $summary -Path $script:SummaryJson -Depth 60

    Write-EngineImportReport -Rows $rows -Config $config -EngineSelftest $helperSelftest

    Write-Progress -Id 1 -Activity "VDF Statistics Engine Import" -Completed

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "VDF ENGINE IMPORT COMPLETE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host ("Status        : {0}" -f $status)
    Write-Host ("Risk          : {0}" -f $risk)
    Write-Host ("Engine        : {0}" -f $enginePath)
    Write-Host ("Engine parse  : {0}" -f $engineParseStatus)
    Write-Host ("Price priority: {0}" -f ($script:PriceFetchPriority -join " -> "))
    Write-Host ("Risk-free     : {0}" -f ($config.risk_free_rates -join ", "))
    Write-Host ("Benchmarks    : {0}" -f ($config.benchmarks -join ", "))
    Write-Host ("Config JSON   : {0}" -f $script:EngineConfigJson)
    Write-Host ("Report HTML   : {0}" -f $script:ReportHtml)

    if ($script:EnableOpenHtmlReport -and (Test-Path -LiteralPath $script:ReportHtml)) {
        Start-Process $script:ReportHtml
    }

    Write-Host ""
    Write-Host "PowerShell remains open. No exit." -ForegroundColor Yellow
}

try {
    Invoke-EngineImport
} catch {
    Write-VdfLine "FAIL" $_.Exception.Message
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
    Write-Host ""
    Write-Host "PowerShell remains open. No exit." -ForegroundColor Yellow
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
