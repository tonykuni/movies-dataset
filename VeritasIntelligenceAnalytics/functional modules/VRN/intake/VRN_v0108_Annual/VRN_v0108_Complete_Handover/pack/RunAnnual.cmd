@echo off
cd /d "%~dp0"
python -X utf8 VRN_AnnualFinancial_v0108.py --dispatcher-root engine --input-root inputs --output-root rerun_output
pause
