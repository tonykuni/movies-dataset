@echo off
rem VIA BoardQA — 指揮板四層測試(unit/integration/system/design-sync;缺工具誠實 SKIP)
rem 用法:via-boardqa(動態解析最新板;報告落 WorkOps\out\board_qa_report.json)
py "%~dp0..\functional modules\WorkOps\qa\board_qa.py" %*
