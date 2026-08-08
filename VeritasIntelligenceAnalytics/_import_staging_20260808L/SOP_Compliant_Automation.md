# 合規自動化 SOP:信件自動進追蹤矩陣
版本 v1.0 · 2026-07-13 · 適用:公司 Microsoft 365 環境
原則:不安裝軟體、不寫程式、不碰本機信件檔,全部走微軟官方雲端功能,IT 可稽核。

---

## 方案一(主方案):Power Automate 雲端流程

**適用**:多數 M365 商業帳號內建標準連接器即可,免額外授權。

### 前置(只做一次)
1. 把追蹤表 Excel 放到公司 OneDrive 或 SharePoint(不能放本機桌面)。
2. 開啟該 Excel,選取資料範圍 → 插入 → 表格(Ctrl+T),並在「表格設計」給表格命名(例:`MatrixTable`)。欄位建議:日期、寄件人、主旨、內容摘要、案件編號、狀態、下一步、責任人。
   - 這一步是關鍵:Power Automate 的「新增列」動作只認得「表格」,不認得一般儲存格範圍。

### 建立流程
1. 瀏覽器開 make.powerautomate.com,用公司帳號登入。
2. 建立 → 自動化雲端流程。
3. 觸發器:**When a new email arrives (V3)**(Office 365 Outlook 連接器)。
   - 進階選項 → Subject Filter 填案件關鍵字(例:`India Transfer`)。
   - 若需多個關鍵字,改在觸發器後加「條件」動作,用 `contains` 判斷 Subject。
4. 動作:**Add a row into a table**(Excel Online (Business) 連接器)。
   - Location:OneDrive/SharePoint → 選檔案 → 選表格 `MatrixTable`。
   - 欄位對應:日期 = Received Time / 寄件人 = From / 主旨 = Subject / 內容摘要 = 動態內容 Body(可先接一個「取前 200 字」的運算式:`substring(triggerOutputs()?['body/body'], 0, 200)`,若信件短於 200 字會報錯,穩妥版用 `if(greater(length(...),200), substring(...,0,200), ...)`;嫌麻煩就直接放 Body Preview)/ 狀態 = 新收到 / 責任人 = Chris。
5. 儲存 → 用一封測試信驗證表格有新增列 → 完成。

### 案件編號自動判斷(進階,可後補)
在步驟 4 前加「切換(Switch)」動作,依 Subject 內含的案件代碼(案01–案14 或客戶料號)分派案件編號;比對不到就填 `待歸類`,每天 Review 時人工補上。先求全收,再求精分。

---

## 方案二(備援):Excel Power Query 直連信箱

**技術修正**:Excel 沒有「從 Outlook」選項,正確連接器名稱是 **Microsoft Exchange (Online)**。

1. Excel → 資料 → 取得資料 → 從線上服務 → **從 Microsoft Exchange Online** → 輸入公司信箱地址 → 組織帳戶登入。
2. 導覽器選 **Mail** → 轉換資料,進 Power Query 編輯器。
3. 篩選:Subject 包含關鍵字;DateTimeReceived 介於追蹤區間。只保留需要的欄(Subject / Sender / DateTimeReceived / Body 的 TextBody)。
4. 關閉並載入 → 資料 → 查詢與連線 → 內容:勾「開啟檔案時重新整理」+「每 30 分鐘重新整理」。

**誠實註記**:此連接器在部分企業租戶被系統管理員停用(登入時會直接報權限錯誤)。被停用就用方案一,兩案效果相同,不必兩個都建。

---

## 與既有工具鏈的關係

- 方案一/二負責「信件 → 矩陣資料」的自動搬運(合規、零程式)。
- 先前交付的 `WorkMatrix.xlsx` 欄位結構照用;`Sync-MatrixToOutlook.ps1`(行事曆提醒)屬本機腳本,若公司政策不允許執行 PS 腳本,行事曆提醒改用 Power Automate 加一條流程:**Recurrence(每日 08:30)→ List rows(讀矩陣表)→ 條件(追蹤日=今天)→ Create event (V4)(建立行事曆事件)**——同樣全程合規。需要這條流程的逐步設定,說一聲即補。

## 給 IT 或主管的一句話說明
「使用公司 Microsoft 365 內建的 Power Automate 與 Excel 功能,把專案信件自動整理成追蹤表;資料留在公司 SharePoint,流程有雲端執行紀錄,可隨時稽核。」


---

## 附錄 A:行事曆提醒全合規流程(Power Automate 逐步,替代 PS1)

**前置**:WorkMatrix(v2)放 OneDrive/SharePoint,資料範圍已格式化為命名表格 `MatrixTable`,且含「編號 / 事務名稱 / 追蹤日期 / 狀態 / 提醒已建」五欄(「提醒已建」為新加欄,防重複)。

1. **觸發器**:Recurrence——每日 08:30,時區 `(UTC+08:00) Taipei`。
2. **List rows present in a table**(Excel Online Business):選檔案與 `MatrixTable`。
   - ⚠️ 關鍵:進階選項 **DateTime Format 改為 ISO 8601**——否則 Excel 日期回傳為序號(45xxx),日期比對必失敗。這是本流程最常見的翻車點。
   - Top Count 填 5000(預設 256 會漏列)。
3. **Apply to each**(逐列)內放 **Condition**,AND 三條:
   - `item()?['追蹤日期']` 開頭等於 `convertFromUtc(utcNow(),'Taipei Standard Time','yyyy-MM-dd')`
   - `item()?['狀態']` 不等於 `已完成`
   - `item()?['提醒已建']` 不等於 `V`
4. **Yes 分支 → Create event (V4)**(Office 365 Outlook):
   - Calendar:行事曆;Subject:`concat('[矩陣 ', item()?['編號'], '] 期限前追蹤:', item()?['事務名稱'])`
   - Start:`concat(item()?['追蹤日期'],'T09:00:00')`;End:`...T09:15:00`;Time zone:Taipei Standard Time;Reminder:0 分鐘。
5. **同分支 → Update a row**:Key Column=`編號`,Key Value=`item()?['編號']`,「提醒已建」寫入 `V`(防重複;此欄屬 Chris 自己的矩陣,非主管原表,不違反 0 侵入)。
6. 存檔 → 用一列今天到期的測試資料驗證 → 完成。之後每天 08:30 自動掃描建提醒,全程無腳本、無 IT。
