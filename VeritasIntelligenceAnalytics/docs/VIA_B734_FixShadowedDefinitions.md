# 批734(原 PR #104 批708,號已被 main 使用,改號)— 修正錯誤:刪掉被同名定義蓋掉的死碼,並修掉全景代讀自己的誤報

> 操作員令:「修正錯誤」(接批707 首跑量到的錯誤)

## 一、先分清楚哪些是真的錯

批707 `via-panorama read .` 在活樹 2,189 檔量到的嚴重類只有兩種:

| 類 | 件數 | 真相 |
|---|---|---|
| PSDUPFN | 14 | **全是我引擎的誤報**:here-string 裡內嵌的 JavaScript(fmt/render/done…)、產生別支腳本的模板(EnsureDir/def_Main)、不同父函式裡的同名區域函式(Test-Prot)。 |
| DUPDEF | 317 | 活樹 211 · 凍結副本 106(SCOPE_COPY、`new modules engines/` 的 bundle/sandbox、VIA_Standalone_Package、唯讀 `ssot/`,一律不動)。 |

## 二、修法:零行為變更

Python 同一層同名定義,**執行期只會用到最後一個**,前面的是死碼。所以刪掉前者不會改變行為。前提是兩個定義之間沒有東西在載入時用到前者,因此修正器加了三道閘:

1. 前者有裝飾器 → 跳過(可能有註冊副作用;setter/overload 是刻意同名,不算錯)。
2. 兩者之間「載入期就執行」的程式碼(裝飾器、預設值、類別本體、模組層陳述式)提到這個名字 → 跳過;中間只要有呼叫本檔自己定義的名字,就退回最嚴格判準(連函式本體都不准提)。
3. 修後必須 `ast.parse` 過,且沿「最後生效」的定義樹,每一個定義的原始碼逐字不變;否則整檔不寫。

第一版的閘 3 自己抓到自己一次:把「被刪掉的前一個 class 裡的方法」也算進比對,於是 `financial_data_standardization.py` 整檔被擋。改成只沿最後生效的定義往下走。

## 三、結果

- **刪掉 167 個死定義**(29 檔,−922 行)。有版號的三支照尾版律切新版:CGC_MDL135 v0115、VRN_ENG086 v0114、VIA_VRN_FirstPageEngine v0128;舊版不動。
- **跳過 44 個**:前者在載入期確實被用過(例如 `accelerate`、`xbatch` 先定義後包裝、`def_main` 被引用),那是刻意的「先定義再覆寫」,刪了反而改變行為。重跑後活樹的 DUPDEF 正好剩這 44 個。
- 驗證:全數 `py_compile` 通過;有自測的 16 支,修前與修後的自測輸出去掉時間戳後**逐行相同**(MDL135 53/53;ENG086 28 OK/2 FAIL 前後相同;FirstPageEngine 42 OK/11 FAIL 前後相同,11 FAIL 為本境缺料,修前就有)。
- VRN_ENG086 v0113 的 16 件,根因是 v0113「疊在 v0112 上」時把整段函式重貼了一份(第二個加速器橋、第二個 `HERE =` 都在)。

## 四、全景代讀自己的錯(CGC_MDL158 v0105 就地修;尚未併入 main)

- PowerShell 讀取先遮掉 here-string 內容(行數不變),再比對同名;同名只在**同一個父作用域**內才算。
- 自測 +㉛ 誤報反例(here-string JS、模板、不同父函式的區域函式都不得報;同父內真重複照報)→ **34/34**。
- 重跑:四支 .ps1 與 Register v0242 PSDUPFN 皆 0。

## 五、冊

- 格子 v0460 站名「三十四檢」,`--only 全景稽核修復` 單站 OK。
- 元件冊 VCGC `registry-sync --apply`(新 1 · 變更 432,多為行號位移)。

## 六、沒動、候令

- 凍結副本 106 件:那是交付包/快照,改了會跟包內 MANIFEST 或原交付不一致。要同步修請指名哪一包。
- 44 件刻意覆寫:行為依賴前者,若要整併成一個定義會改行為,需逐件裁定。

## 併 main 後的改號(批734)

main 在 PR #104 開著期間前進到批733:MDL158 升 v0106(新增 digest、token 尺改 CJK 感知)、EnvGovernance 升 v0116、
ENG086 升 v0116、FirstPageEngine 升 v0129(`_esc` 重複已不在)。所以:
- 撤掉本 PR 原本切的 EnvGovernance v0115 / ENG086 v0114 / FirstPageEngine v0128(從未進 main,已非尾版);
- 在 main 的尾版上重套:**EnvGovernance v0117**(刪 1)· **ENG086 v0117**(刪 16),自測輸出修前修後逐行相同;
- PowerShell 誤報修正移到 **CGC_MDL158 v0107**(v0106 仍會報那 14 件),自測 38/38;格子 v0492 站名「三十八檢」;
- 無版號的 26 支支援模組 main 沒動過,原修正照舊有效;
- `CLAUDE.md` 改成永遠取 MDL158 尾版,不再寫死版號。

## 更正:我違反了批345 不可動律,已還原

VCGC 盤點 VDF 工具格時才看到 SUP_MDL737 的一句話:「兩支加速器工具本體一個位元都沒動(**批345 不可動律**)」,
L50 第②層也寫著「兩支工具本體與收容正本一個位元都不動」。批708 那一刀刪到了 `VeritasCeleritas.py` ×3、`VeritasAegisNexus.py` ×3
(含正典 `accelerator/`、`network/`),而 `50_Protection_Acceleration/` 與 `supportive modules/network/` 本來就在
via_bridge_sweeper 的豁免名冊(EXEMPT_INTAKE / EXEMPT_SELF / EXEMPT_LEGACY_NET)上。**6 檔全數還原成 main 原樣**。
修正器當初只排了凍結夾,沒去讀既有的不可動名冊——先查再改(L01)。刪死碼仍然是零行為變更,但律管的是位元組,不是行為。

## 附:修正器原始碼(一次性,留作存證)

```python
"""零行為變更的 DUPDEF 修正:刪掉被同層後者蓋掉的前一個定義。
安全閘:前者有裝飾器=跳過;前者與最後一個定義之間,任何陳述式(含函式本體)提到這個名字=跳過;
修後 ast.parse 必過,且每一層「最後生效的定義」原始碼逐字不變,否則整檔不寫。"""
import ast, sys, json
from pathlib import Path

def scopes(tree):
    yield tree
    for nd in ast.walk(tree):
        if isinstance(nd, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            yield nd

DEFS = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)

def mentions(stmts, name):
    for st in stmts:
        for n in ast.walk(st):
            if isinstance(n, ast.Name) and n.id == name: return True
            if isinstance(n, ast.Attribute) and n.attr == name: return True
            if isinstance(n, ast.Constant) and n.value == name: return True
    return False

def _root(f):
    """呼叫對象的根名字:foo() → foo;a.b().c() → a;(x / 'y').z() → x;認不出來 → "<?>"(視為本地,保守)。"""
    while True:
        if isinstance(f, ast.Attribute): f = f.value
        elif isinstance(f, ast.Call): f = f.func
        elif isinstance(f, ast.Subscript): f = f.value
        elif isinstance(f, ast.BinOp): f = f.left
        else: break
    if isinstance(f, ast.Name): return f.id
    if isinstance(f, ast.Constant): return "<const>"
    return "<?>"

def executed(stmts):
    """載入時就會執行的節點:函式只取裝飾器/預設值/註記;類別取基底/裝飾器並遞迴類別本體;其餘整句。"""
    out = []
    for st in stmts:
        if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out += st.decorator_list + st.args.defaults + [d for d in st.args.kw_defaults if d is not None]
            out += [a.annotation for a in st.args.args + st.args.kwonlyargs if a.annotation is not None]
            if st.returns is not None: out.append(st.returns)
        elif isinstance(st, ast.ClassDef):
            out += st.decorator_list + st.bases + [k.value for k in st.keywords] + executed(st.body)
        else:
            out.append(st)
    return out

def plan(src):
    tree = ast.parse(src)
    kill, skip = [], []
    for sc in scopes(tree):
        body = sc.body
        byname = {}
        for i, st in enumerate(body):
            if isinstance(st, DEFS):
                byname.setdefault(st.name, []).append(i)
        for name, idxs in byname.items():
            if len(idxs) < 2: continue
            last = idxs[-1]
            for i in idxs[:-1]:
                st = body[i]
                deco = [ast.unparse(d) for d in st.decorator_list]
                if any(not (d.endswith((".setter", ".deleter", ".register")) or d in ("overload", "typing.overload")) for d in deco) and deco:
                    skip.append((name, st.lineno, "前者有裝飾器(可能有註冊副作用)")); continue
                if deco:  # setter/overload 是刻意同名,不算錯
                    continue
                between = body[i + 1:last]
                ex = executed(between)
                local = set(byname)             # 本層定義的名字 + 值裡帶到本層定義的變數(可能持有本檔函式)
                for st2 in body:
                    if isinstance(st2, ast.Assign) and any(isinstance(n, ast.Name) and n.id in byname for n in ast.walk(st2.value)):
                        local |= {t.id for t in st2.targets if isinstance(t, ast.Name)}
                strict = any(isinstance(n, ast.Call) and (_root(n.func) in local or _root(n.func) == "<?>") for e in ex for n in ast.walk(e))
                if mentions(ex, name) or (strict and mentions(between, name)):
                    skip.append((name, st.lineno, "兩個定義之間有程式用到這個名字(那時綁的是前者)")); continue
                kill.append((st.lineno, st.end_lineno, name, body[last].lineno))
    return tree, kill, skip

def final_defs(tree, lines):
    """只沿「最後生效」的定義往下走:每一層同名只取最後一個,再遞迴進它的本體。"""
    out = {}
    def walk(body, prefix):
        eff = {}
        for st in body:
            if isinstance(st, DEFS):
                eff[st.name] = st
        for name, st in eff.items():
            out[prefix + name] = "\n".join(lines[st.lineno - 1: st.end_lineno])
            walk(st.body, prefix + name + ".")
    walk(tree.body, "")
    return out

def fix(path, apply):
    raw = Path(path).read_bytes()
    src = raw.decode("utf-8-sig")
    bom = raw.startswith(b"\xef\xbb\xbf")
    tree, kill, skip = plan(src)
    lines = src.split("\n")
    if not kill:
        return {"file": path, "removed": [], "skipped": skip}
    drop = set()
    for a, b, *_ in kill:
        drop.update(range(a - 1, b))
        j = b                                   # 連帶刪掉緊跟在後的空行(最多 2 行),保持排版
        while j < len(lines) and j - b < 2 and lines[j].strip() == "":
            drop.add(j); j += 1
    new = "\n".join(l for k, l in enumerate(lines) if k not in drop)
    t2 = ast.parse(new)                         # 修後必須能 parse
    before = final_defs(tree, lines); after = final_defs(t2, new.split("\n"))
    if before != after:
        raise SystemExit(f"ABORT {path}: 最後生效的定義有變")
    if apply:
        Path(path).write_bytes((b"\xef\xbb\xbf" if bom else b"") + new.encode("utf-8"))
    return {"file": path, "removed": [(n, a, b, keep) for a, b, n, keep in kill], "skipped": skip}

if __name__ == "__main__":
    apply = "--apply" in sys.argv
    res = [fix(p, apply) for p in sys.argv[1:] if p != "--apply"]
    print(json.dumps(res, ensure_ascii=False, indent=1))
```
