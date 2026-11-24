#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_ENG397_P1Segment v0130 — 薄尾(v0129 一字不動):fidelity 動詞 = 每頁每種擷取方法「還原到原樣」的量測與驗證

操作員 2026-11-24:「VRN 中間用 JSON 傳輸 · 非 OCR / 輕型 OCR / 重型 OCR 眾多工具組成 · 每個工具輸出都有錯 ·
  看能否每種方法都盡可能還原到原始樣態、百分之百一樣並且可驗證 · 輕型能解決的就不用重型 · 用之前的測試檔案夾優化 · 最快最精準」
  → 先量測再接上(本版只量測,擷取流程 run / p1view 行為不變;量完再依數字接進正常流程)。

驗證分三層(每一層都有可重算的證據,不靠「看起來對」):
  ① 文字層一致:pdfplumber · pypdfium2 · PyMuPDF(有裝才用)各自解碼同一頁 → 正規化(NFKC · 去空白)後
       逐字相同 = VERIFIED(序列一致);字元多重集相同但順序不同 = VERIFIED_SET;F1 ≥ 0.995 = NEAR;
       互相不一致 → OCR 當第二證人仲裁(輕到重逐階,哪一階分出勝負就停)= VERIFIED_OCR,用的是勝出的那份文字層(不是 OCR 字);
       實例:非內嵌 CID 字型 pdfplumber / PyMuPDF 解成「合法但錯的字」,只有 pypdfium2 對 → OCR 跟它一致 0.79、跟另兩家 0.36;仲裁不出 = CONFLICT;
       三家都沒字 = NO_TEXT(掃描頁)。含 (cid:N) / 替代字元 / 私用區(前版 garbled)的不算 VERIFIED。
  ② 視覺一致:已驗證的頁拿去跑 OCR 階梯每一階(預設 200 · 325p · 400p),量「OCR 還原率」=
       字元多重集 F1 與數字 token 多重集 F1(順序無關,避免閱讀順序不同被算成錯)→ 得到每一階實測的準度與耗時。
  ③ 沒有文字層的頁:OCR 由輕到重逐階跑,相鄰兩階互相一致(F1 ≥ 0.99)就停 = CONSENSUS;都不一致 = T4(人工)。
  每頁記最低夠用的層:T0 pdfplumber · T1 pypdfium2 / PyMuPDF · T2 / T3 OCR(輕 / 重)· T4 人工。
輸出(不含研報內文):<rep>/p1view/FIDELITY_latest.json + FIDELITY_latest.txt(≤300 行 · NEXT: 結尾)
  只有雜湊(正規化文字 sha256 前 16 碼)、數字、耗時;檔名以「D### + PDF sha1 前 10 碼」代替,對照表只留本機 FIDELITY_names_local.json。
用法:python VRN_ENG397_P1Segment_v0130.py fidelity [輸入夾] [--rep 夾] [--all] [--ladder 200,325p,400p] [--calib 2] [--limit N]
其他用法照前版(輸入夾 / --shard / --selftest)。OCR 走前版的隔離橋(VIA_VRN2_OCR_PY / _BRIDGE;沒設就找 ~/envs/vrn2_ocr);
  主環境裝了 rapidocr_onnxruntime 時才在本行程跑。不出網。零 TA-Lib。
[VIA:AST-CLASS] 類別 = 引擎(第一頁切割擷取)· 入口 = VRN_SystemManager p1view 動詞
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

import hashlib
import importlib.util
import json
import os
import re
import statistics
import sys
import tempfile
import time
import unicodedata
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_ENG397_P1Segment"
TAG = "VRN_ENG397_P1Segment v0130"


def _vnum(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
if PRIOR_PATH.stem in sys.modules:
    PRIOR = sys.modules[PRIOR_PATH.stem]
else:
    _spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem, PRIOR_PATH)
    PRIOR = importlib.util.module_from_spec(_spec)
    sys.modules[PRIOR_PATH.stem] = PRIOR
    _spec.loader.exec_module(PRIOR)


def __getattr__(name):
    return getattr(PRIOR, name)


ENGINE_ID, ENGINE_NAME = PRIOR.ENGINE_ID, PRIOR.ENGINE_NAME
run, selftest_prior = PRIOR.run, PRIOR.selftest
DEFAULT_LADDER = "200,325p,400p"
F1_NEAR, F1_AGREE = 0.995, 0.99
_NUMTOK = re.compile(r"\d[\d,]*(?:\.\d+)?")


# ---- 正規化 · 雜湊 · 多重集比對 ----
def norm(s: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", s or ""))


def sha16(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def f1(ref, got) -> float:
    """多重集 F1(順序無關)。兩邊都空 = 1.0;一邊空 = 0.0。"""
    a, b = Counter(ref), Counter(got)
    na, nb = sum(a.values()), sum(b.values())
    if na == 0 and nb == 0:
        return 1.0
    if na == 0 or nb == 0:
        return 0.0
    hit = sum((a & b).values())
    p, r = hit / nb, hit / na
    return 0.0 if hit == 0 else round(2 * p * r / (p + r), 4)


def nums(s: str) -> list:
    return [x.replace(",", "") for x in _NUMTOK.findall(unicodedata.normalize("NFKC", s or ""))]


# ---- ① 文字層三方 ----
def layers(pl_page, pdoc, i: int, fz=None) -> dict:
    out = {}
    try:
        out["pdfplumber"] = pl_page.extract_text() or ""
    except Exception:  # noqa: BLE001
        out["pdfplumber"] = None
    try:
        out["pypdfium2"] = pdoc[i].get_textpage().get_text_range() if pdoc is not None else None
    except Exception:  # noqa: BLE001
        out["pypdfium2"] = None
    if fz is not None:
        try:
            out["pymupdf"] = fz[i].get_text() or ""
        except Exception:  # noqa: BLE001
            out["pymupdf"] = None
    return out


def verdict(raw: dict) -> dict:
    """文字層判定:回 {status, tier, agree[], ref(正規化文字,只在本行程用,不寫出), sha, pairs{}}。"""
    ne = {k: norm(v) for k, v in raw.items() if v is not None}
    got = {k: v for k, v in ne.items() if v}
    pairs = {}
    ks = sorted(got)
    for x in range(len(ks)):
        for y in range(x + 1, len(ks)):
            pairs["%s~%s" % (ks[x], ks[y])] = f1(got[ks[x]], got[ks[y]])
    if not got:
        return {"status": "NO_TEXT", "tier": None, "agree": [], "ref": "", "sha": "", "pairs": pairs}
    clean = {k: v for k, v in got.items() if PRIOR.garbled(raw[k]) == 0}
    best, how = [], ""
    for k in clean:                                        # 序列完全一致的最大群
        grp = [j for j in clean if clean[j] == clean[k]]
        if len(grp) > len(best):
            best, how = grp, "VERIFIED"
    if len(best) < 2:
        for k in clean:                                    # 字元多重集一致(順序不同)
            grp = [j for j in clean if Counter(clean[j]) == Counter(clean[k])]
            if len(grp) > len(best):
                best, how = grp, "VERIFIED_SET"
    if len(best) >= 2:
        ref = clean["pdfplumber"] if "pdfplumber" in best else clean[best[0]]
        return {"status": how, "tier": "T0" if "pdfplumber" in best else "T1", "agree": sorted(best), "ref": ref, "sha": sha16(ref), "pairs": pairs}
    near = [p for p, v in pairs.items() if v >= F1_NEAR and all(k in clean for k in p.split("~"))]
    if near:
        a = near[0].split("~")[0]
        return {"status": "NEAR", "tier": "T0" if a == "pdfplumber" else "T1", "agree": near[0].split("~"), "ref": clean[a], "sha": sha16(clean[a]), "pairs": pairs}
    if clean:                                              # 文字層互相不一致:交 OCR 當第二證人仲裁(fidelity 迴圈裡做)
        return {"status": "ARBITRATE", "tier": None, "agree": [], "ref": "", "sha": "", "pairs": pairs, "cands": clean}
    return {"status": "CONFLICT", "tier": None, "agree": [], "ref": "", "sha": "", "pairs": pairs}


# OCR 仲裁門檻(本版量測用;量完依數字調,寫進結果檔以便重算)
ARB_MIN, ARB_MARGIN = 0.60, 0.20            # 多個候選:最佳字元 F1 ≥ 0.60 且領先第二名 ≥ 0.20
ARB_SINGLE_CHAR, ARB_SINGLE_NUM = 0.70, 0.995   # 只有一個候選:字元 F1 ≥ 0.70 且數字 F1 ≥ 0.995


def arbitrate(cands: dict, raw: dict, ocr_text: str) -> tuple:
    """回 (勝出者或 None, 各候選字元 F1, 勝出者數字 F1)。OCR 不是答案,只用來挑出跟畫面一致的那一份文字層。"""
    t = norm(ocr_text)
    sc = {k: f1(v, t) for k, v in cands.items()}
    rk = sorted(sc, key=sc.get, reverse=True)
    best = rk[0]
    nf = f1(nums(raw[best]), nums(ocr_text))
    if len(rk) >= 2:
        win = sc[best] >= ARB_MIN and sc[best] - sc[rk[1]] >= ARB_MARGIN
    else:
        win = sc[best] >= ARB_SINGLE_CHAR and nf >= ARB_SINGLE_NUM
    return (best if win else None), sc, nf


# ---- OCR(前版隔離橋;沒有就本行程 rapidocr)----
_INPROC = {}


def ocr_mode() -> str:
    if PRIOR._ocr_ready():
        return "bridge"
    home = Path(os.environ.get("VIA_ENVS_HOME") or (Path.home() / "envs")) / "vrn2_ocr"
    py = home / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    br = home / "VRN2_OCRBridge_v0100.py"
    if py.exists() and br.exists():
        os.environ["VIA_VRN2_OCR_PY"], os.environ["VIA_VRN2_OCR_BRIDGE"] = str(py), str(br)
        return "bridge"
    if importlib.util.find_spec("rapidocr_onnxruntime") is not None:
        return "inproc"
    return ""


def ocr_images(images: list, mode: str) -> dict:
    if mode == "bridge":
        return PRIOR.ocr_bridge(images)
    if mode == "inproc":
        if "eng" not in _INPROC:
            from rapidocr_onnxruntime import RapidOCR
            _INPROC["eng"] = RapidOCR()
        res = []
        for p in images:
            r, _ = _INPROC["eng"](str(p))
            res.append({"image": str(p), "lines": [{"box": [[float(a), float(b)] for a, b in x[0]], "text": str(x[1]), "score": float(x[2])} for x in (r or [])]})
        return {"engine": "rapidocr_onnxruntime(本行程)", "results": res}
    return {"error": "OCR 未就緒(沒有隔離橋,主環境也沒有 rapidocr_onnxruntime)"}


def rungs(spec: str) -> list:
    return [(int(x.strip().rstrip("p")), x.strip().endswith("p")) for x in (spec or "").split(",") if x.strip().rstrip("p").isdigit()]


def render(pdoc, i: int, dpi: int, prep: bool, dst: Path) -> Path:
    from PIL import ImageFilter, ImageOps
    im = pdoc[i].render(scale=dpi / 72.0).to_pil().convert("L")
    if prep:
        im = ImageOps.autocontrast(im, cutoff=1).filter(ImageFilter.SHARPEN)
    im.save(dst)
    return dst


def ocr_rung(pdoc, i: int, dpi: int, prep: bool, mode: str, sp: Path) -> dict:
    t0 = time.time()
    png = render(pdoc, i, dpi, prep, sp / ("fid_%d_%d_%d.png" % (os.getpid(), i, dpi)))
    o = ocr_images([png], mode)
    try:
        png.unlink()
    except OSError:
        pass
    if o.get("error"):
        return {"rung": "%d%s" % (dpi, "p" if prep else ""), "error": o["error"][:120], "secs": round(time.time() - t0, 2)}
    ls = (o.get("results") or [{}])[0].get("lines") or []
    txt = "\n".join(x["text"] for x in ls)
    return {"rung": "%d%s" % (dpi, "p" if prep else ""), "text": txt, "conf": round(sum(x["score"] for x in ls) / max(1, len(ls)), 3),
            "chars": len(norm(txt)), "secs": round(time.time() - t0, 2), "engine": o.get("engine", "")}


# ---- 量測 ----
def fidelity(indir: Path, rep: Path, all_pages: bool = False, ladder: str = "", calib: int = 2, limit: int = 0) -> dict:
    import pdfplumber
    import pypdfium2 as pdfium
    try:
        import fitz  # PyMuPDF(有裝才當第三方)
    except Exception:  # noqa: BLE001
        fitz = None
    lad = rungs(ladder or os.environ.get("VIA_VRN2_OCR_LADDER_CALIB") or DEFAULT_LADDER)
    mode = ocr_mode()
    sp = PRIOR._spill()
    files = sorted(p for p in Path(indir).glob("*.pdf"))[: (limit or None)]
    docs, names, calib_rows = [], {}, []
    t_all = time.time()
    print("[fidelity] %s · %d 份 PDF · 頁 = %s · OCR = %s · 階梯 %s" % (TAG, len(files), "全部" if all_pages else "第一頁 + 財報頁",
          mode or "未就緒", ",".join("%d%s" % (d, "p" if p else "") for d, p in lad)), flush=True)
    for n, f in enumerate(files, 1):
        if n % 10 == 1 and n > 1:
            print("[fidelity] 進度 %d/%d · 已跑 %.0fs" % (n - 1, len(files), time.time() - t_all), flush=True)
        sha = hashlib.sha1(f.read_bytes()).hexdigest()
        did = "D%03d·%s" % (n, sha[:10])
        names[did] = f.name
        doc = {"doc": did, "pages": [], "secs": 0.0}
        t0 = time.time()
        try:
            with pdfplumber.open(str(f)) as pdf:
                pdoc = pdfium.PdfDocument(str(f))
                fz = fitz.open(str(f)) if fitz else None
                idx = list(range(len(pdf.pages))) if all_pages else [0] + PRIOR.fin_pages(pdf, pdoc)
                doc["npages"] = len(pdf.pages)
                used = 0
                for i in idx:
                    raw = layers(pdf.pages[i], pdoc, i, fz)
                    v = verdict(raw)
                    pg = {"pno": i + 1, "status": v["status"], "tier": v["tier"], "agree": v["agree"], "sha": v["sha"], "chars": len(v["ref"]),
                          "pairs": v["pairs"], "ocr": []}
                    if v["status"] == "ARBITRATE":
                        for dpi, prep in (lad if mode else []):    # 輕到重:哪一階先能仲裁就停
                            r = ocr_rung(pdoc, i, dpi, prep, mode, sp)
                            t = r.pop("text", None)
                            if t is not None:
                                w, sc, nf = arbitrate(v["cands"], raw, t)
                                r.update(use="arbitrate", cand_f1=sc, winner=w, num_f1=nf)
                            pg["ocr"].append(r)
                            if t is not None and w:
                                ref = v["cands"][w]
                                pg.update(status="VERIFIED_OCR", tier="T0" if w == "pdfplumber" else "T1", agree=[w, "ocr@" + r["rung"]], sha=sha16(ref), chars=len(ref))
                                break
                        if pg["status"] == "ARBITRATE":
                            pg.update(status="CONFLICT", tier="T4")
                    elif mode and v["status"] in ("VERIFIED", "VERIFIED_SET", "NEAR") and used < calib:
                        used += 1
                        rn = nums(v["ref"])
                        for dpi, prep in lad:
                            r = ocr_rung(pdoc, i, dpi, prep, mode, sp)
                            t = r.pop("text", None)             # OCR 原文只在本行程比對,不寫出
                            if t is not None:
                                r["char_f1"], r["num_f1"], r["use"] = f1(v["ref"], norm(t)), f1(rn, nums(t)), "calib"
                            pg["ocr"].append(r)
                            calib_rows.append(dict(r, doc=did, pno=i + 1))
                    elif mode and v["status"] in ("NO_TEXT", "CONFLICT"):
                        prev = None
                        for dpi, prep in lad:
                            r = ocr_rung(pdoc, i, dpi, prep, mode, sp)
                            t = r.pop("text", None)
                            if t is not None and prev is not None:
                                r["agree_prev"] = f1(norm(prev), norm(t))
                            pg["ocr"].append(r)
                            if t is not None and prev is not None and r["agree_prev"] >= F1_AGREE:
                                pg["status"], pg["tier"], pg["sha"] = "CONSENSUS", "T2" if len(pg["ocr"]) <= 2 else "T3", sha16(norm(t))
                                break
                            prev = t if t is not None else prev
                        if pg["status"] != "CONSENSUS":
                            pg["tier"] = "T4"
                    elif v["status"] in ("NO_TEXT", "CONFLICT"):
                        pg["tier"] = "T4"
                    doc["pages"].append(pg)
                    print("  %s p%d %s %s%s%s" % (did, i + 1, pg["status"], pg["tier"] or "-",
                          "".join(" · %s 字F1 %.3f 數F1 %.3f %.1fs" % (r["rung"], r.get("char_f1", 0), r.get("num_f1", 0), r["secs"]) for r in pg["ocr"] if "char_f1" in r),
                          "".join(" · 仲裁 %s → %s %.1fs" % (r["rung"], r.get("winner") or "未分", r["secs"]) for r in pg["ocr"] if r.get("use") == "arbitrate")), flush=True)
                if fz is not None:
                    fz.close()
                pdoc.close()
        except Exception as exc:  # noqa: BLE001  單檔失敗照實記,不中斷
            doc["error"] = "%s: %s" % (type(exc).__name__, str(exc)[:160])
            print("  %s 失敗 %s" % (did, doc["error"]), flush=True)
        doc["secs"] = round(time.time() - t0, 2)
        docs.append(doc)
    summary = summarize(docs, calib_rows, lad, mode)
    summary["secs"] = round(time.time() - t_all, 1)
    out = {"engine": TAG, "prior": PRIOR_PATH.name, "ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "input_files": len(files), "ocr_mode": mode,
           "ladder": [("%d%s" % (d, "p" if p else "")) for d, p in lad], "summary": summary, "docs": docs}
    od = Path(rep) / "p1view"
    od.mkdir(parents=True, exist_ok=True)
    (od / "FIDELITY_latest.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    (od / "FIDELITY_names_local.json").write_text(json.dumps(names, ensure_ascii=False, indent=1), encoding="utf-8")
    (od / "FIDELITY_latest.txt").write_text("\n".join(report_lines(out)) + "\n", encoding="utf-8")
    return out


def summarize(docs: list, rows: list, lad: list, mode: str) -> dict:
    pages = [p for d in docs for p in d["pages"]]
    st, tier = Counter(p["status"] for p in pages), Counter(p["tier"] or "-" for p in pages)
    per = {}
    for d, p in lad:
        k = "%d%s" % (d, "p" if p else "")
        rs = [r for r in rows if r.get("rung") == k and "char_f1" in r]
        if rs:
            per[k] = {"n": len(rs), "char_f1_median": round(statistics.median(r["char_f1"] for r in rs), 4),
                      "num_f1_median": round(statistics.median(r["num_f1"] for r in rs), 4),
                      "num_exact_ratio": round(sum(1 for r in rs if r["num_f1"] >= 1.0) / len(rs), 3),
                      "secs_mean": round(statistics.mean(r["secs"] for r in rs), 2)}
    light = next((k for k in per if per[k]["num_f1_median"] >= F1_NEAR and per[k]["char_f1_median"] >= 0.98), None)
    arb = Counter(p["agree"][1].split("@", 1)[1] for p in pages if p["status"] == "VERIFIED_OCR")
    errs = sum(1 for d in docs if d.get("error"))
    lamp = "RED" if errs else ("YELLOW" if (not mode or st.get("CONFLICT") or tier.get("T4") or not pages) else "GREEN")
    return {"lamp": lamp, "docs": len(docs), "doc_errors": errs, "pages": len(pages), "status": dict(st), "tier": dict(tier),
            "verified_ratio": round((st.get("VERIFIED", 0) + st.get("VERIFIED_SET", 0)) / max(1, len(pages)), 4),
            "verified_any_ratio": round(sum(st.get(k, 0) for k in ("VERIFIED", "VERIFIED_SET", "VERIFIED_OCR", "CONSENSUS")) / max(1, len(pages)), 4),
            "arbitration_won_at": dict(arb), "thresholds": {"near": F1_NEAR, "agree": F1_AGREE, "arb_min": ARB_MIN, "arb_margin": ARB_MARGIN,
                                                           "arb_single_char": ARB_SINGLE_CHAR, "arb_single_num": ARB_SINGLE_NUM},
            "ocr_per_rung": per, "light_enough": light, "ocr_mode": mode or "未就緒(SKIP ≠ 綠)"}


def report_lines(out: dict) -> list:
    s = out["summary"]
    L = ["# VRN 擷取還原量測(fidelity)· %s · %s" % (out["engine"], out["ts"]),
         "[%s] %d 份 · %d 頁 · 錯 %d · 文字層互相一致 %.1f%% · 含 OCR 仲裁 / 共識後可驗證 %.1f%% · 耗時 %ss" % (s["lamp"], s["docs"], s["pages"], s["doc_errors"],
                                                                                   100 * s["verified_ratio"], 100 * s["verified_any_ratio"], s.get("secs")),
         "OCR 仲裁在哪一階就分出勝負:%s" % (" · ".join("%s %d 頁" % kv for kv in sorted(s["arbitration_won_at"].items())) or "—"),
         "判定:%s" % " · ".join("%s %d" % kv for kv in sorted(s["status"].items())),
         "最低夠用的層:%s" % " · ".join("%s %d" % kv for kv in sorted(s["tier"].items())),
         "OCR:%s · 階梯 %s" % (s["ocr_mode"], ",".join(out["ladder"]))]
    for k, v in s["ocr_per_rung"].items():
        L.append("  %s · %d 頁 · 字元 F1 中位 %.4f · 數字 F1 中位 %.4f · 數字全對 %.0f%% · 平均 %.2fs/頁" % (k, v["n"], v["char_f1_median"], v["num_f1_median"], 100 * v["num_exact_ratio"], v["secs_mean"]))
    L.append("輕型夠用的最低一階:%s" % (s["light_enough"] or "沒有一階達標(數字 F1 ≥ 0.995 且字元 F1 ≥ 0.98)"))
    for d in out["docs"]:
        bad = [p for p in d["pages"] if p["status"] in ("CONFLICT", "NO_TEXT") and p.get("tier") == "T4"]
        if d.get("error") or bad:
            L.append("  %s %s" % (d["doc"], d.get("error") or "要人工:" + ",".join("p%d %s" % (p["pno"], p["status"]) for p in bad)))
    L = L[:299]
    L.append("NEXT: %s" % ("依各階數字定輕 / 重切換點,接進 ENG397 正常流程(需要 OCR 的區塊先輕型,兩階一致就停)" if s["lamp"] != "RED" else "先看失敗的檔"))
    return L


# ---- 自測(全在暫存夾造資料;不吃本機狀態)----
def _image_only_pdf(src: Path, dst: Path) -> Path:
    import pypdfium2 as pdfium
    d = pdfium.PdfDocument(str(src))
    im = d[0].render(scale=200 / 72.0).to_pil().convert("RGB")
    d.close()
    im.save(dst, "PDF", resolution=200.0)
    return dst


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print("[計] %s 自測開始(本版 7 項 · 前版 %s)" % (TAG, PRIOR_PATH.name), flush=True)
    chk("T1 前版 = v0129;擷取入口(run · garbled · fin_pages · ocr_bridge)原樣轉前版", PRIOR_PATH.name == "VRN_ENG397_P1Segment_v0129.py"
        and run is PRIOR.run and __getattr__("garbled") is PRIOR.garbled and __getattr__("ocr_bridge") is PRIOR.ocr_bridge)
    v = [verdict({"pdfplumber": "營收 1,234 億\n毛利率 45.6%", "pypdfium2": "營收 1,234 億 毛利率 45.6%"})["status"],
         verdict({"pdfplumber": "A B", "pypdfium2": "B A"})["status"],
         verdict({"pdfplumber": "營收 1,234", "pypdfium2": "營收 1,235"})["status"],
         verdict({"pdfplumber": "", "pypdfium2": ""})["status"],
         verdict({"pdfplumber": "(cid:12)(cid:13)", "pypdfium2": "(cid:12)(cid:13)"})["status"]]
    chk("T2 文字層判定:序列一致 VERIFIED · 只差順序 VERIFIED_SET · 差一字不算驗證 · 沒字 NO_TEXT · 亂碼一致也不算驗證",
        v[:2] == ["VERIFIED", "VERIFIED_SET"] and v[2] == "ARBITRATE" and v[3] == "NO_TEXT" and v[4] == "CONFLICT", v)
    chk("T3 多重集 F1:相同 1.0 · 全不同 0.0 · 順序無關", f1("abc", "cba") == 1.0 and f1("abc", "xyz") == 0.0 and f1("", "") == 1.0
        and nums("營收 1,234 億、-5.6%") == ["1234", "5.6"])
    td = Path(tempfile.mkdtemp(prefix="eng397f-"))
    saved = {k: os.environ.get(k) for k in ("VIA_SPILL_DIR",)}
    try:
        os.environ["VIA_SPILL_DIR"] = str(td / "spill")
        indir = td / "in"
        indir.mkdir()
        PRIOR._fixture_pdf(indir / "fixture.pdf")
        mode = ocr_mode()
        out = fidelity(indir, td / "rep", calib=1, ladder="200,325p")
        p1 = out["docs"][0]["pages"][0]
        if mode:      # 合成檔用非內嵌 CID 字型:pdfplumber / PyMuPDF 解成合法但錯的字,只有 pypdfium2 對 → 要靠 OCR 仲裁
            chk("T4 合成 PDF 第一頁:文字層不一致 → OCR 仲裁選中 pypdfium2(VERIFIED_OCR · T1 · 有雜湊)",
                p1["status"] == "VERIFIED_OCR" and p1["agree"][0] == "pypdfium2" and p1["tier"] == "T1" and len(p1["sha"]) == 16, p1)
        else:
            chk("T4 合成 PDF 第一頁:沒有 OCR 可仲裁 → 照實 CONFLICT · T4(不冒充已驗證)", p1["status"] == "CONFLICT" and p1["tier"] == "T4", p1)
        raw = (td / "rep" / "p1view" / "FIDELITY_latest.json").read_text(encoding="utf-8")
        import pdfplumber
        with pdfplumber.open(str(indir / "fixture.pdf")) as pdf:
            body = norm(pdf.pages[0].extract_text() or "")
        leak = [body[k:k + 12] for k in range(0, max(0, len(body) - 12), 12) if body[k:k + 12] and body[k:k + 12] in raw]
        chk("T5 輸出不含內文(12 字片段 0 處命中)· 不含檔名 · txt 以 NEXT: 結尾", not leak and "fixture.pdf" not in raw
            and (td / "rep" / "p1view" / "FIDELITY_latest.txt").read_text(encoding="utf-8").rstrip().splitlines()[-1].startswith("NEXT:"), leak[:2])
        _image_only_pdf(indir / "fixture.pdf", indir / "scan.pdf")
        out2 = fidelity(indir, td / "rep2", calib=1, ladder="200,325p")
        sc = next(d for d in out2["docs"] if d["doc"] != out["docs"][0]["doc"])["pages"][0]
        if mode:
            r0 = p1["ocr"][0] if p1["ocr"] else {}
            chk("T6 OCR 就緒(%s):仲裁列有各候選字元 F1 與勝出者數字 F1;輕階分出勝負就不再跑重階;掃描頁走 OCR 階梯(CONSENSUS 或 T4)" % mode,
                r0.get("use") == "arbitrate" and set(r0.get("cand_f1", {})) >= {"pypdfium2"} and "num_f1" in r0 and len(p1["ocr"]) == 1
                and sc["status"] in ("CONSENSUS", "NO_TEXT") and sc["tier"] in ("T2", "T3", "T4") and sc["ocr"], (r0, sc))
        else:
            chk("T6 OCR 未就緒:掃描頁照實 NO_TEXT · T4 · 總燈不給綠(SKIP ≠ 綠)", sc["status"] == "NO_TEXT" and sc["tier"] == "T4" and out2["summary"]["lamp"] != "GREEN", sc)
    finally:
        for k, val in saved.items():
            if val is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = val
        import shutil
        shutil.rmtree(td, ignore_errors=True)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("T7 檔面:加速器橋 · 零 TA-Lib · 不出網 · 本行程不寫同意閘", "[VIA:ACCEL-BRIDGE:v0100]" in src and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"^\s*(import|from)\s+(requests|urllib|httpx|socket)\b", src, re.M) and not re.search(r"os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", src))
    n = sum(ok)
    print("[計] %s 自測 %d/%d · %s" % (TAG, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    print("[前版] %s 自測" % PRIOR_PATH.name, flush=True)
    rc_prior = selftest_prior()
    print("[計] %s 自測 OK %d · FAIL %d · 前版 rc=%s" % (TAG, n, len(ok) - n, rc_prior), flush=True)
    return 0 if n == len(ok) and rc_prior == 0 else 1


def _opt(a: list, k: str, d=None):
    return a[a.index(k) + 1] if k in a and a.index(k) + 1 < len(a) else d


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["fidelity"]:
        pos = [x for i, x in enumerate(a[1:], 1) if not x.startswith("--") and a[i - 1] not in ("--rep", "--ladder", "--calib", "--limit")]
        o = fidelity(Path(pos[0]) if pos else Path(r"C:\測試樣本報告"), Path(_opt(a, "--rep", str(HERE / "_p1view_out"))), "--all" in a,
                     _opt(a, "--ladder", ""), int(_opt(a, "--calib", 2)), int(_opt(a, "--limit", 0)))
        print("\n".join(report_lines(o)))
        raise SystemExit({"GREEN": 0, "YELLOW": 2}.get(o["summary"]["lamp"], 1))
    if "--shard" in a:
        sys.exit(PRIOR._shard_main(a[a.index("--shard") + 1]))
    if "--selftest" in a[:1]:
        raise SystemExit(selftest())
    print(json.dumps(run(Path(a[0]) if a else Path(r"C:\測試樣本報告"), HERE / "_p1view_out"), ensure_ascii=False, default=str)[:1500])
