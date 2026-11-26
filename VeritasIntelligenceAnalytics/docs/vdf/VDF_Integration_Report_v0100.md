# VDF 檔案整合報告 v0100

> 2026-11-25 依操作員令(19:39):「用 VCGC 節省 token 工具檢視所有 VDF 檔案,審視檔案最少、指令模塊化、數量最小化進行整合」。
> - 需求號:VDF-REQ054(需求冊 v0315)。
> - 架構依據:`docs/VIA_SystemArchitecture_SDD_v0100.md` §5(VDF 服務群)。
> - 結果都是雲端容器在 git worktree 上實跑的,最多算黃燈;主機實跑之前不算收尾。

---

## 1 結果一覽

| 項目 | 整合前 | 整合後 |
|---|---|---|
| VDF 夾已追蹤檔 | 1389 | **982**(批 A 搬走 397 · 批 D 搬走 11 · 新增對位冊 1 本)|
| VDF 根目錄 `.ps1` | 69 | **6**(其餘 63 支是舊啟動器:批 A 52 支 · 批 D 11 支)|
| `_integration_*` 封裝夾 | 47 夾 · 324 檔 | **0** |
| 現役 `.py` 家族 | 133 | 133(這一輪只搬封存與舊啟動器,沒動任何引擎) |

搬走的檔都放進 `functional modules/VIA_RetiredEngines/<批>/`,沿用原路徑(以搬代刪),要還原用 `CGC_MDL276_QuarantineRecover restore <原路徑> --apply` 或 `git mv` 回去。

## 2 用了哪些 VCGC 工具

| 工具 | 做什麼 |
|---|---|
| token 卡 · `pack` · `read` | 整夾索引:尾版 125 · 未版號 185 · 舊版 333;309 檔骨架卡(省 99.9%) |
| `chain` | VDF_SystemManager(89 版 · 釘名 18)· MDL013(20 版)· MDL008(13 版)· MDL012(11 版)的版本鏈 |
| VCGC 退役閘 `via-prune --system VDF` / `--prove` | 鏈上走不到的舊版 62 支,分類 · 在 TEMP worktree 拿掉後實跑 |
| VCGC `prune_apply` | 批 A / D 搬前量 → git mv → 編號冊標退役 → 搬後量;變差整批還原(兩批都沒還原) |

- **缺口:** VCGC 退役閘只處理有版號的 `.py`。這一輪的封裝夾、`.ps1`、`_sha` 分身都不在它的範圍,所以名單由小腳本用全倉逐詞比對產生,搬移與標記仍交給 VCGC 的 `prune_apply` 做。這一項收據記黃。
- **另一個缺口:** 見 §4 批 C。

## 3 三條件證明(待裁定 2 部分裁定)

| 條件 | 批 A(397) | 批 D(11) |
|---|---|---|
| ① 沒人載入 | 沒有現役 `.py` 或管理器點名。只有同時代的舊啟動 `.ps1` 副本(`supportive modules/audit_tools` 21 支)和清單冊點名 | 全倉沒有可執行檔點名(`Start-VIA-VDF-v0103` 只被 v0104 點名,兩支一起搬) |
| ② 拿掉後每個動詞實跑 | VDF 管理器尾版 40 個動詞,基準 / 拿掉後 rc 40/40 相同。輸出差異只有時間戳、列順序,以及 `links` 多了 331 條斷鏈,這 331 條全部來自批 B,批 A 造成 0 條 | 40 個動詞 rc 40/40 相同;`links` 斷鏈 648 → 648 |
| ③ 已鎖成功數不變 | 成功鎖定帳 221 列 · 交接 reusable 98 項,都沒有一列涉及 | 同左 0 列 |
| VCGC 指標 | 搬前搬後 lost 27 → 27 · 編號 [0,0,0] → [0,0,0] · SDD RED → RED(都是既有的) | 同左 |

逐檔清單與證據:
- `VIA_RetiredEngines/prune_20261125_120933/`:批 A,含 `RETIRE_MANIFEST.json` · `RETIRE_PROOF.json`。
- `VIA_RetiredEngines/prune_20261125_123256/`:批 D,同樣有 MANIFEST 與 PROOF。

## 4 這一輪沒動的(和原因)

| 批 | 檔數 | 為什麼不動 | 下一步 |
|---|---|---|---|
| B:`_sha` 分身 · `_rebuilds_superseded` · `_bytecode_originals` · `_from_vap_iso_cleanup` | 26 | VDF 自己的冊還登記著:`registry/VDF_FunctionMatrix_v0100`(324 條)· `VDF_Param_Registry_v0102`(5)· `VDF_FetchSystem_SSOT_v0121`(2)。擷取冊點名的檔可能被擷取系統執行 | VDF 先出新版冊,把這些登記指到本體,再退役 |
| C:VCGC 退役閘證過的 19 支舊版 | 19 | **全部都在 11-24 搬回清單 `RESTORED_20261124.json` 上**(現役程式用完整檔名寫死)。退役閘把它們判成「只被死碼點名」,和 11-24 的裁定衝突;照做會重演 11-24 的重工 | 退役閘要先讀 RESTORED 清單、排除這些檔(VCGC 工具缺口,另開需求) |
| `references/` | 260 | 外來參考資料;名字太常見,逐詞比對分不出真正的引用 | 要操作員決定留在 VDF,還是搬到共用參考區 |
| 鏈上的前版(薄尾靠它跑) | 約 333 | 尾版執行時會載入它,不能搬 | 走「本體合併」:每個家族併成一支新本體,證過後前版才可退 |
| VRN 的檔放在 VDF 根目錄 | 6 | 屬 VRN;VDF 不改別人的檔 | VRN 那邊接手 |

## 5 目標:VDF 最少模組(數量最小化)

對位冊 `functional modules/VDF/registry/VDF_IntegrationMap_v0100.json` 把 133 個現役家族逐一對到 12 個目標模組:

| 模組 | 家族數 | 收斂成 |
|---|---|---|
| M0 管理器與入口 | 6 | `VDF_SystemManager`。MDL013 ActivateVDF · ENG093 LaunchConsole · ENG234 UiLauncher 都改成它的動詞 |
| M1 範圍 · 參數 · 名冊 | 24 | 冊為主,解析器一支 |
| M2a 台股擷取 | 15 | 一支台股擷取引擎(來源分道) |
| M2b ETF 擷取 | 6 | 一支 |
| M2c 財報 · 營收 · 共識 | 12 | 一支 |
| M2d 總經 · 情緒 | 18 | 一支 |
| M2e 全球 · 指數 | 6 | 一支(`ENG066` 為本體) |
| M2f 來源轉接 · 探測 | 5 | 一支 |
| M3 啟動與排程 | 7 | `VDF_MDL022_SafeParallelLaunch`。MDL008 / MDL012 / ENG052 / ENG055 / ENG089 都改成它的動詞 |
| M4 資料平面 | 14 | `VDF_MDL020_DataPlane` |
| M5 品質與覆蓋 | 4 | 一支 |
| M6 U/I | 1 | 管理器的 `page` |

另有三類只記、不搬:
- 分析類 8 家族,疑屬 VRN。
- VRN 的檔 6 家族。
- 工具 1 家族,改用 VCGC 的覆蓋注入。

**133 個家族 → 12 個模組**,每一步都是「本體合併 → 證明 → 舊版退役」,一次一個家族、一個 PR。

## 6 指令模塊化

- 只有一個入口:`via-vdf <動詞>` → VDF 管理器(40 個動詞)。
- 倉根的 21 個舊 VDF 短指令(`via-vdfeng` · `via-vdffetch` · `via-fred` · `via-etfhold` …)都經 `Register-VIA-Commands` 轉到各自的引擎。對照表:

| 舊短指令 | 新指令 | 現在有沒有 |
|---|---|---|
| via-vdfsys | `via-vdf status` | 有 |
| via-activate-vdf · via-vdffetch | `via-vdf launch` | 有 |
| via-vdfui | `via-vdf page` | 有 |
| via-vdfcov | `via-vdf datamatrix` | 有 |
| via-vdfmatrix | `via-vdf engine-matrix` | 有 |
| via-vdfeng | `via-vdf engines` | 有 |
| via-vdfinc(ENG089)· via-vdfdb(ENG079)· via-vdfarch(ENG073)· via-fred(ENG074)· via-etfhold(ENG051)· via-etfhist(ENG078)· via-etfuniv(ENG077)· via-etfrev(ENG076)· via-vetf(ENG085) | `via-vdf run <引擎代號>` | **缺**:管理器還沒有 `run`(標準契約 §3 B 群) |
| via-vdf-refill · via-vdf-extra5 · via-tw-backfill · via-twrev · via-vdfchain | 待核:要先讀 `Register-VIA-Commands` 尾版看它們實際呼叫什麼 | — |

- 改這些 `.cmd` 讓它們印「已改名 → 新指令」,要動既有檔,在待裁定 10 之下,**這一輪不改**。

## 7 下一步

1. **批 B:** VDF 出新版的 FunctionMatrix / Param_Registry / FetchSystem_SSOT,把分身登記改指本體,再退役 26 支。
2. **VCGC 退役閘補「讀 RESTORED 清單」:** 有了才再跑批 C。
3. **VDF 管理器補 `run <引擎>` 與 `verbs --json`:** 架構規劃 §3 的 B 群與 A 群。
4. **本體合併,從鏈最長的開始:** MDL013(20 版)→ MDL008(13)→ MDL012(11)。
