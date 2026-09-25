# 批593 — 零損失證明過了還是壞了:綁定工廠的可變預設值

操作員令:`查清 VIA_AutoCodeGenerator 根因並補遷`

---

## 一、根因

原本:

```python
def load_json(path):
    if not path.exists():
        return {}                    # ← 每次呼叫都是一個**新的**空 dict
    return json.loads(path.read_text(encoding="utf-8"))
```

我遷成:

```python
load_json = _JS_MOD.bind_read(bom=False, missing={}, broken=_JS_MOD.RAISE)
```

那個 `{}` 是**工廠建立當下求值一次**的 —— 之後每次呼叫回的都是**同一個物件**。

而呼叫端會直接改它:

```python
chain_reg = load_json(self.ssot.codechain)
chain_reg.setdefault("codechains", [])
chain_reg["codechains"].append(obj)      # ← 改到的是綁在工廠裡的那一個
```

第二次呼叫拿到被改過的那一份,計數一路累加:

```
index_count 2 · product_count 3 · LNK-0004
```

`CGC_MDL155` 檢④⑨ 由綠轉紅。

**這是 Python 的可變預設值坑換了一件外套。**

---

## 二、最要命的一點:**位元組層級的零損失自測全過**

批592 我為 JSON 正典寫了兩層證明:

```
讀  9 種具名變體 × 4 組語料  全同
寫  4 種具名變體            **逐位元組相同**
```

兩層全綠,遷完還是壞。

因為差異不在**輸出的位元組**,在**回傳值的身分**(`is` 不是 `==`)——
**位元組永遠比不出這個。**

> **尺量對了東西才叫量過。量的維度不對,再多組語料都是零。**

這不是「自測寫得不夠多」,是**自測的盲區**。所以修法有兩條,缺一不可:

1. 正典對可變容器(`dict` / `list` / `set` / `bytearray`)一律回 `deepcopy` —— `_fresh()`
2. **自測加一檢是「呼叫端改回傳值,下一次不得被污染」**,而不是只比輸出 —— 檢⑤之二

→ **L76 綁定工廠的預設值律**

---

## 三、查案過程裡犯的錯,也記下來

| | |
|---|---|
| **單檔還原證明不了任何事** | 批592 我單獨把 MDL155 還原成已提交版,跑起來**一樣紅**,就誤判成環境狀態。錯在:**它依賴的是別支**。 |
| **決定性實驗要整批還原** | 把整批遷移暫存還原,一跑就 `OK 9 · FAIL 0` —— 那才證明是我改的。 |
| **再逐支二分** | 一次一支,不要猜。三支試完鎖定 `VIA_AutoCodeGenerator`。 |
| **根因要寫進自測** | 改對只救這一次;寫進自測才救下一次。 |

→ **LL147**

---

## 四、結果

| | 家族 |
|---|---|
| 批592 起點(模組層自己定義 JSON 讀寫) | **18** |
| 批592 遷完 | 1 |
| **批593 補遷完** | **0** |
| 改吃正典綁定 | **14 支** |

唯一沒併的 `CGC_MDL095_DeckServer` 是**類別方法**(HTTP 回應與請求 body),
本來就不該併,具名在 `NOT_FILE_IO`。

`NOT_MIGRATED` 清空;根因留在 `RESOLVED` —— **根因比結果值錢。**

```
全格 245 站   OK 243 · FAIL 0 · SKIP 2
```

## 五、三批整併累計

| 目標 | 起點 | 現在 |
|---|---|---|
| `newest`(批590/591) | 32 家族 | **1**(sha 凍結快照,不能動) |
| JSON 讀寫(批592/593) | 18 家族 | **0** |

## 六、登錄(L70:沒有動任何 `.ps1`)

- `SUP_MDL752_VIAJsonIO_v0100.py` —— `_fresh()` + 檢⑤之二;`NOT_MIGRATED` 清空、`RESOLVED` 記根因
- `VIA_AutoCodeGenerator_v0100.py` —— 補遷
- `CGC_MDL064_SelftestGrid_v0360.py` —— JSON 正典站 十一 → 十二檢
- `VIA_Policy_Laws_SSOT_v0100.json` —— **L76** · **LL147**(律 73→74 · 課 146→147)
- `VIA_AutoCode_Registry_v0100.json` —— 台帳 1160→1163
