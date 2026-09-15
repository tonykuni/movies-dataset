# VIA · AI 接手提示詞與交接格式 v0100(批507;長久使用)

> 這套系統是**多個 AI 工作階段接力寫成的**(每批 `批NNN` 一次 commit),操作員下令、AI 造件、操作員實測貼回、AI 讀實錄修。
> 對話會卡斷,檔案不會。所以「接手不掉球」靠三個檔,不靠對話記憶:
> ① 倉根 `VIA_HANDOVER_LATEST.md`(VCGC 一頁交接;八段 + 〇 接手提示 + 九 掉球清單)
> ② `docs/VIA_Handover_2026MMDD_BNNN.md`(逐批紀錄;最新一份)
> ③ `supportive modules/registry/VIA_Policy_Laws_SSOT_v*.json`(23 律 + lessons;違反=重犯)

---

## A · 給被交接者(接手 AI)——開場提示詞,整段貼進新對話即可

```text
你接手 VIA(VeritasIntelligenceAnalytics)。倉 tonykuni/movies-dataset,分支 claude/via-envmanager-governance-7cls8h,
工作根 VeritasIntelligenceAnalytics/。操作員用中文;工作站 C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics。

先做(不准跳過,任何造件之前):
0. 對齊遠端(L25 多 AI 交會律):git fetch origin claude/via-envmanager-governance-7cls8h; git status --short; git log --oneline HEAD...origin/claude/via-envmanager-governance-7cls8h
   落後→ git pull --ff-only;本機有別的線(未推的 commit/未追蹤的新版號檔)→ 先 commit 到側枝 local/parallel-B<批> 並 push,再對齊;永不在陳舊樹上造件。
1. 讀倉根 VIA_HANDOVER_LATEST.md(一頁交接:〇 接手提示 · 一 政策庫 · 二 安裝核可/環境工具 · 三 邏輯/因子/資料庫 ·
   四 引擎調度/多矩陣 · 五 指令與參數 · 六 註冊稽核 · 七 自動編號註冊表 · 八 交接本文 · 九 掉球清單)。
2. 讀 docs/ 最新 VIA_Handover_*_B*.md 的「三 還掛著的事」與最後兩批段落。
3. 讀 VIA_Policy_Laws_SSOT_v*.json 的 23 律;下面 12 條是最常犯的,背起來:
   L01 先想省 token(不重讀大檔,grep 要改的段;操作員貼回的實錄直接當量測)
   L02 只增不減 · L03 正本零觸碰(references/intake 不編輯)· L04 尾版律(引擎改=新版號檔;冊/無版號檔才就地改)
   L05 Zero-Hydra(綁既有引擎;同一判準只寫一處)· L06 零 CDN 零彈窗
   L07 同意閘(VIA_NET_CONSENT/VIA_SCRAPE_CONSENT/金鑰)操作員自設,永不代設
   L08 零 force push;不 Stop-Process;不 Remove-Item/conda remove/pip uninstall;裝件=操作員的手(--approve + 閘)
   L09 加速器/網路只認 VeritasCeleritas/VeritasAegisNexus · L16 誠實四態 ABSENT/NODATA/GATED/RED(判錯的燈和假綠一樣傷)
   L17 自測零污染(VIA_SELFTEST=1;撤 VIA_DB_*/VIA_DATA_HOME;只寫暫存)· L18 功能註冊七處(規格項/格子站/Register/Deck/Manager/台帳/交接)
   L19 環境統一測式 GREEN 24h 內才核可安裝 · L20 VCGC 為唯一對接口 · L23 只刪有 md5 證據的重複件
4. 接手驗收(在容器裡跑,貼結果給操作員,證明你接上了):
   VCGC=$(ls "supportive modules/registry"/CGC_MDL149_VeritasCentralGovernanceConsole_v*.py | sort | tail -1)   # 尾版律:永遠拿最新版號
   python3 "$VCGC" status
   python3 "$VCGC" --selftest
   git log --oneline -3
5. 讀「九 掉球清單」,把仍掛著的項目原樣列回給操作員,問他要先追哪一顆——不要自己挑。

工作節奏(每一批都一樣):
- 每批一個小主題;commit 訊息「批NNN: …」;push origin claude/via-envmanager-governance-7cls8h(失敗退避重試,不 force)。
- commit 尾註只留 Co-Authored-By / Claude-Session 兩行;倉內任何產物不放模型識別字。
- 造件前先 grep 現況;造完跑 --selftest;新引擎=七處登冊 + 台帳 VIA_AutoCode_Registry(indent=1)+ 交接段。
- 回覆操作員:中文;先講結果;一個 PowerShell 一貼即用區塊,前兩行固定:
    Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
    . (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
  然後要他貼回哪幾個指令的尾段;他貼回來的實錄直接當量測,不自己重跑。
- 容器沒有他的資料與環境(via_database、48 個 env、Tesseract、Paddle);容器裡的 NODATA/ABSENT 不是壞,寫明「容器」。
- 收尾:via-vcgc page --publish(一頁交接 + 倉根副本 + 頁)→ 台帳 → 交接段 → commit → push;再回覆。

掉球定義:操作員說過、你沒做也沒寫進掉球清單的事。掉球清單只增不減,結案用 ~~刪除線~~ 加「已結(批NNN)」。
```

## B · 給交接者(離場 AI)——收尾清單(每一條都要有證據路徑)

0. push 前 git fetch 再比對(HEAD...origin 無分歧);新版號檔要先看遠端有沒有同名(撞名=另一條線在跑,見 L25/LL13)。

| # | 收尾 | 證據 |
|---|------|------|
| 1 | 所有改動 commit「批NNN」並 push;工作樹乾淨(`git status --short` 空) | commit hash |
| 2 | `via-vcgc page --publish`:一頁交接 `docs/VIA_Handover_ONEPAGE.md`、倉根 `VIA_HANDOVER_LATEST.md`、頁 `ui_support/VIA_UI_CentralGovernanceConsole_v0100.html` 三處同一份 | ENG082 ⑯ 交接三處 = 同 |
| 3 | 掉球清單 `docs/VIA_DroppedBalls_*.md` 更新(新掛的加、結案的劃線);未做的**寫進去比做一半更重要** | 檔在、ONEPAGE 九段有列 |
| 4 | 台帳 `VIA_AutoCode_Registry_v0100.json` 追記本批(code/kind/ts/name 四欄;indent=1) | 筆數 +1 |
| 5 | 逐批紀錄 `docs/VIA_Handover_*_B*.md` 追加本批段(做了什麼/實錄讀出/你的手/一貼即用) | 段在 |
| 6 | 新引擎七處登冊齊(規格/格子/Register/Deck/Manager/台帳/交接);`via-vcgc audit` 未登冊數不增 | audit 數 |
| 7 | 操作員機器要跑的復原/同步指令寫在回覆的 PS 區塊(例:`via-vrnlogic sync-db` 讓六本庫的 via_policy_factors/via_handover 跟上) | 回覆 |
| 8 | 最後一則回覆:結果 → 你的手(操作員待辦)→ PS 區塊 → 要貼回什麼 | — |

## C · 交接紀錄固定格式(長久使用;人與 AI 都讀得懂)

```
# VIA 交接紀錄 · 批NNN(YYYY-MM-DD)
〇 接手提示詞 → 見 docs/VIA_AI_Handover_Prompt_v*.md(尾版)
一 律(新收到的原文照錄;編號進 VIA_Policy_Laws_SSOT)
二 現況快照(VCGC status 八行原樣貼)
三 本批做了什麼(表:件 / 檔(版號) / 自測 n/n / 證據)
四 實錄讀出(表:你貼的 / 讀出 / 修)
五 掉球清單(表:代號 / 事 / 狀態 未做·候·操作員的手·容器紅 / 誰 / 下一步)——只增不減,結案劃線
六 你的手(操作員待辦:閘/裝件/決策)
七 一貼即用(PS 區塊;前兩行固定)
八 接手驗收(接手者要跑的三個指令與預期輸出)
```

## D · 「多 AI 寫作」的規矩(為什麼要這樣)

- 每個 AI 只活一個對話;**檔案是唯一的記憶**。所以規則、掉球、參數、指令全部要落檔,不留在對話裡。
- 同一判準只寫一處(L05):兩個 AI 各寫一份,第三個 AI 只會改到其中一份。
- 自測不讀自測本身的字串(LL:批504/506 兩次自我引用誤判)。
- 登冊腳本逐檔獨立寫入、失敗要可見(LL09:批505 錨點斷掉只上一半還 commit 了)。
- 判錯的燈和假綠一樣傷(L16):接手者第一件事不是造新件,是把上一位的燈對一遍。
