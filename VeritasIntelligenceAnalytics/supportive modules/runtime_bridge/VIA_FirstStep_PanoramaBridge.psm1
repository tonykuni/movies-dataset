# VIA FirstStep Panorama Bridge
# Generated: 2026-06-17 01:25:55
# Import:
# Import-Module "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\tools\VIA_FirstStep_PanoramaSandbox\bridge\VIA_FirstStep_PanoramaBridge.psm1" -Force

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
function def_InvokeVIAFirstStep {
    param(
        [string]$ScriptPath = "",
        [int]$TimeoutSec = 180
    )
    $pwsh = Get-Command pwsh -ErrorAction SilentlyContinue
    if (-not $pwsh) {
        return [pscustomobject]@{Status="FAIL_PWSH_MISSING"; Message="pwsh not found."}
    }
    $out = Join-Path "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\tools\VIA_FirstStep_PanoramaSandbox\runs\RUN_20260617_012548_VIA_FIRSTSTEP_PANORAMA_SANDBOX\logs" ("bridge_firststep_stdout_{0}.log" -f (Get-Date -Format "yyyyMMdd_HHmmss"))
    $err = Join-Path "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\tools\VIA_FirstStep_PanoramaSandbox\runs\RUN_20260617_012548_VIA_FIRSTSTEP_PANORAMA_SANDBOX\logs" ("bridge_firststep_stderr_{0}.log" -f (Get-Date -Format "yyyyMMdd_HHmmss"))
    $args = @("-NoProfile","-ExecutionPolicy","Bypass","-File",$ScriptPath,"-OpenReport", "$true")
    $p = Start-Process -FilePath $pwsh.Source -ArgumentList $args -WorkingDirectory "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics" -RedirectStandardOutput $out -RedirectStandardError $err -PassThru -WindowStyle Hidden
    $finished = $p.WaitForExit($TimeoutSec * 1000)
    if (-not $finished) {
        return [pscustomobject]@{Status="WARN_TIMEOUT_CHILD_LEFT_RUNNING"; Stdout=$out; Stderr=$err}
    }
    return [pscustomobject]@{Status=("OK_EXIT_{0}" -f $p.ExitCode); ExitCode=$p.ExitCode; Stdout=$out; Stderr=$err}
}

function def_GetVIAFirstStepArtifacts {
    return [pscustomobject]@{
        RunRoot = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\tools\VIA_FirstStep_PanoramaSandbox\runs\RUN_20260617_012548_VIA_FIRSTSTEP_PANORAMA_SANDBOX"
        ReportHtml = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\tools\VIA_FirstStep_PanoramaSandbox\runs\RUN_20260617_012548_VIA_FIRSTSTEP_PANORAMA_SANDBOX\report\VIA_FirstStep_PanoramaSandbox_Report.html"
        MatrixCsv = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\tools\VIA_FirstStep_PanoramaSandbox\runs\RUN_20260617_012548_VIA_FIRSTSTEP_PANORAMA_SANDBOX\registry\VIA_FirstStep_Panorama_Matrix.csv"
        CommandReviewCsv = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\tools\VIA_FirstStep_PanoramaSandbox\runs\RUN_20260617_012548_VIA_FIRSTSTEP_PANORAMA_SANDBOX\registry\VIA_CommandReview_StrengthWeakness.csv"
        TopLibsCsv = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\tools\VIA_FirstStep_PanoramaSandbox\runs\RUN_20260617_012548_VIA_FIRSTSTEP_PANORAMA_SANDBOX\registry\VIA_Top10_LocalFreeLibs_ByFunctionLanguage.csv"
        ProcessMiningTop20Csv = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\tools\VIA_FirstStep_PanoramaSandbox\runs\RUN_20260617_012548_VIA_FIRSTSTEP_PANORAMA_SANDBOX\registry\VIA_Top20_EnterpriseForms_To_ProcessMining_Libs.csv"
        FirstStepCommand = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\tools\VIA_FirstStep_PanoramaSandbox\runs\RUN_20260617_012548_VIA_FIRSTSTEP_PANORAMA_SANDBOX\plans\VIA_Strongest_FirstStep_Command.ps1"
    }
}

Export-ModuleMember -Function def_InvokeVIAFirstStep,def_GetVIAFirstStepArtifacts
