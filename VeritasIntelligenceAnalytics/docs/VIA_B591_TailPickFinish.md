# 批591 — `newest` 收乾淨:32 → 1,剩下的那一個說得出為什麼不能動

操作員令:`OK`(接著遷剩下的 23 族)

---

## 一、結果

| | 家族 |
|---|---|
| 批589 量到的起點 | **32** |
| 批590 遷完 | 23 |
| **批591 遷完** | **1** |
| 改吃正典綁定 | **31 支** |

剩下的那一個是 `via_selftest_grid_v0105_shac435dd5a` —— **sha 凍結快照,改它 sha 就對不上**。
(`CGC_MDL082_MasterAutorun` 的變體特地濾掉 stem 含 `_sha` 的檔,就是為了這件事。)

**這才叫收乾淨:不是「還剩幾個沒空處理」,而是剩下的每一個都說得出為什麼不能動。**

---

## 二、群數一多,取名字就會失控

批590 用兩個名字(`newest` = root-pattern · `newest_pr` = pattern-root)蓋住了前幾群。
剩下的還差:**預設 root**(`HERE` / `VIA` / 只吃一個參數)、**rglob**、**exclude `_sha`**、
**mtime 排序**、**缺件回 pattern**(而且命中時也得回 `str`,型別不能兩樣)。

照原路走下去,名字會長成 `newest_pr_rglob_nosha_mtime` —— 那只是把 13 份實作換成 13 個名字,
**沒有比較好**。

所以正典 v0101 加一個**綁定工廠**:

```python
bind(*, order="rp"|"pr", root_default=None, stringify=False,
     recursive=…, exclude=…, on_missing=…, key=…)
```

選項留在**呼叫端**、看得見、可被質疑;回來的是**綁定不是 `def`**
(寫 `def` 的話能力庫裡那一家族還在,家族數不會掉 = 等於沒併,LL143)。

### 工廠繞出來的那條路也要證

自測的變體表不能只證直呼:

```
⑫ 零損失:8 種 → **15 種具名變體** × 6 組語料 = 48 → **90 組全同**
```

---

## 三、逐群配的綁定式(寫在腳本裡,可以被質疑)

| 綁定式 | 支 | 家族 |
|---|---|---|
| `bind(order="rp")` | 10 | MDL136 · 137 · 138 · 139 · 152 · 153 · 095 · 149 · 159 · via_conflict_guard |
| `bind(order="pr")` | 4 | MDL078 · 141 · 154 · via_tree_atlas |
| `bind(order="pr", recursive=True)` | 2 | MDL080 · MDL104(**rglob** 不是 glob) |
| `bind(order="pr", root_default=HERE, exclude=("_sha",))` | 1 | MDL082 |
| `bind(order="pr", root_default=HERE)` | 2 | MDL134 · MDL052 |
| `bind(order="pr", root_default=VIA)` | 1 | MDL133(pat 帶目錄,正典自己拆 parent/name) |
| `bind(order="rp", key="mtime")` | 1 | **MDL119** —— 違反尾版律的字典序,但**等價遷移不代改**(LL90) |
| `bind(order="rp", on_missing="pattern", stringify=True)` | 1 | MDL157 |

**遷移前先驗一關**:綁定式若用到 `HERE` / `VIA` 這種本檔區域名字,
要確認**它在注入點之前已經被指派**,驗不過判 `BLOCKED` 不硬幹 ——
**注入一個會 NameError 的綁定,比不遷更糟。**

逐支冒煙:22 支 `import` 之後都解到同一個尾版檔,**BAD/EXC 0**。

---

## 四、收尾實測

```
registry-sync --apply   變更 491 · **退役 20** · AST錯 0
                        (被移除的那些 newest,冊上誠實記成退役,不是刪 —— 只增不減)
全格 243 站             **OK 242 · FAIL 0 · SKIP 2**
```

---

## 五、登錄(L70:沒有動任何 `.ps1`)

- `SUP_MDL751_VIATailPick_v0101.py` —— +`bind()` 工廠 +`stringify`;變體 15 種 / 90 組全同
- 22 支尾版就地改吃正典綁定
- `VIA_Policy_Laws_SSOT_v0100.json` —— **L75 補綁定工廠與 NameError 那一關** · **LL144**(課 143→144)
- `VIA_Component_Inventory_SSOT_v0100.json` —— registry-sync:變更 491 · 退役 20
- `VIA_AutoCode_Registry_v0100.json` —— 台帳 1153→1156

**回退路**:`git revert` 這一個 commit,22 支回到各自的本地實作。
