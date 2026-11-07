# VIA 標準視覺鎖定 U/I v0100(操作員 2026-11-07「本系統標準視覺鎖定U/I」)

操作員令:「視覺鎖定以下用此為格式 <https://viaatlas-39ozanmz.manus.space> ·
個股模板 <Claude Design: TW Stock Dashboard v2> · 本系統標準視覺鎖定 U/I」。

## 一、兩個連結讀不到,但正本倉內都有

| 操作員給的連結 | 本會話能不能讀 | 倉內正本 |
|---|---|---|
| `viaatlas-39ozanmz.manus.space` | **不能** —— 302 轉 `manus.im/app-auth`(OAuth 登入牆) | `review/VIA_Atlas_LocalSite_v0100/index.html`(2026-11-06 已位元組鎖定) |
| `claude.ai/design/p/…TW+Stock+Dashboard+v2` | **不能** —— Artifact 工具明確不支援 Claude Design 連結 | `functional modules/VAP/ASSETS/VIA_TW_Stock_Dashboard_standalone.html` |

所以**不靠外站也做得出來**:格式從 Atlas 正本抽,版面從個股模板撈。
外站只是展示;內容真相 = 倉內檔案(沿用 `VIA_Atlas_VisualLock_20261106.md` §1 的判定)。

## 二、鎖是「抽出來的」,不是手抄的

`VIA_VisualLock_v0100.py kit` 直接從鎖定正本的 `:root{}` 抽 `--vl-*` 宣告,算出 token 區塊 sha256。
**手抄會漂移,抽取不會** —— 正本改了,kit 跟著改,`check` 立刻看得出來。

本輪實測:位元組驗證 `sha256sum -c` **4/4 OK** · token **24** 個 · 區塊 sha256 `541574a7b42fcdacea441745b9c0d134f696ac9107a577241eafe833576e48e9`

| token | 值 |
|---|---|
| `--vl-bg` | `#f2f1ec` |
| `--vl-ink` | `#33403f` |
| `--vl-border-soft` | `#dcdad3` |
| `--vl-title` | `#1b1a17` |
| `--vl-muted` | `#6b6860` |
| `--vl-success` | `#3d7a52` |
| `--vl-white` | `#fff` |
| `--vl-border` | `#dbd9d3` |
| `--vl-row` | `#ebe9e3` |
| `--vl-success-bg` | `#e6efec` |
| `--vl-success-ink` | `#2c4f4a` |
| `--vl-warning-bg` | `#f2ecdd` |
| `--vl-warning-ink` | `#6f5c31` |
| `--vl-danger-bg` | `#f3e7e6` |
| `--vl-danger-ink` | `#9e2b25` |
| `--vl-font-cjk` | `"Microsoft JhengHei","Segoe UI",sans-serif` |
| `--vl-font-display` | `"Cormorant Garamond",Georgia,serif` |
| `--vl-font-mono` | `Consolas,monospace` |
| `--vl-size-title` | `19px` |
| `--vl-size-primary` | `11px` |
| `--vl-size-base` | `clamp(9.5px,1.05vw,11px)` |
| `--vl-size-numeric` | `9.5px` |
| `--vl-size-label` | `9px` |
| `--vl-size-status` | `8px` |

舊別名(`--bg` `--ink` `--line` `--teal` …)在正本裡是 `var(--vl-*)` 的轉接,不是另一套色;
新頁一律直接用 `--vl-*`。

## 三、鎖定閘(`check`)—— 這才讓它是「鎖」而不是一份文件

| # | 判定 | 紅的理由 |
|---|---|---|
| ① | token 區塊 sha 必須等於正本 | 改了一個色值就是另一套視覺,不是鎖定版 |
| ② | 色彩只准 `var(--vl-*)`,頁面不准寫死 hex / rgb / hsl | 寫死就繞過了鎖 |
| ③ | 0 外連(SVG 命名空間不算) | 鎖定律要離線單檔 |
| ④ | 手機側邊槽 `max(16px, env(safe-area-inset-left, 0px))` + 宣告 `overflow-x` | 手機會橫向捲動就不是同一個系統 |

自測實證三種違規都抓得到:寫死 `#ff0000` → 紅 · 外連 `cdn.example.com` → 紅 ·
把 `--vl-bg` 改成 `#ffffff` → 紅(「token 區塊和鎖定正本對不上」)。

## 四、個股頁:版面照模板,樣式用鎖定 kit,值只來自 VRN-2 自報

區段清單從 `VIA_TW_Stock_Dashboard_standalone.html` 的字串撈出來(不是我編的):
標頭 · 基本資料 · 評價分析表 · 年度 EPS/營收共識 · 分析師評級 · 年度損益表 · 比率分析 ·
族群指數比較 · 共振堆疊圖(7 卡共用同一時間索引 · 十字線貫穿 · 價格 K線/MA/EMA/BB(20) ·
成交量日均量 · 隨機指標(9)超買 80/超賣 20 · 三大法人四類堆疊 · 融資券)。

模板自己用的是另一套色盤(`--color-*` 冷灰藍 + Barlow),**本支不沿用它的色** ——
版面照它、樣式接 `--vl-*`,這樣兩頁才讀起來是同一個系統。

**誠實規矩(寫在每一頁上)**:值只來自 VRN-2 自己落庫的欄位;沒有的印「—」並標
`data-state="GRAY"`,區段標頭寫明缺什麼、為什麼。技術面 / 籌碼面要 VDF 日資料
(K線 · 量 · 三大法人 · 融資券),本機沒有就照實 GRAY ——
**絕不畫假 K 線、絕不編價格**。

本輪真資料實跑(容器 2026-11-07):

```
個股盤點 47 檔有料(庫 functional modules/VRN/db/vrn_reports.duckdb)
  1590 亞德客-KY 報告 3 · 券商 2 · 最新 2025-12-03
  3706 神達      報告 3 · 券商 3 · 最新 2025-11-30
  2637 慧洋-KY   報告 2 · 券商 2 · 最新 2026-09-15
出頁 3 張 · 全部過鎖定閘 GREEN · 燈 YELLOW(照實:basic / value / income / ratio / peer / stack
  是 GRAY,因為那些資料不在本機)· kit 4307 bytes
```

有料的區段真的有料:評級表逐列(報告日 · 券商 · 評級 · 方向 · 目標價 · ADJ · 上漲空間 ·
時效 · 分析師)· 目標價中位數由本頁現有筆數算(ADJ 優先,並在頁上寫明「是本庫內的中位數,
不是市場全體共識」)· 指標分到共識 / 損益 / 比率三區並照登原文。

## 五、怎麼跑

```bash
python3 "VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_VisualLock_v0100.py" tokens --via .   # 印 token + 驗位元組
python3 ".../VIA_VisualLock_v0100.py" kit --via .                       # 出 via_visual_lock_v0100.css
python3 ".../VIA_VisualLock_v0100.py" index --via .                     # 哪些 ticker 有料
python3 ".../VIA_VisualLock_v0100.py" stock --via . --ticker 3706,1590  # 出個股頁
python3 ".../VIA_VisualLock_v0100.py" check --via . --files <頁…>        # 鎖定閘
python3 ".../VIA_VisualLock_v0100.py" all --via . --top 3               # 一次跑完
python3 ".../VIA_VisualLock_v0100.py" --selftest                        # 19/19
```

輸出在 `<VIA>/VIA_Reports/visual_lock/`(不進 git):`via_visual_lock_v0100.css` ·
`stock_<代號>.html` · `VISUAL_LOCK.json`(收據)。

## 六、新頁要掛上這個鎖,三件事

1. `<link rel="stylesheet" href="via_visual_lock_v0100.css">` —— 不自己抄 token
2. 顏色一律 `var(--vl-*)`;要新顏色 → 改**鎖定正本**,不是改頁或改 kit
3. 出頁後跑 `check`;紅就不准當完成

## 七、照實沒做到的

- 操作員列的那 20+ 條 `C:\Users\tonyk\Downloads\*`:桌機未經 Remote Control 供出資料夾
  (`list_computer_folders` 回 `folders` 空),雲端讀不到。
- `NON_STOCK_CORE_v0400.zip`(操作員說 v0400 可取代 v0300):同上,要上傳才能接。
- 「持續監控 PS 跑完後自動擷取結果」:雲端會話看不到桌機的行程與輸出夾;
  要我直接做,需要供出資料夾。桌機端的自動擷取可由 `VIA_DesktopFourBlocks_v0100.py`
  的收據夾 + zip 貼回包達成(已在 main)。
