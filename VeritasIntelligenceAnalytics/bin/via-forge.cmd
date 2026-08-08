@echo off
rem VIA_Forge v002(啟動線修正):裸打改起「活」工作台 — 本機服務+瀏覽器,前端 19 端點全接真後端
rem 背景:v001 裸打開 ui\index.html(file://)→ fetch 不到後端,永遠「後端離線(示範資料)」,
rem       操作員誤判功能缺失(附件 hash 與庫內 UI 逐位元組相同,功能本在,只缺這一吋啟動線)。
rem 用法:via-forge         → Start-VIA.ps1 起 127.0.0.1 服務並自動開瀏覽器(一點直入,全功能)
rem       via-forge check  → via_checkmatrix.py 45 項驗收
rem       via-forge server → 同裸打,參數透傳(-NoBrowser -SkipDeps -SelfTestOnly)
rem       via-forge file   → 舊行為:直接開 ui\index.html(離線殼,只增不減保留)
rem 回退:rem 掉裸打分支改回 start ui\index.html 即 v001 行為
if "%~1"=="" (
  pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\supportive modules\VIA_Forge\Start-VIA.ps1"
) else if /i "%~1"=="check" (
  py "%~dp0..\supportive modules\VIA_Forge\via_checkmatrix.py"
) else if /i "%~1"=="server" (
  shift
  pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\supportive modules\VIA_Forge\Start-VIA.ps1" %2 %3 %4
) else if /i "%~1"=="file" (
  start "" "%~dp0..\supportive modules\VIA_Forge\ui\index.html"
) else (
  echo 用法: via-forge ^| via-forge check ^| via-forge server [-NoBrowser -SkipDeps -SelfTestOnly] ^| via-forge file
)
