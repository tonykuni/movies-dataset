# VRN-2 v0158 桌機實測(2026-10-31 · Handle-All v0106 · RoundAll v0114 · 套件 v0158)

## 1. 05:13 · 同意閘二未設(`VIA_SCRAPE_CONSENT` 空)

auto → repair · ③b 黃「同意閘 未開」→ ⑥f 不重抓(現有共識不動)→ 收尾 **BLOCKED · VRN-2 0 · VCGC 1 · 人工 3 · 資料源 2**(跟發行時的預期一樣)。

## 2. 05:30 · 操作員設 `$env:VIA_SCRAPE_CONSENT = 'YES'` 後(真的經 VIA 網路工具抓 · 637 秒)

- ③b 綠:`VIA_NET_CONSENT=YES · VIA_SCRAPE_CONSENT=YES`。
- ⑤ 排「⑥f 改經 VIA 網路工具重抓」→ ConsensusJoin v0104 + 引擎 v0122 補放 → 今天的 checkpoint 封存 → 全部重抓。
- 引擎:`def Net tool : SUP_MDL740_NetUnified_v0119 · 閘 開 · 加速器 VIA_SuperAccel_Module · VeritasCeleritas_v1141`。
- 第一次:43 檔 · 3706 `ASSIGNED_JSON_NOT_FOUND`(一時抓不到)· 6933 / 7728 / 4171 回 404 → 品質閘 FAIL_CLOSED →
  等 30 秒只重抓這 4 檔 → 3706 抓到 · 404 三檔仍 404 → 不納入閘 → 搬 40 / 40 份(不上網)→ **gate PASS_WITH_WARNINGS · GREEN**。
- Combined 重組 52 列(調整後目標價 37 · FactSet 中位數 48 · YFinance 中位數 47 · EPS 格 134)· 增量庫追加 Combined 48 列。
- 除錯報告多一列綠的「⑥f 經 VIA 網路工具」· 收尾 **BLOCKED · VRN-2 0 · VCGC 1 · 人工 2 · 資料源 2**(跟發行時的預期一樣)。

中間那兩次 `Traceback … RuntimeError: QUALITY_GATE_FAIL_CLOSED` 是引擎自己的品質閘在重試前停下(ConsensusJoin 接手重試),不是錯誤。

## 3. 桌機環境(貼回包的收據 · 上一輪整輪 v0153)

- ③ 環境檢查:`C:\Python313\python.exe` 第三方套件 23 · 已裝 23 · 缺 0 → 啟動器 v0157 起的「只檢查」會直接綠(不呼叫 VCGC 安裝閘)。
- ③b OCR 隔離環境:`C:\Users\tonyk\envs\vrn2_ocr` 就緒 → 啟動器 v0158 照用(不建 · 不 pip)。
- ⑥f 這輪用的擷取 Python 是 `envs\via_core_312`(VIA_FETCH_PY)· 引擎印 `Raw Parquet: WARN_PARQUET_ENGINE_UNAVAILABLE`(原始 Parquet 沒寫 · Combined / 矩陣 CSV / DuckDB 不受影響)。

## 4. 剩下的(都不是 VRN-2 要改碼)

| 負責 | 項目 |
|---|---|
| VCGC | ⑥e:MOPS 財報被 VIA 網路工具合規層 DENY(放不放行 mops.twse.com.tw) |
| 人工 | MQ-1560 影像頁 4 點 OCR 摘錄對原圖 · 3 份報告缺年度數據(原文沒有就是沒有) |
| 資料源 | Combined 空格:鉅亨 404 × 3 · AAPL 不是台股 · 3706 / 6669 報告日前日線 PARTIAL(VDF 引擎 08-12~08-21 / 09-24~10-06 / 11-21~12-07 視窗 rc 2)· 市場資料缺 1 |

## 5. 下一步

整輪(`$env:VRN2_MODE = 'full'`)一次:收據換成啟動器 v0158 · 桌機上實測 ③ 只檢查 / ③b 照用 · ⑥e 重抓(PARTIAL 的視窗有機會補到)· ⑥f 沿用今天經網路工具抓的(不重抓)。
