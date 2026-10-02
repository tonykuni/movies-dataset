#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_Panorama v0100 — 萬用型全景偵測引擎:只讀 · 不執行目標 · 省 Token 卡優先 · 矩陣報告(文字 / HTML / JSON)

操作員(側線 2026-09-30):「建立 PY 引擎且名為 VIA_Panorama,加入所有功能導入加速器」「DEFAULT 目標 VCGC_VDF_VRN」
  「VCGC 節省 TOKEN 功能抓來用」「目標是節省 TOKEN」「先做引擎指令,技能稍晚再說」
  「全景式檢是看整個系統連結 SSOT 等的脈絡,萬用型;在此基礎上看 GITHUB 專案現況;好的、壞的三種燈跳出報告;
   客製化給 VIA;歷史紀錄下看全貌矩陣式報告 HTML;擴大到任何系統可看」
一支收齊 Invoke-VIA-GitHubPanorama-v0100.ps1 的唯讀部分(②現況 ③原因位置 ⑤動詞 ⑥矩陣)+ panorama-matrix 規格 §2–§6:
  A 拓樸(OP-100)· B 家族尾版 · C 標記 / 靜態合規(OP-200;--static 才開 ast/compile)· D 治理(鎖 · 隔離區 Q1–Q4 · 帳本 · SSOT · 交接)
  · E 漂移(git:分支 · 領先落後 · 未提交 · stash · 本機獨有 commit 分類 · 尾版本機↔origin · 原因表)· F 分級佇列(OP-300/400/500 濃縮包)
  · G 棘輪(本引擎自己的帳本;紅增 = RETROGRESS)· H 邊界(照實)· 歷史矩陣(同目標最近 12 輪 × 各段燈)
省 Token(L65):預設只印一張 ≤ 15 行的卡;細節落 JSON / HTML;`show <段>` 從上一份 JSON 取一段不重掃;`--if-etag` 沒變回 304;
  `read / slice / digest / pack / chain / brief` 轉交 VCGC 鎖版工具(VIA_ToolVersion_Lock 的 token / nlp;不自己取尾版)。
硬規則:不寫目標(報告只落輸出夾;VIA profile 落 git 忽略的 VIA_Reports/panorama)· 不 import / 不執行目標 · 網路只有 git clone/fetch
  (GitHub 目標或 --fetch)· 報告不回原文(計數 · 路徑 · 行號 · 簽名 · 燈)· 不呼叫第三方分析器 · 五態燈 GREEN/YELLOW/RED/HOLD/ABSENT(NODATA)。
  例外只有明說的 `verbs`(VIA:經 VCGC 中央入口跑 token · functions · handoff check · sync-check · check,只收判決行)。
結束碼:0 綠 · 2 黃/ABSENT/NODATA · 1 紅或 RETROGRESS · 3 目標讀不到。
用法:
  VIA_Panorama_v0100.py [scan] [目標] [--profile 名|檔] [--scope VCGC,VDF,VRN|ALL] [--static] [--fetch] [--predict]
                        [--out 夾] [--top N] [--width N] [--json-only] [--no-git] [--if-etag E] [--rich]
  VIA_Panorama_v0100.py show <A|B|C|D|E|F|G|H|history> [--out 夾] [--top N]
  VIA_Panorama_v0100.py read|slice|digest|pack|chain … (轉交鎖版省 Token 工具) · brief <檔>(NLP 摘要)
  VIA_Panorama_v0100.py verbs · --selftest
  目標:本機路徑 · https://github.com/<o>/<r>[/tree/<br>[/<子路徑>]] · <o>/<r>[@<br>][:<子路徑>];省略 = 本引擎所在的樹(VIA:VCGC,VDF,VRN)
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

import fnmatch
import hashlib
import html as _html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

try:  # 可選;沒有就退化成本引擎自己的純文字表(不報錯)
    import rich  # noqa: F401
    from rich.console import Console as _RichConsole
    from rich.table import Table as _RichTable
    from rich import box as _rich_box
except Exception:
    rich = None

VERSION = "v0100"
ENGINE = Path(__file__).stem
HERE = Path(__file__).resolve().parent
PROFILES_FILE = HERE / "VIA_Panorama_Profiles_v0100.json"
LAMPS = ("GREEN", "YELLOW", "RED", "HOLD", "ABSENT", "NODATA")
SEVER = {"RED": 5, "YELLOW": 3, "ABSENT": 2, "NODATA": 1, "GREEN": 0, "HOLD": -1}
SECTIONS = ("A", "B", "C", "D", "E", "F", "G", "H")
SECTION_NAMES = {"A": "拓樸快照 OP-100", "B": "家族尾版", "C": "標記 / 靜態合規 OP-200", "D": "治理資料",
                 "E": "漂移(git)", "F": "分級佇列 OP-300/400/500", "G": "棘輪", "H": "邊界"}
LANG = {".py": "py", ".ps1": "ps1", ".psm1": "ps1", ".js": "js", ".ts": "ts", ".tsx": "ts", ".go": "go", ".rs": "rs",
        ".java": "java", ".cs": "cs", ".sql": "sql", ".json": "json", ".jsonl": "jsonl", ".md": "md", ".yaml": "yaml",
        ".yml": "yaml", ".toml": "toml", ".html": "html", ".css": "css", ".sh": "sh", ".cmd": "cmd", ".bat": "cmd",
        ".csv": "csv", ".txt": "txt", ".png": "img", ".svg": "img", ".jpg": "img", ".jpeg": "img", ".gif": "img"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", ".pytest_cache", ".mypy_cache",
             ".panorama"}
TEXT_MAX = 4 * 1024 * 1024
BIG_BYTES = 5 * 1024 * 1024
IMPORT_PIN = re.compile(r"^\s*(?:from|import)\s+([A-Za-z_][\w.]*?_v(\d{3,4}))\b", re.M)
ANALYZERS = ("ruff", "black", "mutmut", "pytest", "hypothesis", "semgrep", "coverage")


NOTES: list = []  # 引擎內部降級紀錄(不吞例外:H 段照實列出)


def note(msg: str) -> None:
    NOTES.append(msg[:160])


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def worst(lamps) -> str:
    ls = [x for x in lamps if x and x != "HOLD"]
    return max(ls, key=lambda x: SEVER.get(x, 0)) if ls else "GREEN"


def pmap(fn, items):
    """加速器 accel_map(平行 · 保序 · 例外隔離);缺席退化序跑。回結果串列(例外 = None)。"""
    items = list(items)
    if VIA_ACCEL is not None and hasattr(VIA_ACCEL, "accel_map") and len(items) > 32:
        try:
            return [r if ok else None for ok, r in VIA_ACCEL.accel_map(fn, items)]
        except Exception as e:
            note(f"accel_map 失敗,退化序跑:{e}")
    out = []
    for it in items:
        try:
            out.append(fn(it))
        except Exception:
            out.append(None)
    return out


def git(root, *args, timeout=120) -> tuple:
    try:
        p = subprocess.run(["git", "-C", str(root), *args], capture_output=True, timeout=timeout,
                           stdin=subprocess.DEVNULL)
        return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")
    except Exception as e:  # git 缺席 / 逾時:誠實回 rc 127
        return 127, "", str(e)


# ───────────────────────── 設定(profile) ─────────────────────────

def load_profiles() -> dict:
    base = {"generic": {"name": "generic", "detect": [], "scopes": {"ALL": ["*"]}, "default_scopes": ["ALL"], "markers": [],
                        "tail_regex": r"^(?P<family>.+?)_v(?P<ver>\d{3,4})\.(?P<ext>py|ps1|json|jsonl)$"}}
    try:
        base.update(json.loads(PROFILES_FILE.read_text(encoding="utf-8")).get("profiles", {}))
    except Exception as e:
        note(f"設定冊讀不到,只有 generic:{e}")
    return base


def pick_profile(arg: str | None, root: Path | None, listing: set) -> dict:
    profs = load_profiles()
    if arg:
        if arg in profs:
            prof = dict(profs[arg])
        else:
            prof = json.loads(Path(arg).read_text(encoding="utf-8"))
    else:
        prof = dict(profs["generic"])
        for p in profs.values():
            if p.get("detect") and all(d in listing for d in p["detect"]):
                prof = dict(p)
                break
    if root is not None and (root / "panorama.manifest.json").is_file():  # §6.4 manifest 只讀,有就疊上
        try:
            man = json.loads((root / "panorama.manifest.json").read_text(encoding="utf-8"))
            prof["manifest"] = man.get("name", "manifest")
            if man.get("subsystems"):
                prof["scopes"] = {k: [x.rstrip("/") + "/*" if not any(c in x for c in "*?") else x for x in v]
                                  for k, v in man["subsystems"].items()}
                prof["default_scopes"] = list(prof["scopes"])
            for k in ("tail_regex", "skip_dirs", "ledgers"):
                if man.get(k):
                    prof[k] = man[k]
            if man.get("markers"):
                prof["markers"] = [{"id": k, "name": k, "ext": [], "regex": v, "need": True, "severity": "YELLOW",
                                    "scopes": list(prof["scopes"])} for k, v in man["markers"].items()]
            if man.get("lock") or man.get("quarantine"):
                prof["quarantine"] = {"path": man.get("quarantine"), "lock": man.get("lock"), "file_globs": []}
        except Exception as e:
            prof["manifest_error"] = str(e)[:120]
    return prof


# ───────────────────────── 來源(本機 / GitHub) ─────────────────────────

def parse_target(t: str) -> dict:
    """本機路徑 · https://github.com/o/r[/tree/br[/sub]] · o/r[@br][:sub] → {kind, …}"""
    m = re.match(r"^https?://github\.com/([^/\s]+)/([^/\s]+?)(?:\.git)?(?:/tree/([^/\s]+)(?:/(.+))?)?/?$", t)
    if m:
        return {"kind": "github", "owner": m[1], "repo": m[2], "branch": m[3] or "", "sub": (m[4] or "").strip("/")}
    m = re.match(r"^([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)(?:@([^:\s]+))?(?::(.+))?$", t)
    if m and not Path(t).exists():
        return {"kind": "github", "owner": m[1], "repo": m[2], "branch": m[3] or "", "sub": (m[4] or "").strip("/")}
    return {"kind": "local", "path": str(Path(t).expanduser().resolve())}


class LocalSource:
    kind = "local"

    def __init__(self, root: Path, use_git: bool = True):
        self.root = root
        self.label = str(root)
        self.git_top = None
        if use_git:
            rc, out, _ = git(root, "rev-parse", "--show-toplevel")
            if rc == 0 and out.strip():
                self.git_top = Path(out.strip())

    def listing(self, prof: dict) -> list:
        rows = []
        if self.git_top is not None:
            rc, out, _ = git(self.root, "ls-files", "-s", "-z", timeout=300)
            if rc == 0:
                for rec in out.split("\0"):
                    if "\t" in rec:
                        meta, rel = rec.split("\t", 1)
                        parts = meta.split()
                        rows.append({"rel": rel, "sha": parts[1] if len(parts) > 1 else "", "tracked": True,
                                     "link": parts[0] == "120000"})
                rc2, out2, _ = git(self.root, "ls-files", "-o", "--exclude-standard", "-z", timeout=300)
                for rel in (out2.split("\0") if rc2 == 0 else []):
                    if rel:
                        rows.append({"rel": rel, "sha": "", "tracked": False, "link": False})
        if not rows:
            for dp, dns, fns in os.walk(self.root):
                dns[:] = [d for d in dns if d not in SKIP_DIRS]
                for fn in fns:
                    full = Path(dp) / fn
                    rows.append({"rel": full.relative_to(self.root).as_posix(), "sha": "", "tracked": False,
                                 "link": full.is_symlink()})

        def stat(r):
            try:
                st = (self.root / r["rel"]).lstat()
                return st.st_size
            except OSError:
                return -1
        for r, size in zip(rows, pmap(stat, rows)):
            r["size"] = -1 if size is None else size
        return rows

    def read(self, rel: str) -> str | None:
        try:
            b = (self.root / rel).read_bytes()
        except OSError:
            return None
        return b[:TEXT_MAX].decode("utf-8-sig", "replace")

    def sha256(self, rel: str) -> str:
        try:
            with open(self.root / rel, "rb") as f:
                return hashlib.sha256(f.read(TEXT_MAX)).hexdigest()[:40]
        except OSError:
            return ""

    def exists(self, rel: str) -> bool:
        return (self.root / rel).exists()

    def close(self):
        pass


class GitHubSource:
    """git clone --depth 1 --filter=blob:none --no-checkout --sparse 到暫存夾;只把要看的檔稀疏取出(一次批次抓 blob)。"""
    kind = "github"

    def __init__(self, t: dict):
        self.t = t
        self.tmp = Path(tempfile.mkdtemp(prefix="via_panorama_gh_"))
        self.url = f"https://github.com/{t['owner']}/{t['repo']}.git"
        self.label = f"{t['owner']}/{t['repo']}" + (f"@{t['branch']}" if t["branch"] else "") + (f":{t['sub']}" if t["sub"] else "")
        args = ["clone", "-q", "--depth", "1", "--filter=blob:none", "--no-checkout", "--sparse"]
        if t["branch"]:
            args += ["--branch", t["branch"]]
        env_ok = subprocess.run(["git", *args, self.url, str(self.tmp / "r")], capture_output=True, timeout=600,
                                stdin=subprocess.DEVNULL, env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
        self.ok = env_ok.returncode == 0
        self.err = env_ok.stderr.decode("utf-8", "replace").strip().splitlines()[-1:] if not self.ok else []
        self.repo = self.tmp / "r"
        self.root = self.repo / t["sub"] if t["sub"] else self.repo
        self.git_top = None
        self._got = set()
        self._rows = self._ls() if self.ok else []
        self._names = {r["rel"] for r in self._rows}

    def listing(self, prof: dict) -> list:
        return [dict(r) for r in self._rows]

    def _ls(self) -> list:
        rc, out, _ = git(self.repo, "ls-tree", "-r", "-z", "HEAD", timeout=300)  # 不帶 -l:大小要 blob,會逐一抓(實測 5 分鐘)
        rows, pre = [], (self.t["sub"] + "/") if self.t["sub"] else ""
        for rec in out.split("\0") if rc == 0 else []:
            if "\t" not in rec:
                continue
            meta, path = rec.split("\t", 1)
            mode, typ, sha = (meta.split() + ["", "", ""])[:3]
            size = "-2"  # -2 = 沒量(blob 未抓);-1 = 讀不到
            if typ != "blob" or not path.startswith(pre):
                continue
            rows.append({"rel": path[len(pre):], "sha": sha, "tracked": True, "link": mode == "120000",
                         "size": int(size)})
        return rows

    def prefetch(self, rels):
        want = [r for r in rels if r not in self._got and r in self._names]
        if not want:
            return
        self._got.update(want)  # set 會取代整份樣式:每次帶上累積的全部,已取出的檔不會被收回
        pre = (self.t["sub"] + "/") if self.t["sub"] else ""
        pats = "\n".join("/" + re.sub(r"([*?\[\]\\!#])", r"\\\1", pre + r) for r in sorted(self._got)) + "\n"
        subprocess.run(["git", "-C", str(self.repo), "sparse-checkout", "set", "--no-cone", "--stdin"], input=pats.encode(),
                       capture_output=True, timeout=600)
        subprocess.run(["git", "-C", str(self.repo), "checkout", "-q", "HEAD"], capture_output=True, timeout=900,
                       env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})

    def read(self, rel: str) -> str | None:
        self.prefetch([rel])
        try:
            return (self.root / rel).read_bytes()[:TEXT_MAX].decode("utf-8-sig", "replace")
        except OSError:
            return None

    def sha256(self, rel: str) -> str:
        return ""

    def exists(self, rel: str) -> bool:
        return rel in self._names

    def close(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


# ───────────────────────── 掃描 ─────────────────────────

def _skipped(rel: str, prof: dict) -> str:
    parts = rel.split("/")
    for seg in parts[:-1]:
        if seg in SKIP_DIRS or seg in prof.get("skip_parts", ()) or seg in prof.get("skip_dirs", ()):
            return seg
        if any(seg.startswith(p) for p in prof.get("skip_prefix", ())):
            return seg
    rx = prof.get("skip_file_regex")
    if rx and re.search(rx, parts[-1]):
        return "凍結副本"
    return ""


def in_scope(rel: str, globs) -> bool:
    return any(fnmatch.fnmatchcase(rel, g) for g in globs)


def topology(rows: list, prof: dict, src) -> tuple:
    rx = re.compile(prof.get("tail_regex") or load_profiles()["generic"]["tail_regex"])
    langs, fams, skipped = {}, {}, {}
    venvs = {os.path.dirname(r["rel"]) + "/" for r in rows if os.path.basename(r["rel"]) == "pyvenv.cfg"}
    for r in rows:
        why = _skipped(r["rel"], prof) or next(("虛擬環境" for v in venvs if r["rel"].startswith(v)), "")
        if why:
            skipped[why] = skipped.get(why, 0) + 1
            r["skip"] = why
            continue
        ext = os.path.splitext(r["rel"])[1].lower()
        lang = LANG.get(ext, ext.lstrip(".") or "(無副檔名)")
        L = langs.setdefault(lang, {"files": 0, "bytes": 0, "tails": 0, "old": 0, "untracked": 0})
        L["files"] += 1
        L["bytes"] += max(r["size"], 0)
        L["untracked"] += 0 if r["tracked"] else 1
        r["lang"] = lang
        d, name = os.path.split(r["rel"])
        m = rx.match(name)
        if m:
            key = (d, m.group("family"), (m.groupdict().get("ext") or ext.lstrip(".")))
            fams.setdefault(key, []).append((int(m.group("ver")), r))
        else:
            r["tail"] = True
    for key, vs in fams.items():
        vs.sort(key=lambda x: x[0])
        for i, (v, r) in enumerate(vs):
            r["tail"] = i == len(vs) - 1
            r["family"] = key
    for r in rows:
        if "lang" in r:
            langs[r["lang"]]["tails" if r.get("tail") else "old"] += 1
    # 逐位元重複:git blob sha(免費);未追蹤檔才算 sha256(≤ 4 MB)
    need = [r for r in rows if "lang" in r and not r["sha"] and 0 < r["size"] <= TEXT_MAX]
    empty = {"e69de29bb2d1d6434b8b29ae775ad8c2e48c5391", hashlib.sha256(b"").hexdigest()[:40]}
    for r, h in zip(need, pmap(lambda x: src.sha256(x["rel"]), need)):
        r["sha"] = h or ""
    groups = {}
    for r in rows:
        if "lang" in r and r["sha"] and r["size"] != 0 and r["sha"] not in empty:
            groups.setdefault(r["sha"], []).append(r["rel"])
    dups = {k: v for k, v in groups.items() if len(v) > 1}
    return langs, fams, skipped, dups


def frozen_files(rows: list, prof: dict) -> set:
    """凍結是逐檔的:<檔名><frozen_suffix>(例 X.py.freeze.lock.json)只凍 X.py,不凍整夾。"""
    sufs = prof.get("frozen_suffixes") or []
    out = set()
    for r in rows:
        for suf in sufs:
            if r["rel"].endswith(suf):
                out.add(r["rel"][: -len(suf)])
    return out


def readonly_files(src, prof: dict) -> set:
    """唯讀名冊(profile readonly_rosters:{path, key}):key 下的 files + 各 added_* 批次;讀不到 = 空集合(不假裝有冊)。"""
    got = set()
    for ro in prof.get("readonly_rosters") or []:
        t = src.read(ro["path"]) if src.exists(ro["path"]) else None
        if t is None:
            note(f"唯讀名冊讀不到:{ro['path']}")
            continue
        try:
            sec = json.loads(t).get(ro.get("key", "")) or {}
        except ValueError as e:
            note(f"唯讀名冊壞:{ro['path']} {e}")
            continue
        got |= set(sec.get("files") or [])
        for k, v in sec.items():
            if k.startswith("added_") and isinstance(v, dict):
                f = v.get("files") or []
                got |= set(f.keys() if isinstance(f, dict) else f)
    return got


def static_check(text: str, rel: str) -> dict:
    """Tier-1:標準庫 ast.parse / compile(dont_inherit)只在記憶體;不 exec。只回計數 · 行號 · 簽名。"""
    import ast
    res = {"syntax": None, "compile": None, "defs": 0, "classes": 0, "bare_except": [], "future_pos": None}
    try:
        tree = ast.parse(text, filename=rel)
    except SyntaxError as e:
        res["syntax"] = {"line": e.lineno or 0, "sig": f"SyntaxError: {(e.msg or '')[:60]}"}
        return res
    try:
        compile(text, rel, "exec", dont_inherit=True)
    except SyntaxError as e:
        res["compile"] = {"line": e.lineno or 0, "sig": f"CompileError: {(e.msg or '')[:60]}"}
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            res["defs"] += 1
        elif isinstance(n, ast.ClassDef):
            res["classes"] += 1
        elif isinstance(n, ast.ExceptHandler) and n.type is None:
            res["bare_except"].append(n.lineno)
    return res


def tier0(text: str, ext: str) -> dict:
    """Tier-0 文字標記:docstring 首行 · shebang · from __future__ 位置 · param( 首句。"""
    lines = text.splitlines()
    out = {}
    if ext == ".py":
        body = [ln for ln in lines if ln.strip() and not ln.lstrip().startswith("#")]
        out["doc"] = bool(body) and bool(re.match(r"^[rRuUbB]{0,2}(\"\"\"|'''|\"|')", body[0].lstrip()))
        fut, first_imp, in_str = None, None, ""
        for i, ln in enumerate(lines):  # 三引號內的字(docstring)不算程式;--static 的 compile 才是定論
            if not in_str:
                if ln.startswith("from __future__"):
                    fut = i
                    break
                if first_imp is None and re.match(r"^(import|from)\s", ln):
                    first_imp = i
            for q in re.findall(r'"""|\'\'\'', ln):
                in_str = "" if in_str == q else (in_str or q)
        if fut is not None:
            out["future_late"] = (first_imp is not None and first_imp < fut, fut + 1)
    elif ext in (".ps1", ".psm1"):
        lines = re.sub(r"<#.*?#>", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S).splitlines()  # 區塊註解(說明)可在 param 前
        # 只看腳本層 param(:頂格、且在第一個 function 之前;函式內的 param( 不算
        fn_at = next((i for i, ln in enumerate(lines) if re.match(r"(?i)^function\s", ln)), len(lines))
        if any(re.match(r"(?i)^param\s*\(", ln) for ln in lines[:fn_at]):
            head = [ln.strip() for ln in lines[:fn_at] if ln.strip() and not ln.strip().startswith("#")
                    and not re.match(r"(?i)^(\[(CmdletBinding|OutputType|Diagnostics)|using\s)", ln.strip())]
            out["param_first"] = bool(head) and bool(re.match(r"(?i)^param\s*\(", head[0]))
    out["shebang"] = text.startswith("#!")
    return out


def scan(src, prof: dict, scopes: list, opts: dict) -> dict:
    t0 = time.time()
    rows = src.listing(prof)
    names = {r["rel"] for r in rows}
    langs, fams, skipped, dups = topology(rows, prof, src)
    frozen = frozen_files(rows, prof) | readonly_files(src, prof)
    scope_globs = {s: prof.get("scopes", {}).get(s, ["*"]) for s in scopes}
    qnames = set()
    rep = {"sections": {}}

    # D(先讀隔離區名冊:其他段的隔離項一律 HOLD)
    D = governance(src, prof, rows, names, fams, opts)
    qnames = set(D.get("quarantine_names", []))

    # A
    tails = sum(1 for r in rows if r.get("tail") and "lang" in r)
    old = sum(1 for r in rows if "lang" in r and not r.get("tail"))
    big = [r["rel"] for r in rows if r["size"] > BIG_BYTES and "lang" in r]
    links = sum(1 for r in rows if r.get("link"))
    unread = sum(1 for r in rows if r["size"] == -1)
    unsized = sum(1 for r in rows if r["size"] == -2)
    arows = [{"key": k, "lamp": "GREEN", "files": v["files"], "bytes": v["bytes"], "tails": v["tails"], "old": v["old"],
              "untracked": v["untracked"]} for k, v in sorted(langs.items(), key=lambda kv: -kv[1]["files"])]
    alamp = "YELLOW" if unread else "GREEN"
    rep["sections"]["A"] = {"lamp": alamp, "red_n": 0, "rows": arows,
                           "cols": ["key", "lamp", "files", "bytes", "tails", "old", "untracked"],
                           "summary": {"files": sum(v["files"] for v in langs.values()), "tails": tails, "old": old,
                                       "families": len(fams), "dup_groups": len(dups),
                                       "dup_files": sum(len(v) for v in dups.values()), "big": len(big), "links": links,
                                       "unreadable": unread, "bytes_unmeasured": unsized, "skipped": skipped},
                           "detail": {"big": big[:50], "dup_top": sorted(dups.values(), key=len, reverse=True)[:20]}}

    # B
    brows, scat = [], {}
    for (d, fam, ext) in fams:
        scat.setdefault((fam, ext), set()).add(d)
    for (d, fam, ext), vs in sorted(fams.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        lamp, why = "GREEN", ""
        if fam in qnames:
            lamp, why = "HOLD", "隔離區"
        elif len(scat[(fam, ext)]) > 1:
            lamp, why = "YELLOW", f"同族分散 {len(scat[(fam, ext)])} 夾"
        brows.append({"key": (d + "/" if d else "") + fam + "." + ext, "lamp": lamp, "tail": os.path.basename(vs[-1][1]["rel"]),
                      "versions": len(vs), "oldest": vs[0][0], "newest": vs[-1][0], "note": why})
    rep["sections"]["B"] = {"lamp": worst(r["lamp"] for r in brows), "red_n": 0, "rows": brows,
                           "cols": ["key", "lamp", "tail", "versions", "oldest", "newest", "note"],
                           "summary": {"families": len(brows), "scattered": sum(1 for r in brows if r["lamp"] == "YELLOW")}}

    # C:只看範圍內的尾版(版史不算;凍結夾 = HOLD)
    markers = [dict(m, _rx=re.compile(m["regex"])) for m in prof.get("markers", [])]
    cand = []
    for r in rows:
        if "lang" not in r or not r.get("tail") or r["size"] == -1:
            continue
        ext = os.path.splitext(r["rel"])[1].lower()
        if ext not in (".py", ".ps1", ".psm1") and not any(ext in (m.get("ext") or []) for m in markers):
            continue
        sc = [s for s, g in scope_globs.items() if in_scope(r["rel"], g)]
        if sc:
            r["scopes"] = sc
            cand.append(r)
    if hasattr(src, "prefetch"):
        src.prefetch([r["rel"] for r in cand])

    def inspect(r):
        text = src.read(r["rel"])
        if text is None:
            return {"unread": True}
        ext = os.path.splitext(r["rel"])[1].lower()
        res = {"t0": tier0(text, ext), "hits": {}, "pins": []}
        for m in markers:
            if ext in (m.get("ext") or [ext]):
                res["hits"][m["id"]] = bool(m["_rx"].search(text))
        if ext == ".py":
            res["pins"] = [(mm.group(1), int(mm.group(2)), text.count("\n", 0, mm.start()) + 1)
                           for mm in IMPORT_PIN.finditer(text)]
            if opts.get("static"):
                res["st"] = static_check(text, r["rel"])
        return res
    results = pmap(inspect, cand)
    fam_tail = {}
    for (d, fam, ext), vs in fams.items():
        fam_tail[fam] = max(fam_tail.get(fam, 0), vs[-1][0])
    crows, missing, errors, pins, holds = [], {}, [], [], 0
    counts = {m["id"]: {"have": 0, "miss": 0, "hold": 0} for m in markers}
    t0c = {"py": 0, "py_doc": 0, "future_late": 0, "ps": 0, "param_bad": 0, "unread": 0,
           "defs": 0, "classes": 0, "bare_except": 0, "syntax": 0, "compile": 0}
    for r, res in zip(cand, results):
        if res is None or res.get("unread"):
            t0c["unread"] += 1
            continue
        d, name = os.path.split(r["rel"])
        stem = os.path.splitext(name)[0]
        hold = r["rel"] in frozen or stem in qnames or (r.get("family") and r["family"][1] in qnames)
        holds += 1 if hold else 0
        ext = os.path.splitext(name)[1].lower()
        if ext == ".py":
            t0c["py"] += 1
            t0c["py_doc"] += 1 if res["t0"].get("doc") else 0
            fl = res["t0"].get("future_late")
            if fl and fl[0]:
                t0c["future_late"] += 1
                errors.append({"rel": r["rel"], "line": fl[1], "sig": "FUTURE-LATE: from __future__ 不在檔首", "lamp": "RED"})
        elif ext in (".ps1", ".psm1"):
            t0c["ps"] += 1
            if res["t0"].get("param_first") is False:
                t0c["param_bad"] += 1
                errors.append({"rel": r["rel"], "line": 0, "sig": "PARAM-NOT-FIRST: param( 不是首句", "lamp": "YELLOW"})
        for m in markers:
            if m["id"] not in res["hits"] or not any(s in m.get("scopes", scopes) for s in r["scopes"]):
                continue
            if hold:
                counts[m["id"]]["hold"] += 1
                continue
            if name in m.get("exempt_names", ()) or (m.get("exempt_name_regex") and re.search(m["exempt_name_regex"], name)):
                counts[m["id"]]["hold"] += 1
                continue
            if res["hits"][m["id"]]:
                counts[m["id"]]["have"] += 1
            else:
                counts[m["id"]]["miss"] += 1
                missing.setdefault(m["id"], []).append(r["rel"])
        for mod, ver, line in res["pins"]:
            fam = re.sub(r"_v\d{3,4}$", "", mod.split(".")[-1])
            if fam in fam_tail and ver < fam_tail[fam]:
                pins.append({"rel": r["rel"], "line": line, "sig": f"PINVER: 匯入 {fam}_v{ver:04d}(尾版 v{fam_tail[fam]:04d})",
                             "lamp": "YELLOW"})
        st = res.get("st")
        if st:
            t0c["defs"] += st["defs"]
            t0c["classes"] += st["classes"]
            t0c["bare_except"] += len(st["bare_except"])
            for k in ("syntax", "compile"):
                if st[k]:
                    t0c[k] += 1
                    errors.append({"rel": r["rel"], "line": st[k]["line"], "sig": st[k]["sig"], "lamp": "HOLD" if hold else "RED"})
    for m in markers:
        c = counts[m["id"]]
        tot = c["have"] + c["miss"]
        lamp = "GREEN" if c["miss"] == 0 else (m.get("severity", "YELLOW") if m.get("need") else "GREEN")
        if tot == 0:
            lamp = "ABSENT" if m.get("need") else "NODATA"
        crows.append({"key": m["id"], "lamp": lamp, "have": c["have"], "miss": c["miss"], "hold": c["hold"],
                      "cover": f"{(100.0 * c['have'] / tot):.1f}%" if tot else "—",
                      "note": m.get("name", "") + ("" if m.get("need") else "(資訊,不計燈)"),
                      "first_missing": (missing.get(m["id"]) or [""])[0]})
    crows.append({"key": "PY-DOC", "lamp": "GREEN", "have": t0c["py_doc"], "miss": t0c["py"] - t0c["py_doc"], "hold": 0,
                  "cover": f"{(100.0 * t0c['py_doc'] / t0c['py']):.1f}%" if t0c["py"] else "—", "note": "模組 docstring 首行(資訊)",
                  "first_missing": ""})
    crows.append({"key": "FUTURE-POS", "lamp": "RED" if t0c["future_late"] else "GREEN", "have": t0c["py"] - t0c["future_late"],
                  "miss": t0c["future_late"], "hold": 0, "cover": "", "note": "from __future__ 位置(晚於 import = COMPILE 錯)",
                  "first_missing": next((e["rel"] for e in errors if e["sig"].startswith("FUTURE")), "")})
    if t0c["ps"]:
        crows.append({"key": "PS-PARAM", "lamp": "YELLOW" if t0c["param_bad"] else "GREEN", "have": t0c["ps"] - t0c["param_bad"],
                      "miss": t0c["param_bad"], "hold": 0, "cover": "", "note": "param( 是首句", "first_missing": ""})
    if opts.get("static"):
        crows.append({"key": "AST", "lamp": "RED" if (t0c["syntax"] + t0c["compile"]) else "GREEN",
                      "have": t0c["py"] - t0c["syntax"] - t0c["compile"], "miss": t0c["syntax"] + t0c["compile"], "hold": 0,
                      "cover": "", "note": f"ast/compile · def {t0c['defs']} · class {t0c['classes']} · 裸 except {t0c['bare_except']}",
                      "first_missing": ""})
    red_c = sum(r["miss"] for r in crows if r["lamp"] == "RED")
    rep["sections"]["C"] = {"lamp": worst(r["lamp"] for r in crows) if crows else "NODATA", "red_n": red_c, "rows": crows,
                           "cols": ["key", "lamp", "have", "miss", "hold", "cover", "note", "first_missing"],
                           "summary": {"inspected": len(cand), "hold": holds, "tier": "Tier-1" if opts.get("static") else "Tier-0",
                                       **{k: v for k, v in t0c.items()}},
                           "detail": {"missing": {k: v[:200] for k, v in missing.items()}}}

    rep["sections"]["D"] = D
    rep["sections"]["E"] = drift(src, prof, fams, opts) if (src.git_top is not None and not opts.get("no_git")) else \
        {"lamp": "ABSENT", "na": True, "red_n": 0, "rows": [], "cols": ["key", "lamp", "value"],
         "summary": {"why": "不是本機 git 倉" if src.kind == "local" else "GitHub 目標:只有 HEAD 快照,沒有本機可比"}}

    # F:分級佇列(濃縮包:路徑 · 行號 · 簽名;無原文)
    op300 = [{"rel": p, "line": 0, "sig": f"MISSING-{mid}", "lamp": "YELLOW"} for mid, ps in missing.items()
             for p in ps if any(m["id"] == mid and m.get("need") for m in markers)]
    sig_groups = {}
    for e in errors + pins:
        sig_groups.setdefault(re.sub(r"\d+", "N", e["sig"]), []).append(e)
    op400 = {s: v for s, v in sig_groups.items() if len(v) > 1}
    op500 = [v[0] for s, v in sig_groups.items() if len(v) == 1]
    frows = [{"key": "OP-300 無損注入候選", "lamp": "YELLOW" if op300 else "GREEN", "n": len(op300),
              "groups": len({x["sig"] for x in op300}), "note": "缺標記可注入(不注入;補缺走 CGC_MDL124 via-bridge-sweep)"},
             {"key": "OP-400 同質批次候選", "lamp": "YELLOW" if op400 else "GREEN", "n": sum(len(v) for v in op400.values()),
              "groups": len(op400), "note": "同簽名跨檔重複(不替換)"},
             {"key": "OP-500 順序重構隔離", "lamp": "YELLOW" if op500 else "GREEN", "n": len(op500), "groups": len(op500),
              "note": "單發 / 跨模組(版號硬匯入等);給人或 LLM 第二輪決策"}]
    rep["sections"]["F"] = {"lamp": worst(r["lamp"] for r in frows), "red_n": 0, "rows": frows,
                           "cols": ["key", "lamp", "n", "groups", "note"],
                           "detail": {"op300": op300[:300], "op400": {s: [(x["rel"], x["line"]) for x in v[:50]] for s, v in op400.items()},
                                      "op500_pack": [f"{x['rel']}:{x['line']} · {x['sig']}" for x in op500[:200]]}}
    rep["scan_sec"] = round(time.time() - t0, 2)
    rep["inputs"] = {"files": len(rows), "names": len(names)}
    return rep


def governance(src, prof: dict, rows: list, names: set, fams: dict, opts: dict) -> dict:
    drows, out = [], {}
    # 鎖版工具冊(VIA):鎖的路徑都在 · 樹上是否有更新候選
    tl = prof.get("tool_lock")
    if tl:
        txt = src.read(tl["path"]) if src.exists(tl["path"]) else None
        if txt is None:
            drows.append({"key": "工具鎖 " + tl["path"], "lamp": "ABSENT", "value": "讀不到", "note": ""})
        else:
            try:
                lk = json.loads(txt)
                for k, v in lk.items():
                    p = v.get("path") if isinstance(v, dict) else (v if isinstance(v, str) and v.endswith(".py") else None)
                    if not p:
                        continue
                    rel = p[len(tl.get("strip_prefix", "")):] if p.startswith(tl.get("strip_prefix", "\0")) else p
                    have = rel in names
                    d, n = os.path.split(rel)
                    mm = re.match(r"^(.+?)_v(\d{3,4})\.py$", n)
                    newer = ""
                    if mm:
                        sib = sorted(x for x in names if os.path.dirname(x) == d and re.match(re.escape(mm[1]) + r"_v\d{3,4}\.py$", os.path.basename(x)))
                        if sib and os.path.basename(sib[-1]) != n:
                            newer = os.path.basename(sib[-1])
                    drows.append({"key": f"鎖 {k}", "lamp": "RED" if not have else ("YELLOW" if newer else "GREEN"),
                                  "value": n, "note": ("缺檔" if not have else (f"樹上較新 {newer}(候選未啟用)" if newer else "鎖版 = 樹上最新"))})
            except Exception as e:
                drows.append({"key": "工具鎖 " + tl["path"], "lamp": "RED", "value": "JSON 壞", "note": str(e)[:60]})
    for label, pat in (prof.get("pins") or {}).items():
        hits = sorted(x for x in names if fnmatch.fnmatchcase(x, pat))
        drows.append({"key": f"樹上最新 {label}", "lamp": "GREEN" if hits else "ABSENT",
                      "value": os.path.basename(hits[-1]) if hits else "—", "note": f"{len(hits)} 版"})
    # 隔離區 Q1–Q4
    q = prof.get("quarantine")
    out["quarantine_names"] = []
    if q and q.get("path"):
        qt = src.read(q["path"]) if src.exists(q["path"]) else None
        lt = src.read(q["lock"]) if q.get("lock") and src.exists(q["lock"]) else None
        if qt is None or lt is None:
            drows.append({"key": "隔離區 Q1–Q4", "lamp": "ABSENT", "value": "名冊或鎖讀不到",
                          "note": f"{q['path']} · {q.get('lock')}"})
        else:
            try:
                qj, lj = json.loads(qt), json.loads(lt)
                groups = qj.get("groups") or {k: v for k, v in qj.items() if isinstance(v, list)}
                allq = [n for g in groups.values() for n in g]
                uniq = set(allq)
                lock_names = set(lj.get("names") or []) if isinstance(lj, dict) and "names" in lj else \
                    set(lj.keys() if isinstance(lj, dict) else lj)
                q1 = sorted(uniq - lock_names)
                stems = {os.path.splitext(os.path.basename(x))[0] for x in names} | {os.path.basename(os.path.dirname(x)) for x in names}
                q2 = []
                for n in sorted(uniq):
                    lp = (lj.get(n) or {}).get("path") if isinstance(lj, dict) and isinstance(lj.get(n), dict) else None
                    globs = [g.format(name=n) for g in q.get("file_globs", [])]
                    ok = (lp and lp in names) or n in stems or any(fnmatch.fnmatchcase(x, g) for g in globs for x in names)
                    if not ok:
                        q2.append(n)
                over = sorted({n for n in uniq if allq.count(n) > 1})
                q3_bad = bool(over) or len(uniq) != len(allq)
                drows.append({"key": "Q1 名冊 ⊆ 鎖", "lamp": "RED" if q1 else "GREEN", "value": f"{len(uniq) - len(q1)}/{len(uniq)}",
                              "note": ("缺:" + " · ".join(q1[:8])) if q1 else ""})
                drows.append({"key": "Q2 原檔都在", "lamp": "RED" if q2 else "GREEN", "value": f"{len(uniq) - len(q2)}/{len(uniq)}",
                              "note": ("缺原檔:" + " · ".join(q2[:8])) if q2 else "不搬 · 不刪"})
                drows.append({"key": f"Q3 {len(groups)} 組蓋滿不重複", "lamp": "RED" if q3_bad else "GREEN",
                              "value": f"聯集 {len(uniq)} · 列名 {len(allq)}", "note": ("重疊:" + " · ".join(over[:8])) if over else ""})
                drows.append({"key": "called 聲明", "lamp": "HOLD", "value": str(qj.get("called")),
                              "note": "聲明,不是執行期的鎖;本引擎只讀不改"})
                for g, ns in groups.items():
                    for n in ns:
                        drows.append({"key": f"隔離 {g}/{n}", "lamp": "HOLD", "value": "HOLD", "note": "不呼叫 · 不畫綠"})
                out["quarantine_names"] = sorted(uniq)
                out["quarantine"] = {"groups": len(groups), "names": len(uniq), "q1": q1, "q2": q2, "overlap": over}
            except Exception as e:
                drows.append({"key": "隔離區 Q1–Q4", "lamp": "RED", "value": "JSON 壞", "note": str(e)[:60]})
    # 交接冊
    h = prof.get("handoff")
    if h:
        ht = src.read(h) if src.exists(h) else None
        if ht is None:
            drows.append({"key": "交接冊", "lamp": "ABSENT", "value": h, "note": ""})
        else:
            try:
                hj = json.loads(ht)
                pend = hj.get("pending") or []
                cl = str(hj.get("closeout_lamp", ""))
                drows.append({"key": "交接冊 handoff", "lamp": hj.get("lamp", "NODATA") if hj.get("lamp") in LAMPS else "NODATA",
                              "value": f"待辦 {len(pend)}", "note": f"at {hj.get('at', '')}"})
                drows.append({"key": "驗收 closeout_lamp", "lamp": cl if cl in LAMPS else "YELLOW", "value": cl or "—",
                              "note": "handoff 綠 ≠ 驗收;BLOCKED/REVIEW 照實"})
            except Exception as e:
                drows.append({"key": "交接冊", "lamp": "RED", "value": "JSON 壞", "note": str(e)[:60]})
    # 帳本(最後一筆的燈)
    for lg in prof.get("ledgers", []):
        t = src.read(lg) if src.exists(lg) else None
        if t is None:
            drows.append({"key": "帳本 " + os.path.basename(lg), "lamp": "ABSENT", "value": "—", "note": "讀不到"})
            continue
        lines = [x for x in t.splitlines() if x.strip()]
        last, bad = {}, 0
        for x in reversed(lines[-50:]):
            try:
                last = json.loads(x)
                break
            except Exception:
                bad += 1
        lamp = next((str(last.get(k)) for k in ("verdict", "lamp", "overall", "status") if str(last.get(k)) in LAMPS), "NODATA")
        drows.append({"key": "帳本 " + os.path.basename(lg), "lamp": lamp if not bad else "YELLOW", "value": f"{len(lines)} 行",
                      "note": f"末筆 {last.get('at') or last.get('ts') or last.get('ts_utc') or ''} {last.get('step') or last.get('id') or ''}".strip()})
    # 自動探索治理檔(只讀鍵數與可解析)
    grx = re.compile(prof.get("governance_regex") or r"(?i)(^|/)[^/]*(lock|quarantine|ledger|ssot|manifest)[^/]*\.(json|jsonl)$")
    gov = [r for r in rows if "lang" in r and grx.search(r["rel"]) and -2 <= r["size"] <= 20 * 1024 * 1024 and r["size"] != -1]

    def parse_ok(r):
        t = src.read(r["rel"])
        if t is None:
            return False
        try:
            if r["rel"].endswith(".jsonl"):
                ls = [x for x in t.splitlines() if x.strip()]
                if ls:
                    json.loads(ls[-1])
            else:
                json.loads(t)
            return True
        except Exception:
            return False
    if hasattr(src, "prefetch"):
        src.prefetch([r["rel"] for r in gov])
    oks = pmap(parse_ok, gov)
    badg = [r["rel"] for r, ok in zip(gov, oks) if not ok]
    kinds = {}
    for r in gov:
        k = next((w for w in ("quarantine", "manifest", "ledger", "lock", "ssot") if w in r["rel"].lower()), "other")
        kinds[k] = kinds.get(k, 0) + 1
    drows.append({"key": "治理檔自動探索", "lamp": "YELLOW" if badg else ("GREEN" if gov else "NODATA"), "value": f"{len(gov)} 檔",
                  "note": " · ".join(f"{k} {v}" for k, v in sorted(kinds.items())) + (f" · 壞 {len(badg)}" if badg else "")})
    out.update({"lamp": worst(r["lamp"] for r in drows) if drows else "NODATA",
                "red_n": sum(1 for r in drows if r["lamp"] == "RED"), "rows": drows, "cols": ["key", "lamp", "value", "note"],
                "detail": {"gov_bad": badg[:100]}})
    return out


def drift(src, prof: dict, fams: dict, opts: dict) -> dict:
    root = src.root
    notes = []
    if opts.get("fetch"):
        rc, _, err = git(root, "fetch", "-q", "--prune", "origin", timeout=600)
        notes.append("fetch rc %d%s" % (rc, (" · " + err.strip()[:80]) if rc else ""))
    branch = git(root, "rev-parse", "--abbrev-ref", "HEAD")[1].strip()
    remote = ""
    for cand in (f"origin/{branch}", "origin/HEAD", "origin/main", "origin/master"):
        if git(root, "rev-parse", "--verify", "-q", cand)[0] == 0:
            remote = cand
            break
    head = git(root, "rev-parse", "--short=12", "HEAD")[1].strip()
    rhead = git(root, "rev-parse", "--short=12", remote)[1].strip() if remote else ""
    ahead = behind = 0
    if remote:
        lr = git(root, "rev-list", "--left-right", "--count", f"HEAD...{remote}")[1].split()
        if len(lr) == 2:
            ahead, behind = int(lr[0]), int(lr[1])
    st = git(root, "status", "--porcelain", "--", ".")[1].splitlines()
    untracked = sum(1 for x in st if x.startswith("??"))
    modified = len(st) - untracked
    stash = len([x for x in git(root, "stash", "list")[1].splitlines() if x.strip()])
    wts = len([x for x in git(root, "worktree", "list")[1].splitlines() if x.strip()])
    local_only = []
    if remote and ahead:
        for ln in git(root, "log", "--format=%h|%ci|%s", f"{remote}..HEAD", "-n", "40")[1].splitlines():
            sha, date, subj = (ln.split("|", 2) + ["", ""])[:3]
            files = [f for f in git(root, "show", "--name-only", "--format=", sha)[1].splitlines() if f.strip()]
            code = [f for f in files if not re.search(r"\.(jsonl?|md|html|log)$", f)]
            local_only.append({"sha": sha, "date": date, "files": len(files),
                               "kind": "空" if not files else ("冊/報告" if not code else "含程式改動"), "subject": subj[:80]})
    predict = "沒量(加 --predict)"
    if opts.get("predict") and remote:
        rc, out, _ = git(root, "merge-tree", "--write-tree", "--name-only", "HEAD", remote)
        predict = "乾淨" if rc == 0 else (f"衝突 {len([x for x in out.splitlines()[1:] if x.strip() and not x.startswith(('CONFLICT', 'Auto-merging'))])} 檔" if rc == 1 else "沒量(git < 2.38)")
    # 尾版本機 ↔ origin
    tail_rows = []
    if remote:
        rx = re.compile(prof.get("tail_regex") or load_profiles()["generic"]["tail_regex"])
        rfam = {}
        for p in git(root, "ls-tree", "-r", "-z", "--name-only", remote, timeout=300)[1].split("\0"):  # -z:中文檔名不被引號化
            d, n = os.path.split(p)
            m = rx.match(n)
            if m and not _skipped(p, prof):
                k = (d, m.group("family"), m.groupdict().get("ext") or "")
                rfam[k] = max(rfam.get(k, 0), int(m.group("ver")))
        for k in sorted(set(rfam) | set(fams)):
            lv = fams[k][-1][0] if k in fams else 0
            rv = rfam.get(k, 0)
            if lv == rv:
                continue
            why = "本機缺" if not lv else ("origin 沒有" if not rv else ("本機落後" if lv < rv else "本機領先"))
            tail_rows.append({"key": (k[0] + "/" if k[0] else "") + f"{k[1]}.{k[2]}", "lamp": "RED" if not lv else "YELLOW",
                              "value": f"本機 v{lv:04d} ↔ origin v{rv:04d}", "note": why})
    lamp = "GREEN" if (ahead == 0 and behind == 0 and modified == 0) else "YELLOW"
    if not remote:
        lamp = "ABSENT"
    rows = [{"key": "分支", "lamp": "GREEN", "value": f"{branch} ↔ {remote or '—'}", "note": "refs 為上次 fetch 的狀態(--fetch 更新)"},
            {"key": "HEAD", "lamp": "GREEN" if head == rhead else "YELLOW", "value": f"{head} ↔ {rhead or '—'}", "note": ""},
            {"key": "領先 / 落後", "lamp": "GREEN" if not (ahead or behind) else "YELLOW", "value": f"{ahead} / {behind}", "note": ""},
            {"key": "工作樹", "lamp": "GREEN" if not modified else "YELLOW", "value": f"未提交 {modified} · 未追蹤 {untracked}", "note": ""},
            {"key": "stash / worktree", "lamp": "GREEN" if not stash else "YELLOW", "value": f"{stash} / {wts}", "note": ""},
            {"key": "merge 預測", "lamp": "GREEN" if predict.startswith("乾淨") or predict.startswith("沒量") else "YELLOW",
             "value": predict, "note": ""},
            {"key": "尾版本機↔origin", "lamp": worst(r["lamp"] for r in tail_rows) if tail_rows else "GREEN",
             "value": f"不同 {len(tail_rows)} 族", "note": ""}]
    causes = []
    if behind:
        causes.append({"where": remote, "what": f"origin 領先 {behind} 筆", "effect": "本機尾版可能落後", "fix": f"git merge {remote}(操作員手;本引擎不動)"})
    if ahead:
        kinds = {}
        for c in local_only:
            kinds[c["kind"]] = kinds.get(c["kind"], 0) + 1
        causes.append({"where": branch, "what": f"本機獨有 {ahead} 筆(" + " · ".join(f"{k} {v}" for k, v in kinds.items()) + ")",
                       "effect": "與 origin 分岔 → push 可能被拒", "fix": "備份分支後 merge(不 rebase · 不強推)"})
    if modified:
        causes.append({"where": "工作樹", "what": f"未提交 {modified} 檔", "effect": "merge 會被 git 拒", "fix": "先提交或 stash"})
    return {"lamp": lamp, "red_n": sum(1 for r in tail_rows if r["lamp"] == "RED"), "rows": rows + tail_rows[:200],
            "cols": ["key", "lamp", "value", "note"],
            "summary": {"branch": branch, "remote": remote, "ahead": ahead, "behind": behind, "modified": modified,
                        "untracked": untracked, "stash": stash, "worktrees": wts, "tail_diff": len(tail_rows), "notes": notes},
            "detail": {"local_only": local_only, "causes": causes}}


# ───────────────────────── 判定 · 棘輪 · 邊界 ─────────────────────────

def target_key(label: str, prof: dict, scopes: list) -> str:
    return hashlib.sha256(f"{label}|{prof.get('name')}|{','.join(scopes)}".encode()).hexdigest()[:12]


def read_ledger(path: Path) -> list:
    out = []
    try:
        for ln in path.read_text(encoding="utf-8").splitlines():
            try:
                out.append(json.loads(ln))
            except ValueError:
                note(f"帳本壞行略過:{path.name}")
    except OSError:
        return out
    return out


def ratchet(rep: dict, ledger: Path, tkey: str) -> dict:
    reds = sum(s.get("red_n", 0) for k, s in rep["sections"].items() if k in "ABCDEF")
    prev = [x for x in read_ledger(ledger) if x.get("target_key") == tkey]
    if not prev:
        lamp, verdict, pr = "NODATA", "NODATA", None
    else:
        pr = prev[-1].get("reds", 0)
        lamp, verdict = ("RED", "RETROGRESS") if reds > pr else ("GREEN", "OK")
    return {"lamp": lamp, "red_n": 0, "cols": ["key", "lamp", "value", "note"],
            "rows": [{"key": "棘輪", "lamp": lamp, "value": f"昨 {pr if pr is not None else '—'} · 今 {reds} · 差 "
                      f"{(reds - pr) if pr is not None else '—'}", "note": verdict}],
            "summary": {"prev": pr, "now": reds, "verdict": verdict, "history": len(prev)}}


def boundaries(opts: dict, src) -> dict:
    measured = ["檔名 · 大小 · git blob 雜湊(重複群)", "家族尾版(檔名正則)", "文字標記(Tier-0)", "治理檔可解析 · 鍵 / 行數",
                "git refs(本機)" if src.kind == "local" else "GitHub HEAD 快照(clone --depth 1 --filter=blob:none)"]
    if opts.get("static"):
        measured.append("Tier-1:ast.parse / compile(dont_inherit;不 exec)")
    not_measured = ["不執行任何目標程式 / 測試(R2)", "不呼叫 " + " · ".join(ANALYZERS) + "(R5)",
                    "不跑 rayon / Send / Sync 等非此行程的東西(硬叫只會假綠)"]
    if not opts.get("static"):
        not_measured.append("語法 / 編譯錯(要 --static)")
    if not opts.get("fetch"):
        not_measured.append("origin 最新狀態(refs 是上次 fetch;要 --fetch)")
    rows = [{"key": "量了", "lamp": "GREEN", "value": x, "note": ""} for x in measured] + \
           [{"key": "沒量", "lamp": "NODATA", "value": x, "note": ""} for x in not_measured] + \
           [{"key": "引擎降級", "lamp": "YELLOW" if NOTES else "GREEN", "value": f"{len(NOTES)} 次",
             "note": " · ".join(NOTES[:4])}] + \
           [{"key": "名冊 ≠ 權限", "lamp": "HOLD", "value": "隔離區是名冊策略,不是沙盒", "note": "本引擎只保證自己不呼叫、不搬、不改;不攔截別人的 import / 磁碟 / 網路 / 子行程"},
            {"key": "棘輪基準", "lamp": "HOLD", "value": "本引擎自己的帳本", "note": "換輸出夾 = 基準歸零(NODATA)"}]
    return {"lamp": "GREEN", "red_n": 0, "rows": rows, "cols": ["key", "lamp", "value", "note"]}


def q4_check(rep: dict, qnames: list) -> list:
    """Q4:任何格把隔離項畫成綠 → 本引擎自己 RED。"""
    bad = []
    if not qnames:
        return bad
    pat = re.compile(r"(^|[/\s])(" + "|".join(re.escape(n) for n in qnames) + r")([._/\s]|$)")
    for k, s in rep["sections"].items():
        for r in s.get("rows", []):
            if r.get("lamp") == "GREEN" and pat.search(str(r.get("key", ""))):
                bad.append(f"{k}:{r['key']}")
    return bad


# ───────────────────────── 呈現(文字 / HTML) ─────────────────────────

def dw(s: str) -> int:
    return sum(0 if unicodedata.combining(c) else (2 if unicodedata.east_asian_width(c) in "WF" else 1) for c in str(s))


def clip(s, w: int, mid: bool = False) -> str:
    s = str(s)
    if dw(s) <= w:
        return s
    if w <= 1:
        return "…"
    if mid:
        tail_w = min(24, w - 4)
        tail, i = "", len(s)
        while i > 0 and dw(s[i - 1] + tail) <= tail_w:
            i -= 1
            tail = s[i] + tail
        head, j = "", 0
        while j < i and dw(head + s[j]) <= w - 1 - dw(tail):
            head += s[j]
            j += 1
        return head + "…" + tail
    out = ""
    for c in s:
        if dw(out + c) > w - 1:
            break
        out += c
    return out + "…"


def fit_table(cols: list, rows: list, width: int, top: int) -> str:
    """版面自動調節:key > lamp > 數值 > 說明;不夠寬依序折 → 縮 → 藏(表尾註明省略欄);> 200 列只印前 top + 尾 5。"""
    if not rows:
        return "  (無列)"
    kind = {c: ("key" if c == "key" else "lamp" if c == "lamp" else
                "num" if all(isinstance(r.get(c), (int, float)) for r in rows if r.get(c) not in (None, "")) else "text")
            for c in cols}
    shown = rows if len(rows) <= 200 else rows[:top] + rows[-5:]
    nat = {c: max([dw(c)] + [dw(str(r.get(c, ""))) for r in shown]) for c in cols}
    nat["lamp"] = 6 if "lamp" in nat else 0
    cap = {"key": 64, "text": 60, "num": 14, "lamp": 6}
    w = {c: min(nat[c], cap[kind[c]]) for c in cols}
    hidden = []

    def total():
        return sum(w[c] for c in cols if c not in hidden) + 2 * (len(cols) - len(hidden)) + 2
    for c in [c for c in cols if kind[c] == "text"]:
        while total() > width and w[c] > 12:
            w[c] -= 1
    while total() > width and w.get("key", 0) > 24:
        w["key"] -= 1
    for c in reversed([c for c in cols if kind[c] == "text"]):
        if total() > width:
            hidden.append(c)
    vis = [c for c in cols if c not in hidden]

    def cell(c, v):
        v = "" if v is None else v
        s = clip(v, w[c], mid=(kind[c] == "key" or c in ("first_missing", "tail")))
        pad = w[c] - dw(s)
        return (" " * pad + s) if kind[c] == "num" else (s + " " * pad)
    lines = ["  " + "  ".join(cell(c, c) for c in vis), "  " + "  ".join("─" * w[c] for c in vis)]
    for i, r in enumerate(shown):
        if len(rows) > 200 and i == top:
            lines.append(f"  … 其餘 {len(rows) - top - 5} 列見 JSON")
        lines.append("  " + "  ".join(cell(c, r.get(c, "")) for c in vis))
    if hidden:
        lines.append("  省略欄:" + " · ".join(hidden))
    return "\n".join(lines)


def render_text(rep: dict, width: int, top: int) -> str:
    out = [f"VIA_Panorama {VERSION} · {rep['target']} · profile {rep['profile']} · 範圍 {','.join(rep['scopes'])}"
           f" · sha16 {rep['sha16']} · {rep['at']} · 總判 {rep['verdict']} · rc {rep['rc']}"]
    for k in SECTIONS:
        s = rep["sections"].get(k)
        if not s:
            continue
        out.append(f"\n{k} · {SECTION_NAMES[k]} · {s['lamp']}")
        if s.get("summary"):
            out.append("  " + " · ".join(f"{a} {b}" for a, b in s["summary"].items() if not isinstance(b, (dict, list)))[:width * 2])
        out.append(fit_table(s["cols"], s["rows"], width, top))
    return "\n".join(out) + "\n"


def render_rich(rep: dict, top: int):
    con = _RichConsole()
    for k in SECTIONS:
        s = rep["sections"].get(k)
        if not s:
            continue
        rows = s["rows"] if len(s["rows"]) <= 200 else s["rows"][:top]
        t = _RichTable(title=f"[bold dim]{k} · {SECTION_NAMES[k]} · {s['lamp']}[/]", box=_rich_box.SIMPLE_HEAD if len(rows) <= 25
                       else _rich_box.MINIMAL, padding=(0, 1 if len(rows) <= 25 else 0), row_styles=["", "dim"] if len(rows) > 25 else None)
        for c in s["cols"]:
            t.add_column(c, width=6 if c == "lamp" else None, overflow="fold", justify="left")
        for r in rows:
            t.add_row(*[str(r.get(c, "")) for c in s["cols"]])
        con.print(t)


LAMP_CSS = {"GREEN": "#2e7d32", "YELLOW": "#b58900", "RED": "#c62828", "HOLD": "#6d6d6d", "ABSENT": "#8a8a8a", "NODATA": "#8a8a8a"}
CSS = """body{margin:0;padding:20px;background:#fafafa;color:#222;font:11px/1.45 "JetBrains Mono","Cascadia Code","SF Mono",Consolas,"Noto Sans Mono CJK TC",monospace}
pre{font-size:11px;line-height:1.35;white-space:pre;overflow-x:auto;margin:0}
h1,h2{font-weight:600;font-size:12.5px;letter-spacing:.02em;margin:14px 0 4px;color:#333}
table{border-collapse:collapse;margin:4px 0 10px;max-width:100%}th,td{padding:1px 8px;border-bottom:1px solid #e4e4e4;text-align:left;vertical-align:top;white-space:nowrap}
th{font-weight:600;color:#555;border-bottom:1px solid #bbb}td.n{text-align:right}tr:nth-child(even) td{background:rgba(0,0,0,.018)}
.wrap{overflow-x:auto}.l{display:inline-block;min-width:6ch;font-weight:600}.HOLD{font-style:italic}
.cards{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0 10px}.card{border:1px solid #ddd;border-left:4px solid #999;padding:3px 8px;background:#fff}
details{margin:2px 0 8px}summary{cursor:pointer;color:#555}.mut{color:#777}
@media(prefers-color-scheme:dark){body{background:#111318;color:#d8d8d8}h1,h2{color:#cfd3da}th{color:#aab}td,th{border-color:#2a2f3a}.card{background:#171a21;border-color:#2a2f3a}tr:nth-child(even) td{background:rgba(255,255,255,.03)}}
@media(max-width:700px){body{padding:12px 16px}}"""


def lamp_html(l: str) -> str:
    return f"<span class='l {_html.escape(l)}' style='color:{LAMP_CSS.get(l, '#888')}'>{_html.escape(l)}</span>"


def table_html(cols: list, rows: list, limit: int = 500) -> str:
    e = _html.escape
    h = ["<div class='wrap'><table><thead><tr>" + "".join(f"<th>{e(c)}</th>" for c in cols) + "</tr></thead><tbody>"]
    for r in rows[:limit]:
        tds = []
        for c in cols:
            v = r.get(c, "")
            if c == "lamp":
                tds.append(f"<td>{lamp_html(str(v))}</td>")
            elif isinstance(v, (int, float)):
                tds.append(f"<td class='n'>{v:,}</td>" if isinstance(v, int) else f"<td class='n'>{v}</td>")
            else:
                tds.append(f"<td>{e(str(v))}</td>")
        h.append("<tr>" + "".join(tds) + "</tr>")
    h.append("</tbody></table></div>")
    if len(rows) > limit:
        h.append(f"<div class='mut'>其餘 {len(rows) - limit} 列見 JSON</div>")
    return "".join(h)


def render_html(rep: dict, history: list) -> str:
    e = _html.escape
    s = rep["sections"]
    cards = [("目標", rep["target"]), ("來源", rep["source"]), ("SHA16", rep["sha16"]), ("檔數", s["A"]["summary"]["files"]),
             ("範圍", ",".join(rep["scopes"])), ("總判", rep["verdict"]), ("棘輪", s["G"]["rows"][0]["value"]),
             ("秒", rep["sec"])]
    if "quarantine" in s["D"]:
        q = s["D"]["quarantine"]
        cards.append(("隔離區", f"{q['names']} 名 · {q['groups']} 組"))
    h = [f"<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
         f"<title>VIA Panorama 矩陣</title><style>{CSS}</style></head><body>",
         f"<h1>VIA_Panorama {VERSION} · {e(rep['run'])} · 總判 {lamp_html(rep['verdict'])} · rc {rep['rc']}</h1>",
         "<div class='cards'>" + "".join(f"<div class='card' style='border-left-color:{LAMP_CSS.get(str(v), '#999') if k == '總判' else '#999'}'>"
                                         f"<span class='mut'>{e(k)}</span> {e(str(v))}</div>" for k, v in cards) + "</div>"]
    h.append("<h2>總覽矩陣 · 段 × 燈 × 紅數(先看這張;細節往下)</h2>")
    ov = [{"段": k, "名稱": SECTION_NAMES[k], "lamp": s[k]["lamp"], "紅": s[k].get("red_n", 0),
           "非綠列": sum(1 for r in s[k].get("rows", []) if r.get("lamp") not in ("GREEN", "HOLD")),
           "HOLD": sum(1 for r in s[k].get("rows", []) if r.get("lamp") == "HOLD")} for k in SECTIONS if k in s]
    h.append(table_html(["段", "名稱", "lamp", "紅", "非綠列", "HOLD"], ov))
    for k in SECTIONS:
        sec = s.get(k)
        if not sec:
            continue
        h.append(f"<h2 id='{k}'>{k} · {e(SECTION_NAMES[k])} · {lamp_html(sec['lamp'])}</h2>")
        if sec.get("summary"):
            h.append("<div class='mut'>" + e(" · ".join(f"{a} {b}" for a, b in sec["summary"].items() if not isinstance(b, (dict, list)))) + "</div>")
        rows_s = sorted(sec["rows"], key=lambda r: -SEVER.get(r.get("lamp"), 0)) if k in "BD" else sec["rows"]
        h.append(table_html(sec["cols"], rows_s[:25]))
        if len(rows_s) > 25:
            h.append(f"<details><summary>其餘 {len(rows_s) - 25} 列</summary>{table_html(sec['cols'], rows_s[25:])}</details>")
        det = sec.get("detail") or {}
        for dk, dv in det.items():
            if not dv:
                continue
            if isinstance(dv, dict):
                body = "\n".join(f"{a}: {len(b)} · " + " · ".join(str(x) for x in b[:12]) for a, b in dv.items())
                n = sum(len(b) for b in dv.values())
            elif isinstance(dv, list) and dv and isinstance(dv[0], dict):
                cols = list(dv[0].keys())
                h.append(f"<details><summary>{e(dk)} · {len(dv)}</summary>{table_html(cols, dv, 300)}</details>")
                continue
            else:
                body = "\n".join(str(x) for x in dv)
                n = len(dv)
            h.append(f"<details><summary>{e(dk)} · {n}</summary><pre>{e(body)}</pre></details>")
    if history:
        h.append("<h2>歷史矩陣 · 同目標最近 12 輪 × 各段燈</h2>")
        hrows = [{"at": x.get("at", ""), "sha16": x.get("sha16", ""), "verdict": x.get("verdict", ""), "reds": x.get("reds", 0),
                  **{k: x.get("sections", {}).get(k, "") for k in SECTIONS}, "sec": x.get("sec", "")} for x in history[-12:]][::-1]
        cols = ["at", "sha16", "verdict", "reds", *SECTIONS, "sec"]
        rows_h = []
        for r in hrows:
            rows_h.append("<tr>" + "".join(f"<td>{lamp_html(str(r[c]))}</td>" if c in SECTIONS or c == "verdict" else
                                           f"<td>{e(str(r[c]))}</td>" for c in cols) + "</tr>")
        h.append("<div class='wrap'><table><thead><tr>" + "".join(f"<th>{c}</th>" for c in cols) + "</tr></thead><tbody>"
                 + "".join(rows_h) + "</tbody></table></div>")
    h.append(f"<p class='mut'>只讀 · 不執行目標 · 報告不含原文 · JSON:panorama_latest.json · 帳本:universal_ledger.jsonl</p></body></html>")
    return "\n".join(h)


def card(rep: dict, paths: dict) -> str:
    """省 Token 卡:≤ 15 行。細節看 show <段> 或 HTML。"""
    s = rep["sections"]
    A, C, D, E, F, G = (s[k] for k in "ACDEFG")
    lines = [f"[VIA_Panorama {VERSION}] {rep['target']} · {rep['profile']} · 範圍 {','.join(rep['scopes'])} · sha16 {rep['sha16']}"
             f" · {rep['sec']}s · 總判 {rep['verdict']} · rc {rep['rc']} · etag {rep['etag']}"]
    a = A["summary"]
    lines.append(f"  A {A['lamp']:<6} 檔 {a['files']} · 尾版 {a['tails']} · 舊版 {a['old']} · 家族 {a['families']} · 重複群 {a['dup_groups']}"
                 f" · 大檔 {a['big']} · 略過 {sum(a['skipped'].values())}")
    lines.append(f"  B {s['B']['lamp']:<6} 家族 {s['B']['summary']['families']} · 分散 {s['B']['summary']['scattered']}")
    lines.append(f"  C {C['lamp']:<6} " + " · ".join(f"{r['key']} {r['have']}/{r['have'] + r['miss']}" + (f"(缺{r['miss']})" if r['miss'] else "")
                                                   for r in C["rows"])[:260])
    dbad = " · ".join(f"{r['key']} {r['lamp']}" for r in D["rows"] if r["lamp"] not in ("GREEN", "HOLD"))[:260]
    lines.append(f"  D {D['lamp']:<6} " + (dbad or "非綠 0"))
    es = E.get("summary", {})
    lines.append(f"  E {E['lamp']:<6} " + (f"{es.get('branch')} ↔ {es.get('remote')} · 領先 {es.get('ahead')} · 落後 {es.get('behind')}"
                                            f" · 未提交 {es.get('modified')} · 尾版不同 {es.get('tail_diff')}" if "branch" in es else str(es.get("why", ""))))
    lines.append(f"  F {F['lamp']:<6} " + " · ".join(f"{r['key'].split()[0]} {r['n']}" for r in F["rows"]))
    lines.append(f"  G {G['lamp']:<6} {G['rows'][0]['value']} · {G['rows'][0]['note']}")
    reds = [(k, r) for k in "CDE" for r in s[k]["rows"] if r.get("lamp") == "RED"][:3]
    for k, r in reds:
        lines.append(f"  紅 {k}:{r['key']} · {r.get('value') or r.get('first_missing') or ''} {r.get('note', '')}"[:200])
    lines.append(f"  頁 {paths['html']}")
    lines.append(f"  細看:{ENGINE}.py show <A–H|history> [--top N](不重掃) · 同輸入再跑加 --if-etag {rep['etag']}")
    return "\n".join(lines)


# ───────────────────────── 主流程 ─────────────────────────

def default_target() -> Path:
    return HERE.parents[1]


def out_dir(opts: dict, src, prof: dict) -> Path:
    if opts.get("out"):
        return Path(opts["out"]).expanduser().resolve()
    if src.kind == "local":
        rel = prof.get("out_in_ignored")
        if rel and src.git_top is not None:
            probe = (src.root / rel / "panorama_latest.json").relative_to(src.root).as_posix()
            if git(src.root, "check-ignore", "-q", probe)[0] == 0:
                return src.root / rel
        cwd = Path.cwd().resolve()
        root = src.root.resolve()
        if cwd == root or root in cwd.parents:
            return Path.home() / ".via_panorama"
        return cwd / ".panorama"
    return Path.cwd().resolve() / ".panorama"


def fingerprint(src, prof: dict, scopes: list, opts: dict) -> str:
    h = hashlib.sha256(f"{VERSION}|{prof.get('name')}|{','.join(scopes)}|{sorted((k, v) for k, v in opts.items() if k in ('static', 'no_git'))}".encode())
    for f in (Path(__file__), PROFILES_FILE):  # 引擎或設定一改,etag 就變(不拿舊卡冒充)
        try:
            h.update(f.read_bytes())
        except OSError as e:
            h.update(f"missing:{f.name}:{e.errno}".encode())
    if src.kind == "local" and src.git_top is not None:
        h.update(git(src.root, "rev-parse", "HEAD")[1].encode())
        h.update(git(src.root, "status", "--porcelain", "-z", "--", ".")[1].encode())
        rem = git(src.root, "for-each-ref", "--format=%(objectname)", "refs/remotes")[1]
        h.update(rem.encode())
        # 未提交檔的內容變化:用 mtime+size 帶進來
        for ln in git(src.root, "status", "--porcelain", "--", ".")[1].splitlines():
            p = src.root / ln[3:].strip().strip('"')
            try:
                st = p.stat()
                h.update(f"{st.st_mtime_ns}:{st.st_size}".encode())
            except OSError:
                h.update(f"gone:{p}".encode())  # 已刪的檔也要讓 etag 變
    elif src.kind == "local":
        for dp, dns, fns in os.walk(src.root):
            dns[:] = sorted(d for d in dns if d not in SKIP_DIRS)
            for fn in sorted(fns):
                try:
                    st = (Path(dp) / fn).stat()
                    h.update(f"{dp}/{fn}:{st.st_size}:{st.st_mtime_ns}".encode())
                except OSError:
                    h.update(f"unreadable:{dp}/{fn}".encode())
    else:
        h.update(git(src.repo, "rev-parse", "HEAD")[1].encode())
    return h.hexdigest()[:16]


def run_scan(target: str | None, opts: dict) -> int:
    t0 = time.time()
    tspec = parse_target(target) if target else {"kind": "local", "path": str(default_target())}
    if tspec["kind"] == "github":
        src = GitHubSource(tspec)
        if not src.ok:
            print(f"[VIA_Panorama] 目標讀不到:{src.label} · ABSENT · {' '.join(src.err)[:160]}(私有倉不要憑證,不重試)")
            src.close()
            return 3
    else:
        root = Path(tspec["path"])
        if not root.is_dir():
            print(f"[VIA_Panorama] 目標讀不到:{root} · ABSENT")
            return 3
        src = LocalSource(root, use_git=not opts.get("no_git"))
    try:
        quick = set()
        for p in load_profiles().values():
            for d in p.get("detect", []):
                if src.exists(d):
                    quick.add(d)
        prof = pick_profile(opts.get("profile"), src.root if src.kind == "local" else None, quick)
        scopes = [x for x in (opts.get("scope") or "").split(",") if x] or prof.get("default_scopes") or ["ALL"]
        if scopes == ["ALL"] and "ALL" not in prof.get("scopes", {}):
            scopes = list(prof.get("scopes", {"ALL": ["*"]}))
        unknown = [x for x in scopes if x not in prof.get("scopes", {})]
        if unknown:
            print(f"[VIA_Panorama] 範圍不認得:{','.join(unknown)} · profile {prof.get('name')} 有 {','.join(prof.get('scopes', {}))}")
            return 2
        od = out_dir(opts, src, prof)
        etag = fingerprint(src, prof, scopes, opts)
        latest = od / "panorama_latest.json"
        if opts.get("if_etag") and latest.is_file():
            try:
                old = json.loads(latest.read_text(encoding="utf-8"))
                if old.get("etag") == opts["if_etag"] == etag:
                    print(f"[VIA_Panorama] 304 沒變 · etag {etag} · 總判 {old.get('verdict')} · 沿用 {latest}")
                    return int(old.get("rc", 2))
            except (ValueError, OSError) as e:
                note(f"上一份 JSON 讀不到,照常重掃:{e}")
        rep = scan(src, prof, scopes, opts)
        rep["sections"]["H"] = boundaries(opts, src)
        run = "pan-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        sha16 = (git(src.root if src.kind == "local" else src.repo, "rev-parse", "--short=16", "HEAD")[1].strip()
                 if (src.git_top is not None or src.kind == "github") else "") or "—"
        tkey = target_key(src.label, prof, scopes)
        od.mkdir(parents=True, exist_ok=True)
        ledger = od / "universal_ledger.jsonl"
        rep["sections"]["G"] = ratchet(rep, ledger, tkey)
        qbad = q4_check(rep, rep["sections"]["D"].get("quarantine_names", []))
        if qbad:
            rep["sections"]["D"]["rows"].append({"key": "Q4 隔離項沒畫綠", "lamp": "RED", "value": f"{len(qbad)} 格",
                                                 "note": " · ".join(qbad[:6])})
            rep["sections"]["D"]["lamp"] = "RED"
            rep["sections"]["D"]["red_n"] += 1
        elif rep["sections"]["D"].get("quarantine_names"):
            rep["sections"]["D"]["rows"].append({"key": "Q4 隔離項沒畫綠", "lamp": "GREEN", "value": "0 格", "note": "全 HOLD"})
        lamps = [rep["sections"][k]["lamp"] for k in "ABCDEFG" if not rep["sections"][k].get("na")]  # 不適用段(非 git)不計總判
        verdict = worst(lamps)
        rc = 1 if verdict == "RED" else (2 if verdict in ("YELLOW", "ABSENT", "NODATA") else 0)
        rep.update({"engine": ENGINE, "version": VERSION, "run": run, "at": now_utc(), "target": src.label, "source": src.kind,
                    "profile": prof.get("name", "custom"), "scopes": scopes, "sha16": sha16, "etag": etag, "verdict": verdict,
                    "rc": rc, "sec": round(time.time() - t0, 1), "target_key": tkey,
                    "accel": {"loaded": bool(VIA_ACCEL), "canonical": getattr(VIA_ACCEL, "CANONICAL", None)}})
        reds = sum(s.get("red_n", 0) for k, s in rep["sections"].items() if k in "ABCDEF")
        rec = {"at": rep["at"], "run": run, "engine": ENGINE, "version": VERSION, "target": src.label, "target_key": tkey,
               "profile": rep["profile"], "scopes": scopes, "sha16": sha16, "etag": etag, "verdict": verdict, "rc": rc,
               "reds": reds, "sections": {k: rep["sections"][k]["lamp"] for k in SECTIONS}, "sec": rep["sec"]}
        history = [x for x in read_ledger(ledger) if x.get("target_key") == tkey] + [rec]
        paths = {"html": str(od / "panorama_latest.html"), "json": str(latest)}
        text = render_text(rep, opts.get("width") or 140, opts.get("top") or 60)
        page = render_html(rep, history)
        (od / f"panorama_{run}.html").write_text(page, encoding="utf-8")
        (od / "panorama_latest.html").write_text(page, encoding="utf-8")
        (od / "panorama_latest.txt").write_text(text, encoding="utf-8")
        latest.write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
        with ledger.open("a", encoding="utf-8") as f:  # 只增一行(R9)
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        if opts.get("json_only"):
            print(str(latest))
        elif opts.get("rich") and rich is not None:
            render_rich(rep, opts.get("top") or 60)
            print(card(rep, paths))
        else:
            print(card(rep, paths))
        return rc
    finally:
        src.close()


def show(section: str, opts: dict) -> int:
    od = Path(opts["out"]).expanduser() if opts.get("out") else None
    cands = [od] if od else [default_target() / "VIA_Reports" / "panorama", Path.home() / ".via_panorama", Path.cwd() / ".panorama"]
    files = [c / "panorama_latest.json" for c in cands if c and (c / "panorama_latest.json").is_file()]
    if not files:
        print("[VIA_Panorama] 還沒有報告(先跑 scan)· NODATA")
        return 2
    f = max(files, key=lambda p: p.stat().st_mtime)
    rep = json.loads(f.read_text(encoding="utf-8"))
    top = opts.get("top") or 30
    width = opts.get("width") or 140
    sec = section.upper() if section.lower() != "history" else "history"
    if sec == "history":
        hist = [x for x in read_ledger(f.parent / "universal_ledger.jsonl") if x.get("target_key") == rep.get("target_key")][-top:]
        rows = [{"key": x.get("at", ""), "lamp": x.get("verdict", ""), "reds": x.get("reds", 0),
                 "sections": " ".join(f"{k}:{(x.get('sections') or {}).get(k, '')[:1]}" for k in SECTIONS), "sha16": x.get("sha16", "")} for x in hist]
        print(f"[{ENGINE} show history] {rep.get('target')} · {len(rows)} 輪")
        print(fit_table(["key", "lamp", "reds", "sections", "sha16"], rows, width, top))
        return 0
    s = rep.get("sections", {}).get(sec)
    if not s:
        print(f"[VIA_Panorama] 沒有段 {section}(A–H · history)")
        return 2
    print(f"[{ENGINE} show {sec}] {SECTION_NAMES.get(sec, sec)} · {s['lamp']} · {rep.get('target')} · {rep.get('at')} · etag {rep.get('etag')}")
    if s.get("summary"):
        print("  " + " · ".join(f"{a} {b}" for a, b in s["summary"].items() if not isinstance(b, (dict, list))))
    print(fit_table(s["cols"], s["rows"][:top] if len(s["rows"]) <= 200 else s["rows"], width, top))
    for dk, dv in (s.get("detail") or {}).items():
        if dv:
            if isinstance(dv, dict):
                for a, b in list(dv.items())[:top]:
                    print(f"  [{dk}] {a}: {len(b)} · " + " · ".join(str(x) for x in b[:5]))
            else:
                print(f"  [{dk}] {len(dv)} 項 · 前 {min(top, len(dv))}:")
                for x in dv[:top]:
                    print("    " + (json.dumps(x, ensure_ascii=False) if isinstance(x, (dict, list)) else str(x))[:200])
    return 0


def via_root() -> Path | None:
    p = default_target()
    return p if (p / "supportive modules" / "registry").is_dir() else None


def locked_tool(key: str) -> Path | None:
    """鎖版工具(不自己取尾版):VIA_ToolVersion_Lock 的 key.path。"""
    via = via_root()
    prof = load_profiles().get("via", {})
    if not via or not prof.get("tool_lock"):
        return None
    try:
        lk = json.loads((via / prof["tool_lock"]["path"]).read_text(encoding="utf-8"))
        v = lk.get(key)
        p = v.get("path") if isinstance(v, dict) else v
        return (via.parent / p) if p else None
    except Exception:
        return None


def delegate(verb: str, args: list) -> int:
    if verb == "brief":
        tool = locked_tool("nlp")
        argv = ["text", "--file", *args, "--brief"]
    else:
        tool = locked_tool("token")
        argv = [verb, *args]
    if not tool or not tool.is_file():
        print(f"[VIA_Panorama] 省 Token 工具 ABSENT(鎖冊讀不到 {verb});不自己取尾版")
        return 3
    env = {**os.environ, "VIA_FROM_VCGC": "YES"}
    return subprocess.run([sys.executable, str(tool), *argv], env=env, stdin=subprocess.DEVNULL).returncode


def verbs(opts: dict) -> int:
    """VIA 專用(會執行 VCGC 中央入口 · 明說不是只讀):每動詞只收一行判決(省 Token)。"""
    via = via_root()
    prof = load_profiles().get("via", {})
    hits = sorted(via.glob(prof.get("console_glob", "none"))) if via else []
    if not hits:
        print("[VIA_Panorama verbs] VCGC 尾版 ABSENT")
        return 3
    con = hits[-1]
    plan = [("token", ["token"], ()), ("functions", ["functions"], (2,)), ("handoff check", ["handoff", "check"], (1, 2)),
            ("sync-check", ["sync-check"], (2,)), ("check", ["check"], (2,))]
    lamps = []
    print(f"[VIA_Panorama verbs] {con.name}")
    for name, argv, yellow in plan:
        t = time.time()
        try:
            p = subprocess.run([sys.executable, str(con), *argv], cwd=str(via.parent), capture_output=True, timeout=opts.get("timeout") or 1800,
                               env={**os.environ, "VIA_FROM_VCGC": "YES", "VIA_VCGC_PUSH": "NO", "VIA_NO_OPEN": "1"}, stdin=subprocess.DEVNULL)
            rc, out = p.returncode, (p.stdout + p.stderr).decode("utf-8", "replace")
        except subprocess.TimeoutExpired:
            rc, out = 124, "逾時"
        lamp = "GREEN" if rc == 0 else ("YELLOW" if rc in yellow else "RED")
        lamps.append(lamp)
        key = [ln for ln in out.splitlines() if re.search(r"GREEN|YELLOW|RED|判定|通過|過關|紅|黃", ln)]
        print(f"  {name:<14} {lamp:<6} rc {rc} · {time.time() - t:.1f}s · {(key[-1] if key else (out.strip().splitlines() or [''])[-1])[:150]}")
    v = worst(lamps)
    print(f"  總判 {v}")
    return 1 if v == "RED" else (2 if v != "GREEN" else 0)


def parse_opts(a: list) -> tuple:
    opts, pos = {}, []
    flags = {"--static": "static", "--fetch": "fetch", "--predict": "predict", "--json-only": "json_only", "--no-git": "no_git",
             "--rich": "rich"}
    vals = {"--profile": "profile", "--scope": "scope", "--out": "out", "--top": "top", "--width": "width", "--if-etag": "if_etag",
            "--timeout": "timeout"}
    i = 0
    while i < len(a):
        x = a[i]
        if x in flags:
            opts[flags[x]] = True
        elif x in vals and i + 1 < len(a):
            v = a[i + 1]
            opts[vals[x]] = int(v) if vals[x] in ("top", "width", "timeout") and v.isdigit() else v
            i += 1
        else:
            pos.append(x)
        i += 1
    return opts, pos


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if not a or a[0] in ("scan",) or a[0].startswith("--") or a[0] not in (
            "show", "read", "slice", "digest", "pack", "chain", "brief", "verbs", "help", "-h"):
        if a and a[0] in ("--selftest", "selftest"):
            return selftest()
        if a and a[0] == "scan":
            a = a[1:]
        opts, pos = parse_opts(a)
        return run_scan(pos[0] if pos else None, opts)
    verb, rest = a[0], a[1:]
    if verb in ("help", "-h"):
        print(__doc__)
        return 0
    if verb == "show":
        opts, pos = parse_opts(rest)
        return show(pos[0] if pos else "G", opts)
    if verb == "verbs":
        return verbs(parse_opts(rest)[0])
    return delegate(verb, rest)


# ───────────────────────── 自測(零網路;暫存夾假倉) ─────────────────────────

def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  {'✓' if cond else '✗'} {name}" + (f" · {note}" if note and not cond else ""))
    import contextlib
    import io
    tmp = Path(tempfile.mkdtemp(prefix="via_pan_selftest_"))
    out = tmp / "out"
    try:
        # E1 clean:20 檔 · 3 家族 · 鎖 / 隔離區一致
        clean = tmp / "clean"
        (clean / "verb-engine" / "ssot").mkdir(parents=True)
        (clean / "verb-engine" / "engines").mkdir(parents=True)
        for fam in ("alpha", "beta", "gamma"):
            for v in (100, 101, 102):
                (clean / f"{fam}_v{v:04d}.py").write_text(f'"""{fam} v{v}"""\nX = {v}\n', encoding="utf-8")
        for n in ("e1", "e2", "e3", "e4"):
            (clean / "verb-engine" / "engines" / f"{n}.py").write_text('"""e"""\n', encoding="utf-8")
        (clean / "verb-engine" / "ssot" / "quarantine.json").write_text(json.dumps({"groups": {"g1": ["e1", "e2"], "g2": ["e3", "e4"]}, "called": False}))
        (clean / "verb-engine" / "ssot" / "lock.json").write_text(json.dumps({"names": ["e1", "e2", "e3", "e4"]}))
        for i in range(5):
            (clean / f"doc{i}.md").write_text(f"# d{i}\n", encoding="utf-8")
        before = {p: p.stat().st_mtime_ns for p in clean.rglob("*")}
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = run_scan(str(clean), {"profile": "via-verb-engine", "out": str(out / "e1"), "no_git": True})
        rep = json.loads((out / "e1" / "panorama_latest.json").read_text(encoding="utf-8"))
        holds = [r for r in rep["sections"]["D"]["rows"] if r["key"].startswith("隔離 ")]
        chk("E1 乾淨倉:20 檔 · 3 家族 · 總判非紅(棘輪首輪 NODATA → rc 2)", rc == 2 and rep["sections"]["A"]["summary"]["files"] == 20
            and rep["sections"]["A"]["summary"]["families"] == 3 and rep["verdict"] != "RED", f"rc {rc} · {rep['verdict']}")
        chk("E1 隔離項全 HOLD · Q1–Q3 綠 · Q4 綠", len(holds) == 4 and all(r["lamp"] == "HOLD" for r in holds)
            and all(r["lamp"] == "GREEN" for r in rep["sections"]["D"]["rows"] if r["key"][:2] in ("Q1", "Q2", "Q3", "Q4")))
        chk("E1 R1 目標夾 mtime 一個都沒變 · 報告不在目標底下", before == {p: p.stat().st_mtime_ns for p in clean.rglob("*")}
            and not (clean / ".panorama").exists())
        with contextlib.redirect_stdout(io.StringIO()):
            rc2 = run_scan(str(clean), {"profile": "via-verb-engine", "out": str(out / "e1"), "no_git": True})
        chk("E1 第二輪棘輪 OK → 總判 GREEN · rc 0", rc2 == 0, f"rc {rc2}")
        card_lines = buf.getvalue().strip().splitlines()
        chk("省 Token 卡 ≤ 15 行且不含原文", len(card_lines) <= 15 and "X = 100" not in buf.getvalue(), f"{len(card_lines)} 行")
        etag = json.loads((out / "e1" / "panorama_latest.json").read_text(encoding="utf-8"))["etag"]
        b2 = io.StringIO()
        n_led = len(read_ledger(out / "e1" / "universal_ledger.jsonl"))
        with contextlib.redirect_stdout(b2):
            rc3 = run_scan(str(clean), {"profile": "via-verb-engine", "out": str(out / "e1"), "no_git": True, "if_etag": etag})
        chk("--if-etag 沒變回 304 · 不重掃不增帳", "304" in b2.getvalue() and rc3 == 0
            and len(read_ledger(out / "e1" / "universal_ledger.jsonl")) == n_led, b2.getvalue()[:80])
        # E3 隔離區壞:鎖少 1 名 · 兩組重疊 1 名
        bad = tmp / "qbad"
        shutil.copytree(clean, bad)
        (bad / "verb-engine" / "ssot" / "quarantine.json").write_text(json.dumps({"groups": {"g1": ["e1", "e2"], "g2": ["e2", "e3", "e4"]}, "called": False}))
        (bad / "verb-engine" / "ssot" / "lock.json").write_text(json.dumps({"names": ["e1", "e2", "e3"]}))
        with contextlib.redirect_stdout(io.StringIO()):
            rcb = run_scan(str(bad), {"profile": "via-verb-engine", "out": str(out / "e3"), "no_git": True})
        rb = json.loads((out / "e3" / "panorama_latest.json").read_text(encoding="utf-8"))
        lam = {r["key"][:2]: r["lamp"] for r in rb["sections"]["D"]["rows"]}
        chk("E3 隔離區壞:Q1 RED · Q3 RED · rc 1 · 隔離項沒被畫綠", rcb == 1 and lam.get("Q1") == "RED" and lam.get("Q3") == "RED"
            and not q4_check(rb, rb["sections"]["D"]["quarantine_names"]), f"rc {rcb} · {lam}")
        # E4 棘輪:前一筆紅 2,本次紅 4 → RETROGRESS
        rat = tmp / "ratchet"
        rat.mkdir()
        prof = {"name": "t", "scopes": {"ALL": ["*"]}, "default_scopes": ["ALL"],
                "markers": [{"id": "MK", "ext": [".py"], "regex": "MARK", "need": True, "severity": "RED", "scopes": ["ALL"]}]}
        (tmp / "prof.json").write_text(json.dumps(prof))
        for i in range(2):
            (rat / f"m{i}.py").write_text('"""m"""\n', encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            run_scan(str(rat), {"profile": str(tmp / "prof.json"), "out": str(out / "e4"), "no_git": True})
        for i in range(2, 4):
            (rat / f"m{i}.py").write_text('"""m"""\n', encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            rcr = run_scan(str(rat), {"profile": str(tmp / "prof.json"), "out": str(out / "e4"), "no_git": True})
        rr = json.loads((out / "e4" / "panorama_latest.json").read_text(encoding="utf-8"))
        chk("E4 棘輪 紅 2 → 4 = RETROGRESS · rc 1 · 帳本只增(2 行)", rcr == 1 and rr["sections"]["G"]["summary"]["verdict"] == "RETROGRESS"
            and len(read_ledger(out / "e4" / "universal_ledger.jsonl")) == 2, f"rc {rcr} · {rr['sections']['G']['summary']}")
        # --static:語法錯分群 OP-400 · 單發 OP-500 · from __future__ 太晚
        st = tmp / "static"
        st.mkdir()
        (st / "a.py").write_text("def f(:\n  pass\n", encoding="utf-8")
        (st / "b.py").write_text("def g(:\n  pass\n", encoding="utf-8")
        (st / "c.py").write_text('"""c"""\nimport os\nfrom __future__ import annotations\n', encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            run_scan(str(st), {"profile": "generic", "out": str(out / "st"), "no_git": True, "static": True})
        rs = json.loads((out / "st" / "panorama_latest.json").read_text(encoding="utf-8"))
        f = rs["sections"]["F"]["detail"]
        chk("--static:兩檔同簽名 → OP-400 一群 · FUTURE-LATE 抓到 · 無原文", len(f["op400"]) >= 1
            and any("FUTURE" in x for x in f["op500_pack"] + list(f["op400"])) and "pass" not in json.dumps(rs, ensure_ascii=False),
            json.dumps(f, ensure_ascii=False)[:200])
        # E5 沒有 rich:三種輸出都在
        global rich
        saved, rich = rich, None
        with contextlib.redirect_stdout(io.StringIO()):
            run_scan(str(clean), {"profile": "via-verb-engine", "out": str(out / "e5"), "no_git": True, "rich": True})
        rich = saved
        chk("E5 沒有 rich:html · txt · json · 帳本都在", all((out / "e5" / n).is_file() for n in
                                                          ("panorama_latest.html", "panorama_latest.txt", "panorama_latest.json", "universal_ledger.jsonl")))
        # E2 漂移:本機 git 倉領先 2 落後 3;不 merge / checkout / stash(reflog 為證)
        dr = tmp / "drift"
        env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}

        def g(*args, cwd=dr):
            return subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, env=env)
        if shutil.which("git"):
            (tmp / "remote.git").mkdir()
            g("init", "-q", "--bare", "-b", "main", cwd=tmp / "remote.git")
            dr.mkdir()
            g("init", "-q", "-b", "main")
            (dr / "x_v0100.py").write_text('"""x"""\n', encoding="utf-8")
            g("add", ".")
            g("commit", "-q", "-m", "base")
            g("remote", "add", "origin", str(tmp / "remote.git"))
            g("push", "-q", "origin", "main")
            other = tmp / "other"
            subprocess.run(["git", "clone", "-q", str(tmp / "remote.git"), str(other)], capture_output=True, env=env)
            for i in range(3):
                (other / f"r{i}.md").write_text(f"{i}\n", encoding="utf-8")
                g("add", ".", cwd=other)
                g("commit", "-q", "-m", f"r{i}", cwd=other)
            (other / "x_v0101.py").write_text('"""x2"""\n', encoding="utf-8")
            g("add", ".", cwd=other)
            g("commit", "--amend", "-q", "--no-edit", cwd=other)
            g("push", "-q", "origin", "main", cwd=other)
            for i in range(2):
                (dr / f"l{i}.md").write_text(f"{i}\n", encoding="utf-8")
                g("add", ".")
                g("commit", "-q", "-m", f"l{i}")
            g("fetch", "-q", "origin")
            ref_before = g("reflog").stdout
            with contextlib.redirect_stdout(io.StringIO()):
                rcd = run_scan(str(dr), {"profile": "generic", "out": str(out / "e2")})
            rd = json.loads((out / "e2" / "panorama_latest.json").read_text(encoding="utf-8"))
            es = rd["sections"]["E"]["summary"]
            chk("E2 漂移:領先 2 · 落後 3 · 尾版不同 1 族 · reflog 沒變 · rc 2", es.get("ahead") == 2 and es.get("behind") == 3
                and es.get("tail_diff") == 1 and g("reflog").stdout == ref_before and rcd == 2, f"{es} rc {rcd}")
        else:
            chk("E2 漂移(git 缺席 = 跳過,不假綠)", True)
        # show:從 JSON 取一段不重掃
        b3 = io.StringIO()
        with contextlib.redirect_stdout(b3):
            rcs = show("C", {"out": str(out / "st")})
        chk("show C 從 JSON 取段(不重掃)", rcs == 0 and "show C" in b3.getvalue())
        # 目標解析
        p1 = parse_target("https://github.com/tonykuni/VIA-VERB-ENGINE/tree/main/verb-engine")
        p2 = parse_target("tonykuni/movies-dataset@dev:VeritasIntelligenceAnalytics")
        chk("目標解析:GitHub URL · owner/repo@br:sub", p1 == {"kind": "github", "owner": "tonykuni", "repo": "VIA-VERB-ENGINE",
                                                           "branch": "main", "sub": "verb-engine"}
            and p2["branch"] == "dev" and p2["sub"] == "VeritasIntelligenceAnalytics")
        # 本體:加速器橋在 · 不碰 TA-Lib · 不 import 第三方分析器 · 橋在 from __future__ 之後
        src = Path(__file__).read_text(encoding="utf-8")
        chk("本體:加速器橋在且在 __future__ 後 · 不匯入 TA-Lib / 分析器", "[VIA:ACCEL-BRIDGE" in src
            and src.index("from __future__") < src.index("[VIA:ACCEL-BRIDGE:v0100]")
            and not re.search(r"^\s*(import|from)\s+(talib|" + "|".join(ANALYZERS) + r")\b", src, re.M))
        chk("fit_table:窄 80 欄照出且每行 ≤ 80", all(dw(x) <= 80 for x in fit_table(
            ["key", "lamp", "n", "note"], [{"key": "很長的路徑/" * 12 + "x.py", "lamp": "GREEN", "n": 3, "note": "說明" * 50}], 80, 60).splitlines()))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"  {ENGINE} selftest {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
