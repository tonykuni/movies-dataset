#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
SUP_MDL747_OcrLaneRunner v0101 — OCR 車道執行器(批495;v0101 批499)
====================================================================
v0100→v0101(批499 操作員實錄「lane=via_paddle_311:本境無此階後端:paddleocr,…(在位:apache_pdfbox,marker)」):
  ① 不在位的後端逐支照抄 GLE 探針的 message(python 件在不在/binary 在不在),err 與 JSON probe 欄都帶——
     「不在位」三個字查不了,「paddlepaddle 未裝」才查得了;② 每支 adapter 帶 secs(時間花在哪一支);
  ③ 頁數照實回(pages):ENG072 v0122 起只送一頁的暫存 PDF,這裡回的 pages 就是證據。
為什麼要有這一支:Baseline families.ocr 把 OCR 生態(paddleocr/easyocr/pytesseract…)定在 **via_paddle_311 專屬境**,
而 ENG072 的 OCR 車道是行程內 import(跑在 via_vrn_312)。兩件事同時成立=後端永遠「不在位」。
本件讓 ENG072 在**本境缺後端**時,改派到 OCR 境的 python 跑同一條 GLE 編排器(SUP_MDL743),結果以 JSON 回主行程:
機器讀 stdout 最後一行 JSON;人看的字走 stderr。零假抽:一個後端都沒裝就回空文字 + 逐支因由。
用法:python SUP_MDL747_OcrLaneRunner_v0101.py --pdf <file> [--adapters a,b] [--disabled c] [--json] | --selftest
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _hub():
    hits = sorted(HERE.glob("SUP_MDL743_GenericLayoutHub_v*.py"))
    if not hits:
        return None, "SUP_MDL743_GenericLayoutHub_v*.py 缺(執行器派不出 OCR)"
    try:
        spec = importlib.util.spec_from_file_location("via_hub_gle_runner", hits[-1])
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        st = mod.mount()
        if st.get("state") in ("ABSENT", "FAILED"):
            return None, f"橋在位但掛載 {st.get('state')}:{st.get('why', '')}"
        return mod, ""
    except Exception as exc:
        return None, f"橋載入失敗 {type(exc).__name__}:{str(exc)[:100]}"


def run(pdf: str, adapters: list, disabled: list) -> dict:
    t0 = time.time()
    out = {"text": "", "route": [], "adapters": [], "err": "", "python": sys.executable, "secs": 0.0}
    hub, why = _hub()
    if hub is None:
        out["err"] = why
        return out
    try:
        mx = hub.backend_matrix() or {}
        on = set(mx.get("on") or [])
        want = [a for a in adapters if a] or list((hub.route_modes() or {}).get("ocr") or [])
        out["on"] = sorted(on & set(want))
        # 批499:逐支照抄探針 message(python/binary 在不在)——「不在位」查不了,「缺 paddlepaddle」才查得了
        rows = {str(r.get("name")): r for r in (mx.get("rows") or []) if isinstance(r, dict)}
        out["probe"] = {a: (("在位" if a in on else "不在位") + ":" + str(rows.get(a, {}).get("message") or ("py=" + str(rows.get(a, {}).get("python")) + " bin=" + str(rows.get(a, {}).get("binary")) if a in rows else "探針無此名"))[:160]) for a in want}
        try:
            import fitz
            with fitz.open(pdf) as _d:
                out["pages"] = int(_d.page_count)
        except Exception:
            out["pages"] = -1
        if not (on & set(want)):
            out["err"] = ("本境無此階後端:" + ",".join(f"{a}({out['probe'][a].split(':', 1)[-1][:70]})" for a in want)
                          + f"(在位:{','.join(sorted(on)[:6]) or '無'})")
            out["secs"] = round(time.time() - t0, 2)
            return out
        O = hub.orchestrator()
        cfg = O.OrchestratorConfig(mode="ocr")
        try:
            cfg.selected_adapters = list(want)
            if disabled:
                cfg.disabled_adapters = list(disabled)
        except Exception:
            pass
        with tempfile.TemporaryDirectory() as td:
            r = O.run_orchestrator(Path(pdf), Path(td), cfg)
        out["text"] = "\n".join(e.text for e in (getattr(r, "canonical_elements", None) or []) if getattr(e, "text", ""))
        out["route"] = list(dict.fromkeys(getattr(r, "route", None) or []))
        for x in (getattr(r, "adapter_results", None) or []):
            _sec = getattr(x, "elapsed_seconds", None) or getattr(x, "seconds", None) or getattr(x, "elapsed", None)
            out["adapters"].append({"name": getattr(x, "adapter_name", "?"), "status": str(getattr(x, "status", "?")),
                                    "n": len(getattr(x, "elements", None) or []), "error": str(getattr(x, "error", "") or "")[:160],
                                    "warnings": [str(w)[:120] for w in (getattr(x, "warnings", None) or [])[:2]],
                                    "probe": str(getattr(x, "probe", "") or "")[:120],
                                    "secs": (round(float(_sec), 2) if isinstance(_sec, (int, float)) else None)})
    except Exception as exc:
        out["err"] = f"{type(exc).__name__}:{str(exc)[:160]}"
    out["secs"] = round(time.time() - t0, 2)
    return out


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)
    with tempfile.TemporaryDirectory() as td:
        pdf = Path(td) / "t.pdf"
        try:
            import fitz
            doc = fitz.open()
            page = doc.new_page()
            page.insert_text((72, 72), "VIA runner selftest 2330", fontsize=14)
            doc.save(str(pdf))
            doc.close()
        except Exception as exc:
            pdf.write_bytes(b"%PDF-1.4 fake")
            print(f"  (fitz 缺 {type(exc).__name__}:用假 PDF)")
        d = run(str(pdf), ["definitely_not_a_backend_x"], [])
        chk("① 本境無此階後端=誠實空文字 + err 講明(零假抽)", d["text"] == "" and bool(d["err"]), f"({d['err'][:60]})")
        d2 = run(str(pdf), ["tesseract"], [])
        chk("② tesseract 階:JSON 契約齊(text/route/adapters/err/python/secs);在位則 adapters 留逐支紀錄,不在位則 err",
            set(d2) >= {"text", "route", "adapters", "err", "python", "secs"} and bool(d2["adapters"] or d2["err"]), f"(route={d2['route']} err={d2['err'][:50]})")
        js = json.dumps(d2, ensure_ascii=False)
        chk("③ 機器讀:結果可 JSON 序列化且 python 欄=本解譯器", json.loads(js)["python"] == sys.executable)
        chk("④ 批499:不在位時 probe 欄逐支帶探針因由(不是只講「不在位」);pages 照實回",
            (not d["err"]) or (isinstance(d.get("probe"), dict) and "definitely_not_a_backend_x" in d["probe"] and "pages" in d),
            f"(probe={str(d.get('probe'))[:60]} pages={d.get('pages')})")
    print(f"  [計] 四檢 OK {4 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--pdf")
    ap.add_argument("--adapters", default="")
    ap.add_argument("--disabled", default="")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        print("=== OCR 車道執行器(SUP_MDL747 v0100)· 三檢自測(零網路)===")
        return selftest()
    if not a.pdf:
        ap.print_help(sys.stderr)
        return 2
    d = run(a.pdf, [x for x in a.adapters.split(",") if x], [x for x in a.disabled.split(",") if x])
    sys.stderr.write(f"[OCR 執行器] {Path(a.pdf).name} · 後端 {a.adapters or '路由'} · {len(d['text'])} 字 · {d['secs']}s" + (f" · {d['err']}" if d["err"] else "") + "\n")
    print(json.dumps(d, ensure_ascii=False))
    return 0 if d["text"] else 3


if __name__ == "__main__":
    sys.exit(main())
