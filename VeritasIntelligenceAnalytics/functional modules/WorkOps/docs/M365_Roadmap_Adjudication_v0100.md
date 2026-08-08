# M365 規劃書 v1.3 落地裁定 v0100(2026-08-09)

操作員上傳《WorkOps × M365 郵件追蹤自動化策略規劃書 v1.3》(正本:`docs/VIA_WorkOps_M365_Roadmap_v13.pdf`,
sha256 前 16 碼 `d87280a1bd8ac19d`),令:補強註冊功能/工具 · 整合所有工具 · 建立 U/I ·
test debug…till it work。本文為整合去重裁定正本(只增不減;變更以新版追加)。

## 一、訊號源 S1–S12 盤點裁定(規劃書 §02)

| # | 訊號源 | 裁定 | 落點 |
|---|---|---|---|
| S1 | 主旨代號叢集 | 已建(板③頁)→ **本輪接入融合** | wop_identifier `s1_code` |
| S2 | 控管表 | 已建(板①頁)→ **本輪接入融合**(最強票) | `s2_sheet`;庫根後備同板 v0112 |
| S3 | 關鍵字/命名 | 已建(ENG-023 命名帳本)→ **本輪接入**(THR→CASE→名稱) | `s3_name` |
| S4 | Outlook 資料夾結構 | 候補 — 資料夾稽核表既有,歸戶對映待操作員圈定 | 下輪 |
| S5 | 寄件網域對映 | **本輪新增**(domain_map 空表起步,操作員增列) | `s5_domain` |
| S6 | 收件組合 | **本輪新增 lite**(pending TO 網域;mails.csv 無 To/CC 欄誠實降級) | `s6_recipient` |
| S7 | 回覆鏈拓撲 | 既有雛形(thr_case_map v0101)→ **本輪接入**(同案強票) | `s7_case` |
| S8 | 附件檔名 | 候補 — attach 引擎在深鏈,pattern 庫待建 | 下輪 |
| S9 | 行事曆會議主旨 | 候補 — matrixsync 反向讀取待建 | 下輪 |
| S10 | 時間叢集 | 候補(輔助訊號,權重低) | 下輪 |
| S11 | 語意聚類 | 既有 TF-IDF 於 analytics;embedding 選配不引入(去重原則) | 維持 |
| S12 | Splink 實體歸戶 | 規劃書自判:<1k 實體 rapidfuzz+alias 即夠 — 不引入 | 維持 |

**LEARN 學習記憶**(規劃書 §02「每次人工確認都是訓練資料」):本輪落地
`wop_confirmations.jsonl`(append-only)— 網域/代號/串三軌記憶,權重 `learned`
高於統計訊號;容器實測:1 次確認 → ASK 1→0、留置 2→1(同網域串自動歸戶)。

## 二、模組 M1–M6 對照(規劃書 §07)

| 模組 | 裁定 | 落點 |
|---|---|---|
| M1 wop_identifier | **本輪建成** | `engines/workops_wop_identifier.py`(ENG-028)+ `identifier_params.json` |
| M2 wop_numbering | **本輪建成**(併入 M1;沿用板側 id_ledger 單一序號源防 F11 碰撞) | 同上 + `out/wop_registry.json` |
| M3 reply_parser | 候補 — 投票/token/關鍵詞三層解析;VMT 收斂引擎既有為底 | Phase 1 |
| M4 template_engine | 部分既有(v0113 範本選擇器+approval_request_v2+投票鈕);三語範本包/升級鏈候補 | Phase 1 |
| M5 watchtower | 部分既有(板②追蹤哨+aging+通知);自動升級鏈草稿候補 | Phase 1 |
| M6 graph_connector | 休眠 — 待 IT 核准(申請信正本在規劃書 §12,可直接取用) | Phase 3 |

## 三、UI 裁定(mouse-only 原則)

- **WopConfirmQueue.html**(本輪建成):分歧件預選最可能答案+chips+「全部接受」
  +下載確認檔;留置區可見(F10 不成黑洞)。瀏覽器不可寫檔 → 下載 `wop_confirm.csv`
  存回 `out\` 後 `via-workops wop apply` — 與板拖放區同一資料回流模式。
- 板 v0113 ⓪流程頁/①半自動建構/②範本選擇器 = 規劃書「高度視覺化管控」同軸既有。

## 四、失敗目錄 F1–F25 之本輪內建對策

F7 分歧必進 ASK 不強判 · F9 編號永不變保底 · F10 留置區可見+新郵件自動重判 ·
F11 單一序號源(id_ledger)+原子寫 · F13 暫存改名永不原地覆寫 · F19 壞列隔離不阻斷 ·
電子報不成專案(bulk_senders.txt 既有庫再利用=整合去重)。

## 五、註冊補強

ENG-028 入 `VIA_AutoCode_Registry_v0100.json`(components+ledger append);
引擎數 27→28;板⓪頁註冊晶片下次產板自動反映(現算,不寫死)。

紅線不變:絕不代寄 · 原件/分類零觸碰 · 編號永不變 · 基底零觸碰 · 只增不減 · 參數=JSON。
