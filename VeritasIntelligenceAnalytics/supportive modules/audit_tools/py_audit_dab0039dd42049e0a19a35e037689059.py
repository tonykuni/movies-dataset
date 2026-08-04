import ast, json, sys
p=sys.argv[1]
out=sys.argv[2]
r={"exists":True,"ast":False,"compile":False,"functions":0,"classes":0,"error":""}
try:
    src=open(p,"r",encoding="utf-8-sig").read()
    t=ast.parse(src, filename=p)
    compile(src,p,"exec")
    r["ast"]=True
    r["compile"]=True
    r["functions"]=sum(isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) for n in ast.walk(t))
    r["classes"]=sum(isinstance(n,ast.ClassDef) for n in ast.walk(t))
except Exception as e:
    r["error"]=str(e)
open(out,"w",encoding="utf-8").write(json.dumps(r,ensure_ascii=False,indent=2))