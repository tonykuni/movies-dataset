@echo off
rem 中英文字庫+知識樹引擎:--build 建庫 / --ingest 讀報建構 / --ask 詢問 / --tree 樹枝編號 / --template 模板 / --merge 回填 / --review 審核 — 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\VRN\VRN_ENG063_Lexicon_v0*.py"') do set "LX=%%f"
py "%~dp0..\functional modules\VRN\%LX%" %*
endlocal
