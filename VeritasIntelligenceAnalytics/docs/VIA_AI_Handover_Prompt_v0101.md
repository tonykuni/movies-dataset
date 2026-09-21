# VIA · AI 接手提示詞與交接格式 v0101(批688;長久使用)

> v0100(批507)→ v0101(批688)改了什麼:① 主線不再是一條固定分支,改走「自己的分支 → PR → main」;② 同一天有三條線並行,
> **批號與版號是跨分支共用資源**(LL334:2026-09-21 一天撞四次);③ VCGC v0119 起 ⑬ 把執行期境另列;④ 新容器的套件與料靠開機更新器 ⓪ 自補(批687 起逐件退路);
> ⑤ 格子再生件永不 commit(LL117 ③)。其餘規矩不變。
>
> 這套系統是**多個 AI 工作階段接力寫成的**(每批 `批NNN` 一次 commit),操作員下令、AI 造件、操作員實測貼回、AI 讀實錄修。
> 對話會卡斷,檔案不會。所以「接手不掉球」靠三個檔,不靠對話記憶:
> ① 倉根 `VIA_HANDOVER_LATEST.md`(VCGC 一頁交接;〇 接手提示 + 一～十三段 + 九 掉球清單)
> ② `docs/VIA_Handover_2026MMDD_BNNN.md`(逐批紀錄;最新一份)
> ③ `supportive modules/registry/VIA_Policy_Laws_SSOT_v*.json`(律 + lessons;違反=重犯)

---

## A · 給被交接者(接手 AI)——開場提示詞,整段貼進新對話即可

```text
你接手 VIA(VeritasIntelligenceAnalytics)。倉 tonykuni/movies-dataset;主線在 main。
每個工作階段用自己被指派的分支(claude/<名>)從 main 起算,每批一個 commit「批NNN:…」,推分支後開 PR 併回 main
(操作員說「自動開」就自己開;永不 approve、永不 merge;操作員是併的那隻手)。
工作根 VeritasIntelligenceAnalytics/。操作員用中文;工作站 C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics。

先做(不准跳過,任何造件之前):
0. 對齊遠端(L25 多 AI 交會律):git fetch origin; git status --short; git log --oneline HEAD..origin/main
   落後 → git checkout -B <你的分支> origin/main(你的分支已併進 main 的話這是純快轉,推上去不是 force);
   工作站或別條線的未推件(未推 commit / 未追蹤新版號檔)→ 先推側枝 local/parallel-B<批>,再對齊。永不在陳舊樹上造件。
0b. 批號與版號是跨分支共用資源(LL334)。取號之前掃**全部**遠端分支,不只本地樹:
      git log --remotes=origin --format=%s | grep -oE '^批[0-9]+[A-Z]?' | sort -u | tail -5
      for r in $(git for-each-ref --format='%(refname:short)' refs/remotes/origin); do git ls-tree -r "$r" --name-only | grep -E '<檔名前綴>_v[0-9]+\.py$'; done | sed 's#.*/##' | sort -u | tail -3
    撞了:先併進 main 的贏;後到的改號(批 → 加字尾 B;檔 → 疊在 main 那份上開下一個版號),已推的歷史不改(L08 零 force push)。
1. 讀倉根 VIA_HANDOVER_LATEST.md(〇 接手提示 · 一 政策庫 · 二 安裝核可/環境工具 · 三 邏輯/因子/資料庫 · 四 引擎調度/多矩陣 ·
   五 指令與參數 · 六 註冊稽核 · 七 台帳 · 八 交接本文 · 九 掉球清單 · 十一 中央治理家族 · 十二 U/I 工作流 · 十三 VRN 對接口)。
2. 讀 docs/ 最新 VIA_Handover_*_B*.md 的「五 掉球」「六 你的手」與「四 實錄讀出」。
3. 讀 VIA_Policy_Laws_SSOT_v*.json(律 99;lessons 冊上到 LL305,LL306 起只在批文與 commit 訊息裡,見 Z59);最常犯的 12 條背起來:
   L01 先想省 token(不重讀大檔,grep 要改的段;操作員貼回的實錄直接當量測)
   L02 只增不減 · L03 正本零觸碰(references/intake 不編輯)· L04 尾版律(引擎改=新版號檔;冊/無版號檔才就地改)
   L05 Zero-Hydra(綁既有引擎;同一判準只寫一處)· L06 零 CDN 零彈窗
   L07 同意閘(VIA_NET_CONSENT/VIA_SCRAPE_CONSENT/金鑰)操作員自設,永不代設
   L08 零 force push;不 Stop-Process;不 Remove-Item/conda remove/pip uninstall 操作員的境;裝件=操作員的手(--approve + 閘)
   L09 加速器/網路只認 VeritasCeleritas/VeritasAegisNexus · L16 誠實四態 ABSENT/NODATA/GATED/RED(判錯的燈和假綠一樣傷)
   L17 自測零污染(VIA_SELFTEST=1;撤 VIA_DB_*/VIA_DATA_HOME;只寫暫存)· L18 功能註冊七處(規格項/格子站/Register/Deck/Manager/台帳/交接)
   L19 環境統一測式 GREEN 24h 內才核可安裝 · L20 VCGC 為唯一對接口 · L23 只刪有 md5 證據的重複件 · L50 TA-Lib 禁,QuantGuard 唯一正主
4. 接手驗收(在容器裡跑,貼結果給操作員,證明你接上了):
   VCGC=$(ls "supportive modules/registry"/CGC_MDL149_VeritasCentralGovernanceConsole_v*.py | sort | tail -1)   # 尾版律:永遠拿最新版號
   python3 "$VCGC" status
   python3 "$VCGC" --selftest        # v0119 起二十五檢;⑬ 的「runtime 另列 N」是執行期境(TOOLS_PLAN),不進等式,工作站 N=1、容器 N=0 都對
   git log --oneline -3
5. 讀「九 掉球清單」,把仍掛著的項目原樣列回給操作員,問他要先追哪一顆——不要自己挑。
   他若說「依你建議進行」,就照你列的順序做,每顆開工前說一聲,他隨時可以改。

容器規矩(容器不是他的機器):
- 新容器沒有套件也沒有料。SessionStart 開機更新器 ⓪ 段會自補套件(批687 起整份失敗會退回逐件裝、jieba 走 --use-pep517),
  然後跑資料車道;容器裡 TWSE openapi 三車道回非 JSON,所以產業表 / ETF 冊不會有,那幾站固定紅。
- 全格子在容器固定紅 5(pwsh 不在 · 產業表 ×3 · 首頁 sidecar 庫 0 份),寫明「容器」;不要為了綠去改尺。
- 格子跑完會再生 30 個頁/冊(LL117 ③):跑完 `git stash push -m "grid regen"`(不帶 -u),永不 commit 再生件;自己的改動先 commit 再跑格子最省事。
- 容器裡的 NODATA/ABSENT 不是壞;TA-Lib 禁裝(L50,六域現況矩陣會照紅);不 pip uninstall 操作員的境,容器是自己的沙盒。

工作節奏(每一批都一樣):
- 量現況 → 造件(引擎改=新版號檔;先掃版號)→ --selftest → 七處登冊(台帳 VIA_AutoCode_Registry **照原檔自己的格式寫回**,量出來不挑;
  registry-sync --apply 用尾版 VCGC)→ 掉球清單(新掛的加、結案的劃線)→ 批文 docs/VIA_B<批>_<英文題名>.md →
  推之前跑全格子(LL117)→ commit「批NNN:…」(尾註只留 Co-Authored-By / Claude-Session 兩行;倉內產物不放模型識別字)→ push → 開 PR。
- 三本只增不減冊(台帳 / 元件冊 / 掉球清單)併線必撞,取聯集:台帳兩邊都留、掉球改編號續排、元件冊取 main 再用尾版 VCGC 重跑 registry-sync。
- PR 上 Codex 的每一條:對樹驗真假;真的就在新版號檔修、跑自測、回覆、resolve;假的講清楚為什麼,不改。紅圈不當可選。
- 回覆操作員:中文;先講結果 → 你的手 → 一個 PowerShell 一貼即用區塊,前兩行固定:
    Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
    . (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
  → 要他貼回哪幾個指令的尾段;他貼回來的實錄直接當量測,不自己重跑。他的工作站可能在別條線的分支上,先看 git log -1。
- 收尾:via-vcgc page --publish(一頁交接 + 倉根副本 + 頁,三處同一份)→ 台帳 → 交接紀錄 → commit → push → PR;再回覆。

掉球定義:操作員說過、你沒做也沒寫進掉球清單的事。掉球清單只增不減,結案用 ~~刪除線~~ 加「已結(批NNN)」。
```

## B · 給交接者(離場 AI)——收尾清單(每一條都要有證據路徑)

0. push 前 git fetch 再比對(HEAD..origin/main 無落後);新版號檔與批號先掃全部遠端分支(LL334);撞名=另一條線在跑,後到的改號。

| # | 收尾 | 證據 |
|---|------|------|
| 1 | 所有改動 commit「批NNN」並 push;工作樹乾淨(`git status --short` 空;再生件 stash 不 commit) | commit hash |
| 2 | `via-vcgc page --publish`:一頁交接 `docs/VIA_Handover_ONEPAGE.md`、倉根 `VIA_HANDOVER_LATEST.md`、頁 `ui_support/VIA_UI_CentralGovernanceConsole_v0100.html` 三處同一份 | 三檔同一產生時間 |
| 3 | 掉球清單 `docs/VIA_DroppedBalls_*.md` 更新(新掛的加、結案的劃線);未做的**寫進去比做一半更重要** | 檔在、ONEPAGE 九段有列 |
| 4 | 台帳 `VIA_AutoCode_Registry_v0100.json` 追記本批(ts/op/category/component/code;照原檔格式寫回) | 筆數 +1 |
| 5 | 逐批紀錄 `docs/VIA_Handover_YYYYMMDD_BNNN.md`(格式 C)或至少批文 `docs/VIA_B<批>_*.md` | 檔在;ONEPAGE 八段來源換成它 |
| 6 | 新引擎七處登冊齊(規格/格子/Register/Deck/Manager/台帳/交接);`via-vcgc audit` 未登冊數不增 | audit 數 |
| 7 | PR 開了、CI 綠、Codex 討論串全部答過並 resolve;併不併是操作員的手 | PR 號 |
| 8 | 操作員機器要跑的復原/同步指令寫在回覆的 PS 區塊(例:`via-vrnlogic sync-db`) | 回覆 |
| 9 | 最後一則回覆:結果 → 你的手(操作員待辦)→ PS 區塊 → 要貼回什麼 | — |

## C · 交接紀錄固定格式(長久使用;人與 AI 都讀得懂)

```
# VIA 交接紀錄 · 批NNN(YYYY-MM-DD)
〇 接手提示詞 → 見 docs/VIA_AI_Handover_Prompt_v*.md(尾版)
一 律(新收到的原文照錄;編號進 VIA_Policy_Laws_SSOT;未入冊的教訓寫明「未編號」)
二 現況快照(VCGC status 原樣貼;寫明容器還是工作站)
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
- 批號與版號是跨分支共用資源(LL334):三條線同一天各自取號,撞了先併 main 的贏,後到的改號;取號前掃全部遠端分支。
- 三本只增不減冊(台帳 / 元件冊 / 掉球清單)併線取聯集,不挑一邊。
- 執行期產物(VIA_Reports/ 底下任何 *_latest.json)不進 SSOT 等式:它只在跑過那支工具的機器上存在,算進去=冊隨機器翻轉(批681/682/682B 的 ⑬)。
- 補丁包進了樹、產物沒進樹,就是一條看不見的分岔(批682B):收到補丁包的那一批就把產物落地,做不到就登掉球清單。
- 早退分支不准把承諾一起退掉(批687):誠實話(不代設)要跟著每一條路走出去,不是只跟著成功的那條。
