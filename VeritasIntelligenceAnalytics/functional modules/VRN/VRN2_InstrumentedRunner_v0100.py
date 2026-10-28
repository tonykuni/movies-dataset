#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111] AST 記憶體插樁；引擎原檔不修改。
"""Trace every Python function/method in an external engine without changing its bytes.
This records hooks and executed verbs. It does not claim a real accelerator is available.
"""
import argparse, ast, functools, hashlib, json, os, sys, threading, time
from pathlib import Path

TAG='VRN2_VERB_COVERAGE/1'
METRICS={}
METRICS_LOCK=threading.Lock()


def audit(qualname):
    def decorate(fn):
        @functools.wraps(fn)
        def wrapped(*args,**kwargs):
            started=time.monotonic()
            try:return fn(*args,**kwargs)
            finally:
                with METRICS_LOCK:
                    m=METRICS.setdefault(qualname,{'calls':0,'seconds':0});m['calls']+=1;m['seconds']+=time.monotonic()-started
        return wrapped
    return decorate

class Inject(ast.NodeTransformer):
    def __init__(self):self.stack=[];self.names=[]
    def visit_ClassDef(self,node):
        self.stack.append(node.name);self.generic_visit(node);self.stack.pop();return node
    def visit_FunctionDef(self,node):
        name='.'.join(self.stack+[node.name]);self.names.append(name);self.stack.append(node.name);self.generic_visit(node);self.stack.pop()
        node.decorator_list.append(ast.Call(func=ast.Name(id='__vrn_audit__',ctx=ast.Load()),args=[ast.Constant(name)],keywords=[]));return node


def run_engine(path,args,expected,report):
    raw=Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('引擎雜湊不符；插樁前停止')
    tree=ast.parse(raw,filename=str(path));inject=Inject();tree=inject.visit(tree);ast.fix_missing_locations(tree)
    oldargv=sys.argv;sys.argv=[str(path)]+list(args);sys.path.insert(0,str(Path(path).parent));exit_code=0
    try:
        namespace={'__name__':'__main__','__file__':str(Path(path).resolve()),'__vrn_audit__':audit}
        exec(compile(tree,str(path),'exec'),namespace)
    except SystemExit as exc:exit_code=exc.code if isinstance(exc.code,int) else (0 if exc.code is None else 1)
    except BaseException:
        exit_code=1;raise
    finally:
        sys.argv=oldargv
        payload={'schema':TAG,'engine':str(path),'sha256':expected,'registered':len(inject.names),'total':len(inject.names),'verbs':inject.names,'executed':METRICS,'exit_code':exit_code,'real_accelerator':'UNVERIFIED; instrumentation is not acceleration execution proof','network_contract':'must be checked separately by locked MarketFetch bridge'}
        target=Path(report);target.parent.mkdir(parents=True,exist_ok=True);temp=target.with_suffix('.tmp');temp.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8');os.replace(temp,target)
    return exit_code


def main(argv=None):
    parser=argparse.ArgumentParser();parser.add_argument('--engine',type=Path,required=True);parser.add_argument('--sha256',required=True);parser.add_argument('--report',type=Path,required=True);parser.add_argument('args',nargs=argparse.REMAINDER);a=parser.parse_args(argv)
    return run_engine(a.engine,a.args[1:] if a.args[:1]==['--'] else a.args,a.sha256,a.report)

if __name__=='__main__':raise SystemExit(main())
