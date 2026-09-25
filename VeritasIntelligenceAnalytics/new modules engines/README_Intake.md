# new modules engines — 新模組/引擎收容區(批91)

> 操作員令(2026-08-21):「MOTHER FILE CHANGED TO …\movies-dataset\VeritasIntelligenceAnalytics\new modules engines」。
> 本夾=母系統的**新件收容入口**:新引擎、新模組、外部帶入件一律先落此夾。

## 收容規則(鐵律對齊)

1. **原件零觸碰**:落入本夾的檔案不就地修改;版本前進在正位進行。
2. **編號登記**:`via-number` 或 CGC Console(`Invoke-VIA-CentralGovernanceConsole-v05xx.ps1 -Register <本夾> -Commit`)發 append-only 識別碼(VIA-MOD/ENG/LIB/OTH-####,永不重發不改號)。
3. **整合去重四態判決**(hash 定生死):byte 全同=讓位;倉內他處同 hash=MOVED 讓位;同名異內容=_sha8 鏡像;全新=候歸位。
4. **歸位**:判決後移入 `functional modules/` 或 `supportive modules/` 正位;本夾保留收容存證(零刪除)。
5. **測試**:歸位件掛 selftest 進 grid;誠實三態 OK/FAIL/SKIP。

母根解析順位見 `supportive modules/registry/VIA_MotherRoot_SSOT_v0100.json`(動態探測,嚴禁寫死)。
