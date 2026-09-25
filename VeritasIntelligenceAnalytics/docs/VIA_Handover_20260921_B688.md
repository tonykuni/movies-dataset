# VIA 交接紀錄 · 批682B–688(2026-09-21)

〇 接手提示詞 → 見 `docs/VIA_AI_Handover_Prompt_v0101.md`(尾版;本批改版:分支→PR→main、LL334 取號掃全部分支、v0119 執行期列、容器自補、再生件不 commit)。

## 一 · 律

本期無新律。律冊 lessons 停在 LL305(批662),LL306 起只在批文與 commit 訊息裡(Z59 未做)。本期三條未編號教訓:
- **補丁包進了樹、產物沒進樹,就是一條看不見的分岔**(批682B):工作站三天跑在倉裡不存在的 EngineBus v0128 上,零紅燈。
- **早退分支不准把承諾一起退掉**(批687):ENG090 ㉔ 的「不代設」只跟著成功路徑走,四條 ABSENT 早退分支沒帶。
- **批號與版號跨分支共用,先併 main 的贏**(LL334 今天四次撞號:批682 ×2、批687 ×2、CGC_MDL149 v0119 ×2、Grid v0431):取號前掃全部遠端分支。

## 二 · 現況快照(**容器**,VCGC v0119 `status` 原樣;操作員機器見四)

```
[VCGC] v0119 批662 · 唯一對接口(L20)· 2026-09-21 11:01:54
  政策庫 OK:律 99 · lessons 305 · 政策因子 1766 列
  邏輯庫 OK:件 0 · {} · 壞後端 [] · 同步 {'hash': 'f97024991d6e', 'counts': {'未入': 1}, 'dbs': 1}
  因子庫 OK:130 列 {'SUP_MDL748:allinone 2.1.0': 77, 'SUP_MDL748:financial_data_standardization': 53}
  VRN 系統管理 STALE/NODATA:燈 {'policy': 'GREEN', 'logic': 'GREEN', 'factor': 'GREEN', 'param': 'GREEN', 'engine': 'GATED', 'handover': 'STALE', 'records': 'GREEN'} · 連結 162 {'GREEN': 158, 'GATED': 1, 'ABSENT': 1, 'STAL
  資料庫:庫表冊 54 表 · 資料家 ABSENT VIA_Reports/datahome/DATAHOME_CATALOG_latest.json 不在(via-datahome catalog)
  引擎調度:Deck 90 任務 · 規格 65 項 · 格子 287 站 · Register 166 指令
  多矩陣 ABSENT:ENGINE_BUS_latest.json 不在(via-ryg) · profile None · RunGate YELLOW → BLOCKED_UNITEST
  環境工具 ABSENT:TOOLS_PLAN_latest.json 不在(via-envtools)
  環境復原 ABSENT:RECOVER_latest.json 不在(via-envrecover;L24 安裝出問題先還原前次再順序裝) · 隔離境 0(L24)
  VTMRA 家族測試閘 ABSENT:VTMRA_latest.json 不在(via-vtmra 跑一次即有;七成員家族境真跑自測)(批516;via-vtmra)
  中央治理家族 ABSENT:FAMILY_latest.json 不在(via-cgfamily 跑一次即有;五成員經 CGC_MDL150 擁有者起跑,預設 dry-run) · 成員 -(批514;via-cgfamily)
  註冊稽核:中央冊 6004/6004 缺 0 · 家族 270 已登 270 未登 0 · 操作介面 228
  台帳 1286 筆 · 交接源 VIA_Handover_20260920_B664.md · 頁/一頁:via-vcgc page|onepage(落 VIA_Reports/vcgc;--publish 才入倉)
```

## 三 · 本期做了什麼

| 批 | 件 | 檔(版號) | 自測 | 證據 |
|---|---|---|---|---|
| 682B | 接手 session_01RLMQGZLcigd5Bt5aN6J4Ck;EngineBus v0128 依 L25 落地(操作員側枝 da89abbc cherry-pick) | `CGC_MDL148_EngineBus_v0128.py` | 四十八檢 49/49 | v0127+_patches diff 位元同 · md5 213a6412 |
| 682B | Codex P1:執行期境不進元件等式(Z79) | `CGC_MDL149_…_v0119.py` | 二十五檢 25/25 | 工作站 ⑬ 5991/5991 · runtime 另列 1;容器另列 0 |
| 682B | Codex P2:NEED_INPUT 只認帶 --in | `CGC_MDL148_EngineBus_v0129.py` | 四十九檢 50/50 | ㊿ |
| 687 | Z80:ENG090 ㉔ 四態全帶「不代設」+㉕ | `VDF_ENG090_DataCoverageGate_v0105.py` | 24/24 | 格子站 newest → v0105 OK |
| 687 | Z81:開機更新器 ⓪ 逐件退路 | `via_boot_update.sh`(就地改) | 合成檢 bogus+jieba:逐件 2 · 失敗 1 | `bash -n` 過 |
| 688 | Z58:一頁交接三處追現況 + 提示詞 v0101 + 本紀錄 | `docs/VIA_AI_Handover_Prompt_v0101.md` · `docs/VIA_Handover_20260921_B688.md` · `page --publish` 三處 | VCGC ⑩⑫ | 三檔同一產生時間 |
| 682B–688 | 推之前全格子 | v0432 → v0433 → v0435 | OK 278 · FAIL 5 · SKIP 4 · TIMEOUT 0(三輪同 5 站容器紅) | GRID_20260921_091300 / 104543 |

PR:#58(682B,已併)· #61(687,已併)· #57 關(內容 ⊂ #58 + 批684)。

## 四 · 實錄讀出(操作員貼回 → 讀出 → 修)

| 你貼的 | 讀出 | 修 |
|---|---|---|
| `git status` 在 busy-bell 上有 `?? CGC_MDL148_EngineBus_v0128.py` ×2 + `.bak_b600_*` | B600 補丁包 09-18 套出的產物三天只在工作站;30 條遠端分支都沒有 | L25 側枝 `local/parallel-b600-bus-v0128` da89abbc → 本線 cherry-pick(批682B) |
| `via-vcgc status` 中央冊 5849/5879 缺 30 · 未登 1 VRN_ENG088 | busy-bell 側線自己的檔沒 registry-sync,PR #53 的債 | 歸那條線 |
| `git log -1` = 0b6f7dfb(awesome-bardeen 批684);`via-vcgc --selftest` ⑬ 5993/5994 缺 1 | 工作站在 awesome-bardeen 分支;v0118 把 TOOLS_PLAN 的虛境算活元件、冊上那筆已退役 → Z79 症狀實地出現 | 換 main 跑 v0119 |
| main b45c9380 · v0119:registry-sync PLAN 退役 0;二十五檢 25/25;⑬ 5991/5991 · runtime 另列 1 | Z79 在工作站結案 | 寫進掉球與批687 |
| 「依你建議進行 · 關」「你自動開」 | 關 PR #57;之後每批推完自動開 PR;下一顆依建議 | 批687、批688 |
| 工作站 stash 25 個;`checkout main` 曾被兩個再生檔擋住 | 再生件用 `git stash push`(不帶 -u)收,不 commit | 提示詞 v0101 寫進容器/工作站規矩 |

## 五 · 掉球清單 → `docs/VIA_DroppedBalls_B507.md`(列 99 · 未結 89;只增不減)

本期新掛:Z78(v0128 落地)· Z79(⑬ 互翻)· Z80(ENG090 ㉔)· Z81(開機自補)· Z87(批687 撞號:awesome-bardeen 62d38dd4 也取 687,未併)。
本期結案:~~Z78~~(682B)· ~~Z79~~(682B;工作站實錄 687)· ~~Z80~~ ~~Z81~~(687)· ~~Z58~~(688)· ~~Z70~~(688:brave-goldberg 線已出現並併入)。
仍掛在本線名下候裁:Z59(LL306–LL336 入律冊)· Z63(ebit/ocf 一句話 + 六層層名)· Z86(busy-bell v0119 撞號 → v0120)。

## 六 · 你的手

1. busy-bell(PR #53):`CGC_MDL149_…_v0119.py` 撞 main 的 v0119 → 那條線改 v0120 疊在 main 的 v0119 上(保留 runtime 列);請轉告。
2. awesome-bardeen:批687 撞號(62d38dd4 未併;main 的 687 是本線)→ 它改 687B 或下一號;請轉告。
3. Z63:`ebit` 要不要接 operating_income、`ocf` 三名一路;L0–L5 六層層名——各一句話。
4. Z59 要不要開一批把 LL306–LL336 入律冊(要逐批文抄原文,一批的量)。

## 七 · 一貼即用

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
git fetch origin
git checkout main; git pull --ff-only origin main
git log --oneline -1
via-vcgc status
```

## 八 · 接手驗收(接手者在容器跑)

```
VCGC=$(ls "supportive modules/registry"/CGC_MDL149_VeritasCentralGovernanceConsole_v*.py | sort | tail -1)
python3 "$VCGC" status        # 期望:註冊稽核 中央冊 N/N 缺 0 · 家族 270/270 · 台帳 ≥1287
python3 "$VCGC" --selftest    # 期望:二十五檢 OK 25 · ⑬ ACTIVE N/N · runtime 另列 0(容器)/1(工作站)
git log --oneline -3          # 期望:頭是本線批688 或之後
```
