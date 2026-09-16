# VIA B529：NLP文字修復／內文證據摘要 → VRN → VDF
# 用法：在 Windows PowerShell 直接貼上本檔全部內容，或執行 .\VIA_NLP_VRN_VDF_B529.ps1
$ErrorActionPreference = 'Continue'
$VIA_CANDIDATES = @(
    'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics',
    'C:\Users\tonyk\Documents\movies-dataset\VeritasIntelligenceAnalytics'
)
$VIA = $VIA_CANDIDATES | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $VIA) { throw '找不到 VIA 母系統資料夾；請把 $VIA_CANDIDATES 改成實際 VeritasIntelligenceAnalytics 路徑。' }
$INPUT = 'C:\測試樣本報告'
if (-not (Test-Path -LiteralPath $INPUT -PathType Container)) { throw "找不到輸入資料夾：$INPUT" }

Set-Location -LiteralPath $VIA
. .\Register-VIA-Commands-v0208.ps1
$env:VIA_NO_OPEN = '1'
$env:VIA_FAMILY = 'vrn'

Write-Host "[VIA] 母系統：$VIA" -ForegroundColor Cyan
Write-Host "[VIA] 輸入：$INPUT" -ForegroundColor Cyan
Write-Host '[VIA] 啟動 NLP→VRN ENG072/ENG073→VDF ENG087；網路預設關閉。' -ForegroundColor Cyan

# 單一中央入口：
# - NLP TextProcessor 正規化文字
# - evidence-based summarization，保留 source_span
# - ENG072 首頁擷取
# - ENG073 寫入 vrn_reports.duckdb
# - VDF ENG087 唯讀驗收三份市場清單
NLP串接 -In $INPUT -Force
$PIPELINE_RC = $LASTEXITCODE

Write-Host "[VIA] NLP→VRN→VDF pipeline rc=$PIPELINE_RC" -ForegroundColor $(if ($PIPELINE_RC -eq 0) { 'Green' } else { 'Yellow' })
Write-Host '[VIA] 只讀檢查資料庫表與中央治理狀態。' -ForegroundColor Cyan
庫況 -Tables
中央控管 check

if ($PIPELINE_RC -eq 0) {
    Write-Host '[VIA] GREEN：NLP、VRN 入庫與 VDF 三清單均通過。' -ForegroundColor Green
} else {
    Write-Host '[VIA] 非 GREEN：請查看 VIA_Reports\vrn\nlp_pipeline\NLP_VRN_VDF_latest.json 的 vdf_gate.blockers；文字與摘要結果仍已保留在資料庫。' -ForegroundColor Yellow
}
exit $PIPELINE_RC
