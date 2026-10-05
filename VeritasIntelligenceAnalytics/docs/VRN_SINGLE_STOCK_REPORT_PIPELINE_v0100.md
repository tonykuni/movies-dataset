# VRN 單股研報全流程正典 v0100(操作員口述 2026-10-05 整理;VRN System Manager 統轄)

**統轄律**:VRN System Manager 比照 VDF System Manager 統轄各站——SSOT 登錄、同義字、
工作流、輸入台全在其轄下;引擎只做事,調度與配方選用在 Manager。
**輸入**:一個檔(或整夾)投資研報,PDF 或影像;本流程處理**單一個股**研報(一報一股)。

## 一、取料順序(由輕到重,鐵律)
1. **檔名先行**:檔名解析(券商/代號/評等/日期;GF/廣發 DENY 律照 vrn_sample_reader)。
2. **首頁資訊段**:頂部左/右、或中央題名區(ENG072 階梯 + ENG393 主標題律)。
3. **首頁 LAYOUT 全元件辨識**(ENG394 尾版):資訊區從本文切出——左側或右側;
   資訊區內型別分類:**矩陣/表格/長句/文字** 各自成區,逐一元件化。
4. **財務頁**:先**左右**切半,再把左右各自的多張表**上下**切成視覺元件;同一條抽取梯。
5. **抽取梯(四階段配方,存 ENG400 殼)**:NON-OCR 先行 → 失敗區補互補 NON-OCR →
   無文字層才局部**輕** OCR → 少數失敗區才**重型**(很耗時,絕不先用);
   只有解析度不足,最後才升 DPI **300→350**。
6. **表格還原回原樣**:重建到與原報相同樣式(ENG400.TABLE:寬表 + 長表反 pivot + 來源證據)。

## 二、驗證(多重驗證全過才產出)
- **轉長表(pivot)對帳**:資料轉 long 式逐格驗狀態。
- **外部對帳(派 VDF 車道)**:TWSE/TPEX 取股名/中文簡稱;yfinance 調整收盤價驗目標價合理性。
- **歷史覆蓋律(第一優先)**:能取得最新歷史實際值,一律覆蓋報告內的預期值
  (歷史實際 > 預期);歷史區間長度要對(年數/期數對帳)。
- **倍數交叉驗算**:沿 ENG394 驗算律(漲跌幅、EPS 成長率、隱含常數 P/E×EPS≈價、
  淨利÷EPS≈股數)多路交叉,互證才算數。
- 資料一律取自**清洗修復後的表**;燈語:綠=指定驗證過、黃=有產出未全驗、紅=失敗。
- **EPS 身分核對律(補遺 2026-10-05,操作員令「EPS 不可定義但要確認」)**:報告端 EPS
  **不預設** BASIC/DILUTED——拿報告內**歷史實際** EPS 序列,對 TWSE/TPEX 擷取的
  **BASIC EPS / DILUTED EPS 兩路**逐期核對(容差 max(0.01, 0.5%×|外部值|),報表兩位小數進位),
  吻合的那一路才定其身分;兩路同值全吻合=INDISTINGUISHABLE(數字核對過、身分無法辨);
  部分吻合=UNCONFIRMED 黃、兩路皆不合=紅回查。**僅補充核對流程**,不改抽取端;
  工具口:`VRN_SystemManager eps-check --report … --basic … --diluted …`(外部序列由
  reconcile/VDF 車道供給;核對器不自行擷取)。

### 二之一、分析師三律與實測清場律(補遺 2026-10-05,操作員令)
- **分析師三律**:① email 的 **@ 前通常是分析師英文姓名**(`wang.xm` → Wang Xm);
  ② **@ 後 domain 是券商**(`gs.com` → GS,交互驗證 BROKER 欄);③ **分析師姓名通常在
  職稱/電話/郵箱區塊上方**,上一~二行短行優先,職稱同行剝職稱為後備。抽不到誠實 None。
- **實測清場律**:每一次實測**先刪前一次該動詞的輸出**(回刪單 `cleaned_prev`),避免混淆。
- **LAYOUT 驗證工具口**:`VRN_SystemManager layout-check <檔|夾>` — 首頁左右本文/資訊切割、
  財務頁**先左右切半再上下切視覺元件**(縱向空隙 >14pt 斷)、每區文字修復統計
  (字元/CJK/數字/壞字�),燈語:綠=兩區有料零壞字;自動跳 U/I 矩陣。

## 三、摘要(左側本文 → 四點題旨,來源連結式不捏造)
由 Summarizer(ENG062)+ 估值字典(ENG395)+ 欄位律(SUP_MDL749)產出固定四點:
1. **目標價 + 估值方法與邏輯**(DCF/PE/PB/SOTP…,方法名經 SynonymUnion 正名)。
2. **本年與未來 EPS + 成長動能**(如 AI 需求等動能敘述)。
3. **其餘內容擇要之一**(重要性排序)。
4. **其餘內容擇要之二**。
每點帶據點(頁·區·行),EXTRACTIVE_SOURCE_LINKED,絕不改寫數字。

## 四、SSOT/同義字對帳(本輪清點)
評等(HOLD/SELL/STRONG_*…)、目標價(TP/PT/目標價…)、估值法(DCF/PE/PB/SOTP…)、
RATING_FIELD 等詞彙已在 `VIA_SSOT_SynonymUnion_v0103`(SYN285–297,中央聯集);
券商簡稱 SYN199–282 在冊。**本流程無新增同義字缺口**;新詞一律走中央聯集冊尾版,不散落。

## 四之一、短主令(2026-10-05 全面盤點;以後每輪更新附一個短指令群不漏)
```powershell
via-vcgc run VRN_SystemManager intake "C:\測試樣本報告"        # 檔名律+自動矩陣
via-vcgc run VRN_SystemManager deepread "C:\測試樣本報告"      # 首頁深讀互證(FILENAME 鎖定·OCR 梯·NLP 座)
via-vcgc run VRN_SystemManager layout-check "C:\測試樣本報告"  # 切割/階層/混排/文字修復驗證
via-vcgc run VRN_SystemManager reconstruct "C:\測試樣本報告"   # 三大區重現+REVERIFY 再識別
via-vcgc run VRN_SystemManager eps-check --report … --basic … --diluted …   # EPS 身分核對
via-vcgc run VRN_SystemManager vdf-fetch tw_listings codes=2330 # VRN↔VDF 相連:中介讀庫→轉交 VDF 單獨擷取(--apply 真跑)
via-vcgc run VRN_SystemManager real-test "C:\測試樣本報告"       # 實測清點判定(PY 功能律;PS 只啟動)
via-vcgc registry-sync --apply                                  # 編號登錄(先 commit 再發號)
```
今日新律索引:自動 U/I 矩陣(每動作)· 清場律 · FILENAME 鎖定律 · 斷句修復(接句點/標題不接/TRIM)·
三大區(本文/資訊/財報)+REVERIFY · 梯=非OCR→NLP LAYOUT 修復鏈→輕OCR→重型 · 每步驟掛 LAYOUT NLP 座
(SUP_MDL866+PRADDLE)· 分析師六律 R1–R6 · 券商短縮寫(MEGA/MCQ)+域名別名 · 頁圖/假ETF 不收 ·
NO_TEXT_LAYER 誠實態 · 估值法/職稱/姓名式/財報比率 29 式入中央冊 · SYN +272 發號三零。
批1657 新律:外部價 NaN 列濾除取最後有效收盤 · TP 0/負值拒收(OCR 道 0.0)· 只有重申詞(維持/重申)
=評等誠實 None · TP 合理性燈(TP/報告日前價超出 0.15–8 帶=可疑回查)· REVERIFY 逐欄差異上報
(`reverify_diff`:哪欄首輪/重建後各是什麼)· REVERIFY 掃描先去自家格線「|」(渲染物非原文)。
批1657 三裁定(治理律首輪實行:母系統顯示 → AI+操作員裁 → 子系統落冊):① KEY_BRIDGE 不採用(正典短碼
為主,記 VRN_FieldRules_SSOT_v0101 broker.key_bridge_ruling);② STRONG_BUY/STRONG_SELL 立獨立正典鍵
(canon_map 4→6 鍵對齊六級碼冊,樞紐 glob 尾版自動讀);⑤ 包內三守衛入 ENG086 safe_broker 正本 v0120
(標的段先排除/小寫短碼限檔名黏接/最長優先;drift same 86→90);③④ V 拆型與 K/C/M/S/V 五型=先舉證後裁
(冊 ticker.pending_evidence,派 VDF 車道取 TWSE/TPEX ISIN 名冊)。
批1657 版面升級(操作員令):首頁資訊區**三型**——左側欄/右側欄(再**上下拆**,縱向空隙>14pt 斷)
/**下方帶狀**(再**左右拆**,x 中線分群);拆成獨立元件 `info_parts`(各帶 bbox/text/kind)再識別;
下方帶狀判準=KW 命中數不輸側欄且密度較高(top 不認:大標 KW 會誤搶);layout-check/deepread 列帶
`info_parts` 數;reconstruct/layout-check 依切線分件照走。矩陣頁首帶**引擎戳**(引擎檔名+mtime+出頁
UTC)——介面不動一看戳即辨舊引擎/舊頁。

## 四之二、治理律:子系統獨立性 · 母系統輔助性(操作員令 2026-10-05)
- **子系統獨立性**:所有 SSOT / REGEX / 同義字 / 邏輯由**子系統(VRN)生成**——中央冊尾版
  (Central_Synonym_Regex / SynonymUnion / Broker_Dict / ExtractRules)的 VRN 域條目一律出自
  VRN 工作,VRN System Manager 是唯一載入與使用口(`_central_regex`/`_broker_map`/`_fin_lex`)。
- **母系統輔助性**:母系統(VCGC)**只檢查衝突並顯示**(`via-vcgc ssot panorama` 七探針、
  ENG088 drift 攤開列),**不裁定、不自動改**;修改由 **AI + 操作員**依顯示結果裁定後,
  走子系統冊尾版落冊(只增不減不衝突)。
- **VRN 統轄確認**:deepread / layout-check / reconstruct / eps-check / intake / reconcile /
  closeout 全數經 VRN_SystemManager 動詞口(VIA_FROM_VCGC 閘 + 前版鏈),引擎(ENG052/085/
  SUP_MDL866 NLP 座)只被 Manager 調度,不自行對外。

## 四之三、PY 功能律(操作員令 2026-10-05 批1657)
- **從 VRN 起,所有有功能的指令都用 PY 寫**,帶加速器橋(L103/L102:Celeritas 契約);
  **PS 只負責啟動與連結 HTML U/I**,不帶判定邏輯(.ps1 零觸碰,L70)。
- 首例落實:原 `Invoke-VIA-RealTest-VRN-v0103.ps1` 的判定段(輸出清點/249 判讀/風險判讀/總判)
  PY 化為 `VRN_SystemManager real-test <樣本夾> [分鐘窗]`(矩陣+RESULT json 照出);雙軌引擎照走各自動詞。
- **列管律**:VCGC FLOW 親子表(CGC_MDL223 v0101)加四族工具列(role=tool)——省TOKEN(CGC_MDL158)·
  SSOT全景(CGC_MDL247)· 編號(CGC_MDL237)· 加速器(SUP_MDL737→Celeritas 尾版)· 網路(SUP_MDL740→AegisNexus 尾版);
  工具列紅=擋動詞,與管理者列同權重。

## 五、掛載
工作流:`VIA_Workflow_VRN_SSOT_v0105.json` **VRN-WKF009(single_stock_report)**,九步,
每步正主可尋尾版;需求 `VRN-REQ017` 雙向掛載(`VIA_Requirements_SSOT_v0172.json`)。
編號:WKF009/STP/REQ017 待操作員 `CGC_MDL237 --apply --scope <兩冊>`(VRN 冊走 `--family vrn` 自理口)。
