# 批618:L50 升第一條 · 衝突哨兵的 PATH 終於出得了手

操作員令(原話):

> `衝突哨兵 PATH 跟 L50 不准使用TA-LIB刪除關於他的一切列入第一條用QUANTGUARD替代`

兩件事,一件是**裁定**(L50 的位階),一件是**缺陷**(哨兵抓到卻不出手)。

---

## 一 · L50 升第一條,以及「刪除關於他的一切」到底怎麼執行

### 位階怎麼記

`VIA_Policy_Laws_SSOT` 的 `laws[0]` 換成 L50,記 `rank: 1` 與 `ranked_by`(操作員原話),
條文開頭補一段「【第一條】TA-Lib 禁用,QuantGuard 是唯一正主」,底下標明
「—— 以下為原條文(批534 立,一字不改)——」。

**id 一律不重編。**順序表達位階,id 表達身分;重編會讓 512 批的所有引用一起斷掉。
這件事寫進新增的 `law_order_note`,免得下一批有人「順手整理」。

### 「刪除關於他的一切」

量過:全樹 **623 支檔**提到 talib。但其中絕大多數碰不得——

| 區 | 為什麼碰不得 |
|---|---|
| `references/intake/` | 收件正本,帶 sha 清單(正本零觸碰律) |
| `*_sha*.py` 鏡像 | 同上,雜湊即存證 |
| `RetiredEngines` / `_superseded` / `SCOPE_COPY` | 退役與版本史,只增不減 |
| `accelerator/VeritasCeleritas.py`、`50_Protection_Acceleration/VeritasCeleritas.py` | 批345 不可動律,兩支工具本體的裁定權在操作員 |

所以在這棵樹裡,「刪除關於他的一切」可執行的形式**不是 `rm`,是斷其活路**:
讓 talib 在執行期**永遠不會被載入**。

實測 `SUP_MDL737` 的 `CEL_CANDIDATES` 解析序:

| 順位(v0104) | 檔 | talib 惰性路徑 |
|---|---|---|
| 1 | `VeritasCeleritas.py` | **1** |
| 2 | `50_Protection_Acceleration/VeritasCeleritas.py` | **1** |
| 3 | `accelerator/VeritasCeleritas.py` | **0**(合規本) |

零 talib 的那一本排在**最後**,而本境 `find_spec('talib')` 找得到——執行期會真的載入。
`SUP_MDL737 v0105` 把合規本提到第一,兩支工具本體一個字沒動。

    CGC_MDL156_VIAAcceleratorControl  RED 36/37  →  GREEN 37/37 · accelerators=25

---

## 二 · 衝突哨兵:冊上寫了 action,工具只做了一半

`VIA_BadEnv_Blacklist` 的 `env_hazards` 裡,HZ-02 的 `action` 欄白紙黑字寫著:

> 紅燈+**PATH 換錨指令**

哨兵 v0100 把紅燈做得很好(前綴比對精準、報告落地),**換錨指令從第一版起就沒出現過**。
它能躲這麼久,是因為冊是給人看的、工具是給機器跑的,中間沒有任何一道檢查把兩邊對起來。
操作員每跑一次看到同一盞紅燈,每次都得自己想下一步——**捕捉到卻不出手等於沒捕捉**。

這一條升為 **L92 修法句律**。

### 為什麼不能一律「剝掉」

工作站那兩條命中長這樣:

```
C:\Users\tonyk\OneDrive\Desktop\VRN\poppler\poppler-24.08.0\Library\bin
C:\Users\tonyk\Downloads\movies-dataset\VeritasIntelligenceAnalytics\bin
```

第一條是**工具寄生在黑根**。量過:`pdf2image` 靠 PATH 找 `pdftoppm`,
`VRN_ENG058_TableOmni v0105` 與 `SUP_MDL747_OcrLaneRunner v0102` 都點名 poppler,
沒有任何現役件寫死它的絕對路徑。**剝掉 = VRN 的 PDF 取表道當場斷線。**

第二條是**舊 VIA 克隆的 bin**,黑名單要殺的正是它。

所以 v0101 分四類生成修法句:

| 類 | 判準 | 處方 |
|---|---|---|
| 舊 VIA 克隆 | 路徑含 `VeritasIntelligenceAnalytics` / `movies-dataset` | **剝離**(搬家等於讓封存根復活) |
| 帶工具嫌疑 | 命中冊上 `path_tool_anchors` 的 `dir_anchors` | **搬家**:複製出黑根 → 換錨 → 才剝舊錨;驗收句用 `exe_anchors` |
| 純殘留 | 以上皆非 | **剝離** |
| 不明 | 以 `\bin` / `\Scripts` 收尾但冊上認不出 | **不生成任何動作句**,只印一條唯讀的「先看一眼」 |

最後一格是重點:生成一條把不明目錄掛回 PATH 的指令,比什麼都不生成**危險得多**
(與 MDL167 批613「不明→不動」同律)。裁定權交回操作員。

### 不代設

所有句子由哨兵**印出**,由操作員**親手貼**;而且只動本視窗的 `$env:PATH`,
要永久生效請自己走「系統內容→環境變數」。哨兵不設任何環境變數。

### 具名豁免走冊

黑名單冊 v0102 新增 `path_exemptions`,**出廠是空的**——豁免是裁定,裁定權在操作員。
每一條必須帶 `reason`,**缺 reason 一律判紅**(L87:沒理由的豁免等於假綠)。

---

## 三 · 一盞燈照兩件事

哨兵自測第 ⑩ 檢原本寫:

```python
rc = run()
chk("⑩ 實樹巡檢煙測(rc0=無紅)", rc == 0)
```

`rc` 是**實樹乾不乾淨**。於是哨兵只要**正確地**抓到一件真衝突,自測就紅,
格上那一盞「衝突哨兵十檢」跟著紅——燈上寫「自測失敗」,事實是「工具很好,樹髒了」。

拆成兩盞:

* `--selftest` 只照**工具本身**(不拋例外 + 十三道齊發 + 報告確實落地)
* 新站「**衝突哨兵實樹巡檢**」不帶參數直跑 `run()`,照**樹**

工作站那一盞會是真紅(PATH 有命中)——本來就該紅,只是以前紅在錯的名字底下。
248 → 249 站。

---

## 四 · 三個我自己造的破綻(走過 Windows 那一半才看得到)

容器裡自測全綠。合成一條工作站 PATH 餵過去,當場爆三個:

1. `\bin` 收尾的啟發式把**舊 VIA 克隆**判成帶工具,生成的句子會把死根的 bin
   複製到新家再掛上 PATH——**親手讓封存根復活**。
2. 驗收句寫 `Get-Command poppler`。poppler 沒有這支 exe,這句永遠失敗;
   冊上明明有 `exe_anchors: ["pdftoppm", …]` 而我沒用。
3. 不明工具的佔位字 `(未知工具)` 被當成資料夾名,而 `Get-Command (未知工具)`
   在 PowerShell 是**子運算式語法**。

三個都是生成器的錯,三個都只有把真實輸入餵過去才看得見。L83 第三次應驗。

---

## 五 · 順帶:v0109 的進度回歸(我在批617 自己造的)

操作員逐字稿裡 `05_EnvTools` 那一段糊成一片。根因是我留著原生 `Write-Progress`:
它每 100ms 重畫一次,和我新加的 stdout 進度行疊在同一份逐字稿裡;
再加上我把行補滿主控台寬度,退回去時留下一串 `]` 殘影。

`Invoke-VIA-AllInOne-v0110.ps1`:

* `$ProgressPreference = 'SilentlyContinue'` —— 原生通道本來就是批617 判定為
  「逐字稿裡看不見」的那一支,留著只會互相打架
* 重畫只補到**前一行的長度**,不補滿主控台寬度
* 新增 `-ProgressLines`(強制逐行)與 `-ProgressEverySec`(自訂節奏)

---

## 登錄

* 法 90(**L50 升 laws[0] rank=1** · +L92 修法句律)· 課 186(+LL183/184/185/186)
* 台帳 1214
* 新件:`via_conflict_guard_v0101.py` · `VIA_BadEnv_Blacklist_v0102.json` ·
  `SUP_MDL737_SuperAccelModule_v0105.py` · `CGC_MDL064_SelftestGrid_v0372.py` ·
  `launchers/Invoke-VIA-AllInOne-v0110.ps1`
