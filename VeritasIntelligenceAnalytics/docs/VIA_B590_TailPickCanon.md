# 批590 — `newest` 併成一支正典:先分群,證零損失,再遷

操作員令:`CGC newest 33 族併成一支正典(最乾淨、風險最低)`

---

## 一、併之前先量:**32 份看起來同一件事,其實是 13 個行為群**

把 registry 尾版件裡每一支 `newest` / `_newest` 取出來,AST 正規化後比**骨架**(不比長相):

| 群 | 支 | 簽章 | 差在哪 |
|---|---|---|---|
| `f88659f52d` | **10** | `newest(pattern, root)` | 基準款 |
| `0cf7954847` | **6** | `newest(dirp, pat)` | **參數順序相反** |
| `229d9eae5e` | 3 | `_newest(dirp, pat)` | 同上,無守衛 |
| `814deab1ca` | 2 | `_newest(pat, root)` | **走 `rglob`**(遞迴),不是 `glob` |
| `4fbcbc161e` | 2 | `_newest(pat, root)` | 無型別註記 |
| `6226e981ca` | 2 | `_newest(pat, d)` | `d.exists()` 守衛 |
| `2c54462eb1` | 1 | `newest(folder, pattern)` | **缺件回 `str(folder/pattern)`**,不回 `None` |
| `358116394a` | 1 | `newest(pattern, root=HERE)` | **濾掉 stem 含 `_sha` 的** |
| `000606dfba` | 1 | `newest(pat, root=VIA)` | pat **帶目錄**,先 `root/pat` 再拆 |
| `8a121a3b6b` | 1 | `newest(pattern)` | 只有一個參數 |
| `69abf90773` | 1 | `_newest(dirp, pat)` | **按 `st_mtime` 排序**,不是版號字典序 |
| `52256fcb33` | 1 | `newest(pat, root=HERE)` | 預設值不同 |
| `c2dc24c114` | 1 | `_newest(d, pat)` | `is_dir()` 守衛 |

**這 13 群不是同一件事。**最大的兩群參數順序是**相反的** —— 盲目「併成一支」,
呼叫端不改就會把 root 當 pattern 傳,回錯檔,而且錯得無聲。

**`69abf90773` 那一支按 mtime 排序**:尾版律是「版號字典序最後一個」。
按 mtime 取,舊版檔案被碰過(複製、chmod、還原)之後就會選到舊版。
那是**不同的規則**,不是同一件事的另一種寫法。

→ **L75 正典化前先分群律**

---

## 二、正典:一個簽章,把差異變成**明示的選項**

`supportive modules/SUP_MDL751_VIATailPick_v0100.py`

```python
newest(root, pattern, *, recursive=False, exclude=(), on_missing=None, key="name")
newest_pr(pattern, root, **kw)      # 相容綁定:參數順序是 (pattern, root)
```

參數順序相反的兩群**各給一個具名綁定**,不用「看型別猜哪個是路徑」那種魔法 ——
猜錯就回錯檔,而且錯得無聲。看名字就知道自己吃哪一種:
`newest` = root-pattern · `newest_pr` = pattern-root。

`key="mtime"` 只為了**證明等價與相容遷移**而存在,不代表它是對的。
`CGC_MDL119_SystemAPI` 那一支要不要改成字典序,是操作員的裁定(LL90),正典不代改也不代判。

### 零損失證明是**機器可重跑**的

把每一群的**原始實作原樣抄進正典自測**當對照組,拿同一組語料逐一對答案:

```
⑫ 零損失:8 種具名變體 × 6 組語料 → **48 組全同**
⑩ key="mtime" 與 key="name" 在同一語料給**不同**答案
   (語料刻意把 mtime 做成跟版號相反 —— 證明它們本來就不是同一把尺)
[計] 12 檢 OK 12 · FAIL 0
```

**證不出來的那一群,不准遷。**

---

## 三、遷移:併要併到**家族數真的掉**

第一版我打算把 10 支的 `def newest` 換成「呼叫正典的橋函式」。
那樣每一支**還是有一個 `def newest`** —— 能力庫裡這一家族還在,家族數一個都不會掉,**等於沒併**。

改成**模組層綁定**:

```python
# ===== [VIA:TAILPICK-BRIDGE:v0100] =====
...(向上走找 SUP_MDL751,載入)...
if _TP_MOD is None:
    raise RuntimeError("[FAIL] 尾版取用正典缺席:…")   # 大聲壞掉,不 graceful 回退
newest = _TP_MOD.newest_pr
# ===== [VIA:TAILPICK-BRIDGE:END] =====
```

**正典缺席要大聲壞掉,不回退到本地實作** —— 回退等於把重複留著,
而且尾版取錯是**無聲**的錯(整條鏈指到舊引擎,沒有人會發現)。

| | 家族 |
|---|---|
| 遷移前,活樹尾版自己定義 `newest`/`_newest` | **32** |
| 遷移後 | **23** |
| 改吃正典綁定 | **9**(MDL042 / 050 / 064 / 069 / 087 / 125 / 135 / 142 · via_ocr_super) |

逐支冒煙:九支 `import` 之後 `newest` 都解到同一個尾版檔。

兩件沒遷,而且是對的:
- `via_selftest_grid_v0105_shac435dd5a` 是 **sha 凍結快照**,改它 sha 就對不上
  (MDL082 的變體濾掉 `_sha` 就是為此)。
- 自測格自己在被遷的九支裡 → 改用**新版號 v0358**(尾版律),v0357 還原。

→ **LL143**

---

## 四、全格當場抓到兩件,兩件都是我這批造成的,兩盞都對

```
全格 243 站  OK 240 · FAIL 2 · SKIP 2
```

| 紅 | 根因 | 處置 |
|---|---|---|
| **MDL156 加速器控制面** | 新開的 `SUP_MDL751` **忘了掛 `[VIA:ACCEL-BRIDGE]`**(批102 全樹導入令) | 補上 → **GREEN 37/37** |
| **MDL149 中央控管台** | 元件編號冊沒跟上新檔 | `registry-sync --apply`:變更 241 · **退役 8**(被移除的那幾支 `newest`,冊上誠實記成退役不是刪)→ 20/20 |

「全樹導入」就是全樹,**新開的檔沒有豁免權** —— 而且這種漏掉不會自己現形,要靠閘。

---

## 五、登錄(L70:沒有動任何 `.ps1`)

- `SUP_MDL751_VIATailPick_v0100.py` —— 尾版取用正典,十二檢
- `CGC_MDL064_SelftestGrid_v0358.py` —— +尾版取用正典站;本檔自己也改吃正典
- 8 支尾版就地改吃正典綁定(MDL042 / 050 / 069 / 087 / 125 / 135 / 142 · via_ocr_super)
- `VIA_Policy_Laws_SSOT_v0100.json` —— **L75** · **LL143**(律 72→73 · 課 142→143)
- `VIA_Component_Inventory_SSOT_v0100.json` —— registry-sync:變更 241 · 退役 8
- `VIA_AutoCode_Registry_v0100.json` —— 台帳 1149→1153

**回退路**:`git revert` 這一個 commit,九支就回到各自的本地實作;正典留著不影響任何人。
