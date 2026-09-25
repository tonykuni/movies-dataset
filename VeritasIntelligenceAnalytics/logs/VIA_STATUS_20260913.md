# VIA 現況 2026-09-13 · 批394 收尾

| 層 | 值 | 燈 |
|---|---|---|
| GitHub | tonykuni/movies-dataset @ main + claude/via-system-followup-tz7k9t(雙推) | 綠 |
| HEAD | 以 git log 為準(收尾 commit 後)· 工作樹乾淨 | 綠 |
| 短令冊尾版 | Register-VIA-Commands-v0179.ps1(via-oneshot / via-unstick / via-psrepair-ast 各配 .cmd 梭與別名) | 綠 |
| 台帳 | 958 筆(append-only) | 綠 |
| 雲端全矩陣 | 207 站 · OK 205 · FAIL 0 · SKIP 2 · 286s | 綠 |
| 雲端 PS 全樹 | 尾版 ParseError 0 · 解析綠 164 · T3 死路嫌疑 0 · Report-Only R2 十二枚 | 綠 |
| 工作站倉庫 | 卡未合併已解 · 冊升 v0174→v0179 · 醫生升 v0101→v0104 | 綠 |
| 工作站 OneShot 首跑 | OK 10 · FAIL 5 · SKIP 1 · 3296s | 黃 |
| 工作站全矩陣 | 207 站 · OK 181 · **FAIL 22** · SKIP 2 · 2254s | 紅 |
| 工作站加速器 | via-accel-import --apply --approve 已跑(冊 VIA_AccelImport_v0100.json) | 綠 |
| 工作站 FRED | 鑰在位 · via-fred 真跑 183.8s · 紅冊列 FAIL/PARKED 序列 | 黃 |
| 工作站價格 | 本輪 +680 列 · checkpoint done 1988 / **failed 1430**(失敗過半) | 黃 |
| 工作站籌碼 | **落庫 0 列**(庫仍落後數月) | 紅 |
| 工作站對齊 | via-align update GREEN · tw_universe +4(asof 2026-09-11)· 未對齊 58 票 | 綠 |
| 工作站家族境 | via_core/via_vdf 等未建 → 走 base 退路(能跑≠本位) | 黃 |

## 下一指令(工作站)

```powershell
via-oneshot -SkipAccel -SkipData      # 約 45 分;跑完總表後附 22 紅站明細
via-oneshot -SkipAccel -SkipData -SkipMatrix   # 約 5 分;只看診斷
```

副本拿不到新檔時(bootstrap 死結;git pathspec 支援 glob=零寫死版號):

```powershell
$r="C:\Users\tonyk\OneDrive\Documents\movies-dataset"
git -C $r fetch origin main
git -C $r checkout origin/main -- "VeritasIntelligenceAnalytics/Invoke-VIA-OneShot-v*.ps1"
& (Get-ChildItem "$r\VeritasIntelligenceAnalytics\Invoke-VIA-OneShot-v*.ps1" |
    Sort-Object Name | Select-Object -Last 1).FullName -Root $r
```

## 三件未解(需工作站)

1. **全矩陣 22 紅** — 站名待 v0101 明細列出後逐站修(雲端同矩陣 0 紅,差異來自真資料與真環境)
2. **籌碼落庫 0 列** — 引擎未崩但無新資料入庫;查 checkpoint 是否已全標 done,或端點節流
3. **家族境未建** — `via-envgov apply --approve` 建 via_core/via_* 後 rungate 才由 YELLOW 轉綠

交接全文見 `logs/VIA_HANDOVER_b394_20260913.md`。
