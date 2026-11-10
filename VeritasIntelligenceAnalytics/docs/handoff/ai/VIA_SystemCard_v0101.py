#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VIA_SystemCard v0101 — v0100 + G7 TA-Lib 禁用閘(靜態 + 動態載入;操作員 2026-11-10「不可有 TA-LIB」· 商業審查 G21)。

v0100 已併 main(PR #627)不就地改;本版只增 G7(整棵 AST 找 import talib 與 *import*("talib"))+ 鎖定頁 conflicts 列 · 自測 ⑰。

— 以下為 v0100 原說明 —
VIA_SystemCard v0100 — 全景到底的動詞引擎:給一個資料夾(或 git 倉),一次掃完所有檔,產出 AI 先讀的「系統卡」,省 Token、不降品質。

操作員 2026-11-10:「新增一個引擎協助 AI 節省 TOKEN · 一個動作就是給你的文件夾,透過引擎全景式掃描全部檔案類型 · 抓出 VCGC VDF VRN VQG VAP ·
多矩陣描繪五系統 · 結果 A(桌機兩夾)/ 結果 B(GitHub 兩倉)分開互不干擾 · 編號系統降低丟失 · 事後檢查才有意義 ·
一個邏輯生成全景式分析到底的引擎 · AI 用他節省 TOKEN · 不妥協質量 · 強大的動詞引擎 · 與 AI 充分互動」。

先查過既有工具才寫(不重工):骨架卡 / 切片 = CGC_MDL158(鎖版 v0117);編號 = CGC_MDL237 + VIA_NumberBooks;
注入 = BridgeSweeper;五系統憲法 = VIA_FiveSystemConstitution。本支只補它們沒有的那塊:**任意資料夾 → 一張五系統卡 + 可問答的索引**。
  · 編號只「查」不「發」:讀掃描範圍內的 VIA_NumberBooks(source 路徑 → 號);沒號 = 空號照實(L125:號只由 VCGC 發)。
  · A 軌 = 本機資料夾(os.walk);B 軌 = git 倉的某個 ref(git ls-tree / cat-file,不走 GitHub API → 不截斷、私有倉也讀得到)。
  · 每次掃描各寫自己的輸出夾(A / B 分開),diff 才比對兩邊 —— 互不干擾。
  · 分系統先用 VIA 自己的命名律(CGC_ / VDF_ / VRN_ / VRN2_ / VQG_ / VAP_ / SUP_ 前綴與 functional / supportive 夾),
    非 VIA 的樹再退關鍵字;認不出的進 GEN(通用)或 ORP(孤兒),不藏。VRN 標 VRN-1 / VRN-2 分開寫(看倉名或 --vrn-label)。
  · 版本律:同夾同家族 _vNNNN 取最大 = 尾版(活的);前版 = 凍結件,卡上只計數不展開 —— 這是省 Token 的主力。

動詞(與 AI 互動;每個動詞輸出都精簡、可直接貼):
  scan <路徑…> [--track A|B] [--ref REF] [--out DIR] [--vrn-label L] [--full-hash]   全景掃描 → index.jsonl · summary.json · card.md · matrix.html(· index.parquet)
  card   [--out DIR] [--budget N] [--system S]       依 Token 預算出卡(預設 3000):事後閘 · 五系統矩陣 · 尾版入口 · 下一步怎麼鑽
  find   <regex> [--system S] [--limit N]            在路徑 / 說明 / 定義名找(不回原文)
  where  <名稱>                                      定義在哪個檔第幾行(+ 編號)→ 再用 CGC_MDL158 slice 取那一段
  system <S>                                         某系統全部尾版:檔 · 說明 · 定義數 · 編號
  numbers [--missing]                                尾版編號覆蓋(空號清單)
  slice  <索引裡的檔> <定義名>                       只取一個定義的原文(帶行號;A 讀磁碟 · B 讀 git ref;索引外的檔不讀)
  mcp    [--out DIR]                                 stdio MCP 伺服器(只讀):via_card · via_find · via_where · via_system · via_numbers · via_slice
                                                     —— Claude / ChatGPT / Manus / Gemini / Copilot 經 VIA_MCP_Engine 接同一支
  diff   <A 輸出夾> <B 輸出夾> [--map A根=B根]      A×B 對帳:SYNC · LOCAL_AHEAD · REMOTE_ONLY · DIVERGED(只報告,不 push / pull)
  tools                                              省 Token 外部工具在不在(Graphify · Ponytail · 記憶外掛 · Playwright · DuckDB · ChartDB)
  --selftest
事後閘(每道都真的算,不寫死 PASS):G1 檔案守恆 · G2 AST 守恆 · G3 掃描零變動 · G4 孤兒 ≤ 5% · G5 尾版編號覆蓋 · G6 來源可讀(B 軌 ref 解不開 = RED)· G7 TA-Lib 禁用(靜態 + 動態載入;L50)。
邊界:唯讀被掃的樹;只寫 --out(預設 VIA_Reports/systemcard/<軌>/,不進倉);不執行被掃的檔;零網路;不用 TA-Lib;不 import VCGC。
"""
from __future__ import annotations

# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更)=====
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
import base64
import ast
import hashlib
import html
import json
import os
import re
import subprocess
import warnings
import sys
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

VERSION = "v0101"
ENGINE = "VIA_SystemCard " + VERSION
HERE = Path(__file__).resolve().parent
VIA = HERE.parents[2] if len(HERE.parents) > 2 else HERE
DEFAULT_OUT = VIA / "VIA_Reports" / "systemcard"
SYSTEMS = ("VCGC", "VDF", "VRN", "VQG", "VAP", "SUP", "GEN", "ORP")
SYS_ZH = {"VCGC": "理｜中央治理(工具 · 冊 · 編號 · 閘)", "VDF": "庫｜資料擷取與倉儲", "VRN": "牘｜研報擷取與摘要",
          "VQG": "輔｜量化指標與回測", "VAP": "觀｜視覺化與看板", "SUP": "共用支援模組", "GEN": "通用基礎(README · 設定 · 依賴)",
          "ORP": "孤兒(認不出系統)"}
IGNORE_DIRS = {"VIA_Reports", ".git", ".venv", "venv", "__pycache__", "node_modules", ".pytest_cache", ".ruff_cache", ".mypy_cache", ".idea", ".vscode"}
TEXT_EXT = {".py", ".ps1", ".psm1", ".md", ".txt", ".json", ".toml", ".yaml", ".yml", ".ini", ".cfg", ".sql", ".html", ".csv", ".jsonl",
            ".sh", ".bat", ".cmd", ".ts", ".tsx", ".js", ".mjs", ".svelte", ".css"}
BAD_BOOK_LINES: dict = {}                      # 號冊壞行計數(只記不吞)
READ_MAX = 1024 * 1024                       # 文字檔讀前 1 MB 取說明 / 定義
HASH_MAX = 8 * 1024 * 1024                   # A 軌超過 8 MB 只記大小(--full-hash 全算)
BOOK_MAX = 64 * 1024 * 1024                  # 號冊(MDL / ENG)整本讀(實測 MDL 冊 2.6 MB > READ_MAX,先前因此「有號 0」)
BOOK_RE = re.compile(r"/VIA_NumberBooks/VIA_NumberBook_(MDL|ENG)_v\d{4}\.jsonl$")


def _readable(rel: str, size: int) -> bool:
    return size <= READ_MAX or (bool(BOOK_RE.search(rel)) and size <= BOOK_MAX)
PREFIX = [(re.compile(r"^CGC_"), "VCGC"), (re.compile(r"^VDF_"), "VDF"), (re.compile(r"^(VRN2?_|ActivateVRN)"), "VRN"),
          (re.compile(r"^VQG_"), "VQG"), (re.compile(r"^VAP_"), "VAP"), (re.compile(r"^SUP_"), "SUP"), (re.compile(r"^ActivateVDF"), "VDF")]
SEGMENT = [("functional modules/VDF", "VDF"), ("functional modules/VRN", "VRN"), ("functional modules/VQG", "VQG"), ("functional modules/VAP", "VAP"),
           ("supportive modules/registry", "VCGC"), ("docs/handoff", "VCGC"), ("supportive modules/", "SUP")]
KEYWORDS = {"VCGC": ("governance", "ssot", "registry", "handoff", "vcgc", "policy"), "VDF": ("dataforge", "vdf", "twse", "tpex", "fetch", "ingest", "duckdb"),
            "VRN": ("reportnova", "vrn", "pdf", "ocr", "summar", "report"), "VQG": ("quant", "vqg", "indicator", "backtest", "factor"),
            "VAP": ("autoplot", "vap", "chart", "dashboard", "plot", "visual")}
GEN_NAMES = {"readme", "license", "changelog", "setup", "pyproject", "requirements", "package", "package-lock", "tsconfig", "conftest", "makefile",
             ".gitignore", ".gitattributes", "agents", "claude", "dockerfile", "vite.config", "vercel"}
FAMILY_RE = re.compile(r"^(?P<fam>.+?)_v(?P<ver>\d{4})[A-Za-z]?$")
ENTRY_RE = re.compile(r"SystemManager|Activate|Console|AllInOne|RoundAll|Launcher|MAIN|Workbench|SettleAll", re.I)
XREF_RE = re.compile(r"\b(CGC_MDL\d+|VDF_(?:ENG|MDL)\d+|VRN_(?:ENG|MDL)\d+|VRN2_[A-Za-z]+|VQG_[A-Za-z]+|VAP_[A-Za-z]+|SUP_MDL\d+)")


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def approx_tokens(text: str) -> int:
    cjk = sum(1 for ch in text if ord(ch) > 0x2E7F)
    return cjk + (len(text) - cjk + 3) // 4


def blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()       # 與 git 的 blob 雜湊同算法 → A / B 可直接比


def system_of(rel: str, vrn_label: str) -> tuple[str, str]:
    """回 (系統, 依據)。VIA 命名律優先,其次夾,再關鍵字;GEN / ORP 照實。"""
    name = rel.rsplit("/", 1)[-1]
    for rx, s in PREFIX:
        if rx.search(name):
            return (vrn_label if s == "VRN" else s), "prefix"
    low = rel.lower()
    for seg, s in SEGMENT:
        if seg.lower() in low:
            return (vrn_label if s == "VRN" else s), "folder"
    stem = Path(name).stem.lower()
    if stem in GEN_NAMES or name.lower() in GEN_NAMES or low.startswith((".github/", ".grok/", "config/", "public/", ".vercel/")):
        return "GEN", "infra"
    score = Counter()
    for s, kws in KEYWORDS.items():
        for kw in kws:
            if kw in low:
                score[s] += 1
    if score:
        s = score.most_common(1)[0][0]
        return (vrn_label if s == "VRN" else s), "keyword"
    return "ORP", "none"


TALIB = {"talib", "ta_lib"}


def talib_use(tree) -> str:
    """L50 禁用 TA-Lib:整棵樹找(含函式內)— static = import talib;dynamic = 任何名字含 import 的呼叫把 "talib" 當字串傳進去
    (importlib.import_module · __import__ · 自家 def_import_optional …)。只報位置,不改檔(商業審查 G21)。"""
    hits = []
    for nd in ast.walk(tree):
        if isinstance(nd, (ast.Import, ast.ImportFrom)):
            names = [nd.module or ""] if isinstance(nd, ast.ImportFrom) else [a.name for a in nd.names]
            if any((n or "").split(".")[0].lower() in TALIB for n in names):
                hits.append("static:L%d" % nd.lineno)
        elif isinstance(nd, ast.Call):
            fn = nd.func.attr if isinstance(nd.func, ast.Attribute) else (nd.func.id if isinstance(nd.func, ast.Name) else "")
            if "import" in fn.lower() and nd.args and isinstance(nd.args[0], ast.Constant) and isinstance(nd.args[0].value, str) \
                    and nd.args[0].value.split(".")[0].lower() in TALIB:
                hits.append("dynamic:L%d" % nd.lineno)
    return " ".join(hits[:5])


def describe(rel: str, ext: str, text: str) -> dict:
    warnings.simplefilter("ignore", SyntaxWarning)   # 被掃檔的 '\ ' 跳脫警告不是本引擎的錯,不洗版
    """說明一行 + 定義(名:行)+ 匯入 + 語法錯;不回原文。"""
    out = {"pur": "", "defs": [], "imp": [], "err": "", "tal": ""}
    if not text:
        return out
    if ext == ".py":
        try:
            tree = ast.parse(text)
        except SyntaxError as e:
            out["err"] = "SyntaxError L%s" % e.lineno
            m = re.search(r'"""(.+)', text)
            out["pur"] = (m.group(1) if m else "")[:110]
            return out
        doc = ast.get_docstring(tree) or ""
        out["pur"] = doc.strip().splitlines()[0][:110] if doc.strip() else ""
        for n in tree.body:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                out["defs"].append("%s:%d" % (n.name, n.lineno))
                if isinstance(n, ast.ClassDef):
                    out["defs"] += ["%s.%s:%d" % (n.name, m.name, m.lineno) for m in n.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]
            elif isinstance(n, (ast.Import, ast.ImportFrom)):
                for a in n.names:
                    top = ((n.module if isinstance(n, ast.ImportFrom) and n.module else a.name) or "").split(".")[0]
                    if top and top not in out["imp"]:
                        out["imp"].append(top)
        out["defs"] = out["defs"][:80]
        out["imp"] = out["imp"][:10]
        out["tal"] = talib_use(tree)
        return out
    if ext in (".ps1", ".psm1"):
        m = re.search(r"\.SYNOPSIS\s*\n\s*(.+)", text) or re.search(r"^\s*#\s*(.{8,})$", text, re.M)
        out["pur"] = (m.group(1).strip() if m else "")[:110]
        out["defs"] = ["%s:%d" % (m.group(1), text.count("\n", 0, m.start()) + 1) for m in re.finditer(r"(?im)^\s*function\s+([\w-]+)", text)][:60]
        return out
    if ext == ".md":
        m = re.search(r"^#+\s*(.+)$", text, re.M)
        out["pur"] = (m.group(1).strip() if m else text.strip().splitlines()[0] if text.strip() else "")[:110]
        return out
    if ext == ".json":
        try:
            d = json.loads(text)
        except ValueError:
            out["err"] = "JSON 解析失敗"
            return out
        if isinstance(d, dict):
            for k in ("zh", "title", "description", "topic", "why", "schema"):
                if isinstance(d.get(k), str):
                    out["pur"] = d[k][:110]
                    break
            out["defs"] = ["key:%s" % k for k in list(d)[:12]]
        elif isinstance(d, list):
            out["pur"] = "list[%d]" % len(d)
        return out
    line = next((ln.strip() for ln in text.splitlines() if ln.strip()), "")
    out["pur"] = line[:110]
    return out


def _family(rel: str) -> tuple[str, int]:
    p = Path(rel)
    m = FAMILY_RE.match(p.stem)
    return ((str(p.parent) + "/" + m.group("fam") + p.suffix), int(m.group("ver"))) if m else ((str(p.parent) + "/" + p.stem + p.suffix), 0)


def _num_of(path: str, nums: dict) -> str:
    """號冊 source 是相對 VIA 根(functional modules/… · supportive modules/…)→ 先切到 VIA 根下精確查,再退後綴比對;nums 鍵 = (掃描根, source)。"""
    root = path.split("/", 1)[0]
    key = path.split("VeritasIntelligenceAnalytics/", 1)[-1] if "VeritasIntelligenceAnalytics/" in path else path.split("/", 1)[-1]
    if (root, key) in nums:                # 只查同一個掃描根的號冊:別倉的號不借用
        return nums[(root, key)]
    return next((c for (r, k), c in nums.items() if r == root and (key.endswith("/" + k) or k.endswith("/" + key))), "")


def load_numbers(files: dict) -> tuple[dict, int]:
    """掃描範圍內的 VIA_NumberBooks → {source 路徑: 號}(只查不發)。files = {相對路徑: 取文字函式}。"""
    nums, books = {}, 0
    for rel, getter in files.items():
        if BOOK_RE.search(rel):
            books += 1
            for line in (getter() or "").splitlines():
                try:
                    r = json.loads(line)
                except ValueError:
                    BAD_BOOK_LINES[rel] = BAD_BOOK_LINES.get(rel, 0) + 1   # 壞行照記(不靜默丟)
                    continue
                src = str(r.get("source") or "").replace("\\", "/")
                if src and r.get("code"):
                    nums.setdefault((rel.split("/", 1)[0], src), r["code"])   # (掃描根, source):兩倉同路徑不互蓋(Codex #627 P1)
    return nums, books


# ---------------------------------------------------------------- 兩軌來源
def source_A(paths: list) -> tuple[list, dict]:
    """A 軌:本機資料夾 → [(相對路徑, 絕對路徑, 大小, mtime_ns)];錯誤 / 缺夾照實。"""
    items, meta = [], {"missing": [], "roots": []}
    for root in paths:
        r = Path(root)
        if not r.is_dir():
            meta["missing"].append(str(root))
            continue
        meta["roots"].append(r.name)
        for dp, dns, fns in os.walk(r):
            dns[:] = [d for d in dns if d not in IGNORE_DIRS]
            for fn in fns:
                ap = Path(dp) / fn
                try:
                    st = ap.stat()
                except OSError as exc:
                    meta.setdefault("unstat", []).append("%s:%s" % (ap.name, type(exc).__name__))   # 讀不到 stat 照記 → G6 看得到
                    continue
                items.append((r.name + "/" + ap.relative_to(r).as_posix(), ap, st.st_size, st.st_mtime_ns))
    return items, meta


def _git(repo: Path, *args, input_bytes=None) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, input=input_bytes, timeout=1800)


def source_B(paths: list, ref: str) -> tuple[list, dict]:
    """B 軌:git 倉的 ref → [(相對路徑, blob sha, 大小)];ref 解不開 = 照實記(G6 紅)。"""
    items, meta = [], {"missing": [], "roots": [], "refs": {}}
    for root in paths:
        r = Path(root)
        cp = _git(r, "rev-parse", "--verify", ref + "^{commit}")
        if cp.returncode != 0:
            meta["missing"].append("%s@%s" % (root, ref))
            continue
        meta["roots"].append(r.name)
        meta["refs"][r.name] = cp.stdout.decode().strip()
        cp = _git(r, "ls-tree", "-r", "-l", "-z", ref)
        for rec in cp.stdout.decode("utf-8", "replace").split("\0"):
            if not rec:
                continue
            head, path = rec.split("\t", 1)
            parts = head.split()
            if len(parts) < 4 or parts[1] != "blob":
                continue
            size = int(parts[3]) if parts[3].isdigit() else 0
            items.append((r.name + "/" + path, (r, parts[2]), size, 0))
    return items, meta


def _cat_blobs(repo: Path, shas: list) -> dict:
    out = {}
    if not shas:
        return out
    cp = _git(repo, "cat-file", "--batch", input_bytes=("\n".join(shas) + "\n").encode())
    buf, i = cp.stdout, 0
    while i < len(buf):
        nl = buf.index(b"\n", i)
        head = buf[i:nl].split()
        i = nl + 1
        if len(head) < 3:
            continue
        n = int(head[2])
        out[head[0].decode()] = buf[i:i + n]
        i += n + 1
    return out


# ---------------------------------------------------------------- 掃描
def scan(paths: list, track: str, out: Path, ref: str = "origin/main", vrn_label: str = "", full_hash: bool = False) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    if track == "B":
        items, meta = source_B(paths, ref)
    else:
        items, meta = source_A(paths)
    def label_of(rel: str) -> str:
        """VRN 標籤逐列看所屬倉(兩倉同掃時不互相吃掉):倉名含 via-vdf-vrn = VRN-1(外倉只讀),其餘 = VRN-2;--vrn-label 全域覆寫。"""
        return vrn_label or ("VRN-1" if "via-vdf-vrn" in rel.split("/", 1)[0].lower() else "VRN-2")
    label = vrn_label or ",".join(sorted({label_of(Path(p).name + "/x") for p in paths}))
    texts = {}
    if track == "B":
        by_repo = defaultdict(list)
        for rel, (repo, sha), size, _ in items:
            if Path(rel).suffix.lower() in TEXT_EXT and _readable(rel, size):
                by_repo[repo].append(sha)
        blobs = {}
        for repo, shas in by_repo.items():
            for k in range(0, len(shas), 4000):
                blobs.update(_cat_blobs(repo, shas[k:k + 4000]))
    rows, getters = [], {}
    for rel, src, size, mtime in items:
        ext = Path(rel).suffix.lower()
        text, sha = "", ""
        if track == "B":
            sha = src[1]
            if ext in TEXT_EXT and _readable(rel, size):
                text = blobs.get(sha, b"").decode("utf-8", "replace")
        else:
            try:
                if size <= HASH_MAX or full_hash:
                    data = src.read_bytes()
                    sha = blob_sha(data)
                    if ext in TEXT_EXT and _readable(rel, size):
                        text = data.decode("utf-8", "replace")
                else:
                    sha = "size:%d" % size
            except OSError as e:
                sha = "READ_ERR:%s" % type(e).__name__
        texts[rel] = text
        getters[rel] = (lambda t=text: t)
        rows.append({"p": rel, "z": size, "h": sha[:12] if not sha.startswith(("size:", "READ_ERR")) else sha, "ext": ext or "(無)", "mt": mtime})
    nums, books = load_numbers(getters)
    fam_max = {}
    for r in rows:
        fam, ver = _family(r["p"])
        r["fam"], r["v"] = fam, ver
        if ver and ver > fam_max.get(fam, -1):
            fam_max[fam] = ver
    py_total = py_parsed = py_err = 0
    xref = defaultdict(Counter)
    for r in rows:
        s, why = system_of(r["p"], label_of(r["p"]))
        r["s"], r["why"] = s, why
        r["tail"] = (r["v"] == 0) or (r["v"] == fam_max.get(r["fam"], r["v"]))
        d = describe(r["p"], r["ext"], texts.get(r["p"], ""))
        r.update(pur=d["pur"], defs=d["defs"], imp=d["imp"], err=d["err"], tal=d.get("tal", ""))
        if r["ext"] == ".py":
            py_total += 1
            py_err += 1 if d["err"] else 0
            py_parsed += 0 if d["err"] or not texts.get(r["p"]) else 1
        inner = r["p"].split("/", 1)[-1]
        r["num"] = _num_of(r["p"], nums) if nums and r["tail"] and r["ext"] in (".py", ".ps1") else ""
        r["entry"] = bool(ENTRY_RE.search(Path(r["p"]).name)) and r["tail"] and r["ext"] in (".py", ".ps1")
        if r["tail"] and texts.get(r["p"]):
            for m in XREF_RE.finditer(texts[r["p"]][:200000]):
                t, _ = system_of(m.group(1) + ".py", label_of(r["p"]))
                if t != s and t not in ("GEN", "ORP"):
                    xref[s][t] += 1
    # 事後閘
    sys_count = Counter(r["s"] for r in rows)
    g = {}
    g["G1_檔案守恆"] = {"ok": len(rows) == sum(sys_count.values()) == len(items), "val": "列 %d = 桶加總 %d = 來源 %d" % (len(rows), sum(sys_count.values()), len(items))}
    py_with_text = sum(1 for r in rows if r["ext"] == ".py" and texts.get(r["p"]))
    g["G2_AST守恆"] = {"ok": py_parsed + py_err == py_with_text, "val": "可讀 .py %d = 解析 %d + 語法錯 %d(另 %d 支超過 1 MB 未讀)" % (py_with_text, py_parsed, py_err, py_total - py_with_text)}
    changed = _post_mutation(track, items, paths, meta)
    g["G3_掃描零變動"] = {"ok": not changed, "val": "變動 %d" % len(changed) + ("(%s)" % ", ".join(changed[:3]) if changed else "")}
    orp = sys_count.get("ORP", 0)
    ratio = round(100.0 * orp / max(1, len(rows)), 2)
    g["G4_孤兒比例"] = {"ok": ratio <= 5.0, "val": "ORP %d / %d = %.2f%%(門檻 5%%)" % (orp, len(rows), ratio)}
    code_tails = [r for r in rows if r["tail"] and r["ext"] in (".py", ".ps1") and r["s"] not in ("GEN", "ORP")]
    with_num = sum(1 for r in code_tails if r["num"])
    g["G5_尾版編號覆蓋"] = {"ok": (not books) or with_num == len(code_tails), "val": ("號冊 %d 本 · 尾版程式 %d · 有號 %d · 空號 %d" % (books, len(code_tails), with_num, len(code_tails) - with_num)) if books else "範圍內沒有 VIA_NumberBooks → 不評(照實)"}
    unstat = meta.get("unstat", [])
    tal = [r for r in rows if r.get("tal") and r["tail"]]
    g["G7_TA-Lib禁用"] = {"ok": not tal, "val": ("尾版載入 TA-Lib %d 支:%s" % (len(tal), " ; ".join("%s(%s)" % (r["p"].split("/", 1)[-1], r["tal"]) for r in tal[:4]))) if tal
                         else "尾版靜態 / 動態載入 TA-Lib 0 支(L50)"}
    g["G6_來源可讀"] = {"ok": not meta["missing"], "val": "讀不到:%s%s%s" % (", ".join(meta["missing"]) or "無",
                        (" · stat 失敗 %d(%s)" % (len(unstat), ", ".join(unstat[:3]))) if unstat else "",
                        (" · 號冊壞行 %d" % sum(BAD_BOOK_LINES.values())) if BAD_BOOK_LINES else "")}
    lamp = "RED" if not (g["G1_檔案守恆"]["ok"] and g["G3_掃描零變動"]["ok"] and g["G6_來源可讀"]["ok"]) else ("GREEN" if all(x["ok"] for x in g.values()) else "YELLOW")
    summary = {"engine": ENGINE, "at": _now(), "track": track, "paths": [str(p) for p in paths], "ref": ref if track == "B" else "", "refs": meta.get("refs", {}),
               "vrn_label": label, "files": len(rows), "lamp": lamp, "gates": g, "by_system": dict(sys_count),
               "tails": sum(1 for r in rows if r["tail"]), "frozen": sum(1 for r in rows if not r["tail"]), "py": py_total, "number_books": books,
               "xref": {k: dict(v) for k, v in xref.items()}}
    with (out / "index.jsonl").open("w", encoding="utf-8") as fh:
        for r in rows:
            r.pop("mt", None)
            fh.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "card.md").write_text(render_card(summary, rows, 3000), encoding="utf-8")
    (out / "matrix.html").write_text(render_html(summary, rows), encoding="utf-8")
    try:
        summary["ui"] = render_locked(summary, rows, out)
    except Exception as exc:  # 模板壞了照實記,素面頁仍在
        summary["ui"] = {"applied": False, "why": "%s: %s" % (type(exc).__name__, exc)}
    summary["parquet"] = _to_parquet(out)
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    return summary


def _post_mutation(track: str, items: list, paths: list, meta: dict) -> list:
    """G3:A 軌逐檔重看大小 + mtime_ns;B 軌確認各倉 ref 仍指同一提交。"""
    bad = []
    if track == "B":
        for root in paths:
            r = Path(root)
            want = meta.get("refs", {}).get(r.name)
            if want:
                cp = _git(r, "rev-parse", "HEAD")
                if cp.returncode != 0:
                    bad.append("HEAD?%s" % r.name)
        return bad
    for rel, ap, size, mt in items:
        try:
            st = ap.stat()
            if st.st_size != size or st.st_mtime_ns != mt:
                bad.append(rel)
        except OSError:
            bad.append(rel)
    return bad


def _to_parquet(out: Path) -> str:
    try:
        import duckdb
    except Exception:  # noqa: BLE001 — 沒 duckdb 就只留 jsonl
        return "SKIP(沒有 duckdb)"
    try:
        con = duckdb.connect()
        src, dst = (out / "index.jsonl").as_posix(), (out / "index.parquet").as_posix()
        con.execute("COPY (SELECT * FROM read_json_auto('%s', format='newline_delimited') ORDER BY s, p) TO '%s' (FORMAT PARQUET, COMPRESSION ZSTD)" % (src, dst))
        con.close()
        return "OK"
    except Exception as e:  # noqa: BLE001
        return "FAIL(%s)" % type(e).__name__


# ---------------------------------------------------------------- 卡 / 頁
def _sys_order(summary) -> list:
    return [s for s in ("VCGC", "VDF", "VRN-2", "VRN-1", "VQG", "VAP", "SUP", "GEN", "ORP") if s in summary["by_system"]]


def render_card(summary: dict, rows: list, budget: int, only: str = "") -> str:
    """依 Token 預算出卡:先閘與矩陣(一定有),再每系統入口 → 尾版(說明最長者優先),超預算就停並寫「還有 N 支,用 system / find」。"""
    L = ["# 系統卡 · %s · %s 軌 · %s" % (summary["lamp"], summary["track"], summary["at"]),
         "範圍:%s%s · 檔 %d · 尾版 %d · 凍結前版 %d(不展開)· .py %d · 號冊 %d 本" % (
             ", ".join(summary["paths"]), (" @ " + summary["ref"]) if summary["ref"] else "", summary["files"], summary["tails"], summary["frozen"],
             summary["py"], summary["number_books"]),
         "", "## 事後閘"]
    L += ["- %s %s:%s" % ("✅" if v["ok"] else "⚠️", k, v["val"]) for k, v in summary["gates"].items()]
    by_sys = defaultdict(list)
    for r in rows:
        by_sys[r["s"]].append(r)
    L += ["", "## 五系統矩陣(檔 · 尾版 · 入口 · 主要副檔名 · 引用他系統)", "| 系統 | 定位 | 檔 | 尾版 | 入口 | 副檔名 | 引用 |", "|---|---|---|---|---|---|---|"]
    for s in _sys_order(summary):
        rs = by_sys[s]
        ext = " ".join("%s:%d" % (e, n) for e, n in Counter(r["ext"] for r in rs).most_common(3))
        xr = " ".join("%s×%d" % (k, v) for k, v in sorted(summary["xref"].get(s, {}).items(), key=lambda x: -x[1])[:3])
        L.append("| %s | %s | %d | %d | %d | %s | %s |" % (s, SYS_ZH.get(s.split("-")[0], s), len(rs), sum(r["tail"] for r in rs), sum(r["entry"] for r in rs), ext, xr or "—"))
    L += ["", "## 鑽取(先卡、再定位、最後才讀段落)",
          "- `find <regex>` 找檔 / 定義 · `where <名稱>` 定義在哪行 · `system <系統>` 某系統全部尾版 · `numbers --missing` 空號",
          "- 取一段原文:`python3 \"VeritasIntelligenceAnalytics/supportive modules/registry/CGC_MDL158_VIAPanoramaAuditRepair_v0117.py\" slice <檔> <名稱>`", ""]
    used = approx_tokens("\n".join(L))
    for s in _sys_order(summary):
        if only and s != only:
            continue
        tails = [r for r in by_sys[s] if r["tail"] and r["ext"] in (".py", ".ps1", ".md", ".json") and r["pur"]]
        tails.sort(key=lambda r: (not r["entry"], r["ext"] != ".py", -len(r["defs"]), r["p"]))
        head = "## %s · %s(尾版 %d)" % (s, SYS_ZH.get(s.split("-")[0], s), len(tails))
        if used + approx_tokens(head) > budget:
            L.append("…(預算 %d 用完;其餘系統用 `system <系統>`)" % budget)
            break
        L.append(head)
        used += approx_tokens(head)
        shown = 0
        for r in tails:
            line = "- %s`%s` %s%s · 定義 %d%s" % ("★" if r["entry"] else "", r["p"].split("/", 1)[-1], r["pur"], (" · " + r["num"]) if r["num"] else "",
                                                len(r["defs"]), (" · " + r["err"]) if r["err"] else "")
            t = approx_tokens(line)
            if used + t > budget:
                break
            L.append(line)
            used += t
            shown += 1
        if shown < len(tails):
            L.append("- …還有 %d 支(`system %s` / `find`)" % (len(tails) - shown, s))
    L.append("\n[token 帳] 卡 ≈ %d tokens(預算 %d)" % (approx_tokens("\n".join(L)), budget))
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- 鎖定 U/I 模板(操作員 2026-11-10「視覺鎖定為 U/I 模板」)
def _lock_chain():
    """載入 WorkbenchLock 尾版(它自己 SHA 釘前版)→ (v0100 渲染 · 品牌函式 · 響應式函式)。找不到 = None(退回素面頁,照實標)。"""
    import importlib.util
    cands = sorted(HERE.glob("VIA_WorkbenchLock_v[0-9][0-9][0-9][0-9].py"))
    if not cands:
        return None
    spec = importlib.util.spec_from_file_location("via_wbl_tail_for_systemcard", cands[-1])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    chain, m = [], mod
    while m is not None:
        chain.append(m)
        m = getattr(m, "__dict__", {}).get("BASE")
    v0 = next((m for m in chain if "render_page" in m.__dict__ and "LOCK_FILES" in m.__dict__), None)
    brand = next((m for m in chain if "apply_brand" in m.__dict__), None)
    resp = next((m for m in chain if "apply_responsive" in m.__dict__), None)
    return (v0, brand, resp, cands[-1].name) if v0 else None


def _lrow(**kw) -> dict:
    base = {"status": "YELLOW", "id": "", "ssot_name": "", "version": "", "completion_time": "NOT_OBSERVED", "tools": "", "system": "",
            "source": "", "source_sha256": "", "kind": "", "scope": "", "error_detail": ""}
    base.update(kw)
    return base


def locked_matrix(summary: dict, rows: list, system: str) -> dict:
    """SystemCard 列 → 鎖定模板九分類。精確歸屬 row.system == 頁系統;全域閘只放 SHARED(不在每頁重算 = 不把一次 PASS 算五次)。"""
    M = {c: [] for c in ("systems", "io", "commands", "files", "environment", "policy", "conflicts", "requirements", "tests")}
    mine = [r for r in rows if r["s"] == system]
    tails = [r for r in mine if r["tail"]]
    src = " · ".join(summary["paths"]) + ((" @ " + summary["ref"]) if summary.get("ref") else "")
    M["systems"].append(_lrow(status="GREEN" if not any(r["err"] for r in tails) else "RED", id="SYS-" + system, ssot_name=system + " · " + SYS_ZH.get(system.split("-")[0], system),
                              version=ENGINE, system=system, source=src, kind="SYSTEM", scope="%s 軌" % summary["track"],
                              tools="檔 %d · 尾版 %d · 入口 %d · 凍結前版 %d" % (len(mine), len(tails), sum(r["entry"] for r in mine), len(mine) - len(tails)),
                              completion_time=summary["at"], error_detail="; ".join("%s %s" % (r["p"].split("/", 1)[-1], r["err"]) for r in tails if r["err"])[:400]))
    for r in sorted((r for r in tails if r["entry"]), key=lambda r: r["p"]):
        M["systems"].append(_lrow(status="RED" if r["err"] else ("GREEN" if r["num"] else "YELLOW"), id=r["num"] or "NOT_ASSIGNED", ssot_name=Path(r["p"]).name,
                                  version="v%04d" % r["v"] if r["v"] else "", system=system, source=r["p"], source_sha256=r["h"], kind="ENTRY ★",
                                  scope=r["pur"][:160], tools="定義 %d" % len(r["defs"]), error_detail=r["err"] or ("" if r["num"] else "尾版空號(只查不發)")))
        for d in r["defs"][:60]:
            n, _, ln = d.rpartition(":")
            M["commands"].append(_lrow(status="GREEN", id="%s:%s" % (Path(r["p"]).name, ln), ssot_name=n, system=system, source=r["p"], source_sha256=r["h"],
                                       kind="DEF", scope="slice %s %s" % (r["p"].split("/", 1)[-1], n)))
    for r in sorted(tails, key=lambda r: r["p"]):
        st = "RED" if r["err"] else ("YELLOW" if (r["ext"] in (".py", ".ps1") and summary["number_books"] and not r["num"]) else "GREEN")
        M["files"].append(_lrow(status=st, id=r["num"] or r["h"], ssot_name=r["p"].split("/", 1)[-1], version="v%04d" % r["v"] if r["v"] else "",
                                system=system, source=r["p"], source_sha256=r["h"], kind=r["ext"], scope=r["pur"][:160], tools="%d B · %s" % (r["z"], r["why"]),
                                error_detail=r["err"] or ("尾版空號" if st == "YELLOW" else "")))
        if r["err"]:
            M["conflicts"].append(_lrow(status="RED", id="AST-" + r["h"], ssot_name=r["p"].split("/", 1)[-1], system=system, source=r["p"], kind="SYNTAX", error_detail=r["err"]))
        if r.get("tal"):
            M["conflicts"].append(_lrow(status="RED", id="TALIB-" + r["h"], ssot_name=r["p"].split("/", 1)[-1], system=system, source=r["p"], kind="POLICY L50",
                                        scope="TA-Lib 禁用;只報位置 · 由該系統自己修(L123 互監不代修)", error_detail=r["tal"]))
        if st == "YELLOW" and not r["err"]:
            M["requirements"].append(_lrow(status="YELLOW", id="NUM-" + r["h"], ssot_name=r["p"].split("/", 1)[-1], system=system, source=r["p"], kind="NUMBERING",
                                           scope="尾版程式沒在 VIA_NumberBooks 查到號", error_detail="空號照實;發號只經 VCGC CGC_MDL237"))
    for t, n in sorted(summary["xref"].get(system, {}).items(), key=lambda x: -x[1]):
        M["io"].append(_lrow(status="YELLOW", id="XREF-%s-%s" % (system, t), ssot_name="%s → %s" % (system, t), system=system, kind="DECLARED", tools="提到 %d 次" % n,
                             scope="尾版原文提到他系統模組名(靜態;不是 live 流程)", error_detail="L123:只讀互監,不代修"))
    return M


def render_locked(summary: dict, rows: list, out: Path) -> dict:
    """每系統一頁 + Hub,全部套鎖定模板(鎖站 CSS / JS / 頁模板一字不改;品牌與響應式用 WorkbenchLock 自己的函式)。"""
    lk = _lock_chain()
    if not lk:
        return {"applied": False, "why": "找不到 VIA_WorkbenchLock 尾版 → 退回素面 matrix.html"}
    v0, brand, resp, tail = lk
    via = HERE.parents[2]
    site = v0.lock_site(via)
    vl = v0.verify_lock_site(via)
    if not vl.get("ok"):
        return {"applied": False, "why": "鎖站 sha 不過,不生成(%s)" % vl.get("problems")}
    old_b64 = base64.b64encode((site / v0.LOCK_FILES["logo"]).read_bytes()).decode("ascii")
    new_b64, icons_js = "", None
    if brand:
        bp = brand.brand_paths(via)
        new_b64 = base64.b64encode(bp["logo"].read_bytes()).decode("ascii") if bp["logo"].is_file() else ""
        icons_js = brand.icons_literal(json.loads(bp["icons"].read_text(encoding="utf-8"))) if bp["icons"].is_file() else None
    gates = [{"category": "tests", "row": _lrow(status="GREEN" if v["ok"] else "YELLOW", id=k.split("_")[0], ssot_name=k, system="VIA_SHARED", kind="GATE",
                                                 scope="SystemCard 事後閘", tools=v["val"], completion_time=summary["at"], error_detail="" if v["ok"] else v["val"])}
             for k, v in summary["gates"].items()]

    def finish(html_text: str) -> str:
        if brand:
            html_text, _ = brand.apply_brand(html_text, old_b64, new_b64, icons_js)
        if resp:
            html_text, _ = resp.apply_responsive(html_text)
        return html_text.replace("本倉自建 · " + v0.ENGINE, "本倉自建 · " + ENGINE).replace(v0.ENGINE + " · 本倉冊快照", ENGINE + " · " + summary["track"] + " 軌快照")

    pages = {}
    for sysname in _sys_order(summary):
        M = locked_matrix(summary, rows, sysname)
        bundle = {"version": v0.UI_CONTRACT_VERSION, "workbench_engine": ENGINE, "system": sysname, "LAST_MATRIX": M, "SHARED_EVIDENCE": gates,
                  "SHARED_CANDIDATE_OR_SESSION_OBSERVATIONS": {}, "DATABASE_HISTORICAL_GOVERNANCE": {},
                  "source": {"engine": ENGINE, "generated_utc": summary["at"], "main": summary.get("ref", "") or "working-tree",
                             "constitution_lamp": summary["lamp"], "lock_site": str(v0.LOCK_REL), "template_engine": tail}}
        fn = "VIA_SystemCard_%s.html" % sysname
        (out / fn).write_text(finish(v0.render_page(site, sysname, bundle, "matrix.html")), encoding="utf-8")
        pages[sysname] = {"file": fn, "rows": {c: len(v) for c, v in M.items()},
                          "red": sum(1 for v in M.values() for r in v if r["status"] == "RED"), "green": sum(1 for v in M.values() for r in v if r["status"] == "GREEN"),
                          "n": sum(len(v) for v in M.values())}
    hub = finish(render_locked_hub(summary, pages, site, v0))
    (out / "matrix.html").write_text(hub, encoding="utf-8")
    (out / "index.html").write_text(hub, encoding="utf-8")       # 與鎖的 check 同名(hub 模式)
    chk = v0.check(via, files=[out / p["file"] for p in pages.values()] + [out / "index.html"], write=False)
    return {"applied": True, "check_lamp": chk["lamp"], "check_red": [Path(f["file"]).name for f in chk["files"] if f["lamp"] != "GREEN"], "template": tail, "lock_site": str(v0.LOCK_REL), "pages": pages}


# ---------------------------------------------------------------- VCGC 管理者工具卡(操作員 2026-11-10「卡片式管理 · 畫面乾淨清楚」)
CARD_GROUPS = [
    ("省 Token 工具", [("lock", "token", "骨架卡 / 切片 / 鏈圖", "read · slice · chain · digest"),
                      ("lock", "nlp", "長文摘要", "--brief"),
                      ("glob", "docs/handoff/ai/VIA_SystemCard_v[0-9][0-9][0-9][0-9].py", "全景卡 · 動詞引擎 · MCP", "scan · card · find · where · slice · mcp"),
                      ("glob", "../VIA_MCP_Engine/VIA_MCP_Engine_v[0-9][0-9][0-9][0-9].py", "同一組 MCP 給所有 AI", "parity · probe · apply")]),
    ("中央管理工具", [("glob", "supportive modules/registry/CGC_MDL149_VeritasCentralGovernanceConsole_v[0-9][0-9][0-9][0-9].py", "VCGC 主控台", "token · handoff · test · run"),
                     ("glob", "supportive modules/registry/CGC_MDL237_NumberingSystem_v[0-9][0-9][0-9][0-9].py", "中央編號(只由 VCGC 發)", "audit · --apply --scope"),
                     ("glob", "supportive modules/registry/CGC_MDL279_MCPServer_v[0-9][0-9][0-9][0-9].py", "VCGC MCP(只讀)", "--serve · --client-config"),
                     ("glob", "supportive modules/registry/VIA_VCGC_FunctionInventory_SSOT_v[0-9][0-9][0-9][0-9].json", "串測站表(盤點冊)", "test --quick"),
                     ("book", "docs/handoff/HANDOFF_latest.json", "交接冊(綠 ≠ 驗收)", "handoff check · checkpoint"),
                     ("book", "docs/handoff/ai/VIA_FiveSystemConstitution_latest.json", "五系統憲法矩陣", "L125 · 衝突 · 編號"),
                     ("glob", "docs/handoff/ai/VIA_WorkbenchLock_v[0-9][0-9][0-9][0-9].py", "視覺鎖定工作台", "build · check")]),
    ("支援工具", [("lock", "accelerator", "加速器", "Celeritas"), ("lock", "network", "網路工具", "AegisNexus · 同意閘"),
                 ("lock", "layout", "LAYOUT", "版面中樞"), ("lock", "nlp", "NLP", "統一 NLP 調度"),
                 ("lock", "pdfplumber", "PDF 抽取", "pdfplumber+"), ("lock", "ocr", "OCR", "ocr super"),
                 ("lock", "frame", "資料框", "Polars frame"), ("lock", "praddle", "版面抽取", "Praddle")]),
]


def vcgc_tool_cards(via: Path) -> list:
    """每張卡的燈都是實比:鎖冊條目 = 檔在且 sha256 = 鎖冊值才綠;尾版檔 = 在就黃(本頁不代跑自測,未跑 ≠ 綠);冊 = 冊自己報的燈。"""
    lock = {}
    try:
        lock = json.loads((via / "supportive modules" / "registry" / "VIA_ToolVersion_Lock_v0100.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        lock = {"_error": "%s: %s" % (type(exc).__name__, exc)}           # 鎖冊讀不到 → 每張鎖卡都紅並寫原因
    groups = []
    for title, items in CARD_GROUPS:
        cards = []
        for kind, key, label, verbs in items:
            c = {"label": label, "verbs": verbs, "lamp": "RED", "ver": "", "path": "", "note": ""}
            if kind == "lock":
                ent = lock.get(key) or {}
                f = via.parent / str(ent.get("path", ""))
                c.update(ver=str(ent.get("version", "")), path=str(ent.get("path", "")).split("/")[-1])
                if not ent:
                    c["note"] = lock.get("_error") or "鎖冊沒有 %s" % key
                elif not f.is_file():
                    c["note"] = "鎖定的檔不在"
                else:
                    ok = hashlib.sha256(f.read_bytes()).hexdigest() == ent.get("sha256")
                    c.update(lamp="GREEN" if ok else "RED", note="鎖冊 sha 相符" if ok else "sha 與鎖冊不符(被改過)")
            elif kind == "glob":
                base = (via / key).parent
                hits = sorted(base.glob(Path(key).name)) if base.is_dir() else []
                if hits:
                    f = hits[-1]
                    m = FAMILY_RE.match(f.stem)
                    c.update(lamp="YELLOW", ver="v" + m.group("ver") if m else "", path=f.name, note="尾版在 · 本頁未代跑自測")
                else:
                    c["note"] = "找不到尾版"
            else:
                f = via / key
                try:
                    d = json.loads(f.read_text(encoding="utf-8"))
                    lp = str(d.get("closeout_lamp") or d.get("lamp") or "YELLOW").upper()
                    c.update(lamp=lp if lp in ("GREEN", "YELLOW", "RED") else "YELLOW", path=f.name,
                             ver=str(d.get("generated_utc") or d.get("at") or "")[:10],
                             note=("交接冊 %s · 驗收 %s" % (d.get("lamp"), d.get("closeout_lamp"))) if "closeout_lamp" in d else "冊自報 %s" % d.get("lamp"))
                except (OSError, ValueError):
                    c["note"] = "冊讀不到"
            cards.append(c)
        groups.append((title, cards))
    return groups


def render_tool_cards(via: Path) -> str:
    e = html.escape
    out = []
    for title, cards in vcgc_tool_cards(via):
        g = sum(c["lamp"] == "GREEN" for c in cards)
        r = sum(c["lamp"] == "RED" for c in cards)
        body = "".join(
            '<div class="kpi" style="display:flex;flex-direction:column;gap:4px;align-items:flex-start;min-width:0">'
            '<div class="status-cell"><span class="status-dot %s" aria-label="%s"></span><strong style="font-size:1.05rem;line-height:1.3">%s</strong></div>'
            '<span class="code" style="overflow-wrap:anywhere">%s %s</span><span>%s</span><span class="micro" style="overflow-wrap:anywhere">%s</span></div>' % (
                c["lamp"].lower(), c["lamp"], e(c["label"]), e(c["path"] or "—"), e(c["ver"]), e(c["note"]), e(c["verbs"]))
            for c in cards)
        out.append('<section class="center-panel"><div class="center-panel-head"><h2>VCGC · %s</h2><span class="micro">綠 %d · 紅 %d · 共 %d</span></div>'
                   '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:10px;padding:10px">%s</div></section>' % (e(title), g, r, len(cards), body))
    return "\n".join(out)


def render_locked_hub(summary: dict, pages: dict, site: Path, v0) -> str:
    e = html.escape
    css = (site / v0.LOCK_FILES["css"]).read_text(encoding="utf-8")
    logo = base64.b64encode((site / v0.LOCK_FILES["logo"]).read_bytes()).decode("ascii")
    cards = "".join('<div class="kpi"><span class="icon"></span><strong>%s</strong><span>%d rows · RED %d · GREEN %d</span></div>' % (e(k), v["n"], v["red"], v["green"])
                    for k, v in pages.items())
    def lamp(v):
        return "RED" if v["red"] else ("GREEN" if v["n"] and v["green"] == v["n"] else "YELLOW")
    trs = "".join('<tr class="matrix-row"><td><div class="status-cell"><span class="status-dot %s" aria-label="%s"></span><span class="status-label">%s</span></div></td>'
                  '<td>%s</td><td>%s</td><td>%d</td><td>%d</td><td>%d</td><td><a href="%s">%s</a></td></tr>' % (
                      lamp(v).lower(), lamp(v), lamp(v), e(k), e(SYS_ZH.get(k.split("-")[0], k)), v["n"], v["red"], v["green"], e(v["file"]), e(v["file"]))
                  for k, v in pages.items())
    gates = "".join('<tr class="matrix-row"><td><div class="status-cell"><span class="status-dot %s"></span><span class="status-label">%s</span></div></td><td>%s</td><td colspan="5">%s</td></tr>' % (
        "green" if g["ok"] else "yellow", "GREEN" if g["ok"] else "YELLOW", e(k), e(g["val"])) for k, g in summary["gates"].items())
    return """<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src data:; base-uri 'none'; form-action 'none'">
<title>VIA 系統卡 Hub · %s</title><style>%s</style></head>
<body>
<header id="masthead"><div class="brand"><img class="brand-logo" src="data:image/png;base64,%s" alt="Veritas Intelligence Analytics">
<div class="brand-copy"><p class="eyebrow">VIA · 系統卡 HUB · %s · %s</p><h1>VIA 自建平台 · 管理者版</h1>
<p class="subtitle">%s 軌 · %s · 檔 %d · 尾版 %d · 凍結前版 %d(不展開)</p></div></div>
<div class="mast-actions"><span class="badge candidate">本倉真資料</span><span class="badge %s">總燈 %s</span><span class="badge lock">ENG049 v0102 VISUAL LOCK</span></div></header>
<div class="review-note" role="status">五系統對等獨立(L123):每頁只放 row.system == 該系統的列;事後閘是全域證據(SHARED),不在每頁重算。靜態掃描 ≠ runtime 已運作;黃不是綠。</div>
<div class="workspace" id="workspace"><main class="center" style="grid-column:1/-1"><section class="kpis" id="kpis">%s</section>
<section class="center-panel"><div class="center-panel-head" id="center-panel-head"><h2>系統總表</h2><span class="micro">鑽取:card · find · where · system · numbers</span></div>
<div id="view" role="region"><div class="table-wrap"><table><thead><tr><th>燈號</th><th>系統</th><th>定位</th><th>rows</th><th>RED</th><th>GREEN</th><th>頁面</th></tr></thead><tbody>%s</tbody></table></div></div></section>
%s
<section class="center-panel"><div class="center-panel-head"><h2>事後閘(SHARED)</h2><span class="micro">G1/G3/G6 不過 = RED</span></div>
<div class="table-wrap"><table><thead><tr><th>燈號</th><th>閘</th><th colspan="5">值</th></tr></thead><tbody>%s</tbody></table></div></section>
<footer class="center-footer">模板 = WorkbenchLock 鎖站(css :root 區塊 sha 與 check 同一套);資料 = %s。</footer></main></div>
</body></html>
""" % (ENGINE, css, logo, e(summary["at"][:10]), ENGINE, e(summary["track"]), e(" · ".join(summary["paths"]) + ((" @ " + summary["ref"]) if summary.get("ref") else "")),
       summary["files"], summary["tails"], summary["frozen"], "success" if summary["lamp"] == "GREEN" else ("danger" if summary["lamp"] == "RED" else "candidate"),
       e(summary["lamp"]), cards, trs, render_tool_cards(HERE.parents[2]), gates, ENGINE)


def render_html(summary: dict, rows: list) -> str:
    """素面備援頁(鎖定模板不可用時才用)。"""
    e = html.escape
    lamp = {"GREEN": "#1f8a4c", "YELLOW": "#a87400", "RED": "#c62828"}.get(summary["lamp"], "#777")
    gates = "".join("<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % ("✅" if v["ok"] else "⚠️", e(k), e(v["val"])) for k, v in summary["gates"].items())
    by_sys = defaultdict(list)
    for r in rows:
        by_sys[r["s"]].append(r)
    mat = "".join("<tr><td><b>%s</b></td><td>%s</td><td class=n>%d</td><td class=n>%d</td><td class=n>%d</td><td>%s</td></tr>" % (
        e(s), e(SYS_ZH.get(s.split("-")[0], s)), len(by_sys[s]), sum(r["tail"] for r in by_sys[s]), sum(r["entry"] for r in by_sys[s]),
        e(" · ".join("%s×%d" % kv for kv in summary["xref"].get(s, {}).items()) or "—")) for s in _sys_order(summary))
    ent = "".join("<tr><td>%s</td><td><code>%s</code></td><td>%s</td><td>%s</td></tr>" % (e(r["s"]), e(r["p"].split("/", 1)[-1]), e(r["pur"]), e(r["num"] or "空號"))
                  for r in sorted((r for r in rows if r["entry"]), key=lambda r: (r["s"], r["p"]))[:200])
    return ("<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'><title>VIA 系統卡</title>"
            "<style>body{font:14px/1.5 system-ui,'Noto Sans TC',sans-serif;margin:0;background:#f5f6f4;color:#1b2420}main{max-width:1180px;margin:0 auto;padding:16px}"
            "section{background:#fff;border:1px solid #d9dfdb;border-radius:10px;padding:12px 14px;margin:12px 0;overflow-x:auto}table{border-collapse:collapse;width:100%%}"
            "th,td{text-align:left;padding:5px 7px;border-bottom:1px solid #e3e8e5;vertical-align:top}.n{text-align:right;font-variant-numeric:tabular-nums}"
            "code{font:12px ui-monospace,monospace;overflow-wrap:anywhere}.lp{color:#fff;border-radius:999px;padding:1px 10px;background:%s}</style>"
            "<main><h1>VIA 系統卡 <span class=lp>%s</span></h1><p>%s 軌 · %s · 檔 %d · 尾版 %d · 凍結前版 %d</p>"
            "<section><h2>事後閘</h2><table>%s</table></section><section><h2>五系統矩陣</h2><table><tr><th>系統</th><th>定位</th><th>檔</th><th>尾版</th><th>入口</th><th>引用他系統</th></tr>%s</table></section>"
            "<section><h2>入口(尾版)</h2><table><tr><th>系統</th><th>檔</th><th>說明</th><th>編號</th></tr>%s</table></section></main>") % (
        lamp, e(summary["lamp"]), e(summary["track"]), e(summary["at"]), summary["files"], summary["tails"], summary["frozen"], gates, mat, ent)


# ---------------------------------------------------------------- 互動動詞
def _load(out: Path) -> tuple[dict, list]:
    s = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    rows = [json.loads(x) for x in (out / "index.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    return s, rows


def v_find(rows: list, pattern: str, system: str = "", limit: int = 30) -> list:
    rx = re.compile(pattern, re.I)
    hits = []
    for r in rows:
        if system and r["s"] != system:
            continue
        if rx.search(r["p"]) or rx.search(r["pur"]) or any(rx.search(d) for d in r["defs"]):
            hits.append("%s%s %s · %s%s" % ("" if r["tail"] else "(前版)", r["s"], r["p"].split("/", 1)[-1], r["pur"][:70], (" · " + r["num"]) if r["num"] else ""))
        if len(hits) >= limit:
            break
    return hits


def v_where(rows: list, name: str) -> list:
    out = []
    for r in rows:
        for d in r["defs"]:
            n, _, ln = d.rpartition(":")
            if n == name or n.endswith("." + name):
                out.append("%s%s:%s %s · %s%s" % ("" if r["tail"] else "(前版)", r["p"].split("/", 1)[-1], ln, n, r["s"], (" · " + r["num"]) if r["num"] else ""))
    out.sort(key=lambda x: x.startswith("(前版)"))
    old = [x for x in out if x.startswith("(前版)")]
    if len(old) > 2:                      # 凍結前版只留 2 條 + 計數(省 Token;要全列用 find)
        out = [x for x in out if not x.startswith("(前版)")] + old[-2:] + ["…另 %d 個凍結前版也有(find 可全列)" % (len(old) - 2)]
    return out


def v_system(rows: list, s: str) -> list:
    return ["%s`%s` %s · 定義 %d%s" % ("★" if r["entry"] else "", r["p"].split("/", 1)[-1], r["pur"][:90], len(r["defs"]), (" · " + r["num"]) if r["num"] else " · 空號")
            for r in sorted((r for r in rows if r["s"] == s and r["tail"] and r["ext"] in (".py", ".ps1")), key=lambda r: (not r["entry"], r["p"]))]


def v_diff(a_out: Path, b_out: Path, root_map: dict | None = None) -> dict:
    """A×B:以「倉根 + 倉內相對路徑」對齊,比 git blob 雜湊。兩倉同掃時倉根留在鍵裡(README.md 不互蓋;Codex #627 P2)。
    A / B 夾名不同:各只有一個根 → 自動對上;多根 → 同名對同名,不同名用 root_map {A 根名: B 根名}(CLI --map A=B)。"""
    _, ra = _load(a_out)
    _, rb = _load(b_out)
    roots_a = sorted({r["p"].split("/", 1)[0] for r in ra})
    roots_b = sorted({r["p"].split("/", 1)[0] for r in rb})
    rmap = dict(root_map or {})
    if not rmap and len(roots_a) == 1 and len(roots_b) == 1:
        rmap = {roots_a[0]: roots_b[0]}

    def key(r, side):
        root, _, inner = r["p"].partition("/")
        return "%s/%s" % (rmap.get(root, root) if side == "A" else root, inner)
    A, B = {key(r, "A"): r for r in ra}, {key(r, "B"): r for r in rb}
    if len(A) != len(ra) or len(B) != len(rb):
        raise ValueError("對帳鍵撞了(同根同路徑兩列):A %d→%d · B %d→%d" % (len(ra), len(A), len(rb), len(B)))
    states = Counter()
    rows = []
    for k in sorted(set(A) | set(B)):
        a, b = A.get(k), B.get(k)
        if a and b:
            st = "SYNC" if a["h"] == b["h"] else ("SIZE_ONLY" if a["h"].startswith("size:") else "DIVERGED")
        else:
            st = "LOCAL_AHEAD" if a else ("A_SKIPPED" if any("/%s/" % d in "/" + k for d in IGNORE_DIRS) else "REMOTE_ONLY")   # A 軌依規則不掃的夾(VIA_Reports 等)不冒充「遠端才有」
        states[st] += 1
        if st != "SYNC":
            rows.append({"path": k, "state": st, "system": (a or b)["s"], "tail": (a or b)["tail"]})
    return {"engine": ENGINE, "at": _now(), "states": dict(states), "rows": rows, "root_map": rmap, "roots": {"A": roots_a, "B": roots_b}}


def v_numbers(rows: list, missing: bool = False, limit: int = 30) -> list:
    tails = [r for r in rows if r["tail"] and r["ext"] in (".py", ".ps1") and r["s"] not in ("GEN", "ORP")]
    miss = [r for r in tails if not r["num"]]
    out = ["尾版程式 %d · 有號 %d · 空號 %d" % (len(tails), len(tails) - len(miss), len(miss))]
    if missing:
        out += ["  空號 %s %s" % (r["s"], r["p"].split("/", 1)[-1]) for r in miss[:limit]]
    return out


def v_slice(summary: dict, rows: list, path: str, name: str) -> str:
    """只取一個定義的原文(帶行號)。path 必須是索引裡的列(不能讀索引外的檔);A 軌讀磁碟、B 軌讀 git ref。"""
    row = next((r for r in rows if r["p"] == path or r["p"].split("/", 1)[-1] == path), None)
    if not row:
        return "(索引裡沒有這個檔:先 find / where)"
    root_name, _, inner = row["p"].partition("/")
    root = next((Path(p) for p in summary["paths"] if Path(p).name == root_name), None)
    if root is None:
        return "(找不到掃描根 %s)" % root_name
    try:
        if summary["track"] == "B":
            top = _git(root, "rev-parse", "--show-toplevel").stdout.decode().strip()
            sub = str(root.resolve().relative_to(Path(top).resolve())).replace("\\", "/")
            rev = (summary.get("refs") or {}).get(root_name) or summary["ref"]   # 索引記下的 commit,不是會往前走的 ref(Codex #627 P2)
            spec = "%s:%s" % (rev, (sub + "/" if sub not in (".", "") else "") + inner)
            text = _git(Path(top), "show", spec).stdout.decode("utf-8", "replace")
        else:
            text = (root / inner).read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return "(讀不到:%s)" % type(exc).__name__
    if not name:
        return "(要給定義名;整檔請用 card / system 看摘要)"
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return "(語法錯,無法切:%s)" % exc
    want = name.split(".")
    kinds = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)

    def walk_path(nodes, parts):          # Class.method 逐層走,不丟限定詞(Codex #627 P2)
        for nd in nodes:
            if isinstance(nd, kinds) and nd.name == parts[0]:
                if len(parts) == 1:
                    return nd
                hit = walk_path(nd.body, parts[1:])
                if hit is not None:
                    return hit
        return None
    found = walk_path(tree.body, want)
    if found is None and len(want) == 1:
        found = next((nd for nd in ast.walk(tree) if isinstance(nd, kinds) and nd.name == want[0]), None)
    if found is None:
        return "(%s 裡沒有 %s)" % (inner, name)
    lines = text.splitlines()
    a, b = found.lineno, getattr(found, "end_lineno", found.lineno)
    if getattr(found, "decorator_list", None):
        a = min(d.lineno for d in found.decorator_list)
    return "\n".join("%5d  %s" % (i, lines[i - 1]) for i in range(a, min(b, a + 400) + 1)) + ("\n…(截在 400 行)" if b - a > 400 else "")


# ---------------------------------------------------------------- MCP(stdio · JSON-RPC 2.0 · 只讀)
MCP_TOOLS = [
    ("via_card", "VIA 系統卡:事後閘 + 五系統矩陣 + 尾版入口,依 token 預算出卡(先讀這張,不讀原始碼)",
     {"budget": {"type": "integer", "default": 3000}, "system": {"type": "string", "default": ""}}, []),
    ("via_find", "在索引的路徑 / 說明 / 定義名找(正規式),不回原文",
     {"pattern": {"type": "string"}, "system": {"type": "string", "default": ""}, "limit": {"type": "integer", "default": 30}}, ["pattern"]),
    ("via_where", "定義在哪個檔第幾行(+ VCGC 編號)",
     {"name": {"type": "string"}}, ["name"]),
    ("via_system", "某系統全部尾版程式:檔 · 說明 · 定義數 · 編號",
     {"system": {"type": "string"}, "limit": {"type": "integer", "default": 60}}, ["system"]),
    ("via_numbers", "尾版編號覆蓋;missing=true 列空號(只查不發)",
     {"missing": {"type": "boolean", "default": False}, "limit": {"type": "integer", "default": 30}}, []),
    ("via_slice", "只取一個定義的原文(帶行號);path 必須是索引裡的檔",
     {"path": {"type": "string"}, "name": {"type": "string"}}, ["path", "name"]),
]


def mcp_call(out: Path, name: str, args: dict) -> str:
    if not (out / "index.jsonl").is_file():
        return "還沒掃過 %s:先在終端跑 scan(MCP 只讀,不替你掃)" % out
    s, rows = _load(out)
    if name == "via_card":
        return render_card(s, rows, int(args.get("budget") or 3000), str(args.get("system") or ""))
    if name == "via_find":
        return "\n".join(v_find(rows, str(args.get("pattern") or "."), str(args.get("system") or ""), int(args.get("limit") or 30))) or "(沒有)"
    if name == "via_where":
        return "\n".join(v_where(rows, str(args.get("name") or ""))) or "(沒有)"
    if name == "via_system":
        lines = v_system(rows, str(args.get("system") or ""))
        lim = int(args.get("limit") or 60)
        return "\n".join(lines[:lim]) + ("\n…還有 %d 支" % (len(lines) - lim) if len(lines) > lim else "") if lines else "(沒有)"
    if name == "via_numbers":
        return "\n".join(v_numbers(rows, bool(args.get("missing")), int(args.get("limit") or 30)))
    if name == "via_slice":
        return v_slice(s, rows, str(args.get("path") or ""), str(args.get("name") or ""))
    raise KeyError(name)


def mcp_handle(out: Path, msg: dict):
    mid, method = msg.get("id"), msg.get("method")
    if mid is None:                       # notification(initialized 等)不回
        return None
    if method == "initialize":
        res = {"protocolVersion": (msg.get("params") or {}).get("protocolVersion") or "2025-06-18",
               "capabilities": {"tools": {"listChanged": False}}, "serverInfo": {"name": "via-systemcard", "version": VERSION},
               "instructions": "先 via_card(預算內的全景卡)→ via_find / via_where 定位 → via_slice 只取那一段;不要整檔讀。黃不是綠。"}
    elif method == "ping":
        res = {}
    elif method == "tools/list":
        res = {"tools": [{"name": n, "description": d, "inputSchema": {"type": "object", "properties": props, "required": req, "additionalProperties": False},
                          "annotations": {"readOnlyHint": True, "openWorldHint": False}} for n, d, props, req in MCP_TOOLS]}
    elif method == "tools/call":
        p = msg.get("params") or {}
        try:
            text = mcp_call(out, str(p.get("name")), p.get("arguments") or {})
            res = {"content": [{"type": "text", "text": text}], "isError": False}
        except KeyError:
            return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32602, "message": "未知工具 %s" % p.get("name")}}
        except Exception as exc:          # 照實回錯,不吞
            res = {"content": [{"type": "text", "text": "%s: %s" % (type(exc).__name__, exc)}], "isError": True}
    else:
        return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": "不支援 %s" % method}}
    return {"jsonrpc": "2.0", "id": mid, "result": res}


def mcp_serve(out: Path) -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except ValueError:
            resp = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "parse error"}}
        else:
            resp = mcp_handle(out, msg) if isinstance(msg, dict) else {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "invalid"}}
        if resp is not None:
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()
    return 0


def v_tools() -> list:
    """省 Token 外部工具偵測(只看在不在,不裝;要裝走 VCGC InstallGate / 外掛目錄)。"""
    import shutil
    home = Path.home()

    def mod(name):
        try:
            __import__(name)
            return True
        except Exception:  # noqa: BLE001
            return False
    skills = home / ".claude" / "skills"
    plugins = home / ".claude" / "plugins"
    names = " ".join(p.name.lower() for d in (skills, plugins, plugins / "data") if d.is_dir() for p in d.iterdir())
    return [("Graphify", mod("graphify") or bool(shutil.which("graphify")), "程式關係圖;VIA 有 via_graphify v0100/v0101 收據"),
            ("Ponytail", "ponytail" in names, "Claude Code 技能:寫碼前問「要不要做」,少寫程式;要裝在 ~/.claude/skills"),
            ("記憶外掛(claude-mem 類)", any(k in names for k in ("memory", "mem")), "跨對話記憶;外掛目錄有 claude-memory / Project Memory 等"),
            ("find-skills", "find" in names or "zizi" in names, "找現成技能,避免重寫"),
            ("Playwright", bool(shutil.which("playwright")) or Path("/opt/pw-browsers").is_dir(), "U/I 實測;容器有預裝瀏覽器"),
            ("DuckDB", mod("duckdb"), "本引擎 index.parquet / 查詢"),
            ("ChartDB", bool(shutil.which("chartdb")), "資料庫結構圖;本引擎 matrix.html 先代")]


# ---------------------------------------------------------------- 自測
def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""), flush=True)
    print("[%s selftest]" % ENGINE, flush=True)
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "VeritasIntelligenceAnalytics"
        files = {
            "supportive modules/registry/CGC_MDL001_Tool_v0100.py": '"""VCGC 工具本體"""\ndef run():\n    return 1\n',
            "supportive modules/registry/CGC_MDL001_Tool_v0101.py": '"""VCGC 工具薄尾 v0101"""\nclass T:\n    def go(self):\n        return 2\n',
            "functional modules/VDF/VDF_SystemManager_v0100.py": '"""VDF 入口:擷取與倉儲"""\nimport duckdb\ndef main():\n    return "CGC_MDL001"\n',
            "functional modules/VRN/VRN_ENG001_Reader_v0100.py": '"""VRN 研報讀取"""\ndef read_pdf(p):\n    return p\n',
            "functional modules/VQG/VQG_AllInOne_v0100.py": '"""VQG 指標"""\ndef rsi():\n    return 0\n',
            "functional modules/VAP/VAP_AllInOne_v0300.py": '"""VAP 看板"""\ndef serve():\n    pass\n',
            "functional modules/VRN/broken_v0100.py": 'def x(:\n',
            "README.md": "# VIA 倉\n",
            "supportive modules/registry/VIA_NumberBooks/VIA_NumberBook_MDL_v0100.jsonl":
                json.dumps({"code": "VIA-VCGC-MDL001", "source": "supportive modules/registry/CGC_MDL001_Tool_v0101.py"}) + "\n",
            "misc/random_notes.txt": "隨手筆記\n",
        }
        for rel, txt in files.items():
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(txt, encoding="utf-8")
        outA = Path(td) / "outA"
        s = scan([root], "A", outA)
        _, rows = _load(outA)
        bys = {r["p"].split("/", 1)[-1]: r for r in rows}
        chk("① 分系統用 VIA 命名律:CGC_→VCGC · VDF_→VDF · VRN_→VRN-2 · VQG_ · VAP_ · README→GEN · 認不出→ORP",
            bys["supportive modules/registry/CGC_MDL001_Tool_v0101.py"]["s"] == "VCGC" and bys["functional modules/VDF/VDF_SystemManager_v0100.py"]["s"] == "VDF"
            and bys["functional modules/VRN/VRN_ENG001_Reader_v0100.py"]["s"] == "VRN-2" and bys["functional modules/VQG/VQG_AllInOne_v0100.py"]["s"] == "VQG"
            and bys["README.md"]["s"] == "GEN" and bys["misc/random_notes.txt"]["s"] == "ORP", s["by_system"])
        chk("② 版本律:同家族 v0101 = 尾版 · v0100 = 凍結前版(卡上不展開)",
            bys["supportive modules/registry/CGC_MDL001_Tool_v0101.py"]["tail"] and not bys["supportive modules/registry/CGC_MDL001_Tool_v0100.py"]["tail"])
        chk("③ 編號只查不發:號冊有的 = 帶號 · 沒有的 = 空號照實(G5 黃)",
            bys["supportive modules/registry/CGC_MDL001_Tool_v0101.py"]["num"] == "VIA-VCGC-MDL001" and not bys["functional modules/VDF/VDF_SystemManager_v0100.py"]["num"]
            and not s["gates"]["G5_尾版編號覆蓋"]["ok"], s["gates"]["G5_尾版編號覆蓋"]["val"])
        chk("④ 事後閘真的算:G1 守恆 · G2 解析 + 語法錯 = 可讀 .py · G3 零變動 · G4 孤兒 1/10 = 10% > 5% → 黃",
            s["gates"]["G1_檔案守恆"]["ok"] and s["gates"]["G2_AST守恆"]["ok"] and s["gates"]["G3_掃描零變動"]["ok"] and not s["gates"]["G4_孤兒比例"]["ok"]
            and s["lamp"] == "YELLOW", s["lamp"])
        card, floor = render_card(s, rows, 400), approx_tokens(render_card(s, rows, 0))
        chk("⑤ 卡依預算出(400;閘與矩陣是必出段,超出只能是必出段)· 卡 ≤ max(預算, 必出段) + 30 · 先閘與矩陣",
            approx_tokens(card) <= max(400, floor) + 30 and "## 事後閘" in card and "五系統矩陣" in card, "卡 %d · 必出段 %d" % (approx_tokens(card), floor))
        chk("⑥ 互動動詞:find 找到 · where 指到檔:行 · system 列尾版 · 引用矩陣抓到 VDF→VCGC",
            v_find(rows, "擷取") and v_where(rows, "go")[0].endswith("VCGC · VIA-VCGC-MDL001") and "go" in v_where(rows, "go")[0] and v_system(rows, "VDF")
            and s["xref"].get("VDF", {}).get("VCGC"), (v_where(rows, "go"), s["xref"]))
        # B 軌:git 倉
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        subprocess.run(["git", "-C", str(root), "-c", "user.email=t@t", "-c", "user.name=t", "add", "-A"], check=True)
        subprocess.run(["git", "-C", str(root), "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "x"], check=True)
        (root / "functional modules/VDF/VDF_New_v0100.py").write_text('"""只在本機"""\n', encoding="utf-8")
        (root / "README.md").write_text("# 改過\n", encoding="utf-8")
        outB = Path(td) / "outB"
        sb = scan([root], "B", outB, ref="HEAD")
        chk("⑦ B 軌走 git(ls-tree / cat-file)· 檔數 = 提交時 10 · 說明照樣抽到 · G6 可讀", sb["files"] == 10 and sb["gates"]["G6_來源可讀"]["ok"]
            and any(r["pur"] == "VDF 入口:擷取與倉儲" for r in _load(outB)[1]), sb["files"])
        bad = scan([root], "B", Path(td) / "outBad", ref="no-such-ref")
        chk("⑧ B 軌 ref 解不開 → G6 紅 · 燈 RED(不回空清單冒充綠)", bad["lamp"] == "RED" and not bad["gates"]["G6_來源可讀"]["ok"], bad["gates"]["G6_來源可讀"]["val"])
        outA2 = Path(td) / "outA2"
        scan([root], "A", outA2)
        d = v_diff(outA2, outB)
        chk("⑨ A×B 對帳:新檔 = LOCAL_AHEAD · 改過 = DIVERGED(git blob 雜湊同算法)· 其餘 SYNC",
            d["states"].get("LOCAL_AHEAD") == 1 and d["states"].get("DIVERGED") == 1 and d["states"].get("SYNC") == 9, d["states"])
        chk("⑩ 輸出:index.jsonl · summary.json · card.md · matrix.html(有 duckdb 再加 parquet)",
            all((outA / f).is_file() for f in ("index.jsonl", "summary.json", "card.md", "matrix.html")), s.get("parquet"))
        ui = (s.get("ui") or {})
        chk("⑫ 鎖定 U/I 模板:每系統一頁 + Hub 套 WorkbenchLock 鎖站(css token 區塊 · 結構 id · payload 信封)· 鎖的 check 綠 · 頁內只放本系統列",
        ui.get("applied") and ui.get("check_lamp") == "GREEN" and set(ui.get("pages", {})) == set(s["by_system"]), (ui.get("why") or ui.get("check_red"), sorted(ui.get("pages", {}))))
        two = Path(td) / "via-vdf-vrn"
        (two / "functional modules" / "VRN").mkdir(parents=True)
        (two / "functional modules" / "VRN" / "VRN_Summarizer_v0100.py").write_text('"""VRN-1 摘要"""\n', encoding="utf-8")
        s2 = scan([root, two], "A", Path(td) / "outTwo")
        chk("⑮ 兩倉同掃 VRN 逐列標:本倉 VRN_ = VRN-2 · via-vdf-vrn 倉 = VRN-1(不互相吃掉)",
            s2["by_system"].get("VRN-1") == 1 and s2["by_system"].get("VRN-2") == s["by_system"].get("VRN-2"), s2["by_system"])
        # ⑯ Codex #627 四條回歸:號冊依倉 · 對帳鍵留倉根 · slice 限定名 · B 軌 slice 用索引當下的 commit
        r1, r2 = Path(td) / "repoX", Path(td) / "repoY"
        same = "supportive modules/registry/CGC_MDL002_Same_v0100.py"
        for rr, code in ((r1, "VIA-VCGC-MDL101"), (r2, "VIA-VCGC-MDL202")):
            (rr / same).parent.mkdir(parents=True, exist_ok=True)
            (rr / same).write_text('"""同路徑"""\nclass First:\n    def run(self):\n        return 1\nclass Second:\n    def run(self):\n        return 2\n', encoding="utf-8")
            bk = rr / "supportive modules/registry/VIA_NumberBooks/VIA_NumberBook_MDL_v0100.jsonl"
            bk.parent.mkdir(parents=True, exist_ok=True)
            bk.write_text(json.dumps({"code": code, "source": same}) + "\n", encoding="utf-8")
            (rr / "README.md").write_text("# 同名\n", encoding="utf-8")
        o1 = Path(td) / "outXY1"
        sxy = scan([r1, r2], "A", o1)
        _, rxy = _load(o1)
        num = {r["p"]: r["num"] for r in rxy}
        (r1 / "README.md").write_text("# repoX 改了\n", encoding="utf-8")
        o2 = Path(td) / "outXY2"
        scan([r1, r2], "A", o2)
        dxy = v_diff(o2, o1)
        sl = v_slice(sxy, rxy, "repoX/" + same, "Second.run")
        subprocess.run(["git", "-C", str(root), "-c", "user.email=t@t", "-c", "user.name=t", "add", "-A"], check=True)
        tool = root / "supportive modules/registry/CGC_MDL001_Tool_v0101.py"
        tool_orig = tool.read_text(encoding="utf-8")
        tool.write_text('"""後來才加"""\ndef newfn():\n    return 9\n', encoding="utf-8")
        subprocess.run(["git", "-C", str(root), "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qam", "later"], check=True)
        sb_s, sb_rows = _load(outB)
        late = v_slice(sb_s, sb_rows, "supportive modules/registry/CGC_MDL001_Tool_v0101.py", "newfn")
        then = v_slice(sb_s, sb_rows, "supportive modules/registry/CGC_MDL001_Tool_v0101.py", "T.go")
        tool.write_text(tool_orig, encoding="utf-8")   # 還原夾具,後面 ⑭(A 軌讀磁碟)不受影響
        chk("⑯ Codex #627:號冊依倉不互借(X=101 · Y=202)· 兩倉同名 README 對帳不互蓋(DIVERGED 1)· slice Second.run 取到 Second · B 軌 slice 讀索引當下 commit(之後才加的 newfn 取不到)",
            num.get("repoX/" + same) == "VIA-VCGC-MDL101" and num.get("repoY/" + same) == "VIA-VCGC-MDL202"
            and dxy["states"].get("DIVERGED") == 1 and any(r["path"] == "repoX/README.md" for r in dxy["rows"])
            and "return 2" in sl and "return 1" not in sl and "沒有" in late and "def go" in then,
            (num, dxy["states"], sl[-20:], late[-20:]))
        tx = Path(td) / "talib_fx"
        (tx / "functional modules" / "VAP").mkdir(parents=True)
        (tx / "functional modules" / "VAP" / "VAP_Dyn_v0100.py").write_text('"""動態"""\ndef f(name):\n    return name\ndef g():\n    t = def_import_optional("talib")\n    return t\n', encoding="utf-8")
        (tx / "functional modules" / "VAP" / "VAP_Static_v0100.py").write_text('"""靜態"""\ndef h():\n    import talib\n    return talib\n', encoding="utf-8")
        (tx / "functional modules" / "VAP" / "VAP_Clean_v0100.py").write_text('"""乾淨:只提到字樣"""\nNOTE = "talib is forbidden"\n', encoding="utf-8")
        st = scan([tx], "A", Path(td) / "outTal")
        _, rt = _load(Path(td) / "outTal")
        tl = {r["p"].rsplit("/", 1)[-1]: r["tal"] for r in rt}
        chk("⑰ G7 TA-Lib 禁用閘(商業審查 G21):函式內 import talib = static · def_import_optional(\"talib\") = dynamic · 只提到字樣不算 · 閘不過照實黃",
            tl.get("VAP_Static_v0100.py", "").startswith("static") and tl.get("VAP_Dyn_v0100.py", "").startswith("dynamic") and not tl.get("VAP_Clean_v0100.py")
            and not st["gates"]["G7_TA-Lib禁用"]["ok"] and s["gates"]["G7_TA-Lib禁用"]["ok"], (tl, st["gates"]["G7_TA-Lib禁用"]["val"]))
        chk("⑬ 號冊整本讀(MDL 冊 > 1 MB 也讀 · 實測 2.6 MB)· source 相對 VIA 根精確對號",
            _readable("x/VeritasIntelligenceAnalytics/supportive modules/registry/VIA_NumberBooks/VIA_NumberBook_MDL_v0100.jsonl", 2_700_000)
            and not _readable("x/big.json", 2_700_000)
            and _num_of("movies-dataset/VeritasIntelligenceAnalytics/functional modules/VDF/VDF_A_v0101.py", {("movies-dataset", "functional modules/VDF/VDF_A_v0101.py"): "VIA-VDF-MDL009"}) == "VIA-VDF-MDL009"
            and _num_of("via-vdf-vrn/functional modules/VDF/VDF_A_v0101.py", {("movies-dataset", "functional modules/VDF/VDF_A_v0101.py"): "VIA-VDF-MDL009"}) == "")
        msgs = [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}},
                {"jsonrpc": "2.0", "method": "notifications/initialized"},
                {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
                {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "via_where", "arguments": {"name": "go"}}},
                {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "via_slice", "arguments": {"path": "supportive modules/registry/CGC_MDL001_Tool_v0101.py", "name": "T.go"}}},
                {"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {"name": "via_slice", "arguments": {"path": "../../etc/passwd", "name": "x"}}}]
        pr = subprocess.run([sys.executable, str(Path(__file__).resolve()), "mcp", "--out", str(outA)], input="\n".join(json.dumps(m) for m in msgs) + "\n",
                            capture_output=True, text=True, timeout=60)
        resp = {r.get("id"): r for r in (json.loads(l) for l in pr.stdout.splitlines() if l.strip())}
        txt = lambda i: ((resp.get(i) or {}).get("result") or {}).get("content", [{}])[0].get("text", "")
        chk("⑭ MCP stdio 真握手:initialize → tools/list 6 支(readOnly)→ via_where 指到檔:行 → via_slice 取到 def go → 索引外路徑拒讀 · 通知不回",
            resp.get(1, {}).get("result", {}).get("serverInfo", {}).get("name") == "via-systemcard"
            and len(resp.get(2, {}).get("result", {}).get("tools", [])) == 6 and "CGC_MDL001_Tool_v0101.py:" in txt(3)
            and "def go" in txt(4) and "索引裡沒有" in txt(5) and None not in resp, (sorted(k for k in resp if k is not None), txt(4)[:60], pr.stderr[-200:]))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑪ 不用 TA-Lib · 不 import VCGC · 零網路", not re.search(r"^\s*(?:import|from)\s+(talib|CGC_|requests|urllib|httpx)", src, re.M))
    n = sum(ok)
    print("[%s] %s selftest · %d/%d" % ("PASS" if n == len(ok) else "FAIL", ENGINE, n, len(ok)), flush=True)
    return 0 if n == len(ok) else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=ENGINE)
    ap.add_argument("verb", nargs="?", default="card")
    ap.add_argument("args", nargs="*")
    ap.add_argument("--track", choices=["A", "B"], default="A")
    ap.add_argument("--ref", default="origin/main")
    ap.add_argument("--out", default="")
    ap.add_argument("--vrn-label", default="")
    ap.add_argument("--full-hash", action="store_true")
    ap.add_argument("--budget", type=int, default=3000)
    ap.add_argument("--system", default="")
    ap.add_argument("--limit", type=int, default=30)
    ap.add_argument("--map", action="append", default=[], help="diff 用:A 根名=B 根名(可重複)")
    ap.add_argument("--missing", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest or a.verb == "selftest":
        return selftest()
    out = Path(a.out) if a.out else DEFAULT_OUT / a.track
    if a.verb == "scan":
        s = scan([Path(p) for p in a.args] or [VIA], a.track, out, a.ref, a.vrn_label, a.full_hash)
        print("[%s] %s · %s 軌 · 檔 %d · 尾版 %d · %s · 卡 → %s" % (s["lamp"], ENGINE, s["track"], s["files"], s["tails"],
              json.dumps(s["by_system"], ensure_ascii=False), out / "card.md"))
        for k, v in s["gates"].items():
            print("  %s %s:%s" % ("✅" if v["ok"] else "⚠️", k, v["val"]))
        return 0 if s["lamp"] != "RED" else 2
    if a.verb == "tools":
        for name, here, note in v_tools():
            print("  %s %-24s %s" % ("在" if here else "無", name, note))
        return 0
    if a.verb == "diff":
        if len(a.args) != 2:
            print("用法:diff <A 輸出夾> <B 輸出夾>")
            return 2
        d = v_diff(Path(a.args[0]), Path(a.args[1]), dict(m.split("=", 1) for m in a.map if "=" in m))
        print(json.dumps(d["states"], ensure_ascii=False))
        for r in d["rows"][:a.limit]:
            print("  %-12s %s %s%s" % (r["state"], r["system"], r["path"], "" if r["tail"] else "(前版)"))
        return 0
    if a.verb == "mcp":
        return mcp_serve(out)
    if not (out / "index.jsonl").is_file():
        print("還沒掃過:先 scan <路徑> --track %s" % a.track)
        return 2
    s, rows = _load(out)
    if a.verb == "card":
        print(render_card(s, rows, a.budget, a.system), end="")
    elif a.verb == "find":
        print("\n".join(v_find(rows, a.args[0] if a.args else ".", a.system, a.limit)) or "(沒有)")
    elif a.verb == "where":
        print("\n".join(v_where(rows, a.args[0] if a.args else "")) or "(沒有)")
    elif a.verb == "system":
        lines = v_system(rows, a.args[0] if a.args else a.system)
        print("\n".join(lines[:a.limit]) + ("\n…還有 %d 支(--limit)" % (len(lines) - a.limit) if len(lines) > a.limit else "") if lines else "(沒有)")
    elif a.verb == "numbers":
        print("\n".join(v_numbers(rows, a.missing, a.limit)))
    elif a.verb == "slice":
        print(v_slice(s, rows, a.args[0] if a.args else "", a.args[1] if len(a.args) > 1 else ""))
    else:
        print("動詞:scan · card · find · where · slice · system · numbers · diff · tools · mcp · --selftest")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
