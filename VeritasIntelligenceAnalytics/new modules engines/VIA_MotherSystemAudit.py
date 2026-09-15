#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_MotherSystemAudit.py  —  URN VIA-SYS-ENG-006  v0200

母系統唯讀盤點 / 控制層識別 / 工作流可視化 / JSON 參數整合去重
================================================================

只增不減地升級自 VIA_AuthorityAudit v0100。v0100 做了「JSON 參數整合去重」
與「控制層識別」；v0200 把範圍收斂到母系統一棵樹，並補上：

  A 只讀母系統          輸出目錄強制在母系統之外；跑前跑後各按一次指紋，
                        不一致就 FAIL（RO01）。母系統一個位元組都不動。
  B 抓最新的 PowerShell  同家族的多版本只留最新一份參與拓樸，其餘列為
                        SUPERSEDED。家族鍵含父目錄；日期字串不當版本號；
                        沒有版本標記的檔案自成一家 —— 這三條是上次
                        VersionGuard 誤搬檔案的直接補丁。
  C 誰在控管             對每支 .ps1/.py 算控制訊號與引擎訊號，建呼叫圖，
                        依 fan-out/fan-in 定層。會呼叫到 manager/engine 的
                        PowerShell 標為 GOVERNOR —— 這就是「控管 system
                        managers/engines 的 PowerShell」。
  D 工作流               modules/engines 分層 SVG，邊即實際的字面量引用。
  E 循環依賴             Tarjan 強連通分量。>1 個節點的 SCC 就是環。
  F 何者遺漏             被引用但找不到檔案 / 有進入點卻沒人叫 /
                        子系統資料夾沒有自己的 manager。
  G JSON 整合去重        沿用 v0100：AGREED / CONFLICT / SINGLE + 內容雜湊
                        重複清單。只有 AGREED 進 SSOT，衝突一個都不放。
  H 自動編號             全部節點交給 VIA_AutoNumberSSOT（ENG-007）發號。
                        號碼存 SSOT，不寫檔名 —— 改檔名會打斷 bin\\ 的
                        via-*.cmd shim 與所有字面量路徑引用。

用法：
    python VIA_MotherSystemAudit.py
    python VIA_MotherSystemAudit.py --root "<母系統路徑>" --out "<輸出路徑>"
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import html
import json
import os
import re
import sys
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from VIA_AutoNumberSSOT import AutoNumberSSOT
    HAS_AUTONUM = True
except ImportError:
    HAS_AUTONUM = False

URN_SELF = "VIA-SYS-ENG-006"
VERSION = "v0200"
SPEC_VERSION = "VIA-SSOT-SPEC-v0100"

DEFAULT_ROOT = r"C:\Users\tonyk\Downloads\movies-dataset\VeritasIntelligenceAnalytics"
DEFAULT_OUT = r"C:\VeritasIntelligenceAnalytics\CGE\_mother_audit"

CODE_EXT = {".ps1", ".psm1", ".py"}
INVENTORY_EXT = {".ps1", ".psm1", ".py", ".json", ".cmd", ".html", ".md", ".csv"}

SKIP_DIRS = {
    "_superseded", "_legacy", "_to_delete", "_backup", "_recover", "_duplicates",
    "_versionguard", "_governance", "_hardening", "_deepprobe", "_audit",
    "_mother_audit", "_archive", ".git", "__pycache__", ".venv", "venv",
    "node_modules", "site-packages", ".idea", ".vs", ".pytest_cache",
}

# 產物與資料，不是設定：不納入參數整合
DERIVED_JSON = re.compile(
    r"(_snapshot|_report|_matrix|_audit|_index|manifest|registry|ledger|"
    r"history|state|\.preview\.|_result|_output)", re.I)

CONTROL_SIGNALS_PS = [
    (r"Start-Process", 3, "生子行程"),
    (r"ProcessStartInfo", 3, "生子行程"),
    (r"Invoke-Expression", 2, "動態執行"),
    (r"\[ValidateSet\([^)]*\)\]\s*\r?\n?\s*\[string\]\s*\$(Mode|Task|Action|Target|Command)", 3, "模式派工參數"),
    (r"&\s*\$\w*(exe|Exe|Path|Script)", 2, "呼叫外部程式"),
    (r"Import-Module\s+[\"']?\.", 1, "載入本地模組"),
    (r"(?i)\bswitch\s*\(\s*\$(Mode|Task|Action|Target)\b", 3, "依模式分派"),
    (r"(?i)\bpython(3|\.exe)?\s+", 2, "呼叫 Python"),
    (r"(?i)pwsh\s+-File", 2, "呼叫 PowerShell"),
]
CONTROL_SIGNALS_PY = [
    (r"\bsubprocess\.(run|Popen|call|check_output)", 3, "生子行程"),
    (r"importlib\.util\.spec_from_file_location", 3, "動態載入模組"),
    (r"add_subparsers", 2, "子命令派工"),
    (r"(?m)^\s*(DISPATCH|_REGISTRY|STAGES|PIPELINE)\s*[:=]\s*[\[{]", 2, "派工表"),
    (r"ThreadPoolExecutor|ProcessPoolExecutor", 2, "併發調度"),
]
ENTRYPOINT_PY = re.compile(r'if\s+__name__\s*==\s*["\']__main__["\']')
ENTRYPOINT_PS = re.compile(r"(?m)^\s*param\s*\(")
DEF_PY = re.compile(r"(?m)^\s*(class|def)\s+\w+")
DEF_PS = re.compile(r"(?mi)^\s*function\s+[\w\-]+")

# 字面量引用：'foo.py' / "Bar.ps1" / foo.psm1
REFERENCE = re.compile(r"['\"]?([A-Za-z0-9_\-. ]+\.(?:ps1|psm1|py))['\"]?")

VERSION_TOKEN = re.compile(r"(?i)[_\-.]v(\d{3,4})([A-Za-z]?)(?:\.\d+)?(?![0-9])")
SHA_TOKEN = re.compile(r"(?i)_sha[0-9a-f]{8}\b")
COPY_TOKEN = re.compile(r"\s*\(\d+\)$")
DATE_LIKE = re.compile(r"(?<![0-9])(?:19|20)\d{6}(?![0-9])")


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def esc(text: Any) -> str:
    return html.escape(str(text), quote=True)


# ---------------------------------------------------------------------------
# 掃描
# ---------------------------------------------------------------------------

def walk(root: Path) -> List[Path]:
    found: List[Path] = []
    for dirpath, dirnames, filenames in os.walk(str(root)):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for name in filenames:
            if Path(name).suffix.lower() in INVENTORY_EXT:
                found.append(Path(dirpath) / name)
    return found


def fingerprint(root: Path) -> Tuple[int, int]:
    """檔數 + 總位元組。跑前跑後比對，證明本工具沒動過母系統。"""
    count = 0
    total = 0
    for dirpath, dirnames, filenames in os.walk(str(root)):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for name in filenames:
            try:
                total += (Path(dirpath) / name).stat().st_size
                count += 1
            except OSError:
                pass
    return count, total


def read_text(path: Path) -> str:
    for enc in ("utf-8-sig", "utf-8", "cp950", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except (UnicodeDecodeError, OSError):
            continue
    return ""


# ---------------------------------------------------------------------------
# B. 版本家族：何者最新
# ---------------------------------------------------------------------------

def family_of(path: Path, root: Path) -> Tuple[str, Optional[Tuple[int, str]], bool]:
    """回傳 (家族鍵, 版本序, 是否帶版本/分身標記)。

    三條補丁，全部來自上次 VersionGuard 誤搬檔案的教訓：
      1. 家族鍵含父目錄 —— 不同資料夾的同名檔不是同一家族
      2. 日期字串（20260804）不當版本號 —— snapshot 資料夾曾因此被誤判
      3. 完全沒有版本或分身標記的檔案永不被判為「被取代」—— 它可能就是
         正在用的那一份，只是兄弟們多了 -v0113 後綴
    _sha<hex8> 與 " (2)" 依母系統既有慣例視為同一家族的內容分身。
    """
    stem = path.stem
    match = VERSION_TOKEN.search(stem)
    ver: Optional[Tuple[int, str]] = None
    if match and not DATE_LIKE.fullmatch(match.group(1)):
        ver = (int(match.group(1)), match.group(2) or "")
        stem = stem[:match.start()] + stem[match.end():]
    twin = bool(SHA_TOKEN.search(stem) or COPY_TOKEN.search(stem))
    stem = SHA_TOKEN.sub("", stem)
    stem = COPY_TOKEN.sub("", stem)
    try:
        parent = str(path.parent.relative_to(root))
    except ValueError:
        parent = str(path.parent)
    key = "%s::%s%s" % (parent, stem.strip("_-. ") or path.stem, path.suffix.lower())
    return key, ver, (ver is not None) or twin


# ---------------------------------------------------------------------------
# 節點
# ---------------------------------------------------------------------------

class Node:
    __slots__ = ("path", "rel", "name", "lang", "family", "ver", "marked", "mtime", "size",
                 "control", "engine", "signals", "entry", "refs", "tier",
                 "fan_in", "fan_out", "latest", "category", "code")

    def __init__(self, path: Path, root: Path):
        self.path = path
        self.rel = str(path.relative_to(root))
        self.name = path.name
        self.lang = "ps1" if path.suffix.lower() in (".ps1", ".psm1") else (
            "py" if path.suffix.lower() == ".py" else path.suffix.lower().lstrip("."))
        self.family, self.ver, self.marked = family_of(path, root)
        stat = path.stat()
        self.mtime = stat.st_mtime
        self.size = stat.st_size
        self.control = 0
        self.engine = 0
        self.signals: List[str] = []
        self.entry = False
        self.refs: List[str] = []
        self.tier = "UNCLASSIFIED"
        self.fan_in = 0
        self.fan_out = 0
        self.latest = True
        self.category = "其他"
        self.code = ""


def categorize(rel: str) -> str:
    low = rel.lower().replace("\\", "/")
    if "/" not in low:
        return "母檔案"
    if low.startswith("supportive modules/"):
        return "子檔案"
    if low.startswith("functional modules/") or low.startswith("system_core/"):
        return "子檔案"
    if low.startswith("bin/"):
        return "母檔案"
    return "其他"


def analyze_code(node: Node, text: str) -> None:
    table = CONTROL_SIGNALS_PS if node.lang == "ps1" else CONTROL_SIGNALS_PY
    for pattern, weight, label in table:
        if re.search(pattern, text):
            node.control += weight
            node.signals.append(label)
    node.entry = bool((ENTRYPOINT_PS if node.lang == "ps1" else ENTRYPOINT_PY).search(text))
    defs = (DEF_PS if node.lang == "ps1" else DEF_PY).findall(text)
    node.engine = min(len(defs), 12)
    if not node.entry:
        node.engine += 3
    seen = set()
    for ref in REFERENCE.findall(text):
        low = ref.strip().lower()
        if low and low != node.name.lower() and low not in seen:
            seen.add(low)
            node.refs.append(low)


# ---------------------------------------------------------------------------
# E. 循環依賴（Tarjan）
# ---------------------------------------------------------------------------

def find_cycles(nodes: List[str], edges: List[Tuple[str, str]]) -> List[List[str]]:
    graph = collections.defaultdict(list)
    for src, dst in edges:
        graph[src].append(dst)
    index: Dict[str, int] = {}
    low: Dict[str, int] = {}
    on_stack: Dict[str, bool] = {}
    stack: List[str] = []
    result: List[List[str]] = []
    counter = [0]

    def strongconnect(start: str) -> None:
        work = [(start, 0)]
        while work:
            node, pos = work[-1]
            if pos == 0:
                index[node] = low[node] = counter[0]
                counter[0] += 1
                stack.append(node)
                on_stack[node] = True
            recursed = False
            children = graph[node]
            while pos < len(children):
                child = children[pos]
                pos += 1
                if child not in index:
                    work[-1] = (node, pos)
                    work.append((child, 0))
                    recursed = True
                    break
                if on_stack.get(child):
                    low[node] = min(low[node], index[child])
            if recursed:
                continue
            work[-1] = (node, pos)
            if pos >= len(children):
                work.pop()
                if work:
                    parent = work[-1][0]
                    low[parent] = min(low[parent], low[node])
                if low[node] == index[node]:
                    component = []
                    while True:
                        member = stack.pop()
                        on_stack[member] = False
                        component.append(member)
                        if member == node:
                            break
                    if len(component) > 1:
                        result.append(sorted(component))

    for node in nodes:
        if node not in index:
            strongconnect(node)
    # 自環
    for src, dst in edges:
        if src == dst:
            result.append([src])
    return result


# ---------------------------------------------------------------------------
# G. JSON 參數整合去重
# ---------------------------------------------------------------------------

def flatten(obj: Any, prefix: str = "", out: Optional[Dict[str, Any]] = None,
            depth: int = 0) -> Dict[str, Any]:
    if out is None:
        out = {}
    if depth > 8:
        return out
    if isinstance(obj, dict):
        for key, value in obj.items():
            flatten(value, "%s.%s" % (prefix, key) if prefix else str(key), out, depth + 1)
    elif isinstance(obj, list):
        if obj and all(not isinstance(x, (dict, list)) for x in obj):
            out[prefix] = json.dumps(obj, ensure_ascii=False, sort_keys=True)
    else:
        out[prefix] = obj
    return out


def audit_json(files: List[Path], root: Path, max_keys: int) -> Dict[str, Any]:
    groups: Dict[str, Dict[str, List[str]]] = collections.defaultdict(
        lambda: collections.defaultdict(list))
    excluded: List[Tuple[str, str]] = []
    hashes: Dict[str, List[str]] = collections.defaultdict(list)
    config_files: List[str] = []

    for path in files:
        rel = str(path.relative_to(root))
        try:
            raw = path.read_bytes()
        except OSError:
            continue
        hashes[hashlib.blake2s(raw, digest_size=8).hexdigest()].append(rel)
        if DERIVED_JSON.search(path.name):
            excluded.append((rel, "檔名帶產物/註冊表字樣"))
            continue
        try:
            data = json.loads(raw.decode("utf-8-sig"))
        except (ValueError, UnicodeDecodeError):
            excluded.append((rel, "無法解析為 JSON"))
            continue
        if isinstance(data, list):
            excluded.append((rel, "頂層是陣列，判為資料"))
            continue
        flat = flatten(data)
        if len(flat) > max_keys:
            excluded.append((rel, "鍵數 %d 超過上限 %d，判為資料" % (len(flat), max_keys)))
            continue
        config_files.append(rel)
        for key, value in flat.items():
            groups[key][json.dumps(value, ensure_ascii=False, sort_keys=True)].append(rel)

    agreed, conflicts, single = [], [], 0
    for key, variants in groups.items():
        total = sum(len(v) for v in variants.values())
        if total == 1:
            single += 1
        elif len(variants) == 1:
            value = next(iter(variants))
            agreed.append({"key": key, "files": total, "value": value})
        else:
            conflicts.append({
                "key": key, "variants": len(variants),
                "detail": [{"value": v, "files": f} for v, f in
                           sorted(variants.items(), key=lambda kv: -len(kv[1]))]})

    duplicates = [{"hash": h, "count": len(f), "files": sorted(f)}
                  for h, f in hashes.items() if len(f) > 1]
    return {
        "config_files": config_files, "agreed": sorted(agreed, key=lambda a: a["key"]),
        "conflicts": sorted(conflicts, key=lambda c: -c["variants"]),
        "single": single, "excluded": excluded,
        "duplicates": sorted(duplicates, key=lambda d: -d["count"]),
    }


# ---------------------------------------------------------------------------
# SVG 工作流
# ---------------------------------------------------------------------------

LAYERS = [
    ("GOVERNOR", "控管 PowerShell"),
    ("SYSTEM_MANAGER", "System Manager"),
    ("ORCHESTRATOR", "Orchestrator"),
    ("ENGINE", "Engine"),
    ("LIBRARY", "Library"),
]
LAYER_COLOR = {
    "GOVERNOR": "#c96b5a", "SYSTEM_MANAGER": "#4c78a8", "ORCHESTRATOR": "#439a9a",
    "ENGINE": "#5a9e6f", "LIBRARY": "#8a8780",
}
MAX_PER_LAYER = 12


def render_workflow(nodes: Dict[str, Node], edges: List[Tuple[str, str]]) -> str:
    buckets: Dict[str, List[Node]] = {tier: [] for tier, _ in LAYERS}
    for node in nodes.values():
        if node.tier in buckets and node.latest:
            buckets[node.tier].append(node)
    for tier in buckets:
        buckets[tier].sort(key=lambda n: (-n.fan_out, -n.fan_in, n.name))

    col_w, row_h, box_w, box_h = 250, 40, 214, 26
    top = 54
    shown: Dict[str, Tuple[float, float]] = {}
    truncated: List[str] = []
    body: List[str] = []

    for col, (tier, label) in enumerate(LAYERS):
        items = buckets[tier]
        x = 14 + col * col_w
        body.append(
            '<text x="%d" y="24" class="lyr" fill="%s">%s</text>'
            '<text x="%d" y="40" class="cnt">%d</text>'
            % (x, LAYER_COLOR[tier], esc(label), x, len(items)))
        for row, node in enumerate(items[:MAX_PER_LAYER]):
            y = top + row * row_h
            shown[node.rel] = (x + box_w, y + box_h / 2)
            name = node.name if len(node.name) <= 28 else node.name[:26] + "\u2026"
            body.append(
                '<rect x="%d" y="%d" width="%d" height="%d" rx="2" fill="#fff" '
                'stroke="%s" stroke-width="1.2"/>'
                '<text x="%d" y="%d" class="nd">%s</text>'
                '<text x="%d" y="%d" class="mt">%s out%d in%d</text>'
                % (x, y, box_w, box_h, LAYER_COLOR[tier],
                   x + 7, y + 12, esc(name),
                   x + 7, y + 22, esc(node.code or node.lang), node.fan_out, node.fan_in))
        if len(items) > MAX_PER_LAYER:
            truncated.append("%s 另有 %d 個未繪" % (label, len(items) - MAX_PER_LAYER))

    left: Dict[str, Tuple[float, float]] = {}
    for col, (tier, _) in enumerate(LAYERS):
        x = 14 + col * col_w
        for row, node in enumerate(buckets[tier][:MAX_PER_LAYER]):
            left[node.rel] = (x, top + row * row_h + box_h / 2)

    drawn = 0
    for src, dst in edges:
        if src in shown and dst in left and drawn < 160:
            x1, y1 = shown[src]
            x2, y2 = left[dst]
            if x2 <= x1:
                continue
            mid = (x1 + x2) / 2
            body.append('<path d="M%.0f %.0f C%.0f %.0f %.0f %.0f %.0f %.0f" '
                        'fill="none" stroke="#c3c0b8" stroke-width="0.9"/>'
                        % (x1, y1, mid, y1, mid, y2, x2, y2))
            drawn += 1

    height = top + MAX_PER_LAYER * row_h + 24
    note = ("<div class='note'>%s</div>" % esc(" · ".join(truncated))) if truncated else ""
    return (
        '<svg viewBox="0 0 %d %d" width="100%%" style="max-width:1280px">'
        '<style>.lyr{font:600 11px DM Mono,Consolas,monospace;letter-spacing:.06em}'
        '.cnt{font:10px DM Mono,Consolas,monospace;fill:#8a8780}'
        '.nd{font:11px DM Sans,sans-serif;fill:#1e1d1a}'
        '.mt{font:9px DM Mono,Consolas,monospace;fill:#8a8780}</style>%s</svg>%s'
        % (14 + len(LAYERS) * col_w, height, "".join(body), note))


# ---------------------------------------------------------------------------
# HTML
# ---------------------------------------------------------------------------

CSS = """
:root{--bg:#f5f4f0;--paper:#fff;--ink:#1e1d1a;--line:#dbd9d3;--mute:#8a8780;
--blue:#4c78a8;--teal:#439a9a;--red:#c96b5a;--green:#5a9e6f}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--ink);margin:0;padding:28px 30px 60px;
font:13px/1.5 "DM Sans",-apple-system,"Noto Sans TC",sans-serif}
h1{font:400 21px/1.2 "Syne","DM Sans",sans-serif;margin:0 0 4px;letter-spacing:.01em}
h2{font:400 15px/1.2 "Syne","DM Sans",sans-serif;margin:30px 0 8px;
border-left:3px solid var(--ink);padding-left:9px}
.head{display:flex;align-items:center;gap:16px;border-bottom:1px solid var(--ink);
padding-bottom:16px;margin-bottom:6px}
.seal{font:400 34px/1 "Noto Serif TC",serif;border:1.5px solid var(--red);
color:var(--red);padding:6px 11px;border-radius:2px}
.sub{color:var(--mute);font:11px "DM Mono",Consolas,monospace;letter-spacing:.04em}
.lede{color:var(--mute);font-size:12px;margin:6px 0 10px;max-width:96ch}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(132px,1fr));gap:9px;margin:14px 0 4px}
.card{background:var(--paper);border:1px solid var(--line);border-radius:2px;padding:9px 11px}
.card .k{font:10px "DM Mono",Consolas,monospace;color:var(--mute);letter-spacing:.07em;text-transform:uppercase}
.card .v{font:400 21px/1.2 "Syne",sans-serif;margin-top:3px}
table{width:100%;border-collapse:collapse;background:var(--paper);
border:1px solid var(--line);font-size:12px;table-layout:fixed}
th,td{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;
vertical-align:top;word-break:break-all}
th{background:#faf9f6;font:10px "DM Mono",Consolas,monospace;color:var(--mute);
letter-spacing:.07em;text-transform:uppercase;position:sticky;top:0;z-index:2}
tr:last-child td{border-bottom:none}
.mono{font:11px "DM Mono",Consolas,monospace}
.num{text-align:right;font:11px "DM Mono",Consolas,monospace}
.pass{color:var(--green)}.fail{color:var(--red);font-weight:600}.warn{color:#b8893f}
.tag{display:inline-block;font:9px "DM Mono",Consolas,monospace;padding:1px 5px;
border-radius:2px;border:1px solid var(--line);color:var(--mute)}
.t-GOVERNOR{border-color:var(--red);color:var(--red)}
.t-SYSTEM_MANAGER{border-color:var(--blue);color:var(--blue)}
.t-ORCHESTRATOR{border-color:var(--teal);color:var(--teal)}
.t-ENGINE{border-color:var(--green);color:var(--green)}
.wrap{max-height:520px;overflow:auto;border:1px solid var(--line);border-radius:2px}
.wrap table{border:none}
.note{color:var(--mute);font:11px "DM Mono",Consolas,monospace;margin-top:6px}
.sup{background:#faf9f6;color:var(--mute)}
select,textarea{font:11px "DM Mono",Consolas,monospace;border:1px solid var(--line);
border-radius:2px;background:var(--paper);color:var(--ink);padding:2px 4px}
textarea{width:100%;height:150px;padding:9px}
button{font:11px "DM Mono",Consolas,monospace;border:1px solid var(--ink);
background:var(--paper);color:var(--ink);border-radius:2px;padding:5px 12px;
margin:0 7px 7px 0;cursor:pointer}
button:hover{background:var(--ink);color:var(--paper)}
label.pick{margin-right:8px;font-size:11px;cursor:pointer;white-space:nowrap}
"""


def table_html(rows: List[List[str]], headers: List[str],
               widths: Optional[List[str]] = None) -> str:
    if not rows:
        return '<p class="lede">（無）</p>'
    cols = ""
    if widths:
        cols = "<colgroup>%s</colgroup>" % "".join(
            '<col style="width:%s">' % w for w in widths)
    head = "".join("<th>%s</th>" % esc(h) for h in headers)
    body = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % c for c in row) for row in rows)
    return "<table>%s<thead><tr>%s</tr></thead><tbody>%s</tbody></table>" % (cols, head, body)


def build_html(ctx: Dict[str, Any]) -> str:
    gates = ctx["gates"]
    verdict = "FAIL" if any(g["status"] == "FAIL" for g in gates) else (
        "WARN" if any(g["status"] == "WARN" for g in gates) else "PASS")

    gate_rows = [[
        '<span class="mono">%s</span>' % esc(g["code"]), esc(g["title"]),
        '<span class="%s">%s</span>' % (g["status"].lower(), g["status"]),
        esc(g["detail"])] for g in gates]

    mgr_rows = []
    for row in ctx["manager_matrix"]:
        mgr_rows.append([
            "<b>%s</b>" % esc(row["category"]),
            '<span class="mono">%s</span>' % esc(row["latest"]),
            esc(row["role"]), '<span class="mono">%s</span>' % esc(row["location"]),
            '<span class="num">%d</span>' % row["count"]])

    ctl_rows = []
    for node in ctx["control_sorted"]:
        ctl_rows.append([
            '<span class="tag t-%s">%s</span>' % (node.tier, node.tier),
            '<span class="mono">%s</span>' % esc(node.code),
            '<span class="mono">%s</span>' % esc(node.rel),
            esc(node.lang), '<span class="num">%d</span>' % node.fan_out,
            '<span class="num">%d</span>' % node.fan_in,
            esc(", ".join(sorted(set(node.signals))[:4]))])

    sup_rows = [[
        '<span class="mono">%s</span>' % esc(n.rel),
        '<span class="mono">%s</span>' % esc(n.name),
        '<span class="mono">%s</span>' % esc(ver),
        esc(datetime.fromtimestamp(n.mtime).strftime("%Y-%m-%d %H:%M")),
        '<span class="mono">%s</span>' % esc(keep)] for n, ver, keep in ctx["superseded"]]

    cyc_rows = [['<span class="mono">%s</span>' % esc(" \u2192 ".join(c) + " \u2192 " + c[0])]
                for c in ctx["cycles"]]

    miss_rows = [[esc(kind), '<span class="mono">%s</span>' % esc(what), esc(detail)]
                 for kind, what, detail in ctx["missing"]]

    conf_rows = []
    for item in ctx["jsonaudit"]["conflicts"][:80]:
        detail = "<br>".join(
            '<span class="mono">%s</span> &larr; %s' % (
                esc(d["value"][:70]), esc(", ".join(d["files"][:3]) + (
                    " \u2026+%d" % (len(d["files"]) - 3) if len(d["files"]) > 3 else "")))
            for d in item["detail"][:5])
        conf_rows.append(['<span class="mono">%s</span>' % esc(item["key"]),
                          '<span class="num">%d</span>' % item["variants"], detail])

    agreed_rows = [['<span class="mono">%s</span>' % esc(a["key"]),
                    '<span class="num">%d</span>' % a["files"],
                    '<span class="mono">%s</span>' % esc(a["value"][:90])]
                   for a in ctx["jsonaudit"]["agreed"][:120]]

    dup_rows = [['<span class="num">%d</span>' % d["count"],
                 '<span class="mono">%s</span>' % esc(d["hash"]),
                 '<span class="mono">%s</span>' % "<br>".join(esc(f) for f in d["files"])]
                for d in ctx["jsonaudit"]["duplicates"][:60]]

    inv_rows = []
    for idx, node in enumerate(ctx["inventory"]):
        picks = "".join(
            '<label class="pick"><input type="radio" name="p%d" value="%s" '
            'data-f="%s" data-c="%s"%s> %s</label>'
            % (idx, val, esc(node.rel), esc(node.category),
               " checked" if val == "SKIP" else "", label)
            for val, label in (("KEEP", "保留"), ("ARCHIVE", "歸檔"), ("SKIP", "跳過")))
        opts = "".join('<option value="%s"%s>%s</option>' % (
            o, " selected" if o == node.category else "", o)
            for o in ("支援性模組", "子系統", "新增子系統", "母檔案", "子檔案", "其他"))
        inv_rows.append([
            '<span class="mono">%s</span>' % datetime.fromtimestamp(node.mtime).strftime("%Y-%m-%d %H:%M"),
            '<span class="mono">%s</span>' % esc(node.rel),
            '<span class="mono">%s</span>' % esc(node.name),
            node.path.suffix.lstrip(".").upper(),
            '<span class="num">%.1f</span>' % (node.size / 1024.0),
            '<span class="mono">%s</span>' % esc(node.code),
            ("最新" if node.latest else '<span class="warn">SUPERSEDED</span>'),
            picks,
            '<select data-f="%s" onchange="tok()">%s</select>' % (esc(node.rel), opts)])

    cards = "".join(
        '<div class="card"><div class="k">%s</div><div class="v">%s</div></div>' % (k, v)
        for k, v in ctx["cards"])

    script = """
function tok(){
 var cats={};
 document.querySelectorAll('select[data-f]').forEach(function(s){cats[s.dataset.f]=s.value;});
 var out=['==VIA-MOTHER-DECISION==','# stamp: __STAMP__',
          '# format: ACTION | CATEGORY | RELPATH'];
 document.querySelectorAll('td input[type=radio]:checked').forEach(function(r){
   if(r.value!=='SKIP'){out.push(r.value+' | '+(cats[r.dataset.f]||r.dataset.c)+' | '+r.dataset.f);}
 });
 document.getElementById('tk').value=out.join('\\n');
}
function setAll(v){
 document.querySelectorAll('td input[type=radio][value="'+v+'"]').forEach(function(r){r.checked=true;});
 tok();
}
function copyTok(){var t=document.getElementById('tk');t.select();
 document.execCommand('copy');}
function dl(){var b=new Blob([document.getElementById('tk').value],
 {type:'text/plain;charset=utf-8'});var a=document.createElement('a');
 a.href=URL.createObjectURL(b);a.download='VIA_Mother_Decision___STAMP__.txt';a.click();}
document.addEventListener('change',function(e){
 if(e.target.matches('td input[type=radio]'))tok();});
tok();
""".replace("__STAMP__", ctx["stamp"])

    return (
        "<!DOCTYPE html><html lang='zh-Hant'><head><meta charset='utf-8'>"
        "<title>VIA 母系統唯讀盤點 %s</title>"
        "<link href='https://fonts.googleapis.com/css2?family=Syne:wght@400;600&"
        "family=DM+Sans:wght@400;500&family=DM+Mono:wght@400;500&"
        "family=Noto+Serif+TC:wght@400&display=swap' rel='stylesheet'>"
        "<style>%s</style></head><body>"
        "<div class='head'><div class='seal'>理</div><div>"
        "<h1>VIA 母系統唯讀盤點 · 控制層 · 工作流</h1>"
        "<div class='sub'>%s %s · %s · 判定 <span class='%s'>%s</span></div>"
        "</div></div>"
        "<div class='sub'>root %s</div>"
        "<div class='cards'>%s</div>"

        "<h2>閘門</h2>%s"

        "<h2>Modules / Engines Workflow</h2>"
        "<p class='lede'>邊 = 實際在程式碼裡出現的字面量引用，不是宣告的架構圖。"
        "只畫每個家族的最新版本。</p>%s"

        "<h2>SYSTEM MANAGER / SUBSYSTEM MANAGER / 支援性模組 / 功能分類</h2>"
        "<p class='lede'>這張表由掃描結果推出，不是手打的。「最新入口」是實際存在、"
        "且是該家族最新版本的檔案。</p>%s"

        "<h2>控管 system managers / engines 的 PowerShell</h2>"
        "<p class='lede'>GOVERNOR = 會呼叫到 manager 或 engine 的 PowerShell。"
        "最上層控制者超過一個，代表控制權分裂 —— 沒有機制保證它們不會同時動同一批檔案。</p>"
        "<div class='wrap'>%s</div>"

        "<h2>何者最新（同家族被取代的版本）</h2>"
        "<p class='lede'>只標註，不搬動、不改名。家族鍵含父目錄；日期字串不當版本號；"
        "無版本標記者自成一家。</p><div class='wrap'>%s</div>"

        "<h2>循環依賴</h2>"
        "<p class='lede'>Tarjan 強連通分量。任一節點數大於 1 的分量就是環。</p>%s"

        "<h2>何者遺漏</h2>%s"

        "<h2>JSON 參數衝突（必須裁決）</h2>"
        "<p class='lede'>同一個鍵在多個檔案有不同的值。在裁決這些之前，"
        "任何「以某一份為準」的整併都是賭博。SSOT 只收 AGREED，衝突一個都不放。</p>%s"

        "<h2>值一致的參數（可集中管理）</h2>"
        "<p class='lede'>已寫入 <span class='mono'>%s</span>。原檔保留不動。</p>%s"

        "<h2>內容完全相同的 JSON</h2>%s"

        "<h2>檔案盤點矩陣</h2>"
        "<p class='lede'>DATE / FILE / FILENAME / FORMAT / SIZE / 編號 / 版本 / 勾選 / 分類下拉。"
        "勾選與下拉都只產生 Decision Token —— 本工具不會依 Token 動任何檔案。</p>"
        "<div class='wrap'>%s</div>"
        "<div style='margin-top:14px'>"
        "<button onclick=\"setAll('KEEP')\">全部保留</button>"
        "<button onclick=\"setAll('ARCHIVE')\">全部歸檔</button>"
        "<button onclick=\"setAll('SKIP')\">全部跳過</button>"
        "<button onclick='copyTok()'>複製 Token</button>"
        "<button onclick='dl()'>下載 Decision</button>"
        "<textarea id='tk' readonly></textarea></div>"
        "<script>%s</script></body></html>"
        % (esc(ctx["stamp"]), CSS,
           URN_SELF, VERSION, esc(ctx["generated"]), verdict.lower(), verdict,
           esc(ctx["root"]), cards,
           table_html(gate_rows, ["code", "gate", "status", "detail"],
                      ["7%", "26%", "9%", "58%"]),
           ctx["svg"],
           table_html(mgr_rows, ["category", "最新入口", "角色", "位置", "檔數"],
                      ["16%", "30%", "24%", "22%", "8%"]),
           table_html(ctl_rows, ["tier", "編號", "path", "lang", "out", "in", "控制訊號"],
                      ["12%", "16%", "32%", "6%", "6%", "6%", "22%"]),
           table_html(sup_rows, ["path", "filename", "版本", "mtime", "被誰取代"],
                      ["30%", "22%", "8%", "16%", "24%"]),
           table_html(cyc_rows, ["環"], ["100%"]),
           table_html(miss_rows, ["類型", "對象", "說明"], ["18%", "38%", "44%"]),
           table_html(conf_rows, ["鍵路徑", "版本數", "各檔的值"], ["28%", "8%", "64%"]),
           esc(ctx["ssot_path"]),
           table_html(agreed_rows, ["鍵路徑", "檔數", "值"], ["34%", "8%", "58%"]),
           table_html(dup_rows, ["份數", "hash", "檔案"], ["8%", "16%", "76%"]),
           table_html(inv_rows,
                      ["date", "file", "filename", "fmt", "kb", "編號", "版本",
                       "勾選", "分類"],
                      ["10%", "24%", "14%", "5%", "5%", "12%", "8%", "14%", "8%"]),
           script))


# ---------------------------------------------------------------------------

def run(root: Path, out_dir: Path, max_keys: int, open_browser: bool) -> int:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir.mkdir(parents=True, exist_ok=True)

    # RO01：輸出目錄不得在母系統之內
    try:
        out_dir.resolve().relative_to(root.resolve())
        inside = True
    except ValueError:
        inside = False
    fp_before = fingerprint(root)

    files = walk(root)
    nodes: Dict[str, Node] = {}
    json_files: List[Path] = []
    for path in files:
        try:
            node = Node(path, root)
        except OSError:
            continue
        node.category = categorize(node.rel)
        nodes[node.rel] = node
        if path.suffix.lower() == ".json":
            json_files.append(path)

    # B. 家族 → 最新
    families: Dict[str, List[Node]] = collections.defaultdict(list)
    for node in nodes.values():
        families[node.family].append(node)
    superseded: List[Tuple[Node, str, str]] = []
    for members in families.values():
        if len(members) < 2:
            continue
        # 同版本層級下，_sha 分身排在正本之後（正本才是 canonical）
        members.sort(key=lambda n: (n.ver or (-1, ""),
                                    0 if (n.marked and n.ver is None) else 1,
                                    n.mtime), reverse=True)
        winner = members[0]
        for loser in members[1:]:
            # 沒有版本或分身標記的檔案永不被判為被取代（補丁 3）
            if not loser.marked:
                continue
            loser.latest = False
            superseded.append((loser, "v%04d%s" % loser.ver if loser.ver else "twin",
                               winner.name))

    # C. 程式碼分析
    code_nodes = {r: n for r, n in nodes.items() if n.path.suffix.lower() in CODE_EXT}
    for node in code_nodes.values():
        analyze_code(node, read_text(node.path))

    by_name: Dict[str, List[Node]] = collections.defaultdict(list)
    for node in code_nodes.values():
        by_name[node.name.lower()].append(node)

    edges: List[Tuple[str, str]] = []
    referenced_missing: Dict[str, List[str]] = collections.defaultdict(list)
    for node in code_nodes.values():
        for ref in node.refs:
            targets = by_name.get(ref)
            if not targets:
                referenced_missing[ref].append(node.rel)
                continue
            for target in targets:
                if target.rel != node.rel:
                    edges.append((node.rel, target.rel))
    edges = sorted(set(edges))
    for src, dst in edges:
        code_nodes[src].fan_out += 1
        code_nodes[dst].fan_in += 1

    for node in code_nodes.values():
        if not node.entry and node.fan_out == 0:
            node.tier = "LIBRARY"
        elif node.fan_out > 0 and node.fan_in == 0 and node.control > 0:
            node.tier = "SYSTEM_MANAGER"
        elif node.fan_out > 0 and node.fan_in > 0:
            node.tier = "ORCHESTRATOR"
        elif node.fan_in > 0 and node.fan_out == 0:
            node.tier = "ENGINE"
        elif node.fan_out > 0:
            node.tier = "SYSTEM_MANAGER"
        else:
            node.tier = "ISOLATED"

    # GOVERNOR：呼叫到 manager/engine 的 PowerShell
    governed = {"SYSTEM_MANAGER", "ORCHESTRATOR", "ENGINE"}
    for src, dst in edges:
        source = code_nodes[src]
        if source.lang == "ps1" and code_nodes[dst].tier in governed:
            source.tier = "GOVERNOR"

    managers = [n for n in code_nodes.values()
                if n.tier in ("SYSTEM_MANAGER", "GOVERNOR") and n.latest]

    # E. 環
    cycles = find_cycles(sorted(code_nodes), edges)

    # F. 遺漏
    missing: List[Tuple[str, str, str]] = []
    for ref, callers in sorted(referenced_missing.items())[:60]:
        missing.append(("引用不到檔案", ref,
                        "被 %s 引用" % ", ".join(sorted(callers)[:3])))
    orphan_entries = [n for n in code_nodes.values()
                      if n.entry and n.fan_in == 0 and n.fan_out == 0 and n.latest]
    for node in sorted(orphan_entries, key=lambda n: n.rel)[:40]:
        missing.append(("有進入點但無人呼叫", node.rel, "孤立入口，無法從任何管線抵達"))
    subsys_root = root / "functional modules"
    if subsys_root.is_dir():
        for child in sorted(subsys_root.iterdir()):
            if not child.is_dir() or child.name in SKIP_DIRS:
                continue
            prefix = "functional modules" + os.sep + child.name + os.sep
            has_mgr = any(n.rel.startswith(prefix) and n.tier in ("SYSTEM_MANAGER", "GOVERNOR", "ORCHESTRATOR")
                          for n in code_nodes.values())
            if not has_mgr:
                missing.append(("子系統無 manager", child.name,
                                "此子系統沒有任何會派工的入口"))

    # G. JSON
    jsonaudit = audit_json(json_files, root, max_keys)
    ssot_path = out_dir / "via_parameters_ssot.json"
    ssot_path.write_text(json.dumps({
        "urn": URN_SELF, "version": VERSION, "spec": SPEC_VERSION,
        "generated_at": now(), "root": str(root),
        "note": "只收錄跨檔案值一致（AGREED）的鍵；衝突鍵不收錄",
        "keys": {a["key"]: json.loads(a["value"]) for a in jsonaudit["agreed"]},
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "via_parameter_conflicts.json").write_text(
        json.dumps(jsonaudit["conflicts"], ensure_ascii=False, indent=2), encoding="utf-8")

    # H. 自動編號
    autonum_gates: List[Dict[str, str]] = []
    if HAS_AUTONUM:
        registry = AutoNumberSSOT(out_dir)
        tier_type = {"GOVERNOR": "GOV", "SYSTEM_MANAGER": "MGR", "ORCHESTRATOR": "ORC",
                     "ENGINE": "ENG", "LIBRARY": "LIB", "ISOLATED": "MDL",
                     "UNCLASSIFIED": "MDL"}
        for node in sorted(nodes.values(), key=lambda n: n.rel):
            if node.rel in code_nodes:
                type_code = tier_type.get(node.tier, "MDL")
            elif node.path.suffix.lower() == ".json":
                type_code = "CFG"
            else:
                type_code = "MDL"
            record = registry.assign(type_code, node.family, {
                "name": node.name, "lang": node.lang, "tier": node.tier,
                "category": node.category})
            node.code = record["code"]
        for item in jsonaudit["agreed"][:400]:
            registry.assign("PRM", item["key"], {"files": item["files"]})
        registry.sweep_absent()
        registry.save()
        autonum_gates = registry.verify()
    else:
        for node in nodes.values():
            node.code = "(ENG-007 未載入)"

    fp_after = fingerprint(root)

    # 閘門
    gates: List[Dict[str, str]] = [{
        "code": "RO01", "title": "母系統唯讀",
        "status": "PASS" if (fp_before == fp_after and not inside) else "FAIL",
        "detail": "掃描前 %d 檔 %d bytes；掃描後 %d 檔 %d bytes；輸出目錄%s母系統內"
                  % (fp_before[0], fp_before[1], fp_after[0], fp_after[1],
                     "在" if inside else "不在")}, {
        "code": "A01", "title": "JSON 參數無衝突",
        "status": "PASS" if not jsonaudit["conflicts"] else "FAIL",
        "detail": "%d 個設定檔，%d 鍵一致，%d 鍵衝突，%d 鍵單一來源"
                  % (len(jsonaudit["config_files"]), len(jsonaudit["agreed"]),
                     len(jsonaudit["conflicts"]), jsonaudit["single"])}, {
        "code": "A02", "title": "唯一最上層控制者",
        "status": "PASS" if len(managers) == 1 else "FAIL",
        "detail": ("%d 個最上層控制者：%s。超過一個代表控制權分裂"
                   % (len(managers), ", ".join(sorted(n.name for n in managers)[:6]))
                   if len(managers) != 1 else "控制權集中於 %s" % managers[0].name)}, {
        "code": "A03", "title": "無內容重複的 JSON",
        "status": "PASS" if not jsonaudit["duplicates"] else "WARN",
        "detail": "%d 組內容完全相同" % len(jsonaudit["duplicates"])}, {
        "code": "A04", "title": "版本家族已收斂",
        "status": "PASS" if not superseded else "WARN",
        "detail": "%d 個家族，%d 個檔案被同家族較新版本取代（僅標註未搬動）"
                  % (len(families), len(superseded))}, {
        "code": "A05", "title": "無循環依賴",
        "status": "PASS" if not cycles else "FAIL",
        "detail": "%d 個環" % len(cycles) + (
            "：" + " / ".join("→".join(Path(m).name for m in c) for c in cycles[:3])
            if cycles else "")}, {
        "code": "A06", "title": "引用皆可解析",
        "status": "PASS" if not referenced_missing else "WARN",
        "detail": "%d 個被引用但找不到的檔名" % len(referenced_missing)}]
    gates.extend(autonum_gates)

    # Manager matrix（推導，非手打）
    def latest_names(pred) -> Tuple[str, int]:
        picked = sorted((n for n in code_nodes.values() if n.latest and pred(n)),
                        key=lambda n: (-n.fan_out, -n.control, n.name))
        names = " / ".join(n.name for n in picked[:3]) or "（掃描未發現）"
        return names, len(picked)

    sup_pred = lambda n: n.rel.lower().startswith("supportive modules")
    sub_pred = lambda n: n.rel.lower().startswith("functional modules")
    mgr_names, mgr_n = latest_names(lambda n: n.tier in ("SYSTEM_MANAGER", "GOVERNOR"))
    sub_names, sub_n = latest_names(lambda n: sub_pred(n) and n.tier in
                                    ("SYSTEM_MANAGER", "GOVERNOR", "ORCHESTRATOR"))
    sup_names, sup_n = latest_names(sup_pred)
    eng_names, eng_n = latest_names(lambda n: n.tier == "ENGINE")
    manager_matrix = [
        {"category": "SYSTEM MANAGER", "latest": mgr_names, "count": mgr_n,
         "role": "最上層派工者：有 fan-out 且無人呼叫", "location": "母系統根 / bin"},
        {"category": "SUBSYSTEM MANAGER", "latest": sub_names, "count": sub_n,
         "role": "子系統入口：在 functional modules 底下且會派工",
         "location": "functional modules"},
        {"category": "導入支援性模組", "latest": sup_names, "count": sup_n,
         "role": "被上層調用的支援層", "location": "supportive modules"},
        {"category": "功能分類 / ENGINE", "latest": eng_names, "count": eng_n,
         "role": "被呼叫、不呼叫別人的執行體", "location": "全樹"},
    ]

    inventory = sorted(nodes.values(), key=lambda n: (-n.mtime,))[:900]
    control_sorted = sorted(
        (n for n in code_nodes.values() if n.tier != "LIBRARY"),
        key=lambda n: ({"GOVERNOR": 0, "SYSTEM_MANAGER": 1, "ORCHESTRATOR": 2,
                        "ENGINE": 3}.get(n.tier, 4), -n.fan_out, n.name))[:300]

    ctx = {
        "stamp": stamp, "generated": now(), "root": str(root),
        "gates": gates, "manager_matrix": manager_matrix,
        "control_sorted": control_sorted, "superseded": superseded[:300],
        "cycles": cycles, "missing": missing, "jsonaudit": jsonaudit,
        "ssot_path": str(ssot_path), "inventory": inventory,
        "svg": render_workflow(code_nodes, edges),
        "cards": [
            ("掃描檔數", "%d" % len(nodes)),
            ("程式碼", "%d" % len(code_nodes)),
            ("最上層控制者", "%d" % len(managers)),
            ("引擎", "%d" % sum(1 for n in code_nodes.values() if n.tier == "ENGINE")),
            ("呼叫邊", "%d" % len(edges)),
            ("循環依賴", "%d" % len(cycles)),
            ("被取代版本", "%d" % len(superseded)),
            ("參數衝突", "%d" % len(jsonaudit["conflicts"])),
        ],
    }

    html_path = out_dir / ("VIA_MotherSystemAudit_%s.html" % stamp)
    html_path.write_text(build_html(ctx), encoding="utf-8")

    (out_dir / ("via_mother_workflow_%s.json" % stamp)).write_text(json.dumps({
        "urn": URN_SELF, "version": VERSION, "generated_at": now(), "root": str(root),
        "gates": gates,
        "nodes": [{"rel": n.rel, "code": n.code, "tier": n.tier, "lang": n.lang,
                   "latest": n.latest, "fan_in": n.fan_in, "fan_out": n.fan_out,
                   "category": n.category} for n in code_nodes.values()],
        "edges": [{"caller": s, "callee": d} for s, d in edges],
        "cycles": cycles,
        "superseded": [{"rel": n.rel, "superseded_by": w} for n, _, w in superseded],
        "missing": [{"kind": k, "what": w, "detail": d} for k, w, d in missing],
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print("=" * 66)
    print(" VIA 母系統唯讀盤點 %s %s" % (URN_SELF, VERSION))
    print("=" * 66)
    for gate in gates:
        print("%-5s %-22s %-5s %s" % (gate["code"], gate["title"], gate["status"],
                                      gate["detail"][:90]))
    print("-" * 66)
    print(" 報告  %s" % html_path)
    print(" SSOT  %s" % ssot_path)
    if open_browser:
        try:
            webbrowser.open(html_path.as_uri())
        except Exception:
            pass
    return 0 if all(g["status"] != "FAIL" for g in gates) else 2


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="VIA_MotherSystemAudit.py",
        description="%s %s 母系統唯讀盤點 / 控制層 / 工作流 / JSON 整合去重"
                    % (URN_SELF, VERSION))
    parser.add_argument("--root", default=DEFAULT_ROOT, help="母系統路徑")
    parser.add_argument("--out", default=DEFAULT_OUT, help="輸出目錄（必須在母系統之外）")
    parser.add_argument("--max-keys", type=int, default=400,
                        help="超過此鍵數的 JSON 視為資料而非設定")
    parser.add_argument("--no-open", action="store_true")
    args = parser.parse_args(argv)

    root = Path(args.root)
    if not root.is_dir():
        print("找不到母系統目錄：%s" % root)
        return 1
    return run(root, Path(args.out), args.max_keys, not args.no_open)


if __name__ == "__main__":
    sys.exit(main())
