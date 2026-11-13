# VCGC 工具矩陣 · 政策 L129 · 新命名 · 整合兩會話(2026-11-13 b)

> 操作員令(節):「矩陣顯示目前VCGC本身中央控管功能及節省TOKEN工具所有工具即被整合進來的所有工具 … 自動隨時更新於HTML」
> 「VCGC政策規範強硬化 … 獨立性 … 我跟AI有修政權 … 不可用且不可出現任何TA-LIB … 子系統自行註冊 VCGC檢視登陸 … VIA_VCGC_SUP001_ / VIA_VCGC_MDL001」
> 「將我指令視覺鎖定模板整合進來併用它來顯示VCGC進行VCGC收尾」「檢差商業化產品號封裝管理模組有無被整合」「(兩個會話連結)整合進來」
> 需求 VCGC-REQ227–231 · 工作流 VCGC-WKF044 · 政策 L129(VIA-VCGC-PLCY6522)

## 一、新件 / 新版

| 件 | 做什麼 |
|---|---|
| `VIA_VCGC_MDL258_ToolMatrix_v0100.py`(新命名第一支) | 一頁 HTML:VCGC 收尾 · 工具 MDL / SUP · 整合進來 INT · 獨立性 / 衝突 · TA-Lib · 各系統登錄 · 命名與政策。畫面用 `VIA_VisualLock` 尾版(token 從鎖定正本抽、內嵌、出頁當場過鎖定閘)。`build` / `naming [--apply]` / `check` / `watch`。自測 16/16 |
| `VIA_Policy_Laws_SSOT_v0118.json` +L129 | 獨立性強化 · 升級不連動 · 修法權(操作員 + AI)· 無衝突出號具法律性 · TA-Lib 不可用不可出現 · 子系統自行註冊 · 命名 `VIA_<系統>_<類>###_<名>_vNNNN` · 顯示走視覺鎖定。L128 已被 optimistic-goodall 分支用掉,跳號 |
| `VIA_VCGC_ToolNaming_v0100.jsonl`(只增) | 名碼帳:MDL001–259 · SUP001–038(297 列,每列帶中央編號 · 尾版版本 · 時間);留白 10(7 支 CGC 沒版本號 · Celeritas / AegisNexus 沒中央 MDL 號 · FLOW_ENG023 沒號) |
| `CGC_MDL224_TestAuto_v0107.py` | 串測家族掃描認得 `VIA_VCGC_<MDL|SUP>###_*`(舊家族一個不少)→ 新命名家族自動自測、紀錄冊留版本與時間 |
| `CGC_MDL279_MCPServer_v0104.py` | 本分支的讀檔三動詞版;practical-pasteur 的 v0103(uploads/latest)先寫 → 那支留 v0103、本支升 v0104(L25)。`.mcp.json` 指 v0104 |

自動更新:盤點冊站 `C-tool-matrix-build`(quick)→ 每次 `test --quick` 重出 `VIA_Reports/vcgc/VCGC_ToolMatrix_latest.html`;頁面每 5 分鐘自動重整;本機背景可 `run VIA_VCGC_MDL258_ToolMatrix watch`。

## 二、實測(容器)

| 項 | 結果 |
|---|---|
| ToolMatrix 自測 | 16/16(含真樹出頁 · 鎖定閘 GREEN · build 不動命名帳 / 號冊 / 工具鎖冊) |
| 真樹 build | 307 家族(MDL 267 · SUP 40)· 已發 297 · 衝突 0 · 鎖定閘 GREEN · Playwright:0 JS 錯 · 390px 寬不橫捲 |
| check | 尾版 TA-Lib 程式使用 0 · 命名衝突 0 · **他系統尾版 4 檔釘 VCGC 版號**(紅,點名不代改)· VCGC 54 家族釘他系統版(黃) |
| 政策閘 | rc 0(v0118) |
| 編號 --scope | +708 列 · 遺失 0 · 改身分 0 · 重號 0 |
| handoff test | C-tool-matrix-v0100 · C-mcp-server-v0104 · chain 全 rc 0 |
| test --quick | YELLOW 站 14(綠 12 · 黃 2 既有 · 紅 0)· case 280/280 · workflow 184/184 |
| closeout(乾跑,三案) | ③ 全綠;① / ⑨ 交接閘 RED、⑥ SDD RED(既有 + 下面一項) |

## 三、照實沒做完

- **registry-sync 沒寫入**:乾跑退役 378 幾乎全是主控台元件 —— 合進來的收容版 `docs/handoff/ai/intake_20261110_vcgc_multimatrix/v0195/CGC_MDL149_…_v0195.py` 被掃描面當成主控台尾版(主控台 SCAN_EXCLUDE 只排 `references/`)。寫入會把收容副本登成現役主控台 → 不寫。SDD X-REG 因此列「ToolMatrix 未註冊」。待操作員二選一(交接待辦 `VCGC-REQ230:registry-sync-intake-shadow`)。
- 舊家族不改檔名(L02 · L04 · 薄尾 glob 鏈);改用新檔名逐家族裁定(`VCGC-REQ228:legacy-rename`)。
- 商業化 / 封裝 / 產品閘四家族:有中央編號、在矩陣裡,但沒有 VCGC 測站 · 動詞 · 工作流;CAND-VCGC-COM-001…008 未核准;PKG 產品號沒中央發號(`VCGC-REQ231:commercial`)。
- 與 optimistic-goodall-yhalc5 仍撞:MDL279 v0103(第三支)· 主控台 v0193–v0196 · 政策 v0118 · 需求 / 盤點冊版號 —— 合併順序由操作員定。

## 四、第二輪(同日):主控台 v0197 · 兩大功能 · L130 單檔收斂 · L131

| 件 | 結果 |
|---|---|
| 主控台 `CGC_MDL149 v0197`(操作員選 a) | 掃描面只增排除 `/intake_`;收容版 v0195 不再冒充主控台。跳號避開 optimistic-goodall 的 v0193–v0196。自測 7/7 · 前版鏈 rc 0 |
| registry-sync | 乾跑「退役 378」→ 退役 0;`--apply`:新 107 · 變 33 · 撞號 0;刪舊版後再 `--apply`:新 7 · 變 22 · 退役 0 |
| 矩陣「兩大功能」 | 首頁 = VIA 中央管理工具(主控台 · 編號 / SSOT · 測試 / 閘 · 交接 / 收尾 · 環境 · 流程 · UI)× VIA 支援工具(Token-Saving · 加速器 / 支援橋 · 網路 · NLP / Layout / OCR · AI 平台 · 整併 / 資料)。自測 19/19 · 鎖定閘 GREEN |
| 政策 L130(PLCY6887) | 單檔收斂 · 驗證後刪舊版 · 支援工具一發行版 / 他系統各存一份同版副本 |
| 收斂就緒度(VCGC 307 族) | 單檔 138 · 可刪舊版 3 · 薄尾待合成 133 · 舊版被點名 33 |
| 首批刪除 | CGC_MDL267 v0100 · CGC_MDL268 v0100 · CGC_MDL270 v0100–v0105(8 檔);刪前 / 刪後自測 0 · 主控台 run 再驗 3/3 · 刪除帳 `VIA_VCGC_PruneLedger_v0100.jsonl` |
| 政策 L131 | 各系統管理器自管 · VCGC 管視覺規範 · 一鍵布建只問一題 A/B/C · 只用滑鼠 |
| 需求 | +REQ232–237(收斂 · 支援工具發行 · 一鍵布建 · 環境衝突 · 編號優化 · 管理器 / VCGC 角色) |

還開著:133 族薄尾要逐族合成單檔並證零遺失才可刪(不能機械合併);支援工具發行冊待操作員核可格式;一鍵布建器下一版(純滑鼠 HTML 一題 A/B/C)要在操作員電腦實裝(L19)。
