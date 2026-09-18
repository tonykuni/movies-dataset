# B600 + VRN samples/logic/val — executor status (2026-09-18 Asia/Taipei)

## Blocker
Executor Shell has **no machineId routing** to Tony-NB. All Shell runs on Linux box. Cannot list `C:\\測試樣本報告` or run `via-*` on the workstation from this agent.

## B600 vrn_unified fix (prepared + partially pushed)
Branch: `grok/vrn-unified-need-input-absent-20260918` (from governance `946132b0…`)
- Docs: `VeritasIntelligenceAnalytics/_patches/vrn_unified_b600_README.md` (committed)
- Patch kit: Apply-B600-vrn_unified.ps1 + CGC_MDL148_EngineBus_v0127_to_v0128.diff + _apply_bus_diff.py

Root cause: Spec `vrn_unified.engine.verb=[]` + custom `[ERROR] at least one --in…` not in ARGERR_RX → false RED.
Fix: verb=`["--selftest"]`; Bus v0128 NEED_INPUT_RX → ABSENT.

## VRN 邏輯庫 / 驗證法 (Register + Spec)
| Alias / cmd | Engine | Role / methods |
|---|---|---|
| `via-vrnlogic` / 邏輯庫 | `VRN_ENG082_ExtractionLogic_v*.py` | status / reset-backends / --selftest; ledger VIA_Reports\\vrn\\extraction_logic\\ |
| Spec `vrn_logic` | same ENG082 | matrix verb `--selftest` (十二檢) |
| `via-finlogic` / 財務邏輯 | `SUP_MDL748_FinancialLogicHub_v*.py` | status / opinion / rating / --selftest |
| `via-vrnuni` / 統一報告 | UnifiedReportEngine | -SelfTest / --in/--out |
| Spec `vrn_unified` | same | was verb:[] → should be --selftest (B600) |
| `via-vrnval` | → via-closeout vrn | MDL141 ClosingGate |
| `via-closeout` | `CGC_MDL141_ClosingGate_v*.py` | vrn/vap/all [--run] [--dir]; 五段鏈 → DONE/FAIL/PENDING |
| `via-vrnrules` | (SUP_MDL749 claimed) | **Not found** in Register tip; MDL748 present instead |

Hard rules: no talib; QuantGuard/VDF not mixed into this VRN path.

## Tony-NB (parent must run)
```powershell
Set-Location 'C:\\Users\\tonyk\\OneDrive\\Documents\\movies-dataset\\VeritasIntelligenceAnalytics'
git fetch origin grok/vrn-unified-need-input-absent-20260918
# checkout or copy _patches then:
pwsh -File .\\_patches\\Apply-B600-vrn_unified.ps1
. (Get-ChildItem .\\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
Get-ChildItem -LiteralPath 'C:\\測試樣本報告' | Format-Table Name,Length,LastWriteTime
via-vrnlogic --selftest
via-vrnval --dir 'C:\\測試樣本報告'
via-bus matrix --ids vrn_unified --apply
```
