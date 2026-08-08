@echo off
rem WorkOps × Mail Tracker 統合指揮板 v0104(一系統四頁:專案/追蹤哨/範疇關係人/VMT;負載對照;絕不代寄)
rem 用法:via-workops all               → ONE POWERSHELL:環境自癒+指揮板+深度鏈 全一支([-Days n] [-SkipDeep] [-NoOpen])
rem       via-workops                    → 一支到底:掃描+對帳+編號+指揮板+週報+通知+KPI
rem       via-workops silent            → 靜默背景:同上但不開瀏覽器(配 WorkOps_Background.vbs)
rem       via-workops drafts            → 自動佇列(≥3 天未回)一次建草稿
rem       via-workops drafts THR-…,…    → 只為「圈選件」建草稿(板上複製之指令)
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
  py "%~dp0..\functional modules\WorkOps\engines\workops_decision_log.py" %2 %3 %4 %5 %6 %7
) else if /i "%~1"=="names" (
  rem 命名核對:names propose(提議)| apply(核對表寫回)| add 名稱 關鍵字(自建歸類)| names(現況)
  py "%~dp0..\functional modules\WorkOps\engines\workops_namer.py" %2 %3 %4 %5
) else if /i "%~1"=="bridge" (
  py "%~dp0..\functional modules\WorkOps\engines\workops_corpus_bridge.py" %2 %3 %4 %5 %6
) else if /i "%~1"=="engine" (
  shift
  py "%~dp0..\functional modules\WorkOps\engines\email_super_engine.py" %2 %3 %4 %5 %6 %7 %8 %9
) else if /i "%~1"=="pmsetup" (
  for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\WorkOps\engines\Invoke-VIA-WorkOps-PmSetup-v0*.ps1"') do set "WOPS_PMS=%%f"
  call pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\functional modules\WorkOps\engines\%%WOPS_PMS%%" %2
) else if /i "%~1"=="workbench" (
  rem 智慧工作台(Forge 前端 12 分頁 × 真後端 19 端點):起本機服務並開瀏覽器,同 via-forge
  pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\supportive modules\VIA_Forge\Start-VIA.ps1"
) else if /i "%~1"=="dotsetup" (
  rem graphviz 可攜式取得(免 winget/管理員):via-workops dotsetup → 狀態;dotsetup install → 下載+驗證+解壓
  py "%~dp0..\functional modules\WorkOps\engines\workops_graphviz_setup.py" %2 %3
) else if /i "%~1"=="envmgr" (
  rem 中央環境治理直達:via-workops envmgr health | plan pm4py | install pm4py --wheels-only
  py "%~dp0..\functional modules\WorkOps\engines\workops_envmanager_bridge.py" %2 %3 %4 %5 %6
) else if /i "%~1"=="analytics" (
  if exist "%~dp0..\functional modules\WorkOps\engines\.venv_pm\Scripts\python.exe" (
    "%~dp0..\functional modules\WorkOps\engines\.venv_pm\Scripts\python.exe" "%~dp0..\functional modules\WorkOps\engines\engine_analytics.py" %2 %3 %4 %5
  ) else (
    py "%~dp0..\functional modules\WorkOps\engines\engine_analytics.py" %2 %3 %4 %5
  )
) else if /i "%~1"=="actiondb" (
  py "%~dp0..\functional modules\WorkOps\engines\email_action_db.py" %2 %3 %4 %5
) else if /i "%~1"=="scanrange" (
  pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\functional modules\WorkOps\engines\Invoke-VIA-Outlook-TimeRange-ReadOnly.ps1" %2 %3 %4 %5 %6
) else if /i "%~1"=="matrixsync" (
  rem 注意:此工具會「建立」Outlook 行事曆事件(使用者主動觸發之寫入;郵件/分類仍零觸碰)
  pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\functional modules\WorkOps\engines\Sync-MatrixToOutlook.ps1" %2 %3 %4
) else if /i "%~1"=="help" (
  echo ============================================================
  echo  via-workops 動詞總表（重串接後全系統）
  echo ============================================================
  echo  ^(裸打^)      指揮板一支到底:掃描+對帳+編號+六頁板+週報+KPI
  echo  all          總指揮:環境自癒 - 指揮板 - 深度鏈 - 總結表 [-Days n] [-SkipDeep] [-NoOpen]
  echo  deep         深度鏈 [-Days n] [-StartDate yyyy-MM-dd] [-EndDate yyyy-MM-dd]（尾端自動命名提議）
  echo  names        命名核對:names=現況 propose=提議 apply=核對寫回 add 名稱 關鍵字=自建歸類
  echo  workbench    智慧工作台（Forge 12 分頁,共用語料,起本機服務）
  echo  pmsetup      隔離 venv 安裝 pm4py 全家（經 EnvManager 中央治理;-Recreate 重建）
  echo  envmgr       中央環境治理:envmgr=健檢 plan 套件=決策 install 套件 --wheels-only=執行
  echo  dotsetup     graphviz 可攜版:dotsetup=狀態 install=下載+sha256+解壓（免 winget）
  echo  drafts       追蹤草稿:drafts=自動佇列 drafts THR-...=圈選件 [第三參數=範本鍵]（絕不代寄）
  echo  silent       靜默一支到底（不開瀏覽器;配開機 vbs）
  echo  report       開週報   ui  開單機板   scanrange  時段唯讀掃描
  echo  bridge       語料橋   engine  超級引擎   analytics  分析層   actiondb  行動庫
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
