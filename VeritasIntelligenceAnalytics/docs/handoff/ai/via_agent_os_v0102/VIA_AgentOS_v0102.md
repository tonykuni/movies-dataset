# VIA Agent OS v0102(引擎 1.0.2 Hardened · 由 VCGC 線整合啟動)

操作員 2026-11-04:「VCGC(整合 VIA Agent OS 並啟動)· 自測 · 自修正 · 自完成」。上傳 `via_agent_os_all_latest_engines_20261104.zip`(兩份上傳同一個檔 · SHA-256 `7f82d0b1835f`)· 清單 25 檔逐檔 SHA-256 核對全對。

| 項目 | 內容 |
|---|---|
| 位置 | `supportive modules\agent_os\VIA_AgentOS_v0102.py` = `src/via_agent_os_unified_readonly_hardened.py` + 第 3 行加速器標記(AST 與原檔完全相同 · SHA-256 `3d23c7adefce`)· v0100 留著不動 |
| 原包 | `VIA_AgentOS_AllLatestEngines_20261104.zip`(原樣 · 含報告、儀表板、VCGC 遠端預檢工具與測試、設定範例)|
| 性質 | 只讀 · 標準庫 · 不寫倉 · 不抓資料 · 不開子行程 · 不跑 VCGC 程式(`vcgc-status` 只讀白名單文件的 metadata)|
| 遠端 VCGC | `vcgc_remote_preflight.py` 留在原包(不當現役模組):預設零網路;`--tls-check` 會做 DNS / TCP / TLS,**要操作員授權端點與出網才可用**;OAuth / 憑證不放進倉 |

## 實測(容器 · 4 核)

| 項目 | 結果 | 秒 | 峰值 MB |
|---|---|---|---|
| selftest | 48 / 48(基本 28 + 整合 20)· 倉寫 0 · 子行程 0 | 0.4 | 42 |
| skills test | 8 Skill · 27 / 27 | 0.1 | 33 |
| VCGC 遠端預檢離線測試 | 20 / 20 | 0.1 | 27 |
| status / vcgc-status / deploy-preflight / repo-check(本倉)| rc 0 · `production_integration_ready: false`(引擎自己說的)| 0.1–0.2 | 42 |
| scan(VIA 樹)| 1,500 模組(引擎上限)· 單執行緒 | 48.8 | 117 |
| dashboard | 獨立 HTML · 外部請求 0 · 驗收 27 / 27 | 47.2 | 94 |

跑完本倉 `git status` 不變(只讀)。全景卡報 8 處「例外被吞 / 其他」(只報不修 · 原作的設計 · 記給 Agent OS 線)。

## 桌機啟動(PowerShell 7 · 一行)

```powershell
$r="$HOME\OneDrive\Documents\movies-dataset";git -C $r fetch -q origin claude/optimistic-goodall-yhalc5;$c=(git -C $r show "FETCH_HEAD:VeritasIntelligenceAnalytics/docs/handoff/ai/via_agent_os_v0102/VIA_AgentOS_v0102_boot.txt")-join"`n";if((Get-FileHash -InputStream ([IO.MemoryStream]::new([byte[]][char[]]$c))).Hash-eq'2891720ab9a02809fa92fa7c3b8683550529b69ed5e064e918029c384fe1df8b'){iex $c}else{'[RED] boot SHA-256 mismatch - not run'}
```

它做:取 v0102(SHA-256 核對 · 換行先正規化)→ `Downloads\` → selftest · skills test · status · vcgc-status(結果寫 `VIA_Reports\agent_os\`)→ 全綠才產生儀表板到 `Downloads\VIA_AgentOS_Dashboard_v0102_<時間>.html` 並打開。不寫 `.via\ssot.json`(1.0.2 沒有 bootstrap)。PowerShell 7 沙盒實跑過:四項 rc 0 · 儀表板寫成。
