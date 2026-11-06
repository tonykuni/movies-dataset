# VIA_SettleAll v0106 · 快(操作員 2026-11-06「PS 指令貼上去跑後速度很慢」)

桌機 v0104 實錄的時間都花在哪:Graphify 四張 **1,881 秒**(1 worker 下 VRN_Shared 1,114 秒 · VCGC 188 秒後被看門狗殺)· VCGC 串測 ~180 秒 · ⓫ 政策全景逐檔讀 7,000 個檔(OneDrive 夾)· ③ 沒同步時 ④ ⑥ 還在舊樹上白跑(結果沒意義)。

| 段 | v0106 怎麼省 | 預期 |
|---|---|---|
| ⑦ Graphify | 預設 `--graphify changed`:該系統夾最新 .py / .ps1 的 mtime 沒晚於上一張 graph.json → **沿用上一張**(GREEN · 0 秒);可用記憶體 < v0101 估計 → **直接不跑**(實測會被殺 · 省 15 分);`--graphify all` 照舊 · `skip` 全不跑 | 四張 1,881 秒 → 程式沒變時 0 秒 |
| ⓫ 政策全景 | mtime + size 快取(`VIA_Reports\settle\policy_cache.json`),檔沒變不重讀 | 第二次起只讀改過的檔 |
| ④ ⑥ | ③ 沒合併且工作樹落後分支 → 不在舊版上跑(YELLOW 寫原因 · `--force-old-tree` 可逼跑) | 省 VDF ui + VCGC 串測 ~4–5 分的白跑 |
| 全部 | 每段記秒數(報告 `log[].secs`) | 下一輪看得到哪段慢 |

v0105 一字不動 · 自測 35 / 35(新:changed 模式沿用 / 新檔重抽 · 快取第二次全命中 · 舊樹判定三種)。

## 桌機一行(PowerShell 7 · 從檔案複製)

```powershell
$r="$HOME\OneDrive\Documents\movies-dataset";$t="$HOME\Downloads\VIA_Settle_v0106";git -C $r fetch -q origin claude/optimistic-goodall-yhalc5;git -C $r archive --format=zip -o "$t.zip" FETCH_HEAD VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_SettleAll_v0106.py;Expand-Archive "$t.zip" $t -Force;$f="$t\VeritasIntelligenceAnalytics\docs\handoff\ai\VIA_SettleAll_v0106.py";if((Get-FileHash -InputStream ([IO.MemoryStream]::new([byte[]]([IO.File]::ReadAllBytes($f) -ne 13)))).Hash-eq'87062098DB3568DE512FE96F765AE1C24B1A6789C2BFE5638447D997032EAC78'){python $f --root $r}else{'[RED] SettleAll SHA-256 mismatch - not run'}
```

③ 那 28 個 VRN 舊版改動(真的改了內容)還是要你決定:報告 `sync_dirty.other_diff` 會列每檔 +/− 與前 6 行差異;提交(`git add/commit`)或還原(`git checkout -- <檔>`)後再貼一次,④ ⑥ 就會在新樹上跑。
