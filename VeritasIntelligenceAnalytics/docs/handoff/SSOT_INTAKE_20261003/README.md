# SSOT 自動編號註冊管理

本批由 CGC_MDL237_NumberingSystem_v0114 接入既有中央編號。附件是候選需求，不是已部署的 Skill，也不是可直接採用的正式號碼；VRN 是 ReportNova，版本另存 version。禁止 TA-Lib。

## 正常流程

1. 底層提交 VIA_AssetCandidates_SSOT 的新版候選冊：ssot_code 必須 null。
2. VCGC 執行 `run CGC_MDL237_NumberingSystem assets-plan`：檢查目前中央冊、候選批次、來源、版本、同義詞與 Regex。
3. 提交來源後，VCGC 執行 `run CGC_MDL237_NumberingSystem --apply --scope`。沿用中央 allocator，只發 READY 項目；REVIEW/BLOCKED 保持無號。
4. VCGC 執行 `run CGC_MDL237_NumberingSystem audit` 及 `run CGC_MDL237_NumberingSystem assets-view`。
5. 註冊、SDD 與交接驗證保留實際燈號，再送 GitHub 候選分支。

`assets-plan <JSON檔>` 可預覽外部候選檔，但不寫入；實際收錄只讀中央 registry 最新 VIA_AssetCandidates_SSOT_v*.json，並要求已提交的 scope。寫入後沿用既有 scope 快照／稽核還原機制；未宣稱跨檔寫入具有崩潰原子性。本版加入排他 writer lock，不強制接管，也不保證其他舊版工具會遵守這把新鎖。環境變數 VIA_FROM_VCGC 是入口契約，並非安全認證。

## 身分與分類

|內容|既有中央類型|
|---|---|
|INPT / CNFG|PRMT|
|REGEX|RGX|
|SYNONYM|SYN|
|LOGIC / INDICATOR / OUTP / WORKFLOW 定義|LGC|
|POLICY|PLCY|
|SSOT 資產定義|SSOT|

MDL/ENG/CLS/FNC/LIB/ENV 繼續由現有程式與環境 collector 收編；這批不另建平行流水號。工作流定義 LGC 與實際治理工作流 WKF/STP 分開；本流程已登 WKF014 / REQ133。

來源身分 = source_id + source_pointer + candidate_id；再加 version 構成中央唯一鍵。同值不同來源分別編號。相同版本不可改定義；新版本必須明示 supersedes。不同來源對同一 owner/scope/semantic_key 有不同值時，不以時間或權重偷偷裁決。

風險與環境、依賴庫是登錄 metadata，不代表已安裝、授權或已強制隔離。REGISTERED 不等於 ACTIVE／正式資料正確。asset_views 是中央冊的三表唯讀投影，沒有第二套資料庫。

## 同義字與 Regex 邊界

同義字以 NFKC、trim、casefold 做精確映射，保留 scope；模糊比對不會自動改身分。與舊冊重疊而舊冊 scope 無法判定，保留 REVIEW，需在原正主冊建立有依據的範圍或裁定。

Regex 採 DuckDB RE2 測正反例；自動判斷重疊只支援錨定、固定寬度 ASCII 字面、字元集合／範圍、固定次數 `{n}`，上限 64 字元。此子集可用每個位置的字元集合交集證明是否重疊；其餘語法不靠少量樣本宣告安全，而是 REVIEW。舊 Regex 缺 scope、無法證明不重疊，也不自動發號。

目前 8 筆候選：兩個不同來源的起始日、MOM 週期、MOM 定義、來源分號邏輯，以及 MOM 同義字和兩個普通股 Regex。日期 2026-01-02 是操作員提出的預設，不代表已驗證交易日；MOM 為定義登錄，不宣称本輪新增了正式計算／交易策略。

## 附件口徑更正

- 不使用附件任意指定的 CNFG0001 / INPT0002；只有中央實際核發號有效。
- 不使用附件 TA-Lib 依賴。
- MOM 有回看期，不能稱零延遲或保證領先；ROC 沒有固定上下界。
- 不把 HIGH 風險只能跑 PRD 當作治理政策；隔離與授權仍由既有環境工具裁定。
- 既有 134 支 Windows 車道、舊同義字待裁定與總體紅燈並未因本輪登錄消失。
