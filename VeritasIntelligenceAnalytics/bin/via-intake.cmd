@echo off
rem 自動化收編管線:檔名即真理+AST 特徵+URN 賦碼+SSOT 註冊+Add-Only 搬移(dry-run 預設;零刪除;HOLD 候裁)— 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\CGC_MDL057_Intake_v0*.py"') do set "IK=%%f"
py "%~dp0..\supportive modules\registry\%IK%" %*
endlocal
