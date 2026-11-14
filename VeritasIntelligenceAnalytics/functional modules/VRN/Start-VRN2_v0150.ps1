#requires -Version 7.0
# [VIA:ACCEL-BRIDGE] 沿用本機既有 PS7 模板；本檔提供啟動進度與心跳。
param(
    [string]$Launcher = "$PSScriptRoot\ActivateVRN-2_v0150.py",
    [string]$ViaRoot = "C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics",
    [string]$Python = "$env:USERPROFILE\envs\via_core\Scripts\python.exe",
    [int]$StartupTimeoutSeconds = 120
)
$ErrorActionPreference = 'Stop'
$Template = Join-Path $ViaRoot 'supportive modules\ps7\VeritasCeleritas.PS7.Template.ps1'
$LogFolder = Join-Path $env:TEMP 'VIA_progress\vrn2_desktop_v0150'
$LogFile = Join-Path $LogFolder ('Startup_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.log')
$Process = $null
$Ready = $false

try {
    New-Item -ItemType Directory -Path $LogFolder -Force | Out-Null
    Write-Progress -Id 149 -Activity 'VRN-2 桌面啟動' -Status '檢查啟動器與環境' -PercentComplete 5
    if (-not (Test-Path -LiteralPath $Launcher -PathType Leaf)) { throw "找不到 $Launcher" }
    if (-not (Test-Path -LiteralPath $ViaRoot -PathType Container)) { throw "專案根不存在：$ViaRoot" }
    if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
        $Candidate = Get-Command python -CommandType Application -ErrorAction SilentlyContinue |
            Where-Object { $_.Source -notmatch '[\\/]WindowsApps[\\/]' } | Select-Object -First 1
        if (-not $Candidate) { throw '找不到可用 Python。' }
        $Python = $Candidate.Source
    }
    Remove-Item Env:\VIA_NO_OPEN -ErrorAction SilentlyContinue
    $env:VIA_ROOT = $ViaRoot
    $env:PYTHONUTF8 = '1'
    $env:PYTHONIOENCODING = 'utf-8'
    $env:VIA_VRN2_PS_TEMPLATE_LOADED = '0'
    if (Test-Path -LiteralPath $Template -PathType Leaf) {
        . $Template
        $env:VIA_VRN2_PS_TEMPLATE_LOADED = '1'
        Write-Host '[GREEN] 已載入既有 PS7 加速模板。' -ForegroundColor Green
    } else {
        Write-Host '[YELLOW] 未找到本機 PS7 模板；工作台將明示未收到載入證據。' -ForegroundColor Yellow
    }
    & $Python -X utf8 $Launcher --selftest
    if ($LASTEXITCODE -ne 0) { throw '內嵌雜湊自測未通過。' }
    Write-Progress -Id 149 -Activity 'VRN-2 桌面啟動' -Status '自測完成，啟動 WebView2' -PercentComplete 30

    $Info = [System.Diagnostics.ProcessStartInfo]::new()
    $Info.FileName = $Python
    $Info.UseShellExecute = $false
    $Info.RedirectStandardOutput = $true
    $Info.RedirectStandardError = $true
    $Info.StandardOutputEncoding = [System.Text.UTF8Encoding]::new($false)
    $Info.StandardErrorEncoding = [System.Text.UTF8Encoding]::new($false)
    foreach ($Argument in @('-X','utf8',$Launcher,'--root',$ViaRoot)) { $Info.ArgumentList.Add($Argument) }
    $Process = [System.Diagnostics.Process]::new()
    $Process.StartInfo = $Info
    [void]$Process.Start()
    $Clock = [System.Diagnostics.Stopwatch]::StartNew()
    $OutTask = $Process.StandardOutput.ReadLineAsync()
    $ErrTask = $Process.StandardError.ReadLineAsync()
    $OutDone = $false
    $ErrDone = $false
    while (-not ($Process.HasExited -and $OutDone -and $ErrDone)) {
        if (-not $OutDone -and $OutTask.IsCompleted) {
            $Line = $OutTask.GetAwaiter().GetResult()
            if ($null -eq $Line) { $OutDone = $true } else {
                Add-Content -LiteralPath $LogFile -Value $Line -Encoding utf8
                Write-Host $Line
                if ($Line.StartsWith('VRN2_UI_READY ')) {
                    $Ready = $true
                    Write-Progress -Id 149 -Activity 'VRN-2 桌面啟動' -Status 'HTML / Python 橋接完成' -PercentComplete 100 -Completed
                    Write-Host '[GREEN] 桌面 HTML U/I 已連線；資料擷取進度請看畫面百分比。' -ForegroundColor Green
                } elseif ($Line.StartsWith('VRN2_JOB_PROGRESS ')) {
                    $JobStage = $Line.Substring('VRN2_JOB_PROGRESS '.Length) | ConvertFrom-Json
                    Write-Progress -Id 151 -Activity 'VRN-2 資料擷取流程' -Status $JobStage.label -PercentComplete $JobStage.percent
                    if ($JobStage.lamp -eq 'RED' -or $JobStage.percent -ge 100) { Write-Progress -Id 151 -Activity 'VRN-2 資料擷取流程' -Completed }
                } elseif ($Line.StartsWith('VRN2_STARTUP ')) {
                    $Stage = $Line.Substring('VRN2_STARTUP '.Length) | ConvertFrom-Json
                    Write-Progress -Id 149 -Activity 'VRN-2 桌面啟動' -Status $Stage.stage -PercentComplete $Stage.percent
                }
                $OutTask = $Process.StandardOutput.ReadLineAsync()
            }
        }
        if (-not $ErrDone -and $ErrTask.IsCompleted) {
            $Line = $ErrTask.GetAwaiter().GetResult()
            if ($null -eq $Line) { $ErrDone = $true } else {
                Add-Content -LiteralPath $LogFile -Value $Line -Encoding utf8
                Write-Host $Line -ForegroundColor Yellow
                $ErrTask = $Process.StandardError.ReadLineAsync()
            }
        }
        if (-not $Ready -and -not $Process.HasExited -and $Clock.Elapsed.TotalSeconds -gt $StartupTimeoutSeconds) {
            $Process.Kill($true)
            throw "桌面啟動超過 $StartupTimeoutSeconds 秒且未握手，已停止本次啟動；日誌：$LogFile"
        }
        if (-not $Ready) {
            Write-Progress -Id 150 -Activity '啟動心跳（不虛增百分比）' -Status ("等待 HTML 就緒 · {0:N0} 秒" -f $Clock.Elapsed.TotalSeconds) -PercentComplete -1
        }
        Start-Sleep -Milliseconds 100
    }
    $Process.WaitForExit()
    if ($Process.ExitCode -ne 0) { throw "桌面程序退出碼 $($Process.ExitCode)；日誌：$LogFile" }
} catch {
    Write-Host ('[RED] ' + $_.Exception.Message) -ForegroundColor Red
    Write-Host "啟動日誌：$LogFile" -ForegroundColor Yellow
} finally {
    Write-Progress -Id 149 -Activity 'VRN-2 桌面啟動' -Completed
    Write-Progress -Id 150 -Activity '啟動心跳' -Completed
    Write-Progress -Id 151 -Activity 'VRN-2 資料擷取流程' -Completed
    if (Get-Command Restore-CeleritasPS7 -ErrorAction SilentlyContinue) { Restore-CeleritasPS7 }
    Write-Host 'VRN-2 已結束；PowerShell 保持開啟。' -ForegroundColor Cyan
    Read-Host '按 Enter 返回 PowerShell' | Out-Null
}
