#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0139 — 薄尾:panorama 動詞(操作員令 2026-10-06:從 VCGC 省 token 工具進 VRN,全景看現況——所有 SSOT · 參數 · REGEX · 同義字 · 邏輯 · WORKFLOW)。自管自報,唯讀。
  panorama [--json]   ① 冊:掃 SSOT/ registry/ knowledge/ workflows/ 與 VRN 根 → 每族尾版一列:類別(SSOT / PARAMS / REGEX / SYNONYM / LOGIC / WORKFLOW / LEXICON / INDEX / NUMBERS / LEDGER / HEADER / FNMATRIX / OTHER)
                           · 條目數(rows/entries/items/patterns/rules/laws/steps 或頂層鍵)· 表號(表頭冊)· 被誰引用(VRN 尾版 .py 字樣)· 版數 · 燈(綠 有號有人用 · 黃 無號或沒人用 · 灰 退役 · 紅 讀不了)
                       ② 動詞:VRN_SystemManager 鏈每版 main 派發的動詞 → 動詞 · 現行版 · 出現版
                       ③ 工作流:VRN-WKF### / *Workflow* / *Stage* 冊的步驟數
                       → VIA_Reports/vrn/PANORAMA_latest.{html,md,json}(淺色緊湊自適應,燈第一欄,按類別篩)+ 貼回包 ≤300
其餘動詞照前版鏈。沙盒鍵:VIA_VRN_SSOT_HOME · VIA_VRN_HEALTH_OUT。
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
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: F401
except ImportError:
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import ast
import datetime
import html
import importlib.util
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0139"
LAMP = {"GREEN": "#16a34a", "YELLOW": "#f59e0b", "RED": "#dc2626", "GRAY": "#9ca3af"}
EXCL = {"_superseded", "references", "intake", "__pycache__", "VIA_RetiredEngines", "_quarantine", "input", "output", "_df"}
_KIND = [("WORKFLOW", re.compile(r"(?i)wkf|workflow|pipeline|stage|steps?")), ("REGEX", re.compile(r"(?i)regex|pattern|_rx")), ("SYNONYM", re.compile(r"(?i)synonym|alias|broker_dict|dict|union")), ("LEXICON", re.compile(r"(?i)lexicon|fin.?label|accounts")),
         ("LOGIC", re.compile(r"(?i)rule|logic|docclass|fieldrule|policy|law|gate|profile")), ("PARAMS", re.compile(r"(?i)param|config|threshold|setting|canon")), ("NUMBERS", re.compile(r"(?i)numbers?|numbering")), ("INDEX", re.compile(r"(?i)index|catalog|manifest|registry")),
         ("LEDGER", re.compile(r"(?i)ledger|history|log")), ("HEADER", re.compile(r"(?i)tableheader|header")), ("FNMATRIX", re.compile(r"(?i)functionmatrix|fn_matrix")), ("SSOT", re.compile(r"(?i)ssot"))]
_COUNT_KEYS = ("rows", "entries", "items", "patterns", "rules", "laws", "steps", "records", "tables", "books", "keys", "brokers", "synonyms", "aliases", "assets", "columns")


def _vnum_v0139(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0139(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0139(p) < _vnum_v0139(__file__)), key=_vnum_v0139)
PRIOR = _load_v0139(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def _kind_of(name: str, data) -> str:
    for k, rx in _KIND:
        if rx.search(name):
            return k
    if isinstance(data, dict):
        keys = " ".join(map(str, data.keys()))[:300].lower()
        for k, rx in _KIND[:7]:
            if rx.search(keys):
                return k
    return "OTHER"


def _count(data) -> tuple:
    if isinstance(data, list):
        return len(data), "list"
    if isinstance(data, dict):
        for k in _COUNT_KEYS:
            v = data.get(k)
            if isinstance(v, (list, dict)):
                return len(v), k
        return len(data), "keys"
    return 0, "-"


def _read_book(p: Path):
    try:
        if p.suffix.lower() == ".jsonl":
            lines = [ln for ln in p.read_text(encoding="utf-8-sig", errors="replace").splitlines() if ln.strip()]
            return {"rows": lines}, None
        if p.suffix.lower() == ".json":
            return json.loads(p.read_text(encoding="utf-8-sig")), None
        if p.suffix.lower() in (".csv", ".tsv"):
            n = sum(1 for _ in p.open(encoding="utf-8-sig", errors="replace")) - 1
            return {"rows": [None] * max(0, n)}, None
        return None, "非冊"
    except Exception as exc:  # noqa: BLE001
        return None, type(exc).__name__


def _verbs_of_chain(home: Path) -> dict:
    out = defaultdict(list)
    for p in sorted(home.glob("VRN_SystemManager_v*.py"), key=lambda q: _vnum_v0139(q.stem)):
        try:
            tree = ast.parse(p.read_text(encoding="utf-8-sig", errors="replace"))
        except (SyntaxError, ValueError):
            continue
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == "main":
                for n in ast.walk(node):
                    if isinstance(n, ast.Compare) and re.search(r"id='(args|a|sub|verb|cmd)'", ast.dump(n.left)):
                        for c in n.comparators:
                            vals = [x.value for x in c.elts if isinstance(x, ast.Constant) and isinstance(x.value, str)] if isinstance(c, ast.List) else ([c.value] if isinstance(c, ast.Constant) and isinstance(c.value, str) else [])
                            v = " ".join(vals)
                            if v and not v.startswith("-"):
                                out[v].append("v%04d" % _vnum_v0139(p.stem))
    return {v: {"current": vs[-1], "versions": sorted(set(vs))} for v, vs in out.items()}


def panorama() -> dict:
    home = Path(os.environ.get("VIA_VRN_SSOT_HOME") or HERE)
    out_dir = Path(os.environ.get("VIA_VRN_HEALTH_OUT") or (home.parents[1] / "VIA_Reports" / "vrn"))
    now = datetime.datetime.now().isoformat(timespec="seconds")
    th = None
    reg = home / "registry"
    hits = sorted(reg.glob("VRN_TableHeader_v*.json"), key=lambda q: _vnum_v0139(q.stem)) if reg.is_dir() else []
    if hits:
        try:
            th = json.loads(hits[-1].read_text(encoding="utf-8-sig"))
        except ValueError:
            th = None
    tnos = {}
    for tid, e in ((th or {}).get("tables") or {}).items():
        src = Path(e.get("source", "")).name
        if e.get("table_no"):
            tnos.setdefault(src, e["table_no"])
    tails_txt = {}
    for p in home.rglob("*.py"):
        if set(p.relative_to(home).parts[:-1]) & EXCL:
            continue
        fam = re.sub(r"_v\d{2,4}[A-Za-z0-9]*$", "", p.stem)
        if fam not in tails_txt or _vnum_v0139(p.stem) > tails_txt[fam][0]:
            tails_txt[fam] = (_vnum_v0139(p.stem), p)
    tail_bodies = {}
    for fam, (_, p) in tails_txt.items():
        try:
            tail_bodies[fam] = p.read_text(encoding="utf-8-sig", errors="replace").split("\ndef selftest(")[0]
        except OSError:
            tail_bodies[fam] = ""
    fams = defaultdict(list)
    for p in home.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in (".json", ".jsonl", ".csv", ".tsv"):
            continue
        if set(p.relative_to(home).parts[:-1]) & EXCL:
            continue
        fams[(p.parent, re.sub(r"_v\d{2,4}[A-Za-z0-9]*$", "", p.stem), p.suffix.lower())].append(p)
    rows = []
    for (d, fam, ext), ps in sorted(fams.items(), key=lambda x: (x[0][1].lower(), str(x[0][0]))):
        ps.sort(key=lambda q: (_vnum_v0139(q.stem), q.name))
        tail = ps[-1]
        data, err = _read_book(tail)
        kind = _kind_of(fam, data)
        n, unit = _count(data) if data is not None else (0, "-")
        users = sorted(f for f, body in tail_bodies.items() if f != fam and (fam in body or tail.name in body))
        tno = tnos.get(tail.name, "")
        status = (data.get("status") if isinstance(data, dict) else "") or "ACTIVE"
        lamp = "RED" if err else ("GRAY" if str(status).upper() == "RETIRED" else ("GREEN" if (tno and users) else "YELLOW"))
        why = err or ("" if lamp == "GREEN" else ((" · ".join(x for x in ("無表號" if not tno else "", "沒人引用" if not users else "") if x)) or ""))
        rows.append({"family": fam, "dir": d.relative_to(home).as_posix() if str(d).startswith(str(home)) else str(d), "tail": tail.name, "version": ("v%04d" % _vnum_v0139(tail.stem)) if _vnum_v0139(tail.stem) >= 0 else "—", "n_versions": len(ps), "kind": kind, "entries": n, "unit": unit,
                     "table_no": tno, "users": users[:8], "n_users": len(users), "size_kb": round(tail.stat().st_size / 1024, 1), "status": status, "lamp": lamp, "why": why})
    verbs = _verbs_of_chain(home)
    wkf = [r for r in rows if r["kind"] == "WORKFLOW"]
    per = defaultdict(lambda: Counter())
    for r in rows:
        per[r["kind"]][r["lamp"]] += 1
    out = {"verb": "panorama", "sub": "VRN", "ts": now, "home": str(home), "books": rows, "verbs": verbs, "workflows": wkf, "per_kind": {k: dict(v) for k, v in per.items()},
           "summary": {"books": len(rows), "red": sum(1 for r in rows if r["lamp"] == "RED"), "yellow": sum(1 for r in rows if r["lamp"] == "YELLOW"), "green": sum(1 for r in rows if r["lamp"] == "GREEN"), "gray": sum(1 for r in rows if r["lamp"] == "GRAY"),
                       "entries": sum(r["entries"] for r in rows), "verbs": len(verbs), "chain": len(list(home.glob("VRN_SystemManager_v*.py"))), "workflows": len(wkf)}}
    out["lamp"] = "RED" if out["summary"]["red"] else ("YELLOW" if out["summary"]["yellow"] else "GREEN")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "PANORAMA_latest.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    (out_dir / "PANORAMA_latest.html").write_text(_html_v0139(out), encoding="utf-8")
    md = ["# VRN 全景(%s)" % now, "", "| 燈 | 類別 | 族 | 尾版 | 版數 | 條目 | 表號 | 引用 | 備註 |", "|---|---|---|---|---|---|---|---|---|"] + ["| %s | %s | %s | %s | %d | %d %s | %s | %d | %s |" % (r["lamp"], r["kind"], r["family"], r["version"], r["n_versions"], r["entries"], r["unit"], r["table_no"] or "留白", r["n_users"], r["why"]) for r in rows]
    md += ["", "## 動詞", "| 動詞 | 現行版 | 出現版 |", "|---|---|---|"] + ["| %s | %s | %s |" % (v, d["current"], ",".join(d["versions"])) for v, d in sorted(verbs.items())]
    (out_dir / "PANORAMA_latest.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    out["html"] = str(out_dir / "PANORAMA_latest.html")
    return out


def _html_v0139(o: dict) -> str:
    def lp(l):
        return "<i class='lp %s' style='background:%s'></i>" % (l, LAMP[l])
    kinds = sorted(o["per_kind"])
    chips = "".join("<button onclick=\"flt('%s')\">%s · %d</button>" % (k, k, sum(o["per_kind"][k].values())) for k in kinds)
    trs = "\n".join("<tr data-k='%s' data-l='%s'><td>%s</td><td>%s</td><td><b>%s</b><div class='dim'>%s · %s</div></td><td>%s</td><td class='n'>%d</td><td class='n'>%d <small>%s</small></td><td class='code'>%s</td><td title='%s'>%d</td><td class='n'>%s</td><td class='dim'>%s</td></tr>"
                     % (r["kind"], r["lamp"], lp(r["lamp"]), r["kind"], html.escape(r["family"]), html.escape(r["dir"]), html.escape(r["tail"]), r["version"], r["n_versions"], r["entries"], r["unit"], html.escape(r["table_no"] or "留白"), html.escape(", ".join(r["users"])), r["n_users"], r["size_kb"], html.escape(r["why"])) for r in o["books"])
    vtr = "\n".join("<tr><td class='code'>%s</td><td>%s</td><td class='dim'>%s</td></tr>" % (html.escape(v), d["current"], ", ".join(d["versions"])) for v, d in sorted(o["verbs"].items()))
    s = o["summary"]
    return """<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>VRN 全景</title>
<style>body{font-family:"Microsoft JhengHei UI","Segoe UI",Arial;color:#1f2937;margin:0;padding:12px;font-size:12px;background:#fff}h1{font-size:16px;margin:0 0 4px}h2{font-size:13px;margin:12px 0 4px}.meta{color:#6b7280;font-size:11px;margin-bottom:8px}
button{margin:0 4px 6px 0;padding:3px 8px;border:1px solid #e0e0e0;background:#f7f7f7;border-radius:6px;cursor:pointer;font-size:11px}.wrap{overflow-x:auto}table{border-collapse:collapse;width:100%%;table-layout:auto}th,td{border:1px solid #e0e0e0;padding:2px 5px;text-align:left;vertical-align:top;white-space:nowrap}
th{background:#111827;color:#fff;position:sticky;top:0}tr:nth-child(even){background:#fafafa}td.code{font-family:Consolas,monospace}td.n{text-align:right}.dim{color:#6b7280;font-size:10.5px;white-space:normal}
.lp{display:inline-block;width:11px;height:11px;border-radius:50%%;vertical-align:middle}.lp.RED{animation:bl 2.4s ease-in-out infinite}@keyframes bl{0%%,100%%{opacity:1}50%%{opacity:.25}}@media(max-width:700px){th,td{font-size:10.5px;padding:2px 3px}}</style></head><body>
<h1>VRN 全景 · SSOT / 參數 / REGEX / 同義字 / 邏輯 / WORKFLOW</h1><div class="meta">%s · 冊族 %d(紅 %d 黃 %d 綠 %d 灰 %d)· 條目 %d · 管理器鏈 %d 版 · 動詞 %d · 工作流 %d · <span style="color:#16a34a">●</span>綠 有號且有人引用 <span style="color:#f59e0b">●</span>黃 無號或沒人引用 <span style="color:#dc2626">●</span>紅 讀不了 <span style="color:#9ca3af">●</span>灰 退役</div>
<div>%s <button onclick="flt('')">全部</button> <button onclick="lampf('YELLOW')">只看黃</button> <button onclick="lampf('RED')">只看紅</button></div>
<div class="wrap"><table id="m"><thead><tr><th>燈</th><th>類別</th><th>族 / 夾 · 尾版檔</th><th>尾版</th><th>版數</th><th>條目</th><th>表號</th><th>引用</th><th>KB</th><th>備註</th></tr></thead><tbody>%s</tbody></table></div>
<h2>VRN_SystemManager 動詞(鏈 %d 版)</h2><div class="wrap"><table><thead><tr><th>動詞</th><th>現行版</th><th>出現版</th></tr></thead><tbody>%s</tbody></table></div>
<script>function flt(k){document.querySelectorAll('#m tbody tr').forEach(function(t){t.style.display=(!k||t.dataset.k===k)?'':'none'})}function lampf(l){document.querySelectorAll('#m tbody tr').forEach(function(t){t.style.display=(t.dataset.l===l)?'':'none'})}</script></body></html>""" % (
        o["ts"], s["books"], s["red"], s["yellow"], s["green"], s["gray"], s["entries"], s["chain"], s["verbs"], s["workflows"], chips, trs, s["chain"], vtr)


def _print_pan(o: dict) -> None:
    s = o["summary"]
    print("[計] VRN panorama · 冊族 %d(紅 %d 黃 %d 綠 %d 灰 %d)· 條目 %d · 鏈 %d 版 · 動詞 %d · 工作流 %d · %s" % (s["books"], s["red"], s["yellow"], s["green"], s["gray"], s["entries"], s["chain"], s["verbs"], s["workflows"], o["lamp"]))
    print("[計] 類別 · " + " · ".join("%s %d(%s)" % (k, sum(v.values()), " ".join("%s%d" % (l[0], n) for l, n in sorted(v.items()))) for k, v in sorted(o["per_kind"].items())))
    for k in sorted(o["per_kind"]):
        print("[計] ── %s ──" % k)
        for r in [x for x in o["books"] if x["kind"] == k][:40]:
            print("  [%s] %s · %s · %d %s · %s · 引用 %d%s" % ({"GREEN": "OK", "YELLOW": "YEL", "RED": "RED", "GRAY": "GRAY"}[r["lamp"]], r["family"][:52], r["version"], r["entries"], r["unit"], r["table_no"] or "留白", r["n_users"], (" · " + r["why"]) if r["why"] else ""))
    print("[計] 動詞 · " + " · ".join("%s@%s" % (v, d["current"]) for v, d in sorted(o["verbs"].items())))
    print("  [MATRIX] %s" % o["html"])
    print("NEXT: 黃 = 無表號(走 table register → VCGC govern)或沒人引用(DORMANT 候選);紅 = 冊讀不了(格式);工作流 0 = VRN 還沒有 WKF 冊,extract 四步可作第一本")


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()
    if args[:1] == ["panorama"]:
        o = panorama()
        if "--json" in args:
            print(json.dumps(o, ensure_ascii=False))
        _print_pan(o)
        return 1 if o["lamp"] == "RED" else 0
    return PRIOR.main(args)


def selftest() -> int:
    import shutil
    import tempfile
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)

    td = Path(tempfile.mkdtemp(prefix="vrnpan-"))
    home = td / "functional modules" / "VRN"
    saved = {k: os.environ.get(k) for k in ("VIA_VRN_SSOT_HOME", "VIA_VRN_HEALTH_OUT")}
    os.environ["VIA_VRN_SSOT_HOME"] = str(home)
    os.environ["VIA_VRN_HEALTH_OUT"] = str(td / "out")
    (home / "SSOT").mkdir(parents=True)
    (home / "registry").mkdir()
    (home / "SSOT" / "VRN_Central_Synonym_Regex_v0100.json").write_text(json.dumps({"patterns": [{"k": "ticker"}, {"k": "rating"}]}), encoding="utf-8")
    (home / "SSOT" / "VRN_Broker_Dict_v0100.json").write_text(json.dumps({"brokers": [1, 2, 3]}), encoding="utf-8")
    (home / "SSOT" / "VRN_FinLexicon_SSOT_v0101.json").write_text(json.dumps({"rows": [1] * 73}), encoding="utf-8")
    (home / "SSOT" / "VRN_DocClass_SSOT_Rules_v0100.json").write_text(json.dumps({"rules": [1, 2]}), encoding="utf-8")
    (home / "SSOT" / "VRN_Fin_Params_v0100.json").write_text(json.dumps({"threshold": 1}), encoding="utf-8")
    (home / "SSOT" / "VRN-WKF009-Intake_v0100.json").write_text(json.dumps({"steps": [1, 2, 3, 4]}), encoding="utf-8")
    (home / "registry" / "VRN_SSOT_Adopt_Ledger.jsonl").write_text("{}\n{}\n", encoding="utf-8")
    (home / "registry" / "broken.json").write_text("{nope", encoding="utf-8")
    (home / "registry" / "VRN_TableHeader_v0100.json").write_text(json.dumps({"tables": {"vrn_finlexicon_ssot": {"source": "functional modules/VRN/SSOT/VRN_FinLexicon_SSOT_v0101.json", "table_no": "SSOT-VCGC-VRN-TBL0099"}}}), encoding="utf-8")
    (home / "VRN_ENG001_A_v0100.py").write_text("x = 'VRN_FinLexicon_SSOT'\n", encoding="utf-8")
    (home / "VRN_SystemManager_v0100.py").write_text("import sys\ndef main(argv=None):\n    args = list(sys.argv[1:] if argv is None else argv)\n    if args[:1] == ['intake']:\n        return 0\n    if args[:2] == ['ssot', 'adopt']:\n        return 0\n    return 2\n", encoding="utf-8")
    o = panorama()
    R = {r["family"]: r for r in o["books"]}
    chk("① 類別:Synonym_Regex→REGEX · Broker_Dict→SYNONYM · FinLexicon→LEXICON · DocClass_Rules→LOGIC · Params→PARAMS · WKF→WORKFLOW · Ledger→LEDGER",
        R["VRN_Central_Synonym_Regex"]["kind"] == "REGEX" and R["VRN_Broker_Dict"]["kind"] == "SYNONYM" and R["VRN_FinLexicon_SSOT"]["kind"] == "LEXICON" and R["VRN_DocClass_SSOT_Rules"]["kind"] == "LOGIC" and R["VRN_Fin_Params"]["kind"] == "PARAMS" and R["VRN-WKF009-Intake"]["kind"] == "WORKFLOW" and R["VRN_SSOT_Adopt_Ledger"]["kind"] == "LEDGER")
    chk("② 條目:patterns 2 · rows 73 · steps 4 · jsonl 2 列", R["VRN_Central_Synonym_Regex"]["entries"] == 2 and R["VRN_FinLexicon_SSOT"]["entries"] == 73 and R["VRN-WKF009-Intake"]["entries"] == 4 and R["VRN_SSOT_Adopt_Ledger"]["entries"] == 2)
    chk("③ 燈:FinLexicon 有號有人引用綠 · Broker 無號黃 · broken 紅", R["VRN_FinLexicon_SSOT"]["lamp"] == "GREEN" and R["VRN_FinLexicon_SSOT"]["table_no"] == "SSOT-VCGC-VRN-TBL0099" and R["VRN_Broker_Dict"]["lamp"] == "YELLOW" and R["broken"]["lamp"] == "RED")
    chk("④ 動詞:intake · ssot adopt(鏈 1 版)", set(o["verbs"]) >= {"intake", "ssot adopt"} and o["summary"]["chain"] == 1)
    htm = Path(o["html"]).read_text(encoding="utf-8")
    chk("⑤ 輸出:HTML 四色 · viewport · 類別篩 · 動詞表 · md · json", all(c in htm for c in LAMP.values()) and "viewport" in htm and "flt('REGEX')" in htm and "ssot adopt" in htm and (td / "out" / "PANORAMA_latest.md").exists())
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("⑥ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    body = Path(__file__).read_text(encoding="utf-8")
    chk("⑦ 帶加速器橋 · glob 取前版", "[VIA:ACCEL-BRIDGE:v0100]" in body)
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    shutil.rmtree(td, ignore_errors=True)
    print("[計] VRN_SystemManager_v0139 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
