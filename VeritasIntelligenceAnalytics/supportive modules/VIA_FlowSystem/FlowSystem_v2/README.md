# VIA-FlowSystem · 全球 ETF 資金流向與強度 — 自我驗證系統

把前面所有方法論固化成一個**會自我證明**的可運行系統:參數/資料走 JSON,引擎+測試+系統管理走 PY,一支 PowerShell 啟動並同步前後端 HTML。

## 一鍵啟動
```powershell
.\Activate-VIAFlowSystem.ps1                 # 預設 cmd=all:synth→calibrate→run→ui→開 HTML
.\Activate-VIAFlowSystem.ps1 -Cmd calibrate  # 只跑校準迴圈
.\Activate-VIAFlowSystem.ps1 -PythonExe C:\Users\tonyk\envs\via_plot_basic\Scripts\python.exe
.\Activate-VIAFlowSystem.ps1 -NoOpen         # 不自動開瀏覽器
```
PowerShell 會自動定位 venv(Auto-Locator 掃 `C:\Users\tonyk\envs\`),以 `ProcessStartInfo + ArgumentList.Add` 非同步雙流抽乾跑後端,讀 `calibration.json` 印出 VALID/NOT_VALID,再 `Start-Process` 開 `index.html`。

## 直接用 Python(等效)
```bash
python engines/flow_manager.py all          # 或 synth | calibrate | run | ui
```

## 結構
```
config/
  params.json      # FIS 參數、驗證 gate 門檻、校準 grid、synthetic 設定
  universe.json    # 30 檔 ETF:asset_class/risk_bucket/backing/monitor_role/fidelity
data/
  input/daily_data.json    # 運行/測試資料(JSON);無 live 餵入時由 synth 產生
  output/calibration.json  # 校準迴圈結果 + 驗證報告 + 最佳參數
  output/snapshot.json     # 最新快照:per-ticker FIS、bucket、RORO
  state/run_ledger.jsonl   # append-only 執行紀錄
engines/
  flow_core.py     # FIS 強度 + 雙估計器信任 + 聚合(VDF-FLOW-CORE-11)
  flow_validate.py # IC/decay/quantile/long-short/null + gate 評估(VALIDATE-12)
  flow_calibrate.py# optimize→test→debug→backtest→calibrate 迴圈(CALIBRATE-13)
  flow_ui.py       # 由 JSON 產 Visual Lock index.html(UI-14)
  flow_manager.py  # 系統管理/編排 + synth + CLI(MANAGER-15)
Activate-VIAFlowSystem.ps1  # 單一啟動器(LAUNCHER-16)
index.html        # 前端(生成):驗證徽章 + RORO 單針 + 類別/bucket FIS + per-ETF 表
```

## 校準迴圈如何「證明有效」
1. 依 `train_frac` 切 train/OOS
2. 掃 grid(window × kappa × min_tier),每組:`compute_fis` → `evaluate`(train gates)
3. **DEBUG**:任何組失敗只記錄原因不中斷;記每組卡在哪些 gate
4. 取 train 通過且 objective(ICIR)最高者為 best
5. **OOS 確認**:best 在測試段必須同號且顯著(G009)
6. 全綠 → `PROVED_VALID`(寫入 `calibrated_params`,run 自動採用);否則 `NOT_VALID` 並列出最常失敗的 gate

## 反證保證(這是可信度的地基)
把 `params.json` 的 `synthetic.alpha` 設 0(無 flow→return 結構),系統**必須**回 `NOT_VALID`。實測:0/24 組通過,`G003_icir` 全數失敗。系統在沒訊號時報「沒訊號」,不是橡皮圖章。

## 接真實資料
把 `fetch_global_etf_tracker_v4` 的輸出寫成 `data/input/daily_data.json`(欄位:`snapshot_date, ticker, close, shares_out, aum_reported`),其餘不變。`aum_reported` 提供時自動啟用雙估計器交叉驗證(防 shares 陳舊/申贖假象)。Pillar A(對 ETF.com/COT 真值校準)仍需先接官方流量源。

## Gate 對照
G002 null · G003 IC/ICIR/t · G004 quantile 單調 · G008 LS Sharpe(扣成本)· G009 OOS 確認。
(完整 G001~G021 見 FMEA / Validation Charter。)

---

## v0103 — SOLID 三層驗證(本輪新增)

系統現在要**三層獨立驗證全綠**才算 `SOLID`,任何一層紅 → `NOT_SOLID`:

| 層 | 問題 | 引擎 | Gate |
|---|---|---|---|
| **Pillar A 測量** | 估的流量是真的嗎? | `flow_pillar_a.py` (PILLARA-19) | VAL-G001(對真值的 rank-corr/符號/回歸/lead-lag) |
| **Pillar B 效力** | 能預測未來嗎? | `flow_validate`+`flow_calibrate` | G002~G009 |
| **self-test** | 引擎在邊界情況穩嗎? | `flow_selftest.py` (SELFTEST-20) | 14 項邊界測試 |

新命令:
```bash
python engines/flow_manager.py selftest      # 14 項邊界測試
python engines/flow_manager.py validate-a     # Pillar A 測量校準(需 reference_flows.json)
python engines/flow_manager.py all            # 全鏈:synth→selftest→calibrate→factors→run→validate-a→status→ui
python engines/flow_manager.py live           # 同上但用 bridge 吃真實資料
```
`all`/`live` 末端輸出 `data/output/status.json` 與 UI 頂端的三層狀態橫幅。

### Pillar A 真值來源(上線需接)
`validate-a` 讀 `data/input/reference_flows.json`(schema:`{records:[{snapshot_date,ticker,ref_flow}]}`)。真實上線時由以下免費真值供應:
- **ICI** 週度美國基金流(aggregate)· **issuer/NAV** 每日 AUM(per-ETF)· **CFTC COT** 期貨/FX 持倉(futures-backed 的真值)· **AkShare** 中國申贖
沒有 reference 時 `validate-a` 回 `UNCALIBRATED`,系統狀態自動降為 `NOT_SOLID` 並標「signal indicative only」——不會假裝校準過。

### self-test 涵蓋
正常/單檔/短歷史 FIS、sub-floor AUM 降級、stale-shares CONFLICT、role-gated 聚合、RORO、snapshot、validate、null≈0、factor 剔除 noise、Pillar A good-pass/bad-catch、空輸入安全。

---

## v0104 — 多分頁儀表板(本輪新增)

UI 改為三分頁(`flow_grid.py` / `VDF-FLOW-GRID-22` 從 live snapshot 算出網格資料):
1. **Flow & Validation** — 系統狀態、驗證 verdict、RORO 單針、類別/bucket FIS、因子庫、per-ETF(含 composite)。
2. **Region × Sector** — 全球股票輪動熱圖(7 區 × 11 GICS sector)。US 列為 direct(XL* 直接讀),其餘列為 proxy = 區域錨點 baseline × US-sector tilt;TW 紅=流入綠=流出;proxy cell 標記。
3. **Fidelity** — ETF 流量監控可信度評分卡(10 類):每類中位 fidelity、主要 backing/role、live FIS、建議用法、免費三角驗證來源。weak/blind 類(FX/Vol/futures 商品)明確標示需非 ETF 真值佐證。

新命令 `grid`,已串進 `all`/`live`。`grid.json` 為輸出。

---

## v0105 — 四階風險分層 + GRAM(整合外部宏觀框架)

吸收「全球宏觀資金水表」框架的可用部分,按 add-only 併入:
- **4-tier 風險分層**(universe `risk_tier`):Tier1 主權/現金/黃金 → Tier2 防禦/IG/長債 → Tier3 景氣循環 → Tier4 高Beta投機。70 檔全分層(T1=9/T2=15/T3=22/T4=24)。新增 BNDX/IEV/GREK/AAXJ/SMH。
- **GRAM(Global Risk Appetite Momentum)** `flow_core.gram()`,雙形並陳:
  - **標準化版(嚴謹)**:`gram_score = 100·tanh((T3+T4 − T1−T2)/2 / κ)`,用 AUM 加權 tier FIS,尺度不變、有界。
  - **原始版(文件公式)**:`gram_raw = net$(T3+T4 − T1−T2) / 總監控池`,±0.05 → RISK_ON / RISK_OFF / NEUTRAL。
  - 兩者都**尊重 monitor_role 閘門**(期貨/FX positioning 不進現貨流量池)——比原文件直接相加異質美元流量更穩。
- UI Flow 分頁新增 **Risk-Tier Ladder + GRAM** 卡(四階 bar + regime 徽章 + score/raw)。

說明:原文件的「三大水表」中,ETF 申贖水表=我們的 FIS 核心(已實作);CFTC COT=Pillar A 真值源之一(待接);TIC/SWIFT=主權層,目前未納入(per-ETF 系統外)。

---

## v0106 — 世界地圖動態資金流動畫(本輪新增)

`flow_worldmap.py`(`VDF-FLOW-WORLDMAP-23`)生成**自含離線** Plotly 世界地圖動畫:
- 世界輪廓由快取 GeoJSON 以 Scatter 線繪製(不依賴 CDN topojson,完全離線)。
- 10 個區域節點(US Equity/Cash、Gold、JPY、Europe、China、Taiwan、Korea、India、EM LatAm),顏色=FIS(紅流入/綠流出)、大小=|流量|、標籤即時更新。
- 區域間資金流弧線(width/colour/opacity = 流量強度與方向),risk-on 從避險→風險(紅),risk-off 反向回流(綠)。
- 19 時點情境時間軸(Risk-On→高峰→地緣衝擊→Risk-Off→美元擠壓→企穩→復甦),▶ 播放 / 滑桿步進,標題 + GRAM/regime 標示隨幀更新。

命令 `worldmap`,已串進 `all`/`live`;launcher 會同時開 `index.html` 與 `world_flow.html`。plotly 未安裝時優雅跳過不中斷。

---

## v0107 — 各風險類別資金流動 動態階梯(本輪新增)

`flow_worldmap.build_tierflow()` 生成第二張離線 Plotly 動畫 `tier_flow.html`,與世界地圖同一條情境時間軸,呈現風險維度的資金遷移:
- 四階階梯(T1 主權/現金 底 → T4 高Beta投機 頂),節點顏色=tier FIS(紅流入/綠流出)、大小=|流量|、標籤即時數值。
- 左側遷移箭頭:Risk-On 紅色向上(資金爬升追逐風險)、Risk-Off 綠色向下(下滑逃向安全),寬度=風險偏好強度。
- ▶ 播放/滑桿,GRAM/regime 標示隨幀更新。

`worldmap` 命令現在一次產出兩張(world_flow.html + tier_flow.html);launcher 三張一起開(儀表板+全球地圖+風險階梯)。

---

## v0108 — 動態圖改為「真實每日資料驅動」+ 地圖放大

`flow_worldmap` 的兩張動畫不再用情境推演,改讀系統的**真實每日 FIS panel**:
- `cmd_worldmap` 先 `compute_fis` 整個 daily panel(用校準後參數),再按 **region / risk_tier** 每日 AUM 加權聚合(flow_roles 閘門),取最近 ~150 日取樣成 26 幀。
- 每幀 = 一個真實日期;節點/階梯顏色與大小 = 當日真實 FIS(由各 ETF 價格波動×AUM 波動×淨現金流推導),GRAM 為當日真實 tier 梯度;標題顯示日期。
- 世界地圖**放大**(height 780、緯度聚焦 −40~74、節點/標籤加大、CJK 區域名),`build_*` 接 `(df, ap)` 走真實資料、不帶則回退情境 demo。
- 修了 date-key 型別不符的 bug(sample 回傳 date 物件、index 以 str 為鍵 → 查無 → 空圖),統一以 `str(date)` 對齊。

接真實資料:bridge 餵入 TWSE/yfinance 每日價量股數後,兩張動畫即become真實歷史回放。

---

## v0109 — 20 失效模式硬化全實作(本輪)

把上一輪列的 20 個潛在邏輯/系統錯誤轉成系統內可運行、可測試的解法。selftest 14/14 · autotest **19/19**(新增 5 個硬化驗證測試)· SYSTEM SOLID · PROVED_VALID。

**已實作並測試(✅):**
- #1 公司行動/分割守衛:`compute_fis` 偵測 (1+Δshares%)·(1+ret)≈1 的分割簽名→該日 d_shares 歸零 + `corp_action` 旗標。測試 `harden_split_guard`。
- #7 新生/清算排除:每檔前 `inception_buffer`(20)列強制 confidence D,不進 A/B 聚合。測試 `harden_inception_excl`。
- #11 Newey-West HAC t 值:`daily_ic` 加 HAC 自相關校正 t(實測 13.8→7.8,誠實降低),新增 gate `G011_thac`。
- #13 tanh 飽和:per-ticker snapshot 暴露原始 `z`(flow_z),尾部資訊不流失。
- #14 AUM 權重上限:`bucket_fis` 加 `weight_cap`(0.25),單檔 ETF 權重封頂,巨型 ETF 不主宰。測試 `harden_weight_cap`。
- #15 反身性/內生性:`evaluate` 加 contemporaneous IC vs 預測 IC 分解,`lead_ratio`(實測 0.66,訊號確實領先非機械同期),新增 gate `G010_lead`。
- #20 分類敏感度:autotest 擾動 taxonomy 標籤,檢查聚合仍有限穩定。測試 `harden_taxonomy_sens`。
- (既有已硬化)#2 雙估計器 stale-shares、#8 NaN/Inf 消毒、#9 look-ahead shift、#12 K=15 排列 null、#16 falsifiability、#18 fidelity 閘門。

**輕量補強(◐):**
- #5 幣別:universe 加 `currency`,snapshot `non_usd_n` 標記非美計價曝險。
- #10 市場體制:snapshot `regime`(flow_stress 廣度 → CALM/ELEVATED/STRESSED)。
- #19 地理語意:snapshot `region_semantics="exposure_not_origin"`,UI 明標「region=曝險非來源」。

**真資料路線圖(⚠️,容器外):**
- #3 AP 套利/heartbeat 過濾、#4 多重上市去重、#6 時區/NAV 對齊、#17 wrapper 替代三角驗證(需 CFTC COT/issuer 真值,接 bridge 後啟用)。

UI 新增硬化條與 `tHAC`/`lead` 指標;`harden` 命令現跑 19 測試。

---

## v0110 — 響應式設計(RWD,PC + 手機自動適配)

- 儀表板 `index.html`:fluid type(`clamp()` 標題/數字)、`.row` 兩欄在 ≤760px 收為單欄、tabs 可橫向捲動、表格在窄屏 `min-width` + 卡片 `overflow-x:auto` 橫捲、Tier+GRAM 卡在手機改直向堆疊(`flexcol-m`/`noborder-m`)、≤460px 再縮字級與內距。實測 390px 無水平溢出(scrollWidth=innerWidth=390)。
- Plotly 動畫/累積圖:`config.responsive=true` + `default_width="100%"`,寬度隨容器自適應(手機 390px 下圖寬 374px 正常)。
- 模擬終端 `via_flowsim.html`:既有 820px 斷點(grid 收單欄)保留。

---

## v0111 — 全球資金流動 情境模擬(互動動態,本輪)

`flow_worldmap.build_map_sim()` 生成 `global_map_sim.html`:自含 SVG 世界地圖(內嵌輪廓,離線、151KB、不依賴 Plotly)。互動式情境驅動——
- 8 個情境鈕 + 4 條因子滑桿(RISK/USD/INFL/GEO),改任一即時重算 10 區域節點 FIS 與弧線。
- 弧線 `stroke-dashoffset` CSS 動畫 = 資金流向脈衝;Risk-On 避險→風險(紅),Risk-Off 反向回流(綠)。
- 「▶ 播放情境過渡」用 requestAnimationFrame 在 1.4s 內 ease 插值因子,看資金平滑遷移;GRAM/美元體制即時更新。
- RWD:控制列 ≤680px 收 2 欄,SVG width:100% 自適應,390px 無溢出。

已串進 `worldmap` 命令(scenario-driven,免 df);launcher 一併開啟。

---

## v0112 — 情境模擬重做為「時間軸 + 方向 + 累積」(本輪)

`global_map_sim.html` 重寫,解決「看不到資金方向/隨時間變化/區間累積」:
- **方向明確**:弧線加 SVG 箭頭(marker-end)+ 沿路徑移動的資金顆粒(getPointAtLength),顆粒移動方向 = 資金流向,風險偏好翻轉時箭頭與顏色同步反向。
- **強度 × 時間**:84 步情境時間軸(7 keyframes 插值,代表 180 天),▶播放/滑桿/速度,節點顏色大小與弧線粗細逐步變化,顯示相位(Risk-On→地緣衝擊→Risk-Off→…→復甦)與 GRAM。
- **區間累積**:每步算各區域淨流 $B proxy(FIS/100×AUM×dt),prefix-sum 支援 O(1) 任意視窗累積;節點顯示累積環圈 + 數值,右側「區間累積淨流」排行榜紅/綠長條;「⚑設此刻為累積起點」可選任意期間。
- 揭示瞬時 vs 累積差異:當下 Risk-Off 但 0–90 天累積仍由先前 Risk-On 主導。
- RWD:map+panel ≤860px 收單欄,390px 無溢出。

---

## v0113 — 三維合一 + 縮小箭頭 + 自動結論

`global_map_sim.html` 升級:
- **三維合一 UI**:頂部 區域 / 風險分類 / 類型分類 切換鈕,共用時間軸/粒子/累積/結論。區域=地理地圖(10 節點);風險分類=T1→T4 上升階梯;類型分類=8 資產類別弧形(股/債/現金/商品/黃金/加密/地產/外匯)。切到 tier/type 自動隱藏世界地圖。
- **箭頭縮小**(markerWidth 6→3.4)更專業;弧線寬度上限 8→5、粒子變小。
- **📌 自動結論面板**:每一時點自動產生中文結論——當前天數/regime/GRAM、瞬時最大流入與流出標的及 FIS、整體強度(強/中等/弱)、本期間累積最大贏家與輸家($B),並標示「瞬時 vs 累積方向是否一致」。使用者直接讀結論即可,不必自己判讀。

---

## v0115 — 模擬架構標準化 + 新變數「評價」+ 失效模式解法

**架構標準化(與系統一致):** 模擬參數移到 `config/sim.json`(因子/情境關鍵幀/三維節點載荷/AUM/評價參數/門檻),引擎 `engines/flow_sim.py`,由 `flow_manager.py` 的 `sim` 命令維護並串進 `all`/`live`,PowerShell launcher 啟動開啟,HTML UI 由引擎注入同步。

**新變數 評價(Value):** `V=(預期報酬 ER − λ·風險)/估值成本`;成本隨「區間累積流入」上升(反身性:錢湧入→變貴)。Vscore 0–100(越高越划算)。UI 新增「資金流/評價」模式切換,節點與排行榜並陳 FIS 與評價。揭示反身性洞察:錢狂湧的標的評價轉差(美債/現金 +360B 但評價1),錢流出的反而便宜(中國 −273B 評價80)。

**失效模式解法(上一輪 20 條的可實作部分):**
- FM#1/#2 載荷用假設 → `ground_loadings()` 從真實 FIS panel 回歸(group FIS vs 實現 RORO 風險因子)估計 RISK 載荷、向先驗收縮;UI 標示「載荷來源:estimated/prior」。
- FM#12 無不確定性 → 累積數字標 ±18% 不確定區間。
- FM#13/#20 → 明標「情境推演非預測」+ 載荷來源。

**起訖時間區間:** 雙滑桿(累積起點 + 累積訖/游標)可選任意區間,顯示起訖天數;播放推進訖點。

**自動結論回答三問 + 有效性:** 🌍流向哪地區 📊哪風險層 🏷️哪類型,各附評價(划算/中性/偏貴),末行給有效性判斷(資金是否流入評價偏貴標的→追高存疑 / 流入評價尚可→健康)。

測試:selftest 14/14 · autotest **21/21**(新增 sim_engine_build、sim_loading_grounding)· SOLID。

---

## v0116 — 模擬 UI 打磨

- **雙向發散長條圖**:排行榜改為中線分隔,正數(淨流入)紅色向左、負數(淨流出)綠色向右;標題加圖例「← 紅 淨流入 ｜ 綠 淨流出 →」。
- **分類說明**:每維度底部加說明列(類型分類:股票=全球股市、債券=投資級/主權債、現金=短債、大宗商品=原油/工業金屬、黃金、加密、地產=REIT、外匯=美元指數;風險分類 T1–T4 與區域同理)。
- **中國/歐洲等節點釐清**:標籤加註(中國(新興)、歐洲(成熟)、黃金(避險)),黃金挪到中大西洋避開歐洲重疊,日韓挪開;每個節點加 hover 提示(全名+說明+FIS+累積+評價)。

---

## v0118 — 正規化走勢圖 + 主題(故事性)分類

`config/perf.json` + `engines/flow_perf.py` + manager `perf` 命令 + PS 啟動,生成 `perf_trend.html`:
- **內容**:S&P 500 + ^TWII + 全 11 個 GICS 產業 ETF + 台股指標個股,**正規化 adj-close(基準=100)**;基準日預設 2025-01-02,**瀏覽器內可調**(下拉選日期即時重算)。
- **主題故事分類(本輪重點)**:採納「主題比 GICS 更貼近資金敘事」——新增 12 檔美股主題 ETF(AI/半導體/軍工/網安/雲端/潔淨能源/電動車/太空/生技/鈾核能/基建/黃金礦)+ 9 檔台股主題個股(AI伺服器 廣達/緯創/緯穎、重電 華城/士電/中興電、軍工 漢翔、散熱 奇鋐、光通訊 華星光),各帶自身敘事共同因子。分類切換:指數/主題ETF/GICS產業/台股主題/台股個股;預設突出主題與指數,GICS 與個股可開關。
- **資料**:容器內為合成示意;真實資料走 `data/input/perf_prices.json`(yfinance bridge)即自動切換,UI 標示來源。
- 測試:autotest 22/22(新增 perf_trend_engine)· SOLID。

---

## v0119 — 走勢圖過濾 UI 重做(去雜訊)

回應「太多看不清/第二圖一堆線/要更寬/線粗規格」:
- **分類下拉 + 勾選過濾**:上方「分類篩選」下拉(主題ETF/台股主題/GICS產業/台股個股/指數),下方對應該分類的勾選清單(含顏色樣本),可單獨勾選/全選/全不選——使用者自己決定畫面要哪些線。
- **移除底部 rangeslider**(先前誤認的「第二圖一堆線」),改為乾淨的**時間範圍鈕**(1月/3月/6月/今年/1年/全部)。
- **拿掉右側圖例 → 圖更寬**;以勾選清單當控制,滑鼠移上顯示名稱。
- **線粗規格**:重點(勾選)線 1.4、一般 1.0、benchmark(指數)0.8 虛線、基準 100 線 0.8 虛線水平。
- **預設乾淨**:首載只顯示主題ETF(12)+ 指數 benchmark,台股主題/GICS/個股一鍵篩選開啟。

---

## v0120 — 資金流動 採用項目專頁 + 族群整合監控

`engines/flow_monitor.py` + manager `monitor` 命令(進 `all`)+ PS 啟動,生成 `flow_monitor.html`(兩分頁):
- **族群整合監控(方向·強度·走勢 整合為一)**:每一族群(指數/美股主題ETF/台股主題族群/GICS產業)一列,整合「方向(近月動能 流入▲/流出▼)+ 強度(0–100 bar)+ 走勢(自基準日 %)+ 正規化軌跡 sparkline + 成分檔數」。
- **資金流動 實際採用項目(專頁)**:從設定檔自動列出真正追蹤的標的——① FIS 資金流 ETF 宇宙(70檔依 T1–T4)② 正規化走勢採用標的(指數/美股主題ETF/台股主題個股/GICS/台股個股,含主題標籤)③ 情境模擬三維節點(區域10/層級4/類型8)④ 資料來源(TWSE T86/MI_MARGN/FRED/Yahoo/yfinance bridge + 時效規則)。明確區分「美股主題ETF vs 台股主題個股」。
- 測試:autotest 23/23(新增 monitor_engine)· SOLID。

---

## v0121R — 宏觀對照層 + 六介面互串(v0100R 重建樹上新增;2026-08-12 操作員令)

「先檢視全球各類各區ETF現金流搭配各地匯率利率美元指數經濟狀況強弱來觀察資金流動的強弱及方向 串連所有工具及介面」:

- **`flow_macro.py`(第 17 引擎)+ `config/macro.json`**:12 區每區宏觀分 =
  w1·本幣動能 + w2·利差(區−美) + w3·經濟強度(PMI−50) − w4·美元逆風(DXY×敏感區)。
  **判讀矩陣**:FIS 與宏觀分同號=順風(流入獲支撐/流出有理由);異號=背離
  (流入無宏觀支撐=慎追 / 流出但宏觀轉佳=關注轉折)。產物 `macro_overlay.json`,
  儀表板新增「宏觀對照」卡(DXY regime chip + 12 區判讀表)。
- **資料**:`data/input/macro_data.json` 側車(schema 見 config;零爬站);缺=合成 demo 明標。
- **六介面互串**:`flow_ui.nav_strip()` — 儀表板/世界地圖/風險階梯/情境模擬/走勢圖/監控台
  六頁頂端互跳導覽帶(同資料夾相對連結,離線可用)。
- **manager**:新 `macro` 命令,已串進 `all`/`live`;autotest 16/16(+macro_overlay_engine/
  macro_verdict_rule/ui_macro_card/nav_chain_six)。
- 註:本節建於 v0100R 重建樹;原 session 檔到件依整合去重裁定合流。

---

## v0122R — 整合 Hub 一窗到底 + 理論總覽(2026-08-12 操作員令)

「理論整合 所有跳出來的介面整合 用流程圖說明邏輯 圖示說明清楚邏輯清楚各項關聯清楚重整介面」:

- **`flow_hub.py`(第 18 引擎)→ `flow_hub.html`**:固定左側欄(VRN 側欄規約同族)00-06
  七頁一窗切換;六視圖 iframe 內嵌懶載(點到才載,啟動秒開;同資料夾離線)。
  **啟動器自此只開 Hub 一窗** — Activate hub-first,不再彈六窗(hub 缺才退舊行為)。
- **00 理論總覽(全 SVG 自含)**:①全鏈流程圖(資料側車→FIS 核心→校準迴圈→三層驗證→
  宏觀對照→六視圖,箭頭標資料物)②判讀四象限(FIS×宏觀分;圖示=行動:✅順風流入/
  ⚠️背離慎追/🌱轉折關注/🍂順風流出)③三層 SOLID AND 關係圖 ④引擎五層關聯圖
  (資料→核心→驗證→呈現→編排;18 支誰餵誰誰把關誰)+ 核心公式四條(FIS/GRAM/宏觀分/評價 V)。
- manager 新 `hub` 命令,all/live 鏈尾自動重生;autotest 17/17(+hub_one_window)。

---

## v0123R — 宏觀對照 v2:14 因子全譜 + 自適應權重鐵律(2026-08-12 操作員令)

「新台幣/日圓/英鎊/歐元/人民幣匯率 · 各區利率 · 長中短期公債殖利率 · 黃金現貨期貨 ·
總經/貿易/財政/通膨 · 加密貨幣 — 重因素全部考量;任何參數權重全都是算出來的變動的不可固定」:

- **14 因子/區**:五幣匯率動能 · 政策利差 · 2y/10y/30y 殖利差 + 期限斜率 · 黃金現貨動能
  + 期現基差 · 總經 · 貿易收支 · 財政收支 · 通膨 · DXY · BTC(UK 區新增,13 區)。
- **權重鐵律(核心)**:config 不再含任何因子權重(autotest 硬鎖)。
  `weight_i(t) = 滾動 rank-IC(因子_i, 次期區域 FIS) / Σ|IC|`(帶號正規化,Σ|w|=1)
  — **連因子方向都由 IC 符號決定,引擎零手寫符號**;視窗 {20,40,60} 逐區掃選(自適應);
  樣本 < min_obs 之因子誠實閒置;全閒置=判讀留白「樣本不足」;每輪重算 — 權重是輸出不是設定。
- **可稽**:macro_overlay.json 含 weights_table(逐區 window/weights/ICs)+ weights_derivation;
  UI 卡逐區列主導因子 chips(權重×當前 z)。
- **資料 schema v2**:長表 {date,series,value};series = FX_<區>/RATE_<區>/Y2/Y10/Y30/ECON/
  TRADE/FISCAL/CPI_<區> + DXY/GOLD_SPOT/GOLD_FUT/BTC(側車零爬站;synth demo 注入相關結構
  供權重推導示範,明標)。
- autotest 20/20(+macro_no_fixed_weights/macro_weights_computed/macro_small_sample_honest)。

---

## v0124R — 效度×信度量測 + 誠實缺口卡 + 全面白話化(2026-08-12 操作員三問令)

「提升有效度信度如何衡量 · 我們少考量甚麼 · U/I 說明要簡單白話一點」:

- **效度(準不準)**:walk-forward 樣本外命中率 — 把時間切回過去,每步只用當步以前的資料
  算權重+打分,對隔天區域資金流方向計分;丟銅板=50%。非事後諸葛。
- **信度(穩不穩)**:①對半重算 — 資料切前後兩段各算一次權重,兩份答案排名相關(1=完全一致)
  ②判讀翻號頻率(翻來翻去=不可靠)。
- 三數字入儀表板「效度×信度」卡,附白話解讀;合成 demo 下命中率≈50%/相似度低=誠實
  (示範資料本無領先訊號 — 系統不裝懂;真實資料進來數字自然收斂)。
- **誠實缺口卡(我們還沒考量)**:12 項白話+補法 — 真實資料(最大)/VIX/信用利差/油銅/
  流動性/資金面/政策行事曆/市場情緒/因子重疊正交化/牛熊分段權重/FDR 多重檢定/季節性。
  只增不減,補一項劃一項。
- **白話化**:SOLID 橫幅、權重推導、理論頁四公式全部加【白話】一行(例:FIS=
  「今天進出這檔 ETF 的錢,比平常多還是少?」)。
- BoardQA 封印驗真修 Windows CRLF 差異(雙式 hash:原始 or 換行正規化命中皆過)+
  .gitattributes 對 *.dc.html 鎖 -text。autotest 22/22(+macro_vr_measured/macro_gaps_listed)。

---

## v0125R — 現金流判讀準確度實測提升(2026-08-12 操作員令)

「提高描述現金流精準度與強度並測試成功 · 用何指標判讀 · 為何用他 · 準確度多少 · 如何再提高」:

- **因子 +2(共 16)**:資金流自身動能 flow_mom(錢有慣性 — 文獻最穩單一預測子)+ 變化率 flow_chg。
  每因子附「為何用它」白話理由(WHY 目錄→儀表板「判讀指標與理由」卡)。
- **權重引擎三升級**:①t 顯著閘(|t|<1.5 之因子當輪閒置 — 雜訊不給話語權)②收縮
  (IC×n/(n+20) — 小樣本不給大權重)③三視窗「集成」取代單視窗挑選(挑最好=過擬合;
  平均=穩)→ 信度對半相似 0.08→0.57。
- **NO_Z 規則**:已是分數單位的因子(FIS 本身)不二次標準化 — 二次 z 會洗掉水準/慣性資訊。
- **synth 補真實特性 flow_rho=0.35**:真實 ETF 資金流具正自相關(Lou 2012 等)— demo 原為
  iid 流量,任何日級方向預測之數學上限=50%(先前 47-50% 即誠實);補齊慣性後可測。
- **強度校準**:walk-forward 依 |宏觀分| 三分位 — 強訊號命中率須高於弱訊號(分數大小有意義)。
- **實測(70 檔×260 日,n≈509-528)**:反證端 rho=0 → 47.3%(≈丟銅板,系統不裝懂)·
  正向端 rho=0.35 → **54.0%**(強 54.0% > 弱 51.1%;理論天花板 ~61%)· 兩端 PASS。
- **新命令 `accuracy`**:一鍵重跑兩端實證(顯式 rho_override,修 __main__ 雙實例補丁假綠隱患)。
  真實資料到位後以此動詞持續追蹤實際準確度。

## v0126R — 原始會話五件原版工件歸戶 + Hub 07-11 掛入(2026-08-12 整合去重令)

六件上傳(無文字=裁定令)。cumulative_flow 兩件位元組全同(sha16 9b341923)去重保留一件;
五件皆原始會話正典產物、非本代引擎可重生 → 歸戶 `uploads_original/`(追蹤;root *.html
gitignore 不及子目錄)並掛入 Hub 側欄 07-11(flow_hub v0101R,懶載 iframe):

| # | 頁 | 檔 | sha16 | 說明 |
|---|----|----|-------|------|
| 07 | 模擬終端(原版) | via_flowsim.html | 7d372ca0 | 現貨資金流→價格動態模擬,8 情境×7 商品(含台指期/期貨基差/外資買賣超),自含零 CDN |
| 08 | 世界地圖(原版) | world_flow_original.html | be4f2876 | 世界資金流地圖動畫,inline Plotly v3.6.0(內嵌非 CDN) |
| 09 | 累積資金流(原版) | cumulative_flow_original.html | 9b341923 | 累積資金流曲線,inline Plotly |
| 10 | 監控台(原版) | flow_monitor_original.html | c2ff8be6 | 資金流動採用項目+族群整合監控原版 |
| 11 | 因子字典矩陣(原版) | factor_dict_matrix_original.html | aee4ee50 | 30 因子優化流程定位(Google Fonts CDN=參考樣張,離線優雅降級) |

同回兩張原始會話截圖=原版設計參考存證(驗證圖版式/RORO 指針儀表板 NETFLOW·TRUST·FID 欄,
W=126 κ=2 30 ETF)→ 候令升級參考,無明令不改本代版面。順修引擎關聯圖口徑 autotest 17→22。
QA:autotest 22/22 · selftest 14/14 · Playwright 實測 07-11 五頁 Hub 內全載入。
