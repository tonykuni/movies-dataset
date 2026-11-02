# VRN-2 v0169 驗證紀錄(2026-11-02 · ⑥f 同意閘列 → 人工 · 整輪遇閘未開先問中止 · 套件 v0168 不動 · RoundAll v0125 · Handle-All v0117)

## 1. 桌機 2026-11-02 12:31(v0116 整輪 3117 秒)——資料面已全部完成

| 項目 | 結果 |
|---|---|
| 年度數據 | 11,905 筆(6143 的 40 值補回 · v0259 轉置表再驗)· 剔除 2,508 · **缺項 0** |
| 驗證 | 冪等閘 GREEN · ⑪ 獨立驗證錯值 0(TRANSALIGNED 190 → 230)· 完成判定 紅 0 · 四項全綠 52 份 |
| 增量庫 | FinancialData 累計 11,953 · MOPS 列乾淨 · TP(ADJ) 同步還原 5 |
| 這輪唯一退步 | Combined 共識欄 52 列全空 —— ⑥f 被 DENY(見下)· 閘開 + repair 重抓即補回(增量庫兩輪都留 · 查詢用最新)|

## 2. 收尾 OPEN「VRN-2 1 項」是什麼

- 操作員在 **PowerShell 視窗**貼了 **cmd 寫法**的 `set "VIA_SCRAPE_CONSENT=YES"` → 沒設成(③b 已印黃字提醒)→ ⑥f 共識整輪被 VIA 網路工具 DENY(同意閘未開 · 引擎不代設 · 不換道)。
- 收尾頁那一列「⑥f VIA 網路工具 DENY · 同意閘未開(操作員決定)」在負責方規則**沒有分支** → 落到預設 VRN-2;它與 ⑥f 共識列同根,合併取最重負責方 → 整個共識項被標成 VRN-2。
- 同意閘是操作員的環境變數,從來不是 VRN-2 要修的程式 → 標籤錯。

## 3. 修正

- **RoundAll v0125**:⑥f 列 detail 帶「同意閘未開」→ **人工**(提示附 PowerShell 與 cmd 兩種設法 · 開了再跑 auto = repair 會重抓共識補回 Combined);帶「合規 DENY」→ VCGC。其他規則不變。
- **Handle-All v0117**:整輪 + 同意閘未開 → 先停下來問(`A` = 中止 · 自己設好再重貼;Enter / 非互動 = 照跑 · 閘保持關)。**腳本永遠不代設同意閘**(操作員 2026-10-31 規則)。
- 套件 v0168 不動(雜湊照釘)· 啟動器 / 管理器都不動。

## 4. 測試

| 項目 | 結果 |
|---|---|
| RoundAll v0125 自測 | [PASS] VRN2_RoundAll v0125 --selftest · 91 項 · 不過 0 |
| 12:31 那兩列重判(沙盒 · 只讀) | 兩列都 → 人工 · 合併成一項人工(以前 VRN-2)|
| PowerShell 剖析 | pwsh 7.4.6 剖析錯 [0, 0, 0, 0, 0] · Handle-All 一行 = 可讀版 True · 開機行 = 可讀版 True |
| e2e(最短一行 · 沙盒含三份原文) | auto1 rc 0 · confirm list rc 0 · auto2 rc 0 · abort rc 0 · tamper rc 0 · auto 整輪(閘關 · 非互動 stdin 預設照跑)→ repair → VRN2_MODE=full + 管入 A → 「已中止」且沒跑 RoundAll → 竄改開機檔不執行 · 收尾狀態 {"auto1": {"state": "OPEN", "per_owner": {"VCGC": 8, "VRN-2": 3, "人工": 8}}, "auto2": {"state": "OPEN", "per_owner": {"VCGC": 6, "VRN-2": 3, "人工": 8}}} |

## 5. 一行指令(PowerShell 視窗 · 先開同意閘)

```powershell
$env:VIA_NET_CONSENT = 'YES'; $env:VIA_SCRAPE_CONSENT = 'YES'
```

再貼最短一行(443 字元 · 開機檔 `vrn2_release_v0169/VRN2_HandleAll_v0117_boot.txt` SHA-256 `38188cd76b7f` · Handle-All 一行 `3f23f333b036` · RoundAll v0125 `617542d2f196` · 套件 `931b6a9ac38c` 不動)。
auto:收據已是 v0168 → repair(重抓 ⑥f 共識 · 約 10 ~ 15 分鐘)→ 收尾應 REVIEW(VRN-2 0)· 人工只剩 MQ-1560 四點。

## 6. VRN-2 收尾的終點定義(給操作員)

PASS 要所有外部缺口都消失,做不到(⑥e VDF rc 2 PARTIAL 與 AAPL 非台股是來源的事)。VRN-2 側的終點 = 收尾頁 **VRN-2 0 · VCGC 0**,
人工項由操作員 `--confirm` 記錄後 → **DATA_GAP(只剩資料源)**。SSOT 517 件待 VCGC 核號(四系統對等 · VRN-2 只讀等待)。

## 7. 沒做 / 待辦

- 人工確認只有操作員親手打 `--confirm`(MQ-1560 四點 · 上輪代碼 H-fd2ea35f · 以收尾頁列的為準)。
- 3014TT 四點(第 2 點從句中開始 · 第 1 / 3 點重複)· MQ-1560 OCR 字詞錯(chi players)→ 要改摘要器 + 整輪,操作員點頭才做。
