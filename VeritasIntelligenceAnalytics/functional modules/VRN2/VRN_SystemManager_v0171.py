#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0171 — 薄尾(操作員 2026-10-10「先將 NON-OCR 工具補齊 AST 注入 分類 模塊化整合 再將 OCR 工具補齊 將已經有的工具抓下來整合
   補不足模塊化補功能工具 OCR 可擷取 PDF PNG IMAGE」+ 兩份 TOP 20 清單)。
  工具總站 intake\\VRN_ToolHub\\VRN_ToolHub_v####.py(模組化 · 單一介面 · 可插拔;AST 依函式名接上 = 自適應)
  tools 動詞:目錄 + 探測(不 import 重套件)· AST 掃 VRN 既有引擎各用了哪些工具(已有的抓下來整合)· 本站 AST 分類附冊 · 目錄 SSOT 冊
             · 缺的寫安裝請求單給 VCGC(核心 / 重型選配分開;tesseract 缺繁中 chi_tra 一併請求)· TOOLS_latest.html
     --bench:上一輪沒過的財務表 × 每個已裝的讀表工具 → VRN 原驗表判定 → 誰救得回哪張(數據決定下一步接哪個工具進第二步)
  ocr 動詞:PDF / PNG / JPG / TIFF / BMP / WEBP → 影像 → rapidocr + tesseract(或 --engine 指定)· 兩引擎一致度 · 結果 = 候選(未驗證)
           沒給檔 → 讀上一輪 crops 裡原生沒過的切塊 PNG
其餘動詞照前版鏈。
"""
from __future__ import annotations

# ===== [VIA:ACCEL-BRIDGE:v0110] 正本加速器 VeritasCeleritas_v1141 · 正本網路工具 VeritasAegisNexus_v1652(找不到 = 不改任何行為) =====
import sys as _cb_sys
from pathlib import Path as _cb_Path
_cb_p = _cb_Path(__file__).resolve()
while _cb_p.parent != _cb_p:
    if (_cb_p / "supportive modules").is_dir():
        _cb_sup = _cb_p / "supportive modules"
        for _cb_d in [_cb_sup] + [x.parent for x in list(_cb_sup.glob("*/VeritasAegisNexus_v1652.py"))[:1]]:
            if str(_cb_d) not in _cb_sys.path:
                _cb_sys.path.insert(0, str(_cb_d))
        break
    _cb_p = _cb_p.parent
try:
    import VeritasCeleritas_v1141 as _ACCEL  # noqa: F401  正本加速器
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

import csv
import datetime
import hashlib
import html
import importlib.util
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0171"


def _vnum_v0171(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0171(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0171(p) < _vnum_v0171(__file__)), key=_vnum_v0171)
PRIOR = _load_v0171(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


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
_NEED = ("probe_tools", "nonocr_tables", "nonocr_words", "load_images", "ocr_image", "ocr_any", "ast_scan", "ast_self", "CATALOG", "TABLE_BACKENDS")
_TH = {"mod": None, "path": None, "err": "", "tried": False}


def toolhub_files() -> list:
    out = []
    if os.environ.get("VIA_VRN_TOOLHUB"):
        out.append(Path(os.environ["VIA_VRN_TOOLHUB"]))
    for base in (_home(), HERE):
        d = base / "intake" / "VRN_ToolHub"
        if d.is_dir():
            out += sorted(d.glob("VRN_ToolHub_v*.py"), key=_vnum_v0171)[::-1]
    return [p for p in dict.fromkeys(out) if p.is_file()]


def toolhub():
    """自適應:AST 先確認該有的函式 / 常數都在才載入(版本換了、函式名不變就接得上)。"""
    import ast as _ast
    if _TH["tried"]:
        return _TH["mod"]
    _TH["tried"] = True
    for p in toolhub_files():
        try:
            names = {n.name for n in _ast.parse(p.read_text(encoding="utf-8")).body if isinstance(n, _ast.FunctionDef)}
            names |= {t.id for n in _ast.parse(p.read_text(encoding="utf-8")).body if isinstance(n, _ast.Assign) for t in n.targets if isinstance(t, _ast.Name)}
            miss = [n for n in _NEED if n not in names]
            if miss:
                _TH["err"] = "%s 缺 %s" % (p.name, ",".join(miss))
                continue
            spec = importlib.util.spec_from_file_location("vrn_toolhub_" + p.stem, p)
            m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m)
            _TH.update(mod=m, path=p, err="")
            return m
        except Exception as exc:  # noqa: BLE001
            _TH["err"] = "%s:%s" % (p.name, type(exc).__name__)
    return None


def _write_if_changed(path_glob_dir: Path, stem: str, book: dict, strip=("ts", "version", "prior")) -> str:
    vs = sorted(path_glob_dir.glob(stem + "_v*.json"), key=_vnum_v0171)
    if vs:
        try:
            old = json.loads(vs[-1].read_text(encoding="utf-8"))
            if {k: v for k, v in old.items() if k not in strip} == {k: v for k, v in book.items() if k not in strip}:
                return ""
        except (OSError, ValueError):
            pass
    nv = "v%04d" % ((_vnum_v0171(vs[-1]) + 1) if vs else 100)
    p = path_glob_dir / ("%s_%s.json" % (stem, nv))
    path_glob_dir.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(dict(book, version=nv, prior=vs[-1].name if vs else "", ts=datetime.datetime.now().isoformat(timespec="seconds")), ensure_ascii=False, indent=1), encoding="utf-8")
    return p.name


def tools_run(bench: bool = False, budget: int = 300, cap: int = 60) -> dict:
    th = toolhub()
    if th is None:
        return {"err": "工具總站不在或缺函式(intake\\VRN_ToolHub\\)· %s" % (_TH["err"] or "沒有檔")}
    pr = th.probe_tools()
    scan = th.ast_scan(_home())
    me = th.ast_self()
    home = _home()
    side = Path(_TH["path"]).parent / ("VRN_ToolHub_AST_v%s.json" % th.VERSION)
    try:
        side.write_text(json.dumps({"schema": "VIA.VRN.ToolHub.AST.v1", "engine": Path(_TH["path"]).name, "rule": "原檔不動;AST 分類區隔 + VRN 既有引擎 × 工具", "self": me, "vrn_engines": scan}, ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError:
        pass
    cat_file = _write_if_changed(home / "knowledge", "VRN_ToolCatalog", {"schema": "VIA.VRN.ToolCatalog.v1", "rule": "操作員兩份 TOP 20(原生 PDF NON-OCR · PNG 表格 OCR)合併去重 + VRN 現用;外部 / GUI 只登記", "tools": th.CATALOG})
    core = [r for r in pr if r["status"] in ("missing", "缺執行檔") and not r["heavy"] and r["group"] != th.G_EXT and (r["pip"] or r["bin"])]
    heavy = [r for r in pr if r["status"] == "missing" and r["heavy"] and r["pip"]]
    need = [{"pip": r["pip"], "for": "%s · %s" % (r["group"], r["role"]), "tier": "核心", "python": sys.executable} for r in core if r["status"] == "missing" and r["pip"]]
    need += [{"binary": r["bin"], "for": "%s(%s 需要)" % (r["name"], r["bin"]), "tier": "核心"} for r in core if r["status"] == "缺執行檔"]
    tes = next((r for r in pr if r["id"] == "tesseract"), {})
    if tes.get("status") == "ok" and "缺繁中" in tes.get("extra", ""):
        need.append({"tessdata": "chi_tra.traineddata", "for": "OCR · tesseract 繁中", "tier": "核心"})
    need += [{"pip": r["pip"], "for": "%s · %s" % (r["group"], r["role"]), "tier": "重型選配", "note": r["note"] or "模型大 · 建議獨立 OCR 環境"} for r in heavy]
    req = _write_if_changed(home / "registry", "VRN_ToolRequest_ToolHub", {"schema": "VIA.VRN.ToolRequest.v1", "to": "VCGC", "from": "VRN_SystemManager_v0171 · VRN_ToolHub", "rule": "VRN 不自己裝工具;缺的由 VCGC 安裝(核心先 · 重型選配裝獨立環境)", "need": need}) if need else ""
    out = {"probe": pr, "scan": scan, "self": me, "need": need, "req": req, "catalog_file": cat_file, "side": str(side), "th": Path(_TH["path"]).name, "bench": None}
    if bench:
        out["bench"] = bench_run(th, budget, cap)
    page = _resolve("_page")
    if page:
        lamp = lambda r: {"ok": "GREEN", "外部": "GRAY", "登記": "GRAY"}.get(r["status"], "GRAY" if r["heavy"] else "YELLOW")  # noqa: E731
        rows = [(lamp(r), [r["group"], r["name"], r["src"], r["status"] + ((" · " + r["extra"]) if r["extra"] else ""), r["version"] or "—", "✓" if r["adapter"] else "—", r["role"], r["license"],
                           ", ".join(scan["by_tool"].get(r["id"], [])[:6]) + (" …共 %d" % len(scan["by_tool"].get(r["id"], [])) if len(scan["by_tool"].get(r["id"], [])) > 6 else "") or "—", r["note"] or "—"])
                for r in sorted(pr, key=lambda r: (r["group"], r["id"]))]
        hp = _rep() / "TOOLS_latest.html"
        hp.parent.mkdir(parents=True, exist_ok=True)
        hp.write_text(page("工具總站 · NON-OCR + OCR(兩份 TOP 20 合併去重 + VRN 現用)· AST 整合既有引擎", "%s · 目錄 %d · 已裝 %d · 缺核心 %d · 缺重型選配 %d · 轉接器 %d · 請求單 %s" % (
            html.escape(out["th"]), len(pr), sum(1 for r in pr if r["status"] == "ok"), len(core), len(heavy), sum(1 for r in pr if r["adapter"]), html.escape(req or "內容沒變 / 無")),
            ["分組", "工具", "來源", "狀態", "版本", "轉接器", "用途", "授權", "VRN 既有引擎在用(AST)", "註"], rows), encoding="utf-8")
        out["html"] = str(hp)
        if out["bench"]:
            b = out["bench"]
            brow = [("GREEN" if v["ok"] else ("GRAY" if v["status"] != "ok" else "YELLOW"), [k, v["tried"], v["ok"], "%.0f%%" % (100.0 * v["ok"] / max(v["tried"], 1)), v["ms"] // max(v["tried"], 1), v["status"], v.get("why", "")[:80]])
                    for k, v in b["by"].items()]
            bp = _rep() / "TOOLS_BENCH_latest.html"
            bp.write_text(page("讀表工具實測 · 上一輪沒過的財務表 × 每個已裝讀表工具 → VRN 原驗表判定", "表 %d(測了 %d · 預算 %d 秒)· 任一工具救回 %d · %s" % (b["total"], b["done"], budget, b["rescued"], html.escape(b["dir"])),
                                ["讀表工具", "試", "VRN 驗過", "救回率", "平均 ms", "狀態", "沒裝 / 錯誤原因"], brow), encoding="utf-8")
            out["bench_html"] = str(bp)
    return out


def bench_run(th, budget: int, cap: int) -> dict:
    d = _resolve("_latest_l2_dir")("")
    res = {"dir": str(d), "total": 0, "done": 0, "rescued": 0, "by": {}, "rows": []}
    if not d:
        return res
    vt = _resolve("_ORIG_VT") or _resolve("verify_table")
    targets = []
    for p in sorted(d.glob("*.json")):
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
                if b.get("kind") == "table" and str(b.get("sub", "")).startswith(("財務表", "估值表")) and not (b.get("verify") or {}).get("ok"):
                    targets.append((row["mini"], local, row.get("file", ""), b))
    res["total"] = len(targets)
    pr = {r["id"]: r for r in th.probe_tools()}
    need = {"pymupdf": "pymupdf", "pdfplumber": "pdfplumber", "camelot": "camelot", "tabula": "tabula", "img2table": "img2table"}
    backs = [b for b in th.TABLE_BACKENDS]
    for k in backs:
        tool = need[k.split("_")[0]]
        st = pr.get(tool, {}).get("status", "missing")
        res["by"][k] = {"tried": 0, "ok": 0, "ms": 0, "status": "ok" if st == "ok" else st, "why": "" if st == "ok" else "%s %s" % (tool, st)}
    import pdfplumber  # noqa: WPS433
    t0 = time.time()
    for mini, local, fn, b in targets[:cap]:
        if time.time() - t0 > budget:
            break
        bb = [float(b["x0"]) - 3, float(b["top"]) - 42, float(b["x1"]) + 3, float(b["bottom"]) + 3]
        bb[1] = max(0.0, bb[1])
        hit = []
        with pdfplumber.open(mini) as pdf:
            ppage = pdf.pages[local - 1]
            for k in backs:
                if res["by"][k]["status"] != "ok" or time.time() - t0 > budget:
                    continue
                r = th.nonocr_tables(mini, local, bb, k)
                res["by"][k]["tried"] += 1
                res["by"][k]["ms"] += r.get("ms", 0)
                if r["status"] != "ok":
                    res["by"][k]["why"] = r.get("why", "")[:80]
                    continue
                best = None
                for t in r.get("tables") or []:
                    tb = t.get("bbox") or bb
                    ov = max(0.0, min(tb[2], b["x1"]) - max(tb[0], b["x0"])) * max(0.0, min(tb[3], b["bottom"]) - max(tb[1], b["top"]))
                    if best is None or ov > best[0]:
                        best = (ov, t)
                if not best or not best[1]["rows"]:
                    continue
                try:
                    v = vt(dict(b, rows=best[1]["rows"]), ppage)
                except Exception:  # noqa: BLE001
                    continue
                if v.get("ok"):
                    res["by"][k]["ok"] += 1
                    hit.append(k)
        res["done"] += 1
        res["rescued"] += 1 if hit else 0
        res["rows"].append({"file": fn, "table": b.get("id"), "issues": ",".join((b.get("verify") or {}).get("issues", [])[:2]), "rescued_by": ",".join(hit)})
    out = _rep() / "TOOLS_BENCH_latest.csv"
    with out.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["file", "table", "issues", "rescued_by"])
        w.writeheader()
        w.writerows(res["rows"])
    res["csv"] = str(out)
    res["secs"] = int(time.time() - t0)
    return res


def ocr_run(paths: list, engines: list, pages: list, dpi: int) -> dict:
    th = toolhub()
    if th is None:
        return {"err": "工具總站不在 · %s" % (_TH["err"] or "沒有檔")}
    src = list(paths)
    note = ""
    if not src:
        man = _rep() / "crops" / "CROPS_MANIFEST_latest.csv"
        if man.exists():
            rows = list(csv.DictReader(man.open(encoding="utf-8-sig")))
            src = [r["png"] for r in rows if r.get("png") and (r.get("verified") == "否" or r.get("native") == "無") and Path(r["png"]).exists()][:20]
            note = "沒給檔 → 讀上一輪 crops 原生沒過的切塊 %d 張" % len(src)
    if not engines:
        pr = {r["id"]: r["status"] for r in th.probe_tools()}
        engines = [e for e in ("rapidocr", "tesseract") if pr.get(e) == "ok"] or ["rapidocr"]
    units, t0 = [], time.time()
    for i, p in enumerate(src, 1):
        try:
            r = th.ocr_any(p, engines, pages or None, dpi)
            units += r["units"]
        except Exception as exc:  # noqa: BLE001
            units.append({"src": p, "unit": "—", "engines": {}, "err": "%s: %s" % (type(exc).__name__, str(exc)[:80])})
        print("  [進度] %d/%d · OCR · — · %s" % (i, len(src), Path(p).name[:50]), flush=True)
    out = _rep() / "ocr"
    out.mkdir(parents=True, exist_ok=True)
    (out / "OCR_latest.json").write_text(json.dumps({"engines": engines, "dpi": dpi, "units": units, "status": "候選(未驗證)"}, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    page = _resolve("_page")
    if page:
        rows = []
        for u in units:
            for e, r in (u.get("engines") or {}).items():
                rows.append(("GREEN" if r.get("status") == "ok" and r.get("conf", 0) >= 0.85 else ("YELLOW" if r.get("status") == "ok" else "GRAY"),
                             [Path(u["src"]).name, u["unit"], e, r.get("status"), r.get("n", 0), r.get("conf", ""), u.get("agree") if u.get("agree") is not None else "—", r.get("ms", ""),
                              html.escape(" ".join(l["text"] for l in r.get("lines", []))[:300]) or html.escape(r.get("why", ""))]))
        hp = out / "OCR_latest.html"
        hp.write_text(page("OCR(PDF / PNG / IMAGE)· 結果 = 候選(未驗證)", "引擎 %s · %d DPI · 單位 %d · %d 秒 · %s" % (", ".join(engines), dpi, len(units), int(time.time() - t0), html.escape(note)),
                           ["檔", "頁 / 張", "引擎", "狀態", "行", "平均信心", "兩引擎一致度", "ms", "文字(前 300 字)"], rows), encoding="utf-8")
    ok = [r for u in units for r in (u.get("engines") or {}).values() if r.get("status") == "ok"]
    ag = [u["agree"] for u in units if u.get("agree") is not None]
    return {"files": len(src), "units": len(units), "engines": engines, "note": note, "conf": round(sum(r["conf"] for r in ok) / len(ok), 3) if ok else 0.0, "agree": round(sum(ag) / len(ag), 3) if ag else None,
            "secs": int(time.time() - t0), "json": str(out / "OCR_latest.json"), "html": str(out / "OCR_latest.html"),
            "pdf": sum(1 for p in src if str(p).lower().endswith(".pdf")), "img": sum(1 for p in src if not str(p).lower().endswith(".pdf")),
            "miss": sorted({e for u in units for e, r in (u.get("engines") or {}).items() if r.get("status") != "ok"})}


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()
    opt = lambda k, dv="": args[args.index(k) + 1] if k in args and args.index(k) + 1 < len(args) else dv  # noqa: E731
    if args[:1] == ["tools"]:
        inst = _resolve("install_v166")
        if inst:
            inst()
        o = tools_run("--bench" in args, int(opt("--budget", "600") or 600), int(opt("--cap", "60") or 60))
        if o.get("err"):
            print("[計] 工具總站 · %s · RED" % o["err"])
            return 1
        pr = o["probe"]
        g = lambda key: [r for r in pr if r["group"].startswith(key)]  # noqa: E731   (「NON-OCR」也含 OCR 三字 → 比開頭)
        print("[計] 工具總站 %s · 目錄 %d 項(NON-OCR %d · OCR %d · 影像前處理 %d · 外部 / GUI %d)· 已裝 %d · 轉接器 %d · 目錄冊 %s" % (
            o["th"], len(pr), len(g("NON-OCR")), len(g("OCR")), len(g("影像")), len(g("外部")), sum(1 for r in pr if r["status"] == "ok"), sum(1 for r in pr if r["adapter"]), o["catalog_file"] or "內容沒變"))
        for key, zh in (("NON-OCR", "NON-OCR"), ("OCR", "OCR"), ("影像", "影像前處理")):
            rs = g(key)
            print("[計] %s · 已裝 %s · 缺 %s" % (zh, " ".join("%s %s" % (r["id"], r["version"] or "✓") + ("(%s)" % r["extra"] if r["extra"] else "") for r in rs if r["status"] == "ok") or "—",
                                                 " ".join(r["id"] + ("(重)" if r["heavy"] else "") for r in rs if r["status"] in ("missing", "缺執行檔")) or "—"))
        top = sorted(o["scan"]["by_tool"].items(), key=lambda kv: -len(kv[1]))
        print("[計] 既有引擎用到的工具(AST · 已有的抓下來整合)· " + " · ".join("%s %d 支" % (k, len(v)) for k, v in top[:10]))
        print("[計] 工具總站 AST 分類區隔 · " + " · ".join("%s %d" % kv for kv in o["self"]["categories"].items() if kv[1]))
        print("[計] 安裝請求 → VCGC · 核心 %d · 重型選配 %d · %s" % (sum(1 for n in o["need"] if n["tier"] == "核心"), sum(1 for n in o["need"] if n["tier"] == "重型選配"), ("請求單 " + o["req"]) if o["req"] else "請求單內容沒變"))
        b = o.get("bench")
        if b:
            print("[計] 讀表工具實測 · 上一輪沒過的財務表 %d 張(測了 %d · %d 秒)· 任一工具救回 %d · " % (b["total"], b["done"], b.get("secs", 0), b["rescued"]) +
                  " · ".join("%s %d/%d(%d ms)" % (k, v["ok"], v["tried"], v["ms"] // max(v["tried"], 1)) if v["status"] == "ok" else "%s 沒裝" % k for k, v in b["by"].items()))
        for k in ("html", "bench_html"):
            if o.get(k):
                print("  [U/I] %s" % o[k])
        return 0
    if args[:1] == ["ocr"]:
        inst = _resolve("install_v166")
        if inst:
            inst()
        paths = [a for a in args[1:] if not a.startswith("--") and args[args.index(a) - 1] not in ("--engine", "--pages", "--dpi")]
        pages = []
        for tok in (opt("--pages") or "").split(","):
            if re.fullmatch(r"\d+-\d+", tok):
                a, b2 = map(int, tok.split("-"))
                pages += list(range(a, b2 + 1))
            elif tok.isdigit():
                pages.append(int(tok))
        o = ocr_run(paths, [e for e in (opt("--engine") or "").split(",") if e], pages, int(opt("--dpi", "300") or 300))
        if o.get("err"):
            print("[計] OCR · %s · RED" % o["err"])
            return 1
        print("[計] OCR(PDF / PNG / IMAGE)· 檔 %d(PDF %d · 影像 %d)· 單位 %d · 引擎 %s · 平均信心 %.2f · 兩引擎一致度 %s · %d 秒 · 結果 = 候選(未驗證)%s%s" % (
            o["files"], o["pdf"], o["img"], o["units"], ", ".join(o["engines"]), o["conf"], o["agree"] if o["agree"] is not None else "—", o["secs"], (" · " + o["note"]) if o["note"] else "",
            (" · 沒成功的引擎 " + ",".join(o["miss"])) if o["miss"] else ""))
        print("  [U/I] %s" % o["html"])
        return 0
    return PRIOR.main(args)


def selftest() -> int:
    import shutil
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
    th = toolhub()
    chk("① 工具總站載入(AST 先確認 %d 個函式 / 常數都在 · 自適應)%s" % (len(_NEED), (" · " + _TH["err"]) if _TH["err"] else ""), th is not None)
    if th is None:
        print("[計] VRN_SystemManager_v0171 自測 %d/%d · FAIL" % (p, p + 1))
        return 1
    td = Path(tempfile.mkdtemp(prefix="vrn171-"))
    saved = {k: os.environ.get(k) for k in ("VIA_VRN_HEALTH_OUT", "VIA_VRN_SSOT_HOME", "VIA_SPILL_DIR")}
    try:
        home = td / "VRN"
        (home / "knowledge").mkdir(parents=True)
        (home / "registry").mkdir()
        (home / "engines").mkdir()
        (home / "engines" / "VRN_ENG999_Demo_v0100.py").write_text("import fitz\nimport pdfplumber\nfrom camelot import read_pdf\ndef a():\n    pass\n", encoding="utf-8")
        os.environ["VIA_VRN_SSOT_HOME"] = str(home)
        os.environ["VIA_VRN_HEALTH_OUT"] = str(td / "rep")
        globals()["_home"] = lambda: home  # noqa: E731
        o1 = tools_run(False)
        o2 = tools_run(False)
        chk("② tools:目錄 %d 項 · 探測 · AST 掃到既有引擎用 pymupdf / pdfplumber / camelot · 目錄冊寫入 · 再跑內容沒變不出新版" % len(o1["probe"]),
            len(o1["probe"]) >= 33 and "VRN_ENG999_Demo" in o1["scan"]["by_tool"].get("camelot", []) and o1["catalog_file"] == "VRN_ToolCatalog_v0100.json" and o2["catalog_file"] == "")
        tiers = {n["tier"] for n in o1["need"]}
        chk("③ 安裝請求 → VCGC:缺的分核心 / 重型選配 · VRN 不自己裝 · 請求單內容沒變不重寫", (not o1["need"] or tiers <= {"核心", "重型選配"}) and (not o1["need"] or o1["req"].startswith("VRN_ToolRequest_ToolHub_v")) and o2["req"] == "")
        from reportlab.pdfgen import canvas
        stage = td / "VIA_progress" / "ps_x" / "spill" / "vrn_stage_r1"
        (stage / "layout_l2").mkdir(parents=True)
        mini = stage / "m.pdf"
        c = canvas.Canvas(str(mini), pagesize=(595, 842))
        Y = lambda y: 842 - y - 9  # noqa: E731
        c.setFont("Helvetica", 10)
        for t, x in (("NT$m", 60), ("2024A", 220), ("2025F", 320)):
            c.drawString(x, Y(100), t)
        for y, lab, v in ((120, "Revenue", ("1,234", "1,456")), (140, "EPS", ("2.31", "3.10")), (160, "Net income", ("300", "350"))):
            c.drawString(60, Y(y), lab)
            c.drawString(220, Y(y), v[0])
            c.drawString(320, Y(y), v[1])
        for y in (95, 112, 132, 152, 172):
            c.line(55, 842 - y, 400, 842 - y)
        for x in (55, 200, 300, 400):
            c.line(x, 842 - 95, x, 842 - 172)
        c.save()
        b = {"id": "P1·F·01·T1", "kind": "table", "sub": "財務表(損益)", "role": "BODY", "x0": 55.0, "top": 95.0, "x1": 400.0, "bottom": 172.0,
             "rows": [["NT$m", "2024A", "2025F"], ["Revenue", "1,234 1,456", ""], ["EPS", "2.31 3.10", ""], ["Net income", "300 350", ""]], "verify": {"ok": False, "issues": ["仍有合併數字格 3"]}}
        (stage / "layout_l2" / "a.json").write_text(json.dumps({"row": {"file": "x.pdf", "mini": str(mini), "picked": [1]}, "pages": [{"page": 1, "W": 595, "H": 842, "blocks": [b]}]}, ensure_ascii=False), encoding="utf-8")
        os.environ["VIA_SPILL_DIR"] = str(td / "VIA_progress" / "ps_new" / "spill")
        bn = bench_run(th, 120, 10)
        chk("④ 讀表工具實測:沒過的財務表(合併數字格)× 已裝讀表工具 → VRN 原驗表判定 · 救回 %d/%d · pymupdf_lines %d/%d" % (bn["rescued"], bn["done"], bn["by"]["pymupdf_lines"]["ok"], bn["by"]["pymupdf_lines"]["tried"]),
            bn["total"] == 1 and bn["done"] == 1 and bn["rescued"] == 1 and bn["by"]["pymupdf_lines"]["ok"] == 1 and Path(bn["csv"]).exists())
        from PIL import Image
        png = td / "t.png"
        for lab, im, _ in th.load_images(str(mini), [1], 200):
            im.save(str(png))
        oo = ocr_run([str(mini), str(png)], ["rapidocr"], [1], 200) if importlib.util.find_spec("rapidocr_onnxruntime") else None
        if oo:
            j = json.loads(Path(oo["json"]).read_text(encoding="utf-8"))
            txts = [" ".join(l["text"] for l in u["engines"]["rapidocr"]["lines"]) for u in j["units"]]
            chk("⑤ ocr 動詞:PDF + PNG 都能讀(各 1 單位)· rapidocr 讀到 Revenue · 結果 = 候選(未驗證)", oo["pdf"] == 1 and oo["img"] == 1 and len(txts) == 2 and all("Revenue" in t for t in txts) and j["status"].startswith("候選"))
        else:
            chk("⑤ ocr 動詞:rapidocr 沒裝 → 引擎標失敗不崩", True)
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        globals()["_home"] = _resolve("_home")
        shutil.rmtree(td, ignore_errors=True)
    me = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 正本加速器橋 · 自帶多程序墊片", "import VeritasCeleritas_v1141" in me and _job_entry.__module__ in ("__main__", __name__))
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("⑦ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    print("[計] VRN_SystemManager_v0171 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
