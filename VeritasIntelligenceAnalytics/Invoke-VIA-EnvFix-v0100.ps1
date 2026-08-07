#requires -Version 7.0
<#
Invoke-VIA-EnvFix v0100 — EnvManager 決策式無衝突安裝(Mega parquet/rich + FIS 依賴)
流程:[1] VIA_EnvManager plan-install 逐包決策(append-only 留痕,run-local 輸出)
     [2] NumPy 黃金律 constraints(>=1.24,<2.0;與 VIA_EnvManager_Deploy_VMT 同律)
     [3] py 基底一次性聯合安裝五包(pip 全域解衝突;only-if-needed 不動既有版本)
     [4] gatekeeper 後驗:pip check + import + 版本表
慣例:無 Read-Host、無 exit;失敗誠實標 FAIL 續行;輸出全部 run-local(VIA_Reports\envmgr_run)。
安裝目標=py 基底(bin\*.cmd 的實際執行器);受保護 venv(via_core 等)一律不碰。
#>
param([string[]]$Packages = @("duckdb", "rich", "scipy", "numpy", "pandas"))
$ErrorActionPreference = "Continue"
$VIA = $PSScriptRoot
$RunDir = Join-Path $VIA "VIA_Reports\envmgr_run"
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
Push-Location $RunDir
$Results = @()
try {
    Write-Host ("=" * 66) -ForegroundColor DarkCyan
    Write-Host "  VIA ENVFIX v0100  |  EnvManager 決策式無衝突安裝" -ForegroundColor Cyan
    Write-Host ("=" * 66) -ForegroundColor DarkCyan

    # [1] EnvManager 逐包決策(留痕 _via_envmanager_output;決策僅供稽核,不改變受保護 venv)
    $EnvMgr = Join-Path $VIA "supportive modules\VIA_EnvManager.py"
    foreach ($p in $Packages) {
        Write-Host ("[STATUS] EnvManager plan-install {0}" -f $p) -ForegroundColor Yellow
        $raw = & py $EnvMgr plan-install $p 2>&1 | Out-String
        $verdict = "(無法解析,原文見 run-local 輸出)"
        try {
            $j = $raw | ConvertFrom-Json
            $d = $j.decision
            $verdict = if ($d.approved) { "APPROVED -> env=$($d.target_env)" } else { "BLOCKED($($d.blocked_reason))" }
        } catch {}
        Write-Host ("         {0}" -f $verdict) -ForegroundColor DarkGray
        $Results += [pscustomobject]@{ 項目 = "決策 $p"; 結果 = $verdict }
    }

    # [2] NumPy 黃金律 constraints(防 numpy 2.x 漂移撞 pm4py/既有引擎)
    $Con = Join-Path $RunDir "via_constraints.txt"
    "numpy>=1.24,<2.0" | Set-Content -Path $Con -Encoding utf8
    Write-Host "[STATUS] 黃金律 constraints: numpy>=1.24,<2.0" -ForegroundColor Yellow

    # [3] 一次性聯合安裝(pip 對五包整體解依賴 = 無衝突;不升級既有滿足版)
    Write-Host "[STATUS] py 基底聯合安裝(only-if-needed)" -ForegroundColor Yellow
    & py -m pip install --upgrade-strategy only-if-needed -c $Con @Packages
    $installOK = ($LASTEXITCODE -eq 0)
    $Results += [pscustomobject]@{ 項目 = "聯合安裝"; 結果 = ($installOK ? "OK" : "FAIL") }

    # [4] gatekeeper 後驗:pip check(全環境相容性)+ import + 版本
    Write-Host "[STATUS] gatekeeper 後驗 pip check" -ForegroundColor Yellow
    & py -m pip check
    $Results += [pscustomobject]@{ 項目 = "pip check"; 結果 = (($LASTEXITCODE -eq 0) ? "OK" : "FAIL") }
    $verify = & py -c "import importlib;mods={'duckdb':'duckdb','rich':'rich','scipy':'scipy','numpy':'numpy','pandas':'pandas'};[print(k, getattr(importlib.import_module(v), '__version__', '?')) for k, v in mods.items()]" 2>&1 | Out-String
    Write-Host $verify -ForegroundColor DarkGray
    $importOK = ($LASTEXITCODE -eq 0)
    $Results += [pscustomobject]@{ 項目 = "import 驗證"; 結果 = ($importOK ? "OK" : "FAIL") }
    $npOK = & py -c "import numpy,sys;sys.exit(0 if numpy.__version__.startswith('1.') else 1)"
    $Results += [pscustomobject]@{ 項目 = "NumPy 黃金律(<2.0)"; 結果 = (($LASTEXITCODE -eq 0) ? "OK" : "FAIL") }
}
finally { Pop-Location }
Write-Host ""
$Results | Format-Table -AutoSize
$okN = ($Results | Where-Object { $_.結果 -like "OK*" -or $_.結果 -like "APPROVED*" }).Count
Write-Host ("[總結] {0}/{1} 項通過 · 決策/輸出留痕 VIA_Reports\envmgr_run(run-local 不入庫)" -f $okN, $Results.Count) -ForegroundColor Green
Write-Host "[後續] via-mega(parquet+rich 滿配)· via-fis(scipy 就緒)" -ForegroundColor DarkGray
