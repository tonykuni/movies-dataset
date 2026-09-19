# 批610 — VDF 審計閘:「pass audit and run perfectly」做成一支可重跑的引擎

操作員令:`vdf pass audit and run perfectly`。

在此之前,「VDF 跑得起來」這句話只存在於我一次性的便條腳本裡。
便條會過期,引擎不會 —— 所以這一批的主件是 `VDF_ENG091_VdfAuditGate_v0100.py`。

---

## 裁決(容器實測)

```
[列冊] 活樹 58 支待審 · 豁免 8 支(附理由;含本閘自己)
[計]   GREEN 49 · NODATA 9 · RED 0 · 缺動詞 0
[裁決] rc=2 (NODATA)
```

`rc=2` 不是「沒過」。它誠實地說:**沒有任何一支是壞的,少的是套件**
(`RICH_AVAILABLE` / `AKSHARE_AVAILABLE` / `GSPREAD_AVAILABLE` / `PDR_AVAILABLE` / `XLRD_AVAILABLE` …)。
容器沒裝、工作站有裝的,判 NODATA 不判 RED —— **不代裝套件**(那是操作員的手)。

---

## 一、我的尺自己先壞了(LL166)

便條版審計 6 路平行跑,結果:

| 跑次 | 平行段判紅 | 逐支單獨跑 |
|---|---|---|
| 第一跑 | ENG060 · ENG062 · ENG072 | 全是 GREEN / NODATA |
| 第二跑 | ENG061 · ENG062 · ENG070 | 全是 GREEN / NODATA |
| 第三跑 | (又換了兩支) | 全是 GREEN / NODATA |

**同一棵樹、同一把尺,紅的名單每次都不一樣。**
這個「不可重現」本身就是 DuckDB 鎖撞的指紋,不是引擎的病。

格子(`CGC_MDL064_SelftestGrid`)早就有序跑複判這一段,我自己新寫的尺沒有 ——
**壞的是尺,不是引擎。**

ENG091 把序跑複判做成骨頭而不是選配,並且**兩條路都要走過**才算跑過(L83):

- 合成 `A_holder.py`(持鎖 3 秒)· `B_contended.py`(見鎖即紅)· `C_reallybad.py`(永遠紅)
- 自測⑧ 要求 B 在平行段判紅、序跑段**轉綠**
- 自測⑨ 要求 C 兩段都紅,**真紅不准被複判洗綠**

---

## 二、有自測不等於有動詞(LL167)

`VDF_MDL101_OutputManager.py` 早就有一段寫得好好的自測 —— 但它掛在裸
`if __name__ == "__main__":` 底下,沒有 `--selftest` 旗標。

對全樹契約(L53)來說,它跟「根本沒有自測」一模一樣:格子點不到它,審計把它算成缺件。

所以補法不是「去寫一個自測」,而是「把既有行為接上統一動詞」。
`[VIA:SELFTEST-VERB:v0100]` 段補進 **10 支**活樹檔(只增不減,既有呼叫方一行未改):

```
VDF_ENG019_MDL501FetchContractManager.py       VDF_MDL101_OutputManager.py
VDF_ENG044_MDLXXXYFinanceGlobalDataFetcher.py  VDF_MDL104_RegistryLoader.py
VDF_MDL002 / MDL003 / MDL007  ×  根與 engine/ 各一份
```

新動詞六檢,每一檢都是真的:

| 檢 | 量什麼 |
|---|---|
| ① | 模組載入無例外(import 即死的引擎印不出這一行) |
| ② | 宣告符號齊備(逐檔點名 main / 各 Fetcher / 各 Manager) |
| ③ | **零連線實證** —— 自測期間攔截 `socket.socket.connect`,有人連線就判紅 |
| ④ | 動詞路由在 main 之前(讀自己的原始碼比對位置) |
| ⑤ | 橋接件完好(ACCEL-BRIDGE / NET-BRIDGE 標記齊) |
| ⑥ | 套件旗標盤點 —— **缺件 = NODATA,不是紅燈** |

---

## 三、模組層早用:一個炸很大聲,一個不出聲(LL168)

補完動詞一跑,`VDF_MDL003_SentimentMacroEngine` 當場現形:

```
File ".../VDF_MDL003_SentimentMacroEngine.py", line 224, in <module>
    FRED_API_KEY = (os.environ.get("FRED_API_KEY", "").strip() or _via_fred_keyfile())
NameError: name 'os' is not defined. Did you mean: '_os'?
```

PARAM 段在檔尾那批 `import os` / `from pathlib import Path` **之前**就用了它們。
**這支引擎 import 即死 —— 根與 `engine/` 兩份一起死。**
對照組(批610 修改前的正本,`exec_module`)複現:`rc=1` / 同一個 `NameError`。

同一段裡還有第二個,而它**不出聲**:

```python
def _via_fred_keyfile() -> str:
    try:
        _p = Path(__file__).resolve()     # ← Path 此時也還沒 import
        ...
    except Exception:
        pass
    return ""                              # ← 永遠回空字串
```

`Path` 一樣未定義,但外面包著 `except Exception: pass` —— 它不死,它**安靜地永遠回空字串**。
FRED 鑰匙檔車道就此失效,而且看起來像「使用者沒放鑰匙」。

**一個是紅燈,一個是假綠;假綠那個躲得更久。**

補法只增不減:在首次使用之前補上標準庫 import(`[VIA:EARLYIMPORT-FIX:v0100]`),
檔尾重複 import 無害,既有行為一行未改。

---

## 四、MDL105 的冊找不到,不是冊壞掉

`VDF_MDL105_CrossValidator.py` 自測原本直接 `RegistryLoader("VDF_MDL403_RegistryFull.json")` ——
裸檔名。冊的正典位置在 `supportive modules/registry/`,所以自測必噴 `FileNotFoundError`。

改為三處解析(本夾 → 正典冊夾 → cwd),找得到就照跑:

```
✓ Loader loaded 238 items  (冊 .../supportive modules/registry/VDF_MDL403_RegistryFull.json)
```

找不到時**誠實停**,不裸噴 traceback:

```
[ABSENT] 冊 VDF_MDL403_RegistryFull.json 不在(本夾 / supportive modules/registry / cwd 都找過)
         **缺冊不是壞掉**:先把冊放回正典位置再跑本自測。
rc = 3
```

兩個方向都量過才算修好。

---

## 五、豁免冊:沒理由的豁免等於假綠(新法 L87)

審計要排除檔案,就得說出憑什麼。7 支豁免,逐支附理由,**跑的時候連理由一起印**:

| 檔 | 憑什麼豁免 |
|---|---|
| `_from_vap_iso_cleanup/VDF_MDL003_…` | VAP 隔離清理殘件:非活樹,留作回溯;正本在 VDF 根與 `engine/` |
| `_vdf_system/macro_manifest_fetch_runs/RUN_…/VDF_ManifestFetchAdapter.py` | 跑次產物快照:那是一次跑留下的輸出,不是活引擎 |
| `engine/candidates/sector_rotation_capital_flow_engine.py` | 候選夾:尚未升正的試作 |
| `tools/VDF_InjectAccelNetBridges_v0104.py` | 一次性注入工具,跑完即退場(同批605 `_patches/` 理由) |
| `_vdf_engines/sentiment_strength/VDF_Engine_{aaii_sentiment,cnn_fear_greed_proxy,sentiment_strength}.py` | 純函式庫模組(無 main;由 `SUP_MDL566_SentimentStrengthRouter` 呼叫):自測歸呼叫端 |
| `engine/VDF_ENG091_VdfAuditGate_v*.py`(整個家族) | 本閘自己:判定器不自判(LL133);它的自測由格子站「VDF 審計閘十檢」跑,覆蓋沒有掉 |

理由同時決定豁免的**壽命**:`candidates/` 的理由是「尚未升正」,
所以升正那一刻豁免自動失效;一次性工具的理由是「跑完即退場」,所以它再被改就該重新審。

ENG091 自測第①檢就是驗「每筆理由長度 ≥ 8 字」—— 豁免項不是消失,是換一種方式被看見。

---

## 五之二、棘輪當場抓到寫閘的人(LL169)

ENG091 寫完,跑全格子 —— **紅了**:

```
[FAIL] 制度健全度稽核二十二檢(CGC_MDL164)
       ⑰ 自我指涉閘(LL133 棘輪):基線外不得再冒出「回答誰引用卻沒排掉自己家族」的判定器
       (共 20 支 · SAFE 4 · WEAK_SELF 0 · NO_EXCLUDE 16 · 基線外 1)
[NO_EXCLUDE] **新增!**  functional modules/VDF/engine/VDF_ENG091_VdfAuditGate_v0100.py
```

那一支就是我自己。ENG091 掃 VDF 樹回答「誰要受審」,卻沒把自己的家族排掉。

兩條路:把它加進基線(紅燈立刻消失),或把它修好。
**加進基線等於把棘輪拆掉** —— 基線的意思是「這些是歷史債,逐支還」,
不是「紅燈太吵就把它收編」。

修法是排掉**整個家族**,不是只排 `__file__` 那一支
(只排一支的話,一開新版號,舊版就變成被自己數進去的受審者):

```python
_SELF_FAMILY = Path(__file__).stem.rsplit("_v", 1)[0]

def is_self_family(p: Path) -> bool:
    return p.stem.rsplit("_v", 1)[0] == _SELF_FAMILY
```

排掉之後照 L87 仍要連理由一起印,並補上自測第⑪檢(合成同家族兩個版號 + 一支外人,
驗「待審只剩外人、豁免只剩本家族尾版、理由一致」)。

複量:`SAFE 4 → 5` · **基線外 0 支(棘輪守住了)** · 自測 10 檢 → 11 檢。

**這一批最值得記的不是我寫了新閘,是既有的棘輪在同一個小時內抓到了寫閘的人。**

---

## 六、怎麼跑

```bash
# 審計(預設):列冊 → 平行跑 → 序跑複判 → 報告
python "functional modules/VDF/engine/VDF_ENG091_VdfAuditGate_v0100.py" --audit

# 參數:--workers N(預設 6) --timeout S(預設 300) --root PATH --json PATH
# 自測(零連線、零寫樹,只在暫存夾合成假樹)
python "functional modules/VDF/engine/VDF_ENG091_VdfAuditGate_v0100.py" --selftest   # 十一檢 rc=0
```

格子新站:**VDF 審計閘十檢**(自測本身十一檢)(`CGC_MDL064_SelftestGrid_v0366`)。

---

## 七、這一批沒做的(誠實留白)

- `VDF_ENG072_StoryRotationBridge_v0101` 仍是 **NODATA**:它要 `tw_chip_inst` / `tw_chip_margin`,
  得先跑 `via-chip` / `via-daytrade`。**缺料不是壞掉**,而補料是操作員的手。
- 9 支 NODATA 的共同原因是容器沒裝 `rich` / `akshare` / `gspread` / `pandas_datareader` / `xlrd`。
  工作站有裝的話同一把尺會判 GREEN —— 請用 `via-allinone` 跑一次,以工作站的數字為準。
- `_from_vap_iso_cleanup/` 那份 MDL003 帶著同一個模組層早用 bug,**沒修**:
  它在豁免冊裡(非活樹),修它等於在殘件上做功。若哪天要升回活樹,先套 L53 與這個補法。
