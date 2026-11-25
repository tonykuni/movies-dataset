#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VDF_LocalIntegrateLaunch v0100 — VDF 在地整合啟動器(桌機一行 PS 叫它;只動 VDF)

操作員 2026-11-25:「只整合 VDF 在地整合 Desktop\\測試\\VDF」「用一個 ps 指令完成下載且進入環境完成以上全部 ·
所有指令都用 py 撰寫導入加速器 · 每個指令加到最快 · 三個獨立步驟並行 · 功能都寫入 py · ps 單純是啟動動作」。
流程(PS 只負責:找倉 → 找 via_vdf 境 → 從分支取出本檔到 TEMP → 叫它):
  0 同步倉    呼叫倉內 VIA_HostBoot 尾版 --dry(fetch · 擋路檔處理 · main 快轉);失敗 = 黃,沿用現有工作樹,不碰已追蹤改動
  並行三步(互不相依,三道同時跑,每 20 秒一行心跳):
    A 候選引擎盤點   <候選夾> 每支 .py 的 AST:定義 / 簽章 / 匯入 / 出網件 / 落盤件 / CLI 參數 / LF 雜湊(不執行、不讀資料)
    B 資料庫 schema  <via_01_vdf>:.duckdb 唯讀開 → 表 · 欄 · 型別 · 主鍵 · 估計列數;.parquet 只讀頁尾 → 欄 · 型別 · 壓縮 · 列數;
                     擷取模組 .py 同 A。OneDrive 只在雲端的檔(召回屬性)略過,不觸發下載。不讀任何資料列。
    C 倉內 VDF       VDF 引擎尾版一覽(家族 · 版本 · 首行說明 · 出網 / 落盤件)+ 省 Token `chain VDF_ENG239_ParquetLakeBuild`
  3 寫 task.md(指向 A/B/C 的 JSON;Parquet 由 DuckDB 管理 = 沿用 VDF_ENG239 家族,不另做)
  4 本機 claude -p(stream-json → 每個動作一行;全文存 claude_stream.jsonl · 最終報告存 report.md)
輸出:<倉>/VeritasIntelligenceAnalytics/VIA_Reports/vdf_local_integrate/<時間>/(已 .gitignore)
資料邊界:JSON 只有程式結構與 schema(欄名 · 型別 · 列數);不含任何資料列。
用法:python VDF_LocalIntegrateLaunch_v0100.py --repo <倉> [--cand <夾>] [--db <夾>] [--max-turns 80] [--no-sync] [--dry]
      python VDF_LocalIntegrateLaunch_v0100.py --selftest
rc:0 綠 · 2 黃 · 1 紅
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0111] SuperAccel 加速器橋(從 TEMP 跑時改由工作目錄 / VIA_REPO 找倉;graceful) =====
try:
    import os as _sa_os
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_hit = None
    _sa_roots = [_sa_Path(__file__).resolve(), _sa_Path.cwd().resolve()]
    if _sa_os.environ.get("VIA_REPO"):
        _sa_roots.append(_sa_Path(_sa_os.environ["VIA_REPO"]).resolve())
    for _sa_r in _sa_roots:
        for _sa_q in (_sa_r, *_sa_r.parents):
            for _sa_c in (_sa_q / "supportive modules", _sa_q / "VeritasIntelligenceAnalytics" / "supportive modules"):
                if (_sa_c / "VIA_SuperAccel_Module.py").exists():
                    _sa_hit = _sa_c
                    break
            if _sa_hit:
                break
        if _sa_hit:
            break
    if _sa_hit and str(_sa_hit) not in _sa_sys.path:
        _sa_sys.path.insert(0, str(_sa_hit))
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響(自測會把它記成黃)
# ===== [VIA:ACCEL-BRIDGE:END] =====

import argparse
import ast
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

try:
    import orjson as _oj
except Exception:  # noqa: BLE001
    _oj = None

STEM = "VDF_LocalIntegrateLaunch"
VERSION = "v0100"
TAG = f"{STEM} {VERSION}"
_T0 = time.time()
SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", "env", "node_modules", "site-packages", ".mypy_cache", ".pytest_cache"}
NET_LIBS = {"httpx", "requests", "aiohttp", "curl_cffi", "urllib3", "urllib", "yfinance", "twstock", "selenium", "playwright", "websockets"}
STORE_LIBS = {"polars", "duckdb", "pyarrow", "pandas", "orjson", "fastparquet", "sqlite3"}
PARQUET_CALLS = {"write_parquet", "to_parquet", "sink_parquet", "write_table", "read_parquet", "scan_parquet"}
_OFFLINE_ATTRS = 0x1000 | 0x400000 | 0x40000  # OFFLINE · RECALL_ON_DATA_ACCESS · RECALL_ON_OPEN(OneDrive 只在雲端)
REPO_VDF = Path("VeritasIntelligenceAnalytics") / "functional modules" / "VDF"
OUT_REL = Path("VeritasIntelligenceAnalytics") / "VIA_Reports" / "vdf_local_integrate"
TOKEN_LOCK = Path("VeritasIntelligenceAnalytics") / "supportive modules" / "registry" / "VIA_ToolVersion_Lock_v0100.json"
CLAUDE_TOOLS = "Read,Write,Edit,Bash,Glob,Grep"


def say(msg: str) -> None:
    print(f"[{time.time() - _T0:6.1f}s] {msg}", flush=True)


def dump(obj, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".{os.getpid()}.tmp")
    if _oj is not None:
        tmp.write_bytes(_oj.dumps(obj, option=_oj.OPT_INDENT_2 | _oj.OPT_NON_STR_KEYS, default=str))
    else:
        tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    os.replace(tmp, path)


def lf_sha(data: bytes) -> str:
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()[:16]


def cloud_only(p: Path) -> bool:
    """OneDrive「只在雲端」的檔:讀它會觸發下載 → 略過。非 Windows 沒有這個屬性。"""
    try:
        return bool(getattr(p.stat(), "st_file_attributes", 0) & _OFFLINE_ATTRS)
    except OSError:
        return True


WALK_ERRORS: list = []  # 讀不到的夾(權限 / OneDrive I/O)照實記,摘要帶出,不吞


def walk(root: Path, exts: tuple):
    stack = [root]
    while stack:
        d = stack.pop()
        try:
            entries = list(os.scandir(d))
        except OSError as e:
            WALK_ERRORS.append(f"{d}: {type(e).__name__}: {e}")
            entries = []
        for e in entries:
            if e.is_dir(follow_symlinks=False):
                if e.name not in SKIP_DIRS:
                    stack.append(Path(e.path))
            elif e.name.lower().endswith(exts):
                yield Path(e.path)


def _vnum(p: Path) -> int:
    m = re.search(r"_v(\d{4})$", p.stem)
    return int(m.group(1)) if m else -1


# ---------------------------------------------------------------- A / B 共用:一支 .py 的結構卡
def scan_py(path: Path, base: Path) -> dict:
    rel = path.relative_to(base).as_posix()
    if cloud_only(path):
        return {"file": rel, "skipped": "cloud_only"}
    raw = path.read_bytes()
    card = {"file": rel, "lines": raw.count(b"\n") + 1, "bytes": len(raw), "sha_lf": lf_sha(raw)}
    try:
        tree = ast.parse(raw.decode("utf-8-sig", errors="replace"), filename=rel)
    except SyntaxError as e:
        card["error"] = f"SyntaxError L{e.lineno}: {e.msg}"
        return card
    imps, defs, cli, pq = set(), [], [], set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imps.update(a.name.split(".")[0] for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            imps.add(n.module.split(".")[0])
        elif isinstance(n, ast.Call):
            f = n.func
            name = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")
            if name in PARQUET_CALLS:
                pq.add(name)
            if name == "add_argument":
                cli += [a.value for a in n.args if isinstance(a, ast.Constant) and isinstance(a.value, str)]
        elif isinstance(n, ast.Constant) and isinstance(n.value, str) and "FORMAT PARQUET" in n.value.upper():
            pq.add("COPY_TO_PARQUET")
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            item = {"name": n.name, "line": n.lineno, "kind": type(n).__name__.replace("Def", "")}
            if not isinstance(n, ast.ClassDef):
                item["args"] = [a.arg for a in n.args.args]
            else:
                item["methods"] = [m.name for m in n.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))][:30]
            doc = ast.get_docstring(n)
            if doc:
                item["doc"] = doc.strip().splitlines()[0][:120]
            defs.append(item)
    main_guard = any(isinstance(n, ast.If) and "__main__" in ast.dump(n.test) for n in tree.body)
    doc = ast.get_docstring(tree)
    card.update({"doc": (doc or "").strip().splitlines()[0][:160] if doc else "", "imports": sorted(imps),
                 "net": sorted(imps & NET_LIBS), "store": sorted(imps & STORE_LIBS), "parquet_calls": sorted(pq),
                 "cli": cli[:40], "main_guard": main_guard, "accel_bridge": "VIA:ACCEL-BRIDGE" in raw[:4000].decode("utf-8", "replace"),
                 "defs": defs[:80]})
    return card


def step_a(cand: Path) -> dict:
    """A 候選引擎盤點(只 AST,不執行)。"""
    if not cand.is_dir():
        return {"lamp": "RED", "note": f"候選夾不在:{cand}", "should": 0, "done": 0, "skipped": []}
    files = sorted(walk(cand, (".py",)))
    cards = [scan_py(p, cand) for p in files]
    others = sorted(p.relative_to(cand).as_posix() for p in walk(cand, (".ipynb", ".ps1", ".bat", ".json", ".yaml", ".yml", ".toml", ".txt", ".md")))
    skipped = [c["file"] for c in cards if c.get("skipped")]
    errs = [c["file"] for c in cards if c.get("error")]
    lamp = "RED" if not files else ("YELLOW" if skipped or errs else "GREEN")
    return {"lamp": lamp, "root": str(cand), "should": len(files), "done": len(files) - len(skipped), "skipped": skipped,
            "syntax_errors": errs, "non_py": others[:200], "engines": cards}


# ---------------------------------------------------------------- B 資料庫 schema(只結構)
def _duck_schema(path: Path) -> dict:
    import duckdb  # 延後匯入:沒裝 = 黃,不擋 A / C
    con = duckdb.connect(str(path), read_only=True)
    try:
        cols = con.execute("SELECT table_schema, table_name, column_name, data_type, ordinal_position "
                           "FROM information_schema.columns ORDER BY 1, 2, 5").fetchall()
        keys = con.execute("SELECT schema_name, table_name, constraint_type, constraint_column_names "
                           "FROM duckdb_constraints() WHERE constraint_type IN ('PRIMARY KEY','UNIQUE')").fetchall()
        est = dict(((r[0], r[1]), r[2]) for r in con.execute(
            "SELECT schema_name, table_name, estimated_size FROM duckdb_tables()").fetchall())
        views = {(r[0], r[1]) for r in con.execute("SELECT schema_name, view_name FROM duckdb_views() WHERE NOT internal").fetchall()}
    finally:
        con.close()
    tables: dict = {}
    for s, t, c, ty, _ in cols:
        k = f"{s}.{t}"
        tables.setdefault(k, {"kind": "view" if (s, t) in views else "table", "est_rows": est.get((s, t)), "columns": [], "keys": []})
        tables[k]["columns"].append([c, ty])
    for s, t, kind, cn in keys:
        tables.setdefault(f"{s}.{t}", {"columns": [], "keys": []})["keys"].append([kind, list(cn)])
    return {"tables": tables}


def _pq_schema(path: Path) -> dict:
    try:
        import pyarrow.parquet as pq
        md = pq.ParquetFile(str(path)).metadata
        sch = md.schema.to_arrow_schema()
        comp = md.row_group(0).column(0).compression if md.num_row_groups else ""
        return {"columns": [[f.name, str(f.type)] for f in sch], "rows": md.num_rows, "compression": comp}
    except ImportError:
        import duckdb
        con = duckdb.connect()
        try:
            d = con.execute("DESCRIBE SELECT * FROM read_parquet(?)", [str(path)]).fetchall()
            n = con.execute("SELECT SUM(row_group_num_rows) FROM (SELECT DISTINCT row_group_id, row_group_num_rows "
                            "FROM parquet_metadata(?))", [str(path)]).fetchone()[0]
        finally:
            con.close()
        return {"columns": [[r[0], r[1]] for r in d], "rows": n, "compression": ""}


def step_b(db: Path) -> dict:
    """B via_01_vdf schema:duckdb 唯讀 · parquet 只讀頁尾 · 擷取模組 AST。"""
    if not db.is_dir():
        return {"lamp": "RED", "note": f"資料庫夾不在:{db}", "should": 0, "done": 0, "skipped": []}
    out = {"root": str(db), "duckdb": {}, "parquet_dirs": {}, "modules": [], "skipped": [], "errors": {}}
    ducks = sorted(walk(db, (".duckdb", ".db")))
    pqs = sorted(walk(db, (".parquet",)))
    pys = sorted(walk(db, (".py",)))
    for p in ducks:
        rel = p.relative_to(db).as_posix()
        if cloud_only(p):
            out["skipped"].append(rel + " (cloud_only)")
            continue
        try:
            out["duckdb"][rel] = _duck_schema(p)
        except Exception as e:  # noqa: BLE001 - 鎖 / 版本不合照實記
            out["errors"][rel] = f"{type(e).__name__}: {str(e)[:200]}"
    groups: dict = {}
    for p in pqs:
        groups.setdefault(p.parent, []).append(p)
    for d, fs in sorted(groups.items()):
        rel = d.relative_to(db).as_posix() or "."
        local = [f for f in fs if not cloud_only(f)]
        info = {"files": len(fs), "bytes": sum(f.stat().st_size for f in fs), "cloud_only": len(fs) - len(local)}
        if local:
            newest = max(local, key=lambda f: f.stat().st_mtime)
            try:
                info["sample"] = newest.name
                info.update(_pq_schema(newest))
            except Exception as e:  # noqa: BLE001
                out["errors"][rel] = f"{type(e).__name__}: {str(e)[:200]}"
        else:
            out["skipped"].append(rel + " (parquet 全在雲端)")
        out["parquet_dirs"][rel] = info
    out["modules"] = [scan_py(p, db) for p in pys]
    out["skipped"] += [m["file"] + " (cloud_only)" for m in out["modules"] if m.get("skipped")]
    should = len(ducks) + len(groups) + len(pys)
    out.update(should=should, done=should - len(out["skipped"]) - len(out["errors"]))
    out["lamp"] = "RED" if should == 0 else ("YELLOW" if out["skipped"] or out["errors"] else "GREEN")
    return out


# ---------------------------------------------------------------- C 倉內 VDF 尾版 + 版本鏈
def token_tool(repo: Path):
    try:
        return repo / json.loads((repo / TOKEN_LOCK).read_text(encoding="utf-8"))["token"]["path"]
    except Exception:  # noqa: BLE001
        return None


def step_c(repo: Path) -> dict:
    vdf = repo / REPO_VDF
    if not vdf.is_dir():
        return {"lamp": "RED", "note": f"倉內沒有 {REPO_VDF}", "should": 0, "done": 0, "skipped": []}
    fams: dict = {}
    for p in list(vdf.glob("VDF_*_v*.py")) + list((vdf / "engine").glob("VDF_*_v*.py")):
        fam = re.sub(r"_v\d{4}$", "", p.stem)
        if fam not in fams or _vnum(p) > _vnum(fams[fam]):
            fams[fam] = p
    tails = []
    for fam, p in sorted(fams.items()):
        c = scan_py(p, repo)
        tails.append({"family": fam, "tail": p.name, "path": c["file"], "doc": c.get("doc", ""), "net": c.get("net", []),
                      "store": c.get("store", []), "parquet_calls": c.get("parquet_calls", []), "error": c.get("error")})
    chain, rc = "", None
    t = token_tool(repo)
    if t and t.exists():
        try:
            r = subprocess.run([sys.executable, str(t), "chain", "VDF_ENG239_ParquetLakeBuild"], cwd=str(repo),
                               capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180,
                               env=dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8"))
            chain, rc = r.stdout[-6000:], r.returncode
        except Exception as e:  # noqa: BLE001
            chain = f"{type(e).__name__}: {e}"
    skipped = [] if rc == 0 else ["chain VDF_ENG239_ParquetLakeBuild"]
    errs = [x["tail"] for x in tails if x.get("error")]
    return {"lamp": "YELLOW" if skipped or errs else "GREEN", "should": len(tails) + 1, "done": len(tails) + (rc == 0),
            "skipped": skipped, "syntax_errors": errs, "tails": tails, "chain_ENG239": chain, "chain_rc": rc,
            "lake_engine": next((x for x in tails if x["family"] == "VDF_ENG239_ParquetLakeBuild"), None),
            "manager": next((x for x in tails if x["family"] == "VDF_SystemManager"), None)}


# ---------------------------------------------------------------- 並行三步 + 心跳
def run_parallel(jobs: dict, beat: float = 20.0) -> dict:
    res, stop = {}, threading.Event()

    def heart():
        while not stop.wait(beat):
            say("心跳 · 還在跑:" + " · ".join(k for k in jobs if k not in res))

    hb = threading.Thread(target=heart, daemon=True)
    hb.start()
    with ThreadPoolExecutor(max_workers=len(jobs)) as ex:
        futs = {k: (time.time(), ex.submit(fn)) for k, fn in jobs.items()}
        for k, (t0, f) in futs.items():
            try:
                res[k] = f.result()
            except Exception as e:  # noqa: BLE001 - 一步爆 = 該步紅,其他照收
                res[k] = {"lamp": "RED", "note": f"{type(e).__name__}: {e}", "should": 1, "done": 0, "skipped": []}
            res[k]["seconds"] = round(time.time() - t0, 2)
            say(f"{k} · {res[k]['lamp']} · 應 {res[k].get('should')} · 已 {res[k].get('done')} · 略過 {len(res[k].get('skipped', []))} · {res[k]['seconds']}s")
    stop.set()
    return res


# ---------------------------------------------------------------- task.md
def build_task(out: Path, repo: Path, cand: Path, db: Path, res: dict) -> str:
    rel = lambda k: (out / f"{k}.json").relative_to(repo).as_posix()  # noqa: E731
    lake = (res.get("C_repo_vdf") or {}).get("lake_engine") or {}
    mgr = (res.get("C_repo_vdf") or {}).get("manager") or {}
    three = "\n".join(f"  - {k}: {v.get('lamp')} · 應 {v.get('should')} · 已 {v.get('done')} · 略過 {v.get('skipped')}" for k, v in res.items())
    return f"""<system_directive>
你是在操作員桌機上執行的 VDF 整合代理。範圍只有 VDF(操作員 2026-11-25:「只整合 VDF 在地整合」);VRN / VCGC / VQG / VAP 一律不動。
全自動端到端:不中途詢問、不整檔讀大檔。第一步讀倉根 CLAUDE.md 並照做(token 卡 → functions → 改薄尾前 chain);與本檔衝突時以 CLAUDE.md 為準並在報告列出。
</system_directive>

<inputs>
- 候選引擎夾:{cand}
- 資料庫夾:{db}
- 啟動器已並行做完三項盤點(只結構,不含資料列),先讀這三個 JSON,不要重掃:
  - A 候選引擎 AST:{rel('A_candidates')}
  - B 資料庫 schema:{rel('B_db_schema')}
  - C 倉內 VDF 尾版 + ENG239 版本鏈:{rel('C_repo_vdf')}
{three}
- VDF 入口:{mgr.get('path', 'VDF_SystemManager 尾版')}
- Parquet 由 DuckDB 管理的現役引擎:{lake.get('path', 'VDF_ENG239_ParquetLakeBuild 尾版')}(沿用它的湖與 DuckDB 目錄,不另做)
</inputs>

<constraints>
- 只讀程式結構與 schema;市場資料內容不貼進對話、不送任何外部服務。
- 改程式照 SDD 四步:read 找節點 → slice → TEMP 改好(ast.parse + compile 過)→ --selftest + 整合測試。薄尾家族出新版號,前版一字不動;改完 read 的 TAILAPI 必須 0。
- 新 .py 第 3 行 # [VIA:ACCEL-BRIDGE:v0111] + 橋區塊;自測要驗 VIA_ACCEL is not None。有對外擷取的引擎另經 AST 導入鎖冊上的網路工具。
- 同意閘(VIA_NET_CONSENT 等)只在真擷取那一步的子行程裡設,不寫進任何檔。
- 舊擷取器:三條都過才刪(chain 無人載入 · 拿掉後尾版每個動詞實跑過 · 鎖定帳已鎖成功數不變),刪除單獨一批;否則只標停用。候選夾是操作員的測試夾,不刪不改。
- 不改既有 .ps1;不直接 pip(缺件走 VCGC 安裝閘)。OneDrive I/O error = 停下回報,不繞過。
- 動工前跑 VIA_ReworkGuard 尾版 check --fetch-prs;紅 = 不推。工作在新分支,不直接推 main。
</constraints>

<workflow>
1 契約:由 A + B 建 VDFRequestConfig(來源 · 代碼(台股四碼首位非 0)· 起訖日 · 視窗 · 並發 / 重試)與 VDFOutputSchema(polars 欄名 · 型別 Float64 / Date / Utf8 · 主鍵 = B 的 DuckDB 主鍵);@dataclass(frozen=True);參數集中在 VDF 參數冊,不寫死在引擎。
2 實測:TEMP 寫一次性基準腳本,同一組輸入(2330 · 最近 5 個交易日)跑每支候選:端到端秒 · 峰值 MB · 對 VDFOutputSchema 的欄位對齊率。對齊 100% 且最快者勝出;其餘標淘汰。腳本跑完自刪。
3 整合:勝出邏輯補進對應 VDF 擷取家族的新版號(先 chain 找本體;沒有本體才開新家族並照 VDF 自發號登記):連線池複用 + 指數退避;orjson + polars;落盤 = ZSTD Parquet 進 ENG239 的湖,由 DuckDB 目錄(VIEW over read_parquet)管理,主鍵 upsert,缺值不補 0(FAIL_CLOSED)。
4 入口:掛成 VDF_SystemManager 尾版的動詞(--source --tickers --start --end --mode incremental|full|benchmark --dry-run),不另做啟動器。
5 驗收:實跑 benchmark --dry-run + 一次真實短區間增量;筆數 > 0;欄位型別對 DuckDB 目錄 100%;失敗就修到綠。之後 註冊 → 鎖定帳 → 提交推送。
</workflow>

<final_output_format>
400 字內:1 勝出引擎實測表(名稱 · 秒 · MB · 吞吐)2 輸入契約與輸出 schema 摘要 3 變更檔清單 · 一行啟動指令 · 範圍外改動檔數 · 與 CLAUDE.md 的衝突與處理。
標「主機實跑」;沒關的項目逐項寫缺什麼證據,有沒關的就不寫收尾成功。
</final_output_format>
"""


# ---------------------------------------------------------------- 4 本機 claude
def claude_cmd(max_turns: int):
    exe = shutil.which("claude") or shutil.which("claude.cmd") or shutil.which("claude.exe")
    if not exe:
        return None
    return [exe, "-p", "--permission-mode", "acceptEdits", "--allowedTools", CLAUDE_TOOLS,
            "--max-turns", str(max_turns), "--output-format", "stream-json", "--verbose"]


def _brief(ev: dict) -> list:
    lines = []
    if ev.get("type") == "assistant":
        for c in (ev.get("message") or {}).get("content", []) or []:
            if c.get("type") == "tool_use":
                inp = c.get("input") or {}
                hint = inp.get("command") or inp.get("file_path") or inp.get("pattern") or ""
                lines.append(f"  ▸ {c.get('name')} {str(hint).splitlines()[0][:140] if hint else ''}")
            elif c.get("type") == "text" and c.get("text", "").strip():
                lines.append("  · " + c["text"].strip().splitlines()[0][:160])
    return lines


def run_claude(cmd: list, task: str, repo: Path, out: Path) -> int:
    log = (out / "claude_stream.jsonl").open("w", encoding="utf-8")
    last = {"t": time.time()}
    stop = threading.Event()

    def heart():
        while not stop.wait(30):
            if time.time() - last["t"] >= 30:
                say("心跳 · claude 還在想(%ds 沒新動作)" % (time.time() - last["t"]))

    threading.Thread(target=heart, daemon=True).start()
    proc = subprocess.Popen(cmd, cwd=str(repo), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, encoding="utf-8", errors="replace", env=dict(os.environ, PYTHONUTF8="1"))
    proc.stdin.write(task)
    proc.stdin.close()
    result = None
    for line in proc.stdout:
        log.write(line)
        last["t"] = time.time()
        try:
            ev = json.loads(line)
        except ValueError:
            if line.strip():
                say("  " + line.rstrip()[:200])
            continue
        for ln in _brief(ev):
            say(ln)
        if ev.get("type") == "result":
            result = ev
    rc = proc.wait()
    stop.set()
    log.close()
    if result:
        (out / "report.md").write_text(str(result.get("result", "")), encoding="utf-8")
        print("\n" + "=" * 70 + "\n" + str(result.get("result", "")) + "\n" + "=" * 70, flush=True)
        if result.get("is_error") or result.get("subtype") not in (None, "success"):
            say(f"[YELLOW] claude 結束狀態 {result.get('subtype')}(例:error_max_turns = 回合用完,加大 --max-turns 再跑)")
            return 2
    return 0 if rc == 0 and result else 1


# ---------------------------------------------------------------- 0 同步
def sync(repo: Path) -> str:
    d = repo / "VeritasIntelligenceAnalytics" / "docs" / "handoff" / "ai"
    hb = sorted(d.glob("VIA_HostBoot_v*.py"), key=_vnum)
    if not hb:
        return "YELLOW(沒有 VIA_HostBoot,沿用現有工作樹)"
    rc = subprocess.run([sys.executable, str(hb[-1]), "--repo", str(repo), "--dry"], cwd=str(repo),
                        env=dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")).returncode
    return "GREEN" if rc == 0 else f"YELLOW(HostBoot rc {rc}:4 = 有已追蹤改動沒動 · 5 = git 失敗;沿用現有工作樹)"


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    home = Path.home()
    ap = argparse.ArgumentParser(prog=TAG)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--cand", default=str(home / "OneDrive" / "Desktop" / "測試" / "VDF"))
    ap.add_argument("--db", default=str(home / "OneDrive" / "Documents" / "VeritasIntelligenceAnalytics" / "via_01_vdf"))
    ap.add_argument("--branch", default="")
    ap.add_argument("--max-turns", type=int, default=80)
    ap.add_argument("--no-sync", action="store_true")
    ap.add_argument("--dry", action="store_true", help="只做盤點與 task.md,不叫 claude")
    a = ap.parse_args(argv)
    repo, cand, db = Path(a.repo).expanduser().resolve(), Path(a.cand).expanduser(), Path(a.db).expanduser()
    if not (repo / "VeritasIntelligenceAnalytics").is_dir():
        say(f"[RED] 不是 VIA 倉:{repo}")
        return 1
    say(f"{TAG} · 倉 {repo} · 加速器 {'載入' if VIA_ACCEL is not None else '沒載到(黃)'}")
    lamps = []
    if not a.no_sync:
        say("0 同步倉(VIA_HostBoot --dry)")
        s = sync(repo)
        say("0 同步 · " + s)
        lamps.append(s.split("(")[0])
    out = repo / OUT_REL / datetime.now().strftime("%Y%m%d_%H%M%S")
    out.mkdir(parents=True, exist_ok=True)
    say("並行三步 A 候選引擎 · B 資料庫 schema · C 倉內 VDF")
    res = run_parallel({"A_candidates": lambda: step_a(cand), "B_db_schema": lambda: step_b(db), "C_repo_vdf": lambda: step_c(repo)})
    names = {"A_candidates": "A_candidates", "B_db_schema": "B_db_schema", "C_repo_vdf": "C_repo_vdf"}
    for k, v in res.items():
        dump(v, out / f"{names[k]}.json")
    lamps += [v["lamp"] for v in res.values()]
    if res["A_candidates"]["lamp"] == "RED" or res["C_repo_vdf"]["lamp"] == "RED":
        say("[RED] 候選夾或倉內 VDF 不在,不叫 claude:" + " · ".join(str(res[k].get("note", "")) for k in ("A_candidates", "C_repo_vdf")))
        return 1
    task = build_task(out, repo, cand, db, res)
    (out / "task.md").write_text(task, encoding="utf-8")
    if WALK_ERRORS:
        say(f"[YELLOW] {len(WALK_ERRORS)} 個夾讀不到(OneDrive I/O error 屬環境紅:先處理再跑):" + WALK_ERRORS[0][:200])
        lamps.append("YELLOW")
    summ = {"tag": TAG, "utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "accel": VIA_ACCEL is not None,
            "walk_errors": WALK_ERRORS[:50],
            "steps": {k: {x: v.get(x) for x in ("lamp", "should", "done", "skipped", "seconds")} for k, v in res.items()}}
    dump(summ, out / "summary.json")
    say(f"3 task.md → {out / 'task.md'}")
    if a.dry:
        say("--dry:不叫 claude。總計 %ds" % (time.time() - _T0))
        return 2 if "RED" in lamps or "YELLOW" in lamps or VIA_ACCEL is None else 0
    cmd = claude_cmd(a.max_turns)
    if not cmd:
        say("[RED] 找不到 claude 指令(Claude Code CLI 沒裝或不在 PATH)")
        return 1
    say("4 本機 claude -p(每個動作一行;全文 claude_stream.jsonl)")
    rc = run_claude(cmd, task, repo, out)
    say(f"完成 · rc {rc} · 盤點燈 {' · '.join(lamps)} · 輸出 {out} · 總計 {time.time() - _T0:.0f}s")
    if rc == 0 and ("YELLOW" in lamps or "RED" in lamps):
        return 2
    return rc


# ---------------------------------------------------------------- 自測(全在暫存夾造資料)
def selftest() -> int:
    ok, bad = [], []

    def chk(name, cond, note=""):
        (ok if cond else bad).append(name)
        print(("  [OK] " if cond else "  [NG] ") + name + (f" · {note}" if note else ""), flush=True)

    chk("加速器載入(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        cand, db, repo = td / "cand", td / "db", td / "repo"
        (cand / "sub").mkdir(parents=True)
        (cand / "fast_engine.py").write_text(
            "import httpx, polars as pl\nimport argparse\n"
            "def fetch(ticker, start, end):\n    '''抓日線'''\n    return pl.DataFrame()\n"
            "class Store:\n    def save(self, df):\n        df.write_parquet('x.parquet')\n"
            "if __name__ == '__main__':\n    ap = argparse.ArgumentParser(); ap.add_argument('--tickers')\n", encoding="utf-8")
        (cand / "sub" / "broken.py").write_text("def x(:\n", encoding="utf-8")
        (cand / "crlf.py").write_bytes(b"import requests\r\nX = 1\r\n")
        (cand / "notes.md").write_text("x", encoding="utf-8")
        a = step_a(cand)
        eng = {c["file"]: c for c in a["engines"]}
        chk("A 三數(應 3 · 已 3)", a["should"] == 3 and a["done"] == 3)
        chk("A 出網件 / 落盤件 / CLI", eng["fast_engine.py"]["net"] == ["httpx"] and "write_parquet" in eng["fast_engine.py"]["parquet_calls"]
            and eng["fast_engine.py"]["cli"] == ["--tickers"] and eng["fast_engine.py"]["main_guard"])
        chk("A 語法錯誤照報(黃)", a["syntax_errors"] == ["sub/broken.py"] and a["lamp"] == "YELLOW")
        chk("A CRLF 與 LF 雜湊相同", eng["crlf.py"]["sha_lf"] == lf_sha(b"import requests\nX = 1\n"))
        chk("A 非 .py 列出", a["non_py"] == ["notes.md"])
        chk("A 候選夾不在 = 紅", step_a(td / "nope")["lamp"] == "RED")
        db.mkdir()
        (db / "fetcher.py").write_text("import duckdb\n", encoding="utf-8")
        try:
            import duckdb
            con = duckdb.connect(str(db / "vdf.duckdb"))
            con.execute("CREATE TABLE px(date DATE, code VARCHAR, close DOUBLE, PRIMARY KEY(date, code))")
            con.execute("INSERT INTO px VALUES (DATE '2026-11-24', '2330', 1.0)")
            (db / "lake" / "px").mkdir(parents=True)
            con.execute(f"COPY px TO '{(db / 'lake' / 'px' / 'p1.parquet').as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)")
            con.close()
            b = step_b(db)
            t = b["duckdb"]["vdf.duckdb"]["tables"]["main.px"]
            chk("B duckdb 欄 · 型別 · 主鍵", t["columns"][0] == ["date", "DATE"] and t["keys"][0] == ["PRIMARY KEY", ["date", "code"]])
            pd = b["parquet_dirs"]["lake/px"]
            chk("B parquet 只讀頁尾(欄 · 列數)", pd["rows"] == 1 and [c[0] for c in pd["columns"]] == ["date", "code", "close"])
            chk("B 三數(應 3 · 已 3 · 綠)", b["should"] == 3 and b["done"] == 3 and b["lamp"] == "GREEN", str((b["should"], b["done"], b["lamp"])))
            chk("B JSON 不含資料值", "1.0" not in json.dumps(b["duckdb"]) and "2026-11-24" not in json.dumps(b))
        except ImportError:
            chk("B duckdb 可用(缺件 = 黃)", False, "duckdb 沒裝")
        global cloud_only
        real = cloud_only
        cloud_only = lambda p: p.suffix == ".parquet"  # noqa: E731 - 模擬 OneDrive 只在雲端
        try:
            b2 = step_b(db)
            chk("B 雲端檔略過不下載(黃)", any("雲端" in s for s in b2["skipped"]) and b2["lamp"] == "YELLOW")
        finally:
            cloud_only = real
        eng_dir = repo / REPO_VDF / "engine"
        eng_dir.mkdir(parents=True)
        for v in ("v0100", "v0102"):
            (eng_dir / f"VDF_ENG239_ParquetLakeBuild_{v}.py").write_text(f"'''湖 {v}'''\nimport duckdb\n", encoding="utf-8")
        (repo / REPO_VDF / "VDF_SystemManager_v0191.py").write_text("'''mgr'''\n", encoding="utf-8")
        c = step_c(repo)
        chk("C 取尾版", c["lake_engine"]["tail"] == "VDF_ENG239_ParquetLakeBuild_v0102.py" and c["manager"]["tail"] == "VDF_SystemManager_v0191.py")
        chk("C 沒有省 Token 工具 = 黃(chain 略過)", c["lamp"] == "YELLOW" and c["skipped"])
        calls = []
        res = run_parallel({"A_candidates": lambda: (calls.append("A"), step_a(cand))[1],
                            "B_db_schema": lambda: (calls.append("B"), step_b(db))[1],
                            "C_repo_vdf": lambda: 1 / 0}, beat=0.05)
        chk("並行三步都收到結果 · 一步爆只紅那步", sorted(calls) == ["A", "B"] and res["C_repo_vdf"]["lamp"] == "RED" and "seconds" in res["A_candidates"])
        out = repo / OUT_REL / "t"
        task = build_task(out, repo, cand, db, {"A_candidates": a, "C_repo_vdf": c})
        chk("task.md 指向三個 JSON · 只做 VDF · ENG239", "A_candidates.json" in task and "B_db_schema.json" in task
            and "只有 VDF" in task and "VDF_ENG239_ParquetLakeBuild_v0102.py" in task)
        cmd = ["claude", "-p", "--permission-mode", "acceptEdits", "--allowedTools", CLAUDE_TOOLS, "--max-turns", "80",
               "--output-format", "stream-json", "--verbose"]
        got = claude_cmd(80)
        chk("claude 指令組法", got is None or got[1:] == cmd[1:])
        chk("stream-json 每個動作一行", _brief({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Bash", "input": {"command": "python x.py\nmore"}}]}}) == ["  ▸ Bash python x.py"])
        (repo / "VeritasIntelligenceAnalytics" / "VIA_Reports").mkdir(parents=True, exist_ok=True)
        rc = main(["--repo", str(repo), "--cand", str(cand), "--db", str(db), "--no-sync", "--dry"])
        outs = sorted((repo / OUT_REL).glob("2*"))
        chk("main --dry 端到端(黃 rc 2 · 寫出 4 檔)", rc == 2 and outs and all((outs[-1] / f).exists() for f in
            ("A_candidates.json", "B_db_schema.json", "C_repo_vdf.json", "task.md", "summary.json")), f"rc {rc}")
        chk("不是 VIA 倉 = 紅", main(["--repo", str(td / "cand"), "--no-sync", "--dry"]) == 1)
    print(f"{TAG} selftest {len(ok)}/{len(ok) + len(bad)}" + (" · 不過:" + " · ".join(bad) if bad else ""), flush=True)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
