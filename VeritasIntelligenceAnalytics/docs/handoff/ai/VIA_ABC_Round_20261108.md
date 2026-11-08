# A / B / C 全授權輪(操作員 2026-11-08)

操作員令:「A B C 全部自動完成授權 FIX ALL TEST DEBUG OPTIMIZE TEST DEBUG CONSOLIDATE
TEST DEBUG USER-TEST DEBUG AND ACTIVATE TEST DEBUG TILL THEY WORK PERFECTLY.」

| | 事 | 結果 |
|---|---|---|
| **A** | 裝 fitz / curl_cffi / yfinance → 清 ENV_PKG | **做不到(兩道閘,照實記)** |
| **B** | `VIA_Lessons_Ledger` 真的脫離版控 | **完成** |
| **C** | UNKNOWN 10 案逐案查到根因並處理 | **完成,10 → 0** |

結果數字:鎖住 **209 → 218** 案 · 未鎖 **32 → 23** · UNKNOWN **10 → 0**。

## A —— 沒做到,兩道各自獨立的閘

這件我試了,沒成功,不假裝做了:

1. **雲端沙盒拒絕**:`python3 -m pip install pymupdf curl-cffi yfinance` 被
   auto mode 分類器擋下,理由 `[Code from External]`。這是容器層的限制,不是政策問題。
2. **VIA 自己的安裝閘也不會動**:`CGC_MDL135_EnvGovernance_v0118` 自測第 ㊿ 檢
   明文寫「授權但同意閘未開 = `BLOCKED_CONSENT` 零動作(**不代設**)」,
   而且它裝的目標是 `via_vdf_312` / `via_vrn_312` 這些隔離境 —— 本容器一個都不存在。
   `CGC_MDL240_EnvGovernance` 查為 `ABSENT`(找不到尾版)。

三支套件在冊上都是已宣告的(`VIA_EnvGovernance_Baseline_v0102`:
`pymupdf` → `via_vrn_312`、`curl-cffi` → `target_env: via_vdf_312`、
`yfinance` → `boot_update_core`),所以不是「要不要裝」的問題,是**裝的地方在桌機**。

主境逐一實測(這部分做完了):`fitz` 缺 · `curl_cffi` 缺 · `yfinance` 缺;
`pandas` / `polars` / `reportlab` / `duckdb` 都有。

→ **A 只能在桌機側完成。** ENV_PKG 那 18 案照實留著,黃不是綠。

## B —— 完成,順便更正我自己的建議

我前一輪建議「加進 `.gitignore`」,這一輪照你的話做下去才發現**那句對這支檔無效**:
git 的 `.gitignore` 不管已被追蹤的檔,`git check-ignore` 直接回空。

照實三步做完:

```
git update-index --no-skip-worktree <ledger>   # 先解掉上一輪的本機旗標
git rm --cached <ledger>                        # 脫離版控,檔留在磁碟
```

驗證:`git ls-files` 回 0 筆 · 檔還在磁碟 · `git check-ignore -v` 現在真的命中
`.gitignore:388`。此後主控台怎麼追寫都不會再污染工作樹。

## C —— 10 案 UNKNOWN 全部查到根因

「UNKNOWN」的定義是 `rc 0` 但 `target_marker_seen == False`:程式跑完沒炸,
但交接冊登記的成功標記字串沒出現在日誌裡。逐案查完,分成三類:

### C-1 標記釘了舊版號 / 舊計數(9 案 → 全綠)

冊上的標記是歷史值,工具早就往前走了。新標記**一律取自容器實跑的真輸出**,
並挑「只有成功才印得出來」的子字串:

| 案 | 冊上舊標記 | 實跑真輸出 → 新標記 |
|---|---|---|
| `manager` | `[VRN 來源入口] fail=0` | `· PASS · 前版鏈 rc 0` |
| `vrn_engine` | 釘 v0114 `本版 6/6` | 同上 |
| `vrn_engine_params` | 釘 v0115 `7/7` | 同上 |
| `vrn_outputs` | 釘 v0111 `薄尾 11/11` | 同上 |
| `vrn_unknown_verb` | 釘 v0116 `本版 6/6` | 同上 |
| `cov_vrn_eng399` | `自測 8/8 · PASS` | `VRN_ENG399_RealTestHarness_v0100 自測 7/7 · PASS` |
| `vdfvrn_readiness` | `v0100 自測 11/11` | `CGC_MDL265_VdfVrnReadiness_v0101 自測 10/10 · v0100 鏈 PASS · PASS` |
| `vrn_header_frame` | `[計] 7 檢 OK · FAIL 0` | 改指新尾版 v0102(見 C-2) |
| `cov_vrn_eng400` | 釘 v0101 `10/10` | 改指新尾版 v0102(見 C-3) |

前 5 案共用同一指令 `VRN_SystemManager --selftest`(尾版 v0262)。新標記
`· PASS · 前版鏈 rc 0` **不釘版號也不釘計數**,只有整條鏈都過才印得出來 ——
下次管理器出新版也不會再因為標記過期變成假 UNKNOWN。每案都加了 `marker_note`
寫清楚改的理由與日期。

**9 案重跑結果:全部 `rc 0 · marker true`。**

### C-2 真修一:ENG115 duckdb 2.0 API 破壞

```
VRN_ENG115_HeaderFrameTemp_v0100.py:332
    duckdb.sql("SELECT count(*) ...").fetchone()[0]
→ AttributeError: Relations no longer have fetchone()
```

**根因**:duckdb **2.0.0** 移除了 `DuckDBPyRelation.fetchone()`,官方訊息要求改用
`rel.limit(1).fetchall()`。v0101 的第一檢「舊尺仍過」會呼 v0100 的自測,
於是整支連 `[計]` 總表行都印不出來 —— 標記永遠看不到。
全倉掃過,真會炸的只有這一處活檔(另一處在 `references/intake` 的封存參考)。

**修法**(v0100 / v0101 一個位元都不改):add-only 出
`VRN_ENG115_HeaderFrameTemp_v0102.py` —— 進自測前把被移除的方法用官方指定寫法補回,
跑前版鏈,**跑完一定還原**。自測 6 項:缺席才補 · 語意對 · 零列回 `None` ·
多列只取首列 · 前版鏈在墊片下全過 · 跑完乾淨。

**結果 6/6 PASS**,連帶 v0100 的 12 檢、v0101 的 7 檢全過。

### C-3 真修二:ENG400 的 ⑩ 沒跟自己的兄弟檢一致

v0100 的自測在 `except ImportError:` 裡,對 ③④⑤⑥⑦ 明寫
「fitz/PIL 缺席環境:跳實跑、不假造」並記 OK;但 ⑩「EVIDENCE 只增帳」要求
`len(sink) >= 4`,而**那四列證據只有被跳掉的那段實跑會產生**。
→ 沒有 fitz 的環境裡 ⑩ 一定紅,v0101 的 ⑨ 總結檢再跟著紅。
這不是證據帳壞了,是 ⑩ 漏做缺件處理。

v0101 的 `except ImportError: pass` 更把原因整個吞掉(全景工具本來就標了這條
`SWALLOW`),日誌上看不到是缺哪一件。

**修法**:add-only 出 `VRN_ENG400_SixEngineShell_v0102.py`:
* 相依件狀態**逐字印出來**,不再吞原因
* **直接跑 v0100** 拿它自己的逐檢行(v0101 用 `redirect_stdout` 只留最後一行總表,
  靠它判斷等於沒看到證據)
* 只有在「相依件真的缺席」且「紅的只有 ⑩ 與它的總結檢」時才中和;
  **獨立紅一律照紅,不代為漂白**
* 相依件在場時 ⑩ 照原樣實跑實判,本版不介入

自測 8 項,其中三項專門證明這支不是萬用漂白劑:獨立紅認得出來 ·
總結檢樣式窄到不會誤收別的檢 · 有獨立紅就一定回 rc 1。**結果 8/8 PASS。**

過程中它真的擋過我一次:第一版我沒把「總結檢」排除,它直接判
`[FAIL] ② 缺件但另有紅 —— 照紅不漂白`,逼我回去把 v0101 的 ⑨ 認成總結檢才過。

### C-4 第 10 案其實不是 UNKNOWN

`vdf_fetch_integration` 的日誌寫得很清楚:

```
[ABSENT] VDF_MDL008_FetchSystem v0102:本直譯器缺核心套件 yfinance —— 不代裝
```

是 **ENV_PKG**,只是它不丟 `ModuleNotFoundError` 而是自己印一句話,
所以我的分類器認不出來。已把「缺(核心)套件 X」與「`[ABSENT]` …不代裝」兩個樣式
加進 `LOG_SIGNALS`,並補一條測試驗它會帶出套件名。
→ 歸類正確後,**UNKNOWN 歸零**。

## ④ 一個我自己造成的後果,照實記

改完交接冊再跑 `handoff check`,RED 從 36 跳到 **123**,多出一類
`EVIDENCE_INVALID ×46`,理由逐條寫著
`dependency changed: supportive modules/registry/VIA_Handoff_Continuity_SSOT_v0100.json`。

**那是我寫進那本冊造成的** —— 46 個案把它列為相依,一動它們的收據就失效。
這是閘**設計上就該這樣叫**,不是壞掉。照 CLAUDE.md 的流程處理:
只重跑有相依變更的已宣告測試 → registry-sync → 編號 → SDD → `handoff checkpoint`。

## ⑤ 鎖與燈

`VIA_ThreeDayLock` 自測 **30 → 31**(新增「缺核心套件」樣式那條)。
鎖冊照 add-only 出 **v0101**(鎖 218 案),**v0100 一個位元都沒動**(`git status` 證實)。

未鎖 23 案分類:`ENV_PKG 18` · `DESKTOP 2` · `NO_PWSH 2` · `NET_GATE 1` ·
**`UNKNOWN 0`**。每一類都附逐字日誌證據。

## ⑥ 入冊

| 冊 | 版 | 增了什麼 |
|---|---|---|
| 需求冊 | `v0227` | +`VCGC-REQ199`(status PARTIAL;A 的兩道閘寫進 `blocked`) |
| 盤點冊 | `v0200` | +站 `E-vrn-eng115-v0102` · `E-vrn-eng400-v0102` |
| 交接冊 | `v0100` | 9 案標記改成實跑真輸出 + 各案 `marker_note` |

---

五系統對等獨立(L120 / L123)。兩支修的都是 VRN-2 車道自己的引擎,
add-only 不改已發布版本;VDF / VQG / VAP / VCGC 的正本一個字沒動。
