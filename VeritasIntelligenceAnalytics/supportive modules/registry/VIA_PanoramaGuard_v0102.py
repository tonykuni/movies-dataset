#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VIA_PanoramaGuard v0102 — 薄尾:全景掃描 + 安全修復一輪,補上「任何對象都能用、省額度」缺的功能與 15 個在地免費工具

操作員 2026-11-22 01:03:「強化這全景式檢視安全修復一輪的指令,可用於任何對象作為 VCGC 節省額度支援開發的重要工具,
解釋還有什麼不齊全的功能也把它加上去,在地免費工具的空間最佳 15 個加入來強化這個功能,測試無誤後上傳為功能引擎註冊」。
v0101(上傳原檔,一字不動)只做 Python AST 掃描、AST 等價的安全修復覆層、棘輪帳本、唯讀 MCP。本版補:
  ① 範圍:--changed-since <git 參照>(只看改過與新增的檔)· --paths <檔…>  → 大樹只掃要看的,省時間也省額度
  ② 快取:同內容 + 同規則 + 同版本的檔不再重剖析(--no-cache 關)
  ③ 304:--if-etag <上一輪 etag>,範圍內檔、規則、工具都沒變就只回一行,不重跑
  ④ 15 個在地免費工具(沒裝 = 灰燈,不裝不連網;裝套件只經 VCGC 安裝閘):
     ruff(lint + 格式漂移)· mypy · pyright · bandit · detect-secrets · vulture · radon · lizard · pylint(跨檔重複碼)·
     interrogate · codespell · deptry · pip check · yamllint · PSScriptAnalyzer(沒有就退 pwsh 剖析器 / tree-sitter)
     另內建 JSON 語法檢查與 PowerShell「param() 必須是第一個可執行敘述」檢查
  ⑤ 工具輔助修復:repair --tool-fix → 只用 ruff 的 safe 修正,改在覆層副本;逐檔要 compile 過、本引擎不新增紅、ruff 件數下降,
     有專案測試就前後再比一次,不過全部退回
  ⑥ 治理剖面(--profile via|generic|auto):VIA 樹自動加 加速器橋 / 網路橋 / 禁 TA-Lib / 不准程式寫同意閘 / PS 加速橋 檢查
  ⑦ 產出:tools.json · results.sarif(SARIF 2.1.0)· pastepack.txt(≤300 行、只黃紅、以 NEXT: 結尾)· tools.html(四色燈在第一欄)
  ⑧ MCP 唯讀多兩個工具:tool_findings(分頁)· pastepack
唯讀界線照 v0101:不執行受掃的程式、不改原檔(修復只在工作樹外的覆層)、不連網;工具訊息裡的長字串常值一律遮成「…」。
結束碼照 v0101:0 完成 · 1 仍有紅燈 · 2 阻擋或執行失敗。
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

import argparse
import ast
import collections
import concurrent.futures as cf
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VIA_PanoramaGuard"
TAIL = "0.1.2"
TOOL_TIMEOUT = 300
CHUNK = 150
HEAVY_LIMIT = 120          # auto 模式:Python 檔多於這數,重工具(mypy · pyright · lizard · pylint)略過(灰),要跑就 --tools all
PASTE_LINES = 300


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))          # 行程池(Windows spawn)要能用模組名找回前版
if PRIOR_PATH.stem in sys.modules:
    PRIOR = sys.modules[PRIOR_PATH.stem]
else:
    _spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem, PRIOR_PATH)
    PRIOR = importlib.util.module_from_spec(_spec)
    sys.modules[PRIOR_PATH.stem] = PRIOR
    _spec.loader.exec_module(PRIOR)
BASE_VERSION = PRIOR.VERSION
PRIOR.VERSION = BASE_VERSION + "+" + TAIL   # 新版號進 project_key → 新基線,不和 v0101 的帳混算


def __getattr__(name):
    return getattr(PRIOR, name)


# ─────────────────────────── ① 範圍 ───────────────────────────
SCOPE = {"files": None}       # None = 不限;set = 只看這些相對路徑


def git_changed(root: Path, ref: str) -> set:
    """git diff <ref> 的名字 + 未追蹤檔(相對 root;--literal-pathspecs)。參照不存在就報錯,不默默放大範圍。"""
    def run(*a):
        p = subprocess.run(["git", "--literal-pathspecs", "-C", str(root), *a], capture_output=True, stdin=subprocess.DEVNULL, timeout=60)
        if p.returncode:
            raise ValueError("git %s 失敗(rc=%d):參照 %r 不存在或不是 git 倉" % (a[0], p.returncode, ref))
        return p.stdout
    top = Path(os.fsdecode(run("rev-parse", "--show-toplevel")).strip()).resolve()
    names = run("diff", "--name-only", "-z", "--diff-filter=ACMR", ref, "--", ".").split(b"\0")
    names += run("ls-files", "--others", "--exclude-standard", "-z", "--", ".").split(b"\0")
    out = set()
    for raw in names:
        if not raw:
            continue
        path = Path(os.fsdecode(raw))
        absolute = (top / path) if not path.is_absolute() else path
        if not absolute.exists():
            absolute = root / path          # ls-files 在子夾給的是相對 cwd
        try:
            out.add(absolute.resolve().relative_to(root.resolve()).as_posix())
        except ValueError:
            continue
    return out


_PREV_INVENTORY = PRIOR.inventory
_PREV_CHECKED = PRIOR.checked_manifest


def inventory(root, conf):
    names = _PREV_INVENTORY(root, conf)
    if SCOPE["files"] is None:
        return names
    return [n for n in names if n in SCOPE["files"]]


def checked_manifest(root):
    conf = _PREV_CHECKED(root)
    if SCOPE["files"] is not None and conf.get("api_contracts"):
        conf = dict(conf)
        conf["api_contracts"] = {k: v for k, v in conf["api_contracts"].items() if k in SCOPE["files"]}
    return conf


PRIOR.inventory = inventory
PRIOR.checked_manifest = checked_manifest


# ─────────────────────────── ② 快取 ───────────────────────────
_PREV_INSPECT = PRIOR.inspect_file


def _policy_key(conf, rel) -> str:
    keep = {k: conf.get(k) for k in ("static_guard_rules", "subsystems")}
    keep["contract"] = conf.get("api_contracts", {}).get(rel)
    return hashlib.sha256(PRIOR.json_bytes([PRIOR.VERSION, PRIOR.RULES, keep, rel])).hexdigest()


def cached_inspect(root, conf, rel):
    """同 v0101 inspect_file;多一層內容快取(位置由環境變數 VIA_PG_CACHE 帶,行程池子行程也看得到)。"""
    cache = os.environ.get("VIA_PG_CACHE")
    if not cache:
        return _PREV_INSPECT(root, conf, rel)
    try:
        raw = PRIOR.read_limited(PRIOR.within(root, rel))
    except (ValueError, OSError):
        return _PREV_INSPECT(root, conf, rel)
    key = hashlib.sha256(raw).hexdigest() + "-" + _policy_key(conf, rel)[:24]
    hit = Path(cache) / key[:2] / (key + ".json")
    if hit.is_file():
        try:
            row = json.loads(hit.read_text(encoding="utf-8"))
            if row.get("sha256") == hashlib.sha256(raw).hexdigest():
                return row
        except (OSError, ValueError):
            pass
    row = PRIOR.inspect_bytes(raw, rel, conf)
    try:
        PRIOR.atomic_write(hit, PRIOR.json_bytes(row))
    except OSError:
        pass
    return row


PRIOR.inspect_file = cached_inspect


# ─────────────────────────── ④ 工具層 ───────────────────────────
_QUOTED = re.compile(r"(['\"])(.*?)\1")


SENSITIVE_TOOLS = {"bandit", "detect-secrets", "via-governance", "codespell"}


def clean(msg: str, limit: int = 140, keep_names: bool = True) -> str:
    """只留第一行;引號裡不像程式名字的內容(可能是資料 / 密碼)遮成「…」。安全類工具的引號內容一律遮。"""
    first = (msg or "").strip().splitlines()[0] if (msg or "").strip() else ""
    keep = (lambda v: bool(re.fullmatch(r"[A-Za-z_][\w.]{0,39}", v))) if keep_names else (lambda v: False)
    first = _QUOTED.sub(lambda m: m.group(0) if keep(m.group(2)) else m.group(1) + "…" + m.group(1), first)
    return first[:limit]


def finding(tool, rule, level, file, line, msg=""):
    return {"tool": tool, "rule": str(rule), "level": level, "file": file, "line": int(line or 0),
            "msg": clean(msg, keep_names=tool not in SENSITIVE_TOOLS)}


def _run(cmd, cwd, timeout, env=None):
    e = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8", NO_COLOR="1")
    if env:
        e.update(env)
    try:
        p = subprocess.run(cmd, cwd=str(cwd), capture_output=True, stdin=subprocess.DEVNULL, timeout=timeout, env=e)
    except FileNotFoundError:
        return None, "", ""
    except subprocess.TimeoutExpired:
        return "TIMEOUT", "", ""
    return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")


def _has_module(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):
        return False


def _chunks(seq, n=CHUNK):
    seq = list(seq)
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def _rel(root: Path, name: str) -> str:
    p = Path(name)
    if not p.is_absolute():
        p = root / p
    try:
        return p.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return Path(name).as_posix()


class Tool:
    """一個在地工具:探測(有沒有裝)· 跑 · 把輸出整理成統一的 finding。"""
    name = ""
    kind = "py"          # py · yaml · ps · any
    heavy = False
    module = None        # python -m <module>
    exe = None           # PATH 上的執行檔
    pip = None           # 安裝提示(只經 VCGC 安裝閘)

    def command(self):
        if self.module and _has_module(self.module):
            return [sys.executable, "-m", self.module]
        if self.exe and shutil.which(self.exe):
            return [shutil.which(self.exe)]
        return None

    def available(self):
        return self.command() is not None

    def run(self, root, files, timeout):
        raise NotImplementedError


class Ruff(Tool):
    name, module, exe, pip = "ruff", "ruff", "ruff", "ruff"
    RED = {"E999", "F821", "F822", "F823", "F632", "F701", "F702", "F704", "F706", "F707", "PLE0101", "PLE0116", "PLE0117"}

    def _cfg(self, root):
        own = (root / "ruff.toml").is_file() or (root / ".ruff.toml").is_file() or (
            (root / "pyproject.toml").is_file() and "[tool.ruff" in (root / "pyproject.toml").read_text(encoding="utf-8", errors="replace"))
        return [] if own else ["--isolated"]

    def run(self, root, files, timeout):
        cmd, out = self.command(), []
        for part in _chunks(files):
            rc, so, _ = _run(cmd + ["check", "--output-format", "json", "--no-cache", "--exit-zero"] + self._cfg(root) + ["--"] + part, root, timeout)
            if rc in (None, "TIMEOUT"):
                return out, rc
            for item in json.loads(so or "[]"):
                code = item.get("code") or "ruff"
                lvl = "RED" if code in self.RED or code.startswith("E9") else "YELLOW"
                out.append(finding("ruff", code, lvl, _rel(root, item.get("filename", "")), (item.get("location") or {}).get("row"), item.get("message")))
            rc, so, _ = _run(cmd + ["format", "--check", "--no-cache"] + self._cfg(root) + ["--"] + part, root, timeout)
            for line in (so or "").splitlines():
                m = re.match(r"Would reformat:\s+(.+)$", line.strip())
                if m:
                    out.append(finding("ruff", "format-drift", "INFO", _rel(root, m.group(1)), 0, "ruff format would reformat"))
        return out, 0


class Mypy(Tool):
    name, module, exe, pip, heavy = "mypy", "mypy", "mypy", "mypy", True

    def run(self, root, files, timeout):
        cmd, out = self.command(), []
        cache = Path(tempfile.gettempdir()) / "VIA_PanoramaGuard_mypy"
        for part in _chunks(files):
            rc, so, _ = _run(cmd + ["--no-error-summary", "--show-error-codes", "--hide-error-context", "--no-color-output",
                                    "--ignore-missing-imports", "--follow-imports=silent", "--cache-dir", str(cache), "--"] + part, root, timeout)
            if rc in (None, "TIMEOUT"):
                return out, rc
            for line in so.splitlines():
                m = re.match(r"^(.+?):(\d+): (error|note): (.*?)(?:\s+\[([\w-]+)\])?$", line)
                if m and m.group(3) == "error":
                    out.append(finding("mypy", m.group(5) or "error", "RED" if m.group(5) == "syntax" else "YELLOW", _rel(root, m.group(1)), m.group(2), m.group(4)))
        return out, 0


class Pyright(Tool):
    name, exe, pip, heavy = "pyright", "pyright", "pyright(要 Node.js)", True
    RED = {"reportUndefinedVariable", "reportSyntaxError"}

    def run(self, root, files, timeout):
        cmd, out = self.command(), []
        for part in _chunks(files):
            rc, so, _ = _run(cmd + ["--outputjson"] + part, root, timeout)
            if rc in (None, "TIMEOUT"):
                return out, rc
            try:
                data = json.loads(so or "{}")
            except ValueError:
                return out, "ERROR"
            for d in data.get("generalDiagnostics", []):
                if d.get("severity") != "error":
                    continue
                rule = d.get("rule") or "error"
                out.append(finding("pyright", rule, "RED" if rule in self.RED else "YELLOW", _rel(root, d.get("file", "")),
                                   ((d.get("range") or {}).get("start") or {}).get("line", -1) + 1, d.get("message")))
        return out, 0


class Bandit(Tool):
    name, module, pip = "bandit", "bandit", "bandit"
    LV = {"HIGH": "RED", "MEDIUM": "YELLOW", "LOW": "INFO"}

    def run(self, root, files, timeout):
        cmd, out = self.command(), []
        for part in _chunks(files):
            rc, so, _ = _run(cmd + ["-q", "-f", "json"] + part, root, timeout)
            if rc in (None, "TIMEOUT"):
                return out, rc
            try:
                data = json.loads(so or "{}")
            except ValueError:
                return out, "ERROR"
            for r in data.get("results", []):
                out.append(finding("bandit", r.get("test_id"), self.LV.get(r.get("issue_severity"), "YELLOW"), _rel(root, r.get("filename", "")),
                                   r.get("line_number"), r.get("issue_text")))
        return out, 0


class DetectSecrets(Tool):
    name, module, pip = "detect-secrets", "detect_secrets", "detect-secrets"
    kind = "any"

    def run(self, root, files, timeout):
        cmd, out = self.command(), []
        for part in _chunks(files):
            rc, so, _ = _run(cmd + ["scan"] + part, root, timeout)
            if rc in (None, "TIMEOUT"):
                return out, rc
            try:
                data = json.loads(so or "{}")
            except ValueError:
                return out, "ERROR"
            for fname, hits in (data.get("results") or {}).items():
                for h in hits:   # 不帶 hashed_secret,只留種類與行號
                    out.append(finding("detect-secrets", h.get("type", "secret"), "RED", _rel(root, fname), h.get("line_number"), "possible secret"))
        return out, 0


class Vulture(Tool):
    name, module, pip = "vulture", "vulture", "vulture"

    def run(self, root, files, timeout):
        cmd, out = self.command(), []
        for part in _chunks(files):
            rc, so, _ = _run(cmd + ["--min-confidence", "80"] + part, root, timeout)
            if rc in (None, "TIMEOUT"):
                return out, rc
            for line in so.splitlines():
                m = re.match(r"^(.+?):(\d+): (.+?) \((\d+)% confidence\)", line)
                if m:
                    out.append(finding("vulture", "dead-code", "INFO" if int(m.group(4)) < 100 else "YELLOW", _rel(root, m.group(1)), m.group(2), m.group(3)))
        return out, 0


class Radon(Tool):
    name, module, pip = "radon", "radon", "radon"

    def run(self, root, files, timeout):
        cmd, out = self.command(), []
        for part in _chunks(files):
            rc, so, _ = _run(cmd + ["cc", "-j", "-n", "D"] + part, root, timeout)
            if rc in (None, "TIMEOUT"):
                return out, rc
            try:
                data = json.loads(so or "{}")
            except ValueError:
                return out, "ERROR"
            for fname, blocks in data.items():
                if not isinstance(blocks, list):
                    continue
                for b in blocks:
                    rank = b.get("rank", "")
                    out.append(finding("radon", "complexity-" + rank, "YELLOW", _rel(root, fname), b.get("lineno"),   # 複雜度是維護風險,不是壞掉 → 最多黃
                                       "%s complexity %s" % (b.get("name", ""), b.get("complexity"))))
        return out, 0


class Lizard(Tool):
    name, module, pip, heavy = "lizard", "lizard", "lizard", True
    kind = "any"

    def run(self, root, files, timeout):
        cmd, out = self.command(), []
        for part in _chunks(files):
            rc, so, _ = _run(cmd + ["--csv"] + part, root, timeout)
            if rc in (None, "TIMEOUT"):
                return out, rc
            for cols in __import__("csv").reader(so.splitlines()):
                if len(cols) < 11 or not cols[0].isdigit():
                    continue
                nloc, params, fname, func, start = int(cols[0]), int(cols[3]), cols[6], cols[7], cols[9]
                if nloc > 200:
                    out.append(finding("lizard", "long-function", "YELLOW", _rel(root, fname), start, "%s nloc %d" % (func, nloc)))
                if params > 8:
                    out.append(finding("lizard", "too-many-params", "INFO", _rel(root, fname), start, "%s params %d" % (func, params)))
        return out, 0


class PylintDup(Tool):
    name, module, pip, heavy = "pylint-duplicate", "pylint", "pylint", True

    def run(self, root, files, timeout):
        if len(files) < 2:
            return [], "NA"
        rc, so, _ = _run(self.command() + ["--disable=all", "--enable=duplicate-code", "--min-similarity-lines=12",
                                           "--output-format=json", "--score=n"] + list(files), root, timeout)
        if rc in (None, "TIMEOUT"):
            return [], rc
        try:
            data = json.loads(so or "[]")
        except ValueError:
            return [], "ERROR"
        return [finding("pylint", "duplicate-code", "INFO", _rel(root, d.get("path", "")), d.get("line"), d.get("message")) for d in data], 0


class Interrogate(Tool):
    name, module, pip = "interrogate", "interrogate", "interrogate"
    THRESHOLD = 50.0

    def run(self, root, files, timeout):
        rc, so, se = _run(self.command() + ["--fail-under", "0"] + list(files)[:2000], root, timeout)
        if rc in (None, "TIMEOUT"):
            return [], rc
        m = re.search(r"actual:\s*([\d.]+)%", so + se)
        if not m:
            return [], "ERROR"
        pct = float(m.group(1))
        return ([finding("interrogate", "docstring-coverage", "YELLOW" if pct < self.THRESHOLD else "INFO", "*", 0, "docstring coverage %.1f%%" % pct)], 0)


class Codespell(Tool):
    name, module, exe, pip = "codespell", "codespell_lib", "codespell", "codespell"
    kind = "any"

    def run(self, root, files, timeout):
        out = []
        for part in _chunks(files):
            rc, so, _ = _run(self.command() + ["--quiet-level", "2"] + part, root, timeout)
            if rc in (None, "TIMEOUT"):
                return out, rc
            for line in so.splitlines():
                m = re.match(r"^(.+?):(\d+): (.+)$", line)
                if m:
                    out.append(finding("codespell", "typo", "INFO", _rel(root, m.group(1)), m.group(2), m.group(3)))
        return out, 0


class Deptry(Tool):
    name, module, pip = "deptry", "deptry", "deptry"
    LV = {"DEP001": "YELLOW", "DEP002": "INFO", "DEP003": "INFO", "DEP004": "INFO"}

    def run(self, root, files, timeout):
        if not any((root / n).is_file() for n in ("pyproject.toml", "requirements.txt", "setup.py", "setup.cfg")):
            return [], "NA"
        with tempfile.TemporaryDirectory(prefix="pg_deptry_") as td:
            js = Path(td) / "d.json"
            rc, so, se = _run(self.command() + [".", "--json-output", str(js)], root, timeout)
            if rc in (None, "TIMEOUT"):
                return [], rc
            if not js.is_file():
                return [], "ERROR"
            data = json.loads(js.read_text(encoding="utf-8") or "[]")
        declared = (root / "pyproject.toml").is_file() and "[project]" in (root / "pyproject.toml").read_text(encoding="utf-8", errors="replace")
        scope = set(files)
        out = []
        for d in data:
            code = (d.get("error") or {}).get("code", "DEP")
            loc = d.get("location") or {}
            rel = _rel(root, loc.get("file") or "*")
            if rel not in scope and rel != "*":
                continue        # deptry 看整個專案;只留範圍內的檔
            lvl = self.LV.get(code, "INFO") if declared else "INFO"   # 沒有 [project] 依賴宣告 = 只當參考
            out.append(finding("deptry", code, lvl, rel, loc.get("line"), (d.get("error") or {}).get("message")))
        return out, 0


class PipCheck(Tool):
    name, pip = "pip-check", "(pip 內建)"
    kind = "env"

    def command(self):
        return [sys.executable, "-m", "pip"]

    def run(self, root, files, timeout):
        rc, so, se = _run(self.command() + ["check"], root, timeout)
        if rc in (None, "TIMEOUT"):
            return [], rc
        lines = [x for x in (so or "").splitlines() if x.strip() and "No broken requirements" not in x]
        return [finding("pip-check", "broken-requirement", "YELLOW", "*", 0, x) for x in lines], 0


class Yamllint(Tool):
    name, module, pip = "yamllint", "yamllint", "yamllint"
    kind = "yaml"

    def run(self, root, files, timeout):
        out = []
        for part in _chunks(files):
            rc, so, _ = _run(self.command() + ["-f", "parsable", "-d", "{extends: relaxed}"] + part, root, timeout)
            if rc in (None, "TIMEOUT"):
                return out, rc
            for line in so.splitlines():
                m = re.match(r"^(.+?):(\d+):\d+: \[(error|warning)\] (.*?)(?: \(([\w-]+)\))?$", line)
                if m:
                    rule = m.group(5) or m.group(3)
                    lvl = "RED" if rule == "syntax" else ("YELLOW" if m.group(3) == "error" else "INFO")
                    out.append(finding("yamllint", rule, lvl, _rel(root, m.group(1)), m.group(2), m.group(4)))
        return out, 0


_PS_SCRIPT = r"""
param([string]$ListFile)
$ErrorActionPreference = 'Continue'
$hasPssa = $null -ne (Get-Module -ListAvailable -Name PSScriptAnalyzer)
$out = foreach ($f in (Get-Content -LiteralPath $ListFile -Encoding UTF8)) {
  $t = $null; $e = $null
  [void][System.Management.Automation.Language.Parser]::ParseFile($f, [ref]$t, [ref]$e)
  foreach ($x in $e) { [pscustomobject]@{ file = $f; line = $x.Extent.StartLineNumber; rule = 'ps-syntax'; sev = 'Error'; msg = $x.ErrorId } }
  if ($hasPssa -and -not $e) {
    foreach ($r in (Invoke-ScriptAnalyzer -LiteralPath $f -Severity Error,Warning)) {
      [pscustomobject]@{ file = $f; line = $r.Line; rule = $r.RuleName; sev = [string]$r.Severity; msg = $r.RuleName }
    }
  }
}
[pscustomobject]@{ pssa = $hasPssa; items = @($out) } | ConvertTo-Json -Depth 4 -Compress
"""


def ps_param_first(text: str):
    """回 None(合規或沒有腳本層 param)或違規行號:param() 前只准註解、#Requires、using、[屬性]。"""
    lines = text.splitlines()
    in_block = False
    first = None
    for i, raw in enumerate(lines, 1):
        s = raw.strip()
        if in_block:
            if "#>" in s:
                in_block = False
            continue
        if s.startswith("<#"):
            in_block = "#>" not in s[2:]
            continue
        if not s or s.startswith("#") or s.lower().startswith("using ") or re.match(r"^\[[\w.]+(\(.*\))?\]$", s):
            continue
        first = (i, s)
        break
    if first is None:
        return None
    has_param = any(re.match(r"^param\s*\(", ln, re.I) for ln in lines)
    if not has_param:
        return None
    return None if re.match(r"^param\s*\(", first[1], re.I) else first[0]


class PSScriptAnalyzer(Tool):
    name, exe, pip = "psscriptanalyzer", "pwsh", "Install-Module PSScriptAnalyzer(PowerShell 7)"
    kind = "ps"

    def available(self):
        return True     # 內建的 param 檢查一定跑;pwsh / tree-sitter 有就加深

    def run(self, root, files, timeout):
        out, mode = [], "builtin"
        for f in files:
            text = (root / f).read_text(encoding="utf-8-sig", errors="replace")
            bad = ps_param_first(text)
            if bad:
                out.append(finding("psscriptanalyzer", "ps-param-not-first", "RED", f, bad, "param() must be the first executable statement"))
        pwsh = shutil.which("pwsh")
        if pwsh:
            with tempfile.TemporaryDirectory(prefix="pg_ps_") as td:
                lst, scr = Path(td) / "files.txt", Path(td) / "pg.ps1"
                lst.write_text("\n".join(str((root / f).resolve()) for f in files), encoding="utf-8")
                scr.write_text(_PS_SCRIPT, encoding="utf-8")
                rc, so, _ = _run([pwsh, "-NoProfile", "-NonInteractive", "-File", str(scr), "-ListFile", str(lst)], root, timeout)
            if rc not in (None, "TIMEOUT"):
                try:
                    data = json.loads(so.strip().splitlines()[-1]) if so.strip() else {}
                except (ValueError, IndexError):
                    data = {}
                mode = "pssa" if data.get("pssa") else "pwsh-parser"
                items = data.get("items") or []
                for it in items if isinstance(items, list) else [items]:
                    lvl = "RED" if it.get("rule") == "ps-syntax" or it.get("sev") == "Error" else "YELLOW"
                    out.append(finding("psscriptanalyzer", it.get("rule"), lvl, _rel(root, it.get("file", "")), it.get("line"), it.get("msg")))
                return out, 0, mode
        try:
            import tree_sitter_powershell as tsp
            from tree_sitter import Language, Parser
            parser = Parser(Language(tsp.language()))
            for f in files:
                tree = parser.parse((root / f).read_bytes())
                stack = [tree.root_node]
                while stack:
                    n = stack.pop()
                    if n.type == "ERROR" or n.is_missing:
                        out.append(finding("psscriptanalyzer", "ps-syntax", "RED", f, n.start_point[0] + 1, "tree-sitter parse error"))
                        break
                    stack.extend(n.children)
            mode = "tree-sitter"
        except ImportError:
            pass
        return out, 0, mode


TOOLS = [Ruff(), Mypy(), Pyright(), Bandit(), DetectSecrets(), Vulture(), Radon(), Lizard(), PylintDup(), Interrogate(),
         Codespell(), Deptry(), PipCheck(), Yamllint(), PSScriptAnalyzer()]
TOOL_NAMES = [t.name for t in TOOLS]


def other_files(root: Path, conf: dict, exts) -> list:
    """非 Python 檔(YAML / PowerShell / JSON)盤點:同 v0101 的略過與排除規則,也守範圍。"""
    patterns = conf.get("exclude_patterns", [])
    hits = []
    for folder, dirs, files in os.walk(root, followlinks=False):
        base = Path(folder)
        dirs[:] = sorted(d for d in dirs if d.lower() not in PRIOR.SKIP and not PRIOR.is_link(base / d))
        for name in files:
            if Path(name).suffix.lower() in exts:
                rel = (base / name).relative_to(root).as_posix()
                if any(__import__("fnmatch").fnmatchcase(rel, p) for p in patterns):
                    continue
                if SCOPE["files"] is not None and rel not in SCOPE["files"]:
                    continue
                hits.append(rel)
    return sorted(hits)


def json_syntax(root, files):
    out = []
    for f in files:
        try:
            json.loads((root / f).read_text(encoding="utf-8-sig"))
        except ValueError as e:
            out.append(finding("json", "json-syntax", "RED", f, getattr(e, "lineno", 0), "invalid JSON"))
        except OSError:
            out.append(finding("json", "unreadable", "YELLOW", f, 0, "unreadable"))
    return out


def run_tools(root: Path, py: list, yaml_files: list, ps_files: list, json_files: list, select, timeout: int) -> dict:
    """逐工具平行跑;回 {工具: {status, lamp, findings, version…}}。沒裝 = ABSENT(灰)· 不適用 = NA(灰)· 太大略過 = SKIPPED(灰)。"""
    plan = {}
    for t in TOOLS:
        if select is not None and t.name not in select:
            plan[t.name] = ("OFF", t, [])
            continue
        files = {"py": py, "any": py + yaml_files + ps_files, "yaml": yaml_files, "ps": ps_files, "env": ["*"]}[t.kind]
        if not files:
            plan[t.name] = ("NA", t, [])
        elif not t.available():
            plan[t.name] = ("ABSENT", t, [])
        elif t.heavy and select is None and len(py) > HEAVY_LIMIT:
            plan[t.name] = ("SKIPPED", t, [])
        else:
            plan[t.name] = ("RUN", t, files)
    results = {}

    total = sum(1 for v in plan.values() if v[0] == "RUN")
    done = [0]

    def say(text):
        print("[工具] " + text, file=sys.stderr, flush=True)     # 進度只寫 stderr:主機上看得到在跑,不污染 stdout 的 JSON 卡

    say("開始 %d 個(%s)· 略過:%s" % (total, ", ".join(n for n, v in plan.items() if v[0] == "RUN") or "—",
                                  ", ".join("%s=%s" % (n, v[0]) for n, v in plan.items() if v[0] != "RUN") or "—"))

    def go(name):
        state, t, files = plan[name]
        start = time.time()
        if state == "RUN":
            say("%s 開始 · %d 檔" % (name, len(files)))
        if state != "RUN":
            return name, {"status": state, "lamp": "GRAY", "findings": [], "install": t.pip, "seconds": 0}
        try:
            res = t.run(root, files if t.kind != "env" else [], timeout)
        except (OSError, ValueError, subprocess.SubprocessError) as e:
            return name, {"status": "ERROR", "lamp": "YELLOW", "findings": [], "error": type(e).__name__, "seconds": round(time.time() - start, 1)}
        found, rc = res[0], res[1]
        extra = {"mode": res[2]} if len(res) > 2 else {}
        status = {0: "OK", "NA": "NA", "TIMEOUT": "TIMEOUT", "ERROR": "ERROR", None: "ABSENT"}.get(rc, "OK")
        lv = {f["level"] for f in found}
        lamp = "GRAY" if status in ("NA", "ABSENT") else "RED" if "RED" in lv else "YELLOW" if ("YELLOW" in lv or status in ("TIMEOUT", "ERROR")) else "GREEN"
        done[0] += 1
        say("%s %s · %d 件 · %.1f 秒 · 完成 %d/%d" % (name, lamp, len(found), time.time() - start, done[0], total))
        return name, dict(status=status, lamp=lamp, findings=found, seconds=round(time.time() - start, 1), files=len(files), **extra)

    workers = max(1, min(4, os.cpu_count() or 1))
    with cf.ThreadPoolExecutor(max_workers=workers) as pool:
        for name, res in pool.map(go, list(plan)):
            results[name] = res
    return results


# ─────────────────────────── ⑥ 治理剖面 ───────────────────────────
NET_MODS = {"requests", "urllib.request", "httpx", "aiohttp", "yfinance", "akshare", "twstock", "selenium", "playwright"}


def is_via(root: Path) -> bool:
    return any((r / "supportive modules/registry/VIA_ToolVersion_Lock_v0100.json").is_file() for r in (root, root / "VeritasIntelligenceAnalytics"))


def via_governance(root: Path, py: list, ps_files: list) -> list:
    """VIA 剖面:加速器橋 · 網路橋 · 禁 TA-Lib · 不准程式寫同意閘 · PS 加速橋。只讀,只報位置。"""
    out = []
    for f in py:
        if PRIOR.frozen(f) or Path(f).name.startswith(("VeritasCeleritas", "VeritasAegisNexus", "VIA_SuperAccel")):
            continue
        try:
            raw = PRIOR.read_limited(root / f)
            text, _ = PRIOR.decode(raw)
            tree = ast.parse(text)
        except (ValueError, OSError, SyntaxError, UnicodeError, LookupError, RecursionError):
            continue
        mods = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                mods.update(a.name for a in n.names)
            elif isinstance(n, ast.ImportFrom) and n.module and not n.level:
                mods.add(n.module)
        if any(m == "talib" or m.startswith("talib.") for m in mods):
            out.append(finding("via-governance", "talib-forbidden", "RED", f, 1, "TA-Lib is banned in VIA"))
        if "[VIA:ACCEL-BRIDGE" not in text:
            out.append(finding("via-governance", "accel-bridge-missing", "YELLOW", f, 1, "no [VIA:ACCEL-BRIDGE] marker"))
        if any(m in NET_MODS or m.split(".")[0] in NET_MODS for m in mods) and "[VIA:NET-BRIDGE" not in text:
            out.append(finding("via-governance", "net-bridge-missing", "YELLOW", f, 1, "network import without [VIA:NET-BRIDGE] marker"))
        for m in re.finditer(r"environ\[\s*[\"']VIA_(?:NET|SCRAPE)_CONSENT[\"']\s*\]\s*=(?!=)", text):
            out.append(finding("via-governance", "consent-written-by-code", "RED", f, text.count("\n", 0, m.start()) + 1, "code sets a consent gate"))
    for f in ps_files:
        try:
            text = (root / f).read_text(encoding="utf-8-sig", errors="replace")
        except OSError:
            continue
        if "[VIA:PS-ACCEL" not in text and "CELERITAS-TEMPLATE-JOIN" not in text:
            out.append(finding("via-governance", "ps-accel-missing", "YELLOW", f, 1, "no PS accelerator marker"))
    return out


# ─────────────────────────── ⑤ 工具輔助修復 ───────────────────────────
def tool_fix(root: Path, run_dir: Path, report: dict, conf: dict, project_tests: bool, suites, timeout: int) -> dict:
    """ruff safe 修正只改在覆層副本;逐檔 compile + 不新增本引擎紅 + ruff 件數下降才收;專案測試前後再比一次,不過全退。"""
    ruff = Ruff()
    if not ruff.available():
        return {"status": "ABSENT", "accepted": 0}
    overlay = run_dir / "overlay"
    accepted, rejected, backups = [], [], {}
    for rel, row in report["files"].items():
        if PRIOR.frozen(rel) or "exact" not in row:
            continue
        src = overlay / rel if (overlay / rel).is_file() else root / rel
        with tempfile.TemporaryDirectory(prefix="pg_fix_") as td:
            tmp = Path(td) / Path(rel).name
            raw = PRIOR.read_limited(src)
            tmp.write_bytes(raw)
            before = ruff.run(Path(td), [tmp.name], timeout)[0]
            if not [x for x in before if x["rule"] != "format-drift"]:
                continue
            _run(ruff.command() + ["check", "--fix", "--no-cache", "--exit-zero"] + ruff._cfg(root) + ["--", tmp.name], td, timeout)
            fixed = tmp.read_bytes()
            if fixed == raw:
                continue
            after = ruff.run(Path(td), [tmp.name], timeout)[0]
        try:
            compile(fixed, rel, "exec", dont_inherit=True)
            check = PRIOR.inspect_bytes(fixed, rel, conf)
        except (SyntaxError, ValueError):
            rejected.append([rel, "compile"])
            continue
        if PRIOR.reds({rel: check}) - PRIOR.reds({rel: row}) or len(after) >= len(before):
            rejected.append([rel, "no_gain_or_new_red"])
            continue
        target = overlay / rel
        backups[rel] = target.read_bytes() if target.is_file() else None
        PRIOR.atomic_write(target, fixed)
        accepted.append(rel)
    status = "PASS"
    if accepted and project_tests:
        with tempfile.TemporaryDirectory(prefix="pg_fixtest_") as td:
            _, status = PRIOR.compare_project_tests(root, overlay, Path(td), suites=suites)
        if status != "PASS":
            for rel, old in backups.items():
                if old is None:
                    (overlay / rel).unlink(missing_ok=True)
                else:
                    PRIOR.atomic_write(overlay / rel, old)
            rejected += [[r, "project_tests_" + status] for r in accepted]
            accepted = []
    return {"status": status, "accepted": len(accepted), "files": accepted, "rejected": rejected}


# ─────────────────────────── ⑦ 產出 ───────────────────────────
def lamp_css(root: Path) -> str:
    for r in (root, root / "VeritasIntelligenceAnalytics"):
        hits = sorted((r / "supportive modules/registry").glob("VIA_UI_FormatLock_v*.json")) if (r / "supportive modules/registry").is_dir() else []
        if hits:
            try:
                css = json.loads(hits[-1].read_text(encoding="utf-8")).get("lamp_css")
                if css:
                    return css
            except (OSError, ValueError):
                pass
    # 沒有 VIA 鎖冊(其他專案)時的預設:與 VIA_UI_FormatLock 同值
    return ("@keyframes via-blink{0%,100%{opacity:1}50%{opacity:.25}}.lamp{display:inline-block;width:12px;height:12px;border-radius:50%;"
            "vertical-align:middle;margin-right:4px;border:1px solid rgba(0,0,0,.15)}.lamp.GREEN{background:#16a34a}.lamp.YELLOW{background:#f59e0b}"
            ".lamp.RED{background:#dc2626;animation:via-blink 1.8s ease-in-out infinite}.lamp.GRAY{background:#9ca3af}"
            "@media (prefers-reduced-motion: reduce){.lamp.RED{animation:none}}")


def tools_page(root: Path, summary: dict, tools: dict, gov: list) -> str:
    esc = PRIOR.html.escape
    rows = []
    for name, r in tools.items():
        by = collections.Counter(f["rule"] for f in r["findings"])
        top = " · ".join("%s %d" % (k, v) for k, v in by.most_common(4))
        rows.append("<tr><td><span class='lamp %s'></span>%s</td><td>%s</td><td>%s</td><td>%d</td><td>%s</td></tr>" % (
            r["lamp"], r["lamp"], esc(name), esc(r["status"] + ("/" + r["mode"] if r.get("mode") else "")), len(r["findings"]),
            esc(top or (("安裝:" + str(r.get("install"))) if r["status"] == "ABSENT" else "—"))))
    gl = "RED" if any(f["level"] == "RED" for f in gov) else "YELLOW" if gov else ("GREEN" if summary.get("profile") == "via" else "GRAY")
    gby = collections.Counter(f["rule"] for f in gov)
    rows.append("<tr><td><span class='lamp %s'></span>%s</td><td>via-governance</td><td>%s</td><td>%d</td><td>%s</td></tr>" % (
        gl, gl, esc(summary.get("profile", "")), len(gov), esc(" · ".join("%s %d" % kv for kv in gby.most_common(4)) or "—")))
    return ("<!doctype html><html lang='zh-Hant'><meta charset='utf-8'><meta name='viewport' content='width=device-width'>"
            "<title>VIA PanoramaGuard · 工具矩陣</title><style>" + lamp_css(root) +
            "body{font:11px/1.35 system-ui,'Segoe UI',sans-serif;background:#f8fafc;color:#0f172a;margin:12px}"
            "table{border-collapse:collapse;width:100%;table-layout:fixed}td,th{padding:3px 6px;border-bottom:1px solid #e2e8f0;"
            "text-align:left;overflow-wrap:anywhere;white-space:normal}th{background:#f1f5f9}td:first-child,th:first-child{width:9em}"
            "h1{font-size:14px;margin:0 0 6px}p{margin:2px 0}</style><h1>全景守衛 · 在地工具矩陣 v" + TAIL + "</h1><p>" +
            esc("%s · 範圍 %s · Python %d 檔 · YAML %d · PS %d · JSON %d · etag %s" % (summary.get("decision_all"), summary.get("scope"),
                summary.get("files", 0), summary.get("yaml_files", 0), summary.get("ps_files", 0), summary.get("json_files", 0), summary.get("etag", ""))) +
            "</p><table><thead><tr><th>燈</th><th>工具</th><th>狀態</th><th>件數</th><th>前幾種規則 / 安裝提示</th></tr></thead><tbody>" +
            "".join(rows) + "</tbody></table></html>")


def sarif(report: dict, tools: dict, gov: list) -> dict:
    lvl = {"RED": "error", "YELLOW": "warning", "INFO": "note"}
    runs = []
    eng = [{"ruleId": i["rule"], "level": lvl.get(i["level"], "note"), "message": {"text": "%s AST-OP-%s" % (i["rule"], i["op"])},
            "locations": [{"physicalLocation": {"artifactLocation": {"uri": p}, "region": {"startLine": max(1, i["line"] or 1)}}}]}
           for p, r in report["files"].items() for i in r["issues"]]
    runs.append({"tool": {"driver": {"name": "VIA_PanoramaGuard", "version": TAIL, "rules": [{"id": x} for x in sorted({e["ruleId"] for e in eng})]}}, "results": eng})
    for name, r in list(tools.items()) + [("via-governance", {"findings": gov})]:
        res = [{"ruleId": f["rule"], "level": lvl.get(f["level"], "note"), "message": {"text": f["msg"] or f["rule"]},
                "locations": [{"physicalLocation": {"artifactLocation": {"uri": f["file"]}, "region": {"startLine": max(1, f["line"] or 1)}}}]}
               for f in r["findings"]]
        if res:
            runs.append({"tool": {"driver": {"name": name, "rules": [{"id": x} for x in sorted({e["ruleId"] for e in res})]}}, "results": res})
    return {"$schema": "https://json.schemastore.org/sarif-2.1.0.json", "version": "2.1.0", "runs": runs}


def pastepack(report: dict, tools: dict, gov: list, summary: dict, limit: int = PASTE_LINES) -> str:
    """只黃紅、去雜訊、≤limit 行、以 NEXT: 結尾(VIA 動詞迴圈的貼回包形狀)。"""
    head = ["# VIA_PanoramaGuard v%s 貼回包 · %s" % (TAIL, summary.get("utc", "")[:19]),
            "[總判] %s · 引擎 %s → %s · 範圍 %s · etag %s" % (summary.get("decision_all"), summary.get("before"), summary.get("after"), summary.get("scope"), summary.get("etag")),
            "[工具] " + " · ".join("%s %s%s" % (n, r["lamp"], "(%d)" % len(r["findings"]) if r["findings"] else "") for n, r in tools.items())]
    reds, yellows = [], collections.Counter()
    for p, r in report["files"].items():
        for i in r["issues"]:
            if i["level"] == "RED":
                reds.append("[紅] 引擎 %s:%s %s" % (p, i["line"], i["rule"]))
            elif i["level"] == "YELLOW":
                yellows["引擎 " + i["rule"]] += 1
    for f in [x for r in tools.values() for x in r["findings"]] + gov:
        if f["level"] == "RED":
            reds.append("[紅] %s %s:%s %s %s" % (f["tool"], f["file"], f["line"], f["rule"], f["msg"][:80]))
        elif f["level"] == "YELLOW":
            yellows["%s %s" % (f["tool"], f["rule"])] += 1
    body = ["[紅 %d 件]" % len(reds)] + reds
    body += ["[黃 %d 種 · %d 件(只列種類與件數)]" % (len(yellows), sum(yellows.values()))] + ["[黃] %s × %d" % kv for kv in yellows.most_common()]
    nxt = summary.get("next") or "NEXT: 先看紅"
    room = max(1, limit - len(head) - 1)
    if len(body) > room:
        body = body[:room - 1] + ["… 另 %d 行在 report.json / tools.json(MCP tool_findings 分頁讀)" % (len(body) - room + 1)]
    return "\n".join(head + body + [nxt]) + "\n"


def compute_etag(root: Path, names: list, other: list, argsig: list, select) -> str:
    h = hashlib.sha256()
    h.update(PRIOR.json_bytes([PRIOR.VERSION, argsig, sorted(select) if select else "auto",
                               {t.name: t.available() for t in TOOLS}]))
    mf = root / PRIOR.MANIFEST
    if mf.is_file():
        h.update(mf.read_bytes())
    for rel in list(names) + list(other):
        try:
            h.update(rel.encode() + b"\0" + hashlib.sha256((root / rel).read_bytes()).digest())
        except OSError:
            h.update(rel.encode() + b"\0missing")
    return h.hexdigest()[:16]


def next_line(decision: str, tools: dict, gov: list, rc: int) -> str:
    if decision == "FAIL_STOP":
        return "NEXT: 先處理 blocked(report.json 的 blocked 欄);修復覆層已收回,原檔沒動"
    red_tools = [n for n, r in tools.items() if r["lamp"] == "RED"]
    if red_tools or any(f["level"] == "RED" for f in gov):
        return "NEXT: 先修紅(%s);修完用 --changed-since 只重掃改過的檔" % ", ".join(red_tools + (["via-governance"] if any(f["level"] == "RED" for f in gov) else []))
    if rc == 1:
        return "NEXT: 引擎仍有紅,看 report.json 的紅燈列(AST-OP-500 需人工審)"
    return "NEXT: 無紅;黃燈照種類分批處理,或帶 --if-etag 下次沒變就 304"


# ─────────────────────────── 主流程 ───────────────────────────
def run_all(args) -> int:
    root = Path(args.root).resolve(strict=True)
    out = Path(args.output).resolve()
    select = None if args.tools in ("auto", "all") else ([] if args.tools == "none" else [x.strip() for x in args.tools.split(",") if x.strip()])
    if select:
        bad = sorted(set(select) - set(TOOL_NAMES))
        if bad:
            raise ValueError("不認得的工具:%s(可用:%s)" % (", ".join(bad), ", ".join(TOOL_NAMES)))
    if args.tools == "all":
        select = list(TOOL_NAMES)
    if args.changed_since and args.paths:
        raise ValueError("--changed-since 與 --paths 擇一")
    if getattr(args, "tool_fix", False) and getattr(args, "commit", False):
        raise ValueError("--tool-fix 與 --commit 不能同時用(提交只收本引擎 AST 等價修復)")
    scope_desc = "全部"
    if args.changed_since:
        SCOPE["files"] = git_changed(root, args.changed_since)
        scope_desc = "自 %s 起改過 %d 檔" % (args.changed_since, len(SCOPE["files"]))
    elif args.paths:
        SCOPE["files"] = {PRIOR.within(root, p).relative_to(root).as_posix() for p in args.paths}
        scope_desc = "指定 %d 檔" % len(SCOPE["files"])
    if args.changed_since or args.paths:
        PRIOR.VERSION = BASE_VERSION + "+" + TAIL + "+scoped"   # 範圍掃描另立基線,不污染全樹棘輪
    conf = PRIOR.checked_manifest(root)
    names = PRIOR.inventory(root, conf)
    yaml_f = other_files(root, conf, {".yml", ".yaml"})
    ps_f = other_files(root, conf, {".ps1", ".psm1", ".psd1"})
    json_f = other_files(root, conf, {".json"})
    if not names and not (yaml_f or ps_f or json_f):
        print(json.dumps({"decision": "EMPTY_SCOPE", "scope": scope_desc}, ensure_ascii=False))
        return 0
    profile = args.profile if args.profile != "auto" else ("via" if is_via(root) else "generic")
    argsig = [args.mode, scope_desc, bool(getattr(args, "narrow_except", False)), bool(getattr(args, "draft_docstrings", False)),
              bool(args.project_tests), args.suite, profile, bool(getattr(args, "tool_fix", False))]
    etag = compute_etag(root, names, yaml_f + ps_f + json_f, argsig, select)
    if args.if_etag and args.if_etag == etag and args.mode == "scan":
        print(json.dumps({"decision": "304_NOT_MODIFIED", "etag": etag, "scope": scope_desc,
                          "note": "範圍內檔、規則、工具都沒變;沿用上一輪收據"}, ensure_ascii=False))
        return 0
    if not args.no_cache:
        os.environ["VIA_PG_CACHE"] = str(out / "cache" / "inspect")
    if names:
        rc, run_dir, summary = PRIOR.run_engine(root, out, args.mode, args.workers, getattr(args, "narrow_except", False),
                                                getattr(args, "draft_docstrings", False), args.require_accelerator,
                                                args.project_tests, getattr(args, "commit", False), args.suite)
    else:   # 範圍裡只有非 Python 檔:不跑 AST 引擎,只跑工具
        rc, summary = 0, {"decision": "NO_PYTHON", "before": {}, "after": {}, "utc": datetime.now(timezone.utc).isoformat(), "files": 0}
        run_dir = out / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "-tools")
        run_dir.mkdir(parents=True, exist_ok=True)
        PRIOR.atomic_write(run_dir / "report.json", PRIOR.json_bytes({"summary": summary, "files": {}, "blocked": []}))
        PRIOR.atomic_write(run_dir / "summary.json", PRIOR.json_bytes(summary))
    report = PRIOR.read_json(run_dir / "report.json")
    tools = run_tools(root, names, yaml_f, ps_f, json_f, select, args.tool_timeout)
    tools["json-syntax"] = (lambda fs: {"status": "OK" if json_f else "NA", "findings": fs, "seconds": 0, "files": len(json_f),
                                        "lamp": "GRAY" if not json_f else "RED" if fs else "GREEN"})(json_syntax(root, json_f))
    gov = via_governance(root, names, ps_f) if profile == "via" else []
    fix = None
    if getattr(args, "tool_fix", False) and args.mode == "repair" and summary.get("accepted"):
        fix = tool_fix(root, run_dir, report, conf, args.project_tests, args.suite, args.tool_timeout)
    tool_red = any(r["lamp"] == "RED" for r in tools.values()) or any(f["level"] == "RED" for f in gov)
    tool_yellow = any(r["lamp"] == "YELLOW" for r in tools.values()) or bool(gov)
    decision_all = summary.get("decision") if summary.get("decision") in ("FAIL_STOP", "REVIEW_RED") else (
        "REVIEW_RED" if tool_red else "REVIEW_YELLOW" if (tool_yellow or summary.get("decision") == "REVIEW_YELLOW") else summary.get("decision"))
    rc_all = max(rc, 1 if tool_red and rc == 0 else 0)
    summary.update(engine_tail=TAIL, scope=scope_desc, profile=profile, etag=etag, yaml_files=len(yaml_f), ps_files=len(ps_f),
                   json_files=len(json_f), decision_all=decision_all,
                   tools={n: {"lamp": r["lamp"], "status": r["status"], "count": len(r["findings"]), "seconds": r.get("seconds")} for n, r in tools.items()},
                   governance={"lamp": "RED" if any(f["level"] == "RED" for f in gov) else "YELLOW" if gov else ("GREEN" if profile == "via" else "GRAY"),
                               "count": len(gov)},
                   tool_fix=fix)
    summary["next"] = next_line(summary.get("decision"), tools, gov, rc)
    PRIOR.atomic_write(run_dir / "tools.json", PRIOR.json_bytes({"tools": tools, "governance": gov, "tool_fix": fix}))
    PRIOR.atomic_write(run_dir / "results.sarif", json.dumps(sarif(report, tools, gov), ensure_ascii=False).encode("utf-8"))
    PRIOR.atomic_write(run_dir / "pastepack.txt", pastepack(report, tools, gov, summary, args.paste_lines).encode("utf-8"))
    PRIOR.atomic_write(run_dir / "tools.html", tools_page(root, summary, tools, gov).encode("utf-8"))
    PRIOR.atomic_write(run_dir / "summary.json", PRIOR.json_bytes(summary))
    try:
        with PRIOR.writer_lock(out):
            PRIOR.append_ledger(out, {"event": "TOOLS_PHASE", "accepted": False, "run": summary.get("run"), "utc": datetime.now(timezone.utc).isoformat(),
                                      "project_key": summary.get("project_key"), "scope": summary.get("scope"), "etag": etag,
                                      "decision_all": decision_all, "tools": summary["tools"], "governance": summary["governance"]})
    except OSError:
        pass
    mcp = {"mcpServers": {"VIA_PanoramaGuard": {"command": sys.executable, "args": ["-I", str(Path(__file__).resolve()), "serve", "--run", str(run_dir)]}}}
    card = {k: summary.get(k) for k in ("decision_all", "decision", "scope", "profile", "files", "before", "after", "etag", "next")}
    card.update(receipt=str(run_dir), pastepack=str(run_dir / "pastepack.txt"), tools_page=str(run_dir / "tools.html"),
                sarif=str(run_dir / "results.sarif"), tools={n: v["lamp"] + ("·%d" % v["count"] if v["count"] else "") for n, v in summary["tools"].items()},
                mcp_config=mcp)
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return rc_all


# ─────────────────────────── ⑧ MCP ───────────────────────────
_PREV_MCP_TOOLS = PRIOR.mcp_tools
_PREV_TOOL_RESULT = PRIOR.tool_result


def mcp_tools():
    page = {"type": "object", "properties": {"offset": {"type": "integer", "minimum": 0}, "limit": {"type": "integer", "minimum": 1, "maximum": 50},
                                             "tool": {"type": "string"}}, "additionalProperties": False}
    none = {"type": "object", "properties": {}, "additionalProperties": False}
    return _PREV_MCP_TOOLS() + [
        {"name": "tool_findings", "description": "分頁讀在地工具與治理剖面的發現(只有規則、行號、遮過的訊息)", "inputSchema": page, "annotations": {"readOnlyHint": True}},
        {"name": "pastepack", "description": "≤300 行的黃紅貼回包,以 NEXT: 結尾", "inputSchema": none, "annotations": {"readOnlyHint": True}}]


def tool_result(name, args, run):
    if name == "pastepack" and isinstance(args, dict) and not args:
        p = run / "pastepack.txt"
        if not p.is_file():
            raise ValueError("這份收據沒有貼回包")
        return p.read_text(encoding="utf-8")
    if name == "tool_findings" and isinstance(args, dict) and not (set(args) - {"offset", "limit", "tool"}):
        offset, limit, which = args.get("offset", 0), args.get("limit", 20), args.get("tool")
        if type(offset) is not int or type(limit) is not int or offset < 0 or not 1 <= limit <= 50 or (which is not None and not isinstance(which, str)):
            raise ValueError("無效分頁")
        data = PRIOR.read_json(run / "tools.json")
        rows = [f for r in data["tools"].values() for f in r["findings"]] + data.get("governance", [])
        if which:
            rows = [f for f in rows if f["tool"] == which]
        part = rows[offset:offset + limit + 1]
        return {"items": part[:limit], "next_offset": offset + limit if len(part) > limit else None, "total": len(rows)}
    return _PREV_TOOL_RESULT(name, args, run)


PRIOR.mcp_tools = mcp_tools
PRIOR.tool_result = tool_result


def tools_card() -> int:
    print("[VIA_PanoramaGuard v%s] 在地免費工具 %d 個(沒裝 = 灰燈;裝只經 VCGC 安裝閘,不在這裡裝)" % (TAIL, len(TOOLS)))
    missing = []
    for t in TOOLS:
        ok = t.available()
        cmd = t.command() if not isinstance(t, PSScriptAnalyzer) else ([shutil.which("pwsh")] if shutil.which("pwsh") else None)
        print("  %-18s %-6s %-6s %s" % (t.name, "有" if ok else "沒裝", "重" if t.heavy else "", " ".join(cmd[-2:]) if cmd else t.pip))
        if not ok and t.pip and not t.pip.startswith(("(", "Install-", "pyright")):
            missing.append(t.pip)
    if missing:
        print("  裝法(VIA):via-vcgc run CGC_MDL056_InstallGate " + " ".join(missing))
    return 0


# ─────────────────────────── 自測 ───────────────────────────
def selftest() -> int:
    import unittest
    from unittest import mock

    class Tail(unittest.TestCase):
        def setUp(self):
            self.td = tempfile.TemporaryDirectory()
            self.addCleanup(self.td.cleanup)
            self.root = Path(self.td.name) / "src"
            self.root.mkdir()
            self.out = Path(self.td.name) / "out"
            SCOPE["files"] = None
            PRIOR.VERSION = BASE_VERSION + "+" + TAIL
            self.addCleanup(lambda: SCOPE.update(files=None))
            os.environ.pop("VIA_PG_CACHE", None)
            self.addCleanup(lambda: os.environ.pop("VIA_PG_CACHE", None))

        def put(self, rel, data):
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data if isinstance(data, bytes) else data.encode())
            return p

        def args(self, **kw):
            base = dict(root=str(self.root), output=str(self.out), mode="scan", workers=2, require_accelerator=False, project_tests=False,
                        suite=None, tools="none", tool_timeout=60, changed_since=None, paths=None, if_etag=None, no_cache=False,
                        profile="generic", paste_lines=PASTE_LINES, narrow_except=False, draft_docstrings=False, commit=False, tool_fix=False)
            base.update(kw)
            return argparse.Namespace(**base)

        def quiet(self, a):
            with mock.patch("sys.stdout", new=__import__("io").StringIO()) as so:
                rc = run_all(a)
            return rc, json.loads(so.getvalue())

        def test_T1_changed_since_scope_only_changed_and_untracked(self):
            self.put("a.py", "x = 1\n")
            self.put("b.py", "y = 2\n")
            g = lambda *a: subprocess.run(["git", "-C", str(self.root), *a], capture_output=True, check=True)
            g("init", "-q")
            g("add", ".")
            g("-c", "user.email=t@localhost", "-c", "user.name=T", "commit", "-qm", "base")
            self.put("b.py", "y = 3\n")
            self.put("c.py", "z = 4\n")
            self.assertEqual(git_changed(self.root, "HEAD"), {"b.py", "c.py"})
            rc, card = self.quiet(self.args(changed_since="HEAD"))
            rep = PRIOR.read_json(Path(card["receipt"]) / "report.json")
            self.assertEqual(sorted(rep["files"]), ["b.py", "c.py"])
            with self.assertRaises(ValueError):
                git_changed(self.root, "no-such-ref")

        def test_T2_cache_hit_returns_identical_row(self):
            self.put("m.py", "def f():\n    return 1\n")
            os.environ["VIA_PG_CACHE"] = str(self.out / "c")
            conf = {}
            a = cached_inspect(self.root, conf, "m.py")
            with mock.patch.object(PRIOR, "inspect_bytes", side_effect=AssertionError("should hit cache")):
                b = cached_inspect(self.root, conf, "m.py")
            self.assertEqual(a, b)
            self.put("m.py", "def f():\n    return 2\n")
            c = cached_inspect(self.root, conf, "m.py")
            self.assertNotEqual(a["sha256"], c["sha256"])

        def test_T3_etag_304_and_change_invalidates(self):
            self.put("m.py", "# [AST-ANCHOR: M]\nX = 1\n")
            _, card = self.quiet(self.args())
            rc, again = self.quiet(self.args(if_etag=card["etag"]))
            self.assertEqual(again["decision"], "304_NOT_MODIFIED")
            self.put("m.py", "# [AST-ANCHOR: M]\nX = 2\n")
            _, third = self.quiet(self.args(if_etag=card["etag"]))
            self.assertNotEqual(third.get("decision"), "304_NOT_MODIFIED")

        def test_T4_message_masking(self):
            self.assertEqual(clean("unused import 'os'"), "unused import 'os'")
            self.assertNotIn("hunter2-hunter2-secret", clean("Possible hardcoded password: 'hunter2-hunter2-secret'"))
            self.assertNotIn("hunter2", finding("bandit", "B105", "INFO", "a.py", 1, "Possible hardcoded password: 'hunter2'")["msg"])
            self.assertIn("'os'", finding("vulture", "dead-code", "INFO", "a.py", 1, "unused import 'os'")["msg"])
            self.assertEqual(len(clean("x" * 500)), 140)
            self.assertEqual(clean("line1\nline2 secret"), "line1")

        def test_T5_ps_param_first(self):
            self.assertIsNone(ps_param_first("#Requires -Version 7\n<# help\n#>\n[CmdletBinding()]\nparam([string]$A)\n$x=1\n"))
            self.assertEqual(ps_param_first("$ErrorActionPreference='Stop'\nparam([string]$A)\n"), 1)
            self.assertIsNone(ps_param_first("Write-Host 'no param'\n"))
            self.put("ok.ps1", "param([int]$N)\n$N\n")
            self.put("bad.ps1", "$x = 1\nparam([int]$N)\n")
            found = PSScriptAnalyzer().run(self.root, ["bad.ps1", "ok.ps1"], 60)[0]
            self.assertTrue(any(f["file"] == "bad.ps1" and f["rule"] == "ps-param-not-first" for f in found))
            self.assertFalse(any(f["file"] == "ok.ps1" and f["rule"] == "ps-param-not-first" for f in found))

        def test_T6_absent_tool_is_gray_not_green(self):
            with mock.patch.object(Bandit, "available", return_value=False):
                res = run_tools(self.root, ["x.py"], [], [], [], ["bandit"], 30)
            self.assertEqual((res["bandit"]["status"], res["bandit"]["lamp"]), ("ABSENT", "GRAY"))
            self.assertEqual(res["ruff"]["status"], "OFF")

        def test_T7_via_governance(self):
            self.put("supportive modules/registry/VIA_ToolVersion_Lock_v0100.json", "{}")
            self.put("net.py", "import requests\n")
            self.put("ta.py", "# [VIA:ACCEL-BRIDGE:v0111]\nimport talib\n")
            self.put("gate.py", "# [VIA:ACCEL-BRIDGE:v0111]\nimport os\nos.environ['VIA_NET_" + "CONSENT'] = 'YES'\n")
            self.put("ok.py", "# [VIA:ACCEL-BRIDGE:v0111]\nX = 1\n")
            self.put("run.ps1", "param()\n")
            self.assertTrue(is_via(self.root))
            rules = {(f["file"], f["rule"]) for f in via_governance(self.root, ["net.py", "ta.py", "gate.py", "ok.py"], ["run.ps1"])}
            self.assertTrue({("net.py", "accel-bridge-missing"), ("net.py", "net-bridge-missing"), ("ta.py", "talib-forbidden"),
                             ("gate.py", "consent-written-by-code"), ("run.ps1", "ps-accel-missing")} <= rules)
            self.assertFalse(any(f == "ok.py" for f, _ in rules))

        def test_T8_outputs_sarif_pastepack_page_json(self):
            self.put("m.py", "try:\n    pass\nexcept:\n    pass\n")
            self.put("bad.json", "{oops")
            self.put("good.json", "{}")
            rc, card = self.quiet(self.args(tools="none"))
            run = Path(card["receipt"])
            s = json.loads((run / "results.sarif").read_text(encoding="utf-8"))
            self.assertEqual(s["version"], "2.1.0")
            self.assertTrue(any(r["ruleId"] == "bare_except" for x in s["runs"] for r in x["results"]))
            pack = (run / "pastepack.txt").read_text(encoding="utf-8").splitlines()
            self.assertLessEqual(len(pack), PASTE_LINES)
            self.assertTrue(pack[-1].startswith("NEXT:"))
            self.assertIn("json-syntax", (run / "tools.html").read_text(encoding="utf-8"))
            data = PRIOR.read_json(run / "tools.json")
            self.assertEqual([f["file"] for f in data["tools"]["json-syntax"]["findings"]], ["bad.json"])
            self.assertEqual(rc, 1)
            short = pastepack({"files": {}}, {"t": {"lamp": "RED", "findings": [finding("t", "r", "RED", "f.py", i) for i in range(500)]}},
                              [], {"decision_all": "REVIEW_RED"}, 50).splitlines()
            self.assertEqual(len(short), 50)
            self.assertTrue(short[-1].startswith("NEXT:"))

        def test_T9_mcp_new_tools(self):
            self.put("m.py", "X = 1\n")
            _, card = self.quiet(self.args())
            run = Path(card["receipt"])
            names = [t["name"] for t in PRIOR.mcp_tools()]
            self.assertTrue({"summary", "findings", "handoff", "tool_findings", "pastepack"} <= set(names))
            self.assertIn("NEXT:", PRIOR.tool_result("pastepack", {}, run))
            page = PRIOR.tool_result("tool_findings", {"offset": 0, "limit": 5}, run)
            self.assertIn("items", page)
            with self.assertRaises(ValueError):
                PRIOR.tool_result("tool_findings", {"limit": 99}, run)

        def test_T10_live_adapters_parse_real_output(self):
            self.put("a.py", "import os\nimport subprocess\n\ndef f(x):\n    eval(x)\n    subprocess.call(x, shell=True)\n    return undefined_name\n")
            self.put("c.yaml", "a: [1,2\n")
            live = [t for t in TOOLS if t.available() and t.kind in ("py", "yaml", "any") and t.name not in ("pyright", "deptry", "pylint-duplicate", "interrogate")]
            res = run_tools(self.root, ["a.py"], ["c.yaml"], [], [], [t.name for t in live], 120)
            for t in live:
                self.assertIn(res[t.name]["status"], ("OK", "NA"), (t.name, res[t.name]))
            if "ruff" in res and res["ruff"]["status"] == "OK":
                self.assertTrue(any(f["rule"] == "F821" and f["level"] == "RED" for f in res["ruff"]["findings"]))
            if "bandit" in res and res["bandit"]["status"] == "OK":
                self.assertTrue(any(f["rule"] in ("B602", "B307") for f in res["bandit"]["findings"]))
            if "yamllint" in res and res["yamllint"]["status"] == "OK":
                self.assertTrue(any(f["rule"] == "syntax" and f["level"] == "RED" for f in res["yamllint"]["findings"]))

        def test_T11_tool_fix_only_in_overlay_and_reverts_on_test_failure(self):
            if not Ruff().available():
                self.skipTest("ruff 沒裝")
            src = "# [AST-ANCHOR: M]\nimport os\nimport sys\n\n\ndef f():\n    \"\"\"Doc.\"\"\"\n    return sys.argv\n"
            p = self.put("m.py", src)
            rc, card = self.quiet(self.args(mode="repair", tools="ruff", tool_fix=True))
            run = Path(card["receipt"])
            self.assertEqual(p.read_text(), src)                       # 原檔一字不動
            fixed = (run / "overlay" / "m.py").read_text()
            self.assertNotIn("import os", fixed)
            self.assertEqual(PRIOR.read_json(run / "tools.json")["tool_fix"]["accepted"], 1)
            self.put("tests/test_m.py", "import unittest\nimport m\nclass T(unittest.TestCase):\n    def test_os(self):\n        self.assertTrue(hasattr(m, 'os'))\n")
            out2 = Path(self.td.name) / "out2"
            rc, card = self.quiet(self.args(mode="repair", tools="ruff", tool_fix=True, project_tests=True, output=str(out2)))
            fix = PRIOR.read_json(Path(card["receipt"]) / "tools.json")["tool_fix"]
            self.assertEqual(fix["accepted"], 0)
            self.assertTrue(any("project_tests" in r[1] for r in fix["rejected"]))

        def test_T12_file_surface(self):
            text = Path(__file__).read_text(encoding="utf-8")
            self.assertEqual(text.splitlines()[2].strip(), "# [VIA:ACCEL-BRIDGE:v0111]")
            self.assertFalse(re.search(r"^\s*(import|from)\s+talib", text, re.M))
            self.assertFalse(re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=(?!=)", text))
            self.assertEqual(len(TOOLS), 15)
            self.assertEqual(len(set(TOOL_NAMES)), 15)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Tail)
    ok_tail = unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful()
    print("[計] VIA_PanoramaGuard v%s 本版 %d 項 · %s" % (TAIL, suite.countTestCases(), "PASS" if ok_tail else "FAIL"), flush=True)
    patched = {k: getattr(PRIOR, k) for k in ("inventory", "checked_manifest", "inspect_file", "mcp_tools", "tool_result", "VERSION")}
    originals = {"inventory": _PREV_INVENTORY, "checked_manifest": _PREV_CHECKED, "inspect_file": _PREV_INSPECT,
                 "mcp_tools": _PREV_MCP_TOOLS, "tool_result": _PREV_TOOL_RESULT, "VERSION": BASE_VERSION}
    SCOPE["files"] = None
    os.environ.pop("VIA_PG_CACHE", None)
    for k, v in originals.items():      # 前版自測要看前版原樣(例:MCP 工具數 3)
        setattr(PRIOR, k, v)
    try:
        rc_prior = PRIOR.selftest()
    finally:
        for k, v in patched.items():
            setattr(PRIOR, k, v)
        PRIOR.VERSION = BASE_VERSION + "+" + TAIL
    print("[計] 前版 %s 自測 %s" % (PRIOR_PATH.name, "PASS" if rc_prior == 0 else "FAIL"), flush=True)
    good = ok_tail and rc_prior == 0
    print("[計] VIA_PanoramaGuard v%s 自測 %s" % (TAIL, "PASS" if good else "FAIL"), flush=True)
    return 0 if good else 2


def main() -> int:
    argv = sys.argv[1:]
    if len(argv) == 4 and argv[0] == "_unittest":
        PRIOR.project_test_worker(Path(argv[1]), Path(argv[2]), argv[3])
        return 0
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", action="version", version=BASE_VERSION + "+" + TAIL)
    subs = ap.add_subparsers(dest="mode", required=True)
    for name in ("scan", "repair"):
        p = subs.add_parser(name)
        p.add_argument("--root", default=str(Path.cwd()), help="專案根目錄(任何對象)")
        p.add_argument("--output", default=str(PRIOR.DEFAULT_OUTPUT), help="工作樹外的收據目錄")
        p.add_argument("--workers", type=int, default=PRIOR.WORKERS)
        p.add_argument("--require-accelerator", action="store_true")
        p.add_argument("--suite", action="append", help="unittest 目錄(相對 root,可多次)")
        p.add_argument("--project-tests", action="store_true")
        p.add_argument("--changed-since", help="只看此 git 參照之後改過 / 新增的檔(例:origin/main、HEAD~3)")
        p.add_argument("--paths", nargs="+", help="只看這些相對路徑")
        p.add_argument("--tools", default="auto", help="auto(有裝就跑;大樹略過重工具)· all · none · 逗號清單(%s)" % ",".join(TOOL_NAMES))
        p.add_argument("--tool-timeout", type=int, default=TOOL_TIMEOUT)
        p.add_argument("--if-etag", help="上一輪 etag;都沒變就回 304(只限 scan)")
        p.add_argument("--no-cache", action="store_true")
        p.add_argument("--profile", choices=("auto", "via", "generic"), default="auto")
        p.add_argument("--paste-lines", type=int, default=PASTE_LINES)
        if name == "repair":
            p.add_argument("--commit", action="store_true")
            p.add_argument("--narrow-except", action="store_true")
            p.add_argument("--draft-docstrings", action="store_true")
            p.add_argument("--tool-fix", action="store_true", help="ruff safe 修正進覆層(逐檔驗證;專案測試不過全退)")
    t = subs.add_parser("template")
    t.add_argument("kind", choices=["manifest", "ledger", "powershell"])
    subs.add_parser("selftest")
    subs.add_parser("tools", help="列 15 個在地工具有沒有裝與裝法")
    s = subs.add_parser("serve", help="固定同一批收據的唯讀 MCP stdio")
    s.add_argument("--run", type=Path, required=True)
    if not argv or (argv[0].startswith("--") and argv[0] not in ("--help", "-h", "--version")):
        argv = ["repair" if "--apply" in argv else "scan"] + [a for a in argv if a != "--apply"]
    a = ap.parse_args(argv)
    if a.mode == "template":
        text = PRIOR.template(a.kind)
        print(text.replace("VIA_PanoramaGuard_v0101.py", Path(__file__).name) if a.kind == "powershell" else text)
        return 0
    if a.mode == "selftest":
        return selftest()
    if a.mode == "tools":
        return tools_card()
    if a.mode == "serve":
        PRIOR.serve(a.run, sys.stdin.buffer, sys.stdout.buffer)
        return 0
    return run_all(a)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError, KeyError, TypeError, RecursionError, subprocess.SubprocessError) as err:
        print("VIA BLOCKED · %s · %s" % (type(err).__name__, err), file=sys.stderr)
        sys.exit(2)
