---
name: vcgc-daily-close
description: VCGC 每日收尾(VCGC-WKF046):用全部省 Token 工具 + Graphify / OmniRoute 做當日交接儲存、五系統備份、本機 ↔ GitHub 一致性更新。使用者說「收尾」「今日收尾」「每日收尾」「交接儲存」「備份收工」「daily close」「下班前」,或打 /vcgc-daily-close 時用。只做 VCGC 自己的事;他系統(VDF · VRN · VQG · VAP)只讀其自報收據,不代改。
---

# /vcgc-daily-close — 每日收尾:交接儲存 · 備份 · 本機 / GitHub 一致(VCGC-WKF046)

在倉根執行。先設兩個變數(照 CLAUDE.md 第一步):

```bash
V=$(ls "VeritasIntelligenceAnalytics/supportive modules/registry/"CGC_MDL149_VeritasCentralGovernanceConsole_v*.py | tail -1)
E=$(python3 -c "import json;print(json.load(open('VeritasIntelligenceAnalytics/supportive modules/registry/VIA_ToolVersion_Lock_v0100.json',encoding='utf-8'))['token']['path'])")
```

## 步驟(依序;任一步紅 → 停在那一步,照實回報,不跳過)

| 步 | 做什麼 | 指令 |
|---|---|---|
| 1 | 省 Token 第一步(紅就停) | `VIA_FROM_VCGC=YES python3 "$V" token > /tmp/token_card.txt 2>&1; cat /tmp/token_card.txt` |
| 2 | 交接檢查(讀摘要 · 待辦 · 相依變更) | `VIA_FROM_VCGC=YES python3 "$V" handoff check` |
| 3 | 串測(順手重出工具矩陣 HTML) | `VIA_FROM_VCGC=YES python3 "$V" test --quick` |
| 4 | 獨立性 / TA-Lib / 命名衝突 | `VIA_FROM_VCGC=YES python3 "$V" run VIA_VCGC_MDL258_ToolMatrix check` |
| 5 | Graphify 車道(只讀 · 收據) | `python3 VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_GraphifyLane_v0100.py` |
| 6 | OmniRoute / MCP 健康(只讀) | `VIA_FROM_VCGC=YES python3 "$V" mcp doctor` |
| 7 | 有新模組 / 新冊:編號 + 註冊(先提交再編號) | `git add … && git commit …` → `VIA_FROM_VCGC=YES python3 "$V" run CGC_MDL237_NumberingSystem --apply --scope` → `… registry-sync`(乾跑,退役數不合理就停)→ `… registry-sync --apply` |
| 8 | 稽核(必 遺失 0 · 改身分 0 · 重號 0) | `VIA_FROM_VCGC=YES python3 "$V" run CGC_MDL237_NumberingSystem audit` |
| 8b | 註冊結果(收尾必看:元件冊新 / 變 / 退役 · 名碼 · 中央號)| `VIA_FROM_VCGC=YES python3 "$V" registry-sync`(看計數)· `… run VIA_VCGC_MDL258_ToolMatrix naming` |
| 8c | 舊版重複:整合優化驗證後刪除(只 VCGC 自己的)| `… run VIA_VCGC_MDL260_ConvergeEngine all` → `… run VIA_VCGC_MDL258_ToolMatrix prune`(READY 才 `--apply`)|
| 8d | 環境 / LIB 衝突偵測 → 新增計畫(操作員電腦;容器無境 = NODATA)| `VIA_FROM_VCGC=YES python3 "$V" run CGC_MDL186_EnvGovernance_8Hub eight-hub --env-root <境根> --base-python <BASE python>`(BASE · VIA_CORE · VIA_* 境:清華 / 阿里 / 官方鏡像比對 · 衝突因子移除計畫 · 健康境上再新增 · 反覆驗證 · 只出計畫,安裝是操作員的手 L19)|
| 8e | AUTO SYNC(全景監控同步 · 同步檢查;任何 VCGC 動作背景自動開,這裡明跑一次看結果)| `VIA_FROM_VCGC=YES python3 "$V" monitor sync` · `… sync-check` |
| 9 | 收尾閘(乾跑;只重測相依案) | `VIA_FROM_VCGC=YES python3 "$V" closeout` |
| 10 | 五系統每日備份(只增 · MANIFEST 入倉) | `python3 VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_DailyBackup_v0100.py backup` |
| 11 | 備份自查 | `python3 VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_DailyBackup_v0100.py check` |
| 12 | 工具矩陣重出(視覺鎖定 · 收尾分頁) | `VIA_FROM_VCGC=YES python3 "$V" run VIA_VCGC_MDL258_ToolMatrix build` |
| 13 | 提交 + 推送 + 一致性 | `git add -A <本批檔> && git commit` → `git push -u origin <分支>` → `git fetch origin <分支> && git status -sb`(必須 `ahead 0 · behind 0`) |

## 規矩
- 讀檔一律先 `python3 "$E" read` / `slice` / `digest`,不整檔讀;日誌只看判決行。
- `closeout --apply --push` 只在 ⑥ SDD 與交接閘都不紅時才用;紅就照實寫「收尾未驗收」,不寫成成功。
- 不改 .ps1(L70)· 不裝套件(L19)· 不碰 TA-Lib(L50)· 不代設同意閘 · 他系統的冊與檔不代改(L123)。
- 推送只推本工作分支;沒說要開 PR 就不開。
- 最後一句回報:備份時戳 · 備份燈 · 收尾各步燈 · 推送後 ahead / behind · 明天第一步 = `/vcgc-daily-open`。
