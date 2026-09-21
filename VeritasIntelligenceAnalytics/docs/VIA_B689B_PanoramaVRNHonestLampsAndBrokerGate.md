# 批689B · 全景式檢視 VRN:紅燈裡有幾盞是尺的錯;券商同義字過拒絕閘;總管多一域「同義字」

> **撞號**:本線 批687/688/689 與 brave-goldberg 線(PR #61/#62/#64 已併 main)同號;先併進 main 的贏(LL334),本線三批改稱 **687B / 688B / 689B**(已推的 commit 主旨不改,L08);掉球 Z87–Z91 亦與 main 的 Z87 撞號,本線五條改 **Z88–Z92**。

操作員令:「GO ON 檢視 VRN 現況 測試修正各引擎 實測 修正 直到成功 全景式分析檢視 識別錯誤 避免傷害引擎跟系統 避免九頭龍風險 可同時修正的錯誤同時修 不能的順序修 TEST DEBUG … 與總管系統 SSOT REGEX 同義字 上傳更新只增不減不衝突 整合好」。

## 一 · 全景量到的(容器;LL329)

| 面 | 量到 | 讀法 |
|---|---|---|
| 六層鏈 `run --fast`(批688 尾) | GREEN 31 · RED 1 · GATED 1 · NODATA 13 | 唯一的 RED 是 ENG068 ②「台股 0 列」——**缺料被判成壞**(L16) |
| 全格子 20 紅(容器) | 逐站看理由 | VRN 家族 5 盞是**尺的錯**(缺料/缺件判紅):ENG068 ②⑥、ENG064 ⑦⑧(jieba/pytest 缺件)、首頁全能 ㊳(0 份 sidecar)、SUP_MDL742 ④(寫死 jieba 一定在)、六層鏈實跑(跟著 ENG068 紅);其餘 15 盞是 VDF/VAP 缺料(表不在的 SQL 直接炸=同型病,Z92) |
| 同義字聯集閘 MDL176 `status` | SAME 365 · ADD 62 · CONFLICT 5 · DENIED 10 · WIDEN 1;裁定 16;LEAK 0;**沒過拒絕閘的活支 9/10** | 9 支裡兩支是**中樞**:SUP_MDL749(四支引擎的券商實作委派它)與 ENG086(它委派的正本實作)——閘裝在實作那一處,四支消費者一起過(L30) |
| 樞紐增補冊 `additive` | 443 詞/7 域 · 多義 10(按來源判)· 候選 36(REVIEWABLE 未安裝) | 待你裁定(LL90),不是壞 |
| 工作站 V2(上次貼回) | RED 3(SUP_MDL746 · MDL141 · ENG068 ⑨ 26.8%) | ENG068 ⑨ 本批改 SKIP 並指路;前兩支要 v0102 跑器印出來的 FAIL 行(Z84) |

## 二 · 做了什麼(可同時修的同時修:七支新版互不相依;順序只有 ENG086 → 樞紐 → 總管)

| 件 | 檔 | 改了什麼 | 驗 |
|---|---|---|---|
| 券商拒絕閘 | `VRN_ENG086_FirstPageLogicBridge_v0110.py` | `_safe_broker_raw`:別名在 CGC_MDL176 `baseline().deny`(操作員令「大陸券商刪除」「去摩通」)者**不算券商證據**(跳過,冊零觸碰);回傳前經 `KEY_ALIAS_RULINGS` 對映到正典鍵(MEGABANK→MEGA · J.P. MORGAN→JPM · IBF→WATERLAND);MDL176 缺席=零回歸 | **二十二檢 22/22**(㉑ 廣發證券/摩通 → None、凱基 → KGI;㉒ 對映 6 條) |
| 樞紐 | `SUP_MDL749_VRNFieldRuleHub_v0112.py` | `broker_gate()` 端上 ENG086 的閘態;status 多印;既有判定函式零改 | **49/49**(㊼);status「券商拒絕閘 OK(拒 20 · 正典鍵對映 6;經 ENG086)」;MDL176 重量:沒過閘 **9/10 → 7/10**(兩支中樞過閘) |
| 總管第八域 | `VRN_SystemManager_v0102.py` | +`read('ssot')`:聯集冊 tally/拒絕/裁定/沒過閘 + 增補冊多義/候選 + 券商閘;入 rc 範圍;status/一頁/目錄/連結各一行;只讀不重算不寫冊 | **廿七檢 27/27**(㉖㉗);VCGC 25/25 |
| 缺料不是壞 | `VRN_ENG068_DailyBrief_v0106.py` | ② 台股 0 列 → SKIP 指路;⑥ 無數字可查核 → SKIP;⑨ 該日在庫 ≠ 宇宙(工作站 530/1978)→ SKIP 指路重跑因子段;數字對不起來才 FAIL;無 FAIL 有 SKIP=rc2 | 容器 OK 4 · SKIP 5 · rc2;六層鏈 **RED 0**(GREEN 31 · GATED 1 · NODATA 14 → rc4) |
| 缺件不是壞 | `VRN_ENG064_KnowledgeStack_v0103.py` | ⑦ jieba 缺=NODATA(不代裝)· ⑧ pytest 缺=NODATA | OK 9 · NODATA 2 · rc2 |
| 缺料不是壞 | `VIA_VRN_FirstPageEngine_v0127.py` | ㊳ 0 份 sidecar 的境=[NODATA] rc2(工作站 66 份才真驗) | 四十一檢 OK 40 · NODATA 1 · rc2 |
| 尺要誠實 | `SUP_MDL742_ToolLadder_v0103.py` | ④ 逐階 available 對本境 `find_spec` 真值(不再寫死 jieba 一定在) | 十檢 10/10 |
| 格子 | `CGC_MDL064_SelftestGrid_v0439.py` | 五站改名;每日觀察摘要/首頁全能 → nodata_ok;站數 287 | 見四 |

**沒動的**(避免傷害/九頭龍):正典冊、疊加層、聯集冊、增補冊一個字都沒改(只增不減:底冊 971 條少 0);7 支仍沒過閘的舊讀冊件(SUP_MDL015 · VIS_VRN_BrokerAlias_Compatibility v0222 / Extension v0224 · PDFTextLayerFallbackPlan v0222 · Q1_AliasRoutePatch v0100 · ENG062 v0102 · vrn_report_digest v0116)不在六層冊的活路上或是舊系,登 Z91 逐支對表後再裁。

## 三 · 你的手

1. 拉線 → `via-vrnrun`:六層鏈這一次應該只剩 SUP_MDL746 / MDL141 兩盞紅,而且格子裡會直接印 `[FAIL]` 行——貼回那兩行(Z84)。
2. `via-vcgc status` 看「VRN 系統管理」燈:多了 `ssot`(同義字);`via-py vrn "functional modules\VRN\VRN_SystemManager_v0102.py" read ssot pending` 看待裁定清單(多義 10 · 候選 36)。
3. 同義字裁定(LL90,你的手):多義 10 鍵(strong buy / conviction buy / top pick / 強力買進 … 是 BUY 還是 STRONG_BUY;accumulate/add 是 ADD 還是 BUY)一句話裁,我落冊(只增)。
