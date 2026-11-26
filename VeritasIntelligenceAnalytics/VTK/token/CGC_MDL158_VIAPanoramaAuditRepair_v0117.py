#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""CGC_MDL158_VIAPanoramaAuditRepair v0117 — 薄尾:省 Token 再升級(JSON 深卡 · JSONL 卡 · JSON 路徑切片 · 薄尾鏈圖)

操作員令(側線 2026-09-29 i):「既有的工具功能下再進一步升級優化 TOKEN SAVING 工具 · AI 進入讀取後開始使用」。
實測缺口(本輪追 VDF 管理器 / SDD / 編號 / 系統管理器的薄尾鏈,與讀工作流冊 · 需求冊 · 編號冊時量到):
  ① read 讀 .jsonl 只給行數與位元組,看不到欄位 → 本版:列數 · 每個鍵的出現次數與型別 · 頭尾各一列的縮影。
  ② read 讀 .json 只到第一層(list workflows[11] 看不到元素長相)→ 本版預設看兩層(--depth N):list 內 dict 的鍵聯集與次數。
  ③ slice 直接拒 JSON → 本版 slice <檔.json|.jsonl> <路徑>:a.b[0].c · [-1] · [*] 全展開 · [鍵=值] 篩選;超過 --max 字截斷照報。
  ④ 薄尾鏈沒有地圖(每次都 grep)→ 本版 chain <家族名|檔> [--all]:由新到舊每一版的行數 · 首行說明 · 前版怎麼接
     (glob 取前版 / 釘名 / exec 本體 / 無)· 本版自己定義的函式 · 其中蓋掉前版同名的函式;釘名的標 PINVER 風險。
.py / .ps1 / 夾的 read · slice · digest · pack · --if-etag 一字不動轉 v0116;[token 帳] 尾行格式照舊。
唯讀:不寫檔、不執行被讀的檔(chain 只做 ast.parse)。
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import ast
import collections
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
_STEM = "CGC_MDL158_VIAPanoramaAuditRepair"


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


_PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum,
                  default=HERE / "CGC_MDL158_VIAPanoramaAuditRepair_v0116.py")   # the prior this tail was cut from (⑭ follows the chain)
_spec = importlib.util.spec_from_file_location("panorama_prior_for_" + Path(__file__).stem, _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    return getattr(PRIOR, name)


_NAMES = ("_ACCEL_EXEMPT", "_TREE_EXEMPT")                  # carried over from v0116 (parameter tables only grow)
TOKEN_VERBS = ("read", "slice", "digest", "pack", "chain")
USAGE = "via-panorama read <檔或夾> | slice <檔> <名> | digest [日誌] [--if-etag ETAG] | pack [夾] [--if-etag ETAG]"   # v0116 原值一字不動
USAGE_V0117 = "read <檔.json|.jsonl> [--depth N] | slice <檔.json|.jsonl> <路徑> [--max N] | chain <家族名|檔> [--all]"   # 本版只增


def pack_payload(root, limit: int = 200) -> dict:
    return PRIOR.pack_payload(root, limit)


def digest_log(text: str) -> dict:
    return PRIOR.digest_log(text)
JSONISH = (".json", ".jsonl")
PATH_RX = re.compile(r"([^.\[\]]+)|\[(-?\d+)\]|(\[\*\])|\[([^=\]]+)=([^\]]*)\]")


def _footer(src: str, card: str, etag: str) -> str:
    a, b = PRIOR._tok(len(src), src), PRIOR._tok(len(card), card)
    pct = round(100 * (a - b) / a, 1) if a else 0.0
    return f"[token 帳] 原檔≈{a} · 骨架卡≈{b} · 省 {pct}%(ASCII≈4 字元/token · CJK≈1 字元/token;負數照報不修飾) · etag={etag}"


def _type(v) -> str:
    return {dict: "dict", list: "list", str: "str", int: "int", float: "float", bool: "bool", type(None): "null"}.get(type(v), type(v).__name__)


def _size(v) -> str:
    return f"[{len(v)}]" if isinstance(v, (dict, list, str)) else ""


def _keys_of(items) -> str:
    cnt = collections.Counter(k for x in items if isinstance(x, dict) for k in x)
    shown = [f"{k}({n})" for k, n in cnt.most_common(30)]
    return " ".join(shown) + (f" …+{len(cnt) - 30}" if len(cnt) > 30 else "")


def _shape(v, depth: int, indent: int = 1) -> list:
    pad = "  " * indent
    out = []
    if isinstance(v, dict):
        for i, (k, x) in enumerate(v.items()):
            if i >= 60:
                out.append(f"{pad}… 另 {len(v) - 60} 鍵")
                break
            out.append(f"{pad}{_type(x):>6} {k}{_size(x)}")
            if depth > 1 and isinstance(x, (dict, list)) and x:
                out += _shape(x, depth - 1, indent + 1)
    elif isinstance(v, list) and v:
        types = collections.Counter(_type(x) for x in v)
        out.append(f"{pad}[*] " + " · ".join(f"{t} × {n}" for t, n in types.most_common()))
        dicts = [x for x in v if isinstance(x, dict)]
        if dicts:
            out.append(f"{pad}    鍵(出現次數):{_keys_of(dicts)}")
            if depth > 1:
                nested = {k: x for d in dicts for k, x in d.items() if isinstance(x, (dict, list)) and x}
                for k, x in list(nested.items())[:12]:
                    out.append(f"{pad}    {_type(x):>6} [*].{k}{_size(x)}(首見)")
                    if depth > 2:
                        out += _shape(x, depth - 2, indent + 3)
    return out


def json_card(path: Path, depth: int = 2) -> dict:
    """Skeleton card of a .json / .jsonl book: shape, key unions, sizes. Nothing is executed."""
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    head = f"## {path}  [{path.suffix.lstrip('.')} · {text.count(chr(10)) + (0 if text.endswith(chr(10)) else 1)} 行 · {path.stat().st_size} B]"
    lines = [head]
    if path.suffix == ".jsonl":
        rows, bad = [], 0
        for line in text.splitlines():
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except ValueError:
                    bad += 1
        types = collections.defaultdict(set)
        for r in rows:
            if isinstance(r, dict):
                for k, x in r.items():
                    types[k].add(_type(x))
        cnt = collections.Counter(k for r in rows if isinstance(r, dict) for k in r)
        lines.append(f"  列 {len(rows)}" + (f" · 壞列 {bad}" if bad else ""))
        lines.append("  鍵(出現次數:型別):" + " ".join(f"{k}({n}:{'/'.join(sorted(types[k]))})" for k, n in cnt.most_common(40)))
        for tag, r in (("首列", rows[0] if rows else None), ("末列", rows[-1] if rows else None)):
            if r is not None:
                s = json.dumps(r, ensure_ascii=False, separators=(",", ":"))
                lines.append(f"  {tag} {s[:220]}{'…' if len(s) > 220 else ''}")
    else:
        try:
            obj = json.loads(text)
        except ValueError as exc:
            lines.append(f"  [SYNTAX] JSON 解析不過:{exc}")
            obj = None
        if obj is not None:
            lines.append(f"  頂層 {_type(obj)}{_size(obj)} · 看 {depth} 層(--depth N 可加深)")
            lines += _shape(obj, depth)
    card = "\n".join(lines)
    etag = PRIOR.text_etag(text)
    return {"card": card, "etag": etag, "footer": _footer(text, card, etag)}


def json_slice(path: Path, spec: str, max_chars: int = 4000) -> dict:
    """a.b[0].c · [-1] · [*] fans out · [key=value] filters a list of dicts; a .jsonl book is a list of rows."""
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    root = [json.loads(x) for x in text.splitlines() if x.strip()] if path.suffix == ".jsonl" else json.loads(text)
    cur, fan = [root], False
    for m in PATH_RX.finditer(spec):
        key, idx, star, fk, fv = m.groups()
        nxt = []
        for node in cur:
            if key is not None:
                if isinstance(node, dict) and key in node:
                    nxt.append(node[key])
            elif idx is not None:
                i = int(idx)
                if isinstance(node, list) and -len(node) <= i < len(node):
                    nxt.append(node[i])
            elif star:
                fan = True
                nxt.extend(node if isinstance(node, list) else (list(node.values()) if isinstance(node, dict) else []))
            else:
                fan = True
                if isinstance(node, list):
                    nxt.extend(x for x in node if isinstance(x, dict) and str(x.get(fk)) == fv)
        cur = nxt
    value = cur if fan else (cur[0] if cur else None)
    body = json.dumps(value, ensure_ascii=False, indent=1)
    cut = len(body) > max_chars
    shown = body[:max_chars] + (f"\n…(截斷:原長 {len(body)} 字;縮小路徑或加 --max N)" if cut else "")
    etag = PRIOR.text_etag(text)
    return {"found": bool(cur), "value": value, "text": shown, "cut": cut, "etag": etag,
            "footer": f"[token 帳] 整檔≈{PRIOR._tok(len(text), text)} · 片段≈{PRIOR._tok(len(shown), shown)} · etag={etag}"}


# ---------------------------------------------------------------- ④ thin-tail chain map
def _family_files(target: str) -> list:
    p = Path(target)
    if not p.is_absolute() and not p.exists() and (VIA / target).exists():
        p = VIA / target
    if p.is_file():
        stem = re.sub(r"_v\d+$", "", p.stem)
        return sorted(p.parent.glob(stem + "_v*.py"), key=_vnum, reverse=True)
    stem = re.sub(r"_v\d+(\.py)?$", "", target)
    listed = subprocess.run(["git", "ls-files", f"*{stem}_v*.py"], cwd=VIA, capture_output=True, text=True).stdout.splitlines()
    hits = [VIA / x for x in listed if re.fullmatch(re.escape(stem) + r"_v\d+", Path(x).stem)]
    if not hits:
        hits = [x for x in VIA.rglob(stem + "_v*.py") if "references/" not in x.as_posix()]
    folders = collections.Counter(h.parent for h in hits)
    if not folders:
        return []
    home = folders.most_common(1)[0][0]                           # the family's own folder (copies elsewhere are not the chain)
    return sorted((h for h in hits if h.parent == home), key=_vnum, reverse=True)


def _link(text: str, stem: str, name: str) -> str:
    pinned = [x for x in re.findall(re.escape(stem) + r"_v\d+\.py", text) if x != name]
    if re.search(r"exec\s*\(", text) and pinned:
        return "exec 本體 " + pinned[0].rsplit("_", 1)[-1][:-3]
    if re.search(r"\.glob\(", text) and re.search(r"_vnum|<\s*Path\(__file__\)\.name|p\.name\s*<", text):
        return "glob 取前版"
    if pinned:
        return "釘名 " + pinned[0].rsplit("_", 1)[-1][:-3] + "(PINVER 風險)"
    return "本體(無前版連結)"


def chain_map(target: str, show_all: bool = False) -> dict:
    files = _family_files(target)
    if not files:
        return {"found": False, "text": f"  [chain] NODATA:找不到家族 {target} 的版號檔(給家族名如 CGC_MDL245_SDDValidator,或任一版的路徑)"}
    stem = re.sub(r"_v\d+$", "", files[0].stem)
    info = []
    for p in files:
        text = p.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(text)
            defs = [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
            doc = (ast.get_docstring(tree) or "").strip().splitlines()
        except SyntaxError as exc:
            defs, doc = [], [f"SYNTAX L{exc.lineno}"]
        info.append({"file": p.name, "v": p.stem.rsplit("_", 1)[-1], "lines": text.count("\n") + 1, "defs": defs,
                     "doc": (doc[0] if doc else "")[:90], "link": _link(text, stem, p.name)})
    older = set()
    for row in reversed(info):                                   # oldest first: what did earlier versions already define?
        row["overrides"] = [d for d in row["defs"] if d in older and not d.startswith("_") and d not in ("main", "selftest")]
        row["new"] = [d for d in row["defs"] if d not in older]
        older |= set(row["defs"])
    body = max(info, key=lambda r: len(r["defs"]))
    shown = info if show_all else info[:12]
    lines = [f"## chain {stem} · {len(info)} 版(由新到舊)· 本體(定義最多)= {body['v']}({len(body['defs'])} 個定義)· 釘名 "
             f"{sum(1 for r in info if r['link'].startswith('釘名'))} 支 · exec {sum(1 for r in info if r['link'].startswith('exec'))} 支"]
    for r in shown:
        lines.append(f"  {r['v']:<7} {r['lines']:>5} 行 · {r['link']:<22} · 定義 {len(r['defs'])}(新 {len(r['new'])})"
                     + (f" · 蓋前版:{', '.join(r['overrides'][:6])}" + (" …" if len(r["overrides"]) > 6 else "") if r["overrides"] else "")
                     + (f" · {r['doc']}" if r["doc"] else ""))
    if len(info) > len(shown):
        lines.append(f"  … 另 {len(info) - len(shown)} 支較舊的版(--all 全列)")
    return {"found": True, "text": "\n".join(lines), "versions": info}


# ---------------------------------------------------------------- routing
def _opt(argv: list, name: str, default: int) -> int:
    if name in argv and argv.index(name) + 1 < len(argv):
        try:
            return int(argv[argv.index(name) + 1])
        except ValueError:
            return default
    return default


def _targets(argv: list) -> list:
    out, skip = [], False
    for a in argv[1:]:
        if skip:
            skip = False
            continue
        if a in ("--depth", "--max", "--if-etag", "--limit", "--max-defs", "--workers", "--classes"):
            skip = True
            continue
        if not a.startswith("--"):
            out.append(a)
    return out


def _resolve(t: str) -> Path:
    p = Path(t)
    return p if p.exists() or p.is_absolute() else (VIA / t if (VIA / t).exists() else p)


def route(argv: list) -> str:
    """Which door serves this call: 'json-read' · 'json-slice' · 'chain' · 'prior'."""
    verb = argv[0] if argv else ""
    tg = _targets(argv)
    if verb == "chain":
        return "chain"
    if verb == "read" and len(tg) == 1 and _resolve(tg[0]).suffix in JSONISH and _resolve(tg[0]).is_file():
        return "json-read"
    if verb == "slice" and len(tg) == 2 and _resolve(tg[0]).suffix in JSONISH:
        return "json-slice"
    return "prior"


def main() -> int:
    argv = sys.argv[1:]
    if argv == ["--selftest"]:
        return selftest()
    door = route(argv)
    if door == "prior":
        return PRIOR.main()
    tg = _targets(argv)
    etag_in = argv[argv.index("--if-etag") + 1] if "--if-etag" in argv and argv.index("--if-etag") + 1 < len(argv) else ""
    if door == "chain":
        if not tg:
            print("  [chain] 用法:chain <家族名|任一版的檔> [--all]")
            return 2
        r = chain_map(tg[0], "--all" in argv)
        print(r["text"])
        return 0 if r["found"] else 3
    path = _resolve(tg[0])
    if not path.is_file():
        print(f"  [{argv[0]}] ABSENT:找不到:{tg[0]}")
        return 3
    try:
        if door == "json-read":
            r = json_card(path, _opt(argv, "--depth", 2))
            if etag_in and etag_in == r["etag"]:
                print(f"[304_NOT_MODIFIED] etag={r['etag']} 原檔未變,沿用上一張骨架卡")
                return 0
            print(r["card"] + "\n" + r["footer"])
            return 0
        r = json_slice(path, tg[1], _opt(argv, "--max", 4000))
    except (OSError, ValueError) as exc:
        print(f"  [{argv[0]}] ABSENT:{type(exc).__name__}: {exc}")
        return 3
    if etag_in and etag_in == r["etag"]:
        print(f"[304_NOT_MODIFIED] etag={r['etag']} 原檔未變,沿用上一個片段")
        return 0
    if not r["found"]:
        print(f"  [slice] NODATA:{path.name} 沒有路徑 {tg[1]}(先 read 看骨架卡)")
        return 3
    print(f"## {path.name} · {tg[1]}\n{r['text']}\n{r['footer']}")
    return 0


# ---------------------------------------------------------------- selftest
def selftest() -> int:
    import contextlib
    import io
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "w.json").write_text(json.dumps({"schema": "x", "workflows": [
            {"code": "A-WKF001", "steps": [{"code": "A-WKF001-STP001", "verb": "run"}], "spec": {"requirements": ["A-REQ001"]}},
            {"code": "A-WKF002", "steps": [], "spec": {"requirements": []}}]}, ensure_ascii=False), encoding="utf-8")
        (d / "b.jsonl").write_text('{"code":"C1","key":"k1","n":1}\n{"code":"C2","key":"k2"}\n', encoding="utf-8")
        card = json_card(d / "w.json")
        deep = json_card(d / "w.json", depth=3)
        chk("① JSON 卡:預設兩層看到 list 內 dict 的鍵聯集與次數;--depth 3 再看到元素裡的巢狀", "鍵(出現次數):code(2) steps(2) spec(2)" in card["card"]
            and "[*].steps" not in card["card"] and "[*].steps" in deep["card"], card["card"].splitlines()[2:6])
        jl = json_card(d / "b.jsonl")
        chk("② JSONL 卡:列數 · 鍵次數與型別 · 首末列縮影", "列 2" in jl["card"] and "code(2:str)" in jl["card"] and "n(1:int)" in jl["card"]
            and "首列" in jl["card"] and "末列" in jl["card"])
        s1 = json_slice(d / "w.json", "workflows[0].steps[-1].verb")
        s2 = json_slice(d / "w.json", "workflows[*].code")
        s3 = json_slice(d / "w.json", "workflows[code=A-WKF002].spec")
        s4 = json_slice(d / "b.jsonl", "[1].key")
        s5 = json_slice(d / "w.json", "workflows[9].code")
        chk("③ JSON 路徑切片:鍵 · 索引 · [-1] · [*] · [鍵=值] · JSONL 當列表;找不到 = NODATA",
            (s1["value"], s2["value"], s3["value"], s4["value"], s5["found"]) == ("run", ["A-WKF001", "A-WKF002"], [{"requirements": []}], "k2", False))
        big = json_slice(d / "w.json", "workflows", max_chars=40)
        chk("④ 切片超長照報截斷,不默默吞掉", big["cut"] and "截斷" in big["text"])
        fam = d / "fam"
        fam.mkdir()
        (fam / "X_MDL001_Demo_v0100.py").write_text('"""body"""\ndef check(): pass\ndef load(): pass\ndef main(): pass\n', encoding="utf-8")
        (fam / "X_MDL001_Demo_v0101.py").write_text('"""tail glob"""\nfrom pathlib import Path\nHERE = Path(".")\n'
                                                    'PRIOR = max(p for p in HERE.glob("X_MDL001_Demo_v*.py") if p.name < Path(__file__).name)\n'
                                                    'def check(): pass\ndef main(): pass\n', encoding="utf-8")
        (fam / "X_MDL001_Demo_v0102.py").write_text('"""tail pinned"""\nPRIOR = "X_MDL001_Demo_v0101.py"\ndef extra(): pass\n', encoding="utf-8")
        cm = chain_map(str(fam / "X_MDL001_Demo_v0102.py"))
        rows = {r["v"]: r for r in cm.get("versions") or []}
        chk("⑤ 薄尾鏈圖:由新到舊 · 前版怎麼接(glob / 釘名 / 本體)· 蓋掉前版的函式",
            [r["v"] for r in cm["versions"]] == ["v0102", "v0101", "v0100"] and rows["v0101"]["link"] == "glob 取前版"
            and rows["v0102"]["link"].startswith("釘名 v0101") and rows["v0100"]["link"].startswith("本體") and rows["v0101"]["overrides"] == ["check"],
            {k: (v["link"], v["overrides"]) for k, v in rows.items()})
        routes = (route(["read", str(d / "w.json")]), route(["read", str(fam)]), route(["read", str(fam / "X_MDL001_Demo_v0100.py")]),
                  route(["slice", str(d / "w.json"), "schema"]), route(["slice", str(fam / "X_MDL001_Demo_v0100.py"), "check"]),
                  route(["digest"]), route(["chain", "X"]))
        chk("⑥ 分流:JSON 單檔 read / slice 走本版;.py · 夾 · digest · pack 照舊交 v0116", routes ==
            ("json-read", "prior", "prior", "json-slice", "prior", "prior", "chain"), routes)
        saved = sys.argv
        try:
            sys.argv = ["x", "read", str(d / "w.json"), "--if-etag", card["etag"]]
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = main()
        finally:
            sys.argv = saved
        chk("⑦ --if-etag:JSON 卡沒變回 304", rc == 0 and "304_NOT_MODIFIED" in buf.getvalue())
    real = chain_map("CGC_MDL245_SDDValidator")
    chk("⑧ 實樹:SDD 家族鏈圖讀得到(只 ast.parse,不執行)", real["found"] and len(real["versions"]) >= 4, real["text"].splitlines()[0][:120])
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑨ 檔頭 · 加速器橋 · 網路橋在;不碰 TA-Lib;省 Token 介面(read · slice · digest · pack · chain)齊",
        "VIA:ACCEL-BRIDGE" in text and "VIA:NET-BRIDGE" in text and not re.search(r"^\s*(import|from)\s+talib", text, re.M)
        and all(v in TOKEN_VERBS for v in ("read", "slice", "digest", "pack", "chain")) and set(PRIOR.TOKEN_VERBS) <= set(TOKEN_VERBS)
        and USAGE == PRIOR.USAGE and "chain" in USAGE_V0117 and callable(pack_payload) and callable(digest_log))
    print(f"[省 Token v0117] 本版 {sum(ok)}/{len(ok)}")
    if not all(ok):
        return 1
    saved = sys.argv
    try:
        sys.argv = [saved[0], "--selftest"]
        return PRIOR.selftest()
    finally:
        sys.argv = saved


if __name__ == "__main__":
    raise SystemExit(main())
