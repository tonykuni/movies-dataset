# VRN-2 v0165 驗證紀錄(2026-11-01 · RoundAll v0121 · Handle-All v0113 · 套件 v0164 不動)

## 1. 起因

桌機 2026-11-01 04:11(v0164 repair):收尾 **REVIEW**(VRN-2 0 · VCGC 0 · 人工 2 · 資料源 3)· 操作員「繼續下一步,依照你的建議進行」。
上一輪建議:① 人工確認紀錄(看過原文、親手確認後不再列)· ② 這輪新增的 8 條 SSOT 規則要送 VCGC(repair 不放提案冊 → 核號請求仍「提案 9」)。

## 2. 修法(只換 RoundAll · 套件 / runtime / 啟動器不動)

| 檔 | 內容 |
|---|---|
| RoundAll v0121(`627f6af3fd9b`)| `--confirm list / H-代碼 [--note] / revoke H-代碼`(只有操作員親手打 · 只增 `VIA_Reports\\vrn2\\VRN2_HumanConfirm.json` · 打錯 / 內容已變的代碼不記 · 確認後用上一輪結果重做收尾頁)· 收尾頁人工項帶代碼(根 + 內容指紋)與可複製的指令 · 有效確認 → 「人工已核」不計 · 「輸出冊 · 缺項 N 份」寫出哪幾份(讀最新啟動器日誌)· ⑤ ssot:套件 runtime 的提案冊比核號請求新 → 補放提案冊 v0101 + SSOTSync 鏈 → ⑤b sync · 自測 83 |
| Handle-All v0113(一行 `6ffe1f970276` · 開機檔 `4a904c294227`)| 指向 RoundAll v0121 · REVIEW 的下一步提示提 `--confirm` · 最短一行 443 字元 · cmd 一行 1240 字元 |

AI / 自動流程永不寫確認冊(自測 82 驗證只有 step_confirm 寫 · 流程裡不呼叫)。內容一變(份數 / 檔 / 點)代碼就變 → 舊確認不算。

## 3. 測試

```text
[PASS] 79 人工確認代碼:同內容(空白不同)同代碼 · 內容變了代碼就變 · revoke 之後不算
[PASS] 80 收尾頁:人工項帶代碼 + 複製用的 --confirm 指令 · 打錯代碼不記(rc 1)· 確認後重做收尾頁 → 人工已核 · REVIEW → DATA_GAP · revoke → 回 REVIEW · 紀錄只增(2 筆)
[PASS] 81 ⑤ ssot:套件 runtime 的提案冊 v0101 比核號請求用的 v0100 新 → 排 ssot · 一樣新 → 不排 · 沒有套件 → 不排
[PASS] 83 「輸出冊 · 缺項 N 份」寫出哪幾份(讀最新啟動器日誌的「輸出冊缺項 · 檔:缺什麼」· 去色碼)· 代碼含檔名(檔變了要重核)
[PASS] 82 v0121:套件照舊 v0164 · 貼回包收人工確認紀錄 · 只有 step_confirm 寫確認冊(流程裡不呼叫)· ⑤ ssot 補放提案冊鏈
[PASS] VRN2_RoundAll v0121 --selftest · 83 項 · 不過 0
venv(py3.12):[PASS] VRN2_RoundAll v0121 --selftest · 85 項 · 不過 0
pwsh 7.4.6 剖析錯 [0, 0, 0, 0, 0] · Handle-All 一行 = 可讀版 True · 開機行 = 可讀版 True
e2e:repair rc 0 · confirm list rc 0 · confirm bad rc 1 · confirm ok rc 0 · H-43073c23 H-764d04e4  · report rc 0 · tamper rc 0
```

## 4. e2e(桌機 v0153 狀態沙盒 · 發行夾 v0164 套件 + v0165 · pwsh 7.4.6)

```text
[repair] [GREEN] boot: Handle-All v0113 SHA-256 OK (claude/optimistic-goodall-yhalc5)
[repair] [GREEN] ⑤ 修 · SSOT 提案冊 VRN2_SSOT_Proposals_v0101.json(這輪新規則 · ssot_id 空白)送 · 提案冊 VRN2_SSOT_Proposals_v0101.json · 提案 17 · 待核號 503(ssot_id 空白 · 等 VCGC 核發)
[repair] [GRAY] ⑥ SSOT-ID 請求 · 待核號 503 · 提案 17 · 自撞 0(等 VCGC 核發)
[repair] ===== 收尾 · BLOCKED · 等 VCGC · VRN-2 側沒有待修 · 3 項等 VCGC 決定 / 安裝
[repair]   [VCGC] 3 項
[repair]   [人工] 2 項
[report] [GREEN] boot: Handle-All v0113 SHA-256 OK (claude/optimistic-goodall-yhalc5)
[report] [GRAY] ⑥ SSOT-ID 請求 · 待核號 503 · 提案 17 · 自撞 0(等 VCGC 核發)
[report] ===== 收尾 · BLOCKED · 等 VCGC · VRN-2 側沒有待修 · 3 項等 VCGC 決定 / 安裝
[report]   [VCGC] 3 項
[tamper] [RED] boot SHA-256 mismatch - not run
```

確認流程:
```text
[待核] H-764d04e4 · ⑥ 四點原文核對 · REVIEW_OCR · {"PASS": 52, "OCR_PENDING": 4} · 不過 4 點:MQ-1560 20260520.pdf 第 1 點 OCR_PENDING(image page; OCR excerpt needs image verification) | MQ-1560 20260520.pdf 第 2 點 
       你核對過原文 / 做了決定 → python "<sbx>/home/Downloads/VRN2_RoundAll_v0121.py" --confirm H-764d04e4
[待核] H-43073c23 · ⑥ ⑥f 共識還沒經 VIA 網路工具 · 這份共識是直連引擎抓的(VIA_CNYES_FactSet_YFinance_Consensus_Fusion_Engine_v0121.py)· 同意閘未開 → 這輪沒重抓(現有共識不動)
       你核對過原文 / 做了決定 → python "<sbx>/home/Downloads/VRN2_RoundAll_v0121.py" --confirm H-43073c23
[RED] H-deadbeef 不在上一輪收尾頁的人工核對項(打錯 · 或內容已變 → 先 --confirm list 看現在的代碼)· 沒記
[GREEN] 已記確認 H-43073c23 · ⑥ ⑥f 共識還沒經 VIA 網路工具
[GREEN] 已記確認 H-764d04e4 · ⑥ 四點原文核對
收尾頁(用上一輪的結果重做)· BLOCKED · 等 VCGC · VRN-2 側沒有待修 · 3 項等 VCGC 決定 / 安裝 → <sbx>/VIA/VIA_Reports/vrn2/VRN2_CloseoutUI_latest.html
```

收尾狀態:{"repair": {"state": "BLOCKED", "per_owner": {"VCGC": 3, "人工": 2}, "codes": [["人工", "H-764d04e4"], ["人工", "H-43073c23"]]}, "confirmed": {"state": "BLOCKED", "per_owner": {"VCGC": 3}, "codes": [["人工已核", "H-764d04e4"], ["人工已核", "H-43073c23"]]}, "report": {"state": "BLOCKED", "per_owner": {"VCGC": 3}, "codes": [["人工已核", "H-764d04e4"], ["人工已核", "H-43073c23"]]}}

桌機狀態預演(03:08 貼回包):RoundAll v0121 build_closeout on the 03:08 paste-back state: REVIEW (人工 2 · 資料源 3) → both 人工 items confirmed → DATA_GAP (資料源 3)

**沒跑到的**:the desktop itself (next repair: ⑤ ssot → 提案 17 · closeout shows the --confirm lines) · the operator's own confirmation (by design only the operator runs --confirm)。
