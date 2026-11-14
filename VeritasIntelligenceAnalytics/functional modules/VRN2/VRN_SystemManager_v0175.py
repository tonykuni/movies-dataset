#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0175 — 薄尾(操作員 2026-10-11「修正不停還原不停會不會把指令修壞 · 任何修正都要用 VCGC 全景式分析 · 檢視錯誤分類 · 可同步 / 不可同步修正 ·
   AST 精準或彈性錨點 · 避免傷害系統引擎 · 避免九頭龍 · 所有 PY/PS 加速器覆蓋 · 每一次修正執行都要跑一輪這個流程」「加速器用最新有版本號的加速器 ·
   在地測試未成功不上傳 · 獨立系統」「三系統獨立運作但相互監控 · 安裝透過 VCGC」)。
  selfgate 動詞(VRN 自己的修正閘;VCGC 全景只讀監控 = 互相監控,不連結):
    ① 盤點尾版(家族 _v####)· ② 靜態:py ast.parse + compile(不執行)· ps1 Parser · ③ 加速器:最新有版號 VeritasCeleritas_v#### · 每支尾版橋型
    ④ 九頭龍:管理器鏈執行期替換頭數(setattr / _patch / vars()[…] =)· 熱點 ≥3 頭 · 新增頭在熱點 = 紅 · ⑤ 指紋:既有檔被改動 = 紅(只增不減)
    ⑥ AST 錨點:精準(檔 · 行 · def 結構雜湊)/ 彈性(名 · 參數)· ⑦ --sandbox:新舊尾版整條鏈自測並跑 → 新增失敗 = 紅(啟動器據此決定落不落地)
    ⑧ VCGC 全景(VIA_Panorama 尾版 · 只讀 · --scope VRN --static)棘輪退步 = 紅 · 其餘紅 = 既有(黃)· ⑨ 上一輪紀錄分診(中斷 / 環境 / 真錯)
    分類:可同步修正 = OP-300 缺標記 · OP-400 同型批次 · 單點非熱點缺陷;不可同步 = OP-500 熱點 / 既有檔被改 / 環境(經 VCGC 安裝)/ 資料
  auto --resume:前三段輸出都在 → 只做 讀表實測 · KPI · 決策 · 台帳(不重跑;同輸入不重跑)
  讀表實測有進度(實測 i/N)· 重型讀表器(camelot / tabula / img2table)每次呼叫在子程序跑 · 逾時 = 失敗(不再卡住)
其餘動詞照前版鏈。
"""
from __future__ import annotations

# ===== [VIA:ACCEL-BRIDGE:v0111] 最新有版號的正本加速器(動態取最高 VeritasCeleritas_v####;退回鎖版 v1141)· 正本網路工具 VeritasAegisNexus_v1652(找不到 = 不改任何行為) =====
import importlib as _cb_il
import re as _cb_re
import sys as _cb_sys
from pathlib import Path as _cb_Path
_ACCEL, _ACCEL_VER = None, ""
_cb_p = _cb_Path(__file__).resolve()
while _cb_p.parent != _cb_p:
    if (_cb_p / "supportive modules").is_dir():
        _cb_sup = _cb_p / "supportive modules"
        _cb_c = sorted(list(_cb_sup.glob("VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")) + list(_cb_sup.glob("*/VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")),
                       key=lambda x: int(_cb_re.search(r"_v(\d{4})", x.name).group(1)))
        for _cb_d in [str(_cb_sup)] + ([str(_cb_c[-1].parent)] if _cb_c else []) + [str(x.parent) for x in list(_cb_sup.glob("*/VeritasAegisNexus_v1652.py"))[:1]]:
            if _cb_d not in _cb_sys.path:
                _cb_sys.path.insert(0, _cb_d)
        if _cb_c:
            try:
                _ACCEL, _ACCEL_VER = _cb_il.import_module(_cb_c[-1].stem), _cb_c[-1].stem
            except Exception:  # noqa: BLE001
                _ACCEL = None
        break
    _cb_p = _cb_p.parent
if _ACCEL is None:
    try:
        import VeritasCeleritas_v1141 as _ACCEL  # noqa: F401  退回鎖版
        _ACCEL_VER = "VeritasCeleritas_v1141"
    except Exception:  # noqa: BLE001
        _ACCEL = None


def _net():
    """正本網路工具(只在需要出網時載入;本引擎不出網)。"""
    try:
        import VeritasAegisNexus_v1652 as _NET  # noqa: WPS433
        return _NET
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import ast
import datetime
import hashlib
import html
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0175"


def _vnum_v0175(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0175(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0175(p) < _vnum_v0175(__file__)), key=_vnum_v0175)
PRIOR = _load_v0175(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def _owner(name):
    import types
    mod, seen = PRIOR, set()
    while isinstance(mod, types.ModuleType) and id(mod) not in seen:
        seen.add(id(mod))
        if name in vars(mod):
            return mod
        mod = vars(mod).get("PRIOR")
    return None


def _resolve(name):
    m = _owner(name)
    return vars(m)[name] if m else None


def _job_entry(kind, item):
    return _resolve("_job")(kind, item)


def _init_entry(*args):
    return _resolve("_init_entry")(*args)


_rep, _home = _resolve("_rep"), _resolve("_home")
SKIP_DIRS = re.compile(r"(^|[\\/])(_quarantine|_retired|_superseded|_archive|__pycache__|\.git|\.venv|venv|envs|evidence|tests?|node_modules|_staging)([\\/]|$)", re.I)
FAMILY = re.compile(r"^(?P<fam>.+?)_v(?P<ver>\d{3,4})\.(?P<ext>py|ps1)$", re.I)
HOT = 3
HEAVY = ("camelot", "tabula", "img2table")

# ───────── 進度:加「實測」段(讀表實測不再無聲)─────────
_m166 = _owner("_RANGE")
if _m166 is not None and isinstance(vars(_m166).get("_RANGE"), dict) and "實測" not in vars(_m166)["_RANGE"]:
    vars(_m166)["_RANGE"]["實測"] = (95, 99)
    vars(_m166)["_RX"] = re.compile(r"^\s*\[進度\]\s*(\d+)\s*/\s*(\d+)\s*·\s*(?:(分類|取頁|還原|切塊|OCR|實測)\s*·\s*)?(?:([A-Z—-]+)\s*·\s*)?(.*)$")


# ───────── 重型讀表器:子程序 + 逾時(逾時 = 失敗,不再卡住)─────────
_SUB = r"""
import importlib.util, json, sys
s = importlib.util.spec_from_file_location("th", sys.argv[1]); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
bb = json.loads(sys.argv[4])
r = m.nonocr_tables(sys.argv[2], int(sys.argv[3]), bb, sys.argv[5])
print("\n@@JSON@@" + json.dumps(r, ensure_ascii=False, default=str))
"""


def guarded_tables(th_path: str, prev, pdf: str, page: int, bbox=None, backend: str = "pymupdf_lines", timeout: int = 25) -> dict:
    if not backend.startswith(HEAVY):
        return prev(pdf, page, bbox, backend)
    t0 = time.time()
    flags = 0x00000200 if os.name == "nt" else 0          # CREATE_NEW_PROCESS_GROUP:逾時整棵(含 java)一起收
    p = subprocess.Popen([sys.executable, "-c", _SUB, th_path, pdf, str(page), json.dumps(bbox), backend], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                         text=True, encoding="utf-8", errors="replace", creationflags=flags)
    try:
        out, _ = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True)
        else:
            p.kill()
        try:
            p.communicate(timeout=5)
        except Exception:  # noqa: BLE001
            pass
        return {"status": "error", "backend": backend, "why": "逾時 %d 秒(視為失敗)" % timeout, "ms": int((time.time() - t0) * 1000)}
    if "@@JSON@@" in (out or ""):
        try:
            return json.loads(out.split("@@JSON@@")[-1].strip())
        except ValueError:
            pass
    return {"status": "error", "backend": backend, "why": "子程序沒有回結果", "ms": int((time.time() - t0) * 1000)}


def _guard_toolhub():
    try:
        th = (_resolve("toolhub") or (lambda: None))()
    except Exception:  # noqa: BLE001
        return None
    if th is None or getattr(th.nonocr_tables, "_v175", False):
        return th
    prev = th.nonocr_tables
    path = str(getattr(th, "__file__", "") or "")

    def nonocr_tables(pdf, page, bbox=None, backend="pymupdf_lines"):
        return guarded_tables(path, prev, pdf, page, bbox, backend, int(os.environ.get("VIA_VRN_READER_TIMEOUT", "25") or 25))
    nonocr_tables._v175 = True
    th.nonocr_tables = nonocr_tables
    return th


_guard_toolhub()


# ───────── 讀表實測:有進度 · 用受保護的讀表器(取代 v0174 的無聲版)─────────
def auto_bench_v175(d: Path, th, budget: int) -> dict:
    vt = _resolve("_ORIG_VT") or _resolve("verify_table")
    real = _resolve("_real_table") or (lambda rows, v: True)
    fast = list(_resolve("FAST") or ["pymupdf_lines", "pymupdf_text", "pdfplumber_lines", "pdfplumber_text"])
    failed, trset = [], []
    for p in sorted(d.glob("*.json")) if d else []:
        try:
            j = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        row = j.get("row") or {}
        picked = list(row.get("picked") or [])
        if not row.get("mini") or not Path(row["mini"]).exists():
            continue
        for pi, pg in enumerate(j.get("pages", [])):
            orig = int(pg.get("page") or pi + 1)
            local = (picked.index(orig) + 1) if orig in picked else pi + 1
            for b in pg.get("blocks", []):
                if b.get("kind") != "table" or not str(b.get("sub", "")).startswith(("財務表", "估值表")):
                    continue
                v = b.get("verify") or {}
                if "TableRepair" in str(b.get("engine", "")) or str(v.get("native", "")).startswith("雙讀一致"):
                    trset.append((row["mini"], local, b))
                elif not v.get("ok"):
                    failed.append((row["mini"], local, b))
    orig_b = list(_resolve("_ORIG_BACKENDS") or []) or list(getattr(th, "TABLE_BACKENDS", []))
    pr = {r["id"]: r["status"] for r in th.probe_tools()}
    tool_of = lambda k: {"pymupdf": "pymupdf", "pdfplumber": "pdfplumber", "camelot": "camelot", "tabula": "tabula", "img2table": "img2table"}[k.split("_")[0]]  # noqa: E731
    by = {k: {"tried": 0, "ok": 0, "ms": 0, "installed": pr.get(tool_of(k)) == "ok", "timeouts": 0} for k in orig_b}
    import pdfplumber  # noqa: WPS433
    t0 = time.time()
    todo = [("沒過", x) for x in failed[:60]] + [("雙讀", x) for x in trset[:30]]
    res = {"failed_total": len(failed), "failed_done": 0, "failed_rescued": 0, "tr_total": len(trset), "tr_done": 0, "tr_alt_cover": 0}
    for i, (kind, (mini, local, b)) in enumerate(todo, 1):
        if time.time() - t0 > budget:
            break
        print("  [進度] %d/%d · 實測 · — · %s %s" % (i, len(todo), kind, b.get("id")), flush=True)
        ks = orig_b if kind == "沒過" else [k for k in fast if k in by]
        bb = [float(b["x0"]) - 3, max(0.0, float(b["top"]) - 42), float(b["x1"]) + 3, float(b["bottom"]) + 3]
        hit = []
        with pdfplumber.open(mini) as pdf:
            pp = pdf.pages[local - 1]
            for k in ks:
                if not by[k]["installed"] or time.time() - t0 > budget:
                    continue
                r = th.nonocr_tables(mini, local, bb, k)
                by[k]["tried"] += 1
                by[k]["ms"] += r.get("ms", 0)
                by[k]["timeouts"] += 1 if "逾時" in str(r.get("why", "")) else 0
                best, bov = None, -1.0
                for t in (r.get("tables") or []) if r.get("status") == "ok" else []:
                    tb = t.get("bbox") or bb
                    ov = max(0.0, min(tb[2], b["x1"]) - max(tb[0], b["x0"])) * max(0.0, min(tb[3], b["bottom"]) - max(tb[1], b["top"]))
                    if ov > bov:
                        best, bov = t, ov
                if best and best["rows"]:
                    try:
                        vv = vt(dict(b, rows=best["rows"]), pp)
                        if vv.get("ok") and real(best["rows"], vv):
                            by[k]["ok"] += 1
                            hit.append(k)
                    except Exception:  # noqa: BLE001
                        pass
        if kind == "沒過":
            res["failed_done"] += 1
            res["failed_rescued"] += 1 if hit else 0
        else:
            res["tr_done"] += 1
            res["tr_alt_cover"] += 1 if hit else 0
    res.update(by=by, secs=int(time.time() - t0))
    return res


_m174 = _owner("auto_bench")
if _m174 is not None and not getattr(vars(_m174)["auto_bench"], "_v175", False):
    auto_bench_v175._v175 = True
    setattr(_m174, "auto_bench", auto_bench_v175)


# ───────── 修正閘:盤點 · 靜態 · 加速器 · 九頭龍 · 指紋 · 錨點 ─────────
def tails(root: Path) -> dict:
    fams, solo = {}, {}
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in (".py", ".ps1") or SKIP_DIRS.search(str(p.relative_to(root))):
            continue
        m = FAMILY.match(p.name)
        if m:
            k = (str(p.parent.relative_to(root)), m.group("fam"), m.group("ext").lower())
            if k not in fams or int(m.group("ver")) > int(FAMILY.match(fams[k].name).group("ver")):
                fams[k] = p
        else:
            solo[str(p.relative_to(root))] = p
    out = {str(p.relative_to(root)): p for p in fams.values()}
    out.update(solo)
    return out


def static_check(files: dict) -> dict:
    bad = {}
    for rel, p in files.items():
        if p.suffix.lower() != ".py":
            continue
        try:
            src = p.read_text(encoding="utf-8-sig", errors="replace")
            compile(ast.parse(src), str(p), "exec", dont_inherit=True)
        except SyntaxError as exc:
            bad[rel] = "語法錯 第 %s 行" % exc.lineno
        except Exception as exc:  # noqa: BLE001
            bad[rel] = "編譯失敗 %s" % type(exc).__name__
    ps = [str(p) for p in files.values() if p.suffix.lower() == ".ps1"]
    pw = shutil.which("pwsh") or shutil.which("powershell")
    ps_state = "ABSENT"
    if ps and pw:
        lst = Path(os.environ.get("VIA_SPILL_DIR") or os.environ.get("TEMP") or "/tmp") / ("vrn_gate_ps_%d.json" % os.getpid())
        lst.write_text(json.dumps(ps, ensure_ascii=False), encoding="utf-8")
        cmd = ("$l = Get-Content -LiteralPath '%s' -Raw -Encoding UTF8 | ConvertFrom-Json; foreach ($f in $l) { $t = $null; $e = $null; "
               "[void][System.Management.Automation.Language.Parser]::ParseFile($f, [ref]$t, [ref]$e); if ($e.Count) { '@@ERR@@' + $f + '|' + $e[0].Extent.StartLineNumber + '|' + $e[0].Message } }") % str(lst).replace("'", "''")
        try:
            r = subprocess.run([pw, "-NoProfile", "-NonInteractive", "-Command", cmd], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
            ps_state = "OK"
            for ln in (r.stdout or "").splitlines():
                if ln.startswith("@@ERR@@"):
                    f, line, msg = (ln[7:].split("|", 2) + ["", ""])[:3]
                    rel = next((k for k, v in files.items() if str(v) == f), f)
                    bad[rel] = "PS 剖析錯 第 %s 行 · %s" % (line, msg[:60])
        except Exception:  # noqa: BLE001
            ps_state = "ERROR"
        finally:
            try:
                lst.unlink()
            except OSError:
                pass
    return {"bad": bad, "py": sum(1 for p in files.values() if p.suffix.lower() == ".py"), "ps1": len(ps), "ps_parser": ps_state}


def latest_accel(start: Path) -> str:
    p = start.resolve()
    while p.parent != p:
        sup = p / "supportive modules"
        if sup.is_dir():
            c = sorted(list(sup.glob("VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")) + list(sup.glob("*/VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")),
                       key=lambda x: int(re.search(r"_v(\d{4})", x.name).group(1)))
            return c[-1].stem if c else ""
        p = p.parent
    return ""


def accel_kind(text: str, ext: str, latest: str) -> tuple:
    if ext == ".ps1":
        ok = "CELERITAS-TEMPLATE-JOIN" in text and "[VIA:PS-ACCEL" in text
        return ("PS 加速橋", "GREEN") if ok else ("缺 PS 加速橋標記", "OP-300")
    if "[VIA:ACCEL-BRIDGE" not in text:
        return "缺加速器標記", "OP-300"
    if "VIA:ACCEL-BRIDGE:v0111" in text:
        return "版號橋 · 動態最新", "GREEN"
    m = re.search(r"VeritasCeleritas_v(\d{4})", text)
    if m:
        if latest and int(re.search(r"(\d{4})$", latest).group(1)) > int(m.group(1)):
            return "版號橋 · 寫死 v%s(最新 %s)" % (m.group(1), latest), "OP-300"
        return "版號橋 · v%s" % m.group(1), "GREEN"
    if "VIA_SuperAccel_Module" in text:
        return "舊橋(轉接 SUP_MDL737 → 正本)", "OP-400"
    return "加速器標記但沒接正本", "OP-300"


def hydra_heads(root: Path) -> dict:
    heads = defaultdict(list)
    chain = sorted((p for p in root.glob(_STEM + "_v*.py") if _vnum_v0175(p) >= 127), key=_vnum_v0175)
    for p in chain:
        v = "%04d" % _vnum_v0175(p)
        try:
            t = ast.parse(p.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        defs = {n.name for n in ast.walk(t) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
        for n in ast.walk(t):
            tgt = None
            if isinstance(n, ast.Call):
                fn = n.func
                nm = fn.id if isinstance(fn, ast.Name) else (fn.attr if isinstance(fn, ast.Attribute) else "")
                if nm == "setattr" and len(n.args) >= 2 and isinstance(n.args[1], ast.Constant) and isinstance(n.args[1].value, str):
                    tgt = n.args[1].value
                elif nm in ("_patch", "_patch_v") and n.args and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str):
                    tgt = n.args[0].value
            elif isinstance(n, ast.Assign) and n.targets:
                tg = n.targets[0]
                if isinstance(tg, ast.Subscript) and isinstance(tg.value, ast.Call) and getattr(tg.value.func, "id", "") == "vars":
                    sl = tg.slice.value if hasattr(tg.slice, "value") and not isinstance(tg.slice, ast.Constant) else tg.slice
                    if isinstance(sl, ast.Constant) and isinstance(sl.value, str):
                        tgt = sl.value
                elif isinstance(tg, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id in defs:
                    tgt = tg.attr
            if tgt and not tgt.startswith("__") and v not in heads[tgt]:
                heads[tgt].append(v)
    return dict(heads)


def fingerprint(root: Path) -> dict:
    out = {}
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in (".py", ".ps1") and not SKIP_DIRS.search(str(p.relative_to(root))):
            out[str(p.relative_to(root))] = hashlib.sha256(p.read_bytes()).hexdigest()[:16]
    return out


def anchors(root: Path, newest: Path) -> list:
    """最新尾版的每個替換點:精準錨點(擁有者檔 · 行 · def 結構雜湊)/ 彈性錨點(名 · 參數)。"""
    try:
        t = ast.parse(newest.read_text(encoding="utf-8"))
    except SyntaxError:
        return []
    defs = {n.name for n in ast.walk(t) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    names = []
    for n in ast.walk(t):
        if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "setattr" and len(n.args) >= 2 and isinstance(n.args[1], ast.Constant):
            names.append(n.args[1].value)
        elif isinstance(n, ast.Assign) and n.targets and isinstance(n.targets[0], ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id in defs:
            names.append(n.targets[0].attr)
    cands = sorted([p for p in root.glob(_STEM + "_v*.py") if _vnum_v0175(p) < _vnum_v0175(newest)], key=_vnum_v0175, reverse=True)
    cands += sorted((root / "intake").rglob("*_v*.py"), key=lambda p: p.name, reverse=True) if (root / "intake").is_dir() else []
    out = []
    for nm in dict.fromkeys(names):
        hit = None
        for p in cands:
            try:
                tt = ast.parse(p.read_text(encoding="utf-8"))
            except (SyntaxError, OSError):
                continue
            for d in tt.body:
                if isinstance(d, ast.FunctionDef) and d.name == nm:
                    hit = (p, d)
                    break
            if hit:
                break
        if hit:
            p, d = hit
            out.append({"target": nm, "precise": "%s:%d#%s" % (p.name, d.lineno, hashlib.sha1(ast.dump(d).encode()).hexdigest()[:12]),
                        "elastic": "%s(%s)" % (nm, ", ".join(a.arg for a in d.args.args)), "resolved": "精準"})
        else:
            out.append({"target": nm, "precise": "—", "elastic": nm, "resolved": "沒找到"})
    return out


def chain_selftest(tail: Path, timeout: int = 1800) -> dict:
    t0 = time.time()
    env = dict(os.environ)
    env.pop("VIA_SKIP_PRIOR_SELFTEST", None)
    try:
        r = subprocess.run([sys.executable, "-W", "ignore", str(tail), "--selftest"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout, env=env, cwd=str(tail.parent))
        txt, rc = (r.stdout or "") + (r.stderr or ""), r.returncode
    except subprocess.TimeoutExpired:
        return {"fails": set(), "crash": "逾時 %d 秒" % timeout, "secs": int(time.time() - t0)}
    norm = lambda s: re.sub(r"\s+", " ", re.sub(r"\d+(\.\d+)?", "#", s)).strip()[:80]  # noqa: E731
    fails = {norm(l.split("[FAIL]", 1)[1]) for l in txt.splitlines() if "[FAIL]" in l and "前版鏈" not in l}
    crash = "Traceback" if re.search(r"^Traceback", txt, re.M) else ""
    return {"fails": fails, "crash": crash, "secs": int(time.time() - t0), "rc": rc}


def panorama_monitor(vrn_real: Path, out: Path) -> dict:
    """VCGC 全景(只讀監控 · 互相監控不連結):找不到 = ABSENT。"""
    p = vrn_real.resolve()
    root = None
    while p.parent != p:
        if (p / "supportive modules").is_dir():
            root = p
            break
        p = p.parent
    eng = sorted((root / "supportive modules" / "registry").glob("VIA_Panorama_v*.py"), key=_vnum_v0175) if root else []
    if not eng:
        return {"state": "ABSENT", "why": "VCGC 全景引擎不在本機"}
    out.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run([sys.executable, "-W", "ignore", str(eng[-1]), str(root), "--profile", "via", "--scope", "VRN", "--static", "--json-only", "--no-git", "--out", str(out)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
        r = json.loads((out / "panorama_latest.json").read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return {"state": "ERROR", "why": "%s" % type(exc).__name__, "engine": eng[-1].name}
    S = r.get("sections") or {}
    g = (S.get("G") or {}).get("summary") or {}
    F = S.get("F") or {}
    return {"state": "OK", "engine": eng[-1].name, "verdict": r.get("verdict"), "ratchet": g.get("verdict"), "red_now": g.get("now"), "red_prev": g.get("prev"),
            "c_bad": [(x.get("key"), x.get("lamp"), x.get("first_missing")) for x in (S.get("C") or {}).get("rows") or [] if x.get("lamp") not in ("GREEN", "ABSENT")],
            "f": {x.get("key"): x.get("n") for x in F.get("rows") or []}, "op300": [x.get("rel") for x in ((F.get("detail") or {}).get("op300") or [])][:50]}


def triage_last_run(rep: Path) -> dict:
    rv = rep.parent / "review" if rep.name.lower() == "vrn" else rep / "review"
    ds = sorted((d for d in rv.glob("ps_*") if d.is_dir()), key=lambda d: d.stat().st_mtime) if rv.is_dir() else []
    if not ds:
        return {"state": "NODATA"}
    d = ds[-1]
    py = d / "B.python.log"
    prog = (d / "B.progress").read_text(encoding="utf-8", errors="replace").strip() if (d / "B.progress").exists() else ""
    if not (d / "paste.md").exists() and not py.exists():
        return {"state": "中斷", "run": d.name, "why": "沒有 paste.md / python 記錄(啟動器沒走到結尾)· 最後進度 %s" % prog[:80], "fix": "不可同步(人為中斷)· 沿用已完成的輸出(auto --resume)"}
    t = py.read_text(encoding="utf-8", errors="replace") if py.exists() else ""
    if re.search(r"ModuleNotFoundError|No module named|ImportError|FileNotFoundError|PermissionError|MemoryError|找不到", t):
        return {"state": "環境", "run": d.name, "why": (re.findall(r".*(?:ModuleNotFoundError|ImportError|FileNotFoundError|PermissionError|MemoryError).*", t) or ["—"])[-1][:120],
                "fix": "不可同步 · 經 VCGC 安裝 / 設定"}
    if "Traceback" in t:
        return {"state": "真錯", "run": d.name, "why": (re.findall(r"^\w*Error.*$", t, re.M) or ["Traceback"])[-1][:120], "fix": "依錨點分類"}
    return {"state": "正常", "run": d.name, "why": prog[:80]}



def _rep_for(real: Path) -> Path:
    if os.environ.get("VIA_VRN_HEALTH_OUT"):
        return Path(os.environ["VIA_VRN_HEALTH_OUT"])
    p = real.resolve()
    while p.parent != p:
        if (p / "supportive modules").is_dir() or (p / "VIA_Reports").is_dir():
            return p / "VIA_Reports" / "vrn"
        p = p.parent
    return _rep()


def selfgate_run(mode: str = "quick", vrn_dir: Path = None, real_dir: Path = None, panorama: bool = True) -> dict:
    vrn = Path(vrn_dir or HERE)
    real = Path(real_dir or os.environ.get("VIA_VRN_SANDBOX_OF") or vrn)
    rep = _rep_for(real)
    out = rep / "selfgate"
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    red, sync, nonsync, rows = [], [], [], []
    T = tails(vrn)
    fp = fingerprint(vrn)
    snap_p = out / "snapshot_latest.json"
    prev = None
    if mode == "quick" and snap_p.exists():
        try:
            prev = json.loads(snap_p.read_text(encoding="utf-8"))
        except ValueError:
            prev = None
    if mode == "quick" and prev and prev.get("fp") == fp and prev.get("verdict") != "RED":
        return dict(prev.get("result") or {}, cached=True, secs=int(time.time() - t0))
    if mode == "sandbox":
        staged = sorted(rel for rel in fp if not (real / rel).exists())
        modified = sorted(rel for rel in fp if (real / rel).exists() and hashlib.sha256((real / rel).read_bytes()).hexdigest()[:16] != fp[rel])
        prev_heads = hydra_heads(real)
    else:
        staged = sorted(rel for rel in fp if prev and rel not in prev.get("fp", {})) if prev else []
        modified = sorted(rel for rel in fp if prev and rel in prev.get("fp", {}) and prev["fp"][rel] != fp[rel]) if prev else []
        prev_heads = (prev or {}).get("hydra")
    st = static_check(T if mode == "quick" else {k: v for k, v in T.items() if k in staged or k in T})
    bad_new = {k: v for k, v in st["bad"].items() if k in staged}
    bad_old = {k: v for k, v in st["bad"].items() if k not in staged}
    for k, v in bad_new.items():
        red.append("新檔 %s %s" % (k, v))
    for k, v in bad_old.items():
        nonsync.append({"cls": "OP-500", "what": "既有尾版 %s" % v, "file": k})
    latest = latest_accel(real) or latest_accel(vrn)
    acc = {}
    for rel, p in T.items():
        try:
            acc[rel] = accel_kind(p.read_text(encoding="utf-8", errors="replace"), p.suffix.lower(), latest)
        except OSError:
            continue
    for rel, (kind, cls) in acc.items():
        if cls == "GREEN":
            continue
        if rel in staged:
            red.append("新檔 %s 加速器不合格(%s)" % (rel, kind))
        else:
            sync.append({"cls": cls, "what": kind, "file": rel})
    H = hydra_heads(vrn)
    added = {}
    if prev_heads is not None:
        for tgt, vs in H.items():
            before = len(prev_heads.get(tgt, []))
            if len(vs) > before:
                added[tgt] = (before, len(vs))
                if before >= HOT or len(vs) >= HOT:
                    red.append("九頭龍:%s 從 %d 頭變 %d 頭(熱點不准再加頭)" % (tgt, before, len(vs)))
    hot = sorted(((t, vs) for t, vs in H.items() if len(vs) >= HOT), key=lambda kv: -len(kv[1]))
    for t, vs in hot:
        nonsync.append({"cls": "OP-500", "what": "九頭龍熱點 %s %d 頭(%s)→ 需整併版" % (t, len(vs), ",".join(vs)), "file": t})
    for rel in modified:
        red.append("既有檔被改動 %s(違反只增不減)" % rel)
    newest = max(vrn.glob(_STEM + "_v*.py"), key=_vnum_v0175, default=None)
    A = anchors(vrn, newest) if newest else []
    for a in A:
        if a["resolved"] == "沒找到":
            red.append("AST 錨點沒找到:%s(替換目標不存在)" % a["target"])
    sbx = {}
    if mode == "sandbox":
        olds = [p for p in vrn.glob(_STEM + "_v*.py") if str(p.relative_to(vrn)) not in staged]
        old_tail = max(olds, key=_vnum_v0175, default=None)
        if newest and old_tail and newest != old_tail:
            from concurrent.futures import ThreadPoolExecutor  # noqa: WPS433
            to = int(os.environ.get("VIA_VRN_GATE_SELFTEST_SEC", "1800") or 1800)
            with ThreadPoolExecutor(2) as ex:
                fo, fn = ex.submit(chain_selftest, old_tail, to), ex.submit(chain_selftest, newest, to)
                ro, rn = fo.result(), fn.result()
            newf = sorted(rn["fails"] - ro["fails"])
            sbx = {"old": old_tail.name, "new": newest.name, "old_fails": len(ro["fails"]), "new_fails": len(rn["fails"]), "added": newf, "old_secs": ro["secs"], "new_secs": rn["secs"],
                   "crash": rn.get("crash", ""), "old_crash": ro.get("crash", "")}
            if ro.get("crash"):
                sbx["note"] = "舊尾版自測%s → 基準不可信:新尾版的失敗全部當新增(保守)" % ("逾時" if "逾時" in ro["crash"] else "崩潰")
            for x in newf:
                red.append("在地測試:新尾版多出失敗「%s」" % x)
            if rn.get("crash"):
                red.append("在地測試:新尾版自測%s" % ("逾時" if "逾時" in rn["crash"] else "崩潰(Traceback)"))
        else:
            sbx = {"note": "沒有新管理器尾版 → 只做靜態 / 加速器 / 九頭龍 / 錨點"}
    pm = {"state": "SKIP"}
    if mode == "quick" and panorama:
        pm = panorama_monitor(real, out / "panorama")
        if pm.get("state") == "OK" and pm.get("ratchet") == "RETROGRESS":
            red.append("VCGC 全景棘輪退步(紅 %s → %s)" % (pm.get("red_prev"), pm.get("red_now")))
    tr = triage_last_run(rep) if mode == "quick" else {"state": "SKIP"}
    if tr.get("state") in ("環境",):
        nonsync.append({"cls": "環境", "what": tr.get("why", ""), "file": tr.get("run", "")})
    verdict = "RED" if red else ("YELLOW" if (sync or nonsync or pm.get("state") not in ("OK", "SKIP")) else "GREEN")
    cs = Counter(x["cls"] for x in sync)
    res = {"mode": mode, "verdict": verdict, "red": red, "sync": sync, "nonsync": nonsync, "tails_py": st["py"], "tails_ps1": st["ps1"], "ps_parser": st["ps_parser"],
           "bad_new": bad_new, "bad_old": bad_old, "latest_accel": latest, "accel": dict(Counter(k for k, _ in acc.values())), "accel_cls": dict(cs),
           "hydra_targets": len(H), "hot": [(t, len(vs)) for t, vs in hot], "added": {k: list(v) for k, v in added.items()}, "staged": staged, "modified": modified,
           "anchors": A, "sandbox": sbx, "panorama": pm, "triage": tr, "secs": int(time.time() - t0), "cached": False}
    ts = datetime.datetime.now().isoformat(timespec="seconds")
    with (out / ("VRN_SelfGate_Ledger.jsonl")).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"ts": ts, "mode": mode, "verdict": verdict, "red": red, "sync": len(sync), "nonsync": len(nonsync), "staged": len(staged), "modified": len(modified),
                             "hot": res["hot"], "sandbox": {k: v for k, v in sbx.items() if k != "added"}}, ensure_ascii=False, default=str) + "\n")
    if mode == "quick" and verdict != "RED":
        snap_p.write_text(json.dumps({"ts": ts, "fp": fp, "hydra": H, "verdict": verdict, "result": res}, ensure_ascii=False, default=str), encoding="utf-8")
    page = _resolve("_page")
    if page:
        R = []
        R.append(("RED" if bad_new else ("YELLOW" if bad_old else "GREEN"), ["MODULE", "靜態(ast / compile 不執行 · PS Parser)", len(st["bad"]), "新檔 %d · 既有 %d · PS 剖析 %s" % (len(bad_new), len(bad_old), st["ps_parser"])]))
        R.append(("YELLOW" if sync else "GREEN", ["ENGINE", "加速器(最新 %s)" % (latest or "—"), len(acc), " · ".join("%s %d" % kv for kv in Counter(k for k, _ in acc.values()).most_common())]))
        R.append(("RED" if any("九頭龍" in x for x in red) else ("YELLOW" if hot else "GREEN"), ["FUNCTION-LIB", "九頭龍(執行期替換頭數)", len(H), " · ".join("%s %d 頭" % (t, n) for t, n in res["hot"]) or "無熱點"]))
        R.append(("RED" if any("錨點" in x for x in red) else "GREEN", ["FUNCTION-LIB", "AST 錨點(%s)" % (newest.name if newest else "—"), len(A), " · ".join("%s → %s" % (a["target"], a["precise"] if a["resolved"] == "精準" else "沒找到") for a in A)[:300]]))
        R.append(("RED" if modified else "GREEN", ["OTHERS", "只增不減(既有檔被改動)", len(modified), ", ".join(modified[:6]) or "沒有"]))
        if mode == "sandbox":
            R.append(("RED" if any("在地測試" in x for x in red) else "GREEN", ["OTHERS", "在地測試(新舊尾版整條鏈自測)", len(sbx.get("added", [])), json.dumps({k: v for k, v in sbx.items() if k != "added"}, ensure_ascii=False)[:300]]))
        R.append(({"OK": "GREEN" if pm.get("ratchet") != "RETROGRESS" else "RED"}.get(pm.get("state"), "GRAY"), ["OTHERS", "VCGC 全景監控(只讀 · 互相監控)", len(pm.get("c_bad") or []),
                  "%s · 總判 %s · 棘輪 %s" % (pm.get("engine", pm.get("why", pm.get("state"))), pm.get("verdict", "—"), pm.get("ratchet", "—"))]))
        R.append(({"中斷": "YELLOW", "環境": "YELLOW", "真錯": "RED"}.get(tr.get("state"), "GRAY"), ["OTHERS", "上一輪分診", 1, "%s · %s · %s" % (tr.get("state"), tr.get("run", ""), tr.get("why", ""))[:300]]))
        for x in sync[:60]:
            R.append(("YELLOW", ["可同步修正", x["cls"] + " · " + x["what"], 1, x["file"]]))
        for x in nonsync[:40]:
            R.append(("YELLOW", ["不可同步修正", x["cls"] + " · " + x["what"], 1, x["file"]]))
        for x in red:
            R.append(("RED", ["紅(擋下)", x[:120], 1, ""]))
        (out / ("SELFGATE_%s_latest.html" % ("SANDBOX" if mode == "sandbox" else "QUICK"))).write_text(page("VRN 修正閘(%s)· 判定 %s" % ("在地測試 · 沙盒" if mode == "sandbox" else "快查 · 真實樹", verdict),
            "%s · %d 秒 · 可同步 %d · 不可同步 %d · 紅 %d" % (html.escape(str(vrn)), res["secs"], len(sync), len(nonsync), len(red)), ["區", "項目", "數", "說明"], R), encoding="utf-8")
        res["html"] = str(out / ("SELFGATE_%s_latest.html" % ("SANDBOX" if mode == "sandbox" else "QUICK")))
    return res


def _print_gate(o: dict) -> int:
    if o.get("cached"):
        print("[計] 修正閘(VRN 自己)· 指紋沒變 → 沿用上次判定 %s(%d 秒)" % (o.get("verdict"), o.get("secs", 0)))
        return {"RED": 1, "YELLOW": 2}.get(o.get("verdict"), 0)
    cs = Counter(x["cls"] for x in o["sync"])
    print("[計] 修正閘(VRN 自己 · %s)· 判定 %s · 尾版 py %d / ps1 %d · 新檔 %d · 既有檔被改 %d · %d 秒" % ("在地測試" if o["mode"] == "sandbox" else "快查", o["verdict"], o["tails_py"], o["tails_ps1"],
                                                                                      len(o["staged"]), len(o["modified"]), o["secs"]))
    print("[計] 靜態(不執行)· 語法 / 編譯錯 新 %d · 既有 %d · PS 剖析 %s" % (len(o["bad_new"]), len(o["bad_old"]), o["ps_parser"]))
    print("[計] 加速器 · 最新版號 %s · " % (o["latest_accel"] or "—") + " · ".join("%s %d" % kv for kv in Counter(o["accel"]).most_common()))
    print("[計] 九頭龍 · 執行期替換 %d 個目標 · 熱點(≥%d 頭)%s · 本次新增頭 %s" % (o["hydra_targets"], HOT, " · ".join("%s %d" % kv for kv in o["hot"]) or "無",
                                                                         " · ".join("%s %d→%d" % (k, a, b) for k, (a, b) in o["added"].items()) or "無"))
    print("[計] AST 錨點 · 最新尾版替換點 %d · 精準 %d · 沒找到 %d" % (len(o["anchors"]), sum(1 for a in o["anchors"] if a["resolved"] == "精準"), sum(1 for a in o["anchors"] if a["resolved"] != "精準")))
    if o["mode"] == "sandbox":
        s = o["sandbox"]
        print("[計] 在地測試 · " + ("舊尾版 %s FAIL %d(%d 秒)· 新尾版 %s FAIL %d(%d 秒)· 新增失敗 %d%s" % (s.get("old"), s.get("old_fails", 0), s.get("old_secs", 0), s.get("new"), s.get("new_fails", 0),
                                                                                           s.get("new_secs", 0), len(s.get("added", [])), (" · " + s["crash"]) if s.get("crash") else "") if s.get("old") else s.get("note", "")))
    pm = o["panorama"]
    if pm.get("state") != "SKIP":
        print("[計] VCGC 全景監控(只讀 · 互相監控不連結)· %s · 總判 %s · 棘輪 %s(紅 %s → %s)" % (pm.get("engine", pm.get("why", pm.get("state"))), pm.get("verdict", "—"), pm.get("ratchet", "—"),
                                                                                      pm.get("red_prev", "—"), pm.get("red_now", "—")))
    tr = o["triage"]
    if tr.get("state") not in ("SKIP", "NODATA"):
        print("[計] 上一輪分診 · %s · %s · %s" % (tr.get("state"), tr.get("run", ""), tr.get("why", "")[:120]))
    print("[計] 分類 · 可同步修正 %d(%s)· 不可同步 %d(熱點 %d · 既有語法 %d · 環境 %d)" % (len(o["sync"]), " · ".join("%s %d" % kv for kv in cs.most_common()) or "—", len(o["nonsync"]),
                                                                        len(o["hot"]), len(o["bad_old"]), sum(1 for x in o["nonsync"] if x["cls"] == "環境")))
    for x in o["red"][:12]:
        print("  [RED] 修正閘 · %s" % x)
    if o.get("html"):
        print("  [U/I] %s" % o["html"])
    return {"RED": 1, "YELLOW": 2}.get(o["verdict"], 0)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()
    if args[:1] == ["selfgate"]:
        return _print_gate(selfgate_run("sandbox" if "--sandbox" in args else "quick", panorama="--no-panorama" not in args))
    if args[:1] == ["auto"] and "--resume" in args:
        d = _resolve("_latest_l2_dir")("")
        rep = _rep()
        need = [(rep / "restore" / "RESTORE_SUMMARY_latest.json", "restore"), (rep / "basicinfo" / "BASIC_INFO_latest.json", "basicinfo")]
        bad = []
        for p, nm in need:
            try:
                lr = json.loads(p.read_text(encoding="utf-8")).get("layout_run")
            except (OSError, ValueError):
                lr = None
            if not d or lr != d.parent.name:
                bad.append("%s(%s)" % (nm, "沒有" if lr is None else "不是同一輪 layout"))
        if bad:
            print("[計] 自動實測優化 · --resume 不能用:%s → 請跑完整 auto · RED" % " · ".join(bad))
            return 1
        print("[計] 自動實測優化 · --resume:沿用 layout(%s)· restore · basicinfo 的輸出(同輸入不重跑)→ 只做 讀表實測 · KPI · 決策 · 台帳" % d.parent.name, flush=True)
        m = _owner("auto_run")
        orig, orig_la = vars(m)["auto_run"], vars(m)["ledger_append"]
        setattr(m, "auto_run", lambda runner=None, skip_layout=False, layout_extra=None: orig(runner=lambda a: 0, skip_layout=True))
        setattr(m, "ledger_append", lambda rec, home=None: orig_la(dict(rec, mode="resume(沿用已完成輸出 · 不重跑)"), home))
        try:
            return PRIOR.main(["auto"])
        finally:
            setattr(m, "auto_run", orig)
            setattr(m, "ledger_append", orig_la)
    return PRIOR.main(args)



def selftest() -> int:
    import tempfile
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)
    td = Path(tempfile.mkdtemp(prefix="vrn175-"))
    saved = {k: os.environ.get(k) for k in ("VIA_VRN_HEALTH_OUT", "VIA_SPILL_DIR", "VIA_VRN_SANDBOX_OF", "VIA_VRN_GATE_SELFTEST_SEC")}
    try:
        br = Path(__file__).read_text(encoding="utf-8")
        i, j = br.index("# ===== [VIA:ACCEL-BRIDGE:v0111]"), br.index("# ===== [VIA:ACCEL-BRIDGE:END] =====")
        blk = br[i:j] + "# ===== [VIA:ACCEL-BRIDGE:END] =====\n"
        root = td / "VIA"
        sup = root / "supportive modules"
        sup.mkdir(parents=True)
        for v in ("1141", "1142"):
            (sup / ("VeritasCeleritas_v%s.py" % v)).write_text("V = '%s'\n" % v, encoding="utf-8")
        vrn = root / "functional modules" / "VRN"
        vrn.mkdir(parents=True)
        (vrn / "probe.py").write_text(blk + "\nprint(_ACCEL_VER)\n", encoding="utf-8")
        got = subprocess.run([sys.executable, str(vrn / "probe.py")], capture_output=True, text=True).stdout.strip()
        chk("① 加速器橋 v0111:最新有版號 → 挑 VeritasCeleritas_v1142(不寫死 v1141)→ %s" % got, got == "VeritasCeleritas_v1142")
        (vrn / "probe.py").unlink()
        W = lambda n, s: (vrn / n).write_text(s, encoding="utf-8")  # noqa: E731
        W("A_v0100.py", "# [VIA:ACCEL-BRIDGE:v0100]\nimport VIA_SuperAccel_Module\n")
        W("A_v0101.py", blk + "X = 1\n")
        W("B_v0100.py", "X = 1\n")
        W("C_v0100.py", "# [VIA:ACCEL-BRIDGE:v0100]\nimport VIA_SuperAccel_Module\n")
        W("D_v0100.py", "# [VIA:ACCEL-BRIDGE:v0100]\nimport VIA_SuperAccel_Module\n")
        W("E_v0100.py", "# [VIA:ACCEL-BRIDGE:v0110] VeritasCeleritas_v1141\ndef x(:\n")
        W("F_v0100.py", "# [VIA:ACCEL-BRIDGE:v0110]\nimport VeritasCeleritas_v1141\n")
        chain = {127: "def foo(a, b):\n    return a\n\n\ndef hot():\n    return 0\n", 128: "if False:\n    setattr(m, 'hot', 1)\n", 129: "if False:\n    setattr(m, 'hot', 1)\n",
                 130: "if False:\n    setattr(m, 'hot', 1)\n    setattr(m, 'foo', 2)\n"}
        for v, s in chain.items():
            W("%s_v%04d.py" % (_STEM, v), blk + s + "import sys\nif '--selftest' in sys.argv:\n    print('  [FAIL] 舊問題 甲')\n")
        os.environ["VIA_VRN_HEALTH_OUT"] = str(td / "rep")
        o1 = selfgate_run("quick", vrn, vrn, panorama=True)
        cls = {x["file"]: x["cls"] for x in o1["sync"]}
        chk("② 加速器分類:B 缺標記 → OP-300 · C / D 舊橋 → OP-400(同型批次)· F 寫死 v1141(最新 v1142)→ OP-300 · A 尾版 v0111 綠 · 全部列「可同步修正」",
            cls.get("B_v0100.py") == "OP-300" and cls.get("C_v0100.py") == "OP-400" and cls.get("D_v0100.py") == "OP-400" and cls.get("F_v0100.py") == "OP-300" and "A_v0101.py" not in cls)
        chk("③ 靜態不執行:E 語法錯(既有)→ 不可同步 OP-500 · 九頭龍 hot 3 頭 = 熱點(不可同步)· 首輪基準 → 不紅(%s)" % o1["verdict"],
            "E_v0100.py" in o1["bad_old"] and ("hot", 3) in o1["hot"] and o1["verdict"] != "RED" and any("九頭龍熱點 hot" in x["what"] for x in o1["nonsync"]))
        o2 = selfgate_run("quick", vrn, vrn)
        chk("④ 同輸入不重跑:指紋沒變 → 沿用上次判定(cached)", o2.get("cached") is True)
        W("%s_v0131.py" % _STEM, blk + "if False:\n    setattr(m, 'hot', 1)\n    setattr(m, 'ghost', 3)\n")
        W("B_v0100.py", "X = 2  # 偷改既有檔\n")
        o3 = selfgate_run("quick", vrn, vrn)
        chk("⑤ 擋下:熱點 hot 3 → 4 頭(九頭龍)· 既有檔 B_v0100.py 被改(違反只增不減)· 錨點 ghost 沒找到 → RED",
            o3["verdict"] == "RED" and any("hot 從 3 頭變 4 頭" in x for x in o3["red"]) and any("B_v0100.py" in x for x in o3["red"]) and any("ghost" in x for x in o3["red"]))
        (vrn / ("%s_v0131.py" % _STEM)).unlink()
        W("B_v0100.py", "X = 1\n")
        a = anchors(vrn, vrn / ("%s_v0130.py" % _STEM))
        chk("⑥ AST 錨點:foo 精準 = %s · 彈性 = %s" % (a[1]["precise"] if len(a) > 1 else "—", a[1]["elastic"] if len(a) > 1 else "—"),
            len(a) == 2 and a[1]["target"] == "foo" and a[1]["precise"].startswith("%s_v0127.py:" % _STEM) and a[1]["elastic"] == "foo(a, b)")
        real = vrn
        sb = td / "sandbox"
        shutil.copytree(real, sb)
        (sb / ("%s_v0132.py" % _STEM)).write_text(blk + "import sys\nif '--selftest' in sys.argv:\n    print('  [FAIL] 舊問題 甲')\n    print('  [FAIL] 新問題 乙')\n", encoding="utf-8")
        os.environ["VIA_VRN_GATE_SELFTEST_SEC"] = "60"
        s1 = selfgate_run("sandbox", sb, real)
        chk("⑦ 在地測試:新尾版多出失敗「新問題 乙」→ RED(啟動器據此不落地)· 舊問題 甲 不算新", s1["verdict"] == "RED" and s1["sandbox"]["added"] == ["新問題 乙"] and s1["staged"] == ["%s_v0132.py" % _STEM])
        (sb / ("%s_v0132.py" % _STEM)).write_text(blk + "import sys\nif '--selftest' in sys.argv:\n    print('  [FAIL] 舊問題 甲')\n", encoding="utf-8")
        s2 = selfgate_run("sandbox", sb, real)
        chk("⑧ 在地測試:新尾版沒多出失敗 → 可落地(%s · 新增失敗 0)" % s2["verdict"], s2["verdict"] != "RED" and s2["sandbox"].get("added") == [])
        (sb / ("%s_v0132.py" % _STEM)).write_text("def broken(:\n", encoding="utf-8")
        s3 = selfgate_run("sandbox", sb, real)
        chk("⑨ 在地測試:新檔語法錯 / 沒帶加速器 → RED", s3["verdict"] == "RED" and any("語法錯" in x for x in s3["red"]) and any("加速器不合格" in x for x in s3["red"]))
        fk = td / "fake_th.py"
        fk.write_text("import time\ndef nonocr_tables(pdf, page, bbox=None, backend='x'):\n    time.sleep(30)\n    return {'status': 'ok', 'tables': []}\n", encoding="utf-8")
        t0 = time.time()
        r = guarded_tables(str(fk), lambda *a: {"status": "ok", "fast": True}, "x.pdf", 1, None, "camelot_stream", timeout=3)
        el = time.time() - t0
        rf = guarded_tables(str(fk), lambda *a: {"status": "ok", "fast": True}, "x.pdf", 1, None, "pymupdf_lines", timeout=3)
        chk("⑩ 重型讀表器卡住 → %.1f 秒收掉(逾時 = 失敗)· 快速讀表器照原路" % el, r["status"] == "error" and "逾時" in r["why"] and el < 12 and rf.get("fast"))
        rx = vars(_m166)["_RX"] if _m166 is not None else None
        mm = rx.match("  [進度] 3/60 · 實測 · — · 沒過 P5·F·01·T1") if rx else None
        chk("⑪ 讀表實測有進度(「實測」段 95→99%)· v0174 auto 的實測換成有進度 + 受保護版", bool(mm) and mm.group(3) == "實測" and getattr(_resolve("auto_bench"), "_v175", False))
        rv = td / "rep2" / "review" / "ps_20261011_010355"
        rv.mkdir(parents=True)
        (rv / "B.progress").write_text("95 · 2120s · 還原 57/57 · YELLOW · x.pdf", encoding="utf-8")
        tr = triage_last_run(td / "rep2" / "vrn")
        chk("⑫ 上一輪分診:沒有 paste.md / python 記錄 → 中斷(不可同步 · 沿用輸出 --resume)", tr["state"] == "中斷" and "resume" in tr["fix"])
        pmx = panorama_monitor(vrn, td / "pan")
        chk("⑬ VCGC 全景監控:本機沒有引擎 → ABSENT(不崩 · 不連結)", pmx["state"] == "ABSENT")
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(td, ignore_errors=True)
    me = Path(__file__).read_text(encoding="utf-8")
    chk("⑭ 本檔帶最新有版號加速器橋 [VIA:ACCEL-BRIDGE:v0111] · 自帶多程序墊片", "[VIA:ACCEL-BRIDGE:v0111]" in me and _job_entry.__module__ in ("__main__", __name__))
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("⑮ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    print("[計] VRN_SystemManager_v0175 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
