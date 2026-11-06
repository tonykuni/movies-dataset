# VIA_SettleAll v0111(2026-11-06 · v0110 一字不動 · ⑭ 的「未登號」是查漏不是沒編號)

v0110 容器實跑 ⑭ 有 **144 列「未登號」**(VDF 78 · VRN-2 65 · VeritasCeleritas 1)。查 VCGC 編號冊:那些家族**都在 ENG 冊**
`VIA_NumberBooks/VIA_NumberBook_ENG_v0100.jsonl`(例 `VDF_ENG049_FiveDayFetch_v0100` = VIA-VDF-ENG015 · 2026-09-28;`VRN_ENG017_…` = VIA-VRN-ENG003;`VeritasCeleritas_v1141` = VIA-SUP-ENG013),
v0110 只讀 MDL 冊。v0111 兩本一起讀(各一次 · 快取),**VCGC 冊零寫入、不跑編號**。

容器實跑 ⑭(只跑 ⑭ · 所以 VDF STATUS ⚪):**508 列 · 未登號 0** · 🟢 279(VCGC 功能帳 · 含剛登的 MCP 伺服器 family:CGC_MDL279_MCPServer added GREEN 2026-11-06T14:02Z)🔴 4(VCGC 功能帳 2026-11-01 的 DeckServer v0161 · TestAuto v0106 · NumberingSystem v0119 · NumberGrant v0100)⚪ 225 · AST 錯 0 · 5 秒。
自測 41 / 41(㉘ 加:ENG 冊查得到 · MDL 冊沒有的不冒充)。欄位 / 來源 / 燈規則同 `VIA_SettleAll_v0110.md`。

## 桌機一行(PowerShell 7 · 從檔案複製 · 取代 v0110 那行)

```powershell
$r="$HOME\OneDrive\Documents\movies-dataset";$t="$HOME\Downloads\VIA_Settle_v0111";git -C $r fetch -q origin claude/optimistic-goodall-yhalc5;git -C $r archive --format=zip -o "$t.zip" FETCH_HEAD VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_SettleAll_v0111.py;Expand-Archive "$t.zip" $t -Force;$f="$t\VeritasIntelligenceAnalytics\docs\handoff\ai\VIA_SettleAll_v0111.py";if((Get-FileHash -InputStream ([IO.MemoryStream]::new([byte[]]([IO.File]::ReadAllBytes($f) -ne 13)))).Hash-eq'D04B90BD5A302A9D28628EBEF21BD16C5B7A48EAE8A24A6DC73114355F95CD91'){python $f --root $r}else{'[RED] SettleAll SHA-256 mismatch - not run'}
```
