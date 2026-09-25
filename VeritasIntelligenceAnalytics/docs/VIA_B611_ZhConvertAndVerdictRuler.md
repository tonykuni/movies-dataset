# 批611 — 工作站 23 紅分流:一支補殼扛三站,一把尺擋住真原因

操作員貼回批610 之前那一跑的 ALL-IN-ONE 全紀錄(v0106 + Grid v0365,落後 1 個 commit)。

```
15 步:GREEN 9 · NODATA 3 · RED 3
格子:OK 223 · FAIL 23 · SKIP 4 · 7,062s(序跑複判已翻綠 17 支)
```

這一批處理其中**最有槓桿的兩件**,都在容器裡複現得出來。

---

## 一、三站一個病根:沒裝 OpenCC(LL170)

工作站紅的三站:

| 站 | 紅在哪 | 畫面 |
|---|---|---|
| 知識堆疊轉接八檢(批141) | ② 補殼正規化 · ③b 正主件生效 | `2026年Q1,备抵呆账覆盖率` · `source=shim` |
| NLP 支援樞紐九檢(批157) | ② 正規化統一道 | `2026年Q1 备抵呆账覆盖率` |
| 三語 SSOT×MindMap 九檢(批158) | ③ 簡中→繁體正字收斂 | `联发科→聯發科` 沒入冊 |

**容器全綠。** 差別只有一個:容器裝了 `opencc`。把它擋掉,三站當場全紅,一次複現:

```bash
$ echo 'raise ImportError("模擬工作站:未裝 opencc")' > /tmp/noopencc/opencc.py
$ PYTHONPATH=/tmp/noopencc python3 VRN_ENG064_KnowledgeStack_v0101.py --selftest
  [FAIL] ② 補殼正規化 … (2026年Q1,备抵呆账覆盖率)
  [FAIL] ③b 批152 正主件生效 … (source=shim)
```

### 鏈條

`ENG067 → ENG066 → ENG064.load_stack() → npl_preprocessor`,**一支補殼扛三站**。

```python
            try:
                import opencc
                self._cc = opencc.OpenCC(...)
            except Exception:
                self._cc = None  # 誠實直通(OpenCC 缺)
```

註解寫「誠實直通」,可是直通等於**把簡體原樣交給下游**,而下游的冊全按繁體正字比對 ——
於是每一條都落空。尺把它判紅,判得沒錯;錯的是那句「直通」被當成一種降級,
其實它是**功能消失**。

### 補法不是叫操作員裝套件

`opencc` 是他機器上的東西,**不代裝**。所以給補殼一條零依賴的路:

- `opencc` 在 → 照用(行為零變更)
- `opencc` 缺 → 用凍結對照表

對照表不是我憑記憶造字 —— 是在容器裡**逐字元實跑 `opencc s2twp` 量出來的**:

```
掃描 CJK 碼位 28,096 · 逐字會變的 2,784
  备抵呆账覆盖率 → 備抵呆賬覆蓋率   OK
  联发科 → 聯發科                 OK
```

落在 `supportive modules/registry/VIA_ZhConvert_S2TWP_CharMap_v0100.json`(44 KB),
冊裡帶 provenance:工具、版本、config、掃描範圍、抽取日期。

**而且講白它補不到什麼**:這是**字元層**。片語層的台灣用詞(`軟件→軟體` 這一類)
補不起來,所以 `zh_which()` 要說得出走的是哪條路 —— `opencc` / `builtin_char` / `passthrough`。
不講的話就是假綠。

### 結果(兩條路都量過)

| 引擎 | 有 opencc | 無 opencc(= 工作站) |
|---|---|---|
| `VRN_ENG064_KnowledgeStack_v0102` | 十一檢 OK 11 · rc=0 GREEN | 十一檢 OK 10 · NODATA 1 · rc=2 |
| `VRN_ENG066_NLPSupportHub_v0100` | 九檢 OK 9 | **九檢 OK 9**(檔案一行未改) |
| `VRN_ENG067_MindMapSSOT_v0103` | 九檢 OK 9 | **九檢 OK 9**(檔案一行未改) |

ENG066/067 沒動過 —— 修在咽喉,下游自己就好了。

ENG064 的 `③b` 改判 **NODATA**:正主件**在**,是它的相依缺。
缺套件 ≠ 缺件 ≠ 壞掉,判紅會把真正的紅淹掉(L57)。站改掛 `nodata_ok`。

### 順手撈出來一句被吞掉的話

```python
    except Exception:
        return None          # ← 退回補殼的原因,就這樣沒了
```

補上因由之後,畫面第一次說得出來:

```
因由=RuntimeError: 缺少 OpenCC 依賴。請執行：pip install opencc-python-reimplemented
```

這句話**一直都在**,只是被 `except` 吞了。跟批610 的 LL168 同一課。

---

## 二、尺挑理由挑到狀態名(LL171)

```
[FAIL] 擷取單引擎八檢 · 23.8s · [FAIL-CLOSED] VIA_NET_CONSENT≠YES:同意閘未開,零外呼(絕不代設)
```

看起來像「同意閘沒開所以紅」。**不是。** 容器跑同一支 `VDF_ENG050_OrderFetch_v0101`:

```
  [OK] ④ 同意閘未開=rc2
  [計] 十檢 OK 10 · FAIL 0        rc=0
```

那行 `[FAIL-CLOSED]` 是某一檢**通過時**印的誠實訊息。
我批603 寫的理由挑選器用 `startswith("[FAIL")` 抓判決行,
`[FAIL-CLOSED]` 長得像,就被抓走了一個名額 —— **真正紅的那一檢被它擠掉**,
操作員拿不到任何可查的線索。

`[FAIL-CLOSED]` 是**狀態名**,不是判決。v0367 的尺:

```python
_STATE_NOT_VERDICT = ("[FAIL-CLOSED", "[FAIL_CLOSED", "[FAILCLOSED", "[FAIL-SAFE")
```

對照組(同一份輸入):

```
v0366: [FAIL-CLOSED] VIA_NET_CONSENT≠YES… / [FAIL] ⑨ 002 八車道分派齊 / [計] 十檢 OK 9 · FAIL 1
v0367: [FAIL] ⑨ 002 八車道分派齊 / [計] 十檢 OK 9 · FAIL 1
```

一行判決都挑不到時,也不再默默拿尾段充數,而是明說「挑不到逐檢判決行」。

---

## 三、被砍的站等於沒跑過,不是紅

`產品資格閘九檢` 工作站 300s 逾時被砍(容器 31s)。逾時 300→900。

**逾時不是紅燈,是「這一站沒跑完」** —— 兩者混在一起,紅燈的帳就算不準。

---

## 四、我自己在這一批踩的(LL172)

改逾時用了一條跨行的正則,**打到隔壁那一站**:
`產品資格閘` 還是 300,`十道並行編排` 被改成 900。
改完回讀一次才抓到。正則改設定表,錨點要釘在**同一行**內。

---

## 五、剩下的紅,誠實留白

這一批沒處理的,按可查性分三類:

**A. 你機器上的環境事實(我改不動,也不該代改)**
- `衝突哨兵 ⑫ PATH 黑名單前綴` —— `poppler\Library\bin` 與 `Downloads` 在 PATH 上
- `加速器控制面 L50` —— 解析首位帶可活化的 talib 路徑

**B. 需要你機器的料才判得準**
- `每日觀察摘要 ⑨`、`市場分析引擎 ④⑤`、`主動ETF×共識 ④`、`共識融合橋 ②`
- `環境治理 31 檢 ㉜㉞`(容器 46/46 綠,工作站這兩檢紅 —— 要你的 `05_EnvTools.log`)

**C. 尺本身還要再查**
- `擷取單引擎`:002 段有幾條車道**真的連了網**(容器看得到 `HTTP Error 404: 3324.TW`),
  所以這一站的結果跟當下網路狀態有關 —— 那是假綠/假紅的製造機。
  這一批只先讓它**說得出話**,沒有盲改。下一跑會印出真正紅的那一檢,再修。
- `治理台 UI Matrix ②`、`測試結果總表 ④` —— 兩者都是**從格子自己的失敗導出來的鏡像**,
  上游轉綠它們會跟著動,先不單獨修。
