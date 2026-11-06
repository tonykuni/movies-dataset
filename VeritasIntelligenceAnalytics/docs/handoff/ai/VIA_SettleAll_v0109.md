# VIA_SettleAll v0109(桌機 v0108 貼回 2026-11-06 21:04 · 兩個阻塞的真相)

| 真相 | 證據 | v0109 怎麼修(可回滾)|
|---|---|---|
| 28 支「other」= **桌機把 VRN 舊版整支刪掉並已 `git rm`** | git 狀態碼 `D ` · +0 / −1116 行(ENG062 v0101–0112 · ENG397 v0113–0128 · SystemManager v0152–0153)| 新類別 **deleted → 從 HEAD 還原**(檔都在 git 裡 · 零資料損失;要回滾再刪一次即可)。刪已發布版本違反只增規則、薄尾可能還引用它們 |
| 桌機 VCGC 主控台 rc 1 的壞 JSON = **`VIA_VCGC_SubsystemSeat_v0100.json` 第 8 行** | 壞 JSON 掃描指名 · state 冊 | stash 前把 receipt / state 類裡 json.loads 不過的冊**先備份到 `VIA_Reports\settle\broken_json_backup\` 再還原 HEAD 版** |

兩件修完 ③ 就能合併 → ④ VDF ui · ⑥ VCGC · MCP 全部有燈。

另新增:
- ⑫ 矩陣多「**VCGC 編號 · 編號時間**」欄(從 VIA_NumberBook_MDL 冊查各系統尾版的 VIA-…-MDL 號與 numbered_at)—— 成功部分用 VCGC 的名字與版號記。
- **⑬ VDF 全引擎自測掃描**(操作員「實測 VDF 所有引擎都可跑」):VDF 根 + VDF/engine 每個家族尾版跑 `--selftest`(2 線 · 每支 120 秒 · 總預算 20 分 · `--vdf-budget`)→ `VIA_Reports\settle\VDF_Engines_Matrix_latest.json / .md`(🟢 rc 0 · 🟡 rc 2 · 🔴 其他 · 附最後一行)+ 系統矩陣 VDF 子列;舊樹不掃(同 ④)。
- 容器實跑(預算 240 秒):**98 家族 · 🟢 74 🟡 9 🔴 13 · 預算外 2**(紅 = 容器缺 yfinance / fastparquet / 無網 · 桌機環境不同)。

自測 39 / 39(新:deleted 類還原 · 壞 JSON 備份還原 · VCGC 編號欄 · 引擎掃描三色)。

## 桌機一行(PowerShell 7 · 從檔案複製)

```powershell
$r="$HOME\OneDrive\Documents\movies-dataset";$t="$HOME\Downloads\VIA_Settle_v0109";git -C $r fetch -q origin claude/optimistic-goodall-yhalc5;git -C $r archive --format=zip -o "$t.zip" FETCH_HEAD VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_SettleAll_v0109.py;Expand-Archive "$t.zip" $t -Force;$f="$t\VeritasIntelligenceAnalytics\docs\handoff\ai\VIA_SettleAll_v0109.py";if((Get-FileHash -InputStream ([IO.MemoryStream]::new([byte[]]([IO.File]::ReadAllBytes($f) -ne 13)))).Hash-eq'C8C529A6DE27F758C3FCAD1159AFE697A8D3E634C765DD2E0C0A14AEE331FFD1'){python $f --root $r}else{'[RED] SettleAll SHA-256 mismatch - not run'}
```

預期:③ 「從 HEAD 還原:刪掉的舊版 28 · 壞 JSON 1」→ 合併成功 → ④ VDF ui v0168 · ⑥ VCGC v0192 · ⑬ 98 個 VDF 引擎 · MCP 自測 全部有燈;矩陣綠的進只增帳。整輪約 25 分(⑬ 預算 20 分;`--vdf-budget 300` 可縮)。
