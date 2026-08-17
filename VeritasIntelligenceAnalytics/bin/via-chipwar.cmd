@echo off
rem 籌碼戰整合主控台(六引擎:GovFund/SectorWhale/FinMind/Rotation/MarginFOMO/Strategy;全免費源;test→consolidate→usertest→activate 循環)
setlocal
pushd "%~dp0..\functional modules\ChipWar\engines"
py VIA_ChipWar_Console_v010.py %*
popd
endlocal
