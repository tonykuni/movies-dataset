import ast, json, sys
inp=sys.argv[1]
outp=sys.argv[2]
paths=json.load(open(inp,"r",encoding="utf-8-sig"))
rows=[]
for p in paths:
    r={"path":p,"ok":False,"ast":False,"compile":False,"functions":0,"classes":0,"error":""}
    try:
        src=open(p,"r",encoding="utf-8-sig").read()
        t=ast.parse(src, filename=p)
        compile(src,p,"exec")
        r["ok"]=True
        r["ast"]=True
        r["compile"]=True
        r["functions"]=sum(isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) for n in ast.walk(t))
        r["classes"]=sum(isinstance(n,ast.ClassDef) for n in ast.walk(t))
    except Exception as e:
        r["error"]=str(e)
    rows.append(r)
json.dump(rows,open(outp,"w",encoding="utf-8"),ensure_ascii=False,indent=2)