#Requires -Version 7.0
<#
=============================================================================
Invoke-VIA-UnifyOneFolder-v0102 — 唯一文件夾整併統包器(TOOL-087,批86)
=============================================================================
v0101→v0102(批86 收尾令「請將這幾個系統進行收尾」):
  ① -ScopeFile:S5 舊 Downloads VIA 夾對帳走 oldscan --scope 範圍閘
     (預設接 VIA_OldRoot_Scope_v0100.json 具名 19 項;檔不存在=不加
     旗標,誠實記帳)。工作站實證:範圍閘 187,866→31,228 件,4 分鐘
     全程進度條;DIFF 9+MISSING 40 待抓回。
  ② -SkipOldClone:S4 舊克隆已於前輪 rc=0 完成者可跳過(SKIP 誠實
     記帳),收尾只跑 S5 scoped apply→S6 具名入庫→S7/S8 雙推→
     S9/S10 復驗。
=============================================================================
v0100→v0101(批82,工作站實證):stash push -u 在 rollback/rb-… 深巢
路徑撞 Windows 260 字元上限(error: Filename too long → fatal)整場
自救失敗。三修:
  ① S2 先下 git config core.longpaths true(新正典 repo 本地設定,
     一次設定永久生效);
  ② stash 降級後備:-u(含未追蹤)失敗→改追蹤檔限定 stash 再試
     (未追蹤檔不擋 pull,誠實記帳);
  ③ S1 前檢加 OS LongPathsEnabled 探測:0/缺=WARN 並印管理員一行
     啟用令(不強制,oldscan v0103 已 \\?\ 前綴免疫)。
操作員令(批81):「卡斷 修復不卡斷 加入25個POWERSHELL加速器 動態進度條
改為新舊路徑文件夾 不要打開任何其他視窗自動完成一切 INTEGRATE ALL INTO ONE PS CODE」

一支 PS 全自動完成(零互動、零新視窗、每步看門狗逾時截停=不卡斷):
  S1 前檢(python/git 解析;fd/rg 加速器偵測;25 工加速器注入)
  S2 新正典 git 自救(本地變更 stash 保全,零刪除)+拉最新(退避重試)
  S3 動態解析最新版 oldscan(glob,嚴禁寫死版號)
  S4 舊克隆 VIA 樹抓回:--apply --with-artifacts(runtime 資料整併)
  S5 舊 Downloads VIA 夾抓回:--apply
  S6 manifest 具名入庫(禁 add -A:逐檔來自 oldscan manifest;
     gitignore 區誠實濾出=留在本地唯一夾不入 git)
  S7 commit(標準尾標)
  S8 雙推 main+claude 分支(退避重試 2/4/8/16s)
  S9 官方個股冊重建 via-flowops --refresh-equity(同意閘內)
  S10 六道復驗 via-run via-wrapup --battery(看門狗截停不卡斷)
  S11 誠實三態總結矩陣+JSON 存證 VIA_Reports\unify_runs\

用法(單行,全自動):
  pwsh -NoProfile -ExecutionPolicy Bypass -File Invoke-VIA-UnifyOneFolder-v0102.ps1 -SkipOldClone
唯讀演練(不 apply 不 commit 不推):加 -Plan
=============================================================================
#>
param(
    [string]$NewRepo  = 'C:\Users\tonyk\Downloads\movies-dataset',
    [string]$OldClone = 'C:\Users\tonyk\movies-dataset\VeritasIntelligenceAnalytics',
    [string]$OldVia   = 'C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics',
    [int]$Accelerators = 25,
    [int]$ScanTimeoutSec = 7200,
    [int]$BatteryTimeoutSec = 1800,
    [string]$ScopeFile = '',
    [switch]$SkipOldClone,
    [switch]$Plan
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Continue'
$ProgressPreference = 'Continue'

$NewVia = Join-Path $NewRepo 'VeritasIntelligenceAnalytics'
$RunStart = Get-Date
$Ts = $RunStart.ToString('yyyyMMdd_HHmmss')
$EvDir = Join-Path $NewVia 'VIA_Reports\unify_runs'
$null = New-Item -ItemType Directory -Force -Path $EvDir
$Steps = [System.Collections.Generic.List[object]]::new()

function Write-Line { param([string]$Level,[string]$Msg)
    $c = switch ($Level) { 'OK' {'Green'} 'FAIL' {'Red'} 'WARN' {'Yellow'} 'RUN' {'Cyan'} 'SKIP' {'DarkYellow'} default {'Gray'} }
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] [$Level] $Msg" -ForegroundColor $c
}
function Add-Step { param([string]$Name,[string]$State,[string]$Note='')
    $Steps.Add([pscustomobject]@{ step=$Name; state=$State; note=$Note })
    Write-Line $State "$Name $Note"
}
function Q { param([string]$s) if ($s -match '\s') { '"' + $s + '"' } else { $s } }

function Invoke-Guarded {
    # 看門狗外呼:同視窗直播輸出(-NoNewWindow),逾時 Kill 整樹=不卡斷
    param([string]$Name,[string]$Exe,[string[]]$CmdArgs,[int]$TimeoutSec = 1800,[string]$Cwd = $NewRepo)
    $argStr = ($CmdArgs | ForEach-Object { Q $_ }) -join ' '
    Write-Line 'RUN' "$Name"
    $p = Start-Process -FilePath $Exe -ArgumentList $argStr -NoNewWindow -PassThru -WorkingDirectory $Cwd
    $t0 = Get-Date
    while (-not $p.HasExited) {
        $el = [int]((Get-Date) - $t0).TotalSeconds
        if ($el -ge $TimeoutSec) {
            try { $p.Kill($true) } catch {}
            Write-Line 'FAIL' "$Name 逾時 $TimeoutSec s 看門狗截停(不卡斷)"
            return 124
        }
        Write-Progress -Id 7 -Activity '唯一文件夾整併(動態進度)' `
            -Status "$Name · 已 $el s / 上限 $TimeoutSec s" `
            -PercentComplete ([Math]::Min(99, [int](100 * $el / $TimeoutSec)))
        Start-Sleep -Milliseconds 800
    }
    Write-Progress -Id 7 -Activity '唯一文件夾整併(動態進度)' -Completed
    return $p.ExitCode
}

function Invoke-GitRetry {
    # 網路退避重試 2/4/8/16s(標準令);git 皆錨定新正典
    param([string]$Name,[string[]]$GitArgs,[int]$TimeoutSec = 600)
    foreach ($d in @(0, 2, 4, 8, 16)) {
        if ($d) { Write-Line 'WARN' "$Name 重試前等待 $d s…"; Start-Sleep -Seconds $d }
        $rc = Invoke-Guarded $Name 'git' (@('-C', $NewRepo) + $GitArgs) $TimeoutSec
        if ($rc -eq 0) { return 0 }
    }
    return 1
}

Write-Host ''
Write-Host '================================================================================' -ForegroundColor Cyan
Write-Host "VIA 唯一文件夾整併統包器 v0102 · TOOL-087(批86:範圍閘收尾)$(if($Plan){' · Plan 唯讀演練'})" -ForegroundColor Cyan
Write-Host "  唯一正典:$NewRepo" -ForegroundColor Cyan
Write-Host '================================================================================' -ForegroundColor Cyan
Start-Transcript -Path (Join-Path $EvDir "UNIFY_$Ts.log") -Append | Out-Null

# ---- S1 前檢:解譯器+加速器 -------------------------------------------------
if (-not (Test-Path -LiteralPath $NewVia -PathType Container)) {
    Add-Step 'S1 前檢' 'FAIL' "唯一正典不存在:$NewVia"
    Stop-Transcript | Out-Null; exit 1
}
$Py = if (Get-Command py -ErrorAction SilentlyContinue) { 'py' }
      elseif (Get-Command python -ErrorAction SilentlyContinue) { 'python' } else { $null }
if (-not $Py) { Add-Step 'S1 前檢' 'FAIL' '無 python/py'; Stop-Transcript | Out-Null; exit 1 }
$env:VIA_OLDSCAN_WORKERS = "$Accelerators"                       # 25 個加速器注入 oldscan
$env:Path = (Join-Path $NewVia 'bin') + ';' + $env:Path          # PATH 錨定新正典 bin(修舊 bin 誤掛)
$fd = [bool](Get-Command fd -ErrorAction SilentlyContinue)
$rg = [bool](Get-Command rg -ErrorAction SilentlyContinue)
$lpe = 0
try {
    $lpe = [int](Get-ItemPropertyValue -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem' `
        -Name 'LongPathsEnabled' -ErrorAction Stop)
} catch { $lpe = 0 }
if ($lpe -ne 1) {
    Write-Line 'WARN' 'OS LongPathsEnabled=0:超長路徑靠 git core.longpaths + oldscan \\?\ 前綴免疫;要根治可用管理員跑:'
    Write-Line 'WARN' 'New-ItemProperty -Path HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem -Name LongPathsEnabled -Value 1 -PropertyType DWord -Force'
}
Add-Step 'S1 前檢' 'OK' "python=$Py · 加速器 $Accelerators 工 · fd=$fd rg=$rg · LongPaths=$lpe"

# ---- S2 git 自救+拉新(本地變更 stash 保全=零刪除) -------------------------
git -C $NewRepo config core.longpaths true      # 批82:260 字元上限免疫(repo 本地永久)
Write-Line 'OK' 'S2 前置:git core.longpaths=true(長路徑免疫)'
$dirty = git -C $NewRepo status --porcelain
if ($dirty) {
    $rc = Invoke-Guarded 'S2a stash 保全(-u 含未追蹤)' 'git' @('-C', $NewRepo, 'stash', 'push', '-u', '-m', "unify-rescue-$Ts") 600
    if ($rc -ne 0) {
        # 批82 後備:未追蹤區撞長路徑→改追蹤檔限定 stash(未追蹤不擋 pull)
        Write-Line 'WARN' 'stash -u 失敗(疑長路徑未追蹤件)→降級為追蹤檔限定 stash'
        $rc = Invoke-Guarded 'S2a stash 保全(追蹤檔限定)' 'git' @('-C', $NewRepo, 'stash', 'push', '-m', "unify-rescue-tracked-$Ts") 600
    }
    Add-Step 'S2a stash 保全' ($(if ($rc -eq 0) { 'OK' } else { 'FAIL' })) "$(($dirty | Measure-Object).Count) 件本地變更(stash 可 pop 取回,零刪除)"
} else { Add-Step 'S2a stash 保全' 'SKIP' '工作樹乾淨' }
$rc = Invoke-GitRetry 'S2b git pull origin main' @('pull', 'origin', 'main')
Add-Step 'S2b 拉最新' ($(if ($rc -eq 0) { 'OK' } else { 'FAIL' })) "rc=$rc"
if ($rc -ne 0) { Write-Line 'WARN' '拉新失敗仍續行(用既有版本,誠實記帳)' }

# ---- S3 動態解析最新版 oldscan(嚴禁寫死版號) -------------------------------
$scanner = Get-ChildItem -LiteralPath (Join-Path $NewVia 'supportive modules\registry') `
    -Filter 'via_oldroot_scan_v0*.py' | Sort-Object Name | Select-Object -Last 1
if (-not $scanner) { Add-Step 'S3 解析 oldscan' 'FAIL' '查無 via_oldroot_scan_v0*.py'; Stop-Transcript | Out-Null; exit 1 }
Add-Step 'S3 解析 oldscan' 'OK' $scanner.Name

# ---- S4/S5 兩棵舊樹抓回(并行雜湊+進度條在 python 側直播) -------------------
$applyFlags = if ($Plan) { @() } else { @('--apply') }
if (-not $ScopeFile) {
    $ScopeFile = Join-Path $NewVia 'supportive modules\registry\VIA_OldRoot_Scope_v0100.json'
}
$scopeFlags = @()
if (Test-Path -LiteralPath $ScopeFile -PathType Leaf) {
    $scopeFlags = @('--scope', $ScopeFile)
    Write-Line 'OK' "S5 範圍閘掛載:$(Split-Path -Leaf $ScopeFile)(批85 具名收斂,防過度發散)"
} else {
    Write-Line 'WARN' "範圍冊不存在($ScopeFile)→ S5 全樹對帳(誠實記帳)"
}
foreach ($job in @(
        @{ n = 'S4 舊克隆 VIA 樹抓回(runtime 含產物)'; old = $OldClone; extra = @('--with-artifacts'); skip = [bool]$SkipOldClone },
        @{ n = 'S5 舊 Downloads VIA 夾抓回(範圍閘)';   old = $OldVia;   extra = $scopeFlags;            skip = $false })) {
    if ($job.skip) {
        Add-Step $job.n 'SKIP' '-SkipOldClone:前輪已 rc=0 完成(冪等,不重跑)'; continue
    }
    if (-not (Test-Path -LiteralPath $job.old -PathType Container)) {
        Add-Step $job.n 'SKIP' "舊根不存在:$($job.old)"; continue
    }
    $rc = Invoke-Guarded $job.n $Py (@($scanner.FullName, '--old', $job.old, '--repo', $NewVia) + $applyFlags + $job.extra) $ScanTimeoutSec
    Add-Step $job.n ($(if ($rc -eq 0) { 'OK' } else { 'FAIL' })) "rc=$rc$(if($Plan){' (Plan 唯讀)'})"
}

# ---- S6 manifest 具名入庫(禁 add -A;gitignore 誠實濾出) --------------------
if ($Plan) {
    Add-Step 'S6 具名入庫' 'SKIP' 'Plan 唯讀演練'
} else {
    $manifests = Get-ChildItem -LiteralPath (Join-Path $NewVia 'VIA_Reports\oldroot_runs') `
        -Filter 'OLDROOT_*.json' -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -ge $RunStart }
    $paths = [System.Collections.Generic.HashSet[string]]::new()
    foreach ($mf in $manifests) {
        $j = Get-Content -LiteralPath $mf.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($j.PSObject.Properties['apply']) {
            foreach ($a in $j.apply.applied) {
                $null = $paths.Add(('VeritasIntelligenceAnalytics/' + ($a.rel -replace '\\', '/')))
            }
        }
    }
    if ($paths.Count -eq 0) {
        Add-Step 'S6 具名入庫' 'SKIP' '本輪 manifest 無 apply 落檔'
    } else {
        $tmpAll = Join-Path $EvDir "UNIFY_${Ts}_paths_all.txt"
        [System.IO.File]::WriteAllLines($tmpAll, $paths)
        $ignored = [System.Collections.Generic.HashSet[string]]::new()
        (Get-Content -LiteralPath $tmpAll | git -C $NewRepo check-ignore --stdin) |
            ForEach-Object { $null = $ignored.Add($_) }
        $stage = @($paths | Where-Object { -not $ignored.Contains($_) })
        if ($stage.Count -eq 0) {
            Add-Step 'S6 具名入庫' 'SKIP' "抓回 $($paths.Count) 件全在 gitignore 區(留本地唯一夾,誠實)"
        } else {
            $tmpStage = Join-Path $EvDir "UNIFY_${Ts}_paths_stage.txt"
            [System.IO.File]::WriteAllLines($tmpStage, $stage)
            $rc = Invoke-Guarded 'S6 git add(manifest 具名)' 'git' @('-C', $NewRepo, 'add', "--pathspec-from-file=$tmpStage") 900
            Add-Step 'S6 具名入庫' ($(if ($rc -eq 0) { 'OK' } else { 'FAIL' })) "staged $($stage.Count) · gitignore 濾出 $($ignored.Count)(留本地)"
        }
    }
}

# ---- S7 commit(標準尾標)+ S8 雙推 -----------------------------------------
if ($Plan) {
    Add-Step 'S7 commit' 'SKIP' 'Plan'; Add-Step 'S8 雙推' 'SKIP' 'Plan'
} else {
    git -C $NewRepo diff --cached --quiet
    if ($LASTEXITCODE -ne 0) {
        $msgFile = Join-Path $EvDir "UNIFY_${Ts}_commitmsg.txt"
        @(
            '批81 唯一文件夾整併:兩棵舊樹資料抓回(oldscan apply,manifest 具名入庫)'
            ''
            "- 統包器 Invoke-VIA-UnifyOneFolder 全自動:stash 自救+拉新+雙舊樹 apply+具名 staging"
            "- 舊克隆 runtime(含產物區)與舊 Downloads VIA 夾遺漏件整併入唯一正典"
            ''
            'Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>'
            'Claude-Session: https://claude.ai/code/session_01R2d69oa1AGvnPVwjSUdSv5'
        ) | Set-Content -LiteralPath $msgFile -Encoding UTF8
        $rc = Invoke-Guarded 'S7 git commit' 'git' @('-C', $NewRepo, 'commit', '-F', $msgFile) 600
        Add-Step 'S7 commit' ($(if ($rc -eq 0) { 'OK' } else { 'FAIL' })) "rc=$rc"
        $rc1 = Invoke-GitRetry 'S8a push main' @('push', 'origin', 'HEAD:main')
        $rc2 = Invoke-GitRetry 'S8b push claude 分支' @('push', '-u', 'origin', 'HEAD:claude/via-system-followup-tz7k9t')
        Add-Step 'S8 雙推' ($(if ($rc1 -eq 0 -and $rc2 -eq 0) { 'OK' } else { 'FAIL' })) "main rc=$rc1 · claude rc=$rc2"
    } else {
        Add-Step 'S7 commit' 'SKIP' '無 staged 變更'; Add-Step 'S8 雙推' 'SKIP' '無 commit'
    }
}

# ---- S9 官方個股冊 + S10 六道復驗(皆看門狗,不卡斷) -------------------------
if ($Plan) {
    Add-Step 'S9 個股冊重建' 'SKIP' 'Plan'; Add-Step 'S10 battery 復驗' 'SKIP' 'Plan'
} else {
    $bin = Join-Path $NewVia 'bin'
    $rc = Invoke-Guarded 'S9 via-flowops --refresh-equity' 'cmd.exe' @('/c', (Join-Path $bin 'via-flowops.cmd'), '--refresh-equity') 900 $NewVia
    Add-Step 'S9 個股冊重建' ($(if ($rc -eq 0) { 'OK' } else { 'FAIL' })) "rc=$rc(官方 OpenAPI 同意閘內)"
    $rc = Invoke-Guarded 'S10 via-run via-wrapup --battery' 'cmd.exe' @('/c', (Join-Path $bin 'via-run.cmd'), 'via-wrapup', '--battery') $BatteryTimeoutSec $NewVia
    Add-Step 'S10 battery 復驗' ($(if ($rc -eq 0) { 'OK' } elseif ($rc -eq 124) { 'FAIL' } else { 'FAIL' })) "rc=$rc$(if($rc -eq 124){'(逾時截停,誠實不卡斷)'})"
}

# ---- S11 誠實三態總結+存證 ---------------------------------------------------
Write-Host ''
Write-Host '=== 唯一文件夾整併 · 總結矩陣(誠實三態)===' -ForegroundColor Cyan
$Steps | Format-Table -AutoSize | Out-String | Write-Host
$ok = @($Steps | Where-Object state -eq 'OK').Count
$fail = @($Steps | Where-Object state -eq 'FAIL').Count
$skip = @($Steps | Where-Object state -eq 'SKIP').Count
[pscustomobject]@{
    schema = 'VIA.UnifyOneFolder.v1'; ts = $Ts; plan = [bool]$Plan
    new_repo = $NewRepo; old_clone = $OldClone; old_via = $OldVia
    accelerators = $Accelerators; steps = $Steps; ok = $ok; fail = $fail; skip = $skip
} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $EvDir "UNIFY_$Ts.json") -Encoding UTF8
Write-Line ($(if ($fail -eq 0) { 'OK' } else { 'FAIL' })) "OK $ok · FAIL $fail · SKIP $skip · 存證 VIA_Reports\unify_runs\UNIFY_$Ts.json"
Write-Line 'WARN' '兩棵舊樹=退役候裁:零刪除不動,僅停止寫入;清理時機由操作員裁決'
Stop-Transcript | Out-Null
exit $(if ($fail -eq 0) { 0 } else { 1 })

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
