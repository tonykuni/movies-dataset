# 批707 — 全景代讀:AI 讀卡,不讀原始碼

> 操作員令:「全景式讀取指令的功能整合起來…代為讀取節省 AI 讀取的 TOKEN…自動讀取識別錯誤 AST…避免傷害…串起來成唯一的標準功能…若已經有將它進行優化」

## 一、先量:已經有的是什麼、缺的是什麼(L116)

| 既有正主 | 做什麼 | 回答不了什麼 |
|---|---|---|
| `via-panorama`(CGC_MDL158 v0104) | 全樹**治理稽核**七類 + 純增量修復 + 多 TAB 報告 | 「這支檔裡有什麼、錯在哪一行」 |
| `via-peis`(CGC_MDL161 → `via_unified_engine.py`) | 跨家族**能力卡**(要先 scan 建庫) | 「這支檔第 N 行那個函式長什麼樣」 |

缺的正是 L65「AI 讀卡,不讀原始碼」的**單檔那一層**。所以**不另立引擎**(零九頭龍),補在全景正主上 → **CGC_MDL158 v0105**。

## 二、兩個新動詞(唯讀)

```
via-panorama read  <檔或夾…> [--json] [--full] [--max-defs N]
via-panorama slice <檔> <定義名|Class.method>
```

- `read`:骨架卡 = 匯入 · 定義樹(行號範圍 / 簽章 / 首行說明)· 問題清單 · token 帳。給資料夾=一檔一行全景,**真 bug 類排在前面**(SWALLOW 在 graceful 設計裡常是刻意的,不拿總數排)。
- `slice`:只回一個定義的原始碼(帶行號、裝飾器一起帶;同名兩個都列)。
- 支援 `.py`(AST)、`.ps1/.psm1`(文字剖析:function 範圍)、`.md`(標題)、`.json`(頂層鍵)。

## 三、錯誤判準分兩層,不混帳

- **治理七類**:照舊由 `audit_source` 出,只在 VIA 樹內算(樹外檔不背 VIA 的律)。
- **通用 AST 類(本批新增,只報位置)**:DUPDEF(同層同名定義,後者蓋前者;LL283)· UNREACH · BAREEXC · SWALLOW(LL151)· MUTDEF;PowerShell:PSDUPFN(LL283)· PSDOCSTR(LL182)。
- 通用類**不進 scan 的帳**:v0104 與 v0105 的 `scan` 輸出逐行比對相同(1523 檔 · 133 問題)。

## 四、避免傷害

- 零寫檔、不執行被讀的檔。自測 ㉗ 用「頂層會寫旗標檔」的樣品釘死:讀完旗標不得出現、位元組與 mtime 不變。
- 資料夾模式沿用活樹判準(尾版律、收容件/退役夾/md5 冊管夾不讀)。

## 五、實測(本境)

| 對象 | 原檔 ≈token | 骨架卡 ≈token | 省 |
|---|---|---|---|
| `CGC_MDL158 v0105` 單檔 1,797 行 | 28,174 | 1,349 | 95.2% |
| `Register-VIA-Commands-v0242.ps1` | 41,110 | 1,645 | 96.0% |
| `supportive modules/registry` 191 檔 | 1,305,695 | 4,472 | 99.7% |
| `slice` 取 `via-panorama` 一個函式 | 41,110 | 103 | 99.7% |

首跑即量到真 bug(只報不改,候令):`CGC_MDL135_EnvGovernance_v0114.py` L3587 `core_whitelist` 蓋掉 L368 的同名定義;`VRN_ENG086_FirstPageLogicBridge_v0113.py` DUPDEF 16;`VIA_SSOT_Unified.py` DUPDEF 15(樹上四份副本)。

## 六、自測與冊

- CGC_MDL158 自測 28 → **33 檢**(㉖ 骨架卡+五類+反例 · ㉗ 唯讀不執行 · ㉘ slice · ㉙ PowerShell · ㉚ 不進 scan 帳)。
- 格子 CGC_MDL064 v0460:站名改「三十三檢」,站仍走尾版 glob;`--only 全景稽核修復` 單站 OK。
- 元件冊:VCGC `registry-sync --apply`(新 16 · 變更 39)。
- 短令不新增:沿用 `via-panorama`(Register 已 `@args` 透傳),七處不必重做一輪(LL92)。
- 倉根 `CLAUDE.md`:讓之後的 AI session 自動先讀骨架卡。

## 七、本批自己踩的坑

- 我跑 `CGC_MDL064_SelftestGrid_v0460.py --help` 想看用法——它**不吃 `--help`**,直接把格子跑起來,重寫了 21 個已追蹤檔(冊 JSON、UI 頁)。已全數 `git checkout` 還原,只留刻意的元件冊。量的動作又一次改變了被量的東西(LL368)。已寫進 `CLAUDE.md`。

## 八、候令

- 真 bug 類(DUPDEF 等)要不要逐檔修:會改行為,本器只報位置(L56 ③)。說要修哪幾支,我分批修。
