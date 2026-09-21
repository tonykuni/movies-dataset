# 批692 · 工作站那兩盞紅,紅的是尺不是引擎:一把拿隨資料變的數當斷言,一把拿 POSIX 字串比 Windows 的 Path

> 本線=VRN 線(分支 `claude/vrn-line-b691`,第一版 b38ad8cf 推到 PR #68 時 PR 已在 43b4e03e 併掉,重新自 main 90c59c14 重起、重貼)。批號 692 取號前掃過全部遠端分支(LL334):691/691B 已用,692 空。
> 版號:SUP_MDL746 v0100 → **v0101**;CGC_MDL141 v0110 → **v0111**(第一版取 v0110 時 PR #65 已把側線 c 的 v0110 併進 main:它只加 duckdb 缺=ABSENT rc3,沒修 ⑫;LL334 先併的贏,本檔疊其上重貼)。Grid 站名不含檢數(九檢/十四檢不變),不開 Grid 版。

來件:母線 awesome-bardeen 2026-09-21 17:29Z 轉交操作員貼回的工作站 `via-vrnrun` 兩行 `[FAIL]`(Z84 從批685 掛到現在;工作站樹在本線 644663ee 上跑)。直接當量測,不重跑。

## 一 · 讀出(兩行都被截斷,但截到的部分已足夠對樹)

| 貼的 | 對樹 | 根因 |
|---|---|---|
| `SUP_MDL746_PDFPlumberPlusHub RED 33.0s:[FAIL] ⑦ 密度只當訊號不當判決——949×7448 長捲頁那件有 862 字真正文…字數 >= 300 只標 THIN 不降級` | ⑦ 斷言三件:THIN 全 >= 300 字 · SCANNED 全 < 300 字 · **全庫最低 DIGITAL 首頁字數 > 300**。前兩件是 `triage()` 規則表推得出的不變量;第三件不是:DIGITAL 的條件只有密度 >= 2e-4、字數 >= 10 | 工作站 `input/incoming` 64 件裡任一頁小版面、字少但密的封面/摘要頁 = DIGITAL < 300 字 → 工作站必紅;容器只有 specs/ 夾具,沒這種頁 → 容器必綠。**判錯的燈**(L16)+ 隨資料變的數當斷言(LL332)。容器重現:塞一頁 200×200 pt、83 字(密度 2.08e-3)的 PDF 進樹,v0100 ⑦ 立刻紅、v0101 綠 |
| `CGC_MDL141_ClosingGate RED 12.3s:[FAIL] ⑫ CLI --db/--zones 真的傳到 vrn_closeout(批425…實跑證據=ENG080 報 GREEN/上漲已算…` | ⑫ 餵 `--db /tmp/_x_.duckdb --zones /tmp/_z_`,main() 照批425 `Path(_v)` 再轉發(這一段是對的);自測用 `str(kw["db"]) == "/tmp/_x_.duckdb"` 比 | Windows 的 `str(Path("/tmp/_x_.duckdb"))` 是 `\tmp\_x_.duckdb`,字串永遠不等 → 工作站必紅、POSIX 容器必綠。母線猜的「讀到第二顆頭的庫」不是這一盞的因(那是 Z88,另一件事) |

## 二 · 做了什麼(兩支判準本體零改;改的都是自測那把尺)

| 件 | 檔 | 改 | 驗 |
|---|---|---|---|
| 尺不拿隨資料變的數當斷言 | `supportive modules/70_VRN_Rules/SUP_MDL746_PDFPlumberPlusHub_v0101.py` | ⑦:① 夾具本人 `specs/Veritas Intelligence Analytics Brief.pdf` 必須 THIN、字數 >= 300、密度 < 門檻(這才是「密度只當訊號」的真檔證據);② 全庫每件合規則表(THIN ⇒ >= 300 · SCANNED ⇒ < 300 · DIGITAL ⇒ 密度 >= 門檻);③ 最低 DIGITAL 字數只印不斷言 | 九檢 9/9;重現件在樹時 v0100 8/9 · v0101 9/9;夾具 THIN 862 字 1.22e-4 |
| 尺比 Path 不比字串 | `supportive modules/registry/CGC_MDL141_ClosingGate_v0111.py` | ⑫:`Path(str(kw["db"])) == Path("/tmp/_x_.duckdb")`(zones 同);橫幅 v0105/十二檢 → v0111/十四檢(停了五版) | 十四檢 14/14 |
| 格子 | Grid v0445 `--only` 兩站 | 站名不含檢數,不改 | OK 2/2 |
| 索引冊 / 元件冊 | `via-vrnbook build` · VCGC v0123 registry-sync `--apply` | 兩支指標 → 新尾版 | VCGC 廿九檢;總管連結見四 |
| 掉球 | ~~Z84~~ 已結(批692) | | |

**沒動的**:`triage()` 規則表、`main()` 的 --db/--zones 透傳、Grid、格子站名、其餘引擎。

## 三 · 沒法在容器證的一件

兩支修的都是「工作站紅、容器綠」的尺;容器只能證「舊尺會紅的那種輸入,新尺不紅」(⑦ 用 83 字密頁重現了)與「Path 比法在 POSIX 仍綠」。**工作站那兩格真的轉綠,要你拉了 批692 再跑一次 `via-vrnrun` 貼回**。

## 四 · 全格子(LL117;容器)

第一版(b38ad8cf,未併)Grid v0444:OK 275 · FAIL 12 · SKIP 5。重貼後 Grid v0445(292 站):**OK 280 · FAIL 7 · SKIP 5 · TIMEOUT 0**(274s;GRID_20260921_174322)——7 盞=Z92 一族殘餘 + 鉅亨(母線批690 的誠實燈把 12 收到 7);兩支新版站上 OK;VCGC v0123 廿九檢 29/29;元件冊 6170。再生件 stash 不 commit。

## 五 · 你的手

1. 拉 批692(PR #68 併了就是 main)後 `via-vrnrun`,貼 SUP_MDL746 / CGC_MDL141 兩格那行——這次應是 `[OK]`;不是就把整行貼回。
2. 其餘不變:Z114「登這四件」· Z109 三選一 · Z91 · Z82 · Z88 封存。

## 六 · 一貼即用

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
git merge --abort
git checkout -- "supportive modules/registry/VIA_VRN_LogicArchitecture_SSOT_v0100.json"
git checkout main; git pull origin main; git log --oneline -1
via-vrnrun
```
