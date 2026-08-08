# IT 申請範本 — WorkOps 雲端 Graph/Copilot 選配模組(核准前休眠)

> 平台治理裁決:本模組屬**選配雲端線**,需 Azure Entra ID 憑證與 IT 核准。
> 核准前 WorkOps 全功能維持在地零雲端運作(COM 唯讀 + 本地提示語庫)。
> 本範本整理自 2026/08 操作員提供之參考材料,供向 IT 部門備案申請使用。

## 一、申請信範本(可直接改寫寄出)

主旨:【權限與備案申請】同仁自建 M365 Outlook 郵件自動化處理腳本(Python + Copilot)

收件人:IT 部門 / 資訊資安團隊

您好,為優化日常郵件處理效率,本人規劃以 Python 撰寫自動化腳本,
串接公司現有之 Microsoft 365 Graph API 與 Copilot 模組,
對本人信箱之郵件進行語意分類與回信草稿生成(不自動寄出)。
為符合公司資安規範,特此備案並申請 API 憑證:

1. 軟體架構:本地端(Local)執行之 Python 腳本,不經任何外部第三方雲端平台
   (如 Zapier/Make),資料傳輸均在微軟官方 M365 租戶之 SSL 加密通道內。
2. 申請之 Entra ID 權限範圍(最小權限原則):
   - Mail.Read(或 Mail.ReadWrite)— 僅限申請人本人信箱
   - Copilot 呼叫所需之對應 scope(依租戶版本,如 Copilot.Chat)
3. 安全承諾:
   - Client Secret 僅存於本機環境變數,絕不硬編碼於原始碼
   - 不進行跨租戶或未知外部 IP 連線
   - 草稿一律人工過目後親自寄出,系統不代寄

請協助於 Entra ID 建立 App Registration,並提供 Tenant ID / Client ID。謝謝!

## 二、核准後的本機設定(Windows)

使用者環境變數(編輯系統環境變數 → 使用者變數 → 新增;設定後重開終端機):

| 變數 | 內容 |
|---|---|
| AZURE_TENANT_ID | IT 提供之租戶 ID |
| AZURE_CLIENT_ID | IT 提供之應用程式 ID |
| AZURE_CLIENT_SECRET | IT 核發之密鑰(絕不入 repo) |

驗證:`py -c "import os; print(os.environ.get('AZURE_CLIENT_ID'))"`

## 三、核准後選配之函式庫(現階段不安裝)

`azure-identity`、`msgraph-core`(Graph 呼叫)、`openpyxl`(xlsx 輸出;
本平台現以 CSV 落地,Excel 直開,無需先裝)。

## 四、與本平台紅線之對齊

- 不代寄:雲端線亦僅產草稿;寄出永遠是人。
- 不動原件:Graph 呼叫僅讀取;分類標籤等寫入行為需另案申請並記錄。
- Shadow IT 防治:未備案不啟用;本文件即備案底稿。
