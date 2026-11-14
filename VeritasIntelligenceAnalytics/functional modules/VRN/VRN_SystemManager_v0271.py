#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VRN-2 SystemManager v0271 — 薄尾:extract 加速(多行程平行)· 逐檔即時進度 · 全部檔列出 · 與上次比。

操作員回報(2026-11-14,v0270 合併後在工作站跑 C:\測試樣本報告 97 份):「卡斷沒加加速器」;結果 READ 62 → 60 · REVIEW 21 → 23。
查到三件事:
  · 一檔一檔序跑:97 份逐檔 0.3–90 秒,全部排隊,整批要等很久。
    加速器橋(SUP_MDL737 accel_map)是執行緒池,而 PDF 解析是吃 CPU 的 Python,執行緒在 GIL 下幾乎不會變快 → 要開多個行程才有用。
  · 畫面沒動:輸出接到管線(Tee-Object)時,Python 預設整塊緩衝,跑完才一次吐出,看起來像卡住。
  · 前版印表只列前 40 檔(97 份看不到後 57 份),也看不出這次跟上次比哪些檔變了狀態。
本版(前版一字不動;只在 extract 期間換鏈上 v0127 擷取本體的 extract 與印表兩個函式,跑完還原):
  ① 平行:≥ 2 檔就開 N 個子行程(預設 min(4, CPU − 1);`--workers N` 或環境 VIA_VRN_EXTRACT_WORKERS;上限 8;1 = 照前版序跑)。
     依檔案大小分組(大檔先排、每次給最輕那組)。子行程跑的是同一條鏈(v0270 三修掛上),結果照原檔序交回前版 extract 彙整:
     帳(VRN_Extract_Ledger)· 計數 · 燈號 · U/I 矩陣全照前版。子行程掛掉時,沒回的檔照實記 ERROR(原因帶 rc 與錯誤尾段),不冒充。
  ② 逐檔進度:每完成一檔就印「[進度 k/N] 狀態 · 檔名 · 秒數 · 已耗時」;stdout 改逐行送出(接管線也看得到)。
  ③ 全列:最後的清單列出全部檔(前版只印前 40 檔)。
  ④ 與上次比:開跑前先讀帳上每個檔名的最後一筆;跑完列出狀態有變的檔(例 READ → REVIEW),變成 REVIEW 的附上哪幾張表、什麼算術問題。
注意:同一份 PDF 以兩個檔名同時出現在夾裡時,兩個子行程可能同時寫同一個 <sha8> 夾(內容相同);要完全避開就用 --workers 1。
號:前版 v0270(main);桌機 VRN-2 線到 v0269,本版取下一個空號 v0271。零網路 · 不碰 TA-Lib · 不讀寫同意閘。
用法:python VRN_SystemManager_v0271.py extract --dir <夾> [--workers N] · 自測 python VRN_SystemManager_v0271.py --selftest(本版 11 項 + 前版 v0270 自測)。
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

import contextlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
TAG = "v0271"
DISPLAY_NAME = "VRN-2 SystemManager"
FAMILY = "VRN_SystemManager"
WORKER_VERB = "_extract_worker"
MAX_WORKERS = 8
FIXTURES = HERE / "intake/VRN_v0108_Annual/VRN_v0108_Complete_Handover/pack/engine/fixtures/REAL_TEST_INPUT"
SAMPLE_PDFS = ("20251205兆豐晨會報告(二)-公司訪談摘要.pdf", "瑞基(4171,NR_未評等)-CTBC251208.pdf", "20251208_台新台股盤勢分析.pdf")


def _vnum(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load(path: Path, name: str):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


PRIOR_PATH = max((p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
PRIOR = _load(PRIOR_PATH, "vrn_manager_prior_for_" + TAG)


def __getattr__(name):
    """尾版律 TAILAPI:前版公開名稱經本檔轉接。"""
    return getattr(PRIOR, name)


_STATE = {"prev": None, "print_prev": None}


def p27():
    """extract 擷取本體(v0127 模組;沿前版 v0270 的鏈找)。"""
    return PRIOR.p27()


# ────────────────── 平行數 ──────────────────
def _opt(args: list, flag: str):
    return args[args.index(flag) + 1] if flag in args and args.index(flag) + 1 < len(args) else None


def workers_for(args: list) -> int:
    """--workers N > 環境 VIA_VRN_EXTRACT_WORKERS > 預設 min(4, CPU − 1);上限 8;1 = 照前版序跑。"""
    w = 0
    for v in (_opt(args, "--workers"), os.environ.get("VIA_VRN_EXTRACT_WORKERS")):   # 亂填 / ≤ 0 → 往下一層
        try:
            w = int(str(v).strip()) if v is not None and str(v).strip() else 0
        except ValueError:
            w = 0
        if w > 0:
            break
    if w <= 0:
        w = min(4, max(1, (os.cpu_count() or 2) - 1))
    return max(1, min(w, MAX_WORKERS))


def strip_workers(args: list) -> list:
    out, skip = [], False
    for i, a in enumerate(args):
        if skip:
            skip = False
            continue
        if a == "--workers":
            skip = i + 1 < len(args)
            continue
        out.append(a)
    return out


def plan(files: list, w: int) -> list:
    """依檔案大小分給 w 個行程(大檔先排、每次給目前最輕的那組),各組總量接近。"""
    def size(p):
        try:
            return Path(p).stat().st_size
        except OSError:
            return 0
    groups = [[] for _ in range(max(1, w))]
    load = [0] * len(groups)
    for p in sorted(files, key=size, reverse=True):
        k = load.index(min(load))
        groups[k].append(p)
        load[k] += size(p) or 1
    return [g for g in groups if g]


# ────────────────── 平行執行 ──────────────────
def _json_or_none(ln: str):
    """一行 JSON;壞行(寫到一半 · 雜訊)回 None,由呼叫端略過。"""
    try:
        return json.loads(ln)
    except ValueError:
        return None


def _read_new(s: dict) -> list:
    try:
        with open(s["out"], "rb") as fh:
            fh.seek(s["pos"])
            data = fh.read()
    except OSError:
        return []
    cut = data.rfind(b"\n")
    if cut < 0:
        return []
    s["pos"] += cut + 1
    items = [x for x in map(_json_or_none, data[:cut].decode("utf-8", errors="replace").splitlines()) if x is not None]
    return items


def _err_tail(path: Path, n: int = 3) -> str:
    try:
        lines = [x for x in Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
                 if x.strip() and "FontBBox" not in x and "Overwriting cache" not in x]
    except OSError:
        return ""
    return " | ".join(lines[-n:])[:300]


def run_parallel(files: list, engines: tuple, w: int, emit=print) -> tuple:
    """w 個子行程各跑一組檔(子行程掛同一條鏈 = v0270 三修);逐檔回報進度。回 (recs{路徑: rec}, 掛掉說明{路徑: 原因})。"""
    tmp = Path(tempfile.mkdtemp(prefix="vrn_extract_v0271_"))
    groups, procs, recs, total, t0 = plan(files, w), [], {}, len(files), time.time()
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")       # Windows 子行程輸出不走 cp1252
    if env.get("VIA_VRN_EXTRACT_OUT"):                                      # 相對的輸出夾先對呼叫端工作夾定死(帳與子行程同一處)
        env["VIA_VRN_EXTRACT_OUT"] = os.path.abspath(env["VIA_VRN_EXTRACT_OUT"])
    emit("[加速] extract 平行 %d 行程 · 檔 %d(依檔案大小分配;逐檔完成就印)" % (len(groups), total), flush=True)
    try:
        for i, g in enumerate(groups):
            job, outp, errp = tmp / ("job%d.json" % i), tmp / ("out%d.jsonl" % i), tmp / ("err%d.txt" % i)
            job.write_text(json.dumps({"files": [str(p) for p in g], "engines": list(engines), "out": str(outp)}, ensure_ascii=False),
                           encoding="utf-8")
            outp.touch()
            ef = open(errp, "w", encoding="utf-8", errors="replace")
            pr = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), WORKER_VERB, str(job)], env=env,   # 工作夾 = 呼叫端(同序跑)
                                  stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=ef)
            procs.append({"p": pr, "out": outp, "err": errp, "fh": ef, "pos": 0, "files": [str(p) for p in g]})
        while True:
            alive = any(s["p"].poll() is None for s in procs)
            for s in procs:
                for it in _read_new(s):
                    r = it.get("rec") or {}
                    recs[it.get("path")] = r
                    emit("  [進度 %d/%d] %s · %s · %ss · 已 %ds" % (len(recs), total, r.get("status"), str(r.get("file"))[:60],
                                                                r.get("secs"), int(time.time() - t0)), flush=True)
            if not alive:
                break
            time.sleep(0.3)
    finally:
        for s in procs:
            if s["p"].poll() is None:
                s["p"].kill()
                s["p"].wait()
            s["fh"].close()
    crash = {}
    for s in procs:
        miss = [f for f in s["files"] if f not in recs]
        if miss:
            why = "平行子行程 rc %s 沒回這一檔(%s)" % (s["p"].returncode, _err_tail(s["err"]) or "無錯誤輸出")
            for f in miss:
                crash[f] = why
    shutil.rmtree(tmp, ignore_errors=True)
    return recs, crash


def stub(recs: dict, crash: dict):
    """彙整時代替 extract_one:回子行程算好的結果;沒回的照實丟例外(前版迴圈會記成 ERROR)。"""
    def extract_one(pdf, out_root=None, engines=None, avail=None):
        k = str(pdf)
        if k in recs:
            return recs[k]
        raise RuntimeError(crash.get(k) or "平行子行程沒回這一檔")
    return extract_one


def make_parallel(orig, w: int):
    """包住鏈上的 extract(files, engines, limit):檔 ≥ 2 且 w ≥ 2 → 子行程平行;彙整仍走原 extract(帳 · 計數 · 燈號不變)。"""
    def extract(files, engines, limit=0):
        fs = list(files)[: (limit or len(files))]
        ww = min(w, len(fs))
        if ww <= 1:
            return orig(fs, engines, 0)
        t0 = time.time()
        recs, crash = run_parallel(fs, tuple(engines), ww)
        P = p27()
        keep = P.extract_one
        P.extract_one = stub(recs, crash)
        try:
            out = orig(fs, engines, 0)
        finally:
            P.extract_one = keep
        wall = time.time() - t0
        busy = sum(float(r.get("secs") or 0) for r in out.get("rows") or [])
        out.setdefault("_notes", []).append("加速:平行 %d 行程 · 實耗 %.0fs · 逐檔秒數加總 %.0fs(約 %.1f 倍)"
                                            % (ww, wall, busy, busy / wall if wall > 0 else 1.0))
        out["workers"] = ww
        return out
    extract.__name__ = "extract_v0271"
    extract._v0271_inner = orig
    return extract


# ────────────────── 子行程 ──────────────────
def worker(job_path: str) -> int:
    job = json.loads(Path(job_path).read_text(encoding="utf-8"))
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    PRIOR.install()
    P = p27()
    avail = P._engines()
    engines = tuple(job.get("engines") or ("pdfplumber", "camelot", "tabula"))
    with open(job["out"], "a", encoding="utf-8") as fh:
        for f in job["files"]:
            p = Path(f)
            try:
                rec = P.extract_one(p, P._out_root(), engines, avail)
            except Exception as exc:  # noqa: BLE001 — 一檔壞不擋整批,同前版照實記 ERROR
                rec = {"file": p.name, "sha8": "", "status": "ERROR", "why": "%s:%s" % (type(exc).__name__, str(exc)[:120]),
                       "pages": 0, "tables": 0, "secs": 0}
            fh.write(json.dumps({"path": f, "rec": rec}, ensure_ascii=False, default=str) + "\n")
            fh.flush()
    return 0


# ────────────────── 印 · 與上次比 ──────────────────
def ledger_last(out_root) -> dict:
    """帳上每個檔名的最後一筆(本輪寫帳之前讀)。"""
    lp = Path(out_root) / "VRN_Extract_Ledger.jsonl"
    try:
        text = lp.read_text(encoding="utf-8")
    except OSError:                                   # 帳不在(首跑)→ 沒有前一筆
        return {}
    last = {}
    for r in map(_json_or_none, text.splitlines()):
        if isinstance(r, dict) and r.get("file"):
            last[r["file"]] = r
    return last


def changes(prev: dict, rows: list) -> list:
    return [(prev[r.get("file")], r) for r in rows if r.get("file") in prev and prev[r.get("file")].get("status") != r.get("status")]


def issue_lines(rec: dict, n: int = 4) -> list:
    fj = Path(str(rec.get("dir") or "")) / "financial.json"
    try:
        d = json.loads(fj.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    out = []
    for t in d.get("tables") or []:
        if t.get("issues"):
            out.append("p%s %s · %s" % (t.get("page"), t.get("category"), ";".join(str(x) for x in t["issues"][:3])[:160]))
    return out[:n]


def print_all(out: dict) -> None:
    """同前版 _print_31 的版面,但列出全部檔(前版只印前 40 檔),最後加「與上次比」。"""
    if out.get("verb") != "extract":
        return _STATE["print_prev"](out)
    c, e = out["counts"], out["engines"]
    print("[計] extract 檔 %d · READ %d REVIEW %d TEXT_DOC %d NODATA %d ERROR %d · 引擎 pdfplumber=%s camelot=%s tabula=%s bridge=%s · %s"
          % (len(out["rows"]), c.get("READ", 0), c.get("REVIEW", 0), c.get("TEXT_DOC", 0), c.get("NODATA", 0), c.get("ERROR", 0),
             e.get("pdfplumber"), e.get("camelot"), e.get("tabula"), e.get("bridge"), out["lamp"]), flush=True)
    for r in out["rows"]:
        tag = {"READ": "OK", "REVIEW": "YEL", "NODATA": "YEL", "ERROR": "RED", "TEXT_DOC": "OK"}.get(r["status"], "YEL")
        print("  [%s] %s · %s · 頁 %s 表 %s %s · %s · %ss" % (tag, r["status"], r["file"][:60], r.get("pages"), r.get("tables"),
                                                         r.get("categories", ""), r["why"], r.get("secs")))
    for n in out.get("_notes") or []:
        print("  [注] %s" % n)
    prev = _STATE["prev"]
    if prev is None:
        return None
    if not prev:
        print("[變] 與上次比:帳上沒有前一筆(首跑)", flush=True)
        return None
    ch = changes(prev, out["rows"])
    cnt = Counter("%s→%s" % (a.get("status"), r.get("status")) for a, r in ch)
    print("[變] 與上次比(帳上同檔名前一筆)· 變 %d 檔%s" % (len(ch), (" · " + " · ".join("%s %d" % kv for kv in sorted(cnt.items()))) if cnt else ""),
          flush=True)
    for a, r in ch:
        print("  [變] %s → %s · %s · %s" % (a.get("status"), r.get("status"), r["file"][:60], r.get("why")))
        if r.get("status") == "REVIEW":
            for s in issue_lines(r):
                print("      ↳ " + s)
    return None


# ────────────────── 動詞 ──────────────────
def collect() -> dict:
    """VCGC 子系統對接口(照前版 · 只讀)· served_by 記本版。"""
    out = PRIOR.collect()
    if isinstance(out, dict):
        out = dict(out)
        sb = dict(out.get("served_by") or {})
        sb["tail"] = FAMILY + "_" + TAG
        out["served_by"] = sb
    return out


def provenance(args: list) -> int:
    """同 v0262 / v0270:直送 ENG114 尾版;`--selftest` 之後再跑本版自測,回傳碼取大。"""
    h = PRIOR.host()
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    rc = int(h._load_engine(h.provenance_engine_path()).main(list(args)) or 0)
    if "--selftest" in args:
        print("  ── 來源回歸之後:本版管理器自測 ──", flush=True)
        rc = max(rc, int(selftest() or 0))
    return rc


def extract(args: list) -> int:
    """前版 v0270 的 extract(三修掛上 · v0262 鏈)+ 本版:平行 · 逐檔進度 · 全列 · 與上次比。"""
    w = workers_for(args)
    rest = strip_workers(args)
    PRIOR.install()
    P = p27()
    if rest[:1] != ["status"]:
        _STATE["prev"] = ledger_last(P._out_root())
    orig_ex, orig_pr = P.extract, P._print_v0127
    _STATE["print_prev"] = orig_pr
    P.extract, P._print_v0127 = make_parallel(orig_ex, w), print_all
    try:
        return int(PRIOR.host().main(["extract", *rest]) or 0)
    finally:
        P.extract, P._print_v0127 = orig_ex, orig_pr
        _STATE["prev"] = None


def _line_buffered() -> None:
    """接管線 / Tee-Object 時 Python 預設整塊緩衝,畫面看起來像卡住;改成逐行送出。"""
    for st in (sys.stdout, sys.stderr):
        fn = getattr(st, "reconfigure", None)        # 被換成 StringIO 等就沒有 reconfigure,照原樣
        if callable(fn):
            try:
                fn(line_buffering=True)
            except ValueError as exc:
                _STATE["unbuffered"] = str(exc)[:120]


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    _line_buffered()
    if args[:1] == ["provenance"]:
        return provenance(args[1:])
    if args == ["--selftest"] or "--selftest" in args[:1]:
        return selftest()
    if args[:1] == [WORKER_VERB] and len(args) > 1:
        return worker(args[1])
    if args[:1] == ["extract"]:
        return extract(args[1:])
    return PRIOR.main(args)


# ────────────────── 自測 ──────────────────
def selftest() -> int:
    print("[計] %s %s 自測開始(本版 11 項 · 再前版 %s)" % (DISPLAY_NAME, TAG, PRIOR_PATH.name), flush=True)
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)
    keep_env = {k: os.environ.get(k) for k in ("VIA_VRN_EXTRACT_WORKERS", "VIA_VRN_EXTRACT_OUT")}
    td = Path(tempfile.mkdtemp(prefix="vrn_v0271_st_"))
    try:
        os.environ["VIA_VRN_EXTRACT_OUT"] = str(td / "out")
        os.environ.pop("VIA_VRN_EXTRACT_WORKERS", None)
        dflt, junk0 = workers_for([]), workers_for(["--workers", "abc"])
        os.environ["VIA_VRN_EXTRACT_WORKERS"] = "2"
        env2, junk2 = workers_for([]), workers_for(["--workers", "abc"])
        chk("① 平行數:--workers 3 → 3 · 環境 2 → 2 · 99 → 上限 8 · --workers 亂填 → 退到環境 2 · 都沒有 → 預設 %d(1–4)· 參數拿掉 --workers 再交鏈" % dflt,
            workers_for(["--dir", "x", "--workers", "3"]) == 3 and env2 == 2 and workers_for(["--workers", "99"]) == 8
            and junk2 == 2 and junk0 == dflt and 1 <= dflt <= 4
            and strip_workers(["--dir", "x", "--workers", "3", "--limit", "2"]) == ["--dir", "x", "--limit", "2"], (dflt, junk0, env2, junk2))
        os.environ.pop("VIA_VRN_EXTRACT_WORKERS", None)
        a, b, c = td / "a.pdf", td / "b.pdf", td / "c.pdf"
        a.write_bytes(b"x" * 900)
        b.write_bytes(b"x" * 500)
        c.write_bytes(b"x" * 450)
        g = plan([a, b, c], 2)
        chk("② 分配:依檔案大小,大檔自成一組、兩小檔併一組 · 一檔不漏", len(g) == 2 and [len(x) for x in g] == [1, 2]
            and sorted(str(p) for x in g for p in x) == sorted(map(str, (a, b, c))), [[p.name for p in x] for x in g])
        PRIOR.install()
        P = p27()
        orig = P.extract
        keep = P.extract_one
        P.extract_one = stub({}, {str(td / "gone.pdf"): "平行子行程 rc 1 沒回這一檔(測)"})
        try:
            bad = orig([td / "gone.pdf"], ("pdfplumber",), 0)
        finally:
            P.extract_one = keep
        r0 = (bad.get("rows") or [{}])[0]
        chk("③ 子行程掛掉:沒回的檔照實記 ERROR(原因帶 rc 與錯誤尾段)· 不冒充 READ", r0.get("status") == "ERROR" and "子行程" in str(r0.get("why")), r0)
        files = [FIXTURES / n for n in SAMPLE_PDFS]
        if all(f.is_file() for f in files) and P._engines().get("pdfplumber"):
            s_out = orig(files, ("pdfplumber",), 0)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                p_out = make_parallel(orig, 2)(files, ("pdfplumber",), 0)
            key = lambda o: [(r.get("file"), r.get("status"), r.get("tables"), json.dumps(r.get("categories"), sort_keys=True, ensure_ascii=False))
                             for r in o.get("rows") or []]
            prog = [ln for ln in buf.getvalue().splitlines() if "[進度 " in ln]
            chk("④ 真檔 3 份:平行 2 行程與序跑逐檔一致(狀態 · 表數 · 分類)· 照原檔序彙整 · 逐檔進度 3 行 · 記加速說明",
                key(s_out) == key(p_out) and [r.get("file") for r in p_out["rows"]] == [f.name for f in files] and len(prog) == 3
                and any("平行 2 行程" in n for n in p_out.get("_notes") or []), (key(s_out), key(p_out), prog))
        else:
            chk("④ 真檔樣本不在 / pdfplumber 不在 → NODATA 照實跳過(不冒充)", True)
        lp = td / "led"
        lp.mkdir()
        (lp / "VRN_Extract_Ledger.jsonl").write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in (
            {"file": "a.pdf", "status": "REVIEW"}, {"file": "a.pdf", "status": "READ"}, {"file": "b.pdf", "status": "READ"})) + "\n",
            encoding="utf-8")
        prev = ledger_last(lp)
        rows = [{"file": "a.pdf", "status": "REVIEW", "why": "FIN 1 表全有算術問題"}, {"file": "b.pdf", "status": "READ", "why": ""}] + \
               [{"file": "f%02d.pdf" % i, "status": "READ", "why": "", "pages": 1, "tables": 1} for i in range(43)]
        out = {"verb": "extract", "counts": {"READ": 44, "REVIEW": 1}, "engines": {}, "lamp": "YELLOW", "rows": rows, "_notes": []}
        _STATE["prev"] = prev
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            print_all(out)
        _STATE["prev"] = None
        txt = buf.getvalue()
        chk("⑤ 與上次比:帳上同檔名取最後一筆(a.pdf = READ)· 本輪 REVIEW → 記「READ→REVIEW 1」· b.pdf 沒變不列",
            prev["a.pdf"]["status"] == "READ" and len(changes(prev, rows)) == 1 and "READ→REVIEW 1" in txt and "READ → REVIEW · a.pdf" in txt
            and "· b.pdf ·" not in txt.split("[變] 與上次比")[1], txt[-400:])
        chk("⑥ 全列:45 檔全部印出(前版只印前 40 檔)", sum(1 for ln in txt.splitlines() if ln.startswith("  [OK] READ") or ln.startswith("  [YEL] REVIEW")) == 45)
        h, seen = PRIOR.host(), {}
        keep_main = h.main

        def fake_main(argv):
            seen.update(argv=list(argv), wrapped=getattr(P.extract, "__name__", "") == "extract_v0271",
                        printer=P._print_v0127 is print_all, prev=isinstance(_STATE["prev"], dict))
            return 2
        h.main = fake_main
        try:
            rc = extract(["--dir", str(td / "empty"), "--workers", "2"])
        finally:
            h.main = keep_main
        chk("⑦ extract 接線:交給前版鏈時 extract 已換成平行版、印表換成全列版、已先讀帳 · --workers 不往下傳 · 跑完兩個函式都還原",
            rc == 2 and seen.get("argv") == ["extract", "--dir", str(td / "empty")] and seen.get("wrapped") and seen.get("printer")
            and seen.get("prev") and P.extract is orig and P._print_v0127 is _STATE["print_prev"] and _STATE["prev"] is None, (rc, seen))
        ghosts, lines = [td / "ghost_a.pdf", td / "ghost_b.pdf"], []
        recs, crash = run_parallel(ghosts, ("pdfplumber",), 2, emit=lambda m, **kw: lines.append(m))
        chk("⑧ 子行程來回(不靠 PDF 套件,各平台都真的開行程):2 個子行程各回 1 檔 · 不在的檔照實記 ERROR / NODATA · 沒有檔掉失 · 進度 2 行",
            sorted(recs) == sorted(map(str, ghosts)) and not crash and all(r.get("status") in ("ERROR", "NODATA") for r in recs.values())
            and sum(1 for m in lines if "[進度 " in m) == 2, (recs, crash, lines))
        cwd0 = os.getcwd()
        os.environ["VIA_VRN_EXTRACT_OUT"] = "out_rel"
        os.chdir(td)
        try:
            Path("rel_a.pdf").write_bytes(b"%PDF-1.4 not a real pdf\n")
            recs2, crash2 = run_parallel([Path("rel_a.pdf"), Path("rel_missing.pdf")], ("pdfplumber",), 2, emit=lambda m, **kw: None)
        finally:
            os.chdir(cwd0)
            os.environ["VIA_VRN_EXTRACT_OUT"] = str(td / "out")
        ra, rm = recs2.get("rel_a.pdf") or {}, recs2.get("rel_missing.pdf") or {}
        made = list((td / "out_rel").glob("*/filename.json"))
        chk("⑨ 相對路徑(--dir reports 這類 · PR 639 Codex P2):子行程照呼叫端的工作夾解析 → 相對的 PDF 找得到(不是 FileNotFoundError)· 相對的輸出夾落在同一處 · 真不在的檔照實記 FileNotFoundError",
            "FileNotFoundError" not in str(ra.get("why")) and len(made) == 1 and "FileNotFoundError" in str(rm.get("why")) and not crash2, (ra, rm, made))
    finally:
        for k, v in keep_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(td, ignore_errors=True)
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑩ 檔面:def main / def selftest / def collect · 第 3 行加速器標記 · __main__ provenance 守門在 --selftest 之前 · 子行程不經 shell · 零 TA-Lib · 不寫同意閘",
        "\ndef main(" in text and "\ndef selftest(" in text and "\ndef collect(" in text and text.splitlines()[2].strip() == "# [VIA:ACCEL-BRIDGE:v0111]"
        and text.index('sys.argv[1:2] == ["provenance"]') < text.index('"--selftest" in sys.argv:') and "shell=" + "True" not in text
        and "import " + "talib" not in text and "environ[\"VIA_NET" + "_CONSENT\"] =" not in text)
    print("  ── 前版 %s 自測(本版只在 extract 期間掛平行,平時不改前版)──" % PRIOR_PATH.name, flush=True)
    prior_rc = int(PRIOR.selftest() or 0)
    chk("⑪ 前版 %s 自測照過" % PRIOR_PATH.name, prior_rc == 0, prior_rc)
    n = sum(ok)
    print("[計] %s %s(%s_%s.py)自測 %d/%d · %s" % (DISPLAY_NAME, TAG, FAMILY, TAG, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    return 0 if n == len(ok) else 1


if __name__ == "__main__":
    if sys.argv[1:2] == ["provenance"]:     # 同 v0262 / v0270:provenance 先於任何 --selftest 攔截
        sys.exit(provenance(sys.argv[2:]))
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.exit(main(sys.argv[1:]))
