@echo off
rem VIA WF 統一工作流啟動器 — 新模組家族一鍵(WorkflowEngine/ChipWar/TALib/MultiFactor/FlowSystem)
rem 用法:via-wf status ^| via-wf all ^| via-wf chipwar ^| via-wf mf ^| via-wf theory ^| via-wf everything
rem      via-wf vap probe ^| via-wf selftest ^| via-wf backends(引擎動詞全透傳)
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\VIA_WorkflowEngine.ps1" %*
