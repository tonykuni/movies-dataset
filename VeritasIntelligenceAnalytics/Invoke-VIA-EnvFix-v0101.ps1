#requires -Version 7.0
<#
Invoke-VIA-EnvFix v0101 — EnvManager 決策式無衝突安裝(v0100 版本前送)
v0101 修正(依操作員機實跑證據):
  [F1] 已就緒即不動:五依賴先 import 探測,已可用者一律跳過(v0100 在 numpy2/pandas3
       世代的 base 上強套 numpy<2.0 constraints 導致無解 FAIL——黃金律範圍錯置)
  [F2] NumPy 黃金律改為「範圍正確」:僅適用 vmt_pm venv(pm4py 世代,由
       VIA_EnvManager_Deploy_VMT.ps1 自帶 constraints);base 以引擎實證為準
       (Mega/FIS 已在 numpy 2.x 全綠/LOGIC PROVEN),此處只做資訊性顯示
  [F3] pip check 改「前後差分」:base 既有破損(torch/tokenizers 等)為存量雜訊,
       只有「本次新增的破損」才判 FAIL;存量誠實列數不列罪
慣例:無 Read-Host、無 exit;失敗誠實 FAIL 續行;輸出 run-local。回退=改跑 v0100。
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
    Write-Host "  VIA ENVFIX v0101  |  已就緒不動 · 黃金律範圍修正 · check 差分" -ForegroundColor Cyan
    Write-Host ("=" * 66) -ForegroundColor DarkCyan

    # [1] import 探測:已就緒者不動(唯一真正要件=引擎 import 得到)
    $missing = @()
    foreach ($p in $Packages) {
        & py -c "import $p" 2>$null
        if ($LASTEXITCODE -eq 0) {
            $v = (& py -c "import $p,importlib.metadata as m; print(m.version('$p'))" 2>$null)
            Write-Host ("[READY] {0} {1}" -f $p, $v) -ForegroundColor Green
            $Results += [pscustomobject]@{ 項目 = "依賴 $p"; 結果 = "READY $v" }
        } else {
            Write-Host ("[MISS ] {0}" -f $p) -ForegroundColor DarkYellow
            $missing += $p
        }
    }

    if ($missing.Count -eq 0) {
        Write-Host "[STATUS] 五依賴全就緒 — 無需安裝(v0100 的 FAIL 為黃金律範圍錯置,非依賴缺失)" -ForegroundColor Green
        $Results += [pscustomobject]@{ 項目 = "聯合安裝"; 結果 = "SKIP(全就緒)" }
    } else {
        # [2] EnvManager 決策留痕(僅對缺件)
        $EnvMgr = Join-Path $VIA "supportive modules\VIA_EnvManager.py"
        foreach ($p in $missing) {
            $raw = & py $EnvMgr plan-install $p 2>&1 | Out-String
            $verdict = "(見 run-local 輸出)"
            try { $d = ($raw | ConvertFrom-Json).decision
                  $verdict = if ($d.approved) { "APPROVED->$($d.target_env)" } else { "BLOCKED($($d.blocked_reason))" } } catch {}
            $Results += [pscustomobject]@{ 項目 = "決策 $p"; 結果 = $verdict }
        }
        # [3] pip check 基線(存量破損不列罪)
        $pre = @(& py -m pip check 2>&1 | Where-Object { $_ -match "requires|requirement" })
        Write-Host ("[STATUS] pip check 基線:存量破損 {0} 條(既有雜訊,非本次)" -f $pre.Count) -ForegroundColor DarkGray
        # [4] 只裝缺件;不帶 constraints(base 以既裝生態為準),不升級既有
        Write-Host ("[STATUS] 安裝缺件:{0}" -f ($missing -join ", ")) -ForegroundColor Yellow
        & py -m pip install --upgrade-strategy only-if-needed @missing
        $Results += [pscustomobject]@{ 項目 = "安裝缺件"; 結果 = (($LASTEXITCODE -eq 0) ? "OK" : "FAIL") }
        # [5] pip check 差分:只有新增破損才 FAIL
        $post = @(& py -m pip check 2>&1 | Where-Object { $_ -match "requires|requirement" })
        $new = @($post | Where-Object { $pre -notcontains $_ })
        if ($new.Count) { $new | ForEach-Object { Write-Host ("[NEW-BREAK] {0}" -f $_) -ForegroundColor Red } }
        $Results += [pscustomobject]@{ 項目 = "pip check 差分"; 結果 = ($new.Count -eq 0 ? "OK(存量 $($pre.Count) 條未增)" : "FAIL(+$($new.Count))") }
    }

    # [6] 最終 import 驗證 + NumPy 資訊行(黃金律僅 vmt_pm venv 適用)
    & py -c "import duckdb,rich,scipy,numpy,pandas" 2>$null
    $Results += [pscustomobject]@{ 項目 = "import 驗證(引擎要件)"; 結果 = (($LASTEXITCODE -eq 0) ? "OK" : "FAIL") }
    $np = (& py -c "import numpy;print(numpy.__version__)" 2>$null)
    Write-Host ("[INFO] base numpy {0}(引擎已於 2.x 實證全綠;numpy<2.0 黃金律僅適用 vmt_pm venv/pm4py)" -f $np) -ForegroundColor DarkGray
    $Results += [pscustomobject]@{ 項目 = "NumPy 世代"; 結果 = "INFO $np(base 無鎖;vmt_pm 另律)" }
}
finally { Pop-Location }
Write-Host ""
$Results | Format-Table -AutoSize
$bad = ($Results | Where-Object { $_.結果 -like "FAIL*" }).Count
Write-Host ($bad -eq 0 ? "[總結] 依賴層綠燈 — via-mega / via-fis / via-bridge 滿配可跑" : "[總結] 有 FAIL,見上表逐列") -ForegroundColor ($bad -eq 0 ? "Green" : "Red")

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
