# KNO × CodeChain × Index × Product — 全域治理規範 v1.0

單指令：`python VIA_AutoCodeGenerator.py <cmd> …`
SSOT：`vcg/ssot/`

---

## 0. 四語法（固定）

| 體系 | 格式 |
| --- | --- |
| CodeChain | `{SYSTEM}-{SUBSYSTEM}-{MODULE}-{FUNCTION}-{LIBNAME}-{LIBVER}` |
| KNO | `KNO-{DOMAIN}-{COUNTRY?}-{CATEGORY}-{TYPE}-{SOURCE}-{FREQ}-{VERSION}-{SEQ4}` |
| IDX | `IDX-{MARKET}-{COUNTRY}-{FAMILY}-{SYMBOL}-{SOURCE}-{FREQ}-{VERSION}-{SEQ4}` |
| PRD | `PRD-{ASSET}-{COUNTRY}-{FAMILY}-{SYMBOL}-{VENUE}-{FREQ}-{VERSION}-{SEQ4}` |

例：

```
VIA-VRN-MDL003-FNC025-SEABORN-V2.46
KNO-MACRO-US-PMI-HEAD-ISM-M-V1-0042
KNO-TA-MOMENTUM-RSI-VIA-D-V1-0007
IDX-EQ-US-BENCHMARK-SPX-SPGLOBAL-D-V1-0001
PRD-ETF-US-ENERGY-USO-ARCA-D-V1-0001
```

COUNTRY 可省略：DOMAIN ∈ {TA, STAT, ML} 且未給國家時不寫該段。

---

## A. KNO-Unified 欄位 Schema

| 欄位 | 允許值 | 來源 | 自動 |
| --- | --- | --- | --- |
| DOMAIN | MACRO LABOR CB TA STAT ML RISK OTHER | AI/人工 | ❌ |
| COUNTRY | US CN JP TW EU GLOBAL / null | AI/人工 | ❌ |
| CATEGORY | taxonomy.categories[DOMAIN] | AI/人工 | ❌ |
| TYPE | taxonomy.types[CATEGORY] | AI/人工 | ❌ |
| SOURCE | official/semiofficial/private/bank/internal | AI/人工 | ❌ |
| FREQ | M Q W D T A | AI/人工 | ❌ |
| VERSION | V1 RAW / V2 CLEANED / V3 SA / V4 FORECAST / V5 ENHANCED | AI/預設 V1 | ❌ |
| SEQ4 | 0001–9999 | SSOT latest_index+1 | ✔ |

指紋（冪等鍵，不含 SEQ）：
`{DOMAIN}-{COUNTRY|NA}-{CATEGORY}-{TYPE}-{SOURCE}-{FREQ}-{VERSION}`
同指紋重跑回傳既有編碼；`--force-new` 才燒新 SEQ。

---

## B. KnowledgeClassifier（落地版）

介面等同 Multi-Head Transformer；現行為 SSOT taxonomy + 規則頭，可替換 Encoder。

```
Raw Text → Tokenizer/Hints → Heads(DOMAIN/CAT/TYPE/COUNTRY/SOURCE/FREQ/VERSION)
        → Validator → AutoCode SEQ → SSOT/Ledger/Snapshot
```

| 任務 | 輸出 |
| --- | --- |
| Domain | MACRO… |
| Category | PMI / INFLATION / GDP / … |
| Type | HEAD / NEWORD / CPI / RSI / … |
| Country | US / … / null |
| Source | ISM / BLS / VIA / … |
| Freq | M / Q / W / D / T / A |
| Version | V1–V5 |

訓練資料格式（正式）：

```
{"text":"ISM Manufacturing PMI - New Orders (US)","label":{"domain":"MACRO","country":"US","category":"PMI","type":"NEWORD","source":"ISM","freq":"M","version":"V1"}}
```

---

## C. 全域治理規範（KNO × CC × IDX × PRD）

### C1 層級

| 層 | 物件 | Registry |
| --- | --- | --- |
| 知識 | KNO | kno.registry.json |
| 功能 | CodeChain | codechain.registry.json |
| 指標 | IDX | index.registry.json |
| 商品 | PRD | product.registry.json |
| 連結 | LNK | governance.registry.json |
| 詞表 | taxonomy | kno.taxonomy.json |

### C2 連結角色

| ROLE | 意義 |
| --- | --- |
| MEASURES | KNO 度量 IDX/PRD |
| COMPUTES | CodeChain 計算 KNO/IDX |
| PRICES | PRD 報價 IDX |
| HEDGES | PRD 對沖 IDX |
| FEEDS | KNO/IDX 餵給 CodeChain |

### C3 連結物件

| 欄位 | 說明 |
| --- | --- |
| link_id | LNKxxxx |
| kno | 可空 |
| codechain | 可空 |
| index | 可空 |
| product | 可空 |
| role | 上表 |

至少一鍵。四鍵皆須已存在於各自 Registry。同四元+role 冪等。

### C4 5/3 對映

| 軸 | 編碼 |
| --- | --- |
| 知識 | KNO |
| 數據 | PRD + SOURCE + VERSION |
| 指標 | IDX + KNO(MACRO/TA/…) |
| 方法/模型 | CodeChain + KNO(STAT/ML) |

---

## CLI（單一 PY）

```
python VIA_AutoCodeGenerator.py classify "ISM Manufacturing PMI - New Orders (US, Monthly)"
python VIA_AutoCodeGenerator.py kno --text "ISM Manufacturing PMI - New Orders (US, Monthly)"
python VIA_AutoCodeGenerator.py kno --domain TA --category MOMENTUM --type RSI --source VIA --freq D
python VIA_AutoCodeGenerator.py idx --market EQ --country US --family BENCHMARK --symbol SPX --source SPGLOBAL --freq D
python VIA_AutoCodeGenerator.py prd --asset ETF --country US --family ENERGY --symbol USO --venue ARCA --freq D
python VIA_AutoCodeGenerator.py generate --subsystem VRN --libname PANDAS
python VIA_AutoCodeGenerator.py link --kno KNO-… --codechain VIA-… --index IDX-… --product PRD-… --role MEASURES
python VIA_AutoCodeGenerator.py gov
python VIA_AutoCodeGenerator.py health
```
