# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
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