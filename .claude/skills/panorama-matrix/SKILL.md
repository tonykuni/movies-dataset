---
name: panorama-matrix
description: 萬用型系統級「全景偵測」:對本機路徑或 GitHub 路徑的任何程式系統做只讀、不執行、不改檔、不連外的全面現況盤點,輸出 Rich 渲染的專業矩陣報告(HTML/文字/JSON)。當使用者說「全景」「盤點現況」「檢查這個倉/這個路徑」「監測不動作」「產出矩陣報告」「看一下隔離區/鎖/帳本對不對」「這批修完有沒有退步」時觸發;要修檔、重構、跑測試時不觸發(那是 ast-sandbox 的事)。
---

# panorama-matrix — 萬用全景偵測(只看不動 · 矩陣報告)

本技能是**監測器**,不是修復器。執行體是 `scripts/panorama_matrix.py`,它轉交釘版引擎
`VeritasIntelligenceAnalytics/supportive modules/registry/VIA_Panorama_v0100.py`(同一支程式,不另抄)。

## 1. 硬規則(Hard Rules)

「監測不動作」的意思是:

| # | 規則 | 說明 |
|---|---|---|
| R1 | **只讀** | 對目標路徑不寫入任何位元組:不建檔、不改檔、不刪檔、不動 `.git` 工作樹、不 `git checkout/merge/stash`。報告只落在技能自己的輸出夾(§5.6)。 |
| R2 | **不執行目標** | 不 `import` 目標裡的任何模組、不 `subprocess` 跑目標的任何程式、不跑目標的測試。目標對本技能而言是**位元組與檔名**。 |
| R3 | **不連外** | 唯一允許的網路動作是 `git fetch / git clone --depth 1 --filter=blob:none` 讀 GitHub 目標(§6.2)。不下載規則、不打 API、不裝套件。抓不到就寫 `ABSENT`,不編。 |
| R4 | **不回原文** | 報告只放**計數、路徑、行號、雜湊、燈**。不把原始碼、設定值、金鑰、資料列貼進報告或對話。 |
| R5 | **不呼叫分析器 / 隔離區** | 不 `import` 也不 `subprocess` 任何第三方分析工具(ruff · black · mutmut · pytest · hypothesis · semgrep · coverage 等),不呼叫目標的隔離區引擎。理由見 [reference/quarantine-policy.md](reference/quarantine-policy.md)。 |
| R6 | **靜態剖析是選項,不是預設** | 預設 Tier-0 只用檔名、大小、雜湊、文字標記。`--static` 才開 Tier-1:**只用標準庫** `ast.parse` / `compile(..., dont_inherit=True)` 在本行程記憶體解析、**不 exec**,輸出只有計數與行號。 |
| R7 | **誠實燈** | 五態:`GREEN · YELLOW · RED · HOLD · ABSENT/NODATA`。量不到寫 ABSENT;隔離區寫 HOLD;黃不是綠;沒有「假綠」。 |
| R8 | **萬用** | 沒有 manifest 也能跑(§6.3 的自動探索)。VIA / 任何專案只是 `profiles/*.json` 的一份設定,核心程式碼不得寫死任何專案名。 |
| R9 | **一次一報** | 每次執行一份報告 + 一行只增 JSONL 帳本(技能自己的夾)。不改前一份。 |

## 2. 怎麼跑(省 Token:先卡、再段、最後才頁)

```bash
S=.claude/skills/panorama-matrix/scripts/panorama_matrix.py
python3 $S                                   # 預設:本倉 VIA 樹 · 範圍 VCGC,VDF,VRN → ≤15 行卡 + HTML
python3 $S <路徑|owner/repo[@br][:sub]|https://github.com/o/r/tree/br/sub> [--profile generic|via|via-verb-engine|檔.json]
python3 $S … --static                        # Tier-1(ast/compile 只在記憶體)
python3 $S show C --top 20                   # 從上一份 JSON 取一段,不重掃
python3 $S … --if-etag <上一張卡的 etag>      # 沒變回 304(約 0.3 秒)
```

1. 只看卡(≤ 15 行):總判 · 各段燈 · 前 3 紅 · 頁路徑 · etag。**不要把 HTML / JSON 整份讀進對話。**
2. 要細節 → `show <段>`;同輸入再問 → `--if-etag`。
3. 給人看 → 打開卡上的 `panorama_latest.html`(總覽矩陣在最上面,歷史矩陣在最下面)。

結束碼:`0` 總判 GREEN(隔離區 HOLD 不算紅)· `2` 有 YELLOW / ABSENT / NODATA · `1` 有 RED 或棘輪 RETROGRESS · `3` 目標讀不到。

## 3. 全景動作字典(偵測用,不是修復用)

OP-100 拓樸快照 · OP-200 靜態合規 · OP-300 無損注入候選 · OP-400 同質批次候選 · OP-500 順序重構隔離 · RATCHET 棘輪。
本技能**只判定會落在哪一級並計數**,不執行任何一級的修復。全文:[reference/action-matrix.md](reference/action-matrix.md)。

## 4. 隔離區策略(名冊策略,不是沙盒)

只核對四件事:Q1 名冊 ⊆ 鎖 · Q2 原檔都在 · Q3 各組蓋滿且不重複 · Q4 報告把隔離項一律標 HOLD。
`called: false` 是聲明,不是執行期的鎖;本技能讀它、核它、**不改它**。全文與「有做到 / 沒做到」:[reference/quarantine-policy.md](reference/quarantine-policy.md)。

## 5. 報告

三種輸出(同一份資料):`panorama_<run>.html` + `panorama_latest.html` · `panorama_latest.txt` · `panorama_latest.json`,另一行只增 `universal_ledger.jsonl`。
頁面次序:總燈列 → 總覽矩陣 → A 拓樸 → B 家族尾版 → C 靜態合規 → D 治理 → E 漂移 → F 分級佇列 → G 棘輪 → H 邊界 → 歷史矩陣。
版面自動調節(`fit_table`)、配色、CSS、輸出夾規則:[reference/report-layout.md](reference/report-layout.md)。

## 6. 輸入與探索

- 目標:本機路徑;`https://github.com/<owner>/<repo>[/tree/<branch>[/<子路徑>]]`;`owner/repo[@branch][:子路徑]`;省略 = 引擎所在的 VIA 樹。
- GitHub:`git clone --depth 1 --filter=blob:none --no-checkout --sparse` 到暫存夾 → `git ls-tree -r`(不帶 `-l`:大小要逐一抓 blob)→ 只把要看的檔稀疏取出(一次批次)→ 刪暫存夾。私有倉抓不到 = ABSENT + 結束碼 3,不重試、不要憑證。
- 沒有 manifest 時自動探索:副檔名對照語言;家族尾版正則 `^(?P<family>.+?)_v(?P<ver>\d{3,4})\.(py|ps1|json|jsonl)$`;檔名含 lock · quarantine · ledger · ssot · manifest 的 json/jsonl 列入 D 段;略過 `.git · node_modules · __pycache__ · .venv · venv · dist · build · .pytest_cache · .mypy_cache` 與含 `pyvenv.cfg` 的夾;Tier-0 標記:py docstring 首行 · `from __future__` 位置 · ps1 腳本層 `param(` 首句 · `#!`。
- 可選 `panorama.manifest.json`(只讀):`name · subsystems · ledgers · lock · quarantine · markers · tail_regex · skip_dirs`。
- profiles:`generic`(全自動)· `via`(VIA 樹:ACCEL / NET / PS 模板 / PS 加速橋 標記 · 工具鎖 · 交接冊 · 帳本 · 唯讀名冊)· `via-verb-engine`(隔離區 5 組 · 鎖 · 參考用 `VIA_PanoramaCheck.py`,不呼叫)。
  本夾的 `profiles/*.json` 與引擎旁的 `VIA_Panorama_Profiles_v0100.json` 逐鍵相同(evals 會核)。

## 7. 已知邊界(照實)

- 名冊不能代替權限:本技能不攔截磁碟寫入 / 網路 / 子行程,只保證**自己**不做。
- `--static` 用標準庫 `ast` 解析仍然「把原始碼讀進本行程」;不想擴大讀取面就不要開。
- GitHub 私有倉沒憑證就是 ABSENT;本技能不會要憑證。GitHub 目標沒有檔案大小(A 段 `bytes_unmeasured`),也沒有 E 段(只有 HEAD 快照)。
- 棘輪基準是本技能自己的帳本,不是目標倉的帳本;換輸出夾 = 基準歸零(NODATA)。首輪一定是 NODATA → 結束碼 2。
- **輸出夾例外**:`via` profile 落在目標底下 git 忽略的 `VIA_Reports/panorama`(先用 `git check-ignore` 核過;沒被忽略就退回目標外)。要嚴格照 R1 就加 `--out <目標外的夾>`。其他目標永遠落在目標外(`<cwd>/.panorama`,cwd 在目標內則 `~/.via_panorama`)。
- `rich` 沒裝時用引擎自己的純文字表與 HTML(CSS 照 report-layout.md);`--rich` 只在有 rich 時把各段表印到終端,HTML 不走 `export_html`。
- `--fetch`(更新 origin refs)與 `--predict`(`git merge-tree` 會在 `.git` 物件庫寫暫存樹)都是選項,預設不做。
- `verbs` 子命令會執行 VCGC 中央入口(不是只讀),不屬於本技能的監測範圍。
- 觸發描述的準確率還沒用 skill-creator 的描述最佳化迴圈跑過;`evals/cases.json` 的 E6 十句是給它的案例。
- 這是監測器。要修、要注入、要重跑測試,請用 `ast-sandbox`;兩者各自獨立,互不呼叫。
