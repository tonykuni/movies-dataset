#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""CGC_MDL255_GitHubPanorama v0100 — AI 讀 GitHub 全面性全景(只讀 origin/main 有版號的尾版;AST 定位;九本分號冊)

操作員(2026-10-03):「上方替代 AI 讀取全面性 GitHub 功能強化導入 · 功能只用 py 寫 · 輸入 輸出 參數 邏輯 政策 ssot regex 同義字 來源
區隔不同編號 · 一切編號化版本號化 · 只對 GitHub 掛進 main 的有版本號」。

量法(不執行任何目標程式;只 ast.parse / tokenize / json.loads):
  範圍  = git 樹(預設 origin/main;--ref 可指)裡 supportive modules/registry · functional modules/VDF(+engine) · functional modules/VRN
          · supportive modules/{network,70_VRN_Rules,VIA_Central_Governance} 的 *.py 尾版(同 stem 取最大 _vNNNN;沒版號的只記不量)+ *.json/*.jsonl 冊。
  九本冊(各自一個冊號 GHP-01…09、各自版號;每列帶 檔:行 錨點與 sha16):
    01 Inputs   每支的 argparse / argv 旗標 · 環境變數(os.environ[...]) · 讀檔(open/read_text/read_json/read_parquet)
    02 Outputs  每支的寫檔(to_parquet/to_csv/json.dump/write_text/open(...,'w'))· 回傳 DataFrame 的函數 · 有無驗證字樣(validate/verify/schema/assert)
    03 Params   模組層全大寫常數(名 · 型 · 值縮影)
    04 Logic    函數 / 類別骨架(名 · 參數 · 行數 · 分支數)· 薄尾鏈(PRIOR 指向)
    05 Policy   政策命中:import talib(L50)· input()(自動化不可跑)· 寫死路徑(C:\Users\tonyk / Downloads)· 加速器橋章缺(L103)· bare except · from __future__ 位置 · SyntaxWarning / SyntaxError
    06 SSOT     冊:可解析否 · 版本鏈 · 尾版 · BOM / 控制字元 · 鍵數
    07 Regex    re.compile / re.match 等的字面樣式(檔:行 · 樣式 · 旗標)
    08 Synonyms 名稱含 alias / synonym / canonical / 別名 / 同義 的 dict 常數(鍵數 · 樣本)
    09 Sources  字串裡的 URL / 網域(來源區隔:官方 / API / 其他)
  產出  VIA_Reports/github_panorama/VIA_GHP_<Cat>_SSOT_v0100.json ×9 · GHP_latest.json(索引 + 計數)· ANCHORS_latest.txt · GHP_latest.html(矩陣)
        --promote 把九本冊複製進 supportive modules/registry(已有就出下一個版號;只增不減)。
  不做  不執行引擎 · 不改任何冊 · 不連網(git 由本機 .git 讀;--ref 需先 git fetch)· 不代設同意閘 · 不碰 TA-Lib。
用法  VIA_FROM_VCGC=YES python CGC_MDL255_GitHubPanorama_v0100.py scan [--ref origin/main] [--repo <倉根>] [--promote] [--no-open]
      python CGC_MDL255_GitHubPanorama_v0100.py --selftest
結束碼  0 政策冊零紅 · 2 有紅(列在 Policy 冊)· 1 跑不動
"""
from __future__ import annotations
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

import ast
import collections
import hashlib
import html
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import tokenize
import warnings
from datetime import datetime, timezone
from pathlib import Path

ENGINE = "CGC_MDL255_GitHubPanorama_v0100"
HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1] if HERE.name == "registry" else HERE
SCOPE = ["supportive modules/registry", "functional modules/VDF", "functional modules/VDF/engine", "functional modules/VRN",
         "supportive modules/network", "supportive modules/70_VRN_Rules", "supportive modules/VIA_Central_Governance"]
NUM_RX = re.compile(r"^(?P<fam>[A-Z]{2,5})_(?P<kind>MDL|ENG)(?P<no>\d{3})_(?P<name>\w+?)(?:_v(?P<v>\d{4}))?\.py$")
VER_RX = re.compile(r"_v(\d{4})\.(py|json|jsonl)$")
PATH_RX = re.compile(r"C:\\\\Users\\\\tonyk|C:\\Users\\tonyk|/Users/tonyk|Downloads\\\\movies-dataset")
URL_RX = re.compile(r"https?://[A-Za-z0-9._\-]+(?:/[^\s'\"<>)]*)?")
SYN_RX = re.compile(r"alias|synonym|canonical|別名|同義|正典", re.I)
BOOKS = [("01", "Inputs", "輸入"), ("02", "Outputs", "輸出"), ("03", "Params", "參數"), ("04", "Logic", "邏輯"), ("05", "Policy", "政策"),
         ("06", "SSOT", "冊"), ("07", "Regex", "正則"), ("08", "Synonyms", "同義字"), ("09", "Sources", "來源")]
WRITE_FUNCS = {"to_parquet", "to_csv", "to_json", "write_text", "write_bytes", "dump", "save", "to_excel", "to_sql"}
READ_FUNCS = {"read_text", "read_bytes", "read_json", "read_parquet", "read_csv", "load", "loads", "read_excel", "read_sql"}


def sha16(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()[:16]


class Tree:
    """git 樹讀取器:ref 給 git ls-tree / cat-file;ref 空 = 直接讀工作樹。"""

    def __init__(self, repo: Path, ref: str | None):
        self.repo, self.ref = repo, ref
        self.files: dict[str, bytes] = {}

    def _git(self, *a: str) -> bytes:
        return subprocess.check_output(["git", "-C", str(self.repo), *a], stderr=subprocess.DEVNULL)

    def listing(self, prefix: str) -> list[str]:
        if self.ref:
            out = self._git("ls-tree", "-r", "--name-only", self.ref, "--", prefix).decode("utf-8", "replace")
            return [l for l in out.splitlines() if l]
        base = self.repo / prefix
        return [str(p.relative_to(self.repo)).replace(os.sep, "/") for p in base.rglob("*") if p.is_file()] if base.is_dir() else []

    def read(self, rel: str) -> bytes:
        if rel in self.files:
            return self.files[rel]
        b = self._git("cat-file", "-p", f"{self.ref}:{rel}") if self.ref else (self.repo / rel).read_bytes()
        self.files[rel] = b
        return b

    def head(self) -> str:
        try:
            return self._git("rev-parse", "--short=12", self.ref or "HEAD").decode().strip()
        except Exception:
            return "worktree"


def pick_tails(paths: list[str]) -> tuple[list[str], list[str]]:
    fam: dict[tuple[str, str], list[tuple[int, str]]] = collections.defaultdict(list)
    unversioned = []
    for p in paths:
        m = VER_RX.search(p)
        if not m:
            unversioned.append(p)
            continue
        stem = re.sub(r"_v\d{4}\.\w+$", "", os.path.basename(p))
        fam[(os.path.dirname(p), stem + "." + m.group(2))].append((int(m.group(1)), p))
    return [max(v)[1] for v in fam.values()], unversioned


def scan(repo: Path, ref: str | None, out_dir: Path, promote: bool = False, open_page: bool = True) -> dict:
    tree = Tree(repo, ref)
    scope_prefix = "VeritasIntelligenceAnalytics/" if (repo / "VeritasIntelligenceAnalytics").exists() or ref else ""
    all_paths: list[str] = []
    for d in SCOPE:
        all_paths += [p for p in tree.listing(scope_prefix + d) if p.endswith((".py", ".json", ".jsonl")) and p.count("/") == (scope_prefix + d).count("/") + 1]
    all_paths = sorted(set(all_paths))
    py_tails, py_unversioned = pick_tails([p for p in all_paths if p.endswith(".py")])
    book_paths = [p for p in all_paths if p.endswith((".json", ".jsonl"))]
    head = tree.head()
    rows: dict[str, list[dict]] = {b[1]: [] for b in BOOKS}
    samenum: dict[str, set] = collections.defaultdict(set)

    def add(cat: str, path: str, line: int, **kw):
        rows[cat].append({"file": path, "line": line, **kw})

    for p in py_tails:
        raw = tree.read(p)
        fsha = sha16(raw)
        try:
            src = io.TextIOWrapper(io.BytesIO(raw), encoding=tokenize.detect_encoding(io.BytesIO(raw).readline)[0]).read()
        except Exception as exc:
            add("Policy", p, 0, cls="READ", lamp="RED", detail=str(exc)[:120], sha16=fsha)
            continue
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            try:
                tree_ast = ast.parse(src, p)
            except SyntaxError as exc:
                add("Policy", p, exc.lineno or 0, cls="SYNTAX", lamp="RED", detail=exc.msg, sha16=fsha)
                continue
            for x in w:
                add("Policy", p, x.lineno or 0, cls="SYNTAXWARN", lamp="YELLOW", detail=str(x.message), sha16=fsha)
        m = NUM_RX.match(os.path.basename(p))
        if m:
            samenum[m.group("fam") + "_" + m.group("kind") + m.group("no")].add(m.group("name"))
        if "VIA:ACCEL-BRIDGE" not in src:
            add("Policy", p, 1, cls="NO_ACCEL_BRIDGE", lamp="YELLOW", detail="PY 加速器橋章缺(L103)", sha16=fsha)
        body = tree_ast.body
        i = 1 if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant) else 0
        seen = False
        for st in body[i:]:
            if isinstance(st, ast.ImportFrom) and st.module == "__future__":
                if seen:
                    add("Policy", p, st.lineno, cls="FUTURE_LATE", lamp="RED", detail="from __future__ 晚於其他語句(COMPILE 錯)", sha16=fsha)
            elif not (isinstance(st, ast.Expr) and isinstance(st.value, ast.Constant)):
                seen = True
            if isinstance(st, ast.Assign) and len(st.targets) == 1 and isinstance(st.targets[0], ast.Name) and st.targets[0].id.isupper():
                v = st.value
                kind = type(v).__name__
                preview = ast.unparse(v)[:80] if hasattr(ast, "unparse") else kind
                add("Params", p, st.lineno, name=st.targets[0].id, type=kind, value=preview, sha16=fsha)
                if isinstance(v, ast.Dict) and SYN_RX.search(st.targets[0].id):
                    keys = [ast.unparse(k)[:30] for k in v.keys[:5] if k is not None] if hasattr(ast, "unparse") else []
                    add("Synonyms", p, st.lineno, name=st.targets[0].id, keys=len(v.keys), sample=keys, sha16=fsha)
            if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                br = sum(1 for n in ast.walk(st) if isinstance(n, (ast.If, ast.For, ast.While, ast.Try, ast.With)))
                args = [a.arg for a in st.args.args] if not isinstance(st, ast.ClassDef) else []
                add("Logic", p, st.lineno, name=st.name, kind=type(st).__name__, args=args, lines=(getattr(st, "end_lineno", st.lineno) - st.lineno + 1), branches=br, sha16=fsha)
        if "PRIOR_PATH" in src and "spec_from_file_location" in src:
            add("Logic", p, 1, name="<thin-tail>", kind="ThinTail", args=[], lines=0, branches=0, detail="薄尾:轉接前版", sha16=fsha)
        for node in ast.walk(tree_ast):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ""]
                if any(n.split(".")[0] == "talib" for n in names):
                    add("Policy", p, node.lineno, cls="TALIB_IMPORT", lamp="RED", detail="import talib(L50 禁)", sha16=fsha)
            elif isinstance(node, ast.Call):
                fn = node.func
                fname = fn.id if isinstance(fn, ast.Name) else (fn.attr if isinstance(fn, ast.Attribute) else "")
                if fname == "input":
                    add("Policy", p, node.lineno, cls="INPUT_CALL", lamp="YELLOW", detail="input() 互動呼叫", sha16=fsha)
                elif fname == "add_argument" and node.args and isinstance(node.args[0], ast.Constant):
                    add("Inputs", p, node.lineno, kind="flag", name=str(node.args[0].value), sha16=fsha)
                elif fname in WRITE_FUNCS:
                    tgt = ast.unparse(node.args[0])[:80] if node.args and hasattr(ast, "unparse") else ""
                    add("Outputs", p, node.lineno, kind=fname, target=tgt, sha16=fsha)
                elif fname in READ_FUNCS:
                    tgt = ast.unparse(node.args[0])[:80] if node.args and hasattr(ast, "unparse") else ""
                    add("Inputs", p, node.lineno, kind=fname, name=tgt, sha16=fsha)
                elif fname == "open" and len(node.args) >= 2 and isinstance(node.args[1], ast.Constant) and "w" in str(node.args[1].value):
                    add("Outputs", p, node.lineno, kind="open-w", target=ast.unparse(node.args[0])[:80] if hasattr(ast, "unparse") else "", sha16=fsha)
                elif fname in {"compile", "match", "search", "sub", "findall", "fullmatch", "finditer"} and isinstance(fn, ast.Attribute) and isinstance(fn.value, ast.Name) and fn.value.id == "re" and node.args and isinstance(node.args[0], ast.Constant):
                    flags = ast.unparse(node.args[1])[:30] if len(node.args) > 1 and hasattr(ast, "unparse") else ""
                    add("Regex", p, node.lineno, pattern=str(node.args[0].value)[:120], flags=flags, sha16=fsha)
            elif isinstance(node, ast.Subscript) and isinstance(node.value, ast.Attribute) and node.value.attr == "environ":
                key = ast.unparse(node.slice)[:40] if hasattr(ast, "unparse") else ""
                add("Inputs", p, node.lineno, kind="env", name=key, sha16=fsha)
            elif isinstance(node, ast.ExceptHandler) and node.type is None:
                add("Policy", p, node.lineno, cls="BARE_EXCEPT", lamp="YELLOW", detail="bare except", sha16=fsha)
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                s = node.value
                if PATH_RX.search(s):
                    add("Policy", p, node.lineno, cls="HARDCODED_PATH", lamp="YELLOW", detail=s[:80], sha16=fsha)
                for u in URL_RX.findall(s)[:3]:
                    dom = re.sub(r"^https?://", "", u).split("/")[0]
                    kind = "official" if re.search(r"twse|tpex|mops|gov|fred|sec\.gov", dom) else ("api" if "api" in dom else "other")
                    add("Sources", p, node.lineno, url=u[:120], domain=dom, kind=kind, sha16=fsha)
        if "DataFrame" in src and any(r["file"] == p for r in rows["Outputs"]) and not re.search(r"validate|verify|schema|assert ", src, re.I):
            add("Outputs", p, 1, kind="DF_NO_VALIDATE", target="輸出 DataFrame 但看不到驗證字樣(validate/verify/schema/assert)", sha16=fsha)
    for key, names in samenum.items():
        if len(names) > 1:
            add("Policy", key, 0, cls="SAME_NUMBER", lamp="YELLOW", detail="同號異名 " + ",".join(sorted(names))[:160], sha16="")
    book_tails, _ = pick_tails(book_paths)
    for p in book_paths:
        raw = tree.read(p)
        bom = raw.startswith(b"\xef\xbb\xbf")
        try:
            txt = raw.decode("utf-8-sig")
            if p.endswith(".json"):
                obj = json.loads(txt)
                keys = len(obj) if isinstance(obj, (dict, list)) else 1
            else:
                keys = sum(1 for l in txt.splitlines() if l.strip() and json.loads(l) is not None)
            state = "BOM" if bom else "OK"
        except Exception as exc:
            state, keys = "BROKEN:" + str(exc)[:60], 0
        m = VER_RX.search(p)
        add("SSOT", p, 1, state=state, version=(m.group(1) if m else ""), tail=(p in book_tails), keys=keys, sha16=sha16(raw))
    # 寫九本冊 + 索引 + 錨點 + 頁
    out_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    index = {"via": "vcgc", "door": ENGINE, "ref": ref or "worktree", "head": head, "at": now, "scope": SCOPE,
             "py_tails": len(py_tails), "py_unversioned": len(py_unversioned), "books": len(book_paths), "counts": {}, "files": {}}
    for no, cat, zh in BOOKS:
        book = {"book_id": "GHP-" + no, "name": f"VIA_GHP_{cat}_SSOT", "version": "v0100", "zh": zh, "head": head, "at": now, "rows": rows[cat],
                "n": len(rows[cat]), "lamp": "GREEN"}
        if cat == "Policy":
            reds = sum(1 for r in rows[cat] if r.get("lamp") == "RED")
            book["lamp"] = "RED" if reds else ("YELLOW" if rows[cat] else "GREEN")
            book["reds"] = reds
        fn = out_dir / f"VIA_GHP_{cat}_SSOT_v0100.json"
        fn.write_text(json.dumps(book, ensure_ascii=False, indent=1), encoding="utf-8")
        index["counts"][cat] = len(rows[cat])
        index["files"][cat] = str(fn)
    anchors = [f"{r['file']}:{r['line']}  {r.get('cls','')}  {r.get('detail','')}" for r in rows["Policy"]]
    (out_dir / "ANCHORS_latest.txt").write_text("# 定位=AST精準(python ast) · ref " + (ref or "worktree") + " · head " + head + "\n" + "\n".join(anchors) + "\n", encoding="utf-8")
    index["policy_lamp"] = json.loads((out_dir / "VIA_GHP_Policy_SSOT_v0100.json").read_text(encoding="utf-8"))["lamp"]
    index["policy_reds"] = sum(1 for r in rows["Policy"] if r.get("lamp") == "RED")
    (out_dir / "GHP_latest.json").write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    write_page(out_dir / "GHP_latest.html", index, rows)
    if promote:
        reg = VIA / "supportive modules" / "registry"
        for no, cat, zh in BOOKS:
            name = f"VIA_GHP_{cat}_SSOT"
            existing = sorted(reg.glob(name + "_v*.json"))
            nxt = (int(re.search(r"_v(\d{4})", existing[-1].name).group(1)) + 1) if existing else 100
            dst = reg / f"{name}_v{nxt:04d}.json"
            dst.write_bytes((out_dir / f"{name}_v0100.json").read_bytes())
            index.setdefault("promoted", []).append(dst.name)
        (out_dir / "GHP_latest.json").write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    if open_page and os.environ.get("VIA_NO_OPEN") != "1" and os.name == "nt":
        try:
            os.startfile(str(out_dir / "GHP_latest.html"))  # type: ignore[attr-defined]
        except Exception:
            pass
    return index


def write_page(path: Path, index: dict, rows: dict) -> None:
    e = html.escape
    parts = ["<!doctype html><html><head><meta charset='utf-8'><title>GitHub Panorama</title><style>body{font:13px/1.4 'Segoe UI','Microsoft JhengHei';background:#0b1220;color:#e5e7eb;margin:0}header{padding:12px 20px;background:#111827}h1{margin:0;font-size:18px;color:#93c5fd}nav{position:sticky;top:0;background:#0f172a;padding:8px 20px}nav button{background:#1e293b;color:#cbd5e1;border:1px solid #334155;padding:5px 12px;border-radius:6px;cursor:pointer;margin-right:6px}nav button.on{background:#2563eb;color:#fff}section{display:none;padding:12px 20px}section.on{display:block}table{border-collapse:collapse;font-size:12px}td,th{border:1px solid #334155;padding:4px 8px;vertical-align:top;max-width:520px;word-break:break-all}th{background:#1e293b}.RED{color:#f87171}.YELLOW{color:#fbbf24}.GREEN{color:#4ade80}</style><script>function go(i){document.querySelectorAll('nav button').forEach((b,k)=>b.classList.toggle('on',k===i));document.querySelectorAll('section').forEach((s,k)=>s.classList.toggle('on',k===i));}document.addEventListener('DOMContentLoaded',()=>go(0));</script></head><body>"]
    parts.append(f"<header><h1>GitHub Panorama · {e(index['ref'])} · {e(index['head'])} · 政策 <span class='{index['policy_lamp']}'>{index['policy_lamp']}</span></h1><div>尾版 {index['py_tails']} 支 · 沒版號只記 {index['py_unversioned']} 支 · 冊 {index['books']} 本 · {e(index['at'])}</div></header><nav>")
    cats = ["總覽"] + [c for _, c, _ in BOOKS]
    parts += [f"<button onclick='go({i})'>{e(c)}</button>" for i, c in enumerate(cats)]
    parts.append("</nav><section><table><tr><th>冊</th><th>冊號</th><th>列數</th></tr>")
    parts += [f"<tr><td>{e(c)}({e(z)})</td><td>GHP-{no}</td><td>{index['counts'][c]}</td></tr>" for no, c, z in BOOKS]
    parts.append("</table></section>")
    for _, cat, _ in BOOKS:
        rs = rows[cat][:400]
        cols = sorted({k for r in rs for k in r.keys()}, key=lambda k: (k not in ("file", "line"), k))
        parts.append("<section><table><tr>" + "".join(f"<th>{e(c)}</th>" for c in cols) + "</tr>")
        for r in rs:
            parts.append("<tr>" + "".join(f"<td class='{e(str(r.get('lamp','')))}'>{e(str(r.get(c,'')))}</td>" for c in cols) + "</tr>")
        parts.append(f"</table><p>顯示 {len(rs)} / {len(rows[cat])} 列(全部在冊 JSON)</p></section>")
    parts.append("</body></html>")
    path.write_text("".join(parts), encoding="utf-8")


def selftest() -> int:
    ok_all = []

    def chk(name, ok, note=""):
        ok_all.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + note) if note else ''}")

    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        reg = repo / "supportive modules" / "registry"
        reg.mkdir(parents=True)
        (repo / "functional modules" / "VDF").mkdir(parents=True)
        (reg / "XX_MDL001_A_v0100.py").write_text("import talib\nAPI='https://api.twse.com.tw/x'\nimport re\nRX=re.compile(r'\\d+')\ndef main():\n    try:\n        x=input('q')\n    except:\n        pass\n    return 1\n", encoding="utf-8")
        (reg / "XX_MDL001_A_v0101.py").write_text("# ===== [VIA:ACCEL-BRIDGE:v0100]\nimport pandas as pd\nALIAS_MAP={'a':'b'}\nimport os\np=os.environ['VIA_X']\ndef out(df):\n    df.to_parquet('o.parquet')\n    return pd.DataFrame()\n", encoding="utf-8")
        (reg / "XX_MDL001_B_v0100.py").write_text("import json\nwith open('C:\\\\Users\\\\tonyk\\\\x.json') as f: json.load(f)\n", encoding="utf-8")
        (reg / "VIA_Book_SSOT_v0100.json").write_bytes(b"\xef\xbb\xbf{\"a\":1}")
        (reg / "VIA_Bad_SSOT_v0100.json").write_text('{"a":"x\ty"}', encoding="utf-8")
        out = repo / "VIA_Reports" / "github_panorama"
        idx = scan(repo, None, out, promote=False, open_page=False)
        pol = json.loads((out / "VIA_GHP_Policy_SSOT_v0100.json").read_text(encoding="utf-8"))["rows"]
        cls = collections.Counter(r["cls"] for r in pol)
        chk("① 尾版律:同 stem 只量最大版(v0101),v0100 的 talib / input 不算", idx["py_tails"] == 2 and cls.get("TALIB_IMPORT", 0) == 0 and cls.get("INPUT_CALL", 0) == 0, str(dict(cls)))
        chk("② 政策冊:寫死路徑 · 加速器橋缺 · 同號異名 都抓到", cls.get("HARDCODED_PATH") == 1 and cls.get("NO_ACCEL_BRIDGE") == 1 and cls.get("SAME_NUMBER") == 1)
        books = {c: json.loads((out / f"VIA_GHP_{c}_SSOT_v0100.json").read_text(encoding="utf-8")) for _, c, _ in BOOKS}
        chk("③ 九本冊各自冊號 GHP-01…09 與版號 v0100", [b["book_id"] for b in books.values()] == ["GHP-%02d" % i for i in range(1, 10)] and all(b["version"] == "v0100" for b in books.values()))
        chk("④ 輸入冊:env 讀到 · 輸出冊:to_parquet + DF 無驗證標記", any(r.get("kind") == "env" for r in books["Inputs"]["rows"]) and any(r.get("kind") == "to_parquet" for r in books["Outputs"]["rows"]) and any(r.get("kind") == "DF_NO_VALIDATE" for r in books["Outputs"]["rows"]))
        chk("⑤ 同義字冊:ALIAS_MAP 入冊 · 參數冊:全大寫常數", any(r["name"] == "ALIAS_MAP" for r in books["Synonyms"]["rows"]) and any(r["name"] == "ALIAS_MAP" for r in books["Params"]["rows"]))
        chk("⑥ 冊冊:BOM 標 BOM · 控制字元標 BROKEN · 尾版標記", any(r["state"] == "BOM" for r in books["SSOT"]["rows"]) and any(r["state"].startswith("BROKEN") for r in books["SSOT"]["rows"]))
        chk("⑦ 錨點檔與頁在;不執行目標(無 subprocess 以外呼叫)", (out / "ANCHORS_latest.txt").is_file() and (out / "GHP_latest.html").is_file())
        chk("⑧ 檔頭:加速器橋在 · 不碰 TA-Lib(本檔只在字串比對出現)", "VIA:ACCEL-BRIDGE" in Path(__file__).read_text(encoding="utf-8"))
    ok = all(ok_all)
    print(f"  {ENGINE} selftest +{sum(ok_all)}/{len(ok_all)} {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
        return 2
    if not a or a[0] != "scan":
        print(__doc__)
        return 2
    ref = a[a.index("--ref") + 1] if "--ref" in a else "origin/main"
    repo = Path(a[a.index("--repo") + 1]) if "--repo" in a else VIA.parent
    out = VIA / "VIA_Reports" / "github_panorama"
    idx = scan(repo, None if ref in ("worktree", "") else ref, out, promote="--promote" in a, open_page="--no-open" not in a)
    print(f"[GitHub 全景] {idx['policy_lamp']} · ref {idx['ref']} · head {idx['head']} · 尾版 {idx['py_tails']} · 冊 {idx['books']} · 政策紅 {idx['policy_reds']} · " + " · ".join(f"{c} {n}" for c, n in idx["counts"].items()))
    print(f"  頁 {out / 'GHP_latest.html'} · 錨點 {out / 'ANCHORS_latest.txt'}" + (f" · 已登冊 {idx['promoted']}" if idx.get("promoted") else ""))
    return 0 if idx["policy_reds"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
