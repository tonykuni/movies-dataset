---
name: vcgc-converge
description: VCGC 類似功能全景收斂(VCGC-WKF045 · VIA_VCGC_MDL260_ConvergeEngine):全景清點類似功能群 → AST 分類編號說明註冊體檢 → 複製到 TEMP 影子區 → 整合去重(零遺失證明)→ 一個最強模組候選 → 驗證後刪舊版。使用者說「收斂」「整合去重」「類似功能清點」「合併成一個最強模組」「刪舊版」或打 /vcgc-converge 時用。
---

# /vcgc-converge — 類似功能收斂成一個最強模組(WKF045)

```bash
V=$(ls "VeritasIntelligenceAnalytics/supportive modules/registry/"CGC_MDL149_VeritasCentralGovernanceConsole_v*.py | tail -1)
VIA_FROM_VCGC=YES python3 "$V" run VIA_VCGC_MDL260_ConvergeEngine census          # ① 全景清點類似群(只讀)
VIA_FROM_VCGC=YES python3 "$V" run VIA_VCGC_MDL258_ToolMatrix converge <家族>     # ② 13 步體檢(AST · 分類 · 編號 · 註冊 · 測試 · 啟動 · 橋)
VIA_FROM_VCGC=YES python3 "$V" run VIA_VCGC_MDL260_ConvergeEngine pair <A> <B>    # ③ 複製到 TEMP 影子區 → 逐定義比對 → 零遺失證明(原檔不動)
VIA_FROM_VCGC=YES python3 "$V" run VIA_VCGC_MDL260_ConvergeEngine all             # ④ 全部類似群一輪 → VIA_Reports/converge/CONVERGE_latest.html(視覺鎖定)
VIA_FROM_VCGC=YES python3 "$V" run VIA_VCGC_MDL258_ToolMatrix prune               # ⑤ 驗證後刪舊版(乾跑;--apply 才刪 · 刪前 / 刪後自測 · 不過即還原 · 刪除帳)
```

規矩:PROVEN_ZERO_LOSS 才合;BLOCKED / 同簽章不同本體 = 交操作員裁定(L75)· 只收斂 VCGC 自己的家族,他系統只攤開(L123)·
合成後跑 handoff test · 編號 --scope · registry-sync(乾跑看退役數)· audit 0/0/0 · 20 種失敗可能見工作流冊 WKF045 failure_modes。
