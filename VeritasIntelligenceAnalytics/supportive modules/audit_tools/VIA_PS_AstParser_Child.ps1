param([string]$Target)
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

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
