# VIA 收尾 · 批560 —— 你貼的那面狀態板,逐行判真假

操作員令「解決所有問題 收尾」。我**逐行去跑**過,不是照著板子複述。
結論先講:**九行裡只有兩行是真問題,其中一行是我的,已修;其餘七行是陳舊快照或你的手。**

分類只有三種,不含模糊地帶:
**真**=現在重跑還是壞 · **陳舊**=板上的數字是舊快照,尾版重跑已經好了 · **你的手**=我不能代做。

---

## 一、逐行判定

| # | 板上那行 | 判 | 證據(我在容器實跑的) |
|---|---|---|---|
| 1 | 安裝核可 L19 **BLOCKED_UNITEST** | **你的手 · 一道指令** | 阻因兩條:RunGate **齡 52.6h**(閘要 24h 內)+`vdf 家族未測`。我跑 `--family vdf`:**引擎 8/8 OK · 必要庫 4/4**。你上一跑是 **vrn-only**,所以 vdf 那欄是「未測」不是「測壞」 |
| 2 | 五矩陣 OK · GREEN 15 / PLAN 48 | **已綠** | 你自己那一跑就是證據;PLAN 48 是「只留契約不執行」,不是失敗 |
| 3 | 環境工具 UNROUTED 59 · BROKEN 2 · HIGH 2 | **你的手** | 快照是 **2026-09-14 20:50**(3 天前)。解法是 `via-envgov apply --approve` ——**裝件是你的手,我一律不代裝** |
| 4 | 環境復原 L24 **ABSENT** | **誠實 ABSENT,不是壞** | `RECOVER_latest.json` 不在 = 從來沒有需要還原過。隔離境 0。這盞要變綠,得先有一次安裝出事 |
| 5 | 中央治理家族 **RED** | **真,但不是活樹的債** | 我實跑 `via-cgfamily`:五件 md5 全對。RED 來自 console 自己 09-15 的快照 `G17 4 個循環依賴`。**而它下一行就寫著**:`G17 循環判讀 4 圈 · 活樹 0 · 退役 3 · 收容 1`——**循環全在退役與收容件裡,活樹一圈都沒有**。console 是收容件(正本零觸碰),它的判定我不改也不蓋 |
| 6 | U/I 頁 71 · 新鮮 68 · **不在 1** | **未隔離** | 我沒查出是哪一頁缺;`via-famui all` 會把該再生的補回來。**我不裝作知道** |
| 7 | VTMRA **YELLOW**(talib / talib_one ABSENT) | **陳舊 · 已經好了** | **批539 就把 talib 兩個成員隨 L50 退役拔掉了**。我實跑尾版 `CGC_MDL152 v0102`:六員 **全 OK · 判定 GREEN**。你板上那個 YELLOW 讀的是 **2026-09-15 10:08** 的舊檔,由舊版閘產的 |
| 8 | 工作流 **庫分類 RED** | **你的手 · 資料** | 這是資料新鮮度,不是程式。全部寫在 `docs/VIA_DataUpdate_B559.md`:籌碼整組缺、共識 0 列、月營收停在 2025-12 |
| 9 | 掉球 68 列 · 未結 64 | **長期 · 只增不減** | 本來就不該一次歸零;要結的是那幾件卡著你的(FRED 金鑰 / Z43 / 期貨三檔) |

---

## 二、真正是我的、已經修掉的一條

**`.gitignore` 擋不住巢狀的 `_governance/`。**

實測抓到:跑一次 `via-cgrouter`,它就在**自己旁邊**產出五個檔——

```
supportive modules/VIA_Central_Governance/VIA_CentralGovernanceFamily_b514/_governance/priority/
  file_index.json · priority_manifest.json · format_catalog.json
  VIA_Priority_Matrix_*.html · priority_log_*.log
```

而 `.gitignore` 只有 `VeritasIntelligenceAnalytics/_governance/`(**根目錄那一個**),
擋不住巢狀的。也就是說:**任何人跑一次家族,再 `git add -A`,執行產物就混進正本夾**
——那是正本零觸碰的破口,而且它安靜到沒人會發現。

修法(只增不減,加一行):

```gitignore
VeritasIntelligenceAnalytics/**/_governance/
```

負向對照:我先建一個巢狀 `_governance/x/t.json`,確認 `git status` **看不見它**,再刪掉。
我自己跑出來的那五個檔也已經刪除,樹回到原狀。

---

## 三、一貼即用(清掉板上七行裡的五行)

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
git pull origin claude/via-envmanager-governance-7cls8h
. (Get-ChildItem 'Register-VIA-Commands-v*.ps1' | Sort-Object Name | Select-Object -Last 1).FullName

via-rungate --all      # ① 清 L19 BLOCKED(24h 內 + 兩族都測)
via-vtmra              # ⑦ 清 VTMRA 陳舊 YELLOW → 應為 GREEN(尾版閘已無 talib)
via-famui all          # ⑥ 補那一頁不在的
via-cgfamily cycles    # ⑤ 把 G17 四圈對回檔名(確認活樹仍是 0)
via-entry              # 重出狀態板
```

剩下兩行要你決定:
`via-envgov apply --approve`(③ 裝件=你的手)· `docs/VIA_DataUpdate_B559.md` 那段(⑧ 資料回補)。

---

## 四、我沒做、也說明為什麼

- **沒去改 console 的 G17 判定**:`VIA_CentralGovernanceConsole.py` 是收容件,正本零觸碰。
  而且把 RED 改成 GREEN 只因為「循環在退役件裡」,那是我替它發明一個綠燈。
  正確做法是 MDL150 現在這樣:**照實轉述 console 說的 RED,旁邊附上活樹 0 的判讀**,由你看完再決定。
- **沒裝任何套件**、**沒設任何同意閘**、**沒 merge / approve PR #38**。
