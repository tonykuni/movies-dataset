"""SYSTEM MANAGER: discover engine headers using AST, expose the same capability SSOT.
Does not import or execute the inspected engine. Existing audit rounds are retained.
"""
from __future__ import annotations
import ast
import hashlib
import html
import importlib.util
import json
import re
import sys
from pathlib import Path

# def 01_PARAMETERS — one machine-readable header, one feature source of truth.
HERE=Path(__file__).resolve().parent
VIA=HERE.parents[1]
PREVIOUS=HERE/"CGC_MDL069_SystemManager_v0112.py"
ENGINE_ROOT=VIA/"supportive modules/70_VRN_Rules"
ENGINE_GLOB="SUP_MDL743_GenericLayoutHub_v*.py"
COMPONENT_REGISTRY="supportive modules/registry/VIA_Component_Inventory_SSOT_v0100.json"
_PREV=None
# [VIA:ACCEL-BRIDGE] Existing runtime bridge is retained when audit execution loads v0112.


def def_ast_index(tree, text, stem, records):
    """Qualified definition locations and hashes; no execution or repeated source dump."""
    lines=text.splitlines(keepends=True);index={}
    def visit(nodes, prefix=''):
        for node in nodes:
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
                name=prefix+node.name;kind='class' if isinstance(node,ast.ClassDef) else 'function'
                start=min([node.lineno]+[d.lineno for d in node.decorator_list])
                source=''.join(lines[start-1:node.end_lineno])
                index[name]={'kind':kind,'start_line':start,'end_line':node.end_lineno,'sha256':hashlib.sha256(source.encode()).hexdigest(),'code':records.get(kind+'|'+stem+':'+name,{}).get('code')}
                visit(node.body,name+'.')
            else:
                children=[c for c in ast.iter_child_nodes(node) if isinstance(c,ast.stmt)]
                visit(children,prefix)
    visit(tree.body)
    return index


def def_effective_api(catalog):
    """Resolve facade precedence once; superseded wrappers are not competing owners."""
    api={}
    for module in catalog.get('composition',{}).get('facade_precedence',[]):
        if module not in catalog['definitions']:raise ValueError('missing facade module: '+module)
        definition=catalog['definitions'][module]
        for function in definition['functions']:
            if function.startswith('_'):continue
            binding=module+':'+function
            if function in api:api[function]['shadowed_bindings'].append(binding)
            else:api[function]={'binding':binding,'source':definition['source'],'code':definition['function_codes'][function],'shadowed_bindings':[]}
    return api


def def_engine_catalog(engine=None):
    """Static introspection only; unavailable bindings fail the catalog."""
    engine=Path(engine) if engine else sorted(ENGINE_ROOT.glob(ENGINE_GLOB))[-1]
    tree=ast.parse(engine.read_text(encoding="utf-8"));manifest=None
    for node in tree.body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="ENGINE_MANIFEST" for t in node.targets):manifest=ast.literal_eval(node.value)
    if not manifest:raise RuntimeError("ENGINE_MANIFEST absent")
    path=(VIA/manifest["capability_ssot"]).resolve()
    if not path.is_relative_to(VIA.resolve()):raise ValueError("catalog outside VIA")
    catalog=json.loads(path.read_text(encoding="utf-8"));definitions={};errors=[]
    registry_path=VIA/COMPONENT_REGISTRY
    registry=json.loads(registry_path.read_text(encoding='utf-8')) if registry_path.is_file() else {'records':[]}
    records={r['key']:r for r in registry['records'] if r.get('state','ACTIVE')=='ACTIVE'}
    test_names=set()
    if catalog.get('test_source'):
        test_path=(VIA/catalog['test_source']).resolve()
        if not test_path.is_relative_to(VIA.resolve()) or not test_path.is_file():errors.append('missing test source')
        else:test_names={n.name for n in ast.walk(ast.parse(test_path.read_text(encoding='utf-8'))) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
    for name,relative in catalog["modules"].items():
        source=(VIA/relative).resolve()
        if not source.is_relative_to(VIA.resolve()) or not source.is_file():errors.append("missing module: "+name);continue
        data=source.read_bytes();module_ast=ast.parse(data.decode("utf-8"))
        functions=[n.name for n in module_ast.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
        stem=catalog.get('registry_stems',{}).get(name) or ('SUP_MDL743_Reference_'+name if name.startswith('gle_') else re.sub(r'_v\d+\.py$','',source.name))
        components=[{'code':r['code'],'category':r['category'],'identity':r['identity']} for r in records.values() if r['identity']==stem or r['identity'].startswith(stem+':')]
        codes={f:records.get('function|'+stem+':'+f,{}).get('code') for f in functions}
        definitions[name]={"source":relative,"functions":functions,"sha256":hashlib.sha256(data).hexdigest(),'registry_stem':stem,'function_codes':codes,'registered_components':components,'definition_index':def_ast_index(module_ast,data.decode('utf-8'),stem,records)}
    ids=[]
    for c in catalog["capabilities"]:
        ids.append(c["id"]);missing=[]
        for binding in c["implementation"]:
            module,function=binding.split(":",1)
            if module not in definitions or function not in definitions[module]["functions"]:missing.append(binding)
        errors.extend("unbound: "+b for b in missing)
        c["implementation_state"]="MISSING" if missing else "IMPLEMENTED"
        c['registration_code']=records.get('feature|layout/'+c['id'],{}).get('code')
        c['binding_codes']={b:definitions.get(b.split(':',1)[0],{}).get('function_codes',{}).get(b.split(':',1)[1]) for b in c['implementation']}
        c['registration_state']='REGISTERED' if c['registration_code'] and all(c['binding_codes'].values()) else 'PENDING'
        if catalog.get('test_source') and c.get('test_id') not in test_names:errors.append('missing verification test: '+str(c.get('test_id')))
    if len(ids)!=len(set(ids)):errors.append("duplicate capability IDs")
    registered=bool(ids) and all(c['registration_state']=='REGISTERED' for c in catalog['capabilities'])
    catalog.update(engine_manifest=manifest,definitions=definitions,errors=errors,state="ERROR" if errors else "REGISTERED" if registered else "REGISTERABLE")
    try:catalog['effective_api']=def_effective_api(catalog)
    except ValueError as exc:catalog['errors'].append(str(exc));catalog['state']='ERROR'
    return catalog


def def_catalog_html(catalog):
    rows=''.join('<tr><td>'+html.escape(c['id'])+'</td><td>'+html.escape(c.get('registration_code') or 'PENDING')+'</td><td>'+html.escape(c['name'])+'</td><td>'+html.escape(c['implementation_state'])+'</td><td>'+html.escape(c['verification_scope'])+'</td></tr>' for c in catalog['capabilities'])
    modules=''.join('<tr><td>'+html.escape(name)+'</td><td>'+html.escape(catalog.get('composition',{}).get('roles',{}).get(name,''))+'</td><td>'+html.escape(record['source'])+'</td><td>'+str(len(record.get('definition_index',{})))+'</td></tr>' for name,record in catalog.get('definitions',{}).items())
    ownership='<details class="engine-modules"><summary>模組分工與函式索引</summary><p>對外單一入口；內部沿用鎖定擷取與共用修復模組。JSON 清冊提供每個函式的唯一有效歸屬、行號、雜湊與註冊碼。</p><table><tr><th>模組</th><th>職責</th><th>來源</th><th>定義數</th></tr>'+modules+'</table></details>'
    return '<section class="engine-capabilities"><h2>'+html.escape(catalog['purpose'])+'</h2><p>來源：引擎頂部 ENGINE_MANIFEST → 單一功能 SSOT。實作在位不等於所有文件已驗證。</p><table><tr><th>功能號</th><th>中央註冊碼</th><th>完整功能</th><th>實作</th><th>驗證範圍／依賴</th></tr>'+rows+'</table>'+ownership+'</section>'


def def_previous():
    global _PREV
    if _PREV is None:
        spec=importlib.util.spec_from_file_location("system_manager_previous",PREVIOUS)
        _PREV=importlib.util.module_from_spec(spec);sys.modules[spec.name]=_PREV;spec.loader.exec_module(_PREV)
    return _PREV


def __getattr__(name):
    return getattr(def_previous(),name)


def main():
    if "--catalog" in sys.argv:
        catalog=def_engine_catalog();print(json.dumps(catalog,ensure_ascii=False,indent=2));return 1 if catalog['errors'] else 0
    if "--selftest" in sys.argv:
        catalog=def_engine_catalog();assert not catalog['errors'];print('Static engine catalog PASS:',len(catalog['capabilities']));return 0
    previous=def_previous();old_inventory=previous.c6_inventory;old_html=previous.html_report
    def inventory():
        result=old_inventory();result['engine_catalog']=def_engine_catalog();return result
    def render(rounds,ts):
        hp,jp,state=old_html(rounds,ts)
        text=hp.read_text(encoding='utf-8').replace('</body>',def_catalog_html(def_engine_catalog())+'</body>')
        hp.write_text(text,encoding='utf-8');return hp,jp,state
    previous.c6_inventory=inventory;previous.html_report=render
    try:return previous.main()
    finally:previous.c6_inventory=old_inventory;previous.html_report=old_html


if __name__=="__main__":raise SystemExit(main())
