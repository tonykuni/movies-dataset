# 批690 · VDF 一族的誠實燈(Z92 前五支)· 2026-09-21

> 操作員令(批689B 續,「GO ON」):全景式檢視 · 識別錯誤 · 避免傷害引擎跟系統 · 避免九頭龍 · TEST DEBUG TILL IT WORKS。
> 本批對象=容器全格子剩下的 14 盞同一型病(Z92):**表不在時 SQL 直接炸**。先 VDF 五支;VAP/中央 9 盞下一批。
> **撞號**:Grid v0440 已在 busy-bell 線(LL334),本線跳 **v0441**;批690 掃全部遠端未撞。
> 同時開了 **VRN 線** session_01GkJosEQeEZpMhCyJpF8BuZ(操作員令「開一個 vrn」;批691 起、只做 VRN;本線不再碰 VRN 引擎)。

## 一 · 尺沒動,燈改對(L16)

一張表不在,舊行為是 `CatalogException` 把整支自測炸掉——一行 FAIL 都不印,格子記紅。這不是量測,是崩潰。
批584(ENG072)、批538(ENG060/061/062 綁 2330 的假紅)、批689B(VRN 五盞)都是同一條律:**缺料記 NODATA rc2 並指路;表在、數字不合才 FAIL**。
門檻(≥95% 列數、≥10 群、≥30 碼…)一個字沒動;本批不是「為了綠改尺」,是把崩潰改成量測。

| 引擎 | 檔(版號) | 缺哪張表=NODATA | 指路 | 自測(容器,無料) |
|------|-----------|-----------------|------|-------------------|
| 產業混合分類冊 | `VDF_ENG058_IndustryUnifiedMap_v0101.py` | tw_listings_industry | `$env:VIA_NET_CONSENT='YES'; via-market-lists`(容器 openapi 三車道回非 JSON=固定缺) | ① OK · ② NODATA · ③–⑥ SKIP · rc2 |
| 調整後價格層 | `VDF_ENG060_AdjPriceLayer_v0105.py` | tw_daily_prices | `via-price`(ENG054 boot ②)→ `VDF_ENG060 build`(②b) | ① NODATA · ②–⑧ SKIP · rc2 |
| 因子庫 | `VDF_ENG061_FeatureStore_v0103.py` | tw_prices_adj · prices_canonical(視圖;SHOW TABLES 含視圖已實證) | `via-price` → ENG060 build → `VDF_ENG061 build`(②c) | ① OK · ② NODATA · ③–⑨ SKIP · rc2 |
| 族群聚合因子層 | `VDF_ENG062_GroupFeatureLayer_v0103.py` | features_daily | `VDF_ENG061 build` | ② NODATA · ③–⑦ SKIP · ⑧ OK(兩條路共用一處判準)· rc2 |
| 故事輪動橋 | `VDF_ENG072_StoryRotationBridge_v0102.py` | tw_listings · tw_daily_prices · tw_prices_adj + 籌碼三張(六張一次探) | 缺哪一族指哪一條(名冊/價→調整層/籌碼·當沖) | ① OK · ② NODATA · ③–⑧ SKIP · rc2 |

預設 CLI 路(boot 日更呼的 `build`)同樣先探表:缺=印 `[NODATA] … 指路` rc2,不再 Traceback。
每支各帶一個六行的 `_missing_tables(db, need)`(庫檔不在=全缺;`SHOW TABLES` 含視圖)——沒抽成共用模組:五支引擎各自可獨立執行(尾版 glob 檔),跨檔 import 版號檔=新的分岔;判準只有「表在不在」一句。

Grid **v0441**:五站 `rc0 → nodata_ok`(rc0 或 rc2 皆 OK;rc1 才紅),站數不變。

## 二 · Z91 對表(交給 VRN 線裁;本線不動程式)

| 件(尾版) | 活樹誰引用 | 六層冊 | 建議 |
|-----------|-----------|--------|------|
| SUP_MDL015_VISVRNBrokerAliasFullList_v0100 | SUP_MDL115_ControlTower.py · via_vrn_logic_book(家族指標) | L0 節點 | **改綁**(讀冊走 ENG086/樞紐) |
| VRN_ENG062_SummarizerV1_v0102 | VIA_SYSTEM_MANAGER_v0147 | L4 節點 | **改綁** |
| VIS_VRN_BrokerAlias_Extension_v0224 | 只剩 CGC_MDL177 稽核 · SUP_MDL560 編譯探針 | 無 | 退役候 |
| VIS_VRN_Q1_AliasRoutePatch_v0100 | 只剩 CGC_MDL177 稽核 · 編譯探針 · 舊登記 JSON | 無 | 退役候 |
| VIS_VRN_BrokerAlias_Compatibility_v0222 | 只被 SUP_MDL015 引 | 無 | 退役候(MDL015 改綁後即孤兒) |
| VIS_VRN_PDFTextLayerFallbackPlan_v0222 | SUP_MDL115_ControlTower.py · 舊 ps1 | 無 | 候(ControlTower 還指著) |
| vrn_report_digest_v0116 | CGC_MDL081_SubsystemManagerV2 · 舊格子 | 無 | 候 |

## 三 · 沒動的(避免傷害/九頭龍)

VAP/中央那 9 盞(VAP 模板跑器 matplotlib · 全球市場觀測 · 寬表刷新器 · 市場分析引擎 · 引擎簡化稽核 · 治理主控台 · 治理台 UI Matrix · 系統同步樞紐 · 資料庫目錄台)一支未動——下一批一族一批。VRN 引擎一個字沒改(VRN 線接手)。正典冊/聯集冊/律冊未改。

## 四 · 全格子 v0441(容器;PATH 帶 /opt/pwsh)

OK 266 · FAIL 9 · SKIP 6 · TIMEOUT 0(235s;GRID_20260921_125458)。對 批689B 收尾那一跑(OK 261 · FAIL 14):**新紅 0 · 消失 5**(五站全綠,NODATA rc2 被 nodata_ok 收)。剩 9 盞全是 VAP/中央一族:VAP 模板跑器(matplotlib)· 全球市場觀測 · 寬表刷新器 · 市場分析引擎 · 引擎簡化稽核 · 治理主控台 · 治理台 UI Matrix(綠燈率門檻,隨其他站走)· 系統同步樞紐 · 資料庫目錄台。regen gate 還原再生物後才 commit。
