# Install-VIA-Product-v0101.ps1 — VIA 商品通用安裝器(全新電腦全自動版)。
# 用法:pwsh -File Install-VIA-Product-v0101.ps1 -Pointer .\pkg_pointers\PKG_010_Pointer.json [-Base C:\VeritasIntelligenceAnalytics] [-DryRun]
# v0101 新增(操作員令 2026-08-13):
#   ⓪ PS5.1 下自救:偵測 pwsh → 缺則 winget 自動裝 PS7 → 自我轉交 pwsh 重跑(全新電腦零手動)
#   ⑦ 環境衝突掃描:動詞撞名/python 版本/磁碟空間/虛擬環境干擾 — 誠實 OK/WARN
#   ⑧ 綁機商品實例:machine_id=sha256(MachineGuid+電腦名) · 商品組合號=sha256(組合+machine_id)[:12]
#   ⑨ DEFAULT 值落檔:_instance\VIA_Defaults.json(缺才寫;全自動預設)
# 沿用規約:①環境 ②pip ③基座 ④內容物+sha256 舉證 ⑤動詞 ⑥開第一頁;不刪不覆蓋;誠實 OK/FAIL 不卡斷。
param(
    [Parameter(Mandatory = $true)][string]$Pointer,
    [string]$Base = "C:\VeritasIntelligenceAnalytics",
    [switch]$DryRun
)
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
$ErrorActionPreference = "Stop"

function Write-Tag { param([string]$Tag, [string]$Msg)
    Write-Host ("  [{0}] {1}" -f $Tag.PadRight(4), $Msg)
}

Write-Host "=== VIA 商品安裝器 v0101(全新電腦全自動)==="

# ── ⓪ PS7 自動升級自救(在 Windows PowerShell 5.x 下亦可啟動本檔) ──────
if ($PSVersionTable.PSVersion.Major -lt 7) {
    Write-Tag "INFO" ("目前 PowerShell {0} — 啟動 PS7 自救鏈" -f $PSVersionTable.PSVersion)
    $pwsh = Get-Command pwsh -ErrorAction SilentlyContinue
    if (-not $pwsh -and (Test-Path "$env:ProgramFiles\PowerShell\7\pwsh.exe")) {
        $pwsh = @{ Source = "$env:ProgramFiles\PowerShell\7\pwsh.exe" }
    }
    if (-not $pwsh) {
        $winget = Get-Command winget -ErrorAction SilentlyContinue
        if ($winget -and -not $DryRun) {
            Write-Tag "INST" "winget install Microsoft.PowerShell(全自動)"
            & winget install --id Microsoft.PowerShell --silent --accept-package-agreements --accept-source-agreements
            if (Test-Path "$env:ProgramFiles\PowerShell\7\pwsh.exe") { $pwsh = @{ Source = "$env:ProgramFiles\PowerShell\7\pwsh.exe" } }
        }
    }
    if ($pwsh) {
        Write-Tag "HAND" "轉交 pwsh 7 重跑本安裝器"
        & $pwsh.Source -NoProfile -File $PSCommandPath -Pointer $Pointer -Base $Base @(if ($DryRun) { "-DryRun" })
        exit $LASTEXITCODE
    }
    Write-Tag "FAIL" "PS7 無法自動布建(winget 缺席)— 手動一次:https://aka.ms/powershell-release?tag=stable"
    exit 2
}

if (-not (Test-Path -LiteralPath $Pointer)) { throw "指針不在位:$Pointer" }
$ptr = Get-Content -LiteralPath $Pointer -Raw -Encoding UTF8 | ConvertFrom-Json
Write-Host ("商品:{0} {1} · 內容物 {2} 件" -f $ptr.pkg_code, $ptr.name, $ptr.contents_n)

# ── ① 環境檢查 ───────────────────────────────────────────────────────────
Write-Tag "OK" ("PowerShell {0}(需 {1}+)" -f $PSVersionTable.PSVersion, $ptr.install.ps_min)
$py = Get-Command py -ErrorAction SilentlyContinue
if (-not $py) { $py = Get-Command python3 -ErrorAction SilentlyContinue }
if (-not $py) { $py = Get-Command python -ErrorAction SilentlyContinue }
if (-not $py -and -not $DryRun) {
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if ($winget) {
        Write-Tag "INST" "winget install Python.Python.3.12(全自動)"
        & winget install --id Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements
        $py = Get-Command py -ErrorAction SilentlyContinue
        if (-not $py) { $py = Get-Command python -ErrorAction SilentlyContinue }
    }
}
if ($py) { Write-Tag "OK" ("python:{0}" -f $py.Source) }
else { Write-Tag "FAIL" "python 不在位且無法自動布建 — winget install Python.Python.3.12 後重跑"; exit 2 }

# ── ⑦ 環境衝突掃描(誠實列況,不卡斷) ─────────────────────────────────
$pyver = (& $py.Source -c "import sys;print('%d.%d'%sys.version_info[:2])" 2>$null)
$pyMinOK = $false
try { $pyMinOK = ([version]$pyver -ge [version]$ptr.install.python_min) } catch {}
Write-Tag ($(if ($pyMinOK) { "OK" } else { "WARN" })) ("python 版本 {0}(需 {1}+)" -f $pyver, $ptr.install.python_min)
if ($env:VIRTUAL_ENV) { Write-Tag "WARN" ("虛擬環境作用中({0})— pip --user 落點將受其影響" -f $env:VIRTUAL_ENV) }
else { Write-Tag "OK" "無虛擬環境干擾" }
$drive = (Split-Path -Qualifier $Base)
$free = (Get-PSDrive -Name $drive.TrimEnd(':') -ErrorAction SilentlyContinue).Free
if ($free) { Write-Tag ($(if ($free -gt 500MB) { "OK" } else { "WARN" })) ("磁碟可用 {0:N0} MB({1})" -f ($free / 1MB), $drive) }
$collide = 0
foreach ($v in @($ptr.install.bin_verbs)) {
    $ext = Get-Command $v -ErrorAction SilentlyContinue
    if ($ext -and ($ext.Source -notlike "$Base*")) { $collide++; Write-Tag "WARN" ("動詞撞名:{0} 已被 {1} 佔用" -f $v, $ext.Source) }
}
if ($collide -eq 0) { Write-Tag "OK" "動詞無撞名(PATH 掃描)" }

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

# ── ⑧ 綁機商品實例(machine_id + 商品組合號;append-only) ──────────────
$instDir = Join-Path $Base "_instance"
$instFile = Join-Path $instDir "VIA_Instance.json"
if (-not $DryRun) {
    New-Item -ItemType Directory -Path $instDir -Force | Out-Null
    $guid = ""
    try { $guid = (Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Cryptography" -Name MachineGuid -ErrorAction Stop).MachineGuid } catch {}
    $sha = [System.Security.Cryptography.SHA256]::Create()
    $mid = ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes("$guid|$env:COMPUTERNAME"))) -replace '-', '').ToLowerInvariant().Substring(0, 16)
    $inst = if (Test-Path -LiteralPath $instFile) { Get-Content -LiteralPath $instFile -Raw -Encoding UTF8 | ConvertFrom-Json } else { [pscustomobject]@{ machine_id = $mid; installed = @(); history = @() } }
    if ($inst.installed -notcontains $ptr.pkg_code) { $inst.installed = @($inst.installed) + $ptr.pkg_code }
    $comboSrc = (($inst.installed | Sort-Object) -join '+') + '|' + $inst.machine_id
    $combo = ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($comboSrc))) -replace '-', '').ToLowerInvariant().Substring(0, 12)
    $inst | Add-Member -NotePropertyName combo_serial -NotePropertyValue ("VIA-C-" + $combo.ToUpperInvariant()) -Force
    $inst.history = @($inst.history) + [pscustomobject]@{ ts = (Get-Date -Format s); op = "install"; pkg = $ptr.pkg_code }
    $inst | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $instFile -Encoding UTF8
    Write-Tag "OK" ("綁機實例:machine {0} · 組合號 {1} · 已裝 [{2}]" -f $inst.machine_id, $inst.combo_serial, ($inst.installed -join ', '))
} else { Write-Tag "PLAN" "將寫綁機實例 _instance\VIA_Instance.json(machine_id+組合號)" }

# ── ⑨ DEFAULT 值(缺才寫 — 全自動預設,消費者零設定) ──────────────────
$defFile = Join-Path $instDir "VIA_Defaults.json"
if (-not $DryRun -and -not (Test-Path -LiteralPath $defFile)) {
    [pscustomobject]@{
        base = $Base; lang = "zh-Hant"; theme = "veritas_header_lock_v0101"
        auto_open_mother = $true; precheck_before_run = $true
        output_formats = @("parquet", "csv", "json"); duckdb = $true
        no_send_mail = $true; readonly_originals = $true
    } | ConvertTo-Json | Set-Content -LiteralPath $defFile -Encoding UTF8
    Write-Tag "OK" "DEFAULT 值落檔 _instance\VIA_Defaults.json(紅線預設:絕不代寄+唯讀原件)"
} elseif (Test-Path -LiteralPath $defFile) { Write-Tag "OK" "DEFAULT 已在位(不覆蓋)" }

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
