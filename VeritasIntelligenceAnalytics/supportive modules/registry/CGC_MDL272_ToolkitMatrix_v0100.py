#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC ToolkitMatrix v0100 — 輔助工具整合管理 MATRIX(操作員令 2026-10-06:加速器 · 網路工具 · NLP · SSOT 管理 … 每一功能列清單、舉版本號、MATRIX)。唯讀。
掃 supportive modules(根 + accelerator/ network/ ssot/ ui_support/ audit_tools/ registry 的 CGC_MDL*)+ functional modules 的 NLP;每「族」(去版號)一列:
  類別 · 族 · 夾 · 尾版 · 版數 · 類型 · 入口(頂層 def/class · 動詞字樣)· 誰在用(VRN/VDF/registry 尾版 import 或 glob 到它的檔數)· 加速器橋 · 編號 · 最後更新 · 燈
燈:綠 = 有人用且有橋;黃 = 沒人用(DORMANT 候選)或同類同義族重疊(整合候選)或無橋;灰 = 退役夾/_superseded;紅 = AST 壞 / 檔不在
類別規則(名稱比對,可擴):accelerator · network · nlp · ssot_mgmt(numbering/governance/dataframe/ssot/registry/book) · temp · ui · canon_lib(SUP_MDL75x · LibCanon) · env · verb_bridge(AiVerb/PyCommandHub/ToolLadder) · audit · other
只寫:VIA_Reports/review/vcgc_toolkit/TOOLKIT_MATRIX_latest.{json,html} · docs/handoff/ai/VCGC_ToolkitCard_<日>.md。動詞:matrix [--json] · --selftest   沙盒鍵:VIA_ROOT
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
import json
import os
import re
import shutil
import sys
import tempfile
import time
from collections import defaultdict
from pathlib import Path

ME = Path(__file__).resolve()
NAME = ME.stem
TAG = "v0100"
LAMP = {"GREEN": "#16a34a", "YELLOW": "#f59e0b", "RED": "#dc2626", "GRAY": "#9ca3af"}
EXCL = {"references", "intake", "__pycache__", ".venv", "venv", "node_modules", ".git", "VIA_NumberBooks", "_df", "_inbox_to_classify"}
DORMANT_DIRS = {"_superseded", "VIA_RetiredEngines", "_quarantine", "_quarantine_pip_vendor"}
CATS = [
    ("accelerator", re.compile(r"(?i)celeritas|accel|turbo|speed|parallel|inprocess|fast", re.I)),
    ("network", re.compile(r"(?i)net(support|unified|core|gate|bench)|network|aegis|proxy|request|fetch|akshare|fred|twse|yfinance", re.I)),
    ("nlp", re.compile(r"(?i)nlp|knowledge|synonym_engine|lexicon|tokeniz|embedding", re.I)),
    ("temp", re.compile(r"(?i)tempspill|temp_spill|spill|ssd.?resource", re.I)),
    ("ssot_mgmt", re.compile(r"(?i)ssot|numbering|registry|governance|dataframe|book|canon_registry|panorama|matrix|standardizer|governor", re.I)),
    ("verb_bridge", re.compile(r"(?i)aiverb|pycommand|toolladder|verb|command", re.I)),
    ("canon_lib", re.compile(r"(?i)libcanon|SUP_MDL75[0-9]|commonutils|tailpick|jsonio|polarsframe|intakebaseline|toolkit", re.I)),
    ("env", re.compile(r"(?i)env(manager|registry|gov)|micromamba|mamba|pip_|venv|path", re.I)),
    ("ui", re.compile(r"(?i)\bui\b|uihead|uiengine|dashboard|theme|layout|console|progress|html", re.I)),
    ("audit", re.compile(r"(?i)audit|health|validator|xcheck|smoke|gate|check|precheck|selftest", re.I)),
]
VERB_RX = re.compile(r"(?m)^\s{0,4}(?:[a-z][\w-]+(?: [a-z][\w-]+)?)\s{2,}\S")


def _now() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


def _root() -> Path:
    if os.environ.get("VIA_ROOT"):
        return Path(os.environ["VIA_ROOT"])
    p = ME
    while p.parent != p:
        if (p / "supportive modules").is_dir() and (p / "functional modules").is_dir():
            return p
        p = p.parent
    return ME.parents[2]


def _paths() -> dict:
    r = _root()
    return {"root": r, "sup": r / "supportive modules", "registry": r / "supportive modules" / "registry", "vrn": r / "functional modules" / "VRN", "vdf": r / "functional modules" / "VDF",
            "nlp": r / "functional modules" / "NLP", "cards": r / "docs" / "handoff" / "ai", "out": r / "VIA_Reports" / "review" / "vcgc_toolkit"}


def _vnum(name: str) -> int:
    m = re.search(r"[_-]v(\d{2,4})[A-Za-z0-9]*(?:\.[A-Za-z0-9]+)?$", name)
    return int(m.group(1)) if m else -1


def _ver(name: str) -> str:
    m = re.search(r"[_-](v\d{2,4}[A-Za-z0-9]*)(?:\.[A-Za-z0-9]+)?$", name)
    return m.group(1) if m else "—"


def _family(name: str) -> str:
    stem = re.sub(r"_sha[0-9a-f]{8,}$", "", Path(name).stem)
    stem = re.sub(r"[_-]v\d{2,4}[A-Za-z0-9]*$", "", stem)
    stem = re.sub(r"\.(before|bak|old|backup)\d*$", "", stem)
    return stem


def _read(p: Path, limit: int = 600_000) -> str:
    raw = p.read_bytes()[:limit]
    for enc in ("utf-8-sig", "utf-16", "cp950", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return ""


def _rel(p: Path, P: dict) -> str:
    try:
        return p.relative_to(P["root"]).as_posix()
    except ValueError:
        return p.as_posix()


def _cat(name: str, folder: str) -> str:
    fl = folder.lower()
    for c, rx in CATS:
        if c in fl:
            return c
    for c, rx in CATS:
        if rx.search(name):
            return c
    return "other"


def _scan(P: dict) -> list:
    files = []
    roots = [P["sup"]]
    if P["nlp"].is_dir():
        roots.append(P["nlp"])
    for d in roots:
        for p in d.rglob("*"):
            if not p.is_file() or p.suffix.lower() not in (".py", ".ps1"):
                continue
            parts = set(p.relative_to(P["root"]).parts[:-1])
            if parts & EXCL:
                continue
            if p.parent == P["registry"] and not p.name.startswith(("CGC_", "SUP_")):
                continue   # registry 裡非引擎的 py(工具腳本)不算輔助工具族
            files.append(p)
    return files


def _entry_points(p: Path) -> dict:
    txt = _read(p)
    out = {"defs": 0, "classes": 0, "verbs": [], "accel": False, "ast_ok": True, "lines": txt.count("\n") + 1, "doc": ""}
    if p.suffix.lower() == ".py":
        out["accel"] = "[VIA:ACCEL-BRIDGE" in txt or "VeritasCeleritas_v1141" in txt
        try:
            tree = ast.parse(txt)
            out["doc"] = (ast.get_docstring(tree) or "").split("\n")[0][:90]
            for n in tree.body:
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    out["defs"] += 1
                elif isinstance(n, ast.ClassDef):
                    out["classes"] += 1
            m = re.search(r"動詞[::]\s*(.+)", txt[:4000])
            if m:
                out["verbs"] = [v.strip() for v in re.split(r"[·|,，]", m.group(1)) if v.strip()][:8]
        except (SyntaxError, ValueError):
            out["ast_ok"] = False
    else:
        out["accel"] = bool(re.search(r"\[VIA:PS-ACCEL|VeritasCeleritas\.PS7|Initialize-VCAccel|VIA_PS_Accel_Module", txt))
        out["defs"] = len(re.findall(r"^\s*function\s+[\w:-]+", txt, re.M))
        m = re.search(r"^#\s*(.+)$", txt, re.M)
        out["doc"] = (m.group(1)[:90] if m else "")
    return out


def _users(P: dict, fams: set) -> dict:
    """VRN / VDF / registry 尾版檔案裡 import / glob / 字串提到哪些族。"""
    best = {}
    for d in (P["vrn"], P["vdf"], P["registry"], P["sup"]):
        if not d.is_dir():
            continue
        for p in d.rglob("*"):
            if not p.is_file() or p.suffix.lower() not in (".py", ".ps1"):
                continue
            if set(p.relative_to(P["root"]).parts[:-1]) & (EXCL | DORMANT_DIRS):
                continue
            k = (p.parent, _family(p.name), p.suffix.lower())
            if k not in best or _vnum(p.name) > _vnum(best[k].name):
                best[k] = p
    users = defaultdict(set)
    fam_rx = {f: re.compile(r"(?<![\w])" + re.escape(f) + r"(?=_v\d|\b)") for f in fams if len(f) >= 6}
    for p in best.values():
        txt = _read(p, 300_000).split("\ndef selftest(")[0]
        own = _family(p.name)
        for f, rx in fam_rx.items():
            if f != own and rx.search(txt):
                users[f].add(_rel(p, P))
    return users


def matrix(P: dict | None = None) -> dict:
    P = P or _paths()
    t0 = time.time()
    files = _scan(P)
    fams: dict = defaultdict(list)
    for p in files:
        fams[(p.parent, _family(p.name), p.suffix.lower())].append(p)
    users = _users(P, {f for (_, f, _) in fams})
    rows = []
    for (d, fam, ext), ps in fams.items():
        ps.sort(key=lambda q: (_vnum(q.name), q.name))
        tail = ps[-1]
        folder = _rel(d, P)
        dormant_dir = bool(set(d.parts) & DORMANT_DIRS)
        ep = _entry_points(tail)
        used = sorted(users.get(fam, ()))
        age = (time.time() - tail.stat().st_mtime) / 86400
        cat = _cat(fam, folder)
        why = []
        if dormant_dir:
            lamp = "GRAY"
            why.append("退役/隔離夾")
        elif not ep["ast_ok"]:
            lamp = "RED"
            why.append("AST 失敗")
        else:
            lamp = "GREEN"
            if not used:
                lamp = "YELLOW"
                why.append("沒人引用(DORMANT 候選,%.0f 天未改)" % age)
            if not ep["accel"] and ep["lines"] >= 40:
                lamp = "YELLOW"
                why.append("無加速器橋")
        rows.append({"cat": cat, "family": fam, "folder": folder, "ext": ext, "tail": tail.name, "tail_ver": _ver(tail.name), "n_versions": len(ps), "versions": [_ver(q.name) for q in ps][-10:],
                     "defs": ep["defs"], "classes": ep["classes"], "verbs": ep["verbs"], "doc": ep["doc"], "accel": ep["accel"], "used_by": used[:12], "n_users": len(used),
                     "lines": ep["lines"], "mtime": datetime.datetime.fromtimestamp(tail.stat().st_mtime).strftime("%Y-%m-%d"), "lamp": lamp, "why": why})
    # 同類同義重疊候選:同類別內,去掉前綴(VIA_/SUP_MDL###_/CGC_MDL###_/via_)後的核心詞相同或互為子串
    def core(f):
        c = re.sub(r"^(VIA_|via_|SUP_MDL\d{3}_|CGC_MDL\d{3}_|VRN_MDL\d{3}_|Invoke-VIA-|VeritasCeleritas\.PS7\.)", "", f)
        return re.sub(r"[_\-\.]", "", c).lower()
    KEY = {"network": ("net", "proxy", "request", "aegis"), "temp": ("spill", "temp"), "accelerator": ("accel", "celeritas", "turbo", "parallel"), "nlp": ("nlp", "knowledge", "synonym"),
           "ssot_mgmt": ("number", "ssot", "registry", "dataframe", "panorama", "matrix", "govern", "standard", "book"), "verb_bridge": ("verb", "command", "ladder"), "canon_lib": ("canon", "utils", "jsonio", "tailpick"),
           "env": ("env", "mamba", "pip"), "ui": ("ui", "dashboard", "theme", "layout", "progress"), "audit": ("audit", "health", "valid", "xcheck", "smoke", "gate")}
    by_cat = defaultdict(list)
    for r in rows:
        if r["lamp"] != "GRAY":
            by_cat[r["cat"]].append(r)
    overlaps = []
    for cat, lst in by_cat.items():
        keys = KEY.get(cat, ())
        for i in range(len(lst)):
            for j in range(i + 1, len(lst)):
                a, b = core(lst[i]["family"]), core(lst[j]["family"])
                shared = [k for k in keys if k in a and k in b]
                if len(a) >= 6 and len(b) >= 6 and (a == b or a in b or b in a or shared):
                    for r in (lst[i], lst[j]):
                        if r["lamp"] == "GREEN":
                            r["lamp"] = "YELLOW"
                        r["why"].append("同類同義:%s" % (lst[j]["family"] if r is lst[i] else lst[i]["family"]))
                    overlaps.append({"cat": cat, "a": lst[i]["family"], "b": lst[j]["family"]})
    rows.sort(key=lambda r: (r["cat"], r["family"]))
    per = defaultdict(lambda: {"families": 0, "files": 0, "RED": 0, "YELLOW": 0, "GREEN": 0, "GRAY": 0})
    for r in rows:
        per[r["cat"]]["families"] += 1
        per[r["cat"]]["files"] += r["n_versions"]
        per[r["cat"]][r["lamp"]] += 1
    order = {"RED": 3, "YELLOW": 2, "GREEN": 1, "GRAY": 0}
    lamp = max((r["lamp"] for r in rows), key=lambda x: order[x]) if rows else "GRAY"
    return {"verb": "matrix", "engine": NAME, "ts": _now(), "root": str(P["root"]), "lamp": lamp, "per": dict(per), "rows": rows, "overlaps": overlaps, "secs": round(time.time() - t0, 1)}


def _html(res: dict) -> str:
    cats = sorted(res["per"])
    chips = "".join("<button onclick=\"flt('%s')\">%s · 族 %d · 紅 %d 黃 %d 綠 %d 灰 %d</button>" % (c, c, res["per"][c]["families"], res["per"][c]["RED"], res["per"][c]["YELLOW"], res["per"][c]["GREEN"], res["per"][c]["GRAY"]) for c in cats)
    trs = []
    for r in res["rows"]:
        trs.append("<tr data-cat='%s' data-lamp='%s'><td><i class='lamp %s' style='background:%s'></i></td><td>%s</td><td><b>%s</b><div class='doc'>%s</div></td><td>%s</td><td>%s</td><td title='%s'>%d</td><td>%s</td><td>%s</td><td title='%s'>%d</td><td>%s</td><td>%s</td><td class='note'>%s</td></tr>"
                   % (r["cat"], r["lamp"], r["lamp"], LAMP[r["lamp"]], r["cat"], html.escape(r["family"]), html.escape(r["doc"]), html.escape(r["folder"]), r["tail_ver"], html.escape(" ".join(r["versions"])), r["n_versions"],
                      "%d def / %d class%s" % (r["defs"], r["classes"], (" · " + " · ".join(r["verbs"])) if r["verbs"] else ""), "有" if r["accel"] else "<b style='color:#dc2626'>缺</b>", html.escape("\n".join(r["used_by"])), r["n_users"], r["ext"], r["mtime"], html.escape(";".join(r["why"]))))
    return """<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><title>VIA 輔助工具 MATRIX</title>
<style>body{font-family:"Microsoft JhengHei UI","Segoe UI",Arial,sans-serif;color:#1f2937;margin:0;padding:16px;background:#fff}h1{font-size:18px;margin:0 0 6px}.meta{color:#6b7280;font-size:12px;margin-bottom:10px}
button{margin:4px 6px 4px 0;padding:4px 10px;border:1px solid #e0e0e0;background:#f7f7f7;border-radius:6px;cursor:pointer}table{border-collapse:collapse;width:100%%;font-size:12px}th,td{border:1px solid #e0e0e0;padding:3px 6px;text-align:left;vertical-align:top}
th{background:#111827;color:#fff;position:sticky;top:0}tr:nth-child(even){background:#fafafa}.lamp{display:inline-block;width:12px;height:12px;border-radius:50%%}.lamp.RED{animation:blink 2.4s ease-in-out infinite}@keyframes blink{0%%,100%%{opacity:1}50%%{opacity:.25}}.doc{color:#6b7280;font-size:11px}.note{color:#6b7280}</style></head><body>
<h1>VIA 輔助工具 MATRIX(supportive modules + NLP)</h1><div class="meta">%s · 根 %s · 族 %d · 重疊候選 %d · %ss · 綠 = 有人用且有橋;黃 = 沒人用 / 無橋 / 同類同義重疊(整合候選);灰 = 退役夾;紅 = AST 壞</div>
<div>%s <button onclick="flt('')">全部</button> <button onclick="lampf('YELLOW')">只看黃</button> <button onclick="lampf('RED')">只看紅</button></div>
<table id="m"><thead><tr><th>燈</th><th>類別</th><th>族 / 說明</th><th>夾</th><th>尾版</th><th>版數</th><th>入口</th><th>加速器</th><th>誰在用</th><th>型</th><th>最後更新</th><th>備註</th></tr></thead><tbody>
%s</tbody></table>
<script>function flt(s){document.querySelectorAll('#m tbody tr').forEach(function(t){t.style.display=(!s||t.dataset.cat===s)?'':'none'})}function lampf(l){document.querySelectorAll('#m tbody tr').forEach(function(t){t.style.display=(t.dataset.lamp===l)?'':'none'})}</script></body></html>""" % (
        res["ts"], html.escape(res["root"]), len(res["rows"]), len(res["overlaps"]), res["secs"], chips, "\n".join(trs))


def paste_pack(res: dict) -> list:
    L = ["[計] vcgc toolkit matrix · 族 %d · 重疊候選 %d · %s · " % (len(res["rows"]), len(res["overlaps"]), res["lamp"]) + " · ".join("%s %d(紅%d 黃%d 綠%d 灰%d)" % (c, v["families"], v["RED"], v["YELLOW"], v["GREEN"], v["GRAY"]) for c, v in sorted(res["per"].items()))]
    for r in [x for x in res["rows"] if x["lamp"] == "RED"][:10]:
        L.append("  [RED] %s %s · %s" % (r["cat"], r["tail"], ";".join(r["why"])))
    L.append("[計] 同類同義重疊(整合候選,裁:留一族,其餘退役帶 replaced_by)")
    for o in res["overlaps"][:30]:
        L.append("  [YEL] %s · %s ⇄ %s" % (o["cat"], o["a"], o["b"]))
    L.append("[計] 各類尾版(族@尾版 · 版數 · 用者數)")
    for c in sorted(res["per"]):
        rs = [r for r in res["rows"] if r["cat"] == c and r["lamp"] != "GRAY"]
        L.append("  [%s] %s · " % (c, "·".join(sorted({r["lamp"][0] for r in rs}))) + " · ".join("%s@%s×%d/%d" % (r["family"], r["tail_ver"], r["n_versions"], r["n_users"]) for r in rs[:14]) + (" …+%d" % (len(rs) - 14) if len(rs) > 14 else ""))
    dormant = [r for r in res["rows"] if r["lamp"] == "YELLOW" and any(w.startswith("沒人引用") for w in r["why"])]
    L.append("[計] 沒人引用 %d 族(DORMANT 候選,前 20)" % len(dormant))
    for r in dormant[:20]:
        L.append("  [YEL] %s %s · %s" % (r["cat"], r["tail"], r["why"][0]))
    L.append("NEXT: 重疊對貼給 AI 裁留誰;DORMANT 候選兩輪沒人用就標 DORMANT(不刪);缺橋的出薄尾補 [VIA:ACCEL-BRIDGE];MATRIX 在 VIA_Reports\\review\\vcgc_toolkit\\TOOLKIT_MATRIX_latest.html")
    return L[:300]


def write_outputs(res: dict, P: dict | None = None) -> dict:
    P = P or _paths()
    P["out"].mkdir(parents=True, exist_ok=True)
    P["cards"].mkdir(parents=True, exist_ok=True)
    (P["out"] / "TOOLKIT_MATRIX_latest.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    ht = P["out"] / "TOOLKIT_MATRIX_latest.html"
    ht.write_text(_html(res), encoding="utf-8")
    pack = paste_pack(res)
    day = datetime.datetime.now().strftime("%Y%m%d")
    md = P["cards"] / ("VCGC_ToolkitCard_%s.md" % day)
    L = ["# VCGC 輔助工具整合管理卡(%s)" % day, "", "> 唯讀。每族一列:尾版 · 版數 · 入口 · 誰在用 · 燈。", "", "## 貼回包", "```"] + pack + ["```", "", "| 類別 | 族 | 夾 | 尾版 | 版數 | 入口 | 橋 | 用者 | 燈 | 備註 |", "|---|---|---|---|---|---|---|---|---|---|"]
    for r in res["rows"]:
        L.append("| %s | %s | %s | %s | %d | %d def/%d cls | %s | %d | %s | %s |" % (r["cat"], r["family"], r["folder"], r["tail_ver"], r["n_versions"], r["defs"], r["classes"], "有" if r["accel"] else "缺", r["n_users"], r["lamp"], ";".join(r["why"]).replace("|", "¦")))
    md.write_text("\n".join(L) + "\n", encoding="utf-8")
    return {"html": str(ht), "md": str(md), "pack": pack}


def main(argv=None) -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VCGC] 拒絕。只能經 via-vcgc。")
        return 2
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a[:2]:
        return selftest()
    if a[:1] != ["matrix"]:
        print("[拒跑] matrix [--json] | --selftest")
        return 2
    res = matrix()
    out = write_outputs(res)
    if "--json" in a:
        print(json.dumps(res, ensure_ascii=False))
    for ln in out["pack"]:
        print(ln)
    print("  [MATRIX] %s" % out["html"])
    print("  [卡] %s" % out["md"])
    if os.environ.get("VIA_NO_OPEN") != "1" and os.name == "nt":
        try:
            os.startfile(out["html"])  # type: ignore[attr-defined]
        except OSError:
            pass
    return 1 if res["lamp"] == "RED" else 0


def _w(p: Path, s: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8")


def selftest() -> int:
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)

    td = Path(tempfile.mkdtemp(prefix="cgctool-"))
    os.environ["VIA_ROOT"] = str(td)
    os.environ["VIA_NO_OPEN"] = "1"
    P = _paths()
    chk("① 沙盒", all(str(v).startswith(str(td)) for v in P.values()))
    A = "# [VIA:ACCEL-BRIDGE:v0100]\n" + "\n".join("# p%d" % i for i in range(40)) + "\n"
    _w(P["sup"] / "VIA_SuperAccel_Module.py", A + "def accel():\n    pass\n")
    _w(P["sup"] / "SUP_MDL867_TempSpill_v0100.py", A + '"""x\n動詞: activate · connect\n"""\ndef activate(n):\n    pass\n')
    _w(P["sup"] / "VIA_TempSpill_v0100.py", A + "class TempSpill:\n    pass\n")                           # 同類同義 → 黃
    _w(P["sup"] / "network" / "SUP_MDL740_NetUnified_v0103.py", A + "def get(u):\n    pass\n")
    _w(P["sup"] / "network" / "SUP_MDL740_NetUnified_v0104.py", A + "def get(u):\n    pass\n\ndef post(u):\n    pass\n")
    _w(P["sup"] / "VIA_NetSupport.py", A + "def fetch():\n    pass\n")                                    # 同類同義 Net → 黃
    _w(P["sup"] / "VIA_Old_Thing.py", "\n".join("# p%d" % i for i in range(45)) + "\ndef z():\n    pass\n")  # 無橋且沒人用 → 黃
    _w(P["sup"] / "_superseded" / "VIA_Dead_v0100.py", "x=1\n")                                          # 灰
    _w(P["sup"] / "registry" / "CGC_MDL237_NumberingSystem_v0100.py", A + "def main():\n    pass\n")
    _w(P["sup"] / "registry" / "CGC_MDL249_DataFrameLock_v0100.py", A + "def check(:\n")                 # AST 壞 → 紅
    _w(P["sup"] / "registry" / "helper_script.py", "print(1)\n")                                          # registry 非引擎不算
    _w(P["sup"] / "VIA_PS_Accel_Module.ps1", "# [VIA:PS-ACCEL]\n" + "\n".join("# p%d" % i for i in range(40)) + "\nfunction Invoke-VIAGuarded { }\n")
    _w(P["nlp"] / "NLP_SystemManager_v0100.py", A + "def main():\n    pass\n")
    _w(P["vrn"] / "VRN_ENG001_A_v0100.py", A + "import VIA_SuperAccel_Module\nfrom SUP_MDL740_NetUnified_v0104 import get\nimport NLP_SystemManager_v0100\n")
    res = matrix(P)
    R = {r["family"]: r for r in res["rows"]}
    chk("② 族數與尾版:NetUnified 尾版 v0104 版數 2 · registry helper 不計 · 退役夾灰", R["SUP_MDL740_NetUnified"]["tail_ver"] == "v0104" and R["SUP_MDL740_NetUnified"]["n_versions"] == 2 and "helper_script" not in R and R["VIA_Dead"]["lamp"] == "GRAY")
    chk("③ 類別:SuperAccel=accelerator · NetUnified=network(夾)· TempSpill=temp · NumberingSystem=ssot_mgmt · NLP=nlp · PS_Accel=accelerator", R["VIA_SuperAccel_Module"]["cat"] == "accelerator" and R["SUP_MDL740_NetUnified"]["cat"] == "network" and R["SUP_MDL867_TempSpill"]["cat"] == "temp" and R["CGC_MDL237_NumberingSystem"]["cat"] == "ssot_mgmt" and R["NLP_SystemManager"]["cat"] == "nlp" and R["VIA_PS_Accel_Module"]["cat"] == "accelerator")
    chk("④ 誰在用:SuperAccel/NetUnified/NLP 各 1 用者(VRN_ENG001)· Old_Thing 0", R["VIA_SuperAccel_Module"]["n_users"] >= 1 and R["SUP_MDL740_NetUnified"]["n_users"] >= 1 and R["NLP_SystemManager"]["n_users"] >= 1 and R["VIA_Old_Thing"]["n_users"] == 0)
    chk("⑤ 燈:Old_Thing 黃(沒人用+無橋)· DataFrameLock 紅(AST)· TempSpill×2 同類同義黃 · NetUnified⇄NetSupport 重疊", R["VIA_Old_Thing"]["lamp"] == "YELLOW" and R["CGC_MDL249_DataFrameLock"]["lamp"] == "RED" and any(w.startswith("同類同義") for w in R["VIA_TempSpill"]["why"]) and any(o["cat"] == "network" for o in res["overlaps"]))
    chk("⑥ 入口:TempSpill(867) 動詞 activate/connect · PS 函式數 1", R["SUP_MDL867_TempSpill"]["verbs"][:2] == ["activate", "connect"] and R["VIA_PS_Accel_Module"]["defs"] == 1)
    out = write_outputs(res, P)
    htm = Path(out["html"]).read_text(encoding="utf-8")
    chk("⑦ 輸出:HTML 四色 token + 紅燈慢閃 · md 卡 · 貼回包 ≤300 NEXT:", all(c in htm for c in LAMP.values()) and "@keyframes blink" in htm and Path(out["md"]).exists() and len(out["pack"]) <= 300 and out["pack"][-1].startswith("NEXT:"))
    chk("⑧ 唯讀:supportive modules 檔數不變", len(list(P["sup"].rglob("*.py"))) == 11)
    body = ME.read_text(encoding="utf-8")
    chk("⑨ 帶加速器橋 · VIA_FROM_VCGC 閘", "[VIA:ACCEL-BRIDGE:v0100]" in body and "VIA_FROM_VCGC" in body)
    for k in ("VIA_ROOT", "VIA_NO_OPEN"):
        os.environ.pop(k, None)
    shutil.rmtree(td, ignore_errors=True)
    print("[計] %s 自測 %d/%d · %s" % (NAME, p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
