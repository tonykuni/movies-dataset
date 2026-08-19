@echo off
rem VIA 指揮中心(TOOL-074):多矩陣一頁 U/I——狀態燈/引擎樹/VRN·VDF·VAP·FLOW 結果區/操作面(一鍵複製指令)— 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\via_command_center_v0*.py"') do set "CC=%%f"
py "%~dp0..\supportive modules\registry\%CC%" %*
endlocal
