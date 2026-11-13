---
name: vcgc-daily-open
description: VCGC 每天第一步(VCGC-WKF047):讀昨日備份與交接狀況 → 啟動 VCGC 全部工具(省 Token · 工具矩陣 · Graphify · OmniRoute)→ 五系統各走自己入口更新實測。使用者說「開工」「早上第一步」「接續昨天」「讀昨天備份」「啟動 VCGC」「daily open」,或打 /vcgc-daily-open 時用。只讀晨檢(不更新)用 /vcgc-morning。
---

# /vcgc-daily-open — 隔天第一步:讀昨日備份 → 啟動全部工具 → 五系統更新(VCGC-WKF047)

在倉根執行,先同步再動手(L25 多 AI 交會):

```bash
git fetch origin && git status -sb          # 落後就 git pull --ff-only;有並行分支先看撞號(後合者升版)
V=$(ls "VeritasIntelligenceAnalytics/supportive modules/registry/"CGC_MDL149_VeritasCentralGovernanceConsole_v*.py | tail -1)
E=$(python3 -c "import json;print(json.load(open('VeritasIntelligenceAnalytics/supportive modules/registry/VIA_ToolVersion_Lock_v0100.json',encoding='utf-8'))['token']['path'])")
```

## 步驟(依序;紅就停在那一步照實回報)

| 步 | 做什麼 | 指令 |
|---|---|---|
| 1 | 省 Token 第一步 | `VIA_FROM_VCGC=YES python3 "$V" token > /tmp/token_card.txt 2>&1; cat /tmp/token_card.txt` |
| 2 | 必用功能卡 | `VIA_FROM_VCGC=YES python3 "$V" functions` |
| 3 | 讀昨日備份(逐檔 sha 對倉 · 幾小時前 · HEAD 前進沒) | `python3 VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_DailyBackup_v0100.py check` |
| 4 | 交接檢查(昨天的待辦 · 相依變更;不從記憶推定已完成) | `VIA_FROM_VCGC=YES python3 "$V" handoff check` |
| 4b | AUTO SYNC(全景監控同步 · 同步檢查)| `VIA_FROM_VCGC=YES python3 "$V" monitor sync` · `… sync-check` |
| 5 | 串測(全部 VCGC 工具 · 自動重出矩陣) | `VIA_FROM_VCGC=YES python3 "$V" test --quick` |
| 6 | 工具矩陣(兩大功能 · 收斂 · 覆蓋率 · 發行冊) | `VIA_FROM_VCGC=YES python3 "$V" run VIA_VCGC_MDL258_ToolMatrix build` |
| 7 | 支援工具發行冊有沒有新版待核 | `VIA_FROM_VCGC=YES python3 "$V" run VIA_VCGC_MDL258_ToolMatrix release`(乾跑;新版經操作員與 AI 協調、測試無誤才 `--apply`,L134 ④) |
| 8 | Graphify 車道 | `python3 VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_GraphifyLane_v0100.py` |
| 9 | OmniRoute / MCP(只讀探測;金鑰與隧道是操作員的手) | `VIA_FROM_VCGC=YES python3 "$V" mcp doctor` · `VIA_FROM_VCGC=YES python3 "$V" mcp probe <平台>` |
| 10 | 五系統各走自己入口並行實測(VCGC · VDF · VRN · VQG · VAP;只寫各自收據與進度帳) | `python3 VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_FiveSystemConstitution_v0100.py run --apply` |
| 11 | 工具看板(燈號最前) | `python3 VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_VCGCToolBoard_v0100.py run` |
| 12 | 今日待辦 | 從 ④ 的 pending + ⑥ 的「單檔收斂」挑今天要做的;照 WKF045 收斂工序(`run VIA_VCGC_MDL258_ToolMatrix converge <家族>`) |

## 規矩
- 讀檔先骨架卡(`"$E" read` / `slice`);日誌用 `"$E" digest`。
- 五系統各自實測、各自記帳;一個系統紅不影響其他系統(L125 ⑤);他系統只讀其自報收據,不代改(L123)。
- 不改 .ps1(L70)· 不裝套件(L19)· 不碰 TA-Lib(L50)· 不代設同意閘。
- 回報一張短卡:昨日備份燈與時戳 · 交接待辦數 · 串測紅黃綠 · 矩陣鎖定閘 · 五系統各燈 · 今天第一件事。收工用 `/vcgc-daily-close`。
