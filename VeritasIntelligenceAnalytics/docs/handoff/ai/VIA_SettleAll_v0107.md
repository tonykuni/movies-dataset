# VIA_SettleAll v0107(桌機 v0106 兩次貼回 2026-11-06 19:33 / 19:41)

v0106 把整輪從 ~50 分壓到 **5 分 → 2.5 分**(三張圖沿用 0 秒 · VCGC 那張可用 3.4 GB < 6 不跑 · ⓫ 第二次快取命中 5,087 檔 7 秒 · ④ ⑥ 不在舊樹白跑)。還差兩處,v0107 補:

| 問題 | 原因 | v0107 |
|---|---|---|
| ③ 28 個 other 的差異 `+?/−?`、沒有樣本 | 桌機那些檔已 `git add` 進索引,`git diff` 只比工作樹對索引 → 空 | 改比 **HEAD**(`git diff HEAD --numstat / -U0`)· 每檔附 git 狀態碼 XY |
| 桌機 VCGC 主控台 rc 1 的壞 JSON 一直沒指名 | ⑥ 被略過(舊樹)時壞 JSON 掃描也沒跑 | ⑥ 不論跑不跑先掃小 JSON(registry 冊 · VIA_Reports/vcgc · .via · 只讀 · 幾秒),壞的印檔名 + 行列 |

自測 35 / 35(⑩ 改成「已 git add 的改動」情境 · 對 HEAD 抓到 +1 · XY = `M `)。v0106 一字不動。

## 桌機一行(PowerShell 7 · 從檔案複製)

```powershell
$r="$HOME\OneDrive\Documents\movies-dataset";$t="$HOME\Downloads\VIA_Settle_v0107";git -C $r fetch -q origin claude/optimistic-goodall-yhalc5;git -C $r archive --format=zip -o "$t.zip" FETCH_HEAD VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_SettleAll_v0107.py;Expand-Archive "$t.zip" $t -Force;$f="$t\VeritasIntelligenceAnalytics\docs\handoff\ai\VIA_SettleAll_v0107.py";if((Get-FileHash -InputStream ([IO.MemoryStream]::new([byte[]]([IO.File]::ReadAllBytes($f) -ne 13)))).Hash-eq'F40722F5B68F40A95A5DC020D4045ED1EFB2952D887AAF480E2F911CE298AACA'){python $f --root $r}else{'[RED] SettleAll SHA-256 mismatch - not run'}
```

跑完看報告 `SETTLE_latest.md` 的「other 類改動差在哪」與「壞 JSON」兩節(或上傳貼回包),那 28 支 VRN 舊版的改動是什麼、哪本冊壞了,就會寫在那裡。
