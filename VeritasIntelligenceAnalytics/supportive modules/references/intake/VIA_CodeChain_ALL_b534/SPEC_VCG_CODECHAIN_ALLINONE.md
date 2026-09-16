# VIA CodeChain ALL-IN-ONE — Protocol v1.1

落地根：`VIA_CodeChain/`
引擎：`VIA_AutoCodeGenerator.py`
SSOT：`vcg/ssot/`

---

## 0. CodeChain 語法（不可變）

```
{SYSTEM}-{SUBSYSTEM}-{MODULE}-{FUNCTION}-{LIBNAME}-{LIBVER}
VIA-VRN-MDL003-FNC025-SEABORN-V2.46
```

| 欄位 | 格式 | 自動生成 | 人工輸入 | 來源 |
| --- | --- | --- | --- | --- |
| SYSTEM | VIA | ❌ | ✔ | 請求 |
| SUBSYSTEM | VRN / VDF / VAP | ❌ | ✔ | 請求 |
| MODULE | MDLxxx | ✔ | ❌ | module.registry.json |
| FUNCTION | FNCxxx | ✔ | ❌ | function.registry.json |
| LIBNAME | SEABORN / PLOTLY / … | ❌ | ✔ | 請求，必須已註冊 |
| LIBVER | Vx.xx | ✔ | ❌ | lib.registry.json |

規則：

- LIBNAME = 語意名稱，禁止 LIB001、禁止 LIB-VRN-XXX
- LIBVER 禁止人工輸入
- MODULE / FUNCTION 禁止人工指定 index（可指定既有 `module_code` 掛功能）
- CodeChain 全域唯一
- 每次生成必須 Ledger + Version Snapshot + Registry 寫入

遞增規則（落地修正）：

| 模式 | MODULE | FUNCTION |
| --- | --- | --- |
| 預設 generate | 沿用該 SUBSYSTEM 最新 MODULE | latest_index + 1 |
| `--new-module` | latest_index + 1 | latest_index + 1 |
| `--module-code MDLxxx` | 使用既有 MODULE | latest_index + 1 |

---

## A. Artifact Promotion 整合（正式版流程）

### A1 狀態機

| 狀態 | 可轉入 |
| --- | --- |
| DRAFT | VALIDATED, RETIRED |
| VALIDATED | STAGED, DRAFT, RETIRED |
| STAGED | PROMOTED, VALIDATED, RETIRED |
| PROMOTED | FROZEN, RETIRED |
| FROZEN | RETIRED |
| RETIRED | ∅ |

### A2 流程矩陣

| 階段 | 模組 | 動作 | 說明 |
| --- | --- | --- | --- |
| 1 | Gateway.Router | 解析 | codechain + target_state + kind + ref |
| 2 | Registry.Lookup | 查找 | codechain.registry.json |
| 3 | Transition.Guard | 驗證 | 僅允許矩陣內轉移 |
| 4 | Artifact.Upsert | 建立/更新 | artifact.registry.json |
| 5 | Chain.Patch | 回寫 | promotion.state / artifact_id |
| 6 | Ledger.Write | 審計 | from / to / who / when |
| 7 | Version.Snapshot | 快照 | /versions/codechain/ |
| 8 | Return | 回傳 | 更新後 CodeChain 物件 |

### A3 生成路由

```
User → VCG Gateway → AutoCodeEngine.promote
     → artifact.registry.json
     → codechain.registry.json
     → Ledger
     → Version Snapshot
     → Return
```

### A4 Artifact 欄位矩陣

| 欄位 | 說明 |
| --- | --- |
| artifact_id | ARTxxxx |
| kind | FUNCTION / MODEL / FACTOR / ENGINE |
| codechain | 綁定編碼 |
| ref | 外部路徑或模型 ID |
| state | Promotion 狀態 |
| worldline | 可空 |
| engine | 可空 |
| factor | 可空 |

### A5 CLI

```
python VIA_AutoCodeGenerator.py promote VIA-VRN-MDL003-FNC025-SEABORN-V2.46 --state VALIDATED
python VIA_AutoCodeGenerator.py promote VIA-VRN-MDL003-FNC025-SEABORN-V2.46 --state STAGED
python VIA_AutoCodeGenerator.py promote VIA-VRN-MDL003-FNC025-SEABORN-V2.46 --state PROMOTED --kind MODEL --ref models/alpha_v1.pkl
```

---

## B. 世界線 × 引擎 × 因子 整合矩陣

### B1 維度登記（SSOT）

| 維度 | Registry | 預設代碼 |
| --- | --- | --- |
| 世界線 | worldline.registry.json | WL-BASE / WL-STRESS / WL-ALPHA |
| 引擎 | engine.registry.json | ENG-QUAD / ENG-HYPER / ENG-FORGE / ENG-NOVA |
| 因子 | factor.registry.json | FCT-MOM / FCT-VOL / FCT-FLOW / FCT-MACRO |

### B2 關聯矩陣（CodeChain 為主鍵）

| CodeChain | SUB | LIB | 世界線 | 引擎 | 因子 | Promotion |
| --- | --- | --- | --- | --- | --- | --- |
| VIA-VRN-MDL003-FNC025-SEABORN-V2.46 | VRN | SEABORN | WL-* | ENG-* | FCT-* | DRAFT→… |

允許組合：任一已註冊 WL × 任一已註冊 ENG × 任一已註冊 FCT。
未綁定欄位 = null（合法，生成時可後綁）。

### B3 綁定流程

```
User → VCG Gateway → AutoCodeEngine.bind
     → 驗證 WL/ENG/FCT 均存在於 SSOT
     → 回寫 codechain.registry.json
     → Ledger + Snapshot
     → Return
```

### B4 CLI

```
python VIA_AutoCodeGenerator.py generate --subsystem VRN --libname PLOTLY --worldline WL-ALPHA --engine ENG-NOVA --factor FCT-FLOW
python VIA_AutoCodeGenerator.py bind VIA-VRN-MDL003-FNC026-PLOTLY-V5.22 --worldline WL-STRESS --engine ENG-HYPER --factor FCT-VOL
python VIA_AutoCodeGenerator.py matrix
```

### B5 NLP 擷取欄位（固定鍵）

`system, subsystem, module.code, module.index, function.code, function.index, library.name, library.version, codechain, worldline, engine, factor, promotion.state, promotion.artifact_id`

---

## C. VCG 全域路由圖（正式版）

### C1 層級矩陣

| 層級 | 模組 | 說明 |
| --- | --- | --- |
| Gateway Layer | AutoCodeEngine | 生成 / 綁定 / 晉升 / 查詢 |
| Registry Layer | codechain.registry.json | 保存完整 CodeChain |
| SSOT Layer | lib / module / function / worldline / engine / factor | 權威來源 |
| Artifact Layer | artifact.registry.json | Promotion 產物 |
| Version Layer | /versions/codechain/ | 不可變快照 |
| Ledger Layer | ledger/audit.log | 審計 |
| Enforcement Layer | Sync | 推送到 VRN / VDF / VAP |
| Drift Layer | health() | LIBVER / 重複 / 語法 |
| Monitoring Layer | RYG | GREEN / YELLOW / RED |

### C2 路由表

| 路由 ID | 路徑 |
| --- | --- |
| GENERATE | User → VCG Gateway → generate → Registry → SSOT → Ledger → Version → Return |
| READ | Subsystem → SSOT.Read → codechain.registry.json |
| BIND | User → VCG Gateway → bind → WL/ENG/FCT SSOT → Ledger → Return |
| PROMOTE | User → VCG Gateway → promote → artifact.registry → Ledger → Version → Return |
| HEALTH | Monitor → health → RYG |
| SYNC | Enforcement → Push 至 VRN/VDF/VAP |

```
python VIA_AutoCodeGenerator.py routes
python VIA_AutoCodeGenerator.py health
```

### C3 SSOT 檔案地圖

```
vcg/ssot/
  registry/
    lib.registry.json
    module.registry.json
    function.registry.json
    codechain.registry.json
    artifact.registry.json
    worldline.registry.json
    engine.registry.json
    factor.registry.json
  ledger/audit.log
  versions/codechain/
```

---

## CLI 全表

```
python VIA_AutoCodeGenerator.py generate --subsystem VRN --libname SEABORN
python VIA_AutoCodeGenerator.py generate --subsystem VDF --libname NUMPY --new-module
python VIA_AutoCodeGenerator.py generate --subsystem VRN --libname PANDAS --module-code MDL003
python VIA_AutoCodeGenerator.py lookup VIA-VRN-MDL003-FNC025-SEABORN-V2.46
python VIA_AutoCodeGenerator.py list
python VIA_AutoCodeGenerator.py bind <CC> --worldline WL-BASE --engine ENG-QUAD --factor FCT-MOM
python VIA_AutoCodeGenerator.py promote <CC> --state VALIDATED
python VIA_AutoCodeGenerator.py matrix
python VIA_AutoCodeGenerator.py health
python VIA_AutoCodeGenerator.py routes
```

SSOT 根目錄可覆寫：`--ssot /path/to/vcg/ssot`
