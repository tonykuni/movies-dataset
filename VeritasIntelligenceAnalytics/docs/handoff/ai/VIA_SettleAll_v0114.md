# VIA_SettleAll v0114(操作員 2026-11-06「啟動手機可同步監控操作功能」· v0113 一字不動)

三張矩陣 HTML(⑫ 系統 · ⑭ 模組 · VCGC 站表)加 viewport、表格各自 overflow-x、窄螢幕字級;**內容與欄位不變**。
容器 Chromium 390px 實測:三張都不再橫向捲動、0 JS 錯誤。手機監控快照頁(Artifact · 私人連結)另由收據生成:https://claude.ai/artifact/2cq1KMq1mpWwuMfGfxsUu9

自測 43 / 43。容器實跑 ⑭ 509 列 · ⑫ 11 列。

## 桌機一行(PowerShell 7 · 從檔案複製 · 取代 v0113 那行)

```powershell
$r="$HOME\OneDrive\Documents\movies-dataset";$t="$HOME\Downloads\VIA_Settle_v0114";git -C $r fetch -q origin claude/optimistic-goodall-yhalc5;git -C $r archive --format=zip -o "$t.zip" FETCH_HEAD VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_SettleAll_v0114.py;Expand-Archive "$t.zip" $t -Force;$f="$t\VeritasIntelligenceAnalytics\docs\handoff\ai\VIA_SettleAll_v0114.py";if((Get-FileHash -InputStream ([IO.MemoryStream]::new([byte[]]([IO.File]::ReadAllBytes($f) -ne 13)))).Hash-eq'594064C04294B4E21800D4D589461F9C0F729A9627C24DE962F06B1364B26085'){python $f --root $r}else{'[RED] SettleAll SHA-256 mismatch - not run'}
```
