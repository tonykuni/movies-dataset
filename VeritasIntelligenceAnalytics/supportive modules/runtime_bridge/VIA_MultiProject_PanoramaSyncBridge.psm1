# VIA MultiProject Panorama Sync Bridge
# Generated: 2026-06-17 02:35:01

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
function def_InvokeVIAMultiProjectPanoramaSync {
    param(
        [string]$ScriptPath = "",
        [int]$TimeoutSec = 180
    )
    $pwsh = Get-Command pwsh -ErrorAction SilentlyContinue
    if (-not $pwsh) {
        return [pscustomobject]@{Status="FAIL_PWSH_MISSING"; Message="pwsh not found."}
    }
    $out = Join-Path "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\tools\VIA_MultiProject_PanoramaSync\runs\RUN_20260617_023145_VIA_MULTIPROJECT_PANORAMA_SYNC\logs" ("bridge_multiproject_stdout_{0}.log" -f (Get-Date -Format "yyyyMMdd_HHmmss"))
    $err = Join-Path "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\tools\VIA_MultiProject_PanoramaSync\runs\RUN_20260617_023145_VIA_MULTIPROJECT_PANORAMA_SYNC\logs" ("bridge_multiproject_stderr_{0}.log" -f (Get-Date -Format "yyyyMMdd_HHmmss"))
    $args = @("-NoProfile","-ExecutionPolicy","Bypass","-File",$ScriptPath,"-OpenReport", "$true")
    $p = Start-Process -FilePath $pwsh.Source -ArgumentList $args -WorkingDirectory "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics" -RedirectStandardOutput $out -RedirectStandardError $err -PassThru -WindowStyle Hidden
    $finished = $p.WaitForExit($TimeoutSec * 1000)
    if (-not $finished) {
        return [pscustomobject]@{Status="WARN_TIMEOUT_CHILD_LEFT_RUNNING"; Stdout=$out; Stderr=$err}
    }
    return [pscustomobject]@{Status=("OK_EXIT_{0}" -f $p.ExitCode); ExitCode=$p.ExitCode; Stdout=$out; Stderr=$err}
}

function def_GetVIAMultiProjectPanoramaArtifacts {
    return [pscustomobject]@{
        RunRoot = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\tools\VIA_MultiProject_PanoramaSync\runs\RUN_20260617_023145_VIA_MULTIPROJECT_PANORAMA_SYNC"
        ReportHtml = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\tools\VIA_MultiProject_PanoramaSync\runs\RUN_20260617_023145_VIA_MULTIPROJECT_PANORAMA_SYNC\report\VIA_MultiProject_PanoramaSync_Report.html"
        MatrixCsv = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\tools\VIA_MultiProject_PanoramaSync\runs\RUN_20260617_023145_VIA_MULTIPROJECT_PANORAMA_SYNC\registry\VIA_MultiProject_PanoramaSync_Matrix.csv"
        ProjectCsv = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\tools\VIA_MultiProject_PanoramaSync\runs\RUN_20260617_023145_VIA_MULTIPROJECT_PANORAMA_SYNC\registry\VIA_Project_Status.csv"
        HistoryCsv = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\tools\VIA_MultiProject_PanoramaSync\runs\RUN_20260617_023145_VIA_MULTIPROJECT_PANORAMA_SYNC\registry\VIA_PastRun_HistoryLens.csv"
        TaskCsv = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\tools\VIA_MultiProject_PanoramaSync\runs\RUN_20260617_023145_VIA_MULTIPROJECT_PANORAMA_SYNC\registry\VIA_Flow_ProgressTasks.csv"
        TopLibsCsv = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\tools\VIA_MultiProject_PanoramaSync\runs\RUN_20260617_023145_VIA_MULTIPROJECT_PANORAMA_SYNC\registry\VIA_Top10_LocalFreeLibs_ByFunctionLanguage.csv"
        PM20Csv = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\tools\VIA_MultiProject_PanoramaSync\runs\RUN_20260617_023145_VIA_MULTIPROJECT_PANORAMA_SYNC\registry\VIA_Top20_EnterpriseForms_To_ProcessMining_Libs.csv"
        AnchorCsv = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\tools\VIA_MultiProject_PanoramaSync\runs\RUN_20260617_023145_VIA_MULTIPROJECT_PANORAMA_SYNC\registry\VIA_Project_AnchorMap.csv"
        EngineCsv = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\tools\VIA_MultiProject_PanoramaSync\runs\RUN_20260617_023145_VIA_MULTIPROJECT_PANORAMA_SYNC\registry\VIA_Engine_Module_Status.csv"
        CompletionCsv = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\tools\VIA_MultiProject_PanoramaSync\runs\RUN_20260617_023145_VIA_MULTIPROJECT_PANORAMA_SYNC\registry\VIA_Project_Completion_Status.csv"
        RiskTriageCsv = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\tools\VIA_MultiProject_PanoramaSync\runs\RUN_20260617_023145_VIA_MULTIPROJECT_PANORAMA_SYNC\registry\VIA_Risk_Triage_ByProject.csv"
        NextActionCsv = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\tools\VIA_MultiProject_PanoramaSync\runs\RUN_20260617_023145_VIA_MULTIPROJECT_PANORAMA_SYNC\plans\VIA_NextAction_ConvergencePlan.csv"
        SequentialPlan = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\tools\VIA_MultiProject_PanoramaSync\runs\RUN_20260617_023145_VIA_MULTIPROJECT_PANORAMA_SYNC\plans\VIA_Sequential_RepairPlan.csv"
        ParallelPlan = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\tools\VIA_MultiProject_PanoramaSync\runs\RUN_20260617_023145_VIA_MULTIPROJECT_PANORAMA_SYNC\plans\VIA_ParallelSafe_OptimizationPlan.csv"
    }
}

Export-ModuleMember -Function def_InvokeVIAMultiProjectPanoramaSync,def_GetVIAMultiProjectPanoramaArtifacts
