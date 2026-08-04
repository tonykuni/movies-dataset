# VIA Evolving SSOT Engine v0100

def 目的：將 HTML / MD / JSON / CSV / XLSX / PY / PS1 / PDF / DOCX / ZIP / 圖片 / 資料夾，全部讀成同一張 VIA SSOT Matrix。

def 安全政策：read-only、append-only output、no delete、no subprocess、no network、no canonical mutation。

def 建議執行：
```powershell
$py = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\_envs\via_operation_optimizer_2026\Scripts\python.exe"
$engine = "C:\Users\tonyk\Downloads\VIA_Evolving_SSOT_Engine_v0100.py"
$pathList = "C:\Users\tonyk\Downloads\VIA_Evolving_SSOT_Input_Paths_20260702.txt"
$out = "C:\Users\tonyk\Downloads\VIA_Evolving_SSOT_Output"

& $py $engine --path-list $pathList --output-root $out
```

def 輸出：
- VIA_Evolving_SSOT_Matrix.csv
- VIA_Evolving_SSOT_Matrix.json
- VIA_Evolving_SSOT_Matrix.parquet（若 pandas/pyarrow 可用）
- VIA_Evolving_SSOT_Matrix.html
- VIA_Evolving_SSOT_RunManifest.json
