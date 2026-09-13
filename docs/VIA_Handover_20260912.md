# VIA 接棒報告 — 2026-09-12

分支 `claude/via-envmanager-governance-7cls8h` · HEAD `3dd2374a`(批462)
上一份接棒報告 `docs/VIA_VRN_Handover_20260909.md`(批421)
姊妹庫 `tonykuni/VIA-VDF-VRN`:**PR #8 已於 2026-09-12 15:38 併入 main**(merge `222d9f8`)

---

## 一、一句話現況

**鏈是通的、修正是對的,卡住的是「修正送不到工作站」——
工作站的 git 工作區有未合併檔,pull 進不去,於是引擎還停在 v0122。**

工作站實測(2026-09-12):

```
[檔名層] 綁 VIA_VRN_FirstPageEngine_v0122.py      ← 尾版是 v0123,代表 pull 沒到
GREEN ENGINE …v0122 · [計] 三十九檢 OK 38 · FAIL 1
[計] 64 件 · 雙法 52 · 候OCR 8
[via-closeout] 總判 RED · DONE 27 · FAIL 10 · PENDING 6
8 份候 OCR 全卡同一句:none of the requested Tesseract languages are installed
```

三件都在操作員手上,不在碼上:**git 解卡 → 拉到 v0123 → tessdata 放語言檔**。

---

## 二、這一輪做了什麼(批454–462)

| 批 | 一句話 |
|---|---|
| 454 | Codex 兩件 P1 + 測它們時撞出的第三件。**代號沒傳到生產線**(頭號剔除律從沒被叫過,自測卻是綠的)、**年份律只看數值區間**(`Price Target 2000` 靜靜回 null)、**數字借走鄰居的貨幣記號**。兩庫同型,母庫開 `VIA_VRN_FirstPageEngine_v0123`(四十檢 40/40) |
| 455 | 中文燈句在 Windows runner 上把 CI 打紅(`UnicodeEncodeError: '無'`)。守衛由操作員修,我補「不准再鬆掉」的回歸釘(子行程實跑 cp1252) |
| 456 | 一貼收尾 `Invoke-VIA-FixAll-v0100`。**測的路徑要跟跑的路徑一樣**——我用 `-File` 測,他用「貼」的,`else` 變孤兒指令 |
| 457 | 把 main 併進 PR #8。四處衝突逐檔講清楚:入口搬到 `VIA-Launch-Console.ps1` 取 main、`VIA_EnvManager.py` 取我方(main 那版 39 行無 OCR) |
| 458 | 解卡腳本。**盲目重拉會把你卡回去**——實測跑完 `MERGE_HEAD` 又在 |
| 459 | 一鍵 `Invoke-VIA-OneKey-v0100`。**git 改成非阻塞**,死迴圈才打得斷 |
| 460 | 完整性閘。**看不見全部的儀器沒資格說全綠** |
| 461 | ③ 會把**產物**衝突自己解掉(取遠端;下次跑重生),原始碼不猜 |
| 462 | 20 加速器綁正典 `SUP_MDL737` + 不卡斷 `RunProc` + 進度百分比 |

---

## 三、這一輪自己犯的錯(比做對的更該留給接棒者)

同一個病 —— **假綠** —— 在九批裡出現**四次**,每次換一張臉:

1. **批454 ①**:`FP_TP_ECHO` 自測綠燈,但 `extractTargetPriceOf` 在整個 repo **沒有任何生產線呼叫點**。測的路徑不是跑的路徑。
2. **批456**:用 `pwsh -File` 驗證(整檔一次解析),操作員是「貼」的(逐句執行)。那條路永遠不會出 `else` 孤兒的錯。
3. **批460**:總表只印 1 列卻報 `總判:GREEN`,而同場收尾是 RED。**假綠出現在我自己的儀表上。**
4. **批462**:引擎燈全篇搜 `FAIL 0`,而子報告也印 `FAIL 0`,於是真總計 `FAIL 1` 掛綠燈。

還有一次是**誣賴**:假 tesseract 樁沒寫 `exit 0`,我差點斷定 `VIA_EnvManager` 有雞生蛋的病。去裝了真 tesseract 實測(空 tessdata 下 `exit 0`)才知道是我樁的錯。**不拿樁的行為當引擎的證據。**

立下來的規矩:
- 燈少於站數 → **不准給總判**
- 只認最後一行 `[計]` 的數字,別的地方寫什麼都不算
- 每一站**發完燈才算數**(收尾檢查有沒有發過,沒有就照實況補)
- 對照組要**實跑**確認會紅,不然就是恆真判準

---

## 四、還卡在操作員手上的

| # | 事 | 證據 | 動作 |
|---|---|---|---|
| 1 | **git 工作區未合併** | `error: Pulling is not possible because you have unmerged files` | 貼 `Invoke-VIA-OneKey-v0100.ps1`;③ 會自動解產物衝突,原始碼衝突會點名 |
| 2 | **tessdata 空** | `tesseract --list-langs` → `(0)` | 同一支腳本 ⑧ 會用 `VIA_EnvManager ocr --repair` 下載(已用真 tesseract 端到端驗過) |
| 3 | **EnvManager 三支都是舊血脈** | 兩個 clone 在 `main`、一個在 `grok/…` | **PR #8 已併 main**,在 main 的 `git pull` 即可 |

### 一個推測(未證實)

庫內有 **94 個被 track 的產物檔**(74 parquet + 6 duckdb + 2 db + 7 zip + 5 pyc)。
`.gitignore` 第 324 行有 `*.parquet`,但**不會 untrack 已經進去的檔**。
引擎每跑一次就重寫它們 → 下次 pull 撞同一批。

這**很可能**就是衝突一直復發的根,但我只看到結構、沒看到他實際卡在哪幾個檔。
③ 的未合併清單一出來就能確認或推翻。若確認,修法是 `git rm --cached`(檔案留在磁碟),
動 80+ 檔、觸及「只增不減」,**等操作員發話**。

---

## 五、姊妹庫 `VIA-VDF-VRN` 三個開著的 PR

| PR | 規模 | 病 | 查實的根因 | 建議 |
|---|---|---|---|---|
| #5 | 17 檔 | `dirty` | **56 條路徑裡 49 條 main 已有**,真正新的只有 Central SSOT 那 7 個檔 | 關掉,改在 main 上開只帶 7 檔的小 PR |
| #3 | 187 檔 | `dirty` + CI 紅 | `npm error Missing script: "via:seal"`——分支的 `package.json` 沒有,**main 有** | 先把 main 併進去,紅燈大概率跟著好 |
| #2 | 147 檔 | CI 紅 | `throw 'Standalone HTML was not generated'` | 要追那步怎麼產的 |

三個都是操作員開的、規模大,**未經他發話不動他的分支**。

---

## 六、長期未結

- Task #35 批416 F2 逐家投信 PCF 端點查實 · ETF 覆蓋 3/23
- `via-psrepair -Fix` · `via-envgov` RED 重建 · 158 個 legacy 死短令 · 5 個不可解析 ps1
- 三方對照 `AGREE 0 / 表格獨有 468` —— 比對鍵要重新設計(已提議,未動手)
- `-RepairOcr` 掛鉤隨 main 的入口搬家消失;要不要移進 `VIA-Launch-Console.ps1` 是架構作者的設計決定

---

## 七、接棒者第一步

```powershell
cd "C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics"
# 整段貼 Invoke-VIA-OneKey-v0100.ps1(一次貼完,別分段)
```

看三盞燈:`GIT`(產物衝突會自己解)、`ENGINE`(變 v0123 代表批454 生效)、`OCR-FIX`。
總判若說「不給 —— 總表只收到 N 盞燈」,那是分段貼上造成的,逐站的即時輸出仍可信。
