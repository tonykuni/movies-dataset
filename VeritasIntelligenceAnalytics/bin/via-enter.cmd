@echo off
rem 進入 via_core 環境(快速道):落位正典+git pull+三層母根指標+VIA_PYTHON+動詞可達+存證 — 動態解析最新版(鐵律)
rem 注意:cmd 殼呼叫時環境變數/cwd 只影響子行程;要讓「當前 PowerShell 視窗」進場,請直接以 & 呼叫 ps1(用法見腳本檔頭)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\Invoke-VIA-Enter-v0*.ps1"') do set "EN=%%f"
pwsh -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\supportive modules\registry\%EN%" %*
endlocal
