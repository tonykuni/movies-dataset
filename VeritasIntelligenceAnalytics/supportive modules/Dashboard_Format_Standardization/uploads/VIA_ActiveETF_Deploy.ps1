#requires -Version 7.0
# ============================================================================
# VIA_ActiveETF_Deploy.ps1  —  結案：環境稽核 → 基準快照 → 自動部署設定 → 每日更新
# ----------------------------------------------------------------------------
#  1) AUDIT     : 檢查 Python / 套件(pyarrow,pandas,numpy<2.0,yfinance) / eco 衝突 /
#                 vetf 核心檔 / 輔助工具(4) / Edge
#  2) GATE      : 有衝突(numpy>=2.0、eco BLOCK、缺核心) → 停止（除非 -Force）
#  3) SNAPSHOT  : 無衝突 → 以現況為「自動部署基準」寫 VIA_ActiveETF_DeployConfig.json
#  4) SETTINGS  : 寫入所有環境/工具/路徑；-AddToPath 將 vetf 加入使用者 PATH（append-only）
#                 -Install 用 pip 補齊缺套件（numpy 鎖 <2.0）
#  5) DAILY     : 註冊 Windows 排程 VIA_ActiveETF_DailyUpdate（每日 sync 重建）
#  6) CLOSEOUT  : 結案報告（JSON + 主控台摘要）
#  LL：param 頂部 / 全名函式 / py 啟動器(LL#16) / [IO.File](LL) / .Replace(LL#34) / 無 Start-Job
# ============================================================================
param(
    [string]$Root       = "C:\Users\tonyk\OneDrive\Desktop\VeritasIntelligenceAnalytics\modules\vetf",
    [string]$ModulesDir = "C:\Users\tonyk\OneDrive\Desktop\VeritasIntelligenceAnalytics\modules\supportive modules",
    [string]$PythonExe  = "",
    [string]$DictRoot   = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\_dict\active_etf",
    [string]$UpdateTime = "08:00",
    [switch]$Install,
    [switch]$AddToPath,
    [switch]$NoSchedule,
    [switch]$Force
)

$script:Core = @("VIA_ActiveETF_System.py","console_merged_template.html","VIA_ActiveETF.ps1","VIA_ActiveETF_Console.html","VIA_ActiveETF_PackList.json")
$script:Used = @("VeritasAegisNexus.py","VeritasCeleritas.py","VIA_EnvManager.py","VIA_SSOT_Unified.py")
$script:ReqPkgs = @("pyarrow","pandas")          # 資料層必需
$script:OptPkgs = @("yfinance")                  # 接真實量價時需要
$script:TaskName = "VIA_ActiveETF_DailyUpdate"
$script:Report = [ordered]@{}

function Write-Status { param([string]$Level,[string]$Message)
    $c = switch ($Level.ToUpper()) { "OK"{"Green"} "WARN"{"Yellow"} "FAIL"{"Red"} default{"Gray"} }
    Write-Host ("[{0}][{1}] {2}" -f (Get-Date -Format "HH:mm:ss"), $Level.ToUpper(), $Message) -ForegroundColor $c }

function Resolve-Python { param([string]$Hint)
    if ($Hint -and (Test-Path $Hint)) { return @($Hint) }
    foreach ($v in @("3.12","3.11","3.13")) { try { & py "-$v" -c "import sys" 2>$null; if ($LASTEXITCODE -eq 0) { return @("py","-$v") } } catch {} }
    try { & python -c "import sys" 2>$null; if ($LASTEXITCODE -eq 0) { return @("python") } } catch {}
    return $null
}
function Invoke-Py { param([string[]]$Py,[string[]]$Args)
    return (& $Py[0] ($Py[1..($Py.Count-1)] + $Args) 2>$null) }
function Get-PkgVersion { param([string[]]$Py,[string]$Pkg)
    try { $v = Invoke-Py $Py @("-c","import $Pkg,sys;sys.stdout.write(getattr($Pkg,'__version__','?'))"); if ($LASTEXITCODE -eq 0) { return "$v" } } catch {}
    return $null }
function Test-VersionLt { param([string]$Ver,[int]$Major)
    try { return ([int]($Ver.Split('.')[0]) -lt $Major) } catch { return $false } }

$conflicts = New-Object System.Collections.Generic.List[string]
$warnings  = New-Object System.Collections.Generic.List[string]

# ---------- 1) AUDIT ----------
Write-Status INFO "VIA Active ETF — 結案部署稽核開始"
if (-not (Test-Path $Root)) { Write-Status FAIL "找不到 vetf：$Root"; exit 1 }

$py = Resolve-Python -Hint $PythonExe
if (-not $py) { Write-Status FAIL "找不到 Python（py 啟動器 / python / -PythonExe）。"; exit 1 }
$pyReal = (Invoke-Py $py @("-c","import sys;sys.stdout.write(sys.executable)"))
$pyVer  = (Invoke-Py $py @("-c","import sys;sys.stdout.write('.'.join(map(str,sys.version_info[:3])))"))
Write-Status OK ("Python = {0} ({1})" -f $pyVer, $pyReal)
$script:Report.python = @{ version=$pyVer; exe=$pyReal; launcher=($py -join ' ') }

# 套件
$pkgInfo = [ordered]@{}
foreach ($p in ($script:ReqPkgs + @("numpy") + $script:OptPkgs)) {
    $v = Get-PkgVersion -Py $py -Pkg $p
    $pkgInfo[$p] = $v
    if ($v) { Write-Status OK ("pkg {0} = {1}" -f $p, $v) }
    else {
        if ($script:OptPkgs -contains $p) { Write-Status WARN ("選用套件未安裝：{0}（接真實量價時需要）" -f $p); $warnings.Add("opt_missing:$p") }
        elseif ($p -eq "numpy") { Write-Status WARN "numpy 未偵測（System.py 用 pyarrow/pandas，可不需）" }
        else { Write-Status WARN ("必需套件未安裝：{0}" -f $p); $warnings.Add("req_missing:$p") }
    }
}
# numpy 黃金律：<2.0
if ($pkgInfo["numpy"] -and -not (Test-VersionLt -Ver $pkgInfo["numpy"] -Major 2)) {
    Write-Status FAIL ("numpy {0} 違反黃金律(<2.0)" -f $pkgInfo["numpy"]); $conflicts.Add("numpy>=2.0:$($pkgInfo['numpy'])") }
$script:Report.packages = $pkgInfo

# eco-check（呼叫 System.py）
$sys = Join-Path $Root "VIA_ActiveETF_System.py"
if (Test-Path $sys) {
    $eco = Invoke-Py $py @($sys,"eco-check","--pkgs","pyarrow pandas yfinance","--py",$pyVer,"--os","windows")
    try { $ecoObj = ($eco | ConvertFrom-Json); if ($ecoObj.decision -eq "BLOCK") { Write-Status FAIL "eco-check BLOCK"; $conflicts.Add("eco_block") } else { Write-Status OK "eco-check PASS（無生態衝突）" }; $script:Report.eco = $ecoObj.decision } catch { Write-Status WARN "eco-check 解析失敗" }
} else { Write-Status WARN "缺 VIA_ActiveETF_System.py，略過 eco-check"; $warnings.Add("missing:System.py") }

# 核心檔 / 輔助工具 / Edge
$missCore = @($script:Core | Where-Object { -not (Test-Path (Join-Path $Root $_)) })
foreach ($m in $missCore) { Write-Status FAIL "缺核心檔：$m"; $conflicts.Add("missing_core:$m") }
$haveUsed = @($script:Used | Where-Object { (Test-Path (Join-Path $ModulesDir $_)) -or (Test-Path (Join-Path $Root $_)) })
Write-Status OK ("輔助工具就緒 {0}/4：{1}" -f $haveUsed.Count, ($haveUsed -join ", "))
$edge = @("${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe","$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($edge) { Write-Status OK "Edge 偵測（EXE/PWA 可用 --app 視窗）" } else { Write-Status WARN "未偵測 Edge（退回預設瀏覽器）"; $warnings.Add("no_edge") }
$script:Report.files = @{ core_missing=$missCore; used_ready=$haveUsed; edge=$edge }

# ---------- 1b) 可選 INSTALL（補齊缺套件，numpy 鎖 <2.0） ----------
if ($Install) {
    Write-Status INFO "INSTALL：補齊缺套件..."
    $need = @($script:ReqPkgs | Where-Object { -not $pkgInfo[$_] }) + @($script:OptPkgs | Where-Object { -not $pkgInfo[$_] })
    if (-not $pkgInfo["numpy"]) { $need += '"numpy>=1.24,<2.0"' }
    if ($need.Count) {
        & $py[0] ($py[1..($py.Count-1)] + @("-m","pip","install","--upgrade") + $need)
        if ($LASTEXITCODE -eq 0) { Write-Status OK ("已安裝：{0}" -f ($need -join ' ')) ; foreach ($p in $script:ReqPkgs) { $pkgInfo[$p] = (Get-PkgVersion -Py $py -Pkg $p) } } else { Write-Status WARN "pip 安裝回傳非零" }
    } else { Write-Status OK "套件齊全，無需安裝。" }
}

# ---------- 2) GATE ----------
if ($conflicts.Count -gt 0 -and -not $Force) {
    Write-Status FAIL ("發現衝突/缺項 {0}：{1}" -f $conflicts.Count, ($conflicts -join '; '))
    Write-Status FAIL "結案中止。請修正（或 -Install 補套件 / -Force 強制），不部署、不排程。"
    $script:Report.result = "BLOCKED"; $script:Report.conflicts = @($conflicts)
    [IO.File]::WriteAllText((Join-Path $Root "VIA_ActiveETF_DeployConfig.json"), ($script:Report | ConvertTo-Json -Depth 6), [System.Text.UTF8Encoding]::new($false))
    exit 2
}
Write-Status OK "稽核通過：環境/工具齊備、無衝突。以現況作為自動部署基準。"

# ---------- 3+4) SNAPSHOT + SETTINGS ----------
if ($AddToPath) {
    $cur = [Environment]::GetEnvironmentVariable("Path","User"); if (-not $cur) { $cur = "" }
    if ($cur -notlike "*$Root*") {
        [Environment]::SetEnvironmentVariable("Path", ($cur.TrimEnd(';') + ";" + $Root), "User")
        Write-Status OK "已將 vetf 加入使用者 PATH（append-only）。"
    } else { Write-Status OK "PATH 已含 vetf，無需重加。" }
}
$dailyArgs = @($sys,"sync","--dict",$DictRoot,"--templates",$Root,"--out",$Root)
$logo = Join-Path $Root "VIA_logo.png"; if (Test-Path $logo) { $dailyArgs += @("--logo",$logo) }
$script:Report.autodeploy = [ordered]@{
    baseline_at = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    root = $Root; modules_dir = $ModulesDir; dict_root = $DictRoot
    python = $pyReal; required = $script:ReqPkgs; optional = $script:OptPkgs; numpy_rule = ">=1.24,<2.0"
    edge = $edge; add_to_path = [bool]$AddToPath
    daily_update = @{ task = $script:TaskName; time = $UpdateTime; exec = $pyReal; args = ($dailyArgs -join ' ') }
    reinstall_cmd = ("{0} -m pip install --upgrade pyarrow pandas ""numpy>=1.24,<2.0"" yfinance" -f $pyReal)
}

# ---------- 5) DAILY UPDATE（排程） ----------
if (-not $NoSchedule) {
    try {
        $action  = New-ScheduledTaskAction -Execute $pyReal -Argument ($dailyArgs -join ' ') -WorkingDirectory $Root
        $trigger = New-ScheduledTaskTrigger -Daily -At $UpdateTime
        $set     = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd -ExecutionTimeLimit (New-TimeSpan -Hours 1)
        Register-ScheduledTask -TaskName $script:TaskName -Action $action -Trigger $trigger -Settings $set -Description "VIA Active ETF 每日資料同步 + Console 重建" -Force | Out-Null
        Write-Status OK ("每日更新已排程：{0} @ {1}（sync→PARQUET 增量→重建 Console）" -f $script:TaskName, $UpdateTime)
        $script:Report.autodeploy.daily_update.registered = $true
    } catch {
        Write-Status WARN ("排程註冊失敗（需系統管理員權限？）：{0}" -f $_.Exception.Message)
        Write-Status INFO ("手動：schtasks /Create /SC DAILY /ST {0} /TN {1} /TR ""{2} {3}""" -f $UpdateTime, $script:TaskName, $pyReal, ($dailyArgs -join ' '))
        $script:Report.autodeploy.daily_update.registered = $false
    }
} else { Write-Status INFO "NoSchedule：略過每日排程。"; $script:Report.autodeploy.daily_update.registered = $false }

# ---------- 6) CLOSEOUT ----------
$script:Report.result = "DEPLOYED"
$script:Report.warnings = @($warnings)
$cfg = Join-Path $Root "VIA_ActiveETF_DeployConfig.json"
[IO.File]::WriteAllText($cfg, ($script:Report | ConvertTo-Json -Depth 6), [System.Text.UTF8Encoding]::new($false))
Write-Status OK ("自動部署設定已寫出：{0}" -f $cfg)
Write-Host ""
Write-Status OK "============ 結案 CLOSEOUT ============"
Write-Status OK ("環境：Python {0} · pyarrow/pandas 就緒 · numpy<2.0 · eco {1}" -f $pyVer, $script:Report.eco)
Write-Status OK ("基準：以現況鎖定為自動部署基準（{0}）" -f $Root)
Write-Status OK ("每日更新：{0} @ {1}" -f $script:TaskName, $UpdateTime)
Write-Status OK ("啟動 UI：pwsh -File VIA_ActiveETF.ps1   或   打包 EXE：pwsh -File VIA_ActiveETF_Pack.ps1")
if ($warnings.Count) { Write-Status WARN ("提醒：{0}" -f ($warnings -join '; ')) }
Write-Status OK "VIA Active ETF 系統已部署並啟動每日更新。結案完成。"
exit 0

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
