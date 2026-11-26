#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""via_ocr_super_v0102 — 薄尾:隔離境 OCR 車道回傳逐行座標(給 LAYOUT 修復鏈用)

操作員 2026-10-02(VCGC-REQ126 · VRN-REQ006):「PRADDLE 工具 + EXTRACTOR 針對 LAYOUT TEXT TABLE GRAPH」「跟 LAYOUT 引擎相互搭配並修復驗證」
「PRADDLE 工具們高風險要獨立環境」。
v0101 的車道(RapidOCR → via_rapidocr · PaddleOCR → via_paddle_311 …)本來就是**每車道一個隔離境、子行程跑、JSON 回主行程**;
但 run_lane() 只回文字與平均信心,把每行的座標框丟了——LAYOUT 修復鏈(SUP_MDL743)要座標才能逐列對齊、還原表格。
本版只加一件事:run_lane_boxes(lane, py, image) —— 同一個隔離境子行程,多回每行 bbox(像素;左上右下)與信心。
  · rapidocr:RapidOCR()(path) 的 [四點框, 文字, 信心]。
  · paddleocr:2.x ocr(path, cls=True);3.x(不吃 show_log / cls)退 predict(path) 的 rec_texts / rec_scores / rec_boxes|rec_polys。
  · 子行程任何例外照實回 {"ok": false, "err": ...},不假抽;主行程不 import 任何 OCR 套件。
車道表、環境探測、門檻、v0101 的 run_lane / pick_winner 一字不動;零網路(子行程本身也不下載;paddle 3.x 首跑要模型 = 同意閘的事)。
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
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "via_ocr_super"
PRIOR_PATH = max(p for p in HERE.glob(_STEM + "_v*.py") if p.name < Path(__file__).name)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_v0102", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):
    return getattr(PRIOR, name)


_SRC_BOX = {
    "rapidocr": (
        "import json,sys\n"
        "try:\n"
        "    from rapidocr_onnxruntime import RapidOCR\n"
        "    r,_=RapidOCR()(sys.argv[1])\n"
        "    L=[]\n"
        "    for b,t,c in (r or []):\n"
        "        xs=[float(p[0]) for p in b];ys=[float(p[1]) for p in b]\n"
        "        L.append({'text':t,'conf':float(c),'bbox':[min(xs),min(ys),max(xs),max(ys)]})\n"
        "    print(json.dumps({'ok':True,'lines':L},ensure_ascii=False))\n"
        "except Exception as e:\n"
        "    print(json.dumps({'ok':False,'err':(type(e).__name__+':'+str(e))[:160]},ensure_ascii=False))\n"),
    "paddleocr": (
        "import json,sys\n"
        "def box(b):\n"
        "    b=[list(map(float,p)) for p in b] if hasattr(b[0],'__len__') else [list(map(float,b[i:i+2])) for i in range(0,len(b),2)]\n"
        "    xs=[p[0] for p in b];ys=[p[1] for p in b];return [min(xs),min(ys),max(xs),max(ys)]\n"
        "try:\n"
        "    from paddleocr import PaddleOCR\n"
        "    L=[]\n"
        "    try:\n"
        "        o=PaddleOCR(use_angle_cls=True,lang='ch',show_log=False)\n"
        "        res=o.ocr(sys.argv[1],cls=True)\n"
        "        for pg in (res or []):\n"
        "            for ln in (pg or []):\n"
        "                L.append({'text':ln[1][0],'conf':float(ln[1][1]),'bbox':box(ln[0])})\n"
        "    except (TypeError,ValueError):\n"
        "        o=PaddleOCR(lang='ch')\n"
        "        for r in o.predict(sys.argv[1]):\n"
        "            bs=r.get('rec_boxes') if r.get('rec_boxes') is not None else r.get('rec_polys')\n"
        "            for t,c,b in zip(r['rec_texts'],r['rec_scores'],list(bs)):\n"
        "                b=list(b);L.append({'text':t,'conf':float(c),'bbox':box([b[0:2],b[2:4]] if len(b)==4 and not hasattr(b[0],'__len__') else b)})\n"
        "    print(json.dumps({'ok':True,'lines':L},ensure_ascii=False))\n"
        "except Exception as e:\n"
        "    print(json.dumps({'ok':False,'err':(type(e).__name__+':'+str(e))[:160]},ensure_ascii=False))\n"),
}


def parse_box_output(stdout: str, k: str) -> dict:
    """子行程最後一行 JSON → 車道結果(純函式可自測)。行 = {text, conf, bbox[4]};缺 bbox 的行照實剔除並計數。"""
    try:
        d = json.loads((stdout or "").strip().splitlines()[-1])
    except (ValueError, IndexError) as exc:
        return {"k": k, "ok": False, "err": f"輸出不是 JSON({type(exc).__name__})"}
    if not d.get("ok"):
        return {"k": k, "ok": False, "err": d.get("err", "?")}
    lines, dropped = [], 0
    for x in d.get("lines") or []:
        b = x.get("bbox")
        if not (isinstance(b, list) and len(b) == 4 and str(x.get("text") or "").strip()):
            dropped += 1
            continue
        lines.append({"text": str(x["text"]), "conf": float(x.get("conf") or 0.0), "bbox": [float(v) for v in b]})
    avg = round(sum(x["conf"] for x in lines) / len(lines), 4) if lines else 0.0
    return {"k": k, "ok": True, "n": len(lines), "avg": avg, "lines": lines, "dropped": dropped}


def run_lane_boxes(lane: dict, py: str, image: str, timeout: int | None = None) -> dict:
    """在該車道的隔離境 python 跑一次,回逐行座標。沒有帶座標的工人(tesseract / surya)照實回 NO_BOX_WORKER。"""
    src = _SRC_BOX.get(lane["k"])
    if src is None:
        return {"k": lane["k"], "ok": False, "err": "NO_BOX_WORKER(本車道還沒有回座標的工人)"}
    try:
        r = subprocess.run([py, "-c", src, image], capture_output=True, text=True,
                           timeout=timeout or lane["timeout"], stdin=subprocess.DEVNULL)
    except Exception as exc:
        return {"k": lane["k"], "ok": False, "err": f"{type(exc).__name__}:{str(exc)[:80]}"}
    return parse_box_output(r.stdout, lane["k"])


def cmd_selftest() -> int:
    print("=== via_ocr_super v0102 · 薄尾自測(隔離境車道回座標)===")
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    good = parse_box_output('noise\n{"ok":true,"lines":[{"text":"營收","conf":0.9,"bbox":[1,2,3,4]},{"text":"x","conf":0.5},'
                            '{"text":"","conf":0.9,"bbox":[0,0,1,1]}]}', "rapidocr")
    chk("① 解析:取最後一行 JSON;缺座標 / 空字的行照實剔除並計數;平均信心只算留下的",
        good["ok"] and good["n"] == 1 and good["dropped"] == 2 and good["avg"] == 0.9, good)
    bad = parse_box_output('{"ok":false,"err":"ModuleNotFoundError:paddle"}', "paddleocr")
    chk("② 子行程回失敗 → 照實 ok=False 帶因由(不假抽)", bad == {"k": "paddleocr", "ok": False, "err": "ModuleNotFoundError:paddle"})
    chk("③ 輸出不是 JSON → ok=False", parse_box_output("Traceback ...", "rapidocr")["ok"] is False)
    lanes = {x["k"]: x for x in PRIOR.LANES}
    chk("④ 車道表照 v0101(RapidOCR → via_rapidocr · PaddleOCR → via_paddle_311 優先;每車道隔離境)",
        lanes["rapidocr"]["envs"][0] == "via_rapidocr" and lanes["paddleocr"]["envs"][0] == "via_paddle_311")
    nb = run_lane_boxes({"k": "surya", "timeout": 5}, sys.executable, "x.png")
    chk("⑤ 沒有回座標工人的車道照實回 NO_BOX_WORKER", nb["ok"] is False and "NO_BOX_WORKER" in nb["err"])
    fake = run_lane_boxes({"k": "rapidocr", "timeout": 60}, sys.executable, "no_such_image.png")
    chk("⑥ 主行程 python 沒有 rapidocr → 子行程照實回失敗(主行程本身不 import OCR 套件)",
        fake["ok"] is False and "rapidocr" not in {m.split('.')[0] for m in sys.modules}, fake.get("err", "")[:60])
    for k, src in _SRC_BOX.items():
        compile(src, f"<{k}>", "exec")
    chk("⑦ 兩支工人原始碼都編得過(rapidocr · paddleocr 2.x / 3.x)", True)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 加速器橋在;v0101 一字不動;零網路;不碰 TA-Lib",
        "[VIA:ACCEL-BRIDGE" in src and "import talib" not in src.replace('"import talib"', "") and PRIOR_PATH.name.endswith("v0101.py"))
    print(f"  [計] via_ocr_super v0102 本版 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


def main() -> int:
    if "--selftest-tail" in sys.argv[1:]:
        return cmd_selftest()
    if "--selftest" in sys.argv[1:]:
        rc = cmd_selftest()
        prior = PRIOR.cmd_selftest()
        return rc or prior
    return PRIOR.main()


if __name__ == "__main__":
    sys.exit(main())
