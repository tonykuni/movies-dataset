# NexusCore AI Onboarding Guide

## Purpose

This guide tells engineers and AI how to integrate and reason about Veritas supportive modules.

The approved flow is:

```text
Read_Me_VeritasNexusCore.md
    -> Invoke-VeritasNexusCore.ps1
    -> SSOT Registry
    -> VeritasAegisNexus.py HardGate
    -> EnvManager Plan
    -> VeritasCeleritas.py AccelerationPlan
    -> DownloadOnly / Install / Validate
    -> Final Matrix Report
```

## Absolute Rules

- Do not directly pip install.
- Do not pollute global Python.
- Do not skip Aegis.
- Do not run Celeritas install without HardGate.
- Do not install without InstallPlan.
- Do not modify environment when Risk is MEDIUM or HIGH.
- Do not treat missing HTML / JSON / CSV reports as complete.

## AI Reading Order

1. Read_Me_VeritasNexusCore.md
2. NEXUSCORE_TOOL_MATRIX.json
3. supportive_modules_registry.json
4. aegis_hardgate_report.json
5. env_manager_plan.json
6. celeritas_install_plan.json

## Tool Matrix

| Tool | Layer | Role | Status | Risk | Target Env |
| --- | --- | --- | --- | --- | --- |
| Read_Me_VeritasNexusCore | L0_SSOT_Documentation | Human and AI onboarding SSOT | FOUND | LOW | document |
| Invoke-VeritasNexusCore | L1_Control_Entry | Single PowerShell entry for all supportive modules | FOUND | LOW | PowerShell 7 |
| VeritasAegisNexus | L3_HardGate_Protection | Protection, network guard, environment risk gate | FOUND | LOW | via_core_312 |
| VeritasCeleritas | L5_Acceleration_InstallPlanner | Acceleration, cache, wheelhouse, retry, download and install planning | FOUND | LOW | via_core_312 |

## Required NexusCore Actions

```powershell
.\Invoke-VeritasNexusCore.ps1 -Action ScanOnly
.\Invoke-VeritasNexusCore.ps1 -Action BuildRegistry
.\Invoke-VeritasNexusCore.ps1 -Action HardGate
.\Invoke-VeritasNexusCore.ps1 -Action EnvPlan
.\Invoke-VeritasNexusCore.ps1 -Action AccelerationPlan
.\Invoke-VeritasNexusCore.ps1 -Action DownloadOnly
.\Invoke-VeritasNexusCore.ps1 -Action Install
.\Invoke-VeritasNexusCore.ps1 -Action Validate
.\Invoke-VeritasNexusCore.ps1 -Action Matrix
```

## Final Ready State

```text
Status   : NEXUSCORE_SUPPORTIVE_LAYER_READY
Risk     : LOW
Registry : READY
HardGate : READY
EnvMgr   : READY
Aegis    : READY
Celeritas: READY
Fail     : 0
Warn     : 0
```