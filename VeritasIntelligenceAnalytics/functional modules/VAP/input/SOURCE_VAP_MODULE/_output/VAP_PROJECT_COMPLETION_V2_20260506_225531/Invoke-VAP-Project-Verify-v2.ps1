#Requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Python = "C:\\Users\\tonyk\\envs\\via_core_312\\Scripts\\python.exe"
$Probe = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VAP\_output\VAP_PROJECT_COMPLETION_V2_20260506_225531\vap_project_completion_probe_v2.py"
& $Python $Probe
