# 批570:政策入冊 · 指令卡與凍結 · 資料涵蓋 · 畫面統一 · 撞號更正(2026-09-17)

## 一、政策入冊(操作員令「上面列入邏輯或政策」)

你貼的治理規格逐條收進政策庫,四條新律:

| 律 | 內容 |
|---|---|
| **L64 四階段治理流程** | 單元 → 整合 → **系統實測試跑** → 詳細報告;稽核通過才凍結且**留鉤子**;反碎片化合併成**大一統功能引擎**;無損精簡 |
| **L65 Token 撙節** | 嚴禁全檔傾倒 · 本機檔當外部記憶體 · 直奔重點 · 結果導向本機文字檔 · **AI 讀卡不讀原始碼** |
| **L66 凍結與鉤子** | 凍在哪一版(內容雜湊)+ 憑什麼凍(哪一輪測試)+ 哪些還可調(鉤子具名),**三件缺一不算凍結**;**解凍不由 AI 代行** |
| **L67 無損精簡** | 零功能損失;精簡後**必須重跑測試 100% 通過**才准凍結 |

## 二、指令卡與凍結冊 `via-cmdcard`(L65/L66 的實作)

AI 要知道 VIA 有哪些指令,現在唯一辦法是讀 **1,100 行**的短令冊,每接手一次付一次那個 token。

```
[token] 冊 39,232 → 卡 15,393 · 省 23,839(60.76%)
```

一行一指令:名稱 · 別名 · **背後引擎** · 鉤子 · 一句話。跑 `via-cmdcard cards` 會當場把帳印給你。

**凍結照 L66 三件齊**:`freeze --apply` **沒帶 `--evidence` 一律擋**;`verify` 重新雜湊每一支凍結指令,對不上就報 **DRIFT 並指名**;**沒有 `unfreeze` 動詞**。

## 三、VDF 資料涵蓋閘 `via-vdfcov`(三件合成一支大一統引擎;L64 階段三)

### `universe` — 你要的八個欄位逐欄判

| 欄位 | 狀態判定 | 缺了怎麼補 |
|---|---|---|
| Date / Ticker / Name | 在庫=GREEN | — |
| **YFinance Ticker** | 缺=NODATA | ticker + 上市 `.TW` / 上櫃 `.TWO`(**離線可推**,market 欄已在庫) |
| **Bloomberg Ticker** | 缺=NODATA | ticker + ` TT Equity`(**離線可推**) |
| **台灣產業分類** | 缺=NODATA | `tw_listings_industry` 連結 ticker(雙所官方冊) |
| **YFinance Sector** | 缺=**GATED** | yfinance 的 sector —— **要觸網**,不是缺件也不是壞掉 |
| **Industry** | 缺=**GATED** | 同上 |

主動式 ETF 名單同理(`yf_ticker` = `etf_ticker + .TW`)。

> 欄位比對**逐字**,不用裸子字串。第一版我寫 `"ticker" in "yf_ticker"` → 庫裡沒有 YFinance Ticker 卻判 GREEN,批558 那個假綠的翻版。

### `revenue` — 月營收涵蓋

逐表報最新月份與落後幾個月;落後兩個月以上=**STALE 誠實報**,不當成齊。

### `macro` — 總經 × akshare

16 項候選對照(中國 PMI/CPI/PPI/GDP/M2/進出口 · 美國 CPI/ISM PMI/非農/失業/GDP/利率 · 台灣 CPI/GDP/出口 · 原油),
每項底下列多個候選介面。

> **預設全部 UNVERIFIED**。這些介面名是候選,**不是我驗過的**(批562 的教訓:憑直覺挑的東西與實測零重疊)。
> 要算數就在裝了 akshare 的機器上跑 `via-vdfcov macro --probe` —— **我不代裝**。

## 四、U/I 畫面統一閘 `via-uiunify`

先量再定契約(65 張頁實測):零 CDN 只有 56/65 · **深色模式只有 7/65**。
一視同仁的話深色模式那條會讓 58 張頁全紅,而那不是你這一令的重點。所以**分三級**:

| 級別 | 項目 | 違反 |
|---|---|---|
| **LAW** | 零 CDN · 零彈窗 · charset · viewport · lang | **RED** |
| **UNIFY** | `:root` 主題令牌 · VIA 頁腳 · `<title>` | YELLOW |
| **ADVISORY** | 深色模式 | **永不判紅**(路線圖) |

**實測 106 張活頁:GREEN 43 · YELLOW 20 · RED 43** —— 多數 RED 是破了**零 CDN 這條既有律**,那是真缺失。
`plan` 會對每一張**指名該由哪一支引擎再生**。**不代改頁**:頁是引擎產的,手改下一次再生就被蓋掉。

## 五、撞號更正(我自己的債)

批568 我把 PEIS 掛線口取名 `CGC_MDL158`,而樹上**早就有** `CGC_MDL158_VIAPanoramaAuditRepair`;
批570 我又用 `CGC_MDL159` 撞了 `CGC_MDL159_VIAUnifiedConsole` 一次。**兩次都是取號之前沒掃樹。**

- 改號:`CGC_MDL161_PEISCapabilityEngine_v0102` · `CGC_MDL162_CommandCardFreeze_v0100`
- 舊件**退役不刪** → `functional modules/VIA_RetiredEngines/batch570_number_collision/`
- 守衛加在 `CGC_MDL157 v0104`(唯一性本來就是它的事):**同前綴同號不得兩個家族**,
  基線 ratchet 收既有的 `CGC_MDL142`(非本線造成,裁定權在你),超出基線報紅指名。

> 寫這道閘時我**又錯一次**:第一版用**裸號**當鍵,把 `VDF_ENG072` 與 `VRN_ENG072` 也算成撞號 ——
> 那是**刻意的並存命名空間**(元件冊裡就有 `coexisting_namespaces` 這個鍵),一掃 57 個假紅。
> 改成「前綴+號」才對。**尺量錯東西比沒有尺更糟。**

## 六、一貼即用

```powershell
git pull origin claude/via-envmanager-governance-7cls8h
. (Get-ChildItem 'Register-VIA-Commands-v*.ps1' | Sort-Object Name | Select-Object -Last 1).FullName

via-cmdcard                      # 一行一指令的卡 + token 帳
via-cmdcard freeze               # 凍結計畫(零寫)
via-cmdcard verify               # 凍結後被動過沒有

via-datahome catalog             # 先清點
via-vdfcov universe              # 兩張名單八個欄位逐欄判
via-vdfcov revenue               # 月營收停在哪個月
via-vdfcov macro                 # 總經 × akshare 候選(全 UNVERIFIED)
via-vdfcov macro --probe         # 裝了 akshare 才驗(我不代裝)

via-uiunify contract             # 三級契約
via-uiunify plan                 # 43 張 RED 逐張指名 owner 引擎
```

## 七、驗收

VCGC 20/20 · MDL156 30/30 · MDL157 **26/26**(+撞號閘)· MDL160 12/12 · MDL161 21/21 · MDL162 18/18
· ENG090 15/15 · DeckServer 25/25 · Manager 10/10 · 合約測 19/19 · PS 解析錯 0 · 短令零 ghost
