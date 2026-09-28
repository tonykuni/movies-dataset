#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL237_NumberingSystem v0100 — 無所不編號:母系統 VIA → 子系統 → 類 → 分類 → 流水號(只增不減)

操作員 2026-09-28:「把自動編號註冊能力做到最強無所不編號 整測優化也編號 環境布建 lib 編號 … MDL ENG CLS FNC LIB ENV
PLCY PRMT LGC FD BI Ticker/YFinance Ticker/Bloomberg Ticker/Name/English Name/Exchange/Instrument/Currency/Unit(容許無值
得存在,台股全部/主動式台股 ETF 全部/其他參數及商品)」「總體經濟數據要如何建構編號表請自決 更新日期及資料來源及 API 來源
存入全部編號系統」「同一數據多來源可以相互取最新三值對照增加同義字 SSOT REGEX 同義字都要編號並編入 SSOT」「VIA 是母系統號
VRN VDF 是子系統號 分類分好 全部都要有分類」。

操作員續令:「VIA-VRN-MDL-CLS-FNC-LIB LIB 尾數四碼 其他都三碼連續數字」「後面加版本號在名字後面」「更新版本就要換一號」。
號碼格式(階層):VIA-<子系統>-<類><三碼>;有父層的接在父號後面:
  模組   VIA-VRN-MDL012(引擎檔 VIA-VRN-ENG005)
  類別   VIA-VRN-MDL012-CLS003
  函式   VIA-VRN-MDL012-FNC007 · 方法 VIA-VRN-MDL012-CLS003-FNC002 · 內層函式再往下接一段
  函式庫 VIA-VCGC-LIB0042(LIB 尾數四碼)
  總體經濟 VIA-VDF-MRC-US-0001(MRC-<地區>-四碼;地區取序列代號首段:US EU CN JP UK,Global = GLB)
  金融市場 VIA-VDF-FM-US-EQT-0001(FM-<地區>-<資產類別>-四碼;地區:台股 · 主動式 ETF = TW,美股 = US,指數 / 期貨 / 匯率照
           所屬市場;資產類別三碼:EQT 股票(EQUITY)· ETF · IDX 指數 · CMD 期貨商品 · CUR 匯率;操作員令「FM-US-EQT-XXXX」)
  其他   VIA-VDF-XSRC001 · VIA-VCGC-PLCY012 …(三碼連續;同一父層同一類超過 999 時自然進到四碼,不拒收)
全名:full = 號碼 + 名字 + _版本號(名字已帶版本就不重複),例 VIA-VCGC-MDL231 CGC_MDL231_MatrixPages_v0101。
版本一換就換一號:鍵 = 內容鍵@版本,新版本 = 新鍵 = 新號;舊版本的號與列留著(只增不減)。沒有版本的項目取來源冊的版本,
再沒有就記 v0100(基準)。
  母系統  VIA(只有一個)。
  子系統  VIA-01 VCGC · VIA-02 VDF · VIA-03 VRN · VIA-04 VAP · VIA-05 SUP · VIA-06 CORE,之後 functional modules 底下
          每一個子系統資料夾自動取下一號(只增)。
  類      K01 MDL … K21 XSRC(見 KINDS),只增。
  分類    每一類的分類各自編號 <類>-C001 …;每一列都有分類與分類碼,沒有「未分類」。
  每一列  code · sys · sub · sub_no · kind · kind_no · cat · cat_code · key · name · version · source(資料來源)·
          api(API 來源 / 呼叫方式)· updated_at(更新日期:資料日或來源檔最後提交時間,含時區)· numbered_at · lamp · note。
只增不減:同一個 key 永遠同一號;key 不見了,列留著、記 gone_since;子系統、類、分類的號碼也一樣。
存放:SSOT / RGX / SYN 三類整列寫進 VIA_Numbering_SSOT_v0100.json(編入 SSOT);其餘各類一類一本 JSONL
      (VIA_NumberBooks/VIA_NumberBook_<類>_v0100.jsonl),SSOT 記每本的列數與 sha。
多來源對照(XSRC):同一個數據有兩個以上來源時,各取最新三值並排,取最近的共同日期比:一致 = 綠、不一致 = 紅、
      沒有共同日期或只有一個來源 = 黃。一致的那組代號互為同義字(SYN,照 USMacro 程序冊:兩源一致才收)。
本支只彙整、不另立尺(L05):工具 / SSOT / regex / 參數 / 指數 / 測試 / 邏輯路徑沿用 CGC_MDL236 的號(alias),商品清單
問 VDF_ENG087 尾版,總經問 macro_ssot 與 USMacro 樹。只收 VCGC 呼叫;預設乾跑,--apply 才寫。零網路。
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
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REPO = VIA.parent
FM = VIA / "functional modules"
ENGINE = Path(__file__).stem
SSOT_NEW = HERE / "VIA_Numbering_SSOT_v0100.json"
BOOK_DIR = HERE / "VIA_NumberBooks"
IN_SSOT = ("SSOT", "RGX", "SYN")
COMPACT = ("CLS", "FNC")        # stored per subsystem as {code, q, api, line}; the rest is inherited from the module row
ROOT_RX = re.compile(r"^(VIA-[A-Z0-9]+-(?:MDL|ENG)\d+)")
NOT_LIVE = ("references/", "VIA_Reports/", "VIA_RetiredEngines", "_output/", "RUN_2026", "SCOPE_COPY", "new modules engines",
            "_quarantine", "BACKUP/")

SUBSYSTEMS = [  # seed order = number; later functional-module folders are appended after these (only add)
    ("VCGC", "中央治理控制台(CGC 模組 · 治理冊 · 治理執行層)"),
    ("VDF", "資料鍛造 VeritasDataForge(行情 · 總經 · 清單 · 財報庫)"),
    ("VRN", "研報引擎 VRN(研報擷取 · 欄位 · 邏輯 · 頁面)"),
    ("VAP", "視覺繪圖 VeritasAutoPlot(模板 · 圖示 · 儀表板)"),
    ("SUP", "支援模組(加速器 · 網路 · NLP · 版面 · 啟動層)"),
    ("CORE", "母系統根層(VIA.ps1 · 系統管理 · bin · docs)"),
]
FOLDER_ABBR = {"GroupIndex": "GRPIDX", "ChipWar": "CHIPWAR", "MultiFactor": "MFACTOR", "SuperDocExtractor": "SDX",
               "VIA_PEIS": "PEIS", "WorkOps": "WORKOPS", "VIA_Accelerated_Integration_v0139A_DELIVERY": "ACCINT"}
KINDS = [
    ("MDL", "模組"), ("ENG", "引擎"), ("CLS", "類別"), ("FNC", "函式"), ("LIB", "函式庫"), ("ENV", "環境與布建"),
    ("PLCY", "政策"), ("PRMT", "參數"), ("LGC", "邏輯"), ("FD", "財務數據欄位"), ("BI", "基本資料欄位"),
    ("MRC", "總體經濟"), ("FM", "金融市場商品"), ("SSOT", "SSOT 冊"), ("RGX", "正規式"), ("SYN", "同義字"),
    ("IDX", "指數與資料表"), ("TOOL", "工具"), ("TST", "測試"), ("OPT", "整測優化紀錄"), ("XSRC", "多來源對照"),
]
KIND_NO = {k: f"K{i + 1:02d}" for i, (k, _) in enumerate(KINDS)}
OLD_KIND = {"TOOL": "TOOL", "SSOT": "SSOT", "REGEX": "RGX", "PARAM": "PRMT", "INDEX": "IDX", "TEST": "TST", "PATH": "LGC"}
REGIONAL = {"MRC", "FM"}   # <類>-<地區>-四碼
INS_COLS = ("ticker", "yfinance", "bloomberg", "name", "name_en", "exchange", "instrument", "currency", "unit")


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", path.stem)
    return int(m.group(1)) if m else -1


def _newest(folder: Path, pattern: str) -> Path | None:
    hits = [p for p in folder.glob(pattern) if _vnum(p) >= 0]
    return max(hits, key=_vnum) if hits else None


def _json(path: Path | None):
    if not path or not Path(path).exists():
        return None
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _rel(path) -> str:
    try:
        return Path(path).resolve().relative_to(VIA).as_posix()
    except ValueError:
        return str(path)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S +0000")


def _version(name: str) -> str:
    m = re.search(r"_v(\d{3,5})(?:\.\w+)?$", name) or re.search(r"_v(\d{3,5})$", Path(name).stem)
    return "v" + m.group(1) if m else "—"


# ---------------------------------------------------------------- git times (one pass; date time zone)
_TIMES: dict = {}


def git_times() -> dict:
    if not _TIMES:
        out = subprocess.run(["git", "log", "--format=>%ci", "--name-only", "--", "."], cwd=VIA,
                             capture_output=True, text=True).stdout.splitlines()
        stamp = ""
        prefix = _rel(VIA) if False else "VeritasIntelligenceAnalytics/"
        for line in out:
            if line.startswith(">"):
                stamp = line[1:]
            elif line and stamp:
                rel = line[len(prefix):] if line.startswith(prefix) else line
                _TIMES.setdefault(rel, stamp)
    return _TIMES


def updated(rel: str) -> str:
    return git_times().get(rel, "uncommitted")


def live_files(*patterns) -> list:
    out = subprocess.run(["git", "ls-files", *patterns], cwd=VIA, capture_output=True, text=True).stdout.splitlines()
    return [f for f in out if not any(s in f for s in NOT_LIVE)]


# ---------------------------------------------------------------- classification
def subsystem_of(rel_or_name: str) -> str:
    s = rel_or_name.replace("\\", "/")
    name = s.rsplit("/", 1)[-1]
    for pre, sub in (("CGC_", "VCGC"), ("VDF_", "VDF"), ("VRN_", "VRN"), ("VIS_VRN", "VRN"), ("VAP_", "VAP"),
                     ("SUP_", "SUP")):
        if name.startswith(pre):
            return sub
    if re.search(r"(^|_)VRN(_|$)", name):
        return "VRN"
    if re.search(r"(^|_)VDF(_|$)", name):
        return "VDF"
    m = re.match(r"functional modules/([^/]+)/", s)
    if m:
        d = m.group(1)
        return d if d in ("VDF", "VRN", "VAP") else FOLDER_ABBR.get(d, re.sub(r"[^A-Z0-9]", "", d.upper())[:8] or "FM")
    if s.startswith("supportive modules/registry/") or s.startswith("supportive modules/VIA_Governance_Runtime/"):
        return "VCGC"
    if s.startswith("supportive modules/"):
        return "SUP"
    return "CORE"


def lamp_of(state) -> str:
    s = str(state or "").upper()
    if any(k in s for k in ("RED", "FAIL", "CONFLICT", "BROKEN", "BAD_ID", "DIFFER", "FORBID")):
        return "RED"
    if any(k in s for k in ("AMBER", "PARK", "PENDING", "NODATA", "ABSENT", "STALE", "SINGLE", "DISJOINT", "UNVERIFIED",
                            "GATED", "WAIT", "候", "待")):
        return "AMBER"
    return "GREEN"


def item(kind, key, name, cat, source, api, upd, sub=None, version="—", lamp="GREEN", note="", **extra) -> dict:
    if version in (None, "", "—"):
        version = _version(Path(str(source or "")).stem) if source else "—"
        version = version if version != "—" else "v0100"
    row = {"kind": kind, "key": key, "name": name, "cat": cat or "其他", "source": source or "—", "api": api or "—",
           "updated_at": upd or "—", "sub": sub or subsystem_of(source or key), "version": version, "lamp": lamp, "note": note}
    row.update({k: v for k, v in extra.items() if v not in (None, "", [], {})})
    return row


# ---------------------------------------------------------------- code: MDL ENG CLS FNC (+ ps1 functions)
def _args(fn) -> str:
    a = [x.arg for x in fn.args.posonlyargs + fn.args.args]
    if fn.args.vararg:
        a.append("*" + fn.args.vararg.arg)
    a += [x.arg for x in fn.args.kwonlyargs]
    if fn.args.kwarg:
        a.append("**" + fn.args.kwarg.arg)
    return ", ".join(a)


def _walk_defs(tree, prefix=""):
    for node in getattr(tree, "body", []):
        if isinstance(node, ast.ClassDef):
            q = prefix + node.name
            bases = ", ".join(ast.unparse(b) for b in node.bases)[:80]
            yield "CLS", q, node.lineno, f"class {node.name}({bases})", prefix[:-1]
            yield from _walk_defs(node, q + ".")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            q = prefix + node.name
            yield "FNC", q, node.lineno, f"{q}({_args(node)})", prefix[:-1]
            yield from _walk_defs(node, q + ".")
        elif isinstance(node, ast.stmt):
            # any compound statement (if / for / while / with / try / try* / match, async too): walk every statement list
            # it holds, including each except handler's body and each match case's body
            blocks = [getattr(node, part, None) or [] for part in ("body", "orelse", "finalbody")]
            blocks += [h.body for h in getattr(node, "handlers", None) or []]
            blocks += [c.body for c in getattr(node, "cases", None) or []]
            for block in blocks:
                if block:
                    yield from _walk_defs(_Block(block), prefix)


class _Block:
    """A bare statement list, walked like a module body."""

    def __init__(self, body):
        self.body = body


def _ledger_versions() -> dict:
    book = _json(_newest(HERE, "VIA_EngineVersion_Ledger_v*.json")) or {}
    return {r.get("path"): r.get("version") for r in book.get("rows") or []}


def code_items() -> tuple:
    """MDL/ENG per live .py/.ps1/.psm1; CLS/FNC per definition; plus the import table for LIB."""
    out, imports, envs = [], {}, {}
    ledver = _ledger_versions()
    env_rx = re.compile(r"""(?:os\.environ\.get|os\.getenv|os\.environ\.setdefault|environ\.get)\(\s*["']([A-Za-z_][A-Za-z0-9_]*)["']"""
                        r"""|os\.environ\[\s*["']([A-Za-z_][A-Za-z0-9_]*)["']\s*\]""")
    ps_env = re.compile(r"\$env:([A-Za-z_][A-Za-z0-9_]*)", re.I)
    ps_fn = re.compile(r"^\s*function\s+([A-Za-z][\w-]*)", re.I | re.M)
    for rel in live_files("*.py", "*.ps1", "*.psm1"):
        p = VIA / rel
        unread = ""
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError as exc:                      # tracked but unreadable here (sparse checkout, locked): numbered, RED
            text, unread = "", f"讀不到:{exc.__class__.__name__}"
        stem, upd, sub = Path(rel).stem, updated(rel), subsystem_of(rel)
        kind = "ENG" if re.search(r"_ENG\d|^Veritas(Celeritas|AegisNexus)", stem) else "MDL"
        ver = _version(stem) if _version(stem) != "—" else (ledver.get(rel) or "—")
        cat = Path(rel).parent.name or "root"
        is_py = rel.endswith(".py")
        lamp, note, defs = "GREEN", "", []
        if is_py:
            try:
                tree = ast.parse(text)
                defs = list(_walk_defs(tree))
                for n in ast.walk(tree):
                    if isinstance(n, ast.Import):
                        for a in n.names:
                            imports.setdefault(a.name.split(".")[0], set()).add(rel)
                    elif isinstance(n, ast.ImportFrom) and n.module and not n.level:
                        imports.setdefault(n.module.split(".")[0], set()).add(rel)
            except SyntaxError as exc:
                lamp, note = ("AMBER", "需 py3.12 才剖得動") if "f-string" in str(exc) else ("RED", f"語法錯 L{exc.lineno}")
            api = f"python {Path(rel).name}" if "__main__" in text else f"import {stem}"
            for m in env_rx.finditer(text):
                envs.setdefault(m.group(1) or m.group(2), set()).add(rel)
        else:
            defs = [("FNC", m.group(1), text.count("\n", 0, m.start()) + 1, f"{m.group(1)} (PowerShell)", "")
                    for m in ps_fn.finditer(text)]
            api = f"pwsh -File {Path(rel).name}" if rel.endswith(".ps1") else f"Import-Module {Path(rel).name}"
            for m in ps_env.finditer(text):
                envs.setdefault(m.group(1), set()).add(rel)
        if unread:
            lamp, note = "RED", unread
        out.append(item(kind, rel, stem, cat, rel, api, upd, sub, ver, lamp, note, lang=Path(rel).suffix[1:],
                        defs=len(defs)))
        for dkind, q, line, sig, parent in defs:
            out.append(item(dkind, f"{rel}::{q}", q, stem, rel, sig, upd, sub, ver, "GREEN", "", line=line,
                            parent_key=f"{rel}::{parent}" if parent else rel))
    return out, imports, envs


# ---------------------------------------------------------------- LIB
def _requirements() -> dict:
    req = {}
    for rel in live_files("*requirements*.txt", "VIA_Env_Requirements_v*.txt"):
        for line in (VIA / rel).read_text(encoding="utf-8", errors="ignore").splitlines():
            m = re.match(r"\s*([A-Za-z0-9_.\-]+)\s*([=<>!~]=?\s*[\w.*]+)?", line)
            if m and not line.strip().startswith("#"):
                req.setdefault(m.group(1).lower().replace("-", "_"), []).append((rel, (m.group(2) or "").replace(" ", "")))
    return req


def lib_items(imports: dict) -> list:
    std = set(sys.stdlib_module_names)
    stems = {Path(f).stem for f in live_files("*.py")} | {Path(f).parent.name for f in live_files("*/__init__.py")}
    req, out = _requirements(), []
    try:
        from importlib import metadata as _md
    except ImportError:
        _md = None
    for name, users in sorted(imports.items()):
        if name in stems or name.startswith(("CGC_", "SUP_", "VDF_", "VRN_", "VAP_", "VIS_", "via_", "VIA_")) or name == "__future__":
            continue
        users = sorted(users)
        upd = max((updated(u) for u in users), default="—")
        subs = {}
        for u in users:
            subs[subsystem_of(u)] = subs.get(subsystem_of(u), 0) + 1
        sub = max(subs, key=subs.get)
        if name.lower() in ("talib", "ta_lib"):
            cat, lamp, note, ver, src = "禁用(L50)", "RED", "TA-Lib 永遠禁(L50)", "—", "禁用"
        elif name in std:
            cat, lamp, note, ver, src = "標準庫", "GREEN", "本境 python " + sys.version.split()[0], "stdlib", "python stdlib"
        else:
            spec = importlib.util.find_spec(name) if re.match(r"^[A-Za-z_]\w*$", name) else None
            pins = req.get(name.lower(), [])
            ver = next((v.lstrip("=") for _, v in pins if v), "") or "未釘"   # the key follows the pin, not this machine
            here = ""
            if spec and _md:
                try:
                    here = "本境 " + _md.version(name)
                except Exception:
                    here = "本境已裝"
            cat = "第三方(清單有列)" if pins else "第三方"
            src = pins[0][0] if pins else "pip(未列清單)"
            lamp = "GREEN" if spec or pins else "AMBER"
            note = here or "本境未裝(工作站有則綠)"
        out.append(item("LIB", name, name, cat, src, f"import {name}", upd, sub, ver, lamp, note, users=len(users)))
    return out


# ---------------------------------------------------------------- ENV (variables · provisioning steps · requirement lists · tool locks)
def env_items(envs: dict) -> list:
    out = []
    for name, users in sorted(envs.items()):
        users = sorted(users)
        if re.search(r"CONSENT|ENFORCE|_PUSH$|FROM_VCGC|_YES$|APPROV", name):
            cat, note = "操作員開關", "操作員手(L07/L08),AI 不設"
        elif re.search(r"KEY|TOKEN|SECRET|PASSWORD", name):
            cat, note = "金鑰(只記名,不收值)", ""
        elif name.startswith("VIA_DB_") or name in ("VIA_DATA_HOME",):
            cat, note = "資料庫路徑", ""
        elif name.startswith(("VIA_", "VDF_", "VRN_", "VCGC_")):
            cat, note = "VIA 設定", ""
        else:
            cat, note = "系統與外部", ""
        subs = {}
        for u in users:
            subs[subsystem_of(u)] = subs.get(subsystem_of(u), 0) + 1
        api = "$env:" + name if all(u.endswith((".ps1", ".psm1")) for u in users) else "os.environ[" + repr(name) + "]"
        out.append(item("ENV", "var|" + name, name, cat, users[0], api, max(updated(u) for u in users),
                        max(subs, key=subs.get), "—", "GREEN", note, users=len(users)))
    er = _newest(HERE, "VIA_EnvRestore_Methodology_SSOT_v*.json")
    for st in (_json(er) or {}).get("steps") or []:
        out.append(item("ENV", f"step|{st.get('n')}", st.get("name") or str(st.get("n")), "布建步驟", _rel(er),
                        str(st.get("how") or "")[:160], updated(_rel(er)), "VCGC", _version(er.stem), "GREEN",
                        str(st.get("what") or "")[:120]))
    for rel in live_files("*requirements*.txt", "VIA_Env_Requirements_v*.txt"):
        out.append(item("ENV", "req|" + rel, Path(rel).name, "套件清單", rel, "pip install -r " + Path(rel).name, updated(rel)))
    lock = _newest(HERE, "VIA_ToolVersion_Lock_v*.json")
    for fam, row in ((_json(lock) or {}).get("tools") or (_json(lock) or {}).get("families") or {}).items():
        if isinstance(row, dict):
            out.append(item("ENV", "lock|" + fam, fam, "工具鎖", _rel(lock), "via-vcgc tools activate " + fam,
                            updated(_rel(lock)), "VCGC", str(row.get("version") or row.get("file") or "—"), "GREEN",
                            str(row.get("file") or row.get("name") or "")))
    boot = VIA / "supportive modules" / "bootstrap" / "sitecustomize.py"
    if boot.exists():
        out.append(item("ENV", "boot|sitecustomize", "sitecustomize.py", "啟動層", _rel(boot), "python 啟動自動載入",
                        updated(_rel(boot)), "SUP"))
    return out


# ---------------------------------------------------------------- PLCY
POLICY_FILE = re.compile(r"(?i)polic|law|complian|charter|prompt|guard|gate|red.?line|round_policy|oneway")
POLICY_SKIP = re.compile(r"(?i)^pycompile_|freeze\.lock|\.example\.|_stdout|_stderr")
RULE_LISTS = re.compile(r"(?i)^(rules?|red_lines?|laws?|lessons?|must|never|forbid\w*|principles?|prohibit\w*|gates?|order|"
                        r"hard_rules?|policy_rules?|constraints?|bans?)$")


def _clean(text, n=70) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[*`#>]+", "", str(text or ""))).strip()[:n]


def _cjk(text) -> bool:
    return bool(re.search(r"[\u3400-\u9fff]", str(text or "")))


def policy_items() -> list:
    """Laws + lessons of the laws book, every policy-type file in the tree (laws · policy · compliance · charter · prompt ·
    gate · guard), every rule inside those books, and laws cited in code/docs that the laws book does not have (RED)."""
    out = []
    laws_p = _newest(HERE, "VIA_Policy_Laws_SSOT_v*.json")
    laws = _json(laws_p) or {}
    rel = _rel(laws_p) if laws_p else ""
    have_l, have_ll = set(), set()
    for i, law in enumerate(laws.get("laws") or []):
        have_l.add(str(law.get("id")))
        st = law.get("status") or ("SUPERSEDED" if law.get("superseded_by") else "")
        out.append(item("PLCY", "law|" + str(law.get("id")), f"{law.get('id')} {_clean(law.get('zh'), 60)}",
                        "法條/" + str(law.get("cat") or "未標類"), rel, f"laws[{i}]", updated(rel), "VCGC",
                        None, "AMBER" if st else "GREEN",
                        ("被 " + str(law.get("superseded_by")) + " 取代") if law.get("superseded_by") else str(law.get("batch") or "")))
    for i, ll in enumerate(laws.get("lessons") or []):
        have_ll.add(str(ll.get("id")))
        out.append(item("PLCY", "lesson|" + str(ll.get("id")), f"{ll.get('id')} {_clean(ll.get('zh'), 60)}", "教訓",
                        rel, f"lessons[{i}]", updated(rel), "VCGC", None, "GREEN", str(ll.get("batch") or "")))
    files = [f for f in subprocess.run(["git", "ls-files", "*.json", "*.md", "*.yaml", "*.yml", "*.txt"], cwd=VIA,
                                       capture_output=True, text=True).stdout.splitlines()
             if POLICY_FILE.search(Path(f).name) and not POLICY_SKIP.search(Path(f).name)
             and not any(x in f for x in ("VIA_Reports/", "VIA_RetiredEngines", "SCOPE_COPY", "ASSETS/"))]
    for rel2 in sorted(files):
        if rel2 == rel:
            continue
        name = Path(rel2).name
        cat = ("法冊" if re.search(r"(?i)law", name) else "合規" if re.search(r"(?i)complian", name) else
               "憲章" if re.search(r"(?i)charter", name) else "提示詞" if re.search(r"(?i)prompt", name) else
               "閘門" if re.search(r"(?i)gate|guard", name) else "政策冊")
        if "references/" in rel2:
            cat += "(正本唯讀)"
        out.append(item("PLCY", "book|" + rel2, Path(rel2).stem, cat, rel2, Path(rel2).suffix[1:], updated(rel2), None,
                        _version(Path(rel2).stem)))
        if rel2.endswith(".json"):
            book = _json(VIA / rel2)

            def walk(obj, path):
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        sub = f"{path}.{k}" if path else str(k)
                        if isinstance(v, list) and RULE_LISTS.match(str(k)):
                            for j, r in enumerate(v):
                                yield f"{sub}[{j}]", r
                        elif isinstance(v, (dict, list)) and path.count(".") < 3:
                            yield from walk(v, sub)
            for path, r in walk(book, ""):
                text = r if isinstance(r, str) else (r.get("zh") or r.get("rule") or r.get("text") or r.get("id") or
                                                     json.dumps(r, ensure_ascii=False)) if isinstance(r, dict) else str(r)
                out.append(item("PLCY", f"rule|{rel2}|{path}", _clean(text), "條文/" + Path(rel2).stem[:40], rel2, path,
                                updated(rel2), None, _version(Path(rel2).stem)))
    cited_l, cited_ll = {}, {}
    grep = subprocess.run(["git", "grep", "-n", "-E", r"[(（]L[0-9]{2,3}[)）]|LL[0-9]{2,3}", "--", "*.py", "*.ps1", "*.md",
                           "*.json"], cwd=VIA, capture_output=True, text=True).stdout.splitlines()
    for line in grep:
        if any(x in line for x in ("VIA_Reports/", "RetiredEngines", "SCOPE_COPY")):
            continue
        where, _, text = line.partition(":")
        text = text.partition(":")[2]
        if not _cjk(text):                          # an English line citing (L186) is a line number, not a law
            continue
        for m in re.finditer(r"LL(\d{2,3})", text):
            cited_ll.setdefault("LL" + m.group(1).zfill(2), set()).add(where)
        for m in re.finditer(r"[(（]L(\d{2,3})[)）]", text):
            cited_l.setdefault("L" + m.group(1).zfill(2), set()).add(where)
    for lid, where in sorted(cited_l.items()):
        if lid not in have_l:
            w = sorted(where)
            out.append(item("PLCY", "missing-law|" + lid, lid + " 被引用卻不在法冊", "遺漏偵測/法條", w[0], "git grep (Lnn)",
                            updated(w[0]), "VCGC", None, "RED" if len(w) > 1 else "AMBER",
                            (f"{len(w)} 檔引用;法冊沒有這一條,補法條要操作員批准" if len(w) > 1 else
                             "只一處引用(可能是行號),候核") + " · " + ", ".join(Path(x).name for x in w[:3])))
    for lid, where in sorted(cited_ll.items()):
        if lid not in have_ll:
            w = sorted(where)
            out.append(item("PLCY", "missing-lesson|" + lid, lid + " 被引用卻不在法冊教訓", "遺漏偵測/教訓", w[0], "git grep LLnn",
                            updated(w[0]), "VCGC", None, "AMBER", f"{len(w)} 檔引用;教訓清單沒有這一條"))
    return out


# ---------------------------------------------------------------- PRMT (VDF param registry + central params) / LGC / FD / BI
def param_items() -> list:
    out = []
    reg = FM / "VDF" / "VDF_Param_Registry_v0100.json"
    book = _json(reg) or {}
    for p in book.get("params") or []:
        src = str(p.get("src") or "")
        out.append(item("PRMT", f"vdf|{src}|{p.get('name')}|{p.get('lineno')}", str(p.get("name")), Path(src).stem or "VDF",
                        _rel(reg), f"{src}:L{p.get('lineno')}", updated(_rel(reg)), "VDF", "v0100", "GREEN",
                        str(p.get("value"))[:80]))
    for k, v in (book.get("canonical") or {}).items():
        out.append(item("PRMT", "vdf-canon|" + k, k, "VDF 正典裁定", _rel(reg), "canonical." + k, updated(_rel(reg)), "VDF",
                        "v0100", "GREEN", str((v or {}).get("ruling") if isinstance(v, dict) else v)[:80]))
    cp = _newest(HERE, "VIA_Central_Params_SSOT_v*.json")
    for k, v in (_json(cp) or {}).items():
        if isinstance(v, (dict, list)):
            n = len(v)
            out.append(item("PRMT", "central|" + k, k, "中央參數冊", _rel(cp), "via-params " + k, updated(_rel(cp)), "VCGC",
                            _version(cp.stem), "GREEN", f"{n} 項"))
    return out


def logic_items() -> list:
    out = []
    la = _newest(HERE, "VIA_VRN_LogicArchitecture_SSOT_v*.json")
    book = _json(la) or {}
    for layer, body in (book.get("layers") or {}).items():
        for n in (body or {}).get("nodes") or []:
            out.append(item("LGC", f"vrn-layer|{layer}|{n.get('family')}", str(n.get("family")), layer, _rel(la),
                            str(n.get("tail") or n.get("head") or "—"), updated(_rel(la)), "VRN", str(book.get("version") or "—"),
                            "GREEN", str(n.get("role") or "")[:80]))
    el = _newest(HERE, "VRN_ExtractionLogic_SSOT_v*.json")
    for st in (_json(el) or {}).get("ladder") or []:
        out.append(item("LGC", f"vrn-ladder|{st.get('stage')}", str(st.get("stage")), "擷取階梯", _rel(el),
                        ", ".join(map(str, st.get("adapters") or []))[:120], updated(_rel(el)), "VRN", _version(el.stem)))
    for card_p in sorted(HERE.glob("VIA_Essentia_CardBook_*_v*.json")):
        for c in (_json(card_p) or {}).get("cards") or []:
            out.append(item("LGC", f"card|{card_p.stem}|{c.get('engine')}", str(c.get("engine")), "引擎卡", _rel(card_p),
                            ", ".join(map(str, c.get("verbs") or []))[:120] or str(c.get("path") or ""), updated(_rel(card_p)),
                            subsystem_of(str(c.get("engine") or "")), str(c.get("version") or "—"), "GREEN",
                            str(c.get("purpose") or "")[:80]))
    return out


def field_items() -> list:
    out = []
    vreg = FM / "VRN" / "registry"
    for fn, kind, cat_core, cat_opt in (("VRN_REPORT_BASIC_INFO_SSOT_v0100.json", "BI", "研報基本資料核心欄", "研報基本資料延伸欄"),
                                        ("VRN_REPORT_FINANCIAL_DATA_SSOT_v0100.json", "FD", "研報財務數據核心欄", "研報財務數據延伸欄")):
        p = vreg / fn
        book = _json(p) or {}
        rel = _rel(p)

        def cols(obj, want):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if re.search(want, k) and isinstance(v, list):
                        yield k, v
                    else:
                        yield from cols(v, want)
        for key, lst in cols(book, r"core_columns$"):
            for c in lst:
                name = c if isinstance(c, str) else (c.get("name") or c.get("column") or json.dumps(c, ensure_ascii=False)[:40])
                out.append(item(kind, f"{fn}|{name}", name, cat_core, rel, key, updated(rel), "VRN", "v0100"))
        for key, lst in cols(book, r"(optional|extension)_columns$"):
            for c in lst:
                name = c if isinstance(c, str) else (c.get("name") or c.get("column") or json.dumps(c, ensure_ascii=False)[:40])
                out.append(item(kind, f"{fn}|{name}", name, cat_opt, rel, key, updated(rel), "VRN", "v0100"))
        for key, lst in cols(book, r"validation_gates$"):
            for g in lst:
                gid = g.get("id") or g.get("gate") if isinstance(g, dict) else str(g)
                out.append(item(kind, f"{fn}|gate|{gid}", str(gid), "驗證閘", rel, key, updated(rel), "VRN", "v0100", "GREEN",
                                str(g.get("rule") or g.get("desc") or "")[:80] if isinstance(g, dict) else ""))
    fs = _newest(HERE, "VIA_VRN_FieldSpec_SSOT_v*.json")
    bi_keys = {"report_date", "filename", "broker", "analyst", "ticker", "yf_ticker", "bloomberg_ticker", "name", "rating"}
    for f in (_json(fs) or {}).get("fields") or []:
        k = f.get("key")
        out.append(item("BI" if k in bi_keys else "FD", "fieldspec|" + str(k), f"{k} {f.get('zh') or ''}".strip(),
                        "研報欄位規格", _rel(fs), str(f.get("source") or "—")[:120], updated(_rel(fs)), "VRN",
                        _version(fs.stem), "GREEN", str(f.get("rule") or "")[:80]))
    dr = FM / "VDF" / "VDF_TWEquity_DailyRow_Schema_v0100.json"
    for c in (_json(dr) or {}).get("columns") or []:
        name = c if isinstance(c, str) else (c.get("name") or c.get("column") or "")
        kind = "BI" if re.search(r"ticker|name|market|industry|exchange|currency", str(name), re.I) else "FD"
        out.append(item(kind, "twdaily|" + str(name), str(name), "台股日列欄", _rel(dr), "columns", updated(_rel(dr)), "VDF",
                        "v0100", "GREEN", str(c.get("zh") or c.get("desc") or "")[:80] if isinstance(c, dict) else ""))
    return out


# ---------------------------------------------------------------- MRC (macro: registry · tree adds · detail roster · agencies)
def macro_items() -> tuple:
    out, syn = [], []
    parent = FM / "VDF" / "references" / "intake" / "VIA_VDF_SSOT_b360" / "macro_ssot.json"
    ms = _json(parent) or {}
    rel = _rel(parent)
    legend, routing = ms.get("sources_legend") or {}, ms.get("fetcher_routing") or {}

    def api_of(src, fred_id):
        if fred_id and (src in ("FRED", "BLS", "BEA", "Fed", "ISM", "UMich", "ConfBoard", "FRBNY", "Treasury") or not src):
            return f"FRED series/observations?series_id={fred_id} · {routing.get('FRED', '')}"
        leg = legend.get(src) or {}
        return leg.get("endpoint") or leg.get("base") or routing.get(src) or src or "—"
    for code, row in (ms.get("series_registry") or {}).items():
        if code.startswith("_") or not isinstance(row, dict):
            continue
        src = row.get("source") or ""
        cat = "/".join(x for x in (row.get("macro_theme"), row.get("sub_theme")) if x) or code.split(".")[1]
        out.append(item("MRC", code, f"{code} {row.get('indicator') or ''}".strip(), cat, src or "macro_ssot",
                        api_of(src, row.get("fred_id")), updated(rel), "VDF", ms.get("schema_version") or "—", "GREEN",
                        "", freq=row.get("freq"), unit=row.get("unit"), fred_id=row.get("fred_id"), book=rel))
        if row.get("fred_id"):
            syn.append(("macro|" + code, [code, row["fred_id"], row.get("indicator")], "總經代號", rel, "GREEN"))
    for m in (ms.get("derived_models") or {}) if isinstance(ms.get("derived_models"), dict) else []:
        out.append(item("MRC", "derived|" + m, m, "衍生模型", "Derived", routing.get("Derived", "—"), updated(rel), "VDF"))
    tree_p = FM / "VDF" / "VDF_USMacro_Tree_v0100.json"
    tree = _json(tree_p) or {}
    for fam in tree.get("families") or []:
        fam_state = fam.get("state") or ""
        for a in fam.get("add") or []:
            out.append(item("MRC", a.get("code"), a.get("code"), f"{fam.get('id')}/{fam.get('zh') or ''}", "FRED",
                            api_of("FRED", a.get("fred_id")), a.get("date") or updated(_rel(tree_p)), "VDF", "v0100",
                            "GREEN", "實測值 " + str(a.get("value")), freq=a.get("freq"), fred_id=a.get("fred_id"), book=_rel(tree_p)))
        for d in fam.get("declared") or []:
            out.append(item("MRC", d.get("code"), d.get("code"), f"{fam.get('id')}/{fam.get('zh') or ''}", "未定來源", "—",
                            updated(_rel(tree_p)), "VDF", "v0100", "AMBER", str(d.get("why") or "")[:80], book=_rel(tree_p)))
        for pc in fam.get("parent_codes") or []:
            if fam_state:
                out.append(item("MRC", pc, pc, f"{fam.get('id')}/{fam.get('zh') or ''}", "FRED", "—", updated(_rel(tree_p)), "VDF",
                                "v0100", lamp_of(fam_state), str(fam.get("why") or fam_state)[:80], book=_rel(tree_p)))
        if fam.get("synonyms"):
            syn.append(("macro-family|" + str(fam.get("id")), [fam.get("zh")] + list(fam["synonyms"]), "總經族同義",
                        _rel(tree_p), "GREEN"))
    roster_p = FM / "VDF" / "VDF_USMacro_Detail_Fetch_Roster_v0100.json"
    for sec, rows in ((_json(roster_p) or {}).get("sections") or {}).items():
        for r in rows:
            out.append(item("MRC", r.get("key"), f"{r.get('key')} {r.get('zh') or ''}".strip(), "細目/" + sec, "FRED",
                            api_of("FRED", r.get("fred_id")), updated(_rel(roster_p)), "VDF", "v0100",
                            lamp_of(r.get("confidence")), str(r.get("confidence") or ""), fred_id=r.get("fred_id"),
                            book=_rel(roster_p)))
            if r.get("fred_id") and r.get("zh"):
                syn.append(("macro|" + str(r.get("key")), [r.get("key"), r["fred_id"], r.get("zh")], "總經代號",
                            _rel(roster_p), "GREEN"))
    return out, syn


# ---------------------------------------------------------------- FM (instrument master; nullable columns)
TW_API = {"TWSE": "https://openapi.twse.com.tw/v1/opendata/t187ap03_L",
          "TPEX": "https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O",
          "ETF": "https://openapi.twse.com.tw/v1/opendata/t187ap47_L"}


def _eng087():
    p = _newest(FM / "VDF" / "engine", "VDF_ENG087_MarketListGovernance_v*.py")
    try:
        return _load(p, "eng087_for_mdl237") if p else None
    except Exception as exc:  # the list engine missing its own deps must not stop numbering
        return type("Absent", (), {"why": str(exc)})()


CCY = {"TW": "TWD", "JP": "JPY", "KR": "KRW", "CN": "CNY", "HK": "HKD", "EU": "EUR", "US": "USD"}
FX_QUOTE = {"TWD=X": "TWD", "JPY=X": "JPY", "EURUSD=X": "USD"}          # yfinance quotes these in the quote currency
FX_UNIT = {"TWD=X": "TWD/USD", "JPY=X": "JPY/USD", "EURUSD=X": "USD/EUR"}
UNIT_OF = {"CL=F": "USD/桶", "BZ=F": "USD/桶", "GC=F": "USD/金衡盎司"}


def instrument_items() -> tuple:
    inst, syn, notes = {}, [], []

    def put(key, src, api, upd, cat, **cols):
        row = inst.setdefault(key, {"cols": {c: None for c in INS_COLS}, "sources": [], "names": set(), "cat": cat,
                                    "api": api, "updated": upd, "lamp": "GREEN", "note": ""})
        for c, v in cols.items():
            if v in (None, ""):
                continue
            if c == "name":
                row["names"].add(str(v))
            if row["cols"].get(c) in (None, ""):
                row["cols"][c] = v
            elif c in ("yfinance", "exchange") and str(row["cols"][c]) != str(v):
                row["lamp"], row["note"] = "RED", f"{c} 兩源不一:{row['cols'][c]} / {v}"
        row["sources"].append(src)
        if upd and upd > str(row["updated"]):
            row["updated"] = upd
    eng = _eng087()
    for fn, cat_of in (("load_stock_list", None), ("load_active_etfs", "主動式台股ETF")):
        res = getattr(eng, fn)() if eng is not None and hasattr(eng, fn) else {"state": "ABSENT", "why": "VDF_ENG087 尾版不在"}
        notes.append(f"{fn}: {res.get('state')} · {res.get('why') or ''}"[:160])
        for r in res.get("rows") or []:
            code = str(r.get("code") or r.get("ticker"))
            mk = r.get("market") or ("TWSE" if code.endswith("A") else None)
            put(code, "VDF_ENG087." + fn, TW_API.get("ETF" if cat_of else mk, "—"), str(res.get("as_of") or res.get("ts") or res.get("db") or "—"), cat_of or
                ("台股上市股票" if mk == "TWSE" else "台股上櫃股票"), ticker=code, yfinance=r.get("yf_ticker") or
                (code + (".TWO" if mk == "TPEX" else ".TW")), name=r.get("name"), exchange=mk, currency="TWD",
                unit="TWD/股" if not cat_of else "TWD/單位", instrument="Active ETF" if cat_of else "Stock",
                bloomberg=(code + " TT") if mk == "TWSE" or cat_of else None)
    fu = FM / "VDF" / "VDF_TW_Focus_Universe_v0100.json"
    for m in (_json(fu) or {}).get("members") or []:
        put(str(m.get("ticker")), _rel(fu), TW_API.get(m.get("market"), "—"), updated(_rel(fu)),
            "台股上市股票" if m.get("market") == "TWSE" else "台股上櫃股票", ticker=m.get("ticker"), yfinance=m.get("yfinance"),
            bloomberg=m.get("bloomberg"), name=m.get("name"), exchange=m.get("market"), instrument="Stock", currency="TWD",
            unit="TWD/股")
    ae = VIA / "supportive modules" / "VIA_FlowSystem" / "FlowSystem_v2" / "config" / "TW_Active_ETF_Registry_v0100.json"
    for e in (_json(ae) or {}).get("etfs") or []:
        t = str(e.get("ticker"))
        put(t, _rel(ae), TW_API["ETF"], updated(_rel(ae)), "主動式台股ETF", ticker=t, yfinance=t + ".TW", bloomberg=t + " TT",
            name=e.get("name"), exchange="TWSE", instrument="Active ETF", currency="TWD", unit="TWD/單位")
        if e.get("matrix_name") and e.get("matrix_name") != e.get("name"):
            inst[t]["lamp"] = "AMBER" if inst[t]["lamp"] == "GREEN" else inst[t]["lamp"]
            inst[t]["note"] = f"名稱兩源不一(候 TWSE 實連驗證):{e.get('name')} / {e.get('matrix_name')}"
    un = VIA / "supportive modules" / "VIA_FlowSystem" / "FlowSystem_v2" / "config" / "universe.json"
    for e in (_json(un) or {}).get("etfs") or []:
        t = str(e.get("ticker"))
        put(t, _rel(un), "yfinance Ticker(" + t + ")", updated(_rel(un)), "美股ETF/" + str(e.get("asset_class") or ""),
            ticker=t, yfinance=t, bloomberg=t + " US", name=e.get("name"), exchange=e.get("exchange"), instrument="ETF",
            currency=e.get("currency") or "USD", unit=(e.get("currency") or "USD") + "/股")
    fo = FM / "VDF" / "VDF_Fetch_Orders_v0100.json"
    for order in (_json(fo) or {}).get("orders") or []:
        for t in (((order.get("lanes") or {}).get("yfinance") or {}).get("targets") or []):
            yf = str(t.get("yf"))
            kind = ("期貨商品" if yf.endswith("=F") else "匯率" if yf.endswith("=X") else "指數" if yf.startswith("^") or
                    yf.endswith(".NYB") else "股票/ETF")
            if kind == "股票/ETF" and "ETF" in str(t.get("zh") or ""):
                kind = "ETF"
            region = region_of("FM", {"key": yf, "cols": {"yfinance": yf}})
            cur = FX_QUOTE.get(yf) or CCY.get(region)
            put(yf, _rel(fo), "yfinance Ticker(" + yf + ")", updated(_rel(fo)), kind, ticker=yf, yfinance=yf,
                name=t.get("zh"), instrument={"期貨商品": "Commodity Future", "匯率": "FX", "指數": "Index", "ETF": "ETF"}.get(kind, "Equity"),
                currency=cur, unit=UNIT_OF.get(yf) or FX_UNIT.get(yf) or ("點" if kind == "指數" else f"{cur}/單位" if kind == "ETF"
                                                                          else f"{cur}/股" if kind == "股票/ETF" and cur else None))
    out = []
    for key, r in sorted(inst.items()):
        names = sorted(r["names"])
        if len(names) > 1:
            syn.append(("ins|" + key, [key] + names + [r["cols"].get("yfinance"), r["cols"].get("bloomberg")], "商品名稱多源",
                        ", ".join(sorted(set(r["sources"])))[:120], "GREEN" if r["lamp"] == "GREEN" else "AMBER"))
        elif r["cols"].get("yfinance") and r["cols"]["yfinance"] != key:
            syn.append(("ins|" + key, [key, r["cols"].get("yfinance"), r["cols"].get("bloomberg")] + names, "商品代號對照",
                        r["sources"][0], "GREEN"))
        nulls = [c for c in INS_COLS if r["cols"].get(c) in (None, "")]
        out.append(item("FM", key, r["cols"].get("name") or key, r["cat"], ", ".join(sorted(set(r["sources"])))[:160],
                        r["api"], r["updated"], "VDF", "—", r["lamp"], r["note"] or (("空欄 " + "/".join(nulls)) if nulls else ""),
                        **{"cols": r["cols"]}))
    return out, syn, notes


# ---------------------------------------------------------------- XSRC (same datum, many sources: latest three each)
def _wide() -> dict:
    p = FM / "VAP" / "VDF_MacroRawWide.json"
    rows = _json(p) or []
    series = {}
    for r in rows:
        for k, v in r.items():
            if k != "date" and v is not None:
                series.setdefault(k, []).append((str(r["date"])[:10], float(v)))
    return {"_rel": _rel(p), "_upd": updated(_rel(p)), **series}


XSRC_SPECS = [
    ("US10Y", "美國10年期公債殖利率", ("abs", 0.1),
     [("FRED DGS10", "wide:DGS10", "FRED series/observations?series_id=DGS10"),
      ("yfinance ^TNX", "wide:TNX", "yfinance Ticker(^TNX)"),
      ("VDF cross_macro GOV10Y", "wide:US10Y", "vdf_global_market.duckdb::cross_macro(metric=GOV10Y)")]),
    ("US10Y3M", "美國10年-3個月利差", ("abs", 0.05),
     [("FRED T10Y3M", "wide:T10Y3M", "FRED series/observations?series_id=T10Y3M"),
      ("VDF 模型 yield_curve_10y3m", "wide:yield_curve_10y3m", "vdf_fetchers_derived::compute_models")]),
    ("WTI", "WTI 原油", ("rel", 0.02),
     [("VDF 寬表 WTI", "wide:WTI", "yfinance Ticker(CL=F)"),
      ("VDF global_daily CL=F", "wide:OIL_WTI", "vdf_global_market.duckdb::global_daily(ticker=CL=F)")]),
    ("UNRATE", "美國失業率", ("abs", 0.05),
     [("BLS LNS14000000", "agency:BLS:LNS14000000:bls", "https://api.bls.gov/publicAPI/v1/timeseries/data/LNS14000000"),
      ("FRED UNRATE", "agency:BLS:LNS14000000:fred", "FRED series/observations?series_id=UNRATE"),
      ("VDF 寬表 UNRATE", "wide:UNRATE", "FRED(寬表)")]),
    ("PAYEMS", "美國非農就業", ("rel", 0.001),
     [("BLS CES0000000001", "agency:BLS:CES0000000001:bls", "https://api.bls.gov/publicAPI/v1/timeseries/data/CES0000000001"),
      ("FRED PAYEMS", "agency:BLS:CES0000000001:fred", "FRED series/observations?series_id=PAYEMS"),
      ("VDF 寬表 NFP", "wide:NFP", "FRED(寬表)")]),
    ("TSMC_CLOSE", "台積電收盤價", ("rel", 0.001),
     [("TWSE 官方日行情", "db:vdf_tw_market.duckdb:SELECT CAST(date AS VARCHAR), close FROM tw_daily_prices WHERE ticker='2330'",
       "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"),
      ("yfinance 2330.TW", "db:vdf_global_market.duckdb:SELECT CAST(date AS VARCHAR), close FROM global_daily WHERE ticker='2330.TW'",
       "yfinance Ticker(2330.TW)")]),
]


def _agency(agency: str, sid: str, side: str) -> list:
    p = FM / "VDF" / "VDF_USMacro_Agencies_v0100.json"
    for ag in (_json(p) or {}).get("agencies") or []:
        if ag.get("id") == agency:
            for r in ag.get("rows") or []:
                if sid in (r.get("bls_id"), r.get("fred_id"), r.get("endpoint")):
                    try:
                        return [(str(r.get("date")), float(r.get(side)))]
                    except (TypeError, ValueError):
                        return []
    return []


def _db(spec: str) -> list:
    dbname, sql = spec.split(":", 1)
    eng = _eng087()
    homes = [os.environ.get("VIA_DATA_HOME") or "", str(FM / "VDF" / "output_hub" / "mega"), str(FM / "VDF" / "db")]
    path = next((Path(h) / dbname for h in homes if h and (Path(h) / dbname).exists()), None)
    if path is None and hasattr(eng, "db_tw_path") and "tw_market" in dbname:
        path = eng.db_tw_path() if eng.db_tw_path().exists() else None
    if path is None:
        return []
    try:
        import duckdb
        con = duckdb.connect(str(path), read_only=True)
        try:
            return [(str(d)[:10], float(v)) for d, v in con.execute(sql).fetchall() if v is not None]
        finally:
            con.close()
    except Exception:
        return []


def _series(loader: str, wide: dict) -> list:
    kind, _, rest = loader.partition(":")
    if kind == "wide":
        return sorted(wide.get(rest) or [])
    if kind == "agency":
        a, sid, side = rest.split(":")
        return _agency(a, sid, side)
    if kind == "db":
        return sorted(_db(rest))
    return []


def _close(a: float, b: float, tol) -> bool:
    mode, t = tol
    return abs(a - b) <= (t if mode == "abs" else t * max(abs(a), abs(b), 1e-12))


def cross_source() -> tuple:
    wide, out, syn = _wide(), [], []
    for key, zh, tol, sources in XSRC_SPECS:
        lanes = []
        for label, loader, api in sources:
            s = _series(loader, wide)
            lanes.append({"source": label, "api": api, "loader": loader.split(":")[0], "latest3": s[-3:], "n": len(s),
                          "_all": dict(s)})
        have = [ln for ln in lanes if ln["n"]]
        pairs = []
        for i in range(len(have)):
            for j in range(i + 1, len(have)):
                a, b = have[i], have[j]
                common = sorted(set(a["_all"]) & set(b["_all"]))
                if not common:
                    pairs.append({"pair": f"{a['source']} × {b['source']}", "state": "DISJOINT",
                                  "why": f"沒有共同日期(最新 {a['latest3'][-1][0]} / {b['latest3'][-1][0]})"})
                    continue
                d = common[-1]
                ok = _close(a["_all"][d], b["_all"][d], tol)
                pairs.append({"pair": f"{a['source']} × {b['source']}", "date": d, "a": a["_all"][d], "b": b["_all"][d],
                              "state": "AGREE" if ok else "DIFFER"})
        states = {p["state"] for p in pairs}
        verdict = ("NODATA" if not have else "SINGLE" if len(have) == 1 else "DIFFER" if "DIFFER" in states else
                   "AGREE" if states == {"AGREE"} else "PARTIAL" if "AGREE" in states else "DISJOINT")
        lamp = {"AGREE": "GREEN", "DIFFER": "RED"}.get(verdict, "AMBER")
        upd = max((ln["latest3"][-1][0] for ln in have), default="—")
        for ln in lanes:
            ln.pop("_all", None)
        out.append(item("XSRC", key, zh, "多來源對照/" + verdict, " · ".join(ln["source"] for ln in lanes),
                        " · ".join(ln["api"] for ln in lanes), upd, "VDF", "v0100", lamp,
                        f"{verdict} · 容差 {tol[0]} {tol[1]}", lanes=lanes, pairs=pairs))
        agreed = {p["pair"].split(" × ")[0] for p in pairs if p["state"] == "AGREE"} | \
                 {p["pair"].split(" × ")[1] for p in pairs if p["state"] == "AGREE"}
        words = [zh, key] + [w for s in sorted(agreed) for w in (s, s.split()[-1])]
        syn.append(("xsrc|" + key, words, "多來源同義(對照一致才收)" if agreed else "多來源同義(候:未一致不收)",
                    "XSRC " + key, "GREEN" if agreed else "AMBER"))
    return out, syn


# ---------------------------------------------------------------- SYN (central union book · macro · instruments · cross-source)
def split_lang(words) -> tuple:
    """(Chinese words, English words) of a synonym group; a word with any CJK character is Chinese."""
    zh = [w for w in words if _cjk(w)]
    en = [w for w in words if not _cjk(w) and re.search(r"[A-Za-z]", str(w))]
    return zh, en


def synonym_items(extra: list) -> list:
    """One row per canonical group (central union book, per scope) + macro / instrument / cross-source groups. Every group
    carries name_zh and name_en; a missing language = AMBER; a word owned by two different canonicals in one scope = RED."""
    out = []
    su = _newest(HERE, "VIA_SSOT_SynonymUnion_v*.json")
    book = _json(su) or {}
    rel = _rel(su) if su else ""
    ver = "v" + str(book.get("version") or "0100")
    ka = {k.upper(): (v or {}).get("canonical") for k, v in (book.get("key_alias") or {}).items() if isinstance(v, dict)}
    for scope, table in (book.get("scopes") or {}).items():
        groups, owners_of = {}, {}
        for raw, owners in (table or {}).items():
            canon = sorted({ka.get(str(o.get("canonical")).upper()) or o.get("canonical") for o in owners
                            if isinstance(o, dict) and o.get("canonical") and o.get("inclusion") != "DENIED"})
            owners_of[raw] = canon
            for c in canon:
                groups.setdefault(c, {c}).add(raw)
        for canon, words in sorted(groups.items()):
            words = sorted(words, key=lambda w: (not _cjk(w), w))
            # a word owned by two long canonical keys = real conflict (RED); a long key vs an old 2-3 letter short code = the
            # short-code dictionary not merged yet (AMBER, the book's own policy keeps existing short codes)
            clash = [w for w in words if len([c for c in owners_of.get(w, []) if len(c) > 3]) > 1]
            short = [w for w in words if len(owners_of.get(w, [])) > 1 and w not in clash]
            lamp = "RED" if clash else "AMBER" if short else "GREEN"
            note = (("一詞兩主(待裁定 key_alias):" + ", ".join(f"{w}→{'/'.join(owners_of[w])}" for w in clash[:4])) if clash else
                    ("短碼待併:" + ", ".join(f"{w}→{'/'.join(owners_of[w])}" for w in short[:4])) if short else
                    " ≡ ".join(words))
            out.append(item("SYN", f"union|{scope}|{canon}", canon, "中央同義冊/" + scope, rel, "scopes." + scope, updated(rel),
                            "VRN" if scope in ("broker", "rating", "rating_label", "target_price", "valuation_method") else "VCGC",
                            ver, lamp, note[:120], words=words))
    for key, words, cat, src, lamp in extra:
        words = [str(w) for w in dict.fromkeys(w for w in words if w)]
        out.append(item("SYN", key, words[0] if words else key, cat, src, "—", updated(src) if "/" in str(src) else updated(_rel(Path(__file__))),
                        subsystem_of(src), None, lamp, " ≡ ".join(words)[:120], words=words))
    return out


RULE_ZH = {"rating": "評等", "target_price": "目標價", "broker": "券商", "date": "日期", "contact": "聯絡資訊", "financial": "財務",
           "ticker": "股票代號", "period": "期別", "filename_tokens": "檔名詞元", "source_priority": "來源優先序",
           "analyst": "分析師", "currency": "幣別", "unit": "單位", "eps": "每股盈餘", "per": "本益比"}


def _rule_zh(path: str) -> str:
    parts = [p for p in re.split(r"[.\[\]]", path) if p and not p.isdigit()]
    hit = [RULE_ZH[p] for p in parts if p in RULE_ZH]
    return "・".join(dict.fromkeys(hit)) + "規則式" if hit else ""


def regex_items() -> list:
    out = []
    # RegexDict (top_shared / dropped_uncompilable) is an SSOT book in the registry: CGC_MDL236 already numbers every pattern in
    # it and r22_items() carries those codes as alias. Numbering it here again would give one pattern two numbers.

    def lamp_of_rx(pat):
        try:
            re.compile(pat)
            return "GREEN", ""
        except re.error as exc:
            return "RED", f"編不過:{exc}"
    fr = FM / "VRN" / "registry" / "VRN_FieldRules_SSOT_v0100.json"

    def walk(obj, path, zh=""):
        if isinstance(obj, dict):
            here = obj.get("zh") if isinstance(obj.get("zh"), str) else zh
            for k, v in obj.items():
                yield from walk(v, f"{path}.{k}" if path else k, here)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                yield from walk(v, f"{path}[{i}]", zh)
        elif isinstance(obj, str) and re.search(r"(regex|pattern|rx|re)(\b|\[|$)", re.sub(r"\[\d+\]$", "", path.split(".")[-1]), re.I) \
                and not _PATHLIKE_RX.search(obj):
            yield path, obj, zh
    for path, pat, zh in walk(_json(fr) or {}, ""):
        lamp, why = lamp_of_rx(pat)
        en = " ".join(p for p in re.split(r"[.\[\]_]", path) if p and not p.isdigit())
        out.append(item("RGX", "vrn-field|" + path, pat[:80], "研報欄位規則/" + (path.split(".")[1] if "." in path else path),
                        _rel(fr), path, updated(_rel(fr)), "VRN", None, lamp, why,
                        name_zh=zh or _rule_zh(path), name_en=en))
    return out


_PATHLIKE_RX = re.compile(r"^[A-Za-z]:[\\/]|\.(json|jsonl|py|ps1|txt|csv|xlsx?|md)$", re.I)


def ssot_items() -> list:
    """Every SSOT book in the tree (registry, functional modules, and the read-only canon under references/intake), with a
    Chinese and an English name. R22 codes kept as alias."""
    alias = {}
    p236 = _newest(HERE, "CGC_MDL236_NumberedCatalog_v*.py")
    led = _json(_newest(HERE, "VIA_Numbering_Ledger_v*.json")) or {}
    for k, code in (led.get("codes") or {}).items():
        if k.startswith("SSOT|"):
            alias[k.split("|", 1)[1]] = code
    out = []
    for rel in subprocess.run(["git", "ls-files", "*SSOT*.json", "*ssot*.json"], cwd=VIA, capture_output=True,
                              text=True).stdout.splitlines():
        if any(x in rel for x in ("VIA_Reports/", "RetiredEngines", "SCOPE_COPY", "ASSETS/")) or "freeze.lock" in rel:
            continue
        book = _json(VIA / rel)
        name = Path(rel).stem
        zh = ""
        if isinstance(book, dict):
            for k in ("zh", "title_zh", "name_zh", "title", "purpose", "description", "desc", "why", "rank_note", "note", "policy",
                      "source"):
                v = book.get(k)
                if isinstance(v, str) and _cjk(v):
                    zh = v[:48]
                    break
            if not zh:
                zh = next((str(v)[:48] for v in book.values() if isinstance(v, str) and _cjk(v)), "")
        en = re.sub(r"_v\d+$", "", name).replace("_", " ")
        zh_by, unknown = ("本冊", [])
        if not zh:
            zh, unknown = gloss_zh(name)
            zh_by = "詞彙表譯名"
            if unknown:
                zh = ""
        lamp = "RED" if book is None else "GREEN"
        cat = "SSOT 冊/" + ("正本唯讀" if "references/" in rel else Path(rel).parent.name)
        out.append(item("SSOT", rel, name, cat, rel, "json", updated(rel), None, None, lamp,
                        ("讀不動(JSON 壞)" if book is None else "詞彙表缺:" + ", ".join(unknown) if unknown else ""),
                        name_zh=zh, name_en=en, zh_by=zh_by if zh else "", alias=alias.get(name) or alias.get(Path(rel).name) or ""))
    return out


# ---------------------------------------------------------------- OPT (rounds · dropped balls · batch docs)
def opt_items() -> list:
    out = []
    for rel in live_files("docs/VIA_Progress_*.md"):
        for line in (VIA / rel).read_text(encoding="utf-8", errors="ignore").splitlines():
            m = re.match(r"^\|\s*(R[\w-]+)\s*\|(.*)$", line)
            if m:
                cells = [c.strip() for c in m.group(2).split("|")]
                status = cells[2] if len(cells) > 3 else "記錄"
                out.append(item("OPT", f"{Path(rel).stem}|{m.group(1)}", f"{m.group(1)} {cells[0][:60]}", "整測回合", rel,
                                "docs", updated(rel), "CORE", "—", lamp_of(status) if status != "完成" else "GREEN", status[:40]))
    for rel in live_files("docs/VIA_DroppedBalls_*.md"):
        for line in (VIA / rel).read_text(encoding="utf-8", errors="ignore").splitlines():
            m = re.match(r"^\|\s*(Z\d+\w*)\s*\|(.*)$", line)
            if m:
                cells = [c.strip() for c in m.group(2).split("|")]
                status = cells[1] if len(cells) > 1 else ""
                out.append(item("OPT", f"{Path(rel).stem}|{m.group(1)}", f"{m.group(1)} {cells[0][:60]}", "掉球追蹤", rel,
                                "docs", updated(rel), "CORE", "—", "GREEN" if re.search(r"完成|結|已", status) else lamp_of(status or "候"),
                                status[:40]))
    for rel in live_files("docs/VIA_B*_*.md"):
        m = re.match(r"VIA_B(\d+)_(.*)\.md$", Path(rel).name)
        if m:
            out.append(item("OPT", "batch|" + rel, f"批{m.group(1)} {m.group(2)[:60]}", "批次紀錄", rel, "docs", updated(rel), "CORE"))
    return out


# ---------------------------------------------------------------- glossary (English token -> 中文; only add, numbered as SYN)
ACRONYMS = {"VIA", "VRN", "VDF", "VAP", "VCGC", "CGC", "SUP", "MDL", "ENG", "FNC", "LIB", "SSOT", "FRED", "BLS", "GDP", "CPI", "PMI",
            "ISM", "TWSE", "TPEX", "CME", "RSI", "YOY", "MOM", "QA", "UI", "DB", "AI", "API", "PY", "HTML", "AIO", "VPNS", "VPT", "VETF",
            "VIS", "VSM", "VHB", "CTR", "PRD", "FUT", "CL", "EQ", "IDX", "TA", "LNK", "AK", "US", "TW", "JP", "CN", "EU", "UK", "HK",
            "KR", "ETF", "EPS", "PER", "KNO", "DUP", "SHA", "V", "A", "B", "C", "D", "E", "F", "I", "M", "Q", "NLP", "OCR", "PDF",
            "CSV", "JSON", "SQL", "ENV", "AAII", "CNN", "BEA", "ECB", "BOJ", "BOE", "VIX", "WTI", "TSMC", "ADR", "IPO", "ESG", "NAV"}
GLOSSARY = {
    "ACCELERATOR": "加速器", "ACCOUNT": "帳戶", "ACTION": "動作", "ACTIVATION": "啟用", "ACTIVE": "主動", "ADAPTIVE": "自適應",
    "ADDITIVE": "增補", "ALIAS": "別名", "ALIASES": "別名", "ANCHORED": "錨定", "ANNUAL": "年度", "APPLICABILITY": "適用性",
    "ARCHITECTURE": "架構", "ARGFIX": "引數修正", "ARTIFACT": "產物", "ARTIFACTS": "產物", "ATLANTA": "亞特蘭大", "AUDIT": "稽核",
    "BACKUP": "備份", "BASELINE": "基線", "BASIC": "基本", "BEGINNING": "起始", "BIDIRECTIONAL": "雙向", "BRAND": "品牌",
    "BRIDGE": "橋接", "BROKER": "券商", "BUILDER": "建構器", "CANDIDATE": "候選", "CANDIDATES": "候選", "CANONICAL": "正典",
    "CANONICALIZER": "正典化器", "CAPABILITIES": "能力", "CAUSE": "成因", "CENSUS": "普查", "CENTRAL": "中央", "CHAIN": "鏈",
    "CHARTLIB": "圖庫", "CHECKER": "檢查器", "CHERRYLAGOON": "櫻桃湖", "CHIP": "晶片", "CODECHAIN": "程式鏈", "COLUMN": "欄",
    "COMMIT": "提交", "COMMODITY": "商品", "COMPARISON": "比較", "COMPLETION": "完成", "COMPLIANCE": "合規", "COMPONENT": "組件",
    "CONFIDENCE": "信心", "CONFIG": "設定", "CONFLICTS": "衝突", "CONSENSUS": "共識", "CONSISTENCY": "一致性",
    "CONSOLIDATION": "整併", "CONTAINMENT": "圍堵", "CONTRACT": "契約", "CORE": "核心", "CROSS": "交叉", "DATA": "數據",
    "DATAFLOW": "資料流", "DATE": "日期", "DEDUP": "去重", "DEFINITION": "定義", "DELIVERY": "交付", "DESIGN": "設計",
    "DETAILED": "詳細", "DICT": "字典", "DIGEST": "摘要", "DRY": "乾", "DRYRUN": "乾跑", "DUALFLOW": "雙流", "DUCKDB": "DuckDB",
    "EMPTY": "空", "ENDPOINTS": "端點", "ENERGY": "能源", "ENGINE": "引擎", "ENGLISH": "英文", "ENRICHMENT": "增補", "EXECUTE": "執行",
    "EXTENSION": "延伸", "EXTRA": "額外", "EXTRACT": "擷取", "EXTRACTION": "擷取", "FACTOR": "因子", "FALSE": "偽", "FETCH": "抓取",
    "FIELD": "欄位", "FILE": "檔案", "FILELIST": "檔案清單", "FILENAME": "檔名", "FILL": "填補", "FIN": "財務", "FINAL": "最終",
    "FINANCIAL": "財務", "FINANCIALDATA": "財務數據", "FIRST": "首", "FIX": "修正", "FIXED": "固定", "FIXTURE": "夾具", "FLOW": "資金流",
    "FLOWROT": "資金輪動", "FORGE": "鍛造", "FREE": "免費", "FREEZE": "凍結", "FROM": "來自", "FULL": "完整", "FUNCTION": "函式",
    "GATE": "閘門", "GATEWAY": "閘道", "GETTER": "取值器", "GLOBAL": "全球", "GOVERNANCE": "治理", "GROUP": "族群", "HARD": "硬",
    "HEADER": "表頭", "HEARTBEAT": "心跳", "HOME": "根目錄", "HOTFIX": "熱修", "HUB": "樞紐", "HYDRA": "多頭", "HYGIENE": "衛生",
    "IMPLEMENTATION": "實作", "INCREMENTAL": "增量", "INDEX": "指數", "INFLATION": "通膨", "INFO": "資訊", "INGEST": "攝入",
    "INPUT": "輸入", "INSTITUTION": "機構", "INTAKE": "收件", "INTEGRATED": "整合", "INTEGRATION": "整合", "INTELLIGENCE": "情報",
    "INTERFACE": "介面", "INVENTORY": "清冊", "INVESTMENT": "投資", "INVESTOR": "投資人", "ITEMS": "項目", "JOIN": "接合",
    "KEY": "鍵", "KEYWORD": "關鍵字", "LAST": "最後", "LATEST": "最新", "LAWS": "法條", "LAYOUT": "版面", "LEXICON": "詞庫",
    "LIBRARY": "函式庫", "LIBS": "函式庫", "LINKS": "連結", "LIST": "清單", "LOCAL": "本機", "LOCK": "鎖", "LOGIC": "邏輯",
    "MACRO": "總經", "MANIFEST": "清單冊", "MAP": "對照", "MAPPING": "對照", "MARKET": "市場", "MASTER": "母", "MATRIX": "矩陣",
    "MERGE": "合併", "METHOD": "方法", "METHODOLOGY": "方法論", "MODULE": "模組", "MOMENTUM": "動能", "MONITOR": "監控",
    "MONTHLY": "月", "MOTHER": "母系統", "NARROW": "收窄", "NEWORD": "新訂單", "NEXUS": "樞紐", "NO": "無", "NORMALIZATION": "正規化",
    "NOTION": "Notion", "NUMPY": "NumPy", "ONE": "單一", "ONLY": "僅", "OPERATION": "作業", "OPS": "維運", "OUTPUT": "輸出",
    "OUTPUTS": "輸出", "OVERLAY": "疊加層", "PANORAMA": "全景", "PANORAMIC": "全景", "PARAMETER": "參數", "PARAMETERS": "參數",
    "PARAMS": "參數", "PARQUET": "Parquet", "PARSER": "剖析器", "PATTERNS": "樣式", "PERIOD": "期別", "PHASE": "階段",
    "PLAN": "計畫", "PLANNER": "規劃器", "PLOTLY": "Plotly", "POINTER": "指標", "POLICY": "政策", "POLYGLOT": "多語", "POSITIVE": "陽性",
    "POST": "事後", "POSTCHECK": "事後檢查", "PREVIEW": "預覽", "PROBES": "探針", "PROCESS": "程序", "PRODUCT": "產品",
    "PRODUCTION": "正式", "PROFILE": "輪廓", "PROJECT": "專案", "PYTHON": "Python", "QUANT": "量化", "RATING": "評等", "RAW": "原始",
    "READ": "讀取", "REAL": "實", "RECON": "對帳", "RECONSTRUCTION": "重建", "RECONSTRUCTOR": "重建器", "RECORD": "紀錄",
    "REFRESH": "刷新", "REGEN": "再生", "REGEX": "正規式", "REGISTER": "登錄", "REGISTRY": "登錄冊", "REMAP": "重對照", "REPAIR": "修復",
    "REPAIRED": "已修復", "REPORT": "研報", "RESEARCH": "研究", "RESOLVER": "解析器", "RESTORE": "還原", "RESULT": "結果",
    "RESULTS": "結果", "REUSE": "重用", "REVENUE": "營收", "REVIEW": "審查", "ROLLBACK": "回滾", "ROOT": "根", "ROSTER": "名冊",
    "ROTATION": "輪動", "RULE": "規則", "RULES": "規則", "RUN": "執行", "RUNTIME": "執行期", "SAFE": "安全", "SCHEMA": "結構",
    "SCOPE": "範圍", "SCRAPING": "爬取", "SEAL": "封印", "SECRET": "密鑰", "SEED": "種子", "SHARE": "分享", "SHARED": "共用",
    "SMALL": "小", "SMART": "智慧", "SNAPSHOT": "快照", "SOURCE": "來源", "SPEC": "規格", "STAGE": "階段", "STAKEHOLDERS": "利害關係人",
    "START": "啟動", "STATE": "狀態", "STATEMENT": "報表", "STATUS": "狀態", "STOCK": "股票", "STORE": "儲存", "STORY": "故事",
    "STRICT": "嚴格", "SUMMARIZER": "摘要器", "SUMMARY": "摘要", "SUPPLEMENT": "補充", "SUPPORT": "支援", "SUPPORTIVE": "支援",
    "SYNC": "同步", "SYNONYM": "同義字", "SYSTEM": "系統", "TABLE": "表", "TAXONOMY": "分類法", "TEMPLATE": "模板", "TERM": "詞",
    "TERMS": "詞彙", "TEST": "測試", "THREE": "三", "THRESHOLDS": "門檻", "TICKER": "代號", "TO": "至", "TOOL": "工具", "TOP": "頂層",
    "TRAINSET": "訓練集", "TRILINGUAL": "三語", "TRUST": "信任", "TYPE": "類型", "UNIFIED": "統一", "UNION": "聯集", "UNIT": "單位",
    "USER": "使用者", "VALIDATION": "驗證", "VERIFICATION": "驗證", "VERIFIER": "驗證器", "VERITAS": "Veritas", "VISUAL": "視覺",
    "WAR": "戰", "WEB": "網頁", "WORK": "工作", "WORKFLOW": "流程", "WORLDLINE": "世界線", "YFINANCE": "yfinance", "AKSHARE": "AKShare",
    "ENTRY": "入口", "LOG": "日誌", "CARD": "卡", "BOOK": "冊", "LAW": "法", "LESSON": "教訓", "PROMPT": "提示詞", "CHARTER": "憲章",
    "GUARD": "守門", "PRICE": "價格", "PRICES": "價格", "DAILY": "每日", "WEEKLY": "每週", "QUARTERLY": "季", "HOLDINGS": "持股",
    "UNIVERSE": "範圍名冊", "FOCUS": "焦點", "ORDERS": "訂單", "COVERAGE": "覆蓋", "AGENCIES": "機關", "TREE": "樹", "DETAIL": "細目",
    "GAP": "缺口", "LISTINGS": "上市清單", "LISTING": "上市", "CALENDAR": "行事曆", "HOLIDAY": "假日", "SECTOR": "產業",
    "INDUSTRY": "產業", "EXCHANGE": "交易所", "CURRENCY": "幣別", "NAME": "名稱", "CODE": "代碼", "PAGE": "頁", "PAGES": "頁",
    "RX": "正規式", "RE": "正規式", "PATTERN": "樣式", "LOCKED": "鎖定", "ALIGNMENT": "對齊", "VALUE": "值", "SHAPES": "形狀",
    "QUARTER": "季", "DROPPED": "已剔除", "UNCOMPILABLE": "不可編譯", "ROC": "民國", "YEAR": "年", "VALIDATOR": "驗證器",
    "VERBS": "動詞", "VERB": "動詞", "COMPACT": "緊湊", "AS": "作為", "GIVEN": "給定", "REJECTED": "已拒", "BARE": "裸",
    "VETO": "否決", "FORMATS": "格式", "NEVER": "永不", "TOUCH": "觸碰", "ISO": "ISO", "SLASH": "斜線", "WORDS": "詞",
    "YYYYMM": "年月", "YYYY": "西元年", "MM": "月", "YM": "年月", "LABEL": "標籤", "Y": "年", "YY": "兩位年", "YYMMDD": "年月日",
    "BB": "Bloomberg", "YF": "yfinance", "BLOOMBERG": "Bloomberg", "HEAD": "開頭", "MARK": "標記", "AFTER": "之後", "BEFORE": "之前",
    "CUE": "提示", "COLUMNS": "欄", "SLOT": "槽", "STOP": "停止", "OUTPUT": "輸出", "FORMAT": "格式", "REGISTRY": "登錄冊",
}


def gloss_zh(name: str) -> tuple:
    """(中文名, 不認得的詞): a book name translated word by word through GLOSSARY; acronyms stay as they are."""
    stem = re.sub(r"_sha[0-9a-f]+$", "", re.sub(r"_v\d+$", "", name))
    words, unknown = [], []
    for part in re.split(r"[_\-\s.]+", stem):
        for w in re.findall(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|\d+", part):
            u = w.upper()
            if w.isdigit() or u in ("DUP", "SHA") or re.fullmatch(r"[A-Z]", u):
                continue
            if u in GLOSSARY:
                words.append(GLOSSARY[u])
            elif u in ACRONYMS:
                words.append(u)
            else:
                unknown.append(w)
    return ("".join(w if _cjk(w) else f" {w} " for w in words).strip().replace("  ", " "), unknown)


def zh_of_path(path: str) -> tuple:
    """A field path (locked_alignment[3].pattern) in Chinese through RULE_ZH + GLOSSARY; unknown words returned."""
    words, unknown = [], []
    for part in re.split(r"[.\[\]_]+", path):
        if not part or part.isdigit():
            continue
        if part in RULE_ZH:
            words.append(RULE_ZH[part])
            continue
        for w in re.findall(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+", part):
            u = w.upper()
            if u in GLOSSARY:
                words.append(GLOSSARY[u])
            elif u in ACRONYMS:
                words.append(u)
            else:
                unknown.append(w)
    return "".join(words), unknown


def glossary_syn() -> list:
    return [("glossary|" + en, [zh, en], "詞彙表(中英)", "CGC_MDL237 GLOSSARY", "GREEN") for en, zh in sorted(GLOSSARY.items())]


# ---------------------------------------------------------------- R22 catalog (alias; its codes stay)
def r22_items() -> list:
    p = _newest(HERE, "CGC_MDL236_NumberedCatalog_v*.py")
    if not p:
        return []
    cat = _load(p, "mdl236_for_mdl237").catalog()
    out = []
    for old, kind in OLD_KIND.items():
        if kind == "SSOT":                      # ssot_items() numbers every SSOT book in the tree and keeps the R22 alias
            continue
        key = "paths" if old == "PATH" else old.lower()
        for r in cat.get(key) or []:
            if str(r.get("source") or "").startswith("VIA_Numbering_") and kind in ("RGX", "PRMT"):
                continue                        # this system's own output is not a rule source (second guard; MDL236 v0101 first)
            if kind == "LGC":
                out.append(item("LGC", "r22|" + r["code"], r.get("name") or r["code"], "流程路徑", r.get("source") or "—",
                                " → ".join(r.get("nodes") or [])[:160], r.get("source_locked_at") or r.get("locked_at") or "—",
                                subsystem_of(str(r.get("name") or "")), r.get("version") or "—", r.get("lamp") or "GREEN",
                                "", alias=r["code"]))
                continue
            src = str(r.get("source") or "")
            level = src.split("·")[0].strip() if kind in ("TST", "TOOL") else ""
            cat_name = {"TOOL": "工具/" + level, "SSOT": "SSOT 冊/" + (Path(str(r.get("name"))).parent.name or "registry"),
                        "RGX": "SSOT 與工具內式", "PRMT": "工具與規則模組參數表", "IDX": "資料表/" + src.split("·")[0].strip(),
                        "TST": "測試/" + level}.get(kind, kind)
            extra, lamp, note = {}, r.get("lamp") or "GREEN", str(r.get("note") or "")[:80]
            if kind == "RGX":
                book_zh, unk1 = gloss_zh(Path(src).stem)
                path_zh, unk2 = zh_of_path(str(r.get("name")))
                extra = {"name_zh": "" if unk1 + unk2 else f"{book_zh}・{path_zh}",
                         "name_en": f"{re.sub(r'_v[0-9]+$', '', Path(src).stem).replace('_', ' ')} · {r.get('name')}"}
                if "dropped_uncompilable" in str(r.get("name")):      # the dictionary itself records these as dropped fragments
                    lamp, note = "AMBER", "RegexDict 自記 dropped:f-string 擷取殘片,原式在 py3.12 可編 · " + note[:40]
            out.append(item(kind, "r22|" + r["code"], str(r.get("name")), cat_name, src, src, r.get("locked_at"),
                            subsystem_of(str(r.get("name")) + " " + src) if kind != "TST" else subsystem_of(str(r.get("name"))),
                            r.get("version") or "—", lamp, note, alias=r["code"], **extra))
    return out


# ---------------------------------------------------------------- numbering (append-only)
def load_state() -> dict:
    ssot = _json(_newest(HERE, "VIA_Numbering_SSOT_v*.json")) or {}
    rows = {}
    for kind in IN_SSOT:
        for r in (ssot.get("rows") or {}).get(kind) or []:
            rows[(kind, r["key"])] = r
    by_code = {}
    for kind, _ in KINDS:
        if kind in IN_SSOT or kind in COMPACT:
            continue
        p = _newest(BOOK_DIR, f"VIA_NumberBook_{kind}_v*.jsonl")
        if p:
            for line in p.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    r = json.loads(line)
                    rows[(kind, r["key"])] = r
                    by_code[r["code"]] = r
    for kind in COMPACT:
        for p in sorted(BOOK_DIR.glob(f"VIA_NumberBook_{kind}_*_v*.jsonl")):
            for line in p.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    r = expand(json.loads(line), kind, by_code)
                    if r:
                        rows[(kind, r["key"])] = r
    subs = [s["abbr"] for s in ssot.get("subsystems") or []] or [a for a, _ in SUBSYSTEMS]
    cats = {k: dict(v) for k, v in (ssot.get("categories") or {}).items()}
    return {"rows": rows, "subs": subs, "cats": cats}


def _width(kind: str) -> int:
    return 4 if kind in ("LIB",) or kind in REGIONAL else 3


MACRO_REGIONS = {"US", "EU", "CN", "JP", "UK", "TW", "KR", "HK", "DE", "FR"}
YF_REGION = {"^GSPC": "US", "^DJI": "US", "^IXIC": "US", "^SOX": "US", "^VIX": "US", "DX-Y.NYB": "US", "^TNX": "US", "^IRX": "US",
             "^FVX": "US", "^TYX": "US", "^KS11": "KR", "^N225": "JP", "1306.T": "JP", "000001.SS": "CN", "^HSI": "HK",
             "^STOXX50E": "EU", "^TWII": "TW", "^TWOII": "TW", "TWD=X": "TW", "JPY=X": "JP", "EURUSD=X": "EU"}


def region_of(kind: str, it: dict) -> str:
    """MRC: first segment of the series code (Global = GLB). FM: the instrument's market."""
    if it.get("region"):
        return it["region"]
    key = str(it.get("key") or "")
    if kind == "MRC":
        head = key.split("|")[-1].split(".")[0].upper()
        return head if head in MACRO_REGIONS else "GLB"
    cols = it.get("cols") or {}
    yf = str(cols.get("yfinance") or key)
    if yf in YF_REGION:
        return YF_REGION[yf]
    if cols.get("currency") == "TWD" or yf.endswith((".TW", ".TWO")):
        return "TW"
    if yf.endswith(".T"):
        return "JP"
    if yf.endswith("=F") or cols.get("currency") == "USD" or re.fullmatch(r"[A-Z]{1,5}", yf):   # bare yfinance symbol = US listing
        return "US"
    return "GLB"


ASSET = {"Stock": "EQT", "Equity": "EQT", "EQUITY": "EQT", "ETF": "ETF", "Active ETF": "ETF", "Index": "IDX",
         "Commodity Future": "CMD", "FX": "CUR"}


def asset_of(it: dict) -> str:
    """FM asset class, three letters (EQUITY = EQT)."""
    inst = str((it.get("cols") or {}).get("instrument") or it.get("instrument") or "")
    return ASSET.get(inst, "EQT" if not inst else re.sub(r"[^A-Z]", "", inst.upper())[:3] or "OTH")


def _head(kind: str, it: dict) -> str:
    if kind == "FM":
        return f"FM-{region_of(kind, it)}-{asset_of(it)}-"
    return f"{kind}-{region_of(kind, it)}-" if kind in REGIONAL else kind


def _full(code: str, name: str, version: str) -> str:
    name = str(name)
    return f"{code} {name}" if version in ("—", "") or name.endswith(version) else f"{code} {name}_{version}"


INHERIT = ("sys", "sub", "sub_no", "source", "version", "updated_at", "numbered_at")


def compact(r: dict) -> dict:
    out = {"code": r["code"], "q": r["name"], "api": r.get("api"), "line": r.get("line")}
    for k in ("lamp", "note", "gone_since", "reclassified_to"):
        if r.get(k) and not (k == "lamp" and r[k] == "GREEN"):
            out[k] = r[k]
    return out


def expand(c: dict, kind: str, by_code: dict) -> dict | None:
    m = ROOT_RX.match(c.get("code", ""))
    root = by_code.get(m.group(1)) if m else None
    if not root:
        return None
    rel = root.get("source")
    row = {k: root.get(k) for k in INHERIT}
    row.update({"code": c["code"], "kind": kind, "kind_no": KIND_NO[kind], "name": c.get("q"), "api": c.get("api"),
                "line": c.get("line"), "cat": root.get("name"), "key": f"{rel}::{c.get('q')}@{root.get('version')}",
                "lamp": c.get("lamp", "GREEN"), "note": c.get("note", "")})
    row["full"] = _full(row["code"], row["name"], row["version"])
    for k in ("gone_since", "reclassified_to"):
        if c.get(k):
            row[k] = c[k]
    return row


def assign(items: list, state: dict) -> dict:
    """Hierarchical codes, append only. Key = content key @ version (a new version is a new key, so a new number)."""
    rows, subs, cats, stamp = state["rows"], state["subs"], state["cats"], _now()
    counters, by_base = {}, {}
    for (kind, _), r in rows.items():
        m = (re.match(r"^(.*)-(" + kind + r"(?:-[A-Z]+)+-)(\d+)$", r.get("code", "")) if kind in REGIONAL else
             re.match(r"^(.*)-(" + kind + r")(\d+)$", r.get("code", "")))
        if m:
            counters[(m.group(1), m.group(2))] = max(counters.get((m.group(1), m.group(2)), 0), int(m.group(3)))
    seen = set()
    for it in items:
        kind, key = it["kind"], f"{it['key']}@{it['version']}"
        if (kind, key) in seen:
            continue
        seen.add((kind, key))
        if it["sub"] not in subs:
            subs.append(it["sub"])
        kc = cats.setdefault(kind, {})
        if it["cat"] not in kc:
            kc[it["cat"]] = f"{kind}-C{len(kc) + 1:03d}"
        old = rows.get((kind, key))
        if old:
            code, sub, first = old["code"], old["sub"], old.get("numbered_at") or stamp
        else:
            sub = it["sub"]
            prefix = by_base.get(it.get("parent_key")) or f"VIA-{sub}"
            head = _head(kind, it)
            n = counters.get((prefix, head), 0) + 1
            counters[(prefix, head)] = n
            code, first = f"{prefix}-{head}{n:0{_width(kind)}d}", stamp
        by_base[it["key"]] = code
        new = {"code": code, "full": _full(code, it["name"], it["version"]), "sys": "VIA", "sub": sub,
               **({"region": region_of(kind, it)} if kind in REGIONAL else {}),
               **({"asset": asset_of(it)} if kind == "FM" else {}),
               "sub_no": f"VIA-{subs.index(sub) + 1:02d}", "kind": kind, "kind_no": KIND_NO[kind], "cat_code": kc[it["cat"]],
               **{k: v for k, v in it.items() if k not in ("sub", "kind", "key")}, "key": key, "numbered_at": first}
        if old and old.get("sub") != it["sub"]:
            new["reclassified_to"] = it["sub"]
        rows[(kind, key)] = new
    kinds_now = {i["kind"] for i in items}
    for (kind, key), r in rows.items():
        if (kind, key) not in seen and kind in kinds_now:
            r.setdefault("gone_since", stamp)
            r["lamp"] = "AMBER"
    return state


def collect() -> tuple:
    items, notes = [], {}
    code, imports, envs = code_items()
    items += code + lib_items(imports) + env_items(envs) + policy_items() + param_items() + logic_items() + field_items()
    mac, syn1 = macro_items()
    ins, syn2, notes["ins"] = instrument_items()
    xs, syn3 = cross_source()
    items += mac + ins + xs + ssot_items() + regex_items() + synonym_items(syn1 + syn2 + syn3 + glossary_syn()) + opt_items() + r22_items()
    return bilingual(items), notes


def bilingual(items: list) -> list:
    """SSOT · RGX · SYN carry both a Chinese and an English name. Filled from the row itself when it can be; a language
    still missing turns a green row AMBER with the reason (never invented)."""
    for it in items:
        if it["kind"] not in IN_SSOT:
            continue
        if it["kind"] == "SYN":
            zh, en = split_lang(it.get("words") or [it["name"]])
            it.setdefault("name_zh", " / ".join(zh[:6]))
            it.setdefault("name_en", " / ".join(en[:6]))
        else:
            it.setdefault("name_zh", it["name"] if _cjk(it["name"]) else "")
            it.setdefault("name_en", it["name"] if not _cjk(it["name"]) else "")
        miss = [x for x, v in (("缺中文", it.get("name_zh")), ("缺英文", it.get("name_en"))) if not v]
        if miss:
            it["lang"] = "·".join(miss)
            if it["lamp"] == "GREEN":
                it["lamp"] = "AMBER"
                it["note"] = ("·".join(miss) + " " + str(it.get("note") or "")).strip()[:120]
    return items


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def build(apply: bool = False) -> dict:
    items, notes = collect()
    state = assign(items, load_state())
    by_kind = {}
    for (kind, _), r in state["rows"].items():
        by_kind.setdefault(kind, []).append(r)
    for rows in by_kind.values():
        rows.sort(key=lambda r: r["code"])
    books = {}
    ssot = {"schema": "VIA.NumberingSSOT.v1", "append_only": True, "engine": ENGINE, "built_at": _now(),
            "format": "VIA-<子系統>-<類><三碼>[-<子類><三碼>…];LIB 四碼;全名 = 號碼 名字_版本",
            "rule": "鍵 = 內容鍵@版本:同鍵永遠同號,版本一換就是新鍵新號;新號取同父層同類的下一號(連續);"
                    "舊號不改不刪(不見了記 gone_since);子系統 · 類 · 分類號碼同樣只增",
            "mother": {"code": "VIA", "zh": "Veritas Intelligence Analytics 母系統"},
            "subsystems": [{"no": f"VIA-{i + 1:02d}", "abbr": a, "zh": dict(SUBSYSTEMS).get(a) or ("functional modules/" + next(
                (d for d, x in FOLDER_ABBR.items() if x == a), a))} for i, a in enumerate(state["subs"])],
            "kinds": [{"no": KIND_NO[k], "kind": k, "zh": zh} for k, zh in KINDS],
            "categories": state["cats"], "row_fields": ["code", "full", "sys", "sub", "sub_no", "kind", "kind_no", "cat", "cat_code", "key",
                                                        "name", "version", "source", "api", "updated_at", "numbered_at", "lamp",
                                                        "note"],
            "instrument_columns": {"ticker": "Ticker", "yfinance": "YFinance Ticker", "bloomberg": "Bloomberg Ticker",
                                   "name": "Name", "name_en": "English Name", "exchange": "Exchange", "instrument": "Instrument",
                                   "currency": "Currency", "unit": "Unit", "_rule": "容許無值(null)存在"},
            "notes": notes, "books": {}, "rows": {k: by_kind.get(k, []) for k in IN_SSOT}}
    for kind, _ in KINDS:
        rows = by_kind.get(kind, [])
        if kind in IN_SSOT:
            ssot["books"][kind] = {"in": "rows." + kind, "n": len(rows)}
            continue
        if kind in COMPACT:
            per = {}
            for r in rows:
                per.setdefault(r["sub"], []).append(r)
            ssot["books"][kind] = {"n": len(rows), "compact": ["code", "q", "api", "line"], "inherit": list(INHERIT) + ["cat"],
                                   "inherit_rule": "號碼前綴 VIA-<子系統>-MDL### / ENG### 就是所屬模組列;來源 · 版本 · 更新日 · 子系統 · "
                                                   "分類(= 模組名)都從那一列繼承", "files": {}}
            for sub, sub_rows in sorted(per.items()):
                text = "".join(json.dumps(compact(r), ensure_ascii=False, separators=(",", ":")) + "\n" for r in sub_rows)
                path = _newest(BOOK_DIR, f"VIA_NumberBook_{kind}_{sub}_v*.jsonl") or BOOK_DIR / f"VIA_NumberBook_{kind}_{sub}_v0100.jsonl"
                books[f"{kind}_{sub}"] = (path, text)
                ssot["books"][kind]["files"][sub] = {"file": _rel(path), "n": len(sub_rows), "sha": _sha(text)}
            continue
        text = "".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in rows)
        path = _newest(BOOK_DIR, f"VIA_NumberBook_{kind}_v*.jsonl") or BOOK_DIR / f"VIA_NumberBook_{kind}_v0100.jsonl"
        books[kind] = (path, text)
        ssot["books"][kind] = {"file": _rel(path), "n": len(rows), "sha": _sha(text)}
    if apply:
        BOOK_DIR.mkdir(parents=True, exist_ok=True)
        for path, text in books.values():
            path.write_text(text, encoding="utf-8", newline="")
        (_newest(HERE, "VIA_Numbering_SSOT_v*.json") or SSOT_NEW).write_text(
            json.dumps(ssot, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="")
    lamps = {}
    for rows in by_kind.values():
        for r in rows:
            lamps[r["lamp"]] = lamps.get(r["lamp"], 0) + 1
    matrix = {}
    for (kind, _), r in state["rows"].items():
        matrix.setdefault(r["sub"], {}).setdefault(kind, 0)
        matrix[r["sub"]][kind] += 1
    return {"via": "vcgc", "door": ENGINE, "apply": apply, "total": sum(len(v) for v in by_kind.values()),
            "kinds": {k: len(by_kind.get(k, [])) for k, _ in KINDS}, "subsystems": state["subs"], "lamps": lamps,
            "matrix": matrix, "notes": notes, "ssot": ssot}


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
        return 2
    rep = build("--apply" in args)
    rep.pop("ssot")
    print(json.dumps(rep, ensure_ascii=False, indent=1))
    return 0


def selftest() -> int:
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + note) if note else ''}")

    chk("① 子系統歸屬:CGC→VCGC · VDF→VDF · VRN→VRN · 其他功能夾自取", subsystem_of("x/CGC_MDL1_v0100.py") == "VCGC" and
        subsystem_of("functional modules/VDF/a.json") == "VDF" and subsystem_of("VIA_VRN_FieldSpec_SSOT_v0100.json") == "VRN"
        and subsystem_of("functional modules/GroupIndex/x.py") == "GRPIDX" and subsystem_of("VIA.ps1") == "CORE")
    st = {"rows": {}, "subs": [a for a, _ in SUBSYSTEMS], "cats": {}}
    f1 = "functional modules/VRN/engine/VRN_MDL009_X_v0100.py"
    a = [item("MDL", f1, "VRN_MDL009_X_v0100", "engine", f1, "import", "t", "VRN", "v0100"),
         item("CLS", f1 + "::K", "K", "VRN_MDL009_X_v0100", f1, "class K()", "t", "VRN", "v0100", parent_key=f1),
         item("FNC", f1 + "::K.run", "K.run", "VRN_MDL009_X_v0100", f1, "K.run(self)", "t", "VRN", "v0100", parent_key=f1 + "::K"),
         item("FNC", f1 + "::main", "main", "VRN_MDL009_X_v0100", f1, "main()", "t", "VRN", "v0100", parent_key=f1),
         item("LIB", "duckdb", "duckdb", "第三方", "req", "import duckdb", "t", "VRN", "1.5.5"),
         item("MRC", "US.X", "x", "Prices/CPI", "FRED", "api", "2026-09-01", "VDF", "v0100"),
         item("MRC", "US.Y", "y", "Labor", "FRED", "api", "2026-09-01", "VDF", "v0100")]
    assign(a, st)
    c1 = {k: r["code"] for k, r in st["rows"].items()}
    k = lambda kind, key, v="v0100": (kind, f"{key}@{v}")
    chk("② 階層號 MDL/CLS/FNC 三碼、LIB 四碼、其他三碼", c1[k("MDL", f1)] == "VIA-VRN-MDL001" and
        c1[k("CLS", f1 + "::K")] == "VIA-VRN-MDL001-CLS001" and c1[k("FNC", f1 + "::K.run")] == "VIA-VRN-MDL001-CLS001-FNC001"
        and c1[k("FNC", f1 + "::main")] == "VIA-VRN-MDL001-FNC001" and c1[k("LIB", "duckdb", "1.5.5")] == "VIA-VRN-LIB0001"
        and c1[k("MRC", "US.Y")] == "VIA-VDF-MRC-US-0002", c1[k("FNC", f1 + "::K.run")])
    chk("②b 全名 = 號碼 名字_版本", st["rows"][k("MRC", "US.X")]["full"] == "VIA-VDF-MRC-US-0001 x_v0100" and
        st["rows"][k("MDL", f1)]["full"] == "VIA-VRN-MDL001 VRN_MDL009_X_v0100")
    assign([a[6], item("MRC", "US.X", "x", "Prices/CPI", "FRED", "api", "t", "VDF", "v0101"),
            item("MRC", "US.Z", "z", "Labor", "FRED", "api", "t", "VDF", "v0100")], st)
    c2 = {kk: r["code"] for kk, r in st["rows"].items()}
    chk("③ 版本一換就換一號,舊號留著;新鍵接連續號", c2[k("MRC", "US.X", "v0101")] == "VIA-VDF-MRC-US-0003" and
        c2[k("MRC", "US.X")] == "VIA-VDF-MRC-US-0001" and c2[k("MRC", "US.Z")] == "VIA-VDF-MRC-US-0004" and
        all(c2[x] == v for x, v in c1.items()) and "gone_since" in st["rows"][k("MRC", "US.X")])
    fm = {"kind": "FM", "key": "2330", "cols": {"yfinance": "2330.TW", "currency": "TWD"}}
    st2 = {"rows": {}, "subs": ["VDF"], "cats": {}}
    assign([item("FM", "NVDA", "NVIDIA", "股票", "f", "api", "t", "VDF", "v0100", cols={"yfinance": "NVDA", "currency": "USD",
                                                                                    "instrument": "Equity"}),
            item("FM", "SPY", "SPY", "ETF", "f", "api", "t", "VDF", "v0100", cols={"yfinance": "SPY", "currency": "USD",
                                                                              "instrument": "ETF"}),
            item("FM", "AAPL", "Apple", "股票", "f", "api", "t", "VDF", "v0100", cols={"yfinance": "AAPL", "currency": "USD",
                                                                                 "instrument": "Stock"})], st2)
    fmc = sorted(r["code"] for r in st2["rows"].values())
    chk("③b 總經 MRC-<地區>-四碼 · 金融市場 FM-<地區>-<類別>-四碼(EQUITY = EQT)", region_of("MRC", {"key": "Global.Oil"}) == "GLB"
        and region_of("FM", fm) == "TW" and region_of("FM", {"key": "^N225"}) == "JP" and
        fmc == ["VIA-VDF-FM-US-EQT-0001", "VIA-VDF-FM-US-EQT-0002", "VIA-VDF-FM-US-ETF-0001"], " · ".join(fmc))
    chk("④ 每列都有分類與分類碼", all(r.get("cat") and re.match(r"^[A-Z]+-C\d{3}$", r.get("cat_code", "")) for r in st["rows"].values()))
    wide = {"A": [("2026-01-01", 1.0), ("2026-01-02", 1.02), ("2026-01-03", 1.04)], "B": [("2026-01-02", 1.03), ("2026-01-03", 1.2)]}
    lanes = [dict(latest3=wide[k][-3:], _all=dict(wide[k])) for k in "AB"]
    d = sorted(set(lanes[0]["_all"]) & set(lanes[1]["_all"]))[-1]
    mdl = st["rows"][k("MDL", f1)]
    meth = st["rows"][k("FNC", f1 + "::K.run")]
    back = expand(compact(meth), "FNC", {mdl["code"]: mdl})
    chk("④b CLS/FNC 壓縮存、讀回繼承模組列(號 · 鍵 · 來源 · 版本 · 更新日不變)", back and back["code"] == meth["code"] and
        back["key"] == meth["key"] and back["source"] == mdl["source"] and back["version"] == "v0100")
    src = ("try:\n    import x\nexcept ImportError:\n    def tbl(): pass\n    class _E: pass\n"
           "with open('f') as h:\n    def w(): pass\nmatch 1:\n    case 1:\n        def m(): pass\n"
           "for i in []:\n    pass\nelse:\n    def e(): pass\n")
    names = {q for _, q, *_ in _walk_defs(ast.parse(src))}
    chk("④c except / with / match / for-else 裡的定義都收(不漏編)", names == {"tbl", "_E", "w", "m", "e"}, ", ".join(sorted(names)))
    chk("⑤ 多來源對照:取最近共同日期比、容差外 = 不一致", d == "2026-01-03" and not _close(1.04, 1.2, ("abs", 0.05)) and
        _close(4.48, 4.422, ("abs", 0.1)))
    chk("⑥ TA-Lib 進 LIB = 紅(L50)", lib_items({"talib": {"supportive modules/x.py"}})[0]["lamp"] == "RED")
    chk("⑦ 不經 VCGC 就拒跑", os.environ.get("VIA_FROM_VCGC") == "YES" or main([]) == 2)
    ok = all(results)
    print(f"  {ENGINE} selftest {sum(results)}/{len(results)} {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
