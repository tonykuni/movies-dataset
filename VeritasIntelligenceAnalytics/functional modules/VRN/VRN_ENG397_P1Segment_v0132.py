#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_ENG397_P1Segment v0132 — 薄尾(v0129–v0131 一字不動):隔離橋 OCR 一頁一批(不再每張圖起一個行程)

操作員 2026-11-24 主機實跑 fidelity:測試樣本報告 2507 秒才 13 份(約 190 秒 / 份;同類報告容器約 12 秒 / 份),「速度太慢」。
  量到的原因:主機有隔離環境 vrn2_ocr → OCR 走「橋」(v0129 ocr_bridge):v0130 的 ocr_rung 每一階(200 · 325p · 400p)
  各算一張圖、各起一個隔離 Python 子行程,每個子行程都重新載入 OCR 模型;容器沒有隔離環境,走本行程 rapidocr(模型只載一次)。
  一頁要跑三階 = 起三次行程、載三次模型。
本版:橋模式下,某一頁第一次要 OCR 時,把這一頁整條階梯的圖一次算好、一次丟給橋(橋本來就收圖片清單),
  後面幾階直接取結果;換頁就清掉。每階的結果(字 · 信心 · 字數)跟一張一張跑相同;耗時欄 = 這批平均。
  本行程模式(rapidocr)不變。量測方法、判定、輸出格式(只有雜湊與數字)都照 v0131。不 import 他系統。零 TA-Lib。
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
TAG = "VRN_ENG397_P1Segment v0132"


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
norm, rungs, report_lines, render, ocr_images = PRIOR.norm, PRIOR.rungs, PRIOR.report_lines, PRIOR.render, PRIOR.ocr_images
DEFAULT_LADDER = PRIOR.DEFAULT_LADDER
_OCR_RUNG0 = PRIOR.ocr_rung                               # v0130 一張一張跑的那支(本行程模式照用)
_FID0 = PRIOR.fidelity                                    # v0131 量測
_LAD = {"lad": None}
_CACHE = {"key": None, "res": {}}
STATS = {"bridge_calls": 0, "images": 0}
BRIDGE_SECS_PER_IMAGE = 240                               # v0129 ocr_bridge 一張圖的上限


def _rung_name(dpi: int, prep: bool) -> str:
    return "%d%s" % (dpi, "p" if prep else "")


def _batch(pdoc, i: int, want: list, sp: Path) -> dict:
    """一頁的多階一次算圖、一次丟橋 → {(dpi, prep): 跟 v0130 ocr_rung 同格式的結果}。"""
    t0 = time.time()
    pngs = [render(pdoc, i, dpi, prep, Path(sp) / ("fid_%d_%d_%s.png" % (os.getpid(), i, _rung_name(dpi, prep)))) for dpi, prep in want]
    try:
        o = PRIOR.ocr_bridge(pngs, timeout=BRIDGE_SECS_PER_IMAGE * len(pngs))   # 上限照前版每張 240 秒 × 張數
    finally:
        for p in pngs:
            try:
                p.unlink()
            except OSError:
                pass
    STATS["bridge_calls"] += 1
    STATS["images"] += len(pngs)
    secs = round((time.time() - t0) / max(1, len(want)), 2)
    if o.get("error"):
        return {k: {"rung": _rung_name(*k), "error": o["error"][:120], "secs": secs} for k in want}
    res = o.get("results") or []
    by_img = {str(r.get("image")): r for r in res if isinstance(r, dict)}
    out = {}
    for n, (k, png) in enumerate(zip(want, pngs)):
        r = by_img.get(str(png)) or (res[n] if n < len(res) else {})
        ls = r.get("lines") or []
        txt = "\n".join(x["text"] for x in ls)
        out[k] = {"rung": _rung_name(*k), "text": txt, "conf": round(sum(x["score"] for x in ls) / max(1, len(ls)), 3),
                  "chars": len(norm(txt)), "secs": secs, "engine": o.get("engine", ""), "batch": len(want)}
    return out


def ocr_rung(pdoc, i: int, dpi: int, prep: bool, mode: str, sp: Path) -> dict:
    if mode != "bridge":
        return _OCR_RUNG0(pdoc, i, dpi, prep, mode, sp)
    key = (id(pdoc), i)
    if _CACHE["key"] != key:
        _CACHE.update(key=key, res={})
    k = (int(dpi), bool(prep))
    if k not in _CACHE["res"]:
        lad = _LAD["lad"] or rungs(os.environ.get("VIA_VRN2_OCR_LADDER_CALIB") or DEFAULT_LADDER)
        want = [r for r in lad if r not in _CACHE["res"]]
        if k not in want:
            want.append(k)
        _CACHE["res"].update(_batch(pdoc, i, want, sp))
    return dict(_CACHE["res"].pop(k))


def fidelity(indir: Path, rep: Path, all_pages: bool = False, ladder: str = "", calib: int = 2, limit: int = 0) -> dict:
    _LAD["lad"] = rungs(ladder or os.environ.get("VIA_VRN2_OCR_LADDER_CALIB") or DEFAULT_LADDER)
    _CACHE.update(key=None, res={})
    try:
        return _FID0(indir, rep, all_pages, ladder, calib, limit)
    finally:
        _CACHE.update(key=None, res={})


PRIOR.ocr_rung = ocr_rung                                 # v0131 的 fidelity 叫它模組裡的 ocr_rung → 換成一頁一批


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print("[計] %s 自測開始(本版 5 項 · 前版 %s · 暫存夾 · 假橋)" % (TAG, PRIOR_PATH.name), flush=True)
    chk("T1 鏈:前版 v0131 · v0131 的 fidelity 用的 ocr_rung 換成本版 · 量測本體照前版",
        PRIOR_PATH.name == "VRN_ENG397_P1Segment_v0131.py" and PRIOR.ocr_rung is ocr_rung and _FID0 is PRIOR.fidelity
        and PRIOR.fidelity.__globals__ is vars(PRIOR))
    from PIL import Image, ImageDraw

    class Page:
        def __init__(self, n):
            self.n = n

        def render(self, scale):
            im = Image.new("L", (int(60 * scale), int(20 * scale)), 255)
            ImageDraw.Draw(im).text((2, 2), "P%d" % self.n, fill=0)
            return type("B", (), {"to_pil": lambda _s: im.convert("RGB")})()
    pdoc = [Page(0), Page(1)]
    with tempfile.TemporaryDirectory(prefix="eng397_132_") as td:
        td = Path(td)
        log = td / "spawns.txt"
        br = td / "fake_bridge.py"
        br.write_text("import json,sys,pathlib\n"
                      "pathlib.Path(%r).open('a').write('x')\n"
                      "job=json.load(open(sys.argv[1],encoding='utf-8'))\n"
                      "from PIL import Image\n"
                      "res=[{'image':p,'lines':[{'text':'w%%d h%%d'%%Image.open(p).size,'score':0.9,'box':[[0,0]]}]} for p in job['images']]\n"
                      "json.dump({'engine':'fake','results':res},open(sys.argv[2],'w',encoding='utf-8'))\n" % str(log), encoding="utf-8")
        keep_env = {k: os.environ.get(k) for k in ("VIA_VRN2_OCR_PY", "VIA_VRN2_OCR_BRIDGE")}
        os.environ["VIA_VRN2_OCR_PY"], os.environ["VIA_VRN2_OCR_BRIDGE"] = sys.executable, str(br)
        try:
            _LAD["lad"] = rungs("200,325p,400p")
            _CACHE.update(key=None, res={})
            STATS.update(bridge_calls=0, images=0)
            new = [ocr_rung(pdoc, 0, d, p, "bridge", td) for d, p in _LAD["lad"]]
            n_new = len(log.read_text()) if log.exists() else 0
            log.unlink(missing_ok=True)
            old = [_OCR_RUNG0(pdoc, 0, d, p, "bridge", td) for d, p in _LAD["lad"]]
            n_old = len(log.read_text()) if log.exists() else 0
            log.unlink(missing_ok=True)
            nxt = ocr_rung(pdoc, 1, 200, False, "bridge", td)
            n_next = len(log.read_text()) if log.exists() else 0
            pngs_left = list(td.glob("fid_*.png"))
            os.environ["VIA_VRN2_OCR_BRIDGE"] = str(td / "missing.py")
            _CACHE.update(key=None, res={})
            err = ocr_rung(pdoc, 0, 325, True, "bridge", td)
        finally:
            for k, v in keep_env.items():
                os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
            _LAD["lad"] = None
            _CACHE.update(key=None, res={})
    strip = lambda r: {k: v for k, v in r.items() if k not in ("secs", "batch")}       # noqa: E731
    chk("T2 一頁三階:新版起 1 次橋行程(舊版 3 次)· 每階的字 · 信心 · 字數跟一張一張跑一樣",
        n_new == 1 and n_old == 3 and [strip(r) for r in new] == [strip(r) for r in old] and all(r.get("batch") == 3 for r in new), (n_new, n_old, new, old))
    chk("T3 換頁重新一批(不拿上一頁的結果)· 暫存圖都刪掉", n_next == 1 and nxt["text"] == "w166 h55" and not pngs_left, (n_next, nxt, pngs_left))
    chk("T4 橋壞了:每階照 v0130 格式回 error(不崩潰、不當成讀到字)", "error" in err and err["rung"] == "325p" and "text" not in err, err)
    seen = []
    keep0 = globals()["_OCR_RUNG0"]
    try:
        globals()["_OCR_RUNG0"] = lambda *a: seen.append(a[4]) or {"rung": "200"}
        ocr_rung(pdoc, 0, 200, False, "inproc", Path("."))
    finally:
        globals()["_OCR_RUNG0"] = keep0
    src = Path(__file__).read_text(encoding="utf-8")
    chk("T5 本行程模式(rapidocr)照 v0130 一張一張跑 · 檔面:加速器橋 · 零 TA-Lib · 不出網 · 不設同意閘",
        seen == ["inproc"] and "[VIA:ACCEL-BRIDGE:v0100]" in src and not re.search(r"^\s*(import|from)\s+(talib|requests|urllib)", src, re.M)
        and not re.search(r"os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", src))
    n = sum(ok)
    print("[計] %s 自測 %d/%d · %s" % (TAG, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    print("[前版] %s 自測(ocr_rung 還原成前版的)" % PRIOR_PATH.name, flush=True)
    PRIOR.ocr_rung = _OCR_RUNG0
    try:
        rc_prior = PRIOR.selftest()
    finally:
        PRIOR.ocr_rung = ocr_rung
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
        print("[fidelity] 橋呼叫 %d 次 · 圖 %d 張" % (STATS["bridge_calls"], STATS["images"]), flush=True)
        raise SystemExit({"GREEN": 0, "YELLOW": 2}.get(o["summary"]["lamp"], 1))
    if "--selftest" in a[:1]:
        raise SystemExit(selftest())
    keep = sys.argv
    import runpy                                             # 其他動作(run · --shard)照前版原樣
    sys.argv = [str(PRIOR_PATH)] + a
    try:
        runpy.run_path(str(PRIOR_PATH), run_name="__main__")
    finally:
        sys.argv = keep
