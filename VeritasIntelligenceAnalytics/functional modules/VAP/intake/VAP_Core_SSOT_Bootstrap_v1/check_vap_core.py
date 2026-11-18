from pathlib import Path
import json
import sys
import unittest
from datetime import datetime, timezone
from vap_core import VAPContracts

root=Path(__file__).resolve().parent
out=root/'core_validation';out.mkdir(exist_ok=True)
suite=unittest.defaultTestLoader.discover(str(root/'tests_core'),pattern='test_*.py')
result=unittest.TextTestRunner(verbosity=2).run(suite)
core=VAPContracts(root)
report=core.report()
report['tested_at_utc']=datetime.now(timezone.utc).isoformat()
report['tests']={'total':result.testsRun,'passed':result.testsRun-len(result.failures)-len(result.errors),'failed':len(result.failures),'errors':len(result.errors),'successful':result.wasSuccessful()}
(out/'core_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(out/'test_result.md').write_text('# VAP 核心契約驗證\n\n'+f"{report['tests']['passed']}/{result.testsRun} 測試通過。\n\n"+'僅驗證附件正式 JSON、28 圖碼宣告、規範參數解析與安全拒絕；不等於分析計算、圖表渲染、指標公式、互動或 Windows 部署通過。\n\n'+ '\n'.join(str(t)+'\n'+e for t,e in result.failures+result.errors)+'\n',encoding='utf-8')
print('\n'+str(out/'core_report.json'))
sys.exit(0 if result.wasSuccessful() else 1)
