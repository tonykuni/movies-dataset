#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC EnvToolAudit v0101 — 環境工具全景檢查(v0101:requirements 冊的 URL/路徑/旗標列不當套件名 · fill 逐套件裝,一個壞名不擋整批 · import 掃描丟垃圾名與單檔孤例;其餘同 v0100) + 補缺 + PDF 工具獨立隔離環境(操作員令 2026-10-06:透過 VCGC 環境工具全景式檢查母系統/子系統所有工具都安裝,有缺漏趕快補上;tabula / camelot 獨立隔離安裝)。
  audit            找所有 python 環境(micromamba/conda envs · venv · VIA 樹內 python · 目前直譯器)→ 每環境裝了什麼 × 各子系統要什麼(requirements 冊 ∪ 尾版 .py 的第三方 import)→ 矩陣;外部工具 java / tesseract / ghostscript / git / gh / pwsh / node
  fill --apply     只補「requirements 冊有列」而該環境缺的套件(pip install,逐環境);import 到但冊沒列的只列黃不裝(誠實,不亂塞)
  pdftools --apply 建獨立環境 <VIA>/envs/via_pdf_tools(venv)裝 pdfplumber camelot-py pypdfium2 opencv-python-headless tabula-py;寫 registry/VIA_EnvTools_Registry_v0100.json(鍵 pdf_tools.python)供 VRN 橋使用;已在=升級檢查,不重建
  --selftest       temp 沙盒(不出網)
只寫:registry/VIA_EnvTools_Registry_v0100.json · docs/handoff/ai/VCGC_EnvToolCard_<日>.md · VIA_Reports/review/vcgc_env/ENV_MATRIX_latest.{json,html};pip 只在 --apply 時動該環境。沙盒鍵:VIA_ROOT · VIA_ENV_NO_PIP=1
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

import datetime
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from collections import defaultdict
from pathlib import Path

ME = Path(__file__).resolve()
NAME = ME.stem
TAG = "v0101"
LAMP = {"GREEN": "#16a34a", "YELLOW": "#f59e0b", "RED": "#dc2626", "GRAY": "#9ca3af"}
EXCL = {"references", "intake", "_superseded", "VIA_RetiredEngines", "_quarantine_pip_vendor", "__pycache__", ".venv", "venv", "node_modules", ".git", "_quarantine", "envs", "_vdf_envs", "VIA_NumberBooks", "_df", "docs", "VIA_Reports"}
LOCAL_PREFIX = re.compile(r"^(VIA|via|VRN|vrn|VDF|vdf|CGC|SUP|VAP|GIF|VRM|NLP|_sa_)")
ALIAS = {"cv2": "opencv-python-headless", "PIL": "pillow", "sklearn": "scikit-learn", "yaml": "pyyaml", "bs4": "beautifulsoup4", "fitz": "pymupdf", "dateutil": "python-dateutil", "dotenv": "python-dotenv",
         "attr": "attrs", "Crypto": "pycryptodome", "talib": "ta-lib", "win32com": "pywin32", "win32api": "pywin32", "pythoncom": "pywin32", "camelot": "camelot-py", "tabula": "tabula-py", "pypdfium2": "pypdfium2", "lxml": "lxml", "docx": "python-docx", "pptx": "python-pptx"}
PDF_TOOLS = ["pdfplumber", "camelot-py", "pypdfium2", "opencv-python-headless", "tabula-py", "pandas", "pyarrow"]
JUNK_IMPORTS = {"android", "ascii", "distutils", "dummy_threading", "manylinux", "pypy", "typeshed", "accelerator", "batch_pdf_validator", "final_accelerator_system", "email_case_tracker", "devils_advocate", "flow_bridge", "flow_calibrate", "flow_core", "flow_factors", "flow_grid", "extract_msg", "docopt", "https", "http", "ftp", "site", "setuptools", "pip", "wheel"}
EXT_TOOLS = ["java", "tesseract", "gs", "gswin64c", "git", "gh", "pwsh", "node", "micromamba", "conda"]
TOOLS_REG = "VIA_EnvTools_Registry_v0100.json"


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
    return {"root": r, "registry": r / "supportive modules" / "registry", "vrn": r / "functional modules" / "VRN", "vdf": r / "functional modules" / "VDF", "sup": r / "supportive modules",
            "envs": r / "envs", "cards": r / "docs" / "handoff" / "ai", "out": r / "VIA_Reports" / "review" / "vcgc_env"}


def _norm(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name.strip().lower())


def _read(p: Path, limit: int = 300_000) -> str:
    raw = p.read_bytes()[:limit]
    for enc in ("utf-8-sig", "utf-16", "cp950", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return ""


# ───────── 環境探索 ─────────
def _py_exe(d: Path):
    for c in (d / "python.exe", d / "Scripts" / "python.exe", d / "bin" / "python", d / "bin" / "python3"):
        if c.exists():
            return c
    return None


def discover_envs(P: dict) -> list:
    envs = []
    seen = set()

    def add(name, exe, kind):
        key = str(exe).lower()        # 不 resolve:venv 的 python 是 symlink/launcher,resolve 會與母直譯器撞成同一個
        if key in seen:
            return
        seen.add(key)
        envs.append({"name": name, "python": str(exe), "kind": kind})
    add("current(%s)" % Path(sys.prefix).name, sys.executable, "current")
    home = Path(os.environ.get("USERPROFILE") or os.environ.get("HOME") or "~").expanduser()
    for base in (home / "micromamba" / "envs", home / "miniconda3" / "envs", home / "anaconda3" / "envs", home / "mambaforge" / "envs", home / ".conda" / "envs", home / ".venvs", home / "venvs"):
        if base.is_dir():
            for d in sorted(base.iterdir()):
                exe = _py_exe(d) if d.is_dir() else None
                if exe:
                    add(d.name, exe, "conda" if "conda" in str(base) or "mamba" in str(base) else "venv")
    for extra in os.environ.get("VIA_EXTRA_ENVS", "").split(";"):
        if extra.strip() and _py_exe(Path(extra.strip())):
            add(Path(extra.strip()).name, _py_exe(Path(extra.strip())), "extra")
    for base in (P["envs"], P["vdf"] / "_vdf_envs", P["root"]):
        if not base.is_dir():
            continue
        depth = 1 if base != P["root"] else 2
        for d in base.iterdir():
            if d.is_dir() and not (set(d.parts) & {"references", "intake"}):
                exe = _py_exe(d)
                if exe:
                    add(d.name, exe, "via-env")
                elif depth > 1:
                    for dd in d.iterdir():
                        if dd.is_dir():
                            e2 = _py_exe(dd)
                            if e2:
                                add(dd.name, e2, "via-env")
    return envs


def _installed(exe: str, timeout: int = 60) -> dict:
    code = "import json,sys\ntry:\n    import importlib.metadata as m\n    d={}\n    for x in m.distributions():\n        try:\n            d[x.metadata['Name']]=x.version\n        except Exception:\n            pass\n    print(json.dumps({'py':sys.version.split()[0],'pk':d}))\nexcept Exception as e:\n    print(json.dumps({'err':str(e)}))\n"
    try:
        out = subprocess.run([exe, "-c", code], capture_output=True, text=True, timeout=timeout)
        d = json.loads(out.stdout.strip().splitlines()[-1]) if out.stdout.strip() else {"err": out.stderr[-200:]}
    except (subprocess.SubprocessError, ValueError, OSError) as exc:
        d = {"err": "%s" % type(exc).__name__}
    if "pk" in d:
        d["pk"] = {_norm(k): v for k, v in d["pk"].items()}
    return d


# ───────── 需求集 ─────────
def _req_names(P: dict) -> dict:
    """requirements 冊:{套件: [冊名]}"""
    req = defaultdict(set)
    globs = list(P["root"].glob("requirements*.txt")) + list(P["registry"].glob("VIA_Env_Requirements*.txt")) + list((P["root"].parent).glob("requirements*.txt"))
    for p in globs:
        if not p.is_file():
            continue
        for ln in _read(p).splitlines():
            ln = ln.split("#")[0].strip()
            if not ln or ln.startswith(("-", "git+", "file:")) or "://" in ln or "/" in ln or "\\" in ln or ln.endswith((".txt", ".whl")):
                continue   # URL / 路徑 / 旗標列不是套件名(2026-10-06 實跑:'https' 被當套件 → 整批 pip FAIL)
            m = re.match(r"([A-Za-z0-9][A-Za-z0-9_.\-]*)", ln)
            if m and len(m.group(1)) >= 2:
                req[_norm(m.group(1))].add(p.name)
    return dict(req)


def _imports_by_sub(P: dict) -> dict:
    std = set(getattr(sys, "stdlib_module_names", ()))
    best = {}
    for sub, d in (("VRN", P["vrn"]), ("VDF", P["vdf"]), ("VCGC", P["sup"])):
        if not d.is_dir():
            continue
        for p in d.rglob("*.py"):
            if set(p.relative_to(P["root"]).parts[:-1]) & EXCL:
                continue
            fam = re.sub(r"_v\d{2,4}[A-Za-z0-9]*$", "", p.stem)
            k = (sub, p.parent, fam)
            v = int((re.search(r"_v(\d{4})", p.name) or [0, "-1"])[1]) if re.search(r"_v(\d{4})", p.name) else -1
            if k not in best or v > best[k][0]:
                best[k] = (v, p)
    out = defaultdict(lambda: defaultdict(set))
    for (sub, _, _), (_, p) in best.items():
        txt = _read(p).split("\ndef selftest(")[0]
        for m in re.finditer(r"^\s*(?:from\s+([A-Za-z_][\w]*)|import\s+([A-Za-z_][\w]*))", txt, re.M):
            mod = m.group(1) or m.group(2)
            if mod in std or LOCAL_PREFIX.match(mod) or mod in JUNK_IMPORTS or mod.startswith("_"):
                continue
            out[sub][_norm(ALIAS.get(mod, mod))].add(p.name)
    # 單檔孤例不算需求(多半是實驗/舊檔);≥2 檔 import 才列
    return {s: {k: sorted(v)[:5] for k, v in d.items() if len(v) >= 2} for s, d in out.items()}


def _sub_of_env(name: str) -> str:
    n = name.lower()
    if "vrn" in n:
        return "VRN"
    if "vdf" in n:
        return "VDF"
    if "pdf" in n:
        return "PDFTOOLS"
    if any(k in n for k in ("cgc", "core", "via", "base", "current")):
        return "VCGC"
    return "OTHER"


def audit(P: dict | None = None) -> dict:
    P = P or _paths()
    t0 = time.time()
    envs = discover_envs(P)
    req = _req_names(P)
    imps = _imports_by_sub(P)
    rows = []
    for e in envs:
        inst = _installed(e["python"])
        e["sub"] = _sub_of_env(e["name"])
        e["py"] = inst.get("py")
        e["err"] = inst.get("err")
        pk = inst.get("pk", {})
        e["n_installed"] = len(pk)
        need = set(req) if e["sub"] in ("VRN", "VDF", "VCGC") else set()
        if e["sub"] == "PDFTOOLS":
            need = {_norm(x) for x in PDF_TOOLS}
        want_imports = set(imps.get(e["sub"], {})) if e["sub"] in imps else set()
        missing_req = sorted(n for n in need if n not in pk)
        missing_imp = sorted(n for n in want_imports if n not in pk and n not in need)
        e["missing_req"] = missing_req
        e["missing_import_only"] = missing_imp[:30]
        e["has"] = {k: pk.get(_norm(k)) for k in ("pandas", "pyarrow", "duckdb", "pdfplumber", "camelot-py", "tabula-py", "pymupdf", "polars", "requests", "psutil")}
        e["lamp"] = "RED" if e["err"] else ("YELLOW" if (missing_req or missing_imp) else "GREEN")
        rows.append(e)
    tools = {}
    for t in EXT_TOOLS:
        p = shutil.which(t)
        ver = None
        if p:
            try:
                r = subprocess.run([p, "--version"] if t not in ("java", "gs", "gswin64c") else [p, "-version" if t == "java" else "--version"], capture_output=True, text=True, timeout=20)
                ver = ((r.stdout or r.stderr).strip().splitlines() or [""])[0][:60]
            except (subprocess.SubprocessError, OSError):
                ver = "?"
        tools[t] = {"path": p, "version": ver}
    reg = P["registry"] / TOOLS_REG
    tools_reg = json.loads(_read(reg)) if reg.exists() else {}
    pdf_env = (tools_reg.get("pdf_tools") or {}).get("python")
    pdf_ok = bool(pdf_env and Path(pdf_env).exists())
    lamp = "RED" if any(r["lamp"] == "RED" for r in rows) else ("YELLOW" if (any(r["lamp"] == "YELLOW" for r in rows) or not pdf_ok or not tools["java"]["path"]) else "GREEN")
    return {"verb": "audit", "engine": NAME, "ts": _now(), "root": str(P["root"]), "envs": rows, "requirements": sorted(req), "n_req_books": len({b for v in req.values() for b in v}), "imports_by_sub": {s: sorted(d) for s, d in imps.items()},
            "tools": tools, "pdf_tools_env": pdf_env, "pdf_tools_ok": pdf_ok, "lamp": lamp, "secs": round(time.time() - t0, 1)}


# ───────── 補缺 / 獨立 PDF 環境 ─────────
def _pip(exe: str, pkgs: list, timeout: int = 900) -> dict:
    if os.environ.get("VIA_ENV_NO_PIP") == "1":
        return {"rc": 0, "skipped": True, "out": "VIA_ENV_NO_PIP=1"}
    try:
        r = subprocess.run([exe, "-m", "pip", "install", "--disable-pip-version-check", "-q"] + pkgs, capture_output=True, text=True, timeout=timeout)
        return {"rc": r.returncode, "out": (r.stdout + r.stderr)[-600:]}
    except (subprocess.SubprocessError, OSError) as exc:
        return {"rc": 1, "out": "%s" % type(exc).__name__}


def fill(res: dict, P: dict | None = None, apply: bool = False) -> dict:
    P = P or _paths()
    out = {"verb": "fill", "apply": apply, "rows": []}
    for e in res["envs"]:
        if e.get("err") or not e["missing_req"] or e["sub"] not in ("VRN", "VDF", "VCGC"):
            continue
        rec = {"env": e["name"], "python": e["python"], "install": e["missing_req"], "status": "PLAN"}
        if apply:
            ok, bad, skipped = [], [], False
            for pkg in e["missing_req"]:
                r = _pip(e["python"], [pkg], timeout=600)
                if r.get("skipped"):
                    skipped = True
                    break
                (ok if r["rc"] == 0 else bad).append(pkg)
            rec["ok"], rec["bad"] = ok, bad
            rec["status"] = "SKIPPED" if skipped else ("OK" if not bad else ("PARTIAL" if ok else "FAIL"))
        out["rows"].append(rec)
    out["lamp"] = "RED" if any(r["status"] == "FAIL" for r in out["rows"]) else ("GREEN" if apply else ("YELLOW" if out["rows"] else "GREEN"))
    return out


def pdftools(P: dict | None = None, apply: bool = False) -> dict:
    P = P or _paths()
    env_dir = P["envs"] / "via_pdf_tools"
    exe = _py_exe(env_dir)
    out = {"verb": "pdftools", "apply": apply, "env": str(env_dir), "created": False, "installed": [], "status": "PLAN", "_notes": []}
    if not exe and apply:
        try:
            P["envs"].mkdir(parents=True, exist_ok=True)
            subprocess.run([sys.executable, "-m", "venv", str(env_dir)], check=True, capture_output=True, timeout=300)
            exe = _py_exe(env_dir)
            out["created"] = True
        except (subprocess.SubprocessError, OSError) as exc:
            out["status"] = "FAIL"
            out["_notes"].append("venv 建立失敗 %s" % type(exc).__name__)
            out["lamp"] = "RED"
            return out
    if exe:
        inst = _installed(str(exe)).get("pk", {})
        need = [p for p in PDF_TOOLS if _norm(p) not in inst]
        out["missing"] = need
        if apply and need:
            r = _pip(str(exe), need)
            out["pip_rc"] = r["rc"]
            out["pip_tail"] = r["out"][-300:]
            out["status"] = "SKIPPED" if r.get("skipped") else ("OK" if r["rc"] == 0 else "FAIL")
            inst = _installed(str(exe)).get("pk", {})
        elif apply:
            out["status"] = "OK"
        out["installed"] = {p: inst.get(_norm(p)) for p in PDF_TOOLS}
        out["python"] = str(exe)
        if apply and out["status"] in ("OK", "SKIPPED"):
            reg = P["registry"] / TOOLS_REG
            d = json.loads(_read(reg)) if reg.exists() else {"schema": "VIA.EnvTools.Registry.v1", "version": "v0100", "rule": "獨立隔離工具環境;子系統經橋(subprocess)呼叫,不污染自己的 venv;只增不減", "created_at": _now()}
            d["pdf_tools"] = {"python": str(exe), "packages": out["installed"], "java": shutil.which("java"), "updated_at": _now(), "engine": NAME}
            P["registry"].mkdir(parents=True, exist_ok=True)
            reg.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
            out["registry"] = str(reg)
    else:
        out["_notes"].append("環境不在(dry-run 未建)")
    out["lamp"] = "RED" if out["status"] == "FAIL" else ("GREEN" if out["status"] in ("OK", "SKIPPED") else "YELLOW")
    return out


# ───────── 輸出 ─────────
def paste_pack(res: dict, extra: list) -> list:
    L = ["[計] vcgc env audit · 環境 %d · requirements 冊 %d(%d 套件)· 外部工具 java=%s tesseract=%s gs=%s git=%s gh=%s · PDF 隔離環境 %s · %ss · %s"
         % (len(res["envs"]), res["n_req_books"], len(res["requirements"]), bool(res["tools"]["java"]["path"]), bool(res["tools"]["tesseract"]["path"]), bool(res["tools"]["gs"]["path"] or res["tools"]["gswin64c"]["path"]), bool(res["tools"]["git"]["path"]), bool(res["tools"]["gh"]["path"]),
            ("有:" + res["pdf_tools_env"]) if res["pdf_tools_ok"] else "無(待 pdftools --apply)", res["secs"], res["lamp"])]
    for e in res["envs"]:
        tag = {"RED": "RED", "YELLOW": "YEL", "GREEN": "OK"}[e["lamp"]]
        has = " ".join("%s=%s" % (k, v or "-") for k, v in e["has"].items() if k in ("pandas", "pdfplumber", "camelot-py", "tabula-py", "pymupdf", "duckdb"))
        L.append("  [%s] %s(%s)· py %s · 裝 %d · %s · 缺(冊列)%d · 缺(只 import)%d%s" % (tag, e["name"], e["sub"], e.get("py") or "?", e["n_installed"], has, len(e["missing_req"]), len(e["missing_import_only"]), (" · " + e["err"]) if e.get("err") else ""))
        if e["missing_req"]:
            L.append("      缺冊列:" + ", ".join(e["missing_req"][:25]))
        if e["missing_import_only"]:
            L.append("      只 import 未列冊(不自動裝,黃):" + ", ".join(e["missing_import_only"][:20]))
    L += extra
    L.append("NEXT: 冊列的缺 → fill --apply 已補(看上面);只 import 未列冊的 → 貼給 AI 裁要不要進 VIA_Env_Requirements 新版;PDF 工具走 envs\\via_pdf_tools(VRN v0131 橋)")
    return L[:300]


def _html(res: dict) -> str:
    cols = ["pandas", "pyarrow", "duckdb", "pdfplumber", "camelot-py", "tabula-py", "pymupdf", "polars", "requests", "psutil"]
    trs = []
    for e in res["envs"]:
        cells = "".join("<td style='background:%s;color:#fff'>%s</td>" % (LAMP["GREEN"] if e["has"].get(c) else LAMP["GRAY"], html.escape(str(e["has"].get(c) or "—"))) for c in cols)
        trs.append("<tr><td><i class='lamp %s' style='background:%s'></i></td><td>%s</td><td>%s</td><td>%s</td><td>%d</td>%s<td class='note'>%s</td></tr>" % (e["lamp"], LAMP[e["lamp"]], html.escape(e["name"]), e["sub"], e.get("py") or "?", e["n_installed"], cells, html.escape(", ".join(e["missing_req"][:12]) + ((" | import:" + ", ".join(e["missing_import_only"][:8])) if e["missing_import_only"] else ""))))
    tools = "".join("<span class='chip' style='background:%s'>%s %s</span>" % (LAMP["GREEN"] if v["path"] else LAMP["GRAY"], t, html.escape((v["version"] or "")[:30])) for t, v in res["tools"].items())
    return """<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><title>VIA 環境工具 MATRIX</title><style>body{font-family:"Microsoft JhengHei UI","Segoe UI",Arial;color:#1f2937;margin:0;padding:16px}h1{font-size:18px;margin:0 0 6px}.meta{color:#6b7280;font-size:12px}.chip{display:inline-block;color:#fff;padding:2px 8px;border-radius:12px;margin:2px;font-size:12px}table{border-collapse:collapse;width:100%%;font-size:12px;margin-top:10px}th,td{border:1px solid #e0e0e0;padding:3px 6px;text-align:left}th{background:#111827;color:#fff}.lamp{display:inline-block;width:12px;height:12px;border-radius:50%%}.lamp.RED{animation:blink 2.4s ease-in-out infinite}@keyframes blink{0%%,100%%{opacity:1}50%%{opacity:.25}}.note{color:#6b7280}</style></head><body>
<h1>VIA 環境工具 MATRIX(母系統 + 子系統)</h1><div class="meta">%s · PDF 隔離環境:%s · <span class="chip" style="background:#16a34a">綠 冊列齊</span><span class="chip" style="background:#f59e0b">黃 有缺</span><span class="chip" style="background:#dc2626">紅 環境壞</span><span class="chip" style="background:#9ca3af">灰 未裝</span></div><div>%s</div>
<table><thead><tr><th>燈</th><th>環境</th><th>子系統</th><th>python</th><th>裝</th>%s<th>缺</th></tr></thead><tbody>%s</tbody></table></body></html>""" % (
        res["ts"], html.escape(res["pdf_tools_env"] or "無"), tools, "".join("<th>%s</th>" % c for c in cols), "\n".join(trs))


def write_outputs(res: dict, pack: list, P: dict | None = None) -> dict:
    P = P or _paths()
    P["out"].mkdir(parents=True, exist_ok=True)
    P["cards"].mkdir(parents=True, exist_ok=True)
    (P["out"] / "ENV_MATRIX_latest.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    ht = P["out"] / "ENV_MATRIX_latest.html"
    ht.write_text(_html(res), encoding="utf-8")
    md = P["cards"] / ("VCGC_EnvToolCard_%s.md" % datetime.datetime.now().strftime("%Y%m%d"))
    md.write_text("\n".join(["# VCGC 環境工具全景卡", "", "```"] + pack + ["```", ""]), encoding="utf-8")
    return {"html": str(ht), "md": str(md)}


def main(argv=None) -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VCGC] 拒絕。只能經 via-vcgc。")
        return 2
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a[:2]:
        return selftest()
    apply = "--apply" in a
    verb = a[0] if a else ""
    if verb not in ("audit", "fill", "pdftools"):
        print("[拒跑] audit | fill --apply | pdftools --apply | --selftest")
        return 2
    extra = []
    if verb == "pdftools":
        r = pdftools(apply=apply)
        extra.append("[計] pdftools%s · %s · 建 %s · 裝 %s · %s%s" % (" --apply" if apply else "(dry-run)", r["env"], r["created"], r.get("installed") or r.get("missing"), r["status"], (" · " + ";".join(r["_notes"])) if r["_notes"] else ""))
        if r.get("pip_tail") and r["status"] == "FAIL":
            extra.append("  [RED] pip:" + r["pip_tail"].replace("\n", " ¦ ")[-200:])
    res = audit()
    if verb == "fill":
        fr = fill(res, apply=apply)
        for row in fr["rows"]:
            extra.append("  [%s] fill %s · 裝 %s · %s%s" % ("RED" if row["status"] == "FAIL" else ("OK" if row["status"] == "OK" else "YEL"), row["env"], ", ".join(row["install"][:15]), row["status"], (" · 裝不上:" + ", ".join(row["bad"])) if row.get("bad") else ""))
        if apply:
            res = audit()
    pack = paste_pack(res, extra)
    out = write_outputs(res, pack)
    for ln in pack:
        print(ln)
    print("  [MATRIX] %s" % out["html"])
    print("  [卡] %s" % out["md"])
    return 1 if res["lamp"] == "RED" else 0


def _w(p: Path, s) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s if isinstance(s, str) else json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8")


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

    td = Path(tempfile.mkdtemp(prefix="cgcenv-"))
    os.environ["VIA_ROOT"] = str(td)
    os.environ["VIA_ENV_NO_PIP"] = "1"
    P = _paths()
    chk("① 沙盒 · 不出網(VIA_ENV_NO_PIP=1)", all(str(v).startswith(str(td)) for v in P.values()))
    _w(P["registry"] / "VIA_Env_Requirements_v0100.txt", "pandas\nnosuchpkg-zz>=1\nhttps://example.com/x.whl\n-e .\n# c\n")
    _w(P["vrn"] / "VRN_ENG001_A_v0100.py", "import pandas\nimport pdfplumber\nimport nosuchmod_qq\nimport android\n")
    _w(P["vrn"] / "VRN_ENG002_B_v0100.py", "import nosuchmod_qq\n")
    res = audit(P)
    cur = [e for e in res["envs"] if e["kind"] == "current"][0]
    chk("② 探到目前直譯器 · 裝了 pandas · 缺冊列 nosuchpkg-zz · URL/-e 列不當套件", cur["n_installed"] > 0 and cur["has"].get("pandas") and "nosuchpkg-zz" in cur["missing_req"] and "https" not in res["requirements"] and "e" not in res["requirements"])
    chk("③ 只 import 未列冊 → 黃不裝(nosuchmod-qq ≥2 檔才列;android 垃圾名不列;pdfplumber 單檔孤例不列)", "nosuchmod-qq" in res["imports_by_sub"].get("VRN", []) and "android" not in res["imports_by_sub"].get("VRN", []) and "pdfplumber" not in res["imports_by_sub"].get("VRN", []))
    chk("④ 外部工具探針 python 可跑 · git 有路徑或 None(誠實)", "git" in res["tools"] and (res["tools"]["git"]["path"] is None or Path(res["tools"]["git"]["path"]).exists()))
    fr = fill(res, P, apply=True)
    chk("⑤ fill --apply 在 NO_PIP 下全 SKIPPED(不出網)", fr["rows"] and all(r["status"] == "SKIPPED" for r in fr["rows"]))
    pt = pdftools(P, apply=True)
    reg = P["registry"] / TOOLS_REG
    chk("⑥ pdftools --apply:建 venv envs/via_pdf_tools · pip 在 NO_PIP 下 SKIPPED · 寫 VIA_EnvTools_Registry(pdf_tools.python)", pt["created"] and pt["status"] == "SKIPPED" and reg.exists() and json.loads(reg.read_text(encoding="utf-8"))["pdf_tools"]["python"])
    res2 = audit(P)
    chk("⑦ 再 audit:看得到 PDF 隔離環境", res2["pdf_tools_ok"] and any(e["sub"] == "PDFTOOLS" for e in res2["envs"]))
    pack = paste_pack(res2, [])
    out = write_outputs(res2, pack, P)
    chk("⑧ 輸出:HTML 四色 · 卡 · 貼回包 ≤300 NEXT:", all(c in Path(out["html"]).read_text(encoding="utf-8") for c in LAMP.values()) and Path(out["md"]).exists() and pack[-1].startswith("NEXT:") and len(pack) <= 300)
    body = ME.read_text(encoding="utf-8")
    chk("⑨ 帶加速器橋 · VIA_FROM_VCGC 閘", "[VIA:ACCEL-BRIDGE:v0100]" in body and "VIA_FROM_VCGC" in body)
    for k in ("VIA_ROOT", "VIA_ENV_NO_PIP"):
        os.environ.pop(k, None)
    shutil.rmtree(td, ignore_errors=True)
    print("[計] %s 自測 %d/%d · %s" % (NAME, p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
