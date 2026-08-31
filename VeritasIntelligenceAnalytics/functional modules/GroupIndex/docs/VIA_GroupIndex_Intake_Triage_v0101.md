# VIA GroupIndex 外部上傳分流紀錄 v0101(2026-08-17 第二波)

## def 分流結論矩陣

| 上傳件 | 類型 | 判定 | 處置 |
| --- | --- | --- | --- |
| VIA_TW_SubGroup_SSOT_v0100_3.xlsx | SSOT | 與 repo 現行 SSOT SHA-256 相同 | 確認件,免整合 |
| VIA_TW_SubGroup_Matrix_v0100_3.html | 名單矩陣 | 與 repo 現行版相同 | 確認件,免整合 |
| ThreeList v0200 Zip 驗證 / 靜態稽核 / 套件 manifest / index6.html | v0200 證據 | 既有 v0200 交付的驗證憑證(CONTROLLED_ACTIVATION_PASS) | 佐證存查;報告分節樣式已由儀表板「名單/詳細結果矩陣」對齊 |
| VIA_ActiveStockETF(.py + mocktest) | LiveData 引擎 | 19/19 + 59/59 全過 | **已整合** → RUN_ETF_CONSOLES_V0100 |
| VIA_GlobalETFFlow.py | LiveData 引擎 | 26/26 + 38/38 全過 | **已整合** → RUN_ETF_CONSOLES_V0100 |
| VIA_FinMind_Ingest_v010.py | 資料入庫車道 | MOCK 8 項全過(T-1/append-only/raw_hash) | **已整合** → RUN_CHIPWAR_REVENUE_V0100 |
| VIA_SectorWhaleEngine_v020.py | 大戶偵測 | 10 種子成對回測 A1–A6 全過(召回 0.57→0.91) | **已整合** → 同上 |
| VIA_GovFundEngine_v040.py | 官股護盤偵測 | 四世界對抗 + LOEO E1–E8 全過(OOS 召回 0.905) | **已整合** → 同上 |
| VIA_ChipWar_Console_v010.py | 主控台 | 六階段全循環通過、零付費依賴 | **已整合** → 同上 |
| taiwan_revenue_engine_3.zip(twrevenue) | 月營收引擎 | selftest 8/8 + demo 合成端到端(1750 家/36 月)全過 | **已整合** → engine/taiwan_revenue_engine/ |
| sample_dashboard_2.html | 月營收儀表板樣張 | 與 zip 內建 output 同源 | 參考件 |
| VIA_VAP v015(csv/json/html/QA/ps1) | 舊版 VAP 規格 | 與 v018 40/40 逐欄一致(僅 sourceEvidence 版本戳) | 重複規格,免整合;SpecLineage 更新為 v015→v017→v018 |
| VIA_GIF_Integration_Blueprint_v001.html | 藍圖 | GIF 全球資金流整合藍圖(GlobalETFFlow 已實作其探針法) | 參考件 |
| VIA_Accelerated_Integration_CommandCenter_v0139A.html + ps1 | UI 骨架 | 其自帶稽核(下列)判定不可作為 canonical | 參考件,不導入 |
| VIA_System_Manager_Attachment_Audit_v0139A.md | 稽核文件 | A01–A08 FAIL(空函式/假性 PASS/未鎖 interpreter),A09–A10 可重用命名與版面 | 稽核結論採納:僅重用版面概念,零程式導入 |
| geminicode…(FX Zero-Sum Matrix html) | 概念稿 | 無資料引擎、無證據鏈 | 參考件 |

## def 去重(整合所有引擎後的同源歸一)

| 重疊面 | 判定 | Canonical |
| --- | --- | --- |
| robust z(MAD)| GroupIndex 資金流、GlobalETFFlow FIS_pv、SectorWhale I1 同法(median/1.4826·MAD)異參 | 方法同源、引擎各自成立(樣本門檻各異,不強行共庫) |
| 名冊 SSOT | SectorWhale 四族群 registry、twrevenue groups.csv(31 群/148 檔/L-P-M-G)與 GroupIndex SSOT(14 群/378 檔)語意部分重疊 | **GroupIndex SSOT 為 canonical**;其餘屬引擎內部監控清單,角色學(L/P/M/G)已同構 |
| VAP 規格 | v015 = v017 = v018(40 圖逐欄一致) | **v018**(APPEND_ONLY_VERSION_ARCHIVE_RESTORE) |
| 證據階梯 | ActiveStockETF 與 GlobalETFFlow V/Der/Est/P 一致;ChipWar T1–T4 同義擴充 | 階梯統一,T3 估流永不寫成金額、永不 Syn |
| 主控台調度 | ChipWar Console(subprocess 調度)與 OneClick PS1(段閘調度)分層不重疊 | OneClick 為套件總入口,ChipWar 為籌碼戰域內入口 |

## def 治理邊界

LiveData 引擎(ETF ×2、FinMind、月營收 fetch)live 模式僅本機顯式啟用;
套件內收證一律離線(mock=127.0.0.1 / MOCK / 合成),於暫存目錄執行,零 repo 污染。

## def 第三/四波上傳分流(2026-08-31)

| 上傳件 | 判定 | 處置 |
| --- | --- | --- |
| forward_valuation_vintage_v2_2.py | 前瞻評價 vintage 引擎;pandas 3.x merge_asof dtype bug 已修(統一鎖 datetime64[ns])→ self-test PASS | **已整合** → GroupIndex/engine |
| VIA_Hybrid_TW_Flow_Engine_v1.5.0(zip) | 官方 TWSE/TPEX/TDCC 優先 + FinMind 缺口接手;unittest 33/33 | **已整合** → GroupIndex/engine/FinMind_TW_Flow_Engine;TW 入庫 canonical |
| VUSIPE v0100 FINAL(zip) | 語意插件引擎;pytest 26/26 | **已整合** → supportive modules(dist/ wheel 屬同源建置產物,已刪) |
| Veritas_OmniFormat_Intelligence_Engine_v0140(zip) | 全格式引擎;pytest 67/67+10 | **已整合** → supportive modules |
| MarkdownEditingEngine_v1.2.0(zip) | 多語言 Markdown 工具;MANIFEST 34/34 驗證 | **已整合** → supportive modules(PS1 runtime 於本機執行) |
| VAP_v025_Complete_System_Package(zip) | VAP 系統 v025;40 圖 canon 與 v018 同套(APPEND_ONLY_STABLE_CODE);自帶測試 17/17 | **已整合** → functional modules/VAP/VAP_v025_Complete_Package |
| VIA_Toolchain_Bundle_20260830(zip) | 工具鏈(MotherImport/PSRepair/MarkItDown/VRN 批次);MANIFEST 11/11 驗證、名稱零重複 | **已整合** → supportive modules |
| VUSIPE FINAL(第 4 批重傳) | 與第 3 批**位元組級同雜湊** | 多餘 → 不落地 |
| MarkdownEditingEngine FINAL_1(重傳) | 同上 | 多餘 → 不落地 |
| VIA_Hybrid_TW_Flow_Engine _2(重傳) | 同上 | 多餘 → 不落地 |

## def 去重刪除紀錄(多餘的請刪除)

| 重複 | 驗證 | 動作 |
| --- | --- | --- |
| VIA_GovFundEngine_v040.py ×2(ChipWar/engines 既有 vs GroupIndex/engine 新副本) | SHA-256 位元組級相同 | **刪 GroupIndex 副本**;canonical 留 ChipWar 子系統,OneClick/收證改引 canonical |
| VUSIPE dist/*.whl | 同源建置產物 | 刪 dist/(pyproject 可重建) |
| 第 4 批 3 份 zip 重傳 | 與第 3 批同雜湊 | 不落地 |
| VAP v015/v017 規格 | 與 v018 40/40 逐欄一致 | 免整合(SpecLineage 存查) |
