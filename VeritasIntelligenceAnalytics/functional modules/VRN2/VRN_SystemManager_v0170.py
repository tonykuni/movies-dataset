#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0170 — 薄尾(操作員 2026-10-10「讀取所有報告 抓出個股報告 用 LAYOUT 切塊功能將第一頁資訊區跟本文區分表格分區切塊
   及年度財報頁分表左右上下切塊 轉換為 DPI 300 的 PNG 並有效編號分區擷取 …… 在 TEMP 再進行擷取 BASIC INFO / FINANCIAL DATA /
   FIXED CONTENT TEXT AND INFO AREA AND ANNUAL FINANCIAL STATEMENTS」)。
  crops 動詞(讀上一輪 layout 的逐檔結果 —— 第一步已從全部報告挑出個股報告,第二步已切好區塊;不重跑 layout):
  ① 切塊:第一頁 資訊區(每區一塊)· 資訊區的表(每張一塊)· 本文(每區 · 遇表 / 圖分段)· 本文的表(每張一塊);頁首頁尾不切
          年度財報頁 每張表一塊 · 位置 LT 左上 / RT 右上 / LB 左下 / RB 右下 / WT 寬上 / WB 寬下
  ② 300 DPI PNG(PyMuPDF clip)存 TEMP:<序>_<代號>_<券商>_<日期>\\P<頁>_<類>_<序>[_<位置>].png;切塊編號 = <序>-P<頁>_<類>_<序>[_<位置>]
  ③ 五類擷取(原生文字層 · 依切塊):BASIC_INFO(每份一列)· INFO_AREA · FIXED_CONTENT_TEXT · FINANCIAL_DATA(首頁表逐格)· ANNUAL_FS(年度財報逐格)
     → VIA_Reports\\vrn\\crops\\CROPS_<類>_latest.csv + parquet;每格標驗證過與否
  ④ OCR 補讀(只給原生沒過 / 讀不出字的切塊 · rapidocr 單引擎 · 預算 240 秒)→ OCR_CANDIDATE(候選,不當已驗證);--no-ocr 不跑
  ⑤ CROPS_latest.html 總覽 + 每份報告切塊圖庫(TEMP 夾內 index.html)
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
import html
import importlib.util
import json
import os
import re
import sys
import tempfile
import time
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0170"


def _vnum_v0170(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0170(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0170(p) < _vnum_v0170(__file__)), key=_vnum_v0170)
PRIOR = _load_v0170(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


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
PAD = 4.0

# 進度條:加「切塊」「OCR」兩段(v0166 的三段進度只認 分類 / 取頁 / 還原)
_m166 = _owner("_RANGE")
if _m166 is not None and isinstance(vars(_m166).get("_RANGE"), dict):
    vars(_m166)["_RANGE"].update({"切塊": (5, 80), "OCR": (80, 97)})
    vars(_m166)["_RX"] = re.compile(r"^\s*\[進度\]\s*(\d+)\s*/\s*(\d+)\s*·\s*(?:(分類|取頁|還原|切塊|OCR)\s*·\s*)?(?:([A-Z—-]+)\s*·\s*)?(.*)$")


def _union(bs: list) -> list:
    return [min(b["x0"] for b in bs), min(b["top"] for b in bs), max(b["x1"] for b in bs), max(b["bottom"] for b in bs)]


def _pos(b: dict, W: float, H: float) -> str:
    cx, cy = (b["x0"] + b["x1"]) / 2, (b["top"] + b["bottom"]) / 2
    v = "T" if cy < H / 2 else "B"
    if (b["x1"] - b["x0"]) >= 0.6 * W:
        return "W" + v
    return ("L" if cx < W / 2 else "R") + v


def plan_regions(pg: dict, first: bool, annual: bool) -> list:
    """一頁要切哪些塊:(類, 序號 / 區, 位置, bbox, 區塊編號, 區塊)。"""
    W, H = float(pg.get("W") or 595), float(pg.get("H") or 842)
    roles = pg.get("roles") or {}
    role = lambda b: b.get("role") or roles.get(b.get("zone"), "BODY")  # noqa: E731
    blocks = [b for b in pg.get("blocks", []) if role(b) not in ("HEADER", "FOOTER") and all(k in b for k in ("x0", "top", "x1", "bottom"))]
    tables = sorted([b for b in blocks if b.get("kind") == "table"], key=lambda b: (b["top"], b["x0"]))
    obst = [b for b in blocks if b.get("kind") in ("table", "figure")]
    out = []
    if first:
        info = [b for b in blocks if b.get("kind") == "text" and role(b) == "INFO"]
        for z in sorted({b.get("zone", "F") for b in info}):
            g = [b for b in info if b.get("zone", "F") == z]
            out.append(("INFO", z, "", _union(g), [b["id"] for b in g], g))
        it = [t for t in tables if role(t) == "INFO"]
        for k, t in enumerate(it, 1):
            out.append(("INFO_TBL", "%02d" % k, "", _union([t]), [t["id"]], [t]))
        body = sorted([b for b in blocks if b.get("kind") == "text" and role(b) == "BODY"], key=lambda b: b["top"])
        for z in sorted({b.get("zone", "F") for b in body}):
            g = [b for b in body if b.get("zone", "F") == z]
            segs, cur = [], []
            for b in g:
                if cur:
                    lo, hi = cur[-1]["bottom"], b["top"]
                    cut = any(o["top"] >= lo - 1 and o["bottom"] <= hi + 1 and min(o["x1"], b["x1"]) > max(o["x0"], b["x0"]) for o in obst)
                    if cut:
                        segs.append(cur)
                        cur = []
                cur.append(b)
            if cur:
                segs.append(cur)
            for k, sg in enumerate(segs, 1):
                out.append(("BODY", "%s_%02d" % (z, k), "", _union(sg), [b["id"] for b in sg], sg))
        for k, t in enumerate([t for t in tables if role(t) != "INFO"], 1):
            out.append(("TBL", "%02d" % k, "", _union([t]), [t["id"]], [t]))
    if annual:
        for k, t in enumerate(tables, 1):
            out.append(("FIN", "%02d" % k, _pos(t, W, H), _union([t]), [t["id"]], [t]))
    return out


def _safe(s: str) -> str:
    return re.sub(r'[\\/:*?"<>|\s]+', "_", str(s or "")).strip("_")[:24]


def _cells(rows: list, verified: bool, pn, ph) -> list:
    out = []
    if not rows:
        return out
    hi = ph(rows) if ph else 0
    periods = rows[hi] if hi < len(rows) else []
    for ri, r in enumerate(rows[hi + 1:], hi + 1):
        label = (r[0] if r else "") or ""
        for ci, raw in enumerate(r[1:], 1):
            if not (raw or "").strip():
                continue
            num = pn(raw) if pn else None
            out.append({"row": ri, "label": label, "period": periods[ci] if ci < len(periods) else "", "raw": raw, "number": "" if num is None else num, "verified": "是" if verified else "否"})
    return out


def _ocr_engine():
    try:
        from rapidocr_onnxruntime import RapidOCR  # noqa: WPS433
        return RapidOCR()
    except Exception:  # noqa: BLE001
        return None


def crops_run(run: str = "", ocr: bool = True, budget: int = 240, dpi: int = 300) -> dict:
    d = _resolve("_latest_l2_dir")(run)
    if not d:
        return {"err": "找不到上一輪 layout 的逐檔結果(先跑 -Verb layout)"}
    import fitz  # noqa: WPS433
    pn, ph = _resolve("parse_number"), _resolve("_period_header")
    docs = []
    for p in sorted(d.glob("*.json")):
        try:
            j = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        row = j.get("row") or {}
        if row.get("mini") and Path(row["mini"]).exists() and j.get("pages"):
            docs.append(j)
    docs.sort(key=lambda j: j["row"].get("file", ""))
    ts = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
    root = (Path(os.environ["VIA_SPILL_DIR"]) if os.environ.get("VIA_SPILL_DIR") else Path(tempfile.gettempdir()) / "VIA_progress") / ("vrn_crops_" + ts)
    root.mkdir(parents=True, exist_ok=True)
    man, cats = [], defaultdict(list)
    t0 = time.time()
    for nn, j in enumerate(docs, 1):
        row, info = j["row"], j.get("info") or {}
        code, broker, date8 = row.get("code", ""), row.get("broker", ""), re.sub(r"\D", "", row.get("date", "") or "")
        rid = "%02d_%s_%s_%s" % (nn, code or "NA", _safe(broker) or "NA", date8 or "NA")
        folder = root / rid
        folder.mkdir(parents=True, exist_ok=True)
        picked, annual = list(row.get("picked") or []), set(row.get("annual") or [])
        base = {"report": rid, "file": row.get("file", ""), "code": code, "name": row.get("name", "")}
        lamp_doc, n_doc = "GREEN", 0
        try:
            doc = fitz.open(row["mini"])
        except Exception as exc:  # noqa: BLE001
            man.append(dict(base, crop_id="", png="", cls="—", lamp="RED", note="開不了取頁檔 %s" % type(exc).__name__))
            continue
        try:
            for pi, pg in enumerate(j["pages"]):
                orig = int(pg.get("page") or (pi + 1))
                local = picked.index(orig) if orig in picked else pi
                if local >= len(doc):
                    continue
                page = doc[local]
                sx = page.rect.width / float(pg.get("W") or page.rect.width)
                sy = page.rect.height / float(pg.get("H") or page.rect.height)
                first = pi == 0
                for cls, seq, pos, bb, ids, blks in plan_regions(pg, first, orig in annual and not first):
                    stem = "P%02d_%s_%s%s" % (orig, cls, seq, ("_" + pos) if pos else "")
                    cid = "%02d-%s" % (nn, stem)
                    rect = fitz.Rect(max(0, (bb[0] - PAD) * sx), max(0, (bb[1] - PAD) * sy), min(page.rect.width, (bb[2] + PAD) * sx), min(page.rect.height, (bb[3] + PAD) * sy))
                    png = folder / (stem + ".png")
                    try:
                        pix = page.get_pixmap(clip=rect, dpi=dpi, alpha=False)
                        pix.save(str(png))
                        wpx, hpx = pix.width, pix.height
                    except Exception as exc:  # noqa: BLE001
                        man.append(dict(base, crop_id=cid, png="", cls=cls, lamp="RED", note="輸出 PNG 失敗 %s" % type(exc).__name__))
                        lamp_doc = "RED"
                        continue
                    tbl = [b for b in blks if b.get("kind") == "table"]
                    ver = all((b.get("verify") or {}).get("ok") for b in tbl) if tbl else None
                    txt = " ".join((b.get("text") or "") for b in blks if b.get("kind") == "text").strip()
                    has_native = bool(txt) or any(b.get("rows") for b in tbl)
                    lamp = "GREEN" if (ver is not False and has_native) else ("YELLOW" if has_native else "GRAY")
                    if lamp != "GREEN" and lamp_doc == "GREEN":
                        lamp_doc = "YELLOW"
                    man.append(dict(base, crop_id=cid, png=str(png), cls=cls, page=orig, pos=pos, bbox=[round(x, 1) for x in bb], px="%dx%d" % (wpx, hpx), dpi=dpi, blocks=",".join(ids),
                                    verified={True: "是", False: "否", None: "—"}[ver], native="有" if has_native else "無", lamp=lamp, note=""))
                    n_doc += 1
                    if cls == "INFO":
                        for b in blks:
                            cats["INFO_AREA"].append(dict(base, crop_id=cid, block=b["id"], kind="文字", key="", value=b.get("text", "")))
                    elif cls == "INFO_TBL":
                        for b in tbl:
                            for r in b.get("rows") or []:
                                if any((c or "").strip() for c in r):
                                    cats["INFO_AREA"].append(dict(base, crop_id=cid, block=b["id"], kind="表", key=(r[0] or "").strip(), value=" | ".join((c or "").strip() for c in r[1:])))
                    elif cls == "BODY":
                        for b in blks:
                            cats["FIXED_CONTENT_TEXT"].append(dict(base, crop_id=cid, block=b["id"], sub=b.get("sub", ""), text=b.get("text", "")))
                    elif cls in ("TBL", "FIN"):
                        for b in tbl:
                            for c in _cells(b.get("rows") or [], bool((b.get("verify") or {}).get("ok")), pn, ph):
                                cats["FINANCIAL_DATA" if cls == "TBL" else "ANNUAL_FS"].append(dict(base, crop_id=cid, page=orig, pos=pos, table=b["id"], category=b.get("sub", ""), **c))
        finally:
            doc.close()
        an = info.get("analysts") or []
        cats["BASIC_INFO"].append(dict(base, broker=broker, date=row.get("date", ""), yf=row.get("yf", ""), bbg=row.get("bbg", ""), rating=info.get("rating", ""), rating_raw=info.get("rating_raw", ""),
                                       tp=info.get("tp", ""), close=info.get("close", ""), date_p1=info.get("date_p1", ""),
                                       analysts="; ".join((a.get("name") or "") if isinstance(a, dict) else str(a) for a in an),
                                       info_crops=",".join(m["crop_id"] for m in man if m.get("report") == rid and m.get("cls") in ("INFO", "INFO_TBL"))))
        print("  [進度] %d/%d · 切塊 · %s · %s(%d 塊)" % (nn, len(docs), lamp_doc, row.get("file", "")[:44], n_doc), flush=True)
    # ④ OCR 補讀:只給原生沒過 / 讀不出字的切塊
    ocr_n, ocr_skip, ocr_ms = 0, 0, 0
    targets = [m for m in man if m.get("png") and (m.get("verified") == "否" or m.get("native") == "無")]
    eng = _ocr_engine() if (ocr and targets) else None
    if ocr and targets and eng is None:
        ocr_skip = len(targets)
    t1 = time.time()
    for i, m in enumerate(targets, 1):
        if eng is None:
            break
        if time.time() - t1 > budget:
            ocr_skip = len(targets) - i + 1
            break
        ts0 = time.time()
        try:
            res, _ = eng(m["png"])
            lines = sorted(res or [], key=lambda r: (round(r[0][0][1] / 12), r[0][0][0]))
            text = " ".join(r[1] for r in lines)
            conf = sum(float(r[2]) for r in lines) / len(lines) if lines else 0.0
            cats["OCR_CANDIDATE"].append({"report": m["report"], "file": m["file"], "code": m["code"], "crop_id": m["crop_id"], "cls": m["cls"], "engine": "rapidocr", "dpi": dpi,
                                          "lines": len(lines), "mean_conf": round(conf, 3), "text": text[:4000], "status": "候選(未驗證)"})
            m["note"] = "OCR 候選 %d 行 · 信心 %.2f" % (len(lines), conf)
            ocr_n += 1
        except Exception as exc:  # noqa: BLE001
            m["note"] = "OCR 失敗 %s" % type(exc).__name__
        ocr_ms += int((time.time() - ts0) * 1000)
        print("  [進度] %d/%d · OCR · — · %s" % (i, len(targets), m["crop_id"]), flush=True)
    out = _rep() / "crops"
    out.mkdir(parents=True, exist_ok=True)
    cols = {"BASIC_INFO": ["report", "file", "code", "name", "broker", "date", "yf", "bbg", "rating", "rating_raw", "tp", "close", "date_p1", "analysts", "info_crops"],
            "INFO_AREA": ["report", "file", "code", "name", "crop_id", "block", "kind", "key", "value"],
            "FIXED_CONTENT_TEXT": ["report", "file", "code", "name", "crop_id", "block", "sub", "text"],
            "FINANCIAL_DATA": ["report", "file", "code", "name", "crop_id", "page", "pos", "table", "category", "row", "label", "period", "raw", "number", "verified"],
            "ANNUAL_FS": ["report", "file", "code", "name", "crop_id", "page", "pos", "table", "category", "row", "label", "period", "raw", "number", "verified"],
            "OCR_CANDIDATE": ["report", "file", "code", "crop_id", "cls", "engine", "dpi", "lines", "mean_conf", "text", "status"],
            "MANIFEST": ["report", "file", "code", "name", "crop_id", "cls", "page", "pos", "bbox", "px", "dpi", "blocks", "verified", "native", "lamp", "note", "png"]}
    paths = {}
    cats["MANIFEST"] = man
    for k, cl in cols.items():
        p = out / ("CROPS_%s_latest.csv" % k)
        with p.open("w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cl, extrasaction="ignore")
            w.writeheader()
            w.writerows([{c: (json.dumps(v, ensure_ascii=False) if isinstance(v, list) else v) for c, v in r.items()} for r in cats.get(k, [])])
        paths[k] = str(p)
        try:
            import duckdb  # noqa: WPS433
            if cats.get(k):
                duckdb.connect().execute("copy (select * from read_csv_auto('%s', header=true, all_varchar=true)) to '%s' (format parquet)" % (str(p).replace("'", "''"), str(p.with_suffix(".parquet")).replace("'", "''")))
                paths[k + "_parquet"] = str(p.with_suffix(".parquet"))
        except Exception:  # noqa: BLE001
            pass
    page = _resolve("_page")
    by = defaultdict(list)
    for m in man:
        by[m["report"]].append(m)
    for rid, ms in by.items():
        g = root / rid / "index.html"
        cards = "".join("<div class='c'><div class='h'><b>%s</b> · %s · %s · 驗證 %s · %s</div><img src='%s' loading='lazy'><div class='n'>%s</div></div>" % (
            html.escape(m["crop_id"]), html.escape(m["cls"]), html.escape(m.get("px", "")), html.escape(m.get("verified", "")), html.escape(m.get("blocks", "")), html.escape(Path(m["png"]).name), html.escape(m.get("note", "")))
                        for m in ms if m.get("png"))
        g.write_text("<!doctype html><meta charset='utf-8'><title>%s</title><style>body{font:13px 'Microsoft JhengHei',sans-serif;margin:12px;background:#fafafa}.c{background:#fff;border:1px solid #ddd;border-radius:6px;padding:8px;margin:8px 0}"
                     ".c img{max-width:100%%;border:1px solid #eee}.h{margin-bottom:6px}.n{color:#666;font-size:12px}</style><h3>%s · %s</h3>%s" % (html.escape(rid), html.escape(rid), html.escape(ms[0]["file"]), cards), encoding="utf-8")
    if page:
        rows = []
        for rid, ms in by.items():
            cnt = defaultdict(int)
            for m in ms:
                cnt[m["cls"]] += 1
            lam = "RED" if any(m["lamp"] == "RED" for m in ms) else ("YELLOW" if any(m["lamp"] in ("YELLOW", "GRAY") for m in ms) else "GREEN")
            rows.append((lam, ["<a href='file:///%s'>%s</a>" % (html.escape(str(root / rid / "index.html")).replace("\\", "/"), html.escape(rid)), html.escape(ms[0]["file"]), cnt["INFO"], cnt["INFO_TBL"], cnt["BODY"], cnt["TBL"], cnt["FIN"],
                                sum(1 for m in ms if m.get("verified") == "否"), sum(1 for m in ms if "OCR 候選" in (m.get("note") or ""))]))
        hp = out / "CROPS_latest.html"
        hp.write_text(page("分區切塊 300 DPI PNG · 五類擷取(BASIC INFO / INFO AREA / FIXED CONTENT TEXT / FINANCIAL DATA / ANNUAL FS)",
                           "讀 %s · 個股報告 %d 份 · 切塊 %d · PNG 在 %s · OCR 補讀 %d(略過 %d)· %d 秒" % (html.escape(str(d)), len(docs), sum(1 for m in man if m.get("png")), html.escape(str(root)), ocr_n, ocr_skip, int(time.time() - t0)),
                           ["報告(點開看切塊)", "檔", "資訊區", "資訊表", "本文段", "首頁表", "年度表", "原生沒過", "OCR 候選"], rows), encoding="utf-8")
        paths["html"] = str(hp)
    return {"dir": str(d), "root": str(root), "docs": len(docs), "crops": sum(1 for m in man if m.get("png")), "by_cls": {c: sum(1 for m in man if m.get("cls") == c) for c in ("INFO", "INFO_TBL", "BODY", "TBL", "FIN")},
            "cats": {k: len(v) for k, v in cats.items()}, "ocr": ocr_n, "ocr_skip": ocr_skip, "ocr_ms": ocr_ms, "targets": len(targets), "paths": paths, "secs": int(time.time() - t0),
            "red": sum(1 for m in man if m.get("lamp") == "RED"), "unverified": sum(1 for m in man if m.get("verified") == "否")}


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()
    if args[:1] == ["crops"]:
        inst = _resolve("install_v166")
        if inst:
            inst()
        opt = lambda k, dv="": args[args.index(k) + 1] if k in args and args.index(k) + 1 < len(args) else dv  # noqa: E731
        o = crops_run(opt("--run"), "--no-ocr" not in args, int(opt("--budget", "240") or 240), int(opt("--dpi", "300") or 300))
        if o.get("err"):
            print("[計] 分區切塊 · %s · RED" % o["err"])
            return 1
        b = o["by_cls"]
        print("[計] 分區切塊 · 讀上一輪 layout(%s)· 個股報告 %d 份 · 切塊 %d(資訊區 %d · 資訊表 %d · 本文段 %d · 首頁表 %d · 年度表 %d)· 300 DPI PNG · %d 秒%s" % (
            Path(o["dir"]).parent.name, o["docs"], o["crops"], b["INFO"], b["INFO_TBL"], b["BODY"], b["TBL"], b["FIN"], o["secs"], " · 紅 %d" % o["red"] if o["red"] else ""))
        print("[計] PNG 夾 %s(編號 <序>_<代號>_<券商>_<日期>\\P<頁>_<類>_<序>[_位置])" % o["root"])
        c = o["cats"]
        print("[計] 五類擷取 · BASIC_INFO %d 份 · INFO_AREA %d 列 · FIXED_CONTENT_TEXT %d 段 · FINANCIAL_DATA %d 格 · ANNUAL_FS %d 格 · 原生沒過的表 %d 塊" % (
            c.get("BASIC_INFO", 0), c.get("INFO_AREA", 0), c.get("FIXED_CONTENT_TEXT", 0), c.get("FINANCIAL_DATA", 0), c.get("ANNUAL_FS", 0), o["unverified"]))
        print("[計] OCR 補讀(只給原生沒過 / 讀不出字的切塊 · rapidocr)· 目標 %d · 讀了 %d · 略過 %d · %d 秒 · 結果 = 候選(未驗證)" % (o["targets"], o["ocr"], o["ocr_skip"], o["ocr_ms"] // 1000)
              if "--no-ocr" not in args else "[計] OCR 補讀 · 本輪不跑(--no-ocr)")
        print("[計] 檔 %s" % " · ".join(Path(v).name for k, v in o["paths"].items() if k.endswith("_parquet")))
        if o["paths"].get("html"):
            print("  [U/I] %s" % o["paths"]["html"])
        return 0
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
    td = Path(tempfile.mkdtemp(prefix="vrn170-"))
    saved = {k: os.environ.get(k) for k in ("VIA_SPILL_DIR", "VIA_VRN_HEALTH_OUT")}
    try:
        from reportlab.pdfgen import canvas
        stage = td / "VIA_progress" / "ps_x" / "spill" / "vrn_stage_r1"
        (stage / "layout_l2").mkdir(parents=True)
        (stage / "pages").mkdir()
        mini = stage / "pages" / "a_mini.pdf"
        c = canvas.Canvas(str(mini), pagesize=(595, 842))
        Y = lambda y: 842 - y - 9  # noqa: E731
        c.setFont("Helvetica", 9)
        c.drawString(40, Y(100), "Rating: Buy")
        c.drawString(40, Y(115), "Target price: NT$650")
        c.drawString(220, Y(100), "We expect revenue to grow strongly in 2026.")
        for t, x in (("NT$m", 220), ("2025A", 330), ("2026F", 420)):
            c.drawString(x, Y(200), t)
        for y, lab, v in ((215, "Revenue", ("1,234", "1,456")), (230, "EPS", ("2.31", "3.10"))):
            c.drawString(220, Y(y), lab)
            c.drawString(330, Y(y), v[0])
            c.drawString(420, Y(y), v[1])
        c.drawString(220, Y(300), "Margins should stay healthy next year.")
        c.showPage()
        c.setFont("Helvetica", 9)
        for x0 in (40, 320):
            c.drawString(x0, Y(100), "Income")
            c.drawString(x0 + 80, Y(100), "2025A")
            c.drawString(x0, Y(115), "Sales")
            c.drawString(x0 + 80, Y(115), "100")
        c.drawString(40, Y(600), "Wide table Revenue 2024 2025 2026")
        c.save()
        tb = lambda i, x0, t, x1, b, rows, ok, role="BODY": {"id": i, "kind": "table", "zone": "F", "role": role, "x0": x0, "top": t, "x1": x1, "bottom": b, "rows": rows, "sub": "財務表", "verify": {"ok": ok}}  # noqa: E731
        tx = lambda i, z, role, x0, t, x1, b, text: {"id": i, "kind": "text", "zone": z, "role": role, "x0": x0, "top": t, "x1": x1, "bottom": b, "text": text, "sub": "內文"}  # noqa: E731
        j = {"run_id": "r1", "row": {"file": "凱基投顧_3653 健策_20260917.pdf", "code": "3653", "name": "健策", "broker": "KGI", "date": "2026-09-17", "yf": "3653.TW", "bbg": "3653 TT",
                                      "mini": str(mini), "picked": [1, 5], "annual": [5]},
             "info": {"rating": "Buy", "rating_raw": "Buy", "tp": 650.0, "close": 520.0, "date_p1": "2026-09-17", "analysts": [{"name": "向子慧"}]},
             "pages": [{"page": 1, "W": 595.0, "H": 842.0, "roles": {"L": "INFO", "R": "BODY", "H": "HEADER", "B": "FOOTER"},
                        "blocks": [tx("P1·L·01", "L", "INFO", 40, 100, 160, 124, "Rating: Buy Target price: NT$650"),
                                   tx("P1·R·01", "R", "BODY", 220, 100, 420, 109, "We expect revenue to grow strongly in 2026."),
                                   dict(tb("P1·R·02·T1", 220, 200, 470, 239, [["NT$m", "2025A", "2026F"], ["Revenue", "1,234", "1,456"], ["EPS", "2.31", "3.10"]], True), zone="R"),
                                   tx("P1·R·03", "R", "BODY", 220, 300, 420, 309, "Margins should stay healthy next year."),
                                   tx("P1·B·01", "B", "FOOTER", 40, 800, 300, 808, "disclaimer")]},
                       {"page": 5, "W": 595.0, "H": 842.0, "roles": {"F": "BODY"},
                        "blocks": [tb("P5·F·01·T1", 40, 100, 200, 124, [["Income", "2025A"], ["Sales", "100"]], True), tb("P5·F·02·T2", 320, 100, 480, 124, [["Income", "2025A"], ["Sales", "100"]], False),
                                   tb("P5·F·03·T3", 40, 600, 560, 609, [["Wide table Revenue", "2024 2025 2026"]], True)]}]}
        (stage / "layout_l2" / "a.json").write_text(json.dumps(j, ensure_ascii=False), encoding="utf-8")
        os.environ["VIA_SPILL_DIR"] = str(td / "VIA_progress" / "ps_new" / "spill")
        os.environ["VIA_VRN_HEALTH_OUT"] = str(td / "rep")
        o = crops_run("", ocr=True, budget=60)
        man = list(csv.DictReader(open(o["paths"]["MANIFEST"], encoding="utf-8-sig")))
        ids = sorted(m["crop_id"] for m in man)
        chk("① 切塊:第一頁 資訊區(L)· 本文(R 遇表分兩段)· 首頁表 · 頁尾不切;年度頁 左上 LT · 右上 RT · 寬下 WB → %s" % " ".join(ids),
            ids == ["01-P01_BODY_R_01", "01-P01_BODY_R_02", "01-P01_INFO_L", "01-P01_TBL_01", "01-P05_FIN_01_LT", "01-P05_FIN_02_RT", "01-P05_FIN_03_WB"])
        pngs = [Path(m["png"]) for m in man]
        from PIL import Image
        w0 = Image.open(next(x for x in pngs if x.name == "P01_TBL_01.png")).size[0]
        chk("② 300 DPI PNG 在 TEMP · 有效編號 01_3653_KGI_20260917\\P01_TBL_01.png · 寬 %d px(= (250+8) pt × 300/72 ≈ 1075)" % w0,
            all(x.exists() for x in pngs) and pngs[0].parent.name == "01_3653_KGI_20260917" and str(td) in str(pngs[0]) and abs(w0 - 1075) <= 3)
        cats = o["cats"]
        bi = list(csv.DictReader(open(o["paths"]["BASIC_INFO"], encoding="utf-8-sig")))[0]
        fd = list(csv.DictReader(open(o["paths"]["FINANCIAL_DATA"], encoding="utf-8-sig")))
        chk("③ 五類擷取:BASIC_INFO(評等 Buy · 目標價 650 · 分析師 向子慧 · 資訊區切塊)· INFO_AREA · FIXED_CONTENT_TEXT 2 段 · FINANCIAL_DATA(Revenue × 2026F = 1,456 · 驗證過)· ANNUAL_FS",
            bi["rating"] == "Buy" and bi["tp"] == "650.0" and bi["analysts"] == "向子慧" and "01-P01_INFO_L" in bi["info_crops"] and cats["INFO_AREA"] == 1 and cats["FIXED_CONTENT_TEXT"] == 2
            and any(r["label"] == "Revenue" and r["period"] == "2026F" and r["raw"] == "1,456" and r["verified"] == "是" for r in fd) and cats["ANNUAL_FS"] >= 2)
        eng = _ocr_engine()
        if eng is not None:
            oc = list(csv.DictReader(open(o["paths"]["OCR_CANDIDATE"], encoding="utf-8-sig")))
            chk("④ OCR 補讀只給原生沒過的切塊(P05 右上表)· rapidocr 讀到「Sales」· 標候選(未驗證)", o["targets"] == 1 and len(oc) == 1 and oc[0]["crop_id"] == "01-P05_FIN_02_RT" and "Sales" in oc[0]["text"] and oc[0]["status"].startswith("候選"))
        else:
            chk("④ OCR 補讀:這台沒有 rapidocr → 目標 1 · 全數略過(不崩)", o["targets"] == 1 and o["ocr"] == 0 and o["ocr_skip"] == 1)
        gal = Path(o["root"]) / "01_3653_KGI_20260917" / "index.html"
        chk("⑤ 總覽頁 CROPS_latest.html + 每份報告切塊圖庫 index.html · CSV + parquet", Path(o["paths"]["html"]).exists() and gal.exists() and "P01_INFO_L.png" in gal.read_text(encoding="utf-8")
            and all(Path(o["paths"][k]).exists() for k in ("BASIC_INFO", "INFO_AREA", "FIXED_CONTENT_TEXT", "FINANCIAL_DATA", "ANNUAL_FS", "MANIFEST")))
        rx = vars(_m166)["_RX"] if _m166 is not None else None
        mm = rx.match("  [進度] 3/57 · 切塊 · GREEN · x.pdf") if rx else None
        chk("⑥ 進度條認得「切塊」「OCR」兩段(5→80% · 80→97%)", bool(mm) and mm.group(3) == "切塊" and vars(_m166)["_RANGE"]["OCR"] == (80, 97))
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(td, ignore_errors=True)
    me = Path(__file__).read_text(encoding="utf-8")
    chk("⑦ 正本加速器橋 · 自帶多程序墊片", "import VeritasCeleritas_v1141" in me and _job_entry.__module__ in ("__main__", __name__))
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("⑧ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    print("[計] VRN_SystemManager_v0170 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
