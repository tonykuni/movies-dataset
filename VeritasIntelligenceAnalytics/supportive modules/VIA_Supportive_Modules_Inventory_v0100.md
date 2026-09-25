# VIA 支援性模組清冊 v0100(2026-08-18;操作員問「支援性模組有表列嗎」)

實體:頂層目錄 45 個 · 頂層引擎檔 28 支 · 命名冊 SUP 家族 737

## 一、頂層支援引擎(直屬檔)

| 檔 | 正典號 | 職能 |
|---|---|---|
| Invoke-VIA-CentralGovernanceManager.ps1 | — |  |
| Invoke-VIA-IntegrationFirstStep-Panorama-AIO-v0104.ps1 | — |  |
| Invoke-VIA-MarketFlow-AllInOne-v0112.ps1 | — |  |
| Invoke-VIA-PolyglotCheckTestRepair-v0101.ps1 | — |  |
| Invoke-VIA-SafePolyglotOptimizer-AIO-v0102.ps1 | — |  |
| Invoke-VIA-SafePolyglotOptimizer.ps1 | — |  |
| Invoke-VIA-Supportive-GitClone-StockDashboard.ps1 | — |  |
| Invoke-VIA-Supportive-InstallLaunch-StockDashboard.ps1 | — |  |
| Invoke-VIA-SupportiveCore-PromptInjection.ps1 | — |  |
| Invoke-VIA-UltimateEngineForge-AIO-v060.ps1 | — |  |
| Invoke-VeritasCodexNexus.ps1 | — |  |
| Invoke-VeritasNexusCore.ps1 | — |  |
| Invoke_VIA_SSD_Resource_Guard_v0100.py | — | SSD/CPU/DRAM 資源 Gate(TOOL-052) |
| VIA_DataTransformEngine.py | SUP_MDL116_DataTransformEngine |  |
| VIA_EnvManager.py | SUP_MDL117_EnvManager | 環境管理 |
| VIA_Final_Xbatch_100Symbol_FIX_AllInOne.ps1 | — |  |
| VIA_NetSupport.py | SUP_MDL145_NetSupport | 網路同意閘(VIA_NET_CONSENT) |
| VIA_Panorama_AST_RuntimeInjector.py | SUP_MDL148_PanoramaASTRuntimeInjector |  |
| VIA_RegistryCore_v1.py | SUP_MDL153_RegistryCoreV1 |  |
| VIA_Runtime_Bridge_All_in_One.py | SUP_MDL154_RuntimeBridgeAllInOne |  |
| VIA_SSOT_Unified.py | SUP_MDL155_SSOTUnified | SSOT 統一讀寫 |
| VIA_SuperAccel_Module.py | SUP_MDL737_SuperAccelModule | 統一加速器(平行/快取抓取/輔助安裝道)TOOL-051 |
| VIA_SupportiveModule_100Coverage_FIX_AllInOne.ps1 | — |  |
| VIA_Toolkit.py | SUP_MDL163_Toolkit | Top-10 graceful 取用(TOOL-040) |
| VeritasAegisNexus.py | SUP_MDL169_VeritasAegisNexus | 防護中樞 |
| VeritasCeleritas.py | SUP_MDL170_VeritasCeleritas | VDF 加速橋(vdf_fetch 快取重試去重) |
| email_case_tracker_v2.py | SUP_MDL565_EmailCaseTrackerV2 |  |
| via_manager.py | SUP_MDL735_Manager |  |

## 二、支援子系統目錄(頂層)

| 目錄 | 命名冊轄下家族數 |
|---|---|
| 10_Core_Runtime/ | 3 |
| 20_Registry_SSOT/ | 3 |
| 30_HardGate_Governance/ | 2 |
| 40_Environment_Health/ | 2 |
| 50_Protection_Acceleration/ | 2 |
| 60_PowerShell_Entry_Internal/ | 0 |
| 70_VRN_Rules/ | 20 |
| 80_VETF_Supportive_Sort/ | 10 |
| Dashboard_Format_Standardization/ | 5 |
| PMIS-Lite/ | 65 |
| TFE_Engine/ | 1 |
| VIA_AutoSandbox20_Runtime/ | 1 |
| VIA_Canonical_Units/ | 0 |
| VIA_Central_Governance/ | 0 |
| VIA_ContractEngine_v0200/ | 0 |
| VIA_Control_Tower/ | 1 |
| VIA_Decision_Studio/ | 0 |
| VIA_EngineForge/ | 0 |
| VIA_FlowSystem/ | 0 |
| VIA_Forge/ | 20 |
| VIA_Governance_Runtime/ | 7 |
| VIA_IF_Engine/ | 1 |
| VIA_OCR_Router/ | 1 |
| VIA_Optimizer_Suite/ | 1 |
| VIA_Pipeline/ | 4 |
| VIA_Rescue_Staging_20260802/ | 0 |
| VIA_SSOT/ | 0 |
| VIA_Standalone_Package_v0102/ | 7 |
| VIA_VHS/ | 1 |
| VIA_VVX/ | 1 |
| VIA_VisualLock/ | 0 |
| VMT_SuperBOM/ | 0 |
| VPNS/ | 1 |
| VRN_Helpers_Rescued/ | 2 |
| accelerator/ | 10 |
| audit_tools/ | 48 |
| environment/ | 15 |
| network/ | 58 |
| notes/ | 0 |
| parameters/ | 0 |
| registry/ | 0 |
| runtime_bridge/ | 10 |
| specs/ | 0 |
| ssot/ | 53 |
| ui_support/ | 33 |

## 三、既有三層冊(互補)

1. 命名冊 TOOL-047:SUP 家族全數正典號(U/I 板 SYS=SUP 即點即濾)
2. 介面合約冊 TOOL-041:SUPPORT 域函式/類/import 零執行合約
3. 功能群審計 TOOL-052:12 功能群聚類+資源分級

> 紅線提醒:正典倉在 `%USERPROFILE%\movies-dataset`;訊息中出現的
> `Downloads\movies-dataset` 若為第二份克隆=「不開第三根」紅線鄰域,請確認。