# Start-VIA-VDF-VRN.ps1 — 開 VDF 與 VRN 各自的 U/I(L119 各自入口;邏輯在 Invoke-VIA-Launch → 各 SystemManager)
# 2026-10-10:原檔三行換行遺失併成一行('…ps1'& pwsh …:PS7 把 & 當背景運算子,$L 傳不到後兩道)→ 拆回三行 · 補 PS-ACCEL 橋
# ===== [VIA:PS-ACCEL:v0101] PS 25 加速器橋(B531 全樹導入;graceful 缺席零影響) =====
try { $VIAPSAccelProbe = if ($PSScriptRoot) { $PSScriptRoot } else { 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics' }
  while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) { $m = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"; if (Test-Path $m) { . $m; break }; $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent } } catch { }
# ===== [VIA:PS-ACCEL:END] =====
$L = 'C:\Users\tonyk\Downloads\Invoke-VIA-Launch-v0111.ps1'
& pwsh -ExecutionPolicy Bypass -File $L -Sub VDF -Verb ui
& pwsh -ExecutionPolicy Bypass -File $L -Sub VRN -Verb ui
