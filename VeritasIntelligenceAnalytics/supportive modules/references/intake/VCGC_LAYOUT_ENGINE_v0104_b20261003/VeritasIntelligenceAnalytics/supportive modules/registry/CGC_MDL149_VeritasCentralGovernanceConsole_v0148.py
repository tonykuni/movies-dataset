"""VCGC one door: registered modular Layout capabilities, evidence reuse, manager catalog.
Canonical registry_sync still owns counters and writes. No governance gate is skipped.
"""
from __future__ import annotations
import argparse
import ast
import importlib.util
import json
import re
import sys
from pathlib import Path

# def 01_PARAMETERS
HERE=Path(__file__).resolve().parent
VIA=HERE.parents[1]
PREVIOUS=HERE/"CGC_MDL149_VeritasCentralGovernanceConsole_v0146.py"
OUTPUT=VIA/"VIA_Reports/layout_review"
VERSION="v0148"
# [VIA:ACCEL-BRIDGE] Canonical compatibility bridge is initialized by the previous console.


def def_load():
    spec=importlib.util.spec_from_file_location("vcgc_layout_v0146",PREVIOUS)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    return module


prev=def_load()
body=prev.body
_BASE_LIVE=body.live_components


def __getattr__(name):
    return getattr(prev,name)


def live_components():
    """Extend the existing inventory, preserving its categories and stable code writer."""
    inventory=_BASE_LIVE();rows={r['key']:r for r in inventory['rows']}
    hub=prev.def_layout_hub();catalog=hub.def_manifest()
    if catalog['errors']:raise RuntimeError('unregistered Layout binding: '+str(catalog['errors']))
    for feature in catalog['capabilities']:
        identity='layout/'+feature['id'];key='feature|'+identity
        rows[key]={'key':key,'category':'feature','identity':identity,'source':hub.ENGINE_MANIFEST['capability_ssot']}
    # Frozen intake remains frozen. Register delegated implementations as references,
    # including nested adapter methods; never activate an unavailable model here.
    for name,record in catalog['definitions'].items():
        source=record['source'];stem=record['registry_stem']
        key='module|'+stem;rows.setdefault(key,{'key':key,'category':'module','identity':stem,'source':source})
        class Visitor(ast.NodeVisitor):
            def __init__(self):self.stack=[]
            def visit_ClassDef(self,node):
                self.def_add(node,'class');self.stack.append(node.name);self.generic_visit(node);self.stack.pop()
            def visit_FunctionDef(self,node):
                self.def_add(node,'function');self.stack.append(node.name);self.generic_visit(node);self.stack.pop()
            visit_AsyncFunctionDef=visit_FunctionDef
            def def_add(self,node,category):
                identity=stem+':'+'.'.join(self.stack+[node.name]);key=category+'|'+identity
                rows.setdefault(key,{'key':key,'category':category,'identity':identity,'source':source,'line':node.lineno})
        Visitor().visit(ast.parse((VIA/source).read_text(encoding='utf-8')))
    inventory['rows']=[rows[k] for k in sorted(rows)];counts={}
    for row in inventory['rows']:counts[row['category']]=counts.get(row['category'],0)+1
    inventory['counts']=counts
    return inventory


body.live_components=live_components


def def_registry_layout(apply=False, path=None):
    """Scope registration to this integration. Never retire uninspected components.

    The existing registry writer still assigns IDs, increments its counters and
    atomically persists. Out-of-scope records are carried forward, not reverified.
    """
    path=path or body.COMPONENT_REGISTRY
    baseline=body._json(path)
    if not baseline or not baseline.get('records'):raise RuntimeError('canonical registry baseline absent')
    catalog=prev.def_layout_hub().def_manifest()
    if catalog['errors']:raise RuntimeError(str(catalog['errors']))
    inventory=live_components()
    prefixes=('SUP_MDL743','CGC_MDL149_VeritasCentralGovernanceConsole','CGC_MDL069_SystemManager')
    selected={r['key']:r for r in inventory['rows'] if r['identity'].startswith(prefixes) or r['identity'].startswith('layout/LAYOUT.') or r['identity']=='central/vcgc_layout_review'}
    retained={r['key']:dict(r) for r in baseline['records'] if r.get('state','ACTIVE')=='ACTIVE'}
    retained.update(selected)
    scope_inventory={**inventory,'rows':list(retained.values()),'counts':{}}
    for row in scope_inventory['rows']:
        cat=row['category'];scope_inventory['counts'][cat]=scope_inventory['counts'].get(cat,0)+1
    saved=body.live_components
    try:
        body.live_components=lambda:scope_inventory
        result=body.registry_sync(apply=apply,path=path)
    finally:body.live_components=saved
    if result['stale']:raise RuntimeError('scoped registration attempted retirement')
    result.update(scope='Layout integration only; other records preserved without revalidation',scope_keys=sorted(selected),capabilities=len(catalog['capabilities']))
    return result


def main(argv=None):
    args=list(sys.argv[1:] if argv is None else argv)
    if args and args[0]=='registry-sync' and '--layout-only' in args:
        for gate in (body.require_token_gate,body.policy_step,body.env_step):
            if gate():return 2
        result=def_registry_layout('--apply' in args)
        print(json.dumps(result,ensure_ascii=False,indent=2));return 0
    if args and args[0]=='layout':
        hub=prev.def_layout_hub()
        if args==['layout','--selftest']:return hub.selftest()
        for gate in (body.require_token_gate,body.policy_step,body.env_step):
            if gate():return 2
        parser=argparse.ArgumentParser(description='One registered Layout engine; original extraction locked')
        parser.add_argument('--dir',type=Path);parser.add_argument('--out',type=Path,default=OUTPUT)
        parser.add_argument('--evidence',type=Path);parser.add_argument('--manifest',action='store_true');parser.add_argument('--open',action='store_true')
        options=parser.parse_args(args[1:])
        if options.manifest:
            catalog=hub.def_manifest();print(json.dumps(catalog,ensure_ascii=False,indent=2));return 1 if catalog['errors'] else 0
        locator=prev.def_load(HERE/'CGC_MDL149_LayoutUse_v0100.py','layout_input_locator')
        report=hub.def_run_batch(options.dir or locator.sample_dir(),options.out,options.evidence)
        print(json.dumps({k:report[k] for k in ('state','errors','repair_cache_hits','financial_database_written')},ensure_ascii=False,indent=2))
        if options.open:
            import webbrowser
            webbrowser.open((options.out/hub.HTML_NAME).resolve().as_uri())
        return 1 if report['errors'] else 2
    original=sys.argv
    try:
        sys.argv=[original[0],*args];return prev.main(args)
    finally:sys.argv=original


if __name__=='__main__':raise SystemExit(main())
