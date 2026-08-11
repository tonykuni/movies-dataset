# VIA 母系統 · 模組化商品化與母頁規劃正本 v0100(2026-08-12)

操作員令:「清點資源性/功能性模組清單並對映運作狀態;VIA=母系統,子系統(VDF/VRN/VAP/
FlowSystem/後續開發)任一可單獨打包成獨立商品(獨立商品編號+指針);幫第一台電腦設立規範,
模組化商品化可搭配組合;消費者如開全新電腦 — 自動裝 PS7+ 與一切工具環境,進系統後能自動化
全自動,僅商品代碼增減由使用者改,現有代碼以舉證顯示;第一頁=設定+輸入現況+下方運作結果,
其他說明放最後幾頁(可隱藏);母頁左側可進任何子系統,子系統同構呈現,下方矩陣化說明;
輸入前檢查(重複等);檔案位置首次導入即設好 — C:\VeritasIntelligenceAnalytics 為 base;
視覺待操作員給介面連結後鎖定(風格鎖+色鎖);開始之前先規劃頁面與左 panel。」

**本文=規劃正本(先規劃後施工)。視覺鎖定候操作員介面連結到件。只增不減。**

---

## 一、盤點 — 功能性模組(functional modules,7 支)運作狀態

| 模組 | 定位 | 運作證據(本會話實測/存證) | 狀態 |
|---|---|---|---|
| WorkOps | 郵件×專案治理+指揮板(母版) | BoardQA 四層全綠(14/14+SYS 9/9+封印驗真);ALL v0111;操作員實機多輪全綠 | 🟢 生產 |
| VAP | 繪圖/視覺資產 | chartlib v007 端到端+--sql/--panels 實測;seaborn/plotly 引擎 selftest 65 PASS/1 SKIP;跨系統雙實證(VDF/MultiFactor 資料) | 🟢 生產(UI CDN 候修) |
| VRN | 研報 OCR/萃取治理 | MDL001-008 compile 全過·manifest 9/9 hash·HealthCheck 曾 89 PASS·53 凍結鎖 | 🟡 核心綠(斷鏈候修,執行端在工作站) |
| VDF | 市場資料鍛造 | MDL501 契約 277 項 check PASS·movies intake DryRun GREEN;MDL301/302 可跑但內部 ❌(MDL101 缺) | 🟡 半成(11 模組+v0160 三本體候上傳) |
| ChipWar | 晶片戰情指標族 | 併入時 harness L1 6/6+L2 8/8(存證) | 🟢 已驗 |
| MultiFactor | 多因子驗證模擬 | test v0101 過;simulation_ledger 本輪被 via-plot 實渲 | 🟢 已驗 |
| TALib | 技術指標 64 式 | 併入時全測過(adj 鐵律) | 🟢 已驗 |

另二支實為子系統但現居 supportive:**FlowSystem v2**(18 引擎;autotest 22/22+操作員實機全綠)🟢、
**VMT**(碼齊資料未布建)🟡、VTR(確定性層完成)🟡 — 商品化時各自立戶。

## 二、盤點 — 資源性模組(supportive modules,60 目錄)分族對映

每族標注「服務哪些功能模組」— 資源清單導入功能清單之對照即此矩陣(母頁矩陣頁資料源)。

| 族 | 目錄 | 服務對象 | 狀態 |
|---|---|---|---|
| 治理/登錄 | registry · 20_Registry_SSOT · VIA_Central_Governance · VIA_Governance_Runtime · 30_HardGate_Governance · audit_tools · _freeze_reports · VIA_VisualLock · specs · ssot · VIA_SSOT | 全體 | 🟢 登錄簿 162 筆 append-only 運作中 |
| 執行入口 | 60_PowerShell_Entry_Internal · bin(43+1 支 via-* 動詞) | 全體 | 🟢 本輪 via-plot 新增即用 |
| 子系統級引擎 | VIA_FlowSystem · VIA_Pipeline · VMT_SuperBOM · PMIS-Lite · TFE_Engine · VIA_IF_Engine · VIA_EngineForge · VIA_Forge · VIA_Optimizer_Suite | 各對應功能線 | 🟢/🟡 FlowSystem 全綠;餘按大架構表 |
| 執行環境 | 10_Core_Runtime · 40_Environment_Health · 50_Protection_Acceleration · VIA_AutoSandbox20_Runtime · runtime_bridge · environment · accelerator · network · parameters · VIA_Canonical_Units · VIA_VHS · VIA_VVX · VPNS | 全體 | 🟡 多屬工作站運行時,庫內為正本 |
| UI 支援 | ui_support · Dashboard_Format_Standardization · VIA_Decision_Studio · VIA_Control_Tower | 母頁/各子系統 | 🟡 部分 CDN 候在地化 |
| 規則庫 | 70_VRN_Rules(25 模組) · 80_VETF_Supportive_Sort · VIA_OCR_Router | VRN/FlowSystem | 🟢 凍結鎖最嚴 |
| nexuscore 家族 | _nexuscore_*(12 目錄)· _via_mother_system_manager · _via_governance_parameter_control · _via_safe_polyglot_optimizer · _central_governance_runs · _nexus_registry | 母系統編排 | 🟡 存量待對帳 |
| 打包/救援/待整理 | VIA_Standalone_Package_v0102 · VIA_Rescue_Staging_20260802 · VRN_Helpers_Rescued · _inbox_to_classify · _quarantine_pip_vendor · _superseded_redundant · notes | — | 🔴 待整理族(商品化前清冊) |

## 三、商品化規範 v0100(沿用既有 PKG-### 編號,整合去重不另立體系)

登錄簿既有 PKG-001…008(MegaAuditor/CentralGovernance/CommandBridge/AuditToolkit/
FlowSystem/IndustryForecast/MailTracker/SupportTools)。規範如下:

1. **商品編號**:PKG-###,append-only 永不變;子系統升商品時領號(候領:WorkOps母版/
   VAP/VRN/VDF/ChipWar/MultiFactor/TALib)。
2. **指針檔(每商品一件)** `PKG_###_Pointer.json`:
   `{pkg_code, name, version, subsystem_root, contents:[{path,sha256}], shared_supportive:[族],
   install:{ps_min:"7.0", python_min:"3.10", pip:[…], bin_verbs:[…]}, base:"C:\\VeritasIntelligenceAnalytics",
   ui_entry, first_page:"設定+現況+結果", docs_pages:"末尾可隱藏", precheck:["重複輸入","缺欄"]}` —
   一號一指針,舉證(sha256)顯示現有代碼。
3. **安裝器規約** `Install-PKG-###.ps1`(每商品隨附):①偵測/引導安裝 PS7+ ②python+pip 依賴
   (--user)③布建 `C:\VeritasIntelligenceAnalytics` 基座(首次導入即定檔案位置)④bin 動詞入 PATH
   ⑤開商品第一頁。全程自動;僅商品代碼增減交使用者。
4. **可搭配組合**:多商品共用資源族由指針 `shared_supportive` 宣告,安裝器去重(同族只落一份)。
5. **打包器**:沿用 bin/via-pack 線擴充(候令施工)。

## 四、母頁與左 panel 規劃(視覺候操作員介面連結鎖定 — 先結構後皮膚)

**三段式頁面規約(母頁與所有子系統頁同構):**

- **P1 消費者頁(唯一必看頁)**
  - 上半「設定+輸入現況」:base 路徑(預設 C:\VeritasIntelligenceAnalytics)· 環境燈
    (PS7/python/pip 依賴)· 已安裝商品代碼清單(勾選增減)· **輸入前檢查**(重複輸入/缺欄/
    路徑不存在 → 先擋後跑,誠實列問題)
  - 下半「運作後結果」:各子系統一鍵執行+OK/FAIL 燈+最新產出連結(舉證:時間戳+sha 摘要)
- **P2…n 矩陣頁**:分類清楚矩陣化 — ①資源模組×功能模組對映矩陣(本文§二)②運作證據矩陣
  (測試名/結果/時間)③商品目錄矩陣(PKG 編號/內容物/版本)
- **末頁**:設定細項/說明/規格/變更紀錄 — 預設收合,可整頁隱藏(hidden toggle)

**左 panel(母頁):**

```
[品牌塊] VERITAS INTELLIGENCE ANALYTICS · VIA 母系統
00  母頁(消費者頁)
—— 功能子系統(點入=同構三段式頁)——
01  WorkOps 母版        02  FlowSystem
03  VAP 繪圖            04  VRN 研報
05  VDF 資料鍛造        06  ChipWar
07  MultiFactor         08  TALib
—— 治理 ——
90  商品目錄(PKG 矩陣)  91  規格母版(最後一頁)
[底部誠實燈] SOLID/NOT_SOLID · 登錄簿筆數 · 版本
```

**子系統頁左 panel 同法**:00 本系統消費者頁 → 各視圖 → 末:說明/規格。FlowSystem 之
flow_hub(00 理論+01-13)即此規約先行實作,母頁=其擴大版;技術同構(單檔 HTML+側欄+
lazy iframe+零 CDN)。

**互通**:母頁左欄進任何子系統;子系統頁首行 nav 回母頁(FlowSystem nav_strip 先例擴至全體)。

## 五、施工順序(候「下一步」)

1. 母頁 v0100(結構先行,佔位配色;操作員介面連結到件即視覺鎖定換膚)
2. 首批商品指針+安裝器:PKG-005 FlowSystem(最完整)示範件
3. 矩陣頁資料源:由登錄簿+本文§一§二自動生成(AI 只整理不發明)
4. 輸入前檢查引擎(重複/缺欄/路徑)共用件
5. 待整理族(§二🔴)清冊歸戶後再入商品內容物
