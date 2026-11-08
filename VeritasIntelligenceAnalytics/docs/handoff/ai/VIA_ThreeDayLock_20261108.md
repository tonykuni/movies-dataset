# 三日進度:實測成功鎖住 · 未完成照實分類 · HTML U/I(操作員 2026-11-08 令)

操作員令:「依照你的建議 · 讀取進三日進度 · 實際測成成功部分記錄鎖住 ·
未完成者持續做到完成 · 自動完成並跳出 HTML U/I」。

交付:`docs/handoff/ai/VIA_ThreeDayLock_v0100.py`(引擎,自測 30/30)·
`VIA_ThreeDayLock_v0100.json`(鎖冊)· `VIA_ThreeDayLock_UI.html`(U/I)。

## ⓿ 先辦你批准的那件事:帳本不再污染工作樹

`VIA_Lessons_Ledger_v0100.json` 每跑一次 `token` 就被主控台追寫,每輪都要我手動還原。

**我原本的建議「加進 .gitignore」對這支檔其實無效** —— git 的規則是
`.gitignore` 不管已被追蹤的檔。照實說、照實改:

* `.gitignore` 還是加了一行(新 clone / 新副本不會被加進來)
* 真正讓它停止污染的是 `git update-index --skip-worktree`,**本機、可逆、不刪倉內檔**
* 要讓它真的脫離版控得 `git rm --cached` —— 那會把它從 main 移除,**那是你的檔案政策,我不自己動**

驗證:`git ls-files -v` 顯示 `S`(skip-worktree)· `git status` 乾淨。

## ① 三日視窗(2026-11-06 → HEAD)

| 日 | 提交 |
|---|---|
| 11-06 | 76 |
| 11-07 | 24 |
| 11-08 | 14 |
| 合計 | **114** |

改檔次 **1,442**(提交 × 檔的累計):

| 系統 / 區 | 檔次 |
|---|---|
| docs | 1,195 |
| VCGC(registry / supportive) | 209 |
| VRN-2 | 22 |
| VAP | 11 |
| VQG | 4 |
| 其他 | 1 |
| **VDF** | **0** |

VDF 三日 0 檔 —— 照實是 0,不補、不美化。它的待辦全卡在桌機側(日資料擷取要桌機跑)。

視窗起點刻意取自 **git 最新提交日 − 2 天**,不用機器當下時間,否則同一份收據隔天重跑就對不上。

## ② 鎖住什麼:209 案(門檻一字不放寬)

鎖的四條門檻全要:

```
收據 schema == VIA.Handoff.TestReceipt.v1
rc == 0
target_marker_seen == True
有 completed_at 且有 log_sha256
```

**鎖住的是 (case, log_sha256) 這一對。** 下一輪同案 log_sha256 變了 = `REGRESSED`;
案不見了 = `GONE`。兩者任一出現總燈 RED。不靠記憶、不靠對話,只靠收據指紋。

本輪:`LOCKED_OK 209 · REGRESSED 0 · GONE 0 · 新綠 0` → 總燈 **GREEN**。

鎖冊 add-only:
* 實質(鎖了哪些 case × log_sha256)沒變就**不出新版號**(時間戳不算實質,免得每跑一次就長一版)
* 目標版號已存在 → **rc 1 拒寫**,已發布檔一字不動
* 撤鎖要寫 `revoked_at`,寫了之後不再判 GONE

## ③ 還沒鎖住的 32 案 —— 分類方式本輪改過

**第一版我的分類器是看案名猜的,那是錯的做法,而且真的猜錯了。**
它把 `nlp_*` 與 `*coverage*` / `*probe*` 一律歸成「MINE 本車道可做」,
實際讀日誌後根本不是那樣。已改成**只認日誌裡真的出現過的字**,認不出來寫
`UNKNOWN` 留白,並且每一類都附逐字證據那一行。自測裡特意放了一案
`nlp_fetch_coverage_probe`(案名同時像三類),驗它仍照日誌判。

| 類別 | 案 | 意思 | 逐字證據(樣本) |
|---|---|---|---|
| `ENV_PKG` | 17 | 容器缺套件 | `ModuleNotFoundError: No module named 'fitz'` / `'curl_cffi'` / `'yfinance'` |
| `UNKNOWN` | 10 | rc 0 但標記沒印 → 判不出來,不硬歸類 | `標記沒印` |
| `DESKTOP` | 2 | 要桌機 | — |
| `NO_PWSH` | 2 | 容器沒有 pwsh,PS 側交叉讀法做不到 | `[FAIL] ㉖ 真樹:… PS 尾版 …` |
| `NET_GATE` | 1 | 要觸網同意閘 | — |

### ENV_PKG 的根因已查到底

`nlp_praddle` / `nlp_optional` 兩案我重跑過一次(`handoff test`),仍 rc 1。
讀完整日誌,兩案根因**同一個**:

```
VRN_ENG398_PraddleExtractor_v0100.py:320  import fitz
ModuleNotFoundError: No module named 'fitz'
```

主境逐一實測確認:**`fitz`(PyMuPDF)· `curl_cffi` · `yfinance` 真的缺**;
`pandas` / `polars` / `reportlab` / `duckdb` 都有(所以提到這幾支的案是跑在隔離 via_ 境裡)。

**沒裝。** 照政策不 pip,唯一路徑是
`via-envgov tools --apply --approve` —— `--approve` 是操作員的手,我不代按。
`CGC_MDL240_EnvGovernance` 查為 `ABSENT`(找不到尾版),環境計畫頁自己也寫
「最佳點 NODATA 沒有過關紀錄,不新建假的」。所以這 17 案照實留 ENV_PKG,不寫成成功。

### UNKNOWN 10 案是什麼

`rc 0` 但 `target_marker_seen == False` —— 程式跑完沒炸,但交接冊登記的
`success_marker` 字串沒在日誌裡出現。可能是工具改了輸出字樣、也可能是案登錯,
**兩種都不能當成功**。要逐案比對冊上的 marker 與工具實際印的字,橫跨 VRN / VDF / VCGC 三個車道,
不是這一輪能一次清完的;照實留 UNKNOWN。

## ④ 交接閘現況(只讀自報)

`handoff check` = **RED**,36 項,全是既有積欠,本輪沒有新增:
`CHANGED_CODE_WITHOUT_TEST` ×28 · `ACCEL_BRIDGE_MISSING` ×4 · `MODULE_UNREGISTERED` ×4。
註冊冊待同步 `new 228 · changed 162 · stale 0`。
背景全景監控:落後 417 提交 · 未登 2,381 支。

`token` 卡 **6/6 已啟用**(全景 v0117 · NLP v0108),本輪全程照 L65 次序用:
`token` → `read` 骨架卡 → `read --depth 2` 讀冊 → `slice`。整檔一次都沒讀進對話。

編號稽核:**遺失 0 · 改身分 0 · 重號 0**(冊內不一致 1 為既有黃)。

## ⑤ 入冊(只增不減)

| 冊 | 版 | 增了什麼 |
|---|---|---|
| 需求冊 | `VIA_Requirements_SSOT_v0226.json` | +`VCGC-REQ198`(status COVERED) |
| 工作流冊 | `VIA_Workflow_VCGC_SSOT_v0131.json` | +`VCGC-WKF025` `threeday_lock`(6 步 · 7 條驗收) |
| 盤點冊 | `VIA_VCGC_FunctionInventory_SSOT_v0199.json` | +站 `C-threedaylock-v0100` · coverage.case / workflow |
| 交接冊 | `VIA_Handoff_Continuity_SSOT_v0100.json` | +案 `C-threedaylock-v0100`(含 `timeout_seconds`)· +工作項 `WI-THREEDAYLOCK-001` VERIFIED |

交接收據 `docs/handoff/evidence/C-threedaylock-v0100.json`:
`rc 0 · target_marker_seen true · log_sha256 636fdd5b…`。

## ⑥ 本輪我自己出的兩個錯,照實記

1. **分類器看案名猜**(見 ③)→ 改成只認日誌真訊號 + 加了 6 條迴歸測試。
2. **我用錯的 sed 錨點把自己的引擎檔截斷了**:正則 `# ⑰ 車道判定` 先命中了模組層
   的註解 `# 車道判定(路徑 → 系統)`,整段 43–638 行被覆蓋,檔只剩 90 行。
   那支檔還沒進版控,所以 git 救不回來 —— 我照設計整支重寫,自測從 21 項補到 30 項。
   教訓:**對沒進版控的新檔做範圍替換前先提交一次**,否則沒有還原點。

## ⑦ 下一手(要你一句話的)

| # | 事 | 誰的手 |
|---|---|---|
| A | 裝 `fitz`(PyMuPDF)/ `curl_cffi` / `yfinance` → 清 ENV_PKG 17 案 | 操作員 `via-envgov tools --apply --approve` |
| B | `VIA_Lessons_Ledger` 要不要真的脫離版控(`git rm --cached`) | 操作員檔案政策 |
| C | UNKNOWN 10 案逐案比對 marker 字樣(跨 VRN / VDF / VCGC 三車道) | 可排下一輪 |
| D | `CHANGED_CODE_WITHOUT_TEST` 28 支逐支宣告測試 | 要分車道排 |

---

五系統對等獨立(L120 / L123):本輪只讀各系統自報的收據與 git 紀錄,
不改他系統正本 / 冊 / 號 / 檔。鎖冊與 U/I 都是本工具自己的檔。
