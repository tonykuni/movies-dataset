# VRN-2 v0155 驗證紀錄(2026-10-31 · RoundAll v0111 · Handle-All v0103 · 套件 v0154 不動)

## 1. 桌機 2026-10-31 02:06(最短一行 → Handle-All v0102 repair · 608 秒)

- 最短一行過了:`[GREEN] boot: Handle-All v0102 SHA-256 OK` → auto 選 repair → RoundAll v0110 取套件 v0154(11 檔逐檔相符)。
- ⑥f(ConsensusJoin v0103):今天的 checkpoint 搬 38 / 43 份 → 只重抓 6933 / 8358 / 7728 / 2891 / 4171 → **8358 / 2891 這次抓到** →
  4171 / 6933 / 7728 仍 404 → 等 30 秒重試一次仍 404 → 不納入閘 → 搬 40 / 40 份(不上網)→ gate PASS_WITH_WARNINGS · **GREEN**。
- Combined 重組 · 增量庫追加 Combined 6 列 · Workbench 重渲染。
- 收尾 **OPEN · VRN-2 1** = ⑥ Combined 冊:GFHK Apple(TICKER `AAPL`)那列共識欄空 → 原因「共識缺:共識 40 / 40 代號 …」→ v0110 算 VRN-2。
  v0109 以前這格被整批摘要裡的「鉅亨沒有 FactSet 頁」字樣碰巧算成資料源;v0110 拿掉整批代號清單後就露出來。

## 2. 修法(RoundAll v0111)

共識欄空、代號不是台股 4 碼 → 「代號不是台股 4 碼(TICKER 'AAPL')· 共識只查台股」→ 資料源(TICKER 空白 → 人工)—— 跟同一份冊調整後目標價的規則一樣。台股代號的「共識缺」照舊 VRN-2。

## 3. 測試

```text
[PASS] 51 Combined:代號不是台股 4 碼(GFHK Apple · AAPL)那列共識欄空 → 資料源(桌機 02:06 被 v0110 算成 VRN-2)· TICKER 空白 → 人工 · 台股代號的「共識缺」照舊 VRN-2
[PASS] VRN2_RoundAll v0111 --selftest · 51 項 · 不過 0
pwsh 7.4.6 剖析 0 錯 · Handle-All 一行 = 可讀版 · 開機行 = 可讀版(詞序列相同)
```

## 4. 最短一行 e2e(沙盒 GitHub 分支 · pwsh 7.4.6 · 路徑用 / 測)

```text
[report] [GREEN] boot: Handle-All v0103 SHA-256 OK (claude/optimistic-goodall-yhalc5)
[report] ===== 收尾 · BLOCKED · 等 VCGC · VRN-2 側沒有待修 · 5 項等 VCGC 決定 / 安裝
[report]   [VCGC] 5 項
[report]   [人工] 1 項
[report] [計] Handle-All 結束 · RoundAll 結束碼 1 · 1 秒(視窗不會關)
[auto] [GREEN] boot: Handle-All v0103 SHA-256 OK (claude/optimistic-goodall-yhalc5)
[auto] [計] ④ 自動選模式 repair · 上一輪收據 VRN2_Closeout_v0153.json · 上一輪輸出冊 有(輸出冊是啟動器 v0153 以後做的 · 這版只改 ⑥f 共識 → 不整輪)(整輪:先貼 $env:VRN2_MODE = 'full')
[auto] [計] ④ 模式 repair:取套件 v0154 → ⑤ 自動修(⑥f 共識閘只因 404 / 一時抓不到 → 用 ConsensusJoin v0103 重跑 · 沿用今天抓到的 · 重組 Combined · 增量庫 · Workbench)→ 除錯報告 → 收尾頁 → 貼回包(幾分鐘)
[auto] [計] ⑤ 自動修計畫:市場資料比歷史對齊新 / 歷史對齊沒跑 → 重跑 ⑬b · Combined 比市場 / 共識舊(或不在)→ 重組 · ⑬ 增量庫補寫(本輪有修正) · Workbench 重渲染(最新收據)
[auto] ===== 收尾 · BLOCKED · 等 VCGC · VRN-2 側沒有待修 · 6 項等 VCGC 決定 / 安裝
[auto]   [VCGC] 6 項
[auto]   [人工] 1 項
[auto] [計] Handle-All 結束 · RoundAll 結束碼 1 · 13 秒(視窗不會關)
[tamper] [RED] boot SHA-256 mismatch - not run
```

## 5. 桌機預期

貼 `VRN2_HandleAll_v0103.md` 最上面那行 → auto → repair → ⑤ 沒有要修的 → 收尾頁用 v0111 重算 → **BLOCKED · VRN-2 0 · VCGC 1 · 人工 2 · 資料源 2**。
