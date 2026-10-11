#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0169 — 薄尾(操作員 2026-10-10 實跑 v0168:801 秒跑完 · 6 份 KeyError:'size' 整份失敗 · 復健 118 表只修好 2 · 沒跑 OCR 卻發安裝請求)。
  ① 修崩潰:「改回正文」的區塊沿用 _lines() 產生逐行資料(字級 size · 粗體 · 字型)· 產生不出來就不改(維持表)
  ② 復健記原因 + 取字範圍往上多 42 點(表頭常在偵測到的表框上方):無座標候選 / 候選不在表框 / 候選結構沒過 / VRN 再驗沒過(主因)/ 矩陣待審
  ③ 文字幾何表不送雙讀(兩輪 9 + 8 = 17 張 0 過 · 每張約 2 秒)
  ④ 沒跑 OCR:不探測工具(子程序每環境最多等 90 秒)· 不發安裝請求;探測失敗 ≠ 沒安裝(不發請求)
  ⑤ 引擎稽核頁補擷取後復健一列(包 engines_audit_v158 —— v0158 主程式直接呼叫它)
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

import hashlib
import importlib.util
import json
import os
import re
import sys
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0169"


def _vnum_v0169(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0169(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0169(p) < _vnum_v0169(__file__)), key=_vnum_v0169)
PRIOR = _load_v0169(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


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


_P168 = PRIOR if "verify_table_v168" in vars(PRIOR) else _owner("verify_table_v168")
_ORIG_VT = vars(_P168)["_PREV_VT"]            # v0168 之前的 VRN 原驗表
_PE_LOG = vars(_P168)["_PE_LOG"]
_pe, _PE = vars(_P168)["_pe"], vars(_P168)["_PE"]
_rows_from_pt = vars(_P168)["_rows_from_period_table"]
_LAST = {"skip_tr": False}
_SKIP_TR = []


def _area(b) -> float:
    return max((b[2] - b[0]) * (b[3] - b[1]), 1e-6)


def _inter(a, b) -> float:
    return max(0.0, min(a[2], b[2]) - max(a[0], b[0])) * max(0.0, min(a[3], b[3]) - max(a[1], b[1]))


# ───────── ② 復健(取字範圍往上 42 點 · 每關記原因)─────────
def pe_try_v169(m, b: dict, page) -> dict:
    bbox = [float(b["x0"]), float(b["top"]), float(b["x1"]), float(b["bottom"])]
    W, H = float(page.width), float(page.height)
    win = [max(0.0, bbox[0] - 6), max(0.0, bbox[1] - 42), min(W, bbox[2] + 6), min(H, bbox[3] + 6)]
    words = []
    try:
        for w in page.crop(win).extract_words():
            words.append({"text": w["text"], "bbox": [float(w["x0"]), float(w["top"]), float(w["x1"]), float(w["bottom"])]})
    except Exception:  # noqa: BLE001
        pass
    data = {"extractor": "pdfplumber", "coordinate_space": "pdf_points", "pages": [{"number": int(b.get("page") or 1), "width": W, "height": H, "words": words, "tables": [{"rows": b.get("rows") or [], "bbox": bbox}]}]}
    res = getattr(m, _PE["ast"]["interface"]["entry"])(data, extractor="pdfplumber", source_id=str(b.get("id") or "vrn"))
    pg = (res.get("pages") or [{}])[0]
    mat = (pg.get("repaired_tables") or [{}])[0]
    codes = [(i.get("code"), i.get("status")) for i in mat.get("issues", [])]
    rows0 = b.get("rows") or [[""]]
    label0 = rows0[0][0] if rows0 and rows0[0] and not re.search(r"\d", rows0[0][0] or "") else ""
    geo_all = [t for t in pg.get("period_tables") or [] if "geometry" in str(t.get("region_origin", "")) and t.get("bbox")]
    geo_in = [t for t in geo_all if _inter(t["bbox"], bbox) / min(_area(t["bbox"]), _area(bbox)) >= 0.6 and len(t.get("headers") or []) >= 2 and len(t.get("rows") or []) >= 2]
    geo_ok = [t for t in geo_in if all(c.get("status") == "PASS" for c in t.get("structure_checks", []))]
    cands = [("依字詞座標重建", _rows_from_pt(t, label0)) for t in sorted(geo_ok, key=lambda t: -_inter(t["bbox"], bbox))]
    if mat.get("rows") and not any(s == "REVIEW" for _, s in codes) and mat["rows"] != rows0:
        cands.append(("矩陣修復", mat["rows"]))
    stage = "無座標候選" if not geo_all else ("座標候選不在表框或不足 2 期 2 列" if not geo_in else ("座標候選結構檢查沒過" if not geo_ok else ""))
    cells = [c for r in (mat.get("parsed_cells") or []) for c in r if (c.get("raw_text") or "").strip()]
    num = sum(1 for c in cells if c.get("status") == "numeric")
    lt = [len(c.get("raw_text") or "") for c in cells if c.get("status") != "numeric"]
    text_like = any(c == "F23" for c, _ in codes) or (len(cells) >= 2 and num / max(len(cells), 1) < 0.15 and lt and sum(lt) / len(lt) >= 12 and not geo_ok)
    return {"cands": cands, "codes": codes, "stage": stage, "text_like": text_like, "version": _PE["ast"]["version"], "words": len(words)}


def _to_text(b: dict, page) -> bool:
    """改回正文:沿用 v0155 的 _lines() 產生完整逐行資料(size · bold · font);產生不出來 → 不改。"""
    lf = _resolve("_lines")
    try:
        lines = lf(page.crop((b["x0"], b["top"], b["x1"], b["bottom"]))) if lf else []
    except Exception:  # noqa: BLE001
        lines = []
    lines = [l for l in lines if (l.get("text") or "").strip() and "size" in l]
    if not lines:
        return False
    txt = ""
    for i, l in enumerate(lines):
        if i and not (re.search(r"[\u4e00-\u9fff]$", lines[i - 1]["text"]) and re.match(r"[\u4e00-\u9fff]", l["text"])):
            txt += " "
        txt += l["text"]
    b["rows_pe_text"] = b.get("rows")
    b.update(kind="text", sub="正文(表格誤判 → PostExtract 分離)", lines=lines, text=txt, size=max(float(l["size"]) for l in lines),
             bold=sum(1 for l in lines if l.get("bold")) * 2 >= len(lines), role=b.get("role") or "BODY")
    return True


def verify_table_v169(b: dict, page=None) -> dict:
    v = _ORIG_VT(b, page)
    _LAST["skip_tr"] = bool(not v.get("ok") and b.get("how") == "text-geometry")
    if _LAST["skip_tr"]:
        _SKIP_TR.append(b.get("id"))
    if v.get("ok") or v.get("tiny") or page is None or os.environ.get("VIA_VRN_POSTEXTRACT_OFF") == "1":
        return v
    sig = hashlib.md5(json.dumps(b.get("rows") or [], ensure_ascii=False).encode("utf-8")).hexdigest()
    if b.get("_pe_sig") == sig:
        return v
    b["_pe_sig"] = sig
    m = _pe()
    if m is None:
        return v
    t0 = time.time()
    try:
        res = pe_try_v169(m, b, page)
    except Exception as exc:  # noqa: BLE001
        _PE_LOG.append({"id": b.get("id"), "status": "錯誤", "why": "引擎例外 %s" % type(exc).__name__, "ms": int((time.time() - t0) * 1000)})
        return v
    why2 = []
    for how, rows in res["cands"]:
        v2 = _ORIG_VT(dict(b, rows=rows), page)
        if v2.get("ok"):
            b["raw_rows_pe"], b["rows"] = b.get("rows"), rows
            b["engine"] = "PostExtract v%s(%s)" % (res["version"], how)
            v2["native"] = "擷取後復健 PostExtract v%s · %s" % (res["version"], how)
            b["pe"] = {"status": "修好", "how": how}
            _PE_LOG.append({"id": b.get("id"), "status": "修好", "how": how, "ms": int((time.time() - t0) * 1000)})
            return v2
        why2.append("%s → VRN 再驗沒過:%s" % (how, (v2.get("issues") or ["?"])[0].split(" ")[0]))
    sub0 = b.get("sub", "")
    if res["text_like"] and not str(sub0).startswith(("財務表", "估值表")) and _to_text(b, page):
        b["pe"] = {"status": "改回正文"}
        _PE_LOG.append({"id": b.get("id"), "status": "改回正文", "ms": int((time.time() - t0) * 1000)})
        return {"ok": True, "header": False, "rect": True, "parse_rate": 1.0, "multi_left": 0, "text_cov": None, "arith": "不適用", "issues": [], "unit": "",
                "rule": "文字/表格分離:逐格判讀幾乎都是長句 → 改回正文(表框內逐行完整文字)", "as_text": True}
    why = why2[0] if why2 else (res["stage"] or "只有矩陣候選")
    if any(s == "REVIEW" for _, s in res["codes"]) and not why2:
        why += " · 矩陣待審 " + ",".join(sorted({c for c, s in res["codes"] if s == "REVIEW"}))
    b["pe"] = {"status": "未過", "why": why}
    _PE_LOG.append({"id": b.get("id"), "status": "未過", "why": why, "codes": [c for c, s in res["codes"] if s == "REVIEW"], "ms": int((time.time() - t0) * 1000)})
    v["pe"] = "復健未過:" + why
    return v


_mv = _owner("verify_table")
if _mv:
    setattr(_mv, "verify_table", verify_table_v169)

# ───────── ③ 文字幾何表不送雙讀 ─────────
_PREV_TR = _resolve("tr_check_v160")


def tr_check_v169(*a, **k):
    if _LAST.get("skip_tr"):
        _LAST["skip_tr"] = False
        return None
    return _PREV_TR(*a, **k) if _PREV_TR else None


_mtr = _owner("tr_check_v160")
if _mtr:
    setattr(_mtr, "tr_check_v160", tr_check_v169)

_PREV_L2 = _resolve("l2_one")


def l2_one_v169(row: dict) -> dict:
    del _SKIP_TR[:]
    r = _PREV_L2(row)
    if isinstance(r, dict):
        skip = set(_SKIP_TR)
        for t in r.get("tools", []) or []:
            if t.get("table") in skip and "→ 雙讀(TableRepair)" in t.get("tool", ""):
                t["tool"] = t["tool"].replace("→ 雙讀(TableRepair)", "→ 雙讀略過(文字幾何表)")
        log = list(_PE_LOG)
        if log:
            pe = r.setdefault("pe", {})
            pe["why"] = dict(Counter(re.sub(r"\s·\s矩陣待審.*$", "", e.get("why", "")) for e in log if e["status"] == "未過"))
            pe["tr_skipped"] = len(skip)
    return r


_ml2 = _owner("l2_one")
if _ml2:
    setattr(_ml2, "l2_one", l2_one_v169)

_PREV_LR = _resolve("layout_run_v158")


def layout_run_v169(d, opts):
    o = _PREV_LR(d, opts)
    try:
        why, skip = Counter(), 0
        for r in o.get("rows", []) or []:
            why.update((r.get("pe") or {}).get("why", {}))
            skip += (r.get("pe") or {}).get("tr_skipped", 0)
        if why:
            print("[計] 復健沒過在哪一關 · " + " · ".join("%s×%d" % kv for kv in why.most_common(6)))
        print("[計] 文字幾何表雙讀略過 %d 張(兩輪實測 17 張 0 過 · 每張約 2 秒)" % skip)
        if os.environ.get("VIA_VRN_NO_OCR") == "1":
            print("[計] OCR 本輪沒跑 · 候選區 %d 留給 --ocr · 工具探測略過 · 不發安裝請求" % len(o.get("regions") or []))
    except Exception as exc:  # noqa: BLE001
        print("[計] 復健原因統計失敗 · %s" % type(exc).__name__)
    return o


_mlr = _owner("layout_run_v158")
if _mlr:
    setattr(_mlr, "layout_run_v158", layout_run_v169)

# ───────── ④ 沒跑 OCR 不探測 · 探測失敗 ≠ 沒安裝 ─────────
_PREV_PROBE = _resolve("ocr_probe")
_PREV_REQ = _resolve("tool_request")


def ocr_probe_v169(*a, **k):
    if os.environ.get("VIA_VRN_NO_OCR") == "1":
        return {"runtimes": [], "avail": {}, "skipped": True}
    return _PREV_PROBE(*a, **k)


def tool_request_v169(probe=None, *a, **k):
    """主程式讀 req["need"] / req["file"] → 一律回這個形狀(v0165 收尾隔離的安全預設 {} 也會在這裡補齊)。"""
    if isinstance(probe, dict) and (probe.get("skipped") or any(rt.get("err") for rt in probe.get("runtimes", []) or [])):
        need = []
        if a and not a[0]:          # TableRepair 不在(缺 pymupdf)跟 OCR 無關 → 照常請求
            need.append({"pip": "pymupdf", "for": "第二步 TableRepair 雙讀(表格還原修正)", "python": sys.executable})
        return {"need": need, "file": "", "note": "OCR 工具探測略過或失敗 → 不發 OCR 安裝請求(探測失敗 ≠ 沒安裝)"}
    r = _PREV_REQ(probe, *a, **k) if _PREV_REQ else None
    if not isinstance(r, dict) or "need" not in r:
        r = {"need": [], "file": "", "note": "安裝請求步驟失敗 → 空清單"}
    r.setdefault("file", "")
    return r


for _nm, _fn in (("ocr_probe", ocr_probe_v169), ("tool_request", tool_request_v169)):
    _mo = _owner(_nm)
    if _mo:
        setattr(_mo, _nm, _fn)

# ───────── ⑤ 引擎稽核頁補擷取後復健一列(包 engines_audit_v158)─────────
_PREV_EA = _resolve("engines_audit_v158")
_FAM = "VRN_Generic_PostExtract_Engine"


def engines_audit_v169(*a, **k):
    o = _PREV_EA(*a, **k)
    try:
        fs = [p for p in vars(_P168)["pe_files"]() if p.parent.name == "VRN_PostExtract"]
        if fs and not any(r.get("family") == _FAM for r in o.get("rows", [])):
            tail = max(fs, key=_vnum_v0169)
            proto = next((r for r in o["rows"] if "雙讀" in str(r.get("pipeline", ""))), None) or (o["rows"][0] if o.get("rows") else {})
            row = dict(proto)
            home = _resolve("_home")()
            row.update(family=_FAM, ext=".py", tail=str(tail.relative_to(home)) if str(tail).startswith(str(home)) else str(tail), n=len(fs), version=True,
                       registered=bool(k.get("register") or (a[0] if a else False)), accel="[VIA:ACCEL-BRIDGE" in tail.read_text(encoding="utf-8", errors="replace"),
                       pipeline="第二步擷取後復健(PostExtract · 文字/表格分離)", sha8=hashlib.sha256(tail.read_bytes()).hexdigest()[:8])
            o["rows"].append(row)
    except Exception:  # noqa: BLE001
        pass
    return o


_mea = _owner("engines_audit_v158")
if _mea:
    setattr(_mea, "engines_audit_v158", engines_audit_v169)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()
    if args[:1] == ["layout"] and "--ocr" not in args:
        os.environ["VIA_VRN_NO_OCR"] = "1"
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
    td = Path(tempfile.mkdtemp(prefix="vrn169-"))
    try:
        from reportlab.pdfgen import canvas
        import pdfplumber
        pdfp = td / "t.pdf"
        c = canvas.Canvas(str(pdfp), pagesize=(595, 842))
        Y = lambda y: 842 - y - 9  # noqa: E731
        c.setFont("Helvetica", 9)
        c.drawString(60, Y(100), "The company expects demand to keep growing next year")
        c.drawString(320, Y(100), "management guided margins higher in 2H")
        c.drawString(60, Y(115), "driven by AI server shipments and new customers")
        c.drawString(320, Y(115), "while pricing remains stable for now")
        c.showPage()
        c.setFont("Helvetica", 9)
        for t, x in (("NT$m", 60), ("2024A", 200), ("2025F", 300), ("2026F", 400)):
            c.drawString(x, Y(100), t)
        for y, lab, vals in ((120, "Revenue", ("1,234", "5,678", "6,789")), (140, "Operating profit", ("(83)", "120", "150")), (160, "EPS", ("2.31", "3.10", "3.85"))):
            c.drawString(60, Y(y), lab)
            for x, v in zip((200, 300, 400), vals):
                c.drawString(x, Y(y), v)
        c.showPage()
        c.save()
        with pdfplumber.open(str(pdfp)) as pdf:
            bt = {"id": "P1·F·01·T1", "kind": "table", "sub": "資訊表", "role": "BODY", "page": 1, "x0": 55.0, "top": 95.0, "x1": 560.0, "bottom": 130.0,
                  "rows": [["The company expects demand to keep growing", "management guided margins higher in 2H"], ["driven by AI server shipments", "while pricing remains stable for now"]]}
            vt = verify_table_v169(bt, pdf.pages[0])
            ok1 = vt.get("as_text") and bt["kind"] == "text" and bt.get("lines") and all("size" in l and "bold" in l for l in bt["lines"])
            try:
                [round(l["size"] * 2) / 2 for l in bt["lines"]]
                "%s|%s" % (round(bt["size"] * 2) / 2, bt["bold"])
                ok1b = "next year" in bt["text"] and "for now" in bt["text"]
            except Exception:  # noqa: BLE001
                ok1b = False
            chk("① 改回正文的區塊有完整逐行資料(lines · size · bold · font)· 下游字級階層運算不再 KeyError:'size' · 文字一字不丟", bool(ok1 and ok1b))
            del _PE_LOG[:]
            bh = {"id": "P2·F·01·T1", "kind": "table", "sub": "財務表(損益)", "role": "BODY", "page": 2, "x0": 55.0, "top": 115.0, "x1": 460.0, "bottom": 175.0,
                  "rows": [["Revenue", "1,234 5,678", "6,789"], ["Operating profit", "(83) 120", "150"], ["EPS", "2.31 3.10", "3.85"]]}
            v0 = _ORIG_VT(dict(bh), pdf.pages[1])
            vh = verify_table_v169(bh, pdf.pages[1])
            chk("② 表頭在偵測到的表框上方(框只含資料列)→ 取字範圍往上 42 點找到 2024A/2025F/2026F → 依座標重建 → VRN 再驗過(原驗:%s)" % ",".join((v0.get("issues") or [])[:2]),
                not v0["ok"] and vh["ok"] and bh["rows"][0][1:] == ["2024A", "2025F", "2026F"] and bh["rows"][1] == ["Revenue", "1,234", "5,678", "6,789"] and _PE_LOG[-1]["status"] == "修好")
            bn = {"id": "P2·F·09·T9", "kind": "table", "sub": "財務表(損益)", "role": "BODY", "page": 2, "x0": 450.0, "top": 300.0, "x1": 590.0, "bottom": 360.0, "rows": [["a", "1 2"], ["b", "3 4"]]}
            verify_table_v169(bn, pdf.pages[1])
            chk("③ 復健沒過會記在哪一關(這張:%s)" % _PE_LOG[-1].get("why"), _PE_LOG[-1]["status"] == "未過" and _PE_LOG[-1].get("why", "").startswith(("無座標候選", "座標候選", "只有矩陣", "依字詞", "矩陣修復")))
        calls = []
        global _PREV_TR
        keep = _PREV_TR
        _PREV_TR = lambda *a, **k: calls.append(1) or {"status": "PASS"}  # noqa: E731
        try:
            _LAST["skip_tr"] = True
            r1 = tr_check_v169(1, 2)
            r2 = tr_check_v169(1, 2)
        finally:
            _PREV_TR = keep
        bg = {"id": "HT", "kind": "table", "how": "text-geometry", "sub": "財務表", "rows": [["", "2024", "2025"], ["a", "1 2", "3"], ["b", "4", "5"]], "x0": 0, "top": 0, "x1": 1, "bottom": 1}
        verify_table_v169(bg, None)          # 資料列有黏住數字 → 沒過 → 文字幾何表 → 記略過
        chk("④ 文字幾何表沒過 → 雙讀略過(回 None,第二步拿到空結果照常走);下一張一般表照常雙讀", r1 is None and r2 == {"status": "PASS"} and len(calls) == 1 and "HT" in _SKIP_TR)
        saved = os.environ.get("VIA_VRN_NO_OCR")
        os.environ["VIA_VRN_NO_OCR"] = "1"
        try:
            pr = ocr_probe_v169()
            rq = tool_request_v169(pr, True)
        finally:
            if saved is None:
                os.environ.pop("VIA_VRN_NO_OCR", None)
            else:
                os.environ["VIA_VRN_NO_OCR"] = saved
        rq2 = tool_request_v169({"runtimes": [{"python": "x", "engines": {}, "err": "TimeoutExpired"}], "avail": {}}, True)
        rq3 = tool_request_v169(pr, False)
        chk("⑤ 沒跑 OCR → 不探測(不開子程序等 90 秒)· 不發 OCR 安裝請求;探測失敗(逾時)≠ 沒安裝 → 也不發;回傳形狀 need/file 不變(主程式讀 req[\"need\"])· TableRepair 缺 pymupdf 照常請求",
            pr.get("skipped") and rq["need"] == [] and "file" in rq and rq2["need"] == [] and [n["pip"] for n in rq3["need"]] == ["pymupdf"])
        global _PREV_EA
        keep2 = _PREV_EA
        _PREV_EA = lambda *a, **k: {"rows": [{"family": "VRN_TableGeometry", "pipeline": "第二步表格還原修正(雙讀)", "tail": "x", "version": True, "registered": False, "accel": True}]}  # noqa: E731
        try:
            ea = engines_audit_v169(False)
        finally:
            _PREV_EA = keep2
        pe_row = next((r for r in ea["rows"] if r.get("family") == _FAM), None)
        chk("⑥ 引擎稽核頁補擷取後復健一列(包對函式 engines_audit_v158)· 管線用途 · 正本橋", (pe_row is not None and "擷取後復健" in pe_row["pipeline"] and pe_row["accel"]) or not vars(_P168)["pe_files"]())
    finally:
        shutil.rmtree(td, ignore_errors=True)
    me = Path(__file__).read_text(encoding="utf-8")
    chk("⑦ 正本加速器橋 · 自帶多程序墊片", "import VeritasCeleritas_v1141" in me and _job_entry.__module__ in ("__main__", __name__))
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("⑧ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    print("[計] VRN_SystemManager_v0169 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
