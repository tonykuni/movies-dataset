# v0200 RC / TargetAcceptance v0201 整合裁定 v0100(2026-08-09)

操作員令:整合補強功能。九檔全數入庫(sha256 前16 見各檔旁);本文為與現行
VIA WorkOps(run-local 線)之整合去重裁定正本。

## 一、兩條產品線關係裁定

**v0200 RC = 平行產品線**(FastAPI 127.0.0.1:8775 · 36 模組 · Graph 委派 ·
DuckDB/Parquet SSOT · Windows installer),與本庫 run-local 線(PS+py · COM 唯讀 ·
side-car JSON)**共存不強併** — 安全預設完全同軸(no auto-send/no move-delete/
draft opt-in/restore staging-only/人工確認閘門),故裁定:
- 治理文件包 = 兩線共用正本,入 `docs/v0200_rc/`
- RC 引擎本體(36 模組/payload zip)未附 — 到貨再逐模組去重裁定
- DuckDB SSOT 屬 RC 產品內部存儲;本庫 side-car 既裁不變(F2)

## 二、驗收執行器 v0201 入庫狀態(誠實)

`acceptance/Invoke-VeritasWorkOps-TargetAcceptance-v0201.ps1`(sha 3159d541…):
- AST parse PASS;紅線稽核 CLEAN(無 send 端點;草稿驗證後 fail-safe 回關;還原僅暫存)
- **不可執行**:執行器要求 `payload\VeritasWorkOps_v0200_RC.zip`
  (期望 sha `2fdc8163…`)— payload 未附,L01 會誠實 FAIL。
  附上的 SHA256.txt 指整包 bundle zip(`da2b608e…`),亦未附。
  → 本庫入藏為「治理正本+對照」;要實跑驗收,操作員請在原 bundle zip 佈局內執行。

## 三、Graph 休眠線對接

IT_GOVERNANCE_HANDOFF + IT_INPUTS_REQUIRED = 規劃書 §12 IT 申請包的具體化
(Mail.Read+User.Read 最小 scope、public client、token 本機、無 send scope)—
歸入既有 Graph 休眠線材料;IT 核准前不啟用(治理不變)。

## 四、閉環範圍對照(closed_scopes 33 項 × 本庫)

已有同等:控制表匯入(表頭映射)/專案發現+人工確認(八層路由+佇列)/穩定編號
append-only(PLM 帳本)/三語範本/每日追蹤批次(三段升級鏈)/草稿不寄/關係人
候選(S4+網絡圖)/升級建議(T3)/附件智能免OCR(L7)/串重建(THR 互鏈)/
統一登記(WOP registry)/流程探勘 KPI(PM4Py)/診斷(ALL 總結)。
**本輪補強落地**:Gold Set 準確度基準(ENG-030,Gate E)· 備份/驗證/還原到暫存
(ENG-031,L06)。
候令(RC 有本庫無,待 payload 或另令):Today/Watchlist 產品 UI(板已有監看台雛形)、
里程碑管理、結案智能、Lesson Learned 結構化、統一搜尋、保留政策、onboarding 狀態機。

紅線不變:絕不代寄 · 唯讀 · 編號永不變 · 只增不減 · restore 僅暫存。
