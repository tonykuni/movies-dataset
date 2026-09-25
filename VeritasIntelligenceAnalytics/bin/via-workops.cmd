@echo off
rem WorkOps × Mail Tracker 統合指揮板 v0104（一系統四頁:專案/追蹤哨/範疇關係人/VMT;負載對照;絕不代寄）
rem 用法:via-workops all               → ONE POWERSHELL:環境自癒+指揮板+深度鏈 全一支（[-Days n] [-SkipDeep] [-NoOpen]）
rem       via-workops                    → 一支到底:掃描+對帳+編號+指揮板+週報+通知+KPI
rem       via-workops silent            → 靜默背景:同上但不開瀏覽器（配 WorkOps_Background.vbs）
rem       via-workops drafts            → 自動佇列（≥3 天未回）一次建草稿
rem       via-workops drafts THR-…,…    → 只為「圈選件」建草稿（板上複製之指令）
rem       via-workops report | ui | Scan|Reconcile|Draft|FollowUp|Templates|All
if "%~1"=="" (
  for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\WorkOps\Invoke-VIA-WorkOps-CommandBoard-v0*.ps1"') do set "WOPS_BOARD=%%f"
  call pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\functional modules\WorkOps\%%WOPS_BOARD%%"
) else if /i "%~1"=="all" (
  for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\WorkOps\Invoke-VIA-WorkOps-All-v0*.ps1"') do set "WOPS_ALL=%%f"
  call pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\functional modules\WorkOps\%%WOPS_ALL%%" %2 %3 %4 %5 %6
) else if /i "%~1"=="drafts" (
  if "%~2"=="" (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\functional modules\WorkOps\Invoke-VeritasMailOps.ps1" -Action FollowUp -RecipientsCsv "%~dp0..\functional modules\WorkOps\out\recipients_auto.csv"
  ) else (
    for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\WorkOps\Invoke-VIA-WorkOps-CommandBoard-v0*.ps1"') do set "WOPS_BOARD=%%f"
    call pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\functional modules\WorkOps\%%WOPS_BOARD%%" -DraftsFor "%~2" -DraftsTemplate "%~3"
  )
) else if /i "%~1"=="silent" (
  for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\WorkOps\Invoke-VIA-WorkOps-CommandBoard-v0*.ps1"') do set "WOPS_BOARD=%%f"
  call pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\functional modules\WorkOps\%%WOPS_BOARD%%" -Silent
) else if /i "%~1"=="deep" (
  for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\WorkOps\engines\Invoke-VIA-WorkOps-Deep-v0*.ps1"') do set "WOPS_DEEP=%%f"
  call pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\functional modules\WorkOps\engines\%%WOPS_DEEP%%" %2 %3 %4 %5 %6 %7 %8 %9
) else if /i "%~1"=="decisions" (
  rem 決策追蹤（ENG-027）:decisions add "決議" 負責人 [截止] [THR-#] [會議碼] / list / start|done|block DEC-# / report / export
  py "%~dp0..\functional modules\WorkOps\engines\VIA_ENG068_WorkopsDecisionLog.py" %2 %3 %4 %5 %6 %7
) else if /i "%~1"=="accuracy" (
  rem Gate E 準確度:accuracy=template 產核對樣板 | accuracy run=Gold Set 實測計分 | accuracy harness=ENG-050 受控驗證
  if /i "%~2"=="harness" (
    py "%~dp0..\functional modules\WorkOps\engines\VIA_ENG059_WorkopsAccuracyHarness.py" %3
  ) else (
    py "%~dp0..\functional modules\WorkOps\engines\workops_accuracy_benchmark.py" %2 %3
  )
) else if /i "%~1"=="commitments" (
  rem ENG-051 承諾追蹤:candidates=候選 accept=納管 create/state/reschedule/fulfill 全人工確認,絕不自動生承諾
  py "%~dp0..\functional modules\WorkOps\engines\workops_commitment_intelligence.py" %2 %3 %4 %5 %6 %7 %8 %9
) else if /i "%~1"=="register" (
  rem ENG-054 統一工作登記簿:唯讀衍生跨帳總表,來源帳本仍為正本
  py "%~dp0..\functional modules\WorkOps\engines\workops_unified_work_register.py"
) else if /i "%~1"=="consistency" (
  rem ENG-052 跨帳一致性守衛:唯讀矛盾報告,絕不自動修
  py "%~dp0..\functional modules\WorkOps\engines\workops_consistency_guard.py"
) else if /i "%~1"=="health" (
  rem ENG-053 可解釋專案健康分:進度加權 + 扣分逐項透明列示
  py "%~dp0..\functional modules\WorkOps\engines\workops_project_health.py"
) else if /i "%~1"=="harvest" (
  rem v0108 回件收割:Downloads/根 → wop_confirm/gold_set/lexicon_review/control_sheet 自動歸位
  for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\WorkOps\Invoke-VIA-WorkOps-All-v0*.ps1"') do set "WOPS_ALL=%%f"
  call pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\functional modules\WorkOps\%%WOPS_ALL%%" -HarvestOnly
) else if /i "%~1"=="ml" (
  rem ENG-055 ML 實驗室:probe=二十庫探測 setup=裝核心 train=詞庫泛化模型 suggest=未解析候選 cluster=聚類提詞 adopt=人核詞寫回 — ML 只建議永不自判
  py "%~dp0..\functional modules\WorkOps\engines\VIA_ENG075_WorkopsMlLab.py" %2
) else if /i "%~1"=="backup" (
  rem L06 安全車道:backup=備份側車正本 | verify=雜湊驗證 | restore=只還原到暫存
  py "%~dp0..\functional modules\WorkOps\engines\VIA_ENG061_WorkopsBackup.py" %2 %3
) else if /i "%~1"=="selftest" (
  rem ENG-032 全鏈自測：沙箱實跑五段，正本零觸碰；FinalGate=PASS 才可宣稱鏈路無誤
  py "%~dp0..\functional modules\WorkOps\engines\VIA_ENG081_WorkopsSelftest.py"
) else if /i "%~1"=="replies" (
  rem M3 回覆解析:replies=parse 三層判讀 | replies status=現況
  py "%~dp0..\functional modules\WorkOps\engines\workops_reply_parser.py" %2
) else if /i "%~1"=="wop" (
  rem WOP 專案歸戶:wop=propose 提議歸戶 | apply 套用確認檔 | list 專案清單 | status 即況 | domains 網域收割
  py "%~dp0..\functional modules\WorkOps\engines\VIA_ENG087_WorkopsWopIdentifier.py" %2 %3
) else if /i "%~1"=="names" (
  rem 命名核對:names propose（提議）| apply（核對表寫回）| add 名稱 關鍵字（自建歸類）| names（現況）
  py "%~dp0..\functional modules\WorkOps\engines\VIA_ENG076_WorkopsNamer.py" %2 %3 %4 %5
) else if /i "%~1"=="slides" (
  rem ENG-033 自動簡報:板資料合成週報 slides;產完自動開啟;Ctrl+P 列印即簡報
  py "%~dp0..\functional modules\WorkOps\engines\VIA_ENG082_WorkopsSlides.py"
  start "" "%~dp0..\functional modules\WorkOps\out\VIA_WorkOps_Slides.html"
) else if /i "%~1"=="mtg" (
  rem ENG-048 會議對帳橋:MeetingLoop 決議→DEC 帳（冪等）· 未完行動→TO-DO 會議行動批;mtg=pull | status
  py "%~dp0..\functional modules\WorkOps\engines\VIA_ENG073_WorkopsMeetingloopBridge.py" %2
) else if /i "%~1"=="todo" (
  rem ENG-046 每日 TO-DO:同類一口氣批次（前日16:00 寄出/11:00 收件/16:00 前急追）+AI 代筆提示
  py "%~dp0..\functional modules\WorkOps\engines\VIA_ENG067_WorkopsDailyTodo.py"
) else if /i "%~1"=="search" (
  rem 統一搜尋（唯讀跨九側車）:search 關鍵字 [關鍵字2]
  py "%~dp0..\functional modules\WorkOps\engines\workops_unified_search.py" %2 %3 %4 %5 %6 %7 %8 %9
) else if /i "%~1"=="milestones" (
  rem 里程碑（append-only）:create WOP-# 名 日期 [--owner] | complete MLS-# [--evidence] | list | status
  py "%~dp0..\functional modules\WorkOps\engines\workops_milestone_manager.py" %2 %3 %4 %5 %6 %7 %8 %9
) else if /i "%~1"=="timeline" (
  rem 時間軸/依賴（下游衝擊）:timeline=build | link MLS-A MLS-B | list
  py "%~dp0..\functional modules\WorkOps\engines\workops_timeline_dependency.py" %2 %3 %4 %5 %6 %7 %8 %9
) else if /i "%~1"=="closure" (
  rem 案件結案智能（絕不自動結案）:closure=build 候選 | confirm WOP-# --reason 事由 | list
  py "%~dp0..\functional modules\WorkOps\engines\workops_closure_intelligence.py" %2 %3 %4 %5 %6 %7 %8 %9
) else if /i "%~1"=="lessons" (
  rem 教訓（人工確認才成立）:lessons=build 候選 | confirm 序號 --root-cause X --prevention Y | list
  py "%~dp0..\functional modules\WorkOps\engines\workops_lesson_learned.py" %2 %3 %4 %5 %6 %7 %8 %9
) else if /i "%~1"=="retention" (
  rem 保留政策（PLAN 先行;apply 三重門）:retention=plan | apply --confirm | log
  py "%~dp0..\functional modules\WorkOps\engines\workops_retention_manager.py" %2 %3 %4 %5 %6 %7 %8 %9
) else if /i "%~1"=="onboard" (
  rem 首跑導入狀態機（唯讀,由真實產物推導八步）
  py "%~dp0..\functional modules\WorkOps\engines\workops_onboarding.py" %2 %3 %4 %5 %6 %7 %8 %9
) else if /i "%~1"=="auditpack" (
  rem ENG-036 稽核包:全系統證據+現場紅線掃描 → 帶 sha256 manifest 之 zip（IT/主管交件）
  py "%~dp0..\functional modules\WorkOps\engines\VIA_ENG060_WorkopsAuditBundle.py"
) else if /i "%~1"=="matrix" (
  rem ENG-037 總結矩陣:成果×側車×DB 全盤點 → out\VIA_Summary_Matrix.html;產完自動開啟
  py "%~dp0..\functional modules\WorkOps\engines\VIA_ENG083_WorkopsSummaryMatrix.py"
  start "" "%~dp0..\functional modules\WorkOps\out\VIA_Summary_Matrix.html"
) else if /i "%~1"=="vtr" (
  rem VTR 會議紀錄修復引擎:裸打=All 全套驗證;Doctor Lexicon Test Manifest Restore Inspect Replay 傳遞
  pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\functional modules\WorkOps\VTR\Invoke-VTR.ps1" %2 %3 %4 %5 %6 %7 %8 %9
) else if /i "%~1"=="bridge" (
  py "%~dp0..\functional modules\WorkOps\engines\VIA_ENG066_WorkopsCorpusBridge.py" %2 %3 %4 %5 %6
) else if /i "%~1"=="engine" (
  shift
  py "%~dp0..\functional modules\WorkOps\engines\VIA_ENG056_EmailSuperEngine.py" %2 %3 %4 %5 %6 %7 %8 %9
) else if /i "%~1"=="pmsetup" (
  for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\WorkOps\engines\Invoke-VIA-WorkOps-PmSetup-v0*.ps1"') do set "WOPS_PMS=%%f"
  call pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\functional modules\WorkOps\engines\%%WOPS_PMS%%" %2
) else if /i "%~1"=="workbench" (
  rem 智慧工作台（Forge 前端 12 分頁 × 真後端 19 端點）:起本機服務並開瀏覽器,同 via-forge
  pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\supportive modules\VIA_Forge\Start-VIA.ps1"
) else if /i "%~1"=="dotsetup" (
  rem graphviz 可攜式取得（免 winget/管理員）:via-workops dotsetup → 狀態;dotsetup install → 下載+驗證+解壓
  py "%~dp0..\functional modules\WorkOps\engines\VIA_ENG070_WorkopsGraphvizSetup.py" %2 %3
) else if /i "%~1"=="envmgr" (
  rem 中央環境治理直達:via-workops envmgr health | plan pm4py | install pm4py --wheels-only
  py "%~dp0..\functional modules\WorkOps\engines\VIA_ENG069_WorkopsEnvmanagerBridge.py" %2 %3 %4 %5 %6
) else if /i "%~1"=="analytics" (
  if exist "%~dp0..\functional modules\WorkOps\engines\.venv_pm\Scripts\python.exe" (
    "%~dp0..\functional modules\WorkOps\engines\.venv_pm\Scripts\python.exe" "%~dp0..\functional modules\WorkOps\engines\VIA_ENG057_EngineAnalytics.py" %2 %3 %4 %5
  ) else (
    py "%~dp0..\functional modules\WorkOps\engines\VIA_ENG057_EngineAnalytics.py" %2 %3 %4 %5
  )
) else if /i "%~1"=="actiondb" (
  py "%~dp0..\functional modules\WorkOps\engines\VIA_ENG055_EmailActionDb.py" %2 %3 %4 %5
) else if /i "%~1"=="scanrange" (
  pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\functional modules\WorkOps\engines\Invoke-VIA-Outlook-TimeRange-ReadOnly.ps1" %2 %3 %4 %5 %6
) else if /i "%~1"=="matrixsync" (
  rem 注意:此工具會「建立」Outlook 行事曆事件（使用者主動觸發之寫入;郵件/分類仍零觸碰）
  pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\functional modules\WorkOps\engines\Sync-MatrixToOutlook.ps1" %2 %3 %4
) else if /i "%~1"=="note" (
  rem VIA Note Pro 單機筆記（FNT-001）:雙擊即用,資料全在瀏覽器 localStorage;同 via-note
  for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\VAP\spec\UIUX_Design_Source\VIA_Note_Pro_Standalone*.html"') do set "WOPS_NOTE=%%f"
  call start "" "%~dp0..\functional modules\VAP\spec\UIUX_Design_Source\%%WOPS_NOTE%%"
) else if /i "%~1"=="help" (
  echo ============================================================
  echo  via-workops 動詞總表（重串接後全系統）
  echo ============================================================
  echo  ^(裸打^)      指揮板一支到底:掃描+對帳+編號+六頁板+週報+KPI
  echo  all          總指揮:環境自癒 - 指揮板 - 深度鏈 - 總結表 [-Days n] [-SkipDeep] [-NoOpen]
  echo  deep         深度鏈 [-Days n] [-StartDate yyyy-MM-dd] [-EndDate yyyy-MM-dd]（尾端自動命名提議）
  echo  accuracy     準確度:template=產樣板 run=Gold Set 實測 harness=受控驗證（ENG-050）
  echo  commitments  承諾追蹤（ENG-051）:candidates accept 候選ID create state reschedule fulfill
  echo  register     統一工作登記簿（ENG-054）:唯讀跨帳總表 JSON+CSV
  echo  consistency  跨帳一致性守衛（ENG-052）:唯讀矛盾報告不自動修
  echo  health       可解釋專案健康分（ENG-053）:進度+扣分透明列示
  echo  ml           ML 實驗室（ENG-055）:probe setup train suggest cluster adopt — 只建議不自判
  echo  harvest      回件收割:Downloads/根的確認檔·Gold Set·詞庫表·控管表自動歸位
  echo  backup       備份/驗證/還原到暫存:backup verify restore
  echo  selftest     全鏈自測（ENG-032）:沙箱實跑 命名-歸戶-回覆-準確度-會議決策-備份 六段
  echo  replies      M3 回覆解析:replies=三層判讀 status=現況
  echo  wop          WOP 專案歸戶:wop=提議歸戶 apply=套用確認 domains=網域收割 list=清單 status=即況
  echo  names        命名核對:names=現況 propose=提議 apply=核對寫回 add 名稱 關鍵字=自建歸類
  echo  workbench    智慧工作台（Forge 12 分頁,共用語料,起本機服務）
  echo  pmsetup      隔離 venv 安裝 pm4py 全家（經 EnvManager 中央治理;-Recreate 重建）
  echo  envmgr       中央環境治理:envmgr=健檢 plan 套件=決策 install 套件 --wheels-only=執行
  echo  dotsetup     graphviz 可攜版:dotsetup=狀態 install=下載+sha256+解壓（免 winget）
  echo  drafts       追蹤草稿:drafts=自動佇列 drafts THR-...=圈選件 [第三參數=範本鍵]（絕不代寄）
  echo  silent       靜默一支到底（不開瀏覽器;配開機 vbs）
  echo  report       開週報   ui  開單機板   scanrange  時段唯讀掃描
  echo  bridge       語料橋   engine  超級引擎   analytics  分析層   actiondb  行動庫
  echo  mtg          會議對帳橋（ENG-048）:MeetingLoop 決議入 DEC 帳、行動入 TO-DO 批
  echo  todo         每日 TO-DO（ENG-046）:三時間錨批次+AI 代筆提示（寄出永遠人按）
  echo  search       統一搜尋:search 關鍵字（跨九側車唯讀）
  echo  milestones   里程碑:create/complete/list/status（MLS-# 永不變）
  echo  timeline     時間軸+下游衝擊:build/link/list（A 逾期即列受阻 B）
  echo  closure      案件結案:build 候選/confirm 顯式結案（絕不自動結案）
  echo  lessons      教訓:build 候選/confirm 補根因預防才成立（LLN-#）
  echo  retention    保留政策:plan 零刪除/apply --confirm 三重門
  echo  onboard      首跑導入八步狀態（由真實產物推導）
  echo  auditpack    稽核包（ENG-036）:證據彙整+現場紅線掃描 → 帶雜湊 zip 交件
  echo  matrix       總結矩陣（ENG-037）:成果×側車×DB 全盤點 HTML
  echo  slides       自動簡報（ENG-033）:板資料合成週報投影片,Ctrl+P 列印即簡報
  echo  vtr          會議紀錄修復引擎（VTR 子系統）:裸打=全套驗證 Restore=修逐字稿 Inspect=待裁決
  echo  note         VIA Note Pro 單機筆記（FNT-001）:雙擊即開,資料在本機瀏覽器
  echo  matrixsync   WorkMatrix 到行事曆（唯一寫入,主動觸發）
  echo  Scan/Reconcile/Draft/FollowUp/Templates/All  MailOps v001 傳遞
) else if /i "%~1"=="report" (
  start "" "%~dp0..\VIA_Reports\workops_run\VIA_WorkOps_WeeklyReport.html"
) else if /i "%~1"=="ui" (
  for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\WorkOps\Veritas_MailOps_Standalone*.html"') do set "WOPS_UI=%%f"
  call start "" "%~dp0..\functional modules\WorkOps\%%WOPS_UI%%"
) else (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\functional modules\WorkOps\Invoke-VeritasMailOps.ps1" -Action %1
)
