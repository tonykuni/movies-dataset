VRN v0108 完整交接包 — 請先閱讀

不必整包替換正式 VRN／VIA 模組。先解壓到新的獨立資料夾。
原 v0108 放在 pack，保留原始 199 檔與 manifest；54 個既有引擎樹檔案未更動。
新增部署／驗證工具位於根目錄及 tools，不覆寫 pack。

快速使用（Windows / PowerShell 7 / Python 3.12）
1. 開啟 PowerShell，切換到解壓後、包含 RunAndVerify.ps1 的資料夾。
2. 首次執行：
   & .\RunAndVerify.ps1 -InstallDependencies
3. 若找不到 Python：
   & .\RunAndVerify.ps1 -PythonPath 'C:\Users\tonyk\envs\via_vrn_312\Scripts\python.exe' -InstallDependencies
4. 後續執行：
   & .\RunAndVerify.ps1
5. 開啟本次 runs\時間_亂數\RUN_STATUS.json 及 RESULT_VERIFICATION.json。
   只有當次完整驗證成功，才接受 PASS_WITH_SOURCE_LIMITATIONS。

入口會建立獨立 envs\via_vrn_annual_v0108、保存日誌並保持 PowerShell 開啟。
第一次安裝需要可存取套件來源。專用環境不要指向正式 via_core。
Windows／PowerShell 入口未在 Windows 實機測試；Linux Python 流程與驗證器已實測。
新增 RunAnnual_v0108.py 僅適配 ZIP 路徑為正斜線，調用原版主程式；原檔未改。

先看成果，不重跑：
pack\VRN_RealTest_v0104.xlsx：年度還原表、原值、驗算、單位、來源問題。
pack\VRN_AnnualFinancialPages_v0108.pdf：12 頁年度來源裁切。
pack\VRN_ProblemsSolved_v0108.pdf：問題處理與來源限制。
請勿將人工註記存回基準檔；另存副本。

完整操作與下一位 AI／工程師提示詞：
docs\VRN_v0108_Technical_Prompt.pdf — 易讀版。
docs\VRN_v0108_Technical_Prompt.txt — 完整複製／貼上版，含 21 節技術規範及附錄。

可重現基準：9 份報告／12 頁／43 表／4415 格／409 算式 PASS／5462 來源格 PASS。
只取年度。千元先轉百萬元；全部驗算後，整數來源取整數，小數來源取一位。
GS 2028 缺值保持空值（1 項不可算）；CLST 本文 10% 與年度表約 20.0106% 的矛盾保留。
這是固定來源／版面的年度包；不能任意投入新 PDF 就宣稱已支援。
同 PDF 相符不等於官方財報核實；圖片 OCR、NLP 推論與全部加速器未在本批執行。

evidence 保存本次環境、完整性、重跑、負面測試及引擎比較收據。
初次重跑 ZIP 讀回曾失敗，保留失敗收據；重新封裝通過後，再以新增入口重跑驗證。
完整交接檔案雜湊列在 HANDOVER_SHA256.json。原 pack 的 manifest 另行保留。
