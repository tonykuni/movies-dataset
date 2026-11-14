#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0176 — 薄尾(操作員 2026-10-11「從 140 為起點前進」「檔案過大且很多應該重複 · 各類整合為一 · 不衝突只增不減 · 善用 TEMP」
   「自動註冊編號版本號 · 由 VRN SYSTEM MANAGER 統一管理」「NON-OCR OCR 雙軌並進 · 兩條共近完美修復」)。
  ① 在地測試看得到:整條鏈自測每 15 秒印心跳 · 同一條鏈的自測結果進快取(舊尾版基準只跑一次)
  ② 自動註冊:VRN_Engine_Register 同一本冊(唯一寫入者)· 每族穩定編號 VRN-E-#### · 尾版號 · 版本清單 · sha · 加速器;快查時自動 · engines --register 也走這裡
  ③ dualtrack 動詞:每張財務 / 估值表 + 第一頁資訊區 NON-OCR 軌 與 OCR 軌並進(OCR 在 TEMP 子程序工人平行跑)→ 逐格 / 逐欄比對 → 三燈信心
     兩軌一致 = 綠(之後 NON-OCR 為主、OCR 只驗)· 部分一致 / 單軌 = 黃 · 衝突 / 兩軌都沒有 = 紅;OCR 結果進 TEMP 快取(同輸入不重跑;換輸入且上一輪全綠才清)
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

import datetime
import hashlib
import html
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0176"


def _vnum_v0176(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0176(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0176(p) < _vnum_v0176(__file__)), key=_vnum_v0176)
PRIOR = _load_v0176(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


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


_rep = _resolve("_rep")


# ───────── ① 在地測試:心跳 + 同鏈自測快取 ─────────
def _chain_key(tail: Path) -> str:
    h = hashlib.sha256()
    for p in sorted((q for q in tail.parent.glob(_STEM + "_v*.py") if _vnum_v0176(q) <= _vnum_v0176(tail)), key=_vnum_v0176):
        h.update(p.name.encode() + hashlib.sha256(p.read_bytes()).digest())
    intake = tail.parent / "intake"
    for p in sorted(intake.rglob("*.py")) if intake.is_dir() else []:
        h.update(str(p.relative_to(intake)).encode() + hashlib.sha256(p.read_bytes()).digest())
    return h.hexdigest()[:20]


def _selftest_cache_dir() -> Path:
    real = Path(os.environ.get("VIA_VRN_SANDBOX_OF") or HERE)
    rf = _resolve("_rep_for")
    return (rf(real) if rf else _rep()) / "selfgate" / "selftest_cache"


def chain_selftest_v176(tail: Path, timeout: int = 1800) -> dict:
    cd = _selftest_cache_dir()
    key = _chain_key(tail)
    cf = cd / (key + ".json")
    if cf.exists():
        try:
            d = json.loads(cf.read_text(encoding="utf-8"))
            print("  [進度] 在地測試 · 快取 · %s 同一條鏈已測過 → 沿用(FAIL %d)" % (tail.name, len(d["fails"])), flush=True)
            return {"fails": set(d["fails"]), "crash": "", "secs": 0, "cached": True}
        except (ValueError, KeyError, OSError):
            pass
    beat = float(os.environ.get("VIA_VRN_GATE_BEAT", "15") or 15)
    env = dict(os.environ)
    env.pop("VIA_SKIP_PRIOR_SELFTEST", None)
    t0 = time.time()
    flags = 0x00000200 if os.name == "nt" else 0
    out_f = tempfile.TemporaryFile(mode="w+", encoding="utf-8", errors="replace")
    p = subprocess.Popen([sys.executable, "-W", "ignore", str(tail), "--selftest"], stdout=out_f, stderr=subprocess.STDOUT, env=env, cwd=str(tail.parent), creationflags=flags)
    last = t0
    while p.poll() is None:
        time.sleep(0.2)
        if time.time() - last >= beat:
            last = time.time()
            print("  [進度] 在地測試 進行中 · %s · %d 秒" % (tail.name, int(last - t0)), flush=True)
        if time.time() - t0 > timeout:
            if os.name == "nt":
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True)
            else:
                p.kill()
            out_f.close()
            return {"fails": set(), "crash": "逾時 %d 秒" % timeout, "secs": int(time.time() - t0)}
    out_f.seek(0)
    txt = out_f.read()
    out_f.close()
    norm = lambda s: re.sub(r"\s+", " ", re.sub(r"\d+(\.\d+)?", "#", s)).strip()[:80]  # noqa: E731
    fails = {norm(l.split("[FAIL]", 1)[1]) for l in txt.splitlines() if "[FAIL]" in l and "前版鏈" not in l}
    crash = "Traceback" if re.search(r"^Traceback", txt, re.M) else ""
    res = {"fails": fails, "crash": crash, "secs": int(time.time() - t0), "rc": p.returncode}
    print("  [進度] 在地測試 · %s 完成 · FAIL %d · %d 秒" % (tail.name, len(fails), res["secs"]), flush=True)
    if not crash:
        try:
            cd.mkdir(parents=True, exist_ok=True)
            cf.write_text(json.dumps({"tail": tail.name, "fails": sorted(fails), "secs": res["secs"], "ts": datetime.datetime.now().isoformat(timespec="seconds")}, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass
    return res


_m175 = _owner("chain_selftest")
if _m175 is not None and not getattr(vars(_m175)["chain_selftest"], "_v176", False):
    chain_selftest_v176._v176 = True
    setattr(_m175, "chain_selftest", chain_selftest_v176)


# ───────── ② 自動註冊:同一本 VRN_Engine_Register · 唯一寫入者 · 穩定編號 ─────────
def register_v176(rows: list, home: Path = None) -> dict:
    home = home or (_resolve("_home") or (lambda: HERE))()
    rd = home / "registry"
    rd.mkdir(parents=True, exist_ok=True)
    hits = sorted(rd.glob("VRN_Engine_Register_v*.json"), key=_vnum_v0176)
    prev = {}
    if hits:
        try:
            prev = json.loads(hits[-1].read_text(encoding="utf-8")).get("engines") or {}
        except ValueError:
            prev = {}
    used = [int(re.search(r"(\d+)$", v.get("no", "")).group(1)) for v in prev.values() if isinstance(v, dict) and re.search(r"(\d+)$", v.get("no", "") or "")]
    nxt = max(used, default=0) + 1
    body = {}
    for r in sorted(rows, key=lambda r: (r.get("family", ""), r.get("ext", ""))):
        k = r.get("family", "") + r.get("ext", "")
        old = prev.get(k) if isinstance(prev.get(k), dict) else {}
        no = old.get("no")
        if not no:
            no = "VRN-E-%04d" % nxt
            nxt += 1
        tail = str(r.get("tail", ""))
        m = re.search(r"_v(\d{3,4})", Path(tail).stem)
        vl = list(dict.fromkeys(list(old.get("version_list") or []) + ([("v" + m.group(1).zfill(4))] if m else [])))
        body[k] = {"no": no, "tail": tail, "version": ("v" + m.group(1).zfill(4)) if m else "(無版號)", "version_list": vl, "sha8": r.get("sha8", ""), "versions": r.get("n", 0),
                   "accel": r.get("accel"), "pipeline": r.get("pipeline", ""), "status": "ACTIVE", "first_seen": old.get("first_seen") or datetime.date.today().isoformat()}
    for k, v in prev.items():
        if k not in body and isinstance(v, dict):
            body[k] = dict(v, status="ABSENT(樹上不見 · 只增不減保留)")
    if prev == body:
        return {"file": hits[-1].name + "(無變更)", "changed": False, "families": len(body), "new": 0}
    nv = "v%04d" % ((_vnum_v0176(hits[-1]) + 1) if hits else 100)
    fp = rd / ("VRN_Engine_Register_%s.json" % nv)
    fp.write_text(json.dumps({"schema": "VIA.VRN.EngineRegister.v2", "version": nv, "prior": hits[-1].name if hits else None, "ts": datetime.datetime.now().isoformat(timespec="seconds"),
                              "rule": "VRN SystemManager 自家引擎登記(唯一寫入者 · 穩定編號 VRN-E-#### 只增不減 · 內容變才出新版 · 編號只在冊裡不進原始碼)", "engines": body}, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"file": fp.name, "changed": True, "families": len(body), "new": sum(1 for k in body if k not in prev)}


def auto_register() -> dict:
    ea = _resolve("engines_audit")
    if ea is None:
        return {"file": "—", "why": "沒有引擎稽核"}
    try:
        o = ea(False)
    except TypeError:
        o = ea(register=False)
    return register_v176(o.get("rows") or [])



# ───────── ③ NON-OCR / OCR 雙軌並進 ─────────
_WORKER = r"""
import json, sys, time
from pathlib import Path
tasks = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
out = open(sys.argv[2], "a", encoding="utf-8")
try:
    import fitz
    import numpy as np
    from rapidocr_onnxruntime import RapidOCR
    eng = RapidOCR()
except Exception as exc:
    for t in tasks:
        out.write(json.dumps({"key": t["key"], "status": "missing", "why": "%s: %s" % (type(exc).__name__, str(exc)[:80])}) + "\n"); out.flush()
    sys.exit(0)
for t in tasks:
    t0 = time.time()
    try:
        with fitz.open(t["mini"]) as d:
            p = d[t["local"] - 1]
            r = fitz.Rect(*t["clip"]) & p.rect
            pix = p.get_pixmap(clip=r, dpi=t["dpi"], alpha=False)
            arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        res, _ = eng(arr)
        lines = []
        for box, text, conf in res or []:
            xs, ys = [q[0] for q in box], [q[1] for q in box]
            lines.append({"text": text, "bbox": [min(xs), min(ys), max(xs), max(ys)], "conf": round(float(conf), 3)})
        out.write(json.dumps({"key": t["key"], "status": "ok", "lines": lines, "ms": int((time.time() - t0) * 1000)}, ensure_ascii=False) + "\n")
    except Exception as exc:
        out.write(json.dumps({"key": t["key"], "status": "error", "why": "%s: %s" % (type(exc).__name__, str(exc)[:80]), "ms": int((time.time() - t0) * 1000)}) + "\n")
    out.flush()
"""


def dt_cache_dir() -> Path:
    base = Path(os.environ.get("VIA_TEMP_ROOT") or (Path(tempfile.gettempdir()) / "VIA_progress"))
    return base / "vrn_cache" / "dualtrack"


def _sha_file(p: str) -> str:
    try:
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]
    except OSError:
        return ""


def dt_units(d: Path, dpi: int = 200) -> list:
    units = []
    restore = {}
    rep = _rep()
    for f in (rep / "restore").glob("*.json") if (rep / "restore").is_dir() else []:
        if f.name.startswith("RESTORE_"):
            continue
        try:
            dj = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if dj.get("layout_run") != d.parent.name:
            continue
        for t in dj.get("tables", []):
            if t.get("block"):
                restore[(dj["document_meta"].get("file"), t["block"])] = t
    for p in sorted(d.glob("*.json")):
        try:
            j = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        row, info = j.get("row") or {}, j.get("info") or {}
        if not row.get("file"):
            continue
        mini = row.get("mini") or ""
        msha = _sha_file(mini) if mini and Path(mini).exists() else ""
        picked = list(row.get("picked") or [])
        for pi, pg in enumerate(j.get("pages", [])):
            orig = int(pg.get("page") or pi + 1)
            local = (picked.index(orig) + 1) if orig in picked else pi + 1
            roles = pg.get("roles") or {}
            for b in pg.get("blocks", []):
                if b.get("kind") == "table" and str(b.get("sub", "")).startswith(("財務表", "估值表")) and all(k in b for k in ("x0", "top", "x1", "bottom")):
                    rt = restore.get((row["file"], b.get("id")))
                    a_ok = bool((b.get("verify") or {}).get("ok")) or (rt or {}).get("status") == "還原無誤"
                    a_rows = (rt or {}).get("raw_rows") if rt and rt.get("status") == "還原無誤" else b.get("rows")
                    clip = [float(b["x0"]) - 4, max(0.0, float(b["top"]) - 42), float(b["x1"]) + 4, float(b["bottom"]) + 4]
                    units.append({"kind": "table", "file": row["file"], "code": row.get("code", ""), "id": b.get("id"), "page": orig, "local": local, "mini": mini, "msha": msha, "clip": clip,
                                  "a_rows": a_rows or [], "a_ok": a_ok, "a_method": (rt or {}).get("method") or b.get("engine", "")})
            if pi == 0:
                ib = [b for b in pg.get("blocks", []) if (b.get("role") or roles.get(b.get("zone"))) == "INFO" and all(k in b for k in ("x0", "top", "x1", "bottom"))]
                if ib:
                    clip = [min(b["x0"] for b in ib) - 6, max(0.0, min(b["top"] for b in ib) - 6), max(b["x1"] for b in ib) + 6, max(b["bottom"] for b in ib) + 6]
                    units.append({"kind": "info", "file": row["file"], "code": row.get("code", ""), "id": "P%d·INFO" % orig, "page": orig, "local": local, "mini": mini, "msha": msha, "clip": clip,
                                  "a_info": {"rating_raw": info.get("rating_raw"), "rating": info.get("rating"), "tp": info.get("tp"), "date": info.get("date_p1") or ""}, "fn_date": row.get("date", "")})
    for u in units:
        u["key"] = hashlib.sha1(("%s|%d|%s|%d|rapidocr" % (u["msha"], u["local"], ",".join("%.1f" % x for x in u["clip"]), dpi)).encode()).hexdigest()[:20] if u["msha"] else ""
    return units


def dt_run_ocr(tasks: list, workers: int, budget: int) -> dict:
    cd = dt_cache_dir()
    cd.mkdir(parents=True, exist_ok=True)
    run = Path(tempfile.mkdtemp(prefix="vrn_dt_", dir=str(cd.parent)))
    wk = run / "worker.py"
    wk.write_text(_WORKER, encoding="utf-8")
    chunks = [tasks[i::max(1, workers)] for i in range(max(1, workers))]
    procs = []
    flags = 0x00000200 if os.name == "nt" else 0
    for i, ch in enumerate(c for c in chunks if c):
        tf, of = run / ("t%d.json" % i), run / ("o%d.jsonl" % i)
        tf.write_text(json.dumps(ch, ensure_ascii=False), encoding="utf-8")
        procs.append((subprocess.Popen([sys.executable, "-W", "ignore", str(wk), str(tf), str(of)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=flags), of))
    t0, seen, killed = time.time(), 0, False
    while any(p.poll() is None for p, _ in procs):
        time.sleep(0.5)
        n = sum(sum(1 for _ in of.open(encoding="utf-8")) if of.exists() else 0 for _, of in procs)
        if n != seen:
            seen = n
            print("  [進度] %d/%d · OCR · — · 雙軌 OCR 軌(工人 %d)" % (n, len(tasks), len(procs)), flush=True)
        if time.time() - t0 > budget:
            for p, _ in procs:
                if p.poll() is None:
                    if os.name == "nt":
                        subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True)
                    else:
                        p.kill()
            killed = True
            break
    got = 0
    for _, of in procs:
        for ln in of.read_text(encoding="utf-8").splitlines() if of.exists() else []:
            try:
                r = json.loads(ln)
            except ValueError:
                continue
            (cd / (r["key"] + ".json")).write_text(json.dumps(r, ensure_ascii=False), encoding="utf-8")
            got += 1
    try:
        import shutil as _sh
        _sh.rmtree(run, ignore_errors=True)
    except Exception:  # noqa: BLE001
        pass
    return {"done": got, "secs": int(time.time() - t0), "killed": killed}


def _cells(rows: list, lex: list) -> list:
    """→ [(標準鍵, 正規化科目名, 期間, 值)];OCR 常吃掉空白(Net income → Netincome)→ 比對時標準鍵或正規化名任一相同就算同科目。"""
    rec = (_resolve("table_record"))(rows, 0, "x", "t", lex, True) if rows else {"rows": []}
    out = []
    for r in rec.get("rows") or []:
        norm = re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", str(r.get("label_raw") or "").lower())[:30]
        for c in r.get("cells") or []:
            if isinstance(c.get("value"), (int, float)):
                out.append((r.get("std") or "", norm, re.sub(r"\s+", "", str(c.get("period", ""))).upper(), float(c["value"])))
    return out


def _nums(rows: list) -> Counter:
    pn = _resolve("_to_num") or (lambda s: None)
    c = Counter()
    for r in rows or []:
        for x in r[1:] if r else []:
            for tok in str(x or "").split():
                v = pn(tok)
                if v is not None:
                    c[round(v, 2)] += 1
    return c


def dt_compare_table(a_rows: list, b_rows: list, lex: list) -> dict:
    eq = lambda x, y: abs(x - y) <= max(0.011, abs(x) * 0.005)  # noqa: E731
    A, B = _cells(a_rows, lex), _cells(b_rows, lex)
    if A and B:
        used, match, conf = set(), 0, []
        for (sa, na, pa, va) in A:
            hit = next((i for i, (sb, nb, pb, vb) in enumerate(B) if i not in used and pb == pa and ((sa and sa == sb) or (na and na == nb))), None)
            if hit is None:
                continue
            used.add(hit)
            if eq(va, B[hit][3]):
                match += 1
            else:
                conf.append(("%s·%s" % (sa or na, pa), va, B[hit][3]))
        return {"agree": round(match / max(len(A), len(B)), 3), "how": "逐格(科目 × 期間)", "cells": max(len(A), len(B)), "conflicts": conf[:5]}
    na, nb = _nums(a_rows), _nums(b_rows)
    if na and nb:
        inter = sum((na & nb).values())
        return {"agree": round(inter / max(sum(na.values()), sum(nb.values())), 3), "how": "數字集合", "cells": max(sum(na.values()), sum(nb.values())), "conflicts": []}
    return {"agree": None, "how": "—", "cells": 0, "conflicts": []}


def dt_compare_info(a: dict, text: str, fn_date: str) -> dict:
    rc = _resolve("_rating_code") or (lambda r, c: (None, ""))
    rft = _resolve("_rating_from_text") or (lambda t: "")
    tprx = _resolve("_TP_RX")
    iso = _resolve("_iso") or (lambda s: "")
    out = {}
    ar = rc(a.get("rating_raw"), a.get("rating"))[0]
    br_raw = rft(text or "")
    br = rc(br_raw, "")[0] if br_raw else None
    out["評等"] = ("一致" if ar is not None and ar == br else ("衝突" if ar is not None and br is not None else "單軌"), a.get("rating") or "—", br_raw or "—")
    m = tprx.search(text or "") if tprx else None
    btp = float(m.group(1).replace(",", "")) if m else None
    atp = a.get("tp")
    out["目標價"] = ("一致" if atp and btp and abs(atp - btp) <= abs(atp) * 0.005 else ("衝突" if atp and btp else "單軌"), atp if atp else "—", btp if btp else "—")
    bd = ""
    for mm in re.finditer(r"(?:20\d{2}[-/.年]\d{1,2}[-/.月]\d{1,2})|(?:(?:\d{1,2}\s+)?(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s+(?:\d{1,2},?\s+)?20\d{2})", text or "", re.I):
        bd = iso(mm.group(0))
        if bd:
            break
    ad = iso(a.get("date") or "") or iso(fn_date)
    out["報告日"] = ("一致" if ad and bd and ad == bd else ("衝突" if ad and bd else "單軌"), ad or "—", bd or "—")
    return out



def dualtrack_run(workers: int = 2, budget: int = 1200, dpi: int = 200) -> dict:
    d = _resolve("_latest_l2_dir")("")
    if not d:
        return {"err": "找不到上一輪 layout 的逐檔結果(先跑 -Verb layout)"}
    t0 = time.time()
    units = dt_units(d, dpi)
    cd = dt_cache_dir()
    cd.mkdir(parents=True, exist_ok=True)
    keys = sorted({u["key"] for u in units if u["key"]})
    cur_fp = hashlib.sha1("|".join(keys).encode()).hexdigest()[:16]
    idx_p = cd / "index.json"
    idx = {}
    if idx_p.exists():
        try:
            idx = json.loads(idx_p.read_text(encoding="utf-8"))
        except ValueError:
            idx = {}
    cleaned = 0
    if idx and idx.get("input_fp") != cur_fp and idx.get("all_green"):                # 上一輪全綠 + 這輪換了輸入 → 才清掉用不到的快取
        keep = set(keys)
        for f in cd.glob("*.json"):
            if f.name != "index.json" and f.stem not in keep:
                f.unlink()
                cleaned += 1
    hit = 0
    tasks = []
    pri = {}
    for u in units:
        if not u["key"]:
            continue
        pri[u["key"]] = 0 if (u["kind"] == "table" and not u.get("a_ok")) else (1 if u["kind"] == "info" else 2)
        if (cd / (u["key"] + ".json")).exists():
            hit += 1
        elif not any(t["key"] == u["key"] for t in tasks):
            tasks.append({"key": u["key"], "mini": u["mini"], "local": u["local"], "clip": u["clip"], "dpi": dpi})
    tasks.sort(key=lambda t: pri.get(t["key"], 3))
    oc = dt_run_ocr(tasks, workers, budget) if tasks else {"done": 0, "secs": 0, "killed": False}
    lex = (_resolve("_lex") or (lambda: []))()
    ocr_rows = _resolve("ocr_rows")
    recs = []
    for u in units:
        b = None
        if u["key"] and (cd / (u["key"] + ".json")).exists():
            try:
                b = json.loads((cd / (u["key"] + ".json")).read_text(encoding="utf-8"))
            except ValueError:
                b = None
        bst = (b or {}).get("status") or ("無來源(TEMP 已清)" if not u["key"] else "沒跑到(預算)")
        r = {"kind": u["kind"], "file": u["file"], "code": u["code"], "id": u["id"], "page": u["page"], "ocr": bst}
        if u["kind"] == "table":
            brows = ocr_rows(b["lines"]) if (b and b.get("status") == "ok" and ocr_rows) else []
            w = max((len(x) for x in brows), default=0)
            brows = [x + [""] * (w - len(x)) for x in brows]
            ast_ = "驗過" if u["a_ok"] else ("未過" if u["a_rows"] else "無")
            cmp = dt_compare_table(u["a_rows"], brows, lex) if (u["a_rows"] and brows) else {"agree": None, "how": "—", "cells": 0, "conflicts": []}
            ag = cmp["agree"]
            if u["a_ok"] and ag is not None and ag >= 0.98:
                lamp, path = "GREEN", "兩軌一致 → NON-OCR 主 · OCR 只驗"
            elif ag is not None and ag >= 0.98:
                lamp, path = "YELLOW", "兩軌數字一致 · NON-OCR 驗表沒過(可升級)"
            elif ag is not None and ag >= 0.8:
                lamp, path = "YELLOW", "部分一致 · 待修"
            elif ag is not None:
                lamp, path = "RED", "兩軌衝突 · 待查"
            elif u["a_ok"]:
                lamp, path = "YELLOW", "單軌 NON-OCR(OCR %s)" % bst
            elif brows:
                lamp, path = "YELLOW", "單軌 OCR 候選(NON-OCR 沒過)"
            else:
                lamp, path = "RED", "兩軌都沒有 · 待修"
            r.update(nonocr=ast_, method=u.get("a_method", ""), agree=ag, how=cmp["how"], cells=cmp["cells"], conflicts=cmp["conflicts"], lamp=lamp, path=path)
        else:
            text = " ".join(l["text"] for l in b["lines"]) if (b and b.get("status") == "ok") else ""
            f = dt_compare_info(u["a_info"], text, u.get("fn_date", "")) if text else {}
            st = [v[0] for v in f.values()]
            lamp = "GREEN" if st and all(s == "一致" for s in st) else ("RED" if "衝突" in st else "YELLOW")
            r.update(nonocr="資訊區", fields={k: list(v) for k, v in f.items()}, agree=round(sum(1 for s in st if s == "一致") / len(st), 3) if st else None,
                     lamp=lamp, path="兩軌一致 → NON-OCR 主" if lamp == "GREEN" else ("衝突 · 待查" if lamp == "RED" else "單軌 / 部分 · 待補"))
        recs.append(r)
    all_green = bool(recs) and all(x["lamp"] == "GREEN" for x in recs)
    idx_p.write_text(json.dumps({"input_fp": cur_fp, "keys": keys, "all_green": all_green, "ts": datetime.datetime.now().isoformat(timespec="seconds"), "layout_run": d.parent.name}, ensure_ascii=False), encoding="utf-8")
    out = _rep() / "dualtrack"
    out.mkdir(parents=True, exist_ok=True)
    summ = {"schema": "VIA.VRN.DualTrack.v1", "layout_run": d.parent.name, "units": len(recs), "tables": sum(1 for x in recs if x["kind"] == "table"), "info": sum(1 for x in recs if x["kind"] == "info"),
            "cache_hit": hit, "ocr_new": oc["done"], "ocr_secs": oc["secs"], "budget_hit": oc["killed"], "workers": workers, "dpi": dpi, "cleaned": cleaned, "all_green": all_green,
            "lamps": dict(Counter(x["lamp"] for x in recs)), "paths": dict(Counter(x["path"] for x in recs)), "secs": int(time.time() - t0)}
    (out / "DUALTRACK_latest.json").write_text(json.dumps(dict(summ, records=recs), ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    page = _resolve("_page")
    if page:
        rows = [(x["lamp"], [x["kind"], x["file"][:40], x["id"], x["page"], x.get("nonocr", ""), x["ocr"], "—" if x.get("agree") is None else "%.0f%%" % (100 * x["agree"]), x["path"],
                             html.escape(json.dumps(x.get("conflicts") or x.get("fields") or "", ensure_ascii=False)[:160])]) for x in recs]
        (out / "DUALTRACK_latest.html").write_text(page("NON-OCR / OCR 雙軌並進 · 逐格比對 · 三燈信心(綠 = 兩軌一致 · 黃 = 部分 / 單軌 · 紅 = 衝突 / 兩軌都沒有)",
                                                        "讀 %s · 單位 %d · 快取命中 %d · 新跑 OCR %d(%d 秒 · 工人 %d · %d DPI)%s" % (html.escape(d.parent.name), len(recs), hit, oc["done"], oc["secs"], workers, dpi,
                                                                                                       " · 預算用完" if oc["killed"] else ""),
                                                        ["類", "報告", "單位", "頁", "NON-OCR", "OCR", "一致度", "前後路徑判定", "衝突 / 欄位"], rows), encoding="utf-8")
        summ["html"] = str(out / "DUALTRACK_latest.html")
    summ["records"] = recs
    return summ


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()
    opt = lambda k, dv="": args[args.index(k) + 1] if k in args and args.index(k) + 1 < len(args) else dv  # noqa: E731
    if args[:1] == ["dualtrack"]:
        inst = _resolve("install_v166")
        if inst:
            inst()
        o = dualtrack_run(int(opt("--workers", "2") or 2), int(opt("--budget", "1200") or 1200), int(opt("--dpi", "200") or 200))
        if o.get("err"):
            print("[計] 雙軌 · %s · RED" % o["err"])
            return 1
        tb = [x for x in o["records"] if x["kind"] == "table"]
        inf = [x for x in o["records"] if x["kind"] == "info"]
        ags = [x["agree"] for x in tb if x.get("agree") is not None]
        print("[計] NON-OCR / OCR 雙軌並進 · 讀上一輪 layout(%s)· 單位 %d(表 %d · 資訊區 %d)· 快取命中 %d · 新跑 OCR %d(%d 秒 · 工人 %d · %d DPI)%s%s" % (
            o["layout_run"], o["units"], o["tables"], o["info"], o["cache_hit"], o["ocr_new"], o["ocr_secs"], o["workers"], o["dpi"], " · 預算用完(下一輪接著跑 · 已跑的進快取)" if o["budget_hit"] else "",
            (" · 清掉舊快取 %d" % o["cleaned"]) if o["cleaned"] else ""))
        print("[計] 表 · " + " · ".join("%s %d" % kv for kv in Counter(x["path"] for x in tb).most_common()) + (" · 平均一致度 %.0f%%" % (100 * sum(ags) / len(ags)) if ags else ""))
        fc = Counter()
        for x in inf:
            for k, v in (x.get("fields") or {}).items():
                fc[(k, v[0])] += 1
        print("[計] 資訊區 · " + " · ".join("%s %s/%d" % (k, fc[(k, "一致")], sum(fc[(k, s)] for s in ("一致", "衝突", "單軌"))) for k in ("評等", "目標價", "報告日")) + " 一致")
        print("[計] 三燈 · 綠 %d · 黃 %d · 紅 %d · 全綠 %s(全綠才清換輸入後的舊快取)" % (o["lamps"].get("GREEN", 0), o["lamps"].get("YELLOW", 0), o["lamps"].get("RED", 0), "是" if o["all_green"] else "否"))
        if o.get("html"):
            print("  [U/I] %s" % o["html"])
        return 0
    if args[:1] == ["selfgate"] and "--sandbox" not in args:
        o = _resolve("selfgate_run")("quick", panorama="--no-panorama" not in args)
        rc = _resolve("_print_gate")(o)
        if not o.get("cached") and o.get("verdict") != "RED":
            try:
                rg = auto_register()
                print("[計] 自動註冊(VRN SystemManager 唯一寫入者)· %s · 族 %s · 新編號 %s" % (rg.get("file"), rg.get("families", "—"), rg.get("new", 0)))
            except Exception as exc:  # noqa: BLE001
                print("[計] 自動註冊 · 沒寫成 %s(不擋)" % type(exc).__name__)
        return rc
    if args[:1] == ["engines"] and "--register" in args:
        rc = PRIOR.main([a for a in args if a != "--register"])
        rg = auto_register()
        print("[計] 註冊(唯一寫入者 · 穩定編號)· %s · 族 %s · 新編號 %s" % (rg.get("file"), rg.get("families", "—"), rg.get("new", 0)))
        return rc
    return PRIOR.main(args)



def selftest() -> int:
    import shutil
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)
    td = Path(tempfile.mkdtemp(prefix="vrn176-"))
    saved = {k: os.environ.get(k) for k in ("VIA_VRN_HEALTH_OUT", "VIA_SPILL_DIR", "VIA_TEMP_ROOT", "VIA_VRN_SANDBOX_OF", "VIA_VRN_GATE_BEAT")}
    try:
        import contextlib
        import io
        os.environ["VIA_VRN_HEALTH_OUT"] = str(td / "rep")
        ch = td / "chain"
        ch.mkdir()
        (ch / ("%s_v0300.py" % _STEM)).write_text("import sys, time\nif '--selftest' in sys.argv:\n    time.sleep(1.2)\n    print('  [FAIL] 甲 3 件')\n", encoding="utf-8")
        os.environ["VIA_VRN_SANDBOX_OF"] = str(ch)
        os.environ["VIA_VRN_GATE_BEAT"] = "0.3"
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            r1 = chain_selftest_v176(ch / ("%s_v0300.py" % _STEM), 60)
            t0 = time.time()
            r2 = chain_selftest_v176(ch / ("%s_v0300.py" % _STEM), 60)
            el = time.time() - t0
        chk("① 在地測試看得到:跑的時候每 0.3 秒印心跳 · 同一條鏈第二次直接沿用快取(%.2f 秒)· FAIL 一樣「甲 # 件」" % el,
            "在地測試 進行中" in buf.getvalue() and r1["fails"] == {"甲 # 件"} and r2.get("cached") and r2["fails"] == r1["fails"] and el < 0.5)
        home = td / "VRN"
        (home / "registry").mkdir(parents=True)
        rows = [{"family": "VRN_B", "ext": ".py", "tail": "VRN_B_v0102.py", "n": 3, "sha8": "bb", "accel": True}, {"family": "VRN_A", "ext": ".py", "tail": "VRN_A_v0100.py", "n": 1, "sha8": "aa", "accel": True}]
        g1 = register_v176(rows, home)
        g2 = register_v176(rows, home)
        g3 = register_v176(rows + [{"family": "VRN_0New", "ext": ".py", "tail": "VRN_0New_v0100.py", "n": 1, "sha8": "cc", "accel": True}], home)
        g4 = register_v176([rows[1]], home)
        last = max((home / "registry").glob("VRN_Engine_Register_v*.json"), key=_vnum_v0176)
        bk = json.loads(last.read_text(encoding="utf-8"))["engines"]
        chk("② 自動註冊:同一本冊 · 編號穩定(VRN_A=0001 · VRN_B=0002 · 後來的 VRN_0New=0003 不插隊)· 沒變不出新版 · 不見的族標 ABSENT 不刪",
            g1["file"] == "VRN_Engine_Register_v0100.json" and not g2["changed"] and g3["new"] == 1 and last.name == "VRN_Engine_Register_v0102.json" and bk["VRN_A.py"]["no"] == "VRN-E-0001" and bk["VRN_B.py"]["no"] == "VRN-E-0002"
            and bk["VRN_0New.py"]["no"] == "VRN-E-0003" and bk["VRN_B.py"]["status"].startswith("ABSENT") and bk["VRN_B.py"]["version"] == "v0102")
        lex = (_resolve("_lex") or (lambda: []))()
        A = [["NT$m", "2024A", "2025F"], ["Revenue", "1,234", "1,456"], ["EPS", "2.31", "3.10"]]
        B = [["", "2024A", "2025F"], ["Revenue", "1,234", "1,456"], ["EPS", "2.31", "3.01"]]
        c1, c2 = dt_compare_table(A, A, lex), dt_compare_table(A, B, lex)
        c3 = dt_compare_table([["", "2024A"], ["Net income", "300"]], [["", "2024A"], ["Netincome", "300"]], lex)
        chk("③ 表逐格比對(科目 × 期間):完全一樣 → 100%%;EPS 2025F 3.10 vs 3.01 → 衝突列出 · 一致度 %s;OCR 吃掉空白 Netincome = Net income → %s" % (c2["agree"], c3["agree"]),
            c1["agree"] == 1.0 and c2["agree"] == 0.75 and c2["conflicts"] and "eps" in c2["conflicts"][0][0] and c3["agree"] == 1.0)
        fi = dt_compare_info({"rating_raw": "Buy", "rating": "Buy", "tp": 260.0, "date": "2026-05-21"}, "Rating: Buy  Target price: TWD 260  21 May 2026", "2026-05-21")
        chk("④ 資訊區三欄比對:評等 / 目標價 / 報告日 → %s" % " · ".join("%s %s" % (k, v[0]) for k, v in fi.items()), all(v[0] == "一致" for v in fi.values()))
        if importlib.util.find_spec("rapidocr_onnxruntime") and importlib.util.find_spec("fitz"):
            from reportlab.pdfgen import canvas
            stage = td / "VIA_progress" / "ps_x" / "spill" / "vrn_stage_r1"
            (stage / "layout_l2").mkdir(parents=True)
            mini = stage / "m.pdf"
            c = canvas.Canvas(str(mini), pagesize=(595, 842))
            Y = lambda y: 842 - y - 10  # noqa: E731
            c.setFont("Helvetica", 11)
            for i, t in enumerate(["Rating: Buy", "Target price: TWD 260", "21 May 2026"]):
                c.drawString(40, Y(60 + 18 * i), t)
            for t, x in (("NT$m", 260), ("2024A", 380), ("2025F", 480)):
                c.drawString(x, Y(300), t)
            for y, lab, v in ((322, "Revenue", ("1,234", "1,456")), (344, "EPS", ("2.31", "3.10")), (366, "Net income", ("300", "350"))):
                c.drawString(260, Y(y), lab)
                c.drawString(380, Y(y), v[0])
                c.drawString(480, Y(y), v[1])
            c.save()
            tbl = {"id": "P1·R·01·T1", "kind": "table", "zone": "R", "role": "BODY", "sub": "財務表(損益)", "x0": 255, "top": 298, "x1": 540, "bottom": 380,
                   "rows": [["NT$m", "2024A", "2025F"], ["Revenue", "1,234", "1,456"], ["EPS", "2.31", "3.10"], ["Net income", "300", "350"]], "verify": {"ok": True}}
            inb = {"id": "P1·L·01", "kind": "text", "zone": "L", "role": "INFO", "x0": 38, "top": 58, "x1": 200, "bottom": 104}
            (stage / "layout_l2" / "a.json").write_text(json.dumps({"row": {"file": "Daiwa-6278 20260521.pdf", "code": "6278", "date": "2026-05-21", "mini": str(mini), "picked": [1]},
                                                                    "info": {"rating": "Buy", "rating_raw": "Buy", "tp": 260.0, "date_p1": "2026-05-21"},
                                                                    "pages": [{"page": 1, "roles": {"L": "INFO", "R": "BODY"}, "blocks": [inb, tbl]}]}, ensure_ascii=False), encoding="utf-8")
            os.environ["VIA_SPILL_DIR"] = str(td / "VIA_progress" / "ps_new" / "spill")
            os.environ["VIA_TEMP_ROOT"] = str(td / "VIA_progress")
            o1 = dualtrack_run(workers=2, budget=120, dpi=200)
            T = {x["kind"]: x for x in o1["records"]}
            chk("⑤ 雙軌並進(OCR 在 2 個子程序工人跑):表 兩軌一致度 %s → %s · 資訊區三欄 → %s" % (T["table"].get("agree"), T["table"]["lamp"], T["info"]["lamp"]),
                T["table"]["lamp"] == "GREEN" and T["info"]["lamp"] == "GREEN" and o1["ocr_new"] == 2 and o1["all_green"])
            t0 = time.time()
            o2 = dualtrack_run(workers=2, budget=120, dpi=200)
            chk("⑥ 同輸入不重跑:第二次全部快取命中(%d)· 新跑 OCR 0 · %.1f 秒" % (o2["cache_hit"], time.time() - t0), o2["cache_hit"] == 2 and o2["ocr_new"] == 0 and o2["all_green"])
            j = json.loads((stage / "layout_l2" / "a.json").read_text(encoding="utf-8"))
            j["pages"][0]["blocks"][1]["x1"] = 545
            (stage / "layout_l2" / "a.json").write_text(json.dumps(j, ensure_ascii=False), encoding="utf-8")
            o3 = dualtrack_run(workers=1, budget=120, dpi=200)
            chk("⑦ 換輸入 + 上一輪全綠 → 才清掉用不到的舊快取(清 %d)· 新的照跑" % o3["cleaned"], o3["cleaned"] == 1 and o3["ocr_new"] == 1)
        else:
            chk("⑤ 這台沒有 rapidocr / PyMuPDF → 雙軌端到端略過", True)
            chk("⑥ (略)", True)
            chk("⑦ (略)", True)
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(td, ignore_errors=True)
    me = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 最新有版號加速器橋 [VIA:ACCEL-BRIDGE:v0111] · 自帶多程序墊片", "[VIA:ACCEL-BRIDGE:v0111]" in me and _job_entry.__module__ in ("__main__", __name__))
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("⑨ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    print("[計] VRN_SystemManager_v0176 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
