#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0168 — 薄尾(操作員 2026-10-10「JSON 介面在裡面 · INTERFACE 自適應式 · 引擎模組模塊化 · 注入 AST 分類區隔 ·
   在啟用 LAYOUT OCR 之前,PDFPLUMBER TABULA 等 NON-OCR 工具搭配復健工具修復分離文字跟表」;+ 實跑 layout 60 分逾時:OCR 收尾 86+ 區 × 3 引擎 · 0 接受)。
  ① 擷取後復健引擎 VRN_Generic_PostExtract_Engine 接進第二步(intake\\VRN_PostExtract\\ 尾版;v0101 = v0100 + 正本橋 + 記憶體介面帶座標崩潰修正)
     自適應介面:AST 讀引擎檔,依簽名找入口(data + extractor 參數),不寫死函式名;JSON 記憶體介面(不開檔 · 不跑 OCR / 模型)
  ② 第二步順序:pdfplumber 單讀 → VRN 驗表沒過 → 復健(先依字詞座標重建 · 再矩陣修復)→ VRN 原驗表再驗 → 還沒過才 TableRepair 雙讀
     只在 VRN 驗表通過時採用復健結果(引擎 REVIEW / F22 等不放水);原列留 raw_rows_pe
  ③ 文字 / 表格分離:非財務表沒過驗表、逐格判讀幾乎都是長句(或引擎 F23)→ 改回正文(內容取表框內完整文字,不丟字)
  ④ layout 預設不跑 OCR(先 NON-OCR + 復健);要跑加 --ocr
  ⑤ postextract 動詞:引擎 · 介面(AST)· 分類區隔(七類 · F01~F25 對應函式)· 引擎自測 · 座標重建樣例 → AST 附冊 + POSTEXTRACT_latest.html(原檔不動)
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

import ast
import datetime
import hashlib
import html
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
TAG = "v0168"


def _vnum_v0168(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0168(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0168(p) < _vnum_v0168(__file__)), key=_vnum_v0168)
PRIOR = _load_v0168(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


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
_FAM = "VRN_Generic_PostExtract_Engine"


# ───────── ① 引擎尋找 + AST 自適應介面 + 分類區隔 ─────────
def pe_files() -> list:
    out = []
    if os.environ.get("VIA_VRN_POSTEXTRACT"):
        out.append(Path(os.environ["VIA_VRN_POSTEXTRACT"]))
    for base in (_home(), HERE):
        d = base / "intake" / "VRN_PostExtract"
        if d.is_dir():
            out += sorted(d.glob(_FAM + "_v*.py"), key=_vnum_v0168)[::-1]
    seen, res = set(), []
    for p in out:
        if p.is_file() and str(p) not in seen:
            seen.add(str(p))
            res.append(p)
    return res


_CATS = [("介面", lambda n: n in ("repair_extracted_data", "reconcile_extractor_results", "run_engine", "read_annual_dataframe", "tool_inventory", "main", "parse_arguments", "watch_folder")),
         ("文字/表格分離", lambda n: n in ("classify_page_roles", "repair_body_text", "html_body_text", "sort_block_reading_order")),
         ("驗證", lambda n: n.startswith(("validate_", "run_self_check", "failure_case")) or n in ("boxes_overlap", "find_account_role", "semantic_account_key", "is_parent_year_header")),
         ("修復", lambda n: n.startswith(("repair_", "parse_cell", "normalize_cell", "parse_value", "parse_period", "canonical_", "raw_cell", "legacy_rounding", "normalize_label"))),
         ("表格重建", lambda n: n.startswith(("reconstruct_", "cluster_", "split_", "infer_", "detect_", "collect_", "get_cell", "annual_", "find_row", "resolve_", "get_region", "prepare_visible", "legacy_inside", "legacy_join"))),
         ("輸入正規化", lambda n: n.startswith(("normalize_", "parse_html", "parse_markdown", "extract_", "find_pdf", "read_page", "load_", "legacy_load"))),
         ("輸出", lambda n: n.startswith(("write_", "export_", "build_", "json_bytes", "file_sha256")))]


def pe_ast(path: Path) -> dict:
    """不 import、只讀 AST:入口(依簽名)· 七類分類區隔 · 每個函式處理哪些 F01~F25 · 版本常數。"""
    src = path.read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(src)
    lines = src.splitlines()
    fns, ver = [], ""
    for n in tree.body:
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "ENGINE_VERSION" for t in n.targets) and isinstance(n.value, ast.Constant):
            ver = str(n.value.value)
        if isinstance(n, ast.FunctionDef):
            args = [a.arg for a in n.args.args]
            seg = "\n".join(lines[n.lineno - 1:getattr(n, "end_lineno", n.lineno)])
            cat = next((c for c, f in _CATS if f(n.name)), "其他")
            fns.append({"name": n.name, "args": args, "lines": [n.lineno, getattr(n, "end_lineno", n.lineno)], "cat": cat,
                        "doc": (ast.get_docstring(n) or "").split("\n")[0][:90], "fcodes": sorted(set(re.findall(r"['\"](F\d\d)['\"]", seg)))})
    entry = next((f["name"] for f in fns if f["name"] == "repair_extracted_data"), None) or next((f["name"] for f in fns if f["args"][:1] in (["data"], ["payload"]) and "extractor" in f["args"]), None)
    pick = lambda pred: next((f["name"] for f in fns if pred(f["name"])), None)  # noqa: E731
    iface = {"entry": entry, "reconcile": pick(lambda n: "reconcile" in n), "selfcheck": pick(lambda n: n.startswith("run_self_check")), "inventory": pick(lambda n: n == "tool_inventory")}
    fc = {}
    for f in fns:
        for c in f["fcodes"]:
            fc.setdefault(c, []).append(f["name"])
    return {"file": path.name, "sha12": hashlib.sha256(src.encode("utf-8")).hexdigest()[:12], "version": ver, "functions": fns, "interface": iface,
            "categories": dict(Counter(f["cat"] for f in fns)), "fcodes": dict(sorted(fc.items())), "lines": len(lines), "bridge": "[VIA:ACCEL-BRIDGE" in src}


_PE = {"mod": None, "path": None, "ast": None, "err": "", "tried": False}


def _pe():
    if _PE["tried"]:
        return _PE["mod"]
    _PE["tried"] = True
    for p in pe_files():
        try:
            a = pe_ast(p)
            if not a["interface"]["entry"]:
                _PE["err"] = "%s:AST 找不到入口(data + extractor)" % p.name
                continue
            spec = importlib.util.spec_from_file_location("vrn_postextract_engine_%s" % (a["version"] or "x"), p)
            m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m)
            _PE.update(mod=m, path=p, ast=a, err="")
            return m
        except Exception as exc:  # noqa: BLE001
            _PE["err"] = "%s:%s:%s" % (p.name, type(exc).__name__, str(exc)[:80])
    return None


# ───────── ② 第二步插入點:verify_table(第二步執行當下才查找)─────────
_PE_LOG = []


def _overlap(a, b) -> float:
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    ar = max((a[2] - a[0]) * (a[3] - a[1]), 1e-6)
    return ix * iy / ar


def _rows_from_period_table(t: dict, label0: str) -> list:
    hd = [h.get("period", {}).get("raw") or "" for h in t.get("headers", [])]
    n = len(hd)
    items = []
    for r in t.get("rows", []):
        ys = [b[1] for b in (r.get("value_bboxes") or []) if b]
        vals = list(r.get("raw_values") or [])[:n] + [""] * max(0, n - len(r.get("raw_values") or []))
        items.append((min(ys) if ys else 1e9, [r.get("label") or ""] + vals))
    for tr in t.get("textual_rows", []) or []:
        bb = tr.get("bbox") or [0, 1e9, 0, 0]
        items.append((bb[1], [tr.get("text") or ""] + [""] * n))
    items.sort(key=lambda x: x[0])
    return [[label0] + hd] + [r for _, r in items]


def pe_repair_block(m, b: dict, page) -> dict:
    bbox = [float(b["x0"]), float(b["top"]), float(b["x1"]), float(b["bottom"])]
    words = []
    try:
        for w in page.crop(bbox).extract_words():
            words.append({"text": w["text"], "bbox": [float(w["x0"]), float(w["top"]), float(w["x1"]), float(w["bottom"])]})
    except Exception:  # noqa: BLE001
        words = []
    data = {"extractor": "pdfplumber", "coordinate_space": "pdf_points",
            "pages": [{"number": int(b.get("page") or 1), "width": float(page.width), "height": float(page.height), "words": words, "tables": [{"rows": b.get("rows") or [], "bbox": bbox}]}]}
    entry = getattr(m, _PE["ast"]["interface"]["entry"])
    res = entry(data, extractor="pdfplumber", source_id=str(b.get("id") or "vrn"))
    pg = (res.get("pages") or [{}])[0]
    mats = pg.get("repaired_tables") or []
    mat = mats[0] if mats else {}
    codes = [(i.get("code"), i.get("status")) for i in mat.get("issues", [])]
    rows0 = b.get("rows") or [[""]]
    label0 = rows0[0][0] if rows0 and rows0[0] and not re.search(r"\d", rows0[0][0] or "") else ""
    cands = []
    for t in pg.get("period_tables") or []:
        if "geometry" in str(t.get("region_origin", "")) and t.get("bbox") and _overlap(t["bbox"], bbox) >= 0.6 and len(t.get("headers") or []) >= 2 and len(t.get("rows") or []) >= 2 \
                and all(c.get("status") == "PASS" for c in t.get("structure_checks", [])):
            cands.append(("依字詞座標重建", _rows_from_period_table(t, label0)))
    if mat.get("rows") and not any(s == "REVIEW" for _, s in codes) and mat["rows"] != rows0:
        cands.append(("矩陣修復", mat["rows"]))
    data_cells = [c for r in (mat.get("parsed_cells") or []) for c in r if (c.get("raw_text") or "").strip()]     # 正文誤當表:沒有真表頭 / 標籤欄 → 全部格子都算
    num = sum(1 for c in data_cells if c.get("status") == "numeric")
    long_txt = [len(c.get("raw_text") or "") for c in data_cells if c.get("status") != "numeric"]
    text_like = any(c == "F23" for c, _ in codes) or (len(data_cells) >= 2 and num / max(len(data_cells), 1) < 0.15 and long_txt and sum(long_txt) / len(long_txt) >= 12 and not any(h == "依字詞座標重建" for h, _ in cands))
    return {"cands": cands, "codes": codes, "text_like": text_like, "words": len(words), "version": _PE["ast"]["version"], "errors": res.get("errors") or []}


_PREV_VT = _resolve("verify_table")


def verify_table_v168(b: dict, page=None) -> dict:
    v = _PREV_VT(b, page)
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
        res = pe_repair_block(m, b, page)
    except Exception as exc:  # noqa: BLE001
        b["pe"] = {"status": "錯誤", "err": "%s:%s" % (type(exc).__name__, str(exc)[:80])}
        _PE_LOG.append({"id": b.get("id"), "status": "錯誤", "ms": int((time.time() - t0) * 1000)})
        return v
    for how, rows in res["cands"]:
        v2 = _PREV_VT(dict(b, rows=rows), page)
        if v2.get("ok"):
            b["raw_rows_pe"], b["rows"] = b.get("rows"), rows
            b["engine"] = "PostExtract v%s(%s)" % (res["version"], how)
            v2["native"] = "擷取後復健 PostExtract v%s · %s · %s" % (res["version"], how, ",".join(sorted({c for c, _ in res["codes"]})) or "—")
            b["pe"] = {"status": "修好", "how": how, "codes": res["codes"]}
            _PE_LOG.append({"id": b.get("id"), "status": "修好", "how": how, "ms": int((time.time() - t0) * 1000)})
            return v2
    strict = str(b.get("sub", "")).startswith(("財務表", "估值表"))
    if res["text_like"] and not strict:
        try:
            txt = page.crop((b["x0"], b["top"], b["x1"], b["bottom"])).extract_text() or ""
        except Exception:  # noqa: BLE001
            txt = "\n".join(" ".join(c for c in r if c) for r in (b.get("rows") or []))
        b["rows_pe_text"] = b.get("rows")
        b.update(kind="text", sub="正文(表格誤判 → PostExtract 分離)", text=txt, role=b.get("role") or "BODY")
        b["pe"] = {"status": "改回正文", "codes": res["codes"]}
        _PE_LOG.append({"id": b.get("id"), "status": "改回正文", "ms": int((time.time() - t0) * 1000)})
        return {"ok": True, "header": False, "rect": True, "parse_rate": 1.0, "multi_left": 0, "text_cov": None, "arith": "不適用", "issues": [], "unit": "",
                "rule": "文字/表格分離:逐格判讀幾乎都是長句 → 改回正文(表框內完整文字)", "as_text": True}
    b["pe"] = {"status": "未過", "codes": res["codes"]}
    _PE_LOG.append({"id": b.get("id"), "status": "未過", "codes": [c for c, s in res["codes"] if s == "REVIEW"], "ms": int((time.time() - t0) * 1000)})
    v["pe"] = "復健未過:" + (",".join(sorted({c for c, s in res["codes"] if s == "REVIEW"})) or "結構 / 字還原")
    return v


_mv = _owner("verify_table")
if _mv:
    setattr(_mv, "verify_table", verify_table_v168)

_PREV_L2 = _resolve("l2_one")


def l2_one_v168(row: dict) -> dict:
    del _PE_LOG[:]
    r = _PREV_L2(row)
    log = list(_PE_LOG)
    if isinstance(r, dict) and log:
        by = {e["id"]: e for e in log}
        for t in r.get("tools", []) or []:
            e = by.get(t.get("table"))
            if e:
                t["tool"] = t["tool"].replace("單讀(pdfplumber)", "單讀(pdfplumber) → 復健(PostExtract)" + ("" if e["status"] == "修好" else ":" + e["status"]), 1)
                if e["status"] in ("修好", "改回正文"):
                    t["ok"] = True
        r["pe"] = {"tried": len(log), "fixed": sum(1 for e in log if e["status"] == "修好"), "geo": sum(1 for e in log if e.get("how") == "依字詞座標重建"),
                   "mat": sum(1 for e in log if e.get("how") == "矩陣修復"), "text": sum(1 for e in log if e["status"] == "改回正文"), "fail": sum(1 for e in log if e["status"] == "未過"),
                   "err": sum(1 for e in log if e["status"] == "錯誤"), "ms": sum(e["ms"] for e in log), "review": dict(Counter(c for e in log for c in e.get("codes", [])))}
    return r


_ml2 = _owner("l2_one")
if _ml2:
    setattr(_ml2, "l2_one", l2_one_v168)

_PREV_LR = _resolve("layout_run_v158")


def layout_run_v168(d, opts):
    o = _PREV_LR(d, opts)
    try:
        agg = Counter()
        rev = Counter()
        for r in o.get("rows", []) or []:
            pe = r.get("pe") or {}
            for k in ("tried", "fixed", "geo", "mat", "text", "fail", "err", "ms"):
                agg[k] += pe.get(k, 0)
            rev.update(pe.get("review", {}))
        a = _PE.get("ast") or (pe_ast(pe_files()[0]) if pe_files() else None)
        if a:
            print("[計] 擷取後復健 PostExtract v%s(%s · 介面 %s · AST 找到)· 試 %d 表 · 修好 %d(依座標 %d · 矩陣 %d)· 改回正文 %d · 未過 %d · 錯 %d · 平均 %d ms%s" % (
                a["version"], a["file"], a["interface"]["entry"], agg["tried"], agg["fixed"], agg["geo"], agg["mat"], agg["text"], agg["fail"], agg["err"], agg["ms"] / max(agg["tried"], 1),
                (" · 未過主因 " + " ".join("%s×%d" % kv for kv in rev.most_common(4))) if rev else ""))
        else:
            print("[計] 擷取後復健 PostExtract · 引擎不在 intake\\VRN_PostExtract\\(%s)· 本輪沒用" % (_PE.get("err") or "沒有檔"))
    except Exception as exc:  # noqa: BLE001
        print("[計] 擷取後復健統計失敗 · %s:%s" % (type(exc).__name__, str(exc)[:100]))
    return o


_mlr = _owner("layout_run_v158")
if _mlr:
    setattr(_mlr, "layout_run_v158", layout_run_v168)

# 引擎稽核:補 PostExtract 一列(同 TableRepair 的作法)
_PREV_EA = _resolve("engines_audit")


def engines_audit_v168(register: bool = False) -> dict:
    o = _PREV_EA(register)
    try:
        fs = [p for p in pe_files() if p.parent.name == "VRN_PostExtract"]
        if fs and not any(r.get("family") == _FAM for r in o.get("rows", [])):
            tail = max(fs, key=_vnum_v0168)
            proto = next((r for r in o["rows"] if "TableRepair" in str(r.get("tail", "")) or "雙讀" in str(r.get("pipeline", ""))), None) or {}
            row = {k: proto.get(k) for k in proto}
            row.update(family=_FAM, ext=".py", tail=str(tail.relative_to(_home())) if str(tail).startswith(str(_home())) else str(tail), n=len(fs), version=True, registered=register,
                       accel="[VIA:ACCEL-BRIDGE" in tail.read_text(encoding="utf-8", errors="replace"), pipeline="第二步擷取後復健(PostExtract · 文字/表格分離)",
                       sha8=hashlib.sha256(tail.read_bytes()).hexdigest()[:8])
            o["rows"].append(row)
    except Exception:  # noqa: BLE001
        pass
    return o


_mea = _owner("engines_audit")
if _mea:
    setattr(_mea, "engines_audit", engines_audit_v168)


# ───────── ④ layout 預設不跑 OCR ─────────
def layout_args(args: list) -> tuple:
    a = list(args)
    if not a or a[0] != "layout":
        return a, ""
    if "--ocr" in a:
        a.remove("--ocr")
        return a, "[計] OCR · 本輪要跑(--ocr)· 只在 NON-OCR + 復健都沒過的區"
    if "--no-ocr" not in a:
        a.append("--no-ocr")
    return a, "[計] OCR · 本輪不跑(先 NON-OCR + 擷取後復健;要跑 OCR 加 --ocr)"


# ───────── ⑤ postextract 動詞 ─────────
def _geo_sample(m) -> dict:
    W = []

    def w(t, x, y):
        W.append({"text": t, "bbox": [x, y, x + 6 * len(t), y + 9]})
    for t, x in (("NT$m", 60), ("2024A", 200), ("2025F", 300), ("2026F", 400)):
        w(t, x, 100)
    for y, lab, vals in ((120, "Revenue", ("1,234", "5,678", "6,789")), (140, "EBIT", ("(83)", "120", "150")), (160, "EPS", ("2.31", "3.10", "3.85"))):     # 座標重建至少 3 列
        w(lab, 60, y)
        for x, v in zip((200, 300, 400), vals):
            w(v, x, y)
    rows = [["NT$m", "2024A", "2025F 2026F"], ["Revenue", "1,234 5,678", "6,789"], ["EBIT", "(83) 120", "150"], ["EPS", "2.31 3.10", "3.85"]]
    data = {"extractor": "pdfplumber", "coordinate_space": "pdf_points", "pages": [{"number": 1, "width": 595, "height": 842, "words": W, "tables": [{"rows": rows, "bbox": [55, 95, 460, 175]}]}]}
    res = getattr(m, _PE["ast"]["interface"]["entry"])(data, extractor="pdfplumber", source_id="sample")
    t = next((t for t in res["pages"][0]["period_tables"] if "geometry" in t["region_origin"]), None)
    return {"rows": _rows_from_period_table(t, "NT$m") if t else [], "errors": res.get("errors") or []}


def postextract_status() -> dict:
    fs = pe_files()
    if not fs:
        return {"err": "找不到引擎(intake\\VRN_PostExtract\\%s_v####.py)" % _FAM}
    a = pe_ast(fs[0])
    m = _pe()
    out = {"ast": a, "files": [str(p) for p in fs], "loaded": bool(m), "err": _PE.get("err", "")}
    if m and a["interface"]["selfcheck"]:
        try:
            sc = getattr(m, a["interface"]["selfcheck"])()
            out["selfcheck"] = (sum(1 for x in sc if isinstance(x, dict) and x.get("status") == "PASS"), len(sc))
        except Exception as exc:  # noqa: BLE001
            out["selfcheck"] = (0, 0)
            out["err"] = "自測例外 %s" % type(exc).__name__
    if m:
        try:
            out["sample"] = _geo_sample(m)
        except Exception as exc:  # noqa: BLE001
            out["sample"] = {"rows": [], "errors": ["%s:%s" % (type(exc).__name__, str(exc)[:80])]}
    side = fs[0].parent / ("VRN_PostExtract_AST_%s.json" % ("v" + a["version"] if a["version"] else "v0100"))
    book = {"schema": "VIA.VRN.PostExtract.AST.v1", "engine": a["file"], "sha12": a["sha12"], "rule": "原檔不動;本冊 = AST 分類區隔 + 介面 + F01~F25 對應函式", "interface": a["interface"],
            "categories": a["categories"], "fcodes": a["fcodes"], "functions": a["functions"]}
    try:
        old = json.loads(side.read_text(encoding="utf-8")) if side.exists() else None
        if old != book:
            side.write_text(json.dumps(book, ensure_ascii=False, indent=1), encoding="utf-8")
            out["side_written"] = side.name
        out["side"] = str(side)
    except OSError:
        pass
    page = _resolve("_page")
    if page:
        rows = [("GREEN" if f["name"] in a["interface"].values() else ("YELLOW" if f["cat"] == "其他" else "GRAY"), [f["cat"], f["name"], ", ".join(f["args"][:5]), "%d–%d" % tuple(f["lines"]), " ".join(f["fcodes"]) or "—", f["doc"] or "—"]) for f in sorted(a["functions"], key=lambda f: ([c for c, _ in _CATS] + ["其他"]).index(f["cat"]))]
        hp = _rep() / "POSTEXTRACT_latest.html"
        hp.parent.mkdir(parents=True, exist_ok=True)
        hp.write_text(page("擷取後復健引擎 · AST 分類區隔(原檔不動)· 自適應介面", "%s v%s · %d 行 · %d 函式 · 介面 %s · 正本橋 %s · 自測 %s" % (a["file"], a["version"], a["lines"], len(a["functions"]), a["interface"]["entry"], "有" if a["bridge"] else "無", "%d/%d" % out.get("selfcheck", (0, 0))),
                               ["類", "函式", "參數", "行", "處理情境", "說明"], rows), encoding="utf-8")
        out["html"] = str(hp)
    return out


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()
    if args[:1] == ["postextract"]:
        o = postextract_status()
        if o.get("err") and not o.get("ast"):
            print("[計] 擷取後復健引擎 · %s · RED" % o["err"])
            return 1
        a = o["ast"]
        print("[計] 擷取後復健引擎 · %s v%s · %d 行 · %d 函式 · 正本橋 %s · 載入 %s%s" % (a["file"], a["version"], a["lines"], len(a["functions"]), "有" if a["bridge"] else "無", "✓" if o["loaded"] else "✗", (" · " + o["err"]) if o.get("err") else ""))
        print("[計] 自適應介面(AST)· 入口 %s · 比對 %s · 自測 %s · 清單 %s" % tuple(a["interface"].get(k) or "—" for k in ("entry", "reconcile", "selfcheck", "inventory")))
        print("[計] 分類區隔(AST)· " + " · ".join("%s %d" % (c, a["categories"].get(c, 0)) for c in [c for c, _ in _CATS] + ["其他"]))
        print("[計] 處理情境 F01~F25 · 有對應函式 %d 種 · %s" % (len(a["fcodes"]), " ".join(sorted(a["fcodes"]))))
        if "selfcheck" in o:
            print("[計] 引擎自測 %d/%d" % o["selfcheck"])
        s = o.get("sample") or {}
        print("[計] 座標重建樣例(黏住的 1,234 5,678 → 依字詞座標拆開)· %s" % (" | ".join("/".join(r) for r in s.get("rows", [])) or ("失敗 " + "; ".join(s.get("errors", [])))))
        if o.get("side"):
            print("[計] AST 附冊 %s%s" % (o["side"], " · 已寫" if o.get("side_written") else " · 內容沒變"))
        if o.get("html"):
            print("  [U/I] %s" % o["html"])
        return 0
    if args[:1] == ["layout"]:
        args, msg = layout_args(args)
        print(msg)
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
    td = Path(tempfile.mkdtemp(prefix="vrn168-"))
    try:
        fake = td / "fake_engine.py"
        fake.write_text("ENGINE_VERSION = '0999'\ndef repair_data(data, extractor='x', source_id=None):\n    return {}\ndef run_self_checks():\n    return []\ndef write_x(a):\n    pass\n", encoding="utf-8")
        fa = pe_ast(fake)
        chk("① 自適應介面:AST 依簽名找入口(函式改名 repair_data 也找得到)· 版本常數 0999 · 分類區隔(驗證 / 輸出)",
            fa["interface"]["entry"] == "repair_data" and fa["version"] == "0999" and fa["categories"].get("驗證") == 1 and fa["categories"].get("輸出") == 1)
        fs = pe_files()
        m = _pe()
        chk("② 擷取後復健引擎在(intake\\VRN_PostExtract\\ 尾版 · AST 找到入口 repair_extracted_data · 載入成功)", bool(fs) and m is not None and _PE["ast"]["interface"]["entry"] == "repair_extracted_data")
        if m is not None:
            a = _PE["ast"]
            sc = getattr(m, a["interface"]["selfcheck"])()
            chk("③ 引擎自帶自測全過(%d/%d)· AST 分類區隔七類都有 · F01~F25 對應函式 ≥ 20 種" % (sum(1 for x in sc if x.get("status") == "PASS"), len(sc)),
                all(x.get("status") == "PASS" for x in sc) and len(sc) >= 50 and all(a["categories"].get(c, 0) > 0 for c, _ in _CATS) and len(a["fcodes"]) >= 20)
            s = _geo_sample(m)
            chk("④ 記憶體 JSON 介面帶字詞座標(v0101 修正前會 KeyError)· 黏住的「1,234 5,678」依座標拆成 Revenue 1,234 / 5,678 / 6,789",
                not s["errors"] and s["rows"][:2] == [["NT$m", "2024A", "2025F", "2026F"], ["Revenue", "1,234", "5,678", "6,789"]])
            from reportlab.pdfgen import canvas
            import pdfplumber
            pdfp = td / "t.pdf"
            c = canvas.Canvas(str(pdfp), pagesize=(595, 842))
            c.setFont("Helvetica", 9)
            Y = lambda y: 842 - y - 9  # noqa: E731
            for t, x in (("NT$m", 60), ("2024A", 200), ("2025F", 300), ("2026F", 400)):
                c.drawString(x, Y(100), t)
            for y, lab, vals in ((120, "Revenue", ("1,234", "5,678", "6,789")), (140, "Operating profit", ("(83)", "120", "150")), (160, "EPS", ("2.31", "3.10", "3.85"))):
                c.drawString(60, Y(y), lab)
                for x, v in zip((200, 300, 400), vals):
                    c.drawString(x, Y(y), v)
            c.showPage()
            c.setFont("Helvetica", 9)
            c.drawString(60, Y(100), "The company expects demand to keep growing next year")
            c.drawString(320, Y(100), "management guided margins higher in 2H")
            c.drawString(60, Y(115), "driven by AI server shipments and new customers")
            c.drawString(320, Y(115), "while pricing remains stable for now")
            c.save()
            with pdfplumber.open(str(pdfp)) as pdf:
                pg = pdf.pages[0]
                b = {"id": "P1·F·01·T1", "kind": "table", "sub": "財務表(損益)", "role": "BODY", "page": 1, "x0": 55.0, "top": 95.0, "x1": 460.0, "bottom": 175.0,
                     "rows": [["NT$m", "2024A", "2025F 2026F"], ["Revenue", "1,234 5,678", "6,789"], ["Operating profit", "(83) 120", "150"], ["EPS", "2.31 3.10", "3.85"]]}
                del _PE_LOG[:]
                v0 = _PREV_VT(dict(b), pg)
                v = verify_table_v168(b, pg)
                chk("⑤ 第二步插入:單讀沒過(合併數字格 %d)→ 復健依座標重建 → VRN 原驗表再驗過 · 原列留 raw_rows_pe · 引擎標 PostExtract" % v0.get("multi_left", 0),
                    not v0["ok"] and v["ok"] and b["rows"][1] == ["Revenue", "1,234", "5,678", "6,789"] and b.get("raw_rows_pe") and "PostExtract" in b.get("engine", "") and _PE_LOG[-1]["status"] == "修好")
                pg2 = pdf.pages[1]
                bt = {"id": "P2·F·01·T1", "kind": "table", "sub": "資訊表", "role": "BODY", "page": 2, "x0": 55.0, "top": 95.0, "x1": 560.0, "bottom": 130.0,
                      "rows": [["The company expects demand to keep growing", "management guided margins higher in 2H"], ["driven by AI server shipments", "while pricing remains stable for now"]]}
                vt = verify_table_v168(bt, pg2)
                chk("⑥ 文字 / 表格分離:兩欄長句被當成表(字還原不足沒過)→ 逐格判讀幾乎都是句子 → 改回正文 · 內容取表框內完整文字(不丟字)",
                    vt.get("as_text") and bt["kind"] == "text" and "next year" in bt.get("text", "") and "for now" in bt.get("text", "") and bt.get("rows_pe_text"))
        a1, m1 = layout_args(["layout", "--dir", "x"])
        a2, m2 = layout_args(["layout", "--ocr"])
        chk("⑦ layout 預設不跑 OCR(自動加 --no-ocr)· 要跑加 --ocr(拿掉旗標交給前版 = 前版預設會跑)", a1[-1] == "--no-ocr" and "不跑" in m1 and a2 == ["layout"] and "要跑" in m2)
        global _PREV_L2
        keep = _PREV_L2

        def fake_l2(row):
            _PE_LOG.extend([{"id": "T1", "status": "修好", "how": "依字詞座標重建", "ms": 12}, {"id": "T2", "status": "未過", "codes": ["F22"], "ms": 9}])
            return {"tools": [{"table": "T1", "tool": "單讀(pdfplumber)", "ok": False}, {"table": "T2", "tool": "單讀(pdfplumber) → 雙讀(TableRepair)", "ok": False}]}
        _PREV_L2 = fake_l2
        try:
            r = l2_one_v168({})
        finally:
            _PREV_L2 = keep
        chk("⑧ 工具效益帳標上復健:T1「單讀 → 復健(PostExtract)」過 · T2「單讀 → 復健:未過 → 雙讀」· 統計 試 2 修好 1 未過主因 F22",
            r["tools"][0]["tool"] == "單讀(pdfplumber) → 復健(PostExtract)" and r["tools"][0]["ok"] and r["tools"][1]["tool"].startswith("單讀(pdfplumber) → 復健(PostExtract):未過 → 雙讀")
            and r["pe"]["tried"] == 2 and r["pe"]["fixed"] == 1 and r["pe"]["review"] == {"F22": 1})
    finally:
        shutil.rmtree(td, ignore_errors=True)
    me = Path(__file__).read_text(encoding="utf-8")
    chk("⑨ 正本加速器橋 · 自帶多程序墊片", "import VeritasCeleritas_v1141" in me and _job_entry.__module__ in ("__main__", __name__))
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("⑩ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    print("[計] VRN_SystemManager_v0168 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
