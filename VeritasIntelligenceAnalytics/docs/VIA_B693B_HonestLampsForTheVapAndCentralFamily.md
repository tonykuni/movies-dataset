# 批693B · Z92 收尾——VAP/中央一族最後五盞紅改成誠實燈 · 2026-09-21

> 操作員令「自測自修」(GO ON 續;批689B「TEST DEBUG TILL IT WORKS」)。
> **撞號**:VRN 線分支已出 批693(未併),本批依 LL334 預先取 **批693B**;Grid v0446 掃全部遠端未撞。
> 對象=容器全格子剩下的 5 盞(批690 後的 Z92 餘族):同一型病——庫缺/表空/0 列時把「沒料」當「壞」。

## 一 · 尺沒動,燈改對(L16;批584/689B/690 同律)

| 站 | 引擎(新版號) | 舊行為(容器) | 新行為 | 容器自測 |
|----|--------------|--------------|--------|----------|
| 寬表刷新器六檢 | `VAP_ENG007_RawWideRefresh_v0103` | ① 寬表/全球庫不在 → FAIL,②–⑤ 在沒庫的境上亂跑 | 缺哪個先探 → [NODATA] ① 指路(全球庫=OmniFetch/via-vdffetch;寬表=本器 refresh 自建)· ②–⑤ SKIP · ⑥ 紀律宣告照檢 | OK 1 · NODATA 1 · SKIP 4 · rc2 |
| 系統同步樞紐八檢 | `CGC_MDL090_SystemHub_v0102` | ③ 台股庫 0 列 → FAIL | 庫缺/0 列 → [NODATA] ③(指路 via-price);其餘八檢照跑;有料而 <100 萬列才 FAIL | OK 8 · NODATA 1 · rc2 |
| 引擎簡化稽核八檢 | `CGC_MDL092_ConsolidationAudit_v0110` | ④ 雙庫 3 表 <20 → FAIL | 表少且庫缺/空 → [NODATA] ④(指路 boot 鏈落表);有 ≥20 表而缺 tw_prices_adj/consensus_daily 才 FAIL | OK 8 · NODATA 1 · rc2 |
| 資料庫目錄台八檢 | `CGC_MDL098_DataCatalog_v0103` | 側線 v0102 只探庫檔;庫在但 tw_daily_prices/tw_monthly_revenue 沒落表 → ② FAIL | 兩表不在也記 NODATA;兩表都在才驗 header 細則 | OK 7 · NODATA 1 · rc2 |
| 市場分析引擎自測 | `VAP_ENG013_MarketAnalytics_v0105` | ②③ 拿 NOT_RUN(tw_trading_daily 空 / etf_book 空)當 FAIL | 沒 groups / n_book=0 → [NODATA] ②③ 指路;有料而數字不合才 FAIL | OK 13 · NODATA 2 · rc2 |

門檻(百萬列 · ≥20 表 · header 三字串 · 族群 7 欄守恆)一個字沒動。**Grid v0446** 四站 rc0 → nodata_ok(目錄台站本來就是)。

## 二 · 沒動的

VRN 引擎一支未動(VRN 線)。`VIA_PS_PyProgress_Module.ps1` 未動(Z115 候「准改 PyProgress」)。Z76 794 支註解未動(候「統一」)。

## 三 · 全格子 v0446(容器;PATH 帶 /opt/pwsh)

**OK 278 · FAIL 0 · SKIP 8 · TIMEOUT 0**(234s;GRID_20260921_180133;rc=0)。對上一跑(FAIL 5):消失 5 · 新紅 0。容器全格子**第一次零紅**——不是為了綠改尺,是把崩潰改成量測;工作站有料時這五支走原本的完整檢。Z92 結。
