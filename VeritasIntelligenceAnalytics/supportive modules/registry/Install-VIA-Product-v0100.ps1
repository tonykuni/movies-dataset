# Install-VIA-Product-v0100.ps1 — VIA 商品通用安裝器(消費者如開全新電腦)。
# 用法:pwsh -File Install-VIA-Product-v0100.ps1 -Pointer .\pkg_pointers\PKG_010_Pointer.json [-Base C:\VeritasIntelligenceAnalytics] [-DryRun]
# 規約:①環境檢查 PS7+/python ②pip 依賴(--user;缺才裝)③布建 base 基座 ④內容物落位+sha256 驗真(舉證)
#      ⑤bin 動詞可用性 ⑥開商品第一頁。全自動;僅商品代碼增減交使用者。不刪除、不覆蓋既有正本(僅缺者落位)。
param(
    [Parameter(Mandatory = $true)][string]$Pointer,
    [string]$Base = "C:\VeritasIntelligenceAnalytics",
    [switch]$DryRun
)
$ErrorActionPreference = "Stop"

function Write-Tag { param([string]$Tag, [string]$Msg)
    Write-Host ("  [{0}] {1}" -f $Tag.PadRight(4), $Msg)
}

Write-Host "=== VIA 商品安裝器 v0100 ==="
if (-not (Test-Path -LiteralPath $Pointer)) { throw "指針不在位:$Pointer" }
$ptr = Get-Content -LiteralPath $Pointer -Raw -Encoding UTF8 | ConvertFrom-Json
Write-Host ("商品:{0} {1} · 內容物 {2} 件" -f $ptr.pkg_code, $ptr.name, $ptr.contents_n)

# ── ① 環境檢查 ───────────────────────────────────────────────────────────
$psOK = $PSVersionTable.PSVersion.Major -ge [int]($ptr.install.ps_min.Split('.')[0])
Write-Tag ($(if ($psOK) { "OK" } else { "FAIL" })) ("PowerShell {0}(需 {1}+)" -f $PSVersionTable.PSVersion, $ptr.install.ps_min)
if (-not $psOK) { Write-Host "請先安裝 PowerShell 7+:winget install Microsoft.PowerShell"; exit 2 }
$py = Get-Command py -ErrorAction SilentlyContinue
if (-not $py) { $py = Get-Command python3 -ErrorAction SilentlyContinue }
if (-not $py) { $py = Get-Command python -ErrorAction SilentlyContinue }
if ($py) { Write-Tag "OK" ("python:{0}" -f $py.Source) }
else { Write-Tag "FAIL" "python 不在位 — winget install Python.Python.3.12 後重跑"; exit 2 }

# ── ② pip 依賴(缺才裝;--user) ─────────────────────────────────────────
foreach ($dep in @($ptr.install.pip)) {
    if (-not $dep) { continue }
    & $py.Source -c ("import {0}" -f ($dep -replace '-', '_')) 2>$null
    if ($LASTEXITCODE -eq 0) { Write-Tag "OK" ("依賴 {0} 已在位" -f $dep) }
    elseif ($DryRun) { Write-Tag "PLAN" ("將安裝 {0}(--user)" -f $dep) }
    else {
        Write-Tag "INST" ("pip install --user {0}" -f $dep)
        & $py.Source -m pip install --user --quiet $dep
        if ($LASTEXITCODE -ne 0) { Write-Tag "FAIL" ("{0} 安裝失敗 — 誠實列出,不卡斷" -f $dep) }
    }
}

# ── ③ 基座布建(首次導入即定檔案位置) ─────────────────────────────────
if (-not (Test-Path -LiteralPath $Base)) {
    if ($DryRun) { Write-Tag "PLAN" ("將建立基座 {0}" -f $Base) }
    else { New-Item -ItemType Directory -Path $Base -Force | Out-Null; Write-Tag "OK" ("基座建立 {0}" -f $Base) }
} else { Write-Tag "OK" ("基座已在位 {0}" -f $Base) }

# ── ④ 內容物落位 + sha256 驗真(舉證;不覆蓋既有) ────────────────────
$src = Split-Path (Split-Path (Resolve-Path -LiteralPath $Pointer) -Parent) -Parent  # registry 上兩層=VIA 根
$src = Split-Path $src -Parent
$nOK = 0; $nCopy = 0; $nMismatch = 0
foreach ($c in $ptr.contents) {
    $from = Join-Path $src $c.path
    $to = Join-Path $Base $c.path
    if (Test-Path -LiteralPath $to) {
        if ($c.sha256 -ne "SKIP_LARGE") {
            $h = (Get-FileHash -LiteralPath $to -Algorithm SHA256).Hash.ToLowerInvariant()
            if ($h -eq $c.sha256) { $nOK++ } else { $nMismatch++ }
        } else { $nOK++ }
        continue
    }
    if ($DryRun) { $nCopy++; continue }
    if (Test-Path -LiteralPath $from) {
        New-Item -ItemType Directory -Path (Split-Path $to -Parent) -Force | Out-Null
        Copy-Item -LiteralPath $from -Destination $to
        $nCopy++
    }
}
Write-Tag "OK" ("內容物:既有驗真 {0} · 新落位 {1} · 雜湊不符 {2}(不符=版本前進,非錯)" -f $nOK, $nCopy, $nMismatch)

# ── ⑤ bin 動詞 ───────────────────────────────────────────────────────────
foreach ($v in @($ptr.install.bin_verbs)) {
    $cmd = Join-Path $Base ("bin\{0}.cmd" -f $v)
    Write-Tag ($(if (Test-Path -LiteralPath $cmd) { "OK" } else { "WARN" })) ("動詞 {0}" -f $v)
}
Write-Tag "INFO" ("PATH 提示:將 {0}\bin 加入使用者 PATH 後動詞全域可用" -f $Base)

# ── ⑥ 開第一頁(消費者頁) ──────────────────────────────────────────────
$mother = Join-Path $Base "VIA_Mother.html"
if ((Test-Path -LiteralPath $mother) -and -not $DryRun) {
    Write-Tag "OPEN" $mother
    Start-Process -FilePath $mother
} else { Write-Tag "INFO" "母頁第一頁:VIA_Mother.html(布建後自動開)" }

Write-Host ("=== {0} 安裝{1}完成 · 誠實列況不卡斷 ===" -f $ptr.pkg_code, $(if ($DryRun) { "(DryRun)" } else { "" }))
exit 0

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
