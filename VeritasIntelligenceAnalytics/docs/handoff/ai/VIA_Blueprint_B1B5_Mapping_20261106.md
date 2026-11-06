# 架構基線(操作員 2026-11-05 貼上 · ENGINE v0102 · 固定 commit a5123fdd9)B1–B5 ↔ 本倉現況對照(2026-11-06)

來源:操作員貼的「VIA · ARCHITECTURE BASELINE · 六個獨立系統 · 五項阻礙 · 15 條契約全 OFF · 32 工具 · GLOBAL RELEASE RED / BLOCKED」。
那份文件**自述**:證據固定於 commit `a5123fdd9…`、未連 VCGC / Windows / 資料庫 / 任何 runtime。本倉現況用的是分支 `claude/optimistic-goodall-yhalc5`
(a5123fdd9 之後 200+ 提交)與桌機貼回的收據。下表只寫查得到的,查不到就寫查不到;**不改他們的結論**(放行與否是 owner 的事)。

| 阻礙(他們的)| 系統 | 他們的證據 | 本倉現況(可查)| 差距 / 下一步 |
|---|---|---|---|---|
| **B1** VDF movies intake exact path not found(`engine/vdf_movies_intake_v001.py` 10,506 B · SHA 5675d447…)| VDF | 固定 commit 樹沒這支 | 分支樹**也沒有**這支(全倉 find 只有 `VDF/qa/evidence/movies_intake_summary.json`)。VDF 入口是 `ActivateVDF_v01xx` / `VDF_SystemManager_v0168`;v0109 ⑬ 掃 98 個 VDF 家族尾版 `--selftest`(容器 🟢74 🟡9 🔴13) | 一致:manifest 宣告的檔不存在。要 VDF owner 決定:改 manifest 指向現有入口,或補那支檔。本倉不代補(他系統)。|
| **B2** VRN root / storage direction unresolved(HandleAll / RoundAll 多路徑解根 · Parquet 與 DuckDB 都可寫)| VRN | 無 owner 綁定的正本登錄 | VRN-2 側已有 `registry/VRN2_SSOT_v0101.json` · `VRN_ChainNodeLedger_v0100.json` · OutputStore(DuckDB 增量庫 = 主 · Parquet = 匯出)· 收尾 PASS 收據(桌機 2026-11-03 起多輪)。但「唯一正本根」仍是啟動器參數 / 環境變數 / 註冊紀錄三選一 | 部分一致:角色已定(DuckDB 主 · Parquet 匯出),**根的唯一正本**沒有 hash 釘住的只讀登錄。收尾期不做新登錄;寫進待辦。|
| **B3** VQG source binding / production read-only DB unverified(bridge v0100 · receipts production_database_verified=false)| VQG · Database | 固定樹只有 QuantGuard bridge v0100 | 分支有 `VQG_AllInOne_v0104 / v0105`(SHA 釘在 SettleAll PINNED)· 輸入 = VDF 資料庫(`VDF_DataHome_SSOT_v0101` 兩個家)· 桌機 closeout **YELLOW**(351 日線 parquet · DERIVE_READY · 探針 0050.TW)· VQG 只讀 VDF 庫、不回寫 | 大半一致:綁定靠 VDF 冊 + doctor 探根,不是 owner 簽的 BindingManifest;唯讀是程式約定不是 ACL。|
| **B4** VAP manifest / path / bytes / hash / version drift(25,587 vs 52,872 B · 樹 26,249 B · v0101 檔名宣告 v0100)| VAP | 主 / 影子 manifest 不一致 | 本倉 `VAP_Subsystem_Manifest.json`(8,399 B)宣告 `engine/via_autoplot_engine_v001.py`;engine 夾實際是 `VAP_ENG002_AutoplotEngine_v001.py` 等 8 支;`VAP_SystemManager_v0100.py` 在;VAP 未納入自動測試(矩陣 ⚪)· 桌機 VAP_AllInOne 未上傳 | 一致:漂移還在。VAP 是支援模組,收尾期只記錄。|
| **B5** VCGC source lock disagreement · Database governance missing(EnvManager freeze hash/path ≠ fixed source)| VCGC · Database | 無全域 DB owner / schema / migration / rollback 契約 | VCGC 鎖冊 `VIA_ToolVersion_Lock_v0100.json`(token / nlp / layout / accelerator / network 席位)+ `handoff check` 綠 · `test --full` 317 站(🟢252 🟡14 🔴51 · 紅 = NODATA 20 · 環境 24 · VDF 前版鏈 7)· 編號冊審計 遺失 0 · 改身分 0 · 重號 0;`VIA_EnvManager.py` 本倉有多份副本(40_Environment_Health · VAP/ASSETS/SCOPE_COPY · new modules engines)| 鎖冊的是**工具席位**,不是 EnvManager source;DB 治理冊**沒有**(VDF 冊只記家的路徑)。收尾期不新建 DB 冊;寫進待辦。|

## 他們的 15 條契約(全 OFF)對本倉的實際資料流

| 方向 | 他們 | 本倉實際 |
|---|---|---|
| VCGC → 五系統(control) | 版本化政策快照 · 只讀 · OFF | VCGC 只讀監控(看對方自報的燈與收據),不推政策快照;四系統對等(L123)。**與契約方向一致,但不是「快照」機制。** |
| VDF / Database → VQG · VAP · VRN(data) | immutable artifact / 只讀 view · OFF | VQG 讀 VDF 日線 parquet(只讀);VRN-2 讀 VDF 市場資料(`_vdf_fetch`);VAP 未接。**事實上已在跑,但沒有「契約」文件。** |
| VQG → VAP / VRN | immutable derived artifact · OFF | 未接。 |
| VRN → VDF optional | owner 核准 · OFF | 未接(VRN-2 不回寫 VDF)。 |

## 結論(照收尾規範:不虛構)

- 五項阻礙在本倉**沒有一項被「關掉」**;B1 / B4 完全一致,B2 / B3 / B5 有進展但不是他們要的 owner 簽核物(BindingManifest · hash 釘住的根登錄 · DB 治理冊)。
- 這些都是**新冊 / 新契約**,在操作員 2026-11-06 Release Closure 規範下(不新增模組 · 不引入新架構)**不在本輪做**;列為待辦,等操作員決定要不要開新一輪。
- 可以現在就做、且已做的:每輪矩陣(⑫ 系統 · ⑭ 模組)把實測燈與 VCGC 編號 / 時間印出來,給 owner 判斷用。
