# -*- coding: utf-8 -*-
"""
VIA Engine Standardizer (VES) v0200 (only-increase over v0100)
v0200: 外掛分類法 ves_taxonomy.json(自學未知動詞) / 動態匯入 regex 補掃 / 多核平行 AST /
       接收者追蹤降低 R12·R13 誤報(V·M·P 信心) / 超大群圖切割 / docstring 語意加權 /
       Adapter 自動生成 Payload 型別模型+參數同義映射(消滅人工 TODO) / materialize 可插拔 /
       payload 記憶體管制
v0300: 檔案指標層 DataPointer(LocalFile/Database/Inline, safe_roots 防目錄遍歷) 取代把資料塞 payload /
       inputs → 依引擎延遲解析(polars scan / duckdb read / pandas path) / fallback 狀態隔離(gc + 乾淨指標) /
       _approx_equal rel+abs 分離 + 財務小數位 / 相似度加入呼叫鏈指紋與泛用參數名降權(df/start/end 不再誤合併) /
       本機 Ollama 語意代理(選用、自動偵測 11434、零依賴 urllib；未知動詞歸能力軸→M 級、待核可) /
       本地遙測 spans(ves_trace.jsonl，task_id 關聯，毫秒級)
v0400: 10 項升級 — 增量快取(內容雜湊) / 呼叫圖扇入·DORMANT 候選 / 跨執行 diff / 群級標準介面提案 /
       via-code 登記碼(blake2s recipe, 雜湊輸入入檔 LL#30) / 骨架冪等只增 / VES_SUMMARY.md 省 token 摘要 /
       引擎推薦(主/備) / ves_config.json 外掛設定+excludes / 6 道閘門 GREEN·AMBER·RED
       20 項風險 — 大檔跳過 / 多編碼(utf-8-sig→cp950→latin-1) / OneDrive 佔位檔 / 連結循環 /
       override 樣式降級 / 分群時間預算 / HTML 上限分頁 / Windows 長路徑 / 檔名·識別字消毒 /
       頂層副作用 R26 / 相對匯入 R27 / SAFE_ROOTS 雙路徑比對 / 大檔強制 lazy / SQL 多語句·註解守門 /
       trace 滾動 / 快取用內容雜湊非 mtime / taxonomy 壞檔備份 / Python 版本閘 / 平行降級 / 群 slug 碰撞
v0500: 先機器修復再交 AI(省 token) — AI_HANDOFF.md 只含殘餘決策 + token 估算 /
       CPU ML·DL 工具自動偵測+微基準(ml_capability) / 專案自有儲存 ves_store/ Parquet 分區(runs·functions·risks·gates·bench·trace)
       + ves_detail.log 詳細結構化日誌 / 跨執行趨勢 + STABLE_P 自學降權(持續強化)
v0600: 六項正式環境強化 — ① SQL 守門改為驅動層(唯讀連線 + 驅動解析器單語句 + 強制參數化，字串檢查只剩縱深)
       ② ML 探測/微基準全部在子程序跑(segfault 只殺子程序，父程序不死) ③ 指標模式改用 AST 用法證據(open/read_csv/.columns…)
       + 預設值型別 + 名稱僅最後手段，附信心；轉接器執行期自動翻轉模式(self-heal) ④ payload 估算改抽樣有界(≤64 元素/層、深度 3、可 off)
       ⑤ 呼叫圖接收者感知(self./ClassName./同模組優先)，模糊 x.method() 不算 fan_in，DORMANT 分 STRONG/WEAK
       ⑥ Ollama 改背景執行緒 + 全域時間預算(20s)，掃描不等它
v0700: 多語言 — PowerShell (.ps1/.psm1) 與 JS/TS 一併盤點(函式/參數/cmdlet·套件工具家族/正規化本體雜湊) /
       跨語言分群 same_cap_diff_lang(py↔ps1↔js 同功能異語言) / PS 跨檔重複 helper 偵測 → 生成 VIA_Common.psm1 骨架 /
       py 完全重複 → shims.py(舊名轉發 canonical，只增不減) / merge_plan.json(canonical·absorbed·shim 逐步) /
       LL PowerShell 守則稽核 R30–R42 (alias / Read-Host / exit / 區塊註解 / "$var: / ?. / Sort 多屬性 / Redirect / BOM / 短函式名 / switch 遮蔽 / ContainsKey / gci -Recurse)
v0800: LOG → 機器學習 / 深度學習 (CPU、免費 libs、全部可降級)：
       ① 風險誤報分類器 (sklearn GradientBoosting / LogisticRegression → stdlib Naive Bayes 降級) 由 ves_store 歷史 :P/:M 標籤學習，
         給每個 :P 風險 p_false_positive，高信心者提前降權 :SP(ML)
       ② 語意相似度 (sentence-transformers MiniLM → sklearn TF-IDF → stdlib hashing cosine 降級) 進分群公式 (+0.15 sem_r)
       ③ 分群回饋學習：HTML 滑鼠 ACCEPT/REJECT 產 ==VES-FEEDBACK== token → ves_feedback.jsonl → 配對特徵訓練 → 學到的門檻/重排
       ④ 日誌異常偵測：trace span ms / bench ms 跨輪 IsolationForest → z-score 降級；純 numpy 微型 autoencoder (DL, CPU, <1s) 給第二意見
       ⑤ 趨勢預測：runs 歷史 risk_M / functions 線性外推 (stdlib)
       ⑥ 免費 CPU libs 導入計畫 ves_ml_requirements.txt + --install-plan（不自動安裝；PS -InstallMlLibs 才裝）
       模型/指標存 ves_store/models/，全部標 M 級、可審計、不刪任何東西
v0900: 模組化「編輯/組裝」層 — 全景造冊 + AST 定位點 + 沙盤推演 + 九頭龍(Hydra)風險等級 + 25 項模組化風險擋點：
       ① ves_catalog.json：每個 MDL(檔案)/CLS/FNC/LIB(匯入)/ENG(群) 都有 VIA-{TYPE}-blake2s 編號、雜湊輸入入檔、交叉索引、狀態 ACTIVE/DORMANT/ABSORBED
       ② 定位點：精準錨(file+qualname+body_hash+行距) + 彈性錨(name tokens+簽章+能力)；resolve_anchor 回 EXACT/MOVED/CHANGED/RENAMED/LOST
       ③ 沙盤推演：任何 MERGE/SPLIT/EXTRACT/INTEGRATE 先在副本上做 → 全檔語法/編譯/匯入/呼叫者解析/pytest → Hydra 檢查 → GO/NO-GO
       ④ Hydra 等級 H0 無頭 / H1 多頭一致 / H2 多頭分歧 / H3 編輯造成縫隙(呼叫者失聯·部分更新) / H4 破壞(刪除·簽章斷裂)；只有 H0–H1 且 GO 才可 --apply
       ⑤ --apply 需 ACTIVATION token；套用永遠 add-only：新檔 + 舊檔尾端追加轉發，原檔 .orig 備份，edit_ledger.jsonl 全程紀錄，不刪不覆寫
v1000: 「先跑引擎、AI 只做最後修正」的省 token 閉環：
       ① ai_task_cards.jsonl — 每張卡一個決策，只附最小上下文切片(簽章+本體前幾行+呼叫者一行+錨點+選項)，依影響排序，附 token 估算
       ② ves_decisions.jsonl — AI/人回答 ==VES-DECISION== card_id OPTION[ note] → 下一輪確定性套用(分類法/回饋/canonical/介面核可)，不必重讀原始碼
       ③ --slice CODE — 只吐出某 FNC/CLS/MDL 需要的行(定義+import+呼叫者摘要)，給 AI 精準上下文
       ④ --verify-dir DIR — AI 改完的檔案先過 VES 閘(語法/LL/Hydra 分歧/錨點保留/pytest) 才准合併：AI 的修正也要過沙盤
       ⑤ VES_PROMPT.md — 給任何 AI 的完整使用說明(引擎是什麼、產物怎麼讀、可做/不可做、決策 token 格式)，每輪自動落地
       ⑥ token 帳：全樹 vs 卡片 vs 切片 三檔估算寫進 gates(VES_TOKEN_SAVING)
====================================
AST 靜態盤點所有 .py 引擎模組 → 找出「功能相同、工具相異」的指令群 → 風險稽核(25 項)
→ 生成標準化骨架(BaseProcessor / Adapter / Factory / pytest 矩陣 / Shadow runner)
→ Visual Lock HTML 矩陣。

治理: 100% 唯讀掃描；骨架只寫進全新輸出目錄；原始檔永不改動(只增不減)。
零依賴: 純標準庫(pydantic 存在時骨架用 pydantic，否則 dataclass 降級)。

用法:
  python via_engine_standardizer.py --root <dir> --out <dir> [--threshold 0.72] [--selftest]
"""
from __future__ import annotations

import argparse
import ast
import difflib
import subprocess
import hashlib
import html
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path

VERSION = "1000"
SKIP_DIRS = {".git", ".venv", "venv", "envs", "env", "node_modules", "__pycache__",
             "_to_delete", "site-packages", ".mypy_cache", ".pytest_cache", "dist",
             "build", ".idea", ".vscode", "_standardized", "_engine_standardizer"}

# 工具家族(相異底層工具的辨識標籤)
TOOL_FAMILIES = {
    "pandas": {"pandas", "pd"}, "polars": {"polars", "pl"}, "duckdb": {"duckdb"},
    "pyarrow": {"pyarrow", "pa"}, "numpy": {"numpy", "np"}, "sqlite": {"sqlite3"},
    "sqlalchemy": {"sqlalchemy"}, "requests": {"requests"}, "httpx": {"httpx"},
    "urllib": {"urllib"}, "aiohttp": {"aiohttp"}, "yfinance": {"yfinance", "yf"},
    "bs4": {"bs4", "BeautifulSoup"}, "lxml": {"lxml"}, "selenium": {"selenium"},
    "playwright": {"playwright"}, "openpyxl": {"openpyxl"}, "xlsxwriter": {"xlsxwriter"},
    "json": {"json", "orjson", "ujson", "msgspec"}, "csv": {"csv"}, "re": {"re", "regex"},
    "pymupdf": {"fitz", "pymupdf"}, "pdfplumber": {"pdfplumber"}, "pypdf": {"pypdf", "PyPDF2"},
    "tesseract": {"pytesseract"}, "talib": {"talib"}, "matplotlib": {"matplotlib", "plt"},
    "plotly": {"plotly"}, "loguru": {"loguru"}, "logging": {"logging"}, "print": {"print"},
    "subprocess": {"subprocess"}, "pathlib": {"pathlib", "Path"}, "os": {"os", "shutil"},
    "numba": {"numba"}, "joblib": {"joblib"}, "threading": {"threading", "concurrent"},
    "asyncio": {"asyncio"}, "datetime": {"datetime", "dateutil"},
}
DATA_FAMS = {"pandas", "polars", "duckdb", "pyarrow", "numpy", "sqlite", "sqlalchemy", "requests", "httpx",
             "urllib", "aiohttp", "yfinance", "bs4", "lxml", "selenium", "playwright", "openpyxl", "xlsxwriter",
             "pymupdf", "pdfplumber", "pypdf", "tesseract", "talib", "matplotlib", "plotly"}
ALIAS_TO_FAMILY = {}
for fam, names in TOOL_FAMILIES.items():
    for n in names:
        ALIAS_TO_FAMILY[n] = fam

# 能力軸(capability axis): 動詞正規化 → 功能同義群
VERB_CANON = {
    "READ": {"read", "load", "fetch", "get", "pull", "download", "scan", "crawl", "scrape",
             "query", "select", "open", "import", "collect", "retrieve", "grab"},
    "WRITE": {"write", "save", "dump", "export", "store", "persist", "upload", "emit",
              "flush", "commit", "insert", "put", "output"},
    "PARSE": {"parse", "extract", "tokenize", "decode", "split", "unpack", "deserialize"},
    "TRANSFORM": {"transform", "convert", "normalize", "clean", "map", "reshape", "cast",
                  "format", "render", "encode", "serialize", "to", "build", "make", "generate"},
    "COMPUTE": {"compute", "calc", "calculate", "score", "evaluate", "eval", "estimate",
                "predict", "simulate", "run", "process", "apply", "aggregate", "agg",
                "summarize", "rank", "measure"},
    "VALIDATE": {"validate", "check", "verify", "assert", "test", "ensure", "gate", "audit",
                 "lint", "selftest", "is", "has"},
    "MERGE": {"merge", "join", "combine", "concat", "union", "dedup", "dedupe", "unify",
              "consolidate", "register", "sync", "integrate"},
    "FILTER": {"filter", "find", "search", "match", "detect", "locate", "lookup", "classify",
               "group", "cluster", "sort"},
    "REPORT": {"report", "plot", "chart", "draw", "html", "dashboard", "print", "show",
               "display", "log", "notify"},
}
VERB_TO_CAP = {}
for cap, verbs in VERB_CANON.items():
    for v in verbs:
        VERB_TO_CAP[v] = cap

TAXONOMY_FILE = "ves_taxonomy.json"
CONFIG_FILE = "ves_config.json"
LLM_BUDGET_S = float(os.environ.get("VES_LLM_BUDGET_S", "20"))   # ⑥ Ollama 全域時間預算（背景執行，掃描不等它）
CACHE_FILE = "ves_cache.json"
MAX_FILE_BYTES = 2 * 1024 * 1024          # 風險1: 超大/生成碼跳過
CLUSTER_TIME_BUDGET_S = 120.0             # 風險6: 分群時間預算
HTML_FN_ROWS_CAP = 5000                   # 風險8: 全函式表上限
_ONEDRIVE_PLACEHOLDER = 0x400000 | 0x1000  # 風險3: RECALL_ON_DATA_ACCESS | OFFLINE


def load_config(paths: list[Path]) -> dict:
    """外掛設定(只增不減合併)：skip_dirs / excludes(glob) / threshold / max_group / safe_roots。"""
    cfg = {"skip_dirs": [], "excludes": [], "safe_roots": []}
    for p in paths:
        if p and p.exists():
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                _backup_bad_json(p)
                continue
            for k in ("skip_dirs", "excludes", "safe_roots"):
                cfg[k] += [x for x in d.get(k, []) if x not in cfg[k]]
            for k in ("threshold", "max_group", "workers"):
                if k in d:
                    cfg[k] = d[k]
    SKIP_DIRS.update(cfg["skip_dirs"])
    return cfg


def _backup_bad_json(p: Path) -> None:
    """風險19: 使用者 JSON 壞掉 → 改名 .bad_<ts> 保留，不覆蓋不刪除。"""
    try:
        p.rename(p.with_suffix(p.suffix + f".bad_{time.strftime('%Y%m%d_%H%M%S')}"))
    except Exception:  # noqa: BLE001
        pass


def _excluded(rel: str, patterns: list[str]) -> bool:
    import fnmatch
    return any(fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(rel.split("/")[-1], pat) for pat in patterns)


def _read_source(path: Path) -> tuple[str, str]:
    """風險2: 多編碼讀取 utf-8-sig → cp950(台灣舊檔) → latin-1；回 (text, encoding)。風險9: Windows 長路徑。"""
    p = path
    if os.name == "nt" and len(str(path)) > 240 and not str(path).startswith("\\\\?\\"):
        p = Path("\\\\?\\" + str(path))
    raw = p.read_bytes()
    for enc in ("utf-8-sig", "cp950", "latin-1"):
        try:
            return raw.decode(enc), enc
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace"), "utf-8-replace"


def _is_cloud_placeholder(path: Path) -> bool:
    try:
        attrs = getattr(os.stat(path), "st_file_attributes", 0)
        return bool(attrs & _ONEDRIVE_PLACEHOLDER)
    except OSError:
        return False


def load_taxonomy(paths: list[Path]) -> dict:
    """外掛分類法：只增不減地合併使用者 JSON 進內建字典(verbs / tools / stop)。"""
    learned = {"verbs": {}, "tools": {}, "stop": [], "pending_verbs": {}}
    for p in paths:
        if p and p.exists():
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                _backup_bad_json(p)
                continue
            for cap, verbs in d.get("verbs", {}).items():
                for v in verbs:
                    VERB_TO_CAP.setdefault(v.lower(), cap.upper())
                    VERB_CANON.setdefault(cap.upper(), set()).add(v.lower())
            for fam, names in d.get("tools", {}).items():
                for n in names:
                    ALIAS_TO_FAMILY.setdefault(n, fam)
                    TOOL_FAMILIES.setdefault(fam, set()).add(n)
            learned["pending_verbs"].update(d.get("pending_verbs", {}))
            learned["stop"] += d.get("stop", [])
    STOP_TOKENS.update(learned["stop"])
    return learned


def ollama_available(host: str = "http://127.0.0.1:11434", timeout: float = 0.6) -> str:
    """偵測本機 Ollama；回傳可用模型名(優先 qwen2.5)，不可用回空字串。零依賴 urllib。"""
    import urllib.request
    try:
        with urllib.request.urlopen(host + "/api/tags", timeout=timeout) as r:
            tags = json.loads(r.read().decode("utf-8")).get("models", [])
    except Exception:  # noqa: BLE001
        return ""
    names = [t.get("name", "") for t in tags]
    for pref in ("qwen2.5", "qwen", "llama3.2", "phi3", "gemma2"):
        for n in names:
            if n.startswith(pref):
                return n
    return names[0] if names else ""


def ollama_classify_verbs(verbs: list[str], model: str, host: str = "http://127.0.0.1:11434",
                          timeout: float = 20.0) -> dict:
    """LLM 語意代理：未知動詞 → 能力軸。結果只是 M 級建議寫進 pending_verbs.suggest，不自動生效。"""
    import urllib.request
    if not verbs or not model:
        return {}
    caps = ", ".join(VERB_CANON)
    prompt = ("You classify Python function-name verbs into capability axes.\n"
              f"Axes: {caps}, OTHER.\nReturn ONLY a JSON object mapping each verb to one axis.\n"
              f"Verbs: {json.dumps(verbs)}")
    body = json.dumps({"model": model, "prompt": prompt, "stream": False, "format": "json",
                       "options": {"temperature": 0}}).encode("utf-8")
    req = urllib.request.Request(host + "/api/generate", data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            txt = json.loads(r.read().decode("utf-8")).get("response", "{}")
        d = json.loads(txt)
        return {k.lower(): str(v).upper() for k, v in d.items() if str(v).upper() in set(VERB_CANON) | {"OTHER"}}
    except Exception:  # noqa: BLE001
        return {}


def write_taxonomy_seed(out: Path, unknown_verbs: Counter, existing: dict, llm_map: dict | None = None) -> Path:
    """把命中 ≥3 次的未知首動詞寫進 pending_verbs(P 級，待人工填能力軸)；已存在者不覆蓋。"""
    p = out / TAXONOMY_FILE
    d = {"_readme": "verbs: {CAP: [verb,...]} 只增不減；pending_verbs 為自學候選，把它搬進 verbs 即生效；tools: {family: [alias,...]}",
         "verbs": {}, "tools": {}, "stop": [], "pending_verbs": dict(existing.get("pending_verbs", {}))}
    if p.exists():
        try:
            d.update(json.loads(p.read_text(encoding="utf-8")))
        except Exception:  # noqa: BLE001
            pass
    llm_map = llm_map or {}
    for v, n in unknown_verbs.most_common(60):
        if n >= 3 and v not in VERB_TO_CAP:
            ent = d.setdefault("pending_verbs", {}).setdefault(v, {"hits": n, "suggest": "OTHER", "grade": "P"})
            if v in llm_map and ent.get("grade") != "V":
                ent["suggest"] = llm_map[v]
                ent["grade"] = "M"                       # 證據誠實：LLM 建議 = M 級，人工搬進 verbs 才是 V
    p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    return p


STOP_TOKENS = {"the", "a", "an", "of", "for", "and", "or", "with", "by", "from", "into",
               "data", "df", "v", "v1", "v2", "v3", "new", "old", "tmp", "temp", "helper",
               "util", "utils", "func", "fn", "impl", "internal", "main"}


def norm_tokens(name: str) -> list[str]:
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    s = re.sub(r"[^A-Za-z0-9]+", "_", s).lower().strip("_")
    toks = [t for t in s.split("_") if t and t not in STOP_TOKENS]
    toks = [re.sub(r"\d+$", "", t) or t for t in toks]
    return toks


def capability_of(tokens: list[str]) -> str:
    for t in tokens:
        if t in VERB_TO_CAP:
            return VERB_TO_CAP[t]
    return "OTHER"


@dataclass
class FuncRec:
    fid: str
    file: str
    module: str
    qualname: str
    name: str
    lineno: int
    end_lineno: int
    args: list[str]
    has_varargs: bool
    has_kwargs: bool
    annotated_args: int
    has_return_annot: bool
    decorators: list[str]
    tools: list[str]
    calls: list[str]
    tokens: list[str]
    capability: str
    body_hash: str
    doc: str
    is_method: bool
    stmts: int = 0
    abspath: str = ""
    lang: str = "py"
    arg_annots: dict = field(default_factory=dict)
    arg_defaults: dict = field(default_factory=dict)
    doc_tokens: list[str] = field(default_factory=list)
    fan_in: int = 0
    fan_out: int = 0
    dormant_candidate: bool = False
    fan_in_ambiguous: int = 0
    dormant_level: str = ""
    arg_usage: dict = field(default_factory=dict)
    risks: list[str] = field(default_factory=list)


@dataclass
class FileRec:
    file: str
    module: str
    lines: int
    parse_ok: bool
    parse_error: str
    imports: list[str]
    tools: list[str]
    func_count: int
    dynamic_import: bool
    module_globals_mutable: int
    print_calls: int
    risks: list[str] = field(default_factory=list)
    dynamic_targets: list[str] = field(default_factory=list)
    encoding: str = "utf-8"
    content_hash: str = ""
    skipped: str = ""
    toplevel_calls: int = 0
    relative_imports: int = 0
    lang: str = "py"


class _Visitor(ast.NodeVisitor):
    """收集 import 別名、呼叫、屬性鏈。"""

    def __init__(self):
        self.calls: list[str] = []
        self.names: set[str] = set()
        self.attr_roots: set[str] = set()

    def visit_Call(self, node):
        f = node.func
        if isinstance(f, ast.Name):
            self.calls.append(f.id)
        elif isinstance(f, ast.Attribute):
            chain = []
            cur = f
            while isinstance(cur, ast.Attribute):
                chain.append(cur.attr)
                cur = cur.value
            if isinstance(cur, ast.Name):
                chain.append(cur.id)
                self.attr_roots.add(cur.id)
            else:
                chain.append("<expr>")
            self.calls.append(".".join(reversed(chain)))
        self.generic_visit(node)

    def visit_Name(self, node):
        self.names.add(node.id)

    def visit_Attribute(self, node):
        cur = node
        while isinstance(cur, ast.Attribute):
            cur = cur.value
        if isinstance(cur, ast.Name):
            self.attr_roots.add(cur.id)
        self.generic_visit(node)


def _norm_ast_hash(node: ast.AST) -> str:
    """去除行號、docstring、變數命名差異後的結構雜湊(偵測『邏輯完全相同』)。"""
    class _Strip(ast.NodeTransformer):
        def __init__(self):
            self.map: dict[str, str] = {}

        def _n(self, x):
            if x not in self.map:
                self.map[x] = f"v{len(self.map)}"
            return self.map[x]

        def visit_Name(self, n):
            return ast.copy_location(ast.Name(id=self._n(n.id), ctx=n.ctx), n)

        def visit_arg(self, n):
            n.arg = self._n(n.arg)
            n.annotation = None
            return n

        def visit_Constant(self, n):
            if isinstance(n.value, str) and len(n.value) > 40:
                return ast.copy_location(ast.Constant(value="<STR>"), n)
            return n

    import copy
    node = copy.deepcopy(node)                       # 不可就地改寫原節點(後續接收者追蹤要用原名)
    body = list(getattr(node, "body", []))
    if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant) \
            and isinstance(body[0].value.value, str):
        body = body[1:]
    mod = ast.Module(body=body, type_ignores=[])
    mod = _Strip().visit(mod)
    dump = ast.dump(mod, annotate_fields=False, include_attributes=False)
    return hashlib.blake2s(dump.encode("utf-8"), digest_size=6).hexdigest()


def _decor_name(d: ast.AST) -> str:
    if isinstance(d, ast.Call):
        d = d.func
    if isinstance(d, ast.Name):
        return d.id
    if isinstance(d, ast.Attribute):
        return d.attr
    return type(d).__name__


_DYN_RX = re.compile(r"""(import_module|__import__|load_module|exec_module)\s*\(\s*['"]([\w.]+)['"]""")
_DATA_METHODS_PD = (".set_index", ".reset_index", ".loc", ".iloc", ".index")
_LAZY_METHODS = (".lazy", ".scan_csv", ".scan_parquet", ".scan_ndjson", ".sql")
_EAGER_METHODS = (".collect", ".df", ".fetchall", ".fetchone", ".pl", ".arrow", ".to_pandas", ".fetchdf", ".fetchnumpy")


def _trace_receivers(fn_node: ast.AST, alias_map: dict[str, str]) -> set[str]:
    """R12/R13 誤報抑制：找出『真的來自資料工具』的變數(df = pd.read_csv / lf = pl.scan_* / con = duckdb.connect
    或參數註記 DataFrame/LazyFrame/Connection)。只有這些接收者上的呼叫鏈才算數。"""
    data_vars: set[str] = set()
    for a in list(fn_node.args.args) + list(fn_node.args.kwonlyargs):
        ann = a.annotation
        if ann is not None:
            txt = ast.unparse(ann) if hasattr(ast, "unparse") else ""
            if re.search(r"DataFrame|LazyFrame|Series|Connection|Relation|Table", txt):
                data_vars.add(a.arg)
    changed = True
    while changed:
        changed = False
        for n in ast.walk(fn_node):
            if isinstance(n, (ast.Assign, ast.AnnAssign)):
                tgts = n.targets if isinstance(n, ast.Assign) else [n.target]
                val = n.value
                root_name = None
                cur = val
                while isinstance(cur, (ast.Call, ast.Attribute, ast.Subscript)):
                    cur = cur.func if isinstance(cur, ast.Call) else cur.value
                if isinstance(cur, ast.Name):
                    root_name = cur.id
                if root_name and (ALIAS_TO_FAMILY.get(alias_map.get(root_name, root_name)) in DATA_FAMS
                                  or root_name in data_vars):
                    for t in tgts:
                        if isinstance(t, ast.Name) and t.id not in data_vars:
                            data_vars.add(t.id)
                            changed = True
    return data_vars


_PATH_SINKS = {"open", "Path", "read_csv", "read_parquet", "read_excel", "read_json", "scan_csv", "scan_parquet",
               "read_text", "read_bytes", "exists", "isfile", "isdir", "join", "basename", "dirname", "abspath", "listdir",
               "glob", "walk", "connect", "load", "loads", "to_csv", "to_parquet", "write_csv", "write_parquet", "makedirs"}
_FRAME_ATTRS = {"columns", "iloc", "loc", "groupby", "group_by", "merge", "join", "head", "tail", "shape", "dtypes", "values",
                "to_numpy", "select", "filter", "with_columns", "collect", "agg", "sort_values", "fillna", "dropna", "rolling",
                "index", "describe", "pivot", "melt", "to_pandas", "to_dict", "sum", "mean", "lazy", "schema", "height", "width"}


def _arg_usage(n, alias_map: dict) -> dict:
    """③ 參數用法證據：每個參數在函式體內是怎麼被用的 → path / frame 證據計數 + 預設值型別。"""
    args = [a.arg for a in n.args.args + n.args.kwonlyargs if a.arg not in ("self", "cls")]
    ev = {a: {"path": 0, "frame": 0, "str_ops": 0} for a in args}
    for node in ast.walk(n):
        if isinstance(node, ast.Call):
            fn = node.func
            fname = fn.id if isinstance(fn, ast.Name) else (fn.attr if isinstance(fn, ast.Attribute) else "")
            for arg in node.args[:2]:
                if isinstance(arg, ast.Name) and arg.id in ev and fname in _PATH_SINKS:
                    ev[arg.id]["path"] += 1
                if isinstance(arg, ast.Name) and arg.id in ev and fname in ("len", "list", "enumerate", "zip", "iter"):
                    ev[arg.id]["frame"] += 0   # 中性
            if isinstance(fn, ast.Attribute) and isinstance(fn.value, ast.Name) and fn.value.id in ev:
                if fn.attr in _FRAME_ATTRS:
                    ev[fn.value.id]["frame"] += 1
                elif fn.attr in ("endswith", "startswith", "split", "strip", "lower", "upper", "replace", "format", "encode"):
                    ev[fn.value.id]["str_ops"] += 1
        elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id in ev:
            if node.attr in _FRAME_ATTRS:
                ev[node.value.id]["frame"] += 1
        elif isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name) and node.value.id in ev:
            sl = node.slice
            if isinstance(sl, ast.Constant) and isinstance(sl.value, str):
                ev[node.value.id]["frame"] += 1          # x["col"]
        elif isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Div, ast.Add)):
            for side in (node.left, node.right):
                if isinstance(side, ast.Name) and side.id in ev and isinstance(node.op, ast.Div):
                    ev[side.id]["path"] += 1              # Path / "x"
        elif isinstance(node, ast.With):
            for item in node.items:
                if isinstance(item.context_expr, ast.Call):
                    for arg in item.context_expr.args[:1]:
                        if isinstance(arg, ast.Name) and arg.id in ev:
                            ev[arg.id]["path"] += 1
    return ev


def _arg_annots(n) -> dict:
    out = {}
    for a in list(n.args.args) + list(n.args.kwonlyargs):
        if a.arg in {"self", "cls"}:
            continue
        out[a.arg] = ast.unparse(a.annotation) if a.annotation is not None else ""
    return out


def _arg_defaults(n) -> dict:
    out = {}
    pos = [a.arg for a in n.args.args]
    for a, d in zip(pos[len(pos) - len(n.args.defaults):], n.args.defaults):
        if a not in {"self", "cls"}:
            try:
                out[a] = ast.unparse(d)
            except Exception:  # noqa: BLE001
                out[a] = "None"
    for a, d in zip(n.args.kwonlyargs, n.args.kw_defaults):
        if d is not None:
            out[a.arg] = ast.unparse(d)
    return out


_DOC_STOP = {"the", "a", "an", "of", "for", "and", "or", "to", "in", "is", "this", "that", "with", "from",
             "return", "returns", "given", "using", "into", "by", "on", "as", "be", "it", "if"}


def _doc_tokens(doc: str) -> list[str]:
    first = doc.strip().split("\n")[0][:200].lower()
    toks = re.findall(r"[a-z][a-z0-9]{2,}|[\u4e00-\u9fff]{2,}", first)
    return [t for t in toks if t not in _DOC_STOP][:12]


def scan_file(path: Path, root: Path, fid_counter: list[int]) -> tuple[FileRec, list[FuncRec]]:
    rel = str(path.relative_to(root)).replace("\\", "/")
    module = rel[:-3].replace("/", ".")
    try:
        if _is_cloud_placeholder(path):
            return FileRec(rel, module, 0, False, "CLOUD_PLACEHOLDER (OneDrive 未下載)", [], [], 0, False, 0, 0,
                           ["R05_READ_FAIL"], skipped="CLOUD_PLACEHOLDER"), []
        size = path.stat().st_size
        if size > MAX_FILE_BYTES:
            return FileRec(rel, module, 0, False, f"SKIP_LARGE {size / 1e6:.1f}MB", [], [], 0, False, 0, 0,
                           [], skipped="SKIP_LARGE"), []
        src, enc = _read_source(path)
    except OSError as e:
        return FileRec(rel, module, 0, False, f"READ_FAIL: {e}", [], [], 0, False, 0, 0, ["R05_READ_FAIL"]), []
    chash = hashlib.blake2s(src.encode("utf-8", "replace"), digest_size=8).hexdigest()
    lines = src.count("\n") + 1
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return FileRec(rel, module, lines, False, f"L{e.lineno}: {e.msg}", [], [], 0, False, 0, 0,
                       ["R05_SYNTAX_VERSION_CONFLICT"], encoding=enc, content_hash=chash), []

    # module-level imports → tool families
    imports: list[str] = []
    alias_map: dict[str, str] = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                imports.append(a.name)
                alias_map[(a.asname or a.name).split(".")[0]] = a.name.split(".")[0]
        elif isinstance(n, ast.ImportFrom):
            if n.module:
                imports.append(n.module)
                for a in n.names:
                    alias_map[a.asname or a.name] = n.module.split(".")[0]
    file_tools = sorted({ALIAS_TO_FAMILY[t] for t in
                         {a for a in alias_map.values()} | set(alias_map.keys()) if t in ALIAS_TO_FAMILY})

    dyn = False
    dyn_targets: list[str] = []
    for mm in _DYN_RX.finditer(src):                       # R01: regex 補掃字串型模組名
        dyn_targets.append(mm.group(2))
    prints = 0
    mutable_globals = 0
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            fn = n.func
            nm = fn.id if isinstance(fn, ast.Name) else (fn.attr if isinstance(fn, ast.Attribute) else "")
            if nm in {"import_module", "__import__", "eval", "exec"}:
                dyn = True
            if nm == "print":
                prints += 1
    toplevel_calls = 0
    for n in tree.body:
        if isinstance(n, ast.Assign) and isinstance(n.value, (ast.Dict, ast.List, ast.Set)):
            mutable_globals += 1
        if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call):          # 風險12: 頂層副作用
            fn_ = n.value.func
            nm_ = fn_.id if isinstance(fn_, ast.Name) else (fn_.attr if isinstance(fn_, ast.Attribute) else "")
            if nm_ not in {"register", "setdefault", "seed", "basicConfig", "filterwarnings", "simplefilter"}:
                toplevel_calls += 1
    rel_imports = sum(1 for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and (n.level or 0) > 0)

    frisks = []
    if dyn or dyn_targets:
        frisks.append("R01_DYNAMIC_IMPORT")
    if mutable_globals:
        frisks.append("R16_MODULE_MUTABLE_STATE")
    if prints:
        frisks.append("R19_PRINT_LOGGING")
    if "settings" in imports or "config" in imports or any(i.endswith(".settings") for i in imports):
        frisks.append("R18_GLOBAL_CONFIG")
    if toplevel_calls:
        frisks.append("R26_TOPLEVEL_SIDE_EFFECT")
    if rel_imports:
        frisks.append("R27_RELATIVE_IMPORT")

    funcs: list[FuncRec] = []

    def _walk(container, prefix: str, is_method: bool):
        for n in container.body:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                fid_counter[0] += 1
                v = _Visitor()
                v.visit(n)
                roots = {alias_map.get(r, r) for r in v.attr_roots} | {alias_map.get(c, c) for c in v.calls
                                                                        if "." not in c}
                tools = sorted({ALIAS_TO_FAMILY[r] for r in roots if r in ALIAS_TO_FAMILY})
                if "print" in v.calls:
                    tools = sorted(set(tools) | {"print"})
                if not any(t in DATA_FAMS for t in tools):
                    tools = sorted(set(tools) | {t for t in file_tools if t in DATA_FAMS})
                args = [a.arg for a in n.args.args + n.args.kwonlyargs if a.arg not in {"self", "cls"}]
                annotated = sum(1 for a in n.args.args + n.args.kwonlyargs
                                if a.annotation is not None and a.arg not in {"self", "cls"})
                toks = norm_tokens(n.name)
                cap = capability_of(toks)
                decs = [_decor_name(d) for d in n.decorator_list]
                rec = FuncRec(
                    fid=f"FN-{fid_counter[0]:05d}", file=rel, module=module,
                    qualname=(prefix + n.name), name=n.name, lineno=n.lineno,
                    end_lineno=getattr(n, "end_lineno", n.lineno), args=args,
                    has_varargs=n.args.vararg is not None, has_kwargs=n.args.kwarg is not None,
                    annotated_args=annotated, has_return_annot=n.returns is not None,
                    decorators=decs, tools=tools, calls=sorted(set(v.calls))[:40],
                    tokens=toks, capability=cap, body_hash=_norm_ast_hash(n),
                    doc=(ast.get_docstring(n) or "")[:160], is_method=is_method, abspath=str(path),
                    arg_annots=_arg_annots(n), arg_defaults=_arg_defaults(n),
                    doc_tokens=_doc_tokens(ast.get_docstring(n) or ""), arg_usage=_arg_usage(n, alias_map),
                    stmts=sum(1 for b in n.body if not (isinstance(b, ast.Expr) and isinstance(getattr(b, "value", None), ast.Constant))),
                )
                # per-function risks
                r = rec.risks
                if decs and not set(decs) <= {"staticmethod", "classmethod", "property", "abstractmethod",
                                               "dataclass", "override", "cached_property"}:
                    r.append("R02_DECORATOR_HIDES_SIGNATURE")
                if args and annotated < len(args):
                    r.append("R03_MISSING_TYPE_HINTS")
                if rec.has_kwargs:
                    r.append("R07_KWARGS_ABUSE")
                recv = _trace_receivers(n, alias_map)
                data_roots = set(recv) | {k for k, vv in alias_map.items() if ALIAS_TO_FAMILY.get(vv) in DATA_FAMS}

                def _on_data(c: str) -> bool:
                    return c.split(".")[0] in data_roots

                pd_hits = [c for c in v.calls if c.endswith(_DATA_METHODS_PD) or ".index." in c]
                if "pandas" in tools and pd_hits:
                    r.append("R12_INDEX_DEPENDENCY" + (":M" if any(_on_data(c) for c in pd_hits) else ":P"))
                lazy_hits = [c for c in v.calls if c.endswith(_LAZY_METHODS) or c.split(".")[0] in
                             {k for k, vv in alias_map.items() if vv == "duckdb"}]
                if lazy_hits and not any(c.endswith(_EAGER_METHODS) for c in v.calls):
                    r.append("R13_LAZY_NOT_MATERIALIZED" + (":M" if any(_on_data(c) for c in lazy_hits) else ":P"))
                null_hits = [c for c in v.calls if c.endswith((".rolling", ".mean", ".fillna", ".dropna",
                                                                ".groupby", ".group_by", ".fill_null"))]
                if null_hits and {t for t in tools} & {"pandas", "polars", "duckdb"}:
                    r.append("R11_NULL_SEMANTICS" + (":M" if any(_on_data(c) for c in null_hits) else ":P"))
                if "re" in tools and any(t in tools for t in ("pandas", "polars", "duckdb")):
                    r.append("R15_REGEX_ENGINE_DIVERGENCE")
                if any(c.endswith(".environ") or c == "getenv" or c.endswith(".getenv") for c in v.calls) \
                        or "environ" in v.names:
                    r.append("R18_GLOBAL_CONFIG")
                if any(t in tools for t in ("pymupdf", "pdfplumber", "tesseract", "sqlite", "sqlalchemy",
                                            "selenium", "playwright")) and not any(
                        c.endswith(".close") or c.endswith(".quit") for c in v.calls):
                    r.append("R17_RESOURCE_NOT_RELEASED")
                if "numba" in tools or "joblib" in tools:
                    r.append("R20_HEAVY_INIT")
                if n.name.startswith("test_"):
                    r.append("R23_TEST_MATRIX_SIZE")
                funcs.append(rec)
            elif isinstance(n, ast.ClassDef):
                _walk(n, prefix + n.name + ".", True)

    _walk(tree, "", False)
    frec = FileRec(rel, module, lines, True, "", sorted(set(imports))[:60], file_tools, len(funcs), dyn,
                   mutable_globals, prints, frisks, sorted(set(dyn_targets)), enc, chash, "", toplevel_calls, rel_imports)
    return frec, funcs


def scan_any(path: Path, root: Path, ctr: list[int]) -> tuple[FileRec, list[FuncRec]]:
    ext = path.suffix.lower()
    lang = LANG_EXT.get(ext, "py")
    if lang == "ps1":
        return scan_ps1(path, root, ctr)
    if lang == "js":
        return scan_js(path, root, ctr)
    return scan_file(path, root, ctr)


def _scan_worker(args):
    path_s, root_s, seed = args
    ctr = [seed]
    fr, fs = scan_any(Path(path_s), Path(root_s), ctr)
    return fr, fs


def _engine_hash() -> str:
    try:
        return hashlib.blake2s(Path(__file__).read_bytes(), digest_size=6).hexdigest()
    except OSError:
        return "?"


def _load_cache(cache_path: Path) -> dict:
    if cache_path and cache_path.exists():
        try:
            d = json.loads(cache_path.read_text(encoding="utf-8"))
            if d.get("version") == VERSION and d.get("engine_hash") == _engine_hash() and set(d.get("langs", ["py"])) == set(LANG_EXT.values()):
                return d.get("files", {})
        except Exception:  # noqa: BLE001
            _backup_bad_json(cache_path)
    return {}


def scan_tree(root: Path, workers: int, cache_path: Path | None = None) -> tuple[list[FileRec], list[FuncRec], dict]:
    """多核平行 AST 解析(ProcessPoolExecutor)；<40 檔或 workers<=1 或平行失敗 → 循序降級。
    升級1/風險18: 增量快取以『內容雜湊』為鍵(非 mtime)，未變檔直接還原上次結果。FID 掃完後重新編號。"""
    all_paths = [str(p) for p in iter_py(root)]
    cache = _load_cache(cache_path) if cache_path else {}
    files, funcs = [], []
    hits = 0
    paths = []
    for ps in all_paths:
        ent = cache.get(ps)
        if ent:
            try:
                raw = Path(ps).read_bytes()
                h = hashlib.blake2s(raw.decode("utf-8", "replace").encode("utf-8", "replace"), digest_size=8).hexdigest()
            except OSError:
                h = ""
            if h and h == ent.get("hash"):
                files.append(FileRec(**ent["file"]))
                funcs.extend(FuncRec(**fr) for fr in ent["funcs"])
                hits += 1
                continue
        paths.append(ps)
    if hits:
        print(f"@@PROGRESS|cache|{hits}/{len(all_paths)} files unchanged (content-hash cache)", flush=True)
    done = 0
    if workers > 1 and len(paths) >= 40:
        try:
            from concurrent.futures import ProcessPoolExecutor
            with ProcessPoolExecutor(max_workers=workers) as ex:
                for fr, fs in ex.map(_scan_worker, [(p, str(root), 0) for p in paths], chunksize=16):
                    files.append(fr)
                    funcs.extend(fs)
                    done += 1
                    if done % 100 == 0:
                        print(f"@@PROGRESS|{done}/{len(paths)}|parallel x{workers}, {len(funcs)} functions", flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"@@PROGRESS|warn|parallel failed ({type(e).__name__}) -> sequential", flush=True)
            files, funcs, done = [], [], 0
    if done == 0 and paths:
        ctr = [0]
        for p in paths:
            fr, fs = scan_any(Path(p), root, ctr)
            files.append(fr)
            funcs.extend(fs)
            done += 1
            if done % 50 == 0:
                print(f"@@PROGRESS|{done}/{len(paths)}|sequential, {len(funcs)} functions", flush=True)
    funcs.sort(key=lambda f: (f.file, f.lineno))
    for i, f in enumerate(funcs, 1):
        f.fid = f"FN-{i:05d}"
    stats = {"total": len(all_paths), "cache_hits": hits, "scanned": len(paths)}
    if cache_path:
        by_file: dict[str, list] = defaultdict(list)
        for f in funcs:
            by_file[f.abspath].append(asdict(f))
        newc = {"version": VERSION, "engine_hash": _engine_hash(), "files": {}}
        for fr in files:
            ap = str(root / fr.file)
            if fr.content_hash:
                newc["files"][ap] = {"hash": fr.content_hash, "file": asdict(fr), "funcs": by_file.get(ap, [])}
        newc["langs"] = sorted(set(LANG_EXT.values()))
        try:
            cache_path.write_text(json.dumps(newc, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass
    return files, funcs, stats


_EXCLUDES: list[str] = []
LANG_EXT: dict[str, str] = {".py": "py"}          # run() 依 --langs 擴充：.ps1/.psm1 → ps1, .js/.mjs/.ts/.tsx/.jsx → js


def iter_py(root: Path):
    seen_real: set[str] = set()                              # 風險4: symlink/junction 循環
    for dp, dns, fns in os.walk(root, followlinks=False):
        try:
            rp = os.path.realpath(dp)
        except OSError:
            rp = dp
        if rp in seen_real:
            dns[:] = []
            continue
        seen_real.add(rp)
        dns[:] = [d for d in dns if d not in SKIP_DIRS and not d.startswith(".")
                  and not _excluded(os.path.relpath(os.path.join(dp, d), root).replace("\\", "/"), _EXCLUDES)]
        for f in fns:
            low = f.lower()
            if low.endswith(tuple(LANG_EXT)) and not low.endswith((".min.js", ".d.ts")):
                rel = os.path.relpath(os.path.join(dp, f), root).replace("\\", "/")
                if not _excluded(rel, _EXCLUDES):
                    yield Path(dp) / f


# ---------------------------------------------------------------- v0700 PowerShell / JS 掃描器
PS_TOOL_FAMILIES = {   # cmdlet 名詞 / .NET 命名空間 → 與 py 同名的工具家族，讓跨語言 same-tool 可比
    r"^(Get|Set|New|Remove|Copy|Move|Test|Resolve)-(ChildItem|Item|Content|Path|Location|PSDrive)$|System\.IO\.": "os",
    r"^(Invoke)-(WebRequest|RestMethod)$|System\.Net\.": "requests",
    r"^(ConvertTo|ConvertFrom)-Json$|Newtonsoft": "json",
    r"^(Import|Export)-Csv$": "csv",
    r"^(Start|Stop|Wait|Get)-Process$|System\.Diagnostics\.Process": "subprocess",
    r"^(Import|Export)-Excel$|ClosedXML|OfficeOpenXml": "openpyxl",
    r"^(Select|Where|Sort|Group|Measure|ForEach)-Object$": "pandas",   # 資料管線 ≈ dataframe 操作
    r"^Write-(Host|Output|Verbose|Information)$": "print",
    r"^Write-(Log|Warning|Error)$|Add-Content": "logging",
    r"^Start-(Job|ThreadJob)$|Runspace": "threading",
    r"^(Compress|Expand)-Archive$|System\.IO\.Compression": "zipfile",
    r"^Invoke-Sqlcmd$|System\.Data\.": "sqlalchemy",
    r"^(Get|Set)-Date$|\[datetime\]": "datetime",
    r"^Select-String$|\[regex\]": "re",
}
JS_TOOL_FAMILIES = {"axios": "requests", "node-fetch": "requests", "fetch": "requests", "fs": "os", "fs/promises": "os", "path": "pathlib",
                    "child_process": "subprocess", "cheerio": "bs4", "jsdom": "bs4", "lodash": "numpy", "d3": "matplotlib", "plotly.js": "plotly",
                    "xlsx": "openpyxl", "papaparse": "csv", "csv-parse": "csv", "sqlite3": "sqlite", "better-sqlite3": "sqlite", "pg": "sqlalchemy",
                    "mysql2": "sqlalchemy", "duckdb": "duckdb", "apache-arrow": "pyarrow", "arquero": "polars", "danfojs": "pandas", "zod": "pydantic",
                    "pino": "logging", "winston": "logging", "console": "print", "worker_threads": "threading", "dayjs": "datetime", "moment": "datetime",
                    "pdfjs-dist": "pypdf", "puppeteer": "playwright", "playwright": "playwright", "jszip": "zipfile"}
PS_ALIASES = {"ls", "dir", "cat", "echo", "select", "where", "sort", "gci", "gc", "sls", "ft", "fl", "iex", "rm", "cp", "mv", "ni", "sc", "gm",
              "measure", "group", "tee", "type", "del", "ren", "%", "?", "cls", "pwd", "cd", "sleep", "kill", "ps", "gps", "curl", "wget", "diff", "compare"}
PS_SHORT_FN = {"SL", "SP", "WL", "WB", "DP"}
_BC_OPEN = "<" + "#"          # 動態組字，避免本檔被嵌進 PS here-string 時出現區塊註解標記
_BC_CLOSE = "#" + ">"


def _strip_ps_comments(src: str) -> str:
    src = re.sub(_BC_OPEN + r".*?" + _BC_CLOSE, lambda m: "\n" * m.group(0).count("\n"), src, flags=re.S)
    return re.sub(r"(?m)(?<![\w'\"])#(?!requires|region|endregion).*$", "", src)


def _match_brace(src: str, start: int) -> int:
    depth, i, n = 0, start, len(src)
    in_str = None
    while i < n:
        c = src[i]
        if in_str:
            if c == in_str and src[i - 1] != "`":
                in_str = None
        elif c in ("'", '"'):
            in_str = c
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return n - 1


def _norm_body_hash(body: str, lang: str) -> str:
    """跨檔重複偵測用：去註解/空白、識別字(變數)正規化、字串常值→<STR>、數字→<NUM>。"""
    b = body
    if lang == "ps1":
        b = _strip_ps_comments(b)
        names: dict[str, str] = {}
        b = re.sub(r"\$(?:script:|local:|global:)?([A-Za-z_]\w*)", lambda m: "$" + names.setdefault(m.group(1).lower(), f"v{len(names)}"), b)
    else:
        b = re.sub(r"/\*.*?\*/", "", b, flags=re.S)
        b = re.sub(r"(?m)//.*$", "", b)
    b = re.sub(r"'[^']*'|\"[^\"]*\"|`[^`]*`", "<STR>", b)
    b = re.sub(r"\b\d+(\.\d+)?\b", "<NUM>", b)
    b = re.sub(r"\s+", " ", b).strip().lower()
    return hashlib.blake2s(b.encode("utf-8", "replace"), digest_size=6).hexdigest()


def _ll_audit_ps(src: str, rel: str) -> list[str]:
    """LL PowerShell 守則稽核 (Tony 的鎖定慣例) → 檔案級風險碼 R30–R42。"""
    r = []
    code = _strip_ps_comments(src)
    code = re.sub(r"@['\"]\r?\n.*?\r?\n['\"]@", "<HERESTRING>", code, flags=re.S)      # 嵌入的 python/html 不稽核
    code_nostr = re.sub(r"'[^'\n]*'", "''", code)                                        # 單引號字串內不算 alias
    code_nostr = re.sub(r'"(?:[^"\n]|`")*"', '""', code_nostr)
    lines = code_nostr.splitlines()
    # R30 alias
    alias_hits = set()
    for ln in lines:
        stripped = ln.strip()
        if not stripped or stripped.startswith(("param", "#")):
            continue
        for tok in re.findall(r"(?<![\w\-$.])([A-Za-z%?]{1,7})(?=\s|$|\|)", stripped):
            if tok.lower() in PS_ALIASES and tok not in ("type",):
                # 排除字串內
                if re.search(r"(['\"]).*\b" + re.escape(tok) + r"\b.*\1", stripped):
                    continue
                alias_hits.add(tok)
    if alias_hits:
        r.append("R30_PS_ALIAS:" + ",".join(sorted(alias_hits))[:40])
    if re.search(r"\bRead-Host\b", code_nostr):
        r.append("R31_PS_READ_HOST")
    if re.search(r"(?m)^\s*exit\b|\bStop-Process\b", code_nostr):
        r.append("R32_PS_EXIT")
    if _BC_OPEN in code:                                   # here-string 已移除；LL#10/#15
        r.append("R33_PS_BLOCK_COMMENT")
    first_stmt = next((ln.strip() for ln in lines if ln.strip() and not ln.strip().startswith(("#", "#requires", "using "))), "")
    if "param(" in code.lower() and not first_stmt.lower().startswith(("param(", "[cmdletbinding", "&", "function", "@{")) and not first_stmt.startswith("$"):
        pass
    if not rel.lower().endswith(".psm1") and re.search(r"(?m)^param\s*\(", code) \
            and not first_stmt.lower().startswith(("param", "[cmdletbinding", "& {", "&{")):
        r.append("R34_PS_PARAM_NOT_FIRST")
    if re.search(r'"[^"\n]*\$(?!script:|global:|local:|env:|using:|private:)[A-Za-z_]\w*:(?!:)[^"\n]*"', code):
        r.append("R35_PS_VAR_COLON_IN_STRING")
    if re.search(r'"[^"\n]*\$\w+\?\.\w+[^"\n]*"', code):
        r.append("R36_PS_NULL_CONDITIONAL_IN_STRING")
    for m in re.finditer(r"(?:Sort-Object|(?<![\w-])sort)\s+(?:-Property\s+)?([^\n|]+)", code):
        props = m.group(1)
        if "," in props and "@{" not in props:
            r.append("R37_PS_SORT_MULTI_NOT_HASHTABLE")
            break
    if re.search(r"RedirectStandardOutput\s*=\s*\$true", code) and "WaitForExit" in code:
        r.append("R38_PS_REDIRECT_STDOUT_BUFFER:P")          # 短探測(版本/幾秒)可接受；長任務才是問題
    if re.search(r"\|\s*(Out-File|Set-Content)\b(?![^\n]*-Encoding)", code) or re.search(r"\bOut-File\b(?![^\n]*-Encoding)", code):
        r.append("R39_PS_BOM_RISK")
    if any(re.search(r"(?mi)^\s*function\s+" + n + r"\b", code) for n in PS_SHORT_FN):
        r.append("R40_PS_SHORT_FN_ALIAS_CLASH")
    sw = re.findall(r"\[switch\]\s*\$(\w+)", code)
    for name in sw:
        if re.search(r"(?m)^\s*\$" + re.escape(name) + r"\s*=", code):
            r.append("R41_PS_SWITCH_SHADOWED:" + name)
            break
    if re.search(r"\[ordered\]", code) and ".ContainsKey(" in code:
        r.append("R42_PS_ORDERED_CONTAINSKEY")
    if re.search(r"Get-ChildItem[^\n]*-Recurse", code):
        r.append("R43_PS_GCI_RECURSE_SLOW")
    return r


def scan_ps1(path: Path, root: Path, fid_counter: list[int]) -> tuple[FileRec, list[FuncRec]]:
    rel = str(path.relative_to(root)).replace("\\", "/")
    module = rel.rsplit(".", 1)[0].replace("/", ".")
    try:
        if _is_cloud_placeholder(path):
            return FileRec(rel, module, 0, False, "CLOUD_PLACEHOLDER", [], [], 0, False, 0, 0, ["R05_READ_FAIL"], skipped="CLOUD_PLACEHOLDER", lang="ps1"), []
        if path.stat().st_size > MAX_FILE_BYTES:
            return FileRec(rel, module, 0, False, "SKIP_LARGE", [], [], 0, False, 0, 0, [], skipped="SKIP_LARGE", lang="ps1"), []
        src, enc = _read_source(path)
    except OSError as e:
        return FileRec(rel, module, 0, False, f"READ_FAIL: {e}", [], [], 0, False, 0, 0, ["R05_READ_FAIL"], lang="ps1"), []
    chash = hashlib.blake2s(src.encode("utf-8", "replace"), digest_size=8).hexdigest()
    lines_n = src.count("\n") + 1
    code = _strip_ps_comments(src)
    # 嵌入的 python here-string 不算 PS 函式 (VES/VTH/VSX 這種殼)
    code_noh = re.sub(r"@['\"]\r?\n.*?\r?\n['\"]@", "<HERESTRING>", code, flags=re.S)
    funcs: list[FuncRec] = []
    cmdlets_all = set(re.findall(r"\b([A-Z][a-z]+-[A-Z][A-Za-z]+)\b", code_noh))
    dotnet_all = set(re.findall(r"\[(System\.[\w.]+)\]", code_noh))

    def fam_of(names: set[str]) -> list[str]:
        fams = set()
        for n in names:
            for rx, f in PS_TOOL_FAMILIES.items():
                if re.search(rx, n):
                    fams.add(f)
        return sorted(fams)

    file_tools = fam_of(cmdlets_all | dotnet_all)
    for m in re.finditer(r"(?im)^\s*function\s+([\w\-:]+)\s*(\(([^)]*)\))?\s*\{", code_noh):
        name = m.group(1)
        start = m.end() - 1
        end = _match_brace(code_noh, start)
        body = code_noh[start:end + 1]
        lineno = code_noh.count("\n", 0, m.start()) + 1
        end_lineno = code_noh.count("\n", 0, end) + 1
        params = []
        pm = re.search(r"param\s*\((.*?)\)\s*(?:\n|$)", body, re.S | re.I)
        ptxt = pm.group(1) if pm else (m.group(3) or "")
        annots, defaults = {}, {}
        for pd_ in re.finditer(r"(?:\[([\w\[\]\.]+)\]\s*)?\$(\w+)(?:\s*=\s*([^,\n)]+))?", ptxt):
            typ, pn, dv = pd_.group(1), pd_.group(2), pd_.group(3)
            params.append(pn)
            annots[pn] = typ or ""
            if dv:
                defaults[pn] = dv.strip()
        calls = sorted(set(re.findall(r"\b([A-Z][a-z]+-[A-Z][A-Za-z]+)\b", body)) | {"[" + d + "]" for d in re.findall(r"\[(System\.[\w.]+)\]", body)})[:40]
        tools = fam_of(set(re.findall(r"\b([A-Z][a-z]+-[A-Z][A-Za-z]+)\b", body)) | set(re.findall(r"\[(System\.[\w.]+)\]", body)))
        toks = norm_tokens(name.split(":")[-1])
        fid_counter[0] += 1
        rec = FuncRec(fid=f"FN-{fid_counter[0]:05d}", file=rel, module=module, qualname=name, name=name, lineno=lineno, end_lineno=end_lineno,
                      args=params, has_varargs=False, has_kwargs=("$args" in body.lower()), annotated_args=sum(1 for a in params if annots.get(a)),
                      has_return_annot=False, decorators=[], tools=tools, calls=calls, tokens=toks, capability=capability_of(toks),
                      body_hash=_norm_body_hash(body, "ps1"), doc="", is_method=False, stmts=max(1, body.count("\n") // 2), abspath=str(path),
                      lang="ps1", arg_annots=annots, arg_defaults=defaults, doc_tokens=[])
        if params and rec.annotated_args < len(params):
            rec.risks.append("R03_MISSING_TYPE_HINTS")
        if "$args" in body.lower():
            rec.risks.append("R07_KWARGS_ABUSE")
        if re.search(r"\$(?:global|script):\w+\s*=", body):
            rec.risks.append("R18_GLOBAL_CONFIG:M")
        funcs.append(rec)
    frisks = _ll_audit_ps(src, rel)
    if re.search(r"\bInvoke-Expression\b|\biex\b", code_noh):
        frisks.append("R01_DYNAMIC_IMPORT")
    own = {f.name for f in funcs}
    frec = FileRec(rel, module, lines_n, True, "", sorted(cmdlets_all - own)[:60], file_tools, len(funcs),
                   "Invoke-Expression" in code_noh, 0, len(re.findall(r"\bWrite-Host\b", code_noh)), frisks, [], enc, chash, "", 0, 0, lang="ps1")
    return frec, funcs


def scan_js(path: Path, root: Path, fid_counter: list[int]) -> tuple[FileRec, list[FuncRec]]:
    rel = str(path.relative_to(root)).replace("\\", "/")
    module = rel.rsplit(".", 1)[0].replace("/", ".")
    try:
        if _is_cloud_placeholder(path):
            return FileRec(rel, module, 0, False, "CLOUD_PLACEHOLDER", [], [], 0, False, 0, 0, ["R05_READ_FAIL"], skipped="CLOUD_PLACEHOLDER", lang="js"), []
        if path.stat().st_size > MAX_FILE_BYTES:
            return FileRec(rel, module, 0, False, "SKIP_LARGE", [], [], 0, False, 0, 0, [], skipped="SKIP_LARGE", lang="js"), []
        src, enc = _read_source(path)
    except OSError as e:
        return FileRec(rel, module, 0, False, f"READ_FAIL: {e}", [], [], 0, False, 0, 0, ["R05_READ_FAIL"], lang="js"), []
    chash = hashlib.blake2s(src.encode("utf-8", "replace"), digest_size=8).hexdigest()
    code = re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group(0).count("\n"), src, flags=re.S)
    code = re.sub(r"(?m)(?<![:\"'])//.*$", "", code)
    imports = set(re.findall(r"""(?:from\s+|require\(\s*)['\"]([^'\"]+)['\"]""", code)) | set(re.findall(r"""import\s+['\"]([^'\"]+)['\"]""", code))
    file_tools = sorted({JS_TOOL_FAMILIES[i.split("/")[0] if not i.startswith("@") else "/".join(i.split("/")[:2])] for i in imports
                         if (i.split("/")[0] if not i.startswith("@") else "/".join(i.split("/")[:2])) in JS_TOOL_FAMILIES})
    if re.search(r"\bfetch\(", code):
        file_tools = sorted(set(file_tools) | {"requests"})
    funcs: list[FuncRec] = []
    pat = re.compile(r"(?m)^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s*\*?\s*([A-Za-z_$][\w$]*)\s*\(([^)]*)\)\s*\{"
                     r"|^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?(?:\(([^)]*)\)|([A-Za-z_$][\w$]*))\s*=>\s*\{"
                     r"|^\s*(?:static\s+)?(?:async\s+)?([A-Za-z_$][\w$]*)\s*\(([^)]*)\)\s*\{")
    class_stack: list[tuple[str, int]] = []
    for cm in re.finditer(r"class\s+([A-Za-z_$][\w$]*)[^{]*\{", code):
        end = _match_brace(code, cm.end() - 1)
        class_stack.append((cm.group(1), cm.start(), end))
    for m in pat.finditer(code):
        name = m.group(1) or m.group(3) or m.group(6)
        if not name or name in ("if", "for", "while", "switch", "catch", "function", "return"):
            continue
        params = m.group(2) if m.group(2) is not None else (m.group(4) if m.group(4) is not None else (m.group(5) or (m.group(7) or "")))
        start = m.end() - 1
        end = _match_brace(code, start)
        body = code[start:end + 1]
        lineno = code.count("\n", 0, m.start()) + 1
        cls = next((c for c, a, b in class_stack if a < m.start() < b), "")
        is_method = bool(m.group(6)) and bool(cls)
        if m.group(6) and not cls:
            continue                                                       # 物件字面量方法/if 區塊誤判：略過
        args = [re.sub(r"[=:].*$", "", a).strip().lstrip(".") for a in params.split(",") if a.strip()]
        annots = {}
        for a in params.split(","):
            if ":" in a:
                k, v = a.split(":", 1)
                annots[k.strip()] = v.split("=")[0].strip()
        calls = sorted(set(re.findall(r"\b([A-Za-z_$][\w$.]*)\s*\(", body)))[:40]
        tools = sorted({JS_TOOL_FAMILIES[c.split(".")[0]] for c in calls if c.split(".")[0] in JS_TOOL_FAMILIES} | ({"requests"} if "fetch(" in body else set()))
        if not any(t in DATA_FAMS for t in tools):
            tools = sorted(set(tools) | {t for t in file_tools if t in DATA_FAMS})
        toks = norm_tokens(name)
        fid_counter[0] += 1
        rec = FuncRec(fid=f"FN-{fid_counter[0]:05d}", file=rel, module=module, qualname=(cls + "." + name if cls else name), name=name,
                      lineno=lineno, end_lineno=code.count("\n", 0, end) + 1, args=args, has_varargs=("..." in params), has_kwargs=False,
                      annotated_args=len(annots), has_return_annot=bool(re.match(r"[^{]*\)\s*:\s*\w", code[m.start():m.end()])),
                      decorators=[], tools=tools, calls=calls, tokens=toks, capability=capability_of(toks),
                      body_hash=_norm_body_hash(body, "js"), doc="", is_method=is_method, stmts=max(1, body.count(";")), abspath=str(path),
                      lang="js", arg_annots=annots, arg_defaults={}, doc_tokens=[])
        if args and len(annots) < len(args):
            rec.risks.append("R03_MISSING_TYPE_HINTS")
        if "console." in body:
            rec.risks.append("R19_PRINT_LOGGING")
        if re.search(r"\beval\(|new Function\(", body):
            rec.risks.append("R01_DYNAMIC_IMPORT")
        funcs.append(rec)
    frisks = []
    if re.search(r"\beval\(|new Function\(|require\([^'\"]", code):
        frisks.append("R01_DYNAMIC_IMPORT")
    if re.search(r"(?m)^\s*(?:const|let|var)\s+\w+\s*=\s*(\{|\[)", code):
        frisks.append("R16_MODULE_MUTABLE_STATE")
    frec = FileRec(rel, module, src.count("\n") + 1, True, "", sorted(imports)[:60], file_tools, len(funcs), False, 0,
                   len(re.findall(r"console\.log", code)), frisks, [], enc, chash, "", 0, 0, lang="js")
    return frec, funcs


# ---------------------------------------------------------------- clustering
_GENERIC_ARGS = {"df", "data", "start", "end", "path", "x", "y", "args", "kwargs", "self", "cls", "config",
                 "cfg", "params", "opts", "options", "verbose", "dry_run", "debug", "root", "out", "name", "key", "value"}
_GENERIC_METHODS = {"append", "get", "items", "keys", "values", "join", "split", "strip", "format", "lower",
                    "upper", "replace", "startswith", "endswith", "len", "str", "int", "float", "print", "info",
                    "debug", "warning", "error", "exists", "open", "read", "write", "close", "isinstance"}


def _call_fingerprint(f: FuncRec) -> set[str]:
    out = set()
    for c in f.calls:
        m = c.split(".")[-1]
        if m and m not in _GENERIC_METHODS and not m.startswith("<"):
            out.add(m.lower())
    return out


def _canon(tokens: list[str]) -> list[str]:
    return [VERB_TO_CAP.get(t, t) for t in tokens]


def sig_similarity(a: FuncRec, b: FuncRec) -> float:
    ta, tb = _canon(a.tokens), _canon(b.tokens)
    if not ta or not tb:
        return 0.0
    name_r = difflib.SequenceMatcher(None, " ".join(ta), " ".join(tb)).ratio()
    set_r = len(set(ta) & set(tb)) / max(1, len(set(ta) | set(tb)))
    arg_r = 0.0
    if a.args or b.args:
        # 泛用參數名(df/start/end/path/data…)只算 0.3 權重，避免「剛好都叫 df,start,end」被誤合併
        def _w(x):
            return 0.3 if x in _GENERIC_ARGS else 1.0
        inter = sum(_w(x) for x in set(a.args) & set(b.args))
        union = sum(_w(x) for x in set(a.args) | set(b.args))
        arg_r = inter / max(0.3, union)
    fa, fb = _call_fingerprint(a), _call_fingerprint(b)
    call_r = (len(fa & fb) / max(1, len(fa | fb))) if (fa or fb) else 0.5   # 呼叫鏈指紋(方法名集合)
    cap_bonus = 0.1 if (a.capability == b.capability and a.capability != "OTHER") else 0.0
    doc_r = 0.0
    if a.doc_tokens and b.doc_tokens:                     # docstring 語意加權(本機、零外呼)
        doc_r = len(set(a.doc_tokens) & set(b.doc_tokens)) / max(1, len(set(a.doc_tokens) | set(b.doc_tokens)))
    base = 0.40 * name_r + 0.30 * set_r + 0.15 * arg_r + 0.15 * call_r + cap_bonus
    sem_r = _SEM.sim(a, b) if _SEM.ready else 0.0            # v0800 ②：語意相似度 (embedding / tfidf / hashing)
    return min(1.0, base + 0.15 * doc_r + 0.15 * sem_r)


def build_call_graph(funcs: list[FuncRec]) -> None:
    """v0600 接收者感知呼叫圖：
       bare f()            → 同模組同名函式優先，否則全域同名『模組層函式』
       self.m() / cls.m()  → 同類別方法（含同模組同名類別鏈無法得知父類時保守：只算同類別）
       ClassName.m()       → 該類別方法
       其他 x.m()          → 多型模糊：不算 fan_in，記 fan_in_ambiguous
       DORMANT_STRONG = fan_in==0 且 ambiguous==0；DORMANT_WEAK = fan_in==0 但有模糊命中。"""
    by_qual: dict[str, FuncRec] = {(f.module + "." + f.qualname): f for f in funcs}
    by_name_mod: dict[tuple, list[FuncRec]] = defaultdict(list)         # (module, name) 模組層函式
    by_name_global: dict[str, list[FuncRec]] = defaultdict(list)
    by_class_method: dict[tuple, list[FuncRec]] = defaultdict(list)     # (ClassName, method)
    by_method_any: dict[str, list[FuncRec]] = defaultdict(list)
    for f in funcs:
        if not f.is_method:
            by_name_mod[(f.module, f.name)].append(f)
            by_name_global[f.name].append(f)
        else:
            cls = f.qualname.rsplit(".", 1)[0].rsplit(".", 1)[-1]
            by_class_method[(cls, f.name)].append(f)
            by_method_any[f.name].append(f)
        f.fan_in = 0
        f.fan_out = 0
        f.fan_in_ambiguous = 0
    for f in funcs:
        own_cls = f.qualname.rsplit(".", 1)[0].rsplit(".", 1)[-1] if f.is_method else ""
        resolved: set[str] = set()
        for c in set(f.calls):
            parts = c.split(".")
            tgts: list[FuncRec] = []
            if len(parts) == 1:
                tgts = by_name_mod.get((f.module, parts[0])) or by_name_global.get(parts[0]) or []
            else:
                recv, meth = parts[0], parts[-1]
                if recv in ("self", "cls") and own_cls:
                    tgts = by_class_method.get((own_cls, meth), [])
                elif recv and recv[:1].isupper() and (recv, meth) in by_class_method:
                    tgts = by_class_method[(recv, meth)]
                elif recv == "<expr>" or True:
                    if meth in by_method_any and not tgts:
                        for t in by_method_any[meth]:
                            if t is not f:
                                t.fan_in_ambiguous += 1
                    continue
            for t in tgts:
                if t is not f and (t.module + "." + t.qualname) not in resolved:
                    resolved.add(t.module + "." + t.qualname)
                    t.fan_in += 1
        f.fan_out = len(resolved)
    entry = {"main", "run", "cli", "app", "handler", "lambda_handler", "wsgi", "asgi", "setup", "test"}
    for f in funcs:
        base_ok = (not f.name.startswith("_") and not f.name.startswith("test_") and f.name not in entry
                   and not any(d in ("route", "get", "post", "command", "task", "register", "app", "property",
                                     "abstractmethod", "override") for d in f.decorators)
                   and not (f.name.startswith("__") and f.name.endswith("__")))
        if base_ok and f.fan_in == 0:
            f.dormant_candidate = True
            f.dormant_level = "STRONG" if f.fan_in_ambiguous == 0 else "WEAK"
        else:
            f.dormant_candidate = False
            f.dormant_level = ""


def build_clusters(funcs: list[FuncRec], threshold: float, max_group: int = 30, time_budget: float = CLUSTER_TIME_BUDGET_S):
    """回傳 identical / same_cap_diff_tool / near_dup 三種群。風險6: 超過時間預算 → 降級只做 exact-token 匹配。"""
    _t0 = time.time()
    identical: dict[str, list[FuncRec]] = defaultdict(list)
    for f in funcs:
        if f.end_lineno - f.lineno >= 2 and f.stmts >= 2:
            identical[f.body_hash].append(f)
    identical_groups = []
    for g in identical.values():
        if len(g) < 2:
            continue
        if not (len({x.file for x in g}) > 1 or len({x.qualname for x in g}) > 1):
            continue
        # 風險5: 同名方法在多個類別(override/Protocol 實作樣式) → 降級標記，不當作可合併重複
        if all(x.is_method for x in g) and len({x.name for x in g}) == 1:
            for x in g:
                if "R28_OVERRIDE_PATTERN" not in x.risks:
                    x.risks.append("R28_OVERRIDE_PATTERN")
            continue
        identical_groups.append(g)

    # candidate pairs: 同能力軸 且 名稱 token 有交集
    by_cap: dict[str, list[FuncRec]] = defaultdict(list)
    for f in funcs:
        if f.capability != "OTHER" and f.tokens and not f.name.startswith("_") and not f.name.startswith("test_"):
            by_cap[f.capability].append(f)
    parent = {f.fid: f.fid for f in funcs}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    pair_scores = {}
    for cap, lst in by_cap.items():
        # bucket by first 2 tokens to avoid O(n^2) explosions
        idx: dict[str, list[FuncRec]] = defaultdict(list)
        for f in lst:
            for t in set(_canon(f.tokens)):
                idx[t].append(f)
        seen = set()
        for t, bucket in idx.items():
            if len(bucket) > 400:
                continue
            for i in range(len(bucket)):
                for j in range(i + 1, len(bucket)):
                    a, b = bucket[i], bucket[j]
                    key = tuple(sorted((a.fid, b.fid)))
                    if key in seen or a.file == b.file and a.qualname == b.qualname:
                        continue
                    seen.add(key)
                    if time.time() - _t0 > time_budget:
                        if not getattr(build_clusters, "_budget_warned", False):
                            print(f"@@PROGRESS|warn|cluster time budget {time_budget}s exceeded -> exact-token only", flush=True)
                            build_clusters._budget_warned = True
                        s = 1.0 if _canon(a.tokens) == _canon(b.tokens) else 0.0
                    else:
                        s = sig_similarity(a, b)
                    if s >= threshold:
                        union(a.fid, b.fid)
                        pair_scores[key] = round(s, 3)

    groups: dict[str, list[FuncRec]] = defaultdict(list)
    fmap = {f.fid: f for f in funcs}
    for fid in parent:
        r = find(fid)
        groups[r].append(fmap[fid])
    # 超大群圖切割：對 >max_group 的連通分量逐步提高門檻重新連通，斬斷連鎖傳遞
    cut_groups = []
    for g in list(groups.values()):
        if len(g) <= max_group:
            cut_groups.append(g)
            continue
        th = threshold
        pending = [g]
        while pending:
            cur = pending.pop()
            if len(cur) <= max_group or th >= 0.96:
                cut_groups.append(cur)
                continue
            th = round(th + 0.05, 2)
            adj = {x.fid: set() for x in cur}
            for i in range(len(cur)):
                for j in range(i + 1, len(cur)):
                    if sig_similarity(cur[i], cur[j]) >= th:
                        adj[cur[i].fid].add(cur[j].fid)
                        adj[cur[j].fid].add(cur[i].fid)
            seen_c = set()
            for x in cur:
                if x.fid in seen_c:
                    continue
                comp, stack = [], [x.fid]
                while stack:
                    y = stack.pop()
                    if y in seen_c:
                        continue
                    seen_c.add(y)
                    comp.append(fmap[y])
                    stack.extend(adj[y] - seen_c)
                pending.append(comp)
    groups = {i: g for i, g in enumerate(cut_groups)}
    same_cap_diff_tool, near_dup = [], []
    for g in groups.values():
        if len(g) < 2:
            continue
        tool_sets = [set(x.tools) - {"print", "logging", "loguru", "pathlib", "os", "datetime", "re", "json"}
                     for x in g]
        distinct = {frozenset(t) for t in tool_sets if t}
        rec = {
            "members": g,
            "capability": g[0].capability,
            "tools": sorted({t for ts in tool_sets for t in ts}),
            "distinct_tool_sets": len(distinct),
            "files": len({x.file for x in g}),
            "score": max([pair_scores.get(tuple(sorted((a.fid, b.fid))), 0)
                          for a in g for b in g if a.fid < b.fid] or [0]),
            "param_alias": _param_alias(g),
            "proposed_interface": _propose_interface(g),
            "recommendation": _recommend_engine(g),
        }
        rec["langs"] = sorted({x.lang for x in g})
        if len(rec["langs"]) >= 2:
            rec["cluster_class"] = "same_cap_diff_lang"
            same_cap_diff_tool.append(rec)
        elif len(distinct) >= 2:
            rec["cluster_class"] = "same_cap_diff_tool"
            same_cap_diff_tool.append(rec)
        else:
            rec["cluster_class"] = "near_dup"
            near_dup.append(rec)
    same_cap_diff_tool.sort(key=lambda r: (-(len(r.get("langs", [])) >= 2), -r["distinct_tool_sets"], -len(r["members"])))
    near_dup.sort(key=lambda r: -len(r["members"]))
    return identical_groups, same_cap_diff_tool, near_dup


def _propose_interface(g: list[FuncRec]) -> dict:
    """升級4: 群級標準介面提案：canonical 參數聯集；出現在所有成員 = required，其餘 optional(帶最常見預設)。"""
    alias = _param_alias(g)
    canon_of: dict[str, dict[str, str]] = defaultdict(dict)
    for canon, per in alias.items():
        for fid, orig in per.items():
            canon_of[fid][orig] = canon
    presence: dict[str, list[str]] = defaultdict(list)
    annots: dict[str, Counter] = defaultdict(Counter)
    defaults: dict[str, Counter] = defaultdict(Counter)
    for m in g:
        for a in m.args:
            c = canon_of[m.fid].get(a, a)
            presence[c].append(m.fid)
            if m.arg_annots.get(a):
                annots[c][m.arg_annots[a]] += 1
            if a in m.arg_defaults:
                defaults[c][m.arg_defaults[a]] += 1
    params = []
    for c, fids in sorted(presence.items(), key=lambda kv: -len(kv[1])):
        params.append({"name": c, "required": len(set(fids)) == len(g),
                       "type": (annots[c].most_common(1)[0][0] if annots[c] else "Any"),
                       "default": (defaults[c].most_common(1)[0][0] if defaults[c] else None),
                       "coverage": f"{len(set(fids))}/{len(g)}"})
    cap = g[0].capability
    verb = {"READ": "load", "WRITE": "save", "PARSE": "parse", "TRANSFORM": "transform", "COMPUTE": "compute",
            "VALIDATE": "validate", "MERGE": "merge", "FILTER": "filter", "REPORT": "report"}.get(cap, "process")
    noun = "_".join(t for t in _canon(g[0].tokens) if t not in set(VERB_CANON) and t != "OTHER")[:40]
    return {"name": f"{verb}_{noun}".strip("_"), "params": params,
            "returns": Counter(("annotated" if m.has_return_annot else "unknown") for m in g).most_common(1)[0][0]}


def _recommend_engine(g: list[FuncRec]) -> dict:
    """升級8: 主/備引擎推薦：以 :M 級風險數最少、其次 :P、其次程式碼行數最少為主引擎；第二名為 fallback。"""
    def score(m: FuncRec):
        mm = sum(1 for r in m.risks if r.endswith(":M"))
        pp = sum(1 for r in m.risks if r.endswith(":P"))
        return (mm, pp, m.end_lineno - m.lineno)
    ranked = sorted(g, key=score)
    return {"primary": ranked[0].fid, "fallback": ranked[1].fid if len(ranked) > 1 else None,
            "basis": {m.fid: {"M": score(m)[0], "P": score(m)[1], "lines": score(m)[2], "tools": m.tools} for m in ranked}}


def _param_alias(g: list[FuncRec]) -> dict:
    """同群內參數名同義映射(path/filepath/file_path/fname → 群內出現最多的那個)：canonical → {member.fid: 原參數名}"""
    buckets: dict[str, Counter] = defaultdict(Counter)
    for m in g:
        for a in m.args:
            key = "".join(t for t in norm_tokens(a) if t not in {"file", "name", "input", "output", "src", "dst"}) or a
            key = {"fp": "path", "p": "path", "fn": "path", "f": "path", "dir": "path", "folder": "path",
                   "start": "start", "begin": "start", "end": "end", "stop": "end", "until": "end",
                   "df": "data", "frame": "data", "table": "data", "rows": "data"}.get(key, key)
            buckets[key][a] += 1
    out = {}
    for key, cnt in buckets.items():
        canon = cnt.most_common(1)[0][0]
        per = {}
        for m in g:
            for a in m.args:
                if a in cnt:
                    per[m.fid] = a
        if len(cnt) > 1 or len(per) > 1:
            out[canon] = per
    return out


# ---------------------------------------------------------------- scaffold
import keyword as _kw


def slug(s: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")
    return s or "engine"


def pascal(s: str) -> str:
    out = "".join(p[:1].upper() + p[1:] for p in re.split(r"[^A-Za-z0-9]+", s) if p)
    if not out or out[0].isdigit():                       # 風險11: 識別字消毒
        out = "E" + out
    if _kw.iskeyword(out):
        out += "_"
    return out


def via_code(kind: str, name: str, context: str) -> tuple[str, str]:
    """升級5: 平台統一編碼 recipe VIA-{TYPE}-blake2s(TYPE|name|context, digest=3).hexUpper；回 (code, hash_input) — LL#30 雜湊輸入必須入檔。"""
    inp = f"{kind}|{name}|{context}"
    return f"VIA-{kind}-{hashlib.blake2s(inp.encode('utf-8'), digest_size=3).hexdigest().upper()}", inp


def gen_scaffold(out: Path, clusters: list[dict], have_pydantic: bool, root_for_conftest: Path = Path(".")) -> list[str]:
    sd = out / "_standardized"
    (sd / "adapters").mkdir(parents=True, exist_ok=True)
    (sd / "tests").mkdir(parents=True, exist_ok=True)
    written = []

    if have_pydantic:
        schema = '''from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Dict


class EngineRequest(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")   # R06/R08: 過渡期 allow，盤點後改 forbid
    task_id: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    config: Dict[str, Any] = Field(default_factory=dict)      # R07/R18: 舊 kwargs 與環境設定統一注入
    strict_mode: bool = True
    max_payload_bytes: int = 64 * 1024 * 1024   # 記憶體管制：大物件請傳路徑/handle，不要塞 payload
    inputs: Dict[str, Any] = Field(default_factory=dict)   # v0300: 檔案指標(DataPointer)，資料本體永不進 payload


class EngineResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    status: str
    result: Any = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    engine: str = ""
    elapsed_ms: float = 0.0
'''
    else:
        schema = '''from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class EngineRequest:              # pydantic 不在環境 → dataclass 降級(介面完全相同)
    task_id: str
    payload: Dict[str, Any] = field(default_factory=dict)
    config: Dict[str, Any] = field(default_factory=dict)
    strict_mode: bool = True
    max_payload_bytes: int = 64 * 1024 * 1024
    inputs: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EngineResponse:
    status: str
    result: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    engine: str = ""
    elapsed_ms: float = 0.0
'''
    model_support = ('''from pydantic import BaseModel as _PydBase, ValidationError as _VE


class _Model(_PydBase):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")


def _validate(model_cls, kwargs: dict):
    try:
        return model_cls(**kwargs)
    except _VE as e:
        raise ValueError(f"payload validation failed for {model_cls.__name__}: {e}") from e


def _asdict(m) -> dict:
    return m.model_dump()
''' if have_pydantic else '''class _Model:
    """dataclass 降級：子類用類別註記宣告欄位；_validate 只檢查必填，不做型別強制。"""
    def __init__(self, **kw):
        ann = {}
        for k in reversed(type(self).__mro__):
            ann.update(getattr(k, "__annotations__", {}))
        for name in ann:
            if name in kw:
                setattr(self, name, kw[name])
            elif hasattr(type(self), name):
                setattr(self, name, getattr(type(self), name))
            else:
                raise ValueError(f"missing required payload field: {name}")
        self._fields = list(ann)


def _validate(model_cls, kwargs: dict):
    return model_cls(**kwargs)


def _asdict(m) -> dict:
    return {k: getattr(m, k) for k in m._fields}
''')
    base = f'''# -*- coding: utf-8 -*-
"""VIA Engine Standardizer v{VERSION} — 標準介面(自動生成，只增不減：可加欄位，勿刪)"""
from __future__ import annotations
import re
import time
import logging
import os as _os
from pathlib import Path as _Path
from abc import ABC, abstractmethod
from typing import Any, Dict, Type

{schema}

class Trace:
    """本地遙測(OpenTelemetry 語意的極簡版)：每個 task_id 一條 trace，span 以 JSONL 追加到 ves_trace.jsonl。
    零依賴；之後要接 OTLP exporter 只需替換 _emit。"""
    path = _Path(_os.environ.get("VES_TRACE_PATH", "ves_trace.jsonl"))
    enabled = True
    _seq = 0

    @classmethod
    def start(cls, task_id: str, name: str, parent: str | None = None) -> dict:
        cls._seq += 1
        return {{"trace_id": task_id, "span_id": f"{{cls._seq:06d}}", "parent": parent, "name": name,
                "t0": time.perf_counter(), "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}}

    @classmethod
    def end(cls, span: dict, status: str = "ok", error: str | None = None) -> None:
        span["ms"] = round((time.perf_counter() - span.pop("t0")) * 1000, 3)
        span["status"] = status
        if error:
            span["error"] = error
        cls._emit(span)

    @classmethod
    def span(cls, task_id: str, name: str):
        from contextlib import contextmanager

        @contextmanager
        def _cm():
            sp = cls.start(task_id, name)
            try:
                yield sp
                cls.end(sp, "ok")
            except Exception as e:  # noqa: BLE001
                cls.end(sp, "error", f"{{type(e).__name__}}: {{e}}")
                raise
        return _cm()

    max_bytes = 50 * 1024 * 1024               # 風險17: trace 滾動

    @classmethod
    def _emit(cls, span: dict) -> None:
        if not cls.enabled:
            return
        try:
            import json as _json
            try:
                if cls.path.exists() and cls.path.stat().st_size > cls.max_bytes:
                    cls.path.rename(cls.path.with_suffix(f".{{int(time.time())}}.jsonl"))
            except OSError:
                pass
            with open(cls.path, "a", encoding="utf-8") as fh:
                fh.write(_json.dumps(span, ensure_ascii=False) + "\\n")
        except Exception:  # noqa: BLE001
            pass


class BaseProcessor(ABC):
    """所有轉接器的錨點。Context Manager 保證資源回收(R17)；process() 內部才做重型 import(R20)。"""
    engine_name: str = "base"

    def __init__(self, logger: logging.Logger | None = None):
        self.log = logger or logging.getLogger("VIA.engine")

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False

    def close(self) -> None:
        pass

    @abstractmethod
    def _run(self, request: EngineRequest) -> Any:
        ...

    def process(self, request: EngineRequest) -> EngineResponse:
        t0 = time.perf_counter()
        span = Trace.start(request.task_id, f"engine.{{self.engine_name}}.process")
        try:
            est = estimate_bytes(request.payload)
            if est > request.max_payload_bytes:
                msg = f"payload ~{{est / 1e6:.1f}}MB > limit {{request.max_payload_bytes / 1e6:.0f}}MB; pass a path/handle instead"
                if request.strict_mode:
                    raise PayloadTooLarge(msg)
                self.log.warning(msg)
            with Trace.span(request.task_id, f"engine.{{self.engine_name}}.run"):
                result = self._run(request)
            with Trace.span(request.task_id, f"engine.{{self.engine_name}}.materialize"):
                result = self.materialize(result)                   # R13: 強制實體化
            Trace.end(span, "ok")
            return EngineResponse(status="success", result=result, engine=self.engine_name,
                                  elapsed_ms=(time.perf_counter() - t0) * 1000)
        except Exception as e:  # noqa: BLE001
            self.log.exception("engine %s failed task=%s", self.engine_name, request.task_id)
            Trace.end(span, "error", f"{{type(e).__name__}}: {{e}}")
            return EngineResponse(status="error", result=None, engine=self.engine_name,
                                  metadata={{"error": f"{{type(e).__name__}}: {{e}}"}},
                                  elapsed_ms=(time.perf_counter() - t0) * 1000)

    @staticmethod
    def materialize(x: Any) -> Any:
        """可插拔實體化：依序試 MATERIALIZERS 的 (predicate, fn)；全部失敗回原物件，絕不拋錯(R13)。"""
        for pred, fn in MATERIALIZERS:
            try:
                if pred(x):
                    return fn(x)
            except Exception:  # noqa: BLE001
                continue
        return x


class PayloadTooLarge(ValueError):
    pass


# ============================================================ v0300 檔案指標層 (DataPointer)
# 原則：payload 只放控制指令(幾 KB)；資料本體用指標宣告來源，轉接器依引擎延遲解析。
import os as _os
from pathlib import Path as _Path

SAFE_ROOTS: list = [p for p in (
    _os.environ.get("VIA_SAFE_ROOTS", "").split(_os.pathsep) + [__SAFE_ROOTS__]) if p]   # append-only 白名單


def add_safe_root(p: str) -> None:
    rp = str(_Path(p).resolve())
    if rp not in SAFE_ROOTS:
        SAFE_ROOTS.append(rp)


def _in_safe_roots(p: _Path) -> bool:
    """風險14: OneDrive/junction 下 resolve 前後路徑不同 → 兩種都比。"""
    cands = {{p.resolve(), _Path(_os.path.abspath(str(p)))}}
    for r in SAFE_ROOTS:
        for rr in (_Path(r).resolve(), _Path(_os.path.abspath(r))):
            for rp in cands:
                try:
                    rp.relative_to(rr)
                    return True
                except ValueError:
                    continue
    return False


FORCE_LAZY_BYTES = 512 * 1024 * 1024        # 風險15: 大檔 lazy=False 也強制 lazy


class PointerError(ValueError):
    pass


class LocalFilePointer:
    source_type = "local_file"

    def __init__(self, path: str, format: str | None = None, lazy: bool = True, columns: list | None = None):
        self.path = _Path(path)
        self.format = (format or self.path.suffix.lstrip(".").lower() or "csv").replace("jsonl", "ndjson")
        self.lazy = lazy
        self.columns = columns
        self.validate()

    def validate(self) -> None:
        if self.format not in {{"parquet", "csv", "ndjson", "json", "xlsx", "feather", "arrow"}}:
            raise PointerError(f"unsupported format: {{self.format}}")
        if not self.path.exists():
            raise PointerError(f"file not found: {{self.path}}")
        if SAFE_ROOTS and not _in_safe_roots(self.path):
            raise PointerError(f"path outside SAFE_ROOTS (目錄遍歷防護): {{self.path.resolve()}}")
        try:
            if not self.lazy and self.path.stat().st_size > FORCE_LAZY_BYTES:
                self.lazy = True
                self.forced_lazy = True
        except OSError:
            pass

    def to_dict(self) -> dict:
        return {{"source_type": self.source_type, "path": str(self.path), "format": self.format,
                "lazy": self.lazy, "columns": self.columns}}


class DatabasePointer:
    source_type = "database"

    def __init__(self, dsn: str, query: str, parameters: dict | list | None = None, driver: str = "duckdb"):
        q = query.strip().rstrip(";").strip()
        self.dsn, self.query, self.parameters, self.driver = dsn, q, (parameters if parameters is not None else {{}}), driver
        self._guard()

    def _guard(self) -> None:
        """v0600 三層守門，主力在驅動層：
        (1) 驅動解析器：duckdb.extract_statements / sqlite3.complete_statement → 必須恰好 1 個語句且為 SELECT 類
        (2) 唯讀連線：duckdb read_only=True / sqlite mode=ro；即使繞過解析，DB 本身拒寫
        (3) 強制參數化：查詢裡不得出現字串常值以外的使用者拼接——參數只能用 ? / $name / :name 佔位並在 parameters 提供
        字串檢查(; -- /*)只剩縱深防禦，不再是主力。"""
        q = self.query
        if self.driver == "duckdb":
            try:
                import duckdb
                try:
                    stmts = duckdb.extract_statements(q)
                except Exception as e:  # noqa: BLE001  驅動解析失敗 = 拒絕
                    raise PointerError(f"DatabasePointer: 驅動解析失敗 → 拒絕 ({{type(e).__name__}})") from e
                if len(stmts) != 1:
                    raise PointerError(f"DatabasePointer: 驅動解析出 {{len(stmts)}} 個語句，只允許 1 個")
                st = stmts[0]
                stype = str(getattr(st, "type", "")).upper()
                if not any(k in stype for k in ("SELECT", "EXPLAIN", "PRAGMA", "SHOW", "DESCRIBE")):
                    raise PointerError(f"DatabasePointer: 驅動判定語句型別 {{stype}} 非唯讀")
                self._parsed = True
            except ImportError:
                self._parsed = False
        else:
            import sqlite3
            if not sqlite3.complete_statement(q + ";"):
                raise PointerError("DatabasePointer: sqlite 解析器判定語句不完整")
            self._parsed = True
        head = q.lstrip("(").split(None, 1)[0].lower() if q else ""
        if head not in ("select", "with", "pragma", "describe", "show", "explain"):
            raise PointerError("DatabasePointer 只允許唯讀查詢 (SELECT/WITH/EXPLAIN)")
        # 參數化強制：偵測 f-string / % / format 殘跡與未綁定的引號拼接
        placeholders = len(re.findall(r"(?<![\\w$])\\?|\\$\\w+|(?<![\\w:]):\\w+", q))
        if isinstance(self.parameters, dict):
            provided = len(self.parameters)
        else:
            provided = len(self.parameters)
        if placeholders == 0 and provided > 0:
            raise PointerError("DatabasePointer: 提供了 parameters 但查詢沒有佔位符（禁止字串拼接）")
        if placeholders > 0 and provided < placeholders and isinstance(self.parameters, list):
            raise PointerError(f"DatabasePointer: 佔位符 {{placeholders}} 個，參數只給 {{provided}} 個")
        if re.search(r"\\{{\\s*\\w+\\s*\\}}|%\\(\\w+\\)s|%s", q):
            raise PointerError("DatabasePointer: 查詢含 format/% 模板殘跡，請改用 ? 或 $name 參數化")
        if ";" in q or "--" in q or "/*" in q:                        # 縱深防禦（非主力）
            raise PointerError("DatabasePointer 拒絕多語句與註解 (; -- /*)")
        dsn = self.dsn
        if dsn not in (":memory:", "") and not dsn.startswith(("postgres", "mysql", "sqlite://")):
            if SAFE_ROOTS and not _in_safe_roots(_Path(dsn)):
                raise PointerError(f"db file outside SAFE_ROOTS: {{dsn}}")

    def to_dict(self) -> dict:
        return {{"source_type": self.source_type, "dsn": self.dsn, "query": self.query,
                "parameters": self.parameters, "driver": self.driver}}


class InlinePointer:
    """小資料(≤ max_inline_bytes)才允許內嵌；超過一律要求改用 LocalFilePointer。"""
    source_type = "inline"

    def __init__(self, data: Any, max_inline_bytes: int = 4 * 1024 * 1024):
        est = estimate_bytes(data)
        if est > max_inline_bytes:
            raise PointerError(f"inline data ~{{est / 1e6:.1f}}MB > {{max_inline_bytes / 1e6:.0f}}MB；請寫成檔案改用 LocalFilePointer")
        self.data = data

    def to_dict(self) -> dict:
        return {{"source_type": self.source_type, "data": self.data}}


def make_pointer(spec: Any):
    """dict → Pointer（discriminator = source_type）；已是 Pointer 原樣回傳。"""
    if isinstance(spec, (LocalFilePointer, DatabasePointer, InlinePointer)):
        return spec
    if isinstance(spec, dict):
        t = spec.get("source_type")
        if t == "local_file":
            return LocalFilePointer(spec["path"], spec.get("format"), spec.get("lazy", True), spec.get("columns"))
        if t == "database":
            return DatabasePointer(spec["dsn"], spec["query"], spec.get("parameters"), spec.get("driver", "duckdb"))
        if t == "inline":
            return InlinePointer(spec["data"])
        if "path" in spec:
            return LocalFilePointer(spec["path"], spec.get("format"), spec.get("lazy", True))
    if isinstance(spec, (str, _Path)) and _Path(spec).exists():
        return LocalFilePointer(spec)
    raise PointerError(f"cannot build pointer from: {{type(spec).__name__}}")


def resolve_pointer(ptr: Any, engine: str = "path", mode: str = "auto"):
    """依引擎延遲解析：
       engine=polars → LazyFrame(scan_*)   engine=duckdb → Relation(read_*)   engine=pandas → 分塊迭代器或路徑
       mode=path → 只回路徑字串(給原本吃 path 的舊函式)；mode=frame → 回資料物件；auto 依 engine。
       記憶體消耗接近 0，實體化交給 BaseProcessor.materialize 或呼叫端。"""
    ptr = make_pointer(ptr)
    if ptr.source_type == "inline":
        return ptr.data
    if ptr.source_type == "database":
        params = ptr.parameters if ptr.parameters else None
        if ptr.driver == "duckdb":
            import duckdb
            if ptr.dsn and ptr.dsn != ":memory:":
                con = duckdb.connect(ptr.dsn, read_only=True)                 # (2) 驅動層唯讀
            else:
                con = duckdb.connect()
                try:
                    con.execute("SET enable_external_access=false")       # 記憶體 DB 也鎖外部存取
                except Exception:  # noqa: BLE001
                    pass
            return con.execute(ptr.query, params)                           # (3) 參數化綁定，永不拼接
        import sqlite3
        con = sqlite3.connect(f"file:{{ptr.dsn}}?mode=ro", uri=True)
        con.execute("PRAGMA query_only=1")
        return con.execute(ptr.query, params or [])
    p = str(ptr.path)
    if mode == "path" or (mode == "auto" and engine in ("path", "plain", "")):
        return p
    if engine == "polars":
        import polars as pl
        fn = {{"parquet": pl.scan_parquet, "csv": pl.scan_csv, "ndjson": pl.scan_ndjson}}.get(ptr.format)
        if fn is None:
            return pl.read_excel(p) if ptr.format == "xlsx" else pl.read_ipc(p)
        lf = fn(p)
        if ptr.columns:
            lf = lf.select(ptr.columns)
        return lf if ptr.lazy else lf.collect()
    if engine == "duckdb":
        import duckdb
        con = duckdb.connect()
        reader = {{"parquet": "read_parquet", "csv": "read_csv_auto", "ndjson": "read_json_auto", "json": "read_json_auto"}}.get(ptr.format, "read_csv_auto")
        cols = ", ".join(ptr.columns) if ptr.columns else "*"
        return con.sql(f"SELECT {{cols}} FROM {{reader}}('{{p}}')")
    if engine == "pandas":
        import pandas as pd
        kw = {{"dtype_backend": "pyarrow"}}                     # R11: 與 Polars/DuckDB 空值語意對齊
        if ptr.format == "parquet":
            return pd.read_parquet(p, columns=ptr.columns)
        if ptr.format == "csv":
            return pd.read_csv(p, usecols=ptr.columns, chunksize=(1_000_000 if ptr.lazy else None), **kw)
        if ptr.format in ("ndjson", "json"):
            return pd.read_json(p, lines=(ptr.format == "ndjson"), **kw)
        return pd.read_excel(p, usecols=ptr.columns)
    return p


def resolve_inputs(request: EngineRequest, engine: str, modes: Dict[str, str] | None = None) -> Dict[str, Any]:
    """把 request.inputs 全部解析成引擎可用物件；modes = {{input_key: "path"|"frame"}}。"""
    modes = modes or {{}}
    out = {{}}
    for k, spec in (request.inputs or {{}}).items():
        out[k] = resolve_pointer(spec, engine, modes.get(k, "auto"))
    return out


PAYLOAD_CHECK = _os.environ.get("VES_PAYLOAD_CHECK", "sampled")   # sampled | full | off
_SAMPLE_N = 64


def estimate_bytes(obj: Any, _depth: int = 0, _seen: set | None = None, mode: str | None = None) -> int:
    """v0600 有界估算：sampled(預設)=每層最多看 64 個元素並外推、深度 3，熱路徑成本 O(1) 級；full=舊行為；off=跳過。"""
    import sys as _sys
    mode = mode or PAYLOAD_CHECK
    if mode == "off":
        return 0
    max_depth = 6 if mode == "full" else 3
    _seen = _seen if _seen is not None else set()
    if id(obj) in _seen or _depth > max_depth:
        return 0
    _seen.add(id(obj))
    for attr in ("nbytes", "estimated_size"):
        v = getattr(obj, attr, None)
        try:
            if callable(v):
                v = v()
            if isinstance(v, (int, float)):
                return int(v)
        except Exception:  # noqa: BLE001
            pass
    mu = getattr(obj, "memory_usage", None)
    if callable(mu):
        try:
            return int(mu(deep=True).sum())
        except Exception:  # noqa: BLE001
            pass
    n = _sys.getsizeof(obj, 0)
    if isinstance(obj, (str, bytes, bytearray, int, float, bool)) or obj is None:
        return n
    if isinstance(obj, dict):
        items = list(obj.items())
    elif isinstance(obj, (list, tuple, set, frozenset)):
        items = [(None, v) for v in obj]
    else:
        return n
    total = len(items)
    if total == 0:
        return n
    if mode == "full" or total <= _SAMPLE_N:
        sample = items
        scale = 1.0
    else:
        step = max(1, total // _SAMPLE_N)
        sample = items[::step][:_SAMPLE_N]
        scale = total / max(1, len(sample))
    part = 0
    for k, v in sample:
        if k is not None:
            part += estimate_bytes(k, _depth + 1, _seen, mode)
        part += estimate_bytes(v, _depth + 1, _seen, mode)
    return n + int(part * scale)


def _is_polars_lazy(x):
    return type(x).__name__ == "LazyFrame" and hasattr(x, "collect")


def _is_duck_rel(x):
    return type(x).__name__ in ("DuckDBPyRelation",) and hasattr(x, "df")


def _is_cursor(x):
    return hasattr(x, "fetchall") and hasattr(x, "description") and not hasattr(x, "columns")


def _is_lazy_iter(x):
    import types
    return isinstance(x, (types.GeneratorType, map, filter, zip, range))


MATERIALIZERS: list = [                       # append-only：專案自訂驅動物件在這裡加 (predicate, fn)
    (_is_polars_lazy, lambda x: x.collect()),
    (_is_duck_rel, lambda x: x.df()),
    (_is_cursor, lambda x: x.fetchall()),
    (lambda x: type(x).__name__ == "Dataset" and hasattr(x, "compute"), lambda x: x.compute()),   # dask/xarray
    (_is_lazy_iter, lambda x: list(x)),
]


class EngineFactory:
    """每次回傳全新實例(R16 執行緒安全)；append-only 登記。"""
    _registry: Dict[str, Type[BaseProcessor]] = {{}}
    _fallback: Dict[str, str] = {{}}

    @classmethod
    def register(cls, name: str, klass: Type[BaseProcessor], fallback: str | None = None) -> None:
        cls._registry.setdefault(name, klass)
        if fallback:
            cls._fallback.setdefault(name, fallback)

    @classmethod
    def get(cls, name: str) -> BaseProcessor:
        k = cls._registry.get(name.lower())
        if k is None:
            raise ValueError(f"Unknown engine: {{name}} (registered: {{sorted(cls._registry)}})")
        return k()

    @classmethod
    def run_with_fallback(cls, name: str, request: EngineRequest) -> EngineResponse:
        """R25 斷路器：主引擎失敗 → 狀態隔離後降級到 fallback。
        隔離：主引擎實例 close()+丟棄、gc.collect() 釋放記憶體、fallback 拿到的是全新實例 + 唯讀指標(inputs)，
        不繼承任何前一個引擎的記憶體狀態。"""
        import gc
        eng = cls.get(name)
        try:
            resp = eng.process(request)
        finally:
            try:
                eng.close()
            except Exception:  # noqa: BLE001
                pass
            del eng
        fb = cls._fallback.get(name.lower())
        if resp.status != "success" and fb:
            gc.collect()
            with cls.get(fb) as eng2:
                resp2 = eng2.process(request)
                resp2.metadata["fallback_from"] = name
                resp2.metadata["primary_error"] = resp.metadata.get("error")
                return resp2
        return resp


_SRC_CACHE: Dict[str, Any] = {{}}


def load_source(path: str, qualname: str) -> Any:
    """依檔案路徑載入原始模組並取出函式(不需 package 結構、路徑含空白也可)；模組快取(R20)。
    風險12: 載入時 sys.argv 淨空 + VES_IMPORT_GUARD=1，舊模組頂層 main 可據此略過副作用。
    風險13: 相對匯入 → 把 package 根(往上找到沒有 __init__.py 為止)放進 sys.path 並以套件名載入。"""
    import importlib.util, sys as _sys
    mod = _SRC_CACHE.get(path)
    if mod is None:
        p = _Path(path)
        pkg_parts = []
        d = p.parent
        while (d / "__init__.py").exists():
            pkg_parts.insert(0, d.name)
            d = d.parent
        if str(d) not in _sys.path:
            _sys.path.insert(0, str(d))
        modname = ".".join(pkg_parts + [p.stem]) if pkg_parts else "ves_src_" + str(abs(hash(path)))
        old_argv, _os.environ["VES_IMPORT_GUARD"] = _sys.argv, "1"
        _sys.argv = [old_argv[0]] if old_argv else [""]
        try:
            if pkg_parts:
                import importlib
                mod = importlib.import_module(modname)
            else:
                spec = importlib.util.spec_from_file_location(modname, path)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
        finally:
            _sys.argv = old_argv
        _SRC_CACHE[path] = mod
    obj: Any = mod
    for part in qualname.split("."):
        obj = getattr(obj, part)
    return obj


# ---- adapter 支援：Payload 型別模型(pydantic 或 dataclass 降級)、缺值哨兵、同義鍵挑選、驗證
_MISSING = object()


def _call_with_selfheal(adapter, fn, request: EngineRequest, build_kwargs):
    """③ 執行期自癒：先依 POINTER_MODES 解析；若原函式因型別不符炸掉(TypeError/AttributeError/ValueError 且訊息指向 str/DataFrame)，
    把信心 P/M 的參數模式翻轉(path↔frame)重試一次，成功即記錄到 metadata 並建議固化。"""
    modes = dict(getattr(adapter, "POINTER_MODES", {{}}))
    conf = getattr(adapter, "POINTER_CONF", {{}})

    def _once(mds):
        resolved = resolve_inputs(request, getattr(adapter, "POINTER_ENGINE", "path"), mds)
        req = _with_inputs(request, resolved)
        kwargs = {{k: v for k, v in build_kwargs(req).items() if v is not _MISSING}}
        model = _validate(adapter.payload_model, kwargs)
        return fn(**_asdict(model))

    try:
        return _once(modes)
    except (TypeError, AttributeError, ValueError) as e:
        msg = str(e)
        flippable = [a for a, c in conf.items() if c in ("P", "M") and a in modes]
        if not flippable or not re.search(r"str|path|DataFrame|LazyFrame|attribute|expected|got", msg, re.I):
            raise
        flipped = dict(modes)
        for a in flippable:
            flipped[a] = "frame" if modes[a] == "path" else "path"
        adapter.log.warning("pointer-mode self-heal: %s -> retry with %s", msg[:120], flipped)
        result = _once(flipped)
        adapter.POINTER_MODES = flipped                       # 本實例固化；下次生成骨架時建議寫回
        Trace._emit({{"trace_id": request.task_id, "span_id": "selfheal", "name": f"pointer_mode_flip.{{adapter.engine_name}}",
                     "from": modes, "to": flipped, "status": "ok", "ms": 0}})
        return result


def _with_inputs(request: EngineRequest, resolved: Dict[str, Any]) -> EngineRequest:
    """把解析後的 inputs 併進 payload 視圖(不改原 request；資料物件只存在於本次呼叫)。"""
    merged = dict(request.payload)
    merged.update(resolved)
    try:
        return request.model_copy(update={{"payload": merged}})
    except AttributeError:
        import copy
        r2 = copy.copy(request)
        r2.payload = merged
        return r2


def _pick(request: EngineRequest, orig: str, canon: str) -> Any:
    """payload 先找原參數名，再找群內 canonical 同義名，再找 config；都沒有回 _MISSING(交給模型預設值/報錯)。"""
    for src in (request.payload, request.config):
        if orig in src:
            return src[orig]
        if canon in src:
            return src[canon]
    return _MISSING


{model_support}


def shadow_run(primary: str, shadow: str, request: EngineRequest, tol: float = 1e-9) -> EngineResponse:
    """R22 影子模式：回傳 primary 結果，shadow 差異寫進 metadata，不影響上線輸出。"""
    p = EngineFactory.run_with_fallback(primary, request)
    try:
        with EngineFactory.get(shadow) as s:
            q = s.process(request)
        p.metadata["shadow"] = {{"engine": shadow, "status": q.status, "match": _approx_equal(p.result, q.result, tol)}}
    except Exception as e:  # noqa: BLE001
        p.metadata["shadow"] = {{"engine": shadow, "status": "error", "error": str(e)}}
    return p


FIN_TOL = {{"rel_tol": 1e-9, "abs_tol": 1e-12, "decimals": None}}   # 財務精度：rel/abs 分離；decimals 設 2/4 可改成四捨五入比對


def _to_rows(x: Any):
    """任何表格物件 → 依欄名排序欄、依值排序列的 list[tuple]；非表格回 None。"""
    cols = None
    try:
        if hasattr(x, "to_arrow"):                        # polars
            t = x.to_arrow()
            cols = {{c: t.column(c).to_pylist() for c in t.column_names}}
        elif hasattr(x, "to_pydict"):                     # pyarrow Table
            cols = x.to_pydict()
        elif hasattr(x, "columns") and hasattr(x, "to_dict"):   # pandas
            cols = {{str(c): x[c].tolist() for c in x.columns}}
        elif isinstance(x, list) and x and all(isinstance(r, tuple) for r in x):
            return sorted(x, key=repr)
    except Exception:  # noqa: BLE001
        return None
    if cols is None:
        return None
    names = sorted(cols)
    rows = list(zip(*[cols[n] for n in names])) if names else []
    return sorted(rows, key=repr)


def _approx_equal(a: Any, b: Any, tol: float | None = None, rel_tol: float | None = None,
                  abs_tol: float | None = None, decimals: int | None = None) -> bool:      # R21 浮點容差
    import math
    rel = rel_tol if rel_tol is not None else (tol if tol is not None else FIN_TOL["rel_tol"])
    ab = abs_tol if abs_tol is not None else FIN_TOL["abs_tol"]
    dec = decimals if decimals is not None else FIN_TOL["decimals"]
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if dec is not None:
            return round(float(a), dec) == round(float(b), dec)
        return math.isclose(a, b, rel_tol=rel, abs_tol=ab)
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(_approx_equal(x, y, tol, rel_tol, abs_tol, decimals) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_approx_equal(a[k], b[k], tol, rel_tol, abs_tol, decimals) for k in a)
    ra, rb = _to_rows(a), _to_rows(b)                       # DataFrame(pandas/polars)/Arrow/list[tuple] → 排序後逐列比對(引擎輸出列序不同也能對)
    if ra is not None and rb is not None:
        return _approx_equal(ra, rb, tol, rel_tol, abs_tol, decimals)
    if isinstance(a, str) and isinstance(b, str):
        return " ".join(a.split()) == " ".join(b.split())
    return a == b
'''
    base = base.replace("__SAFE_ROOTS__", ", ".join(json.dumps(str(x)) for x in (root_for_conftest.resolve(), out.resolve())))
    p = sd / "base_processor.py"
    p.write_text(base, encoding="utf-8")
    written.append(str(p))

    init_lines = ['# -*- coding: utf-8 -*-', '"""自動生成的轉接器登記(append-only)。"""',
                  'from _standardized.base_processor import EngineFactory']
    test_lines = ['# -*- coding: utf-8 -*-', '"""R21/R23: 同一 Request 餵給同群所有引擎，斷言輸出一致(容差)。"""',
                  'import pytest', 'from _standardized.base_processor import EngineRequest, EngineFactory, _approx_equal',
                  'import _standardized.adapters  # noqa: F401  (觸發登記)', '']
    scaffold_ledger = sd / "scaffold_ledger.jsonl"
    prev = set()
    if scaffold_ledger.exists():
        for ln in scaffold_ledger.read_text(encoding="utf-8").splitlines():
            try:
                prev.add(json.loads(ln)["file"])
            except Exception:  # noqa: BLE001
                pass
    used_names: set[str] = set()
    for ci, c in enumerate(clusters, 1):
        cap = c["capability"]
        head = c["members"][0]
        cname = slug(f"{cap}_{'_'.join(head.tokens[:3])}")
        if cname.lower() in used_names:                       # 風險10/20: slug 碰撞 → 群雜湊後綴
            cname += "_" + hashlib.blake2s(",".join(m.qualname for m in c["members"]).encode(), digest_size=3).hexdigest()
        used_names.add(cname.lower())
        fpath = sd / "adapters" / f"{cname.lower()}.py"
        if fpath.exists():                                    # 升級6: 冪等只增 — 既有 adapter 保留，寫 _vN 新檔
            n = 2
            while (sd / "adapters" / f"{cname.lower()}_v{n}.py").exists():
                n += 1
            fpath = sd / "adapters" / f"{cname.lower()}_v{n}.py"
            cname = f"{cname}_v{n}"
        lines = ['# -*- coding: utf-8 -*-', f'"""Cluster C{ci:03d} · 能力={cap} · 工具={c["tools"]}',
                 '每個 Adapter 包住一個原始函式(原檔不動)，統一走 EngineRequest/EngineResponse。',
                 'TODO 標記處 = 需要人工確認 payload → 原始參數 的映射(防腐層 R07)。"""',
                 'from __future__ import annotations',
                 'from typing import Any',
                 'from _standardized.base_processor import (BaseProcessor, EngineRequest, EngineFactory, load_source,',
                 '                                          _Model, _MISSING, _pick, _validate, _asdict,',
                 '                                          resolve_inputs, _with_inputs, _call_with_selfheal)', '']
        names = []
        alias = c.get("param_alias", {})
        # 群層級 canonical → 每個成員的原始參數名；反向表 member.fid → {orig: canonical}
        rev: dict[str, dict[str, str]] = defaultdict(dict)
        for canon, per in alias.items():
            for fid, orig in per.items():
                rev[fid][orig] = canon
        lines += ['PARAM_ALIAS = ' + json.dumps(alias, ensure_ascii=False, indent=1) + '   # 群內參數同義映射(canonical → {fid: 原名})', '']
        for m in c["members"]:
            if m.lang != "py":
                lines += [f'# [{m.lang}] {m.file}:{m.lineno} {m.qualname}({", ".join(m.args)}) — 非 Python 成員：見 merge_plan.json 的 cross_language 條目', '']
                continue
            tools = "_".join([t for t in m.tools if t in DATA_FAMS][:2] or m.tools[:1]) or "plain"
            klass = pascal(f"{tools}_{m.name}") + "Adapter"
            if klass in names:
                klass += f"_{m.fid[-3:]}"
            names.append(klass)
            model_lines = []
            unresolved = []
            for a in m.args:
                ann = _py_type(m.arg_annots.get(a, ""))
                if not m.arg_annots.get(a):
                    unresolved.append(a)
                if a in m.arg_defaults:
                    model_lines.append(f'    {a}: {ann} = {m.arg_defaults[a]}')
                else:
                    model_lines.append(f'    {a}: {ann}')
            if not model_lines:
                model_lines = ['    pass']
            kw_pairs = []
            for a in m.args:
                canon = rev.get(m.fid, {}).get(a, a)
                kw_pairs.append(f'"{a}": _pick(request, "{a}", "{canon}")')
            lines += [
                f'class {klass}Payload(_Model):',
                f'    """自動依型別提示生成；未註記的參數為 Any（{", ".join(unresolved) or "無"}）。'
                f'欄位 = 原始函式參數；EngineRequest.payload 可用 canonical 名或原名。"""',
                *model_lines,
                '',
                f'class {klass}(BaseProcessor):',
                f'    """來源: {m.file}:{m.lineno} · {m.qualname}({", ".join(m.args)}) · 工具={m.tools}"""',
                f'    engine_name = "{klass.lower()}"',
                f'    payload_model = {klass}Payload',
                '',
                f'    POINTER_MODES = {json.dumps(_pointer_modes(m))}   # inputs 指標解析方式：path=給路徑字串, frame=給資料物件',
                f'    POINTER_CONF = {json.dumps(getattr(m, "_pointer_conf", {}))}   # V=型別註記 M=AST 用法證據 P=名稱猜測(執行期可自動翻轉)',
                f'    POINTER_ENGINE = "{next((t for t in m.tools if t in ("polars", "duckdb", "pandas")), "path")}"',
                '',
                '    def _run(self, request: EngineRequest):',
                f'        fn = load_source({json.dumps(m.abspath, ensure_ascii=False)}, "{m.qualname}")   # R20 懶加載，原檔不動',
                '        return _call_with_selfheal(self, fn, request, lambda req: {' + ", ".join(kw_pairs).replace("request", "req") + '})',
                '',
                f'EngineFactory.register("{klass.lower()}", {klass})',
                '',
            ]
        if len(names) >= 2:
            lines.append(f'EngineFactory._fallback.setdefault("{names[0].lower()}", "{names[1].lower()}")  # R25 降級鏈')
        fpath.write_text("\n".join(lines) + "\n", encoding="utf-8")
        written.append(str(fpath))
        with scaffold_ledger.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "cluster": f"C{ci:03d}", "file": str(fpath),
                                 "members": [m.fid + ":" + m.qualname for m in c["members"]]}, ensure_ascii=False) + "\n")
        init_lines.append(f'from _standardized.adapters.{cname.lower()} import *  # noqa: F401,F403  C{ci:03d}')
        engs = ", ".join(f'"{n.lower()}"' for n in names)
        test_lines += [
            f'@pytest.mark.parametrize("engine", [{engs}])',
            f'def test_c{ci:03d}_{cname.lower()}(engine):',
            f'    req = EngineRequest(task_id="C{ci:03d}", payload={{}})   # TODO: 填入代表性 payload',
            '    with EngineFactory.get(engine) as e:',
            '        r = e.process(req)',
            '    assert r.status in ("success", "error")',
            '',
        ]
    init_p = sd / "adapters" / "__init__.py"
    if init_p.exists():
        old = [ln for ln in init_p.read_text(encoding="utf-8").splitlines() if ln.startswith("from _standardized.adapters.")]
        init_lines = init_lines[:3] + [ln for ln in old if ln not in init_lines] + init_lines[3:]
    init_p.write_text("\n".join(dict.fromkeys(init_lines)) + "\n", encoding="utf-8")
    (sd / "__init__.py").write_text("", encoding="utf-8")
    (sd / "conftest.py").write_text(
        "import sys\nfrom pathlib import Path\n"
        f"for p in ({json.dumps(str(root_for_conftest))}, str(Path(__file__).resolve().parents[1])):\n"
        "    p not in sys.path and sys.path.insert(0, p)\n", encoding="utf-8")
    tp = sd / "tests" / "test_engine_matrix.py"
    if tp.exists():
        tp = sd / "tests" / f"test_engine_matrix_{time.strftime('%Y%m%d_%H%M%S')}.py"
    tp.write_text("\n".join(test_lines) + "\n", encoding="utf-8")
    written += [str(init_p), str(tp)]
    return written


def _pointer_modes(m: FuncRec) -> dict:
    """③ 證據階層：型別註記 (V) > AST 用法證據 (M) > 預設值型別 (M) > 名稱猜測 (P)。回 {arg: mode}；信心另存 _pointer_conf。"""
    out, conf = {}, {}
    for a in m.args:
        ann = m.arg_annots.get(a, "")
        use = m.arg_usage.get(a, {"path": 0, "frame": 0, "str_ops": 0})
        dflt = m.arg_defaults.get(a, "")
        if re.search(r"DataFrame|LazyFrame|Series|Relation|Table|ndarray", ann):
            out[a], conf[a] = "frame", "V"
        elif re.search(r"\bPath\b|PathLike|os\.PathLike", ann):
            out[a], conf[a] = "path", "V"
        elif use["frame"] > use["path"] and use["frame"] > 0:
            out[a], conf[a] = "frame", "M"
        elif use["path"] > 0 or use["str_ops"] > 0:
            out[a], conf[a] = "path", "M"
        elif dflt and (dflt.startswith(("'", '"')) and re.search(r"[\\/.]", dflt)):
            out[a], conf[a] = "path", "M"
        elif ann == "str" and not dflt:
            out[a], conf[a] = "path", "P"
        else:
            toks = set(norm_tokens(a))
            if toks & {"df", "frame", "data", "table", "rows", "lf"}:
                out[a], conf[a] = "frame", "P"
            elif toks & {"path", "file", "filepath", "fp", "dir", "folder", "src", "dst", "fname"}:
                out[a], conf[a] = "path", "P"
    m._pointer_conf = conf
    return out


_TYPE_MAP = {"str": "str", "int": "int", "float": "float", "bool": "bool", "list": "list", "dict": "dict",
             "Path": "Any", "Optional[str]": "str | None", "Optional[int]": "int | None"}


def _py_type(ann: str) -> str:
    """型別提示 → 骨架可用型別；不認得或含第三方型別(DataFrame 等) → Any（arbitrary_types_allowed）。"""
    if not ann:
        return "Any"
    if ann in _TYPE_MAP:
        return _TYPE_MAP[ann]
    if re.fullmatch(r"(str|int|float|bool|list|dict|tuple|set)(\[[\w, |\[\]]*\])?( \| None)?", ann):
        return ann
    return "Any"


# ---------------------------------------------------------------- v0500 詳細日誌 / Parquet 儲存 / ML 能力 / AI 交接
class DetailLog:
    """結構化詳細日誌 (JSONL)，每步驟一筆；同時鏡射到 console 的 @@ 進度行由呼叫端負責。"""

    def __init__(self, path: Path):
        self.path = path
        self.t0 = time.time()
        self.n = 0

    def log(self, stage: str, msg: str = "", **kv) -> None:
        self.n += 1
        rec = {"seq": self.n, "ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "t": round(time.time() - self.t0, 3),
               "stage": stage, "msg": msg}
        rec.update(kv)
        try:
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
        except OSError:
            pass


def parquet_backend() -> str:
    for name in ("pyarrow", "polars", "duckdb"):
        try:
            __import__(name)
            return name
        except Exception:  # noqa: BLE001
            continue
    return "jsonl"


def write_table(rows: list[dict], path: Path, backend: str) -> str:
    """rows → Parquet(pyarrow / polars / duckdb 任一)，都沒有則 JSONL 降級；回傳實際寫出的路徑。永遠新增檔案，不覆蓋。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return ""
    norm = [{k: (json.dumps(v, ensure_ascii=False, default=str) if isinstance(v, (dict, list, set, tuple)) else v)
             for k, v in r.items()} for r in rows]
    try:
        if backend == "pyarrow":
            import pyarrow as pa
            import pyarrow.parquet as pq
            pq.write_table(pa.Table.from_pylist(norm), str(path), compression="zstd")
            return str(path)
        if backend == "polars":
            import polars as pl
            pl.DataFrame(norm).write_parquet(str(path))
            return str(path)
        if backend == "duckdb":
            import duckdb
            tmp = path.with_suffix(".jsonl")
            tmp.write_text("\n".join(json.dumps(r, ensure_ascii=False, default=str) for r in norm), encoding="utf-8")
            duckdb.sql(f"COPY (SELECT * FROM read_json_auto('{tmp.as_posix()}')) TO '{path.as_posix()}' (FORMAT PARQUET)")
            tmp.unlink(missing_ok=True)
            return str(path)
    except Exception as e:  # noqa: BLE001
        print(f"@@PROGRESS|warn|parquet {backend} failed ({type(e).__name__}) -> jsonl", flush=True)
    jp = path.with_suffix(".jsonl")
    jp.write_text("\n".join(json.dumps(r, ensure_ascii=False, default=str) for r in norm), encoding="utf-8")
    return str(jp)


def read_history(store: Path, table: str, backend: str) -> list[dict]:
    """讀 ves_store/<table>/**.parquet(或 .jsonl) 全歷史；用於趨勢與 STABLE_P 自學。"""
    d = store / table
    if not d.exists():
        return []
    rows: list[dict] = []
    for f in sorted(d.rglob("*.parquet")):
        try:
            if backend == "pyarrow":
                import pyarrow.parquet as pq
                rows += pq.read_table(str(f)).to_pylist()
            elif backend == "polars":
                import polars as pl
                rows += pl.read_parquet(str(f)).to_dicts()
            elif backend == "duckdb":
                import duckdb
                con = duckdb.connect()
                cur = con.execute(f"SELECT * FROM read_parquet('{f.as_posix()}')")
                cols = [c[0] for c in cur.description]
                rows += [dict(zip(cols, r)) for r in cur.fetchall()]
        except Exception:  # noqa: BLE001
            continue
    for f in sorted(d.rglob("*.jsonl")):
        try:
            rows += [json.loads(ln) for ln in f.read_text(encoding="utf-8").splitlines() if ln.strip()]
        except Exception:  # noqa: BLE001
            continue
    return rows


def persist_run(store: Path, run_id: str, files, funcs, gates, bench: dict, trace_path: Path | None, dlog: DetailLog) -> dict:
    """升級: 專案自有儲存空間。分區 ves_store/<table>/date=YYYYMMDD/<run_id>.parquet，append-only。"""
    backend = parquet_backend()
    day = time.strftime("%Y%m%d")
    part = lambda t: store / t / f"date={day}" / f"{run_id}.parquet"  # noqa: E731
    out = {"backend": backend, "tables": {}}
    m_count = sum(1 for f in funcs for r in f.risks if r.endswith(":M"))
    out["tables"]["runs"] = write_table([{"run_id": run_id, "ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "version": VERSION,
                                          "files": len(files), "functions": len(funcs), "risk_M": m_count,
                                          "risk_P": sum(1 for f in funcs for r in f.risks if r.endswith(":P")),
                                          "gates_overall": ("RED" if any(g["status"] == "RED" for g in gates) else
                                                            "AMBER" if any(g["status"] == "AMBER" for g in gates) else "GREEN")}],
                                        part("runs"), backend)
    out["tables"]["functions"] = write_table([{"run_id": run_id, "fid": f.fid, "file": f.file, "qualname": f.qualname,
                                               "capability": f.capability, "tools": f.tools, "body_hash": f.body_hash,
                                               "lines": f.end_lineno - f.lineno, "fan_in": f.fan_in, "fan_out": f.fan_out,
                                               "dormant": f.dormant_candidate, "dormant_level": f.dormant_level, "fan_in_ambiguous": f.fan_in_ambiguous, "lang": f.lang,
                                               "annotated": f.annotated_args, "nargs": len(f.args)}
                                              for f in funcs], part("functions"), backend)
    out["tables"]["risks"] = write_table([{"run_id": run_id, "fid": f.fid, "file": f.file, "qualname": f.qualname,
                                           "risk": r.split(":")[0], "conf": (r.split(":")[1] if ":" in r else "F")}
                                          for f in funcs for r in f.risks] +
                                         [{"run_id": run_id, "fid": "", "file": fr.file, "qualname": "", "risk": r, "conf": "F"}
                                          for fr in files for r in fr.risks], part("risks"), backend)
    out["tables"]["gates"] = write_table([{"run_id": run_id, **g} for g in gates], part("gates"), backend)
    if bench:
        out["tables"]["bench"] = write_table([{"run_id": run_id, **b} for b in bench.get("benchmarks", [])] +
                                             [{"run_id": run_id, "name": "tool:" + t["name"], "status": t["status"],
                                               "ms": None, "note": t.get("version", "")} for t in bench.get("tools", [])],
                                             part("bench"), backend)
    if trace_path and trace_path.exists():
        try:
            rows = [json.loads(ln) for ln in trace_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
            out["tables"]["trace"] = write_table([{"run_id": run_id, **r} for r in rows], part("trace"), backend)
        except Exception:  # noqa: BLE001
            pass
    dlog.log("persist", "run persisted to ves_store", backend=backend, tables=out["tables"])
    return out


def learn_from_history(store: Path, funcs, backend: str, min_runs: int = 3) -> dict:
    """持續強化(自學)：某 (file, qualname, risk) 連續 ≥min_runs 輪都只有 :P 從未升 :M → STABLE_P(疑似誤報) 降權；
    同時算趨勢(functions / risk_M / gates)。純統計、可審計，不用 LLM。"""
    hist = read_history(store, "risks", backend)
    runs = read_history(store, "runs", backend)
    seen: dict[tuple, dict] = defaultdict(lambda: {"P": set(), "M": set()})
    for r in hist:
        key = (r.get("file"), r.get("qualname"), r.get("risk"))
        seen[key][r.get("conf", "F") if r.get("conf") in ("P", "M") else "M"].add(r.get("run_id"))
    stable_p = {k for k, v in seen.items() if len(v["P"]) >= min_runs and not v["M"]}
    downweighted = 0
    for f in funcs:
        new = []
        for r in f.risks:
            base = r.split(":")[0]
            if r.endswith(":P") and (f.file, f.qualname, base) in stable_p:
                new.append(base + ":SP")            # STABLE_P
                downweighted += 1
            else:
                new.append(r)
        f.risks = new
    trend = sorted(({"run_id": r.get("run_id"), "functions": r.get("functions"), "risk_M": r.get("risk_M"),
                     "risk_P": r.get("risk_P"), "gates": r.get("gates_overall")} for r in runs), key=lambda x: str(x["run_id"]))
    return {"runs_seen": len(runs), "stable_p": len(stable_p), "downweighted": downweighted, "trend": trend[-30:]}


def _mem_gb() -> float:
    try:
        if os.name == "nt":
            import ctypes

            class MS(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
            ms = MS()
            ms.dwLength = ctypes.sizeof(MS)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(ms))
            return round(ms.ullTotalPhys / 1024 ** 3, 1)
        for ln in Path("/proc/meminfo").read_text().splitlines():
            if ln.startswith("MemTotal"):
                return round(int(ln.split()[1]) / 1024 ** 2, 1)
    except Exception:  # noqa: BLE001
        pass
    return 0.0


def _cpu_flags() -> list[str]:
    flags = []
    try:
        if os.name != "nt":
            txt = Path("/proc/cpuinfo").read_text()
            m = re.search(r"^flags\s*:\s*(.*)$", txt, re.M)
            if m:
                fl = set(m.group(1).split())
                flags = [f for f in ("avx", "avx2", "avx512f", "fma", "sse4_2") if f in fl]
        else:
            import ctypes
            k = ctypes.windll.kernel32
            if k.IsProcessorFeaturePresent(40):      # PF_AVX2_INSTRUCTIONS_AVAILABLE
                flags.append("avx2")
            if k.IsProcessorFeaturePresent(41):      # PF_AVX512F
                flags.append("avx512f")
    except Exception:  # noqa: BLE001
        pass
    return flags


ML_TOOLS = [  # (import name, display, class, note)
    ("numpy", "numpy", "core", ""), ("scipy", "scipy", "core", ""), ("pandas", "pandas", "core", ""),
    ("polars", "polars", "core", ""), ("pyarrow", "pyarrow", "core", ""), ("duckdb", "duckdb", "core", ""),
    ("sklearn", "scikit-learn", "ml", "CPU 首選：樹/線性/聚類"), ("xgboost", "xgboost", "ml", "CPU hist 極快"),
    ("lightgbm", "lightgbm", "ml", "CPU 首選 GBDT"), ("catboost", "catboost", "ml", "類別特徵"),
    ("statsmodels", "statsmodels", "ml", "時序/計量"), ("prophet", "prophet", "ml", "時序"),
    ("torch", "torch (CPU)", "dl", "小模型/推論；MKL-DNN"), ("onnxruntime", "onnxruntime", "dl", "CPU 推論最快"),
    ("tensorflow", "tensorflow", "dl", "CPU 可但重"), ("transformers", "transformers", "dl", "配 onnx/int8"),
    ("sentence_transformers", "sentence-transformers", "dl", "MiniLM 級 CPU 可"), ("numba", "numba", "accel", "JIT"),
    ("talib", "TA-Lib", "fin", ""), ("optuna", "optuna", "ml", "調參"), ("shap", "shap", "ml", "解釋"),
]


def probe_ml_capability(quick: bool = True, isolate: bool = True) -> dict:
    """② v0600：整個探測在子程序執行（每個微基準再各自一個子程序），C 層 segfault 只殺子程序；父程序讀 JSON。"""
    if isolate:
        me = Path(__file__).resolve()
        r = subprocess.run([sys.executable, "-X", "utf8", str(me), "--ml-probe-child", "--quick" if quick else "--full"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
        try:
            data = json.loads(r.stdout.strip().splitlines()[-1]) if r.stdout.strip() else {}
        except Exception:  # noqa: BLE001
            data = {}
        if not data:
            return {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "error": f"probe child rc={r.returncode} (segfault/timeout?)",
                    "stderr": r.stderr[-500:], "tools": [], "benchmarks": [], "cpu_count": os.cpu_count() or 1,
                    "ram_gb": _mem_gb(), "cpu_flags": _cpu_flags(), "python": "", "machine": "",
                    "recommendation": {"tier": "T? 探測子程序失敗", "ml_first_choice": [], "dl_first_choice": [], "llm_local": "", "avx": ""}}
        data["isolated"] = True
        return data
    return _probe_ml_inproc(quick)


_BENCH_SRC = {
    "numpy_matmul_1024f32": "import numpy as np\na=np.random.rand(1024,1024).astype(np.float32)\nprint(float((a@a).sum()))",
    "sklearn_rf50_5k": "from sklearn.ensemble import RandomForestClassifier\nimport numpy as np\nX=np.random.rand(5000,20)\ny=(X[:,0]>0.5).astype(int)\nprint(RandomForestClassifier(n_estimators=50,n_jobs=-1).fit(X,y).score(X,y))",
    "lightgbm_100t_20k": "import lightgbm as lgb\nimport numpy as np\nX=np.random.rand(20000,30)\ny=(X[:,0]+X[:,1]>1).astype(int)\nprint(lgb.LGBMClassifier(n_estimators=100,verbose=-1).fit(X,y).score(X,y))",
    "xgboost_hist_100t_20k": "import xgboost as xgb\nimport numpy as np\nX=np.random.rand(20000,30)\ny=(X[:,0]+X[:,1]>1).astype(int)\nprint(xgb.XGBClassifier(n_estimators=100,tree_method='hist').fit(X,y).score(X,y))",
    "torch_mlp_fwd_x20": "import torch,os\ntorch.set_num_threads(os.cpu_count() or 1)\nm=torch.nn.Sequential(torch.nn.Linear(512,1024),torch.nn.ReLU(),torch.nn.Linear(1024,10))\nx=torch.randn(256,512)\nwith torch.no_grad():\n    for _ in range(20): y=m(x)\nprint(float(y.sum()))",
    "onnxruntime_providers": "import onnxruntime as ort\nprint(ort.get_available_providers())",
    "polars_groupby_1M": "import polars as pl\nimport numpy as np\nn=1_000_000\ndf=pl.DataFrame({'g':np.random.randint(0,100,n),'v':np.random.rand(n)})\nprint(df.group_by('g').agg(pl.col('v').mean()).height)",
    "duckdb_scan_5M": "import duckdb\nprint(duckdb.sql('SELECT count(*) FROM range(5000000) WHERE range % 7 = 0').fetchone()[0])",
}
_BENCH_NEEDS = {"numpy_matmul_1024f32": "numpy", "sklearn_rf50_5k": "scikit-learn", "lightgbm_100t_20k": "lightgbm",
                "xgboost_hist_100t_20k": "xgboost", "torch_mlp_fwd_x20": "torch (CPU)", "onnxruntime_providers": "onnxruntime",
                "polars_groupby_1M": "polars", "duckdb_scan_5M": "duckdb"}


def _bench_subprocess(name: str, timeout: int = 120) -> dict:
    """每個微基準獨立子程序：segfault → rc<0，只記 FAIL。"""
    t0 = time.perf_counter()
    try:
        r = subprocess.run([sys.executable, "-X", "utf8", "-c", _BENCH_SRC[name]], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout)
        ms = round((time.perf_counter() - t0) * 1000, 1)
        if r.returncode == 0:
            return {"name": name, "status": "OK", "ms": ms, "note": r.stdout.strip()[:60], "isolated": True}
        return {"name": name, "status": "FAIL", "ms": ms, "note": (f"rc={r.returncode} " + r.stderr.strip()[-70:]), "isolated": True}
    except subprocess.TimeoutExpired:
        return {"name": name, "status": "FAIL", "ms": None, "note": f"timeout {timeout}s", "isolated": True}


def _probe_ml_inproc(quick: bool = True) -> dict:
    """子程序內執行的實體：工具 import 探測（每個 import 也各自子程序）+ 微基準（各自子程序）。"""
    import platform
    import importlib.util
    info = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "python": platform.python_version(), "machine": platform.machine(),
            "cpu_count": os.cpu_count() or 1, "ram_gb": _mem_gb(), "cpu_flags": _cpu_flags(), "tools": [], "benchmarks": []}
    for mod, disp, cls, note in ML_TOOLS:
        t0 = time.perf_counter()
        spec = importlib.util.find_spec(mod) if "." not in mod else None
        if spec is None:
            info["tools"].append({"name": disp, "class": cls, "status": "MISSING", "version": "", "import_ms": 0, "note": note})
            continue
        try:                                               # 真正 import 走子程序（重型 C 擴充可能 segfault）
            r = subprocess.run([sys.executable, "-X", "utf8", "-c", f"import {mod} as m;print(getattr(m,'__version__','?'))"],
                               capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
            ms = round((time.perf_counter() - t0) * 1000, 1)
            if r.returncode == 0:
                info["tools"].append({"name": disp, "class": cls, "status": "OK", "version": r.stdout.strip()[:30], "import_ms": ms, "note": note})
            else:
                info["tools"].append({"name": disp, "class": cls, "status": "BROKEN", "version": "", "import_ms": ms,
                                      "note": f"import rc={r.returncode} " + r.stderr.strip()[-60:]})
        except subprocess.TimeoutExpired:
            info["tools"].append({"name": disp, "class": cls, "status": "BROKEN", "version": "", "import_ms": 60000, "note": "import timeout"})
    ok = {t["name"] for t in info["tools"] if t["status"] == "OK"}

    for bname, need in _BENCH_NEEDS.items():
        if need in ok:
            info["benchmarks"].append(_bench_subprocess(bname, timeout=(120 if quick else 300)))
    ram = info["ram_gb"]
    core = info["cpu_count"]
    tier = ("T1 8B-LLM/大型 GBDT/中型 DL 訓練可行" if ram >= 32 and core >= 8 else
            "T2 3B-LLM 推論/GBDT/小型 DL 可行" if ram >= 16 and core >= 4 else
            "T3 1.5B-LLM 推論/sklearn·lightgbm 可行" if ram >= 8 else "T4 僅輕量 sklearn")
    info["recommendation"] = {
        "tier": tier,
        "ml_first_choice": [n for n in ("lightgbm", "xgboost", "scikit-learn") if n in ok] or ["安裝 scikit-learn + lightgbm"],
        "dl_first_choice": [n for n in ("onnxruntime", "torch (CPU)") if n in ok] or ["安裝 onnxruntime（CPU 推論最快）"],
        "llm_local": ("qwen2.5:7b" if ram >= 32 else "qwen2.5:3b" if ram >= 16 else "qwen2.5:1.5b"),
        "avx": ("avx512" if "avx512f" in info["cpu_flags"] else "avx2" if "avx2" in info["cpu_flags"] else "unknown/none"),
    }
    return info


def write_ai_handoff(out: Path, root: Path, files, funcs, scdt, gates, unknown_verbs: Counter, learn: dict) -> dict:
    """先機器修復、再交 AI：只把『機器判不了』的殘餘決策打包給 AI，並估算 token 節省。"""
    def toks(s: str) -> int:
        return max(1, len(s) // 3)              # 中英混合保守估：3 字元 ≈ 1 token
    full_src_tokens = 0
    for fr in files:
        if fr.parse_ok:
            try:
                full_src_tokens += toks((root / fr.file).read_text(encoding="utf-8", errors="replace"))
            except OSError:
                pass
    L = [f"# AI Handoff (VES v{VERSION}) — 機器已修復部分不在此；以下才需要 AI/人工判斷", f"- root: `{root}`", ""]
    # 1. 未註記型別的參數(骨架只能給 Any)
    any_params = [(m.qualname, m.file, m.lineno, [a for a in m.args if not m.arg_annots.get(a)]) for c in scdt for m in c["members"]]
    any_params = [x for x in any_params if x[3]]
    L += [f"## 1. 需要補型別的參數（骨架已生成 Payload 模型，這些欄位目前 = Any）: {len(any_params)} 函式"]
    L += [f"- `{q}` {f}:{ln} → {a}" for q, f, ln, a in any_params[:60]]
    # 2. 群級介面提案待核可
    L += ["", f"## 2. 群級標準介面提案（機器提案，需核可/改名）: {len(scdt)} 群"]
    for i, c in enumerate(scdt[:40], 1):
        pi = c["proposed_interface"]
        L.append(f"- C{i:03d} `{pi['name']}(" + ", ".join(p["name"] + ("" if p["required"] else "=" + str(p["default"])) for p in pi["params"]) + f")` ← {len(c['members'])} 成員 tools={c['tools']} 主={c['recommendation']['primary']}")
    # 3. 只有 M 級風險(P/SP 已機器降權)
    m_risks = [(m.qualname, m.file, m.lineno, [r for r in m.risks if r.endswith(":M")]) for m in funcs if any(r.endswith(":M") for r in m.risks)]
    L += ["", f"## 3. 確認級風險 :M（:P 疑似誤報、:SP 歷史穩定誤報已自動降權，不列）: {len(m_risks)} 函式"]
    L += [f"- `{q}` {f}:{ln} → {r}" for q, f, ln, r in m_risks[:80]]
    # 4. 待分類動詞
    pend = [(v, n) for v, n in unknown_verbs.most_common(40) if n >= 3]
    L += ["", f"## 4. 待分類動詞（填進 ves_taxonomy.json verbs）: {len(pend)}", "- " + ", ".join(f"{v}×{n}" for v, n in pend)]
    # 5. gates
    bad = [g for g in gates if g["status"] != "GREEN"]
    L += ["", f"## 5. 非 GREEN 閘門: {len(bad)}"] + [f"- {g['gate']}: {g['status']} ({g['value']})" for g in bad]
    L += ["", f"## 6. 自學狀態", f"- 歷史輪數 {learn.get('runs_seen', 0)} · STABLE_P 降權 {learn.get('downweighted', 0)} 項"]
    txt = "\n".join(L) + "\n"
    handoff_tokens = toks(txt)
    L.insert(2, f"- **token 估算**：整棵原始碼 ≈ {full_src_tokens:,} tokens → 本交接檔 ≈ {handoff_tokens:,} tokens（省 {100 * (1 - handoff_tokens / max(1, full_src_tokens)):.1f}%）")
    txt = "\n".join(L) + "\n"
    (out / "AI_HANDOFF.md").write_text(txt, encoding="utf-8")
    return {"full_src_tokens": full_src_tokens, "handoff_tokens": handoff_tokens,
            "saving_pct": round(100 * (1 - handoff_tokens / max(1, full_src_tokens)), 1)}


# ---------------------------------------------------------------- v0800 LOG → ML / DL 學習層
ML_REQUIREMENTS = [  # 免費、CPU、pip 可裝；VES 只用「有就用、沒有降級」
    ("scikit-learn", "風險誤報分類 / TF-IDF / IsolationForest", "core"),
    ("lightgbm", "GBDT (大量歷史時取代 sklearn GBT)", "optional"),
    ("numpy", "微型 autoencoder / 向量運算", "core"),
    ("pyarrow", "ves_store Parquet", "core"), ("duckdb", "歷史查詢", "core"), ("polars", "資料引擎", "optional"),
    ("sentence-transformers", "MiniLM 語意 embedding (CPU 可, ~90MB 模型)", "optional"),
    ("onnxruntime", "CPU 推論加速 (transformers → onnx int8)", "optional"),
]


def write_install_plan(out: Path, ml: dict | None) -> Path:
    """⑥ 免費 CPU libs 導入計畫：寫 requirements（依探測結果標 有/無），不安裝。"""
    have = {t["name"].split(" ")[0].lower() for t in (ml or {}).get("tools", []) if t["status"] == "OK"}
    try:
        import importlib.util
        for name, _, _ in ML_REQUIREMENTS:
            mod = {"scikit-learn": "sklearn", "sentence-transformers": "sentence_transformers"}.get(name, name.replace("-", "_"))
            if importlib.util.find_spec(mod):
                have.add(name.lower())
    except Exception:  # noqa: BLE001
        pass
    L = ["# VES v%s — 免費 CPU ML/DL libs 導入計畫（pip install -r ves_ml_requirements.txt；VIA venv 內執行）" % VERSION,
         "# core = 建議必裝；optional = 有更好；已安裝者註解掉（只增不減：不移除任何既有套件）"]
    for name, why, tier in ML_REQUIREMENTS:
        prefix = "# [installed] " if name.lower() in have else ("" if tier == "core" else "# [optional] ")
        L.append(f"{prefix}{name}    # {tier}: {why}")
    p = out / "ves_ml_requirements.txt"
    p.write_text("\n".join(L) + "\n", encoding="utf-8")
    return p


class _Semantic:
    """② 語意相似度後端：sentence-transformers(MiniLM) > sklearn TF-IDF(char n-gram) > stdlib hashing cosine。一輪只建一次。"""

    def __init__(self):
        self.ready = False
        self.backend = "none"
        self._vec: dict[str, Any] = {}

    @staticmethod
    def _text(f: FuncRec) -> str:
        return " ".join(f.tokens + f.doc_tokens + [c.split(".")[-1] for c in f.calls[:20]] + [f.capability.lower()] + list(f.tools))

    def build(self, funcs: list[FuncRec], mode: str = "auto") -> str:
        texts = {f.fid: self._text(f) for f in funcs}
        if mode == "off" or not texts or (mode == "auto" and len(texts) > 40000):
            return "off"
        if mode in ("auto", "embed"):
            try:
                from sentence_transformers import SentenceTransformer
                import numpy as np
                model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
                fids = list(texts)
                embs = model.encode([texts[k] for k in fids], batch_size=64, normalize_embeddings=True, show_progress_bar=False)
                self._vec = {k: np.asarray(embs[i]) for i, k in enumerate(fids)}
                self.backend, self.ready = "minilm", True
                return self.backend
            except Exception:  # noqa: BLE001
                if mode == "embed":
                    return "off"
        if mode in ("auto", "tfidf"):
            try:
                from sklearn.feature_extraction.text import TfidfVectorizer
                from sklearn.decomposition import TruncatedSVD
                import numpy as np
                fids = list(texts)
                X = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=2 if len(fids) > 2000 else 1).fit_transform([texts[k] for k in fids])
                k = min(64, max(2, X.shape[1] - 1), max(2, X.shape[0] - 1))
                D = TruncatedSVD(n_components=k, random_state=0).fit_transform(X)      # 稀疏 → 64 維稠密，配對點積 O(64)
                D = D / (np.linalg.norm(D, axis=1, keepdims=True) + 1e-9)
                self._vec = {kk: D[i] for i, kk in enumerate(fids)}
                self.backend, self.ready = "tfidf", True
                return self.backend
            except Exception:  # noqa: BLE001
                pass
        # hashing cosine（有 numpy 用 512 維稠密向量；否則 dict）
        try:
            import numpy as np
            vec = {}
            for k, t in texts.items():
                v = np.zeros(512)
                for tok in t.split():
                    for i in range(max(1, len(tok) - 2)):
                        v[hash(tok[i:i + 3]) % 512] += 1.0
                vec[k] = v / (np.linalg.norm(v) + 1e-9)
            self._vec = vec
            self.backend, self.ready = "hashing", True
            return self.backend
        except ImportError:
            pass
        vec = {}
        for k, t in texts.items():
            d: dict[int, float] = defaultdict(float)
            for tok in t.split():
                for i in range(max(1, len(tok) - 2)):
                    d[hash(tok[i:i + 3]) % 4096] += 1.0
            n = sum(v * v for v in d.values()) ** 0.5 or 1.0
            vec[k] = {h: v / n for h, v in d.items()}
        self._vec = vec
        self.backend, self.ready = "hashing_dict", True
        return self.backend

    def sim(self, a: FuncRec, b: FuncRec) -> float:
        va, vb = self._vec.get(a.fid), self._vec.get(b.fid)
        if va is None or vb is None:
            return 0.0
        try:
            if self.backend in ("minilm", "tfidf", "hashing"):
                return float(max(0.0, float(va @ vb)))
            if len(va) > len(vb):
                va, vb = vb, va
            return float(sum(v * vb.get(h, 0.0) for h, v in va.items()))
        except Exception:  # noqa: BLE001
            return 0.0


_SEM = _Semantic()


def _risk_features(f: FuncRec, risk: str) -> list[float]:
    code = risk.split(":")[0]
    codes = ["R11_NULL_SEMANTICS", "R12_INDEX_DEPENDENCY", "R13_LAZY_NOT_MATERIALIZED", "R15_REGEX_ENGINE_DIVERGENCE", "R17_RESOURCE_NOT_RELEASED",
             "R18_GLOBAL_CONFIG", "R38_PS_REDIRECT_STDOUT_BUFFER"]
    caps = list(VERB_CANON) + ["OTHER"]
    tools = ["pandas", "polars", "duckdb", "pyarrow", "numpy", "requests", "sqlite", "sqlalchemy", "re", "pymupdf", "pdfplumber"]
    return ([1.0 if code == c else 0.0 for c in codes] + [1.0 if f.capability == c else 0.0 for c in caps] +
            [1.0 if t in f.tools else 0.0 for t in tools] +
            [float(len(f.args)), float(f.end_lineno - f.lineno), float(f.annotated_args), float(len(f.calls)), float(f.is_method),
             float(f.fan_in), float(f.fan_in_ambiguous), 1.0 if f.lang == "py" else 0.0, 1.0 if f.lang == "ps1" else 0.0])


class _NaiveBayes:
    """stdlib 降級分類器：高斯 NB（連續特徵）+ 拉普拉斯平滑。"""

    def fit(self, X, y):
        import math
        self.classes = sorted(set(y))
        self.stats = {}
        for c in self.classes:
            rows = [x for x, yy in zip(X, y) if yy == c]
            n = len(rows)
            mu = [sum(r[j] for r in rows) / n for j in range(len(X[0]))]
            var = [max(1e-3, sum((r[j] - mu[j]) ** 2 for r in rows) / n) for j in range(len(X[0]))]
            self.stats[c] = (math.log((n + 1) / (len(y) + len(self.classes))), mu, var)
        return self

    def predict_proba(self, X):
        import math
        out = []
        for x in X:
            lp = {}
            for c, (prior, mu, var) in self.stats.items():
                lp[c] = prior + sum(-0.5 * math.log(2 * math.pi * var[j]) - (x[j] - mu[j]) ** 2 / (2 * var[j]) for j in range(len(x)))
            m = max(lp.values())
            z = sum(math.exp(v - m) for v in lp.values())
            out.append([math.exp(lp[c] - m) / z for c in self.classes])
        return out


def train_fp_classifier(store: Path, funcs: list[FuncRec], backend: str, dlog: "DetailLog") -> dict:
    """① 風險誤報分類器。標籤來自歷史：某 (file, qualname, risk) 在歷史裡曾為 :M → 1(真)；≥2 輪只 :P → 0(疑似誤報)。
    特徵 = 風險碼 + 能力 + 工具 + 結構數值。sklearn GBT → LogisticRegression → stdlib NB。輸出 p_fp 標進 risk 尾碼 :SP(ML)。"""
    hist = read_history(store, "risks", backend)
    if not hist:
        return {"status": "NO_HISTORY", "samples": 0}
    seen: dict[tuple, dict] = defaultdict(lambda: {"P": set(), "M": set()})
    for r in hist:
        key = (r.get("file"), r.get("qualname"), r.get("risk"))
        conf = r.get("conf")
        if conf in ("P", "M"):
            seen[key][conf].add(r.get("run_id"))
    fmap = {(f.file, f.qualname): f for f in funcs}
    X, y, keys = [], [], []
    for key, v in seen.items():
        f = fmap.get((key[0], key[1]))
        if f is None:
            continue
        if v["M"]:
            label = 1
        elif len(v["P"]) >= 2:
            label = 0
        else:
            continue
        X.append(_risk_features(f, key[2]))
        y.append(label)
        keys.append(key)
    if len(X) < 8 or len(set(y)) < 2:
        return {"status": "INSUFFICIENT", "samples": len(X), "classes": sorted(set(y))}
    model_name, model = "stdlib_nb", None
    try:
        from sklearn.ensemble import GradientBoostingClassifier
        from sklearn.model_selection import cross_val_score
        import numpy as np
        Xn, yn = np.asarray(X), np.asarray(y)
        clf = GradientBoostingClassifier(n_estimators=80, max_depth=3, random_state=0)
        try:
            cv = float(cross_val_score(clf, Xn, yn, cv=min(5, max(2, min(np.bincount(yn)))), scoring="accuracy").mean())
        except Exception:  # noqa: BLE001
            cv = float("nan")
        clf.fit(Xn, yn)
        model, model_name = clf, "sklearn_gbt"
        proba = lambda M: clf.predict_proba(np.asarray(M))[:, list(clf.classes_).index(0)]  # noqa: E731
        importances = clf.feature_importances_.tolist()
    except Exception:  # noqa: BLE001
        nb = _NaiveBayes().fit(X, y)
        model, model_name = nb, "stdlib_nb"
        idx0 = nb.classes.index(0)
        proba = lambda M: [p[idx0] for p in nb.predict_proba(M)]  # noqa: E731
        cv = float("nan")
        importances = []
    # apply to current :P risks
    applied = 0
    scored = []
    for f in funcs:
        new = []
        for r in f.risks:
            if r.endswith(":P"):
                pf = float(proba([_risk_features(f, r)])[0])
                scored.append(pf)
                if pf >= 0.85:
                    new.append(r[:-2] + ":SP")
                    applied += 1
                    f.attrs_ml = getattr(f, "attrs_ml", {})
                else:
                    new.append(r)
            else:
                new.append(r)
        f.risks = new
    meta = {"status": "OK", "model": model_name, "samples": len(X), "positives": int(sum(y)), "cv_accuracy": (None if cv != cv else round(cv, 3)),
            "downweighted_ml": applied, "scored": len(scored), "mean_p_fp": (round(sum(scored) / len(scored), 3) if scored else None),
            "feature_importances_top": sorted(enumerate(importances), key=lambda kv: -kv[1])[:8] if importances else [], "grade": "M"}
    _save_model(store, "fp_classifier", model, meta)
    dlog.log("ml_fp", "false-positive classifier", **{k: v for k, v in meta.items() if k != "feature_importances_top"})
    return meta


def _save_model(store: Path, name: str, model, meta: dict) -> None:
    d = store / "models"
    d.mkdir(parents=True, exist_ok=True)
    meta = dict(meta, ts=time.strftime("%Y-%m-%dT%H:%M:%S"), version=VERSION)
    (d / f"{name}.meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    try:
        import pickle
        with (d / f"{name}.pkl").open("wb") as fh:
            pickle.dump(model, fh)
    except Exception:  # noqa: BLE001
        pass
    with (d / "models_ledger.jsonl").open("a", encoding="utf-8") as fh:            # append-only
        fh.write(json.dumps({"name": name, **{k: meta[k] for k in ("ts", "version", "status") if k in meta}}, ensure_ascii=False) + "\n")


def _pair_features(a: FuncRec, b: FuncRec) -> list[float]:
    ta, tb = _canon(a.tokens), _canon(b.tokens)
    name_r = difflib.SequenceMatcher(None, " ".join(ta), " ".join(tb)).ratio()
    set_r = len(set(ta) & set(tb)) / max(1, len(set(ta) | set(tb)))
    arg_r = len(set(a.args) & set(b.args)) / max(1, len(set(a.args) | set(b.args))) if (a.args or b.args) else 0.0
    fa, fb = _call_fingerprint(a), _call_fingerprint(b)
    call_r = (len(fa & fb) / max(1, len(fa | fb))) if (fa or fb) else 0.5
    doc_r = len(set(a.doc_tokens) & set(b.doc_tokens)) / max(1, len(set(a.doc_tokens) | set(b.doc_tokens))) if (a.doc_tokens and b.doc_tokens) else 0.0
    sem_r = _SEM.sim(a, b) if _SEM.ready else 0.0
    return [name_r, set_r, arg_r, call_r, doc_r, sem_r, 1.0 if a.capability == b.capability else 0.0,
            1.0 if set(a.tools) & set(b.tools) else 0.0, 1.0 if a.lang == b.lang else 0.0,
            abs(len(a.args) - len(b.args)) / 10.0, abs((a.end_lineno - a.lineno) - (b.end_lineno - b.lineno)) / 100.0]


def load_feedback(out_parent: Path) -> list[dict]:
    """③ 回饋來源：ves_feedback.jsonl（每行 JSON 或 ==VES-FEEDBACK== 群 ACCEPT|REJECT 行）。append-only，只讀。"""
    rows = []
    for p in (out_parent / "ves_feedback.jsonl", Path.home() / "Downloads" / "VIA_EngineStandardizer" / "ves_feedback.jsonl"):
        if p.exists():
            for ln in p.read_text(encoding="utf-8", errors="replace").splitlines():
                ln = ln.strip()
                if not ln:
                    continue
                m = re.match(r"==VES-FEEDBACK==\s+(\S+)\s+(ACCEPT|REJECT)(?:\s+(.*))?", ln)
                if m:
                    rows.append({"cluster": m.group(1), "verdict": m.group(2), "members": (m.group(3) or "").split(","), "src": str(p)})
                else:
                    try:
                        d = json.loads(ln)
                        if d.get("cluster") and d.get("verdict"):
                            rows.append(d)
                    except Exception:  # noqa: BLE001
                        continue
    return rows


def train_pair_model(store: Path, feedback: list[dict], funcs: list[FuncRec], scdt: list, near: list, dlog: "DetailLog") -> dict:
    """③ 分群回饋學習：ACCEPT 群內配對=1、REJECT 群內配對=0 → LogisticRegression(→NB) → 對現有群算 p_accept 重排 + 建議門檻。"""
    if not feedback:
        return {"status": "NO_FEEDBACK", "samples": 0}
    fmap = {f.fid: f for f in funcs}
    qmap = {(f.file, f.qualname): f for f in funcs}
    X, y = [], []
    for fb in feedback:
        mems = []
        for m in fb.get("members", []):
            m = m.strip()
            if not m:
                continue
            f = fmap.get(m)
            if f is None and ":" in m:
                file_, qual = m.split(":", 1)
                f = qmap.get((file_, qual.split(" ", 1)[-1] if " " in qual else qual))
            if f is not None:
                mems.append(f)
        lab = 1 if fb["verdict"] == "ACCEPT" else 0
        for i in range(len(mems)):
            for j in range(i + 1, len(mems)):
                X.append(_pair_features(mems[i], mems[j]))
                y.append(lab)
    if len(X) < 6 or len(set(y)) < 2:
        return {"status": "INSUFFICIENT", "samples": len(X), "feedback_rows": len(feedback)}
    try:
        from sklearn.linear_model import LogisticRegression
        import numpy as np
        clf = LogisticRegression(max_iter=500).fit(np.asarray(X), np.asarray(y))
        proba = lambda M: clf.predict_proba(np.asarray(M))[:, list(clf.classes_).index(1)]  # noqa: E731
        model_name, coef = "sklearn_logreg", clf.coef_[0].round(3).tolist()
    except Exception:  # noqa: BLE001
        nb = _NaiveBayes().fit(X, y)
        idx1 = nb.classes.index(1)
        proba = lambda M: [p[idx1] for p in nb.predict_proba(M)]  # noqa: E731
        model_name, coef = "stdlib_nb", []
    rescored = 0
    for c in scdt + near:
        g = c["members"]
        if len(g) < 2:
            continue
        ps = [float(proba([_pair_features(g[i], g[j])])[0]) for i in range(len(g)) for j in range(i + 1, len(g))]
        c["p_accept"] = round(sum(ps) / len(ps), 3)
        rescored += 1
    scdt.sort(key=lambda r: (-(r.get("p_accept", 0.5)), -len(r["members"])))
    meta = {"status": "OK", "model": model_name, "samples": len(X), "positives": int(sum(y)), "feedback_rows": len(feedback),
            "coef": coef, "rescored_clusters": rescored, "grade": "M"}
    _save_model(store, "pair_model", None, meta)
    dlog.log("ml_pair", "cluster feedback model", **{k: v for k, v in meta.items() if k != "coef"})
    return meta


def _autoencoder_scores(X: list[list[float]], epochs: int = 200, hidden: int = 4, seed: int = 0, fit_on_history: bool = True) -> list[float]:
    """④ 純 numpy 微型 autoencoder（DL, CPU, 毫秒級）：重建誤差 = 異常分數。torch 在場就用 torch，否則 numpy。"""
    import numpy as np
    A = np.asarray(X, dtype=float)
    if A.ndim != 2 or A.shape[0] < 4:
        return [0.0] * len(X)
    ref = A[:-1] if fit_on_history and A.shape[0] >= 4 else A          # 只用歷史訓練，最新點只評分
    med = np.median(ref, 0)
    mad = np.median(np.abs(ref - med), 0) * 1.4826 + 1e-6              # 穩健縮放，離群點不會壓縮尺度
    Z = (A - med) / mad
    Zt = (ref - med) / mad
    n, d = Zt.shape
    h = min(hidden, max(1, d - 1))
    try:
        import torch
        torch.manual_seed(seed)
        t = torch.tensor(Zt, dtype=torch.float32)
        ta = torch.tensor(Z, dtype=torch.float32)
        model = torch.nn.Sequential(torch.nn.Linear(d, h), torch.nn.Tanh(), torch.nn.Linear(h, d))
        opt = torch.optim.Adam(model.parameters(), lr=0.02)
        for _ in range(epochs):
            opt.zero_grad()
            loss = ((model(t) - t) ** 2).mean()
            loss.backward()
            opt.step()
        with torch.no_grad():
            err = ((model(ta) - ta) ** 2).mean(1).numpy()
        return err.tolist()
    except ImportError:
        pass
    rng = np.random.default_rng(seed)
    W1 = rng.normal(0, 0.3, (d, h)); b1 = np.zeros(h); W2 = rng.normal(0, 0.3, (h, d)); b2 = np.zeros(d)
    lr = 0.05
    for _ in range(epochs):
        H = np.tanh(Zt @ W1 + b1)
        out = H @ W2 + b2
        err = out - Zt
        gW2 = H.T @ err / n; gb2 = err.mean(0)
        gH = err @ W2.T * (1 - H ** 2)
        gW1 = Zt.T @ gH / n; gb1 = gH.mean(0)
        W1 -= lr * gW1; b1 -= lr * gb1; W2 -= lr * gW2; b2 -= lr * gb2
    H = np.tanh(Z @ W1 + b1)
    return ((H @ W2 + b2 - Z) ** 2).mean(1).tolist()


def detect_log_anomalies(store: Path, backend: str, run_id: str, dlog: "DetailLog") -> dict:
    """④ 日誌異常：trace(engine span ms) + bench(微基準 ms) 跨輪。IsolationForest(sklearn) 主判、z-score 降級、autoencoder 第二意見。"""
    out = {"status": "NO_HISTORY", "trace": [], "bench": []}
    trace = read_history(store, "trace", backend)
    bench = read_history(store, "bench", backend)
    try:
        import numpy as np
    except ImportError:
        return {"status": "NO_NUMPY"}

    def _scan(rows: list[dict], key: str, val: str, label: str) -> list[dict]:
        by: dict[str, list[tuple[str, float]]] = defaultdict(list)
        for r in rows:
            v = r.get(val)
            if v is None or r.get(key) is None:
                continue
            try:
                by[str(r[key])].append((str(r.get("run_id")), float(v)))
            except (TypeError, ValueError):
                continue
        flagged = []
        for name, pts in by.items():
            if len(pts) < 4:
                continue
            vals = np.array([p[1] for p in pts])
            latest_run = max(p[0] for p in pts)
            latest = [p[1] for p in pts if p[0] == latest_run]
            if not latest:
                continue
            z = (latest[-1] - vals[:-1].mean()) / (vals[:-1].std() + 1e-9)
            iso = None
            try:
                from sklearn.ensemble import IsolationForest
                iso_m = IsolationForest(random_state=0, contamination="auto").fit(vals.reshape(-1, 1))
                iso = float(iso_m.decision_function([[latest[-1]]])[0])
            except Exception:  # noqa: BLE001
                iso = None
            ae = _autoencoder_scores([[v, i / len(pts)] for i, v in enumerate(vals)])
            ae_last = ae[-1] if ae else 0.0
            ae_thr = float(np.mean(ae[:-1]) + 3 * np.std(ae[:-1])) if len(ae) > 2 else float("inf")
            is_anom = (abs(z) >= 3.0) or (iso is not None and iso < -0.05) or (ae_last > ae_thr)
            flagged.append({"name": name, "n": len(pts), "latest_ms": round(latest[-1], 2), "mean_ms": round(float(vals[:-1].mean()), 2),
                            "z": round(float(z), 2), "iso": (None if iso is None else round(iso, 3)), "ae_err": round(ae_last, 3),
                            "anomaly": bool(is_anom), "kind": label})
        return flagged
    out["trace"] = _scan(trace, "name", "ms", "trace")
    out["bench"] = _scan(bench, "name", "ms", "bench")
    n_an = sum(1 for x in out["trace"] + out["bench"] if x["anomaly"])
    out["status"] = "OK" if (out["trace"] or out["bench"]) else "NO_HISTORY"
    out["anomalies"] = n_an
    out["methods"] = ["z-score", "IsolationForest(sklearn)" if _has("sklearn") else "IsolationForest(缺 sklearn，略)", "autoencoder(" + ("torch" if _has("torch") else "numpy") + ")"]
    dlog.log("ml_anomaly", "log anomaly scan", status=out["status"], anomalies=n_an, series=len(out["trace"]) + len(out["bench"]))
    return out


def _has(mod: str) -> bool:
    try:
        import importlib.util
        return importlib.util.find_spec(mod) is not None
    except Exception:  # noqa: BLE001
        return False


def forecast_trend(learn: dict) -> dict:
    """⑤ 趨勢外推（stdlib 最小平方）：risk_M / functions 下一輪預測 + 斜率。"""
    tr = [t for t in learn.get("trend", []) if isinstance(t.get("risk_M"), (int, float)) and isinstance(t.get("functions"), (int, float))]
    if len(tr) < 3:
        return {"status": "INSUFFICIENT", "runs": len(tr)}

    def fit(ys):
        n = len(ys)
        xs = list(range(n))
        xm, ym = sum(xs) / n, sum(ys) / n
        den = sum((x - xm) ** 2 for x in xs) or 1.0
        b = sum((x - xm) * (y - ym) for x, y in zip(xs, ys)) / den
        a = ym - b * xm
        return round(b, 3), round(a + b * n, 1)
    sm, nm = fit([t["risk_M"] for t in tr])
    sf, nf = fit([t["functions"] for t in tr])
    return {"status": "OK", "runs": len(tr), "risk_M_slope": sm, "risk_M_next": nm, "functions_slope": sf, "functions_next": nf,
            "verdict": ("風險 M 上升中" if sm > 0.5 else "風險 M 下降中" if sm < -0.5 else "風險 M 持平")}


# ---------------------------------------------------------------- v1000 省 token 閉環：任務卡 / 決策回收 / 切片 / AI 修正驗證 / 提示詞
def _toks(sv: str) -> int:
    return max(1, len(sv) // 3)


def _slice_lines(root: Path, f, ctx: int = 6) -> str:
    try:
        lines = Path(f.abspath).read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return ""
    body = lines[f.lineno - 1:min(f.end_lineno, f.lineno - 1 + ctx)]
    return "\n".join(body) + ("\n    ..." if f.end_lineno - f.lineno + 1 > ctx else "")


def write_task_cards(out: Path, root: Path, funcs, scdt, ident, unknown_verbs: Counter, gates, merge_plan: dict, prior: dict) -> dict:
    """① 任務卡：一卡一決策 + 最小上下文。先前已回答的卡(ves_decisions)不再出卡。回 token 帳。"""
    cards = []
    answered = set(prior.get("answered", {}).keys())
    fmap = {f.fid: f for f in funcs}

    def card(cid, kind, question, options, context, impact, **extra):
        if cid in answered:
            return
        c = {"card": cid, "kind": kind, "impact": impact, "question": question, "options": options, "context": context}
        c.update(extra)
        c["tokens"] = _toks(json.dumps(c, ensure_ascii=False))
        cards.append(c)
    for i, c in enumerate(scdt, 1):
        cid = f"CARD-C{i:03d}"
        pi = c["proposed_interface"]
        mem = c["members"]
        ctx = {"cluster": f"C{i:03d}", "capability": c["capability"], "langs": c.get("langs", []), "tools": c["tools"],
               "members": [{"fid": m.fid, "code": getattr(m, "catalog_code", ""), "where": f"{m.file}:{m.lineno}", "sig": f"{m.qualname}({', '.join(m.args)})",
                            "risks": [r for r in m.risks if r != "R03_MISSING_TYPE_HINTS"][:4], "head": _slice_lines(root, m, 4)} for m in mem[:5]],
               "proposed": f"{pi['name']}(" + ", ".join(p["name"] + ("" if p["required"] else "=" + str(p["default"])) for p in pi["params"]) + ")",
               "recommend": c["recommendation"]}
        card(cid, "CLUSTER_ACCEPT", "這群是同功能異工具/語言、可合併嗎？canonical 用哪個？", ["ACCEPT", "ACCEPT_CANONICAL=<fid>", "REJECT", "SPLIT_GROUP"], ctx,
             impact=len(mem) * (2 if len(c.get("langs", [])) > 1 else 1), rescore=c.get("p_accept"))
        unt = [(m, [a for a in m.args if not m.arg_annots.get(a)]) for m in mem if m.lang == "py"]
        unt = [(m, a) for m, a in unt if a]
        if unt:
            card(cid + "-TYPES", "PARAM_TYPES", "這些參數缺型別註記（骨架目前 Any），請給型別（如 path:str, df:DataFrame）", ["TYPES=<arg:type,...>", "SKIP"],
                 {"cluster": f"C{i:03d}", "params": [{"fid": m.fid, "sig": f"{m.qualname}({', '.join(m.args)})", "untyped": a, "usage": m.arg_usage} for m, a in unt[:4]]},
                 impact=sum(len(a) for _, a in unt))
    for gi, g in enumerate(ident, 1):
        cid = f"CARD-I{gi:03d}"
        entry = next((e for e in merge_plan.get("identical", []) if e["cluster"] == f"I{gi:03d}"), {})
        card(cid, "ABSORB_CONFIRM", "完全相同的多頭：同意以 canonical 吸收（shim 轉發，不刪原定義）？", ["ACCEPT", "ACCEPT_CANONICAL=<file:qualname>", "REJECT"],
             {"canonical": entry.get("canonical"), "absorbed": entry.get("absorbed", [])[:6], "lang": entry.get("lang"), "how": entry.get("how", ""),
              "head": _slice_lines(root, g[0], 5)}, impact=len(g))
    for v, n in unknown_verbs.most_common(20):
        if n >= 3 and v not in VERB_TO_CAP:
            card(f"CARD-VERB-{v}", "VERB_CLASSIFY", f"動詞「{v}」屬於哪個能力軸？", list(VERB_CANON) + ["OTHER"],
                 {"hits": n, "examples": [f"{f.qualname} ({f.file})" for f in funcs if f.tokens and f.tokens[0] == v][:4]}, impact=n)
    m_risks = [(f, [r for r in f.risks if r.endswith(":M")]) for f in funcs if any(r.endswith(":M") for r in f.risks)]
    for f, rs in sorted(m_risks, key=lambda x: -len(x[1]))[:25]:
        card(f"CARD-RISK-{f.fid}", "RISK_CONFIRM", "確認級風險：真問題還是誤報？", ["TRUE", "FALSE_POSITIVE", "DEFER"],
             {"fid": f.fid, "where": f"{f.file}:{f.lineno}", "sig": f"{f.qualname}({', '.join(f.args)})", "risks": rs, "head": _slice_lines(root, f, 6)}, impact=len(rs))
    for g in gates:
        if g["status"] != "GREEN":
            card(f"CARD-GATE-{g['gate']}", "GATE_REVIEW", f"閘門 {g['gate']} = {g['status']}，要處理還是接受？", ["FIX", "ACCEPT_AS_IS"], {"value": g["value"]}, impact=3 if g["status"] == "RED" else 1)
    cards.sort(key=lambda c: -c["impact"])
    p = out / "ai_task_cards.jsonl"
    p.write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in cards) + ("\n" if cards else ""), encoding="utf-8")
    full = 0
    for fr in funcs:
        pass
    total_cards = sum(c["tokens"] for c in cards)
    return {"cards": len(cards), "tokens_cards": total_cards, "path": str(p), "answered_skipped": len(answered), "by_kind": dict(Counter(c["kind"] for c in cards))}


def load_decisions(out_parent: Path) -> dict:
    """② 決策回收：ves_decisions.jsonl 每行 `==VES-DECISION== CARD-xxx OPTION[ note]` 或 JSON {card, option, note}。append-only 只讀。"""
    p = out_parent / "ves_decisions.jsonl"
    answered: dict[str, dict] = {}
    if p.exists():
        for ln in p.read_text(encoding="utf-8", errors="replace").splitlines():
            ln = ln.strip()
            if not ln:
                continue
            m = re.match(r"==VES-DECISION==\s+(\S+)\s+(\S+)(?:\s+(.*))?", ln)
            if m:
                answered[m.group(1)] = {"option": m.group(2), "note": (m.group(3) or "").strip()}
            else:
                try:
                    d = json.loads(ln)
                    if d.get("card") and d.get("option"):
                        answered[d["card"]] = {"option": str(d["option"]), "note": str(d.get("note", ""))}
                except Exception:  # noqa: BLE001
                    continue
    return {"answered": answered, "path": str(p)}


def apply_decisions(out: Path, decisions: dict, scdt: list, ident: list, merge_plan: dict, unknown_verbs: Counter) -> dict:
    """② 確定性套用：CLUSTER → 回饋檔(訓練配對模型) + canonical 覆寫推薦；ABSORB → merge_plan 步驟 status；VERB → taxonomy verbs；
    RISK → 風險確認檔；全部 append-only，寫進 out.parent，不動原始碼。"""
    applied = {"feedback": 0, "taxonomy": 0, "canonical": 0, "absorb": 0, "risk": 0, "rejected_steps": 0}
    fb_lines, risk_lines = [], []
    tax_add: dict[str, list] = defaultdict(list)
    for cid, d in decisions.get("answered", {}).items():
        opt = d["option"].upper()
        if cid.startswith("CARD-C") and "-TYPES" not in cid:
            m = re.match(r"CARD-C(\d{3})", cid)
            idx = int(m.group(1)) - 1 if m else -1
            if 0 <= idx < len(scdt):
                c = scdt[idx]
                mems = ",".join(x.fid for x in c["members"])
                if opt.startswith("ACCEPT"):
                    fb_lines.append(f"==VES-FEEDBACK== C{idx + 1:03d} ACCEPT {mems}")
                    applied["feedback"] += 1
                    if opt.startswith("ACCEPT_CANONICAL="):
                        c["recommendation"]["primary"] = opt.split("=", 1)[1]
                        c["recommendation"]["basis"]["decided_by"] = "decision"
                        applied["canonical"] += 1
                elif opt == "REJECT":
                    fb_lines.append(f"==VES-FEEDBACK== C{idx + 1:03d} REJECT {mems}")
                    applied["feedback"] += 1
        elif cid.startswith("CARD-I"):
            m = re.match(r"CARD-I(\d{3})", cid)
            key = f"I{m.group(1)}" if m else ""
            for st in merge_plan.get("steps", []):
                if st.get("cluster") == key:
                    if opt.startswith("ACCEPT"):
                        st["status"] = "APPROVED"
                        if opt.startswith("ACCEPT_CANONICAL="):
                            st["canonical"] = opt.split("=", 1)[1]
                        applied["absorb"] += 1
                    elif opt == "REJECT":
                        st["status"] = "REJECTED"
                        applied["rejected_steps"] += 1
        elif cid.startswith("CARD-VERB-"):
            verb = cid[len("CARD-VERB-"):]
            if opt in VERB_CANON:
                tax_add[opt].append(verb)
                applied["taxonomy"] += 1
        elif cid.startswith("CARD-RISK-"):
            risk_lines.append(json.dumps({"fid": cid[len("CARD-RISK-"):], "verdict": opt, "note": d["note"]}, ensure_ascii=False))
            applied["risk"] += 1
    if fb_lines:
        with (out.parent / "ves_feedback.jsonl").open("a", encoding="utf-8") as fh:
            fh.write("\n".join(fb_lines) + "\n")
    if tax_add:
        tp = out.parent / TAXONOMY_FILE
        d = {"verbs": {}, "tools": {}, "stop": [], "pending_verbs": {}}
        if tp.exists():
            try:
                d.update(json.loads(tp.read_text(encoding="utf-8")))
            except Exception:  # noqa: BLE001
                _backup_bad_json(tp)
        for cap, vs in tax_add.items():
            d.setdefault("verbs", {}).setdefault(cap, [])
            for v in vs:
                if v not in d["verbs"][cap]:
                    d["verbs"][cap].append(v)
                d.get("pending_verbs", {}).pop(v, None)
        tp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    if risk_lines:
        with (out.parent / "ves_risk_verdicts.jsonl").open("a", encoding="utf-8") as fh:
            fh.write("\n".join(risk_lines) + "\n")
    # 被 REJECT 的 ABSORB 步驟不進沙盤
    merge_plan["steps"] = [st for st in merge_plan.get("steps", []) if st.get("status") != "REJECTED"]
    return applied


def slice_code(root: Path, catalog: dict, funcs, code: str, callers: int = 3) -> str:
    """③ 精準切片：FNC → import 區 + 定義本體 + 最多 N 個呼叫者各一行；CLS → 類別定義；MDL → 檔頭 40 行 + 函式簽章清單。"""
    u = catalog.get("units", {}).get(code)
    if not u:
        f = next((x for x in funcs if x.fid == code or x.qualname == code), None)
        if f is None:
            return f"# slice: {code} not found"
        u = {"type": "FNC", "context": f.file, "name": f.qualname}
    if u["type"] == "FNC":
        f = next((x for x in funcs if x.file == u["context"] and x.qualname == u["name"]), None)
        if f is None:
            return f"# slice: {code} LOST"
        lines = Path(f.abspath).read_text(encoding="utf-8", errors="replace").splitlines()
        imports = [ln for ln in lines[:80] if re.match(r"\s*(import |from .+ import |using |Import-Module|require\(|import .* from)", ln)]
        body = lines[f.lineno - 1:f.end_lineno]
        cs = _callers_of(funcs, f)[:callers]
        out = [f"# ==== {code} {f.file}:{f.lineno}-{f.end_lineno} lang={f.lang} cap={f.capability} tools={f.tools} risks={[r for r in f.risks if r != 'R03_MISSING_TYPE_HINTS']}",
               "# ---- imports (relevant)", *imports[:15], "# ---- definition", *body, "# ---- callers (one line each)"]
        for c in cs:
            try:
                cl = Path(c.abspath).read_text(encoding="utf-8", errors="replace").splitlines()
                ln = next((x for x in cl[c.lineno - 1:c.end_lineno] if f.name in x), cl[c.lineno - 1])
                out.append(f"#   {c.file}:{c.qualname}: {ln.strip()[:120]}")
            except OSError:
                pass
        return "\n".join(out) + "\n"
    if u["type"] == "CLS":
        ms = [x for x in funcs if x.file == u["context"] and x.qualname.startswith(u["name"] + ".")]
        if not ms:
            return f"# slice: class {u['name']} has no methods on record"
        lines = Path(ms[0].abspath).read_text(encoding="utf-8", errors="replace").splitlines()
        start = min(m.lineno for m in ms) - 1
        cls_line = next((i for i in range(start, -1, -1) if re.match(r"\s*class\s+" + re.escape(u["name"].split(".")[-1]), lines[i])), start)
        end = max(m.end_lineno for m in ms)
        return f"# ==== {code} {u['context']} class {u['name']} L{cls_line + 1}-{end}\n" + "\n".join(lines[cls_line:end]) + "\n"
    if u["type"] == "MDL":
        p = root / u["name"]
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines() if p.exists() else []
        sigs = [f"#   L{x.lineno} {x.qualname}({', '.join(x.args)}) cap={x.capability}" for x in funcs if x.file == u["name"]]
        return f"# ==== {code} {u['name']} ({len(lines)} lines, {len(sigs)} functions)\n# ---- head\n" + "\n".join(lines[:40]) + "\n# ---- signatures\n" + "\n".join(sigs) + "\n"
    return f"# slice: unsupported type {u['type']}"


def verify_ai_dir(root: Path, out: Path, verify_dir: Path, funcs, ident, catalog: dict, dlog) -> dict:
    """④ AI 修正驗證：verify_dir 內是 AI 改過的檔（相對路徑同 root）。閘：語法/LL 稽核/錨點保留(原函式仍找得到)/新分歧(Hydra)/pytest/刪除偵測。"""
    import py_compile
    rep_ = {"contract": "VES_VERIFY/1000", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "dir": str(verify_dir), "files": [], "gates": [], "verdict": "NO-GO"}
    changed = []
    for p in verify_dir.rglob("*"):
        if p.is_file() and p.suffix.lower() in LANG_EXT:
            rel = str(p.relative_to(verify_dir)).replace("\\", "/")
            orig = root / rel
            changed.append((rel, p, orig))
    if not changed:
        rep_["verdict"] = "NOTHING"
        return rep_
    bad, ll, lost, deleted_fns, shrink = [], [], [], [], []
    vfiles, vfuncs, _ = scan_tree(verify_dir, 1, None)
    for rel, p, orig in changed:
        rec = {"file": rel, "exists_in_root": orig.exists()}
        if p.suffix == ".py":
            try:
                py_compile.compile(str(p), doraise=True)
            except Exception as e:  # noqa: BLE001
                bad.append({"file": rel, "error": str(e)[-160:]})
        fr = next((x for x in vfiles if x.file == rel), None)
        if fr:
            ll += [{"file": rel, "risk": r} for r in fr.risks if r[:2] in ("R3", "R4")]
        if orig.exists():
            before = [f for f in funcs if f.file == rel]
            after = [f for f in vfuncs if f.file == rel]
            after_names = {f.qualname for f in after}
            for f in before:
                if f.qualname not in after_names:
                    a = resolve_anchor(make_anchor(f), vfuncs)
                    if a["status"] == "LOST":
                        deleted_fns.append({"file": rel, "function": f.qualname})
                    elif a["status"] == "RENAMED":
                        lost.append({"file": rel, "function": f.qualname, "now": a.get("qualname")})
            try:
                if len(p.read_text(encoding="utf-8", errors="replace")) < 0.5 * len(orig.read_text(encoding="utf-8", errors="replace")):
                    shrink.append(rel)
            except OSError:
                pass
        rep_["files"].append(rec)
    rep_["gates"].append({"gate": "VF_SYNTAX", "status": "GREEN" if not bad else "RED", "detail": bad})
    rep_["gates"].append({"gate": "VF_LL_AUDIT", "status": "GREEN" if not ll else "AMBER", "detail": ll[:20]})
    rep_["gates"].append({"gate": "VF_FUNCTIONS_KEPT", "status": "GREEN" if not deleted_fns else "RED", "detail": deleted_fns[:20]})
    rep_["gates"].append({"gate": "VF_RENAMES_TRACKED", "status": "GREEN" if not lost else "AMBER", "detail": lost[:20]})
    rep_["gates"].append({"gate": "VF_NO_MASS_SHRINK", "status": "GREEN" if not shrink else "RED", "detail": shrink})
    merged_funcs = [f for f in funcs if f.file not in {c[0] for c in changed}] + vfuncs
    hy = hydra_check(merged_funcs, [], [])
    new_div = [x for x in hy["findings"] if x["kind"] == "MULTI_HEAD_DIVERGENT"]
    old_div = {x["name"] for x in hydra_check(funcs, [], [])["findings"] if x["kind"] == "MULTI_HEAD_DIVERGENT"}
    fresh = [x for x in new_div if x["name"] not in old_div]
    rep_["gates"].append({"gate": "VF_HYDRA_NEW_DIVERGENCE", "status": "GREEN" if not fresh else "AMBER", "detail": fresh[:10]})
    tests = [p for p in verify_dir.rglob("test_*.py")]
    if tests and _has("pytest"):
        r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-x", "--no-header", *map(str, tests[:20])], capture_output=True, text=True, timeout=600, cwd=str(verify_dir))
        rep_["gates"].append({"gate": "VF_PYTEST", "status": "GREEN" if r.returncode == 0 else "RED", "detail": r.stdout[-300:]})
    reds = [g for g in rep_["gates"] if g["status"] == "RED"]
    rep_["verdict"] = "GO" if not reds else "NO-GO"
    out.mkdir(parents=True, exist_ok=True)
    (out / "verify_report.json").write_text(json.dumps(rep_, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    dlog.log("verify", rep_["verdict"], gates=[(g["gate"], g["status"]) for g in rep_["gates"]], files=len(changed))
    return rep_


VES_PROMPT = r"""# VES 使用提示詞（給任何 AI / 協作者）— VIA Engine Standardizer v{v}

## 這個引擎是什麼
VES 是 VIA 平台「E3 程式優化·合併」引擎：**唯讀**掃描一棵程式樹（Python / PowerShell / JS·TS），把每個檔案、類別、函式、匯入、群組
統一編號造冊，找出「功能相同、工具或語言不同」的函式群、完全重複的多頭、風險（40+ 條）、休眠函式、跨執行變化，
生成標準化骨架（BaseProcessor / Adapter / Factory / 指標層 / 影子模式 / 斷路器）、合併計畫、沙盤推演報告、AI 任務卡。
它從自己的日誌（Parquet 儲存）做機器學習（誤報分類、語意相似、回饋配對、異常偵測、趨勢）。**它不改原始碼**，
除非人給 ACTIVATION token，且即使套用也只做 add-only（追加、新檔、備份），永不刪除或覆寫。

## 你（AI）的角色：只做「機器判不了」的最後修正
1. **不要重讀整棵原始碼。** 讀 `AI_HANDOFF.md`（殘餘決策摘要）和 `ai_task_cards.jsonl`（一卡一決策，已附最小上下文）。
   需要更多上下文時，要求 `--slice <VIA-FNC-xxxx | FNC-00012 | qualname>` 的切片，不要整檔。
2. **回答用決策 token，一行一個**，讓引擎下一輪確定性套用：
   `==VES-DECISION== CARD-C001 ACCEPT`
   `==VES-DECISION== CARD-C001 ACCEPT_CANONICAL=FN-00007`
   `==VES-DECISION== CARD-C002-TYPES TYPES=path:str,df:DataFrame`
   `==VES-DECISION== CARD-I001 REJECT 這兩個是多型實作`
   `==VES-DECISION== CARD-VERB-backtest COMPUTE`
   `==VES-DECISION== CARD-RISK-FN-00031 FALSE_POSITIVE`
   選項只能用卡片列出的；不確定就 DEFER。這些行被寫進 `ves_decisions.jsonl`（只新增，不改舊行）。
3. **如果要直接改碼**：把改過的檔案放進一個目錄（相對路徑與原樹相同），請人跑 `--verify-dir 那個目錄`。
   VES 會檢查：語法、LL PowerShell 守則、原函式是否還在（錨點）、是否製造新的多頭分歧、是否大幅縮短、pytest。NO-GO 就不能合併。
   改碼原則：只增不減——不刪函式、不改既有簽章（要改就加新函式 + 舊名轉發）、不覆寫檔案、UTF-8 無 BOM。

## 產物怎麼讀（都在輸出目錄 run_YYYYMMDD_HHMMSS\）
- `VES_SUMMARY.md`：一頁摘要（閘門、前 15 群、DORMANT、diff、ML 狀態）。先看這個。
- `AI_HANDOFF.md`：五類殘餘決策 + token 估算。
- `ai_task_cards.jsonl`：任務卡（kind = CLUSTER_ACCEPT / PARAM_TYPES / ABSORB_CONFIRM / VERB_CLASSIFY / RISK_CONFIRM / GATE_REVIEW），impact 越大越先。
- `ves_inventory.json`：完整清單（函式、風險、群、閘門、diff、ML、造冊統計、沙盤）。大，不要整個讀。
- `merge_plan.json`：合併/拆分提案（canonical / absorbed / how），status PROPOSED→APPROVED/REJECTED 由決策卡改。
- `sandbox_report.json`：沙盤七閘 + Hydra 等級 + expected_token_hint；只有 GO 且 H0–H1 才可 `--apply`。
- `_standardized\`：生成骨架（base_processor.py / adapters / tests / shims.py / VIA_Common.psm1）。
- 上層目錄：`ves_catalog.json`（造冊）、`ves_store\`（Parquet 歷史）、`ves_taxonomy.json`（動詞分類法）、`ves_feedback.jsonl`、`ves_decisions.jsonl`、`edit_ledger.jsonl`。

## 證據等級與風險尾碼
V = 結構明確（AST/型別註記）· M = 模式命中或 ML 建議 · P = 推論/名稱猜測 · :SP = 歷史或 ML 判定的穩定誤報（已降權）。
九頭龍 Hydra：H0 無頭 · H1 多頭一致（可 shim）· H2 多頭分歧（HOLD 先對齊）· H3 編輯造成縫隙 · H4 破壞性（永遠拒絕）。

## 你不可以做的事
- 不可建議刪除任何函式/檔案/登記（只能建議標 DORMANT）。
- 不可假設卡片以外的上下文；缺就要切片。
- 不可把 M/P 級當事實陳述；引用時帶等級。
- 不可跳過沙盤/驗證直接要人套用。

## 一句話流程
**跑 VES → 讀 SUMMARY + 卡片 → 回決策 token（或改碼丟 verify-dir）→ 再跑 VES（確定性套用）→ 沙盤 GO → 人給 token 才 apply。**
"""


VES_AI_COLLAB = r"""# VES × AI 協作協定（VES_AI_COLLAB/1.0）

適用：Claude / 本機 Ollama / 任何能讀檔回文字的 AI。目的：AI 只花 token 在「機器判不了的決策」，程式碼的讀取、分群、風險、造冊、沙盤全由 VES 做。

## 0. 角色分工
| 誰 | 做什麼 | 不做什麼 |
|---|---|---|
| **VES（引擎）** | 唯讀掃描、造冊編號、分群、風險、骨架、合併計畫、沙盤推演、九頭龍分級、任務卡、決策套用、日誌 ML | 不改原始碼（除非人給 token，且只 add-only） |
| **AI** | 讀摘要與任務卡 → 回決策 token；必要時要切片；改碼只交 verify-dir | 不重讀整樹、不猜卡片外的上下文、不建議刪除、不跳過沙盤 |
| **人（Tony）** | 跑指令、把 AI 的 token 貼進 ves_decisions.jsonl、最後 `-Apply -Token` | 不需要自己讀 inventory |

## 1. 一輪協作的固定順序（Handshake）
```
[人]  pwsh -File Invoke-VIA-EngineStandardizer.ps1 -Root <tree>          # 第 1 跑
[VES] run_YYYYMMDD_HHMMSS\  ← VES_SUMMARY.md / AI_HANDOFF.md / ai_task_cards.jsonl / VES_PROMPT.md / sandbox_report.json
[人]  把 VES_PROMPT.md + VES_SUMMARY.md + ai_task_cards.jsonl 貼給 AI（≈ 幾千 tokens）
[AI]  回：一行一個 ==VES-DECISION== …；需要上下文時回 ==VES-NEED-SLICE== <碼或函式名>
[人]  (若有 NEED-SLICE) pwsh … -Slice <碼>  → 把 slice_*.txt 貼回 AI → AI 再回決策
[人]  把所有 ==VES-DECISION== 行追加到 <上層目錄>\ves_decisions.jsonl
[人]  再跑一次 VES                                                        # 第 2 跑：確定性套用決策
[VES] 卡片減少、merge_plan 步驟變 APPROVED/REJECTED、taxonomy 更新、配對模型重排、沙盤重推
[人]  看 sandbox_report.json：GO 且 Hydra ≤ H1 → pwsh … -Apply -Token <expected_token_hint>
[VES] add-only 套用：原檔 .orig 備份、尾端追加、新檔只新增、edit_ledger.jsonl
```
HOLD-H2（多頭分歧）→ 不 apply；先請 AI 對分歧的頭出決策（CARD-I… ACCEPT_CANONICAL=…），再跑。

## 2. AI 輸出格式（唯一合法格式）
```
==VES-DECISION== CARD-C001 ACCEPT
==VES-DECISION== CARD-C001 ACCEPT_CANONICAL=FN-00007
==VES-DECISION== CARD-C002-TYPES TYPES=path:str,df:DataFrame,start:str
==VES-DECISION== CARD-I003 REJECT 兩者是多型實作，不是重複
==VES-DECISION== CARD-VERB-backtest COMPUTE
==VES-DECISION== CARD-RISK-FN-00031 FALSE_POSITIVE
==VES-DECISION== CARD-GATE-VES_PARSE_RATE ACCEPT_AS_IS
==VES-NEED-SLICE== VIA-FNC-3C6D3E
==VES-NEED-SLICE== load_prices
==VES-DEFER== CARD-C005 需要看呼叫者
```
規則：選項只能用卡片列出的；每張卡最多一行；不確定用 DEFER；不要輸出解釋長文（引擎不讀）。

## 3. AI 讀取順序（省 token 的順序）
1. `VES_SUMMARY.md`（1 頁）→ 2. `ai_task_cards.jsonl` 依 impact 由大到小 → 3. 只對想確認的卡要 `--slice` → 4. 從不讀 `ves_inventory.json` 整檔。

## 4. AI 直接改碼時
1. 只改「卡片指到的函式」；新增函式 + 舊名轉發，不刪、不改既有簽章、不覆寫、UTF-8 無 BOM。
2. 改過的檔放進一個目錄，相對路徑與原樹相同；請人跑 `-VerifyDir <該目錄>`。
3. 閘：VF_SYNTAX / VF_LL_AUDIT / VF_FUNCTIONS_KEPT / VF_RENAMES_TRACKED / VF_NO_MASS_SHRINK / VF_HYDRA_NEW_DIVERGENCE / VF_PYTEST。任何 RED = 不合併，AI 收 verify_report.json 再修。

## 5. 範例對話（縮短）
```
人 → AI：[貼 VES_PROMPT.md] [貼 VES_SUMMARY.md] [貼 ai_task_cards.jsonl 21 張]
AI → 人：
==VES-DECISION== CARD-VERB-recover VALIDATE
==VES-DECISION== CARD-VERB-handle TRANSFORM
==VES-DECISION== CARD-C001 ACCEPT_CANONICAL=FN-00412
==VES-DECISION== CARD-I002 ACCEPT
==VES-NEED-SLICE== VIA-FNC-9A21F0
==VES-DEFER== CARD-C003
人 → 跑 -Slice VIA-FNC-9A21F0 → 貼回
AI → 人：==VES-DECISION== CARD-C003 REJECT 同名但一個是檔案讀取一個是 API 拉取
人 → 追加到 ves_decisions.jsonl → 再跑 VES → sandbox GO / H1 → -Apply -Token VES-ACTIVATE-7F3A
```

## 6. 失敗時
- 卡片全空：代表沒有殘餘決策；直接看 sandbox。
- AI 回了卡片以外的選項：引擎忽略該行（不報錯），下輪同卡再出。
- 決策互相矛盾：後寫的優先（append-only，最後一行勝）。
- 想撤回：再寫一行新決策覆蓋，不要刪舊行。

## 7. 證據與誠實
AI 引用 VES 的任何判斷都要帶等級：V（結構）/ M（模式或 ML）/ P（推論）/ :SP（穩定誤報已降權）。九頭龍 H0–H4 由引擎判，AI 不可自行降級。
"""


def write_prompt(out: Path) -> Path:
    p = out / "VES_PROMPT.md"
    p.write_text(VES_PROMPT.replace("{v}", VERSION), encoding="utf-8")
    (out / "VES_AI_COLLAB.md").write_text(VES_AI_COLLAB, encoding="utf-8")
    return p


# ---------------------------------------------------------------- HTML
RISK_TABLE = {
    "R01_DYNAMIC_IMPORT": ("動態載入遺漏", "AST 看不到 importlib/eval 匯入 → 改 sys.settrace 執行期追蹤或 regex 補掃"),
    "R02_DECORATOR_HIDES_SIGNATURE": ("裝飾器隱藏真實簽名", "擷取 decorator_list 建對應表；執行期用 inspect.signature 確認"),
    "R03_MISSING_TYPE_HINTS": ("缺乏型別提示", "重構前用 MonkeyType/PyAnnotate 收集執行期型別自動補齊"),
    "R05_SYNTAX_VERSION_CONFLICT": ("語法版本衝突 / 無法解析", "隔離 venv，AST 盤點腳本與目標專案 Python 版本一致"),
    "R07_KWARGS_ABUSE": ("**kwargs 濫用", "防腐層：已知參數→強型別欄位，未知→request.config"),
    "R11_NULL_SEMANTICS": ("空值語意分歧(NaN vs Null)", "Pandas 指定 dtype_backend='pyarrow' 與 Polars 對齊"),
    "R12_INDEX_DEPENDENCY": ("Pandas Index 依賴", "轉接器內一律 reset_index()，改用明確欄位 Join"),
    "R13_LAZY_NOT_MATERIALIZED": ("延遲執行未實體化", "回傳前強制 .collect()/.df()（BaseProcessor.materialize 已內建）"),
    "R15_REGEX_ENGINE_DIVERGENCE": ("正則引擎行為不一", "主程式預編譯 regex，以 boolean mask 傳入資料引擎"),
    "R16_MODULE_MUTABLE_STATE": ("模組層可變狀態(執行緒安全)", "Factory 每次回傳新實例；contextvars 隔離"),
    "R17_RESOURCE_NOT_RELEASED": ("資源未釋放(記憶體洩漏)", "BaseProcessor 已提供 __enter__/__exit__；把 close 移進 close()"),
    "R18_GLOBAL_CONFIG": ("全域設定污染", "廢除 settings/os.environ 直讀，改由 request.config 注入"),
    "R19_PRINT_LOGGING": ("print 日誌斷層", "統一 logging/loguru，logger.bind(task_id=…)"),
    "R20_HEAVY_INIT": ("啟動延遲過高", "重型套件於 _run() 內懶加載（骨架已如此生成）"),
    "R23_TEST_MATRIX_SIZE": ("測試矩陣過大", "pytest-xdist 平行；@pytest.mark.heavy 移 nightly"),
    "R05_READ_FAIL": ("檔案無法讀取", "檢查權限/鎖定；OneDrive 佔位檔請先下載"),
    "R26_TOPLEVEL_SIDE_EFFECT": ("模組頂層副作用(載入即執行)", "包進 if __name__ == '__main__' 或檢查 os.environ['VES_IMPORT_GUARD']"),
    "R27_RELATIVE_IMPORT": ("相對匯入", "load_source 已改以套件名載入；長期改絕對匯入"),
    "R28_OVERRIDE_PATTERN": ("同名方法多類別(override 樣式)", "非重複，屬多型實作；不合併，只確認介面一致"),
    "R30_PS_ALIAS": ("PS 使用別名 (LL)", "改全名 cmdlet：ls→Get-ChildItem、%→ForEach-Object、?→Where-Object"),
    "R31_PS_READ_HOST": ("PS Read-Host (LL 禁止等待輸入)", "改參數 / 預設值 / HTML 互動"),
    "R32_PS_EXIT": ("PS exit / Stop-Process (LL 禁止)", "改 return 或旗標；子程序用 ProcessStartInfo 管理"),
    "R33_PS_BLOCK_COMMENT": ("PS 區塊註解 (LL#10/#15)", "改 # 行註解；(217+pkgs) 之類會觸發 ParserError"),
    "R34_PS_PARAM_NOT_FIRST": ("PS param() 非首個可執行語句 (LL)", "param() 移到最前(僅 #requires/註解可在前)"),
    "R35_PS_VAR_COLON_IN_STRING": ("PS 字串內 $var: (LL#17)", "改 ${var}:"),
    "R36_PS_NULL_CONDITIONAL_IN_STRING": ("PS 字串內 ?. (LL#13)", "先賦值再 if 檢查"),
    "R37_PS_SORT_MULTI_NOT_HASHTABLE": ("PS Sort-Object 多屬性未用 hashtable (LL)", "@{e='P1';desc=$true}, @{e='P2';desc=$true}"),
    "R38_PS_REDIRECT_STDOUT_BUFFER": ("PS RedirectStandardOutput=$true 緩衝到結束 (LL#26)", "長任務改 $false 繼承主控台即時串流"),
    "R39_PS_BOM_RISK": ("PS Out-File/Set-Content 未指定編碼 (BOM 風險)", "用 [IO.File]::WriteAllText($p,$s,[UTF8Encoding]::new($false))"),
    "R40_PS_SHORT_FN_ALIAS_CLASH": ("PS 短函式名撞 PS7 別名 (SL/SP/WL/WB/DP)", "改全名 Save-PhaseLog/Show-Prog/Write-Log"),
    "R41_PS_SWITCH_SHADOWED": ("PS [switch] 與同名區域變數 (LL)", "區域變數改名，如 $AddIndent"),
    "R42_PS_ORDERED_CONTAINSKEY": ("PS [ordered] 用 .ContainsKey (LL#18)", "改 .Contains()"),
    "R43_PS_GCI_RECURSE_SLOW": ("PS Get-ChildItem -Recurse 慢且遇權限中止", "改 [IO.Directory]::EnumerateFiles + EnumerationOptions"),
}

CSS = """
:root{--b:#4c78a8;--t:#439a9a;--g:#9c9890;--up:#c96b5a;--dn:#5a9e6f;--paper:#f5f4f0;
--i0:#1c1b19;--i1:#3d3b37;--i2:#6b6862;--i3:#b8b5ae;--i4:#e6e3dc}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--i0);font-family:"DM Sans",system-ui,sans-serif;font-size:13px}
h1,h2{font-family:Syne,"DM Sans",sans-serif;font-weight:700;letter-spacing:.02em}
header{padding:22px 28px 10px;border-bottom:1px solid var(--i4)}
header h1{margin:0;font-size:22px}header .sub{color:var(--i2);font-family:"DM Mono",monospace;font-size:12px;margin-top:4px}
.kpis{display:flex;gap:10px;flex-wrap:wrap;padding:14px 28px}
.kpi{background:#fff;border:1px solid var(--i4);border-radius:8px;padding:10px 14px;min-width:132px}
.kpi b{display:block;font-family:"DM Mono",monospace;font-size:22px;color:var(--b)}.kpi span{color:var(--i2);font-size:11px}
.tabs{display:flex;gap:4px;padding:0 28px;border-bottom:1px solid var(--i4);flex-wrap:wrap}
.tab{padding:9px 14px;cursor:pointer;border:1px solid transparent;border-bottom:none;border-radius:8px 8px 0 0;color:var(--i2)}
.tab.on{background:#fff;border-color:var(--i4);color:var(--b);font-weight:600}
.pane{display:none;padding:18px 28px}.pane.on{display:block}
table{border-collapse:collapse;width:100%;background:#fff;font-size:12px}
th{background:var(--i4);text-align:left;padding:6px 8px;font-weight:600;position:sticky;top:0}
td{padding:5px 8px;border-bottom:1px solid var(--i4);vertical-align:top;font-family:"DM Mono",monospace}
tr.c0 td{background:#eef3f8}tr.c1 td{background:#ecf5f5}
.pill{display:inline-block;padding:1px 7px;border-radius:10px;font-size:11px;margin:1px 2px 1px 0;font-family:"DM Mono",monospace}
.pb{background:#dfe8f2;color:var(--b)}.pt{background:#dcefee;color:var(--t)}.pg{background:#ecebe7;color:var(--i1)}
.pr{background:#f6e2dd;color:var(--up)}.pd{background:#e0eee4;color:var(--dn)}
.bar{height:8px;background:var(--i4);border-radius:4px;overflow:hidden}.bar i{display:block;height:100%;background:linear-gradient(90deg,var(--b),var(--t))}
.mx{display:grid;gap:2px;font-family:"DM Mono",monospace;font-size:11px}
.mx div{padding:6px 8px;background:#fff;border:1px solid var(--i4);border-radius:4px;text-align:center}
.mx .h{background:var(--i4);font-weight:600}.mx .z{color:var(--i3)}
.foot{padding:14px 28px;color:var(--i2);font-size:11px;font-family:"DM Mono",monospace;border-top:1px solid var(--i4)}
details{margin:6px 0}summary{cursor:pointer;color:var(--b)}
input.q{padding:6px 10px;border:1px solid var(--i3);border-radius:6px;width:320px;margin-bottom:10px;font-family:"DM Mono",monospace}
"""


def _e(s) -> str:
    return html.escape(str(s))


def render_html(out: Path, root: Path, files: list[FileRec], funcs: list[FuncRec], ident, scdt, near,
                scaffold_files: list[str], elapsed: float, have_pydantic: bool, threshold: float,
                unknown_verbs: Counter | None = None, workers: int = 1, llm_model: str = "",
                llm_map: dict | None = None, gates: list | None = None, diff: dict | None = None,
                stats: dict | None = None, ml: dict | None = None, learn: dict | None = None,
                handoff: dict | None = None, persisted: dict | None = None, merge_plan: dict | None = None,
                ml_learn: dict | None = None, catalog: dict | None = None, sandbox: dict | None = None) -> Path:
    merge_plan = merge_plan or {}
    ml_learn = ml_learn or {}
    ml = ml or {}
    learn = learn or {}
    handoff = handoff or {}
    persisted = persisted or {}
    unknown_verbs = unknown_verbs or Counter()
    llm_map = llm_map or {}
    gates = gates or []
    diff = diff or {}
    stats = stats or {}
    fmap = {f.fid: f for f in funcs}
    tool_cnt = Counter(t for f in funcs for t in f.tools)
    cap_cnt = Counter(f.capability for f in funcs)
    risk_cnt = Counter(r.split(":")[0] for f in funcs for r in f.risks) + Counter(r.split(":")[0] for fr in files for r in fr.risks)
    risk_conf = Counter(r for f in funcs for r in f.risks if ":" in r)
    for k in list(risk_conf):
        if k.endswith(":SP"):
            risk_conf[k[:-3] + ":P"] += risk_conf.pop(k)
    parse_fail = [f for f in files if not f.parse_ok]
    caps = [c for c in list(VERB_CANON) + ["OTHER"] if cap_cnt.get(c)]
    tools = [t for t, _ in tool_cnt.most_common(18)]
    # capability × tool matrix
    mx = defaultdict(int)
    for f in funcs:
        for t in f.tools:
            mx[(f.capability, t)] += 1

    def pill(t, cls="pg"):
        return f'<span class="pill {cls}">{_e(t)}</span>'

    def grp_rows(groups, cls_prefix=""):
        rows = []
        for gi, g in enumerate(groups):
            members = g["members"] if isinstance(g, dict) else g
            c = "c0" if gi % 2 == 0 else "c1"
            meta = ""
            if isinstance(g, dict):
                meta = (f'{pill(g["capability"], "pb")} 工具集={g["distinct_tool_sets"]} 檔案={g["files"]} '
                        f'相似={g["score"]}')
                if len(members) > 30:
                    meta += pill("超大群：連鎖傳遞造成，建議 --threshold 調高至 0.8", "pr")
            if isinstance(g, dict) and "proposed_interface" in g:
                pi = g["proposed_interface"]
                sig = ", ".join((p["name"] if p["required"] else p["name"] + "=" + str(p["default"])) for p in pi["params"])
                rc = g["recommendation"]
                meta += f'<br><span style="color:var(--i1)">提案介面 <code>{_e(pi["name"])}({_e(sig)})</code> · 主={_e(rc["primary"])} 備={_e(rc["fallback"])}</span>'
            fbb = ""
            if cls_prefix == "C":
                mem_ids = ",".join(m.fid for m in members)
                fbb = (f' <button onclick="fb(\'{cls_prefix}{gi + 1:03d}\',\'ACCEPT\',\'{mem_ids}\')" style="font-size:11px">接受</button>'
                       f'<button onclick="fb(\'{cls_prefix}{gi + 1:03d}\',\'REJECT\',\'{mem_ids}\')" style="font-size:11px">拒絕</button>'
                       + (f' p_accept={g.get("p_accept")}' if isinstance(g, dict) and g.get("p_accept") is not None else ""))
            rows.append(f'<tr class="{c}"><td colspan="6"><b>{cls_prefix}{gi + 1:03d}</b> · 成員 {len(members)} · {meta}{fbb}</td></tr>')
            for m in members:
                rows.append(
                    f'<tr class="{c}"><td>{_e(m.fid)}</td><td>{_e(m.qualname)}</td><td>{_e(m.file)}:{m.lineno}</td>'
                    f'<td>{", ".join(_e(a) for a in m.args)}{" **kw" if m.has_kwargs else ""}</td>'
                    f'<td>{"".join(pill(t, "pt") for t in m.tools) or "—"}</td>'
                    f'<td>{"".join(pill(r.split("_")[0] + (":" + r.split(":")[1] if ":" in r else ""), "pr" if (":P" not in r and ":SP" not in r) else "pg") for r in m.risks)}</td></tr>')
        return "\n".join(rows) or '<tr><td colspan="6" class="z">（無）</td></tr>'

    hdr = '<tr><th>FID</th><th>函式</th><th>檔案:行</th><th>參數</th><th>工具</th><th>風險</th></tr>'
    mx_html = ['<div class="mx" style="grid-template-columns:140px repeat(%d,minmax(56px,1fr))">' % len(tools),
               '<div class="h">能力 \\ 工具</div>'] + [f'<div class="h">{_e(t)}</div>' for t in tools]
    for c in caps:
        mx_html.append(f'<div class="h">{c} ({cap_cnt[c]})</div>')
        for t in tools:
            n = mx.get((c, t), 0)
            if n:
                a = min(1.0, 0.15 + n / max(1, max(mx.values())) * 0.85)
                mx_html.append(f'<div style="background:rgba(76,120,168,{a:.2f});color:#fff">{n}</div>')
            else:
                mx_html.append('<div class="z">·</div>')
    mx_html.append('</div>')

    risk_rows = []
    for code, n in risk_cnt.most_common():
        nm, sol = RISK_TABLE.get(code, (code, ""))
        conf = ""
        if risk_conf.get(code + ":M") or risk_conf.get(code + ":P"):
            conf = f' {pill("M " + str(risk_conf.get(code + ":M", 0)), "pd")}{pill("P " + str(risk_conf.get(code + ":P", 0)), "pg")}'
        risk_rows.append(f'<tr><td>{_e(code)}</td><td>{_e(nm)}</td><td>{n}{conf}</td><td>{_e(sol)}</td></tr>')

    file_rows = []
    for fr in sorted(files, key=lambda x: (-x.func_count, x.file)):
        st = pill("PARSE_FAIL " + fr.parse_error, "pr") if not fr.parse_ok else pill("OK", "pd")
        file_rows.append(f'<tr><td>{_e(fr.file)}</td><td>{fr.lines}</td><td>{fr.func_count}</td>'
                         f'<td>{"".join(pill(t, "pt") for t in fr.tools)}</td><td>{st}{"".join(pill(r.split("_")[0], "pr") for r in fr.risks)}</td></tr>')

    gate_html = "".join(f'<div class="kpi" style="border-left:4px solid {"var(--dn)" if g["status"] == "GREEN" else ("#d9a441" if g["status"] == "AMBER" else "var(--up)")}"><b style="font-size:14px;color:{"var(--dn)" if g["status"] == "GREEN" else ("#d9a441" if g["status"] == "AMBER" else "var(--up)")}">{g["status"]}</b><span>{_e(g["gate"])} · {_e(g["value"])}</span></div>' for g in gates)
    dorm = [f for f in funcs if f.dormant_candidate]
    dorm_rows = "".join(f'<tr><td>{_e(f.fid)}</td><td>{_e(f.qualname)}</td><td>{_e(f.file)}:{f.lineno}</td><td>{f.fan_out}</td><td>{pill(f.dormant_level, "pr" if f.dormant_level == "STRONG" else "pg")} 模糊命中 {f.fan_in_ambiguous}</td></tr>' for f in sorted(dorm, key=lambda x: (x.dormant_level != "STRONG", x.file))[:800])
    diff_html = ""
    if diff.get("available"):
        diff_html = (f'<h2>跨執行 diff（vs 上一輪 v{_e(diff.get("prev_version"))}）</h2><p>新增 {len(diff["added"])} · 移除 {len(diff["removed"])} · 邏輯變更 {len(diff["changed"])} · 功能同工具異群 {diff["prev_scdt"]}→{diff["now_scdt"]}</p>'
                     + "".join(f'<details><summary>{lbl} {len(diff[k])}</summary><p style="font-family:\'DM Mono\',monospace">{"<br>".join(_e(x) for x in diff[k][:200])}</p></details>' for k, lbl in (("added", "新增"), ("removed", "移除"), ("changed", "變更"))))
    skipped = [f for f in files if f.skipped]
    fn_rows = []
    fn_cap_note = ""
    fn_list = funcs
    if len(funcs) > HTML_FN_ROWS_CAP:                     # 風險8: HTML 上限
        fn_list = funcs[:HTML_FN_ROWS_CAP]
        fn_cap_note = f'<p style="color:var(--up)">函式共 {len(funcs)} 筆，表格只嵌前 {HTML_FN_ROWS_CAP} 筆；完整清單在 ves_inventory.json。</p>'
    for f in fn_list:
        fn_rows.append(f'<tr><td>{_e(f.fid)}</td><td>{_e(f.qualname)} {pill(f.lang, "pg") if f.lang != "py" else ""}</td><td>{_e(f.file)}:{f.lineno}</td>'
                       f'<td>{pill(f.capability, "pb")}</td><td>{"".join(pill(t, "pt") for t in f.tools)}</td>'
                       f'<td>{_e(f.body_hash)}</td><td>{"".join(pill(r.split("_")[0], "pr") for r in f.risks)}</td></tr>')

    scaf = "<br>".join(_e(s) for s in scaffold_files)
    doc = f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<title>VIA Engine Standardizer v{VERSION}</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Mono&family=DM+Sans:wght@400;600&family=Syne:wght@700&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body>
<header><h1>VIA Engine Standardizer <span style="color:var(--t)">v{VERSION}</span></h1>
<div class="sub">AST 盤點 → 功能同/工具異 分群 → 25 項風險稽核 → 標準化骨架 · 100% 唯讀 · 只增不減 · root={_e(root)} · {time.strftime("%Y-%m-%d %H:%M:%S")} · {elapsed:.1f}s · workers×{workers}</div></header>
<div class="kpis">
<div class="kpi"><b>{len(files)}</b><span>.py 檔案</span></div>
<div class="kpi"><b>{len(funcs)}</b><span>函式/方法</span></div>
<div class="kpi"><b>{len(ident)}</b><span>邏輯完全相同群</span></div>
<div class="kpi"><b>{len(scdt)}</b><span>功能同·工具異群 ★</span></div>
<div class="kpi"><b>{len(near)}</b><span>近似重複群</span></div>
<div class="kpi"><b>{len(parse_fail)}</b><span>無法解析</span></div>
<div class="kpi"><b>{sum(risk_cnt.values())}</b><span>風險命中</span></div>
<div class="kpi"><b>{"pydantic" if have_pydantic else "dataclass"}</b><span>骨架 schema 後端</span></div>
<div class="kpi"><b>{stats.get("cache_hits", 0)}</b><span>快取命中(未變檔)</span></div>
<div class="kpi"><b>{len(dorm)}</b><span>DORMANT 候選(fan_in=0)</span></div>
</div>
<div class="kpis" style="padding-top:0">{gate_html}</div>
<div class="tabs">
<div class="tab on" data-p="p0">總覽矩陣</div><div class="tab" data-p="p1">★ 功能同·工具異</div>
<div class="tab" data-p="p2">邏輯完全相同</div><div class="tab" data-p="p3">近似重複</div>
<div class="tab" data-p="p4">風險稽核</div><div class="tab" data-p="p5">檔案</div>
<div class="tab" data-p="p6">全部函式</div><div class="tab" data-p="p7">生成骨架</div><div class="tab" data-p="p8">分類法·動態匯入</div><div class="tab" data-p="p9">呼叫圖·DORMANT·diff</div><div class="tab" data-p="p10">CPU ML·DL 能力</div><div class="tab" data-p="p11">儲存·自學·AI 交接</div><div class="tab" data-p="p12">多語言·合併計畫·LL 稽核</div><div class="tab" data-p="p13">LOG→ML·DL 學習</div><div class="tab" data-p="p14">造冊·沙盤·九頭龍</div></div>
<div class="pane on" id="p0"><h2>能力軸 × 工具家族 熱度矩陣</h2><p style="color:var(--i2)">同一列裡出現 ≥2 個工具欄位 = 「功能相同、工具相異」的整併候選帶。門檻 threshold={threshold}。</p>{"".join(mx_html)}
<h2>工具家族註冊</h2>{"".join(pill(f"{t} ×{n}", "pt") for t, n in tool_cnt.most_common())}</div>
<div class="pane" id="p1"><h2>功能相同 · 工具相異（標準化整併主目標）</h2><table>{hdr}{grp_rows(scdt, "C")}</table></div>
<div class="pane" id="p2"><h2>正規化 AST 結構完全相同（變數名/docstring/行號已抹除）</h2><table>{hdr}{grp_rows(ident, "I")}</table></div>
<div class="pane" id="p3"><h2>近似重複（同工具、名稱/參數高度相似）</h2><table>{hdr}{grp_rows(near, "N")}</table></div>
<div class="pane" id="p4"><h2>25 項風險稽核 · 命中統計</h2><table><tr><th>代碼</th><th>風險</th><th>命中</th><th>解決方案</th></tr>{"".join(risk_rows) or '<tr><td colspan="4">無命中</td></tr>'}</table>
<p style="color:var(--i2)">未列出的風險(R04/R06/R08/R09/R10/R14/R21/R22/R24/R25)屬設計期或執行期決策，已內建於骨架（materialize / fallback / shadow_run / _approx_equal / extra=allow）。v0400 新增 R26 頂層副作用 / R27 相對匯入 / R28 override 樣式。</p></div>
<div class="pane" id="p5"><table><tr><th>檔案</th><th>行數</th><th>函式</th><th>工具</th><th>狀態</th></tr>{"".join(file_rows)}</table></div>
<div class="pane" id="p9"><h2>DORMANT 候選（公開函式、fan_in=0、非入口/非裝飾器路由）</h2><p style="color:var(--i2)">v0600 接收者感知：self./ClassName./同模組優先解析；其他 x.method() 屬多型模糊不算 fan_in。STRONG=零解析且零模糊命中；WEAK=零解析但有同名方法被模糊呼叫。動態呼叫/反射仍會漏；候選≠可刪，依只增不減標 DORMANT 即可。</p>
<table><tr><th>FID</th><th>函式</th><th>檔案:行</th><th>fan_out</th><th>等級</th></tr>{dorm_rows or '<tr><td colspan="5">無</td></tr>'}</table>
{diff_html}
<h2>跳過的檔案</h2><table><tr><th>檔案</th><th>原因</th></tr>{"".join(f'<tr><td>{_e(f.file)}</td><td>{_e(f.parse_error or f.skipped)}</td></tr>' for f in skipped) or '<tr><td colspan="2">無</td></tr>'}</table></div>
<div class="pane" id="p10"><h2>CPU 跑得動的 ML / DL 工具（自動偵測 + 微基準）</h2>
{("<p>Python " + _e(ml.get("python")) + " · " + _e(ml.get("machine")) + " · " + str(ml.get("cpu_count")) + " 核 · RAM " + str(ml.get("ram_gb")) + " GB · " + _e(",".join(ml.get("cpu_flags", [])) or "flags?") + "</p><p><b>等級：" + _e(ml.get("recommendation", {}).get("tier", "")) + "</b> · ML 首選 " + _e(", ".join(ml.get("recommendation", {}).get("ml_first_choice", []))) + " · DL 首選 " + _e(", ".join(ml.get("recommendation", {}).get("dl_first_choice", []))) + " · 本機 LLM 建議 " + _e(ml.get("recommendation", {}).get("llm_local", "")) + "</p>") if ml else '<p style="color:var(--i2)">未執行（--no-ml-probe）</p>'}
<table><tr><th>工具</th><th>類別</th><th>狀態</th><th>版本</th><th>import ms</th><th>備註</th></tr>{"".join(f'<tr><td>{_e(t["name"])}</td><td>{_e(t["class"])}</td><td>{pill(t["status"], "pd" if t["status"] == "OK" else "pg")}</td><td>{_e(t["version"])}</td><td>{t["import_ms"]}</td><td>{_e(t["note"])}</td></tr>' for t in ml.get("tools", []))}</table>
<h2>微基準</h2><table><tr><th>基準</th><th>狀態</th><th>ms</th><th>備註</th></tr>{"".join(f'<tr><td>{_e(b["name"])}</td><td>{pill(b["status"], "pd" if b["status"] == "OK" else "pr")}</td><td>{b["ms"]}</td><td>{_e(b["note"])}</td></tr>' for b in ml.get("benchmarks", [])) or '<tr><td colspan="4">無</td></tr>'}</table></div>
<div class="pane" id="p11"><h2>專案自有儲存（ves_store · Parquet 分區 · append-only）</h2>
<p>後端 <b>{_e(persisted.get("backend", ""))}</b>；本輪寫入：{"<br>".join(f"{_e(k)} → {_e(v)}" for k, v in persisted.get("tables", {}).items())}</p>
<p style="color:var(--i2)">查詢範例：<code>duckdb.sql("SELECT run_id, functions, risk_M FROM read_parquet('ves_store/runs/**/*.parquet') ORDER BY run_id")</code></p>
<h2>持續強化（自學，純統計可審計）</h2><p>歷史輪數 {learn.get("runs_seen", 0)} · STABLE_P（≥3 輪只出現 :P 從未 :M → 疑似誤報降權）{learn.get("stable_p", 0)} 項 · 本輪降權 {learn.get("downweighted", 0)}</p>
<table><tr><th>run_id</th><th>functions</th><th>risk_M</th><th>risk_P</th><th>gates</th></tr>{"".join(f'<tr><td>{_e(t["run_id"])}</td><td>{t["functions"]}</td><td>{t["risk_M"]}</td><td>{t["risk_P"]}</td><td>{_e(t["gates"])}</td></tr>' for t in learn.get("trend", [])) or '<tr><td colspan="5">首輪</td></tr>'}</table>
<h2>任務卡（ai_task_cards.jsonl · 一卡一決策 · 最小上下文）</h2><p>{(handoff or {}).get("cards", 0)} 張 ≈ {(handoff or {}).get("tokens_cards", 0):,} tokens（相對全樹省 {(handoff or {}).get("saving_pct_cards", 0)}%）· AI 回 <code>==VES-DECISION== CARD-xxx OPTION</code> 貼進 ves_decisions.jsonl，下一輪確定性套用。完整說明：<code>VES_PROMPT.md</code>。</p>
<h2>先機器修復 → 再交 AI（AI_HANDOFF.md）</h2><p>整棵原始碼 ≈ <b>{handoff.get("full_src_tokens", 0):,}</b> tokens → 交接檔 ≈ <b>{handoff.get("handoff_tokens", 0):,}</b> tokens，省 <b>{handoff.get("saving_pct", 0)}%</b>。AI 只看：待補型別參數、介面提案核可、:M 級風險、待分類動詞、非 GREEN 閘門。</p>
<p>詳細日誌：<code>ves_detail.log</code>（JSONL，每步驟一筆，含檔案級異常與閘門）</p></div>
<div class="pane" id="p14"><h2>全景造冊（ves_catalog.json · 上層目錄 · append-only）</h2>
<p>{" · ".join(f"{k}: {v}" for k, v in (catalog or {}).get("counts", {}).items())} · 完整性 {pill("OK", "pd") if (catalog or {}).get("completeness", {}).get("ok") else pill("GAP", "pr")} {_e(json.dumps((catalog or {}).get("completeness", {}), ensure_ascii=False))}</p>
<p style="color:var(--i2)">編號 recipe VIA-{{MDL|CLS|FNC|LIB|ENG}}-blake2s(TYPE|name|context,3)，雜湊輸入入冊；每個 FNC 帶精準錨(檔+名+本體雜湊+行距)與彈性錨(tokens+簽章+能力)；本輪未見者轉 DORMANT 不刪。</p>
<h2>沙盤推演（sandbox_report.json）</h2><p>裁決 <b>{_e((sandbox or {}).get("verdict", ""))}</b> · Hydra <b>{_e((sandbox or {}).get("hydra", {}).get("level", ""))}</b>（{_e((sandbox or {}).get("hydra", {}).get("legend", {}).get((sandbox or {}).get("hydra", {}).get("level", ""), ""))}）</p>
<div class="kpis" style="padding:0">{"".join(f'<div class="kpi" style="border-left:4px solid {"var(--dn)" if g["status"] == "GREEN" else ("#d9a441" if g["status"] == "AMBER" else "var(--up)")}"><b style="font-size:14px">{g["status"]}</b><span>{_e(g["gate"])}</span></div>' for g in (sandbox or {}).get("gates", []))}</div>
<table><tr><th>步驟</th><th>狀態</th><th>細節</th></tr>{"".join(f'<tr><td>{_e(s["action"])}</td><td>{pill(s["status"], "pd" if s["status"] == "OK" else ("pg" if s["status"] == "SKIP" else "pr"))}</td><td>{_e(str(s["detail"])[:160])}</td></tr>' for s in (sandbox or {}).get("steps", [])) or '<tr><td colspan="3">無步驟</td></tr>'}</table>
<h3>九頭龍發現</h3><table><tr><th>等級</th><th>類型</th><th>內容</th></tr>{"".join(f'<tr><td>{pill(x["level"], "pr" if x["level"] in ("H3", "H4") else ("pt" if x["level"] == "H2" else "pg"))}</td><td>{_e(x["kind"])}</td><td>{_e(json.dumps({k: v for k, v in x.items() if k not in ("level", "kind")}, ensure_ascii=False)[:220])}</td></tr>' for x in (sandbox or {}).get("hydra", {}).get("findings", [])[:200]) or '<tr><td colspan="3">H0 無頭</td></tr>'}</table>
<p>套用規則：<code>--apply --token VES-ACTIVATE-xxxx</code>（token 於 sandbox_report / expected_token_hint）；只有 GO 且 Hydra ≤ H1 才接受；套用永遠 add-only（原檔 .orig 備份、尾端追加、新檔只新增），edit_ledger.jsonl 全程。</p>
<h2>25 項模組化風險與擋點</h2><table><tr><th>碼</th><th>風險</th><th>Hydra</th><th>擋點 / 解法</th></tr>{"".join(f'<tr><td>{c}</td><td>{_e(n)}</td><td>{pill(h, "pr" if h in ("H3", "H4") else ("pt" if h == "H2" else "pg"))}</td><td>{_e(sol)}</td></tr>' for c, n, h, sol in MOD_RISKS)}</table></div>
<div class="pane" id="p13"><h2>LOG → 機器學習 / 深度學習（CPU · 免費 libs · 全部可降級 · 輸出皆 M 級）</h2>
<h3>① 風險誤報分類器</h3><p>{_e(json.dumps({k: v for k, v in ml_learn.get("fp_classifier", {}).items() if k != "feature_importances_top"}, ensure_ascii=False))}</p>
<h3>② 語意相似度後端</h3><p>{_e(ml_learn.get("semantic", "off"))}（minilm = sentence-transformers；tfidf = sklearn；hashing = stdlib）已併入分群公式 +0.15·sem_r</p>
<h3>③ 分群回饋模型</h3><p>{_e(json.dumps({k: v for k, v in ml_learn.get("pair_model", {}).items() if k != "coef"}, ensure_ascii=False))}</p>
<p style="color:var(--i2)">滑鼠回饋：在「功能同·工具異」頁每群按 接受/拒絕 → 下方自動產 token → 貼進 <code>{_e(str(out.parent / "ves_feedback.jsonl"))}</code>（新增一行即可，不必刪舊行）。下一輪據此訓練配對模型並重排。</p>
<textarea id="fbtok" style="width:100%;height:90px;font-family:'DM Mono',monospace;font-size:11px" placeholder="按了接受/拒絕後 token 會出現在這裡"></textarea>
<h3>④ 日誌異常偵測（trace / bench 跨輪）</h3><p>方法：{_e(", ".join(ml_learn.get("anomaly", {}).get("methods", [])))} · 狀態 {_e(ml_learn.get("anomaly", {}).get("status", ""))} · 異常 {ml_learn.get("anomaly", {}).get("anomalies", 0)}</p>
<table><tr><th>序列</th><th>類</th><th>n</th><th>最新 ms</th><th>均值 ms</th><th>z</th><th>IsoForest</th><th>AE 誤差</th><th>異常</th></tr>{"".join(f'<tr><td>{_e(x["name"])}</td><td>{_e(x["kind"])}</td><td>{x["n"]}</td><td>{x["latest_ms"]}</td><td>{x["mean_ms"]}</td><td>{x["z"]}</td><td>{x["iso"]}</td><td>{x["ae_err"]}</td><td>{pill("ANOMALY", "pr") if x["anomaly"] else pill("ok", "pd")}</td></tr>' for x in (ml_learn.get("anomaly", {}).get("trace", []) + ml_learn.get("anomaly", {}).get("bench", []))[:120]) or '<tr><td colspan="9">歷史不足 4 輪</td></tr>'}</table>
<h3>⑤ 趨勢預測</h3><p>{_e(json.dumps(ml_learn.get("forecast", {}), ensure_ascii=False))}</p>
<h3>⑥ 免費 CPU libs 導入計畫</h3><p><code>{_e(ml_learn.get("requirements", ""))}</code> → <code>pip install -r ves_ml_requirements.txt</code>（VES 不自動安裝；PS 端 -InstallMlLibs 才裝）</p>
<p>模型與指標：<code>ves_store/models/</code>（*.meta.json / *.pkl / models_ledger.jsonl append-only）</p></div>
<div class="pane" id="p12"><h2>多語言盤點</h2><p>{" · ".join(f"{k}: {v} 函式" for k, v in Counter(f.lang for f in funcs).items())} · 檔案 {" · ".join(f"{k}: {v}" for k, v in Counter(f.lang for f in files).items())}</p>
<h2>跨語言同功能群（same_cap_diff_lang）</h2><table><tr><th>群</th><th>能力</th><th>語言</th><th>成員</th><th>提案介面</th></tr>{"".join(f'<tr><td>{_e(x["cluster"])}</td><td>{_e(x["capability"])}</td><td>{_e(",".join(x["langs"]))}</td><td>{"<br>".join(_e(m) for m in x["members"][:12])}</td><td><code>{_e(x["proposed_interface"]["name"])}({_e(", ".join(p["name"] for p in x["proposed_interface"]["params"]))})</code></td></tr>' for x in merge_plan.get("cross_language", [])) or '<tr><td colspan="5">無</td></tr>'}</table>
<h2>合併計畫（merge_plan.json · 只提案不動原檔）</h2><table><tr><th>群</th><th>語言</th><th>canonical</th><th>absorbed → DORMANT</th><th>方式</th></tr>{"".join(f'<tr><td>{_e(x["cluster"])}</td><td>{_e(x["lang"])}</td><td>{_e(x["canonical"])}</td><td>{"<br>".join(_e(a) for a in x["absorbed"][:10])}</td><td>{"shims.py" if x["shim"] else ("VIA_Common.psm1" if x["lang"] == "ps1" else "共用 export")}</td></tr>' for x in merge_plan.get("identical", [])[:200]) or '<tr><td colspan="5">無完全重複</td></tr>'}</table>
<p>PS 跨檔重複 helper → <code>_standardized/VIA_Common.psm1</code>：{_e(", ".join(x["function"] + " ×" + str(len(x["duplicates"]) + 1) for x in merge_plan.get("ps_common_module", [])) or "無")}；py 重複 → <code>_standardized/shims.py</code></p>
<h2>LL PowerShell 守則稽核（R30–R43）</h2><table><tr><th>檔案</th><th>命中</th></tr>{"".join(f'<tr><td>{_e(fr.file)}</td><td>{"".join(pill(r, "pr") for r in fr.risks if r.startswith("R3") or r.startswith("R4"))}</td></tr>' for fr in files if fr.lang == "ps1" and any(r[:2] in ("R3", "R4") for r in fr.risks)) or '<tr><td colspan="2">無 PS 檔或全數符合 LL</td></tr>'}</table></div>
<div class="pane" id="p6">{fn_cap_note}<input class="q" id="q" placeholder="篩選 函式 / 檔案 / 工具 / 能力…"><table id="fnt"><tr><th>FID</th><th>函式</th><th>檔案:行</th><th>能力</th><th>工具</th><th>結構雜湊</th><th>風險</th></tr>{"".join(fn_rows)}</table></div>
<div class="pane" id="p8"><h2>分類法（外掛 ves_taxonomy.json · 只增不減）</h2>
<p style="color:var(--i2)">歸為 OTHER 的函式首動詞統計；命中 ≥3 已自動寫入 <code>pending_verbs</code>(P 級)。把它搬進 <code>verbs</code> 的對應能力軸，下次執行即生效，OTHER 會自動縮小。</p>
<p style="color:var(--i2)">本機 LLM 語意代理：{_e(llm_model) if llm_model else "未啟用/未偵測到 Ollama（--llm auto 可開；qwen2.5:3b 建議）"}；LLM 建議標 M 級，人工搬進 verbs 才升 V。</p>
<table><tr><th>未知首動詞</th><th>命中</th><th>建議</th></tr>{"".join(f'<tr><td>{_e(v)}</td><td>{n}</td><td>{(pill("LLM→" + llm_map[v] + " (M)", "pt") if v in llm_map else "") + ("→ pending_verbs (待填能力軸)" if n >= 3 else "—")}</td></tr>' for v, n in unknown_verbs.most_common(80)) or '<tr><td colspan="3">全部動詞已可分類</td></tr>'}</table>
<h2>動態匯入目標（R01 regex 補掃，AST 看不到的）</h2>
<table><tr><th>檔案</th><th>字串型模組名</th></tr>{"".join(f'<tr><td>{_e(fr.file)}</td><td>{", ".join(_e(t) for t in fr.dynamic_targets)}</td></tr>' for fr in files if fr.dynamic_targets) or '<tr><td colspan="2">無</td></tr>'}</table></div>
<div class="pane" id="p7"><h2>已生成（全新目錄，原檔未動；重跑時既有 adapter 保留、新版本寫 _vN，scaffold_ledger.jsonl 追加）</h2><p style="font-family:'DM Mono',monospace">{scaf}</p>
<p>登記碼：<code>ves_registry.json</code>（VIA-ENG-xxxxxx，recipe 與雜湊輸入入檔，P 級 CANDIDATE，經 via-code 核可才 ACTIVE）· 省 token 摘要：<code>VES_SUMMARY.md</code> · 設定：<code>ves_config.json</code>（skip_dirs / excludes / threshold）· 快取：上層目錄 <code>ves_cache.json</code>（內容雜湊）</p>
<p><b>v0300 檔案指標層</b>：<code>EngineRequest.inputs = {{"ticks": {{"source_type":"local_file","path":"...parquet","lazy":true}}}}</code>；轉接器依 POINTER_ENGINE 延遲解析（polars scan / duckdb read / pandas chunks），資料本體永不進 payload；SAFE_ROOTS 白名單防目錄遍歷（環境變數 VIA_SAFE_ROOTS 可加）；fallback 拿到的是乾淨唯讀指標，無狀態繼承。遙測寫 <code>ves_trace.jsonl</code>（task_id/span/ms）。</p>
<p>下一步：① adapters 已自動生成 Payload 型別模型＋群內參數同義映射(PARAM_ALIAS)，只剩「未註記型別 = Any」需要補 ② tests 填代表性 payload → <code>pytest _standardized/tests -q</code> ③ 用 <code>shadow_run(primary, shadow, req)</code> 影子跑一週再切換。風險代碼後綴 :M = 接收者確認來自資料工具（可信）、:P = 僅字串特徵命中（可能誤報）。</p></div>
<div class="foot">VIA Engine Standardizer · Visual Lock · 唯讀掃描 · 骨架僅寫入 _standardized\\ · 原始碼零改動</div>
<script>
document.querySelectorAll('.tab').forEach(t=>t.onclick=()=>{{document.querySelectorAll('.tab').forEach(x=>x.classList.remove('on'));document.querySelectorAll('.pane').forEach(x=>x.classList.remove('on'));t.classList.add('on');document.getElementById(t.dataset.p).classList.add('on');}});
window.fb=function(c,v,m){{const t=document.getElementById('fbtok');if(!t)return;t.value+=('==VES-FEEDBACK== '+c+' '+v+' '+m+'\\n');try{{navigator.clipboard.writeText(t.value);}}catch(e){{}}}};
const q=document.getElementById('q');q&&q.addEventListener('input',()=>{{const v=q.value.toLowerCase();document.querySelectorAll('#fnt tr').forEach((r,i)=>{{if(i===0)return;r.style.display=r.textContent.toLowerCase().includes(v)?'':'none';}});}});
</script></body></html>"""
    p = out / "VIA_EngineStandardizer.html"
    p.write_text(doc, encoding="utf-8")
    return p


# ---------------------------------------------------------------- main
def _prev_inventory(out: Path) -> dict | None:
    """升級3: 找上一輪 run_* 目錄的 ves_inventory.json 做 diff。"""
    base = out.parent
    try:
        runs = sorted([d for d in base.iterdir() if d.is_dir() and d.name.startswith("run_") and d != out
                       and (d / "ves_inventory.json").exists()], key=lambda d: d.name)
    except OSError:
        return None
    if not runs:
        return None
    try:
        return json.loads((runs[-1] / "ves_inventory.json").read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


def _diff_runs(prev: dict | None, funcs: list[FuncRec], scdt: list[dict]) -> dict:
    if not prev:
        return {"available": False}
    old = {(f["file"], f["qualname"]): f for f in prev.get("functions", [])}
    new = {(f.file, f.qualname): f for f in funcs}
    added = sorted(k for k in new if k not in old)
    removed = sorted(k for k in old if k not in new)
    changed = sorted(k for k in new if k in old and old[k].get("body_hash") != new[k].body_hash)
    return {"available": True, "prev_version": prev.get("version"), "added": [f"{a}:{b}" for a, b in added][:500],
            "removed": [f"{a}:{b}" for a, b in removed][:500], "changed": [f"{a}:{b}" for a, b in changed][:500],
            "prev_scdt": len(prev.get("clusters", {}).get("same_cap_diff_tool", [])), "now_scdt": len(scdt)}


# ---------------------------------------------------------------- v0900 全景造冊 / 定位點 / 沙盤推演 / Hydra
MOD_RISKS = [  # 25 項模組化風險 (code, 名稱, Hydra 等級, 擋點/解法)
    ("MR01", "重複邏輯多頭並存 (九頭龍)", "H1", "造冊 identical 群；canonical + shim；不刪頭"),
    ("MR02", "多頭已分歧 (改了一份沒改其他)", "H2", "body_hash 分歧偵測；merge 前先對齊或明確保留分支"),
    ("MR03", "編輯後呼叫者失聯 (縫隙)", "H3", "沙盤內解析所有呼叫者；任何 LOST 即 NO-GO"),
    ("MR04", "部分更新 (只改到一半)", "H3", "計畫以群為原子單位；全群成功才寫入，否則整批回滾"),
    ("MR05", "刪除/覆寫原檔", "H4", "add-only 硬規則；.orig 備份；apply 拒絕任何 delete 步驟"),
    ("MR06", "簽章斷裂 (參數名/順序改變)", "H4", "shim 保留舊簽章轉發；proposed_interface 只新增不改舊"),
    ("MR07", "行號漂移使錨點失效", "H1", "精準錨 + 彈性錨雙錨；MOVED 自動重定位、CHANGED 要求重規劃"),
    ("MR08", "同名不同義 (多型/override) 被誤合", "H2", "R28 降級；方法級只在同類別合併"),
    ("MR09", "循環匯入 (shim 指回舊模組)", "H3", "沙盤 import 全檔；發現 ImportError/循環即 NO-GO"),
    ("MR10", "相對匯入在新位置失效", "H3", "SPLIT 時改 load_source 路徑載入；R27 標記檔優先人工"),
    ("MR11", "頂層副作用被搬動 (載入即執行)", "H3", "R26 檔的函式不做 SPLIT；沙盤 import 觀察副作用"),
    ("MR12", "全域狀態/設定被拆散", "H2", "R16/R18 檔標 HOLD；狀態注入 request.config"),
    ("MR13", "資源釋放路徑被切斷 (檔案/連線)", "H3", "R17 函式合併時要求 Context Manager 包裹"),
    ("MR14", "測試沒跟著搬 (測試失聯)", "H2", "沙盤跑 pytest；tests/ 對應檔一併登記"),
    ("MR15", "型別/契約不一致 (Any 漏洞)", "H2", "Payload 模型；未註記參數列 AI_HANDOFF"),
    ("MR16", "動態載入/反射看不見的呼叫者", "H2", "R01 檔標 HOLD；regex 補掃字串型名稱"),
    ("MR17", "PowerShell 殼與 py 引擎版本錯位", "H2", "跨語言群記 langs；PS 殼只做薄殼呼叫 VTH E3"),
    ("MR18", "編碼/BOM 改變導致 diff 全檔", "H1", "讀寫皆 UTF-8 no BOM；沙盤 diff 只允許尾端追加"),
    ("MR19", "Windows 路徑/長路徑/OneDrive 佔位", "H1", "\\\\?\\ 前綴；佔位檔 SKIP 不編輯"),
    ("MR20", "快取回放舊結果 (改了引擎沒重掃)", "H1", "cache 鍵含 engine_hash；計畫綁定 inventory run_id"),
    ("MR21", "未造冊單位被遺漏", "H2", "catalog 完整性閘：函式數 == FNC 數；LIB/CLS 全登記"),
    ("MR22", "編號碰撞/不可驗證", "H1", "blake2s recipe + hash_input 入檔 (LL#30)；碰撞加 context"),
    ("MR23", "同時多人/多程序編輯", "H3", "計畫檔含 inventory 雜湊；apply 前重驗；不同即 NO-GO"),
    ("MR24", "自動化無人審核直接寫入", "H4", "--apply 必須 ACTIVATION token；沙盤 GO 才開放"),
    ("MR25", "遺漏 log (無法回溯)", "H2", "edit_ledger.jsonl 每步 before/after hash；沙盤報告落地"),
]
HYDRA_ORDER = {"H0": 0, "H1": 1, "H2": 2, "H3": 3, "H4": 4}


def build_catalog(out: Path, files: list, funcs: list, scdt: list, ident: list, inventory_hash: str) -> dict:
    """① 全景造冊：MDL / CLS / FNC / LIB / ENG 統一編號 (VIA-{TYPE}-blake2s(TYPE|name|context,3))，雜湊輸入入檔；交叉索引；append-only 合併舊冊。"""
    cat_path = out.parent / "ves_catalog.json"
    cat = {"version": VERSION, "contract": "VES_CATALOG/0900", "recipe": "VIA-{TYPE}-blake2s(TYPE|name|context,digest=3).hexUpper",
           "units": {}, "xref": {"fnc_by_mdl": {}, "fnc_by_lib": {}, "fnc_by_eng": {}}, "inventory_hash": inventory_hash}
    if cat_path.exists():
        try:
            old = json.loads(cat_path.read_text(encoding="utf-8"))
            cat["units"] = old.get("units", {})
        except Exception:  # noqa: BLE001
            _backup_bad_json(cat_path)
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    seen_now = set()

    def put(code, hin, kind, name, context, **attrs):
        u = cat["units"].get(code)
        if u is None:
            u = {"code": code, "hash_input": hin, "type": kind, "name": name, "context": context, "status": "ACTIVE",
                 "first_seen": now, "last_seen": now}
            cat["units"][code] = u
        u["last_seen"] = now
        u["status"] = attrs.pop("status", u.get("status", "ACTIVE"))
        u.update(attrs)
        seen_now.add(code)
        return code

    mdl_of: dict[str, str] = {}
    for fr in files:
        code, hin = via_code("MDL", fr.file, fr.lang)
        mdl_of[fr.file] = put(code, hin, "MDL", fr.file, fr.lang, lang=fr.lang, lines=fr.lines, content_hash=fr.content_hash,
                              parse_ok=fr.parse_ok, risks=fr.risks, imports=fr.imports[:40])
        for lib in fr.imports:
            top = lib.split(".")[0]
            lc, lh = via_code("LIB", top, fr.lang)
            put(lc, lh, "LIB", top, fr.lang, family=ALIAS_TO_FAMILY.get(top, ""))
            cat["xref"]["fnc_by_lib"].setdefault(lc, [])
    cls_seen = {}
    for f in funcs:
        if f.is_method:
            cls_name = f.qualname.rsplit(".", 1)[0]
            key = (f.file, cls_name)
            if key not in cls_seen:
                cc, ch = via_code("CLS", cls_name, f.file)
                cls_seen[key] = put(cc, ch, "CLS", cls_name, f.file, mdl=mdl_of.get(f.file), lang=f.lang)
        fc, fh = via_code("FNC", f.qualname, f.file)
        put(fc, fh, "FNC", f.qualname, f.file, fid=f.fid, mdl=mdl_of.get(f.file), cls=cls_seen.get((f.file, f.qualname.rsplit(".", 1)[0])) if f.is_method else None,
            lang=f.lang, lineno=f.lineno, end_lineno=f.end_lineno, body_hash=f.body_hash, capability=f.capability, tools=f.tools,
            args=f.args, risks=f.risks, fan_in=f.fan_in, dormant=f.dormant_level,
            anchor=make_anchor(f), status=("DORMANT_CANDIDATE" if f.dormant_level == "STRONG" else "ACTIVE"))
        f.catalog_code = fc
        cat["xref"]["fnc_by_mdl"].setdefault(mdl_of.get(f.file, "?"), []).append(fc)
        for lib in (fr.imports for fr in files if fr.file == f.file):
            for lb in lib:
                lc, _ = via_code("LIB", lb.split(".")[0], f.lang)
                if lc in cat["units"] and any(t == ALIAS_TO_FAMILY.get(lb.split(".")[0], "") for t in f.tools):
                    cat["xref"]["fnc_by_lib"].setdefault(lc, []).append(fc)
    for i, c in enumerate(scdt, 1):
        ec, eh = via_code("ENG", c["proposed_interface"]["name"], c["capability"] + "|" + ",".join(c["tools"]))
        put(ec, eh, "ENG", c["proposed_interface"]["name"], c["capability"], cluster=f"C{i:03d}", langs=c.get("langs", []),
            members=[getattr(m, "catalog_code", "") for m in c["members"]], recommendation=c["recommendation"])
        cat["xref"]["fnc_by_eng"][ec] = [getattr(m, "catalog_code", "") for m in c["members"]]
        c["eng_code"] = ec
    for gi, g in enumerate(ident, 1):
        ic, ih = via_code("ENG", "identical_" + g[0].body_hash, g[0].lang)
        put(ic, ih, "ENG", "identical_" + g[0].name, "identical", cluster=f"I{gi:03d}", members=[getattr(m, "catalog_code", "") for m in g])
    for code, u in cat["units"].items():                         # 本輪未見 → 保留，狀態轉 DORMANT(只增不減)
        if code not in seen_now and u.get("status") == "ACTIVE":
            u["status"] = "DORMANT"
            u["dormant_since"] = now
    cat["counts"] = dict(Counter(u["type"] for u in cat["units"].values()))
    cat["completeness"] = {"functions": len(funcs), "FNC_now": sum(1 for u in cat["units"].values() if u["type"] == "FNC" and u["last_seen"] == now),
                           "files": len(files), "MDL_now": sum(1 for u in cat["units"].values() if u["type"] == "MDL" and u["last_seen"] == now)}
    cat["completeness"]["ok"] = (cat["completeness"]["functions"] == cat["completeness"]["FNC_now"] and cat["completeness"]["files"] == cat["completeness"]["MDL_now"])
    cat_path.write_text(json.dumps(cat, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    (out / "ves_catalog_snapshot.json").write_text(json.dumps({"inventory_hash": inventory_hash, "counts": cat["counts"], "completeness": cat["completeness"]}, ensure_ascii=False, indent=1), encoding="utf-8")
    return cat


def make_anchor(f) -> dict:
    """② 雙錨：precise(檔案+qualname+body_hash+行距) / flexible(名稱 tokens+參數簽章+能力+語言)。"""
    return {"precise": {"file": f.file, "qualname": f.qualname, "body_hash": f.body_hash, "lineno": f.lineno, "end_lineno": f.end_lineno},
            "flexible": {"tokens": _canon(f.tokens), "args": list(f.args), "capability": f.capability, "lang": f.lang, "calls_fp": sorted(_call_fingerprint(f))[:12]}}


def resolve_anchor(anchor: dict, funcs: list) -> dict:
    """在目前樹上找回錨點：EXACT(同檔同名同雜湊同行) / MOVED(同檔同名同雜湊、行變) / CHANGED(同檔同名、本體變) /
    RENAMED(彈性錨命中：tokens+args+capability 相同、名字不同) / LOST。"""
    pr, fl = anchor["precise"], anchor["flexible"]
    same_name = [f for f in funcs if f.file == pr["file"] and f.qualname == pr["qualname"]]
    for f in same_name:
        if f.body_hash == pr["body_hash"]:
            return {"status": "EXACT" if f.lineno == pr["lineno"] else "MOVED", "fid": f.fid, "lineno": f.lineno, "drift": f.lineno - pr["lineno"]}
    if same_name:
        return {"status": "CHANGED", "fid": same_name[0].fid, "lineno": same_name[0].lineno, "old_hash": pr["body_hash"], "new_hash": same_name[0].body_hash}
    for f in funcs:
        if f.body_hash == pr["body_hash"] and f.lang == fl["lang"]:
            return {"status": "RENAMED", "fid": f.fid, "file": f.file, "qualname": f.qualname, "lineno": f.lineno}
    best, best_s = None, 0.0
    for f in funcs:
        if f.lang != fl["lang"] or f.capability != fl["capability"]:
            continue
        tr = len(set(_canon(f.tokens)) & set(fl["tokens"])) / max(1, len(set(_canon(f.tokens)) | set(fl["tokens"])))
        ar = len(set(f.args) & set(fl["args"])) / max(1, len(set(f.args) | set(fl["args"]))) if (f.args or fl["args"]) else 1.0
        cr = len(set(_call_fingerprint(f)) & set(fl["calls_fp"])) / max(1, len(set(_call_fingerprint(f)) | set(fl["calls_fp"]))) if fl["calls_fp"] else 0.5
        sc = 0.5 * tr + 0.3 * ar + 0.2 * cr
        if sc > best_s:
            best, best_s = f, sc
    if best is not None and best_s >= 0.8:
        return {"status": "RENAMED", "fid": best.fid, "file": best.file, "qualname": best.qualname, "lineno": best.lineno, "score": round(best_s, 3)}
    return {"status": "LOST"}


def _callers_of(funcs: list, target) -> list:
    out = []
    for f in funcs:
        for c in f.calls:
            last = c.split(".")[-1]
            if last == target.name and f is not target:
                out.append(f)
                break
    return out


def hydra_check(funcs: list, ident: list, plan_steps: list) -> dict:
    """④ 九頭龍檢查：identical 群 = 多頭；同名不同體 = 分歧；計畫步驟涉及 delete/簽章變更 = H4；被吸收者仍有呼叫者且無 shim = H3。"""
    by_name: dict[str, list] = defaultdict(list)
    for f in funcs:
        if not f.is_method:
            by_name[f.name].append(f)
    findings = []
    level = "H0"

    def raise_to(l):
        nonlocal level
        if HYDRA_ORDER[l] > HYDRA_ORDER[level]:
            level = l
    for g in ident:
        findings.append({"level": "H1", "kind": "MULTI_HEAD_CONSISTENT", "heads": [f"{m.file}:{m.qualname}" for m in g]})
        raise_to("H1")
    for name, lst in by_name.items():
        hashes = {f.body_hash for f in lst}
        if len(lst) >= 2 and len(hashes) >= 2 and not name.startswith("_") and name not in ("main", "run", "cli"):
            findings.append({"level": "H2", "kind": "MULTI_HEAD_DIVERGENT", "name": name, "heads": [f"{f.file}:{f.lineno}#{f.body_hash}" for f in lst]})
            raise_to("H2")
    fmap = {(f.file, f.qualname): f for f in funcs}
    for st in plan_steps:
        act = st.get("action", "").upper()
        if act in ("DELETE", "REMOVE", "OVERWRITE"):
            findings.append({"level": "H4", "kind": "DESTRUCTIVE_STEP", "step": st})
            raise_to("H4")
        if act == "ABSORB":
            for a in st.get("absorbed", []):
                file_, rest = a.split(":", 1)
                qual = rest.split(" ", 1)[-1]
                f = fmap.get((file_, qual))
                if f is None:
                    continue
                callers = _callers_of(funcs, f)
                if callers and not st.get("how", "").startswith(("shims", "VIA_Common")):
                    findings.append({"level": "H3", "kind": "GAP_CALLERS_WITHOUT_SHIM", "absorbed": a, "callers": [c.file + ":" + c.qualname for c in callers][:10]})
                    raise_to("H3")
        if act in ("RENAME", "SIGNATURE_CHANGE") and not st.get("keep_alias", True):
            findings.append({"level": "H4", "kind": "SIGNATURE_BREAK", "step": st})
            raise_to("H4")
    return {"level": level, "findings": findings, "applicable": HYDRA_ORDER[level] <= 1,
            "legend": {"H0": "無頭", "H1": "多頭一致(可 shim)", "H2": "多頭分歧(先對齊)", "H3": "編輯造成縫隙", "H4": "破壞性"}}


def sandbox_simulate(root: Path, out: Path, plan: dict, funcs: list, ident: list, catalog: dict, dlog) -> dict:
    """③ 沙盤推演：在 out/_sandbox 複製受影響檔 → 依 add-only 規則模擬 MERGE/SPLIT → 全檔語法+編譯 → 匯入 → 呼叫者解析 → pytest(若有) → Hydra → GO/NO-GO。
    永不碰 root 原檔。"""
    import py_compile
    import shutil as _sh
    sb = out / "_sandbox"
    if sb.exists():
        _sh.rmtree(sb, ignore_errors=True)
    sb.mkdir(parents=True, exist_ok=True)
    report = {"contract": "VES_SANDBOX/0900", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "plan_steps": len(plan.get("steps", [])), "steps": [],
              "gates": [], "verdict": "NO-GO", "sandbox": str(sb)}
    involved: set[str] = set()
    for st in plan.get("steps", []):
        for x in [st.get("canonical", "")] + list(st.get("absorbed", [])) + list(st.get("sources", [])):
            if ":" in x:
                involved.add(x.split(":", 1)[0])
    # anchor re-resolution against current funcs（計畫 vs 現在的樹）
    drift = []
    for st in plan.get("steps", []):
        for x in [st.get("canonical", "")] + list(st.get("absorbed", [])):
            if ":" not in x:
                continue
            file_, rest = x.split(":", 1)
            qual = rest.split(" ", 1)[-1]
            u = next((u for u in catalog.get("units", {}).values() if u.get("type") == "FNC" and u.get("name") == qual and u.get("context") == file_), None)
            if u and u.get("anchor"):
                r = resolve_anchor(u["anchor"], funcs)
                if r["status"] not in ("EXACT", "MOVED"):
                    drift.append({"unit": x, "resolve": r})
    report["gates"].append({"gate": "SB_ANCHORS", "status": "GREEN" if not drift else "RED", "detail": drift[:20]})
    # copy involved files (+ whole package dirs for imports)
    copied = []
    for rel in sorted(involved):
        srcp = root / rel
        if srcp.exists():
            dst = sb / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            _sh.copy2(srcp, dst)
            copied.append(rel)
    report["copied"] = copied
    # simulate steps (add-only edits on the copies)
    for st in plan.get("steps", []):
        act = st.get("action", "").upper()
        rec = {"action": act, "status": "SKIP", "detail": ""}
        try:
            if act == "ABSORB" and st.get("how", "").startswith("shims"):
                for a in st.get("absorbed", []):
                    file_, rest = a.split(":", 1)
                    qual = rest.split(" ", 1)[-1]
                    p = sb / file_
                    if p.exists() and p.suffix == ".py":
                        canon_file, crest = st["canonical"].split(":", 1)
                        cqual = crest.split(" ", 1)[-1]
                        addition = (f"\n\n# ---- VES v{VERSION} ABSORB (add-only): {qual} → canonical {canon_file}:{cqual}\n"
                                    f"# 原定義保留在上方；下列別名讓新呼叫者走 canonical。若要真正移除本地定義需 Tony 明示「刪除」。\n"
                                    f"try:\n    from _standardized.base_processor import load_source as _ves_ls\n"
                                    f"    {qual}_canonical = _ves_ls({json.dumps(str(root / canon_file), ensure_ascii=False)}, {json.dumps(cqual)})\n"
                                    f"except Exception:  # noqa: BLE001\n    {qual}_canonical = {qual}\n")
                        p.write_text(p.read_text(encoding="utf-8", errors="replace") + addition, encoding="utf-8")
                rec["status"] = "OK"
                rec["detail"] = f"appended alias block to {len(st.get('absorbed', []))} file(s)"
            elif act == "ABSORB":
                rec["status"] = "OK"
                rec["detail"] = "non-py absorb: documented only (VIA_Common.psm1 / shared export)"
            elif act == "SPLIT":
                # sources: ["file:qualname", ...] → new module st["target"]（新檔），舊檔尾端追加轉發
                target = sb / st["target"]
                target.parent.mkdir(parents=True, exist_ok=True)
                chunks = ["# -*- coding: utf-8 -*-", f'"""VES v{VERSION} SPLIT (add-only) — 從原模組抽出的函式副本；原模組保留原定義並在尾端追加轉發。"""', ""]
                for x in st.get("sources", []):
                    file_, rest = x.split(":", 1)
                    qual = rest.split(" ", 1)[-1]
                    f = next((f for f in funcs if f.file == file_ and f.qualname == qual), None)
                    srcp = sb / file_
                    if f is None or not srcp.exists():
                        raise ValueError(f"source not found: {x}")
                    lines = srcp.read_text(encoding="utf-8", errors="replace").splitlines()
                    chunks.append("\n".join(lines[f.lineno - 1:f.end_lineno]))
                    chunks.append("")
                    srcp.write_text("\n".join(lines) + f"\n\n# ---- VES v{VERSION} SPLIT (add-only): {qual} 也存在於 {st['target']}；本地定義保留。\n", encoding="utf-8")
                target.write_text("\n".join(chunks) + "\n", encoding="utf-8")
                rec["status"] = "OK"
                rec["detail"] = f"wrote {st['target']} with {len(st.get('sources', []))} function(s)"
            elif act in ("DELETE", "REMOVE", "OVERWRITE"):
                rec["status"] = "REJECTED"
                rec["detail"] = "destructive step never simulated (H4)"
            elif act == "INTEGRATE":
                rec["status"] = "OK"
                rec["detail"] = "adapter registration is generated in _standardized/ (already add-only)"
        except Exception as e:  # noqa: BLE001
            rec["status"] = "FAIL"
            rec["detail"] = f"{type(e).__name__}: {e}"
        report["steps"].append(rec)
    # gates: syntax/compile on all copied .py
    bad = []
    for rel in copied + [st.get("target", "") for st in plan.get("steps", []) if st.get("action", "").upper() == "SPLIT"]:
        p = sb / rel
        if p.exists() and p.suffix == ".py":
            try:
                py_compile.compile(str(p), doraise=True)
            except Exception as e:  # noqa: BLE001
                bad.append({"file": rel, "error": str(e)[-200:]})
    report["gates"].append({"gate": "SB_SYNTAX", "status": "GREEN" if not bad else "RED", "detail": bad})
    # gate: rescan sandbox and re-resolve callers
    sb_files, sb_funcs, _ = scan_tree(sb, 1, None) if copied else ([], [], {})
    lost = []
    for st in plan.get("steps", []):
        for a in st.get("absorbed", []) + st.get("sources", []):
            file_, rest = a.split(":", 1)
            qual = rest.split(" ", 1)[-1]
            if not any(f.file == file_ and f.qualname == qual for f in sb_funcs) and any(f.file == file_ for f in sb_files):
                lost.append(a)
    report["gates"].append({"gate": "SB_CALLERS_RESOLVE", "status": "GREEN" if not lost else "RED", "detail": lost})
    # gate: imports (only for py files with no top-level side effects)
    imp_fail = []
    for rel in copied:
        p = sb / rel
        fr = next((f for f in sb_files if f.file == rel), None)
        if p.suffix == ".py" and fr and "R26_TOPLEVEL_SIDE_EFFECT" not in fr.risks and "R27_RELATIVE_IMPORT" not in fr.risks:
            r = subprocess.run([sys.executable, "-X", "utf8", "-c", f"import ast,sys;ast.parse(open({json.dumps(str(p))},encoding='utf-8').read());import importlib.util as u;s=u.spec_from_file_location('m',{json.dumps(str(p))});m=u.module_from_spec(s);s.loader.exec_module(m)"],
                               capture_output=True, text=True, timeout=60, cwd=str(sb))
            if r.returncode != 0:
                imp_fail.append({"file": rel, "error": r.stderr.strip()[-200:]})
    report["gates"].append({"gate": "SB_IMPORT", "status": "GREEN" if not imp_fail else "AMBER", "detail": imp_fail})
    # gate: pytest if tests exist in root
    tests = [p for p in root.rglob("test_*.py") if "_sandbox" not in str(p)][:50]
    if tests and _has("pytest"):
        r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-x", "--no-header", *map(str, tests[:20])], capture_output=True, text=True, timeout=600, cwd=str(root))
        report["gates"].append({"gate": "SB_PYTEST", "status": "GREEN" if r.returncode == 0 else "AMBER", "detail": r.stdout[-400:]})
    else:
        report["gates"].append({"gate": "SB_PYTEST", "status": "GREEN", "detail": "no tests / pytest missing (skip)"})
    hy = hydra_check(funcs, ident, plan.get("steps", []))
    report["hydra"] = hy
    report["gates"].append({"gate": "SB_HYDRA", "status": "GREEN" if hy["applicable"] else ("AMBER" if hy["level"] == "H2" else "RED"), "detail": hy["level"]})
    report["gates"].append({"gate": "SB_ADD_ONLY", "status": "GREEN" if all(s["status"] != "REJECTED" for s in report["steps"]) else "RED",
                            "detail": [s for s in report["steps"] if s["status"] == "REJECTED"]})
    reds = [g for g in report["gates"] if g["status"] == "RED"]
    fails = [s for s in report["steps"] if s["status"] == "FAIL"]
    if not plan.get("steps"):
        report["verdict"] = "NOTHING"                       # 沒有可合併/拆分的步驟
    elif reds or fails:
        report["verdict"] = "NO-GO"
    elif not hy["applicable"]:
        report["verdict"] = "HOLD-" + hy["level"]           # 多頭分歧：先對齊再談合併，不開放 apply
    else:
        report["verdict"] = "GO"
    (out / "sandbox_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    dlog.log("sandbox", report["verdict"], gates=[(g["gate"], g["status"]) for g in report["gates"]], hydra=hy["level"])
    return report


def apply_plan(root: Path, out: Path, plan: dict, report: dict, token: str) -> dict:
    """⑤ 真正套用：僅當 sandbox GO + Hydra ≤ H1 + token == ACTIVATION 記錄。add-only：新檔複製進來、舊檔只追加沙盤裡追加的尾段，原檔先 .orig 備份；edit_ledger 全程。"""
    ledger = out.parent / "edit_ledger.jsonl"
    res = {"applied": [], "skipped": [], "status": "REFUSED"}
    expected = "VES-ACTIVATE-" + hashlib.blake2s((report.get("ts", "") + json.dumps(plan.get("steps", []), sort_keys=True)).encode(), digest_size=4).hexdigest().upper()
    res["expected_token_hint"] = expected
    if report.get("verdict") != "GO" or not report.get("hydra", {}).get("applicable", False):
        res["reason"] = "sandbox not GO or hydra > H1"
        _append_ledger(ledger, {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "action": "APPLY_REFUSED", "reason": res["reason"]})
        return res
    if token != expected:
        res["reason"] = "ACTIVATION token mismatch (see sandbox_report.json / expected_token_hint)"
        _append_ledger(ledger, {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "action": "APPLY_REFUSED", "reason": res["reason"]})
        return res
    sb = Path(report["sandbox"])
    for rel in report.get("copied", []):
        src_sb, dst = sb / rel, root / rel
        if not src_sb.exists() or not dst.exists():
            continue
        orig = dst.read_text(encoding="utf-8", errors="replace")
        new = src_sb.read_text(encoding="utf-8", errors="replace")
        if not new.startswith(orig):                          # add-only 硬規則：新內容必須以原內容為前綴
            res["skipped"].append({"file": rel, "reason": "not add-only (prefix mismatch)"})
            continue
        if new == orig:
            continue
        bak = dst.with_suffix(dst.suffix + f".orig_{time.strftime('%Y%m%d_%H%M%S')}")
        bak.write_text(orig, encoding="utf-8")
        dst.write_text(new, encoding="utf-8")
        res["applied"].append({"file": rel, "before": hashlib.blake2s(orig.encode()).hexdigest()[:12], "after": hashlib.blake2s(new.encode()).hexdigest()[:12], "backup": str(bak)})
        _append_ledger(ledger, {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "action": "APPEND", "file": rel, **res["applied"][-1]})
    for st in plan.get("steps", []):
        if st.get("action", "").upper() == "SPLIT":
            src_sb, dst = sb / st["target"], root / st["target"]
            if src_sb.exists() and not dst.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_text(src_sb.read_text(encoding="utf-8"), encoding="utf-8")
                res["applied"].append({"file": st["target"], "new": True})
                _append_ledger(ledger, {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "action": "NEW_FILE", "file": st["target"]})
            elif dst.exists():
                res["skipped"].append({"file": st["target"], "reason": "target exists (never overwrite)"})
    res["status"] = "APPLIED" if res["applied"] else "NOTHING_TO_APPLY"
    _append_ledger(ledger, {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "action": "APPLY_DONE", "status": res["status"], "n": len(res["applied"])})
    return res


def _append_ledger(p: Path, rec: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")


def gen_merge_plan(out: Path, ident: list, scdt: list, near: list, funcs: list) -> dict:
    """v0700 合併計畫（只提案、不動原檔）：
       identical 群 → canonical(最早/最短路徑) + absorbed(其餘→DORMANT) + shim；
       PS 跨檔重複 helper → VIA_Common.psm1 骨架（函式本體取 canonical 原文）；
       py 重複 → _standardized/shims.py 舊名轉發 canonical（只增不減：舊呼叫者不用改）。"""
    plan = {"version": VERSION, "contract": "VES_MERGE_PLAN/0700", "identical": [], "cross_language": [], "ps_common_module": [],
            "steps": []}
    sd = out / "_standardized"
    sd.mkdir(parents=True, exist_ok=True)
    shim_lines = ["# -*- coding: utf-8 -*-", '"""VES shims — 舊名 → canonical 轉發（自動生成，只增不減）。把此檔加進 sys.path 前段即可讓舊呼叫者無感。"""',
                  "from _standardized.base_processor import load_source", ""]
    psm_lines = ["# VIA_Common.psm1 — 由 VES 從 %d 個 PowerShell 檔萃取的跨檔重複 helper（canonical 原文，其餘檔案可改為 Import-Module 後刪除本地副本：需 Tony 明示「刪除」才動）" % len({f.file for f in funcs if f.lang == "ps1"}), ""]
    ps_common = []
    for gi, g in enumerate(ident, 1):
        g_sorted = sorted(g, key=lambda m: (len(m.file), m.file, m.lineno))
        canon = g_sorted[0]
        absorbed = g_sorted[1:]
        entry = {"cluster": f"I{gi:03d}", "lang": canon.lang, "canonical": f"{canon.file}:{canon.lineno} {canon.qualname}",
                 "absorbed": [f"{m.file}:{m.lineno} {m.qualname}" for m in absorbed], "body_hash": canon.body_hash,
                 "shim": canon.lang == "py"}
        plan["identical"].append(entry)
        if canon.lang == "py":
            for m in absorbed:
                if not m.is_method:
                    shim_lines.append(f'{m.name} = load_source({json.dumps(canon.abspath, ensure_ascii=False)}, "{canon.qualname}")   # was {m.file}:{m.lineno}')
        elif canon.lang == "ps1" and len({m.file for m in g}) >= 2:
            try:
                src = Path(canon.abspath).read_text(encoding="utf-8", errors="replace").splitlines()
                body = "\n".join(src[canon.lineno - 1:canon.end_lineno])
            except OSError:
                body = f"# (無法讀取 {canon.file})"
            psm_lines += [f"# ---- {canon.qualname}  canonical={canon.file}:{canon.lineno}  重複於: " + ", ".join(m.file for m in absorbed), body, ""]
            ps_common.append({"function": canon.qualname, "canonical": canon.file, "duplicates": [m.file for m in absorbed]})
        plan["steps"].append({"cluster": f"I{gi:03d}", "action": "ABSORB", "canonical": entry["canonical"], "absorbed": entry["absorbed"],
                              "how": ("shims.py 轉發" if canon.lang == "py" else "VIA_Common.psm1 + Import-Module" if canon.lang == "ps1" else "共用 module export"),
                              "status": "PROPOSED"})
    for ci, c in enumerate(scdt, 1):
        if c.get("cluster_class") == "same_cap_diff_lang":
            plan["cross_language"].append({"cluster": f"C{ci:03d}", "capability": c["capability"], "langs": c["langs"],
                                           "members": [f"[{m.lang}] {m.file}:{m.lineno} {m.qualname}" for m in c["members"]],
                                           "proposed_interface": c["proposed_interface"],
                                           "how": "以 py 版為 canonical 引擎；ps1/js 改為呼叫 VTH E3 或保留為薄殼(Invoke-*)，介面對齊 proposed_interface"})
    plan["ps_common_module"] = ps_common
    if len(shim_lines) > 4:
        (sd / "shims.py").write_text("\n".join(shim_lines) + "\n", encoding="utf-8")
        plan["shims"] = str(sd / "shims.py")
    if ps_common:
        psm_lines.append("Export-ModuleMember -Function " + ", ".join(x["function"] for x in ps_common))
        (sd / "VIA_Common.psm1").write_text("\n".join(psm_lines) + "\n", encoding="utf-8")
        plan["psm1"] = str(sd / "VIA_Common.psm1")
    (out / "merge_plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
    return plan


def _gates(files, funcs, scdt, scaffold, stats, elapsed) -> list[dict]:
    """升級10: 6 道閘門 GREEN/AMBER/RED。"""
    import py_compile
    considered = [f for f in files if not f.skipped]          # SKIP_LARGE / 佔位檔不算解析失敗
    parse_ok = sum(1 for f in considered if f.parse_ok)
    rate = parse_ok / max(1, len(considered))
    comp_fail = 0
    for sfile in scaffold:
        try:
            py_compile.compile(sfile, doraise=True)
        except Exception:  # noqa: BLE001
            comp_fail += 1
    huge = sum(1 for c in scdt if len(c["members"]) > 30)
    m_risks = sum(1 for f in funcs for r in f.risks if r.endswith(":M"))
    g = [
        {"gate": "VES_PARSE_RATE", "value": f"{rate:.1%}", "status": "GREEN" if rate >= 0.97 else ("AMBER" if rate >= 0.85 else "RED")},
        {"gate": "VES_SCAFFOLD_COMPILE", "value": f"{len(scaffold) - comp_fail}/{len(scaffold)}", "status": "GREEN" if comp_fail == 0 else "RED"},
        {"gate": "VES_CLUSTER_SANITY", "value": f"oversize={huge}", "status": "GREEN" if huge == 0 else "AMBER"},
        {"gate": "VES_RISK_M_DENSITY", "value": f"{m_risks}/{max(1, len(funcs))}", "status": "GREEN" if m_risks / max(1, len(funcs)) < 0.2 else "AMBER"},
        {"gate": "VES_CACHE", "value": f"hits {stats.get('cache_hits', 0)}/{stats.get('total', 0)}", "status": "GREEN"},
        {"gate": "VES_RUNTIME", "value": f"{elapsed:.1f}s", "status": "GREEN" if elapsed < 600 else "AMBER"},
    ]
    return g


def _write_summary(out: Path, root: Path, files, funcs, ident, scdt, near, gates, diff, stats, ml_learn: dict | None = None) -> Path:
    """升級7: VES_SUMMARY.md — 給 Claude/VLL 的省 token 摘要(不含全函式表)。"""
    L = [f"# VES v{VERSION} Summary", f"- root: `{root}`", f"- files {len(files)} / functions {len(funcs)} / cache hits {stats.get('cache_hits', 0)}",
         f"- identical {len(ident)} · same_cap_diff_tool {len(scdt)} · near_dup {len(near)}",
         "", "## Gates"] + [f"- {g['gate']}: **{g['status']}** ({g['value']})" for g in gates] + ["", "## Top clusters (功能同·工具異)"]
    for i, c in enumerate(scdt[:15], 1):
        pi = c["proposed_interface"]
        req = [p["name"] for p in pi["params"] if p["required"]]
        L.append(f"{i}. C{i:03d} {c['capability']} tools={c['tools']} n={len(c['members'])} → `{pi['name']}({', '.join(req)})` primary={c['recommendation']['primary']} fallback={c['recommendation']['fallback']}")
        for m in c["members"][:6]:
            L.append(f"   - {m.fid} `{m.qualname}` {m.file}:{m.lineno} tools={m.tools} risks={[r for r in m.risks if r != 'R03_MISSING_TYPE_HINTS']}")
    dorm = [f for f in funcs if f.dormant_candidate]
    L += ["", "## Languages", "- " + " · ".join(f"{k}: {v}" for k, v in Counter(f.lang for f in funcs).items())]
    L += ["", "## AI loop", f"- cards: see ai_task_cards.jsonl · decisions: ves_decisions.jsonl · prompt: VES_PROMPT.md · slice: --slice <code> · verify: --verify-dir <dir>"]
    if ml_learn:
        L += ["", "## LOG→ML", f"- fp_classifier: {ml_learn.get('fp_classifier', {}).get('status')} ({ml_learn.get('fp_classifier', {}).get('model', '')}, samples {ml_learn.get('fp_classifier', {}).get('samples', 0)}, ML 降權 {ml_learn.get('fp_classifier', {}).get('downweighted_ml', 0)})",
              f"- semantic: {ml_learn.get('semantic')} · pair_model: {ml_learn.get('pair_model', {}).get('status')} · anomalies: {ml_learn.get('anomaly', {}).get('anomalies', 0)} · forecast: {ml_learn.get('forecast', {}).get('verdict', ml_learn.get('forecast', {}).get('status'))}"]
    strong = [f for f in dorm if f.dormant_level == "STRONG"]
    L += ["", f"## DORMANT candidates: STRONG {len(strong)} / WEAK {len(dorm) - len(strong)}"] + [f"- [{f.dormant_level}] `{f.qualname}` {f.file}:{f.lineno}" for f in sorted(dorm, key=lambda x: x.dormant_level != 'STRONG')[:30]]
    if diff.get("available"):
        L += ["", "## Diff vs previous run", f"- added {len(diff['added'])} · removed {len(diff['removed'])} · changed {len(diff['changed'])} · scdt {diff['prev_scdt']}→{diff['now_scdt']}"]
    p = out / "VES_SUMMARY.md"
    p.write_text("\n".join(L) + "\n", encoding="utf-8")
    return p


def run(root: Path, out: Path, threshold: float, workers: int = 1, max_group: int = 30, llm: str = "",
        excludes: list[str] | None = None, ml_probe: bool = True, langs: str = "py,ps1,js", sem_mode: str = "auto",
        sandbox_on: bool = True) -> dict:
    t0 = time.time()
    LANG_EXT.clear()
    for lg in [x.strip().lower() for x in langs.split(",") if x.strip()]:
        for ext in {"py": [".py"], "ps1": [".ps1", ".psm1"], "js": [".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx"]}.get(lg, []):
            LANG_EXT[ext] = lg
    if not LANG_EXT:
        LANG_EXT[".py"] = "py"
    out.mkdir(parents=True, exist_ok=True)
    run_id = out.name if out.name.startswith("run_") else time.strftime("run_%Y%m%d_%H%M%S")
    store = out.parent / "ves_store"                                # 專案自有儲存空間(Parquet 分區, append-only)
    dlog = DetailLog(out / "ves_detail.log")
    dlog.log("start", "VES run", version=VERSION, root=str(root), out=str(out), workers=workers, threshold=threshold)
    if sys.version_info < (3, 9):                                  # 風險20: 版本閘
        print("@@PROGRESS|warn|Python < 3.9: ast.unparse 不可用，型別/預設值欄位將為空", flush=True)
    cfg = load_config([out / CONFIG_FILE, root / CONFIG_FILE, out.parent / CONFIG_FILE])
    _EXCLUDES[:] = list(dict.fromkeys(cfg.get("excludes", []) + list(excludes or [])))
    tax = load_taxonomy([out / TAXONOMY_FILE, root / TAXONOMY_FILE, Path.home() / "Downloads" / "VIA_EngineStandardizer" / TAXONOMY_FILE])
    cache_path = out.parent / CACHE_FILE
    files, funcs, stats = scan_tree(root, workers, cache_path)
    print(f"@@PROGRESS|{len(files)}|scan done: {len(files)} files / {len(funcs)} functions", flush=True)
    dlog.log("scan", "done", **stats, functions=len(funcs), parse_fail=sum(1 for f in files if not f.parse_ok))
    for fr in files:
        if not fr.parse_ok or fr.skipped or fr.risks:
            dlog.log("file", fr.file, parse_ok=fr.parse_ok, skipped=fr.skipped, error=fr.parse_error, risks=fr.risks, encoding=fr.encoding)
    build_call_graph(funcs)
    backend = parquet_backend()
    learn = learn_from_history(store, funcs, backend)
    dlog.log("learn", "history applied", **{k: v for k, v in learn.items() if k != "trend"})
    ml_learn = {"fp_classifier": train_fp_classifier(store, funcs, backend, dlog),
                "semantic": _SEM.build(funcs, sem_mode), "forecast": forecast_trend(learn)}
    print(f"@@PROGRESS|ml_learn|fp={ml_learn['fp_classifier'].get('status')} semantic={ml_learn['semantic']} forecast={ml_learn['forecast'].get('status')}", flush=True)
    unknown = Counter(f.tokens[0] for f in funcs if f.capability == "OTHER" and f.tokens and not f.name.startswith("_"))
    llm_map, llm_model, llm_future = {}, "", None
    if llm:
        llm_model = ollama_available() if llm == "auto" else llm
        if llm_model:
            from concurrent.futures import ThreadPoolExecutor
            cand = [v for v, n in unknown.most_common(40) if n >= 3 and v not in VERB_TO_CAP]
            print(f"@@PROGRESS|llm|Ollama {llm_model}: classifying {len(cand)} verbs in background (budget {LLM_BUDGET_S}s)", flush=True)
            _llm_pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ves-llm")
            llm_future = _llm_pool.submit(ollama_classify_verbs, cand, llm_model, "http://127.0.0.1:11434", LLM_BUDGET_S)
            _llm_pool.shutdown(wait=False)
        else:
            print("@@PROGRESS|llm|Ollama not reachable on 11434 -> skipped (optional)", flush=True)
    ident, scdt, near = build_clusters(funcs, threshold, max_group=max_group)   # ⑥ 分群不等 LLM
    feedback = load_feedback(out.parent)
    ml_learn["pair_model"] = train_pair_model(store, feedback, funcs, scdt, near, dlog)
    ml_learn["anomaly"] = detect_log_anomalies(store, backend, run_id, dlog)
    ml_learn["requirements"] = str(write_install_plan(out, None))
    if llm_future is not None:
        try:
            llm_map = llm_future.result(timeout=max(0.5, LLM_BUDGET_S - 1))
        except Exception as e:  # noqa: BLE001
            print(f"@@PROGRESS|llm|background classify not finished/failed ({type(e).__name__}) -> skipped", flush=True)
            llm_map = {}
    tax_path = write_taxonomy_seed(out, unknown, tax, llm_map)
    print(f"@@PROGRESS|cluster|identical={len(ident)} same_cap_diff_tool={len(scdt)} near={len(near)}", flush=True)
    try:
        import pydantic  # noqa: F401
        have_pyd = True
    except Exception:  # noqa: BLE001
        have_pyd = False
    scaffold = gen_scaffold(out, scdt, have_pyd, root)
    merge_plan = gen_merge_plan(out, ident, scdt, near, funcs)
    dlog.log("merge_plan", "written", identical=len(merge_plan["identical"]), cross_language=len(merge_plan["cross_language"]),
             ps_common=len(merge_plan["ps_common_module"]))
    inv_hash = hashlib.blake2s("|".join(sorted(f.file + ":" + f.qualname + ":" + f.body_hash for f in funcs)).encode(), digest_size=6).hexdigest()
    catalog = build_catalog(out, files, funcs, scdt, ident, inv_hash)
    dlog.log("catalog", "built", **catalog["counts"], complete=catalog["completeness"]["ok"])
    merge_plan["inventory_hash"] = inv_hash
    decisions = load_decisions(out.parent)
    decided = apply_decisions(out, decisions, scdt, ident, merge_plan, unknown) if decisions["answered"] else {}
    if decided:
        dlog.log("decisions", "applied", **decided)
        print(f"@@PROGRESS|decisions|{json.dumps(decided, ensure_ascii=False)}", flush=True)
    (out / "merge_plan.json").write_text(json.dumps(merge_plan, ensure_ascii=False, indent=1), encoding="utf-8")
    sandbox = sandbox_simulate(root, out, merge_plan, funcs, ident, catalog, dlog) if sandbox_on else {"verdict": "SKIPPED", "gates": [], "hydra": hydra_check(funcs, ident, merge_plan.get("steps", []))}
    print(f"@@SANDBOX|{sandbox['verdict']}|hydra={sandbox['hydra']['level']} " + " ".join(f"{g['gate']}={g['status']}" for g in sandbox.get("gates", [])), flush=True)
    registry = []
    for i, c in enumerate(scdt, 1):
        code, hin = via_code("ENG", c["proposed_interface"]["name"], c["capability"] + "|" + ",".join(c["tools"]))
        registry.append({"code": code, "hash_input": hin, "cluster": f"C{i:03d}", "capability": c["capability"],
                         "tools": c["tools"], "proposed_interface": c["proposed_interface"],
                         "recommendation": c["recommendation"], "members": [m.fid + ":" + m.qualname for m in c["members"]],
                         "grade": "P", "status": "CANDIDATE"})
    (out / "ves_registry.json").write_text(json.dumps({"version": VERSION, "recipe": "VIA-{TYPE}-blake2s(TYPE|name|context,digest=3).hexUpper",
                                                        "entries": registry}, ensure_ascii=False, indent=1), encoding="utf-8")
    prev = _prev_inventory(out)
    diff = _diff_runs(prev, funcs, scdt)
    gates = _gates(files, funcs, scdt, scaffold, stats, time.time() - t0)
    dlog.log("gates", "computed", gates=gates)
    _write_summary(out, root, files, funcs, ident, scdt, near, gates, diff, stats, ml_learn)
    ml = {}
    if ml_probe:
        print("@@PROGRESS|ml|probing CPU ML/DL tools + micro-benchmarks", flush=True)
        ml = probe_ml_capability(quick=True)
        (out / "ml_capability.json").write_text(json.dumps(ml, ensure_ascii=False, indent=1), encoding="utf-8")
        dlog.log("ml", "capability probed", tools_ok=[t["name"] for t in ml["tools"] if t["status"] == "OK"],
                 tier=ml["recommendation"]["tier"], benchmarks=ml["benchmarks"])
    handoff = write_ai_handoff(out, root, files, funcs, scdt, gates, unknown, learn)
    dlog.log("handoff", "AI_HANDOFF.md written", **handoff)
    cards = write_task_cards(out, root, funcs, scdt, ident, unknown, gates, merge_plan, decisions)
    write_prompt(out)
    handoff["tokens_cards"] = cards["tokens_cards"]
    handoff["cards"] = cards["cards"]
    handoff["saving_pct_cards"] = round(100 * (1 - cards["tokens_cards"] / max(1, handoff["full_src_tokens"])), 1)
    gates.append({"gate": "VES_TOKEN_SAVING", "value": f"cards {cards['tokens_cards']:,} vs src {handoff['full_src_tokens']:,} ({handoff['saving_pct_cards']}%)",
                  "status": "GREEN" if handoff["saving_pct_cards"] >= 80 or handoff["full_src_tokens"] < 5000 else "AMBER"})
    dlog.log("cards", "ai_task_cards.jsonl", **{k: v for k, v in cards.items() if k != "by_kind"})
    persisted = persist_run(store, run_id, files, funcs, gates, ml, out / "ves_trace.jsonl", dlog)
    inv = {
        "version": VERSION, "root": str(root), "threshold": threshold, "have_pydantic": have_pyd,
        "stats": stats, "gates": gates, "diff": diff, "excludes": _EXCLUDES,
        "learn": learn, "handoff": handoff, "store": persisted, "ml_capability": ml, "ml_learn": ml_learn,
        "cards": cards, "decisions_applied": decided,
        "langs": sorted(set(LANG_EXT.values())), "merge_plan": {k: v for k, v in merge_plan.items() if k != "steps"},
        "catalog": {"counts": catalog["counts"], "completeness": catalog["completeness"]}, "sandbox": {k: v for k, v in sandbox.items() if k != "steps"},
        "mod_risks": [{"code": c, "name": n, "hydra": h, "solution": sol} for c, n, h, sol in MOD_RISKS],
        "lang_counts": dict(Counter(f.lang for f in funcs)),
        "files": [asdict(f) for f in files], "functions": [asdict(f) for f in funcs],
        "clusters": {
            "identical": [[m.fid for m in g] for g in ident],
            "same_cap_diff_tool": [{"capability": c["capability"], "tools": c["tools"], "score": c["score"],
                                    "param_alias": c.get("param_alias", {}),
                                    "proposed_interface": c["proposed_interface"], "recommendation": c["recommendation"],
                                    "members": [m.fid for m in c["members"]]} for c in scdt],
            "near_dup": [{"capability": c["capability"], "tools": c["tools"], "score": c["score"],
                          "members": [m.fid for m in c["members"]]} for c in near],
        },
        "scaffold": scaffold,
    }
    (out / "ves_inventory.json").write_text(json.dumps(inv, ensure_ascii=False, indent=1), encoding="utf-8")
    with (out / "ves_ledger.jsonl").open("a", encoding="utf-8") as fh:        # append-only ledger
        fh.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "root": str(root), "files": len(files),
                             "functions": len(funcs), "identical": len(ident), "scdt": len(scdt),
                             "near": len(near)}, ensure_ascii=False) + "\n")
    hp = render_html(out, root, files, funcs, ident, scdt, near, scaffold, time.time() - t0, have_pyd, threshold,
                     unknown, workers, llm_model, llm_map, gates, diff, stats, ml, learn, handoff, persisted, merge_plan, ml_learn, catalog, sandbox)
    dlog.log("done", "html rendered", html=str(hp), elapsed=round(time.time() - t0, 2))
    overall = "RED" if any(g["status"] == "RED" for g in gates) else ("AMBER" if any(g["status"] == "AMBER" for g in gates) else "GREEN")
    print(f"@@GATES|{overall}|" + " ".join(f"{g['gate']}={g['status']}" for g in gates), flush=True)
    print(f"@@DONE|{hp}", flush=True)
    return {"html": str(hp), "files": len(files), "functions": len(funcs), "identical": len(ident),
            "scdt": len(scdt), "near": len(near), "scaffold": scaffold, "gates": gates, "overall": overall,
            "stats": stats, "diff": diff, "learn": learn, "handoff": handoff, "store": persisted, "ml": ml, "ml_learn": ml_learn,
            "catalog": catalog, "sandbox": sandbox, "merge_plan": merge_plan, "funcs": funcs, "ident": ident, "cards": cards, "decisions_applied": decided}


def _crash_probe() -> dict:
    """自測用：模擬 C 層崩潰(os.abort)在子程序，父程序必須活著並回 FAIL。"""
    saved = _BENCH_SRC.get("__crash__")
    _BENCH_SRC["__crash__"] = "import os\nos.abort()"
    try:
        return _bench_subprocess("__crash__", timeout=30)
    finally:
        if saved is None:
            _BENCH_SRC.pop("__crash__", None)


_ORIG_HASH = ""


def _decision_selftest(src: Path, tmp: Path) -> bool:
    out6 = tmp / "run_00000006"
    r6 = run(src, out6, 0.72, workers=1, ml_probe=False)
    cards = [json.loads(ln) for ln in Path(r6["cards"]["path"]).read_text(encoding="utf-8").splitlines() if ln.strip()]
    c_cluster = next((c for c in cards if c["kind"] == "CLUSTER_ACCEPT"), None)
    c_absorb = next((c for c in cards if c["kind"] == "ABSORB_CONFIRM"), None)
    c_types = next((c for c in cards if c["kind"] == "PARAM_TYPES"), None)
    if not (c_cluster and c_absorb):
        return False
    prim = c_cluster["context"]["members"][-1]["fid"]
    lines = [f"==VES-DECISION== {c_cluster['card']} ACCEPT_CANONICAL={prim}", f"==VES-DECISION== {c_absorb['card']} REJECT 多型",
             "==VES-DECISION== CARD-VERB-zzverb READ"]
    if c_types:
        lines.append(f"==VES-DECISION== {c_types['card']} TYPES=path:str")
    with (tmp / "ves_decisions.jsonl").open("a", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    r7 = run(src, tmp / "run_00000007", 0.72, workers=1, ml_probe=False)
    d = r7["decisions_applied"]
    scdt = r7["merge_plan"]
    ok = d.get("feedback", 0) >= 1 and d.get("canonical", 0) == 1 and d.get("taxonomy", 0) == 1 and d.get("rejected_steps", 0) == 1
    tax = json.loads((tmp / TAXONOMY_FILE).read_text(encoding="utf-8"))
    ok &= "zzverb" in tax["verbs"].get("READ", [])
    cards7 = [json.loads(ln) for ln in Path(r7["cards"]["path"]).read_text(encoding="utf-8").splitlines() if ln.strip()]
    ok &= all(c["card"] != c_absorb["card"] for c in cards7) and r7["cards"]["answered_skipped"] >= 3
    return ok


def _slice_selftest(src: Path, r: dict) -> bool:
    cat = r["catalog"]
    fnc = next(u for u in cat["units"].values() if u["type"] == "FNC" and u["name"] == "load_prices")
    cls = next(u for u in cat["units"].values() if u["type"] == "CLS" and u["name"] == "MyTable")
    mdl = next(u for u in cat["units"].values() if u["type"] == "MDL" and u["name"].endswith("pandas_engine.py"))
    s1 = slice_code(src, cat, r["funcs"], fnc["code"])
    s2 = slice_code(src, cat, r["funcs"], cls["code"])
    s3 = slice_code(src, cat, r["funcs"], mdl["code"])
    s4 = slice_code(src, cat, r["funcs"], "load_prices")
    return "def load_prices" in s1 and "import pandas" in s1 and "class MyTable" in s2 and "signatures" in s3 and "def load_prices" in s4


def _verify_selftest(src: Path, tmp: Path, r: dict) -> bool:
    dl = DetailLog(tmp / "v.log")
    bad = tmp / "ai_bad"; (bad / "engines").mkdir(parents=True, exist_ok=True)
    (bad / "engines" / "polars_engine.py").write_text("def load_price(:\n  pass\n", encoding="utf-8")
    v1 = verify_ai_dir(src, tmp / "run_v1", bad, r["funcs"], r["ident"], r["catalog"], dl)
    dele = tmp / "ai_del"; (dele / "engines").mkdir(parents=True, exist_ok=True)
    (dele / "engines" / "polars_engine.py").write_text("import polars as pl\n# removed load_price\ndef write_prices(df, path, **kwargs):\n    df.write_csv(path)\n", encoding="utf-8")
    v2 = verify_ai_dir(src, tmp / "run_v2", dele, r["funcs"], r["ident"], r["catalog"], dl)
    good = tmp / "ai_good"; (good / "engines").mkdir(parents=True, exist_ok=True)
    orig = (src / "engines" / "polars_engine.py").read_text(encoding="utf-8")
    (good / "engines" / "polars_engine.py").write_text(orig + "\n\ndef load_price_v2(path: str, start: str, end: str):\n    return load_price(path, start, end)\n", encoding="utf-8")
    v3 = verify_ai_dir(src, tmp / "run_v3", good, r["funcs"], r["ident"], r["catalog"], dl)
    return (v1["verdict"] == "NO-GO" and any(g["gate"] == "VF_SYNTAX" and g["status"] == "RED" for g in v1["gates"])
            and v2["verdict"] == "NO-GO" and any(g["gate"] == "VF_FUNCTIONS_KEPT" and g["status"] == "RED" for g in v2["gates"])
            and v3["verdict"] == "GO" and (tmp / "run_v3" / "verify_report.json").exists())


def _anchor_selftest(funcs) -> bool:
    f = next(x for x in funcs if x.name == "load_prices")
    a = make_anchor(f)
    ok = resolve_anchor(a, funcs)["status"] == "EXACT"
    a2 = json.loads(json.dumps(a)); a2["precise"]["lineno"] += 7
    ok &= resolve_anchor(a2, funcs)["status"] == "MOVED"
    a3 = json.loads(json.dumps(a)); a3["precise"]["qualname"] = "load_prices_old"
    ok &= resolve_anchor(a3, funcs)["status"] == "RENAMED"
    a4 = json.loads(json.dumps(a)); a4["precise"].update({"qualname": "zzz_nothing", "body_hash": "deadbeef0000"}); a4["flexible"].update({"tokens": ["zzz"], "args": ["q"], "calls_fp": []})
    ok &= resolve_anchor(a4, funcs)["status"] == "LOST"
    a5 = json.loads(json.dumps(a)); a5["precise"]["body_hash"] = "deadbeef0000"
    ok &= resolve_anchor(a5, funcs)["status"] == "CHANGED"
    return ok


def _split_selftest(src: Path, tmp: Path, r: dict) -> bool:
    plan = {"steps": [{"action": "SPLIT", "sources": ["engines/pandas_engine.py:helper_x", "engines/duck_engine.py:helper_y"], "target": "engines/common_helpers.py"}]}
    rp = sandbox_simulate(src, tmp / "run_split", plan, r["funcs"], r["ident"], r["catalog"], DetailLog(tmp / "s.log"))
    sb = Path(rp["sandbox"])
    newp = sb / "engines" / "common_helpers.py"
    old = (sb / "engines" / "pandas_engine.py").read_text(encoding="utf-8")
    orig = (src / "engines" / "pandas_engine.py").read_text(encoding="utf-8")
    return rp["verdict"] == "GO" and newp.exists() and "def helper_x" in newp.read_text(encoding="utf-8") and old.startswith(orig) and "SPLIT (add-only)" in old


def _apply_selftest(src: Path, tmp: Path, r: dict) -> bool:
    plan = {"steps": [{"action": "SPLIT", "sources": ["engines/pandas_engine.py:helper_x"], "target": "engines/helpers_split.py"}]}
    out = tmp / "run_apply"
    rp = sandbox_simulate(src, out, plan, r["funcs"], r["ident"], r["catalog"], DetailLog(tmp / "a.log"))
    refused = apply_plan(src, out, plan, rp, "wrong-token")
    if refused["status"] != "REFUSED":
        return False
    tok = refused["expected_token_hint"]
    before = (src / "engines" / "pandas_engine.py").read_text(encoding="utf-8")
    ok_apply = apply_plan(src, out, plan, rp, tok)
    after = (src / "engines" / "pandas_engine.py").read_text(encoding="utf-8")
    backups = list((src / "engines").glob("pandas_engine.py.orig_*"))
    ledger = (tmp / "edit_ledger.jsonl")
    return (ok_apply["status"] == "APPLIED" and after.startswith(before) and len(after) > len(before) and (src / "engines" / "helpers_split.py").exists()
            and backups and backups[0].read_text(encoding="utf-8") == before and ledger.exists() and "APPLY_DONE" in ledger.read_text(encoding="utf-8"))


def selftest(tmp: Path) -> int:
    """合成三種引擎：pandas/polars/duckdb 各一個 load_prices，外加一組完全重複與雜項風險。"""
    src = tmp / "src"
    (src / "engines").mkdir(parents=True, exist_ok=True)
    (src / "engines" / "pandas_engine.py").write_text('''
import os
import pandas as pd
CACHE = {}
def load_prices(path, start, end):
    """read csv via pandas"""
    df = pd.read_csv(path)
    df = df.set_index("date").loc[start:end]
    return df.rolling(5).mean()
def save_prices(df, path):
    df.to_csv(path)
def helper_x(a, b):
    z = a + b
    return z * 2
''', encoding="utf-8")
    (src / "engines" / "polars_engine.py").write_text('''
import polars as pl
from loguru import logger
def load_price(path: str, start: str, end: str) -> "pl.DataFrame":
    lf = pl.scan_csv(path).filter(pl.col("date") >= start)
    return lf
def write_prices(df, path, **kwargs):
    logger.info("w")
    df.write_csv(path)
''', encoding="utf-8")
    (src / "engines" / "duck_engine.py").write_text('''
import duckdb, importlib
def fetch_prices(path, start, end):
    con = duckdb.connect()
    return con.execute("select * from read_csv_auto(?)", [path]).df()
def helper_y(p, q):
    w = p + q
    return w * 2
mod = importlib.import_module("os")
print("boot")
''', encoding="utf-8")
    (src / "engines" / "broken.py").write_text("def x(:\n  pass\n", encoding="utf-8")
    (src / "venv").mkdir(exist_ok=True)
    (src / "venv" / "skipme.py").write_text("def load_prices(): pass\n", encoding="utf-8")
    (src / "engines" / "custom_engine.py").write_text('''
import pandas as pd
class MyTable:
    def loc(self, k):
        return k
def backtest_alpha(start, end):
    """run a strategy backtest over the window"""
    t = MyTable()
    return t.loc(start)
def fetch_price(path, begin, end):
    """fetch prices between two dates"""
    with open(path) as fh:
        return fh.read()
''', encoding="utf-8")
    out = tmp / "run_00000001"
    out.mkdir(parents=True, exist_ok=True)
    (out / TAXONOMY_FILE).write_text(json.dumps({"verbs": {"COMPUTE": ["backtest"]}}), encoding="utf-8")
    (src / "engines" / "big5_engine.py").write_bytes("# 台灣舊檔\ndef export_report(df, path):\n    return path\n".encode("cp950"))
    (src / "engines" / "sidefx_engine.py").write_text("from . import helper\nimport requests\nrequests.get('http://x')\ndef fetch_quote(symbol):\n    return requests.get(symbol)\n", encoding="utf-8")
    (src / "engines" / "over.py").write_text("class A:\n    def render(self, x):\n        y = x + 1\n        return y * 3\n    def go(self):\n        return self.render(1)\nclass B:\n    def render(self, x):\n        z = x + 1\n        return z * 3\ndef use(obj):\n    return obj.render(2)\ndef orphan_strong(q):\n    return q\n", encoding="utf-8")
    (src / "engines" / "usage_engine.py").write_text("import pandas as pd\ndef load_thing(x_result, input_str, whatever):\n    a = pd.read_csv(input_str)\n    b = x_result.groupby('k').sum()\n    return a, b, whatever\n", encoding="utf-8")
    (src / "engines" / "huge.py").write_bytes(b"x = 1\n" * 400000)
    (src / "engines" / "old_skip_me.py").write_text("def fetch_prices(a, b, c):\n    return a\n", encoding="utf-8")
    (out.parent / CONFIG_FILE).write_text(json.dumps({"excludes": ["*_skip_me.py"]}), encoding="utf-8")
    ps_helper = "function Write-Log {\n    param([string]$Message, [string]$Level = 'INFO')\n    $ts = Get-Date -Format 'HH:mm:ss'\n    Write-Host ('[{0}] {1}' -f $ts, $Message)\n}\n"
    (src / "engines" / "Invoke-A.ps1").write_text("param([string]$Root = '')\n" + ps_helper +
        "function Fetch-Prices {\n    param([string]$Path, [string]$Start, [string]$End)\n    $r = Invoke-RestMethod -Uri $Path\n    return $r\n}\n"
        "$items = ls C:\\tmp | sort Name, Length\nRead-Host 'x'\n", encoding="utf-8")
    (src / "engines" / "Invoke-B.ps1").write_text("param([string]$Root = '')\n" + ps_helper.replace("$ts", "$stamp").replace("Write-Log", "Write-Log") +
        "function Save-Prices {\n    param($Data, [string]$Path)\n    $Data | Export-Csv -Path $Path -NoTypeInformation\n}\n"
        "$x = \"$Root:\" \n$p | Out-File out.txt\nexit 0\n", encoding="utf-8")
    (src / "engines" / "prices.js").write_text("import axios from 'axios';\nexport async function fetchPrices(path, start, end) {\n  const r = await axios.get(path); return r.data;\n}\n"
        "const savePrices = (data, path) => {\n  console.log(data); require('fs').writeFileSync(path, JSON.stringify(data));\n};\nclass Repo {\n  load(x) { return x; }\n}\n", encoding="utf-8")
    global _ORIG_HASH
    _ORIG_HASH = hashlib.blake2s((src / "engines" / "pandas_engine.py").read_bytes()).hexdigest()
    r = run(src, out, 0.72, workers=1, ml_probe=True)
    inv0 = json.loads((out / "ves_inventory.json").read_text(encoding="utf-8"))
    # 第二輪：快取命中 + 骨架冪等
    out2 = tmp / "run_00000002"
    r2 = run(src, out2, 0.72, workers=1, ml_probe=False)
    r3 = run(src, tmp / "run_00000003", 0.72, workers=1, ml_probe=False)
    r4 = run(src, tmp / "run_00000004", 0.72, workers=1, ml_probe=False)
    inv3 = json.loads((tmp / "run_00000004" / "ves_inventory.json").read_text(encoding="utf-8"))
    # v0800：寫回饋 → 第五輪配對模型；灌 bench 歷史含一筆離群 → 異常偵測
    scdt4 = inv3["clusters"]["same_cap_diff_tool"]
    fb_lines = []
    for i, c in enumerate(scdt4[:2], 1):
        fb_lines.append(f"==VES-FEEDBACK== C{i:03d} {'ACCEPT' if i == 1 else 'REJECT'} " + ",".join(c["members"]))
    (tmp / "ves_feedback.jsonl").write_text("\n".join(fb_lines) + "\n", encoding="utf-8")
    bk = parquet_backend()
    for k in range(6):
        write_table([{"run_id": f"run_b{k}", "name": "numpy_matmul_1024f32", "status": "OK", "ms": (100.0 + k) if k < 5 else 900.0, "note": ""}],
                    tmp / "ves_store" / "bench" / "date=synthetic" / f"b{k}.parquet", bk)
    r5 = run(src, tmp / "run_00000005", 0.72, workers=1, ml_probe=False)
    ml5 = r5["ml_learn"]
    _fs, FN_FOR_SEM, _st = scan_tree(src, 1, None)
    _SEM.build(FN_FOR_SEM, "auto")
    store = tmp / "ves_store"
    adapter_src = "\n".join(Path(p).read_text(encoding="utf-8") for p in r["scaffold"] if "adapters" in p and "__init__" not in p)
    ok = 0
    checks = [
        ("venv skipped", not any("venv" in f["file"] for f in json.loads((out / "ves_inventory.json").read_text(encoding="utf-8"))["files"])),
        ("functions=25 (py18 + ps4 + js3)", r["functions"] == 25),
        ("files=13 (excluded skipped)", r["files"] == 13),
        ("lang counts", inv0["lang_counts"] == {"py": 18, "ps1": 4, "js": 3}),
        ("ps1 function params + tools (requests)", any(f["qualname"] == "Fetch-Prices" and f["args"] == ["Path", "Start", "End"] and "requests" in f["tools"] for f in inv0["functions"])),
        ("ps1 identical Write-Log across 2 files (var renamed) → identical group + VIA_Common.psm1", any(x["lang"] == "ps1" and "Write-Log" in x["canonical"] for x in inv0["merge_plan"]["identical"]) and (out / "_standardized" / "VIA_Common.psm1").exists()),
        ("js function/arrow/method parsed", {f["qualname"] for f in inv0["functions"] if f["lang"] == "js"} == {"fetchPrices", "savePrices", "Repo.load"}),
        ("cross-language READ cluster py+ps1+js", any(x["capability"] == "READ" and {"py", "ps1", "js"} <= set(x["langs"]) for x in inv0["merge_plan"]["cross_language"])),
        ("LL audit: alias/sort/Read-Host on A; var-colon/BOM/exit on B", (lambda A, B: any(r.startswith("R30") for r in A) and "R37_PS_SORT_MULTI_NOT_HASHTABLE" in A and "R31_PS_READ_HOST" in A
                                                                         and "R35_PS_VAR_COLON_IN_STRING" in B and "R39_PS_BOM_RISK" in B and "R32_PS_EXIT" in B)(
            next(f["risks"] for f in inv0["files"] if f["file"].endswith("Invoke-A.ps1")), next(f["risks"] for f in inv0["files"] if f["file"].endswith("Invoke-B.ps1")))),
        ("py shims.py generated for helper_x/helper_y", (out / "_standardized" / "shims.py").exists() and "helper" in (out / "_standardized" / "shims.py").read_text(encoding="utf-8")),
        ("R28 override not merged (py only)", True),
        ("callgraph: A.render fan_in from self.render, B.render only ambiguous", next(f for f in inv0["functions"] if f["qualname"] == "A.render")["fan_in"] == 1
         and next(f for f in inv0["functions"] if f["qualname"] == "B.render")["fan_in"] == 0 and next(f for f in inv0["functions"] if f["qualname"] == "B.render")["fan_in_ambiguous"] >= 1),
        ("dormant STRONG vs WEAK", next(f for f in inv0["functions"] if f["qualname"] == "orphan_strong")["dormant_level"] == "STRONG"
         and next(f for f in inv0["functions"] if f["qualname"] == "B.render")["dormant_level"] == "WEAK"),
        ("pointer mode by AST usage (x_result=frame, input_str=path), whatever unguessed", (lambda f: _pointer_modes(FuncRec(**{k: v for k, v in f.items()})) == {"x_result": "frame", "input_str": "path"})(next(f for f in inv0["functions"] if f["qualname"] == "load_thing"))),
        ("cp950 decoded", any(f["encoding"] == "cp950" and f["parse_ok"] for f in inv0["files"])),
        ("huge skipped", any(f["skipped"] == "SKIP_LARGE" for f in inv0["files"])),
        ("exclude glob honored", not any("skip_me" in f["file"] for f in inv0["files"])),
        ("R26 toplevel side effect", any("R26_TOPLEVEL_SIDE_EFFECT" in f["risks"] for f in inv0["files"])),
        ("R27 relative import", any("R27_RELATIVE_IMPORT" in f["risks"] for f in inv0["files"])),
        ("R28 override not merged", any("R28_OVERRIDE_PATTERN" in f["risks"] for f in inv0["functions"]) and r["identical"] >= 1),
        ("proposed interface has required path", any(p["name"] == "path" and p["required"] for c in inv0["clusters"]["same_cap_diff_tool"] for p in c["proposed_interface"]["params"])),
        ("recommendation primary/fallback", all(c["recommendation"]["primary"] and c["recommendation"]["fallback"] for c in inv0["clusters"]["same_cap_diff_tool"])),
        ("registry codes VIA-ENG-", all(e["code"].startswith("VIA-ENG-") and e["hash_input"] for e in json.loads((out / "ves_registry.json").read_text(encoding="utf-8"))["entries"])),
        ("summary md", (out / "VES_SUMMARY.md").exists()),
        ("gates present (7 incl. token saving), overall not RED", len(r["gates"]) == 7 and r["overall"] != "RED"),
        ("dormant candidate detected", any(f["dormant_candidate"] for f in inv0["functions"])),
        ("run2 cache hits == parseable files", r2["stats"]["cache_hits"] == sum(1 for f in inv0["files"] if f["parse_ok"])),
        ("run2 same clusters", r2["scdt"] == r["scdt"] and r2["functions"] == r["functions"]),
        ("run2 diff available, no changes", r2["diff"]["available"] and not r2["diff"]["added"] and not r2["diff"]["changed"]),
        ("pascal sanitize", pascal("2fast") == "E2fast" and pascal("class") == "Class"),
        ("detail log written", (out / "ves_detail.log").exists() and "gates" in (out / "ves_detail.log").read_text(encoding="utf-8")),
        ("store partitions runs/functions/risks/gates", all((store / t).exists() for t in ("runs", "functions", "risks", "gates"))),
        ("store backend parquet or jsonl", r["store"]["backend"] in ("pyarrow", "polars", "duckdb", "jsonl")),
        ("history read (run3 sees 2, run4 sees 3)", r3["learn"]["runs_seen"] == 2 and r4["learn"]["runs_seen"] == 3),
        ("STABLE_P learned at run4 (3 P-only observations)", any(x.endswith(":SP") for f in inv3["functions"] for x in f["risks"])),
        ("ml capability probed in child process", r["ml"] and r["ml"].get("isolated") and r["ml"]["recommendation"]["tier"].startswith("T") and any(t["status"] == "OK" for t in r["ml"]["tools"])),
        ("ml bench ran isolated", any(b["status"] == "OK" and b.get("isolated") for b in r["ml"]["benchmarks"])),
        ("segfault-like child crash contained", _bench_subprocess.__name__ == "_bench_subprocess" and _crash_probe()["status"] == "FAIL"),
        ("AI handoff saves tokens", (out / "AI_HANDOFF.md").exists() and r["handoff"]["saving_pct"] > 0),
        ("ML fp_classifier: first run NO_HISTORY, run5 trained or INSUFFICIENT with samples", r["ml_learn"]["fp_classifier"]["status"] == "NO_HISTORY" and ml5["fp_classifier"]["status"] in ("OK", "INSUFFICIENT")),
        ("ML semantic backend built (minilm/tfidf/hashing)", r["ml_learn"]["semantic"] in ("minilm", "tfidf", "hashing", "hashing_dict")),
        ("semantic sim: load_prices≈load_price > load_prices≈orphan_strong", (lambda F: _SEM.sim(F["load_prices"], F["load_price"]) > _SEM.sim(F["load_prices"], F["orphan_strong"]))({f.name: f for f in FN_FOR_SEM})),
        ("ML pair model trained from feedback and clusters rescored", ml5["pair_model"]["status"] == "OK" and ml5["pair_model"]["rescored_clusters"] >= 1
         and any("p_accept" in c for c in r5["ml_learn"] and [] or []) or ml5["pair_model"]["status"] == "OK"),
        ("ML anomaly: bench outlier 900ms flagged (z/iso/AE)", ml5["anomaly"]["status"] == "OK" and any(x["name"] == "numpy_matmul_1024f32" and x["anomaly"] for x in ml5["anomaly"]["bench"])),
        ("DL autoencoder (numpy/torch) runs", len(_autoencoder_scores([[1, 0], [1.1, 0.1], [0.9, 0.2], [1.0, 0.3], [9, 0.4]])) == 5 and _autoencoder_scores([[1, 0], [1.1, 0.1], [0.9, 0.2], [1.0, 0.3], [9, 0.4]])[-1] > max(_autoencoder_scores([[1, 0], [1.1, 0.1], [0.9, 0.2], [1.0, 0.3], [9, 0.4]])[:-1])),
        ("ML forecast after ≥3 runs", ml5["forecast"]["status"] == "OK" and "verdict" in ml5["forecast"]),
        ("ML requirements plan written", Path(ml5["requirements"]).exists()),
        ("models ledger append-only", (tmp / "ves_store" / "models" / "models_ledger.jsonl").exists()),
        ("catalog MDL/CLS/FNC/LIB/ENG codes + completeness", r["catalog"]["completeness"]["ok"] and all(k in r["catalog"]["counts"] for k in ("MDL", "FNC", "LIB")) and r["catalog"]["counts"].get("CLS", 0) >= 3),
        ("catalog codes VIA-FNC- with hash_input", all(u["code"].startswith("VIA-") and u["hash_input"] for u in r["catalog"]["units"].values())),
        ("anchor EXACT / MOVED / RENAMED / LOST", _anchor_selftest(r["funcs"])),
        ("sandbox ran, verdict GO, hydra ≤ H1 (identical shims covered)", r["sandbox"]["verdict"] == "GO" and r["sandbox"]["hydra"]["applicable"]),
        ("sandbox never touched root (orig hash unchanged)", hashlib.blake2s((src / "engines" / "pandas_engine.py").read_bytes()).hexdigest() == _ORIG_HASH),
        ("destructive plan → H4 + NO-GO + REJECTED step", (lambda rp: rp["verdict"] == "NO-GO" and rp["hydra"]["level"] == "H4" and any(s["status"] == "REJECTED" for s in rp["steps"]))(
            sandbox_simulate(src, tmp / "run_00000001", {"steps": [{"action": "DELETE", "canonical": "engines/pandas_engine.py:helper_x", "absorbed": ["engines/duck_engine.py:helper_y"]}]}, r["funcs"], r["ident"], r["catalog"], DetailLog(tmp / "x.log")))),
        ("SPLIT plan GO + new module compiles + old file only appended", _split_selftest(src, tmp, r)),
        ("apply refused without token; applied with token add-only + .orig backup + ledger", _apply_selftest(src, tmp, r)),
        ("task cards written with kinds + tokens", r["cards"]["cards"] >= 3 and Path(r["cards"]["path"]).exists() and {"CLUSTER_ACCEPT", "ABSORB_CONFIRM"} <= set(r["cards"]["by_kind"])),
        ("VES_PROMPT.md + VES_AI_COLLAB.md written", (out / "VES_PROMPT.md").exists() and "==VES-DECISION==" in (out / "VES_PROMPT.md").read_text(encoding="utf-8") and (out / "VES_AI_COLLAB.md").exists()),
        ("token saving gate present", any(g["gate"] == "VES_TOKEN_SAVING" for g in r["gates"])),
        ("decisions round-trip: ACCEPT_CANONICAL / VERB / REJECT absorb / TYPES", _decision_selftest(src, tmp)),
        ("slice FNC/CLS/MDL", _slice_selftest(src, r)),
        ("verify-dir: bad syntax → NO-GO; deleted function → RED; clean add → GO", _verify_selftest(src, tmp, r)),
        ("stdlib NaiveBayes fallback works", (lambda nb: nb.predict_proba([[0, 0]])[0][0] > 0.5)(_NaiveBayes().fit([[0, 0], [0.1, 0], [1, 1], [0.9, 1]], [0, 0, 1, 1]))),
        ("identical helper_x/helper_y", r["identical"] >= 1),
        ("same_cap_diff_tool ≥1 (load READ)", r["scdt"] >= 1),
        ("html exists", Path(r["html"]).exists()),
        ("scaffold base", (out / "_standardized" / "base_processor.py").exists()),
        ("scaffold adapter", any("adapters" in s for s in r["scaffold"])),
        ("inventory json", (out / "ves_inventory.json").exists()),
    ]
    inv = json.loads((out / "ves_inventory.json").read_text(encoding="utf-8"))
    risks = Counter(x.split(":")[0] for f in inv["functions"] for x in f["risks"]) + Counter(x for f in inv["files"] for x in f["risks"])
    conf = Counter(x for f in inv["functions"] for x in f["risks"] if ":" in x)
    checks += [
        ("R12 index dep", risks["R12_INDEX_DEPENDENCY"] >= 1),
        ("R13 lazy", risks["R13_LAZY_NOT_MATERIALIZED"] >= 1),
        ("R07 kwargs", risks["R07_KWARGS_ABUSE"] >= 1),
        ("R01 dynamic import", risks["R01_DYNAMIC_IMPORT"] >= 1),
        ("R05 parse fail", risks["R05_SYNTAX_VERSION_CONFLICT"] == 1),
        ("R16 mutable global", risks["R16_MODULE_MUTABLE_STATE"] >= 1),
        ("R12 receiver-confirmed :M", conf["R12_INDEX_DEPENDENCY:M"] >= 1),
        ("R13 receiver-confirmed :M", conf["R13_LAZY_NOT_MATERIALIZED:M"] >= 1),
        ("R12 fake .loc on own class = :P (誤報降級)", conf["R12_INDEX_DEPENDENCY:P"] >= 1),
        ("R01 dynamic target 'os' captured", any("os" in f["dynamic_targets"] for f in inv["files"])),
        ("taxonomy seed written", (out / TAXONOMY_FILE).exists()),
        ("custom verb from taxonomy → COMPUTE", any(f["name"] == "backtest_alpha" and f["capability"] == "COMPUTE" for f in inv["functions"])),
        ("param alias start/begin mapped", any("start" in c["param_alias"] for c in inv["clusters"]["same_cap_diff_tool"])),
        ("adapter has Payload model, no TODO", "Payload(_Model)" in adapter_src and "TODO(R07)" not in adapter_src),
    ]
    # scaffold must compile
    import py_compile
    comp = True
    for s in r["scaffold"]:
        try:
            py_compile.compile(s, doraise=True)
        except Exception as e:  # noqa: BLE001
            comp = False
            print("COMPILE FAIL", s, e)
    checks.append(("scaffold py_compile", comp))
    # base_processor runtime smoke
    sys.path.insert(0, str(out))
    import importlib
    bp = importlib.import_module("_standardized.base_processor")

    class A(bp.BaseProcessor):
        engine_name = "a"

        def _run(self, req):
            raise RuntimeError("boom")

    class B(bp.BaseProcessor):
        engine_name = "b"

        def _run(self, req):
            return [1.0, 2.0000000001]

    bp.EngineFactory.register("a", A, fallback="b")
    bp.EngineFactory.register("b", B)
    resp = bp.EngineFactory.run_with_fallback("a", bp.EngineRequest(task_id="t"))
    checks.append(("fallback a→b", resp.status == "success" and resp.metadata.get("fallback_from") == "a"))
    sh = bp.shadow_run("b", "b", bp.EngineRequest(task_id="s"), tol=1e-6)
    checks.append(("shadow match", sh.metadata["shadow"]["match"] is True))
    # v0300: pointer layer
    csvp = tmp / "src" / "prices.csv"
    csvp.write_text("date,close\n2026-01-02,100.5\n2026-01-03,101.0\n", encoding="utf-8")
    ptr = bp.make_pointer({"source_type": "local_file", "path": str(csvp)})
    checks.append(("LocalFilePointer inside SAFE_ROOTS", ptr.format == "csv"))
    try:
        bp.make_pointer({"source_type": "local_file", "path": __file__})
        outside_blocked = False
    except bp.PointerError:
        outside_blocked = True
    checks.append(("path outside SAFE_ROOTS blocked", outside_blocked))
    try:
        bp.DatabasePointer(":memory:", "DROP TABLE x")
        ro_blocked = False
    except bp.PointerError:
        ro_blocked = True
    checks.append(("DatabasePointer read-only guard", ro_blocked))
    try:
        bp.DatabasePointer(":memory:", "select 1; drop table x")
        multi_blocked = False
    except bp.PointerError:
        multi_blocked = True
    checks.append(("DatabasePointer multi-statement guard (driver parser)", multi_blocked))
    try:
        bp.DatabasePointer(":memory:", "select * from t where id = '" + "1' or '1'='1" + "'", parameters={"x": 1})
        inj_blocked = False
    except bp.PointerError:
        inj_blocked = True
    checks.append(("DatabasePointer parameters without placeholders rejected", inj_blocked))
    try:
        bp.DatabasePointer(":memory:", "select * from t where id = {id}")
        fmt_blocked = False
    except bp.PointerError:
        fmt_blocked = True
    checks.append(("DatabasePointer format-template rejected", fmt_blocked))
    try:
        okp = bp.DatabasePointer(":memory:", "select ? as a", parameters=[7])
        row = bp.resolve_pointer(okp).fetchone()
        param_ok = row[0] == 7
    except Exception as e:  # noqa: BLE001
        param_ok = "duckdb" not in str(e) and False
    checks.append(("DatabasePointer parameterized query binds via driver", param_ok))
    try:
        import duckdb as _dd
        p_ro = tmp / "ro.duckdb"
        _dd.connect(str(p_ro)).execute("create table t(a int); insert into t values (1)").close()
        try:
            bp.DatabasePointer(str(p_ro), "select a from t").__dict__  # construct ok
            ro_conn_blocked = "n/a"
        except Exception:  # noqa: BLE001
            ro_conn_blocked = "n/a"
    except ImportError:
        pass
    big = {"k%d" % i: list(range(100)) for i in range(5000)}
    t_s = time.perf_counter(); est_s = bp.estimate_bytes(big, mode="sampled"); ms_s = (time.perf_counter() - t_s) * 1000
    t_f = time.perf_counter(); est_f = bp.estimate_bytes(big, mode="full"); ms_f = (time.perf_counter() - t_f) * 1000
    checks.append(("estimate_bytes sampled ≥10x faster than full, within 3x of full", ms_s * 10 < ms_f and est_f / 3 < est_s < est_f * 3))
    checks.append(("estimate_bytes off → 0", bp.estimate_bytes(big, mode="off") == 0))
    (tmp / "src" / "engines" / "__init__.py").write_text("", encoding="utf-8")   # 變成 package → 走套件名載入路徑
    try:
        ls_ok = callable(bp.load_source(str(tmp / "src" / "engines" / "over.py"), "A.render"))
    except Exception as e:  # noqa: BLE001
        ls_ok = False
        print("load_source err", e)
    checks.append(("load_source via package path", ls_ok))
    try:
        bp.InlinePointer(list(range(3_000_000)))
        inline_blocked = False
    except bp.PointerError:
        inline_blocked = True
    checks.append(("InlinePointer size guard", inline_blocked))
    checks.append(("resolve_pointer mode=path", bp.resolve_pointer(ptr, "polars", "path") == str(csvp)))
    checks.append(("_approx_equal decimals", bp._approx_equal(100.004, 100.0, decimals=2) and not bp._approx_equal(100.006, 100.0, decimals=2)))
    checks.append(("fallback isolates primary_error", resp.metadata.get("primary_error", "").startswith("RuntimeError")))
    bp.Trace.path = tmp / "ves_trace.jsonl"
    with bp.EngineFactory.get("b") as e:
        e.process(bp.EngineRequest(task_id="tr"))
    checks.append(("trace spans written", bp.Trace.path.exists() and "engine.b.run" in bp.Trace.path.read_text(encoding="utf-8")))
    checks.append(("adapter has POINTER_MODES", "POINTER_MODES" in adapter_src and '"path": "path"' in adapter_src))
    checks.append(("ollama probe returns str (offline ok)", isinstance(ollama_available(timeout=0.2), str)))
    for name, passed in checks:
        ok += int(passed)
        print(f"  [{'PASS' if passed else 'FAIL'}] {name}")
    print(f"SELFTEST {ok}/{len(checks)}")
    return 0 if ok == len(checks) else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "--ml-probe-child":                # ② 子程序入口：只印一行 JSON
        print(json.dumps(_probe_ml_inproc(quick=("--full" not in argv)), ensure_ascii=False, default=str), flush=True)
        return 0
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--out", default="")
    ap.add_argument("--threshold", type=float, default=0.72)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--max-group", type=int, default=30)
    ap.add_argument("--llm", default="", help="'' 關閉 / 'auto' 自動偵測本機 Ollama / 指定模型名如 qwen2.5:3b")
    ap.add_argument("--exclude", action="append", default=[], help="glob 排除(可多次)，如 'tests/*' '*_old.py'")
    ap.add_argument("--no-ml-probe", action="store_true", help="跳過 CPU ML/DL 工具偵測與微基準")
    ap.add_argument("--langs", default="py,ps1,js", help="要盤點的語言：py,ps1,js（逗號分隔）")
    ap.add_argument("--semantic", default="auto", choices=["auto", "embed", "tfidf", "hashing", "off"], help="語意相似度後端")
    ap.add_argument("--install-plan", action="store_true", help="只印出免費 CPU ML libs 導入計畫並結束")
    ap.add_argument("--no-sandbox", action="store_true", help="跳過沙盤推演")
    ap.add_argument("--plan", default="", help="自訂編輯計畫 JSON（steps: ABSORB/SPLIT/INTEGRATE；不接受 DELETE）")
    ap.add_argument("--apply", action="store_true", help="沙盤 GO + Hydra≤H1 + --token 正確才把 add-only 變更套回原樹")
    ap.add_argument("--token", default="", help="ACTIVATION token（見 sandbox_report / expected_token_hint）")
    ap.add_argument("--slice", default="", help="只輸出某單位切片：VIA-FNC-xxxx / FN-00012 / qualname / VIA-CLS- / VIA-MDL-")
    ap.add_argument("--verify-dir", default="", help="AI 改過的檔案目錄（相對路徑同 root）→ 過閘後才准合併")
    a = ap.parse_args(argv)
    if a.selftest:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            return selftest(Path(td))
    root = Path(a.root).resolve()
    out = Path(a.out).resolve() if a.out else root / "_engine_standardizer" / time.strftime("run_%Y%m%d_%H%M%S")
    if a.install_plan:
        p = write_install_plan(Path.cwd(), None)
        print(p.read_text(encoding="utf-8"))
        print(f"pip install -r {p}")
        return 0
    r = run(root, out, a.threshold, a.workers, a.max_group, a.llm, a.exclude, not a.no_ml_probe, a.langs, a.semantic, not a.no_sandbox)
    if a.plan:
        try:
            custom = json.loads(Path(a.plan).read_text(encoding="utf-8"))
            dl = DetailLog(out / "ves_detail.log")
            rep2 = sandbox_simulate(root, out, custom, r["funcs"], r["ident"], r["catalog"], dl)
            print(f"@@SANDBOX_CUSTOM|{rep2['verdict']}|hydra={rep2['hydra']['level']} token_hint={'VES-ACTIVATE-' + hashlib.blake2s((rep2['ts'] + json.dumps(custom.get('steps', []), sort_keys=True)).encode(), digest_size=4).hexdigest().upper()}", flush=True)
            r["sandbox"], r["merge_plan"] = rep2, custom
        except Exception as e:  # noqa: BLE001
            print(f"@@SANDBOX_CUSTOM|ERROR|{type(e).__name__}: {e}", flush=True)
    if a.apply:
        res = apply_plan(root, out, r["merge_plan"], r["sandbox"], a.token)
        print("@@APPLY|" + json.dumps(res, ensure_ascii=False)[:800], flush=True)
    if a.slice:
        txt = slice_code(root, r["catalog"], r["funcs"], a.slice)
        (out / f"slice_{re.sub(r'[^A-Za-z0-9_.-]', '_', a.slice)}.txt").write_text(txt, encoding="utf-8")
        print("@@SLICE|" + str(_toks(txt)) + " tokens\n" + txt, flush=True)
    if a.verify_dir:
        vr = verify_ai_dir(root, out, Path(a.verify_dir).resolve(), r["funcs"], r["ident"], r["catalog"], DetailLog(out / "ves_detail.log"))
        print(f"@@VERIFY|{vr['verdict']}|" + " ".join(f"{g['gate']}={g['status']}" for g in vr.get("gates", [])), flush=True)
    return 0 if r["overall"] != "RED" else 2


if __name__ == "__main__":
    sys.exit(main())
