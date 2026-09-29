# 側線 2026-09-29 c:Polars 表格層 · 記憶體不足轉 temp(11 支必要引擎)

主線批號由併線的手指定(L25)。本批接在 PR #368(4ae4f2bd)之後。

## 一、操作員令(原文)

- 「go on add polars to all necessary engines 記憶體不足可用temp替代用」

## 二、先量再寫(容器實量)

| 量到的 | 數字 | 所以 |
|---|---|---|
| 全樹尾版 import pandas / polars | 327 支 | 大多讀小表、只計數、逐日抓取 —— 不是「必要」 |
| 真的把全市場大表(日價 · 還原價 · 因子 · 法人)撈進 Python 表格 | **4 支**(N1) | 必要 |
| 在 DuckDB 裡對全歷史重算 / 整表複製 | **7 支**(N2) | 必要 |
| 本境套件 | polars **不在**(依規不代裝,L19);pandas 3.0.6 · duckdb 1.5.5 · pyarrow 25.0.1 · psutil 7.2.2 | Polars 路徑只能驗「缺席時誠實退回」 |
| DuckDB 預設上限 | 總記憶體 80%(10.6 GiB),**不看當下可用** | 別的程式吃掉一半時它仍以為有 80%,先把機器擠到換頁 |
| DuckDB 預設溢寫夾 | 檔案庫 = 庫檔旁 `.tmp`(輸出夾裡);記憶體庫 = **工作夾** `.tmp`(常是倉根) | 溢寫位置不受管 |
| ENG070 面板載入 | 58.8 萬列 · 面板 94 MB · 載入峰值 RSS +343 MB | 工作站 190 萬列以上會放大 |
| 把 `.df()` 改走 temp parquet 再讀回 | 峰值 **761 MB 對 642 MB**(反而高);沒 ORDER BY 時列序會變 | pandas 端**不走**這條 |
| 記憶體庫(`:memory:`)表資料 | 不能溢寫;上限收小直接 Out of Memory | 記憶體庫只換溢寫夾、不收上限 |
| 視窗函數 | 300 萬列 64 MiB → Out of Memory、128 MiB 過;1000 萬列 256 MiB 過 | 預算下限 **512 MiB**(兩倍餘裕) |

## 三、共用件:`SUP_MDL755_VIAPolarsFrame_v0100`(VIA-TOOL-0195;經 VCGC 啟用,鎖冊 `frame`)

| 函式 | 做什麼 |
|---|---|
| `polars()` | polars 探針,經 VIA_Toolkit(TOOL-040)取件;缺 = None + 因由 + 裝令(`via-install polars`,或 `pip install "polars>=1.21,<2"`,與 QuantGuard 同一根釘;裝 = 操作員的手)。`VIA_FRAME_BACKEND=pandas` 強制退回 |
| `budget()` | 記憶體預算 = **當下可用 × 0.5**(`VIA_FRAME_MEM_FRACTION`,夾在 0.05–0.9;下限 512 MiB;量不到 = None,不猜) |
| `spill_dir()` / `sweep()` | 受管 temp:`VIA_TEMP_ROOT`(SUP_MDL738 既有名)或系統 temp 下的 `VIA_spill/`;用完即刪。`sweep` 只清本件命名、有標記或空、夠舊、行程已不在的殘留夾;別人的不碰 |
| `install_duckdb_guard()` | 本行程之後開的每條 DuckDB 連線:溢寫夾 → 受管 temp;**檔案庫上限收到預算**(比現值小才收);記憶體庫只換夾;呼叫端 config 自己給了的照它;有 polars 的境 Polars 串流也寫同一夾(`POLARS_TEMP_DIR`)。閥:`VIA_FRAME_GUARD=off` |
| `frame()` | DuckDB 查詢 → 表格。`want="pandas"` 與 `.df()` 一字不差;`"polars"` / `"auto"`:估算 ≤ 預算走 `.pl()`,超過 → COPY 到 temp parquet、回 LazyFrame(`scan_parquet`,`collect()` 走串流引擎) |
| `estimate()` / `plan()` | 估算 = 列數 × 定長寬度 + 變長欄(字串 · 二進位 · 巢狀)內文**實量**:同一趟查詢算列數與內文位元組(`strlen` 是 UTF-8 位元組;巢狀以文字長度近似)。`plan()` 判 ≤ 預算走記憶體、超過走 temp、預算量不到不收(Codex #369 P2:原本字串一律算 32 位元組,百萬筆 1 KiB 字串會估成 32 MiB) |
| `coverage()` | 必要引擎名冊 `NECESSARY` 逐支看尾版有沒有**正典橋塊**(逐字)與守門 |

動詞(經 VCGC):`via-vcgc run --family core SUP_MDL755_VIAPolarsFrame status | probe | sweep [--apply] | coverage`。
`probe` 在沒有 polars 的境回 rc 3(ABSENT = 本境能力缺,不是壞)。

## 四、11 支必要引擎(新版薄尾;前一版一字不動)

| 類 | 引擎 | 前 → 新 | 量到的理由 |
|---|---|---|---|
| N1 | VDF_ENG070 族群分類×價格指數 | v0112 → v0113 | 全市場面板撈進 pandas(58.8 萬列 · 峰值 +343 MB) |
| N1 | VDF_ENG072 故事輪動橋 | v0103 → v0104 | 價 · 法人 · 融資券整表撈進 pandas |
| N1 | GRP_ENG041 輪動方法論實測室 | v0102 → v0103 | 價 · 成交 · 法人面板撈進 pandas(滾動 17 處) |
| N1 | GRP_ENG040 族群輪動實庫轉接 | v0103 → v0104 | 台股 / 全球價面板撈進 pandas |
| N2 | VDF_ENG060 調整後價格層 | v0107 → v0108 | 全歷史還原價層 CREATE OR REPLACE TABLE … AS |
| N2 | VDF_ENG061 因子庫 | v0105 → v0106 | 全歷史因子(視窗函數 27 處) |
| N2 | VDF_ENG062 族群聚合因子層 | v0104 → v0105 | 族群因子層 CTAS |
| N2 | VDF_ENG064 歷史回補 | v0112 → v0113 | 回補批次對全價表 anti-join 落庫 |
| N2 | VDF_ENG079 本機三庫整併 | v0103 → v0104 | 本機庫合併(CTAS 42 處) |
| N2 | VDF_ENG081 台股日交易×籌碼對齊 | v0102 → v0103 | 全市場對齊 CTAS + INSERT … SELECT |
| N2 | VDF_ENG085 VATETF 應用端正主橋 | v0105 → v0106 | 全價表複製成 VATETF 暫存庫(CTAS 16 處) |

每支薄尾一樣的形狀:前一版的 ACCEL / NET 橋塊逐字照抄 + **正典 FRAME 橋**(`[VIA:FRAME-BRIDGE:v0100]`,鎖冊 `frame` 優先,缺則尾版)·
`main()` = 先裝守門再交前一版 `main()`(CLI 一字不動)· 自測 ①橋 ②守門 ③零足跡,再串前一版全部檢。

兩個讀者都要讀得懂薄尾(提交後補修,見第七節):
- **說明首行 = 引擎名 +(括號裡的薄尾註記)**。總控頁的候核名稱取說明首行、剝掉括號;沒有正式名的 4 支(ENG070 · 072 · 079 · 081)顯示與前一版一字不差。
- **家族名寫 `_STEM`**。VCGC v0172(main 的 R33)沿薄尾鏈盤點元件,認的是 `_STEM = "<家族>"`;這樣前一版的函式留在元件冊上(source 記定義它的那一版),不被當成退役。

**子行程也要有守門(Codex #369 P1)**。守門換掉的是本行程的 `duckdb.connect`,子行程是新的直譯器,碰不到。普查 11 支的前版鏈:
- **ENG085**:v0105 的 `_INSPECT`(全表 count / max)與 `_PREPARE`(整表 CTAS)經 `subprocess` 在家族境跑 —— 整表複製正好在子行程裡。
  v0106 加 `guard_children()`:把守門段接在這兩段腳本開頭(冪等),子行程載同一支 FRAME 正典、自己量預算、自己開受管 temp、跑完自己刪;閥 `VIA_FRAME_GUARD=off` 經 `child_env` 傳下去,子行程也聽。
  adapter 不接:它是收容件原樣,讀 `_PREPARE` 已縮好的暫存庫、整表讀成 Python 紀錄,DuckDB 上限管不到那一段。
- ENG079 的子行程是 `ENG064 --rebuild-ckpt`,glob 取到的就是本批 ENG064 v0113 薄尾,它自己的 `main()` 會裝守門。
- ENG072 · GRP_ENG040 的子行程跑外部收容包,只用 pandas 讀父行程匯出的檔,不碰 DuckDB;DuckDB 撈表在父行程,已守。ENG081 的 subprocess 只讀持鎖行程的命令列。

不列入(量過):單碼查詢(VAP_ENG015 · CGC_MDL118)、小表(共識 · 當沖)、逐日抓取器(ENG054 / 056 / 057)、只計數的閘、ENG059 薄尾。

## 五、Polars 在哪裡、不在哪裡(照實說)

- **在**:共用件的表格層 Polars 優先(`.pl()` 零拷貝;超過預算 → temp parquet → LazyFrame 串流);守門讓 Polars 串流也溢寫進同一個受管夾。
- **本境驗不到 Polars 本身**:沒有 polars,依規不代裝。容器驗到的是「缺席時誠實退回 pandas(零差異)」與「要 polars 沒有就拋 FrameAbsent 附裝令」;
  一致性檢 ⑫(`.pl()` 與 temp LazyFrame 兩路逐列 = DuckDB 原值)在有 polars 的境**自動跑**。
- **不在**:11 支引擎的 pandas 計算沒有改寫成 Polars —— 量到 pandas 端改走 temp 反而更耗記憶體,而且它們的重活本來就在 DuckDB;
  統計邏輯改寫在本境做不出零差異證明,**不做驗不了的改寫**。
- 工作站啟用 Polars(操作員的手):`& <vdf python> -m pip install "polars>=1.21,<2"` → `via-vcgc run --family core SUP_MDL755_VIAPolarsFrame probe` 回 rc 0 →
  `--selftest` 的 ⑫ 由 ABSENT 變 OK。

## 六、驗證

| 項 | 結果 |
|---|---|
| SUP_MDL755 自測 | 13/13 PASS · ⑫ ABSENT(本境無 polars);突變 20/20 全抓(兩個原本存活的恆真檢已改寫死期望值)。Codex #369 P2 修正後:⑪ 期望值全寫死('é'×512 = 1 KiB × 2000 列 · BLOB · BIGINT[] · 全 NULL · 重名 / 怪名欄 · `plan()` 邊界),新突變 11/11 全抓(含「字元數冒充位元組」「不照位置改名」);舊突變重跑 19/19(M15 的錨點 `VARCHAR_WIDTH` 已拿掉,由 P2-F 接手) |
| ENG085 v0106 子行程守門(Codex #369 P1) | 薄尾自測 4/4 + 前一版 12/12(前一版的 `_PREPARE` / `_INSPECT` 就在接了守門的子行程裡跑);③ 實測:子行程另開 pid、溢寫夾在受管 temp、上限收到子行程自己的預算、只接一次、閥 off 子行程也不裝;突變 6/6 全抓 |
| 真庫 · ENG085 `run` | rc 0 · OK · 1,163 筆;跑的時候盯著受管夾:父行程 1 個 + 子行程 2 個(`_INSPECT` · `_PREPARE`),跑完全清,stderr 空 |
| 11 支薄尾自測 | rc 與前一版**完全一致**(10 支 0 · ENG072 2 = 上游籌碼表缺 NODATA);薄尾 3/3;前一版檢數一個不少;自測前後倉內零改動。說明首行與 `_STEM` 補修後 12 支(含 MDL233)重跑:rc 與檢數不變,倉內零改動 |
| 真庫副本 · ENG061 原規模 | 58.8 萬列,上限 128 MiB → 溢寫 8 種進受管 temp · 結果全欄雜湊**位元級一致** |
| 真庫副本 · ENG061 放大 8 倍 | 470 萬列 · 7,208 檔:不設限峰值 RSS **1,138 MiB** / 9.0 s;上限 256 MiB → **583 MiB(−49%)** / 7.5 s,溢寫進受管 temp、跑完清空 |
| 同上 · 逐欄比 | 11 欄裡 9 欄位元級一致;`vol_20d_ann`、`volu_z20`(`stddev_samp` 視窗)最後幾位不同:最大絕對 1.8e-15、最大相對 8.4e-15;空值型態完全一致。不設限重跑兩次雜湊相同 → 差異來自溢寫改了 DuckDB 的合併順序,**只在記憶體真的不足時出現** |
| 真庫 · ENG070 面板 | 上限 128 MiB:結果雜湊與欄型別一字不差;64 MiB(低於下限、只為測試)Out of Memory → 下限 512 MiB 的由來 |
| CGC_MDL233 v0103 自測 | 20/20(六家同一把尺;frame 冊上那一支過全部檢查;家別不對擋下;已經 VCGC 啟用、鎖冊位元吻合) |
| 擊斃閘 v0103 `--base origin/main --run-selftest` | 通過 rc 0 · 判 17 檔 · 擊斃 0 · 記債 13(12 支薄尾委派前一版自測 + 格子沿襲既有 ⑥ 撞號)。第一跑抓到 SUP_MDL755 ⑩ 兩個分支各一條 chk(KILL-09 新增撞號),合成一條後重跑通過。補修後、Codex 修正後各再跑一次:判 31 檔(本批已在 HEAD,判的是那一步)· 通過 rc 0 · 記債 1(格子 ⑥) |
| 格子 v0501 `--only`(受影響 13 站) | OK 13 · FAIL 0;正式庫這 13 站前後三本位元組與 mtime 一致。補修後、Codex 修正後各重跑一次,同樣 13/13,工作樹前後一致 |
| 合併 main(PR #367 · 55fcb1ef) | 合併提交 e61b245b 逐檔核對:與 main 不同的 18 檔全等於本批原檔,其餘全等於 main(衝突兩本 —— 元件冊、總控頁 —— 取 main 後重生) |
| VCGC `registry-sync --apply`(併 main 後,VCGC v0172 沿薄尾鏈盤點) | 對 main:新 102(共用件 56 · 11 支薄尾各 4 · ENG085 另 +2)· 遺失 0 · 改號 0 · **退役 0**;變更 = 尾版自己重定義的函式把 source 移到新版檔(格子 v0501 42 · 薄尾與 MDL233 各 5–6)。補修前是退役 231(見第七節);Codex 修正加的 4 個函式(`_varlen` · `plan` · `child_preamble` · `guard_children`)已入冊 |
| 編號冊(只增合併) | 10 本 +210 列(CLS_SUP 3 · ENG 11 · ENV 4 · FNC_GRPIDX 14 · FNC_SUP 52 · FNC_VCGC 46 · FNC_VDF 74 · LGC 2 · MDL 3 · TOOL 1);對 main 逐鍵比:遺失 0 · 改號 0 · 既有列欄位 0 變;TST 列不加(那是本機格子存證衍生);SSOT 46 本 n/sha 一致;CGC_MDL237 自測 rc 0。Codex 修正後**以 origin/main 為底**重算:本 PR 的列全換成最終行號,FNC 代碼照最終定義順序(這些代碼都還沒進 main) |
| VCGC `val`(驗證 SSOT) | GREEN · 八道規則全綠 · 交叉代碼 22(補修後重跑同) |
| VCGC `sdd check` | YELLOW:X-NUM · X-REG · X-LOCK 等全綠;只剩 X-REQ-OPEN 黃(既有 13 條需求未落地) |
| 總控頁再生 · 契約測試(py3.12) | 再生前暫移容器本機的 StdDashboard(gitignore);對 main 只差時間戳與 MDL233 一列(五件 → 六件);契約 19/19 OK |
| `tools activate frame --apply`(經 VCGC) | 鎖冊 `frame` = v0100 · sha256 382c5e80… · 50,012 位元組(Codex #369 P2 修正後重新啟用;鎖冊位元與檔一致,CGC_MDL233 ㉑ OK) |

## 七、教訓(照實記)

- **「加 Polars」先量**:這一倉的重活在 DuckDB;pandas 端改走 temp 反而更耗記憶體。不量就會做出一個看起來很對的退步。
- **上限收小不是免費的**:視窗函數與記憶體庫不能全溢寫 → 下限 512 MiB、記憶體庫不收上限。
- **溢寫改了浮點合併順序**:`stddev_samp` 類視窗在最後幾位會不同 —— 寫進說明,不假裝位元級不變。
- **自測拿常數比常數是恆真**:突變 M15(字串寬度)、M20(溢寫根不聽 VIA_TEMP_ROOT)原本存活;期望值要寫死、環境變數要驗真的被聽。
- **VCGC 失敗會記進教訓冊**:`sdd check` 回紅被記成 VF-028(VF-016 第 5 次),照規矩還原。那次的紅是 X-NUM:上一批 VCGC v0171 由 main 的 R33c 補編號,本批的新檔由下面的只增合併補上。
- **編號冊在容器只做只增合併**:容器實跑 `CGC_MDL237 --apply` 會新增 1,100 列,其中 862 列是**容器本機庫**的台股代號(VDF_ENG087 讀本機名冊,容器庫只有 907 檔);updated_at 取 git 最後提交時間,淺層 clone 會讓整冊翻動(+36,299 / −11,854 行);TST 列來自本機格子存證。所以只把新鍵補進 main 的冊,既有列一字不動。
- **VCGC 座位自動上傳會把進行中的合併一起推上去**:CGC_MDL223 `publish()` 只 `git add` 座位檔,卻用不帶路徑的 `git commit`,暫存區裡的東西會整包提交再 `git push`。本批合併 main 時,VCGC 以「vcgc: sync the subsystem seat」的名義把合併提交並推送了(e61b245b)。內容逐檔核對無誤(第六節)。以後合併中或暫存區有東西時,先設 `VIA_VCGC_PUSH=NO` 再跑 VCGC。
- **薄尾要讓兩個讀者都看懂**:① 總控頁取說明首行當候核名稱。本批原本 11 支首行都是「薄尾:Polars…」,ENG079 · ENG081 的真名因此被換成同一句,ENG070 · 072 也從「正式名稱待治理」變成那一句。② VCGC v0172 的薄尾偵測只認 `_STEM = "<家族>"`,本批 12 支原本寫 `STEM`,被當成實體,前一版 231 個函式被標退役。首行改成引擎名、家族名改成 `_STEM` 之後,總控頁名稱與前一版相同,退役 0。
- **容器本機產物會滲進總控頁**:容器裡的格子跑過 StdDashboard(gitignore),總控頁的 Plotly 段就變成「頁面已產生」,時間是容器的。再生前先暫移,入倉的頁不帶容器狀態。
- **守門只蓋得到本行程**(Codex #369 P1):換掉 `duckdb.connect` 管不到 `subprocess` 開的新直譯器。ENG085 的整表複製就在子行程,原本那支薄尾等於沒守到重活。薄尾上線前要沿前版鏈查一遍 subprocess,子行程跑的是誰、碰不碰 DuckDB。
- **估算用的寬度常數會說謊**(Codex #369 P2):字串一律算 32 位元組,長字串就少估幾個數量級,「超過預算走 temp」的判斷跟著失效。變長欄要實量;測資也要用多位元組字元,才抓得到「字元數冒充位元組」。

## 八、待辦(本批做不到或不在範圍,照實交出)

| 項 | 為什麼本批不做 | 下一步 |
|---|---|---|
| Polars 一致性 ⑫ | 容器沒有 polars,依規不代裝 | 工作站:`& <vdf python> -m pip install "polars>=1.21,<2"` → `via-vcgc run --family core SUP_MDL755_VIAPolarsFrame probe`(rc 0)→ `--selftest` ⑫ 應為 OK |
| 編號冊既有列刷新(updated_at · 使用者 · 燈號 · TST 列) | 容器只補新鍵(X-NUM 已綠);這些欄位該由正本環境給 | 工作站(選做):`via-vcgc run --family core CGC_MDL237_NumberingSystem --apply` 然後 `via-vcgc sdd check` |
| CGC_MDL223 座位上傳只提交座位檔 | VCGC 治理件,不在本批範圍 | 新版:`git commit -m … -- <座位檔>`;有 MERGE_HEAD 或暫存區有別的檔就不提交,回 `held` |
| VCGC v0172 薄尾偵測也要認 `STEM = "<家族>"` | main 既有缺口:用 `STEM` 的家族尾版另有 24 支(VDF_ENG082 v0106 · VRN_ENG049 / 050 / 052 / 055 / 056 / 057 / 062 · CGC_MDL058 / 089 / 107 / 137 / 142 / 156 / 226 / 231 / 234 / 236 / 237 / 242 · SUP_MDL030 / 737 / 740 · celeritas launcher),main 元件冊裡它們前一版約 230 個函式標退役 | VCGC 新版把 `_STEM` 條件放寬成 `_?STEM`,補正控與負控,再 `registry-sync --apply` |

## 九、還原

- 刪本批新檔,即回到尾版律的前一版:SUP_MDL755 v0100 · 11 支薄尾 · CGC_MDL233 v0103 · 格子 v0501。
- 鎖冊 `frame` 一項、引擎版號冊 VIA-TOOL-0195 一列:`git restore --source=4ae4f2bd` 對應冊(PR #367 沒動這兩本)。
- 編號冊 10 本 + `VIA_Numbering_SSOT_v0100.json`、元件冊、總控頁:`git restore --source=55fcb1ef` 對應檔(= 本批之前的 main)。
- 工作站臨時關守門、不改碼:`$env:VIA_FRAME_GUARD = "off"`;預算要鬆:`$env:VIA_FRAME_MEM_FRACTION = "0.8"`。
