param([string]$Target)
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
try {
    if (-not (Test-Path -LiteralPath $Target)) {
        Write-Output "MISSING`t$Target"
        exit 8
    }
    $tokens = $null
    $errors = $null
    [System.Management.Automation.Language.Parser]::ParseFile($Target, [ref]$tokens, [ref]$errors) | Out-Null
    if ($null -ne $errors -and $errors.Count -gt 0) {
        foreach ($e in $errors) {
            $line = 0
            $column = 0
            try { $line = $e.Extent.StartLineNumber; $column = $e.Extent.StartColumnNumber } catch {}
            Write-Output ("PARSE_ERROR`t{0}`t{1}`t{2}" -f $line,$column,$e.Message)
        }
        exit 2
    }
    Write-Output "OK"
    exit 0
} catch {
    Write-Output ("PARSER_FATAL`t" + $_.Exception.Message)
    exit 20
}

