# =============================================================================
# VIA_PS_Accel_Module — PS 側 20 加速器實體模組(TOOL-101,批102)
# 操作員令:「所有 PS 檔案也要導入前述 20 個加速器」。
# 用法:. "$VIARoot\supportive modules\VIA_PS_Accel_Module.ps1"(dot-source)
# 提供:$VIA_ACCEL20 冊 + Invoke-VIAGuarded(18 非阻塞看門狗)
#       + Write-VIAProgress(16 動態進度/17 動態說明)+ Invoke-VIAParallel(并行)
# =============================================================================
if (-not (Get-Variable -Name VIA_ACCEL20 -Scope Script -ErrorAction SilentlyContinue)) {

$script:VIA_ACCEL20 = [ordered]@{
    '01' = 'AST 精準解析(PS Parser::ParseFile / py ast.parse)'
    '02' = '多語言語意(同義字冊+finlex 承接)'
    '03' = '九頭龍風險預測(fan-in 偵測)'
    '04' = '依賴拓撲排序(via-deps)'
    '05' = '沙盒隔離執行(selftest grid/tempfile)'
    '06' = '自動修正建議(via-fixsyntax 提案不盲修)'
    '07' = '三輪全景式分析(CentralGov R1-R3)'
    '08' = 'SSOT 對齊(via-params/Regex 中心)'
    '09' = '視覺化矩陣生成(UI Matrix/via-center)'
    '10' = '錯誤分類分群(Parallel-Fixable/Sequence-Dependent)'
    '11' = '性能複雜度分析(P4 死碼盤點)'
    '12' = '多子系統同步檢視(via-subsys)'
    '13' = '版本差異回滾(git+manifest --undo)'
    '14' = '覆蓋率回歸(grid 全站)'
    '15' = '修正順序最佳化(fan-in 升冪排程)'
    '16' = '動態進度條(Write-VIAProgress)'
    '17' = '動態說明(narration)'
    '18' = '非阻塞 PS 執行(Invoke-VIAGuarded 看門狗)'
    '19' = '多引擎整合(via-py Celeritas 常駐+cmd 動詞群)'
    '20' = '自動部署初始化(via_provision/同意閘)'
}

function Write-VIAProgress {
    # 16 動態進度條+17 動態說明:單列不卡斷
    param([string]$Activity, [string]$Status, [int]$Percent = -1, [int]$Id = 11)
    if ($Percent -ge 0) {
        Write-Progress -Id $Id -Activity $Activity -Status $Status -PercentComplete ([Math]::Min(100, $Percent))
    } else {
        Write-Progress -Id $Id -Activity $Activity -Status $Status
    }
}

function Invoke-VIAGuarded {
    # 18 非阻塞看門狗:同視窗直播、逾時 Kill 整樹=不卡斷(統包器同款)
    param([string]$Name, [string]$Exe, [string[]]$CmdArgs, [int]$TimeoutSec = 900, [string]$Cwd = (Get-Location).Path)
    $argStr = ($CmdArgs | ForEach-Object { if ($_ -match '\s') { '"' + $_ + '"' } else { $_ } }) -join ' '
    $p = Start-Process -FilePath $Exe -ArgumentList $argStr -NoNewWindow -PassThru -WorkingDirectory $Cwd
    $t0 = Get-Date
    while (-not $p.HasExited) {
        $el = [int]((Get-Date) - $t0).TotalSeconds
        if ($el -ge $TimeoutSec) { try { $p.Kill($true) } catch {}; return 124 }
        Write-VIAProgress -Activity 'VIA 加速器看門狗' -Status "$Name · $el s / $TimeoutSec s" -Percent ([int](100 * $el / $TimeoutSec))
        Start-Sleep -Milliseconds 800
    }
    Write-Progress -Id 11 -Activity 'VIA 加速器看門狗' -Completed
    return $p.ExitCode
}

function Invoke-VIAParallel {
    # 并行原語(ForEach-Object -Parallel 包裝;PS7)
    param([object[]]$Items, [scriptblock]$Body, [int]$Throttle = 8)
    if (-not $Items) { return @() }
    $Items | ForEach-Object -Parallel $Body -ThrottleLimit $Throttle
}

function Get-VIAAccelRoster { $script:VIA_ACCEL20 }

# 批366 零跳出閘(PS 側):VIA_NO_OPEN=1 時 Start-Process/Invoke-Item 之頁面目標(.html/.htm/.url/http)靜默略過;
# 其餘目標(python 工人/exe)全參數直通=ProxyCommand 產生之代理(保留原 cmdlet 全部參數集);缺席/失敗=graceful 不裝
function Test-VIAPageTarget { param([string]$T) if (-not $T) { return $false }; return ($T -match '^(https?:|file:)' -or $T -match '\.(html?|url|svg|pdf)$') }
try {
    foreach ($cmdName in @('Start-Process', 'Invoke-Item')) {
        $orig = Get-Command -Name $cmdName -CommandType Cmdlet -ErrorAction Stop
        $md = New-Object System.Management.Automation.CommandMetaData($orig)
        $body = [System.Management.Automation.ProxyCommand]::Create($md)
        $probe = if ($cmdName -eq 'Start-Process') { '$PSBoundParameters["FilePath"]' } else { '($PSBoundParameters["Path"] + $PSBoundParameters["LiteralPath"])' }
        $guard = '$script:__viaSkip = ($env:VIA_NO_OPEN -eq "1" -and (Test-VIAPageTarget ("" + ' + $probe + '))); if ($script:__viaSkip) { Write-Host ("  [VIA_NO_OPEN] 抑制跳出 " + ' + $probe + ') -ForegroundColor DarkGray; return }'
        $body = $body -replace 'begin\s*\{', ('begin { ' + $guard)
        $body = $body -replace 'process\s*\{', 'process { if ($script:__viaSkip) { return }'
        $body = $body -replace 'end\s*\{', 'end { if ($script:__viaSkip) { return }'
        Invoke-Expression ("function global:" + $cmdName + " { " + $body + " }")
    }
} catch { }

}
# ===== [VIA:PS-ACCEL-MODULE:END] =====
