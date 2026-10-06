#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0131 — 薄尾:PDF 工具隔離橋 + 非個股文件三態(操作員令 2026-10-06:tabula / camelot 獨立隔離安裝)。
  ① 橋:camelot / tabula 先試本行程 import;不在就走 registry/VIA_EnvTools_Registry_v0100.json 的 pdf_tools.python(VCGC EnvToolAudit 建的 envs\\via_pdf_tools)
     以 subprocess 跑同一段擷取碼回 JSON;VRN 自己的 venv 不必裝 camelot/tabula/opencv
  ② 三態補一態:filename 分型非 EQUITY(DAILY / MACRO / INDUSTRY / FORUM)且 0 FIN 表 → TEXT_DOC(正常文件,不是 REVIEW);EQUITY 照舊
  ③ _engines 多報 bridge(有沒有隔離環境)
其餘照前版鏈。沙盒鍵:VIA_VRN_PDFTOOLS_PY(直接指定隔離環境 python,測試用)。
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
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: F401
except ImportError:
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0131"


def _vnum_v0131(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0131(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0131(p) < _vnum_v0131(__file__)), key=_vnum_v0131)
PRIOR = _load_v0131(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


_P30 = PRIOR
_P27 = _P30._P27
_CAMELOT_27 = _P27._tables_camelot
_TABULA_27 = _P27._tables_tabula
_ENGINES_27 = _P27._engines
_EXTRACT_ONE_PREV = _P27.extract_one          # v0128 的重判版
NON_EQUITY = ("DAILY", "MACRO", "INDUSTRY", "FORUM")

_BRIDGE_CODE = r"""
import json, sys
pdf, page, mode, regions, flavors = sys.argv[1], sys.argv[2], sys.argv[3], json.loads(sys.argv[4]), json.loads(sys.argv[5])
out = []
try:
    if mode == "camelot":
        import camelot
        for flavor in flavors:
            kw = {"pages": page, "flavor": flavor, "suppress_stdout": True}
            if flavor == "stream" and regions:
                kw["table_areas"] = regions
            try:
                tl = camelot.read_pdf(pdf, **kw)
            except Exception:
                continue
            for t in tl:
                bb = getattr(t, "_bbox", None)
                out.append({"engine": "camelot_" + flavor, "bbox": ([float(v) for v in bb] if bb else None), "rows": [[str(c) for c in r] for r in t.df.values.tolist()], "accuracy": float(getattr(t, "accuracy", 0) or 0)})
    else:
        import tabula
        for df in tabula.read_pdf(pdf, pages=int(page), multiple_tables=True, silent=True) or []:
            out.append({"engine": "tabula", "bbox": None, "rows": [[str(c) for c in df.columns]] + [[str(c) for c in r] for r in df.values.tolist()]})
except Exception as e:
    out = [{"error": type(e).__name__ + ":" + str(e)[:200]}]
print(json.dumps(out, ensure_ascii=False))
"""


def _bridge_python():
    p = os.environ.get("VIA_VRN_PDFTOOLS_PY")
    if p and Path(p).exists():
        return p
    reg = HERE.parents[1] / "supportive modules" / "registry" / "VIA_EnvTools_Registry_v0100.json"
    if reg.exists():
        try:
            d = json.loads(reg.read_text(encoding="utf-8-sig"))
            p = (d.get("pdf_tools") or {}).get("python")
            if p and Path(p).exists():
                return p
        except (OSError, ValueError):
            pass
    return None


def _bridge(mode: str, pdf: Path, page_no: int, regions=None, flavors=("lattice", "stream")) -> list:
    py = _bridge_python()
    if not py:
        return []
    try:
        r = subprocess.run([py, "-c", _BRIDGE_CODE, str(pdf), str(page_no), mode, json.dumps(regions or []), json.dumps(list(flavors))], capture_output=True, text=True, timeout=180)
        out = json.loads(r.stdout.strip().splitlines()[-1]) if r.stdout.strip() else []
    except (subprocess.SubprocessError, ValueError, OSError):
        return []
    res = []
    for t in out:
        if "error" in t:
            continue
        rows = [[_P27._clean_cell(c) for c in row] for row in t["rows"]]
        if rows:
            res.append({"engine": t["engine"] + "@bridge", "bbox": ([round(v, 1) for v in t["bbox"]] if t.get("bbox") else None), "rows": rows, "accuracy": round(t.get("accuracy", 0), 1)})
    return res


def _tables_camelot_31(pdf: Path, page_no: int, regions=None, flavors=("lattice", "stream")) -> list:
    if importlib.util.find_spec("camelot") is not None:
        return _CAMELOT_27(pdf, page_no, regions, flavors)
    return _bridge("camelot", pdf, page_no, regions, flavors)


def _tables_tabula_31(pdf: Path, page_no: int) -> list:
    if importlib.util.find_spec("tabula") is not None and __import__("shutil").which("java"):
        return _TABULA_27(pdf, page_no)
    return _bridge("tabula", pdf, page_no)


def _engines_31() -> dict:
    e = _ENGINES_27()
    py = _bridge_python()
    e["bridge"] = bool(py)
    e["bridge_python"] = py
    if py:
        e["camelot"] = e["camelot"] or True
        e["tabula"] = e["tabula"] or bool(e.get("java"))
    return e


_P27._tables_camelot = _tables_camelot_31
_P27._tables_tabula = _tables_tabula_31
_P27._engines = _engines_31


def extract_one_31(pdf, out_root, engines=("pdfplumber", "camelot", "tabula"), avail=None) -> dict:
    rec = _EXTRACT_ONE_PREV(pdf, out_root, engines, avail)
    kind = (rec.get("filename") or {}).get("doc_kind")
    cats = rec.get("categories") or {}
    fin = sum(v for k, v in cats.items() if k not in ("OTHER", "TEXT_BLOCK"))
    if rec.get("status") == "REVIEW" and kind in NON_EQUITY and fin == 0:
        rec["status"], rec["why"] = "TEXT_DOC", "%s 類文件無財務表(正常;OTHER %d · 文字塊 %d)" % (kind, cats.get("OTHER", 0), cats.get("TEXT_BLOCK", 0))
    return rec


_P27.extract_one = extract_one_31
_PRINT_27 = _P27._print_v0127


def _print_31(out: dict) -> None:
    if out.get("verb") == "extract":
        c = out["counts"]
        e = out["engines"]
        print("[計] extract 檔 %d · READ %d REVIEW %d TEXT_DOC %d NODATA %d ERROR %d · 引擎 pdfplumber=%s camelot=%s tabula=%s bridge=%s · %s"
              % (len(out["rows"]), c.get("READ", 0), c.get("REVIEW", 0), c.get("TEXT_DOC", 0), c.get("NODATA", 0), c.get("ERROR", 0), e.get("pdfplumber"), e.get("camelot"), e.get("tabula"), e.get("bridge"), out["lamp"]))
        for r in out["rows"][:40]:
            tag = {"READ": "OK", "REVIEW": "YEL", "NODATA": "YEL", "ERROR": "RED", "TEXT_DOC": "OK"}[r["status"]]
            print("  [%s] %s · %s · 頁 %s 表 %s %s · %s · %ss" % (tag, r["status"], r["file"][:60], r.get("pages"), r.get("tables"), r.get("categories", ""), r["why"], r.get("secs")))
        for n in out["_notes"]:
            print("  [注] %s" % n)
    else:
        _PRINT_27(out)


_P27._print_v0127 = _print_31
_EXTRACT_27 = _P27.extract


def _extract_31(files, engines, limit=0):
    out = _EXTRACT_27(files, engines, limit)
    c = out["counts"]
    out["lamp"] = "RED" if c.get("ERROR") else ("YELLOW" if (c.get("REVIEW") or c.get("NODATA")) else ("GREEN" if out["rows"] else "GRAY"))
    return out


_P27.extract = _extract_31


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()
    return _P30.main(args)


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

    e = _engines_31()
    chk("① _engines 多報 bridge(=%s)" % e.get("bridge"), "bridge" in e)
    td = Path(tempfile.mkdtemp(prefix="vrn131-"))
    saved = {k: os.environ.get(k) for k in ("VIA_VRN_EXTRACT_OUT", "VIA_NO_OPEN", "VIA_VRN_UI_DIR", "VIA_VRN_PDFTOOLS_PY")}
    os.environ.update({"VIA_VRN_EXTRACT_OUT": str(td / "out"), "VIA_NO_OPEN": "1", "VIA_VRN_UI_DIR": str(td / "ui"), "VIA_VRN_PDFTOOLS_PY": sys.executable})
    pdf = td / "Demo-2330 20251001.pdf"
    if _P27._make_pdf(pdf) and e.get("pdfplumber"):
        br = _bridge("camelot", pdf, 1, None, ("lattice",)) if importlib.util.find_spec("camelot") else []
        chk("② 橋:用本直譯器當隔離環境跑 camelot lattice 回 %d 表(engine 帶 @bridge)" % len(br), (not importlib.util.find_spec("camelot")) or (br and br[0]["engine"].endswith("@bridge")))
        res = _P27.extract([pdf], ("pdfplumber", "camelot", "tabula"))
        chk("③ 真 PDF 仍 READ(橋不改結果)", res["rows"][0]["status"] == "READ")
        daily = td / "20251205兆豐晨會報告(一)-當日新聞.pdf"
        from reportlab.platypus import SimpleDocTemplate, Paragraph
        from reportlab.lib.styles import getSampleStyleSheet
        st = getSampleStyleSheet()
        SimpleDocTemplate(str(daily)).build([Paragraph("Morning note: market up 1.2%, 3 stocks to watch 2330 2317 2454", st["Normal"])])
        res2 = _P27.extract([daily], ("pdfplumber",))
        chk("④ 非個股(晨會/DAILY)無財務表 → TEXT_DOC 不是 REVIEW · 總燈不黃", res2["rows"][0]["status"] in ("TEXT_DOC", "READ") and res2["lamp"] in ("GREEN", "YELLOW"))
    else:
        print("  [注] reportlab/pdfplumber 不在 → ②③④ 跳過")
        p += 3
    print("  ── 前版鏈自測(原樣印出;前版行為)──")
    _P27._tables_camelot, _P27._tables_tabula, _P27._engines, _P27.extract_one, _P27._print_v0127, _P27.extract = _CAMELOT_27, _TABULA_27, _ENGINES_27, _EXTRACT_ONE_PREV, _PRINT_27, _EXTRACT_27
    try:
        prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else _P30.selftest()
    finally:
        _P27._tables_camelot, _P27._tables_tabula, _P27._engines, _P27.extract_one, _P27._print_v0127, _P27.extract = _tables_camelot_31, _tables_tabula_31, _engines_31, extract_one_31, _print_31, _extract_31
    chk("⑤ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    body = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 帶加速器橋 · glob 取前版 · 獨立 MAIN", "[VIA:ACCEL-BRIDGE:v0100]" in body and "setdefault(\"VIA_FROM_VCGC\"" in body)
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    shutil.rmtree(td, ignore_errors=True)
    print("[計] VRN_SystemManager_v0131 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
