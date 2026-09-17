# PEIS 能力引擎(批568 收留 · 2026-09-17)

> 操作員令:「將 `session_01FQMN8uBxreDrzmDUpPrXTG` 引擎整合進來」+ PEIS 六功能規格
> +「用引擎去執行以節省 TOKEN」+「你自己收留整合後啟動她」。

---

## 一、為什麼是「收留」而不是「重寫」

先量。PEIS 那六件功能——搜尋領域 → AST 全景分析 → 聚眾 → 低風險無損耗合併 →
完整測試 → 鎖定 → 能力抽象 → 快速截取——**已經有一支寫好的正主**:

| 項目 | 值 |
|---|---|
| 引擎 | `via_unified_engine.py` v0200(`VIA-VIA-ENG996`) |
| 來源 | `github.com/tonykuni/via-vdf-vrn` @ `412e9af7fac6`(branch `claude/charming-brown-2qaooh`) |
| 規模 | 6,628 行 · **純標準庫** · 零網路 · 零安裝 · 不改來源檔 |
| 它自己的自測 | **69/69 PASS**(本境實跑過) |

照規格再寫一支,就是**第二顆頭**(零九頭龍),而且要把別人已經驗過的 69 檢重驗一次。
所以做法回到 VIA 老規矩:**正本收容 + 一個掛線口**。

```
functional modules/VIA_PEIS/references/intake/PEIS_UnifiedEngine_b568/
  ├── via_unified_engine.py          282 KB  ← 正本,一個 byte 不改
  ├── VIA_PEISCapabilityMap.via        6 KB  ← CME v2.0 能力表(26 能力字典)
  ├── VIA_UNIFIED_ENGINE.md           24 KB
  ├── governance_engine.py             2 KB
  └── _INTAKE_MANIFEST_b568.json             ← 來源 repo/commit + 每檔 md5/sha256
```

掛線口 `supportive modules/registry/CGC_MDL158_PEISCapabilityEngine_v0100.py`
只做 VIA 這一側該做的事:誠實四態 · 報告落點 · 加速器橋 · 紀律斷言,**subprocess 代跑正本**。

## 二、六功能對照(規格 → 正本動詞)

| 規格 | 正本 | 掛線口 |
|---|---|---|
| ① 搜尋領域 → AST 全景 → 找關聯引擎 → 功能群組 | INTAKE → SCAN → CLUSTER | `via-peis scan --family …` |
| ② 低風險、無損耗地合併功能 | CLUSTER(指紋相同折疊 `dup`;不同實作**保留為 variant**,不覆寫) | 同上 |
| ③ 低風險地合併指令順序 | `govern` 十一階段鏈 | (正本直呼) |
| ④ 完整測試直到完美運作 | TEST(影子對照,浮點容差 1e-9)+ EVIDENCE | 掛線口 ④ 驗它自己的 69 檢 |
| ⑤ 成功引擎鎖定 + 能力抽象 | LOCK(**測試 PASS 才 SEALED**;已封印永不解封)+ ANNOTATE | `via-peis cards` |
| ⑥ AI 快速截取能力 | `run --capability`(RESULT_ONLY) | `via-peis run <能力> --params JSON` |
| 啟動條件:無重複則不啟動 | 折疊 0 | 掛線口回 **NODATA(rc=2)**,不報紅 |

## 三、啟動實測(2026-09-17,本境真跑,不是規劃)

| 家族 | 檔 | 函式 | 能力 | SEALED | 折疊 | 近似 | 原文 token | capsule | 省 |
|---|---|---|---|---|---|---|---|---|---|
| VDF + VRN | 674 | 14,984 | 2,606 | 140 | **10,436** | 2,864 | 7,264,857 | 6,092 | **99.92%** |
| CGC + SUP | 1,780 | 31,416 | 7,291 | 374 | **18,694** | 42,902 | 13,777,125 | 7,277 | **99.95%** |
| VAP | 37 | 806 | 324 | 21 | 374 | 108 | 342,584 | 6,728 | 98.04% |

能力庫:`VIA_Reports/peis/VIA_Capability_Store.sqlite`(51 MB · 2,606 張卡 · 140 SEALED;**已 gitignore,不進倉**)。

**快速截取層實證**:

```
via-peis run misc.upside --params '{"target": 180, "current": 120}'
  → {"c":"misc.upside","a":"RUN","r":"RESULT_ONLY","status":"GREEN","result":0.5,"path":"sandbox"}
```

該能力**折疊了 28 份實作**。AI 只讀那張卡(`sig` + 探針 in→out),不必讀 28 份原始碼。

## 四、收下來真跑才看得到的三件事

1. **省略 `--db` 的話能力庫只在記憶體=白掃一場。** 掛線口第一版就是這樣,`cards`/`report`
   全讀不到。現在一律掛 `--db VIA_Reports/peis/VIA_Capability_Store.sqlite --root <VIA>`,
   並加一檢盯著(⑰)。
2. **`--params` 傳物件會在正本的沙箱車道壞掉。** 正本是 `def_execute_guarded(..., list(payload or []))`,
   傳陣列沒事(`[180,120]` → 0.5),傳物件就把 key 當引數(`list({'target':..})` = `['target','current']`
   → `TypeError`)。可是操作員規格寫的正是物件 `RUN(math, {symbol:"2330"})`。
   **正本零觸碰**,所以轉接寫在掛線口:物件依**能力卡上的簽章順序**攤平成位置引數;
   簽章讀不到就**不猜**,原樣送 `--params` 並把正本的話原封回報。
   > ⚠️ 這是**上游正本的缺陷**,值得回報給 `via-vdf-vrn` 那一側修;本庫只做不改正本的轉接。
3. **小語料的 token 帳是負的,正本照實報 −1511%。** 沒有為了帳面好看放寬門檻——
   這比帳面好看更值得信。

## 五、紀律(掛線口自己守的,19 檢逐條驗)

- **正本零觸碰**:每檔 sha256 與 manifest 逐字比對;真跑後**比 bytes** 證明來源檔沒被改。
- **零網路 · 零安裝**:不 import `requests/httpx/urllib`,不呼叫 `pip/conda`;代跑時明示 `VIA_NET_DISABLED=1`。
- **不代設同意閘**:本口不寫任何 `VIA_*_CONSENT` / API key。
- **不提供 `--apply`**:能力表落地與引擎鎖定是**操作員的裁定**(LL90 同族)。
  要落地請直接對收容正本下令。
- **掃描排除**收容件與退役件(正本零觸碰;退役件不是活樹)。

## 六、一貼即用

```powershell
Set-Location 'D:\OneDrive\文件\GitHub\movies-dataset\VeritasIntelligenceAnalytics'
git pull origin claude/via-envmanager-governance-7cls8h
. (Get-ChildItem 'Register-VIA-Commands-v*.ps1' | Sort-Object Name | Select-Object -Last 1).FullName

via-peis                              # 收容正本在不在 + 它自己的 69 檢
via-peis scan --family vdf,vrn        # 聚眾→測試→鎖定→能力卡(AUDIT;零網路;不改來源)
via-peis scan --family cgc,sup        # VIA 治理側
via-peis report                       # token 節省帳
via-peis cards misc.upside            # 讀一張能力卡
via-peis run misc.upside --params '{"target":180,"current":120}'
```
