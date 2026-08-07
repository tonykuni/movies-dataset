# -*- coding: utf-8 -*-
"""VIA PSU+Thermal 中間層 · 驗證 + 自動編號 append(A)。
用法:
  python validate.py validate                # 驗證全部 7 表(空表也應 PASS)
  python validate.py add T01_suppliers name=奇鋐 country=台灣 evidence_tier=T2 status=active
治理:只增不減(不改既有列)· 全自動編號(VIA-XXX-0001)· T-1 紀律(T06 需 asof_release)
     · 證據 tier 白名單 · 財報優先法說次之(data_priority 枚舉)· retired 用狀態欄不刪列。
"""
import json, csv, sys, os, re

BASE=os.path.dirname(os.path.abspath(__file__))
SCHEMA=json.load(open(os.path.join(BASE,"schema","via_pt_schema.json"),encoding="utf-8"))

def _rows(t):
    p=os.path.join(BASE,"data",f"{t}.csv")
    with open(p,encoding="utf-8") as f: return list(csv.DictReader(f))

def _cols(t): return SCHEMA["tables"][t]["column_order"]

def validate():
    issues=[]; total=0
    for t,meta in SCHEMA["tables"].items():
        rows=_rows(t); total+=len(rows)
        seen=set()
        pat=re.compile(meta["properties"]["id"]["pattern"])
        for i,r in enumerate(rows,1):
            # 主鍵格式 + 唯一(append-only:不得重複)
            rid=r.get("id","")
            if not pat.match(rid): issues.append((t,i,f"id 格式錯:{rid}"))
            if rid in seen: issues.append((t,i,f"id 重複(違反 append-only):{rid}"))
            seen.add(rid)
            # 必填
            for req in meta["required"]:
                if not (r.get(req) or "").strip(): issues.append((t,i,f"缺必填 {req}"))
            # 枚舉
            for c,p in meta["properties"].items():
                if "enum" in p and (r.get(c,"") not in p["enum"]):
                    issues.append((t,i,f"{c} 非白名單:{r.get(c)}"))
            # T-1 紀律:T06 財務必須有 asof_release
            if meta.get("t1_asof") and not (r.get("asof_release") or "").strip():
                issues.append((t,i,"T-1 紀律:財務列缺 asof_release(發布日)"))
    return issues,total

def add(t,kv):
    if t not in SCHEMA["tables"]: sys.exit(f"未知表 {t}")
    meta=SCHEMA["tables"][t]; cols=_cols(t)
    led=os.path.join(BASE,"ledger",f"{t}.ledger.json"); L=json.load(open(led,encoding="utf-8"))
    L["high_water"]+=1  # 只增,永不回收
    rid=f"{meta['prefix']}-{L['high_water']:04d}"
    row={c:"" for c in cols}; row["id"]=rid
    for k,v in kv.items():
        if k not in cols: sys.exit(f"{t} 無欄位 {k}")
        row[k]=v
    row.setdefault("status","active")
    # 先驗這一列(不寫壞資料)
    for req in meta["required"]:
        if not (row.get(req) or "").strip(): sys.exit(f"缺必填 {req}(未寫入)")
    p=os.path.join(BASE,"data",f"{t}.csv")
    with open(p,"a",newline="",encoding="utf-8") as f:
        csv.DictWriter(f,fieldnames=cols).writerow(row)
    json.dump(L,open(led,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
    print(f"append {rid} → {t}")

if __name__=="__main__":
    cmd=sys.argv[1] if len(sys.argv)>1 else "validate"
    if cmd=="validate":
        iss,tot=validate()
        print(f"驗證 7 表 · {tot} 列")
        if not iss: print("PASS · 全部符合 schema(含空表)")
        else:
            print(f"FAIL · {len(iss)} 個問題:")
            for t,i,m in iss: print(f"  [{t}] row{i}: {m}")
        sys.exit(1 if iss else 0)
    elif cmd=="add":
        t=sys.argv[2]; kv=dict(x.split("=",1) for x in sys.argv[3:])
        add(t,kv)
