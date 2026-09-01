@echo off
rem =====================================================================
rem VIA-ALL.cmd - 萬用總門(批261;cmd/PowerShell/雙擊三通)
rem =====================================================================
rem 批261 總根因:操作員終端有時是 cmd 有時是 pwsh——PS 語法一行
rem (Sort-Object/分號串接/2>$null)在 cmd 全滅=歷來「指令不識/
rem unknown switch」實錄的唯一共因。
rem 本檔=純 cmd 語法,任何殼任何方式(打路徑/雙擊/捷徑)都通:
rem   自動找 pwsh(缺=退 powershell)-> 跑 Invoke-VIA-All 尾版
rem   (它自己會 pull 同步+點源短指令+全背景派工=零卡斷)
rem =====================================================================
setlocal
set "VIA=%~dp0"

rem --- 批269 前置自癒:髒樹全收留痕(stash -u;乾淨=無事退出) --------
rem 實錄根因:工作站本機分流提交+執行期再生存證檔=每次 pull 被
rem 「local changes would be overwritten」擋死;連同步修好版都拉不到
rem =雞生蛋死鎖。本門先 stash 再派工=任何狀態都能同步(找回:git stash pop)
git -C "%VIA%.." stash push --include-untracked -m "VIA-selfheal-preclean" >nul 2>nul

rem --- 尾版解析 Invoke-VIA-All-v*.ps1(cmd 版尾版 glob) ---------------
set "ALLPS="
for /f "delims=" %%f in ('dir /b /o:n "%VIA%Invoke-VIA-All-v*.ps1" 2^>nul') do set "ALLPS=%VIA%%%f"
if not defined ALLPS (
    echo [VIA-ALL] Invoke-VIA-All 缺 - 先同步一次...
    git -C "%VIA%.." -c core.editor=true pull --no-edit origin main
    for /f "delims=" %%f in ('dir /b /o:n "%VIA%Invoke-VIA-All-v*.ps1" 2^>nul') do set "ALLPS=%VIA%%%f"
)
if not defined ALLPS (
    echo [VIA-ALL] 同步後仍缺=誠實停(檢查網路後重跑本檔)
    exit /b 2
)

rem --- pwsh 優先,缺=退 powershell(兩者必有其一) ----------------------
where pwsh >nul 2>nul
if %errorlevel%==0 (
    pwsh -NoProfile -ExecutionPolicy Bypass -File "%ALLPS%"
) else (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%ALLPS%"
)
exit /b %errorlevel%
