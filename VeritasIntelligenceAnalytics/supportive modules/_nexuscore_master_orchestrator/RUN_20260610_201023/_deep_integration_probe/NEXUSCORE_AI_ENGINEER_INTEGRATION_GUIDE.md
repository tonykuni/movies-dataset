# NexusCore AI / Engineer Integration Guide

Generated: 20260610_201023

## Current State

```text
NEXUSCORE_MASTER_ORCHESTRATOR_READY
Install LOCKED
Aegis gates environment modification.
Celeritas accelerates only after policy check.
EnvManager routes tools by target environment.
```

## Rules

- Do not call Python supportive tools directly.
- Do not pip install directly.
- Do not modify global Python.
- Do not modify PATH globally.
- Do not run Celeritas Install without Aegis Risk LOW.
- Do not unlock Install unless DownloadOnly and Validate are PASS.

## Safe Chain

```text
Matrix -> ScanOnly -> BuildRegistry -> HardGate -> EnvPlan -> AccelerationPlan -> DownloadOnly -> Validate
```