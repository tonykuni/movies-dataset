#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_ENG397_P1Segment v0131 — 薄尾(v0129 · v0130 一字不動):fidelity 兩處量測錯修正(PR #733 Codex P2 ×2)

① 校準的數字 F1:v0130 從「正規化後的參照文字」切數字 token;正規化去掉所有空白 / 換行,表格相鄰格
   「100 200\n300 400」會黏成一個「100200300400」,OCR 四個數字全對也得 0 分 → 壓低 num_f1 / 數字全對比例 / 輕型建議。
   本版改從「勝出那一家的原文」切數字(字元 F1 照舊用正規化文字比)。
② 無文字層頁的 OCR 共識:v0130 兩階都讀到空字串時 f1("", "") = 1.0 → 判 CONSENSUS · T2,掃描頁一個字都沒讀到卻算可驗證。
   本版要求兩階正規化後都至少 MIN_CONSENSUS_CHARS 個字才算共識;讀不到 = T4(人工)。
其餘(三層證據 · 仲裁 · 輸出不含內文與檔名)照 v0130。擷取流程(run / p1view)照 v0129。
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
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_ENG397_P1Segment"
TAG = "VRN_ENG397_P1Segment v0131"


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
run = PRIOR.run
(norm, sha16, f1, nums, digits, layers, verdict, arbitrate, ocr_mode, rungs, ocr_rung, summarize, report_lines) = (
    PRIOR.norm, PRIOR.sha16, PRIOR.f1, PRIOR.nums, PRIOR.digits, PRIOR.layers, PRIOR.verdict, PRIOR.arbitrate, PRIOR.ocr_mode,
    PRIOR.rungs, PRIOR.ocr_rung, PRIOR.summarize, PRIOR.report_lines)
DEFAULT_LADDER, F1_AGREE = PRIOR.DEFAULT_LADDER, PRIOR.F1_AGREE
MIN_CONSENSUS_CHARS = 10        # 兩階都至少讀到這麼多字(正規化後)才算共識


def ref_raw(v: dict, raw: dict) -> str:
    """共識參照的原文(保留空白 / 換行,數字 token 的界線才在):agree 裡第一家正規化後等於參照的那份原文。"""
    for k in v.get("agree") or []:
        if raw.get(k) is not None and norm(raw[k]) == v["ref"]:
            return raw[k]
    for k in v.get("agree") or []:
        if raw.get(k):
            return raw[k]
    return v["ref"]


def calib_scores(ref_norm: str, ref_original: str, ocr_text: str) -> dict:
    """已驗證頁的 OCR 還原率:字元 F1 用正規化文字;數字 token F1 用原文切;數字字元 F1 只看數字。"""
    return {"char_f1": f1(ref_norm, norm(ocr_text)), "num_f1": f1(nums(ref_original), nums(ocr_text)),
            "digit_f1": f1(digits(ref_original), digits(ocr_text)), "use": "calib"}


def consensus_ok(prev: str, cur: str, agree: float) -> bool:
    """兩階 OCR 一致且都真的讀到字;空對空不算共識。"""
    return agree >= F1_AGREE and len(norm(prev)) >= MIN_CONSENSUS_CHARS and len(norm(cur)) >= MIN_CONSENSUS_CHARS


def fidelity(indir: Path, rep: Path, all_pages: bool = False, ladder: str = "", calib: int = 2, limit: int = 0) -> dict:
    import pdfplumber
    import pypdfium2 as pdfium
    try:
        import pymupdf as fitz  # PyMuPDF(有裝才當第三方;新名稱,不觸發 fitz 舊名的棄用警告)
    except Exception:  # noqa: BLE001
        try:
            import fitz  # 舊版 PyMuPDF 只有 fitz 這個名字
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
                        rr = ref_raw(v, raw)                     # v0131:數字從原文切(正規化去掉空白會把相鄰格黏成一個數)
                        for dpi, prep in lad:
                            r = ocr_rung(pdoc, i, dpi, prep, mode, sp)
                            t = r.pop("text", None)             # OCR 原文只在本行程比對,不寫出
                            if t is not None:
                                r.update(calib_scores(v["ref"], rr, t))
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
                            if t is not None and prev is not None and consensus_ok(prev, t, r["agree_prev"]):
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
            msg = str(exc).replace(str(f), did).replace(f.name, did).replace(str(Path(indir)), "<輸入夾>")   # 錯誤訊息不帶檔名 / 路徑
            doc["error"] = "%s: %s" % (type(exc).__name__, msg[:160])
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




def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print("[計] %s 自測開始(本版 5 項 · 前版 %s)" % (TAG, PRIOR_PATH.name), flush=True)
    chk("T1 前版 = v0130;擷取入口與 v0130 的判定函式原樣沿用", PRIOR_PATH.name == "VRN_ENG397_P1Segment_v0130.py" and run is PRIOR.run and verdict is PRIOR.verdict)
    raw = {"pdfplumber": "營收 100 200\n毛利 300 400", "pypdfium2": "營收 100 200\r\n毛利 300 400"}
    v = verdict(raw)
    rr = ref_raw(v, raw)
    sc = calib_scores(v["ref"], rr, "營收 100 200\n毛利 300 400")
    old = f1(nums(v["ref"]), nums("營收 100 200\n毛利 300 400"))
    chk("T2 Codex 重現:表格相鄰格 · OCR 全對 → 數字 F1 = 1.0(v0130 從正規化文字切得 %.2f)" % old,
        v["status"] == "VERIFIED" and sc["num_f1"] == 1.0 and sc["digit_f1"] == 1.0 and sc["char_f1"] == 1.0 and old < 1.0, (v["status"], sc, old))
    chk("T3 共識要真的讀到字:空對空(f1 = 1.0)不算 · 兩邊都有字且一致才算 · 一致但太短也不算",
        f1("", "") == 1.0 and not consensus_ok("", "", 1.0) and consensus_ok("營收一二三四五六七八九十", "營收一二三四五六七八九十", 1.0)
        and not consensus_ok("營收", "營收", 1.0))
    td = Path(tempfile.mkdtemp(prefix="eng397g-"))
    saved = {"VIA_SPILL_DIR": os.environ.get("VIA_SPILL_DIR")}
    keep_rung = globals()["ocr_rung"]
    try:
        os.environ["VIA_SPILL_DIR"] = str(td / "spill")
        indir = td / "in"
        indir.mkdir()
        PRIOR.PRIOR._fixture_pdf(td / "fx.pdf")
        PRIOR._image_only_pdf(td / "fx.pdf", indir / "scan.pdf")
        globals()["ocr_rung"] = lambda pdoc, i, dpi, prep, mode, sp: {"rung": "%d%s" % (dpi, "p" if prep else ""), "text": "", "conf": 0.0, "chars": 0, "secs": 0.0}
        keep_mode = globals()["ocr_mode"]
        globals()["ocr_mode"] = lambda: "inproc"
        try:
            out = fidelity(indir, td / "rep", ladder="200,325p")
        finally:
            globals()["ocr_mode"] = keep_mode
        pg = out["docs"][0]["pages"][0]
        chk("T4 Codex 重現:掃描頁兩階 OCR 都讀不到字 → 不是 CONSENSUS · 是 T4 · 總燈不給綠",
            pg["status"] == "NO_TEXT" and pg["tier"] == "T4" and len(pg["ocr"]) == 2 and out["summary"]["lamp"] != "GREEN"
            and out["summary"]["verified_any_ratio"] == 0.0, (pg, out["summary"]["lamp"]))
    finally:
        globals()["ocr_rung"] = keep_rung
        for k, val in saved.items():
            if val is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = val
        import shutil
        shutil.rmtree(td, ignore_errors=True)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("T5 檔面:加速器橋 · 零 TA-Lib · 不出網 · 本行程不寫同意閘", "[VIA:ACCEL-BRIDGE:v0100]" in src and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"^\s*(import|from)\s+(requests|urllib|httpx|socket)\b", src, re.M) and not re.search(r"os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", src))
    n = sum(ok)
    print("[計] %s 自測 %d/%d · %s" % (TAG, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    print("[前版] %s 自測" % PRIOR_PATH.name, flush=True)
    rc_prior = PRIOR.selftest()
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
        sys.exit(PRIOR.PRIOR._shard_main(a[a.index("--shard") + 1]))
    if "--selftest" in a[:1]:
        raise SystemExit(selftest())
    print(json.dumps(run(Path(a[0]) if a else Path(r"C:\測試樣本報告"), HERE / "_p1view_out"), ensure_ascii=False, default=str)[:1500])
