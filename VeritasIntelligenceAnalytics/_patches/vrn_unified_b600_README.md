# 批600 · vrn_unified 假紅修復

## Root cause
- Spec `vrn_unified.engine.verb` 為 `[]` → matrix/`--apply` 無 argv
- Engine 自訂句 `[ERROR] at least one --in file/directory is required` 不進 MDL148 `ARGERR_RX` → 誤判 RED

## Fix
1. Spec: `verb` → `["--selftest"]`（與 `vrn_logic` / `vrn_pdfplus` 同型）
2. Bus → `CGC_MDL148_EngineBus_v0128.py`：`NEED_INPUT_RX` → `ABSENT`（缺參數,不是壞掉）

## Apply on Tony-NB
```powershell
# 同步本 branch 後
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
via-bus matrix --ids vrn_unified --apply
# expect GREEN (selftest)
Get-ChildItem -LiteralPath 'C:\測試樣本報告' | Format-Table Name,Length,LastWriteTime
via-vrnlogic --selftest
via-vrnrules selftest
via-vrnval --help
```

Files prepared on agent box (push next if MCP size allows):
- `supportive modules/registry/VIA_InputConsole_Spec_v0100.json`
- `supportive modules/CGC/CGC_MDL148_EngineBus_v0128.py` (path may vary — match tree)
