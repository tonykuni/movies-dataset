# 給 IT 的一封信 — Veritas WorkOps 使用申請(v0100)

> 定位:操作員個人購入之生產力工具,依公司政策送 IT 審查。本文件=可直接寄出的申請信正本
> (整併來源:M365 規劃書 §12 申請信 + v0200 RC IT_GOVERNANCE_HANDOFF + IT_INPUTS_REQUIRED)。
> 使用法:複製「信件正文」段落,填妥【】欄位後寄出。附件建議一併附上本檔全文供 IT 留存。

---

## 信件正文(可直接複製)

主旨:個人生產力工具 Veritas WorkOps 使用申請 — 唯讀郵件整理/追蹤草稿輔助(不代發信)

【IT 部門 / 資安審查窗口】您好:

我是【部門】【姓名】(分機【分機】)。因日常需追蹤大量往來郵件與工作控管表,
我自行購入了本機生產力工具「Veritas WorkOps」,依公司軟體使用政策提出使用申請。
工具的行為邊界如下,請協助審查:

一、目前申請階段(Phase 1 — 本機 COM 唯讀):
1. 僅在我個人工作機上執行(PowerShell/Python 本機程式),無伺服器、無對外服務。
2. 透過 Outlook 桌面版既有登入(COM 介面)「唯讀」讀取郵件標題/寄件人/時間/內文摘要,
   用於整理追蹤清單。不移動、不刪除、不改分類、不標記任何郵件。
3. 絕不代為發送郵件:追蹤信一律只產生「草稿」(.Display/.Save),寄出永遠由我本人按下。
4. 所有資料(索引、報表、備份)只落在本機資料夾;不上傳雲端、不對外連網爬取網站。
5. 憑證機密一律不寫入程式或設定檔(僅環境變數);備份還原只到暫存區,正本零觸碰。

二、未來階段(Phase 2 — Microsoft Graph,先行報備、核准前休眠不啟用):
1. 若公司核准,將申請 Entra 桌面公用程式(public client)委派授權,範圍僅:
   Mail.Read + User.Read(選配草稿功能才需 Mail.ReadWrite);明確「不申請 Mail.Send」。
2. 屆時需要 IT 提供:Client ID、Tenant ID(或核准 authority)、IT 單號/變更參考。
3. 應用綁定 127.0.0.1 本機;MSAL token 快取僅存本機且排除於工具備份之外。
4. 在取得上述核准之前,此線路在工具內為「休眠」狀態,程式不會發出任何 Graph 呼叫。

三、可供審查之佐證(隨信附上或到機檢視):
- 程式碼可全文檢視(無混淆);紅線稽核:全庫無 .Send() 呼叫。
- 一鍵全鏈自測報告 out/selftest_report.json(FinalGate)。
- v0200 RC 治理文件包(IT_GOVERNANCE_HANDOFF.md、TARGET_ACCEPTANCE_CHECKLIST.md、SHA256 清單)。

若審查需要展示或補充任何資訊,我可隨時配合。謝謝!

【姓名】敬上 【日期】

---

## 內部對照(不隨信寄出)

| 紅線 | 落實 |
|---|---|
| 系統不可代為發送 | 全庫 lint:.Send() 零出現;範本一律 .Display()/.Save() |
| 原郵件/分類不改 | COM 唯讀掃描;無 Move/Delete/Categories 寫入 |
| 正本零觸碰 | 還原=out/restore_staging 暫存;canonical_mutation=false |
| 不爬站 | run-local 裁定;機構名取自 FROM 顯示名+網域+URL 網域 |
| 機密只走環境變數 | 設定檔無密碼欄位;Graph 憑證由 IT 發配後亦僅本機 MSAL 快取 |
| Graph 休眠 | 核准前零呼叫;核准後僅 Mail.Read/User.Read(草稿選配 ReadWrite;永不 Send) |
