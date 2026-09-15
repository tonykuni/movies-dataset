import importlib.util
import sys
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace
import os

ROOT=Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location('panorama_console_test', ROOT/'supportive modules/registry/CGC_MDL149_VeritasCentralGovernanceConsole_v0103.py')
C=importlib.util.module_from_spec(SPEC);sys.modules[SPEC.name]=C;SPEC.loader.exec_module(C)


class ConsoleFlow(unittest.TestCase):
    def test_calendar_month_clamping(self):
        self.assertEqual(C.def_panorama_dates(2,'2026-09-15'),('2026-07-15','2026-09-15'))
        self.assertEqual(C.def_panorama_dates(1,'2024-03-31'),('2024-02-29','2024-03-31'))

    def test_html_escapes_diagnostic_text(self):
        page=C.def_panorama_render({'results':[{'id':'x','phase':'test','state':'RED','why':'<script>alert(1)</script>'}]})
        self.assertNotIn('<script>alert',page)
        self.assertIn('&lt;script&gt;',page)

    def test_prior_full_logs_collected_no_rerun(self):
        with tempfile.TemporaryDirectory() as td,patch.object(C,'REPORTS',Path(td)):
            bus=Path(td)/'engine_bus';bus.mkdir()
            log=bus/'station.log';log.write_text('[FAIL] full assertion after cutoff\n')
            (bus/'ENGINE_BUS_latest.json').write_text(json.dumps({'results':[{'family':'vrn','id':'vrn_firstpage','state':'RED','stdout_log':str(log)}]}))
            result=C.def_panorama_collect(Path(td)/'run')
            self.assertEqual(result[0]['failed_assertions'],['[FAIL] full assertion after cutoff'])
            self.assertTrue(Path(result[0]['evidence_log']).exists())

    def test_panorama_open_issues_block_install(self):
        with tempfile.TemporaryDirectory() as td,patch.object(C,'REPORTS',Path(td)),patch.object(C,'rungate',return_value={'install':'INSTALL_OK','state':'GREEN'}):
            C.def_panorama_atomic(Path(td)/'panorama/PANORAMA_latest.json',{'status':'FINISHED','blockers':1})
            self.assertEqual(C.check()['install'],'BLOCKED_PANORAMA')

    def test_independent_fetch_survives_vrn_test_failure(self):
        with tempfile.TemporaryDirectory() as td,patch.object(C,'REPORTS',Path(td)/'reports'):
            root=Path(td);py=root/'via_vrn/python';py.parent.mkdir();py.touch()
            calls=[]
            catalog=[{'id':'tw_history','family':'vdf'},{'id':'etf_holdings_daily','family':'vdf'},{'id':'vrn_firstpage','family':'vrn'}]
            def bus_call(item,params=None,**kw):
                calls.append((item,params,kw.get('profile')))
                family=next(r['family'] for r in catalog if r['id']==item)
                return {'id':item,'family':family,'state':'RED' if item=='vrn_firstpage' else 'GREEN','why':'[FAIL] fixture' if item=='vrn_firstpage' else ''}
            bus=SimpleNamespace(catalog=lambda:catalog,python_for=lambda f:{'python':str(py)},call=bus_call,_census_block=lambda:{})
            gate=SimpleNamespace(run=lambda *a,**k:{'verdict':'GREEN'})
            def load(name,path):
                return bus if name=='panorama_bus' else gate
            dbs={'prices':{'state':'GREEN','path':str(root/'p.duckdb'),'env':'VIA_DB_VDF_TW_MARKET'},'etf':{'state':'GREEN','path':str(root/'e.duckdb'),'env':'VIA_DB_ACTIVETWETF'}}
            with patch.object(C,'_load',side_effect=load),patch.object(C,'def_panorama_resolve_dbs',return_value=dbs),patch.object(C,'def_panorama_sync_laws',return_value={'state':'APPLIED'}),patch.object(C,'def_panorama_sync_params',return_value={'state':'APPLIED'}),patch.object(C,'registry_sync',return_value={'state':'APPLIED'}),patch.object(C,'snapshot',return_value={}),patch.object(C,'write_outputs'),patch.object(C,'rungate',return_value={'install':'INSTALL_OK','state':'GREEN'}),patch.dict(os.environ,{}):
                rc=C.def_panorama_main(['--apply','--fetch','--out',str(root/'run'),'--end','2026-09-15'])
            self.assertEqual(rc,2)
            fetched={item for item,params,profile in calls if params and params.get('gap-mode')=='fetch'}
            self.assertEqual(fetched,{'tw_history','etf_holdings_daily'})
            result=json.loads((root/'run/PANORAMA.json').read_text())
            self.assertEqual(result['approval'],'BLOCKED')
            self.assertTrue(any(r['id']=='vrn_real_reports' and r['state']=='BLOCKED_DEPENDENCY' for r in result['results']))
            self.assertTrue((root/'run/PANORAMA.html').is_file())


if __name__=='__main__':
    unittest.main()
