# VRN-2 一支 Python · VRN2_RoundAll_v0101.py(取套件 → 診斷 → 全部自測 → 跑 → 自動修 → 除錯報告 → 貼回包)

`VRN2_RoundAll_v0101.py`(只用 Python 標準庫 · SHA-256 `ee9500d3a352`)一支跑完 VRN-2 一輪;套件 = `VRN2_Closeout_v0148.zip`(SHA-256 `c43a2355cf15`,本檔內已釘死)。
v0101 = v0100 + 桌機 2026-10-29 14:40 第一次跑 v0100 的貼回修正(紅 4 · 黃 10):

| 桌機看到的 | 根因 | v0148 / v0101 怎麼修 |
|---|---|---|
| ③ `VRN2_UIAction_v0109.py --selftest` ④ FAIL(容器裡過)| 你的殼有 `VIA_ROOT`,處理器的「重渲染」就去讀它 → 自測真的重渲染了桌機的 Workbench,對不上「沒有 VIA 根」的預期 | 處理器 **v0110**:自測先拿掉 VIA_ROOT / VRN2_* 再跑、結束還原;動作照 v0109 |
| ⑥f 8 檔 Yahoo 404「####.TW」(5274 · 5904 · 8358 · 4966 · 7728 · 6147 · 3264 · 6143)· gate FAIL_CLOSED | 鉅亨對上櫃股也回 `TWS:####` → 共識引擎一律組 `.TW`;這 8 檔是上櫃,Yahoo 要 `.TWO` | **ConsensusJoin v0101**:用 ⑥e 市場冊(VDF 身分表 TWSE .TW / TPEX .TWO)的代號對應,換掉引擎組代號那一個函式(引擎檔原樣不動);今天快取裡用錯尾碼抓的代號會重抓 |
| ② 擷取 Python = `envs\via_core.retired-20260914_111946` | 本檔把 `envs` 下任何裝齊套件的夾都當候選 | **RoundAll v0101**:名字有 retired / backup / bak / old / deprecated / archive 的夾一律略過(照列)|
| ⑬b「檢驗 534(不過 120)」 | 科目對錯列:其他營收當總營收 · 應付所得稅當所得稅 · 負債與權益合計當權益 · 部門成長率當營收成長率 · 成本寫負數直接相減 · 預估調整表同年三個值取到舊估 | **HistoryAlign v0102**:這些列不對應(不覆蓋 · 不刪 · 不檢驗)· 成本取絕對值 · ROE 可用平均權益 · 同年同科目取報告裡重複出現的值 · 差到不像同口徑標「口徑不明」不算不過(容器資料:74 / 218 → 5 / 192,剩的 5 筆是測試故意做錯的)|
| `python "%USERPROFILE%\Downloads\…"` 在 PowerShell 找不到檔 | `%USERPROFILE%` 只有 cmd 認得;PowerShell 要 `$env:USERPROFILE` | 本檔跑完最後印「下次」三行,用**完整路徑**(兩種殼都能貼);下面也分開寫 |
| ⑥ 四點 FAIL / ⑥e 紅只有一行 | 證據在貼回包,主控台看不到 | 除錯報告多印:FAIL 那一點的摘錄原文 · `market\vdf\last_error.txt` 最後幾行 · Yahoo 404 代號與上櫃 .TWO 數 |

| 步驟 | 做什麼 | 不做什麼 |
|---|---|---|
| ⓪ VIA 根 | `--root` → `VRN2_ROOT` / `VIA_ROOT` → 本檔所在的倉 → 啟動器記的 `Downloads\VRN2_Closeout_v0*\VRN2_Runtime_Context.json` → vrn2:// 註冊 → `%USERPROFILE%\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics` | 找不到不猜:印出查過的地方 |
| ① 套件 | 本機 `Downloads\VRN2_Closeout_v0148` 的 zip 雜湊對 + 逐檔對 → 直接用;否則 git archive 發行夾(分支 → main)→ 核對 → 解壓;本機夾有檔不對 → 整夾改名備份再解壓 | 不刪舊套件夾 |
| ② 診斷 | VRN-2 Python 的必裝套件 · 擷取 Python(`VIA_FETCH_PY` / `%USERPROFILE%\envs\via_tw_fetch` / 其他 envs · 退役 / 備份夾略過)的 yfinance 等 · 共用 MarketFetch / VDF 引擎 · 啟動器鎖 · 輸出夾可寫 · 來源夾 · 磁碟 · CPU · git | 不裝套件(缺的交 VCGC,照印指令)|
| ③ 自測 | runtime zip 解到 TEMP(逐檔核對)→ Workbench v0102 · HistoryAlign v0100 / v0102 · DataIntegrate v0100 / v0101 · UIAction v0110 · SSOTSync v0101 · OutputStore v0101 · ConsensusJoin v0101 · 管理器 v0255 各 `--selftest` + 啟動器 `--selftest` | 不碰真資料 |
| ④ 跑 | `ActivateVRN-2_v0148.py`(預設不上船 `VIA_VRN2_NO_PUSH=1`)· 逐行即時印 · 60 秒沒輸出印心跳 · 另一個啟動器在跑就不跑 | `--ship` 才推 |
| ⑤ 自動修 | 同 v0100(重抓 ⑥e · 重跑 ⑥f · 重跑 ⑬b · Combined 重組 · ⑬ 補寫 · Workbench 重渲染 · 舊資料庫問你 · 清過期鎖)| 收尾收據先備份成 `.before_roundall.json` 再標註;不刪任何資料 |
| ⑥ 除錯 | 每個非綠步驟 + 下一步 · 四點核對不過的點 **+ 摘錄原文** · ⑥e 錯誤最後幾行 · Yahoo 404 / 上櫃 .TWO · 缺項 · 完成判定 · 冪等閘 · 階段耗時 · Combined 欄序 / 空格 · Workbench · 市場 / 歷史 / 庫 / 整合 / SSOT → `VIA_Reports\vrn2\VRN2_RoundAll_latest.json` | — |
| ⑦ 貼回包 | `Downloads\VRN2_PasteBack_<時間>.zip`(多收 `consensus\VRN2_YFTickerMap_latest.json`)| — |

結束碼 0 綠 · 2 黃 · 1 紅;最後一行 `NEXT: [燈] …`(前面三行「下次」是完整路徑的重跑指令)。

## 在 cmd 或 PowerShell 貼這一行(建議)

它開 Windows PowerShell → 從 GitHub 分支 `claude/optimistic-goodall-yhalc5`(讀不到 → `main`)取 `VRN2_RoundAll_v0101.py` → **核對 SHA-256**(`ee9500d3a352`)→ 存到 `Downloads` → 用你的 python 執行。
VIA 根不在預設位置就先設(cmd:`set VRN2_ROOT=…` · PowerShell:`$env:VRN2_ROOT='…'`);要帶參數就設 `VRN2_ROUNDALL_ARGS`(例:`--integrate yes --source C:\測試樣本報告`)。

```bat
powershell -NoProfile -ExecutionPolicy Bypass -EncodedCommand JABFAHIAcgBvAHIAQQBjAHQAaQBvAG4AUAByAGUAZgBlAHIAZQBuAGMAZQAgAD0AIAAnAEMAbwBuAHQAaQBuAHUAZQAnAAoAdAByAHkAIAB7ACAAWwBDAG8AbgBzAG8AbABlAF0AOgA6AE8AdQB0AHAAdQB0AEUAbgBjAG8AZABpAG4AZwAgAD0AIABbAFQAZQB4AHQALgBFAG4AYwBvAGQAaQBuAGcAXQA6ADoAVQBUAEYAOAAgAH0AIABjAGEAdABjAGgAIAB7ACAAfQAKACQAUgAgACAAPQAgAGkAZgAgACgAJABlAG4AdgA6AFYAUgBOADIAXwBSAE8ATwBUACkAIAB7ACAAJABlAG4AdgA6AFYAUgBOADIAXwBSAE8ATwBUACAAfQAgAGUAbABzAGUAIAB7ACAAJwBDADoAXABVAHMAZQByAHMAXAB0AG8AbgB5AGsAXABPAG4AZQBEAHIAaQB2AGUAXABEAG8AYwB1AG0AZQBuAHQAcwBcAG0AbwB2AGkAZQBzAC0AZABhAHQAYQBzAGUAdABcAFYAZQByAGkAdABhAHMASQBuAHQAZQBsAGwAaQBnAGUAbgBjAGUAQQBuAGEAbAB5AHQAaQBjAHMAJwAgAH0ACgAkAEIAcgAgAD0AIAAnAGMAbABhAHUAZABlAC8AbwBwAHQAaQBtAGkAcwB0AGkAYwAtAGcAbwBvAGQAYQBsAGwALQB5AGgAYQBsAGMANQAnAAoAJABQACAAIAA9ACAAJwBWAGUAcgBpAHQAYQBzAEkAbgB0AGUAbABsAGkAZwBlAG4AYwBlAEEAbgBhAGwAeQB0AGkAYwBzAC8AZABvAGMAcwAvAGgAYQBuAGQAbwBmAGYALwBhAGkALwB2AHIAbgAyAF8AcgBlAGwAZQBhAHMAZQBfAHYAMAAxADQAOAAnAAoAJABGACAAIAA9ACAAJwBWAFIATgAyAF8AUgBvAHUAbgBkAEEAbABsAF8AdgAwADEAMAAxAC4AcAB5ACcACgAkAEgAIAAgAD0AIAAnAGUAZQA5ADUAMAAwAGQAMwBhADMANQAyAGIAZgBjADQAMwAxADQANABjADUAMgAyADMAOAA5ADcAYwAyADkAYgA2ADAAMQA4ADYAYgA2ADEAOAAyAGUANgA3AGYANgA2ADAANQBkADcANAAxADMAYwAwADYAZgA1ADMAOQBlADYAJwAKAFcAcgBpAHQAZQAtAEgAbwBzAHQAIAAoACcAWwBWAFIATgAtADIAXQAgAFAAbwB3AGUAcgBTAGgAZQBsAGwAIAAnACAAKwAgACQAUABTAFYAZQByAHMAaQBvAG4AVABhAGIAbABlAC4AUABTAFYAZQByAHMAaQBvAG4AIAArACAAJwAgALcAIACeXyAARwBpAHQASAB1AGIAIACAiyAAVgBSAE4AMgBfAFIAbwB1AG4AZABBAGwAbABfAHYAMAAxADAAMQAuAHAAeQAoADhoDVwgAFMASABBAC0AMgA1ADYAIACMX/dXTIgpACcAKQAgAC0ARgBvAHIAZQBnAHIAbwB1AG4AZABDAG8AbABvAHIAIABZAGUAbABsAG8AdwAKACQAdABvAHAAIAA9ACAAZwBpAHQAIAAtAEMAIAAkAFIAIAByAGUAdgAtAHAAYQByAHMAZQAgAC0ALQBzAGgAbwB3AC0AdABvAHAAbABlAHYAZQBsACAAMgA+ACQAbgB1AGwAbAAKAGkAZgAgACgALQBuAG8AdAAgACQAdABvAHAAKQAgAHsAIABXAHIAaQB0AGUALQBIAG8AcwB0ACAAIgBbAFIARQBEAF0AIAAkAFIAIAANTi9mIABnAGkAdAAgAAlQFmJ+Yg1OMFIgAGcAaQB0ACgASFEtiiAAYAAkAGUAbgB2ADoAVgBSAE4AMgBfAFIATwBPAFQAKQAiACAALQBGAG8AcgBlAGcAcgBvAHUAbgBkAEMAbwBsAG8AcgAgAFIAZQBkADsAIABlAHgAaQB0ACAAMQAgAH0ACgAkAHQAbwBwACAAPQAgACIAJAB0AG8AcAAiAC4AVAByAGkAbQAoACkACgAkAHQAIAA9ACAASgBvAGkAbgAtAFAAYQB0AGgAIAAoAFsASQBPAC4AUABhAHQAaABdADoAOgBHAGUAdABUAGUAbQBwAFAAYQB0AGgAKAApACkAIAAoACcAdgByAG4AMgBfAHIAbwB1AG4AZABhAGwAbABfACcAIAArACAAKABHAGUAdAAtAEQAYQB0AGUAKQAuAFQAbwBTAHQAcgBpAG4AZwAoACcAeQB5AHkAeQBNAE0AZABkAF8ASABIAG0AbQBzAHMAJwApACkACgBOAGUAdwAtAEkAdABlAG0AIAAtAEkAdABlAG0AVAB5AHAAZQAgAEQAaQByAGUAYwB0AG8AcgB5ACAALQBGAG8AcgBjAGUAIAAtAFAAYQB0AGgAIAAkAHQAIAB8ACAATwB1AHQALQBOAHUAbABsAAoAJAB6ACAAPQAgAEoAbwBpAG4ALQBQAGEAdABoACAAJAB0ACAAJwByAG8AdQBuAGQAYQBsAGwALgB6AGkAcAAnADsAIAAkAG8AawB6ACAAPQAgACQAZgBhAGwAcwBlAAoAZgBvAHIAZQBhAGMAaAAgACgAJABiACAAaQBuACAAJABCAHIALAAgACcAbQBhAGkAbgAnACkAIAB7AAoAIAAgAGYAbwByAGUAYQBjAGgAIAAoACQAdwAgAGkAbgAgADAALAAgADIALAAgADQALAAgADgALAAgADEANgApACAAewAgAGkAZgAgACgAJAB3ACkAIAB7ACAAUwB0AGEAcgB0AC0AUwBsAGUAZQBwACAALQBTAGUAYwBvAG4AZABzACAAJAB3ACAAfQA7ACAAZwBpAHQAIAAtAEMAIAAkAHQAbwBwACAAZgBlAHQAYwBoACAALQBxACAAbwByAGkAZwBpAG4AIAAkAGIAIAAyAD4AJgAxACAAfAAgAE8AdQB0AC0ATgB1AGwAbAA7ACAAaQBmACAAKAAkAEwAQQBTAFQARQBYAEkAVABDAE8ARABFACAALQBlAHEAIAAwACkAIAB7ACAAYgByAGUAYQBrACAAfQAgAH0ACgAgACAAZwBpAHQAIAAtAEMAIAAkAHQAbwBwACAAYQByAGMAaABpAHYAZQAgAC0ALQBmAG8AcgBtAGEAdAA9AHoAaQBwACAALQBvACAAJAB6ACAAKAAnAG8AcgBpAGcAaQBuAC8AJwAgACsAIAAkAGIAIAArACAAJwA6ACcAIAArACAAJABQACkAIAAkAEYAIAAyAD4AJgAxACAAfAAgAE8AdQB0AC0ATgB1AGwAbAAKACAAIABpAGYAIAAoACQATABBAFMAVABFAFgASQBUAEMATwBEAEUAIAAtAGUAcQAgADAAIAAtAGEAbgBkACAAKABUAGUAcwB0AC0AUABhAHQAaAAgAC0ATABpAHQAZQByAGEAbABQAGEAdABoACAAJAB6ACkAKQAgAHsAIAAkAG8AawB6ACAAPQAgACQAdAByAHUAZQA7ACAAVwByAGkAdABlAC0ASABvAHMAdAAgACgAJwBbAAiKXQAgAIZPkG4gAEcAaQB0AEgAdQBiACAAJwAgACsAIAAkAGIAKQAgAC0ARgBvAHIAZQBnAHIAbwB1AG4AZABDAG8AbABvAHIAIABEAGEAcgBrAEcAcgBhAHkAOwAgAGIAcgBlAGEAawAgAH0ACgB9AAoAaQBmACAAKAAtAG4AbwB0ACAAJABvAGsAegApACAAewAgAFcAcgBpAHQAZQAtAEgAbwBzAHQAIAAiAFsAUgBFAEQAXQAgAICLDU4wUiAARwBpAHQASAB1AGIAIAAGUi9lIAAkAEIAcgAgABZiIABtAGEAaQBuACAAhHYgACQARgAoALJ9740gAC8AIABnAGkAdAApACIAIAAtAEYAbwByAGUAZwByAG8AdQBuAGQAQwBvAGwAbwByACAAUgBlAGQAOwAgAGUAeABpAHQAIAAxACAAfQAKAEUAeABwAGEAbgBkAC0AQQByAGMAaABpAHYAZQAgAC0ATABpAHQAZQByAGEAbABQAGEAdABoACAAJAB6ACAALQBEAGUAcwB0AGkAbgBhAHQAaQBvAG4AUABhAHQAaAAgACQAdAAgAC0ARgBvAHIAYwBlAAoAJABjAG8AZABlACAAPQAgAFsASQBPAC4ARgBpAGwAZQBdADoAOgBSAGUAYQBkAEEAbABsAFQAZQB4AHQAKAAoAEoAbwBpAG4ALQBQAGEAdABoACAAJAB0ACAAJABGACkALAAgAFsAVABlAHgAdAAuAEUAbgBjAG8AZABpAG4AZwBdADoAOgBVAFQARgA4ACkAIAAtAHIAZQBwAGwAYQBjAGUAIAAiAGAAcgBgAG4AIgAsACAAIgBgAG4AIgAKACQAYgB5AHQAZQBzACAAPQAgACgATgBlAHcALQBPAGIAagBlAGMAdAAgAFQAZQB4AHQALgBVAFQARgA4AEUAbgBjAG8AZABpAG4AZwAoACQAZgBhAGwAcwBlACkAKQAuAEcAZQB0AEIAeQB0AGUAcwAoACQAYwBvAGQAZQApAAoAJABzAGgAYQAgAD0AIAAtAGoAbwBpAG4AIAAoAFsAUwBlAGMAdQByAGkAdAB5AC4AQwByAHkAcAB0AG8AZwByAGEAcABoAHkALgBTAEgAQQAyADUANgBdADoAOgBDAHIAZQBhAHQAZQAoACkALgBDAG8AbQBwAHUAdABlAEgAYQBzAGgAKAAkAGIAeQB0AGUAcwApACAAfAAgAEYAbwByAEUAYQBjAGgALQBPAGIAagBlAGMAdAAgAHsAIAAkAF8ALgBUAG8AUwB0AHIAaQBuAGcAKAAnAHgAMgAnACkAIAB9ACkACgBpAGYAIAAoACQAcwBoAGEAIAAtAG4AZQAgACQASAApACAAewAgAFcAcgBpAHQAZQAtAEgAbwBzAHQAIAAiAFsAUgBFAEQAXQAgACQARgAgAFMASABBAC0AMgA1ADYAIAANTg1cKAAkAHMAaABhACkAtwAgAA1O91dMiCIAIAAtAEYAbwByAGUAZwByAG8AdQBuAGQAQwBvAGwAbwByACAAUgBlAGQAOwAgAGUAeABpAHQAIAAxACAAfQAKACQAZABzAHQAIAA9ACAASgBvAGkAbgAtAFAAYQB0AGgAIAAkAGUAbgB2ADoAVQBTAEUAUgBQAFIATwBGAEkATABFACAAKAAnAEQAbwB3AG4AbABvAGEAZABzAFwAJwAgACsAIAAkAEYAKQAKAFsASQBPAC4ARgBpAGwAZQBdADoAOgBXAHIAaQB0AGUAQQBsAGwAQgB5AHQAZQBzACgAJABkAHMAdAAsACAAJABiAHkAdABlAHMAKQAKACQAZQB4AGUAIAA9ACAAaQBmACAAKAAkAGUAbgB2ADoAVgBSAE4AMgBfAFAAWQApACAAewAgACQAZQBuAHYAOgBWAFIATgAyAF8AUABZACAAfQAgAGUAbABzAGUAIAB7ACAAKABHAGUAdAAtAEMAbwBtAG0AYQBuAGQAIABwAHkAdABoAG8AbgAsACAAcAB5ACAALQBFAHIAcgBvAHIAQQBjAHQAaQBvAG4AIABTAGkAbABlAG4AdABsAHkAQwBvAG4AdABpAG4AdQBlACAAfAAgAFcAaABlAHIAZQAtAE8AYgBqAGUAYwB0ACAAewAgACQAXwAuAFMAbwB1AHIAYwBlACAALQBuAG8AdABtAGEAdABjAGgAIAAnAFcAaQBuAGQAbwB3AHMAQQBwAHAAcwAnACAAfQAgAHwAIABTAGUAbABlAGMAdAAtAE8AYgBqAGUAYwB0ACAALQBGAGkAcgBzAHQAIAAxACkALgBTAG8AdQByAGMAZQAgAH0ACgBpAGYAIAAoAC0AbgBvAHQAIAAkAGUAeABlACkAIAB7ACAAVwByAGkAdABlAC0ASABvAHMAdAAgACcAWwBSAEUARABdACAAfmINTjBSIABwAHkAdABoAG8AbgAoAA1OgYkodSAAVwBpAG4AZABvAHcAcwBBAHAAcABzACAAhHZHUCAAcAB5AHQAaABvAG4AKQAnACAALQBGAG8AcgBlAGcAcgBvAHUAbgBkAEMAbwBsAG8AcgAgAFIAZQBkADsAIABlAHgAaQB0ACAAMQAgAH0ACgBXAHIAaQB0AGUALQBIAG8AcwB0ACAAKAAnAFsARwBSAEUARQBOAF0AIAAnACAAKwAgACQARgAgACsAIAAnACAAUwBIAEEALQAyADUANgAgACcAIAArACAAJABIAC4AUwB1AGIAcwB0AHIAaQBuAGcAKAAwACwAIAAxADIAKQAgACsAIAAnACAA+HYmeyAAkiEgACcAIAArACAAJABkAHMAdAAgACsAIAAnACAAtwAgACh1IAAnACAAKwAgACQAZQB4AGUAIAArACAAJwAgAPdXTIgnACkAIAAtAEYAbwByAGUAZwByAG8AdQBuAGQAQwBvAGwAbwByACAARwByAGUAZQBuAAoAJAByAGEAIAA9ACAAQAAoACQAZABzAHQALAAgACcALQAtAHIAbwBvAHQAJwAsACAAJABSACkACgBpAGYAIAAoACQAZQBuAHYAOgBWAFIATgAyAF8AUgBPAFUATgBEAEEATABMAF8AQQBSAEcAUwApACAAewAgACQAcgBhACAAKwA9ACAAKAAkAGUAbgB2ADoAVgBSAE4AMgBfAFIATwBVAE4ARABBAEwATABfAEEAUgBHAFMAIAAtAHMAcABsAGkAdAAgACcAXABzACsAJwAgAHwAIABXAGgAZQByAGUALQBPAGIAagBlAGMAdAAgAHsAIAAkAF8AIAB9ACkAIAB9AAoAJgAgACQAZQB4AGUAIABAAHIAYQAKAGUAeABpAHQAIAAkAEwAQQBTAFQARQBYAEkAVABDAE8ARABFAAoA
```

## 已經有這個檔時

在 **cmd**(提示字元 `C:\Users\…>`):

```bat
python "%USERPROFILE%\Downloads\VRN2_RoundAll_v0101.py"
python "%USERPROFILE%\Downloads\VRN2_RoundAll_v0101.py" --skip-run --integrate yes
python "%USERPROFILE%\Downloads\VRN2_RoundAll_v0101.py" --only preflight,selftest
```

在 **PowerShell**(提示字元 `PS C:\Users\…>`;`%USERPROFILE%` 在這裡不會展開):

```powershell
python "$env:USERPROFILE\Downloads\VRN2_RoundAll_v0101.py"
python "$env:USERPROFILE\Downloads\VRN2_RoundAll_v0101.py" --skip-run --integrate yes
python "$env:USERPROFILE\Downloads\VRN2_RoundAll_v0101.py" --only preflight,selftest
```

兩種殼都能貼的寫法:完整路徑,例 `python "C:\Users\<你>\Downloads\VRN2_RoundAll_v0101.py"`(本檔跑完最後就印這三行)。

常用參數:`--source <報告夾>` · `--integrate ask|yes|no|skip`(舊資料庫)· `--no-open` · `--ship`(允許上船)· `--offline`(不連 GitHub)· `--python <VRN-2 的 python>` · `--skip-selftest` · `--selftest`(本檔自測)。

## 一行解開來的程式碼(核對用)

```text
$ErrorActionPreference = 'Continue'
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch { }
$R  = if ($env:VRN2_ROOT) { $env:VRN2_ROOT } else { 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics' }
$Br = 'claude/optimistic-goodall-yhalc5'
$P  = 'VeritasIntelligenceAnalytics/docs/handoff/ai/vrn2_release_v0148'
$F  = 'VRN2_RoundAll_v0101.py'
$H  = 'ee9500d3a352bfc43144c5223897c29b60186b6182e67f6605d7413c06f539e6'
Write-Host ('[VRN-2] PowerShell ' + $PSVersionTable.PSVersion + ' · 從 GitHub 讀 VRN2_RoundAll_v0101.py(核對 SHA-256 後執行)') -ForegroundColor Yellow
$top = git -C $R rev-parse --show-toplevel 2>$null
if (-not $top) { Write-Host "[RED] $R 不是 git 倉或找不到 git(先設 `$env:VRN2_ROOT)" -ForegroundColor Red; exit 1 }
$top = "$top".Trim()
$t = Join-Path ([IO.Path]::GetTempPath()) ('vrn2_roundall_' + (Get-Date).ToString('yyyyMMdd_HHmmss'))
New-Item -ItemType Directory -Force -Path $t | Out-Null
$z = Join-Path $t 'roundall.zip'; $okz = $false
foreach ($b in $Br, 'main') {
  foreach ($w in 0, 2, 4, 8, 16) { if ($w) { Start-Sleep -Seconds $w }; git -C $top fetch -q origin $b 2>&1 | Out-Null; if ($LASTEXITCODE -eq 0) { break } }
  git -C $top archive --format=zip -o $z ('origin/' + $b + ':' + $P) $F 2>&1 | Out-Null
  if ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $z)) { $okz = $true; Write-Host ('[計] 來源 GitHub ' + $b) -ForegroundColor DarkGray; break }
}
if (-not $okz) { Write-Host "[RED] 讀不到 GitHub 分支 $Br 或 main 的 $F(網路 / git)" -ForegroundColor Red; exit 1 }
Expand-Archive -LiteralPath $z -DestinationPath $t -Force
$code = [IO.File]::ReadAllText((Join-Path $t $F), [Text.Encoding]::UTF8) -replace "`r`n", "`n"
$bytes = (New-Object Text.UTF8Encoding($false)).GetBytes($code)
$sha = -join ([Security.Cryptography.SHA256]::Create().ComputeHash($bytes) | ForEach-Object { $_.ToString('x2') })
if ($sha -ne $H) { Write-Host "[RED] $F SHA-256 不對($sha)· 不執行" -ForegroundColor Red; exit 1 }
$dst = Join-Path $env:USERPROFILE ('Downloads\' + $F)
[IO.File]::WriteAllBytes($dst, $bytes)
$exe = if ($env:VRN2_PY) { $env:VRN2_PY } else { (Get-Command python, py -ErrorAction SilentlyContinue | Where-Object { $_.Source -notmatch 'WindowsApps' } | Select-Object -First 1).Source }
if (-not $exe) { Write-Host '[RED] 找不到 python(不要用 WindowsApps 的假 python)' -ForegroundColor Red; exit 1 }
Write-Host ('[GREEN] ' + $F + ' SHA-256 ' + $H.Substring(0, 12) + ' 相符 → ' + $dst + ' · 用 ' + $exe + ' 執行') -ForegroundColor Green
$ra = @($dst, '--root', $R)
if ($env:VRN2_ROUNDALL_ARGS) { $ra += ($env:VRN2_ROUNDALL_ARGS -split '\s+' | Where-Object { $_ }) }
& $exe @ra
exit $LASTEXITCODE
```
