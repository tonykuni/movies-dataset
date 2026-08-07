Veritas MailOps · 追蹤信範本引擎 (Tracking-Draft Template Engine)
================================================================

這支工具幫你「一鍵批次擬好追蹤信草稿」。每封信內建「預填答案表」——
收件人照格子填，回覆就不會漏掉狀態 / ETA / 阻礙。你檢視、最少幅度修改後，
自己按「傳送」。

核心原則(和 SafeLocal 同一條線)
--------------------------------
- 只建立「草稿」，開啟供你檢視後由你本人手動寄出。絕不自動寄信。
- 不讀取、不搬移、不刪除、不修改任何既有郵件。
- 不連網、不用 Graph/API、不排程、不改登錄檔、不要求系統管理員。
- 不壓制、不繞過 Outlook 安全提示。COM 被公司封鎖就停，不繞過。

怎麼用(三步)
------------
1. 開啟並登入 Classic Outlook for Windows(不是「新版 Outlook」)。

2. 第一次:雙擊 START_TrackingDrafts.cmd(或用下面的 powershell 指令)。
   它會在腳本旁自動建立:
     templates\  (4 個範本 HTML: 進度 / 交期 / 風險 / 核准)
     recipients.csv  (收件人清單範例)
   然後結束。

3. 編輯 recipients.csv 填你要追蹤的專案與收件人:
     ProjectCode,ProjectName,To,Cc,Template
     PRJ-001,日本合資案,someone@example.com,,status_request
   欄位說明:
     - Template 可填: status_request / eta_confirm / blocker_check / approval_request
       (留空則用預設 status_request)
     - Cc 可留空
     - 你可以自己在 CSV 多加欄位，範本裡用 {{欄位名}} 就會自動代入

4. 再執行一次 START_TrackingDrafts.cmd。
   每一列會建立一封草稿並開啟撰寫視窗，你檢視 → 微調 → 自己按「傳送」。

大量寄送(可選)
--------------
若要追蹤的專案很多，不想一次跳出很多視窗，改用「靜靜存到草稿匣」模式:
  powershell.exe -NoProfile -ExecutionPolicy Bypass -STA -File ".\Invoke-VeritasMailOps-TrackingDrafts.ps1" -OpenMode Save -MyName "你的名字"
跑完會自動打開「草稿匣」，你在裡面逐封檢視後傳送。草稿都會貼上分類標籤 VIA_Tracking，方便篩選。

補追殺(FollowUp)
--------------
對還沒回你的專案再追一次:
  powershell.exe -NoProfile -ExecutionPolicy Bypass -STA -File ".\Invoke-VeritasMailOps-TrackingDrafts.ps1" -Mode FollowUp
沒填 Template 的列會自動用「followup」範本(語氣:尚未收到回覆,再麻煩圈選)。
想更急的語氣,把該列 Template 填「followup_firm」。一樣只建草稿、你自己按傳送。

選擇題式必回內容
--------------
範本的答案表已經是「○ 圈選」式,對方多半只要保留適用項、幾乎免打字:
  1. 狀態： ○進行中 ○已完成 ○卡關
  2. 完成度： ○25% ○50% ○75% ○100%
  3. ETA： ○今日 ○明日 ○本週 ○其他:____
  4. 阻礙： ○無 ○有:____
  5. 需協助： ○否 ○是:____
要改選項就直接編輯 templates\TPL_*.html。

一鍵工作台(選用)
--------------
把 START_Veritas_MailOps.cmd 跟這些檔案、SafeLocal 掃描腳本、Dashboard HTML 放同一資料夾,
雙擊它會出現選單:掃描信箱→開結果資料夾→開 Dashboard、或建立/補追殺草稿,都在一處。
(瀏覽器安全限制:本機網頁不能自動讀硬碟,所以掃描後仍需把 JSON 拖進 Dashboard 一次。)

參數(可選)
----------
  -MyName "你的名字"          署名(預設 Tony Huang)
  -OpenMode Display|Save     Display=逐封開視窗檢視(預設) / Save=存草稿匣
  -Mode Initial|FollowUp     Initial=初次追蹤(預設) / FollowUp=補追殺
  -DefaultTemplate status_request   CSV 沒填 Template 時的預設
  -TemplateDir / -RecipientsCsv     自訂範本資料夾 / 清單路徑

範本怎麼改
----------
templates\TPL_*.html 就是純 HTML，可直接用記事本改。
- 第一行的  <!-- SUBJECT: ... -->  就是信件主旨，可含 {{變數}}。
- 內文的「請直接在下方填寫並回覆」表格就是預填答案表，想加減欄位自己改。
- 可用變數: {{ProjectCode}} {{ProjectName}} {{MyName}} {{Date}} + recipients.csv 任一欄位。

閉環搭配
--------
發出去 → 對方照表回覆 → 你用 SafeLocal / Outlook Wizard 掃描分類 →
匯出 JSON → 用 Veritas_MailOps_Standalone.html 的「📁 本機匯出」載入 →
「生成簡報」出一份專業投影片(可列印 / 存 PDF)。全程你自己的資料、你自己的機器、離線。

已驗證 / 未驗證(誠實交代)
------------------------
已驗證(在 Linux PowerShell 7 實跑):語法解析 0 錯誤;範本自動建立、變數代入、
主旨產生全部正確。
未驗證(這裡沒有 Windows / Outlook 可測):實際的 Outlook COM 建立草稿、開啟視窗、
存草稿匣。這些要在你有 Classic Outlook 的 Windows 上第一次跑時確認。
