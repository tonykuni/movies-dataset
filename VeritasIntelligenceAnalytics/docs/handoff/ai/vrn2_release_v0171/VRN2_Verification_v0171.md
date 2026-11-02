# VRN-2 v0171 驗證紀錄(2026-11-02 · 已合併 PR 整併 · 兩線版號對照 · 貼回包去重 · 套件 v0170 不動 · RoundAll v0127 · Handle-All v0119)

## 1. 桌機 2026-11-02 15:18(v0170 整輪 · 閘開)——「開閘共識欄」做到了

| 項目 | 結果 |
|---|---|
| ⑥f 共識 | 真抓 **41 / 41**(兩輪重試後,只剩 404 的 4171 / 6933 依 v0102 規則不納入閘 → PASS_WITH_WARNINGS)· rc 0 |
| Combined 共識欄 | 52 列:FactSet 中位數 **49** · Yahoo 中位數 **48** · 調整後目標價 42 · EPS 格 137(空格全是來源面:404 兩檔 · AAPL 非台股 · 原文沒目標價)|
| Workbench | **v0105(前版 v0104)** 渲染成功 —— 動態前版尾在桌機接上另一線的 v0104,緊湊 / 白字 / 欄寬自動 / 資料驗證燈 / 共識面板都上線 |
| 快照補位 | 這輪**用不到**(閘開 · 真抓);它仍是閘關輪次的後備 |
| 收尾 | REVIEW · **VRN-2 0 · VCGC 0** · 人工 1(MQ-1560 四點 `--confirm H-fd2ea35f`)· 資料源 3(VDF rc 2 PARTIAL · 404 / AAPL / 原文沒目標價)|

## 2. 「很多問題昨天就已經解決但又出現了」——全景根因

1. **VRN-2 有兩條工作線,v0124 之後各自編號。** main(經 PR #584 / #585 併入 · 分支 claude/vrn2-closeout-authorization-y4ixl7)上的
   `VRN2_RoundAll_v0124–v0126`、`Handle-All v0116–v0118`、`runtime v0160`、`套件 v0169` 是**另一線**(Workbench v0103 / v0104 ·
   VeritasReportNova 標題 · 印章 logo)的正本——跟本線**同名不同內容**。兩線各修各的,操作員貼到哪一線的一行,就只帶那一線的修法
   → 另一線已解決的,換線跑就「又出現」(例:Handle-All REVIEW 顏色紅字,本線 v0116 修過、另一線 v0117 當時還沒修,04:24 跑到另一線的就又見到)。
2. **桌機倉落後 GitHub 甚多**(另一線收尾報告原文:719 個提交 · 另有 2 個沒推 · `pull --ff-only` 一直不成功)→ 已合併的 VDF / VCGC /
   Workbench 修正到不了桌機本地樹(VDF 尾版停在 v0162,GitHub 已 v0166+)→ VDF 紅字(04:35 rc 1)這類問題反覆出現。
   本線取檔用 `git fetch + git show`(不靠本地樹)所以不受影響。

## 3. 本輪整併(操作員:「查 GITHUB 已經整合的 PR 將問題全部解決」)

- **origin/main 併入本分支**(commit 見 git log):19 個衝突(本線 v0168 / v0169 發行夾 + 交接 v0169 / v0170 被另一線同名改寫)
  **一律保留本線正本**;另一線的檔(含 Workbench v0103 / v0104 原始碼 · 套件 v0169 · SettleAll v0100 / v0101 · FreezeLock v0100–v0103)
  與 VDF / VCGC 的已合併修正**原樣帶入** · 刪 0 檔 · 本線 vrn2_release_v0170 未動。
- **RoundAll v0127**:移植另一線 v0126 的貼回包逐檔去重(先後照舊 · 防 Duplicate name 警告)· 版號直接跳過兩線相撞的 v0126 · 自測 94 項全過。
- **Handle-All v0119**:指到 v0127 · 其餘不動。套件 v0170 不動(雜湊照釘)。
- **版號規則(以後都照)**:出任何 VRN-2 新版號前先查本分支與 main 兩邊;本線下一版 RoundAll v0128+ · Handle-All v0120+ ·
  **Workbench v0107+**(桌機加速器已自動生成 v0106 = v0105 + 標記;本線新版要自帶 `[VIA:ACCEL-BRIDGE:v0111]` 標記)· runtime v0162+。
- 另一線 v0104 的 `render(root, out_path, logo, assets_zip)` 簽章與本線 v0102 相同(已從 main 取原始碼核對;桌機 15:18 實跑也已證明)。

## 4. 測試

| 項目 | 結果 |
|---|---|
| RoundAll v0127 自測 | [PASS] VRN2_RoundAll v0127 --selftest · 94 項 · 不過 0 |
| PowerShell 剖析 | pwsh 7.4.6 剖析錯 [0, 0, 0, 0, 0] · Handle-All 一行 = 可讀版 True · 開機行 = 可讀版 True |
| e2e(最短一行 · 沙盒)| auto1 rc 0 · confirm list rc 0 · auto2 rc 0 · tamper rc 0 · auto 整輪 → repair → 竄改開機檔不執行 · 收尾狀態 {"auto1": {"state": "OPEN", "per_owner": {"VCGC": 8, "人工": 10, "VRN-2": 3}}, "auto2": {"state": "OPEN", "per_owner": {"VCGC": 6, "VRN-2": 3, "人工": 8}}} · 貼回包檔名無重複 · Workbench v0105 面板在 |

## 5. 桌機下一步(收尾只剩兩件 · 都在操作員手上)

1. 貼 `vrn2_release_v0171/VRN2_HandleAll_v0119.md` 的最短一行(auto = repair · 幾分鐘)→ 收尾頁應維持 REVIEW(VRN-2 0 · VCGC 0)。
2. 看過 MQ-1560 原圖四點後:`python "%USERPROFILE%\\Downloads\\VRN2_RoundAll_v0127.py" --confirm H-fd2ea35f --note "…"`(只有操作員打才算)
   → 收尾轉 **DATA_GAP(只剩資料源)= VRN-2 側終點**。
3. (共用倉 · 非 VRN-2)桌機要吃到已合併的 VDF / VCGC 修正:照 main `VRN2_Handover_latest.md` 第 13 節 SettleAll v0101 的一行做合併式同步。

## 6. 沒做 / 待辦

- 操作員的 `--confirm` 不代打(v0165 規則)· 同意閘不代設。
- 3014TT 四點(第 2 點從句中開始 · 第 1 / 3 點重複)與 MQ-1560 OCR 字詞錯(chi players 應為 chip layers)照舊等操作員點頭(要改摘要器 + 整輪)。
