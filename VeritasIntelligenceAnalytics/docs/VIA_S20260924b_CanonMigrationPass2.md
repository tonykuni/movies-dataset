# VIA 側線 2026-09-24 第二段 · 期別正典第二回遷移(操作員令「繼續完成」)

> 主線批號由併線的手指定(L25)。上一段 = `docs/VIA_S20260924_SourceEnginePanorama.md`(五組擷取引擎全景三回,已由 PR #98 併進 main)。
> 本段只做「一次解不掉、要依序」清單裡**不需要操作員許可、也不需要操作員裁定**的部分;需要的,寫成提案放在第五節。

## 一 · 一句話

上一段立了期別正典(哪一欄是日期、民國怎麼換、月/季表怎麼算落後),本段把私有的份一支支遷過去。
遷之前先量,結果每一處都比冊上寫的多:日期欄清單是**九份**(冊上寫兩份),ENG055 的民國換算是**六處**(冊上寫兩份)。
另外量到一個會讓價格被截成整數的舊洞(ENG054 空跑哨兵),一起修掉。

## 二 · 量到的(全部是實量,附量法)

| # | 量到什麼 | 怎麼量 | 冊上原本寫 |
|---|---|---|---|
| 1 | VDF/VIA 碼裡「哪一欄是日期」的私有清單**九份**:MDL123 · MDL139 · ENG073 · MDL148 · ENG089 · ENG087 · ENG090 · MDL119 · MDL128(另七類範圍外,附因由) | AST 掃尾版 2025 支:字串常值 tuple/list/set 過半是日期欄名;第一回 ≥3 名、第二回 ≥2 名 | 兩份 |
| 2 | ENG055 一支民國/緊湊日期換算**六處**:`_iso_date` · `_roc_to_iso` 兩個 def + L12 當沖市場級 · L15 當沖逐股 openapi 與 rwd 三處內嵌 + L10 CBC 年月 | 逐行讀 `1911` 與 `len(ds)` 判斷 | 兩份 |
| 3 | 全樹尾版含 `1911 +` / `+ 1911` 算式:**70 支**(除 references/intake 61;再除退役/封存 41) | git ls-files 同族取尾版,原始碼比對 | 81 支(第一段的算法沒留下,重量不出來;以本次方法為準) |
| 4 | **ENG054 空跑哨兵會讓新庫的價被截成整數**:一輪 0 列時寫的 `_NOOP_` 列除 date/ticker 全是 None,若表還不存在,就是這一列建表 → open…volume 推成 INTEGER → 之後 1050.5 存成 1050;量 5.1e9 整批寫不進去 | duckdb 1.5.5 + pandas 3.0.6 容器實測,自測 ⑫ 負控重現 | 冊上只記「最早日變 1900」 |
| 5 | 正典 v0105 的 `roc_to_iso` 不認八碼 19xx:`_iso_date('19991231')` 給 1999-12-31,正典回 None——v0105 ㉖「零差異」的語料裡沒有 19xx | 補語料重跑 | 「零差異」 |
| 6 | 格子站名的檢數九站過時(例:總擷取執行器寫八檢,引擎 v0111 起就是十檢) | 逐支 `--selftest` 實數 | — |
| 7 | 焦點九支「例外被吞」22 處:20 處是退路(編碼逐一試 · 關連線 · 開瀏覽器 · 可選欄位);**2 處會把事情蓋掉**:ENG055 當沖收容冊寫不進(下輪重收;upsert 有鍵不重列)· ENG073 單表 MIN/MAX 查詢失敗(該表範圍空白、不說原因) | 全景讀卡 `[報] SWALLOW` 逐處看上下文 | — |
| 8 | 介面合約 MDL054 對月營收項報 PARAM_DRIFT(codes→--ticker/--tickers):ENG063 的代碼本來就是位置參數,主控台組的 argv(`run 2330 2317`)也對——是合約尺錯;v0105 起每次都報 | 同一冊項分別對 v0105 / v0106 尾版跑 `sync_item` | — |
| 9 | 一鍵鏈沒排的六支(ENG056 籌碼 · ENG057 成交值 · ENG055 全車道 · ENG060/061 衍生 · ENG059 估計)**每天都在開機鏈 `via_boot_update` 跑** | 讀 via_boot_update.sh / .ps1 | Z161「只在開機鏈」 |

## 三 · 改了什麼(全是新版檔;舊版零觸碰,留作版史 L04)

| 檔 | 版 | 為什麼 | 自測 |
|---|---|---|---|
| `supportive modules/registry/VIA_SSOT_PeriodRules_v0100.json`(冊,就地) | — | 補普查 `date_columns.census`(九份逐檔:行 + 七類範圍外因由)· corrected 尾端補六欄(portfolio_date 讓 ETF 持股兩表第一次量得到新鮮度)· record_only 補 snapshot_at / run_at(ENG051 寫 `datetime.now()`)· fallback_rule · value_shapes 立 ROC_YM · roc_date_2 重量 · 帳 +3 | 正典 ㉞ 讀冊驗 |
| `supportive modules/SUP_MDL753_VIACommonUtils_v0106.py` | v0105→v0106 | +`fallback_date_columns(own)`(補位差集收回正典,讀者不自己做)· `roc_to_iso` 八碼放寬到 19xx · +`roc_to_iso_keep`(認不出=原值,ENG055 `_iso_date` 語意)· +`roc_ym`(民國年月,實作逐字取自 ENG063) | 36/36(+㉞㉟㊱;㉖ 語料 30→39 式) |
| `supportive modules/registry/CGC_MDL139_InputConsole_v0111.py` | v0110→v0111 | 主控台 status 滯後改讀正典:日期欄先認自己那份、認不到才補位;月/季表 PERIOD_DUE、凍結表不算天;**架構冊快照列在讀的當下重算**(v0110 直接搬 09-15 建冊那天的滯後,冊越舊越顯得新鮮),建冊那天的值留 `lag_days_at_stamp`;右矩陣 +「滯後態」欄 | 19/19(+⑲) |
| `functional modules/VDF/engine/VDF_ENG073_DataArchitecture_v0101.py` | v0100→v0101 | 架構冊盤點補位 + 滯後讀正典;冊上 engine 欄記真的檔名(原寫死 v0100) | 10/10(+⑩) |
| `functional modules/VDF/engine/VDF_ENG055_OmniFetch_v0113.py` | v0112→v0113 | 六處民國/緊湊日期全綁正典(`_iso_date = roc_to_iso_keep` · `_roc_to_iso = roc_to_iso` 綁定不是 def;三處內嵌改呼叫綁定;L10 改呼叫 `roc_ym`) | 11/11(+⑪) |
| `functional modules/VDF/engine/VDF_ENG063_MonthlyRevenue_v0106.py` | v0105→v0106 | `_roc_ym = roc_ym`(MOPS「資料年月」) | 10/10(+⑨b) |
| `functional modules/VDF/engine/VDF_ENG054_TWDailyBackfill_v0106.py` | v0105→v0106 | 日價表欄型寫明(價/量 DOUBLE);表不在才建空表、在=零觸碰;空跑不寫哨兵;`--status` 多印一行欄型(整數型標 ⚠) | 12/12(+⑫) |
| `supportive modules/registry/CGC_MDL064_SelftestGrid_v0479.py` | v0478→v0479 | 只改九站站名的檢數;別的尺拿站名當鑰匙的字一個不動(MDL133 數「(批376)」· 「月營收分析」· MDL131「擷取/回補/月營收」) | `--only` 11 站:OK 10 · SKIP 1(狀況頁:容器沒有目錄=環境缺) |
| `supportive modules/ui_support/VIA_UI_MasterControl_v0100.html` | 再生(LL49 准提交的那一頁) | 總控頁的模組說明取自各尾版文件第一行;格子 v0479 等新尾版的說明變了,契約測 ⑪「提交頁 = 產生器輸出」要求同步(本機儀表板先移開再生,Plotly 面板照舊是空狀態) | 契約 19/19 |
| 元件冊 · 正則清冊 · 帳 · 掉球 | 就地 | VCGC registry-sync 重掃 · CGC_MDL115 重建 · 帳 +1 · Z161–Z167 更新、Z168–Z171 新開 | — |

## 四 · 怎麼證明(每一檢都有負控或變種)

| 檢 | 正向 | 負控 / 變種(改壞一處,檢要紅) |
|---|---|---|
| 正典 ㉞ | 九份每一欄都在 corrected ∪ record_only;補位不含時間戳;與 MDL123 v0104 自算差集逐欄相同;ENG051 fetch_status(照建表欄序)補到 portfolio_date 不是 run_at | 冊上塞假欄 bogus_col 抓得到;把 snapshot_at 塞進 corrected 照樣不補;變種「不跳 record_only」「不跳自己那份」「自己那份大小寫敏感」三支全紅 |
| 正典 ㉟ | roc_to_iso_keep 對 ENG055 `_iso_date` 逐式四類:同答 20 · 正規化 11(另一份舊版給過的同一日期)· 拒不存在的日期 3(回原值)· 具名刻意不同 4;類外 0 | 變種「八碼退回只認 20xx」「直通不去空白」「七碼不驗日期」全紅 |
| 正典 ㊱ | roc_ym 對 ENG063 原實作逐式零差異(19 式);對 ENG055 L10 內嵌在有效輸入上同答 | 舊內嵌造出 2026-13-01 的式子正典回 None;變種「拿掉年份範圍」紅;刻意不同 1 式具名(民國 80 年前;CBC 表實際從民國 90 年起,現役資料零影響) |
| MDL139 ⑲ | 月營收 202608=PERIOD_DUE 0 · 財報 6/30=0(期限 11/14)· 日頻 3 日同 v0110 · 凍結不算天;快照列 3 → 12;實庫 status 一輪同判 | canon=None 照 v0110(月 None · 財報 86 · 快照 3 · 補位不給);變種四支全紅 |
| ENG073 ⑩ | 月營收補到 ym · ETF 持股補到 portfolio_date · 只有 snapshot_at 的表不補 · 頁印期限/凍結 | canon=None 照 v0100;變種四支全紅 |
| ENG055 ⑪ | L12 民國七碼與七字元斜線皆成 ISO · L15 openapi 七碼與 rwd 八碼皆成 ISO · 1151301 原樣回 · 五條車道原始碼零民國加法 · 自測收容夾換空夾 | 變種「L12 舊內嵌」「_iso_date 回 def」「L15 rwd 舊寫法」「收容夾不換」全紅 |
| ENG054 ⑫ | 新庫價/量 DOUBLE、建的是空表、第二次零觸碰;1050.5 · 5.1e9 保留;`--status` 欄型行 OK | 照 v0105 空跑先寫哨兵建表 → INTEGER、1050→截、5.1e9 寫不進、欄型行標 ⚠;變種四支全紅 |

另跑:VIA_LibCanon 7/7 · MDL123 v0104 14/14 · ENG093 v0103 13/13(新正典下不變)· VRN_ENG070 9/9 · VRN_ENG071 10/10 · python 3.12(本容器這一境沒有 duckdb / pandas):正典 36/36、主控台 19/19 照過;四支 VDF 引擎自測一開頭就要 duckdb / pandas,在這一境停在 import——舊版(ENG055 v0112 · ENG063 v0105 · ENG054 v0105 · ENG073 v0100)一模一樣,以 3.11 為準 · 全景讀卡七支新版與前一版問題數逐類相同(沒有新增)· 本機 CI 鏡像(管理器 · 牌卡 · 同步 · 儀表板 · 契約 · UAT)。

## 五 · 沒做的,為什麼

**Z161 一鍵鏈補步——不動 Python 半邊,改提案。** 量到那六支每天都在開機鏈跑。把它們一支支抄進 CGC_MDL125 步冊,
同一條日更序列就長出第二份(九頭龍),而且 FixAll / MDL134 不帶 `--only` 時會連帶多跑——「先動 Python 半邊」會改掉 FixAll 的預設行為,不是無害的準備。
建議改成**一步委派**:

- CGC_MDL125 新版加一步 `daily_chain`(呼叫開機鏈,不抄清單);MDL134 鏈冊掛在 `hist_2023` · `revenue_backfill` · `consensus` 之後。
- `Invoke-VIA-VdfFetch` 新版(**要你逐支許可 L70**)`$stepBook` 尾端加 `,daily_chain`;v0107 那一行是
  `$stepBook = "datahome,hist_2023,global,fred,revenue_backfill,etf_universe,etf_fetch,etf_history,consensus,revenue_consensus,etf_revenue"`。
- 要你裁的一件:開機鏈有「當日已跑」記號(`.last_boot_update`),一鍵鏈當天再按一次時,這一步要**照記號跳過(誠實 SKIP)**還是**強跑**。

**Z162 剩六支日期欄清單**:MDL148 普查算的是跨度不是滯後,月/季表的跨度要用期數算,正典還沒有這條規則;ENG089 缺口是日頻語意,期別缺口要另立規則;
ENG087 · ENG090 · MDL119 · MDL128 各一版(MDL128 另有跨表字串比大小,緊湊八碼會贏過 ISO)。先立規則再遷,不在本段硬塞。

**Z163 其餘 41 支**:照帳逐支,語料零差異才准。ENG075 是反方向(西元→民國組 MOPS 網址),不是同一件事;ENG051 不在焦點。

**例外被吞的 2 處**:記在 Z167 結案說明,本段不改(一處要改寫收容冊的行為,一處要在架構冊加欄,都不是順手的事)。

**MDL054 假漂移(Z171)**:是中央線合約尺的規則,不在本側線改。

## 六 · 工作站要做的(依序)

1. 先照 `docs/VIA_B729_TheSmallPrintAndTheAdjustedClose.md` §九 / §十一 把工作站從卡住的分支解下來,拉到最新 main。
2. `via-price --status`(唯讀、不觸網)→ 看最後一行「tw_daily_prices 欄型」:`OK` = 沒事;標 ⚠ = 貼回給我(Z168)。
3. 照常跑一鍵指令,看資料庫狀況頁;主控台 `via-console status` 的「更新到哪一天」:月/季表帶期限、凍結表印「凍結」、快照列標「(快照)」。
4. 要驗真回包(容器被 TWSE/MOPS 防火牆擋):你開同意閘後照 Z170 那三行各跑一次,輸出貼回。

## 七 · 還原

程式檔全是新版,刪掉新版檔(或 `git revert` 本段提交)尾版就回到上一版;冊(期別規則 · 元件冊 · 正則清冊 · 帳 · 掉球)與總控頁是就地改的,`git revert` 即回。沒有動任何 `.ps1`。
