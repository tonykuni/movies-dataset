# VRN-2 v0132 容器實測紀錄(2026-10-20 · 借不到時說清楚下一步 · 四系統各自獨立)

操作員令:「用中文回復 一路實測修復到底 TEST DEBUG OPTIMIZE … FACILITATE … USER-TEST … ACTIVATE … TILL THEY WORKS PERFECTLY. 授權全自動完成」·
「重申VCGC VRN-1 VRN-2 VDF皆是獨立系統有獨立的MAIN獨立運作互不影響」·「自動完成一切到收尾」。

## 1. 主體不動(逐位元組)

`VRN2_Release_v0132.json` 的內嵌清單與 v0131 比:管理器鏈 v0231 → v0239、ENG397 v0127、ENG062 v0114、獨立驗證器 v0102、U/I 處理器 v0102、
OCR 橋 v0100、規則目錄 **15 支 sha256 全部相同**;換掉的只有工具橋 `VRN2_ToolBridge_v0100.py` → `VRN2_ToolBridge_v0101.py`(v0100 留在原處 · 只增不改)與交接報告 v0132。

## 2. 自測

| 項目 | 結果 |
|---|---|
| 啟動器 `--selftest` | 27 / 27 |
| 工具橋 `VRN2_ToolBridge_v0101.py --selftest` | 15 / 15(多一條:VRN-1 的倉在、那一版沒有工具冊 → 說明裡有 `git switch`,整條指令在啟動器顯示的 260 字內) |

## 3. 沙盒樹(倉內 19 份 PDF · 個股 14)· OCR 隔離環境是真的(Python 3.11 · rapidocr · 只在暫存區)

| 情境 | VRN-1 | 結果 |
|---|---|---|
| A 第 1 次 | 本機 VIA-VDF-VRN 倉 `claude/optimistic-goodall-yhalc5` @ e10679c(工具冊在) | ② 借出工具冊 `section.near` / `ocr.image` 都能用 · ⑦ **14 / 14 全綠**(首頁 14 綠 —— v0131 沙盒沒有 OCR 環境時 MQ-1560 首頁紅)· ⑧ 完成 紅 0 黃 4(v0131:黃 7)· ⑨ 上船 19 檔 · ⑪ 錯值 0(年度數據 4,905:對位 4,378 · 轉置 75 · 子欄 452 · OCR 欄位標 OCR)· ⑫ 綠 事實 4,653 / 4,905 · 年度 1,060 列 · 衝突 18 |
| A 第 2 次 | 同上 | 同 · 新鎖 0 · ⑨ 已是最新 · ⑫ 指紋相同(冪等) |
| B | main 工作樹 62475b0(沒有工具冊) | ⑫ 灰「VRN-1 這一版沒有工具冊(第十三輪起才有)→ cd <倉>; git fetch origin; git switch claude/optimistic-goodall-yhalc5(已合併進 main:git pull)→ 再跑 VRN-2」· VRN-2 照常完成 |
| C | `VIA_VRN2_NO_BORROW=1` | ⑫ 灰「這次不借」· ⑦ 14 / 14 · ⑧ 完成 · ⑪ 錯值 0(VRN-2 單獨運作) |

③ 環境檢查在沙盒是紅(`--no-install` · 加速器要的 7 個套件沒裝 · v0130 / v0131 沙盒同一燈 · 使用者機器 ③ 會補裝)。

**實測抓到、改掉的**:B 的第一版說明把指令放在後面,長路徑時被啟動器那一行的 300 / 260 字上限截在 `git switch claude/opt` → 工具橋改成「短原因 + 指令」、路徑只出現一次(啟動器不改)。

## 4. 一鍵(使用者機器情境 · pwsh 7.4.6)

Downloads 是 **v0131** 啟動器(上次跑的)· 發行夾 `vrn2_release_v0132` 放在 GitHub 分支 · 貼「一行」:一鍵程式碼 SHA-256 相符 → ③ 舊啟動器備份 · 取 v0132(雜湊相符)
→ ①~⑫ → ⑤ 摘要(② 借出工具冊兩支都能用 · ⑧ 本輪完成 紅 0 · ⑪ 錯值 0 · ⑫ PIVOT 綠)→ NEXT 綠。

## 5. 借給 VRN-1(VRN-1 自己的 MAIN 實跑 · 另一團隊的倉)

USER-TEST(照操作員的流程):從 GitHub **全新複製** VIA-VDF-VRN → `git switch claude/optimistic-goodall-yhalc5`(e10679c)→ 操作員入口 `artifacts/VRN-1.ps1`(pwsh)
`check` → GREEN 13 / 13(含 P25 工具冊)· `run --no-cache`(19 份真實 PDF · VRN-2 = 上面 A 跑完的沙盒樹)→

* G23 借到 2 / 2:`section.near` / `ocr.image` 都從 `VRN2_ToolBridge_v0101.py`(sha256 `489c5d5738c7` 與 VRN-2 工具冊相同)
* G21 驗證過的年度數據 1,686 / 1,725(逐欄證實 1,679 · 自動修正 7 · 段落標題剔除 39 —— 借來的段落標題)· 年度財報格 354 / 354 · 代號紀錄 104 / 104
* G22 PIVOT PASS · 指紋 `6a508702ffcf29bf`(與 VRN-1 本機回歸相同)· 收尾 完成 · 複製下來的倉沒有被寫入任何檔(`git status` 乾淨)

## 6. 四系統各自獨立(實測)

* VRN-2 不借(C)→ 照常完成;VRN-1 那一版沒有工具冊(B)→ 照常完成並說下一步。
* VRN-1 關掉借用(`VRN_NO_BORROW=1`)/ VRN-2 不在場 → 19 份真報告 FAIL 0 · 收尾完成(VRN-1 第十四輪紀錄)。
* 借用只讀對方的工具冊與檔(逐檔 sha256)· 不改、不複製、不寫對方的夾 · VCGC / VDF 的檔一個都沒動。
