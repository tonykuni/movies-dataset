# VIA SSOT / Regex / 同義字 / 政策 編號協作協定 v0100(操作員 2026-10-29 政策 · VRN-2 側已實作 · VDF / VCGC 側為契約描述)

> 操作員(2026-10-29):「VRN-2 / VDF / VCGC 三個都是獨立系統,彼此有依賴性但不會直接影響。VRN-2 / VDF 這些子系統端會產生很多 SSOT、REGEX、同義字、政策上的規範,由基層提出;VCGC 也有需求可提。
> 子系統提出後 SSOT ID 空白;另一個子系統也提了 SSOT ID 空白的,VCGC 會提示有衝突,等使用者與 AI 修改無誤後自動生成 SSOT 號碼,子系統看到了也會自動填上補全資料。三者靠使用者及 AI 協調,三個系統的這類手冊是一致的;三個系統都有自己的 SystemManager、SSOT、REGEX、同義字、政策庫及 MAIN()。」
> 自測到完成:TEST → DEBUG → OPTIMIZE → TEST → DEBUG → CONSOLIDATE → TEST → DEBUG → USER-TEST → DEBUG → ACTIVATE → TEST → DEBUG,直到全部正常。

## 1. 角色與邊界(四系統對等獨立 · 政策 L123)

| 系統 | 提出 | 核號 | 補填 | 寫誰的檔 |
|---|---|---|---|---|
| VRN-2 | 自己的 SSOT / Regex / 同義字 / 政策 / 參數(元件登記冊 `registry/VRN2_Component_Register_v*.json` · 暫編號 `VRN2-<類>-####` · `ssot_id` 空白)→ `contract/VRN2_NUMBER_REQUEST_latest.json` | 不核號 | 讀到 VCGC 核發冊就自動把 `ssot_id` 填進登記冊(出新版 · 只增不減)· 衝突標「待人判」 | 只寫 VRN-2 自己的 `registry/` `contract/` |
| VDF | 同上(自己的請求冊 · 自己的格式 · 本協定只要求 §2 的最小欄位) | 不核號 | 同上 | 只寫 VDF 自己的 |
| VCGC | 可提自己的需求 | **唯一核號者**:讀各子系統請求冊 → 跨系統比對(同鍵 / 同內容指紋 / 同義字衝突)→ 有衝突 → 提示使用者 + AI;修到無誤 → 寫核發冊 | — | 只寫 VCGC 自己的核發冊與衝突清單 |

三者之間只有**檔案契約**(請求冊 / 核發冊),沒有函式呼叫、沒有共用程式;任一方不在,其餘兩方照常跑(VRN-2:待核號條目一直是「暫編」,不擋 ⑧)。

## 2. 檔案契約

### 2.1 子系統 → VCGC:請求冊(VRN-2 的 `functional modules/VRN2/contract/VRN2_NUMBER_REQUEST_latest.json`)

```json
{"from": "VRN-2", "ts": "…", "register": "VRN2_Component_Register_v0136.json",
 "pending": ["VRN2-SSOT-0001", "VRN2-REGEX-0007"],
 "ssot_items": [{"key": "VRN2_SSOT", "entry": "SSOT|VRN2_SSOT", "kind": "SSOT", "vcgc_kind": "SSOT", "proposed_no": "VRN2-SSOT-0001", "ssot_id": "",
                 "fingerprint": "a1b2…", "version": "v0101", "src": "VRN2_SSOT_v0101.json", "status": "暫編 · 待 VCGC 核號", "note": ""}],
 "program_items": [{"key": "VRN_ENG397_P1Segment", "kind": "ENG", "vcgc_kind": "ENG", "proposed_no": "VRN2-ENG-0001", "ssot_id": "", "…": "…"}],
 "self_conflicts": [{"key": "VRN_Broker", "kind": "DICT", "fingerprints": ["f1", "f2"]}]}
```

最小欄位(VDF 也用這一組):`key` · `kind`(自己的類)· `vcgc_kind`(對應 `VIA_Numbering_SSOT` 的類:SSOT / RGX / SYN / PLCY / PRMT …)· `proposed_no` · `ssot_id`(空白)· `fingerprint`(內容 sha256 前 12)· `version` · `src`。

### 2.2 VCGC → 子系統:核發冊 `VCGC_NUMBER_GRANT_latest.json`

VRN-2 依序找:`<VRN-2 程式夾>/contract/` · `<VIA>/VCGC/contract/` · `<VIA>/supportive modules/registry/` · `<VIA>/VIA_Reports/vcgc/`(都只讀,全部合併)。

```json
{"ts": "…", "engine": "CGC_MDL237_NumberingSystem_v####",
 "grants": {"VRN2-SSOT-0001": "VIA-03-SSOT-014", "VRN_ENG397._TP": "VIA-03-RGX-007"},
 "conflicts": [{"key": "VRN_FinLexicon", "with": "VDF", "why": "同義字 '營收' 兩系統定義不同"}]}
```

`grants` 的鍵可以是子系統的暫編號、登記鍵(`SSOT|VRN2_SSOT`)或 `key`,值 = 核發號(格式照 `VIA_Numbering_SSOT`:`VIA-<子系統>-<類><三碼>`)。`conflicts` 每條指名對方系統與原因;修好後 VCGC 把它移出 `conflicts` 並寫進 `grants`。

### 2.3 子系統補填(VRN-2 已實作:`VRN2_SSOTSync_v0100.py sync`)

- 核發 → 登記冊該條 `ssot_id = 核發號` · `status = 已確認(VCGC)` · `granted_at`;衝突 → `status = 衝突 · 待人判(VCGC)· <原因>` · `ssot_id` 清空;其餘維持「暫編」。
- 內容有變才出新版登記冊(`VRN2_Component_Register_v+1.json` · 前版留著);寫 `contract/VRN2_NUMBER_STATE_latest.json`(granted / conflicts / pending / 來源)。
- 再把剩下的待核號(含衝突的)重寫請求冊;已確認的不再送。
- 啟動器 ⑤b 每輪在 ⑤ 元件登記之後跑;Workbench 交接頁有「SSOT · Regex · 同義字 · 政策編號協作」表(待核號 / 已核發 / 衝突 / 來源)。

## 3. 衝突與一致性(靠使用者 + AI)

- VCGC 偵測到的衝突只會出現在核發冊 `conflicts`;VRN-2 把它標成「待人判」並在 Workbench 列出,不自動改內容、不自動改號。
- 使用者 + AI 修改(改 VRN-2 的規則 / 同義字 → 出新版冊;或改 VDF 的;或 VCGC 判定一方為準)→ 指紋變 → 下一輪 ⑤ 登記冊記版本史 → ⑤b 重送請求 → VCGC 重比對 → 無衝突 → 核發。
- 三系統「手冊一致」的意思:同一個鍵在三本登記冊裡只有一個核發號;VCGC 的 `VIA_Numbering_SSOT` 是唯一的號碼來源。

## 4. VRN-2 本輪落地(v0144)

| 件 | 位置 | 狀態 |
|---|---|---|
| `VRN2_SSOTSync_v0100.py` | runtime v0144 · 倉 `functional modules/VRN/` | 自測 9/9(無核發冊 / 核發 + 衝突 / 自撞 / 無登記冊 / 不寫 VCGC 的檔)|
| 啟動器 ⑤b | ActivateVRN-2 v0144 | 每輪跑 · 收據 `ssot_sync` |
| Workbench v0101 | 交接頁 | 協作狀態表 |
| VDF 側 · VCGC 側 | 不在本倉 VRN-2 的範圍 | 本協定 §2 為契約;VCGC 目前的 `CGC_MDL237_NumberingSystem` 有 audit / apply(編號冊),尚無讀子系統請求冊寫核發冊的動詞 —— 那是 VCGC 自己的事,由操作員提給 VCGC 線 |
