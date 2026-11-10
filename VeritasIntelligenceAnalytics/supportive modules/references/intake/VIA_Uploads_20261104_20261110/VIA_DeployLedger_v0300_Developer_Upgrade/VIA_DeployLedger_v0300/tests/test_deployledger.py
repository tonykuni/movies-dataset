from __future__ import annotations
# def PARAMETERS
ROOT = __import__('pathlib').Path(__file__).resolve().parents[1]
import ast
import contextlib
import copy
import importlib.util
import io
import json
import os
import secrets
import shutil
import sqlite3
import sys
import tempfile
import types
import unittest
import zipfile
from pathlib import Path
from unittest import mock
from datetime import datetime, timedelta, timezone
sys.path.insert(0, str(ROOT))
import VIA_DeployLedger_v0300 as d
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
L = d.legacy()


def fails(function, *args, **kwargs):
    try:
        function(*args, **kwargs)
    except (ValueError, RuntimeError, FileExistsError, FileNotFoundError, KeyError):
        return
    raise AssertionError('Expected rejection: '+function.__name__)


def load_client(pin, apin):
    pins = types.ModuleType('via_pins')
    pins.RELEASE_PIN, pins.AUTHORITY_PIN = pin, apin
    sys.modules['via_pins'] = pins
    name = 'test_client_'+secrets.token_hex(4)
    spec = importlib.util.spec_from_file_location(name, ROOT/'VIA_Client_v0300.py')
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def public_bytes(k):
    return k.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)


def fixture(base, release_id='R1'):
    root = base/'bundle'
    root.mkdir()
    rk, ak = Ed25519PrivateKey.generate(), Ed25519PrivateKey.generate()
    (root/'release.pub').write_bytes(public_bytes(rk))
    (root/'authority.pub').write_bytes(public_bytes(ak))
    product = L.def_create_product_record()
    (root/'VRN').mkdir()
    (root/'VRN/core.exe').write_bytes(b'SYNTHETIC_TEST_FIXTURE_NOT_A_WINDOWS_EXECUTABLE')
    doc = {'schema':'via.client-release.v3','release_id':release_id,'baseline_id':'FIXTURE','product_number':product['product_number'],'units':[{'id':'VRN_CORE','artifact':'VRN/core.exe','smoke_args':['--selftest'],'success_regex':'PASS','timeout':30}]}
    d.write(root/'release.json',doc)
    env = L.def_sign_package_tree_manifest(L.def_build_package_tree_manifest(root,product['product_number'],release_id),rk)
    d.write(base/'package.signed.json',env)
    c = load_client(d.sha(root/'release.pub'),d.sha(root/'authority.pub'))
    zpath = base/'bundle.zip'
    with zipfile.ZipFile(zpath,'w') as z:
        for p in root.rglob('*'):
            if p.is_file(): z.write(p,'payload/'+p.relative_to(root).as_posix())
        z.write(base/'package.signed.json','package.signed.json')
    return c,root,zpath,env,rk,ak,product


def test_json_duplicate():
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'a.json';p.write_text('{"x":1,"x":2}')
        fails(d.read,p)


def test_windows_paths():
    for name in ('../x','x/../y','/etc/passwd','C:/windows','a\\b','a//b','CON','con.txt','a.','a ','a:ads','a/./b'):
        fails(d.safe_rel,name)
    assert d.safe_rel('資料/繁體中文.json') == '資料/繁體中文.json'


def test_case_collision():
    with tempfile.TemporaryDirectory() as td:
        p=Path(td);(p/'A.txt').write_text('1');(p/'a.txt').write_text('2')
        if len(list(p.iterdir())) == 2: fails(d.tree,p)


def test_tree_link():
    with tempfile.TemporaryDirectory() as td:
        p=Path(td);(p/'a').write_text('x')
        try: (p/'b').symlink_to(p/'a')
        except OSError: return
        fails(d.tree,p)


def test_disjoint():
    fails(d.disjoint,'/a','/a/b');fails(d.disjoint,'/a/b','/a')
    d.disjoint('/a','/b')


def test_source_copy():
    with tempfile.TemporaryDirectory() as td:
        p=Path(td);s=p/'src';s.mkdir();(s/'a.py').write_text('print(1)')
        inv=d.tree(s);d.copy_source(s,p/'stage',inv)
        assert d.tree(s)==d.tree(p/'stage')==inv
        fails(d.copy_source,s,p/'stage',inv)


def test_guard_future_docstring():
    p=L.def_create_product_record()
    src='"""doc"""\nfrom __future__ import annotations\ndef main():\n    return 7\n'
    guarded=d.inject_guard(src,'VRN_CORE',p['product_number'])
    nodes=ast.parse(guarded).body
    assert isinstance(nodes[0],ast.Expr) and isinstance(nodes[1],ast.ImportFrom)
    with mock.patch.dict(os.environ,{},clear=True):
        fails(exec,compile(guarded,'guarded','exec'),{'__file__':'test.exe'})


def test_runtime_no_authority():
    text=d.client_runtime((ROOT/'legacy'/(d.LEGACY_NAME+'.py')).read_text(),'a'*64,'b'*64)
    name='extracted_client_runtime'
    m=types.ModuleType(name);sys.modules[name]=m
    exec(compile(text,name,'exec'),m.__dict__)
    assert m.def_PARAM_BUILD_MODE=='PRODUCTION'
    assert m.def_PARAM_TRUSTED_RELEASE_PUBLIC_KEY_SHA256=='b'*64
    assert not any(hasattr(m,n) for n in d.AUTHORITY_FORBIDDEN)
    for n in d.RUNTIME_ROOTS: assert hasattr(m,n),n
    assert hasattr(m,'def_validate_no_link_chain') and hasattr(m,'def_require_free_disk')


def test_pins_required():
    fails(d.client_runtime,'', '', 'b'*64)


def test_client_source_rejected():
    for name in ('secret.py','raw.ps1','private.pem','data.parquet','db.duckdb','payload.whl'):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);(p/name).write_text('data')
            fails(d.validate_client_tree,p)


def test_client_secret_content():
    with tempfile.TemporaryDirectory() as td:
        p=Path(td);(p/'config.json').write_text('{"s":"'+L.def_create_product_record()['master_key']+'"}')
        fails(d.validate_client_tree,p)


def test_signed_package():
    with tempfile.TemporaryDirectory() as td:
        p=Path(td);c,root,z,e,*_=fixture(p)
        assert c.verify_package(root,p/'package.signed.json')['release_id']=='R1'
        out=c.extract_archive(z,p/'extract')
        assert (out/'payload/VRN/core.exe').exists()


def test_signed_tamper():
    with tempfile.TemporaryDirectory() as td:
        p=Path(td);c,root,*_=fixture(p)
        (root/'VRN/core.exe').write_bytes(b'TAMPER')
        fails(c.verify_package,root,p/'package.signed.json')


def test_extra_dll():
    with tempfile.TemporaryDirectory() as td:
        p=Path(td);c,root,*_=fixture(p)
        (root/'injected.dll').write_bytes(b'injected')
        fails(c.verify_package,root,p/'package.signed.json')


def test_wrong_public_key():
    with tempfile.TemporaryDirectory() as td:
        p=Path(td);c,root,*_=fixture(p)
        (root/'release.pub').write_bytes(public_bytes(Ed25519PrivateKey.generate()))
        fails(c.verify_package,root,p/'package.signed.json')


def test_zip_traversal():
    with tempfile.TemporaryDirectory() as td:
        p=Path(td);c,root,z,*_=fixture(p)
        with zipfile.ZipFile(z,'a') as a:a.writestr('../outside','x')
        fails(c.extract_archive,z,p/'extract')
        assert not (p/'outside').exists()


def test_zip_extra():
    with tempfile.TemporaryDirectory() as td:
        p=Path(td);c,root,z,*_=fixture(p)
        with zipfile.ZipFile(z,'a') as a:a.writestr('payload/inject.dll','x')
        fails(c.extract_archive,z,p/'extract')


def test_zip_case_duplicate():
    with tempfile.TemporaryDirectory() as td:
        p=Path(td);c,root,z,*_=fixture(p)
        with zipfile.ZipFile(z,'a') as a:a.writestr('payload/VRN/CORE.EXE','x')
        fails(c.extract_archive,z,p/'extract')


def test_zip_symlink():
    with tempfile.TemporaryDirectory() as td:
        p=Path(td);c,root,z,*_=fixture(p)
        with zipfile.ZipFile(z,'a') as a:
            info=zipfile.ZipInfo('payload/link');info.create_system=3;info.external_attr=(0o120777<<16);a.writestr(info,'/etc/passwd')
        fails(c.extract_archive,z,p/'extract')


def test_zip_bound():
    with tempfile.TemporaryDirectory() as td:
        p=Path(td);c,root,z,*_=fixture(p)
        with mock.patch.object(c,'MAX_ARCHIVE_BYTES',1):fails(c.extract_archive,z,p/'extract')


def test_install_failed_retains_previous():
    with tempfile.TemporaryDirectory() as td:
        p=Path(td);c,root,z,*_=fixture(p)
        home=p/'home';home.mkdir();prev={'release_id':'OLD','tree_sha256':'a'*64}
        d.write(home/'current.json',prev);d.write(p/'license.json',{'fixture':True})
        with mock.patch.object(c,'validate_license',return_value=None),mock.patch.object(c,'quick_test',side_effect=ValueError('forced quick test failure')):
            fails(c.install,home,z,p/'license.json')
        assert d.read(home/'current.json')==prev
        assert d.read(home/'install-journal.json')['status']=='FAILED_PREVIOUS_RETAINED'


def test_install_commit_and_repeat():
    with tempfile.TemporaryDirectory() as td:
        p=Path(td);c,root,z,*_=fixture(p)
        home=p/'home';d.write(p/'license.json',{'fixture':True})
        with mock.patch.object(c,'validate_license',return_value=None),mock.patch.object(c,'quick_test',return_value={'status':'PASS'}):
            first=c.install(home,z,p/'license.json')
            second=c.install(home,z,p/'license.json')
        assert first['status']==second['status']=='ACTIVE'
        assert d.read(home/'current.json')['previous'] is None
        assert d.read(home/'releases/R1/license.json')=={'fixture':True}
        c.installed_release(home)


def test_install_lock_reentry():
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'lock'
        with L.def_file_lock(p, timeout_seconds=0.2):
            try:
                with L.def_file_lock(p, timeout_seconds=0.1):pass
            except TimeoutError:return
        raise AssertionError('Concurrent lock allowed')


def test_runtime_cli_linux_refusal():
    if os.name=='nt':return
    c=load_client('a'*64,'b'*64)
    with contextlib.redirect_stdout(io.StringIO()):
        assert c.main(['activate','--product-number','ABCD-EFGH-JKLM'])==3


def authority_fixture(p):
    db=p/'authority.sqlite'
    d.register_product(db,p/'product')
    product=d.read(p/'product/product_PRIVATE.json')
    authority=Ed25519PrivateKey.generate()
    private=p/'license.pem'
    private.write_bytes(authority.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.BestAvailableEncryption(b'TEST-ONLY-PASSPHRASE')))
    return db,product,authority,private


def request_fixture(product,device=None):
    device=device or Ed25519PrivateKey.generate()
    return L.def_create_activation_request(device,L.def_PARAM_PRODUCT_SKU,'PRO',product['product_number'],product['master_key'],'pc',{'cpu':'a'*64,'board':'b'*64})


def test_authority_issue_idempotent():
    with tempfile.TemporaryDirectory() as td,mock.patch.dict(os.environ,{'VIA_PRIVATE_KEY_PASSWORD':'TEST-ONLY-PASSPHRASE'}):
        p=Path(td);db,prod,ak,pem=authority_fixture(p)
        req=request_fixture(prod);d.write(p/'req.json',req)
        r1=d.issue(db,p/'req.json',pem,p/'l1.json');r2=d.issue(db,p/'req.json',pem,p/'l2.json')
        assert r1['license_id']==r2['license_id']
        assert d.read(p/'l1.json')==d.read(p/'l2.json')
        L.def_verify_signed_payload(d.read(p/'l1.json'),ak.public_key())


def test_authority_seat_limit():
    with tempfile.TemporaryDirectory() as td,mock.patch.dict(os.environ,{'VIA_PRIVATE_KEY_PASSWORD':'TEST-ONLY-PASSPHRASE'}):
        p=Path(td);db,prod,ak,pem=authority_fixture(p)
        d.write(p/'req.json',request_fixture(prod));d.issue(db,p/'req.json',pem,p/'license.json')
        d.write(p/'req2.json',request_fixture(prod));fails(d.issue,db,p/'req2.json',pem,p/'license2.json')


def test_authority_wrong_product_key():
    with tempfile.TemporaryDirectory() as td,mock.patch.dict(os.environ,{'VIA_PRIVATE_KEY_PASSWORD':'TEST-ONLY-PASSPHRASE'}):
        p=Path(td);db,prod,ak,pem=authority_fixture(p)
        prod['master_key']=L.def_create_product_record()['master_key']
        d.write(p/'req.json',request_fixture(prod));fails(d.issue,db,p/'req.json',pem,p/'license.json')


def test_authority_revoked():
    with tempfile.TemporaryDirectory() as td,mock.patch.dict(os.environ,{'VIA_PRIVATE_KEY_PASSWORD':'TEST-ONLY-PASSPHRASE'}):
        p=Path(td);db,prod,ak,pem=authority_fixture(p)
        d.write(p/'req.json',request_fixture(prod));d.revoke(db,prod['product_number'])
        fails(d.issue,db,p/'req.json',pem,p/'license.json')


def test_expired_activation():
    with tempfile.TemporaryDirectory() as td,mock.patch.dict(os.environ,{'VIA_PRIVATE_KEY_PASSWORD':'TEST-ONLY-PASSPHRASE'}):
        p=Path(td);db,prod,ak,pem=authority_fixture(p)
        dev=Ed25519PrivateKey.generate();req=request_fixture(prod,dev)
        req['payload']['created_at']=(datetime.now(timezone.utc)-timedelta(hours=1)).isoformat()
        req=L.def_sign_payload(req['payload'],dev,req['key_id'],req['schema'])
        d.write(p/'req.json',req);fails(d.issue,db,p/'req.json',pem,p/'license.json')


def test_probe_no_truncation():
    with tempfile.TemporaryDirectory() as td:
        result=d.environment_probe(sys.executable,td)
        assert result['python'] and isinstance(result['packages'],list)


def test_adapter_replay_rejected():
    with tempfile.TemporaryDirectory() as td:
        p=Path(td);receipt=p/'r.json';d.write(receipt,{'status':'PASS','nonce':'old','binding':'x','conflicts':[]})
        fails(d.adapter,{'command':[sys.executable,'-c','pass']},p,receipt,'x')


def test_adapter_bound_receipt():
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)
        code="import os,json;open(os.environ['VIA_DEPLOY_RECEIPT'],'w').write(json.dumps({'status':'PASS','conflicts':[],'nonce':os.environ['VIA_DEPLOY_NONCE'],'binding':os.environ['VIA_DEPLOY_BINDING']}))"
        r=d.adapter({'command':[sys.executable,'-c',code]},p,p/'r.json','binding')
        assert r['receipt']['binding']=='binding'


def test_plan_not_baseline():
    fails(d.assert_baseline,{'status':'PLAN_ONLY','rounds':[]})


def test_contract_requires_closure():
    c={'schema':d.SCHEMA,'platform':'Windows','release_id':'R1','units':[{'id':'VRN_CORE','component':'VRN','entry':'main.py','smoke_args':['--selftest'],'success_regex':'PASS','closure_reviewed':False}]}
    fails(d.validate_contract,c)


def test_no_false_discovery_green():
    with tempfile.TemporaryDirectory() as td:
        r=d.discover(Path(td)/'out',[Path(td)/'absent'])
        assert r['status']=='NEEDS_DEPLOY_CONTRACT' and not r['baseline_sealed']



def audit_fixture(p):
    src=p/'source';src.mkdir();(src/'main.py').write_text('print("ALL_7_PASS")\n')
    governance=p/'gov';governance.mkdir()
    probe=governance/'probe.py'
    probe.write_text("import os,json\nfrom pathlib import Path\nPath(os.environ['VIA_DEPLOY_RECEIPT']).write_text(json.dumps({'status':'PASS','conflicts':[],'nonce':os.environ['VIA_DEPLOY_NONCE'],'binding':os.environ['VIA_DEPLOY_BINDING']}))\n")
    ready=p/'closeout.json';d.write(ready,{'state':'PASS'})
    c={'schema':d.SCHEMA,'platform':'Windows','bits':64,'release_id':'TEST_R1','units':[{'id':'VRN_CORE','component':'VRN','source':str(src),'entry':'main.py','python':sys.executable,'smoke_args':['--selftest'],'success_regex':'ALL_7_PASS','closure_reviewed':True}],'tools':[{'role':r,'path':str(probe),'sha256':d.sha(probe)} for r in d.REQUIRED_TOOL_ROLES],'vcgc':{'root':str(governance),'audit':{'command':[sys.executable,str(probe)]}},'accelerator':{'command':[sys.executable,str(probe)]},'readiness':[{'component':'VRN','path':str(ready),'status_field':'state','pass_values':['PASS']}]}
    env={'platform':'Windows','bits':64,'python':'3.12.1','packages':[],'pip_check':{'ok':True}}
    return c,env


def test_three_round_baseline_source_preserved():
    with tempfile.TemporaryDirectory() as td:
        p=Path(td);c,env=audit_fixture(p);before=d.tree(c['units'][0]['source'])
        with mock.patch.object(d,'environment_probe',return_value=env): b=d.prepare(c,p/'out')
        assert b['status']=='BASELINE_READY' and len(b['rounds'])==3
        assert before==d.tree(c['units'][0]['source'])
        d.assert_baseline(b)


def test_open_closeout_blocks_release():
    with tempfile.TemporaryDirectory() as td:
        p=Path(td);c,env=audit_fixture(p);d.write(p/'closeout.json',{'state':'OPEN'})
        with mock.patch.object(d,'environment_probe',return_value=env): b=d.prepare(c,p/'out')
        assert b['status']=='BLOCKED'
        assert any(f['code']=='CLOSEOUT_NOT_READY' for f in b['rounds'][-1]['findings'])
        fails(d.assert_baseline,b)


def test_source_drift_blocks_build():
    with tempfile.TemporaryDirectory() as td:
        p=Path(td);c,env=audit_fixture(p)
        with mock.patch.object(d,'environment_probe',return_value=env): b=d.prepare(c,p/'out')
        (Path(c['units'][0]['source'])/'main.py').write_text('print("changed")')
        fails(d.assert_baseline,b)


def test_preexisting_pip_conflict_blocks():
    with tempfile.TemporaryDirectory() as td:
        p=Path(td);c,env=audit_fixture(p);env['pip_check']['ok']=False
        with mock.patch.object(d,'environment_probe',return_value=env): b=d.prepare(c,p/'out')
        assert b['status']=='BLOCKED'


def test_semantic_failure_blocks_even_exit_zero():
    with tempfile.TemporaryDirectory() as td:
        p=Path(td);c,env=audit_fixture(p);c['units'][0]['success_regex']='NO_SUCH_RESULT'
        with mock.patch.object(d,'environment_probe',return_value=env): b=d.prepare(c,p/'out')
        assert b['status']=='BLOCKED'


def test_pipeline_stops_without_contract():
    with tempfile.TemporaryDirectory() as td:
        p=Path(td);d.write(p/'job.json',{'contract':str(p/'missing.json')})
        r=d.pipeline(p/'job.json',p/'out')
        assert r['status']=='BLOCKED' and not (p/'out/build').exists()


def test_legacy_plan_cannot_release():
    with tempfile.TemporaryDirectory() as td:
        p=Path(td);src=p/'src';src.mkdir();(src/'main.py').write_text('def main():\n    return 0\n')
        r=L.def_package_plan(src,p/'stage',p/'out',L.def_create_product_record(),audit_path=p/'audit.jsonl')
        assert not r['summary']['release_eligible']


def test_clock_backwards_rejected():
    L.def_test_clock_rollback()


def test_runtime_replay_and_process_binding():
    L.def_test_runtime_token_one_use_and_process_binding()



def test_postcommit_journal_warning_is_not_false_rollback():
    with tempfile.TemporaryDirectory() as td:
        p=Path(td);c,root,z,*_=fixture(p);home=p/'home';d.write(p/'license.json',{'fixture':True})
        original=c.write
        def failing_journal(path,value):
            if Path(path).name=='install-journal.json' and value.get('status')=='ACTIVE':
                raise OSError('forced journal disk failure after commit')
            return original(path,value)
        with mock.patch.object(c,'validate_license',return_value=None),mock.patch.object(c,'quick_test',return_value={'status':'PASS'}),mock.patch.object(c,'write',side_effect=failing_journal):
            result=c.install(home,z,p/'license.json')
        assert result['status']=='ACTIVE_JOURNAL_WARNING'
        assert d.read(home/'current.json')['release_id']=='R1'


def test_concurrent_authority_seat_limit():
    from concurrent.futures import ThreadPoolExecutor
    with tempfile.TemporaryDirectory() as td,mock.patch.dict(os.environ,{'VIA_PRIVATE_KEY_PASSWORD':'TEST-ONLY-PASSPHRASE'}):
        p=Path(td);db,prod,ak,pem=authority_fixture(p)
        for n in range(2):d.write(p/('r'+str(n)+'.json'),request_fixture(prod))
        def attempt(n):
            try:d.issue(db,p/('r'+str(n)+'.json'),pem,p/('l'+str(n)+'.json'));return 'PASS'
            except ValueError:return 'DENY'
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(attempt,range(2)))
        assert sorted(results)==['DENY','PASS']


def test_assets_require_redistribution_and_hash():
    with tempfile.TemporaryDirectory() as td:
        p=Path(td);c,env=audit_fixture(p)
        c['assets']=[{'source':'anything','target':'Assets/model.dat','sha256':'a'*64,'redistribution_reviewed':False,'license_notice':'unknown'}]
        fails(d.validate_contract,c)



def test_native_source_loader_not_silently_frozen():
    assert d.native_hazards('import importlib.util\nimportlib.util.spec_from_file_location("engine", "a.py")')
    assert d.native_hazards('from pathlib import Path\nlist(Path(".").glob("*_v*.py"))')
    assert not d.native_hazards('def main():\n    return 1')


def main():
    tests=[v for n,v in sorted(globals().items()) if n.startswith('test_') and callable(v)]
    suite=unittest.TestSuite(unittest.FunctionTestCase(t) for t in tests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    evidence={'schema':'via.deployment-test.v3','tests':result.testsRun,'passes':result.testsRun-len(result.failures)-len(result.errors),'failures':[{'test':str(t),'traceback':msg} for t,msg in result.failures+result.errors],'platform':sys.platform,'windows_native_build_tested':False,'dpapi_tested':False,'fixtures':'Package byte/integrity fixtures are synthetic; install transaction tests mock licensing and executable smoke; authority signature and legacy license tests execute real cryptography.'}
    d.write(ROOT/'evidence/deployment_tests.json',evidence)
    return 0 if result.wasSuccessful() else 1


if __name__=='__main__':raise SystemExit(main())
