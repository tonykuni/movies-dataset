# VIA_SettleAll v0112(桌機 2026-11-06 22:19 v0111 貼回 · v0111 一字不動)

> **已被 v0113 取代**(一行請用 `VIA_SettleAll_v0113.md`)。

## 桌機 v0111 實錄(真相)

| 步 | 燈 | 實錄 |
|---|---|---|
| ③ 同步 | 🟡 | **還原成功 26 支 git rm 的舊版 + 2 本壞 JSON**(SubsystemSeat · Lessons_Ledger)。剩 **other 2 = `VRN_SystemManager_v0152.py` / `v0153.py` 被改了內容**(+220 / −61 · +939 / −73 行;家族尾版 v0254 · 分支 v0261)→ 不合併 → 桌機仍在 main 122bab5f8 · 落後 254 提交 |
| ④ ⑥ ⑬ | 🟡 | 因 ③ 沒合併不在舊樹上跑(正確) |
| ⑤ VRN | 🟡 | 收尾收據 DATA_GAP(資料源 3 · VRN-2 待修 0 · 2026-11-04)|
| ⑦ Graphify | 🟡 | VRN 🟢 VDF 🟢 · VRN_Shared / VCGC 看門狗不跑(可用 3.40 GB)|
| ⑧ VQG | 🟡 | 家 `via_database\vdf_database` DERIVE_READY 351 日線 · closeout YELLOW |
| ⑨ Agent OS | 🟡 | 48 項 · 失敗 0 · 錯誤 1(WinError 1314 symlink 權限 = 環境)· skills / status / vcgc-status rc 0 |
| ⑭ 模組矩陣 | 🟢 | **527 列**(桌機 VRN-2 有 116 家族:多 26 支啟動器解出來的 runtime 版本)· 🟢 280 🟡 1 🔴 1 ⚪ 245 · AST 錯 0 · 未登號 148(桌機編號冊是舊的 · 同步後歸零)|

## v0112 改什麼

- ③ 新類 **frozen**:已發布的**非尾版** `_vNNNN.py / .ps1`(同夾有更高版號)被改了內容 → 先備份桌機版到 `VIA_Reports/settle/frozen_version_backup/<檔>.<時間>.desktop`,再 `git checkout HEAD -- 檔`(可回滾 = 把備份放回)。
  理由:已發布版本的 bytes 以 git 為正本(只增規則 · 薄尾鏈引用它們);**尾版**被改仍算 other(可能是真的在做事 · 不動)。
- ③ 把**未追蹤檔**(桌機 404 個)依夾計數 + 程式 / 冊類檔名(前 40)寫進報告(只讀 · 不加不刪)→ 下一輪就看得到桌機 / Manus 新增了什麼。
- 自測 41 / 41(㉖ 加 frozen 判對 · 尾版改了仍 other · 備份在 · 未追蹤摘要在)。

## 桌機一行(PowerShell 7 · 從檔案複製 · 取代 v0111 那行)

```powershell
$r="$HOME\OneDrive\Documents\movies-dataset";$t="$HOME\Downloads\VIA_Settle_v0112";git -C $r fetch -q origin claude/optimistic-goodall-yhalc5;git -C $r archive --format=zip -o "$t.zip" FETCH_HEAD VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_SettleAll_v0112.py;Expand-Archive "$t.zip" $t -Force;$f="$t\VeritasIntelligenceAnalytics\docs\handoff\ai\VIA_SettleAll_v0112.py";if((Get-FileHash -InputStream ([IO.MemoryStream]::new([byte[]]([IO.File]::ReadAllBytes($f) -ne 13)))).Hash-eq'322F1D0B1B23F4387F1921A8A553340195C49AF97E75FADD14C38D388B1DD587'){python $f --root $r}else{'[RED] SettleAll SHA-256 mismatch - not run'}
```

預期:③ 「從 HEAD 還原:改了的凍結版 2」→ 合併 origin 成功 → ④ VDF ui v0168 · ⑥ VCGC v0192 · ⑬ 98 引擎 · ⑭ 第一欄全部有燈 · MCP 伺服器有燈 → 兩張 HTML → 貼回包。
