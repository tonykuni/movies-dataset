# 批592 — `load.json` / `save.json`:量完才發現跟 `newest` 不是同一種問題

操作員令:`load.json save.json 繼續整併`

---

## 一、先量,結論就變了

| | 定義 | 行為群 | 最大一群 |
|---|---|---|---|
| `newest`(批590) | 32 份 | 13 群 | **10 支完全相同** → 合併收益大 |
| **JSON 讀寫(本批)** | **20 處** | **17 群** | 3 處 → 幾乎每處都不一樣 |

(debt 報的 `load.json` 83 檔 / `save.json` 35 檔含**版本史**;LL142 說過,債要以家族計。)

而且 **兩處根本不是檔案 IO**:

| | 它其實在做什麼 |
|---|---|
| `CGC_MDL095_DeckServer._json(self, obj, code)` | 發 **HTTP 回應**(`send_header` / `wfile.write`) |
| `CGC_MDL095_DeckServer._read_json(self, cap)` | 讀 **HTTP 請求 body**(Content-Type 驗證 · 拒 Transfer-Encoding · 容量上限) |

只是名字長得像。**併進去會出大事**,所以具名進正典的 `NOT_FILE_IO`,免得下一輪又被算成整合債。

---

## 二、所以做法不一樣:讀的收,寫的只收證得出位元組相同的

### 讀 —— 差異只有兩件事,而且不改變產出

- **編碼是活的不一致**:`utf-8-sig` 7 處 vs `utf-8` 5 處。
  同一個帶 BOM 的 JSON,**有些引擎讀得到,有些讀不到**。
- **缺檔與壞檔是兩個旋鈕,不是一個**。
  `VIA_AutoCodeGenerator.load_json` 是**缺檔回 `{}` 而壞檔直接拋** —— 一個 `default` 表達不出來。
  而且合成一個會**把壞檔說成「不存在」** —— 那是 LL138 的假的零。

```python
read(path, *, missing=None, broken=None, bom=True, strict=False)
```

### 寫 —— `indent` 與尾換行是**產出契約**,不得統一

原子寫 / `indent=1`(3 處)/ `indent=2` + **尾換行**(1 處)/ `default=str`。
把 `indent` 統一,等於讓所有 registry JSON 的 diff 整個炸開 ——
而本樹的慣例(registry JSON `indent=1`、**無尾換行**)本身就是要守的契約。

```python
write(path, obj, *, indent=1, ensure_ascii=False, atomic=True, mkdir=True,
      default=…, newline=False)      # 預設值不代表「對」
```

### 零損失

```
讀  9 種具名變體 × 4 組語料(正常 / BOM / 缺檔 / 壞檔)  全同
寫  4 種具名變體                                      **逐位元組相同**
```

**對照組必須原樣抄。**第一版我把 `try/except` 寫掉了,自測報「原 EXC ≠ 正典 None」——
**紅的是對照組不是正典**。對照組抄錯,證出來的零損失就是假的。

---

## 三、一支證不過,就不遷

遷 14 支,其中 **`VIA_AutoCodeGenerator` 換成正典綁定之後,`CGC_MDL155` 的檢④⑨ 由綠轉紅**:

```
index_count 2 · product_count 3 · LNK-0004     ← 計數在累加
```

我一開始誤判成環境狀態 —— 因為**單獨**把 MDL155 還原成已提交版跑起來一樣紅。
那個實驗證明不了任何事:**它依賴的是別支**。

決定性實驗是**把整批遷移暫存還原**:一跑就 `OK 9 · FAIL 0`。再逐支二分,鎖定 `VIA_AutoCodeGenerator`。

位元組層級的零損失自測是**過的**,所以差異在**呼叫端的狀態語意**,不在 `dumps` 的輸出 ——
**根因還沒查清楚。沒查清楚就不遷。**

那一支還原,MDL155 立刻回綠;它的名字與理由寫進正典的 `NOT_MIGRATED`,並加**檢②之二**釘住。
**留名字、留理由,不留一句「之後再說」。** → L75 · LL146

---

## 四、另一個踩到的坑:載入器放錯位置

同一檔有兩處要遷時,我由下往上改行號(對的),但把**載入器放在先處理到的那一處** ——
也就是檔案裡**後面**那一個。前面那一處先執行就 `NameError: _JS_MOD is not defined`,**四支當場炸**。

載入器要放在**最前面**那一處,後面的只補綁定。

---

## 五、結果

| | 家族 |
|---|---|
| 批592 起點(模組層自己定義) | **18** |
| **遷完** | **1** |
| 改吃正典綁定 | **13 支** |

剩的那一個就是證不過的 `VIA_AutoCodeGenerator`;另有 1 支(`CGC_MDL095_DeckServer`)是類別方法,
本來就不該併。

```
全格 245 站   OK 243 · FAIL 0 · SKIP 2
```

## 六、登錄(L70:沒有動任何 `.ps1`)

- `SUP_MDL752_VIAJsonIO_v0100.py` —— JSON 讀寫正典,十一檢
- 13 支尾版就地改吃正典綁定
- `CGC_MDL064_SelftestGrid_v0359.py` —— +JSON 讀寫正典站
- `VIA_Policy_Laws_SSOT_v0100.json` —— **LL145** · **LL146**(課 144→146)
- `VIA_AutoCode_Registry_v0100.json` —— 台帳 1156→1160
