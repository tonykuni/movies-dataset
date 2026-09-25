# VIA 倉衛生 批518(中央治理主控台 G03 重複家族 WARN 的處置)

> 律:L23 只刪 byte 同(md5 同)且檔名未被程式/冊引用的重複件;正本零觸碰(intake / SCOPE_COPY 惰性存檔 / 退役件不動);git 可回溯

## 量到

- 操作員貼回 `via-cgfamily`:console `[WARN] G03 DUP_FAMILY_RESOLVED:1049 組同內容檔案,2702 份冗餘`(工作站;主控台把 .json/.md/.html/.csv 資料檔與 VIA_Reports 也算進去)。
- 容器複算(只算 git 追蹤的程式檔 .py/.ps1/.psm1/.psd1):325 組 / 494 份冗餘;其中 home-only 210 組、intake-only 79 組、home×retired 9、newmod 9、home×intake 5、其他 13。
- 快照側候選(SCOPE_COPY / _output 快照夾 / 雙 sha 尾綴檔,且活件同 md5 在外面):128 件 → 檔名被引用 122 件(留)· 未被任何冊/程式引用 6 件(刪)。

## 留(122 件,理由)

`functional modules/VAP/ASSETS/SCOPE_COPY/` 是 VAP 的惰性存檔(VAP_ENG006 列 INERT,不入活動掃描),但 `VAP_Param_Registry_v0100.json` 的 src、`VIA_AllDocumentsModules_Inventory_v028711.csv`、`asset_scan.json`、多支 `Invoke-VAP-*.ps1` 以檔名引用 → L23 不刪;主控台的 G03 對它們永遠 WARN=設計上的存檔,不是債。

## 刪(6 件;雙 sha 尾綴 = 早期衛生工具把同檔又掛了一次尾綴;皆 byte 同於單尾綴正位件,且檔名零引用)

| 路徑 | md5 | 正位件 |
|---|---|---|
| `functional modules/VDF/vrn_financialdata_staging_extraction_store_v029vrn1d_sha35458a11a7b7_sha71e96a0a.py` | 4a88a49ac1f2e11084f682b70c923aa3 | `functional modules/VDF/vrn_financialdata_staging_extraction_store_v029vrn1d_sha35458a11a7b7.py` |
| `functional modules/VRN/C_Users_tonyk_OneDrive_Desktop_VRN_Start_VeritasReportNova_sha20aa071f465b_sha20aa071f.ps1` | 2621717729d6781bdb3c2f6fd0c6ac92 | `functional modules/VRN/C_Users_tonyk_OneDrive_Desktop_VRN_Start_VeritasReportNova_sha20aa071f465b.ps1` |
| `functional modules/VRN/Deploy-VRN (1)_sha16e38dc47dda_sha16e38dc4.ps1` | 247a12d61c116865a526950a4525c442 | `functional modules/VRN/Deploy-VRN (1)_sha16e38dc47dda.ps1` |
| `functional modules/VRN/analyze_pdf_shade7e8a994795_shade7e8a99.py` | c43f7a5b9f46be35a5a8e2af6f259b29 | `functional modules/VRN/analyze_pdf_shade7e8a994795.py` |
| `functional modules/VRN/complete_table_extractor_sha058efb79c1ea_sha058efb79.py` | 6c57107f37e5abbce70172e72de0faf0 | `functional modules/VRN/complete_table_extractor_sha058efb79c1ea.py` |
| `functional modules/VRN/comprehensive_pdf_extractor (1)_sha72238d6aa40a_sha72238d6a.py` | 92af120a041600ba5d885700f4ca722f | `functional modules/VRN/comprehensive_pdf_extractor (1)_sha72238d6aa40a.py` |

## 退役(1 件;git mv 可回滾;wave8)

| 路徑 | 去處 | 因由 |
|---|---|---|
| `functional modules/VRN/Invoke-VRN-Activate-And-Validate.ps1` | `functional modules/VIA_RetiredEngines/batch518_wave8/…` | G17 唯一活樹循環:舊部署啟動器仍呼叫批180 已退役的 VRN_ENG008/ENG027 等 25 檔;啟動器隨引擎退;引用僅存舊部署清單(VRN_Production_Manifest/README),現役鏈走 via-vrn*/via-ryg vrn |

## 沒動的(不是我們的債)

- G04 無法解析:退役件/收容件的原始語法錯(batch180/183 wave、GroupIndex intake、new modules engines bundle)+ VeritasPulse_v14 的空 `__init__.py`(合法 Python;工具把空檔列為無法解析)→ 零觸碰。容器(3.11)另多出 12 件 f-string 反斜線=3.12 以下的語法差,工作站 3.13 不算。
- G16 呼叫目標找不到 URN(1457):對外部函式庫/內建函式的呼叫本來就無 URN → 設計上 WARN。
- G18 爆炸半徑 >3 禁自動覆寫:我們從不給 --commit,本來就不自動覆寫。
- G22 未啟用 --probe:探針會動態載入模組頂層程式碼(工具自述);要舉證就 `via-cgconsole --probe`(操作員之手)。
