# VIA_SettleAll v0104 · 桌機 v0103 貼回(2026-11-05 00:08)的處理 + 操作員新令

操作員令(2026-11-05):「自動測試自動完成全部 · 所有 PS / PY 檔案都要加速器 · 向外擷取資料的引擎或 VDF 引擎都要導入最新網路工具 · 未來任何 PS / PY 指令也要加入加速器 · 五個獨立步驟同步進行 · 不影響引擎及系統健康 · 不產生九頭龍風險」。

## v0103 在桌機的結果(只記結論與筆數)

| 段 | 燈 | 事實 |
|---|---|---|
| ③ 同步 | 黃 | 38 個已追蹤改動:收據 1 · **其他 37**(VRN 舊版 ENG062 v0101–0112 / ENG397 v0113–0128 / SystemManager v0152–0153 共 30 支 · VCGC 狀態冊 RestorePoint / ParallelLanes / ProjectCompletion / SubsystemSeat · VDF 的 WHERE_IS_OUTPUT_HUB.md · TW_Active_ETF_Registry · 2 個 U/I html · paste.md)→ 照規矩停 → ④ ⑥ 仍在舊樹上紅 |
| ⑥ VCGC | 紅 | 兩個指令只印到 token 卡就 rc 1,輸出裡沒有任何 `[RED]` 行 |
| ⑦ Graphify | 黃 | 三張綠;VCGC extract 階段 2 個 worker 吃 4.8 GB(起始可用 5.53 → 0.73)被殺 |
| ⑧ VQG · ⑨ Agent OS · ⑤ VRN | 黃 | 同 v0102(VQG 算得出 · symlink 權限 · DATA_GAP) |

## v0104 改什麼(v0103 一字不動)

| 段 | 改法 | 對應操作員令 |
|---|---|---|
| ③ 同步 | 每個已追蹤改動用 `git show HEAD:檔` 對工作樹**算類別**:receipt · state(VCGC / VDF 自己寫的狀態冊)· **bridge(只差加速器 / 網路橋塊 = 桌機 via-bridge-sweep / via_net_injector 注入的)** · eol(只差換行)· other。只有 other 才停;其餘 stash → 合併 → 放回,衝突 receipt 取桌機版、state / bridge / eol 取分支版 | 不產生九頭龍:分支是正本,桌機注入的橋由 sweep 再補,不會長出第二份程式 |
| ④⑤⑧⑨ | VDF ui · VRN 狀態 · VQG · Agent OS 併行(各寫各的收據夾 · 不碰同一個檔;`--serial` 可關);⑥ VCGC(寫紀錄冊)與 ⑦ Graphify(吃記憶體)仍一個一個來 | 五系統同步進行 · 健康優先 |
| ⑥ VCGC | 讀 VCGC 自己的事件冊 `VIA_Reports/vcgc/events/EVENTS_<日>.jsonl` 最後幾筆 outcome / error 進報告(它不印的錯它自己有記) | 自動完成 |
| ⑦ Graphify | 可用記憶體 < 估計 + 2 GB → `--max-workers 1`(峰值約減半 · 慢一點) | 不影響健康 |
| ⓫ 政策全景 | L103 三條只讀盤點:.py 沒加速器橋 · 有網路 import 卻沒網路橋 · .ps1 沒 Celeritas;範圍 = VCGC 全景工具的 SKIP 名單 + 待分類 / 被取代 / 新模組收容 / 工具本體不算;只算個數列檔名,**補缺是 VCGC 的 via-bridge-sweep / via_net_injector 的事,本檔不改他系統的檔** | 所有 PS / PY 加速器 · 擷取引擎網路工具(量 · 不代改) |

容器現況(⓫):.py 3,6xx 支 · 沒加速器橋 16 · 網路 import 沒網路橋 74 · .ps1 1,0xx 支 · 沒 Celeritas 162 —— 全清單在貼回包 `settle/SETTLE_latest.json` 的 `policy`。

自測 30 / 30(新:分類 bridge / state / eol / other · state 衝突取分支版 · 政策盤點 · worker 規則 · 併行段炸一段不拖垮 · 去橋比對)· 容器實跑 scan / sync / vrn(併行)/ vcgc / vqg / agentos / policy / report · VCGC 全景卡治理錯 0(報 3 PINVER 釘 SHA · 3 SWALLOW:1 承自 v0101 · 2 是事件冊讀壞行 / 讀不到就略過)。

## 桌機要做的(PowerShell 7 · 一行 · 從檔案複製)

```powershell
$r="$HOME\OneDrive\Documents\movies-dataset";$t="$HOME\Downloads\VIA_Settle_v0104";git -C $r fetch -q origin claude/optimistic-goodall-yhalc5;git -C $r archive --format=zip -o "$t.zip" FETCH_HEAD VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_SettleAll_v0104.py;Expand-Archive "$t.zip" $t -Force;$f="$t\VeritasIntelligenceAnalytics\docs\handoff\ai\VIA_SettleAll_v0104.py";if((Get-FileHash -InputStream ([IO.MemoryStream]::new([byte[]]([IO.File]::ReadAllBytes($f) -ne 13)))).Hash-eq'F6F6EF1052B435E8BB6D3E8F2CCE30B10A1A2B12CBB11D1C2FAC38BF9FF0F086'){python $f --root $r}else{'[RED] SettleAll SHA-256 mismatch - not run'}
```

預期:③ 這次 37 個「其他」大多會被算成 bridge / state / receipt → 自動 stash 合併放回 → ④ 跑到 VDF v0168、⑥ 在新樹上;還剩 other 的會列檔名(真的改了程式才會)。⑦ VCGC 那張會用 1 個 worker 再試;還是不夠就要 ≥ 6 GB 可用。
