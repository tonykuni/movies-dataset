# VCGC → VRN / VDF 資訊卡:SSOT 與合規問題(2026-10-05)

依 **L111 子系統獨立 · 母系統監控協助律(一對二)**:VCGC 只監控、提供資訊、代裝工具與環境;**不改 VRN / VDF 正本**。
下列問題由子系統 manager 修(VRN_SystemManager / VDF_SystemManager),修完由 VCGC 重測收據轉態。

量測環境:容器、main @ 22a05a5b;唯讀(VCGC run / ssot panorama / handoff check),不寫子系統檔。

---

## A. VRN SSOT:中央鎖定正則有 2 條,自己的範例都過不了

正本:`supportive modules/registry/VRN_S05_FieldRegistry_v0102.json`(VRN S05 欄位冊),由 SUP_MDL749 v0117 第⑦檢量出(冊例 OK 91 · RED 2)。

| 正則 | 現行 pattern(要點) | 冊上自己的 pass 例 | 實際 | 問題 |
|---|---|---|---|---|
| `EMAIL_FULL` | `[A-Za-z][A-Za-z0-9._%+\-]+@…` | `10863@entrust.com.tw` | 不中 | local part 規定要字母開頭,冊例卻是數字開頭;冊內自相矛盾 |
| `TARGET_PRICE_LABEL` | `…\s*([0-9]+(?:\.[0-9]+)?)` | `Target Price NT$1,100` | 擷取 `1` | 數值沒收千分位,`1,100` 被截成 `1`(VALUE_TRUNCATED) |

**建議修正(由 VRN 出新版號冊;VCGC 只提供):**
- `EMAIL_FULL`:`[A-Za-z0-9][A-Za-z0-9._%+\-]*@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}`
  — 加 `examples_fail`:`@entrust.com.tw`、`abc@`;純數字 local part 仍由 `EMAIL_LOCAL_NUMERIC` 判為「聯絡 ID、非分析師」。
- `TARGET_PRICE_LABEL` 數值段:`([0-9]{1,3}(?:,[0-9]{3})+(?:\.[0-9]+)?|[0-9]+(?:\.[0-9]+)?)`
  — 下游取值前去掉 `,`;加 `examples_fail`:`TP 5`(個位數不是目標價,與 SUP_MDL749 ⑮ 負控一致)。

**同一個壞擷取段被拷貝到 4 處**(改一處不夠,要一起對齊;正本歸 VRN):
1. `supportive modules/registry/VRN_S05_FieldRegistry_v0102.json`(正本)
2. `functional modules/VRN/knowledge/VRN_Digest_Params_v0100.json`
3. `functional modules/VRN/references/intake/VRN_SSOT_Books_b561/VRN_Digest_Params_v0100.json`(收容件,凍結不改,只記錄)
4. `supportive modules/registry/VIA_FinalParameters_CanonicalRegistry.json`(中央參數冊的鏡像)

**VDF 交界(一對二的共用冊)**:`supportive modules/registry/VDF_VRN_SourceFallback_AllDataRegistry_v0100.json`
在 Stage-4 以名稱引用 `TARGET_PRICE_LABEL`。VDF 讀到的目標價會有同樣的千分位截斷。
→ VRN 修正本後,VDF 端要確認引用的是新版冊(不要自己拷一份 pattern)。

## B. VRN SSOT 檢核鏈(SUP_MDL749)的前版量尺過時

- 交接案 `vrn_ssot_consistency` 的標記寫的是 v0116,但尾版已是 v0117(main 加的)。
  v0117 本身 7/7 PASS,可是它往回跑前版鏈時 v0116 是 13/15,v0115 是 48/50。
- v0115 ⑤:預期 ENG080 有「看得見的落差」,實測落差 0/5 支。
- v0115 ⑭:負控預期 TW02 是「寫死 11 條、沒讀冊」,實測 TW02 已經讀冊(16/16)。
- 判讀:VRN 引擎已經改好了(TW02 讀冊、ENG073 v0139),是**檢核的前提過時**,不是引擎壞掉。
- 建議:VRN 出 SUP_MDL749 新尾版,更新 ⑤ / ⑭ 的預期與夾具;交接案標記跟著換到新尾版(VCGC 代改案冊,子系統先出版)。

## C. VRN 引擎:收據失效 / 自測未過

| 案 / 模組 | 現況(VCGC 唯讀實跑) | 歸屬 / 動作 |
|---|---|---|
| `VRN_ENG394_LayoutRestore` v0102 | 原本 `ModuleNotFoundError: reportlab`,之後 `fonttools_weight` FAIL。**VCGC 已代裝 reportlab · fonttools · opencv-python-headless · pytesseract 進 via_vrn_312** → 現在 rc 0 · failed 0 | VCGC 已協助完成;VRN 確認後重測收據(`vrn_layout` 等 6 案因相依換版失效) |
| `VRN_ENG393_DocClassVerify` v0101 | 14/15 FAIL;前版 v0100 34/35:逐件總判預期 GREEN,實得 YELLOW(ENG072 兩法分區 DIVERGE) | VRN:判讀是邏輯 / 夾具問題,不是工具缺;請 VRN 確認 ENG072 兩法分歧是預期還是回歸 |
| `VRN_ENG396_ReportEntities` v0100 | 25/25 PASS | 只需重開收據 |
| `VRN_ENG397_PluginHub` v0100 | 17/17 PASS | 只需重開收據 |
| VRN 新模組 ENG399 / ENG400 / LibPlugins / OCRPlugins / FirstPageEngine v0130 | 沒有交接案(CHANGED_CODE_WITHOUT_TEST) | VRN:補自測與交接案 |
| `VRN_NewPlugins_v0102` 本體 | 缺 PY 加速器橋(已由 v0103 薄尾接上;本體已發布、VCGC 不改) | 操作員裁:VRN 就地補或列版史豁免 |
| `functional modules/VRN/references/intake/VIA_NLP_OneEngine_v1.9.0/**` | 整批 ACCEL_BRIDGE_MISSING / CHANGED_CODE_WITHOUT_TEST | 收容件:建議 VRN 把 intake 列入掃描豁免(凍結來源不改) |

## D. SSOT 全景(VCGC → VDF → VRN → SUP)黃燈清單

| 族 | VDF | VRN |
|---|---|---|
| 同義字 | — | 收容件對樞紐漂移 8 列;拒絕清單真漏口 8;讀券商冊但還沒過拒絕閘 26 支 |
| 自動編號 | 缺號 1:`VDF_ENG234_UiLauncher_v0102.py` | 缺號 5:`VRN_ENG394_LayoutRestore_v0102`、`VRN_ENG399_RealTestHarness_v0100`、`VRN_ENG400_SixEngineShell_v0101` … |
| 命名 | 同號異名 3 組(VDF_ENG110:AKShareProbe / USMacroProbe / USMacroTree …) | 同號異名 1 組(VRN_ENG109:GateMap / TabStore) |
| 上下連結 | 待重驗鎖 VDF-WKF011 | 待重驗鎖 VRN-WKF008 |

缺號由 VCGC 的編號系統(CGC_MDL237 `--scope`)在子系統檔提交後補發;同號異名由子系統出四碼新版號改名。

## E. VCGC 已代做的協助(L111 ④)

- 環境:`via_vrn_312` 補 reportlab、fonttools、opencv-python-headless、pytesseract、markitdown、beautifulsoup4。
  `uv pip check` 全相容;numpy 2.5.3 不變。RunGate vrn GREEN。
- 不動任何 VRN / VDF 程式與冊。

## F. 建議協調順序

1. **VRN**:出 `VRN_S05_FieldRegistry` 新版(A 兩條正則 + fail 例)→ 同步 `VRN_Digest_Params` → SUP_MDL749 新尾版(B)。
2. **VDF**:確認 `VDF_VRN_SourceFallback` 引用的是新版冊;ENG234 v0102 提交後補號。
3. **VCGC**:重跑 `vrn_ssot_consistency` / `vrn_layout` / `vrn_docclass` / `vrn_entities` / `vrn_plugin_hub`,轉態收據;編號 `--scope` 補號。
