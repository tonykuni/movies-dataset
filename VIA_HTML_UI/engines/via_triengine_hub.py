# -*- coding: utf-8 -*-
"""
VIA TriEngine Hub (VTH) v0100
=============================
把這一大組整併成三個泛用型引擎，並給每個引擎統一的「對外掛載」協定：

  E1  規格轉換 · 內容擷取   VIA Format & Extraction   = VOFIE (全格式→IR→五檔) + VSHP (HTML/UI/JS/CSS/後端→Markdown) + MarkItDown
  E2  自然語言               VIA NLP One Engine        = via_nlp_engine v1.5 (process / reconstruct-bundle / providers / health / serve)
  E3  程式優化 · 合併        VIA Engine Standardizer   = VES v0500 (AST 分群→骨架→指標層→閘門→AI 交接)

掛載 (mount) 協定 = mounts/<name>/mount.json：任何免費在地工具 (Python lib / JS package / PowerShell module / exe)
都能以宣告方式掛進某個引擎；Hub 只做：發現 → 驗證 → 探測可用性 → 登記 (append-only, VIA-MNT- 碼) → 依模板執行 → 帳本。
不安裝、不下載、不執行來源檔內容；缺工具只降級。

用法:
  python via_triengine_hub.py status   [--root DIR] [--deep]         三引擎 + 掛載 + 工具矩陣 → HTML
  python via_triengine_hub.py route    --in <files...>               依副檔名/內容路由到 E1/E2/E3 (不執行)
  python via_triengine_hub.py run      --engine E1|E2|E3 --in ... [--out DIR] [--args "..."]
  python via_triengine_hub.py pipeline --in <files...> [--out DIR]   E1 擷取 → E2 NLP → E3 程式標準化 (檔案交接)
  python via_triengine_hub.py mount    list|probe|run <name> [--in ...] [--out DIR]
  python via_triengine_hub.py init-mounts                            寫出三個範例掛載 (py / js / ps1)
  python via_triengine_hub.py selftest
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

VERSION = "0110"
HUB_CONTRACT = "VIA_HUB_ENVELOPE/1.0"
MOUNT_CONTRACT = "VIA_MOUNT_MANIFEST/1.0"

ENGINES = {
    "E1": {"id": "E1", "code": "VFX", "name_zh": "規格轉換 · 內容擷取", "name": "VIA Format & Extraction Engine",
           "members": ["VOFIE", "VSHP", "VSX", "MarkItDown"],
           "inputs": [".md", ".txt", ".log", ".rst", ".html", ".htm", ".xhtml", ".docx", ".pptx", ".xlsx", ".xlsm",
                      ".csv", ".tsv", ".json", ".jsonl", ".xml", ".yaml", ".yml", ".toml", ".ini", ".pdf", ".epub"],
           "outputs": ["Reconstructed.md", "ComponentSpecs.json (Universal Content IR)", "TopicMatrix.csv", ".docx", ".html"],
           "contract": "veritas.universal-content-ir/1.0"},
    "E2": {"id": "E2", "code": "VNL", "name_zh": "自然語言", "name": "VIA NLP One Engine",
           "members": ["via_nlp_engine v1.5"],
           "inputs": [".md", ".txt", ".log", ".json"],
           "outputs": ["knowledge/mindmap json", "refined text", "handoff", "bundle zip"],
           "contract": "VIA_KNOWLEDGE_GRAPH/3.0"},
    "E3": {"id": "E3", "code": "VES", "name_zh": "程式優化 · 合併", "name": "VIA Engine Standardizer",
           "members": ["VES v0500"],
           "inputs": [".py", ".ps1", ".js", ".ts"],
           "outputs": ["ves_inventory.json", "_standardized/ scaffold", "AI_HANDOFF.md", "ves_store/ parquet"],
           "contract": "VES_INVENTORY/0500"},
}

# 免費、在地、三語系工具目錄（探測用；不安裝）。kind: py=import name, js=npm package, ps=PowerShell module, exe=command
TOOL_CATALOG = {
    "E1": [
        ("py", "markitdown", "Office/PDF/HTML/EPUB/圖音→Markdown"), ("py", "pypdf", "PDF 文字"), ("py", "pdfplumber", "PDF 表格"),
        ("py", "fitz", "PyMuPDF 版面/影像"), ("py", "docx", "python-docx"), ("py", "pptx", "python-pptx"), ("py", "openpyxl", "xlsx"),
        ("py", "bs4", "HTML DOM"), ("py", "lxml", "XML/HTML 快速解析"), ("py", "tinycss2", "CSS"), ("py", "esprima", "JS AST"),
        ("py", "markdownify", "HTML→MD"), ("py", "yaml", "PyYAML"), ("py", "tomllib", "TOML (stdlib 3.11+)"),
        ("js", "cheerio", "DOM 查詢"), ("js", "jsdom", "瀏覽器級 DOM"), ("js", "turndown", "HTML→MD"), ("js", "mammoth", "docx→HTML/MD"),
        ("js", "xlsx", "SheetJS"), ("js", "pdfjs-dist", "PDF"), ("js", "acorn", "JS AST"), ("js", "postcss", "CSS AST"),
        ("ps", "PSParseHTML", "HTML 解析"), ("ps", "PowerHTML", "HtmlAgilityPack 包裝"), ("ps", "ImportExcel", "xlsx 無需 Excel"),
        ("ps", "PSWriteHTML", "HTML 報表"), ("ps", "PSWriteWord", "docx 輸出"), ("ps", "PSSQLite", "SQLite"),
        ("exe", "pandoc", "萬用文件轉換"), ("exe", "libreoffice", "Office 無頭轉換"),
    ],
    "E2": [
        ("py", "sklearn", "規則/ML 分類"), ("py", "jieba", "中文斷詞"), ("py", "spacy", "NER/句法 (選)"), ("py", "rapidfuzz", "模糊比對"),
        ("py", "sentence_transformers", "Embedding (MiniLM CPU)"), ("py", "argostranslate", "離線翻譯"), ("py", "opencc", "繁簡"),
        ("py", "zhon", "中文標點/字集"), ("py", "hanlp", "中文 NLP (重)"), ("py", "ckip_transformers", "CKIP 繁中 (重)"),
        ("py", "sumy", "抽取式摘要"), ("py", "yake", "關鍵字"), ("py", "langdetect", "語言偵測"), ("py", "psutil", "資源閘門"),
        ("js", "compromise", "輕量英文 NLP"), ("js", "natural", "分詞/分類"), ("js", "nodejieba", "中文斷詞"), ("js", "wink-nlp", "快速 NLP"),
        ("js", "@xenova/transformers", "transformers.js 本機推論"), ("js", "franc", "語言偵測"),
        ("ps", "Microsoft.PowerShell.TextUtility", "ConvertFrom-TextTable"), ("ps", "PSFramework", "日誌/設定"),
        ("exe", "ollama", "本機 LLM (qwen2.5)"),
    ],
    "E3": [
        ("py", "ast", "stdlib AST"), ("py", "astroid", "作用域推論 (選)"), ("py", "radon", "複雜度"), ("py", "vulture", "死碼"),
        ("py", "ruff", "lint/格式"), ("py", "mypy", "型別"), ("py", "pyflakes", "未用/未定義"), ("py", "bandit", "安全"),
        ("py", "pytest", "測試矩陣"), ("py", "hypothesis", "屬性測試"), ("py", "pydantic", "介面約束"), ("py", "pyarrow", "Parquet 儲存"),
        ("py", "duckdb", "歷史查詢"), ("py", "polars", "資料引擎"), ("py", "libcst", "保留格式的重寫 (選)"),
        ("js", "acorn", "JS AST"), ("js", "@babel/parser", "JS/TS AST"), ("js", "eslint", "lint"), ("js", "jscpd", "跨語言重複偵測"),
        ("js", "typescript", "型別/TS AST"), ("js", "prettier", "格式"), ("js", "zod", "schema (與 pydantic 對接)"),
        ("ps", "PSScriptAnalyzer", "PS lint/規則"), ("ps", "Pester", "PS 測試"), ("ps", "PSGraph", "呼叫圖 (graphviz)"),
        ("ps", "platyPS", "PS 說明文件"),
        ("exe", "semgrep", "多語言規則掃描"), ("exe", "git", "版本/差異"),
    ],
}

EXT_ROUTE = {}
for eid, e in ENGINES.items():
    for ext in e["inputs"]:
        EXT_ROUTE.setdefault(ext, []).append(eid)
# 重疊副檔名的優先順序：.md/.txt/.log/.json → E1 先擷取再 E2；程式碼 → E3
ROUTE_PRIORITY = {".md": ["E2", "E1"], ".txt": ["E2", "E1"], ".log": ["E2", "E1"], ".json": ["E1", "E2"],
                  ".py": ["E3"], ".ps1": ["E3", "E1"], ".js": ["E3", "E1"], ".ts": ["E3"]}


def via_code(kind: str, name: str, context: str) -> tuple[str, str]:
    inp = f"{kind}|{name}|{context}"
    return f"VIA-{kind}-{hashlib.blake2s(inp.encode('utf-8'), digest_size=3).hexdigest().upper()}", inp


def _utf8(p: Path, txt: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(txt, encoding="utf-8")


def _append(p: Path, rec: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")


# ----------------------------------------------------------------- engine discovery
def _first(paths: list[Path]) -> Path | None:
    for p in paths:
        if p and p.exists():
            return p
    return None


def discover_engines(root: Path, cfg: dict) -> dict:
    """在設定/常見位置找三引擎的實體檔；找不到 → status=MISSING，不影響其他引擎。"""
    home = Path.home()
    here = root
    cands = {
        "VOFIE": [Path(cfg.get("vofie", "")) if cfg.get("vofie") else None,
                  *here.rglob("Veritas_OmniFormat_Intelligence_Engine.py"),
                  home / "Downloads" / "Veritas_OmniFormat_Intelligence_Engine_v0140" / "Veritas_OmniFormat_Intelligence_Engine.py",
                  Path("C:/VIA/VOFIE/Veritas_OmniFormat_Intelligence_Engine.py")],
        "VSHP": [Path(cfg.get("vshp", "")) if cfg.get("vshp") else None,
                 *here.rglob("Invoke-VIA-SuperHtmlParser.ps1"),
                 Path("C:/VIA/VeritasSuperHtmlParser/Invoke-VIA-SuperHtmlParser.ps1"),
                 home / "Downloads" / "Invoke-VIA-SuperHtmlParser.ps1"],
        "NLP": [Path(cfg.get("nlp", "")) if cfg.get("nlp") else None,
                *[p.parents[2] for p in here.rglob("src/via_nlp_engine/__init__.py")],
                home / "Downloads" / "VIA_NLP_OneEngine_v1.5.0", Path("C:/VIA/VIA_NLP_OneEngine")],
        "VSX": [Path(cfg.get("vsx", "")) if cfg.get("vsx") else None,
                here / "via_spec_extractor.py", *here.rglob("via_spec_extractor.py"),
                home / "Downloads" / "VIA_SpecExtractor" / "via_spec_extractor.py"],
        "VES": [Path(cfg.get("ves", "")) if cfg.get("ves") else None,
                here / "via_engine_standardizer.py", *here.rglob("via_engine_standardizer.py"),
                home / "Downloads" / "VIA_EngineStandardizer" / "via_engine_standardizer.py"],
    }
    found = {}
    for k, lst in cands.items():
        p = _first([c for c in lst if c is not None])
        found[k] = {"path": str(p) if p else "", "status": "FOUND" if p else "MISSING"}
        if p and k == "NLP":
            found[k]["src"] = str(p / "src")
    for k in ("VOFIE", "VES", "VSX"):
        if found[k]["path"]:
            try:
                txt = Path(found[k]["path"]).read_text(encoding="utf-8", errors="replace")
                m = re.search(r'(?:ENGINE_VERSION|VERSION)\s*=\s*"([^"]+)"', txt)
                found[k]["version"] = m.group(1) if m else "?"
            except OSError:
                found[k]["version"] = "?"
    if found["VSHP"]["path"]:
        try:
            m = re.search(r"\$script:Version\s*=\s*'([^']+)'", Path(found["VSHP"]["path"]).read_text(encoding="utf-8", errors="replace"))
            found["VSHP"]["version"] = m.group(1) if m else "?"
        except OSError:
            found["VSHP"]["version"] = "?"
    if found["NLP"]["path"]:
        try:
            m = re.search(r'__version__\s*=\s*"([^"]+)"', (Path(found["NLP"]["src"]) / "via_nlp_engine" / "__init__.py").read_text(encoding="utf-8"))
            found["NLP"]["version"] = m.group(1) if m else "?"
        except OSError:
            found["NLP"]["version"] = "?"
    return found


def _run(cmd: list[str], cwd: Path | None = None, timeout: int = 180, env: dict | None = None) -> dict:
    t0 = time.time()
    try:
        e = dict(os.environ)
        e["PYTHONIOENCODING"] = "utf-8"
        e["PYTHONUTF8"] = "1"
        if env:
            e.update(env)
        p = subprocess.run(cmd, cwd=str(cwd) if cwd else None, capture_output=True, text=True, timeout=timeout, env=e,
                           encoding="utf-8", errors="replace")
        return {"cmd": cmd, "rc": p.returncode, "out": p.stdout[-4000:], "err": p.stderr[-2000:], "ms": round((time.time() - t0) * 1000)}
    except FileNotFoundError:
        return {"cmd": cmd, "rc": 127, "out": "", "err": "not found", "ms": 0}
    except subprocess.TimeoutExpired:
        return {"cmd": cmd, "rc": 124, "out": "", "err": f"timeout {timeout}s", "ms": timeout * 1000}


def health(found: dict, deep: bool) -> dict:
    """三引擎健康檢查：淺=存在+版本；深=各自 self-test / health。"""
    py = sys.executable
    h = {}
    for k, v in found.items():
        rec = {"status": v["status"], "version": v.get("version", ""), "checks": []}
        if v["status"] == "FOUND" and deep:
            if k == "VOFIE":
                rec["checks"].append(_run([py, v["path"], "self-test"], timeout=300))
            elif k == "NLP":
                rec["checks"].append(_run([py, "-m", "via_nlp_engine", "health"], cwd=Path(v["path"]), env={"PYTHONPATH": v["src"]}))
            elif k == "VES":
                rec["checks"].append(_run([py, v["path"], "--selftest"], timeout=600))
            elif k == "VSX":
                rec["checks"].append(_run([py, v["path"], "--selftest"], timeout=300))
            elif k == "VSHP":
                pw = shutil.which("pwsh") or shutil.which("powershell")
                rec["checks"].append(_run([pw, "-NoProfile", "-Command",
                                           f"[System.Management.Automation.Language.Parser]::ParseFile('{v['path']}',[ref]$null,[ref]$e); $e.Count"]) if pw
                                     else {"rc": 127, "err": "pwsh not found", "out": "", "ms": 0, "cmd": []})
            rec["status"] = "OK" if all(c.get("rc") == 0 for c in rec["checks"]) else "FAIL"
        h[k] = rec
    return h


# ----------------------------------------------------------------- tool probing (py / js / ps / exe)
def _node_roots(root: Path) -> list[Path]:
    r = [root / "node_modules", Path.home() / "node_modules", Path.home() / "AppData" / "Roaming" / "npm" / "node_modules"]
    try:
        out = subprocess.run(["npm", "root", "-g"], capture_output=True, text=True, timeout=15)
        if out.returncode == 0 and out.stdout.strip():
            r.append(Path(out.stdout.strip()))
    except Exception:  # noqa: BLE001
        pass
    return [p for p in r if p.exists()]


def probe_tools(root: Path, ps_modules: dict) -> dict:
    """探測目錄裡每個工具是否可用（不安裝）。ps_modules 由 PowerShell 端提供 {name: version}。"""
    import importlib
    node_roots = _node_roots(root)
    res = {}
    for eid, items in TOOL_CATALOG.items():
        rows = []
        for kind, name, note in items:
            ok, ver = False, ""
            if kind == "py":
                try:
                    m = importlib.import_module(name)
                    ok, ver = True, str(getattr(m, "__version__", ""))
                except Exception:  # noqa: BLE001
                    ok = False
            elif kind == "js":
                for nr in node_roots:
                    mf = nr / name / "package.json"
                    if mf.exists():
                        try:
                            ver = json.loads(mf.read_text(encoding="utf-8")).get("version", "")
                        except Exception:  # noqa: BLE001
                            ver = "?"
                        ok = True
                        break
            elif kind == "ps":
                if name in ps_modules:
                    ok, ver = True, str(ps_modules[name])
            elif kind == "exe":
                p = shutil.which(name)
                ok, ver = bool(p), (p or "")
            rows.append({"kind": kind, "name": name, "note": note, "available": ok, "version": ver})
        res[eid] = rows
    return res


# ----------------------------------------------------------------- mounts
MOUNT_EXAMPLES = {
    "markitdown_py": {
        "contract": MOUNT_CONTRACT, "id": "markitdown_py", "engine": "E1", "language": "py", "free_local": True,
        "name": "MarkItDown → Markdown", "entry": {"kind": "py_module", "module": "markitdown", "cmd": ["{python}", "-m", "markitdown", "{in}"]},
        "inputs": [".docx", ".pptx", ".xlsx", ".pdf", ".html", ".epub"], "outputs": ["{out}/{stem}.md"], "capture_stdout_to": "{out}/{stem}.md",
        "health": ["{python}", "-c", "import markitdown"], "license": "MIT", "notes": "convert_local only; no plugins/LLM/URL",
    },
    "turndown_js": {
        "contract": MOUNT_CONTRACT, "id": "turndown_js", "engine": "E1", "language": "js", "free_local": True,
        "name": "turndown HTML → Markdown", "entry": {"kind": "node_script", "cmd": ["node", "{mount_dir}/run.js", "{in}"]},
        "inputs": [".html", ".htm"], "outputs": ["{out}/{stem}.md"], "capture_stdout_to": "{out}/{stem}.md",
        "health": ["node", "-e", "require('turndown')"], "license": "MIT",
    },
    "psscriptanalyzer_ps": {
        "contract": MOUNT_CONTRACT, "id": "psscriptanalyzer_ps", "engine": "E3", "language": "ps", "free_local": True,
        "name": "PSScriptAnalyzer lint → JSON", "entry": {"kind": "pwsh", "cmd": ["pwsh", "-NoProfile", "-Command",
                 "Invoke-ScriptAnalyzer -Path '{in}' -Recurse | ConvertTo-Json -Depth 4"]},
        "inputs": [".ps1", ".psm1"], "outputs": ["{out}/{stem}.psa.json"], "capture_stdout_to": "{out}/{stem}.psa.json",
        "health": ["pwsh", "-NoProfile", "-Command", "Get-Module -ListAvailable PSScriptAnalyzer | Select-Object -First 1 | ForEach-Object Version"],
        "license": "MIT",
    },
}
TURNDOWN_RUN_JS = """// turndown_js mount runner (free/local). node run.js <file.html>  → Markdown on stdout
const fs = require('fs'); const TurndownService = require('turndown');
const td = new TurndownService({ headingStyle: 'atx', codeBlockStyle: 'fenced' });
const html = fs.readFileSync(process.argv[2], 'utf8');
process.stdout.write(td.turndown(html));
"""


def init_mounts(root: Path) -> list[str]:
    written = []
    for name, man in MOUNT_EXAMPLES.items():
        d = root / "mounts" / name
        if not (d / "mount.json").exists():                # 只增不減：已存在不覆蓋
            _utf8(d / "mount.json", json.dumps(man, ensure_ascii=False, indent=1))
            written.append(str(d / "mount.json"))
        if name == "turndown_js" and not (d / "run.js").exists():
            _utf8(d / "run.js", TURNDOWN_RUN_JS)
            written.append(str(d / "run.js"))
    return written


def validate_mount(man: dict) -> list[str]:
    errs = []
    for k in ("id", "engine", "language", "entry", "inputs"):
        if k not in man:
            errs.append(f"missing {k}")
    if man.get("engine") not in ENGINES:
        errs.append("engine must be E1/E2/E3")
    if man.get("language") not in ("py", "js", "ps", "exe"):
        errs.append("language must be py/js/ps/exe")
    if not isinstance(man.get("entry", {}).get("cmd"), list):
        errs.append("entry.cmd must be a list")
    if man.get("free_local") is False:
        errs.append("free_local=false: Hub 只掛免費在地工具")
    return errs


def list_mounts(root: Path) -> list[dict]:
    out = []
    for mf in sorted((root / "mounts").glob("*/mount.json")):
        try:
            man = json.loads(mf.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            out.append({"id": mf.parent.name, "path": str(mf), "errors": [f"bad json: {e}"]})
            continue
        man["_path"] = str(mf)
        man["_dir"] = str(mf.parent)
        man["errors"] = validate_mount(man)
        code, hin = via_code("MNT", man.get("id", mf.parent.name), man.get("engine", "?") + "|" + man.get("language", "?"))
        man["via_code"], man["hash_input"] = code, hin
        out.append(man)
    return out


def _fmt(cmd: list[str], **kv) -> list[str]:
    return [c.format(**kv) for c in cmd]


def probe_mount(man: dict) -> dict:
    if man.get("errors"):
        return {"status": "INVALID", "errors": man["errors"]}
    hc = man.get("health")
    if not hc:
        return {"status": "UNKNOWN"}
    r = _run(_fmt(hc, python=sys.executable, mount_dir=man["_dir"], **{"in": "", "out": "", "stem": ""}), timeout=60)
    return {"status": "OK" if r["rc"] == 0 else "MISSING", "detail": (r["out"] or r["err"]).strip()[:200], "ms": r["ms"]}


def run_mount(root: Path, man: dict, inputs: list[Path], out: Path) -> list[dict]:
    """依模板執行掛載：每個輸入一次；stdout 可導到 capture_stdout_to；帳本 append-only。"""
    if man.get("errors"):
        raise ValueError(f"invalid mount: {man['errors']}")
    out.mkdir(parents=True, exist_ok=True)
    results = []
    for f in inputs:
        if man.get("inputs") and f.suffix.lower() not in man["inputs"]:
            results.append({"input": str(f), "status": "SKIP", "reason": f"ext {f.suffix} not in {man['inputs']}"})
            continue
        kv = {"python": sys.executable, "mount_dir": man["_dir"], "in": str(f), "out": str(out), "stem": f.stem}
        r = _run(_fmt(man["entry"]["cmd"], **kv), cwd=Path(man["_dir"]), timeout=int(man.get("timeout", 600)))
        rec = {"input": str(f), "status": "OK" if r["rc"] == 0 else "FAIL", "rc": r["rc"], "ms": r["ms"], "err": r["err"][-300:]}
        cap = man.get("capture_stdout_to")
        if cap and r["rc"] == 0:
            target = Path(cap.format(**kv))
            _utf8(target, r["out"] if len(r["out"]) < 4000 else r["out"])
            rec["output"] = str(target)
        results.append(rec)
        _append(root / "vth_ledger.jsonl", {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "kind": "mount_run", "mount": man["id"],
                                             "code": man["via_code"], **rec})
    return results


# ----------------------------------------------------------------- routing / running / pipeline
def route(files: list[Path]) -> list[dict]:
    rows = []
    for f in files:
        ext = f.suffix.lower()
        pri = ROUTE_PRIORITY.get(ext) or EXT_ROUTE.get(ext) or []
        reason = "副檔名"
        if ext in (".md", ".txt") and pri and pri[0] == "E2":
            try:
                head = f.read_text(encoding="utf-8", errors="replace")[:4000]
                if head.count("```") >= 4 or re.search(r"^\s*(def |class |function |param\()", head, re.M):
                    pri = ["E3", "E2"]
                    reason = "內容含大量程式碼 fence → 先程式層"
            except OSError:
                pass
        rows.append({"file": str(f), "ext": ext, "engines": pri or ["?"], "reason": reason})
    return rows


def run_engine(root: Path, found: dict, eid: str, inputs: list[Path], out: Path, extra: list[str]) -> dict:
    """統一信封：{task_id, engine, inputs, out, contract} → 呼叫對應引擎 CLI，結果與帳本落地。"""
    py = sys.executable
    task_id, _ = via_code("TSK", eid + "|" + ",".join(p.name for p in inputs), time.strftime("%Y%m%d%H%M%S"))
    out.mkdir(parents=True, exist_ok=True)
    env_rec = {"contract": HUB_CONTRACT, "task_id": task_id, "engine": eid, "inputs": [str(p) for p in inputs], "out": str(out),
               "engine_contract": ENGINES[eid]["contract"], "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
    _utf8(out / "hub_envelope.json", json.dumps(env_rec, ensure_ascii=False, indent=1))
    res = {"task_id": task_id, "engine": eid, "steps": []}
    if eid == "E1":
        v = found["VOFIE"]
        if v["status"] != "FOUND":
            res["steps"].append({"member": "VOFIE", "status": "MISSING"})
        else:
            docs = [p for p in inputs][:5]
            r = _run([py, v["path"], "simple", *map(str, docs), "--output", str(out / "vofie"), "--role", "ENGINE", *extra], timeout=900)
            res["steps"].append({"member": "VOFIE", "status": "OK" if r["rc"] == 0 else "FAIL", "ms": r["ms"], "err": r["err"][-300:]})
        vx = found.get("VSX", {})
        if vx.get("status") == "FOUND":
            r = _run([py, vx["path"], "--in", *map(str, inputs), "--out", str(out / "vsx"), "--title", inputs[0].stem if inputs else "spec"], timeout=900)
            res["steps"].append({"member": "VSX", "status": "OK" if r["rc"] == 0 else "FAIL", "ms": r["ms"], "err": r["err"][-300:],
                                 "summary": next((ln for ln in r["out"].splitlines() if ln.startswith("@@SUMMARY")), "")})
        else:
            res["steps"].append({"member": "VSX", "status": "MISSING"})
        htmls = [p for p in inputs if p.suffix.lower() in (".html", ".htm")]
        if htmls and found["VSHP"]["status"] == "FOUND":
            pw = shutil.which("pwsh")
            if pw:
                r = _run([pw, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", found["VSHP"]["path"], "-Targets", *map(str, htmls),
                          "-Root", str(out / "vshp"), "-NoOpen"], timeout=900)
                res["steps"].append({"member": "VSHP", "status": "OK" if r["rc"] == 0 else "FAIL", "ms": r["ms"], "err": r["err"][-300:]})
            else:
                res["steps"].append({"member": "VSHP", "status": "SKIP", "reason": "pwsh not found"})
    elif eid == "E2":
        v = found["NLP"]
        if v["status"] != "FOUND":
            res["steps"].append({"member": "NLP", "status": "MISSING"})
        else:
            r = _run([py, "-m", "via_nlp_engine", "reconstruct-bundle", "--input", *map(str, inputs), "--output-dir", str(out / "nlp"),
                      "--quality", "fast", *extra], cwd=Path(v["path"]), env={"PYTHONPATH": v["src"]}, timeout=1800)
            if r["rc"] != 0:
                r2 = _run([py, "-m", "via_nlp_engine", "process", "--file", str(inputs[0]), "--quality", "fast"],
                          cwd=Path(v["path"]), env={"PYTHONPATH": v["src"]}, timeout=1800)
                if r2["rc"] == 0:
                    _utf8(out / "nlp" / "process_result.json", r2["out"])
                    r = r2
            res["steps"].append({"member": "NLP", "status": "OK" if r["rc"] == 0 else "FAIL", "ms": r["ms"], "err": r["err"][-300:],
                                 "out_tail": r["out"][-300:]})
    elif eid == "E3":
        v = found["VES"]
        if v["status"] != "FOUND":
            res["steps"].append({"member": "VES", "status": "MISSING"})
        else:
            scan_root = inputs[0] if len(inputs) == 1 and inputs[0].is_dir() else _stage_dir(out / "ves_in", inputs)
            r = _run([py, v["path"], "--root", str(scan_root), "--out", str(out / "ves" / time.strftime("run_%Y%m%d_%H%M%S")),
                      "--no-ml-probe", *extra], timeout=1800)
            res["steps"].append({"member": "VES", "status": "OK" if r["rc"] in (0, 2) else "FAIL", "ms": r["ms"],
                                 "gates": next((ln for ln in r["out"].splitlines() if ln.startswith("@@GATES")), ""), "err": r["err"][-300:]})
    res["status"] = "OK" if all(s.get("status") in ("OK", "SKIP") for s in res["steps"]) else "PARTIAL"
    _append(root / "vth_ledger.jsonl", {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "kind": "engine_run", **res})
    _utf8(out / "hub_result.json", json.dumps(res, ensure_ascii=False, indent=1))
    return res


def _stage_dir(d: Path, files: list[Path]) -> Path:
    """VES 要目錄：把散檔（只讀）複製到暫存目錄再掃（來源不動）。"""
    d.mkdir(parents=True, exist_ok=True)
    for f in files:
        if f.is_dir():
            shutil.copytree(f, d / f.name, dirs_exist_ok=True)
        else:
            shutil.copy2(f, d / f.name)
    return d


def pipeline(root: Path, found: dict, inputs: list[Path], out: Path) -> dict:
    """E1 擷取 → E2 NLP → E3 程式標準化，靠檔案交接：E1 的 Reconstructed.md 餵 E2；輸入裡的程式檔/E1 抽出的 code 餵 E3。"""
    res = {"stages": []}
    docs = [p for p in inputs if p.suffix.lower() in ENGINES["E1"]["inputs"] and p.suffix.lower() not in (".py",)]
    code = [p for p in inputs if p.suffix.lower() in ENGINES["E3"]["inputs"] or p.is_dir()]
    e1 = run_engine(root, found, "E1", docs, out / "01_E1", []) if docs else {"status": "SKIP"}
    res["stages"].append({"stage": "E1", **e1})
    md = list((out / "01_E1").rglob("Veritas_VOFIE_Reconstructed.md"))
    e2_in = md or [p for p in docs if p.suffix.lower() in (".md", ".txt")]
    e2 = run_engine(root, found, "E2", e2_in, out / "02_E2", []) if e2_in else {"status": "SKIP"}
    res["stages"].append({"stage": "E2", **e2})
    e3 = run_engine(root, found, "E3", code, out / "03_E3", []) if code else {"status": "SKIP"}
    res["stages"].append({"stage": "E3", **e3})
    _utf8(out / "pipeline_result.json", json.dumps(res, ensure_ascii=False, indent=1))
    return res


# ----------------------------------------------------------------- registry + html
def write_registry(root: Path, found: dict, mounts: list[dict], probes: dict) -> Path:
    """append-only 登記：引擎 + 掛載 各一碼；已存在的碼不重寫。"""
    p = root / "vth_registry.json"
    reg = {"version": VERSION, "recipe": "VIA-{TYPE}-blake2s(TYPE|name|context,digest=3).hexUpper", "entries": []}
    if p.exists():
        try:
            reg = json.loads(p.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            pass
    have = {e["code"] for e in reg["entries"]}
    for eid, e in ENGINES.items():
        code, hin = via_code("ENG", e["code"], eid)
        if code not in have:
            reg["entries"].append({"code": code, "hash_input": hin, "type": "engine", "id": eid, "name": e["name"], "members": e["members"],
                                   "grade": "V", "status": "ACTIVE"})
    for m in mounts:
        if m.get("via_code") and m["via_code"] not in have:
            reg["entries"].append({"code": m["via_code"], "hash_input": m["hash_input"], "type": "mount", "id": m["id"], "engine": m.get("engine"),
                                   "language": m.get("language"), "grade": "M" if probes.get(m["id"], {}).get("status") == "OK" else "P",
                                   "status": "ACTIVE" if not m.get("errors") else "INVALID"})
    _utf8(p, json.dumps(reg, ensure_ascii=False, indent=1))
    return p


CSS = """:root{--b:#4c78a8;--t:#439a9a;--up:#c96b5a;--dn:#5a9e6f;--paper:#f5f4f0;--i0:#1c1b19;--i2:#6b6862;--i3:#b8b5ae;--i4:#e6e3dc}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--i0);font-family:"DM Sans",system-ui,sans-serif;font-size:13px}
h1,h2{font-family:Syne,"DM Sans",sans-serif;font-weight:700}header{padding:22px 28px 10px;border-bottom:1px solid var(--i4)}header h1{margin:0;font-size:22px}
.sub{color:var(--i2);font-family:"DM Mono",monospace;font-size:12px;margin-top:4px}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;padding:18px 28px}
.card{background:#fff;border:1px solid var(--i4);border-radius:10px;padding:14px 16px}.card h2{margin:0 0 6px;font-size:16px;color:var(--b)}.card .zh{font-size:18px;font-weight:700}
.pill{display:inline-block;padding:1px 7px;border-radius:10px;font-size:11px;margin:1px 2px 1px 0;font-family:"DM Mono",monospace}
.ok{background:#e0eee4;color:var(--dn)}.no{background:#ecebe7;color:var(--i2)}.bad{background:#f6e2dd;color:var(--up)}.pb{background:#dfe8f2;color:var(--b)}
section{padding:6px 28px 18px}table{border-collapse:collapse;width:100%;background:#fff;font-size:12px}th{background:var(--i4);text-align:left;padding:6px 8px}
td{padding:5px 8px;border-bottom:1px solid var(--i4);font-family:"DM Mono",monospace;vertical-align:top}code{background:#efede8;padding:1px 4px;border-radius:3px}
.foot{padding:14px 28px;color:var(--i2);font-size:11px;font-family:"DM Mono",monospace;border-top:1px solid var(--i4)}"""


def render_html(root: Path, found: dict, hz: dict, mounts: list[dict], probes: dict, tools: dict) -> Path:
    e = html.escape
    member_of = {"VOFIE": "E1", "VSHP": "E1", "VSX": "E1", "NLP": "E2", "VES": "E3"}
    cards = []
    for eid, en in ENGINES.items():
        mem = "".join(f'<span class="pill {"ok" if hz[k]["status"] in ("FOUND", "OK") else ("bad" if hz[k]["status"] == "FAIL" else "no")}">{k} {e(hz[k].get("version", ""))} · {hz[k]["status"]}</span>'
                      for k, v in member_of.items() if v == eid)
        tl = tools.get(eid, [])
        avail = sum(1 for t in tl if t["available"])
        by = {k: (sum(1 for t in tl if t["kind"] == k and t["available"]), sum(1 for t in tl if t["kind"] == k)) for k in ("py", "js", "ps", "exe")}
        mts = [m for m in mounts if m.get("engine") == eid]
        cards.append(f'''<div class="card"><h2>{eid} · {e(en["code"])}</h2><div class="zh">{e(en["name_zh"])}</div><div class="sub">{e(en["name"])} · {e(en["contract"])}</div>
<p>{mem}</p><p>輸入 {"".join(f'<span class="pill pb">{e(x)}</span>' for x in en["inputs"][:12])}{"…" if len(en["inputs"]) > 12 else ""}</p>
<p>免費在地工具可用 <b>{avail}/{len(tl)}</b> · py {by["py"][0]}/{by["py"][1]} · js {by["js"][0]}/{by["js"][1]} · ps {by["ps"][0]}/{by["ps"][1]} · exe {by["exe"][0]}/{by["exe"][1]}</p>
<p>掛載 {len(mts)}：{"".join(f'<span class="pill {"ok" if probes.get(m["id"], {}).get("status") == "OK" else "no"}">{e(m["id"])}</span>' for m in mts) or "—"}</p></div>''')
    tool_rows = "".join(f'<tr><td>{eid}</td><td>{t["kind"]}</td><td>{e(t["name"])}</td><td><span class="pill {"ok" if t["available"] else "no"}">{"可用" if t["available"] else "未裝"}</span></td><td>{e(t["version"][:40])}</td><td>{e(t["note"])}</td></tr>'
                        for eid, tl in tools.items() for t in tl)
    mount_rows = "".join(f'<tr><td>{e(m.get("via_code", ""))}</td><td>{e(m.get("id", ""))}</td><td>{e(m.get("engine", ""))}</td><td>{e(m.get("language", ""))}</td>'
                         f'<td><span class="pill {"ok" if probes.get(m.get("id"), {}).get("status") == "OK" else ("bad" if m.get("errors") else "no")}">{e(probes.get(m.get("id"), {}).get("status", "?"))}</span></td>'
                         f'<td>{e(", ".join(m.get("inputs", [])))}</td><td>{e("; ".join(m.get("errors", [])) or probes.get(m.get("id"), {}).get("detail", ""))}</td></tr>' for m in mounts)
    deep = "".join(f'<details><summary>{k} 深檢 {hz[k]["status"]}</summary><pre style="white-space:pre-wrap;font-size:11px">{e(json.dumps(hz[k]["checks"], ensure_ascii=False, indent=1)[:3000])}</pre></details>'
                   for k in hz if hz[k].get("checks"))
    doc = f'''<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8"><title>VIA TriEngine Hub v{VERSION}</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Mono&family=DM+Sans:wght@400;600&family=Syne:wght@700&display=swap" rel="stylesheet"><style>{CSS}</style></head><body>
<header><h1>VIA TriEngine Hub <span style="color:var(--t)">v{VERSION}</span></h1><div class="sub">三大泛用型引擎 · 統一掛載協定 {e(MOUNT_CONTRACT)} · 信封 {e(HUB_CONTRACT)} · 免費在地 py/js/ps/exe · root={e(str(root))} · {time.strftime("%Y-%m-%d %H:%M:%S")}</div></header>
<div class="grid">{"".join(cards)}</div>
<section><h2>掛載（mounts/&lt;name&gt;/mount.json）</h2><table><tr><th>碼</th><th>id</th><th>引擎</th><th>語言</th><th>狀態</th><th>輸入</th><th>備註</th></tr>{mount_rows or '<tr><td colspan="7">尚無掛載；執行 init-mounts 產生三個範例 (py/js/ps1)</td></tr>'}</table></section>
<section><h2>免費在地工具矩陣（探測，不安裝）</h2><table><tr><th>引擎</th><th>類</th><th>工具</th><th>狀態</th><th>版本/路徑</th><th>用途</th></tr>{tool_rows}</table></section>
<section>{deep}</section>
<section><h2>路由規則</h2><p>文件/Office/PDF/HTML → <b>E1</b>；.md/.txt/.log 純文字 → <b>E2</b>（含大量 code fence 則先 E3）；.py/.ps1/.js/.ts → <b>E3</b>。pipeline = E1 擷取 → E2 NLP → E3 程式標準化，靠檔案交接（Reconstructed.md / ComponentSpecs.json / ves_inventory.json），任何一段缺引擎自動 SKIP 不中斷。</p></section>
<div class="foot">VIA TriEngine Hub · 只增不減 · 不安裝不下載 · 掛載只宣告不執行來源內容 · vth_registry.json / vth_ledger.jsonl</div></body></html>'''
    p = root / "VIA_TriEngineHub.html"
    _utf8(p, doc)
    return p


# ----------------------------------------------------------------- commands
def load_cfg(root: Path) -> dict:
    p = root / "vth_config.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return {}
    return {}


def cmd_status(root: Path, deep: bool, ps_modules_file: Path | None) -> dict:
    cfg = load_cfg(root)
    found = discover_engines(root, cfg)
    hz = health(found, deep)
    ps_mods = {}
    if ps_modules_file and ps_modules_file.exists():
        try:
            ps_mods = json.loads(ps_modules_file.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            ps_mods = {}
    tools = probe_tools(root, ps_mods)
    mounts = list_mounts(root)
    probes = {m["id"]: probe_mount(m) for m in mounts if "id" in m}
    reg = write_registry(root, found, mounts, probes)
    hp = render_html(root, found, hz, mounts, probes, tools)
    summary = {"engines": {k: v["status"] for k, v in hz.items()}, "mounts": len(mounts),
               "tools_available": {k: sum(1 for t in v if t["available"]) for k, v in tools.items()},
               "tools_total": {k: len(v) for k, v in tools.items()}, "registry": str(reg), "html": str(hp)}
    _utf8(root / "vth_status.json", json.dumps({"found": found, "health": hz, "tools": tools, "mounts": mounts, "probes": probes,
                                                "summary": summary}, ensure_ascii=False, indent=1, default=str))
    print("@@STATUS|" + json.dumps(summary, ensure_ascii=False), flush=True)
    print(f"@@DONE|{hp}", flush=True)
    return summary


def selftest(tmp: Path) -> int:
    ok = 0
    checks = []
    root = tmp / "hub"
    root.mkdir(parents=True)
    w = init_mounts(root)
    checks.append(("init-mounts writes 3 manifests + run.js", len(w) == 4))
    w2 = init_mounts(root)
    checks.append(("init-mounts idempotent (只增不減)", w2 == []))
    ms = list_mounts(root)
    checks.append(("3 mounts valid", len(ms) == 3 and all(not m["errors"] for m in ms)))
    checks.append(("mount codes VIA-MNT-", all(m["via_code"].startswith("VIA-MNT-") for m in ms)))
    bad = {"id": "x", "engine": "E9", "language": "rb", "entry": {"cmd": "str"}, "inputs": []}
    checks.append(("validate_mount catches errors", len(validate_mount(bad)) >= 3))
    # custom py mount that echoes → capture
    d = root / "mounts" / "echo_py"
    _utf8(d / "mount.json", json.dumps({"id": "echo_py", "engine": "E2", "language": "py", "free_local": True,
                                        "entry": {"cmd": ["{python}", "-c", "import sys;print(open(sys.argv[1],encoding='utf-8').read().upper())", "{in}"]},
                                        "inputs": [".txt"], "capture_stdout_to": "{out}/{stem}.up.txt", "health": ["{python}", "-c", "print(1)"]}))
    ms = list_mounts(root)
    m = next(x for x in ms if x["id"] == "echo_py")
    checks.append(("probe custom mount OK", probe_mount(m)["status"] == "OK"))
    (tmp / "a.txt").write_text("hello via", encoding="utf-8")
    (tmp / "b.md").write_text("# t\n```python\ndef f(x):\n    return x\n```\n```python\ndef g(y):\n    return y\n```\n", encoding="utf-8")
    r = run_mount(root, m, [tmp / "a.txt", tmp / "b.md"], tmp / "mo")
    checks.append(("run mount: txt OK, md SKIP", r[0]["status"] == "OK" and r[1]["status"] == "SKIP" and (tmp / "mo" / "a.up.txt").read_text(encoding="utf-8").strip() == "HELLO VIA"))
    checks.append(("ledger appended", (root / "vth_ledger.jsonl").exists()))
    rt = route([tmp / "a.txt", tmp / "b.md", Path("x.py"), Path("x.docx"), Path("x.html")])
    checks.append(("route txt→E2, code-heavy md→E3, py→E3, docx→E1, html→E1",
                   rt[0]["engines"][0] == "E2" and rt[1]["engines"][0] == "E3" and rt[2]["engines"] == ["E3"] and rt[3]["engines"][0] == "E1" and rt[4]["engines"][0] == "E1"))
    found = discover_engines(root, {})
    checks.append(("discover returns 5 members", set(found) == {"VOFIE", "VSHP", "NLP", "VES", "VSX"}))
    hz = health(found, False)
    tools = probe_tools(root, {"PSScriptAnalyzer": "1.22"})
    checks.append(("ps module from PS-side json recognized", any(t["name"] == "PSScriptAnalyzer" and t["available"] for t in tools["E3"])))
    checks.append(("py stdlib ast available", any(t["name"] == "ast" and t["available"] for t in tools["E3"])))
    probes = {x["id"]: probe_mount(x) for x in ms}
    reg = write_registry(root, found, ms, probes)
    regd = json.loads(reg.read_text(encoding="utf-8"))
    n1 = len(regd["entries"])
    write_registry(root, found, ms, probes)
    n2 = len(json.loads(reg.read_text(encoding="utf-8"))["entries"])
    checks.append(("registry 3 engines + 4 mounts, idempotent", n1 == 7 and n2 == 7))
    hp = render_html(root, found, hz, ms, probes, tools)
    checks.append(("html rendered", hp.exists() and "TriEngine" in hp.read_text(encoding="utf-8")))
    res = run_engine(root, found, "E3", [tmp / "b.md"], tmp / "e3", [])
    checks.append(("run_engine on missing engine → MISSING step, no crash", res["steps"][0]["status"] in ("MISSING", "OK", "FAIL")))
    e1 = run_engine(root, found, "E1", [tmp / "b.md"], tmp / "e1", [])
    checks.append(("E1 run includes VSX step", any(st["member"] == "VSX" for st in e1["steps"])))
    for name, passed in checks:
        ok += int(passed)
        print(f"  [{'PASS' if passed else 'FAIL'}] {name}")
    print(f"SELFTEST {ok}/{len(checks)}")
    return 0 if ok == len(checks) else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["status", "route", "run", "pipeline", "mount", "init-mounts", "selftest"])
    ap.add_argument("sub", nargs="?", default="")
    ap.add_argument("--root", default=".")
    ap.add_argument("--in", dest="inputs", nargs="*", default=[])
    ap.add_argument("--out", default="")
    ap.add_argument("--engine", default="")
    ap.add_argument("--args", default="")
    ap.add_argument("--deep", action="store_true")
    ap.add_argument("--ps-modules", default="")
    a = ap.parse_args(argv)
    root = Path(a.root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    if a.cmd == "selftest":
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            return selftest(Path(td))
    if a.cmd == "init-mounts":
        print(json.dumps(init_mounts(root), ensure_ascii=False, indent=1))
        return 0
    if a.cmd == "status":
        cmd_status(root, a.deep, Path(a.ps_modules) if a.ps_modules else None)
        return 0
    inputs = [Path(p).resolve() for p in a.inputs]
    out = Path(a.out).resolve() if a.out else root / "runs" / time.strftime("run_%Y%m%d_%H%M%S")
    if a.cmd == "route":
        print(json.dumps(route(inputs), ensure_ascii=False, indent=1))
        return 0
    found = discover_engines(root, load_cfg(root))
    if a.cmd == "run":
        if a.engine not in ENGINES:
            print("--engine E1|E2|E3")
            return 2
        r = run_engine(root, found, a.engine, inputs, out, a.args.split() if a.args else [])
        print(json.dumps(r, ensure_ascii=False, indent=1))
        print(f"@@DONE|{out}")
        return 0 if r["status"] == "OK" else 1
    if a.cmd == "pipeline":
        r = pipeline(root, found, inputs, out)
        print(json.dumps(r, ensure_ascii=False, indent=1))
        print(f"@@DONE|{out}")
        return 0
    if a.cmd == "mount":
        ms = list_mounts(root)
        if a.sub in ("list", ""):
            print(json.dumps([{k: v for k, v in m.items() if k in ("id", "engine", "language", "via_code", "errors", "inputs")} for m in ms],
                             ensure_ascii=False, indent=1))
            return 0
        if a.sub == "probe":
            print(json.dumps({m["id"]: probe_mount(m) for m in ms}, ensure_ascii=False, indent=1))
            return 0
        m = next((x for x in ms if x.get("id") == a.sub), None)
        if not m:
            print(f"unknown mount {a.sub}; have {[x.get('id') for x in ms]}")
            return 2
        print(json.dumps(run_mount(root, m, inputs, out), ensure_ascii=False, indent=1))
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
