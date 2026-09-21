# 批684 · PR #57 不用解衝突,它的內容已經在這條線上

操作員貼來 PR #57(`local/parallel-b600-bus-v0128` → main;12 commits · 49 檔 · **Merge conflicts**)。沒有字,只有截圖——先量它是什麼。

## 一 · PR #57 是什麼(量出來的)

| 成分 | commit | 本線狀態 |
|---|---|---|
| 側線 busy-bell 11 個 commit(VDF 審視 5 + 併主線 1 + 側線 5) | `7b90186d` … `225702bc` | VRN 件 批682 已原樣收進(位元相同);台帳 4 筆已入(0 筆新);規格項 `vrn_ssot_additive` 已在 |
| 操作員工作站落地件 | `da89abbc` local/parallel B600:EngineBus v0128(NEED_INPUT→ABSENT) | **本批收進**:`CGC_MDL148_EngineBus_v0128.py`(四十八檢 **49/49**;批600:引擎自述「[NEED_INPUT] run requires --in」不是 argparse 標準句,ARGERR_RX 漏接→假 RED;缺參數≠壞掉=ABSENT L16) |
| VDF 審視文 | `docs/VIA_VDF_StatusReview_20260921.md`(430 行) | **本批收進**(唯讀審視;零模型識別字;貼用區塊過 MDL157 廿六檢) |

衝突的 4 檔(元件冊 · 台帳 · 索引冊 · 總控頁 · 規格冊)全是**再生物或只增不減冊**:main(= 本線 批681–682,PR #56 已併)那一份是超集,PR 那一份是舊快照。不必解,也不該拿舊快照蓋新冊。

**沒收的**:`_patches/CGC_MDL148_EngineBus_v0128.py`(與 registry 那份位元相同=第二顆頭,只認 registry 正位)· `CGC_MDL064_SelftestGrid_v0431.py`(主線尾版已 v0433,v0431 是撞號中繼,批679c 已撤)· PR 自己的再生冊。

## 二 · 裁決建議(你的手)

- **PR #57:關掉即可**(本線已含其全部內容;main 已併 PR #56 = 本線 批681–682;批683–684 在本線等下一個 PR)。硬要併它會把舊快照併回去,而且要先解 5 個衝突。
- 第三條線 `claude/brave-goldberg-ri5k42`:仍未出現在遠端(Z70)。
- PR #53(busy-bell 原 PR):同理可關(內容 ⊂ PR #57 ⊂ 本線)。

## 三 · 本批實測(容器)

```
EngineBus v0128 --selftest        四十八檢(49 檢)OK 49 · FAIL 0(㊾ uni=ABSENT · qg=ABSENT · real=RED-fallback)
格子 --only 匯流排                 引擎調度匯流排十九檢 OK · 工作流重組台十二檢 OK
格子 --only 唯一接觸口             廿六檢 OK(含新收的 VDF 審視文貼用區塊)
registry-sync --apply             活 5993 · 新 0 · 變更 40(v0128 行號位移)
全格子(LL117)                     OK 255 · FAIL 20 · SKIP 6 · TIMEOUT 0(281 站;GRID_20260921_085108)· 對 批683 第六跑逐站相同:只在本批紅 0 · 只在 批683 紅 0
```
